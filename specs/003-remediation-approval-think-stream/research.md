# Research: Remediation Approval And Think Stream

## Decision: `workflow.remediation.mode` is the only remediation execution control

**Rationale**: The user explicitly cancelled `AUTO_REMEDIATE` and request-level `remediate=true` as control surfaces. A single config key avoids ambiguous precedence between environment, request, and ConfigMap values. `workflow.remediation.enabled=false` disables the stage; `mode=review` requires human approval; `mode=auto` automatically approves safe actions.

**Alternatives considered**:
- Keep `AUTO_REMEDIATE` as compatibility alias: rejected because it keeps the ambiguity that caused `manual_only/actions=[]`.
- Keep `remediate=true` as request gate: rejected because the user chose ordinary `/ask` to enter remediation when workflow config enables it.
- Fail on mixed config: unnecessary once `AUTO_REMEDIATE` is removed from semantics.

## Decision: Structured remediation plan remains the executor contract

**Rationale**: The executor already consumes `remediation_plan` JSON. Natural-language suggestions are useful to humans but too brittle for write execution. Confirmed repairable cases must produce valid JSON actions, and invalid/missing actions must surface as `invalid_plan`.

**Alternatives considered**:
- Parse commands from Markdown repair advice: rejected as unsafe and prone to stale or ambiguous command extraction.
- Let `actions=[]` silently skip: rejected because it hides structure-generation regressions.
- Execute directly from runbooks: rejected because current evidence and target scope must be reflected in the plan.

## Decision: Stabilize action generation at the conclusion/plan boundary

**Rationale**: The observed report had natural-language `kubectl patch` advice but `remediation_available=false`. The best fix is to make the conclusion prompt/schema/validation produce aligned `remediation_plan.actions` for confirmed repairable branches. The executor should detect inconsistencies, not invent missing actions.

**Alternatives considered**:
- Patch the executor to infer actions from the report: rejected for safety and coupling.
- Hard-code only TerminatingStuck finalizer actions in executor: rejected because it couples Kubernetes branch knowledge into execution.

## Decision: Review mode approval remains before plan and before each write action

**Rationale**: Existing `RemediationAgentExecutor` already has plan and action approval events. Keeping both gates gives the user explicit control over the overall plan and each command.

**Alternatives considered**:
- Approve only the plan: rejected because a react executor can choose later commands based on observations.
- Approve only write actions: rejected because the operator should be able to reject the overall remediation strategy before command selection.

## Decision: Think stream should adapt to provider-exposed reasoning and progress events

**Rationale**: The current service already supports `<think>` filtering and extracts provider `reasoning_content`. Different OpenAI-compatible gateways expose reasoning differently, and some paths do not token-stream at all. The stream should display available LLM intermediate reasoning without fabricating hidden reasoning, and should always show auditable progress fallback events.

**Alternatives considered**:
- Require literal `<think>` tags: rejected because provider metadata may carry reasoning without tags.
- Hide all reasoning and show only tools: rejected because the user explicitly wants intermediate LLM reasoning when available.
- Synthesize reasoning summaries from hidden state: rejected because it can misrepresent what the model actually produced.

## Decision: Real validation must exercise both remediation and streaming

**Rationale**: The bug was discovered in the deployed service with real model output. Unit tests are necessary but insufficient for model-facing behavior. The validation path must deploy the versioned image, run a real TerminatingStuck finalizer scenario, inspect remediation approval/auto behavior, and run a streaming query or diagnosis for think/progress output.

**Alternatives considered**:
- Unit tests only: rejected by constitution and user request.
- Manual log inspection only: rejected because it does not prove user-visible stream behavior.
