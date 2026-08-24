# Q2 路线专用文献卡

## 检索边界

- 只检索一般的纯方位/纯夹角定位、方位刚性、锚点可定位性、三点后方交会和几何条件评价。
- 未使用当前赛题标题或高度唯一原句检索；未读取任何 2022 B 赛后题解、获奖论文或讲评。
- `CONTAMINATION_BLOCKED = NO`。
- 证据等级分为 `FULL_TEXT`、`ABSTRACT_ONLY` 和 `REPOSITORY_FULL_TEXT`，避免把“知道题名”写成“读过原文”。

## P1：Jing, Wan & Dai — Angle-Based Sensor Network Localization

- **Year / Source：** 2022，IEEE Transactions on Automatic Control 67(2), 840–855。
- **DOI / link：** 10.1109/TAC.2021.3061980；<https://arxiv.org/abs/1912.01665>。
- **Evidence level：** `FULL_TEXT`（作者公开稿及完整证明版）。
- **研究问题：** 已知部分锚点位置、每个节点只在自身局部坐标系测角时，何时可唯一定位。
- **改变的判断：** 角的数量并不自动等于唯一可定位；必须同时检查角可固定性、锚点非共线和退化结构。
- **对本题迁移：** Q2 要显式区分“自由相似规范”和“由可信基线固定的尺度”，并对每个目标槽位做完整候选和局部秩审计。
- **不能迁移：** 文中的集中 SDP 和传感器间通信不符合本题禁止跨接收机角度汇总的边界。
- **Effect：** `CONFIRM + CORRECT`。

## P2：Advani & Weile — Position and orientation inference via on-board triangulation

- **Year / Source：** 2017，PLOS ONE 12(6), e0180089。
- **DOI / link：** 10.1371/journal.pone.0180089；<https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0180089>。
- **Evidence level：** `FULL_TEXT`（开放获取原文）。
- **研究问题：** 移动物体只利用自身测得的多个已知信标方向/夹角进行机载定位。
- **核心几何：** 每一对信标的定夹角轨迹为两支圆弧；两信标只给一个角，一般不足以确定二维位置；三信标一般可定位但可能多解，第四信标或历史信息可消歧。
- **改变的判断：** 它直接否定了“任取三架参考机就一定唯一”的想法，支持本项目把第四架参考机用于完整本机六角消歧。
- **对本题迁移：** 定夹角圆分支、全部交点保留、额外同机角回代。
- **不能迁移：** 文中已知信标世界坐标和天线姿态恢复不是本题在线可用信息；本项目只预装目标角并用本机闭环动作。
- **Effect：** `CORRECT + INSPIRE`。

## P3：Ligas — Simple Solution to the Three Point Resection Problem

- **Year / Source：** 2013，Journal of Surveying Engineering 139(3), 120–125。
- **DOI / link：** 10.1061/(ASCE)SU.1943-5428.0000104。
- **Evidence level：** `ABSTRACT_ONLY`（出版页元数据与摘要；未把它当作本项目公式证明的唯一来源）。
- **研究问题：** 已知三个控制点和观测夹角的平面三点后方交会。
- **对本题迁移：** 两个定夹角圆的交点是解析候选生成机制；0/180 度和重合圆必须作为特殊状态处理。
- **不能迁移：** 具体测量学坐标约定、定向角和唯一性结论不能直接替代本项目的无符号本机角模型。
- **Effect：** `CONFIRM`。

## P4：Zhao & Zelazo — Bearing Rigidity and Almost Global Bearing-Only Formation Stabilization

- **Year / Source：** 2016，IEEE Transactions on Automatic Control 61(5), 1255–1268。
- **DOI / link：** 10.1109/TAC.2015.2459191；<https://arxiv.org/abs/1408.6552>。
- **Evidence level：** `FULL_TEXT`（作者最终稿）。
- **研究问题：** 由相邻方向约束确定编队形状和进行方位编队稳定。
- **改变的判断：** 纯方向约束天然保留平移和共同尺度；不注入合法长度参考就不能声称恢复指定物理间距。
- **对本题迁移：** 自由度审计、尺度不可辨识、编队约束几何的结构语言。
- **不能迁移：** 文中有向 bearing、共同参考方向、邻接通信和近全局控制律不属于本题观测，不能照搬。
- **Effect：** `CORRECT`。

## P5：Zhao & Zelazo — Localizability and Distributed Protocols for Bearing-Based Network Localization

- **Year / Source：** 2016，Automatica；作者稿 2015/2016。
- **Link：** <https://arxiv.org/abs/1502.00154>。
- **Evidence level：** `FULL_TEXT`（作者公开稿）。
- **研究问题：** 已知锚点、共同参考系中的节点间 bearing 下的网络可定位性。
- **对本题迁移：** 锚点和几何秩共同决定可定位；参考机误差会传播到跟随者。
- **不能迁移：** 共同全局朝向、bearing Laplacian、通信协议均超出本题信息边界。
- **Effect：** `CONFIRM`。

## P6：Bishop et al. — Optimality analysis of sensor-target localization geometries

- **Year / Source：** 2010，Automatica。
- **DOI / link：** 10.1016/j.automatica.2009.12.003。
- **Evidence level：** `ABSTRACT_ONLY`（出版元数据与摘要；本项目没有移植其 Fisher 信息公式）。
- **研究问题：** 传感器—目标相对几何如何影响定位信息和误差下界。
- **对本题迁移：** 参考机选择不能只看数量；应用当前无符号夹角方程自己的 Jacobian 最小奇异值、条件数和角边界裕度评价几何。
- **不能迁移：** 文中的噪声模型、Fisher 信息矩阵和 CRLB 数值没有题面参数支持。
- **Effect：** `INSPIRE`。

## 国内全文证据复用

不重复扩张检索，继续复用 `literature/chinese_paper_cards.md` 中已经核查的：

1. 孙文涵、鲜斌《基于方位信息的无人机编队控制设计与验证》：支持“纯方位约束可能漂移或不唯一，锚点结构会改变结果”；其 Leader 位置、动力学和连续控制律不迁移。
2. 刘忠《多站纯方位定位系统的可观测性条件》：支持“观测数量足够仍可能因几何退化不可观测”；其动态多时刻模型不迁移。
3. 吴龙文等《基于 AOA 的双机无源定位模型及其解算方法》：仅作为几何布局影响定位条件的工程背景，不移植绝对 AOA 方程。

## 对最终路线真正产生的作用

- **真正改变路线：** P1、P2、P4。它们分别迫使路线加入锚点/可辨识性审计、第四参考机消歧、尺度参考的明示假设。
- **支持求解与评价：** P3、P6。
- **背景和迁移边界：** P5 及三篇国内文献。
- 文献没有替代本题有限几何证明。最终的 FY11/FY15、FY04/FY03 和四参考组选择来自本题 16380 个排程的完整枚举及独立验证。
