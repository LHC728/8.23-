# GitHub 仓库阅读指南：供队友与 AI 使用

> GitHub 仓库：[LHC728/8.23-](https://github.com/LHC728/8.23-)
>
> 本指南解释怎样判断项目当前状态、怎样追踪每个结论、怎样让 AI 在不改模型和不污染 clean-room 的前提下帮助阅读。
>
> 当前里程碑：Q1(1)～Q1(3) 及 Q1 中期审查已经通过；Q2 尚未启动。

## 1. 最重要的原则：不要只看 README 或聊天记录

仓库中的信息有明确优先级：

```text
B题.pdf 的原题要求
        ↓
AGENTS.md 的长期规则和信息边界
        ↓
CURRENT_STATE.md 的当前状态
        ↓
opening/07_STRATEGY_FREEZE.md 的冻结数学路线
        ↓
model_contract 的实现契约
        ↓
src + tests + JSON 的实际计算证据
        ↓
Official Result 的正式结论
        ↓
Human Check Card、Paper Handoff 和 Review
```

如果旧文档、README、聊天记忆和当前状态冲突：

- 项目状态以 `CURRENT_STATE.md` 为准；
- 数学路线以 `opening/07_STRATEGY_FREEZE.md` 为准；
- 正式数字以对应 JSON 和 Official Result 为准；
- 原题要求以 `B题.pdf` 为准。

README 是导航页，不是最终事实裁判。

## 2. 在 GitHub 网页上怎样阅读

### 2.1 第一次进入

1. 打开仓库主页；
2. 确认分支为 `main`；
3. 查看最新提交时间和提交哈希；
4. 先打开 `CURRENT_STATE.md`；
5. 再按本指南的阅读路线查看文件。

如果别人给你的提交哈希和 GitHub `main` 最新哈希不同，先不要假设内容已经上传成功。

### 2.2 查看 Markdown

GitHub 会直接渲染 `.md` 文件：

- 左侧目录用于跳转标题；
- 蓝色相对链接可以在仓库内部继续打开；
- 公式使用 GitHub Markdown 数学渲染；
- 若公式显示源代码，检查是否被放进了普通代码块，或者是否使用了不兼容宏。

### 2.3 查看 JSON

JSON 是机器可读的原始结果，不适合从头阅读。推荐：

1. 先看对应 `Q1_*_OFFICIAL_RESULT.md` 了解关键结论；
2. 再在 JSON 中搜索具体字段、数值、阈值和 PASS 条件；
3. 最后看测试脚本确认这些字段怎样计算。

不要只看到 JSON 中的 `PASS` 就相信它。应同时找到：

- 原始计算值；
- 判断阈值；
- 实际事件或候选记录；
- 生成它的测试代码。

### 2.4 下载整个仓库

不使用 Git 时，可在 GitHub 页面选择：

```text
Code → Download ZIP
```

使用 Git 时，在 PowerShell 中执行：

```powershell
git clone https://github.com/LHC728/8.23-.git
Set-Location '8.23-'
git status
```

如果已经有本地仓库，查看当前状态：

```powershell
git rev-parse HEAD
git status --short
git branch --show-current
```

`git status --short` 没有输出，通常表示工作树干净；它不等于远程一定已经同步。

## 3. 三种推荐阅读路线

### 3.1 十分钟快速理解 Q1

按顺序阅读：

1. `CURRENT_STATE.md`：确认 Q1 已通过、Q2 未开始；
2. `writing_reference/Q1_DETAILED_SOLUTION_AND_EVIDENCE.md`：看懂三小问；
3. `review/Q1_MID_REVIEW.md`：看允许结论、禁止结论和已知限制；
4. `human_check/Q1_MID_REVIEW_HUMAN_CHECK_CARD.md`：看人工最终接受了什么。

适合：队友、论文统稿者、指导老师快速了解。

### 3.2 深入审查某一小问

以 Q1(2) 为例：

1. `B题.pdf`：确认原题问法；
2. `opening/07_STRATEGY_FREEZE.md` 的 Q1(2)；
3. `model_contract/Q1_2_MODEL_CONTRACT.md`：正式输入、公式和失败语义；
4. `src/q1_2_identity.py`：生产枚举器；
5. `tests/q1_2_minimum_gate.py`：怎样验证；
6. `results/q1_2/q1_2_minimum_gate.json`：原始事件和数字；
7. `results/q1_2/Q1_2_OFFICIAL_RESULT.md`：允许使用的正式结论；
8. `human_check/Q1_2_HUMAN_CHECK_CARD.md`：用户核查内容；
9. `paper_handoff/Q1_2_PAPER_HANDOFF.md`：怎样进入论文。

把文件名中的 `Q1_2` 换成 `Q1_1` 或 `Q1_3`，即可审查其他小问。

### 3.3 准备写论文

按顺序阅读：

1. `writing_reference/SAFE_WRITING_GUIDE.md`；
2. `writing_reference/Q1_WRITING_GUIDE_FOR_HUMAN_AND_AI.md`；
3. `writing_reference/Q1_DETAILED_SOLUTION_AND_EVIDENCE.md`；
4. 三个 `paper_handoff/Q1_*_PAPER_HANDOFF.md`；
5. 三个 Official Result 和 JSON；
6. `opening/04_LITERATURE_EVIDENCE.md`；
7. `literature/international_paper_cards.md` 和 `literature/chinese_paper_cards.md`。

写作不能只读 Paper Handoff，因为 Paper Handoff 是叙事接口，不是全部数学和原始证据。

## 4. 每个目录是干什么的

| 路径 | 主要用途 | 阅读时要注意什么 |
|---|---|---|
| `B题.pdf` | 当前赛题原文 | 唯一允许使用的 2022 来源 |
| `AGENTS.md` | 长期规则、clean-room、冻结治理、模型路由 | 所有 AI 和执行者都必须遵守 |
| `CURRENT_STATE.md` | 当前阶段、通过情况、下一动作 | 判断“现在做到哪一步”的第一入口 |
| `opening/` | 问题地图、文献证据、路线设计和冻结蓝图 | 01～06 含历史过程；07 才是当前真源 |
| `model_contract/` | 每问的正式数学与程序接口 | 看输入、观测、未知、失败语义 |
| `src/` | 生产实现 | 不能仅凭函数名判断是否合规 |
| `tests/` | 确定性 Gate、独立检查和负对照 | 检查 PASS 是否真的由数据计算 |
| `results/` | 原始 JSON 和 Official Result | JSON 给证据，Official Result 给允许结论 |
| `human_check/` | 用户能够理解和裁决的核查卡 | 人工 PASS 不是程序证据的替代品 |
| `paper_handoff/` | 论文作者的段落、图表和措辞接口 | 不能擅自增强结论 |
| `review/` | 独立审查、队友方案比较 | 看问题、允许结论和禁止外推 |
| `modeling/` | 详细数学推导 | 应与模型契约和正式结果一致 |
| `literature/` | 已筛选论文卡片 | 文献只作理论背景和决策依据 |
| `writing_reference/` | 解法说明和写作/阅读指南 | 面向人和 AI 的解释层 |

## 5. 怎样理解一条完整证据链

以“Q1(2) 局部最少一架匿名发射机”为例：

```text
冻结规范要求完整编号—位置联合枚举
        ↓
MODEL_CONTRACT 定义 Φ_b、候选集合和局部证书
        ↓
src/q1_2_identity.py 实现生产枚举
        ↓
tests/q1_2_minimum_gate.py 调用生产枚举器并记录事件
        ↓
q1_2_minimum_gate.json 保存 392 次假设和 294 条远端记录
        ↓
Q1_2_OFFICIAL_RESULT.md 将结论限定为局部 m_min=1
        ↓
Human Check Card 由用户确认没有把局部结论说成全局结论
        ↓
Q1_MID_REVIEW 再检查三问接口和结论强度
```

可信度来自整条链的一致，不来自单独一个 PASS。

## 6. Q1 当前正式结论速览

### Q1(1)

- 双侧定夹角圆生成全部有限候选；
- 第三条本机角逐候选回代；
- 局部槽位内唯一且 Jacobian 满秩时才判定局部唯一；
- 镜像、多根和退化不会被静默删除；
- 不宣称全平面唯一。

### Q1(2)

- $m=0$ 只有等角圆弧，不能定位二维位置；
- 一架匿名发射机在明示局部条件下足以联合辨认编号与位置；
- 局部理论结论为 $m_{\min}=1$；
- 第二匿名机只是证据不足时的冗余发射备用方案；
- 远端或错误候选明确保留，不宣称全局唯一。

### Q1(3)

- 固定 FY00/FY01；
- FY04/FY07 执行五个严格本地交替校正宏周期；
- 固定 FY00/FY01/FY04/FY07 四锚；
- 其余六机使用各自本机角并行归槽；
- 表 1 确定性回放形成半径 100 m 正九边形；
- 不宣称任意初态全局收敛或现实微米精度。

## 7. 怎样运行现有 Q1 检查

项目已经有本地虚拟环境时，可在仓库根目录执行：

```powershell
.\.venv\Scripts\python.exe -m tests.q1_1_minimum_gate
.\.venv\Scripts\python.exe -m tests.q1_2_minimum_gate
.\.venv\Scripts\python.exe -m tests.q1_3_program_gate
```

如果没有 `.venv`，先阅读 `requirements-validation.txt`，在独立虚拟环境中安装通用依赖。不要把虚拟环境、缓存或密钥提交到仓库。

运行后要检查：

- 命令退出码；
- JSON 是否由本次运行更新；
- 原始数值与阈值；
- 是否出现新的未提交修改；
- 测试是否真的调用生产实现，而不是在测试中重写同一结论。

普通读者不需要运行测试才能看懂论文；复现者和审查者才需要进入这一层。

## 8. 怎样把仓库交给 AI 阅读

### 8.1 AI 能直接访问本地仓库时

先给它如下约束：

```text
这是一个本地数学建模项目。回答前必须先读取当前仓库，不得仅凭聊天记忆。

必须先读：
- AGENTS.md
- CURRENT_STATE.md
- opening/07_STRATEGY_FREEZE.md

clean-room 规则：
- B题.pdf 是唯一允许使用的 2022 来源；
- 禁止读取 2023.md；
- 禁止搜索或使用任何 2022 B 赛后论文、题解、讲评、博客或 GitHub 解答。

模型已冻结：
- 不得新增模型家族；
- 不得恢复旧 Route A/B；
- 禁止跨接收机夹角汇总；
- 内部坐标和仿真真值不能作为在线输入；
- 局部结论不能改写成全局结论。

请先报告：HEAD、git status、SOURCE_OF_TRUTH 和本任务涉及的正式文件。
```

### 8.2 AI 不能直接访问仓库时

不要一次把整个仓库无差别粘贴给它。按任务提供最小上下文包。

#### 解释 Q1 的最小包

- `AGENTS.md` 中 clean-room 与信息边界；
- `CURRENT_STATE.md`；
- `opening/07_STRATEGY_FREEZE.md` 中 Q1；
- `writing_reference/Q1_DETAILED_SOLUTION_AND_EVIDENCE.md`。

#### 检查某一小问的最小包

- 对应 Model Contract；
- 对应 Official Result；
- 对应 JSON；
- 对应 `src` 和 `tests`；
- `review/Q1_MID_REVIEW.md` 的相关章节。

#### 帮助写论文的最小包

- 本指南；
- `Q1_WRITING_GUIDE_FOR_HUMAN_AND_AI.md`；
- 对应 Paper Handoff；
- 对应 Official Result；
- 已筛选 paper cards。

### 8.3 AI 输出时应强制附带的字段

```text
REPO_FILES_READ =
SOURCE_OF_TRUTH_USED =
ONLINE_INFORMATION_USED =
OFFLINE_ONLY_INFORMATION =
RESULT_SOURCE =
CLAIM_SCOPE = LOCAL / NONDEGENERATE / TABLE_1_REPLAY / OTHER
NEW_MODEL_INTRODUCED = YES / NO
CONFLICT_FOUND =
```

这些字段能快速发现 AI 是否脱离仓库或偷偷扩大结论。

## 9. 常用 AI 提示词

### 9.1 小白解释某个公式

```text
请基于当前仓库解释 Q1(2) 的编号观测分离度。
按“题目目的—可观测信息—未知量—公式—逐符号解释—几何直觉—证据—适用范围—失败情形”的顺序回答。
不要新增模型，不要使用距离、真值坐标或其他接收机夹角。
```

### 9.2 审查代码是否符合模型

```text
请对照 opening/07_STRATEGY_FREEZE.md 和对应 MODEL_CONTRACT，检查生产实现是否一致。
不要把已有 PASS 当证据。追踪规范→函数输入→实际计算→测试→JSON→Official Result。
重点检查 hard-coded PASS、首根偏差、真值泄漏、检查器与主实现自证、分支覆盖和结论过强。
只做审查，不自动改文件。
```

### 9.3 从仓库写论文段落

```text
请按 writing_reference/Q1_WRITING_GUIDE_FOR_HUMAN_AND_AI.md 写 Q1(3) 正文。
正式数字只能来自 Q1_3_OFFICIAL_RESULT.md 和 q1_3_program_gate.json。
必须写明信息隔离、固定排程、零谱的局部范围和表 1 确定性回放性质。
文献只提供背景，不声称直接证明 FY04/FY07 公式。
```

### 9.4 检查引用

```text
请核对正文中每个 [n] 引用实际支持哪一句。
标记：SUPPORTED、PARTIAL、MISATTRIBUTED、UNNECESSARY。
不得联网搜索当前 2022 B 题；只使用 literature paper cards 和已保存的一般学术全文。
缺失作者或页码时标记 MISSING_METADATA，不得猜测。
```

## 10. 怎样判断 AI 的回答是否可信

只要出现以下任一情况，就应暂停并要求 AI 回到仓库：

1. 没读 `CURRENT_STATE.md` 就宣布项目阶段；
2. 把 `opening/06_INNOVATION_AND_ROUTES.md` 的旧路线当成当前方案；
3. 使用距离、绝对 AOA、公共罗盘或真实坐标做在线决策；
4. 汇总不同接收机测得的角；
5. Q1(1) 只返回一个求解器首根；
6. 把 Q1(2) 的 $m_{\min}=1$ 写成无条件全局结论；
7. 把 Q1(3) 的谱半径零写成有限步或全局保证；
8. 把表 1 仿真误差写成现实飞行精度；
9. 用“某论文证明”代替本题独立推导；
10. 读取或搜索了污染性的 2022 B 赛后材料。

## 11. Clean-room 与安全边界

- `B题.pdf` 是唯一允许使用的 2022 来源；
- 不得打开或读取 `2023.md`；
- 不得搜索、引用或使用 2022 B 赛后题解、优秀论文、讲评、博客、论坛或 GitHub 解答；
- 历史资料只能提供一般建模和写作经验；
- 文献中的距离、绝对方位、运动学、概率分布或 Leader 位置，除非题面授权，否则不能进入当前模型；
- AI 发现真正的致命模型不匹配时只能提出 `REOPEN_REQUEST`，不能自行替换冻结主线。

## 12. 当前最安全的协作方式

### 队友负责论文时

1. 从详细解法文档理解每问；
2. 按 Q1 写作指南搭章节；
3. 从 Official Result 和 JSON 转数字；
4. 从 paper cards 核对引用；
5. 将初稿交给 AI 做“证据—结论一致性审查”；
6. 人工确认公式、图表、引用和结论范围。

### AI 负责辅助时

1. 先做 repo-first audit；
2. 只处理一个明确小任务；
3. 每个结论给出来源文件；
4. 不更换模型、不扩大搜索；
5. 输出后由人检查；
6. 未获得明确授权时不提交、不推送、不开始 Q2。

## 13. 最后一句话

看这个仓库时，不要问“哪个 Markdown 写得最像论文”，而要问：

> 这条结论能否沿着“冻结规范 → 模型契约 → 生产实现 → 测试 → 原始 JSON → 正式结果 → 人工核查”完整追溯？

能完整追溯，才是当前项目可以信任和写入论文的内容。
