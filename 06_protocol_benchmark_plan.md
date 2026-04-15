# 协议型 Benchmark 工作计划（1 个月版）

> 面向 Ch06 的目标：不是再造一个“大而全”的新 benchmark，而是做一个 **协议型 benchmark**，把现有 benchmark 变成可以衡量“自进化”的评测系统。
>
> 工作名建议：`SI-Protocol Benchmark`（简称 `SIP-Bench`）
>
> 核心判断：一个月内可交付的，不应该是新环境，而应该是 **统一评测协议 + 统一指标 + 小规模跨环境验证**。

---

## 1. 目标与边界

## 1.1 核心目标

在 1 个月内构建一个可运行、可复现、可写论文的协议型 benchmark，用来解决当前 agent benchmark 的三个核心缺口中的至少一个：

1. 不报告 `BWT/FWT` 或 agent 版本的旧任务保留/新任务增益。
2. 不报告“改进效率”，即每单位交互/算力/人工成本换来多少净增益。
3. 不区分 `外部路径`（skill/memory/tool）和 `参数路径`（LoRA/SFT/RL）带来的改进。

本计划的建议取舍是：

**主打解决 1 + 2，部分覆盖 3。**

原因：
- `BWT/FWT + efficiency` 最容易通过协议层而不是环境层实现。
- 一个月内做 `外部路径 vs 参数路径` 的完全公平对照风险较高，但可以先做轻量版。

## 1.2 不做什么

以下内容不进入 1 个月 MVP 范围：

1. 不从零构建新环境。
2. 不做大规模动态数据生产线。
3. 不试图一次性统一所有 agent benchmark。
4. 不把 benchmark 做成“社区标准最终版”。
5. 不追求覆盖安全、经济性、社会偏好、长期用户建模等全部维度。

## 1.3 一个月后必须交付的东西

最小可交付物应包含：

1. 一份公开协议文档。
2. 一套统一日志与打分脚本。
3. 至少 2 个现有 benchmark 的协议化版本。
4. 至少 3 个 baseline。
5. 一份结果表：展示前向增益、后向保留、改进效率。
6. 一份短论文草稿或技术报告。

---

## 2. 方案总览

## 2.1 核心思路

`SIP-Bench` 不是定义新任务，而是给已有 benchmark 叠加一个统一协议层：

1. 定义时间轴。
2. 定义改进阶段。
3. 定义旧任务回测。
4. 定义 held-out 新任务评测。
5. 定义成本记录与归一化指标。

这样做的好处是：
- 一个月内能落地。
- 容易和现有结果接轨。
- 论文叙事明确：我们不是声称任务更难，而是声称“评测更对”。

## 2.2 推荐 MVP benchmark 组合

### 必选环境

1. `SkillsBench`
- 原因：最直接测 skill-based self-improvement。
- 优势：已有 deterministic verifier，任务粒度清楚。
- 作用：验证“引入新能力后是否真的变好，以及是否有负迁移”。

2. `tau-bench`
- 原因：有动态 user-agent-tool 闭环，且有 `pass^k` 可靠性协议。
- 优势：对话、多轮、工具约束明显，接近部署态。
- 作用：验证“反复交互后是否更稳、是否保持旧能力”。

### 可选第三环境

3. `SWE-bench-Live` 小子集
- 原因：动态更新、抗污染、任务真实。
- 风险：环境重、运行慢、复现成本高。
- 使用策略：只取 20-50 题小样本作为扩展验证，不作为 MVP 主体。

### 不建议进入 MVP 的环境

1. `ClawArena`
- 很有价值，但如果依赖内部实现或环境复杂，1 个月内有交付风险。

2. `DomusMind / AgentMemoryBench`
- 理论价值高，但当前更适合作为下一阶段扩展，不适合 1 个月首发的主战场。

---

## 3. 协议设计

## 3.1 时间轴

所有环境统一使用三阶段协议：

1. `T0`：初始模型/初始 agent，不允许任何针对性改进。
2. `T1`：完成一轮改进后评测。
3. `T2`：经历延迟、漂移或额外任务流后再次评测。

其中：
- `T0 -> T1` 用来测“改进是否发生”。
- `T1 -> T2` 用来测“改进是否保住”。

## 3.2 任务切分

每个环境都切成三类任务：

1. `Replay Set`
- 旧任务集合。
- 用来测 retention / backward effect。

2. `Adapt Set`
- 改进阶段允许接触的任务或轨迹。
- 用来触发 skill 学习、memory 更新、prompt 更新或小规模参数更新。

3. `Held-out Set`
- 改进后测试的新任务。
- 用来测真正的 forward gain。

如果环境支持漂移，再增加：

4. `Drift Set`
- 与 `Held-out Set` 同任务形式但分布变化。
- 用来测恢复能力与适应速度。

## 3.3 路径对照

协议至少要跑三类 agent：

1. `Frozen Agent`
- 不允许任何更新。
- 作用：基线。

2. `External-path Agent`
- 仅允许 skill / memory / retrieval / prompt 库更新。
- 作用：测 Harness 层改进。

3. `Lightweight Parameter-path Agent`
- 仅允许 LoRA 或极小规模 SFT。
- 作用：给出参数路径参考。

如果资源不足，参数路径可作为第二阶段扩展，但协议从一开始就预留字段。

---

## 4. 指标设计

## 4.1 三个主指标

### A. Forward Gain

定义：

`FG = Score(T1, Held-out) - Score(T0, Held-out)`

含义：
- 改进后在新任务上是否真的更强。

### B. Backward Retention

定义：

`BR = Score(T1, Replay) - Score(T0, Replay)`

或保留率版本：

`BR_ratio = Score(T1, Replay) / max(Score(T0, Replay), eps)`

含义：
- 改进后旧任务是否掉分。

### C. Improvement Efficiency

定义：

`IE = FG / Cost`

其中 `Cost` 至少包含：
- token 使用量
- tool call 数
- wall-clock 时间
- optional: 人工标注或人工修正次数

含义：
- 每单位成本能换来多少净提升。

## 4.2 两个辅助指标

### D. Post-Drift Stability

定义：

`PDS = Score(T2, Held-out_or_Drift) - Score(T1, Held-out)`

含义：
- 改进是否稳定，经漂移后是否还能维持。

### E. Net Improvement Score

建议定义：

`NIS = FG - lambda * max(0, -BR)`

含义：
- 如果新任务提升建立在旧任务退化之上，净收益要被扣回去。

这个指标适合做图表摘要，不替代主指标。

---

## 5. 日志与输出规范

## 5.1 每次运行必须记录

1. 模型名与 agent 版本。
2. 改进路径类型（frozen / external / parameter）。
3. 任务 ID。
4. 阶段（T0/T1/T2）。
5. 成败分数。
6. token 数。
7. tool call 数。
8. wall-clock 时间。
9. memory write/read 次数。
10. 可选：人工介入次数。

## 5.2 统一输出文件

建议输出 3 个文件：

1. `runs.jsonl`
- 每题每次运行一条记录。

2. `summary.csv`
- 聚合后的环境级指标。

3. `leaderboard.md`
- 面向论文和展示的可读表格。

---

## 6. Baseline 设计

## 6.1 必跑 baseline

1. `Frozen`
- 不更新。

2. `Skill/Memory External`
- 按环境不同，允许 skill 库或 memory 库更新。

3. `Prompt-Retrieval`
- 不改参数，只增强上下文检索。

## 6.2 选跑 baseline

4. `LoRA-lite`
- 小预算参数更新。

5. `Oracle-help`
- 用于估计上界，不计入主榜单。

## 6.3 最小实验矩阵

建议 MVP：

1. 2 个环境
2. 3 个 baseline
3. 每环境 20-50 个任务
4. 每个任务 3 次重复

这样既能看稳定性，也不会把算力消耗拉爆。

---

## 7. 一个月排期

## Week 1: 定义与止损

目标：
- 锁定环境
- 锁定任务切分
- 锁定指标
- 跑通最小日志链路

任务：
1. 写 `protocol spec v0.1`
2. 选定 `SkillsBench + tau-bench` 为主环境
3. 决定是否加 `SWE-bench-Live` 小样本
4. 给每个环境切 `Replay / Adapt / Held-out`
5. 实现统一日志 schema
6. 先跑 5-10 个任务的 dry run

周末验收：
1. 至少一个环境从 T0 到 T1 跑通
2. 能自动输出 FG / BR / IE
3. 若 `SWE-bench-Live` 环境不稳定，则立即降级为第二阶段扩展

## Week 2: 协议实现

目标：
- 协议层代码可用
- 两个主环境完整跑通

任务：
1. 实现 benchmark adapter
2. 实现 metric aggregator
3. 实现 result summarizer
4. 跑 `Frozen / External / Prompt-Retrieval`
5. 验证每项指标数值合理

周末验收：
1. 两个环境均能跑主 baseline
2. 结果表可导出
3. 指标公式不再改动

## Week 3: 实验与分析

目标：
- 收集主要结果
- 看协议是否真能揭示旧 benchmark 看不到的问题

任务：
1. 完成主矩阵实验
2. 加重复运行
3. 生成图表
4. 检查是否出现“FG 为正但 BR 为负”的例子
5. 检查不同路径的效率差异

周末验收：
1. 至少产出 3 个强结论
2. 至少有 1 个案例清楚说明“旧 benchmark 会高估自进化”

## Week 4: 收尾与发布

目标：
- 交付 benchmark MVP
- 形成论文草稿

任务：
1. 整理代码与配置
2. 写 README 和复现文档
3. 生成最终 leaderboard
4. 写技术报告或论文短稿
5. 准备 appendix：任务切分、成本定义、失败案例

周末验收：
1. 外部同事能按文档复跑
2. 论文图表可直接进入草稿
3. 协议定义不再变化

---

## 8. 人力配置

## 8.1 最小团队

建议最少 3 人：

1. `Protocol Lead`
- 负责指标、协议、论文叙事。

2. `Infra / Eval Engineer`
- 负责 adapter、日志、汇总脚本。

3. `Experiment Owner`
- 负责 baseline 运行、故障排查、结果整理。

## 8.2 两人版本

如果只有 2 人：

1. 一人负责协议与论文。
2. 一人负责代码与实验。

此时必须砍掉第三环境，避免超载。

---

## 9. 风险与止损

## 9.1 最高风险

1. 环境太重，无法稳定复跑。
2. 参数路径 baseline 太慢。
3. 任务切分不合理，导致 FG/BR 无解释力。
4. 不同环境的成本口径无法统一。

## 9.2 对策

1. 优先做协议，不优先做环境扩张。
2. 参数路径 baseline 若 Week 2 仍跑不通，降级为 appendix。
3. 每个环境只保留 20-50 题的高质量子集。
4. 成本统一先用 `token + wall-clock + tool calls` 三项，不追求一步到位。

## 9.3 Go / No-Go 规则

到 Week 1 结束：

1. 如果连 1 个环境的 `T0 -> T1 -> 指标输出` 都跑不通，项目应收缩为“协议设计论文”，暂停 benchmark 实验。
2. 如果 2 个环境都能跑通，则继续做完整 MVP。

---

## 10. 最终论文主张

如果项目按计划推进，1 个月后最有可能形成的论文主张是：

1. 现有 benchmark 报告的是能力分数，不是自进化分数。
2. 只要加入 `Forward Gain + Backward Retention + Improvement Efficiency` 三元组，很多“看似变强”的方法会被重新排序。
3. 在外部路径与参数路径之间，哪条更优不能只看最终分数，必须看单位成本和旧任务保留。

---

## 11. 推荐结论

这项工作值得做，而且适合 1 个月内启动，但必须坚持三个原则：

1. **做协议，不做新世界。**
2. **先解决一个痛点，不追求大而全。**
3. **先交付能复跑的 MVP，再考虑扩展到更多环境。**

如果一定要给这个项目一句最准确的定位，它不是“新的大 benchmark”，而是：

**一套把现有 benchmark 变成“可衡量自进化”的评测协议。**

---

## 12. 单人 + Codex-Heavy 工作流

## 12.1 基本假设

当前执行条件如下：

1. 只有 1 位研究者负责推进。
2. Codex token 充足，可承担大部分读写、脚本实现、实验编排和文档整理工作。
3. 本地资源以 CPU 为主，GPU 可申请但不应作为 MVP 的必要前提。
4. API token 可申请，短期内不设上限。
5. 目标优先级为：**最快速做出可开源项目**，投稿作为后续选项，而不是当前约束。

基于这些条件，推荐策略不是“扩环境”，而是“压缩研究变量、强化自动化、把 Codex 当成主执行层”。

## 12.2 角色分工

### 你负责的事

1. 决定方向，不负责重复劳动。
2. 每天只做两次关键决策：
- 上午确认当天唯一优先目标。
- 晚上确认结果是否进入主线，还是降级为 appendix / exploratory。
3. 审核科学结论，尤其是以下三类：
- 是否真的存在 `FG > 0 且 BR < 0` 的反例。
- 是否真的能说明旧 benchmark 高估了“自进化”。
- 是否值得把第三环境纳入主线。

### Codex 负责的事

1. 阅读 benchmark 文档和代码。
2. 写协议文档、adapter、日志脚本、汇总脚本。
3. 跑 smoke test、回归测试、小样本实验。
4. 生成表格、图、失败案例、README、技术报告。
5. 维护 `decision log`，记录每次取舍的理由。

## 12.3 单人项目的硬约束

1. 主线只允许 2 个环境：`SkillsBench + tau-bench`。
2. `SWE-bench-Live` 只能作为可选扩展，且必须在 Week 2 结束后再决定是否加入。
3. 参数路径 baseline 默认降级：
- 优先 `Frozen / External / Prompt-Retrieval`
- `LoRA-lite` 只有在 GPU 申请稳定后才加入
4. 所有工作都必须围绕可开源结构组织，而不是围绕论文叙事先行。

---

## 13. 开源项目优先的目录与交付结构

建议项目从第一天就按开源仓库来组织：

1. `protocol/`
- 协议说明、指标定义、任务切分说明。

2. `adapters/`
- `skillsbench/`
- `taubench/`
- 可选 `swebench_live/`

3. `schemas/`
- `runs.schema.json`
- `summary.schema.json`

4. `scripts/`
- `run_eval`
- `aggregate_metrics`
- `build_leaderboard`
- `run_regression`

5. `results/`
- `dryrun/`
- `main/`
- `regression/`

6. `docs/`
- `README.md`
- `protocol_spec.md`
- `decision_log.md`
- `known_limitations.md`

这样的好处是：
- 任何一周结束时都可以直接开源。
- 如果论文来不及，项目本身仍然成立。
- Codex 更容易围绕稳定目录迭代。

---

## 14. 单人版四周执行节奏

## Day 1-3：立骨架，不做大实验

目标：
- 把仓库骨架搭起来。
- 固定日志 schema。
- 让一个 toy run 跑通。

必须完成：
1. `protocol_spec_v0.md`
2. `runs.jsonl` 字段定义
3. `summary.csv` 字段定义
4. 一个 adapter 的最小版本

禁止做的事：
1. 不要急着跑大模型大实验。
2. 不要提前做第三环境。

## Day 4-7：跑通第一个环境

目标：
- `SkillsBench` 跑通 `T0 -> T1 -> FG/BR/IE`

必须完成：
1. `Frozen` baseline
2. `External` baseline
3. 5-10 个任务 dry run
4. 一个自动汇总脚本

验收条件：
1. 日志完整
2. 指标自动计算
3. 至少出现 1 个有解释力的案例

## Week 2：加第二环境并冻结协议

目标：
- 加入 `tau-bench`
- 冻结核心协议

必须完成：
1. 第二个 adapter
2. 两环境统一输出格式
3. 回归测试脚本
4. 结果表模板

禁止做的事：
1. 不再大改指标定义
2. 不做复杂参数路径训练

## Week 3：做结果，不做新功能

目标：
- 找到最有论文价值的现象

重点寻找：
1. `FG > 0 但 BR < 0`
2. `IE` 很差但最终分数更高的 baseline
3. `pass@1` 看起来更强，但按 `FG/BR/IE` 排序后更差的系统

这周原则：
- 只加实验，不加新模块

## Week 4：整理成可开源项目

目标：
- 让别人能拉下仓库就知道怎么复跑

必须完成：
1. README
2. 最终表格
3. 失败案例
4. known limitations
5. 一页技术报告摘要

---

## 15. 测试计划

这个项目必须把“协议正确性测试”当成一等公民。否则最后只能得到一堆不可解释的结果。

## 15.1 指标测试

### 目标

确保 `FG / BR / IE / PDS / NIS` 定义正确、符号正确、边界行为正确。

### 具体做法

1. 人工构造 10 组 toy case。
2. 明确预期输出。
3. 用单元测试校验。

必须覆盖：
1. `FG > 0, BR > 0`
2. `FG > 0, BR < 0`
3. `FG = 0`
4. `Cost = 0` 的防护逻辑
5. `Replay score = 0` 时 `BR_ratio` 的行为

## 15.2 任务切分测试

### 目标

避免 `Replay / Adapt / Held-out` 泄漏。

### 具体做法

1. 对任务 ID 做集合检查。
2. 对任务模板元数据做近重复检查。
3. 如果 benchmark 支持轨迹级检查，再做轨迹来源去重。

验收：
1. 任一任务不能同时出现在 `Adapt` 与 `Held-out`。
2. 任一旧任务不能因为 rename 混入新任务集合。

## 15.3 Adapter 集成测试

### 目标

确保每个 benchmark adapter 输出一致。

### 具体做法

每个 adapter 至少做：
1. `3-5` 个任务 smoke test
2. 环境 reset 检查
3. 打分脚本检查
4. 日志完整性检查

## 15.4 方差测试

### 目标

避免“偶然一次跑好”。

### 具体做法

1. 每个主 baseline 至少重复 `3` 次。
2. 输出均值和标准差。
3. 如果方差过大，结果不进主表，只进附录。

## 15.5 回归测试

### 目标

协议冻结后，任何代码修改都不能悄悄改变历史结果。

### 具体做法

固定一组 `golden tasks`：

1. SkillsBench 5 题
2. tau-bench 5 题

每次修改 adapter 或 metric 脚本后，自动回跑：
1. score 是否变化
2. 日志字段是否变化
3. 运行时间是否异常膨胀

## 15.6 开源前验收测试

开源前至少满足：

1. 新机器可按 README 跑通 smoke test
2. 输出文件格式稳定
3. 一键汇总脚本可生成表格
4. known limitations 已写清楚

---

## 16. 需要提前确认的决策点

以下几点建议在项目开始前就锁死，不要边做边摇摆：

1. **主线环境是否只保留 2 个**
- 当前建议：是。

2. **参数路径 baseline 是否默认延期**
- 当前建议：是，除非 Week 2 前 GPU 稳定。

3. **结果进入主表的条件**
- 当前建议：至少 3 次重复，方差可接受，日志完整。

4. **第三环境是否进入主线**
- 当前建议：只有当 Week 2 已完成双环境协议冻结，才考虑 `SWE-bench-Live` 小样本。

5. **开源优先还是论文优先**
- 当前建议：开源优先。论文只是对开源协议的解释层。
