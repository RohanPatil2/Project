#!/usr/bin/env python3
"""
Synthetic Robot Data Generator for Uncertainty-Aware SLAM Testing
COMPLEX ENVIRONMENT VERSION with DEGRADED SENSOR and AUTONOMOUS NAVIGATION.

Features:
- 10m×10m complex layout with internal walls, multiple rooms, narrow corridors
- U-shaped obstacles creating occlusions
- 240-degree frontal FOV laser (DEGRADED - realistic blind spots)
- 4.0m max range (DEGRADED - limited visibility)
- Realistic 2cm sensor noise (Gaussian)
- AUTONOMOUS NAVIGATION with /cmd_vel publishing
- Pre-planned waypoints covering all rooms
- Stuck detection and automatic waypoint skipping

Author: Rohan Upendra Patil
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
    """Simulates a COMPLEX 2D environment with multiple rooms and occlusions."""

    def __init__(self, width=10.0, height=10.0):
        self.width = width
        self.height = height
        self.obstacles = []
        self._create_complex_environment()

    def _create_complex_environment(self):
        """
        Create a COMPLEX environment with internal walls, multiple rooms,
        narrow corridors, and U-shaped obstacles.

        Layout (10m × 10m):
        ┌──────────────────────────────────────┐
        │         │ Corridor │                 │
        │ Room 1  │──────────│    Room 2       │
        │   ┌─┐   │          │      ┌─┐        │
        │   │U│   │          │      │U│        │
        ├───┴─┴───┤          ├──────┴─┴────────┤
        │         Door       │                 │
        │ Room 3  │          │    Room 4       │
        │    ┌┐   │          │       ┌┐        │
        │    └┘   │          │       └┘        │
        └─────────┴──────────┴─────────────────┘

        4 Rooms + Central Corridor + Narrow Doorways + U-shaped obstacles
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
        self.obstacles.append({'type': 'wall', 'x1': -0.5, 'y1': 3.0, 'x2': -0.5, 'y2': 0.75})   # Left corridor wall (top)
        self.obstacles.append({'type': 'wall', 'x1': -0.5, 'y1': -0.75, 'x2': -0.5, 'y2': -3.0}) # Left corridor wall (bottom)
        self.obstacles.append({'type': 'wall', 'x1': 0.5, 'y1': 3.0, 'x2': 0.5, 'y2': 0.75})     # Right corridor wall (top)
        self.obstacles.append({'type': 'wall', 'x1': 0.5, 'y1': -0.75, 'x2': 0.5, 'y2': -3.0})   # Right corridor wall (bottom)
        # This creates a 1.0m wide central corridor passage

        # ===== U-SHAPED OBSTACLES (Create shadow zones for entropy variation) =====

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

        DEGRADED SENSOR SPECIFICATIONS:
        - Max range: 4.0m (LIMITED visibility)
        - Realistic noise: 2cm std dev (Gaussian)
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

        # Realistic sensor noise (2cm std dev Gaussian)
        noise = np.random.normal(0.0, 0.02)
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
    Synthetic robot with DEGRADED sensor in COMPLEX environment.

    COMPLETE AUTONOMOUS NAVIGATION with /cmd_vel publishing.

    DEGRADED SENSOR SPECIFICATIONS:
    - 240° frontal FOV (REALISTIC - has blind spots behind)
    - 4.0m max range (LIMITED visibility)
    - 2cm realistic noise (Gaussian)
    - 628 laser rays
    - 10 Hz scan rate

    ENVIRONMENT:
    - 10m×10m boundary
    - 4 rooms with internal walls
    - Narrow corridors (1.0-1.5m wide)
    - U-shaped and L-shaped obstacles
    - Multiple occlusion zones

    AUTONOMOUS NAVIGATION:
    - Hard-coded waypoints covering all rooms
    - /cmd_vel publisher for velocity commands
    - Proportional controller for waypoint following
    - 0.35m waypoint reach tolerance
    - Stuck detection: 0.15m in 8 seconds
    - Automatic waypoint skipping when stuck
    """

    def __init__(self):
        super().__init__('synthetic_robot')

        # Parameters
        self.declare_parameter('robot_mode', 'EXPLORATION_PATTERN')
        robot_mode = self.get_parameter('robot_mode').value

        # Publishers
        self.scan_pub = self.create_publisher(LaserScan, '/scan', 10)
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)  # NEW: /cmd_vel publisher
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
        self.max_linear_vel = 0.35  # m/s (slower for complex environment)
        self.max_angular_vel = 1.0  # rad/s
        self.linear_accel = 0.4
        self.angular_accel = 0.8

        # Mode
        self.mode = robot_mode.upper() if robot_mode.upper() in ('MANUAL', 'AUTONOMOUS', 'EXPLORATION_PATTERN') else 'EXPLORATION_PATTERN'
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
        # 240° FRONTAL FOV (realistic - has blind spots)
        self.angle_min = -2.0944  # -120 degrees (-2π/3 radians)
        self.angle_max = 2.0944   # +120 degrees (+2π/3 radians)
        self.angle_increment = (self.angle_max - self.angle_min) / 628  # 628 rays

        # SHORT RANGE: 4.0m (DEGRADED visibility)
        self.range_min = 0.1
        self.range_max = 4.0

        # Timers
        self.dt = 0.05  # 20 Hz
        self.create_timer(self.dt, self.update_robot)
        self.create_timer(0.1, self.publish_scan)  # 10 Hz scan
        self.create_timer(0.02, self.publish_tf)  # 50 Hz TF publishing

        # Keyboard control
        self.cmd_vel = {'linear': 0.0, 'angular': 0.0}

        # Waypoints for exploration
        self.waypoints = self._create_exploration_waypoints()

        self.get_logger().info('=== Synthetic Robot Started (COMPLEX ENVIRONMENT) ===')
        self.get_logger().info(f'Mode: {self.mode}')
        self.get_logger().info('DEGRADED SENSOR CONFIGURATION:')
        self.get_logger().info(f'  - Laser FOV: 240° (FRONTAL - realistic blind spots)')
        self.get_logger().info(f'  - Max Range: {self.range_max}m (DEGRADED)')
        self.get_logger().info(f'  - Sensor Noise: 2cm std dev (Gaussian)')
        self.get_logger().info('ENVIRONMENT: 10m×10m Complex Multi-Room with Occlusions')
        self.get_logger().info(f'Starting position: ({self.x:.2f}, {self.y:.2f})')
        self.get_logger().info(f'Total waypoints: {len(self.waypoints)}')

        # Start keyboard listener if TTY available
        if sys.stdin.isatty():
            self.create_timer(0.05, self.check_keyboard)
        else:
            self.get_logger().warn('Keyboard control disabled (no TTY)')

    def _create_exploration_waypoints(self):
        """
        Create a LOGICAL EXPLORATION PATH that visits ALL ROOMS in the complex environment.

        Strategy:
        1. Start at origin (0, 0)
        2. Explore central corridor
        3. Enter and explore Room 1 (top-left)
        4. Return to corridor and explore Room 2 (top-right)
        5. Return to corridor and explore Room 3 (bottom-left)
        6. Return to corridor and explore Room 4 (bottom-right)
        7. Final sweep of central corridor
        8. Return to origin

        Each room is thoroughly explored to reduce entropy.
        """
        waypoints = [
            # ===== PHASE 1: STARTING POSITION =====
            (0.0, 0.0),      # Origin

            # ===== PHASE 2: CENTRAL CORRIDOR EXPLORATION =====
            (-0.2, 0.5),     # Move into central corridor
            (-0.2, 1.0),
            (-0.2, 1.5),
            (-0.2, 2.0),
            (-0.2, 2.5),     # Top of central corridor
            (0.0, 2.0),
            (0.2, 1.5),
            (0.2, 1.0),
            (0.2, 0.5),
            (0.0, 0.0),      # Return to center doorway

            # ===== PHASE 3: ROOM 1 EXPLORATION (Top-Left) =====
            (-1.0, 0.3),     # Approach Room 1 doorway
            (-2.0, 0.3),     # Enter doorway
            (-2.5, 0.5),     # Inside Room 1
            (-3.0, 1.0),     # Explore corners
            (-4.0, 1.5),
            (-4.2, 2.0),
            (-4.2, 2.5),
            (-3.5, 2.8),     # Approach U-shape obstacle
            (-3.5, 3.2),     # Around U-shape
            (-3.0, 3.0),
            (-3.5, 2.5),
            (-4.0, 3.0),
            (-3.0, 2.0),
            (-2.5, 1.5),
            (-3.5, 1.2),     # Box obstacle area
            (-2.8, 0.8),
            (-3.5, 3.5),     # Far corner
            (-4.0, 4.0),
            (-4.5, 4.5),     # Maximum coverage
            (-3.0, 4.0),
            (-2.5, 3.5),
            (-2.0, 2.5),
            (-2.0, 0.3),     # Exit doorway
            (0.0, 0.0),      # Return to center

            # ===== PHASE 4: ROOM 2 EXPLORATION (Top-Right) =====
            (1.0, 0.3),      # Approach Room 2 doorway
            (1.5, 0.3),      # Enter doorway
            (2.0, 0.5),      # Inside Room 2
            (2.5, 1.0),
            (3.0, 1.5),
            (3.5, 2.0),
            (4.0, 2.5),
            (4.2, 3.0),
            (3.5, 3.2),      # Approach U-shape obstacle
            (3.5, 2.8),      # Around U-shape
            (3.0, 3.0),
            (3.5, 2.5),
            (4.0, 3.0),
            (3.0, 2.0),
            (2.5, 1.5),
            (3.5, 1.2),      # Box obstacle area
            (2.8, 0.8),
            (3.5, 3.5),      # Far corner
            (4.0, 4.0),
            (4.5, 4.5),      # Maximum coverage
            (3.0, 4.0),
            (2.5, 3.5),
            (2.0, 2.5),
            (1.5, 0.3),      # Exit doorway
            (0.0, 0.0),      # Return to center

            # ===== PHASE 5: CENTRAL CORRIDOR (Bottom Half) =====
            (-0.2, -0.5),
            (-0.2, -1.0),
            (-0.2, -1.5),
            (-0.2, -2.0),
            (-0.2, -2.5),    # Bottom of central corridor
            (0.0, -2.0),
            (0.2, -1.5),
            (0.2, -1.0),
            (0.2, -0.5),
            (0.0, 0.0),      # Return to center

            # ===== PHASE 6: ROOM 3 EXPLORATION (Bottom-Left) =====
            (-1.0, -0.3),    # Approach Room 3 doorway
            (-2.0, -0.3),    # Enter doorway
            (-2.5, -0.5),    # Inside Room 3
            (-3.0, -1.0),
            (-3.5, -1.5),
            (-4.0, -2.0),
            (-4.5, -2.5),
            (-4.2, -3.0),
            (-4.0, -3.5),    # L-shape obstacle area
            (-3.5, -2.5),
            (-3.0, -2.2),
            (-3.2, -3.0),
            (-3.5, -3.5),    # Box obstacle area
            (-2.8, -3.2),
            (-4.0, -4.0),    # Far corner
            (-4.5, -4.5),    # Maximum coverage
            (-3.5, -4.0),
            (-3.0, -3.5),
            (-2.5, -3.0),
            (-2.5, -2.0),
            (-2.0, -0.3),    # Exit doorway
            (0.0, 0.0),      # Return to center

            # ===== PHASE 7: ROOM 4 EXPLORATION (Bottom-Right) =====
            (1.0, -0.3),     # Approach Room 4 doorway
            (1.5, -0.3),     # Enter doorway
            (2.0, -0.5),     # Inside Room 4
            (2.5, -1.0),
            (3.0, -1.5),
            (3.5, -2.0),
            (4.0, -2.5),
            (4.5, -3.0),
            (4.2, -3.5),
            (3.5, -2.5),     # L-shape obstacle area
            (3.0, -2.2),
            (3.2, -3.0),
            (3.5, -3.5),     # Box obstacle area
            (2.8, -3.2),
            (4.0, -4.0),     # Far corner
            (4.5, -4.5),     # Maximum coverage
            (3.5, -4.0),
            (3.0, -3.5),
            (2.5, -3.0),
            (2.5, -2.0),
            (1.5, -0.3),     # Exit doorway
            (0.0, 0.0),      # Return to center

            # ===== PHASE 8: FINAL CORRIDOR SWEEP =====
            (-0.3, 2.0),
            (0.3, 2.0),
            (-0.3, -2.0),
            (0.3, -2.0),
            (0.0, 0.0),      # Final position: origin
        ]

        return waypoints

    def goal_callback(self, msg):
        """Receive autonomous exploration goals."""
        self.autonomous_goal = (msg.pose.position.x, msg.pose.position.y)
        if self.mode != 'AUTONOMOUS':
            self.mode = 'AUTONOMOUS'
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
            self.mode = 'MANUAL'
        elif key == 'x':
            self.cmd_vel['linear'] = -self.max_linear_vel
            self.mode = 'MANUAL'
        elif key == 'a':
            self.cmd_vel['angular'] = self.max_angular_vel
            self.mode = 'MANUAL'
        elif key == 'd':
            self.cmd_vel['angular'] = -self.max_angular_vel
            self.mode = 'MANUAL'
        elif key == 's':
            self.cmd_vel['linear'] = 0.0
            self.cmd_vel['angular'] = 0.0
            self.linear_vel = 0.0
            self.angular_vel = 0.0
        elif key == 'm':
            self.mode = 'MANUAL'
            self.autonomous_goal = None
            self.get_logger().info('Switched to MANUAL mode')
            self.publish_mode()
        elif key == 'e':
            self.mode = 'EXPLORATION_PATTERN'
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
        """
        Update robot state based on current mode.

        NEW: Publishes Twist messages to /cmd_vel for autonomous navigation.
        """
        if self.mode == 'MANUAL':
            target_linear = self.cmd_vel['linear']
            target_angular = self.cmd_vel['angular']

        elif self.mode == 'AUTONOMOUS':
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
                if dist < 0.35:  # 0.35m tolerance
                    self.get_logger().info('Goal reached!')
                    self.autonomous_goal = None
                    self.mode = 'MANUAL'
                    self.publish_mode()

        elif self.mode == 'EXPLORATION_PATTERN':
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

        # NEW: Publish /cmd_vel for autonomous navigation
        cmd_msg = Twist()
        cmd_msg.linear.x = self.linear_vel
        cmd_msg.angular.z = self.angular_vel
        self.cmd_vel_pub.publish(cmd_msg)

        # Publish odometry (TF is published separately at higher rate)
        self.publish_odometry()

    def compute_control_to_goal(self, goal_x, goal_y):
        """
        Proportional controller to navigate to goal.

        Calculates distance and angle to waypoint.
        Returns linear and angular velocities.
        """
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
        k_linear = 0.5
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
        AUTONOMOUS WAYPOINT FOLLOWING with stuck detection.

        Features:
        - Follows hard-coded waypoints
        - 0.35m waypoint tolerance
        - Stuck detection: 0.15m in 8 seconds
        - Automatic waypoint skipping
        - Progress tracking
        """
        total_wp = len(self.waypoints)

        # Initialize waypoint timer on first call
        if self.waypoint_start_time is None:
            self.waypoint_start_time = self.get_clock().now().nanoseconds / 1e9

        # Check if exploration complete
        if self.exploration_pattern_index >= total_wp:
            if not self.exploration_complete:
                self.exploration_complete = True
                self.get_logger().info('')
                self.get_logger().info('='*60)
                self.get_logger().info('🎉 ✅ EXPLORATION 100% COMPLETE!')
                self.get_logger().info('='*60)
                self.get_logger().info(f'Total waypoints: {total_wp}')
                self.get_logger().info(f'Skipped waypoints: {self.stuck_counter}')
                self.get_logger().info('📊 Results should be generated automatically')
                self.get_logger().info('='*60)

                # Publish completion
                status_msg = String()
                status_msg.data = 'COMPLETE'
                self.status_pub.publish(status_msg)

            return 0.0, 0.0

        # Current target
        target = self.waypoints[self.exploration_pattern_index]

        # Distance to target
        dist = math.sqrt((self.x - target[0])**2 + (self.y - target[1])**2)

        # Stuck detection
        current_time = self.get_clock().now().nanoseconds / 1e9
        time_at_waypoint = current_time - self.waypoint_start_time

        if self.last_stuck_check_time is None:
            self.last_stuck_check_time = current_time

        time_since_last_check = current_time - self.last_stuck_check_time

        # Check if stuck: no 0.15m movement in 8 seconds
        if time_since_last_check >= 8.0:
            position_change = math.sqrt((self.x - self.last_position[0])**2 +
                                       (self.y - self.last_position[1])**2)

            if position_change < 0.15:
                self.stuck_counter += 1
                self.get_logger().warn(f'⚠️ Robot stuck at waypoint {self.exploration_pattern_index + 1}! Skipping...')
                self.exploration_pattern_index += 1
                self.waypoint_start_time = current_time
                self.last_position = (self.x, self.y)
                self.last_stuck_check_time = current_time

                if self.exploration_pattern_index < total_wp:
                    target = self.waypoints[self.exploration_pattern_index]
            else:
                self.last_position = (self.x, self.y)
                self.last_stuck_check_time = current_time

        # Timeout
        if time_at_waypoint > self.waypoint_timeout:
            self.get_logger().warn(f'⏱️ Waypoint {self.exploration_pattern_index + 1} timeout! Skipping...')
            self.exploration_pattern_index += 1
            self.waypoint_start_time = current_time
            self.last_position = (self.x, self.y)
            self.last_stuck_check_time = current_time

            if self.exploration_pattern_index < total_wp:
                target = self.waypoints[self.exploration_pattern_index]

        # If reached waypoint (0.35m tolerance)
        if dist < 0.35:
            self.exploration_pattern_index += 1
            current_wp = self.exploration_pattern_index
            progress = (current_wp / total_wp) * 100

            self.waypoint_start_time = current_time
            self.last_position = (self.x, self.y)
            self.last_stuck_check_time = current_time

            self.get_logger().info(f'✓ Waypoint {current_wp}/{total_wp} | Progress: {progress:.1f}%')

            if self.exploration_pattern_index >= total_wp:
                return 0.0, 0.0

            target = self.waypoints[self.exploration_pattern_index]

        # Log progress periodically
        if not hasattr(self, '_exploration_counter'):
            self._exploration_counter = 0
        self._exploration_counter += 1
        if self._exploration_counter % 100 == 0:
            self.get_logger().info(f'→ Waypoint {self.exploration_pattern_index + 1}/{total_wp}: target={target}, dist={dist:.2f}m')

        # Compute control
        return self.compute_control_to_goal(target[0], target[1])

    def publish_scan(self):
        """
        Generate and publish laser scan.

        DEGRADED SENSOR:
        - 240° frontal FOV (realistic blind spots)
        - 4.0m max range
        - 2cm Gaussian noise
        """
        # Publish TF first to ensure frames are available
        self.publish_tf()

        scan = LaserScan()
        scan.header.stamp = self.get_clock().now().to_msg()
        scan.header.frame_id = 'base_scan'

        scan.angle_min = self.angle_min      # -120°
        scan.angle_max = self.angle_max      # +120°
        scan.angle_increment = self.angle_increment
        scan.range_min = self.range_min
        scan.range_max = self.range_max      # 4.0m (DEGRADED)

        # Generate ranges using np.linspace for exact 628 rays
        angles = np.linspace(self.angle_min, self.angle_max, 628)
        ranges = []

        for angle in angles:
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
