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

## Quick start: copy-paste deployment

The commands below target the internal reference environment: node address **10.2.0.48**, with all three repositories cloned into **~/aiops-workspace**. Run them in order in one Bash terminal, and only continue when a step succeeds.

Prerequisites: Git/SSH access, kubectl access to the cluster, private image pulls and storage are ready; the [observability stack](http://10.2.0.86/platform/observability) is deployed and the MCP backend configuration matches your site. Other environments must adjust addresses and connection settings first.

The agent's `make deploy` uses both the main service image and the A2A image for the current `VERSION`. If that version has not been fully published, run `make build` and `make push` (see the end of this document) first; publishing only the main image is not enough for a full deployment.

Redeploy with **make delete deploy**: it deletes and then redeploys the service, so the service is down meanwhile. Never redeploy while a diagnosis or test run is in progress. A first deployment can use `make deploy`; do not add `-j`.

### 1. Clone and deploy MCP

```bash
mkdir -p ~/aiops-workspace
```

```bash
cd ~/aiops-workspace
```

```bash
git clone http://10.2.0.86/wanghuhu/mcpstander.git
```

```bash
cd ~/aiops-workspace/mcpstander
```

```bash
make delete deploy
```

```bash
kubectl get pods,svc -n mcp
```

Wait until mcp-server-manager is deployed and its Pod is Ready before continuing. Images, backends and permissions are described in the [MCP repository](http://10.2.0.86/wanghuhu/mcpstander).

### 2. Clone and deploy the agent

```bash
cd ~/aiops-workspace
```

```bash
git clone --branch qwen-before-architecture ssh://git@10.2.0.86:9922/wanghuhu/holmegpt-agent.git
```

```bash
cd ~/aiops-workspace/holmegpt-agent
```

Before the first deployment, prepare `deploy/secrets/core.yaml` as described in [model configuration](docs/GUIDE.md#2-agent-配置): model name, API base, API key and context window. Keep any existing configuration and never commit real credentials. For a single cluster set `federation.enabled: false` in [config.yaml](deploy/configmap/config.yaml) and check the MCP addresses.

```bash
make delete deploy A2A_PUBLIC_HOST=10.2.0.48
```

```bash
kubectl get pods,svc,pvc -n aiops
```

```bash
curl -fsS http://10.2.0.48:30800/health
```

```bash
curl -fsS http://10.2.0.48:30800/api/v1/mcp/status
```

Expect aiops-copilot to be 2/2 Ready and the PVC to be Bound. A reachable health endpoint does not mean every observability backend works; check the MCP status as well.

### 3. Clone and deploy the frontend

```bash
cd ~/aiops-workspace
```

```bash
git clone ssh://git@10.2.0.86:9922/wanghuhu/aiops-frount.git
```

```bash
cd ~/aiops-workspace/aiops-frount
```

```bash
make delete deploy
```

```bash
kubectl get pods,svc -n aiops
```

Then open **[http://10.2.0.48:30081](http://10.2.0.48:30081)** in a browser.

| Entry point | Address |
|---|---|
| Chat frontend | [http://10.2.0.48:30081](http://10.2.0.48:30081) |
| Agent API | [http://10.2.0.48:30800](http://10.2.0.48:30800) |
| A2A Agent Card | [http://10.2.0.48:30801/.well-known/agent-card.json](http://10.2.0.48:30801/.well-known/agent-card.json) |

### 4. Create fault test cases

Go back to the agent repository and deploy c08 (OOMKilled):

```bash
cd ~/aiops-workspace/holmegpt-agent
```

```bash
make case-deploy CASE=c08
```

```bash
kubectl get pods -n aiops-case-08
```

You can also deploy c04 to try grouped diagnosis with two abnormal Pods at once:

```bash
make case-deploy CASE=c04
```

```bash
kubectl get pods -n aiops-case-04
```

Common base cases:

| Case | Expected state / symptom | Main cause |
|---|---|---|
| c01 | Pending / FailedScheduling | Node selector matches no node |
| c02 | ImagePullBackOff | Registry hostname does not resolve |
| c03 | FailedMount | Volume references a missing ConfigMap |
| c04 | CreateContainerConfigError | Environment variable references a missing Secret key |
| c05 | FailedCreatePodSandBox | Multus network attachment missing (Multus must be installed) |
| c06 | CrashLoopBackOff / exit 2 | Application exits non-zero at runtime |
| c07 | Config error / HTTP 500 / trace / exit 78 | Application exits after missing configuration |
| c08 | OOMKilled / exit 137 | Application memory grows past the container limit |
| c09 | Running, Ready=False / HTTP 503 | Readiness check fails |
| c10 | Liveness failure / repeated restarts | Health endpoint returns HTTP 500 |
| c11 | Terminating | A finalizer blocks deletion |

### 5. Run a diagnosis

```bash
curl --no-buffer -G "http://10.2.0.48:30800/ask"  --data-urlencode "q=What is wrong in my cluster?"
```

Or ask the same question in the frontend. You should first see location and evidence progress; the final report lists abnormal Pods, evidence, root causes and unknowns, grouped when there are several. Results depend on live data and model analysis and are not guaranteed to be correct every time.

### 6. Clean up the cases

This removes only the test environments deployed above (resources in their namespaces); the aiops and mcp services are not affected:

```bash
cd ~/aiops-workspace/holmegpt-agent
```

```bash
make case-clean CASE=c08
```

```bash
make case-clean CASE=c04
```

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

## Updating and redeploying

The recommended one-step release: increment `VERSION`, then run `make release` (builds and pushes the images, then rolls the deployment; old Pods exit only after the `/ready` probe passes, a failed rollout is rolled back automatically and the new Pod's logs are printed; it no longer deletes before creating).

When you change code, update `VERSION` in that repository and run, in order:

```bash
make build
```

```bash
make push
```

```bash
make deploy
```

`make deploy` does not build images. The agent, MCP and frontend are built and published separately; updating `VERSION` in one repository does not upgrade the other two.

If an existing test environment must be deleted before redeploying, run in the repository concerned:

```bash
make delete deploy
```

`make` is lowercase. This interrupts the service and is not needed for a first deployment or a normal upgrade; do not use `-j`. The agent's `make delete` keeps the reports PVC; for MCP and the frontend see their Makefiles. Do not redeploy while a diagnosis or quality test is running.

Logs, federation and detailed troubleshooting are in the [deployment guide](docs/GUIDE.md); background quality tests and resumable runs are in the [quality test notes](test/aiops_quality_e2e/README.md).

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
| [Multi-cluster design](docs/multi-cluster-design.md) (Chinese) | Current multi-cluster design and implementation: cluster registration, data and execution paths, tunnel messages, routing scope, multi-cluster diagnosis, repair, operator-declared expected states, frontend, known limits (branch `008-multi-cluster`, not merged) |
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
