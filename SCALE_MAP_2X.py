#!/usr/bin/env python3
"""
Quick script to scale all coordinates by 2x
Run this to see the scaled coordinates
"""

obstacles_old = [
    # VERTICAL DIVIDER 1
    {'type': 'wall', 'x1': -2.5, 'y1': 5.0, 'x2': -2.5, 'y2': 2.0},
    {'type': 'wall', 'x1': -2.5, 'y1': 0.5, 'x2': -2.5, 'y2': -5.0},
    # VERTICAL DIVIDER 2
    {'type': 'wall', 'x1': 2.5, 'y1': 5.0, 'x2': 2.5, 'y2': 2.0},
    {'type': 'wall', 'x1': 2.5, 'y1': 0.5, 'x2': 2.5, 'y2': -5.0},
    # HORIZONTAL DIVIDER
    {'type': 'wall', 'x1': -5.0, 'y1': 0.0, 'x2': -3.5, 'y2': 0.0},
    {'type': 'wall', 'x1': 3.5, 'y1': 0.0, 'x2': 5.0, 'y2': 0.0},
    # CORRIDOR WALLS
    {'type': 'wall', 'x1': -1.0, 'y1': 2.0, 'x2': -1.0, 'y2': 0.5},
    {'type': 'wall', 'x1': 1.0, 'y1': 2.0, 'x2': 1.0, 'y2': 0.5},
]

for obs in obstacles_old:
    if 'x1' in obs:
        print(f"{{'type': 'wall', 'x1': {obs['x1']*2}, 'y1': {obs['y1']*2}, 'x2': {obs['x2']*2}, 'y2': {obs['y2']*2}}},")
    elif 'cx' in obs:
        print(f"{{'type': 'box', 'cx': {obs['cx']*2}, 'cy': {obs['cy']*2}, 'w': {obs['w']*2}, 'h': {obs['h']*2}}},")
