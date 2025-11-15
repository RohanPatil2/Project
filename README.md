# Uncertainty-Aware SLAM System

**Real-Time Uncertainty Quantification for 2D SLAM using Shannon Entropy**

This system implements autonomous SLAM with cell-wise uncertainty tracking and automatic visualization generation after complete map exploration.

---

## 🎯 Features

✅ **Autonomous Exploration** - Robot automatically explores the entire environment
✅ **Uncertainty Quantification** - Real-time Shannon entropy computation for each map cell
✅ **Complete Coverage** - Optimized boustrophedon (lawnmower) pattern with 139 waypoints
✅ **Stuck Recovery** - Automatic detection and recovery when robot gets stuck
✅ **Auto Visualization** - Generates graphs and heat-maps after 100% exploration
✅ **No Simulator Required** - Built-in synthetic robot with virtual environment

---

## 🚀 Quick Start

### Single Command Launch:

```bash
cd ~/slam_uncertainty_ws
./RUN_COMPLETE_SYSTEM.sh
```

This will:
1. Build the package
2. Launch all components
3. Start autonomous exploration
4. Generate visualizations after completion (~10-15 minutes)

### Results Location:

All visualizations will be saved to:
```
~/slam_uncertainty_ws/results/visualizations/
```

---

## 📊 What Gets Generated

After exploration completes, you'll get:

1. **Occupancy Map** (`occupancy_map_*.png`) - The SLAM-generated map
2. **Entropy Heat-Map** (`entropy_map_*.png`) - Uncertainty visualization
3. **Entropy Evolution** (`entropy_evolution_*.png`) - Uncertainty over time
4. **Combined View** (`combined_view_*.png`) - Side-by-side comparison
5. **Statistics Report** (`report_*.txt`) - Numerical analysis
6. **JSON Data** (`statistics_*.json`) - Machine-readable stats

---

## 🎮 System Components

### 1. Synthetic Robot
- **Purpose**: Generates laser scans and odometry without external simulator
- **Environment**: 10m × 10m room with 5 obstacles
- **Modes**:
  - `exploration_pattern` (default) - Autonomous systematic coverage
  - `manual` - Keyboard control (w/a/s/d/x)
  - `autonomous` - Navigate to specific goal

### 2. SLAM Toolbox
- **Algorithm**: Particle filter-based SLAM
- **Update Rate**: Real-time (~10 Hz)
- **Map Topic**: `/map`

### 3. Uncertainty Node
- **Method**: Cell-wise variance tracking → Shannon entropy
- **Rate**: 10 Hz entropy updates
- **Topics**:
  - `/entropy_map` - Entropy heat-map (OccupancyGrid)
  - `/map_average_entropy` - Average entropy value
  - `/map_max_entropy` - Maximum entropy value

### 4. Results Generator
- **Trigger**: Automatically when exploration reaches 100%
- **Delay**: 30 seconds after completion (allows SLAM to finalize)
- **Output**: High-resolution PNG images + statistics

---

## 🛠️ Advanced Usage

### Manual Launch (Custom Configuration):

```bash
source ~/slam_uncertainty_ws/install/setup.bash

ros2 launch uncertainty_slam complete_system.launch.py \
    use_rviz:=true \
    use_results_generator:=true \
    use_active_explorer:=false
```

### Launch Arguments:

| Argument | Default | Description |
|----------|---------|-------------|
| `use_rviz` | `true` | Enable RViz visualization |
| `use_results_generator` | `true` | Auto-generate visualizations |
| `use_active_explorer` | `false` | Entropy-driven exploration |
| `use_ecs_logger` | `false` | Experiment logging |

### Keyboard Controls (Manual Mode):

Press `m` in terminal to switch to manual mode, then:
- `w` / `x` - Forward / Backward
- `a` / `d` - Rotate Left / Right
- `s` - Stop
- `e` - Switch to exploration pattern mode
- `q` - Quit

---

## 📈 Exploration Pattern Details

**Total Waypoints**: 139
**Coverage Strategy**: Boustrophedon (lawnmower) with obstacle avoidance
**Waypoint Tolerance**: 0.35m (ensures dense coverage)

**Pattern Breakdown**:
- Bottom row (y = -4.0): 17 waypoints
- Vertical transition: 3 waypoints
- Second row (y = -2.0): 15 waypoints
- Vertical transition: 3 waypoints
- Center row (y = 0.0): 13 waypoints (avoids center obstacle)
- Vertical transition: 4 waypoints
- Fourth row (y = 2.0): 15 waypoints
- Vertical transition: 3 waypoints
- Top row (y = 4.0): 16 waypoints
- Right edge sweep: 11 waypoints
- Center diagonal passes: 6 waypoints
- Final return: 1 waypoint

**Stuck Recovery**:
- 5-second position check (skip if <10cm movement)
- 20-second timeout per waypoint
- Automatic waypoint skip with logging

---

## 🔍 Monitoring Progress

### Terminal Output:

```
✅ Coverage: 25.2% - Waypoint 35/139 reached at (2.50, -2.00)
→ Waypoint 36/139: target=(3.0, -2.0), dist=0.48m, time=1.2s
```

### Completion Message:

```
============================================================
🎉 ✅ EXPLORATION 100% COMPLETE!
============================================================
Total waypoints covered: 139
Waypoints skipped (stuck): 2
📊 Generating results in 30 seconds...
============================================================
```

### RViz Topics to Visualize:

1. `/map` - SLAM occupancy grid (grayscale)
2. `/entropy_map` - Uncertainty heat-map (hot colormap)
3. `/scan` - Laser scan data
4. `/robot_mode` - Current robot mode
5. `/exploration_status` - Exploration state

---

## 🐛 Troubleshooting

### Issue: Robot gets stuck at obstacles
**Solution**: Already handled! System has:
- Automatic stuck detection (5-second check)
- Waypoint timeout (20 seconds)
- Automatic skip to next waypoint

### Issue: Visualizations not generated
**Check**:
1. Did exploration reach 100%? Look for "EXPLORATION 100% COMPLETE" message
2. Wait 30 seconds after completion
3. Check `~/slam_uncertainty_ws/results/visualizations/` directory
4. Check terminal for results_generator errors

### Issue: Build fails
**Solution**:
```bash
cd ~/slam_uncertainty_ws
rm -rf build install log
colcon build --packages-select uncertainty_slam --symlink-install
```

### Issue: RViz doesn't show maps
**Solution**:
1. Check Fixed Frame is set to `map`
2. Add displays manually:
   - Add → By topic → /map → Map
   - Add → By topic → /entropy_map → Map
   - Add → By topic → /scan → LaserScan

---

## 📁 File Structure

```
slam_uncertainty_ws/
├── src/uncertainty_slam/
│   ├── uncertainty_slam/
│   │   ├── synthetic_robot.py          # Virtual robot & environment
│   │   ├── uncertainty_node.py         # Entropy computation
│   │   ├── results_generator.py        # Auto visualization
│   │   ├── active_explorer.py          # Entropy-driven exploration
│   │   └── ...
│   ├── launch/
│   │   └── complete_system.launch.py   # Main launch file
│   ├── config/
│   │   ├── uncertainty_slam.rviz       # RViz configuration
│   │   └── mapper_params_*.yaml        # SLAM parameters
│   └── setup.py
├── results/visualizations/             # Generated outputs
├── RUN_COMPLETE_SYSTEM.sh             # Quick launch script
└── README.md                           # This file
```

---

## 📊 Expected Results

### Entropy Behavior:

- **Start**: High entropy (unknown map)
- **During**: Decreasing entropy (map being built)
- **End**:
  - Low entropy in well-scanned open areas
  - High entropy behind obstacles (occlusion)
  - Medium entropy at boundaries

### Typical Statistics:

- **Duration**: 10-15 minutes
- **Initial Entropy**: ~0.8-0.9 bits
- **Final Entropy**: ~0.2-0.4 bits
- **Entropy Reduction**: ~50-70%
- **Map Coverage**: >95% of accessible area

---

## 🔬 Research Applications

This system is designed for:

1. **Active SLAM** - Entropy-driven exploration strategies
2. **Uncertainty Analysis** - Quantifying map quality
3. **Frontier Detection** - High-entropy region identification
4. **Multi-Robot SLAM** - Uncertainty-aware task allocation
5. **Sensor Planning** - Optimal viewpoint selection

---

## 📝 Citation

If you use this system in research, please cite:

```
Rohan Upendra Patil (2025). Uncertainty-Aware SLAM with Real-Time
Entropy Quantification. GitHub repository.
```

---

## 🤝 Contributing

Issues and improvements welcome! Key areas:

- [ ] Dynamic obstacle handling
- [ ] Multi-floor environments
- [ ] 3D uncertainty quantification
- [ ] Integration with Nav2
- [ ] Machine learning-based exploration

---

## 📄 License

Apache-2.0

---

## 🎓 Technical Details

### Entropy Computation:

The system computes Shannon entropy for each cell using variance tracking:

1. **Variance Tracking**: Each map update increments per-cell statistics
2. **Entropy Mapping**: Variance → Entropy using binary distribution model
3. **Normalization**: Scaled to [0, 100] for visualization

**Formula**:
```
H(cell) = -Σ p(x) log₂(p(x))

where p(x) is derived from cell occupancy variance
```

### Robot Dynamics:

- **Max Linear Velocity**: 0.5 m/s
- **Max Angular Velocity**: 1.2 rad/s
- **Acceleration**: 0.6 m/s²
- **Angular Acceleration**: 1.0 rad/s²

### Virtual Environment:

- **Size**: 10m × 10m
- **Obstacles**: 5 boxes (4 corners + 1 center)
- **Wall Thickness**: Infinite (ray-casting boundaries)
- **Laser Range**: 10m, 360°, ~628 rays

---

**Ready to run!** Execute `./RUN_COMPLETE_SYSTEM.sh` to start. 🚀
# Slam
