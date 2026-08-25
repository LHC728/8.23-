# FINAL MODEL REVIEW

## 1. 当前程序审查结论

```text
FINAL_MODEL_REVIEW_PROGRAM_VERDICT = PASS_WITH_MINOR_FIX
FINAL_MAJOR_01_STATUS = REMEDIATED_AND_CLOSED
Q2_END_TO_END_WORK_REAUDIT = PASS
Q2_END_TO_END_GATE = PASS
FATAL_MODEL_MISMATCH = NO
REOPEN_REQUIRED = NO
FINAL_MODEL_REVIEW_HUMAN_VERDICT = PASS
FINAL_MODEL_FREEZE = PASS
```

Work 已复审 Q2 端到端验证器修复：实际有限步 FY04/FY03 建锚终点已传入 11 架跟随者控制，实际 15 节点终态已验收 30 条边与 12 条最大直线，锚点重置与终态几何扰动负对照均可失败。因此 `FINAL-MAJOR-01` 已关闭；当前仅余 Q2 新增端到端证据的用户人工复确认及 FINAL MODEL REVIEW 人工裁决。本报告其余章节保留原始发现和裁决过程，作为可追溯历史记录。

## 2. Repo Snapshot

```text
BRANCH = main
LOCAL_HEAD = 1be78b983274e214eb5b57f06348dfb27e75edb2
REMOTE_HEAD = 1be78b983274e214eb5b57f06348dfb27e75edb2
WORKTREE_AT_REVIEW_START = CLEAN
```

本审查仅读取 `B题.pdf` 作为 2022 来源；未读取 `2023.md`，未搜索或使用任何 2022 B 赛后材料。

## 3. Original Problem Coverage

| 原题要求 | 覆盖状态 | 证据链 | 审查结论 |
| --- | --- | --- | --- |
| Q1(1)：三架编号已知、无偏差发射机下定位略有偏差接收机 | COVERED | 完整双侧定夹角圆、全交点、三角回代、局部秩 | 仅局部、非退化候选与局部唯一性判定 |
| Q1(2)：FY00/FY01 已知且其余编号未知时的最少新增发射机数 | CONDITIONALLY_COVERED | `m=0` 反例、392 次枚举、局部分离判据、`m=2` 冗余方案 | `m_min=1` 仅限自身编号已知、目标邻域、非退化 |
| Q1(3)：表 1、FY00 与至多三架外围发射机、多轮调整至半径 100 m 正九边形 | COVERED | 实际排程日志、表 1 确定性回放、最终几何验收 | 仅表 1、目标邻域、非退化回放 |
| Q2：锥形编队、三族直线相邻等距的纯方位调整 | CONDITIONALLY_COVERED | 可信基线、局部建锚、四参考候选、11 机局部控制、30 边/12 线评估 | 缺少实际完整回放末态的最终几何验收，见 MAJOR-01 |

不存在“模型完整但漏答题目文字要求”的 FATAL 缺口；Q2 的端到端数值证据缺口使其不能在本轮通过最终模型审查。

## 4. Q1(1) Verdict

`Q1_1_FINAL_VERDICT = PASS`。生产实现 `src/q1_1_geometry.py` 枚举双侧定夹角圆和全部圆交点，并对每个候选回代三条原始 `\mathrm{atan2}` 无符号角。正式 JSON 覆盖理想、镜像/多根、相切、近退化与 `0/\pi` 边界；独立多初值数值复核器不构造圆。局部秩 `2` 仅支持非退化局部唯一性判定，未被写成全局唯一。

## 5. Q1(2) Verdict

`Q1_2_FINAL_VERDICT = PASS`。`m=0` 的同角圆弧反例否定零匿名机；生产枚举器实际记录 `392` 次身份假设，保留 `294` 条远端或错误身份候选，并以 80 位复算给出 `20°` 编号假设间观测分离度和 1 m 局部域正下界。`m=2` 的 `42` 个有序排列只是证据不足时的冗余发射备用方案。允许结论仍是局部 `m_min=1`，而非全平面最少数。

## 6. Q1(3) Verdict

`Q1_3_FINAL_VERDICT = PASS`。实际事件日志、排程审计、预置目标纯方位观测向量独立复算、同机留出角约束检验、有限差分与独立解析基准求解器隔离、旋转/镜像几何不变性检验及同口径对照试验均已进入可失败 Gate。控制器输入不含世界坐标、仿真真值、锚点坐标、别机角或评估器输出。结论严格限于表 1、目标邻域、非退化、确定性回放。

## 7. Q2 Verdict

`Q2_FINAL_VERDICT = REMEDIATION_REQUIRED`。以下子证据仍有效：纯夹角共同缩放不可辨识性负对照；FY11/FY15 的用户批准可信尺度基线；FY04/FY03 目标点的满秩 Jacobian、`GF=0` 与一阶周期谱近零；四参考下 11 个理想槽位的完整单候选及独立根集复核；局部网格、压力域失败保留和在线信息隔离故障注入。

但 `tests/q2_program_gate.py` 的跟随者检查以理想 `lattice` 直接构造四参考锚点和目标观测，未使用有限步建锚后 FY03/FY04 的实际终点；随后几何评估也直接评估理想 `lattice`。因此，当前 30 条边和 12 条最大直线的舍入级误差只验证目标格点自身，不能验证完整控制回放的最终队形。

## 8. Cross-question Consistency

`CROSS_QUESTION_CONSISTENCY = PASS_WITH_Q2_VALIDATION_GAP`。

- Q1(1) 的稳定无符号角、完整候选和拒绝语义被 Q1(2) 生产枚举真实复用；Q1(3) 在排程已知时合理关闭匿名层。
- 四问均把坐标限定为内部推导、仿真观测生成或离线评估；在线动作只使用本机角与预装目标量。
- Q1 的 100 m 圆形硬尺度未与 Q2 的参数化 (d^\ast) 混用；Q2 的 FY11/FY15 可信基线是用户批准的附加条件，不反向改变 Q1。

## 9. Information Boundary Audit

`INFORMATION_BOUNDARY = PASS`。Q1(3) 与 Q2 的控制器 API、AST 审计、实际观测事件和非法字段负对照均未发现距离、世界坐标、仿真真值、未来状态、跨接收机角或评估器回灌。Q2 的 FY11/FY15 仅作为可信相对基线的尺度条件；其绝对坐标没有输入其他无人机控制器。留出角约束均来自同一接收机，未被当作独立外部证据。

## 10. Mathematical Red Team and Evidence-chain Audit

| Claim | Evidence | Evidence type | Allowed strength | Prohibited strength | Source file |
| --- | --- | --- | --- | --- | --- |
| Q1(1) 完整有限候选 | 双侧圆、全交点、三角回代、独立多初值根集 | 几何构造 + 同源第二实现 | 局部非退化候选/判定 | 全局唯一 | `results/q1_1/q1_1_minimum_gate.json` |
| Q1(2) 局部 `m_min=1` | `m=0` 反例、392 次生产轨迹、秩与分离下界 | 反例 + 穷举 + 局部解析/高精度复算 | 给定局部域内联合可辨识 | 全平面最少或全局身份唯一 | `results/q1_2/q1_2_minimum_gate.json` |
| Q1(3) 表 1 恢复 | 本机事件、独立解析基准求解器、最终几何评估 | 确定性回放 + 故障注入 | 表 1 局部回放 | 全局/实机结论 | `results/q1_3/q1_3_program_gate.json` |
| Q2 局部建锚结构 | 导数块、`GF=0`、720/256 分阶段回放 | 解析 + 有限差分 + 局部回放 | 目标邻域的一阶局部结论 | 两轮精确到位、任意初态收敛 | `results/q2/q2_program_gate.json` |
| Q2 四参考槽位判定 | 全圆分支、全部本机角回代、独立根集、旧路线双根负对照 | 完整枚举 + 独立数值复核 | 理想目标附近单候选 | 全平面唯一 | `results/q2/q2_program_gate.json` |
| Q2 最终 30 边/12 线 | 当前仅对理想格点调用评估器 | 静态目标几何检查 | 目标格点满足几何定义 | 完整控制回放的最终验收 | `tests/q2_program_gate.py:169` |

## 11. Innovation Verdict

| 创新 | Verdict | 审查结论 |
| --- | --- | --- |
| 完整几何候选、退化登记与拒绝机制 | CORE | 修复首根偏差与多解掩盖；有完整枚举、回代和负例证据 |
| 匿名编号—连续位置联合局部可辨识 | CORE | 离散身份被独立建模；反例、枚举、局部分离与 `m=2` 备用闭环 |
| Q1(3) 严格本机双节点交替校正建锚与局部零谱 | CORE | 机制、导数、回放、排程和信息隔离均已验证；仅局部 |
| Q2 尺度审计、可信基线、严格本机建锚与四参考归槽 | CORE_PENDING_END_TO_END_EVIDENCE | 局部机制成立；完整端到端几何验收须修复后才能作为最终已验证贡献 |
| 信息隔离、独立复核器、故障注入与几何不变性检验 | SUPPORTING | 支持证据可信度，不单独夸大为核心模型创新 |

## 12. Claim-strength Matrix and Known Limitations

允许使用 `LOCAL`、`NONDEGENERATE`、`TARGET_NEIGHBORHOOD`、`DETERMINISTIC_REPLAY`，以及仅 Q2 的 `TRUSTED_BASELINE`。所有正式材料不得声称全局唯一、任意初态全局收敛、现实飞行精度、无尺度参考仍可恢复指定 (d^\ast)、FY11/FY15 是原题明示可信种子，或留出角是独立外部验证。

已知限制包括：Q1(2) 的远端候选存在；Q1(3) 只覆盖表 1 局部回放；Q2 压力域保留 2 个失败；Q2 可信参考误差会传播；以及 MAJOR-01 所述端到端最终几何验收尚未闭环。

## 13. Paper Readiness

Q1 可进入论文准备，前提是维持既有局部结论边界。Q2 的叙事可保留尺度不可辨识性、可信基线公开、局部建锚和理想四参考候选；在修复前必须删除或降级任何把 30 边/12 线舍入级误差称为完整控制回放终态的表述。正式 Markdown 的当前公式审计未发现 `\operatorname`、异常控制字符或标题中的块公式；现有术语统一问题仅属次要表达问题，因 MAJOR-01 未在本轮改写。

## 14. Findings by Severity

```text
FINDING_ID = FINAL-MAJOR-01
SEVERITY = MAJOR
FILE = tests/q2_program_gate.py
LINE = 99-113, 169, 173
ISSUE = 跟随者控制和几何验收未接入实际有限步建锚末态。
EVIDENCE = _follower_checks 直接以理想 lattice 生成 FY03/FY04/四参考锚点；evaluate_formation(lattice) 直接评估理想格点。
CONSEQUENCE = 30 边/12 线及舍入级终态误差不能作为完整 Q2 控制回放的证据。
REQUIRED_ACTION = 从明确扰动的 15 机初态完整执行建锚和 11 机本机归槽；用实际最终点重算留出角、30 边、12 线和拒绝状态；将可信参考误差敏感性纳入正式 Gate或同步收窄契约。
MODEL_CHANGE_REQUIRED = NO
REOPEN_REQUIRED = NO
```

```text
FINDING_ID = FINAL-MINOR-01
SEVERITY = MINOR
FILE = CURRENT_STATE.md / paper_handoff/Q2_PAPER_HANDOFF.md
LINE = 121-125 / 67
ISSUE = Q2 创新、最高风险和人工冻结状态存在过时描述。
EVIDENCE = 当前 Q2 已最终冻结，但状态文字仍保留旧路线或“尚未给出裁决”。
CONSEQUENCE = 论文交接时可能误导读者；不改变数学或数值。
REQUIRED_ACTION = 在 MAJOR-01 修复完成后，与正式证据同步作非语义更新。
MODEL_CHANGE_REQUIRED = NO
REOPEN_REQUIRED = NO
```

## 15. Sol Delegation Record

```text
SOL_DELEGATION = YES
ROLE = FINAL MODEL REVIEW SPECIALIST
REQUESTED_MODEL = gpt-5.6-sol
REQUESTED_REASONING_EFFORT = xhigh
ACTUAL_MODEL = NOT_VERIFIED
ACTUAL_REASONING_EFFORT = NOT_VERIFIED
ACTUAL_PROFILE_VERIFIED = NO
DECISION = REMEDIATION_REQUIRED
FATAL_MODEL_MISMATCH = NO
REOPEN_REQUIRED = NO
RETURN_TO_TERRA = YES
```

## 16. Final Reviewer Decision

在完成 `FINAL-MAJOR-01` 的有界 Q2 验证器修复、重新生成 Q2 Gate JSON 与正式证据、并由用户重新确认受影响的 Q2 人工核查内容之前，不得将本项目写为 FINAL MODEL REVIEW 通过，不得开始正式论文写作或后续阶段。

## 17. 端到端修复实施状态（Work 复审前的历史记录）

`FINAL-MAJOR-01` 的实现性修复在当时已完成待复审：Q2 Gate 现从 33 个完整案例的实际有限试探 FY04/FY03 建锚末态出发，再运行 11 架跟随者的本机控制，并以实际 15 节点末态评估 30 条边和 12 条最大直线。理想锚点重置与最终几何扰动负对照均可机械失败。

## 18. Remediation Closure / Work Reaudit（人工裁决前的历史记录）

```text
FINAL_MAJOR_01_STATUS = REMEDIATED_AND_CLOSED
Q2_END_TO_END_WORK_REAUDIT = PASS
Q2_END_TO_END_GATE = PASS
FINAL_MODEL_REVIEW_PROGRAM_VERDICT = PASS_WITH_MINOR_FIX
FATAL_MODEL_MISMATCH = NO
REOPEN_REQUIRED = NO
```

Work 复审确认：33 个完整端到端案例（其中 32 个非零扰动）均通过；跟随者实际使用 FY03/FY04 建锚终点；理想锚点重置和终态几何扰动负对照均被检出；在线信息隔离仍通过。唯一修正为 Q2 人工核查卡中的历史文字澄清：理想目标格点的舍入级 30 边/12 线检查不得再描述为实际端到端终态。该 MINOR 文字修正不改变模型、公式、数值、信息边界或结论强度。

据此，程序审查当时已通过；在用户随后给出人工裁决前，`FINAL_MODEL_REVIEW_HUMAN_VERDICT` 与 `FINAL_MODEL_FREEZE` 保持 `PENDING`。

## 19. 最终人工裁决与冻结登记

```text
Q2_END_TO_END_HUMAN_RECONFIRMATION = PASS
FINAL_MODEL_REVIEW_HUMAN_VERDICT = PASS
FINAL_MODEL_FREEZE = PASS
FATAL_MODEL_MISMATCH = NO
REOPEN_REQUIRED = NO
```

上述两项 `PASS` 均由用户本人明确给出，不是 Codex 或程序自动判定。用户接受 Q1(1) 至 Q2 的适用条件与结论边界，接受 FY11/FY15 可信无偏差基线是 Q2 的额外建模条件，接受 `FINAL-MAJOR-01` 已通过端到端修复关闭，并接受模型不得外推为全局唯一、任意初态成功、现实飞行精度或有偏差参考机仍可靠。冻结仅标志模型阶段在这些边界内结束，不改变既有冻结数学路线、正式数值或信息边界。

## 20. Q2 固定周期停止规则证据修复

Q2 的实际 FY04/FY03 建锚回放现按预编排固定 20 个宏周期运行；每个宏周期均包括 FY04 本机子轮与 FY03 本机子轮。AST 审计记录 `break_count = 0`、`TRUTH_BASED_STAGE_SWITCH_FOUND = NO`、`CROSS_RECEIVER_RESIDUAL_AGGREGATION_FOUND = NO`。排程结束后才由离线评估器读取仿真真值；33 个完整端到端案例均通过，最坏节点误差、边长误差、共线距离与同机留出角约束残差分别为 \(5.66\times10^{-10}d^\ast\)、\(5.65\times10^{-10}d^\ast\)、\(1.70\times10^{-10}d^\ast\)、\(2.52\times10^{-10}\) rad。该修复不改变数学路线或结论强度。
