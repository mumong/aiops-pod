# K8s AIOps Pod 检测助手 / HolmesGPT Agent 项目指南

> 当前正式部署以 `qwen-before-architecture` 分支为准。本文按当前实现更新，历史 README 中的旧模式说明只保留仍然有效的设计思想。

## 目录

1. [项目概述](#1-项目概述)
2. [完整部署指南](#2-完整部署指南)
3. [架构总览](#3-架构总览)
4. [核心能力](#4-核心能力)
5. [工作流与数据流](#5-工作流与数据流)
6. [API 使用](#6-api-使用)
7. [核心配置](#7-核心配置)
8. [核心模块](#8-核心模块)
9. [节点开发指南](#9-节点开发指南)
10. [运维与测试](#10-运维与测试)
11. [关键目录](#11-关键目录)
12. [参考文档](#12-参考文档)

## 1. 项目概述

### 1.1 项目定位

**K8s AIOps Copilot** 是面向私有化 Kubernetes 环境的 AIOps Pod 专业检测助手。项目以 HolmesGPT Agent 为核心，结合 MCP 工具、Pod 异常 Runbook、Prometheus 可观测数据、LangGraph 工作流、多集群联邦和可选修复审批，为集群提供 Pod 异常检测、证据采集、根因分析、指标查询和修复计划能力。

核心链路可以概括为：

```text
用户自然语言问题
  -> FastAPI 入口分流
  -> 当前 Pod 状态扫描 / 指标查询
  -> Pod 异常类型识别与异常组覆盖
  -> MCP 工具采集真实证据
  -> 结构化诊断 / 查询结果 / 修复计划
  -> Markdown 报告 / 可审批修复计划
```

本项目不是单纯聊天机器人。它会通过 MCP 调用 Kubernetes、Prometheus、Bash、Helm、Runbook 等工具获取真实数据，再把工具证据组织成结构化诊断链路和最终报告。

### 1.2 适用问题

本项目主要解决私有化 Kubernetes 环境里的日常运维诊断问题：

- 当前集群是否存在异常。
- Pod 为什么处于 `CrashLoopBackOff`、`ImagePullBackOff`、`OOMKilled`、`Terminating`、`Pending` 等状态。
- CPU、内存、磁盘、网络等指标当前是多少。
- 多个集群之间哪个集群异常更严重，或者哪个集群指标更高。
- 故障诊断后，是否能生成可审批、可验证、可回滚的修复计划。

### 1.3 完整系统组成

完整智能运维助手由核心 Agent、MCP 工具集合、可观测性组件和可选前端组成：

| 组件 | 地址 | 是否必需 | 作用 |
| --- | --- | --- | --- |
| HolmesGPT Agent | [holmegpt-agent](http://192.168.1.63/wanghuhu/holmegpt-agent) | 必需 | 本项目，负责 API、工作流、LLM 调用、报告生成、联邦聚合和修复审批 |
| MCP 工具集合 | [mcpstander](http://192.168.1.63/wanghuhu/mcpstander) | 必需 | 第三方 MCP 工具集合，提供 Kubernetes、Prometheus、Bash、Helm、Runbook 等工具入口 |
| 可观测性组件 | [observability](http://192.168.1.63/platform/observability) | 完整功能建议部署 | 为 `/query` 指标查询和诊断采证提供 Prometheus 数据支撑 |
| 前端页面 | [aiops-frount](http://192.168.1.63/wanghuhu/aiops-frount) | 可选 | 提供可视化交互页面 |

Agent 和 MCP 工具集合需要部署在同一个集群中，Agent 才能通过配置中的 MCP SSE 地址调用工具。可观测性组件用于给 CPU、内存、磁盘、网络等指标查询提供数据支撑。

### 1.4 核心价值

| 能力 | 说明 |
| --- | --- |
| Pod 异常专业检测 | 先扫描当前 Pod 状态，再识别 `pod_status_keyword`、`pod_abnormal_type` 和异常组 |
| 当前态优先 | `abnormal_pods` 只能来自当前工具扫描；历史 Event 只能作为辅助，不替代当前状态 |
| 异常组覆盖 | 基于 `abnormal_groups` / `current_abnormal_summary.status_counts` 覆盖并发异常，不只分析单个 Pod |
| 证据驱动 | `evidence` 节点按计划调用真实工具，结论以当前工具结果、指标、事件、日志为依据 |
| 权威事实合同 | 优先消费 `aiops.fact-ledger.v1`，只允许通过来源、实体、UID 和引用校验的 FactRecord 进入权威报告 |
| 查询与诊断分流 | `/query` 走 direct 快路径，`/ask` 走完整诊断链路 |
| Pod Runbook 知识库 | 模型可按 Pod 异常类型抓取对应 Runbook，辅助诊断和修复计划生成 |
| MCP 扩展 | Kubernetes、Prometheus、Bash、Helm、Runbook 等能力通过 MCP SSE 接入 |
| 多集群联邦 | 支持广播式多集群查询，也支持 Agent-to-Agent 智能路由查询 |
| 上下文归档 | 工具原始输出、结构化摘要、节点输入输出、token budget、handoff 会落盘，便于复盘 |
| 修复审批 | 诊断报告可生成 remediation plan；canonical Fact 路径在没有 typed policy 时固定为 `manual_only` 且 `actions=[]` |

### 1.5 当前 Pod 异常检测模型

当前 `/ask` 的主线不是泛化集群巡检，而是 AIOps Pod 专业检测：

```text
全局 Pod 状态扫描
  -> current_abnormal_summary
  -> abnormal_pods
  -> abnormal_groups / issue_groups
  -> pod_status_keyword
  -> pod_abnormal_type
  -> matched_runbooks
  -> layer_handoff
```

关键设计：

- 第一优先级是当前仍存在的异常 Pod，而不是历史 Event 或旧报告。
- `current_abnormal_summary.status_counts` 是下游 evidence 的覆盖基准。
- 多类异常并发时，主异常组做完整验证，其他异常组至少做最小验证。
- `layer` / `derived_layer` 仍在代码里保留为内部兼容字段，但不是产品说明里的主模型。

当前主线 Pod 异常类型来自 `deploy/configmap/runbooks.yaml`：

| Pod 异常类型 | 典型状态 / 信号 | Runbook |
| --- | --- | --- |
| `Evicted` | `Evicted` / `Failed`，节点资源压力、临时存储、NoExecute 驱逐 | `pod-evicted.md` |
| `VolumeMountFailed` | `Pending` / `ContainerCreating`，`FailedMount`、`FailedAttachVolume` | `pod-volume-mount-failed.md` |
| `PendingUnschedulable` | `Pending`，`FailedScheduling`、资源不足、taint、affinity 不匹配 | `pod-pending-unschedulable.md` |
| `NodeLostOrUnknown` | `Unknown`，Node `NotReady` / `Unknown`、kubelet 停止上报 | `pod-node-lost-unknown.md` |
| `TerminatingStuck` | `Terminating`，`deletionTimestamp`、finalizer、kubelet/volume detach 卡住 | `pod-terminating-stuck.md` |
| `OOMKilled` | `CrashLoopBackOff` / `Error`，Last State `OOMKilled`、exit code 137 | `pod-oomkilled.md` |
| `CrashLoopBackOffRuntime` | `CrashLoopBackOff`，非 OOM、非镜像拉取、非配置缺失的容器反复退出 | `pod-crashloop-runtime.md` |
| `ImagePullFailed` | `ImagePullBackOff` / `ErrImagePull` / `ImageInspectError` | `pod-imagepull-failed.md` |
| `SandboxCreateFailed` | `ContainerCreating` / `FailedCreatePodSandBox`，CNI/IPAM/runtime sandbox 异常 | `pod-sandbox-create-failed.md` |
| `ConfigError` | `CreateContainerConfigError` / `CreateContainerError` / 配置启动失败 | `pod-config-error.md` |
| `NotReadyProbeFailed` | Running 但 READY 不满足，readiness/startup/liveness probe 失败 | `pod-notready-probe-failed.md` |

## 2. 完整部署指南

### 2.1 部署顺序

建议部署顺序：

1. 部署 MCP 工具集合 `mcpstander`。
2. 部署可观测性组件 `observability`，如果需要完整指标查询能力。
3. 部署本项目 `holmegpt-agent`。
4. 按需部署前端项目 `aiops-frount`。

部署前需要配置各项目里的镜像仓库、集群访问参数、LLM 参数、MCP 地址、federation 子集群地址、前端后端地址等必要参数。

### 2.2 部署 MCP 工具集合

下载项目：

```bash
git clone http://192.168.1.63/wanghuhu/mcpstander
cd mcpstander
```

首次部署可在根目录执行：

```bash
make deploy
```

重新部署或希望先删除旧资源时执行：

```bash
make delete deploy
```

MCP 工具集合部署完成后，Agent 才能正常调用 Kubernetes、Prometheus、Bash、Helm、Runbook 等外部能力。

### 2.3 部署可观测性组件

如果需要 CPU、内存、磁盘、网络等指标查询能力，先部署可观测性组件。

下载资源：

```bash
git clone http://192.168.1.63/platform/observability
cd observability
```

在对应资源目录执行：

```bash
helm install observability ./ -n xnet --create-namespace
```

等待可观测性相关服务全部启动后，再部署或重启 Agent。

### 2.4 部署 HolmesGPT Agent

下载本项目：

```bash
git clone http://192.168.1.63/wanghuhu/holmegpt-agent
cd holmegpt-agent
git checkout qwen-before-architecture
```

关键配置文件：

| 文件 | 作用 |
| --- | --- |
| `deploy/secrets/core.yaml` | LLM API Key、模型、API Base、上下文窗口、日志级别等敏感配置 |
| `deploy/configmap/config.yaml` | MCP 地址、workflow、remediation、metrics、federation、i18n 等运行配置 |
| `deploy/configmap/runbooks.yaml` | Runbook 知识库 |
| `deploy/k8s-simple.yaml` | Agent Deployment、Service、PVC |
| `deploy/rbac.yaml` | ServiceAccount 和 RBAC |

#### 单节点运行

```bash
make delete deploy
```

#### 多集群主集群部署

多集群模式下，需要先修改主集群 `deploy/configmap/config.yaml` 中的 `federation.sub_agents`，确保每个子集群 URL 都能被主集群 Pod 访问。

```bash
make delete deploy-master
```

#### 多集群子集群部署

在其他被控制的子集群中执行：

```bash
make delete deploy-slave
```

子集群会关闭 federation，只提供单集群 `/ask` 和 `/query` 能力供主集群调用。

#### 代码变更后的升级

如果 Agent 代码发生变化，先修改 `VERSION` 中的版本号，再构建、推送并部署。

主集群：

```bash
make delete build push deploy-master
```

子集群：

```bash
make delete build push deploy-slave
```

单节点：

```bash
make delete build push deploy
```

### 2.5 部署前端

下载前端项目：

```bash
git clone http://192.168.1.63/wanghuhu/aiops-frount
cd aiops-frount
```

在前端项目目录执行：

```bash
make delete deploy
```

前端需要配置后端 Agent 的访问地址，确保浏览器或网关能访问 `holmegpt-agent` 暴露的服务。

### 2.6 部署验证

检查 Agent：

```bash
kubectl get pods -n aiops
kubectl get svc -n aiops
curl http://<node-ip>:30800/health
```

检查 MCP 状态：

```bash
curl http://<node-ip>:30800/api/v1/mcp/status
```

执行一次诊断：

```bash
curl --no-buffer -G "http://<node-ip>:30800/ask" \
  --data-urlencode "q=我的集群现在有什么问题？"
```

执行一次查询：

```bash
curl --no-buffer -G "http://<node-ip>:30800/query" \
  --data-urlencode "q=集群 CPU 和内存使用率是多少？"
```

## 3. 架构总览

### 3.1 当前正式架构

当前服务对外是一个 FastAPI API Server，内部核心是：

- AICall + LangGraph 工作流。
- MCP 工具调用。
- Runbook 知识库。
- Context archive 和 token budget 管理。
- 多集群 federation。
- Post-diagnosis remediation。

当前实现已经是 AICall + Workflow 唯一正式模式，不再通过旧 README 中的 `USE_WORKFLOW` 切换新旧执行模式。

### 3.2 整体架构图

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ 用户 / 前端 / curl                                                           │
│   /ask   /query   /federation/*   /remediation/approve                       │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ FastAPI API 层                                                               │
│ app/api/routes.py                                                            │
│ - 参数解析、GET/POST、text/SSE 流式响应                                      │
│ - /ask 进入诊断链路，/query 进入 direct 查询链路                             │
│ - /federation/* 进入多集群聚合或 Agent-to-Agent                              │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ HolmesService 服务编排层                                                     │
│ app/core/service.py                                                          │
│ - 加载 Secret / ConfigMap / Runbook                                          │
│ - 初始化 AICall、MCP tools、federation、remediation                           │
│ - 渲染终端和前端可读的流式输出                                                │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ LangGraph Workflow                                                           │
│ layer -> evidence -> rca -> conclusion                                       │
│ - WorkflowState 在节点间传递结构化字段                                       │
│ - structured_runtime 使用 Pydantic schema 校验关键节点输出                   │
│ - query direct 模式可以从 layer 直接到 conclusion                            │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
                         ┌─────────────┴─────────────┐
                         ▼                           ▼
┌──────────────────────────────────────┐ ┌─────────────────────────────────────┐
│ MCP 工具集合                          │ │ 上下文与报告存储                    │
│ mcpstander                            │ │ /tmp/aiops/reports                  │
│ - Kubernetes / Prometheus / Bash       │ │ - context_archives                  │
│ - Helm / Runbook / Connectivity        │ │ - saved reports                     │
└──────────────────────────────────────┘ └─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ Kubernetes 集群 / Prometheus / 外部工具 / 子集群 Agent                        │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 设计原则

- LLM 负责理解意图、规划证据、解释现象和生成报告。
- MCP 工具负责获取真实当前态数据。
- 工作流负责把诊断拆成稳定阶段，避免简单查询走完整诊断链。
- Pydantic schema 负责约束关键节点输出，fallback 负责兼容 OpenAI-compatible 网关不支持原生 structured output 的情况。
- context archive 负责保存原始证据，最终报告只展示关键摘要和引用。
- remediation 默认以审批优先，生产环境不要直接打开不受控自动写操作。

## 4. 核心能力

### 4.1 能力清单

| 能力 | 当前实现 |
| --- | --- |
| 单集群诊断 | `/ask` 进入 `layer -> evidence -> rca -> conclusion` |
| 单集群查询 | `/query` 进入 direct 快路径，适合指标、列表、状态查询 |
| 多集群广播 | `/federation/ask`、`/federation/query` 并发调用配置中的子集群 |
| Agent-to-Agent 联邦 | `/federation/ask/v2`、`/federation/query/v2` 由主 Agent 决定查询哪些子集群 |
| MCP 工具调用 | 通过 `mcp_servers` 配置加载 Kubernetes、Prometheus、Bash、Helm、Runbook 等工具 |
| Runbook 参考 | 模型可调用 Runbook 工具，最终报告区分核心 Runbook 和参考 Runbook |
| 结构化运行时 | `LayerOutput`、`LayerHandoff`、`QueryResult`、Evidence/RCA 结构通过 Pydantic 校验 |
| Canonical Fact Ledger | 保留 MCP canonical Ledger，严格门禁 trusted legacy adapter，并校验 RCA 引用的 Fact ID |
| 权威报告 | 精确事实、coverage、限制和机器附录从 validated FactRecords 确定性渲染 |
| 人类可读报告 | 正文解释证据且隐藏内部 ID；机器附录保留完整 Fact、引用和限制；混合 provider 下真实信号优先于单源空结果 |
| 上下文治理 | observation summary、context compaction、context archive、token budget 日志 |
| 32K 硬门禁 | 每次 provider-bound 请求在调用前校验，超限时先做确定性压缩或停止 |
| 流式输出 | 支持 text 和 SSE，展示节点进度、工具调用、模型输出和最终报告 |
| 修复审批 | `workflow.remediation` 控制 deterministic/react executor 和 review/auto mode |
| 报告查看 | `/reports`、`/reports/{filename}` 查看已保存报告 |
| 大输出查看 | `/artifacts/{artifact_id}` 获取被截断工具输出全文 |

### 4.2 查询与诊断边界

`/ask` 用于“为什么、分析原因、当前有什么异常、如何修复”这类诊断问题。

`/query` 用于“是多少、列出来、对比指标、查看状态”这类窄查询问题。

这个分流是当前架构最重要的边界之一：查询不应该因为进入完整 RCA 链路而变慢，诊断也不应该只返回一组指标而缺少证据链和根因分析。

## 5. 工作流与数据流

### 5.1 `/ask` 诊断链路

```text
question
  -> layer      扫描当前 Pod 状态，识别异常 Pod、异常组和 pod_abnormal_type
  -> evidence   围绕异常组制定证据计划，调用 MCP 工具验证当前状态
  -> rca        基于 evidence 结构化事实收敛根因，默认 lite 模式不重复调工具
  -> conclusion 汇总最终诊断报告，可输出结构化 remediation plan
```

| 节点 | 作用 | 关键输出 |
| --- | --- | --- |
| `layer` | 轻量扫描当前 Pod 状态，形成异常概览和 Pod 异常类型 | `current_abnormal_summary`、`abnormal_pods`、`abnormal_groups`、`pod_status_keyword`、`pod_abnormal_type`、`layer_handoff` |
| `evidence` | 根据 `layer_handoff` 生成证据计划，按异常组调用 MCP 工具验证当前状态 | `evidence_items`、`tool_results`、`evidence_analysis`、`evidence_facts`、`evidence_conflicts` |
| `rca` | 基于 evidence 结构化事实分析根因和因果链 | `root_cause`、`causal_chain`、`rca_analysis`、`primary_runbook_id` |
| `conclusion` | 生成最终 Markdown 报告，并按需生成 remediation plan | `conclusion_formatted`、`remediation_plan`、`remediation_result` |

`HEALTHY` 会从 `layer` 直接到 `conclusion`。这类问题不进入完整采证和 RCA，避免把健康态硬分析成故障。

#### Canonical Fact Ledger authority

MCP 原生 `source=mcp_canonical`、`legacy_contract=false` 的 Ledger 是首选路径。
滚动升级期间，legacy 结果只有在来源、namespace/Pod、独立 Pod UID、
evidence refs、Fact ID 和实体关系全部通过时才会标记为 `trusted_legacy`。
其他结果保留为兼容或拒绝状态，不会把模型文本升级为精确事实。

RCA 仍由模型形成 hypothesis 和 supporting Fact ID，但 Conclusion 只发布引用
校验通过的 FactRecords。指标采样间隔、代表性 Trace、可用性未测量、容量策略
缺失和拓扑因果边界由确定性代码生成。

正文与机器附录的边界、混合来源优先级和通用扩展规则见
[`docs/human-readable-diagnostic-reports.md`](docs/human-readable-diagnostic-reports.md)。

### 5.2 `/query` 查询链路

```text
question
  -> layer      direct query 模式下调用工具并产出 query_result
  -> conclusion 本地渲染 query_result，不走完整诊断链
```

`/query` 的目标是快而窄：只查询用户关心的数据，不进入 evidence/RCA 诊断链。Prometheus 指标类查询依赖可观测性组件。

### 5.3 多集群联邦链路

当前有两类联邦入口：

| 入口 | 模式 | 说明 |
| --- | --- | --- |
| `/federation/ask` | 广播诊断 | 并发调用所有 enabled 子集群的 `/ask`，再汇总 |
| `/federation/query` | 广播查询 | 并发调用所有 enabled 子集群的 `/query`，再汇总 |
| `/federation/ask/v2` | Agent-to-Agent 诊断 | 主 Agent 根据问题决定查询哪些子集群、调用哪些子任务 |
| `/federation/query/v2` | Agent-to-Agent 查询 | 主 Agent 根据问题做跨集群查询和对比 |

主集群开启 `federation.enabled=true` 并配置 `sub_agents`；子集群通过 `make deploy-slave` 关闭 federation，作为被调度 Agent 暴露单集群能力。

### 5.4 修复执行链路

修复是诊断之后的可选阶段，由 `workflow.remediation` 控制：

```text
诊断报告
  -> remediation_plan
  -> approval request
  -> deterministic executor 或 react executor
  -> verify
  -> remediation_result
```

| 配置 | 说明 |
| --- | --- |
| `executor=deterministic` | 按报告中的结构化 plan 固定执行，适合明确命令序列 |
| `executor=react` | LLM 根据真实 observation 多轮决策，适合需要边执行边验证的场景 |
| `mode=review` | 计划和写动作需要人工审批，推荐生产环境使用 |
| `mode=auto` | 自动执行安全校验通过的动作，生产环境谨慎使用 |

旧环境变量或请求参数 `remediate` 不再控制修复执行，修复行为以 `workflow.remediation` 配置为准。
对 canonical Fact Ledger 报告，上述执行配置不会覆盖证据合同：没有独立
typed Remediation Policy Contract 时只允许人工复核和只读验证。

## 6. API 使用

### 6.1 端点列表

| 端点 | 用途 | 推荐场景 |
| --- | --- | --- |
| `/ask` | 单集群诊断 | 故障分析、根因分析、修复建议 |
| `/query` | 单集群查询 | 指标查询、资源列表、状态查看 |
| `/federation/ask` | 多集群广播诊断 | 所有子集群都要诊断时 |
| `/federation/query` | 多集群广播查询 | 所有子集群都要查询时 |
| `/federation/ask/v2` | 多集群 Agent 诊断 | 需要主 Agent 自主选择子集群时 |
| `/federation/query/v2` | 多集群 Agent 查询 | 需要跨集群对比或智能路由时 |
| `/remediation/approve` | 修复审批接口 | `mode=review` 时审批 plan 或写动作 |
| `/health` | 健康检查 | 部署验证 |
| `/tools` | 工具列表 | 调试 |
| `/tools/detail` | 工具详情和 schema | 二次开发、排障 |
| `/api/v1/mcp/status` | MCP 状态 | 检查 MCP server 连接 |
| `/runbooks` | Runbook 列表 | 调试 |
| `/reports` | 查看已保存报告 | 联邦报告和历史报告查看 |
| `/reports/{filename}` | 查看具体报告内容 | 报告详情 |
| `/artifacts/{artifact_id}` | 查看大输出 artifact | 工具输出被截断时 |
| `/q/{question}` | 兼容快捷入口 | 不推荐作为正式入口 |

### 6.2 常用示例

单集群诊断：

```bash
curl --no-buffer -G "http://HOST:30800/ask" \
  --data-urlencode "q=我的集群有什么问题？"
```

单集群查询：

```bash
curl --no-buffer -G "http://HOST:30800/query" \
  --data-urlencode "q=集群 CPU 和内存使用率是多少，具体到每个 node"
```

多集群 Agent-to-Agent 诊断：

```bash
curl --no-buffer -G "http://HOST:30800/federation/ask/v2" \
  --data-urlencode "q=main 集群和 cluster-24 现在分别有什么问题？"
```

多集群 Agent-to-Agent 查询：

```bash
curl --no-buffer -G "http://HOST:30800/federation/query/v2" \
  --data-urlencode "q=对比 main 和 cluster-24 的 CPU 使用率"
```

人工审批修复动作：

```bash
curl -X POST "http://HOST:30800/remediation/approve" \
  -d run_id=<run_id> \
  -d approval_id=<approval_id> \
  -d approved=true \
  -d reviewer=operator
```

交互式修复客户端：

```bash
.venv/bin/python tools/aiops_remediate_chat.py --url http://HOST:30800 "我的集群有什么问题？"
```

## 7. 核心配置

正式运行配置在 `deploy/configmap/config.yaml`，敏感配置在 `deploy/secrets/core.yaml`。

### 7.1 Secret: LLM 连接配置

`deploy/secrets/core.yaml` 主要配置：

| 配置 | 说明 |
| --- | --- |
| `LLM_API_KEY` | LLM 网关 API Key |
| `LLM_MODEL` | 模型名，例如 OpenAI-compatible Qwen、DeepSeek、Claude、OpenAI 等 |
| `LLM_API_BASE` | OpenAI-compatible API Base，使用公网服务时可为空 |
| `MODEL_CONTEXT_WINDOW` | 模型真实上下文窗口，用于 token budget 百分比计算 |
| `AIOPS_CONTEXT_USAGE_PROBE` | 是否请求网关返回真实 prompt token 使用量 |
| `AIOPS_TOKENIZER_JSON_PATH` | 可选，模型 tokenizer.json 路径 |
| `AIOPS_TIKTOKEN_ENCODING` | 可选，tiktoken 编码名 |
| `LOG_LEVEL` | 服务日志级别 |

不要把真实 Key 写入 README、提交说明或问题记录中。切换模型时优先改 Secret，不要在 ConfigMap 里重复维护默认模型。

### 7.2 ConfigMap: MCP Servers

`mcp_servers` 定义 Agent 可用的外部工具入口。当前主力能力包括：

- `k8s-mcp-service`：Kubernetes 资源查询、describe、logs、events、yaml、table 等。
- `prometheus_tool`：PromQL 即时查询和范围查询。
- `bash_tool`：bash 命令执行。
- `helmcharts`：Helm list/status/values 等。
- `core-investigation`：任务分解与规划。
- `runbook`：Runbook 排障知识库。
- `connectivity_check_tool`：TCP 连通性检查。

示例：

```yaml
mcp_servers:
  k8s-mcp-service:
    description: "K8s MCP - kubectl get/describe/logs/events/yaml/table 等只读资源查询"
    config:
      url: "http://mcp-server-manager.mcp.svc.cluster.local:8093/sse"
      mode: "sse"
    enabled: true
```

`description` 会影响模型选择工具，修改工具用途时需要同步更新描述。

### 7.3 ConfigMap: LLM transport

Qwen/OpenAI-compatible 网关可以通过 `llm.extra_body` 配置 provider-specific 参数，例如模型思考开关：

```yaml
llm:
  extra_body:
    chat_template_kwargs:
      enable_thinking: true
```

这个配置属于模型传输控制，不是工作流业务逻辑。

### 7.4 ConfigMap: Workflow

核心配置示例：

```yaml
workflow:
  rca_mode: lite
  nodes:
    layer: true
    evidence: true
    rca: true
    conclusion: true
  max_steps:
    layer: 15
    evidence: 20
    rca: 0
    conclusion: 0
  structured_runtime:
    enabled: true
    fallback_enabled: true
```

说明：

- `rca_mode=lite`：RCA 不重复调工具，只基于已采集证据分析。
- `max_steps` 直接作为 LangGraph recursion limit，模型到工具一轮通常会消耗多次 recursion。
- `structured_runtime.enabled=true`：关键节点优先使用 Pydantic 结构化输出。
- `structured_runtime.fallback_enabled=true`：OpenAI-compatible 网关不支持原生 structured output 时，可回退到文本 JSON 并继续用 Pydantic 校验。
- `/ask` 和 `/query` 会在 API 层覆盖节点路径，`/query` 使用 direct 快路径。

### 7.5 ConfigMap: Streaming 与 Context

```yaml
workflow:
  think_stream:
    mode: full
    max_chars: 1200
  observation_summary:
    mode: rule
    max_chars: 3000
  context_compaction:
    enabled: true
    nodes:
      - evidence
    max_context_window: 35000
    trigger_ratio: 0.70
    max_compactions_per_call: 1
    summary_max_tokens: 1200
```

说明：

- `think_stream.mode` 控制 `<think>` 内容展示：`full`、`truncated`、`hidden`。
- `observation_summary.mode=rule` 默认使用规则摘要，`ai` 会额外调用 LLM 摘要，成本更高。
- `context_compaction` 控制 evidence 上下文超过阈值后的压缩策略。
- context archive 默认落在 `/tmp/aiops/reports/context_archives`。

### 7.6 ConfigMap: Remediation

```yaml
workflow:
  remediation:
    enabled: true
    executor: react
    mode: review
    approval_timeout_seconds: 600
    max_iterations: 10
    max_write_actions: 10
    max_duration_seconds: 900
    verify_settle_seconds: 5
```

生产环境建议使用 `mode=review`。`mode=auto` 只适合受控测试或明确接受自动写动作风险的环境。

### 7.7 ConfigMap: Federation

主集群开启 federation，子集群关闭 federation。

```yaml
federation:
  enabled: true
  max_tokens_per_agent: 0
  synthesis_timeout: 300
  sub_agents:
    - name: "main"
      url: "http://localhost:8000"
      description: "主集群"
      enabled: true
    - name: "cluster-24"
      url: "http://10.2.0.24:30800"
      description: "被管集群 10.2.0.24"
      enabled: true
```

注意：

- 主集群自身可以配置为 `http://localhost:8000`。
- 子集群 URL 必须从主集群 Pod 内可访问。
- 修改 federation 配置后需要重新应用 ConfigMap 并重启 Agent，或重新执行部署命令。

### 7.8 ConfigMap: Metrics 与 i18n

```yaml
i18n:
  prompt_language: zh
  response_language: zh

metrics:
  enabled: false
  thresholds:
    mttr_seconds: 600
    rca_confidence: 0.8
    evidence_completeness: 0.9
```

`metrics.enabled=false` 时，最终输出默认只展示性能统计和诊断追踪；开启后会展示 MTTR、证据完整率、根因置信度、Runbook 匹配等质量指标。

## 8. 核心模块

### 8.1 模块职责

| 模块 | 路径 | 职责 |
| --- | --- | --- |
| API 层 | `app/api/routes.py` | 注册 `/ask`、`/query`、`/federation/*`、`/health`、`/tools`、`/runbooks`、`/reports` 等端点 |
| 服务编排 | `app/core/service.py` | 加载配置、初始化模型、加载 MCP 工具、执行工作流、渲染流式输出 |
| LLM 调用 | `app/core/aicall/` | AICall、LangGraph Agent、工具封装、流式事件 |
| 工作流图 | `app/core/workflow/graph.py` | 构建 `layer -> evidence -> rca -> conclusion` 图和条件路由 |
| 工作流执行器 | `app/core/workflow/executor.py` | 执行 LangGraph，发出节点生命周期和流式事件 |
| 工作流状态 | `app/core/workflow/state.py` | 定义 `WorkflowState`，承载节点间结构化字段 |
| 结构化 schema | `app/core/workflow/schemas.py` | 定义 Layer、Handoff、Query、Evidence、RCA 等 Pydantic contract |
| 工作流节点 | `app/core/workflow/nodes/` | layer、evidence、rca、conclusion 四个节点实现 |
| 报告展示 | `app/core/workflow/report_presentation.py` | 通用维度投影、source-backed observation 归一化和 AI 事实引用校验 |
| Context 管理 | `app/core/context/` | context archive、token budget、observation summary、usage probe |
| 修复执行 | `app/core/remediation/` | 修复计划解析、审批、deterministic/react 执行 |
| 多集群联邦 | `app/core/federation/` | 子集群注册、广播查询、Agent-to-Agent、报告聚合 |
| Runbook | `app/core/runbook/` | Runbook catalog 加载与管理 |
| MCP 管理 | `app/core/mcp/` | MCP 状态管理和兼容补丁 |
| Holmes 兼容层 | `app/core/holmes/` | artifacts、streaming、config loader、工具日志补丁 |
| 配置与部署 | `deploy/` | Kubernetes YAML、Secret、ConfigMap、RBAC |

### 8.2 工作流节点文件

```text
app/core/workflow/nodes/
├── base.py
├── layer_classifier.py
├── evidence_collector.py
├── root_cause_analyzer.py
└── conclusion_formatter.py
```

### 8.3 关键状态字段

| 字段 | 来源 | 说明 |
| --- | --- | --- |
| `question` | API | 用户原始问题 |
| `run_id` | executor | 当前执行 ID |
| `layer` / `derived_layer` | layer | 内部兼容字段，用于保留历史路由/归因语义，不作为当前 README 主模型 |
| `layer_handoff` | layer | 给 evidence/RCA/conclusion 的结构化交接信息 |
| `current_abnormal_summary` | layer | 当前 Pod 异常概览，包含状态计数和代表行 |
| `abnormal_pods` | layer | 当前扫描确认仍异常的 Pod 列表 |
| `abnormal_groups` | layer | 当前异常组，按异常状态族聚合 |
| `pod_status_keyword` | layer | 当前异常状态关键字，如 `ImagePullBackOff`、`CrashLoopBackOff`、`Terminating` |
| `pod_abnormal_type` | layer | 归一化 Pod 异常类型，如 `ImagePullFailed`、`OOMKilled`、`TerminatingStuck` |
| `status_category` | layer | Pod 异常类型的稳定分类，如 `image_registry`、`container_resource`、`lifecycle` |
| `query_result` | layer | `/query` direct 模式结构化查询结果 |
| `evidence_items` | evidence | 已采集证据 |
| `tool_results` | evidence | 工具调用结果 |
| `evidence_facts` | evidence | 已验证事实摘要 |
| `root_cause` | rca | 根因结论 |
| `causal_chain` | rca | 因果链 |
| `primary_runbook_id` | rca | 核心 Runbook |
| `conclusion_formatted` | conclusion | 最终 Markdown 报告 |
| `remediation_plan` | conclusion | 结构化修复计划 |
| `remediation_result` | remediation | 修复执行结果摘要 |
| `context_archive_ref` | context | 当前 run 的归档目录引用 |
| `tool_artifact_refs` | context | 工具 raw/structured/summary 归档引用 |

## 9. 节点开发指南

### 9.1 节点基类约定

所有工作流节点都继承 `WorkflowNode`，核心约定是：

- `node_id`：节点唯一标识，需要与 `graph.py` 中的节点 ID 一致。
- `node_name`：节点显示名，用于日志和流式输出。
- `get_required_fields()`：声明节点依赖的 `WorkflowState` 字段。
- `execute(state)`：节点入口，负责错误处理和状态更新。
- `_execute_impl(state)`：节点实际业务逻辑。

节点只更新自己负责的字段，不直接修改无关状态。需要传递给下游的信息应放入结构化字段，例如 `layer_handoff`、`evidence_facts`、`query_result`。

### 9.2 新增节点流程

1. 在 `app/core/workflow/nodes/` 下创建新节点文件。
2. 继承 `WorkflowNode`，实现 `node_id`、`node_name`、`get_required_fields()` 和 `_execute_impl()`。
3. 如果节点有新的结构化输出，在 `app/core/workflow/schemas.py` 增加 Pydantic schema。
4. 如果节点要给下游传递新字段，在 `app/core/workflow/state.py` 增加 `WorkflowState` 字段。
5. 在 `app/core/prompts.py` 增加或更新节点 prompt。
6. 在 `app/core/workflow/graph.py` 的 `NODE_REGISTRY`、节点顺序和条件路由中注册节点。
7. 增加 focused unit tests，至少覆盖节点输入、结构化输出、失败 fallback 和路由行为。

### 9.3 节点开发注意事项

- 证据采集必须优先使用 MCP 工具当前返回，不把历史 event 直接当作当前故障。
- 结构化输出必须经过 schema 校验，不能只依赖模型自然语言。
- `/query` direct 路径不能引入 evidence/RCA 的额外延迟。
- 大工具输出不要直接塞满下游上下文，应通过 artifact、summary、context archive 引用。
- 写操作和修复执行必须走 remediation 审批与安全约束，不要在普通诊断节点里直接执行写动作。

## 10. 运维与测试

### 10.1 Make 命令

Agent 项目目录常用命令：

```bash
make build
make push
make deploy
make deploy-master
make deploy-slave
make delete
make restart
make logs
```

查看服务：

```bash
kubectl get pods -n aiops
kubectl get svc -n aiops
curl http://<node-ip>:30800/health
```

查看日志：

```bash
make logs
```

查看报告：

```bash
curl http://<node-ip>:30800/reports
```

查看 MCP 状态：

```bash
curl http://<node-ip>:30800/api/v1/mcp/status
```

### 10.2 本地开发

本仓库使用 Python 3.12。当前环境中建议使用项目虚拟环境：

```bash
.venv/bin/python run.py
```

如果本地没有 `CONFIG_FILE`，服务会尝试读取 `config/config.yaml`；Kubernetes 部署时使用 `/app/config-override/config.yaml`。

### 10.3 Focused unit tests

常用 focused unit tests：

```bash
.venv/bin/python -m pytest -q \
  tests/unit/workflow/test_fast_paths.py \
  tests/unit/workflow/test_query_direct_mode.py
```

结构化 fallback 相关场景可参考：

```bash
.venv/bin/python -m pytest -q tests/unit/workflow
```

Fact Ledger authority、报告和修复安全的 focused 回归：

```bash
.venv/bin/python -m pytest -q \
  tests/unit/aicall/test_observation_processing.py \
  tests/unit/workflow/test_fact_contract.py \
  tests/unit/workflow/test_context_handoff.py \
  tests/unit/workflow/test_ask_conclusion_remediation_json.py \
  tests/unit/remediation/test_plans.py
```

## 11. 关键目录

| 路径 | 说明 |
| --- | --- |
| `app/api/routes.py` | API 路由 |
| `app/core/service.py` | 服务初始化、工作流执行、文本流渲染 |
| `app/core/aicall/` | LLM 和 LangGraph Agent 调用封装 |
| `app/core/workflow/` | LangGraph 工作流、节点、schema、metrics |
| `app/core/remediation/` | 修复计划解析、审批和执行 |
| `app/core/federation/` | 多集群联邦查询 |
| `app/core/context/` | context archive、token budget、工具 observation 摘要 |
| `app/core/mcp/` | MCP server 状态管理 |
| `deploy/` | Kubernetes 部署资源 |
| `docs/` | 架构、上下文、流式输出、修复审批等详细文档 |
| `specs/` | Speckit 功能规格和任务 |
| `test/` | E2E 场景和数据集 |
| `tests/unit/` | 单元测试 |

## 12. 参考文档

- `docs/ARCHITECTURE.md`
- `docs/GUIDE.md`
- `docs/aiops-observability-mcp-design.md`
- `docs/aiops-traced-oom-test-environment.md`
- `docs/aiops-observability-sprint-test-guide.md`
- `docs/remediation-usage.md`
- `docs/human-readable-diagnostic-reports.md`
- `docs/prompt-governance.md`
- `docs/workflow-structured-runtime-evolution-2026-05-09.md`
- `docs/上下文管理设计与实现.md`
- `docs/工作流上下文流转说明.md`
- `docs/流式输出设计与演进.md`
