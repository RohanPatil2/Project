#!/usr/bin/env python3
"""
Static Map Publisher - Pre-renders the environment map
Publishes a pre-built occupancy grid showing all walls before robot exploration.
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid
import numpy as np
import math


class StaticMapPublisher(Node):
    """Publishes a pre-rendered static map of the environment."""

    def __init__(self):
        super().__init__('static_map_publisher')

        # Publishers
        self.map_pub = self.create_publisher(OccupancyGrid, '/static_map', 10)

        # Map parameters (10m×10m environment)
        self.resolution = 0.05  # 5cm per cell
        self.width = 10.0  # meters
        self.height = 10.0  # meters
        self.grid_width = int(self.width / self.resolution)  # 200 cells
        self.grid_height = int(self.height / self.resolution)  # 200 cells

        # Create the map
        self.static_map = self._create_static_map()

        # Publish at 1 Hz
        self.create_timer(1.0, self.publish_map)

        self.get_logger().info('Static Map Publisher initialized')
        self.get_logger().info(f'Map size: {self.grid_width}×{self.grid_height} ({self.width}m×{self.height}m)')
        self.get_logger().info(f'Resolution: {self.resolution}m/cell')
        self.get_logger().info('Publishing pre-rendered map to /static_map')

    def _create_static_map(self):
        """Create the static occupancy grid with all environment obstacles."""
        # Initialize grid (0 = free, 100 = occupied, -1 = unknown)
        # Start with all free space
        grid = np.zeros((self.grid_height, self.grid_width), dtype=np.int8)

        # Define obstacles (same as synthetic_robot.py environment)
        obstacles = []

        # ===== EXTERIOR WALLS (10m × 10m) =====
        obstacles.append({'type': 'wall', 'x1': -5.0, 'y1': -5.0, 'x2': 5.0, 'y2': -5.0})  # Bottom
        obstacles.append({'type': 'wall', 'x1': 5.0, 'y1': -5.0, 'x2': 5.0, 'y2': 5.0})    # Right
        obstacles.append({'type': 'wall', 'x1': 5.0, 'y1': 5.0, 'x2': -5.0, 'y2': 5.0})    # Top
        obstacles.append({'type': 'wall', 'x1': -5.0, 'y1': 5.0, 'x2': -5.0, 'y2': -5.0})  # Left

        # ===== INTERNAL WALLS - ROOM DIVIDERS =====

        # VERTICAL WALL 1 - Left side
        obstacles.append({'type': 'wall', 'x1': -2.0, 'y1': 5.0, 'x2': -2.0, 'y2': 0.75})
        obstacles.append({'type': 'wall', 'x1': -2.0, 'y1': -0.75, 'x2': -2.0, 'y2': -5.0})

        # VERTICAL WALL 2 - Right side
        obstacles.append({'type': 'wall', 'x1': 1.5, 'y1': 5.0, 'x2': 1.5, 'y2': 0.75})
        obstacles.append({'type': 'wall', 'x1': 1.5, 'y1': -0.75, 'x2': 1.5, 'y2': -5.0})

        # HORIZONTAL WALL 1 - Top-left
        obstacles.append({'type': 'wall', 'x1': -5.0, 'y1': 0.0, 'x2': -2.75, 'y2': 0.0})
        obstacles.append({'type': 'wall', 'x1': -1.25, 'y1': 0.0, 'x2': -2.0, 'y2': 0.0})

        # HORIZONTAL WALL 2 - Top-right
        obstacles.append({'type': 'wall', 'x1': 1.5, 'y1': 0.0, 'x2': 2.25, 'y2': 0.0})
        obstacles.append({'type': 'wall', 'x1': 3.75, 'y1': 0.0, 'x2': 5.0, 'y2': 0.0})

        # CENTRAL CORRIDOR WALLS
        obstacles.append({'type': 'wall', 'x1': -0.5, 'y1': 3.0, 'x2': -0.5, 'y2': 0.75})
        obstacles.append({'type': 'wall', 'x1': -0.5, 'y1': -0.75, 'x2': -0.5, 'y2': -3.0})
        obstacles.append({'type': 'wall', 'x1': 0.5, 'y1': 3.0, 'x2': 0.5, 'y2': 0.75})
        obstacles.append({'type': 'wall', 'x1': 0.5, 'y1': -0.75, 'x2': 0.5, 'y2': -3.0})

        # ===== U-SHAPED OBSTACLES =====

        # U-SHAPE in Room 1
        obstacles.append({'type': 'wall', 'x1': -4.0, 'y1': 3.5, 'x2': -3.0, 'y2': 3.5})
        obstacles.append({'type': 'wall', 'x1': -4.0, 'y1': 3.5, 'x2': -4.0, 'y2': 2.0})
        obstacles.append({'type': 'wall', 'x1': -3.0, 'y1': 3.5, 'x2': -3.0, 'y2': 2.0})

        # U-SHAPE in Room 2
        obstacles.append({'type': 'wall', 'x1': 3.0, 'y1': 3.5, 'x2': 4.0, 'y2': 3.5})
        obstacles.append({'type': 'wall', 'x1': 3.0, 'y1': 3.5, 'x2': 3.0, 'y2': 2.0})
        obstacles.append({'type': 'wall', 'x1': 4.0, 'y1': 3.5, 'x2': 4.0, 'y2': 2.0})

        # ===== L-SHAPED OBSTACLES =====

        # L-SHAPE in Room 3
        obstacles.append({'type': 'wall', 'x1': -4.5, 'y1': -2.0, 'x2': -3.0, 'y2': -2.0})
        obstacles.append({'type': 'wall', 'x1': -3.0, 'y1': -2.0, 'x2': -3.0, 'y2': -3.5})

        # L-SHAPE in Room 4
        obstacles.append({'type': 'wall', 'x1': 3.0, 'y1': -2.0, 'x2': 4.5, 'y2': -2.0})
        obstacles.append({'type': 'wall', 'x1': 3.0, 'y1': -2.0, 'x2': 3.0, 'y2': -3.5})

        # ===== BOX OBSTACLES =====

        # Box in Room 1
        obstacles.append({'type': 'box', 'cx': -3.5, 'cy': 1.0, 'w': 0.6, 'h': 0.6})

        # Box in Room 2
        obstacles.append({'type': 'box', 'cx': 3.5, 'cy': 1.0, 'w': 0.6, 'h': 0.6})

        # Box in Room 3
        obstacles.append({'type': 'box', 'cx': -3.5, 'cy': -3.5, 'w': 0.7, 'h': 0.7})

        # Box in Room 4
        obstacles.append({'type': 'box', 'cx': 3.5, 'cy': -3.5, 'w': 0.7, 'h': 0.7})

        # Pillars in central corridor
        obstacles.append({'type': 'box', 'cx': -0.2, 'cy': 2.0, 'w': 0.3, 'h': 0.3})
        obstacles.append({'type': 'box', 'cx': 0.2, 'cy': -2.0, 'w': 0.3, 'h': 0.3})

        # Draw all obstacles on the grid
        for obs in obstacles:
            if obs['type'] == 'wall':
                self._draw_wall(grid, obs['x1'], obs['y1'], obs['x2'], obs['y2'])
            elif obs['type'] == 'box':
                self._draw_box(grid, obs['cx'], obs['cy'], obs['w'], obs['h'])

        return grid

    def _world_to_grid(self, x, y):
        """Convert world coordinates to grid coordinates."""
        # Map origin is at bottom-left corner (-5, -5)
        grid_x = int((x + self.width/2) / self.resolution)
        grid_y = int((y + self.height/2) / self.resolution)
        return grid_x, grid_y

    def _draw_wall(self, grid, x1, y1, x2, y2):
        """Draw a wall on the grid using Bresenham's line algorithm."""
        gx1, gy1 = self._world_to_grid(x1, y1)
        gx2, gy2 = self._world_to_grid(x2, y2)

        # Bresenham's line algorithm
        dx = abs(gx2 - gx1)
        dy = abs(gy2 - gy1)
        sx = 1 if gx2 > gx1 else -1
        sy = 1 if gy2 > gy1 else -1
        err = dx - dy

        x, y = gx1, gy1

        # Draw with thickness (3 cells wide for visibility)
        thickness = 3
        while True:
            # Draw thick line
            for dx_offset in range(-thickness//2, thickness//2 + 1):
                for dy_offset in range(-thickness//2, thickness//2 + 1):
                    nx = x + dx_offset
                    ny = y + dy_offset
                    if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                        grid[ny, nx] = 100  # Occupied

            if x == gx2 and y == gy2:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def _draw_box(self, grid, cx, cy, w, h):
        """Draw a box obstacle on the grid."""
        # Get corners
        x1 = cx - w/2
        y1 = cy - h/2
        x2 = cx + w/2
        y2 = cy + h/2

        # Draw four walls
        self._draw_wall(grid, x1, y1, x2, y1)  # Bottom
        self._draw_wall(grid, x2, y1, x2, y2)  # Right
        self._draw_wall(grid, x2, y2, x1, y2)  # Top
        self._draw_wall(grid, x1, y2, x1, y1)  # Left

    def publish_map(self):
        """Publish the static map."""
        msg = OccupancyGrid()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'

        msg.info.resolution = self.resolution
        msg.info.width = self.grid_width
        msg.info.height = self.grid_height

        # Map origin is at bottom-left corner
        msg.info.origin.position.x = -self.width / 2
        msg.info.origin.position.y = -self.height / 2
        msg.info.origin.position.z = 0.0
        msg.info.origin.orientation.w = 1.0

        # Flatten grid (row-major order)
        msg.data = self.static_map.flatten().tolist()

        self.map_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = StaticMapPublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
