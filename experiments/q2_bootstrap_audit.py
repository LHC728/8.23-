"""Q2 两可信种子到四参考机的严格本机交替建锚审计。"""

from __future__ import annotations

import json
from itertools import product
from math import cos, pi, sin
from pathlib import Path

import numpy as np

from experiments.q2_anchor_route_audit import PAIR_CHOICES, _best_pair, triangular_lattice
from experiments.q2_local_route_sanity import run_local_receiver
from src.q1_1_geometry import ANGLE_NAMES, ANGLE_PAIRS, angle_jacobian, angle_signature, complete_candidates


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "q2_design" / "q2_bootstrap_audit.json"
SEED_IDS = (11, 15)
BOOTSTRAP_ORDER = (4, 3)


def transmitter_gradient(
    receiver: np.ndarray,
    first: np.ndarray,
    second: np.ndarray,
    *,
    with_respect_to: str,
    eps: float = 1e-12,
) -> np.ndarray:
    """无符号夹角对第一或第二发射机坐标的解析梯度。"""
    u = first - receiver
    v = second - receiver
    cross = float(u[0] * v[1] - u[1] * v[0])
    dot = float(np.dot(u, v))
    denominator = cross * cross + dot * dot
    if abs(cross) <= eps or denominator <= eps:
        raise ValueError("transmitter gradient is singular at 0/pi")
    if with_respect_to == "first":
        gradient_cross = np.array([v[1], -v[0]])
        gradient_dot = v
    elif with_respect_to == "second":
        gradient_cross = np.array([-u[1], u[0]])
        gradient_dot = u
    else:
        raise ValueError("with_respect_to must be 'first' or 'second'")
    return np.sign(cross) * (dot * gradient_cross - cross * gradient_dot) / denominator


def other_transmitter_jacobian(
    receiver: np.ndarray,
    transmitters: np.ndarray,
    names: tuple[str, str],
    moving_index: int = 2,
) -> np.ndarray:
    rows: list[np.ndarray] = []
    for name in names:
        left, right = ANGLE_PAIRS[name]
        if moving_index == left:
            rows.append(
                transmitter_gradient(receiver, transmitters[left], transmitters[right], with_respect_to="first")
            )
        elif moving_index == right:
            rows.append(
                transmitter_gradient(receiver, transmitters[left], transmitters[right], with_respect_to="second")
            )
        else:
            rows.append(np.zeros(2))
    return np.vstack(rows)


def finite_difference_other_jacobian(
    receiver: np.ndarray,
    transmitters: np.ndarray,
    names: tuple[str, str],
    moving_index: int = 2,
    step: float = 1e-6,
) -> np.ndarray:
    matrix = np.empty((2, 2), dtype=float)
    name_indices = [ANGLE_NAMES.index(name) for name in names]
    for axis in range(2):
        plus = transmitters.copy()
        minus = transmitters.copy()
        plus[moving_index, axis] += step
        minus[moving_index, axis] -= step
        matrix[:, axis] = (
            angle_signature(receiver, plus)[name_indices] - angle_signature(receiver, minus)[name_indices]
        ) / (2.0 * step)
    return matrix


def bootstrap_linearization(lattice: dict[int, np.ndarray]) -> dict[str, object]:
    records: dict[int, dict[str, object]] = {}
    response_matrices: dict[int, np.ndarray] = {}
    first_receiver, second_receiver = BOOTSTRAP_ORDER
    for receiver, other in ((first_receiver, second_receiver), (second_receiver, first_receiver)):
        transmitters = np.vstack([lattice[SEED_IDS[0]], lattice[SEED_IDS[1]], lattice[other]])
        best = _best_pair(lattice[receiver], transmitters)
        names = tuple(str(name) for name in best["names"])
        self_jacobian = angle_jacobian(lattice[receiver], transmitters, names)
        other_jacobian = other_transmitter_jacobian(lattice[receiver], transmitters, names)
        finite_difference = finite_difference_other_jacobian(lattice[receiver], transmitters, names)
        response = -np.linalg.solve(self_jacobian, other_jacobian)
        response_matrices[receiver] = response
        records[receiver] = {
            "receiver": receiver,
            "other_bootstrap_node": other,
            "transmitter_ids": [SEED_IDS[0], SEED_IDS[1], other],
            "primary_angle_names": list(names),
            "target_angles_rad": angle_signature(lattice[receiver], transmitters).tolist(),
            "self_jacobian": self_jacobian.tolist(),
            "other_jacobian_analytic": other_jacobian.tolist(),
            "other_jacobian_finite_difference": finite_difference.tolist(),
            "analytic_fd_max_abs_difference": float(np.max(np.abs(other_jacobian - finite_difference))),
            "self_sigma_min": float(np.linalg.svd(self_jacobian, compute_uv=False)[-1]),
            "self_condition_number": float(np.linalg.cond(self_jacobian)),
            "best_response_derivative": response.tolist(),
        }

    first = response_matrices[first_receiver]
    second = response_matrices[second_receiver]
    period_reduced = second @ first
    # 状态顺序 [x_second, x_first]；先更新 first，再更新 second。
    period_full = np.block([[period_reduced, np.zeros((2, 2))], [first, np.zeros((2, 2))]])
    eigenvalues = np.linalg.eigvals(period_full)
    spectral_radius = float(np.max(np.abs(eigenvalues)))
    return {
        "records": {str(index): value for index, value in records.items()},
        "period_reduced_jacobian": period_reduced.tolist(),
        "period_full_jacobian_state_order_second_first": period_full.tolist(),
        "eigenvalues": [[float(value.real), float(value.imag)] for value in eigenvalues],
        "spectral_radius": spectral_radius,
        "status": "PASS"
        if spectral_radius < 1.0
        and max(float(item["analytic_fd_max_abs_difference"]) for item in records.values()) < 1e-8
        else "FAIL",
    }


def exact_local_best_response(
    receiver: int,
    other: int,
    other_position: np.ndarray,
    lattice: dict[int, np.ndarray],
) -> tuple[np.ndarray, dict[str, object]]:
    transmitters = np.vstack([lattice[SEED_IDS[0]], lattice[SEED_IDS[1]], other_position])
    ideal_transmitters = np.vstack([lattice[SEED_IDS[0]], lattice[SEED_IDS[1]], lattice[other]])
    target_angles = angle_signature(lattice[receiver], ideal_transmitters)
    report = complete_candidates(transmitters, target_angles, angle_tol=2e-8, geometry_tol=1e-10)
    roots = [item.point for item in report.candidates]
    if not roots:
        raise RuntimeError(f"no local best-response candidate for FY{receiver:02d}")
    selected = min(roots, key=lambda point: float(np.linalg.norm(point - lattice[receiver])))
    return selected, {
        "candidate_count": len(roots),
        "selected_distance_to_target": float(np.linalg.norm(selected - lattice[receiver])),
        "candidate_points": [point.tolist() for point in roots],
        "status": sorted(report.status),
    }


def exact_cycle_map(state: np.ndarray, lattice: dict[int, np.ndarray]) -> tuple[np.ndarray, dict[str, object]]:
    first_receiver, second_receiver = BOOTSTRAP_ORDER
    point_second = state[:2]
    new_first, audit_first = exact_local_best_response(first_receiver, second_receiver, point_second, lattice)
    new_second, audit_second = exact_local_best_response(second_receiver, first_receiver, new_first, lattice)
    return np.hstack([new_second, new_first]), {
        f"FY{first_receiver:02d}": audit_first,
        f"FY{second_receiver:02d}": audit_second,
    }


def exact_map_finite_difference(lattice: dict[int, np.ndarray], step: float = 1e-6) -> dict[str, object]:
    first_receiver, second_receiver = BOOTSTRAP_ORDER
    target_state = np.hstack([lattice[second_receiver], lattice[first_receiver]])
    matrix = np.empty((4, 4), dtype=float)
    for axis in range(4):
        delta = np.zeros(4)
        delta[axis] = step
        plus, _ = exact_cycle_map(target_state + delta, lattice)
        minus, _ = exact_cycle_map(target_state - delta, lattice)
        matrix[:, axis] = (plus - minus) / (2.0 * step)
    return {"jacobian": matrix.tolist()}


def exact_grid_check(lattice: dict[int, np.ndarray]) -> dict[str, object]:
    first_receiver, second_receiver = BOOTSTRAP_ORDER
    target = np.hstack([lattice[second_receiver], lattice[first_receiver]])
    radii = (0.01, 0.05, 0.10, 0.20, 0.30)
    phases = tuple(2.0 * pi * index / 12.0 for index in range(12))
    cases: list[dict[str, object]] = []
    for radius, phase_second, phase_first in product(radii, phases, phases):
        state = target.copy()
        state[:2] += radius * np.array([cos(phase_second), sin(phase_second)])
        state[2:] += radius * np.array([cos(phase_first), sin(phase_first)])
        converged = False
        audit: dict[str, object] = {}
        for iteration in range(25):
            state, audit = exact_cycle_map(state, lattice)
            if float(np.linalg.norm(state - target, ord=np.inf)) < 2e-8:
                converged = True
                break
        cases.append(
            {
                "radius_d": radius,
                "phase_second": phase_second,
                "phase_first": phase_first,
                "converged": converged,
                "iterations": iteration + 1,
                "final_error_inf": float(np.linalg.norm(state - target, ord=np.inf)),
                "last_candidate_audit": audit,
            }
        )
    return {
        "status": "PASS" if all(bool(case["converged"]) for case in cases) else "FAIL",
        "case_count": len(cases),
        "radii_d": list(radii),
        "worst_iterations": max(int(case["iterations"]) for case in cases),
        "worst_final_error_inf": max(float(case["final_error_inf"]) for case in cases),
        "cases": cases,
    }


def finite_probe_grid_check(lattice: dict[int, np.ndarray]) -> dict[str, object]:
    first_receiver, second_receiver = BOOTSTRAP_ORDER
    target = np.hstack([lattice[second_receiver], lattice[first_receiver]])
    radii = (0.02, 0.05, 0.10, 0.20)
    phases = tuple(2.0 * pi * index / 8.0 for index in range(8))
    cases: list[dict[str, object]] = []
    for radius, phase_second, phase_first in product(radii, phases, phases):
        point_second = lattice[second_receiver] + radius * np.array([cos(phase_second), sin(phase_second)])
        point_first = lattice[first_receiver] + radius * np.array([cos(phase_first), sin(phase_first)])
        cycle_history: list[float] = []
        for cycle in range(20):
            anchors_first = np.vstack([lattice[SEED_IDS[0]], lattice[SEED_IDS[1]], point_second])
            ideal_anchors_first = np.vstack(
                [lattice[SEED_IDS[0]], lattice[SEED_IDS[1]], lattice[second_receiver]]
            )
            heading_first = 0.37 * first_receiver
            rotation_first = np.array(
                [[cos(heading_first), -sin(heading_first)], [sin(heading_first), cos(heading_first)]]
            )
            run_first = run_local_receiver(
                point_first,
                anchors_first,
                angle_signature(lattice[first_receiver], ideal_anchors_first),
                rotation_first,
                max_iterations=30,
            )
            point_first = run_first.final_point

            anchors_second = np.vstack([lattice[SEED_IDS[0]], lattice[SEED_IDS[1]], point_first])
            ideal_anchors_second = np.vstack(
                [lattice[SEED_IDS[0]], lattice[SEED_IDS[1]], lattice[first_receiver]]
            )
            heading_second = 0.37 * second_receiver
            rotation_second = np.array(
                [[cos(heading_second), -sin(heading_second)], [sin(heading_second), cos(heading_second)]]
            )
            run_second = run_local_receiver(
                point_second,
                anchors_second,
                angle_signature(lattice[second_receiver], ideal_anchors_second),
                rotation_second,
                max_iterations=30,
            )
            point_second = run_second.final_point
            error = float(np.linalg.norm(np.hstack([point_second, point_first]) - target, ord=np.inf))
            cycle_history.append(error)
            if error < 2e-7:
                break
        cases.append(
            {
                "radius_d": radius,
                "phase_second": phase_second,
                "phase_first": phase_first,
                "converged": bool(cycle_history[-1] < 2e-7),
                "cycles": cycle + 1,
                "final_error_inf": cycle_history[-1],
                "cycle_error_history": cycle_history,
            }
        )
    return {
        "status": "PASS" if all(bool(case["converged"]) for case in cases) else "FAIL",
        "case_count": len(cases),
        "radii_d": list(radii),
        "worst_cycles": max(int(case["cycles"]) for case in cases),
        "worst_final_error_inf": max(float(case["final_error_inf"]) for case in cases),
        "cases": cases,
    }


def run_audit() -> dict[str, object]:
    lattice = triangular_lattice()
    linearization = bootstrap_linearization(lattice)
    exact_fd = exact_map_finite_difference(lattice)
    analytic_full = np.asarray(linearization["period_full_jacobian_state_order_second_first"], dtype=float)
    numeric_full = np.asarray(exact_fd["jacobian"], dtype=float)
    exact_fd["max_abs_difference_from_implicit_jacobian"] = float(np.max(np.abs(analytic_full - numeric_full)))
    exact_fd["status"] = "PASS" if exact_fd["max_abs_difference_from_implicit_jacobian"] < 2e-6 else "FAIL"
    exact_grid = exact_grid_check(lattice)
    finite_probe_grid = finite_probe_grid_check(lattice)
    status = "PASS" if all(
        item["status"] == "PASS" for item in (linearization, exact_fd, exact_grid, finite_probe_grid)
    ) else "FAIL"
    return {
        "gate": "Q2_TWO_SEED_BOOTSTRAP_AUDIT",
        "status": status,
        "scope": "两可信种子下的目标邻域、非退化、严格本机交替建锚；不主张任意初态全局收敛。",
        "seed_ids": list(SEED_IDS),
        "seed_distance_in_d": float(np.linalg.norm(lattice[SEED_IDS[0]] - lattice[SEED_IDS[1]])),
        "bootstrap_order": list(BOOTSTRAP_ORDER),
        "linearization": linearization,
        "exact_map_finite_difference": exact_fd,
        "exact_best_response_grid": exact_grid,
        "finite_probe_grid": finite_probe_grid,
        "information_boundary": {
            "online": "每个待建锚节点只使用自己测得的三发射机夹角、本机试探和预装目标夹角；两个种子与另一待建锚节点在其接收子轮仅发射。",
            "offline_only": "坐标、候选全集、周期 Jacobian、谱和最终误差。",
            "cross_receiver_angle_exchange": False,
        },
        "minimality": {
            "zero_or_one_trusted_seed": "不能消除纯夹角的共同尺度自由度。",
            "two_noncoincident_trusted_seeds": "已知种子基线提供米制尺度；再由本机交替建锚扩展为四参考组。",
        },
    }


if __name__ == "__main__":
    result = run_audit()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": result["status"],
                "seed_ids": result["seed_ids"],
                "seed_distance_in_d": result["seed_distance_in_d"],
                "spectral_radius": result["linearization"]["spectral_radius"],
                "exact_grid_cases": result["exact_best_response_grid"]["case_count"],
                "finite_probe_cases": result["finite_probe_grid"]["case_count"],
                "output": str(OUT),
            },
            ensure_ascii=False,
        )
    )
    raise SystemExit(0 if result["status"] == "PASS" else 1)
