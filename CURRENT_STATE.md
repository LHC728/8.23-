# Current Project State

```text
PHASE = MODEL_EXECUTION
OPENING_STATUS = COMPLETE
STRATEGY_STATUS = FROZEN
NEXT_EXECUTOR = CODEX
SOURCE_OF_TRUTH = opening/07_STRATEGY_FREEZE.md
Q1_1_MINIMUM_GATE = PASS
Q1_1_PROGRAM_GATE = PASS
Q1_1_OFFICIAL_RESULT = results/q1_1/Q1_1_OFFICIAL_RESULT.md
Q1_1_HUMAN_CHECK_CARD = human_check/Q1_1_HUMAN_CHECK_CARD.md
Q1_1_PAPER_HANDOFF = paper_handoff/Q1_1_PAPER_HANDOFF.md
Q1_1_HUMAN_VERDICT = PASS
Q1_1_REMOTE_CHECKPOINT = SUCCESS
Q1_1_FINAL_FREEZE = PASS
Q1_1_FINAL_CHECKPOINT = SUCCESS
Q1_1_FINAL_LOCAL_COMMIT = 75b1ad5d861d04124302e15d5c844a370030fa39
Q1_1_FINAL_REMOTE_COMMIT = 75b1ad5d861d04124302e15d5c844a370030fa39
Q1_1_FINAL_REMOTE_VERIFICATION = origin/main HEAD matches local final-freeze commit; human verdict, final-freeze state, and Q1(1) package confirmed present
Q1_1_LOCAL_COMMIT = 63bc9b1 (Q1.1: pass minimum gate and freeze official result)
REMOTE_CHECKPOINT = SUCCESS
REMOTE_COMMIT = 63bc9b11bab7355782378a7ece00c6c0dcc68cb2
REMOTE_VERIFICATION = origin/main HEAD matches local HEAD; required Q1(1) package and governance/reference files confirmed present
Q1_2_PROGRAM_GATE = PASS
Q1_2_OFFICIAL_RESULT = results/q1_2/Q1_2_OFFICIAL_RESULT.md
Q1_2_HUMAN_CHECK_CARD = human_check/Q1_2_HUMAN_CHECK_CARD.md
Q1_2_PAPER_HANDOFF = paper_handoff/Q1_2_PAPER_HANDOFF.md
Q1_2_HUMAN_VERDICT = PASS
Q1_2_FINAL_FREEZE = PASS
Q1_2_FINAL_CHECKPOINT = SUCCESS
Q1_2_FINAL_LOCAL_COMMIT = 96eb332cfeb4fc7d8c1f8d348d629565b2a86733
Q1_2_FINAL_REMOTE_COMMIT = 96eb332cfeb4fc7d8c1f8d348d629565b2a86733
Q1_2_FINAL_REMOTE_VERIFICATION = origin/main HEAD matches local final-freeze commit; human verdict, final-freeze state, and Q1(2) package confirmed present
Q1_2_SOL_DELEGATION = NO
Q1_2_RETROSPECTIVE_REMEDIATION = PASS
Q1_2_RETROSPECTIVE_WORK_REAUDIT = PASS
Q1_2_RETROSPECTIVE_HUMAN_RECONFIRMATION = PASS
Q1_MID_REVIEW_STARTED = YES
Q1_MID_REVIEW_REPORT = review/Q1_MID_REVIEW.md
Q1_MID_REVIEW_PROGRAM_VERDICT = PASS_WITH_MINOR_FIX
Q1_TERMINOLOGY_NORMALIZATION = COMPLETE
Q1_FORMULA_RENDERING_AUDIT = PASS
Q1_MID_REVIEW_HUMAN_CHECK_CARD = human_check/Q1_MID_REVIEW_HUMAN_CHECK_CARD.md
Q1_MID_REVIEW_HUMAN_VERDICT = PASS
Q1_MID_REVIEW_FINAL_CHECKPOINT = SUCCESS
Q2_STARTED = NO
Q2_ROUTE_DESIGN_REVIEW = COMPLETE
Q2_ROUTE_PROPOSAL_GATE = PASS
Q2_ROUTE_PROPOSAL = review/Q2_FINAL_ROUTE_PROPOSAL.md
Q2_ROUTE_HUMAN_CHECK_CARD = human_check/Q2_ROUTE_PROPOSAL_HUMAN_CHECK_CARD.md
Q2_ROUTE_HUMAN_VERDICT = PENDING
Q2_REOPEN_REQUEST = PENDING_USER_DECISION
Q2_REOPEN_SCOPE = REFERENCE_FRAME_AND_SCALE_LAYER
Q2_PROVISIONAL_WINNER = FY11/FY15_TRUSTED_SEEDS_TO_FY04/FY03_BOOTSTRAP_TO_FOUR_REFERENCE_PLACEMENT
Q1_3_STARTED = YES
Q1_3_CORE_IMPLEMENTATION = COMPLETE
Q1_3_PROGRAM_GATE = PASS
Q1_3_REMEDIATION = PASS
Q1_3_VALIDATOR_HARDENING = PASS
Q1_3_WORK_AUDIT = REMEDIATED: preloaded ideal signatures, plant/controller isolation, actual holdouts, independent exact oracle, full metamorphic test, same-metric ablation, and mechanical schedule/firewall checks
Q1_3_OFFICIAL_RESULT = results/q1_3/Q1_3_OFFICIAL_RESULT.md
Q1_3_HUMAN_CHECK_CARD = human_check/Q1_3_HUMAN_CHECK_CARD.md
Q1_3_PAPER_HANDOFF = paper_handoff/Q1_3_PAPER_HANDOFF.md
Q1_3_HUMAN_VERDICT = PASS
Q1_3_FINAL_FREEZE = PASS
Q1_3_SOL_DELEGATION = NO
CODEX_NEXT_ACTION = WAIT_FOR_Q2_ROUTE_HUMAN_VERDICT
```

## Frozen winner

- `WINNER = STRICT_LOCAL_CERTIFIED_ANGLE_CONSTRAINT_ROUTE`
- Q1(1)：双侧定夹角完整候选与局部单射。
- Q1(2)：匿名身份—连续位置联合枚举，局部 (m_{\min}=1)，第二匿名机为 fail-safe。
- Q1(3)：FY04/FY07 严格本地交替自举，随后固定 FY00/FY01/FY04/FY07、六机并行本机归槽。
- Q2：FY01/FY11/FY15 各自本机内角均衡，固定自由尺度等边外框后十二机并行本机签名归槽。

## Frozen information decisions

1. 禁止跨接收机上报或汇总夹角；某个夹角只可由测得它的无人机用于本机动作与本机验收。
2. 允许预编排收发时序、固定编号、预装目标签名和本机动作历史。
3. Q2 的“如 50 m”只是例示；共同尺度为自由相似规范。
4. 表 1 除题给且保持不动的 FY00/FY01 种子外只进入离线评估器，不进入在线决策器。
5. 旧跨机互易两角、在线全图因子、集中 Route A/B 和依赖跨机合角的 2-tree 均已淘汰。

## Pending Q2 route proposal

- 当前 Strategy Freeze 尚未修改；正式 Q2 仍是上面的自由尺度路线。
- 已完成固定参数间距 $d^\ast$ 路线的设计 Gate：FY11/FY15 可信种子，FY04/FY03 严格本机交替建锚，随后四参考机下 11 机并行归槽。
- 该候选要求用户明示批准 FY11/FY15 的无偏差可信基线 $4d^\ast$；否则退回自由尺度路线。
- 设计证据见 `review/Q2_FINAL_ROUTE_PROPOSAL.md`；当前等待 `Q2_ROUTE_PROPOSAL_HUMAN_VERDICT`，不得自动改写 `opening/07_STRATEGY_FREEZE.md` 或开始 Q2 正式实现。

## Core innovations

1. 局部认证域与匿名身份分离证书。
2. FY04/FY07 严格本地零谱交替自举。
3. 三内角本地均衡—固定外框并行签名。

## Highest execution risk

核心解析结论对应精确、非退化、目标邻域内的局部映射；有限差分、阻尼、有限宏周期、Q2 边界槽位和远端根仍需按 `opening/07_STRATEGY_FREEZE.md` 的最小 Gate 顺序核验。不得宣称全局唯一或任意初态收敛。

## Clean-room record

- `B题.pdf` 仍是唯一允许使用的 2022 来源。
- 禁止读取 `2023.md` 或任何 2022 B 赛后论文、题解、讲评和标准路线。
- `CONTAMINATION_BLOCKED`：历史候选审阅中曾遇到明显针对当前赛题的赛后材料，已立即停止读取且未使用其内容。
- Stage 6 未重新进行文献搜索；裁决仅使用原题、既有 opening 文件和已筛选 paper cards。

## Governance

Codex 不得擅自重新开题。实现阶段若发现满足五类重开条件的 `FATAL_MODEL_MISMATCH`，可以提交 `REOPEN_REQUEST`，但在用户批准前不得更换整条主线。
