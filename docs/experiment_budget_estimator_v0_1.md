# SIP-Bench v0.1 实验预算估计器（草案）

目标：给新实验提供“能否在两天内完成、风险可控、是否需 API 资源”快速评估。该文档不是审计账单，仅用于规划与门控。

## 估计框架

对每个 suite，先按三个量计算：

- `N_tasks`: 每次 run 的任务规模
- `N_runs`: run 数量（`T0/T1 × repeat × split`）
- `I_retry`: 平均重试比例（`(实际执行次数-最小执行次数)/最小执行次数`）

估算时间基于两个分量：

- `T_local`: 本地可复现实验时间（import-only / fixture）
- `T_dock`: 容器执行时间（Docker）
- `T_total ≈ N_runs × (T_local + (1 + I_retry) × T_dock) × risk_factor`

`risk_factor` 由 0.8~1.8 取值：

- 0.8：已有完整缓存、固定镜像、网络稳定
- 1.0：标准 Linux-first 环境
- 1.8：高并发机器/网络抖动、首次启动环境、无预热镜像

## 套件级预算（当前仓库基线）

| 套件 | 主要依赖 | N_tasks | N_runs | 本地/纯导入 | 初始估计 (`risk_factor=1.0`) | 失败/重试风险 |
| --- | --- | ---: | ---: | --- | --- | --- |
| `results/dryrun/sample` | fixture | 12 | 1 | ✓（import-only） | `~2 分钟` | 低 |
| `skillsbench_oracle_real_suite` | SkillsBench + Docker | 4 | 4 | ✗（需执行） | `~20 分钟`（首次运行可达 `~40 分钟`） | 中（infra/容器） |
| `tau_bench_retail_historical_suite` | tau-bench + import-only | 6 | 5 | ✓（导入） | `~3 分钟` | 低 |
| `skillsbench_codex_external_prepared_suite` | SkillsBench + Docker | 2~8（按 bundle） | 4~16 | ✗（需执行） | `~30-90 分钟`（取决于路径和重试） | 高（provider + infra） |
| `mock-bench`（适配器回归） | fixture | 1~4 | 1~4 | ✓（import-only） | `~1-5 分钟` | 低 |

## 阈值门控（建议）

先验门槛用于决定是否进入主实验：

- `T_total > 60 分钟 且 I_retry > 0.3`：建议先缩小任务规模或固定更多 seed
- `风险重试 > 2x`：建议先清理环境再重跑，而不是扩大覆盖
- `重复实验后失败分布偏移 > 1.5`：优先做失败签名归因，而非新增 benchmark

## 预算复用规则

1. 每个 suite 至少保留一次“可复现快照运行”（本地命令 + 输出路径）。
2. 产出到 `docs/results_table_data/` 与 `docs/figures/` 的主资产，应在同一 PR 中可 1 分钟内重建。
3. `release` 判定只依赖可复现资产，不依赖 provider-backed 实验。

## 典型执行顺序（高性价比）

1. `dryrun` 与 fixture 导入（`run_release_checks`）
2. `skillsbench_oracle_real_suite` 关键路径
3. `tau_bench_retail_historical_suite` 对照路径
4. mock-bench/smoke 适配器回归

