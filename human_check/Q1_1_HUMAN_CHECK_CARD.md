# Q1(1) Human Check Card

## Decision

```text
Q1_1_MINIMUM_GATE = PASS
SOL_DELEGATION = NO
```

## What was checked

| Check | Human-readable evidence | Verdict |
| --- | --- | --- |
| No first-root shortcut | Primary routine returns a set and preserves two reflected roots in the collinear example. | PASS |
| Two-sided constant-angle geometry | Each nonboundary transmitter pair supplies both circle-center branches; all three pairs of constraints are attempted. | PASS |
| Raw-angle consistency | Candidate is retained only when three original `atan2(abs(cross), dot)` values match. | PASS |
| Independent path | A multi-start, finite-difference Gauss-Newton checker does not use circle construction and returns the same roots in normal/mirror cases. | PASS |
| Tangency and coincidences | Tangency and merged/coincident branch states are status records; transmitter coincidence is rejected. | PASS |
| 0/pi singularity | Exact boundary inputs are safely rejected from ordinary finite-circle and smooth-Jacobian certification. | PASS |
| Local condition | Ideal target has rank 2 with `sigma_min = 0.53988258`; mirror roots each have rank 2 but remain globally ambiguous. | PASS |

## Interpretation guardrails

1. The mirror example demonstrates why rank two at an individual root does **not** imply global uniqueness.
2. A third local angle is a same-receiver branch/order holdout. It is not independent external evidence and is never sent to another UAV.
3. Near-boundary angles are flagged; exact `0/pi` values are rejected by the finite-candidate interface rather than silently treated as regular constraints.
4. The deterministic Gate verifies the code path and its declared failure semantics only. It does not certify a numerical local domain radius for every Q1 receiver; that is a Q1(2) task.

## Reproduce before relying on this result

```text
python -m tests.q1_1_minimum_gate
```

Inspect `results/q1_1/q1_1_minimum_gate.json`: all seven case entries and every boolean in `requirements_checked` must be `true`.
