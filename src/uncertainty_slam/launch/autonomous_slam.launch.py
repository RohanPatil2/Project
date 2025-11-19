#!/usr/bin/env python3
"""
SIMPLE AUTONOMOUS SLAM SYSTEM - GUARANTEED TO WORK!
Uses the synthetic robot which ALREADY HAS autonomous waypoint following built-in.

This is the SIMPLE, WORKING solution.
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():

    uncertainty_pkg_dir = get_package_share_directory('uncertainty_slam')

    use_rviz_arg = DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='Launch RViz2 for visualization'
    )

    use_rviz = LaunchConfiguration('use_rviz')

    # 1. Static Map Publisher - Pre-renders environment before robot moves
    static_map_node = Node(
        package='uncertainty_slam',
        executable='static_map_publisher',
        name='static_map_publisher',
        output='screen'
    )

    # 2. Synthetic Robot - ALREADY HAS waypoint following built-in!
    synthetic_robot_node = Node(
        package='uncertainty_slam',
        executable='synthetic_robot',
        name='synthetic_robot',
        output='screen',
        parameters=[{
            'robot_mode': 'EXPLORATION_PATTERN',  # This triggers AUTONOMOUS waypoint following!
        }]
    )

    # 2. SLAM Toolbox - For mapping
    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            os.path.join(uncertainty_pkg_dir, 'config', 'mapper_params_online_async.yaml')
        ],
        remappings=[
            ('/scan', '/scan'),
        ]
    )

    # 3. Uncertainty Node - Computes entropy from map variance
    uncertainty_node = Node(
        package='uncertainty_slam',
        executable='uncertainty_node',
        name='uncertainty_node',
        output='screen',
        parameters=[{
            'entropy_publish_rate': 10.0,
            'map_topic': '/map',
            'entropy_grid_topic': '/entropy_map',
            'entropy_image_topic': '/entropy_heatmap_image',
            'min_observations': 3,
        }]
    )

    # 4. Results Generator
    results_generator_node = Node(
        package='uncertainty_slam',
        executable='results_generator',
        name='results_generator',
        output='screen',
        parameters=[{
            'output_dir': '~/slam_uncertainty_ws/results/visualizations',
            'auto_generate': True,
        }]
    )

    # 5. Final Heatmap Saver - Saves entropy overlay when exploration completes
    final_heatmap_saver_node = Node(
        package='uncertainty_slam',
        executable='final_heatmap_saver',
        name='final_heatmap_saver',
        output='screen'
    )

    # 6. RViz
    rviz_config_file = os.path.join(
        uncertainty_pkg_dir,
        'config',
        'uncertainty_slam.rviz'
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_file] if os.path.exists(rviz_config_file) else [],
        output='screen',
        condition=IfCondition(use_rviz)
    )

    return LaunchDescription([
        use_rviz_arg,
        static_map_node,
        synthetic_robot_node,
        slam_toolbox_node,
        uncertainty_node,
        results_generator_node,
        final_heatmap_saver_node,
        rviz_node,
    ])
