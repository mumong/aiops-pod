# Optional record selection/counting — release verification

## Delivered scope

The existing `query_pod_lifecycle` accepts optional `record_type`, `fields`,
`where`, `match`, and `group_by`. With no new parameters its old result contract
is preserved. MCP performs typed selection/counting; the backend archives and
passes the complete computed packet without a second lossy summary. The frontend
shows row unit, source/page coverage, matched and unknown counts, records/groups,
display omissions and archive reference. Existing metrics rendering is retained.

This is the first adapter for a generic pure row-operation module, not universal
automatic compaction of every tool. There are no new diagnosis rules, repair
policies, routing decisions or summary-agent calls. Global context compaction and
ordinary full-lifecycle output are unchanged. Design/configuration details are in
[the approved proposal](evidence-record-integration-proposal.md).

## Verification

| Check | Result |
|---|---|
| MCP syntax and offline contracts | 263 tests passed |
| Backend actual release source (clean baseline + integration) | 1,733 unit/Runbook tests passed |
| Targeted backend contracts and Prometheus regression | 49 passed; targeted Ruff passed |
| Frontend tests/lint/TypeScript/Vite | 94 tests passed; build succeeded |
| Browser replay | Existing native/Pod metrics, new groups/selection, partial/unknown and persisted history passed |
| Live MCP SSE | Catalog includes optional schema; old output, nested predicates, counts, empty selection, unknown predicates and partial page passed |
| Actual frontend-proxied Query + same-session follow-up | Both successful; exact result events also replayed in browser without JavaScript errors |
| Model input preservation | Deployed raw and summary artifacts are byte-identical for both computed calls |
| Kubernetes rollout/health | Backend 2/2, frontend 1/1, MCP 1/1; frontend-proxied `/health` healthy |

Live runs using the unchanged `openai/gpt-6-luna` provider/model:

- `4540fbc9e2904c40`: natural request to count xnet Pods per node. Agent selected
  `record_type=pod, group_by=node`, one tool call. node1=2, master=1, node2=1;
  checked against the actual lifecycle list. Total 19.9 seconds.
- `250e69d9d85c47f4`: follow-up without repeating namespace, asking for containers
  with lifetime restart count above zero. Router retained xnet; Agent selected
  container fields and `restart_count_total > 0`, one tool call. Four rows with
  counts 2, 2, 4, 1; final answer matched tool evidence and explicitly distinguished
  lifetime counts from ten-minute counts. Total 20.8 seconds.

These samples establish integration, not universal model accuracy or 28B-model
behavior. Existing deprecation warnings and the frontend bundle-size warning
remain. Deep diagnosis, repair and long-history compaction were not rerun end to
end in this release; their serving code was not changed.

## Deployment and rollback

All images use prefix `xnet.registry.io:8443/xnet-cloud/`:

| Component | Deployed tag | Rollback tag |
|---|---|---|
| aiops-copilot | 11.0.205-records-20261009 | 11.0.204-pod-lifecycle-20261009 |
| aiops-copilot-frontend | 0.1.39-records-20261009 | 0.1.38 |
| mcp-server-manager | 7.0.34-records-20261009 | 7.0.33-pod-lifecycle-10m-20261009 |

Image config IDs:

```text
backend  sha256:8f562552089859d12829f63ad6d5701072204bbd5dadc7b127b9f327fc9d4993
frontend sha256:5a6c6a1fdd27d8331fd002d7fb9f6ce3f610b6f86fd907d06da06ff30d0684cf
mcp      sha256:cfa5b6788ba3539aacb5e2a05c909c6ca14bb702bda8adf1fd1ddb84fa5e95df
```

Registry TLS access failed, so versioned images were imported into containerd on
all three nodes. Live deployments use IfNotPresent; registry source manifests and
VERSION files were not rewritten for this temporary release. Consumers rolled
first, then MCP, then backend catalog refresh. MCP's prior live imagePullPolicy
was Always; restore it when returning to a working registry-based rollout.

Backend packaging starts FROM the prior live image and copies only
`record_result.py`, `stream_contract.py`, and baseline `observation.py` plus the
new contract hook. Base-image version metadata remains inherited; use the above
image tags/IDs to identify this scoped release. The three existing aicall module
hashes match git HEAD exactly. Pending local evidence-view experiments were not
shipped. Frontend copies verified dist onto its previous image; MCP copies only
the new engine/adapter and modified lifecycle/entrypoint modules.

Rollback order: revert/disable MCP optional capability first, then revert backend
and frontend images. Refresh backend catalog after provider changes. No Secret,
PVC, model setting, A2A sidecar or unrelated workload was changed. Two temporary
image-import Pods were deleted after successful imports; they held no workload
data. No Git commit or push was performed.

Build source, overlay Dockerfiles, exported images, complete live SSE, MCP
responses and browser screenshots are retained locally at:
`/tmp/aiops-record-release-20261009.frAcTg/`.

## Deliberate limits

- Counting covers the fetched page only. No hidden full-cluster aggregation.
- Oversized computed packets fail explicitly at the configured byte bound;
  Agent must narrow fields/scope, filter, group or page. No silent sampling.
- Unknown predicate values remain counted as unknown, not confirmed negatives.
- Full original Kubernetes objects are not archived by this adapter; the archive
  is the computed tool response. Requeries may observe a newer resource version.
- No guarantee that every task will select the most efficient parameters. The
  capability is optional; broad legacy queries can still consume more context.
