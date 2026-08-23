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
