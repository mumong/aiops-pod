# K8s AIOps Copilot
![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)

English | [简体中文](README.md)

## Table of contents
- [Overview](#overview)
- [Key features](#key-features)
- [Quick start](#quick-start)
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
Ask in the frontend "why does the Pod in aiops-case-08 keep restarting?", then click "生成修复方案" (generate repair plan) under the report. Clean up with `make case-clean CASE=c08`.

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
