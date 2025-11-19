from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'uncertainty_slam'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*.world')),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Rohan Upendra Patil',
    maintainer_email='rohan@example.com',
    description='Real-Time Uncertainty-Aware 2D SLAM with Entropy Quantification',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'uncertainty_node = uncertainty_slam.uncertainty_node:main',
            'active_explorer = uncertainty_slam.active_explorer:main',
            'advanced_explorer = uncertainty_slam.advanced_explorer:main',
            'autonomous_explorer = uncertainty_slam.autonomous_explorer:main',
            'ecs_logger = uncertainty_slam.ecs_logger:main',
            'synthetic_robot = uncertainty_slam.synthetic_robot:main',
            'results_generator = uncertainty_slam.results_generator:main',
            'static_map_publisher = uncertainty_slam.static_map_publisher:main',
            'stage_explorer = uncertainty_slam.stage_explorer:main',
            'simple_test_robot = uncertainty_slam.simple_test_robot:main',
            'final_heatmap_saver = uncertainty_slam.final_heatmap_saver:main',
        ],
    },
)
