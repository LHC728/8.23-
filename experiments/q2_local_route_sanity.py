"""Q2 优化参考组路线的严格本机小范围验证。

该脚本是路线级 sanity check，而非正式批量仿真。在线控制函数只接收
本机试探观测回调、预装目标夹角与算法参数；坐标、参考机位置和离线
评价指标都保留在仿真环境中，不传入控制器。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from itertools import combinations
from math import cos, pi, sin
from pathlib import Path
from typing import Callable

import numpy as np

from experiments.q2_anchor_route_audit import FOUR_PAIR_INDICES, evaluate_four_reference_set, triangular_lattice
from src.q1_1_geometry import angle_signature, raw_angle


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "q2_design" / "q2_local_route_sanity.json"
REFERENCE_IDS = (3, 4, 11, 15)


@dataclass
class LocalRun:
    final_point: np.ndarray
    iterations: int
    final_residual_inf: float
    converged: bool
    residual_history: list[float]


def _residual(observed: np.ndarray, target: np.ndarray) -> np.ndarray:
    return observed - target


def receiver_angle_vector(point: np.ndarray, anchor_points: np.ndarray) -> np.ndarray:
    if len(anchor_points) == 3:
        return angle_signature(point, anchor_points)
    if len(anchor_points) == 4:
        return np.array(
            [raw_angle(point, anchor_points[left], anchor_points[right]) for left, right in FOUR_PAIR_INDICES]
        )
    raise ValueError("local angle controller supports exactly three or four labelled transmitters")


def local_probe_controller_action(
    observe_offset: Callable[[np.ndarray], np.ndarray],
    target_angles: np.ndarray,
    *,
    probe: float,
    gain: float,
    damping: float,
    max_step: float,
) -> tuple[np.ndarray, float]:
    """只用本机夹角试探，返回本机执行坐标中的一步动作。"""
    origin = np.zeros(2)
    observed = observe_offset(origin)
    residual = _residual(observed, target_angles)
    jacobian = np.empty((len(target_angles), 2), dtype=float)
    for axis in range(2):
        offset = np.zeros(2)
        offset[axis] = probe
        jacobian[:, axis] = (observe_offset(offset) - observe_offset(-offset)) / (2.0 * probe)

    normal = jacobian.T @ jacobian + damping * np.eye(2)
    action = -gain * np.linalg.solve(normal, jacobian.T @ residual)
    norm = float(np.linalg.norm(action))
    if norm > max_step:
        action *= max_step / norm

    base_norm = float(np.linalg.norm(residual))
    for factor in (1.0, 0.5, 0.25, 0.125, 0.0625, 0.0):
        proposal = factor * action
        proposal_norm = float(np.linalg.norm(_residual(observe_offset(proposal), target_angles)))
        if proposal_norm < base_norm or factor == 0.0:
            return proposal, proposal_norm
    raise RuntimeError("unreachable backtracking state")


def run_local_receiver(
    initial_point: np.ndarray,
    anchor_points: np.ndarray,
    target_angles: np.ndarray,
    local_rotation: np.ndarray,
    *,
    active_indices: tuple[int, ...] | None = None,
    probe: float = 2e-4,
    gain: float = 0.9,
    damping: float = 1e-7,
    max_step: float = 0.25,
    max_iterations: int = 50,
    residual_tol: float = 2e-10,
) -> LocalRun:
    point = initial_point.copy()
    history: list[float] = []
    indices = active_indices if active_indices is not None else tuple(range(len(target_angles)))
    if len(target_angles) != len(indices):
        raise ValueError("target_angles must contain exactly the active observation components")
    for iteration in range(max_iterations + 1):
        observed = receiver_angle_vector(point, anchor_points)[list(indices)]
        residual_inf = float(np.max(np.abs(_residual(observed, target_angles))))
        history.append(residual_inf)
        if residual_inf <= residual_tol:
            return LocalRun(point, iteration, residual_inf, True, history)
        if iteration == max_iterations:
            break

        # 环境闭包模拟“本机试探后返回”：控制器只看到 offset -> angles。
        def observe_offset(local_offset: np.ndarray) -> np.ndarray:
            return receiver_angle_vector(point + local_rotation @ local_offset, anchor_points)[list(indices)]

        local_action, _ = local_probe_controller_action(
            observe_offset,
            target_angles,
            probe=probe,
            gain=gain,
            damping=damping,
            max_step=max_step,
        )
        point = point + local_rotation @ local_action
    return LocalRun(point, max_iterations, history[-1], False, history)


def selected_reference_map(lattice: dict[int, np.ndarray]) -> dict[int, dict[str, object]]:
    audit = evaluate_four_reference_set(REFERENCE_IDS, lattice)
    if not audit["feasible"] or audit["global_unique_receiver_count"] != 11:
        raise RuntimeError("selected four-reference set no longer passes the finite geometry audit")
    return {
        int(item["receiver"]): {
            "anchor_ids": REFERENCE_IDS,
            "active_indices": tuple(int(index) for index in item["best_pair"]["constraint_indices"]),
            "holdout_indices": tuple(
                int(index)
                for index in item["active_constraint_indices"]
                if int(index) not in item["best_pair"]["constraint_indices"]
            ),
            "best_pair": item["best_pair"],
        }
        for item in audit["receivers"]
    }


def nearest_neighbor_edges(lattice: dict[int, np.ndarray], tol: float = 1e-9) -> list[tuple[int, int]]:
    edges: list[tuple[int, int]] = []
    for left, right in combinations(sorted(lattice), 2):
        if abs(float(np.linalg.norm(lattice[left] - lattice[right])) - 1.0) <= tol:
            edges.append((left, right))
    return edges


def line_groups(lattice: dict[int, np.ndarray]) -> list[list[int]]:
    """枚举三族格点方向上的全部最大直线（至少含两点）。"""
    directions = (
        np.array([0.0, 1.0]),
        np.array([-np.sqrt(3.0) / 2.0, -0.5]),
        np.array([-np.sqrt(3.0) / 2.0, 0.5]),
    )
    groups: set[tuple[int, ...]] = set()
    for direction in directions:
        normal = np.array([-direction[1], direction[0]])
        buckets: dict[int, list[int]] = {}
        for index, point in lattice.items():
            key = int(round(float(np.dot(normal, point)) * 10**8))
            buckets.setdefault(key, []).append(index)
        for members in buckets.values():
            if len(members) >= 2:
                members.sort(key=lambda index: float(np.dot(direction, lattice[index])))
                groups.add(tuple(members))
    return [list(group) for group in sorted(groups)]


def formation_metrics(points: dict[int, np.ndarray], ideal: dict[int, np.ndarray]) -> dict[str, float | int]:
    edges = nearest_neighbor_edges(ideal)
    lengths = np.array([np.linalg.norm(points[left] - points[right]) for left, right in edges])
    maximum_collinearity = 0.0
    for group in line_groups(ideal):
        matrix = np.vstack([points[index] for index in group])
        centered = matrix - np.mean(matrix, axis=0)
        _, _, right_vectors = np.linalg.svd(centered, full_matrices=False)
        normal = right_vectors[-1]
        maximum_collinearity = max(maximum_collinearity, float(np.max(np.abs(centered @ normal))))
    return {
        "nearest_neighbor_edge_count": len(edges),
        "edge_mean": float(np.mean(lengths)),
        "edge_relative_std": float(np.std(lengths) / np.mean(lengths)),
        "edge_max_abs_error_from_d": float(np.max(np.abs(lengths - 1.0))),
        "maximum_line_distance": maximum_collinearity,
    }


def local_basin_grid_check(lattice: dict[int, np.ndarray], reference_map: dict[int, dict[str, object]]) -> dict[str, object]:
    radii = (0.02, 0.05, 0.10, 0.20, 0.30, 0.40)
    certified_radius = 0.20
    directions = tuple(2.0 * pi * step / 16.0 for step in range(16))
    cases: list[dict[str, object]] = []
    for radius in radii:
        for theta in directions:
            points = {index: point.copy() for index, point in lattice.items()}
            run_records: list[dict[str, object]] = []
            for receiver, specification in reference_map.items():
                anchor_ids = tuple(int(index) for index in specification["anchor_ids"])
                active_indices = tuple(int(index) for index in specification["active_indices"])
                holdout_indices = tuple(int(index) for index in specification["holdout_indices"])
                target = lattice[receiver]
                phase = theta + 0.173 * receiver
                initial = target + radius * np.array([cos(phase), sin(phase)])
                anchors = np.vstack([lattice[index] for index in anchor_ids])
                target_angles = receiver_angle_vector(target, anchors)[list(active_indices)]
                local_heading = 0.37 * receiver + 0.11 * theta
                local_rotation = np.array(
                    [[cos(local_heading), -sin(local_heading)], [sin(local_heading), cos(local_heading)]]
                )
                run = run_local_receiver(
                    initial,
                    anchors,
                    target_angles,
                    local_rotation,
                    active_indices=active_indices,
                )
                points[receiver] = run.final_point
                run_records.append(
                    {
                        "receiver": receiver,
                        "anchor_ids": list(anchor_ids),
                        "active_constraint_indices": list(active_indices),
                        "holdout_constraint_indices": list(holdout_indices),
                        "converged": run.converged,
                        "iterations": run.iterations,
                        "final_residual_inf": run.final_residual_inf,
                        "final_position_error": float(np.linalg.norm(run.final_point - target)),
                        "residual_monotone": bool(
                            all(next_value <= value + 1e-14 for value, next_value in zip(run.residual_history, run.residual_history[1:]))
                        ),
                    }
                )
            metrics = formation_metrics(points, lattice)
            passed = all(bool(item["converged"]) and float(item["final_position_error"]) < 2e-8 for item in run_records)
            cases.append(
                {
                    "radius_d": radius,
                    "direction_rad": theta,
                    "pass": bool(passed),
                    "max_iterations": max(int(item["iterations"]) for item in run_records),
                    "max_final_position_error": max(float(item["final_position_error"]) for item in run_records),
                    "all_residual_histories_monotone": all(bool(item["residual_monotone"]) for item in run_records),
                    "formation_metrics": metrics,
                    "receivers": run_records,
                }
            )
    certified_cases = [case for case in cases if float(case["radius_d"]) <= certified_radius]
    stress_cases = [case for case in cases if float(case["radius_d"]) > certified_radius]
    return {
        "status": "PASS" if all(bool(case["pass"]) for case in certified_cases) else "FAIL",
        "certified_radius_d": certified_radius,
        "certified_case_count": len(certified_cases),
        "certified_all_pass": all(bool(case["pass"]) for case in certified_cases),
        "certified_worst_final_position_error": max(
            float(case["max_final_position_error"]) for case in certified_cases
        ),
        "certified_worst_iterations": max(int(case["max_iterations"]) for case in certified_cases),
        "stress_case_count": len(stress_cases),
        "stress_failure_count": sum(int(not bool(case["pass"])) for case in stress_cases),
        "stress_interpretation": "超过认证半径的探索性失败被保留，用于界定局部适用域；不用于声称全局收敛。",
        "case_count": len(cases),
        "receiver_runs": len(cases) * len(reference_map),
        "radii_d": list(radii),
        "directions_per_radius": len(directions),
        "worst_final_position_error": max(float(case["max_final_position_error"]) for case in cases),
        "worst_iterations": max(int(case["max_iterations"]) for case in cases),
        "all_residual_histories_monotone": all(bool(case["all_residual_histories_monotone"]) for case in cases),
        "cases": cases,
    }


def anchor_perturbation_check(lattice: dict[int, np.ndarray], reference_map: dict[int, dict[str, object]]) -> dict[str, object]:
    """离线量化“可信参考机并非完全准确”时的后果。"""
    epsilons = (0.001, 0.01, 0.05)
    patterns = 12
    cases: list[dict[str, object]] = []
    for epsilon in epsilons:
        for pattern in range(patterns):
            actual = {index: point.copy() for index, point in lattice.items()}
            for reference in REFERENCE_IDS:
                phase = 0.61 * reference + 2.0 * pi * pattern / patterns
                actual[reference] = lattice[reference] + epsilon * np.array([cos(phase), sin(phase)])
            receiver_records: list[dict[str, object]] = []
            for receiver, specification in reference_map.items():
                anchor_ids = tuple(int(index) for index in specification["anchor_ids"])
                active_indices = tuple(int(index) for index in specification["active_indices"])
                holdout_indices = tuple(int(index) for index in specification["holdout_indices"])
                ideal_target = lattice[receiver]
                ideal_anchors = np.vstack([lattice[index] for index in anchor_ids])
                actual_anchors = np.vstack([actual[index] for index in anchor_ids])
                target_angles = receiver_angle_vector(ideal_target, ideal_anchors)[list(active_indices)]
                local_heading = 0.29 * receiver
                local_rotation = np.array(
                    [[cos(local_heading), -sin(local_heading)], [sin(local_heading), cos(local_heading)]]
                )
                run = run_local_receiver(
                    ideal_target,
                    actual_anchors,
                    target_angles,
                    local_rotation,
                    active_indices=active_indices,
                )
                actual[receiver] = run.final_point
                actual_signature = receiver_angle_vector(run.final_point, actual_anchors)
                ideal_signature = receiver_angle_vector(ideal_target, ideal_anchors)
                holdout_residual = (
                    float(np.max(np.abs(actual_signature[list(holdout_indices)] - ideal_signature[list(holdout_indices)])))
                    if holdout_indices
                    else 0.0
                )
                receiver_records.append(
                    {
                        "receiver": receiver,
                        "converged": run.converged,
                        "position_bias": float(np.linalg.norm(run.final_point - ideal_target)),
                        "final_residual_inf": run.final_residual_inf,
                        "holdout_residual_inf": holdout_residual,
                    }
                )
            metrics = formation_metrics(actual, lattice)
            cases.append(
                {
                    "anchor_perturbation_norm_d": epsilon,
                    "pattern": pattern,
                    "all_receivers_converged": all(bool(item["converged"]) for item in receiver_records),
                    "max_receiver_position_bias_d": max(float(item["position_bias"]) for item in receiver_records),
                    "max_holdout_residual_rad": max(float(item["holdout_residual_inf"]) for item in receiver_records),
                    "formation_metrics": metrics,
                    "receivers": receiver_records,
                }
            )
    summaries: list[dict[str, object]] = []
    for epsilon in epsilons:
        subset = [case for case in cases if float(case["anchor_perturbation_norm_d"]) == epsilon]
        summaries.append(
            {
                "anchor_perturbation_norm_d": epsilon,
                "all_receivers_converged": all(bool(case["all_receivers_converged"]) for case in subset),
                "worst_receiver_position_bias_d": max(float(case["max_receiver_position_bias_d"]) for case in subset),
                "worst_holdout_residual_rad": max(float(case["max_holdout_residual_rad"]) for case in subset),
                "worst_edge_relative_std": max(float(case["formation_metrics"]["edge_relative_std"]) for case in subset),
                "worst_edge_max_abs_error_d": max(
                    float(case["formation_metrics"]["edge_max_abs_error_from_d"]) for case in subset
                ),
                "worst_maximum_line_distance_d": max(
                    float(case["formation_metrics"]["maximum_line_distance"]) for case in subset
                ),
            }
        )
    return {
        "status": "PASS" if all(bool(item["all_receivers_converged"]) for item in summaries) else "FAIL",
        "interpretation": "该检验不把参考机偏差回灌控制器；它只量化可信参考假设被轻微破坏后的输出偏差。",
        "summaries": summaries,
        "cases": cases,
    }


def run_sanity() -> dict[str, object]:
    lattice = triangular_lattice()
    reference_map = selected_reference_map(lattice)
    basin = local_basin_grid_check(lattice, reference_map)
    perturbation = anchor_perturbation_check(lattice, reference_map)
    status = "PASS" if basin["status"] == "PASS" and perturbation["status"] == "PASS" else "FAIL"
    return {
        "gate": "Q2_TRUSTED_REFERENCE_LOCAL_SANITY",
        "status": status,
        "scope": "目标邻域确定性小网格与参考机偏差情景；不是任意初态全局收敛证明。",
        "reference_ids": list(REFERENCE_IDS),
        "receiver_reference_map": {
            str(index): {
                "anchor_ids": list(specification["anchor_ids"]),
                "active_constraint_indices": list(specification["active_indices"]),
                "holdout_constraint_indices": list(specification["holdout_indices"]),
                "best_pair": specification["best_pair"],
            }
            for index, specification in reference_map.items()
        },
        "controller_information_boundary": {
            "online_inputs": ["receiver-local probe observations", "preloaded target angles", "local action parameters"],
            "forbidden_online_inputs": ["global coordinates", "distances", "other receivers' angles", "offline evaluator outputs"],
            "truth_usage": "coordinates and anchor perturbations exist only inside the simulation plant and offline evaluator",
        },
        "local_basin_grid_check": basin,
        "anchor_perturbation_check": perturbation,
    }


if __name__ == "__main__":
    result = run_sanity()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": result["status"],
                "reference_ids": result["reference_ids"],
                "local_cases": result["local_basin_grid_check"]["case_count"],
                "receiver_runs": result["local_basin_grid_check"]["receiver_runs"],
                "certified_radius_d": result["local_basin_grid_check"]["certified_radius_d"],
                "certified_worst_position_error": result["local_basin_grid_check"][
                    "certified_worst_final_position_error"
                ],
                "stress_failure_count": result["local_basin_grid_check"]["stress_failure_count"],
                "anchor_perturbation_summary": result["anchor_perturbation_check"]["summaries"],
                "output": str(OUT),
            },
            ensure_ascii=False,
        )
    )
    raise SystemExit(0 if result["status"] == "PASS" else 1)
