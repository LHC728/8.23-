# Q1(1) Model Contract

## Scope and information firewall

This contract implements only Q1(1). A receiver-local call takes labelled ideal transmitter coordinates `(q_a, q_b, q_c)`, the receiver identifier, and that receiver's three raw unsigned angles `(y_ab, y_ac, y_bc)`. The solver neither receives nor exchanges any angle observed by another receiver. Coordinates are proof, simulation, and offline-evaluation quantities only; no truth coordinate is an online input.

## Frozen mathematical map

For receiver position `x`, the raw observation is

\[
h_{ij}(x)=\operatorname{atan2}(|(q_i-x)\times(q_j-x)|,(q_i-x)^\mathsf T(q_j-x))\in[0,\pi].
\]

For each nonboundary angle `0 < theta < pi`, construct both circle-center branches for its transmitter chord:

\[
\rho=\frac{\|A-B\|}{2\sin\theta},\qquad
d_\perp=\rho|\cos\theta|.
\]

The primary implementation enumerates every pair among `ab`, `ac`, and `bc`, intersects every pair of their circle branches, removes receiver/transmitter coincidences and duplicate intersections, and retains a point only after all three original `atan2` angles are re-evaluated. The unused angle is therefore a branch/order holdout for each primary pair. No first numerical root is treated as unique.

Boundary angles `0/pi`, merged centers, coincident circles, tangencies, transmitter/receiver coincidence, and near-boundary angles are explicit status outputs. Certification requires exactly one candidate in the receiver's local slot domain and a full-rank local Jacobian; this minimum Gate only establishes candidate completeness and local rank, not global uniqueness.

## Independent oracle

The checker uses deterministic multi-start damped Gauss-Newton on each two-angle residual pair, with finite-difference Jacobians and full three-angle `atan2` validation. It intentionally uses no circle construction. Agreement means same finite retained root set within tolerance; it is implementation cross-checking, not external validation.

## Local rank

Away from `0/pi`, for signed cross product `s=(A-x)\times(B-x)` and dot product `d=(A-x)^\mathsf T(B-x)`,

\[
\nabla h_{AB}(x)=\operatorname{sign}(s)\,
\frac{d\nabla s-s\nabla d}{d^2+s^2},\quad
\nabla s=(A_y-B_y,B_x-A_x),\quad
\nabla d=-[(A-x)+(B-x)].
\]

The two selected primary rows form `DG(x)`. Its singular values, rank, and condition number are reported at the known target in deterministic tests.
