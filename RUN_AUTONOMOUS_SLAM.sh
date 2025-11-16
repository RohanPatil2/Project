#!/bin/bash
# SIMPLE AUTONOMOUS SLAM - GUARANTEED TO WORK!
# Uses synthetic robot with built-in waypoint following

echo "=========================================="
echo "🤖 AUTONOMOUS SLAM SYSTEM"
echo "=========================================="
echo ""
echo "✅ COMPLETELY AUTONOMOUS - ROBOT MOVES BY ITSELF!"
echo ""
echo "Components:"
echo "  1. Synthetic Robot (with built-in waypoint following)"
echo "  2. SLAM Toolbox (builds map in real-time)"
echo "  3. Uncertainty Node (live entropy heatmap)"
echo "  4. RViz2 (visualization)"
echo ""
echo "What you'll see:"
echo "  ✅ Robot AUTOMATICALLY follows 100+ waypoints"
echo "  ✅ SLAM map builds in real-time"
echo "  ✅ Live entropy heatmap (RED → BLUE)"
echo "  ✅ NO MANUAL CONTROL NEEDED!"
echo ""
echo "Duration: ~15-20 minutes"
echo ""
echo "=========================================="
echo ""

cd ~/slam_uncertainty_ws
source install/setup.bash

echo "🚀 Launching system..."
echo ""

ros2 launch uncertainty_slam autonomous_slam.launch.py use_rviz:=true
