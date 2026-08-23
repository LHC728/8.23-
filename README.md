# 8.23 数学建模模拟：2022 B 题纯方位无人机编队

本仓库记录一次全国大学生数学建模竞赛本科组 B 题的 clean-room 限时模拟。

当前状态：

- 开题已经完成；
- 最终策略已经冻结；
- 下一执行者为 Codex；
- 唯一施工蓝图是 [opening/07_STRATEGY_FREEZE.md](opening/07_STRATEGY_FREEZE.md)；
- 下一项工作是完成 Q1(1) 的双侧定夹角完整候选器和独立多根检查器。

## 1. 最推荐的阅读顺序

### 如果你只想快速看懂解法

1. 先看 [通俗解法与公式](SOLUTION_GUIDE.md)；
2. 再看 [最终施工蓝图](opening/07_STRATEGY_FREEZE.md)；
3. 最后按需查看 [问题地图](opening/01_PROBLEM_MAP.md) 和 [综合文献证据](opening/04_LITERATURE_EVIDENCE.md)。

### 如果你要继续推导、写代码或做实验

1. [AGENTS.md](AGENTS.md)：长期规则、clean-room 边界和不得重新开题的约束；
2. [CURRENT_STATE.md](CURRENT_STATE.md)：当前阶段、冻结方案和下一动作；
3. [opening/07_STRATEGY_FREEZE.md](opening/07_STRATEGY_FREEZE.md)：唯一施工真源；
4. [SOLUTION_GUIDE.md](SOLUTION_GUIDE.md)：小白友好的公式解释；
5. [opening/04_LITERATURE_EVIDENCE.md](opening/04_LITERATURE_EVIDENCE.md)：真正改变路线的文献证据；
6. [literature/international_paper_cards.md](literature/international_paper_cards.md) 和 [literature/chinese_paper_cards.md](literature/chinese_paper_cards.md)：论文卡片；
7. [review/TEAMMATE_METHOD_COMPARISON.md](review/TEAMMATE_METHOD_COMPARISON.md)：队友方案的同口径比较。

不要把 [opening/06_INNOVATION_AND_ROUTES.md](opening/06_INNOVATION_AND_ROUTES.md) 第 1～15 节中的旧 Route A/B 当成当前方案。它们依赖跨接收机汇总夹角，已经被用户裁决淘汰。当前只以 07 冻结文件为准。

## 2. 仓库目录说明

| 路径 | 作用 |
|---|---|
| B题.pdf | 当前赛题原文，也是唯一允许使用的 2022 来源 |
| AGENTS.md | Work 与 Codex 都必须遵守的长期规则 |
| CURRENT_STATE.md | 当前阶段、执行人、冻结路线和下一动作 |
| SOLUTION_GUIDE.md | 每一问的小白解法、公式解释和理论依据 |
| opening/01_PROBLEM_MAP.md | 任务卡、信息账本、数学结构和题意歧义 |
| opening/02_PRIOR_EXPERIENCE.md | 历年经验形成的当前题检查清单 |
| opening/03_LITERATURE_PLAN.md | clean-room 文献检索决策问题与计划 |
| opening/04_LITERATURE_EVIDENCE.md | 中外文献综合证据与迁移边界 |
| opening/05_BASELINE_AND_METHOD_MAP.md | Baseline、方法地图、参数和 Failure Map |
| opening/06_INNOVATION_AND_ROUTES.md | 创新候选与历史路线审计；含已失效旧路线 |
| opening/07_STRATEGY_FREEZE.md | 当前唯一有效的 Codex 施工蓝图 |
| literature/ | 已筛选的中文、国际论文卡片 |
| review/ | 队友方法比较和独立审查记录 |
| modeling/ | 后续数学推导与模型模块 |
| experiments/ | 后续最小实验和批量实验 |
| results/ | 后续结构化数值结果 |
| figures/ | 后续论文图表 |

## 3. 当前冻结方案的四问摘要

### Q1(1)

用三架已知发射机的夹角建立双侧定夹角圆弧，完整枚举交点，再用第三角回代。目标槽位附近 Jacobian 满秩时才能声明局部唯一。

### Q1(2)

零架额外发射机只能得到一条圆弧，所以不足。增加一架匿名发射机后，完整枚举其可能编号与位置分支；在小偏差和非退化条件下，理论最少数量为 1。第二匿名机只作拒绝后的稳健保护。

### Q1(3)

固定表 1 中 FY00–FY01 的 100 m 种子。FY04 与 FY07 交替使用本机两个角自举；局部精确最佳响应周期的谱半径为 0。随后固定 FY00、FY01、FY04、FY07，其余六架只用自己的角签名并行归槽。

### Q2

FY01、FY11、FY15 各自只测自己的三角形内角，并同步调整到等边外框。共同尺度保持自由。外框固定后，十二架跟随者各自使用三个角点形成的本机角签名并行归槽。

详细公式见 [SOLUTION_GUIDE.md](SOLUTION_GUIDE.md)。

## 4. 使用 AI 理解仓库时必须告诉它什么

建议每次新开 AI 对话时，先给出以下约束：

> 这是一次 2022 B 题的 clean-room 模拟。只允许把 B题.pdf 作为 2022 来源，不得读取 2023.md，也不得搜索或使用任何 2022 B 赛后论文、题解、讲评或标准路线。当前策略已冻结，唯一真源是 opening/07_STRATEGY_FREEZE.md。禁止跨接收机上报夹角，Q2 的 50 m 只是例示。请先区分在线决策信息与离线评估真值，再回答问题。

这段话非常重要。否则 AI 很容易：

- 偷用距离或真实坐标；
- 把别的无人机测得的角汇总起来；
- 把内部坐标误写成无人机实时可见的信息；
- 把旧 Route A/B 当成当前路线；
- 把局部收敛说成全局收敛；
- 搜到本题赛后答案，破坏 clean-room 模拟。

## 5. 推荐的 AI 提问模板

### 5.1 让 AI 用小白语言解释某一问

> 请只读取 AGENTS.md、CURRENT_STATE.md、SOLUTION_GUIDE.md 和 opening/07_STRATEGY_FREEZE.md。用“现实含义 → 变量 → 公式 → 每个符号解释 → 为什么成立 → 适用条件 → 失败情形”的顺序解释 Q1(1)。不要引入新模型，不要使用距离和跨机夹角。

把最后的 Q1(1) 换成 Q1(2)、Q1(3) 或 Q2 即可。

### 5.2 让 AI 检查公式是否正确

> 请以 opening/07_STRATEGY_FREEZE.md 为真源，独立推导下面的公式。先写假设和角度分支，再逐步求导；用一个数值有限差分检查器复核，但不要用数值接近代替解析证明。明确结论是局部还是全局，并检查是否使用了非法信息。

然后把要检查的公式粘贴在后面。

### 5.3 让 AI 写程序

> 请按 opening/07_STRATEGY_FREEZE.md 的 Codex Execution Order 工作。先实现统一 atan2 夹角和 Q1(1) 双侧圆弧完整候选器，再实现独立多根检查器。决策器输入只能含 receiver_id、transmitter_tokens、local_angles、local_action_history 和 schedule_step；真值必须放在独立评估器中。最小 Gate 未通过前不要批量仿真。

### 5.4 让 AI 做红队审查

> 请不要维护已有方案，按以下顺序攻击它：题目覆盖、信息边界、唯一性、多解、退化、局部/全局结论、有限差分实现、参数来源和独立验证。只有根本误读、非法信息、核心结构错误、某问无法回答或核心参数不可取得才建议 REOPEN；普通编码和参数问题不属于重新开题。

### 5.5 让 AI 帮忙写论文段落

> 请根据 SOLUTION_GUIDE.md 和 opening/07_STRATEGY_FREEZE.md，把 Q1(2) 改写成正式论文段落。必须保留 m_min=1 的局部适用条件、m=0 的必要性证明、匿名身份完整枚举和第二匿名机只是 fail-safe 的区别。不要把文献写成对本题公式的直接证明。

## 6. 怎样判断 AI 的解释是否可信

每次检查以下九点：

1. 是否明确接收机只能看到两架发射机在本机处形成的夹角？
2. 是否偷用了距离、绝对坐标、共同罗盘或未来状态？
3. 是否使用了另一架接收机测得的夹角？
4. 是否把表 1 真值输入在线决策器？
5. 是否保留 Q1(1) 的全部几何分支，而不是只报一个优化根？
6. 是否把 Q1(2) 的“局部最少为 1”误说成无条件全局唯一？
7. 是否说明 Q1(3) 的零谱结论对应精确局部最佳响应？
8. 是否说明 Q2 的收敛是目标相似类附近的局部横向收敛？
9. 是否给出与主计算不同的检查器和明确失败情形？

任何一项回答不清楚，都应要求 AI 返回原题和 07 文件重新审查。

## 7. 公式阅读速查

| 符号 | 含义 |
|---|---|
| $p_i$ | 第 $i$ 架无人机的实际位置，只用于推导或仿真真值 |
| $q_i$ | 第 $i$ 个目标槽位的内部坐标 |
| $h_{ab}^{(i)}$ | 无人机 $i$ 看到发射机 $a,b$ 的夹角 |
| $F_i$ | 无人机 $i$ 自己能够计算的角残差 |
| $J_i$ | 本机角残差对本机移动的 Jacobian |
| $\sigma_{\min}$ | Jacobian 最小奇异值，越接近 0 越容易退化 |
| $\kappa$ | 条件数，越大通常表示越敏感 |
| $\rho$ | 迭代线性化谱半径，小于 1 表示局部收缩 |
| $\delta$ | 本机有限差分试探距离 |
| $\eta,\lambda$ | 更新步长和阻尼 |
| $\mu$ | Q2 三角点角度更新增益 |
| $U_i$ | 第 $i$ 个槽位的局部认证区域 |

## 8. 当前最重要的待办

Codex 必须按以下顺序施工：

1. Q1(1) 双侧定夹角圆弧与完整候选；
2. 独立多根检查器和退化小例；
3. Q1(2) 全部 56 组合复算；
4. Q1(3) FY04/FY07 精确根和表 1 盲化回放；
5. Q2 三角点吸引域和十二槽位远端根；
6. 通过最小 Gate 后才做批量扰动、对照和图表。

详细的 Kill / Fallback 规则见 [opening/07_STRATEGY_FREEZE.md](opening/07_STRATEGY_FREEZE.md)。

## 9. Clean-room 与项目治理

- B题.pdf 是唯一允许的 2022 来源。
- 不得打开或读取 2023.md。
- 不得搜索、引用或使用任何 2022 B 赛后论文、获奖论文、题解、讲评、博客或标准路线。
- 历年资料只能作为建模经验先验，不能作为当前题答案。
- Codex 不得擅自重新开题。
- 若发现 FATAL_MODEL_MISMATCH，只能提交 REOPEN_REQUEST，在用户批准前不得替换主线。
- 已淘汰的跨机互易两角、在线全图因子、集中 Route A/B 和 2-tree fallback 不得恢复。

## 10. 项目链接

GitHub 目标仓库：

https://github.com/LHC728/8.23-

仓库完成推送后，队友可以从 README 开始阅读，再把具体文件交给 AI 按第 5 节的模板解释。
