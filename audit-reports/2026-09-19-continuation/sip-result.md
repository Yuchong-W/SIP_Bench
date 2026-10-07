# SIP-Bench upstream continuation audit

日期：2026-09-19

## 交付对象

- 上游仓库：`Yuchong-W/Protocol_Bench`
- 上游 PR：<https://github.com/Yuchong-W/SIP_Bench/pull/1>
- PR 标题：`feat: add synthetic medical adapter and credential-free validation lane`
- base：`main` / `a0c826f6417ae5ec69fcc46c23c1ac2c603adc0c`
- implementation ancestor：`9cd6626e86e50ad41b975177e0c960084b7098e3`
- continuation audit commit：`fec63bcdc80d5af38efbd064bce0d98cf75ec75d`
- 状态：OPEN，GitHub 判定 `MERGEABLE`

本次继续工作采用现有上游 PR #1 的快进路径。没有创建新的上游 PR，没有改写历史，没有合并，也没有直接推送上游 `main`。

## 依赖关系

现有 fork staging PR 为 <https://github.com/Frankie-Xu/SIP_Bench/pull/1>，base 为 `medical-native-suite`（`8b21b4047dd636f369dc144af709ebeae52499ab`），head 为 `medical-native-ci`。上游 PR 已快进到包含同一实现和审计记录的 fork head，因此上游 PR 是 canonical review surface；fork staging PR 没有再产生新的代码包或新的依赖分支。

fork 远端两个分支均已核对：

```text
navilia-medical-adapter  fec63bcdc80d5af38efbd064bce0d98cf75ec75d
medical-native-ci        fec63bcdc80d5af38efbd064bce0d98cf75ec75d
```

## Diff、secret 与 artifact 审查

- 相对上游 `main` 的变更范围为 28 个文件，覆盖 medical adapter、native result-only suite、schema、release checks、CI、文档和测试。
- `git diff --check` 通过。
- 对提交 diff 检查了常见 API key、AWS key、私钥、密码、secret/token 文字模式，没有发现凭据。
- tracked tree 中没有 `.env`、secret、credential、token 或 `ci-artifacts` 文件。
- `results/medical_demo/` 是仓库内的明确合成示例结果；CI 生成的 release report 和 native suite 输出只上传为 workflow artifact，不写入源码树。

## 验证证据

本地重新运行：

- unittest discovery：104 项，99 通过，5 跳过；跳过项为可选 EvoAgentBench 集成。
- release checks：返回码 0，native result-only suite 生成 12 runs / 24 records。
- native report 含 token、tool calls、wall-clock、USD、human-interventions 成本字段，failure family，以及 `combined_runs.jsonl`、`summary.jsonl`、`suite_report.json` 的 SHA-256。
- 非严格 plan matrix 有既存结果目录缺失 warning（100 条），失败数为 0；这不阻断 release checks。

同一实现 ancestor 的 fork CI：<https://github.com/Frankie-Xu/SIP_Bench/actions/runs/35370024218> 为 SUCCESS，上传 artifact `sip-bench-native-suite-report`，大小 14,513 bytes，未过期。审计记录提交本身也通过了 fork CI：<https://github.com/Frankie-Xu/SIP_Bench/actions/runs/35423398837>，artifact `sip-bench-native-suite-report` 大小 14,480 bytes，未过期，下载地址为 <https://api.github.com/repos/Frankie-Xu/SIP_Bench/actions/artifacts/10577914906/zip>。

上游 workflow run：<https://github.com/Yuchong-W/SIP_Bench/actions/runs/35417806021>，head SHA 为实现 ancestor `9cd6626...`，状态为 `action_required` 且没有 job 输出。这是 fork workflow 的仓库审批门槛，不是测试失败；同一提交的 fork CI 已成功。

## 结论

native suite 与 credential-free CI 已通过现有上游 PR #1 交付，review URL、实现 ancestor、审计记录、依赖关系和同 SHA fork CI 证据均已固定。后续只需上游维护者批准该 workflow 并完成正常 review；本次不执行合并。
