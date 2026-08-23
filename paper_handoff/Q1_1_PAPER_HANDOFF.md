# Q1(1) Paper Handoff

## 1. One-sentence direct answer

For a receiver observing the three pairwise unsigned angles from FY00 and two labelled, error-free peripheral transmitters, enumerate the two-sided constant-angle branches, retain only intersections that reproduce all raw local angles, and certify a local position only when the receiver's slot domain contains one full-rank candidate.

## 2. Role in the full problem

This is the geometric foundation for Q1(2): under any fixed identity hypothesis, Q1(1) returns all finite position candidates rather than concealing ambiguity with one numerical root. It contributes the common stable angle kernel, branch semantics, Jacobian interface, and reject interface used later; it does not determine the anonymous-identity minimum by itself.

## 3. Recommended narrative

Use an **evidence progression**:

1. The obstacle is that unsigned pairwise angles can have mirrored, tangent, or degenerate branches.
2. State the local `atan2` observation and the two-sided constant-angle circle construction.
3. Enumerate intersections using two constraints and use the third local angle as a same-source holdout.
4. State the local-rank condition and distinguish a local certificate from global uniqueness.
5. Report the deterministic branch/degeneracy checks.

## 4. Core mathematics

### MAIN_TEXT

- The raw unsigned angle `h_ab(x)=atan2(|(q_a-x)×(q_b-x)|,(q_a-x)^T(q_b-x))`.
- The constant-angle radius and signed-side center offset `rho=||A-B||/(2 sin theta)`, `d_perp=rho|cos theta|`.
- The set-valued candidate definition and the condition `rank DG(q_r)=2` for local regularity.
- One explicit sentence that every retained point is re-evaluated against all three original angles.

### APPENDIX

- Full analytic gradient formula.
- Arc/branch enumeration pseudocode, tolerances, duplicate rule, and complete deterministic case table.
- Multi-start checker settings and all status flags.

### OMIT

- Internal debugging iterations and rejected Newton trajectories.
- Any wording that suggests a generic numerical solver creates uniqueness.

## 5. Result package

- Main table: the seven deterministic cases from `q1_1_minimum_gate.json`, with expected branch behavior and pass/fail.
- Explanation figure: a single diagram of chord `AB`, its two circle centers, the retained intersection(s), and the mirror branch.
- High-value check: independent multi-start nonlinear roots agree with the geometric candidate set; exact `0/pi` inputs are explicitly rejected.

## 6. Evidence nature

- Internal consistency: all retained candidates pass three raw local-angle evaluations.
- Implementation cross-check: circle construction versus independent multi-start numerical roots.
- Boundary evidence: tangent, near-degenerate, and exact `0/pi` cases.
- Local mathematical condition: singular-value/rank calculation at known deterministic targets.
- External evidence: none.

## 7. Claim strength

### Can write

- “在精确、非退化且目标邻域内，模型返回全部有限候选；当编号槽位内仅保留一个满秩候选时，可作局部认证。”
- “镜像样例保留两个候选，说明模型不会将多根误写为唯一位置。”

### Must not write

- “三个夹角在全平面唯一定位。”
- “该方法对任意初始偏差均可定位。”
- “数值求解收敛因而得到全局唯一解。”
- “第三角是独立外部验证。”

## 8. Innovation / contribution

The relevant contribution is not a new solver: it is the explicit candidate-completeness and rejection layer that fixes the baseline weakness of silently selecting one root. Evidence is the two-sided enumeration, raw-angle revalidation, independent checker agreement, and preserved mirror roots.

## 9. Paragraph-level outline

1. Define the receiver-local geometry and the source of branch ambiguity.
2. Derive both constant-angle circle branches and the all-pairs intersection procedure.
3. Define raw-angle filtering, degenerate statuses, and the local rank certificate.
4. Present the deterministic case table and independent-checker agreement.
5. State local applicability and the interface passed to Q1(2).

## 10. Source interface

- Official result: `results/q1_1/Q1_1_OFFICIAL_RESULT.md`.
- Raw result: `results/q1_1/q1_1_minimum_gate.json`.
- Model contract: `model_contract/Q1_1_MODEL_CONTRACT.md`.
- Code: `src/q1_1_geometry.py`.
- Verification: `tests/q1_1_minimum_gate.py`.
- Writing reference: `writing_reference/SAFE_WRITING_GUIDE.md`.

## 11. Remaining writing risks

- Do not convert local full-rank regularity into a global uniqueness assertion.
- Do not describe same-receiver third-angle filtering as external validation.
- Generate the proposed geometry figure only from the formal case data, and keep it explanatory rather than presenting it as a flight test.
