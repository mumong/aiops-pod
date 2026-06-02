# Contract: AIOps Observability Case Dataset

## 目标

定义未来 AIOps agent 如何消费可观测性异常 case 数据集，以及评测程序如何使用 ground truth。当前阶段只定义合同，不修改现有 agent 逻辑。

## 目录合同

一个合法 case MUST 至少包含：

```text
case.yaml
labels.yaml
time_window.yaml 或 case.yaml.time_window
topology.yaml
metrics/prometheus_queries.yaml
logs/elasticsearch_queries.yaml
traces/deepflow_queries.yaml
k8s/
expected/root_cause.json 或 labels.yaml.root_cause
expected/remediation.json
evaluation/rubric.yaml
```

允许大体量结果文件按需缺失，但必须在 `case.yaml.observability_coverage` 中声明缺失原因和证据强度。

严格计数规则：

- Metrics 只有在 Prometheus 返回真实非空 result 时，才能计为该 case 的 metrics 数据。
- Logs 只有在 Elasticsearch/Filebeat 返回真实 log hit 时，才能计为该 case 的 logging 数据。
- Tracing 只有在 DeepFlow 返回真实 flow、trace、span 或 L7 request row 时，才能计为该 case 的 tracing 数据。
- 查询成功但返回 0 条，只能作为 absent/negative query 记录，不能计入三维完整数据集。

## 诊断输入边界

Agent 诊断时 MAY 读取：

- `case.yaml`
- `time_window.yaml`
- `topology.yaml`
- `metrics/**`
- `logs/**`
- `traces/**`
- `k8s/**`

Agent 诊断时 MUST NOT 读取：

- `labels.yaml`
- `expected/**`
- `evaluation/**`

除非运行模式明确是 scorer/evaluator，而不是 diagnosis。

## Case Metadata Contract

```yaml
case_id: string
title: string
abnormal_type: string
category: string
severity: low | medium | high | critical
question_templates: [string]
time_window:
  fault_start: timestamp
  fault_end: timestamp | null
  collection_start: timestamp
  collection_end: timestamp
  timezone: string
primary_entity:
  type: Pod | Node | Service | Workload | PVC | Other
  namespace: string | null
  name: string
related_entities:
  - type: string
    namespace: string | null
    name: string
observability_coverage:
  metrics:
    source: prometheus
    strength: strong | weak | absent | not_applicable
    note: string
  logs:
    source: elasticsearch_filebeat
    strength: strong | weak | absent | not_applicable
    note: string
  tracing:
    source: deepflow
    strength: strong | weak | absent | not_applicable
    note: string
```

## Evidence Result Contract

### Metrics

Prometheus result JSONL SHOULD use:

```json
{
  "query_id": "string",
  "ts": "timestamp",
  "metric": {},
  "value": 0,
  "labels": {},
  "entity_ref": {
    "namespace": "string",
    "pod": "string",
    "node": "string"
  }
}
```

### Logs

Log JSONL SHOULD use:

```json
{
  "ts": "timestamp",
  "source": "elasticsearch_filebeat",
  "namespace": "string",
  "pod": "string",
  "container": "string",
  "node": "string",
  "level": "string",
  "message": "string",
  "fields": {}
}
```

### DeepFlow

DeepFlow flow JSONL SHOULD use:

```json
{
  "ts": "timestamp",
  "source": "deepflow",
  "flow_id": "string",
  "trace_id": "string",
  "span_id": "string",
  "namespace": "string",
  "pod": "string",
  "pod_ip": "string",
  "service": "string",
  "node": "string",
  "protocol": "TCP|HTTP|DNS|Other",
  "request_count": 0,
  "error_count": 0,
  "latency_ms": 0,
  "signal": "string",
  "raw": {}
}
```

如果 DeepFlow 当前只有 flow 或 dashboard panel 数据，没有 span，`trace_id` 和 `span_id` MAY 为空，但 `signal` MUST 说明证据含义。

## Evaluation Contract

评测程序 MUST 至少支持以下维度：

- root cause accuracy
- evidence completeness
- observability correlation
- runbook alignment
- remediation safety
- negative evidence handling

评测程序 MUST 能识别以下失败：

- 把历史证据当成当前根因
- 忽略关键 K8s 当前状态
- metrics/logs/traces 任一数据源缺失却声称完整
- finalizer stuck case 中优先推荐 force delete，且没有 preconditions
- DeepFlow 只有弱信号时夸大为直接根因证据

## Versioning

Dataset schema 使用语义版本：

- MAJOR: 破坏旧 case 消费合同
- MINOR: 新增可选字段或新证据类型
- PATCH: 文档、示例或非破坏性说明修正
