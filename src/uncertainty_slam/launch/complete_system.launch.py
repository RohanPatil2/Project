#!/usr/bin/env python3
"""
Complete Uncertainty-Aware SLAM System Launch File
Launches all components with synthetic robot for immediate testing.
No external simulator required!
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from ament_index_python.packages import get_package_share_directory
from rclpy.qos import QoSDurabilityPolicy, QoSProfile
import os


def generate_launch_description():
    """Generate launch description for complete system."""

    # Get package directory
    pkg_dir = get_package_share_directory('uncertainty_slam')

    # Launch arguments
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    use_active_explorer = LaunchConfiguration('use_active_explorer', default='false')
    use_ecs_logger = LaunchConfiguration('use_ecs_logger', default='false')
    use_results_generator = LaunchConfiguration('use_results_generator', default='true')
    experiment_name = LaunchConfiguration('experiment_name', default='test_run')

    # SLAM Toolbox parameters
    slam_params_file = os.path.join(pkg_dir, 'config', 'mapper_params_online_async.yaml')

    return LaunchDescription([
        # Launch arguments
        DeclareLaunchArgument(
            'use_rviz',
            default_value='true',
            description='Launch RViz for visualization'
        ),
        DeclareLaunchArgument(
            'use_active_explorer',
            default_value='false',
            description='Enable active exploration'
        ),
        DeclareLaunchArgument(
            'use_ecs_logger',
            default_value='false',
            description='Enable ECS logging'
        ),
        DeclareLaunchArgument(
            'use_results_generator',
            default_value='true',
            description='Enable automatic results generation'
        ),
        DeclareLaunchArgument(
            'experiment_name',
            default_value='test_run',
            description='Experiment name for logging'
        ),

        # Info message
        LogInfo(msg='=== Launching Complete Uncertainty-Aware SLAM System ==='),
        LogInfo(msg='Components:'),
        LogInfo(msg='  1. Synthetic Robot (keyboard controllable)'),
        LogInfo(msg='  2. SLAM Toolbox'),
        LogInfo(msg='  3. Uncertainty Quantification Node'),
        LogInfo(msg='  4. RViz (if use_rviz:=true)'),
        LogInfo(msg='  5. Active Explorer (if use_active_explorer:=true)'),
        LogInfo(msg='  6. ECS Logger (if use_ecs_logger:=true)'),
        LogInfo(msg='  7. Results Generator (if use_results_generator:=true)'),
        LogInfo(msg=''),
        LogInfo(msg='Keyboard controls:'),
        LogInfo(msg='  w/x: forward/backward'),
        LogInfo(msg='  a/d: rotate left/right'),
        LogInfo(msg='  s: stop'),
        LogInfo(msg='  m: manual mode'),
        LogInfo(msg='  e: exploration pattern mode'),
        LogInfo(msg='  q: quit'),

        # 1. Synthetic Robot
        Node(
            package='uncertainty_slam',
            executable='synthetic_robot',
            name='synthetic_robot',
            output='screen',
            parameters=[{
                'use_sim_time': False,
                'start_mode': 'exploration_pattern',
            }]
        ),

        # 2. SLAM Toolbox
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[
                slam_params_file,
                {
                    'use_sim_time': False,
                }
            ],
            remappings=[
                ('/scan', '/scan'),
            ]
        ),

        # 3. Uncertainty Quantification Node
        Node(
            package='uncertainty_slam',
            executable='uncertainty_node',
            name='uncertainty_node',
            output='screen',
            parameters=[{
                'use_sim_time': False,
                'map_topic': '/map',
                'entropy_map_topic': '/entropy_map',
                'entropy_publish_rate': 10.0,  # Match parameter name in code
                'min_observations': 5,  # Reduced for faster initial display (was 10)
            }]
        ),

        # 4. RViz (conditional)
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', os.path.join(pkg_dir, 'config', 'uncertainty_slam.rviz')]
                      if os.path.exists(os.path.join(pkg_dir, 'config', 'uncertainty_slam.rviz'))
                      else [],
            output='screen',
            condition=IfCondition(use_rviz),
        ),

        # 5. Active Explorer (conditional)
        Node(
            package='uncertainty_slam',
            executable='active_explorer',
            name='active_explorer',
            output='screen',
            parameters=[{
                'use_sim_time': False,
                'min_entropy': 0.3,
                'max_distance': 5.0,
            }],
            condition=IfCondition(use_active_explorer),
        ),

        # 6. ECS Logger (conditional)
        Node(
            package='uncertainty_slam',
            executable='ecs_logger',
            name='ecs_logger',
            output='screen',
            parameters=[{
                'use_sim_time': False,
                'experiment_name': experiment_name,
                'record_duration': 300.0,  # 5 minutes
            }],
            condition=IfCondition(use_ecs_logger),
        ),

        # 7. Results Generator (conditional)
        Node(
            package='uncertainty_slam',
            executable='results_generator',
            name='results_generator',
            output='screen',
            parameters=[{
                'use_sim_time': False,
                'output_dir': '~/slam_uncertainty_ws/results/visualizations',
                'auto_generate': True,
            }],
            condition=IfCondition(use_results_generator),
        ),
    ])
