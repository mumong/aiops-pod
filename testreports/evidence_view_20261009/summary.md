# Generic evidence view: first comparative trial (2026-10-09)

## Scope and checkpoint

Current-state checkpoints are present on BOTH existing GitLab and GitHub branches:
- backend `5d70ada701af0ff8aec398152e4fe00072afc03d`
- MCP `4600af1baf7c3b356d04880d92dff6333fed0bfb`
- frontend `aac3c10e137e1f05e26825c4ec93bdbd0a8ac96f`

Prototype changes only backend observation presentation and the archive reader.
No fault-specific collection sequence, diagnosis rule, repair action, route or
system prompt was added. All received raw output remains archived. The default
mode is legacy, including the old reader's parameter schema and description.

Production remains `aiops-copilot:11.0.204-pod-lifecycle-20261009`, digest
`sha256:44e3d38a6870f6757a1ceb10479dba19b5faa92f933acef02fa2b655bc2525f4`.
No prototype deployment or model/config/credential/PVC change was performed.

## Reproducibility

Runner: `scripts/evaluate_evidence_view.py`.
Local experiment root: `/tmp/aiops-evidence-view-20261009.ObUEzB`.
Each execution records input size, projection time, model calls, token usage,
exact archive-read arguments/results and final answer. Raw material stays local.

```bash
.venv/bin/python scripts/evaluate_evidence_view.py \
  --source-dir /tmp/aiops-evidence-view-20261009.ObUEzB/dab-tools \
  --output /tmp/aiops-evidence-view-20261009.ObUEzB/new-replay --llm
```

Real archived sources:
- `dab61a799fdf49ca`: lifecycle, topology, scoped metrics, logging, tracing.
- `b122d7b1acbc44fe`: Running+Ready with a previous OOM termination.
- `6c6f04d8f407491e`: small xnet Pod inventory.
- `8019c12f1d56461e`: native Prometheus result.

Synthetic sources: late log failure/recovery, long single metric series, repeated
unknown-tool records, small booleans, and text table. Synthetic data is never
presented as current cluster data. Questions are identical across modes.

The initial harness incorrectly passed the provider-prefixed model name directly
to ChatOpenAI. Those requests failed before analysis (`llm-r1`) and are excluded.
The corrected harness uses the application's `_parse_model` adapter. The model
was not changed: `openai/gpt-6-luna`, low.

## First paired run: 4k candidate

Selected outcomes from `llm-r2`, `llm-extra` and `llm-history`:

| Case | Old model calls / archive reads | New calls / reads | Old/new total input tokens | Observation |
|---|---:|---:|---:|---|
| Full controller chain | 2 / 1 | 1 / 0 | 8,551 / 5,362 | New retains both ownership hops directly |
| Five metric series | 2 / 1 | 1 / 0 | 11,888 / 5,658 | Values, timestamps and identities retained; no cross-instance sum |
| Structured logs | 3 / 2 | 3 / 2 | 44,494 / 23,174 | Less repeated input; source truncation correctly disclosed |
| Unknown tool | 1 / 0 | 1 / 0 | 12,585 / 2,771 | Generic lossless factoring works without tool registration |
| 67-Pod lifecycle page | 1 / 0 | 5 / 4 | 29,850 / 55,966 | Significant regression from repeated collection reads |
| Tracing | 2 / 1 | 3 / 2 | 16,954 / 19,440 | More reads; not an efficiency win |
| Long single series | 2 / 1 | 3 / 2 | 10,722 / 6,334 | Fewer tokens but extra round trip |
| Late log event | 2 / 1 | 3 / 2 | 8,680 / 9,978 | Model unnecessarily reread an already lossless view |

Small inventory, recovered Pod, native metric, small synthetic object and table
keep the original data and need no additional read. New reader schema costs
additional prompt tokens. API latency varies substantially even for identical
small inputs; single-run wall time is not treated as a performance guarantee.

String-presence checks are only screening. The metric candidate rendered
`51,224,576` with separators, producing an initial false alarm. Manual comparison
confirmed the five values and latest value **44,908,544 bytes at 03:39:50.207Z**.
The expected latest-value check was corrected and separator handling added.
Do not interpret a green token-presence check as proof of complete correctness.

## Iterations and remaining problem

- Complete views now say `integrity=lossless_received_response`, omit redundant
  retrieval instructions, and explicitly report zero omitted records.
- Collection indexes expose field names. Readers accept plain names as well as
  exact JSON pointers; fields on one object select that object's fields.
- Old mode restores its original reader schema as well as original processing.
- Selector errors, missing fields, source errors, zero/false/null and incomplete
  views remain distinct. Read access cannot leave existing archive roots.

Two repeated 4k trials after these changes still required two reads for the large
Pod inventory and three reads for the long-series case. The 8k experiment
(`llm-budget-r5`) reduced medium-result reads: metrics 0, tracing 0, structured
logs 1, long series 0. The large inventory still needed 4 reads. Increasing a
fixed ceiling alone therefore does not solve the general allocation problem.

## Verification / release decision

Latest backend unit + existing workflow guidance suite: **1,781 passed**, 27
existing deprecation warnings, 29.54 seconds. Focused view/evaluation/lifecycle
suite: **65 passed** (included in the full suite, not additional tests).
`git diff --check` passed.
Production recheck: Deployment 1/1 ready on the unchanged baseline image. This
health check is not a prototype integration test.

Do NOT broadly enable this candidate yet. It establishes structural integrity and
useful improvements in several families, but not an overall efficiency win.
Still pending: context-aware/shared allocation, actual multi-step workflow and
compaction tests, memory follow-up, parallel diagnosis groups and frontend
rendering with the enabled mode. No new faulty workloads or repair approvals
were created/executed for this experiment.

Recovery: keep `AIOPS_EVIDENCE_VIEW_MODE` unset/legacy; on an enabled test deployment,
restore legacy and restart so the reader catalog is reloaded. For code rollback,
restore the recorded immutable backend image. Do not reset repositories or delete
archives/PVCs. Initial code checkpoints remain on both remotes.

## Follow-up: evaluation fidelity and producer-contract regression

The first harness used a simplified legacy reader description. It is now replaced
with the actual legacy tool class/schema; historical measurements above remain
provisional and are not silently rewritten. The runner also validates QueryAnswer
with the application's parser/schema, refuses missing requested fixtures and
nonempty output directories, records source SHA-256 and task text, and shuffles
mode order using a recorded seed. Token-presence checks remain screening only.

All 56 prior successful model executions (`llm-r2` through `llm-budget-r5`) were
retroactively checked against QueryAnswer: 56 valid contracts. This does NOT
establish factual correctness of all 56 answers.

New paired replay (`llm-fair-schema-r6`, seed 917, 4k view ceiling):

| Case | Old calls/reads | New calls/reads | Old/new total input tokens |
|---|---:|---:|---:|
| Controller chain | 2 / 1 | 1 / 0 | 8,654 / 5,449 |
| Long single series | 3 / 2 | 3 / 2 | 17,566 / 6,504 |

All four new outputs have valid answer contracts and contain the expected values.
The long-series difference from earlier trials illustrates model variability;
it does not invalidate the unresolved large-inventory regression.

A producer-contract compatibility probe also found that compact mode bypassed
the existing lifecycle schema validation and could mark a malformed success
envelope as semantically successful. Both modes now share the unchanged producer
validator, covered by six parity cases (valid, missing contract, wrong collection
type, explicit error, invalid JSON and wrong root type). This preserves an existing
data contract; it adds no fault-specific diagnosis or collection rule.

The remaining-context-based allocation proposal was subsequently rejected.
The approved follow-up instead bounds initial responses and uses a cumulative
high/low-water policy. Details and latest results follow; they supersede the
earlier pending-design statement, not the historical measurements above.

## Serial-budget follow-up

Implemented, still opt-in and NOT deployed to the serving process:
- 4096-token response/read cap; 24000-token cumulative tool-interaction trigger;
  at most 8000 tokens of recent atomic exchanges after history replacement.
- Include inherited node observations, not just new ToolMessages; independent
  budgets/archives per parallel lane and existing whole-request guard preserved.
- Generic record-table encoding, bounded explicit raw reading, source directories
  outside lossy summaries, distinct subtree completeness and lookup errors.
- Legacy restores old observation processing, reader schema and cumulative policy.
  No task/fault-specific selection, forced checks, repair actions or prompt edits.

### Live compactor, synthetic serial data

`scripts/evaluate_evidence_accumulation.py`, output `live-serial-summary-final`:
18 synthetic sequential results, actual deployed `openai/gpt-6-luna` low used
only for history compression. Compaction occurred at calls **8 and 14**, not on
each return. Tool-history tokens fell 25342→6342 and 25688→6502; later calls had
headroom. Total replay 29.22s, mostly the two real summary requests. Source
directories and full before/after history remain archived. Manually inspected
summaries retain the requested batch-final entity/value/unit/time tuples. This is
NOT a claim that arbitrary summaries are lossless or that this is autonomous E2E.

### Frozen paired model replay, r9

| Case | Legacy calls/reads | Candidate calls/reads | Legacy/candidate input tokens |
|---|---:|---:|---:|
| Topology | 2/1 | 1/0 | 8636/5449 |
| Lifecycle inventory | 1/0 | 4/3 | 29897/21127 |
| Scoped metrics | 3/2 | 1/0 | 18800/5743 |
| Tracing | 4/3 | 2/1 | 35534/14118 |
| Structured logs | 8/8, step limit | 2/1 | 74258/11584 |
| Long series | 3/2 | 3/2 | 17539/6295 |

Candidate six answer contracts and expected-value screening passed. Manual checks
confirmed the five distinct metric-instance values/times, two different trace
span IDs/units, logging coverage 120 matched / 100 retrieved / 20 returned, and
OOM-vs-cumulative-restarts distinction. This is sampled factual review, not proof
of universal correctness. In r8, lifecycle needed one read; in r9, three: **the
large-inventory round-trip regression remains variable and unresolved**.

R7 was stopped after discovering a temporary legacy-reader default mismatch; it
is excluded. Compatibility was restored and covered by tests. r8/r9 used successive
reader/encoding candidates; later source-directory and explicit-error changes have
unit/live-compactor verification, not a repeated complete six-case comparison.

### Actual workflow and frontend checks

An isolated Python process inside the current backend Pod imports worktree modules
in memory. Serving code/config is unchanged. Its tools are restricted to the
existing read tool set; repair is disabled, no faulty workloads were created.

- `intent-smoke-800185737d8f`: real xnet list, 4 Running Pods, one tool call, 65.20s.
- `intent-smoke-9e02168258fb`: same-session follow-up resolves xnet and correctly
  maps all four Pods to nodes, one tool call, 12.81s; session memory saved.
- `intent-smoke-23db5da2eefa`: real two-lane deep investigation called Metrics,
  Logging, Tracing, topology and OOM Runbook; both lanes finished. Final fan-in
  required three summary chunks and did not complete within the observation
  period (>12 minutes total); the isolated test PID was terminated. Not a pass.
- A second investigation `intent-smoke-695684ffd114` includes inherited-evidence
  accounting. Both lanes entered independently; final fan-in still required four
  summary chunks plus a merge. This demonstrates a remaining material-assembly
  bottleneck, not evidence that the whole pipeline is solved.
- Browser replay against the unchanged served frontend: direct query passed.
  Parallel replay passed initial per-group progress/partial-group checks, then
  failed the existing final-status assertion (`本次仅部分完成`). This replay injects
  SSE and bypasses the backend, so it is not caused by candidate tool processing;
  full parallel UI acceptance must not be claimed. Chromium used existing local
  library files; no host package changes were made.

The existing legacy replay suite has 2 failures/2 passes. The same failures were
reproduced from an isolated archive of checkpoint `5d70ada7`; no tests were weakened.
Latest full unit/guidance counts and the second deep-run terminal outcome are
recorded in the completion addendum below.

### Release decision

**Hold production rollout.** Serial accumulation behavior and source integrity
improved, but broad adoption is not justified by the live deep-diagnosis/fan-in
results. A shared evidence-reference handoff instead of repeated large material
assembly is a separate architecture decision requiring discussion before coding.
No images, Secrets, PVCs, MCP or frontend deployments were changed. Existing
checkpoints remain; prototype changes are intentionally uncommitted.

## Completion addendum

- Final backend unit/guidance suite: **1797 passed**, 27 existing deprecation
  warnings, 25.33s. Targeted static checks and `git diff --check` passed.
- Second real deep run returned after **649.217s**, `status=partial`, reporting
  **step_limit**. It issued 32 tool results including 7 archive reads; three
  agent-history replacement events were followed by a four-chunk final-material
  compaction plus merge. It disclosed incomplete evidence and did not execute
  repairs. This is a terminal result, **not end-to-end acceptance**.
- The deep-run code snapshots predate the final source-directory/lookup-status
  corrections. Those last corrections passed unit and live synthetic-compactor
  tests, but no full final-version deep-run success is claimed.
- Both isolated workflow processes are now finished/terminated; the production
  process remains healthy, Deployment 1/1 on the unchanged baseline image. No
  background test continues using the provider.
- Remaining decision: redesign the generic inter-node/parallel evidence handoff
  so shared source material is not repeatedly assembled into large final inputs,
  and evaluate useful initial views/precise reads against broad inventories.
  Do not raise step limits or broadly enable the candidate to conceal this result.
