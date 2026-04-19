# 仓库结构说明

## 一句话地图

SIP-Bench 分三层：`src/` 是协议核心逻辑，`scripts/` 是运行与发布工具链，`protocol/ + results/ + docs/` 是实验配置与可复现实证据。  
目标是让一个 benchmark 环境（如 SkillsBench、tau-bench）只要接入 protocol adapter，就能在统一协议下跑出可复核指标。

## 顶层目录职责

- `src/`
  - 协议和运行时核心代码。
  - 关键文件：
    - `src/sip_bench/metrics.py`：FG/BR/PDS/IE 等指标与摘要聚合逻辑
    - `src/sip_bench/protocol_runner.py`：suite 级运行与 evidence 分类
    - `src/sip_bench/runner.py`：plan 执行、导入、重试与失败归类
    - `src/sip_bench/validation.py`：schema 校验器
    - `src/sip_bench/adapters/*`：benchmark adapter 接口与实现
- `scripts/`
  - 命令层封装与发布验证脚本。
  - 关键文件：
    - `scripts/run_protocol.py`：一键执行协议 suite
    - `scripts/run_release_checks.py`：发布前一致性检查
    - `scripts/evidence_gate.py`：Evidence 门禁判断
    - `scripts/build_results_gallery_artifacts.py`：图表与表格重生成
    - `scripts/aggregate_metrics.py` / `scripts/validate_records.py`：指标聚合与 schema 校验
- `protocol/`
  - suite 配置与环境变量模板。
  - 各 benchmark 的运行脚本（`*.json`）和可选 `.env.example`。
- `schemas/`
  - JSON schema 约束（`runs.schema.json`、`summary.schema.json`、`protocol_suite.schema.json`）。
- `tests/`
  - 单元测试、fixture 与最小稳定性验证。
- `docs/`
  - 设计说明、里程碑、复现说明、结果画廊与实验日志。
- `results/`
  - 跟踪证据：干跑样本、真实 suite 报告、summary、attempt 级 artifacts。
- `benchmarks/`
  - 本地 benchmark 代码仓库依赖目录（本地缓存，不是代码发布主面）。

## 发布文档入口

- `docs/release_manifest.md`：发布物清单与纳入范围
- `docs/release_checklist_v0_1.md`：发布前检查项
- `docs/evidence_readme.md`：复现实验命令与产物对应关系
- `docs/results_gallery_post_v0_1.md`：对外结果展示入口
- `docs/overview.md`：项目叙事与方法说明（对外汇报主文）

## 运行时忽略目录（仓库内存在但不纳入版本发布）

以下目录在仓库中用于本地运行，不会进入可追踪发布面（已 `.gitignore`）：

- `.venv/`, `.pydeps311/`, `.uv-cache/`
- `benchmarks/skillsbench/`, `benchmarks/tau-bench/`
- `results/*` 中大量运行时生成目录（如 `results/real_jobs*`、`results/prepared_probes/`、`results/dryrun/artifacts/`）
