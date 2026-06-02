# Research: 可观测性异常 Case 数据集

**Date**: 2026-06-02

## 结论摘要

本项目的数据集应采用 case-centric 组织方式：每个异常事件是一个独立 case，case 下分别保存 metrics、logs、traces、Kubernetes 快照、ground truth 和 evaluation rubric。

不建议按数据源分别建立孤立目录，例如只按 Prometheus、Elasticsearch、DeepFlow 分桶。诊断任务需要回答的是“同一故障窗口内哪些实体异常、哪些证据支持根因、agent 应输出什么”，因此事件维度应高于数据源维度。

## 外部参考

### GAIA / AIOps Challenge

GAIA 类数据集面向 AIOps 异常检测和根因分析，通常会围绕异常事件保存多源观测数据、异常标签和评测目标。这支持本项目采用“case + 多源遥测 + 标签”的组织方式。

Reference: https://github.com/CloudWise-OpenSource/GAIA-DataSet

### RCAEval

RCAEval 面向微服务根因分析评测，强调可复现 benchmark、故障注入/标签和遥测数据之间的关联。它说明数据集必须保留 ground truth，并区分诊断输入与评分标签。

Reference: https://github.com/phamquiluan/RCAEval

### AIOpsLab

AIOpsLab 把 AIOps agent 评测放在任务环境、故障注入、观测数据和评分体系中理解。它对本项目的启发是：数据集不只是数据归档，还必须提供 agent 可执行或可回放的评测任务描述。

Reference: https://arxiv.org/abs/2501.06706

### OpenTelemetry Semantic Conventions

OpenTelemetry 语义规范可作为字段命名和跨源关联参考，尤其适用于服务名、Kubernetes namespace/pod/container/node、trace/span、网络和资源属性字段。

Reference: https://opentelemetry.io/docs/concepts/semantic-conventions/

### DeepFlow

DeepFlow 是当前集群 tracing/flow 维度的数据源。数据集应保存 DeepFlow/Grafana 查询来源、查询结果、flow/trace 证据强度，而不是仅保存 dashboard 截图。

Reference: https://deepflow.io/docs/

## 当前环境事实

已在集群中确认以下可观测组件存在：

- metrics: `xnet/observability-prometheus`、`xnet/observability-grafana`
- logging: `xnet/elasticsearch-external`、`xnet/observability-kibana`、`xnet/observability-filebeat-*`
- tracing/flow: `xnet/deepflow-agent`、`xnet/observability-deepflow-server`、`xnet/observability-deepflow-app`、`xnet/observability-clickhouse`

当前仓库已有可复用上下文：

- `test/e2e/manifests/`: Pod 异常主线 manifest
- `test/pod_rootcause_e2e/manifests/`: 更细粒度根因变体 manifest
- `deploy/configmap/runbooks.yaml`: 异常类型、证据和修复建议
- `/tmp/aiops/reports/context_archives/<run_id>/`: agent 运行时证据归档结构
- `docs/quality-metrics.md`: 现有诊断质量指标说明

## 设计决策

### Decision 1: 数据集按 case 组织

**Decision**: 使用 `cases/<case_id>/` 作为核心目录。

**Rationale**: 根因诊断和评测以故障事件为单位。按 case 组织可以把同一时间窗口内的 metrics、logs、DeepFlow、K8s 快照和 ground truth 对齐。

**Alternatives considered**:

- 按数据源组织：查询方便但难以表达一次故障。
- 只保存 agent context archive：能复盘 agent 过程，但不能作为独立 benchmark 数据集。

### Decision 2: DeepFlow 作为 tracing 主数据源

**Decision**: `traces/` 目录保存 DeepFlow/Grafana 查询定义、flow/trace 结果和证据强度。

**Rationale**: 用户确认 tracing 是 DeepFlow，集群中也存在 DeepFlow agent/server/app 和 ClickHouse。Langfuse 只作为 agent 自身调用轨迹补充。

**Alternatives considered**:

- 等待 Jaeger/Tempo/OTel：不符合当前环境。
- 只保存 Langfuse：会混淆业务 tracing 和 agent tracing。

### Decision 3: 明确诊断输入和评分标签隔离

**Decision**: `metrics/`、`logs/`、`traces/`、`k8s/` 可作为诊断输入；`expected/` 和 `evaluation/` 仅供评测使用。

**Rationale**: 防止 agent 读取 ground truth 后产生虚假高分。

### Decision 4: 支持证据强度标注

**Decision**: 每类证据使用 `strong`、`weak`、`absent`、`not_applicable` 标注覆盖度和有效性。

**Rationale**: 某些 Kubernetes 生命周期异常不会天然产生强业务 trace。数据集应如实记录缺失或弱证据，而不是制造不真实 trace。
