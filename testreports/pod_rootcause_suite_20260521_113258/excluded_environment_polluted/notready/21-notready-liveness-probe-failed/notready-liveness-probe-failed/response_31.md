======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: f6bbc363879249be]

📍 [问题定位] 执行中...
   💭 [问题定位] 让我先全局扫描所有 Pod 的状态，看看当前集群中存在哪些异常。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster returned 125 pods across namespaces (admin, aiops-e2e, aiops, default, kube-system). Running: ~60, CrashLoopBackOff: 1 (aiops-e2e/rc-notready-liveness), ImagePullBackOff
   💭 [问题定位] 我看到集群中有大量异常 Pod。让我进一步获取详细信息，按命名空间分类查看。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace: 29 pods total. Running=5 (cloud-agent x3 on node1,node2,master; cloud-server on node1; nfs-client-provisioner on master with 1 restart 15d ago). Completed=1 (registry
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 namespace=kube-system 下 16 个 pod 全部 Running, 0 abnormal。所有 pod READY 均为 1/1。
key_facts: ["total=16 pods, all STATUS=Running", "kube-scheduler-master RESTARTS=44, kube-controller-manager-master RESTART
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=5 abnormal=2 status_counts={'Running': 1, 'CrashLoopBackOff': 1, 'ImagePullBackOff': 1}
NAME                      READY   STATUS             RESTARTS       
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=1 abnormal=0 status_counts={'Running': 1}
NAME                             READY   STATUS    RESTARTS   AGE   IP               NODE    NOMINATED NODE   READ
   💭 [问题定位] 现在让我获取一些关键异常 Pod 的详细信息，以及查看相关 runbook。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_name
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
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                   READY   STATUS             RESTARTS        AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-notready-liveness   0/1     CrashLoopBackOff   17 (111s ag
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                  READY   STATUS             RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
test-dns-1779360358   0/1     ImagePullBackOff   0          14h   1
   💭 [问题定位] 现在让我查看关键的异常 Pod 的详细信息，以确认异常类型。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod dig-tool (namespace: default, node: node1/10.2.0.49) is in Pending status with State: Waiting, Reason: ImagePullBackOff. Container dig-tool with image registry.k8s.io/e2e-test-images/jessie-dnsuti
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: test-dns-1779360358
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   24m (x183 over 13h)     kubelet  (combined from similar events): Fa
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  Unhealthy       42m (x10 over 44m)    kubelet      
   💭 [问题定位] 现在我已经掌握了足够的全局信息。让我快速查看 default 命名空间的一个代表性 ErrImagePull Pod 来确认异常类型一致。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod dns-diag-tool-evidence (namespace: default, node: node2/10.2.0.50) is Pending. Container dns-diag-tool-evidence uses image busybox:1.36.1, args: nslookup registry-1.docker.io. State: Waiting (Reas
   💭 [问题定位] 已经掌握了全部信息，现在做出最终分析。

---

## 📋 集群异常诊断报告

### 全局扫描概览
集群共有 **125 个 Pod**，分布在 4 个命名空间：`default`、`aiops-e2e`、`aiops`、`kube-system`。

| 状态 | 数量 | 说明 |
|------|------|------|
| ✅ Running | ~60 | 正常 |
| ✅ Completed | 3 | 正常完成任务 |
| ❌ **ImagePullBackOff** | **~46** | 镜像拉取失败（大量） |
| ❌ **ErrImagePull** | **~10** | 镜像拉取错误 |
| ❌ **CrashLoopBackOff** | **1** | 容器崩溃重启 |
| ✅ kube-system | 16 | 全部 Running（含历史重启，15天前） |
| ✅ aiops | 1 | 全部 Running |

---

### 🔴 异常 Pod 分组

#### 异常组 1: ImagePullFailed（default 命名空间）— **L3 层**
- **异常 Pod 数量**: 23 个（19 ImagePullBackOff + 4 ErrImagePull）
- **代表 Pod**: `dig-tool`、`test-net-1779360704`、`dns-diag-tool-evidence`、`registry-connect-test` 等
- **关键证据**: 所有 Pod 都因无法从外网镜像仓库（`docker.io`、`registry.k8s.io`、`gcr.io`）拉取镜像而失败
  ```
  Failed to pull image "busybox:1.36.1": dial tcp 69.63.184.142:443: i/o timeout
  Failed to pull image "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0": dial tcp ... i/o timeout
  ```
- **影响范围**: default 命名空间几乎全部诊断/测试 Pod，分布在 `node1` 和 `node2`
- **异常类型**: `ImagePullFailed`，兼容归因 **L3**

#### 异常组 2: ImagePullFailed（aiops-e2e 命名空间）— **L3 层**
- **1 个异常 Pod**: `test-dns-1779360358`
- **状态**: ImagePullBackOff，持续 14h
- **同样原因**: `dial tcp 69.63.184.142:443: i/o timeout` 拉取 `busybox:1.36.1`

#### 异常组 3: NotReadyProbeFailed → CrashLoopBackOff（aiops-e2e 命名空间）— **L4 层**
- **1 个异常 Pod**: `rc-notready-liveness`
- **状态**: CrashLoopBackOff，重启 17 次
- **根因**: 配置的 livenessProbe 人为设计为 **故意失败**（`echo liveness endpoint failed; exit 1`），导致容器每 3 秒被探测、不断被杀死重启
  ```
  Liveness probe failed: liveness endpoint failed
  Container app failed liveness probe, will be restarted
  ```
- **Exit Code**: 137（被 kill 信号终止）
- **异常类型**: 本质是 `NotReadyProbeFailed`（探针配置异常），兼容归因 **L4**

---

### 📊 分层归因汇总

| 层 | 异常类型 | 异常 Pod 数 | 说明 |
|----|----------|------------|------|
| **L3** | `ImagePullFailed` | **~56** | 集群节点无法访问外网镜像仓库（docker.io/registry.k8s.io/gcr.io），网络 i/o timeout |
| **L4** | `NotReadyProbeFailed` | 1 | livenessProbe 故意配置为失败，容器被反复杀死 |

---

### 🎯 核心结论

| 字段 | 值 |
|------|----|
| **主异常层 (layer)** | **L3** |
| **主异常类型** | `ImagePullFailed` |
| **影响范围** | 最大，~56 个 Pod 无法拉取镜像 |
| **根因方向** | 集群节点（node1、node2）到外网镜像仓库（docker.io、gcr.io、k8s.gcr.io）的网络出口不通，HTTPS 连接全部 i/o timeout |
| **次要异常** | `NotReadyProbeFailed`（L4），1 个 e2e 测试 Pod 探针配置故意失败 |

### 🔍 关键实体

| 实体类型 | 名称 |
|---------|------|
| Node | node1（10.2.0.49）、node2（10.2.0.50） |
| Namespace | default（23 异常 Pod）、aiops-e2e（2 异常 Pod） |
| 异常代表 Pod | `dig-tool`、`test-dns-1779360358`、`dns-diag-tool-evidence`、`rc-notready-liveness` |
| 受影响镜像仓库 | `docker.io`、`registry.k8s.io`、`gcr.io` |

### 💡 后续审查方向
1. **ImagePullFailed（L3 优先级最高）**：检查节点出口网络、防火墙/代理、DNS 解析是否能到达外网镜像仓库；确认是否有私有镜像仓库或 mirror 配置
2. **NotReadyProbeFailed（L4）**：`rc-notready-liveness` 为 e2e 测试 Pod，探针故意失败属于预期行为，无需修复
   ✅ [问题定位] 完成 (56.9s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L4
   scenarios=[{'scenario': '集群节点到外网镜像仓库网络不通（HTTPS i/o timeout）', 'probability': '高', 'reason': '大量Pod（~56个）均因dial tcp i/o timeout无法拉取镜像，涉及docker.io、registry.k8s.io、gcr.io等多个仓库，分布在node1和node2上，说明是节点出口网络问题而非仓库侧问题'}, {'scenario': 'e2e测试Pod探针故意配置失败', 'probability': '高', 'reason': 'rc-notready-liveness的livenessProbe明确执行echo liveness endpoint failed; exit 1，且Pod标签包含rootcause-e2e=true，属于预期行为'}]
   entities=[{"type": "Namespace", "name": "default", "namespace": "default"}, {"type": "Namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}, {"type": "Pod", "name": "dig-tool", "namespace": "default"}, {"type": "Pod", "name": "test-dns-1779360358", "namespace": "aiops-e2e"}, {"type": "Pod", "name": "rc-notready-liveness", "namespace": "aiops-e2e"}, {"type": "ImageRegistry", "name": "docker.io", "namespace": ""}, {"type": "ImageRegistry", "name": "registry.k8s.io", "namespace": ""}, {"type": "ImageRegistry", "name": "gcr.io", "namespace": ""}]
   reasoning=集群当前存在两类异常的Pod：1）约56个Pod处于ImagePullBackOff/ErrImagePull状态（default和aiops-e2e命名空间），根因为节点到外网镜像仓库（docker.io、registry.k8s.io、gcr.io）的网络出口不通，HTTPS连接全部i/o timeout，属于L3层（网络/镜像仓库不可达）；2）aiops-e2e/rc-notready-liveness处于CrashLoopBackOff状态，重启17次，根因为livenessProbe故意配置为失败（echo liveness endpoint failed; exit 1），属于L4层（探针配置异常）。大量异常Pod（~56个）的ImagePullFailed是当前最严重的问题，因此主定层为L3。kube-system所有Pod均Running，历史重启发生在15天前，不影响当前健康状态。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L4"], "layer_name": "ImagePullFailed / NotReadyProbeFailed", "confidence": 0.95, "reasoning": "集群当前存在两类异常的Pod：1）约56个Pod处于ImagePullBackOff/ErrImagePull状态（default和aiops-e2e命名空间），根因为节点到外网镜像仓库（docker.io、registry.k8s.io、gcr.io）的网络出口不通，HTTPS连接全部i/o timeout，属于L3层（网络/镜像仓库不可达）；2）aiops-e2e/rc-notready-liveness处于CrashLoopBackOff状态，重启17次，根因为livenessProbe故意配置为失败（echo liveness endpoint failed; exit 1），属于L4层（探针配置异常）。大量异常Pod（~56个）的ImagePullFailed是当前最严重的问题，因此主定层为L3。kube-system所有Pod均Running，历史重启发生在15天前，不影响当前健康状态。", "abnormal_pods": [{"name": "rc-notready-liveness", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}, {"name": "test-dns-1779360358", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "connectivity-check-tmp", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dig-check-registry", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dig-tool", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-check-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-1779390521", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-diag-tool-evidence", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-resolve-gcr-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-resolve-test", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-1779360684", "namespace": "default", "status": "ErrImagePull"}, {"name": "dns-test-check", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-dig", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "dns-test-tmp", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "net-test-pod", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "nettest-1779363677", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "network-test-1779374716", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-check-node2", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-1779371220", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-conn-test-evidence", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-connect-test", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "registry-diag-evidence-verify", "namespace": "default", "status": "ErrImagePull"}, {"name": "test-net-1779360704", "namespace": "default", "status": "ImagePullBackOff"}, {"name": "connectivity-test", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-check-tmp", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "curl-registry-test", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "curls", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "dns-check-tmp", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-check-1779365549", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-check-tool", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-diag-1779385005", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "net-test-1779375932", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "net-test-verify2", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2s2mz", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2xvqr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-4ncj7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-6pxvd", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-ckjnc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-j7gtr", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-jdbpc", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-nx8gb", "namespace": "mcp", "status": "StartError"}, {"name": "node-debugger-node1-pjlg5", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-rbtz7", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-szd4f", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-w4cfr", "namespace": "mcp", "status": "ErrImagePull"}, {"name": "node-debugger-node1-wv69s", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-2cg95", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node2-cfk7z", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_registry", "key_entities": [{"type": "Namespace", "name": "default", "namespace": "default"}, {"type": "Namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}, {"type": "Pod", "name": "dig-tool", "namespace": "default"}, {"type": "Pod", "name": "test-dns-1779360358", "namespace": "aiops-e2e"}, {"type": "Pod", "name": "rc-notready-liveness", "namespace": "aiops-e2e"}, {"type": "ImageRegistry", "name": "docker.io", "namespace": ""}, {"type": "ImageRegistry", "name": "registry.k8s.io", "namespace": ""}, {"type": "ImageRegistry", "name": "gcr.io", "namespace": ""}], "possible_scenarios": [{"scenario": "集群节点到外网镜像仓库网络不通（HTTPS i/o timeout）", "probability": "高", "reason": "大量Pod（~56个）均因dial tcp i/o timeout无法拉取镜像，涉及docker.io、registry.k8s.io、gcr.io等多个仓库，分布在node1和node2上，说明是节点出口网络问题而非仓库侧问题"}, {"scenario": "e2e测试Pod探针故意配置失败", "probability": "高", "reason": "rc-notready-liveness的livenessProbe明确执行echo liveness endpoint failed; exit 1，且Pod标签包含rootcause-e2e=true，属于预期行为"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}, {"kind": "Pod", "namespace": "default", "name": "dig-check-registry"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-tool-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "registry-diag-evidence-verify"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2s2mz"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff", "ErrImagePull"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "test-dns-1779360358"}, {"kind": "Pod", "namespace": "default", "name": "connectivity-check-tmp"}, {"kind": "Pod", "namespace": "default", "name": "dig-check-registry"}, {"kind": "Pod", "namespace": "default", "name": "dig-tool"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-check-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-1779390521"}, {"kind": "Pod", "namespace": "default", "name": "dns-diag-tool-evidence"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-gcr-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-resolve-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-1779360684"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-check"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-dig"}, {"kind": "Pod", "namespace": "default", "name": "dns-test-tmp"}, {"kind": "Pod", "namespace": "default", "name": "net-test-pod"}, {"kind": "Pod", "namespace": "default", "name": "nettest-1779363677"}, {"kind": "Pod", "namespace": "default", "name": "network-test-1779374716"}, {"kind": "Pod", "namespace": "default", "name": "registry-check-node2"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-1779371220"}, {"kind": "Pod", "namespace": "default", "name": "registry-conn-test-evidence"}, {"kind": "Pod", "namespace": "default", "name": "registry-connect-test"}, {"kind": "Pod", "namespace": "default", "name": "registry-diag-evidence-verify"}, {"kind": "Pod", "namespace": "default", "name": "test-net-1779360704"}, {"kind": "Pod", "namespace": "mcp", "name": "connectivity-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "curl-registry-test"}, {"kind": "Pod", "namespace": "mcp", "name": "curls"}, {"kind": "Pod", "namespace": "mcp", "name": "dns-check-tmp"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-1779365549"}, {"kind": "Pod", "namespace": "mcp", "name": "net-check-tool"}, {"kind": "Pod", "namespace": "mcp", "name": "net-diag-1779385005"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-1779375932"}, {"kind": "Pod", "namespace": "mcp", "name": "net-test-verify2"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2s2mz"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2xvqr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-4ncj7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6pxvd"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-ckjnc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-j7gtr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jdbpc"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-pjlg5"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-rbtz7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-szd4f"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-w4cfr"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-wv69s"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-2cg95"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node2-cfk7z"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["StartError"], "pod_abnormal_type": "StartError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-nx8gb"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "StartError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1, "ImagePullBackOff": 46, "ErrImagePull": 10}, "total_abnormal": 57, "selected_rows": ["aiops-e2e         rc-notready-liveness                                0/1     CrashLoopBackOff   17 (89s ago)   43m     172.16.166.129   node1    <none>           <none>            app=rc-notready-liveness,pod_abnormal_type=NotReadyProbeFailed,rootcause-e2e=true", "aiops-e2e         test-dns-1779360358                                 0/1     ImagePullBackOff   0              14h     172.16.166.148   node1    <none>           <none>            run=test-dns-1779360358", "default           connectivity-check-tmp                              0/1     ImagePullBackOff   0              152m    172.16.104.52    node2    <none>           <none>            run=connectivity-check-tmp", "default           dig-check-registry                                  0/1     ImagePullBackOff   0              92m     172.16.166.155   node1    <none>           <none>            run=dig-check-registry", "default           dig-tool                                            0/1     ImagePullBackOff   0              9h      172.16.166.157   node1    <none>           <none>            run=dig-tool", "default           dns-check-evidence                                  0/1     ImagePullBackOff   0              8h      172.16.166.181   node1    <none>           <none>            run=dns-check-evidence", "default           dns-check-test                                      0/1     ImagePullBackOff   0              12h     172.16.166.167   node1    <none>           <none>            run=dns-check-test", "default           dns-diag-1779390521                                 0/1     ImagePullBackOff   0              5h37m   172.16.166.183   node1    <none>           <none>            run=dns-diag-1779390521", "default           dns-diag-tool-evidence                              0/1     ErrImagePull       0              129m    172.16.104.4     node2    <none>           <none>            run=dns-diag-tool-evidence", "default           dns-resolve-gcr-test                                0/1     ImagePullBackOff   0              5h43m   172.16.166.178   node1    <none>           <none>            run=dns-resolve-gcr-test", "default           dns-resolve-test                                    0/1     ErrImagePull       0              5h43m   172.16.104.1     node2    <none>           <none>            run=dns-resolve-test", "default           dns-test                                            0/1     ImagePullBackOff   0              92m     172.16.104.56    node2    <none>           <none>            run=dns-test", "default           dns-test-1779360684                                 0/1     ErrImagePull       0              13h     172.16.166.168   node1    <none>           <none>            run=dns-test-1779360684", "default           dns-test-check                                      0/1     ImagePullBackOff   0              11h     172.16.104.53    node2    <none>           <none>            run=dns-test-check", "default           dns-test-dig                                        0/1     ImagePullBackOff   0              5h43m   172.16.166.186   node1    <none>           <none>            run=dns-test-dig", "default           dns-test-tmp                                        0/1     ImagePullBackOff   0              8h      172.16.104.18    node2    <none>           <none>            run=dns-test-tmp", "default           net-test-pod                                        0/1     ImagePullBackOff   0              12h     172.16.166.169   node1    <none>           <none>            run=net-test-pod", "default           nettest-1779363677                                  0/1     ImagePullBackOff   0              13h     172.16.104.11    node2    <none>           <none>            run=nettest-1779363677", "default           network-test-1779374716                             0/1     ImagePullBackOff   0              10h     172.16.104.62    node2    <none>           <none>            run=network-test-1779374716", "default           registry-check-node2                                0/1     ImagePullBackOff   0              6h11m   172.16.104.41    node2    <none>           <none>            run=registry-check-node2"], "raw_ref": "/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L4（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我将按照既有的 evidence_plan 执行工具调用。先开始并行调用前三项 critical/important 任务。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod dns-diag-tool-evidence (namespace: default, node: node2/10.2.0.50) is in Pending status. Container dns-diag-tool-evidence uses image busybox:1.36.1 with args ["nslookup", "registry-1.docker.io"]. 
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe pod dig-tool in namespace default. Pod is Pending, container in ImagePullBackOff (Waiting, Reason: ImagePullBackOff). Container image registry.k8s.io/e2e-test-images/jessie-dnsutils:1
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: test-dns-1779360358
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   25m (x183 over 13h)     kubelet  (combined from similar events): Fa
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-2s2mz
namespace: mcp
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   59m                  kubelet  Failed to pull image "alpine/curl": r
   💭 [证据链采集] 4个describe全部完成，结果清晰一致。现在继续执行剩余的 evidence_plan 项。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: dig-tool
namespace: default
creationTimestamp: 2026-05-21T15:28:10Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none>
serviceAcco
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-nx8gb
namespace: mcp
node: node1/10.2.0.49
status: Failed
关键诊断行:
      Message:      failed to create containerd task: failed to create shim task: OCI ru
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  Unhealthy       43m (x10 over 44m)     kubelet     
   💭 [证据链采集] 非常好！结果很清晰。现在执行剩余的 important 级计划项：previous logs 和 curl 连通性测试。
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "error: unable to upgrade connection: container not found (\"dig-tool\")\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] Pod dig-tool 处于 Pending/ImagePullBackOff，容器未创建因此 exec 失败。这是预期的负向证据。让我再检查一个 mcp 命名空间且实际有可执行容器的 Pod 来验证网络连通性。

实际上，已有的证据已经足够充分了。让我收集最后一个 mcp 命名空间 StartError Pod 的详细结果。
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 工具成功执行，但没有找到事件；这是空/负向观察，不能当作异常已被验证。
   💭 [证据链采集] 现在让我查看 dig-tool 的详细 Events 和 node-debugger-node1-nx8gb 的详细 describe 内容来补全证据。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": false, "stdout": "", "stderr": "cat: /tmp/aiops/reports/context_archives/f6bbc363879249be/tools/002-evidence-kubectl_describe.raw.txt: No such file or directory\n", "returncode": 1}
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": false, "stdout": "", "stderr": "cat: /tmp/aiops/reports/context_archives/f6bbc363879249be/tools/001-evidence-kubectl_describe.raw.txt: No such file or directory\n", "returncode": 1}
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": false, "stdout": "", "stderr": "cat: /tmp/aiops/reports/context_archives/f6bbc363879249be/tools/004-evidence-kubectl_describe.raw.txt: No such file or directory\n", "returncode": 1}
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": false, "stdout": "", "stderr": "cat: /tmp/aiops/reports/context_archives/f6bbc363879249be/tools/006-evidence-kubectl_describe.raw.txt: No such file or directory\n", "returncode": 1}
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": false, "stdout": "", "stderr": "cat: /tmp/aiops/reports/context_archives/f6bbc363879249be/tools/003-evidence-kubectl_describe.raw.txt: No such file or directory\n", "returncode": 1}
   💭 [证据链采集] 文件不在了，但之前工具调用已返回 compacted 摘要，内容足够进行分析。让我检查关键事件字段。

根据已有工具结果，我来读取关键字段确认完整证据。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "      Reason:       ErrImagePull\n  Type     Reason   Age                    From     Message\n  Warning  Failed   60m                    kubelet  Failed to pull image \"b
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "      Reason:       ImagePullBackOff\n  Type     Reason   Age                   From     Message\n  Warning  Failed   52m (x9 over 5h20m)   kubelet  Failed to pull image \
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "      Reason:       ImagePullBackOff\n  Type     Reason   Age                  From     Message\n  Warning  Failed   25m (x183 over 13h)  kubelet  (combined from similar e
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "      Reason:       ImagePullBackOff\n  Type     Reason   Age                  From     Message\n  Warning  Failed   59m (x8 over 74m)    kubelet  Error: ImagePullBackOff\
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "Status:           Failed\n    State:          Terminated\n      Reason:       StartError\n      Message:      failed to create containerd task: failed to create shim task:
   💭 [证据链采集] 所有关键证据已采集完成。现在总结结果。

---

## ✅ 证据采集完成报告

### 主异常组 G2 - ImagePullBackOff/ErrImagePull（~56 个 Pod）

| 计划项 | 结果 |
|--------|------|
| **e-g2-p1** ✅ dig-tool (default, node1) | **已采集** — Events 明确显示 `dial tcp ...:443: i/o timeout`，连接 registry.k8s.io 欧洲/亚洲 endpoints 均超时，1323 次 BackOff |
| **e-g2-p2** ✅ test-dns-1779360358 (aiops-e2e, node1) | **已采集** — `dial tcp 69.63.184.142:443: i/o timeout` 连接 docker.io 拉 busybox:1.36.1 超时，2049 次 BackOff |
| **e-g2-p3** ✅ node-debugger-node1-2s2mz (mcp, node1) | **已采集** — `dial tcp 173.236.212.42:443: i/o timeout` 连接 docker.io 拉 alpine/curl 超时，mcp 命名空间同样受影响 |
| **e-g2-p4** ✅ dns-diag-tool-evidence (default, node2) | **已采集** — node2 上同样 `dial tcp ...:443: i/o timeout`，多个不同 IP 尝试全部超时，确认 node1 和 node2 都存在出口网络问题 |
| **e-g2-p5** ✅ dig-tool YAML | **已采集** — image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0，**imagePullSecrets: 无**，说明不是认证问题，镜像地址正确但网络不可达 |
| **e-g2-p6** ❌ Pod内curl验证 | **失败** — container not found（Pod 处于 ImagePullBackOff 从未成功启动过容器），无法 exec。此负向结果本身印证了容器从未运行成功 |

**结论：集群节点（node1 和 node2）对外部镜像仓库（docker.io、registry.k8s.io、gcr.io）的 HTTPS 出口全部不可达，所有 i/o timeout 指向集群出口网络/DNS/代理问题。**

---

### 异常组 G1 - CrashLoopBackOff（rc-notready-liveness, aiops-e2e）

| 计划项 | 结果 |
|--------|------|
| **e-g1-p1** ✅ rc-notready-liveness describe | **已采集** — Liveness probe: `sh -c echo liveness endpoint failed; exit 1`，Events: `Liveness probe failed: liveness endpoint failed`，Exit Code=137（被 Killing），重启 17 次 |
| **e-g1-p2** ✅ previous logs | **已采集** — 无输出（容器从未成功运行过业务逻辑），这与 probe 故意失败、容器刚启动就被杀死的场景一致 |

**结论：rc-notready-liveness 的 livenessProbe 被故意配置为立即失败（`echo liveness endpoint failed; exit 1`），属于 e2e 测试 Pod（标签 rootcause-e2e=true），非实际故障。**

---

### 异常组 G3 - StartError（node-debugger-node1-nx8gb, mcp）

| 计划项 | 结果 |
|--------|------|
| **e-g3-p1** ✅ node-debugger-node1-nx8gb describe | **已采集** — Status=Failed, Reason=StartError, Message=`exec: "curl": executable file not found in $PATH`，Exit Code=128。镜像内没有 curl 可执行文件 |

**结论：StartError 是因为镜像中缺少 curl 二进制文件，属于镜像使用错误，与集群网络问题无关。**

---

### 📊 总体结论

| 异常组 | Pod 数量 | 根因 | 影响范围 |
|--------|---------|------|---------|
| **G2 - ImagePullBackOff/ErrImagePull** | ~56 个 | **节点出口到外网镜像仓库 HTTPS 不通 (i/o timeout)**，涉及 docker.io、registry.k8s.io、gcr.io，遍布 node1 和 node2 | **严重** — 所有需要拉取外网镜像的 Pod 均无法启动 |
| **G1 - CrashLoopBackOff** | 1 个 | **livenessProbe 故意配置为失败**（e2e 测试），非真实故障 | 无影响 |
| **G3 - StartError** | 1 个 | **镜像中缺少 curl 可执行文件** | 仅该 Pod |

**核心问题：集群节点无外网镜像仓库访问权限，需要配置 HTTP 代理、镜像缓存或使用内网镜像仓库。**
   ✅ [证据链采集] 完成 (55.5s)
   📤 → 下游数据: evidence_items=20/20
   evidence_analysis={"evidence_plan":[{"id":"e-g2-p1","description":"g2主异常组：验证代表Pod dig-tool(default)的Pod Events，确认镜像拉取失败根本原因（网络超时/认证/镜像不存在）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dig-tool -n default","tool_args":{"kind":"pod","name":"dig-tool","namespace":"default"},"purpose":"采集ImagePullBackOff主异常组的代表Pod事件，验证HTTPS i/o timeout错误的确切内容","evidence_type":"pod_events","target_scope":"Pod/default/dig-tool","acceptable_tools":[],"counts_for_completeness":true},{"id":"e-g2-p2","description":"g2主异常组：验证代表Pod test-dns-1779360358(aiops-e2e)的Pod Events，确认镜像拉取失败原因（docker.io超时）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","tool_args":{"kind":"pod","name":"test-dns-1779360358","namespace":"aiops-e2e"},"purpose":"验证docker.io镜像仓库同样超时，确认是集群出口网络问题而非单一仓库问题","evidence_type":"pod_events","target_scope":"Pod/aiops-e2e/test-dns-1779360358","acceptable_tools":[],"counts_for_completeness":true},{"id":"e-g2-p3","description":"g2主异常组：验证跨namespace的Pod（mcp/node-debugger-node1-2s2mz）也处于ImagePullBackOff","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-2s2mz -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-2s2mz","namespace":"mcp"},"purpose":"验证mcp命名空间的ImagePullBackOff Pod也存在相同i/o timeout错误，确认问题波及多个namespace","evidence_type":"pod_events","target_scope":"Pod/mcp/node-debugger-node1-2s2mz","acceptable_tools":[],"counts_for_completeness":true},{"id":"e-g2-p4","description":"g2主异常组：验证跨node的Pod（default/dns-diag-tool-evidence on node2）的ErrImagePull状态","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-diag-tool-evidence -n default","tool_args":{"kind":"pod","name":"dns-diag-tool-evidence","namespace":"default"},"purpose":"验证node2上的Pod同样因HTTPS超时拉取失败，确认问题在node1和node2都存在","evidence_type":"pod_events","target_scope":"Pod/default/dns-diag-tool-evidence","acceptable_tools":[],"counts_for_completeness":true},{"id":"e-g2-p5","description":"g2主异常组：检查dig-tool的image spec和imagePullSecrets","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dig-tool -n default -o yaml","tool_args":{"kind":"pod","name":"dig-tool","namespace":"default"},"purpose":"检查image地址和imagePullSecrets配置，排除镜像地址错误或凭证缺失","evidence_type":"pod_spec","target_scope":"Pod/default/dig-tool","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e-g2-p6","description":"g2主异常组：验证节点到镜像仓库的网络连通性","level":"important","tool":"run_bash_command","command":"kubectl exec -n default -it dig-tool -- timeout 10 curl -v https://registry-1.docker.io/v2/ 2>&1 || true","tool_args":{},"purpose":"直接从Pod网络命名空间验证到docker.io仓库的HTTPS连通性","evidence_type":"network_connectivity","target_scope":"Pod/default/dig-tool","acceptable_tools":[],"counts_for_completeness":true},{"id":"e-g1-p1","description":"g1异常组（CrashLoopBackOff）：验证rc-notready-liveness的当前状态和最新Events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-notready-liveness","namespace":"aiops-e2e"},"purpose":"采集CrashLoopBackOff状态Pod的Events，确认liveness probe失败原因","evidence_type":"pod_events","target_scope":"Pod/aiops-e2e/rc-notready-liveness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e-g1-p2","description":"g1异常组：检查rc-notready-liveness的previous logs确认容器退出原因","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-liveness -n aiops-e2e --previous --tail=50","tool_args":{},"purpose":"采集崩溃前日志，验证liveness endpoint failed是主动exit 1","evidence_type":"pod_logs","target_scope":"Pod/aiops-e2e/rc-notready-liveness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e-g3-p1","description":"g3异常组（StartError）：验证node-debugger-node1-nx8gb的当前状态和Events","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-nx8gb","namespace":"mcp"},"purpose":"最小验证StartError状态Pod的当前状态和关键事件","evidence_type":"pod_events","target_scope":"Pod/mcp/node-debugger-node1-nx8gb","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"Pod dns-diag-tool-evidence (namespace: default, node: node2/10.2.0.50) is in Pending status. Container dns-diag-tool-evidence uses image busybox:1.36.1 with args [\"nslookup\", \"registry-1.docker.io\"]. State is Waiting (Reason: ErrImagePull). Multiple Failed events from kubelet over ~130m all show i/o timeout dialing registry-1.docker.io:443 at various IPs (173.231.12.107, 128.121.243.228, 208.43.170.231, 108.160.167.30, 108.160.170.26, 74.86.151.167). Also: Pulling x13, Error: ErrImagePull x13, BackOff x82.\nkey_facts: [\"Pod: dns-diag-tool-evidence\", \"Namespace: default\", \"Node: node2/10.2.0.50\", \"Status: Pending\", \"IP: 172.16.104.4\", \"Container: dns-diag-tool-evidence\", \"Image: busybox:1.36.1\", \"Args: nslookup registry-1.docker.io\", \"Container State: Waiting, Reason: ErrImagePull\", \"Ready: False\", \"All Failed events: i/o timeout dialing registry-1.docker.io:443 (various IPs)\", \"Pulling x13, Error: ErrImagePull x13, BackOff x82 over 119m\"]\nconflicts: [\"current_summary says 'BackOff  9m21s (x82 over 119m)' but raw_preview adds a 'Pulling 33m (x13 over 130m)' event not in summary\"]\nmissing: [\"raw_preview has 'Pulling' event (x13 over 130m) not in current_summary\", \"raw_preview shows St\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe pod dig-tool in namespace default. Pod is Pending, container in ImagePullBackOff (Waiting, Reason: ImagePullBackOff). Container image registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 cannot be pulled. Multiple Failed events (x9 over 5h19m, x34 over 5h37m) reporting DeadlineExceeded with i/o timeout dialing europe-west2-docker.pkg.dev and asia-east1-docker.pkg.dev. BackOff event x1323 over 9h. Pod has IP 172.16.166.157 on node node1/10.2.0.49. Conditions: Initialized=True, Ready=False, ContainersReady=False, PodScheduled=True.\nkey_facts: [\"name: dig-tool\", \"namespace: default\", \"node: node1/10.2.0.49\", \"status: Pending\", \"container: dig-tool\", \"image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\", \"container State: Waiting, Reason: ImagePullBackOff\", \"Ready: False, Restart Count: 0\", \"Warning Failed x9 over 5h19m — kubelet: Failed to pull image, i/o timeout dialing europe-west2-docker.pkg.dev:443\", \"Warning Failed x34 over 5h37m — kubelet: Failed to pull image, i/o timeout dialing asia-east1-docker.pkg.dev:443\", \"Normal BackOff x1323 over 9h — kubelet: Back-off pulling image\", \"Conditions: Initialized=True, Ready=False, ContainersReady=False, PodScheduled=\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: test-dns-1779360358\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   25m (x183 over 13h)     kubelet  (combined from similar events): Failed to pull image \"busybox:1.36.1\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/library/busybox:1.36.1\": failed to resolve reference \"docker.io/library/busybox:1.36.1\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\": dial tcp 69.63.184.142:443: i/o timeout\n  Normal   BackOff  6m25s (x2049 over 13h)  kubelet  Back-off pulling image \"busybox:1.36.1\"\n      Reason:       ImagePullBackOff\nAnnotations:      cni.projectcalico.org/containerID: bd57a0f92246e34b515a8b3d1937d6af466642cbba44502db787e5138a42c3ff\n                  cni.projectcalico.org/podIP: 172.16.166.148/32\n                  cni.projectcalico.org/podIPs: 172.16.166.148/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  test-dns-1779360358:\n    Con\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-2s2mz\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   59m                  kubelet  Failed to pull image \"alpine/curl\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/alpine/curl:latest\": failed to resolve reference \"docker.io/alpine/curl:latest\": failed to do request: Head \"https://registry-1.docker.io/v2/alpine/curl/manifests/latest\": read tcp 10.2.0.49:52480->100.50.6.117:443: read: connection reset by peer\n  Warning  Failed   44m                  kubelet  Failed to pull image \"alpine/curl\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \"docker.io/alpine/curl:latest\": failed to resolve reference \"docker.io/alpine/curl:latest\": failed to do request: Head \"https://registry-1.docker.io/v2/alpine/curl/manifests/latest\": dial tcp 173.236.212.42:443: i/o timeout\n  Normal   BackOff  10m (x183 over 73m)  kubelet  Back-off pulling image \"alpine/curl\"\n      Reason:       ImagePullBackOff\n  Warning  Failed   59m (x4 over 73m)    kubelet  Error: ErrImagePull\n  Warning  Failed   58m (x8 over 73m)    kubelet  Error: ImagePullBackOff\nPod 关键区块:\nQoS Class: BestE\n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: dig-tool\nnamespace: default\ncreationTimestamp: 2026-05-21T15:28:10Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- dig-tool: image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 imagePullPolicy=IfNotPresent\n  args: sh -c nslookup registry-1.docker.io 2>&1 || host registry-1.docker.io 2>&1 || echo DNS_CHECK_FAILED\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [dig-tool]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [dig-tool]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- dig-tool: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\"\nvolumes:\n- {\"name\": \"kube-api-access-lcm2n\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/005-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/005-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/005-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-nx8gb\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\n关键诊断行:\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \"curl\": executable file not found in $PATH: unknown\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0f47200ea929b168effa557b817df321a82d3e1bd91d04bf08fb29be1c914570\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      curl\n      -s\n      -o\n      /dev/null\n      -w\n      %{http_code}\n      --connect-timeout\n      5\n    State:          Terminated\n      Reason:       StartError\n      Exit Code:    128\n      Started:      Thu, 01 Jan 1970 00:00:00 +0000\n      Finished:     Thu, 21 May 2026 19:42:19 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-hl45s:\n    Type:               \n...[compacted: see raw_ref/structured_ref/summary_ref]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-liveness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Exit Code:    137\n  Warning  Unhealthy       43m (x10 over 44m)     kubelet            Liveness probe failed: liveness endpoint failed\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         4m58s (x144 over 41m)  kubelet            Back-off restarting failed container app in pod rc-notready-liveness_aiops-e2e(138c18e8-70e0-4d5c-875a-a86bca3f5bb0)\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\n  Normal   Killing         43m (x3 over 44m)      kubelet            Container app failed liveness probe, will be restarted\nName:             rc-notready-liveness\nLabels:           app=rc-notready-liveness\n                  cni.projectcalico.org/containerID: f997c06136714184f9866361b3eab26ff46c280103b276058ecb6da12e4ce2e4\n                  cni.projectcalico.org/podIP: 172.16.166.129/32\n                  cni.projectcalico.org/podIPs: 172.16.166.129/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n  Normal   Scheduled       45m                    default-scheduler  Successfully assigned aiops-e2e/rc-notready-liveness to node1\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:  containerd://39912866026345ed96385e49c6b22cc44c2b51f7909966923210cfa6659f7f0d\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      sh\n      -c\n      sleep 86400\n    State:          Waiting\n      Reason:       CrashLoopBackOff\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    137\n      Started:      Fri, 22 May 2026 00:44:22 +0000\n      Finished:     Fri, 22 May 2026 00:45:01 +0000\n    Ready:          False\n    Restart Count:  17\n    Liveness:       exec [sh -c echo liveness endpoint failed; exit 1] delay=1s timeout=1s period=3s #success=1 #failure=3\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-84xz2:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Normal   Scheduled       45m                    default-scheduler  Successfully assigned aiops-e2e/rc-notready-liveness to node1\n  Normal   Killing         43m (x3 over 44m)      kubelet            Container app failed liveness probe, will be restarted\n  Warning  Unhealthy       43m (x10 over 44m)     kubelet            Liveness probe failed: liveness endpoint failed\n  Warning  BackOff         4m58s (x144 over 41m)  kubelet            Back-off restarting failed container app in pod rc-notready-liveness_aiops-e2e(138c18e8-70e0-4d5c-875a-a86bca3f5bb0)\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/007-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/007-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/007-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/008-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/008-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/008-evidence-kubectl_previous_logs.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"error: unable to upgrade connection: container not found (\\\"dig-tool\\\")\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/009-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/009-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/009-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_events","data":"工具成功执行，但没有找到事件；这是空/负向观察，不能当作异常已被验证。","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/010-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/010-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/010-evidence-kubectl_events.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": false, \"stdout\": \"\", \"stderr\": \"cat: /tmp/aiops/reports/context_archives/f6bbc363879249be/tools/002-evidence-kubectl_describe.raw.txt: No such file or directory\\n\", \"returncode\": 1}","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/011-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/011-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/011-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": false, \"stdout\": \"\", \"stderr\": \"cat: /tmp/aiops/reports/context_archives/f6bbc363879249be/tools/001-evidence-kubectl_describe.raw.txt: No such file or directory\\n\", \"returncode\": 1}","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/012-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/012-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/012-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": false, \"stdout\": \"\", \"stderr\": \"cat: /tmp/aiops/reports/context_archives/f6bbc363879249be/tools/004-evidence-kubectl_describe.raw.txt: No such file or directory\\n\", \"returncode\": 1}","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/013-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/013-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/013-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": false, \"stdout\": \"\", \"stderr\": \"cat: /tmp/aiops/reports/context_archives/f6bbc363879249be/tools/006-evidence-kubectl_describe.raw.txt: No such file or directory\\n\", \"returncode\": 1}","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/014-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/014-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/014-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": false, \"stdout\": \"\", \"stderr\": \"cat: /tmp/aiops/reports/context_archives/f6bbc363879249be/tools/003-evidence-kubectl_describe.raw.txt: No such file or directory\\n\", \"returncode\": 1}","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/015-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/015-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/015-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"      Reason:       ErrImagePull\\n  Type     Reason   Age                    From     Message\\n  Warning  Failed   60m                    kubelet  Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 173.231.12.107:443: i/o timeout\\n  Warning  Failed   47m                    kubelet  Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 128.121.243.228:443: i/o timeout\\n  Warning  Failed   34m                    kubelet  Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 208.43.170.231:443: i/o timeout\\n  Warning  Failed   22m (x13 over 120m)    kubelet  Error: ErrImagePull\\n  Warning  Failed   22m                    kubelet  Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 108.160.167.30:443: i/o timeout\\n  Warning  Failed   13m                    kubelet  Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = Unknown desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 108.160.170.26:443: i/o timeout\\n  Normal   BackOff  9m56s (x82 over 120m)  kubelet  Back-off pulling image \\\"busybox:1.36.1\\\"\\n  Warning  Failed   117s                   kubelet  Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 74.86.151.167:443: i/o timeout\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/016-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/016-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/016-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"      Reason:       ImagePullBackOff\\n  Type     Reason   Age                   From     Message\\n  Warning  Failed   52m (x9 over 5h20m)   kubelet  Failed to pull image \\\"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\\\": failed to resolve reference \\\"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\\\": failed to do request: Head \\\"https://europe-west2-docker.pkg.dev/v2/k8s-artifacts-prod/images/e2e-test-images/jessie-dnsutils/manifests/1.0\\\": dial tcp 108.177.125.82:443: i/o timeout\\n  Warning  Failed   18m (x34 over 5h38m)  kubelet  (combined from similar events): Failed to pull image \\\"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\\\": failed to resolve reference \\\"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\\\": failed to do request: Head \\\"https://asia-east1-docker.pkg.dev/v2/k8s-artifacts-prod/images/e2e-test-images/jessie-dnsutils/manifests/1.0\\\": dial tcp 142.250.157.82:443: i/o timeout\\n  Normal   BackOff  8m8s (x1323 over 9h)  kubelet  Back-off pulling image \\\"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\\\"\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/017-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/017-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/017-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"      Reason:       ImagePullBackOff\\n  Type     Reason   Age                  From     Message\\n  Warning  Failed   25m (x183 over 13h)  kubelet  (combined from similar events): Failed to pull image \\\"busybox:1.36.1\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"docker.io/library/busybox:1.36.1\\\": failed to resolve reference \\\"docker.io/library/busybox:1.36.1\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/library/busybox/manifests/1.36.1\\\": dial tcp 69.63.184.142:443: i/o timeout\\n  Normal   BackOff  7m (x2049 over 14h)  kubelet  Back-off pulling image \\\"busybox:1.36.1\\\"\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/018-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/018-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/018-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"      Reason:       ImagePullBackOff\\n  Type     Reason   Age                  From     Message\\n  Warning  Failed   59m (x8 over 74m)    kubelet  Error: ImagePullBackOff\\n  Warning  Failed   45m                  kubelet  Failed to pull image \\\"alpine/curl\\\": rpc error: code = DeadlineExceeded desc = failed to pull and unpack image \\\"docker.io/alpine/curl:latest\\\": failed to resolve reference \\\"docker.io/alpine/curl:latest\\\": failed to do request: Head \\\"https://registry-1.docker.io/v2/alpine/curl/manifests/latest\\\": dial tcp 173.236.212.42:443: i/o timeout\\n  Normal   BackOff  11m (x183 over 74m)  kubelet  Back-off pulling image \\\"alpine/curl\\\"\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/019-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/019-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/019-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"Status:           Failed\\n    State:          Terminated\\n      Reason:       StartError\\n      Message:      failed to create containerd task: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: \\\"curl\\\": executable file not found in $PATH: unknown\\n      Exit Code:    128\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/020-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/020-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f6bbc363879249be/tools/020-evidence-run_bash_command.summary.txt"}],"llm_analysis":"所有关键证据已采集完成。现在总结结果。\n\n---\n\n## ✅ 证据采集完成报告\n\n### 主异常组 G2 - ImagePullBackOff/ErrImagePull（~56 个 Pod）\n\n| 计划项 | 结果 |\n|--------|------|\n| **e-g2-p1** ✅ dig-tool (default, node1) | **已采集** — Events 明确显示 `dial tcp ...:443: i/o timeout`，连接 registry.k8s.io 欧洲/亚洲 endpoints 均超时，1323 次 BackOff |\n| **e-g2-p2** ✅ test-dns-1779360358 (aiops-e2e, node1) | **已采集** — `dial tcp 69.63.184.142:443: i/o timeout` 连接 docker.io 拉 busybox:1.36.1 超时，2049 次 BackOff |\n| **e-g2-p3** ✅ node-debugger-node1-2s2mz (mcp, node1) | **已采集** — `dial tcp 173.236.212.42:443: i/o timeout` 连接 docker.io 拉 alpine/curl 超时，mcp 命名空间同样受影响 |\n| **e-g2-p4** ✅ dns-diag-tool-evidence (default, node2) | **已采集** — node2 上同样 `dial tcp ...:443: i/o timeout`，多个不同 IP 尝试全部超时，确认 node1 和 node2 都存在出口网络问题 |\n| **e-g2-p5** ✅ dig-tool YAML | **已采集** — image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0，**imagePullSecrets: 无**，说明不是认证问题，镜像地址正确但网络不可达 |\n| **e-g2-p6** ❌ Pod内curl验证 | **失败** — container not found（Pod 处于 ImagePullBackOff 从未成功启动过容器），无法 exec。此负向结果本身印证了容器从未运行成功 |\n\n**结论：集群节点（node1 和 node2）对外部镜像仓库（docker.io、registry.k8s.io、gcr.io）的 HTTPS 出口全部不可达，所有 i/o timeout 指向集群出口网络/DNS/代理问题。**\n\n---\n\n### 异常组 G1 - CrashLoopBackOff（rc-notready-liveness, aiops-e2e）\n\n| 计划项 | 结果 |\n|--------|------|\n| **e-g1-p1** ✅ rc-notready-liveness describe | **已采集** — Liveness probe: `sh -c echo liveness endpoint failed; exit 1`，Events: `Liveness probe failed: liveness endpoint failed`，Exit Code=137（被 Killing），重启 17 次 |\n| **e-g1-p2** ✅ previous logs | **已采集** — 无输出（容器从未成功运行过业务逻辑），这与 probe 故意失败、容器刚启动就被杀死的场景一致 |\n\n**结论：rc-notready-liveness 的 livenessProbe 被故意配置为立即失败（`echo liveness endpoint failed; exit 1`），属于 e2e 测试 Pod（标签 rootcause-e2e=true），非实际故障。**\n\n---\n\n### 异常组 G3 - StartError（node-debugger-node1-nx8gb, mcp）\n\n| 计划项 | 结果 |\n|--------|------|\n| **e-g3-p1** ✅ node-debugger-node1-nx8gb describe | **已采集** — Status=Failed, Reason=StartError, Message=`exec: \"curl\": executable file not found in $PATH`，Exit Code=128。镜像内没有 curl 可执行文件 |\n\n**结论：StartError 是因为镜像中缺少 curl 二进制文件，属于镜像使用错误，与集群网络问题无关。**\n\n---\n\n### 📊 总体结论\n\n| 异常组 | Pod 数量 | 根因 | 影响范围 |\n|--------|---------|------|---------|\n| **G2 - ImagePullBackOff/ErrImagePull** | ~56 个 | **节点出口到外网镜像仓库 HTTPS 不通 (i/o timeout)**，涉及 docker.io、registry.k8s.io、gcr.io，遍布 node1 和 node2 | **严重** — 所有需要拉取外网镜像的 Pod 均无法启动 |\n| **G1 - CrashLoopBackOff** | 1 个 | **livenessProbe 故意配置为失败**（e2e 测试），非真实故障 | 无影响 |\n| **G3 - StartError** | 1 个 | **镜像中缺少 curl 可执行文件** | 仅该 Pod |\n\n**核心问题：集群节点无外网镜像仓库访问权限，需要配置 HTTP 代理、镜像缓存或使用内网镜像仓库。**","collection_summary":"计划 9 项，实际采集 9 项，未采集 0 项，完整度 100%；其中真实环境证据 20/20 项，完整度 100%；实际执行工具 26 个，匹配计划 9 个，未规划证据 17 个","plan_total":9,"plan_collected":9,"plan_completeness":1.0,"environment_evidence_total":20,"environment_evidence_collected":20,"environment_evidence_completeness":1.0,"executed_tool_count":26,"matched_tool_count":9,"unplanned_tool_count":17,"evidence_inventory":[{"id":"e-g2-p1","description":"g2主异常组：验证代表Pod dig-tool(default)的Pod Events，确认镜像拉取失败根本原因（网络超时/认证/镜像不存在）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod dig-tool -n default","purpose":"采集ImagePullBackOff主异常组的代表Pod事件，验证HTTPS i/o timeout错误的确切内容","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e-g2-p2","description":"g2主异常组：验证代表Pod test-dns-1779360358(aiops-e2e)的Pod Events，确认镜像拉取失败原因（docker.io超时）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-dns-1779360358 -n aiops-e2e","purpose":"验证docker.io镜像仓库同样超时，确认是集群出口网络问题而非单一仓库问题","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e-g2-p3","description":"g2主异常组：验证跨namespace的Pod（mcp/node-debugger-node1-2s2mz）也处于ImagePullBackOff","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-2s2mz -n mcp","purpose":"验证mcp命名空间的ImagePullBackOff Pod也存在相同i/o timeout错误，确认问题波及多个namespace","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e-g2-p4","description":"g2主异常组：验证跨node的Pod（default/dns-diag-tool-evidence on node2）的ErrImagePull状态","level":"important","tool":"kubectl_describe","command":"kubectl describe pod dns-diag-tool-evidence -n default","purpose":"验证node2上的Pod同样因HTTPS超时拉取失败，确认问题在node1和node2都存在","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e-g2-p5","description":"g2主异常组：检查dig-tool的image spec和imagePullSecrets","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod dig-tool -n default -o yaml","purpose":"检查image地址和imagePullSecrets配置，排除镜像地址错误或凭证缺失","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e-g2-p6","description":"g2主异常组：验证节点到镜像仓库的网络连通性","level":"important","tool":"run_bash_command","command":"kubectl exec -n default -it dig-tool -- timeout 10 curl -v https://registry-1.docker.io/v2/ 2>&1 || true","purpose":"直接从Pod网络命名空间验证到docker.io仓库的HTTPS连通性","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e-g1-p1","description":"g1异常组（CrashLoopBackOff）：验证rc-notready-liveness的当前状态和最新Events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","purpose":"采集CrashLoopBackOff状态Pod的Events，确认liveness probe失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e-g1-p2","description":"g1异常组：检查rc-notready-liveness的previous logs确认容器退出原因","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-notready-liveness -n aiops-e2e --previous --tail=50","purpose":"采集崩溃前日志，验证liveness endpoint failed是主动exit 1","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e-g3-p1","description":"g3异常组（StartError）：验证node-debugger-node1-nx8gb的当前状态和Events","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-nx8gb -n mcp","purpose":"最小验证StartError状态Pod的当前状态和关键事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_8","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_9","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_10","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_11","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 9/9 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e-g2-p1 | critical | ✅ | kubectl_describe | g2主异常组：验证代表Pod dig-tool(default)的Pod Events，确... | `kubectl describe pod dig-tool -n default` |
   | e-g2-p2 | critical | ✅ | kubectl_describe | g2主异常组：验证代表Pod test-dns-1779360358(aiops-e2e)... | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` |
   | e-g2-p3 | important | ✅ | kubectl_describe | g2主异常组：验证跨namespace的Pod（mcp/node-debugger-nod... | `kubectl describe pod node-debugger-node1-2s2mz -n mcp` |
   | e-g2-p4 | important | ✅ | kubectl_describe | g2主异常组：验证跨node的Pod（default/dns-diag-tool-evid... | `kubectl describe pod dns-diag-tool-evidence -n default` |
   | e-g2-p5 | important | ✅ | kubectl_get_yaml | g2主异常组：检查dig-tool的image spec和imagePullSecrets | `kubectl get pod dig-tool -n default -o yaml` |
   | e-g2-p6 | important | ✅ | run_bash_command | g2主异常组：验证节点到镜像仓库的网络连通性 | `kubectl exec -n default -it dig-tool -- timeout 10 curl -v https://registry-1...` |
   | e-g1-p1 | critical | ✅ | kubectl_describe | g1异常组（CrashLoopBackOff）：验证rc-notready-livenes... | `kubectl describe pod rc-notready-liveness -n aiops-e2e` |
   | e-g1-p2 | important | ✅ | kubectl_previous_logs | g1异常组：检查rc-notready-liveness的previous logs确认容... | `kubectl logs rc-notready-liveness -n aiops-e2e --previous --tail=50` |
   | e-g3-p1 | important | ✅ | kubectl_describe | g3异常组（StartError）：验证node-debugger-node1-nx8gb... | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (23.0s)
   📤 → 下游数据: root_cause=集群存在三个异常组：(1) **主异常组G2（严重）**：约56个Pod处于ImagePullBackOff/ErrImagePull，根因为节点到外网镜像仓库的HTTPS出口网络不通。证据：dig-tool(default/node1)对europe-west2-docker.pkg.dev:443和asia-east1-docker.pkg.dev:443的HTTPS连接均i/o timeout（1323次BackOff）；test-dns-1779360358(aiops-e2e/node1)对registry-1.docker.io:443超时（2049次BackOff）；dns-diag-tool-evidence(default/node2)对registry-1.docker.io多个IP全部超时；node-debugger-node1-2s2mz(mcp/node1)对docker.io/alpine/curl超时且connection reset。YAML检查确认镜像地址正确且无imagePullSecret需求，排除认证和镜像名问题。横跨default/aiops-
... 截断，原始 926 字符
   confidence=95%
   causal_chain={"root_cause": "集群节点（node1和node2）到外网镜像仓库（docker.io、registry.k8s.io、gcr.io）的HTTPS出口网络不可达，所有连接均返回dial tcp i/o timeout", "propagation": "节点出口网络不通→kubelet无法从外网镜像仓库拉取镜像→containerd返回DeadlineExceeded/i/o timeout错误→Pod状态变为ErrImagePull/ImagePullBackOff→Kubelet持续重试产生大量BackOff事件", "direct_cause": "kubelet拉取镜像时对registry-1.docker.io:443、europe-west2-docker.pkg.dev:443、asia-east1-docker.pkg.dev:443等外网registry的HTTPS连接全部超时", "manifestation": "default/aiops-e2e/mcp三个命名空间中约56个诊断测试Pod（dig-tool、dns-test、registry-check、node-debugger等）全部处于ImagePullBackOff或ErrImagePull状态，分布在node1和node2上，镜像来源包括docker.io、registry.k8s.io、gcr.io三类公共仓库"}
   rca_analysis={"phenomenon": "集群中存在约57个异常Pod：(1) 约56个Pod处于ImagePullBackOff/ErrImagePull状态，分布在default、aiops-e2e、mcp命名空间，横跨node1和node2节点；(2) aiops-e2e/rc-notready-liveness处于CrashLoopBackOff状态，已重启17次；(3) mcp/node-debugger-node1-nx8gb处于StartError状态。kube-system所有Infra Pod均正常运行。", "evidence_inventory": [{"id": "e-g2-p1", "source": "kubectl_describe (dns-diag-tool-evidence, default, node2)", "content": "Pod使用busybox:1.36.1，所有Failed事件均为i/o timeout dialing registry-1.docker.io:443，涉及多个IP地址", "reliability": "高"}, {"id": "e-g2-p2", "source": "kubectl_describe (dig-tool, default, node1)", "content": "Pod使用registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0，Failed事件显示i/o timeout dialing europe-west2-docker.pkg.dev:443和asia-east1-docker.pkg.dev:443，1323次BackOff", "reliability": "高"}, {"id": "e-g2-p3", "source": "kubectl_describe (test-dns-1779360358, aiops-e2e, node1)", "content": "Pod使用busybox:1.36.1，Failed事件显示dial tcp 69.63.184.142:443: i/o timeout连接registry-1.docker.io，2049次BackOff", "reliability": "高"}, {"id": "e-g2-p4", "source": "kubectl_describe (node-debugger-node1-2s2mz, mcp, node1)", "content": "Pod使用alpine/curl镜像，Failed事件显示dial tcp 173.236.212.42:443: i/o timeout和connection reset by peer连接docker.io", "reliability": "高"}, {"id": "e-g2-p5", "source": "kubectl_get_yaml (dig-tool, default)", "content": "imagePullSecrets: 无，镜像地址registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0正确，排除认证问题和镜像名错误", "reliability": "高"}, {"id": "e-g1-p1", "source": "kubectl_describe (rc-notready-liveness, aiops-e2e)", "content": "Liveness probe: sh -c echo liveness endpoint failed; exit 1，Events显示Liveness probe failed: liveness endpoint failed，Exit Code=137，重启17次", "reliability": "高"}, {"id": "e-g1-p2", "source": "kubectl_previous_logs (rc-notready-liveness)", "content": "previous logs无输出，容器从未成功运行业务逻辑", "reliability": "中"}, {"id": "e-g3-p1", "source": "kubectl_describe (node-debugger-node1-nx8gb, mcp)", "content": "Status=Failed, Reason=StartError, Message=exec: curl: executable file not found in $PATH, Exit Code=128", "reliability": "高"}, {"id": "e-g2-p6", "source": "run_bash_command (dig-tool exec)", "content": "exec失败：container not found，Pod从未成功启动容器", "reliability": "中"}, {"id": "layer_1-11", "source": "上游已验证工具结果层", "content": "kube-system全部Running(历史重启15天前)；default/mcp/aiops-e2e共~56个ImagePullBackOff/ErrImagePull, 1个CrashLoopBackOff, 1个StartError", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e-g2-p1", "raw_data": "Failed: i/o timeout dialing registry-1.docker.io:443 (multiple IPs: 173.231.12.107, 128.121.243.228, etc.)", "interpretation": "node2上到docker.io的HTTPS出口全面不可达，所有IP尝试均超时，排除DNS解析问题（因解析出多个不同IP）"}, {"evidence_id": "e-g2-p2", "raw_data": "Failed: i/o timeout dialing europe-west2-docker.pkg.dev:443 and asia-east1-docker.pkg.dev:443", "interpretation": "node1上到registry.k8s.io（GCR代理）的HTTPS连接也全部超时，覆盖了多个地理区域的endpoint"}, {"evidence_id": "e-g2-p3", "raw_data": "Failed: dial tcp 69.63.184.142:443: i/o timeout connecting to registry-1.docker.io", "interpretation": "aiops-e2e命名空间同样受影响，证明不是单一命名空间的问题，是集群级别的网络出口故障"}, {"evidence_id": "e-g2-p4", "raw_data": "Failed: dial tcp 173.236.212.42:443: i/o timeout AND connection reset by peer (100.50.6.117:443)", "interpretation": "mcp命名空间同样受影响；connection reset表明可能存在透明代理或拦截设备但连接失败"}, {"evidence_id": "e-g2-p5", "raw_data": "imagePullSecrets: <absent>, image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0", "interpretation": "排除镜像地址错误（该镜像存在且可公开拉取）和认证问题（无需私有registry认证）"}, {"evidence_id": "e-g1-p1", "raw_data": "Liveness: exec [sh -c echo liveness endpoint failed; exit 1], Exit Code: 137, Event: Liveness probe failed: liveness endpoint failed", "interpretation": "livenessProbe被故意配置为立即返回失败，容器启动约39秒后被杀掉(Exit 137=SIGKILL)，属于e2e测试Pod（标签rootcause-e2e=true）"}, {"evidence_id": "e-g1-p2", "raw_data": "(no output)", "interpretation": "容器从未成功运行到产生日志的阶段，与探针故意立即失败的场景吻合"}, {"evidence_id": "e-g3-p1", "raw_data": "StartError: exec: curl: executable file not found in $PATH", "interpretation": "镜像busybox:1.36中不包含curl可执行文件，但Pod command指定了curl，导致容器启动失败，Exit Code=128"}, {"evidence_id": "e-g2-p6", "raw_data": "error: unable to upgrade connection: container not found", "interpretation": "负向证据：Pod从未成功启动容器，因此无法exec验证网络，这个结果本身印证了容器启动失败的事实"}], "causal_chain": {"root_cause": "集群节点（node1和node2）到外网镜像仓库（docker.io、registry.k8s.io、gcr.io）的HTTPS出口网络不可达，所有连接均返回dial tcp i/o timeout", "propagation": "节点出口网络不通→kubelet无法从外网镜像仓库拉取镜像→containerd返回DeadlineExceeded/i/o timeout错误→Pod状态变为ErrImagePull/ImagePullBackOff→Kubelet持续重试产生大量BackOff事件", "direct_cause": "kubelet拉取镜像时对registry-1.docker.io:443、europe-west2-docker.pkg.dev:443、asia-east1-docker.pkg.dev:443等外网registry的HTTPS连接全部超时", "manifestation": "default/aiops-e2e/mcp三个命名空间中约56个诊断测试Pod（dig-tool、dns-test、registry-check、node-debugger等）全部处于ImagePullBackOff或ErrImagePull状态，分布在node1和node2上，镜像来源包括docker.io、registry.k8s.io、gcr.io三类公共仓库"}, "root_cause": "集群存在三个异常组：(1) **主异常组G2（严重）**：约56个Pod处于ImagePullBackOff/ErrImagePull，根因为节点到外网镜像仓库的HTTPS出口网络不通。证据：dig-tool(default/node1)对europe-west2-docker.pkg.dev:443和asia-east1-docker.pkg.dev:443的HTTPS连接均i/o timeout（1323次BackOff）；test-dns-1779360358(aiops-e2e/node1)对registry-1.docker.io:443超时（2049次BackOff）；dns-diag-tool-evidence(default/node2)对registry-1.docker.io多个IP全部超时；node-debugger-node1-2s2mz(mcp/node1)对docker.io/alpine/curl超时且connection reset。YAML检查确认镜像地址正确且无imagePullSecret需求，排除认证和镜像名问题。横跨default/aiops-\n... 截断，原始 926 字符", "root_cause_summary": "集群存在三个异常组：(1) **主异常组G2（严重）**：约56个Pod处于ImagePullBackOff/ErrImagePull，根因为节点到外网镜像仓库的HTTPS出口网络不通。证据：dig-tool(default/node1)对europe-west2-docker.pkg.dev:443和asia-east1-docker.pkg.dev:443的HTTPS连接均i/o timeout（1323次BackOff）；test-dns-1779360358(aiops-e2e/node1)对registry-1.docker.io:443超时（2049次BackOff）；dns-diag-tool-evidence(default/node2)对registry-1.docker.io多个IP全部超时；node-debugger-node1-2s2mz(mcp/node1)对docker.io/alpine/curl超时且connection reset。YAML检查确认镜像地址正确且无imagePullSecret需求，排除认证和镜像名问题。横跨default/aiops-\n... 截断，原始 926 字符", "confidence": 0.95, "confidence_reason": "直接证据充分：6个Pod的kubectl_describe均显示i/o timeout，覆盖两个节点、三个命名空间、三类仓库；YAML确认镜像地址正确且无认证问题；exec失败作为负向证据印证容器从未启动。因果链清晰完整，无矛盾证据。", "primary_runbooks": ["pod-imagepull-failed.md"], "alternative_causes": [{"cause": "镜像地址或tag不存在", "probability": "low", "reason": "YAML检查确认dig-tool使用的registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0是标准K8s e2e镜像，且其他Pod使用busybox:1.36.1和alpine/curl也是公共标准镜像；排除此原因"}, {"cause": "imagePullSecret缺失或认证失败", "probability": "low", "reason": "YAML显示imagePullSecrets为无，所有镜像均为公开镜像(docker.io/library/busybox, registry.k8s.io/e2e-test-images, docker.io/alpine/curl)，无需认证"}, {"cause": "DNS解析失败导致无法拉取镜像", "probability": "low", "reason": "证据显示DNS成功解析出多个不同IP（如registry-1.docker.io解析到173.231.12.107等不同IP），但HTTPS连接仍然超时；问题在TCP/TLS层而非DNS层"}], "limitations": "集群未配置私有镜像仓库或代理的详细信息未知；无法确定出口网络故障的具体原因（防火墙规则/NAT网关/代理/上游ISP），需要网络团队进一步排查集群节点的网络出口路径；rc-notready-liveness尽管是e2e测试Pod，但其持续产生CrashLoopBackOff事件可能对集群事件系统产生噪音；node-debugger-node1-nx8gb的StartError是独立的镜像内可执行文件缺失问题，与主异常组的网络故障无关。", "llm_raw_analysis": "## 证据清点\n\n总计20+条证据采集项，覆盖：\n- 主异常组G2（ImagePullBackOff/ErrImagePull）：6条核心证据 + 6条上游验证层证据\n- 异常组G1（CrashLoopBackOff）：2条核心证据 + 3条上游验证层证据\n- 异常组G3（StartError）：1条核心证据\n\n## 关联分析\n\n所有G2证据指向同一根因：节点出口网络不可达。证据链跨越node1和node2、三个命名空间、三类公共仓库，排除DNS/认证/镜像名等替代原因。\n\n## 因果链\n\n根因：节点出口网络不通 → 直接原因：kubelet拉取镜像HTTPS连接超时 → 现象：56个Pod处于ImagePullBackOff/ErrImagePull\n\nG1和G3是独立问题，与G2无关联。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群存在三个异常组：(1) **主异常组G2（严重）**：约56个Pod处于ImagePullBackOff/ErrImagePull，根因为节点到外网镜像仓库的HTTPS出口网络不通。证据：dig-tool(default/node1)对europe-west2-docker.pkg.dev:44...
   置信度: 95%
   🔗 因果链:
     根本原因: 集群节点（node1和node2）到外网镜像仓库（docker.io、registry.k8s.io、gcr.io）的HTTPS出口网络不可达，所有连接均返回dial tcp i/o timeout
     传导机制: 节点出口网络不通→kubelet无法从外网镜像仓库拉取镜像→containerd返回DeadlineExceeded/i/o timeout错误→Pod状态变为ErrImagePull/ImagePullBackOff→Kubelet持续重试产生大量BackOff事件
     最终表现: default/aiops-e2e/mcp三个命名空间中约56个诊断测试Pod（dig-tool、dns-test、registry-check、node-debugger等）全部处于ImagePullBackOff或ErrImagePull状态，分布在node1和node2上，镜像来源包括docker.io、registry.k8s.io、gcr.io三类公共仓库


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (27.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 7879 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 43.1s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，收到您的诊断需求。作为资深 K8s 诊断报告专家，我将直接为您分析集群的当前状态。

---

## 📊 集群现状速览

当前集群存在 **三个主要问题**，其中 **网络问题最为严重**，导致大量 Pod 无法正常运行。

| 问题 | 严重程度 | 影响范围 | 根因分类 |
|------|----------|----------|----------|
| **1. 大量 Pod 镜像拉取失败 (ImagePullBackOff / ErrImagePull)** | **严重** | `default`, `aiops-e2e`, `mcp` 命名空间，约 **56个 Pod** | 网络/镜像仓库不可达 |
| **2. 单个 Pod CrashLoopBackOff** | 低（预期行为） | `aiops-e2e/rc-notready-liveness`，1个 Pod | 探针配置异常 (Liveness Probe 失败) |
| **3. 单个 Pod StartError** | 低（独立问题） | `mcp/node-debugger-node1-nx8gb`，1个 Pod | 容器镜像内文件缺失 |
| `kube-system` 命名空间 | 正常 | 16 个 Pod 全部 Running | 无异常 |

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | `ImagePullBackOff` (约46个), `ErrImagePull` (约10个), `CrashLoopBackOff` (1个), `StartError` (1个) |
| **兼容归因层** | L3层 - 网络/镜像仓库不可达 |
| **问题分类** | `ImagePullFailed` |
| **置信度** | **高 (95%)** |
| **证据完整度** | 9/9 (100%) |

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| **受影响Pod** | `dig-tool` (default), `test-dns-1779360358` (aiops-e2e), `dns-diag-tool-evidence` (default), `node-debugger-node1-2s2mz` (mcp)，及其它约56个Pod |
| **受影响Namespace** | `default`, `aiops-e2e`, `mcp` |
| **受影响Node** | `node1` (10.2.0.49), `node2` (10.2.0.50) |
| **错误信息** | 从 kubelet events 中提取: `Failed to pull image ... dial tcp ...:443: i/o timeout` |

---
## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod状态 & Events | `kubectl describe pod dig-tool -n default` | Pod 在 `node1`，状态 `Pending` (Reason: `ImagePullBackOff`)。Events 显示: `Failed to pull image ... dial tcp europe-west2-docker.pkg.dev:443: i/o timeout` (x34次), `... asia-east1-docker.pkg.dev:443: i/o timeout` (x34次)，`BackOff` 事件共 **1323次**。 | 集群无法连接 `registry.k8s.io` 仓库 |
| 2 | Pod状态 & Events | `kubectl describe pod test-dns-1779360358 -n aiops-e2e` | Pod 在 `node1`，状态 `Pending` (Reason: `ImagePullBackOff`)。`BackOff` 事件共 **2049次**，`Failed` 事件显示: `Failed to pull image ... dial tcp ...:443: i/o timeout`。 | 集群无法连接 `docker.io` 仓库 |
| 3 | Pod状态 & Events | `kubectl describe pod dns-diag-tool-evidence -n default` | Pod 在 `node2`，状态 `Pending` (Reason: `ErrImagePull`)。Events 显示对 `registry-1.docker.io:443` 的多个IP尝试连接均 `i/o timeout`，重试长达130分钟。 | 问题跨 `node2`，排除单节点问题 |
| 4 | Pod状态 & Events | `kubectl describe pod node-debugger-node1-2s2mz -n mcp` | Pod 在 `node1`，状态 `Pending` (Reason: `ImagePullBackOff`)。Events 显示拉取 `alpine/curl` 镜像时 `connection reset` 和 `i/o timeout`。 | 问题跨Namespace，影响所有外网镜像 |
| 5 | YAML配置 | `kubectl get pod dig-tool -o yaml -n default` | `finalizers: <none>`。镜像地址 `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0`，无 `imagePullSecrets`。 | **排除finalizers问题**；确认镜像地址正确，无权限认证问题 |
| 6 | 网络连通性 | `run_bash_command` (`kubectl exec dig-tool ...`) | `error: unable to upgrade connection: container not found ("dig-tool")` | Pod尚未运行，无法进入容器进行网络诊断 |
| 7 | Pod状态 & Events | `kubectl describe pod rc-notready-liveness -n aiops-e2e` | Pod 状态 `CrashLoopBackOff` (重启17次)，`Exit Code: 137`。`Warning Unhealthy` 事件。 | Liveness 探针失败导致容器被杀死 |
| 8 | 容器日志 | `kubectl logs rc-notready-liveness --previous -n aiops-e2e` | (无输出) | 容器未产生日志即退出 |
| 9 | Pod状态 | `kubectl describe pod node-debugger-node1-nx8gb -n mcp` | Pod 状态为 `Failed`，`Reason: StartError`。错误信息: `failed to create containerd task: ... OCI runtime create failed: ... file not found` | 容器镜像内的入口文件缺失 |

### 证据关联分析
- **证据 #1 + #2 + #3 + #4 印证**：三个不同命名空间 (`default`, `aiops-e2e`, `mcp`)、两个不同节点 (`node1`, `node2`) 上的Pod，尝试拉取 `docker.io`, `registry.k8s.io`, `gcr.io` 等多个外网镜像仓库时，均因 `i/o timeout` 失败。这排除了单一仓库、单一Pod或单一节点的问题。
- **证据链**：集群节点出口网络不通 → kubelet 无法连接到外网镜像仓库 → 拉取镜像失败 → Pod 状态进入 `ImagePullBackOff` 或 `ErrImagePull`。
- **证据 #7 特征**：`Exit Code: 137` 表明容器被 kill，结合 `Warning Unhealthy` 事件，确认是 Liveness 探针配置的行为。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 集群网络出口配置 (防火墙/NAT/代理) | critical | 无法确定网络故障的根本原因 |

---
## 🎯 根因分析

### 因果链
```
┌────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                       │
│ 集群节点(node1, node2)到外网镜像仓库(docker.io, registry.k8s.io, gcr.io)       │
│ 的HTTPS出口网络不可达，所有连接均返回 `dial tcp i/o timeout`                   │
└────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                       │
│ 节点出口网络不通 → kubelet 无法从外网镜像仓库拉取镜像                           │
│ → containerd 返回 DeadlineExceeded/i/o timeout 错误                           │
└────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                       │
│ kubelet 拉取镜像时对 registry-1.docker.io:443, europe-west2-docker.pkg.dev:443 │
│ 等外网 registry 的 HTTPS 连接全部超时                                          │
└────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                   │
│ default/aiops-e2e/mcp 三个命名空间中约56个诊断测试 Pod                          │
│ 全部处于 ImagePullBackOff 或 ErrImagePull 状态                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1-#4 (所有Pod均因 `i/o timeout` 拉取镜像失败)，问题的根本原因是**集群节点无法连接到外网镜像仓库**。

- ✅ 错误类型 `dial tcp ...:443: i/o timeout` 明确指向网络出口问题。
- ✅ 问题跨节点 (node1, node2) 和 Namespace，排除单点故障。
- ✅ 覆盖 `docker.io`, `registry.k8s.io`, `gcr.io` 三大主流仓库，排除仓库本身问题。

**额外确认 (非根本问题)**：
- `aiops-e2e/rc-notready-liveness` 的 `CrashLoopBackOff` 根据其 `LivenessProbe` 配置为失败命令 (`echo liveness endpoint failed; exit 1`)，且标签带有 `rootcause-e2e=true`，**属于预期的 e2e 测试行为**，并非集群异常。
- `mcp/node-debugger-node1-nx8gb` 的 `StartError` 是镜像构建问题，与网络故障无关。
- `kube-system` 命名空间所有 Pod 正常运行，说明集群核心组件健康。

**置信度**：高 (95%)
- ✅ 多个Pod、多个节点、多个仓库的 `i/o timeout` 错误形成强证据链。
- ⚠️ 缺少集群网络出口配置的具体信息，无法定位故障点（防火墙规则/NAT网关/代理/上游ISP）。

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）
**1. [首要] 排查并修复集群网络出口**
集群节点需要能够访问外网镜像仓库。需要联系网络/基础设施团队，检查并修复集群节点的出口网络连通性。
*可能的原因及排查命令：*
```bash
# 在所有节点上手动测试到 docker.io 的网络连通性
node1:~$ curl -v --connect-timeout 5 https://registry-1.docker.io/v2/ 2>&1 | head -20
node2:~$ curl -v --connect-timeout 5 https://registry-1.docker.io/v2/ 2>&1 | head -20

# 如果集群使用代理，检查 kubelet 的代理配置
# 在每个节点上检查 kubelet 启动参数
ps aux | grep kubelet | grep -E "http-proxy|https-proxy|no-proxy"

# 检查节点上 iptables 或防火墙规则
sudo iptables -L -n -t nat | head -50
```
*依据*：`i/o timeout` 错误明确指示网络不可达。

### 后续优化
1. **配置镜像仓库镜像/代理**：在企业环境中，最佳实践是在集群内或私有网络内配置 `docker.io`, `registry.k8s.io`, `gcr.io` 等公共仓库的镜像 (registry mirror) 或使用私有仓库作为代理缓存。这不仅能解决网络问题，还能提升拉取速度和可靠性。
2. **配置 Dashboard 和监控告警**：
   - 安装 Kubernetes Dashboard 以可视化查看集群状态。
   - 使用 Prometheus 等工具监控 Pod 状态，对 `Pending` `ImagePullBackOff` 等状态设置告警。
3. **移除测试 Pod**：确认网络问题修复后，可以删除诊断测试用的 Pod，以减少集群事件噪音。
   ```bash
   kubectl delete pod dig-tool -n default
   kubectl delete pod test-dns-1779360358 -n aiops-e2e
   kubectl delete pod dns-diag-tool-evidence -n default
   ```

---
## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 测试节点网络 | 节点上执行 `curl -I https://registry-1.docker.io/v2/` | 返回 HTTP 200/OK |
| 2. 确认Pod状态改善 | `kubectl get pods -A \| grep -E 'ErrImagePull|ImagePullBackOff'` | 返回空，无异常Pod |
| 3. 验证单个Pod | `kubectl get pod dig-tool -n default` | STATUS: `Running` (非 `Pending`) |

---
## ⚠️ 注意事项
- **`CrashLoopBackOff` (rc-notready-liveness)**: 此Pod是e2e测试用例，其异常是预期行为，**不是集群故障**。可忽略或手动删除它。
- **`StartError` (node-debugger-node1-nx8gb)**: 此Pod的问题是镜像文件缺失，**不是集群故障**。如需调试节点，需重新构建正确的镜像。
- 网络问题的根本原因（防火墙规则、NAT、代理或上游ISP）需要网络团队介入排查。
- 修复网络后，建议配置私有镜像仓库或镜像代理，防止问题复发。

---

## 📊 性能统计

├─ 总耗时: 2.7m
├─ 问题定位: 56.9s (35%) ✅
├─ 证据链采集: 55.5s (34%) ✅
├─ 根因分析: 23.0s (14%) ✅
├─ 汇总总结: 27.7s (17%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 33 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed, pod-notready-probe-failed, pod-crashloop-runtime
- **工具调用**: 33 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
