#!/usr/bin/env python3
"""
Continuous Snapshot & Analytics Engine with Research-Grade Metrics

FEATURES:
- 10-second snapshot timer with sequential timestamped files
- Trajectory tracking with path overlay on maps
- Exploration rate vs. time analytics
- Entropy histogram distribution analysis
- 2x2 composite dashboard images
- Time-series data for video generation

NEW RESEARCH-GRADE METRICS:
- Phase 1: Localization RMSE (Ground Truth vs SLAM Estimate)
- Phase 2: Delta Entropy Heatmaps (ΔH = H_{t-10s} - H_t)
- Phase 3: Real-Time Covariance Ellipse Visualization

Author: Rohan Upendra Patil
Enhanced: 2025-11-18 (Research-Grade Metrics Version)
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid, Odometry
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from std_msgs.msg import Float64, String
from visualization_msgs.msg import Marker
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for performance
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from matplotlib.patches import Circle as MPLCircle
from datetime import datetime
import os
import json
import math
from collections import deque


class ResearchGradeAnalyticsEngine(Node):
    """
    Research-Grade Continuous Analytics Engine.

    Captures evolution of mapping process with:
    - 10-second snapshots
    - Trajectory tracking
    - Live analytics graphs
    - Composite dashboards
    - RMSE localization validation
    - Delta entropy dynamics
    - Covariance ellipse visualization
    """

    def __init__(self):
        super().__init__('research_grade_analytics_engine')

        # Parameters
        self.declare_parameter('output_dir', '~/slam_uncertainty_ws/results')
        self.declare_parameter('snapshot_interval', 10.0)  # seconds

        self.output_dir = os.path.expanduser(self.get_parameter('output_dir').value)
        self.snapshot_interval = self.get_parameter('snapshot_interval').value

        # Create output directories
        self.snapshots_dir = os.path.join(self.output_dir, 'snapshots')
        self.dashboards_dir = os.path.join(self.output_dir, 'dashboards')
        self.analytics_dir = os.path.join(self.output_dir, 'analytics')
        self.rmse_dir = os.path.join(self.output_dir, 'rmse_validation')
        self.delta_dir = os.path.join(self.output_dir, 'delta_entropy')

        os.makedirs(self.snapshots_dir, exist_ok=True)
        os.makedirs(self.dashboards_dir, exist_ok=True)
        os.makedirs(self.analytics_dir, exist_ok=True)
        os.makedirs(self.rmse_dir, exist_ok=True)
        os.makedirs(self.delta_dir, exist_ok=True)

        # Data storage
        self.occupancy_map = None
        self.entropy_map = None
        self.delta_entropy_map = None
        self.robot_position = (0.0, 0.0)  # Current (x, y)

        # Trajectory history (for path overlay)
        self.trajectory = []  # List of (x, y) tuples
        self.max_trajectory_points = 10000  # Limit memory usage

        # Time-series analytics
        self.timestamps = []
        self.avg_entropy_history = []
        self.exploration_rate_history = []  # Percentage of known cells

        # NEW: PHASE 1 - RMSE Tracking
        self.ground_truth_poses = []  # List of (timestamp, x, y, theta)
        self.slam_poses = []  # List of (timestamp, x, y, theta)
        self.pose_errors = []  # List of (timestamp, error_x, error_y, error_euclidean)
        self.rmse_history = []  # List of (timestamp, rmse_x, rmse_y, rmse_total)
        self.last_rmse_calc_time = None

        # NEW: PHASE 3 - Covariance tracking
        self.current_covariance = None  # 2x2 covariance matrix for x,y

        # Snapshot counter
        self.snapshot_count = 0
        self.start_time = None

        # Exploration status
        self.exploration_complete = False
        self.final_results_generated = False

        # Map metadata
        self.map_resolution = 0.05  # Default, will be updated
        self.map_origin_x = 0.0
        self.map_origin_y = 0.0

        # QoS for SLAM topics
        from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy

        slam_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )

        # Subscribers - Basic
        self.map_sub = self.create_subscription(
            OccupancyGrid, '/map', self.map_callback, 10
        )
        self.entropy_sub = self.create_subscription(
            OccupancyGrid, '/entropy_map', self.entropy_callback, 10
        )
        self.avg_entropy_sub = self.create_subscription(
            Float64, '/map_average_entropy', self.avg_entropy_callback, 10
        )
        self.odom_sub = self.create_subscription(
            Odometry, '/odom', self.odom_callback, 10
        )
        self.status_sub = self.create_subscription(
            String, '/exploration_status', self.status_callback, 10
        )

        # NEW: Phase 1 - Ground Truth and SLAM Pose Subscribers
        self.ground_truth_sub = self.create_subscription(
            PoseStamped, '/robot/ground_truth', self.ground_truth_callback, 10
        )

        # Subscribe to SLAM Toolbox pose (adjust topic if using different SLAM)
        self.slam_pose_sub = self.create_subscription(
            PoseWithCovarianceStamped, '/slam_toolbox/pose',
            self.slam_pose_callback, slam_qos
        )

        # NEW: Phase 2 - Delta Entropy Subscriber
        self.delta_entropy_sub = self.create_subscription(
            OccupancyGrid, '/delta_entropy_map', self.delta_entropy_callback, 10
        )

        # NEW: Phase 3 - Covariance Ellipse Publisher
        self.covariance_marker_pub = self.create_publisher(
            Marker, '/localization_uncertainty_ellipse', 10
        )

        # Timers
        self.snapshot_timer = self.create_timer(
            self.snapshot_interval,
            self.snapshot_callback
        )

        # NEW: 1 Hz timer for RMSE calculation
        self.rmse_timer = self.create_timer(1.0, self.calculate_rmse)

        # NEW: 10 Hz timer for covariance ellipse visualization
        self.ellipse_timer = self.create_timer(0.1, self.publish_covariance_ellipse)

        self.get_logger().info('='*70)
        self.get_logger().info('🔬 Research-Grade Analytics Engine Initialized')
        self.get_logger().info('='*70)
        self.get_logger().info(f'Snapshot interval: {self.snapshot_interval}s')
        self.get_logger().info(f'Snapshots dir: {self.snapshots_dir}')
        self.get_logger().info(f'Dashboards dir: {self.dashboards_dir}')
        self.get_logger().info(f'RMSE validation dir: {self.rmse_dir}')
        self.get_logger().info(f'Delta entropy dir: {self.delta_dir}')
        self.get_logger().info('NEW RESEARCH METRICS:')
        self.get_logger().info('  ✓ Phase 1: RMSE Localization Validation')
        self.get_logger().info('  ✓ Phase 2: Delta Entropy Dynamics (ΔH)')
        self.get_logger().info('  ✓ Phase 3: Real-Time Covariance Ellipses')
        self.get_logger().info('='*70)

    def map_callback(self, msg):
        """Store latest occupancy map and update metadata."""
        self.occupancy_map = msg
        self.map_resolution = msg.info.resolution
        self.map_origin_x = msg.info.origin.position.x
        self.map_origin_y = msg.info.origin.position.y

    def entropy_callback(self, msg):
        """Store latest entropy map."""
        self.entropy_map = msg

    def delta_entropy_callback(self, msg):
        """Store latest delta entropy map (ΔH = H_{t-10s} - H_t)."""
        self.delta_entropy_map = msg

    def avg_entropy_callback(self, msg):
        """Track average entropy over time."""
        current_time = self.get_clock().now().nanoseconds / 1e9

        if self.start_time is None:
            self.start_time = current_time

        self.avg_entropy_history.append(msg.data)
        self.timestamps.append(current_time - self.start_time)

    def odom_callback(self, msg):
        """Track robot trajectory for path overlay."""
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y

        self.robot_position = (x, y)

        # Add to trajectory (with decimation to save memory)
        if len(self.trajectory) == 0 or \
           np.linalg.norm(np.array([x, y]) - np.array(self.trajectory[-1])) > 0.05:
            self.trajectory.append((x, y))

            # Limit trajectory size
            if len(self.trajectory) > self.max_trajectory_points:
                self.trajectory = self.trajectory[-self.max_trajectory_points:]

    # ===== NEW: PHASE 1 - RMSE VALIDATION =====

    def ground_truth_callback(self, msg):
        """
        Store ground truth pose (noise-free simulation state).
        """
        timestamp = self.get_clock().now().nanoseconds / 1e9
        x = msg.pose.position.x
        y = msg.pose.position.y

        # Extract theta from quaternion
        qz = msg.pose.orientation.z
        qw = msg.pose.orientation.w
        theta = 2.0 * math.atan2(qz, qw)

        self.ground_truth_poses.append((timestamp, x, y, theta))

        # Keep only last 1000 poses (memory management)
        if len(self.ground_truth_poses) > 1000:
            self.ground_truth_poses = self.ground_truth_poses[-1000:]

    def slam_pose_callback(self, msg):
        """
        Store SLAM estimated pose (from SLAM Toolbox or other SLAM system).
        Also extract covariance for ellipse visualization.
        """
        timestamp = self.get_clock().now().nanoseconds / 1e9
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y

        # Extract theta from quaternion
        qz = msg.pose.pose.orientation.z
        qw = msg.pose.pose.orientation.w
        theta = 2.0 * math.atan2(qz, qw)

        self.slam_poses.append((timestamp, x, y, theta))

        # Keep only last 1000 poses
        if len(self.slam_poses) > 1000:
            self.slam_poses = self.slam_poses[-1000:]

        # NEW: Extract covariance matrix for x, y position
        # Covariance is 6x6 matrix (x, y, z, roll, pitch, yaw)
        # We only need x, y components (indices 0, 1)
        cov = msg.pose.covariance
        self.current_covariance = np.array([[cov[0], cov[1]],
                                           [cov[6], cov[7]]])

    def calculate_rmse(self):
        """
        Calculate RMSE every second and log pose errors.
        RMSE = sqrt(1/N * sum((estimated - true)^2))
        """
        if len(self.ground_truth_poses) == 0 or len(self.slam_poses) == 0:
            return

        current_time = self.get_clock().now().nanoseconds / 1e9

        if self.start_time is None:
            return

        # Find matching poses (by timestamp)
        for gt_timestamp, gt_x, gt_y, gt_theta in self.ground_truth_poses[-10:]:
            # Find closest SLAM pose in time
            closest_slam = None
            min_time_diff = float('inf')

            for slam_timestamp, slam_x, slam_y, slam_theta in self.slam_poses[-10:]:
                time_diff = abs(slam_timestamp - gt_timestamp)
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    closest_slam = (slam_timestamp, slam_x, slam_y, slam_theta)

            if closest_slam is not None and min_time_diff < 0.1:  # Within 100ms
                _, slam_x, slam_y, _ = closest_slam

                # Calculate errors
                error_x = slam_x - gt_x
                error_y = slam_y - gt_y
                error_euclidean = math.sqrt(error_x**2 + error_y**2)

                # Store error
                self.pose_errors.append((current_time - self.start_time,
                                        error_x, error_y, error_euclidean))

        # Calculate RMSE from all errors
        if len(self.pose_errors) > 0:
            errors_x = [e[1] for e in self.pose_errors]
            errors_y = [e[2] for e in self.pose_errors]
            errors_euclidean = [e[3] for e in self.pose_errors]

            rmse_x = math.sqrt(np.mean(np.array(errors_x)**2))
            rmse_y = math.sqrt(np.mean(np.array(errors_y)**2))
            rmse_total = math.sqrt(np.mean(np.array(errors_euclidean)**2))

            self.rmse_history.append((current_time - self.start_time,
                                     rmse_x, rmse_y, rmse_total))

            # Log periodically
            if self.last_rmse_calc_time is None or \
               (current_time - self.last_rmse_calc_time) >= 10.0:
                self.get_logger().info(
                    f'RMSE: Total={rmse_total:.4f}m, X={rmse_x:.4f}m, Y={rmse_y:.4f}m | '
                    f'Samples: {len(self.pose_errors)}'
                )
                self.last_rmse_calc_time = current_time

    # ===== NEW: PHASE 3 - COVARIANCE ELLIPSE VISUALIZATION =====

    def publish_covariance_ellipse(self):
        """
        Publish 2-sigma covariance ellipse as RViz marker.
        Visualizes X/Y localization uncertainty around robot pose.
        """
        if self.current_covariance is None:
            return

        if len(self.slam_poses) == 0:
            return

        # Get latest SLAM pose
        _, x, y, theta = self.slam_poses[-1]

        # Extract eigenvalues and eigenvectors from covariance matrix
        eigenvalues, eigenvectors = np.linalg.eig(self.current_covariance)

        # Largest eigenvalue corresponds to major axis
        largest_eigenvalue_index = np.argmax(eigenvalues)
        largest_eigenvalue = eigenvalues[largest_eigenvalue_index]
        largest_eigenvector = eigenvectors[:, largest_eigenvalue_index]

        # Angle of ellipse (orientation)
        angle = math.atan2(largest_eigenvector[1], largest_eigenvector[0])

        # Ellipse dimensions (2-sigma = 95% confidence)
        # 2-sigma: multiply by sqrt(chi-square(2, 0.95)) = 2.448
        chi_square_95 = 2.448
        width = 2.0 * math.sqrt(eigenvalues[0] * chi_square_95)
        height = 2.0 * math.sqrt(eigenvalues[1] * chi_square_95)

        # Create ellipse marker
        marker = Marker()
        marker.header.frame_id = 'map'
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = 'localization_uncertainty'
        marker.id = 0
        marker.type = Marker.CYLINDER
        marker.action = Marker.ADD

        # Position (at robot pose)
        marker.pose.position.x = x
        marker.pose.position.y = y
        marker.pose.position.z = 0.01  # Slightly above ground

        # Orientation (aligned with covariance ellipse)
        marker.pose.orientation.x = 0.0
        marker.pose.orientation.y = 0.0
        marker.pose.orientation.z = math.sin(angle / 2)
        marker.pose.orientation.w = math.cos(angle / 2)

        # Scale (ellipse dimensions)
        marker.scale.x = width
        marker.scale.y = height
        marker.scale.z = 0.02  # Thin disk

        # Color (semi-transparent blue)
        marker.color.r = 0.0
        marker.color.g = 0.5
        marker.color.b = 1.0
        marker.color.a = 0.3

        marker.lifetime.sec = 1  # 1 second lifetime

        self.covariance_marker_pub.publish(marker)

    # ===== SNAPSHOT AND VISUALIZATION FUNCTIONS =====

    def status_callback(self, msg):
        """Track exploration status."""
        if msg.data == 'COMPLETE' and not self.exploration_complete:
            self.exploration_complete = True
            self.get_logger().info('🎉 Exploration complete! Continuing snapshots for final data...')

            # Schedule final results generation
            self.create_timer(30.0, self.generate_final_results)

    def snapshot_callback(self):
        """
        10-second timer callback: Capture snapshot and analytics.
        """
        if self.occupancy_map is None or self.entropy_map is None:
            return

        self.snapshot_count += 1
        elapsed_time = int(self.snapshot_interval * self.snapshot_count)

        try:
            # Calculate exploration metrics
            exploration_rate = self.calculate_exploration_rate()
            self.exploration_rate_history.append(exploration_rate)

            # Generate all snapshot outputs
            self.save_snapshot_maps(elapsed_time)
            self.save_dashboard(elapsed_time)

            # NEW: Save delta entropy if available
            if self.delta_entropy_map is not None:
                self.save_delta_entropy_snapshot(elapsed_time)

            self.get_logger().info(
                f'📸 Snapshot #{self.snapshot_count} | '
                f'T={elapsed_time:04d}s | '
                f'Exploration: {exploration_rate:.1f}% | '
                f'Trajectory: {len(self.trajectory)} points | '
                f'RMSE samples: {len(self.pose_errors)}'
            )

        except Exception as e:
            self.get_logger().error(f'Snapshot error: {e}')

    def calculate_exploration_rate(self):
        """
        Calculate exploration rate: percentage of known cells vs unknown.
        """
        if self.occupancy_map is None:
            return 0.0

        map_data = np.array(self.occupancy_map.data)
        known_cells = np.sum(map_data >= 0)
        total_cells = len(map_data)

        if total_cells == 0:
            return 0.0

        exploration_rate = (known_cells / total_cells) * 100.0
        return exploration_rate

    def world_to_grid(self, x, y):
        """Convert world coordinates to grid coordinates."""
        gx = int((x - self.map_origin_x) / self.map_resolution)
        gy = int((y - self.map_origin_y) / self.map_resolution)
        return gx, gy

    def save_snapshot_maps(self, elapsed_time):
        """Save individual snapshot maps with trajectory overlay."""
        width = self.occupancy_map.info.width
        height = self.occupancy_map.info.height

        occ_data = np.array(self.occupancy_map.data).reshape((height, width))
        ent_data = np.array(self.entropy_map.data).reshape((height, width))

        # Entropy heatmap with trajectory
        fig, ax = plt.subplots(figsize=(8, 8))
        im = ax.imshow(ent_data, cmap='jet', origin='lower', vmin=0, vmax=100)

        if len(self.trajectory) > 1:
            traj_grid = [self.world_to_grid(x, y) for x, y in self.trajectory]
            traj_x = [gx for gx, gy in traj_grid]
            traj_y = [gy for gx, gy in traj_grid]
            ax.plot(traj_x, traj_y, 'c-', linewidth=2, alpha=0.8, label='Robot Path')

        robot_gx, robot_gy = self.world_to_grid(*self.robot_position)
        ax.plot(robot_gx, robot_gy, 'wo', markersize=10, markeredgecolor='black',
                markeredgewidth=2, label='Robot')

        ax.set_title(f'Entropy Heatmap + Trajectory (T={elapsed_time:04d}s)',
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('X (cells)')
        ax.set_ylabel('Y (cells)')
        plt.colorbar(im, ax=ax, label='Entropy (0-100)')
        ax.legend(loc='upper right')
        plt.tight_layout()

        filename = os.path.join(self.snapshots_dir, f'heatmap_{elapsed_time:04d}s.png')
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()

    def save_delta_entropy_snapshot(self, elapsed_time):
        """
        Save delta entropy heatmap: ΔH = H_{t-10s} - H_t.
        """
        width = self.delta_entropy_map.info.width
        height = self.delta_entropy_map.info.height

        delta_data = np.array(self.delta_entropy_map.data).reshape((height, width))

        fig, ax = plt.subplots(figsize=(8, 8))

        # Custom colormap: Green (positive/reduced) -> Black (zero) -> Red (negative/increased)
        from matplotlib.colors import TwoSlopeNorm

        im = ax.imshow(delta_data, cmap='RdYlGn', origin='lower',
                      norm=TwoSlopeNorm(vmin=-100, vcenter=0, vmax=100))

        ax.set_title(f'Delta Entropy (ΔH = H_{{t-10s}} - H_t) | T={elapsed_time:04d}s',
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('X (cells)')
        ax.set_ylabel('Y (cells)')

        cbar = plt.colorbar(im, ax=ax, label='ΔH')
        cbar.set_label('Green=Reduced | Black=NoChange | Red=Increased')

        plt.tight_layout()

        filename = os.path.join(self.delta_dir, f'delta_entropy_{elapsed_time:04d}s.png')
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()

    def save_dashboard(self, elapsed_time):
        """Save 2x2 composite dashboard with all metrics."""
        width = self.occupancy_map.info.width
        height = self.occupancy_map.info.height

        occ_data = np.array(self.occupancy_map.data).reshape((height, width))
        ent_data = np.array(self.entropy_map.data).reshape((height, width))

        fig = plt.figure(figsize=(16, 16))
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

        # Top-left: Entropy + Path
        ax1 = fig.add_subplot(gs[0, 0])
        im1 = ax1.imshow(ent_data, cmap='jet', origin='lower', vmin=0, vmax=100)

        if len(self.trajectory) > 1:
            traj_grid = [self.world_to_grid(x, y) for x, y in self.trajectory]
            traj_x = [gx for gx, gy in traj_grid]
            traj_y = [gy for gx, gy in traj_grid]
            ax1.plot(traj_x, traj_y, 'c-', linewidth=2, alpha=0.8)

        robot_gx, robot_gy = self.world_to_grid(*self.robot_position)
        ax1.plot(robot_gx, robot_gy, 'wo', markersize=8, markeredgecolor='black', markeredgewidth=2)

        ax1.set_title('Entropy Heatmap + Robot Path', fontsize=12, fontweight='bold')
        plt.colorbar(im1, ax=ax1, label='Entropy', fraction=0.046)

        # Top-right: Occupancy Map
        ax2 = fig.add_subplot(gs[0, 1])
        im2 = ax2.imshow(occ_data, cmap='gray', origin='lower', vmin=-1, vmax=100)

        if len(self.trajectory) > 1:
            ax2.plot(traj_x, traj_y, 'c-', linewidth=2, alpha=0.6)

        ax2.plot(robot_gx, robot_gy, 'ro', markersize=8, markeredgecolor='white', markeredgewidth=2)
        ax2.set_title('Occupancy Grid Map', fontsize=12, fontweight='bold')
        plt.colorbar(im2, ax=ax2, label='Occupancy', fraction=0.046)

        # Bottom-left: Average Entropy vs Time
        ax3 = fig.add_subplot(gs[1, 0])

        if len(self.timestamps) > 0:
            ax3.plot(self.timestamps, self.avg_entropy_history, 'b-', linewidth=2)
            ax3.fill_between(self.timestamps, 0, self.avg_entropy_history, alpha=0.3)
            ax3.axhline(y=np.mean(self.avg_entropy_history), color='r',
                       linestyle='--', label=f'Mean: {np.mean(self.avg_entropy_history):.3f}')

        ax3.set_title('Average Entropy Evolution', fontsize=12, fontweight='bold')
        ax3.set_xlabel('Time (seconds)')
        ax3.set_ylabel('Avg Entropy (bits)')
        ax3.grid(True, alpha=0.3)
        ax3.legend()

        # Bottom-right: RMSE vs Time (NEW!)
        ax4 = fig.add_subplot(gs[1, 1])

        if len(self.rmse_history) > 0:
            times = [r[0] for r in self.rmse_history]
            rmse_x = [r[1] for r in self.rmse_history]
            rmse_y = [r[2] for r in self.rmse_history]
            rmse_total = [r[3] for r in self.rmse_history]

            ax4.plot(times, rmse_total, 'r-', linewidth=2, label='Total RMSE')
            ax4.plot(times, rmse_x, 'g--', linewidth=1.5, label='RMSE X')
            ax4.plot(times, rmse_y, 'b--', linewidth=1.5, label='RMSE Y')

            # Add final RMSE annotation
            if len(rmse_total) > 0:
                final_rmse = rmse_total[-1]
                ax4.text(0.98, 0.98, f'Final: {final_rmse:.4f}m',
                        transform=ax4.transAxes,
                        verticalalignment='top', horizontalalignment='right',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                        fontsize=10, fontweight='bold')

        ax4.set_title('Localization RMSE Evolution', fontsize=12, fontweight='bold')
        ax4.set_xlabel('Time (seconds)')
        ax4.set_ylabel('RMSE (meters)')
        ax4.grid(True, alpha=0.3)
        ax4.legend()

        fig.suptitle(f'Uncertainty-Aware SLAM Dashboard | Time: {elapsed_time:04d}s | ' +
                    f'Snapshots: {self.snapshot_count}',
                    fontsize=16, fontweight='bold')

        filename = os.path.join(self.dashboards_dir, f'dashboard_{elapsed_time:04d}s.png')
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()

    def generate_final_results(self):
        """Generate comprehensive final analytics."""
        if self.final_results_generated:
            return

        self.final_results_generated = True

        self.get_logger().info('📊 Generating final comprehensive analytics...')

        try:
            self.save_entropy_histogram()
            self.save_rmse_analysis()
            self.save_comprehensive_statistics()
            self.save_timeseries_data()

            self.get_logger().info('✅ Final analytics complete!')
            self.get_logger().info(f'📁 Results location: {self.output_dir}')

        except Exception as e:
            self.get_logger().error(f'Final analytics error: {e}')

    def save_rmse_analysis(self):
        """
        Save comprehensive RMSE analysis plots and statistics.
        """
        if len(self.rmse_history) == 0:
            return

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

        times = [r[0] for r in self.rmse_history]
        rmse_x = [r[1] for r in self.rmse_history]
        rmse_y = [r[2] for r in self.rmse_history]
        rmse_total = [r[3] for r in self.rmse_history]

        # Plot 1: RMSE Evolution
        ax1.plot(times, rmse_total, 'r-', linewidth=2, label='Total RMSE')
        ax1.plot(times, rmse_x, 'g--', linewidth=1.5, label='RMSE X')
        ax1.plot(times, rmse_y, 'b--', linewidth=1.5, label='RMSE Y')
        ax1.set_title('RMSE Evolution Over Time', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Time (seconds)')
        ax1.set_ylabel('RMSE (meters)')
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # Plot 2: Pose Error Scatter
        if len(self.pose_errors) > 0:
            error_times = [e[0] for e in self.pose_errors]
            errors_x = [e[1] for e in self.pose_errors]
            errors_y = [e[2] for e in self.pose_errors]

            ax2.scatter(error_times, errors_x, c='green', s=10, alpha=0.5, label='Error X')
            ax2.scatter(error_times, errors_y, c='blue', s=10, alpha=0.5, label='Error Y')
            ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax2.set_title('Individual Pose Errors', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Time (seconds)')
            ax2.set_ylabel('Position Error (meters)')
            ax2.grid(True, alpha=0.3)
            ax2.legend()

        # Plot 3: Error Distribution Histogram
        if len(self.pose_errors) > 0:
            errors_euclidean = [e[3] for e in self.pose_errors]
            ax3.hist(errors_euclidean, bins=50, color='purple', alpha=0.7, edgecolor='black')
            ax3.axvline(x=np.mean(errors_euclidean), color='red', linestyle='--',
                       linewidth=2, label=f'Mean: {np.mean(errors_euclidean):.4f}m')
            ax3.set_title('Error Distribution', fontsize=14, fontweight='bold')
            ax3.set_xlabel('Euclidean Error (meters)')
            ax3.set_ylabel('Frequency')
            ax3.grid(True, alpha=0.3)
            ax3.legend()

        # Plot 4: Statistics Summary
        ax4.axis('off')
        if len(rmse_total) > 0:
            stats_text = f"""
            RMSE STATISTICS

            Final RMSE (Total): {rmse_total[-1]:.6f} m
            Final RMSE (X): {rmse_x[-1]:.6f} m
            Final RMSE (Y): {rmse_y[-1]:.6f} m

            Mean RMSE (Total): {np.mean(rmse_total):.6f} m
            Std Dev (Total): {np.std(rmse_total):.6f} m

            Max Error: {np.max(errors_euclidean):.6f} m
            Min Error: {np.min(errors_euclidean):.6f} m

            Total Samples: {len(self.pose_errors)}
            Duration: {times[-1]:.1f} seconds
            """
            ax4.text(0.1, 0.9, stats_text, transform=ax4.transAxes,
                    verticalalignment='top', fontfamily='monospace',
                    fontsize=12, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.suptitle('RMSE Localization Validation Analysis', fontsize=16, fontweight='bold')
        plt.tight_layout()

        filename = os.path.join(self.rmse_dir, 'rmse_analysis_final.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()

        self.get_logger().info(f'Saved RMSE analysis: {filename}')

    def save_entropy_histogram(self):
        """Save entropy distribution histogram."""
        if self.entropy_map is None:
            return

        ent_data = np.array(self.entropy_map.data)
        valid_entropy = ent_data[ent_data >= 0]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        counts, bins, patches = ax1.hist(valid_entropy, bins=50, color='purple',
                                         alpha=0.7, edgecolor='black')

        for i, patch in enumerate(patches):
            if bins[i] < 30:
                patch.set_facecolor('blue')
            elif bins[i] < 70:
                patch.set_facecolor('orange')
            else:
                patch.set_facecolor('red')

        ax1.set_title('Entropy Distribution Histogram', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Entropy Value (0-100)')
        ax1.set_ylabel('Number of Cells')
        ax1.grid(True, alpha=0.3)
        ax1.axvline(x=30, color='blue', linestyle='--', linewidth=2, label='Certain (<30)')
        ax1.axvline(x=70, color='red', linestyle='--', linewidth=2, label='Uncertain (>70)')
        ax1.legend()

        certain_cells = np.sum(valid_entropy < 30)
        medium_cells = np.sum((valid_entropy >= 30) & (valid_entropy < 70))
        uncertain_cells = np.sum(valid_entropy >= 70)

        categories = ['Certain\n(<30)', 'Medium\n(30-70)', 'Uncertain\n(>70)']
        sizes = [certain_cells, medium_cells, uncertain_cells]
        colors = ['blue', 'orange', 'red']
        explode = (0.05, 0, 0.05)

        ax2.pie(sizes, explode=explode, labels=categories, colors=colors, autopct='%1.1f%%',
                shadow=True, startangle=90, textprops={'fontsize': 12, 'fontweight': 'bold'})
        ax2.set_title('Entropy Distribution by Category', fontsize=14, fontweight='bold')

        plt.suptitle('Final Entropy Analysis', fontsize=16, fontweight='bold')
        plt.tight_layout()

        filename = os.path.join(self.analytics_dir, 'entropy_histogram_final.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()

        self.get_logger().info(f'Saved entropy histogram: {filename}')

    def save_comprehensive_statistics(self):
        """Save detailed JSON statistics."""
        if len(self.timestamps) == 0:
            return

        stats = {
            'metadata': {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_snapshots': self.snapshot_count,
                'total_duration_seconds': self.timestamps[-1] if self.timestamps else 0,
                'snapshot_interval': self.snapshot_interval,
            },
            'entropy_stats': {
                'initial_avg': float(self.avg_entropy_history[0]) if self.avg_entropy_history else 0,
                'final_avg': float(self.avg_entropy_history[-1]) if self.avg_entropy_history else 0,
                'min_avg': float(min(self.avg_entropy_history)) if self.avg_entropy_history else 0,
                'max_avg': float(max(self.avg_entropy_history)) if self.avg_entropy_history else 0,
                'mean_avg': float(np.mean(self.avg_entropy_history)) if self.avg_entropy_history else 0,
                'reduction': float(self.avg_entropy_history[0] - self.avg_entropy_history[-1])
                            if len(self.avg_entropy_history) > 1 else 0,
            },
            'exploration_stats': {
                'final_exploration_rate': float(self.exploration_rate_history[-1])
                                        if self.exploration_rate_history else 0,
                'avg_exploration_rate': float(np.mean(self.exploration_rate_history))
                                       if self.exploration_rate_history else 0,
            },
            'rmse_stats': {
                'final_rmse_total': float(self.rmse_history[-1][3]) if len(self.rmse_history) > 0 else 0,
                'final_rmse_x': float(self.rmse_history[-1][1]) if len(self.rmse_history) > 0 else 0,
                'final_rmse_y': float(self.rmse_history[-1][2]) if len(self.rmse_history) > 0 else 0,
                'mean_rmse_total': float(np.mean([r[3] for r in self.rmse_history]))
                                  if len(self.rmse_history) > 0 else 0,
                'total_pose_samples': len(self.pose_errors),
            },
            'trajectory_stats': {
                'total_waypoints': len(self.trajectory),
                'path_length_meters': self.calculate_path_length(),
            },
            'map_info': {
                'width': self.occupancy_map.info.width if self.occupancy_map else 0,
                'height': self.occupancy_map.info.height if self.occupancy_map else 0,
                'resolution': self.map_resolution,
            }
        }

        filename = os.path.join(self.analytics_dir, 'comprehensive_stats.json')
        with open(filename, 'w') as f:
            json.dump(stats, f, indent=2)

        self.get_logger().info(f'Saved comprehensive statistics: {filename}')

    def calculate_path_length(self):
        """Calculate total path length."""
        if len(self.trajectory) < 2:
            return 0.0

        total_length = 0.0
        for i in range(1, len(self.trajectory)):
            dx = self.trajectory[i][0] - self.trajectory[i-1][0]
            dy = self.trajectory[i][1] - self.trajectory[i-1][1]
            total_length += np.sqrt(dx**2 + dy**2)

        return total_length

    def save_timeseries_data(self):
        """Export time-series as CSV."""
        filename = os.path.join(self.analytics_dir, 'timeseries_data.csv')

        with open(filename, 'w') as f:
            f.write('timestamp_s,avg_entropy,exploration_rate_percent,rmse_total\n')

            max_len = max(len(self.timestamps), len(self.avg_entropy_history),
                         len(self.exploration_rate_history), len(self.rmse_history))

            for i in range(max_len):
                t = self.timestamps[i] if i < len(self.timestamps) else 0
                e = self.avg_entropy_history[i] if i < len(self.avg_entropy_history) else 0
                r = self.exploration_rate_history[i] if i < len(self.exploration_rate_history) else 0
                rmse = self.rmse_history[i][3] if i < len(self.rmse_history) else 0
                f.write(f'{t:.2f},{e:.6f},{r:.2f},{rmse:.6f}\n')

        self.get_logger().info(f'Saved time-series CSV: {filename}')


def main(args=None):
    rclpy.init(args=args)
    node = ResearchGradeAnalyticsEngine()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
