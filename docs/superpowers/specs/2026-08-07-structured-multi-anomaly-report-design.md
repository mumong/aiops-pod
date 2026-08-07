# 结构化多异常诊断与可观测性报告设计

## 目标

多异常工作流继续保持 `Layer -> parallel_evidence -> Conclusion`，但不再把自由文本分析截断后作为组间交接协议。每个异常实体必须生成结构化诊断摘要，并由代码确定性聚合 Kubernetes、Metrics、Logging、Tracing 的真实查询结果。Conclusion 的模型只负责根据结构化摘要整理现象、结论、关键逻辑和修复建议。

设计同时解决以下问题：

1. `llm_analysis` 被移出 handoff 后，并发节点回退读取 500 字 `ai_message.content`，导致 c09/c10 决定性事实丢失。
2. 同一维度多次查询时，读者会看到后续窄查询的 `empty`，却难以发现先前已经命中的 `present` 事实。
3. 多异常报告按工具调用堆叠，Kubernetes 输出占据正文，Metrics、Logging、Tracing 缺少按异常实体组织的可读视图。

## 事实边界

- c01-c05 属于控制面/启动前异常，容器没有运行，因此应用 Logging、DeepFlow flow 和 Tempo span 物理上不存在。报告必须显示这些维度，但状态应为 `not_applicable`、`empty` 或 `absent`，并解释原因，不能伪造 `present`。
- c06-c11 属于运行态异常，实验 Case 会产生 Metrics、Logging、DeepFlow 和 Tempo。任一维度未命中时必须显示查询缺口、查询范围和限制原因，不能隐藏。
- `present` 只表示命中真实事实，不自动表示该事实支持根因。根因判断必须引用事实 ID 或 evidence reference。
- Kubernetes 与 Elasticsearch 中可能包含相同日志内容，但来源维度必须分别保留，不能因文本相同而去重为一个来源。

## 方案选择

### 方案一：扩大文本摘要

把 500/1600 字符上限调大，并把 `full_content` 传给 Conclusion。实现快，但仍依赖文本顺序，无法证明每个实体和每个维度均被覆盖。

### 方案二：只改报告渲染器

Conclusion 根据 `thinking_events` 临时按维度分组。能改善展示，但单组根因摘要仍是自由文本，c09/c10 的因果信息仍可能在组间 handoff 时丢失。

### 采用方案：端到端结构化契约

Evidence 产生结构化实体诊断摘要；ParallelEvidence 聚合事实与维度；Conclusion 读取结构化摘要写叙述，并由代码渲染每组观测矩阵。这条路径不依赖字符串截断，是唯一能确定性验证实体覆盖和维度覆盖的方案。

## 数据契约

### `EntityDiagnosisSummary`

每个 `group.entities` 项必须对应一条记录：

```json
{
  "entity_id": "k8s.pod:aiops-case-09/workload-xxx:<uid>",
  "namespace": "aiops-case-09",
  "name": "workload-xxx",
  "status": "Running / Ready=False",
  "phenomenon": "readiness probe HTTP 503",
  "root_cause": "dependency unavailable",
  "causal_chain": [
    "dependency unavailable",
    "GET /work -> HTTP 503",
    "readiness probe failed",
    "Ready=False"
  ],
  "confidence": 0.96,
  "supporting_fact_ids": ["fact-..."],
  "contradicting_fact_ids": [],
  "unknowns": []
}
```

模型可以提出 `phenomenon/root_cause/causal_chain`，但 `supporting_fact_ids` 必须来自当前组事实账本。代码校验实体覆盖和事实引用；无有效事实时根因必须为“证据不足”，不能猜测。

### `DimensionEvidenceSummary`

每个实体固定包含以下维度：

- `kubernetes`
- `metrics`
- `logging`
- `tracing`

可选保留 `topology`，但不计入用户要求的可观测性三维度。

每个维度字段：

```json
{
  "dimension": "tracing",
  "status": "present",
  "source_systems": ["deepflow", "tempo"],
  "query_count": 2,
  "present_query_count": 1,
  "empty_query_count": 1,
  "facts": [
    {
      "fact_id": "fact-...",
      "source_system": "deepflow",
      "value": "GET /work -> 503, trace_id=...",
      "evidence_refs": ["deepflow-..."]
    }
  ],
  "limitations": ["后续 trace_id 窄查询未命中，但不覆盖首轮已命中事实"]
}
```

聚合状态优先级：

1. 任一合法查询包含 source-backed facts：`present`。
2. 无 `present`，但存在 `weak/partial`：`weak`。
3. 所有成功查询都没有 facts：根据工具契约保留 `empty/absent`。
4. 实体没有运行容器或 Pod IP，且该维度物理上不能产生：`not_applicable`。
5. 所有查询失败：`error`。

后续 `empty` 不得覆盖先前 `present`。所有独立查询仍保留在归档，主报告只展示聚合状态、代表性事实和限制说明。

### `GroupDiagnosisResult`

`group_results` 中每组包含：

- `group_id`
- `entities`
- `entity_summaries`
- `dimension_evidence_by_entity`
- `collection_summary`
- `completeness`
- `archive_run_id`
- `error`

旧 `summary` 字段仅作为兼容回退，不再作为 Conclusion 的权威输入。

## 数据流

1. 每组 EvidenceCollector 继续独立采集并落盘。
2. EvidenceCollector 输出完整事实账本、结构化工具结果和独立的结构化实体诊断摘要。普通 `evidence_analysis` 仍保持紧凑，避免影响 `<=2` 的原 RCA 链路。
3. ParallelEvidence 对当前组的 `tool_result.structured` 做确定性维度聚合，并校验每个输入实体都存在摘要和四维状态。
4. Conclusion 向模型只传 `entity_summaries` 和紧凑维度摘要，模型生成叙述部分。
5. 代码在叙述后渲染每个异常组的四维观测矩阵和代表性真实事实。
6. 原始逐工具调用放入折叠附录，并链接 `{run_id}-{group_id}` 完整归档。

## 报告格式

```markdown
## 异常组 g7 · aiops-case-09/workload-xxx

**状态**：Running / Ready=False

**根因**：dependency unavailable

**关键逻辑**：dependency unavailable -> HTTP 503 -> readiness probe failed -> Ready=False

| 维度 | 状态 | 真实结果 | 作用 |
|---|---|---|---|
| Kubernetes | present | Ready=False；Unhealthy；readiness HTTP 503 | 确认直接现象 |
| Metrics | present | kube_pod_container_status_ready=0 | 量化当前状态 |
| Logging | present | `dependency unavailable`, http_status=503 | 确认应用返回原因 |
| Tracing | present | GET /work -> 503, trace_id=... | 串联请求失败 |

**采集边界**：后续关键词窄查询 0 命中，但首轮 UID 查询已有真实日志，不影响 Logging=present。
```

控制面 Case 的空维度示例：

```markdown
| Logging | not_applicable | 容器未启动，无应用日志 | 符合 Pending 异常边界 |
| Tracing | not_applicable | Pod 无运行进程/业务流量 | 符合启动前异常边界 |
```

## 错误处理

- 单组失败不影响其他组，失败组仍输出实体、四维状态和归档引用。
- 结构化诊断解析失败时，从事实账本确定性生成“已确认事实/证据不足”摘要，不回退到 500 字 `content`。
- 为兼容旧归档，允许最后回退到 `full_content`，然后才是 `content`；兼容路径必须标注 `legacy_text_fallback=true`。
- Conclusion 模型漏掉实体时，代码补充该实体的确定性摘要；不得静默遗漏。

## 测试与验收

单元测试必须覆盖：

1. `content` 只有 500 字但 `full_content` 含 c09 决定性事实时，结构化摘要不丢事实。
2. 同一维度先 `present` 后 `empty`，聚合结果仍为 `present`，且记录补查为空。
3. 每组每个实体均有 Kubernetes、Metrics、Logging、Tracing 四维条目。
4. 控制面 Case 没有日志/Trace 时输出 `not_applicable/empty`，不得伪造事实。
5. 运行态 Case 三维缺失时报告明确显示缺口。
6. 多实体组不能把一个实体的退出码、OOM 或探针结论套给另一个实体。
7. N=10 所有实体都出现在叙述、观测矩阵和归档引用中。
8. 普通 `<=2` 链路继续排除大段 `llm_analysis`，原行为不回归。

真实验收使用运行态 Case 至少覆盖 c06、c09、c10：

- c06：Logging 和 Tracing 显示 `/work -> 500`，不能推断未证实的缺失配置。
- c09：显示 `dependency unavailable -> 503 -> Ready=False`。
- c10：显示 liveness HTTP 500 和重启，不能因 exit 137 推断 OOMKilled。

完成标准是报告主正文无需翻阅原始逐工具附录，即可看清每个异常实体的现象、根因、因果链和可观测性三维真实结果；附录和归档仍能完整追溯全部查询。
