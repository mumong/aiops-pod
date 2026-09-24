# 部署与运维

[返回 README](../README.md)。本文以仓库中的 Makefile 和部署清单为准，不假设某台机器已配置完成。

## 1. 配套服务

- [可观测性组件](http://10.2.0.86/platform/observability)：部署指标、日志和链路后端，确认目标集群数据已进入。
- [MCP](http://10.2.0.86/wanghuhu/mcpstander)：配置 Kubernetes 和可观测后端访问，再部署工具服务。
- [前端](http://10.2.0.86/wanghuhu/aiops-frount)：可选，指向本 Agent 的 HTTP/SSE 接口。

跨仓库的部署参数以各仓库 README 为准，不要求源码目录必须相邻。Agent 需要可达的 MCP 地址，而不是读取 MCP 源文件。

## 2. Agent 配置

| 文件 | 需要核对 |
|---|---|
| 本地 deploy/secrets/core.yaml | 模型地址、模型名、API Key、实际上下文容量 |
| [deploy/configmap/config.yaml](../deploy/configmap/config.yaml) | MCP SSE 地址、工作流、语言、联邦配置 |
| [deploy/configmap/runbooks.yaml](../deploy/configmap/runbooks.yaml) | 排障知识及目录，挂载后由 fetch_runbook 读取 |
| [deploy/k8s-simple.yaml](../deploy/k8s-simple.yaml) | 主服务、A2A、initContainer 镜像；PVC、资源、端口 |
| [deploy/rbac.yaml](../deploy/rbac.yaml) | Agent ServiceAccount 权限 |
| [Makefile](../Makefile)、[VERSION](../VERSION) | 镜像仓库与发布版本 |

缺少 Secret 文件时，可复制 [Secret 示例](../config/examples/aiops-secret.yaml) 到
`deploy/secrets/core.yaml`，将占位内容换成真实配置，勿提交。示例刻意放在 `deploy/`
之外，避免递归部署时用占位值覆盖真实 Secret；已有本地配置无需覆盖。结构如下：

~~~yaml
apiVersion: v1
kind: Secret
metadata:
  name: aiops-secret
  namespace: aiops
type: Opaque
stringData:
  LLM_API_KEY: "<API key>"
  LLM_MODEL: "<provider/model>"
  LLM_API_BASE: "<OpenAI-compatible API base>"
  MODEL_CONTEXT_WINDOW: "<实际上下文 token 数>"
  LOG_LEVEL: "INFO"
~~~

A2A 可增加 A2A_API_TOKEN。模型需要支持工具调用；配置中的 llm.extra_body 是模型服务特定参数，不支持 Qwen chat_template_kwargs 的服务应移除或改成对应参数。

当前 MCP 默认使用集群 DNS，例如 http://mcp-server-manager.mcp.svc.cluster.local:8100/sse。外部 MCP 要改为可达地址，并核实查询的是目标集群。单集群关闭 federation.enabled，避免向示例子集群地址发请求。

清单申请 aiops-reports-pvc，容量 20Gi、ReadWriteOnce；需要默认 StorageClass 或匹配 PV。修改仓库前缀时同步核对 Makefile 与清单：版本替换只匹配 Makefile 当前定义的镜像前缀，initContainer 镜像不会跟随主镜像版本更新。

## 3. 发布与验证

~~~bash
kubectl config current-context

# 已有可拉取镜像
make deploy

# 自行构建或升级：更新 VERSION 后顺序执行
make build
make push
make deploy
~~~

make build / push 包含主服务和 A2A 两个镜像；不包含前端、MCP 或测试 Delegator。

make deploy 会更新本地清单中的镜像版本和 A2A_PUBLIC_URL、创建 aiops namespace、递归应用 deploy/ 并等待 rollout。若同 namespace 已有 aiops-copilot-frontend，还会重启该前端以刷新后端 DNS。因此不要把临时 YAML 或旧备份放在 deploy/ 中。

A2A 对外地址默认使用首个 Node InternalIP。可显式指定：

~~~bash
make deploy A2A_PUBLIC_HOST=<可访问的节点IP>
# 或同时指定完整对外 URL
make deploy A2A_PUBLIC_HOST=<节点IP> A2A_PUBLIC_URL=https://<A2A域名>
~~~

~~~bash
kubectl get pods,svc,pvc -n aiops
kubectl port-forward -n aiops svc/aiops-copilot 8000:8000 8001:8001
~~~

另一终端：

~~~bash
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/api/v1/mcp/status
curl -fsS http://127.0.0.1:8000/tools/detail
curl -fsS http://127.0.0.1:8001/.well-known/agent-card.json
~~~

主 API NodePort 为 30800，A2A 为 30801。健康接口可达不代表遥测后端全部正常，还需实际调用三维工具验证；工具结果解读见[可观测性采集](observability.md)。

## 4. 配置更新、日志与卸载

~~~bash
# 配置或 Runbook 修改后，重启使进程重新加载
kubectl apply -f deploy/configmap/ --recursive
kubectl apply -f deploy/secrets/ --recursive
make restart

# 查看主服务日志
kubectl logs -n aiops deployment/aiops-copilot -c aiops-copilot -f
~~~

RBAC 由 Kubernetes API 实时执行，权限变更通常不需要重启 Pod；进程加载的配置、Secret 环境变量和 Runbook 则应按上述步骤更新。

升级不需要先卸载。确需停用服务时，make delete 删除主 Deployment、Service、RBAC、Secret 和 ConfigMap，保留 namespace、PVC/PV；它不是清空报告的命令。删除 namespace 会连带删除其中资源及 PVC，必须另行确认数据备份，不作为常规升级步骤。

## 5. 权限边界

自动修复当前默认为关闭，但这不等于所有已接入工具只读。生产环境需同时约束 MCP 工具暴露、ServiceAccount、后端凭据和 API 入口。

若 MCP 配置通过 exec 进入已有后端 Pod 查询，需给该 MCP 身份对应 namespace 的 pods/exec create 权限；这不是 pods create，不会因此创建新 Pod，但 exec 本身允许执行命令，应限制目标范围。撤销 exec 可能使日志与链路查询失效。具体权限由 MCP 仓库管理，本仓库的 Agent RBAC 不能替代它。

测试 Case 由操作者的 kubectl 身份部署，与诊断 Agent 的权限分开。

## 6. 多集群与 A2A

联邦查询要求各集群的 Agent/MCP 均可独立使用。在主集群配置 federation.sub_agents 的名称和可达 URL，主集群自身可用 http://localhost:8000。

- make deploy-master：修改本地 federation.enabled 为 true 后部署。
- make deploy-slave：修改为 false 后部署。
- /federation/ask/v2、/federation/query/v2：主 Agent 选择子集群。
- 标准 A2A 的发现、JSON-RPC、SSE 和鉴权见 [A2A 指南](a2a-server.md)，不要与联邦 HTTP 接口混用。

## 7. 排查入口

| 现象 | 优先检查 |
|---|---|
| Pod Pending | PVC/StorageClass、资源和调度事件 |
| 工具缺失或连接失败 | MCP enabled、地址、端口、网络及服务版本 |
| 指标 empty | exporter 抓取、指标名、标签、时间窗 |
| 日志/链路 error | 后端连接、凭据、exec 权限、索引与 selector |
| 日志/链路 empty | 容器是否启动、流量、采集延迟、查询条件及埋点 |
| 报告与现场冲突 | run_id、Pod UID、时间窗、原始归档；不能用旧报告替代当前观测 |

报告路径、组 ID 和 Langfuse 定位见[核心实现](current-aiops-diagnosis-architecture.md#归档与运行排查)。
