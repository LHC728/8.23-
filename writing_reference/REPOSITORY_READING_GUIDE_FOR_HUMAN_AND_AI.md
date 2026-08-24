# 当前仓库阅读与使用指南：供队友、论文作者和 AI 使用

> GitHub 仓库：[LHC728/8.23-](https://github.com/LHC728/8.23-)
>
> 本文不是第二份 README。README 负责快速导航；本文负责解释怎样判断文件权威性、怎样追踪每一问的证据、怎样避开历史旧路线，以及怎样让 AI 安全地读取本项目。
>
> 文档状态：Q1、Q2、Q2 端到端补强和最终模型审查均已完成并通过人工裁决；模型已在明示适用边界内最终冻结。论文阶段尚未由本指南擅自启动。

## 1. 先回答：README 和本指南分别有什么用？

### README 适合解决的问题

- 这个仓库研究什么？
- 当前做到哪一步？
- Q1、Q2 的最终方案是什么？
- 最重要的文件在哪里？
- 怎样运行四个确定性 Gate？

### 本指南适合解决的问题

- 同一个结论应该依次检查哪些文件？
- 哪些文件是最终真源，哪些只是历史记录？
- JSON、测试、正式结果和人工核查卡分别证明什么？
- 论文作者、程序复核者和辅助 AI 应使用哪条阅读路线？
- 怎样防止 AI 恢复旧方案、偷用真值或扩大结论？

因此：第一次进入仓库先看 [README](../README.md)；需要真正理解、复核或交接时，再看本指南。

## 2. 当前项目状态

查看项目状态的第一入口是 [CURRENT_STATE.md](../CURRENT_STATE.md)，不要依据聊天记忆判断。

当前关键状态为：

```text
STRATEGY_STATUS = FROZEN
Q1_1_FINAL_FREEZE = PASS
Q1_2_FINAL_FREEZE = PASS
Q1_3_FINAL_FREEZE = PASS
Q1_MID_REVIEW_HUMAN_VERDICT = PASS
Q2_FINAL_FREEZE = PASS
Q2_END_TO_END_HUMAN_RECONFIRMATION = PASS
FINAL_MODEL_REVIEW_HUMAN_VERDICT = PASS
FINAL_MODEL_FREEZE = PASS
REOPEN_REQUIRED = NO
```

这意味着：

1. 四个问题都有正式数学路线、程序实现、Gate、正式结果和人工裁决；
2. Q2 曾发现端到端验证缺口，但已经补强并关闭，修复历史保留在审查文件中；
3. 当前不需要重新开题或更换模型；
4. 后续写作只能使用已冻结公式、参数、正式数字和结论边界；
5. “最终冻结”不等于已经证明全局定理，也不等于完成现实飞行实验。

## 3. 文件权威性：冲突时听谁的？

建议按以下优先级判断：

```text
B题.pdf 的原题要求
        ↓
AGENTS.md 的长期规则、clean-room 和信息边界
        ↓
CURRENT_STATE.md 的当前项目状态
        ↓
opening/07_STRATEGY_FREEZE.md 的冻结数学路线
        ↓
model_contract/ 的每问正式接口与失败语义
        ↓
src/、tests/ 和 results/*.json 的实际程序证据
        ↓
results/*/Q*_OFFICIAL_RESULT.md 的正式结论与数字
        ↓
review/ 的审查裁决与允许结论强度
        ↓
human_check/ 的人工裁决
        ↓
paper_handoff/ 和 writing_reference/ 的解释与写作接口
        ↓
早期 opening 候选、历史比较、旧提示词和聊天记录
```

需要区分两种“真源”：

- 数学路线真源：[opening/07_STRATEGY_FREEZE.md](../opening/07_STRATEGY_FREEZE.md)；
- 最终允许的证据与结论强度：[review/FINAL_MODEL_REVIEW.md](../review/FINAL_MODEL_REVIEW.md)。

如果两者与通俗解法、Paper Handoff 或旧审查记录冲突，不能自行折中，必须回到模型契约、正式结果和最终审查查明原因。

## 4. 五分钟阅读路线

### 4.1 队友只想知道“最终用了什么方法”

按顺序阅读：

1. [README](../README.md) 的“四问最终方案”；
2. [小白版逐问解法](../SOLUTION_GUIDE.md)；
3. [Q1 详细解法与证据](Q1_DETAILED_SOLUTION_AND_EVIDENCE.md)；
4. [Q2 详细解法与证据](Q2_DETAILED_SOLUTION_AND_EVIDENCE.md)。

读完后应能说清：每问的输入、观测、未知量、核心公式、求解步骤和结论范围。

### 4.2 论文作者准备写正文

按顺序阅读：

1. [安全写作指南](SAFE_WRITING_GUIDE.md)；
2. [Q1 写作指南](Q1_WRITING_GUIDE_FOR_HUMAN_AND_AI.md)；
3. [Q2 问题分析与模型写作指南](Q2_PROBLEM_ANALYSIS_AND_MODEL_WRITING_GUIDE.md)；
4. 对应的 `paper_handoff/`；
5. 对应的 Official Result；
6. [最终模型审查](../review/FINAL_MODEL_REVIEW.md)；
7. 已筛选的 `literature/` 文献卡片。

写作时不能只看 Paper Handoff。它是叙事接口，不是全部数学证据。

### 4.3 程序复核者要检查某一问

按固定链条阅读：

```text
原题
→ Strategy Freeze 对应章节
→ Model Contract
→ src 生产实现
→ tests 确定性 Gate
→ results JSON
→ Official Result
→ Human Check Card
→ Review
```

重点不是看最后有没有 `PASS`，而是确认 PASS 是否由实际计算、阈值、事件记录和负对照共同产生。

### 4.4 AI 接手仓库

至少先读：

1. [AGENTS.md](../AGENTS.md)；
2. [CURRENT_STATE.md](../CURRENT_STATE.md)；
3. [Strategy Freeze](../opening/07_STRATEGY_FREEZE.md)；
4. 本次任务涉及的 Model Contract、Official Result 和 Review；
5. 若涉及写作，再读相应写作指南和 Paper Handoff。

AI 未完成这一步，不应回答“当前方案是什么”或直接修改项目。

## 5. 各目录分别放什么？

| 路径 | 作用 | 阅读提醒 |
|---|---|---|
| `B题.pdf` | 当前赛题原文 | 唯一允许使用的 2022 来源 |
| `AGENTS.md` | 长期规则、信息边界、冻结治理、模型路由和备份规则 | 所有执行者必须先读 |
| `CURRENT_STATE.md` | 当前阶段、各 Gate 和人工裁决状态 | 判断项目现状的第一入口 |
| `opening/` | 问题地图、文献证据、候选路线和最终冻结蓝图 | 01～06 主要记录形成过程；07 是正式数学真源 |
| `model_contract/` | 每问输入、观测、未知量、公式、输出和失败语义 | 是规范与代码之间的合同 |
| `src/` | 生产几何、枚举、调整和评估实现 | 在线控制器与离线评估器必须区分 |
| `tests/` | 确定性 Gate、独立复核、负对照和信息防火墙 | 检查是否真的调用生产实现 |
| `results/` | Gate JSON、路线设计数据和 Official Result | JSON 是细证据，Official Result 是允许引用的正式结果 |
| `human_check/` | 人能够理解和裁决的检查卡 | 人工 PASS 不能替代程序证据 |
| `review/` | Q1 中期审查、Q2 补强和最终模型审查 | 用于确认缺口、修复和结论强度 |
| `paper_handoff/` | 每问向论文正文移交的公式、数字和图表建议 | 不得擅自增强结论 |
| `literature/` | 已筛选中外论文卡片 | 文献支持一般原理，不直接证明本题特定编号和数字 |
| `writing_reference/` | 详细解法、写作指南和本阅读指南 | 面向人和辅助 AI 的解释层 |
| `experiments/` | Q2 路线设计阶段的有限枚举与局部审计 | 不是当前在线控制器 |
| `modeling/` | 详细推导和执行提示记录 | 提示词不是最终状态真源 |

## 6. 每一问的正式文件包

### 6.1 Q1(1)

| 层次 | 文件 |
|---|---|
| 模型契约 | `model_contract/Q1_1_MODEL_CONTRACT.md` |
| 生产实现 | `src/q1_1_geometry.py` |
| 程序 Gate | `tests/q1_1_minimum_gate.py` |
| 原始结果 | `results/q1_1/q1_1_minimum_gate.json` |
| 正式结论 | `results/q1_1/Q1_1_OFFICIAL_RESULT.md` |
| 人工核查 | `human_check/Q1_1_HUMAN_CHECK_CARD.md` |
| 论文交接 | `paper_handoff/Q1_1_PAPER_HANDOFF.md` |

主结论：生成双侧定夹角圆的全部有限候选，用第三角逐候选回代；只有在目标局部域内候选唯一且 Jacobian 满秩时，才给出局部唯一性判定。

### 6.2 Q1(2)

| 层次 | 文件 |
|---|---|
| 模型契约 | `model_contract/Q1_2_MODEL_CONTRACT.md` |
| 生产实现 | `src/q1_2_identity.py` |
| 程序 Gate | `tests/q1_2_minimum_gate.py` |
| 原始结果 | `results/q1_2/q1_2_minimum_gate.json` |
| 正式结论 | `results/q1_2/Q1_2_OFFICIAL_RESULT.md` |
| 人工核查 | `human_check/Q1_2_HUMAN_CHECK_CARD.md` |
| 论文交接 | `paper_handoff/Q1_2_PAPER_HANDOFF.md` |

主结论：零架额外发射机不足；一架编号未知的发射机在明示局部、非退化条件下，经完整编号与几何分支枚举可以联合辨认身份和位置，因此局部最少数为 1。第二匿名机是证据不足时的冗余发射备用方案。

### 6.3 Q1(3)

| 层次 | 文件 |
|---|---|
| 模型契约 | `model_contract/Q1_3_MODEL_CONTRACT.md` |
| 核心推导 | `modeling/Q1_3_CORE_DERIVATION.md` |
| 生产控制 | `src/q1_3_adjustment.py` |
| 离线评估 | `src/q1_3_evaluator.py` |
| 程序 Gate | `tests/q1_3_program_gate.py` |
| 原始结果 | `results/q1_3/q1_3_program_gate.json` |
| 正式结论 | `results/q1_3/Q1_3_OFFICIAL_RESULT.md` |
| 人工核查 | `human_check/Q1_3_HUMAN_CHECK_CARD.md` |
| 论文交接 | `paper_handoff/Q1_3_PAPER_HANDOFF.md` |

主结论：固定 FY00、FY01；FY04、FY07 按预编排时序严格使用各自本机夹角交替建锚；随后固定四锚，其余六架无人机分别归槽。表 1 真值只进入观测生成和离线评估。

Q1 三小问的总装结论还要阅读：

- `review/Q1_MID_REVIEW.md`；
- `human_check/Q1_MID_REVIEW_HUMAN_CHECK_CARD.md`。

### 6.4 Q2

| 层次 | 文件 |
|---|---|
| 模型契约 | `model_contract/Q2_MODEL_CONTRACT.md` |
| 生产几何 | `src/q2_geometry.py` |
| 生产控制 | `src/q2_adjustment.py` |
| 离线评估 | `src/q2_evaluator.py` |
| 程序 Gate | `tests/q2_program_gate.py` |
| 原始结果 | `results/q2/q2_program_gate.json` |
| 正式结论 | `results/q2/Q2_OFFICIAL_RESULT.md` |
| 端到端补强 | `review/Q2_END_TO_END_REMEDIATION.md` |
| 人工核查 | `human_check/Q2_HUMAN_CHECK_CARD.md` |
| 论文交接 | `paper_handoff/Q2_PAPER_HANDOFF.md` |

当前正式路线只有一条：

```text
FY11/FY15 可信无偏差基线 4d*
→ FY04/FY03 严格本机交替建锚
→ 固定 FY03/FY04/FY11/FY15
→ 其余 11 架使用各自本机六维纯方位观测归槽
→ 离线验收实际 15 节点终态的 30 条边和 12 条直线
```

需要同时记住：

- 可信基线是用户批准的附加条件，不是原题明示事实；
- 整体平移、旋转和镜像仍自由；
- 在线控制器不知道可信种子的绝对坐标；
- 没有跨接收机夹角汇总；
- 结论只覆盖可信基线、目标邻域、非退化和确定性回放；
- 不能宣称任意初态全局收敛或现实飞行精度。

## 7. 怎样理解“证据链闭合”？

一条可信结论至少应能完成以下追踪：

```text
原题到底要求什么
        ↓
冻结路线规定使用什么信息和数学机制
        ↓
Model Contract 把机制写成可执行接口
        ↓
src 实际实现这些接口
        ↓
tests 用可失败检查、独立复核和负对照进行验证
        ↓
JSON 保存原始数值、阈值、事件和失败情况
        ↓
Official Result 只提取证据允许支持的结论
        ↓
Review 检查是否漏问、越界或过度声称
        ↓
Human Check Card 由用户确认理解并接受结论范围
```

不能把以下内容单独当成充分证据：

- JSON 里一个孤立的 `PASS`；
- AI 说“公式看起来正确”；
- 主程序与检查器调用完全相同的核心函数；
- 只展示一个成功案例；
- 只验证理想格点而没有验证实际控制终态；
- 用户人工通过，但程序没有实际计算证据。

## 8. Q2 端到端修复历史为什么必须看？

最终模型审查曾发现：早期 Q2 分阶段检查都通过，但最终 30 边和 12 线验收使用的是理想格点，而不是完整控制回放得到的实际终态。

这不是核心数学路线错误，因此没有重开模型；但它是重大证据链缺口。修复后：

- FY03/FY04 的实际建锚终点直接传给后续控制；
- 11 架跟随者使用实际四参考终点；
- 33 个端到端确定性案例全部通过；
- 实际 15 节点终态接受 30 边和 12 线检查；
- 理想锚点重置和人为破坏终态都会被负对照拒绝。

因此应同时阅读：

1. [Q2 正式结果](../results/q2/Q2_OFFICIAL_RESULT.md)；
2. [Q2 端到端补强报告](../review/Q2_END_TO_END_REMEDIATION.md)；
3. [最终模型审查](../review/FINAL_MODEL_REVIEW.md)。

保留这段修复历史不是“项目有问题”，而是为了证明最终结论经过了可追溯的纠错。

## 9. 哪些文件是历史记录，不能执行？

以下文件有研究价值，但不是当前执行路线：

### `opening/06_INNOVATION_AND_ROUTES.md`

保存 Stage 5 的候选路线、允许跨接收机角汇总的旧假设、自由尺度 Q2 候选及创新筛选。文件顶部已经标明 **HISTORICAL / 禁止执行**。

### `review/TEAMMATE_METHOD_COMPARISON.md`

保存队友方案比较和当时的路线排名。其中“当前路线”等措辞是历史语境，不能覆盖最终冻结路线。

### `review/Q2_FINAL_ROUTE_PROPOSAL.md`

保存 FY11/FY15 条件获批前的路线提案。文件中的 `Q2_REOPEN_REQUIRED = YES` 和 `HUMAN_APPROVAL_REQUIRED = YES` 是当时状态；现在已完成批准、实施和冻结。

### Strategy Freeze 中的正式 fallback

`opening/07_STRATEGY_FREEZE.md` 中标为 **Formal fallback only: free-similarity route** 的部分不是废弃垃圾，而是正式备用路线。只有可信尺度基线条件被撤回时，才能按治理规则启用；平时不得与当前主路线混用。

判断原则：

> 历史文件可以解释“为什么没有采用某方案”，但不能决定“现在应执行什么”。

## 10. 在 GitHub 网页上怎样查看？

### 10.1 第一次进入

1. 打开仓库主页；
2. 确认分支是 `main`；
3. 查看最新提交哈希和提交时间；
4. 打开 `CURRENT_STATE.md`；
5. 再按本指南选择对应阅读路线。

若别人提供的提交哈希与远程 `main` 不同，应先确认是否存在尚未推送的本地提交。

### 10.2 查看 Markdown

- 使用页面目录跳转章节；
- 相对链接可以继续打开仓库内文件；
- 公式由 GitHub 数学渲染器显示；
- 若看到 LaTeX 原码或红色公式报错，应检查公式定界符和不兼容宏，而不是猜公式含义。

### 10.3 查看 JSON

推荐顺序：

1. 先看对应 Official Result，知道要找什么；
2. 在 JSON 中搜索数值、阈值、事件数和失败记录；
3. 回到测试脚本查这些字段怎样生成；
4. 回到生产实现确认测试是否调用真实代码。

### 10.4 查看提交历史

GitHub 页面中的 `commits` 可以看到每次检查点。普通 push 是在历史后面增加提交，不会覆盖旧版本。除非执行 force push 或改写历史，否则旧提交仍可追溯。

## 11. 下载和本地查看

不使用 Git 时，可以选择：

```text
Code → Download ZIP
```

使用 Git 时，在 PowerShell 中执行：

```powershell
git clone https://github.com/LHC728/8.23-.git
Set-Location '8.23-'
git branch --show-current
git rev-parse HEAD
git status --short
```

说明：

- `git rev-parse HEAD` 显示当前本地提交；
- `git status --short` 没有输出，表示工作树通常是干净的；
- 工作树干净不等于远程一定同步；
- 可用 `git fetch origin` 后比较本地 HEAD 与 `origin/main`。

不要使用 `reset --hard`、force push 或自动删除未跟踪文件来“清理”仓库。

## 12. 怎样复现现有 Gate？

如果项目本地虚拟环境存在，可在仓库根目录执行：

```powershell
.\.venv\Scripts\python.exe -m tests.q1_1_minimum_gate
.\.venv\Scripts\python.exe -m tests.q1_2_minimum_gate
.\.venv\Scripts\python.exe -m tests.q1_3_program_gate
.\.venv\Scripts\python.exe -m tests.q2_program_gate
```

如果没有 `.venv`，先查看 `requirements-validation.txt`，在独立虚拟环境中安装通用依赖。

运行前后检查：

1. 命令退出码；
2. JSON 是否由本次运行更新；
3. 是否产生新的未提交修改；
4. 原始值与阈值是否对应；
5. 负对照是否真的会失败；
6. 测试是否调用生产实现；
7. 在线控制器是否读取了离线真值或评估器结果。

普通论文作者不必重跑全部程序；复核者和准备修改实现的人才需要进入这一层。

## 13. 怎样把仓库交给 AI？

### 13.1 AI 能访问本地仓库时

可直接复制以下提示词：

```text
这是一个已经完成最终模型冻结的数学建模本地仓库。回答前必须先读取仓库真实状态，不得只凭聊天记忆。

先读取：
- AGENTS.md
- CURRENT_STATE.md
- opening/07_STRATEGY_FREEZE.md
- review/FINAL_MODEL_REVIEW.md
- 本任务对应的 MODEL_CONTRACT、OFFICIAL_RESULT 和 PAPER_HANDOFF

规则：
1. B题.pdf 是唯一允许使用的 2022 来源；禁止读取 2023.md，禁止搜索或使用任何 2022 B 赛后题解、优秀论文、讲评、博客或 GitHub 解答。
2. 不得修改冻结模型、参数、正式数字或结论强度。
3. 禁止跨接收机夹角汇总；仿真真值和内部坐标只能用于离线评估。
4. opening/06、TEAMMATE_METHOD_COMPARISON 和 Q2_FINAL_ROUTE_PROPOSAL 是历史记录，不得作为当前执行路线。
5. Q2 当前路线只能是 FY11/FY15 可信基线、FY04/FY03 本机交替建锚、四参考下 11 机归槽。
6. 局部、非退化、可信基线和确定性回放结论不得扩大为全局或现实飞行保证。

请先报告：
CURRENT_HEAD =
WORKTREE_STATUS =
SOURCE_OF_TRUTH =
FILES_READ =
CONFLICT_FOUND =

然后再完成我交给你的具体任务。
```

### 13.2 AI 不能访问本地仓库时

按任务提供最小上下文，不要无差别粘贴整个仓库。

#### 解释某一问

- `AGENTS.md` 的 clean-room 和信息边界；
- `CURRENT_STATE.md`；
- Strategy Freeze 对应章节；
- 对应详细解法和 Model Contract；
- 对应 Official Result。

#### 审查某一问

再增加：

- 对应 `src`；
- 对应 `tests`；
- 对应 JSON；
- 对应 Human Check Card 和 Review。

#### 辅助论文写作

再增加：

- 对应写作指南；
- Paper Handoff；
- 已筛选 paper cards；
- 最终模型审查。

### 13.3 要求 AI 输出来源字段

建议要求 AI 在重要任务末尾报告：

```text
REPO_FILES_READ =
SOURCE_OF_TRUTH_USED =
ONLINE_INFORMATION_USED =
OFFLINE_ONLY_INFORMATION =
FORMAL_RESULT_SOURCE =
CLAIM_SCOPE =
NEW_MODEL_INTRODUCED = YES / NO
HISTORICAL_ROUTE_USED = YES / NO
CONFLICT_FOUND =
```

## 14. 怎样判断 AI 是否读错了仓库？

出现以下任一情况，应立即暂停：

1. 没读 `CURRENT_STATE.md` 就宣布项目阶段；
2. 把 `opening/06` 或队友比较中的旧路线称为当前方案；
3. 把 Q2 写成“三个外角点等角化后 12 架归槽”；
4. 没有说明 FY11/FY15 可信基线是批准的附加条件；
5. 让无人机在线读取真实坐标、距离、仿真真值或评估器结果；
6. 汇总不同接收机测得的夹角；
7. Q1(1) 只保留求解器第一个根；
8. 把 Q1(2) 的局部最少数 1 写成无条件全局结论；
9. 把 Q1(3) 或 Q2 的一阶零谱写成有限步精确到位；
10. 把确定性仿真误差写成现实飞行精度；
11. 用“某篇论文已经证明本题编号选择”代替本题推导和 Gate；
12. 删除 Q2 端到端缺口及其修复记录；
13. 读取或搜索污染性的 2022 B 赛后材料。

## 15. 论文阶段怎样使用仓库？

论文中的每个主要结论应回答四个问题：

1. 公式来自哪里：解析推导、模型契约还是文献？
2. 数字来自哪里：哪个 Official Result 或 JSON 字段？
3. 验证来自哪里：解析、独立复核、负对照还是端到端回放？
4. 允许说到什么强度：局部、非退化、可信基线还是确定性回放？

推荐流程：

```text
详细解法理解数学
→ 写作指南搭建章节
→ Paper Handoff 提取叙事接口
→ Official Result 提取正式数字
→ JSON 核对数字来源
→ paper cards 安排引用
→ Final Model Review 限制结论强度
→ 人工检查公式、图表、引用和数字
```

不得为了文字更漂亮而改变：

- 参考机编号；
- 观测分量；
- 控制参数；
- Gate 阈值；
- 正式实验数量；
- 失败域；
- 附加条件；
- 局部与全局的结论边界。

## 16. Clean-room 边界

- `B题.pdf` 是唯一允许使用的 2022 来源；
- 不得打开或读取 `2023.md`；
- 不得搜索、引用或使用 2022 B 赛后题解、优秀论文、专家讲评、博客、论坛或 GitHub 解答；
- 历年资料只能提供一般建模与写作经验，不能替代当前题分析；
- 文献只用于一般理论、参数依据和验证方法；
- 若搜索中遇到明显的当前赛题赛后材料，应停止读取并记录 `CONTAMINATION_BLOCKED`。

## 17. 阅读完成检查表

读者能够回答以下问题，才算真正看懂仓库：

- [ ] 当前 Git HEAD 和远程 `main` 是否一致？
- [ ] 项目状态应去哪个文件确认？
- [ ] 数学路线和最终结论强度分别由哪些文件决定？
- [ ] Q1(1) 为什么不能只保留第一个根？
- [ ] Q1(2) 的 $m_{\min}=1$ 为什么只是一条局部结论？
- [ ] Q1(3) 如何保证没有跨接收机角度汇总？
- [ ] Q2 为什么必须额外处理尺度？
- [ ] FY11/FY15、FY04/FY03 和四参考机分别承担什么角色？
- [ ] Q2 的实际端到端终态在哪里验收？
- [ ] 哪些旧文件只能作为历史记录？
- [ ] 正式 fallback 在什么条件下才能启用？
- [ ] 哪些结论禁止写成全局保证或现实飞行精度？

## 18. 最后一句话

阅读这个仓库时，不要只问“哪个 Markdown 写得最像论文”，而要问：

> 这条结论能否沿着“原题 → 冻结规范 → 模型契约 → 生产实现 → 确定性 Gate → 原始 JSON → 正式结果 → 独立审查 → 人工裁决”完整追溯？

能完整追溯，并且没有越过信息边界和结论边界，才是当前项目可以信任、复现和写入论文的内容。
