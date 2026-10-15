# Development and compatibility

Use Python 3.12, matching the image. Runtime pins live in `requirements.runtime.txt`;
development-only tools in `requirements.dev.txt`. HolmesGPT is installed separately
by the Dockerfile. `PYTHON` defaults to `.venv/bin/python`; `RUFF` defaults to
`.venv-quality/bin/ruff`. Override these Make variables for another environment.

```sh
make test-unit
make test-replay
make check-syntax
make lint          # ruff check: E9 syntax, F pyflakes, I import order, B bugbear
make format        # ruff format (line length 99); make format-check only verifies
make build-main
```

`make check` includes replay and intentionally reports its existing failures.
See [the baseline](docs/maintenance-normalization.md). Do not weaken assertions to
make a refactor green. Live Kubernetes/LLM tests are separate from offline tests;
fault-injection/deployment targets are not unit tests. Artifacts are containers,
not standalone native binaries.

## Responsibilities

- `app/api`: transport and request parsing, not diagnosis policy.
- `app/core/workflow/nodes`: orchestration, not copies of parsing/selection rules.
- `app/core/workflow/query_contract.py`: response schema and narrow JSON recovery.
- `app/core/workflow/working_material.py`: shared evidence/context projection.
- `app/core/aicall`: model/tool runtime; `app/core/context`: archives and budgets.
- `app/core/prompts.py`: public prompt entry point; extracted compatibility
  templates live in `app/core/prompt_catalog`. Text changes require behavior tests.
- `app/core/remediation`: approvals, command snapshots, execution and verification.

### Prompt ownership

Import model instructions through `app/core/prompts.py`. Its catalog modules own
literal text; nodes retain mode selection, evidence serialization and call order.

| Location | Responsibility |
|---|---|
| `prompts.py` | Public exports and primary route/query/deep-workflow templates |
| `prompt_catalog/compatibility.py` | Extracted legacy/federation/focused templates |
| `prompt_catalog/runtime_policy.py` | Shared approval and visible-output policies |
| `prompt_catalog/evidence.py` | Planning, evidence-mode and post-case refinement instructions |
| `prompt_catalog/diagnosis.py` | RCA input/output contracts and report instructions |
| `prompt_catalog/context_policy.py` | Runtime compaction and summary boundary instructions |
| `prompt_catalog/task_context.py` | Autonomous task scope, time and Runbook guidance |
| `prompt_catalog/handoff.py` | Layer handoff, scoped groups and investigation retry instructions |

Do not merge similarly worded mode-specific instructions unless behavior changes
are intended and separately reviewed. Keep Pydantic field descriptions beside
their schemas and tool descriptions beside their tool contracts. Golden tests
capture exact model inputs, not just the existence of a template name.

## Style and review

Use Python snake_case and `#`/docstrings, not Go comments or hyphenated module names.
Prefer 99 columns for modified code; do not alter literal prompts or command text
to satisfy line length. Explain public functions and complex policy decisions.
Extract cohesive transformations or injected clients, not one file per expression.
Keep compatibility exports. Use dispatch tables for independent cases; preserve
ordered branches when order is meaningful. Avoid speculative abstractions.

Write Arrange/Act/Assert characterization tests before moving behavior. Include
failure/partial/cancellation paths, invalid JSON, concurrent groups and sessions.
Prompt byte snapshots, tool schema snapshots and event replay complement unit
coverage. Real-model responses are not deterministic acceptance oracles.

Review shared-state mutation, evidence references, ordering and approval snapshots.
Keep transport refactors separate from diagnosis policies. Repository roles and
protected branches need authorized owner review in GitLab; files cannot enforce
the requested organizational permission model.

| Project role | Intended responsibility | Grant/review owner |
|---|---|---|
| Guest | Issues and discussion; no private repository source access | Project policy |
| Reporter | Read/clone and report issues; no code pushes | PM |
| Developer | Develop, commit and push permitted branches | RD |
| Maintainer | Releases/tags, protected branches and project membership | Core RD owner |
| Owner | Group access, project deletion/transfer and group membership | Development lead |

This is the requested team policy, not a claim that permissions were changed.
GitLab edition, visibility, protected branches and group inheritance determine
effective access. Validate them in the hosting platform before granting roles;
do not infer authority to change membership from a code contribution.

Never commit credentials or raw security scan output. Preserve private deployment
configuration and PVC data. Credential rotation, permission changes and licenses
need owner coordination, not incidental formatting. Dependency upgrades require
compatibility evidence, not merely a cleaner vulnerability count.
