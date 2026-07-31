# 人类可读、证据可核验的诊断报告

`/ask` 的 Fact Ledger 路径同时服务两类读者：正文供运维人员快速决策，机器附录供程序校验和事后审计。正文不是 Ledger 的字段转储，附录也不承担解释任务。

## 报告边界

正文固定包含诊断概览、现象描述、关键证据、可观测性摘要、证据关联与因果链、根因结论、修复建议、验证步骤和注意事项。

- 正文使用 `namespace/name` 等可读名称，不显示 Fact ID、内部 entity ID 或 JSON。
- 精确状态、数值、单位、来源和因果关系只能来自 validated FactRecord 或通过校验的 source-backed observation。
- AI 可以解释“证据说明什么”，但不能改变事实、补算精确值或扩大因果范围。
- `机器可核验附录` 保留全部已验证事实、根因引用、coverage 限制和合同版本。

## 混合数据源优先级

可观测性按 Metrics、Logging、Tracing、Kubernetes 和 Topology 等通用维度组织，不按故障类型选择渲染路径。

一个 provider 的空结果只描述该 provider，不代表整个维度没有数据：

- Elasticsearch 为空、Kubernetes previous logs 有有效内容时，Logging 为“部分数据”，展示真实日志信号。
- Tempo 为空、DeepFlow 有 flow 时，Tracing 为“部分数据”，展示请求、响应码、耗时和 trace ID。
- 只有该维度没有任何 substantive signal 时，才显示“查询完成，当前窗口未发现匹配记录”。

`semantic_success=true` 只是 observation 的必要条件。工具还必须属于已知日志工具，且 `structured.selected_lines` 非空。JSON 日志中的 `message`、`event`、`path` 和带 `_mib`、`_bytes`、`_ms`、`_us` 等单位后缀的字段会被通用归一化；原始归档引用仍留在附录数据中。

## AI 叙述的事实约束

模型生成的事实段落使用隐藏引用：

```markdown
容器状态为 **CrashLoopBackOff**。 <!-- facts:fact-123456789abc -->
```

渲染器只保留满足以下条件的段落，并在展示前删除注释：

1. 引用的 Fact ID 全部存在。
2. 普通观察段只能引用本轮已验证事实。
3. 因果链和根因段只能引用 `claim_validation.valid_supporting_fact_ids`。
4. 文中的精确数字、单位、哈希和代码字面量能在所引用事实中找到。

不满足条件的 AI 叙述会被丢弃，并由通用、可读的确定性描述兜底。Logging 和 Tracing 等背景信号可以解释现场，但不会自动升级为根因证据。

## 扩展新的 Pod 场景

新增场景时扩展事实和来源合同，不新增 `if OOMKilled`、`if ImagePullBackOff` 一类报告分支。

推荐顺序：

1. 数据源发布标准 `FactRecord`，设置 dimension、fact_type、attribute、value、source_system 和 evidence_refs。
2. 优先复用通用 value 字段，例如 `message`、`reason`、`status`、`request_type`、`request_resource`、`response_code`、`duration_us`、`trace_id`。
3. 新字段确有跨场景价值时，在 `report_presentation.py` 增加字段级归一化，并用至少两个无关异常场景验证。
4. coverage 只表达数据源能力；不得用空 coverage 覆盖同维度的真实信号。
5. 因果结论仍通过 claim validation 和实体范围校验，不由展示代码猜测。

这种扩展方式同样适用于配置错误、镜像拉取失败、调度失败、探针失败、运行时崩溃和后续新增的 Pod 异常。

## 修复安全合同

报告展示能力不改变修复授权。没有 typed remediation policy 时始终输出：

```json
{
  "fix_type": "manual_only",
  "requires_human_approval": true,
  "actions": []
}
```

来源证据中的容量值可以显示，但不会因此变成推荐资源目标，也不会授权 Kubernetes 写操作。

## 回归验证

本地回放 `tests/fixtures/observability/a006_human_report_replay.json` 覆盖 ES 空结果、Kubernetes previous logs 和 DeepFlow flow 共存的情况。它不依赖历史 agent-loop 目录、集群、MCP 或 LLM。

```bash
pytest -q \
  tests/unit/workflow/test_report_presentation.py \
  tests/unit/workflow/test_fast_paths.py::test_a006_replay_shows_previous_logs_and_deepflow_in_human_body \
  tests/unit/workflow/test_ask_conclusion_remediation_json.py \
  tests/unit/remediation/test_plans.py
```
