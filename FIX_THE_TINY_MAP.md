# 🔧 FIX THE TINY MAP ISSUE

## The Problem

Your map shows only **21×21 cells (2.1m×2.1m)** instead of **200×200 cells (20m×20m)**.

This means **the old code is still running** - the package wasn't rebuilt after my changes!

## The Solution

### Step 1: STOP the current system

```bash
# Press Ctrl+C in the terminal where you launched it
```

### Step 2: CLEAN BUILD (Fresh start)

```bash
cd ~/slam_uncertainty_ws

# Source ROS
source /opt/ros/humble/setup.bash

# Clean build (removes old compiled files)
rm -rf build/ install/ log/

# Build fresh
colcon build --packages-select uncertainty_slam

# Source the new build
source install/setup.bash
```

### Step 3: TEST the environment first

Before launching the full system, let's verify the environment is correct:

```bash
cd ~/slam_uncertainty_ws
python3 test_environment.py
```

**Expected output:**
```
Environment size: 20.0m × 20.0m
Number of obstacles: 19

LASER SCAN TEST FROM ORIGIN (0, 0)
East (+X)      :  10.00m (expected ~10.0m to walls)
North (+Y)     :  10.00m (expected ~10.0m to walls)
West (-X)      :  10.00m (expected ~10.0m to walls)
South (-Y)     :  10.00m (expected ~10.0m to walls)
```

If you see distances around **1-2m instead of 10m**, the old environment is still being used!

### Step 4: Launch the system

```bash
ros2 launch uncertainty_slam complete_system.launch.py
```

## What You Should See

### In RViz (after fix):

- **Map size:** 200 width × 200 height at 0.1 resolution = **20m×20m**
- **Immediate visibility:** Map appears within 1-2 seconds
- **Laser coverage:** Full 360° scan rays visible (not just a small arc)
- **Map content:** Large gray area with walls at the edges

### In terminal output:

```
ENVIRONMENT: 20m×20m with 4 Rooms + Wide Corridors
UPGRADED SENSOR FOR CLEAR MAPPING:
  - Laser FOV: 360° - FULL COVERAGE
  - Max Range: 10.0m
```

## Still Having Issues?

### Issue: Python test shows old environment (distances ~1-2m)

**This means the source code didn't update.** Try:

```bash
# Check the actual source file
cat src/uncertainty_slam/uncertainty_slam/synthetic_robot.py | grep "def __init__(self, width="

# Should show:
# def __init__(self, width=20.0, height=20.0):
```

If it shows `width=10.0`, the file wasn't saved!

### Issue: Map is still tiny after rebuild

This could mean:

1. **SLAM Toolbox config issue**
   
   Check if the YAML file was updated:
   ```bash
   cat src/uncertainty_slam/config/mapper_params_online_async.yaml | grep "resolution:"
   
   # Should show:
   # resolution: 0.1
   ```

2. **ROS cache issue**
   
   Clear everything:
   ```bash
   cd ~/slam_uncertainty_ws
   rm -rf build/ install/ log/
   source /opt/ros/humble/setup.bash
   colcon build --packages-select uncertainty_slam --symlink-install
   source install/setup.bash
   ```

### Issue: "No module named 'uncertainty_slam'"

You forgot to source the workspace:
```bash
cd ~/slam_uncertainty_ws
source install/setup.bash
```

## Quick Verification Checklist

After building, verify these files:

```bash
# 1. Check environment size in source
grep "width=20.0, height=20.0" src/uncertainty_slam/uncertainty_slam/synthetic_robot.py
# Should return a match

# 2. Check SLAM resolution
grep "resolution: 0.1" src/uncertainty_slam/config/mapper_params_online_async.yaml  
# Should return a match

# 3. Check laser FOV
grep "self.angle_min = -3.14159" src/uncertainty_slam/uncertainty_slam/synthetic_robot.py
# Should return a match (360° laser)

# 4. Check laser range
grep "self.range_max = 10.0" src/uncertainty_slam/uncertainty_slam/synthetic_robot.py
# Should return a match (10m range)
```

## Expected Behavior After Fix

| Metric | Before (Wrong) | After (Correct) |
|--------|----------------|-----------------|
| **Map width** | 21 cells | **200 cells** |
| **Map height** | 21 cells | **200 cells** |  
| **Map size** | 2.1m×2.1m | **20m×20m** |
| **Resolution** | 0.1m | **0.1m** (same) |
| **Laser distances** | ~1-2m | **~10m to walls** |
| **Laser FOV** | 240° | **360°** |

## Debug Command

If still not working, run this to see what the robot is actually publishing:

```bash
# Check scan data
ros2 topic echo /scan --once

# Look for:
# angle_min: -3.14159 (should be -π for 360°)
# angle_max: 3.14159 (should be +π for 360°)  
# range_max: 10.0 (should be 10m)
# ranges: [should have ~628 values, not ~418]
```

---

## TL;DR Quick Fix

```bash
cd ~/slam_uncertainty_ws
rm -rf build/ install/ log/
source /opt/ros/humble/setup.bash
colcon build --packages-select uncertainty_slam
source install/setup.bash
ros2 launch uncertainty_slam complete_system.launch.py
```

**Map should now be 20m×20m (200×200 cells) and clearly visible!**

If it's still tiny, run `python3 test_environment.py` and send me the output.

