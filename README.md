# K8s AIOps Copilot
![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)

[English](README.en.md) | 简体中文

## 目录
- [项目概述](#项目概述)
- [核心功能](#核心功能)
- [快速开始](#快速开始)
- [架构设计](#架构设计)
- [文档](#文档)
- [许可证](#许可证)

## 项目概述
面向 Kubernetes 的智能运维助手：用自然语言查询集群、诊断异常 Pod、生成并执行修复方案。
- 结论附带证据：现象、根因、依据和未知项
- 修复默认人工审批，高危命令一律拦截
- 支持单集群，以及经 xnet 管理的多集群（一个中心 + 若干边缘）

![异常诊断与分组证据](docs/screenshots/pod-diagnosis-evidence.png)

## 核心功能
### 诊断与修复
✔️ 异常诊断：调度、镜像、挂载、配置、CrashLoop、OOM、探针、删除阻塞等  
✔️ 指标、日志、链路经 MCP 实时查询，多个异常 Pod 并行分析  
✔️ 修复闭环：方案 → 审批 → 执行 → 恢复观察，全程审计  

### 多集群与接入
⚡ 中心统一查询和修复，边缘只部署一个 runner  
⚡ 经 xnet 隧道访问边缘，不需要边缘 kubeconfig  
⚡ HTTP/SSE、聊天前端、标准 A2A（供其他 Agent 调用）  

## 快速开始
### 环境要求
- Kubernetes 集群；部署机有 `git`、`make`、`kubectl`、`python3`（含 PyYAML）
- 已部署可观测性组件（单集群：Prometheus / Elasticsearch / Tempo；多集群：中心的 VictoriaMetrics / VictoriaLogs）
- 镜像已发布在 `xnet.registry.io:8443`，无需构建；模型配置 `deploy/secrets/core.yaml` 已填好默认值

### 下载代码
```bash
mkdir -p ~/aiops-workspace && cd ~/aiops-workspace
git clone ssh://git@10.2.0.86:9922/wanghuhu/mcpstander.git
git clone ssh://git@10.2.0.86:9922/wanghuhu/holmegpt-agent.git
git clone ssh://git@10.2.0.86:9922/wanghuhu/aiops-frount.git
```

### 单集群
```bash
cd ~/aiops-workspace/mcpstander     && make deploy
cd ~/aiops-workspace/holmegpt-agent && make deploy
cd ~/aiops-workspace/aiops-frount   && make deploy
```
打开 `http://<节点IP>:30082`。API：`:30800`；A2A：`:30801`（见 [A2A](docs/a2a.md)）。

### 多集群
前提：边缘已经通过 xnet 接入中心（在中心执行 `kubectl get nodes`，能看到 `vc-…` 虚拟 Node）。

#### 安装中心（在中心节点执行）
```bash
cd ~/aiops-workspace/holmegpt-agent
make mc-discover WRITE=1     # 已接入的集群写入 deploy-edge/clusters.mc.yaml（### 之间）
make mc-init                 # 证书、密钥、集群配置；最后打印边缘要执行的命令
cd ~/aiops-workspace/mcpstander     && make deploy-mc
cd ~/aiops-workspace/holmegpt-agent && make deploy-mc
cd ~/aiops-workspace/aiops-frount   && make deploy-mc
```

#### 加入边缘（在每个边缘节点执行，不需要 kubeconfig）
```bash
cd ~/aiops-workspace/holmegpt-agent
make edge-deploy EDGE=local RUNNER_KEY=<mc-init 打印的值>   # RUNNER_LEVEL=1|2|3，默认 2
```
打开 `http://<中心IP>:30082`，问"我有哪些集群？"。

### 试一个异常
```bash
make case-deploy CASE=c08    # OOMKilled，全部 Case：make case-list
```
在前端问"aiops-case-08 的 Pod 为什么一直重启？"，然后在报告下点"生成修复方案"。用完执行 `make case-clean CASE=c08` 清理。

### 升级
```bash
echo <新版本号> > VERSION && make build push deploy   # 多集群中心把 deploy 换成 deploy-mc
```

### 卸载与清理
```bash
# 异常 Case：在 Case 所在集群执行（边缘的 Case 就在边缘节点执行）
cd ~/aiops-workspace/holmegpt-agent && make case-clean   # 清理全部 Case；只清一个：make case-clean CASE=c08

# 单集群；多集群时在中心执行同样三条
cd ~/aiops-workspace/aiops-frount   && make delete
cd ~/aiops-workspace/holmegpt-agent && make delete
cd ~/aiops-workspace/mcpstander     && make delete

# 多集群：每个边缘节点执行
cd ~/aiops-workspace/holmegpt-agent && make edge-delete EDGE=local
```
`make delete` 保留命名空间和运行历史（PVC）；要连历史一起删：`kubectl delete namespace aiops mcp`。

## 架构设计
```
用户 / 前端 / A2A ──> AIOps Agent ──> MCP 工具 ──> K8s API、指标、日志、链路
                         │                └─(多集群) xnet 隧道 ──> 边缘 runner ──> 边缘 K8s
                         └─ 定位 → 取证 → 根因 → 结论 → 修复（审批 → 执行 → 恢复观察）
```

## 文档
| 文档 | 内容 |
|---|---|
| [部署与运维](docs/GUIDE.md) | 配置、发布、日常变更、可选变量、排查 |
| [核心架构](docs/ARCHITECTURE.md) | 完整流程、修复与高危命令规则、边界 |
| [HTTP API](docs/api.md) / [A2A](docs/a2a.md) | 接口与调用示例 |
| [多集群设计](docs/multi-cluster-design.md) | 中心、边缘 runner、权限等级 |
| [异常 Case](tests/cases/README.md) | 故障环境部署与清理 |

开发：Python 3.12，`make check` 运行 lint 和单元测试。

## 许可证
[Apache License 2.0](LICENSE)。第三方代码保留各自的许可证。
