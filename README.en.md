# K8s AIOps Copilot

**English** | [中文](README.md)

An AI operations assistant for Kubernetes. Ask about your cluster in natural language; the agent collects live evidence for each abnormal Pod independently, then produces a diagnosis report with the symptom, root cause, supporting evidence and open questions.

## Background

Troubleshooting a Kubernetes Pod means combining resource state, events, logs, metrics and traces, and that evidence is spread across many tools and observability systems. This project drives queries and diagnosis through natural language, so operators spend less time switching tools and stitching evidence together.

## Features

- **Fault diagnosis**: scheduling, image pulls, volume mounts, configuration, CrashLoop, OOM, probes, stuck deletions and other Pod failures.
- **Three observability signals**: Metrics, Logging and Tracing through MCP; PromQL, log filters and trace conditions are combined according to what the investigation needs.
- **Multi-object analysis**: when a deep diagnosis finds several targets, evidence collection and RCA run per group in parallel and are then summarised; a single target goes straight to evidence and RCA through the same stages.
- **Traceable evidence**: raw tool responses, structured results and model summaries are archived separately and can be read back by reference.
- **Integration**: HTTP/SSE, an optional chat frontend, multi-cluster federation and a standard A2A adapter.
- **Self-diagnosing runs**: every run writes a ledger and engineering findings (repeated calls, step/time limits, model service errors, context compaction). `GET /runs/{run_id}` shows within a minute where the time went and which guard fired; see [Run diagnostics](docs/run-diagnostics.md).
- **Guards for small models**: repeated tool calls are answered with a notice instead of re-running; per-round call counts and repeats are capped; output budgets are set per call type; reasoning is fed back inside the tool loop; the tool loop does not force a tool call every round (`llm.loop_tool_choice`). All of these are configuration, with no special cases per fault type or metric name.

The agent plans and explains, MCP queries real data, and runbooks supply troubleshooting knowledge.

## Screenshots

Real screenshots of the flow from a natural-language query, through fault diagnosis, to a human-approved repair. The UI may differ slightly between screenshots and deployed versions. Click an image to view it full size.

### Natural-language queries and resource usage

Ask "what is the CPU and memory usage of each node" and see the query target, run details and the analysis.

![Natural-language query for node CPU and memory usage](docs/screenshots/resource-query-overview.png)

Expand a tool call to see the Prometheus query parameters and results that the answer is based on.

![Prometheus tool call details and parameters](docs/screenshots/resource-query-tool-details.png)

The final answer summarises CPU and memory usage per node, together with the PromQL used.

![Per-node CPU and memory usage summary](docs/screenshots/node-cpu-memory-results.png)

### Fault diagnosis and root cause analysis

Several abnormal Pods are summarised, and each group shows its live evidence: Kubernetes state, events and metrics.

![Multi-Pod overview and grouped diagnosis evidence](docs/screenshots/pod-diagnosis-evidence.png)

Container memory limits, logs and metrics are combined into the causal chain from memory growth to OOM, process exit and CrashLoopBackOff.

![Evidence correlation and root cause analysis of an OOM failure](docs/screenshots/oom-root-cause-analysis.png)

### Human approval and repair result

After diagnosis the repair plan is shown with its execute and verify commands, stage timings and call statistics, for the user to review and approve.

![Repair plan and human approval](docs/screenshots/remediation-approval.png)

After the plan and each action are approved, the verification result is shown. The example removes a finalizer that blocked a Pod deletion.

![Completed repair after the plan and action were approved](docs/screenshots/remediation-completed.png)

## Companion projects and observability components

| Project / component | Responsibility |
|---|---|
| This repository | FastAPI + LangGraph diagnosis service and A2A adapter |
| [MCP tool server](http://10.2.0.86/wanghuhu/mcpstander) | Kubernetes and observability query tools |
| [Observability stack](http://10.2.0.86/platform/observability) | Prometheus metrics, Filebeat/Elasticsearch logs, DeepFlow/ClickHouse flows, Tempo application spans |
| [Chat frontend](http://10.2.0.86/wanghuhu/aiops-frount) | Shows diagnosis progress, tool results and reports; optional |

These links point to an internal network and need matching access. Deploy the observability stack first and confirm data is being ingested, then configure the backend connections as described in the MCP repository. MCP does not install collectors; application spans also need instrumentation and trace-context propagation.

## Deployment (copy and paste)

Three repositories work together: this one (the agent), the [MCP tool service](http://10.2.0.86/wanghuhu/mcpstander) and the [chat frontend](http://10.2.0.86/wanghuhu/aiops-frount). Images are published in `xnet.registry.io:8443`, so deploying needs no build.

The deploy host needs `git`, `make`, `kubectl` (pointing at the target cluster) and `python3` with PyYAML. Install the observability components first (single cluster: Prometheus / Elasticsearch / Tempo, addresses configured in the MCP repository; multi-cluster: VictoriaMetrics / VictoriaLogs on the center).

### 0. Clone and fill in the model settings (once)

```bash
mkdir -p ~/aiops-workspace && cd ~/aiops-workspace
git clone --branch main http://10.2.0.86/wanghuhu/mcpstander.git
git clone --branch main ssh://git@10.2.0.86:9922/wanghuhu/holmegpt-agent.git
git clone --branch main ssh://git@10.2.0.86:9922/wanghuhu/aiops-frount.git
mkdir -p holmegpt-agent/deploy/secrets
cp holmegpt-agent/config/examples/aiops-secret.yaml holmegpt-agent/deploy/secrets/core.yaml
vi holmegpt-agent/deploy/secrets/core.yaml   # LLM_MODEL, LLM_API_BASE, LLM_API_KEY, MODEL_CONTEXT_WINDOW
```

`core.yaml` is in `.gitignore`. Every `make deploy` writes it to the cluster Secret, so it must hold the real settings.

### 1. Single cluster

```bash
cd ~/aiops-workspace/mcpstander     && make deploy
cd ~/aiops-workspace/holmegpt-agent && make deploy
cd ~/aiops-workspace/aiops-frount   && make deploy
IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
curl -fsS http://$IP:30800/health && printf "\nfrontend: http://$IP:30081\n"
```

| Entry | Address |
|---|---|
| Chat frontend | `http://<node IP>:30081` |
| Agent API | `http://<node IP>:30800` |
| A2A (for other agents) | `http://<node IP>:30801/.well-known/agent-card.json`, see [A2A](docs/a2a.md) |

### 2. Multi-cluster (one center, several edges)

Prerequisites: the edges are connected to the center through xnet-cloud (`kubectl get nodes` on the center lists a `vc-…` virtual Node per edge), and each edge's vmagent / vlagent pushes to VictoriaMetrics / VictoriaLogs on the center. `make mc-init` handles the xnet certificate and the runner signing key.

**Center** (run on the center node, kubectl pointing at the center):

```bash
cd ~/aiops-workspace/holmegpt-agent
make mc-discover                      # lists the clusters connected through xnet
vi deploy-edge/clusters.mc.yaml       # paste the printed clusters: block; rename aliases (e.g. edge-88); check the VictoriaMetrics/VictoriaLogs URLs
make mc-init                          # certificate, signing key, cluster config -> mcp and aiops namespaces
cd ~/aiops-workspace/mcpstander     && make deploy-mc
cd ~/aiops-workspace/holmegpt-agent && make deploy-mc
cd ~/aiops-workspace/aiops-frount   && make deploy-mc   # frontend on 30082 (xnet uses 30081)
```

**Each edge** gets one runner (edge kubeconfigs in `~/.kube/aiops-mc/<alias>` on the center):

```bash
cd ~/aiops-workspace/holmegpt-agent
make edge-deploy EDGE=edge-88                    # level 2 by default
make edge-deploy EDGE=edge-89 RUNNER_LEVEL=1     # 1 read-only / 2 standard / 3 admin
```

To run it on the edge node instead, copy the center's `~/.kube/aiops-mc/runner.key` to the same path on the edge and run `make edge-deploy EDGE=local`.

Check: open `http://<center IP>:30082`, ask "which clusters do I have?" (all should be online), then "what Pods are failing on edge-88?".

Runner levels: 1 diagnoses only; 2 reads everything (Secret values are redacted) and changes common repair objects (Pods, workloads, ConfigMaps, Services, PVCs, HPAs, Jobs, Ingresses, …) but not Secrets or RBAC; 3 is cluster-admin. See the [multi-cluster design](docs/multi-cluster-design.md) §5.2.

### 3. Upgrading

Make sure no diagnosis or repair is running (a release interrupts it), then in each changed repository:

```bash
echo <new version> > VERSION
make build push deploy          # multi-cluster center: make build push deploy-mc
```

Release in the order MCP → agent → frontend, only the repositories that changed. `make deploy` is a rolling update: the old Pod leaves once the new one is ready, and a failed rollout is undone.

Edge runner: bump `deploy-edge/VERSION`, then `make runner-build runner-push edge-deploy EDGE=edge-88`.

### 4. Try it with a fault case

```bash
cd ~/aiops-workspace/holmegpt-agent
make case-deploy CASE=c08       # OOMKilled; make case-list shows all cases
```

Ask in the frontend "why does the Pod in aiops-case-08 keep restarting?", or:

```bash
curl -N -G http://<node IP>:30800/ask --data-urlencode "q=why does the Pod in aiops-case-08 keep restarting?"
```

Under the report, "generate repair plan" plans the fix; after approval it runs and the recovery is observed. Clean up with `make case-clean CASE=c08`.

| Case | Symptom | Cause |
|---|---|---|
| c01 | Pending | no node matches the node selector |
| c02 | ImagePullBackOff | registry host does not resolve |
| c03 | FailedMount | volume references a missing ConfigMap |
| c04 | CreateContainerConfigError | referenced Secret key is missing |
| c06 | CrashLoopBackOff | wrong variable name in the start script |
| c07 | exit 78, HTTP 500 | missing application config |
| c08 | OOMKilled | memory above the limit |
| c09 | Running, Ready=False | wrong readiness port |
| c10 | repeated restarts | liveness endpoint returns 500 |
| c11 | Terminating | a finalizer blocks deletion |

### 5. Day-to-day changes and removal

| Task | Command |
|---|---|
| Changed `config.yaml`, runbooks or `core.yaml` | single cluster `make deploy`; multi-cluster center `make deploy-mc` (agent repository) |
| Add an edge | center: `make mc-discover` → update `clusters.mc.yaml` → `make deploy-mc` in the agent and MCP repositories → `make edge-deploy EDGE=<new edge>` |
| Change the high-risk command rules (`workflow.remediation`) | center `make deploy-mc`, then `make edge-deploy` for every edge (the rules ship with the runner) |
| Rotate the xnet certificate | `make deploy-mc` in the agent and MCP repositories |
| Use a dedicated xnet certificate from operations | `make mc-init XNET_CERT_DIR=<dir with cert.pem, key.pem, ca.pem>` |
| Logs | `kubectl -n aiops logs deploy/aiops-copilot -c aiops-copilot -f` |
| Remove | `make delete` in each repository (keeps the report PVC); `make edge-delete EDGE=<alias>` per edge |

Optional variables (append to the make command, e.g. `make deploy-mc MC_A2A_PUBLIC_URL=https://aiops.example.com`):

| Variable | Default | Meaning |
|---|---|---|
| `CENTER_KUBECONFIG` | `~/.kube/aiops-mc/center`, else the current context | center cluster |
| `EDGE` | none, required | `EDGE=edge-88` uses `~/.kube/aiops-mc/edge-88`; `EDGE=local` the current context |
| `RUNNER_LEVEL` | `2` | runner permission level 1 / 2 / 3 |
| `A2A_PUBLIC_HOST` / `MC_A2A_PUBLIC_URL` | the cluster's first node (multi-cluster skips xnet virtual Nodes) | A2A address published in the Agent Card (single cluster / multi-cluster center) |
| `MC_CLUSTERS_FILE` | `deploy-edge/clusters.mc.yaml` | cluster config |
| `MC_KEY_FILE` | `~/.kube/aiops-mc/runner.key` | runner signing key; fetched from the center when missing locally |
| `MC_LOAD_HOSTS`, `MC_PULL_POLICY` | none, `Always` | test env only: side-load images over SSH when the registry cannot be pushed, e.g. `SSHPASS=… make deploy-mc MC_LOAD_HOSTS=10.2.5.85` |

Kubeconfigs are used only while deploying. At run time the center uses its own Pods' ServiceAccounts and each edge only the runner's. More settings: [Deployment and operations](docs/GUIDE.md) (Chinese).

## Other ways to use it

### Running commands and repairing Pods (human approval by default)

Two paths with separate responsibilities:

- **Run an explicit command** (for example "uninstall default/cloud-server", "run ls /tmp in Pod xx", "helm list"): the lightweight route `focused/operate`. The agent runs the command directly and then does at most one read-only check; there is no repair plan and no approval card. The high-risk command rules are the only gate, and both executions and refusals are audited.
- **Repair a diagnosed fault** ("generate repair plan" under a report, or "fix the problem just now" in the conversation): one planning job per abnormal group, run in parallel. Commands in a plan pass the high-risk rules, are approved according to the execution mode, run, and are followed by recovery observation (recovered / not recovered within the timeout / needs follow-up).

**Execution mode**: `workflow.remediation.mode: review` (default; every action needs human approval, and an expired approval cancels instead of approving) or `auto` (runs automatically; controlled environments only). An administrator holding `AIOPS_ADMIN_TOKEN` from the Secret can switch the mode at runtime for a limited time with `PUT /repair/policy/mode`; every change is audited.

**High-risk command rules** ("view rules" in the repair panel, `GET /repair/policy` to read, `POST /repair/policy/check` for a dry run) have three classes. Planning, execution and chat use the same rule set:

| Class | Contents | Handling |
|---|---|---|
| Always denied | Kubernetes: `taint`, `edit`, `cp`, `port-forward` and similar; writes to nodes, CRDs, cluster roles and other cluster-scoped resources; `--all`/`-A` bulk operations. Shell: `dd`, `mkfs`, `reboot`, `shutdown` and similar | Never executed; the refusal names the rule |
| Approval required | `drain`, deleting or changing a namespace, `rm` inside a Pod | Refused in chat; allowed in a repair plan but always waits for human approval, **also in auto mode** |
| Ordinary repair actions | `delete pod`, `patch`, `set env`, `rollout restart`, `scale` and similar | Approved or run automatically per the execution mode; still limited to the group's own objects and their controllers |

The MCP bash tool has its own gate, so the agent itself can never run the denied shell commands or `rm`; approved high-risk commands are run by the backend repair executor. Acceptance steps are in [high-risk command acceptance](docs/acceptance-blacklist.md); the lifecycle and boundaries are in section 5 of [architecture](docs/ARCHITECTURE.md).

A successful command does not mean the root cause is gone; check the recovery observation. Approval and repair locks live in process memory, so restart the job after a Pod restart, and do not run several replicas of the repair executor. The AIOps/MCP Kubernetes RBAC has cluster-admin rights; that is a credential-level permission and does not remove the command rules or human approval above.

`/query` and `/ask` first let the agent understand the intent and emit a JSON route. Everyday queries and quick checks are answered directly by the query agent as a structured answer, without a separate summary model. Root-cause diagnosis of a Pod, namespace or cluster runs "locate → evidence → root cause → summary", and several Pods can be collected and analysed in parallel groups. A deep diagnosis is not a full scan: each stage chooses read-only tools and runbooks around the original question, with no fixed fallback collection. The frontend renders Markdown; the SSE `query_answer` carries intent, scope, status, body, sources and missing items. A valid structure does not mean the diagnosis is verified. Both endpoints share `session_id` memory and automatic context compaction (54k configuration); in-process memory is lost when the Pod restarts.

```bash
curl -N -G "http://10.2.0.48:30800/query" --data-urlencode 'q=Show the logs of all Pods in the xnet namespace'
```

```bash
curl -N -G "http://10.2.0.48:30800/query"  --data-urlencode 'q=What is the current CPU and memory usage of each node?'
```

## Documentation

The documents below are written in Chinese.

| Document | Contents |
|---|---|
| [Architecture](docs/ARCHITECTURE.md) | Full lifecycle from user input to repair and recovery observation, data contracts, tool result handling, context compaction, boundaries and known limits |
| [HTTP API](docs/api.md) | Query, deep diagnosis, repair, approval and observation with curl; A2A and API identity backlog |
| [Deployment and operations](docs/GUIDE.md) | Configuration, releases, permissions, federation and common troubleshooting |
| [Run diagnostics](docs/run-diagnostics.md) | Per-run ledger, engineering finding types, `/runs/{run_id}` report |
| [LLM anomalies](docs/llm-model-anomalies.md) | Issues of the model / inference service itself, with external references |
| [High-risk command acceptance](docs/acceptance-blacklist.md) | Standard acceptance steps for the command blacklist and approval-required commands |
| [Multi-cluster design](docs/multi-cluster-design.md) (Chinese) | Multi-cluster design and implementation: cluster registration, data and execution paths, tunnel, routing scope, diagnosis, repair, runner permission levels, expected states, known limits |
| [Multi-cluster acceptance plan](docs/multi-cluster-acceptance.md) (Chinese) | Test layers, acceptance scripts (seam contracts, stream and frontend replay, false positives, intent accuracy measurement), per-phase cases and results |
| [Repair sprints](docs/remediation-sprint-design-2026-10.md) | Repair requirements, design and acceptance records |
| [Observability collection](docs/observability.md) | MCP tools, PromQL examples, logs and traces, meaning of results |
| [A2A](docs/a2a.md) | Standard protocol, client, authentication and real agent-to-agent tests |
| [Environment variables](docs/configuration-env.md) | Generated by `scripts/list_env_vars.py` |
| [Fault environments](test/pod-anomaly-cases/README.md) | Deploying, validating and safely cleaning faults (`make case-*` / `make repair-cases-*`) |
| [Quality tests](test/aiops_quality_e2e/README.md) | Single-scenario, multi-root-cause, four metrics and reports |

Historical process notes and old hand-over documents have been removed from the repository; they can be recovered from git history (before tag `baseline-20261019-run-3c052423`).

## Development

Python 3.12, matching the image. Runtime dependencies are in `requirements.runtime.txt` (HolmesGPT is installed separately by the Dockerfile), development tools in `requirements.dev.txt`, and A2A dependencies in `requirements.a2a*.txt` (separate virtualenv `.venv-a2a`).

```sh
make check          # syntax + lint (ruff E9/F/I/B) + format check + unit tests
make test-unit      # unit tests only (tests/unit)
make test-a2a       # A2A tests (needs .venv-a2a)
make release        # build and push images, then roll the deployment
```

Layout: `app/` service code, `a2a_adapter/` A2A adapter, `a2a_test_agent/` A2A test agent, `deploy/` Kubernetes manifests and configuration, `tests/` automated regression tests, `test/` fault environments and quality evaluation tools, `scripts/` run reports, environment-variable docs and acceptance scripts, `tools/` command-line clients, `config/examples/` Secret examples. Prompts are imported only from `app/core/prompts.py`; prompt changes need accompanying behaviour tests.

Reports and tool archives are written to `/tmp/aiops/reports` inside the Pod (PVC). Source code may differ from the version currently deployed, and historical test scores do not represent the current deployment.

## License

The project's own code is licensed under the [Apache License 2.0](LICENSE), which permits commercial use. Third-party code and dependencies keep their own licenses and attribution and are not relicensed by this project.
