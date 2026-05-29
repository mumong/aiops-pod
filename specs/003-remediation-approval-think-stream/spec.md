# Feature Specification: Remediation Approval And Think Stream

**Feature Branch**: `003-remediation-approval-think-stream`

**Created**: 2026-05-29

**Status**: Draft

**Input**: User description: "修复当前诊断后修复流程没有进入的问题；取消 AUTO_REMEDIATE，只使用 workflow.remediation.mode 控制全部修复行为。review 表示所有修复命令必须人工审批，auto 表示自动审批并自动执行安全校验通过的动作。修复 TerminatingStuck finalizer case 中自然语言建议 patch 但结构化 remediation_plan 标记 manual_only/actions 为空的问题。分析并修复 think 输出不稳定或 think 块不可见的问题，确保开启配置后用户能稳定看到模型思考/工具过程。使用 speckit 先明确需求，再计划和实现，并进行真实测试。"

## Clarifications

### Session 2026-05-29

- Q: 修复执行模式由 `AUTO_REMEDIATE` 还是 `workflow.remediation.mode` 控制？ → A: 取消 `AUTO_REMEDIATE`，只使用 `workflow.remediation.mode` 控制全部修复行为。
- Q: `/ask` 是否还需要 `remediate=true` 才进入修复流程？ → A: 取消 `remediate=true` 门禁；只要 `workflow.remediation.enabled=true` 且 `workflow.remediation.mode` 是 `review` 或 `auto`，普通 `/ask` 诊断后就进入修复流程。
- Q: think 输出以原始模型推理还是可审计过程为准？ → A: 以可审计过程为准：工具调用、工具结果、模型阶段性决策、心跳、审批状态必须稳定展示；原始 reasoning 有则按配置展示，但不强依赖 `<think>` 标签。
- Q: 已确认可修复但结构化 `remediation_plan` 缺失或 `actions=[]` 时如何处理？ → A: 标记为 `invalid_plan` 并在流里明确输出“修复计划缺失/不一致”，停止修复；同时必须尽可能稳定地产生结构化 JSON actions，避免走到该错误分支。
- Q: think 部分是否只需要可审计过程？ → A: 需要尽可能展示 LLM 中间推理过程；系统应适配 `<think>`、provider reasoning 字段和普通 AI message 中的阶段性推理/决策文本，工具/状态进度作为兜底可观测信号。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Approval-Gated Remediation Plan Is Generated (Priority: P1)

As an operator running a diagnosis with remediation enabled, I want confirmed safe repair actions to appear in the structured remediation plan even when automatic remediation is disabled, so the workflow can pause for human approval instead of silently skipping repair.

**Why this priority**: The current failure mode diagnosed a finalizer issue and suggested a patch in natural language, but the structured plan said `remediation_available=false` and `actions=[]`, so the executor skipped remediation.

**Independent Test**: Run a real TerminatingStuck finalizer scenario with remediation enabled and verify the emitted structured plan has `remediation_available=true`, contains a scoped `kubectl patch ... finalizers:null` action, and reaches a human approval event before any write command executes.

**Acceptance Scenarios**:

1. **Given** a Terminating Pod with current `deletionTimestamp` and non-empty `metadata.finalizers`, **When** the diagnosis confirms finalizer cleanup is the standard safe repair, **Then** the final report MUST include a structured remediation plan with `remediation_available=true` and a patch action matching the confirmed Pod and namespace.
2. **Given** `workflow.remediation.mode=review` and remediation is requested, **When** the structured plan contains write actions, **Then** the workflow MUST require human approval before executing each write action.
3. **Given** `workflow.remediation.mode=review`, **When** the LLM generates the final report, **Then** it MUST NOT be instructed that patch/delete/rollout/scale commands are categorically forbidden; it MUST be instructed that write commands require approval.

---

### User Story 2 - Auto Mode Means No Human Approval (Priority: P2)

As an operator in a controlled test environment, I want automatic remediation mode to mean approvals are granted automatically, so end-to-end tests can validate the full repair loop without manual input.

**Why this priority**: The user-defined meaning of `auto` is automatic approval and automatic execution, while `review` means manual approval, not no remediation.

**Independent Test**: Run the same remediation-capable scenario in automatic mode and verify the workflow executes approved-safe actions without pausing for approval, then verifies the result.

**Acceptance Scenarios**:

1. **Given** automatic remediation mode is enabled in a controlled environment, **When** the remediation plan contains a safe write action, **Then** the workflow MUST execute the action without emitting a blocking human approval prompt.
2. **Given** automatic remediation mode is not enabled, **When** the same action is planned, **Then** the workflow MUST emit a human approval prompt and wait for approval before execution.
3. **Given** an action is unsafe or unsupported by the remediation command policy, **When** automatic mode is enabled, **Then** the workflow MUST still reject or fail the action instead of executing it.

---

### User Story 3 - Think Stream Is Visible And Diagnosable (Priority: P3)

As an operator watching a streaming diagnosis, I want the configured think stream to show available LLM intermediate reasoning plus auditable progress, tool activity, model decision summaries, heartbeat events, and approval status, so I can tell why the agent is choosing actions and whether it is working, stuck, or skipping expected steps.

**Why this priority**: The current configuration reports `think_stream.mode=full`, but users sometimes do not see a visible think block or only see partial tool events.

**Independent Test**: Run streaming `/query` and `/ask` calls with think display enabled and verify the output contains visible LLM intermediate reasoning when the model/provider emits it, plus auditable progress events for agent-driven nodes. Nodes that cannot stream token-level reasoning still expose a clear reason or fallback progress signal.

**Acceptance Scenarios**:

1. **Given** `workflow.think_stream.mode=full`, **When** a node emits `<think>` text, provider `reasoning_content`, token-level reasoning, ordinary AI message reasoning, tool activity, decision summaries, heartbeat events, or approval waits, **Then** the stream MUST display available LLM intermediate reasoning and auditable progress fields stably.
2. **Given** a node uses a non-token-streaming path, **When** it cannot emit token-level thinking, **Then** the stream MUST still show node start, heartbeat, tool progress if any, and a clear completion summary.
3. **Given** `workflow.think_stream.mode=hidden`, **When** model reasoning is available, **Then** internal reasoning text MUST be hidden while auditable tool/progress/approval events remain visible.
4. **Given** `workflow.think_stream.mode=truncated`, **When** reasoning exceeds the configured limit, **Then** the stream MUST show the prefix and an explicit truncation marker without corrupting subsequent progress or answer text.

### Edge Cases

- A report contains natural language repair advice but structured `remediation_plan.actions` is empty; the workflow must treat this as `invalid_plan` for repairable confirmed cases, not as a successful no-op, and the stream must show a clear remediation-plan inconsistency reason.
- A repairable confirmed case has enough evidence and runbook guidance to produce a safe action; the system should stabilize the structured JSON generation path so `actions` are populated instead of relying on post-hoc natural-language extraction.
- A confirmed issue is safe to suggest but not safe to execute automatically; the plan should still be generated, with approval and risk metadata enforcing the boundary.
- A user runs `/ask` while `workflow.remediation.enabled=false`; the workflow should diagnose and may show repair advice, but must not execute actions or wait for approval.
- A user runs `/ask` without a `remediate` request parameter while workflow remediation is enabled; the workflow should still enter review or automatic remediation according to `workflow.remediation.mode`.
- A model gateway returns no raw reasoning or returns reasoning in provider-specific metadata rather than literal `<think>` tags; the stream should adapt to all available model-provided reasoning forms and still render auditable progress when raw reasoning is unavailable.
- A client disconnects during a remediation approval wait; the workflow should stop cleanly and not execute any pending write action.
- A repair command references a stale Pod or namespace; approval and execution must revalidate current target state before writing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST use `workflow.remediation.mode` as the only supported control for remediation execution mode.
- **FR-002**: The system MUST define `workflow.remediation.mode=review` as manual-review mode: write actions may be planned but require explicit human approval before execution.
- **FR-003**: The system MUST define `workflow.remediation.mode=auto` as automatic-approval mode for remediation actions that pass command safety validation.
- **FR-004**: The system MUST remove `AUTO_REMEDIATE` from remediation control semantics and MUST NOT read it to decide whether repair actions can be planned, approved, or executed.
- **FR-005**: The system MUST stop injecting blanket prompt language that forbids generating repair actions in review mode.
- **FR-006**: The system MUST NOT require a request-level `remediate=true` parameter to enter post-diagnosis remediation.
- **FR-007**: When `workflow.remediation.enabled=true` and `workflow.remediation.mode` is `review` or `auto`, ordinary `/ask` diagnosis MUST evaluate the structured remediation plan after the final report.
- **FR-008**: When `workflow.remediation.enabled=false`, ordinary `/ask` diagnosis MUST NOT execute actions or wait for approval.
- **FR-009**: For confirmed repairable cases, the final report MUST keep natural-language repair advice and structured `remediation_plan` consistent.
- **FR-010**: For a confirmed TerminatingStuck finalizer case, the structured remediation plan MUST include a scoped finalizer patch action with a verification action or success condition.
- **FR-011**: The structured plan generation path MUST be stable enough that repairable confirmed cases produce valid JSON actions without relying on natural-language command extraction.
- **FR-012**: The remediation executor MUST skip execution when remediation is disabled, but when remediation is enabled and a confirmed repairable case has no structured actions, the workflow MUST surface `invalid_plan` with a clear missing/inconsistent-action reason.
- **FR-013**: Human approval mode MUST require approval before every write action, including patch, delete, rollout, scale, apply, and equivalent write operations.
- **FR-014**: Automatic mode MUST still enforce the existing safe-command policy and MUST NOT execute commands rejected by that policy.
- **FR-015**: Think stream configuration MUST consistently control visibility for raw token reasoning, complete AI messages, provider reasoning fields, and auditable progress events.
- **FR-016**: Text and SSE streaming modes MUST expose enough progress events for users to distinguish "LLM reasoning", "model decision", "tool running", "tool result", "waiting", "approval required", and "finished".
- **FR-017**: The stream MUST adapt to available model-provided reasoning formats, including literal `<think>` text, provider `reasoning_content` fields, and ordinary AI message reasoning/decision text.
- **FR-018**: The stream MUST NOT synthesize hidden model reasoning when the provider does not expose it; in that case it MUST show decision summaries and auditable progress instead.
- **FR-019**: The system MUST NOT treat missing literal `<think>` tags as a think stream failure when other model-provided reasoning or auditable progress events are present.
- **FR-020**: The system MUST provide stable progress output for nodes that cannot stream token-level reasoning.
- **FR-021**: The implementation MUST include automated tests for manual-review plan generation, automatic approval behavior, invalid-plan surfacing, stable structured actions, and think stream visibility modes.
- **FR-022**: Real validation MUST run against the deployed service with a remediation-capable TerminatingStuck finalizer scenario and at least one streaming query that demonstrates visible LLM reasoning or, when unavailable, visible tool/progress fallback.
- **FR-023**: Versioning for real validation MUST start from `11.0.0` and increment only if the existing deployed tag has already been used for a prior validation build.

### Key Entities *(include if feature involves data)*

- **Remediation Mode**: The effective execution mode for repair actions, controlled only by `workflow.remediation.mode`, either manual review or automatic approval.
- **Structured Remediation Plan**: The JSON contract consumed by the remediation executor, including availability, issue groups, actions, risk, basis, and stop conditions.
- **Remediation Action**: A dry-run, write, or verification step with command, risk, metadata, target scope, and approval requirements.
- **Think Stream Event**: A streaming event representing available LLM intermediate reasoning and auditable progress such as model decision summaries, complete AI message content, tool start/result, heartbeat, approval wait, raw reasoning if available, or completion.
- **Repairable Confirmed Case**: A diagnosis branch where current evidence confirms a standard remediation with bounded risk and verification criteria.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the real TerminatingStuck finalizer scenario, remediation-enabled review mode reaches `remediation_approval_required` with a patch finalizer action and executes no write command before approval.
- **SC-002**: The same scenario in automatic mode executes the approved-safe patch action and verifies the Pod is deleted or no longer stuck.
- **SC-003**: No tested repairable confirmed case produces natural-language write advice while also emitting `remediation_available=false` with empty actions.
- **SC-004**: If a repairable confirmed case cannot produce valid structured actions, the stream emits `invalid_plan` with a clear missing/inconsistent-action reason instead of silently completing as diagnosis-only.
- **SC-005**: Streaming `/ask` and `/query` validation outputs visible LLM intermediate reasoning when available and visible auditable progress within 10 seconds of node activity for agent-driven paths, unless the model/tool call itself has not emitted data and heartbeat events are shown.
- **SC-006**: Automated tests cover all documented remediation modes, stable structured action generation, invalid-plan handling, and think stream visibility modes before deployment.

## Assumptions

- The existing remediation JSON schema remains the executor-facing contract; this feature clarifies how it is generated and validated.
- Review mode remains the production-safe default unless the deployment explicitly sets `workflow.remediation.mode=auto`.
- Request-level `remediate=true` is deprecated for this feature and must not be required for ordinary `/ask` remediation.
- Runbook content from the prior feature remains available as model-facing guidance, but this feature focuses on execution semantics and stream visibility.
- `AUTO_REMEDIATE` is deprecated for this feature and must not be used as a compatibility alias.
