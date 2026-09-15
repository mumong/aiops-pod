# K8s AIOps Copilot

面向 Kubernetes 的智能运维诊断助手。通过自然语言查询集群、定位异常 Pod，调用 MCP 工具获取现场数据，输出包含**异常现象、真实证据、根因分析、修复建议与未知项**的报告。

本文按当前源码与部署清单介绍，不代表所有运行环境都已更新到相同版本。主要入口：[部署](#部署)、[使用](#使用)、[创建异常测试环境](#创建异常测试环境)、[三维数据采集](#本次更新三维可观测性采集)、[真实异常数据读法](#如何理解报告中的三维数据)、[更多 PromQL](#还能查询哪些-promql)、[日志与归档](#日志归档与-langfuse)。

## 能做什么

- **Pod 故障诊断**：排查 Pending、镜像拉取失败、配置/挂载失败、CrashLoopBackOff、OOMKilled、探针失败、Terminating 卡住、节点失联与驱逐等问题。
- **三维可观测性分析**：结合 Prometheus 指标、Elasticsearch 日志、DeepFlow 流量与 Tempo Span，验证故障假设和业务影响。
- **日常查询**：查询 Pod 状态、节点/集群 CPU、内存及其他已接入 Prometheus 的指标。
- **异常测试环境**：内置 c01～c11 案例，支持手动部署异常负载、验证遥测并发起诊断，便于体验和回归测试；创建资源由测试命令执行，不是诊断 Agent 自动创建。
- **多 Pod、多集群**：每个目标 Pod 独立采证和分析，再汇总报告；支持联邦查询和标准 A2A 接入。
- **证据回查**：保留工具响应、结构化结果和摘要，便于核对报告。修复执行模块已实现，**当前部署配置默认关闭**，报告仍可给出修复建议。

当前默认诊断流程：

```text
/ask → 查询当前 Pod 状态、确定目标
     → 每个 Pod 独立执行：证据规划 → 三维首轮采集 → 自主补查 → RCA 根因分析
     → 按组生成报告并汇总
/query → 直接调用查询工具 → 返回查询结果
```

Agent 负责规划、解释和报告；MCP 负责查询真实数据。Kubernetes 当前状态与 Event 用于确认故障现场，历史事件、Runbook 和正常业务请求用于辅助分析。全局扫描未发现异常时可直接返回概览。

三个项目分工：本仓库 `robusta` 是 Agent，`[mcpstander](../mcpstander/)` 实现工具和数据源访问，`[frountind](../frountind/README.md)` 是可选的聊天前端。Runbook 提供调查指导，不是现场证据，也不保证模型每次都能得到正确根因。

## 部署



### 1. 准备依赖

需要可访问目标集群的 `kubectl`、可用镜像仓库、LLM 服务，以及能为 Agent 的 20 GiB PVC 提供存储的默认 StorageClass 或匹配 PV。自行构建镜像时需要 Docker。


| 组件                                    | 用途与接入要求                                                 |
| ------------------------------------- | ------------------------------------------------------- |
| 本仓库                                   | FastAPI + LangGraph 诊断服务；默认同 Pod 部署 A2A Adapter         |
| [mcpstander](../mcpstander/README.md) | MCP 工具服务；默认部署在 `mcp` namespace                          |
| Prometheus                            | 抓取 kube-state-metrics、kubelet/cAdvisor；业务指标需额外配置抓取      |
| Filebeat + Elasticsearch              | 采集容器日志并保留 namespace、Pod、容器等 Kubernetes 元数据，建议保留 Pod UID |
| DeepFlow + ClickHouse                 | 采集目标 Pod 的真实 L7 流量；查询 `flow_log.l7_flow_log`            |
| Tempo + OTLP Collector                | 保存应用上报的 Span；完整应用链路需要埋点和 trace context 传播               |
| 前端（可选）                                | `frountind` 连接 Agent HTTP/SSE 接口，也可直接使用 curl            |


**MCP 查询已有遥测，不负责安装采集器或生成业务数据。** 先部署可观测性后端并确认数据进入，再部署 MCP 和 Agent。已有平台可直接复用；本仓库不包含这些后端的安装 Chart。

### 2. 配置并部署 MCP

在同级的 `mcpstander` 目录修改 `deploy/configmap.yaml`。当前 Agent 主用 `aiops-observability-query`（端口 `8100`），通用 Prometheus 查询使用 `8095`。


| MCP 配置项                                                         | 需要核对的内容                                                                                         |
| --------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `PROMETHEUS_URL`                                                | 当前清单为 `http://observability-prometheus.monitor.svc:9090`；query 服务和通用 Prometheus 服务均需配置          |
| `AIOPS_ES_EXEC_NAMESPACE` / `AIOPS_ES_SECRET_NAMESPACE`         | ES Pod 与凭据 Secret 所在 namespace，当前清单为 `monitor`                                                  |
| `AIOPS_ES_EXEC_POD` / `AIOPS_ES_SECRET_NAME`                    | 默认 `elasticsearch-master-0` / `elasticsearch-master-credentials`；Secret 含 `username`、`password` |
| `AIOPS_ES_INDEX`                                                | 默认 `filebeat-*`，按实际日志索引修改                                                                       |
| `AIOPS_CLICKHOUSE_EXEC_NAMESPACE` / `AIOPS_CLICKHOUSE_EXEC_POD` | 当前 namespace 为 `monitor`，默认 Pod 为 `observability-clickhouse-0`                                  |
| `AIOPS_TEMPO_EXEC_NAMESPACE` / `AIOPS_TEMPO_EXEC_SELECTOR`      | 当前 namespace 为 `monitor`，默认 selector 为 `app=lgtm`                                               |


当前默认通过 `kubectl exec` 进入 ES、ClickHouse、Tempo 所在 Pod 查询后端；修改后端 namespace 时，要同步修改 MCP 的 `deploy/rbac.yaml` 中对应 Role/RoleBinding。ES/ClickHouse 也有直连模式，配置入口见 [MCP RuntimeConfig](../mcpstander/servers/aiops_observability/config.py)。

当前 MCP RBAC 对集群资源授予 `get/list/watch`，另外仅在 `monitor` 授予 `pods/exec: create`，用于进入**已有后端 Pod**查询，并非授予 `pods: create`。不要为禁止创建临时 Pod 而同时撤销采集所需的 exec。exec 本身可以执行命令，仍应限制工具暴露、后端身份和权限；关闭修复流程也不等于所有工具天然只读。

```bash
cd ../mcpstander
# 先配置后端地址、Pod/Secret 名称和镜像地址
make deploy
# 修改 MCP 配置后的更新
make reload
```



### 3. 配置并部署 Agent

回到本仓库，按实际环境修改：


| 文件                                                           | 配置内容                                                                               |
| ------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| `deploy/secrets/core.yaml`                                   | `LLM_API_KEY`、`LLM_MODEL`、`LLM_API_BASE`、`MODEL_CONTEXT_WINDOW`；可选 `A2A_API_TOKEN` |
| [deploy/configmap/config.yaml](deploy/configmap/config.yaml) | MCP SSE 地址、工作流、语言、联邦子集群；单集群设置 `federation.enabled: false`                          |
| [deploy/k8s-simple.yaml](deploy/k8s-simple.yaml)             | 主服务/A2A/initContainer 镜像、资源、PVC、NodePort                                           |
| [Makefile](Makefile) / [VERSION](VERSION)                    | 构建推送仓库与镜像版本，需与部署清单的镜像前缀一致                                                          |


LLM 需支持工具调用；`MODEL_CONTEXT_WINDOW` 填模型实际上下文容量。Secret 使用 `aiops` namespace、名称 `aiops-secret`，通过 `stringData` 填写上述配置；新环境缺少本地 Secret 文件时需先创建，勿提交真实凭据。

默认 MCP 地址采用集群 DNS，例如 `http://mcp-server-manager.mcp.svc.cluster.local:8100/sse`。按此配置部署时，Agent 与 MCP 位于同一集群；跨集群接入需改成可达地址，并确认 MCP 查询的是目标集群。

```bash

#部署mcp服务
下载mcp服务资源：git clone http://10.2.0.86/wanghuhu/mcpstander.git
cd mcpstander

# 部署mcp服务
make deploy

# 部署aiops服
下载aiops资源：git clone ssh://git@10.2.0.86:9922/wanghuhu/holmegpt-agent.git

cd holmegpt-agent

make deploy

aiops支持部署测试用case
可在aiops的项目目录下执行以下命令。

# 部署一个异常，例如 c08 OOMKilled
make case-deploy CASE=c08

  常用 Case：

  c01  Pending / FailedScheduling
  c02  ImagePullBackOff
  c03  FailedMount
  c04  CreateContainerConfigError
  c05  FailedCreatePodSandBox
  c06  CrashLoopBackOff / exit 2
  c07  配置错误 / HTTP 500 / Trace
  c08  OOMKilled / exit 137
  c09  Running / Ready=False / HTTP 503
  c10  Liveness 失败 / 重启
  c11  Terminating / finalizer 卡死

# (可选)部署前端服务
下载前端frount资源：git clone ssh://git@10.2.0.86:9922/wanghuhu/aiops-frount.git
cd aiops-frount

make  deploy
```

`make deploy` 部署主服务及 A2A sidecar，不构建镜像。代码升级时先更新 `VERSION`，在相应仓库运行 `make build push`，再部署；Agent 会同时构建/推送主服务与 A2A 两个镜像。

可选前端：在 `../frountind` 核对镜像与 `nginx.conf` 的后端地址后执行 `make deploy`，默认访问 `http://<node-ip>:30081`；修改前端代码需先 `make build push`。Agent API 为 `:30800`，A2A 为 `:30801`，不要混用。生产环境应通过鉴权网关、TLS 和网络访问控制接入，不要直接将诊断接口及工具结果暴露到公网。

多集群：每个集群部署自己的 MCP/Agent；主集群配置 `federation.sub_agents` 后执行 `make deploy-master`，子集群执行 `make deploy-slave`。这两个目标会修改本地 federation 开关；标准 A2A 的配置和调用见 [A2A 指南](docs/a2a-server.md)。

### 4. 验证服务

```bash
kubectl get pods,svc -n mcp
kubectl get pods,svc,pvc -n aiops
kubectl port-forward -n aiops svc/aiops-copilot 8000:8000 8001:8001
```

在另一终端执行：

```bash
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/api/v1/mcp/status
curl -fsS http://127.0.0.1:8000/tools/detail
curl -fsS http://127.0.0.1:8001/.well-known/agent-card.json
```

确认工具列表包含 `execute_pod_promql`、`query_pod_logs`、`query_pod_tracing`。健康检查只验证服务入口，三维后端是否可用还需通过一次实际诊断验证。

## 使用

以下沿用端口转发地址；直接访问时替换为 `http://<node-ip>:30800`。

```bash
# 集群级诊断
curl -N -G http://127.0.0.1:8000/ask \
  --data-urlencode 'q=我的集群有什么问题？'

# 指定现场和调查目的，有助于模型选择合适的采证条件
curl -N -G http://127.0.0.1:8000/ask \
  --data-urlencode 'q=请诊断 production 命名空间的 api-xxx Pod，结合最近30分钟的内存趋势、重启、日志和请求链路分析原因。'

# 日常指标查询
curl -N -G http://127.0.0.1:8000/query \
  --data-urlencode 'q=各节点当前 CPU 和内存使用率是多少？'
```

`/ask`、`/query` 默认返回文本流；加 `--data-urlencode 'format=sse'` 获取前端事件流，`stream=false` 获取非流式结果。POST 使用表单参数 `q`，不是 JSON 请求体。


| 入口                                                  | 用途                             |
| --------------------------------------------------- | ------------------------------ |
| `/ask` / `/query`                                   | 故障诊断 / 轻量查询                    |
| `/federation/ask` / `/federation/query`             | 多集群广播查询                        |
| `/federation/ask/v2` / `/federation/query/v2`       | 主 Agent 选择子集群查询；与标准 A2A 协议入口分开 |
| `/reports`、`/reports/{filename}`                    | 查看已保存的报告                       |
| `:30801/.well-known/agent-card.json`、`POST :30801/` | 标准 A2A 发现与 JSON-RPC 调用         |




## 本次更新：三维可观测性采集



### MCP 工具如何设计

当前默认启用 **自主组合查询**（`observability_mode: autonomous`）。模型提供“要验证什么”以及查询条件，工具负责实体校验、构造查询、访问后端和返回带来源的事实。旧 `collect_aiops_case` 粗粒度接口和 fine 工具仍保留，但 Agent 默认不启用。

与预设场景采集相比，当前 `8100` 接口不按 c01～c11 或故障名称选择固定查询：**模型决定调查问题，MCP 执行有范围约束的真实查询**。本次说明的重点是自主查询、三维首轮采集，以及“查询结果 → 完整 MCP 响应 → 模型摘要”的分层处理，不是新增一个自动判定根因的规则引擎。


| 维度 / 工具                     | 真实数据来源                                               | 模型可选择的查询条件                            |
| --------------------------- | ---------------------------------------------------- | ------------------------------------- |
| Metric：`execute_pod_promql` | Prometheus `/api/v1/query` 或 `/api/v1/query_range`   | PromQL、instant/range、时间窗、step         |
| Logging：`query_pod_logs`    | Elasticsearch `filebeat-*` 日志                        | 容器、关键词、级别、trace_id、时间窗、条数             |
| Tracing：`query_pod_tracing` | DeepFlow ClickHouse L7 Flow；按 trace_id 补查 Tempo Span | 入站/出站、协议、响应码、最小时延、对端 IP、请求路径、trace_id |
| 辅助：`query_pod_topology`     | 实时 Kubernetes 对象关系                                   | 目标 Pod 的控制器、Service selector、节点和容器关系  |


工具共同要求精确的 `namespace`、`pod`、`purpose`，可传 `pod_uid` 防止同名 Pod 重建后串用数据。PromQL 每个向量选择器必须包含精确 namespace/pod；日志优先匹配 UID，退回名称和时间窗时标明身份限制；DeepFlow 按 Pod IP 和时间窗约束查询。Flow 与应用 Span 分开保留，只有相同有效 `trace_id` 才能建立对应关联。

**为什么 Logs / Tracing 不需要模型写查询语言？** 模型传 `keywords`、`response_codes` 等参数，MCP 的 `logs.build_query_body` 组合时间、实体与关键词过滤生成 ES DSL；`tracing.build_deepflow_sql` 组合目标 Pod IP、方向、路径、响应码生成 SQL。模型仍需选择有诊断价值的条件，但不用自行处理后端字段兼容与 SQL 拼接。`execute_pod_promql` 则验证作用域后将模型提供的表达式提交给 Prometheus，不替模型选择指标。

### 数据怎样进入报告

1. **确定目标**：查询 Kubernetes 当前状态，将目标拆成独立 Pod 诊断任务；单 Pod 与多 Pod 使用同一套采证和 RCA 流程。
2. **计划与首轮采集**：当前 `planning_mode: structured` 单独调用模型生成 `EvidencePlanOutput` 并做结构校验，再将整理后的计划通过 `# 既有 evidence_plan` 注入 Evidence 执行阶段的用户消息。自主模式下未获得有效计划时，代码可使用最小 Pod Describe 兜底计划；因此归档中的计划不一定全部来自模型。代码在 ReAct 前执行三维首轮查询，缺少相应查询时补通用基线：Pod phase/等待原因/上次终止原因/重启快照、最近 30 分钟日志与 Flow/Span（默认各最多 20 条）。Topology 可用于补查，不属于代码强制执行的三维基线。
3. **按问题补查**：模型看到真实结果后决定换 PromQL、查询趋势、过滤错误日志、追踪某个请求等。基线不是按故障类型写死的完整排障流程，也不保证第一轮就取得决定性证据。
4. **完整返回与归档**：MCP 在查询限额内完整序列化结果，已取消旧的最终 6 KiB 响应裁剪。Agent 先保存原始 MCP 响应，再规范化、去重、选择代表记录，生成有预算限制的模型摘要；未进入摘要的内容可通过 `read_context_archive` 回查。
5. **分析和展示**：每个 Pod 进行正式 RCA，报告按组汇总真实事实。重复日志聚成相同模式，对数值字段计算 first/last/min/max；相同协议、路径、响应码和端点的 Flow 聚合耗时 min/max，应用 Span 另行保留。

“完整返回”仍受查询窗口和条数约束：Pod 查询窗口最长 120 分钟；PromQL 最多 20 条序列、每序列保留最多 20 个样本，范围查询最多 500 个评估点；日志/链路的 `max_records` 最多 50。指标统计使用后端本次返回的该序列完整采样点，展示点可能抽样；日志和 Flow 汇总仅代表参与聚合的记录。

结果包含来源、实体、时间、查询目的、事实、引用、`coverage`、计数与截断信息。`present` 表示查到了数据；`empty/absent` 表示这次条件下没有数据；`error` 表示查询失败，`partial` 表示仅部分结果可用。**采集成功或三维齐全，不等于根因已证实。** 成功但空的结果不会触发代码级失败重试；模型仍可根据调查目的调整条件补查。

当前配置关闭 RCA 的 Fact Ledger 推理投影和 claim 级发布校验，不能将报告视为逐条通过严格因果校验的结论。复核时应对照原始观察和明确的未知项。

可选 `planning_mode: react_only` 会跳过独立 Plan 模型调用，使用代码基线后由 Evidence 自主调查；它不是当前默认值。Pydantic 校验保证结构可消费，不等于结论的语义与因果关系已验证。

### 如何理解报告中的三维数据

下面摘录的是历史测试中**真实工具归档**的关键字段，不是模拟返回或仅引用 LLM 结论。两组来自不同运行，分别说明诊断价值，不能拼成同一次故障的证据链；重新部署后 Pod 名称、时间和数值会变化。

#### 示例 A：c08 OOMKilled——确认终止原因，观察内存增长行为

Run ID：`142581aaee584211-g1`；目标：`aiops-case-08/workload-5c9c7b6489-wmjhr`。


| 维度 / 工具                       | 真实结果摘录                                                                                                                                       | 诊断价值与边界                                                                                             |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Metric / `execute_pod_promql` | `kube_pod_container_status_last_terminated_reason{container="app",reason="OOMKilled"}=1`；`restarts_total=15`；采样时间 `2026-09-07T17:33:31.822Z` | 目标容器上次终止原因被记录为 OOMKilled，并已有重启。它比仅看退出码 137 更直接；这是状态快照，不是内存峰值或趋势。                                    |
| Logging / `query_pod_logs`    | `message="memory allocation advanced"`、`path="/work"`；20 条按时间排列的日志中 `allocated_mib=10,12,14,…,48`，UTC 时间为 `17:32:11.625–17:32:49.785`（同日）    | 观察到应用记录的分配量持续增加，为内存增长假设提供依据。first=10、last=48、min=10、max=48；这是应用字段，不是容器 RSS，也不能声称“已测到超过 64Mi 的内存峰值”。 |


同次 `kubectl_describe` 还返回 `Reason: OOMKilled` 和 `Limits memory: 64Mi`。这些观测支持“存在 OOM 终止与应用分配增长行为”；要定位泄漏位置、证明实际峰值及超限过程，仍应补充应用容器的内存 range 指标或内核/cgroup 事件。

来源定位：该 Run 归档 `tools/001-evidence-execute_pod_promql.*`、`002-evidence-query_pod_logs.*`、`004-evidence-kubectl_describe.*`；OOM 指标事实 ID 为 `fact-be0455d7f7b6`。

#### 示例 B：c09 NotReady——对齐错误日志、网络请求和应用 Span

Run ID：`54e91f6cd7884be0-g1`；目标：`aiops-case-09/workload-5f4fb9ff45-7b77l`。下列三条共享 `trace_id=11a813a37537d619dac9ad9dd14dd35a`：


| 维度 / 来源                 | 真实结果摘录                                                                                            | 诊断价值与边界                                                                                                       |
| ----------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Logging / Elasticsearch | `message="dependency unavailable"`、`http_status=503`、`path="/work"`；时间 `2026-09-07T20:05:41.040Z` | 应用确实记录了业务请求失败，比只展示一条 200 更能说明影响。但消息本身没有确定哪个依赖出了什么故障。                                                          |
| Tracing / DeepFlow      | `HTTP GET /work`、`response_code=503`、`duration_us=10129`                                          | 网络侧也观察到了错误响应；本条耗时为 **10.129 ms**，不是延迟百分位，也不能仅凭它判断超时。                                                          |
| Tracing / Tempo         | Span `GET /work`，`http.response.status_code=503`；开始时间 `2026-09-07T20:05:41.039542Z`               | 与日志/Flow 有相同 trace ID 的应用 Span 可辅助核对同一链路；此次返回标为 `related_context`，Flow 与 Span 的 ID、观测范围仍需分别核对，不能据此宣称完整调用链已采齐。 |


同次 Kubernetes Describe 返回 `Readiness: /ready` 和 `Readiness probe failed … statuscode: 503`，用于确认探针失败。上表证明的是 `/work` **业务请求失败**，不能替代 `/ready` 的探针证据。DeepFlow 原始时间文本未带时区，跨源时间比较应先核对时区，不直接比较字符串。

来源定位：该 Run 归档 `tools/002-evidence-query_pod_logs.*`、`003-evidence-query_pod_tracing.*`、`004-evidence-kubectl_describe.*`；日志事实 ID 为 `fact-e3724443a973`。归档路径读法见[日志与归档](#日志归档与-langfuse)。历史文件属于原测试环境，不随源码克隆自动获得。

这些数值的来源链路是：**K8s 状态 → kube-state-metrics → Prometheus**；**应用 stdout JSON → Filebeat → ES**；**真实网络请求 → DeepFlow → ClickHouse**。有埋点时，应用另外通过 OTLP 上报 Span 到 Tempo。

正常结果也有价值，但解释范围不同：`restarts_total=0` 只是该采样点的计数；`allocated_mib=0` 不代表容器内存为 0；`/work=200` 不代表所有接口健康；Flow 耗时 min/max 只代表所返回记录，不是 P95/P99。上面的例子展示工具能够提供的诊断信息，**不是承诺每次 Agent 都会采到相同证据**。

其中 `/work` 和 `allocated_mib` 来自本仓库的[测试应用](test/pod-anomaly-cases/base/telemetry-app/app-configmap.yaml)：`allocated_mib` 记录测试程序累计保留的分配量，主要在 `oom_growth` 模式递增。生产应用是否有该字段取决于自身日志，不是 MCP 自造的指标。报告中的 `http_status: 200` 是业务日志字段；工具 `query.http_status` 则可能是后端查询 HTTP 状态，两者不能混用。

保留正常值是为了判断影响范围。例如 Pod 已进入 Terminating，而部分 `/work` 仍成功，说明删除状态与业务进程停止并非同步；应继续看 `deletionTimestamp`、finalizer 和控制器，而不能因为 HTTP 200 就判定 Pod 健康。OOM 调查则应补充内存趋势、资源 limit 与 `OOMKilled` 终态；重启次数和成功请求本身不能证明内存耗尽。

对于 c10，`/work` **返回 200 与** `/health` **探针返回 500 可以同时成立**，它们不是同一个接口。应核对 `Liveness probe failed` 和 `Container ... failed liveness probe, will be restarted` 事件来确认重启机制；退出码 137 仅表示 SIGKILL，不能单独推出 OOM。基础采集返回正常业务请求，可能只是窗口内这些记录被选中，需要围绕故障接口继续补查。

跨维度分析先对齐 **Pod/容器身份与时间窗**，日志和 Span/Flow 的同请求关联再核对 **trace_id**。不同 trace_id 的两个 200 可以各自作为观察事实，不能拼成同一条调用链。容器尚未启动的镜像、调度或配置故障，缺少应用日志/Trace 是合理结果，应以 K8s 状态与事件继续调查。

### 还能查询哪些 PromQL

**可以自主构造 PromQL，不限于重启次数。** `/ask` 的 Pod 诊断使用 `execute_pod_promql`，支持聚合、`rate`、`increase`、即时与范围查询；表达式仍须满足精确 Pod 范围和时间限制。实际可用指标取决于 Prometheus 已抓取的 exporter 和标签。

以下将 `production`、`api-xxx`、`app` 替换为实际 namespace、Pod、容器：


| 调查目的           | PromQL 示例                                                                                                                                                                                                     | 读法                                                          |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| 最近 30 分钟重启增量   | `increase(kube_pod_container_status_restarts_total{namespace="production",pod="api-xxx",container="app"}[30m])`                                                                                               | 窗口计数增量，可能因外推为小数；不等同于当前累计值                                   |
| 内存工作集趋势        | `container_memory_working_set_bytes{namespace="production",pod="api-xxx",container="app"}`                                                                                                                    | 使用 range 查询观察变化，bytes ÷ 1048576 为 MiB；与 Pod 配置中的内存 limit 对照 |
| 最近 5 分钟 CPU 用量 | `rate(container_cpu_usage_seconds_total{namespace="production",pod="api-xxx",container="app"}[5m])`                                                                                                           | 单位为 CPU 核，0.5 表示约半核，不是节点 CPU 百分比                            |
| CPU 限流比例       | `rate(container_cpu_cfs_throttled_periods_total{namespace="production",pod="api-xxx",container="app"}[5m]) / rate(container_cpu_cfs_periods_total{namespace="production",pod="api-xxx",container="app"}[5m])` | 被限流周期占比，需结合 CPU limit 和业务延迟解释                               |
| 容器是否就绪         | `kube_pod_container_status_ready{namespace="production",pod="api-xxx",container="app"}`                                                                                                                       | 0/1 状态，可与探针失败事件及对应探针路径的请求对照                                 |


一次 MCP 范围查询参数示例（供 MCP 客户端调用，**不是** `/ask` 的 HTTP JSON body）：

```json
{
  "namespace": "production",
  "pod": "api-xxx",
  "purpose": "检查异常前30分钟应用容器内存是否持续增长",
  "promql": "container_memory_working_set_bytes{namespace=\"production\",pod=\"api-xxx\",container=\"app\"}",
  "query_type": "range",
  "window_minutes": 30,
  "step": "30s"
}
```

即时查询普通 gauge 只有一个快照，不能据此声称有增长趋势；`increase(...[30m])` 等表达式虽然可以即时执行，但计算本身已引用历史样本。查询返回空数组也不等于数值 0，应检查指标名称、标签、抓取配置和时间窗。

节点/集群查询走 `/query`，使用通用 `execute_prometheus_instant_query`、`execute_prometheus_range_query`，还可用 `get_metric_names`、`get_metric_metadata`、`get_label_values`、`get_series` 发现指标和标签。应用 QPS、错误率、延迟直方图同样可以查询，前提是应用已暴露并被抓取；Pod 工具要求这些序列带精确的 `namespace`、`pod` 标签。

### 日志和链路如何继续补查

以下是 MCP 工具参数示例，替换目标后通过 MCP 客户端调用；普通用户在 `/ask` 中表达相同调查目的即可，模型是否采用这些条件需查看实际工具调用。

```json
{
  "namespace": "production", "pod": "api-xxx",
  "purpose": "查找最近30分钟健康检查接口相关的应用日志",
  "window_minutes": 30, "keywords": ["/health"],
  "keyword_mode": "phrase", "max_records": 20
}
```

上例用于 `query_pod_logs`；它检索已进入 ES 的日志，不会让未记录探针请求的应用凭空产生日志。链路可以进一步使用 `query_pod_tracing`：

```json
{
  "namespace": "production", "pod": "api-xxx",
  "purpose": "核对健康检查入站请求是否返回500",
  "window_minutes": 30, "direction": "inbound",
  "request_resource": "/health", "response_codes": [500],
  "include_tempo": true, "max_records": 20
}
```

DeepFlow 返回匹配的网络 Flow；发现有效 `trace_id` 时可继续查询 Tempo。`include_tempo: true` 不是“必定得到 Span”：没有有效 trace ID 或应用未埋点时，需看 `source_coverage` 中的未执行/缺失原因。查询出站慢调用则可改用 `direction: outbound`、`min_duration_us`、`peer_ip` 等条件。**支持丰富查询，不等于模型每次都会主动构造合适的查询。**

## 验证与排查



### 创建异常测试环境

本仓库支持自己创建可复现的异常 Pod，再观察三维数据和 Agent 诊断。**仅在专用测试集群执行**：命令使用当前 kubectl context，操作者需有资源创建/删除权限。先完成前述可观测平台部署；Case 只创建测试负载，不会安装 Prometheus、ES、DeepFlow 或 Tempo。

```bash
# 1. 确认目标集群，查看可用异常
kubectl config current-context
make case-list

# 2. 部署一个异常，例如 c08 OOMKilled（在 robusta 根目录运行）
make case-deploy CASE=c08

# 3. 等待故障与真实遥测成立，不要把刚创建成功当作故障已复现
make case-validate CASE=c08
kubectl get pods -n aiops-case-08

# 4. 对该案例诊断，输出到 reports/case-c08-*.txt
make case-ask CASE=c08

# 5. 验证结束后，仅清理本次创建的 c08 专用 namespace
kubectl delete namespace aiops-case-08
```

也可以部署后在前端直接问“我的集群有什么问题？”，或使用上面的 `/ask` 命令做集群级诊断；`make case-ask` 是定向到该 Case namespace 的便捷入口。运行态案例通过测试应用与流量生成器产生真实日志、指标和 Span，结果随采集时机变化。

其他案例可替换 `CASE=cNN`：c01 调度、c02 镜像、c03 挂载、c04 配置、c05 Sandbox、c06 运行时退出、c07 应用配置退出、c09 Readiness、c10 Liveness、c11 删除卡住。先核对案例中的测试镜像、遥测后端地址和验证器配置；c05 需要 Multus，c11 还需在产生流量后触发删除，不能只 apply。

需要同时体验全部 c01～c11 时，可运行 `make case-deploy-errors`（含 c11 删除触发，**不执行遥测验收**）；`make case-deploy-all` 会部署全部非破坏性案例并执行验收。确认这些 namespace 都属于测试资源后，再用 `make case-clean` 清理全部案例；它会先释放 c11 finalizer，并删除 `aiops-case-01`～`aiops-case-11`，不要用于存有其他资源的同名 namespace。

案例说明见 [Pod 异常实验库](test/pod-anomaly-cases/README.md)，批量盲测、断点续跑与评分见 [E2E 质量测试](test/aiops_quality_e2e/README.md)。测试应用产生真实流量和遥测；评分器的标准答案不注入诊断 Agent。

另有 17 个[同状态、不同根因的扩展 Case](test/pod-anomaly-cases/variants/README.md)：
`make case-list-variants` 查看，`make case-deploy CASE=c03-secret` 部署，
`make case-validate CASE=c03-secret` 验证故障，`make case-clean CASE=c03-secret` 单独清理。
质量脚本用 `--scenario expanded` 测试基础与变体，用 `--combine` 同时部署选中的多个 Case。
`make case-validate` 只检查故障状态及具体原因，不代表三维遥测验收通过。

### 日志、归档与 Langfuse

Agent 日志：`kubectl logs -n aiops deployment/aiops-copilot -c aiops-copilot -f`。部署清单将报告写入 PVC，**容器内**目录如下；宿主机物理路径由存储系统决定，不要照搬其他环境的 `/data/redis/...`。

```text
/tmp/aiops/reports/
├─ *.md                           最终报告，/reports 接口列出这些文件
└─ context_archives/
   ├─ <run_id>/                   主流程：Layer、汇总报告
   └─ <run_id>-g1/                第一个 Pod 诊断组；多组还有 g2、g3
      ├─ tools/*.raw.txt          Agent 收到的原始 MCP 响应（仍受源端查询限额约束）
      ├─ tools/*.structured.json  标准化结果、canonical facts 与覆盖元数据
      ├─ tools/*.summary.txt      提供给模型的工具摘要
      ├─ node_inputs/            节点归档输入
      ├─ node_outputs/           Evidence/RCA 输出；evidence.full.json 含实际计划
      └─ budget/                 上下文预算、压缩与 guard 记录
```

前端工具卡片展开的是工具摘要，`raw_ref`、`structured_ref`、`summary_ref` 指向归档，不是浏览器可直接打开的 HTTP URL。相同 JSON 外壳表示统一观察合同，不表示三个工具查到了相同数据；对照 `source_system`、`evidence`、时间、`coverage`、计数与截断字段。

启用 Langfuse 上报后，主 Run ID 看定位/汇总，`<run_id>-g1` 看该组采证/RCA；计划调用查 `workflow-evidence_plan`，执行阶段模型 Input 中搜索 `既有 evidence_plan`。两条 Session 属于同一次诊断，不是重复运行。注意 `node_inputs/evidence.input.json` 记录在规划前，不是注入既有计划后的完整执行消息。Fact ID 是回查标识，不是“已验证正确”的标志。


| 现象              | 优先检查                                                           |
| --------------- | -------------------------------------------------------------- |
| 工具列表缺少三维查询工具    | Agent 的 `mcp_servers` 开关、MCP `8100/sse` 连通性及部署版本               |
| Metric 返回 empty | kube-state-metrics/cAdvisor 抓取、指标名与 namespace/pod/container 标签 |
| 日志/链路查询报错       | 后端 Pod/Secret/selector、`monitor` namespace 的 exec RBAC、ES 索引   |
| 日志/链路查成功但为空     | 容器是否启动、是否有流量、采集延迟、时间窗、DeepFlow 覆盖和应用埋点                         |
| 有三维数据但根因仍不清楚    | 数据是否回答本次诊断目的；补查故障时段、具体容器/接口及决定性 K8s 事件                         |


维护者源码入口：[工作流路由](app/core/workflow/graph.py)、[三维采证](app/core/workflow/nodes/evidence_collector.py)、[模型摘要投影](app/core/context/observability_projection.py)、[报告聚合](app/core/workflow/nodes/conclusion_formatter.py)、[MCP 工具参数定义](../mcpstander/servers/holmes_tools/aiops_observability_query.py)、[MCP 查询实现](../mcpstander/servers/aiops_observability/query/)。
