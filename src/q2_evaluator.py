"""Q2 离线独立几何评估器；不能被在线控制器导入。"""
from __future__ import annotations
from itertools import combinations
import numpy as np
from src.q2_geometry import target_lattice

def nearest_neighbor_edges() -> list[tuple[int,int]]:
    ideal=target_lattice(); return [(i,j) for i,j in combinations(ideal,2) if abs(float(np.linalg.norm(ideal[i]-ideal[j]))-1)<1e-9]

def line_groups() -> list[list[int]]:
    ideal=target_lattice(); directions=(np.array([0.,1.]),np.array([-np.sqrt(3)/2,-.5]),np.array([-np.sqrt(3)/2,.5])); groups=set()
    for direction in directions:
        normal=np.array([-direction[1],direction[0]]); buckets={}
        for key,point in ideal.items(): buckets.setdefault(int(round(float(normal@point)*1e8)),[]).append(key)
        groups.update(tuple(sorted(v,key=lambda i:float(direction@ideal[i]))) for v in buckets.values() if len(v)>=2)
    return [list(group) for group in sorted(groups)]

def evaluate_formation(points: dict[int,np.ndarray], d_star: float=1.) -> dict[str,float|int]:
    edges=nearest_neighbor_edges(); lengths=np.array([np.linalg.norm(points[i]-points[j]) for i,j in edges]); maximum=0.
    for group in line_groups():
        matrix=np.vstack([points[i] for i in group]); centered=matrix-matrix.mean(0); normal=np.linalg.svd(centered,full_matrices=False)[2][-1]; maximum=max(maximum,float(np.max(np.abs(centered@normal))))
    return {"nearest_neighbor_edge_count":len(edges),"line_group_count":len(line_groups()),"edge_max_abs_error_from_d":float(np.max(np.abs(lengths-d_star))),"edge_relative_std":float(np.std(lengths)/np.mean(lengths)),"maximum_line_distance":maximum}
