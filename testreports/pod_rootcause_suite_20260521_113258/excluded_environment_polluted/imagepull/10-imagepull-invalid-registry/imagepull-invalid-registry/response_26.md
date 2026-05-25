======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: e5e724a99fef41f1]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，让我先扫描整个集群的 Pod 状态，看看全局情况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=70 abnormal=6 status_counts={'Running': 59, 'Terminating': 1, 'ImagePullBackOff': 4}
NAMESPACE         NAME                                                REA
   💭 [问题定位] 发现了 6 个异常 Pod。我来进一步了解细节，先看看各异常 Pod 和一些 runbook 参考。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=7 abnormal=3 status_counts={'Running': 1, 'ImagePullBackOff': 2}
NAME                                  READY   STATUS              RESTARTS   AGE     IP    
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=3 abnormal=3 status_counts={'Terminating': 1, 'ImagePullBackOff': 2}
NAME                            READY   STATUS             RESTARTS   AGE     IP       
   💭 [问题定位] 让我进一步确认这些异常 Pod 的状态详情，特别是看看 `mcp/node-debugger-node1-2tnsd` 的 ContainerCreating 是什么原因。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod node-debugger-node1-djrzl (namespace mcp, node node1/10.2.0.49) is Pending. Container "debugger" with image registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0 is Waiting (ImagePullBackOff) and no
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: network-test
namespace: aiops-e2e
node: node1/10.2.0.49
status: Terminating (lasts 46s)
关键诊断行:
  Warning  Failed          106s                 kubelet            Failed to p
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
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-imagepull-invalid-registry
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          30m (x4 over 32m)     kubelet            Failed to
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod test-network in namespace aiops-e2e, node node1/10.2.0.49, status Pending. Container test-network image busybox:1.28. State Waiting (Reason: ImagePullBackOff), Ready False, Restart Count 0. All pu
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 Pod node-debugger-node1-zst8z (namespace mcp) on node node1/10.2.0.49 is Pending. Container "debugger" with image busybox:1.28 is Waiting (Reason: ImagePullBackOff), not Ready. All 3 pull attempts to 
   💭 [问题定位] 现在我已经掌握了所有信息。让我取一下相关的 runbook 来参考定位。
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
   💭 [问题定位] 现在我已经收集了足够的证据。让我也快速确认一下集群节点状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 好的，所有节点健康。现在让我做最终分析。

---

## 📋 全局 Pod 异常分析报告

### 当前异常 Pod 列表

| 命名空间 | Pod 名称 | 状态 | 异常类型 |
|---------|---------|------|---------|
| `aiops-e2e` | `rc-imagepull-invalid-registry` | ImagePullBackOff | **镜像拉取失败** |
| `aiops-e2e` | `test-network` | ImagePullBackOff | **镜像拉取失败** |
| `aiops-e2e` | `network-test` | Terminating | **删除卡住** |
| `mcp` | `node-debugger-node1-djrzl` | ImagePullBackOff | **镜像拉取失败** |
| `mcp` | `node-debugger-node1-zst8z` | ImagePullBackOff | **镜像拉取失败** |
| `mcp` | `node-debugger-node1-2tnsd` | ContainerCreating | **镜像拉取中（也可能超时）** |

---

### 🟡 异常组 1: 镜像拉取失败 (ImagePullFailed) — 兼容层级 L3
**涉及 Pod (5个)：**
1. **`aiops-e2e/rc-imagepull-invalid-registry`** — 镜像 `registry.invalid/aiops/rootcause:v0` → DNS 解析失败 `no such host`
2. **`aiops-e2e/test-network`** — 镜像 `busybox:1.28` → 连接 `registry-1.docker.io` **i/o timeout**
3. **`aiops-e2e/network-test`** (已 Terminating，但原因也是拉取失败) — 同样 `busybox:1.28` → **i/o timeout**
4. **`mcp/node-debugger-node1-djrzl`** — 镜像 `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0` → **i/o timeout**
5. **`mcp/node-debugger-node1-zst8z`** — 镜像 `busybox:1.28` → **i/o timeout**

**根因分类：**
- **`registry.invalid`** DNS 解析失败（域名不存在）
- **`docker.io`** 和 **`registry.k8s.io`** 均因 **网络 i/o timeout** 无法拉取（节点 `node1` 无法访问外网镜像仓库）

**关键证据：** 所有拉取失败都发生在同一节点 `node1` 上，表明这是**节点出口网络问题**（无法连接外网镜像仓库），而非单个 Pod 配置问题。

---

### 🟡 异常组 2: Terminating 卡住 — 兼容层级 L1
**涉及 Pod：** `aiops-e2e/network-test`

该 Pod 处于 `Terminating` 状态已有约 46 秒（最早事件 2 分钟前），容器实际原因也是镜像拉取失败。terminationGracePeriodSeconds 为 30s，已在正常宽限期外。Node 正常 Ready，推测是 kubelet 在完成容器清理过程中因拉取镜像失败导致的卡住。

---

### 🟡 异常组 3: ContainerCreating — 兼容层级 L3
**涉及 Pod：** `mcp/node-debugger-node1-2tnsd`（刚创建 72 秒，还在 Pulling 阶段）
- 镜像 `busybox:1.28`，当前状态为 `Pulling`，尚未超时报错，但同节点的其他同镜像 Pod 都已失败，预计也会超时。

---

### ✅ 集群健康基线
| 维度 | 状态 |
|-----|------|
| **Node** | 3 个节点全部 **Ready** ✅ |
| **Running Pods** | 59/70 (84%) 正常运行 |
| **节点分布** | 所有异常 Pod 集中在 **node1** |

---

### 📌 结论总结

| 字段 | 值 |
|------|-----|
| **layer** | L3 |
| **layer_name** | 镜像拉取失败 (ImagePullFailed) |
| **derived_layer** | L3 |
| **layers** | L3 (镜像拉取失败为主), L1 (Terminating 卡住) |
| **pod_status_keyword** | ImagePullBackOff, Terminating, ContainerCreating |
| **pod_abnormal_type** | ImagePullFailed |
| **status_category** | image_pull |
| **confidence** | 高 |
| **key_entities** | node1, registry-1.docker.io, registry.k8s.io, registry.invalid |
| **possible_scenarios** | 节点 node1 无法访问外部镜像仓库（Docker Hub、Google Container Registry），导致所有需要拉取外部镜像的 Pod 失败。`registry.invalid` 本身是不存在的域名，属于 e2e 测试用例。整体网络出口或 DNS 解析存在问题。 |
   ✅ [问题定位] 完成 (51.5s)
   📤 → 下游数据: layer=Layer.L3, layers=L3+L1
   scenarios=[{'scenario': '节点node1无法访问外部镜像仓库', 'probability': '高', 'reason': '所有ImagePullBackOff Pod都集中在node1，且错误均为i/o timeout dialing docker.io/registry.k8s.io，表明node1出口网络不通'}, {'scenario': 'DNS解析失败导致registry.invalid不可达', 'probability': '高', 'reason': 'rc-imagepull-invalid-registry的events显示lookup registry.invalid: no such host，该域名本身不存在'}, {'scenario': 'node1出口防火墙/NAT限制', 'probability': '中', 'reason': '多个外部镜像仓库均超时，非单个仓库问题，猜测节点缺少外网访问能力'}]
   entities=[{"type": "node", "name": "node1", "namespace": ""}, {"type": "registry", "name": "registry-1.docker.io", "namespace": ""}, {"type": "registry", "name": "registry.k8s.io", "namespace": ""}, {"type": "registry", "name": "registry.invalid", "namespace": ""}]
   reasoning=集群存在6个异常Pod，其中5个处于ImagePullBackOff状态（1个ContainerCreating也在拉取中），全部集中在node1。镜像拉取失败原因：1) registry.invalid DNS解析失败（域名不存在）；2) busybox:1.28和registry.k8s.io镜像因i/o timeout无法从外网拉取（node1无法访问docker.io和gcr.io）。所有节点Ready，因此问题根因是节点出口网络问题导致镜像拉取失败，归类L3。另有一个Terminating Pod（network-test）属于L1生命周期问题，但根本原因仍是镜像拉取失败。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3", "L1"], "layer_name": "镜像拉取失败 (ImagePullFailed)", "confidence": 0.95, "reasoning": "集群存在6个异常Pod，其中5个处于ImagePullBackOff状态（1个ContainerCreating也在拉取中），全部集中在node1。镜像拉取失败原因：1) registry.invalid DNS解析失败（域名不存在）；2) busybox:1.28和registry.k8s.io镜像因i/o timeout无法从外网拉取（node1无法访问docker.io和gcr.io）。所有节点Ready，因此问题根因是节点出口网络问题导致镜像拉取失败，归类L3。另有一个Terminating Pod（network-test）属于L1生命周期问题，但根本原因仍是镜像拉取失败。", "abnormal_pods": [{"name": "network-test", "namespace": "aiops-e2e", "status": "Terminating"}, {"name": "rc-imagepull-invalid-registry", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "test-network", "namespace": "aiops-e2e", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-2tnsd", "namespace": "mcp", "status": "ContainerCreating"}, {"name": "node-debugger-node1-djrzl", "namespace": "mcp", "status": "ImagePullBackOff"}, {"name": "node-debugger-node1-zst8z", "namespace": "mcp", "status": "ImagePullBackOff"}], "pod_status_keyword": "ImagePullBackOff, Terminating, ContainerCreating", "pod_abnormal_type": "ImagePullFailed", "status_category": "image_pull", "key_entities": [{"type": "node", "name": "node1", "namespace": ""}, {"type": "registry", "name": "registry-1.docker.io", "namespace": ""}, {"type": "registry", "name": "registry.k8s.io", "namespace": ""}, {"type": "registry", "name": "registry.invalid", "namespace": ""}], "possible_scenarios": [{"scenario": "节点node1无法访问外部镜像仓库", "probability": "高", "reason": "所有ImagePullBackOff Pod都集中在node1，且错误均为i/o timeout dialing docker.io/registry.k8s.io，表明node1出口网络不通"}, {"scenario": "DNS解析失败导致registry.invalid不可达", "probability": "高", "reason": "rc-imagepull-invalid-registry的events显示lookup registry.invalid: no such host，该域名本身不存在"}, {"scenario": "node1出口防火墙/NAT限制", "probability": "中", "reason": "多个外部镜像仓库均超时，非单个仓库问题，猜测节点缺少外网访问能力"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "network-test"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-invalid-registry"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "test-network"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-djrzl"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-zst8z"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2tnsd"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Terminating"], "pod_abnormal_type": "TerminatingStuck", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "network-test"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "finalizer 未清理", "probability": "中", "reason": "需验证 metadata.finalizers 与 deletionTimestamp"}, {"scenario": "kubelet 无响应或节点侧删除流程卡住", "probability": "中", "reason": "需验证 Pod 所在节点状态和事件"}, {"scenario": "卷卸载或 detach 流程卡住", "probability": "中", "reason": "需验证 volumes、PVC/PV 和相关事件"}]}, {"group_id": "g2", "status_keywords": ["ImagePullBackOff"], "pod_abnormal_type": "ImagePullFailed", "compatible_layers": ["L3"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-imagepull-invalid-registry"}, {"kind": "Pod", "namespace": "aiops-e2e", "name": "test-network"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-djrzl"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-zst8z"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "镜像地址或 tag 不存在", "probability": "中", "reason": "需通过 Events/镜像地址验证"}, {"scenario": "imagePullSecret 缺失或认证失败", "probability": "中", "reason": "需验证 Pod spec 与 Secret"}, {"scenario": "节点到镜像仓库网络不可达", "probability": "中", "reason": "需验证 registry 连通性、DNS 或 TLS"}]}, {"group_id": "g3", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-2tnsd"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Terminating": 1, "ImagePullBackOff": 4}, "total_abnormal": 5, "selected_rows": ["aiops-e2e         network-test                                        0/1     Terminating         0              2m8s    172.16.166.160   node1    <none>           <none>            run=network-test", "aiops-e2e         rc-imagepull-invalid-registry                       0/1     ImagePullBackOff    0              32m     172.16.166.147   node1    <none>           <none>            app=rc-imagepull-invalid-registry,pod_abnormal_type=ImagePullFailed,rootcause-e2e=true", "aiops-e2e         test-network                                        0/1     ImagePullBackOff    0              5m42s   172.16.166.133   node1    <none>           <none>            run=test-network", "mcp               node-debugger-node1-2tnsd                           0/1     ContainerCreating   0              64s     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-djrzl                           0/1     ImagePullBackOff    0              14m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-zst8z                           0/1     ImagePullBackOff    0              4m26s   10.2.0.49        node1    <none>           <none>            <none>"], "raw_ref": "/tmp/aiops/reports/context_archives/e5e724a99fef41f1/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/e5e724a99fef41f1/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/e5e724a99fef41f1/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L3 + L1（主层级: Layer.L3）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我直接执行既有 evidence_plan 中的工具调用。先并行执行所有独立的工具。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod node-debugger-node1-djrzl (namespace=mcp, node=node1/10.2.0.49) status=Pending. Container debugger: Image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0, State=Waiting(ImagePullBackOff), Read
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 输出摘要: raw_chars=135 lines=3
Command failed (exit 1):
kubectl get -o yaml pod network-test -n aiops-e2e
Error from server (NotFound): pods "network-test" not found
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 Pod test-network (ns: aiops-e2e) on node node1 (10.2.0.49) is Pending with IP 172.16.166.133. Container test-network uses image busybox:1.28, State: Waiting (Reason: ImagePullBackOff), Ready: False, R
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-imagepull-invalid-registry
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          31m (x4 over 33m)     kubelet            Failed to
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                        READY   STATUS         RESTARTS   AGE    IP          NODE    NOMINATED NODE   READINESS GATES   LABELS
node-debugger-node1-2tnsd   0/1     ErrImagePull   0          2m8s   
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                        READY   STATUS             RESTARTS   AGE     IP          NODE    NOMINATED NODE   READINESS GATES   LABELS
node-debugger-node1-zst8z   0/1     ImagePullBackOff   0        
   💭 [证据链采集] 几项工具已返回结果。我来总结一下发现：

## 证据采集报告

### ✅ g2 组（ImagePullBackOff — 主异常组）完整验证

| 计划项 | 结果 | 证据状态 |
|--------|------|----------|
| **ev-g2-1**: `rc-imagepull-invalid-registry` describe | ✅ **registry.invalid DNS 解析失败仍为当前状态** — `dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (31m ago, x4 over 33m) | **已采集** |
| **ev-g2-2**: `test-network` describe | ✅ **busybox:1.28 从 docker.io 拉取 i/o timeout 仍为当前状态** — `dial tcp 31.13.80.37:443: i/o timeout` (x2) 和 `118.184.78.78:443: i/o timeout` | **已采集** |
| **ev-g2-3**: `node-debugger-node1-djrzl` describe | ✅ **registry.k8s.io 拉取 i/o timeout 仍为当前状态** — `dial tcp 74.125.204.82:443: i/o timeout`，连接 asia-east1/europe-west2 docker.pkg.dev 均超时 | **已采集** |
| **ev-g2-4**: `node-debugger-node1-zst8z` get | ✅ **ImagePullBackOff 状态仍然存在** — READY=0/1, STATUS=ImagePullBackOff, AGE=5m30s | **已采集** |

### ⚠️ g1 组（Terminating — 非主异常组）最小验证

| 计划项 | 结果 | 证据状态 |
|--------|------|----------|
| **ev-g1-1**: `network-test` YAML | ❌ **Pod 已不存在** — `Error from server (NotFound): pods "network-test" not found` | **冲突证据：该 Pod 已删除**，不再处于 Terminating 状态 |

### ✅ g3 组（ContainerCreating — 非主异常组）最小验证

| 计划项 | 结果 | 证据状态 |
|--------|------|----------|
| **ev-g3-1**: `node-debugger-node1-2tnsd` get | ✅ 状态已变为 **ErrImagePull**（不再是 ContainerCreating），Image=busybox:1.28 | **已采集** |

---

## 最终证据结论

### 主异常：ImagePullFailed（g2 组 — 4 个 Pod，全部集中在 node1）

所有 4 个 ImagePullBackOff Pod 的当前拉取失败原因均已确认，与上游定位一致：

1. **registry.invalid DNS 不存在**（`rc-imagepull-invalid-registry`）— `no such host`
2. **docker.io (registry-1.docker.io) 网络超时**（`test-network`、`node-debugger-node1-2tnsd`、`node-debugger-node1-zst8z`）— `i/o timeout` 连接 31.13.80.37:443 和 118.184.78.78:443
3. **registry.k8s.io (GCR) 网络超时**（`node-debugger-node1-djrzl`）— `i/o timeout` 连接 74.125.204.82:443

**根因锁定**：node1 节点出口无法访问外部镜像仓库（docker.io、registry.k8s.io），且 `registry.invalid` 是根本不存在的域名。

### 非主异常：Terminating（g1 组）

`network-test` Pod 已从集群中完全删除（NotFound），不再是当前故障。该 Terminating 状态已自动解决。

### 非主异常：ContainerCreating（g3 组）

`node-debugger-node1-2tnsd` 已从 ContainerCreating 变为 **ErrImagePull**（busybox:1.28），同属 docker.io 网络不可达问题，与主根因一致。
   ✅ [证据链采集] 完成 (33.6s)
   📤 → 下游数据: evidence_items=15/16
   evidence_analysis={"evidence_plan":[{"id":"ev-g2-1","description":"Master异常组g2: describe rc-imagepull-invalid-registry (registry.invalid DNS失败)作为ImagePullFailed代表Pod","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-imagepull-invalid-registry","namespace":"aiops-e2e"},"purpose":"确认registry.invalid DNS解析失败事件是否仍为当前状态","evidence_type":"current_status","target_scope":"g2代表Pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-g2-2","description":"Master异常组g2: describe test-network (busybox:1.28 docker.io超时)作为ImagePullFailed代表Pod","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-network -n aiops-e2e","tool_args":{"kind":"Pod","name":"test-network","namespace":"aiops-e2e"},"purpose":"确认busybox:1.28从docker.io拉取i/o timeout是否仍为当前状态","evidence_type":"current_status","target_scope":"g2代表Pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-g2-3","description":"Master异常组g2: describe node-debugger-node1-djrzl (registry.k8s.io超时)作为mcp命名空间ImagePullFailed代表Pod","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-djrzl -n mcp","tool_args":{"kind":"Pod","name":"node-debugger-node1-djrzl","namespace":"mcp"},"purpose":"确认registry.k8s.io拉取i/o timeout是否仍为当前状态","evidence_type":"current_status","target_scope":"g2代表Pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-g2-4","description":"验证node-debugger-node1-zst8z当前状态(最小验证)","level":"important","tool":"kubectl_get_by_name","command":"kubectl get pod node-debugger-node1-zst8z -n mcp","tool_args":{"kind":"Pod","name":"node-debugger-node1-zst8z","namespace":"mcp"},"purpose":"确认ImagePullBackOff状态仍然存在","evidence_type":"current_status","target_scope":"g2最小验证","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-g1-1","description":"异常组g1 Terminating: 获取network-test的YAML检查deletionTimestamp和finalizers","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod network-test -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"network-test","namespace":"aiops-e2e"},"purpose":"确认deletionTimestamp、finalizers、terminationGracePeriodSeconds等关键字段","evidence_type":"current_status","target_scope":"g1代表Pod","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"ev-g3-1","description":"异常组g3 ContainerCreating: 获取node-debugger-node1-2tnsd当前状态和事件","level":"important","tool":"kubectl_get_by_name","command":"kubectl get pod node-debugger-node1-2tnsd -n mcp","tool_args":{"kind":"Pod","name":"node-debugger-node1-2tnsd","namespace":"mcp"},"purpose":"确认ContainerCreating状态是否仍存在","evidence_type":"current_status","target_scope":"g3最小验证","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"Pod node-debugger-node1-djrzl (namespace=mcp, node=node1/10.2.0.49) status=Pending. Container debugger: Image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0, State=Waiting(ImagePullBackOff), Ready=False, RestartCount=0. Command: nslookup registry.invalid. Events show repeated image pull failures (DeadlineExceeded/Unknown) to multiple GCR registry endpoints (asia-east1, europe-west2) all timing out dial tcp 74.125.204.82:443. Also ErrImagePull x4, ImagePullBackOff x6, BackOff x43. Volumes: host-root(/), kube-api-access. QoS=BestEffort. Tolerations: op=Exists.\nkey_facts: [\"name: node-debugger-node1-djrzl\", \"namespace: mcp\", \"node: node1/10.2.0.49\", \"status: Pending\", \"container: debugger\", \"image: registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\", \"container state: Waiting (Reason: ImagePullBackOff)\", \"container Ready: False\", \"command: nslookup registry.invalid\", \"Failed to pull image - DeadlineExceeded/Unknown to asia-east1-docker.pkg.dev and europe-west2-docker.pkg.dev; all dial tcp 74.125.204.82:443 i/o timeout\", \"Events: Failed(15m,13m,12m x2,5m15s), ErrImagePull(12m x4), ImagePullBackOff(11m x6), BackOff(47s x43)\", \"QoS Class: BestEffort\", \"Tolerations: op=Exists\", \"Volumes: host-root(/), kube-api-access-kt6fd\"]\nconflicts: [\"raw_preview shows 'Pulling' event (12m x4 over 16m) not in current_summary\"]\nmissing: [\"No Container ID or Image ID set\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e5e724a99fef41f1/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e5e724a99fef41f1/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e5e724a99fef41f1/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 输出摘要: raw_chars=135 lines=3\nCommand failed (exit 1):\nkubectl get -o yaml pod network-test -n aiops-e2e\nError from server (NotFound): pods \"network-test\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/e5e724a99fef41f1/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e5e724a99fef41f1/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e5e724a99fef41f1/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"Pod test-network (ns: aiops-e2e) on node node1 (10.2.0.49) is Pending with IP 172.16.166.133. Container test-network uses image busybox:1.28, State: Waiting (Reason: ImagePullBackOff), Ready: False, Restart Count: 0. Repeated pull failures to docker.io/library/busybox:1.28 — all attempts timeout dialing registry-1.docker.io (IPs 31.13.80.37, 118.184.78.78:443). Events show ErrImagePull and ImagePullBackOff. Pod was successfully scheduled and interface added.\nkey_facts: [\"Pod: test-network | Namespace: aiops-e2e | Node: node1/10.2.0.49\", \"Status: Pending | IP: 172.16.166.133\", \"Container: test-network | Image: busybox:1.28 | State: Waiting (ImagePullBackOff) | Ready: False | Restart Count: 0\", \"QoS Class: BestEffort\", \"Failed to pull image \\\"busybox:1.28\\\": rpc error: code=DeadlineExceeded/Unknown — dial tcp 31.13.80.37:443: i/o timeout (x2 events)\", \"Failed to pull image: dial tcp 118.184.78.78:443: i/o timeout (DeadlineExceeded) — 1 event\", \"Event: Failed (ErrImagePull) x4 over 5m45s\", \"Event: Failed (ImagePullBackOff) x7 over 5m45s\", \"Event: Normal BackOff x7 — Back-off pulling image \\\"busybox:1.28\\\"\", \"Event: Normal Scheduled (assigned to node1)\", \"Event: Normal AddedInterface (eth0 172.16.166.133/32 from k8s-pod-network)\", \"Pod Conditions: Initialized=True, Ready=False, ContainersReady=False, PodScheduled=True\"]\nconflicts: [\"current_summary omits 'Normal Scheduled' and 'Normal AddedInterface' events present in raw_preview\"]\nmissing: [\"container args (nslookup/wget commands) not in summary\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e5e724a99fef41f1/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e5e724a99fef41f1/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e5e724a99fef41f1/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-imagepull-invalid-registry\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          31m (x4 over 33m)     kubelet            Failed to pull image \"registry.invalid/aiops/rootcause:v0\": rpc error: code = Unknown desc = failed to pull and unpack image \"registry.invalid/aiops/rootcause:v0\": failed to resolve reference \"registry.invalid/aiops/rootcause:v0\": failed to do request: Head \"https://registry.invalid/v2/aiops/rootcause/manifests/v0\": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host\n  Normal   BackOff         3m3s (x117 over 33m)  kubelet            Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"\n      Reason:       ImagePullBackOff\n  Warning  Failed          31m (x6 over 33m)     kubelet            Error: ImagePullBackOff\n  Warning  Failed          31m (x4 over 33m)     kubelet            Error: ErrImagePull\n                  cni.projectcalico.org/containerID: 6b564b34bd28dd42f6854bbc537d2155cfdab18a1486aa3ea2979833ebeaadd1\n                  cni.projectcalico.org/podIP: 172.16.166.147/32\n                  cni.projectcalico.org/podIPs: 172.16.166.147/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:          registry.invalid/aiops/rootcause:v0\n    Image ID:\n    State:          Waiting\n      Reason:       ImagePullBackOff\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  kube-api-access-6zmg5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  Failed          31m (x6 over 33m)     kubelet            Error: ImagePullBackOff\n  Warning  Failed          31m (x4 over 33m)     kubelet            Failed to pull image \"registry.invalid/aiops/rootcause:v0\": rpc error: code = Unknown desc = failed to pull and unpack image \"registry.invalid/aiops/rootcause:v0\": failed to resolve reference \"registry.invalid/aiops/rootcause:v0\": failed to do request: Head \"https://registry.invalid/v2/aiops/rootcause/manifests/v0\": dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host\n  Warning  Failed          31m (x4 over 33m)     kubelet            Error: ErrImagePull\n  Normal   BackOff         3m3s (x117 over 33m)  kubelet            Back-off pulling image \"registry.invalid/aiops/rootcause:v0\"\n关键状态/事件:\n                  pod_abnormal_type=ImagePullFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e5e724a99fef41f1/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e5e724a99fef41f1/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e5e724a99fef41f1/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                        READY   STATUS         RESTARTS   AGE    IP          NODE    NOMINATED NODE   READINESS GATES   LABELS\nnode-debugger-node1-2tnsd   0/1     ErrImagePull   0          2m8s   10.2.0.49   node1   <none>           <none>            <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e5e724a99fef41f1/tools/005-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e5e724a99fef41f1/tools/005-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e5e724a99fef41f1/tools/005-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                        READY   STATUS             RESTARTS   AGE     IP          NODE    NOMINATED NODE   READINESS GATES   LABELS\nnode-debugger-node1-zst8z   0/1     ImagePullBackOff   0          5m30s   10.2.0.49   node1   <none>           <none>            <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e5e724a99fef41f1/tools/006-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e5e724a99fef41f1/tools/006-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e5e724a99fef41f1/tools/006-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"几项工具已返回结果。我来总结一下发现：\n\n## 证据采集报告\n\n### ✅ g2 组（ImagePullBackOff — 主异常组）完整验证\n\n| 计划项 | 结果 | 证据状态 |\n|--------|------|----------|\n| **ev-g2-1**: `rc-imagepull-invalid-registry` describe | ✅ **registry.invalid DNS 解析失败仍为当前状态** — `dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host` (31m ago, x4 over 33m) | **已采集** |\n| **ev-g2-2**: `test-network` describe | ✅ **busybox:1.28 从 docker.io 拉取 i/o timeout 仍为当前状态** — `dial tcp 31.13.80.37:443: i/o timeout` (x2) 和 `118.184.78.78:443: i/o timeout` | **已采集** |\n| **ev-g2-3**: `node-debugger-node1-djrzl` describe | ✅ **registry.k8s.io 拉取 i/o timeout 仍为当前状态** — `dial tcp 74.125.204.82:443: i/o timeout`，连接 asia-east1/europe-west2 docker.pkg.dev 均超时 | **已采集** |\n| **ev-g2-4**: `node-debugger-node1-zst8z` get | ✅ **ImagePullBackOff 状态仍然存在** — READY=0/1, STATUS=ImagePullBackOff, AGE=5m30s | **已采集** |\n\n### ⚠️ g1 组（Terminating — 非主异常组）最小验证\n\n| 计划项 | 结果 | 证据状态 |\n|--------|------|----------|\n| **ev-g1-1**: `network-test` YAML | ❌ **Pod 已不存在** — `Error from server (NotFound): pods \"network-test\" not found` | **冲突证据：该 Pod 已删除**，不再处于 Terminating 状态 |\n\n### ✅ g3 组（ContainerCreating — 非主异常组）最小验证\n\n| 计划项 | 结果 | 证据状态 |\n|--------|------|----------|\n| **ev-g3-1**: `node-debugger-node1-2tnsd` get | ✅ 状态已变为 **ErrImagePull**（不再是 ContainerCreating），Image=busybox:1.28 | **已采集** |\n\n---\n\n## 最终证据结论\n\n### 主异常：ImagePullFailed（g2 组 — 4 个 Pod，全部集中在 node1）\n\n所有 4 个 ImagePullBackOff Pod 的当前拉取失败原因均已确认，与上游定位一致：\n\n1. **registry.invalid DNS 不存在**（`rc-imagepull-invalid-registry`）— `no such host`\n2. **docker.io (registry-1.docker.io) 网络超时**（`test-network`、`node-debugger-node1-2tnsd`、`node-debugger-node1-zst8z`）— `i/o timeout` 连接 31.13.80.37:443 和 118.184.78.78:443\n3. **registry.k8s.io (GCR) 网络超时**（`node-debugger-node1-djrzl`）— `i/o timeout` 连接 74.125.204.82:443\n\n**根因锁定**：node1 节点出口无法访问外部镜像仓库（docker.io、registry.k8s.io），且 `registry.invalid` 是根本不存在的域名。\n\n### 非主异常：Terminating（g1 组）\n\n`network-test` Pod 已从集群中完全删除（NotFound），不再是当前故障。该 Terminating 状态已自动解决。\n\n### 非主异常：ContainerCreating（g3 组）\n\n`node-debugger-node1-2tnsd` 已从 ContainerCreating 变为 **ErrImagePull**（busybox:1.28），同属 docker.io 网络不可达问题，与主根因一致。","collection_summary":"计划 6 项，实际采集 5 项，未采集 1 项，完整度 83%；其中真实环境证据 15/16 项，完整度 94%；实际执行工具 16 个，匹配计划 5 个，未规划证据 11 个","plan_total":6,"plan_collected":5,"plan_completeness":0.8333333333333334,"environment_evidence_total":16,"environment_evidence_collected":15,"environment_evidence_completeness":0.9375,"executed_tool_count":16,"matched_tool_count":5,"unplanned_tool_count":11,"evidence_inventory":[{"id":"ev-g2-1","description":"Master异常组g2: describe rc-imagepull-invalid-registry (registry.invalid DNS失败)作为ImagePullFailed代表Pod","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e","purpose":"确认registry.invalid DNS解析失败事件是否仍为当前状态","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-g2-2","description":"Master异常组g2: describe test-network (busybox:1.28 docker.io超时)作为ImagePullFailed代表Pod","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod test-network -n aiops-e2e","purpose":"确认busybox:1.28从docker.io拉取i/o timeout是否仍为当前状态","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-g2-3","description":"Master异常组g2: describe node-debugger-node1-djrzl (registry.k8s.io超时)作为mcp命名空间ImagePullFailed代表Pod","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-djrzl -n mcp","purpose":"确认registry.k8s.io拉取i/o timeout是否仍为当前状态","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-g2-4","description":"验证node-debugger-node1-zst8z当前状态(最小验证)","level":"important","tool":"kubectl_get_by_name","command":"kubectl get pod node-debugger-node1-zst8z -n mcp","purpose":"确认ImagePullBackOff状态仍然存在","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"ev-g1-1","description":"异常组g1 Terminating: 获取network-test的YAML检查deletionTimestamp和finalizers","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod network-test -n aiops-e2e -o yaml","purpose":"确认deletionTimestamp、finalizers、terminationGracePeriodSeconds等关键字段","collected":false,"source":"planned","outcome":"unknown"},{"id":"ev-g3-1","description":"异常组g3 ContainerCreating: 获取node-debugger-node1-2tnsd当前状态和事件","level":"important","tool":"kubectl_get_by_name","command":"kubectl get pod node-debugger-node1-2tnsd -n mcp","purpose":"确认ContainerCreating状态是否仍存在","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_8","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_9","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_10","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["ev-g1-1(异常组g1 Terminating: 获取network-test的YAML检查deletionTimestamp和finalizers): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 5/6 项, 完整度: 94%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | ev-g2-1 | critical | ✅ | kubectl_describe | Master异常组g2: describe rc-imagepull-invalid-re... | `kubectl describe pod rc-imagepull-invalid-registry -n aiops-e2e` |
   | ev-g2-2 | critical | ✅ | kubectl_describe | Master异常组g2: describe test-network (busybox:1... | `kubectl describe pod test-network -n aiops-e2e` |
   | ev-g2-3 | critical | ✅ | kubectl_describe | Master异常组g2: describe node-debugger-node1-djr... | `kubectl describe pod node-debugger-node1-djrzl -n mcp` |
   | ev-g2-4 | important | ✅ | kubectl_get_by_name | 验证node-debugger-node1-zst8z当前状态(最小验证) | `kubectl get pod node-debugger-node1-zst8z -n mcp` |
   | ev-g1-1 | critical | ❌ | kubectl_get_yaml | 异常组g1 Terminating: 获取network-test的YAML检查delet... | `kubectl get pod network-test -n aiops-e2e -o yaml` |
   | ev-g3-1 | important | ✅ | kubectl_get_by_name | 异常组g3 ContainerCreating: 获取node-debugger-node... | `kubectl get pod node-debugger-node1-2tnsd -n mcp` |

   ⚠️ 未采集原因:
   - ev-g1-1(异常组g1 Terminating: 获取network-test的YAML检查deletionTimestamp和finalizers): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (27.2s)
   📤 → 下游数据: root_cause=集群根因：node1节点出口网络无法访问外部容器镜像仓库。具体证据：1) test-network和node-debugger-node1-zst8z拉取busybox:1.28时对registry-1.docker.io（31.13.80.37:443和118.184.78.78:443）TCP连接超时（i/o timeout）；2) node-debugger-node1-djrzl拉取registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0时对asia-east1-docker.pkg.dev和europe-west2-docker.pkg.dev（74.125.204.82:443）均超时；3) rc-imagepull-invalid-registry的镜像地址registry.invalid根本不存在（DNS lookup no such host）。全部5个异常Pod（4个ImagePullBackOff+1个ErrImagePull）集中在node1节点，3个节点均Ready无异常，因此根因为node1出口网络受限+无效镜像
... 截断，原始 566 字符
   confidence=95%
   causal_chain={"root_cause": "node1节点出口网络无法访问外部镜像仓库（docker.io、registry.k8s.io），同时registry.invalid为无效域名", "propagation": "node1节点到公网的出口网络受限（可能缺少NAT/防火墙规则）→ kubelet在node1上尝试拉取外部镜像时TCP连接超时→ 所有依赖外部镜像的Pod均因无法拉取镜像而陷入ImagePullBackOff/ErrImagePull状态", "direct_cause": "kubelet在node1上拉取docker.io/library/busybox:1.28和registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0时TCP连接超时（i/o timeout），拉取registry.invalid/aiops/rootcause:v0时DNS解析失败（no such host）", "manifestation": "4个Pod处于ImagePullBackOff（rc-imagepull-invalid-registry、test-network、node-debugger-node1-djrzl、node-debugger-node1-zst8z），1个Pod处于ErrImagePull（node-debugger-node1-2tnsd），全部集中在node1节点；另1个Terminating Pod（network-test）已自动消失"}
   rca_analysis={"phenomenon": "集群共有6个异常Pod（4个ImagePullBackOff、1个ContainerCreating已转为ErrImagePull、1个Terminating已自动消失），全部集中在node1节点，所有节点自身Ready状态正常。异常Pod均因镜像拉取失败无法启动。", "evidence_inventory": [{"id": "ev-g2-1", "source": "kubectl_describe rc-imagepull-invalid-registry", "content": "registry.invalid DNS解析失败导致镜像拉取失败：dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host", "reliability": "高"}, {"id": "ev-g2-2", "source": "kubectl_describe test-network", "content": "busybox:1.28从docker.io拉取超时：dial tcp 31.13.80.37:443和118.184.78.78:443 i/o timeout", "reliability": "高"}, {"id": "ev-g2-3", "source": "kubectl_describe node-debugger-node1-djrzl", "content": "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0拉取超时：dial tcp 74.125.204.82:443 i/o timeout连接asia-east1/europe-west2 docker.pkg.dev均失败", "reliability": "高"}, {"id": "ev-g2-4", "source": "kubectl_get_by_name node-debugger-node1-zst8z", "content": "ImagePullBackOff状态确认，AGE=5m30s，同一节点相同busybox:1.28镜像拉取失败", "reliability": "高"}, {"id": "ev-g3-1", "source": "kubectl_get_by_name node-debugger-node1-2tnsd", "content": "状态已从ContainerCreating转为ErrImagePull，AGE=2m8s，同一busybox:1.28镜像", "reliability": "高"}, {"id": "ev-g1-conflict", "source": "kubectl_get_yaml network-test", "content": "Pod network-test已不存在：Error from server (NotFound)", "reliability": "高"}, {"id": "ev-node-status", "source": "kubectl_get_by_kind_in_cluster nodes", "content": "3节点全部Ready（master/worker），node1状态正常", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "ev-g2-1", "raw_data": "rc-imagepull-invalid-registry: Failed to pull image \"registry.invalid/aiops/rootcause:v0\" ... dial tcp: lookup registry.invalid on 127.0.0.53:53: no such host", "interpretation": "registry.invalid域名在DNS中不存在，属于测试用的无效域名，因此镜像拉取必然失败。这不是网络问题，而是镜像地址配置错误。"}, {"evidence_id": "ev-g2-2", "raw_data": "test-network: Failed to pull image \"busybox:1.28\" ... dial tcp 31.13.80.37:443: i/o timeout", "interpretation": "node1节点无法连接到docker.io镜像仓库（registry-1.docker.io），TCP连接超时，表明节点出口网络到公网不通"}, {"evidence_id": "ev-g2-3", "raw_data": "node-debugger-node1-djrzl: Failed to pull image \"registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0\" ... dial tcp 74.125.204.82:443: i/o timeout", "interpretation": "node1节点同样无法连接registry.k8s.io（GCR），两个不同的外部仓库均超时，进一步印证节点出口网络问题"}, {"evidence_id": "ev-g2-4", "raw_data": "node-debugger-node1-zst8z: STATUS=ImagePullBackOff, AGE=5m30s, Image=busybox:1.28", "interpretation": "g2组第4个Pod确认持续处于ImagePullBackOff状态，与test-network相同镜像，同一节点"}, {"evidence_id": "ev-g3-1", "raw_data": "node-debugger-node1-2tnsd: STATUS=ErrImagePull, AGE=2m8s, Image=busybox:1.28", "interpretation": "原ContainerCreating状态已自动变为ErrImagePull，本质上与g2组是同一个根因——busybox:1.28镜像拉取失败"}, {"evidence_id": "ev-g1-conflict", "raw_data": "kubectl get -o yaml pod network-test -n aiops-e2e: Error from server (NotFound)", "interpretation": "Terminating状态的network-test Pod已从集群中完全删除，不再属于当前故障。该异常组已自动解决。"}, {"evidence_id": "ev-node-status", "raw_data": "3 nodes all Ready, node1 Ready as well", "interpretation": "节点自身健康无异常，问题不在节点层面，而是节点到外部镜像仓库的网络连接受限"}], "causal_chain": {"root_cause": "node1节点出口网络无法访问外部镜像仓库（docker.io、registry.k8s.io），同时registry.invalid为无效域名", "propagation": "node1节点到公网的出口网络受限（可能缺少NAT/防火墙规则）→ kubelet在node1上尝试拉取外部镜像时TCP连接超时→ 所有依赖外部镜像的Pod均因无法拉取镜像而陷入ImagePullBackOff/ErrImagePull状态", "direct_cause": "kubelet在node1上拉取docker.io/library/busybox:1.28和registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0时TCP连接超时（i/o timeout），拉取registry.invalid/aiops/rootcause:v0时DNS解析失败（no such host）", "manifestation": "4个Pod处于ImagePullBackOff（rc-imagepull-invalid-registry、test-network、node-debugger-node1-djrzl、node-debugger-node1-zst8z），1个Pod处于ErrImagePull（node-debugger-node1-2tnsd），全部集中在node1节点；另1个Terminating Pod（network-test）已自动消失"}, "root_cause": "集群根因：node1节点出口网络无法访问外部容器镜像仓库。具体证据：1) test-network和node-debugger-node1-zst8z拉取busybox:1.28时对registry-1.docker.io（31.13.80.37:443和118.184.78.78:443）TCP连接超时（i/o timeout）；2) node-debugger-node1-djrzl拉取registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0时对asia-east1-docker.pkg.dev和europe-west2-docker.pkg.dev（74.125.204.82:443）均超时；3) rc-imagepull-invalid-registry的镜像地址registry.invalid根本不存在（DNS lookup no such host）。全部5个异常Pod（4个ImagePullBackOff+1个ErrImagePull）集中在node1节点，3个节点均Ready无异常，因此根因为node1出口网络受限+无效镜像\n... 截断，原始 566 字符", "root_cause_summary": "集群根因：node1节点出口网络无法访问外部容器镜像仓库。具体证据：1) test-network和node-debugger-node1-zst8z拉取busybox:1.28时对registry-1.docker.io（31.13.80.37:443和118.184.78.78:443）TCP连接超时（i/o timeout）；2) node-debugger-node1-djrzl拉取registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0时对asia-east1-docker.pkg.dev和europe-west2-docker.pkg.dev（74.125.204.82:443）均超时；3) rc-imagepull-invalid-registry的镜像地址registry.invalid根本不存在（DNS lookup no such host）。全部5个异常Pod（4个ImagePullBackOff+1个ErrImagePull）集中在node1节点，3个节点均Ready无异常，因此根因为node1出口网络受限+无效镜像\n... 截断，原始 566 字符", "confidence": 0.95, "confidence_reason": "所有ImagePullBackOff/ErrImagePull Pod的当前状态均已通过kubectl_describe/kubectl_get_by_name直接验证，错误消息明确显示i/o timeout和DNS no such host，因果链清晰完整，无间接推理。节点状态也从kubectl_get_nodes确认全部Ready。置信度0.95。", "primary_runbooks": ["pod-imagepullfailed.md"], "alternative_causes": [{"cause": "imagePullSecret缺失或认证失败", "probability": "low", "reason": "所有拉取失败的错误均为网络超时或DNS解析失败，无401/403认证错误，排除此场景"}, {"cause": "镜像tag不存在", "probability": "low", "reason": "i/o timeout错误发生在TCP连接阶段，尚未到达镜像清单检查阶段；registry.invalid是域名不存在，不是镜像不存在"}, {"cause": "节点kubelet故障", "probability": "low", "reason": "节点Ready状态正常，kubelet能正常上报Events和Pod状态，排除kubelet本身问题"}, {"cause": "节点磁盘满导致无法拉取镜像", "probability": "low", "reason": "错误信息为i/o timeout和DNS解析失败，无磁盘空间相关错误"}], "limitations": "未在node1节点上直接执行curl/wget验证出口网络连通性（如curl https://registry-1.docker.io/v2/），但Pod级别kubelet的i/o timeout事件已足够证明网络不可达。registry.invalid域名不存在属于配置错误而非网络问题，与网络不通是两个独立的子根因。", "llm_raw_analysis": "## 证据清点\\n共采集15条证据（含上游已验证的10条），涉及3个异常组。\\n- g1（Terminating）: 1个Pod network-test，但kubectl_get_yaml返回NotFound，该Pod已自动删除\\n- g2（ImagePullBackOff）: 4个Pod，全部在node1，均已完成describe验证\\n- g3（ContainerCreating→ErrImagePull）: 1个Pod node-debugger-node1-2tnsd已转为ErrImagePull\\n\\n## 逐条分析\\n### g2组核心证据\\n1. rc-imagepull-invalid-registry → registry.invalid DNS no such host（域名不存在）\\n2. test-network → busybox:1.28 docker.io i/o timeout（31.13.80.37:443和118.184.78.78:443）\\n3. node-debugger-node1-djrzl → registry.k8s.io i/o t\n... 截断，原始 966 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群根因：node1节点出口网络无法访问外部容器镜像仓库。具体证据：1) test-network和node-debugger-node1-zst8z拉取busybox:1.28时对registry-1.docker.io（31.13.80.37:443和118.184.78.78:443）TCP连...
   置信度: 95%
   🔗 因果链:
     根本原因: node1节点出口网络无法访问外部镜像仓库（docker.io、registry.k8s.io），同时registry.invalid为无效域名
     传导机制: node1节点到公网的出口网络受限（可能缺少NAT/防火墙规则）→ kubelet在node1上尝试拉取外部镜像时TCP连接超时→ 所有依赖外部镜像的Pod均因无法拉取镜像而陷入ImagePullBackOff/ErrImagePull状态
     最终表现: 4个Pod处于ImagePullBackOff（rc-imagepull-invalid-registry、test-network、node-debugger-node1-djrzl、node-debugger-node1-zst8z），1个Pod处于ErrImagePull（node-debugger-node1-2tnsd），全部集中在node1节点；另1个Terminating Pod（network-test）已自动消失


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (30.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 7039 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 22.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将基于你提供的详尽上下文，生成一份完整的诊断报告。

---

## 📊 现象速览

您的集群当前存在 **5个异常Pod**（另有1个Terminating Pod已消失），核心问题是 **节点node1无法从外部容器镜像仓库拉取镜像**。

**核心问题总结：**
- **问题类型**: 镜像拉取失败 (ImagePullFailed)
- **影响范围**: 5个异常Pod全部集中在 **node1** 节点
- **根本原因**: node1 节点 **出口网络受限**，无法访问公网镜像仓库 (docker.io, registry.k8s.io)，且存在无效的镜像地址 (registry.invalid)
- **附加问题**: 1个已消失的Terminating Pod，其根因同样为镜像拉取失败

**异常Pod状态分布：**
| 状态 | 数量 | Pod 名称 (命名空间) |
|---|---|---|
| `ImagePullBackOff` | 4 | `rc-imagepull-invalid-registry` (aiops-e2e), `test-network` (aiops-e2e), `node-debugger-node1-djrzl` (mcp), `node-debugger-node1-zst8z` (mcp) |
| `ContainerCreating` / `ErrImagePull` | 1 | `node-debugger-node1-2tnsd` (mcp) |

---

## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ImagePullBackOff, Terminating, ContainerCreating |
| **兼容归因层** | L3 - 网络连通性 |
| **问题分类** | ImagePullFailed - 镜像拉取失败 |
| **置信度** | 高 (95%) |
| **证据完整度** | 5/6 (83%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-imagepull-invalid-registry, test-network, node-debugger-node1-djrzl, node-debugger-node1-zst8z, node-debugger-node1-2tnsd |
| Namespace | aiops-e2e, mcp |
| Node | node1 |
| 错误信息 | `i/o timeout`, `no such host` |

---

## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 (关键片段) | 分析结论 |
|---|----------|----------|----------|----------|
| **1** | Pod 事件 | kubectl_describe (test-network) | `...Failed to pull image "busybox:1.28"...dial tcp 31.13.80.37:443: i/o timeout` | 节点 node1 无法连接到 docker.io 镜像仓库 (IP: 31.13.80.37) |
| **2** | Pod 事件 | kubectl_describe (node-debugger-node1-djrzl) | `...Failed to pull image "registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0"...dial tcp 74.125.204.82:443: i/o timeout` | 节点 node1 无法连接到 registry.k8s.io 镜像仓库 |
| **3** | Pod 事件 | kubectl_describe (rc-imagepull-invalid-registry) | `...Failed to pull image "registry.invalid/aiops/rootcause:v0"...lookup registry.invalid on 127.0.0.53:53: no such host` | 镜像地址 `registry.invalid` 是无效域名，DNS 解析失败。 |
| **4** | Pod 状态 | kubectl_get_by_name (node-debugger-node1-2tnsd) | `STATUS: ErrImagePull` | mcp 命名空间下的 `node-debugger-node1-2tnsd` Pod 同样处于镜像拉取失败状态。 |
| **5** | Pod 状态 | kubectl_get_by_name (node-debugger-node1-zst8z) | `STATUS: ImagePullBackOff` | mcp 命名空间下的 `node-debugger-node1-zst8z` Pod 位于 ImagePullBackOff 状态，符合镜像拉取失败特征。 |
| **6** | 集群状态 | kubectl_get_by_kind_in_cluster (Nodes) | `STATUS: Ready` (所有3个节点) | 集群内所有节点状态正常，排除节点宕机或 kubelet 故障导致拉取失败的可能。 |

### 证据关联分析
- **证据 #1 + #2 + #4 印证**：**`test-network`** 和 **`node-debugger-node1-2tnsd`** 尝试拉取 `busybox:1.28` (来自 docker.io) 时超时；**`node-debugger-node1-djrzl`** 拉取 `registry.k8s.io` 镜像时也超时。这表明 `node1` 节点的出口网络策略限制了对外部镜像仓库的访问。
- **证据 #3 印证**：**`rc-imagepull-invalid-registry`** 使用了不存在的域名 `registry.invalid`，属于应用配置错误，与网络问题叠加。
- **证据 #5 + #6 印证**：所有异常 Pod 均位于同一节点，且节点健康，将故障范围锁定在 `node1` 的出口网络层面。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| `network-test` Pod 的 YAML | Critical | 无法确认该 Pod 的 `finalizers` 和 `deletionTimestamp` 状态，但该 Pod 已消失，无法采集。 |

---

## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 1. 节点 node1 的出口网络被防火墙/NAT规则限制，无法访问外网      │
│ 2. 应用配置了不存在的镜像仓库地址 registry.invalid              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 当 Pod 调度到 node1 后，kubelet 尝试拉取镜像时：                 │
│ - 向 registry-1.docker.io (外网) 发起的 TCP 连接超时 (i/o timeout)│
│ - 向 registry.k8s.io (外网) 发起的 TCP 连接超时 (i/o timeout)   │
│ - 向 registry.invalid (不存在的域名) 发起的 DNS 查询失败         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ kubelet 无法从外部镜像仓库拉取所需的容器镜像                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ 集群中存在 5 个异常 Pod，均处于 ImagePullBackOff 或 ErrImagePull │
│ 状态，并全部集中在 node1 节点上                                 │
└─────────────────────────────────────────────────────────────────┘
```
### 根因结论

**结论**：根据证据 #1, #2 (外部仓库连接超时)，证据 #3 (无效域名无法解析)，以及证据 #6 (节点本身健康)，
问题的根本原因是 **节点 `node1` 的出口网络无法访问外部容器镜像仓库 (docker.io, registry.k8s.io)**，同时 **`rc-imagepull-invalid-registry` Pod 使用的镜像地址 `registry.invalid` 为无效域名**。

**置信度**：高 (95%)
- ✅ `kubectl describe` 的事件清晰地显示了 `i/o timeout` 和 `no such host` 错误
- ✅ 所有异常 Pod 都集中在 `node1`，排除了镜像或认证等全局性问题
- ✅ 集群内所有 `Node` 状态均为 `Ready`，排除节点级故障

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 解决节点出口网络问题**
请联系网络管理员，检查并放通 **node1** 节点到以下地址的 HTTPS (443端口) 出口流量：
- **docker.io**: `registry-1.docker.io` 以及相关的 CDN 节点
- **registry.k8s.io**: `registry.k8s.io` 以及相关的 `*.pkg.dev` 域名
- 或者为 node1 节点配置 HTTP 代理服务器，用于拉取外部镜像。

**2. [优先] 修正无效的镜像地址**
修复 `rc-imagepull-invalid-registry` Pod 或对应的 Deployment/StatefulSet 的镜像地址。
```bash
# 找到并修改对应的 Deployment 或 StatefulSet 的镜像地址
# 例如，如果它是由 Deployment 管理的：
kubectl edit deployment rc-imagepull-invalid-registry -n aiops-e2e
# 将 image: registry.invalid/aiops/rootcause:v0 修改为正确的镜像地址
```

**3. [辅助] 使用内部镜像仓库解决问题**
如果集群无法访问公网，最佳实践是将外部镜像推送到内部镜像仓库，然后修改所有 Pod 的镜像地址。例如，将 `busybox:1.28` 和 `registry.k8s.io/e2e-test-images/jessie-dnsutils:1.0` 推送到私有仓库 `harbor.example.com/library/` 后，执行以下修改：
```bash
# 修改 test-network Pod
kubectl set image pod/test-network -n aiops-e2e test-network=harbor.example.com/library/busybox:1.28

# 修改 mcp 命名空间下的 node-debugger Pods (需要找到其上层控制器，如 DaemonSet)
# kubectl set image daemonset/<daemonset-name> -n mcp debugger=harbor.example.com/library/busybox:1.28
# kubectl set image daemonset/<daemonset-name> -n mcp debugger=harbor.example.com/library/jessie-dnsutils:1.0
```

### 后续优化
1. **监控告警**：配置 Pod 状态监控，对 `ImagePullBackOff` 和 `ErrImagePull` 状态进行告警
2. **策略优化**：在集群中部署 `ClusterPolicy` 或 `ImagePolicyWebhook`，强制要求所有镜像必须来自内部仓库，避免使用不安全的公网镜像
3. **验证无效问题**：确认 **`rc-imagepull-invalid-registry`** 和 **`node-debugger-node1-djrzl`** 中 `command: ["nslookup", "registry.invalid"]` 是否是测试脚本的一部分，避免在生产中出现类似配置。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认节点连通性 | `kubectl exec -it <any-running-pod> -n <ns> -- curl -v https://registry-1.docker.io/v2/ --connect-timeout 10` | 返回 `HTTP/1.1 401 Unauthorized` 或类似的响应，而非 `Connection timed out` |
| 2. 确认 Pod 状态恢复 | `kubectl get pod -n aiops-e2e` 和 `kubectl get pod -n mcp` | 所有之前异常的 Pod 状态变为 `Running` 或 `Completed` |
| 3. 检查 Pod 事件 | `kubectl describe pod <pod-name> -n <namespace>` | 不再出现 `Failed to pull image ... i/o timeout` 等错误事件 |

---

## ⚠️ 注意事项
- 执行任何修改前，请确认对业务的影响。如果 `mcp` 命名空间下的 `node-debugger` Pod 是用于调试的 DaemonSet，修改其镜像后可能会触发滚动更新
- 如果集群是私有部署且内部已有镜像仓库，强烈建议将所有依赖的外部镜像同步到内部仓库，避免对外网的依赖，提升集群稳定性和拉取速度
- 终端用户报告的问题（`network-test` Pod 卡住）其根本原因与镜像拉取问题一致，该 Pod 已自动清理，无需额外关注

---

## 📊 性能统计

├─ 总耗时: 2.4m
├─ 问题定位: 51.5s (36%) ✅
├─ 证据链采集: 33.6s (24%) ✅
├─ 根因分析: 27.2s (19%) ✅
├─ 汇总总结: 30.0s (21%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 18 次
```

📋 诊断追踪

- **参考 Runbook**: pod-terminating-stuck, pod-imagepull-failed
- **工具调用**: 18 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
