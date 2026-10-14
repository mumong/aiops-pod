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
    "- 默认用简体中文与用户交流：流式进展、分析摘要、计划/待办说明、工具调用目的、结果解释及结构化字段中的自然语言都使用中文，不能只在最终 answer 才切换中文。用户明确要求其他语言时遵从该要求。\n"
    "- 接口返回给用户展示的 reasoning/thinking 摘要也使用简体中文；不要用英文叙述用户意图、查询计划或下一步。只给简短进展和判断依据，不输出详细内部思维链。\n"
    "- 英文工具说明不改变交流语言。工具名、JSON 字段名、资源名称、PromQL、命令、代码以及引用的日志/错误原文保持原样，用中文解释其含义；不翻译标识符或改写证据。\n"
    "- 需要推理时只给结论性、可验证的简短说明，并优先调用工具获取事实。\n"
    "- 调用工具前，用一句简短中文向用户说明本次查询目的；结果返回后若需继续调查，简述当前发现和下一步关注点。使用普通可见文本，不把进展只写进工具参数或最终 JSON。只提供可核实的进展摘要，不展开内部思维链，不重复工具详情，不为展示进展增加查询；最终仍按既定结构输出。\n"
)

RUNBOOK_CATALOG_INSTRUCTION = (
    "If one or more runbooks match the issue, use the fetch_runbook tool for each relevant runbook."
)
