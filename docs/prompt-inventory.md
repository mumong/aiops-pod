# 提示词使用清单（2026-10-09）

实际入口是 `app/core/prompts.py`，不是 `prompt.py`。本清单覆盖其全部公开常量、导入片段及构造函数（128 项）；别名、注册表和消息片段不等于 128 次 LLM 调用。

## 先看当前生效路径

`/ask`、`/query` 在 `app/api/routes.py:172,194` 默认传入 `query_mode=auto`。图构建函数自身默认值 full 是兼容入口，不能据此判断线上走旧四节点。

| 场景 | 提示词 | 实际调用处 / 条件 |
|---|---|---|
| 理解任务 | REQUEST_ROUTER_PROMPT | request_router.py；生成 RequestContract，决定轻量、深度、修复或澄清 |
| 快速查询、解释、授权普通操作 | QUERY_COLLECT_PROMPT | query_answer.py:119；QueryCollectNode，自主工具循环后直接输出 QueryAnswer |
| 深度定位 | DEEP_LAYER_PROMPT | autonomous_diagnosis.py:21；不是旧 LAYER_CLASSIFIER_PROMPT |
| 深度证据采集 | DEEP_EVIDENCE_PROMPT | autonomous_diagnosis.py:87；自主选择证据 |
| 深度根因分析 | DEEP_RCA_PROMPT | autonomous_diagnosis.py:93；collect=False，不调用新工具 |
| 深度取证公共补充 | DIAGNOSTIC_TOOL_GUIDANCE | autonomous_diagnosis.py:45；仅 collect=True 的定位和证据节点（含并发分支） |
| 深度报告 | QUERY_CONCLUSION_PROMPT + DEEP_CONCLUSION_PRESENTATION | query_answer.py:186；名字含 QUERY，但快速 Query 不经过它 |
| 修复方案 | POD_REMEDIATION_PROMPT | remediation.py:80；也加入深度总结以允许在证据充分时附方案，不代表已授权执行 |
| 并发分组 | PARALLEL_TARGETS_PROMPT | autonomous_parallel.py:54；提取目标 |
| 并发子任务 | PARALLEL_LANE_PROMPT 和任务片段 | 约束每个分支对象，汇总时保留归属 |
| 工作记忆压缩 | CONTEXT_SUMMARY_PROMPT | working_context.py，别名 SUMMARY_PROMPT；超预算时，不是每轮必调 |
| 重型工具摘要 | TOOL_OBSERVATION_SUMMARIZER_PROMPT | client.py:4065 经 get_workflow_prompt 读取；与工作记忆压缩不是同一个用途 |
| 联邦多集群 | FEDERATION_AGENT_PROMPT / SYNTHESIS / COMPRESSION | federation/agent.py 与 aggregator.py；仅联邦路径 |
| 旧结构化诊断 | LAYER_* / EVIDENCE_COLLECTOR / ROOT_CAUSE_ANALYZER / CONCLUSION_FORMATTER 等 | graph.py 的非 auto/direct 兼容路径；不等于当前自主四节点 |
| 保留但未发现 app 内实际消费 | SYSTEM_PROMPT、GROUP_EVIDENCE_SUMMARY_PROMPT、REMEDIATION_PLAN_PROMPT | 不能因常量存在就认为它影响当前请求；SYSTEM_PROMPT 仅包级再导出 |

## DIAGNOSTIC_TOOL_GUIDANCE 是什么

它是深度诊断定位/取证阶段的“公共取证约定”：多维可观测性、对象/时间对齐、Runbook 使用、只读边界、失败与空结果、证据边界。它不负责路由，也不是 Query 的基础系统提示词，更不是程序安全控制。

它目前与 DEEP_LAYER / DEEP_EVIDENCE 有重复，包含具体工具选用细节。这是后续可以分层整理的对象；本次只改快速 Query，没有顺带改深度诊断。

## 快速 Query 实际收到什么

1. System：QUERY_COLLECT_PROMPT + Runbook 目录及说明 + QueryAnswer JSON schema。
2. 公共层：VISIBLE_OUTPUT_LANGUAGE_POLICY；Quick Query 设置 skip_remediation_policy=True，不追加旧修复审批提示片段。
3. User：当前用户问题 + UTC 时间 + QUERY_TASK_AUTHORITY_PREFIX + 路由合同。
4. Runtime：会话上下文、当前工具描述/schema、真实工具消息；必要时压缩后的记忆。

因此本次缩减的是主提示词（3,178 → 880 字符，减少 72.3%），并不表示模型全部输入只有 880 字符。没有把删掉的规则重新藏到公共片段。
轻量路径为 router → query_collect → END；query_collect 内可能多次 LLM/工具交互，不等于整轮只调一次模型。

## 本次设计与范围

旧 Query 将通用任务、具体命令、故障特例、单位规则、压缩处理和格式要求挤在一起：规则竞争、重复，维护时很难判断哪条真正生效。
新 Query 按 Role / Goal / Decision Policy / Boundaries / Completion / Output 组织，主提示词保留目标和证据/授权边界；调用参数由工具 schema 表达，领域方法由匹配 Runbook 提供，执行约束继续由现有执行层负责。

这是减少认知负担、便于评测和维护，不是准确率保证。没有改权限、路由、MCP、工具过滤、压缩、输出解析或监控配置；也没有添加固定采集步骤。普通操作路径的安全覆盖仍需单独审计，不能把提示词当作完整安全沙箱。
本次参考了 [OpenAI Prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering) 对 Identity / Instructions / Context 清晰分离及评测迭代的建议，不涉及模型迁移。

备份与恢复见 [prompt_backups/README.md](prompt_backups/README.md)。

## 全部定义与引用索引

“引用处”列列出 app 内读取常量的静态位置或动态查表入口。它证明代码可达引用，不保证每次请求都会执行。兼容模块中也有当前在用的联邦/压缩提示词，不能按文件夹名判定废弃。
定义位置采用仓库相对路径与行号；代码后续变化时以名称搜索为准。摘录只帮助识别内容，不是新的提示词。

### 主文件定义

| 名称 / 定义位置 | 使用条件 | 引用处 | 内容识别 |
|---|---|---|---|
| `PARALLEL_TARGETS_PROMPT`<br>app/core/prompts.py:124 | 当前自主深度分组、子任务或 fan-in 汇总 | `app/core/workflow/nodes/autonomous_parallel.py:54` | 从用户原问题和已经采集的定位材料中，整理需要独立诊断的 Pod 目标，输出给定 JSON。 这是任务分配，不是根因判断。只能引用材料中实际出现的 namespace 和 Pod 名称，不能猜测对象或扩大用户范围。 用户指 |
| `PARALLEL_LANE_PROMPT`<br>app/core/prompts.py:131 | 当前自主深度分组、子任务或 fan-in 汇总 | `app/core/workflow/nodes/autonomous_diagnosis.py:43` | 当前处于独立 Pod 诊断分支，diagnosis_target 是本分支对象和待调查问题。 question 和 request_contract 是当前子任务；original_question/original_r |
| `CONTEXT_SUMMARY_PROMPT`<br>app/core/prompts.py:138 | 当前工作历史或跨节点材料超预算时；保留近期完整交互，压缩较早材料 | `app/core/aicall/working_context.py:12 (别名 SUMMARY_PROMPT；摘要调用使用此别名)` | 整理运维 Agent 的工作记忆，不回答用户，不调用工具。 依据 original_question，把已有工作摘要与历史合并为可继续执行的工作记忆。 保留原任务/范围、已完成检查及参数、真实数值/标签/时间/单位/表达 |
| `QUERY_COLLECT_PROMPT`<br>app/core/prompts.py:150 | 当前 auto 的 focused 路由或显式 direct | `app/core/workflow/nodes/query_answer.py:119` | # Role 你是 Kubernetes 智能运维 Agent，负责资源查询、状态检查、故障分析、可观测数据分析、知识解释及授权范围内的普通资源操作。 # Goal 准确理解用户问题、目标对象、查询范围及预期结果，以必要 |
| `POD_REMEDIATION_PROMPT`<br>app/core/prompts.py:182 | 修复规划节点；深度总结也复用，不等于执行授权 | `app/core/workflow/nodes/remediation.py:80`<br>`app/core/workflow/nodes/query_answer.py:195` | 根据用户当前需求和真实观测，自主制定 Kubernetes 修复方案；此规划节点只取证，不提前执行写操作。 结合会话理解目标、范围和授权，按需要选择工具、Runbook 与 Metrics/Logging/Tracing |
| `REQUEST_ROUTER_PROMPT`<br>app/core/prompts.py:194 | auto 路由任务识别及对应重试 | `app/core/workflow/nodes/request_router.py:36`<br>`app/core/workflow/nodes/request_router.py:98` | 理解当前用户的 Kubernetes 运维意图，输出 RequestContract JSON；不查询环境、不预判根因、不制定工具清单。 识别用户对 Metrics/Prometheus、Logging、Tracing  |
| `DEEP_LAYER_PROMPT`<br>app/core/prompts.py:210 | 当前自主深度诊断相应阶段 | `app/core/workflow/nodes/autonomous_diagnosis.py:21` | # 唯一职责：定位用户所问的对象和异常现象 定位不局限于 Pod phase：用户所问的资源用量、请求错误或延迟需可观测性证据时，可用 Prometheus、日志或链路做必要定位，保留来源交接；详细多维取证仍交给 Evi |
| `DIAGNOSTIC_TOOL_GUIDANCE`<br>app/core/prompts.py:230 | 当前深度定位/取证，collect=True；不注入快速 Query 或 RCA | `app/core/workflow/nodes/autonomous_diagnosis.py:45` | 通用取证约定： 主动利用 Metrics、Logging、Tracing 与 Kubernetes 交叉取证，不将 get/describe/events 视为唯一信息源。资源压力优先 Prometheus 实测值/趋势 |
| `DEEP_EVIDENCE_PROMPT`<br>app/core/prompts.py:242 | 当前自主深度诊断相应阶段 | `app/core/workflow/nodes/autonomous_diagnosis.py:87` | # 唯一职责：为用户的问题采集具有区分力的根因证据 原问题决定范围，上游定位草稿只帮助导航。回答哪些事实支持候选原因、哪些反驳它、还缺什么；不写最终根因报告或修复方案。本路径没有程序生成的首轮采证计划，由你根据实际问题自 |
| `DEEP_RCA_PROMPT`<br>app/core/prompts.py:260 | 当前自主深度诊断相应阶段 | `app/core/workflow/nodes/autonomous_diagnosis.py:93` | # 唯一职责：依据已有真实证据判断用户所问现象的原因 主动对照已采集的 Prometheus/Metrics、Logging、Tracing 与 Kubernetes 证据，解释相互支持、冲突及采样边界，不只复述状态和事 |
| `QUERY_CONCLUSION_PROMPT`<br>app/core/prompts.py:283 | 当前深度诊断总结；不是快速 Query 必经节点 | `app/core/workflow/nodes/query_answer.py:186` | 根据用户原问题、本次工具返回和查询 Agent 草稿，整理最终中文 Markdown 回答。 保留对回答有用的多维观测：Prometheus 实测值与时间窗、关键日志、链路/依赖观察及其来源；不要在总结时只剩 Pod 状 |
| `DEEP_CONCLUSION_PRESENTATION`<br>app/core/prompts.py:312 | 当前自主深度诊断相应阶段 | `app/core/workflow/nodes/query_answer.py:188` | # 深度报告职责（沿用原四节点报告风格，适配当前输入） 根据用户原问题，将 RCA 草稿与真实工具观察组织成简洁、可审计的报告；不调用工具、不重新扩大调查范围。草稿不是程序核验结论，本路径没有“正式 RCA 已通过发布校 |
| `SYSTEM_PROMPT`<br>app/core/prompts.py:349 | 仅再导出，未发现 app 内作为请求系统提示词消费 | 未发现运行时读取；见上文说明 | # 角色 你是 **K8s-SRE Agent**，专业的 Kubernetes 运维助手。你需要运用你的能力以及工具还有额外的runbooks来精准定位到用户提问的问题所在， 如果用户问一些简单的基础性问题，可以直接回 |
| `LAYER_CLASSIFIER_PROMPT`<br>app/core/prompts.py:432 | 旧定位/结构化提取/失败重试路径 | layer → layer_classifier.py:117 | # 唯一职责：定位当前异常实体 只回答三件事：哪些 Pod 当前异常、它们表现为什么状态、如何拆成独立异常组。输出 'HEALTHY / ABNORMAL'，不分析根因，不深度采证，不写报告或修复方案。 # 定位步骤 1 |
| `LAYER_EXTRACT_PROMPT`<br>app/core/prompts.py:460 | 旧定位/结构化提取/失败重试路径 | layer_extract → layer_classifier.py:122 | 根据已有工具分析生成 'LayerOutput'；不要调用工具或补充新事实。 只做当前状态提取： 1. 先保留用户范围内当前仍异常的全部 Pod，再填写状态关键字和异常组。 2. 有活跃异常输出 'ABNORMAL'；没 |
| `LAYER_QUERY_DIRECT_PROMPT`<br>app/core/prompts.py:476 | 旧定位/结构化提取/失败重试路径 | layer_query_direct → layer_classifier.py:116 | # 目标：用真实工具直接回答窄查询 - 如果是 QUERY，你必须调用工具采集真实数据，并在本轮最终 JSON 中直接输出 'query_result' - 最终输出必须是纯 JSON，不要输出 Markdown、解释文 |
| `LAYER_QUERY_DIRECT_EXTRACT_PROMPT`<br>app/core/prompts.py:513 | 旧定位/结构化提取/失败重试路径 | layer_query_direct_extract → layer_classifier.py:121 | 你是 K8s 问题分层专家。根据分析文本生成 'LayerOutput' Pydantic 结构化结果，不要调用工具。 - 如果文本显示用户是在 QUERY，并且已经有足够的真实查询结果，请填充 'query_resul |
| `EVIDENCE_COLLECTOR_PROMPT`<br>app/core/prompts.py:529 | 旧证据采集节点，经 registry 获取 | evidence → evidence_collector.py:991,1267 | # 唯一职责：为当前作用域采集根因证据 只调查 'layer_handoff' 指定的实体。根据真实工具结果回答：哪些事实支持候选原因、哪些事实反驳它、还缺什么。不要写最终根因报告或修复方案。 # 工作方式 1. 执行代 |
| `EVIDENCE_PLAN_PROTOCOL_DYNAMIC`<br>app/core/prompts.py:559 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:2697` | - 用 'EvidencePlanOutput' 生成最小采证计划，然后调用真实只读工具执行。 - 计划只描述待验证问题，不是证据；tool 必须来自 Available tools。 - 至少执行一个 critical |
| `EVIDENCE_PLAN_PROTOCOL_PREPLANNED`<br>app/core/prompts.py:563 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:2693` | - 直接执行已有 'EvidencePlanOutput'，不要重写计划。 - 优先满足每项 purpose；工具不适合时选择 Available tools 中语义正确的只读工具。 - 只把实际完成的 tool_res |
| `EVIDENCE_PLAN_PROTOCOL_EXISTING`<br>app/core/prompts.py:567 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:2691` | - 直接执行已有 evidence_plan，不重新规划。 - 保持计划中的实体范围，按 purpose 选择语义正确的只读工具。 - 只把实际完成的 tool_result 记为已采集；不要新增虚假的已完成项。 |
| `EVIDENCE_USER_MESSAGE_TEMPLATE`<br>app/core/prompts.py:571 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:2702` | # 用户原始问题 {question} # 上游定位结构化结果 layer_handoff {compact_handoff} {abnormal_summary_section} {matched_runbook_co |
| `TOOL_OBSERVATION_SUMMARIZER_PROMPT`<br>app/core/prompts.py:605 | 重型工具摘要启用且命中摘要分支时；不是工作记忆压缩 | tool_observation_summarizer → aicall/client.py:4065（重型工具摘要） | 你是工具输出压缩器，不是诊断 Agent。 # 任务 只基于输入的单次工具输出总结事实，把大段 observation 压缩成主 Agent 可继续推理的短摘要。 输入中可能包含 rule-based current_s |
| `ROOT_CAUSE_ANALYZER_PROMPT`<br>app/core/prompts.py:636 | 旧 RCA / 报告输出对应模式 | rca → root_cause_analyzer.py:109 | # 唯一职责：判断当前现象的根本原因 不调用工具，不重新采集或复述完整报告。输入包含 Evidence Agent 的有界自然语言分析、每次真实工具调用唯一的一份高价值摘要、工具失败边界和归档引用。自然语言分析只帮助组织 |
| `CONCLUSION_FORMATTER_PROMPT`<br>app/core/prompts.py:684 | 旧 RCA / 报告输出对应模式 | conclusion → conclusion_formatter.py:747 | # 角色 你是 K8s 诊断报告 Agent。你只负责把输入中的正式 RCA 与真实工具事实组织成 简洁、可审计的 Markdown 报告，不重新判断工具结果，不提供修复方案。 # 唯一事实边界 - 只用真实数据：数值、 |
| `GROUP_EVIDENCE_SUMMARY_PROMPT`<br>app/core/prompts.py:765 | 未发现 app 内运行时消费 | 未发现运行时读取；见上文说明 | 你是 Kubernetes 单组证据分析器。输入包含本组允许分析的实体，以及按实体和 Kubernetes/Metrics/Logging/Tracing 聚合的真实事实。 输出必须严格符合 GroupDiagnosis |
| `REMEDIATION_PLAN_PROMPT`<br>app/core/prompts.py:781 | 旧修复规划模板；未发现 app 内运行时消费 | 未发现运行时读取；见上文说明 | 在报告末尾额外输出一个 '## 🧩 结构化修复计划' 区块，必须包含一个 JSON fenced block。 要求: - 如果不适合修复，输出 '"remediation_available": false' 和空 a |
| `LAYER_CLASSIFIER_PROMPT_EN`<br>app/core/prompts.py:853 | 语言兼容别名：与中文原常量相同，不是另一个英文提示词 | WORKFLOW_PROMPTS_I18N.en → get_workflow_prompt（仍为中文内容） | 别名 / 注册表 |
| `LAYER_EXTRACT_PROMPT_EN`<br>app/core/prompts.py:854 | 语言兼容别名：与中文原常量相同，不是另一个英文提示词 | WORKFLOW_PROMPTS_I18N.en → get_workflow_prompt（仍为中文内容） | 别名 / 注册表 |
| `LAYER_QUERY_DIRECT_PROMPT_EN`<br>app/core/prompts.py:855 | 语言兼容别名：与中文原常量相同，不是另一个英文提示词 | WORKFLOW_PROMPTS_I18N.en → get_workflow_prompt（仍为中文内容） | 别名 / 注册表 |
| `LAYER_QUERY_DIRECT_EXTRACT_PROMPT_EN`<br>app/core/prompts.py:856 | 语言兼容别名：与中文原常量相同，不是另一个英文提示词 | WORKFLOW_PROMPTS_I18N.en → get_workflow_prompt（仍为中文内容） | 别名 / 注册表 |
| `EVIDENCE_COLLECTOR_PROMPT_EN`<br>app/core/prompts.py:857 | 语言兼容别名：与中文原常量相同，不是另一个英文提示词 | WORKFLOW_PROMPTS_I18N.en → get_workflow_prompt（仍为中文内容） | 别名 / 注册表 |
| `TOOL_OBSERVATION_SUMMARIZER_PROMPT_EN`<br>app/core/prompts.py:858 | 语言兼容别名：与中文原常量相同，不是另一个英文提示词 | WORKFLOW_PROMPTS_I18N.en → get_workflow_prompt（仍为中文内容） | 别名 / 注册表 |
| `ROOT_CAUSE_ANALYZER_PROMPT_EN`<br>app/core/prompts.py:859 | 语言兼容别名：与中文原常量相同，不是另一个英文提示词 | WORKFLOW_PROMPTS_I18N.en → get_workflow_prompt（仍为中文内容） | 别名 / 注册表 |
| `CONCLUSION_FORMATTER_PROMPT_EN`<br>app/core/prompts.py:860 | 语言兼容别名：与中文原常量相同，不是另一个英文提示词 | WORKFLOW_PROMPTS_I18N.en → get_workflow_prompt（仍为中文内容） | 别名 / 注册表 |
| `REMEDIATION_PLAN_PROMPT_EN`<br>app/core/prompts.py:861 | 旧模板别名；未发现 app 内运行时消费 | 仅为中文常量别名，未发现运行时调用 | 别名 / 注册表 |
| `QUERY_CONCLUSION_INSTRUCTION_ZH`<br>app/core/prompts.py:870 | 旧 RCA / 报告输出对应模式 | get_conclusion_mode_instruction → conclusion_formatter.py:1005 | 请基于以上各阶段的分析结果，直接回答用户的查询「{question}」。 必须输出结构化、易读的 Markdown，不要输出原始结构化数据，不要把 evidence_plan 或 llm_analysis 原样贴给用户。 |
| `WORKFLOW_PROMPTS_I18N`<br>app/core/prompts.py:925 | 兼容节点与工具摘要动态查表；不是独立提示词 | get_workflow_prompt() 内部动态查表 | 别名 / 注册表 |
| `FEDERATION_AGENT_PROMPT`<br>app/core/prompts.py:953 | 联邦多集群路由、汇总或报告压缩 | `app/core/federation/agent.py:106` | # 角色 你是多集群 Kubernetes 查询路由器。你的唯一职责是：理解用户意图 → 路由到正确集群 → 忠实转发子集群结果，并把结果排版成可读的结构化报告。 # 核心原则 - 你不在主集群做深入诊断；诊断与取数由子 |
| `get_conclusion_mode_instruction`<br>app/core/prompts.py:1089 | 旧 RCA / 报告输出对应模式 | `app/core/workflow/nodes/conclusion_formatter.py:1005` | 获取 conclusion 节点的模式级指令，避免在节点代码里散落内联提示词。 |
| `get_query_evidence_normalization_prompt`<br>app/core/prompts.py:1111 | 兼容函数；当前直接返回空字符串 | `app/core/workflow/nodes/evidence_collector.py:889` | QUERY-evidence 兼容路径已停用，保留空返回以避免散落改动。 |
| `get_workflow_prompt`<br>app/core/prompts.py:1116 | 按下列引用处调用 | `app/core/aicall/client.py:4065`<br>`app/core/workflow/nodes/conclusion_formatter.py:747`<br>`app/core/workflow/nodes/layer_classifier.py:117`<br>`app/core/workflow/nodes/layer_classifier.py:122`<br>`app/core/workflow/nodes/layer_classifier.py:116`<br>`app/core/workflow/nodes/layer_classifier.py:121`<br>`app/core/workflow/nodes/evidence_collector.py:1267`<br>`app/core/workflow/nodes/evidence_collector.py:991`<br>`app/core/workflow/nodes/root_cause_analyzer.py:109` | 获取指定节点的 Prompt  Args:     node_id: 节点ID (layer/evidence/rca/conclusion)     prompt_language: Prompt 语言（zh/en）     response_language: 用户侧最终输出语言（当前仅 conclusion 使用）  Returns:     对应的 Prompt 字符串 |

### task_context 分层片段

| 名称 / 定义位置 | 使用条件 | 引用处 | 内容识别 |
|---|---|---|---|
| `AUTONOMOUS_RUNBOOK_CATALOG_HEADER`<br>app/core/prompt_catalog/task_context.py:7 | 当前消息、目录或工具描述拼接；以引用处调用者为准 | `app/core/workflow/nodes/autonomous_diagnosis.py:46` | Runbook 目录（匹配当前异常时读取，已读可复用）： |
| `PARALLEL_LANE_TASK_PREFIX`<br>app/core/prompt_catalog/task_context.py:8 | 当前自主深度分组、子任务或 fan-in 汇总 | `app/core/workflow/nodes/autonomous_diagnosis.py:43` | 本分支任务： |
| `PARALLEL_LANE_QUESTION_TEMPLATE`<br>app/core/prompt_catalog/task_context.py:9 | 当前自主深度分组、子任务或 fan-in 汇总 | `app/core/workflow/nodes/autonomous_parallel.py:109` | 本分支只诊断 {namespace}/{name}：{question} |
| `PARALLEL_FANIN_INSTRUCTION`<br>app/core/prompt_catalog/task_context.py:10 | 当前自主深度分组、子任务或 fan-in 汇总 | `app/core/workflow/nodes/autonomous_parallel.py:188` | 各 Pod 分支已结束；请按 parallel_results 中的各组证据和限制汇总，不把分支完成等同于根因确认。 |
| `FOCUSED_RUNBOOK_DESCRIPTION_PREFIX`<br>app/core/prompt_catalog/task_context.py:14 | 当前消息、目录或工具描述拼接；以引用处调用者为准 | `app/core/workflow/nodes/focused.py:81` | 读取相关运维参考资料，不会执行诊断。仅使用与当前问题相关的知识，手册步骤不是强制工具计划，也不是环境事实。可用 runbook_id： |
| `QUERY_RUNBOOK_DESCRIPTION`<br>app/core/prompt_catalog/task_context.py:18 | 当前消息、目录或工具描述拼接；以引用处调用者为准 | `app/core/workflow/nodes/query_answer.py:75` | 读取指定 Runbook 全文作为参考。按原问题选取相关知识，不要求执行全部步骤；手册不是环境事实。 |
| `FOCUSED_REQUEST_TIME_TEMPLATE`<br>app/core/prompt_catalog/task_context.py:21 | 当前消息、目录或工具描述拼接；以引用处调用者为准 | `app/core/workflow/nodes/focused.py:89` | 本次执行开始时间（UTC）：{request_time}；相对时间以此为基准，实际数据时间以工具返回为准。 |
| `QUERY_TASK_AUTHORITY_PREFIX`<br>app/core/prompt_catalog/task_context.py:24 | 当前消息、目录或工具描述拼接；以引用处调用者为准 | `app/core/workflow/nodes/query_answer.py:117` | 任务理解（以原问题为准）： |
| `QUERY_RUNBOOK_CATALOG_HEADER`<br>app/core/prompt_catalog/task_context.py:25 | 当前消息、目录或工具描述拼接；以引用处调用者为准 | `app/core/workflow/nodes/query_answer.py:120` | 可用 Runbook 目录（按需读取）： |

### runtime_policy 分层片段

| 名称 / 定义位置 | 使用条件 | 引用处 | 内容识别 |
|---|---|---|---|
| `RUNBOOK_CATALOG_INSTRUCTION`<br>app/core/prompt_catalog/runtime_policy.py:28 | BaseNode.should_inject_runbook_catalog() 为真且目录非空；快速 Query 使用自己的目录组装 | `app/core/workflow/nodes/base.py:425` | If one or more runbooks match the issue, use the fetch_runbook tool for each relevant runbook. |
| `REMEDIATION_AUTO_MODE_LINE`<br>app/core/prompt_catalog/runtime_policy.py:7 | 同上，模式 auto | `app/core/workflow/nodes/base.py:456` | 当前修复模式为 auto：结构化修复计划中的安全动作可由修复执行器自动审批并执行。 |
| `REMEDIATION_REVIEW_MODE_LINE`<br>app/core/prompt_catalog/runtime_policy.py:8 | 同上，模式 review | `app/core/workflow/nodes/base.py:458` | 当前修复模式为 review：结构化修复计划中的所有写动作必须先经过人工审批。 |
| `REMEDIATION_POLICY_TEMPLATE`<br>app/core/prompt_catalog/runtime_policy.py:10 | BaseNode 未 skip_remediation_policy 时；当前自主 Query/深度显式跳过 | `app/core/workflow/nodes/base.py:459` | # 修复计划与审批约束 - {mode_line} - 诊断节点不要直接执行 kubectl apply/patch/delete/rollout/scale 等写操作。 - 如果当前证据确认存在标准、安全、可验证的修复 |
| `VISIBLE_OUTPUT_LANGUAGE_POLICY`<br>app/core/prompt_catalog/runtime_policy.py:18 | BaseNode 调用时追加中文及简短说明要求 | `app/core/workflow/nodes/base.py:467` | # 语言与可见输出约束 - 全部可见输出必须使用中文，包括分析说明、工具调用前后的说明、结构化字段内的解释文本。 - 需要推理时只给结论性、可验证的简短说明，并优先调用工具获取事实。 |
| `DIAGNOSIS_CONCLUSION_REMEDIATION_CONSTRAINT`<br>app/core/prompt_catalog/runtime_policy.py:24 | 深度总结附修复方案时，限制于已知证据 | `app/core/workflow/nodes/query_answer.py:196` | 当前为诊断总结，无新增工具调用。仅在既有真实证据足以核实对象身份和修复参数时附上修复计划；否则 actions 留空并说明需要补查。诊断报告仍是主任务，不因没有计划而省略诊断结论。 |

### context_policy 分层片段

| 名称 / 定义位置 | 使用条件 | 引用处 | 内容识别 |
|---|---|---|---|
| `LEGACY_COMPACTION_USER_TEMPLATE`<br>app/core/prompt_catalog/context_policy.py:21 | 同上，旧压缩用户消息 | `app/core/workflow/nodes/base.py:718` | 请压缩以下内容（原始 {original_chars} 字符，目标 {max_chars} 字符以内）： {text} |
| `WORKING_CONTEXT_SUMMARY_PREFIX`<br>app/core/prompt_catalog/context_policy.py:7 | 当前工作记忆摘要替换后注入 | `app/core/aicall/working_context.py:264` | [working_context_summary] 以下是较早工作的有损摘要；后续保留消息可能更新这些事实。不是新用户请求： |
| `RUNTIME_COMPACTION_INSTRUCTION`<br>app/core/prompt_catalog/context_policy.py:11 | AICall 旧运行时压缩分支；不等于当前工作历史替换策略 | `app/core/aicall/client.py:3860` | 压缩 evidence 运行上下文。保留关键过程、计划、已完成/未完成证据、正向事实、负向事实、冲突和下一步焦点。若模型陷入重复工具或钻牛角尖，请抓大放小，把重复/无关节点容量、长 JSON、重复 describe 归入 |
| `RUNTIME_COMPACTION_BUDGET_EXCEEDED_INSTRUCTION`<br>app/core/prompt_catalog/context_policy.py:17 | AICall 旧运行时压缩分支；不等于当前工作历史替换策略 | `app/core/aicall/client.py:3917` | 压缩 evidence 上下文，保留计划、工具事实、错误和证据引用。 |

### compatibility 分层片段

| 名称 / 定义位置 | 使用条件 | 引用处 | 内容识别 |
|---|---|---|---|
| `FOCUSED_PROMPT`<br>app/core/prompt_catalog/compatibility.py:18 | 旧 FocusedTaskNode.execute；当前 auto 的 focused 实际映射 QueryCollectNode | `app/core/workflow/nodes/focused.py:90` | 完成用户提出的具体 Kubernetes 运维任务。原始问题决定目标，任务合同用于保留范围与输出要求。 自主选择必要的只读工具，获得足够证据后停止。不预设 get pod -A，不因发现异常就转为全局排障。 先按用户 n |
| `FOCUSED_RESULT_PROMPT`<br>app/core/prompt_catalog/compatibility.py:37 | 旧 FocusedTaskNode 结果结构化补充 | `app/core/workflow/nodes/focused.py:107` | 只根据本次真实工具记录回答用户原问题，输出 FocusedResult。分析草稿不是事实。工具没有采到的数据不得从草稿补入。环境结论必须引用给出的 raw_ref。空结果和失败不同；范围或指标未覆盖写入 missing， |
| `LEGACY_CONTEXT_COMPRESSION_PROMPT`<br>app/core/prompt_catalog/compatibility.py:46 | BaseNode 旧压缩方法调用时，不是 working_context 主策略 | `app/core/workflow/nodes/base.py:708` | 你是一个信息压缩专家。将以下内容压缩为精炼摘要。 规则： 1. 保留所有工具调用记录：工具名 + 关键结果（具体数值、状态、错误信息） 2. 保留所有异常发现（Pod 状态异常、错误码、资源超限等） 3. 保留关键实体（ |
| `CASE_REFINEMENT_PROMPT`<br>app/core/prompt_catalog/compatibility.py:57 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:1728` | 你负责在实时 AIOps Case 之后做一次窄范围证据补全。你只选择是否展开真实 evidence ref 或调用已启用的 AIOps 细粒度查询；不得按故障类型套规则，不得生成根因或修复结论。 |
| `RUNBOOK_RECONCILIATION_PROMPT`<br>app/core/prompt_catalog/compatibility.py:63 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:1957` | 你负责根据实时可观测性证据重新裁决诊断 Runbook。 只允许调用 fetch_runbook；不得调用 Kubernetes、日志、指标、Trace、case 或修复工具。 Runbook 的选择由你完成，宿主不会按 |
| `EVIDENCE_MEMORY_COMPRESSION_PROMPT`<br>app/core/prompt_catalog/compatibility.py:67 | AICall 旧运行时压缩分支；不等于当前工作历史替换策略 | `app/core/aicall/client.py:3974` | 你是 K8s AIOps evidence 上下文压缩器。 任务：把冗长的中间思考和工具输出压缩成结构化摘要，帮助后续模型继续诊断。 要求： - 保留重要事实，不编造。 - 体现过程顺序，用“先...随后...最后... |
| `FEDERATION_SYNTHESIS_PROMPT`<br>app/core/prompt_catalog/compatibility.py:76 | 联邦多集群路由、汇总或报告压缩 | `app/core/federation/aggregator.py:245` | # 角色定义 你是多集群 Kubernetes 运维协调专家。以下是各子集群独立执行诊断后的报告，每份报告都由子集群的 AIOps Agent 生成。 # 核心任务 综合分析所有子集群的报告，输出一份**高度结构化**的 |
| `FEDERATION_COMPRESSION_PROMPT`<br>app/core/prompt_catalog/compatibility.py:219 | 联邦多集群路由、汇总或报告压缩 | `app/core/federation/aggregator.py:34` | 以下是某 Kubernetes 集群的诊断报告，请压缩为简洁摘要，保留： - 集群名称/标识 - 主要问题列表（按严重程度排序） - 根因分析（如有） - 关键证据（Pod 名称、错误信息、关键指标） - 修复建议摘要  |
| `LEGACY_REMEDIATION_AGENT_PROMPT`<br>app/core/prompt_catalog/compatibility.py:232 | 修复 Agent 执行循环；名字 legacy 不表示未使用 | `app/core/remediation/agent.py:344` | 你是 Kubernetes 修复执行 Agent。你只根据诊断报告、修复计划和真实 observation 决定下一步。 必须输出一个 JSON 对象，不要输出 Markdown： { "decision": "run_ |
| `LEGACY_QUERY_CONCLUSION_PROMPT`<br>app/core/prompt_catalog/compatibility.py:6 | 旧 RCA / 报告输出对应模式 | `app/core/workflow/nodes/conclusion_formatter.py:754` | 你是 K8s 查询结果总结器。 任务：把输入中的 'QUERY 结构化结果' 和真实工具数据总结为面向用户的 Markdown。 输出契约：只输出一个 JSON 对象，schema 为 '{"markdown_repor |

### handoff 分层片段

| 名称 / 定义位置 | 使用条件 | 引用处 | 内容识别 |
|---|---|---|---|
| `LAYER_QUERY_RETRY_SUFFIX`<br>app/core/prompt_catalog/handoff.py:3 | 旧定位/结构化提取/失败重试路径 | `app/core/workflow/nodes/layer_classifier.py:461` | # 上一轮结果被系统拒绝 - 原因：你给出了 QUERY 结论，但没有提供足够的真实工具执行结果。 - 本轮必须先执行工具，再让 Pydantic 结构化提取生成最终 query_result。 - 在出现至少一次成功的 |
| `LAYER_EXPLICIT_POD_MUST_VERIFY`<br>app/core/prompt_catalog/handoff.py:14 | 旧定位/结构化提取/失败重试路径 | `app/core/workflow/nodes/layer_classifier.py:952` | 本轮仅验证用户明确指定的 namespace + Pod 列表；全局扫描中的其他异常只作为背景 逐一确认每个目标 Pod 当前仍存在于指定 namespace 逐一确认每个目标 Pod 的 active_signals  |
| `LAYER_GENERAL_MUST_VERIFY`<br>app/core/prompt_catalog/handoff.py:21 | 旧定位/结构化提取/失败重试路径 | `app/core/workflow/nodes/layer_classifier.py:954` | 以 abnormal_groups、abnormal_pods、current_abnormal_summary 为覆盖基准 异常组完整/最小验证由 evidence 节点按 abnormal_groups 覆盖，避免遗 |
| `LAYER_HANDOFF_DO_NOT_CHANGE`<br>app/core/prompt_catalog/handoff.py:30 | 旧定位/结构化提取/失败重试路径 | `app/core/workflow/nodes/layer_classifier.py:988` | 不要把上游 namespace、Pod、Service、Node 名称改写成其他对象 不要把历史 event 当成当前故障 不要把计划或工具名当成证据，必须基于 tool_result |
| `LAYER_SCENARIO_VERIFICATION_REASON`<br>app/core/prompt_catalog/handoff.py:36 | 旧定位/结构化提取/失败重试路径 | `app/core/workflow/nodes/layer_classifier.py:1721` | 当前阶段只定位异常；根因必须由后续实时 canonical facts 确认 |
| `LAYER_EXPLICIT_POD_BASELINE_TEMPLATE`<br>app/core/prompt_catalog/handoff.py:38 | 旧定位/结构化提取/失败重试路径 | `app/core/workflow/nodes/layer_classifier.py:2107` | {question} # 代码预采集的显式 Pod 定位结果 以下结果已经按用户给出的 namespace/Pod 列表真实并行执行。它们是目标清单与当前状态事实，不是根因结论。不得遗漏目标，也不要机械重复相同查询；如结 |
| `LAYER_EXTRACT_INSTRUCTION`<br>app/core/prompt_catalog/handoff.py:47 | 旧定位/结构化提取/失败重试路径 | `app/core/workflow/nodes/layer_classifier.py:2254` | 基于 layer 阶段工具结果和分析文本生成 Pydantic LayerOutput |
| `LAYER_QUERY_RETRY_EXTRACT_INSTRUCTION`<br>app/core/prompt_catalog/handoff.py:48 | 旧定位/结构化提取/失败重试路径 | `app/core/workflow/nodes/layer_classifier.py:2329` | 基于 QUERY direct 严格重试后的工具结果生成 Pydantic LayerOutput |
| `PARALLEL_DIAGNOSIS_RETRY_INSTRUCTION`<br>app/core/prompt_catalog/handoff.py:50 | 旧 parallel_evidence 分组或门禁失败重试分支 | `app/core/workflow/nodes/parallel_evidence.py:745` | Start one fresh ReAct investigation focused on the failed gate. Keep valid facts, collect only missing evidenc |
| `PARALLEL_DIAGNOSIS_RETRY_QUESTION_TEMPLATE`<br>app/core/prompt_catalog/handoff.py:56 | 旧 parallel_evidence 分组或门禁失败重试分支 | `app/core/workflow/nodes/parallel_evidence.py:762` | {question} （第一次诊断未通过最小证据门禁；请用一次新的完整 ReAct 调查解决反馈中的缺口。） |
| `PARALLEL_GROUP_MUST_VERIFY_TEMPLATE`<br>app/core/prompt_catalog/handoff.py:61 | 旧 parallel_evidence 分组或门禁失败重试分支 | `app/core/workflow/nodes/parallel_evidence.py:871` | 只诊断本组实体 {entities}，不要采集其他 namespace/Pod 的证据 |
| `PARALLEL_GROUP_QUESTION_TEMPLATE`<br>app/core/prompt_catalog/handoff.py:65 | 旧 parallel_evidence 分组或门禁失败重试分支 | `app/core/workflow/nodes/parallel_evidence.py:882` | 原始用户任务：{original_question} 以下是该任务内分配给本节点的子任务，不替代原始任务： 只调查 {entities}；初始状态为 {status}。用真实工具事实判断其当前异常、已恢复或证据不足，不查 |

### evidence 分层片段

| 名称 / 定义位置 | 使用条件 | 引用处 | 内容识别 |
|---|---|---|---|
| `EVIDENCE_VALID_PLAN_RETRY_INSTRUCTION`<br>app/core/prompt_catalog/evidence.py:110 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:364` | 上一轮 evidence_plan 已有效，本轮不要重新输出 evidence_plan；请直接按既有计划调用至少一个 critical 或 important 级真实工具。 |
| `EVIDENCE_UPSTREAM_MUST_VERIFY`<br>app/core/prompt_catalog/evidence.py:114 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:630` | 基于真实 tool_result 重新验证上游定位 |
| `EVIDENCE_MISSING_POD_CONFLICT`<br>app/core/prompt_catalog/evidence.py:115 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:847` | 异常 Pod 当前不存在；历史事件或归档摘要不能继续作为该 Pod 当前异常的正向证据 |
| `EVIDENCE_STRICT_SYSTEM_RETRY_TEMPLATE`<br>app/core/prompt_catalog/evidence.py:118 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:1004` | # 本轮最低要求 - 失败原因：{failure_reason} - 至少执行一条 critical/important 只读工具；没有真实 tool_result 时不得声称采集完成。 |
| `EVIDENCE_COMPLETED_COLLECTION_TEMPLATE`<br>app/core/prompt_catalog/evidence.py:123 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:1639` | {user_message} # 已完成首轮采集摘要（不要用相同参数重复调用） {completed_summary} |
| `EVIDENCE_BASELINE_FAILURE_INSTRUCTION`<br>app/core/prompt_catalog/evidence.py:128 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:2205` | 检查错误并补齐/修正参数后重新调用；不得把本次失败写成无匹配数据 |
| `EVIDENCE_BASELINE_HANDOFF_TEMPLATE`<br>app/core/prompt_catalog/evidence.py:132 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:2217` | {user_message} # 代码预采集的三维可观测性 baseline 以下是 ReAct 启动前已真实并行执行的 Metrics、Logging、Tracing 工具结果，不是根因结论。先比较这些事实与 Kube |
| `EVIDENCE_DEFAULT_EXECUTION_REASON`<br>app/core/prompt_catalog/evidence.py:141 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:2676` | 请直接按既有计划执行工具 |
| `EVIDENCE_DEFAULT_STRICT_REASON`<br>app/core/prompt_catalog/evidence.py:142 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:1005`<br>`app/core/workflow/nodes/evidence_collector.py:2680` | 上一轮只返回计划，没有执行工具 |
| `EVIDENCE_ABNORMAL_SUMMARY_HEADER`<br>app/core/prompt_catalog/evidence.py:143 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:3241` | # 当前异常结构化摘要（必须优先审查） |
| `EVIDENCE_ABNORMAL_COUNTS_FALLBACK`<br>app/core/prompt_catalog/evidence.py:144 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:3249` | status_counts: 未提供；从 issue_groups/abnormal_pods 进行最小覆盖。 |
| `EVIDENCE_ABNORMAL_COVERAGE_REQUIREMENT`<br>app/core/prompt_catalog/evidence.py:147 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:3282` | 要求：非 Running/Completed/Succeeded/Ready/Bound/Active 的状态都需要至少最小验证；主异常组做完整验证，非主异常组验证当前状态 + 一个最关键事件/配置/依赖信号。 |
| `EVIDENCE_CONTINUE_GATE_REASON`<br>app/core/prompt_catalog/evidence.py:151 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:1617` | 继续执行尚未尝试的首轮 Metrics、Logging、Tracing、Topology 门控项 |
| `EVIDENCE_CONTINUE_MANDATORY_REASON`<br>app/core/prompt_catalog/evidence.py:152 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:1619` | 继续执行尚未尝试的 mandatory 实时可观测性采集项 |
| `EVIDENCE_PLAN_GENERATION_INSTRUCTION`<br>app/core/prompt_catalog/evidence.py:7 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:1164` | # 结构化计划生成模式 只生成最小 'EvidencePlanOutput'，不调用工具、不总结结论。每个计划项只表达一个待验证问题。 |
| `POST_CASE_REFINEMENT_TASK`<br>app/core/prompt_catalog/evidence.py:12 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:1725` | # 任务 - 只判断当前首屏事实是否足以回答用户问题；coverage=present 仅表示数据源存在，不等于诊断证据充分。 - 如关键判断缺少原文、时间序列、可关联 Trace 或责任边，调用一个或少量允许的细粒度  |
| `POST_CASE_RUNBOOK_RECONCILIATION_TASK`<br>app/core/prompt_catalog/evidence.py:25 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:1956` | # 任务 - 这是 evidence_plan 完成后的 Runbook 重新裁决，不得重写 evidence_plan，也不得采集新的环境证据。 - 由你根据每个异常 Pod 的 Kubernetes 终态、决定性日志 |
| `EVIDENCE_FAILED_OBSERVABILITY_RETRY_TEMPLATE`<br>app/core/prompt_catalog/evidence.py:34 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:2403` | # action=repair_failed_observability_once 用户问题：{question} 下面调用是 Metrics/Logging/Tracing/Topology 的真实执行失败，不是无匹配 |
| `EVIDENCE_EXISTING_PLAN_SECTION_TEMPLATE`<br>app/core/prompt_catalog/evidence.py:46 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:2674` | # 既有 evidence_plan 直接执行以下计划，不重新规划： {plan_lines} - {failure_reason} |
| `EVIDENCE_STRICT_RETRY_SECTION_TEMPLATE`<br>app/core/prompt_catalog/evidence.py:54 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:2679` | # 上一轮结果被系统拒绝 - 失败原因：{failure_reason} - 至少执行一个 critical/important 只读工具；没有 tool_result 时不得声称采集完成。 |
| `EVIDENCE_ARCHIVE_INSTRUCTIONS`<br>app/core/prompt_catalog/evidence.py:61 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:2686` | # context archive - context archive 已落盘，仅供人工排障；evidence 默认不要读取归档。 - 归档不是当前环境证据，不要把读取归档写入 evidence_plan。 |
| `EVIDENCE_HANDOFF_ARCHIVE_INSTRUCTION`<br>app/core/prompt_catalog/evidence.py:66 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:2688` | - layer handoff 已由上方 layer_handoff 注入；不要重复读取归档。 |
| `EVIDENCE_PLAN_PROTOCOL_REACT_ONLY`<br>app/core/prompt_catalog/evidence.py:69 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:2695` | - 代码会在 ReAct 前提供同一组 Metrics、Logging、Tracing baseline 真实结果。 - 不生成或复述 evidence_plan；根据 baseline 尚未回答的关键问题，自主选择少量 |
| `EVIDENCE_EXISTING_PLAN_OUTPUT_INSTRUCTION`<br>app/core/prompt_catalog/evidence.py:74 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:2711` | 直接执行既有 Pydantic evidence_plan 中的必要工具，最后输出简短证据结论。 |
| `EVIDENCE_DYNAMIC_OUTPUT_INSTRUCTION`<br>app/core/prompt_catalog/evidence.py:77 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:2713` | 调用必要真实工具后输出简短证据结论；不要手写 EvidenceCollectionOutput。 |
| `EVIDENCE_DIAGNOSIS_RETRY_TEMPLATE`<br>app/core/prompt_catalog/evidence.py:80 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:2732` | {message} # 第二次完整 ReAct 诊断上下文 根据门禁反馈重新调查未解决的问题。保留已有有效事实，必要时用只读工具补证；可以放弃第一次判断，不要只修 JSON，也不要重复完全相同的查询。 {retry_pa |
| `EVIDENCE_AUTONOMOUS_GUIDANCE_TEMPLATE`<br>app/core/prompt_catalog/evidence.py:88 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:2758` | # 自主可观测性组合查询 - 上游已确认的异常 Pod 候选：{rendered_targets}。 - 代码已安排 Kubernetes 与 Metrics、Logging、Tracing、Topology 首轮查询； |
| `EVIDENCE_LEGACY_GUIDANCE_TEMPLATE`<br>app/core/prompt_catalog/evidence.py:98 | 旧 evidence_collector 对应计划/补证/重试分支；当前自主证据节点不加载 | `app/core/workflow/nodes/evidence_collector.py:2761` | # 实时可观测性证据优先 - 上游已确认的异常 Pod 候选：{rendered_targets}。 - 诊断应优先依赖当前环境工具返回的真实证据，而不是 Runbook、名称、标签或模型经验推断。 - 每个已确认异常  |

### diagnosis 分层片段

| 名称 / 定义位置 | 使用条件 | 引用处 | 内容识别 |
|---|---|---|---|
| `RCA_COMPACT_OUTPUT_CONTRACT`<br>app/core/prompt_catalog/diagnosis.py:7 | 旧 RCA / 报告输出对应模式 | `app/core/workflow/nodes/root_cause_analyzer.py:910` | # 精简输出合同 只填写运行时 RCACompactOutput：现象、根因、最短因果链、置信度、未知项， 以及最多 8 条 key_evidence。causal_chain 按“上游原因 → 机制 → 直接失败 →  |
| `RCA_FULL_OUTPUT_CONTRACT`<br>app/core/prompt_catalog/diagnosis.py:16 | 旧 RCA / 报告输出对应模式 | `app/core/workflow/nodes/root_cause_analyzer.py:911` | # 完整输出合同 按运行时 RCAOutput schema 填写；只保留少量高价值 evidence_analysis， 不要为了填满辅助字段复制工具结果。 |
| `RCA_NO_RECOLLECT_POLICY`<br>app/core/prompt_catalog/diagnosis.py:22 | 旧 RCA / 报告输出对应模式 | `app/core/workflow/nodes/root_cause_analyzer.py:1103` | # ⚠️ 重要：不要重复采集数据 上面的「已采集证据」和「工具采集的原始数据」已经包含了所有需要的信息。 请直接基于这些数据进行分析，**不要重新调用工具采集数据**。 如果数据不足，在 limitations 中说明即 |
| `RCA_LITE_EVIDENCE_LOCATION_NOTE`<br>app/core/prompt_catalog/diagnosis.py:29 | 旧 RCA / 报告输出对应模式 | `app/core/workflow/nodes/root_cause_analyzer.py:1024` | 证据上下文只在 user message 中提供，system prompt 不承载动态证据。 |
| `RCA_REPAIR_INSTRUCTION`<br>app/core/prompt_catalog/diagnosis.py:33 | 旧 RCA / 报告输出对应模式 | `app/core/workflow/nodes/root_cause_analyzer.py:564` | 只修复 RCA 发布合同，不重新采集。若 previous_claim 的语义被事实支持，保留其内容并用本 payload 中精确 fact_id 填写顶层 supporting_fact_ids、唯一 hypothes |
| `RCA_FACT_LEDGER_POLICY`<br>app/core/prompt_catalog/diagnosis.py:40 | 旧 RCA / 报告输出对应模式 | `app/core/workflow/nodes/root_cause_analyzer.py:650` | Fact Ledger 是 AIOps 根因分析的主证据输入；只能引用当前 ledger 中的 fact_id。 |
| `RCA_NARRATIVE_EVIDENCE_POLICY`<br>app/core/prompt_catalog/diagnosis.py:44 | 旧 RCA / 报告输出对应模式 | `app/core/workflow/nodes/root_cause_analyzer.py:665` | Evidence Agent 的自然语言分析仅作为推理草稿；每个数值、状态、错误原文和最终判断仍必须由下方去重后的真实工具观察支撑。不注入 Fact Ledger、selected_facts、evidence_item |
| `RCA_QUALITY_POLICY`<br>app/core/prompt_catalog/diagnosis.py:50 | 旧 RCA / 报告输出对应模式 | `app/core/workflow/nodes/root_cause_analyzer.py:1716` | source_coverage/case_target_coverage 只表示采集覆盖，不能替代 diagnostic_sufficiency；未回答问题必须进入结论限制。 |
| `QUERY_REPORT_TOOL_DATA_HEADER`<br>app/core/prompt_catalog/diagnosis.py:55 | 旧 RCA / 报告输出对应模式 | `app/core/workflow/nodes/conclusion_formatter.py:1001` | # 工具采集的真实数据（必须引用） |
| `REPORT_FACT_AUTHORITY`<br>app/core/prompt_catalog/diagnosis.py:57 | 旧 RCA / 报告输出对应模式 | `app/core/workflow/nodes/conclusion_formatter.py:1820` | canonical normalized facts |
| `REPORT_FACT_AGGREGATION_POLICY`<br>app/core/prompt_catalog/diagnosis.py:58 | 旧 RCA / 报告输出对应模式 | `app/core/workflow/nodes/conclusion_formatter.py:1821` | repeated logs and equivalent L7 flows may be structurally grouped; counts, time ranges, numeric ranges, trace_ |
| `REPORT_METRIC_TREND_RULE`<br>app/core/prompt_catalog/diagnosis.py:62 | 旧 RCA / 报告输出对应模式 | `app/core/workflow/nodes/conclusion_formatter.py:1822` | metric trend is valid only when trend_evaluable=true and sample_count>=2 |
| `build_rca_user_message`<br>app/core/prompt_catalog/diagnosis.py:67 | 旧 RCA / 报告输出对应模式 | `app/core/workflow/nodes/root_cause_analyzer.py:1011` | 组装对应节点的用户消息。 |
| `build_diagnosis_report_instruction`<br>app/core/prompt_catalog/diagnosis.py:77 | 旧 RCA / 报告输出对应模式 | `app/core/workflow/nodes/conclusion_formatter.py:894` | 组装对应节点的用户消息。 |
| `build_diagnosis_report_user_message`<br>app/core/prompt_catalog/diagnosis.py:83 | 旧 RCA / 报告输出对应模式 | `app/core/workflow/nodes/conclusion_formatter.py:899` | 组装对应节点的用户消息。 |
| `build_query_report_user_message`<br>app/core/prompt_catalog/diagnosis.py:109 | 旧 RCA / 报告输出对应模式 | `app/core/workflow/nodes/conclusion_formatter.py:1010` | 组装对应节点的用户消息。 |
| `build_group_report_user_message`<br>app/core/prompt_catalog/diagnosis.py:123 | 旧 RCA / 报告输出对应模式 | `app/core/workflow/nodes/conclusion_formatter.py:1858` | 组装对应节点的用户消息。 |
