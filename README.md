# 2022 B 题纯方位无人机编队：完整建模、验证与写作仓库

本仓库记录一次全国大学生数学建模竞赛本科组 B 题的 clean-room 限时模拟，覆盖：

- 题意与信息边界审计；
- 中外一般学术文献筛选；
- Q1(1)、Q1(2)、Q1(3) 和 Q2 的数学建模；
- 生产实现、确定性验证器和独立复核；
- 人工核查、阶段审查与最终模型冻结；
- 面向论文作者和辅助 AI 的解题、写作及仓库阅读指南。

## 1. 当前状态

```text
OPENING_STATUS = COMPLETE
Q1_1_FINAL_FREEZE = PASS
Q1_2_FINAL_FREEZE = PASS
Q1_3_FINAL_FREEZE = PASS
Q1_MID_REVIEW_HUMAN_VERDICT = PASS
Q2_FINAL_FREEZE = PASS
Q2_END_TO_END_HUMAN_RECONFIRMATION = PASS
FINAL_MODEL_REVIEW_HUMAN_VERDICT = PASS
FINAL_MODEL_FREEZE = PASS
FATAL_MODEL_MISMATCH = NO
REOPEN_REQUIRED = NO
```

模型、实现和验证阶段已经结束，当前没有尚未完成的小问。下一自然阶段是论文正文、正式图表和全文总装，但这些工作不会自动启动。

完整状态见 [CURRENT_STATE.md](CURRENT_STATE.md)。

## 2. 五分钟阅读路线

> **第一次接触这个仓库，不知道该从哪里开始？**
>
> 请先打开 [当前仓库阅读与使用指南](writing_reference/REPOSITORY_READING_GUIDE_FOR_HUMAN_AND_AI.md)。它专门说明文件权威性、Q1/Q2 的正式文件包、证据链、历史文件禁用规则、GitHub/本地查看方法，以及把仓库交给辅助 AI 时应使用的约束。README 是快速入口，该指南是详细操作手册。

### 2.1 队友只想快速理解最终解法

1. 阅读本 README 的“四问最终方案”；
2. 阅读 [Q1 完整解法与证据](writing_reference/Q1_DETAILED_SOLUTION_AND_EVIDENCE.md)；
3. 阅读 [Q2 完整解法与证据](writing_reference/Q2_DETAILED_SOLUTION_AND_EVIDENCE.md)；
4. 对具体数字有疑问时，打开相应 `results/` 正式结果。

### 2.2 论文作者准备写正文

1. [安全写作总指南](writing_reference/SAFE_WRITING_GUIDE.md)；
2. [Q1 写作指南](writing_reference/Q1_WRITING_GUIDE_FOR_HUMAN_AND_AI.md)；
3. [Q2 问题分析与模型写作指南](writing_reference/Q2_PROBLEM_ANALYSIS_AND_MODEL_WRITING_GUIDE.md)；
4. `paper_handoff/` 中各问的论文交接文件；
5. `results/` 中的正式数字和 `figures/` 中后续生成的正式图表。

### 2.3 AI 或 Codex 接手仓库

必须依次读取：

1. [AGENTS.md](AGENTS.md)：clean-room、信息边界、模型路由和 Git 检查点规则；
2. [CURRENT_STATE.md](CURRENT_STATE.md)：当前真实状态；
3. [当前仓库阅读与使用指南](writing_reference/REPOSITORY_READING_GUIDE_FOR_HUMAN_AND_AI.md)：确认阅读顺序、历史文件边界和证据追踪方法；
4. [最终策略冻结文件](opening/07_STRATEGY_FREEZE.md)：数学路线真源；
5. 对应的 `model_contract/`：每问正式模型契约；
6. 对应的 `results/`：正式结果与 Gate JSON；
7. 对应的 `paper_handoff/` 和其他 `writing_reference/`。

不得仅凭聊天记忆或早期候选路线回答项目状态。

### 2.4 需要复核程序证据

依次查看：

1. `src/`：生产几何、身份枚举、调整器和离线评估器；
2. `tests/`：每问确定性 Program Gate；
3. `results/`：Gate 产生的 JSON 与正式结果；
4. `review/`：中期审查、最终审查和 Q2 端到端补强记录；
5. `human_check/`：用户本人完成的人工裁决。

## 3. 事实来源优先级

仓库文件冲突时，按以下顺序判断：

```text
B题.pdf 的原题要求
>
AGENTS.md 的长期边界与治理规则
>
CURRENT_STATE.md 的阶段状态
>
opening/07_STRATEGY_FREEZE.md 的数学路线
>
model_contract/ 的每问正式契约
>
results/ 的正式数字与 Gate 证据
>
review/ 和 human_check/ 的审查裁决
>
早期 opening 候选、旧说明或聊天记录
```

`opening/06_INNOVATION_AND_ROUTES.md`、`review/TEAMMATE_METHOD_COMPARISON.md` 和 `review/Q2_FINAL_ROUTE_PROPOSAL.md` 是历史决策与审计记录，不得作为当前执行指令。它们保留旧候选，是为了说明路线如何被比较、否决和修正，而不是让后续 AI 恢复旧方案。

`SOLUTION_GUIDE.md` 已同步当前 Q1/Q2 路线，用于通俗理解；它不承担数学真源职责。若其中内容与 Strategy Freeze、模型契约、正式结果或最终审查冲突，仍必须以后四者为准。

`opening/07_STRATEGY_FREEZE.md` 中明确标为 **Formal fallback only** 的自由相似尺度路线仍然保留，但只有可信尺度基线条件被撤回时才能按治理规则启用；它不是当前 Q2 主路线。

## 4. 四问最终方案

### 4.1 Q1(1)：已知三发射机下的完整位置候选

统一使用接收机处的无符号夹角观测。对每个定夹角约束生成弦两侧的圆分支，保留全部圆-圆交点，再用第三个夹角逐候选回代。

方案不会默认采用求解器返回的第一个根，并单列：

- $0$ 或 $\pi$ 边界角；
- 相切圆和重合圆；
- 近共线与收发机重合；
- 连续解族和局部 Jacobian 降秩。

只有在目标槽位局部域内候选唯一且 Jacobian 满秩时，才声明局部唯一性。

入口：

- [模型契约](model_contract/Q1_1_MODEL_CONTRACT.md)
- [正式结果](results/q1_1/Q1_1_OFFICIAL_RESULT.md)
- [人工核查卡](human_check/Q1_1_HUMAN_CHECK_CARD.md)
- [论文交接](paper_handoff/Q1_1_PAPER_HANDOFF.md)

### 4.2 Q1(2)：匿名编号与位置的联合局部可辨识

当 FY00、FY01 已知，新增发射机编号未知时，先枚举所有合法编号假设，再对每个假设保留完整几何分支。

正式结论是：

- $m=0$ 时只能形成连续圆弧，不能有效定位；
- 在已知接收机自身编号、小偏差和非退化条件下，$m=1$ 足以形成局部位置与编号的联合判定；
- 第二匿名发射机是被拒绝后的冗余备用方案，不改变局部最少数量结论。

程序实际记录了 392 个 $m=1$ 身份假设事件、294 个局部域外候选和 42 个 $m=2$ 有序排列事件；结论不声称全平面全局唯一。

入口：

- [模型契约](model_contract/Q1_2_MODEL_CONTRACT.md)
- [正式结果](results/q1_2/Q1_2_OFFICIAL_RESULT.md)
- [人工核查卡](human_check/Q1_2_HUMAN_CHECK_CARD.md)
- [论文交接](paper_handoff/Q1_2_PAPER_HANDOFF.md)

### 4.3 Q1(3)：圆形编队的严格本机多轮调整

固定题给的 FY00、FY01 种子。FY04 与 FY07 按预编排时序交替接收和移动，每轮只使用当前接收机自己测得的两个主夹角；完成建锚后固定 FY00、FY01、FY04、FY07，其余六架无人机分别利用本机纯方位观测向量归槽。

表 1 的真实偏差位置只用于盲化观测生成和离线评估，不进入在线控制器。程序结论限定为表 1 确定性回放、目标邻域和非退化情形。

入口：

- [模型契约](model_contract/Q1_3_MODEL_CONTRACT.md)
- [核心推导](modeling/Q1_3_CORE_DERIVATION.md)
- [正式结果](results/q1_3/Q1_3_OFFICIAL_RESULT.md)
- [人工核查卡](human_check/Q1_3_HUMAN_CHECK_CARD.md)
- [论文交接](paper_handoff/Q1_3_PAPER_HANDOFF.md)

### 4.4 Q2：可信尺度基线、交替建锚与四参考归槽

把锥形编队参数化为相邻间距为 $d^\ast$ 的 15 点三角格点。

纯夹角在共同缩放下不变，因此无法自行恢复指定尺度。经用户批准，FY11、FY15 作为可信、无偏差且保持不动的种子，二者基线为 $4d^\ast$。这是一条附加条件，不是原题明示信息。

最终排程为：

1. 固定 FY11、FY15；
2. FY04、FY03 严格使用各自本机夹角交替建锚；
3. 固定 FY03、FY04、FY11、FY15；
4. 其余 11 架无人机分别使用四参考机在本机形成的六个夹角归槽；
5. 离线验收实际 15 节点终态的 30 条相邻边和 12 条最大格点直线。

正式端到端证据包含 33 个确定性案例，其中 32 个为非零扰动；所有案例均把 FY03/FY04 的实际建锚终点传入后续控制，而不是重置为理想锚点。

入口：

- [Q2 完整解法与证据](writing_reference/Q2_DETAILED_SOLUTION_AND_EVIDENCE.md)
- [模型契约](model_contract/Q2_MODEL_CONTRACT.md)
- [正式结果](results/q2/Q2_OFFICIAL_RESULT.md)
- [Program Gate JSON](results/q2/q2_program_gate.json)
- [端到端补强报告](review/Q2_END_TO_END_REMEDIATION.md)
- [人工核查卡](human_check/Q2_HUMAN_CHECK_CARD.md)
- [论文交接](paper_handoff/Q2_PAPER_HANDOFF.md)

## 5. 全题共同的信息边界

在线允许：

- 接收机自己的编号；
- 当轮发射机编号和预编排收发时序；
- 当前接收机自己测得的发射机两两夹角；
- 预装目标角、阈值和本机动作参数；
- 当前接收机自己的动作与试探历史。

在线禁止：

- 距离读数和世界绝对坐标；
- 公共绝对方位或共同罗盘；
- 其他接收机测得的夹角；
- 跨接收机角度汇总或集中动作计算；
- 仿真真值、候选根和评估器输出回灌；
- 未来状态。

内部坐标可以用于推导、预装目标角和离线评估，但不等于无人机在线知道自己的绝对位置。

## 6. 证据链怎样理解

每问都按以下链条交付：

```text
Strategy Freeze
→ Model Contract
→ Production Implementation
→ Deterministic Program Gate
→ Official Result
→ Human Check Card
→ Paper Handoff
→ MID / FINAL REVIEW
```

不同证据的作用不能混淆：

| 证据 | 能证明什么 | 不能证明什么 |
|---|---|---|
| 解析推导 | 公式、局部秩或一阶结构 | 实机效果和任意初态全局结论 |
| 有限差分或第二实现 | 检查推导与实现是否一致 | 外部现实正确性 |
| 完整枚举 | 有限候选和排程没有遗漏 | 枚举域外的普适最优性 |
| 确定性回放 | 给定域内程序表现 | 随机环境、实机精度或全局收敛 |
| 负对照 | 检查器确实能够失败 | 所有未测试错误都不存在 |
| 人工核查 | 用户确认解释与证据可接受 | 自动提升数学结论强度 |

最终模型审查见 [FINAL_MODEL_REVIEW.md](review/FINAL_MODEL_REVIEW.md)。

## 7. 仓库目录

| 路径 | 内容 |
|---|---|
| `B题.pdf` | 原始赛题，唯一允许使用的 2022 来源 |
| `AGENTS.md` | 项目边界、冻结治理、模型路由和备份规则 |
| `CURRENT_STATE.md` | 当前阶段和全部正式状态字段 |
| `opening/` | Problem Map、先验、文献证据、方法地图和最终策略冻结 |
| `model_contract/` | 四个小问的正式输入、模型、边界和允许结论 |
| `src/` | 生产几何、身份枚举、本机控制器和离线评估器 |
| `tests/` | 四个小问的确定性 Program Gate |
| `results/` | Gate JSON、设计阶段结果和 Official Result |
| `experiments/` | Q2 路线设计时的有限枚举与局部审计脚本 |
| `review/` | 队友方案比较、中期审查、最终审查和补强记录 |
| `human_check/` | 用户人工核查卡与裁决记录 |
| `paper_handoff/` | 从模型执行到论文写作的逐问交接材料 |
| `literature/` | 已筛选中外论文卡片和 Q2 路线证据卡 |
| `writing_reference/` | Q1/Q2 解题说明、写作指南和仓库阅读指南 |
| `figures/` | 正式论文图表目录，目前等待论文阶段生成 |

## 8. 本地复核

### 8.1 环境

推荐使用项目本地虚拟环境。生产代码使用 Python 和 NumPy；Q1(2) 的高精度复核另外使用 `requirements-validation.txt` 中固定版本的 mpmath。

PowerShell 示例：

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install numpy
.venv\Scripts\python.exe -m pip install -r requirements-validation.txt
```

### 8.2 四个确定性 Gate

```powershell
.venv\Scripts\python.exe -m tests.q1_1_minimum_gate
.venv\Scripts\python.exe -m tests.q1_2_minimum_gate
.venv\Scripts\python.exe -m tests.q1_3_program_gate
.venv\Scripts\python.exe -m tests.q2_program_gate
```

重新运行 Gate 只是复算已经冻结的证据，不授权修改模型、阈值、参数或正式结果。若输出与仓库正式 JSON 不一致，应先报告差异并审计环境与实现，不能直接覆盖结果。

## 9. 论文写作入口

### 9.1 Q1

- [Q1 完整解法、公式与证据](writing_reference/Q1_DETAILED_SOLUTION_AND_EVIDENCE.md)
- [Q1 写作指南](writing_reference/Q1_WRITING_GUIDE_FOR_HUMAN_AND_AI.md)

### 9.2 Q2

- [Q2 完整解法、公式与证据](writing_reference/Q2_DETAILED_SOLUTION_AND_EVIDENCE.md)
- [Q2 问题分析与模型建立求解指南](writing_reference/Q2_PROBLEM_ANALYSIS_AND_MODEL_WRITING_GUIDE.md)

### 9.3 全文与仓库交接

- [安全写作总指南](writing_reference/SAFE_WRITING_GUIDE.md)
- [当前仓库阅读与使用指南](writing_reference/REPOSITORY_READING_GUIDE_FOR_HUMAN_AND_AI.md)：供队友、论文作者、复核者和辅助 AI 判断真源、追踪证据、避开历史旧路线并正确接手仓库。

论文写作阶段必须从 Official Result 和 Gate JSON 读取正式数字，不得凭记忆或手工改数。写作只能组织已有证据，不能擅自增强结论。

## 10. 推荐给辅助 AI 的启动提示

```text
这是一次 2022 B 题的 clean-room 模拟。请先读取 AGENTS.md、CURRENT_STATE.md 和 opening/07_STRATEGY_FREEZE.md，再读取当前小问的 model_contract、Official Result、Gate JSON、Paper Handoff 与 writing_reference。

B题.pdf 是唯一允许使用的 2022 来源。禁止读取 2023.md，禁止搜索或使用任何 2022 B 赛后题解、获奖论文、讲评、博客或 GitHub 解答。

模型已经最终冻结。不得新增模型家族、替换路线、修改参数和正式数字。禁止跨接收机上报或汇总夹角，禁止把内部坐标、仿真真值和评估器输出作为在线输入。

所有唯一性、收敛性和精度结论必须保留仓库规定的 LOCAL、NONDEGENERATE、TARGET_NEIGHBORHOOD、TRUSTED_BASELINE 或 DETERMINISTIC_REPLAY 边界。
```

## 11. Clean-room 规则

- `B题.pdf` 是唯一允许使用的 2022 来源；
- 不得打开或读取 `2023.md`；
- 不得搜索、引用或使用任何 2022 B 赛后论文、获奖论文、题解、讲评、博客、论坛或 GitHub 解答；
- 历年资料只能提供一般建模和写作经验，不能充当当前题答案；
- 如果遇到当前赛题赛后材料，立即停止读取并记录 `CONTAMINATION_BLOCKED`；
- 已淘汰的跨机互易两角、在线全图因子、集中 Route A/B 和依赖跨机合角的 2-tree 不得恢复。

## 12. 结论边界

本仓库已经证明和验证的是：在各问正式模型契约规定的局部域、非退化条件、固定排程和确定性回放条件下，冻结方案能够完成相应定位与编队调整任务。

本仓库没有声称：

- 所有构型全局唯一；
- 任意初态全局收敛；
- 仿真误差等于现实飞行精度；
- Q2 在没有尺度参考时可以恢复指定物理间距；
- 可信参考机存在偏差时结果不受影响；
- 人工核查能够替代理论和程序证据。

## 13. GitHub

项目仓库：<https://github.com/LHC728/8.23->

本项目采用普通增量提交和推送。每次 push 都是在远程分支上增加新的提交，不会覆盖或删除已有历史；禁止 force push、reset 历史或自动删除成果。
