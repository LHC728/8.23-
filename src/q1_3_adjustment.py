"""Q1(3) strict-local adjustment core.

The online controller receives only a callable returning its *own* angle
residual after a local probe.  Table-1 coordinates live in the simulator and
evaluator only; they are deliberately not fields of the controller.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, pi, sin, sqrt
from typing import Callable, Sequence

import numpy as np

from src.q1_1_geometry import analytic_angle_gradient, raw_angle
from src.q1_2_identity import target_coordinates

O, A, B, C = 0, 1, 4, 7
RADIUS = 100.0
TARGET_ANGLE = pi / 6.0


def table1_coordinates() -> dict[int, np.ndarray]:
    """The supplied table; callers must use it only for simulation/evaluation."""
    polar = {0: (0.0, 0.0), 1: (100.0, 0.0), 2: (98.0, 40.10), 3: (112.0, 80.21),
             4: (105.0, 119.75), 5: (98.0, 159.86), 6: (112.0, 199.96),
             7: (105.0, 240.07), 8: (98.0, 280.17), 9: (112.0, 320.28)}
    return {i: r * np.array((cos(deg * pi / 180.0), sin(deg * pi / 180.0))) for i, (r, deg) in polar.items()}


def transform_positions(points: dict[int, np.ndarray], matrix: np.ndarray) -> dict[int, np.ndarray]:
    return {key: matrix @ value for key, value in points.items()}


def local_residual(point: np.ndarray, transmitters: Sequence[np.ndarray], target_angles: Sequence[float]) -> np.ndarray:
    """Own receiver angle residual, based on frozen Q1(1) raw atan2 semantics."""
    a, b, c = transmitters
    return np.array((raw_angle(point, a, b) - target_angles[0], raw_angle(point, a, c) - target_angles[1]))


def bc_residual_b(point: np.ndarray, c_point: np.ndarray, origin: np.ndarray, a_point: np.ndarray) -> np.ndarray:
    return local_residual(point, (origin, a_point, c_point), (TARGET_ANGLE, TARGET_ANGLE))


def bc_residual_c(point: np.ndarray, b_point: np.ndarray, origin: np.ndarray, a_point: np.ndarray) -> np.ndarray:
    return local_residual(point, (origin, a_point, b_point), (TARGET_ANGLE, TARGET_ANGLE))


@dataclass(frozen=True)
class ControllerSettings:
    delta: float = 0.02
    eta: float = 0.85
    damping: float = 1e-8
    step_cap: float = 12.0
    inner_steps: int = 18
    residual_tolerance: float = 1e-9


@dataclass
class ControllerTrace:
    point: np.ndarray
    residual_norms: list[float]
    probes: int
    backtracks: int
    status: str


Measure = Callable[[np.ndarray], np.ndarray]


def finite_difference_controller(start: np.ndarray, measure: Measure, *, settings: ControllerSettings, axes: np.ndarray | None = None) -> ControllerTrace:
    """Damped local controller; it never receives transmitter or truth coordinates."""
    point = np.asarray(start, dtype=float).copy()
    axes = np.eye(2) if axes is None else np.asarray(axes, dtype=float)
    norms: list[float] = []
    probes = backtracks = 0
    for _ in range(settings.inner_steps):
        residual = np.asarray(measure(point), dtype=float)
        norm = float(np.linalg.norm(residual))
        norms.append(norm)
        if norm <= settings.residual_tolerance:
            return ControllerTrace(point, norms, probes, backtracks, "CONVERGED")
        jacobian = np.empty((2, 2))
        for column in range(2):
            direction = axes[:, column]
            plus = np.asarray(measure(point + settings.delta * direction), dtype=float)
            minus = np.asarray(measure(point - settings.delta * direction), dtype=float)
            probes += 2
            jacobian[:, column] = (plus - minus) / (2.0 * settings.delta)
        delta_local = -settings.eta * np.linalg.solve(jacobian.T @ jacobian + settings.damping * np.eye(2), jacobian.T @ residual)
        step = axes @ delta_local
        step_norm = float(np.linalg.norm(step))
        if step_norm > settings.step_cap:
            step *= settings.step_cap / step_norm
        accepted = False
        for factor in (1.0, 0.5, 0.25, 0.125, 0.0625):
            proposal = point + factor * step
            if float(np.linalg.norm(measure(proposal))) < norm:
                point = proposal
                accepted = True
                break
            backtracks += 1
        if not accepted:
            return ControllerTrace(point, norms, probes, backtracks, "BACKTRACK_REJECTED")
    norms.append(float(np.linalg.norm(measure(point))))
    return ControllerTrace(point, norms, probes, backtracks, "MAX_INNER_STEPS")


def exact_local_best_response(start: np.ndarray, measure: Measure, *, target_slot: np.ndarray, axes: np.ndarray | None = None) -> ControllerTrace:
    """Offline exact-root oracle: same local measurement interface, target-near branch."""
    trace = finite_difference_controller(start, measure, settings=ControllerSettings(delta=1e-3, eta=1.0, damping=1e-12, step_cap=40.0, inner_steps=45, residual_tolerance=1e-12), axes=axes)
    # This oracle deliberately selects only the preloaded target-near local branch.
    if np.linalg.norm(trace.point - target_slot) > 30.0:
        return ControllerTrace(trace.point, trace.residual_norms, trace.probes, trace.backtracks, "TARGET_NEAR_BRANCH_REJECTED")
    return trace


def _bearing_gradient(vector: np.ndarray) -> np.ndarray:
    return np.array((-vector[1], vector[0])) / float(np.dot(vector, vector))


def angle_partials(receiver: np.ndarray, left: np.ndarray, right: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Independent manual partial derivatives of raw atan2 angle (receiver,left,right)."""
    u, v = left - receiver, right - receiver
    sign = 1.0 if float(u[0] * v[1] - u[1] * v[0]) > 0 else -1.0
    left_grad = -sign * _bearing_gradient(u)
    right_grad = sign * _bearing_gradient(v)
    return -(left_grad + right_grad), left_grad, right_grad


def analytic_bc_blocks() -> dict[str, np.ndarray]:
    """Derive, rather than insert, the four frozen target Jacobian blocks."""
    q = target_coordinates()
    b, c, o, a = q[B], q[C], q[O], q[A]
    h_oa_b = angle_partials(b, o, a)[0]
    h_oc_b, _, h_oc_c = angle_partials(b, o, c)
    h_oa_c = angle_partials(c, o, a)[0]
    h_ob_c, _, h_ob_b = angle_partials(c, o, b)
    return {"D_B_f_B": np.vstack((h_oa_b, h_oc_b)), "D_C_f_B": np.vstack((np.zeros(2), h_oc_c)),
            "D_C_f_C": np.vstack((h_oa_c, h_ob_c)), "D_B_f_C": np.vstack((np.zeros(2), h_ob_b))}


@dataclass
class Dual:
    value: float
    derivative: np.ndarray

    def __add__(self, other):
        other = _dual(other, len(self.derivative)); return Dual(self.value + other.value, self.derivative + other.derivative)
    __radd__ = __add__
    def __sub__(self, other):
        other = _dual(other, len(self.derivative)); return Dual(self.value - other.value, self.derivative - other.derivative)
    def __rsub__(self, other): return _dual(other, len(self.derivative)).__sub__(self)
    def __mul__(self, other):
        other = _dual(other, len(self.derivative)); return Dual(self.value * other.value, self.derivative * other.value + other.derivative * self.value)
    __rmul__ = __mul__


def _dual(value, n: int) -> Dual:
    return value if isinstance(value, Dual) else Dual(float(value), np.zeros(n))


def _ad_angle(receiver: list[Dual], left: list[Dual], right: list[Dual]) -> Dual:
    u = [left[i] - receiver[i] for i in range(2)]; v = [right[i] - receiver[i] for i in range(2)]
    cross = u[0] * v[1] - u[1] * v[0]; dot = u[0] * v[0] + u[1] * v[1]
    absolute = 1.0 if cross.value > 0 else -1.0
    value = atan2(abs(cross.value), dot.value)
    derivative = (dot.value * absolute * cross.derivative - abs(cross.value) * dot.derivative) / (dot.value ** 2 + cross.value ** 2)
    return Dual(value, derivative)


def automatic_bc_blocks() -> dict[str, np.ndarray]:
    """Forward automatic differentiation independent of manual partial formulas."""
    q = target_coordinates(); n = 4
    def variables(point: np.ndarray, base: int) -> list[Dual]:
        return [Dual(float(point[i]), np.eye(n)[base + i]) for i in range(2)]
    const = lambda point: [Dual(float(v), np.zeros(n)) for v in point]
    b, c, o, a = variables(q[B], 0), variables(q[C], 2), const(q[O]), const(q[A])
    fb1, fb2 = _ad_angle(b, o, a), _ad_angle(b, o, c)
    fc1, fc2 = _ad_angle(c, o, a), _ad_angle(c, o, b)
    return {"D_B_f_B": np.vstack((fb1.derivative[:2], fb2.derivative[:2])), "D_C_f_B": np.vstack((fb1.derivative[2:], fb2.derivative[2:])),
            "D_C_f_C": np.vstack((fc1.derivative[2:], fc2.derivative[2:])), "D_B_f_C": np.vstack((fc1.derivative[:2], fc2.derivative[:2]))}


def finite_difference_bc_blocks(step: float = 1e-4) -> dict[str, np.ndarray]:
    q = target_coordinates(); b, c, o, a = q[B].copy(), q[C].copy(), q[O], q[A]
    def diff(fn, variable: str) -> np.ndarray:
        matrix = np.empty((2, 2))
        for j in range(2):
            d = np.zeros(2); d[j] = step
            if variable == "b": matrix[:, j] = (fn(b + d, c) - fn(b - d, c)) / (2 * step)
            else: matrix[:, j] = (fn(b, c + d) - fn(b, c - d)) / (2 * step)
        return matrix
    fb = lambda bb, cc: bc_residual_b(bb, cc, o, a); fc = lambda bb, cc: bc_residual_c(cc, bb, o, a)
    return {"D_B_f_B": diff(fb, "b"), "D_C_f_B": diff(fb, "c"), "D_C_f_C": diff(fc, "c"), "D_B_f_C": diff(fc, "b")}


def derivative_audit() -> dict:
    analytic, automatic, finite = analytic_bc_blocks(), automatic_bc_blocks(), finite_difference_bc_blocks()
    expected_a = 1.0 / (100.0 * sqrt(3.0))
    expected = {"D_B_f_B": np.array(((expected_a, 0.0), (-expected_a/2, -1/200))),
                "D_C_f_B": np.array(((0.0, 0.0), (-expected_a, 0.0))),
                "D_C_f_C": np.array(((expected_a, 0.0), (-expected_a/2, 1/200))),
                "D_B_f_C": np.array(((0.0, 0.0), (-expected_a, 0.0)))}
    errors = {name: {"expected": float(np.max(np.abs(analytic[name]-expected[name]))), "automatic": float(np.max(np.abs(analytic[name]-automatic[name]))), "finite_difference": float(np.max(np.abs(analytic[name]-finite[name])))} for name in expected}
    db, dc = analytic["D_B_f_B"], analytic["D_C_f_B"]
    cb, cc = analytic["D_B_f_C"], analytic["D_C_f_C"]
    response_b_c, response_c_b = -np.linalg.solve(db, dc), -np.linalg.solve(cc, cb)
    product = response_c_b @ response_b_c
    joint = np.block([[db, dc], [cb, cc]])
    singular = np.linalg.svd(joint, compute_uv=False)
    return {"blocks": {key: analytic[key].tolist() for key in analytic}, "errors": errors,
            "response_B_wrt_C": response_b_c.tolist(), "response_C_wrt_B": response_c_b.tolist(),
            "cycle_product": product.tolist(), "spectral_radius": float(max(abs(np.linalg.eigvals(product)))),
            "joint_abs_det": abs(float(np.linalg.det(joint))), "joint_sigma_min": float(singular[-1]), "joint_condition": float(singular[0]/singular[-1]),
            "pass": all(max(values.values()) < 2e-6 for values in errors.values()) and float(max(abs(np.linalg.eigvals(product)))) < 1e-10}


def follower_metrics() -> dict:
    q = target_coordinates(); groups = {2:(O,A,B), 3:(O,A,B), 5:(O,B,C), 6:(O,B,C), 8:(O,A,C), 9:(O,A,C)}
    minimum, maximum, details = float("inf"), 0.0, {}
    for receiver, ids in groups.items():
        jac = np.vstack((analytic_angle_gradient(q[receiver], q[ids[0]], q[ids[1]]), analytic_angle_gradient(q[receiver], q[ids[0]], q[ids[2]])))
        sv = np.linalg.svd(jac, compute_uv=False); minimum, maximum = min(minimum, float(sv[-1])), max(maximum, float(sv[0]/sv[-1]))
        details[str(receiver)] = {"sigma_min": float(sv[-1]), "condition": float(sv[0]/sv[-1])}
    return {"per_receiver": details, "worst_sigma_min": minimum, "max_condition": maximum, "pass": minimum > 0.0}


def schedule_is_legal() -> bool:
    return all(len(transmitters) <= 4 and O in transmitters for transmitters in ((O,A,C), (O,A,B), (O,A,B,C)))
