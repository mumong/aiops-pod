# K8s AIOps Copilot
![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)

English | [简体中文](README.md)

## Table of contents
- [Overview](#overview)
- [Key features](#key-features)
- [Quick start](#quick-start)
- [Usage](#usage)
- [Core settings](#core-settings)
- [Architecture](#architecture)
- [Documentation](#documentation)
- [License](#license)

## Overview
An AIOps assistant for Kubernetes: query clusters in natural language, diagnose failing Pods, then plan and run repairs.
- Every conclusion comes with evidence: symptom, root cause, supporting data and unknowns
- Repairs need human approval by default; dangerous commands are always blocked
- Works on a single cluster, or on many clusters managed through xnet (one center plus edges)

![Diagnosis with grouped evidence](docs/screenshots/pod-diagnosis-evidence.png)

## Key features
### Diagnosis and repair
✔️ Diagnosis: scheduling, image, mount, config, CrashLoop, OOM, probes, stuck deletion and more  
✔️ Live metrics, logs and traces through MCP; several failing Pods analysed in parallel  
✔️ Repair loop: plan → approve → execute → recovery watch, all audited  

### Multi-cluster and integration
⚡ Query and repair from the center; each edge runs only one runner  
⚡ Edges reached through the xnet tunnel, no edge kubeconfig needed  
⚡ HTTP/SSE, chat frontend, standard A2A for other agents  

## Quick start
### Requirements
- A Kubernetes cluster; a deploy host with `git`, `make`, `kubectl` and `python3` (with PyYAML)
- Observability installed (single cluster: Prometheus / Elasticsearch / Tempo; multi-cluster: VictoriaMetrics / VictoriaLogs on the center)
- Images are published on `xnet.registry.io:8443`, so nothing to build; the model settings in `deploy/secrets/core.yaml` ship with defaults

### Clone
```bash
mkdir -p ~/aiops-workspace && cd ~/aiops-workspace
git clone ssh://git@10.2.0.86:9922/wanghuhu/mcpstander.git
git clone ssh://git@10.2.0.86:9922/wanghuhu/holmegpt-agent.git
git clone ssh://git@10.2.0.86:9922/wanghuhu/aiops-frount.git
```

### Single cluster
```bash
cd ~/aiops-workspace/mcpstander     && make deploy
cd ~/aiops-workspace/holmegpt-agent && make deploy
cd ~/aiops-workspace/aiops-frount   && make deploy
```
Open `http://<node IP>:30082`. API: `:30800`; A2A: `:30801` (see [A2A](docs/a2a.md)).

### Multi-cluster
Prerequisite: the edges have joined the center through xnet (`kubectl get nodes` on the center shows `vc-…` virtual Nodes).

#### Install the center (run on a center node)
```bash
cd ~/aiops-workspace/holmegpt-agent
make mc-discover WRITE=1     # writes the joined clusters into deploy-edge/clusters.mc.yaml (between ###)
make mc-init                 # certificate, key, cluster config; prints the edge command at the end
cd ~/aiops-workspace/mcpstander     && make deploy-mc
cd ~/aiops-workspace/holmegpt-agent && make deploy-mc
cd ~/aiops-workspace/aiops-frount   && make deploy-mc
```

#### Join an edge (run on each edge node, no kubeconfig needed)
```bash
cd ~/aiops-workspace/holmegpt-agent
make edge-deploy EDGE=local RUNNER_KEY=<value printed by mc-init>   # RUNNER_LEVEL=1|2|3, default 2
```
Open `http://<center IP>:30082` and ask "which clusters do I have?".

### Try a failure
```bash
make case-deploy CASE=c08    # OOMKilled; all cases: make case-list
```
Ask in the frontend "why does the Pod in aiops-case-08 keep restarting?", then click "生成自动修复方案" (generate repair plan) under the report. Clean up with `make case-clean CASE=c08`.

### Upgrade
```bash
echo <new version> > VERSION && make build push deploy   # on a multi-cluster center use deploy-mc instead of deploy
```

### Uninstall and clean up
```bash
# Failure cases: run on the cluster that has them (on the edge node for edge cases)
cd ~/aiops-workspace/holmegpt-agent && make case-clean   # every case; just one: make case-clean CASE=c08

# Single cluster; on a multi-cluster center run the same three
cd ~/aiops-workspace/aiops-frount   && make delete
cd ~/aiops-workspace/holmegpt-agent && make delete
cd ~/aiops-workspace/mcpstander     && make delete

# Multi-cluster: on each edge node
cd ~/aiops-workspace/holmegpt-agent && make edge-delete EDGE=local
```
`make delete` keeps the namespaces and the run history (PVC); to remove the history too: `kubectl delete namespace aiops mcp`.

## Usage
### Web (recommended)
Open `http://<node IP>:30082` (the center IP for multi-cluster) and ask:

| Goal | Example |
|---|---|
| Query | "各节点 CPU 和内存使用率是多少？" (CPU and memory usage per node) |
| Diagnose | "我的集群 Pod 有什么问题？" (what is wrong with my Pods), "aiops-case-08 的 Pod 为什么一直重启？" |
| Multi-cluster | "我有哪些集群？" (which clusters), "edge-88 有什么 Pod 异常？" (it asks which cluster when none is named) |
| Repair | Click "生成自动修复方案" under the report → approve each action → recovery is watched automatically |
| Run a command | "helm list", "重启 default/nginx" (restart default/nginx) |

### API (scripts and other systems)
Queries and diagnoses take one command (`/ask` decides whether it is a query, a diagnosis or a command):
```bash
curl -N -G http://<node IP>:30800/ask --data-urlencode "q=我的集群现在有什么问题？"
```
To continue with a repair, link the calls into one session: pass the same `session_id` and keep the identity cookie with `-c/-b jar.txt` (repair records are visible only to the identity that ran the diagnosis):
```bash
B=http://<node IP>:30800; S=my-session-000001
curl -N -G $B/ask --data-urlencode "q=我的集群现在有什么问题？" -d session_id=$S -c jar.txt -b jar.txt   # diagnose
curl -N -G $B/ask --data-urlencode "q=修复刚刚的问题" -d session_id=$S -c jar.txt -b jar.txt             # plan a repair
curl -b jar.txt $B/repair/batches/batch-<diagnosis run_id>                                              # plan and pending approvals
```
Approval, plan feedback and cancel are in [HTTP API](docs/api.md); other agents call the standard A2A endpoint (`:30801`), see [A2A](docs/a2a.md).

### A2A (chat the way another agent would)
```bash
python3 scripts/a2a_chat.py                          # this node; another cluster: python3 scripts/a2a_chat.py http://<IP>:30801
```
Ask anything; at an approval type `y` to approve all or `n` to reject all; answer a clarifying question directly (e.g. "所有边缘集群"); `/new` starts a new conversation, `exit` quits.

## Core settings
Defaults work as-is; change only these when needed, then run `make deploy` in that repository (`make deploy-mc` on a multi-cluster center).

| What | Where | Notes |
|---|---|---|
| **Human approval / automatic repair** | `deploy/configmap/config.yaml` → `workflow.remediation.mode` | `review` (default) approves every action by hand; `auto` executes automatically (use with care in production). `enabled: false` plans only, never executes |
| Temporary switch | `PUT /repair/policy/mode` (with `AIOPS_ADMIN_TOKEN`) | e.g. `{"mode":"auto","ttl_minutes":30}`; reverts to the configured value when it expires, no redeploy; see [HTTP API](docs/api.md#6-策略与审计) |
| Dangerous-command rules | `denied_*` and `approval_required` under the same `workflow.remediation` | Denied commands never run; `approval_required` forces human approval even in auto. On multi-cluster, re-run `make edge-deploy` on each edge afterwards |
| Model | `deploy/secrets/core.yaml` | Model address, name, key, context size |
| Metrics / logs addresses | MCP repo `deploy/configmap.yaml` (`PROMETHEUS_URL`, `ES_URL`); multi-cluster: `### 核对 ###` in `deploy-edge/clusters.mc.yaml` | Change when the observability components move namespace or service name |
| Cluster list and aliases | Between the `### 替换开始 ###` markers of `deploy-edge/clusters.mc.yaml` | Multi-cluster only; generated by `make mc-discover WRITE=1` |
| Edge permission level | `make edge-deploy … RUNNER_LEVEL=1\|2\|3` | 1 read-only; 2 (default) common repairs; 3 admin |

Every setting: [Deployment and operations](docs/GUIDE.md).

## Architecture
```
user / frontend / A2A ──> AIOps Agent ──> MCP tools ──> K8s API, metrics, logs, traces
                              │                └─(multi-cluster) xnet tunnel ──> edge runner ──> edge K8s
                              └─ locate → evidence → root cause → conclusion → repair (approve → execute → watch)
```

## Documentation
| Document | Content |
|---|---|
| [Deployment and operations](docs/GUIDE.md) | Configuration, releases, routine changes, optional variables, troubleshooting |
| [Architecture](docs/ARCHITECTURE.md) | Full flow, repair and dangerous-command rules, limits |
| [HTTP API](docs/api.md) / [A2A](docs/a2a.md) | Interfaces and examples |
| [Multi-cluster design](docs/multi-cluster-design.md) | Center, edge runner, permission levels |
| [Failure cases](tests/cases/README.md) | Deploying and cleaning failure environments |

Development: Python 3.12; `make check` runs lint and unit tests.

## License
[Apache License 2.0](LICENSE). Third-party code keeps its own licenses.
