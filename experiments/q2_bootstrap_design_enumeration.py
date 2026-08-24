"""完整枚举 Q2 的两可信种子与两节点交替建锚排程。"""

from __future__ import annotations

import json
from functools import lru_cache
from itertools import combinations, permutations
from pathlib import Path

import numpy as np

from experiments.q2_anchor_route_audit import _best_pair, evaluate_four_reference_set, triangular_lattice
from experiments.q2_bootstrap_audit import other_transmitter_jacobian
from src.q1_1_geometry import angle_jacobian, angle_signature, complete_candidates


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "q2_design" / "q2_bootstrap_design_enumeration.json"


def _contains(points: list[np.ndarray], target: np.ndarray, tol: float = 2e-7) -> bool:
    return any(float(np.linalg.norm(point - target)) <= tol for point in points)


def evaluate_schedule(
    seeds: tuple[int, int],
    first_receiver: int,
    second_receiver: int,
    lattice: dict[int, np.ndarray],
    four_audit: dict[str, object],
) -> dict[str, object] | None:
    responses: list[np.ndarray] = []
    node_records: list[dict[str, object]] = []
    for receiver, other in ((first_receiver, second_receiver), (second_receiver, first_receiver)):
        transmitters = np.vstack([lattice[seeds[0]], lattice[seeds[1]], lattice[other]])
        observed = angle_signature(lattice[receiver], transmitters)
        margin = float(np.min(np.minimum(observed, np.pi - observed)))
        if margin <= 1e-7:
            return None
        candidates = complete_candidates(transmitters, observed, angle_tol=2e-8, geometry_tol=1e-10)
        roots = [item.point for item in candidates.candidates]
        if not _contains(roots, lattice[receiver]):
            return None
        best = _best_pair(lattice[receiver], transmitters)
        names = tuple(str(name) for name in best["names"])
        self_jacobian = angle_jacobian(lattice[receiver], transmitters, names)
        other_jacobian = other_transmitter_jacobian(lattice[receiver], transmitters, names)
        if abs(float(np.linalg.det(self_jacobian))) <= 1e-10:
            return None
        response = -np.linalg.solve(self_jacobian, other_jacobian)
        responses.append(response)
        node_records.append(
            {
                "receiver": receiver,
                "other": other,
                "transmitter_ids": [seeds[0], seeds[1], other],
                "primary_angle_names": list(names),
                "candidate_count": len(roots),
                "nearest_wrong_root_distance_d": min(
                    (float(np.linalg.norm(root - lattice[receiver])) for root in roots if np.linalg.norm(root - lattice[receiver]) > 2e-7),
                    default=None,
                ),
                "angle_boundary_margin_rad": margin,
                "self_sigma_min": float(best["sigma_min"]),
                "self_condition_number": float(best["condition_number"]),
                "best_response_derivative": response.tolist(),
            }
        )

    reduced = responses[1] @ responses[0]
    spectral_radius = float(np.max(np.abs(np.linalg.eigvals(reduced))))
    return {
        "seed_ids": list(seeds),
        "bootstrap_order": [first_receiver, second_receiver],
        "reference_ids": sorted([seeds[0], seeds[1], first_receiver, second_receiver]),
        "seed_distance_d": float(np.linalg.norm(lattice[seeds[0]] - lattice[seeds[1]])),
        "spectral_radius": spectral_radius,
        "locally_contracting": bool(spectral_radius < 1.0 - 1e-10),
        "bootstrap_worst_self_sigma_min": min(float(item["self_sigma_min"]) for item in node_records),
        "bootstrap_worst_condition_number": max(float(item["self_condition_number"]) for item in node_records),
        "bootstrap_minimum_angle_margin_rad": min(float(item["angle_boundary_margin_rad"]) for item in node_records),
        "bootstrap_nodes": node_records,
        "final_reference_feasible": bool(four_audit["feasible"]),
        "final_global_unique_receiver_count": int(four_audit["global_unique_receiver_count"]),
        "final_worst_sigma_min": float(four_audit["worst_selected_sigma_min"]),
        "final_worst_condition_number": float(four_audit["worst_selected_condition_number"]),
        "final_minimum_angle_margin_rad": float(four_audit["minimum_selected_angle_margin_rad"]),
    }


def _ranking_key(item: dict[str, object]) -> tuple[float, ...]:
    spectral_radius = float(item["spectral_radius"])
    # 解析上为零的谱半径在浮点计算中可能表现为 1e-16；先按容差归零，
    # 避免数值噪声压过后续的四参考组条件性指标。
    effective_spectral_radius = 0.0 if spectral_radius < 1e-12 else spectral_radius
    return (
        float(bool(item["locally_contracting"])),
        float(bool(item["final_reference_feasible"])),
        float(item["final_global_unique_receiver_count"]),
        -effective_spectral_radius,
        float(item["final_worst_sigma_min"]),
        float(item["bootstrap_worst_self_sigma_min"]),
        -float(item["bootstrap_worst_condition_number"]),
        float(item["bootstrap_minimum_angle_margin_rad"]),
    )


def run_enumeration() -> dict[str, object]:
    lattice = triangular_lattice()
    ids = tuple(sorted(lattice))

    @lru_cache(maxsize=None)
    def four_audit(reference_ids: tuple[int, int, int, int]) -> dict[str, object]:
        return evaluate_four_reference_set(reference_ids, lattice)

    records: list[dict[str, object]] = []
    theoretical_count = 0
    for seeds in combinations(ids, 2):
        remaining = [index for index in ids if index not in seeds]
        for first, second in permutations(remaining, 2):
            theoretical_count += 1
            reference_ids = tuple(sorted([seeds[0], seeds[1], first, second]))
            record = evaluate_schedule(seeds, first, second, lattice, four_audit(reference_ids))
            if record is not None:
                records.append(record)

    ranked = sorted(records, key=_ranking_key, reverse=True)
    winner = ranked[0]
    contracting = [item for item in records if bool(item["locally_contracting"])]
    fully_usable = [
        item
        for item in contracting
        if bool(item["final_reference_feasible"]) and int(item["final_global_unique_receiver_count"]) == 11
    ]
    return {
        "gate": "Q2_TWO_SEED_SCHEDULE_COMPLETE_ENUMERATION",
        "status": "PASS" if fully_usable else "FAIL",
        "theoretical_ordered_schedule_count": theoretical_count,
        "geometrically_valid_schedule_count": len(records),
        "locally_contracting_schedule_count": len(contracting),
        "fully_usable_schedule_count": len(fully_usable),
        "unique_four_reference_sets_evaluated": four_audit.cache_info().currsize,
        "ranking_rule": [
            "交替周期局部收缩",
            "最终四参考组几何可用",
            "最终全局单候选接收机数最多",
            "周期谱半径最小",
            "最终最坏 sigma_min 最大",
            "建锚本机最坏 sigma_min 最大",
            "建锚最大条件数最小",
            "建锚最小角边界裕度最大",
        ],
        "winner": winner,
        "top_20": ranked[:20],
        "requested_schedule_record": next(
            (
                item
                for item in records
                if item["seed_ids"] == [6, 14] and item["bootstrap_order"] == [8, 1]
            ),
            None,
        ),
    }


if __name__ == "__main__":
    result = run_enumeration()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": result["status"],
                "theoretical_count": result["theoretical_ordered_schedule_count"],
                "valid_count": result["geometrically_valid_schedule_count"],
                "contracting_count": result["locally_contracting_schedule_count"],
                "fully_usable_count": result["fully_usable_schedule_count"],
                "winner": result["winner"],
                "requested_schedule": result["requested_schedule_record"],
                "output": str(OUT),
            },
            ensure_ascii=False,
        )
    )
    raise SystemExit(0 if result["status"] == "PASS" else 1)
