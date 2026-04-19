# 项目 Overview：SIP-Bench（协议层自改进评估基建）

## 一句话价值（先讲）
SIP-Bench 不是再造一个 benchmark，它把现有 benchmark 包装成统一评估协议，让“改进是否真实、是否可迁移、是否可复用、是否稳定、是否值得付出成本”能一次性输出证据。

## 项目是什么
我们把问题定义成“评测协议重构”而不是“任务发明”。

1. SIP-Bench 不新增 benchmark world，只接入现有任务基准（当前已接入 SkillsBench、tau-bench）。
2. 核心是统一 `T0 / T1 / T2` 与 `replay / adapt / heldout / drift` 的分阶段记录流程。
3. 任何下游 benchmark 只要实现 adapter，就能进入同一套协议统计和门禁。
4. 运行链路固定为：`plan -> (hydrate) -> execute/import -> validate -> aggregate -> evidence gate -> gallery`，每一步都有文件级产物可追踪。

## 意义在哪里
传统评测只看“某一次 heldout 分数”。

SIP-Bench 关心的是：  

1. heldout 有无提升（FG，`Forward Gain`）。
2. replay 是否遗忘（BR，`Backward Retention`）。
3. 提升是否稳定（PDS，从 T1 到 T2 的漂移/延迟保真）。
4. 提升是否值得代价（IE，效率，含 token、tool call、wall clock、成本）。
5. 运行是否可复现（失败原因、重试记录、attempt provenance 是否可复盘）。

这直接解决“只报一个高分”不能说明方法真的变强、能不能长期用的问题。

## 与对话中的关键问题一一对应

### 1) “是不是只做一致性监测，不捕捉额外信号？”
不是。一致性只是 infra 维度之一，另外还有：

1. FG/BR/BR_ratio/PDS/NIS（协议指标）。
2. 多次 attempt 的失败签名归类（docker/credentials/network/verifier/script）。
3. 重复 run 的均值与标准差（fg_std、br_std、ie_std、pds_std）。
4. 代价维度：token_total、tool_calls_total、wall_clock_seconds、cost_usd。

### 2) “T2 是怎么定义的？”
T2 是延迟/漂移后的一次评估点，定义为：

1. `PDS = score(T2, heldout_or_drift) - score(T1, heldout)`。
2. 若有 drift 分区，优先用 drift；否则退回 heldout 作为 T2 目标。
3. 实现上在 `src/sip_bench/metrics.py` 与 `src/sip_bench/protocol_runner.py` 统一约定。

### 3) “这个东西和 EvoAgentBench 的区别是什么？”
我们不是和它同层竞争。

1. EvoAgentBench：典型是 benchmark-first，重点是“经验复用后是否提升 unseen test”。
2. SIP-Bench：protocol-first，重点是“提升在哪、回退在哪、要多少钱、是否稳定、失败在哪发生”。
3. 两者互补。Evo 类任务可先给出是否有泛化，我们再给出“质量代价剖析”。

### 4) “为什么有工程化意味，是不是没创新？”
有工程味，但这就是方法学基础设施创新的特点：  

1. 把评估对象从“一个数字”提升为“可复核的协议记录”。
2. 同一套 adapter 接口覆盖多 benchmark，不绑定单一任务。
3. 同一层门禁可复用在不同实验组（repo-local、fixture、import-only、live）。
4. 明确了非天花板和 evidence 门禁，避免饱和任务误导结论。

### 5) “SkillsBench 一个 task 有多个 skill，泛化怎么测？”
当前实现更适合回答“任务集内的自适应轨迹”：  

1. 同任务不同 skill 组下我们能做重复运行、记录协议指标和成本。
2. 真正“跨 skill 泛化”没有完整成体系实现；这是下一阶段实验设计缺口。
3. 现有路线优先先做 protocol 可验证和重复稳定，再把 skill-level 泛化指标作为下一代增强项。

### 6) “任何 benchmark 写 adapter 就能接入吗？”
有统一模板，但不是一句话就能完成。

1. 必须提供任务发现、分割构建、命令构建、执行结果导入和 schema 映射。
2. 需要每个 benchmark 的执行约束（日志、输出字段、失败码）适配到 SIP schema。
3. 一旦 adapter 完成，后续跑法、门禁、图表与复现都复用同一套脚本。

### 7) “本地测试有用吗？是否该有真实实验？”
有用，但边界要写清。

1. 本地/fixture 跑法是 CI 与版本回归的基础保障（schema、脚本、门禁、结果格式）。
2. 真正有说服力的 claim 仍以 real-suite（目前以 SkillsBench oracle + tau 历史 import）为主。
3. 本地结果用于“流程不坏 + 复现稳定”；真实结果用于“结论成立”。

### 8) “这算不算可发布给高星开源？”
能发布的部分已足够强，关键是透明地放在同一叙事里：

1. 明确发布边界：核心发布路径已可复现并通过门禁。
2. 非核心难题（如更大规模非天花板 bundle）按实验任务继续迭代。
3. 只把达到门禁的证据纳入对外主故事，避免超出承诺。

## 当前进展（截至目前）
1. 协议层落地：核心评估模型（FG、BR、BR_ratio、IE、PDS、NIS）已稳定实现并写入 summary。
2. 复用层落地：SkillsBench、tau-bench 两大环境已形成统一协议入口。
3. 证据链落地：suite report、attempt 记录、失败归类、evidence 门禁都已入库并可重生成。
4. 复现实验链落地：`run_release_checks.py`、`evidence_gate.py`、`build_results_gallery_artifacts.py` 已闭环。
5. 目前主要缺口：扩充稳定的非天花板高质量实验家族，尤其在 hard-path 与跨任务重复性层面。

## 可直接讲解的叙事顺序
1. 先说明“为什么普通 leaderboard 不够”。
2. 再说明“我们做的是协议层，不是新 benchmark”。
3. 再给一个案例：T0/T1 同时看 FG/BR/PDS，说明改进可能是假的。
4. 再说明复现能力：同一配置可重跑、可审计、可对比。
5. 最后讲明当前证据主链与后续扩展路径（目前支持任务主要是 protocol-first 的可复现性与非天花板验证链）。
