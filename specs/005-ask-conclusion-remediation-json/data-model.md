# Data Model: Ask Conclusion Remediation JSON

## Conclusion Remediation JSON

Fields consumed by existing parser:
- `remediation_available`: boolean
- `fix_type`: string, expected `remove_finalizer` for this feature
- `risk_level`: string
- `requires_human_approval`: boolean
- `issue_groups`: list of issue group objects
- `basis`: evidence strings
- `actions`: list of normalized remediation actions
- `stop_conditions`: list of strings

## Safe Finalizer Evidence

Required facts:
- Pod name is concrete and non-placeholder.
- Namespace is concrete and non-placeholder.
- Current evidence includes `deletionTimestamp`.
- Current evidence includes non-empty `metadata.finalizers` or equivalent finalizer list.
- Evidence does not say Pod is `NotFound`.

## Normalized Remediation Action

Required fields:
- `id`: stable local identifier
- `type`: `kubectl_patch`
- `group_id`: matching issue group id
- `target_issue`: `TerminatingStuck`
- `description`: short action description
- `risk`: `medium`
- `dry_run_command`: read-only YAML command for confirmation
- `execute_command`: finalizer patch command
- `verify_command`: `kubectl get pod` command

State transition:
- Missing/empty structured actions + safe evidence -> normalized parseable action.
- Missing safe evidence -> unchanged report; existing executor handling applies.
