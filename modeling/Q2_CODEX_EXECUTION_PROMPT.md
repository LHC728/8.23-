# Q2 Codex 正式执行提示词

## 身份与模型路由

你是本项目 Q2 的 Terra Main Agent，默认使用 `Terra High` 完成冻结路线修订、正式实现、确定性验证、结果整理与交接。

优先级固定为：

```text
deterministic checker / oracle
→ Terra 自己实现与 Debug
→ 规则化批量任务才考虑 Luna
→ 只有高后果数学冲突无法由确定性证据裁决时才调用 Sol XHigh
```

普通代码错误、数值稳定、路径、依赖和格式问题不得调用 Sol。Sol 不得接管整问或重新开题。

## 一、目标

在用户已经批准的 Q2 局部重开范围内，完成：

1. 对 `opening/07_STRATEGY_FREEZE.md` 的 Q2 参考框架与尺度层作一次受限修订；
2. 建立 Q2 正式模型契约；
3. 实现完整的 `CORE IMPLEMENTATION / 最小充分实现`；
4. 完成确定性 Program Gate；
5. 生成 Official Result、Human Check Card、Paper Handoff；
6. 停止等待用户 Human Verdict。

不得自动最终冻结，不得开始论文总装或其他新问题。

## 二、启动时必须进行 repo-first audit

先读取真实仓库，不得根据聊天记忆重写模型。至少读取：

- 当前 `git HEAD`、`origin/main` 和工作树状态；
- `AGENTS.md`；
- `CURRENT_STATE.md`；
- `opening/07_STRATEGY_FREEZE.md`，尤其 Q2、共享定义、信息边界、验证、Fallback、REOPEN 和 Prohibited Re-expansion；
- `review/Q2_FINAL_ROUTE_PROPOSAL.md`；
- `human_check/Q2_ROUTE_PROPOSAL_HUMAN_CHECK_CARD.md`；
- `literature/q2_route_paper_cards.md`；
- `results/q2_design/q2_final_route_gate.json`；
- `results/q2_design/q2_anchor_route_audit.json`；
- `results/q2_design/q2_bootstrap_design_enumeration.json`；
- `results/q2_design/q2_bootstrap_audit.json`；
- `results/q2_design/q2_local_route_sanity.json`；
- `experiments/q2_*.py`；
- `B题.pdf` 的 Q2 原题。

启动预期状态：

```text
EXPECTED_HEAD = 75851562a3781322cced1385fb53078448d39720
EXPECTED_REMOTE_HEAD_MATCH = YES
EXPECTED_WORKTREE = CLEAN
Q2_ROUTE_HUMAN_VERDICT = PASS
Q2_REFERENCE_FRAME_AND_SCALE_REOPEN_APPROVED = YES
Q2_REOPEN_SCOPE = REFERENCE_FRAME_AND_SCALE_LAYER
Q2_STARTED = NO
CODEX_NEXT_ACTION = Q2_APPROVED_STRATEGY_AMENDMENT_AND_CORE_IMPLEMENTATION
```

若 HEAD 继续前进但状态语义一致，以当前真实 HEAD 为准。若工作树有未知修改、远程落后、人工批准丢失，或正式文件和上述批准范围冲突，先停止并报告，不得强行施工。

## 三、clean-room 与信息边界

继续严格遵守：

- `B题.pdf` 是唯一允许使用的 2022 来源；
- 禁止打开 `2023.md`；
- 禁止搜索或使用任何 2022 B 赛后题解、讲评、优秀论文、博客或 GitHub 解答；
- 不重新进行无边界文献搜索；
- 允许使用已经筛选的通用学术证据，但它们不能替代当前题公式。

在线严格禁止：

- 跨接收机上报、交换或汇总夹角；
- 集中控制器读取多个接收机角并计算动作；
- 发射机绝对坐标、距离、仿真真值、评估器输出进入动作函数；
- 未来状态或隐藏身份进入当前决策。

在线允许：

- 接收机自己的编号；
- 当轮发射机编号；
- 该接收机自己测得的两两夹角；
- 预装目标角、固定排程、本机动作与本机试探历史。

FY11、FY15 的可信基线是物理尺度来源，但其绝对坐标不得进入其他无人机的在线控制器。微小试探只估计本机动作—角响应，不得被包装成新的米制尺度估计方法。

## 四、先完成受限 Strategy Amendment

当前 `opening/07_STRATEGY_FREEZE.md` 仍保存旧自由尺度 Q2 路线。用户已经明确批准：

```text
Q2_ROUTE_PROPOSAL_HUMAN_VERDICT = PASS
APPROVE_Q2_REFERENCE_FRAME_AND_SCALE_REOPEN = YES
```

因此先对 Strategy Freeze 作受限修订，范围只能包括：

- Q2 的尺度状态；
- Q2 Goal/Input/Observable/Unknown/Model；
- Q2 参数与信息来源；
- Q2 执行顺序、验证、Fallback 和禁止结论；
- 与 Q2 直接相关的摘要表、Overall Backbone 和创新说明。

不得修改 Q1(1)、Q1(2)、Q1(3) 的数学结论、正式结果或状态。

修订后的 Q2 正式路线必须是：

```text
FY11/FY15 trusted metric seeds
→ FY04/FY03 strict-local alternating bootstrap
→ FY03/FY04/FY11/FY15 four-reference placement of the remaining 11 UAVs
```

明确写入：

- 参数化目标间距为 $d^\ast>0$；
- FY11–FY15 可信基线长度为 $4d^\ast$；
- 整体平移、旋转和镜像自由；
- 若可信基线假设撤销，则退回旧自由尺度路线；
- 旧自由尺度路线降为正式 fallback，不删除其历史记录；
- 结论只限目标邻域、非退化和可信参考条件。

建立：

```text
model_contract/Q2_MODEL_CONTRACT.md
```

模型契约必须固定符号、编号—格点映射、角顺序、排程、在线 API、参数来源、允许结论、禁止结论、验证 Gate 和 fallback。

完成 Strategy Amendment 后更新 `CURRENT_STATE.md`，创建 milestone commit 并正常 push。远程检查点成功前不得进入正式核心实现。

## 五、正式数学骨架

### 5.1 目标格点

使用

$$
q_{c,j}
=
d^\ast
\begin{bmatrix}
-\sqrt3 c/2\\
j-c/2
\end{bmatrix},
\qquad
c=0,1,2,3,4,
\quad j=0,1,\ldots,c.
$$

编号逐行对应 FY01–FY15。

### 5.2 本机无符号角

统一使用冻结的 `atan2(abs(cross), dot)` 数值内核。不得切换到不稳定的裸 `arccos`。

### 5.3 两可信种子

固定 FY11、FY15，要求实际相对位置无偏差且

$$
\lVert q_{11}-q_{15}\rVert=4d^\ast.
$$

这只固定共同尺度，不恢复世界平移、旋转或镜像。

### 5.4 FY04/FY03 交替建锚

宏周期：

1. FY11、FY15、FY03 发射，FY04 接收和调整；
2. FY11、FY15、FY04 发射，FY03 接收和调整。

目标角、两项主残差和同机留出角必须逐项与 `review/Q2_FINAL_ROUTE_PROPOSAL.md` 对齐。

必须复算：

- $J_C,B_C,J_D,B_D$；
- $F=-J_C^{-1}B_C$ 与 $G=-J_D^{-1}B_D$；
- $GF=0$；
- 周期 Jacobian 二阶幂零与谱半径 0；
- 联合 Jacobian 行列式 $1/(117(d^\ast)^4)$；
- 解析导数与独立有限差分一致。

### 5.5 四参考机下 11 机归槽

固定参考组：

```text
FY03, FY04, FY11, FY15
```

每个接收机形成同一位置上的六个两两夹角。对目标值为 0 或 $\pi$ 的分量只作边界集合检查，不进入普通光滑 Jacobian。

从其余分量中选择使目标处最小奇异值最大的两项作为主控制角；全部其余非边界本机角作回代验收和错误分支拒绝。

## 六、CORE IMPLEMENTATION / 最小充分实现

不得交付玩具版、只跑一个节点的示例或旧自由尺度 Baseline。核心实现至少覆盖：

1. 参数化 $d^\ast$ 的 15 节点格点与编号表；
2. 三参考与四参考的本机角观测内核；
3. 四参考六约束完整候选器：
   - 双侧定夹角圆；
   - 全部圆—圆交点；
   - 相切、重合圆、连续解族；
   - 发射机—接收机重合拒绝；
   - 全部非边界角逐候选回代；
   - 候选去重与明确状态；
4. FY04/FY03 严格本机交替建锚控制器；
5. 四参考机下 11 架接收机的主角选择、动作和留出角验收；
6. 控制器—仿真环境—离线评估器的硬隔离；
7. 30 条最近邻边和三族 12 条最大直线的独立几何评估器；
8. 参数、排程、失败原因和全部验证数据的可复算输出。

设计期 `experiments/q2_*.py` 可以作为证据和原型，但不得仅重命名为生产实现。生产候选器、控制器和独立复核器应有清楚分层，checker 不得调用同一核心求解函数来自证。

## 七、Program Gate 必须包含的验证

### A. 数学与候选完整性

- 复算目标格点、目标角和可信基线；
- 复算四个解析偏导块、隐函数导数、周期谱和联合行列式；
- 解析结果与独立有限差分对照；
- FY04、FY03 完整三角候选均只保留目标根；
- 四参考下 11/11 个槽位完整单候选；
- 所有 0/$\pi$、相切、重合圆、近共线和接收机—发射机重合分支均有机械测试。

### B. 必须保留的负对照

- 旧参考组 $\{2,6,8,14\}$ 对 FY11 必须检测出两个根；若生产候选器只返回一个，Gate 必须 FAIL；
- 含非法真值坐标、距离或跨接收机角字段的控制器接口必须被防火墙测试拒绝；
- hard-coded `True/PASS` 不得代替事件、数值或异常检查；
- 两参考机只有一个独立夹角的局部秩不足必须机械复核；
- 去掉可信基线后，$d^\ast$ 与 $sd^\ast$ 的纯角不可区分性必须通过数值蜕变验证。

### C. 独立求解器

- 完整圆分支候选器之外，建立不调用圆候选器的过定多初值数值复核器；
- 逐节点比较根集合，而不是只看目标根是否存在；
- 独立复核器不得调用生产候选器、生产控制器或共享候选过滤函数。

### D. 建锚回放

- 720 组精确最佳响应扰动网格，至少覆盖半径 $0.01d^\ast$ 至 $0.30d^\ast$；
- 256 组有限试探本机控制网格，至少覆盖 $0.02d^\ast$ 至 $0.20d^\ast$；
- 报告成功率、最慢宏周期、最终误差和失败样例；
- 零谱只能写成一阶局部结论，不能替代非线性回放。

### E. 11 机本机回放

- 至少复现 6 个半径 × 16 个方向 × 11 个接收机；
- 将 $r\le0.20d^\ast$ 作为当前设计期认证网格；
- $0.30d^\ast$、$0.40d^\ast$ 作为压力测试，失败必须保留；
- 不因压力域失败而把局部结论写成全局。

### F. 参考机误差敏感性

- 分别扰动四参考机 $0.001d^\ast$、$0.01d^\ast$、$0.05d^\ast$；
- 输出跟随者偏差、边长误差、共线偏差和留出角残差；
- 这些数据只进入离线评估，不回灌在线控制器；
- 不允许写“参考机误差不影响结果”。

### G. 几何与蜕变验收

- 30 条最近邻边；
- 三族 12 条最大直线；
- 平移、旋转、整体镜像和共同缩放下角观测不变；
- 固定 $d^\ast$ 的尺度来源只允许是 FY11–FY15 基线；
- 比较每步动作、最终本机残差、全部节点位置和最终几何指标。

### H. 信息防火墙

- 对生产控制器函数签名与 AST 做机械检查；
- 运行时记录实际观测事件；
- 注入非法字段的负对照必须失败；
- evaluator/true coordinates 被 monkeypatch 禁止后，在线控制器仍可运行；
- `cross_receiver_angle_exchange = false` 必须由实际调用轨迹证明，不是硬编码布尔值。

## 八、结论边界

允许结论：

> 在 FY11、FY15 为已知编号且实际相对位置无偏差的可信种子、基线为 $4d^\ast$、FY04/FY03 位于目标局部域、每轮发射机保持不动且几何非退化时，FY04/FY03 严格本机交替最佳响应在目标点的一阶周期谱半径为零；建成 FY03/FY04/FY11/FY15 四参考框架后，其余 11 个目标槽位在完整本机角观测下为单候选，并可在认证局部域内并行调整。

禁止结论：

- 原题明示 FY11/FY15 无偏差；
- 没有尺度参考也能恢复指定 $d^\ast$；
- 任意初态全局收敛；
- 一阶零谱等于非线性两轮精确到位；
- 三参考机普遍全局唯一；
- 重合圆可以忽略；
- 参考机有偏差仍完全无影响；
- 世界平移、旋转或镜像被恢复。

## 九、Failure / REOPEN 规则

普通公式细化、代码 bug、依赖、精度、初值、阻尼和运行时间问题均由 Terra 修复，不构成 REOPEN。

只有出现以下情况才登记 `FATAL_MODEL_MISMATCH` 并停止：

- 生产完整候选器和独立求解器共同证明新四参考组仍有未登记多解；
- FY04/FY03 目标附近联合 Jacobian 实际不满秩；
- 在线实现必须读取非法信息才能完成动作；
- FY11/FY15 可信基线无法作为批准范围内的尺度来源；
- 某个题目明确要求仍无法回答。

不得自行扩大 REOPEN 或替换整条路线。

Fallback：若可信基线条件最终被撤销，恢复旧自由尺度三角点内角均衡路线；不允许恢复已经淘汰的跨机合角、集中控制、在线全图因子或 $\{2,6,8,14\}$ 方案。

## 十、Checkpoint 与停止条件

至少建立两个远程里程碑：

1. `Q2: amend frozen strategy and create model contract`；
2. `Q2: pass program gate and prepare human review`。

每次提交后正常 push，并核对 `origin/main` 与本地一致。禁止 force push、rebase、reset 或删除历史。

Program Gate PASS 后必须生成：

```text
results/q2/Q2_OFFICIAL_RESULT.md
human_check/Q2_HUMAN_CHECK_CARD.md
paper_handoff/Q2_PAPER_HANDOFF.md
```

然后停止。必须保持：

```text
Q2_HUMAN_VERDICT = PENDING
Q2_FINAL_FREEZE = PENDING
```

不得代替用户填写 PASS，不得自动最终冻结，不得开始论文总装。

## 十一、最终向用户回报格式

每一行均附中文解释：

```text
Q2_STRATEGY_AMENDMENT = PASS / FAIL
Q2_MODEL_CONTRACT = COMPLETE / INCOMPLETE
Q2_CORE_IMPLEMENTATION = COMPLETE / INCOMPLETE
Q2_PROGRAM_GATE = PASS / FAIL
FOUR_REFERENCE_COMPLETE_CANDIDATES = PASS / FAIL
INDEPENDENT_ROOT_CHECK = PASS / FAIL
BOOTSTRAP_ANALYTIC_CHECK = PASS / FAIL
BOOTSTRAP_REPLAY = PASS / FAIL
FOLLOWER_LOCAL_REPLAY = PASS / FAIL
INFORMATION_FIREWALL = PASS / FAIL
METAMORPHIC_AND_GEOMETRY_CHECK = PASS / FAIL
FATAL_MODEL_MISMATCH = YES / NO
REOPEN_REQUIRED = YES / NO
OFFICIAL_RESULT =
HUMAN_CHECK_CARD =
PAPER_HANDOFF =
Q2_HUMAN_VERDICT = PENDING
Q2_FINAL_FREEZE = PENDING
LOCAL_COMMIT =
REMOTE_COMMIT =
REMOTE_HEAD_MATCHES_LOCAL = YES / NO
WORKTREE_STATUS = CLEAN / DIRTY
NEXT_ACTION = WAIT_FOR_Q2_HUMAN_VERDICT
```
