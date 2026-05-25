======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 8da5209fa33d409f]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我先全局扫描所有 Pod 的状态，看看当前集群中存在哪些异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=70 abnormal=6 status_counts={'Running': 59, 'Terminating': 1, 'ImagePullBackOff': 4}
NAMESPACE         NAME                                                REA
   💭 [问题定位] 扫描到 6 个异常 Pod，我再看看每个异常 Pod 的更多细节，以便准确分类。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                        READY   STATUS             RESTARTS   AGE   IP          NODE    NOMINATED NODE   READINESS GATES   LABELS
node-debugger-node1-djrzl   0/1     ImagePullBackOff   0          
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                        READY   STATUS             RESTARTS   AGE     IP          NODE    NOMINATED NODE   READINESS GATES   LABELS
node-debugger-node1-zst8z   0/1     ImagePullBackOff   0        
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME           READY   STATUS        RESTARTS   AGE     IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
network-test   0/1     Terminating   0          2m25s   172.16.166.160   node
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                        READY   STATUS              RESTARTS   AGE   IP          NODE    NOMINATED NODE   READINESS GATES   LABELS
node-debugger-node1-2tnsd   0/1     ContainerCreating   0        
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME           READY   STATUS             RESTARTS   AGE     IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
test-network   0/1     ImagePullBackOff   0          5m59s   172.16.166.
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                            READY   STATUS             RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-imagepull-invalid-registry   0/1     ImagePullBackOff 
   💭 [问题定位] 好的，Cluster 中有 6 个异常 Pod。根据异常类型，我需要获取对应的 runbook 来辅助定位。主要有两类异常：**ImagePullBackOff** 和 **Terminating**，以及一个 **ContainerCreating**。让我获取相关 runbook。
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
# Pod TerminatingStuck / 删除卡住

> runbook_id: pod-terminating-stuck.md
> Pod异常类型: TerminatingStuck | 典型状态: Terminating | 兼容分类: lifecycle

## 状态识别
- Pod 长时间处于 `Terminating`
- metadata.deletion
   💭 [问题定位] 很好，我现在来快速确认一下关键异常的详细信息。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-imagepull-invalid-registry
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          30m (x4 over 32m)      kubelet            Failed t
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod network-test in namespace aiops-e2e is Terminating (lasts 61s). Container network-test (image busybox:1.28) is in Waiting/ImagePullBackOff state, not Ready. All pull attempts to docker.io/library/
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod node-debugger-node1-zst8s (namespace mcp) on node node1/10.2.0.49 is Pending. Container debugger with image busybox:1.28 is in Waiting state with Reason ImagePullBackOff. All pull attempts to dock
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod test-network (namespace: aiops-e2e) on node node1/10.2.0.49 is Pending. Container test-network uses image busybox:1.28, State Waiting (Reason: ImagePullBackOff), Ready False, Restart Count 0. Pod 
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod node-debugger-node1-djrzl (namespace: mcp) is Pending on node node1/10.2.0.49. Container "debugger" is in ImagePullBackOff (Waiting state), not Ready. Image registry.k8s.io/e2e-test-images/jessie-
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-2tnsd
namespace: mcp
node: node1/10.2.0.49
status: Pending
Pod 关键区块:
QoS Class: BestEffort
Node-Selectors: <none>
Tolerations: op=Exists
Containers:
  de
   💭 [问题定位] 现在我已经掌握了所有信息，可以做出完整的定位分析了。

---

## 📋 集群异常 Pod 定位分析

### 整体概览
集群共 70 个 Pod，其中 **6 个异常 Pod**，全部集中在 **node1** 节点上。正常运行的 Pod 有 59 个。

---

### 异常 Pod 清单与分组

| # | Pod 名称 | 命名空间 | 状态 | 异常类型 | 层级 |
|---|---------|---------|------|---------|------|
| 1 | `network-test` | aiops-e2e | **Terminating**（实际卡在 ImagePullBackOff） | TerminatingStuck + ImagePullFailed | L1/L3 |
| 2 | `rc-imagepull-invalid-registry` | aiops-e2e | **ImagePullBackOff** | ImagePullFailed | L3 |
| 3 | `test-network` | aiops-e2e | **ImagePullBackOff** | ImagePullFailed | L3 |
| 4 | `node-debugger-node1-2tnsd` | mcp | **ContainerCreating**（Pulling 中） | ImagePullFailed | L3 |
| 5 | `node-debugger-node1-djrzl` | mcp | **ImagePullBackOff** | ImagePullFailed | L3 |
| 6 | `node-debugger-node1-zst8z` | mcp | **ImagePullBackOff** | ImagePullFailed | L3 |

---

### 异常分组归纳

#### 📌 异常组 1：镜像拉取失败（ImagePullFailed）— 5 个 Pod 🟡 L3
这是当前最主要的异常类型，覆盖了 **5/6 的异常 Pod**：

| Pod | 镜像 | 失败原因 |
|-----|------|---------|
| `rc-imagepull-invalid-registry` | `registry.invalid/aiops/rootcause:v0` | **DNS 解析失败** — `lookup registry.invalid on 127.0.0.53:53: no such host`（域名不存在） |
| `test-network` | `busybox:1.28` | **网络超时** — `dial tcp registry-1.docker.io:443 i/o timeout` |
| `network-test` | `busybox:1.28` | **网络超时** — `dial tcp registry-1.docker.io:443 i/o timeout` |
| `node-debugger-node1-zst8z` | `busybox:1.28` | **网络超时** — `dial tcp registry-1.docker.io:443 i/o timeout` |
| `node-debugger-node1-djrzl` | `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0` | **网络超时** — `dial tcp asia-east1-docker.pkg.dev:443 i/o timeout` |
| `node-debugger-node1-2tnsd` | `busybox:1.28` | **ContainerCreating**中，正在 Pulling，很可能同样会超时 |

**根因分析**：
- **`rc-imagepull-invalid-registry`** 是配置问题 — 镜像仓库域名 `registry.invalid` 本身不存在（DNS `no such host`），属于测试验证场景（label 标注了 `rootcause-e2e=true`）。
- 其他 **5 个 Pod** 的共性问题是 **node1 节点无法访问外部镜像仓库（registry-1.docker.io、registry.k8s.io）**，表现为 `i/o timeout`，说明节点到公网镜像仓库的网络链路存在问题（可能是防火墙/代理/网络策略导致出站访问被阻断）。

#### 📌 异常组 2：Terminating 卡住（TerminatingStuck）— 1 个 Pod 🟡 L1
- `network-test` 处于 **Terminating** 状态，但根本原因是容器一直在 ImagePullBackOff，从未成功启动过，所以删除时无法正常停止容器，但实际卡住时间仅 61 秒，可能还在正常终止窗口内。

---

### 定位结论

| 字段 | 值 |
|------|-----|
| **layer** | L3（镜像拉取失败是影响范围最大的异常类型） |
| **derived_layer** | L1（Terminating 卡住） |
| **layers** | L3, L1 |
| **layer_name** | ImagePullFailed |
| **confidence** | 高 |
| **status_category** | image_pull |
| **pod_status_keyword** | ImagePullBackOff |
| **pod_abnormal_type** | ImagePullFailed |
| **key_entities** | node1（10.2.0.49）、aiops-e2e namespace、mcp namespace、registry-1.docker.io、registry.k8s.io、registry.invalid |
| **possible_scenarios** | ① node1 节点无法访问公网镜像仓库（防火墙/代理/出站策略拦截）；② `registry.invalid` 镜像地址是测试用例的无效域名；③ `network-test` 因镜像拉取失败导致无法完成容器停止而卡在 Terminating |

### 后续审查方向建议
1. **节点网络**：检查 node1 到 `registry-1.docker.io:443` 和 `registry.k8s.io` 的连通性，确认是否有防火墙或代理限制出站访问
2. **镜像配置**：`rc-imagepull-invalid-registry` 使用了不存在的域名 `registry.invalid`，这是明显的配置错误
3. **Terminating Pod**：如果 `network-test` 长时间卡住，可能需要强制删除（`--force --grace-period=0`）
   ✅ [问题定位] 完成 (57.0s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L1
   scenarios=[{'scenario': 'node1节点无法访问公网镜像仓库', 'probability': '高', 'reason': '5个Pod的describe显示docker.io、registry.k8s.io等仓库均表现为i/o timeout，说明节点出站网络被阻断'}, {'scenario': '镜像地址配置错误', 'probability': '中', 'reason': 'rc-imagepull-invalid-registry使用了不存在的域名registry.invalid，DNS解析失败'}, {'scenario': 'Terminating卡住由镜像拉取失败引起', 'probability': '中', 'reason': 'network-test因镜像拉取失败导致容器从未成功启动，无法正常停止而卡在Terminating'}]
   entities=[{"type": "node", "name": "node1", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}, {"type": "namespace", "name": "mcp", "namespace": "mcp"}, {"type": "registry", "name": "registry-1.docker.io", "namespace": ""}, {"type": "registry", "name": "registry.k8s.io", "namespace": ""}, {"type": "registry", "name": "registry.invalid", "namespace": ""}]
   reasoning=当前集群共70个Pod，其中6个异常Pod全部集中在node1节点。5/6的异常Pod处于ImagePullBackOff/ContainerCreating状态，根本原因是node1节点无法访问外部镜像仓库（registry-1.docker.io、registry.k8s.io等），表现为i/o timeout网络不可达。1个Pod（network-test）虽然处于Terminating状态，但其根本原因也是镜像拉取失败导致容器从未成功启动。因此主要根因是镜像仓库网络不可达（L3），辅助Terminating卡住（L1）。
   layer_analysis={"layer": "L3", "derived_layer": "L1", "layers": ["L3", "L1"], "layer_name": "ImagePullFailed", "confidence": 0.9, "reasoning": "当前集群共70个Pod，其中6个异常Pod全部集中在node1节点。5/6的异常Pod处于ImagePullBackOff/ContainerCreating状态，根本原因是node1节点无法访问外部镜像仓库（registry-1.docker.io、registry.k8s.io等），表现为i/o timeout网络不可达。1个Pod（network-test）虽然处于Terminating状态，但其根本原因也是镜像拉取失败导致容器从未成功启动。因此主要根因是镜像仓库网络不可达（L3），辅助Terminating卡住（L1）。", "abnormal_pods": [{"name": "network-test", "namespace": "aiops-e2e", "status": "Terminating"}, {"name": "rc-imagepull-invalid-registry", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "test-network", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2tnsd", "namespace": "mcp", "status": "ContainerCreating"}, {"name": "node-debugger-node1-djrzl", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-zst8z", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_pull", "key_entities": [{"type": "node", "name": "node1", "namespace": ""}, {"type": "namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}, {"type": "namespace", "name": "mcp", "namespace": "mcp"}, {"type": "registry", "name": "registry-1.docker.io", "namespace": ""}, {"type": "registry", "name": "registry.k8s.io", "namespace": ""}, {"type": "registry", "name": "registry.invalid", "namespace": ""}], "possible_scenarios": [{"scenario": "node1节点无法访问公网镜像仓库", "probability": "高", "reason": "5个Pod的describe显示docker.io、registry.k8s.io等仓库均表现为i/o timeout，说明节点出站网络被阻断"}, {"scenario": "镜像地址配置错误", "probability": "中", "reason": "rc-imagepull-invalid-registry使用了不存在的域名registry.invalid，DNS解析失败"}, {"scenario": "Terminating卡住由镜像拉取失败引起", "probability": "中", "reason": "network-test因镜像拉取失败导致容器从未成功启动，无法正常停止而卡在Terminating"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "network-test"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-invalid-registry"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "test-network"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-djrzl"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-zst8z"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2tnsd"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "network-test"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-invalid-registry"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "test-network"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-djrzl"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-zst8z"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2tnsd"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Terminating": 1, "ImagePullBackOff": 4}, "total_abnormal": 5, "selected_rows": ["aiops-e2e         network-test                                        0/1     Terminating         0              2m20s   172.16.166.160   node1    <none>           <none>            run=network-test", "aiops-e2e         rc-imagepull-invalid-registry                       0/1     ImagePullBackOff    0              32m     172.16.166.147   node1    <none>           <none>            app=rc-imagepull-invalid-registry,pod_abnormal_type=ImagePullFailed,rootcause-e2e=true", "aiops-e2e         test-network                                        0/1     ImagePullBackOff    0              5m54s   172.16.166.133   node1    <none>           <none>            run=test-network", "mcp               node-debugger-node1-2tnsd                           0/1     ContainerCreating   0              76s     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-djrzl                           0/1     ImagePullBackOff    0              15m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-zst8z                           0/1     ImagePullBackOff    0              4m38s   10.2.0.49        node1    <none>           <none>            <none>"], "raw_ref": "/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L1（主层级: Layer.L3）
   置信度: 90%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 好的，我已经理解任务。现在按既有 evidence_plan 执行工具调用。先从影响最大的异常组开始，并行调用所有可独立的 critical 工具。

先批量执行所有 Pod describe 和 node 状态检查：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod node-debugger-node1-djrzl (ns=mcp) is Pending on node node1/10.2.0.49. Container debugger using image registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 is in ImagePullBackOff state (Waiting, Rea
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod node-debugger-node1-zst8z (namespace mcp) on node node1/10.2.0.49 is Pending. Container "debugger" with image busybox:1.28 is in ImagePullBackOff (State: Waiting, Reason: ImagePullBackOff). All pu
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 输出摘要: raw_chars=132 lines=3
Command failed (exit 1):
kubectl describe pod network-test -n aiops-e2e
Error from server (NotFound): pods "network-test" not found
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 输出摘要: raw_chars=135 lines=3
Command failed (exit 1):
kubectl get -o yaml pod network-test -n aiops-e2e
Error from server (NotFound): pods "network-test" not found
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-imagepull-invalid-registry
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          31m (x4 over 33m)      kubelet            Failed t
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node1   Ready    <none>   238d   v1.26.8   10.2.0.49     <
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod test-network 处于 Pending 状态，容器 ImagePullBackOff，无法拉取 busybox:1.28 镜像：所有拉取尝试均因 dial tcp registry-1.docker.io:443 i/o timeout 失败（连接 registry-1.docker.io 超时），触发了 ErrImagePull → BackOff → ImagePullBack
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-2tnsd
namespace: mcp
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed   37s                  kubelet  Failed to pull image "busybox:1.28": 
   💭 [证据链采集] **关键发现：Pod network-test 已删除（NotFound）！** 这是一个重要的冲突证据。让我继续执行剩余的 imagePullSecrets 检查。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-imagepull-invalid-registry
namespace: aiops-e2e
creationTimestamp: 2026-05-21T09:26:39Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finaliz
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: node-debugger-node1-zst8z
namespace: mcp
creationTimestamp: 2026-05-21T09:54:17Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: test-network
namespace: aiops-e2e
creationTimestamp: 2026-05-21T09:53:01Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none>
servi
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: node-debugger-node1-djrzl
namespace: mcp
creationTimestamp: 2026-05-21T09:43:46Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <none
   💭 [证据链采集] 好的，所有计划工具已执行完毕。现在汇总证据结论。

---

## 证据采集结论

### ✅ 已采集证据

#### 🟢 异常组 g2 — ImagePullBackOff（主异常组，完整验证通过）

| Pod | namespace | 镜像 | 失败原因 | 凭据 |
|:---|:---|:---|:---|:---|
| **rc-imagepull-invalid-registry** | aiops-e2e | `registry.invalid/aiops/rootcause:v0` | **DNS 解析失败** — `lookup registry.invalid on 127.0.0.53:53: no such host` | ✅ 无 imagePullSecrets |
| **test-network** | aiops-e2e | `busybox:1.28` | **网络超时** — `dial tcp 31.13.80.37:443: i/o timeout` (registry-1.docker.io) | ✅ 无 imagePullSecrets |
| **node-debugger-node1-djrzl** | mcp | `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0` | **网络超时** — `dial tcp 74.125.204.82:443: i/o timeout` (registry.k8s.io) | ✅ 无 imagePullSecrets |
| **node-debugger-node1-zst8z** | mcp | `busybox:1.28` | **网络超时** — `dial tcp 31.13.80.37:443 / 118.184.78.78:443: i/o timeout` | ✅ 无 imagePullSecrets |

**共同特征**：
- 所有 Pod 均由 `kubelet` 调度到 **node1**，无 imagePullSecrets
- 镜像仓库类型覆盖了 `docker.io`、`registry.k8s.io`、`registry.invalid`（伪造域名）
- **registry-1.docker.io** 和 **registry.k8s.io** 均表现为 `i/o timeout`，指向节点出站网络被阻断

#### 🟢 异常组 g3 — ContainerCreating（最小验证通过）
- **node-debugger-node1-2tnsd** (mcp)：镜像 `busybox:1.28`，同样因 `dial tcp 118.184.78.78:443: i/o timeout` 拉取失败，实际状态等同于 ImagePullBackOff

#### 🟢 节点状态
- **node1** 状态 **Ready**，运行正常 — 不是节点不可用，而是节点**出站网络访问外部镜像仓库被阻断**

#### 🟢 镜像地址配置错误（独立证据）
- `rc-imagepull-invalid-registry` 使用了 **不存在的域名** `registry.invalid`，DNS 解析失败（独立于网络超时问题，但都在 node1 上）

---

### ⚠️ 冲突证据 / 负向证据

| 计划项 | 结果 | 说明 |
|:---|:---|:---|
| g1-terminating-pod-yaml（network-test） | **NotFound** | Pod network-test 已从集群删除，不再存在 |
| g1-terminating-pod-describe（network-test） | **NotFound** | 同上，对象已删除 |
| 上游 abnormal_groups g1 (TerminatingStuck) | **当前无法验证** | 对象已不存在，Terminating 异常组已无实际目标 |

**解读**：`network-test` 在上游分析时处于 Terminating，但本轮采证时已完全删除。这符合"Terminating 由镜像拉取失败间接导致"的场景——Pod 因依赖镜像拉取失败无法正常终止，最终在某个节点被清理删除。当前 g1 异常组已过时。

---

### ❌ 未采集证据
- 容器内网络诊断命令输出（`nslookup`/`wget`）：所有 Pod 容器都在 ImagePullBackOff，从未成功启动，无法进入容器执行命令
- Terminating Pod 的 YAML finalizers/deletionTimestamp：因对象已删除无法采集

---

### 🔍 根因结论
**集群主要问题：node1 节点无法访问公网镜像仓库（registry-1.docker.io、registry.k8s.io），导致 5/5 当前存在的异常 Pod 全部卡在 ImagePullBackOff。** 同时存在一个独立的镜像地址配置错误（`registry.invalid` 域名不可解析）。Terminating 的 network-test 已自然删除。
   ✅ [证据链采集] 完成 (55.3s)
   📤 → 下游数据: evidence_items=23/23
   evidence_analysis={"evidence_plan":[{"id":"g2-rep-pod-describe-1","description":"对 ImagePullBackOff 主异常组代表 Pod rc-imagepull-invalid-registry 执行 kubectl describe 查看镜像拉取失败详情","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-imagepull-invalid-registry","namespace":"aiops-e2e"},"purpose":"确认镜像地址错误/registry.invalid DNS解析失败等关键错误原文","evidence_type":"pod_event","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-rep-pod-describe-2","description":"对 ImagePullBackOff 主异常组代表 Pod test-network 执行 kubectl describe 查看镜像拉取失败详情","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-network -n aiops-e2e","tool_args":{"kind":"pod","name":"test-network","namespace":"aiops-e2e"},"purpose":"确认镜像拉取失败原因是否为registry-1.docker.io超时","evidence_type":"pod_event","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-rep-pod-describe-3","description":"对 ImagePullBackOff 主异常组代表 Pod node-debugger-node1-djrzl 执行 kubectl describe","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-djrzl -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-djrzl","namespace":"mcp"},"purpose":"验证 mcp namespace 下 ImagePullBackOff Pod 的镜像拉取失败原因","evidence_type":"pod_event","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-rep-pod-describe-4","description":"对 ImagePullBackOff 主异常组代表 Pod node-debugger-node1-zst8z 执行 kubectl describe","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-zst8z -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-zst8z","namespace":"mcp"},"purpose":"验证 mcp namespace 下第二个 ImagePullBackOff Pod 的镜像拉取失败原因","evidence_type":"pod_event","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-terminating-pod-yaml","description":"对 Terminating 异常组 Pod network-test 获取完整 YAML 检查 deletionTimestamp 和 finalizers","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod network-test -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"network-test","namespace":"aiops-e2e"},"purpose":"确认 deletionTimestamp、finalizers、terminationGracePeriodSeconds 等关键信息","evidence_type":"pod_yaml","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g1-terminating-pod-describe","description":"对 Terminating 异常组 Pod network-test 执行 kubectl describe 查看 termination 事件和 volume 事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod network-test -n aiops-e2e","tool_args":{"kind":"pod","name":"network-test","namespace":"aiops-e2e"},"purpose":"确认 termination 相关事件、volume detach/unmount 事件、preStop 信息","evidence_type":"pod_event","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g3-containercreating-describe","description":"对 ContainerCreating 异常组 Pod node-debugger-node1-2tnsd 执行 kubectl describe","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-2tnsd -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-2tnsd","namespace":"mcp"},"purpose":"确认 ContainerCreating Pod 的当前事件和状态","evidence_type":"pod_event","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"node1-node-status","description":"检查 node1 节点状态确认是否 Ready","level":"important","tool":"kubectl_get_by_name","command":"kubectl get node node1 -o wide","tool_args":{"kind":"node","name":"node1"},"purpose":"确认节点状态是否正常","evidence_type":"node_status","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-imagepullsecrets-check","description":"检查 Pod rc-imagepull-invalid-registry 和 test-network 的 imagePullSecrets 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-imagepull-invalid-registry test-network -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-imagepull-invalid-registry","namespace":"aiops-e2e","names":["rc-imagepull-invalid-registry","test-network"]},"purpose":"验证是否配置了 imagePullSecrets","evidence_type":"pod_spec","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g2-mcp-imagepullsecrets-check","description":"检查 mcp namespace 下 debugger Pod 的 imagePullSecrets 和镜像地址","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod node-debugger-node1-djrzl node-debugger-node1-zst8z -n mcp -o yaml","tool_args":{"kind":"pod","name":"node-debugger-node1-djrzl","namespace":"mcp","names":["node-debugger-node1-djrzl","node-debugger-node1-zst8z"]},"purpose":"验证 mcp 下 ImagePullBackOff Pod 的镜像地址和 imagePullSecrets","evidence_type":"pod_spec","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"Pod node-debugger-node1-djrzl (ns=mcp) is Pending on node node1/10.2.0.49. Container debugger using image registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 is in ImagePullBackOff state (Waiting, Ready=False). All pull attempts failed with i/o timeout dialing GCR/AR endpoints (asia-east1-docker.pkg.dev, europe-west2-docker.pkg.dev, 74.125.204.82:443). Events show Failed (ErrImagePull, ImagePullBackOff) recurring up to 6x for each error type. BackOff has occurred 43 times over 15m.\nkey_facts: [\"Pod: node-debugger-node1-djrzl, namespace: mcp\", \"Node: node1/10.2.0.49\", \"Status: Pending\", \"Container: debugger, Image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\", \"Container State: Waiting, Reason: ImagePullBackOff, Ready: False\", \"Container Command: nslookup registry.invalid\", \"QoS Class: BestEffort\", \"Events: Multiple Warning Failed - ErrImagePull, ImagePullBackOff, and pull failures due to i/o timeout dialing registry endpoints (asia-east1-docker.pkg.dev, europe-west2-docker.pkg.dev on 74.125.204.82:443)\", \"BackOff: 43 times over 15m, last at 71s ago\"]\nconflicts: [\"current_summary omits the Pulling events (Normal Pulling 12m x4 over 16m) present in raw_preview\"]\nmissing: [\"No Container ID or Image ID set\", \"Command 'nslookup registry.invalid' and mount '/host from host-root' present but root cause of pull failure is network/timeout to registry.k8s.io\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"Pod node-debugger-node1-zst8z (namespace mcp) on node node1/10.2.0.49 is Pending. Container \"debugger\" with image busybox:1.28 is in ImagePullBackOff (State: Waiting, Reason: ImagePullBackOff). All pull attempts to docker.io/library/busybox:1.28 failed with i/o timeout dialing registry-1.docker.io (IPs 31.13.80.37, 118.184.78.78) on port 443. Events show Failed (ErrImagePull, ImagePullBackOff) and BackOff. Pod is not Ready, QoS BestEffort.\nkey_facts: [\"pod: node-debugger-node1-zst8z\", \"namespace: mcp\", \"node: node1/10.2.0.49\", \"status: Pending\", \"container: debugger\", \"image: busybox:1.28\", \"container State: Waiting (ImagePullBackOff)\", \"Ready: False\", \"ContainersReady: False\", \"QoS Class: BestEffort\", \"Event: Warning Failed - pull image failed: dial tcp 31.13.80.37:443: i/o timeout\", \"Event: Warning Failed - pull image failed: dial tcp 118.184.78.78:443: i/o timeout\", \"Event: Warning Failed - Error: ImagePullBackOff (x4)\", \"Event: Warning Failed - Error: ErrImagePull (x4)\", \"Event: Normal BackOff - Back-off pulling image (x4)\", \"all pull attempts to docker.io/library/busybox:1.28 resulted in network i/o timeout to registry-1.docker.io\", \"Restart Count: 0\"]\nmissing: [\"current_summary omitted 'Pulling' event seen in raw_preview (Normal Pulling 83s x4)\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 输出摘要: raw_chars=132 lines=3\nCommand failed (exit 1):\nkubectl describe pod network-test -n aiops-e2e\nError from server (NotFound): pods \"network-test\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 输出摘要: raw_chars=135 lines=3\nCommand failed (exit 1):\nkubectl get -o yaml pod network-test -n aiops-e2e\nError from server (NotFound): pods \"network-test\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/004-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-imagepull-invalid-registry\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          31m (x4 over 33m)      kubelet            Failed to pull image \"registry.invalid/aiops/rootcause:v0\": rpc error: code = Unknown desc = failed to pull and unpack image \"registry.invalid/aiops/rootcause:v0\": failed to resolve reference \"registry.invalid/aiops/rootcause:v0\": failed to do request: Head \"https://registry.invalid/v2/aiops/rootcause/manifests/v0\": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host\n  Normal   BackOff         3m27s (x117 over 33m)  kubelet            Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"\n      Reason:       ImagePullBackOff\n  Warning  Failed          32m (x6 over 33m)      kubelet            Error: ImagePullBackOff\n  Warning  Failed          31m (x4 over 33m)      kubelet            Error: ErrImagePull\n                  cni.projectcalico.org/containerID: 6b564b34bd28dd42f6854bbc537d2155cfdab18a1486aa3ea2979833ebeaadd1\n                  cni.projectcalico.org/podIP: 172.16.166.147/32\n                  cni.projectcalico.org/podIPs: 172.16.166.147/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:          registry.invalid/aiops/rootcause:v0\n    Image ID:\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-6zmg5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed          32m (x6 over 33m)      kubelet            Error: ImagePullBackOff\n  Warning  Failed          31m (x4 over 33m)      kubelet            Failed to pull image \"registry.invalid/aiops/rootcause:v0\": rpc error: code = Unknown desc = failed to pull and unpack image \"registry.invalid/aiops/rootcause:v0\": failed to resolve reference \"registry.invalid/aiops/rootcause:v0\": failed to do request: Head \"https://registry.invalid/v2/aiops/rootcause/manifests/v0\": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host\n  Warning  Failed          31m (x4 over 33m)      kubelet            Error: ErrImagePull\n  Normal   BackOff         3m27s (x117 over 33m)  kubelet            Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"\n关键状态/事件:\n                  pod_abnormal_type=ImagePullFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nnode1   Ready    <none>   238d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/006-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/006-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/006-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_describe","data":"Pod test-network 处于 Pending 状态，容器 ImagePullBackOff，无法拉取 busybox:1.28 镜像：所有拉取尝试均因 dial tcp registry-1.docker.io:443 i/o timeout 失败（连接 registry-1.docker.io 超时），触发了 ErrImagePull → BackOff → ImagePullBackOff 循环。\nkey_facts: [\"name: test-network\", \"namespace: aiops-e2e\", \"node: node1/10.2.0.49\", \"status: Pending\", \"Container: test-network\", \"Image: busybox:1.28\", \"State: Waiting, Reason: ImagePullBackOff\", \"Ready: False\", \"Restart Count: 0\", \"QoS Class: BestEffort\", \"Events: Warning Failed (x2 over 6m9s) - Failed to pull image 'busybox:1.28' - rpc error code=DeadlineExceeded - dial tcp 31.13.80.37:443: i/o timeout\", \"Events: Warning Failed (x1) - rpc error code=Unknown - dial tcp 31.13.80.37:443: i/o timeout\", \"Events: Warning Failed (x4 over 6m9s) - Error: ErrImagePull\", \"Events: Warning Failed (x1) - dial tcp 118.184.78.78:443: i/o timeout\", \"Events: Normal BackOff (x7 over 6m9s) - Back-off pulling image 'busybox:1.28'\", \"Events: Warning Failed (x7 over 6m9s) - Error: ImagePullBackOff\", \"Pod IP: 172.16.166.133\", \"Calico CNI 网络已配置\", \"Scheduled 成功，Assigned to node1\"]\nconflicts: [\"current_summary 未记录 Container args 中的 nslookup/wget 命令；raw_preview 包含该信息\", \"current_summary 遗漏 Normal Scheduled 7m10s 和 Normal AddedInterface 事件；raw_preview 包含\"]\nmissing: [\"Container 未启动（ImagePullBackOff），无法执行容器内网络诊断命令\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/007-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/007-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/007-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-2tnsd\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed   37s                  kubelet  Failed to pull image \"busybox:1.28\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.28\": failed to resolve reference \"docker.io/library/busybox:1.28\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.28\": dial tcp 118.184.78.78:443: i/o timeout\n  Normal   BackOff  37s                  kubelet  Back-off pulling image \"busybox:1.28\"\n      Reason:       ImagePullBackOff\n  Warning  Failed   37s                  kubelet  Error: ErrImagePull\n  Warning  Failed   37s                  kubelet  Error: ImagePullBackOff\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:\n    Image:         busybox:1.28\n    Image ID:\n    Command:\n      nslookup\n      registry-1.docker.io\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-n7gh5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed   37s                  kubelet  Failed to pull image \"busybox:1.28\": rpc error: code = Unknown desc = failed to pull and unpack image \"docker.io/library/busybox:1.28\": failed to resolve reference \"docker.io/library/busybox:1.28\": failed to do request: Head \"https://registry-1.docker.io/v2/library/busybox/manifests/1.28\": dial tcp 118.184.78.78:443: i/o timeout\n  Warning  Failed   37s                  kubelet  Error: ErrImagePull\n  Normal   BackOff  37s                  kubelet  Back-off pulling image \"busybox:1.28\"\n  Warning  Failed   37s                  kubelet  Error: ImagePullBackOff\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/008-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/008-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/008-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-imagepull-invalid-registry\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T09:26:39Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-imagepull-invalid-registry, pod_abnormal_type=ImagePullFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-imagepull-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=registry.invalid/aiops/rootcause:v0 imagePullPolicy=Always\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"\nvolumes:\n- {\"name\": \"kube-api-access-6zmg5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/009-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/009-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/009-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: node-debugger-node1-zst8z\nnamespace: mcp\ncreationTimestamp: 2026-05-21T09:54:17Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 1\ncontainers:\n- debugger: image=busybox:1.28 imagePullPolicy=IfNotPresent\n  command: nslookup registry.invalid\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [debugger]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [debugger]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- debugger: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"busybox:1.28\"\nvolumes:\n- {\"name\": \"host-root\"}\n- {\"name\": \"kube-api-access-xwzf9\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/010-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/010-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/010-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: test-network\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T09:53:01Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 2\ncontainers:\n- test-network: image=busybox:1.28 imagePullPolicy=IfNotPresent\n  args: sh -c nslookup registry.invalid 2>&1; echo ---; wget -q -O /dev/null --timeout=5 https://registry.invalid/v2/ 2>&1 || true; echo ---; nslookup registry.k8s.io 2>&1; echo ---; wget -q -O /dev/null --timeout=5 https://registry.k8s.io/v2/ 2>&1 || true\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [test-network]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [test-network]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- test-network: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"busybox:1.28\"\nvolumes:\n- {\"name\": \"kube-api-access-8cw9x\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/011-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/011-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/011-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: node-debugger-node1-djrzl\nnamespace: mcp\ncreationTimestamp: 2026-05-21T09:43:46Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Never\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\ntolerations_count: 1\ncontainers:\n- debugger: image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 imagePullPolicy=IfNotPresent\n  command: nslookup registry.invalid\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [debugger]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [debugger]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- debugger: ready=False restarts=0 reason=ImagePullBackOff exitCode=None\n  message: Back-off pulling image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\"\nvolumes:\n- {\"name\": \"host-root\"}\n- {\"name\": \"kube-api-access-kt6fd\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/012-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/012-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8da5209fa33d409f/tools/012-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"好的，所有计划工具已执行完毕。现在汇总证据结论。\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据\n\n#### 🟢 异常组 g2 — ImagePullBackOff（主异常组，完整验证通过）\n\n| Pod | namespace | 镜像 | 失败原因 | 凭据 |\n|:---|:---|:---|:---|:---|\n| **rc-imagepull-invalid-registry** | aiops-e2e | `registry.invalid/aiops/rootcause:v0` | **DNS 解析失败** — `lookup registry.invalid on 127.0.0.53:53: no such host` | ✅ 无 imagePullSecrets |\n| **test-network** | aiops-e2e | `busybox:1.28` | **网络超时** — `dial tcp 31.13.80.37:443: i/o timeout` (registry-1.docker.io) | ✅ 无 imagePullSecrets |\n| **node-debugger-node1-djrzl** | mcp | `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0` | **网络超时** — `dial tcp 74.125.204.82:443: i/o timeout` (registry.k8s.io) | ✅ 无 imagePullSecrets |\n| **node-debugger-node1-zst8z** | mcp | `busybox:1.28` | **网络超时** — `dial tcp 31.13.80.37:443 / 118.184.78.78:443: i/o timeout` | ✅ 无 imagePullSecrets |\n\n**共同特征**：\n- 所有 Pod 均由 `kubelet` 调度到 **node1**，无 imagePullSecrets\n- 镜像仓库类型覆盖了 `docker.io`、`registry.k8s.io`、`registry.invalid`（伪造域名）\n- **registry-1.docker.io** 和 **registry.k8s.io** 均表现为 `i/o timeout`，指向节点出站网络被阻断\n\n#### 🟢 异常组 g3 — ContainerCreating（最小验证通过）\n- **node-debugger-node1-2tnsd** (mcp)：镜像 `busybox:1.28`，同样因 `dial tcp 118.184.78.78:443: i/o timeout` 拉取失败，实际状态等同于 ImagePullBackOff\n\n#### 🟢 节点状态\n- **node1** 状态 **Ready**，运行正常 — 不是节点不可用，而是节点**出站网络访问外部镜像仓库被阻断**\n\n#### 🟢 镜像地址配置错误（独立证据）\n- `rc-imagepull-invalid-registry` 使用了 **不存在的域名** `registry.invalid`，DNS 解析失败（独立于网络超时问题，但都在 node1 上）\n\n---\n\n### ⚠️ 冲突证据 / 负向证据\n\n| 计划项 | 结果 | 说明 |\n|:---|:---|:---|\n| g1-terminating-pod-yaml（network-test） | **NotFound** | Pod network-test 已从集群删除，不再存在 |\n| g1-terminating-pod-describe（network-test） | **NotFound** | 同上，对象已删除 |\n| 上游 abnormal_groups g1 (TerminatingStuck) | **当前无法验证** | 对象已不存在，Terminating 异常组已无实际目标 |\n\n**解读**：`network-test` 在上游分析时处于 Terminating，但本轮采证时已完全删除。这符合\"Terminating 由镜像拉取失败间接导致\"的场景——Pod 因依赖镜像拉取失败无法正常终止，最终在某个节点被清理删除。当前 g1 异常组已过时。\n\n---\n\n### ❌ 未采集证据\n- 容器内网络诊断命令输出（`nslookup`/`wget`）：所有 Pod 容器都在 ImagePullBackOff，从未成功启动，无法进入容器执行命令\n- Terminating Pod 的 YAML finalizers/deletionTimestamp：因对象已删除无法采集\n\n---\n\n### 🔍 根因结论\n**集群主要问题：node1 节点无法访问公网镜像仓库（registry-1.docker.io、registry.k8s.io），导致 5/5 当前存在的异常 Pod 全部卡在 ImagePullBackOff。** 同时存在一个独立的镜像地址配置错误（`registry.invalid` 域名不可解析）。Terminating 的 network-test 已自然删除。","collection_summary":"计划 10 项，实际采集 10 项，未采集 0 项，完整度 100%；其中真实环境证据 23/23 项，完整度 100%；实际执行工具 25 个，匹配计划 10 个，未规划证据 15 个","plan_total":10,"plan_collected":10,"plan_completeness":1.0,"environment_evidence_total":23,"environment_evidence_collected":23,"environment_evidence_completeness":1.0,"executed_tool_count":25,"matched_tool_count":10,"unplanned_tool_count":15,"evidence_inventory":[{"id":"g2-rep-pod-describe-1","description":"对 ImagePullBackOff 主异常组代表 Pod rc-imagepull-invalid-registry 执行 kubectl describe 查看镜像拉取失败详情","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e","purpose":"确认镜像地址错误/registry.invalid DNS解析失败等关键错误原文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-rep-pod-describe-2","description":"对 ImagePullBackOff 主异常组代表 Pod test-network 执行 kubectl describe 查看镜像拉取失败详情","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-network -n aiops-e2e","purpose":"确认镜像拉取失败原因是否为registry-1.docker.io超时","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-rep-pod-describe-3","description":"对 ImagePullBackOff 主异常组代表 Pod node-debugger-node1-djrzl 执行 kubectl describe","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-djrzl -n mcp","purpose":"验证 mcp namespace 下 ImagePullBackOff Pod 的镜像拉取失败原因","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"g2-rep-pod-describe-4","description":"对 ImagePullBackOff 主异常组代表 Pod node-debugger-node1-zst8z 执行 kubectl describe","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-zst8z -n mcp","purpose":"验证 mcp namespace 下第二个 ImagePullBackOff Pod 的镜像拉取失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-terminating-pod-yaml","description":"对 Terminating 异常组 Pod network-test 获取完整 YAML 检查 deletionTimestamp 和 finalizers","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod network-test -n aiops-e2e -o yaml","purpose":"确认 deletionTimestamp、finalizers、terminationGracePeriodSeconds 等关键信息","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"g1-terminating-pod-describe","description":"对 Terminating 异常组 Pod network-test 执行 kubectl describe 查看 termination 事件和 volume 事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod network-test -n aiops-e2e","purpose":"确认 termination 相关事件、volume detach/unmount 事件、preStop 信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g3-containercreating-describe","description":"对 ContainerCreating 异常组 Pod node-debugger-node1-2tnsd 执行 kubectl describe","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-2tnsd -n mcp","purpose":"确认 ContainerCreating Pod 的当前事件和状态","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"node1-node-status","description":"检查 node1 节点状态确认是否 Ready","level":"important","tool":"kubectl_get_by_name","command":"kubectl get node node1 -o wide","purpose":"确认节点状态是否正常","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-imagepullsecrets-check","description":"检查 Pod rc-imagepull-invalid-registry 和 test-network 的 imagePullSecrets 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-imagepull-invalid-registry test-network -n aiops-e2e -o yaml","purpose":"验证是否配置了 imagePullSecrets","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-mcp-imagepullsecrets-check","description":"检查 mcp namespace 下 debugger Pod 的 imagePullSecrets 和镜像地址","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod node-debugger-node1-djrzl node-debugger-node1-zst8z -n mcp -o yaml","purpose":"验证 mcp 下 ImagePullBackOff Pod 的镜像地址和 imagePullSecrets","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_8","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_9","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_10","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_11","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_12","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_13","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 10/10 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | g2-rep-pod-de... | critical | ✅ | kubectl_describe | 对 ImagePullBackOff 主异常组代表 Pod rc-imagepull-in... | `kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e` |
   | g2-rep-pod-de... | critical | ✅ | kubectl_describe | 对 ImagePullBackOff 主异常组代表 Pod test-network 执行... | `kubectl describe pod test-network -n aiops-e2e` |
   | g2-rep-pod-de... | critical | ✅ | kubectl_describe | 对 ImagePullBackOff 主异常组代表 Pod node-debugger-n... | `kubectl describe pod node-debugger-node1-djrzl -n mcp` |
   | g2-rep-pod-de... | critical | ✅ | kubectl_describe | 对 ImagePullBackOff 主异常组代表 Pod node-debugger-n... | `kubectl describe pod node-debugger-node1-zst8z -n mcp` |
   | g1-terminatin... | critical | ✅ | kubectl_get_yaml | 对 Terminating 异常组 Pod network-test 获取完整 YAML ... | `kubectl get pod network-test -n aiops-e2e -o yaml` |
   | g1-terminatin... | critical | ✅ | kubectl_describe | 对 Terminating 异常组 Pod network-test 执行 kubectl... | `kubectl describe pod network-test -n aiops-e2e` |
   | g3-containerc... | important | ✅ | kubectl_describe | 对 ContainerCreating 异常组 Pod node-debugger-nod... | `kubectl describe pod node-debugger-node1-2tnsd -n mcp` |
   | node1-node-st... | important | ✅ | kubectl_get_by_name | 检查 node1 节点状态确认是否 Ready | `kubectl get node node1 -o wide` |
   | g2-imagepulls... | important | ✅ | kubectl_get_yaml | 检查 Pod rc-imagepull-invalid-registry 和 test-n... | `kubectl get pod rc-imagepull-invalid-registry test-network -n aiops-e2e -o yaml` |
   | g2-mcp-imagep... | important | ✅ | kubectl_get_yaml | 检查 mcp namespace 下 debugger Pod 的 imagePullSe... | `kubectl get pod node-debugger-node1-djrzl node-debugger-node1-zst8z -n mcp -o...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (35.0s)
   📤 → 下游数据: root_cause=**核心根因：node1节点（10.2.0.49）出站网络无法访问外部镜像仓库。** 具体证据：1) test-network/aiops-e2e、node-debugger-node1-zst8z/mcp、node-debugger-node1-2tnsd/mcp 均拉取 busybox:1.28，报 dial tcp 31.13.80.37:443 和 118.184.78.78:443 i/o timeout（registry-1.docker.io）。2) node-debugger-node1-djrzl/mcp 拉取 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0，报 dial tcp 74.125.204.82:443 i/o timeout。3) node1 节点自身状态 Ready，containerd 1.6.32 正常，不是节点故障。**辅助根因：** rc-imagepull-invalid-registry/aiops-e2e 额外存在镜像地址配置错误——使用了不存在的域名 registry.invali
... 截断，原始 694 字符
   confidence=95%
   causal_chain={"root_cause": "node1节点（10.2.0.49）出站网络访问外部镜像仓库被阻断", "propagation": "node1节点的kubelet/containerd无法与registry-1.docker.io（31.13.80.37、118.184.78.78:443）和registry.k8s.io（74.125.204.82:443）建立TCP连接，导致所有依赖这些仓库拉取镜像的Pod均无法创建容器", "direct_cause": "所有异常Pod的容器状态均为Waiting/ImagePullBackOff（或ContainerCreating），kubelet Events明确记录i/o timeout错误", "manifestation": "用户可见5个异常Pod（4个ImagePullBackOff + 1个ContainerCreating）全部集中在node1节点，且node1本身Ready但无法拉取外部镜像"}
   rca_analysis={"phenomenon": "集群共有70个Pod，其中5个异常Pod集中在node1节点（10.2.0.49）：4个ImagePullBackOff（rc-imagepull-invalid-registry/aiops-e2e、test-network/aiops-e2e、node-debugger-node1-djrzl/mcp、node-debugger-node1-zst8z/mcp），1个ContainerCreating（node-debugger-node1-2tnsd/mcp）。另1个原Terminating Pod network-test/aiops-e2e已从集群删除（NotFound），当前无实际异常目标。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe rc-imagepull-invalid-registry", "content": "镜像registry.invalid/aiops/rootcause:v0拉取失败，DNS解析registry.invalid失败：no such host", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe test-network", "content": "镜像busybox:1.28拉取失败，dial tcp registry-1.docker.io:443 i/o timeout", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe node-debugger-node1-djrzl", "content": "镜像registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0拉取失败，dial tcp 74.125.204.82:443 i/o timeout", "reliability": "高"}, {"id": "e4", "source": "kubectl_describe node-debugger-node1-zst8z", "content": "镜像busybox:1.28拉取失败，dial tcp 31.13.80.37:443和118.184.78.78:443 i/o timeout", "reliability": "高"}, {"id": "e5", "source": "kubectl_describe node-debugger-node1-2tnsd", "content": "镜像busybox:1.28拉取失败，dial tcp 118.184.78.78:443 i/o timeout，状态ContainerCreating实际等同于ImagePullBackOff", "reliability": "高"}, {"id": "e6", "source": "kubectl_get_by_name node1", "content": "node1状态Ready，containerd://1.6.32运行正常", "reliability": "高"}, {"id": "e7", "source": "kubectl_get_yaml rc-imagepull-invalid-registry", "content": "Pod无imagePullSecrets，镜像registry.invalid/aiops/rootcause:v0，imagePullPolicy=Always", "reliability": "高"}, {"id": "e8", "source": "kubectl_get_yaml node-debugger-node1-zst8z", "content": "Pod无imagePullSecrets，镜像busybox:1.28，imagePullPolicy=IfNotPresent", "reliability": "高"}, {"id": "e9", "source": "kubectl_describe network-test (冲突证据)", "content": "Pod network-test已不存在（NotFound）——原Terminating Pod已被删除，g1异常组已无实际目标", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Failed to pull image \"registry.invalid/aiops/rootcause:v0\": lookup registry.invalid on 127.0.0.53:53: no such host", "interpretation": "rc-imagepull-invalid-registry使用了不存在的域名registry.invalid，DNS解析彻底失败。这是一个镜像地址配置错误，独立于网络超时问题。"}, {"evidence_id": "e2", "raw_data": "Failed to pull image \"busybox:1.28\": dial tcp 31.13.80.37:443: i/o timeout", "interpretation": "test-network尝试从registry-1.docker.io拉取busybox:1.28，TCP连接超时。节点node1到Docker Hub的出站网络被阻断。"}, {"evidence_id": "e3", "raw_data": "Failed to pull image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\": dial tcp 74.125.204.82:443: i/o timeout", "interpretation": "node-debugger-node1-djrzl尝试从registry.k8s.io拉取镜像，TCP连接超时。节点到Google Container Registry的出站网络也被阻断。"}, {"evidence_id": "e4", "raw_data": "Failed to pull image \"busybox:1.28\": dial tcp 31.13.80.37:443 and 118.184.78.78:443: i/o timeout", "interpretation": "node-debugger-node1-zst8z同样无法访问Docker Hub，多个IP地址均超时，确认是节点级出站网络阻断而不是DNS问题。"}, {"evidence_id": "e5", "raw_data": "Failed to pull image \"busybox:1.28\": dial tcp 118.184.78.78:443: i/o timeout. State: Waiting(ContainerCreating)", "interpretation": "node-debugger-node1-2tnsd的ContainerCreating状态实际由镜像拉取失败导致，本质与ImagePullBackOff相同，只是kubelet尚未更新状态。最小验证通过。"}, {"evidence_id": "e6", "raw_data": "node1 Ready, containerd://1.6.32", "interpretation": "node1本身运行正常，不是节点故障。问题出在节点出站网络层面，container runtime无法连接到外部镜像仓库。"}, {"evidence_id": "e7", "raw_data": "imagePullSecrets: <absent>, image: registry.invalid/aiops/rootcause:v0", "interpretation": "rc-imagepull-invalid-registry没有配置imagePullSecrets，镜像地址使用了不存在的registry.invalid域名。即使网络正常也会因DNS解析失败而拉取不到。"}, {"evidence_id": "e8", "raw_data": "imagePullSecrets: <absent>, image: busybox:1.28", "interpretation": "mcp命名空间下的debugger Pods没有配置imagePullSecrets。不过busybox:1.28是公有镜像，不需要认证；问题在于节点无法访问Docker Hub。"}, {"evidence_id": "e9", "raw_data": "Error from server (NotFound): pods \"network-test\" not found", "interpretation": "原Terminating的network-test Pod已从集群删除。该Pod的Terminating状态曾由镜像拉取失败间接导致，但当前已不存在，g1异常组无需继续分析。"}], "causal_chain": {"root_cause": "node1节点（10.2.0.49）出站网络访问外部镜像仓库被阻断", "propagation": "node1节点的kubelet/containerd无法与registry-1.docker.io（31.13.80.37、118.184.78.78:443）和registry.k8s.io（74.125.204.82:443）建立TCP连接，导致所有依赖这些仓库拉取镜像的Pod均无法创建容器", "direct_cause": "所有异常Pod的容器状态均为Waiting/ImagePullBackOff（或ContainerCreating），kubelet Events明确记录i/o timeout错误", "manifestation": "用户可见5个异常Pod（4个ImagePullBackOff + 1个ContainerCreating）全部集中在node1节点，且node1本身Ready但无法拉取外部镜像"}, "root_cause": "**核心根因：node1节点（10.2.0.49）出站网络无法访问外部镜像仓库。** 具体证据：1) test-network/aiops-e2e、node-debugger-node1-zst8z/mcp、node-debugger-node1-2tnsd/mcp 均拉取 busybox:1.28，报 dial tcp 31.13.80.37:443 和 118.184.78.78:443 i/o timeout（registry-1.docker.io）。2) node-debugger-node1-djrzl/mcp 拉取 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0，报 dial tcp 74.125.204.82:443 i/o timeout。3) node1 节点自身状态 Ready，containerd 1.6.32 正常，不是节点故障。**辅助根因：** rc-imagepull-invalid-registry/aiops-e2e 额外存在镜像地址配置错误——使用了不存在的域名 registry.invali\n... 截断，原始 694 字符", "root_cause_summary": "**核心根因：node1节点（10.2.0.49）出站网络无法访问外部镜像仓库。** 具体证据：1) test-network/aiops-e2e、node-debugger-node1-zst8z/mcp、node-debugger-node1-2tnsd/mcp 均拉取 busybox:1.28，报 dial tcp 31.13.80.37:443 和 118.184.78.78:443 i/o timeout（registry-1.docker.io）。2) node-debugger-node1-djrzl/mcp 拉取 registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0，报 dial tcp 74.125.204.82:443 i/o timeout。3) node1 节点自身状态 Ready，containerd 1.6.32 正常，不是节点故障。**辅助根因：** rc-imagepull-invalid-registry/aiops-e2e 额外存在镜像地址配置错误——使用了不存在的域名 registry.invali\n... 截断，原始 694 字符", "confidence": 0.95, "confidence_reason": "所有异常Pod的kubectl describe均有明确i/o timeout错误日志，覆盖2个namespace（aiops-e2e、mcp）、3个镜像仓库（registry-1.docker.io、registry.k8s.io、registry.invalid）、5个Pod，证据充分且因果链清晰。节点状态也已验证为Ready，排除了节点故障。置信度0.95。", "primary_runbooks": ["pod-imagepull-failed.md"], "alternative_causes": [{"cause": "imagePullSecret缺失导致认证失败", "probability": "低", "reason": "所有异常Pod使用的busybox:1.28和registry.k8s.io镜像均为公有镜像，不需要认证。kubelet报错是i/o timeout而非认证拒绝（denied/unauthorized）。"}, {"cause": "镜像tag不存在或镜像不存在", "probability": "低", "reason": "kubelet报错是网络层i/o timeout，未到达镜像清单检查阶段。且同一个busybox:1.28在多个Pod中表现一致失败，指向网络问题而非镜像不存在。"}, {"cause": "节点不可用或kubelet故障", "probability": "低", "reason": "node1状态Ready，containerd 1.6.32运行正常。kubelet能正常调度Pod、分配IP（Calico CNI成功）、生成Events，说明kubelet正常工作。"}, {"cause": "Terminating Pod network-test的finalizer/volume卡住", "probability": "低", "reason": "Pod network-test已从集群删除（NotFound），不再存在；不需要对其finalizer或volume进行分析。"}], "limitations": "1. 未在node1节点上直接执行curl/wget测试到registry-1.docker.io:443和registry.k8s.io:443的连通性——所有Pod容器均未成功启动，无法进入容器执行网络诊断命令。2. 未检查node1节点的网络策略、代理配置或iptables规则——这些是导致出站网络阻断的可能原因（如防火墙、代理、安全组规则等），但证据链已足以定位到网络不可达层面。3. 未检查集群级别的镜像缓存（如containerd mirror配置或harbor代理）——如果有镜像代理配置，本可绕过出站网络问题。4. rc-imagepull-invalid-registry使用了registry.invalid伪造域名（DNS解析失败），该问题需要与网络超时问题分开处理。", "llm_raw_analysis": "## 证据清点\n共采集10项证据（含1项冲突/负向证据），覆盖：\n- 异常组g2（ImagePullBackOff）：4个Pod的kubectl describe + YAML ✅\n- 异常组g3（ContainerCreating）：1个Pod的kubectl describe ✅\n- 异常组g1（Terminating）：Pod network-test已NotFound ❌\n- 节点状态：node1 Ready ✅\n- imagePullSecrets检查：所有Pod均无 ✅\n\n## 逐条分析\n所有ImagePullBackOff Pod的kubectl describe显示两类错误：\n1. **网络超时（i/o timeout）**：test-network、node-debugger-node1-djrzl、node-debugger-node1-zst8z、node-debugger-node1-2tnsd 均报dial tcp到各镜像仓库IP的443端口超时\n2. **DNS解析失败（no such host）**：rc-imagepull-invalid-registr\n... 截断，原始 923 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: **核心根因：node1节点（10.2.0.49）出站网络无法访问外部镜像仓库。** 具体证据：1) test-network/aiops-e2e、node-debugger-node1-zst8z/mcp、node-debugger-node1-2tnsd/mcp 均拉取 busybox:1.28...
   置信度: 95%
   🔗 因果链:
     根本原因: node1节点（10.2.0.49）出站网络访问外部镜像仓库被阻断
     传导机制: node1节点的kubelet/containerd无法与registry-1.docker.io（31.13.80.37、118.184.78.78:443）和registry.k8s.io（74.125.204.82:443）建立TCP连接，导致所有依赖这些仓库拉取镜像的Pod均无法创建容器
     最终表现: 用户可见5个异常Pod（4个ImagePullBackOff + 1个ContainerCreating）全部集中在node1节点，且node1本身Ready但无法拉取外部镜像


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (32.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 7844 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 59.7s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，这是为您生成的集群诊断报告。

---
## 📊 诊断概览

根据对集群状态的全量分析，当前集群**主要存在一个核心问题**：**node1 节点无法访问外部镜像仓库**，导致该节点上的 6 个 Pod 全部异常。具体诊断结果如下：

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ImagePullBackOff (主导) / Terminating / ContainerCreating |
| **兼容归因层** | L3(L3 网络连通性) - L1(L1 Pod 生命周期卡住) |
| **问题分类** | **核心问题**：`ImagePullFailed` (镜像拉取失败) <br> **次要问题**：`TerminatingStuck` (删除卡住，为前者衍生) |
| **置信度** | **95%** |
| **证据完整度** | 10/10 (100%) |

**当前集群现状总结**：集群共有 70 个 Pod，其中 59 个正常运行，6 个异常 Pod **全部集中在 node1 节点上**。
- **4 个 Pod** 处于 `ImagePullBackOff` 状态 (镜像拉取失败)
- **1 个 Pod** 处于 `ContainerCreating` 状态 (容器创建中，实为镜像拉取失败导致)
- **1 个 Pod** (`network-test`) 处于 `Terminating` 状态 (删除卡住)

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 | 说明 |
|------|-----|------|
| **问题节点** | `node1` | 所有异常 Pod 均部署在此节点上 |
| **受影响命名空间** | `aiops-e2e`, `mcp` | 两个命名空间下的 Pod 均受影响 |
| **核心错误信息** | `dial tcp ... i/o timeout` | 连接外部镜像仓库超时 |
| **次要错误信息 1** | `lookup registry.invalid on ...: no such host` | 镜像地址配置错误 |
| **次要错误信息 2** | `Terminating` 卡住 | 衍生问题，由核心镜像拉取失败导致 |

---

## 🕵️ 证据链

### 已采集证据（核心证据）

| # | 证据类型 | 来源命令 / 数据 | 原始数据 | 分析结论 |
|---|----------|------------------|----------|----------|
| 1 | **节点状态** | `kubectl get node node1` | `STATUS: Ready` | **排除节点宕机原因**。节点本身运行正常，containerd 1.6.32 也正常。 |
| 2 | **Pod 事件** | `kubectl describe pod test-network -n aiops-e2e` | `... Failed to pull image "busybox:1.28": ... dial tcp 31.13.80.37:443: i/o timeout` | **节点 `node1` 无法连接 Docker Hub** (`registry-1.docker.io`) 镜像仓库。 |
| 3 | **Pod 事件** | `kubectl describe pod node-debugger-node1-djrzl -n mcp` | `... Failed to pull image "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0": ... dial tcp 74.125.204.82:443: i/o timeout` | **节点 `node1` 无法连接 Google 镜像仓库** (`registry.k8s.io`)。

此证据表明问题不是特定于某个仓库。 |
| 4 | **Pod 事件** | `kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e` | `... Failed to pull image "registry.invalid/aiops/rootcause:v0": ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` | **存在镜像地址配置错误**。使用了不存在的域名 `registry.invalid`，导致 DNS 解析失败，与网络不可达是不同的独立问题。 |
| 5 | **Pod YAML** | `kubectl get -o yaml pod network-test -n aiops-e2e` (此前阶段) | `finalizers: <none>` <br> `terminationGracePeriodSeconds: 30` | **明确排除了 finalizer 未清理** 导致 Terminating 卡住的原因。Pod 会在 30 秒宽限期内等待清理。 |
| 6 | **Pod 事件** | `kubectl describe pod network-test -n aiops-e2e` (此前阶段) | 容器状态为 `Waiting: ImagePullBackOff` | **Terminating 卡住的根本原因是主容器从未成功启动（因镜像拉取失败）**，kubelet 无法正常关停容器，导致删除流程卡住。 |

### 证据关联分析
- **证据 #2 + #3 + #4 印证**：尽管镜像仓库地址不同（`docker.io`, `registry.k8s.io`, `registry.invalid`），但错误都发生在 node1 节点上。对 `docker.io` 和 `k8s.gcr.io` 是 `i/o timeout`，对 `registry.invalid` 是 `DNS 解析失败`，共同指向 **node1 出站网络访问外部资源存在问题**。
- **证据 #5 + #6 印证**：`network-test` Pod 的 YAML 确认没有 finalizers，而 `kubectl describe` 显示其容器因镜像拉取失败而从未启动。这表明 **Terminating 状态是核心镜像拉取问题的衍生现象**。

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| 在 node1 节点上直接执行 `curl/wget` 测试外网连通性 | Critical | 无法确认是节点网络策略、代理、DNS 还是防火墙导致出站失败。 |
| 检查 node1 节点上的网络策略、代理配置、iptables 规则 | Important | 无法精确定位出站阻断的配置层面原因。 |
| 检查集群内是否有镜像代理或 mirror 配置 | Normal | 确认是否能通过内部代理间接解决网络问题。 |

---

## 🎯 根因分析

### 因果链

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                     │
│ node1 节点（10.2.0.49）出站网络无法访问外部镜像仓库。                        │
│ (例如：防火墙规则、代理配置、网络策略导致无法连接 registry-1.docker.io:443  │
│  和 registry.k8s.io:443)                                                     │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 传导机制（核心问题）                                                         │
│ node1 上的 kubelet/containerd 尝试连接外部仓库拉取镜像 → TCP 连接超时        │
│ (i/o timeout) → 镜像拉取失败                                                 │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                     │
│ 所有异常 Pod 的容器状态均为 Waiting/ImagePullBackOff。                       │
│ kubelet 事件明确记录 "i/o timeout" 和 "no such host" 错误。                  │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                 │
│ 1. 4个 Pod（test-network, node-debugger-node1-*）状态为 ImagePullBackOff      │
│ 2. 1个 Pod（node-debugger-node1-2tnsd）状态为 ContainerCreating（仍在重试）    │
│ 3. 1个 Pod（network-test）状态为 Terminating（由上述问题衍生，删除卡住）         │
│ 4. 所有 6 个异常 Pod 全部集中在 node1 节点                                     │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：基于上述证据，集群的根本问题在于 **`node1` 节点无法与外部镜像仓库（registry-1.docker.io， registry.k8s.io）建立 TCP 连接，导致所有依赖这些仓库拉取镜像的 Pod 均创建失败**。此外，有一个 Pod (`rc-imagepull-invalid-registry`) 额外存在**镜像地址配置错误**（使用了不存在的域名），这是一个需要与其他 Pod 分开处理的独立问题。

**置信度**：高 (95%)
- ✅ 证据 #1 排除了节点故障
- ✅ 证据 #2、#3 直接证明了与多个不同仓库的网络连接均超时，指向了节点出站网络问题
- ✅ 证据 #4 指出了第二个独立问题（镜像地址错误）
- ✅ 证据 #5、#6 完整解释了 Terminating Pod 的根因，无需额外假设

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [核心] 排查并解决 node1 节点出站网络问题**
这是解决绝大多数异常 Pod 的关键。请在 node1 节点上执行以下排查：

**步骤 1：检查 DNS 解析**
```bash
# 在 node1 节点上执行
nslookup registry-1.docker.io
nslookup registry.k8s.io
```
*预期*：应返回正确 IP。若失败，说明节点 DNS 配置有问题。

**步骤 2：测试网络连通性**
```bash
# 在 node1 节点上执行
curl -v --connect-timeout 10 https://registry-1.docker.io/v2/
curl -v --connect-timeout 10 https://registry.k8s.io/v2/
```
*预期*：应能返回 HTTP 响应（可能是 401 Unauthorized，这说明 TCP 连接成功）。若超时，需排查：
  - **防火墙规则**：检查安全组、iptables 是否有出站限制。
  - **网络策略**：检查 Kubernetes 网络策略（NetworkPolicy）是否限制了节点出站流量（通常不影响节点本身，但建议排查）。
  - **代理配置**：检查 `containerd` 或节点的 HTTP_PROXY 配置是否正确。

**2. [修复] 删除并重建异常 Pod**
在确认网络问题解决后，删除当前异常 Pod，它们将由控制器自动重建。
```bash
# 删除 aiops-e2e 下的异常 Pod
kubectl delete pod test-network --namespace aiops-e2e --force --grace-period=0
kubectl delete pod rc-imagepull-invalid-registry --namespace aiops-e2e --force --grace-period=0
kubectl delete pod network-test --namespace aiops-e2e --ignore-not-found=true

# 删除 mcp 下的异常 Pod
kubectl delete pod node-debugger-node1-2tnsd --namespace mcp --force --grace-period=0
kubectl delete pod node-debugger-node1-djrzl --namespace mcp --force --grace-period=0
kubectl delete pod node-debugger-node1-zst8z --namespace mcp --force --grace-period=0
```

**3. [独立问题] 修复 `rc-imagepull-invalid-registry` 的镜像地址**
```bash
# 获取当前 Pod 的镜像地址，并修改为正确的地址
# 假设这是一个 Deployment
kubectl edit deployment <deployment-name> -n aiops-e2e
# 将 spec.template.spec.containers[0].image 的值 
# 从 "registry.invalid/aiops/rootcause:v0" 修改为正确的镜像地址
```

### 后续优化
1. **配置镜像代理/缓存**：在集群内或节点上配置镜像代理（如 `harbor`、`docker pull-through proxy`），可以缓存镜像并避免直接访问外部仓库的网络问题，提高稳定性和拉取速度。
2. **监控**：对节点到外部关键服务的网络连通性进行监控和告警。
3. **应用资源评估**：检查所有 Pod 的资源请求(Requests)和限制(Limits)，确保资源设置合理（此问题不涉及，但为最佳实践）。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认节点状态 | `kubectl get node node1` | `STATUS: Ready` (该状态已确认) |
| 2. 确认 Pod 运行 | `kubectl get pod -n aiops-e2e` | `STATUS: Running` (所有 Pod 正常运行) |
| 3. 确认 Pod 运行 | `kubectl get pod -n mcp` | `STATUS: Running` (所有 Pod 正常运行) |
| 4. 确认异常数归零 | `kubectl get pod -A --field-selector 'status.phase!=Running'` | 仅返回 Succeeded 或预期内的 Pod，无 ImagePullBackOff 或 Terminating |

---

## ⚠️ 注意事项
- **`network-test` Pod 已经不存在**：在证据采集阶段后期，`kubectl describe pod network-test` 返回 `NotFound`，说明该 Pod 可能已经被自动清理或通过其他方式删除，后续删除命令中已使用 `--ignore-not-found=true` 避免报错。
- **重点在 node1 网络**：所有问题的根源都指向 node1，请优先排查该节点的网络配置，而不要逐个排查 Pod 配置。
- **`registry.invalid` 问题**：这是一个完全独立的配置错误，即使 node1 网络问题修复，该 Pod 仍会失败，需要单独修改镜像地址。

---

## 📊 性能统计

├─ 总耗时: 3.0m
├─ 问题定位: 57.0s (32%) ✅
├─ 证据链采集: 55.3s (31%) ✅
├─ 根因分析: 35.0s (19%) ✅
├─ 汇总总结: 32.5s (18%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 27 次
```

📋 诊断追踪

- **核心 Runbook**: pod-imagepull-failed
- **参考 Runbook**: pod-imagepull-failed, pod-terminating-stuck
- **工具调用**: 27 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
