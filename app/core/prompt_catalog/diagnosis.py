"""Byte-compatible RCA and report instructions, exported via app.core.prompts.

Builders only interpolate prepared material. Evidence selection, serialization,
schema selection, budgets, concurrency and recovery remain in workflow nodes.
"""

RCA_COMPACT_OUTPUT_CONTRACT = """

# 精简输出合同
只填写运行时 RCACompactOutput：现象、根因、最短因果链、置信度、未知项，
以及最多 8 条 key_evidence。causal_chain 按“上游原因 → 机制 → 直接失败 → 现象”
写成字符串数组。每条 key_evidence 使用 `[来源工具] 真实具体值或错误原文 | `
`role=supports/contradicts/limits | fact_id=输入中的ID`；没有 fact_id 就省略。
不要复制采集计划、coverage、完整工具响应或重复事实。"""

RCA_FULL_OUTPUT_CONTRACT = """

# 完整输出合同
按运行时 RCAOutput schema 填写；只保留少量高价值 evidence_analysis，
不要为了填满辅助字段复制工具结果。"""

RCA_NO_RECOLLECT_POLICY = """

# ⚠️ 重要：不要重复采集数据
上面的「已采集证据」和「工具采集的原始数据」已经包含了所有需要的信息。
请直接基于这些数据进行分析，**不要重新调用工具采集数据**。
如果数据不足，在 limitations 中说明即可。"""

RCA_LITE_EVIDENCE_LOCATION_NOTE = (
    "证据上下文只在 user message 中提供，system prompt 不承载动态证据。"
)

RCA_REPAIR_INSTRUCTION = (
    "只修复 RCA 发布合同，不重新采集。若 previous_claim 的语义被事实支持，"
    "保留其内容并用本 payload 中精确 fact_id 填写顶层 supporting_fact_ids、"
    "唯一 hypothesis 及 evidence_analysis；causal_chain 至少填写 trigger、"
    "mechanism、manifestation。若不受支持则输出 inconclusive。"
)

RCA_FACT_LEDGER_POLICY = (
    "Fact Ledger 是 AIOps 根因分析的主证据输入；只能引用当前 ledger 中的 fact_id。"
)

RCA_NARRATIVE_EVIDENCE_POLICY = (
    "Evidence Agent 的自然语言分析仅作为推理草稿；每个数值、状态、"
    "错误原文和最终判断仍必须由下方去重后的真实工具观察支撑。"
    "不注入 Fact Ledger、selected_facts、evidence_items 或采集元状态。"
)

RCA_QUALITY_POLICY = (
    "source_coverage/case_target_coverage 只表示采集覆盖，"
    "不能替代 diagnostic_sufficiency；未回答问题必须进入结论限制。\n"
)

QUERY_REPORT_TOOL_DATA_HEADER = "\n# 工具采集的真实数据（必须引用）\n"

REPORT_FACT_AUTHORITY = "canonical normalized facts"
REPORT_FACT_AGGREGATION_POLICY = (
    "repeated logs and equivalent L7 flows may be structurally grouped; "
    "counts, time ranges, numeric ranges, trace_ids and fact_ids remain explicit"
)
REPORT_METRIC_TREND_RULE = (
    "metric trend is valid only when trend_evaluable=true and sample_count>=2"
)


def build_rca_user_message(question: str, evidence_summary: str) -> str:
    return f"""# 用户问题
{question}

# 已采集证据
{evidence_summary}

请直接基于以上证据进行根因分析，并通过运行时 Pydantic schema 生成结构化结果。"""


def build_diagnosis_report_instruction(question: str) -> str:
    return f"""# 任务
用户的原始问题是「{question}」。只按 system prompt 中唯一的报告结构组织输入事实；
证据表的“真实原始结果”必须摘自工具数据，不输出修复建议或验证步骤。"""


def build_diagnosis_report_user_message(
    question: str,
    layer_section: str,
    evidence_summary: str,
    rca_summary: str,
    tool_section: str,
    instruction: str,
) -> str:
    return f"""# 用户问题
{question}

# 阶段1：问题定位
{layer_section}

# 阶段2：证据采集摘要
{evidence_summary}

# 阶段3：根因分析
{rca_summary}

# 工具采集的真实数据（重要！报告必须引用这些真实数据）
{tool_section}

{instruction}"""


def build_query_report_user_message(
    question: str,
    query_result_section: str,
    tool_section: str,
    instruction: str,
) -> str:
    return f"""# 用户问题
{question}

{query_result_section}
{tool_section}
{instruction}"""


def build_group_report_user_message(question: str, gid: str, context_json: str) -> str:
    return f"""# 用户问题
{question}

# 当前唯一异常组
本次调用只负责异常组 `{gid}`。下面 JSON 是本组唯一事实来源；你看不到也不得推测其他组。
普通 fact 的 `value` 以及聚合 fact 的 `pattern/flow/records/numeric_fields`、labels、stats、timestamp、trace_ids 均来自原始规范化事实；聚合只合并重复记录，不改变事实含义。

{context_json}

# 任务
只输出以下两个 Markdown 区块，组号必须是 `{gid}`：
1. `## 🕵️ 证据内容 · {gid}`
2. `## 🎯 根因分析 · {gid}`
不要输出全局概览，不要提及其他异常组，不要附加修复建议或原始 JSON。
"""
