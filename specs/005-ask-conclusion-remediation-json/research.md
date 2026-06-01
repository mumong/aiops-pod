# Research: Ask Conclusion Remediation JSON

## Decision: Use prompt JSON plus local validation/normalization

**Rationale**: The report is Markdown, but the executor consumes structured remediation JSON. Keeping the model prompt JSON preserves existing behavior, while local validation fixes cases where prose and JSON disagree. This avoids an extra LLM call and avoids changing earlier nodes.

**Alternatives considered**:
- Native Pydantic for the whole conclusion report: rejected because it can increase latency and still wraps remediation JSON inside Markdown.
- Executor-side synthesis: rejected because the user scoped the change to conclusion.
- Evidence-node repair: rejected because layer/evidence/RCA must remain unchanged.

## Decision: Start with confirmed TerminatingStuck finalizer normalization

**Rationale**: This is the reported concrete case. It has clear evidence requirements and a standard Kubernetes repair: `kubectl patch pod ... -p '{"metadata":{"finalizers":null}}' --type=merge`.

**Alternatives considered**:
- Synthesize all runbook repairs: rejected as too broad and unsafe for the incremental goal.
- Convert force delete into structured action: rejected because finalizer patch is safer and force delete requires stricter fallback conditions.

## Decision: Do not add a remediation mode gate

**Rationale**: `workflow.remediation.mode` already controls review vs auto execution. This feature only makes the plan parseable when evidence supports a safe action.

**Alternatives considered**:
- Reintroduce request flags or `AUTO_REMEDIATE`: rejected by prior user decision.
