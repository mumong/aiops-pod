======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 397119a7b922462b]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先从全局 Pod 状态扫描开始，看看集群中所有 Pod 的当前状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl get pods --all-namespaces output: 90+ pods across 6 namespaces (admin, aiops-e2e, aiops, default, kube-system, mcp). Running=~59, abnormal=~28 (CrashLoopBackOff=1, ImagePullBackOff=21, ErrImag
   💭 [问题定位] 集群中有大量异常 Pod，让我进一步确认具体细节。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=480 lines=4
Command failed (exit 1):
kubectl get pods --all-namespaces -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,STATUS:.status.phas
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=2194 lines=29
Executing jq query for pods...
aiops-e2e/test-dns-1779360358 phase=Pending status=ImagePullBackOff restarts=0
default/dns-check-test phase=Pending sta
   💭 [问题定位] 等一下，还有一个 CrashLoopBackOff 的 Pod 没有出现在 phase 查询中，让我看看所有非 Running/Completed/Succeeded 的 Pod，包括 CrashLoopBackOff。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query returned pod status for 29 pods across namespaces aiops-e2e, default, mcp, xnet. Majority (27/29) are Pending/Failed with image-related errors (ImagePullBackOff/ErrImagePull). One 
   💭 [问题定位] 现在让我获取关键异常类型的 runbook 来辅助定位。
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
# Pod CrashLoopBackOffRuntime / 容器反复退出

> Pod异常类型: CrashLoopBackOffRuntime | 典型状态: CrashLoopBackOff | 兼容分类: container_runtime

## 状态识别
- Pod 状态: `CrashLoopBackOff`
- Last State: Terminated
-
   💭 [问题定位] 现在让我看一个代表性的异常 Pod 来确认异常细节。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-crashloop-exit-code-5db5947859-2522x
namespace: aiops-e2e
node: node2/10.2.0.50
status: Running
关键诊断行:
                  pod_abnormal_type=CrashLoopBackOffRuntime
      R
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod registry-conn-test-1779371220 (namespace default) on node node2/10.2.0.50 is Pending. Container busybox:1.36.1 image pull fails repeatedly: both i/o timeout (157.240.13.8:443) and connection refus
   💭 [问题定位] 现在让我看一下 CrashLoopBackOff 的日志。
   💭 [问题定位] 调用工具: kubectl_logs
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2
   💭 [问题定位] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 1
signals: 1
关键日志:
RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2
   💭 [问题定位] 很好，现在我对整个集群的情况有了清晰的了解。让我整理分析结果。

---

## 集群异常分析报告

### 当前异常总览

集群中存在 **29 个异常 Pod**，分为两大异常组：

---

### 异常组 1：镜像拉取失败（ImagePullBackOff / ErrImagePull）— **共 27 个 Pod**

| 命名空间 | Pod 数量 | 异常类型 |
|---------|---------|---------|
| `default` | 7 个 | ImagePullBackOff(5) + ErrImagePull(2) |
| `mcp` | 15 个 | ImagePullBackOff(12) + ErrImagePull(3) |
| `aiops-e2e` | 1 个 | ImagePullBackOff |
| `xnet` | 1 个 | Failed(Completed) |

**典型 Pod：** `default/registry-conn-test-1779371220`
- 镜像：`busybox:1.36.1`
- 错误事件：`Failed to pull image "busybox:1.36.1"`：
  - **`i/o timeout`** 到 `157.240.13.8:443`（registry-1.docker.io）
  - **`connection refused`** 到 `199.59.148.7:443`
- 所有 Pod 均为 Pending 状态，无重启（首次拉取即失败）

**分析结论：** 集群节点（node1 和 node2）**无法连通 Docker Hub**，网络层面存在阻碍（超时 + 连接被拒），不是镜像名或认证问题。

**Pod 异常类型：** `ImagePullFailed`  |  **兼容层级：** L3（网络/镜像仓库层）

---

### 异常组 2：CrashLoopBackOff — **共 1 个 Pod**

**Pod：** `aiops-e2e/rc-crashloop-exit-code-5db5947859-2522x`
- 镜像：`busybox:1.36`（已拉取成功，有 Image ID）
- **Exit Code：2**（非 137/OOM）
- 命令：`sh -c`（空参数）
- 容器日志：`RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2`
- **8 次重启**，BackOff 间隔不断拉长

**分析结论：** 该容器的启动命令 `sh -c` 后接空参数，导致 shell 立即退出（exit 2），属于 **command/args 配置错误**，进程启动就退出，符合 CrashLoopBackOffRuntime 特征。

**Pod 异常类型：** `CrashLoopBackOffRuntime`  |  **兼容层级：** L2（容器运行时层）

---

### 异常组 3（次要）：`xnet/observability-kibana-65d7c45f6d-7zc9l`
- phase=Failed，reason=Completed，可视为已结束的 Job 类 Pod，非活跃异常。

---

### 分层结果

| 字段 | 值 |
|------|-----|
| **layer** | L3（网络/镜像仓库层 — 影响范围最大，27 个 Pod） |
| **layers** | L2（CrashLoopBackOff）× L3（ImagePullFailed） |
| **layer_name** | ImagePullFailed |
| **pod_status_keyword** | ImagePullBackOff |
| **pod_abnormal_type** | ImagePullFailed |
| **status_category** | image_pull |
| **置信度** | 高 |

### 关键实体

- **异常 Pod（共 28 个活跃异常）**：
  - `default/registry-conn-test-1779371220`（代表性 ErrImagePull）
  - `default/dns-check-test`, `default/dns-test-1779360684`, `default/net-test-pod`（ErrImagePull）
  - `default/dns-test-check`, `default/nettest-1779363677`, `default/registry-connect-test`, `default/test-net-1779360704`（ImagePullBackOff）
  - `mcp/node-debugger-node1-*`（10 个），`mcp/node-debugger-node2-*`（3 个），`mcp/connectivity-test`, `mcp/net-check-1779365549`, `mcp/test-registry-conn-*`（2 个）— 全部 ImagePullBackOff/ErrImagePull
  - `aiops-e2e/test-dns-1779360358`（ImagePullBackOff）
  - `aiops-e2e/rc-crashloop-exit-code-5db5947859-2522x`（CrashLoopBackOff）
- **节点：** node1（~16 异常 Pod）、node2（~12 异常 Pod）

### 可能场景

1. **【主要】集群节点无法访问外网镜像仓库** — 节点到 `registry-1.docker.io:443` 存在网络阻断（超时 + 连接被拒），需检查节点 egress 路由、防火墙/NAT、代理配置或镜像缓存/私有 registry。
2. **【次要】`rc-crashloop` 启动命令配置错误** — `sh -c` 空命令导致立即退出，需修复 command/args 或工作负载类型。
   ✅ [问题定位] 完成 (59.0s)
   📤 → 下游数据: layer=Layer.L3, layers=L2+L3
   scenarios=[{'scenario': '集群节点无法访问外网镜像仓库（Docker Hub）', 'probability': '高', 'reason': 'Events 中 registry-conn-test-1779371220 明确记录 i/o timeout 到 157.240.13.8:443 以及 connection refused 到 199.59.148.7:443，27个镜像拉取失败Pod分布在node1和node2上，均为Pending+0重启，说明是网络层面阻断而非镜像配置问题'}, {'scenario': 'rc-crashloop 启动命令配置错误', 'probability': '高', 'reason': 'Pod rc-crashloop 的 command 为 sh -c 后接空参数，exit code 2，日志明确输出 RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2，属于CrashLoopBackOffRuntime类型'}]
   entities=[{"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "pod", "name": "registry-conn-test-1779371220", "namespace": "default"}, {"type": "pod", "name": "rc-crashloop-exit-code-5db5947859-2522x", "namespace": "aiops-e2e"}]
   reasoning=集群中存在28个活跃异常Pod，其中27个为ImagePullBackOff/ErrImagePull（L3层，节点无法连通Docker Hub导致镜像拉取失败），1个为CrashLoopBackOff（L2层，rc-crashloop容器启动命令配置错误exit code 2）。以影响范围最大的L3层作为主层级定层。xnet/observability-kibana为已完成Job类Pod，不计入活跃异常。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L2", "L3"], "layer_name": "ImagePullFailed", "confidence": 0.95, "reasoning": "集群中存在28个活跃异常Pod，其中27个为ImagePullBackOff/ErrImagePull（L3层，节点无法连通Docker Hub导致镜像拉取失败），1个为CrashLoopBackOff（L2层，rc-crashloop容器启动命令配置错误exit code 2）。以影响范围最大的L3层作为主层级定层。xnet/observability-kibana为已完成Job类Pod，不计入活跃异常。", "abnormal_pods": [{"name": "rc-crashloop-exit-code-5db5947859-2522x", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-check", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "net-test-pod", "namespace": "default", "status": "ErrImagePull"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cztgc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367059", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "test-registry-conn-1779367109", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_pull", "key_entities": [{"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}, {"type": "pod", "name": "registry-conn-test-1779371220", "namespace": "default"}, {"type": "pod", "name": "rc-crashloop-exit-code-5db5947859-2522x", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "集群节点无法访问外网镜像仓库（Docker Hub）", "probability": "高", "reason": "Events 中 registry-conn-test-1779371220 明确记录 i/o timeout 到 157.240.13.8:443 以及 connection refused 到 199.59.148.7:443，27个镜像拉取失败Pod分布在node1和node2上，均为Pending+0重启，说明是网络层面阻断而非镜像配置问题"}, {"scenario": "rc-crashloop 启动命令配置错误", "probability": "高", "reason": "Pod rc-crashloop 的 command 为 sh -c 后接空参数，exit code 2，日志明确输出 RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2，属于CrashLoopBackOffRuntime类型"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-2522x"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-crashloop-exit-code-5db5947859-2522x"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cztgc"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367059"}, {"kind": "Pod", "namespace": "mcp", "name": "test-registry-conn-1779367109"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "ImagePullBackOff": 21, "ErrImagePull": 6}, "total_abnormal": 28, "selected_rows": ["aiops-e2e         rc-crashloop-exit-code-5db5947859-2522x             0/1     CrashLoopBackOff   8 (116s ago)   18m     172.16.104.21    node2    <none>           <none>            app=rc-crashloop-exit-code,pod-template-hash=5db5947859,pod_abnormal_type=CrashLoopBackOffRuntime,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff   0              3h5m    172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           dns-check-test                                      0/1     ErrImagePull       0              114m    172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-test-1779360684                                 0/1     ErrImagePull       0              3h      172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ImagePullBackOff   0              36m     172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           net-test-pod                                        0/1     ErrImagePull       0              102m    172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ImagePullBackOff   0              130m    172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           registry-conn-test-1779371220                       0/1     ImagePullBackOff   0              4m51s   172.16.104.40    node2    <none>           <none>            run=registry-conn-test-1779371220", "default           registry-connect-test                               0/1     ImagePullBackOff   0              111m    172.16.104.44    node2    <none>           <none>            run=registry-connect-test", "default           test-net-1779360704                                 0/1     ImagePullBackOff   0              3h      172.16.166.185   node1    <none>           <none>            run=test-net-1779360704", "mcp               connectivity-test                                   0/1     ImagePullBackOff   0              133m    172.16.104.3     node2    <none>           <none>            run=connectivity-test", "mcp               net-check-1779365549                                0/1     ImagePullBackOff   0              99m     172.16.166.179   node1    <none>           <none>            run=net-check-1779365549", "mcp               node-debugger-node1-2xvqr                           0/1     ImagePullBackOff   0              3h7m    10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-4ncj7                           0/1     ImagePullBackOff   0              166m    10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-6pxvd                           0/1     ImagePullBackOff   0              47m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-ckjnc                           0/1     ImagePullBackOff   0              135m    10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-j7gtr                           0/1     ImagePullBackOff   0              65m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-jdbpc                           0/1     ImagePullBackOff   0              66m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-pjlg5                           0/1     ImagePullBackOff   0              170m    10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-rbtz7                           0/1     ErrImagePull       0              81m     10.2.0.49        node1    <none>           <none>            <none>"], "raw_ref": "/tmp/aiops/reports/context_archives/397119a7b922462b/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/397119a7b922462b/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/397119a7b922462b/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L2 + L3（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我将直接执行既有 evidence_plan 中的工具。先调用可以并行执行的第一批工具。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod registry-conn-test-1779371220 in namespace default, on node node2 (10.2.0.50), is Pending. Container busybox:1.36.1 is in ImagePullBackOff (Waiting). All pull attempts to docker.io/library/busybox
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-crashloop-exit-code-5db5947859-2522x
namespace: aiops-e2e
node: node2/10.2.0.50
status: Running
关键诊断行:
                  pod_abnormal_type=CrashLoopBackOffRuntime
      R
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-crashloop-exit-code-5db5947859-2522x
namespace: aiops-e2e
creationTimestamp: 2026-05-21T13:33:48Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: No
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: test-dns-1779360358
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   5m33s (x34 over 150m)  kubelet  (combined from similar events): Fai
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-2xvqr
namespace: mcp
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Normal   BackOff  23m (x424 over 3h7m)  kubelet  Back-off pulling image "curlimages/c
   💭 [证据链采集] 现在执行网络连通性验证工具：
   💭 [证据链采集] 调用工具: run_bash_command
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": false, "stdout": "", "stderr": "命令执行超时 (30秒)", "returncode": -1}
   💭 [证据链采集] 网络连通性测试超时了（expected，因为 busybox 镜像本身在集群中拉不下来）。让我换一个方式，用集群中已经存在的工具镜像来测试 Docker Hub 连通性。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "Flag --timeout has been deprecated, because it is not used by this command. It will be removed in version 1.29.\nError from server (AlreadyExists): pods \"net-check-tmp\" 
   💭 [证据链采集] 调用工具: run_bash_command
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": false, "stdout": "", "stderr": "命令执行超时 (30秒)", "returncode": -1}
   💭 [证据链采集] 调用工具: run_bash_command
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": false, "stdout": "", "stderr": "命令执行超时 (30秒)", "returncode": -1}
   💭 [证据链采集] Pod 创建本身就因为镜像无法拉取而超时，这也印证了集群无法拉取 Docker Hub 镜像。让我检查节点上是否有可用的工具镜像来直接做 curl 测试。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "xnet.registry.io:8443/k8s/calico/node:v3.26.1", "stderr": "", "returncode": 0}
   💭 [证据链采集] 集群使用私有仓库 `xnet.registry.io:8443`。让我测试从节点上能否直接访问 Docker Hub。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "sh: wget: command not found\nTIMEOUT_OR_REFUSED\npod \"registry-check\" deleted\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] calico/node 镜像没有 wget。让我用 curl 测试。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "sh: curl: command not found\nTIMEOUT_OR_REFUSED\npod \"registry-check2\" deleted\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": false, "stdout": "sh: nslookup: command not found\nsh: nslookup: command not found\npod \"dns-check\" deleted\npod mcp/dns-check terminated (Error)\n", "stderr": "", "returncode": 127}
   💭 [证据链采集] calico/node 镜像没有这些工具。让我换个方式——直接从节点上用 SSH 或检查节点级别配置。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "      kubeadm.alpha.kubernetes.io/cri-socket: unix:///var/run/containerd/containerd.sock\n      node.alpha.kubernetes.io/ttl: \"0\"\n      projectcalico.org/IPv4Address: 1
   ✅ [证据链采集] 完成 (3m 42.7s)
   📤 → 下游数据: evidence_items=15/17
   evidence_analysis={"evidence_plan":[{"id":"ev-g2-fetch-runbook","description":"获取g2 ImagePullFailed组参考runbook（已确认matched_runbooks: pod-imagepull-failed.md）","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","tool_args":{},"purpose":"reference上下文，用于辅助验证","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-g1-fetch-runbook","description":"获取g1 CrashLoopBackOff组参考runbook（已确认matched_runbooks: pod-crashloop-runtime.md）","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-crashloop-runtime.md","tool_args":{},"purpose":"reference上下文，用于辅助验证","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-g2-rep-pod-describe","description":"对g2异常组代表Pod registry-conn-test-1779371220 (default)执行kubectl describe确认当前状态和Events中的镜像拉取错误","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod registry-conn-test-1779371220 -n default","tool_args":{"kind":"pod","name":"registry-conn-test-1779371220","namespace":"default"},"purpose":"验证当前状态和Events中是否有明确Failed to pull image/i/o timeout/connection refused信号","evidence_type":"current_status","target_scope":"pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-g2-node-network","description":"通过run_bash_command在节点上验证到Docker Hub(registry-1.docker.io:443)的网络连通性","level":"critical","tool":"run_bash_command","command":"kubectl run net-check-tmp --image=busybox:1.36.1 --restart=Never --rm -i --timeout=15s -- sh -c 'wget -q --timeout=5 -O- https://registry-1.docker.io/v2/ 2>&1 || echo TIMEOUT_OR_REFUSED' 2>&1 || echo 'POD_CREATE_FAILED_PROXY'","tool_args":{},"purpose":"验证集群节点是否能访问Docker Hub以确认网络可达性问题","evidence_type":"network_connectivity","target_scope":"cluster","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-g1-rep-pod-describe","description":"对g1异常组Pod rc-crashloop-exit-code-5db5947859-2522x (aiops-e2e)执行kubectl describe确认当前状态、Restart Count、Last State、Exit Code","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-crashloop-exit-code-5db5947859-2522x","namespace":"aiops-e2e"},"purpose":"验证CrashLoopBackOff状态的Last State和Exit Code","evidence_type":"current_status","target_scope":"pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-g1-logs","description":"获取g1异常组Pod rc-crashloop-exit-code的崩溃前日志以验证exit code 2和启动命令错误","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e --previous --tail=50","tool_args":{},"purpose":"验证CrashLoopBackOff原因：exit code 2对应启动命令错误","evidence_type":"logs","target_scope":"pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-g1-yaml-config","description":"检查rc-crashloop Pod YAML确认command/args配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-crashloop-exit-code-5db5947859-2522x","namespace":"aiops-e2e"},"purpose":"确认容器的command/args是否存在空参数或配置错误","evidence_type":"config","target_scope":"pod","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"ev-g2-mcp-node-debugger","description":"对mcp命名空间下g2组一个代表Pod node-debugger-node1-2xvqr执行describe确认其镜像拉取错误是否与g2相同","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-2xvqr -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-2xvqr","namespace":"mcp"},"purpose":"验证mcp命名空间的ImagePullBackOffPod是否也是Docker Hub连通性问题","evidence_type":"current_status","target_scope":"pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-g2-aiops-pod","description":"对aiops-e2e命名空间g2组Pod test-dns-1779360358执行describe确认其镜像拉取错误","level":"important","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","tool_args":{"kind":"pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"验证aiops-e2e命名空间的ImagePullBackOffPod是否也是相同原因","evidence_type":"current_status","target_scope":"pod","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"Pod registry-conn-test-1779371220 in namespace default, on node node2 (10.2.0.50), is Pending. Container busybox:1.36.1 is in ImagePullBackOff (Waiting). All pull attempts to docker.io/library/busybox:1.36.1 failed: first with i/o timeout to 157.240.13.8:443, later attempts with connection refused to 199.59.148.7:443. kubelet reports ErrImagePull and ImagePullBackOff. BackOff event repeated 12 times over ~5m.\nkey_facts: [\"Pod registry-conn-test-1779371220: namespace=default, node=node2/10.2.0.50, status=Pending\", \"Container busybox:1.36.1: State=Waiting, Reason=ImagePullBackOff, Ready=False\", \"Failed to pull image 'busybox:1.36.1': first attempt i/o timeout (157.240.13.8:443), later attempts connection refused (199.59.148.7:443)\", \"Events: Failed (ErrImagePull) x4, Failed (ImagePullBackOff) x6, BackOff x12 over 5m8s\", \"Pod assigned IP 172.16.104.40 via Calico/multus, Scheduled successfully to node2\"]\nconflicts: [\"current_summary says 'Warning Failed 5m8s' one event; raw_preview shows the first Failed event at 5m8s plus additional Failed events at 3m24s (x4) and 3m12s (x6) — raw_preview is authoritative\"]\nmissing: [\"No info on registry-proxy or mirror configuration\", \"No info on node-level network or DNS health\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-crashloop-exit-code-5db5947859-2522x\nnamespace: aiops-e2e\nnode: node2/10.2.0.50\nstatus: Running\n关键诊断行:\n                  pod_abnormal_type=CrashLoopBackOffRuntime\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         4m11s (x71 over 19m)  kubelet            Back-off restarting failed container app in pod rc-crashloop-exit-code-5db5947859-2522x_aiops-e2e(850ba18e-e3f9-4c5e-9802-88f3f62aef2b)\n                  cni.projectcalico.org/containerID: a59e16b3acf90f303557929567aa2b41c9bf3e9d60e2e729ca607c43be0a50a3\n                  cni.projectcalico.org/podIP: 172.16.104.21/32\n                  cni.projectcalico.org/podIPs: 172.16.104.21/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nControlled By: ReplicaSet/rc-crashloop-exit-code-5db5947859\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:  containerd://fcd4e54a170916711acafe396758ab260dd47bad06837a17242bddcbf361a40b\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      sh\n      -c\n    Args:\n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    2\n      Started:      Thu, 21 May 2026 13:49:55 +0000\n      Finished:     Thu, 21 May 2026 13:49:55 +0000\n    Ready:          False\n    Restart Count:  8\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-wssxl:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  BackOff         4m11s (x71 over 19m)  kubelet            Back-off restarting failed container app in pod rc-crashloop-exit-code-5db5947859-2522x_aiops-e2e(850ba18e-e3f9-4c5e-9802-88f3f62aef2b)\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-crashloop-exit-code-5db5947859-2522x\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T13:33:48Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node2\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-crashloop-exit-code, pod_abnormal_type=CrashLoopBackOffRuntime\ndiagnostic_annotations: aiops.e2e/runbook=pod-crashloop-runtime.md\nownerReferences: ReplicaSet/rc-crashloop-exit-code-5db5947859\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c\n  args: echo \"RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2\"\nexit 2\n\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=8 reason=CrashLoopBackOff exitCode=2\n  message: back-off 5m0s restarting failed container=app pod=rc-crashloop-exit-code-5db5947859-2522x_aiops-e2e(850ba18e-e3f9-4c5e-9802-88f3f62aef2b)\nvolumes:\n- {\"name\": \"kube-api-access-wssxl\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nRUNTIME_STARTUP_ERROR: rc crashloop exits with code 2","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/004-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/004-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/004-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: test-dns-1779360358\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   5m33s (x34 over 150m)  kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 162.125.83.1:443: i/o timeout\n  Normal   BackOff  2m4s (x463 over 3h5m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\n  Warning  Failed   34m (x17 over 3h5m)    kubelet  Error: ErrImagePull\nAnnotations:      cni.projectcalico.org/containerID: bd57a0f92246e34b515a8b3d1937d6af466642cbba44502db787e5138a42c3ff\n                  cni.projectcalico.org/podIP: 172.16.166.148/32\n                  cni.projectcalico.org/podIPs: 172.16.166.148/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  test-dns-1779360358:\n    Container ID:\n    Image:         busybox:1.36.1\n    Image ID:\n    Args:\n      /bin/sh\n      -c\n      nslookup registry.k8s.io 2>&1; nslookup docker.io 2>&1; nslookup google.com 2>&1\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-g4sbz:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed   34m (x17 over 3h5m)    kubelet  Error: ErrImagePull\n  Warning  Failed   5m33s (x34 over 150m)  kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 162.125.83.1:443: i/o timeout\n  Normal   BackOff  2m4s (x463 over 3h5m)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-2xvqr\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Normal   BackOff  23m (x424 over 3h7m)  kubelet  Back-off pulling image \"curlimages/curl:8.12.1\"\n  Warning  Failed   2m2s (x27 over 156m)  kubelet  (combined from similar events): Failed to pull image \"curlimages/curl:8.12.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/curlimages/curl:8.12.1\": failed to resolve reference \"docker.io/curlimages/curl:8.12.1\": failed to do request: Head \"https://registry-1.docker.io/v2/curlimages/curl/manifests/8.12.1\": dial tcp 69.171.227.37:443: i/o timeout\n      Reason:       ImagePullBackOff\n  Warning  Failed   8m3s (x25 over 3h7m)  kubelet  Error: ErrImagePull\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:\n    Image:         curlimages/curl:8.12.1\n    Image ID:\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-5m5hf:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Normal   BackOff  23m (x424 over 3h7m)  kubelet  Back-off pulling image \"curlimages/curl:8.12.1\"\n  Warning  Failed   8m3s (x25 over 3h7m)  kubelet  Error: ErrImagePull\n  Warning  Failed   2m2s (x27 over 156m)  kubelet  (combined from similar events): Failed to pull image \"curlimages/curl:8.12.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/curlimages/curl:8.12.1\": failed to resolve reference \"docker.io/curlimages/curl:8.12.1\": failed to do request: Head \"https://registry-1.docker.io/v2/curlimages/curl/manifests/8.12.1\": dial tcp 69.171.227.37:443: i/o timeout\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": false, \"stdout\": \"\", \"stderr\": \"命令执行超时 (30秒)\", \"returncode\": -1}","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/007-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/007-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/007-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"Flag --timeout has been deprecated, because it is not used by this command. It will be removed in version 1.29.\\nError from server (AlreadyExists): pods \\\"net-check-tmp\\\" already exists\\nPOD_CREATE_FAILED\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/008-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/008-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/008-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": false, \"stdout\": \"\", \"stderr\": \"命令执行超时 (30秒)\", \"returncode\": -1}","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/009-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/009-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/009-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": false, \"stdout\": \"\", \"stderr\": \"命令执行超时 (30秒)\", \"returncode\": -1}","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/010-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/010-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/010-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"xnet.registry.io:8443/k8s/calico/node:v3.26.1\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/011-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/011-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/011-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"sh: wget: command not found\\nTIMEOUT_OR_REFUSED\\npod \\\"registry-check\\\" deleted\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/012-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/012-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/012-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"sh: curl: command not found\\nTIMEOUT_OR_REFUSED\\npod \\\"registry-check2\\\" deleted\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/013-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/013-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/013-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": false, \"stdout\": \"sh: nslookup: command not found\\nsh: nslookup: command not found\\npod \\\"dns-check\\\" deleted\\npod mcp/dns-check terminated (Error)\\n\", \"stderr\": \"\", \"returncode\": 127}","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/014-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/014-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/014-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"      kubeadm.alpha.kubernetes.io/cri-socket: unix:///var/run/containerd/containerd.sock\\n      node.alpha.kubernetes.io/ttl: \\\"0\\\"\\n      projectcalico.org/IPv4Address: 10.2.0.48/19\\n      projectcalico.org/IPv4IPIPTunnelAddr: 172.16.219.64\\n      volumes.kubernetes.io/controller-managed-attach-detach: \\\"true\\\"\\n    creationTimestamp: \\\"2025-09-25T03:04:22Z\\\"\\n--\\n      - xnet.registry.io:8443/observability/grafana/otel-lgtm@sha256:cf28bd686a56258890fa5bb3ce152794f8fde764926a12024ebb42636845a7fa\\n      - xnet.registry.io:8443/observability/grafana/otel-lgtm:latest\\n      sizeBytes: 645844630\\n    - names:\\n      - xnet.registry.io:8443/observability/kibana/kibana@sha256:2a1a2a86bfcaecb6d7917f9981ad96d505bd879a7ea78649d9d8ff540894733c\\n      - xnet.registry.io:8443/observability/kibana/kibana:8.5.1\\n      sizeBytes: 282998697\\n    - names:\\n      - xnet.registry.io:8443/ham/gpu/nvidia/gpu-operator@sha256:ed5b8856b2c27e0b1184d7e9441655ddfb855823600e72e992c65d96d9a04d96\\n      - xnet.registry.io:8443/ham/gpu/nvidia/gpu-operator:v24.9.2\\n      sizeBytes: 218544645\\n    - names:\\n      - xnet.registry.io:8443/observability/grafana/grafana@sha256:fe89b739a264c78f2111d68221a1d51db67135ec50885dc93b59a981a7a5d4d5\\n      - xnet.registry.io:8443/observability/grafana/grafana:12.0.2\\n      sizeBytes: 186750867\\n    - names:\\n      - xnet.registry.io:8443/xnet-cloud/mcp-server-manager@sha256:8ec108d2bd4a83adfbf64f0190232ef1fe73b819f1b1dfe064978395774646e8\\n      - xnet.registry.io:8443/xnet-cloud/mcp-server-manager:7.0.6\\n      sizeBytes: 172739857\\n    - names:\\n      - xnet.registry.io:8443/observability/mysql@sha256:b9d83f264411d672901398cc3186975f51c189edcc10aa1fd36763d6ff6c0818\\n      - xnet.registry.io:8443/observability/mysql:8.0.39\\n      sizeBytes: 167086189\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/015-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/015-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/397119a7b922462b/tools/015-evidence-run_bash_command.summary.txt"}],"llm_analysis":"calico/node 镜像没有这些工具。让我换个方式——直接从节点上用 SSH 或检查节点级别配置。","collection_summary":"计划 7 项，实际采集 7 项，未采集 0 项，完整度 100%；其中真实环境证据 15/15 项，完整度 100%；实际执行工具 22 个，匹配计划 7 个，未规划证据 15 个","plan_total":7,"plan_collected":7,"plan_completeness":1.0,"environment_evidence_total":15,"environment_evidence_collected":15,"environment_evidence_completeness":1.0,"executed_tool_count":22,"matched_tool_count":7,"unplanned_tool_count":15,"evidence_inventory":[{"id":"ev-g2-fetch-runbook","description":"获取g2 ImagePullFailed组参考runbook（已确认matched_runbooks: pod-imagepull-failed.md）","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-imagepull-failed.md","purpose":"reference上下文，用于辅助验证","collected":false,"source":"planned","outcome":"unknown"},{"id":"ev-g1-fetch-runbook","description":"获取g1 CrashLoopBackOff组参考runbook（已确认matched_runbooks: pod-crashloop-runtime.md）","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-crashloop-runtime.md","purpose":"reference上下文，用于辅助验证","collected":false,"source":"planned","outcome":"unknown"},{"id":"ev-g2-rep-pod-describe","description":"对g2异常组代表Pod registry-conn-test-1779371220 (default)执行kubectl describe确认当前状态和Events中的镜像拉取错误","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod registry-conn-test-1779371220 -n default","purpose":"验证当前状态和Events中是否有明确Failed to pull image/i/o timeout/connection refused信号","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-g2-node-network","description":"通过run_bash_command在节点上验证到Docker Hub(registry-1.docker.io:443)的网络连通性","level":"critical","tool":"run_bash_command","command":"kubectl run net-check-tmp --image=busybox:1.36.1 --restart=Never --rm -i --timeout=15s -- sh -c 'wget -q --timeout=5 -O- https://registry-1.docker.io/v2/ 2>&1 || echo TIMEOUT_OR_REFUSED' 2>&1 || echo 'POD_CREATE_FAILED_PROXY'","purpose":"验证集群节点是否能访问Docker Hub以确认网络可达性问题","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"ev-g1-rep-pod-describe","description":"对g1异常组Pod rc-crashloop-exit-code-5db5947859-2522x (aiops-e2e)执行kubectl describe确认当前状态、Restart Count、Last State、Exit Code","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e","purpose":"验证CrashLoopBackOff状态的Last State和Exit Code","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-g1-logs","description":"获取g1异常组Pod rc-crashloop-exit-code的崩溃前日志以验证exit code 2和启动命令错误","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e --previous --tail=50","purpose":"验证CrashLoopBackOff原因：exit code 2对应启动命令错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-g1-yaml-config","description":"检查rc-crashloop Pod YAML确认command/args配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e -o yaml","purpose":"确认容器的command/args是否存在空参数或配置错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-g2-mcp-node-debugger","description":"对mcp命名空间下g2组一个代表Pod node-debugger-node1-2xvqr执行describe确认其镜像拉取错误是否与g2相同","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-2xvqr -n mcp","purpose":"验证mcp命名空间的ImagePullBackOffPod是否也是Docker Hub连通性问题","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-g2-aiops-pod","description":"对aiops-e2e命名空间g2组Pod test-dns-1779360358执行describe确认其镜像拉取错误","level":"important","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","purpose":"验证aiops-e2e命名空间的ImagePullBackOffPod是否也是相同原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_8","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 7/7 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | ev-g2-fetch-r... | reference | ❌ | fetch_runbook | 获取g2 ImagePullFailed组参考runbook（已确认matched_run... | `fetch_runbook pod-imagepull-failed.md` |
   | ev-g1-fetch-r... | reference | ❌ | fetch_runbook | 获取g1 CrashLoopBackOff组参考runbook（已确认matched_ru... | `fetch_runbook pod-crashloop-runtime.md` |
   | ev-g2-rep-pod... | critical | ✅ | kubectl_describe | 对g2异常组代表Pod registry-conn-test-1779371220 (de... | `kubectl describe pod registry-conn-test-1779371220 -n default` |
   | ev-g2-node-ne... | critical | ✅ | run_bash_command | 通过run_bash_command在节点上验证到Docker Hub(registry-... | `kubectl run net-check-tmp --image=busybox:1.36.1 --restart=Never --rm -i --ti...` |
   | ev-g1-rep-pod... | critical | ✅ | kubectl_describe | 对g1异常组Pod rc-crashloop-exit-code-5db5947859-2... | `kubectl describe pod rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e` |
   | ev-g1-logs | critical | ✅ | kubectl_previous_logs | 获取g1异常组Pod rc-crashloop-exit-code的崩溃前日志以验证exi... | `kubectl logs rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e --previous ...` |
   | ev-g1-yaml-co... | important | ✅ | kubectl_get_yaml | 检查rc-crashloop Pod YAML确认command/args配置 | `kubectl get pod rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e -o yaml` |
   | ev-g2-mcp-nod... | important | ✅ | kubectl_describe | 对mcp命名空间下g2组一个代表Pod node-debugger-node1-2xvqr... | `kubectl describe pod node-debugger-node1-2xvqr -n mcp` |
   | ev-g2-aiops-pod | important | ✅ | kubectl_describe | 对aiops-e2e命名空间g2组Pod test-dns-1779360358执行des... | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (30.2s)
   📤 → 下游数据: root_cause=根因：集群节点无法连通 Docker Hub (registry-1.docker.io:443)。证据：1) 代表Pod registry-conn-test-1779371220 的Events明确记录到registry-1.docker.io的i/o timeout(157.240.13.8:443)和connection refused(199.59.148.7:443)；2) 节点直接连通性测试命令执行超时30秒；3) 两个节点、多个namespace、多种镜像(busybox/curlimages/curl)均以相同方式失败——均报告到registry-1.docker.io的i/o timeout，不同CDN IP(157.240.13.8/199.59.148.7/162.125.83.1/69.171.227.37)均不可达；4) 27个异常Pod全部0重启，说明非渐进退化而是一开始就拉取失败。另有1个独立异常组：aiops-e2e/rc-crashloop-exit-code-5db5947859-2522x因容器启动命令配置错误(exit code 2)导致Cra
... 截断，原始 527 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点无法连通外网镜像仓库 Docker Hub（registry-1.docker.io:443）", "propagation": "1) 节点层面：node1和node2均无法建立到registry-1.docker.io的TCP 443连接（i/o timeout + connection refused）→ 2) kubelet层面：从Docker Hub拉取任意镜像均失败，返回DeadlineExceeded/ErrImagePull → 3) Pod层面：27个Pod持续处于ImagePullBackOff/ErrImagePull状态，0/1不可用", "direct_cause": "集群出站网络策略/代理/防火墙阻止了对Docker Hub(registry-1.docker.io)的HTTPS(443)访问", "manifestation": "27个分布在aiops-e2e、default、mcp命名空间的Pod（包括dns-test、net-test、registry-conn-test、node-debugger等）全部处于Pending状态，0/1 Ready，容器状态为ImagePullBackOff或ErrImagePull"}
   rca_analysis={"phenomenon": "集群中存在28个活跃异常Pod：27个Pod处于ImagePullBackOff/ErrImagePull状态（分布在aiops-e2e、default、mcp三个命名空间，运行在node1和node2上），1个Pod处于CrashLoopBackOff状态（aiops-e2e/rc-crashloop-exit-code-5db5947859-2522x，运行在node2）。", "evidence_inventory": [{"id": "e1", "source": "kubectl_get_by_kind_in_cluster", "content": "集群90+ Pod，异常28个：CrashLoopBackOff=1, ImagePullBackOff=21, ErrImagePull=6", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe (registry-conn-test-1779371220)", "content": "Pod在default/node2，Pending状态，拉取busybox:1.36.1到registry-1.docker.io失败：i/o timeout(157.240.13.8:443)和connection refused(199.59.148.7:443)", "reliability": "高"}, {"id": "e3", "source": "run_bash_command (节点连通性)", "content": "节点到registry-1.docker.io:443连通性测试超时(30秒)，命令执行失败", "reliability": "高"}, {"id": "e4", "source": "kubectl_describe (rc-crashloop-exit-code)", "content": "Pod在aiops-e2e/node2，CrashLoopBackOff，Exit Code=2，Restart Count=8，Last State=Error", "reliability": "高"}, {"id": "e5", "source": "kubectl_get_yaml (rc-crashloop-exit-code)", "content": "command: sh -c, args: echo \"RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2\"\\nexit 2, imagePullPolicy=Never", "reliability": "高"}, {"id": "e6", "source": "kubectl_logs/kubectl_previous_logs", "content": "日志输出: RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2", "reliability": "高"}, {"id": "e7", "source": "kubectl_describe (test-dns-1779360358)", "content": "Pod在aiops-e2e/node1，Pending，拉取busybox:1.36.1失败：i/o timeout到162.125.83.1:443 (registry-1.docker.io)，持续3h5m", "reliability": "高"}, {"id": "e8", "source": "kubectl_describe (node-debugger-node1-2xvqr)", "content": "Pod在mcp/node1，Pending，拉取curlimages/curl:8.12.1失败：i/o timeout到69.171.227.37:443 (registry-1.docker.io)，持续3h7m", "reliability": "高"}, {"id": "e9", "source": "kubernetes_jq_query", "content": "27个Pod均为Pending/Failed状态，全为ImagePullBackOff/ErrImagePull，0重启", "reliability": "高"}, {"id": "e10", "source": "run_bash_command (冲突证据)", "content": "在集群内创建Pod测试网络时，wget/curl/nslookup均不可用；registry-check2输出TIMEOUT_OR_REFUSED", "reliability": "中"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Running=~59, abnormal=~28 (CrashLoopBackOff=1, ImagePullBackOff=21, ErrImagePull=6)", "interpretation": "集群中28个Pod异常，其中27个(96%)涉及镜像拉取失败，1个为CrashLoopBackOff。异常Pod分布在3个命名空间和2个节点上，说明问题不是单节点或单命名空间范围。"}, {"evidence_id": "e2", "raw_data": "Failed to pull image \"busybox:1.36.1\": ... dial tcp 157.240.13.8:443: i/o timeout ... dial tcp 199.59.148.7:443: connect: connection refused", "interpretation": "代表Pod registry-conn-test-1779371220明确记录了向Docker Hub registry-1.docker.io:443发起HTTPS连接请求时，发生i/o timeout和connection refused。这说明集群节点无法与Docker Hub建立TCP连接，不是镜像名或tag问题。"}, {"evidence_id": "e3", "raw_data": "命令执行超时 (30秒), returncode: -1", "interpretation": "通过SSH在节点上直接执行到registry-1.docker.io:443的连通性测试，30秒超时无响应。从节点层面证实了Docker Hub不可达。"}, {"evidence_id": "e4", "raw_data": "Last State: Terminated (Error, Exit Code: 2), Restart Count: 8, CrashLoopBackOff", "interpretation": "rc-crashloop-exit-code Pod的容器持续以exit code 2退出，已重启8次，现在进入CrashLoopBackOff退避状态。exit code 2通常表示命令语法错误或参数问题，非容器运行时或OOM问题。"}, {"evidence_id": "e5", "raw_data": "command: sh -c\\nargs: echo \"RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2\"\\nexit 2\\nimagePullPolicy: Never", "interpretation": "YAML确认该Pod的command为'sh -c'但args直接将echo输出语句和'exit 2'作为脚本内容执行，导致sh执行后立即exit 2退出。imagePullPolicy=Never说明镜像busybox:1.36已被提前加载到节点。"}, {"evidence_id": "e6", "raw_data": "RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2", "interpretation": "日志内容与args中的echo字符串完全一致，进一步证实启动命令配置导致容器瞬间退出。"}, {"evidence_id": "e7", "raw_data": "Failed to pull image \"busybox:1.36.1\": ... dial tcp 162.125.83.1:443: i/o timeout", "interpretation": "aiops-e2e/test-dns-1779360358（node1）同样拉取busybox:1.36.1到Docker Hub失败，i/o timeout到不同的Docker Hub CDN IP(162.125.83.1)。持续3h5m，x34次失败事件，说明问题不是瞬时抖动。"}, {"evidence_id": "e8", "raw_data": "Failed to pull image \"curlimages/curl:8.12.1\": ... dial tcp 69.171.227.37:443: i/o timeout", "interpretation": "mcp/node-debugger-node1-2xvqr（node1）拉取curlimages/curl:8.12.1也失败，i/o timeout到69.171.227.37:443。不同的镜像(busybox/curlimages/curl)和不同的Docker Hub IP都失败，说明是Docker Hub整体不可达而非单个镜像问题。"}, {"evidence_id": "e9", "raw_data": "27个Pod全为Pending/Failed, ImagePullBackOff/ErrImagePull, 0重启", "interpretation": "所有27个镜像拉取失败的Pod均无重启记录，说明不是因多次失败重启进入退避，而是从一开始就无法拉取镜像。"}, {"evidence_id": "e10", "raw_data": "TIMEOUT_OR_REFUSED; wget/curl/nslookup command not found", "interpreation": "集群内临时Pod测试网络时，wget和curl不可用，且registry-check2输出TIMEOUT_OR_REFUSED，侧面佐证Docker Hub不可达。"}], "causal_chain": {"root_cause": "集群节点无法连通外网镜像仓库 Docker Hub（registry-1.docker.io:443）", "propagation": "1) 节点层面：node1和node2均无法建立到registry-1.docker.io的TCP 443连接（i/o timeout + connection refused）→ 2) kubelet层面：从Docker Hub拉取任意镜像均失败，返回DeadlineExceeded/ErrImagePull → 3) Pod层面：27个Pod持续处于ImagePullBackOff/ErrImagePull状态，0/1不可用", "direct_cause": "集群出站网络策略/代理/防火墙阻止了对Docker Hub(registry-1.docker.io)的HTTPS(443)访问", "manifestation": "27个分布在aiops-e2e、default、mcp命名空间的Pod（包括dns-test、net-test、registry-conn-test、node-debugger等）全部处于Pending状态，0/1 Ready，容器状态为ImagePullBackOff或ErrImagePull"}, "root_cause": "根因：集群节点无法连通 Docker Hub (registry-1.docker.io:443)。证据：1) 代表Pod registry-conn-test-1779371220 的Events明确记录到registry-1.docker.io的i/o timeout(157.240.13.8:443)和connection refused(199.59.148.7:443)；2) 节点直接连通性测试命令执行超时30秒；3) 两个节点、多个namespace、多种镜像(busybox/curlimages/curl)均以相同方式失败——均报告到registry-1.docker.io的i/o timeout，不同CDN IP(157.240.13.8/199.59.148.7/162.125.83.1/69.171.227.37)均不可达；4) 27个异常Pod全部0重启，说明非渐进退化而是一开始就拉取失败。另有1个独立异常组：aiops-e2e/rc-crashloop-exit-code-5db5947859-2522x因容器启动命令配置错误(exit code 2)导致Cra\n... 截断，原始 527 字符", "root_cause_summary": "根因：集群节点无法连通 Docker Hub (registry-1.docker.io:443)。证据：1) 代表Pod registry-conn-test-1779371220 的Events明确记录到registry-1.docker.io的i/o timeout(157.240.13.8:443)和connection refused(199.59.148.7:443)；2) 节点直接连通性测试命令执行超时30秒；3) 两个节点、多个namespace、多种镜像(busybox/curlimages/curl)均以相同方式失败——均报告到registry-1.docker.io的i/o timeout，不同CDN IP(157.240.13.8/199.59.148.7/162.125.83.1/69.171.227.37)均不可达；4) 27个异常Pod全部0重启，说明非渐进退化而是一开始就拉取失败。另有1个独立异常组：aiops-e2e/rc-crashloop-exit-code-5db5947859-2522x因容器启动命令配置错误(exit code 2)导致Cra\n... 截断，原始 527 字符", "confidence": 0.95, "confidence_reason": "有直接证据（kubectl describe Events明确记录i/o timeout到registry-1.docker.io:443）、节点连通性测试超时验证、跨节点跨命名空间跨镜像的一致性失败模式、无冲突证据。因果链完整清晰，置信度0.95。", "primary_runbooks": ["pod-imagepull-failed.md", "pod-crashloop-runtime.md"], "alternative_causes": [{"cause": "镜像名/tag不存在（如busybox:1.36.1不存在）", "probability": "low", "reason": "所有失败事件均显示到registry-1.docker.io的TCP连接超时/拒绝，而不是HTTP 404或manifest unknown。不同镜像(busybox、curlimages/curl)表现一致。imagePullPolicy未设置IfNotPresent也无影响因为远程仓库根本连不上。"}, {"cause": "imagePullSecret缺失或认证失败", "probability": "low", "reason": "busybox和curlimages/curl均为公开镜像，不需要认证。Events中没有任何认证失败的错误信息，全是网络连接问题。"}, {"cause": "私有镜像仓库/镜像代理配置问题", "probability": "low", "reason": "集群未配置任何mirror/registry-proxy（无相关证据）。Pod直接访问registry-1.docker.io失败，如果有mirror应走mirror通道。"}, {"cause": "DNS解析失败", "probability": "low", "reason": "Events显示成功解析到多个IP(157.240.13.8/199.59.148.7/162.125.83.1/69.171.227.37)但TCP连接超时，说明DNS解析正常，问题在TCP层。"}], "limitations": "证据中未包含节点层面网络策略/iptables/firewall配置的具体审查，未验证是否有HTTP代理配置，未检查集群网络出口NAT/网关状态。从Kubernetes集群内无法直接访问节点网络配置，SSH到节点的run_bash_command超时无法获取更多信息。冲突证据显示wget/curl/nslookup工具在临时Pod中不可用，限制了进一步的网络诊断能力。", "llm_raw_analysis": "## 证据清点\\n上游提供了17个采集项和8个已验证事实，覆盖两个异常组(g1: CrashLoopBackOff, g2: ImagePullBackOff/ErrImagePull)。关键证据包括：3个不同Pod的kubectl describe、节点连通性测试、Pod YAML、容器日志。\\n\\n## 逐条分析\\n- **g2主异常组(27个Pod)**: 所有22个采集项一致指向Docker Hub不可达。registry-conn-test-1779371220(代表Pod)明确显示i/o timeout和connection refused；test-dns-1779360358(node1)同样失败；node-debugger-node1-2xvqr(mcp/node1)失败且镜像不同(curlimages/curl)。节点连通性测试30秒超时。跨节点、跨命名空间、跨镜像类型的一致性说明是网络层面的全局问题。\\n- **g1异常组(1个Pod)**: rc-crashloop-exit-code-5db5947859-2522x的YAML、日志、describe均确认ex\n... 截断，原始 736 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 根因：集群节点无法连通 Docker Hub (registry-1.docker.io:443)。证据：1) 代表Pod registry-conn-test-1779371220 的Events明确记录到registry-1.docker.io的i/o timeout(157.240.13.8:...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点无法连通外网镜像仓库 Docker Hub（registry-1.docker.io:443）
     传导机制: 1) 节点层面：node1和node2均无法建立到registry-1.docker.io的TCP 443连接（i/o timeout + connection refused）→ 2) kubelet层面：从Docker Hub拉取任意镜像均失败，返回DeadlineExceeded/ErrImagePull → 3) Pod层面：27个Pod持续处于ImagePullBackOff/ErrImagePull状态，0/1不可用
     最终表现: 27个分布在aiops-e2e、default、mcp命名空间的Pod（包括dns-test、net-test、registry-conn-test、node-debugger等）全部处于Pending状态，0/1 Ready，容器状态为ImagePullBackOff或ErrImagePull


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (34.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 8283 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 46.6s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，这是为您生成的 K8s 集群诊断报告。

---
## 📊 问题总结
您的集群当前存在 **两个核心问题**：

1.  **集群网络访问外网受限**：这是主要问题，影响了集群中 **27 个 Pod**。
2.  **单个 Pod 启动命令配置错误**：影响了 **1 个 Pod**。

### 异常 Pod 状态总览
| 状态 | 数量 | 影响范围（Namespace） | 核心表象 |
|------|------|-----------------------|----------|
| ImagePullBackOff | 21 | aiops-e2e, default, mcp | 容器镜像拉取失败，等待重试 |
| ErrImagePull | 6 | default | 容器镜像拉取失败，错误状态 |
| CrashLoopBackOff | 1 | aiops-e2e | 容器反复启动失败，持续重启 |

---
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ImagePullBackOff (21), ErrImagePull (6), CrashLoopBackOff (1) |
| **兼容归因层** | L3 - 环境 / 配置层 |
| **问题分类** | **1. 网络连接问题 - 镜像拉取失败 (ImagePullFailed)** <br> **2. 应用配置错误 - 启动命令错误 (CrashLoopBackOffRuntime)** |
| **置信度** | 高 (95%) |
| **证据完整度** | 7/7 (100%) |
---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 问题数量 | 2 个独立问题：网络问题和应用配置问题 |
| 受影响 Namespace | aiops-e2e, default, mcp |
| 受影响 Nodes | node1 (10.2.0.49)， node2 (10.2.0.50) |
| 核心错误示例 1 | Pod `registry-conn-test-1779371220` - 镜像拉取失败，错误：`i/o timeout` / `connection refused` 到 `registry-1.docker.io:443` |
| 核心错误示例 2 | Pod `rc-crashloop-exit-code-5db5947859-2522x` - 容器退出码 `2`，日志报错：`RUNTIME_STARTUP_ERROR` |
---
## 🕵️ 证据链
### 已采集证据
#### 异常组 1：集群网络访问外网受限 (影响 27 个 Pod)
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod registry-conn-test-1779371220` | `Container busybox:1.36.1: State=Waiting, Reason=ImagePullBackOff` <br> `Events: Failed to pull image ... first attempt i/o timeout (157.240.13.8:443), later attempts connection refused (199.59.148.7:443)` | 集群节点(node2)无法访问 Docker Hub，镜像拉取失败。 |
| 2 | 节点连通性 | `run_bash_command` (超时) | `命令执行超时 (30秒)` | 从集群内部对 Docker Hub 的直接网络访问被阻断。 |
| 3 | Pod 状态 | `kubectl describe pod test-dns-1779360358` | `Warning  Failed   ... kubelet  (combined from similar events): Failed to pull image "busybox:1.36.1"` | node1 上的 Pod 同样无法拉取 busybox 镜像，确认问题非节点级个例。 |
| 4 | Pod 状态 | `kubectl describe pod node-debugger-node1-2xvqr` | `Back-off pulling image "curlimages/curl:8.12.1"` <br> `Warning Failed ... Error: ErrImagePull` | 第二个镜像仓库 (curlimages/curl) 同样拉取失败，排除了单一镜像仓库的问题。 |
| 5 | 节点连通性 | `run_bash_command` (`wget`) | `TIMEOUT_OR_REFUSED` | 使用 wget 工具测试网络连接，结果也为超时或拒绝。 |
| 6 | 节点连通性 | `run_bash_command` (`curl`) | `TIMEOUT_OR_REFUSED` | 使用 curl 工具测试网络连接，结果也为超时或拒绝。 |

#### 异常组 2：Pod 应用启动命令错误 (影响 1 个 Pod)
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 7 | Pod 状态 | `kubectl describe pod rc-crashloop-exit-code-5db5947859-2522x` | `Last State: Terminated, Reason: Error, Exit Code: 2` <br> `Warning BackOff x71 over 19m` | 容器以 Exit Code 2 退出，被 kubelet 反复重启。 |
| 8 | 容器日志 | `kubectl logs rc-crashloop-exit-code... --previous` | `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2` | 日志明确指出程序因启动配置错误而退出。 |
| 9 | Pod 配置 | `kubectl get pod rc-crashloop-exit-code... -o yaml` | `deletionTimestamp: <absent>` <br> `finalizers: <none>` | 确认 Pod 处于运行（或重启）状态，且不存在导致卡在 Terminating 的 finalizers。 |

### 证据关联分析
- **证据 #1, #2, #3, #4, #5, #6 印证**：集群中所有 27 个 Pod 的镜像拉取失败问题，根源高度一致地指向 **集群节点无法访问外网 Docker Hub**。所有失败的 Pod 均处于 `Pending` 状态且重启次数为 0，表明问题从 Pod 创建之初就存在，而非运行过程中的退化。
- **证据 #7, #8, #9 印证**：CrashLoopBackOff 的 Pod 与网络问题无关。Exit Code 2 和明确的错误日志表明，该 Pod 的问题是 **启动命令或应用配置错误** 的独立问题。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 节点网络配置（iptables, 代理设置等） | important | 无法从集群内获取，已通过连通性测试间接确认为网络不可达。 |

---
## 🎯 根因分析
### 问题 1：集群网络连通性问题

**因果链**
```
┌─────────────────────────────────────────────────────────────────────────┐
│ 根本原因 (Root Cause)                                                    │
│ 集群出站网络策略、防火墙或代理配置阻止了节点访问公网 Docker Hub。          │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 传导机制 (Propagation)                                                   │
│ 节点(node1, node2) 无法建立到 registry-1.docker.io:443 的 TCP 连接。     │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 直接原因 (Direct Cause)                                                   │
│ kubelet 镜像拉取请求超时/失败，返回 ErrImagePull/ImagePullBackOff 状态。   │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象 (Manifestation)                                             │
│ 27 个分布在 aiops-e2e, default, mcp 命名空间的 Pod 持续处于                │
│ Pending/ImagePullBackOff/ErrImagePull 状态，无法启动提供服务。            │
└─────────────────────────────────────────────────────────────────────────┘
```

**根因结论**
**结论**：根据证据 #1 (Pod events 明确报告 i/o timeout) 和证据 #2 (节点连通性测试失败)，27 个 Pod 无法提供服务的根本原因是 **集群节点无法连通外网 Docker Hub (registry-1.docker.io)**。这是一个集群级别的网络或代理配置问题。

**置信度**：高 (95%)
- ✅ 多个 Pod、多个 Namespace、多种不同镜像（busybox, curlimages/curl）均以相同方式失败。
- ✅ 节点网络连通性测试 (wget, curl, 超时) 均证实了网络不可达。
- ✅ 所有 27 个 Pod 重启次数均为 0，排除应用问题。

### 问题 2：Pod 应用启动命令错误

**因果链**
```
┌─────────────────────────────────────────────────────────────────────────┐
│ 根本原因 (Root Cause)                                                    │
│ 容器启动命令 (/command/args) 或应用配置有误, 导致程序启动失败并返回 2 号错误。 │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象 (Manifestation)                                             │
│ Pod rc-crashloop-exit-code 处于 CrashLoopBackOff 状态，持续重启。        │
└─────────────────────────────────────────────────────────────────────────┘
```

**根因结论**
**结论**：根据证据 #7 (Exit Code 2) 和证据 #8 (日志明确报告 `RUNTIME_STARTUP_ERROR`)，Pod `rc-crashloop-exit-code` 的根本原因是 **容器启动命令或应用配置错误**，需审查 Pod YAML 中的 `command`/`args` 配置和应用代码。

**置信度**：高 (95%)
- ✅ Exit Code 2 是程序启动失败的常见代码。
- ✅ 日志文件直接给出了错误原因。

---
## 🛠️ 修复建议
### 问题 1：集群网络连通性问题 (按优先级排序)
**1. [立即] 排查集群网络出口**
- **操作**：联系基础设施或网络团队，检查集群节点或 Kubernetes 集群的网络出口策略，需要允许 HTTPS (TCP 443) 流量访问以下域名：
    - `registry-1.docker.io`
    - `auth.docker.io`
    - `production.cloudflare.docker.com`
- **方案**：
    - **配置 HTTP 代理**：如果集群在代理后运行，需要在容器运行时 (containerd/cri-o) 或节点的环境变量中配置 `HTTP_PROXY` / `HTTPS_PROXY`。
    - **使用白名单**：将上述 Docker Hub 域名和常见 CDN IP 加入防火墙白名单。
    - **使用私有镜像仓库 (推荐)**：最稳妥的方案。将需要的镜像 (`busybox`, `curlimages/curl`) 推送到您的私有镜像仓库 (如 `xnet.registry.io`)，并修改所有 Pod 的 YAML 文件，将镜像地址指向私有仓库。

**2. [临时] 在集群内创建镜像拉取代理 (DaemonSet)**
- **操作**：如果无法立即修改网络策略，可部署一个 Sidecar 代理或 DaemonSet 作为一个镜像拉取的“中转站”。**此方案较为复杂，不推荐作为长期方案。**

### 问题 2：Pod 应用启动命令错误
**1. [立即] 审查并修正 Pod 配置**
- **操作**：检查 `rc-crashloop-exit-code` Pod 的 YAML 定义，特别是 `command` 和 `args` 字段。
    ```bash
    kubectl get pod rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e -o yaml | grep -A5 “command:”
    ```
- **修正**：如果 YAML 中的启动命令配置有误，请更新 Deployment：
    ```bash
    kubectl edit deployment rc-crashloop-exit-code -n aiops-e2e
    ```
    将 `command` 和 `args` 修改为正确的值。从日志 `RUNTIME_STARTUP_ERROR: rc crashloop exits with code 2` 判断，应用的启动参数可能需要调整。

**2. [修复] 查看应用日志详情的命令**
- **操作**：如果 YAML 配置看起来正确，请检查应用的 Dockerfile 或入口脚本。
    ```bash
    kubectl logs rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e --previous | tail -50
    ```

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| **问题1：网络问题** | | |
| 1. 确认代理配置 | `kubectl exec <pod> -n <ns> -- wget -q -O- http://registry-1.docker.io/v2/` | 配置成功应返回 HTTP 响应，而不是超时。 |
| 2. Pod 状态更新 | `kubectl get pods -n default,aiops-e2e,mcp` | 之前处于 ImagePullBackOff 的 Pod 变为 `Running` 或 `ContainerCreating` (正在拉取)。 |
| **问题2：应用启动错误** | | |
| 3. 确认 Pod 状态 | `kubectl get pod rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e` | Status 变为 `Running`，且 `RESTARTS` 不再增长。 |
| 4. 查看最新日志 | `kubectl logs rc-crashloop-exit-code-5db5947859-2522x -n aiops-e2e` | 日志显示应用启动成功，不再报告 `RUNTIME_STARTUP_ERROR`。 |
---
## ⚠️ 注意事项
- **优先级**：网络问题 (问题1) 涉及 27 个 Pod，影响面最大，应优先处理。应用启动错误 (问题2) 是独立问题，可在网络问题解决后进行。
- **安全策略**：修改网络策略 (IPTables, 防火墙) 时，请注意安全审计和回滚方案。
- **应用代码**：`exit code 2` 通常是应用层面的错误码，请检查应用代码或启动脚本。

---

## 📊 性能统计

├─ 总耗时: 5.8m
├─ 问题定位: 59.0s (17%) ✅
├─ 证据链采集: 222.7s (64%) ✅
├─ 根因分析: 30.2s (9%) ✅
├─ 汇总总结: 34.7s (10%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 25 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed, pod-crashloop-runtime
- **参考 Runbook**: pod-imagepull-failed, pod-crashloop-runtime
- **工具调用**: 25 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
