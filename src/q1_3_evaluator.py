"""Offline-only final geometry and local holdout evaluator for Q1(3)."""
from __future__ import annotations
from math import pi
import numpy as np
from src.q1_3_adjustment import pair_angle

def evaluate_regular_nonagon(world):
    center=world[0];radii=[float(np.linalg.norm(world[i]-center)) for i in range(1,10)]
    phases=sorted(float(np.arctan2(*(world[i]-center)[::-1])) for i in range(1,10))
    gaps=[(phases[(i+1)%9]-phases[i])%(2*pi) for i in range(9)]; target=2*pi/9
    ideals={i:100*np.array((np.cos(target*(i-1)),np.sin(target*(i-1)))) for i in range(1,10)}
    return {"max_radius_error_m":max(abs(v-100) for v in radii),"max_successive_central_angle_error_rad":max(abs(v-target) for v in gaps),"max_target_position_error_m":max(float(np.linalg.norm(world[i]-ideals[i])) for i in range(1,10)),"radii_m":radii,"central_gaps_rad":gaps}

def holdout_report(world,receiver,spec,threshold=1e-6):
    residuals=[pair_angle(world[receiver],world,pair)-target for pair,target in zip(spec["holdout_pairs"],spec["holdout_angles"])]
    maximum=max(map(abs,residuals),default=0.)
    return {"pairs":[list(x) for x in spec["holdout_pairs"]],"residuals_rad":residuals,"threshold_rad":threshold,"max_abs_residual_rad":maximum,"status":"PASS" if maximum<=threshold else "REJECTED"}
