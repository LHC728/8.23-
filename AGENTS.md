# Shared Project Rules

## Scope and clean-room boundary

- This project is a timed simulation for the 2022 National College Students Mathematical Modeling Competition, undergraduate Group B.
- `B题.pdf` is the sole permitted 2022 source. Do not read, search for, invoke, cite, or use any other material concerning 2022 B.
- In particular, do not open or read `2023.md`; it is a contamination source for this simulation.
- The historical files `2016-2018(1).md`, `2019-2021.md`, and `2024-2025(1).md` may be used only as modeling-experience priors, never as an answer to the current problem.
- If any web search result or other source is clearly a post-contest solution, commentary, award paper, or standard route for 2022 B, stop reading it immediately. Do not extract its methods. Record `CONTAMINATION_BLOCKED` in the active project record, then proceed only with general academic materials.

## Collaboration and deliverables

- Put substantive work in project files, not only chat messages.
- Use the numbered files in `opening/` for the opening-stage records:
  - `01_PROBLEM_MAP.md`
  - `02_PRIOR_EXPERIENCE.md`
  - `03_LITERATURE_PLAN.md`
  - `04_LITERATURE_EVIDENCE.md`
  - `05_BASELINE_AND_METHOD_MAP.md`
  - `06_INNOVATION_AND_ROUTES.md`
  - `07_STRATEGY_FREEZE.md`
- Keep `CURRENT_STATE.md` current whenever the phase, ownership, status, or a material blocker changes.
- Chat updates should contain only key conclusions, decisions requiring the user, and the next action; the complete evidence belongs in files.

## Modeling principles

- Full coverage of every problem is mandatory.
- Choose complexity to match mechanisms, data, and validation needs; neither simplicity nor complexity is a virtue by itself.
- Every innovation must identify the real limitation in its baseline model and the mechanism by which it addresses it.
- Consider cross-domain mathematical analogies, but explicitly map states, variables, constraints, and dynamics before adopting them.
- Treat historical experience as soft prior information. Prefer evidence from the current problem.
- Use literature for theory, parameters, upgrade paths, and validation, not as a substitute for problem analysis.

## Opening-stage constraint

- During the opening phase, prioritize interpretation, route design, feasibility checks, and parameter/validation planning.
- Do not begin large-scale implementation, full numerical simulation, formal paper writing, or lengthy engineering setup unless the project state explicitly advances to a later phase.

## 已冻结的题意解释

- 禁止跨接收机上报夹角。某个夹角只能由测得它的接收机保存，并用于该机自身的移动和本机验收；不得把角值转发给其他无人机，也不得汇总到集中控制器参与在线动作计算。
- 预编排的收发时序、无人机编号、目标签名和每架无人机自己的试探/控制历史可以使用；它们不属于跨机夹角上报。
- Q2 中“如 50 m”只是例示，不是必须恢复的物理长度；目标只要求相邻间距相等，共同尺度属于自由的相似规范。

## Frozen strategy and Codex governance

- Opening is complete. The sole strategy source of truth is `opening/07_STRATEGY_FREEZE.md`; older candidate routes are historical records and must not override it.
- Codex 不得擅自重新开题、重新进行无边界方法搜索，或因为想到更复杂的方法而替换冻结主线。
- Codex 必须按 `opening/07_STRATEGY_FREEZE.md` 的 `Codex Execution Order` 逐 Gate 施工；最小解析/有限小例未通过前，不得开始批量仿真或论文包装。
- 实现阶段若发现根本误读、非法信息依赖、核心数学结构错误、某问实际上无法回答或核心参数根本不可取得，应登记 `FATAL_MODEL_MISMATCH` 并向用户提出 `REOPEN_REQUEST`。
- Codex 可以提出 `REOPEN_REQUEST`，但在用户批准前不得自行更换整条主线；普通公式细化、参数调节、代码错误、数值不稳或验证尚未完成不构成重开理由。
- 在线实现继续禁止跨接收机夹角上报或集中动作计算。离线验证器可读取仿真真值或汇总角作独立检查，但其输出不得回灌在线决策器。
- 已淘汰的跨机互易两角、在线全图因子、集中 Route A/B 和依赖跨机合角的 2-tree 不得作为 fallback 恢复。

## Q1 论文术语规范

- Q1 正式 Markdown 中，“角度签名/角签名”统一表述为“纯方位观测向量”；“三角签名”表述为“三维纯方位观测向量”；“身份签名间隔”表述为“编号假设间的观测分离度”。
- “认证”按语境表述为“局部唯一性判定”或“局部可辨识性判定”；“holdout”表述为“留出角约束检验”，并明确其来自同一接收机而非独立外部证据。
- “fail-safe、bootstrap、checker、oracle、plant、truth、metamorphic test、ablation”在首次出现时分别采用“冗余发射备用方案、双节点交替校正建锚、独立数值复核器、独立解析基准求解器、仿真观测生成环境、仿真真值、几何不变性检验、同口径对照试验”的中文说明。状态键、文件名、Python/JSON 标识符保持不变。

# Model Routing Policy

本项目采用“按任务风险分配模型与 reasoning effort”的原则，而不是始终使用最高能力模型。模型等级不代表任务重要程度；选择依据是：**若判断出错，是否会改变核心数学模型、正式结论、创新成立性或整篇论文可信度？** 若不会，原则上不得无必要请求 Sol。

本 Policy 是后续 Work、Codex、Reviewer 与论文阶段共同遵守的长期规则。其只决定“谁来执行、以什么期望模型和 reasoning effort 执行”，不得改变 clean-room boundary、information boundary、Strategy Freeze、REOPEN governance 或冻结数学路线。

## 1. One Main Agent + Temporary Specialists

> Terra 是默认常驻 Main Agent。
>
> 普通模型实施由 Terra 自己完成；已完全规则化、低风险、高重复任务优先委派 Luna Worker Subagent；高后果数学、模型、创新、结论和治理裁决优先委派 Sol Specialist Subagent。子 Agent 完成明确子任务后返回结果并结束，Terra Main Agent 继续施工。

```text
Terra Main Agent
        │
        ├── 普通模型实施 / Debug / 实验 → Terra 自己完成
        ├── 低风险、高重复、机械工作 → Luna Worker Subagent
        └── 高后果数学 / 模型 / Claim 裁决 → Sol Specialist Subagent
```

原则为 **One Main Agent + Temporary Specialists**。不得重新建立复杂 Harness，亦禁止 Reviewer of Reviewer、多层长期 Agent 链、常驻专家委员会、多个 Agent 对同一问题反复讨论，或让一次局部升级导致高级模型接管整问。

## 2. Terra：默认 Main Agent

Terra 是 MODEL_EXECUTION 阶段默认主执行者；主 Agent 原则上保持 Terra，不因局部任务频繁切换整个主 Agent 模型。默认 Main Agent profile 为 `Terra High`。

Terra 负责冻结模型的公式细化、正式代码实现、Debug、deterministic checker / oracle、数值稳定性处理、正式数据计算、小范围参数扫描、Baseline 与 Innovation 实现及同口径比较、常规验证、Human Check Card、Paper Handoff、常规论文内容整理、图表解释与正式结果整理。

Terra 首先将问题分类为 `IMPLEMENTATION ISSUE` 或 `MODEL / MATH / INNOVATION / CLAIM / GOVERNANCE ISSUE`。普通代码 bug、数值误差或精度、初值、步长、阻尼、路径、数据格式、绘图、运行速度、冻结算法实现错误和一般数值稳定性通常均属 IMPLEMENTATION ISSUE，应由 Terra 自己修复；不得因第一次实现失败调用 Sol。

## 3. Luna：Temporary Worker Subagent

Luna 是 temporary low-risk worker，仅在任务同时具备规则已确定、输入输出明确、不需新的核心数学判断、重复性高且结果可机械检查时才值得委派。

典型任务包括：批量运行已验证测试、大量固定参数实验、JSON / CSV / TXT 转换、结果汇总、简单统计、标准图表批量生成、文件完整性检查、Markdown / LaTeX 机械格式整理、表格格式统一与冻结模板下的重复生成。

Luna 不得独立裁决核心数学公式、唯一性、可辨识性、最少数量、收敛性、Jacobian / rank / spectrum 的数学结论、核心创新、论文强结论、`FATAL_MODEL_MISMATCH`、REOPEN 或更换冻结模型。发现异常时仅返回：

```text
WORKER_STATUS = BLOCKED
ANOMALY =
EVIDENCE =
```

由 Terra 判断；Luna 不得自行调用 Sol。

Terra 委派 Luna 时尽量提供：

```text
ROLE =
TASK =
INPUT =
OUTPUT =
ALLOWED_ACTIONS =
FORBIDDEN_DECISIONS =
STOP_CONDITION =
REQUESTED_MODEL =
REQUESTED_REASONING_EFFORT =
```

## 4. Sol：Temporary Specialist Subagent

Sol 是 temporary high-consequence specialist。满足高后果条件时，Terra 应优先委派一个有边界的 Sol Specialist Subagent，而非让 Sol 永久接管 Main Agent。Sol 是 `BOUNDED SPECIALIST`，不得从头重新研究整题、无边界重新检索论文、擅自替换 Strategy Freeze、顺手接管后续代码、为“高级”引入新模型家族，或扩大至当前争议之外。

可委派 Sol 的触发条件为：

### MATH

1. 两个独立实现产生无法由普通 bug 解释的矛盾；
2. 核心解析公式无法确认，或解析与数值结果系统性冲突；
3. 唯一性、可辨识性、最少数量或局部/全局收敛性判断；
4. 核心 Jacobian / rank / spectrum / degeneracy 的裁决。

### MODEL

5. 冻结路线可能存在核心数学结构错误；
6. 当前模型可能无法回答某个题问；
7. 核心变量或参数可能无法获得；
8. 在线实现可能违反 information boundary。

### INNOVATION / CLAIM

9. 核心创新成立性或其与 Baseline 的真实数学差异存在争议；
10. 创新保留、降级或删除将显著影响论文主线；
11. 证据是否足以支持强论文结论，或“局部”能否提升为更强结论；
12. “可行 / 局部较优 / 经验较优 / 全局最优”等结论强度需要裁决。

### GOVERNANCE

13. 可能触发 `FATAL_MODEL_MISMATCH`；
14. 是否提交或批准 `REOPEN_REQUEST`；
15. MID REVIEW、FINAL MODEL REVIEW、全篇论文总体结构高层裁决或 FINAL PAPER RED TEAM。

Terra 委派 Sol 时应提供：

```text
ROLE =
QUESTION =
WHY_SOL_IS_NEEDED =
FROZEN_CONTEXT =
RELEVANT_FORMULAS =
EVIDENCE =
CONFLICT =
ALLOWED_SCOPE =
FORBIDDEN_SCOPE =
STOP_CONDITION =
REQUESTED_MODEL =
REQUESTED_REASONING_EFFORT =
REQUIRED_OUTPUT =
```

Sol 返回优先采用：

```text
DECISION =
EVIDENCE =
CONFIDENCE =
ALLOWED_CLAIM =
PROHIBITED_CLAIM =
REQUIRED_FIX =
FATAL_MODEL_MISMATCH = YES / NO
REOPEN_REQUIRED = YES / NO
RETURN_TO_TERRA = YES / NO
```

不需要 REOPEN 时，Sol 完成后即结束子任务，Terra 接收裁决并继续施工。

## 5. Agent Delegation Logic and Priority

```text
Terra Main Agent
        ↓
执行、发现任务或问题、分类
        ├── 普通 IMPLEMENTATION ISSUE → Terra 自己处理
        ├── LOW-RISK / REPETITIVE → Luna Worker → 返回 → Terra 继续
        └── MODEL / MATH / INNOVATION / CLAIM / GOVERNANCE
                → Terra 先做一次正常定位
                → 仍存在高后果争议
                → Sol Specialist → 返回裁决 → Terra 继续
```

禁止“普通 bug → Sol”、“任务很重要 → 自动 Sol”以及“一次调用 Sol → Sol 接管整个后续问题”。不要因为 Codex 支持 Agent 就使用 Agent；默认优先顺序固定为：

```text
1. deterministic checker / oracle
2. Terra 自己处理
3. Luna Worker
4. Sol Specialist
```

若程序可以机械判定，优先使用 Oracle。不得将“高级模型认为正确”当作正式验证证据。

## 6. Reasoning Effort Routing Policy

模型与 reasoning effort 是独立维度。使用完成任务所需的最低充分 reasoning effort；强模型不自动等于最高 effort，重要任务不必 Max，所有 Sol 不必 Max，所有 Terra 不必 High/XHigh。

### LOW

适用于文件整理、简单格式转换、文本替换、简单 JSON / CSV、文件完整性检查和已冻结命令重复执行。推荐 `Luna Low`；LOW 不用于核心数学判断。

### MEDIUM

适用于已验证程序批量运行、标准统计汇总、标准图表、简单冻结公式实现、常规数据处理和机械论文格式工作。推荐 `Luna Medium` 或 `Terra Medium`。

### HIGH

High 是正常 MODEL_EXECUTION 的主 effort，适用于冻结模型正式实现、非平凡代码设计、Debug、数值稳定、checker / oracle 设计、正式结果计算、小范围参数选择、Baseline / Innovation 实现、Paper Handoff、常规数学验证与结果证据组织。默认 Main Agent profile 为：

```text
Terra High
```

### XHIGH

`Terra XHigh` 仅用于 IMPLEMENTATION HARD 而非 MODEL MAY BE WRONG 的困难实现，例如难定位数值 bug、多个实现细节耦合、非平凡数值稳定性或冻结数学路线下的困难实现。若 Terra XHigh 能解决，则不需要 Sol。

`Sol XHigh` 是主要高后果数学审查配置，适用于唯一性、可辨识性、最少数量、核心收敛、Jacobian / rank / spectrum、退化结构、独立实现数学冲突、`FATAL_MODEL_MISMATCH`、REOPEN、MID REVIEW 与 FINAL MODEL REVIEW。

### MAX

Max 是异常级配置，不用于普通实现、Debug、数学推导、Reviewer、Paper Handoff 或正文写作。仅可在以下条件同时满足时请求：

1. 属于高后果核心问题；
2. Sol XHigh 仍无法形成可信裁决，或存在两个无法消解的强证据；
3. 错误裁决会改变核心路线、某问是否成立、REOPEN 或论文核心结论；
4. 问题范围已明确且有限。

```text
Sol XHigh
↓
仍存在无法解释的核心数学矛盾
↓
Sol Max
↓
返回 Terra
```

## 7. Effort Escalation Ladder

普通实施问题：

```text
Terra Medium → Terra High → Terra XHigh
```

若仍为 implementation issue，不得因困难自动升级为 Sol。高后果数学问题：

```text
Terra High
↓
确认属于 MATH / MODEL / INNOVATION / CLAIM / GOVERNANCE
↓
Sol High / Sol XHigh
↓
极少数仍不能裁决
↓
Sol Max
```

机械任务仅在已完全规则化时可由 Terra 委派 `Luna Medium / Low`。

## 8. Recommended Profiles by Task

| Task | Preferred profile |
| --- | --- |
| 文件整理 / 格式转换 | Luna Low |
| 批量已验证测试、标准统计、标准图表 | Luna Medium |
| 简单冻结公式实现 | Terra Medium |
| 主模型正式实现、Checker / Oracle、非平凡 Debug、正式数值结果、Paper Handoff、创新初步整理 | Terra High |
| 困难实现问题 | Terra XHigh |
| 普通论文扩写 | Terra Medium / High |
| 创新成立性争议 | Sol High / XHigh |
| 唯一性 / 可辨识性 / 最少数量、核心 Jacobian / 谱 / 收敛 | Sol XHigh |
| MID REVIEW、FINAL MODEL REVIEW、REOPEN / FATAL 核心裁决、FINAL PAPER RED TEAM | Sol XHigh |
| XHigh 仍无法裁决的极少数核心问题 | Sol Max |

## 9. Subagent Model / Effort Observability and Profile Control

不得假设当前 Codex UI 一定能显示或证明子 Agent 的实际模型或实际 reasoning effort。必须严格区分：

```text
REQUESTED PROFILE
```

与：

```text
VERIFIED ACTUAL PROFILE
```

每次模型特定委派可以记录：

```text
REQUESTED_MODEL =
REQUESTED_REASONING_EFFORT =
```

仅当运行环境明确提供可验证元数据时，才可记录：

```text
ACTUAL_MODEL =
ACTUAL_REASONING_EFFORT =
ACTUAL_PROFILE_VERIFIED = YES
```

否则应记录 `ACTUAL_PROFILE_VERIFIED = NO`。不得根据子 Agent 名称、Prompt 中的 Sol / Terra / Luna、输出质量、响应时间或主观感觉反推实际模型。

若环境支持创建子 Agent 且可指定模型与 reasoning effort，则按本 Policy 自动委派。若支持子 Agent 但不能指定模型或 effort，不得假装已实现异模型路由，并记录：

```text
SUBAGENT_AVAILABLE = YES
PROFILE_CONTROL_AVAILABLE = NO
REQUESTED_MODEL =
REQUESTED_REASONING_EFFORT =
ACTUAL_PROFILE_VERIFIED = NO
```

此时 Luna 类机械工作可由 Terra 自行完成，不阻塞项目。对于必须由 Sol 级高后果裁决的问题，若不能保证或请求 Sol profile，应记录：

```text
MODEL_ESCALATION_REQUIRED = YES
RECOMMENDED_MODEL = Sol
RECOMMENDED_REASONING_EFFORT = XHigh
REASON =
SCOPE =
```

不得伪造 Sol 裁决。若环境不支持子 Agent，记录 `SUBAGENT_AVAILABLE = NO`，然后按当前能力继续；工具能力限制不得改变冻结数学路线。

## 10. Delegation Profile Contract and Routing Record

创建模型特定子 Agent 时，尽量明确：

```text
ROLE =
TASK =
REQUESTED_MODEL =
REQUESTED_REASONING_EFFORT =
WHY_THIS_PROFILE =
SCOPE =
FORBIDDEN_SCOPE =
STOP_CONDITION =
REQUIRED_OUTPUT =
```

例如对 Q1(2) 局部 `m_min = 1` 结论的可辨识性审查，可请求 `Sol XHigh`，范围仅限 `m_min` 及其适用域，禁止重新开题、替换冻结路线或扩展到 Q1(3) 或 Q2，停止条件为形成明确允许结论或指出致命缺口。

普通 Terra → Luna 低风险委派无需创建长日志。Sol Specialist 委派仅需简短记录：

```text
SOL_DELEGATION =
QUESTION =
REQUESTED_MODEL =
REQUESTED_REASONING_EFFORT =
ACTUAL_PROFILE_VERIFIED =
REASON =
SCOPE =
DECISION =
RETURNED_TO_TERRA =
```

不得创建复杂 Agent 审计系统。

## 11. Contest-Time Concurrency

仅真正独立任务可并行，例如冻结参数的批量实验、独立 checker、标准图表、文件整理及不改变模型的写作材料整理。不得并行有前后依赖的数学推导、前置 Gate 未通过的后续问题、多个 Agent 同时修改同一核心公式或 Strategy Freeze 禁止的路线探索。并行唯一目的是减少 wall-clock time，不是增加 Agent 数量。

## 12. Review and Paper Workflow Routing

MID REVIEW、FINAL MODEL REVIEW 与 FINAL PAPER RED TEAM 默认请求 `Sol XHigh Specialist Subagent`，Main Agent 仍保持 Terra。MID REVIEW 仅检查 FATAL、MAJOR、信息边界、数学主结构、核心结果与创新成立性；FINAL MODEL REVIEW 完成后返回 Terra 修复；FINAL PAPER RED TEAM 仅审题目覆盖、数学与结果一致性、创新和图表证据、结论强度、摘要与正文数字及已知失败域，不无边界重写全文。

每问 Paper Handoff 默认 `Terra High`。仅在创新主线重大争议、两种叙事将改变全篇核心逻辑或结论强度存在高后果争议时调用 Sol Specialist。普通正文扩写为 `Terra Medium / High`；LaTeX、图题、表题、格式、引用格式与标准图表等机械工作可委派 `Luna Low / Medium`。所有写作 Agent 均不得擅自改变正式数字、数学公式含义、参数、单位、Strategy Freeze 或证据支持的结论强度。

## 13. Priority Rule and Contest Efficiency Principle

如本 Policy 与项目其他规则冲突，优先级固定为：

```text
Clean-room Boundary
>
Information Boundary
>
Strategy Freeze
>
REOPEN Governance
>
Model Routing Policy
```

推荐的默认竞赛结构为：

```text
Luna Low / Medium
        +
Terra High
        +
少量 Sol XHigh
        +
极少数 Sol Max
```

不得全程 XHigh 或 Max、所有 Sol Reviewer 都 Max、所有机械 Worker 都 High，或为可程序验证的问题增加 LLM Reviewer。核心原则是：把高推理能力留给高后果判断，把重复执行交给低风险 Worker，把可机械验证的正确性留给 Oracle。

# Checkpoint & Backup Policy

本项目采用以下三层保护：

```text
Local Save
+
Checkpoint Commit
+
Remote Push
```

本地文件保存不等于 Git commit，Git commit 不等于 GitHub push。只有成功 commit 且成功 push 到当前权威远程分支，才构成可远程恢复的检查点。

## 1. Gate 级强制 Checkpoint

每个正式阶段完成后必须创建 Git checkpoint，包括但不限于：Minimum Gate PASS、Official Result 生成、Human Check Card 生成、Paper Handoff 生成、MID REVIEW 完成、FINAL MODEL REVIEW 完成、一个完整小问完成、重要路线状态变化，以及记录 `REOPEN_REQUEST` 或 `FATAL_MODEL_MISMATCH`。

一个小问进入下一小问之前，其正式成果必须至少存在一个成功 push 的远程恢复点：

```text
Q1(1) Gate PASS
→ Official Result
→ Human Check Card
→ Paper Handoff
→ commit
→ push
→ 确认 push 成功
→ 才允许进入 Q1(2)
```

## 2. 约 30 分钟长任务 Checkpoint

若某 Gate、实现、实验或 Debug 连续进行较长时间，且同时满足以下条件，可以创建中间 checkpoint：

1. 距上一次成功 remote push 约 30 分钟或更久；
2. 已产生实质性代码、模型记录、测试、结果或文档改动；
3. 当前状态能形成基本可恢复的工作点。

此时使用 `CHECKPOINT COMMIT`，不必等待整个 Gate 完成。该规则并非精确每 30 分钟机械提交；仅等待长任务、没有新文件变化、只有临时日志或未成形破碎实验时，无需为计时强制 commit。

## 3. Checkpoint 内容

优先纳入正式代码、checker / oracle、tests、实验配置、小规模验证、Official Result、结果数据、Human Check Card、Paper Handoff、有价值的模型说明、已正式更新的 `CURRENT_STATE.md`、图表生成脚本，以及项目本来就跟踪的正式图表及其结果源。

不得为 checkpoint 硬塞虚拟环境、`__pycache__`、临时缓存、巨型原始数据副本、无价值运行日志、临时下载文件、编辑器缓存、密钥、Token、私密配置或明显超出 Git 合理范围的大文件。若 `.gitignore` 已正确覆盖这些内容，保持不动；只有发现明确遗漏时才汇报，不得擅自扩张修改范围。

## 4. Commit 类型

允许两种提交：

### A. Intermediate Checkpoint

用于长时间施工中的可恢复点、重要 Debug 中间状态，或 Gate 尚未完成但已有大量有效工作。推荐使用有意义的 message，例如：

```text
checkpoint: Q1.1 implementation progress
checkpoint: Q1.3 jacobian debugging
```

不得使用无意义的 `update`、`changes` 或 `save`。

### B. Gate / Milestone Commit

用于 Gate PASS、小问完成、正式结果冻结、Review 完成或 Paper Handoff 完成。推荐例如：

```text
Q1.1: pass minimum gate and freeze official result
Q1.2: complete identifiability result and paper handoff
MID REVIEW: freeze Q1 model package
```

## 5. Push 规则

每个 checkpoint commit 完成后应尽快 push 到当前权威远程分支。仅在 push 成功后，才可记录：

```text
REMOTE_CHECKPOINT = SUCCESS
```

commit 成功但 push 失败时，必须记录：

```text
REMOTE_CHECKPOINT = FAILED
PUSH_ERROR =
LOCAL_COMMIT =
RECOVERY_ACTION =
```

不得把“本地 commit 已完成”写成“GitHub 已备份”。

## 6. 进入下一问之前的硬规则

进入下一正式小问前必须满足：

1. 当前小问正式成果已保存；
2. Git 工作树不存在未解释的重要成果；
3. 至少一次 milestone commit 已创建；
4. remote push 成功。

若 remote push 因网络或认证失败，可以继续做极短本地诊断，但不得长时间跨入下一正式小问而没有远程恢复点；应优先解决 push。

## 7. Git 状态检查

每次 Gate / Milestone checkpoint 前后，至少确认以下事项。

提交前：当前 branch、staged / unstaged 的重要文件、是否有异常大文件、是否有不应提交的敏感文件。

提交后：commit hash、push 是否成功、工作树是否仍有未解释的重要变更。

不得为了追求完全 clean 而删除有价值的本地实验；有意保留未提交文件时，必须明确知道其内容与原因。

## 8. 禁止的自动操作

本 Policy 不授权自动 force push、自动 rebase 历史、自动 `reset --hard`、自动删除未跟踪文件、自动清空工作树、自动修改远程分支历史、自动合并未知冲突、自动提交 secret 或超大文件，亦不授权因 backup 需要改变 Strategy Freeze。

任何可能破坏历史或删除数据的 Git 操作均不得自动执行。本 Policy 亦不授权创建复杂 CI/CD、GitHub Actions、cron 或后台守护进程。

## 9. 与 Model Routing 的关系

Checkpoint 是机械工程任务，默认由 Terra Main Agent 直接执行。仅限 `git status`、文件检查、commit message 整理和低风险结果文件确认时，可委派 Luna Worker。不得因普通 Git 问题调用 Sol；Sol 只处理 Model Routing Policy 已规定的高后果数学、模型、Claim 或 Governance 问题。

## 10. Contest-Time Principle and Minimum Recovery

目标不是创建漂亮 Git 历史，而是保证任何一次意外最多损失约一个施工阶段，而非数小时。优先级为：

```text
可恢复
>
清楚
>
简单
>
Git 历史美观
```

不得过度拆分 commit、每改一行就 commit，或为了 Git 管理打断核心建模节奏。

理想情况下，任意已完成小问均应能只依靠 GitHub 中最近一次 milestone checkpoint 恢复正式代码、主要验证、正式结果、写作交接材料和当前状态；若不能做到，则 checkpoint 不完整。
