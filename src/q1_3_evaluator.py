"""Offline Q1(3) outcome evaluator; never imported by an online controller."""
from __future__ import annotations
from math import pi
import numpy as np


def evaluate_regular_nonagon(points: dict[int, np.ndarray]) -> dict:
    center = points[0]
    radii = [float(np.linalg.norm(points[i] - center)) for i in range(1, 10)]
    phases = [float(np.arctan2(*(points[i] - center)[::-1])) for i in range(1, 10)]
    phases.sort()
    gaps = [(phases[(i+1) % 9] - phases[i]) % (2*pi) for i in range(9)]
    target = 2*pi/9
    target_points = {i: 100*np.array((np.cos(2*pi*(i-1)/9), np.sin(2*pi*(i-1)/9))) for i in range(1,10)}
    position_errors = [float(np.linalg.norm(points[i]-target_points[i])) for i in range(1,10)]
    return {"max_radius_error_m": max(abs(radius-100.0) for radius in radii), "max_successive_central_angle_error_rad": max(abs(gap-target) for gap in gaps), "max_target_position_error_m": max(position_errors), "radii_m": radii, "central_gaps_rad": gaps}
