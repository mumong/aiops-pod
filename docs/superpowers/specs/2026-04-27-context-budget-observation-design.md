# Context Budget and Bounded Observation Design

## 背景

未来默认使用本地 32B 小模型，模型上下文和长上下文注意力都弱于当前大模型。现有工作流里存在两个主要风险：

- `layer_full_analysis` 把 layer 节点的完整工具输出跨节点重复传递，导致 evidence / rca / conclusion 上下文膨胀。
- MCP 工具结果会直接作为 tool observation 回注给主 agent，重型 K8s 工具可能一次返回大量表格、YAML、describe 或 Prometheus range 数据。

目标不是让后端替 LLM 决定调用什么工具。LLM 仍然决定工具调用；后端负责控制上下文预算、归档原始结果、把工具 observation 变成预算内摘要。


## 目标

1. 每次 LLM 调用前记录 token budget，用于定位哪个节点、哪类上下文最重。
2. `layer_full_analysis` 不再默认存入 `WorkflowState`，完整原文只归档到固定目录。
3. 新增结构化 `layer_handoff`，作为下游默认输入。
4. 工具结果先归档全量，再按工具类型做结构化裁剪、规则聚合、必要时 LLM 兜底总结。
5. 所有 summarizer prompt 统一放在 `app/core/prompts.py`，和现有 prompt 管理方式一致。
6. Observation processor 按真实 MCP 工具名选择性启用，不假设存在原生命令工具。


## 非目标

- 不改成后端确定性执行 evidence plan。
- 不移除 LLM 自主工具调用能力。
- 不要求所有 MCP 工具都做 JSON 提取。
- 第一阶段不提供“读取完整归档全文”的 agent 工具，避免重新拉爆上下文。


## 总体架构

工具调用后的数据路径：

```text
Main Agent decides tool call
  -> MCP tool executes
  -> raw output archived
  -> tool-specific extractor if registered
  -> rule aggregation if applicable
  -> LLM fallback summarizer if still too large or extractor unavailable
  -> bounded observation returned to Main Agent
```

跨节点数据路径：

```text
layer raw analysis
  -> archive only
  -> layer_handoff in state
  -> evidence / rca / conclusion consume layer_handoff
```

Persistence and recovery path:

```text
LangGraph checkpoint
  -> stores structured state, archive refs, budget metadata, handoff facts
  -> does not store large raw tool output

Context archive
  -> stores full raw artifacts and structured extracts
  -> referenced by checkpoint state

Summary agent
  -> produces bounded observation summaries when rule extractors are insufficient
  -> prompt managed through app/core/prompts.py
```


## LangGraph Checkpoint Strategy

Use LangGraph checkpointing for graph state durability, replay, inspection, and debugging. Do not use checkpoint state as the storage location for large raw artifacts.

Checkpoint should store:

- `run_id`
- `question`
- current node and graph routing state
- `layer_handoff`
- `layer_archive_ref`
- `context_archive_ref`
- `evidence_facts`
- `evidence_conflicts`
- `missing_evidence`
- `rca_analysis`
- context budget metadata
- references to raw/structured/summary tool artifacts

Checkpoint should not store:

- full `layer_full_analysis`
- full `kubectl_get_yaml` output
- full `kubectl_describe` output
- large Prometheus matrix data
- raw 50MB command output

Recommended checkpoint backends:

- Development: in-memory or local SQLite saver if available in the dependency set.
- Production/private deployment: PostgreSQL saver if the deployment already has PostgreSQL, otherwise keep file archive as the artifact store and add DB checkpointing later.

Checkpoint usage by workflow stage:

- After `layer`: checkpoint `layer_handoff` and archive references.
- After `evidence`: checkpoint bounded `evidence_facts`, conflicts, and tool artifact refs.
- After `rca`: checkpoint structured RCA result.
- Before `conclusion`: checkpoint final compact report input for debugging.

This gives time-travel and resume capability without re-running expensive tools or re-feeding raw outputs into small models.


## WorkflowState Changes

Add:

```python
layer_handoff: Optional[Dict[str, Any]]
layer_archive_ref: Optional[Dict[str, Any]]
context_archive_ref: Optional[str]
context_budget: Optional[Dict[str, Any]]
tool_artifact_refs: Optional[List[Dict[str, Any]]]
evidence_facts: Optional[List[Dict[str, Any]]]
evidence_conflicts: Optional[List[Dict[str, Any]]]
missing_evidence: Optional[List[Dict[str, Any]]]
```

Deprecate default downstream use of:

```python
layer_full_analysis
```

The full text may be kept internally during layer execution, but should not be stored in `WorkflowState` as a large string after archiving.


## Archive Layout

Default archive root:

```text
/tmp/aiops/context_archives/<run_id>/
  layer/
    full_analysis.md
    handoff.json
  tools/
    001-layer-kubectl_get_by_kind_in_cluster.raw.txt
    001-layer-kubectl_get_by_kind_in_cluster.structured.json
    001-layer-kubectl_get_by_kind_in_cluster.summary.txt
  budget/
    layer.json
    evidence.json
    rca.json
    conclusion.json
```

The archive stores both full raw output and structured data. The main agent only receives summary/structured excerpts.


## Layer Handoff

`layer_handoff` should be precise enough for evidence to act without reading raw analysis.

Example:

```json
{
  "diagnosis_scope": "current_state_only",
  "layer": "L3",
  "layers": ["L3", "L4"],
  "confidence": 0.9,
  "primary_problem": "多个 xnet Pod 处于 Init:ImagePullBackOff，事件指向私有镜像仓库 TLS 证书不受信任",
  "active_entities": [
    {"type": "Pod", "name": "deepflow-agent-lx7zw", "namespace": "xnet"},
    {"type": "Pod", "name": "observability-mysql-848cf5bc8f-p7q49", "namespace": "xnet"}
  ],
  "active_signals": [
    {
      "source": "kubectl_events",
      "entity": "Pod/deepflow-agent-lx7zw",
      "namespace": "xnet",
      "signal": "x509: certificate signed by unknown authority"
    }
  ],
  "matched_runbooks": ["l3-imagepull-failed"],
  "must_verify": [
    "确认 active_entities 中的 Pod 当前仍存在于指定 namespace",
    "确认事件仍包含 x509 证书错误",
    "确认不是历史 event 或 namespace 漂移"
  ],
  "do_not_change": [
    "不要把 xnet 改成 default/observability",
    "不要把历史 event 当成当前故障"
  ],
  "archive_ref": "/tmp/aiops/context_archives/<run_id>/layer/full_analysis.md"
}
```


## Node User Message Rule

Node-to-node information should be carried in node-specific user messages, not appended to system prompts as large upstream text.

Evidence user message shape:

```text
# 用户原始问题
{question}

# 上游定位结构化结果 layer_handoff
{layer_handoff_json}

# 你的任务
你是 evidence 节点。基于 layer_handoff 的 active_entities、active_signals 和 must_verify 调用工具采集证据。
必须保持 namespace、Pod 名称、资源类型不漂移。
如果工具结果显示对象不存在、namespace 不匹配、事件为空，必须记录为 evidence_conflict，而不是当作成功验证。
```

RCA user message should include:

- original question
- `layer_handoff`
- `evidence_facts`
- `evidence_conflicts`
- `missing_evidence`

Conclusion user message should include:

- original question
- compact `layer_handoff`
- evidence summary
- RCA result
- bounded tool previews


## Token Budget Logging

Every LLM call should log an estimated token budget.

Required fields:

```text
[context_budget] node=evidence model=openai/Qwen3-32B context_window=32768
[context_budget] startup_prompt=5200 user=1800 tool_schema=4300 handoff=1400 tool_traces=6200 scratchpad_reserved=4096 output_reserved=6000 estimated_total=24996 usage=76%
```

Budget categories:

- `startup_prompt`: system prompt and fixed node instructions
- `user`: node-specific user message
- `tool_schema`: serialized available tool schemas, estimated if exact count is unavailable
- `handoff`: structured upstream handoff
- `tool_traces`: observations already returned into the agent loop
- `scratchpad_reserved`: reasoning/tool-call margin
- `output_reserved`: expected final model output budget

For 32K context models, suggested initial targets:

- startup prompt: <= 6K tokens
- tool schema: <= 4K tokens
- handoff/user task: <= 2K tokens
- tool traces: <= 10K tokens
- scratchpad reserve: 4K tokens
- output reserve: 6K tokens

The system should warn at 75% and error/fallback at 90% of configured context window.


## Model Context Window

Do not rely on OpenAI-compatible local servers to expose reliable context metadata.

Configuration priority:

1. Explicit config/env: `MODEL_CONTEXT_WINDOW`
2. Model-name mapping for known local models
3. Unknown fallback with warning

Logs should include `context_window=unknown` if not configured.


## Observation Processor

The processor is called inside `AICall.call()` when a tool result is received, before recording `tool_result` into `thinking_events` and before returning the observation to the main agent.

Important implementation note: the processor must affect the actual tool message content that is fed back into the LangChain agent loop, not only the copied event stored in `thinking_events`. If only `thinking_events` is summarized while the original `ToolMessage` still contains raw output, the main agent context will still be overloaded.

It outputs:

```json
{
  "tool": "kubectl_describe",
  "status": "success",
  "summary": "...",
  "structured_ref": "...structured.json",
  "raw_ref": "...raw.txt",
  "raw_chars": 33296,
  "summary_chars": 1800,
  "processed": true,
  "processor": "k8s_describe"
}
```

The raw tool output remains available in archive. The main model receives the bounded summary.


## Tool Classification

Use real MCP tool names.

Heavy tools with dedicated processors:

- `kubectl_get_by_kind_in_cluster`
- `kubectl_get_by_kind_in_namespace`
- `kubectl_get_yaml`
- `kubectl_describe`
- `kubectl_events`
- `kubernetes_jq_query`
- `kubernetes_tabular_query`

Medium tools processed only if output exceeds threshold:

- `kubectl_get_by_name`
- `kubectl_find_resource`
- `kubectl_lineage_children`
- `kubectl_lineage_parents`
- `execute_prometheus_instant_query`
- `get_prometheus_target`

Light tools default to budget logging and archive only:

- `kubernetes_count`
- `kubectl_top_pods`
- `kubectl_top_nodes`

Prometheus range query tools should be treated as heavy if present in the active tool list.


## K8s Extractors

`kubectl_get_by_kind_in_cluster` and `kubectl_get_by_kind_in_namespace`:

- Detect table-like output.
- Extract abnormal rows.
- Preserve namespace, name, ready, status, restarts, age, node.
- Aggregate status distribution.
- Highlight non-running Pods, NotReady nodes, Pending PVCs, empty endpoints if visible.

`kubectl_describe`:

- Preserve Name, Namespace, Node, Status, Conditions.
- Preserve Container State, Last State, Reason, Exit Code.
- Preserve Warning events.
- Highlight known errors: `ImagePullBackOff`, `ErrImagePull`, `CrashLoopBackOff`, `OOMKilled`, `FailedScheduling`, `MountVolume`, `x509`, `BackOff`.

`kubectl_get_yaml`:

- Parse YAML when possible.
- Drop `managedFields`, large annotations, noise labels.
- Preserve kind, metadata name/namespace, ownerReferences, containers images, resources, env/envFrom, volumes, volumeMounts, status conditions, containerStatuses.

`kubectl_events`:

- Preserve Warning events first.
- Aggregate repeated reason/message.
- Keep object, reason, message, last seen.
- Mark empty results explicitly as `no_events_found`, not as positive evidence.

`kubernetes_jq_query`:

- If output is small scalar/list, keep as-is.
- If JSON-like and large, summarize keys, counts, abnormal entries.

`kubernetes_tabular_query`:

- Summarize table header and abnormal rows.
- Preserve command failure text if present.


## LLM Fallback Summarizer

Local LLM fallback must exist for necessary cases:

- Tool has no dedicated extractor and output exceeds threshold.
- Dedicated extractor fails.
- Structured output is still above tool observation budget.
- Raw data is unstructured text where rules cannot extract enough meaning.

The summarizer is not a diagnostic agent. It only compresses a single tool observation.

The summarizer should be callable from the observation processor, not from the main workflow nodes. Its output becomes a bounded tool observation and is archived alongside raw and structured data.

Prompt management:

- Add summarizer prompts to `app/core/prompts.py`.
- Retrieve via existing-style prompt helpers, for example `get_workflow_prompt("tool_observation_summarizer")`.
- English prompts remain disabled/fallback to Chinese, consistent with current project policy.

Prompt contract:

```text
你是工具输出压缩器，不做根因分析。
只基于输入的工具输出总结事实。
保留资源名、namespace、状态、错误、数值、时间。
明确标记空结果、命令失败、NotFound。
不要把失败或空结果解释成健康。
输出 JSON：summary, key_facts, conflicts, missing, raw_ref。
```


## Evidence Validity

Tool call success and evidence validity are separate concepts.

Examples:

- Tool returned `No events found`: tool execution may be successful, but it does not validate a planned evidence item expecting an error event.
- Tool returned `NotFound`: this is a conflict or negative evidence, not a positive match.
- Tool returned `Command failed`: should be recorded as failed/negative observation, not counted as collected evidence by default.

Evidence completeness should be based on whether the observation answers the planned purpose, not only on matching tool name.


## Implementation Phases

Phase 1: Observability and checkpoint wiring

- Add context budget estimation and logs before each LLM call.
- Add per-tool raw/summary size logs.
- Add checkpoint configuration for structured workflow state if dependency support is already available.
- No prompt behavior change yet.

Phase 2: Archive and layer handoff

- Archive `layer_full_analysis`.
- Add `layer_handoff`.
- Stop passing full layer text to evidence/rca/conclusion.
- Store only archive refs and `layer_handoff` in checkpoint/state.

Phase 3: Generic observation processor

- Archive all tool raw outputs.
- Apply length threshold.
- Return bounded generic summary for oversized unregistered tool outputs.

Phase 4: K8s dedicated processors

- Add processors for the heavy K8s MCP tools.
- Save structured JSON and summary text.
- Update evidence matching to use structured observation metadata.

Phase 5: LLM fallback summarizer

- Add summarizer prompt to `app/core/prompts.py`.
- Use local model through existing `AICall.call_simple_json`.
- Trigger only when rule processing is unavailable or over budget.

Phase 6: Replay and debugging support

- Add a debug command or endpoint to inspect context budget by `run_id`.
- Add a debug command or endpoint to list archive artifacts by `run_id`.
- Document how to replay from checkpoints without reloading raw artifacts into prompts.


## Acceptance Criteria

1. Langfuse and logs show context budget for every LLM call.
2. `evidence` input no longer contains full `layer_full_analysis`.
3. `rca` does not duplicate `layer_full_analysis` in both system prompt and user message.
4. Full layer analysis and tool raw outputs are available under `/tmp/aiops/context_archives/<run_id>/`.
5. Heavy K8s tool outputs are archived and summarized before being returned to the main agent.
6. Empty/failed tool results are visible as negative/conflict observations.
7. Summarizer prompts live in `app/core/prompts.py`, not embedded ad hoc in processor code.
8. Main agent still chooses tools autonomously.
9. Checkpoints contain structured state and archive refs, not large raw outputs.
10. A failed or drifting evidence run can be inspected from checkpoint + archive without relying on Langfuse alone.


## References

- LangGraph persistence saves graph state as checkpoints at execution steps and supports thread state, replay, state updates, and fault-tolerant execution: https://docs.langchain.com/oss/python/langgraph/persistence
- LangGraph checkpoint reference describes checkpointers as state persistence within and across interactions: https://reference.langchain.com/python/langgraph/checkpoints/
- LangGraph memory guidance separates state/memory management from simply keeping all prior messages in the model context: https://docs.langchain.com/oss/python/langgraph/add-memory
- OpenAI Agents tracing documents LLM generations, tool calls, handoffs, guardrails, and custom events as first-class trace data: https://openai.github.io/openai-agents-python/tracing/
- OpenAI Codex harness engineering notes that large instruction/context files can crowd out the actual task and relevant context: https://openai.com/index/harness-engineering/
