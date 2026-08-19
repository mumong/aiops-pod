# 当前 AIOps 诊断全链路架构

> 事实基线：2026-08-14 当前工作树与当前 Kubernetes 运行态。本文只描述当前实现。关键运行文件已在 `aiops/aiops-copilot` Pod 内与工作树做 SHA-256 核对：`executor.py`、`parallel_evidence.py`、`graph.py`、`conclusion_formatter.py`、`evidence_collector.py`、`observation.py` 均一致。Pod 镜像为 `aiops-copilot:11.0.106`。工作树原本已包含业务代码、测试和部署文件的未提交改动；本文不把这些改动写回或清理。

## 图集

1. [部署拓扑](architecture/current-aiops-diagnosis/01-deployment-topology.html)
2. [`/ask` 请求时序](architecture/current-aiops-diagnosis/02-request-sequence.html)
3. [工作流路由与并行分支](architecture/current-aiops-diagnosis/03-workflow-routing.html)
4. [工具 Observation 与 Fact Ledger 数据流](architecture/current-aiops-diagnosis/04-observation-dataflow.html)
5. [上下文预算与压缩生命周期](architecture/current-aiops-diagnosis/05-context-budget-lifecycle.html)
6. [真实运行 c04/c08/c09 证据边界](architecture/current-aiops-diagnosis/06-runtime-cases.html)

六张图均是自包含 HTML：CSS、SVG 和 JavaScript 内联，浏览器可直接打开；右上角提供明暗主题切换，以及 PNG、JPEG、WebP、SVG 导出。

## 1. 当前部署拓扑与边界

当前集群中，Frontend、Robusta 和 MCP Stander 分别由独立 Deployment 提供：

- `aiops-copilot-frontend`：单副本，容器端口 80，NodePort Service 暴露为 30081。React 入口把 `apiBase` 固定为 `/api`（`frountind/src/App.tsx:4-10`）。
- `aiops-copilot`：单副本，容器端口 8000，Service NodePort 为 30800。配置和 runbook 由 ConfigMap 只读挂载；报告与 `context_archives` 写入 `aiops-reports-pvc`，容器内根目录是 `/tmp/aiops/reports`。
- `mcp-server-manager`：单副本，ClusterIP Service 暴露 8088–8100 的多个 MCP SSE 端口。Robusta 当前配置通过集群 DNS `mcp-server-manager.mcp.svc.cluster.local` 访问这些端口，其中 AIOps 可观测查询服务使用 8100。
- Kubernetes API、Prometheus、Elasticsearch/Filebeat、DeepFlow/ClickHouse、Tempo/LGTM 是工具的数据源。MCP Stander 在服务端执行有界查询；LLM 不直接连接这些后端。
- LLM 是 Robusta 的外部模型依赖。API key 只从 Secret/环境或配置装载到进程，本文和图中不展示值（`app/core/service.py:310-346`）。

运行态还给出两个重要约束：`MODEL_CONTEXT_WINDOW=32000`，`AIOPS_CONTEXT_ARCHIVE_ROOT=/tmp/aiops/reports/context_archives`。文档中的代码行号指当前工作树；Kubernetes 对象、镜像、ConfigMap 值和 run archive 指当前部署运行态。二者已对关键诊断源文件做哈希一致性核对，但其他未核对文件仍按各自事实边界理解。

## 2. `/ask` 从浏览器到报告

### 2.1 浏览器请求与 SSE 解析

ChatWidget 以 GET 请求 `${apiBase}/ask`，把问题和模式编码为查询参数（`frountind/src/components/aiops-chat/ChatWidget.tsx:430-457`）。`useSSE` 使用 `fetch` 和 `ReadableStream`，逐行解析 `event:`/`data:`，空行触发一次事件分发；非 `text/event-stream` 响应退化为普通文本流（`frountind/src/hooks/useSSE.ts:30-116`）。

前端按事件类型更新界面：

- `run_start` 绑定 run_id；
- `node_start`/`node_complete` 建立节点卡片和 handoff 摘要；
- `thinking` 下的 `ai_token`、`ai_message`、`tool_start`、`tool_result` 更新推理和工具卡片；
- `heartbeat` 只保活，不改变诊断内容；
- `final` 把 `answer` 设为最终答案并完成消息；
- `error` 显示失败状态（`ChatWidget.tsx:181-379`）。

完成态的 `finalAnswer` 交给 MarkdownReport 渲染；流式期间先按纯文本展示（`frountind/src/components/aiops-chat/BotMessage.tsx:68-76`）。

并行工具卡片的归组不是靠工具名或到达顺序猜测。组内 `_ScopedParallelEventQueue` 写入的 `parallel_context={group_id,entities}` 是后端权威身份；`stream_contract.py` 只从该对象取 `group_id`，再把工具参数或 structured entity 与该组实体求交，投影为 SSE `evidence_context`。前端优先用 `evidence_context.group_id` 选组；结束事件用 `tool_call_id + group_id` 匹配 pending tool（只有唯一 call-id 候选且候选没有组身份时才兼容匹配）。没有 group_id 时，才允许按实体在全部组中“恰好唯一命中”回退；零命中或多组命中一律进入 `unassignedResults`，绝不推断歧义归属（`stream_contract.py:66-135`；`parallelEvidenceModel.ts:223-335`）。当前部署 Frontend 镜像 `local-20260814042717` 的 bundle 已只读确认包含 `evidence_context`、`group_id`、`tool_call_id` 和 `unassignedResults`，所以这不是仅存在于未部署源码的行为。

### 2.2 FastAPI 与 HolmesService

GET/POST `/ask` 都修正可能的双重编码并进入 `_stream_response` 或同步收集路径。默认 `stream=true`；只有 `format=sse` 才返回 `text/event-stream`，否则是文本流（`app/api/routes.py:53-146,632-675`）。`/ask` 强制覆盖为 `query_mode=full` 且启用 layer、evidence、rca、conclusion（`routes.py:677-682`）。客户端断开会设置 cancel event。

HolmesService 初始化时加载 YAML、runbook、AICall、MCP 工具和内置工具。MCP 工具从 `mcp_servers` 配置并发加载，随后和内置工具合并；两个不可用的 top 工具被移除（`app/core/service.py:276-465`）。每个请求建立独立 AICall，避免并发共享模型客户端；WorkflowExecutor 接收同一请求的工具集合（`service.py:488-512,839-879`）。

### 2.3 WorkflowExecutor 与 SSE

Executor 每次请求生成 16 位 run_id，深拷贝 workflow 配置、构图、把 run_id、cancel event、AICall、工具和配置注入每个节点（`app/core/workflow/executor.py:160-230`）。LangGraph 在后台线程运行，容量 500 的 Queue 同时承载节点生命周期、LangGraph state update 与 thinking；前台生成器每 0.3 秒轮询，并在节点运行而 15 秒无事件时发 heartbeat（`executor.py:288-355`）。

每个事件带 run_id、单调 seq 和时间戳。工具 thinking 会经 `project_parallel_tool_event` 投影并附上组身份、实体、归档引用和语义成功状态（`executor.py:423-496`；`app/core/workflow/stream_contract.py`）。节点结束时生成有限 state snapshot 和 handoff archive。工作流完成后，conclusion 加上性能/质量统计，写报告文件，发送 `final`，最后发送 `run_end`（`executor.py:601-673,791-800`）。

## 3. 当前工作流路由

标准节点顺序是 `layer → evidence → rca → conclusion`，但图在运行时有条件路由（`app/core/workflow/graph.py:96-200`）：

- HEALTHY：layer 直接到 conclusion。
- QUERY direct：layer 直接到 conclusion；`/ask` 使用 full，不走此捷径。
- 一般异常：layer → evidence → rca → conclusion。
- 多异常：当 issue group 数量严格大于阈值时，layer → parallel_evidence → conclusion。当前 ConfigMap 为 `threshold=2`、`max_concurrency=3`，因此 3 组会并发；该分支把每组结构化诊断视作组级 RCA，明确跳过全局 RCA（`graph.py:137-163,203-234`）。

### 3.1 layer：发现、归一化与结构化 handoff

layer 使用 ReAct 工具循环识别查询类型、当前异常 Pod、异常族和 runbook。LLM/工具给出的结果经 `LayerOutput` 和 `LayerHandoff` Pydantic 合同归一化（`app/core/workflow/schemas.py:179-235`）。当前 handoff 的核心字段是：

- `layer/layers/derived_layer/confidence/primary_problem`；
- `abnormal_pods`：namespace、name、status；
- `issue_groups`/`abnormal_groups`：group_id、status_keywords、pod_abnormal_type、entities、possible_scenarios；
- `current_abnormal_summary`：来源、状态计数、选中原始行及 raw/structured/summary 引用；
- `active_entities/active_signals/matched_runbooks/must_verify/do_not_change`。

完整模型分析写 `layer/full_analysis.md`，结构化交接写 `layer/handoff.json`；WorkflowState 只保留紧凑 handoff 和引用，`layer_full_analysis` 已是兼容字段（`app/core/context/archive.py:63-68`；`app/core/workflow/state.py:30-48`）。layer 的模型文本超过 30000 字时会先压缩再提取结构化结果（`app/core/workflow/nodes/layer_classifier.py:1556-1563,1684-1688`）。

### 3.2 evidence：计划、工具执行与语义评价

单上下文 evidence 接收原问题和 layer_handoff。它先生成 `EvidencePlanOutput`：每项必须有 id、description、level、tool、command、tool_args、purpose、target_scope 和 acceptable_tools（`schemas.py:328-347`）。计划约束工具意图与统计，但实际 ReAct 仍可依据新结果补证；调用参数由模型从 prompt、handoff、工具 JSON Schema 和先前 Observation 决定，工具实现只校验/约束，不按故障类型替模型选参数。

当前 autonomous observability 首轮门控会围绕每个已确认 Pod 建立 metrics、logging、tracing、topology 维度项。Pod 目标先从 handoff 绑定为精确 namespace/name；可信 Kubernetes 结果可补入 pod_uid，避免同名 Pod 生命周期复用（`app/core/workflow/nodes/evidence_collector.py:2233-2491,3582-3821`）。

采集完成后，evidence 分开计算：计划匹配、实际执行数、环境证据完整度、四维覆盖、source coverage、detail retrieval、diagnostic sufficiency、缺失原因和 early stop。`collected=true` 只表示一次结果与计划相符；`coverage=present` 只表示源返回了数据；两者都不等价于 purpose 已回答或因果已证明（`evidence_collector.py:3822-4771,4938-5460`）。最后发布 `EvidenceCollectionOutput`，并生成 `evidence_facts`、conflicts、missing evidence（`schemas.py:486-526`）。

这里有四个当前限制。第一，首轮门控会优先复用模型计划里同 target/tool 的 metrics 项；只有该项缺失时，代码才注入通用 Pod 生命周期 instant PromQL（phase/waiting reason/last terminated reason/restarts）。因此首轮可能是模型选择的 purpose-aware 指标，也可能退化为通用基线，四维门控本身只保证真实尝试；这也解释了 b8 的 c08 取得 memory 趋势而 efa 主要取得 restart/状态指标的不稳定。第二，门控完成后“是否补采、用什么 purpose”留给同一个 ReAct agent，代码没有一个按未回答 purpose 自动生成补采计划的控制器。第三，early stop 按计划中 `critical/important` 项是否 `collected` 判断，而不是按 diagnostic sufficiency；一次语义成功且与计划匹配的结果可能让项目 collected，即使它没有闭合 purpose。第四，评分也是启发式：case metrics 有 highlight 即 0.5，只要任一 highlight 有至少两个样本或异常/阈值关键词即 1.0；单独 AIOps metrics query 若没有 `trend_evaluable=true` 且 `sample_count>=2`，最多 0.4。最终 sufficiency 是各“实体×维度”分数的等权平均，平均值 `>=0.85` 为充分、`>=0.5` 为部分充分，否则不足；它没有按故障 purpose 或维度重要性加权（`evidence_collector.py:1880-2217,3451-3579,4209-4554,4689-4729`）。

### 3.3 parallel_evidence：隔离每组，合并摘要

当组数大于 2，每个组建立独立 EvidenceCollector、scoped handoff、scoped question 和独立归档 run_id `{run_id}-gN`；ThreadPoolExecutor 并发度当前最多 3（`app/core/workflow/nodes/parallel_evidence.py:118-248`）。scoped handoff 只含本组实体，`must_verify` 明确禁止跨组采集（`parallel_evidence.py:258-328`）。实时事件由 scoped queue 写入权威 `parallel_context={group_id,entities}`，再被 SSE 投影。

每组结果包含 `summary`（最多 1600 字）、collection_summary、completeness、完整 evidence_analysis、保留的 tool_result、archive_run_id，以及按实体、按维度聚合的 `dimension_evidence_by_entity`（`parallel_evidence.py:330-383`）。随后另一次 structured LLM 调用生成 `EntityDiagnosisSummary`；其 supporting/contradicting fact_id 会过滤到当前实体实际存在的 ID，没有有效支持则强制“证据不足”与 0 置信度（`parallel_evidence.py:411-485`）。所有结果进入 WorkflowState.group_results。

### 3.4 RCA：单上下文路径的 Fact Ledger 消费者

非并行异常进入 RootCauseAnalyzer。其上下文优先由 compact layer_handoff、Fact Ledger、质量合同和辅助证据组成，总上限 52000 字；handoff 7000、工具上下文 36000、Fact Ledger 24000、质量合同 4000、补充工具 7000、其他辅助区各 3000 字（`app/core/workflow/nodes/root_cause_analyzer.py:48-54,195-280`）。实体身份索引优先保留，再压缩细节（`root_cause_analyzer.py:284-380`）。

RCA 结构化输出包括 diagnostic_status、phenomenon、evidence_inventory、causal_chain、root_cause、supporting/contradicting fact IDs、unknowns、hypotheses、confidence 与 limitations（`schemas.py:561-608`）。输出必须经过 `validate_rca_claims`，引用不属于当前 ledger 或权威范围不足时降级为 inconclusive（`app/core/workflow/fact_contract.py:3275-3471`）。

### 3.5 conclusion：单路径与多组路径不同

单路径 conclusion 选择 layer_handoff、evidence_analysis、rca_analysis 和最终有效 tool events。固定字符封套为 layer 6000、evidence 8000、RCA 8000、tool data 16000；单条工具 1500、最多 24 条；每次可观测查询最多 8 条事实，单事实值最多 500 字（`app/core/workflow/nodes/conclusion_formatter.py:54-68,177-215`）。

多组路径不读取全局 RCA，而把每组 `entity_summaries + dimension_evidence_by_entity` 放入一次 narrative LLM；随后代码确定性拼接每个实体的四维表和逐工具折叠区，避免 LLM 输出长度决定事实是否展示（`conclusion_formatter.py:788-987`）。最终报告仍同时包含模型叙事和确定性卡片，因此二者可能出现语义不一致，阅读时应以结构化事实及其引用为准。

`8192 tokens` 只限制 conclusion 的一次 LLM completion，不限制最终 Markdown 总长度。单路径的 LLM 输入由 layer/evidence/RCA/tool-data 字符封套组装，LLM 返回值本身就是报告；多组路径的 LLM 只生成 narrative，代码随后在 completion 之外追加所有实体卡片、四维事实表、逐工具证据和归档引用。因此多组最终 Markdown 没有全局 token/字符 cap，组数和证据量会继续增加最终文本长度（`conclusion_formatter.py:553-720,788-897`）。

## 4. 工具注册、选择、参数与返回合同

MCP server 的 `list_tools` 返回四个 AIOps query Tool schema，`call_tool` 记录调用、分派 handler，并始终以单个 TextContent 返回 JSON 文本；异常也包装成结构化 error，而不是把异常直接泄漏给 Agent（`mcpstander/servers/aiops_observability_query_server.py:21-66`）。

四个工具的职责和参数决策如下（`mcpstander/servers/holmes_tools/aiops_observability_query.py:27-258`）：

| 工具 | 模型必须决定 | 工具侧硬约束/绑定 |
|---|---|---|
| `execute_pod_promql` | purpose、PromQL、instant/range、时间窗、step | 每个 vector selector 必须精确含 namespace/pod；范围窗最多 120 分钟 |
| `query_pod_logs` | purpose、时间窗、container、keywords/mode、levels、trace_id、fields、max_records | 安全构建 Elasticsearch DSL；优先 pod_uid；最多 50 条 |
| `query_pod_tracing` | purpose、方向、协议、响应码、时延、peer、trace_id、resource/service、是否 Tempo | DeepFlow 保持 Pod IP scope；显式 trace_id 的 Tempo-only 结果标为 related context |
| `query_pod_topology` | purpose 和时间窗 | 只从实时 Kubernetes owner、Service selector、Node、Container 关系构建，不按名字推断 |

所有工具共同要求精确 namespace、pod、purpose，可选 pod_uid。MCP 输入 JSON 最多 4096 bytes，查询元数据（PromQL/ES DSL 等）最多 4096 bytes，最终序列化 TextContent 最多 6144 bytes；所有时间窗以及 PromQL range+offset 均不得超过两小时（`query/common.py:20-24,106-260,360-407`）。超限输入直接返回 `input_budget_exceeded`；输出通过 `_shrink_result_once` 循环缩小：Topology 先别名化/压实体与事实/去重复及低优先级边，再依次裁 correlations、flows、spans、series、嵌套 samples、samples、非保护 facts、长证据字符串，最后才移除仅存 correlation；每步重建投影、Fact Ledger 和 refs。仍超 6144 bytes 时返回 `result_budget_exceeded`，不把后端大对象偷偷当完整结果（`query/common.py:409-472,649-845`；`aiops_observability_query.py:261-283`）。

维度自身还有限额：metrics 最多 20 series、每 series 20 samples、500 evaluation points、PromQL 2000 字；logs 后端取 100、返回最多 50 records、给 agent 最多 8 samples（keywords 8、levels 6）；tracing 最多 50 flows/records、5 traces、agent sample 为 5 flows+3 spans；topology 最多 2 条 owner、1 条 Service、1 条 Container，加 1 条 Node 关系，共 5 条。因而 `truncated=false` 只说明在这些有界合同内没有继续裁剪，不表示观测后端的全量原始数据已返回（`metrics.py:26-29,431-440`；`logs.py:29-32,509-585`；`tracing.py:21-22,475-570`；`topology.py:24-34,288-312`）。返回合同必须含 `ok,status,source_system,dimension,entity,purpose,coverage,directness,query,facts,samples,evidence_refs,truncated,limits`；可附 flows、spans、topology、fact_ledger 和 error。Robusta 缺字段或 canonical Fact Ledger 校验失败时，把该 Observation 标为 `query_parse_failed/coverage=error`（`app/core/context/observation.py:266-467`）。

Pod 身份链是：layer 的 namespace/name → evidence 精确绑定 → Kubernetes 工具确认 UID → observability MCP 用 UID/Pod IP/labels 查询各后端 → 返回 entity 和 evidence refs → Observation/Fact Ledger 再校验 scope。日志样本和 Trace 只有 trace_id 完全相等时才可声明同一请求；只命中同 Pod、同 path 或同 HTTP code 不能替代该条件（`observation.py:837-919`）。

## 5. raw、structured、summary、Fact Ledger 与 State

每次工具返回经过 ObservationProcessor 形成三级表示（`app/core/context/observation.py:108-201`）：

1. `raw`：Robusta 实际收到的 MCP TextContent 字符串或本地工具输出，原样落 `tools/NNN-node-tool.raw.txt`。对 AIOps query，它已经受 MCP 的 6144-byte 返回上限及各维度限额约束，所以只是“Robusta 接收字符串的完整副本”，绝不等同于 Elasticsearch/Prometheus/DeepFlow/Tempo/Kubernetes 后端的全量 raw 数据。
2. `structured`：按工具类型提取的机器可读对象，落 `.structured.json`。AIOps query 保留合同字段和 canonical Fact Ledger。
3. `summary`：重新注入 ReAct message 的有界文本，落 `.summary.txt`。工具事件同时带 raw_ref、structured_ref、summary_ref、semantic_success。

Fact Ledger v1 由 case_id、scope_entity_ids、records、record_count、truncated、source 构成。FactRecord 强制 entity identity、dimension、fact type、attribute/value、source、directness、confidence 和 evidence refs；非 coverage fact 没有 refs 不能通过，related_context 不能是 high confidence（`app/core/workflow/schemas.py:367-428`）。`fact_contract.py` 负责 canonical 化、排序/裁剪、拓扑端点校验、权威 ledger 选择和 RCA claim 校验。

WorkflowState 跨节点传结构化小字段和引用，不把 raw 复制进 state。单路径主要交接 `layer_handoff → evidence_analysis/evidence_facts → rca_analysis → conclusion`；并行路径交接 `layer_handoff → group_results → conclusion`。归档目录另有 `budget/`、`node_inputs/`、`node_outputs/`、`handoff/` 与 `layer/`（`app/core/context/archive.py:41-109`）。

一个当前可见的归档边界是：Executor 的 node snapshot 只对 layer/evidence/rca/conclusion 定义字段，没有 parallel_evidence/group_results 专用 snapshot；因此运行归档中的 `node_outputs/parallel_evidence.output.json` 可为空快照，而 conclusion.input 又实际包含三组结果。`evidence-to-rca.json` 也可能仍显示 0/0；这不能证明并行组没有采集，只说明通用归档投影未覆盖并行 handoff（`executor.py:881-958,990-1037`）。

### 5.1 字段级交接示例与血缘动作

以下都是脱敏后的最小形状；`copied` 表示同义字段原样跨边界，`projected` 表示从更宽对象选择/归一化，`truncated` 表示有界保留，`dropped` 表示该边界明确不携带。

Layer 写入 WorkflowState 的主干（`state.py:16-84`）：

```json
{"question":"诊断异常 Pod","run_id":"run-redacted","layer":"L2","layer_handoff":{"diagnosis_scope":"question_scope","issue_groups":[{"group_id":"g1"}]},"layer_archive_ref":{"handoff_ref":"layer/handoff.json"},"thinking_events":[],"group_results":null}
```

- `question/run_id/layer` copied；`layer_handoff` projected 自 `LayerOutput + 当前异常摘要`；`layer_archive_ref` copied 引用；full tool raw dropped（只在 archive）；后续 `thinking_events` 增量 copied；并行结束前 `group_results` 为空。

LayerHandoff/IssueGroup（`schemas.py:141-235`）：

```json
{"diagnosis_scope":"question_scope","layer":"L2","confidence":0.91,"primary_problem":"3 个 Pod 异常","abnormal_pods":[{"namespace":"case-ns","name":"pod-a","status":"Pending"}],"issue_groups":[{"group_id":"g1","status_keywords":["CreateContainerConfigError"],"pod_abnormal_type":"ConfigBootstrapFail","entities":[{"kind":"Pod","namespace":"case-ns","name":"pod-a"}],"possible_scenarios":[]}],"current_abnormal_summary":{"source":"kubectl","selected_rows":["pod-a Pending"],"raw_ref":"tools/001.raw.txt","structured_ref":"tools/001.structured.json","summary_ref":"tools/001.summary.txt"},"must_verify":["verify current state"],"do_not_change":[]}
```

- identity/status/groups copied 或 schema-normalized；`current_abnormal_summary.selected_rows` projected 且有界，三个 refs copied；完整 layer 模型文本 dropped 到 `layer/full_analysis.md`；Secret 值 dropped/不得写入 handoff。

并行 scoped_handoff（`parallel_evidence.py:258-328`）：

```json
{"diagnosis_scope":"single_group","layer":"L2","confidence":0.91,"primary_problem":"[g1] case-ns/pod-a CreateContainerConfigError","abnormal_pods":[{"namespace":"case-ns","name":"pod-a","status":"CreateContainerConfigError"}],"issue_groups":[{"group_id":"g1","entities":[{"kind":"Pod","namespace":"case-ns","name":"pod-a"}]}],"matched_runbooks":["rb-config"],"must_verify":["只诊断本组实体 case-ns/pod-a"],"current_abnormal_summary":{"source":"parallel_evidence_group_scope","selected_rows":[]}}
```

- layer/confidence、当前 group、matched_runbooks copied；primary_problem/abnormal_pods/current summary projected；其他组、全局 active_signals、原 selected_rows 和 raw dropped；scoped question 另行 projected 追加组目标。

完整 EvidenceCollectionOutput（`schemas.py:486-526`）先作为审计对象写入 `node_outputs/evidence.full.json`：

```json
{"evidence_plan":[{"id":"obs-g1-k8s","level":"critical","tool":"kubectl_describe","purpose":"确认容器状态"}],"tool_results":["Observation summary；full-passthrough 在低压力时可更长"],"tool_data":[{"tool":"kubectl_describe","raw_ref":"tools/001.raw.txt","structured_ref":"tools/001.structured.json","summary_ref":"tools/001.summary.txt"}],"llm_analysis":"bounded analysis","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"diagnostic_sufficiency":0.5,"diagnostic_sufficiency_label":"部分充分","early_stop":{"triggered":true,"required_levels":["critical","important"]}}
```

- plan/statistics/refs projected；`llm_analysis` truncated/bounded；一般 `tool_results` 使用有界 Observation summary，但 `fetch_runbook`、`run_bash_command`、`kubectl_run_image` 在低于 80% 压力时是 full-passthrough，可超过 3000 字；raw/完整 structured dropped（仅 refs 与 tool_data 投影）；`plan_collected` 不从 sufficiency copied，而是按计划匹配独立计算。这个完整对象只保证出现在 full archive，不能当成跨节点 handoff。

发布到 WorkflowState 前，`_publish_evidence_analysis()` 会复制 full payload、明确 `pop("llm_analysis")`，再把剩余对象序列化为 JSON 字符串（`evidence_collector.py:691-716`）：

```json
{"evidence_analysis":"{\"evidence_plan\":[{\"id\":\"obs-g1-k8s\"}],\"tool_results\":[\"Observation summary\"],\"collection_summary\":\"1/1 collected\",\"plan_total\":1,\"plan_collected\":1,\"plan_completeness\":1.0}"}
```

- full archive copied 完整 `llm_analysis`；WorkflowState handoff dropped `llm_analysis`，只 copied 其余字段的紧凑 JSON 字符串。下游如果只读取 `state.evidence_analysis`，看不到完整模型分析，必须显式回读 full archive 才能恢复；当前 parallel_evidence 并未这样回读。

group_result（`parallel_evidence.py:330-383`）：

```json
{"group_id":"g1","entities":[{"kind":"Pod","namespace":"case-ns","name":"pod-a"}],"status_keywords":["CreateContainerConfigError"],"summary":"last ai_message fallback，最多 1600 字","legacy_text_fallback":true,"entity_summaries":[],"dimension_evidence_by_entity":{"case-ns/pod-a":{}},"collection_summary":"1/1 collected","completeness":1.0,"evidence_analysis":"{\"plan_collected\":1}","thinking_events":[{"type":"ai_message","content":"组内分析"},{"type":"tool_result","tool_name":"kubectl_describe"}],"archive_run_id":"run-redacted-g1","error":null}
```

- group identity copied；collection fields projected 自 WorkflowState 中已移除 `llm_analysis` 的 handoff 字符串。`_build_group_result()` 虽先尝试从 `evidence_analysis.llm_analysis` 取 summary，但该字段通常已经不存在，因此回退到最后一条 `ai_message`，设置 `legacy_text_fallback=true`，再把 summary 前缀 truncated 到 1600 字（`parallel_evidence.py:330-365`）。`dimension_evidence_by_entity` projected 自 tool events；`thinking_events` copied，其中普通/AIOps Observation 有界，但三个 full-passthrough 工具在低于 80% 压力时仍可能携带超过 3000 字的结果；跨组事件 dropped。这里必须区分 full archive、state handoff 和 group summary，三者不是同一份内容。

dimension_evidence_by_entity（`group_evidence.py:285-353`）：

```json
{"case-ns/pod-a":{"kubernetes":{"status":"present","query_count":1,"source_systems":["kubernetes"],"facts":[{"fact_id":"fact-redacted01","source_system":"kubernetes","value":"phase=Pending","evidence_refs":[]}],"limitations":[]},"metrics":{"status":"empty","query_count":1,"facts":[],"limitations":[]},"logging":{"status":"not_applicable","query_count":1,"facts":[],"limitations":["容器未启动"]},"tracing":{"status":"not_applicable","query_count":1,"facts":[],"limitations":["容器未启动"]}}}
```

- entity key/维度与 source systems projected；facts projected/compacted/deduplicated；当前 Kubernetes 派生 group fact 的 `evidence_refs` 固定为空，不能把 Observation 的 structured_ref 冒充为 fact ref；低价值字段和不识别的 structured 路径 dropped；事实条数/值按上游 MCP、Observation 和 aggregator 边界 truncated。

EntityDiagnosisSummary（`schemas.py:528-541`）：

```json
{"namespace":"case-ns","name":"pod-a","status":"CreateContainerConfigError","phenomenon":"Pod Pending","root_cause":"证据不足","causal_chain":[],"confidence":0.0,"supporting_fact_ids":[],"contradicting_fact_ids":[],"unknowns":["缺少当前实体有效 fact_id 支撑"]}
```

- identity/status copied；phenomenon/root cause/chain projected 自 structured LLM；未知 fact_id dropped；若有效 supporting IDs 为空，root_cause/confidence 强制 projected 为“证据不足”/0；自由文本不复制进别的实体。

单路径 RCAOutput（`schemas.py:561-608`）：

```json
{"diagnostic_status":"inconclusive","phenomenon":"Pod not ready","evidence_inventory":[{"fact_id":"fact-redacted01"}],"causal_chain":{},"root_cause":"证据不足","supporting_fact_ids":["fact-redacted01"],"contradicting_fact_ids":[],"unknowns":["依赖实体未知"],"hypotheses":[],"confidence":0.2,"confidence_reason":"只有状态事实","claim_validation":{"valid":true},"limitations":"缺少同 trace 链"}
```

- handoff/ledger facts projected 入 inventory 与 claims；合法 fact IDs copied；越界 IDs dropped；无足够 authority 的 claim 被 projected 为 inconclusive；llm_raw_analysis dropped 出下游主输入并仅供归档/诊断。

多组 conclusion 的 LLM 输入（`conclusion_formatter.py:803-840`）：

```json
{"group_id":"g1","entities":[{"namespace":"case-ns","name":"pod-a"}],"status_keywords":["CreateContainerConfigError"],"pod_abnormal_type":"ConfigBootstrapFail","collection_summary":"1/1 collected","entity_summaries":[{"namespace":"case-ns","name":"pod-a","root_cause":"证据不足"}],"dimension_evidence_by_entity":{"case-ns/pod-a":{"kubernetes":{"status":"present","facts":[{"fact_id":"fact-redacted01","value":"phase=Pending"}]}}}}
```

- group identity、entity summaries 和 dimension evidence copied 到 narrative input；collection_summary truncated 到 220 字；有 entity_summaries 时 legacy `summary` dropped；thinking_events/raw/archive payload dropped 自 LLM 输入，但随后由代码从 group_results copied/projected 成确定性卡片与逐工具区。

SSE evidence_context（`stream_contract.py:99-135`）：

```json
{"tool_call_id":"call-redacted","tool_sequence":6,"evidence_context":{"contract_version":"aiops.parallel-evidence-stream.v1","group_id":"g1","entity":{"kind":"Pod","namespace":"case-ns","name":"pod-a"},"dimension":"logging","source_system":"elasticsearch"},"semantic_success":true,"raw_ref":"tools/006.raw.txt","structured_ref":"tools/006.structured.json","summary_ref":"tools/006.summary.txt"}
```

- `group_id` copied 只能来自权威 parallel_context；entity projected 为“候选与组实体精确相交”的对象，否则 dropped；dimension/source_system projected；call identity/refs/semantic_success copied；parallel_context 的完整 entities 列表和 raw body dropped。前端按本节开头的 group-id/唯一实体规则消费，歧义项 projected 到 `unassignedResults`。

## 6. 所有当前截断、预算与压缩边界

截断发生顺序必须按真实请求链理解，后层永远不能恢复前层已经丢掉的数据：

1. **MCP 返回边界**：输入/查询元数据/输出分别是 4096/4096/6144 bytes，窗口最多两小时，且每维度还有 series/sample/record/trace/relationship 限额。`_shrink_result_once` 按上一节所列顺序删减并设置 `truncated=true`；所以 Robusta 收到的 raw 已经可能只是后端数据的有界投影。
2. **Observation 边界**：raw 原样归档；structured 只 admission 白名单合同字段；summary 默认最多 3000 字。AIOps query summary 的整行准入顺序固定为：`OBSERVABILITY_QUERY → ENTITY → PURPOSE → QUERY → TELEMETRY → TOPOLOGY_SUMMARY → ENTITY_NODE[1..8] → TOPOLOGY_EDGE[1..8] → FACT_LEDGER（否则 FACT[1..6]）→ SAMPLE[1..4] → 无 samples 时 FLOW[1..3]/SPAN[1..2]/CORRELATION[1..2] → LIMITATIONS → EVIDENCE_REFS → ERROR`。每个值先做普通前缀截断（尾部 `...`），再把完整 `LABEL=value` 作为原子行试装；整行加入后若会超过 3000 字则整行 dropped，后面的字段仍继续尝试，不切半行（`observation.py:469-574`）。最终普通 `_bound_summary` 若仍超限，则保留前缀并加“完整内容见 raw_ref”的 suffix，不做头尾保留（`observation.py:2404-2409`）。
3. **70% ReAct runtime compaction**：只对 evidence、且 context window `<=35000`；当前 32000 window 会启用，每次 call 最多一次。system/user/tool schema 之外的 dynamic events 达到 70% 时，从最近最多 24 个 ai_message/tool_result 和最近 3 条 observation tail 构建不超过 6000 tokens 的 payload，目标摘要 1200 tokens。lite LLM 输出只有通过 `ContextCompactionSummary` schema 且仍有 plan、completed/open、key/negative/conflict 等证据合同才采用；验证失败使用确定性 fallback，连确定性摘要都装不下时再退到只保留必要计划、已完成/未完成项、关键/负向事实、冲突和下一焦点的极端最小合同。成功后新增一个 `context_summary`：thinking_events 中 evidence plan 仍有界保留，普通 ai_message 正文被清空；超过 1200 字的既有 tool_result 不再保留正文，只留 preview 与 raw/structured/summary archive refs。Observation context 同时替换为压缩摘要，避免下一轮又把旧大结果注回（`client.py:2564-2700,2924-3450,3514-3637`）。
4. **72% provider hard guard**：每次实际 provider call 前重新计 system、message history、tool schema、structured schema、provider overhead、output reserve 和 safety。tokenizer 优先显式 tokenizer JSON、显式 tiktoken、已知 OpenAI tokenizer，否则 UTF-8 bytes/3 并标为 estimated。硬 input limit 是 `min(32000×0.72, 32000-output_reserved-2000)`，所以不能脱离本次 call 的 output reserve 把某个数写成全局常量：在 32000 window、reserve=6000 的普通示例中是 23040，estimated 再扣 256 drift 后目标为 22784；conclusion 默认 completion reserve=8192 时则是 `min(23040,21808)=21808`，estimated 目标为 **21552**。exact 计数不扣 drift。静态合同已超目标则直接抛 `StructuredContextBudgetError`，不发请求；动态历史超限则确定性保留头尾、省略中段。尾部不是“无条件固定留 1200 tokens”，而是以 `tail_ratio=min(40%, max(5%, 1200/token_budget))` 分配最终可保留字符，余量给头部；极小预算连 marker 都放不下时只保留最长前缀（`client.py:593-925,1827-2136`；`budget.py:142-224`；`conclusion_formatter.py:40-52,611-720,797-862`）。
5. **conclusion 封套与完成后拼接**：单路径先按 layer/evidence/RCA/tool data = 6000/8000/8000/16000 字裁段；若组合后的总 token budget 仍超限，按当前最长段优先做第二轮前缀裁剪，每个非空段至少保留 1000 字。非 observability 工具单条最多 1500 字，按 40% 头部 + 中段省略 marker + 尾部保留；observability 每调用最多 8 facts、单值 500 字。单路径的工具总数最多 24。多组 narrative 不使用这四段字符封套，而是把 group sections 交给 `call_simple`，超 provider 预算时由 72% hard guard 对整个消息做头尾保留/中段删除。LLM completion cap 默认 8192 tokens；完成后代码追加实体卡片（每实体每维最多前三条 fact）和逐工具证据（每组同样最多 24 条），最终 Markdown 没有总 cap（`conclusion_formatter.py:54-68,177-280,553-720,788-987`）。

Observation 的 80% 是另一条局部压力策略，不要和 70%/72% 混为同一层：非确定性 summary 在达到 80% 时可触发 LLM 摘要；AIOps case/query 保持确定性摘要，不再过 LLM。`fetch_runbook`、`run_bash_command`、`kubectl_run_image` 平时 full passthrough，即使超过 3000 字也原样回注；只有达到 80% 且 summarizer 可用时才摘要，随后才 `_bound_summary`。`semantic_success` 在压缩前计算：`query_rejected/query_parse_failed` 为 false；`query_succeeded` 仅接受 coverage 为 present/empty/absent/weak；`query_partial` 必须 coverage=partial 且至少一个 source-backed fact；命令/解析/Prometheus empty 等失败为 false，runbook_loaded 为 true，其他结果再按非空和命令失败文本判断（`observation.py:108-193,2349-2402`）。

其他节点边界仍存在：layer 在结构化提取前把超过 30000 字的模型文本压缩；parallel 兼容 summary 取前 1600 字但维度事实独立；RCA 总上下文 52000 字，子段 handoff/tool/ledger/quality/supplement 分别有预算。这些发生在上述全链路中的节点局部位置，不改变五步主顺序。

## 7. 两次真实运行：c04/c08/c09 在哪里失真

两份归档都来自当前 Pod PVC：`b8e7747d704d4f04` 与 `efa10bd677814b0d`。它们的 layer 都找到 c04、c08、c09 三个实体并生成 g1/g2/g3；因为 3 > 2，均走并行分支。每组工具真实数据保存在 `{run_id}-gN`，主 run 的 conclusion.input 则接收 group_results。

### 7.1 c04：采集到了 Secret key 缺失，但组诊断没有消费决定性字段

- 两次 run 的 layer 都把 c04 定位为 CreateContainerConfigError。
- 组工具归档中的 `kubectl_get_yaml` summary 明确写出：container reason 为 CreateContainerConfigError，message 为 `couldn't find key unavailable-key in Secret aiops-case-04/workload-input`。
- schema mismatch 是精确的：`kubectl_get_yaml` structured 中决定性消息位于 Kubernetes 原生形状 `containerStatuses[].waiting.message`，而 group projector 读取/投影的是 snake_case `container_statuses`（再加 selected_events/key_events/conditions 与顶层 status/reason/message/phase）。因此该消息没有进入 group facts，输入只剩 phase=Pending、Ready=False 等元状态（`observation.py:2039-2052`；`group_evidence.py:236-263`）。
- 结果是 b8/efa 的结构化实体诊断都把 c04 解释为“Pending/NotReady，具体原因待查”，而确定性逐工具区后来又展示了 Secret key 缺失。

归类：原始采集并不不足；缺失发生在 structured Observation → group dimension facts 的交接投影，是结构化交接丢失，随后造成组诊断语义评价不足。

### 7.2 c08：Kubernetes 的 OOMKilled 很强，但跨源请求不能合并

- b8 的 c08 Kubernetes 事实是 OOMKilled、exit code 137、CrashLoopBackOff；Prometheus 展示内存从约 3.8 MiB 上升到约 40.9 MiB，组诊断得出内存超限，证据链基本由 Kubernetes 终态支撑。
- 两次 run 的“日志来源”必须分开：b8 的应用日志事实来自 `query_pod_logs`（Elasticsearch），trace_id 为 `ad5e66ce7844fb8c4c0e22ba6cdda6f1`；efa 的 ES `query_pod_logs` 没有返回带 trace_id 的日志事实，最终可见的内存分配原文来自 Kubernetes `kubectl_previous_logs`，不能把它标成 Elasticsearch correlation。b8 的 DeepFlow flow trace_id 为 `04d9932e5fceaccd5102a141bc7f044b`；efa 的 DeepFlow/Tempo tracing 也只属于 tracing 源，不能与无同 ID 的 Kubernetes 日志合并。
- metrics 也不能合并陈述：b8 查询的是内存序列，从约 3.8 MiB 增长到约 40.9 MiB，可作为 OOM 的量化辅助；efa 查询的是 `restarts_total`，20→30 只能证明重启趋势，不能量化内存耗尽。efa 的指标仍因 `trend_evaluable=true` 且样本数达门槛取得高 Metrics 分；再与其他维度等权平均后 diagnostic sufficiency 约 0.75，同时计划项均 collected 使 `early_stop=true`。这正说明“趋势可评分、计划已采集”不等于本次 OOM purpose 已被指标回答。
- 因而可以分别陈述“日志记录内存分配”和“DeepFlow 看到 /work 200 flow”，不能声明它们是同一请求或完整调用链。OOM 根因不依赖这种错误合并，因为 Last State/Reason/137 是更直接的终态事实。
- efa 的 layer 还把 g2 的 `pod_abnormal_type` 污染为多个全局类型拼接，但组内 Kubernetes facts 最终仍把 OOMKilled 纠正回来；最终折叠区标题仍继承了错误 group type。

归类：c08 的决定性采集足够；主要问题是跨源 trace correlation 的语义评价不足，以及 layer 全局类型进入组 handoff 的结构化污染。

### 7.3 c09：503 是事实，“下游依赖不可用”不是已闭合因果

- Kubernetes Events 确认 readiness probe 持续返回 503，metric 确认 ready=0；这是 Pod 不就绪的直接证据。
- b8 的日志 trace_id `0597533a97536f7f2814a7e1a7d760bb` 与 DeepFlow trace_id `c0d31f5ab03e77fa07f6431fcc175f8b` 不同；efa 最终逐工具区同样展示两条不同 ID。
- 日志 message 是 `dependency unavailable`，但没有 source-backed 拓扑事实指出具体依赖实体，也没有相同 trace_id 的多 span 链。结构化实体诊断却把日志 503 与 DeepFlow 503 拼成“调用下游接口返回 503 → probe 503”，最终叙事再写成“上游依赖服务不可用”。

归类：对 Pod readiness 故障的采集充分；对“哪个依赖、哪条请求链”的采集不足。把不同请求和模糊日志消息上升为依赖根因，是语义评价不足；trace correlation/do_not_merge 没成为组诊断的硬输入约束，是结构化交接丢失。

### 7.4 三类问题的分界

| 类别 | 当前运行中的例子 | 判断依据 |
|---|---|---|
| 采集不足 | c09 未取得具体依赖实体和同 trace_id 的完整链；c04 事件本身未显示 Warning 原因 | 源数据没有回答该 purpose |
| 语义评价不足 | c09 把两个不同 trace_id 拼因果；c08 把独立日志/flow 当同请求的风险 | 数据存在，但结论超过数据支持范围 |
| 结构化交接丢失 | c04 Secret key message 未进 group facts；主 run parallel snapshot/evidence→RCA 归档为空；trace do_not_merge 未约束组诊断 | 上游 raw/structured 有信息，下游合同或投影中消失 |

## 8. 维护者核验入口

源码核验优先入口：

- API/SSE：`app/api/routes.py:53-146,632-682`，`app/core/service.py:796-879`，`app/core/workflow/executor.py:160-673`。
- 路由/状态：`app/core/workflow/graph.py:112-266`，`app/core/workflow/state.py:16-84`，`app/core/workflow/schemas.py:179-610`。
- 节点：`layer_classifier.py:563-918`，`evidence_collector.py:197-517`，`parallel_evidence.py:70-485`，`root_cause_analyzer.py:92-380`，`conclusion_formatter.py:93-215,788-987`。
- 数据合同：`app/core/context/archive.py:20-109`，`budget.py:48-224`，`observation.py:29-201,266-467`，`fact_contract.py:691-741,2000-2306,2950-3471`，`group_evidence.py:285-353`。
- MCP：`mcpstander/servers/aiops_observability_query_server.py:21-75`，`mcpstander/servers/holmes_tools/aiops_observability_query.py:27-307`。
- 前端：`frountind/src/hooks/useSSE.ts:8-135`，`ChatWidget.tsx:181-379,430-474`，`BotMessage.tsx:68-76`。

运行态核验入口：Pod 内 `/tmp/aiops/reports/context_archives/<run_id>/`，重点对照 `layer/handoff.json`、`node_inputs/conclusion.input.json`、`node_outputs/conclusion.output.json` 与各 `{run_id}-gN/tools/*.structured.json`。读取归档引用时必须保持 run_id/group_id 边界，不能把不同时间、不同组或不同 trace_id 的 Observation 合并。
