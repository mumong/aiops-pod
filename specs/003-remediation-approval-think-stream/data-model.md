# Data Model: Remediation Approval And Think Stream

## Remediation Configuration

**Purpose**: Runtime policy that decides whether post-diagnosis remediation runs and how approvals are handled.

**Fields**:
- `enabled`: boolean. `false` disables post-diagnosis remediation.
- `mode`: enum. `review` requires human approval; `auto` automatically approves safe actions.
- `executor`: enum. Existing values `deterministic` and `react`.
- `approval_timeout_seconds`: integer timeout for approval waits in review mode.
- `max_iterations`, `max_write_actions`, `max_duration_seconds`, `verify_settle_seconds`: existing bounded executor limits.

**Validation rules**:
- `mode` must be `review` or `auto` when remediation is enabled.
- `AUTO_REMEDIATE` must not affect this entity.
- Request parameters must not be required to enable this entity.

## Structured Remediation Plan

**Purpose**: JSON contract consumed by remediation executors.

**Fields**:
- `remediation_available`: boolean.
- `fix_type`: string such as `single_issue`, `multi_issue`, or `manual_only`.
- `risk_level`: string risk label.
- `requires_human_approval`: boolean metadata; execution approval is still governed by remediation mode.
- `issue_groups`: list of diagnosed issue groups.
- `basis`: evidence strings grounding the plan.
- `actions`: list of remediation actions.
- `stop_conditions`: list of reasons to stop.

**Validation rules**:
- If a confirmed issue group is repairable, `remediation_available` must be `true`.
- If `remediation_available=true`, at least one action must exist.
- For confirmed TerminatingStuck finalizer branches, an action must include the scoped finalizer patch and verification.
- Natural-language repair advice and `actions` must not contradict each other.
- If the report suggests a write action but `actions=[]`, remediation must emit `invalid_plan`.

## Remediation Action

**Purpose**: A bounded command step used by deterministic or react executors.

**Fields**:
- `id`: stable action identifier.
- `type`: action type, usually `kubectl`.
- `description`: human-readable purpose.
- `risk`: risk label.
- `dry_run_command`: optional read or preview command.
- `execute_command`: optional write command.
- `verify_command`: optional verification command.
- `metadata`: target scope, group id, expected state, and evidence references.

**Validation rules**:
- At least one command must be present.
- Commands must pass existing safe `kubectl` validation.
- Write actions require approval in `review` mode.
- Auto mode may execute only commands that pass safe-command validation.
- Verification must prove the intended terminal state or produce a clear failure.

## Remediation Event

**Purpose**: Streamed workflow event for remediation progress.

**States**:
- `remediation_approval_required`: review mode waits for plan or action approval.
- `remediation_tool_result`: command result from dry-run, execute, or verify.
- `remediation_finished`: terminal event with status and reason.

**Additional status values**:
- `invalid_plan`: structured plan is missing, inconsistent, or lacks actions for a confirmed repairable case.
- Existing statuses such as `success`, `failed`, `timeout`, and `rejected` remain valid.

## Think Stream Event

**Purpose**: User-visible stream item for LLM intermediate reasoning and auditable progress.

**Fields**:
- `type`: `thinking`.
- `thinking_type`: `ai_token`, `ai_message`, `tool_start`, `tool_result`, `heartbeat`, `approval_wait`, or equivalent current event type.
- `node` / `node_name`: workflow stage.
- `content`: token text, model decision text, or reasoning text when exposed by the model/provider.
- `tool_name`, `status`, `result_preview`, `duration_seconds`, `iteration`: optional progress metadata.

**Visibility modes**:
- `full`: show available LLM reasoning and auditable progress.
- `truncated`: show reasoning prefix with truncation marker and keep progress visible.
- `hidden`: hide raw reasoning while keeping tool/progress/approval events visible.

**Validation rules**:
- Missing literal `<think>` tags is not a failure if provider reasoning fields or auditable progress are present.
- The stream must not synthesize hidden reasoning.
- Nodes that cannot stream tokens must still produce start/heartbeat/tool/completion visibility.
