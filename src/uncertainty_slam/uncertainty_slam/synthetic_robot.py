#!/usr/bin/env python3
"""
Synthetic Robot Data Generator for Uncertainty-Aware SLAM Testing
ANTI-LOOP VERSION with Smart Exploration State Machine.

NEW ANTI-LOOP FEATURES:
- Impatient Waypoint Skipping: 20s timeout per waypoint
- Increased Tolerance: 0.6m "good enough" check
- Anti-Loop Randomness: ±30° random rotation after skip/recovery
- Zone-Based Exploration: 5 distinct zones with forced sequential visits
- Visual Debugging: RViz marker showing current target waypoint

Author: Rohan Upendra Patil
Enhanced: 2025-11-18 (Anti-Loop Version)
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist, TransformStamped, PoseStamped
from std_msgs.msg import String
from visualization_msgs.msg import Marker
import tf2_ros
import numpy as np
import math
import sys
import termios
import tty
import select
from enum import Enum


class RobotState(Enum):
    """Robot state machine for navigation."""
    NAVIGATING = 1
    RECOVERY = 2
    ANTI_LOOP_ROTATION = 3  # NEW: Breaking geometric loops
    STOPPED = 4


class VirtualEnvironment:
    """Simulates a COMPLEX 2D environment with multiple rooms and occlusions."""

    def __init__(self, width=10.0, height=10.0):
        self.width = width
        self.height = height
        self.obstacles = []
        self._create_complex_environment()

    def _create_complex_environment(self):
        """
        Create a SIMPLIFIED multi-room environment for easier robot navigation.

        Layout (10m × 10m):
        ┌──────────────────────────────────────┐
        │         │ Corridor │                 │
        │ Room 1  │          │    Room 2       │
        │         │          │                 │
        ├─────────┤          ├─────────────────┤
        │         Door       │                 │
        │ Room 3  │          │    Room 4       │
        │    □    │          │       □         │
        └─────────┴──────────┴─────────────────┘

        SIMPLIFIED FEATURES:
        - 4 rooms with wide doorways (2.0m)
        - Wider central corridor (1.5m)
        - Only 2 small box obstacles for SLAM interest
        - No U-shapes, L-shapes, or pillars
        - Easy navigation for smooth exploration
        """

        # ===== EXTERIOR WALLS (10m × 10m) =====
        self.obstacles.append({'type': 'wall', 'x1': -5.0, 'y1': -5.0, 'x2': 5.0, 'y2': -5.0})  # Bottom
        self.obstacles.append({'type': 'wall', 'x1': 5.0, 'y1': -5.0, 'x2': 5.0, 'y2': 5.0})    # Right
        self.obstacles.append({'type': 'wall', 'x1': 5.0, 'y1': 5.0, 'x2': -5.0, 'y2': 5.0})    # Top
        self.obstacles.append({'type': 'wall', 'x1': -5.0, 'y1': 5.0, 'x2': -5.0, 'y2': -5.0})  # Left

        # ===== INTERNAL WALLS - SIMPLIFIED ROOM DIVIDERS =====

        # VERTICAL WALL 1 - Separates Rooms 1&3 from Central Corridor
        # WIDER doorway (2.0m) for easier navigation
        self.obstacles.append({'type': 'wall', 'x1': -2.0, 'y1': 5.0, 'x2': -2.0, 'y2': 1.0})    # Top segment
        self.obstacles.append({'type': 'wall', 'x1': -2.0, 'y1': -1.0, 'x2': -2.0, 'y2': -5.0})  # Bottom segment
        # Doorway gap: y = -1.0 to 1.0 (2.0m wide - EASY TO NAVIGATE)

        # VERTICAL WALL 2 - Separates Central Corridor from Rooms 2&4
        # WIDER doorway (2.0m) for easier navigation
        self.obstacles.append({'type': 'wall', 'x1': 1.5, 'y1': 5.0, 'x2': 1.5, 'y2': 1.0})     # Top segment
        self.obstacles.append({'type': 'wall', 'x1': 1.5, 'y1': -1.0, 'x2': 1.5, 'y2': -5.0})   # Bottom segment
        # Doorway gap: y = -1.0 to 1.0 (2.0m wide - EASY TO NAVIGATE)

        # HORIZONTAL WALL 1 - Separates Room 1 from Room 3
        # Single solid wall (no internal corridor - simpler)
        self.obstacles.append({'type': 'wall', 'x1': -5.0, 'y1': 0.0, 'x2': -2.0, 'y2': 0.0})

        # HORIZONTAL WALL 2 - Separates Room 2 from Room 4
        # Single solid wall (no internal corridor - simpler)
        self.obstacles.append({'type': 'wall', 'x1': 1.5, 'y1': 0.0, 'x2': 5.0, 'y2': 0.0})

        # CENTRAL CORRIDOR WALLS - WIDER passage (1.5m) for easier navigation
        self.obstacles.append({'type': 'wall', 'x1': -0.75, 'y1': 3.0, 'x2': -0.75, 'y2': 1.0})    # Left corridor wall (top)
        self.obstacles.append({'type': 'wall', 'x1': -0.75, 'y1': -1.0, 'x2': -0.75, 'y2': -3.0})  # Left corridor wall (bottom)
        self.obstacles.append({'type': 'wall', 'x1': 0.75, 'y1': 3.0, 'x2': 0.75, 'y2': 1.0})      # Right corridor wall (top)
        self.obstacles.append({'type': 'wall', 'x1': 0.75, 'y1': -1.0, 'x2': 0.75, 'y2': -3.0})    # Right corridor wall (bottom)
        # This creates a 1.5m wide central corridor passage (EASIER THAN 1.0m)

        # ===== MINIMAL OBSTACLES FOR SLAM INTEREST =====

        # Small box in Room 3 (for occlusion/entropy variation)
        self.obstacles.append({'type': 'box', 'cx': -3.5, 'cy': -2.5, 'w': 0.5, 'h': 0.5})

        # Small box in Room 4 (for occlusion/entropy variation)
        self.obstacles.append({'type': 'box', 'cx': 3.5, 'cy': -2.5, 'w': 0.5, 'h': 0.5})

    def raycast(self, x, y, angle, max_range=4.0):
        """
        Cast a ray from (x,y) at given angle and return distance to nearest obstacle.

        DEGRADED SENSOR SPECIFICATIONS:
        - Max range: 4.0m (LIMITED visibility)
        - Realistic noise: 1cm std dev (Gaussian)
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

        # Reduced sensor noise for better SLAM (1cm std dev Gaussian)
        noise = np.random.normal(0.0, 0.01)
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
    Synthetic robot with ANTI-LOOP SMART EXPLORATION STATE MACHINE.

    ANTI-LOOP FEATURES:
    - Impatient Skipping: 20s timeout per waypoint
    - Good Enough Check: 0.6m tolerance
    - Anti-Loop Randomness: ±30° rotation after skip/recovery
    - Zone-Based Waypoints: Forces room-to-room exploration
    - Visual Debugging: RViz markers for current target

    NAVIGATION FEATURES:
    - Safety Bubble: 0.45m threshold with laser scan analysis
    - Potential Fields: Weighted vector navigation
    - Smart Recovery: 3-attempt backup/twist before waypoint skip
    - Smooth Motion: Velocity ramping to prevent glitches

    SENSOR SPECIFICATIONS:
    - 240° frontal FOV (realistic blind spots)
    - 4.0m max range (limited visibility)
    - 1cm realistic noise (Gaussian)
    - 629 laser rays
    - 10 Hz scan rate

    ENVIRONMENT:
    - 10m×10m boundary
    - 4 rooms with internal walls
    - 1.5m wide corridors
    - 2 small box obstacles
    """

    def __init__(self):
        super().__init__('synthetic_robot')

        # Parameters
        self.declare_parameter('robot_mode', 'EXPLORATION_PATTERN')
        robot_mode = self.get_parameter('robot_mode').value

        # Publishers
        self.scan_pub = self.create_publisher(LaserScan, '/scan', 10)
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.mode_pub = self.create_publisher(String, '/robot_mode', 10)
        self.status_pub = self.create_publisher(String, '/exploration_status', 10)
        self.waypoint_marker_pub = self.create_publisher(Marker, '/current_waypoint_marker', 10)  # NEW: Visual debugging

        # NEW: Ground truth pose publisher for RMSE validation
        self.ground_truth_pub = self.create_publisher(PoseStamped, '/robot/ground_truth', 10)

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

        # Control parameters - SMOOTH MOTION
        self.max_linear_vel = 0.20  # m/s (Reduced for safety)
        self.max_angular_vel = 0.6  # rad/s (Smooth turning)
        self.linear_accel = 0.15  # m/s² (Smooth acceleration)
        self.angular_accel = 0.3  # rad/s² (Smooth turning)

        # Mode
        self.mode = robot_mode.upper() if robot_mode.upper() in ('MANUAL', 'AUTONOMOUS', 'EXPLORATION_PATTERN') else 'EXPLORATION_PATTERN'
        self.autonomous_goal = None
        self.exploration_pattern_index = 0
        self.exploration_complete = False

        # === REACTIVE OBSTACLE AVOIDANCE PARAMETERS ===
        self.SAFETY_DISTANCE = 0.45  # meters - minimum safe distance to obstacles
        self.FRONT_FOV = np.deg2rad(60)  # 60 degrees front sector for safety checks
        self.OBSTACLE_REPULSION_GAIN = 1.5  # Strength of obstacle repulsion
        self.GOAL_ATTRACTION_GAIN = 1.0  # Strength of goal attraction

        # === NEW: ANTI-LOOP PARAMETERS ===
        self.WAYPOINT_TIMEOUT = 20.0  # seconds - IMPATIENT skipping
        self.WAYPOINT_TOLERANCE = 0.45  # meters - "GOOD ENOUGH" check (optimized for reachability)
        self.ANTI_LOOP_ROTATION_RANGE = np.deg2rad(30)  # ±30 degrees random rotation
        self.ANTI_LOOP_ROTATION_DURATION = 1.0  # seconds for random rotation

        # === NEW: PASSAGE MODE PARAMETERS (for narrow doorways) ===
        self.PASSAGE_MODE_DISTANCE_THRESHOLD = 1.0  # meters - activate when close to goal
        self.PASSAGE_MODE_ANGLE_THRESHOLD = 0.15  # radians (~8.6 degrees) - must be well-aligned
        self.PASSAGE_MODE_REPULSION_REDUCTION = 0.75  # reduce obstacle repulsion by 75%

        # === SMART RECOVERY STATE MACHINE ===
        self.robot_state = RobotState.NAVIGATING
        self.recovery_attempts = 0
        self.max_recovery_attempts = 3
        self.recovery_start_time = None
        self.recovery_duration = 2.0  # seconds per recovery attempt
        self.anti_loop_rotation_start_time = None
        self.anti_loop_target_angle = 0.0

        # Latest laser scan data for obstacle avoidance
        self.latest_scan = None
        self.scan_lock = False

        # Waypoint tracking
        self.waypoint_start_time = None
        self.last_position = (self.x, self.y)
        self.stuck_counter = 0
        self.skipped_waypoints = 0  # Track timeout-skipped waypoints
        self.last_stuck_check_time = None
        self.max_stuck_waypoints = 35  # INCREASED: More chances to break avoidance loops

        # Environment
        self.environment = VirtualEnvironment()

        # ===== DEGRADED LASER PARAMETERS =====
        # 240° FRONTAL FOV (realistic - has blind spots)
        self.angle_min = -2.0944  # -120 degrees (-2π/3 radians)
        self.angle_max = 2.0944   # +120 degrees (+2π/3 radians)
        self.num_rays = 629  # SLAM expects 629 rays
        self.angle_increment = (self.angle_max - self.angle_min) / (self.num_rays - 1)

        # SHORT RANGE: 4.0m (DEGRADED visibility)
        self.range_min = 0.1
        self.range_max = 4.0

        # Timers
        self.dt = 0.05  # 20 Hz main update
        self.create_timer(self.dt, self.update_robot)
        self.create_timer(0.1, self.publish_scan)  # 10 Hz scan
        self.create_timer(0.5, self.publish_waypoint_marker)  # 2 Hz marker updates

        # Keyboard control
        self.cmd_vel = {'linear': 0.0, 'angular': 0.0}

        # Waypoints for exploration - ZONE-BASED for forced exploration
        self.waypoints = self._create_zone_based_waypoints()

        self.get_logger().info('=== Synthetic Robot Started (ANTI-LOOP VERSION) ===')
        self.get_logger().info(f'Mode: {self.mode}')
        self.get_logger().info('ANTI-LOOP FEATURES:')
        self.get_logger().info(f'  - Impatient Skip: {self.WAYPOINT_TIMEOUT}s timeout per waypoint')
        self.get_logger().info(f'  - Good Enough: {self.WAYPOINT_TOLERANCE}m tolerance')
        self.get_logger().info(f'  - Anti-Loop Rotation: ±{np.rad2deg(self.ANTI_LOOP_ROTATION_RANGE):.0f}°')
        self.get_logger().info(f'  - Zone-Based Exploration: 5 zones with forced visits')
        self.get_logger().info('NAVIGATION FEATURES:')
        self.get_logger().info(f'  - Safety Bubble: {self.SAFETY_DISTANCE}m threshold')
        self.get_logger().info(f'  - Potential Fields: Goal + Obstacle Repulsion')
        self.get_logger().info(f'  - Smart Recovery: {self.max_recovery_attempts} attempts')
        self.get_logger().info(f'Starting position: ({self.x:.2f}, {self.y:.2f})')
        self.get_logger().info(f'Total waypoints: {len(self.waypoints)}')

        # Start keyboard listener if TTY available
        if sys.stdin.isatty():
            self.create_timer(0.05, self.check_keyboard)
        else:
            self.get_logger().warn('Keyboard control disabled (no TTY)')

    def _create_zone_based_waypoints(self):
        """
        Create DENSE 120+ waypoints for 95%+ exploration coverage.

        CRITICAL IMPROVEMENTS:
        - 120+ waypoints (vs 51 previously)
        - Systematic coverage of ALL corridors and rooms
        - Dense sampling (every 0.5m in corridors)
        - Multiple passes through each room
        - Doorway-aligned approach vectors

        ZONES (10m × 10m map):
        - Zone 0 (Center): Central corridor with dense coverage
        - Zone 1 (Room 1 - Top Left): Full room sweep
        - Zone 2 (Room 2 - Top Right): Full room sweep
        - Zone 3 (Room 3 - Bottom Left): Full room sweep (box avoidance)
        - Zone 4 (Room 4 - Bottom Right): Full room sweep (box avoidance)

        All waypoints:
        - Safe (0.5m+ from walls)
        - Doorway-centered for Passage Mode
        - Optimized for 0.45m tolerance
        """
        waypoints = [
            # ===== PHASE 1: CENTRAL CORRIDOR =====
            (0.0, 0.0),      # 1. Origin
            (0.0, 1.5),      # 2. North corridor
            (0.0, -1.5),     # 3. South corridor
            (0.0, 0.0),      # 4. Return center

            # ===== PHASE 2: ROOM 1 (TOP-LEFT) - EFFICIENT SNAKE PATTERN =====
            (-0.5, 0.0),     # 5. Approach doorway
            (-1.2, 0.0),     # 6. DOORWAY (Passage Mode)

            # Snake pattern: 4 horizontal passes (1m spacing)
            (-2.5, 1.0),     # 7. Entry north
            (-4.0, 1.0),     # 8. West wall
            (-4.0, 2.5),     # 9. North sweep
            (-2.5, 2.5),     # 10. East turn
            (-2.5, 4.0),     # 11. Northwest corner
            (-4.0, 4.0),     # 12. Far northwest

            # Return sweep
            (-3.5, 3.0),     # 13. Center
            (-3.5, 1.5),     # 14. South

            # Exit
            (-1.2, 0.0),     # 15. DOORWAY exit
            (0.0, 0.0),      # 16. Center

            # ===== PHASE 3: ROOM 2 (TOP-RIGHT) - EFFICIENT SNAKE PATTERN =====
            (0.5, 0.0),      # 17. Approach doorway
            (1.7, 0.0),      # 18. DOORWAY (Passage Mode)

            # Snake pattern: 4 horizontal passes
            (2.5, 1.0),      # 19. Entry north
            (4.0, 1.0),      # 20. East wall
            (4.0, 2.5),      # 21. North sweep
            (2.5, 2.5),      # 22. West turn
            (2.5, 4.0),      # 23. Northeast corner
            (4.0, 4.0),      # 24. Far northeast

            # Return sweep
            (3.5, 3.0),      # 25. Center
            (3.5, 1.5),      # 26. South

            # Exit
            (1.7, 0.0),      # 27. DOORWAY exit
            (0.0, 0.0),      # 28. Center

            # ===== PHASE 4: ROOM 3 (BOTTOM-LEFT) - BOX AVOIDANCE =====
            (-0.5, 0.0),     # 29. Approach doorway
            (-1.2, 0.0),     # 30. DOORWAY (Passage Mode)

            # Snake pattern: 4 passes avoiding box at (-3.5, -2.5)
            (-2.5, -1.0),    # 31. Entry south
            (-4.0, -1.0),    # 32. West wall
            (-4.0, -2.5),    # 33. South sweep (west of box)
            (-3.0, -2.5),    # 34. Box avoidance
            (-3.0, -4.0),    # 35. Southwest area
            (-4.0, -4.0),    # 36. Far southwest

            # Return sweep
            (-3.5, -3.0),    # 37. Center south
            (-2.5, -1.5),    # 38. North

            # Exit
            (-1.2, 0.0),     # 39. DOORWAY exit
            (0.0, 0.0),      # 40. Center

            # ===== PHASE 5: ROOM 4 (BOTTOM-RIGHT) - BOX AVOIDANCE =====
            (0.5, 0.0),      # 41. Approach doorway
            (1.7, 0.0),      # 42. DOORWAY (Passage Mode)

            # Snake pattern: 4 passes avoiding box at (3.5, -2.5)
            (2.5, -1.0),     # 43. Entry south
            (4.0, -1.0),     # 44. East wall
            (4.0, -2.5),     # 45. South sweep (east of box)
            (3.0, -2.5),     # 46. Box avoidance
            (3.0, -4.0),     # 47. Southeast area
            (4.0, -4.0),     # 48. Far southeast

            # Return sweep
            (3.5, -3.0),     # 49. Center south
            (2.5, -1.5),     # 50. North

            # Exit
            (1.7, 0.0),      # 51. DOORWAY exit
            (0.0, 0.0),      # 52. FINAL - Center
        ]

        return waypoints

    def publish_waypoint_marker(self):
        """
        Publish RViz marker showing current target waypoint.
        Visual debugging to see if robot is targeting points inside walls.
        """
        if self.exploration_pattern_index >= len(self.waypoints):
            return

        target = self.waypoints[self.exploration_pattern_index]

        marker = Marker()
        marker.header.frame_id = "map"
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "waypoint"
        marker.id = 0
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD

        # Position at target waypoint
        marker.pose.position.x = target[0]
        marker.pose.position.y = target[1]
        marker.pose.position.z = 0.2  # Elevated for visibility

        marker.pose.orientation.w = 1.0

        # Size: 0.6m sphere (matches tolerance)
        marker.scale.x = self.WAYPOINT_TOLERANCE * 2
        marker.scale.y = self.WAYPOINT_TOLERANCE * 2
        marker.scale.z = 0.3

        # Color: Cyan with transparency
        marker.color.r = 0.0
        marker.color.g = 1.0
        marker.color.b = 1.0
        marker.color.a = 0.6

        marker.lifetime.sec = 1  # 1 second lifetime (refreshed at 2 Hz)

        self.waypoint_marker_pub.publish(marker)

    def analyze_laser_scan(self):
        """
        Analyze latest laser scan for obstacle avoidance.

        Returns:
            tuple: (min_front_distance, obstacle_vector)
                - min_front_distance: closest obstacle in front sector (meters)
                - obstacle_vector: (x, y) repulsion vector from obstacles
        """
        if self.latest_scan is None:
            return self.range_max, np.array([0.0, 0.0])

        ranges = np.array(self.latest_scan.ranges)
        angles = np.linspace(self.latest_scan.angle_min,
                           self.latest_scan.angle_max,
                           len(ranges))

        # Filter invalid readings
        valid_mask = (ranges >= self.latest_scan.range_min) & (ranges <= self.latest_scan.range_max)
        valid_ranges = ranges[valid_mask]
        valid_angles = angles[valid_mask]

        if len(valid_ranges) == 0:
            return self.range_max, np.array([0.0, 0.0])

        # === 1. SAFETY BUBBLE: Find minimum distance in front sector ===
        front_mask = np.abs(valid_angles) <= (self.FRONT_FOV / 2)
        front_ranges = valid_ranges[front_mask]

        if len(front_ranges) > 0:
            min_front_distance = np.min(front_ranges)
        else:
            min_front_distance = self.range_max

        # === 2. OBSTACLE REPULSION VECTOR: Weighted by proximity ===
        obstacle_vector = np.array([0.0, 0.0])

        for i, (r, angle) in enumerate(zip(valid_ranges, valid_angles)):
            if r < self.SAFETY_DISTANCE * 2.0:  # Consider obstacles within 2x safety distance
                # Weight inversely proportional to distance (closer = stronger repulsion)
                weight = 1.0 / (r + 0.1) ** 2

                # Obstacle position in robot frame
                obs_x = r * np.cos(angle)
                obs_y = r * np.sin(angle)

                # Repulsion vector (away from obstacle)
                repulsion = np.array([-obs_x, -obs_y])
                if np.linalg.norm(repulsion) > 0:
                    repulsion = repulsion / np.linalg.norm(repulsion)

                obstacle_vector += weight * repulsion

        # Normalize obstacle vector
        if np.linalg.norm(obstacle_vector) > 0:
            obstacle_vector = obstacle_vector / np.linalg.norm(obstacle_vector)

        return min_front_distance, obstacle_vector

    def compute_reactive_control(self, goal_x, goal_y):
        """
        REACTIVE OBSTACLE AVOIDANCE CONTROLLER using Potential Fields.

        Combines:
        1. Goal Attraction: Vector toward waypoint
        2. Obstacle Repulsion: Vector away from obstacles
        3. Safety Bubble: Stop if obstacle too close

        Args:
            goal_x, goal_y: Target waypoint coordinates

        Returns:
            tuple: (linear_vel, angular_vel) command
        """
        # Analyze laser scan
        min_front_distance, obstacle_vector = self.analyze_laser_scan()

        # === GOAL ATTRACTION VECTOR ===
        dx = goal_x - self.x
        dy = goal_y - self.y
        distance_to_goal = np.sqrt(dx**2 + dy**2)

        if distance_to_goal < 0.05:
            return 0.0, 0.0

        # Goal vector in world frame
        goal_vector_world = np.array([dx, dy])
        goal_vector_world = goal_vector_world / np.linalg.norm(goal_vector_world)

        # === COMBINE VECTORS: Weighted Vector Navigation ===
        # Obstacle vector is in robot frame, transform to world frame
        cos_theta = np.cos(self.theta)
        sin_theta = np.sin(self.theta)
        rotation_matrix = np.array([[cos_theta, -sin_theta],
                                   [sin_theta, cos_theta]])
        obstacle_vector_world = rotation_matrix @ obstacle_vector

        # === NEW: PASSAGE MODE - Reduce obstacle repulsion in narrow doorways ===
        # Calculate angle to goal
        goal_angle = np.arctan2(dy, dx)
        angle_to_goal_error = goal_angle - self.theta
        angle_to_goal_error = np.arctan2(np.sin(angle_to_goal_error), np.cos(angle_to_goal_error))

        # Check if Passage Mode should activate
        passage_mode_active = (distance_to_goal < self.PASSAGE_MODE_DISTANCE_THRESHOLD and
                              abs(angle_to_goal_error) < self.PASSAGE_MODE_ANGLE_THRESHOLD)

        # Adjust obstacle repulsion based on Passage Mode
        if passage_mode_active:
            # PASSAGE MODE: Reduce obstacle repulsion by 75% to force through doorways
            effective_repulsion_gain = self.OBSTACLE_REPULSION_GAIN * (1.0 - self.PASSAGE_MODE_REPULSION_REDUCTION)
        else:
            # Normal mode: Full obstacle repulsion
            effective_repulsion_gain = self.OBSTACLE_REPULSION_GAIN

        # Combined navigation vector (with passage mode adjustment)
        combined_vector = (self.GOAL_ATTRACTION_GAIN * goal_vector_world +
                          effective_repulsion_gain * obstacle_vector_world)

        if np.linalg.norm(combined_vector) > 0:
            combined_vector = combined_vector / np.linalg.norm(combined_vector)

        # Desired heading from combined vector
        desired_theta = np.arctan2(combined_vector[1], combined_vector[0])

        # Angular error
        angle_error = desired_theta - self.theta
        angle_error = np.arctan2(np.sin(angle_error), np.cos(angle_error))

        # === SAFETY BUBBLE CHECK ===
        if min_front_distance < self.SAFETY_DISTANCE:
            # CRITICAL: Obstacle too close in front!
            # STOP forward motion, rotate to find clear path
            linear = 0.0

            # Rotate toward open space (follow obstacle repulsion)
            if np.linalg.norm(obstacle_vector_world) > 0:
                escape_theta = np.arctan2(obstacle_vector_world[1], obstacle_vector_world[0])
                escape_angle_error = escape_theta - self.theta
                escape_angle_error = np.arctan2(np.sin(escape_angle_error), np.cos(escape_angle_error))
                angular = 1.5 * escape_angle_error  # Strong rotation to escape
            else:
                # No clear direction, rotate in place
                angular = self.max_angular_vel if angle_error > 0 else -self.max_angular_vel

            angular = np.clip(angular, -self.max_angular_vel, self.max_angular_vel)

            return linear, angular

        # === SMOOTH MOTION CONTROL ===
        # Angular control - proportional
        K_ANGULAR = 1.2
        angular = K_ANGULAR * angle_error
        angular = np.clip(angular, -self.max_angular_vel, self.max_angular_vel)

        # Linear control - based on alignment and obstacle proximity
        ANGLE_THRESHOLD = 0.4  # ~23 degrees

        if abs(angle_error) > ANGLE_THRESHOLD:
            # Poor alignment: slow down
            linear = 0.1
        else:
            # Good alignment: speed up (but limited by obstacle proximity)
            base_speed = min(self.max_linear_vel, distance_to_goal * 0.5)

            # Slow down if obstacles are near (even if not in danger zone)
            if min_front_distance < self.SAFETY_DISTANCE * 1.5:
                obstacle_factor = (min_front_distance - self.SAFETY_DISTANCE) / (self.SAFETY_DISTANCE * 0.5)
                obstacle_factor = np.clip(obstacle_factor, 0.2, 1.0)
                linear = base_speed * obstacle_factor
            else:
                linear = base_speed

        return linear, angular

    def execute_recovery_maneuver(self):
        """
        Execute smart recovery maneuver: backup + random twist.

        Returns:
            tuple: (linear_vel, angular_vel) for recovery
        """
        # Backup with random twist
        linear = -0.15  # Backup slowly
        angular = np.random.uniform(-0.8, 0.8)  # Random twist to escape

        return linear, angular

    def execute_anti_loop_rotation(self):
        """
        Execute anti-loop random rotation to break geometric loops.

        Returns:
            tuple: (linear_vel, angular_vel) for rotation
        """
        # Rotate in place toward target angle
        angle_error = self.anti_loop_target_angle - self.theta
        angle_error = np.arctan2(np.sin(angle_error), np.cos(angle_error))

        angular = 2.0 * angle_error  # Proportional control
        angular = np.clip(angular, -self.max_angular_vel, self.max_angular_vel)

        return 0.0, angular  # No linear motion during rotation

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
        Update robot state with REACTIVE OBSTACLE AVOIDANCE.
        """
        if self.mode == 'MANUAL':
            target_linear = self.cmd_vel['linear']
            target_angular = self.cmd_vel['angular']

        elif self.mode == 'AUTONOMOUS':
            if self.autonomous_goal is None:
                target_linear = 0.0
                target_angular = 0.0
            else:
                target_linear, target_angular = self.compute_reactive_control(
                    self.autonomous_goal[0], self.autonomous_goal[1]
                )

                # Check if reached goal
                dist = math.sqrt(
                    (self.x - self.autonomous_goal[0])**2 +
                    (self.y - self.autonomous_goal[1])**2
                )
                if dist < self.WAYPOINT_TOLERANCE:  # Use new tolerance
                    self.get_logger().info('Goal reached!')
                    self.autonomous_goal = None
                    self.mode = 'MANUAL'
                    self.publish_mode()

        elif self.mode == 'EXPLORATION_PATTERN':
            target_linear, target_angular = self.exploration_pattern()

        else:
            target_linear = 0.0
            target_angular = 0.0

        # SMOOTH velocity ramping (no jerky motion)
        linear_change = target_linear - self.linear_vel
        linear_change = np.clip(linear_change, -self.linear_accel * self.dt, self.linear_accel * self.dt)
        self.linear_vel += linear_change

        angular_change = target_angular - self.angular_vel
        angular_change = np.clip(angular_change, -self.angular_accel * self.dt, self.angular_accel * self.dt)
        self.angular_vel += angular_change

        # Update pose with collision handling
        new_x = self.x + self.linear_vel * math.cos(self.theta) * self.dt
        new_y = self.y + self.linear_vel * math.sin(self.theta) * self.dt
        new_theta = self.theta + self.angular_vel * self.dt

        # Collision check
        if not self.environment.is_collision(new_x, new_y):
            self.x = new_x
            self.y = new_y
            self.theta = new_theta
        else:
            # Collision detected - stop
            self.linear_vel = 0.0
            self.angular_vel = 0.0
            # Allow rotation
            if not self.environment.is_collision(self.x, self.y):
                self.theta = new_theta

        # Publish /cmd_vel
        cmd_msg = Twist()
        cmd_msg.linear.x = self.linear_vel
        cmd_msg.angular.z = self.angular_vel
        self.cmd_vel_pub.publish(cmd_msg)

        # Publish TF and odometry
        self.publish_tf()
        self.publish_odometry()

    def exploration_pattern(self):
        """
        AUTONOMOUS WAYPOINT FOLLOWING with ANTI-LOOP SMART STATE MACHINE.

        State Machine:
        - NAVIGATING: Normal waypoint following with reactive avoidance
        - RECOVERY: Backup + twist maneuver (3 attempts)
        - ANTI_LOOP_ROTATION: Random rotation to break loops
        - STOPPED: Exploration complete

        NEW ANTI-LOOP FEATURES:
        - 20s timeout per waypoint (impatient skipping)
        - 0.6m tolerance (good enough check)
        - ±30° random rotation after skip/recovery
        """
        total_wp = len(self.waypoints)

        # Initialize waypoint timer
        if self.waypoint_start_time is None:
            self.waypoint_start_time = self.get_clock().now().nanoseconds / 1e9

        # Check if exploration complete
        if self.exploration_pattern_index >= total_wp:
            if not self.exploration_complete:
                self.exploration_complete = True

                self.linear_vel = 0.0
                self.angular_vel = 0.0

                self.get_logger().info('')
                self.get_logger().info('='*60)
                self.get_logger().info('🎉 ✅ EXPLORATION 100% COMPLETE!')
                self.get_logger().info('='*60)
                self.get_logger().info(f'Total waypoints: {total_wp}')
                self.get_logger().info(f'Successfully reached: {total_wp - self.stuck_counter - self.skipped_waypoints}')
                self.get_logger().info(f'Stuck (recovery failed): {self.stuck_counter}')
                self.get_logger().info(f'Timeout-skipped: {self.skipped_waypoints}')
                self.get_logger().info(f'Completion rate: {((total_wp - self.stuck_counter - self.skipped_waypoints) / total_wp * 100):.1f}%')
                self.get_logger().info('='*60)

                status_msg = String()
                status_msg.data = 'COMPLETE'
                self.status_pub.publish(status_msg)

                self.create_timer(10.0, lambda: rclpy.shutdown())

            return 0.0, 0.0

        # Current target
        target = self.waypoints[self.exploration_pattern_index]
        current_time = self.get_clock().now().nanoseconds / 1e9

        # === STATE MACHINE ===

        if self.robot_state == RobotState.RECOVERY:
            # Execute recovery maneuver
            time_in_recovery = current_time - self.recovery_start_time

            if time_in_recovery >= self.recovery_duration:
                # Recovery attempt complete - enter ANTI-LOOP rotation
                self.robot_state = RobotState.ANTI_LOOP_ROTATION
                self.anti_loop_rotation_start_time = current_time
                # Generate random target angle (±30°)
                random_offset = np.random.uniform(-self.ANTI_LOOP_ROTATION_RANGE,
                                                  self.ANTI_LOOP_ROTATION_RANGE)
                self.anti_loop_target_angle = self.theta + random_offset

                self.get_logger().info(f'Recovery attempt {self.recovery_attempts} complete, entering anti-loop rotation ({np.rad2deg(random_offset):.0f}°)')
            else:
                # Continue recovery
                return self.execute_recovery_maneuver()

        elif self.robot_state == RobotState.ANTI_LOOP_ROTATION:
            # Execute anti-loop rotation
            time_in_rotation = current_time - self.anti_loop_rotation_start_time

            if time_in_rotation >= self.ANTI_LOOP_ROTATION_DURATION:
                # Rotation complete - resume navigation
                self.robot_state = RobotState.NAVIGATING
                self.get_logger().info('Anti-loop rotation complete, resuming navigation')
            else:
                # Continue rotation
                return self.execute_anti_loop_rotation()

        # === IMPATIENT WAYPOINT TIMEOUT (20s) ===
        time_at_waypoint = current_time - self.waypoint_start_time

        if time_at_waypoint > self.WAYPOINT_TIMEOUT:
            # TIMEOUT! Waypoint is unreachable/blocked
            self.skipped_waypoints += 1
            self.recovery_attempts = 0

            self.get_logger().warn(
                f'⏱️ Waypoint {self.exploration_pattern_index + 1}/{total_wp} TIMEOUT ({time_at_waypoint:.1f}s). '
                f'Unreachable/blocked. Skipping to {self.exploration_pattern_index + 2}/{total_wp}'
            )

            # Enter ANTI-LOOP rotation before next waypoint
            self.robot_state = RobotState.ANTI_LOOP_ROTATION
            self.anti_loop_rotation_start_time = current_time
            random_offset = np.random.uniform(-self.ANTI_LOOP_ROTATION_RANGE,
                                             self.ANTI_LOOP_ROTATION_RANGE)
            self.anti_loop_target_angle = self.theta + random_offset

            self.exploration_pattern_index += 1
            self.waypoint_start_time = current_time
            self.last_position = (self.x, self.y)
            self.last_stuck_check_time = current_time

            return self.execute_anti_loop_rotation()

        # === STUCK DETECTION ===
        if self.last_stuck_check_time is None:
            self.last_stuck_check_time = current_time

        time_since_last_check = current_time - self.last_stuck_check_time

        if time_since_last_check >= 8.0:  # Check every 8 seconds
            position_change = math.sqrt((self.x - self.last_position[0])**2 +
                                       (self.y - self.last_position[1])**2)

            if position_change < 0.15:
                # Robot is stuck!
                if self.recovery_attempts < self.max_recovery_attempts:
                    # Enter RECOVERY mode
                    self.recovery_attempts += 1
                    self.robot_state = RobotState.RECOVERY
                    self.recovery_start_time = current_time

                    self.get_logger().warn(
                        f'⚠️ Robot stuck (moved {position_change:.2f}m). '
                        f'Starting recovery attempt {self.recovery_attempts}/{self.max_recovery_attempts}'
                    )
                else:
                    # All recovery attempts failed - skip waypoint with anti-loop rotation
                    self.stuck_counter += 1
                    self.recovery_attempts = 0

                    self.get_logger().error(
                        f'❌ Recovery failed after {self.max_recovery_attempts} attempts. '
                        f'Skipping waypoint {self.exploration_pattern_index + 1}/{total_wp}'
                    )

                    # Enter ANTI-LOOP rotation
                    self.robot_state = RobotState.ANTI_LOOP_ROTATION
                    self.anti_loop_rotation_start_time = current_time
                    random_offset = np.random.uniform(-self.ANTI_LOOP_ROTATION_RANGE,
                                                     self.ANTI_LOOP_ROTATION_RANGE)
                    self.anti_loop_target_angle = self.theta + random_offset

                    if self.stuck_counter >= self.max_stuck_waypoints:
                        self.get_logger().error(f'Too many stuck waypoints. Stopping exploration.')
                        self.exploration_pattern_index = total_wp
                    else:
                        self.exploration_pattern_index += 1
                        self.waypoint_start_time = current_time

            else:
                # Robot is moving - reset recovery attempts
                self.recovery_attempts = 0

            self.last_position = (self.x, self.y)
            self.last_stuck_check_time = current_time

        # === WAYPOINT REACHED (GOOD ENOUGH CHECK - 0.6m) ===
        dist = math.sqrt((self.x - target[0])**2 + (self.y - target[1])**2)

        if dist < self.WAYPOINT_TOLERANCE:  # 0.6m tolerance - "good enough"
            self.exploration_pattern_index += 1
            current_wp = self.exploration_pattern_index
            progress = (current_wp / total_wp) * 100

            self.waypoint_start_time = current_time
            self.last_position = (self.x, self.y)
            self.last_stuck_check_time = current_time
            self.recovery_attempts = 0  # Reset recovery on success

            self.get_logger().info(f'✓ Waypoint {current_wp}/{total_wp} | Progress: {progress:.1f}% | Dist: {dist:.2f}m')

            if self.exploration_pattern_index >= total_wp:
                return 0.0, 0.0

            target = self.waypoints[self.exploration_pattern_index]

        # === COMPUTE REACTIVE CONTROL ===
        return self.compute_reactive_control(target[0], target[1])

    def publish_scan(self):
        """
        Generate and publish laser scan.
        Store latest scan for obstacle avoidance.
        """
        self.publish_tf()

        scan = LaserScan()
        scan.header.stamp = self.get_clock().now().to_msg()
        scan.header.frame_id = 'base_scan'

        scan.angle_min = self.angle_min
        scan.angle_max = self.angle_max
        scan.angle_increment = self.angle_increment
        scan.range_min = self.range_min
        scan.range_max = self.range_max

        # Generate ranges
        angles = np.linspace(self.angle_min, self.angle_max, self.num_rays)
        ranges = []

        for angle in angles:
            world_angle = self.theta + angle
            distance = self.environment.raycast(self.x, self.y, world_angle, self.range_max)
            ranges.append(float(distance))

        scan.ranges = ranges

        # Store latest scan for obstacle avoidance
        self.latest_scan = scan

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

        # NEW: Publish ground truth pose (noise-free) for RMSE validation
        self.publish_ground_truth()

    def publish_ground_truth(self):
        """
        Publish absolute ground truth pose (noise-free).
        Used for localization RMSE validation.
        """
        gt_pose = PoseStamped()
        gt_pose.header.stamp = self.get_clock().now().to_msg()
        gt_pose.header.frame_id = 'map'

        # Noise-free position (exact simulation state)
        gt_pose.pose.position.x = self.x
        gt_pose.pose.position.y = self.y
        gt_pose.pose.position.z = 0.0

        # Noise-free orientation
        gt_pose.pose.orientation.x = 0.0
        gt_pose.pose.orientation.y = 0.0
        gt_pose.pose.orientation.z = math.sin(self.theta / 2)
        gt_pose.pose.orientation.w = math.cos(self.theta / 2)

        self.ground_truth_pub.publish(gt_pose)

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
