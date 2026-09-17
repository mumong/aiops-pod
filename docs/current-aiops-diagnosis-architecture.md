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

`/ask` 使用任务路由（`query_mode=auto`）；`/query` 使用两个节点：自主查询 Agent → Conclusion Agent。

`/query` 不再用 Prometheus JSON 兜底解析作为最终答案。`query_collect` 根据原问题自主调用只读工具，提供已安装 Runbook 的完整目录并按需读取正文。Conclusion 接收原问题、分析草稿和本次工具结果（含来源引用），不调用工具，生成 `QueryAnswer` JSON：intent、scope、status、answer、evidence_refs、runbooks、missing。最终事件保留 `answer` Markdown 兼容前端，另提供 `query_answer`。JSON 格式失败保留原模型文本，结构化字段为 null；不以格式失败判定没有证据。不对答案做程序级语义或引用校验，正常展示不代表结论已核验。查询不强制指标表、三维采集或诊断模板。保留归档、预算、取消和只读边界，不追加诊断质量评分，不自动修复。实现见 [query_answer.py](../app/core/workflow/nodes/query_answer.py)。

- `request_router` 在查询环境前生成任务合同，保留任务类型、对象范围、时间要求和请求输出。只有明确的全局综合检查进入原诊断图。
- 命名空间检查、指定 Pod 分析、指标/日志查询和组合问题进入 `focused`。该节点先自主调用只读工具，再仅根据本次工具记录整理结构化回答；不是固定工具序列。两个图节点不意味着只有两次模型调用。
- 歧义返回澄清；路由失败停止，不默认全局扫描。用户要求写操作时不执行变更。
- 聚焦路径不加载完整诊断提示词，不执行三维基线或自动异常分组。工具出现异常对象不会改变请求路由。

`/ask` 的 focused 路径目前保留工具归档、预算、取消、输出结构与来源校验；查询范围由提示词指导，不再挂载 namespace/PromQL 参数拦截。引用存在校验只证明出处存在，不证明数值转换、解释或因果判断正确。NotFound、空结果和失败记录可用于说明不存在或采集限制，不能自动成为健康证据。轻量结果不追加诊断质量评分，也不进入自动修复。

聚焦表格摘要按源顺序展示，不按异常状态过滤健康对象；结构化归档保留完整表格行，摘要注明省略数量并提供模型可见的原文回读地址。原诊断路径保留异常优先展示。发现的对象不再兜底成为“用户明确指定的 Pod”；分组子任务保留原始用户问题。

实现入口：[request_router.py](../app/core/workflow/nodes/request_router.py)、[focused.py](../app/core/workflow/nodes/focused.py)、[task_tools.py](../app/core/workflow/task_tools.py)。真实模型/MCP 验证入口：[verify_task_routing.py](../scripts/verify_task_routing.py)，仅做只读请求，不部署异常环境；结果中 `route_pass` 仅代表路由通过，回答需单独核对。

进入完整诊断图后，Layer 根据当前 Kubernetes 状态确定异常目标，无异常时可直接汇总。

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

### QUERY 会话短期记忆

`/query` GET/POST 可传 `session_id`（16–128 位字母、数字、下划线或连字符）；不传保持单次请求。浏览器每个聊天生成随机 ID，同一聊天复用，“新建会话”更换。后端用 HttpOnly、SameSite=Strict 的匿名 Cookie 加 session_id 定位独立缓存；不是用户登录鉴权，生产环境仍需接入身份认证及 HTTPS。命令行续聊需要同时保留 Cookie 和 session_id。ASK 不读写此缓存。

进程内 TTL/LRU 缓存默认保留 30 分钟、最多 64 个会话、每会话最多 256 KiB 序列化内容。同一会话并发请求拒绝，不交错写入；最终结果产生后原子提交，异常或取消不覆盖旧快照，超容量明确提示未保存。历史保存用户问题、最终回答、必要观测与来源、时间及压缩后的工作记忆；最新问题优先，历史指标不能作为当前值。预算不足时复用意图导向状态压缩，后续轮次使用替换后的工作摘要。

这是单进程单副本验证方案：重启、过期或容量淘汰后记忆清空；浏览器仍显示旧对话不代表服务器记忆仍在。多副本/多 worker 需改共享存储。参考 [LangGraph Memory](https://docs.langchain.com/oss/python/langgraph/add-memory) 的 thread_id＋状态持久化及 [LangChain Short-term memory](https://docs.langchain.com/oss/python/langchain/short-term-memory) 的状态整理机制。本项目保留每轮独立工作流与 run_id，通过有界快照缓存实现会话延续，而非直接缓存整个诊断工作流检查点。

### QUERY 原文输入与自动压缩

当前部署将 `workflow.context_compaction.hard_guard_input_ratio` 覆盖为 0.90。54K 窗口下仍预留 6,000 输出、2,000 安全及 256 估算余量，实际主调用输入触发线约 45,744 tokens；以下 0.72 是代码默认值，不是当前部署值。摘要子请求的保守分段预算不随主调用触发比例提高。

`AIOPS_QUERY_RAW_TOOL_OUTPUT=true` 仅作用于 QUERY 的请求级客户端，默认关闭。启用后默认保留工具原文输入，但以下名单在单次返回超过 6,000 字符时使用定向摘要：`get_metric_names`、`kubectl_describe`、`kubectl_events`、`kubectl_get_by_kind_in_cluster`、`kubernetes_tabular_query`、`execute_prometheus_instant_query`、`execute_prometheus_range_query`、`execute_pod_promql`。名单位于 `ObservationProcessor.QUERY_SUMMARY_TOOLS`；events/range 为预防项，近期统计未覆盖独立调用。短结果、其他工具、Runbook 和归档回读保持原文，不因本名单改变 ASK。

名单内采用确定性提取，不调用工具摘要模型：describe/events/表格/Pod 指标复用已有提取器；指标目录按名称前缀类别轮选并标明遗漏数；通用 Prometheus 返回保留完整单条序列的标签、时间和值，不换算单位，不用子集推算整体。大到无法容纳的单条序列可全部省略，需缩小查询或回读。完整 raw/structured 仍归档，模型摘要附原文引用。Conclusion 对定向摘要结果不重新注入完整 structured，避免再次放大输入。摘要会省略信息，不保证保留所有任务相关事实。

当前窗口按实际模型配置为 54,000 tokens；默认主调用输入触发线约 38,624 tokens（0.72 比例并扣除估算余量）。每次模型调用前仍检查预算；超预算时保留至多 min(8,000, 窗口×0.15) tokens 的最近完整交互，其余较早消息交给同配置模型整理。并行工具调用及对应返回作为一组保留，不能拆散；若最新一组本身太大，会进入摘要而不是截断它。消息正文、工具参数、调用关系及缓存来源保留，usage 等运行元数据不送去摘要。原始完整消息另行归档。

摘要请求根据 token 预算优先一次处理，不再固定按 12,000 字符串行切块；为累计摘要、输出和协议保留余量。超大输入按完整交互分段，只有单个交互本身超出摘要容量时才完整切段，全部片段都会送入滚动摘要，不做首尾取样。通过 LangGraph `before_model` 返回 `RemoveMessage(REMOVE_ALL_MESSAGES)` 加原问题、新工作摘要和保留交互，真正替换消息状态。摘要沿用诊断模型，不默认切小模型或改变提供商思考参数。压缩前后快照及保留消息数、摘要调用数位于 `compactions/`；失败或压缩后仍超预算时不静默裁剪。系统提示词和工具定义保持不变。54K 是窗口大小，输出和安全余量仍占用该窗口。

保留交互还通过 `context_compacted.retained_messages` 传递给 Conclusion，并存入会话记忆，避免只传历史摘要而漏掉未摘要的近期证据。

Conclusion 使用最近一次工作摘要和此后新取得的工具结果，不重新拼回已压缩的全部旧工具正文。总结输入仍超预算时，同样按原意图分段整理后再生成回答。压缩使用 LLM，可能有语义遗漏，不构成事实无损保证；归档回读的分页、工具自身行数限制仍有效。工作历史替换是当前运行内的状态更新，不等于已实现跨进程断点恢复。

`AIOPS_QUERY_TOOL_TIMEOUT_SECONDS` 默认 60 秒，限制 QUERY 单次工具等待；失败作为工具错误交给 Agent 决定下一步。步数、运行时限等中断会传给 Conclusion，并在最终回答标记未完成。取消客户端等待不保证远端计算同步停止。

上下文压缩通过 `thinking/runtime_status` 发送分段开始、完成、失败和取消提示，覆盖采集节点及总结节点；不发送内部压缩正文。前端在折叠区域外显示当前阶段及耗时，区分工具等待、模型生成和上下文整理。超过 15 秒提醒当前尚未收到下一阶段结果，不把等待误报为失败。最终完成、错误、断线和手动停止均结束运行提示。普通 AI 正文标为“分析说明”，目前仍按内容类型汇总，不伪装成严格的执行时间线。此状态通道不依赖模型提供商的 reasoning 字段。

默认摘要不是纯代码：表格、事件等使用规则提取，部分通用返回调用 LLM 摘要。原文保存不等于模型看过原文。常见输入缩短位置包括工具摘要限长、摘要模型原文预览、归档分页、运行时历史压缩、模型调用前预算裁剪；原文实验绕过逐次工具摘要，但仍在超预算时压缩输入。压缩是有损的，不保证所有关键字段进入模型，也不保证单位解释或诊断推理正确，需要对照调用参数、原始值与最终答案复核。

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
