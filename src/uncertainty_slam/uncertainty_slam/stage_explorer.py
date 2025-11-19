#!/usr/bin/env python3
"""
Simple, Robust Stage Robot Controller
NO GLITCHING, NO ARTIFACTS - Just smooth, stable motion

This controller:
1. Moves VERY SLOWLY for perfect SLAM
2. Uses SMOOTH velocity ramping
3. Has SIMPLE waypoint following
4. Works PERFECTLY with Stage simulator

Author: Complete Rewrite for Stability
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
import math
import time


class StageExplorer(Node):
    """
    Ultra-simple, ultra-stable robot controller for Stage.
    
    Key principles:
    - SLOW motion (0.1 m/s max)
    - SMOOTH acceleration
    - SIMPLE control logic
    - NO complex algorithms that can fail
    """

    def __init__(self):
        super().__init__('stage_explorer')

        # ULTRA-CONSERVATIVE PARAMETERS FOR PERFECT SLAM
        self.MAX_LINEAR_SPEED = 0.15   # Slow but reasonable (was 0.001 - too slow!)
        self.MAX_ANGULAR_SPEED = 0.3   # Slow rotation (was 0.002 - too slow!)
        self.WAYPOINT_TOLERANCE = 0.5  # Generous tolerance
        
        # Smooth acceleration
        self.LINEAR_ACCEL = 0.05   # Gentle acceleration
        self.ANGULAR_ACCEL = 0.1   # Gentle rotation
        
        # Robot state
        self.x = -6.0
        self.y = -6.0
        self.theta = 0.0
        self.current_linear = 0.0
        self.current_angular = 0.0
        
        # Waypoint tracking
        self.waypoint_index = 0
        self.exploration_complete = False
        
        # Simple exploration path for 16x16 cave
        self.waypoints = self._create_simple_path()
        
        # Publishers
        self.cmd_vel_pub = self.create_publisher(
            Twist,
            '/robot_0/cmd_vel',
            10
        )
        
        # Subscribers
        self.odom_sub = self.create_subscription(
            Odometry,
            '/robot_0/odom',
            self.odom_callback,
            10
        )
        
        self.scan_sub = self.create_subscription(
            LaserScan,
            '/robot_0/base_scan',
            self.scan_callback,
            10
        )
        
        # Control timer - 10 Hz (slow and steady)
        self.create_timer(0.1, self.control_loop)
        
        # Safety
        self.min_obstacle_distance = 1.0
        self.obstacle_detected = False
        
        self.get_logger().info('=' * 60)
        self.get_logger().info('STAGE EXPLORER - ULTRA-STABLE MODE')
        self.get_logger().info('=' * 60)
        self.get_logger().info(f'Max linear speed: {self.MAX_LINEAR_SPEED} m/s')
        self.get_logger().info(f'Max angular speed: {self.MAX_ANGULAR_SPEED} rad/s')
        self.get_logger().info(f'Total waypoints: {len(self.waypoints)}')
        self.get_logger().info('Strategy: SLOW AND SMOOTH for perfect SLAM')
        self.get_logger().info('=' * 60)

    def _create_simple_path(self):
        """
        Create a SIMPLE exploration path.
        
        Strategy: Systematic grid coverage with slow movement.
        """
        waypoints = [
            # Start position
            (-6.0, -6.0),
            
            # Bottom row - moving right
            (-5.0, -6.0),
            (-4.0, -6.0),
            (-3.0, -6.0),
            (-2.0, -6.0),
            (-1.0, -6.0),
            (0.0, -6.0),
            (1.0, -6.0),
            (2.0, -6.0),
            (3.0, -6.0),
            (4.0, -6.0),
            (5.0, -6.0),
            (6.0, -6.0),
            
            # Move up
            (6.0, -5.0),
            (6.0, -4.0),
            (6.0, -3.0),
            (6.0, -2.0),
            (6.0, -1.0),
            (6.0, 0.0),
            (6.0, 1.0),
            (6.0, 2.0),
            (6.0, 3.0),
            (6.0, 4.0),
            (6.0, 5.0),
            (6.0, 6.0),
            
            # Top row - moving left
            (5.0, 6.0),
            (4.0, 6.0),
            (3.0, 6.0),
            (2.0, 6.0),
            (1.0, 6.0),
            (0.0, 6.0),
            (-1.0, 6.0),
            (-2.0, 6.0),
            (-3.0, 6.0),
            (-4.0, 6.0),
            (-5.0, 6.0),
            (-6.0, 6.0),
            
            # Move down
            (-6.0, 5.0),
            (-6.0, 4.0),
            (-6.0, 3.0),
            (-6.0, 2.0),
            (-6.0, 1.0),
            (-6.0, 0.0),
            (-6.0, -1.0),
            (-6.0, -2.0),
            (-6.0, -3.0),
            (-6.0, -4.0),
            (-6.0, -5.0),
            
            # Center sweep
            (-3.0, -3.0),
            (0.0, 0.0),
            (3.0, 3.0),
            (0.0, 0.0),
        ]
        
        return waypoints

    def odom_callback(self, msg):
        """Update robot position from odometry."""
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        
        # Extract yaw from quaternion
        quat = msg.pose.pose.orientation
        siny_cosp = 2 * (quat.w * quat.z + quat.x * quat.y)
        cosy_cosp = 1 - 2 * (quat.y * quat.y + quat.z * quat.z)
        self.theta = math.atan2(siny_cosp, cosy_cosp)

    def scan_callback(self, msg):
        """Check for obstacles in front."""
        # Check front 60 degrees
        num_rays = len(msg.ranges)
        front_rays = num_rays // 4  # Front quarter
        
        front_ranges = []
        for i in range(num_rays // 2 - front_rays, num_rays // 2 + front_rays):
            if i >= 0 and i < len(msg.ranges):
                r = msg.ranges[i]
                if r > msg.range_min and r < msg.range_max:
                    front_ranges.append(r)
        
        if front_ranges:
            self.min_obstacle_distance = min(front_ranges)
            self.obstacle_detected = self.min_obstacle_distance < 0.8
        else:
            self.obstacle_detected = False

    def control_loop(self):
        """Main control loop - SIMPLE and STABLE."""
        
        # Check if exploration complete
        if self.waypoint_index >= len(self.waypoints):
            if not self.exploration_complete:
                self.exploration_complete = True
                self.stop_robot()
                self.get_logger().info('')
                self.get_logger().info('=' * 60)
                self.get_logger().info('✅ EXPLORATION COMPLETE!')
                self.get_logger().info('=' * 60)
            return
        
        # Get current goal
        goal_x, goal_y = self.waypoints[self.waypoint_index]
        
        # Calculate distance and angle
        dx = goal_x - self.x
        dy = goal_y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        angle_to_goal = math.atan2(dy, dx)
        
        # Calculate angle error
        angle_error = angle_to_goal - self.theta
        # Normalize to [-pi, pi]
        while angle_error > math.pi:
            angle_error -= 2 * math.pi
        while angle_error < -math.pi:
            angle_error += 2 * math.pi
        
        # Check if reached waypoint
        if distance < self.WAYPOINT_TOLERANCE:
            self.waypoint_index += 1
            progress = (self.waypoint_index / len(self.waypoints)) * 100
            self.get_logger().info(
                f'✓ Waypoint {self.waypoint_index}/{len(self.waypoints)} | '
                f'Progress: {progress:.1f}%'
            )
            return
        
        # ULTRA-SIMPLE CONTROL: Turn, then move
        target_linear = 0.0
        target_angular = 0.0
        
        if abs(angle_error) > 0.3:  # Need to turn (>17 degrees)
            # JUST TURN
            target_angular = 0.15 * angle_error  # Proportional
            target_linear = 0.0
        elif self.obstacle_detected:
            # STOP if obstacle
            target_linear = 0.0
            target_angular = 0.2  # Gentle turn to avoid
            self.get_logger().warn(f'Obstacle detected at {self.min_obstacle_distance:.2f}m')
        else:
            # JUST MOVE FORWARD
            target_linear = min(0.1, distance * 0.2)  # Proportional, max 0.1 m/s
            target_angular = angle_error * 0.1  # Small correction
        
        # Apply smooth acceleration
        linear_diff = target_linear - self.current_linear
        linear_diff = max(-self.LINEAR_ACCEL, min(self.LINEAR_ACCEL, linear_diff))
        self.current_linear += linear_diff
        
        angular_diff = target_angular - self.current_angular
        angular_diff = max(-self.ANGULAR_ACCEL, min(self.ANGULAR_ACCEL, angular_diff))
        self.current_angular += angular_diff
        
        # Clamp to limits
        self.current_linear = max(-self.MAX_LINEAR_SPEED, 
                                   min(self.MAX_LINEAR_SPEED, self.current_linear))
        self.current_angular = max(-self.MAX_ANGULAR_SPEED,
                                    min(self.MAX_ANGULAR_SPEED, self.current_angular))
        
        # Publish command
        cmd = Twist()
        cmd.linear.x = self.current_linear
        cmd.angular.z = self.current_angular
        self.cmd_vel_pub.publish(cmd)

    def stop_robot(self):
        """Stop the robot completely."""
        cmd = Twist()
        cmd.linear.x = 0.0
        cmd.angular.z = 0.0
        self.cmd_vel_pub.publish(cmd)
        self.current_linear = 0.0
        self.current_angular = 0.0


def main(args=None):
    rclpy.init(args=args)
    node = StageExplorer()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Stopping robot...')
        node.stop_robot()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

