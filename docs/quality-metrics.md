# 质量指标与统计口径

本文只描述当前代码真实实现，不描述理想设计。涉及的核心实现文件：

- [metrics.py](/root/huhu/agent/combine-aiops-mcp/robusta/app/core/workflow/metrics.py)
- [reporter.py](/root/huhu/agent/combine-aiops-mcp/robusta/app/core/workflow/reporter.py)
- [quality_scorer.py](/root/huhu/agent/combine-aiops-mcp/robusta/app/core/workflow/quality_scorer.py)
- [evidence_collector.py](/root/huhu/agent/combine-aiops-mcp/robusta/app/core/workflow/nodes/evidence_collector.py)


## 1. 报告里有哪些指标

最终报告末尾通常有两部分：

- **性能统计**：默认展示。
- **诊断追踪**：默认展示。

当 `metrics.enabled: true` 时，还会额外展示：

- **MTTR**
- **根因置信度**
- **证据完整率**
- **Runbook 覆盖率**
- 置信度评分明细
- 证据完整率明细
- 证据采集清单
- Runbook 覆盖率明细

配置入口在 [deploy/configmap/config.yaml](/root/huhu/agent/combine-aiops-mcp/robusta/deploy/configmap/config.yaml) 的 `metrics` 段。环境变量优先级高于 config。


## 2. 性能统计

性能统计由 `WorkflowMetrics` 记录。

### 2.1 总耗时

字段：

```python
total_duration_ms = (end_time - start_time) * 1000
total_duration_seconds = total_duration_ms / 1000
```

如果工作流尚未调用 `finish()`，则使用 `time.time() - start_time` 动态计算。

### 2.2 节点耗时

每个节点通过 `start_node()` 和 `finish_node()` 记录：

```python
node.duration_ms = (node.end_time - node.start_time) * 1000
```

报告中的节点百分比是：

```python
node_pct = node.duration_ms / total_duration_ms
```

因此节点百分比用于观察耗时分布，不是质量得分。

### 2.3 LLM 调用次数

每次节点通过 `_call_llm()` 或 `call_simple()` 成功记录 LLM 调用时：

```python
metrics.total_llm_calls += 1
metrics.total_llm_duration_ms += duration_ms
```

注意：如果某些调用没有走 metrics 记录路径，`reporter.update_metrics_from_state()` 只会在 `state["llm_calls"]` 存在时做补充。

### 2.4 工具调用次数

工具调用通过：

```python
metrics.record_tool_call(tool_name, duration_ms, success)
```

记录到：

- `metrics.total_tool_calls`
- `metrics.total_tool_duration_ms`
- `metrics.tool_call_details`

当前 AICall 工具调用主要来自 LLM agent loop。部分节点可能用 `thinking_events` 记录工具详情，但 metrics 中的工具耗时可能显示为 0，因为 MCP 工具的精确 duration 并不总是传入 metrics。


## 3. MTTR

当前 MTTR 不是传统生产事故意义上的“从故障发生到恢复”的时间，而是**本次工作流从接收问题到输出报告的端到端耗时**。

实现：

```python
mttr_seconds = total_duration_seconds
```

达标判断：

```python
mttr_pass = mttr_seconds < MTTR_THRESHOLD_SECONDS
```

默认阈值：

```text
METRICS_MTTR_THRESHOLD=600
```

也就是 10 分钟。config 中对应：

```yaml
metrics:
  thresholds:
    mttr_seconds: 600
```

结论：当前 MTTR 适合衡量“诊断响应速度”，不适合衡量“故障修复耗时”。


## 4. Evidence Plan 与 Evidence Items

证据完整率的基础是 `evidence_items`，它由 evidence 节点从 `thinking_events` 构建。

### 4.1 Evidence Plan 从哪里来

evidence 节点提示词要求 LLM 输出 `evidence_plan` JSON，但代码不会假设它一定存在。

解析流程：

1. 遍历 `thinking_events` 中所有 `ai_message`。
2. 优先读取 `full_content`，否则读取 `content`。
3. 只有文本里包含 `evidence_plan` 时才尝试解析。
4. 如果 `thinking_events` 没解析到，再尝试从最终 `response.result` 解析。
5. 都失败则 `evidence_plan=[]`。

对应实现：

- `_extract_plan_from_thinking()`
- `_parse_llm_evidence_plan()`

### 4.2 为什么 prompt 要求了 plan，但仍可能没有 plan

这是当前本地模型 agent loop 的真实风险：prompt 只是约束，模型可能不遵守。

常见情况：

- 模型先输出 `<think>`，然后直接调用工具，没有输出 JSON plan。
- 模型在多轮工具调用后输出自然语言总结，而不是可解析 JSON。
- 模型输出了计划，但字段名、代码块、JSON 格式不满足解析器要求。
- 模型把“计划”写在不可稳定解析的推理文本里。
- 上下文较长、工具 schema 较多时，小模型更容易丢失结构化输出要求。

因此，当前实现有“无 plan 模式”兜底。


## 5. 无 Plan 模式下证据如何计算

如果 `evidence_plan=[]` 且存在成功工具调用，代码会从成功 `tool_result` 反向构造证据项。

逻辑：

```python
successful_tools = [
  ev for ev in thinking_events
  if ev.type == "tool_result" and ev.status == "success"
]
```

过滤非证据工具：

```python
_NON_EVIDENCE_TOOLS = {"todowrite", "todo_write", "todo"}
```

然后每个成功工具调用生成一个证据项：

```python
EvidenceItem(
  id=f"auto_{i}",
  description=f"工具采集: {tool_name}",
  level=IMPORTANT,
  weight=0.2,
  collected=True,
  value=tool_result[:500],
  source="thinking_auto",
)
```

所以无 plan 模式下：

- 每个成功工具调用都会变成一条已采集证据。
- 所有自动证据的 `level` 都是 `IMPORTANT`。
- 所有自动证据的 `collected` 都是 `True`。
- 工具返回内容是否真正满足某个诊断目的，目前不会在这个阶段严格判定。

### 5.1 无 Plan 模式完整率是否真实

它是真实反映了“成功工具调用数量”，但不严格等于“原计划证据覆盖率”。

例如 evidence 调用了 15 个工具，全部成功返回摘要：

```text
计划 15 项，实际采集 15 项，完整度 100%
```

这个“计划 15 项”其实是由 15 个成功工具调用反向构造出来的自动证据项，不是 LLM 事先规划的 15 项 evidence_plan。

因此，无 plan 模式下证据完整率偏乐观。它可以说明“模型确实调用了工具并拿到了结果”，但不能充分说明“关键证据都按预期验证完成”。


## 6. 有 Plan 模式下证据如何计算

如果解析到了 `evidence_plan`，代码会按 plan item 匹配成功工具调用。

每个 plan item 会生成一个 `EvidenceItem`：

```python
EvidenceItem(
  id=plan_item["id"],
  description=plan_item["description"],
  level=critical/important/optional,
  weight=0.2,
  collected=matched,
  value=matched_result,
  source="thinking_match" if matched else "planned",
)
```

匹配规则是工具名和 plan 中的 `tool` / `command` 做宽松匹配：

- `plan_tool == actual_tool_name`
- `plan_tool in actual_tool_name`
- `actual_tool_name in plan_tool`
- `actual_tool_name in plan_command`
- `plan_tool.replace("_", "") == actual_tool_name.replace("_", "")`

未匹配到任何成功工具调用的 plan item：

```python
collected=False
source="planned"
```

成功调用了但没有匹配任何 plan item 的工具，会作为额外证据：

```python
EvidenceItem(
  id=f"extra_{tool_index}",
  description=f"工具采集: {tool_name}",
  level=IMPORTANT,
  weight=0.15,
  collected=True,
  source="thinking_extra",
)
```

### 6.1 有 Plan 模式完整率

普通完整率由 evidence 节点计算：

```python
completeness = collected_count / len(evidence_items)
```

其中：

```python
evidence_items = planned_items + extra_items
```

这意味着额外工具调用也会进入分母和分子。当前普通完整率不是“只按原始 plan 分母计算”。


## 7. 报告中的证据完整率

报告中展示的 `证据完整率` 来自 `WorkflowMetrics.evidence_completeness`。

reporter 会先从最终 state 读取：

```python
evidence_items = state["evidence_items"]
metrics.evidence_planned = len(evidence_items)
metrics.evidence_collected = count(item.collected)
```

然后 `WorkflowMetrics.evidence_completeness`：

```python
if evidence_planned == 0:
    return 0.0
return evidence_collected / evidence_planned
```

达标判断：

```python
evidence_completeness > EVIDENCE_COMPLETENESS_THRESHOLD
```

默认阈值：

```text
METRICS_EVIDENCE_THRESHOLD=0.9
```

config 中对应：

```yaml
metrics:
  thresholds:
    evidence_completeness: 0.9
```

### 7.1 evidence_analysis 里的 collection_summary

evidence 节点也会把类似文本写入 `evidence_analysis`：

```text
计划 {total} 项，实际采集 {collected} 项，未采集 {total - collected} 项，完整度 {completeness}
```

这里的 `total` 也是 `len(evidence_items)`。

因此：

- 有 plan 时，`total = plan item + extra tool item`。
- 无 plan 时，`total = successful tool result item`。


## 8. 加权证据完整率

除了报告表格里的普通完整率，`QualityScorer` 还会计算加权证据完整率，用于根因置信度里的 `evidence_strength` 维度。

默认权重：

```python
CRITICAL = 1.0
IMPORTANT = 0.6
SUPPLEMENTARY = 0.3
```

公式：

```python
weighted_completeness = sum(collected_item_level_weight) / sum(all_item_level_weight)
```

无 plan 模式下自动证据全部是 `IMPORTANT` 且 `collected=True`，所以加权完整率通常也是 100%。

注意：当前加权完整率只是用于根因置信度评分明细，不是报告表格中 `证据完整率` 的主值。


## 9. 根因置信度

根因置信度由 `QualityScorer.score_confidence()` 计算，不是直接等于 LLM 输出的 confidence。

默认维度：

| 维度 | 默认权重 | 计算来源 |
|------|----------|----------|
| evidence_strength | 35% | 加权证据完整率 |
| causal_chain | 25% | 结构化因果链或报告/RCA 文本中的因果链特征 |
| tool_coverage | 15% | 工具成功率或工具调用存在性 |
| runbook_match | 15% | Runbook 是否匹配、是否有核心 Runbook |
| llm_self_score | 10% | deterministic decision、RCA JSON、文本正则、layer confidence 或兜底 |

加权总分：

```python
weighted_total = sum(weight_i * score_i) / sum(weight_i)
```

当前惩罚项已禁用。

### 9.1 evidence_strength

使用第 8 节的加权证据完整率。

### 9.2 causal_chain

优先看 `state["causal_chain"]`：

```python
if len(causal_chain) == 1:
    score = 0.5
elif len(causal_chain) > 1:
    score = min(1.0, 0.3 + len(causal_chain) * 0.2)
```

如果结构化因果链不足，再从 `conclusion + rca_analysis` 文本里找关键词：

- `因果链`
- `根本原因`
- `传导机制`
- `直接原因`
- `causal`
- `root cause`
- `→`
- `┌─`
- `└─`

命中规则：

```python
matches >= 3 -> 1.0
matches >= 1 -> 0.7
```

如果已有 collected evidence 且 chain score > 0：

```python
score += 0.1
```

上限为 1.0。

### 9.3 tool_coverage

如果 `state["tool_results"]` 有内容：

```python
ratio = successful_tool_results / total_tool_results
tool_coverage = 0.5 + ratio * 0.5
```

如果 `tool_results` 为空，但 metrics 记录了工具调用：

```python
tool_coverage = 0.85
```

如果完全没有工具调用：

```python
tool_coverage = 0.3
```

### 9.4 runbook_match

用于根因置信度维度时：

```python
if primary_runbook:
    runbook_score = 1.0
elif runbook_matched:
    runbook_score = 0.8
else:
    runbook_score = 0.3
```

这里的 `runbook_score` 是根因置信度的一个维度，不等于 Runbook 覆盖率。

### 9.5 llm_self_score

优先级：

1. `deterministic_decision.confidence_score`
2. `rca_analysis` JSON 中的 `confidence`
3. `conclusion/evidence/rca` 文本正则提取置信度百分比
4. `state["layer_confidence"]`
5. 兜底 0.5

### 9.6 最终置信度保底

计算完 `weighted_total` 后，还有保底逻辑：

```python
if has_conclusion and (has_evidence or has_tool_calls):
    final_score = max(0.80, weighted_total)
elif has_conclusion and has_root_cause:
    final_score = max(0.75, weighted_total)
```

所以日志里可能出现：

```text
置信度评分: 80% (加权 42%, fallback=False)
```

含义是：加权分只有 42%，但因为有结论且有证据/工具调用，被保底抬到 80%。

达标判断：

```python
root_cause_confidence >= ROOT_CAUSE_CONFIDENCE_THRESHOLD
```

默认阈值为 0.8。


## 10. Runbook 识别与覆盖率

Runbook 统计由 `reporter.update_metrics_from_state()` 完成。

### 10.1 Runbook 痕迹来源

系统会从以下位置收集 runbook：

1. `conclusion_formatted` / `conclusion`
2. `rca_analysis`
3. `evidence_analysis`
4. `thinking_events` 中成功的 `fetch_runbook` 工具结果
5. `metrics.tool_call_details` 中 runbook 相关工具结果

然后使用 runbook catalog 做归一化，只保留 catalog 中可识别的 runbook id。

### 10.2 核心 Runbook

核心 Runbook 只认 AI 明确声明或唯一合法回退：

优先级：

1. `state["primary_runbook_id"]`
2. `rca_analysis.primary_runbooks`
3. `rca_analysis.llm_raw_analysis` 中 `found a runbook named **...**`
4. 如果没有核心，但合法参考 runbook 只有 1 个，则将该 runbook 回退为核心

不会用关键词猜测多个核心 runbook。

### 10.3 参考 Runbook

参考 Runbook 是所有实际使用过、且能归一化到 catalog 的 runbook。

展示顺序：

1. 先放核心 Runbook。
2. 再补其他参考 Runbook。

非 QUERY 模式下会过滤 QUERY 参考手册。

### 10.4 Runbook 覆盖率

Runbook 覆盖率和根因置信度里的 `runbook_match` 不是同一个指标。

覆盖率由三项组成：

| 维度 | 权重 | 分数 |
|------|------|------|
| Runbook 引用 | 50% | 有任意合法 runbook = 1，否则 0 |
| 核心 Runbook 识别 | 30% | 有核心 = 1；只有参考 = 0.3；都没有 = 0 |
| Runbook 结论关联 | 20% | 核心关键词在 conclusion 中命中比例；只有参考且有 conclusion = 0.3 |

公式：

```python
runbook_coverage_score = 0.5 * ref_score + 0.3 * primary_score + 0.2 * conclusion_score
```

保底：

```python
if runbook_matched:
    runbook_coverage_score = max(0.85, runbook_coverage_score)
```

上限：

```python
runbook_coverage_score = min(1.0, runbook_coverage_score)
```

达标判断：

```python
runbook_coverage_score >= 0.80
```


## 11. 定位分层指标

当前没有单独的“定位分层准确率”指标。

和分层相关的字段包括：

- `state["layer"]`
- `state["layers"]`
- `state["layer_confidence"]`
- `state["layer_reasoning"]`

它们的用途：

- 控制工作流路由，例如 `HEALTHY` 或 `/query` direct 直接到 conclusion。
- 在报告中展示问题层级。
- 作为 `llm_self_score` 的最后回退来源。

因此，当前报告中的“根因置信度”并不是“分层准确率”。如果需要严格衡量分层准确率，应在 E2E 标注集里用 expected layer 与实际 `state["layer"]` 做单独统计。


## 12. 工具重复调用对指标的影响

当前工具重复调用会影响三个地方：

### 12.1 性能统计

重复工具调用会增加：

- 总耗时
- evidence 节点耗时
- 工具调用次数
- LLM agent loop 轮次

### 12.2 无 Plan 模式证据完整率

无 plan 模式下，每个成功工具调用都会反向构造成 collected evidence。

因此重复调用可能导致：

```text
证据项数量增加，但完整率仍然是 100%
```

这会让证据完整率偏乐观。

### 12.3 根因置信度

只要有 evidence 或 tool calls，根因置信度可能触发 80% 保底。重复工具调用不一定提高加权分，但会强化 `has_tool_calls=True` 这个条件。


## 13. 当前指标的可信边界

### 13.1 可信的部分

- MTTR 能真实反映本次工作流端到端耗时。
- 性能统计能定位哪个节点慢。
- Runbook 是否被实际引用基本可信。
- 核心 Runbook 是否由 AI 明确声明基本可信。
- context archive 能保留 raw/summary，便于人工复盘。

### 13.2 需要谨慎理解的部分

- 无 plan 模式下证据完整率偏向“工具调用完成率”，不是严格“证据覆盖率”。
- `tool_result.status=success` 当前表示工具调用链路成功，不等于工具输出语义有效。例如 `Command failed` 文本如果被包装为成功 observation，仍可能被当作成功工具结果。
- `kubectl_get_yaml` 的 structured artifact 当前只记录摘要状态和行数，尚不能用于强语义验证。
- 根因置信度有保底逻辑，不是纯加权模型输出。
- 当前没有独立的分层准确率指标。


## 14. 建议的后续修正方向

这些不是当前实现，但建议优先处理：

1. evidence 如果没有解析到 plan，应在报告中明确标记 `plan_mode=auto_from_tools`，不要继续显示成普通“计划 N 项”。
2. 无 plan 模式完整率建议改名为“工具采集完成率”，避免和计划覆盖率混淆。
3. 工具重复调用应做同工具同参数去重，重复 observation 不应重复计入 evidence_items。
4. `ToolMessage` 中包含 `Command failed` / `NotFound` / `No events found` 时，应在 structured artifact 中标记为 negative/conflict，并避免直接计为 collected。
5. `kubectl_get_yaml` structured artifact 应提取 `imagePullSecrets`、`serviceAccountName`、`containerStatuses`、`events` 等高价值字段。
6. 增加独立的“分层准确率” E2E 指标，不要混入根因置信度。

