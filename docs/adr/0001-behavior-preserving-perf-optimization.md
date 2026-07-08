---
status: accepted
---

# 诊断工作流延迟优化：只做行为无损的基础设施优化

面对四节点诊断工作流（layer→evidence→rca→conclusion）"延迟高、效率差"的问题，我们决定**只优化非-LLM-推理的基础设施/管道开销，绝不改变 LLM 调用次数、诊断行为或结果质量**。最大的延迟来源是 layer/evidence 的串行 agent loop 空转（`early_stop` 被关、`max_steps` evidence=20/layer=15），但我们**刻意不动它**。

## 背景与权衡

- wall-clock 主要由 layer+evidence 的串行 agent loop 主导（一次 `/ask` 约 9~23 次 LLM 往返）。
- 最省时的手段本是打开 `early_stop` 或调低 `max_steps`——但 `config.yaml:169` 明确注释「默认关闭 early_stop，避免复杂场景采证不足」，这是一个为保诊断彻底性有意为之的决定。
- 用户明确要求：延迟优先，但**不得牺牲诊断结果/功能/质量，不得砍任何 LLM 轮次**。

## 决定纳入的优化（行为无损）

1. MCP 工具改**持久会话**，消除每次工具调用重建 SSE + 重跑 initialize 握手。
2. **复用** ChatOpenAI 客户端与 event loop，消除每次 LLM 调用重建 model/线程/loop 的开销（不碰 LLM 请求本身）。
3. 收敛 `ContextBudgetEstimator.estimate()` 的重复调用与 `write_tool_artifact` 落盘 I/O。
4. **关闭** `AIOPS_CONTEXT_USAGE_PROBE`：它每请求数十次真实 `POST /chat/completions`（全量 prefill）只为精确 token 计数，对诊断结果零影响，退回本地估算。
5. conclusion 最终报告改**流式**产出，内容不变、仅提前逐段返回，降低感知延迟/TTFB。

## 明确拒绝（会触碰诊断行为，故不做）

- 打开 `early_stop` / 调低 `max_steps.evidence` —— 会减少采证轮次，可能降低复杂场景诊断质量。
- 合并 evidence「计划+执行」两阶段 —— 会删除一次 LLM 调用并改变采证行为。

## 质量护栏

任何触碰诊断行为的改动一律不做；但仍以 `test/pod_rootcause_e2e`（10 类异常）+ `tests/unit`（现 178 passed）作为回归护栏，确保"只快不坏"。
