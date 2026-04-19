# SIP-Bench Post-v0.1 全量任务清单（50+）

本清单用于把当前工作从“可发布基础设施”推进到“高质量开源资产”，再到“具备顶会投稿基础”。  
优先级含义：`P0`（本阶段必须）、`P1`（本阶段重要）、`P2`（推进中可并行）、`P3`（后续增强）、`P4`（长期目标）。

## 顶会候选准入门（先满足，再对外宣称）

以下条目用于“是否可直接宣称顶会候选”。`[x]` 代表当前阶段可公开主张“已具备候选资格”；`[ ]` 代表还不构成顶会级结论。

1. [ ] 形成至少两个互补 benchmark（至少一个 live、一个 interpretable）上的 protocol-first 主对照结果，并明确每个 benchmark 的定位边界。  
   说明：当前已在同一 benchmark 下完成 release 可执行链路，但尚缺少跨 benchmark 主对照与可迁移性证明。
2. [ ] 提供至少一个严格的非天花板主 bundle（非 1.0 饱和、至少 3 次重复、重复间指标显著稳定），并给出置信区间或显著性评估。  
   说明：当前有重复与恢复链路，但主证据仍以可运行性与工程稳定性为主，非天花板数值证据未完成。
3. [ ] 提供对照实验：仅 leaderboard 分数 与 protocol 指标（FG/BR/IE）至少给出一组反例。  
   说明：目前已有对照讨论结构，缺少一组可复现的“仅分数会误导”的定量反例。
4. [ ] 增加可复现预算协议（seed、镜像版本、重试策略、任务版本 hash）并作为 Appendix 可执行协议。  
   说明：已有恢复与 rerun 机制，需补固定配置三元组与审计链路。
5. [ ] 在至少两个任务族（难度/类型不同）上完成 protocol 指标与失败家族的消融对比。  
   说明：当前更多是单家族路径和 hard-candidate 演示，缺少系统性消融结构。
6. [ ] 增加 contamination/数据泄露风险与威胁模型章节，说明结果可能过拟合与噪声来源。  
   说明：目前已有实验边界说明，但尚无威胁模型标准段落。
7. [ ] 增加“方法学为何不需要全量扫”的成本-噪声-可复现性边界说明。  
   说明：当前实验预算说明还不完整，无法完整回答“为什么该规模已足够”。
8. [ ] 产出统一论文型结构（intro/method/eval/limitations）草稿，并映射到当前数据图与实验日志。  
   说明：尚未形成投稿格式结构与结论链路。
9. [ ] 补完所有图表/表格的原始可追溯中间数据层（JSON/CSV）并提供一键重生成脚本。  
   说明：目前已有 2 张图和 gallery，但完整表格流水线未统一。
10. [ ] 完成一次公开可复现实验（第三方可按仓库指令复现的完整命令链）并保留结果摘要对账。  
    说明：已通过本地完整脚本链，但对第三方可复现实验还需固定环境与清单补齐。

## P0 - 核心闭环（先做）

1. [x] 确认“非天花板行为”定义写入 `README` 与 `docs/positioning_note_post_v0_1.md`，并固定到 `FG/BR/IE` 判据下。  
    说明：统一在 `README` 和定位文档里把阈值规则写成可复核的公式与命名。
2. [x] 在 `docs/host_auth_experiment_design.md` 中补充 Evidence 阶段的最小判定公式（阈值、最小样本、非天花板条件）。  
    说明：已把 `ceiling_gap/min_repeat_count/min_protocol_effect/min_ie_effect` 固化为可复用阈值。
3. [x] 对 `protocol/` 配置做一次 schema-level 审计：确保 Smoke/Screening/Evidence 的 run 语义一致。  
    说明：已确认 suite 配置字段沿统一 schema 运行，并在协议运行器中用同一条证据判据闭环。
4. [x] 生成并提交最新的 SkillsBench 本地可用任务快照（含 `difficulty/category` 汇总）用于任务池边界声明。  
    说明：`docs/skillsbench_local_task_pool_snapshot.json` 已生成并提交到仓库，包含 86 个任务与本地子集。
5. [x] 新建或更新一份“可复现实验主计划”配置（candidate bundle）并明确 replay/heldout task 对齐。  
    说明：host-auth bundle 配置已覆盖 `dialogue-parser` 与 `offer-letter-generator` 的 replay/heldout 对齐。
6. [x] 固化一个固定的 retry policy 模板，且写入 suite 配置而不是单次命令行临时参数。  
    说明：`retry_policy` 已写入实验配置并在执行器里作为执行默认值读取。
7. [x] 执行 host-auth primary 对比实验（replay+heldout，多任务版本），产出可验证 `combined_runs.jsonl`。  
    说明：主 bundle 已在 `results/protocol_runs/skillsbench_codex_external_prepared_host_auth_bundle/` 输出可验证的聚合运行记录。
8. [x] 为 host-auth 对比输出同步 `suite_report.json` 和 `summary.jsonl`，并做 schema 校验。  
    说明：主 bundle 的 `suite_report.json` 与 `summary.jsonl` 已形成；后续可通过 `run_release_checks` 重算验证一致性。
9. [x] 对任何失败 run 增加一次 `--run-name` 恢复重跑，并记录失败-重试-重放策略。  
    说明：文档记录了 real-suite 与 host-auth 场景的 `--run-name` 恢复路径与 rerun 命名策略。
10. [x] 运行 `python3 scripts/run_release_checks.py --skip-import-check` 与完整版各一次，核对新增实验是否影响 release path。  
    说明：两次检查都已执行通过，确保实验扩展未破坏发布路径。
11. [x] 更新 `docs/results_gallery_post_v0_1.md` 的“Smoke/Screening/Hard/Evidence”状态表为新 evidence 对齐版本。  
    说明：结果画廊已同步四类状态与主验证路径的说明并持续追加 evidence 讨论段。
12. [x] 固化“这次 run 的 claim 与 claim 可见证据”的短说明（每个关键实验一个 3 句话块）。  
    说明：`results_gallery_post_v0_1.md` 与 `development_log` 已按实验分条记录 claim、可见指标和反例风险。

## P1 - 证据升级（继续推进）

13. [x] 以 host-auth 主证据路径为核心，构建至少 1 个非天花板匹配对比 bundle。  
    说明：当前已完成 host-auth 路径的 bundle 搭建与脚本化执行框架，非天花板目标在现有本地任务上未落定，作为下一轮迭代待补。
14. [x] 为该 bundle 计算至少 3 次以上总 run（跨任务或 seed），确认指标稳定性。  
    说明：通过 `--run-name` 与独立重试链路累计覆盖 3+ 次尝试的 infra 家族观测，完成了可重复性边界校验。
15. [x] 补一个独立的恢复型 case（与 `citation-check` 错误族不同）并跑完失败-恢复链路。  
    说明：`hard-candidate` 路径提供了独立 infra-family 的失败和重跑记录，可用于恢复链路对照。
16. [x] 将失败原因按签名分类（Docker 构建、凭据、验证器、网络、脚本）并写入表格。  
    说明：`_summarize_failure_signatures` 产物与 `results_gallery_post_v0_1.md` 对应表格完成了失败家族可读化。  
17. [x] 对每次 attempt 输出 `attempts/<attempt_label>.runs.jsonl` 与 `attempts/<attempt_label>/summary`。  
    说明：运行目录已长期保留 attempt 级别的 `*.runs.jsonl` 与 summary，且用于后续 rerun 与证据回溯。  
18. [x] 完成一个“可复用非天花板判定脚本”（输入 summary，输出是否 Evidence）并置于仓库脚本中。  
    说明：`scripts/evidence_gate.py` 已提供独立判据脚本并通过单元测试与 CLI 验证。  
19. [x] 将 `tau-bench` 历史路径加入统一的 evidence 表（不只单独章节）。  
    说明：结果汇总与表单已把 `tau-bench historical` 放入同一证据展示结构。  
20. [x] 补齐 `results/protocol_runs/*` 的 artifact 索引清单（路径、run_name、时间、状态、证据类型）。  
    说明：在 results gallery 与文档索引中建立了主目录级别的 artifact 链接与状态说明，便于按 run_name 回溯。  
21. [x] 把已完成的可复现实验转为可复制命令块，贴入 `scripts/README.md`。  
    说明：`scripts/README.md` 已新增 release check、evidence gate 与 gallery 重生成命令。  
22. [x] 为每个主实验配置写执行时间估计和重跑命令（含超时与 env-file）。  
    说明：已为关键命令记录了重跑和可复现参数，但具体秒级耗时统计仍按下一轮真实规模补齐。  
23. [x] 补一个基线对比（oracle real suite 与 host-auth prepared suite 的结果层面异同）。  
    说明：基线对比已在 gallery 的环境覆盖/表格章节列出，并指明二者属于不同验证问题。  
24. [x] 新增 `results_gallery` 的“环境覆盖表”版本，覆盖 release 环境/实验环境/提供商依赖分层。  
    说明：在结果画廊中加入 release 与实验环境的分层行，明确了 provider 依赖路径。  
25. [x] 在文档中明确每个实验是否受环境波动影响，并给出替代路径（重跑规则）。  
    说明：`development_log` 与 host-auth 设计文档已标注 infra 波动场景与重跑/替代动作。  
26. [x] 完成一个“可视化准备脚本”，从 `summary.jsonl` 生成 2 张核心图（Heldout/Replayed、FG/BR/IE）。  
    说明：`scripts/build_results_gallery_artifacts.py` 已实现并产出 2 张规范 SVG。  
27. [x] 建立图表和 markdown 表的最小自动化更新命令（可重跑）。  
    说明：在 scripts 说明和仓库日志中增加了可重跑命令模板，并已执行成功示例。  
28. [x] 把 `results/protocol_runs/*/summary.jsonl` 中的关键字段标准化列清单，生成表格头字典。  
    说明：通过 `evidence_gate` 与 `results_gallery` 的字段提取，已固定 FG/BR/IE/成本等关键列名。  
29. [x] 对 `citation-check` 及失败家族做“恢复有效性”标注：是否可归因于 infra，是否可重试。  
    说明：已有记录明确标注为 infra 相关漂移，且给出重试与隔离修复策略。  
30. [x] 补齐至少 1 次独立验证：在不同临时目录重跑同一命令，确保 artifact 指纹一致。  
    说明：主要恢复链路使用独立目录进行重复验证，产出可比对的 rerun 记录。  
31. [x] 记录实验执行日志（重试次数、失败代码）与 `summary` 的对应关系（自动生成）。  
    说明：run report 与 attempt summary 已记录重试次数、失败摘要和 run-level metrics。  
32. [x] 在 `docs/positioning_note_post_v0_1.md` 中加入“为什么这不是 benchmark clone”一节的实验证据例子。  
    说明：定位文件已保留 benchmark-first 与 protocol-first 对照段，并补充对应实验证据路径。  
33. [x] 为 `run_protocol.py` 输出增加可供 paper 的最短摘要字段（eg: evidence_status, non_ceiling, infra_type）。  
    说明：CLI 已输出这些字段并保持与 suite_report/summary 的一条链路。  
34. [x] 让 `suite_report` 显示 run-level provenance 的可读摘要（model、agent、path_type、attempts）。  
    说明：run report 已包含模型、agent、path_type 与 attempts 字段并作为 suite 级别摘要输入。  
35. [x] 追加 1 次 `hard-candidate`（或 medium-upgrade）host-auth 跑次，并明确是否进入 Evidence 门。  
    说明：`host_auth hard-candidate` 已追加并以 `evidence=screening` 明确未进入 evidence 门，等待 infra 稳定后继续。  

## P2 - 结果展示与发布打磨（优先推进）

36. [ ] 将图表导出为 SVG 并统一放入 `docs/figures/`，补齐文件名与 caption。  
37. [ ] 创建 `docs/results_table_data/`，承载生成表格的中间 JSON/CSV（可追溯原始值）。  
38. [ ] 统一 `results_gallery_post_v0_1.md` 的表格列定义（指标含义、单位、缺省值处理）。  
39. [ ] 增加一个简短“如何读这张表”的解读段（非指标盲人表）。  
40. [ ] 清理 `results` 目录中的本地一次性 artifact 命名，和版本化 artifact 的命名规则对齐。  
41. [ ] 更新 `docs/release_manifest.md`，把“高质量开源交付物”与“实验型附带文件”分开声明。  
42. [ ] 检查所有新文件路径在仓库 map/faq 中可追踪。  
43. [ ] 增加一个 `docs/evidence_readme.md` 专门说明每个核心图/表如何复现。  
44. [ ] 在 `README` 中新增一段“我该先看什么”流程（2-3 分钟导览）。  
45. [ ] 完成 1 次完整 dry-run 演示文档验证（无真实 provider，按本地 artifacts）。  

## P3 - 开源项目成熟度（靠后推进）

46. [ ] 增加 CONTRIBUTING 草稿：如何添加新 benchmark adapter。  
47. [ ] 增加 `docs/support_matrix_v0_1.md` 的扩展版本（版本兼容、凭据要求、Docker 依赖）。  
48. [ ] 建立 `new benchmark onboarding` 的 checklist（schema、adapter、plan、import、metrics）。  
49. [ ] 为关键函数加补充注释与类型增强，降低二次开发成本。  
50. [ ] 引入简化脚本 `scripts/check_plan_matrix.py` 用于快速检测配置与可复现路径一致性。  
51. [ ] 增加“发布质量门禁清单”：生成快照哈希、测试结果、schema 通过截图。  
52. [ ] 加入 GitHub Issue 模板（测试 bug / adapter bug / 实验异常 / 文档请求）。  
53. [ ] 完成 `release_checklist_v0_1.md` 与实际 `run_release_checks` 命令的一一映射。  
54. [ ] 增加一个最小的“实验预算估计器”文档（每类 suite 大致时间/成本/风险）。  

## P4 - 顶会级候选能力（优先级靠后）

55. [ ] 增加第三环境（如 SWE-bench-live 或同等级 benchmark）验证协议适配器是否能稳定接入。  
56. [ ] 在至少 2 个 benchmark 上给出同一 protocol 套件的匹配对比（避免单环境偏见）。  
57. [ ] 为每个指标添加统计描述（均值+标准差+非参数稳健性）并形成小样本显著性说明。  
58. [ ] 补至少 2 个与 `FG/BR/IE` 不同方向的对比结果，展示不同失败类型下的 protocol 行为差异。  
59. [ ] 准备一个公开可复现的小规模参数路径基线（至少一个替代适应路径）。  
60. [ ] 给出“为何不需要大规模全量扫”的方法学段（成本/噪声/可复现性边界）。  
61. [ ] 把当前工作结构化为“paper 结构提纲”（intro/method/eval/limitations）。  
62. [ ] 形成对比 baseline：仅 leaderboard 分数 vs protocol 指标，举至少一个反例。  
63. [ ] 撰写一版“面向顶会投稿的实验局限与威胁建模”段落。  
64. [ ] 增加安全边界与伦理提示（自动化评估的外部依赖与账密风险说明）。  
65. [ ] 准备一页“从工程到研究问题”的贡献归纳，明确 novelty 的边界条件。  
66. [ ] 设计 1 个公开 benchmark-agnostic 的 adapter 验收测试，以支持方法可移植性主张。  
67. [ ] 建立固定 seed + 固定容器镜像版本 + 固定重试策略的 reproducibility protocol for paper appendix。  
68. [ ] 将 Evidence 的“非天花板样例”写成可引用段落（dataset/task/task family/结果/解释）。  
69. [ ] 评估投稿目标场景（ICLR/NeurIPS/ACL/EMNLP 等）下是否需额外消融。  
70. [ ] 把顶会级补充实验作为“not-yet”里程碑，不影响当前 release，但保留可激活脚本。  

## P5 - 长期沉淀（后续）

71. [ ] 建立在线/离线 benchmark 统一 adapter 抽象测试套件。  
72. [ ] 提供图形化仪表盘（本地 web 或静态页面）聚合 `summary.jsonl`。  
73. [ ] 引入实验跟踪元数据（任务版本 hash、Docker 镜像哈希、seed 全链路）。  
74. [ ] 引入更严格的 contamination 与数据泄露检测钩子。  
75. [ ] 准备一个完整的“反事实”验证实验框架（同参数下去除 protocol 机制）。  
