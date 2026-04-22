# 质量指标与 Runbook 统计口径

本文只保留当前仍在使用的统计口径。

## 1. 当前会展示什么

最终报告末尾通常会包含两类信息：

- **性能统计**
- **诊断追踪**

当 `metrics.enabled: true` 时，还会额外展示质量指标。

## 2. 性能统计

默认会展示：

- 总耗时
- 各节点耗时
- LLM 调用次数
- 工具调用次数

来源：

- [app/core/workflow/metrics.py](/root/huhu/agent/combine-aiops-mcp/robusta/app/core/workflow/metrics.py)
- [app/core/workflow/executor.py](/root/huhu/agent/combine-aiops-mcp/robusta/app/core/workflow/executor.py)

## 3. 诊断追踪

默认会展示：

- 核心 Runbook
- 参考 Runbook
- 工具调用
- LLM 调用

格式来自：

- [app/core/workflow/metrics.py](/root/huhu/agent/combine-aiops-mcp/robusta/app/core/workflow/metrics.py)

## 4. 核心 Runbook 与参考 Runbook 的判定

判定逻辑在：

- [app/core/workflow/reporter.py](/root/huhu/agent/combine-aiops-mcp/robusta/app/core/workflow/reporter.py)

### 4.1 先收集“实际使用过哪些 runbook”

系统会从这些位置收集 runbook 痕迹：

1. `thinking_events` 里的 `fetch_runbook`
2. `conclusion`、`rca_analysis`、`evidence_analysis` 中的 `.md`
3. `tool_call_details`

然后做 catalog 归一化，只保留真实存在的 runbook id。

### 4.2 核心 Runbook

`核心 Runbook` 只认 AI 明确声明的核心 runbook：

优先级：

1. `state["primary_runbook_id"]`
2. `rca_analysis.primary_runbooks`
3. 如果 AI 没声明，但全局只识别到 1 个合法 runbook，则回退把这 1 个当核心

注意：

- 核心 runbook 可以是 1 个，也可以是多个
- 如果 RCA 输出了多个 `primary_runbooks`，最终报告里核心 runbook 也会是多个

### 4.3 参考 Runbook

`参考 Runbook` 是所有实际使用过、且能归一化到 catalog 的 runbook。

展示顺序：

1. 先放核心 runbook
2. 再补其他参考 runbook

所以会出现两种常见情况：

- 只有参考，没有核心
- 核心和参考完全一样

这两种都属于当前正常行为。

## 5. Runbook 匹配标记

只要最终能识别出合法 runbook，`runbook_matched=true`。

这会影响：

- 诊断追踪展示
- Runbook 质量得分

## 6. 证据完整率

来源于 `evidence` 节点：

- 计划多少项
- 实际采集多少项

最终表现为：

- `collection_summary`
- `evidence_completeness`

## 7. E2E 测试中的 Runbook 命中口径

当前 `test/e2e/test_accuracy.py` 的口径已经更新为：

- 只要 **核心 Runbook** 命中，算成功
- 只要 **参考 Runbook** 命中，算成功
- 只要从执行日志里提取出的 runbook id 命中，也算成功

也就是说：

- 不再要求必须有核心 runbook
- 只有参考 runbook 也可以判定为命中

对应实现：

- [test/e2e/test_accuracy.py](/root/huhu/agent/combine-aiops-mcp/robusta/test/e2e/test_accuracy.py)

## 8. 当前建议

如果你在看报告时发现：

- `核心 Runbook` 和 `参考 Runbook` 一样
- `核心 Runbook` 有多个
- 只有 `参考 Runbook`

优先按当前 reporter 口径理解，不要再按旧文档里“核心只能有一个”的思路看。
