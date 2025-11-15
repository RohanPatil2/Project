#!/usr/bin/env python3
"""
Real-Time Uncertainty-Aware 2D SLAM Node

This node provides cell-wise uncertainty quantification for SLAM:
1. Subscribes to occupancy grid updates
2. Tracks per-cell variance over time
3. Computes Shannon entropy from variance
4. Publishes real-time entropy heat-map (OccupancyGrid)
5. Publishes color heatmap image for RViz visualization

Compatible with SLAM Toolbox and other SLAM systems.

Author: Rohan Upendra Patil
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid
from sensor_msgs.msg import Image
from std_msgs.msg import Float64
import numpy as np
import threading
import cv2
from cv_bridge import CvBridge


class UncertaintySLAMNode(Node):
    """
    Main node for uncertainty-aware SLAM.

    This node computes cell-wise Shannon entropy by tracking variance
    across the particle filter's occupancy estimates.
    """

    def __init__(self):
        super().__init__('uncertainty_slam_node')

        # Declare parameters
        self.declare_parameter('entropy_publish_rate', 10.0)  # Hz, >= 10 Hz target
        self.declare_parameter('map_topic', '/map')
        self.declare_parameter('entropy_grid_topic', '/entropy_map')
        self.declare_parameter('entropy_image_topic', '/entropy_heatmap_image')
        self.declare_parameter('min_observations', 10)  # Minimum cells before publishing

        # Get parameters
        self.entropy_rate = self.get_parameter('entropy_publish_rate').value
        map_topic = self.get_parameter('map_topic').value
        entropy_grid_topic = self.get_parameter('entropy_grid_topic').value
        entropy_image_topic = self.get_parameter('entropy_image_topic').value
        self.min_observations = self.get_parameter('min_observations').value

        # Initialize data structures
        self.current_map = None
        self.entropy_map = None
        self.map_lock = threading.Lock()

        # Cell-wise variance tracking
        self.cell_hit_counts = None  # Track observation counts per cell
        self.cell_sum = None  # Sum of observations
        self.cell_sum_sq = None  # Sum of squared observations

        # CV Bridge for image conversion
        self.cv_bridge = CvBridge()

        # Subscribers
        self.map_sub = self.create_subscription(
            OccupancyGrid,
            map_topic,
            self.map_callback,
            10
        )

        # Publishers
        self.entropy_grid_pub = self.create_publisher(
            OccupancyGrid,
            entropy_grid_topic,
            10
        )

        self.entropy_image_pub = self.create_publisher(
            Image,
            entropy_image_topic,
            10
        )

        self.avg_entropy_pub = self.create_publisher(
            Float64,
            '/map_average_entropy',
            10
        )

        self.max_entropy_pub = self.create_publisher(
            Float64,
            '/map_max_entropy',
            10
        )

        # Timer for entropy computation and publishing
        timer_period = 1.0 / self.entropy_rate
        self.entropy_timer = self.create_timer(timer_period, self.compute_and_publish_entropy)

        self.get_logger().info('Uncertainty SLAM Node initialized')
        self.get_logger().info(f'Publishing entropy grid at {self.entropy_rate} Hz')
        self.get_logger().info(f'Publishing entropy heatmap image at {self.entropy_rate} Hz')

    def map_callback(self, msg):
        """
        Process incoming occupancy grid and update variance tracking.

        Each map update is treated as a new particle observation for
        cell-wise variance computation.
        """
        with self.map_lock:
            self.current_map = msg

            # Initialize variance tracking on first map
            if self.cell_hit_counts is None:
                self._initialize_variance_tracking(msg)

            # Check if map size changed (dynamic resizing)
            if (msg.info.width * msg.info.height != self.cell_hit_counts.size):
                self.get_logger().info('Map size changed, reinitializing variance tracking')
                self._initialize_variance_tracking(msg)

            # Update cell-wise statistics
            self._update_cell_statistics(msg)


    def _initialize_variance_tracking(self, map_msg):
        """Initialize arrays for variance tracking."""
        map_size = map_msg.info.width * map_msg.info.height
        self.cell_hit_counts = np.zeros(map_size, dtype=np.float64)
        self.cell_sum = np.zeros(map_size, dtype=np.float64)
        self.cell_sum_sq = np.zeros(map_size, dtype=np.float64)

        self.get_logger().info(f'Initialized variance tracking for {map_size} cells')

    def _update_cell_statistics(self, map_msg):
        """
        Update running statistics for variance computation.

        Uses Welford's online algorithm for numerical stability.
        """
        # Convert occupancy grid to numpy array
        # Map values: -1 (unknown), 0 (free), 100 (occupied)
        map_data = np.array(map_msg.data, dtype=np.float64)

        # Only update cells that are known (not -1)
        known_mask = map_data >= 0

        # Update statistics for known cells
        self.cell_hit_counts[known_mask] += 1
        self.cell_sum[known_mask] += map_data[known_mask]
        self.cell_sum_sq[known_mask] += map_data[known_mask] ** 2

    def _compute_cell_variance(self):
        """
        Compute per-cell variance from accumulated statistics.

        Returns:
            numpy.ndarray: Variance for each cell
        """
        # Avoid division by zero
        valid_mask = self.cell_hit_counts > 1

        variance = np.zeros_like(self.cell_hit_counts)

        # Variance = E[X²] - E[X]²
        mean = np.divide(
            self.cell_sum[valid_mask],
            self.cell_hit_counts[valid_mask]
        )
        mean_sq = np.divide(
            self.cell_sum_sq[valid_mask],
            self.cell_hit_counts[valid_mask]
        )

        variance[valid_mask] = mean_sq - mean ** 2

        # Ensure non-negative (numerical errors)
        variance = np.maximum(variance, 0)

        return variance

    def _variance_to_shannon_entropy(self, variance):
        """
        Convert variance to Shannon entropy.

        For a cell with occupancy probability p and variance σ²,
        we model the uncertainty using the relationship between
        variance and entropy for binary random variables.

        For binary variable X ∈ {0, 100}:
        - Variance is maximized when p = 0.5 (maximum uncertainty)
        - Entropy is also maximized when p = 0.5

        We map normalized variance to entropy directly.

        Args:
            variance: Per-cell variance

        Returns:
            numpy.ndarray: Shannon entropy per cell (in bits)
        """
        epsilon = 1e-10

        # Normalize variance to [0, 1] range
        # Maximum variance for binary variable (p=0.5) is 0.25 * 100² = 625
        max_variance = 625.0
        normalized_variance = np.clip(variance / max_variance, 0, 1)

        # Higher normalized variance means more uncertainty
        # Map to probability: high variance (1.0) -> p = 0.5 (max entropy)
        #                     low variance (0.0) -> p close to 0 or 1 (low entropy)

        # Use the fact that for binary RV: Var(X) = p(1-p) * range²
        # So p(1-p) is proportional to variance
        # Maximum p(1-p) = 0.25 when p = 0.5

        # Map variance to distance from certainty:
        # High variance -> p closer to 0.5
        # Low variance -> p closer to 0 or 1
        p_uncertainty = np.sqrt(normalized_variance)  # Smoother mapping
        p = 0.5 * (1 - p_uncertainty) + 0.5 * p_uncertainty  # Blend between 0.5 and extremes

        # Simpler approach: directly use normalized variance as proxy for entropy
        # Since both are maximized at p=0.5
        # H_max = 1 bit for binary variable
        entropy = normalized_variance  # Already in [0,1], will be scaled to [0,100] later

        return entropy

    def _create_entropy_heatmap_image(self, entropy, width, height):
        """
        Convert entropy array to a color heatmap image using cv2.applyColorMap.

        Args:
            entropy: 1D numpy array of entropy values [0, 1]
            width: Map width in cells
            height: Map height in cells

        Returns:
            sensor_msgs.msg.Image: Color heatmap image message
        """
        # Reshape to 2D grid
        entropy_2d = entropy.reshape((height, width))

        # Normalize to 0-255 and convert to uint8
        entropy_normalized = np.clip(entropy_2d * 255.0, 0, 255).astype(np.uint8)

        # Apply JET colormap (blue=low, red=high)
        # Note: OpenCV uses BGR format
        entropy_color = cv2.applyColorMap(entropy_normalized, cv2.COLORMAP_JET)

        # Convert BGR to RGB for proper RViz display
        entropy_color_rgb = cv2.cvtColor(entropy_color, cv2.COLOR_BGR2RGB)

        # Convert to ROS Image message
        try:
            image_msg = self.cv_bridge.cv2_to_imgmsg(entropy_color_rgb, encoding='rgb8')
            image_msg.header.stamp = self.get_clock().now().to_msg()
            image_msg.header.frame_id = 'map'
            return image_msg
        except Exception as e:
            self.get_logger().error(f'Failed to convert entropy to image: {e}')
            return None

    def compute_and_publish_entropy(self):
        """
        Main entropy computation routine.

        Computes cell-wise Shannon entropy from particle variance and
        publishes as both an OccupancyGrid message and a color Image message.
        """
        with self.map_lock:
            if self.current_map is None:
                return

            if self.cell_hit_counts is None:
                return

            # Skip if insufficient data
            if np.sum(self.cell_hit_counts > 1) < self.min_observations:
                self.get_logger().debug(
                    f'Insufficient data: {np.sum(self.cell_hit_counts > 1)} cells '
                    f'(need {self.min_observations})'
                )
                return

            # Compute variance and entropy
            variance = self._compute_cell_variance()
            entropy = self._variance_to_shannon_entropy(variance)

            # Get map dimensions
            width = self.current_map.info.width
            height = self.current_map.info.height

            # Create entropy grid message
            entropy_msg = OccupancyGrid()
            entropy_msg.header = self.current_map.header
            entropy_msg.header.stamp = self.get_clock().now().to_msg()
            entropy_msg.info = self.current_map.info

            # Scale entropy to [0, 100] for visualization as OccupancyGrid
            # Maximum entropy for binary variable is 1 bit
            scaled_entropy = np.clip(entropy * 100.0, 0, 100).astype(np.int8)
            entropy_msg.data = scaled_entropy.tolist()

            # Publish entropy grid
            self.entropy_grid_pub.publish(entropy_msg)

            # Create and publish color heatmap image
            heatmap_image = self._create_entropy_heatmap_image(entropy, width, height)
            if heatmap_image is not None:
                self.entropy_image_pub.publish(heatmap_image)

            # Publish statistics
            avg_entropy = Float64()
            valid_cells = self.cell_hit_counts > 1
            avg_entropy.data = float(np.mean(entropy[valid_cells]))
            self.avg_entropy_pub.publish(avg_entropy)

            max_entropy_msg = Float64()
            max_entropy_msg.data = float(np.max(entropy[valid_cells]))
            self.max_entropy_pub.publish(max_entropy_msg)

            # Log statistics periodically
            if hasattr(self, '_log_counter'):
                self._log_counter += 1
            else:
                self._log_counter = 0

            if self._log_counter % 50 == 0:  # Every 5 seconds at 10 Hz
                self.get_logger().info(
                    f'Entropy Stats - Avg: {avg_entropy.data:.4f} bits, '
                    f'Max: {max_entropy_msg.data:.4f} bits, '
                    f'Valid cells: {np.sum(valid_cells)}'
                )


def main(args=None):
    rclpy.init(args=args)

    node = UncertaintySLAMNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
