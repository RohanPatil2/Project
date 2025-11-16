#!/bin/bash
# Quick test of the autonomous exploration system

echo "=========================================="
echo "🧪 TESTING AUTONOMOUS SLAM SYSTEM"
echo "=========================================="
echo ""

cd ~/slam_uncertainty_ws
source install/setup.bash

echo "✅ Sourced workspace"
echo ""
echo "🚀 Launching system (will run for 2 minutes as test)..."
echo ""
echo "What you should see:"
echo "  - Stage window with cave map and red robot"
echo "  - RViz window with displays"
echo "  - Robot starts moving after 5 seconds"
echo "  - Console shows waypoint progress"
echo ""
echo "Press CTRL+C to stop when you've verified it's working"
echo ""
echo "=========================================="
echo ""

# Launch the system
ros2 launch uncertainty_slam full_system_gmapping.launch.py world:=uncertainty_slam use_rviz:=true
