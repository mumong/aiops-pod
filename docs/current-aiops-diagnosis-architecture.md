# 核心实现：诊断、证据与上下文

[返回 README](../README.md)。本文描述当前源码与仓库默认配置，不代表已核对线上镜像；具体参数以 [config.yaml](../deploy/configmap/config.yaml) 为准。

## 模块职责

| 模块 | 实现入口 | 职责 |
|---|---|---|
| HTTP/SSE | [routes.py](../app/api/routes.py)、[service.py](../app/core/service.py) | 接收请求、加载配置与工具、启动诊断 |
| 工作流 | [graph.py](../app/core/workflow/graph.py)、[executor.py](../app/core/workflow/executor.py) | 条件路由、事件、计时、取消与归档 |
| 定位 | [layer_classifier.py](../app/core/workflow/nodes/layer_classifier.py) | 查询当前现场、确定目标 Pod、异常组和 Runbook |
| Pod 独立诊断 | [parallel_evidence.py](../app/core/workflow/nodes/parallel_evidence.py) | 每 Pod 一条 lane，独立执行 Evidence 与正式 RCA |
| 规划和采集 | [evidence_collector.py](../app/core/workflow/nodes/evidence_collector.py) | Evidence Plan、首轮查询、ReAct 补查及采集统计 |
| 根因与展示 | [root_cause_analyzer.py](../app/core/workflow/nodes/root_cause_analyzer.py)、[conclusion_formatter.py](../app/core/workflow/nodes/conclusion_formatter.py) | 根因推理、分组报告与汇总 |
| 观测处理 | [observation.py](../app/core/context/observation.py)、[observability_projection.py](../app/core/context/observability_projection.py) | 类型解析、规则投影、模式归并、摘要及引用 |
| 上下文 | [client.py](../app/core/aicall/client.py)、[budget.py](../app/core/context/budget.py) | 模型工具循环、预算门禁及压缩 |
| 归档与回读 | [archive.py](../app/core/context/archive.py)、[builtin_tools.py](../app/core/aicall/builtin_tools.py) | 保存节点/工具记录、fetch_runbook、read_context_archive |
| 数据合同 | [schemas.py](../app/core/workflow/schemas.py)、[state.py](../app/core/workflow/state.py) | 结构化输入输出和跨节点状态 |
| A2A | [a2a_adapter](../a2a_adapter/) | 标准协议封装；与主服务分容器、分依赖环境 |

MCP 查询和前端实现在独立仓库，不属于本仓库运行代码。接入关系见[部署指南](GUIDE.md)。

## 请求与 Pod 分组

/ask 强制完整诊断模式；/query 使用轻量查询路径。Layer 根据当前 Kubernetes 状态确定异常目标，无异常时可直接汇总。

默认 workflow.evidence.parallel.threshold=0，任何已确认异常 Pod（包括只有一个）都进入独立 lane，而不是“超过两个异常才并行”。每条 lane 使用本组实体、独立采证上下文、正式 RootCauseAnalyzer 和归档 ID；完成后直达 Conclusion，不再进行一次全局 RCA。

lane_concurrency=0 表示按目标数展开，没有该配置项指定的本地并发上限；受模型服务承载能力限制，可配置正数限制并发。不要把“并行”理解为无限资源。

[entity_evidence_snapshot.py](../app/core/workflow/entity_evidence_snapshot.py)负责组级证据快照，[lane_diagnosis_artifact.py](../app/core/workflow/lane_diagnosis_artifact.py)保存正式组级诊断产物。结构化交接和模型分析文字分别保存；模型文字不是工具事实的替代品。

SSE 事件包含 run_id、节点、工具调用及组身份。并行工具事件由 [stream_contract.py](../app/core/workflow/stream_contract.py)投影 evidence_context，消费者应使用 group_id / tool_call_id 关联，不能按工具同名或到达顺序猜测归属。

## Evidence Plan 与实际执行

当前 planning_mode=structured：

1. 单独调用模型生成 EvidencePlanOutput，程序做结构校验；无法取得有效计划时，自主模式可用最小 Describe 计划兜底。
2. 整理后的计划以“既有 evidence_plan”放入 Evidence 的执行输入；它不是另一个自行运行的 Agent。
3. 在 ReAct 前执行 Metrics、Logging、Tracing 首轮查询。优先使用计划中可用的查询项，否则补通用 Pod 生命周期指标和最近日志/链路基线。Topology 是辅助查询，不属于强制三维基线。
4. Evidence 根据结果决定专项补查、修改 PromQL 或过滤条件、回读归档。计划不等于固定、不可变化的工具序列。
5. 工具执行/参数失败有受限恢复路径；成功但 empty/absent 不等于执行失败，不触发同样的失败重试。
6. 保存实际计划、采集结果、缺口及模型解释，再进入该 lane 的正式 RCA。

可选 react_only 跳过独立 Plan 调用，仍保留首轮基线与自主调查。完整度是计划项完成情况，不等于关键证据充分，更不保证因果结论正确。

## 工具观测的三种表示

ObservationProcessor 接收工具返回和调用参数，按工具类型解析、生成摘要，再通过 ContextArchive 保存：

| 表示 | 内容 | 用途 |
|---|---|---|
| raw | Agent 实际收到的 MCP 响应或本地工具输出 | 原始输入副本，不等于数据源全部数据 |
| structured | 规范化观测、实体、事实、计数、覆盖和来源信息 | 后续程序处理与回查 |
| summary | 有预算限制的模型可见投影 | 进入工具消息，减少上下文占用 |

同一调用用编号、工具名及 raw_ref / structured_ref / summary_ref 关联。可观测性查询使用确定性投影，不直接让摘要模型改写其事实字段；不同工具的解析和摘要路径不同，不能泛称所有文本都无损保留。

投影依据观测类别与模式挑选代表记录，保留可用的数值统计、来源、覆盖及遗漏信息。预算不足时可以减少记录和细节；完整响应中已有但摘要未展示，与工具未取得数据是不同状态。详见[可观测性采集](observability.md)。

Runbook 通常完整传递，但高上下文压力下仍可能被摘要；不能承诺所有运行都原样看到全文。

## 压缩与按引用恢复

运行时压缩与单条工具摘要是两个环节：

- 单条摘要控制每次工具消息体积。
- 运行时压缩检查 Evidence 历史累计预算；默认启用、阈值比例 0.70、每次调用最多一次。只有模型容量能解析且不超过 max_context_window 等条件满足才进入该压缩路径。
- _compact_context_with_lite_llm 使用当前 AICall 的结构化模型调用，并不因函数名含 lite 就自动换成另一个小模型。
- _sanitize_runtime_compaction_summary 从程序保存的来源事件重建证据承载字段，再按预算裁减；结构校验失败时退回确定性摘要。
- 压缩结果用于缩短历史消息并继续当前工具循环；不是重新启动一次诊断。独立的输入硬预算门禁还会限制模型请求长度。

受保护的是指定路径中的来源关系和证据字段处理规则，不是保证所有记录永远进入上下文，也不是保证程序能验证所有自然语言因果关系。

read_context_archive 接收已知 archive_path，按 offset / length 返回文本片段和分页信息，范围限制在归档根目录。大内容仍需分段读取，并经过后续观测/上下文处理；不存在或不可读时返回错误，不会自动从后端补采。

回读工具主要执行文件路径边界检查，不等同于同组事实过滤器；模型是否回读、是否继续读取遗漏部分取决于执行过程。归档中不存在的历史数据不能靠引用恢复。

## RCA 与最终报告的边界

当前配置为 rca_mode=lite，组内正式 RCA 主要使用已采证据推理，不再重复进行取证工具循环。

仓库默认关闭 rca_validation.enabled 和 rca_context.fact_ledger_enabled，启用有界 evidence LLM analysis 作为辅助推理材料；因此不能把当前报告说成“全部经过 Fact Ledger 严格因果验证”。相关合同和校验实现仍保留在 [fact_contract.py](../app/core/workflow/fact_contract.py)，开关状态改变时需重新验证效果。

Conclusion 默认 presentation_mode=agent：各组按本组证据和 RCA 生成片段，代码组织总览与顺序；可切换确定性展示。结构字段合法、引用存在、Plan 完成，都不等价于根因正确。

实际复核必须区分事实和解释，例如 137 不能独立证明 OOM，/work 的 200 不能证明 /health 探针健康。

## 归档与运行排查

部署后报告默认位于 PVC 的 /tmp/aiops/reports，归档根由 AIOPS_CONTEXT_ARCHIVE_ROOT 指定。

| 路径（相对 context_archives） | 内容 |
|---|---|
| <run_id>/ | 主请求：定位、汇总及节点记录 |
| <run_id>-g1/、-g2/… | 各 Pod 组的采证与 RCA |
| 各组 tools/*.raw.txt / *.structured.json / *.summary.txt | 同次工具调用的三种表示 |
| 各组 node_inputs/、node_outputs/ | 节点交接输入输出；evidence.full.json 含计划与采集记录 |
| budget/ | 对应运行的上下文预算和压缩记录 |

引用是容器内文件路径，不是浏览器可直接访问的 URL。报告数据可能包含业务日志和内部地址，需配置权限、备份和保留周期。

启用 Langfuse 后，主 run_id 看定位/汇总，带 -gN 的记录看组内 Evidence/RCA。独立规划调用可查 workflow-evidence_plan；执行输入搜索“既有 evidence_plan”。规划前保存的 evidence.input.json 不是注入后完整模型消息。

测试目录中的 fixture-run-before/after 是测试脚本采集的 Pod 快照，用于核对身份和异常环境，不是 Agent 输出，也不是修复前后记录。
