# Q1(1) 正式结果

## 状态

```text
Q1_1_MINIMUM_GATE = PASS
RESULT_SCOPE = deterministic minimum candidate/oracle/rank gate
ONLINE_INFORMATION_SCOPE = one receiver's own labelled transmitter-pair angles only
```

## 正式模型结果

对三架编号已知、位置无偏差的发射机 `(q_a,q_b,q_c)`，接收无人机自身的原始本机纯方位观测向量为 `(y_ab,y_ac,y_bc)`。对每个非边界角，构造定夹角圆心的双侧分支：

\[
\rho=\frac{\|A-B\|}{2\sin\theta},\qquad d_\perp=\rho|\cos\theta|.
\]

对 `ab`、`ac`、`bc` 中任意两条角约束，枚举对应圆分支的全部交点。剔除收发机重合点、重复点，以及未通过三条原始无符号 `atan2` 角回代的点。未参与该二约束构造的角只作同一接收机内的分支/顺序留出角约束检验。

输出为完整有限候选集，而非被强制选出的单点。只有在接收机编号对应的局部目标槽位域内恰有一个候选、且选定两角 Jacobian 秩为二时，才可作局部唯一性判定。这是局部、非退化结论，不是全局唯一性结论。

## 确定性证据

机器可读来源为 `results/q1_1/q1_1_minimum_gate.json`，由 `python -m tests.q1_1_minimum_gate` 生成。

| 必要检查 | 结果 |
| --- | --- |
| 已知非退化真值被找回 | PASS；保留点 `(1.5, 1.0)` |
| 双侧几何分支均被保留 | PASS；共线镜像样例保留 `(0,1)` 和 `(0,-1)` |
| 显式多根不被写成唯一根 | PASS；保留两个候选 |
| 原始 `atan2` 角回代 | PASS；每个保留候选均匹配三条角 |
| 独立多初值数值复核器 | PASS；理想与镜像样例的根集相同 |
| 相切/近退化/`0-pi` 边界 | PASS；相切被标记、近边界给出警告、精确边界安全拒绝 |
| 理想目标处局部秩 | PASS；秩 `2`，`sigma_min = 0.53988258`，条件数 `1.95283669` |

独立数值复核器采用多初值、阻尼 Gauss--Newton 和有限差分 Jacobian；其不含圆构造，先求两角残差再回代第三角。一致性只属于实现交叉复核，不是外部验证。

## 明确的失败语义

- `CANDIDATE`：一个或多个有限点通过全部原始角检查。
- `CERTIFIED`：要求接收机本地槽位域唯一性条件和完整局部秩；确定性程序验收不指定生产槽位半径。
- `REJECTED`：精确 `0/pi` 边界输入、收发机重合或分支证据不足。

本结果刻意不声称：全局唯一性、任意初始位置均可恢复、对未建模物理噪声稳健，或获得经外部验证的位置估计。

## 复现接口

```text
MODEL CONTRACT = model_contract/Q1_1_MODEL_CONTRACT.md
PRIMARY IMPLEMENTATION = src/q1_1_geometry.py
DETERMINISTIC GATE = tests/q1_1_minimum_gate.py
RAW RESULT = results/q1_1/q1_1_minimum_gate.json
```
