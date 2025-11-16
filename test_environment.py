#!/usr/bin/env python3
"""
Quick test to verify environment is created correctly
"""

import sys
sys.path.insert(0, '/home/rohan/slam_uncertainty_ws/src/uncertainty_slam')

from uncertainty_slam.synthetic_robot import VirtualEnvironment
import math

# Create environment
env = VirtualEnvironment()

print("=" * 60)
print("ENVIRONMENT DIAGNOSTICS")
print("=" * 60)
print(f"Environment size: {env.width}m × {env.height}m")
print(f"Number of obstacles: {len(env.obstacles)}")
print(f"Expected: 20.0m × 20.0m with ~20+ obstacles")
print()

# Test raycasting from origin
print("=" * 60)
print("LASER SCAN TEST FROM ORIGIN (0, 0)")
print("=" * 60)

test_angles = [
    (0, "East (+X)"),
    (math.pi/2, "North (+Y)"),
    (math.pi, "West (-X)"),
    (-math.pi/2, "South (-Y)"),
]

for angle, direction in test_angles:
    dist = env.raycast(0, 0, angle, max_range=10.0)
    print(f"{direction:15s}: {dist:6.2f}m (expected ~10.0m to walls)")

print()
print("=" * 60)
print("ANALYSIS")
print("=" * 60)

if env.width == 20.0 and env.height == 20.0:
    print("✓ Environment size is correct (20m×20m)")
else:
    print(f"✗ ERROR: Environment size is {env.width}×{env.height}, should be 20.0×20.0")

if len(env.obstacles) > 15:
    print(f"✓ Environment has {len(env.obstacles)} obstacles (good)")
else:
    print(f"✗ WARNING: Only {len(env.obstacles)} obstacles (expected 20+)")

# Check first few obstacles
print()
print("First 5 obstacles:")
for i, obs in enumerate(env.obstacles[:5]):
    if obs['type'] == 'wall':
        print(f"  {i+1}. Wall from ({obs['x1']:.1f}, {obs['y1']:.1f}) to ({obs['x2']:.1f}, {obs['y2']:.1f})")
    elif obs['type'] == 'box':
        print(f"  {i+1}. Box at ({obs['cx']:.1f}, {obs['cy']:.1f}) size {obs['w']:.1f}×{obs['h']:.1f}")

print()
print("=" * 60)
print("If distances are NOT ~10m, the environment has a problem!")
print("If distances ARE ~10m, the issue is with SLAM Toolbox config")
print("=" * 60)

