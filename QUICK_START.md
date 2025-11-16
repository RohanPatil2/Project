# 🚀 QUICK START GUIDE

## ✅ Your System is Ready!

Everything is installed and configured. Here's how to run it:

---

## 📋 Prerequisites Check

```bash
cd ~/slam_uncertainty_ws
source install/setup.bash

# Verify packages are built:
ros2 pkg list | grep -E "stage_ros2|slam_gmapping|uncertainty_slam"
```

**Should show**:
- stage_ros2
- slam_gmapping
- openslam_gmapping
- uncertainty_slam

---

## 🎯 METHOD 1: Run Complete System (Easiest)

### Terminal 1 - Launch Everything:

```bash
cd ~/slam_uncertainty_ws
source install/setup.bash
./RUN_GMAPPING_SYSTEM.sh
```

This launches:
- ✅ Stage simulator (16m×16m cave map)
- ✅ GMapping SLAM (particle filter)
- ✅ Uncertainty quantification node
- ✅ RViz2 visualization

**Wait for all nodes to start** (~10 seconds)

### Terminal 2 - Control Robot:

```bash
cd ~/slam_uncertainty_ws
source install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap /cmd_vel:=/robot_0/cmd_vel
```

**Keyboard controls**:
- `i` - Move forward
- `,` - Move backward
- `j` - Turn left
- `l` - Turn right
- `k` - Stop
- `CTRL+C` - Quit

---

## 🎯 METHOD 2: Step-by-Step (For Debugging)

### Terminal 1 - Stage Simulator:

```bash
cd ~/slam_uncertainty_ws
source install/setup.bash
ros2 launch stage_ros2 stage.launch.py world:=uncertainty_slam
```

**Check**: Stage window opens with cave map and red robot

### Terminal 2 - GMapping SLAM:

```bash
cd ~/slam_uncertainty_ws
source install/setup.bash
ros2 run slam_gmapping slam_gmapping_node \
  --ros-args \
  -p base_frame:=robot_0/base_footprint \
  -p odom_frame:=robot_0/odom \
  -p map_frame:=map \
  --remap /scan:=/robot_0/base_scan
```

**Check**: Should see "Laser Pose" messages

### Terminal 3 - Uncertainty Node:

```bash
cd ~/slam_uncertainty_ws
source install/setup.bash
ros2 run uncertainty_slam uncertainty_node
```

**Check**: Should see "Uncertainty SLAM Node initialized"

### Terminal 4 - RViz:

```bash
cd ~/slam_uncertainty_ws
source install/setup.bash
rviz2 -d src/uncertainty_slam/config/gmapping_entropy_viz.rviz
```

**Check**: RViz opens with configured displays

### Terminal 5 - Robot Control:

```bash
cd ~/slam_uncertainty_ws
source install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap /cmd_vel:=/robot_0/cmd_vel
```

---

## 🔍 Verify System is Working

### Check Running Nodes:

```bash
ros2 node list
```

**Should show**:
- /slam_gmapping
- /uncertainty_node
- /stageros
- /results_generator
- /rviz2 (if running)
- /teleop_twist_keyboard (if running)

### Check Topics:

```bash
ros2 topic list
```

**Key topics**:
- `/robot_0/base_scan` - Laser data
- `/robot_0/odom` - Odometry
- `/robot_0/cmd_vel` - Robot commands
- `/map` - SLAM map
- `/entropy_map` - Entropy overlay
- `/entropy_heatmap_image` - Color heatmap

### Monitor Entropy Updates:

```bash
ros2 topic hz /entropy_map
```

**Should show**: ~10 Hz update rate

### View Map Updates:

```bash
ros2 topic hz /map
```

**Should show**: ~1 Hz update rate

---

## 🎨 What You Should See

### Stage Window:
- Gray cave environment (pre-rendered)
- Red pioneer robot
- Green laser scan rays
- Robot moves when you press keys

### RViz Window:
- **Map layer**: Gray occupancy grid (builds as robot moves)
- **Entropy overlay**: Color gradient (starts red, turns blue as explored)
- **Laser scan**: Red points
- **Robot model**: 3D robot visualization
- **Heatmap image panel**: Full entropy visualization

### Expected Behavior:
1. **Start**: Everything is red (high entropy/unknown)
2. **Drive forward**: Blue area expands behind robot
3. **Turn and explore**: Red areas turn blue as robot sees them
4. **Watch map build**: SLAM creates map in real-time
5. **See entropy decrease**: Uncertainty reduces in explored areas

---

## 🐛 Troubleshooting

### Problem: "Package not found"

```bash
cd ~/slam_uncertainty_ws
colcon build --symlink-install
source install/setup.bash
```

### Problem: Stage window doesn't open

```bash
# Check if Stage is installed:
ros2 pkg list | grep stage_ros2

# If missing:
cd ~/slam_uncertainty_ws
colcon build --packages-select stage_ros2
source install/setup.bash
```

### Problem: No /map topic

```bash
# Check GMapping is running:
ros2 node list | grep slam

# Check laser scan is publishing:
ros2 topic hz /robot_0/base_scan

# Check frame names match:
ros2 run tf2_tools view_frames
```

### Problem: Entropy map all gray

**Wait 30-60 seconds** for GMapping to publish enough map updates

```bash
# Check map is updating:
ros2 topic hz /map

# Should show ~1 Hz
```

### Problem: Robot doesn't move

```bash
# Check cmd_vel topic exists:
ros2 topic list | grep cmd_vel

# Test manually:
ros2 topic pub --once /robot_0/cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.5}, angular: {z: 0.0}}"
```

### Problem: RViz shows nothing

- Check "Fixed Frame" is set to "map"
- Check topic names are correct (/map, /entropy_map)
- Wait for first map update (~10-30 seconds)

---

## 💡 Tips for Best Results

### 1. Drive Slowly
- Use lower speeds to get better SLAM results
- Sudden movements can confuse particle filter

### 2. Explore Systematically
- Visit all rooms methodically
- Don't just spin in place
- Cover the whole map

### 3. Watch the Entropy
- Red = unexplored (go there!)
- Blue = explored (avoid revisiting)
- Use entropy to guide exploration

### 4. Wait for Map Updates
- GMapping updates every 1 second
- Don't rush - let SLAM process scans
- Quality over speed

---

## 📊 Performance Expectations

### System Resources:
- **CPU**: 30-40% total
- **RAM**: ~300 MB
- **Real-time**: Yes (10 Hz entropy updates)

### Exploration Time:
- **16m×16m cave**: 10-15 minutes to explore fully
- **Smaller maps**: 5-10 minutes
- **Larger maps**: 20-30 minutes

---

## 🎯 Next Steps

### After Basic Testing:

1. **Try different worlds**:
   ```bash
   ros2 launch uncertainty_slam full_system_gmapping.launch.py world:=cave
   ros2 launch uncertainty_slam full_system_gmapping.launch.py world:=hallway
   ```

2. **Create custom map** (see NEW_GMAPPING_SYSTEM_GUIDE.md)

3. **Add autonomous exploration** (frontier-based)

4. **Record data** for offline analysis:
   ```bash
   ros2 bag record /map /entropy_map /entropy_heatmap_image /scan /odom
   ```

5. **Tune parameters** for better performance

---

## 📚 Documentation

- **This guide**: `QUICK_START.md`
- **Full technical guide**: `NEW_GMAPPING_SYSTEM_GUIDE.md`
- **Code analysis**: `COMPREHENSIVE_CODE_ANALYSIS.md`
- **Summary**: `SYSTEM_COMPLETE_SUMMARY.md`

---

## ✅ Success Checklist

Before you're done, verify:

- [ ] Stage window opens with cave map
- [ ] Robot visible in Stage
- [ ] RViz opens with displays configured
- [ ] Robot moves when you press keys
- [ ] /map topic updates (~1 Hz)
- [ ] /entropy_map topic updates (~10 Hz)
- [ ] Laser scan visible in RViz
- [ ] Entropy overlay shows colors (red → blue)
- [ ] Map builds as robot explores
- [ ] Entropy decreases in explored areas

**If all checked**: 🎉 **SUCCESS! Your system is working!**

---

## 🎨 Final Result

When working correctly, you'll see:
- Beautiful live entropy heatmap
- SLAM map building in real-time
- Color gradient showing uncertainty
- Red (high uncertainty) → Blue (low uncertainty)
- Dynamic visualization as robot explores

**This is exactly what you asked for!** 🚀

---

**Ready? Start with METHOD 1 above!** 🎯
