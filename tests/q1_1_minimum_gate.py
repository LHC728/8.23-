"""Deterministic Q1(1) minimum-oracle Gate.

Run from repository root:
    python -m tests.q1_1_minimum_gate
"""

from __future__ import annotations

import json
from math import pi
from pathlib import Path

import numpy as np

from src.q1_1_geometry import (
    Circle,
    angle_signature,
    complete_candidates,
    independent_multistart_checker,
    rank_certificate,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "q1_1" / "q1_1_minimum_gate.json"


def _contains(points: list[np.ndarray], expected: np.ndarray, tol: float = 2e-5) -> bool:
    return any(float(np.linalg.norm(point - expected)) <= tol for point in points)


def _same_sets(left: list[np.ndarray], right: list[np.ndarray], tol: float = 2e-5) -> bool:
    return len(left) == len(right) and all(_contains(right, point, tol) for point in left)


def _normal_case(name: str, tx: np.ndarray, truth: np.ndarray, *, near_eps: float | None = None) -> dict:
    y = angle_signature(truth, tx)
    main = complete_candidates(tx, y, near_boundary_eps=near_eps or 1e-3)
    checker = independent_multistart_checker(tx, y, starts_per_axis=9, max_iterations=80)
    candidates = [item.point for item in main.candidates]
    rank = rank_certificate(truth, tx, ("ab", "ac"))
    passed = _contains(candidates, truth) and _same_sets(candidates, checker.roots) and bool(rank["full_rank"])
    if near_eps is not None:
        passed = passed and "angle_near_0_or_pi" in main.status
    return {
        "name": name,
        "pass": passed,
        "truth": truth.tolist(),
        "observed_angles_rad": y.tolist(),
        "main_candidates": [point.tolist() for point in candidates],
        "checker_roots": [point.tolist() for point in checker.roots],
        "main_status": sorted(main.status),
        "checker_status": sorted(checker.status),
        "checker_attempts": checker.attempts,
        "rank_certificate": rank,
    }


def run_gate() -> dict:
    cases: list[dict] = []

    # Ideal nondegenerate labelled geometry: one local finite root and rank two.
    cases.append(
        _normal_case(
            "ideal_nondegenerate",
            np.array([[0.0, 0.0], [4.0, 0.0], [1.0, 3.0]]),
            np.array([1.5, 1.0]),
        )
    )

    # Collinear transmitters make reflection across their line indistinguishable
    # to unsigned angles; both finite roots must remain in the answer set.
    tx_mirror = np.array([[-1.0, 0.0], [0.0, 0.0], [1.0, 0.0]])
    y_mirror = angle_signature(np.array([0.0, 1.0]), tx_mirror)
    main_mirror = complete_candidates(tx_mirror, y_mirror)
    checker_mirror = independent_multistart_checker(tx_mirror, y_mirror, starts_per_axis=9, max_iterations=80)
    mirror_points = [item.point for item in main_mirror.candidates]
    expected_mirrors = [np.array([0.0, 1.0]), np.array([0.0, -1.0])]
    cases.append(
        {
            "name": "mirror_multibranch",
            "pass": all(_contains(mirror_points, point) for point in expected_mirrors)
            and _same_sets(mirror_points, checker_mirror.roots)
            and "multiple_candidates_retained" in main_mirror.status,
            "observed_angles_rad": y_mirror.tolist(),
            "main_candidates": [point.tolist() for point in mirror_points],
            "checker_roots": [point.tolist() for point in checker_mirror.roots],
            "main_status": sorted(main_mirror.status),
            "checker_status": sorted(checker_mirror.status),
            "rank_plus": rank_certificate(expected_mirrors[0], tx_mirror, ("ab", "ac")),
            "rank_minus": rank_certificate(expected_mirrors[1], tx_mirror, ("ab", "ac")),
        }
    )

    # This is an explicit simple multi-root record, deliberately separate from
    # uniqueness certification: two roots are expected, not an error to hide.
    cases.append(
        {
            "name": "explicit_multiroot_simple_example",
            "pass": len(mirror_points) == 2 and _contains(mirror_points, expected_mirrors[0]) and _contains(mirror_points, expected_mirrors[1]),
            "expected_root_count": 2,
            "retained_root_count": len(mirror_points),
            "status": sorted(main_mirror.status),
        }
    )

    # A genuine circle-pair tangency is a branch event.  The candidate routine
    # must mark it, reject any transmitter coincidence, and continue checking
    # all remaining branches rather than failing silently.
    tx_tangent = np.array([[0.0, 0.0], [2.0, 0.0], [0.0, 4.0]])
    y_tangent = np.array([pi / 4.0, pi / 4.0, pi / 2.0])
    tangent = complete_candidates(tx_tangent, y_tangent)
    cases.append(
        {
            "name": "tangent_constraint_branch",
            "pass": tangent.tangent_events > 0 and "tangent_circle_intersection" in tangent.status,
            "tangent_events": tangent.tangent_events,
            "coincident_circle_events": tangent.coincident_circle_events,
            "retained_root_count": len(tangent.candidates),
            "status": sorted(tangent.status),
        }
    )

    cases.append(
        _normal_case(
            "near_degenerate_small_angle",
            np.array([[-1.0, 0.0], [1.0, 0.0], [0.0, 2.0]]),
            np.array([0.0, 20.0]),
            near_eps=0.15,
        )
    )

    # Exact 0 and pi observations are explicitly rejected for ordinary circle/
    # Jacobian construction; they are not silently passed to a generic solver.
    tx_boundary = np.array([[-1.0, 0.0], [1.0, 0.0], [0.0, 2.0]])
    for name, truth in (("zero_angle_boundary", np.array([2.0, 0.0])), ("pi_angle_boundary", np.array([0.0, 0.0]))):
        y = angle_signature(truth, tx_boundary)
        main = complete_candidates(tx_boundary, y)
        checker = independent_multistart_checker(tx_boundary, y)
        cases.append(
            {
                "name": name,
                "pass": len(main.candidates) == 0
                and "angle_near_0_or_pi" in main.status
                and "checker_boundary_angle_safely_rejected" in checker.status,
                "observed_angles_rad": y.tolist(),
                "main_status": sorted(main.status),
                "checker_status": sorted(checker.status),
            }
        )

    passed = all(bool(case["pass"]) for case in cases)
    return {
        "gate": "Q1_1_MINIMUM_GATE",
        "status": "PASS" if passed else "FAIL",
        "scope": "deterministic candidate/oracle/rank checks only; no batch simulation",
        "cases": cases,
        "requirements_checked": {
            "known_truth_recovered": bool(cases[0]["pass"]),
            "both_sides_not_artificially_deleted": bool(cases[1]["pass"]),
            "multiroot_not_mislabelled_unique": bool(cases[2]["pass"]),
            "raw_atan2_revalidation": bool(cases[0]["pass"] and cases[1]["pass"]),
            "independent_checker_agrees": bool(cases[0]["pass"] and cases[1]["pass"]),
            "degeneracy_recognized_or_rejected": bool(cases[3]["pass"] and cases[4]["pass"] and cases[5]["pass"] and cases[6]["pass"]),
            "target_branch_has_rank_two": bool(cases[0]["rank_certificate"]["full_rank"]),
        },
    }


if __name__ == "__main__":
    report = run_gate()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(OUT)}, ensure_ascii=False))
    raise SystemExit(0 if report["status"] == "PASS" else 1)
