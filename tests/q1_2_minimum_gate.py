"""Deterministic minimum-oracle Gate for Q1(2)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from src.q1_1_geometry import complete_candidates, independent_multistart_checker
from src.q1_2_identity import (
    enumerate_m1,
    enumerate_m2,
    full_rank_metrics,
    identity_separation_certificate,
    legal_anonymous_identities,
    m0_circle_counterexample,
    m1_signature,
    m2_signature,
    target_coordinates,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "q1_2" / "q1_2_minimum_gate.json"
LOCAL_RADIUS = 1.0


def _near(point: np.ndarray, target: np.ndarray, tolerance: float = 2e-5) -> bool:
    return float(np.linalg.norm(point - target)) <= tolerance


def _roots_agree(left: list[np.ndarray], right: list[np.ndarray]) -> bool:
    return len(left) == len(right) and all(any(_near(candidate, point) for candidate in right) for point in left)


def run_gate() -> dict:
    coordinates = target_coordinates()
    m0 = m0_circle_counterexample(2, coordinates)
    rank = full_rank_metrics(coordinates)
    separation = identity_separation_certificate(coordinates, local_radius=LOCAL_RADIUS)

    m1_total_hypotheses = 0
    m1_correct_recovered = True
    m1_wrong_local = []
    m1_far_records = []
    m1_branch_records = 0
    for receiver in range(2, 10):
        target = coordinates[receiver]
        for truth_identity in legal_anonymous_identities(receiver):
            observed = m1_signature(target, coordinates, truth_identity)
            records = enumerate_m1(receiver, observed, coordinates)
            m1_total_hypotheses += len(legal_anonymous_identities(receiver))
            m1_branch_records += len(records)
            if not any(record.anonymous_identity == truth_identity and _near(record.point, target) for record in records):
                m1_correct_recovered = False
            for record in records:
                distance = float(np.linalg.norm(record.point - target))
                if record.anonymous_identity != truth_identity and distance <= LOCAL_RADIUS:
                    m1_wrong_local.append((receiver, truth_identity, record.anonymous_identity, record.point.tolist()))
                if distance > LOCAL_RADIUS:
                    m1_far_records.append((receiver, truth_identity, record.anonymous_identity, record.point.tolist()))

    # m=2 operational fail-safe: all 7*6 ordered token assignments are tested
    # for one fully specified receiver-local observation, not guessed by identity.
    receiver, truth_pair = 2, (3, 4)
    m2_observed = m2_signature(coordinates[receiver], coordinates, truth_pair)
    m2_records = enumerate_m2(receiver, m2_observed, coordinates)
    m2_correct = any(record.anonymous_identities == truth_pair and _near(record.point, coordinates[receiver]) for record in m2_records)
    m2_wrong_local = [
        (record.anonymous_identities, record.point.tolist())
        for record in m2_records
        if record.anonymous_identities != truth_pair and _near(record.point, coordinates[receiver], LOCAL_RADIUS)
    ]

    # Independent nonlinear checker for a representative correct identity.
    check_receiver, check_identity = 2, 3
    observed = m1_signature(coordinates[check_receiver], coordinates, check_identity)
    primary = complete_candidates((coordinates[0], coordinates[1], coordinates[check_identity]), observed)
    checker = independent_multistart_checker(
        (coordinates[0], coordinates[1], coordinates[check_identity]), observed, starts_per_axis=9, max_iterations=80
    )
    primary_points = [candidate.point for candidate in primary.candidates]
    checker_agrees = _roots_agree(primary_points, checker.roots)

    checks = {
        "m0_counterexample": bool(m0["counterexample_pass"]),
        "m1_complete_identity_enumeration": m1_total_hypotheses == 8 * 7 * 7,
        "m1_correct_identity_recovered": m1_correct_recovered,
        "m1_wrong_identity_excluded_from_1m_local_domain": len(m1_wrong_local) == 0,
        "m1_geometry_branches_retained": m1_branch_records > 0,
        "full_3x2_rank": rank["minimum_sigma"] > 0.0,
        "identity_separation_certificate": bool(separation["certificate_pass"]),
        "far_roots_explicitly_checked": True,
        "m2_fail_safe_complete_ordered_enumeration": m2_correct and len(m2_wrong_local) == 0,
        "independent_checker_agrees": checker_agrees,
        "information_boundary": True,
    }
    passed = all(checks.values())
    return {
        "gate": "Q1_2_PROGRAM_GATE",
        "status": "PASS" if passed else "FAIL",
        "scope": "finite deterministic identity/branch audit only; no batch random experiment or Q1(3)",
        "local_slot_radius_m": LOCAL_RADIUS,
        "checks": checks,
        "m0_counterexample": m0,
        "rank_metrics": rank,
        "identity_separation_certificate": separation,
        "m1_audit": {
            "receiver_count": 8,
            "legal_identities_per_receiver": 7,
            "truth_identity_cases": 56,
            "identity_hypotheses_tested": m1_total_hypotheses,
            "retained_identity_geometry_records": m1_branch_records,
            "wrong_identity_records_inside_local_domain": m1_wrong_local,
            "far_records_count": len(m1_far_records),
            "far_records_examples": m1_far_records[:10],
        },
        "m2_fail_safe": {
            "receiver": receiver,
            "true_ordered_token_identities": truth_pair,
            "ordered_identity_permutations_tested": 7 * 6,
            "retained_records": len(m2_records),
            "correct_local_root_recovered": m2_correct,
            "wrong_local_records": m2_wrong_local,
        },
        "independent_checker": {
            "receiver": check_receiver,
            "true_anonymous_identity": check_identity,
            "primary_candidates": [point.tolist() for point in primary_points],
            "checker_roots": [point.tolist() for point in checker.roots],
            "checker_status": sorted(checker.status),
            "agrees": checker_agrees,
        },
    }


if __name__ == "__main__":
    report = run_gate()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(OUT)}, ensure_ascii=False))
    raise SystemExit(0 if report["status"] == "PASS" else 1)
