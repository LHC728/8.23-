"""Q2 最终候选路线的紧凑确定性总 Gate。"""

from __future__ import annotations

import inspect
import json
from math import cos, sin
from pathlib import Path

import numpy as np

from experiments.q2_anchor_route_audit import _four_signature, triangular_lattice
from experiments.q2_local_route_sanity import formation_metrics, local_probe_controller_action


ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = ROOT / "results" / "q2_design"
OUT = RESULT_DIR / "q2_final_route_gate.json"


def _read(name: str) -> dict[str, object]:
    return json.loads((RESULT_DIR / name).read_text(encoding="utf-8"))


def similarity_check() -> dict[str, object]:
    lattice = triangular_lattice()
    reference_ids = (3, 4, 11, 15)
    follower_ids = tuple(index for index in sorted(lattice) if index not in reference_ids)
    base_anchors = np.vstack([lattice[index] for index in reference_ids])
    transforms = (
        (0.37, 0.41, False, np.array([2.3, -1.7])),
        (2.4, -0.83, False, np.array([-3.2, 4.1])),
        (1.6, 1.17, True, np.array([0.5, 2.2])),
    )
    cases: list[dict[str, object]] = []
    for scale, theta, reflected, translation in transforms:
        rotation = np.array([[cos(theta), -sin(theta)], [sin(theta), cos(theta)]])
        reflection = np.diag([-1.0, 1.0]) if reflected else np.eye(2)
        linear = scale * rotation @ reflection
        transformed_anchors = (linear @ base_anchors.T).T + translation
        maximum_error = 0.0
        for receiver in follower_ids:
            transformed_receiver = linear @ lattice[receiver] + translation
            maximum_error = max(
                maximum_error,
                float(
                    np.max(
                        np.abs(
                            _four_signature(transformed_receiver, transformed_anchors)
                            - _four_signature(lattice[receiver], base_anchors)
                        )
                    )
                ),
            )
        cases.append(
            {
                "scale": scale,
                "theta": theta,
                "reflected": reflected,
                "translation": translation.tolist(),
                "maximum_angle_error": maximum_error,
                "pass": bool(maximum_error < 3e-12),
            }
        )
    return {
        "status": "PASS" if all(bool(case["pass"]) for case in cases) else "FAIL",
        "interpretation": "本机夹角对共同平移、旋转、反射和缩放不变；指定尺度必须来自可信基线。",
        "cases": cases,
    }


def controller_interface_check() -> dict[str, object]:
    parameters = list(inspect.signature(local_probe_controller_action).parameters)
    allowed = {"observe_offset", "target_angles", "probe", "gain", "damping", "max_step"}
    forbidden_fragments = ("coordinate", "distance", "truth", "anchor", "global", "other_receiver")
    forbidden_found = [name for name in parameters if any(fragment in name.lower() for fragment in forbidden_fragments)]
    return {
        "status": "PASS" if set(parameters) == allowed and not forbidden_found else "FAIL",
        "actual_parameters": parameters,
        "forbidden_parameters_found": forbidden_found,
        "interpretation": "在线动作函数只接收本机试探观测回调、预装目标角和本机数值参数。",
    }


def run_gate() -> dict[str, object]:
    anchor = _read("q2_anchor_route_audit.json")
    enumeration = _read("q2_bootstrap_design_enumeration.json")
    bootstrap = _read("q2_bootstrap_audit.json")
    local = _read("q2_local_route_sanity.json")

    four = anchor["four_reference_extension"]
    selected = four["bootstrappable_reference_set"]
    independent = four["bootstrappable_reference_independent_check"]
    winner = enumeration["winner"]
    similarity = similarity_check()
    interface = controller_interface_check()
    ideal_metrics = formation_metrics(triangular_lattice(), triangular_lattice())

    checks = {
        "anchor_route_audit": bool(anchor["status"] == "PASS"),
        "final_four_reference_ids": bool(selected["reference_ids"] == [3, 4, 11, 15]),
        "final_four_all_11_unique": bool(selected["global_unique_receiver_count"] == 11),
        "final_four_independent_root_check": bool(independent["status"] == "PASS"),
        "complete_schedule_enumeration": bool(
            enumeration["status"] == "PASS" and enumeration["theoretical_ordered_schedule_count"] == 16380
        ),
        "winner_identity": bool(
            winner["seed_ids"] == [11, 15]
            and winner["bootstrap_order"] == [4, 3]
            and winner["reference_ids"] == [3, 4, 11, 15]
        ),
        "bootstrap_audit": bool(bootstrap["status"] == "PASS"),
        "bootstrap_first_order_nilpotent": bool(bootstrap["linearization"]["spectral_radius"] < 1e-12),
        "bootstrap_exact_grid": bool(bootstrap["exact_best_response_grid"]["status"] == "PASS"),
        "bootstrap_finite_probe_grid": bool(bootstrap["finite_probe_grid"]["status"] == "PASS"),
        "follower_local_grid": bool(local["local_basin_grid_check"]["status"] == "PASS"),
        "reference_perturbation_sensitivity": bool(local["anchor_perturbation_check"]["status"] == "PASS"),
        "similarity_invariance": bool(similarity["status"] == "PASS"),
        "controller_information_interface": bool(interface["status"] == "PASS"),
        "independent_30_edge_and_line_evaluator": bool(
            ideal_metrics["nearest_neighbor_edge_count"] == 30
            and ideal_metrics["edge_max_abs_error_from_d"] < 1e-12
            and ideal_metrics["maximum_line_distance"] < 1e-12
        ),
    }
    return {
        "gate": "Q2_FINAL_ROUTE_DESIGN_GATE",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "scope": "路线设计与小范围确定性验证；尚未改写 Strategy Freeze，也不是 Q2 正式结果冻结。",
        "checks": checks,
        "winner": {
            "trusted_seed_ids": [11, 15],
            "trusted_baseline_length_in_d_star": 4.0,
            "bootstrap_order": [4, 3],
            "final_reference_ids": [3, 4, 11, 15],
            "remaining_parallel_receivers": 11,
        },
        "similarity_invariance_check": similarity,
        "controller_interface_check": interface,
        "ideal_geometry_evaluator": ideal_metrics,
        "required_assumption": "FY11 与 FY15 的实际相对位置无偏差，因而其基线长度为 4 d*；否则只能退回自由尺度结论。",
        "claim_limit": "仅目标邻域、非退化和明示可信基线条件；不声称任意初态全局收敛。",
    }


if __name__ == "__main__":
    result = run_gate()
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
