# First-Principles Prompt Governance Design

## Goal

Reduce instruction dilution for Codex and the K8s AIOps workflow without weakening evidence, safety, coverage, or remediation contracts. Prompt text should spend model attention on the current task and executable decisions, not on repeated methodology or explanatory prose.

## Decision

Use layered contraction.

1. Global Codex guidance defines how to distill user intent before acting.
2. Project runtime prompts encode only the contract each workflow node must execute.
3. Tests enforce prompt budgets and high-risk boundaries.

The alternatives were rejected:

- Appending the methodology to every prompt would add repeated tokens without changing decisions.
- Rewriting every prompt and remediation schema in one pass would create an unnecessarily large behavioral regression surface.

## Global Codex Guidance

Add a compact section to `/root/.codex/AGENTS.md`. It applies across repositories and instructs Codex to internally reduce an instruction to:

- objective;
- authoritative inputs and context;
- required deliverable;
- hard constraints;
- completion evidence.

It also requires:

- preserving material ambiguity instead of silently inventing intent;
- preferring a high-signal example, schema, command, or acceptance check over repeated explanation;
- retaining negative rules only for probable, costly drift and pairing each with the desired behavior;
- avoiding visible chain-of-thought or a restatement of the full user request;
- keeping progress and final responses proportional to the task.

These are authoring and interpretation rules, not a requirement to expose private reasoning.

## Project Prompt Contract

`app/core/prompts.py` remains the single source for runtime prompts. Active workflow prompts use five semantic blocks:

1. **Objective** — the one decision or artifact owned by the node.
2. **Authority** — which inputs and tool results may support that decision.
3. **Action and stop condition** — what to do and when to stop.
4. **Output** — the schema or human artifact expected downstream.
5. **Hard boundaries** — only high-probability, high-cost failures, paired with the correct alternative.

Schema field names, actual tool names, coverage values, and a minimal real command carry implicit context. Method names such as “第一性原理”“隐性提纯”“负向配平” stay out of runtime prompts because they describe prompt construction rather than the Kubernetes task.

## Scope

This change contracts the highest-frequency active prompts:

- `LAYER_CLASSIFIER_PROMPT`
- `LAYER_EXTRACT_PROMPT`
- `LAYER_QUERY_DIRECT_PROMPT`
- `EVIDENCE_COLLECTOR_PROMPT`
- `ROOT_CAUSE_ANALYZER_PROMPT`

`CONCLUSION_FORMATTER_PROMPT` is already compact and only gains budget coverage. The legacy monolithic system prompt, federation prompt, and executable remediation prompt are not rewritten in this pass; their behavior and schemas remain unchanged.

## Behavioral Invariants

- Current Pod scan remains authoritative over historical events.
- Explicit namespace/Pod requests remain scoped to that target.
- Every current abnormal group receives required coverage.
- Evidence uses real tool results and preserves empty/error coverage as a boundary.
- The initial Metrics, Logging, and Tracing gate remains generic across Pod failures.
- Follow-up collection is driven by information gain, not a fault-name tool chain.
- RCA uses validated facts, keeps entities and trace IDs isolated, and does not call tools.
- Conclusion hides machine identifiers in the human body and retains the machine appendix.
- Without a typed remediation policy: `manual_only`, human approval required, empty actions.

No deterministic production branch may select report or evidence behavior by OOM, image pull, configuration, scheduling, or another fault name.

## Budgets and Quality Gates

Initial character ceilings:

| Prompt | Current | Ceiling |
|---|---:|---:|
| Layer classifier | 3240 | 2600 |
| Layer extract | 1959 | 1400 |
| Query direct | 2301 | 1900 |
| Evidence collector | 5519 | 4000 |
| RCA analyzer | 6047 | 4300 |
| Conclusion formatter | 785 | 1200 |

Tests also reject:

- runtime methodology vocabulary;
- duplicate non-heading instruction lines within an active prompt;
- seeded fixture/workload strings in RCA and conclusion;
- removal of existing evidence, coverage, entity-scope, trace, or remediation safety phrases.

## Verification

Use TDD: add budget and governance tests first, confirm they fail against current prompts, then contract one prompt at a time. Run the focused prompt tests after each change and the full workflow regression before integration. Compare the before/after character table and scan production code for newly added fault-specific branches.

The global file is outside the Git repository, so verify it separately and report its path and content checksum. Project prompt changes, design, plan, and tests are committed normally.
