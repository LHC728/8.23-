"""Q1(1) complete local-angle candidate generator and independent oracle.

This module is deliberately offline verification code.  Its decision-facing
interface receives only one receiver's local angle signature and the labelled
transmitter geometry; it never reads angles measured by another receiver.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from math import atan2, pi, sin, cos, sqrt
from typing import Iterable, Sequence

import numpy as np


ANGLE_NAMES = ("ab", "ac", "bc")
ANGLE_PAIRS = {"ab": (0, 1), "ac": (0, 2), "bc": (1, 2)}


@dataclass(frozen=True)
class Circle:
    center: np.ndarray
    radius: float
    source_angle: str
    side: int


@dataclass
class Candidate:
    point: np.ndarray
    primary_angles: tuple[str, str]
    residuals: np.ndarray
    sources: list[tuple[tuple[str, str], int, int]] = field(default_factory=list)


@dataclass
class CandidateReport:
    candidates: list[Candidate]
    status: set[str]
    tangent_events: int
    coincident_circle_events: int
    rejected_intersections: int


@dataclass
class RootReport:
    roots: list[np.ndarray]
    status: set[str]
    attempts: int


def as_point(value: Sequence[float]) -> np.ndarray:
    point = np.asarray(value, dtype=float)
    if point.shape != (2,):
        raise ValueError("every planar point must have shape (2,)")
    return point


def raw_angle(x: Sequence[float], a: Sequence[float], b: Sequence[float]) -> float:
    """Stable unsigned angle in [0, pi] using the frozen atan2 definition."""
    x, a, b = as_point(x), as_point(a), as_point(b)
    u, v = a - x, b - x
    return atan2(abs(float(u[0] * v[1] - u[1] * v[0])), float(np.dot(u, v)))


def angle_signature(x: Sequence[float], transmitters: Sequence[Sequence[float]]) -> np.ndarray:
    a, b, c = (as_point(p) for p in transmitters)
    return np.array([raw_angle(x, a, b), raw_angle(x, a, c), raw_angle(x, b, c)])


def _circle_branches(
    a: np.ndarray,
    b: np.ndarray,
    theta: float,
    name: str,
    *,
    boundary_eps: float,
) -> tuple[list[Circle], set[str]]:
    flags: set[str] = set()
    chord = float(np.linalg.norm(b - a))
    if chord <= boundary_eps:
        return [], {f"coincident_transmitters:{name}"}
    if theta <= boundary_eps or theta >= pi - boundary_eps:
        return [], {f"angle_boundary:{name}"}

    radius = chord / (2.0 * sin(theta))
    offset = radius * abs(cos(theta))
    midpoint = (a + b) / 2.0
    tangent = (b - a) / chord
    normal = np.array([-tangent[1], tangent[0]])
    if offset <= boundary_eps:
        flags.add(f"merged_circle_centers:{name}")
        return [Circle(midpoint, radius, name, 0)], flags
    return [
        Circle(midpoint + offset * normal, radius, name, +1),
        Circle(midpoint - offset * normal, radius, name, -1),
    ], flags


def circle_intersections(c1: Circle, c2: Circle, *, tol: float = 1e-9) -> tuple[list[np.ndarray], str]:
    """Return all circle intersections, including explicit tangent/coincident states."""
    dvec = c2.center - c1.center
    distance = float(np.linalg.norm(dvec))
    r1, r2 = c1.radius, c2.radius
    scale = max(1.0, r1, r2, distance)
    eps = tol * scale
    if distance <= eps:
        if abs(r1 - r2) <= eps:
            return [], "coincident"
        return [], "concentric_disjoint"
    if distance > r1 + r2 + eps or distance < abs(r1 - r2) - eps:
        return [], "disjoint"

    along = (r1 * r1 - r2 * r2 + distance * distance) / (2.0 * distance)
    height_sq = r1 * r1 - along * along
    if height_sq < -eps * max(1.0, r1 * r1):
        return [], "disjoint"
    base = c1.center + along * dvec / distance
    if abs(height_sq) <= eps * max(1.0, r1 * r1):
        return [base], "tangent"
    height = sqrt(max(0.0, height_sq))
    perpendicular = np.array([-dvec[1], dvec[0]]) / distance
    return [base + height * perpendicular, base - height * perpendicular], "two_points"


def _deduplicate(points: Iterable[Candidate], *, tol: float) -> list[Candidate]:
    kept: list[Candidate] = []
    for item in points:
        for prior in kept:
            if np.linalg.norm(item.point - prior.point) <= tol:
                prior.sources.extend(item.sources)
                break
        else:
            kept.append(item)
    return kept


def complete_candidates(
    transmitters: Sequence[Sequence[float]],
    observed_angles: Sequence[float],
    *,
    angle_tol: float = 1e-8,
    geometry_tol: float = 1e-9,
    boundary_eps: float = 1e-6,
    near_boundary_eps: float = 1e-3,
) -> CandidateReport:
    """Enumerate all two-circle branches and use the remaining angle as holdout.

    Every pair among {ab, ac, bc} is used once as the two independent
    constraints.  Thus a boundary/ill-conditioned pair cannot silently erase a
    valid branch available from another pair.  Every retained point is then
    checked against *all three* original atan2 angles.
    """
    tx = tuple(as_point(p) for p in transmitters)
    y = np.asarray(observed_angles, dtype=float)
    if len(tx) != 3 or y.shape != (3,):
        raise ValueError("Q1(1) requires exactly three transmitters and three angles")
    if not np.all(np.isfinite(y)) or np.any(y < -angle_tol) or np.any(y > pi + angle_tol):
        raise ValueError("observed unsigned angles must be finite and in [0, pi]")

    status: set[str] = set()
    # Exact 0/pi data describe the singular collinear set.  They are not fed to
    # ordinary finite-circle intersection or smooth-Jacobian certification.
    if np.any(y <= boundary_eps) or np.any(y >= pi - boundary_eps):
        status.update({"angle_near_0_or_pi", "boundary_input_safely_rejected", "no_certified_finite_candidate"})
        return CandidateReport([], status, 0, 0, 0)

    circles: dict[str, list[Circle]] = {}
    for name, theta in zip(ANGLE_NAMES, y):
        i, j = ANGLE_PAIRS[name]
        circles[name], flags = _circle_branches(tx[i], tx[j], float(theta), name, boundary_eps=boundary_eps)
        status.update(flags)

    raw_candidates: list[Candidate] = []
    tangent_events = coincident_events = rejected = 0
    transmitter_tol = geometry_tol * max(1.0, *(np.linalg.norm(p) for p in tx))
    for name1, name2 in combinations(ANGLE_NAMES, 2):
        if not circles[name1] or not circles[name2]:
            status.add(f"unusable_primary_pair:{name1}_{name2}")
            continue
        holdout = next(name for name in ANGLE_NAMES if name not in (name1, name2))
        for c1 in circles[name1]:
            for c2 in circles[name2]:
                points, relation = circle_intersections(c1, c2, tol=geometry_tol)
                if relation == "tangent":
                    tangent_events += 1
                    status.add("tangent_circle_intersection")
                elif relation == "coincident":
                    coincident_events += 1
                    status.add("coincident_constraint_circles")
                for point in points:
                    if any(np.linalg.norm(point - t) <= transmitter_tol for t in tx):
                        rejected += 1
                        status.add("transmitter_receiver_coincidence_rejected")
                        continue
                    residuals = angle_signature(point, tx) - y
                    if np.max(np.abs(residuals)) <= angle_tol:
                        raw_candidates.append(
                            Candidate(
                                point=point,
                                primary_angles=(name1, name2),
                                residuals=residuals,
                                sources=[((name1, name2), c1.side, c2.side)],
                            )
                        )
                    else:
                        rejected += 1
                        status.add(f"atan2_holdout_or_arc_rejected:{holdout}")

    result = _deduplicate(raw_candidates, tol=max(geometry_tol * 50.0, angle_tol * 10.0))
    if not result:
        status.add("no_certified_finite_candidate")
    elif len(result) > 1:
        status.add("multiple_candidates_retained")
    if np.any(y <= near_boundary_eps) or np.any(y >= pi - near_boundary_eps):
        status.add("angle_near_0_or_pi")
    return CandidateReport(result, status, tangent_events, coincident_events, rejected)


def analytic_angle_gradient(x: Sequence[float], a: Sequence[float], b: Sequence[float], *, eps: float = 1e-12) -> np.ndarray:
    """Gradient of the unsigned atan2 angle away from the 0/pi singular set."""
    x, a, b = as_point(x), as_point(a), as_point(b)
    u, v = a - x, b - x
    cross = float(u[0] * v[1] - u[1] * v[0])
    dot = float(np.dot(u, v))
    denom = cross * cross + dot * dot
    if abs(cross) <= eps or denom <= eps:
        raise ValueError("angle Jacobian is singular or nondifferentiable at 0/pi")
    grad_cross = np.array([a[1] - b[1], b[0] - a[0]])
    grad_dot = -(u + v)
    return np.sign(cross) * (dot * grad_cross - cross * grad_dot) / denom


def angle_jacobian(
    x: Sequence[float], transmitters: Sequence[Sequence[float]], names: tuple[str, str] = ("ab", "ac")
) -> np.ndarray:
    tx = tuple(as_point(p) for p in transmitters)
    return np.vstack([analytic_angle_gradient(x, tx[ANGLE_PAIRS[name][0]], tx[ANGLE_PAIRS[name][1]]) for name in names])


def rank_certificate(
    x: Sequence[float], transmitters: Sequence[Sequence[float]], names: tuple[str, str], *, rank_tol: float = 1e-9
) -> dict[str, float | int | bool]:
    jacobian = angle_jacobian(x, transmitters, names)
    singular_values = np.linalg.svd(jacobian, compute_uv=False)
    rank = int(np.sum(singular_values > rank_tol))
    condition = float(singular_values[0] / singular_values[-1]) if singular_values[-1] > 0 else float("inf")
    return {
        "rank": rank,
        "sigma_min": float(singular_values[-1]),
        "sigma_max": float(singular_values[0]),
        "condition_number": condition,
        "full_rank": bool(rank == 2),
    }


def _finite_difference_jacobian(x: np.ndarray, tx: tuple[np.ndarray, ...], names: tuple[str, str], step: float) -> np.ndarray:
    matrix = np.empty((2, 2), dtype=float)
    for column in range(2):
        delta = np.zeros(2)
        delta[column] = step
        plus = angle_signature(x + delta, tx)
        minus = angle_signature(x - delta, tx)
        matrix[:, column] = [(plus[ANGLE_NAMES.index(name)] - minus[ANGLE_NAMES.index(name)]) / (2.0 * step) for name in names]
    return matrix


def independent_multistart_checker(
    transmitters: Sequence[Sequence[float]],
    observed_angles: Sequence[float],
    *,
    starts_per_axis: int = 13,
    max_iterations: int = 100,
    root_tol: float = 2e-8,
    finite_difference_step: float = 1e-5,
) -> RootReport:
    """Independent numerical multi-root search; it intentionally does not use circles."""
    tx = tuple(as_point(p) for p in transmitters)
    y = np.asarray(observed_angles, dtype=float)
    status: set[str] = set()
    if np.any(y <= 1e-8) or np.any(y >= pi - 1e-8):
        return RootReport([], {"checker_boundary_angle_safely_rejected"}, 0)
    centroid = np.mean(np.vstack(tx), axis=0)
    span = max(1.0, max(float(np.linalg.norm(p - centroid)) for p in tx))
    roots: list[np.ndarray] = []
    attempts = 0

    for names in combinations(ANGLE_NAMES, 2):
        holdout_index = ANGLE_NAMES.index(next(name for name in ANGLE_NAMES if name not in names))
        for multiplier in (1.0, 3.0, 10.0, 30.0):
            axis = np.linspace(-multiplier * span, multiplier * span, starts_per_axis)
            for dx in axis:
                for dy in axis:
                    attempts += 1
                    x = centroid + np.array([dx, dy])
                    damping = 1e-5
                    for _ in range(max_iterations):
                        signature = angle_signature(x, tx)
                        residual = np.array([signature[ANGLE_NAMES.index(name)] - y[ANGLE_NAMES.index(name)] for name in names])
                        if np.linalg.norm(residual, ord=np.inf) < root_tol:
                            break
                        try:
                            jacobian = _finite_difference_jacobian(x, tx, names, finite_difference_step)
                        except FloatingPointError:
                            break
                        normal = jacobian.T @ jacobian + damping * np.eye(2)
                        step = -np.linalg.solve(normal, jacobian.T @ residual)
                        if not np.all(np.isfinite(step)):
                            break
                        accepted = False
                        current_norm = float(np.linalg.norm(residual))
                        for factor in (1.0, 0.5, 0.25, 0.125, 0.0625):
                            proposal = x + factor * step
                            proposal_signature = angle_signature(proposal, tx)
                            proposal_residual = np.array([proposal_signature[ANGLE_NAMES.index(name)] - y[ANGLE_NAMES.index(name)] for name in names])
                            if float(np.linalg.norm(proposal_residual)) < current_norm:
                                x = proposal
                                damping = max(damping / 3.0, 1e-12)
                                accepted = True
                                break
                        if not accepted:
                            damping *= 10.0
                            if damping > 1e10:
                                break
                    final_residuals = angle_signature(x, tx) - y
                    if np.max(np.abs(final_residuals)) <= root_tol:
                        if all(np.linalg.norm(x - existing) > 2e-5 for existing in roots):
                            roots.append(x)
        if not roots:
            status.add(f"no_root_from_primary_pair:{names[0]}_{names[1]}")
        elif any(abs(angle_signature(root, tx)[holdout_index] - y[holdout_index]) > root_tol for root in roots):
            status.add("checker_holdout_rejection")
    if len(roots) > 1:
        status.add("checker_multiple_roots")
    if not roots:
        status.add("checker_no_root")
    return RootReport(roots, status, attempts)
