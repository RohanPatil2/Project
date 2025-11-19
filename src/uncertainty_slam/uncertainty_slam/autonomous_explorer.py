#!/usr/bin/env python3
"""
Autonomous Path Follower for Stage Robot
Follows a pre-defined path while GMapping builds map and entropy is computed.

This is what the user wants:
- Robot follows FIXED PATH automatically
- No manual control needed
- While exploring, entropy heatmap shows live
- Completely autonomous

Author: Rohan Upendra Patil
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import String
import math
import time

class AutonomousExplorer(Node):
    """
    Autonomous explorer that follows a pre-defined path through the environment.
    """

    def __init__(self):
        super().__init__('autonomous_explorer')

        # Parameters - REDUCED FOR SMOOTH, STABLE MOTION
        self.declare_parameter('linear_speed', 0.15)  # Reduced from 0.3 to 0.15
        self.declare_parameter('angular_speed', 0.3)  # Reduced from 0.5 to 0.3
        self.declare_parameter('goal_tolerance', 0.4)  # Increased from 0.3 to 0.4
        self.declare_parameter('exploration_delay', 2.0)  # Seconds to wait at start

        self.linear_speed = self.get_parameter('linear_speed').value
        self.angular_speed = self.get_parameter('angular_speed').value
        self.goal_tolerance = self.get_parameter('goal_tolerance').value
        self.exploration_delay = self.get_parameter('exploration_delay').value

        # Robot state
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_theta = 0.0
        self.current_waypoint_index = 0
        self.exploration_started = False
        self.exploration_complete = False

        # Pre-defined exploration path for 16m×16m cave map
        # Starting position: (-6, -6)
        # This path systematically explores the entire cave
        self.waypoints = self._create_exploration_path()

        # Publishers
        self.cmd_vel_pub = self.create_publisher(
            Twist,
            '/robot_0/cmd_vel',
            10
        )

        self.status_pub = self.create_publisher(
            String,
            '/exploration_status',
            10
        )

        # Subscribers
        self.odom_sub = self.create_subscription(
            Odometry,
            '/robot_0/odom',
            self.odom_callback,
            10
        )

        # Control loop timer (10 Hz)
        self.control_timer = self.create_timer(0.1, self.control_loop)

        # Startup delay timer
        self.startup_timer = self.create_timer(
            self.exploration_delay,
            self.start_exploration
        )

        self.get_logger().info('='*60)
        self.get_logger().info('🤖 AUTONOMOUS EXPLORER INITIALIZED')
        self.get_logger().info('='*60)
        self.get_logger().info(f'Total waypoints: {len(self.waypoints)}')
        self.get_logger().info(f'Linear speed: {self.linear_speed} m/s')
        self.get_logger().info(f'Angular speed: {self.angular_speed} rad/s')
        self.get_logger().info(f'Starting in {self.exploration_delay} seconds...')
        self.get_logger().info('='*60)

    def _create_exploration_path(self):
        """
        Create a pre-defined exploration path for the 16m×16m cave map.

        This path is designed to:
        - Cover the entire navigable area
        - Visit all rooms and corridors
        - Provide good SLAM coverage
        - Generate rich entropy patterns

        Coordinates are in meters, relative to map origin.
        Cave map spans approximately (-8, -8) to (8, 8).
        """
        waypoints = [
            # Start: Robot spawns at (-6, -6)

            # Phase 1: Explore bottom-left area
            (-6.0, -6.0),   # Starting position
            (-5.0, -6.0),
            (-4.0, -6.0),
            (-3.0, -6.0),
            (-2.0, -6.0),
            (-1.0, -6.0),

            # Move up left side
            (-1.0, -5.0),
            (-1.0, -4.0),
            (-1.0, -3.0),
            (-1.0, -2.0),
            (-1.0, -1.0),
            (-1.0, 0.0),

            # Phase 2: Explore left corridor
            (-2.0, 0.0),
            (-3.0, 0.0),
            (-4.0, 0.0),
            (-5.0, 0.0),
            (-6.0, 0.0),

            # Move up
            (-6.0, 1.0),
            (-6.0, 2.0),
            (-6.0, 3.0),
            (-6.0, 4.0),
            (-6.0, 5.0),
            (-6.0, 6.0),

            # Phase 3: Explore top-left area
            (-5.0, 6.0),
            (-4.0, 6.0),
            (-3.0, 6.0),
            (-2.0, 6.0),
            (-1.0, 6.0),

            # Move across top
            (-1.0, 5.0),
            (-1.0, 4.0),
            (-1.0, 3.0),
            (-1.0, 2.0),
            (-1.0, 1.0),

            # Phase 4: Explore center area
            (0.0, 1.0),
            (0.0, 2.0),
            (0.0, 3.0),
            (0.0, 4.0),
            (0.0, 5.0),
            (0.0, 6.0),

            # Phase 5: Explore top-right area
            (1.0, 6.0),
            (2.0, 6.0),
            (3.0, 6.0),
            (4.0, 6.0),
            (5.0, 6.0),
            (6.0, 6.0),

            # Move down right side
            (6.0, 5.0),
            (6.0, 4.0),
            (6.0, 3.0),
            (6.0, 2.0),
            (6.0, 1.0),
            (6.0, 0.0),

            # Phase 6: Explore right corridor
            (5.0, 0.0),
            (4.0, 0.0),
            (3.0, 0.0),
            (2.0, 0.0),
            (1.0, 0.0),

            # Phase 7: Explore bottom-right area
            (1.0, -1.0),
            (1.0, -2.0),
            (1.0, -3.0),
            (1.0, -4.0),
            (1.0, -5.0),
            (1.0, -6.0),

            # Move across bottom
            (2.0, -6.0),
            (3.0, -6.0),
            (4.0, -6.0),
            (5.0, -6.0),
            (6.0, -6.0),

            # Phase 8: Final sweep - move up right edge
            (6.0, -5.0),
            (6.0, -4.0),
            (6.0, -3.0),
            (6.0, -2.0),
            (6.0, -1.0),

            # Phase 9: Return to center
            (5.0, -1.0),
            (4.0, -1.0),
            (3.0, -1.0),
            (2.0, -1.0),
            (1.0, -1.0),
            (0.0, -1.0),
            (0.0, 0.0),

            # Final position: center
            (0.0, 0.0),
        ]

        return waypoints

    def odom_callback(self, msg):
        """Update current robot pose from odometry."""
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y

        # Extract yaw from quaternion
        quat = msg.pose.pose.orientation
        siny_cosp = 2 * (quat.w * quat.z + quat.x * quat.y)
        cosy_cosp = 1 - 2 * (quat.y * quat.y + quat.z * quat.z)
        self.current_theta = math.atan2(siny_cosp, cosy_cosp)

    def start_exploration(self):
        """Start autonomous exploration after initial delay."""
        self.exploration_started = True
        self.startup_timer.cancel()

        self.get_logger().info('')
        self.get_logger().info('🚀 STARTING AUTONOMOUS EXPLORATION!')
        self.get_logger().info('='*60)
        self.get_logger().info('Watch RViz to see:')
        self.get_logger().info('  - SLAM map building in real-time')
        self.get_logger().info('  - Live entropy heatmap (RED → BLUE)')
        self.get_logger().info('  - Robot following pre-defined path')
        self.get_logger().info('='*60)
        self.get_logger().info('')

        # Publish initial status
        status_msg = String()
        status_msg.data = 'STARTED'
        self.status_pub.publish(status_msg)

    def control_loop(self):
        """Main control loop - navigate to waypoints."""
        if not self.exploration_started or self.exploration_complete:
            return

        # Check if all waypoints completed
        if self.current_waypoint_index >= len(self.waypoints):
            self.complete_exploration()
            return

        # Get current goal
        goal_x, goal_y = self.waypoints[self.current_waypoint_index]

        # Compute distance and angle to goal
        dx = goal_x - self.current_x
        dy = goal_y - self.current_y
        distance = math.sqrt(dx**2 + dy**2)
        desired_theta = math.atan2(dy, dx)

        # Check if waypoint reached
        if distance < self.goal_tolerance:
            self.current_waypoint_index += 1
            progress = (self.current_waypoint_index / len(self.waypoints)) * 100

            self.get_logger().info(
                f'✓ Waypoint {self.current_waypoint_index}/{len(self.waypoints)} '
                f'reached | Progress: {progress:.1f}%'
            )

            # Publish status
            status_msg = String()
            status_msg.data = f'WAYPOINT_{self.current_waypoint_index}'
            self.status_pub.publish(status_msg)

            return

        # Compute angular error
        angle_error = desired_theta - self.current_theta

        # Normalize angle to [-pi, pi]
        while angle_error > math.pi:
            angle_error -= 2 * math.pi
        while angle_error < -math.pi:
            angle_error += 2 * math.pi

        # Create velocity command
        cmd = Twist()

        # SMOOTH Proportional control - reduced gains for stability
        angular_gain = 1.0  # Reduced from 2.0 to 1.0
        linear_gain = 0.3   # Reduced from 0.5 to 0.3

        # TURN-THEN-MOVE strategy (prevents glitching)
        ANGLE_THRESHOLD = 0.3  # ~17 degrees - turn first if misaligned

        if abs(angle_error) > ANGLE_THRESHOLD:
            # STAGE 1: TURN IN PLACE
            cmd.linear.x = 0.0  # NO forward motion while turning
            cmd.angular.z = angular_gain * angle_error
            cmd.angular.z = max(-self.angular_speed, min(self.angular_speed, cmd.angular.z))
        else:
            # STAGE 2: MOVE FORWARD
            cmd.linear.x = linear_gain * distance
            cmd.linear.x = max(0.0, min(self.linear_speed, cmd.linear.x))
            # Small angular correction while moving
            cmd.angular.z = angular_gain * angle_error * 0.5  # Reduced correction
            cmd.angular.z = max(-self.angular_speed * 0.3, min(self.angular_speed * 0.3, cmd.angular.z))

        # Publish command
        self.cmd_vel_pub.publish(cmd)

    def complete_exploration(self):
        """Called when all waypoints are visited."""
        if self.exploration_complete:
            return

        self.exploration_complete = True

        # Stop robot
        stop_cmd = Twist()
        self.cmd_vel_pub.publish(stop_cmd)

        # Publish completion status
        status_msg = String()
        status_msg.data = 'COMPLETE'
        self.status_pub.publish(status_msg)

        self.get_logger().info('')
        self.get_logger().info('='*60)
        self.get_logger().info('🎉 ✅ EXPLORATION 100% COMPLETE!')
        self.get_logger().info('='*60)
        self.get_logger().info(f'Total waypoints covered: {len(self.waypoints)}')
        self.get_logger().info('📊 Generating results in 30 seconds...')
        self.get_logger().info('✅ Results will be saved to: ~/slam_uncertainty_ws/results/visualizations/')
        self.get_logger().info('='*60)
        self.get_logger().info('')

    def stop_robot(self):
        """Emergency stop."""
        stop_cmd = Twist()
        self.cmd_vel_pub.publish(stop_cmd)


def main(args=None):
    rclpy.init(args=args)

    node = AutonomousExplorer()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Keyboard interrupt - stopping robot')
        node.stop_robot()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
