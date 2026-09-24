"""Static instructions for layer handoffs and scoped parallel investigations."""

LAYER_QUERY_RETRY_SUFFIX = (
    "\n\n# 上一轮结果被系统拒绝\n"
    "- 原因：你给出了 QUERY 结论，但没有提供足够的真实工具执行结果。\n"
    "- 本轮必须先执行工具，再让 Pydantic 结构化提取生成最终 query_result。\n"
    "- 在出现至少一次成功的 tool_result 之前，禁止输出最终答案。\n"
    "- 你的最后一条消息必须建立在真实工具结果之上，而不是工具计划之上。\n"
    "- 如果没有至少一次成功的 tool_result，系统会再次拒绝你的输出。\n"
    "- `query_result.rows` 为空且 `missing` 也为空，视为无效结果。\n"
    "- `collection_summary`、`sources`、`rows` 只能基于真实工具结果填写，禁止编造“已采集 100%”。\n"
)

LAYER_EXPLICIT_POD_MUST_VERIFY = (
    "本轮仅验证用户明确指定的 namespace + Pod 列表；全局扫描中的其他异常只作为背景",
    "逐一确认每个目标 Pod 当前仍存在于指定 namespace",
    "逐一确认每个目标 Pod 的 active_signals 仍能被真实工具结果验证",
    "如果工具返回 NotFound、空事件或 namespace 不匹配，记录为冲突/负向证据",
)

LAYER_GENERAL_MUST_VERIFY = (
    "以 abnormal_groups、abnormal_pods、current_abnormal_summary 为覆盖基准",
    "异常组完整/最小验证由 evidence 节点按 abnormal_groups 覆盖，避免遗漏 Terminating、Pending 等并发异常状态",
    "确认 active_entities 中的对象当前仍存在于指定 namespace",
    "确认 active_signals 仍能被真实工具结果验证",
    "如果工具返回 NotFound、空事件或 namespace 不匹配，记录为冲突/负向证据",
    "如果某个异常 Pod 不在当前异常 Pod 列表中，必须把它视为历史事件噪音而不是当前故障",
)

LAYER_HANDOFF_DO_NOT_CHANGE = (
    "不要把上游 namespace、Pod、Service、Node 名称改写成其他对象",
    "不要把历史 event 当成当前故障",
    "不要把计划或工具名当成证据，必须基于 tool_result",
)

LAYER_SCENARIO_VERIFICATION_REASON = "当前阶段只定位异常；根因必须由后续实时 canonical facts 确认"

LAYER_EXPLICIT_POD_BASELINE_TEMPLATE = (
    "{question}\n\n"
    "# 代码预采集的显式 Pod 定位结果\n"
    "以下结果已经按用户给出的 namespace/Pod 列表真实并行执行。"
    "它们是目标清单与当前状态事实，不是根因结论。不得遗漏目标，"
    "也不要机械重复相同查询；如结果失败或信息不足，可继续自主调用只读工具调查。\n"
    "{payload}\n"
)

LAYER_EXTRACT_INSTRUCTION = "基于 layer 阶段工具结果和分析文本生成 Pydantic LayerOutput"
LAYER_QUERY_RETRY_EXTRACT_INSTRUCTION = "基于 QUERY direct 严格重试后的工具结果生成 Pydantic LayerOutput"

PARALLEL_DIAGNOSIS_RETRY_INSTRUCTION = (
    "Start one fresh ReAct investigation focused on the failed "
    "gate. Keep valid facts, collect only missing evidence, and "
    "do not merely repair JSON."
)

PARALLEL_DIAGNOSIS_RETRY_QUESTION_TEMPLATE = (
    "{question}\n"
    "（第一次诊断未通过最小证据门禁；请用一次新的完整 ReAct 调查解决反馈中的缺口。）"
)

PARALLEL_GROUP_MUST_VERIFY_TEMPLATE = (
    "只诊断本组实体 {entities}，不要采集其他 namespace/Pod 的证据"
)

PARALLEL_GROUP_QUESTION_TEMPLATE = (
    "原始用户任务：{original_question}\n"
    "以下是该任务内分配给本节点的子任务，不替代原始任务：\n"
    "只调查 {entities}；初始状态为 "
    "{status}。用真实工具事实判断其当前异常、"
    "已恢复或证据不足，不查询其他 Pod。"
)
