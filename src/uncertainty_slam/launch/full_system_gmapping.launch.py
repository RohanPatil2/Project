#!/usr/bin/env python3
"""
Complete Uncertainty-Aware SLAM System
Uses GMapping SLAM + Stage Simulator + Entropy Visualization

Components:
1. Stage Simulator - Pre-rendered map environment
2. GMapping - Particle filter SLAM with entropy
3. Uncertainty Node - Cell-wise entropy computation
4. RViz2 - Visualization with entropy overlay

Author: Rohan Upendra Patil
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.conditions import IfCondition
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():

    # Package directories
    uncertainty_pkg_dir = get_package_share_directory('uncertainty_slam')
    stage_pkg_share = FindPackageShare('stage_ros2')

    # Launch arguments
    world_arg = DeclareLaunchArgument(
        'world',
        default_value='uncertainty_slam',
        description='Stage world file name (without .world extension)'
    )

    use_rviz_arg = DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='Launch RViz2 for visualization'
    )

    # Get launch configurations
    world_name = LaunchConfiguration('world')
    use_rviz = LaunchConfiguration('use_rviz')

    # 1. Stage Simulator - Provides pre-rendered map environment
    stage_launch = IncludeLaunchDescription(
        PathJoinSubstitution([stage_pkg_share, 'launch', 'stage.launch.py']),
        launch_arguments={
            'world': world_name,
            'use_stamped_velocity': 'false',
            'enforce_prefixes': 'false',
            'one_tf_tree': 'true',
        }.items()
    )

    # 2. GMapping SLAM - Particle filter SLAM with pose entropy
    slam_gmapping_node = Node(
        package='slam_gmapping',
        executable='slam_gmapping_node',
        name='slam_gmapping',
        output='screen',
        parameters=[{
            # Frame names
            'base_frame': 'robot_0/base_footprint',
            'odom_frame': 'robot_0/odom',
            'map_frame': 'map',

            # Map parameters
            'map_update_interval': 1.0,  # Update map every 1 second
            'resolution': 0.05,          # 5cm per cell (matches 0.025m*2 from before)

            # Laser parameters
            'maxUrange': 10.0,  # Maximum range for map updates
            'maxRange': 10.0,   # Maximum laser range
            'sigma': 0.05,      # Laser sigma (measurement noise)

            # Particle filter parameters
            'particles': 30,         # Number of particles (more = better, slower)
            'iterations': 5,         # Scan matching iterations

            # Motion model parameters
            'linearUpdate': 0.3,     # Process scan when moved 0.3m
            'angularUpdate': 0.2,    # Process scan when rotated 0.2 rad (~11 degrees)
            'temporalUpdate': 3.0,   # Process scan every 3 seconds (if not moved)

            # Initial map size
            'xmin': -10.0,
            'ymin': -10.0,
            'xmax': 10.0,
            'ymax': 10.0,
            'delta': 0.05,  # Same as resolution

            # Likelihood parameters
            'llsamplerange': 0.01,
            'llsamplestep': 0.01,
            'lasamplerange': 0.005,
            'lasamplestep': 0.005,
        }],
        remappings=[
            ('/scan', '/robot_0/base_scan'),  # Stage publishes to /robot_0/base_scan
            ('/tf', '/tf'),
            ('/tf_static', '/tf_static'),
        ]
    )

    # 3. Uncertainty Quantification Node - Computes cell-wise entropy from map variance
    uncertainty_node = Node(
        package='uncertainty_slam',
        executable='uncertainty_node',
        name='uncertainty_node',
        output='screen',
        parameters=[{
            'entropy_publish_rate': 10.0,  # Publish at 10 Hz
            'map_topic': '/map',
            'entropy_grid_topic': '/entropy_map',
            'entropy_image_topic': '/entropy_heatmap_image',
            'min_observations': 3,  # Start publishing after 3 map updates
        }]
    )

    # 4. Autonomous Explorer - Follows pre-defined path automatically
    autonomous_explorer_node = Node(
        package='uncertainty_slam',
        executable='autonomous_explorer',
        name='autonomous_explorer',
        output='screen',
        parameters=[{
            'linear_speed': 0.3,
            'angular_speed': 0.5,
            'goal_tolerance': 0.3,
            'exploration_delay': 5.0,  # Wait 5 seconds before starting
        }]
    )

    # 5. Results Generator - Automatically saves results when exploration completes
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

    # 5. RViz2 - Visualization
    rviz_config_file = os.path.join(
        uncertainty_pkg_dir,
        'config',
        'gmapping_entropy_viz.rviz'
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
        # Arguments
        world_arg,
        use_rviz_arg,

        # Nodes
        stage_launch,
        slam_gmapping_node,
        uncertainty_node,
        autonomous_explorer_node,
        results_generator_node,
        rviz_node,
    ])
