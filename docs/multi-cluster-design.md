# 多集群与可观测后端适配设计

状态：设计稿（2026-10-21），尚未实现。
适用代码：robusta 12.0.69、mcpstander 7.0.52、frontend 0.1.71。

## 1. 目标与边界

### 1.1 目标

1. **多集群下使用新的可观测数据**：VictoriaMetrics K8s Stack 的中心/边缘部署（cloud-observability），数据集中在中心，按 `cluster` 标签区分。
2. **兼容现有可观测组件**：Prometheus + Elasticsearch/Filebeat + DeepFlow + Tempo 继续可用，以后可以切回来，或者两种并存（不同集群用不同后端）。
3. **使用方式基本不变**：仍然是"快速查询"和"深度诊断"（以及在其后发起的修复）两条主线。AIOps 的工作流基本不动，**主要改动在 MCP 的适配层**。

### 1.2 硬边界

| 边界 | 含义 |
|---|---|
| **不修改 xnet-cloud，也不要求它做任何适配** | 不改代码、不改它的配置和数据（包括虚拟 Node 的注解），**不在 xnet 命名空间创建任何对象，不通过 Vessel 下发我们的组件**。新增的一切都属于 AIOps 自己的服务，只以只读或调用方的身份使用 xnet 已有的能力（隧道 `/proxy`、客户端证书、虚拟 Node 列表） |
| **不修改可观测组件的采集逻辑** | 不改 vmagent/vlagent/Filebeat 等的采集配置；某个集群没有的数据，就如实返回"未提供"，不补造 |
| **单集群行为不变** | 不配置多集群时，现有部署（10.2.0.48）的行为、提示词和接口完全不变，现有验收全部通过 |
| **安全由我们自己保证** | 不依赖 xnet 修复它自身的问题（JWT 密钥硬编码、隧道可以访问任意地址、Agent 拥有集群全部权限） |
| **只在容器内执行** | 和单集群一样，不提供宿主机级别的操作 |

### 1.3 不做的事

- 不做跨集群的应用迁移、调度或编排（这是 xnet 的职责）。
- 不做交互式终端（`exec -it`）、`logs -f`、`--watch` 这类长连接操作。
- 第一期不支持在边缘集群执行 helm 操作（见 §5.4）。

## 2. 现状

### 2.1 测试环境（2026-10-21 实测）

| 主机 | 角色 | 组件 |
|---|---|---|
| 10.2.5.85 | 中心 | VictoriaMetrics 全套（vmcluster、vlsingle、vmalert、Grafana）、xnet-management |
| 10.2.5.88 / 10.2.5.89 | 边缘 | vmagent、vlagent（推送到中心）、xnet-agent |

- 每个边缘集群在中心表现为一个 xnet 虚拟 Node：`vc-942nkkozc8o5fyb9q3bznb1ws`、`vc-dluw0jousipr6h5co2bwpyqk2`；中心自身为 `vc-xnet-management`。
- **可观测数据的 `cluster` 标签值等于虚拟 Node 名**；边缘还带有 `cluster_id`（即 xnet 集群 UUID）。
- 中心查询入口：指标 `http://10.2.5.85:31500/select/0/prometheus`（集群内为 `vmselect-vm-victoria-metrics-k8s-stack.monitor:8481`），日志 `http://10.2.5.85:31700/select/logsql/*`（集群内为 `vlsingle-vm-victoria-metrics-k8s-stack.monitor:9428`）。

### 2.2 两种可观测后端的能力对比

| 维度 | 旧后端（legacy，当前 10.2.0.48） | 新后端（victoria，三集群环境） |
|---|---|---|
| 指标 | Prometheus，单集群，没有 `cluster` 标签 | VictoriaMetrics，多集群，`cluster` 标签；另有 kepler 能耗指标 |
| 日志 | Elasticsearch/Filebeat，**容器日志** | VictoriaLogs，**只有 K8s 事件**（event-exporter），没有容器日志 |
| 链路 | DeepFlow L7 流量 + Tempo span | 无 |
| 拓扑 | 来自 K8s 实时对象（与后端无关） | 同左 |

新后端的事件是一段非结构化文本，放在 `_msg` 里：

```
event name: ..., count: 412, involvedObject_namespace: xnet, involvedObject_kind: Pod,
involvedObject_name: xnet-management-..., reasoni: Unhealthy, type: Warning, message: Readiness probe failed ...
```

注意：`level` 字段恒为 `INFO`，真实类型在文本里的 `type:`；字段名有拼写错误 `reasoni`；`kubernetes.pod_name` 是 event-exporter 自己的 Pod，**不是事件涉及的对象**。

已知噪声（采集配置导致，不是故障）：三个集群的 kube-controller-manager、kube-scheduler、etcd 均为 `up==0`（kubeadm 默认绑定在 127.0.0.1）；中心采集 3 个虚拟 Node 的 kubelet 失败。

### 2.3 现有代码中与集群相关的位置

| 位置 | 现在怎么做 | 多集群下的问题 |
|---|---|---|
| mcpstander `aiops-observability-query`（`execute_pod_promql`、`query_pod_logs`、`query_pod_tracing`、`query_pod_topology`） | 后端地址来自环境变量（`servers/aiops_observability/config.py`），固定为旧后端 | 只能连一套后端，也不认识集群 |
| mcpstander `prometheus_tool`（`holmes_tools/prometheus.py`） | 只有一个 `PROMETHEUS_URL` | 同上 |
| mcpstander `k8s-core`、`bash_tool`、`helmcharts` | 在 MCP Pod 里起 `kubectl`/`helm` 子进程，使用集群内 SA（`holmes_tools/_command_runner.py`） | 只能访问中心集群 |
| robusta 修复执行器、恢复观察、Pod 身份补全（`remediation/pod_executor.py:run_argv`、`remediation/recovery.py`、`workflow/pod_identity.py`） | 在 AIOps Pod 里起 `kubectl` 子进程 | 只能操作中心集群 |
| robusta 路由（`workflow/nodes/request_router.py`） | 范围只有 `scope / namespaces / pod_names` | 没有集群维度 |
| robusta MCP 工具包装（`aicall/tools.py:_wrap_mcp_tool_for_transport`） | 只清洗参数 | 可以作为注入集群参数的统一位置 |

### 2.4 xnet 能力实测

| 能力 | 结果 |
|---|---|
| 中心使用 xnet 自带的客户端证书（Secret `xnet/xnet-client-cert`，CA 为 `xnet/xnet-ca-cert`）调用隧道 `https://<中心>:30909/proxy?clientid=<UUID>&address=<边缘内地址>` | ✅ 200，约 20ms |
| 通过隧道访问边缘集群里**任意 Service**（两个边缘的 kube-state-metrics，约 260KB） | ✅ 200，约 20ms |
| 不带客户端证书 | ❌ TLS 握手失败（服务端为 `RequireAndVerifyClientCert`） |
| 请求头和请求体是否透传 | ✅ 隧道把完整的 HTTP 请求序列化后转发（swarm-tunnel `httpRequestToWebSocketRequest` 使用 `r.Write`） |
| 隧道的 `exec`、`logs` 协议 | ❌ 只定义了名称，没有实现（`downstream/type.go` 只处理 ws 和 ssh） |
| 虚拟 Node 的 exec、port-forward、stats | ❌ 打一行日志后直接返回成功，**不能使用** |
| 每个 http 请求的超时 | 固定 20 秒（`HttpRequestTimeout`），响应整包缓冲 |
| 集群 UUID 与虚拟 Node 名的对应 | Node 名 = `vc-` + UUID 的 base36 编码，可以反解；Node 上也有 UUID 注解 |

## 3. 总体架构

```
┌──────────────────────────── 中心集群 ────────────────────────────┐
│ 前端 ──▶ AIOps 后端（工作流基本不变）                              │
│            │ 路由识别 clusters；工具调用自动带上 cluster            │
│            ▼                                                     │
│ MCP（mcpstander）                                                │
│   ├─ 集群注册表：xnet 虚拟 Node（只读）+ 我们的配置（别名、后端）   │
│   ├─ 可观测适配层：按集群选择后端                                  │
│   │     legacy  ─▶ Prometheus / Elasticsearch / DeepFlow / Tempo   │
│   │     victoria ─▶ vmselect / vlsingle（带 cluster 过滤）         │
│   └─ 集群访问层（kubectl 垫片）                                    │
│         local ─▶ 本集群 kubectl（现有方式）                        │
│         xnet  ─▶ xnet 隧道 /proxy ──────────────┐                 │
│ xnet-management（不改）   VictoriaMetrics（不改）│                 │
└────────────────────────────────────────────────┼─────────────────┘
                                                 │ 边缘主动建立的 wss 长连接
┌──────────────────────── 边缘集群 ───────────────┴─────────────────┐
│ xnet-agent（不改）：在边缘内部转发 HTTP 请求                        │
│        ▼                                                         │
│ aiops-edge-runner（新增）：校验签名 → 规则检查 → 本地执行 kubectl    │
│ vmagent / vlagent（不改）：数据推送到中心                          │
└──────────────────────────────────────────────────────────────────┘
```

两条原则：

- **数据走中心，操作走隧道。** 指标和事件已经在中心，直接查询，不经过边缘；只有 K8s 实时查询、Pod 内执行和修复动作才经过隧道。
- **后端差异和集群差异都收在 MCP 里。** AIOps 看到的仍然是同样的工具名、同样的参数和同样的结果格式，只是多了一个可选的 `cluster` 参数。

## 4. 核心概念

### 4.1 集群注册表（MCP）

每个集群一条记录：

| 字段 | 来源 | 说明 |
|---|---|---|
| `name` | xnet 虚拟 Node 名，或配置中的静态名称 | 唯一标识，也是可观测数据的 `cluster` 标签值 |
| `aliases` | **我们自己的配置** | 例如 `edge-88`。不写入 xnet |
| `uuid` | Node 名反解，或 Node 注解 | 调用隧道时的 `clientid` |
| `access` | 配置 | `local`（本集群）或 `xnet`（经隧道） |
| `observability` | 配置 | 使用哪个后端档案，例如 `legacy` 或 `victoria` |
| `online` | xnet 虚拟 Node 是否 Ready + runner 健康检查 | 每 30 秒刷新一次 |
| `capabilities` | 后端档案 + runner 健康检查的结果 | metrics / logs / events / traces / flows / k8s / exec |

发现方式：
- `static`：只用配置里的集群列表（现有单集群环境，只有一个 `local`）。
- `xnet_nodes`：读取中心集群里带 `node-role.kubernetes.io/xnet-agent` 标签的 Node，再与配置合并。**只读**，集群的接入和下线以 xnet 为准。

### 4.2 可观测后端档案（observability profile）

同一套工具，根据集群选择不同的后端实现：

| 工具 | legacy | victoria |
|---|---|---|
| `execute_pod_promql` | Prometheus（现有实现） | VictoriaMetrics，查询时附加 `extra_label=cluster=<name>`。VM 会把这个条件强制加到所有选择器上，**不需要改写 PromQL**，模型也无法查到别的集群 |
| `prometheus_tool` 的 6 个工具 | 同上 | 同上（标签、序列、元数据接口都支持 `extra_label`） |
| `query_pod_logs` | Elasticsearch 容器日志（现有实现） | **返回该 Pod 相关的 K8s 事件**：按 `cluster` 和 `_msg` 中的 `involvedObject_name` 过滤，并把文本解析成字段（type、reason、message、count）。结果明确标注 `log_source=k8s_events`、`coverage=partial`，并说明"该集群未采集容器日志，容器日志请使用 kubectl_logs" |
| `query_pod_tracing` | DeepFlow + Tempo（现有实现） | 返回 `capability_missing`："该集群未提供链路数据" |
| `query_pod_topology` | K8s 实时对象 | 同左，经集群访问层查询 |

为什么 `query_pod_logs` 返回事件而不新增工具：MCP 的工具列表是静态的，不能按集群变化；新增工具还要修改 AIOps 的提示词和各节点的工具清单。复用现有工具，并在结果里如实标注数据类型和覆盖范围，AIOps 侧就不需要修改。

结果格式（`facts`、`fact_ledger`、`coverage`、`samples`、`serialization`）保持不变，只在顶层增加 `cluster` 和 `backend` 两个字段。

### 4.3 集群访问层（kubectl 垫片）

现有的 k8s-core 工具用模板拼出 `kubectl ...` 命令，有些还接了 `jq`。为了**不改动这些模板**，在中心的 MCP 和 AIOps 镜像里，用一个垫片替换 PATH 上的 `kubectl`：

```
kubectl <argv>
  ├─ 环境变量 AIOPS_CLUSTER 为空或 local → 执行真正的 kubectl（现在的行为）
  └─ 远端集群 → 签名后经 xnet 隧道 POST 到边缘 runner
                → 原样输出 stdout/stderr，并返回相同的退出码
```

- 管道后面的 `jq`、`grep` 等仍然在中心本地执行，处理的是 runner 返回的输出。
- 垫片拒绝 `-f/--follow`、`-w/--watch`、`-it`、`port-forward`、`proxy`、`attach`，返回明确的错误。
- 每次调用的超时不超过 15 秒（隧道上限为 20 秒）。
- 调用方只需要在起子进程时设置 `AIOPS_CLUSTER`：MCP 的 `_command_runner`，以及 AIOps 的 `run_argv`、恢复观察和 Pod 身份补全。
- 垫片只有一份源码（放在 mcpstander），AIOps 构建镜像时复制进去，用测试保证两份内容一致。

**为什么不直接把 kubeconfig 指向隧道：** 隧道的 http 通道使用 Go 默认客户端，不带集群 CA 和 token，也不支持 exec 需要的连接升级；`/proxy?clientid=…&address=…` 这种格式也不能作为 kubeconfig 的 `server`。

### 4.4 边缘 runner（aiops-edge-runner）

部署在每个边缘集群的 `aiops` 命名空间：1 个 Deployment，1 个副本，ClusterIP Service（端口 8090，不对外暴露），内存约 100MB。

| 接口 | 用途 | 使用的 SA |
|---|---|---|
| `GET /healthz` | 版本、规则版本、能力 | —— |
| `POST /v1/kubectl` | 同步执行一条 kubectl：`{argv, timeout_s, mode}`，返回 `{exit_code, stdout, stderr, truncated, duration_ms}` | `mode=read` 用 reader；`mode=exec` 用 writer |
| `POST /v1/jobs` | 提交异步修复动作：`{idempotency_key, argv, approval_id, timeout_s}`，立即返回 `job_id` | writer |
| `GET /v1/jobs/{id}` | 查询任务状态和输出 | —— |

- **认证**：每个请求带 `X-AIOps-Timestamp` 和 `X-AIOps-Signature`（对时间戳和请求体做 HMAC-SHA256，共享密钥来自双方各自的 Secret）。时间偏差超过 60 秒、或签名重复，一律拒绝。这样只拿到 xnet 客户端证书的人**无法调用 runner**。
- **规则**：runner 加载和中心同一份命令规则（随部署清单中的 ConfigMap 下发，`/healthz` 返回规则版本）。黑名单命令一律拒绝；需人工审批的命令必须带有效的 `approval_id`；`mode=read` 只允许只读子命令（get、describe、logs、events、top、api-resources、explain）。
- **权限**：两个 SA。`reader` 为集群范围的 get/list/watch 加 pods/log；`writer` 只有修复需要的最小权限（pods/exec、删除 Pod、patch/update Deployment 等工作负载、scale）。
- **输出截断**：单个响应最多 256KB，`truncated=true` 时注明截断。
- **任务**：按 `idempotency_key` 去重，重复提交返回同一个 `job_id`；任务记录在内存中保留 24 小时，同时写入 emptyDir，runner 容器重启后不丢失（Pod 重建时会丢失，此时中心标记为"结果未知"）。
- **审计**：runner 本地记录每次执行（集群、argv、审批 ID、结果），中心也照常记录。

### 4.5 xnet 隧道客户端（MCP 与 AIOps）

- 证书：**部署时复制，运行时不访问 xnet 命名空间。** 我们的部署命令（`make sync-xnet-cert`，由有权限的运维人员执行）把 `xnet/xnet-client-cert` 和 `xnet/xnet-ca-cert` 的内容复制成 `mcp/aiops-xnet-client-cert`（AIOps 命名空间同样复制一份），以 Secret 卷挂载。MCP 和 AIOps 的 SA **不需要读取 xnet 命名空间的权限**，也不在 xnet 命名空间创建 Role。
  - 实测证书有效期为 2026-10-21 至 2031-10-20，复制方案的维护成本很低。
  - 隧道客户端启动时和每次握手失败时检查证书：已过期或握手被拒，就返回 `tunnel_auth_failed`，提示"xnet 证书失效，请重新执行 make sync-xnet-cert"，不静默重试。
  - 注意：现有 MCP 的 ClusterRole 含 `*/*/*`（§9），技术上能直接读取 xnet 的 Secret。设计**不依赖**这个过大的权限，权限收缩后仍然可用。
- 地址：`https://xnet-management.xnet.svc:9090/proxy?clientid=<UUID>&address=<URL 编码后的 runner 地址>`。参数尽量放在请求体里，避免嵌套查询字符串。
- 错误分类：TLS 握手失败为 `tunnel_auth_failed`；返回 "side client is not online" 为 `cluster_unreachable`；超时为 `timeout`；runner 返回 401/403 为 `runner_auth_failed` 或 `policy_denied`。

## 5. 工具调用如何带上集群

### 5.1 MCP 工具参数

所有可观测工具、k8s-core、`bash_tool` 增加**可选**参数 `cluster`。不传时：单集群部署为 `local`，所以现有调用不受影响；多集群部署下由 AIOps 按路由确定的范围注入（§5.2），范围本身必须由用户说明（§6.1）。

### 5.2 AIOps 注入规则（工程保证，不依赖模型）

在 `aicall/tools.py:_wrap_mcp_tool_for_transport` 这一层统一处理：

| 运行范围 | 处理 |
|---|---|
| 没有集群信息（单集群部署） | 不处理，行为与现在相同 |
| 本次运行只涉及 1 个集群 | **强制注入**这个集群，覆盖模型传入的值 |
| 涉及多个集群 | 模型必须填写，且必须在范围内；否则直接返回错误，不调用工具 |
| 深度诊断的取证通道 | 注入该异常组所属的集群 |

这与现有命名空间范围的处理方式一致：范围由路由确定，工具层负责保证，提示词只起说明作用。

### 5.3 结果中的集群信息

所有工具结果的顶层带上 `cluster`；事实的身份从 `namespace/kind/name` 扩展为 `cluster/namespace/kind/name`。不同集群里同名的 Pod 不会被合并。

### 5.4 各类工具在远端集群上的能力

| 工具 | 远端集群 |
|---|---|
| 可观测工具 | ✅ 由后端档案决定能力 |
| k8s-core（get、describe、logs、events、top、lineage、jq 查询等） | ✅ 经 kubectl 垫片 |
| `bash_tool` 的 `run_bash_command` | 只允许以 `kubectl` 开头、后面接本地文本处理命令（jq、grep、awk、head 等）的命令；其他命令在中心 MCP Pod 里执行，对边缘没有意义，一律拒绝并说明原因 |
| `kubectl_run_image` | ✅ 经垫片（创建临时 Pod） |
| `helmcharts` | ❌ 第一期不支持，返回 `capability_missing`（helm 直接调用 K8s API，不经过 kubectl，垫片覆盖不到） |

## 6. 两条主线在多集群下怎么运行

### 6.1 路由

`request_router` 的范围增加 `clusters: List[str]` 和 `cluster_mode: single | multiple | center | unspecified`。

**单集群部署**（注册表里只有 `local`）：不识别集群，行为与现在完全相同。

**多集群部署：用户必须说清楚操作哪个范围。** 有三种合法的意图：

| 意图 | 示例 | 结果 |
|---|---|---|
| 一个集群 | "edge-88 上有哪些 Pod 异常" | `single`，`clusters=[vc-942nk…]` |
| 多个集群 | "edge-88 和 edge-89""所有边缘集群""所有集群" | `multiple`，展开为对应集群；"所有"只展开在线集群，离线的在回答里说明 |
| 中心集群 | "中心集群的 vmagent 正常吗" | `center`，`clusters=[中心集群]` |

识别和兜底：

1. 路由模型从问题和当前会话的上文中理解意图。上文已经明确过集群时，追问（"那它的日志呢""再看看另一个"）沿用或切换到对应集群，不需要用户重复。
2. 模型给出的集群名或别名，由工程代码按注册表解析成规范名称。**模型不能自造集群名**；解析不到的，不调用任何工具，回复"没有找到集群 xx"，并列出可用集群。
3. **没有不可靠的默认值。** 多集群部署下，如果问题和上文都没有说明范围，路由走现有的 `clarify` 分支（`request_router.py` 已经支持），反问："要查看哪个范围：中心集群、某个边缘集群（edge-88、edge-89），还是全部集群？" 这一条由代码强制执行：模型输出 `unspecified` 或者 `clusters` 为空时，即使选择了其他路由，也一律改为澄清。
4. 用户回答后，下一轮按正常流程执行。
5. 路由卡片上显示本次的集群范围。

### 6.2 快速查询

> "edge-88 上有哪些 Pod 不正常？"

```
路由：clusters=[vc-942nk…]
query_collect（工作流不变）：
  execute_pod_promql / prometheus_tool  → 中心 VictoriaMetrics（extra_label 限定集群）
  需要实时信息时 → k8s-core → 垫片 → 隧道 → runner
回答
```

在 Pod 内执行命令（`在 edge-88 的 default/xx Pod 里执行 ls /tmp`）：仍然走现有的操作路径（`operate_tools.guard_write_tool` 先做规则检查），垫片把 `kubectl exec` 发给 runner，runner 再检查一遍规则后执行。需人工审批的命令和现在一样：对话中不执行，提示通过修复方案提交。

跨多个集群的快速查询（"各集群分别有几个 Pod"）：仍然是一个 Agent 循环，模型对每个集群分别调用工具，并填写 `cluster`；工具层校验它在范围内。

### 6.3 深度诊断

**第一期：每次诊断只针对一个集群。** 集群由路由强制注入，layer → evidence → rca → conclusion 全部不变，只是所有工具调用都落在这个集群上。

**第二期：一次诊断涉及多个集群。**

```
layer：每个集群各跑一次（复用现有 layer 节点，按集群并行），得到各自的异常组
  → 合并异常组，组的 key 从 (namespace, workload) 扩展为 (cluster, namespace, workload)
parallel_evidence：所有异常组放进同一个并发池（现有逻辑），每组注入自己的集群
rca → conclusion：按集群分段
```

并发控制：全局沿用 `max_workers`；集群访问层对每个集群另设并发上限（默认 4 个同时在途的隧道请求）和超时，单个集群慢或离线只影响它自己那一段，报告中标注"该集群不可达，结果不完整"。

### 6.4 修复

方案的 `targets` 增加 `cluster` 字段，审批卡片显示"将在 <集群> 执行"，审计记录带集群。

| 步骤 | 本地集群 | 远端集群 |
|---|---|---|
| 规则检查、审批 | 现有逻辑 | 相同 |
| 执行 | `run_argv` 本地执行 | 执行前确认集群在线 → `POST /v1/jobs`（幂等键 = 修复任务 ID + 动作序号）→ 轮询 `GET /v1/jobs/{id}` |
| 恢复观察 | `kubectl get` 轮询 | 优先用中心指标（Pod 是否 Ready、重启次数），再经垫片确认 |

**断线处理：**
- 执行中隧道断开：边缘任务继续执行，中心重连后按 `job_id` 继续查询。
- 超过时限仍查不到结果：标记为"结果未知，需人工确认"，**绝不重新提交**。
- 审批等待期间集群离线：卡片显示"集群当前不可达"，批准后也要等到恢复才执行。

## 7. 生命周期

### 7.1 集群

```
接入：xnet join（xnet 现有流程，与我们无关）
  → 边缘运维人员在边缘集群上执行我们的部署命令：make edge-deploy（见下）
  → 在 MCP 配置中声明该集群的访问方式、后端档案和别名
  → 注册表发现 Node，探测 runner 的 /healthz 和能力 → 可用
在线 / 离线：Node Ready + runner 健康检查
升级：重新执行 make edge-deploy；中心检查 runner 接口版本和规则版本是否兼容，不兼容就把该集群标为只读
下线：xnet 删除 Node → 注册表移除；卸载 runner
```

**runner 的部署方式**：和现有的 AIOps、MCP 一样，用我们自己的部署清单（YAML）加 Makefile，**不需要 chart 仓库，也不经过 xnet**。

- 部署命令在边缘集群本地执行（使用边缘的 kubeconfig），不需要中心能访问边缘，所以符合"中心连不进边缘"的场景。测试环境中通过 SSH 或本机保存的 kubeconfig 执行；这些只用于运维和测试，**运行时不依赖**（spec FR-016）。
- 边缘只需要能从镜像仓库拉取 runner 镜像。实测 .88 和 .89 都能访问 `10.2.0.86:8443`，并且已经配置了 `xnet.registry.io:8443`。
- 签名密钥：边缘部署时创建 `aiops/aiops-edge-runner-key`，中心保存同一份密钥（`mcp/aiops-edge-runner-key`）。
- 命令规则随部署清单下发（ConfigMap），与中心的规则版本一致。

之前考虑过用 xnet Vessel 下发，但 Vessel 的 helm 类型要求提供 chart 仓库地址，而且相当于让 xnet 参与我们的部署，已放弃。

### 7.2 一次运行

每个集群单独记录结果：完成 / 部分完成 / 不可达，以及原因，并写入运行报告（`run_report`）。

### 7.3 修复任务

生成方案 → 等待审批 → 执行中（远端时带 `job_id`）→ 验证中 → 完成 / 结果未知。状态流转与现在相同，只多了 `job_id` 和"结果未知"状态。

## 8. 配置示例（MCP）

```yaml
clusters:
  default: local                 # 单集群部署：不提到集群时使用 local
  discovery: static              # static | xnet_nodes
  items:
    - name: local
      access: local
      observability: legacy
```

三集群环境：

```yaml
clusters:
  default: null                  # 多集群部署不设默认值，没说明范围就澄清（§6.1）
  center: vc-xnet-management     # "中心集群"指的是哪一个
  discovery: xnet_nodes
  items:
    - name: vc-xnet-management
      aliases: [center]
      access: local
      observability: victoria
    - name: vc-942nkkozc8o5fyb9q3bznb1ws
      aliases: [edge-88]
      access: xnet
      observability: victoria
    - name: vc-dluw0jousipr6h5co2bwpyqk2
      aliases: [edge-89]
      access: xnet
      observability: victoria
  access:
    xnet:
      proxy_url: https://xnet-management.xnet.svc:9090/proxy
      client_cert_secret: mcp/aiops-xnet-client-cert   # 由 make sync-xnet-cert 从 xnet 复制
      ca_secret: mcp/aiops-xnet-ca-cert
      runner_url: http://aiops-edge-runner.aiops.svc:8090
      runner_key_secret: mcp/aiops-edge-runner-key
      per_cluster_concurrency: 4
      call_timeout_seconds: 15

observability_profiles:
  legacy:                        # 现有环境变量的值迁移到这里；未配置时继续读环境变量
    metrics: {type: prometheus, url: "${PROMETHEUS_URL}"}
    logs:    {type: elasticsearch, mode: kubectl_exec}
    traces:  {type: deepflow_tempo, mode: kubectl_exec}
  victoria:
    metrics: {type: victoriametrics, url: http://vmselect-vm-victoria-metrics-k8s-stack.monitor:8481/select/0/prometheus, cluster_label: cluster}
    logs:    {type: victorialogs_events, url: http://vlsingle-vm-victoria-metrics-k8s-stack.monitor:9428, cluster_field: cluster}
    traces:  {type: none}
```

**兼容规则：** 没有 `clusters` 配置时，等同于上面的单集群示例；`legacy` 档案没有配置时，仍然读取现有的环境变量（`PROMETHEUS_URL`、`AIOPS_ES_*` 等）。所以现有部署不需要修改任何配置。

## 9. 安全

| 威胁 | 措施 |
|---|---|
| 持有 xnet 客户端证书的人可以访问边缘任意 Service | runner 要求 HMAC 签名，只有证书没有签名密钥就无法调用 |
| 中心被绕过，直接调用 runner | runner 本地执行同一套规则；需人工审批的命令必须带有效的审批 ID |
| runner 被滥用 | reader / writer 两个最小权限 SA；只读接口不能使用 writer |
| 证书泄露范围 | 证书复制到我们的命名空间，只挂载给 MCP 和 AIOps；我们的 SA 不需要读取 xnet 命名空间 |
| 跨集群混用数据 | 工具层强制注入集群，VictoriaMetrics 用 `extra_label` 限定 |
| xnet 自身的问题 | **我们无法解决**：xnet-agent 拥有边缘集群的全部权限，JWT 密钥硬编码。我们只能保证"经过我们系统的操作是受控的" |

现有 MCP 的 ClusterRole 含 `*/*/*`（`mcpstander/deploy/rbac.yaml`），这是单集群下已有的风险，与本设计无关，但建议一并收缩。

## 10. 改动清单

### 10.1 mcpstander（主要改动）

| 模块 | 改动 |
|---|---|
| 新增 `servers/cluster/registry.py` | 集群注册表：静态配置 + xnet Node 发现、别名解析、在线状态、能力 |
| 新增 `servers/cluster/xnet_tunnel.py` | 隧道客户端：证书加载与热更新、签名、错误分类、每个集群的并发与超时控制 |
| 新增 `bin/kubectl` 垫片 | 见 §4.3 |
| `aiops_observability/config.py` | 从后端档案读取配置；没有档案时回退到环境变量 |
| 新增 `aiops_observability/collectors/victoriametrics.py` | PromQL 查询，附加 `extra_label` |
| 新增 `aiops_observability/collectors/victorialogs_events.py` | LogsQL 查询，解析事件文本 |
| `query/metrics.py`、`query/logs.py`、`query/tracing.py`、`query/topology.py` | 按集群选择后端；结果增加 `cluster`、`backend`；不支持的能力返回 `capability_missing` |
| `holmes_tools/prometheus.py` | 按集群选择地址，附加 `extra_label` |
| `holmes_tools/_command_runner.py` | 子进程环境变量带上 `AIOPS_CLUSTER` |
| 各工具 schema | 增加可选的 `cluster` 参数 |
| 新增工具 `list_clusters` | 返回集群名、别名、在线状态和能力，供"我有哪些集群"类问题使用 |

### 10.2 新组件 aiops-edge-runner

放在 mcpstander 仓库中（复用 `_command_runner` 和规则代码），以单独的镜像和部署清单（YAML + Makefile）发布。

### 10.3 robusta（少量改动）

| 模块 | 改动 |
|---|---|
| `workflow/nodes/request_router.py` 与路由提示词 | 范围增加 `clusters`、`cluster_mode`；集群名由代码按注册表解析；多集群部署下范围不明确时强制走 `clarify`（§6.1） |
| `aicall/tools.py:_wrap_mcp_tool_for_transport` | 按 §5.2 注入或校验 `cluster` |
| `workflow/pod_identity.py`、分组与事实身份 | 身份中加入集群 |
| `remediation/plans.py`、`pod_executor.py`、`recovery.py`、`audit.py` | 目标带集群；远端集群使用 runner 异步任务；审计带集群 |
| 第二期：layer 按集群并行 | 见 §6.3 |

### 10.4 frontend（少量改动）

路由卡片、异常组标题、审批卡片和修复结果中显示集群。

## 11. 实施阶段

| 阶段 | 内容 | 验收 |
|---|---|---|
| P0 打通链路 | `make sync-xnet-cert`、隧道客户端、垫片、runner 只读接口、`make edge-deploy`；在 .88 部署 runner | 中心执行 `AIOPS_CLUSTER=vc-942nk… kubectl get pods -A` 能返回边缘结果；不带签名调用 runner 被拒 |
| P1 可观测适配 | 后端档案、VictoriaMetrics/VictoriaLogs 采集器、集群注册表、`cluster` 参数、`list_clusters` | 见 §12 的 A1–A5；**10.2.0.48 上现有验收全部通过** |
| P2 AIOps 单集群范围 | 路由识别集群、工具层注入、身份带集群 | 见 A6–A8 |
| P3 远端执行与修复 | runner 的 exec 与异步任务、修复执行器路由、审批卡片显示集群 | 见 A9–A12 |
| P4 一次诊断涉及多个集群 | layer 按集群并行、按集群分段输出 | 见 A13 |

每个阶段完成后都发版，并在两套环境上验证。验收脚本、分支与版本规划、测试环境操作规范见 [多集群验收方案](multi-cluster-acceptance.md)。

## 12. 验收用例

### 可观测适配

| # | 操作 | 预期 |
|---|---|---|
| A1 | 问"edge-88 上 default 命名空间 xx Pod 的内存使用" | 只返回 edge-88 的数据；结果带 `cluster` 和 `backend=victoria` |
| A2 | 模型传入的 PromQL 不带集群条件 | 仍然只返回该集群的数据（`extra_label` 生效） |
| A3 | 在 victoria 集群上查询 Pod 日志 | 返回该 Pod 的 K8s 事件，标明 `log_source=k8s_events`，并说明没有容器日志；Warning 事件被正确识别 |
| A4 | 在 victoria 集群上查询链路 | `capability_missing`，报告中不出现编造的链路结论 |
| A5 | 在 10.2.0.48 上运行现有全部验收 | 结果与改动前一致 |

### 集群范围

| # | 操作 | 预期 |
|---|---|---|
| A6 | 两个边缘部署同名 Pod，只问 edge-88 | 结果中没有 edge-89 的对象 |
| A7 | 问一个不存在的集群 | 回复找不到，并列出可用集群，不调用任何工具 |
| A8 | 问"我有哪些集群" | 列出三个集群、别名和在线状态 |
| A8a | 多集群部署下问"有哪些 Pod 异常"（没说集群） | 反问要查看中心集群、某个边缘集群还是全部集群；不调用任何工具 |
| A8b | 接着回答"edge-89"，再追问"那它的事件呢" | 第一轮只查 edge-89；追问沿用 edge-89，不再反问 |
| A8c | 分别问"中心集群……""edge-88 和 edge-89……""所有集群……" | 范围分别为 `center`、`multiple`（两个）、`multiple`（全部在线集群），路由卡片显示一致 |

### 远端执行与修复

| # | 操作 | 预期 |
|---|---|---|
| A9 | 在 edge-88 的 Pod 内执行 `ls /tmp` | 正常返回 |
| A10 | 在 edge-88 的 Pod 内执行 `rm` 和 `reboot` | 与单集群的黑名单验收结果一致（见 [acceptance-blacklist.md](acceptance-blacklist.md)）；不经过中心、直接调用 runner 也被拒绝 |
| A11 | edge-88 上的故障 case 生成修复方案并批准 | 审批卡片显示集群；runner 执行；恢复观察判定恢复 |
| A12 | 修复执行中隧道断开或 runner 被删除（集成测试用假隧道；真实环境只操作 runner，不加防火墙） | 能恢复时取回结果、不重复执行；无法确认时标记"结果未知" |
| A13 | "检查 edge-88 和 edge-89"，两边各有一个故障 case | 两个集群的异常组并发取证，报告按集群分段 |

### 网络与 xnet 契约

| # | 操作 | 预期 |
|---|---|---|
| A14 | 运行时依赖检查（不加防火墙） | 中心的运行时配置中没有边缘 kubeconfig 和边缘 API Server 地址；远端访问只经过隧道客户端 |
| A15 | 契约测试脚本（每次 xnet 升级后执行） | `/proxy` 可用；Node 名能反解出 UUID；`cluster` 标签与 Node 名一致；不带证书被拒 |

## 13. 风险

| 风险 | 应对 |
|---|---|
| xnet 升级后行为改变 | 固定使用验证过的版本；A15 契约测试 |
| xnet 主副本切换，所有边缘断开约 10 秒 | 快速失败，标记"暂时不可达"；只读调用重试一次 |
| 隧道 20 秒超时、整包缓冲 | 同步调用不超过 15 秒；修复使用异步任务；runner 截断输出 |
| 新后端没有容器日志，诊断质量下降 | 如实标注数据缺失，引导使用 `kubectl_logs`（经 runner 实时获取） |
| 新旧后端的指标名或标签有差异 | P1 编写对照测试，检查常用指标（kube-state-metrics、cadvisor）在两套后端上都存在 |
| 已知采集噪声（控制面组件 down、虚拟 Node 采集失败）引起误报 | 不改采集配置；在 runbook 中说明这类现象的识别方法 |
| 集群名过长、不便输入 | 使用我们自己配置的别名 |
| 中心资源（12 核 / 15G）同时承载可观测全套组件和 AIOps | 部署前确认余量；必要时把故障 case 放在边缘 |

## 14. 已确认的决策（2026-10-21）

| 事项 | 决定 |
|---|---|
| xnet 的参与程度 | 所有新增内容都属于 AIOps 自己的服务，不要求 xnet 做任何适配；不在 xnet 命名空间创建对象，不使用 Vessel |
| 证书获取 | 部署时复制（§4.5），不需要 Role |
| runner 部署 | 我们自己的部署清单加 Makefile，在边缘本地执行，不需要 chart 仓库（§7.1） |
| LLM 网关 | 10.2.5.x 可以访问 |
| 没有说明集群时 | 多集群部署下必须澄清：中心集群、一个集群，还是多个集群（§6.1） |
