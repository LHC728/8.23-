# Q2 最终路线候选人工核查卡

## 当前状态

```text
Q2_ROUTE_DESIGN_GATE = PASS
STRATEGY_FREEZE_UPDATED = NO
Q2_FORMAL_IMPLEMENTATION_STARTED = NO
HUMAN_VERDICT = PENDING
```

## 请先确认你接受的题意条件

推荐路线要把相邻间距固定为参数 $d^\ast$，因此必须有一个现实长度来源。项目采用：

> FY11 与 FY15 是已知编号、位置无偏差并保持不动的可信种子；它们的实际相对距离是 $4d^\ast$。其他无人机不知道其绝对坐标，只接收信号并测自己位置处的夹角。

请判断这条条件是否可接受。

- 若接受：可以固定指定间距 $d^\ast$。
- 若不接受：必须退回自由尺度方案；纯夹角本身不能知道 50 m 或其他指定长度。

## 用小白话复核路线

1. 先固定锥形底边两端的 FY11、FY15，它们给出正确尺度。
2. FY04 和 FY03 轮流接收：一架移动时，另一架只发射；每架只用自己测得的角。
3. 两架到位后，与 FY11、FY15 组成四架参考机。
4. 四架一起发射，每个剩余无人机在自己位置最多测六个两两夹角。
5. 每架用条件最好的两个角控制移动，其余本机角检查是否落入错误分支。
6. 11 架之间不交换角，也没有中心控制器替它们计算动作。

## 你需要看的六项证据

### 1. 尺度是否合法

- 纯夹角对共同缩放不变，所以不能凭空产生 $d^\ast$。
- 本路线只用 FY11–FY15 的 $4d^\ast$ 基线提供尺度。

人工判断：`PASS / FAIL / NEEDS_CLARIFICATION`

### 2. 是否偷用坐标或距离

- 在线动作函数只接收本机试探角、预装目标角和本机数值参数。
- 坐标、候选全集、谱和最终几何误差只在离线验证器中使用。

人工判断：`PASS / FAIL / NEEDS_CLARIFICATION`

### 3. 是否跨接收机汇总夹角

- FY04 不读取 FY03 的角；FY03 不读取 FY04 的角。
- 跟随者之间也不交换角。
- 四参考阶段的六个角全部由同一架接收机在自己位置测得。

人工判断：`PASS / FAIL / NEEDS_CLARIFICATION`

### 4. 多解是否真的处理

- 修正后的程序保留全部定夹角圆分支，并显式识别重合圆。
- 它实际发现并淘汰了旧参考组的 FY11 第二根，说明检查不是形式上的 PASS。
- 新四参考组 11/11 单候选，且独立非线性求解器复现相同结果。

人工判断：`PASS / FAIL / NEEDS_CLARIFICATION`

### 5. 收敛结论是否夸大

- 解析一阶周期谱半径为 0。
- 720 组精确响应和 256 组有限试探建锚回放通过。
- 跟随者在 $0.20d^\ast$ 局部网格内全部通过。
- 较大扰动有失败，所以只声称局部，不声称任意初态全局收敛。

人工判断：`PASS / FAIL / NEEDS_CLARIFICATION`

### 6. 参考机偏差是否被隐藏

- 没有隐藏。参考机偏差为 $1\%d^\ast$ 时，最坏边长误差约 $3.02\%d^\ast$；留出角也出现约 $0.00565$ rad 残差。
- 因此正式结论必须写明可信参考假设，并把留出角作为异常检测。

人工判断：`PASS / FAIL / NEEDS_CLARIFICATION`

## 建议人工裁决

若你接受 FY11/FY15 可信基线条件，并认可结论只限局部、非退化范围，建议填写：

```text
Q2_ROUTE_PROPOSAL_HUMAN_VERDICT = PASS
APPROVE_Q2_REFERENCE_FRAME_AND_SCALE_REOPEN = YES
```

若你不接受可信基线条件，填写：

```text
Q2_ROUTE_PROPOSAL_HUMAN_VERDICT = FAIL
APPROVE_Q2_REFERENCE_FRAME_AND_SCALE_REOPEN = NO
FALLBACK = FREE_SIMILARITY_SCALE_ROUTE
```

若需要先讨论条件，填写：

```text
Q2_ROUTE_PROPOSAL_HUMAN_VERDICT = NEEDS_CLARIFICATION
QUESTION =
```

## 文件入口

- 完整路线：`review/Q2_FINAL_ROUTE_PROPOSAL.md`
- 文献卡：`literature/q2_route_paper_cards.md`
- 紧凑总 Gate：`results/q2_design/q2_final_route_gate.json`
- 完整几何审计：`results/q2_design/q2_anchor_route_audit.json`
- 完整排程枚举：`results/q2_design/q2_bootstrap_design_enumeration.json`
- 建锚回放：`results/q2_design/q2_bootstrap_audit.json`
- 跟随者与敏感性：`results/q2_design/q2_local_route_sanity.json`
