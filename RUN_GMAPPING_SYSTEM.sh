#!/bin/bash
# Launch Complete GMapping-Based Uncertainty-Aware SLAM System
# With Stage Simulator + Live Entropy Heatmap Visualization

echo "=========================================="
echo "🤖 AUTONOMOUS EXPLORATION SYSTEM"
echo "=========================================="
echo ""
echo "✅ COMPLETELY AUTONOMOUS - NO MANUAL CONTROL!"
echo ""
echo "Components:"
echo "  1. Stage Simulator (pre-rendered 16m×16m cave map)"
echo "  2. GMapping SLAM (particle filter)"
echo "  3. Autonomous Explorer (92 waypoint pre-fixed path)"
echo "  4. Live Entropy Heatmap (RED → BLUE visualization)"
echo "  5. RViz2 (real-time display)"
echo ""
echo "=========================================="
echo ""

# Source the workspace
source install/setup.bash

# Check if Stage world file exists
WORLD_FILE="src/stage_ros2/world/uncertainty_slam.world"
if [ ! -f "$WORLD_FILE" ]; then
    echo "⚠️  WARNING: Custom world file not found at $WORLD_FILE"
    echo "    Using default 'cave' world instead"
    WORLD="cave"
else
    echo "✅ Using custom uncertainty_slam world"
    WORLD="uncertainty_slam"
fi

# Launch the complete system
echo ""
echo "🚀 Launching system..."
echo ""
echo "What will happen:"
echo "  ✅ Stage opens with pre-rendered 16m×16m cave map"
echo "  ✅ Robot appears at starting position (-6, -6)"
echo "  ✅ RViz opens with live entropy heatmap overlay"
echo "  ✅ After 5 seconds, robot AUTOMATICALLY starts exploring"
echo "  ✅ Robot follows 92-waypoint pre-fixed path"
echo "  ✅ Watch entropy change RED → BLUE as robot explores!"
echo "  ✅ Exploration completes in ~15-20 minutes"
echo "  ✅ Results auto-generated when done"
echo ""
echo "🎬 NO MANUAL CONTROL NEEDED - JUST WATCH!"
echo ""
echo "=========================================="
echo ""

# Launch the full system
ros2 launch uncertainty_slam full_system_gmapping.launch.py world:=$WORLD use_rviz:=true
