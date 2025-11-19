#!/usr/bin/env python3
"""
SIMPLEST POSSIBLE TEST ROBOT
Just drives in a square at constant speed.
If this doesn't produce a clean map, SLAM is broken.

NO waypoints, NO complex logic, NOTHING fancy.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import time


class SimpleTestRobot(Node):
    """
    Brain-dead simple robot that drives in a square.
    """

    def __init__(self):
        super().__init__('simple_test_robot')

        # Publishers
        self.cmd_vel_pub = self.create_publisher(
            Twist,
            '/robot_0/cmd_vel',
            10
        )

        # State machine
        self.state = 'FORWARD'
        self.state_start_time = time.time()
        
        # Timing
        self.FORWARD_TIME = 8.0   # Drive forward for 8 seconds
        self.TURN_TIME = 4.0      # Turn for 4 seconds
        
        # Speeds - REASONABLE
        self.FORWARD_SPEED = 0.2  # 0.2 m/s
        self.TURN_SPEED = 0.4     # 0.4 rad/s (~23 deg/s)
        
        # Control loop - 10 Hz
        self.create_timer(0.1, self.control_loop)
        
        self.lap_count = 0
        self.side_count = 0
        
        self.get_logger().info('=' * 60)
        self.get_logger().info('SIMPLE TEST ROBOT - SQUARE PATTERN')
        self.get_logger().info('=' * 60)
        self.get_logger().info('Forward: 8 sec at 0.2 m/s')
        self.get_logger().info('Turn: 4 sec at 0.4 rad/s')
        self.get_logger().info('Pattern: Square with 4 sides')
        self.get_logger().info('=' * 60)

    def control_loop(self):
        """State machine: forward, turn, forward, turn..."""
        
        elapsed = time.time() - self.state_start_time
        cmd = Twist()
        
        if self.state == 'FORWARD':
            # Drive forward
            cmd.linear.x = self.FORWARD_SPEED
            cmd.angular.z = 0.0
            
            if elapsed >= self.FORWARD_TIME:
                # Switch to turn
                self.state = 'TURN'
                self.state_start_time = time.time()
                self.side_count += 1
                self.get_logger().info(f'Side {self.side_count} complete - turning...')
                
        elif self.state == 'TURN':
            # Turn in place
            cmd.linear.x = 0.0
            cmd.angular.z = self.TURN_SPEED
            
            if elapsed >= self.TURN_TIME:
                # Switch to forward
                self.state = 'FORWARD'
                self.state_start_time = time.time()
                
                if self.side_count % 4 == 0:
                    self.lap_count += 1
                    self.get_logger().info('')
                    self.get_logger().info(f'✅ LAP {self.lap_count} COMPLETE!')
                    self.get_logger().info('')
                    
                    if self.lap_count >= 3:
                        # Stop after 3 laps
                        self.get_logger().info('Test complete! Stopping.')
                        cmd.linear.x = 0.0
                        cmd.angular.z = 0.0
                        self.cmd_vel_pub.publish(cmd)
                        rclpy.shutdown()
                        return
        
        # Publish command
        self.cmd_vel_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = SimpleTestRobot()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

