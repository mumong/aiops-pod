"""Runtime policy fragments; expose them through app.core.prompts.

These are literal compatibility contracts. Selection and composition remain in
the callers; changing policy wording is separate from extracting these strings.
"""

REMEDIATION_AUTO_MODE_LINE = "当前修复模式为 auto：结构化修复计划中的安全动作可由修复执行器自动审批并执行。"
REMEDIATION_REVIEW_MODE_LINE = "当前修复模式为 review：结构化修复计划中的所有写动作必须先经过人工审批。"

REMEDIATION_POLICY_TEMPLATE = (
    "\n\n# 修复计划与审批约束\n"
    "- {mode_line}\n"
    "- 诊断节点不要直接执行 kubectl apply/patch/delete/rollout/scale 等写操作。\n"
    "- 如果当前证据确认存在标准、安全、可验证的修复方式，可以在最终报告中生成结构化 remediation_plan actions。\n"
    "- 写动作是否执行由 workflow.remediation.mode 和修复执行器控制；review 模式必须人工审批。\n"
)

VISIBLE_OUTPUT_LANGUAGE_POLICY = (
    "\n\n# 语言与可见输出约束\n"
    "- 全部可见输出必须使用中文，包括分析说明、工具调用前后的说明、结构化字段内的解释文本。\n"
    "- 需要推理时只给结论性、可验证的简短说明，并优先调用工具获取事实。\n"
)

DIAGNOSIS_CONCLUSION_REMEDIATION_CONSTRAINT = (
    "\n当前为诊断总结，无新增工具调用。仅在既有真实证据足以核实对象身份和修复参数时附上修复计划；否则 actions 留空并说明需要补查。诊断报告仍是主任务，不因没有计划而省略诊断结论。"
)

RUNBOOK_CATALOG_INSTRUCTION = (
    "If one or more runbooks match the issue, use the fetch_runbook tool for each relevant runbook."
)
