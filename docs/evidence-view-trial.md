# Evidence view trial — design and acceptance plan

## Checkpoint before implementation

2026-10-09: backend `5d70ada7`, MCP `4600af1`, frontend `aac3c10`.
Each checkpoint was pushed to its existing GitLab and GitHub branch. Credentials,
virtual environments and ignored runtime archives are not part of the snapshot.
This records working trees, not a claim that every file is deployed.

Production baseline images:
- backend: `aiops-copilot:11.0.204-pod-lifecycle-20261009`
- MCP: `mcp-server-manager:7.0.33-pod-lifecycle-10m-20261009`

## Scope and flow

One backend evidence-view module, opt-in during evaluation. MCP collection,
diagnosis routing, prompts and repair policy are unchanged. The approved follow-up
adds a cumulative trigger to the existing history-replacement mechanism.

1. Archive the complete received response before projecting it.
2. Keep small responses unchanged.
3. For JSON, remove formatting and factor exactly equal fields shared by object
   records. This is reversible structural encoding, not selection by symptoms.
4. If the data still exceeds the view budget, expose a bounded navigable view:
   actual JSON pointers, counts, source-order records, completeness and retrieval.
   Long records remain discoverable; never label omitted records absent.
5. Agent chooses whether to read a subtree, record page, selected fields or search
   the archived response. Read access stays inside existing archive roots.
6. Count live tool exchanges, archive reads and inherited node evidence together.
   When their high-water mark is exceeded, use the existing intent-aware history
   compactor and retain a bounded suffix of complete interactions. Replace history
   only after the summary and the post-compaction budget check succeed.
7. The whole-request context guard remains independent and can trigger earlier
   when prompts, schemas, drafts or parallel fan-in occupy substantial space.

Source status/coverage, view completeness, historical completeness and frontend
display truncation are distinct. Values, zeros, false, null, identities, units,
timestamps and edge endpoints are not altered. Compact encodings explicitly state
how shared fields apply. No automatic numeric aggregation or fault classification.

The proposal to admit a large result whenever remaining context permits was
rejected: serial results would quickly consume that temporary headroom. Large
responses are therefore bounded from the first return, irrespective of free space.

## Configuration and responsibilities

All switches are process environment settings; defaults remain **legacy/off**.

| Setting | Candidate default | Responsibility |
|---|---:|---|
| `AIOPS_EVIDENCE_VIEW_MODE` | `legacy` | `compact` enables views, reader and cumulative policy together |
| `AIOPS_EVIDENCE_RESULT_TOKENS` | 4096 | Maximum estimated tokens per observation/archive read |
| `AIOPS_EVIDENCE_HISTORY_TOKENS` | 24000 | Live tool interaction high-water mark |
| `AIOPS_EVIDENCE_RECENT_TOKENS` | 8000 | Maximum recent complete interactions retained after replacement |

Smaller model windows reduce history/recent limits to 45%/15% of the configured
window, respectively; recent is also capped at one third of the history limit.
Invalid settings fail explicitly. Response size uses UTF-8 bytes/3 estimation;
history uses the existing configured counter. These are not provider-exact token
guarantees. System/schema/output reservations remain enforced by the original guard.

- `evidence_view.py`: pure cross-tool structural projection, source pointers and
  exact reversible factoring/table encoding. No health classification or PromQL.
- `evidence_policy.py`: immutable per-process policy; no shared mutable counters.
- `ObservationProcessor`: archive first, preserve producer/UI contracts, choose
  a bounded view. Compact failures do not silently fall back to a 3000-char cut.
- Archive reader: bounded JSON pointers, fields, search and pagination; explicit
  raw reads also obey the per-read cap. Invalid lookups use the existing `Error:`
  protocol, not successful empty data. A complete subtree is distinguished from
  a complete response and from upstream datasource coverage.
- `WorkingContextMiddleware`: recount current state (including handoffs); each
  lane has independent replacement and audit files. Parallel calls remain atomic.
  Store a source directory with tool name/arguments/raw_ref separately from LLM
  text, and keep archive provenance in the summary input and retained messages.

Exceptions to observation reprojection remain reference/control operations
(`fetch_runbook`, `TodoWrite`, `read_context_archive`); their live messages are
still counted. The archive reader enforces its own limit. Non-agent RCA/conclusion
material currently still uses the existing whole-request trigger, not an assertion
that all merged lanes fit in a 24k workspace. **Parallel fan-in remains a release
gate; do not describe this prototype as globally bounded across all nodes.**

## Test matrix (defined before code changes)

| Case | Required evidence / behavior |
|---|---|
| Small Pod list / simple scalar | Same factual response, no extra read required |
| Running+Ready with recent termination | Lifecycle reason, time, restart uncertainty preserved |
| Real five-edge topology | Both ownership hops discoverable; no conflation by relation name |
| Long single metric series | Labels retained; samples retrievable, never silently zero series |
| Many instances / trace IDs | No identity merging or deduplication of distinct observations |
| Logs with late error then recovery | Both remain searchable; no first-N-only claim of completeness |
| Zero, false, null, empty, tool error | Preserve distinctions; no invented healthy state |
| Very large individual record/string | Explicit reference and bounded retrieval, no silent discard |
| Pagination | Real offsets/pointers, no fabricated upstream continuation token |
| Invalid JSON / unstructured tables | Lossless raw archive and explicit text mode |
| Missing archive / invalid pointer / traversal | Explicit failure; no outside-root reads |
| Concurrent results / historical compaction | Isolated references and bounded aggregate context |

## Comparison method and release gates

- Offline paired replay: exact same archived MCP responses for old summary,
  full-raw reference and new view. Synthetic cases are labeled, not live claims.
- Structural checks: round-trip encoding; exact facts and coverage; complete
  page reconstruction; bounded views; measured projection CPU time and size.
- Paired LLM checks: same task/model/evidence; assess evidence usage and missing
  information, not answer wording. Record model calls/tokens, archive reads,
  redundant external calls, compactions and wall time. Repeat nondeterministic cases.
- Integration: actual frontend-proxied quick query, follow-up memory, deep query
  and parallel groups. Read-only; no new fault resources or repair approvals.
- All safety/integrity cases must pass. New behavior must be no worse in factual
  correctness for evaluated cases and better in the majority on evidence retention
  or context cost without unjustified extra calls. Report raw baseline separately.
- Do not infer complete acceptance from unit tests or a healthy Deployment.
- If tests expose a tradeoff rather than overall improvement, retain opt-in mode
  and report the result; do not silently broaden rollout.

## Recovery

Keep legacy observation processing available behind the mode switch. Prototype
defaults off. Before a deployment, record the actual image digest and mode, then
enable only for controlled tests. Reverting the mode restores old processing for
new calls; restoring the recorded image restores executable code. Do not reset
working trees, erase archives/PVCs or rewrite the checkpoint commits.

## Results

Prototype implemented, default disabled. `AIOPS_EVIDENCE_VIEW_MODE=compact`
enables it; unset/`legacy` preserves both observation processing and the old
archive-reader tool schema/description. A process restart is required to reload
the tool catalog. No production configuration has been changed.

The first replay covered 13 cases across four real archived runs plus synthetic
edge cases, with legacy/raw/compact variants (39 model executions). Additional
repeated trials tested clearer completeness semantics, schema discovery, plain
field-name selectors, and an 8,192-token ceiling. Model: deployed
`openai/gpt-6-luna`, low. These are isolated evidence-consumption evaluations,
not full workflow/frontend end-to-end acceptance.

Findings so far:
- Whole topology chains and distinct metric/trace identities are recoverable.
- Generic same-field factoring and consecutive-line folding are reversible.
- Explicit execution errors on previously unknown tools must not inherit the
  legacy generic extractor's success flag; top-level failure signals are now
  handled independently of nested resource health.
- Metadata-only offloading of a large collection can cause extra reads and
  higher total input token usage. Smaller initial context is NOT proof of a
  more efficient run. The 4k candidate is not approved for broad rollout.
- Plain field names and object-vs-array projection semantics need ergonomic
  support; forcing users/models to guess JSON pointer syntax adds failed reads.
- An 8k candidate improved several medium-result cases but did not solve the
  large-inventory regression. It is an experiment, not a new production default.

Evidence and remaining gates are recorded in
`testreports/evidence_view_20261009/summary.md`. No claim is made that memory,
multi-group full diagnosis, historical compaction or frontend rendering has
passed with the new mode. Those integration gates remain pending.
