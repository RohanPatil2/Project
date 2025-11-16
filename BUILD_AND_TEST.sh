#!/bin/bash
# Quick build and test script

cd ~/slam_uncertainty_ws

echo "======================================"
echo "Building uncertainty_slam package..."
echo "======================================"

source /opt/ros/humble/setup.bash
colcon build --packages-select uncertainty_slam --cmake-clean-first

echo ""
echo "======================================"
echo "Build complete! Sourcing install..."
echo "======================================"

source install/setup.bash

echo ""
echo "======================================"
echo "Launching system..."
echo "======================================"
echo "Map should appear as 20m×20m (200×200 cells at 0.1m resolution)"
echo "Robot starts at origin with 360° 10m laser"
echo "======================================"
echo ""

ros2 launch uncertainty_slam complete_system.launch.py

