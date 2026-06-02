# Quickstart: 创建第一个 TerminatingStuck DeepFlow Case

本 quickstart 描述未来如何创建第一个数据集 case。当前阶段不要求立即实现采集脚本。

## 1. 创建 case 目录

```text
cases/pod-terminating-finalizer-stuck-001/
  case.yaml
  labels.yaml
  topology.yaml
  metrics/
  logs/
  traces/
  k8s/
  expected/
  evaluation/
```

## 2. 注入或选择异常

使用现有 manifest 方向：

```text
test/e2e/manifests/pod-terminating-stuck.yaml
test/pod_rootcause_e2e/manifests/terminating/finalizer-stuck.yaml
```

目标状态：

- Pod 当前仍存在
- `metadata.deletionTimestamp` 已存在
- `metadata.finalizers` 非空
- Node Ready
- 没有明确 volume detach/unmount 当前错误

## 3. 采集 Kubernetes 快照

应保存：

```text
k8s/pod.yaml
k8s/describe.txt
k8s/events.jsonl
k8s/node.yaml
```

关键字段：

- `metadata.deletionTimestamp`
- `metadata.finalizers`
- `spec.nodeName`
- `spec.terminationGracePeriodSeconds`
- Events 中的 Killing、FailedKillPod、Unmount、Detach 等信号

## 4. 采集 Prometheus metrics

在 `metrics/prometheus_queries.yaml` 中记录查询目的和 PromQL。

建议覆盖：

- Pod phase/status 相关指标
- Node Ready 指标
- 容器 CPU/memory 是否仍有活动
- kube-state-metrics 中可表达的 owner、container、restart 信号

结果保存到：

```text
metrics/prometheus_range.jsonl
```

## 5. 采集 Elasticsearch/Filebeat logs

在 `logs/elasticsearch_queries.yaml` 中记录查询条件。

建议关键词：

- Pod 名称
- namespace
- finalizer
- Killing
- FailedKillPod
- unmount
- detach
- kubelet

结果保存到：

```text
logs/logs.jsonl
```

## 6. 采集 DeepFlow tracing/flow

在 `traces/deepflow_queries.yaml` 中记录 Grafana/DeepFlow 查询来源。

建议从 Grafana DeepFlow dashboard 查：

- Pod IP 相关 L4 flow
- 如果有关联 service，查询 service 的 L7 请求、错误率、延迟
- Node IP 到 Pod IP 的流量变化
- 删除前后请求量是否下降、连接是否 reset/timeout

结果保存到：

```text
traces/deepflow_flows.jsonl
traces/deepflow_spans.jsonl
```

如果没有强 trace/span 信号，应在 `case.yaml` 中标注：

```yaml
observability_coverage:
  tracing:
    source: deepflow
    strength: weak
    note: DeepFlow 未直接证明 finalizer stuck，仅辅助说明业务流量影响或无强调用链信号。
```

## 7. 写入 Ground Truth

`labels.yaml` 应确认：

```yaml
root_cause:
  abnormal_type: TerminatingStuck
  branch: finalizer_stuck
  entity:
    type: Pod
    namespace: aiops-e2e
    name: terminating-stuck
expected_runbook: pod-terminating-stuck.md
```

`expected/remediation.json` 应声明：

- 首选：确认 finalizer 分支后 patch finalizers
- 条件 fallback：force delete 只能在 patch 不适用或对象删除链路已确认安全时出现
- 禁止：未确认 deletionTimestamp/finalizers 就直接推荐 force delete

## 8. 写入 Evaluation Rubric

评测至少覆盖：

- 是否识别 TerminatingStuck
- 是否识别 finalizer stuck 分支
- 是否引用 deletionTimestamp 和 finalizers
- 是否排除 Node NotReady/Unknown
- 是否如实描述 DeepFlow 证据强度
- 是否给出安全修复建议

## 9. 验收标准

一个合格 case 应满足：

- 单独复制 case 目录后仍能离线理解问题和证据
- 诊断输入不包含 ground truth
- 评测标签不依赖真实集群状态
- 三类数据源的缺失或弱信号被明确标注
- 安全修复建议能防止 agent 默认进入危险 force delete
