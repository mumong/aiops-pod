"""Evidence task fragments, exported through app.core.prompts.

Keep literal bytes stable; payload construction and execution gates belong to
the evidence node, not this catalog.
"""

EVIDENCE_PLAN_GENERATION_INSTRUCTION = (
    "\n\n# 结构化计划生成模式\n"
    "只生成最小 `EvidencePlanOutput`，不调用工具、不总结结论。每个计划项只表达一个待验证问题。\n"
)

POST_CASE_REFINEMENT_TASK = (
    "# 任务\n"
    "- 只判断当前首屏事实是否足以回答用户问题；coverage=present 仅表示数据源存在，"
    "不等于诊断证据充分。\n"
    "- 如关键判断缺少原文、时间序列、可关联 Trace 或责任边，调用一个或少量允许的"
    "细粒度 AIOps 工具补证。\n"
    "- `get_aiops_case_evidence` 只能使用上面真实给出的 case_id 与 "
    "recommended_refs_by_dimension，不得猜测 ref。\n"
    "- 当前证据已经决定性、没有冲突时允许零工具调用，并回答 "
    "`detail_retrieval: current_case_sufficient`。\n"
    "- 最多执行这一轮；禁止重新调用 collect_aiops_case、kubectl、Runbook 或修复工具。"
)

POST_CASE_RUNBOOK_RECONCILIATION_TASK = """# 任务
- 这是 evidence_plan 完成后的 Runbook 重新裁决，不得重写 evidence_plan，也不得采集新的环境证据。
- 由你根据每个异常 Pod 的 Kubernetes 终态、决定性日志、Trace 和错误码，自主判断现有 Runbook 是否仍准确。
- 如果实时证据把通用候选收敛成更具体异常，只调用 `fetch_runbook` 获取缺失且明显匹配的 Runbook。
- 已在“上游已经实际获取”列表中的 Runbook 禁止重复调用；同一新 Runbook 本轮最多调用一次。
- 不要求每个 Pod 都新增 Runbook。现有 Runbook 足够或没有可靠匹配时，不调用工具并明确回答 `runbook_reconciliation: keep_existing_or_none`。
- Runbook 是参考知识，不是真实环境证据；不得把名称、标签或 Runbook 内容写成已证实根因。
"""

EVIDENCE_FAILED_OBSERVABILITY_RETRY_TEMPLATE = (
    "# action=repair_failed_observability_once\n"
    "用户问题：{question}\n\n"
    "下面调用是 Metrics/Logging/Tracing/Topology 的真实执行失败，不是无匹配数据。"
    "本轮只处理这些失败：阅读原始错误和当前工具 schema，补齐或修正参数后，"
    "对同一 namespace/Pod 调用对应工具一次。不得原样重复完全相同的错误参数，"
    "不得因为其他维度已有结果而直接总结，也不要调用无关工具。成功但结果为空"
    "属于有效数据边界；修正后仍失败则保留原始错误并停止。必须先实际调用工具，"
    "再简短说明结果。\n"
    "{payload}\n"
)

EVIDENCE_EXISTING_PLAN_SECTION_TEMPLATE = """

# 既有 evidence_plan
直接执行以下计划，不重新规划：
{plan_lines}
- {failure_reason}
"""

EVIDENCE_STRICT_RETRY_SECTION_TEMPLATE = """

# 上一轮结果被系统拒绝
- 失败原因：{failure_reason}
- 至少执行一个 critical/important 只读工具；没有 tool_result 时不得声称采集完成。
"""

EVIDENCE_ARCHIVE_INSTRUCTIONS = (
    "# context archive",
    "- context archive 已落盘，仅供人工排障；evidence 默认不要读取归档。",
    "- 归档不是当前环境证据，不要把读取归档写入 evidence_plan。",
)
EVIDENCE_HANDOFF_ARCHIVE_INSTRUCTION = (
    "- layer handoff 已由上方 layer_handoff 注入；不要重复读取归档。"
)
EVIDENCE_PLAN_PROTOCOL_REACT_ONLY = (
    "- 代码会在 ReAct 前提供同一组 Metrics、Logging、Tracing baseline 真实结果。\n"
    "- 不生成或复述 evidence_plan；根据 baseline 尚未回答的关键问题，"
    "自主选择少量只读工具专项补查。"
)
EVIDENCE_EXISTING_PLAN_OUTPUT_INSTRUCTION = (
    "直接执行既有 Pydantic evidence_plan 中的必要工具，最后输出简短证据结论。"
)
EVIDENCE_DYNAMIC_OUTPUT_INSTRUCTION = (
    "调用必要真实工具后输出简短证据结论；不要手写 EvidenceCollectionOutput。"
)
EVIDENCE_DIAGNOSIS_RETRY_TEMPLATE = (
    "{message}\n\n"
    "# 第二次完整 ReAct 诊断上下文\n"
    "根据门禁反馈重新调查未解决的问题。保留已有有效事实，必要时用只读工具补证；"
    "可以放弃第一次判断，不要只修 JSON，也不要重复完全相同的查询。\n"
    "{retry_payload}\n"
)

EVIDENCE_AUTONOMOUS_GUIDANCE_TEMPLATE = (
    "# 自主可观测性组合查询\n"
    "- 上游已确认的异常 Pod 候选：{rendered_targets}。\n"
    "- 代码已安排 Kubernetes 与 Metrics、Logging、Tracing、Topology 首轮查询；真实执行并保持精确实体范围。\n"
    "- 首轮结果可能是 present、empty、absent、weak 或 error；先判断它们是否回答各自 purpose。\n"
    "- Runbook 查询示例仅供参数形状参考，必须替换真实实体、异常时间窗和 purpose，并以工具 schema 为准。\n"
    "- 仍有关键歧义或冲突时，用新的 purpose 自主选择少量补证；没有诊断增益时停止，不追求维度齐全。\n"
    "- 只在完整 trace_id 一致时关联日志、Flow 和 Span；上下文使用率达到 80% 时停止新增采集。"
)

EVIDENCE_LEGACY_GUIDANCE_TEMPLATE = (
    "# 实时可观测性证据优先\n"
    "- 上游已确认的异常 Pod 候选：{rendered_targets}。\n"
    "- 诊断应优先依赖当前环境工具返回的真实证据，而不是 Runbook、名称、标签或模型经验推断。\n"
    "- 每个已确认异常 Pod 都必须优先执行其 mandatory `collect_aiops_case` 计划项；"
    "这是 Pod 级高信息密度入口，可一次返回 Kubernetes、Metrics、Logging、Tracing 和 Topology。\n"
    "- coarse 结果足够时避免重复采集；coverage 缺失、冲突、error、absent 或工具不可用时，"
    "kubectl/Prometheus 等细粒度工具才作为补证和降级路径。\n"
    "- Agent 负责真实执行、理解 coverage 和选择必要补证，但不能跳过 mandatory coarse 项后直接推论。\n"
    "- 上下文使用率达到 80% 后停止新增采集，明确列出未采集 Pod，不得把它们写成已验证结论。"
)

EVIDENCE_VALID_PLAN_RETRY_INSTRUCTION = (
    "上一轮 evidence_plan 已有效，本轮不要重新输出 evidence_plan；"
    "请直接按既有计划调用至少一个 critical 或 important 级真实工具。"
)
EVIDENCE_UPSTREAM_MUST_VERIFY = "基于真实 tool_result 重新验证上游定位"
EVIDENCE_MISSING_POD_CONFLICT = (
    "异常 Pod 当前不存在；历史事件或归档摘要不能继续作为该 Pod 当前异常的正向证据"
)
EVIDENCE_STRICT_SYSTEM_RETRY_TEMPLATE = (
    "\n\n# 本轮最低要求\n"
    "- 失败原因：{failure_reason}\n"
    "- 至少执行一条 critical/important 只读工具；没有真实 tool_result 时不得声称采集完成。\n"
)
EVIDENCE_COMPLETED_COLLECTION_TEMPLATE = (
    "{user_message}\n\n"
    "# 已完成首轮采集摘要（不要用相同参数重复调用）\n"
    "{completed_summary}\n"
)
EVIDENCE_BASELINE_FAILURE_INSTRUCTION = (
    "检查错误并补齐/修正参数后重新调用；"
    "不得把本次失败写成无匹配数据"
)
EVIDENCE_BASELINE_HANDOFF_TEMPLATE = (
    "{user_message}\n\n"
    "# 代码预采集的三维可观测性 baseline\n"
    "以下是 ReAct 启动前已真实并行执行的 Metrics、Logging、Tracing "
    "工具结果，不是根因结论。先比较这些事实与 Kubernetes 生命周期，"
    "再自主决定需要调用哪些只读工具继续调查；required_follow_up 中的失败"
    "必须先修正参数并继续调用，不要机械重复完全相同的查询。\n"
    "{payload}\n"
)
EVIDENCE_DEFAULT_EXECUTION_REASON = "请直接按既有计划执行工具"
EVIDENCE_DEFAULT_STRICT_REASON = "上一轮只返回计划，没有执行工具"
EVIDENCE_ABNORMAL_SUMMARY_HEADER = "# 当前异常结构化摘要（必须优先审查）"
EVIDENCE_ABNORMAL_COUNTS_FALLBACK = (
    "status_counts: 未提供；从 issue_groups/abnormal_pods 进行最小覆盖。"
)
EVIDENCE_ABNORMAL_COVERAGE_REQUIREMENT = (
    "要求：非 Running/Completed/Succeeded/Ready/Bound/Active 的状态都需要至少最小验证；"
    "主异常组做完整验证，非主异常组验证当前状态 + 一个最关键事件/配置/依赖信号。"
)
EVIDENCE_CONTINUE_GATE_REASON = "继续执行尚未尝试的首轮 Metrics、Logging、Tracing、Topology 门控项"
EVIDENCE_CONTINUE_MANDATORY_REASON = "继续执行尚未尝试的 mandatory 实时可观测性采集项"
