# Data Model: Runbook Remediation Guidance

## Runbook

- **Fields**: runbook id, title, status recognition, evidence plan or checklist,
  typical causes, required checks, decision rules, standard remediation guidance.
- **Validation rules**: Active Pod abnormal-status runbooks must contain exactly
  one concise `## 标准修复建议` section.
- **Relationships**: Embedded in `deploy/configmap/runbooks.yaml`; referenced by
  catalog entries and fetched by the agent through `fetch_runbook`.

## Remediation Branch

- **Fields**: confirmed condition, preferred action, fallback action, risk note,
  verification signal.
- **Validation rules**: Preferred action must be safer and more scoped than
  fallback; destructive actions require prerequisites.
- **Relationships**: Lives inside one runbook section and maps to a diagnosis branch.

## Runbook Backup

- **Fields**: source file, backup timestamp/date, location outside `deploy/`.
- **Validation rules**: Must be a byte-preserving copy of the active runbook file
  before edits and must not be deployed by `make deploy`.

## Real Validation Run

- **Fields**: version tag, build/push/deploy commands, health check, `/ask` query,
  response artifact, optional archive path.
- **Validation rules**: Must use `VERSION=11.0.0` and the deployed service, not
  local file inspection only.
