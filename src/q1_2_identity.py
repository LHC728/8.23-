"""Q1(2) receiver-local anonymous-identity enumeration.

All functions are offline proof/checking interfaces.  A single online receiver
would receive only its own labelled FY00/FY01 signals, anonymous tokens, and
the pairwise angles among those signals.  Truth positions are used here only to
construct deterministic certificates and tests, never as solver inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, permutations
from math import cos, pi, sin
from typing import Sequence

import numpy as np

from src.q1_1_geometry import angle_jacobian, angle_signature, complete_candidates, raw_angle


@dataclass(frozen=True)
class M1Record:
    anonymous_identity: int
    point: np.ndarray


@dataclass(frozen=True)
class M2Record:
    anonymous_identities: tuple[int, int]
    point: np.ndarray


def target_coordinates(radius: float = 100.0) -> dict[int, np.ndarray]:
    """Frozen Q1 coordinate convention: FY00 center, FY01 at phase zero."""
    points = {0: np.array([0.0, 0.0])}
    for index in range(1, 10):
        phase = 2.0 * pi * (index - 1) / 9.0
        points[index] = radius * np.array([cos(phase), sin(phase)])
    return points


def legal_anonymous_identities(receiver: int) -> tuple[int, ...]:
    if receiver not in range(2, 10):
        raise ValueError("Q1(2) receiver must be one of FY02..FY09")
    return tuple(index for index in range(2, 10) if index != receiver)


def m1_signature(x: Sequence[float], coordinates: dict[int, np.ndarray], anonymous_identity: int) -> np.ndarray:
    """Token order is fixed as (01, 0u, 1u), while u's identity is unknown."""
    return angle_signature(x, (coordinates[0], coordinates[1], coordinates[anonymous_identity]))


def m2_signature(x: Sequence[float], coordinates: dict[int, np.ndarray], identities: tuple[int, int]) -> np.ndarray:
    """All six pair angles in token order (01,0u,0v,1u,1v,uv)."""
    transmitter_ids = (0, 1, identities[0], identities[1])
    return np.array(
        [raw_angle(x, coordinates[transmitter_ids[i]], coordinates[transmitter_ids[j]]) for i, j in combinations(range(4), 2)]
    )


def enumerate_m1(
    receiver: int,
    observed: Sequence[float],
    coordinates: dict[int, np.ndarray],
    *,
    angle_tol: float = 1e-8,
) -> list[M1Record]:
    """Complete finite identity × geometry-branch enumeration for one token."""
    records: list[M1Record] = []
    for hypothesis in legal_anonymous_identities(receiver):
        report = complete_candidates(
            (coordinates[0], coordinates[1], coordinates[hypothesis]), observed, angle_tol=angle_tol
        )
        records.extend(M1Record(hypothesis, candidate.point) for candidate in report.candidates)
    return records


def enumerate_m2(
    receiver: int,
    observed: Sequence[float],
    coordinates: dict[int, np.ndarray],
    *,
    angle_tol: float = 1e-8,
) -> list[M2Record]:
    """Full ordered-token identity enumeration for the two-anonymous fail-safe."""
    records: list[M2Record] = []
    for hypothesis in permutations(legal_anonymous_identities(receiver), 2):
        # Use the first anonymous token with known FY00/FY01 for complete
        # branch generation, then validate every one of the six raw angles.
        primary_observation = np.asarray(observed, dtype=float)[[0, 1, 3]]
        report = complete_candidates(
            (coordinates[0], coordinates[1], coordinates[hypothesis[0]]), primary_observation, angle_tol=angle_tol
        )
        for candidate in report.candidates:
            residual = m2_signature(candidate.point, coordinates, hypothesis) - observed
            if np.max(np.abs(residual)) <= angle_tol:
                records.append(M2Record(hypothesis, candidate.point))
    return records


def full_rank_metrics(coordinates: dict[int, np.ndarray]) -> dict:
    """Recompute the frozen 3x2 rank and best 2x2 determinant audit."""
    minimum_sigma = float("inf")
    minimum_best_det = float("inf")
    sigma_arg = det_arg = None
    for receiver in range(2, 10):
        x = coordinates[receiver]
        for identity in legal_anonymous_identities(receiver):
            jacobian = np.vstack(
                [
                    angle_jacobian(x, (coordinates[0], coordinates[1], coordinates[identity]), names)[0]
                    for names in (("ab",), ("ac",), ("bc",))
                ]
            )
            singular_values = np.linalg.svd(jacobian, compute_uv=False)
            if singular_values[-1] < minimum_sigma:
                minimum_sigma, sigma_arg = float(singular_values[-1]), (receiver, identity)
            best_det = max(abs(float(np.linalg.det(jacobian[list(rows), :]))) for rows in combinations(range(3), 2))
            if best_det < minimum_best_det:
                minimum_best_det, det_arg = best_det, (receiver, identity)
    return {
        "minimum_sigma": minimum_sigma,
        "minimum_sigma_times_R": minimum_sigma * 100.0,
        "minimum_sigma_arg": sigma_arg,
        "minimum_best_2x2_det": minimum_best_det,
        "minimum_best_2x2_det_times_R2": minimum_best_det * 10000.0,
        "minimum_best_2x2_det_arg": det_arg,
    }


def _signature_lipschitz_bound(x: np.ndarray, identities: tuple[int, ...], coordinates: dict[int, np.ndarray], radius: float) -> float:
    distances = {index: max(float(np.linalg.norm(x - coordinates[index])) - radius, 1e-12) for index in (0, 1, *identities)}
    pairs = ((0, 1), (0, identities[0]), (1, identities[0]))
    # Each angle gradient is bounded by the sum of the two bearing-gradient norms.
    return float(np.sqrt(sum((1.0 / distances[i] + 1.0 / distances[j]) ** 2 for i, j in pairs)))


def identity_separation_certificate(coordinates: dict[int, np.ndarray], *, local_radius: float = 1.0) -> dict:
    """Finite target audit plus a conservative Lipschitz separation lower bound."""
    min_delta = float("inf")
    min_lower = float("inf")
    delta_arg = lower_arg = None
    for receiver in range(2, 10):
        x = coordinates[receiver]
        identities = legal_anonymous_identities(receiver)
        for left, right in combinations(identities, 2):
            delta = float(np.linalg.norm(m1_signature(x, coordinates, left) - m1_signature(x, coordinates, right)))
            if delta < min_delta:
                min_delta, delta_arg = delta, (receiver, left, right)
            lipschitz = _signature_lipschitz_bound(x, (left,), coordinates, local_radius) + _signature_lipschitz_bound(
                x, (right,), coordinates, local_radius
            )
            lower = delta - local_radius * lipschitz
            if lower < min_lower:
                min_lower, lower_arg = lower, (receiver, left, right)
    return {
        "local_radius_m": local_radius,
        "minimum_target_signature_separation_rad": min_delta,
        "minimum_target_signature_separation_deg": min_delta * 180.0 / pi,
        "minimum_target_separation_arg": delta_arg,
        "conservative_image_separation_lower_bound_rad": min_lower,
        "conservative_lower_bound_arg": lower_arg,
        "certificate_pass": bool(min_lower > 0.0),
    }


def m0_circle_counterexample(receiver: int, coordinates: dict[int, np.ndarray]) -> dict:
    """Produce another point on the same 01 constant-angle arc, deterministically."""
    x = coordinates[receiver]
    a, b = coordinates[0], coordinates[1]
    theta = raw_angle(x, a, b)
    # Circumcenter of A,B,x; receiver targets are noncollinear with FY00/FY01.
    system = 2.0 * np.vstack((b - a, x - a))
    rhs = np.array((np.dot(b, b) - np.dot(a, a), np.dot(x, x) - np.dot(a, a)))
    center = np.linalg.solve(system, rhs)
    radius = float(np.linalg.norm(x - center))
    vector = x - center
    for rotation in (0.05, -0.05, 0.12, -0.12):
        matrix = np.array([[np.cos(rotation), -np.sin(rotation)], [np.sin(rotation), np.cos(rotation)]])
        other = center + matrix @ vector
        if np.linalg.norm(other - x) > 1e-4 and abs(raw_angle(other, a, b) - theta) < 1e-10:
            return {
                "receiver": receiver,
                "observed_angle_rad": theta,
                "target_point": x.tolist(),
                "alternative_point": other.tolist(),
                "alternative_angle_residual": raw_angle(other, a, b) - theta,
                "counterexample_pass": True,
            }
    raise RuntimeError("failed to sample the known m=0 constant-angle arc")
