# K8s AIOps Copilot

面向 Kubernetes 的智能运维诊断助手。使用自然语言查询集群，按异常 Pod 独立采集现场证据，再生成包含现象、根因、依据和未知项的诊断报告。

## 核心能力

- **异常诊断**：调度、镜像、挂载、配置、CrashLoop、OOM、探针及删除阻塞等 Pod 故障。
- **三维可观测性**：通过 MCP 查询 Metrics、Logging、Tracing；支持按调查目的组合 PromQL、日志过滤和链路条件。
- **多对象分析**：每个异常 Pod 独立取证和 RCA，多组并行后汇总，单 Pod 使用同一条处理路径。
- **证据可回查**：工具响应、结构化结果和模型摘要分别归档，支持按引用补读。
- **对外接入**：HTTP/SSE、可选聊天前端、联邦多集群及标准 A2A Adapter。

Agent 负责规划和解释，MCP 查询真实数据，Runbook 提供排障知识。

## 配套项目与可观测性组件


| 项目 / 组件                                           | 职责                                                                           |
| ------------------------------------------------- | ---------------------------------------------------------------------------- |
| 本仓库                                               | FastAPI + LangGraph 诊断服务及 A2A Adapter                                        |
| [MCP 工具服务](http://10.2.0.86/wanghuhu/mcpstander)  | Kubernetes 与可观测性查询接口                                                         |
| [可观测性组件](http://10.2.0.86/platform/observability) | Prometheus 指标、Filebeat/Elasticsearch 日志、DeepFlow/ClickHouse 流量、Tempo 应用 Span |
| [聊天前端](http://10.2.0.86/wanghuhu/aiops-frount)    | 展示诊断进度、工具结果和报告，可选部署                                                          |


以上链接为内网仓库，需要相应网络和访问权限。先部署可观测性组件并确认数据入库，再按 MCP 仓库说明配置后端连接。MCP 不负责安装采集器；应用 Span 还需要埋点和链路上下文传播。

## 快速开始：复制命令部署

以下命令用于本文内网环境：节点地址 **10.2.0.48**，三个仓库统一下载到 **~/aiops-workspace**。在同一个 Bash 终端中依次复制执行，每一步成功后再进行下一步。

前提：Git/SSH 权限、kubectl 集群访问、私有镜像拉取和存储已就绪；[可观测性组件](http://10.2.0.86/platform/observability)已部署，MCP 仓库的后端配置与现场一致。其他环境必须先调整地址和连接配置。

重部署使用 **make delete deploy**：先删除再部署对应服务，期间服务中断。诊断或测试运行期间禁止重部署。首次部署可使用 make deploy，不加 -j。

### 1. 下载并部署 MCP

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

等待 mcp-server-manager 部署完成且 Pod Ready，再继续。镜像、后端和权限配置见 [MCP 仓库](http://10.2.0.86/wanghuhu/mcpstander)。

### 2. 下载并部署 Agent

```bash
cd ~/aiops-workspace
```

```bash
git clone --branch qwen-before-architecture ssh://git@10.2.0.86:9922/wanghuhu/holmegpt-agent.git
```

```bash
cd ~/aiops-workspace/holmegpt-agent
```

首次部署前，按[模型配置说明](docs/GUIDE.md#2-agent-配置)准备 `deploy/secrets/core.yaml`，填写模型名称、API Base、API Key 和上下文容量；已有配置保留，不提交真实凭据。单集群在 [config.yaml](deploy/configmap/config.yaml) 设置 `federation.enabled: false`，并核对 MCP 地址。

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

预期 aiops-copilot 为 2/2 Ready，PVC 为 Bound。健康接口可达不代表全部可观测后端正常，需同时检查 MCP 状态。

### 3. 下载并部署前端

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

部署完成后，浏览器打开 **[http://10.2.0.48:30081](http://10.2.0.48:30081)**。


| 入口             | 地址                                                                                                       |
| -------------- | -------------------------------------------------------------------------------------------------------- |
| 聊天前端           | [http://10.2.0.48:30081](http://10.2.0.48:30081)                                                         |
| Agent API      | [http://10.2.0.48:30800](http://10.2.0.48:30800)                                                         |
| A2A Agent Card | [http://1own/agent-card.json0.2.0.48:30801/.well-kn](http://10.2.0.48:30801/.well-known/agent-card.json) |




### 4. 创建异常测试 Case

回到 Agent 仓库。下面先部署 c08 OOMKilled：

```bash
cd ~/aiops-workspace/holmegpt-agent
```

```bash
make case-deploy CASE=c08
```

```bash
kubectl get pods -n aiops-case-08
```

也可以再部署 c04，体验两个异常 Pod 同时存在时的分组诊断：

```bash
make case-deploy CASE=c04
```

```bash
kubectl get pods -n aiops-case-04
```

常用基础 Case：


| Case | 预期异常状态 / 现象                       | 主要原因                        |
| ---- | --------------------------------- | --------------------------- |
| c01  | Pending / FailedScheduling        | 节点选择器无匹配节点                  |
| c02  | ImagePullBackOff                  | 镜像仓库域名不可解析                  |
| c03  | FailedMount                       | 卷引用的 ConfigMap 不存在          |
| c04  | CreateContainerConfigError        | 环境变量引用的 Secret key 缺失       |
| c05  | FailedCreatePodSandBox            | Multus 网络附件缺失，需要预先安装 Multus |
| c06  | CrashLoopBackOff / exit 2         | 应用运行时非零退出                   |
| c07  | 配置错误 / HTTP 500 / Trace / exit 78 | 应用配置缺失后退出                   |
| c08  | OOMKilled / exit 137              | 应用内存增长超过容器 limit            |
| c09  | Running、Ready=False / HTTP 503    | Readiness 检查失败              |
| c10  | Liveness 失败 / 反复重启                | 健康检查端点返回 HTTP 500           |
| c11  | Terminating                       | finalizer 阻止对象删除            |




### 5. 发起一次诊断

```bash
curl --no-buffer -G "http://10.2.0.48:30800/ask"  --data-urlencode "q=当前集群有什么问题？"
```

或打开前端，输入同样的问题。预期先看到问题定位和取证进度，最终报告列出异常 Pod、证据、根因与未知项；多个异常按组展示。具体结果取决于现场数据及模型分析，不保证每次判断都正确。

### 6. 完成体验后清理 Case

仅清理本次部署的测试环境；删除对应 namespace 内资源，不影响 aiops 和 mcp 服务：

```bash
cd ~/aiops-workspace/holmegpt-agent
```

```bash
make case-clean CASE=c08
```

```bash
make case-clean CASE=c04
```

```bash
make case-clean CASE=c01-cpu
```



## 其他使用方式

`/query` 与 `/ask` 先由 Agent 理解意图并输出 JSON 路由：日常查询和快速初查走“自主查询 → 总结”；Pod、命名空间或集群根因诊断走“定位 → 取证 → 根因 → 总结”。深度诊断不等于全量扫描，各节点围绕原问题自主选择只读工具和 Runbook，不执行固定采集兜底。前端显示 Markdown，SSE 的 `query_answer` 包含意图、范围、状态、正文、来源与缺失项；结构正确不代表诊断已核验。两接口共享 session_id 会话记忆及 54k 环境配置下的自动上下文压缩；进程内记忆在 Pod 重启后丢失。

```bash
curl -N -G "http://10.2.0.48:30800/query" --data-urlencode 'q=查询 xnet 命名空间下所有 Pod 的日志'
```

```bash
curl -N -G "http://10.2.0.48:30800/query"  --data-urlencode 'q=各节点当前 CPU 和内存使用率是多少？'
```



## 更新与重部署

修改代码时，在对应仓库更新 VERSION，再按顺序执行：

```bash
make build
```

```bash
make push
```

```bash
make deploy
```

make deploy 本身不会构建镜像。Agent、MCP、前端分别构建发布，不能只更新其中一个仓库的 VERSION 就认为三个服务均已升级。

已有测试环境需要先删除服务再部署时，可在对应仓库执行：

```bash
make delete deploy
```

注意 make 为小写；此操作会中断对应服务，不是首次部署或常规升级的必需步骤，不要加 -j 并行执行。Agent 的 make delete 保留报告 PVC；MCP、前端删除范围以各自 Makefile 为准。不要在运行诊断或质量测试时重部署。

日志、联邦部署和详细排查见[部署指南](docs/GUIDE.md)；后台质量测试和断点续跑见[质量测试说明](test/aiops_quality_e2e/README.md)。

## 核心文档


| 文档                                                   | 内容                          |
| ---------------------------------------------------- | --------------------------- |
| [部署与运维](docs/GUIDE.md)                               | 配置、发布、权限、联邦及常见排查            |
| [核心实现](docs/current-aiops-diagnosis-architecture.md) | 请求、Pod 分组、规划取证、RCA、上下文与归档   |
| [可观测性采集](docs/observability.md)                      | MCP 工具、PromQL 示例、日志与链路、结果含义 |
| [A2A 接入](docs/a2a-server.md)                         | 标准协议、客户端及鉴权                 |
| [异常环境](test/pod-anomaly-cases/README.md)             | 故障部署、验证和安全清理                |
| [质量测试](test/aiops_quality_e2e/README.md)             | 单场景、多根因、四项指标与报告             |


报告和工具归档默认写入 Pod 内的 `/tmp/aiops/reports`（PVC）。源码实现与当前线上版本可能不同，历史测试成绩不能直接代表当前部署效果。
