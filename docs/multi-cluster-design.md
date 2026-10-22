# 多集群设计与实现

本文是多集群功能的**当前**设计与实现说明，内容以代码为准。

- **当前版本**：AIOps 13.0.18、MCP 8.0.5、edge runner 1.0.2、前端 0.2.4。代码在三个仓库的 `008-multi-cluster` 分支，**尚未合并**到主线。
- **单集群环境**：现有单集群部署（10.2.0.48，AIOps 12.0.69 / MCP 7.0.52）不挂载集群配置，行为与改造前完全相同。
- **相关文档**：
  - 开发前的设计稿：`git show 0b03f423:docs/multi-cluster-design.md`；
  - 开发过程记录：[specs/008-multi-cluster](../specs/008-multi-cluster/spec.md)；
  - 验收方法与结果：[多集群验收方案](multi-cluster-acceptance.md)。

## 1. 目标与边界

**目标**

1. 多集群下使用新的可观测数据：VictoriaMetrics K8s Stack 的中心 / 边缘部署，数据集中在中心，按 `cluster` 标签区分。
2. 兼容现有可观测组件：Prometheus + Elasticsearch + DeepFlow + Tempo 继续可用，不同集群可以用不同后端。
3. 使用方式基本不变：仍然是"快速查询"和"深度诊断"两条主线，以及诊断之后发起的修复。改动主要在 MCP 适配层。

**硬边界**

| 边界 | 含义 |
|---|---|
| 不修改 xnet-cloud，也不要求它做任何适配 | 不改它的代码、配置和数据，不在 xnet 命名空间创建对象，不使用 Vessel。只以调用方身份使用它已有的能力：隧道 `/proxy`、客户端证书、虚拟 Node |
| 不修改可观测组件的采集逻辑 | 某个集群没有的数据，如实返回"未提供" |
| 单集群行为不变 | 没有集群配置时，路由 schema、提示词、工具 schema、工具结果和 kubectl 调用与改造前一致 |
| 运行时不依赖边缘 kubeconfig | 中心到边缘只经过 xnet 隧道和我们的 runner（验收 X3 检查） |
| 只在容器内执行 | 与单集群相同，不提供宿主机级别的操作 |

**不做的事**：跨集群迁移和调度（xnet 的职责）；交互式终端、`logs -f`、`--watch` 这类长连接操作；在边缘集群执行 helm。

## 2. 总体架构

```
中心集群                                                      边缘集群
┌──────────────────────────────────────────┐              ┌──────────────────────────────────┐
│ 前端                                       │              │ xnet-agent（xnet 的，不改）         │
│ AIOps 后端：路由 / 诊断 / 修复执行器         │              │   主动外连中心隧道（wss）            │
│ MCP：可观测工具 → 中心 vmselect / vlsingle  │   xnet 隧道   │        │ 把中心的 HTTP 请求转成     │
│      K8s 工具 → kubectl 垫片               │◀────────────▶│        ▼ 边缘集群内的 HTTP 调用     │
│ 两者都挂载：集群配置、xnet 证书副本、签名密钥 │  （边缘外连）  │ aiops-edge-runner（我们的）         │
│ xnet-management（不改）                    │              │   校验签名 → 规则检查 → kubectl     │
│ VictoriaMetrics / VictoriaLogs（不改）     │              │ vmagent / vlagent（不改，推到中心） │
└──────────────────────────────────────────┘              └──────────────────────────────────┘
```

两条原则：

- **数据走中心，操作走隧道。** 指标和事件已经在中心，直接查询；只有 K8s 实时查询、Pod 内执行和修复动作经过隧道。
- **后端差异和集群差异收在 MCP 里。** AIOps 看到的仍是同样的工具名、参数和结果格式，只多一个可选的 `cluster` 参数。

共享代码 `aiops_edge/` 只依赖标准库。robusta 是唯一源，mcpstander 同步一份（不含 `runner/`），一致性由 mcpstander 的 `test_aiops_edge_sync` 保证。

| 模块 | 作用 |
|---|---|
| `clusters.py` | 读取集群配置；别名解析；集群名 ↔ xnet UUID 换算 |
| `tunnel.py` | 调用 xnet `/proxy`：mTLS、签名、超时、错误分类、每集群并发上限 |
| `signing.py` | 中心与 runner 之间的 HMAC 签名与防重放 |
| `shim.py`、`kubectl` | kubectl 垫片：本集群直接执行，远端集群转发给 runner |
| `kubectl_args.py` | 哪些 kubectl 能远端执行，属于 read / exec / write 哪种模式 |
| `streams.py` | 输出的 gzip+base64 编码 |
| `jobs_client.py` | 修复用的异步任务客户端：提交、轮询、结果未知判定 |
| `runner/` | 边缘 runner：HTTP 服务、命令闸门（复用中心的 `policy.py`）、任务存储 |

## 3. 集群登记与配置

### 3.1 配置文件

集群登记是**静态配置**：`deploy-edge/clusters.mc.yaml` 以 ConfigMap `aiops-clusters` 挂载到 MCP 和 AIOps，路径由环境变量 `AIOPS_CLUSTERS_CONFIG` 指定。没有这个文件时就是单集群模式。

```yaml
clusters:
  default: null                    # 多集群不设默认集群：没说范围就反问
  center: vc-xnet-management       # "中心集群"指谁；其余集群都是边缘集群
  items:
    - name: vc-942nkkozc8o5fyb9q3bznb1ws   # = xnet 虚拟 Node 名 = 可观测数据的 cluster 标签
      aliases: [edge-88]                    # 我们自己维护的别名，不写入 xnet
      access: xnet                          # local = 本集群直连；xnet = 经隧道
      observability: victoria               # 使用哪套可观测后端（见 observability_profiles）
  access:
    xnet:
      proxy_url: https://xnet-management.xnet.svc:9090/proxy
      runner_url: http://aiops-edge-runner.aiops.svc:8090
      cert_file / key_file / ca_file: /etc/aiops-xnet/…     # make sync-xnet-cert 复制来的证书
      signing_key_file: /etc/aiops-edge-key/key
      per_cluster_concurrency: 4
      call_timeout_seconds: 15

observability_profiles:
  victoria:
    metrics: {type: victoriametrics, url: …vmselect…, cluster_label: cluster}
    logs:    {type: victorialogs_events, url: …vlsingle…, cluster_field: cluster}
    traces:  {type: none}

expected_states: [...]             # 运维声明的预期状态，见 §11
```

- 集群名直接使用 xnet 虚拟 Node 名，因为它同时是可观测数据里的 `cluster` 标签。隧道需要的 UUID 由 Node 名反解（`vc-` + UUID 的 base36），不需要额外配置。
- 集群角色：`center` 是中心集群，其余都是边缘集群（子集群）。路由提示词按这个角色列出集群（§7）。
- 没有配置 `legacy` 档案时，MCP 仍读取原有的环境变量（`PROMETHEUS_URL`、`AIOPS_ES_*` 等），所以现有部署不用改配置。
- **没有实现自动发现**：开发前的设计稿里有"读取 xnet 虚拟 Node 自动登记"（`discovery: xnet_nodes`），实际没有做。新增集群需要在配置里加一条，然后重新部署；xnet 虚拟 Node 只用来判断集群是否在线。

### 3.2 接入一个边缘集群

以下全部是我们自己的部署动作，不需要 xnet 做任何事：

| 步骤 | 命令 | 作用 |
|---|---|---|
| 1 | （xnet 侧完成 join） | 边缘的 xnet-agent 已经外连中心隧道 |
| 2 | `make mc-keygen` | 生成中心与 runner 共用的签名密钥（只保存在本机运维目录） |
| 3 | `make edge-deploy EDGE_KUBECONFIG=…` | 在边缘本地部署 runner：两个 SA 与 RBAC、命令规则 ConfigMap（从中心 `config.yaml` 的 `workflow.remediation` 渲染）、签名密钥 Secret、Deployment 和 ClusterIP Service |
| 4 | `make sync-xnet-cert` | 中心：把 xnet 的隧道客户端证书复制到 `mcp`、`aiops` 命名空间，并下发签名密钥 |
| 5 | 编辑 `clusters.mc.yaml`，在 MCP 和 AIOps 各执行一次 `make deploy-mc` | 更新集群配置 |

边缘 kubeconfig 只用于部署和测试，运行时不使用。测试环境的 Harbor 推不了镜像，所以由 `deploy-edge/load_image.sh` 经 SSH 把镜像导入节点，部署清单使用 `IfNotPresent`。

### 3.3 在线状态

MCP 工具 `list_clusters`（`servers/cluster_scope.py`）只返回运维关心的信息：名称、别名、角色（center / edge）、是否在线、有哪些数据（指标、日志是容器日志还是只有 K8s 事件、链路）。访问方式、后端配置名、exec/helm 等实现细节不给模型，也就不会出现在回答里（MCP 8.0.6，Boss：不展示 xnet 隧道这类非运维内容）。

- **在线判定**：xnet 虚拟 Node 为 Ready，且经隧道请求 runner 的 `/healthz` 成功；结果缓存 30 秒。不在线时返回 `reason`。

## 4. 可观测后端

一次工具调用带着 `cluster` 参数进入 MCP。MCP 入口用 `cluster_scope.activate()` 设置当前集群，再按该集群的后端档案决定去哪里取数据。

| 工具 | legacy | victoria |
|---|---|---|
| `execute_pod_promql`、prometheus 的 6 个工具 | Prometheus | 中心 vmselect，附加 `extra_label=cluster=<名称>`。VM 会把这个条件强制加到所有选择器上，模型写错集群也查不到别的集群 |
| `query_pod_logs` | Elasticsearch 容器日志 | 中心 vlsingle 里**该 Pod 相关的 K8s 事件**。查到事件时返回 `query_partial` + `coverage=partial`，没查到时返回 `query_succeeded` + `coverage=empty`；结果标注 `log_source=k8s_events`，并说明"未采集容器日志，请使用 kubectl_logs" |
| `query_pod_tracing` | DeepFlow + Tempo | `capability_missing` |
| `query_pod_topology`、Pod 生命周期 | K8s 实时对象 | 同左，经 kubectl 垫片 |

- 所有结果顶层增加 `cluster` 和 `backend` 字段，其余格式不变。
- `query_pod_logs` 复用现有工具而不新增工具，因为 MCP 的工具列表是静态的；新增工具还要改 AIOps 的提示词和各节点的工具清单。
- 结果必须符合 AIOps 的观测契约（`app/core/context/observation.py`）：`ok=true` 时 `query_succeeded` 不能配 `partial`。MCP 8.0.4 违反了这一条，导致每次日志查询都被判"契约无效"。现在由验收脚本 `contract_mcp_aiops.py` 把每个集群上各工具的真实输出交给 AIOps 解析器校验。

新后端的事件是非结构化文本，放在 `_msg` 字段里：
- `level` 恒为 `INFO`，真实类型在文本的 `type:` 里；
- 字段名有拼写错误 `reasoni`；
- `kubernetes.pod_name` 是 event-exporter 自己的 Pod，不是事件涉及的对象。

采集器（`collectors/victorialogs_events.py`）先按 `cluster` 字段过滤，再按涉及对象名精确比对。

## 5. 集群访问层：kubectl 垫片与边缘 runner

### 5.1 垫片

MCP 和 AIOps 镜像里，真正的 kubectl 改名为 `kubectl.real`，`/usr/local/bin/kubectl` 是垫片：

```
kubectl get pods -A | jq …          （现有工具模板，一行不改）
  │ AIOPS_CLUSTER 为空或是本集群 → exec kubectl.real（与改造前完全相同）
  │ AIOPS_CLUSTER 是边缘集群：
  │   1. kubectl_args.classify：拒绝 -f/--follow、-w、-it、port-forward、--kubeconfig/--as 等；判定 read/exec/write
  │   2. TunnelClient.request(cluster, "/v1/kubectl", {argv, mode, timeout_s:15, compress:true})
  │   3. 原样写回 stdout / stderr，退出码与真实 kubectl 一致
  ▼
管道后面的 jq 在中心本地处理 runner 返回的输出
```

设置 `AIOPS_CLUSTER` 的调用方有：MCP 的 `_command_runner`，以及 AIOps 的 `run_argv(args, cluster=)`（修复执行、恢复观察、Pod 身份补全、预期状态核实都经过它）。

不直接把 kubeconfig 指向隧道，原因有两点：
- 隧道的 http 通道不带集群 CA 和 token，也不支持 exec 需要的连接升级；
- `/proxy?clientid=…&address=…` 这种格式不能作为 kubeconfig 的 `server`。

### 5.2 runner

部署在每个边缘集群的 `aiops` 命名空间：1 个副本，ClusterIP Service，端口 8090，不对外暴露。

| 接口 | 用途 | 身份 |
|---|---|---|
| `GET /healthz` | 版本、规则版本、能力 | — |
| `POST /v1/kubectl` | 同步执行一条 kubectl：`{argv, mode, timeout_s, compress}` | read 用 reader；exec / write 用 writer |
| `POST /v1/jobs` | 提交异步修复动作：`{idempotency_key, argv, approval_id, timeout_s}`，立即返回 `job_id` | writer |
| `GET /v1/jobs/{id}` | 查询任务状态和输出 | — |

收到请求后的处理（`aiops_edge/runner/server.py`、`gate.py`）：
1. 校验签名，失败返回 401；
2. 再次检查参数规则，并核对声明的模式与命令实际类型一致；
3. read 只允许只读子命令；exec / write 按中心同一份命令规则检查：黑名单一律拒绝，需审批的命令必须带 `approval_id`；
4. 执行 kubectl。原始输出最多 4MB，请求压缩时用 gzip+base64 传输；
5. 写本地审计日志。

**身份（`deploy-edge/runner.yaml`）**

- **reader**：`view` + 集群级只读（nodes、namespaces、pv、storageclasses、events）。
- **writer**：修复所需的最小写权限。包括 Pod 的 create / delete / patch、`pods/exec`，工作负载（Deployment、StatefulSet、DaemonSet、ReplicaSet）的修改，以及 scale。

**任务**

- 按 `idempotency_key` 去重，重复提交返回同一个 `job_id`。
- 记录保留 24 小时，并写入 emptyDir：runner 容器重启后仍在，Pod 重建后丢失（中心会把这种情况判为"结果未知"）。

## 6. 中心到边缘的消息

中心到边缘只有一种消息：经 xnet 隧道转发的一次 HTTP 请求。

```
POST https://xnet-management.xnet.svc:9090/proxy
     ?clientid=<集群 UUID>
     &address=http://aiops-edge-runner.aiops.svc:8090/v1/kubectl
TLS：xnet CA 签发的客户端证书（mTLS，从 xnet 复制来的副本）
请求头：X-AIOps-Timestamp、X-AIOps-Nonce、
        X-AIOps-Signature = HMAC-SHA256(密钥, 时间戳 + nonce + 方法 + 路径 + sha256(请求体))
请求体：{"argv": [...], "mode": "read", "timeout_s": 15, "compress": true}
```

1. xnet 隧道服务端按 `clientid` 找到该边缘外连进来的 websocket，把整个 HTTP 请求序列化后推给边缘；
2. 边缘的 xnet-agent 在边缘集群内向 `address` 发起请求，响应沿原路返回；
3. runner 校验签名：时间偏差超过 60 秒、nonce 在 5 分钟内重复、签名不对，一律拒绝。只持有 xnet 证书的人调用不了 runner。

xnet 对每个请求最长等 20 秒，我们的同步调用上限是 15 秒。错误分类：

| 情况 | 返回码 |
|---|---|
| 边缘没连上隧道（xnet 返回 400 "not online"）、runner 不可达（408） | `cluster_unreachable` |
| 证书失效或握手失败 | `tunnel_auth_failed`（提示重新执行 `make sync-xnet-cert`） |
| 超时 | `timeout` |
| 签名不对 | `runner_auth_failed` |
| 规则拒绝 | `policy_denied`（带规则名） |

## 7. 路由与集群范围

路由契约增加三个字段：`cluster_mode`、`clusters`、`cluster_labels`（`request_router.py`、`app/core/multicluster.py`）。

- 多集群部署下，路由提示词会追加一段说明（`router_prompt`），列出每个集群及其角色（中心集群 / 边缘集群）。
- **模型按自己对意图的理解选择范围**，不做任何特判：提示词只列出集群及其角色，说明几种范围的含义和写法，**不放示例原话**（下表的例子只用于说明，不在提示词里）。单元测试 `test_router_prompt_states_principles_not_sample_questions` 保证意图样例里的问题不会出现在提示词中。

| cluster_mode | 何时使用 | 例子 |
|---|---|---|
| `none` | 不需要任何集群的数据 | "什么是 CrashLoopBackOff" |
| `inventory` | 问集群本身的清单、角色与在线情况 | "我现在有哪些集群" |
| `single` / `multiple` / `center` | 需要集群里的实际数据 | "edge-88 上有哪些 Pod 异常"、"中心集群有什么 Pod 异常" |
| `unspecified` | 需要集群数据，但问题和会话都没说是哪个集群 | 开局就问"有哪些 Pod 异常" |

`clusters` 的写法：
- 用户说的集群名或别名，原样填写；
- `["*"]` 表示全部集群（含中心）；
- `["*edge"]` 表示全部边缘集群（不含中心），对应"所有边缘集群""各个子集群"这类说法。

追问时沿用上文的 `request_contract.clusters`。

**代码只做三项与措辞无关的工程保证**（`resolve_contract`）：
1. 范围不明确时反问："中心集群、某个边缘集群，还是全部集群？"
2. 集群名不存在时，列出可用集群；
3. 修复只针对一个集群。

路由卡片显示本次范围（`cluster_labels`）。

## 8. 工具如何带上集群

- **MCP**：多集群部署下，所有可观测工具、k8s-core、bash 和 helm 的 schema 都增加 `cluster` 参数；缺少这个参数时返回 `cluster_required`。单集群部署下 schema 不变。
- **AIOps 绑定**（`multicluster.scoped_tools`，在 `graph._bind_cluster_scope` 和并行取证通道里调用），由代码保证，不依赖模型：

| 运行范围 | 处理 |
|---|---|
| 单集群部署 | 不处理 |
| 本次只涉及 1 个集群 | 强制注入该集群，覆盖模型传入的值 |
| 涉及多个集群 | 模型必须填写，且必须在范围内，否则直接返回错误 |
| 并行取证通道 | 使用该异常组所属的集群 |

**远端集群上各类工具的能力：**

| 工具 | 远端集群 |
|---|---|
| 可观测工具 | 由后端档案决定 |
| k8s-core（get、describe、logs、events、lineage、jq 查询等） | 经垫片 |
| `run_bash_command` | 只允许以 `kubectl` 开头、后接本地文本处理（jq、grep、awk 等）的命令。其他程序会在中心 MCP Pod 里执行，对边缘没有意义，所以直接拒绝 |
| helm | `capability_missing`：helm 直接调用 K8s API，不经过 kubectl，垫片覆盖不到 |

**在边缘 Pod 里执行命令**（例如"在 edge-88 的某 Pod 里执行 ls"），路径与单集群相同：中心先由 `operate_tools.guard_write_tool` 检查规则，再经垫片到 runner，runner 再检查一遍。需人工审批的命令在对话中不执行，而是提示通过修复方案提交。

## 9. 快速查询与深度诊断

### 9.1 快速查询

一个 Agent 循环，工具按 §8 绑定。涉及多个集群时，模型对每个集群分别调用工具。

### 9.2 深度诊断：一个集群

layer → evidence / parallel_evidence → rca → conclusion 全部不变，所有工具调用都落在这个集群上。

### 9.3 深度诊断：多个集群

入口在 `autonomous_diagnosis.py` 的定位节点；涉及多个集群时进入 `multicluster_location.per_cluster_location`：

1. **探测**：每个远端集群先确认 runner 可达。不可达的集群不定位，由代码在报告开头写明"未完成检查的集群：…"。
2. **按集群并行定位**：每个集群新建一个定位节点，工具绑定到该集群。如果定位过程中模型连接中断，该集群自动重试一次（用户主动停止时不重试）；仍然失败，就记为"未完成检查"。
3. **合并结果**：
   - 目标 ID 加集群前缀（`edge-88/t1`），同名对象不会冲突；
   - 异常组带上 `cluster` / `cluster_label`；
   - 各集群按声明排除的对象（§11）汇总到 `expected_exclusions`。
4. **整体评估**：合并后如果判为"健康"，但有集群没查完，改判"检查不完整"（inconclusive），不能对外说"没有异常"。
5. **清单核对**（单集群同样适用，`workflow/inventory_reconcile.py`）：每个集群定位结束后，代码自己读一次该范围的 Pod 清单（远端经垫片和 runner），按与 `lifecycle_core.NOMINAL_CRITERIA` 相同的标准找出非正常状态的 Pod（未就绪、不在运行、10 分钟内终止过、删除中）。模型没有列为目标的，补为待调查目标，`issue` 写原始状态事实。挂在已配置集群的虚拟 Node 上的 Pod 跳过；读取失败时不改动。随后照常应用运维声明（§11）。起因：run `51d58579` 中，模型以"按列返回"的形式读清单（代码解析不了），并漏掉了自己工具结果里 `ready:false` 的 c09。
6. **每个异常 Pod 都取证**：当前仍处于非正常状态的 Pod，定位阶段不能单方面结案。模型标成 `assessed` 的，清单核对时改回 `investigate`，照常走取证和正式根因分析。`assessed` 只用于已核实、当前已恢复的对象；`deferred`（带理由的暂缓）和 `excluded`（运维声明）不受影响；未知的状态值按 `investigate` 处理。剩下的 `assessed` / `deferred` 目标由代码在总览开头写明"定位阶段已判断、未单独取证的对象：…（依据）"。提示词同时规定：测试标签、环境变量、命名只解释背景，不能把当前异常判为预期。起因：run `51d58579` 中 edge-88 的 c08、c10 被判为"预期的测试场景"，报告写成"edge-88 无报告异常"；run `73f4a1f5` 中两者又因"原因已看出"被标为 `assessed`，没有取证。
7. **并发取证**：所有异常组放进同一个并发池；每个通道绑定自己组的集群；只剩一个组时，范围收窄到该集群。
8. **报告**：各组标题和前端诊断卡片都带集群名。总览的输入里有 `unchecked_clusters` 和 `excluded_by_declaration` 两份清单，模型不得把未检查的集群说成"已覆盖"，也不得把已排除的对象列为异常。

**事件流约定**（UI 依赖）：
- 各集群定位产生的事件仍记在 `layer` 节点下，并带 `cluster_lane=<集群标签>`（`ClusterLaneQueue`）。
- 每个集群依次上报进度：检查连通性 → 定位中 → 完成 / 不可达 / 失败。
- 不能借用并发取证的 `LaneQueue`：它会把事件改记到 `parallel_evidence`，导致问题定位阶段提前结束（run `e43e8298`）。
- 每个阶段（定位、取证、根因）交付后，把它交出的分析正文作为一条 `ai_message` 推给前端（根因阶段推"诊断结论 + 原因"）。阶段的分析写在结构化结果里，不会逐字推送；之前前端只看得到推理（run `cc5f9fc7`：每个阶段可见正文约 19 个字）。
- `e2e_ask.py --phase p5` 会检查这些规则。

## 10. 修复

```
诊断（集群已绑定）→ 生成方案（修复节点的工具同样绑定到该集群）
  → 审批卡片：payload / 事件带 cluster，前端显示"将在集群 edge-88 执行"
  → PodRepairExecutor（app/core/remediation/pod_executor.py）：
      1. 从 request_contract.clusters 得到目标集群；本集群走原逻辑
      2. 执行前确认集群可达；不可达就等待（最长 AIOPS_REMOTE_WAIT_SECONDS，默认 600 秒），
         并提示"集群当前不可达"，超时仍未恢复则不执行（cluster_unreachable）
      3. execute 阶段 → POST /v1/jobs {idempotency_key: "<run_id>:<动作ID>:execute", argv, approval_id}
         runner 立即返回 job_id，在边缘后台执行；同一个键重复提交只执行一次
      4. 中心轮询 GET /v1/jobs/{id}，隧道报错时继续轮询，直到时限（单条命令时限的 3 倍，至少 300 秒）
         · succeeded / failed：正常记录
         · unknown（runner 容器重启）、记录丢失（runner Pod 重建）或超时：
           标记为 remote_result_unknown（"结果未知，需人工确认"），绝不重新提交
      5. dry-run、verify 和恢复观察都是只读操作，经垫片同步执行
  → 审计与进度事件带集群、审批 ID、任务键
```

需审批的命令（如 Pod 内 `rm`）：审批 ID 随任务交给 runner，runner 看到 ID 才执行；ID 的真实性由请求签名保证，因为只有中心能发出请求。

## 11. 运维声明的预期状态与虚拟节点

有些平台按设计就会出现"看起来异常"的对象。例如 xnet-management 做主备选举：同一时间只有 1 个副本 Ready，其余副本是 `0/1 Running`。模型无法自己知道这一点，所以由运维在集群配置里声明：

```yaml
expected_states:
  - cluster: center                       # 可选：集群名或别名；不写表示所有集群
    namespace: xnet
    workload: Deployment/xnet-management
    reason: 主备选举，同一时间只有 1 个副本 Ready，其余副本 0/1 Running 属于正常
    healthy_when: {ready_replicas_min: 1}
```

定位结束后，代码（`app/core/workflow/expected_states.py`）用实时数据逐个核对待排查的 Pod。必须同时满足以下条件，目标才会标为 `excluded`，原因写明"运维声明：…（1/3 Ready，满足至少 1 个）"：

1. Pod 属于声明的工作负载（控制器链 ReplicaSet → Deployment）；
2. Pod 处于 Running，且所有容器都在运行，只是未 Ready；
3. 工作负载满足 `healthy_when`。

任何一条不满足，或者无法核实（例如集群不可达），都照常诊断。

- 被排除的对象由代码写进报告："已按运维声明排除（不计为异常）：…"，不会悄悄消失。
- 如果所有待排查对象都被排除，代码直接给出结论：定位覆盖完整时判"健康"，不完整时判"检查不完整"。不再进入取证和根因分析。

**xnet 虚拟节点**：Node 名等于配置中集群名的节点，是 xnet 为接入的集群虚拟出来的，只表示集群已连接。代码根据配置生成说明（`multicluster.virtual_node_note`），写进定位和取证节点的材料：它们不是真实计算节点，不按承载工作负载的节点评估。代码里没有写死 `vc-` 前缀。

## 12. 前端

| 位置 | 显示 |
|---|---|
| 路由卡片 | 本次集群范围（`routePresentation.ts`） |
| 问题定位卡片 | **多集群并发定位看板**（`ClusterLaneBoard.tsx`）：顶部是总进度（已结束 x/N、工具调用数、未完成数）。每个集群一张卡片，显示状态、当前进度、该集群的工具调用、模型思考过程和定位分析；集群的工具只列在自己的卡片里 |
| 并发证据采集 | 每个集群一行进度（"edge-88：1/2 组已结束 · 6 条证据"），异常组标题带集群名 |
| 审批卡片 / 修复进度 | 目标集群；集群不可达时的等待提示 |

事件处理在 `chatEventTransition.ts` / `clusterLanes.ts`。`frountind/scripts/replay-sse.mjs` 可以把一段真实事件流交给同一份事件处理逻辑，输出 UI 最终的状态，验收脚本会用到它。

## 13. 安全

| 威胁 | 措施 |
|---|---|
| 持有 xnet 客户端证书的人可以访问边缘任意 Service | runner 要求 HMAC 签名并防重放；只有证书、没有密钥就调用不了 |
| 中心被绕过，直接调用 runner | runner 本地执行同一套命令规则；需审批的命令必须带审批 ID |
| runner 被滥用 | reader / writer 两个最小权限身份；只读接口不会使用 writer |
| 证书泄露范围 | 证书复制到我们自己的命名空间，只挂载给 MCP 和 AIOps；我们的 SA 不需要读取 xnet 命名空间 |
| 跨集群混用数据 | 工具层强制注入集群；VictoriaMetrics 用 `extra_label` 限定 |
| xnet 自身的问题 | **我们无法解决**：xnet-agent 拥有边缘集群的全部权限，JWT 密钥硬编码。我们只能保证"经过我们系统的操作是受控的" |

现有 MCP 的 ClusterRole 含 `*/*/*`，这是单集群下就有的风险，建议一并收缩。

## 14. 运维命令（robusta Makefile）

| 命令 | 作用 |
|---|---|
| `make runner-build` / `runner-push` | 构建 / 推送 runner 镜像（`Dockerfile.edge-runner`，版本见 `deploy-edge/VERSION`） |
| `make mc-keygen` | 生成签名密钥 |
| `make edge-deploy` / `edge-delete EDGE_KUBECONFIG=…` | 在边缘部署 / 卸载 runner |
| `make sync-xnet-cert` | 中心：复制 xnet 证书、下发签名密钥 |
| `make deploy-mc MC_LOAD_HOSTS=…` | 中心：部署 AIOps 及集群配置（mcpstander、frountind 各有同名目标） |
| `make test-multicluster` | 多集群单元测试 |

## 15. 已知限制

1. 集群登记是静态配置，没有自动发现（§3.1）；到达边缘只支持 xnet。演进方案见 §19。
2. 新后端没有容器日志和链路数据，诊断时只能用 K8s 事件和实时 `kubectl logs`。
3. 远端集群不支持 helm。
4. 快速查询还没有接入运维声明的预期状态（§11 目前只作用于深度诊断）。
5. `["*"]` 会展开为所有已配置的集群，不按在线状态过滤；不可达的集群在深度诊断里写明"未完成检查"，在快速查询里表现为工具返回 `cluster_unreachable`。
6. 恢复观察经垫片读取实时状态，没有优先使用中心指标。
7. runner 只有 1 个副本，Pod 重建后任务记录丢失（中心判为"结果未知"）。命令规则随 runner 部署下发，中心规则改了之后要重新执行 `make edge-deploy`。
8. `run_report` 没有按集群单独记录结果，未完成检查的集群只出现在状态（`cluster_failures`）和报告里。

## 16. 代码索引

| 功能 | robusta | mcpstander / frountind |
|---|---|---|
| 集群配置、别名、UUID | `aiops_edge/clusters.py` | 同步副本 `servers/aiops_edge/` |
| 路由范围 | `app/core/multicluster.py`、`workflow/nodes/request_router.py` | — |
| 工具绑定 | `multicluster.scoped_tools`、`workflow/graph.py`、`nodes/autonomous_parallel.py` | `servers/cluster_scope.py`（激活、schema、远端规则、`list_clusters`） |
| 可观测后端 | — | `servers/aiops_observability/`（metrics extra_label、`collectors/victorialogs_events.py`、tracing） |
| 垫片与隧道 | `aiops_edge/{shim,kubectl,tunnel,signing,streams}.py` | `bin/kubectl` |
| 多集群定位 | `workflow/multicluster_location.py` | — |
| 预期状态 | `workflow/expected_states.py`、`deploy-edge/clusters.mc.yaml` | — |
| 清单核对、阶段正文推送 | `workflow/inventory_reconcile.py`、`nodes/autonomous_diagnosis.py`（`_publish_stage_text`） | — |
| 契约字段容错 | `workflow/contract_coercion.py`（单个字符串 → 列表；JSON 文本 → 对象列表；缺 `target_id` 用对象身份） | — |
| 报告 | `workflow/case_report.py`、`nodes/query_answer.py` | — |
| 修复 | `remediation/pod_executor.py`、`aiops_edge/jobs_client.py` | — |
| runner | `aiops_edge/runner/`、`deploy-edge/runner.yaml` | — |
| 事件流投影 | `workflow/stream_contract.py`（`project_cluster_lane`） | — |
| 前端 | — | `ClusterLaneBoard.tsx`、`clusterLanes.ts`、`chatEventTransition.ts`、`parallelEvidenceModel.ts`、`routePresentation.ts`、`scripts/replay-sse.mjs` |
| 测试 | `tests/unit/multicluster/`、`scripts/acceptance/multicluster/` | `tests/test_cluster_scope.py`、`test_multicluster_wiring.py`、`test_aiops_edge_sync.py`；`tests/chat-transition.test.mjs` |

## 17. 与开发前设计的差异

| 开发前的设计 | 实现 | 原因 |
|---|---|---|
| runner 和垫片放在 mcpstander | 共享库 `aiops_edge/` 放在 robusta，mcpstander 同步除 runner 外的文件 | runner 必须复用 robusta 的命令规则（`policy.py`、`execution_guard.py`） |
| 集群自动发现（`discovery: xnet_nodes`） | 只有静态配置 | 测试环境的集群固定；xnet 虚拟 Node 只用于判断在线 |
| runner 输出上限 256KB | 4MB，可选压缩 | 实测 edge-88 的 `get pods -A -o json` 超过 256KB，截断会破坏 jq |
| "所有集群"只展开在线集群 | 展开所有已配置集群，不可达的集群由代码写明"未完成检查" | 不悄悄缩小范围 |
| 恢复观察优先用中心指标 | 经垫片读取实时状态 | 与单集群共用同一套恢复判定 |
| 范围识别：模型给出的集群必须出现在用户原话或会话中 | 13.0.12 起删除字面检查，改为按意图判断；13.0.14 增加集群角色和 `["*edge"]` | Boss 要求让 agent 理解意图；字面检查会把知识类问题也逼着选集群 |
| 多集群定位：每个集群各跑一次 layer | 同左，另加：事件带 `cluster_lane` 记在 layer 下；模型断线重试一次；总览接收未检查与已排除清单；预期状态声明 | run `e43e8298` 暴露的显示、覆盖与误报问题 |
| 新后端"日志"返回 `query_succeeded` + `partial` | `query_partial` / `empty` | AIOps 契约要求（MCP 8.0.5） |
| 测试环境从共用 Harbor 拉镜像 | 经 SSH 导入节点缓存，`IfNotPresent` | 测试环境的 Harbor 无推送权限；不修改节点配置 |
| 网络故障用防火墙模拟 | 不加防火墙：运行时依赖检查 + 只操作 runner 的故障注入 + 集成测试中的假隧道 | Boss 要求 |
| AIOps 挂载 Secret 用 0440 | 0444 | AIOps 容器以 uid 1000 运行，读不到 0440 的 root 文件 |

## 18. 依赖与部署形态

### 18.1 哪些问题用到 xnet，用到它的什么

xnet 在这套设计里只承担一件事：**把中心的一次 HTTP 请求送到边缘集群里的某个地址**（`/proxy`，见 §6）。我们没有自己实现隧道。边缘 runner 的两个 ServiceAccount 解决的是"在边缘以什么权限执行"，xnet 解决的是"中心的请求怎么到达边缘的 runner"：边缘的 runner 是 ClusterIP Service，真实环境里中心的网络到不了，只能借 xnet-agent 主动外连建立的那条通道。两者互不替代。

| 问题类型 | 例子 | 数据从哪来 | 用不用 xnet | 用到什么 |
|---|---|---|---|---|
| 不需要集群数据 | "OOM 是什么意思" | 模型知识 / Runbook | 不用 | — |
| 集群清单 | "我有哪些集群" | 集群配置 + 在线判定 | 用（只读） | 在中心 K8s 里读虚拟 Node 的 Ready；经 `/proxy` 调 runner `/healthz` |
| 指标、资源使用率 | "edge-88 节点内存使用率" | 中心 VictoriaMetrics（按 `cluster` 标签过滤） | 不用 | — |
| K8s 事件 | "edge-89 最近有什么告警事件" | 中心 VictoriaLogs | 不用 | — |
| K8s 实时查询 | "edge-88 有哪些 Pod 没就绪"、describe、日志 | 边缘 API Server | 用 | `/proxy` → runner `/v1/kubectl`（只读身份） |
| 深度诊断 | "所有边缘集群有什么 Pod 异常" | 定位和清单核对读 Pod 清单；取证读指标、事件、describe、上次崩溃日志 | 用 | 同上 |
| 修复 | "帮我修复 c06" | 边缘 API Server | 用 | `/proxy` → runner `/v1/jobs`（提交后轮询，绕开 xnet 单次 20 秒上限） |
| 任何问题，范围是中心集群 | "中心集群有什么异常" | 本集群 | 不用 | AIOps 用自己的 SA 直接执行 |
| 单集群部署（不挂集群配置） | 所有问题 | 原有链路 | 不用 | — |

### 18.2 xnet 证书从哪来

- **中心侧**（MCP、AIOps）调用 `/proxy` 需要 xnet CA 签发的客户端证书。`make sync-xnet-cert` 复制的是 xnet-management 自己调用隧道用的 `xnet-client-cert`（CN=localhost，Test CA 签发，有效期到 2031 年），复制到 `mcp`、`aiops` 两个命名空间，只挂载给 MCP 和 AIOps。
- **边缘 runner 不使用任何 xnet 证书**。它只认我们自己的 HMAC 签名密钥（`aiops-edge-key`），所以只持有 xnet 证书的人调用不了 runner。
- **边缘的 xnet-agent** 用的是它加入时由 xnet 签发的证书，跟我们无关。
- **评价**：复制 xnet 内部使用的客户端身份，是测试环境下的便捷做法。交付时建议由运维提供一张专门给 AIOps 的客户端证书，创建为 Secret `aiops-xnet-client-cert`；`sync-xnet-cert` 只作为"从现有 xnet 部署复制"的一种可选来源。代码只读取 Secret，不关心证书来自哪里。

### 18.3 部署方式

**单集群**（与 008 之前完全相同）：

| 组件 | 命令 | 前置条件 |
|---|---|---|
| MCP | mcpstander `make deploy` | K8s、原有可观测后端（Prometheus / ES / DeepFlow / Tempo，可缺省）、镜像仓库 |
| AIOps | robusta `make deploy`（或 `make release`） | Secret `aiops-secret`（LLM 网关地址与密钥）、ConfigMap |
| 前端 | frountind `make deploy` | — |

**多集群**：

| 位置 | 命令 | 作用 |
|---|---|---|
| 中心 | `make mc-keygen`、`make sync-xnet-cert` | 生成签名密钥；把 xnet 客户端证书和签名密钥放进 `mcp`、`aiops` 命名空间 |
| 中心 | mcpstander、robusta、frountind 各执行 `make deploy-mc` | 与单集群相同的镜像，额外挂载 ConfigMap `aiops-clusters` 和上述 Secret |
| 每个边缘 | `make edge-deploy EDGE_KUBECONFIG=…` | 部署 runner（两个 SA 与 RBAC、命令规则、签名密钥、Deployment、ClusterIP Service） |

**多集群的前置条件**（缺一项就不能工作）：

1. xnet-cloud 已安装，边缘已加入：中心能看到每个边缘的虚拟 Node，且为 Ready。
2. 新可观测体系：中心有 VictoriaMetrics 和 VictoriaLogs，边缘的 vmagent / vlagent 把数据推到中心，并且数据的 `cluster` 标签等于该边缘的虚拟 Node 名。
3. 中心能访问 LLM 网关；边缘能拉到 runner 镜像。
4. 部署时需要中心和各边缘的 kubeconfig；**运行时不依赖它们**：中心只用自己 Pod 的 SA，边缘只用 runner 的 SA。

### 18.4 MCP 和 AIOps 是否自动适配单集群和多集群

是的，同一个镜像。是否挂载 `AIOPS_CLUSTERS_CONFIG` 决定运行模式：

- **不挂载**：单集群。工具 schema 没有 `cluster` 参数，可观测后端读取原有的环境变量，行为与 008 之前一致（有单元测试保证）。
- **挂载**：多集群。工具多出 `cluster` 参数，并按集群选择后端；kubectl 经垫片转发；`list_clusters` 生效；路由要求说明范围。

部署上的差别只有"多挂一份配置和两个 Secret"，这正是 `deploy-mc` 与 `deploy` 的区别。不需要另外构建镜像，也不需要改代码。

## 19. 演进设计：集群发现与到达方式可替换（待 Boss 确认，未实现）

### 19.1 对照设计原则，现状的问题

| 原则 | 现状 | 问题 |
|---|---|---|
| 依赖抽象、组合优先 | `aiops_edge/tunnel.py` 直接调用 xnet `/proxy`；在线判定直接读虚拟 Node；`clusters.py` 由 `vc-` 名反算 xnet UUID | "怎么到达边缘"绑定在 xnet 这一种实现上 |
| 契约驱动、单一事实来源 | 集群清单写在静态 YAML 里，而 xnet 已经登记了同一份集群（虚拟 Node） | 两处登记；新增边缘要改配置再部署 |
| 扩展开放、修改封闭 | 增加一种非 xnet 的到达方式，要改核心代码 | 变化点没有隔离 |

已经符合原则的部分不动：数据走中心、操作走 runner（关注点分离）；MCP 吸收后端差异，AIOps 只看到统一的工具契约；runner 的 API、签名、命令规则、超时和任务轮询（生命周期可控）；以及假隧道和垫片的独立测试（可测试）。

### 19.2 只隔离两个已知会变的点

```
ClusterSource（有哪些集群）        EdgeTransport（怎么把请求送到边缘 runner）
  ├─ static：YAML（现状）            ├─ local：本集群直接执行（现状）
  └─ xnet_nodes：读虚拟 Node          ├─ xnet：/proxy（现状的 tunnel.py）
     （别名等仍可在 YAML 中补充）     └─ direct：runner 的 HTTPS 地址（Ingress / VPN / 专线）
                                       （不配置任何 transport = 只看观测数据）
```

- **ClusterSource** 只负责产出"集群名、角色、在线状态"。`xnet_nodes` 读取带 `node-role.kubernetes.io/xnet-agent` 标签的虚拟 Node：名字就是集群名（也就是观测数据的 `cluster` 标签），Ready 就是在线状态；YAML 只用来补充别名、预期状态和后端档案。注解里的加入令牌一律不读、不记日志、不交给模型。
- **EdgeTransport** 只负责"把一次已签名的 HTTP 请求送到 runner 并带回响应"，以及健康检查。runner、垫片、任务客户端、签名、命令规则都不变。
- **只看观测数据的集群**：不配置 transport。kubectl 类工具返回 `capability_missing`，诊断如实说明缺少 describe 和日志这类证据。
- 由配置选择实现，核心代码不再出现 xnet 字样。现有的 xnet 实现原样搬进对应的适配器。

### 19.3 有没有 xnet 时的能力对比

| 环境 | 发现 | 到达 | 能做 | 不能做 |
|---|---|---|---|---|
| 有 xnet（现状） | `xnet_nodes` 或 `static` | `xnet` | 全部 | — |
| 无 xnet，runner 可直连 | `static` | `direct` | 全部 | — |
| 无 xnet，只有新可观测体系 | `static` | 无 | 查询指标和事件；从 kube-state-metrics 找出异常 Pod | 实时 kubectl、修复；根因证据会少很多（没有 describe 和上次崩溃日志） |

这次只隔离这两个变化点，不做其他抽象（简单优先）。工作量估计：两个接口加三个适配器，配置格式加两个字段，以及对应的单元测试和一次三集群回归。
