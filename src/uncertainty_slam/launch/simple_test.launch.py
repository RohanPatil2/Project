#!/usr/bin/env python3
"""
SIMPLEST POSSIBLE TEST
10x10m box, robot drives in square, clean map expected.

If this doesn't work, SLAM Toolbox or Stage is broken.
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    stage_pkg = get_package_share_directory('stage_ros2')
    world_file = os.path.join(stage_pkg, 'world', 'test_simple.world')

    return LaunchDescription([
        # 1. Stage simulator
        Node(
            package='stage_ros2',
            executable='stage_ros2',
            name='stage',
            output='screen',
            arguments=[world_file],
        ),

        # 2. Simple test robot
        Node(
            package='uncertainty_slam',
            executable='simple_test_robot',
            name='simple_test_robot',
            output='screen',
        ),

        # 3. SLAM Toolbox with MINIMAL config
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[{
                'odom_frame': 'robot_0/odom',
                'map_frame': 'map',
                'base_frame': 'robot_0/base_footprint',
                'scan_topic': '/robot_0/base_scan',
                'use_map_saver': True,
                'mode': 'mapping',
                
                # DEAD SIMPLE PARAMETERS
                'resolution': 0.05,
                'map_update_interval': 1.0,
                'minimum_travel_distance': 0.2,
                'minimum_travel_heading': 0.2,
                'max_laser_range': 8.0,
                'minimum_time_interval': 0.5,
            }]
        ),

        # 4. RViz
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
        ),
    ])

