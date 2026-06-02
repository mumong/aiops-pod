# Data Model: 可观测性异常 Case 数据集

## Dataset

表示一个可观测性异常 case 集合。

严格数据原则：每个维度必须来自对应观测服务的真实原始记录。Prometheus 查询无 result、Elasticsearch 查询 total=0、DeepFlow 查询 count=0 都不能算该维度 present，只能记录为 absent 或 negative query。

```yaml
dataset_id: aiops-observability-cases
schema_version: 1.0.0
created_at: "2026-06-02T00:00:00+08:00"
description: Kubernetes 异常诊断与 AIOps agent 评测数据集
data_sources:
  metrics: prometheus
  logs: elasticsearch_filebeat
  tracing: deepflow
case_index:
  - cases/pod-terminating-finalizer-stuck-001/case.yaml
usage_boundary:
  diagnosis_inputs:
    - case.yaml
    - topology.yaml
    - metrics/**
    - logs/**
    - traces/**
    - k8s/**
  evaluation_only:
    - labels.yaml
    - expected/**
    - evaluation/**
```

## Case

表示一次异常事件。

```yaml
case_id: pod-terminating-finalizer-stuck-001
title: Pod TerminatingStuck due to finalizer
abnormal_type: TerminatingStuck
category: lifecycle
severity: high
question_templates:
  - "namespace=aiops-e2e pod=terminating-stuck 为什么一直 Terminating？"
  - "我的集群有什么问题？"
time_window:
  fault_start: "2026-06-02T10:00:00+08:00"
  fault_end: null
  collection_start: "2026-06-02T09:55:00+08:00"
  collection_end: "2026-06-02T10:15:00+08:00"
  timezone: Asia/Shanghai
primary_entity:
  type: Pod
  namespace: aiops-e2e
  name: terminating-stuck
related_entities:
  - type: Node
    name: node-1
  - type: Workload
    kind: Pod
    namespace: aiops-e2e
    name: terminating-stuck
observability_coverage:
  metrics:
    source: prometheus
    strength: weak
    note: Pod 生命周期卡住主要由 K8s 对象状态证明，metrics 可辅助观察容器/节点状态。
  logs:
    source: elasticsearch_filebeat
    strength: strong
    note: kubelet 或 Kubernetes event 日志可出现删除/finalizer/volume 相关信号。
  tracing:
    source: deepflow
    strength: weak
    note: DeepFlow 可观察业务流量影响或 Pod IP flow，未必直接证明 finalizer。
```

## Metrics Artifact

Prometheus 查询定义和结果。

```yaml
source: prometheus
queries:
  - id: pod_phase
    purpose: 确认 Pod phase/status 是否异常
    promql: 'kube_pod_status_phase{namespace="aiops-e2e",pod="terminating-stuck"}'
    expected_signal: deletionTimestamp 存在但 phase 指标可能仍停留在旧状态
  - id: node_ready
    purpose: 排除 Node NotReady 导致 kubelet 无法完成删除
    promql: 'kube_node_status_condition{condition="Ready",status="true"}'
  - id: container_cpu
    purpose: 观察删除前后容器是否仍有 CPU 活动
    promql: 'rate(container_cpu_usage_seconds_total{namespace="aiops-e2e",pod="terminating-stuck"}[5m])'
result_files:
  - prometheus_range.jsonl
```

`prometheus_range.jsonl` 推荐每行一条查询结果：

```json
{"query_id":"node_ready","ts":"2026-06-02T10:01:00+08:00","metric":{"node":"node-1"},"value":1}
```

## Logs Artifact

Elasticsearch/Filebeat 查询定义和日志结果。

```yaml
source: elasticsearch_filebeat
queries:
  - id: kubelet_delete_pod
    purpose: 查找 kubelet 删除 Pod、Killing、FailedKillPod、volume unmount 相关日志
    index: "filebeat-*"
    filter:
      namespace: aiops-e2e
      pod: terminating-stuck
      keywords:
        - finalizer
        - Killing
        - FailedKillPod
        - unmount
        - detach
  - id: kubernetes_events
    purpose: 查找 Kubernetes Event 中的删除和生命周期事件
    index: "filebeat-*"
    filter:
      involvedObject.name: terminating-stuck
```

`logs.jsonl` 推荐字段：

```json
{"ts":"2026-06-02T10:03:01+08:00","source":"filebeat","namespace":"aiops-e2e","pod":"terminating-stuck","node":"node-1","container":"main","level":"warning","message":"Killing container ...","raw_ref":"optional"}
```

## Traces Artifact

DeepFlow 查询定义、Grafana panel 来源和 flow/trace 结果。

```yaml
source: deepflow
query_origin:
  grafana_dashboard: observability-deepflow
  dashboard_uid: optional
queries:
  - id: pod_ip_l4_flow
    purpose: 观察 Pod 删除前后 Pod IP 的 L4 flow 是否中断或异常
    entity:
      namespace: aiops-e2e
      pod: terminating-stuck
      pod_ip: 10.x.x.x
    expected_signal: flow volume drops, TCP reset, timeout, no traffic, or no strong signal
  - id: service_l7_flow
    purpose: 如果 Pod 属于服务后端，观察相关服务 L7 请求是否失败
    entity:
      service: optional
evidence_strength: weak
```

`deepflow_flows.jsonl` 推荐字段：

```json
{"ts":"2026-06-02T10:04:00+08:00","flow_id":"optional","namespace":"aiops-e2e","pod":"terminating-stuck","pod_ip":"10.x.x.x","node":"node-1","protocol":"TCP","tap_side":"server","request_count":0,"error_count":0,"latency_ms":null,"signal":"no_strong_trace_signal"}
```

`deepflow_spans.jsonl` 如果 DeepFlow 提供调用链/Span，可使用：

```json
{"trace_id":"trace-1","span_id":"span-1","ts":"2026-06-02T10:04:00+08:00","service_name":"svc-a","namespace":"aiops-e2e","pod":"terminating-stuck","operation":"GET /api","duration_ms":123,"status":"error"}
```

## Kubernetes Artifact

保存采集时的对象快照。

```text
k8s/
  pod.yaml
  describe.txt
  events.jsonl
  node.yaml
  owner.yaml
```

`events.jsonl` 推荐字段：

```json
{"ts":"2026-06-02T10:02:00+08:00","type":"Normal","reason":"Killing","object_kind":"Pod","namespace":"aiops-e2e","name":"terminating-stuck","message":"Stopping container"}
```

## Ground Truth

`labels.yaml`:

```yaml
root_cause:
  category: lifecycle
  abnormal_type: TerminatingStuck
  branch: finalizer_stuck
  entity:
    type: Pod
    namespace: aiops-e2e
    name: terminating-stuck
confidence: confirmed
key_evidence:
  - deletionTimestamp exists for longer than expected grace period
  - metadata.finalizers is non-empty
negative_evidence:
  - node is Ready
  - no volume detach/unmount failure confirmed
expected_runbook: pod-terminating-stuck.md
```

`expected/remediation.json`:

```json
{
  "preferred": [
    {
      "action": "patch_finalizers",
      "command_pattern": "kubectl patch pod <pod> -n <namespace> --type=merge -p '{\"metadata\":{\"finalizers\":null}}'",
      "preconditions": [
        "deletionTimestamp exists",
        "finalizers are confirmed non-empty",
        "owner/controller cleanup impact is understood"
      ],
      "risk": "medium"
    }
  ],
  "discouraged": [
    {
      "action": "force_delete_first",
      "reason": "Force deletion should not be the first recommendation when finalizer branch is confirmed and patch is sufficient."
    }
  ]
}
```

## Evaluation Rubric

```yaml
scores:
  root_cause_accuracy:
    weight: 0.35
    must_match:
      - abnormal_type
      - root_cause.branch
      - primary_entity
  evidence_completeness:
    weight: 0.25
    must_include:
      - deletionTimestamp
      - finalizers
      - node_ready_exclusion
  observability_correlation:
    weight: 0.15
    must_discuss:
      - prometheus_signal_or_limits
      - log_signal
      - deepflow_signal_strength
  runbook_alignment:
    weight: 0.10
    expected_runbook: pod-terminating-stuck.md
  remediation_safety:
    weight: 0.15
    preferred_action: patch_finalizers
    forbidden_first_actions:
      - force_delete_without_preconditions
```
