# Minimal record-query integration — approved additive capability

## Decision

Recommend an additive capability on the existing `query_pod_lifecycle` tool,
not a new diagnostic route or a competing inventory tool. Keep the present
default response unchanged. When the Agent supplies optional record-query
arguments, execute the tested generic selection/counting engine in MCP and
return an explicitly versioned computed-result envelope.

Alternative: a separate MCP tool with its own result contract. This gives a
clean separation, but adds another tool/schema for the model to choose between.
The additive option is preferable for the stated small-model/simple-interface
goal. The user approved the additive approach on 2026-10-09.

## Responsibilities and flow

1. Agent chooses namespace/Pod/labels/window/page and optionally record type,
   requested fields, predicates, any/all matching, or a grouping field.
2. The current lifecycle collector retrieves the selected Kubernetes page and
   projects observed lifecycle facts. Existing credentials, RBAC, argv execution,
   request timeout and pagination behavior remain unchanged.
3. With no record-query arguments, return the existing `pod-lifecycle.v1` payload.
4. With record-query arguments, a source adapter maps facts to Pod or container
   rows. The generic engine filters all received rows before selection/counting.
   It does not classify health, infer a diagnosis, or silently invent conditions.
5. Return `evidence-records.v1` with execution status, executed query, source
   scope/time/window/page metadata, row unit, input/matched/unknown counts and
   exact rows or groups. Preserve row identity. An empty match is not a source
   failure; an unknown predicate is not a confirmed negative result.
6. Backend validates the explicit contract and archives the complete received
   result. A computed packet must not masquerade as a full Pod list or be cut
   again to a 3000-character summary. Existing global history compaction remains
   responsible for accumulated context, not this result parser.
7. The existing SSE projection adds record/group presentation data. Frontend
   presents counts and selected facts separately from Prometheus measurements;
   retain the current raw-result viewer, event identity and session history format.
8. Agent interprets the facts and answers through the existing answer contract.
   No additional LLM summary call or prescribed diagnostic sequence is added.

Example Agent arguments (illustration only, not an automatic query):

```json
{"record_type":"pod","group_by":"node","page_size":100}
```

For a termination investigation the Agent can instead choose container rows,
fields and a reason/time-window predicate. No OOM-specific query is injected by
the engine. Numeric comparisons are typed; zero, false and null remain distinct.

## Boundaries that must be visible

- Counts cover the fetched page, not unreceived pages. No automatic extra fetches
  or cross-page aggregation in this minimal change. Preserve continuation tokens.
- Pod and container counts are different units. Container records retain their
  role (app/init/ephemeral); matching multiple predicates uses the same row.
- Kubernetes lastState is not a window history. Lifetime restart counts do not
  become ten-minute restart counts. Unknown timestamps/state remain unknown.
- A full archived **computed tool response** is not a full archive of every
  underlying Kubernetes field. Requerying may observe a different resource
  version; source time/version must not be disguised as the previous snapshot.
- Oversized computed results fail explicitly under a configurable bound, with
  enough query/error metadata to refine the request. Do not introduce statistical
  profiles, representative sampling or semantic ranking in this change.
- Ordinary no-parameter lifecycle queries retain their existing behavior; the
  known cost of broad full-data queries remains a documented limitation.
- The previous evidence-view prototype stays disabled; do not bundle its history
  triggers, readers or handoff modifications into this release by accident.

## Implementation scope

| Component | Intended change | Preserve |
|---|---|---|
| MCP | Generic row engine, lifecycle adapter, optional tool parameters, versioned output | Old call/output contract, other tools, source security |
| Backend observation | Explicit new-contract parser and lossless computed-packet handling | Existing lifecycle and both Prometheus result families |
| Backend SSE | Generic record/group presentation projection | Event IDs, raw references, parallel groups, transport status |
| Frontend | Record/group summaries and coverage/unknown indicators | Old metrics, raw viewer, saved-history compatibility |

No arbitrary JMESPath/Python/Shell execution capability is introduced. The
experimental expression arm remains evaluation-only; production row operations
do not need its development dependency.

## Practical acceptance and release order

Do not repeat a broad model-optimization campaign. Use deterministic contracts
plus a small real integration check:

- Existing MCP lifecycle tests remain green; review only the intentionally changed
  tool description/schema when updating catalog snapshots.
- Cross-container, recovered state, null/zero/false, invalid fields, partial pages,
  empty results, upstream errors and oversized results retain tested semantics.
- Backend parses old/new contracts, keeps the complete computed packet in model
  input, and does not report a successful empty selection as tool failure.
- Frontend event/browser replay renders new records/counts and still handles old
  Prometheus/lifecycle events and persisted sessions.
- One actual read-only Query count and one lifecycle selection through MCP/backend
  and frontend proxy demonstrate correct wiring, real source refs and unchanged
  final response shape. A memory follow-up checks that the scope persists.
- Package only the intended integration changes. Record image digests and rollback
  images. Deploy consumers with backward compatibility before enabling the MCP
  capability. Disable the capability before rolling consumers back; preserve PVCs,
  credentials, older image references and in-flight requests.

Known model selection errors and variable provider latency are not hidden or
treated as requirements for more fault-specific fallback code. Small-model
validation remains limited by availability of a suitable endpoint; do not claim
the deployed `gpt-6-luna` tests establish 28B model behavior.

## Current status

Approved and deployed on 2026-10-09: optional selection/counting on the lifecycle
tool, with backend and frontend compatibility. See
[release verification](evidence-record-release-20261009.md) for exact artifacts,
live runs and limitations.

## Configuration and examples

MCP `AIOPS_RECORD_QUERY_ENABLED` defaults to `true`; set `false` and restart MCP
to hide the optional schema and reject record-query arguments. Calls without
those arguments remain available. Refresh the backend tool catalog after a
capability change. `AIOPS_RECORD_RESULT_MAX_BYTES` defaults to 12000 (allowed
1024–65536). Oversized computed results return an explicit error, not truncated
facts. These variables belong to the MCP process environment, not the LLM.

```json
{"namespace":"xnet","record_type":"pod","group_by":"node","page_size":100}
```

```json
{"record_type":"container","fields":["ready","restart_count_total","last_termination_reason","termination_within_window"],"where":[{"field":"restart_count_total","op":"gt","value":0}],"page_size":100}
```

Predicates support eq/ne/gt/gte/lt/lte and all/any on the same record. Identities
are always retained. Ordering comparisons accept numbers; equality is typed.
`null` compared with a non-null value is unknown and counted separately. No
automatic health predicate, window-restart estimate or extra query is injected.
The UI shows the first 20 computed records plus omitted count and raw/archive
access; this display limit does not shorten the model's computed packet.
