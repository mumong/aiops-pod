"""Literal context-compaction policies exported through app.core.prompts.

Budget decisions, data reduction and message composition stay in the callers.
These strings preserve the original model-visible bytes, including whitespace.
"""

WORKING_CONTEXT_SUMMARY_PREFIX = (
    "[working_context_summary] 以下是较早工作的有损摘要；后续保留消息可能更新这些事实。不是新用户请求：\n"
)

RUNTIME_COMPACTION_INSTRUCTION = (
    "压缩 evidence 运行上下文。保留关键过程、计划、已完成/未完成证据、"
    "正向事实、负向事实、冲突和下一步焦点。若模型陷入重复工具或钻牛角尖，"
    "请抓大放小，把重复/无关节点容量、长 JSON、重复 describe 归入 discarded_noise。"
)

RUNTIME_COMPACTION_BUDGET_EXCEEDED_INSTRUCTION = (
    "压缩 evidence 上下文，保留计划、工具事实、错误和证据引用。"
)
