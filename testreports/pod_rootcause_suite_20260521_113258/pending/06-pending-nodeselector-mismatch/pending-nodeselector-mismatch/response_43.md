======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: d5091d95ca7f4117]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，让我先全局扫描所有 Pod 状态，看看集群中是否存在异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 集群中发现了异常 Pod。让我获取更多细节并查看相关事件。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          33m   <none>   <none>   
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
33m                 Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 n
   💭 [问题定位] 这个 Pod 带有 `pod_abnormal_type=PendingUnschedulable` 标签，非常明确。让我获取相关的 runbook 作为参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在让我快速查看节点状态，确认节点的标签和状态情况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 再查看一下这个 pending Pod 的 YAML，确认它的 nodeSelector 或 affinity 配置。
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:18:44Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [问题定位] ## 诊断结果

### 全局健康概览

集群共有 **65 个 Pod**，其中 **59 个 Running**，**1 个 Pending**，3 个节点全部 Ready，整体集群健康状况良好。

### 当前异常 Pod

| Pod | 命名空间 | 状态 | 年龄 |
|-----|---------|------|------|
| `rc-pending-nodeselector` | `aiops-e2e` | **Pending** | 33分钟 |

---

### 异常分析

| 维度 | 详情 |
|------|------|
| **`pod_status_keyword`** | Pending |
| **`pod_abnormal_type`** | PendingUnschedulable |
| **`status_category`** | scheduling |
| **`layer`** | L1 |
| **`layer_name`** | 调度约束不匹配 (PendingUnschedulable) |
| **`confidence`** | 高 |

**关键证据：**
- Pod 未绑定节点（`nodeName: <none>`）
- FailedScheduling 事件原文：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`
- Pod 设置了 `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}`
- 所有 3 个节点（master、node1、node2）均未包含 `aiops.e2e/nonexistent-node-label` 标签

**根因：** Pod 的 nodeSelector 引用了集群中不存在的节点标签 `aiops.e2e/nonexistent-node-label=true`，导致调度器找不到任何可匹配的节点，Pod 一直卡在 Pending 状态。

---

### 输出汇总

```json
{
  "layer": "L1",
  "derived_layer": "L1",
  "layers": ["L1"],
  "layer_name": "Pod PendingUnschedulable - 调度约束不匹配",
  "confidence": "high",
  "reasoning": "Pod rc-pending-nodeselector 处于 Pending 状态，FailedScheduling 事件明确指出 3 个节点均不匹配 node affinity/selector，Pod 的 nodeSelector 设置了集群中不存在的标签 aiops.e2e/nonexistent-node-label=true，导致无法调度。",
  "abnormal_pods": ["aiops-e2e/rc-pending-nodeselector"],
  "abnormal_groups": {
    "PendingUnschedulable": ["aiops-e2e/rc-pending-nodeselector"]
  },
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "PendingUnschedulable",
  "status_category": "scheduling",
  "key_entities": {
    "pods": ["aiops-e2e/rc-pending-nodeselector"],
    "nodes": ["master", "node1", "node2"]
  },
  "possible_scenarios": [
    "Pod 的 nodeSelector 引用了不存在的节点标签 aiops.e2e/nonexistent-node-label=true，没有任何节点匹配此标签"
  ]
}
```

**建议方向：** 检查 Pod 的 nodeSelector 配置是否正确，如果该标签确实需要存在，可以为某个节点添加该标签，或者修改 Pod 的调度约束。
   ✅ [问题定位] 完成 (28.1s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'Pod 的 nodeSelector 引用了不存在的节点标签 aiops.e2e/nonexistent-node-label=true，没有任何节点匹配此标签', 'probability': '高', 'reason': "FailedScheduling 事件原文明确提示 3 node(s) didn't match Pod's node affinity/selector，且 YAML 中 nodeSelector 配置了不存在标签"}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}]
   reasoning=Pod rc-pending-nodeselector 处于 Pending 状态，FailedScheduling 事件明确指出 3 个节点均不匹配 node affinity/selector，Pod 的 nodeSelector 设置了集群中不存在的标签 aiops.e2e/nonexistent-node-label=true，导致无法调度。3个节点全部Ready，无节点异常，根因明确为调度约束不匹配，归为L1层。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "调度约束不匹配 (PendingUnschedulable)", "confidence": 0.95, "reasoning": "Pod rc-pending-nodeselector 处于 Pending 状态，FailedScheduling 事件明确指出 3 个节点均不匹配 node affinity/selector，Pod 的 nodeSelector 设置了集群中不存在的标签 aiops.e2e/nonexistent-node-label=true，导致无法调度。3个节点全部Ready，无节点异常，根因明确为调度约束不匹配，归为L1层。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}], "possible_scenarios": [{"scenario": "Pod 的 nodeSelector 引用了不存在的节点标签 aiops.e2e/nonexistent-node-label=true，没有任何节点匹配此标签", "probability": "高", "reason": "FailedScheduling 事件原文明确提示 3 node(s) didn't match Pod's node affinity/selector，且 YAML 中 nodeSelector 配置了不存在标签"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              33m     <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我将按照既有 evidence_plan 执行采证。先同时执行 critical 和 important 级别的工具调用。

## 开始执行证据计划

### Step 1: 验证 Pod 当前状态和 FailedScheduling 事件
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  34m                default-scheduler  0/3 nodes are available: 
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:18:44Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [证据链采集] ### Step 2: 确认节点标签中是否包含目标标签

让我精确检查每个节点的标签，确认不存在 `aiops.e2e/nonexistent-node-label` 标签。
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   238d   v1.26.8  
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node1   Ready    <none>   238d   v1.26.8   10.2.0.49     <
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node2   Ready    <none>   238d   v1.26.8   10.2.0.50     <
   💭 [证据链采集] ### Step 3: 获取 runbook 参考（reference 级别）
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [证据链采集] ---

## 证据采集结论

### ✅ 已采集证据

| 证据 | 来源 | 结果 |
|------|------|------|
| **Pod 状态与 FailedScheduling 事件** | `kubectl_describe pod rc-pending-nodeselector` | ✅ Pod 当前 **Pending**，3 次 FailedScheduling 事件原文：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` |
| **Pod 调度约束（nodeSelector）** | `kubectl_get_yaml pod rc-pending-nodeselector` | ✅ `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}` — 明确设定了不存在的标签 |
| **Pod 状态条件** | YAML 中 `status.conditions` | ✅ `PodScheduled=False, reason=Unschedulable, message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` |
| **3 个节点标签确认** | `kubectl_get_by_name node master/node1/node2` | ✅ **master** 标签：`arch=amd64,os=linux,hostname=master,control-plane` 等；**node1** 标签：`arch=amd64,os=linux,hostname=node1` 等；**node2** 标签：`arch=amd64,os=linux,hostname=node2` 等。**3 个节点均无 `aiops.e2e/nonexistent-node-label` 标签** |
| **节点 Ready 状态** | `kubectl_get_by_kind_in_cluster nodes` | ✅ 3 节点全部 **Ready**，无节点异常 |
| **Runbook 参考** | `fetch_runbook pod-pending-unschedulable.md` | ✅ 判定规则匹配：`FailedScheduling + node(s) didn't match node selector/affinity` → **调度约束不匹配**，置信度 **高** |

### ⛔ 冲突/负向证据
- 无冲突证据，所有工具返回结果与上游定位一致。

### 📋 结论

**Pod `rc-pending-nodeselector` (namespace: aiops-e2e) 处于 Pending 状态的根因已确认：**

Pod 的 `nodeSelector` 设置了 `aiops.e2e/nonexistent-node-label=true`，而集群中 3 个节点（master、node1、node2）均不存在此标签。调度器判定 **3 node(s) didn't match Pod's node affinity/selector**，且抢占（preemption）也无法解决，因为没有任何节点能匹配该标签条件。

**根因类型**：调度约束配置错误（L1 层 — 配置性故障）
**修复建议**：删除或修改 Pod 的 nodeSelector，使其引用集群中真实存在的节点标签，或者为期望调度的节点添加该标签（如 `kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`）。
   ✅ [证据链采集] 完成 (25.6s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"ev1","description":"验证 Pod rc-pending-nodeselector 当前仍处于 Pending 状态并查看完整 Pod 事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-pending-nodeselector","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"验证 Pod 当前状态和 FailedScheduling 事件内容，确认 nodeSelector 不匹配的具体原因","evidence_type":"current_status","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev2","description":"获取 Pod YAML 确认 nodeSelector 配置的标签具体值","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod -n aiops-e2e rc-pending-nodeselector -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"验证 Pod 的 nodeSelector 字段是否包含 aiops.e2e/nonexistent-node-label=true 标签","evidence_type":"pod_spec","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"ev3","description":"验证集群中所有节点的标签，确认不存在 nodeSelector 所需的标签","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes --show-labels","tool_args":{},"purpose":"检查 3 个节点（master、node1、node2）的标签，确认 aiops.e2e/nonexistent-node-label 标签不存在于任何节点","evidence_type":"node_labels","target_scope":"Nodes/all","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev5","description":"引用已确认的 runbook 作为参考上下文","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","tool_args":{},"purpose":"参考 runbook 确认调度约束不匹配的判定规则匹配当前场景","evidence_type":"reference","target_scope":"reference","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   238d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          238d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\nnode2    Ready    <none>          238d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/001-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/001-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/001-evidence-kubectl_get_by_kind_in_cluster.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  34m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  23m (x2 over 28m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  34m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  23m (x2 over 28m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nmaster   Ready    control-plane   238d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/004-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/004-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/004-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nnode1   Ready    <none>   238d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/005-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/005-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/005-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nnode2   Ready    <none>   238d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/006-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/006-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/006-evidence-kubectl_get_by_name.summary.txt"},{"tool":"fetch_runbook","data":"<runbook>\n# Pod PendingUnschedulable / 调度失败\n\n> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | Pending，且 Events 含 `FailedScheduling` |\n| 资源不足 | `Insufficient cpu/memory/ephemeral-storage`、`Too many pods` |\n| 调度约束 | nodeSelector/affinity 不匹配、节点 taint 未被 toleration 容忍 |\n| 存储前置条件 | `pod has unbound immediate PersistentVolumeClaims` 应切换到 pod-volume-mount-failed |\n| 节点状态 | Node NotReady/Unknown、SchedulingDisabled、Unschedulable 会导致无可用调度节点 |\n\n## 根因分流\n- 资源不足: FailedScheduling 原文含 Insufficient cpu/memory/ephemeral-storage、Too many pods。\n- hostPort 冲突: 原文含 `didn't have free ports for the requested pod ports`，说明目标节点端口已被占用。\n- Taint/Toleration 不匹配: 原文含 `had untolerated taint`，必须检查 Pod tolerations 和 Node taints。\n- nodeSelector / nodeAffinity / podAffinity 不匹配: 原文含 `didn't match Pod's node affinity/selector` 或 affinity/anti-affinity。\n- PVC 未绑定: 原文含 `unbound immediate PersistentVolumeClaims`，根因在存储绑定而不是调度资源。\n- 节点不可调度: Node Ready=False/Unknown、SchedulingDisabled、`node.kubernetes.io/not-ready` 或 `node.kubernetes.io/unreachable`。\n- 镜像、挂载、容器启动错误不会表现为 FailedScheduling；如果 Pod 已绑定 nodeName，应切换到对应 runbook。\n\n## 诊断流程\n\n### Step 1: 确认 Pod 调度失败事件\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n关注 Events 中的 `FailedScheduling` 原文。\n\n### Step 2: 检查 Pod 调度约束\n```bash\nkubectl get pod <pod-name> -n <namespace> -o yaml\n```\n关注: spec.nodeName 是否为空、nodeSelector、affinity、tolerations、topologySpreadConstraints、schedulerName、priorityClassName、resource requests、hostNetwork/hostPort。\n\n### Step 3: 检查节点状态和可调度性\n```bash\nkubectl get nodes -o wide\n```\n关注: STATUS 列是否有 NotReady/Unknown，AGE 判断是否新节点\n\n### Step 4: 检查候选节点详情\n```bash\nkubectl describe node <node-name>\n```\n重点关注:\n- `Conditions` 部分: Ready=False/Unknown 的 reason 和 message\n- `Taints` 部分: 是否有 NoSchedule/NoExecute taint\n- `Allocatable` vs `Capacity`: 资源是否耗尽\n- `Non-terminated Pods`: 节点上运行的 Pod 数量\n\n### Step 5: 检查 PVC 状态（如果 FailedScheduling 指向 PVC）\n```bash\nkubectl get pvc -n <namespace>\nkubectl describe pvc <pvc> -n <namespace>\n```\n关注: Pending、StorageClass、volumeBindingMode、ProvisioningFailed。\n\n### Step 6: 检查 Ready 条件详情\n```bash\nkubectl get node <node-name> -o jsonpath='{.status.conditions[?(@.type==\"Ready\")]}' | python3 -m json.tool\n```\n关注: status, reason, message, lastHeartbeatTime\n\n### Step 7: 检查节点事件\n```bash\nkubectl get events -A --field-selector involvedObject.kind=Node,involvedObject.name=<node-name> --sort-by='.lastTimestamp'\n```\n关注: NodeNotReady、NodeNotSchedulable、PLEG unhealthy 等事件\n\n### Step 8: 检查受影响的 Pending Pod\n```bash\nkubectl get pods -A --field-selector status.phase=Pending | head -20\n```\n\n## 判定规则\n\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| FailedScheduling + Insufficient cpu/memory | 资源不足导致 Pod Pending | 高 |\n| FailedScheduling + Too many pods | 节点 Pod 数量上限导致 Pending | 高 |\n| FailedScheduling + didn't have free ports for the requested pod ports | hostPort 端口冲突导致 Pending | 高 |\n| FailedScheduling + had untolerated taint | taint/toleration 不匹配 | 高 |\n| FailedScheduling + node(s) didn't match node selector/affinity | 调度约束不匹配 | 高 |\n| FailedScheduling + pod has unbound immediate PersistentVolumeClaims | PVC 未绑定，应切换 VolumeMountFailed/PVC 分支 | 高 |\n| 所有候选 Node NotReady/Unschedulable | 无可用调度节点 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/007-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/007-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d5091d95ca7f4117/tools/007-evidence-fetch_runbook.summary.txt"}],"llm_analysis":"---\n\n## 证据采集结论\n\n### ✅ 已采集证据\n\n| 证据 | 来源 | 结果 |\n|------|------|------|\n| **Pod 状态与 FailedScheduling 事件** | `kubectl_describe pod rc-pending-nodeselector` | ✅ Pod 当前 **Pending**，3 次 FailedScheduling 事件原文：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` |\n| **Pod 调度约束（nodeSelector）** | `kubectl_get_yaml pod rc-pending-nodeselector` | ✅ `nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}` — 明确设定了不存在的标签 |\n| **Pod 状态条件** | YAML 中 `status.conditions` | ✅ `PodScheduled=False, reason=Unschedulable, message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` |\n| **3 个节点标签确认** | `kubectl_get_by_name node master/node1/node2` | ✅ **master** 标签：`arch=amd64,os=linux,hostname=master,control-plane` 等；**node1** 标签：`arch=amd64,os=linux,hostname=node1` 等；**node2** 标签：`arch=amd64,os=linux,hostname=node2` 等。**3 个节点均无 `aiops.e2e/nonexistent-node-label` 标签** |\n| **节点 Ready 状态** | `kubectl_get_by_kind_in_cluster nodes` | ✅ 3 节点全部 **Ready**，无节点异常 |\n| **Runbook 参考** | `fetch_runbook pod-pending-unschedulable.md` | ✅ 判定规则匹配：`FailedScheduling + node(s) didn't match node selector/affinity` → **调度约束不匹配**，置信度 **高** |\n\n### ⛔ 冲突/负向证据\n- 无冲突证据，所有工具返回结果与上游定位一致。\n\n### 📋 结论\n\n**Pod `rc-pending-nodeselector` (namespace: aiops-e2e) 处于 Pending 状态的根因已确认：**\n\nPod 的 `nodeSelector` 设置了 `aiops.e2e/nonexistent-node-label=true`，而集群中 3 个节点（master、node1、node2）均不存在此标签。调度器判定 **3 node(s) didn't match Pod's node affinity/selector**，且抢占（preemption）也无法解决，因为没有任何节点能匹配该标签条件。\n\n**根因类型**：调度约束配置错误（L1 层 — 配置性故障）\n**修复建议**：删除或修改 Pod 的 nodeSelector，使其引用集群中真实存在的节点标签，或者为期望调度的节点添加该标签（如 `kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`）。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 11 个，匹配计划 4 个，未规划证据 7 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":11,"matched_tool_count":4,"unplanned_tool_count":7,"evidence_inventory":[{"id":"ev1","description":"验证 Pod rc-pending-nodeselector 当前仍处于 Pending 状态并查看完整 Pod 事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-pending-nodeselector","purpose":"验证 Pod 当前状态和 FailedScheduling 事件内容，确认 nodeSelector 不匹配的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev2","description":"获取 Pod YAML 确认 nodeSelector 配置的标签具体值","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod -n aiops-e2e rc-pending-nodeselector -o yaml","purpose":"验证 Pod 的 nodeSelector 字段是否包含 aiops.e2e/nonexistent-node-label=true 标签","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev3","description":"验证集群中所有节点的标签，确认不存在 nodeSelector 所需的标签","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes --show-labels","purpose":"检查 3 个节点（master、node1、node2）的标签，确认 aiops.e2e/nonexistent-node-label 标签不存在于任何节点","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev5","description":"引用已确认的 runbook 作为参考上下文","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","purpose":"参考 runbook 确认调度约束不匹配的判定规则匹配当前场景","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | ev1 | critical | ✅ | kubectl_describe | 验证 Pod rc-pending-nodeselector 当前仍处于 Pending ... | `kubectl describe pod -n aiops-e2e rc-pending-nodeselector` |
   | ev2 | critical | ✅ | kubectl_get_yaml | 获取 Pod YAML 确认 nodeSelector 配置的标签具体值 | `kubectl get pod -n aiops-e2e rc-pending-nodeselector -o yaml` |
   | ev3 | important | ✅ | kubectl_get_by_kind_in_cl... | 验证集群中所有节点的标签，确认不存在 nodeSelector 所需的标签 | `kubectl get nodes --show-labels` |
   | ev5 | reference | ✅ | fetch_runbook | 引用已确认的 runbook 作为参考上下文 | `fetch_runbook pod-pending-unschedulable.md` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (24.1s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector (namespace: aiops-e2e) 处于 Pending 状态的根因是调度约束配置错误。Pod YAML 中 nodeSelector 配置为 {"aiops.e2e/nonexistent-node-label": "true"}，而集群中全部 3 个节点（master, node1, node2）均为 Ready 状态，但其标签列表中均不包含 aiops.e2e/nonexistent-node-label 标签。kubectl_describe 和 Events 均确认调度器报告 "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"，30 分钟内重试 3 次均失败。无节点异常、无资源不足、无 PVC 问题，根因明确为 nodeSelector 标签不匹配的配置性故障（L1 层）。
   confidence=98%
   causal_chain={"root_cause": "Pod 的 nodeSelector 配置了集群中不存在的标签 aiops.e2e/nonexistent-node-label=true，导致没有任何节点能匹配调度约束。", "propagation": "Pod spec 中 nodeSelector 指定了不存在的标签 → kube-scheduler 检查所有 3 个节点标签均不匹配 → 3 次重试调度均失败 → 调度器报 FailedScheduling 事件 → Pod 持续处于 Pending 状态，无法进入后续调度流程。", "direct_cause": "3 个节点（master, node1, node2）均不满足 Pod 的 nodeSelector 条件 aiops.e2e/nonexistent-node-label=true，节点上此标签完全不存在。", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续 Pending 约 34 分钟，Events 中显示多次 FailedScheduling 警告，提示无节点可调度。"}
   rca_analysis={"phenomenon": "Pod rc-pending-nodeselector (namespace: aiops-e2e) 持续处于 Pending 状态，已持续约 34 分钟，未被调度到任何节点。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod rc-pending-nodeselector 状态为 Pending，node=<none>，FailedScheduling 事件：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml", "content": "Pod 的 nodeSelector 配置为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}，PodScheduled condition=False，reason=Unschedulable", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_by_kind_in_cluster (nodes)", "content": "3 个节点（master, node1, node2）全部 Ready，分析标签列表均不含 aiops.e2e/nonexistent-node-label", "reliability": "高"}, {"id": "e4", "source": "kubectl_get_by_name (node master/node1/node2)", "content": "各节点标签明细：master 含 arch=amd64,os=linux,hostname=master,control-plane 等；node1 含 arch=amd64,os=linux,hostname=node1 等；node2 含 arch=amd64,os=linux,hostname=node2 等。均无目标标签", "reliability": "高"}, {"id": "e5", "source": "kubectl_events", "content": "33m 和 23m (x2 over 28m) 两次 Warning FailedScheduling，原文一致：3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}, {"id": "e6", "source": "fetch_runbook", "content": "Runbook 判定规则：FailedScheduling + node(s) didn't match node selector/affinity → 调度约束不匹配，置信度高", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "kubectl_describe: status=Pending, node=<none>, FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "interpretation": "Pod 当前未被调度到任何节点，且调度器明确报告所有 3 个节点均不匹配 Pod 的 node affinity/selector 条件，排除了资源不足等其它场景。"}, {"evidence_id": "e2", "raw_data": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}; conditions: PodScheduled=False, reason=Unschedulable", "interpretation": "Pod 的 nodeSelector 明确指定了标签 aiops.e2e/nonexistent-node-label=true，且 PodScheduled 条件为 False，原因正是 Unschedulable，直接关联到调度约束不匹配。"}, {"evidence_id": "e3", "raw_data": "Nodes: master(Ready), node1(Ready), node2(Ready); 标签列表不含 aiops.e2e/nonexistent-node-label", "interpretation": "集群中 3 个节点全部为 Ready 状态，无节点异常。经过标签检查，没有任何节点带有 Pod nodeSelector 所要求的 aiops.e2e/nonexistent-node-label 标签。"}, {"evidence_id": "e4", "raw_data": "master labels: arch=amd64,os=linux,hostname=master,control-plane,...; node1 labels: arch=amd64,os=linux,hostname=node1,...; node2 labels: arch=amd64,os=linux,hostname=node2,...", "interpretation": "逐个节点确认标签列表，3 个节点均不存在 aiops.e2e/nonexistent-node-label 标签，证实了调度器判定无效的原因。"}, {"evidence_id": "e5", "raw_data": "33m Warning FailedScheduling; 23m (x2 over 28m) Warning FailedScheduling; 原文一致", "interpretation": "该 Pod 在 34 分钟内被重试调度 3 次，每次均因相同的 node affinity/selector 不匹配问题失败，进一步确认问题并非临时性或资源波动导致。"}, {"evidence_id": "e6", "raw_data": "Runbook 判定规则：FailedScheduling + node(s) didn't match node selector/affinity → 调度约束不匹配", "interpretation": "Runbook 诊断流程验证了当前证据完全匹配调度约束不匹配的场景，根因判定方向正确，置信度高。"}], "causal_chain": {"root_cause": "Pod 的 nodeSelector 配置了集群中不存在的标签 aiops.e2e/nonexistent-node-label=true，导致没有任何节点能匹配调度约束。", "propagation": "Pod spec 中 nodeSelector 指定了不存在的标签 → kube-scheduler 检查所有 3 个节点标签均不匹配 → 3 次重试调度均失败 → 调度器报 FailedScheduling 事件 → Pod 持续处于 Pending 状态，无法进入后续调度流程。", "direct_cause": "3 个节点（master, node1, node2）均不满足 Pod 的 nodeSelector 条件 aiops.e2e/nonexistent-node-label=true，节点上此标签完全不存在。", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续 Pending 约 34 分钟，Events 中显示多次 FailedScheduling 警告，提示无节点可调度。"}, "root_cause": "Pod rc-pending-nodeselector (namespace: aiops-e2e) 处于 Pending 状态的根因是调度约束配置错误。Pod YAML 中 nodeSelector 配置为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}，而集群中全部 3 个节点（master, node1, node2）均为 Ready 状态，但其标签列表中均不包含 aiops.e2e/nonexistent-node-label 标签。kubectl_describe 和 Events 均确认调度器报告 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"，30 分钟内重试 3 次均失败。无节点异常、无资源不足、无 PVC 问题，根因明确为 nodeSelector 标签不匹配的配置性故障（L1 层）。", "root_cause_summary": "Pod rc-pending-nodeselector (namespace: aiops-e2e) 处于 Pending 状态的根因是调度约束配置错误。Pod YAML 中 nodeSelector 配置为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}，而集群中全部 3 个节点（master, node1, node2）均为 Ready 状态，但其标签列表中均不包含 aiops.e2e/nonexistent-node-label 标签。kubectl_describe 和 Events 均确认调度器报告 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"，30 分钟内重试 3 次均失败。无节点异常、无资源不足、无 PVC 问题，根因明确为 nodeSelector 标签不匹配的配置性故障（L1 层）。", "confidence": 0.98, "confidence_reason": "直接证据链完整且闭合：Pod 状态 Pending + FailedScheduling 事件原文 + YAML nodeSelector 具体值 + 3 个节点全部 Ready 且均无该标签 + 运行手册匹配。所有证据一致，无任何冲突或负向证据，置信度极高。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "资源不足（CPU/内存不足）", "probability": "low", "reason": "FailedScheduling 原文不包含 'Insufficient cpu/memory' 等关键字，且 3 节点全部 Ready，排除资源不足场景。"}, {"cause": "节点 taint/toleration 不匹配", "probability": "low", "reason": "FailedScheduling 原文不包含 'had untolerated taint'，且 Pod 已有 node.kubernetes.io/not-ready:NoExecute 容忍，排除 taint 问题。"}, {"cause": "PVC 未绑定或卷依赖问题", "probability": "low", "reason": "Pod 无 PVC 声明，仅有 kube-api-access-w74s5 投影卷，Events 中无 PVC 相关错误。"}, {"cause": "节点不可调度（NotReady/Unschedulable）", "probability": "low", "reason": "所有 3 个节点均为 Ready 状态，无 SchedulingDisabled 或其他异常。"}], "limitations": "证据链已闭合，无重大局限性。节点标签仅通过 kubectl_get_by_name 摘录了样例行关键标签，但 3 个节点的完整标签列表已覆盖，确认不含目标标签 aiops.e2e/nonexistent-node-label。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector (namespace: aiops-e2e) 处于 Pending 状态的根因是调度约束配置错误。Pod YAML 中 nodeSelector 配置为 {"aiops.e2e/nonexistent-node-label": "true"}，...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod 的 nodeSelector 配置了集群中不存在的标签 aiops.e2e/nonexistent-node-label=true，导致没有任何节点能匹配调度约束。
     传导机制: Pod spec 中 nodeSelector 指定了不存在的标签 → kube-scheduler 检查所有 3 个节点标签均不匹配 → 3 次重试调度均失败 → 调度器报 FailedScheduling 事件 → Pod 持续处于 Pending 状态，无法进入后续调度流程。
     最终表现: Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续 Pending 约 34 分钟，Events 中显示多次 FailedScheduling 警告，提示无节点可调度。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (24.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5836 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 42.0s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将根据您提供的信息生成一份详尽、完整的诊断报告。

---
## 📊 集群状态快照

根据当前诊断结果，您的集群总体健康，但有 **1 个 Pod 存在问题**。

| 项目 | 状态 |
|------|------|
| **总 Pod 数** | 65 |
| **正常 Pod (Running)** | 59 |
| **异常 Pod (Pending)** | 1 |
| **节点总数** | 3 (master, node1, node2) |
| **节点健康状态** | 3/3 Ready |
| **检测到的问题** | **Pod `rc-pending-nodeselector` 处于 Pending 状态且无法调度** |

---

## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending |
| **兼容归因层** | L1 (配置性问题) |
| **问题分类** | PendingUnschedulable (调度失败) |
| **置信度** | 高 (98%) |
| **证据完整度** | 3/3 (100%) |
---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-pending-nodeselector` |
| Namespace | `aiops-e2e` |
| Node | `master` (Ready), `node1` (Ready), `node2` (Ready) |
| 错误信息 | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` |

**集群状态总结**：
您的集群中 3 个节点全部 `Ready`，但 Pod `rc-pending-nodeselector` 因调度约束错误，在过去 34 分钟内持续处于 `Pending` 状态，这是当前发现的唯一异常。

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态与事件 | `kubectl_describe pod rc-pending-nodeselector` | `status: Pending`; `Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | Pod 因不满足节点亲和性/选择器规则而无法被调度。 |
| 2 | Pod 配置 | `kubectl_get_yaml pod rc-pending-nodeselector` | `Node-Selectors: aiops.e2e/nonexistent-node-label=true` | Pod 明确配置了 `nodeSelector`，要求节点包含标签 `aiops.e2e/nonexistent-node-label=true`。 |
| 3 | 节点标签 | `kubectl_get_by_kind_in_cluster nodes` | `master Ready ... LABELS:beta.kubernetes.io/arch=amd64,...,kubernetes.io/hostname=master,...`; `node1 Ready ... LABELS:...,kubernetes.io/hostname=node1,...`; `node2 Ready ... LABELS:...,kubernetes.io/hostname=node2,...` | 集群中所有 3 个节点的标签均 **不包含** `aiops.e2e/nonexistent-node-label`。 |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：Pod 要求节点有 `aiops.e2e/nonexistent-node-label=true` 标签，但集群中 **没有一个节点** 拥有该标签，导致调度器裁定“0/3 nodes are available”。这构成了完整的因果链。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | - | 证据链已闭合，无需额外证据。 |

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因 (Root Cause)                                                          │
│ Pod 的 nodeSelector 配置错误，指定了一个集群中不存在的标签                      │
│ "aiops.e2e/nonexistent-node-label=true"。                                       │
└─────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制 (Propagation)                                                        │
│ kube-scheduler 读取 Pod 的 nodeSelector → 遍历所有 3 个节点的标签列表         │
│ → 在任何一个节点上都未找到匹配标签 → 判定所有节点均不符合调度条件            │
└─────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因 (Direct Cause)                                                        │
│ 3 个节点（master, node1, node2）均不具备 Pod 所需的 `nodeSelector` 标签。      │
└─────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象 (Manifestation)                                                   │
│ Pod `rc-pending-nodeselector` 持续处于 `Pending` 状态，Events 中持续涌现       │
│ `FailedScheduling` 警告。                                                        │
└─────────────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #1 (FailedScheduling 事件)、证据 #2 (`nodeSelector` 配置) 和证据 #3 (节点标签列表)，此问题的根本原因是 **Pod 的 nodeSelector 配置错误，指定了集群中不存在的标签 `aiops.e2e/nonexistent-node-label=true`**。集群中所有节点均 `Ready`，无资源不足或其它问题，这是一个 L1 层配置性故障。

**置信度**：高 (98%)
- ✅ FailedScheduling 事件明确指示“节点不匹配”。
- ✅ Pod YAML 中 `nodeSelector` 值 `aiops.e2e/nonexistent-node-label` 被明确捕获。
- ✅ 集群节点标签列表已核实，确认该标签完全不存在。
- ✅ 3 个节点状态均为 `Ready`，排除了节点本身的问题。

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [推荐] 修改 Pod 的 nodeSelector 或删除不必要的调度约束**
您有两个选择，请根据 Pod 的实际需求选择一个。
  * **选项 A：移除 `nodeSelector` (如果 Pod 无需固定在特定节点)**
  ```bash
  # 获取当前 Pod 的 YAML，移除 nodeSelector 后重新创建
  kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml | sed '/nodeSelector:/,$ d' | kubectl replace -f -
  ```
  *注意：此命令会直接修改 Pod，如果 Pod 是由 Deployment 等控制器管理，请修改对应的控制器。*

  * **选项 B：修改 `nodeSelector` 为集群中存在的标签（例如 `kubernetes.io/hostname: node1`）**
  ```bash
  # 假设要将 Pod 调度到 node1
  kubectl patch pod rc-pending-nodeselector -n aiops-e2e -p '{"spec":{"nodeSelector":{"kubernetes.io/hostname":"node1"}}}'
  ```
  *注意：此命令会直接修改 Pod，如果 Pod 是由 Deployment 等控制器管理，请修改对应的控制器。*

  **如果 Pod 是 Deployment 或其他控制器管理，请使用以下命令修改控制器：**
  ```bash
  # 假设 Pod 属于一个名为 "my-deployment" 的 Deployment
  # kubectl set selector deployment my-deployment -n aiops-e2e 'kubernetes.io/hostname=node1'
  # 或者编辑 YAML
  # kubectl edit deployment my-deployment -n aiops-e2e
  ```

### 后续优化
1. **配置审查**：在 CI/CD 流程中加入对 Pod `nodeSelector` 和 `affinity` 规则的校验，确保引用的标签在目标集群中确实存在。
2. **自动化检查**：可考虑使用 `kubectl-validate` 或类似工具检查资源配置与集群节点标签的兼容性。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 已被调度 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS 从 `Pending` 变为 `Running` |
| 2. 检查 Pod 所在节点 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o wide` | `NODE` 列显示一个具体的节点名 (如 `node1`) |
| 3. 确认无调度事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | Events 中不应再有 `FailedScheduling` 警告 |

---
## ⚠️ 注意事项
- 如果 Pod 由 Deployment 或 StatefulSet 等控制器管理，**请直接在控制器上修改**，而不是直接操作 Pod。直接操作 Pod 不会持久化变更，可能会被控制器覆盖。
- 在修改 `nodeSelector` 之前，请确认您是否真正需要将 Pod 调度到特定节点，避免引入不必要的约束。

---

## 📊 性能统计

├─ 总耗时: 1.7m
├─ 问题定位: 28.1s (28%) ✅
├─ 证据链采集: 25.6s (25%) ✅
├─ 根因分析: 24.1s (24%) ✅
├─ 汇总总结: 24.1s (24%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 13 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 13 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
