# 多集群部署指南（AIOps + 可观测性）

一个**中心**集群统一提问、诊断和修复；每个**边缘**集群只部署采集器和一个 runner。中心经 xnet 隧道访问边缘，**不需要边缘的 kubeconfig**。

```
                        ┌──────────────── 中心集群 ────────────────┐
用户 / 前端 / A2A ────> │ AIOps ──> MCP ──> 中心 Prometheus / ES / DeepFlow（存所有集群的数据，按 cluster 过滤）
                        │                └─> xnet 隧道 ─────────────┐
                        └──────────────────────────────────────────┘│
                        ┌──────────────── 边缘集群 ────────────────┐│
                        │ aiops-edge-runner（执行 kubectl，按权限等级）<┘
                        │ Filebeat / Prometheus Agent / deepflow-agent ──> 推送到中心
                        └──────────────────────────────────────────┘
```

> **一句话**：先部署可观测性（每个集群一条 helm），再在中心装 AIOps（`mc-discover` → `mc-init` → `deploy-mc`），最后每个边缘执行 `edge-deploy`。全程只有一个配置文件 `deploy-edge/clusters.mc.yaml`，而且是自动生成的。

---

## 部署流程

```
⓪ 准备：确认 xnet 已接入，查看集群名 ─── make mc-discover
        ↓
① 部署可观测性：中心一条 helm、每个边缘一条 helm ─── status.sh 全部 OK
        ↓
② 在中心安装 AIOps ─── mc-discover WRITE=1 → mc-init → 3 个仓库 deploy-mc
        ↓
③ 加入边缘：每个边缘执行 ─── make edge-deploy
        ↓
④ 验证：前端问"我有哪些集群？"
```

### ⓪ 准备

- 部署机有 `git`、`make`、`kubectl`、`helm`、`python3`（含 PyYAML）、`openssl`。
- 边缘已经通过 xnet 接入中心：在中心执行 `kubectl get nodes`，能看到 `vc-…` 虚拟 Node。
- 中心和每个边缘都下载代码：

```bash
mkdir -p ~/aiops-workspace && cd ~/aiops-workspace
git clone ssh://git@10.2.0.86:9922/wanghuhu/mcpstander.git
git clone ssh://git@10.2.0.86:9922/wanghuhu/holmegpt-agent.git
git clone ssh://git@10.2.0.86:9922/wanghuhu/aiops-frount.git
git clone -b feat/multicluster-center-edge http://10.2.0.86/platform/observability.git   # 合并到 main 后去掉 -b
```

**确定集群名**：每个集群的集群名就是它的 xnet 虚拟 Node 名，可观测数据和 AIOps 都用这个名字。在中心执行（只读）：

```bash
cd ~/aiops-workspace/holmegpt-agent && make mc-discover
```

输出示例（`name` 就是集群名，后面注释里有角色和 IP）：

```
    - name: vc-xnet-management   # 中心，IP 10.2.5.85，Ready=True
      aliases: [center, 中心集群, 中心]
    - name: vc-942nkkozc8o5fyb9q3bznb1ws   # 边缘，IP 10.2.5.88，Ready=True
      aliases: [edge-88]
    - name: vc-dluw0jousipr6h5co2bwpyqk2   # 边缘，IP 10.2.5.89，Ready=True
      aliases: [edge-89]
```

### ① 部署可观测性

所有数据存在中心，边缘只装采集器。完整说明（部署后修改、排查、数据完整性）见 [observability 多集群指南](http://10.2.0.86/platform/observability/-/blob/feat/multicluster-center-edge/multicluster/README.md)。

```bash
# 中心节点（一次）
cd ~/aiops-workspace/observability
helm upgrade --install observability . -n monitor --create-namespace \
  -f multicluster/values-center.yaml \
  --set global.cluster=<中心的 vc-… 名> \
  --timeout 20m

# 每个边缘节点
cd ~/aiops-workspace/observability
helm upgrade --install observability . -n monitor --create-namespace \
  -f multicluster/values-edge.yaml \
  --set global.cluster=<该边缘的 vc-… 名> \
  --set global.centerAddress=<中心节点IP>

# 中心节点：约 3 分钟后检查，每个集群都是 OK 再继续
bash multicluster/status.sh
```

> `global.cluster` **必须**与 `mc-discover` 输出的 `name` 一致。AIOps 查询中心的指标、日志、链路时按这个名字过滤，名字对不上就查不到该集群的数据。

**改用 VictoriaMetrics**：按 [VictoriaMetrics K8s Stack](http://10.2.0.86/platform/cloud-observability) 的 README 部署中心和边缘，然后在第 ② 步的 `mc-discover` 加 `OBS=victoria`。两种方案的差别见下文“[EFK 与 Victoria](#efk-与-victoria)”。

### ② 在中心安装 AIOps（在中心节点执行）

```bash
cd ~/aiops-workspace/holmegpt-agent
make mc-discover WRITE=1                                   # Victoria：make mc-discover WRITE=1 OBS=victoria
make mc-init
cd ~/aiops-workspace/mcpstander     && make deploy-mc
cd ~/aiops-workspace/holmegpt-agent && make deploy-mc
cd ~/aiops-workspace/aiops-frount   && make deploy-mc
```

| 命令 | 做什么 |
|---|---|
| `make mc-discover WRITE=1` | 把 xnet 已接入的集群写进 `deploy-edge/clusters.mc.yaml`（两行 `###` 之间），每个集群的可观测档案默认是 `efk` |
| `make mc-init` | 经 xnet 签发接口申请 AIOps 专用证书（不复用 xnet 自己的证书），生成 runner 签名密钥，把集群配置写进中心的 ConfigMap `aiops-clusters`；最后**打印边缘要执行的命令** |
| `make deploy-mc`（3 个仓库） | 部署 MCP、AIOps、前端，挂载上面的集群配置和证书 |

### ③ 加入边缘（在每个边缘节点执行）

把 `mc-init` 最后打印的那条命令拿到边缘节点执行：

```bash
cd ~/aiops-workspace/holmegpt-agent
make edge-deploy EDGE=local RUNNER_KEY=<mc-init 打印的值>      # 可选 RUNNER_LEVEL=1|2|3，默认 2
```

- 权限等级：`1` 只读（只诊断）；`2` 读全部，可改常见修复对象，不能改 Secret 和 RBAC；`3` 管理员。
- 不想登录每个边缘时，可以在中心集中部署：
  1. 把边缘 kubeconfig 放到中心的 `~/.kube/aiops-mc/<别名>`。
  2. 在中心执行 `make edge-deploy EDGE=<别名>`。

  kubeconfig 只在部署时用，运行时不依赖它。

### ④ 验证

```bash
curl -fsS http://<中心IP>:30800/health                  # mcp_failed_servers 应为空
curl -fsS http://<中心IP>:30800/api/v1/mcp/status       # 每个 MCP 服务都是 connected
```

打开 `http://<中心IP>:30082`，依次提问：

1. "我有哪些集群？"：应列出全部集群，以及每个集群的指标、日志、链路是否可用。
2. "edge-88 有什么 Pod 异常？"：只查询 edge-88。

想试一个真实故障：在某个边缘执行 `make case-deploy CASE=c08`，问"edge-88 上 aiops-case-08 为什么一直重启？"。用完执行 `make case-clean CASE=c08` 清理。

---

## 部署后修改

### 配置文件一览

所有命令都在**中心**的 `holmegpt-agent` 目录执行，另有说明的除外。

| 文件 | 内容 | 什么时候改 |
|---|---|---|
| `deploy-edge/clusters.mc.yaml` ① `### 替换开始 ###` 之间 | 集群列表：集群名、别名、访问方式、可观测档案 | 由 `make mc-discover WRITE=1` 自动生成；只想改别名时可手改 |
| `deploy-edge/clusters.mc.yaml` ② `### 核对 ###` 之间 | 可观测档案（efk / victoria）：中心 Prometheus、vmselect 等后端的 Service 地址 | 可观测组件不在 `monitor` 命名空间，或 release 名不是默认值时 |
| `deploy-edge/clusters.mc.yaml` 的 `expected_states` | 运维声明的“看着异常、实际正常”的状态 | 有固定的、可忽略的异常状态时 |
| `deploy/configmap/config.yaml` | 诊断流程、修复模式（`workflow.remediation`）、高危命令规则 | 改行为时 |
| `deploy-edge/center/overrides.yaml` | 只对中心生效的配置项，合并进上面的 `config.yaml` | 中心要和单集群不一样时 |
| `deploy/secrets/core.yaml` 或 `deploy-edge/center/secret.yaml` | 模型地址、名称、Key | 换模型时；后者不入库，优先使用 |
| `~/.kube/aiops-mc/` | runner 签名密钥、AIOps 专用 xnet 证书（`mc-init` 生成） | 一般不动 |

### 改完怎么生效

| 改了什么 | 执行 |
|---|---|
| `clusters.mc.yaml`（集群、别名、档案、后端地址） | `make mc-init` → `mcpstander` 仓库 `make deploy-mc` → 本仓库 `make deploy-mc` |
| `config.yaml`、`overrides.yaml`、模型配置 | 本仓库 `make deploy-mc` |
| 高危命令规则（`workflow.remediation` 下的 `denied_*`、`approval_required`） | 本仓库 `make deploy-mc`，**并在每个边缘重新执行** `make edge-deploy …`（规则随 runner 下发） |
| 边缘 runner 权限等级 | 在该边缘重新执行 `make edge-deploy EDGE=local RUNNER_KEY=… RUNNER_LEVEL=<1/2/3>` |
| 重新申请 xnet 证书（到期前 30 天内 `mc-init` 会自动申请；xnet 重装后也要执行） | `make mc-cert RENEW=1` → `mcpstander` 和本仓库各执行 `make deploy-mc` |
| 可观测组件的参数（中心 IP、ES 密码、保留期等） | 在对应集群重新执行 helm，见 [observability 多集群指南 · 部署后修改](http://10.2.0.86/platform/observability/-/blob/feat/multicluster-center-edge/multicluster/README.md#部署后修改) |

> **注意别名**：`make mc-discover WRITE=1` 会整段重写 `###` 之间的内容，**手改的别名会被覆盖**。重新执行后，把自定义别名加回去，再执行 `make mc-init`。

### 集群配置示例

```yaml
clusters:
  ### 替换开始 ###
  default: null                      # null（推荐）：问题没写集群时先反问；填集群名：没写集群时默认用它
  center: vc-xnet-management
  items:
    - name: vc-942nkkozc8o5fyb9q3bznb1ws   # 集群名 = xnet 虚拟 Node 名 = 可观测数据里的 cluster
      aliases: [edge-88, 测试集群A]          # 提问时可用的别名，可以自己加
      access: xnet                         # 中心是 local，边缘是 xnet
      observability: efk                   # efk 或 victoria，对应下面的档案
  ### 替换结束 ###
```

---

## 新增 / 移除集群

### 新增一个边缘

```
① 新边缘接入 xnet ──> ② 新边缘部署可观测性 ──> ③ 中心更新集群配置 ──> ④ 新边缘部署 runner
```

```bash
# ① 在中心确认新集群出现，记下它的 name
cd ~/aiops-workspace/holmegpt-agent && make mc-discover

# ② 在新边缘部署可观测性，然后回到中心检查新集群为 OK
cd ~/aiops-workspace/observability
helm upgrade --install observability . -n monitor --create-namespace \
  -f multicluster/values-edge.yaml \
  --set global.cluster=<新集群的 vc-… 名> \
  --set global.centerAddress=<中心节点IP>
bash multicluster/status.sh                                   # 在中心执行

# ③ 在中心更新集群配置并重新部署（之前手改过别名的，执行 WRITE=1 后加回去）
cd ~/aiops-workspace/holmegpt-agent && make mc-discover WRITE=1 && make mc-init
cd ~/aiops-workspace/mcpstander     && make deploy-mc
cd ~/aiops-workspace/holmegpt-agent && make deploy-mc

# ④ 在新边缘执行 mc-init 打印的命令
cd ~/aiops-workspace/holmegpt-agent && make edge-deploy EDGE=local RUNNER_KEY=<mc-init 打印的值>
```

### 移除一个边缘

```bash
# 在该边缘执行
cd ~/aiops-workspace/holmegpt-agent && make edge-delete EDGE=local
helm uninstall observability -n monitor

# 在中心执行：从 clusters.mc.yaml 删掉该集群（或 xnet 摘除后重新 mc-discover WRITE=1），再重新部署
cd ~/aiops-workspace/holmegpt-agent && make mc-init
cd ~/aiops-workspace/mcpstander     && make deploy-mc
cd ~/aiops-workspace/holmegpt-agent && make deploy-mc
```

---

## EFK 与 Victoria

`clusters.mc.yaml` 里每个集群的 `observability` 决定 MCP 去哪里查、怎么按集群过滤：

| 维度 | efk（默认） | victoria |
|---|---|---|
| 指标 | 中心 Prometheus；MCP 在每条 PromQL 里注入 `cluster="<集群名>"`，无法注入的查询直接拒绝 | VictoriaMetrics；服务端强制按 `extra_label` 过滤 |
| 日志 | 中心 ES 的**容器日志全文**，按 `cluster` 字段过滤 | VictoriaLogs 中的 **K8s 事件**（没有容器日志） |
| 链路 / 网络流量 | 中心 DeepFlow，要求 Pod 一侧属于本集群（各集群 Pod 网段可以相同） | 无 |
| 集群实时状态（Pod、事件、describe） | 经 xnet 访问目标集群 | 相同 |

**切换档案**：

1. 部署对应的可观测性栈。
2. 执行 `make mc-discover WRITE=1 OBS=efk|victoria`，再执行 `make mc-init`。
3. `mcpstander` 和本仓库各执行 `make deploy-mc`。

两种栈的 Service 地址都在 `clusters.mc.yaml` 的 `### 核对 ###` 段里。

---

## 卸载

```bash
# 中心
cd ~/aiops-workspace/aiops-frount   && make delete
cd ~/aiops-workspace/holmegpt-agent && make delete
cd ~/aiops-workspace/mcpstander     && make delete

# 每个边缘
cd ~/aiops-workspace/holmegpt-agent && make edge-delete EDGE=local

# 可观测性（每个集群）
helm uninstall observability -n monitor
```

`make delete` 保留命名空间和运行历史（PVC）。要连历史一起删：`kubectl delete namespace aiops mcp`。

---

## 排查

| 现象 | 先检查 |
|---|---|
| "我有哪些集群？"里某集群的指标/日志/链路不可用 | 在中心执行 `bash multicluster/status.sh`（observability 目录），看该集群是否 OK、名字是否和 `clusters.mc.yaml` 一致 |
| 查某集群返回空数据，但 `status.sh` 是 OK | 集群名不一致：`helm get values observability -n monitor`（在该集群执行）里的 `global.cluster`，必须等于 `clusters.mc.yaml` 里的 `name` |
| 边缘的 kubectl 操作失败 / 超时 | 在边缘执行 `kubectl -n aiops get pods`，确认 runner 是 Running；`mc-init` 之后签名密钥变过的话，重新执行 `make edge-deploy` |
| `mc-init` 报证书错误 | `make mc-cert RENEW=1`；或使用运维提供的证书 `make mc-init XNET_CERT_DIR=<目录>` |
| MCP 服务 failed | `kubectl -n mcp logs deploy/mcp-server-manager`；多数是中心可观测组件的地址不对，核对 `### 核对 ###` 段 |

更多可选变量（`EDGE`、`RUNNER_LEVEL`、`MC_A2A_PUBLIC_URL`、`MC_SECRET_FILE` 等）见 [部署与运维](GUIDE.md#日常变更卸载与可选变量)，设计细节见 [多集群设计](multi-cluster-design.md)。
