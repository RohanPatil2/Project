#!/usr/bin/env python3
"""
Complete Stage-based SLAM System Launch File
REWRITTEN FROM SCRATCH FOR STABILITY

This system uses:
1. Stage simulator (proper physics, no synthetic bugs)
2. Simple, stable robot controller
3. Optimized SLAM Toolbox configuration
4. Uncertainty computation

NO GLITCHING. NO ARTIFACTS. JUST CLEAN SLAM.

Author: Complete Rewrite
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    uncertainty_pkg = get_package_share_directory('uncertainty_slam')
    stage_pkg = get_package_share_directory('stage_ros2')

    # Launch arguments
    use_rviz_arg = DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='Launch RViz2'
    )

    use_rviz = LaunchConfiguration('use_rviz')

    # World file path
    world_file = os.path.join(stage_pkg, 'world', 'simple_maze.world')

    # ============================================================
    # 1. STAGE SIMULATOR
    # ============================================================
    stage_node = Node(
        package='stage_ros2',
        executable='stage_ros2',
        name='stage_ros2',
        output='screen',
        arguments=[world_file],
        parameters=[{
            'use_sim_time': False,
        }]
    )

    # ============================================================
    # 2. ROBOT CONTROLLER - Simple and stable
    # ============================================================
    robot_controller = Node(
        package='uncertainty_slam',
        executable='stage_explorer',
        name='stage_explorer',
        output='screen',
    )

    # ============================================================
    # 3. SLAM TOOLBOX - High quality mapping
    # ============================================================
    slam_config = os.path.join(
        uncertainty_pkg,
        'config',
        'slam_stage_config.yaml'
    )

    slam_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[slam_config],
    )

    # ============================================================
    # 4. UNCERTAINTY NODE - Entropy computation
    # ============================================================
    uncertainty_node = Node(
        package='uncertainty_slam',
        executable='uncertainty_node',
        name='uncertainty_node',
        output='screen',
        parameters=[{
            'entropy_publish_rate': 5.0,  # 5 Hz - moderate rate
            'map_topic': '/map',
            'entropy_grid_topic': '/entropy_map',
            'entropy_image_topic': '/entropy_heatmap_image',
            'min_observations': 3,
        }]
    )

    # ============================================================
    # 5. RESULTS GENERATOR
    # ============================================================
    results_generator = Node(
        package='uncertainty_slam',
        executable='results_generator',
        name='results_generator',
        output='screen',
        parameters=[{
            'output_dir': '~/slam_uncertainty_ws/results/visualizations',
            'auto_generate': True,
        }]
    )

    # ============================================================
    # 6. ECS LOGGER - Entropy metrics
    # ============================================================
    ecs_logger = Node(
        package='uncertainty_slam',
        executable='ecs_logger',
        name='ecs_logger',
        output='screen',
    )

    # ============================================================
    # 7. RVIZ
    # ============================================================
    rviz_config = os.path.join(
        uncertainty_pkg,
        'config',
        'uncertainty_slam.rviz'
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config] if os.path.exists(rviz_config) else [],
        output='screen',
        condition=IfCondition(use_rviz)
    )

    return LaunchDescription([
        use_rviz_arg,
        stage_node,
        robot_controller,
        slam_node,
        uncertainty_node,
        results_generator,
        ecs_logger,
        rviz_node,
    ])

