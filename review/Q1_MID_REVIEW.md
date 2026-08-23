# Q1 中期审查报告

## 1. Repo Snapshot

```text
HEAD = 2507bc4ebd54a716daba85de2e708d59970aa6f9
origin/main = 2507bc4ebd54a716daba85de2e708d59970aa6f9
BRANCH = main
WORKTREE_AT_START = CLEAN
```

本审查只读取 `B题.pdf` 作为 2022 题面来源；未读取 `2023.md`、任何 2022 B 赛后材料，也未运行三个历史程序验收。

## 2. Original Q1 Coverage Matrix

| 原题要求 | 覆盖结论 | 主要证据 |
| --- | --- | --- |
| Q1(1)：FY00 加两架已知、无偏差发射机的被动定位模型 | PASS | `model_contract/Q1_1_MODEL_CONTRACT.md`；完整双侧候选、全角回代与局部秩 |
| Q1(2)：FY00/FY01 加若干匿名发射机的最少数量 | PASS（局部条件） | `m=0` 圆弧反例；392 次编号假设、局部秩和正观测分离度 |
| Q1(3)：表 1 下的具体多轮调整 | PASS（确定性回放） | FY04/FY07 五个宏周期、四锚阶段、实际排程审计 |
| Q1(3)：FY00 每轮参加、外围发射机不超过 3、接收机不发射 | PASS | Q1(3) 事件日志和排程故障注入 |
| Q1(3)：最终正九边形、半径 100 m | PASS（表 1 目标邻域） | 半径/圆心角/槽位误差的离线评估 |

## 3. Q1(1) → Q1(2) → Q1(3) Interface Audit

Q1(1) 的完整三发射机候选器是 Q1(2) 每一编号假设的内层几何求解器；Q1(2) 保留离散编号枚举，Q1(3) 因排程已明确发射机编号而合理关闭该匿名层。三问均使用同一无符号 `atan2` 纯方位内核、FY00 圆心/FY01 固定相位的目标坐标约定和“候选/局部判定/拒绝”的纪律。接口一致，结论未被后问扩大。

## 4. Information Boundary Audit

- Q1(1) 在线接口仅接收本机三条两两夹角；
- Q1(2) 的生产枚举器 AST 审计拒绝真值身份、接收机真位置、距离和跨接收机角输入；非法源代码负对照被拒绝；
- Q1(3) 控制器只处理本机残差、局部试探位移和本机历史；`ObservationPlant` 保存仿真真值，离线评估器不回灌；事件日志确认每次观测属于当前移动接收机；
- 表 1 的 FY02--FY09 坐标只进入仿真观测生成和事后评估，不作为在线动作输入。

结论：`INFORMATION_BOUNDARY = PASS`。未发现跨接收机夹角汇总、距离/绝对方位偷用、真值回灌或集中动作计算。

## 5. Q1(1) Mathematical Verdict

双侧定夹角圆分支、任意两约束的全部圆交点、三条原始 `atan2` 角回代和重根去除形成完整有限候选生成。镜像多根被保留，相切、近退化和 `0/pi` 边界均有显式失败语义。局部 `rank DG(q_r)=2` 只用于槽位域内的局部唯一性判定。

**裁决：PASS。** 可声称“精确、非退化、局部槽位域中的完整候选与条件性局部唯一性”；不得声称全平面唯一或任意初态恢复。

## 6. Q1(2) Mathematical Verdict

`m=0` 的同角圆弧反例否定零匿名发射机。`m=1` 对 8 个接收机、56 个真编号场景和 392 个编号假设完整枚举；56 个正确局部根被找回，350 条候选中保留 294 条远端/错误编号候选，局部域内错误编号候选为零。`3×2` Jacobian 满列秩、20° 最小编号观测分离度及 1 m 域正的保守下界共同限制结论；`m=2` 的 42 个有序排列只是冗余发射备用方案。

**裁决：PASS。** `m_min=1` 只允许在自身编号已知、目标邻域、非退化且扰动小于分离裕度的局部条件下表述；1 m 是确定性判据示例，不是题给误差上界，也不是全局位置单射定理。

## 7. Q1(3) Mathematical Verdict

FY04/FY07 的严格本地双节点交替校正建锚采用四个导数块、精确最佳响应和完整周期一阶谱；解析、自动微分与有限差分三路对照支持目标点周期谱半径为零。随后四锚固定、六机并行本机更新，预置目标纯方位观测向量独立于自举后的实际锚点。表 1 确定性回放的最大半径误差为 `1.954e-7 m`、最大相邻圆心角误差为 `2.421e-9 rad`、最大目标位置误差为 `2.935e-7 m`。

**裁决：PASS。** 只允许“表 1、目标邻域、非退化的确定性回放成功”及“精确最佳响应周期的一阶谱半径为零”；不得称为任意初态全局收敛、现实飞行精度或 FY04/FY07 对所有排程的全局最优。

## 8. Evidence--Claim Matrix

| Claim | Evidence | Evidence type | Allowed strength | Prohibited strength | Source file |
| --- | --- | --- | --- | --- | --- |
| Q1(1) 完整有限候选 | 双侧圆、全部交点、三角回代、独立多初值根集 | 解析推导 + 同源第二实现 | 局部非退化候选完备 | 全局唯一 | `src/q1_1_geometry.py`; `results/q1_1/q1_1_minimum_gate.json` |
| Q1(2) `m=0` 不足 | 同角圆弧反例 | 结构性反例 | 零匿名机不可辨识 | 任意噪声下的统计结论 | `src/q1_2_identity.py` |
| Q1(2) `m=1` 局部充分 | 全枚举、秩、观测分离度、高精度复算 | 穷举 + 局部解析/数值证书 | 明示局部条件下的最少数 | 全平面 `m_min=1` | `results/q1_2/q1_2_minimum_gate.json` |
| Q1(3) 表 1 队形调整 | 事件日志、独立解析基准求解器、几何评估 | 确定性仿真回放 + 故障注入 | 表 1 目标邻域回放 | 实机或全局收敛 | `results/q1_3/q1_3_program_gate.json` |
| FY04/FY07 选择 | 导数块三路核验与同口径局部谱对照 | 局部线性化 + 对照 | 当前目标点的局部优势 | 一般最优排程 | `src/q1_3_adjustment.py` |

同一接收机的第三角和留出角约束检验均不是独立外部验证；数值收敛不构成全局唯一证明；表 1 回放不构成实机试验；文献只提供结构依据，不逐式证明本题公式；Sol 裁决不能代替确定性证据。

## 9. Innovation Verdict

1. **完整候选与拒绝机制：PASS。** 它修复单根数值求解掩盖多解的基线缺口，可称为“候选完备与局部判定框架”，不应虚构为新求解器。
2. **匿名编号--连续位置联合可辨识：PASS。** 编号被明确建为离散未知量，局部编号观测分离度和 Jacobian 与全枚举共同处理误配；`m=2` 与 `m=1` 的局部最少结论角色不冲突。
3. **严格本地双节点交替校正建锚：PASS。** 它解决仅 FY00/FY01 的二维启动不可辨识；每台移动机只用本机角，FY04/FY07 的局部零谱有解析、三路导数和同口径对照证据。

未见为了装饰而堆叠算法、同一模型换名、无法验证的复杂性或未经支持的参数主张。

## 10. Terminology Standard

Q1 正式 Markdown 已采用以下论文用语：纯方位观测向量、三维纯方位观测向量、编号假设间的观测分离度、编号局部可辨识性判据、二维主观测分量组合、留出角约束检验、冗余发射备用方案、双节点交替校正建锚、独立数值复核器、独立解析基准求解器、仿真观测生成环境、仿真真值、在线信息隔离约束、几何不变性检验和同口径对照试验。状态键、文件路径和 Python/JSON 标识符保持原样。

## 11. Formula Rendering Audit

```text
FORMULA_RENDERING_AUDIT = PASS
BROKEN_MACRO_FOUND = YES (历史 `\operatorname{atan2}` 与两个损坏的 `\varepsilon`)
BROKEN_MACRO_FIXED = YES
FORMULA_MEANING_CHANGED = NO
```

Q1 叙述性公式已使用 `\mathrm{atan2}`；无新增控制字符、标题公式或代码块中的 LaTeX。数值、变量、状态键与实现公式含义未改动。

## 12. Findings by Severity

```text
FINDING_ID = Q1-MR-MINOR-01
SEVERITY = MINOR
FILE = Q1 正式 Markdown（详见本次 diff）
LINE = N/A（术语/渲染性修正）
ISSUE = 英中文术语混用、历史宏与损坏 epsilon 字符影响学术呈现。
EVIDENCE = Markdown 静态检索与逐段语义核对。
CONSEQUENCE = 不改变模型或数值；可能误导论文读者对证据性质的理解。
REQUIRED_ACTION = 已完成非语义中文术语和公式渲染修正。
MODEL_CHANGE_REQUIRED = NO
REOPEN_REQUIRED = NO
```

未发现 FATAL 或 MAJOR。

## 13. Allowed Claims

- Q1(1)：精确、非退化、局部槽位域内的完整有限候选与条件性局部唯一性；
- Q1(2)：明确局部条件下 `m_min=1`，`m=2` 仅为冗余备用；
- Q1(3)：表 1、目标邻域、非退化确定性回放；精确 FY04/FY07 最佳响应周期的一阶谱半径为零；
- Q1 三项贡献：候选完备与拒绝、匿名编号联合局部可辨识、严格本地双节点交替建锚。

## 14. Prohibited Claims

全局唯一、全平面最少一架、任意初态收敛、未建模噪声鲁棒、实机微米精度、FY04/FY07 对所有排程全局最优，以及任何在线跨接收机角/真值/离线评估输出的使用。

## 15. Remaining Known Limitations

Q1(1) 的槽位半径未由该最小验收确定；Q1(2) 的 1 m 是确定性证书示例；Q1(3) 的有限差分、阻尼和五个宏周期只由表 1 回放支持。留出角约束检验为同源本机检查，不能表述为外部验证。

## 16. Q1 → Q2 Transfer Boundary

Q1 只移交稳定纯方位角内核、本机信息隔离、候选/拒绝纪律、局部 Jacobian 与明示适用域。Q1 的 100 m 圆形目标、匿名机最少数、FY04/FY07 排程和表 1 回放数值不得外推到 Q2。

## 17. Sol Delegation Record

```text
ROLE = Independent Q1 Mid Reviewer
REQUESTED_MODEL = gpt-5.6-sol
REQUESTED_REASONING_EFFORT = xhigh
ACTUAL_MODEL = NOT_VERIFIED
ACTUAL_REASONING_EFFORT = NOT_VERIFIED
ACTUAL_PROFILE_VERIFIED = NO
DECISION = PASS
CONFIDENCE = HIGH
FATAL_MODEL_MISMATCH = NO
REOPEN_REQUIRED = NO
RETURN_TO_TERRA = YES
```

Sol 的独立裁决同意上述允许/禁止结论；其审查意见不替代 JSON、源代码、解析导数和人工裁决。

## 18. Final Program Verdict

```text
Q1_MID_REVIEW_PROGRAM_VERDICT = PASS_WITH_MINOR_FIX
FATAL_MODEL_MISMATCH = NO
MAJOR_FINDING = NO
REMEDIATION_REQUIRED = NO
REOPEN_REQUIRED = NO
```
