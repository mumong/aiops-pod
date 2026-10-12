# Evidence computation: minimal trial and release gates

## Objective and authorization

Agent chooses information to inspect; tools select/compute over actual evidence;
Agent interprets the results. Optimize useful evidence and total task efficiency,
not just the size of one tool response. No fault-specific diagnosis rules,
mandatory collection sequence, arbitrary code execution, or new summary agent.

This trial supersedes treating the navigable evidence view as the final solution.
That previous prototype stays disabled by default. Its code and results are not
discarded. This trial initially changes evaluation scripts only, not serving tools,
prompts, repair policy, deployments, or the deep/parallel handoff architecture.

## Problems to measure

1. Fixed-size summaries can omit supporting facts already present in a response.
2. Directory-first offloading can require several extra reads before an answer.
3. Serial tool calls accumulate context; a smaller first result alone is not a win.
4. Selection may move complexity onto a smaller model. Invalid expressions,
   wrong fields, overly narrow predicates and wrong record associations count as
   failures, even when the query engine faithfully executes the request.
5. Current lifecycle facts preserve recovered containers but cannot select fields
   or filter by those facts. Existing Kubernetes jq uses a shell pipeline and a
   different data schema; it is not silently substituted into the read-only path.

## Minimal experiment before production API selection

Use the installed JMESPath library as an experimental, read-only JSON query
primitive. One optional expression on the original lifecycle invocation can
filter, project, count or sort existing records; omission returns the same snapshot.
This is an established expression language, not a new fault-specific DSL. Whether
it is simple enough for the model is a measured question, not an assumption.

The first experiment runs against frozen real lifecycle snapshots and explicitly
labeled synthetic edge cases. It starts BEFORE tool selection: both arms receive
the user question, field contract and tool schema, not preselected evidence.
The baseline returns the full lifecycle snapshot (the current lifecycle behavior);
the candidate executes the model's expression over that exact same snapshot.
Neither arm can access live Kubernetes or execute shell/Python. Expressions only
process JSON, with no user-defined functions. Results retain source scope, time,
window/history limitations, paging metadata and the executed expression.

Do not describe a frozen-page count as a full-cluster count. Selection runs over
the whole received page before display limiting. Oversized output fails explicitly
and invites a narrower selection; it is never silently chopped into invalid JSON.
A null result can mean a missing field, not absence of matching resources.

## Test standards, fixed before implementation

| Area | Required cases and acceptance |
|---|---|
| Evidence | Real OOM/recovery snapshot, late relevant record, exact UID/time/reason associations |
| No fault specialization | Ordinary lists, counts, unknown generic records and user-chosen filters |
| Scope | Namespace/Pod mismatch rejected; partial pages retain real continuation metadata |
| Containers | Multiple containers, init/ephemeral roles; predicates must not cross-join containers |
| Time | Boundary at 10m, absent/future timestamps; lifetime count never relabeled window count |
| Value semantics | Zero, false, null, missing, empty lists, upstream error remain distinct |
| Computation | Filtering/projection/count/sort over full supplied data before output cap |
| Limits | Giant record, long expression, oversized result and invalid syntax are explicit outcomes |
| Integrity | Input not modified, deterministic exact output, no shell/file/network functions |
| Model usability | Agent forms its own arguments; invalid calls, corrections and repeated calls recorded |
| Answer | Correct target/value association, coverage disclosed, no fabricated completeness |

Unit tests establish engine behavior, not model competence. Keyword presence in
answers is screening only; review each answer against an independently computed
oracle and the actual arguments/results. A source checksum identifies every trial.

## Comparison and release criteria

- Paired tasks, same model/settings/source, randomized arm order, at least three
  repeats for nondeterministic comparative conclusions. Record failures too.
- Record model/tool calls, arguments, returned bytes, input/output tokens, local
  computation time, total wall time and final response. Account for schema cost.
- Require exact factual correctness and coverage in evaluated tasks, no regression
  on small queries, and fewer tokens without a material increase in calls/retries.
- Assess medians and slow runs, not one favorable result. A test harness without
  history middleware cannot establish compaction frequency or end-to-end latency.
- Before deployment: actual Query integration, memory follow-up, serial results,
  frontend rendering, dependency pinning and timeout/resource limits must pass.
- A reachable small model must be tested before claiming small-model validation;
  the deployed model's success alone is insufficient. Never change the serving
  model merely for a benchmark.
- A regressing or unverified prototype remains experimental, not broadly deployed.
  Broader tools and deep/parallel changes require separate evidence and design.

## Status

Initial expression trial exposed model/contract friction; a second experimental
arm uses `record_type`, `fields`, `where`, `match`, `group_by` instead of query code.
The engine selects/counts generic rows. The lifecycle adapter copies Pod/container
identity and state fields, with one row per explicitly chosen record unit. It does
not classify anomalies or choose filters. Conditions bind to the same container;
unknown filter values are counted separately. Grouping counts rows, so container
counts cannot silently masquerade as Pod counts. Identities accompany selected
facts even when omitted from the requested fields. No new MCP endpoint yet.

All 47 new offline checks passed; full backend unit + Runbook suite:
**1844 passed**, 27 pre-existing deprecation warnings. Static checks and
`git diff --check` passed. These results are not model/end-to-end acceptance.

### First expression trial (one repeat; exploratory, not a release result)

Artifacts: `/tmp/aiops-evidence-computation-pretool-20261009-r1`.
Model: `openai/gpt-6-luna`, low. Frozen run `dab61a799fdf49ca`, 67 Pods.
Independent count oracle: master=27, node1=22, node2=18.

| Task | Full-response baseline | Expression arm |
|---|---|---|
| Last OOM termination | 2 model calls, 31205 input tokens, 14.3s | 3 calls, 6279 tokens, 29.6s; first query exceeded output cap |
| Count by node | 2 calls, 31151 tokens, 21.5s; incorrect counts 22/22/23 | 3 calls, 4598 tokens, 31.0s; invalid jq-like syntax, then incorrect manual counts 27/21/19 |
| Broad review | 2 calls, 31175 tokens, 54.2s | 4 calls, 9273 tokens, 43.5s; answer still requires fact-by-fact review |

Both count answers sum to 67 but are wrong by node. Syntax correction and token
reduction do not establish correctness or speed. JMESPath does not supply the
model's attempted `group_by`; the simpler arm offers exact grouping directly.
The baseline count answer also misread the pagination *documentation* as evidence
of further pages, although next_continue_token was null. Do not blame collection
or the engine for that interpretation error.

The first harness omitted an explicit archive receipt, and models wrote narrative
evidence references; no citation-integrity pass is claimed. The second trial
provides the actual frozen file reference to both arms. Trial source hashes and
full queries/results/answers are saved, not only summary success flags.

### Remaining work

Three-repeat paired full-response vs simple-record model trials completed in
`/tmp/aiops-evidence-computation-pretool-20261009-r2` (18 runs). All use the same
source checksum and `gpt-6-luna`, low; the cap was five model calls in both arms.

| Task | Full response | Simple record operations |
|---|---|---|
| Node counts | 0/3 exact distributions; median 31184 input tokens, 19.34s | 3/3 exact distributions; 3786 tokens, 13.12s |
| Target termination facts | 3/3 answered, two model calls each | 3/3 correct target/time/exit/restarts and unknown window count; two model calls each |
| Termination performance | Median 31238 input tokens, 17.92s | 4089 tokens, 27.15s; **no wall-time improvement** |
| Broad review | 3/3 produced answers, median 46.01s; not all factually correct | 0/3 completed at five-call cap; 3 step-limit failures |

Manual review found the full-response broad-review repeat 2 changed old timestamps:
the actual apiserver termination is **2026-10-08T02:29:15Z**, but the answer said
03:29:15Z just before the Oct 9 window. Grafana's Oct 8 02:31:43Z became 03:31:43Z,
leading to a fabricated inconsistency with the correct window flag. Full raw
context does not guarantee accurate reading. The candidate's incomplete reviews
are nevertheless failures, not wins over that baseline.

Simple-record broad reviews first requested container fields on Pod rows, then
hit the fixed result cap. Engineering defects: schema offered a union of fields
without sufficiently distinguishing row types; the invalid-field error only said
`unknown field`. These should be corrected before judging the interface. The
five-call experimental cap is not the serving workflow's step limit. Raising it
alone is not an efficiency fix; later trials must report the larger call count.

R2 source fingerprints before subsequent revisions:
- evaluation script: `bf4d3fc2ec6aa552fc33df08f41f1f7fadc7e5a856dc54b1df528757d1d3e129`
- record adapter/engine: `b22012479cbe3516143dc45de24ce2897ad6fc32b8f3b7c7a71732d70fa562b2`

### R3: clearer row contract; larger experimental call cap

Artifacts: `/tmp/aiops-evidence-computation-pretool-20261009-r3`. The manifest now
records the call cap and code hashes; full evaluation/engine source snapshots are
included. Row types have explicit field descriptions; invalid-field errors name
the rejected fields and available fields. No collection/diagnosis logic changed.

- Count: 3/3 completed in two model calls, with correct distributions; median
  22.10s. This differs from R2 latency despite similarly small inputs.
- Target termination: 3/3 completed in two calls, correct target/exit/time/count
  boundaries; median 16.52s. Per-model-call times are recorded separately.
- Broad review: one provider timeout **before any tool call** (60.07s), one
  eight-call step limit (51.94s), one answer after eight calls (94.26s).
- The answered broad review correctly kept old termination dates as Oct 8/Oct 5,
  distinguished the successful recent init termination from the OOM container,
  and did not relabel lifetime totals as window counts. However it omitted
  `evidence_refs` despite receiving the real reference: not a full acceptance pass.
- The row-type mismatch was removed in the observed broad calls, but repeated
  over-budget selections remained. More steps alone did not solve the bottleneck.
- Local filtering is milliseconds; a recorded 34.61s first model call had no
  preceding tool execution. Do not attribute that delay to compaction/processing.

### Serving compatibility check (read-only, no integration change)

`ObservationProcessor._parse_lifecycle_observation` currently requires
`contract_version=pod-lifecycle.v1` and `pods` as a list. Passing the successful
experimental grouped packet produced `parse_status=unsupported` and
`semantic_success=False`. The frontend's `chatEventTransition.ts` maps that flag
to tool failure, and `toolPresentation.ts` likewise displays failure. Thus simply
replacing the MCP response would introduce an integration bug. A versioned generic
result contract and coordinated backend/frontend parsing are required before any
serving rollout; the existing producer contract must remain compatible.

**Release decision: do not deploy this prototype.** Directed selection/grouping
has evidence of value, but broad-review efficiency, citation integrity and serving
compatibility are not proven. No claim of reduced real-workflow compaction,
memory/parallel E2E success, or small-model readiness is supported by these trials.

Potential next experiment, requiring agreement on the representation change:
when a requested result is too large, return an explicitly incomplete statistical
overview with bounded representative source rows instead of only an error. The
profile must show counts/unknowns/omissions and must not embed fault diagnosis or
pretend examples are exhaustive. This is not implemented or automatically enabled.

### Convergence boundary

User clarified that practical engineering completeness, not perfect model behavior,
is the acceptance target. Stop repeatedly tuning against the same broad-review
question. Keep known model selection/latency limitations explicit. Required hard
gates remain exact computation, declared scope/unknowns/omissions, explicit errors,
protocol compatibility and rollback; they are not relaxed by a model completing
one favorable run. No automatic statistical-profile fallback has been authorized
or implemented. Synthetic recovery/partial-page/empty/error fixtures were added
for deterministic regression checks; no additional live-model boundary sweep was
started. These fixtures are explicitly labeled non-cluster data.

The configured endpoint advertises no Qwen/28B model; small-model validation is
not established. Production remains on backend `11.0.204-pod-lifecycle-20261009`
and MCP `7.0.33-pod-lifecycle-10m-20261009`, both with one ready replica. No commits,
pushes, config changes or deployments were performed in this experiment.
