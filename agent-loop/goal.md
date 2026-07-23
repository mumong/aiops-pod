# Goal

为 Robusta 的 32K Qwen 工作流实现可靠上下文压缩：

- RCA 和其他 structured output 调用在请求模型前必须满足硬预算。
- RCA 压缩必须优先保留真实实体、三维可观测事实和 Fact ID。
- Evidence 的 LLM 压缩失败时必须有确定性兜底。
- 使用真实超限归档证明不再发生 32K 输入溢出。
- 不增加故障类型特判，不破坏现有自主工具调用和归档。

