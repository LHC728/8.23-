"""Q2 三参考机路线的有限几何审计。

本脚本只用于离线路线设计与验证，不是在线控制器。它枚举 15 个目标
槽位中的全部三参考机组合，复用 Q1(1) 已冻结的完整候选器，并检查：

1. 三参考机是否非共线；
2. 其余每个槽位的三项纯方位观测是否避开 0/pi；
3. 完整候选器是否找回目标槽位以及是否存在远端根；
4. 最优两项主约束的局部 Jacobian 是否满秩及其条件数；
5. 纯角观测对整体相似变换不变，因而不能自行恢复物理尺度。

结果写入 results/q2_design/q2_anchor_route_audit.json。
"""

from __future__ import annotations

import json
from itertools import combinations
from math import cos, pi, sin, sqrt
from pathlib import Path

import numpy as np

from src.q1_1_geometry import (
    ANGLE_NAMES,
    _circle_branches,
    analytic_angle_gradient,
    angle_jacobian,
    angle_signature,
    circle_intersections,
    complete_candidates,
    independent_multistart_checker,
    raw_angle,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "q2_design" / "q2_anchor_route_audit.json"
PAIR_CHOICES = tuple(combinations(ANGLE_NAMES, 2))
BOOTSTRAPPABLE_REFERENCE_IDS = (3, 4, 11, 15)
FOUR_PAIR_INDICES = tuple(combinations(range(4), 2))


def triangular_lattice() -> dict[int, np.ndarray]:
    """返回相邻间距 d=1 的 15 个锥形编队目标槽位。"""
    points: dict[int, np.ndarray] = {}
    for row in range(5):
        for offset in range(row + 1):
            index = 1 + row * (row + 1) // 2 + offset
            points[index] = np.array([-sqrt(3.0) * row / 2.0, offset - row / 2.0])
    return points


def _point_in(points: list[np.ndarray], target: np.ndarray, tol: float = 2e-7) -> bool:
    return any(float(np.linalg.norm(point - target)) <= tol for point in points)


def _same_point_sets(left: list[np.ndarray], right: list[np.ndarray], tol: float = 2e-5) -> bool:
    return len(left) == len(right) and all(_point_in(right, point, tol) for point in left)


def _best_pair(point: np.ndarray, anchors: np.ndarray) -> dict[str, object]:
    candidates: list[dict[str, object]] = []
    for names in PAIR_CHOICES:
        jacobian = angle_jacobian(point, anchors, names)
        singular_values = np.linalg.svd(jacobian, compute_uv=False)
        sigma_min = float(singular_values[-1])
        condition = float(singular_values[0] / sigma_min) if sigma_min > 0 else float("inf")
        candidates.append(
            {
                "names": list(names),
                "sigma_min": sigma_min,
                "sigma_max": float(singular_values[0]),
                "condition_number": condition,
                "det_abs": float(abs(np.linalg.det(jacobian))),
            }
        )
    return max(candidates, key=lambda item: (float(item["sigma_min"]), -float(item["condition_number"])))


def _four_signature(point: np.ndarray, anchors: np.ndarray) -> np.ndarray:
    return np.array([raw_angle(point, anchors[left], anchors[right]) for left, right in FOUR_PAIR_INDICES])


def _circle_equal(left: object, right: object, tol: float = 2e-8) -> bool:
    scale = max(1.0, float(left.radius), float(right.radius))
    return bool(
        np.linalg.norm(np.asarray(left.center) - np.asarray(right.center)) <= tol * scale
        and abs(float(left.radius) - float(right.radius)) <= tol * scale
    )


def _deduplicate_points(points: list[np.ndarray], tol: float = 2e-7) -> list[np.ndarray]:
    kept: list[np.ndarray] = []
    for point in points:
        if not _point_in(kept, point, tol):
            kept.append(np.asarray(point, dtype=float))
    return kept


def _complete_four_candidates(
    anchors: np.ndarray,
    observed: np.ndarray,
    *,
    angle_tol: float = 3e-8,
    geometry_tol: float = 1e-10,
    boundary_eps: float = 1e-7,
) -> dict[str, object]:
    """枚举四参考机六条角约束的全部有限交点。

    0/pi 约束只登记而不作为光滑主约束。其余每一条定夹角约束均为
    两个圆分支；任一有限孤立解必定出现在至少一对非重合圆的交点中。
    若同一个圆分支同时覆盖全部有效约束，则显式报告连续解族。
    """
    active = [
        index
        for index, value in enumerate(observed)
        if boundary_eps < float(value) < pi - boundary_eps
    ]
    circles: dict[int, list[object]] = {}
    flags: set[str] = set()
    for constraint in active:
        left, right = FOUR_PAIR_INDICES[constraint]
        branches, branch_flags = _circle_branches(
            anchors[left],
            anchors[right],
            float(observed[constraint]),
            f"{left}{right}",
            boundary_eps=boundary_eps,
        )
        circles[constraint] = branches
        flags.update(branch_flags)

    if len(active) < 2:
        return {
            "roots": [],
            "active_constraints": active,
            "boundary_constraints": [index for index in range(6) if index not in active],
            "continuous_solution_family": True,
            "coincident_circle_events": 0,
            "tangent_events": 0,
            "rejected_intersections": 0,
            "status": sorted(flags | {"insufficient_smooth_constraints"}),
        }

    continuous = False
    for constraint in active:
        for circle in circles[constraint]:
            if all(any(_circle_equal(circle, other) for other in circles[other_constraint]) for other_constraint in active):
                continuous = True
                break
        if continuous:
            break

    roots: list[np.ndarray] = []
    coincident_events = 0
    tangent_events = 0
    rejected = 0
    for left_constraint, right_constraint in combinations(active, 2):
        for left_circle in circles[left_constraint]:
            for right_circle in circles[right_constraint]:
                intersections, state = circle_intersections(left_circle, right_circle, tol=geometry_tol)
                if state == "coincident":
                    coincident_events += 1
                    continue
                if state == "tangent":
                    tangent_events += 1
                for point in intersections:
                    if min(float(np.linalg.norm(point - anchor)) for anchor in anchors) <= 5e-8:
                        rejected += 1
                        continue
                    residual = _four_signature(point, anchors) - observed
                    if max(abs(float(residual[index])) for index in active) <= angle_tol:
                        roots.append(point)
                    else:
                        rejected += 1

    roots = _deduplicate_points(roots)
    if continuous:
        flags.add("continuous_solution_family")
    if coincident_events:
        flags.add("coincident_constraint_circles")
    if not roots:
        flags.add("no_finite_candidate")
    return {
        "roots": roots,
        "active_constraints": active,
        "boundary_constraints": [index for index in range(6) if index not in active],
        "continuous_solution_family": continuous,
        "coincident_circle_events": coincident_events,
        "tangent_events": tangent_events,
        "rejected_intersections": rejected,
        "status": sorted(flags),
    }


def _best_four_pair(point: np.ndarray, anchors: np.ndarray, active: list[int]) -> dict[str, object] | None:
    candidates: list[dict[str, object]] = []
    for first, second in combinations(active, 2):
        first_pair = FOUR_PAIR_INDICES[first]
        second_pair = FOUR_PAIR_INDICES[second]
        jacobian = np.vstack(
            [
                analytic_angle_gradient(point, anchors[first_pair[0]], anchors[first_pair[1]]),
                analytic_angle_gradient(point, anchors[second_pair[0]], anchors[second_pair[1]]),
            ]
        )
        singular_values = np.linalg.svd(jacobian, compute_uv=False)
        sigma_min = float(singular_values[-1])
        condition = float(singular_values[0] / sigma_min) if sigma_min > 0 else float("inf")
        candidates.append(
            {
                "constraint_indices": [first, second],
                "anchor_pairs": [list(first_pair), list(second_pair)],
                "sigma_min": sigma_min,
                "sigma_max": float(singular_values[0]),
                "condition_number": condition,
                "det_abs": float(abs(np.linalg.det(jacobian))),
            }
        )
    if not candidates:
        return None
    return max(candidates, key=lambda item: (float(item["sigma_min"]), -float(item["condition_number"])))


def evaluate_triple(ids: tuple[int, int, int], lattice: dict[int, np.ndarray]) -> dict[str, object]:
    anchors = np.vstack([lattice[index] for index in ids])
    edge_1 = anchors[1] - anchors[0]
    edge_2 = anchors[2] - anchors[0]
    doubled_area = float(abs(edge_1[0] * edge_2[1] - edge_1[1] * edge_2[0]))
    followers: list[dict[str, object]] = []
    feasible = doubled_area > 1e-10

    for index, target in lattice.items():
        if index in ids:
            continue
        observed = angle_signature(target, anchors)
        angle_margin = float(np.min(np.minimum(observed, pi - observed)))
        boundary_free = bool(angle_margin > 1e-7)
        record: dict[str, object] = {
            "receiver": index,
            "target": target.tolist(),
            "observed_angles_rad": observed.tolist(),
            "angle_boundary_margin_rad": angle_margin,
            "boundary_free": boundary_free,
        }
        if not boundary_free:
            record.update(
                {
                    "target_recovered": False,
                    "candidate_count": 0,
                    "candidate_points": [],
                    "best_pair": None,
                    "wrong_root_separation": None,
                }
            )
            feasible = False
            followers.append(record)
            continue

        report = complete_candidates(anchors, observed, angle_tol=2e-8, geometry_tol=1e-10)
        roots = [candidate.point for candidate in report.candidates]
        recovered = _point_in(roots, target)
        wrong_distances = [float(np.linalg.norm(root - target)) for root in roots if np.linalg.norm(root - target) > 2e-7]
        best = _best_pair(target, anchors)
        full_rank = bool(float(best["sigma_min"]) > 1e-8)
        record.update(
            {
                "target_recovered": recovered,
                "candidate_count": len(roots),
                "candidate_points": [root.tolist() for root in roots],
                "candidate_status": sorted(report.status),
                "best_pair": best,
                "wrong_root_separation": min(wrong_distances) if wrong_distances else None,
            }
        )
        feasible = feasible and recovered and full_rank
        followers.append(record)

    valid_followers = [item for item in followers if item["best_pair"] is not None]
    unique_count = sum(int(item["candidate_count"] == 1) for item in valid_followers)
    worst_sigma = min((float(item["best_pair"]["sigma_min"]) for item in valid_followers), default=0.0)
    worst_condition = max((float(item["best_pair"]["condition_number"]) for item in valid_followers), default=float("inf"))
    min_margin = min((float(item["angle_boundary_margin_rad"]) for item in followers), default=0.0)
    wrong_separations = [float(item["wrong_root_separation"]) for item in valid_followers if item["wrong_root_separation"] is not None]

    return {
        "anchor_ids": list(ids),
        "anchor_points": anchors.tolist(),
        "anchor_doubled_area": doubled_area,
        "feasible": bool(feasible),
        "global_unique_follower_count": unique_count,
        "follower_count": len(followers),
        "worst_best_pair_sigma_min": worst_sigma,
        "worst_best_pair_condition_number": worst_condition,
        "minimum_angle_boundary_margin_rad": min_margin,
        "minimum_wrong_root_separation": min(wrong_separations) if wrong_separations else None,
        "followers": followers,
    }


def evaluate_four_reference_set(ids: tuple[int, int, int, int], lattice: dict[int, np.ndarray]) -> dict[str, object]:
    """四架参考机同时发射；接收机使用本机六角约束完成消歧。"""
    anchors = np.vstack([lattice[index] for index in ids])
    receivers: list[dict[str, object]] = []
    feasible = True
    for receiver in sorted(lattice):
        if receiver in ids:
            continue
        target = lattice[receiver]
        observed = _four_signature(target, anchors)
        report = _complete_four_candidates(anchors, observed)
        roots = list(report["roots"])
        active = list(report["active_constraints"])
        best_pair = _best_four_pair(target, anchors, active)
        recovered = _point_in(roots, target)
        wrong_distances = [float(np.linalg.norm(root - target)) for root in roots if np.linalg.norm(root - target) > 2e-7]
        active_margins = [min(float(observed[index]), pi - float(observed[index])) for index in active]
        record = {
            "receiver": receiver,
            "target": target.tolist(),
            "observed_angles_rad": observed.tolist(),
            "active_constraint_indices": active,
            "boundary_constraint_indices": report["boundary_constraints"],
            "active_angle_boundary_margin_rad": min(active_margins) if active_margins else 0.0,
            "candidate_count": len(roots),
            "candidate_points": [root.tolist() for root in roots],
            "target_recovered": recovered,
            "continuous_solution_family": bool(report["continuous_solution_family"]),
            "candidate_status": report["status"],
            "best_pair": best_pair,
            "wrong_root_separation": min(wrong_distances) if wrong_distances else None,
        }
        record_feasible = bool(
            recovered
            and len(roots) >= 1
            and not report["continuous_solution_family"]
            and best_pair is not None
            and float(best_pair["sigma_min"]) > 1e-8
        )
        feasible = feasible and record_feasible
        receivers.append(record)

    valid_records = [item for item in receivers if item["best_pair"] is not None]
    unique_count = sum(int(item["candidate_count"] == 1) for item in valid_records)
    return {
        "reference_ids": list(ids),
        "feasible": bool(feasible),
        "receiver_count": len(receivers),
        "global_unique_receiver_count": unique_count,
        "worst_selected_sigma_min": min((float(item["best_pair"]["sigma_min"]) for item in valid_records), default=0.0),
        "worst_selected_condition_number": max(
            (float(item["best_pair"]["condition_number"]) for item in valid_records), default=float("inf")
        ),
        "minimum_selected_angle_margin_rad": min(
            (float(item["active_angle_boundary_margin_rad"]) for item in valid_records), default=0.0
        ),
        "receivers": receivers,
    }


def _four_reference_ranking_key(item: dict[str, object]) -> tuple[float, ...]:
    return (
        float(bool(item["feasible"])),
        float(item["global_unique_receiver_count"]),
        float(item["worst_selected_sigma_min"]),
        -float(item["worst_selected_condition_number"]),
        float(item["minimum_selected_angle_margin_rad"]),
    )


def _ranking_key(item: dict[str, object]) -> tuple[float, ...]:
    """可解释的字典序：完整性优先，其次局部抗病态性。"""
    return (
        float(bool(item["feasible"])),
        float(item["global_unique_follower_count"]),
        float(item["worst_best_pair_sigma_min"]),
        -float(item["worst_best_pair_condition_number"]),
        float(item["minimum_angle_boundary_margin_rad"]),
        float(item["anchor_doubled_area"]),
    )


def similarity_invariance_check(winner: dict[str, object], lattice: dict[int, np.ndarray]) -> dict[str, object]:
    ids = tuple(int(index) for index in winner["anchor_ids"])
    base_anchors = np.vstack([lattice[index] for index in ids])
    base_followers = [index for index in sorted(lattice) if index not in ids]
    cases: list[dict[str, object]] = []
    transforms = [
        (0.4, 0.37, False, np.array([2.5, -1.7])),
        (2.3, -0.81, False, np.array([-3.0, 4.2])),
        (1.7, 1.23, True, np.array([0.4, 2.1])),
    ]
    for scale, theta, reflected, translation in transforms:
        rotation = np.array([[cos(theta), -sin(theta)], [sin(theta), cos(theta)]])
        reflection = np.diag([-1.0, 1.0]) if reflected else np.eye(2)
        linear = scale * rotation @ reflection
        anchors = (linear @ base_anchors.T).T + translation
        max_angle_error = 0.0
        max_normalized_sigma_error = 0.0
        for index in base_followers:
            base_point = lattice[index]
            transformed_point = linear @ base_point + translation
            base_angles = angle_signature(base_point, base_anchors)
            transformed_angles = angle_signature(transformed_point, anchors)
            max_angle_error = max(max_angle_error, float(np.max(np.abs(base_angles - transformed_angles))))
            base_sigma = float(_best_pair(base_point, base_anchors)["sigma_min"])
            transformed_sigma = float(_best_pair(transformed_point, anchors)["sigma_min"])
            max_normalized_sigma_error = max(max_normalized_sigma_error, abs(base_sigma - scale * transformed_sigma))
        cases.append(
            {
                "scale": scale,
                "theta": theta,
                "reflected": reflected,
                "translation": translation.tolist(),
                "max_angle_error": max_angle_error,
                "max_normalized_sigma_error": max_normalized_sigma_error,
                "pass": bool(max_angle_error < 2e-12 and max_normalized_sigma_error < 2e-10),
            }
        )
    return {
        "status": "PASS" if all(bool(case["pass"]) for case in cases) else "FAIL",
        "interpretation": "纯夹角对平移、旋转、整体反射和共同缩放不变；物理尺度只能由合法参考尺度注入。",
        "cases": cases,
    }


def independent_winner_check(winner: dict[str, object], lattice: dict[int, np.ndarray]) -> dict[str, object]:
    ids = tuple(int(index) for index in winner["anchor_ids"])
    anchors = np.vstack([lattice[index] for index in ids])
    cases: list[dict[str, object]] = []
    for index in sorted(lattice):
        if index in ids:
            continue
        target = lattice[index]
        observed = angle_signature(target, anchors)
        primary = complete_candidates(anchors, observed, angle_tol=2e-8, geometry_tol=1e-10)
        secondary = independent_multistart_checker(
            anchors,
            observed,
            starts_per_axis=7,
            max_iterations=80,
            root_tol=2e-8,
            finite_difference_step=1e-5,
        )
        primary_roots = [candidate.point for candidate in primary.candidates]
        agrees = _same_point_sets(primary_roots, secondary.roots)
        cases.append(
            {
                "receiver": index,
                "primary_roots": [point.tolist() for point in primary_roots],
                "secondary_roots": [point.tolist() for point in secondary.roots],
                "secondary_attempts": secondary.attempts,
                "pass": bool(agrees and _point_in(primary_roots, target)),
            }
        )
    return {
        "status": "PASS" if all(bool(case["pass"]) for case in cases) else "FAIL",
        "scope": "赢家三参考机组合的 12 个接收槽位；圆轨迹候选器与有限差分多初值角方程复核器互证。",
        "cases": cases,
    }


def _independent_four_signature(point: np.ndarray, anchors: np.ndarray) -> np.ndarray:
    values: list[float] = []
    for left, right in FOUR_PAIR_INDICES:
        first = anchors[left] - point
        second = anchors[right] - point
        cross = float(first[0] * second[1] - first[1] * second[0])
        dot = float(np.dot(first, second))
        values.append(float(np.arctan2(abs(cross), dot)))
    return np.array(values)


def _independent_four_multistart(
    anchors: np.ndarray,
    observed: np.ndarray,
    active: list[int],
    *,
    starts_per_axis: int = 9,
    max_iterations: int = 100,
    root_tol: float = 3e-8,
    finite_difference_step: float = 1e-5,
) -> dict[str, object]:
    """不用圆轨迹候选器的六角最小二乘多初值复核。"""
    centroid = np.mean(anchors, axis=0)
    span = max(1.0, max(float(np.linalg.norm(anchor - centroid)) for anchor in anchors))
    roots: list[np.ndarray] = []
    attempts = 0
    for multiplier in (1.0, 3.0, 10.0, 30.0):
        axis = np.linspace(-multiplier * span, multiplier * span, starts_per_axis)
        for dx in axis:
            for dy in axis:
                attempts += 1
                point = centroid + np.array([dx, dy])
                damping = 1e-5
                for _ in range(max_iterations):
                    signature = _independent_four_signature(point, anchors)
                    residual = signature[active] - observed[active]
                    if float(np.linalg.norm(residual, ord=np.inf)) < root_tol:
                        break
                    jacobian = np.empty((len(active), 2), dtype=float)
                    for column in range(2):
                        delta = np.zeros(2)
                        delta[column] = finite_difference_step
                        plus = _independent_four_signature(point + delta, anchors)[active]
                        minus = _independent_four_signature(point - delta, anchors)[active]
                        jacobian[:, column] = (plus - minus) / (2.0 * finite_difference_step)
                    normal = jacobian.T @ jacobian + damping * np.eye(2)
                    try:
                        step = -np.linalg.solve(normal, jacobian.T @ residual)
                    except np.linalg.LinAlgError:
                        break
                    if not np.all(np.isfinite(step)):
                        break
                    current_norm = float(np.linalg.norm(residual))
                    accepted = False
                    for factor in (1.0, 0.5, 0.25, 0.125, 0.0625):
                        proposal = point + factor * step
                        proposal_residual = _independent_four_signature(proposal, anchors)[active] - observed[active]
                        if float(np.linalg.norm(proposal_residual)) < current_norm:
                            point = proposal
                            damping = max(damping / 3.0, 1e-12)
                            accepted = True
                            break
                    if not accepted:
                        damping *= 10.0
                        if damping > 1e10:
                            break
                final_residual = _independent_four_signature(point, anchors)[active] - observed[active]
                if float(np.max(np.abs(final_residual))) <= root_tol:
                    roots = _deduplicate_points(roots + [point], tol=2e-5)
    return {"roots": roots, "attempts": attempts}


def independent_four_reference_check(reference_audit: dict[str, object], lattice: dict[int, np.ndarray]) -> dict[str, object]:
    reference_ids = tuple(int(index) for index in reference_audit["reference_ids"])
    anchors = np.vstack([lattice[index] for index in reference_ids])
    cases: list[dict[str, object]] = []
    for receiver_record in reference_audit["receivers"]:
        receiver = int(receiver_record["receiver"])
        observed = _four_signature(lattice[receiver], anchors)
        primary = _complete_four_candidates(anchors, observed)
        active = list(primary["active_constraints"])
        secondary = _independent_four_multistart(anchors, observed, active)
        primary_roots = list(primary["roots"])
        cases.append(
            {
                "receiver": receiver,
                "reference_ids": list(reference_ids),
                "active_constraint_indices": active,
                "primary_roots": [point.tolist() for point in primary_roots],
                "secondary_roots": [point.tolist() for point in secondary["roots"]],
                "secondary_attempts": secondary["attempts"],
                "pass": bool(
                    len(primary_roots) == 1
                    and _point_in(primary_roots, lattice[receiver])
                    and _same_point_sets(primary_roots, secondary["roots"])
                ),
            }
        )
    return {
        "status": "PASS" if all(bool(case["pass"]) for case in cases) else "FAIL",
        "scope": "四参考机六条本机角约束的完整圆轨迹交点枚举，与独立有限差分多初值最小二乘复核器互证。",
        "cases": cases,
    }


def two_reference_rank_check(winner: dict[str, object], lattice: dict[int, np.ndarray]) -> dict[str, object]:
    ids = tuple(int(index) for index in winner["anchor_ids"])
    anchors = np.vstack([lattice[index] for index in ids])
    ranks: list[int] = []
    gradient_norms: list[float] = []
    for index in sorted(lattice):
        if index in ids:
            continue
        jacobian = angle_jacobian(lattice[index], anchors, ("ab",))
        ranks.append(int(np.linalg.matrix_rank(jacobian, tol=1e-10)))
        gradient_norms.append(float(np.linalg.norm(jacobian)))
    return {
        "status": "PASS" if ranks and max(ranks) == 1 and min(ranks) == 1 else "FAIL",
        "observed_scalar_dimension": 1,
        "unknown_position_dimension": 2,
        "local_jacobian_ranks": ranks,
        "gradient_norm_range": [min(gradient_norms), max(gradient_norms)],
        "interpretation": "两参考机只给一个独立夹角方程，局部秩至多为 1，不能一般性确定二维位置。",
    }


def run_audit() -> dict[str, object]:
    lattice = triangular_lattice()
    triples = [evaluate_triple(ids, lattice) for ids in combinations(sorted(lattice), 3)]
    ranked = sorted(triples, key=_ranking_key, reverse=True)
    winner = ranked[0]
    feasible = [item for item in ranked if bool(item["feasible"])]
    four_sets = [evaluate_four_reference_set(ids, lattice) for ids in combinations(sorted(lattice), 4)]
    ranked_four_sets = sorted(four_sets, key=_four_reference_ranking_key, reverse=True)
    four_winner = ranked_four_sets[0]
    bootstrappable_four = evaluate_four_reference_set(BOOTSTRAPPABLE_REFERENCE_IDS, lattice)
    independent_bootstrappable_four = independent_four_reference_check(bootstrappable_four, lattice)
    independent = independent_winner_check(winner, lattice)
    similarity = similarity_invariance_check(winner, lattice)
    two_reference = two_reference_rank_check(winner, lattice)
    gate_pass = (
        bool(feasible)
        and independent["status"] == "PASS"
        and independent_bootstrappable_four["status"] == "PASS"
        and similarity["status"] == "PASS"
        and two_reference["status"] == "PASS"
    )
    return {
        "gate": "Q2_ANCHOR_ROUTE_DESIGN_AUDIT",
        "status": "PASS" if gate_pass else "FAIL",
        "scope": "离线有限几何设计；不构成 Q2 在线控制实现或最终冻结。",
        "lattice": {str(index): point.tolist() for index, point in lattice.items()},
        "triple_count": len(triples),
        "feasible_triple_count": len(feasible),
        "ranking_rule": [
            "完整找回所有目标且局部满秩",
            "全局单候选的跟随槽位数最多",
            "最坏最佳主角对 sigma_min 最大",
            "最坏条件数最小",
            "离 0/pi 的最小角裕度最大",
            "参考三角形面积大",
        ],
        "winner": winner,
        "top_10": [
            {key: value for key, value in item.items() if key != "followers"}
            for item in ranked[:10]
        ],
        "independent_winner_check": independent,
        "similarity_invariance_check": similarity,
        "two_reference_insufficiency_check": two_reference,
        "all_triples": [
            {key: value for key, value in item.items() if key != "followers"}
            for item in triples
        ],
        "four_reference_extension": {
            "set_count": len(four_sets),
            "feasible_set_count": sum(int(item["feasible"]) for item in four_sets),
            "interpretation": "四架可信参考机不是最小配置；它允许每个接收机预选不同的三机子集，用于提高消歧和条件性。",
            "winner": four_winner,
            "bootstrappable_reference_set": bootstrappable_four,
            "bootstrappable_reference_independent_check": independent_bootstrappable_four,
            "top_10": [
                {key: value for key, value in item.items() if key != "receivers"}
                for item in ranked_four_sets[:10]
            ],
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
                "triple_count": result["triple_count"],
                "feasible_triple_count": result["feasible_triple_count"],
                "winner": result["winner"]["anchor_ids"],
                "unique_followers": result["winner"]["global_unique_follower_count"],
                "worst_sigma_min": result["winner"]["worst_best_pair_sigma_min"],
                "worst_condition_number": result["winner"]["worst_best_pair_condition_number"],
                "four_reference_winner": result["four_reference_extension"]["winner"]["reference_ids"],
                "four_reference_unique_receivers": result["four_reference_extension"]["winner"][
                    "global_unique_receiver_count"
                ],
                "four_reference_worst_sigma_min": result["four_reference_extension"]["winner"][
                    "worst_selected_sigma_min"
                ],
                "output": str(OUT),
            },
            ensure_ascii=False,
        )
    )
    raise SystemExit(0 if result["status"] == "PASS" else 1)
