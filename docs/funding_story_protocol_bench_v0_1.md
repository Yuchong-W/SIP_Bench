# 面向支持申请的项目 Story：SIP-Bench（Protocol + Incremental Protocol）

## 一句话价值
SIP-Bench 不是再造一个 benchmark，而是把现有 benchmark 改造成“可复现、可对照、可复用”的统一协议层。它的核心贡献是：用固定协议把**提升（Gain）**、**遗忘（Backward Retention）**和**效率（IE）**同时量化，并把实验流程固化为可复核的证据链，避免“只有单点分数不可靠”的常见评价偏差。

## 我们解决的具体问题
1. 现有 benchmark 过度关注单次 leaderboard 分数，难以区分“提升是否真实可复用”。
2. 跨任务/跨阶段对比缺少统一日志与审计标准，难以复现。
3. 证据链通常不可追踪（没把运行配置、失败原因、重试轨迹与指标统一绑定）。

SIP-Bench 用同一套 `protocol suite`、`suite_report.json`、`summary.jsonl` 和 `plan matrix` 门禁把上述问题统一到一个可执行工程路径里。

## 为什么这是“有潜力”的开源项目
- `skillsbench + tau-bench historical` 两种互补场景同时接入，能在一个代码库内支撑 live 与可解释评估风格。
- 关键指标不只是“分数变高”，而是包括 forward gain / backward retention / improvement efficiency（FG/BR/IE）与 `evidence` 判定。
- 公开脚本覆盖从“任务采样 → 运行 → 汇总 → 图表/表格重生成 → 质量门禁”的完整闭环，别人可以直接复现和复盘。
- 与其他 benchmark 项目相比，它更像“基础设施平台”，更容易被研究者/工程团队复用。

## 当前仓库状态（可直接展示给负责老师）
- 代码与脚本层：新增/修订 `run_release_checks.py`、`run_protocol.py`、`protocol_runner.py`、`runner.py`、`check_plan_matrix.py`。
- 复现治理层：新增 issue 模板、contributing 指南、onboarding checklist、release checklist 与 manifest。
- 证据治理层：新增 evidence 相关图表、表格、可重生成脚本及数据快照。
- 质量门禁层：单元测试通过、schema 校验通过、结果快照校验通过、plan-matrix 严格模式可运行。
- 兼容性层：新增/更新 support matrix 与实验边界，避免“环境依赖踩坑”。

## 已完成的关键验证（可以口头展示）
- `python3 -m unittest discover -s tests -p 'test_*.py'` 全量通过。
- `python3 scripts/run_release_checks.py ... --plan-matrix ...` release 检查通过（含 plan-matrix/数据校验/聚合验证）。
- `python3 scripts/check_plan_matrix.py --protocol-dir protocol --config ... --strict` 已验证：  
  - SkillsBench 正常路径检查完整  
  - tau-bench historical import-only 路径不再误判 execution 产物缺失  
  - 与协议语义一致、可批量门禁。  
- `results_gallery` 与 `evidence_readme` 已把关键图表和表格映射到源文件与命令。

## 与老师汇报时可强调的“差异化叙事”
1. 不只是“跑更多实验”，而是先把**可复现性协议**做对，降低后续实验无效成本。  
2. 我们有“方法学价值 + 工程价值 + 复现价值”的三层闭环，不是短期炫图。  
3. 平台化程度高：后续接入新 benchmark 的成本可显著低于从零写评测脚本的方式。  
4. 已经形成可公开审阅的证据结构（命令、数据、schema、图表、阐释）。

## 这次为什么值得继续投入
现阶段项目已经到了“能跑、能证、能讲故事”的门槛，但想进入顶会友好与高星开源状态，还需要：
- 更大规模的非天花板实验（跨更多 run_family 的重复与稳定性）
- 第三环境适配（减少 benchmark 特异性疑虑）
- 更强显著性与不确定性估计（让结论更硬）
- 少量人工参与的清洗与解释，补齐论文式写作材料

## 预算/支持申请清单（面向导师）
- 目标：把 v0.1 平台稳定到“可公开宣称顶会候选前置条件”。
- 需要支持：  
  - 更高并发的实验配额（API/算力）以完成 2-4 个高价值重复 bundle。  
  - 1-2 周研发保障时间（用于结果扩展和显著性补充）。  
  - 1 名协同角色（偏实验管理）帮助维护任务池、整理失败日志与复盘。  
- 预期收益：以当前工程成本，单次新增实验可复用 70%+ 的现有脚本；边际产出高于重新搭建每个环境独立评测链。

## 现在可直接执行的下一步（支持后优先级）
- 一周内完成剩余 P4 里程碑中：第三环境接入验证、显著性增强、投稿级实验表述收口。  
- 两周内形成一页 paper 草稿（intro/method/eval/limitations）并绑定当前证据目录。  
- 三周内发布可公开对外演示版（含 README 快速导览、复现命令、主图和主表）。  

## 联系人准备（汇报模板）
- 强调：不是“跑一个 benchmark”，而是“建立可复用评估协议标准”。  
- 用一句话收口：  
  “我们在构建一个能让评估从‘一次性打分’升级为‘可重复、可追责、可扩展’的通用协作协议，目标是支持下一轮更强的 self-improvement 研究。”
