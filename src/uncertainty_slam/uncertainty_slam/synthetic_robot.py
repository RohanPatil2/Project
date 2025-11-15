#!/usr/bin/env python3
"""
Synthetic Robot Data Generator for Uncertainty-Aware SLAM Testing
COMPLEX ENVIRONMENT VERSION with degraded sensor for rich entropy maps.

Features:
- Multi-room layout with narrow corridors
- 240-degree FOV laser (blind spot behind robot)
- 4.0m max range (limited visibility)
- Increased sensor noise
- Logical pre-mapped exploration route
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist, TransformStamped, PoseStamped
from std_msgs.msg import String
import tf2_ros
import numpy as np
import math
import sys
import termios
import tty
import select


class VirtualEnvironment:
    """Simulates a complex 2D environment with multiple rooms and corridors."""

    def __init__(self, width=10.0, height=10.0):
        self.width = width
        self.height = height
        self.obstacles = []
        self._create_complex_multi_room_environment()

    def _create_complex_multi_room_environment(self):
        """
        Create a COMPLEX multi-room environment with narrow corridors.

        Layout (10m × 10m):
        ┌──────────────────────────────────────┐
        │         │ Corridor │                 │
        │ Room 1  │──────────│    Room 2       │
        │   ┌─┐   │          │      ┌─┐        │
        │   │U│   │          │      │L│        │
        ├───┴─┴───┤          ├──────┴─┴────────┤
        │         Door       │                 │
        │ Room 3  │          │    Room 4       │
        │    ┌┐   │          │       ┌┐        │
        │    └┘   │          │       └┘        │
        └─────────┴──────────┴─────────────────┘

        4 Rooms + Central Corridor + Narrow Doorways
        """

        # ===== EXTERIOR WALLS (10m × 10m) =====
        self.obstacles.append({'type': 'wall', 'x1': -5.0, 'y1': -5.0, 'x2': 5.0, 'y2': -5.0})  # Bottom
        self.obstacles.append({'type': 'wall', 'x1': 5.0, 'y1': -5.0, 'x2': 5.0, 'y2': 5.0})    # Right
        self.obstacles.append({'type': 'wall', 'x1': 5.0, 'y1': 5.0, 'x2': -5.0, 'y2': 5.0})    # Top
        self.obstacles.append({'type': 'wall', 'x1': -5.0, 'y1': 5.0, 'x2': -5.0, 'y2': -5.0})  # Left

        # ===== INTERNAL WALLS - ROOM DIVIDERS =====

        # VERTICAL WALL 1 - Separates Rooms 1&3 from Central Corridor
        # Left side vertical wall with doorway at y=0
        self.obstacles.append({'type': 'wall', 'x1': -2.0, 'y1': 5.0, 'x2': -2.0, 'y2': 0.75})   # Top segment
        self.obstacles.append({'type': 'wall', 'x1': -2.0, 'y1': -0.75, 'x2': -2.0, 'y2': -5.0}) # Bottom segment
        # Doorway gap: y = -0.75 to 0.75 (1.5m wide)

        # VERTICAL WALL 2 - Separates Central Corridor from Rooms 2&4
        # Right side vertical wall with doorway at y=0
        self.obstacles.append({'type': 'wall', 'x1': 1.5, 'y1': 5.0, 'x2': 1.5, 'y2': 0.75})    # Top segment
        self.obstacles.append({'type': 'wall', 'x1': 1.5, 'y1': -0.75, 'x2': 1.5, 'y2': -5.0})  # Bottom segment
        # Doorway gap: y = -0.75 to 0.75 (1.5m wide)

        # HORIZONTAL WALL 1 - Separates Room 1 from Room 3
        # Top-left horizontal wall with narrow corridor opening
        self.obstacles.append({'type': 'wall', 'x1': -5.0, 'y1': 0.0, 'x2': -2.75, 'y2': 0.0})  # Left segment
        self.obstacles.append({'type': 'wall', 'x1': -1.25, 'y1': 0.0, 'x2': -2.0, 'y2': 0.0})  # Right segment
        # Corridor opening: x = -2.75 to -1.25 (1.5m wide)

        # HORIZONTAL WALL 2 - Separates Room 2 from Room 4
        # Top-right horizontal wall with narrow corridor opening
        self.obstacles.append({'type': 'wall', 'x1': 1.5, 'y1': 0.0, 'x2': 2.25, 'y2': 0.0})    # Left segment
        self.obstacles.append({'type': 'wall', 'x1': 3.75, 'y1': 0.0, 'x2': 5.0, 'y2': 0.0})    # Right segment
        # Corridor opening: x = 2.25 to 3.75 (1.5m wide)

        # CENTRAL CORRIDOR WALLS - Narrow vertical passage connecting doorways
        # Creates a narrow central corridor (width = 1.5m - (-2.0m) = 3.5m, but constrained)
        self.obstacles.append({'type': 'wall', 'x1': -0.5, 'y1': 3.0, 'x2': -0.5, 'y2': 0.75})   # Left corridor wall (top)
        self.obstacles.append({'type': 'wall', 'x1': -0.5, 'y1': -0.75, 'x2': -0.5, 'y2': -3.0}) # Left corridor wall (bottom)

        self.obstacles.append({'type': 'wall', 'x1': 0.5, 'y1': 3.0, 'x2': 0.5, 'y2': 0.75})     # Right corridor wall (top)
        self.obstacles.append({'type': 'wall', 'x1': 0.5, 'y1': -0.75, 'x2': 0.5, 'y2': -3.0})   # Right corridor wall (bottom)
        # This creates a 1.0m wide central corridor passage

        # ===== U-SHAPED OBSTACLES (Create shadow zones) =====

        # U-SHAPE in Room 1 (top-left room)
        self.obstacles.append({'type': 'wall', 'x1': -4.0, 'y1': 3.5, 'x2': -3.0, 'y2': 3.5})  # Top
        self.obstacles.append({'type': 'wall', 'x1': -4.0, 'y1': 3.5, 'x2': -4.0, 'y2': 2.0})  # Left
        self.obstacles.append({'type': 'wall', 'x1': -3.0, 'y1': 3.5, 'x2': -3.0, 'y2': 2.0})  # Right
        # Opens downward - creates shadow zone inside

        # U-SHAPE in Room 2 (top-right room)
        self.obstacles.append({'type': 'wall', 'x1': 3.0, 'y1': 3.5, 'x2': 4.0, 'y2': 3.5})    # Top
        self.obstacles.append({'type': 'wall', 'x1': 3.0, 'y1': 3.5, 'x2': 3.0, 'y2': 2.0})    # Left
        self.obstacles.append({'type': 'wall', 'x1': 4.0, 'y1': 3.5, 'x2': 4.0, 'y2': 2.0})    # Right
        # Opens downward

        # ===== L-SHAPED OBSTACLES =====

        # L-SHAPE in Room 3 (bottom-left room)
        self.obstacles.append({'type': 'wall', 'x1': -4.5, 'y1': -2.0, 'x2': -3.0, 'y2': -2.0})  # Horizontal
        self.obstacles.append({'type': 'wall', 'x1': -3.0, 'y1': -2.0, 'x2': -3.0, 'y2': -3.5})  # Vertical

        # L-SHAPE in Room 4 (bottom-right room)
        self.obstacles.append({'type': 'wall', 'x1': 3.0, 'y1': -2.0, 'x2': 4.5, 'y2': -2.0})    # Horizontal
        self.obstacles.append({'type': 'wall', 'x1': 3.0, 'y1': -2.0, 'x2': 3.0, 'y2': -3.5})    # Vertical

        # ===== ADDITIONAL OBSTACLES FOR COMPLEXITY =====

        # Box in Room 1
        self.obstacles.append({'type': 'box', 'cx': -3.5, 'cy': 1.0, 'w': 0.6, 'h': 0.6})

        # Box in Room 2
        self.obstacles.append({'type': 'box', 'cx': 3.5, 'cy': 1.0, 'w': 0.6, 'h': 0.6})

        # Box in Room 3
        self.obstacles.append({'type': 'box', 'cx': -3.5, 'cy': -3.5, 'w': 0.7, 'h': 0.7})

        # Box in Room 4
        self.obstacles.append({'type': 'box', 'cx': 3.5, 'cy': -3.5, 'w': 0.7, 'h': 0.7})

        # Pillars in central corridor for additional occlusion
        self.obstacles.append({'type': 'box', 'cx': -0.2, 'cy': 2.0, 'w': 0.3, 'h': 0.3})
        self.obstacles.append({'type': 'box', 'cx': 0.2, 'cy': -2.0, 'w': 0.3, 'h': 0.3})

    def raycast(self, x, y, angle, max_range=4.0):
        """
        Cast a ray from (x,y) at given angle and return distance to nearest obstacle.

        DEGRADED SENSOR:
        - Max range: 4.0m (reduced from 10.0m)
        - Increased noise: 2cm std dev
        """
        # Ray direction
        dx = math.cos(angle)
        dy = math.sin(angle)

        min_dist = max_range

        # Check all obstacles
        for obs in self.obstacles:
            if obs['type'] == 'wall':
                # Line-line intersection
                dist = self._ray_wall_intersection(x, y, dx, dy,
                                                   obs['x1'], obs['y1'],
                                                   obs['x2'], obs['y2'])
                if dist is not None and dist < min_dist:
                    min_dist = dist

            elif obs['type'] == 'box':
                # Check all 4 walls of the box
                cx, cy, w, h = obs['cx'], obs['cy'], obs['w'], obs['h']
                walls = [
                    (cx - w/2, cy - h/2, cx + w/2, cy - h/2),  # Bottom
                    (cx + w/2, cy - h/2, cx + w/2, cy + h/2),  # Right
                    (cx + w/2, cy + h/2, cx - w/2, cy + h/2),  # Top
                    (cx - w/2, cy + h/2, cx - w/2, cy - h/2),  # Left
                ]
                for x1, y1, x2, y2 in walls:
                    dist = self._ray_wall_intersection(x, y, dx, dy, x1, y1, x2, y2)
                    if dist is not None and dist < min_dist:
                        min_dist = dist

        # DEGRADED SENSOR: Increased noise (2cm std dev)
        noise = np.random.normal(0, 0.02)
        return max(0.1, min_dist + noise)

    def _ray_wall_intersection(self, rx, ry, rdx, rdy, wx1, wy1, wx2, wy2):
        """Calculate intersection distance between ray and wall segment."""
        # Wall direction
        wdx = wx2 - wx1
        wdy = wy2 - wy1

        # Solve: ray_origin + t1 * ray_dir = wall_start + t2 * wall_dir
        denominator = rdx * wdy - rdy * wdx

        if abs(denominator) < 1e-10:  # Parallel
            return None

        t1 = ((wx1 - rx) * wdy - (wy1 - ry) * wdx) / denominator
        t2 = ((wx1 - rx) * rdy - (wy1 - ry) * rdx) / denominator

        # Check if intersection is in valid range
        if t1 >= 0 and 0 <= t2 <= 1:
            return t1

        return None

    def is_collision(self, x, y, robot_radius=0.18):
        """Check if robot at (x,y) collides with any obstacle."""
        # Check exterior walls
        if (x - robot_radius <= -self.width/2 or
            x + robot_radius >= self.width/2 or
            y - robot_radius <= -self.height/2 or
            y + robot_radius >= self.height/2):
            return True

        # Check all walls (simplified - check if point is too close to wall)
        for obs in self.obstacles:
            if obs['type'] == 'wall':
                # Distance from point to line segment
                x1, y1, x2, y2 = obs['x1'], obs['y1'], obs['x2'], obs['y2']

                # Vector from wall start to point
                dx = x - x1
                dy = y - y1

                # Vector along wall
                wx = x2 - x1
                wy = y2 - y1

                # Length of wall
                wall_length_sq = wx*wx + wy*wy
                if wall_length_sq < 1e-10:
                    continue

                # Project point onto wall line
                t = max(0, min(1, (dx*wx + dy*wy) / wall_length_sq))

                # Closest point on wall segment
                closest_x = x1 + t * wx
                closest_y = y1 + t * wy

                # Distance to closest point
                dist = math.sqrt((x - closest_x)**2 + (y - closest_y)**2)

                if dist < robot_radius + 0.1:  # Small margin
                    return True

            elif obs['type'] == 'box':
                cx, cy, w, h = obs['cx'], obs['cy'], obs['w'], obs['h']
                # Expanded box check (box + robot radius)
                if (abs(x - cx) < w/2 + robot_radius and
                    abs(y - cy) < h/2 + robot_radius):
                    return True

        return False


class SyntheticRobotNode(Node):
    """
    Synthetic robot with degraded sensor and complex environment.

    DEGRADED SENSOR:
    - 240° FOV (blind spot behind)
    - 4.0m max range
    - 2cm noise
    """

    def __init__(self):
        super().__init__('synthetic_robot')

        # Parameters
        self.declare_parameter('start_mode', 'exploration_pattern')
        start_mode = self.get_parameter('start_mode').value

        # Publishers
        self.scan_pub = self.create_publisher(LaserScan, '/scan', 10)
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.mode_pub = self.create_publisher(String, '/robot_mode', 10)
        self.status_pub = self.create_publisher(String, '/exploration_status', 10)

        # TF broadcaster
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)

        # Subscriber for autonomous goals
        self.goal_sub = self.create_subscription(
            PoseStamped,
            '/exploration_goal',
            self.goal_callback,
            10
        )

        # Robot state - START AT ORIGIN (0, 0)
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0  # Facing right (east)
        self.linear_vel = 0.0
        self.angular_vel = 0.0

        # Control parameters
        self.max_linear_vel = 0.4  # m/s (slightly slower for tight spaces)
        self.max_angular_vel = 1.0  # rad/s
        self.linear_accel = 0.5
        self.angular_accel = 0.8

        # Mode
        self.mode = start_mode if start_mode in ('manual', 'autonomous', 'exploration_pattern') else 'manual'
        self.autonomous_goal = None
        self.exploration_pattern_index = 0
        self.exploration_complete = False

        # Stuck detection
        self.waypoint_start_time = None
        self.waypoint_timeout = 30.0
        self.last_position = (self.x, self.y)
        self.stuck_counter = 0
        self.last_stuck_check_time = None

        # Environment
        self.environment = VirtualEnvironment()

        # ===== DEGRADED LASER PARAMETERS =====
        # 240° FOV (±120°) - BLIND SPOT BEHIND
        self.angle_min = -2.0944  # -120 degrees
        self.angle_max = 2.0944   # +120 degrees
        self.angle_increment = 0.01  # ~418 rays

        # REDUCED RANGE: 4.0m
        self.range_min = 0.1
        self.range_max = 4.0

        # Timers
        self.dt = 0.05  # 20 Hz
        self.create_timer(self.dt, self.update_robot)
        self.create_timer(0.1, self.publish_scan)  # 10 Hz scan

        # Keyboard control
        self.cmd_vel = {'linear': 0.0, 'angular': 0.0}

        self.get_logger().info('=== Synthetic Robot Started (COMPLEX ENVIRONMENT) ===')
        self.get_logger().info(f'Mode: {self.mode.upper()}')
        self.get_logger().info('DEGRADED SENSOR:')
        self.get_logger().info(f'  - Laser FOV: 240° (±120°) - BLIND SPOT BEHIND')
        self.get_logger().info(f'  - Max Range: {self.range_max}m (reduced)')
        self.get_logger().info(f'  - Sensor Noise: 2cm std dev')
        self.get_logger().info('ENVIRONMENT: 4 Rooms + Narrow Corridors')
        self.get_logger().info(f'Starting position: ({self.x:.2f}, {self.y:.2f})')

        # Start keyboard listener if TTY available
        if sys.stdin.isatty():
            self.create_timer(0.05, self.check_keyboard)
        else:
            self.get_logger().warn('Keyboard control disabled (no TTY)')

    def goal_callback(self, msg):
        """Receive autonomous exploration goals."""
        self.autonomous_goal = (msg.pose.position.x, msg.pose.position.y)
        if self.mode != 'autonomous':
            self.mode = 'autonomous'
            self.get_logger().info(f'Switching to AUTONOMOUS mode, goal: {self.autonomous_goal}')
            self.publish_mode()

    def check_keyboard(self):
        """Non-blocking keyboard input check."""
        if select.select([sys.stdin], [], [], 0.0)[0]:
            try:
                key = sys.stdin.read(1)
                self.handle_key(key)
            except:
                pass

    def handle_key(self, key):
        """Process keyboard commands."""
        if key == 'w':
            self.cmd_vel['linear'] = self.max_linear_vel
            self.mode = 'manual'
        elif key == 'x':
            self.cmd_vel['linear'] = -self.max_linear_vel
            self.mode = 'manual'
        elif key == 'a':
            self.cmd_vel['angular'] = self.max_angular_vel
            self.mode = 'manual'
        elif key == 'd':
            self.cmd_vel['angular'] = -self.max_angular_vel
            self.mode = 'manual'
        elif key == 's':
            self.cmd_vel['linear'] = 0.0
            self.cmd_vel['angular'] = 0.0
            self.linear_vel = 0.0
            self.angular_vel = 0.0
        elif key == 'm':
            self.mode = 'manual'
            self.autonomous_goal = None
            self.get_logger().info('Switched to MANUAL mode')
            self.publish_mode()
        elif key == 'e':
            self.mode = 'exploration_pattern'
            self.exploration_pattern_index = 0
            self.get_logger().info('Switched to EXPLORATION PATTERN mode')
            self.publish_mode()
        elif key == 'q':
            self.get_logger().info('Quitting...')
            rclpy.shutdown()

    def publish_mode(self):
        """Publish current robot mode."""
        msg = String()
        msg.data = self.mode
        self.mode_pub.publish(msg)

    def update_robot(self):
        """Update robot state based on current mode."""
        if self.mode == 'manual':
            target_linear = self.cmd_vel['linear']
            target_angular = self.cmd_vel['angular']

        elif self.mode == 'autonomous':
            if self.autonomous_goal is None:
                target_linear = 0.0
                target_angular = 0.0
            else:
                target_linear, target_angular = self.compute_control_to_goal(
                    self.autonomous_goal[0], self.autonomous_goal[1]
                )

                # Check if reached goal
                dist = math.sqrt(
                    (self.x - self.autonomous_goal[0])**2 +
                    (self.y - self.autonomous_goal[1])**2
                )
                if dist < 0.3:
                    self.get_logger().info('Goal reached!')
                    self.autonomous_goal = None
                    self.mode = 'manual'
                    self.publish_mode()

        elif self.mode == 'exploration_pattern':
            target_linear, target_angular = self.exploration_pattern()

        else:
            target_linear = 0.0
            target_angular = 0.0

        # Apply acceleration limits
        if target_linear > self.linear_vel:
            self.linear_vel = min(self.linear_vel + self.linear_accel * self.dt, target_linear)
        else:
            self.linear_vel = max(self.linear_vel - self.linear_accel * self.dt, target_linear)

        if target_angular > self.angular_vel:
            self.angular_vel = min(self.angular_vel + self.angular_accel * self.dt, target_angular)
        else:
            self.angular_vel = max(self.angular_vel - self.angular_accel * self.dt, target_angular)

        # Update pose
        new_x = self.x + self.linear_vel * math.cos(self.theta) * self.dt
        new_y = self.y + self.linear_vel * math.sin(self.theta) * self.dt
        new_theta = self.theta + self.angular_vel * self.dt

        # Collision check
        if not self.environment.is_collision(new_x, new_y):
            self.x = new_x
            self.y = new_y
            self.theta = new_theta

        # Publish odometry and TF
        self.publish_odometry()
        self.publish_tf()

    def compute_control_to_goal(self, goal_x, goal_y):
        """Proportional controller to navigate to goal."""
        dx = goal_x - self.x
        dy = goal_y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        angle_to_goal = math.atan2(dy, dx)

        # Angle error
        angle_error = angle_to_goal - self.theta
        while angle_error > math.pi:
            angle_error -= 2 * math.pi
        while angle_error < -math.pi:
            angle_error += 2 * math.pi

        # Control gains
        k_linear = 0.6
        k_angular = 2.0
        angle_threshold = 0.3

        # Rotate in place if large angle error
        if abs(angle_error) > angle_threshold:
            linear = 0.0
            angular = k_angular * angle_error
        else:
            linear = min(k_linear * distance, self.max_linear_vel)
            angular = k_angular * angle_error * 0.5

        # Clamp to limits
        linear = max(-self.max_linear_vel, min(self.max_linear_vel, linear))
        angular = max(-self.max_angular_vel, min(self.max_angular_vel, angular))

        return linear, angular

    def exploration_pattern(self):
        """
        PRE-MAPPED ROUTE through complex multi-room environment.

        Route Logic:
        1. Start at origin (0, 0) in central corridor
        2. Explore central corridor thoroughly
        3. Enter Room 1 (top-left) through doorway
        4. Explore Room 1 completely
        5. Return to corridor, enter Room 2 (top-right)
        6. Explore Room 2 completely
        7. Return to corridor, enter Room 3 (bottom-left)
        8. Explore Room 3 completely
        9. Return to corridor, enter Room 4 (bottom-right)
        10. Explore Room 4 completely
        11. Return to origin
        """
        waypoints = [
            # ===== PHASE 1: CENTRAL CORRIDOR EXPLORATION =====
            # Start at origin, explore central corridor first
            (0.0, 0.0),      # Start position (center of corridor)
            (0.0, 1.0),      # Move north in corridor
            (0.0, 2.0),      # Continue north
            (0.0, 2.5),      # Near north end of corridor
            (0.0, 2.0),      # Back south
            (0.0, 1.0),
            (0.0, 0.0),      # Back to center
            (0.0, -1.0),     # Move south in corridor
            (0.0, -2.0),     # Continue south
            (0.0, -2.5),     # Near south end of corridor
            (0.0, -2.0),     # Back north
            (0.0, -1.0),
            (0.0, 0.0),      # Back to center

            # ===== PHASE 2: ROOM 1 (TOP-LEFT) =====
            # Navigate through left doorway (at y ≈ 0, x = -2.0 to -0.5)
            (-0.5, 0.0),     # Approach left doorway from corridor
            (-1.0, 0.0),     # In doorway
            (-1.5, 0.0),     # Through doorway into Room 1 area
            (-2.2, 0.0),     # Fully in Room 1 (past the wall at x=-2.0)

            # Explore Room 1 systematically
            (-2.5, 0.5),     # Start exploration pattern
            (-3.0, 0.5),
            (-3.5, 0.5),
            (-4.0, 0.5),
            (-4.0, 1.0),
            (-3.5, 1.0),
            (-3.0, 1.0),     # Around box at (-3.5, 1.0)
            (-2.5, 1.0),
            (-2.5, 1.5),
            (-3.0, 1.5),
            (-3.5, 1.5),
            (-4.0, 1.5),
            (-4.0, 2.0),
            (-3.5, 2.0),     # Around U-shape (bottom opening)
            (-3.0, 2.5),
            (-3.5, 2.5),
            (-4.0, 2.5),
            (-4.0, 3.0),
            (-3.5, 3.0),
            (-3.0, 3.0),
            (-2.5, 3.0),
            (-2.5, 3.5),
            (-3.0, 3.5),
            (-3.5, 3.5),     # Near U-shape top
            (-4.0, 3.5),
            (-4.0, 4.0),
            (-3.5, 4.0),
            (-3.0, 4.0),
            (-2.5, 4.0),

            # Exit Room 1 back to corridor
            (-2.2, 2.0),
            (-1.5, 1.0),
            (-1.0, 0.5),
            (-0.5, 0.0),
            (0.0, 0.0),      # Back in central corridor

            # ===== PHASE 3: ROOM 2 (TOP-RIGHT) =====
            # Navigate through right doorway (at y ≈ 0, x = 1.5 to beyond)
            (0.5, 0.0),      # Approach right doorway
            (1.0, 0.0),      # In doorway area
            (1.7, 0.0),      # Through doorway into Room 2 area
            (2.5, 0.0),      # Fully in Room 2 (past wall at x=1.5)

            # Navigate through Room 2's internal corridor opening (x = 2.25 to 3.75)
            (2.5, 0.2),      # Approach corridor opening
            (3.0, 0.3),      # In corridor opening
            (3.5, 0.5),      # Through corridor into top section of Room 2

            # Explore Room 2 top section
            (3.0, 0.8),
            (3.5, 0.8),
            (4.0, 0.8),
            (4.5, 0.8),
            (4.5, 1.2),
            (4.0, 1.2),
            (3.5, 1.2),      # Around box at (3.5, 1.0)
            (3.0, 1.2),
            (3.0, 1.6),
            (3.5, 1.6),
            (4.0, 1.6),
            (4.5, 1.6),
            (4.5, 2.0),
            (4.0, 2.0),
            (3.5, 2.0),      # Around U-shape (bottom opening)
            (3.0, 2.5),
            (3.5, 2.5),
            (4.0, 2.5),
            (4.5, 2.5),
            (4.5, 3.0),
            (4.0, 3.0),
            (3.5, 3.0),
            (3.0, 3.5),
            (3.5, 3.5),      # Near U-shape
            (4.0, 3.5),
            (4.5, 3.5),
            (4.5, 4.0),
            (4.0, 4.0),
            (3.5, 4.0),
            (3.0, 4.0),

            # Exit Room 2 back to corridor
            (3.0, 0.5),
            (2.5, 0.3),
            (2.0, 0.0),
            (1.5, 0.0),
            (1.0, 0.0),
            (0.5, 0.0),
            (0.0, 0.0),      # Back in central corridor

            # ===== PHASE 4: ROOM 3 (BOTTOM-LEFT) =====
            # Through left doorway, then through Room 3's corridor opening
            (-0.5, 0.0),
            (-1.0, 0.0),
            (-1.5, 0.0),
            (-2.2, 0.0),     # In Room 3 area
            (-2.5, -0.3),    # Approach Room 3's corridor opening (x = -2.75 to -1.25)
            (-2.2, -0.5),    # In corridor opening area (to Room 3 bottom section)

            # Explore Room 3 bottom section
            (-2.5, -1.0),
            (-3.0, -1.0),
            (-3.5, -1.0),
            (-4.0, -1.0),
            (-4.0, -1.5),
            (-3.5, -1.5),
            (-3.0, -1.5),    # Around L-shape at (-3.0, -2.0)
            (-2.5, -1.5),
            (-2.5, -2.0),
            (-3.0, -2.5),
            (-3.5, -2.5),
            (-4.0, -2.5),
            (-4.0, -3.0),
            (-3.5, -3.0),
            (-3.0, -3.0),
            (-2.5, -3.0),
            (-2.5, -3.5),
            (-3.0, -3.5),
            (-3.5, -3.5),    # Around box at (-3.5, -3.5)
            (-4.0, -3.5),
            (-4.0, -4.0),
            (-3.5, -4.0),
            (-3.0, -4.0),
            (-2.5, -4.0),

            # Exit Room 3 back to corridor
            (-2.2, -2.0),
            (-1.5, -1.0),
            (-1.0, -0.5),
            (-0.5, 0.0),
            (0.0, 0.0),      # Back in central corridor

            # ===== PHASE 5: ROOM 4 (BOTTOM-RIGHT) =====
            # Through right doorway, then through Room 4's corridor opening
            (0.5, 0.0),
            (1.0, 0.0),
            (1.7, 0.0),
            (2.5, 0.0),      # In Room 4 area
            (3.0, -0.3),     # Approach Room 4's corridor opening (x = 2.25 to 3.75)
            (3.5, -0.5),     # Through corridor opening into Room 4 bottom section

            # Explore Room 4 bottom section
            (3.0, -1.0),
            (3.5, -1.0),
            (4.0, -1.0),
            (4.5, -1.0),
            (4.5, -1.5),
            (4.0, -1.5),
            (3.5, -1.5),
            (3.0, -1.5),     # Around L-shape at (3.0, -2.0)
            (3.0, -2.0),
            (3.5, -2.5),
            (4.0, -2.5),
            (4.5, -2.5),
            (4.5, -3.0),
            (4.0, -3.0),
            (3.5, -3.0),
            (3.0, -3.0),
            (3.0, -3.5),
            (3.5, -3.5),     # Around box at (3.5, -3.5)
            (4.0, -3.5),
            (4.5, -3.5),
            (4.5, -4.0),
            (4.0, -4.0),
            (3.5, -4.0),
            (3.0, -4.0),

            # ===== PHASE 6: RETURN TO ORIGIN =====
            # Exit Room 4 and return to starting position
            (3.0, -2.0),
            (2.5, -1.0),
            (2.0, -0.5),
            (1.5, 0.0),
            (1.0, 0.0),
            (0.5, 0.0),
            (0.0, 0.0),      # Final position: back at origin
        ]

        # Get total waypoints
        total_wp = len(waypoints)

        # Initialize waypoint timer on first call
        if self.waypoint_start_time is None:
            self.waypoint_start_time = self.get_clock().now().nanoseconds / 1e9

        # Current target
        target = waypoints[self.exploration_pattern_index % total_wp]

        # Distance to target
        dist = math.sqrt((self.x - target[0])**2 + (self.y - target[1])**2)

        # Stuck detection
        current_time = self.get_clock().now().nanoseconds / 1e9
        time_at_waypoint = current_time - self.waypoint_start_time

        if self.last_stuck_check_time is None:
            self.last_stuck_check_time = current_time

        time_since_last_check = current_time - self.last_stuck_check_time

        if time_since_last_check >= 8.0:
            position_change = math.sqrt((self.x - self.last_position[0])**2 +
                                       (self.y - self.last_position[1])**2)

            if position_change < 0.15:
                self.stuck_counter += 1
                self.get_logger().warn(f'⚠️ Robot stuck at waypoint {self.exploration_pattern_index}! Skipping...')
                self.exploration_pattern_index += 1
                self.waypoint_start_time = current_time
                self.last_position = (self.x, self.y)
                self.last_stuck_check_time = current_time
                target = waypoints[self.exploration_pattern_index % total_wp]
            else:
                self.last_position = (self.x, self.y)
                self.last_stuck_check_time = current_time

        # Timeout
        if time_at_waypoint > self.waypoint_timeout:
            self.get_logger().warn(f'⏱️ Waypoint {self.exploration_pattern_index} timeout! Skipping...')
            self.exploration_pattern_index += 1
            self.waypoint_start_time = current_time
            self.last_position = (self.x, self.y)
            self.last_stuck_check_time = current_time
            target = waypoints[self.exploration_pattern_index % total_wp]

        # If reached waypoint
        if dist < 0.3:  # Tolerance
            self.exploration_pattern_index += 1
            current_wp = self.exploration_pattern_index
            progress = (current_wp / total_wp) * 100

            self.waypoint_start_time = current_time
            self.last_position = (self.x, self.y)

            self.get_logger().info(f'✅ Progress: {progress:.1f}% - Waypoint {current_wp}/{total_wp} at ({self.x:.2f}, {self.y:.2f})')

            # Check if completed
            if current_wp >= total_wp and not self.exploration_complete:
                self.exploration_complete = True
                self.get_logger().info('')
                self.get_logger().info('='*60)
                self.get_logger().info('🎉 ✅ EXPLORATION 100% COMPLETE!')
                self.get_logger().info('='*60)
                self.get_logger().info(f'Total waypoints: {total_wp}')
                self.get_logger().info(f'Skipped waypoints: {self.stuck_counter}')
                self.get_logger().info('📊 Generating results in 30 seconds...')
                self.get_logger().info('='*60)

                # Publish completion
                status_msg = String()
                status_msg.data = 'COMPLETE'
                self.status_pub.publish(status_msg)

                return 0.0, 0.0

            target = waypoints[self.exploration_pattern_index % total_wp]

        # If already complete, stay stopped
        if self.exploration_complete:
            return 0.0, 0.0

        # Log progress periodically
        if not hasattr(self, '_exploration_counter'):
            self._exploration_counter = 0
        self._exploration_counter += 1
        if self._exploration_counter % 50 == 0:
            self.get_logger().info(f'→ Waypoint {self.exploration_pattern_index % total_wp + 1}/{total_wp}: target={target}, dist={dist:.2f}m')

        # Compute control
        return self.compute_control_to_goal(target[0], target[1])

    def publish_scan(self):
        """
        Generate and publish laser scan.

        DEGRADED SENSOR:
        - 240° FOV (±120°)
        - 4.0m max range
        - 2cm noise
        """
        scan = LaserScan()
        scan.header.stamp = self.get_clock().now().to_msg()
        scan.header.frame_id = 'base_footprint'

        scan.angle_min = self.angle_min      # -120°
        scan.angle_max = self.angle_max      # +120°
        scan.angle_increment = self.angle_increment
        scan.range_min = self.range_min
        scan.range_max = self.range_max      # 4.0m

        # Generate ranges
        ranges = []
        num_rays = int((self.angle_max - self.angle_min) / self.angle_increment)

        for i in range(num_rays):
            angle = self.angle_min + i * self.angle_increment
            world_angle = self.theta + angle
            distance = self.environment.raycast(self.x, self.y, world_angle, self.range_max)
            ranges.append(float(distance))

        scan.ranges = ranges
        self.scan_pub.publish(scan)

    def publish_odometry(self):
        """Publish odometry message."""
        odom = Odometry()
        odom.header.stamp = self.get_clock().now().to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_footprint'

        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0

        odom.pose.pose.orientation.x = 0.0
        odom.pose.pose.orientation.y = 0.0
        odom.pose.pose.orientation.z = math.sin(self.theta / 2)
        odom.pose.pose.orientation.w = math.cos(self.theta / 2)

        odom.twist.twist.linear.x = self.linear_vel
        odom.twist.twist.angular.z = self.angular_vel

        self.odom_pub.publish(odom)

    def publish_tf(self):
        """Publish TF transforms."""
        now = self.get_clock().now().to_msg()

        # map -> odom
        t1 = TransformStamped()
        t1.header.stamp = now
        t1.header.frame_id = 'map'
        t1.child_frame_id = 'odom'
        t1.transform.translation.x = 0.0
        t1.transform.translation.y = 0.0
        t1.transform.translation.z = 0.0
        t1.transform.rotation.w = 1.0

        # odom -> base_footprint
        t2 = TransformStamped()
        t2.header.stamp = now
        t2.header.frame_id = 'odom'
        t2.child_frame_id = 'base_footprint'
        t2.transform.translation.x = self.x
        t2.transform.translation.y = self.y
        t2.transform.translation.z = 0.0
        t2.transform.rotation.x = 0.0
        t2.transform.rotation.y = 0.0
        t2.transform.rotation.z = math.sin(self.theta / 2)
        t2.transform.rotation.w = math.cos(self.theta / 2)

        # base_footprint -> base_scan
        t3 = TransformStamped()
        t3.header.stamp = now
        t3.header.frame_id = 'base_footprint'
        t3.child_frame_id = 'base_scan'
        t3.transform.translation.x = 0.0
        t3.transform.translation.y = 0.0
        t3.transform.translation.z = 0.2
        t3.transform.rotation.w = 1.0

        self.tf_broadcaster.sendTransform([t1, t2, t3])


def main(args=None):
    """Main entry point."""
    old_settings = None
    if sys.stdin.isatty():
        try:
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
        except Exception as e:
            print(f"Warning: Could not set terminal to raw mode: {e}")

    try:
        rclpy.init(args=args)
        node = SyntheticRobotNode()

        try:
            rclpy.spin(node)
        except KeyboardInterrupt:
            pass
        finally:
            node.destroy_node()
            rclpy.shutdown()

    finally:
        if old_settings is not None:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            except Exception:
                pass


if __name__ == '__main__':
    main()
