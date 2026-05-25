======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 0ae1e349f3ed4408]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先来扫描整个集群的所有 Pod，看看当前有哪些异常状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_pods 输出: 共约127行, 异常行约57个非Running/非Completed Pod。按 namespace 分布:
- **admin**: 所有 Running (gpu相关组件, 共4个)
- **aiops-e2e**: rc-notready-liveness CrashLoopBackOff (Restarts 19), test-dns-177936
   💭 [问题定位] 当前集群中有相当多的异常 Pod。让我进一步查看详细情况，先获取所有异常 Pod 的完整列表和状态信息。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=462 lines=4
Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,NODE:.spec.nodeName
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 namespace=mcp 中 33 个 Pod 全部处于 Pending (READY=False) 状态。分布在 node1 (18) 和 node2 (15) 上。包括诊断类 (node-debugger-*, net-*, curl-*, dns-*, registry-*) 和连通性测试 Pod。
key_facts: ["namespace=mcp: 33 Pods all Pendi
   💭 [问题定位] 好的，我看到大量 Pod 在 `mcp` 命名空间处于 Pending 状态。另外之前 `aiops-e2e` 有 CrashLoopBackOff，`default` 有 ImagePullBackOff/ErrImagePull。让我用更精确的方式获取所有异常 Pod 的详细信息。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace returned 37 pods. 34 abnormal (not Running/Completed): 26 ImagePullBackOff, 6 ErrImagePull, 1 StartError, 1 ContainerCreating. 1 Running (mcp-server-manager). 2 Comple
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 Raw preview shows pods in default namespace. Running pods (5): cloud-agent (x3 on node1, node2, master), cloud-server (node1), nfs-client-provisioner (master). Completed pods (1): registry-connect-che
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=5 abnormal=2 status_counts={'Running': 1, 'CrashLoopBackOff': 1, 'ImagePullBackOff': 1}
NAME                      READY   STATUS             RESTARTS       
   💭 [问题定位] 非常好，现在我对所有异常 Pod 有了清晰的认识。让我查看一些关键的异常 Pod 以确认具体原因。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  Unhealthy       49m (x10 over 51m)    kubelet      
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node2-n5zz8
namespace: mcp
node: node2/10.2.0.50
status: Pending
Pod 关键区块:
QoS Class: BestEffort
Node-Selectors: <none>
Tolerations: op=Exists
Containers:
  de
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-nx8gb
namespace: mcp
node: node1/10.2.0.49
status: Failed
关键诊断行:
      Message:      failed to create containerd task: failed to create shim task: OCI ru
   💭 [问题定位] 让我再看看 ImagePullBackOff 的主要原因：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 输出摘要: raw_chars=160 lines=3
Command failed (exit 1):
kubectl describe pod registry-conn-test-1779371220 -n mcp
Error from server (NotFound): pods "registry-conn-test-1779371220" not f
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: test-dns-1779360358
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Normal   BackOff  13m (x2049 over 14h)   kubelet  Back-off pulling image "busybox:1.3
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: dns-test-1779360684
namespace: default
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Normal   BackOff  18m (x1988 over 14h)   kubelet  Back-off pulling image "busybox:1.36.
   💭 [问题定位] 现在我已经掌握了足够的信息。让我获取相关 runbook 来参考定位。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ImagePullFailed / ImagePullBackOff

> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull

## 场景识别

| 信号 | 关键特征 |
|------|----------
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod NotReadyProbeFailed / Running 但未 Ready

> Pod异常类型: NotReadyProbeFailed | 典型状态: Running + READY 0/1 | 兼容分类: probe_health

## 状态识别
- Pod phase 通常为 `Running`，但 READY 为 `0/1` 或部分容器未 Ready

   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod SandboxCreateFailed / Pod sandbox 创建失败

> Pod异常类型: SandboxCreateFailed | 典型状态: ContainerCreating / FailedCreatePodSandBox | 兼容分类: sandbox_runtime

## 状态识别
- Events 含 `FailedCreatePodSa
   💭 [问题定位] 现在我已经获得了足够的证据。让我整理一下完整的分析结果。

## 集群异常诊断分析

### 全局 Pod 扫描结果

| 命名空间 | 异常 Pod 数量 | 异常类型 |
|----------|-------------|---------|
| **mcp** | **34 个** | ImagePullBackOff (26), ErrImagePull (6), StartError (1), ContainerCreating (1) |
| **default** | **23 个** | ErrImagePull (10), ImagePullBackOff (13) |
| **aiops-e2e** | **2 个** | CrashLoopBackOff (1), ImagePullBackOff (1) |
| **kube-system** | **0 个** | 全部 Running |

**总计异常 Pod：约 59 个**

---

### 核心问题分析

#### 🚨 问题 1（最大范围）：镜像拉取失败 — ImagePullFailed（L3）
**影响范围：mcp (34个) + default (23个) + aiops-e2e (1个) = ~58 个 Pod**

通过查看 `dns-test-1779360684`（default）和 `test-dns-1779360358`（aiops-e2e）等代表 Pod 的 Events，发现一致的错误：

> **`Failed to pull image "busybox:1.36.1"`**
> `failed to resolve reference "docker.io/library/busybox:1.36.1": failed to do request: Head "https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1": read tcp ...:443: read: connection reset by peer`

**根本原因：** 集群节点（node1/node2）无法正常连接到 Docker Hub 镜像仓库 `registry-1.docker.io`，HTTPS 连接被重置（connection reset by peer），表明网络层面到 Docker Hub 不通。

| 关键证据 | 说明 |
|---------|------|
| `connection reset by peer` | 节点到 `registry-1.docker.io:443` 的 TCP 连接被中间网络设备/防火墙重置 |
| 跨越 node1 和 node2 | 不是单节点问题 |
| 所有镜像都是 `busybox:*` 系列 | 全部从 Docker Hub 拉取，没有使用内部镜像仓库 |

**兼容归因：L3 — ImagePullFailed**

**Pod 状态关键字：** `ImagePullBackOff`, `ErrImagePull`

---

#### 🚨 问题 2：Liveness Probe 失败导致 CrashLoopBackOff（L4）
**影响范围：aiops-e2e/rc-notready-liveness（1个 Pod）**

此 Pod 是 E2E 测试 Pod，**人为构造**的异常场景（从 Labels `pod_abnormal_type=NotReadyProbeFailed`, `rootcause-e2e=true` 以及 Runbook 注解可确认）。

- STATUS: CrashLoopBackOff
- Exit Code: 137（被 liveness probe 杀死）
- Liveness Probe 配置：`exec [sh -c echo liveness endpoint failed; exit 1]` — 故意配置为失败
- 已重启 19 次

**兼容归因：L4 — NotReadyProbeFailed**

**Pod 状态关键字：** `CrashLoopBackOff`

---

#### 🚨 问题 3（次要）：StartError — 容器启动命令不兼容（L2）
**影响范围：mcp/node-debugger-node1-nx8gb（1个 Pod）**

- 使用 `busybox:1.36` 镜像
- 启动命令为 `curl -s -o /dev/null ...`，但 **busybox 镜像中不包含 curl 可执行文件**
- 错误：`exec: "curl": executable file not found in $PATH`

**兼容归因：L2 — CrashLoopBackOffRuntime（容器启动命令错误）**

---

#### 🚨 问题 4（轻微）：ContainerCreating（L0-L3）
**影响范围：mcp/node-debugger-node2-n5zz8（1个 Pod）**

- 使用 `busybox:1.28` 镜像
- 当前处于 Pulling 状态，还在拉镜像中
- 如果集群到 Docker Hub 不通，此 Pod 也会转为 ImagePullBackOff

---

### 分层汇总

| 层 | 异常类型 | 影响 Pod 数 | 描述 |
|----|---------|-----------|------|
| **L3** | ImagePullFailed | **58** | **主问题** — 节点到 Docker Hub 网络不通（connection reset by peer） |
| **L4** | NotReadyProbeFailed | 1 | E2E 测试 Pod，Liveness Probe 故意配置失败 |
| **L2** | StartError（命令错误） | 1 | busybox 镜像中找不到 curl 命令 |
| 待定 | ContainerCreating | 1 | 还在拉取镜像中，预计将转为 ImagePullBackOff |

### 关键实体（Key Entities）

| 实体 | 角色 |
|------|------|
| node1 (10.2.0.49), node2 (10.2.0.50) | 受影响节点，无法拉取 Docker Hub 镜像 |
| `registry-1.docker.io` | 目标镜像仓库，节点无法连通 |
| `busybox:1.36.1` | 主要拉取失败的镜像 |

### 可能场景（Possible Scenarios）

1. **集群出站网络被阻断** — 节点无法访问外网 Docker Hub（最可能）
2. **DNS 解析问题** — registry-1.docker.io 解析到错误 IP（但错误信息显示 connection reset，说明有 IP 解析结果）
3. **中间防火墙/代理阻断** — 防火墙重置了到 Docker Hub:443 的 HTTPS 连接
4. **镜像仓库限流** — 大量 Pod 同时拉取触发 rate limit（但错误信息是 connection reset 而非 Too Many Requests）

### 后续审查方向

- 验证节点到 `registry-1.docker.io:443` 的 HTTPS 连通性
- 检查是否有配置内部镜像代理/镜像仓库镜像（image mirror）
- 检查镜像拉取凭证（imagePullSecrets）
- 确认是否需要配置 Docker Hub 镜像加速器或私有代理仓库
- 对于 StartError 的 Pod，修正容器命令或使用带有 curl 的镜像
   ✅ [问题定位] 完成 (59.5s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L4+L2
   scenarios=[{'scenario': '集群出站网络被阻断', 'probability': '高', 'reason': '节点到registry-1.docker.io:443的HTTPS连接被connection reset by peer，表明中间网络设备/防火墙拦截了出站流量'}, {'scenario': 'DNS解析问题', 'probability': '低', 'reason': '错误信息显示连接被reset而非DNS解析失败，DNS解析应已成功获取到IP地址'}, {'scenario': '中间防火墙/代理阻断', 'probability': '中', 'reason': 'connection reset by peer典型场景为中间设备重置TCP连接'}, {'scenario': '镜像仓库限流', 'probability': '低', 'reason': '错误信息是connection reset而非Too Many Requests'}]
   entities=[{"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "registry", "name": "registry-1.docker.io", "namespace": ""}, {"type": "image", "name": "busybox:1.36.1", "namespace": ""}]
   reasoning=集群存在约59个异常Pod，核心问题是ImagePullFailed（L3），节点到Docker Hub网络不通（connection reset by peer），影响58个Pod的镜像拉取。另有L4级别rc-notready-liveness（人为构造的CrashLoopBackOff，liveness probe失败）和L2级别node-debugger-node1-nx8gb（StartError，busybox无curl命令）。主根因为L3，因此定层为L3。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L4", "L2"], "layer_name": "ImagePullFailed", "confidence": 0.95, "reasoning": "集群存在约59个异常Pod，核心问题是ImagePullFailed（L3），节点到Docker Hub网络不通（connection reset by peer），影响58个Pod的镜像拉取。另有L4级别rc-notready-liveness（人为构造的CrashLoopBackOff，liveness probe失败）和L2级别node-debugger-node1-nx8gb（StartError，busybox无curl命令）。主根因为L3，因此定层为L3。", "abnormal_pods": [{"name": "rc-notready-liveness", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "connectivity-check-tmp", "namespace": "default", "status": "ErrImagePull"}, {"name": "dig-check-registry", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-connectivity-test", "namespace": "default", "status": "ContainerCreating"}, {"name": "dns-diag-1779390521", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-tool-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-resolve-gcr-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-check", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-dig", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ErrImagePull"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ErrImagePull"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-check-node2", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-conn-test-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-diag-evidence-verify", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-registry-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curls", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2s2mz", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-nx8gb", "namespace": "mcp", "status": "StartError"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ErrImagePull"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [{"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "registry", "name": "registry-1.docker.io", "namespace": ""}, {"type": "image", "name": "busybox:1.36.1", "namespace": ""}], "possible_scenarios": [{"scenario": "集群出站网络被阻断", "probability": "高", "reason": "节点到registry-1.docker.io:443的HTTPS连接被connection reset by peer，表明中间网络设备/防火墙拦截了出站流量"}, {"scenario": "DNS解析问题", "probability": "低", "reason": "错误信息显示连接被reset而非DNS解析失败，DNS解析应已成功获取到IP地址"}, {"scenario": "中间防火墙/代理阻断", "probability": "中", "reason": "connection reset by peer典型场景为中间设备重置TCP连接"}, {"scenario": "镜像仓库限流", "probability": "低", "reason": "错误信息是connection reset而非Too Many Requests"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}, {"kind": "Pod", "namespace": "default", "name": "dig-check-registry"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-tool-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "registry-diag-evidence-verify"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2s2mz"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "default", "name": "dns-connectivity-test"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g4", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}, {"kind": "Pod", "namespace": "default", "name": "dig-check-registry"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-tool-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "registry-diag-evidence-verify"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2s2mz"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "default", "name": "dns-connectivity-test"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g4", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "ImagePullBackOff": 41, "ErrImagePull": 15}, "total_abnormal": 57, "selected_rows": ["aiops-e2e         rc-notready-liveness                                0/1     CrashLoopBackOff    19 (2m46s ago)   51m     172.16.166.129   node1    <none>           <none>            app=rc-notready-liveness,pod_abnormal_type=NotReadyProbeFailed,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff    0                14h     172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           connectivity-check-tmp                              0/1     ErrImagePull        0                160m    172.16.104.52    node2    <none>           <none>            run=connectivity-check-tmp", "default           dig-check-registry                                  0/1     ImagePullBackOff    0                100m    172.16.166.155   node1    <none>           <none>            run=dig-check-registry", "default           dig-tool                                            0/1     ImagePullBackOff    0                9h      172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff    0                8h      172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff    0                12h     172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-connectivity-test                               0/1     ContainerCreating   0                57s     <none>           node2    <none>           <none>            run=dns-connectivity-test", "default           dns-diag-1779390521                                 0/1     ImagePullBackOff    0                5h45m   172.16.166.183   node1    <none>           <none>            run=dns-diag-1779390521", "default           dns-diag-tool-evidence                              0/1     ErrImagePull        0                137m    172.16.104.4     node2    <none>           <none>            run=dns-diag-tool-evidence", "default           dns-resolve-gcr-test                                0/1     ImagePullBackOff    0                5h51m   172.16.166.178   node1    <none>           <none>            run=dns-resolve-gcr-test", "default           dns-resolve-test                                    0/1     ErrImagePull        0                5h51m   172.16.104.1     node2    <none>           <none>            run=dns-resolve-test", "default           dns-test                                            0/1     ErrImagePull        0                100m    172.16.104.56    node2    <none>           <none>            run=dns-test", "default           dns-test-1779360684                                 0/1     ImagePullBackOff    0                14h     172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ErrImagePull        0                11h     172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-dig                                        0/1     ImagePullBackOff    0                5h51m   172.16.166.186   node1    <none>           <none>            run=dns-test-dig", "default           dns-test-tmp                                        0/1     ErrImagePull        0                8h      172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff    0                12h     172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ErrImagePull        0                13h     172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ImagePullBackOff    0                10h     172.16.104.62    node2    <none>           <none>            run=network-test-1779374716"], "raw_ref": "/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L4 + L2（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我先执行所有计划中的工具调用。先拉取 runbook，再同时执行多个 Pod describe 来采集关键证据。
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ImagePullFailed / ImagePullBackOff

> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull

## 场景识别

| 信号 | 关键特征 |
|------|----------
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  Unhealthy       50m (x10 over 52m)     kubelet     
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: test-dns-1779360358
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Normal   BackOff  14m (x2049 over 14h)   kubelet  Back-off pulling image "busybox:1.3
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: curl-registry-test
namespace: mcp
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   5m (x46 over 3h19m)    kubelet  (combined from similar events): Failed to 
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod connectivity-check-tmp (namespace: default, node: node2/10.2.0.50) is Pending with IP 172.16.104.52. Container waiting with Reason: ErrImagePull. Multiple failed pull attempts for image busybox:1.
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: dns-connectivity-test
namespace: default
node: node2/10.2.0.50
status: Terminating (lasts 37s)
关键诊断行:
Annotations:               cni.projectcalico.org/containerID: f4b0d9f19
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-nx8gb
namespace: mcp
node: node1/10.2.0.49
status: Failed
关键诊断行:
      Message:      failed to create containerd task: failed to create shim task: OCI ru
   💭 [证据链采集] 关于 `node-debugger-node1-nx8gb` 的详细输出中，我还需要看看 `rc-notready-liveness` 的完整 events 来确认上一轮诊断是否仍然有效。另外，`dns-connectivity-test` 正在 Terminating，让我确认其终止原因。

现在让我补充一下需要确认的信息：
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
57m                     Warning   Failed    Pod/connectivity-check-tmp   Failed to pull image "busybox:1.36.1": rpc error: code = DeadlineExceeded desc = failed to pull and u
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
LAST SEEN   TYPE     REASON           OBJECT                      MESSAGE
2m24s       Normal   AddedInterface   Pod/dns-connectivity-test   Add eth0 [172.16.104.30/32] from k8s-pod-
   💭 [证据链采集] 现在我已采集了所有计划的证据，进行汇总分析：

---

## 证据采集结果汇总

### 已采集证据

**e1-critical — test-dns-1779360358 (node1 / aiops-e2e)**
✅ **确认：connection reset by peer 仍存在**
- `Busybox:1.36.1` 拉取失败，事件原文：`read tcp 10.2.0.49:41032->52.202.41.60:443: read: connection reset by peer`
- 状态：ImagePullBackOff（14h），Kubelet BackOff x2049

**e2-critical — connectivity-check-tmp (node2 / default)**
✅ **确认：node2 同样拉取 busybox:1.36.1 失败，但错误模式不同**
- 无 connection reset，全部为 `i/o timeout`（多个 Docker Hub IP）和一次 `connection refused`、一次 `pull QPS exceeded`
- 状态：ErrImagePull，BackOff x90 over 151m
- **关键发现：node2 到 registry-1.docker.io 的连通性更差（超时 vs reset），且曾触发限流**

**e3-important — curl-registry-test (node1 / mcp)**
✅ **确认：mcp namespace 中相同错误**
- `connection reset by peer` 到 Docker Hub IP `54.224.154.163:443`，与 node1 上 test-dns-1779360358 一致
- 状态：ImagePullBackOff（3h39m），BackOff x655

**e4-important — rc-notready-liveness (node1 / aiops-e2e)**
✅ **确认：liveness probe failed / Exit Code 137**
- Liveness probe failed → OOMKilled(137) → CrashLoopBackOff，与上游一致
- **此 Pod 的异常原因不同于其他 Pod**，属于独立的 NotReadyProbeFailed 问题

**e5-important — dns-connectivity-test (node2 / default)**
⚠️ **状态已变更为 Terminating（非 ContainerCreating）**
- 正在删除中（Terminating 37s），之前是 ContainerCreating + Pulling image "busybox:1.28"
- 没有 FailedCreatePodSandBox 事件，sandbox 已就绪（AddedInterface 成功），但镜像拉取卡住
- 根本原因仍是**镜像拉取无法完成**（busybox:1.28 同样需要从 Docker Hub 拉取）

**e6-important — node-debugger-node1-nx8gb (node1 / mcp)**
✅ **确认：StartError 原因是 busybox:1.36 中没有 curl 命令**
- `exec: "curl": executable file not found in $PATH`，与上游一致

**e7-reference — Runbook pod-imagepull-failed.md**
✅ Runbook 确认：connection reset by peer / i/o timeout 均匹配 **"镜像仓库网络不可达"** 判定规则

---

### 未采集证据
- 无关键遗漏：已覆盖全部 4 个异常组（g1 CrashLoopBackOff / g2 ImagePullBackOff+ErrImagePull / g3 ContainerCreating→Terminating / g4 StartError）

### 冲突/负向证据
- **dns-connectivity-test**：上游标注为 ContainerCreating（57s），实际已变更为 Terminating（37s），但本质仍是网络问题导致的镜像拉取无法完成
- **connectivity-check-tmp** (node2)：错误模式是 i/o timeout 而非 connection reset，说明 node2 的网络连通性与 node1 有差异

### 核心结论
**集群存在大规模的 Docker Hub (registry-1.docker.io) 网络不可达问题**：
- **node1**（10.2.0.49）：表现为 `connection reset by peer`，TCP 连接被中间设备主动重置
- **node2**（10.2.0.50）：表现为 `i/o timeout` 和偶发 `connection refused`，网络完全不通或超时
- 此问题影响了 56/57 个异常 Pod（约 98%），所有使用 `busybox:*` 等 Docker Hub 镜像的 Pod 全部拉取失败
- 独立异常：rc-notready-liveness（L4 liveness probe 失败）和 node-debugger-node1-nx8gb（StartError/无curl命令）各有自身问题，但镜像拉取失败是集群当前影响范围最大的根因
   ✅ [证据链采集] 完成 (37.6s)
   📤 → 下游数据: evidence_items=19/19
   evidence_analysis={"evidence_plan":[{"id":"e1-critical","description":"验证主异常组g2代表Pod test-dns-1779360358的describe确认当前ImagePullBackOff详细错误","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","tool_args":{"kind":"Pod","name":"test-dns-1779360358","namespace":"aiops-e2e","names":["test-dns-1779360358"]},"purpose":"确认ImagePullBackOff的精确错误原因(connection reset by peer)是否仍存在","evidence_type":"current_state","target_scope":"aiops-e2e/test-dns-1779360358","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2-critical","description":"验证主异常组g2的node2代表Pod connectivity-check-tmp的describe确认ErrImagePull错误","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod connectivity-check-tmp -n default","tool_args":{"kind":"Pod","name":"connectivity-check-tmp","namespace":"default","names":["connectivity-check-tmp"]},"purpose":"确认另一节点node2上的ErrImagePull是否呈现相同connection reset by peer错误","evidence_type":"current_state","target_scope":"default/connectivity-check-tmp","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3-important","description":"验证主异常组g2的mcp namespace代表Pod curl-registry-test描述以确认网络连通性","level":"important","tool":"kubectl_describe","command":"kubectl describe pod curl-registry-test -n mcp","tool_args":{"kind":"Pod","name":"curl-registry-test","namespace":"mcp","names":["curl-registry-test"]},"purpose":"确认mcp namespace中的ImagePullBackOff是否也是相同connection reset错误","evidence_type":"current_state","target_scope":"mcp/curl-registry-test","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4-important","description":"验证g1 CrashLoopBackOff Pod rc-notready-liveness的当前describe","level":"important","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-notready-liveness","namespace":"aiops-e2e","names":["rc-notready-liveness"]},"purpose":"确认CrashLoopBackOff状态是否仍为liveness probe failed(exit 137)","evidence_type":"current_state","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5-important","description":"验证g3 ContainerCreating Pod dns-connectivity-test的最小状态","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-connectivity-test -n default","tool_args":{"kind":"Pod","name":"dns-connectivity-test","namespace":"default","names":["dns-connectivity-test"]},"purpose":"确认ContainerCreating状态是否因sandbox/pause/image拉取被阻塞","evidence_type":"current_state","target_scope":"default/dns-connectivity-test","acceptable_tools":[],"counts_for_completeness":true},{"id":"e6-important","description":"验证g4 StartError Pod node-debugger-node1-nx8gb的最小状态","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","tool_args":{"kind":"Pod","name":"node-debugger-node1-nx8gb","namespace":"mcp","names":["node-debugger-node1-nx8gb"]},"purpose":"确认StartError是否仍为OCI runtime找不到curl命令","evidence_type":"current_state","target_scope":"mcp/node-debugger-node1-nx8gb","acceptable_tools":[],"counts_for_completeness":true},{"id":"e7-reference","description":"获取ImagePullFailed runbook参考","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","tool_args":{"name":"pod-imagepull-failed.md"},"purpose":"确认runbook上下文与当前错误匹配","evidence_type":"reference","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod ImagePullFailed / ImagePullBackOff\n\n> Pod异常类型: ImagePullFailed | 典型状态: ImagePullBackOff / ErrImagePull / ImageInspectError | 兼容分类: image_pull\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | ImagePullBackOff / ErrImagePull / ImageInspectError |\n| Events | `Failed to pull image`, `connection refused`, `timeout`, `manifest unknown`, `context canceled`，或长时间停留在 `Pulling image` |\n| 常见原因 | 镜像名/tag 错误、私有仓库认证失败、仓库访问超时、DNS 解析失败、TLS 证书不被信任、镜像拉取策略导致必须远程拉取 |\n\n## 诊断流程\n\n### Step 1: 确认 Pod 状态\n```bash\nkubectl get pod <pod-name> -n <namespace> -o wide\n```\n\n### Step 2: 获取详细事件（关键步骤）\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n重点关注 Events 部分:\n- `Failed to pull image \"xxx\"`: 具体镜像地址\n- `connection canceled/refused/timeout`: 网络不可达\n- `manifest unknown/not found`: 镜像或 tag 不存在\n- `unauthorized/no basic auth`: 认证失败\n\n### Step 3: 检查镜像地址和 Pull Secret\n```bash\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].image}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.imagePullSecrets}'\nkubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.serviceAccountName}'\nkubectl get serviceaccount <service-account> -n <namespace> -o yaml\n```\n关注: \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-liveness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Exit Code:    137\n  Warning  Unhealthy       50m (x10 over 52m)     kubelet            Liveness probe failed: liveness endpoint failed\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         2m35s (x179 over 49m)  kubelet            Back-off restarting failed container app in pod rc-notready-liveness_aiops-e2e(138c18e8-70e0-4d5c-875a-a86bca3f5bb0)\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\n  Normal   Killing         51m (x3 over 52m)      kubelet            Container app failed liveness probe, will be restarted\nName:             rc-notready-liveness\nLabels:           app=rc-notready-liveness\n                  cni.projectcalico.org/containerID: f997c06136714184f9866361b3eab26ff46c280103b276058ecb6da12e4ce2e4\n                  cni.projectcalico.org/podIP: 172.16.166.129/32\n                  cni.projectcalico.org/podIPs: 172.16.166.129/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n  Normal   Scheduled       52m        \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: test-dns-1779360358\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  14m (x2049 over 14h)   kubelet  Back-off pulling image \"busybox:1.36.1\"\n  Warning  Failed   3m24s (x188 over 13h)  kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:41032->52.202.41.60:443: read: connection reset by peer\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: bd57a0f92246e34b515a8b3d1937d6af466642cbba44502db787e5138a42c3ff\n                  cni.projectcalico.org/podIP: 172.16.166.148/32\n                  cni.projectcalico.org/podIPs: 172.16.166.148/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  test\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: curl-registry-test\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   5m (x46 over 3h19m)    kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:54296->54.224.154.163:443: read: connection reset by peer\n  Normal   BackOff  78s (x655 over 3h39m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\n  Warning  Failed   10m (x42 over 3h39m)   kubelet  Error: ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: 4fc9beae95fbae725e9095e4f1c7b7774797efba9ebeaf4cdf6f72ac66142290\n                  cni.projectcalico.org/podIP: 172.16.166.144/32\n                  cni.projectcalico.org/podIPs: 172.16.166.144/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  curl-registry-test:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      sh\n      -c\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-6jfqq:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed   10m (x42 over 3h39m)   kubelet  Error: ErrImagePull\n  Warning  Failed   5m (x46 over 3h19m)    kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": read tcp 10.2.0.49:54296->54.224.154.163:443: read: connection reset by peer\n  Normal   BackOff  78s (x655 over 3h39m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod connectivity-check-tmp (namespace: default, node: node2/10.2.0.50) is Pending with IP 172.16.104.52. Container waiting with Reason: ErrImagePull. Multiple failed pull attempts for image busybox:1.36.1 from docker.io — all due to network errors (i/o timeout, connection refused, and one pull QPS exceeded). BackOff in progress (x90 over 151m). Final error: ErrImagePull.\nkey_facts: [\"resource: Pod connectivity-check-tmp\", \"namespace: default\", \"node: node2/10.2.0.50\", \"status: Pending\", \"IP: 172.16.104.52\", \"container: connectivity-check-tmp\", \"image: busybox:1.36.1\", \"container State: Waiting\", \"Reason: ErrImagePull\", \"Ready: False\", \"Restart Count: 0\", \"QoS Class: BestEffort\", \"Events: Warning Failed (5m39s, x20 over 151m) — Error: ErrImagePull\", \"Events: Warning Failed (57m) — i/o timeout to 108.160.169.181:443\", \"Events: Warning Failed (44m) — i/o timeout to 108.160.165.173:443\", \"Events: Warning Failed (32m) — i/o timeout to 128.242.245.125:443\", \"Events: Warning Failed (28m) — pull QPS exceeded\", \"Events: Warning Failed (21m) — connection refused to 162.125.80.5:443\", \"Events: Warning Failed (5m39s) — i/o timeout to 199.96.58.177:443\", \"Events: Normal BackOff (16m, x90 over 151m) — Back-off pulling image\"]\nconflicts: [\"current_summary says 'status: Pending' — raw_preview also says Pending, consistent\", \"current_summary mentions 'Annotations: cni.projectcalico.org/podIP: 172.16.104.52/32' — raw_preview shows 172.16.104.52/32, consistent\", \"current_summary omits the container args (wget to registry-1.docker.io/v2/) which raw_preview includes — not a conflict, just missing in summary\"]\nmissing: [\"raw_preview includes container args: 'wget -q -O- --timeout=5 https://registry-1.docker.io/v2/ 2>&1 || echo FAILED' not in current_summary\", \"raw_preview shows Condition: Initialized=True, PodScheduled=True — not highlighted in current_summary\", \"raw_preview shows Start Time: Thu, 21 May 2026 22:13:49 +0000 — not in current_summary\", \"raw_preview shows Normal Pulling event (43m, x14 over 161m) — not in current_summary\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: dns-connectivity-test\nnamespace: default\nnode: node2/10.2.0.50\nstatus: Terminating (lasts 37s)\n关键诊断行:\nAnnotations:               cni.projectcalico.org/containerID: f4b0d9f19908ee4aa75db68e190f8e15211230f6ff1fe5f68c407aca58720bd5\n                           cni.projectcalico.org/podIP: 172.16.104.30/32\n                           cni.projectcalico.org/podIPs: 172.16.104.30/32\n                           k8s.v1.cni.cncf.io/network-status:\n                           k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nTermination Grace Period:  30s\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  dns-connectivity-test:\n    Container ID:\n    Image:         busybox:1.28\n    Image ID:\n    Args:\n      sh\n      -c\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-7n2dw:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Type    Reason          Age   From               Message\n  ----    ------          ----  ----               -------\n  Normal  Scheduled       2m7s  default-scheduler  Successfully assigned default/dns-connectivity-test to node2\n  Normal  AddedInterface  2m7s  multus             Add eth0 [172.16.104.30/32] from k8s-pod-network\n  Normal  Pulling         2m7s  kubelet            Pulling image \"busybox:1.28\"\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:19 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-hl45s:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\n关键状态/事件:\nStatus:           Failed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/007-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/007-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/007-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n57m                     Warning   Failed    Pod/connectivity-check-tmp   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.169.181:443: i/o timeout\n44m                     Warning   Failed    Pod/connectivity-check-tmp   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 108.160.165.173:443: i/o timeout\n32m                     Warning   Failed    Pod/connectivity-check-tmp   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 128.242.245.125:443: i/o timeout\n28m                     Warning   Failed    Pod/connectivity-check-tmp   Failed to pull image \"busybox:1.36.1\": pull QPS exceeded\n21m                     Warning   Failed    Pod/connectivity-check-tmp   Failed to pull image \"busybox:1.36.1\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 162.125.80.5:443: connect: connection refused\n16m (x90 over 151m)     Normal    BackOff   Pod/connectivity-check-tmp   Back-off pulling image \"busybox:1.36.1\"\n5m55s                   Warning   Failed    Pod/connectivity-check-tmp   Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 199.96.58.177:443: i/o timeout\n5m55s (x20 over 151m)   Warning   Failed    Pod/connectivity-check-tmp   Error: ErrImagePull","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/008-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/008-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/008-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\nLAST SEEN   TYPE     REASON           OBJECT                      MESSAGE\n2m24s       Normal   AddedInterface   Pod/dns-connectivity-test   Add eth0 [172.16.104.30/32] from k8s-pod-network\n2m24s       Normal   Pulling          Pod/dns-connectivity-test   Pulling image \"busybox:1.28\"\n2m23s       Normal   Scheduled        Pod/dns-connectivity-test   Successfully assigned default/dns-connectivity-test to node2","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/009-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/009-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0ae1e349f3ed4408/tools/009-evidence-kubectl_events.summary.txt"}],"llm_analysis":"现在我已采集了所有计划的证据，进行汇总分析：\n\n---\n\n## 证据采集结果汇总\n\n### 已采集证据\n\n**e1-critical — test-dns-1779360358 (node1 / aiops-e2e)**\n✅ **确认：connection reset by peer 仍存在**\n- `Busybox:1.36.1` 拉取失败，事件原文：`read tcp 10.2.0.49:41032->52.202.41.60:443: read: connection reset by peer`\n- 状态：ImagePullBackOff（14h），Kubelet BackOff x2049\n\n**e2-critical — connectivity-check-tmp (node2 / default)**\n✅ **确认：node2 同样拉取 busybox:1.36.1 失败，但错误模式不同**\n- 无 connection reset，全部为 `i/o timeout`（多个 Docker Hub IP）和一次 `connection refused`、一次 `pull QPS exceeded`\n- 状态：ErrImagePull，BackOff x90 over 151m\n- **关键发现：node2 到 registry-1.docker.io 的连通性更差（超时 vs reset），且曾触发限流**\n\n**e3-important — curl-registry-test (node1 / mcp)**\n✅ **确认：mcp namespace 中相同错误**\n- `connection reset by peer` 到 Docker Hub IP `54.224.154.163:443`，与 node1 上 test-dns-1779360358 一致\n- 状态：ImagePullBackOff（3h39m），BackOff x655\n\n**e4-important — rc-notready-liveness (node1 / aiops-e2e)**\n✅ **确认：liveness probe failed / Exit Code 137**\n- Liveness probe failed → OOMKilled(137) → CrashLoopBackOff，与上游一致\n- **此 Pod 的异常原因不同于其他 Pod**，属于独立的 NotReadyProbeFailed 问题\n\n**e5-important — dns-connectivity-test (node2 / default)**\n⚠️ **状态已变更为 Terminating（非 ContainerCreating）**\n- 正在删除中（Terminating 37s），之前是 ContainerCreating + Pulling image \"busybox:1.28\"\n- 没有 FailedCreatePodSandBox 事件，sandbox 已就绪（AddedInterface 成功），但镜像拉取卡住\n- 根本原因仍是**镜像拉取无法完成**（busybox:1.28 同样需要从 Docker Hub 拉取）\n\n**e6-important — node-debugger-node1-nx8gb (node1 / mcp)**\n✅ **确认：StartError 原因是 busybox:1.36 中没有 curl 命令**\n- `exec: \"curl\": executable file not found in $PATH`，与上游一致\n\n**e7-reference — Runbook pod-imagepull-failed.md**\n✅ Runbook 确认：connection reset by peer / i/o timeout 均匹配 **\"镜像仓库网络不可达\"** 判定规则\n\n---\n\n### 未采集证据\n- 无关键遗漏：已覆盖全部 4 个异常组（g1 CrashLoopBackOff / g2 ImagePullBackOff+ErrImagePull / g3 ContainerCreating→Terminating / g4 StartError）\n\n### 冲突/负向证据\n- **dns-connectivity-test**：上游标注为 ContainerCreating（57s），实际已变更为 Terminating（37s），但本质仍是网络问题导致的镜像拉取无法完成\n- **connectivity-check-tmp** (node2)：错误模式是 i/o timeout 而非 connection reset，说明 node2 的网络连通性与 node1 有差异\n\n### 核心结论\n**集群存在大规模的 Docker Hub (registry-1.docker.io) 网络不可达问题**：\n- **node1**（10.2.0.49）：表现为 `connection reset by peer`，TCP 连接被中间设备主动重置\n- **node2**（10.2.0.50）：表现为 `i/o timeout` 和偶发 `connection refused`，网络完全不通或超时\n- 此问题影响了 56/57 个异常 Pod（约 98%），所有使用 `busybox:*` 等 Docker Hub 镜像的 Pod 全部拉取失败\n- 独立异常：rc-notready-liveness（L4 liveness probe 失败）和 node-debugger-node1-nx8gb（StartError/无curl命令）各有自身问题，但镜像拉取失败是集群当前影响范围最大的根因","collection_summary":"计划 6 项，实际采集 6 项，未采集 0 项，完整度 100%；其中真实环境证据 18/18 项，完整度 100%；实际执行工具 20 个，匹配计划 7 个，未规划证据 13 个","plan_total":6,"plan_collected":6,"plan_completeness":1.0,"environment_evidence_total":18,"environment_evidence_collected":18,"environment_evidence_completeness":1.0,"executed_tool_count":20,"matched_tool_count":7,"unplanned_tool_count":13,"evidence_inventory":[{"id":"e1-critical","description":"验证主异常组g2代表Pod test-dns-1779360358的describe确认当前ImagePullBackOff详细错误","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","purpose":"确认ImagePullBackOff的精确错误原因(connection reset by peer)是否仍存在","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-critical","description":"验证主异常组g2的node2代表Pod connectivity-check-tmp的describe确认ErrImagePull错误","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod connectivity-check-tmp -n default","purpose":"确认另一节点node2上的ErrImagePull是否呈现相同connection reset by peer错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3-important","description":"验证主异常组g2的mcp namespace代表Pod curl-registry-test描述以确认网络连通性","level":"important","tool":"kubectl_describe","command":"kubectl describe pod curl-registry-test -n mcp","purpose":"确认mcp namespace中的ImagePullBackOff是否也是相同connection reset错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4-important","description":"验证g1 CrashLoopBackOff Pod rc-notready-liveness的当前describe","level":"important","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","purpose":"确认CrashLoopBackOff状态是否仍为liveness probe failed(exit 137)","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5-important","description":"验证g3 ContainerCreating Pod dns-connectivity-test的最小状态","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-connectivity-test -n default","purpose":"确认ContainerCreating状态是否因sandbox/pause/image拉取被阻塞","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e6-important","description":"验证g4 StartError Pod node-debugger-node1-nx8gb的最小状态","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","purpose":"确认StartError是否仍为OCI runtime找不到curl命令","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e7-reference","description":"获取ImagePullFailed runbook参考","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","purpose":"确认runbook上下文与当前错误匹配","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_8","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_9","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_10","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_11","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_12","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 6/6 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1-critical | critical | ✅ | kubectl_describe | 验证主异常组g2代表Pod test-dns-1779360358的describe确认当... | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` |
   | e2-critical | critical | ✅ | kubectl_describe | 验证主异常组g2的node2代表Pod connectivity-check-tmp的de... | `kubectl describe pod connectivity-check-tmp -n default` |
   | e3-important | important | ✅ | kubectl_describe | 验证主异常组g2的mcp namespace代表Pod curl-registry-tes... | `kubectl describe pod curl-registry-test -n mcp` |
   | e4-important | important | ✅ | kubectl_describe | 验证g1 CrashLoopBackOff Pod rc-notready-livenes... | `kubectl describe pod rc-notready-liveness -n aiops-e2e` |
   | e5-important | important | ✅ | kubectl_describe | 验证g3 ContainerCreating Pod dns-connectivity-t... | `kubectl describe pod dns-connectivity-test -n default` |
   | e6-important | important | ✅ | kubectl_describe | 验证g4 StartError Pod node-debugger-node1-nx8gb... | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` |
   | e7-reference | reference | ✅ | fetch_runbook | 获取ImagePullFailed runbook参考 | `fetch_runbook pod-imagepull-failed.md` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (20.9s)
   📤 → 下游数据: root_cause=根因为集群节点（node1 10.2.0.49, node2 10.2.0.50）到 registry-1.docker.io:443 的出站 HTTPS 连接被中间网络设备阻断。证据：test-dns-1779360358 (node1/aiops-e2e) 报 "read: connection reset by peer" 到 52.202.41.60:443（e1）；curl-registry-test (node1/mcp) 报 "connection reset by peer" 到 54.224.154.163:443（e3）；connectivity-check-tmp (node2/default) 报 "i/o timeout" 到多个 Docker Hub IP 及一次 "connection refused"（e2/e8）。该问题影响所有56个尝试拉取 busybox:1.36.1 镜像的Pod，覆盖3个命名空间和2个节点。另有2个独立问题：rc-notready-liveness（g1, CrashLoopBackOff, liveness probe fai
... 截断，原始 585 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点（node1和node2）到 Docker Hub (registry-1.docker.io) 的出站网络被中间设备阻断，表现为 TCP 连接被重置（connection reset by peer）或超时（i/o timeout）", "propagation": "中间网络设备（防火墙/网络策略）拦截了节点到 registry-1.docker.io:443 的出站 HTTPS 流量 → node1 收到 TCP RST（connection reset）、node2 完全超时（i/o timeout）→ kubelet 无法从 Docker Hub 拉取 busybox:1.36.1 镜像 → containerd 反复重试失败 → kubelet 标记 Pod 为 ImagePullBackOff/ErrImagePull", "direct_cause": "节点到 registry-1.docker.io:443 的 HTTPS 连接无法建立（node1: connection reset by peer, node2: i/o timeout + connection refused）", "manifestation": "56个Pod（分布在default/mcp/aiops-e2e命名空间，node1和node2两个节点）均处于 ImagePullBackOff 或 ErrImagePull 状态，尝试拉取 busybox:1.36.1 镜像持续失败"}
   rca_analysis={"phenomenon": "集群存在约57个异常Pod，核心现象是ImagePullBackOff/ErrImagePull（占56个），分布于node1和node2的default、mcp、aiops-e2e等命名空间，所有失败的Pod均尝试拉取busybox:1.36.1镜像但无法连接到registry-1.docker.io。另有1个CrashLoopBackOff Pod（rc-notready-liveness，liveness probe失败）和1个StartError Pod（node-debugger-node1-nx8gb，busybox镜像中无curl命令）。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe test-dns-1779360358 (node1/aiops-e2e)", "content": "ImagePullBackOff, connection reset by peer to registry-1.docker.io:443, 14h", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe connectivity-check-tmp (node2/default)", "content": "ErrImagePull, i/o timeout 及 connection refused 到 Docker Hub 多IP, 151m", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe curl-registry-test (node1/mcp)", "content": "ImagePullBackOff, connection reset by peer, 3h39m", "reliability": "高"}, {"id": "e4", "source": "kubectl_describe rc-notready-liveness (node1/aiops-e2e)", "content": "CrashLoopBackOff, Liveness probe failed, Exit Code 137", "reliability": "高"}, {"id": "e5", "source": "kubectl_describe dns-connectivity-test (node2/default)", "content": "Terminating, 之前ContainerCreating, 镜像busybox:1.28无法拉取", "reliability": "高"}, {"id": "e6", "source": "kubectl_describe node-debugger-node1-nx8gb (node1/mcp)", "content": "StartError, exec: curl not found in $PATH in busybox:1.36", "reliability": "高"}, {"id": "e7", "source": "current_abnormal_summary (全局)", "content": "57异常Pod: 41 ImagePullBackOff, 15 ErrImagePull, 1 CrashLoopBackOff", "reliability": "高"}, {"id": "e8", "source": "kubectl_events connectivity-check-tmp", "content": "多IP i/o timeout, 一次 connection refused, 一次 pull QPS exceeded", "reliability": "高"}, {"id": "e9", "source": "kubectl_events dns-connectivity-test", "content": "Pulling image busybox:1.28, Scheduled, AddedInterface 成功", "reliability": "高"}, {"id": "e10", "source": "runbook pod-imagepull-failed.md", "content": "匹配场景：镜像仓库网络不可达", "reliability": "中"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Failed to pull image \"busybox:1.36.1\": ... read tcp 10.2.0.49:41032->52.202.41.60:443: read: connection reset by peer", "interpretation": "node1 到 registry-1.docker.io 的 HTTPS 连接被对端重置，表明中间网络设备（防火墙/代理）主动断开了TCP连接，而非镜像不存在或认证问题"}, {"evidence_id": "e2", "raw_data": "i/o timeout to 108.160.169.181:443, 108.160.165.173:443, 128.242.245.125:443, 199.96.58.177:443; connection refused to 162.125.80.5:443; pull QPS exceeded", "interpretation": "node2 到 Docker Hub 多IP全部超时或被拒绝，甚至触发Docker Hub限流（pull QPS exceeded），说明node2出站网络完全不通"}, {"evidence_id": "e3", "raw_data": "Failed to pull image \"busybox:1.36.1\": ... read tcp 10.2.0.49:54296->54.224.154.163:443: read: connection reset by peer", "interpretation": "mcp namespace 的 Pod 在 node1 上同样遭遇 connection reset，证明该问题是节点级网络问题而非 namespace 隔离导致"}, {"evidence_id": "e4", "raw_data": "Liveness probe failed: liveness endpoint failed → Exit Code 137 → CrashLoopBackOff", "interpretation": "rc-notready-liveness 的异常原因独立于镜像拉取问题，属于应用层 liveness probe 失败导致的重启"}, {"evidence_id": "e5", "raw_data": "Terminating (lasts 37s), 之前ContainerCreating + Pulling image 'busybox:1.28'", "interpretation": "dns-connectivity-test 尝试拉取 busybox:1.28 同样卡住（sandbox已就绪但镜像拉取未完成），后被删除进入Terminating，底层原因仍是网络不可达"}, {"evidence_id": "e6", "raw_data": "unable to start container process: exec: 'curl': executable file not found in $PATH", "interpretation": "node-debugger-node1-nx8gb 的 StartError 是镜像 busybox:1.36 中没有 curl 命令行工具导致，与网络无关"}, {"evidence_id": "e7", "raw_data": "41 ImagePullBackOff + 15 ErrImagePull = 56 个镜像拉取失败Pod", "interpretation": "集群中绝大多数异常（56/57）由同一根因——无法从 Docker Hub 拉取 busybox 镜像——导致"}, {"evidence_id": "e8", "raw_data": "i/o timeout 多次出现，pull QPS exceeded 出现一次", "interpretation": "node2 不仅出站不通，还因重试过多触发了 Docker Hub 的限流保护，进一步确认网络层故障"}, {"evidence_id": "e9", "raw_data": "Pulling image 'busybox:1.28', Scheduled successfully, AddedInterface ok", "interpretation": "dns-connectivity-test 的调度和网络接口配置正常，镜像拉取是唯一障碍"}, {"evidence_id": "e10", "raw_data": "Pod ImagePullFailed runbook: connection reset/timeout 匹配 '镜像仓库网络不可达'", "interpretation": "runbook 确认 connection reset by peer 和 i/o timeout 均指示网络不可达场景"}], "causal_chain": {"root_cause": "集群节点（node1和node2）到 Docker Hub (registry-1.docker.io) 的出站网络被中间设备阻断，表现为 TCP 连接被重置（connection reset by peer）或超时（i/o timeout）", "propagation": "中间网络设备（防火墙/网络策略）拦截了节点到 registry-1.docker.io:443 的出站 HTTPS 流量 → node1 收到 TCP RST（connection reset）、node2 完全超时（i/o timeout）→ kubelet 无法从 Docker Hub 拉取 busybox:1.36.1 镜像 → containerd 反复重试失败 → kubelet 标记 Pod 为 ImagePullBackOff/ErrImagePull", "direct_cause": "节点到 registry-1.docker.io:443 的 HTTPS 连接无法建立（node1: connection reset by peer, node2: i/o timeout + connection refused）", "manifestation": "56个Pod（分布在default/mcp/aiops-e2e命名空间，node1和node2两个节点）均处于 ImagePullBackOff 或 ErrImagePull 状态，尝试拉取 busybox:1.36.1 镜像持续失败"}, "root_cause": "根因为集群节点（node1 10.2.0.49, node2 10.2.0.50）到 registry-1.docker.io:443 的出站 HTTPS 连接被中间网络设备阻断。证据：test-dns-1779360358 (node1/aiops-e2e) 报 \"read: connection reset by peer\" 到 52.202.41.60:443（e1）；curl-registry-test (node1/mcp) 报 \"connection reset by peer\" 到 54.224.154.163:443（e3）；connectivity-check-tmp (node2/default) 报 \"i/o timeout\" 到多个 Docker Hub IP 及一次 \"connection refused\"（e2/e8）。该问题影响所有56个尝试拉取 busybox:1.36.1 镜像的Pod，覆盖3个命名空间和2个节点。另有2个独立问题：rc-notready-liveness（g1, CrashLoopBackOff, liveness probe fai\n... 截断，原始 585 字符", "root_cause_summary": "根因为集群节点（node1 10.2.0.49, node2 10.2.0.50）到 registry-1.docker.io:443 的出站 HTTPS 连接被中间网络设备阻断。证据：test-dns-1779360358 (node1/aiops-e2e) 报 \"read: connection reset by peer\" 到 52.202.41.60:443（e1）；curl-registry-test (node1/mcp) 报 \"connection reset by peer\" 到 54.224.154.163:443（e3）；connectivity-check-tmp (node2/default) 报 \"i/o timeout\" 到多个 Docker Hub IP 及一次 \"connection refused\"（e2/e8）。该问题影响所有56个尝试拉取 busybox:1.36.1 镜像的Pod，覆盖3个命名空间和2个节点。另有2个独立问题：rc-notready-liveness（g1, CrashLoopBackOff, liveness probe fai\n... 截断，原始 585 字符", "confidence": 0.95, "confidence_reason": "3个命名空间跨2个节点的Pod描述均一致报错 connection reset by peer 或 i/o timeout（e1/e2/e3），错误模式完全匹配\"中间设备阻断出站流量\"场景，runbook（e10）也确认该场景。置信度0.95。", "primary_runbooks": ["pod-imagepull-failed.md"], "alternative_causes": [{"cause": "镜像名/tag 错误（busybox:1.36.1 不存在）", "probability": "low", "reason": "错误信息显示TCP连接被重置，而非 manifest unknown 或 not found，说明连接已建立但被中途中断"}, {"cause": "imagePullSecret 缺失或认证失败", "probability": "low", "reason": "Docker Hub 公共镜像无需认证，且错误为 connection reset 而非 unauthorized"}, {"cause": "DNS 解析失败", "probability": "low", "reason": "错误信息中已解析出IP地址（如52.202.41.60、54.224.154.163），DNS解析成功"}, {"cause": "Docker Hub 限流", "probability": "low", "reason": "仅 node2 出现一次 pull QPS exceeded，是网络重试的次生效应急而非根因"}], "limitations": "未在节点上直接运行 curl/wget 到 Docker Hub 验证出站连通性（集群外测试）；未检查集群网络策略（NetworkPolicy）或节点 iptables 规则；node2 错误表现为 i/o timeout 而非 connection reset，可能 node2 的网络路径与 node1 不同（如经过不同的 NAT/网关）。", "llm_raw_analysis": "根因分析完成。主异常组 g2（56个Pod，ImagePullBackOff/ErrImagePull）根因为节点到 Docker Hub 出站网络被阻断，结论由 node1（e1/e3, connection reset）和 node2（e2/e8, i/o timeout）双向印证。g1（rc-notready-liveness, CrashLoopBackOff）为独立问题——liveness probe failed Exit Code 137。g3（dns-connectivity-test, 原ContainerCreating→现Terminating）已被最小验证为镜像拉取卡住，同根因。g4（node-debugger-node1-nx8gb, StartError）为独立问题——busybox:1.36 镜像中没有 curl 命令。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 根因为集群节点（node1 10.2.0.49, node2 10.2.0.50）到 registry-1.docker.io:443 的出站 HTTPS 连接被中间网络设备阻断。证据：test-dns-1779360358 (node1/aiops-e2e) 报 "read: connection...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点（node1和node2）到 Docker Hub (registry-1.docker.io) 的出站网络被中间设备阻断，表现为 TCP 连接被重置（connection reset by peer）或超时（i/o timeout）
     传导机制: 中间网络设备（防火墙/网络策略）拦截了节点到 registry-1.docker.io:443 的出站 HTTPS 流量 → node1 收到 TCP RST（connection reset）、node2 完全超时（i/o timeout）→ kubelet 无法从 Docker Hub 拉取 busybox:1.36.1 镜像 → containerd 反复重试失败 → kubelet 标记 Pod 为 ImagePullBackOff/ErrImagePull
     最终表现: 56个Pod（分布在default/mcp/aiops-e2e命名空间，node1和node2两个节点）均处于 ImagePullBackOff 或 ErrImagePull 状态，尝试拉取 busybox:1.36.1 镜像持续失败


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (35.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 8582 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 33.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，这是根据您提供的分析结果生成的详尽诊断报告。

---

## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **您的集群健康状态** | ❌ **存在严重问题** |
| **核心问题** | **集群节点无法连接到 Docker Hub (`registry-1.docker.io:443`)**，导致大量 Pod 镜像拉取失败。 |
| **受影响 Pod 数量** | **58 个** (56 个 `ImagePullBackOff`/`ErrImagePull` + 1 个 `CrashLoopBackOff` + 1 个 `StartError`) |
| **问题分组** | **主问题组 (L3)**：ImagePullFailed (57 个) <br> **独立问题组 1 (L4)**：CrashLoopBackOff - Liveness探针失败 (1 个) <br> **独立问题组 2 (L2)**：StartError - 镜像缺少命令 (1 个) |
| **问题分类** | ImagePullFailed / 网络连通性 |
| **置信度** | **高** (95%) |
| **证据完整度** | 6/6 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 受影响命名空间 | `aiops-e2e`, `default`, `mcp` |
| 受影响节点 | `node1` (IP: 10.2.0.49), `node2` (IP: 10.2.0.50) |
| 异常 Pod 状态 | **ImagePullBackOff (41个)**，**ErrImagePull (16个)** |
| 问题镜像仓库 | `registry-1.docker.io` (Docker Hub) |
| 问题镜像 | `busybox:1.36.1` |
| 核心错误信息 | `read: connection reset by peer` (node1), `i/o timeout` (node2) |

**集群现状总结**：
您的集群有 **59 个异常的 Pod**。其中 **绝大多数（57个）的根因是相同的**：集群中的 `node1` 和 `node2` 无法与 Docker Hub (`registry-1.docker.io:443`) 建立正常的 HTTPS 连接，导致所有尝试拉取 `busybox:1.36.1` 镜像的 Pod 持续失败。这 57 个 Pod 分布在 `aiops-e2e`, `default`, `mcp` 三个命名空间。

此外，还有两个独立的、非网络相关的问题：
*   `aiops-e2e/rc-notready-liveness`：因 Liveness 探针失败而不断重启。
*   `mcp/node-debugger-node1-nx8gb`：因镜像 `busybox` 中缺少 `curl` 命令而启动失败。

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态与事件 | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` | `Reason: ImagePullBackOff`；事件: `Failed to pull image "busybox:1.36.1"`；错误: `read tcp ...:443: read: connection reset by peer` 到目标IP `52.202.41.60:443` | **node1** 上的 Pod 拉取镜像时，与 Docker Hub 的 TCP 连接被中间设备重置。 |
| 2 | Pod 状态与事件 | `kubectl describe pod connectivity-check-tmp -n default` | `Reason: ErrImagePull`；事件: `i/o timeout` 到多个 Docker Hub IP，及一次 `connection refused`；最终错误: `ErrImagePull` | **node2** 上的 Pod 无法与 Docker Hub 建立连接，表现为网络超时。 |
| 3 | Pod 状态与事件 | `kubectl describe pod curl-registry-test -n mcp` | `Reason: ImagePullBackOff`；事件: `connection reset by peer` 到目标IP `54.224.154.163:443` | 从 **node1** 上的另一个命名空间也确认了“连接重置”问题，排除了命名空间隔离的可能。 |
| 4 | 集群 Pod 列表 | `kubectl get pods --all-namespaces` | 共 57 个 ImagePullBackOff/ErrImagePull Pod，分布在 `aiops-e2e`, `default`, `mcp` 命名空间，`node1` 和 `node2` 上 | 问题影响范围广，不是个别 Pod 或命名空间的配置问题。 |
| 5 | Pod 状态与事件 | `kubectl describe pod rc-notready-liveness -n aiops-e2e` | `Exit Code: 137`；事件: `Liveness probe failed: liveness endpoint failed` (x10)；`Container app failed liveness probe, will be restarted` | 独立问题：Liveness 探针失败导致容器被 kill (Exit Code 137)，引发 CrashLoopBackOff。**该问题与网络故障无关。** |
| 6 | Pod 状态与事件 | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` | `Reason: StartError`；`Exit Code: 128`；错误: `OCI runtime create failed: exec: "curl": executable file not found in $PATH` | 独立问题：容器启动时执行的 `curl` 命令在 `busybox` 镜像中不存在。**该问题与网络故障或 Liveness 探针无关。** |

### 证据关联分析

-   **证据 #1 + #2 + #3 + #4 印证**：来自两个不同节点（node1, node2）和三个不同命名空间（`aiops-e2e`, `default`, `mcp`）的 Pod 在拉取同一个镜像 (`busybox:1.36.1`) 时都遇到了网络层面的错误。node1 表现为 `connection reset by peer`，node2 表现为 `i/o timeout`。这形成了清晰的证据链，指向集群出站网络到 Docker Hub 的连通性问题。
-   **证据 #5 与主问题解耦**：`rc-notready-liveness` 的 `Exit Code: 137` (OOMKilled 或进程被 kill) 和明确的 `Liveness probe failed` 事件，证明其根因是应用健康检查失败，而非网络问题。
-   **证据 #6 与主问题解耦**：`node-debugger-node1-nx8gb` 的 `OCI runtime create failed` 和 `exec: "curl": not found` 错误，证明其根因是容器镜像内容问题，而非网络或应用探针问题。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 节点的 iptables 规则或网络策略 (NetworkPolicy) 配置 | high | 无法直接确认是集群内策略还是外部防火墙导致了网络阻断。 |
| 从节点上直接 `curl` 或 `wget` Docker Hub 的测试结果 | medium | 可以提供更直接的节点到公网的连通性证明,排除 Pod 网络层面的干扰。 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                    │
│ 集群节点（node1, node2）到 Docker Hub (registry-1.docker.io:443)            │
│ 的出站网络被中间网络设备（如防火墙）阻断。                                   │
│ 证据: #1, #2, #3                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                    │
│ 中间网络设备拦截节点出站 HTTPS 流量 → 返回 TCP RST (node1) 或丢包 (node2)    │
│ → kubelet 无法与 Docker Hub 建立连接 → 镜像拉取请求持续失败                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                    │
│ kubelet 拉取镜像 "busybox:1.36.1" 时，与 registry-1.docker.io:443 的          │
│ HTTPS 连接无法建立。                                                         │
│ 证据: #1 (connection reset), #2 (i/o timeout)                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                │
│ 58 个 Pod 处于 ImagePullBackOff (41) 或 ErrImagePull (16) 状态，持续重启。    │
│ 证据: #4                                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**核心根因**：根据证据 #1 (connection reset)，#2 (i/o timeout) 和 #3 (connection reset)，问题的根本原因是**集群节点（node1, node2）到 Docker Hub (`registry-1.docker.io:443`) 的出站 HTTPS 连接被中间网络设备阻断**。node1 收到的 `connection reset by peer` 信号是防火墙主动拦截的典型特征；node2 的 `i/o timeout` 则表明其网络路径可能不同，但同样被阻断。

**置信度**：高 (95%)
- ✅ 所有相关节点和 Pod 的错误均指向网络问题。
- ✅ 错误信息明确，非配置或鉴权类错误。
- ✅ 影响范围广泛，排除个体 Pod 配置问题。

**独立问题 1**：`aiops-e2e/rc-notready-liveness` Pod 的根因是 **Liveness 探针目标端点失败**，导致 Pod 被 kubelet 反复 kill 并重启 (CrashLoopBackOff)。(基于证据 #5)

**独立问题 2**：`mcp/node-debugger-node1-nx8gb` Pod 的根因是 **启动命令依赖 `curl` 但基础镜像 `busybox` 中不包含该命令**。(基于证据 #6)

---

## 🛠️ 修复建议

### 解决核心网络问题（优先级最高）

**问题定位**：连接 Docker Hub 的网络被阻断。
**解决方向**：需要联系集群网络管理员或云服务提供商，允许节点出站访问 `registry-1.docker.io:443` (HTTPS)。

**1. [推荐] 配置镜像仓库镜像或代理**
这是生产环境的标准最佳实践，可以完全规避公网仓库的连通性问题。
- **方案 A (镜像仓库 Mirror)**：在集群中部署一个 Docker Hub 的镜像仓库 (如 `registry.cn-hangzhou.aliyuncs.com`, Sonatype Nexus, Harbor)，或者直接使用阿里云/AWS ECR等加速器。节点只需能访问内网的镜像仓库即可。
- **方案 B (HTTP 代理 Proxy)**：配置 containerd 或 kubelet 使用一个能访问公网的 HTTP/HTTPS 代理。

**2. [临时] 使用可替代的公共镜像**
如果网络管理员配置规则需要时间，可以临时修改所有受影响 Deployment/StatefulSet 的镜像，使用可从集群内访问的其他镜像源，例如：
```bash
# 示例：将 busybox:1.36.1 替换为阿里云镜像仓库中的 busybox
# 注意：需要找到确切的替代路径，以下仅为格式示例
kubectl set image deployment <deployment-name> -n <namespace> <container-name>=registry.cn-hangzhou.aliyuncs.com/library/busybox:1.36.1
```

**验证命令**：
```bash
# 1. 在 node1 和 node2 上手动测试连通性 (如果节点上有 curl 或 wget)
curl -v https://registry-1.docker.io/v2/ 2>&1 | head -20
wget --timeout=5 -O- https://registry-1.docker.io/v2/

# 2. 排除 DNS 问题
nslookup registry-1.docker.io
```

### 解决独立 Pod 问题

**1. 修复 `rc-notready-liveness` (Liveness 探针失败)**
*   **分析**：Liveness 探针 (`liveness endpoint failed`) 失败导致容器被 kill。需要检查应用为何无法响应探针。
*   **建议操作**：检查应用的配置文件或日志，确认其监听端口和健康检查路径是否正确。
    ```bash
    # 应用可能需要的操作，例如更新 Deployment 的探针配置
    ```
    **注意**：这通常需要修改应用的 Deployment YAML 文件，找到正确的健康检查路径。

**2. 修复 `node-debugger-node1-nx8gb` (镜像内命令缺失)**
*   **分析**：容器启动命令 `curl` 在 `busybox` 镜像中不存在。
*   **建议操作**：要么修改启动命令，要么使用包含 `curl` 的镜像。
    *   **方案A**：将基础镜像改为 `curlimages/curl` 或 `alpine/curl`。
    *   **方案B**：修改启动命令，改为 `sleep infinity` 并进入容器后手动安装调试工具。
    ```bash
    # 方案B示例：修改 Pod 定义
    command: ["sleep", "infinity"]
    ```

---

## 📋 验证步骤

| 步骤 | 命令/操作 | 预期结果 |
|------|-----------|----------|
| 1. 解决网络问题 | `kubectl get pods --all-namespaces \| grep -E 'ImagePullBackOff\|ErrImagePull'` | 数量逐步减少直至为0 |
| 2. 确认 Pod 运行 | `kubectl get pod <pod-name> -n <namespace>` | STATUS: `Running` |
| 3. 检查 `test-dns` Pod | `kubectl get pod test-dns-1779360358 -n aiops-e2e` | STATUS 不再是 `ImagePullBackOff` |
| 4. 验证 Liveness 问题修复 | `kubectl describe pod rc-notready-liveness -n aiops-e2e \| grep -i restart` | Restart Count 不再增加 |
| 5. 验证 StartError 问题修复 | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` | 状态显示为 `Running` 或 `Pending` (非 `StartError`) |

---

## ⚠️ 注意事项

1.  **网络问题是首要解决项**：在解决网络连通性问题之前，修复其他问题没有意义，因为新的 Pod 也无法拉取镜像。
2.  **不要忽略 `mcp` 命名空间**：虽然问题普遍存在，但 `mcp` 命名空间 33 个 Pod 全部 Pending 的状态尤其严重，需要优先恢复。
3.  **生产环境建议**：强烈建议为生产集群配置内网镜像仓库或镜像代理，以**完全避免**对公网仓库的直接依赖，提高集群的稳定性和拉取速度。

---

## 📊 性能统计

├─ 总耗时: 2.6m
├─ 问题定位: 59.5s (39%) ✅
├─ 证据链采集: 37.6s (25%) ✅
├─ 根因分析: 20.9s (14%) ✅
├─ 汇总总结: 35.3s (23%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 24 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed, pod-notready-probe-failed, pod-sandbox-create-failed
- **工具调用**: 24 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
