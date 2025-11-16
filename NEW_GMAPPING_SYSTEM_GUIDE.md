# 🎯 NEW SYSTEM: Proper GM apping SLAM with Live Entropy Visualization

## ✅ What's Fixed

### Before (Problems):
❌ **No pre-rendered map** - Robot was using synthetic raycasting
❌ **No real SLAM** - SLAM Toolbox doesn't provide particle entropy
❌ **Waypoint following** - Not intelligent exploration
❌ **Unclear visualization** - Map wasn't properly rendered

### NOW (Solutions):
✅ **Pre-rendered map in Stage** - 16m×16m cave environment loaded from bitmap
✅ **GMapping particle filter** - Proper RBPF SLAM with pose entropy
✅ **Cell-wise map entropy** - Your existing uncertainty_node tracks map variance
✅ **Live color heatmap** - Beautiful JET colormap overlay on real SLAM map
✅ **Ready for frontier exploration** - Can add m-explore-ros2 next

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────┐
│                   STAGE SIMULATOR                      │
│         (Pre-rendered 16m×16m cave.png map)           │
│                                                        │
│  • Loads bitmap as environment                         │
│  • Provides perfect ground truth map                   │
│  • Simulates laser scanner (360°, 10m range)          │
│  • Publishes /scan, /odom, /tf                        │
└──────────────┬─────────────────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────────────────┐
│                  GMAPPING SLAM NODE                    │
│          (Rao-Blackwellized Particle Filter)          │
│                                                        │
│  • 30 particles for pose estimation                    │
│  • Builds occupancy grid map from laser scans         │
│  • Publishes /map (the SLAM-generated map)            │
│  • Publishes /entropy (pose uncertainty)              │
│  • Updates map every 1 second                         │
└──────────────┬─────────────────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────────────────┐
│            UNCERTAINTY QUANTIFICATION NODE             │
│          (Cell-wise Map Entropy Computation)          │
│                                                        │
│  • Monitors /map updates from GMapping                │
│  • Tracks cell-wise variance over time                │
│  • Computes Shannon entropy from variance             │
│  • Publishes /entropy_map (grid overlay)              │
│  • Publishes /entropy_heatmap_image (color image)     │
│  • Updates at 10 Hz                                   │
└──────────────┬─────────────────────────────────────────┘
               │
               ▼
┌────────────────────────────────────────────────────────┐
│                     RVIZ2 DISPLAY                      │
│                                                        │
│  Layers (bottom to top):                               │
│  1. Grid (reference)                                   │
│  2. /map (SLAM occupancy grid) - 70% alpha            │
│  3. /entropy_map (color overlay) - 60% alpha          │
│  4. /entropy_heatmap_image (side panel)               │
│  5. Laser scan visualization                          │
│  6. Robot model                                        │
└────────────────────────────────────────────────────────┘
```

---

## 🚀 How to Run

### Quick Start:

```bash
cd ~/slam_uncertainty_ws
./RUN_GMAPPING_SYSTEM.sh
```

That's it! The script will:
1. Source the workspace
2. Check for custom world file
3. Launch Stage + GMapping + Uncertainty Node + RViz2

### What You'll See:

**Stage Window** (Simulator):
- 16m×16m cave environment
- Red pioneer robot with laser scanner
- Laser beams visible
- Ground truth map (this is what Stage knows)

**RViz Window** (Visualization):
- **Map layer** - GMapping's SLAM-built map (starts empty, fills as robot explores)
- **Entropy overlay** - Color-coded uncertainty (blue=certain, red=uncertain)
- **Heatmap image** - Side panel showing full entropy heatmap
- **Laser scan** - Red points showing current sensor data
- **Robot model** - 3D representation of robot

---

## 🎮 Controlling the Robot

### Option 1: Keyboard Teleop (Manual Control)

Open a new terminal:

```bash
cd ~/slam_uncertainty_ws
source install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap /cmd_vel:=/robot_0/cmd_vel
```

**Controls**:
- `i` - Move forward
- `,` - Move backward
- `j` - Turn left
- `l` - Turn right
- `k` - Stop
- `q/z` - Increase/decrease speed
- `CTRL+C` - Quit

### Option 2: Simple Waypoint Explorer (TODO - Can Create)

Create a simple Python script to follow waypoints:

```python
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class SimpleExplorer(Node):
    def __init__(self):
        super().__init__('simple_explorer')
        self.pub = self.create_publisher(Twist, '/robot_0/cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.explore)

    def explore(self):
        msg = Twist()
        msg.linear.x = 0.3  # Move forward
        msg.angular.z = 0.2  # Slight turn
        self.pub.publish(msg)

def main():
    rclpy.init()
    node = SimpleExplorer()
    rclpy.spin(node)

if __name__ == '__main__':
    main()
```

### Option 3: Install Frontier Exploration (Advanced - Next Step)

```bash
cd ~/slam_uncertainty_ws/src
git clone https://github.com/robo-friends/m-explore-ros2.git
cd ~/slam_uncertainty_ws
colcon build --packages-select explore_lite
source install/setup.bash
ros2 launch explore_lite explore.launch.py
```

---

## 📊 Understanding the Entropy Visualization

### What the Colors Mean:

**Blue/Cyan** (Low Entropy 0.0-0.3):
- Well-explored areas
- Robot has passed through multiple times
- SLAM is confident about these cells
- Map values are stable

**Green/Yellow** (Medium Entropy 0.3-0.6):
- Partially explored areas
- Robot has seen once or twice
- Some uncertainty remains
- Map still updating

**Orange/Red** (High Entropy 0.6-1.0):
- Unexplored or rarely seen
- High uncertainty
- Frontiers of exploration
- Target areas for active sensing

### Expected Behavior During Exploration:

**Start** (0-30 seconds):
- Entire map is RED (unknown, high entropy)
- Small blue spot where robot starts
- GMapping begins building map

**Early Exploration** (30 seconds - 5 minutes):
- Blue region expands as robot moves
- SLAM map fills in walls and obstacles
- Entropy decreases in explored areas
- Clear blue "trail" behind robot

**Mid Exploration** (5-10 minutes):
- Most visited areas are blue/green
- Unvisited rooms/corridors stay red
- Entropy overlay shows clear patterns
- Walls become certain (blue), unknown space stays red

**Late Exploration** (10+ minutes):
- Majority of navigable space is blue
- Some red zones remain (unexplored areas)
- Entropy map shows exploration progress
- Can use this to guide robot to high-entropy regions

---

## 🔍 Key Topics (for Debugging/Monitoring)

### Published Topics:

```bash
# SLAM Map
ros2 topic echo /map                    # Occupancy grid from GMapping
ros2 topic hz /map                      # Should update ~1 Hz

# Entropy (Pose Uncertainty from GMapping)
ros2 topic echo /entropy                # Float64: pose entropy
ros2 topic hz /entropy                  # Updates when scan is processed

# Entropy Map (Cell-wise from Uncertainty Node)
ros2 topic echo /entropy_map            # OccupancyGrid of entropy values
ros2 topic hz /entropy_map              # Should be 10 Hz

# Live Color Heatmap
ros2 topic echo /entropy_heatmap_image  # RGB8 image with JET colormap
ros2 topic hz /entropy_heatmap_image    # Should be 10 Hz

# Sensor Data
ros2 topic echo /robot_0/base_scan      # Laser scan data
ros2 topic hz /robot_0/base_scan        # Should be 10 Hz (Stage default)

# Robot Control
ros2 topic pub /robot_0/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.3}, angular: {z: 0.0}}"
```

### Checking TF Tree:

```bash
ros2 run tf2_tools view_frames
# Opens PDF showing TF tree:
# map -> robot_0/odom -> robot_0/base_footprint -> robot_0/base_laser
```

---

## 🎨 Customizing the Map

### Using Different Stage Worlds:

Available pre-made worlds in `/src/stage_ros2/world/`:
- `cave` - Cave environment (default, 16m×16m)
- `hallway` - Hallway environment
- `straden` - Street/city environment

```bash
# Run with different world:
ros2 launch uncertainty_slam full_system_gmapping.launch.py world:=hallway
```

### Creating Custom World:

1. **Create a bitmap** (PNG or PGM):
   - Black (0,0,0) = walls/obstacles
   - White (255,255,255) = free space
   - Resolution: ~10-50 pixels per meter recommended
   - Example: 800×800 pixels for 16m×16m = 50 px/m

2. **Save to** `/src/stage_ros2/world/bitmaps/my_map.png`

3. **Create world file** `/src/stage_ros2/world/my_map.world`:

```ruby
include "include/robots.inc"

resolution 0.02
interval_sim 100

window ( size [ 800 600 ] scale 50.0 center [ 0 0 ] )

define floorplan model
(
  color "gray30"
  boundary 1
  laser_return 1
)

floorplan
(
  name "my_custom_map"
  size [16.000 16.000 0.800]  # Adjust size to match your map
  pose [0 0 0 0]
  bitmap "bitmaps/my_map.png"
)

pioneer2dx_with_laser
(
  name "robot_0"
  color "red"
  pose [ -6.0 -6.0 0 0.0 ]  # Starting position
)
```

4. **Run**:
```bash
ros2 launch uncertainty_slam full_system_gmapping.launch.py world:=my_map
```

---

## 🛠️ Tuning GMapping Parameters

Edit `/src/uncertainty_slam/launch/full_system_gmapping.launch.py`:

### For Faster Mapping:

```python
'particles': 15,          # Fewer particles (faster, less accurate)
'map_update_interval': 0.5,  # Update more frequently
'linearUpdate': 0.2,      # Process scans more often
```

### For Better Accuracy:

```python
'particles': 50,          # More particles (slower, more accurate)
'map_update_interval': 2.0,  # Update less frequently (more stable)
'iterations': 10,         # More scan matching iterations
```

### For Smaller Environments:

```python
'xmin': -5.0,
'ymin': -5.0,
'xmax': 5.0,
'ymax': 5.0,
'resolution': 0.025,      # Finer resolution (2.5cm)
```

### For Larger Environments:

```python
'xmin': -20.0,
'ymin': -20.0,
'xmax': 20.0,
'ymax': 20.0,
'resolution': 0.1,        # Coarser resolution (10cm)
```

---

## 📈 Performance Expectations

### Computational Requirements:

| Component | CPU Usage | Memory | Update Rate |
|-----------|-----------|--------|-------------|
| Stage Simulator | ~5% | ~50 MB | 10 Hz |
| GMapping SLAM | ~10-20% | ~100-200 MB | 1 Hz (map) |
| Uncertainty Node | ~5% | ~20 MB | 10 Hz |
| RViz2 | ~10% | ~100 MB | 30 FPS |
| **Total** | ~30-40% | ~300 MB | Real-time |

### Map Size vs Performance:

| Map Size | Cells | GMapping RAM | Entropy Node RAM | Real-time? |
|----------|-------|--------------|------------------|------------|
| 10m×10m @ 5cm | 200×200 = 40k | ~50 MB | ~5 MB | ✅ Yes |
| 16m×16m @ 5cm | 320×320 = 102k | ~100 MB | ~10 MB | ✅ Yes |
| 20m×20m @ 5cm | 400×400 = 160k | ~150 MB | ~15 MB | ✅ Yes |
| 50m×50m @ 5cm | 1000×1000 = 1M | ~500 MB | ~80 MB | ⚠️ Slow |

**Recommendation**: Keep maps under 20m×20m at 5cm resolution for best performance

---

## 🔬 Scientific Validation

### Entropy Sources:

**1. GMapping Pose Entropy** (`/entropy` topic):
```
H_pose = -Σ(w_i * log(w_i))
```
where w_i are normalized particle weights

**Meaning**: Uncertainty about robot's position
- High entropy = particles spread out = uncertain localization
- Low entropy = particles converged = confident localization

**2. Map Cell Entropy** (`/entropy_map` topic):
```
Var(cell_i) = E[X²] - E[X]²
H_cell = f(Var(cell_i))
```
where X is occupancy value over time

**Meaning**: Uncertainty about map cell state
- High entropy = cell value fluctuating = uncertain occupancy
- Low entropy = cell value stable = confident mapping

### Why Two Entropy Measures?

They capture different aspects:
- **Pose entropy** - "Where am I?" (localization uncertainty)
- **Map entropy** - "What's here?" (mapping uncertainty)

Both are important for active SLAM!

---

## 🐛 Troubleshooting

### Issue: Stage doesn't launch

**Check**:
```bash
ros2 pkg list | grep stage_ros2
```

**Fix** (if missing):
```bash
cd ~/slam_uncertainty_ws/src
git clone https://github.com/tuw-robotics/stage_ros2.git
cd ~/slam_uncertainty_ws
colcon build --packages-select stage_ros2
```

### Issue: GMapping doesn't publish /map

**Check frame names**:
```bash
ros2 topic echo /robot_0/base_scan --once
# Should show frame_id: robot_0/base_laser

ros2 topic echo /tf --once
# Should show transforms for robot_0 frames
```

**Check GMapping is running**:
```bash
ros2 node list | grep slam_gmapping
```

### Issue: Entropy map is all gray/black

**Meaning**: Not enough map updates yet

**Wait** 30-60 seconds for GMapping to publish several map updates

**Check**:
```bash
ros2 topic hz /map
# Should show ~1 Hz update rate
```

### Issue: Robot doesn't move

**Check** if teleop is running:
```bash
ros2 node list | grep teleop
```

**Check** cmd_vel topic:
```bash
ros2 topic list | grep cmd_vel
# Should show /robot_0/cmd_vel
```

**Manually command**:
```bash
ros2 topic pub --once /robot_0/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5}}"
```

### Issue: RViz shows nothing

**Check** Fixed Frame is set to `map`:
- In RViz → Displays → Global Options → Fixed Frame → "map"

**Check** topics are correct:
- Map display → Topic → `/map`
- Entropy overlay → Topic → `/entropy_map`

**Reset** RViz config:
```bash
rviz2 -d ~/slam_uncertainty_ws/src/uncertainty_slam/config/gmapping_entropy_viz.rviz
```

---

## 🎯 Next Steps

### Immediate (Can do now):

1. **Run the system**:
   ```bash
   ./RUN_GMAPPING_SYSTEM.sh
   ```

2. **Control robot manually** (teleop_twist_keyboard)

3. **Watch live entropy heatmap** update in RViz

4. **Drive around** and see SLAM build the map

5. **Observe entropy decrease** in explored areas

### Short-term (Next session):

6. **Create simple autonomous explorer** (random walk or wall following)

7. **Add frontier exploration** (m-explore-ros2)

8. **Create custom maps** for specific testing scenarios

9. **Record rosbag** for offline replay and analysis

10. **Tune GMapping parameters** for your specific needs

### Long-term (Research goals):

11. **Compare exploration strategies** (frontier vs entropy-driven vs random)

12. **Quantify exploration efficiency** (coverage vs time vs entropy reduction)

13. **Test on real robot** (Turtlebot, Kobuki, etc.)

14. **Write research paper** comparing uncertainty quantification methods

15. **Publish results** at ICRA/IROS/RA-L

---

## 📚 Key Differences from Old System

| Aspect | Old System | NEW System |
|--------|------------|------------|
| **Simulator** | Synthetic raycasting | Stage (pre-rendered bitmap) |
| **SLAM** | SLAM Toolbox (graph) | GMapping (particle filter) |
| **Map Source** | Generated on-the-fly | Loaded from PNG file |
| **Entropy** | Map variance only | Pose entropy + map variance |
| **Exploration** | Fixed waypoints | Manual teleop (frontier next) |
| **Visualization** | Basic | RViz with layered entropy overlay |
| **Realism** | Synthetic | Realistic RBPF simulation |

---

## 📖 References

### GMapping:
- Original paper: "Improved Techniques for Grid Mapping with Rao-Blackwellized Particle Filters" (Grisetti et al., 2007)
- ROS 2 port: https://github.com/GMHadou/slam_gmapping_Humble

### Stage Simulator:
- Official manual: https://playerstage.sourceforge.net/doc/Stage-3.2.1/
- ROS 2 wrapper: https://github.com/tuw-robotics/stage_ros2

### Uncertainty Quantification:
- Your original implementation (map variance → entropy)
- Shannon entropy: H = -Σ p(x) log p(x)

### Active SLAM:
- Frontier exploration: "Robotic Mapping and Exploration" (Yamauchi, 1997)
- Information-theoretic: "Active SLAM using Model Predictive Control" (Valencia et al., 2012)

---

## ✅ System Checklist

Before running, verify:

- [x] Stage world file exists (`uncertainty_slam.world`)
- [x] GMapping package built successfully
- [x] Uncertainty node ready (`uncertainty_node.py`)
- [x] RViz config file created (`gmapping_entropy_viz.rviz`)
- [x] Launch file created (`full_system_gmapping.launch.py`)
- [x] Run script executable (`RUN_GMAPPING_SYSTEM.sh`)

All done! 🎉

---

## 🎉 Summary

**You now have**:
✅ Proper particle filter SLAM (GMapping)
✅ Pre-rendered map environment (Stage simulator)
✅ Live entropy heatmap visualization (JET colormap)
✅ Cell-wise map uncertainty quantification
✅ Real-time performance (10 Hz updates)
✅ Easy-to-use launch system

**Ready to run**:
```bash
cd ~/slam_uncertainty_ws
./RUN_GMAPPING_SYSTEM.sh
```

Then in another terminal:
```bash
cd ~/slam_uncertainty_ws
source install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args --remap /cmd_vel:=/robot_0/cmd_vel
```

**Drive around and watch the beautiful live entropy heatmap!** 🗺️🎨

The map will build in real-time, and the entropy overlay will show you exactly where the SLAM system is uncertain. Blue = confident, Red = uncertain!

---

**Author**: Rohan Upendra Patil
**System**: GMapping SLAM + Stage Simulator + Live Entropy Visualization
**Status**: ✅ READY TO RUN
**Date**: 2025-01-16
