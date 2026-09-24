"""Literal autonomous task-context instructions, exported via app.core.prompts.

Callers retain dynamic tool IDs, catalog discovery, user input, serialization,
tool cloning and all routing/selection decisions.
"""

AUTONOMOUS_RUNBOOK_CATALOG_HEADER = "\nRunbook 目录（匹配当前异常时读取，已读可复用）：\n"
PARALLEL_LANE_TASK_PREFIX = "\n本分支任务："
PARALLEL_LANE_QUESTION_TEMPLATE = "本分支只诊断 {namespace}/{name}：{question}"
PARALLEL_FANIN_INSTRUCTION = (
    "各 Pod 分支已结束；请按 parallel_results 中的各组证据和限制汇总，不把分支完成等同于根因确认。"
)

FOCUSED_RUNBOOK_DESCRIPTION_PREFIX = (
    "读取相关运维参考资料，不会执行诊断。仅使用与当前问题相关的知识，"
    "手册步骤不是强制工具计划，也不是环境事实。可用 runbook_id："
)
QUERY_RUNBOOK_DESCRIPTION = (
    "读取指定 Runbook 全文作为参考。按原问题选取相关知识，不要求执行全部步骤；手册不是环境事实。"
)
FOCUSED_REQUEST_TIME_TEMPLATE = (
    "\n本次执行开始时间（UTC）：{request_time}；相对时间以此为基准，实际数据时间以工具返回为准。"
)
QUERY_TASK_AUTHORITY_PREFIX = "\n任务理解（以原问题为准）："
QUERY_RUNBOOK_CATALOG_HEADER = "\n可用 Runbook 目录（按需读取）：\n"
