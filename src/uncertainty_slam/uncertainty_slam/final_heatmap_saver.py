#!/usr/bin/env python3
"""
Final Heatmap Saver - Automatically saves HIGH-CONTRAST entropy heatmap overlay when exploration completes.

IMPROVEMENTS:
- Unknown cells (-1 in occupancy grid) are treated as MAXIMUM ENTROPY (RED)
- Gamma correction applied for better mid-tone visibility
- Improved overlay: walls drawn on top, colors show through free space
- JET colormap for maximum color distinctness
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from nav_msgs.msg import OccupancyGrid
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
import os
from datetime import datetime

class FinalHeatmapSaver(Node):
    def __init__(self):
        super().__init__('final_heatmap_saver')

        # CV Bridge
        self.bridge = CvBridge()

        # Storage
        self.latest_map = None
        self.latest_entropy_image = None
        self.saved = False

        # Subscribers
        self.map_sub = self.create_subscription(
            OccupancyGrid,
            '/map',
            self.map_callback,
            10
        )

        self.entropy_image_sub = self.create_subscription(
            Image,
            '/entropy_heatmap_image',
            self.entropy_image_callback,
            10
        )

        self.status_sub = self.create_subscription(
            String,
            '/exploration_status',
            self.status_callback,
            10
        )

        # Output directory
        self.output_dir = os.path.expanduser('~/slam_uncertainty_ws/results/final_heatmaps')
        os.makedirs(self.output_dir, exist_ok=True)

        self.get_logger().info('Final Heatmap Saver initialized (HIGH-CONTRAST MODE)')
        self.get_logger().info(f'Output directory: {self.output_dir}')

    def map_callback(self, msg):
        """Store latest SLAM map."""
        self.latest_map = msg

    def entropy_image_callback(self, msg):
        """Store latest entropy heatmap image."""
        try:
            self.latest_entropy_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f'Failed to convert entropy image: {e}')

    def status_callback(self, msg):
        """Check if exploration is complete."""
        if msg.data == 'COMPLETE' and not self.saved:
            self.get_logger().info('🎨 Exploration complete! Saving HIGH-CONTRAST entropy heatmap...')
            self.save_final_heatmap()
            self.saved = True

    def create_high_contrast_entropy_heatmap(self, map_data):
        """
        Create HIGH-CONTRAST entropy heatmap with proper unknown cell handling.

        Key improvements:
        1. Unknown cells (-1) treated as MAXIMUM entropy (RED)
        2. Gamma correction (power=0.5) for better mid-tone visibility
        3. JET colormap for maximum color distinctness

        Args:
            map_data: Occupancy grid data (int8 array)

        Returns:
            numpy.ndarray: High-contrast BGR color heatmap
        """
        height, width = map_data.shape

        # Create entropy array
        entropy = np.zeros((height, width), dtype=np.float32)

        # CRITICAL FIX: Unknown cells (-1) = MAXIMUM ENTROPY (1.0 = RED)
        unknown_mask = (map_data == -1)
        entropy[unknown_mask] = 1.0

        # Free space (0) = variable entropy based on exploration
        # For now, we'll use a default low entropy for free space
        # (In reality, this should come from the entropy_image, but we need to handle it here too)
        free_mask = (map_data == 0)
        entropy[free_mask] = 0.1  # Low entropy for free, explored space

        # Occupied space (>50) = low entropy (well-defined obstacles)
        occupied_mask = (map_data > 50)
        entropy[occupied_mask] = 0.05

        # Apply gamma correction for better mid-tone visibility
        # Gamma < 1.0 brightens mid-tones (makes Green/Yellow more visible)
        gamma = 0.5
        entropy_enhanced = np.power(entropy, gamma)

        # Normalize to 0-255
        entropy_normalized = np.clip(entropy_enhanced * 255.0, 0, 255).astype(np.uint8)

        # Apply JET colormap (Blue-Cyan-Green-Yellow-Red)
        entropy_color = cv2.applyColorMap(entropy_normalized, cv2.COLORMAP_JET)

        return entropy_color

    def create_improved_overlay(self, map_data, entropy_color):
        """
        Create improved overlay with walls drawn on top of colors.

        Strategy:
        1. Start with full-brightness entropy heatmap as base
        2. Draw black walls on top (occupied cells)
        3. Free space shows colors at 100% brightness
        4. Unknown space shows RED at 100% brightness

        Args:
            map_data: Occupancy grid data (int8 array)
            entropy_color: BGR color heatmap

        Returns:
            numpy.ndarray: Improved overlay image
        """
        height, width = map_data.shape

        # Start with the entropy heatmap as base
        overlay = entropy_color.copy()

        # Draw occupied cells (walls) as BLACK on top
        # This makes walls clearly visible while letting colors shine through free space
        occupied_mask = (map_data > 50)  # Threshold for "occupied"
        overlay[occupied_mask] = [0, 0, 0]  # Black walls

        # Optional: Draw explored free space with slight transparency to show structure
        # But keep colors bright

        return overlay

    def save_final_heatmap(self):
        """Save HIGH-CONTRAST entropy heatmap overlaid on the SLAM map."""
        if self.latest_map is None:
            self.get_logger().warn('No map data available')
            return

        if self.latest_entropy_image is None:
            self.get_logger().warn('No entropy heatmap available')
            return

        try:
            # Convert occupancy grid to numpy array
            map_data = np.array(self.latest_map.data, dtype=np.int8).reshape(
                (self.latest_map.info.height, self.latest_map.info.width)
            )

            # Create traditional map image (for reference)
            map_img = np.zeros((map_data.shape[0], map_data.shape[1], 3), dtype=np.uint8)

            # Color mapping for traditional occupancy grid
            for i in range(map_data.shape[0]):
                for j in range(map_data.shape[1]):
                    if map_data[i, j] == -1:  # Unknown
                        map_img[i, j] = [128, 128, 128]  # Gray
                    elif map_data[i, j] == 0:  # Free
                        map_img[i, j] = [255, 255, 255]  # White
                    else:  # Occupied
                        map_img[i, j] = [0, 0, 0]  # Black

            # Resize entropy image from uncertainty_node to match map dimensions
            entropy_resized = cv2.resize(self.latest_entropy_image,
                                        (map_img.shape[1], map_img.shape[0]),
                                        interpolation=cv2.INTER_LINEAR)

            # CRITICAL: Enhance the entropy image with gamma correction
            # Convert to float, apply gamma, convert back
            entropy_float = entropy_resized.astype(np.float32) / 255.0
            gamma = 0.5  # Brighten mid-tones
            entropy_enhanced = np.power(entropy_float, gamma)
            entropy_enhanced = np.clip(entropy_enhanced * 255.0, 0, 255).astype(np.uint8)

            # Create high-contrast entropy heatmap from occupancy grid
            # This handles unknown cells properly
            entropy_from_occ = self.create_high_contrast_entropy_heatmap(map_data)

            # Combine both entropy sources:
            # Use entropy_enhanced where available, entropy_from_occ for unknown areas
            entropy_combined = entropy_enhanced.copy()
            unknown_mask = (map_data == -1)

            # Set unknown areas to RED (maximum entropy)
            for i in range(map_data.shape[0]):
                for j in range(map_data.shape[1]):
                    if unknown_mask[i, j]:
                        # JET colormap: RED = [0, 0, 255] in BGR
                        entropy_combined[i, j] = [0, 0, 255]

            # Create improved overlay with walls on top
            overlay_improved = self.create_improved_overlay(map_data, entropy_combined)

            # Save timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # Save files
            map_file = os.path.join(self.output_dir, f'slam_map_{timestamp}.png')
            entropy_file = os.path.join(self.output_dir, f'entropy_heatmap_{timestamp}.png')
            overlay_file = os.path.join(self.output_dir, f'entropy_overlay_{timestamp}.png')

            # Also save a version with just entropy (no walls) for comparison
            entropy_pure_file = os.path.join(self.output_dir, f'entropy_pure_{timestamp}.png')

            cv2.imwrite(map_file, map_img)
            cv2.imwrite(entropy_file, entropy_combined)
            cv2.imwrite(overlay_file, overlay_improved)
            cv2.imwrite(entropy_pure_file, entropy_enhanced)

            self.get_logger().info('='*70)
            self.get_logger().info('✅ HIGH-CONTRAST HEATMAP SAVED SUCCESSFULLY!')
            self.get_logger().info('='*70)
            self.get_logger().info(f'📁 SLAM Map: {map_file}')
            self.get_logger().info(f'🔥 Entropy Heatmap (Enhanced): {entropy_file}')
            self.get_logger().info(f'🎨 Overlay (Walls on Colors): {overlay_file}')
            self.get_logger().info(f'🌈 Pure Entropy (No Walls): {entropy_pure_file}')
            self.get_logger().info('='*70)
            self.get_logger().info('💡 HIGH-CONTRAST VISUALIZATION:')
            self.get_logger().info('   - 🔴 RED = HIGH uncertainty (unknown/unexplored areas)')
            self.get_logger().info('   - 🟡 YELLOW/GREEN = MEDIUM uncertainty')
            self.get_logger().info('   - 🔵 BLUE = LOW uncertainty (well-explored areas)')
            self.get_logger().info('   - ⚫ BLACK = Walls/obstacles')
            self.get_logger().info('   - Gamma correction (0.5) applied for bright mid-tones')
            self.get_logger().info('   - Unknown cells (-1) treated as MAXIMUM entropy')
            self.get_logger().info('='*70)

        except Exception as e:
            self.get_logger().error(f'Failed to save final heatmap: {e}')
            import traceback
            traceback.print_exc()


def main(args=None):
    rclpy.init(args=args)
    node = FinalHeatmapSaver()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
