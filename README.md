# K8s AIOps Copilot

[English](README.en.md) | **中文**

面向 Kubernetes 的智能运维诊断助手。使用自然语言查询集群，按异常 Pod 独立采集现场证据，再生成包含现象、根因、依据和未知项的诊断报告。

## 项目背景

Kubernetes Pod 排障需要结合资源状态、事件、日志、指标和链路信息，证据分散在多个工具与可观测性系统中。本项目通过自然语言交互组织查询和诊断，减少手动切换工具与汇总证据的工作。

## 核心功能

- **异常诊断**：调度、镜像、挂载、配置、CrashLoop、OOM、探针及删除阻塞等 Pod 故障。
- **三维可观测性**：通过 MCP 查询 Metrics、Logging、Tracing；支持按调查目的组合 PromQL、日志过滤和链路条件。
- **多对象分析**：自主深度诊断识别多个目标时分组并行取证和 RCA，再汇总；单目标直接进入取证与 RCA，复用相同阶段实现。
- **证据可回查**：工具响应、结构化结果和模型摘要分别归档，支持按引用补读。
- **对外接入**：HTTP/SSE、可选聊天前端、联邦多集群及标准 A2A Adapter。
- **运行可诊断**：每次运行产出账本与工程异常发现（重复调用、步数/时限、模型服务错误、上下文压缩等），`GET /runs/{run_id}` 一分钟看懂时间花在哪、哪个护栏触发；详见[运行诊断](docs/run-diagnostics.md)。
- **小模型护栏**：工具循环内重复调用不执行只提示、单轮调用数与重复次数有上限、输出预算按调用类型配置、工具循环内 reasoning 回传；全部是配置项，不含任何按故障类型或指标名的特判。

Agent 负责规划和解释，MCP 查询真实数据，Runbook 提供排障知识。

## 效果展示

以下为实际运行截图，展示从自然语言查询、故障诊断到人工审批修复的使用流程。不同截图的界面样式可能有所差异，具体以部署版本为准。点击图片可查看原图。

### 自然语言查询与资源使用率

输入“查询我各个节点的 CPU 和内存使用率”，查看查询目标、运行详情和分析过程。

![自然语言查询节点 CPU 和内存使用率](docs/screenshots/resource-query-overview.png)

展开工具调用，查看 Prometheus 查询参数与返回结果，追溯结论的数据来源。

![Prometheus 工具调用详情与查询参数](docs/screenshots/resource-query-tool-details.png)

最终按节点汇总 CPU、内存使用率，并展示对应的 PromQL 查询表达式。

![各节点 CPU 和内存使用率汇总](docs/screenshots/node-cpu-memory-results.png)

### 异常诊断与根因分析

汇总多个异常 Pod 的状态与关键信息，按组展示 Kubernetes 状态、事件和监控指标等现场证据。

![多 Pod 异常概览与分组诊断证据](docs/screenshots/pod-diagnosis-evidence.png)

结合容器内存限制、日志和指标，展示从内存增长到 OOM、进程退出及 CrashLoopBackOff 的因果链。

![OOM 故障的证据关联与根因分析](docs/screenshots/oom-root-cause-analysis.png)

### 人工审批与修复结果

诊断后展示修复方案、执行与验证命令，以及阶段耗时和调用统计，由用户审阅并批准修复方案。

![修复方案与人工审批界面](docs/screenshots/remediation-approval.png)

修复方案和具体动作分别审批后，展示执行后的验证结果；图中为解除 finalizer 删除阻塞的修复流程完成示例。

![修复方案及动作审批通过后的完成状态](docs/screenshots/remediation-completed.png)

## 配套项目与可观测性组件


| 项目 / 组件                                           | 职责                                                                           |
| ------------------------------------------------- | ---------------------------------------------------------------------------- |
| 本仓库                                               | FastAPI + LangGraph 诊断服务及 A2A Adapter                                        |
| [MCP 工具服务](http://10.2.0.86/wanghuhu/mcpstander)  | Kubernetes 与可观测性查询接口                                                         |
| [可观测性组件](http://10.2.0.86/platform/observability) | Prometheus 指标、Filebeat/Elasticsearch 日志、DeepFlow/ClickHouse 流量、Tempo 应用 Span |
| [聊天前端](http://10.2.0.86/wanghuhu/aiops-frount)    | 展示诊断进度、工具结果和报告，可选部署                                                          |


以上链接为内网仓库，需要相应网络和访问权限。先部署可观测性组件并确认数据入库，再按 MCP 仓库说明配置后端连接。MCP 不负责安装采集器；应用 Span 还需要埋点和链路上下文传播。

## 部署（复制即用）

三个仓库配合使用：本仓库（Agent）、[MCP 工具服务](http://10.2.0.86/wanghuhu/mcpstander)、[聊天前端](http://10.2.0.86/wanghuhu/aiops-frount)。镜像已发布在 `xnet.registry.io:8443`，直接部署不需要构建。

部署机需要 `git`、`make`、`kubectl`（指向目标集群）、`python3`（含 PyYAML）。可观测性组件需要先装好（单集群：Prometheus / Elasticsearch / Tempo，地址在 MCP 仓库配置；多集群：中心的 VictoriaMetrics / VictoriaLogs）。

### 0. 下载代码、填写模型配置（只做一次）

```bash
mkdir -p ~/aiops-workspace && cd ~/aiops-workspace
git clone --branch main http://10.2.0.86/wanghuhu/mcpstander.git
git clone --branch main ssh://git@10.2.0.86:9922/wanghuhu/holmegpt-agent.git
git clone --branch main ssh://git@10.2.0.86:9922/wanghuhu/aiops-frount.git
mkdir -p holmegpt-agent/deploy/secrets
cp holmegpt-agent/config/examples/aiops-secret.yaml holmegpt-agent/deploy/secrets/core.yaml
vi holmegpt-agent/deploy/secrets/core.yaml   # 填 LLM_MODEL、LLM_API_BASE、LLM_API_KEY、MODEL_CONTEXT_WINDOW
```

`core.yaml` 已加入 `.gitignore`，不会被提交。每次 `make deploy` 都会用它覆盖集群里的 Secret，所以它必须是真实配置。

### 1. 单集群

```bash
cd ~/aiops-workspace/mcpstander     && make deploy
cd ~/aiops-workspace/holmegpt-agent && make deploy
cd ~/aiops-workspace/aiops-frount   && make deploy
IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
curl -fsS http://$IP:30800/health && printf "\n前端：http://$IP:30081\n"
```

| 入口 | 地址 |
|---|---|
| 聊天前端 | `http://<节点IP>:30081` |
| Agent API | `http://<节点IP>:30800` |
| A2A（给其他 Agent 调用） | `http://<节点IP>:30801/.well-known/agent-card.json`，用法见 [A2A](docs/a2a.md) |

### 2. 多集群（一个中心 + 若干边缘）

前提：边缘已通过 xnet-cloud 接入中心（中心 `kubectl get nodes` 能看到每个边缘的 `vc-…` 虚拟 Node）；边缘的 vmagent / vlagent 把数据推到中心的 VictoriaMetrics / VictoriaLogs。xnet 证书和 runner 签名密钥由 `make mc-init` 自动处理，不需要手动操作。

**中心**（在中心节点上执行，kubectl 指向中心）：

```bash
cd ~/aiops-workspace/holmegpt-agent
make mc-discover                      # 列出 xnet 已接入的集群
vi deploy-edge/clusters.mc.yaml       # 把输出的 clusters: 块贴进去；别名可改（如 edge-88）；核对 VictoriaMetrics/VictoriaLogs 地址
make mc-init                          # 证书、签名密钥、集群配置 → mcp 和 aiops 命名空间
cd ~/aiops-workspace/mcpstander     && make deploy-mc
cd ~/aiops-workspace/holmegpt-agent && make deploy-mc
cd ~/aiops-workspace/aiops-frount   && make deploy-mc   # 前端端口 30082（30081 被 xnet 占用）
```

**每个边缘**部署一个 runner（边缘 kubeconfig 放在中心的 `~/.kube/aiops-mc/<别名>`）：

```bash
cd ~/aiops-workspace/holmegpt-agent
make edge-deploy EDGE=edge-88                    # 默认 2 级权限
make edge-deploy EDGE=edge-89 RUNNER_LEVEL=1     # 1 只读 / 2 标准 / 3 管理员
```

不想把边缘 kubeconfig 放到中心时，也可以在边缘节点上执行：先把中心的 `~/.kube/aiops-mc/runner.key` 拷到边缘同一路径，再执行 `make edge-deploy EDGE=local`。

验证：打开 `http://<中心IP>:30082` 问"我有哪些集群？"，各集群应显示为在线；再问"edge-88 有什么 Pod 异常？"。

runner 权限等级：1 只诊断；2 读全部（Secret 的值会被脱敏），可以改常见修复对象（Pod、工作负载、ConfigMap、Service、PVC、HPA、Job、Ingress 等），不能改 Secret 和 RBAC；3 为 cluster-admin。详见[多集群设计](docs/multi-cluster-design.md) §5.2。

### 3. 升级

先确认没有进行中的诊断或修复（发布会中断它们），然后在改过的仓库里执行：

```bash
echo <新版本号> > VERSION
make build push deploy          # 多集群中心：make build push deploy-mc
```

按 MCP → Agent → 前端的顺序发布，只发布改过的仓库。`make deploy` 是滚动更新：新 Pod 就绪后旧 Pod 才退出，失败会自动回滚。

边缘 runner 升级：改 `deploy-edge/VERSION`，然后执行 `make runner-build runner-push edge-deploy EDGE=edge-88`。

### 4. 试用：部署一个异常 Case

```bash
cd ~/aiops-workspace/holmegpt-agent
make case-deploy CASE=c08       # OOMKilled；make case-list 查看全部 Case
```

在前端问"aiops-case-08 的 Pod 为什么一直重启？"，或者用命令行：

```bash
curl -N -G http://<节点IP>:30800/ask --data-urlencode "q=aiops-case-08 的 Pod 为什么一直重启？"
```

报告下方点"生成修复方案"，审批后执行，随后自动观察恢复情况。试用结束清理：`make case-clean CASE=c08`。

| Case | 现象 | 原因 |
|---|---|---|
| c01 | Pending | 节点选择器无匹配节点 |
| c02 | ImagePullBackOff | 镜像仓库域名不可解析 |
| c03 | FailedMount | 卷引用的 ConfigMap 不存在 |
| c04 | CreateContainerConfigError | 引用的 Secret key 缺失 |
| c06 | CrashLoopBackOff | 启动脚本变量名错误 |
| c07 | 退出码 78、HTTP 500 | 应用配置缺失 |
| c08 | OOMKilled | 内存超过 limit |
| c09 | Running、Ready=False | Readiness 端口错误 |
| c10 | 反复重启 | Liveness 返回 500 |
| c11 | Terminating | finalizer 阻止删除 |

### 5. 日常变更与卸载

| 场景 | 命令 |
|---|---|
| 改了 `config.yaml`、Runbook 或 `core.yaml` | 单集群 `make deploy`，多集群中心 `make deploy-mc`（Agent 仓库） |
| 新增一个边缘 | 中心：`make mc-discover` → 更新 `clusters.mc.yaml` → Agent 仓库和 MCP 仓库各执行 `make deploy-mc` → `make edge-deploy EDGE=<新边缘>` |
| 修改高危命令规则（`workflow.remediation`） | 中心 `make deploy-mc`，并对每个边缘重新执行 `make edge-deploy`（规则随 runner 下发） |
| xnet 证书轮换 | Agent 仓库和 MCP 仓库各执行 `make deploy-mc` |
| 使用运维提供的专用 xnet 证书 | `make mc-init XNET_CERT_DIR=<含 cert.pem、key.pem、ca.pem 的目录>` |
| 查看日志 | `kubectl -n aiops logs deploy/aiops-copilot -c aiops-copilot -f` |
| 卸载 | 各仓库执行 `make delete`（保留报告 PVC）；边缘执行 `make edge-delete EDGE=<别名>` |

kubeconfig 只在部署时使用。运行时中心只用自己 Pod 的 ServiceAccount，边缘只用 runner 的 ServiceAccount。更多配置项见[部署与运维](docs/GUIDE.md)。

## 其他使用方式

### 执行命令与 Pod 修复（默认人工审批）

两条路径，职责分开：

- **执行明确的命令**（如"卸载 default/cloud-server""在 xx Pod 里执行 ls /tmp""helm list"）：走轻量路由 `focused/operate`，Agent 直接执行，之后最多做一次只读确认，不制定修复方案、不弹审批卡。高危命令规则是唯一的闸门，执行与拦截都写审计。
- **修复已诊断的异常**（报告下"生成修复方案"，或会话中说"修复刚才的问题"）：按异常组并发规划，每组一个独立任务；方案中的命令先过高危规则，再按执行方式审批后执行，最后进入恢复观察（已恢复 / 超时未恢复 / 待复查）。

**执行方式**：`workflow.remediation.mode: review`（默认，每个动作人工审批，超时取消而非自动批准）或 `auto`（自动执行，仅限受控环境）。管理员可凭 Secret 中的 `AIOPS_ADMIN_TOKEN` 调 `PUT /repair/policy/mode` 做有时限的运行时切换，变更写审计。

**高危命令规则**（网页修复区"查看拦截规则"，`GET /repair/policy` 可查，`POST /repair/policy/check` 可干跑）分三类，规划、执行、对话三条路径使用同一套：

| 类别 | 内容 | 处理 |
|---|---|---|
| 绝对禁止 | Kubernetes：`taint`、`edit`、`cp`、`port-forward` 等；写节点、CRD、集群角色等集群级资源；`--all`/`-A` 批量操作。Shell：`dd`、`mkfs`、`reboot`、`shutdown` 等 | 任何情况都不执行，拒绝时带规则名 |
| 需人工审批 | `drain`、删除/修改命名空间、Pod 内 `rm` | 对话中拦截；修复方案中可用，执行前强制人工审批，**自动执行模式也一样** |
| 普通修复动作 | `delete pod`、`patch`、`set env`、`rollout restart`、`scale` 等 | 按执行方式审批或自动执行，仍受"只改本组对象及其控制器"的范围校验 |

MCP 的 bash 工具另有一道闸，Agent 自己执行不了 Shell 禁止命令和 `rm`；经批准的高危命令由后端修复执行器执行。验收步骤见[高危命令黑名单验收](docs/acceptance-blacklist.md)，生命周期与边界见[核心流程与模块架构](docs/ARCHITECTURE.md)第 5 节。

命令成功不等于根因已消除，仍需结合恢复观察复查。审批和修复互斥状态为进程内存，Pod 重启后需重新发起；不要据此部署多副本修复执行器。AIOps/MCP 的 Kubernetes RBAC 为集群管理权限，这是凭据层权限，不取消上述命令规则和人工审批。

`/query` 与 `/ask` 先由 Agent 理解意图并输出 JSON 路由：日常查询和快速初查由查询 Agent 直接生成结构化答案，不再调用独立总结模型；Pod、命名空间或集群根因诊断走“定位 → 取证 → 根因 → 总结”，多个 Pod 可分组并发取证和分析。深度诊断不等于全量扫描，各节点围绕原问题自主选择只读工具和 Runbook，不执行固定采集兜底。前端显示 Markdown，SSE 的 `query_answer` 包含意图、范围、状态、正文、来源与缺失项；结构正确不代表诊断已核验。两接口共享 session_id 会话记忆及 54k 环境配置下的自动上下文压缩；进程内记忆在 Pod 重启后丢失。

```bash
curl -N -G "http://10.2.0.48:30800/query" --data-urlencode 'q=查询 xnet 命名空间下所有 Pod 的日志'
```

```bash
curl -N -G "http://10.2.0.48:30800/query"  --data-urlencode 'q=各节点当前 CPU 和内存使用率是多少？'
```



## 核心文档

| 文档 | 内容 |
|---|---|
| [核心流程与模块架构](docs/ARCHITECTURE.md) | 从用户输入到修复与恢复观察的完整生命周期、数据契约、工具结果处理、上下文压缩、边界与已知限制 |
| [HTTP API](docs/api.md) | curl 完成查询、深度诊断、修复、审批与观察的完整流程；A2A 与 API 身份待办 |
| [部署与运维](docs/GUIDE.md) | 配置、发布、权限、联邦及常见排查 |
| [运行诊断](docs/run-diagnostics.md) | 每次运行的账本、工程异常分类、`/runs/{run_id}` 报告 |
| [LLM 自身异常记录](docs/llm-model-anomalies.md) | 模型/推理服务自身问题的现象与外部佐证 |
| [高危命令验收](docs/acceptance-blacklist.md) | 黑名单与需人工审批命令的标准验收步骤 |
| [多集群设计](docs/multi-cluster-design.md) | 多集群设计与实现：集群登记、数据与执行路径、隧道、路由范围、诊断、修复、runner 权限等级、预期状态、已知限制 |
| [多集群验收方案](docs/multi-cluster-acceptance.md) | 测试分层、验收脚本（含衔接处契约、事件流与前端回放、误报、意图准确率统计）、逐阶段用例与结果 |
| [修复三个 Sprint](docs/remediation-sprint-design-2026-10.md) | 修复链路需求、设计与验收记录 |
| [可观测性采集](docs/observability.md) | MCP 工具、PromQL 示例、日志与链路、结果含义 |
| [A2A](docs/a2a.md) | 标准协议、客户端、鉴权与真实 Agent-to-Agent 测试 |
| [环境变量](docs/configuration-env.md) | 由 `scripts/list_env_vars.py` 生成 |
| [异常环境](test/pod-anomaly-cases/README.md) | 故障部署、验证和安全清理（`make case-*` / `make repair-cases-*`） |
| [质量测试](test/aiops_quality_e2e/README.md) | 单场景、多根因、四项指标与报告 |

历史过程记录、旧交接文档已从仓库移除，可通过 git 历史（标签 `baseline-20261019-run-3c052423` 之前）回溯。

## 开发

Python 3.12（与镜像一致）。运行时依赖 `requirements.runtime.txt`（HolmesGPT 由 Dockerfile 单独安装），开发工具 `requirements.dev.txt`，A2A 依赖 `requirements.a2a*.txt`（独立虚拟环境 `.venv-a2a`）。

```sh
make check          # 语法 + lint（ruff E9/F/I/B）+ 格式检查 + 单元测试
make test-unit      # 仅单元测试（tests/unit）
make test-a2a       # A2A 测试（需 .venv-a2a）
make release        # 构建并推送镜像后滚动部署
```

目录：`app/` 服务代码，`a2a_adapter/` A2A 适配器，`a2a_test_agent/` A2A 测试 Agent，`deploy/` K8s 清单与配置，`tests/` 自动化回归，`test/` 故障环境与质量评测工具，`scripts/` 运行报告、环境变量文档生成与验收脚本，`tools/` 命令行客户端，`config/examples/` Secret 示例。提示词只从 `app/core/prompts.py` 引入；修改提示词需配套行为测试。

报告和工具归档默认写入 Pod 内的 `/tmp/aiops/reports`（PVC）。源码实现与当前线上版本可能不同，历史测试成绩不能直接代表当前部署效果。

## License

项目自有代码采用 [Apache License 2.0](LICENSE)，允许商业使用。
第三方代码与依赖保留各自的许可证及署名，不由本项目重新授权。
