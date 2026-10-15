# 核心实现：诊断、证据与上下文

[返回 README](../README.md)。本文描述当前源码与仓库默认配置，不代表已核对线上镜像；具体参数以 [config.yaml](../deploy/configmap/config.yaml) 为准。

## 模块职责

| 模块 | 实现入口 | 职责 |
|---|---|---|
| HTTP/SSE | [routes.py](../app/api/routes.py)、[service.py](../app/core/service.py) | 接收请求、加载配置与工具、启动诊断 |
| 工作流 | [graph.py](../app/core/workflow/graph.py)、[executor.py](../app/core/workflow/executor.py) | 条件路由、事件、计时、取消与归档 |
| 意图路由 | [request_router.py](../app/core/workflow/nodes/request_router.py) | 模型理解意图、范围与深度，输出 JSON 路由 |
| 深度诊断 | [autonomous_diagnosis.py](../app/core/workflow/nodes/autonomous_diagnosis.py) | 自主定位、取证和根因分析，不执行固定扫描兜底 |
| 轻量查询与共同总结 | [query_answer.py](../app/core/workflow/nodes/query_answer.py) | 自主查询、证据驱动总结、会话结果保存 |
| 多组并发 | [autonomous_parallel.py](../app/core/workflow/nodes/autonomous_parallel.py) | 定位交付多个调查组时，每组独立 Evidence → RCA lane（并发上限可配置） |
| 观测处理 | [observation.py](../app/core/context/observation.py)、[observability_projection.py](../app/core/context/observability_projection.py) | 类型解析、规则投影、模式归并、摘要及引用 |
| 上下文 | [client.py](../app/core/aicall/client.py)、[budget.py](../app/core/context/budget.py) | 模型工具循环、预算门禁及压缩 |
| 归档与回读 | [archive.py](../app/core/context/archive.py)、[builtin_tools.py](../app/core/aicall/builtin_tools.py) | 保存节点/工具记录、fetch_runbook、read_context_archive |
| 数据合同 | [schemas.py](../app/core/workflow/schemas.py)、[state.py](../app/core/workflow/state.py) | 结构化输入输出和跨节点状态 |
| A2A | [a2a_adapter](../a2a_adapter/) | 标准协议封装；与主服务分容器、分依赖环境 |

MCP 查询和前端实现在独立仓库，不属于本仓库运行代码。接入关系见[部署指南](GUIDE.md)。

## 当前入口：按意图选择深度

[打开交互流程图](aiops-intent-workflow.html)（支持明暗主题与图片导出；编辑源为 aiops-intent-workflow.json）。图中区分模型意图判断与 LangGraph 的固定连线执行。

`/query` 与 `/ask` 均使用 `query_mode=auto`。RequestRouter Agent 输出 JSON，LangGraph 按 `route` 选择：

- `focused`：`query_collect → END`，日常查询、可观测性数据获取、知识解释和明确要求的快速初查；查询 Agent 在同一工具循环内提交 QueryAnswer，不再调用独立总结模型。
- `full_diagnosis`：单对象或分组暂不可用时 `layer → evidence → rca → conclusion`；定位模型选出多个 Pod 时 `layer → parallel_evidence（每组 evidence → rca）→ conclusion`。该名称表示深度，不表示全量扫描。
- `clarify`：返回模型的澄清问题并保存会话，等待补充；路由格式无效则明确停止，不自动选择某种业务流程。

路由只校验结构，不根据关键词、namespace 或对象数量改写模型决定。工具结果也不会自行改变路由。提示词统一位于 [prompts.py](../app/core/prompts.py)。

路由调用失败保留分类：模型服务 HTTP 错误、连接失败、超时、结构化格式异常与一般路由执行异常，通过 `request_error` 传入节点快照及 final。失败不再统一提示“无法识别任务”；真实澄清仍使用 clarify。公开错误仅含安全提示和 HTTP 状态，不输出提供商错误正文；已有历史时说明上下文已加载，不清空或覆盖旧会话。本策略不增加自动重试、不推测业务路由，也不解决上游服务本身的故障。

路由历史包含用户问题、助手回答、范围与观测时间。助手回答用于识别上一轮查询后新发现的对象（例如“刚才那个异常 Pod”），不被当作当前状态证据；原始工具正文不重复塞入路由。超预算走共享压缩，不预先删掉回答。

深度节点实现见 [autonomous_diagnosis.py](../app/core/workflow/nodes/autonomous_diagnosis.py)，分组实现见 [autonomous_parallel.py](../app/core/workflow/nodes/autonomous_parallel.py)。定位 Agent 直接输出结构化目标；代码分配组，不再二次调用模型从文字提取对象。每组独立客户端、工作上下文和归档；并发上限由 `AIOPS_AUTONOMOUS_PARALLEL_WORKERS` 控制（见 [configuration-env.md](configuration-env.md)），模型服务的 admission control 是最终容量边界。不进入旧节点的程序基线、强制三维计划、提前停止或因果发布门槛。

**定位阶段的清单投影**：`query_pod_lifecycle` 列表结果进入模型前经 `lifecycle_core.inventory_view` 投影——需要关注的 Pod 保留完整生命周期记录，当前快照正常的 Pod（Running+Ready、容器全部 running/ready、窗口内无终止或重启、未删除；或 Succeeded）只按命名空间列成花名册并给出判据。真实 73 Pod 页从约 15.8k tokens 降到约 1.9k；归档与 structured 仍保留全部 Pod，花名册不是健康结论。单 Pod 范围和正常 Pod 少于 4 个时不投影。

**取证 lane 的工具面**：lane 只拥有一个 Pod（namespace/name/uid 来自定位交接），暴露 17 个工具：`execute_pod_promql`、`query_pod_logs`、`query_pod_tracing`、`query_pod_topology`、`query_pod_lifecycle`、本 Pod 的 describe/events/yaml/get_by_name、当前/previous/容器日志、通用 Prometheus 即时/区间查询、`fetch_runbook`、`read_context_archive`。集群列表、grep、目录类和 TodoWrite 不在 lane 内。`execute_pod_promql` 被拒绝或返回空时，MCP 会在 `limitations` 中列出该 Pod 实际存在的指标名，供模型按目的选择。

定位使用 [location-handoff.v1](history/structured-diagnosis-handoff-20261012.md)：可压缩的分析文字之外，只保护稳定目标、简短现象、处理状态和引用，分组直接读取清单。取证与 RCA 仍输出文字；生命周期明细与分析过程可以摘要，不再作为免压缩的全量保护数据。非 Pod 目标兼容单路诊断，不能因不适用 Pod 并发执行器而丢弃。

分支 `question/request_contract` 是该 Pod 子任务，`original_question/original_request_contract` 保留完整父任务。共享定位记录是参考，不是要求每组重新检查全部对象。任一组失败保留已取得证据和失败原因，其他组继续；最终汇总包含每组结果和限制，不因未满足旧 RCA schema 丢弃整组。前端展示真实分组工具事件，多个模型的逐字片段不混排。

每次交接均包含用户原始问题、时间、任务范围、最新工作摘要、保留交互和真实工具观察。上游分析只是草稿，不是事实。工具结果只传一份，不同时重注入 raw 和 structured 的重复内容。超预算后使用替换后的工作上下文，不重新拼回已压缩历史。

采集循环、路由、RCA和总结统一使用 `partition_recent`：在 min(8000, 窗口15%) token 中保留近期完整交互，将较早部分滚动合并成一份摘要。超大单条无法保留时进入摘要，不拆开工具调用与响应。节点间使用 `compact_working_material`，并发汇总保留每条交互的 lane 身份；一个子组的压缩不能重置父流程或兄弟组。失败不替换旧状态，预算仍不足则明确报告，不硬截断或静默循环。

2026-09-18 更新：旧历史需要至少三段时，默认最多三路并行提取证据卡，再按源顺序合并为一份工作摘要；一至两段仍走原串行流程。`AIOPS_COMPACTION_WORKERS=1` 可回退串行。每段都消费，不为了摘要加速裁掉历史；空摘要、超预算、输出被截断或分段失败均不替换旧状态，未完成兄弟任务取消。所有摘要提示词统一位于 `app/core/prompts.py`。这是每次压缩的并发上限，不是整个服务的全局请求限流。

步数是 LangGraph recursion_limit，不等于工具调用数；当前部署定位/取证/查询各 48（`workflow.max_steps`），到达上限时进入结构化收卷而不是直接丢弃结果。工具业务拒绝/失败同时进入事件状态与失败计数，成功空查询仍区别于调用错误；报告/执行未完整时 final.status=partial，不再顶层误报 success。独立诊断组展示各自进度与执行状态；父节点未完成保留为整体限制，不把所有已完成子组自动标成失败。

`evidence_receipts` 在节点交接及整包压缩后保留工具/对象/返回状态/原文引用的轻量记录，防止把摘要未展示误认为未采集。记录只证明调用与返回，不证明根因或数据足够，模型仍自主取证与判断。并发看板保留终态未返回调用，但显示为“阶段已结束，不再等待”，不伪装为持续执行。

Conclusion 生成 `QueryAnswer` JSON，字段为 intent、scope、status、answer、evidence_refs、runbooks、missing；answer 为兼容前端的 Markdown 正文。深度总结使用兼容的 RepairDraft 扩展附带可选修复计划。无程序级语义验收，不宣称已自动验证根因正确。权限、格式、取消、超时、预算与归档属于工程边界，仍保留。`/query` 与 `/ask` 均可按用户意图路由到独立修复节点；普通 focused/query 路由禁止写入。深度计划进入受限审批执行器，未形成计划时提供按需修复入口，详见 [Pod 修复](pod-remediation-delivery.md)。

轻量查询复用同一回答结构、格式解析和会话保存逻辑，但由 QueryCollect 直接生成结果，使用 LangChain ToolStrategy(QueryAnswer) 而非再启动总结节点。网关不兼容时沿用已有无 schema 兼容重试；格式无法恢复则明确标记 partial，不静默调用另一个模型重写。前端 JSON 流只展示 answer 正文，框架结构化工具不显示为集群工具调用。知识解释通常是路由加回答两次模型请求；工具查询还包含工具返回后的模型请求，不保证只有两次。

深度报告另用 `DEEP_CONCLUSION_PRESENTATION` 提示词组织结论、证据表、根因/待核实项及建议/Runbook；普通查询不套此模板。证据表要求区分 Metrics、Logging、Tracing 的已采集、未采集、失败、空结果或不适用，不由程序补造证据。匹配的 Runbook 由模型读取并选用步骤，未设置强制调用兜底，因此仍可能被模型跳过。前端阶段草稿默认折叠，按 Markdown 渲染，不将正文中的环境变量赋值拆成 KV 字段。

深度提示词现以原四节点专业要求为基础适配：定位只确认范围和现象，取证对比支持/反驳证据，RCA 寻找受支持的最上游可行动原因，总结恢复“异常概览—证据内容—因果链/根因结论”风格。没有接回旧 LayerOutput、程序首轮 Evidence Plan、80% 停采或 RCA 发布校验；报告仍包在 QueryAnswer.answer 中。此为提示词适配，不是旧工作流恢复，也不保证模型必然遵循。

## 共享会话与 54k 上下文

### 重型工具入口摘要（11.0.188）

工具结果进入工作上下文前，名单内返回超过 6,000 字符时使用已有 raw / structured / summary 链路，不额外调用摘要模型。名单包括 describe、events、集群/命名空间列表、表格与 jq 查询、指标名称/标签值/PromQL、kubectl 日志系列，以及 Pod 的 Metrics、Logging、Tracing、Topology 工具。不再依赖节点名，避免新增自主节点绕过策略。较小返回保持原文。

原始返回完整归档，结构化结果保存解析信息，模型接收约 3,000 字符正文加覆盖说明和回读引用。日志为错误、恢复及变化首尾记录预留展示机会，再补其他模式；不会把不同 HTTP 状态码合并。表格移除对齐空格、不按健康状态过滤；JSON 查询保留完整记录，不从中间截断 JSON。省略不是不存在，摘要不能用于未经补查的全集统计。Runbook、主动原文回读、未知工具及未列入名单的工具不作此类强制摘要。

这只减少大工具结果引起的上下文增长；累计历史仍可能触发共享上下文压缩。不能保证所有关键内容都进入摘要，缺失部分需回读。验证包括 139 份近期真实大结果回放（原文完整、引用可读、摘要少于 4,000 字符）及噪声末尾错误/恢复、内存增长端点、完整 JSON、宽表格等回归测试；不等同于全量诊断准确率验收。

两个接口均接受 session_id，并用相同 HttpOnly owner cookie 隔离会话。前端同一会话切换入口仍传相同 ID。缓存为进程内 TTL/LRU，30 分钟、64 会话、单会话 256 KiB；Pod 重启丢失，不支持多副本共享。只有完成的结果保存，取消不覆盖旧记忆。

两条路径使用同一 MODEL_CONTEXT_WINDOW（当前环境 54000）和 WorkingContextMiddleware。达到配置预算时，围绕原问题压缩完整工作历史、保留近期完整工具交互，并替换实际 LangGraph messages；后续再超预算仍会触发。工具调用与对应返回不拆散。RCA/总结无工具调用时同样在预算不足时调用共用摘要器。压缩失败不以切片假装完成。

重型工具名单继续使用 ObservationProcessor 中的受限摘要策略：仅名单内且超过 6000 字符时处理，普通工具、日志、Runbook 和归档回读保留原文。摘要不意味着源数据不存在；原文与遗漏信息保留。表格不再仅因存在异常而删掉健康对象。此策略共用于 query_collect、layer、evidence。

## 旧流程（已移除）

2026-10-14 起删除了 `query_mode=full` 旧流水线（layer_classifier、evidence_collector、parallel_evidence、root_cause_analyzer、conclusion_formatter 及其专属模块）。所有入口（含 `/q/{question}`）均使用 auto 图；`direct` 仅保留 QueryCollect。历史报告中的旧节点名与旧行为仅供复核，代码可从 git 历史（提交 2158d245 之前）回溯。

### 轻量直接作答验证（2026-09-18）

后端 1335 项单元测试、前端 67 项测试通过；构建、lint 及部署后直接查询浏览器回放通过。浏览器验证 JSON 分片只显示 answer 的 Markdown 表格、轻量路由没有总结步骤、最终回答与历史恢复正常。

真实模型对照：仅提示词 JSON 的 `intent-smoke-de3017d0315e` 重复请求 Pod 列表并触发步数限制，不作为通过记录；改为 ToolStrategy(QueryAnswer) 后，`intent-smoke-1d9c9c909f7e` 一次工具查询取得 xnet 4 个 Pod，直接返回结构化答案；`intent-smoke-3274d254a78d` 无工具完成能力介绍。两次分别约 49 秒和 61 秒，均保存会话且不经过 conclusion，说明独立总结调用已消除，但不能据此宣称总体延迟已改善或模型异常已解决。

后端 11.0.176、前端 0.1.19 已部署。经前端代理真实请求 `a4e4240afc01427f` 正常返回 xnet 4 个 Pod：路由和 query_collect 两个节点、3 次模型调用、1 次工具执行，耗时约 43 秒，其中工具约 0.19 秒；没有 conclusion 节点。延迟仍主要在模型调用，不能将节点减少等同于已实现低延迟。

### 并发与统一压缩验证（2026-09-18，前版记录）

后端全量单元测试 1332 项、前端 65 项通过；前端构建、lint 和部署后的分组/布局浏览器回放通过。后端镜像为 11.0.174，前端为 0.1.18。回放与单元测试不等价于真实模型端到端验收。

两端已完成实际 Pod 滚动部署。经前端 `/api/query` 的上线查询 `5de3e7144746465f` 在约 19 秒内完成：正确路由 focused，一次工具调用列出 xnet 的 4 个 Running Pod，并收到流式分析事件及最终回答。该检查验证简单路径与前后端连接，不替代下述多组深度测试。

真实三组测试 `intent-smoke-6a84544b99a3` 的三个取证请求在 36ms 内启动；已返回工具记录体现各组独立 Pod 子任务。但第三组取证触发 600 秒 agent_timeout，之后 RCA 仍长时间等待，独立测试进程在约 16 分钟后人工停止，归档保留。该次未产生最终汇总，不能记为端到端通过；已确认等待位于模型调用阶段，尚未确定提供商或客户端的具体根因。无工具 RCA 的等待仍受底层客户端策略影响，不能认为所有阶段已有一致的工作流总时限。

### 前次路由验证记录（当时未部署）

后端单元测试 1323 项通过；A2A 18 项通过。前端相关测试 13 项、构建和 lint 通过，完整前端测试仍有 3 项既有部署仓库断言失败，不能据此宣布全部前端测试通过。

使用独立进程加载本轮源码、连接真实模型与 MCP，未替换线上服务：`intent-smoke-c0457e054868` 正确区分 xnet 当前健康状态与历史重启；`intent-smoke-7f59f45697e0` 通过归档回读补齐集群表格，识别 case05 沙箱、case08 OOM、case09 就绪探针异常。仍观察到将测试背景误解为无需处理、证据引用不精确及部分推断过强，不作为诊断准确率验收。

真实 `intent-smoke-ad1870984a01` 的指标返回回放：13201 字符转为 2733 字符，3 个不同容器运行实例的完整序列、标签、时间和值均保留。修复的是摘要丢失运行实例标签的问题；不保证模型不会错误合并不同序列。重复超预算测试验证实际消息替换，而非仅缩短一次模型请求。

以下为旧流程及上一部署的实现说明；涉及节点编排、仅 QUERY 开关、强制计划和报告校验的描述不适用于上文的新默认 auto 路径。

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

QUERY 当前为单个自主采集 Agent → Conclusion，不执行 ASK 的异常组扇出；同轮多个工具调用可并发。可观测性工具 `execute_pod_promql`、`query_pod_logs`、`query_pod_tracing`、`query_pod_topology` 均可用，是否调用由任务和已获得证据决定，不强制三维采集。其他能力包括只读 Kubernetes 状态/日志/过滤查询、通用 Prometheus、Runbook 和归档回读；任意 shell 与创建测试 Pod 工具不暴露。

本次部署核对的 QUERY 工具共 36 个（实际以已加载工具与白名单的交集为准）：

| 类别 | 工具 |
|---|---|
| Kubernetes 状态与关联 | kubectl_get_by_name、kubectl_get_by_kind_in_namespace、kubectl_get_by_kind_in_cluster、kubectl_find_resource、kubectl_get_yaml、kubectl_describe、kubectl_events、kubectl_lineage_children、kubectl_lineage_parents |
| Kubernetes 日志 | kubectl_logs、kubectl_previous_logs、kubectl_logs_all_containers、kubectl_previous_logs_all_containers、kubectl_container_logs、kubectl_container_previous_logs、kubectl_logs_grep、kubectl_logs_all_containers_grep |
| 过滤与统计 | kubernetes_count、kubernetes_jq_query、kubernetes_tabular_query |
| 通用 Prometheus | execute_prometheus_instant_query、execute_prometheus_range_query、get_metric_names、get_metric_metadata、get_all_labels、get_label_values、get_series、get_prometheus_target、list_prometheus_rules |
| Pod 可观测性 | execute_pod_promql、query_pod_logs、query_pod_tracing、query_pod_topology |
| 辅助 | fetch_runbook、read_context_archive、TodoWrite |

Conclusion 先验证 QueryAnswer JSON；仅对 answer 字符串内未转义双引号/换行实施局部修复，要求外层字段完整且恢复结果唯一，不改写诊断事实。格式无法安全恢复时提示异常并展示可用分析草稿，不把 JSON 外壳当 Markdown。原文及格式处理状态写入 `conclusion/render_audit.json`。前端代码块由单层 pre/code 渲染。

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

组内正式 RCA 无工具，只依据已采证据推理。Fact Ledger 严格因果校验未启用（合同实现仍在 [fact_contract.py](../app/core/workflow/fact_contract.py)），不能把当前报告说成“全部经过严格因果验证”。`workflow` 配置只保留代码实际读取的键（nodes、max_steps、structured_runtime、evidence.parallel、remediation、think_stream、observation_summary、context_compaction），由 `test_deployed_workflow_config_contains_only_keys_the_code_reads` 钉住。结构字段合法、引用存在，都不等价于根因正确。

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
