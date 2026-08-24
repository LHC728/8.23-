"""Q2 的生产几何内核：参数化格点、本机无符号角和完整四参考候选。"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import atan2, pi, sqrt

import numpy as np

FOUR_REFERENCE_IDS = (3, 4, 11, 15)
FOUR_PAIRS = tuple(combinations(range(4), 2))


def target_lattice(d_star: float = 1.0) -> dict[int, np.ndarray]:
    if d_star <= 0:
        raise ValueError("d_star must be positive")
    return {
        1 + c * (c + 1) // 2 + j: d_star * np.array([-sqrt(3.0) * c / 2.0, j - c / 2.0])
        for c in range(5) for j in range(c + 1)
    }


def raw_angle(point: np.ndarray, left: np.ndarray, right: np.ndarray) -> float:
    u, v = np.asarray(left) - point, np.asarray(right) - point
    return float(atan2(abs(float(u[0] * v[1] - u[1] * v[0])), float(u @ v)))


def four_angles(point: np.ndarray, anchors: np.ndarray) -> np.ndarray:
    return np.array([raw_angle(point, anchors[i], anchors[j]) for i, j in FOUR_PAIRS])


def angle_gradient_receiver(point: np.ndarray, left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """0/pi 以外 h_ab 对接收机位置的解析导数。"""
    u, v = left - point, right - point
    cross, dot = float(u[0] * v[1] - u[1] * v[0]), float(u @ v)
    denom = cross * cross + dot * dot
    if abs(cross) < 1e-12 or denom < 1e-18:
        raise ValueError("boundary or collision angle")
    grad_cross = np.array([u[1] - v[1], v[0] - u[0]])
    grad_dot = -u - v
    return np.sign(cross) * (dot * grad_cross - cross * grad_dot) / denom


def angle_gradient_transmitter(point: np.ndarray, left: np.ndarray, right: np.ndarray, *, moving: str) -> np.ndarray:
    """0/pi 以外 h_ab 对指定发射机坐标的解析导数。"""
    u, v = left - point, right - point
    cross, dot = float(u[0] * v[1] - u[1] * v[0]), float(u @ v)
    denom = cross * cross + dot * dot
    if abs(cross) < 1e-12 or denom < 1e-18:
        raise ValueError("boundary or collision angle")
    if moving == "left":
        grad_cross, grad_dot = np.array([v[1], -v[0]]), v
    elif moving == "right":
        grad_cross, grad_dot = np.array([-u[1], u[0]]), u
    else:
        raise ValueError("moving must be left or right")
    return np.sign(cross) * (dot * grad_cross - cross * grad_dot) / denom


def angle_jacobian(point: np.ndarray, anchors: np.ndarray, indices: tuple[int, ...]) -> np.ndarray:
    return np.vstack([angle_gradient_receiver(point, anchors[i], anchors[j]) for i, j in (FOUR_PAIRS[k] for k in indices)])


@dataclass(frozen=True)
class Circle:
    center: np.ndarray
    radius: float


def angle_circles(left: np.ndarray, right: np.ndarray, theta: float, boundary_eps: float = 1e-8) -> list[Circle]:
    chord = np.asarray(right) - left
    length = float(np.linalg.norm(chord))
    if length <= boundary_eps:
        raise ValueError("coincident transmitters")
    if not boundary_eps < theta < pi - boundary_eps:
        return []
    midpoint = (np.asarray(left) + right) / 2.0
    normal = np.array([-chord[1], chord[0]]) / length
    radius = length / (2.0 * np.sin(theta))
    offset = length / (2.0 * np.tan(theta))
    return [Circle(midpoint + normal * offset, radius), Circle(midpoint - normal * offset, radius)]


def circle_intersections(left: Circle, right: Circle, tol: float = 1e-10) -> tuple[list[np.ndarray], str]:
    delta = right.center - left.center
    distance = float(np.linalg.norm(delta))
    if distance <= tol and abs(left.radius - right.radius) <= tol:
        return [], "coincident"
    if distance <= tol or distance > left.radius + right.radius + tol or distance < abs(left.radius - right.radius) - tol:
        return [], "disjoint"
    a = (left.radius**2 - right.radius**2 + distance**2) / (2.0 * distance)
    h2 = max(0.0, left.radius**2 - a**2)
    base = left.center + a * delta / distance
    if h2 <= tol**2:
        return [base], "tangent"
    offset = sqrt(h2) * np.array([-delta[1], delta[0]]) / distance
    return [base + offset, base - offset], "secant"


def _dedupe(points: list[np.ndarray], tol: float = 2e-7) -> list[np.ndarray]:
    answer: list[np.ndarray] = []
    for point in points:
        if not any(float(np.linalg.norm(point - known)) <= tol for known in answer):
            answer.append(point)
    return answer


def complete_four_reference_candidates(
    anchors: np.ndarray, observed: np.ndarray, *, angle_tol: float = 3e-8, boundary_eps: float = 1e-7
) -> dict[str, object]:
    """完整枚举双侧圆分支及全部有限圆交点，绝不默认首根。"""
    anchors, observed = np.asarray(anchors, dtype=float), np.asarray(observed, dtype=float)
    if anchors.shape != (4, 2) or observed.shape != (6,):
        raise ValueError("four anchors and six angles are required")
    active = [k for k, angle in enumerate(observed) if boundary_eps < angle < pi - boundary_eps]
    boundary = [k for k in range(6) if k not in active]
    circles = {k: angle_circles(anchors[i], anchors[j], float(observed[k])) for k, (i, j) in enumerate(FOUR_PAIRS) if k in active}
    coincident, tangent, continuous, rejected = 0, 0, False, 0
    roots: list[np.ndarray] = []
    for first, second in combinations(active, 2):
        for c1 in circles[first]:
            for c2 in circles[second]:
                points, state = circle_intersections(c1, c2)
                coincident += int(state == "coincident")
                tangent += int(state == "tangent")
                for point in points:
                    if min(float(np.linalg.norm(point - anchor)) for anchor in anchors) < 1e-8:
                        rejected += 1; continue
                    residual = four_angles(point, anchors) - observed
                    if max(abs(float(residual[k])) for k in active) <= angle_tol:
                        roots.append(point)
                    else:
                        rejected += 1
    # 一个圆分支覆盖全部活动约束代表连续解族；不把它伪装为单根。
    for k in active:
        for circle in circles[k]:
            if all(any(np.linalg.norm(circle.center - other.center) < 2e-8 and abs(circle.radius-other.radius) < 2e-8 for other in circles[l]) for l in active):
                continuous = True
    roots = _dedupe(roots)
    status = "CANDIDATE" if roots and not continuous else "REJECTED"
    return {"roots": roots, "active_indices": active, "boundary_indices": boundary, "coincident_circle_events": coincident, "tangent_events": tangent, "continuous_solution_family": continuous, "rejected_intersections": rejected, "status": status}


def independent_multistart_roots(anchors: np.ndarray, observed: np.ndarray, *, tol: float = 2e-8) -> list[np.ndarray]:
    """独立的过定多初值 Gauss--Newton 复核器，不调用圆候选器。"""
    active = tuple(k for k, value in enumerate(observed) if 1e-7 < value < pi - 1e-7)
    center = np.mean(anchors, axis=0)
    span = max(1.0, float(np.max(np.linalg.norm(anchors-center, axis=1))))
    starts = [center + span * np.array([x, y]) for x in (-3,-1,0,1,3) for y in (-3,-1,0,1,3)]
    roots: list[np.ndarray] = []
    for point in starts:
        point = point.astype(float)
        for _ in range(80):
            try:
                residual = four_angles(point, anchors)[list(active)] - observed[list(active)]
                jac = angle_jacobian(point, anchors, active)
            except ValueError:
                break
            step = -np.linalg.solve(jac.T @ jac + 1e-10*np.eye(2), jac.T @ residual)
            point += np.clip(step, -0.5*span, 0.5*span)
            if float(np.max(np.abs(residual))) < tol:
                roots.append(point.copy()); break
    return _dedupe(roots, tol=2e-5)
