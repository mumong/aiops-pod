# Feature Specification: 可观测性异常 Case 数据集

**Feature Branch**: `007-observability-case-dataset`

**Created**: 2026-06-02

**Status**: Draft

**Input**: User description: "基于现有集群中的 metrics、logging、tracing 三类可观测数据，为多个 Kubernetes 异常 case 构建可被 AIOps agent 消费的诊断和测评数据集；tracing 数据源为 DeepFlow，在 Grafana 中已有 dashboard。第一阶段不修改现有项目业务逻辑。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 以异常 Case 归档三类可观测证据 (Priority: P1)

数据集维护者需要为每一个 Kubernetes 异常 case 建立独立目录，保存同一时间窗口内的 Prometheus metrics、Elasticsearch/Filebeat logs、DeepFlow tracing/flow、Kubernetes 对象状态、ground truth 和评测规则。

**Why this priority**: 没有稳定的 case 组织方式，后续无法扩展多个异常样本，也无法让 agent 在相同输入上可重复诊断和测评。

**Independent Test**: 选择 `TerminatingStuck + finalizer` 作为样例，检查 case 目录是否包含 case 元信息、三类可观测查询定义、采集结果、K8s 证据、根因标签和评分规则。

**Acceptance Scenarios**:

1. **Given** 一个新的 Pod 异常场景，**When** 数据集维护者创建 case，**Then** case MUST 能声明异常类型、时间窗口、影响实体、数据覆盖状态和 ground truth。
2. **Given** 同一个 case 的 Prometheus、Elasticsearch、DeepFlow 查询结果，**When** agent 或评测程序读取该 case，**Then** 三类数据 MUST 能通过 namespace、pod、node、workload、pod_ip、service 或 trace/flow 相关字段对齐到同一故障窗口。
3. **Given** 某个异常没有强 tracing 信号，**When** 数据集维护者归档 DeepFlow 数据，**Then** case MUST 明确标注 tracing 证据强度，而不是伪造业务 trace。

---

### User Story 2 - 为 Agent 诊断提供标准消费契约 (Priority: P2)

Agent 项目未来需要从数据集中读取 case，获得可观测证据、问题描述、期望根因、期望证据和修复建议，用于离线诊断和自动化评分。

**Why this priority**: 数据集不是单纯归档材料，最终目的是让 agent 可消费、可回放、可比较。

**Independent Test**: 使用一个 case 的 `case.yaml` 和 `expected/root_cause.json`，验证消费端无需访问真实集群也能知道问题范围、证据来源、根因标签、评测维度和安全修复期望。

**Acceptance Scenarios**:

1. **Given** 一个已归档 case，**When** 未来 agent 以离线模式加载它，**Then** agent MUST 能读取问题描述、实体范围、metrics/logs/traces/k8s 证据路径和 ground truth。
2. **Given** agent 生成诊断报告，**When** 评测程序对比 `evaluation/rubric.yaml`，**Then** MUST 能独立评分根因准确性、证据完整性、跨源关联、runbook 匹配和修复建议安全性。

---

### User Story 3 - 支持逐步扩展多个异常类型 (Priority: P3)

数据集维护者需要持续新增 Pod 生命周期、调度、镜像、配置、探针、资源、卷挂载等异常 case，并保持目录和标签格式一致。

**Why this priority**: 数据集价值来自覆盖面。格式必须足够稳定，避免每新增一个异常都重新设计。

**Independent Test**: 从现有 e2e manifest 中选取至少三类异常，检查它们能使用同一个 case schema 表达不同根因、不同证据强度和不同修复期望。

**Acceptance Scenarios**:

1. **Given** 现有 `pod-terminating-stuck`、`pod-imagepull-failed`、`pod-oomkilled` 等场景，**When** 转换为数据集 case，**Then** 它们 MUST 共享同一目录结构和核心字段。
2. **Given** 一个 case 只覆盖 metrics 和 logs，DeepFlow 无强关联证据，**When** 写入数据集，**Then** schema MUST 允许标注 tracing 为 `weak` 或 `not_applicable`，并解释原因。

### Edge Cases

- 某些 Pod 生命周期异常不会产生明确业务调用链；DeepFlow 数据仍可记录 flow、pod_ip、node_ip、服务影响或标注无强信号。
- 日志或 trace 查询窗口可能包含历史噪声；case 必须显式声明故障窗口和采集窗口，评测时不能把窗口外事件当成当前根因。
- Pod 已被删除时，case 必须保留采集时的 yaml/describe/events 快照，否则无法复盘 Terminating/Deleted 边界。
- 不同数据源时间戳精度和时区可能不同；case 必须统一记录时区和时间格式。
- 敏感信息、token、业务用户数据不得进入公开数据集；必要字段需要脱敏或哈希化。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 数据集 MUST 以 case/incident 为中心组织，每个异常 case 拥有独立目录和唯一 `case_id`。
- **FR-002**: 每个 case MUST 包含 `case.yaml`，记录问题描述、异常类型、时间窗口、影响实体、数据源覆盖状态和数据质量备注。
- **FR-003**: 每个 case MUST 支持 Prometheus metrics 数据，至少包含查询定义和查询结果引用。
- **FR-004**: 每个 case MUST 支持 Elasticsearch/Filebeat logs 数据，至少包含查询定义、日志结果和字段映射说明。
- **FR-005**: 每个 case MUST 支持 DeepFlow tracing/flow 数据，至少包含 Grafana/DeepFlow 查询来源、flow 或 trace 结果、证据强度标注。
- **FR-006**: 每个 case MUST 保存 Kubernetes 证据快照，包括与异常相关的 Pod yaml、describe、events，以及必要的 Node、owner workload 或 PVC/ConfigMap/Secret 摘要。
- **FR-007**: 每个 case MUST 包含 ground truth，记录根因类型、根因实体、关键证据、反证/排除项和期望 runbook。
- **FR-008**: 每个 case MUST 包含安全修复期望；例如 TerminatingStuck finalizer 分支应优先期望 scoped patch finalizer，并把 force delete 作为有条件 fallback。
- **FR-009**: 数据集 MUST 区分原始证据、归一化证据、标签和评测规则，避免评测时把 ground truth 泄漏给诊断输入。
- **FR-010**: 数据集 MUST 支持标注每类证据强度：`strong`、`weak`、`absent`、`not_applicable`。
- **FR-011**: 数据集 MUST 使用一致实体标识字段，包括 namespace、pod、container、node、workload、pod_ip、service、trace_id、flow_id。
- **FR-012**: 数据集 MUST 提供面向未来 agent 的消费契约，说明哪些文件可作为诊断输入，哪些文件仅供评分使用。
- **FR-013**: 第一阶段 MUST 不修改现有 `/ask`、`/query`、remediation 或部署逻辑。
- **FR-014**: 第一阶段 SHOULD 以独立数据集项目承载大体量 case 数据，当前 agent 仓库只保留 Speckit 规格和消费契约。

### Key Entities *(include if feature involves data)*

- **Dataset**: 一个可观测性异常样本集合，包含版本、schema 版本、数据源说明、case 列表和使用边界。
- **Case**: 一次可复现或可回放的异常事件，绑定时间窗口、实体、证据、标签和评测规则。
- **Evidence Source**: Prometheus、Elasticsearch/Filebeat、DeepFlow、Kubernetes API 等数据来源。
- **Telemetry Artifact**: 某一数据源在 case 时间窗口内的查询定义、原始结果和归一化结果。
- **Ground Truth**: 人工确认或注入脚本确认的根因、影响实体、关键证据和安全修复期望。
- **Evaluation Rubric**: 对 agent 输出进行评分的规则，覆盖根因、证据、跨源关联、runbook、修复建议和禁止项。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 首个样例 case 能完整表达 `TerminatingStuck + finalizer` 的根因、三类可观测数据覆盖状态、K8s 当前证据和安全修复期望。
- **SC-002**: 至少 10 类现有 Pod 异常 manifest 能映射到统一 case schema，而无需新增根目录结构。
- **SC-003**: 未来 agent 消费端能在不访问真实集群的情况下，从单个 case 中读取诊断输入和评分标签。
- **SC-004**: 评测规则能区分“根因正确但证据不足”“证据充分但修复建议危险”“引用历史证据当当前根因”等情况。
- **SC-005**: 数据集明确标注 metrics/logs/tracing 的覆盖度，不能因为某类数据缺失而隐式假装完整。

## Assumptions

- 当前 metrics 数据源为 Prometheus/Grafana。
- 当前 logging 数据源为 Elasticsearch/Kibana/Filebeat。
- 当前 tracing 数据源为 DeepFlow，Grafana dashboard 可作为查询入口和面板来源。
- Langfuse/agent trace 可作为 agent 自身运行轨迹的补充，但不替代 DeepFlow 业务 tracing/flow 证据。
- 第一阶段重点是 schema、样例规范和消费契约，不修改现有 agent 运行逻辑。
- 大体量采集结果后续应放入独立数据集项目；当前仓库只保留规格和合同。
