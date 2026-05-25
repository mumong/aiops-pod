======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 83a3b99c3a8c40db]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先全局扫描所有 Pod 的状态，看看当前集群中哪些 Pod 异常。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 扫描结果很清楚，当前集群中有 1 个异常 Pod。让我进一步查看它的详细信息。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          10m   <none>   <none>   
   💭 [问题定位] 这个 Pod 处于 Pending 状态且没有绑定节点，标签里已经标注了 `pod_abnormal_type=PendingUnschedulable`。让我查看它的 Events 确认调度失败原因。
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
10m                   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3
   💭 [问题定位] 由于匹配 PendingUnschedulable 类型，让我获取对应的 runbook 作为参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在信息已经很明确了。让我快速确认一下节点情况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 所有 3 个节点都处于 Ready 状态。让我再检查一下这个 Pod 的调度约束。
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
   💭 [问题定位] 现在所有信息都齐了，我来输出诊断结果。

---

## 🏥 集群 Pod 异常诊断结果

### 全局概览
| 指标 | 数值 |
|------|------|
| 集群总 Pod 数 | **65** |
| 正常 Running Pods | **59** |
| 异常 Pods | **1** |
| 节点总数 | **3**（全部 Ready） |

---

### 🚨 异常 Pod 详情

| 字段 | 值 |
|------|-----|
| **Pod 名称** | `rc-pending-nodeselector` |
| **命名空间** | `aiops-e2e` |
| **状态** | `Pending` |
| **绑定的 Node** | 无（`<none>`） |
| **异常类型（pod_abnormal_type）** | `PendingUnschedulable` |
| **状态关键字** | `Pending` |

---

### 🔍 根因分析

**Pod 调度失败原因：nodeSelector 不匹配**

- **Events 关键信息：**
  ```
  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.
  ```
- **Pod 配置中设置了 nodeSelector：**
  ```yaml
  nodeSelector:
    aiops.e2e/nonexistent-node-label: "true"
  ```
- **当前集群 3 个节点（master, node1, node2）均没有 `aiops.e2e/nonexistent-node-label` 这个标签**，因此没有节点可以调度该 Pod。

---

### 📊 诊断摘要

| 维度 | 内容 |
|------|------|
| **layer** | `L1` — 调度相关问题 |
| **layer_name** | `PendingUnschedulable` |
| **derived_layer** | `L1` |
| **layers** | `["L1"]` |
| **confidence** | `高` |
| **status_category** | `scheduling` |
| **pod_status_keyword** | `Pending` |
| **pod_abnormal_type** | `PendingUnschedulable` |
| **key_entities** | Pod: `aiops-e2e/rc-pending-nodeselector`, Nodes: `master, node1, node2` |
| **possible_scenarios** | Pod 配置了 `nodeSelector: {aiops.e2e/nonexistent-node-label: "true"}`，但集群中没有任何节点拥有该标签，导致调度器无法放置该 Pod |

### ✅ 后续建议
这个 Pod 是一个 E2E 测试用例（标签 `rootcause-e2e=true`），人为设置了不存在的 nodeSelector 来模拟调度失败场景。如果需要让它正常运行，可以：
1. 给某个节点打上 `aiops.e2e/nonexistent-node-label=true` 标签
2. 或者修改/删除该 Pod 的 nodeSelector 约束
   ✅ [问题定位] 完成 (29.1s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector 不匹配', 'probability': '高', 'reason': "Pod 配置 nodeSelector: {aiops.e2e/nonexistent-node-label: true}，集群3个节点均无该标签，Events 明确显示 3 node(s) didn't match Pod's node affinity/selector"}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}]
   reasoning=集群中存在异常 Pod: aiops-e2e/rc-pending-nodeselector，状态为 Pending，没有分配到节点。Events 显示 FailedScheduling，原因为 3 nodes 均不匹配 nodeSelector/affinity。Pod 配置了 nodeSelector: {aiops.e2e/nonexistent-node-label: "true"}，但集群3个节点均无此标签。节点全部 Ready，排除了节点层面问题。根因是调度约束不匹配，属于典型的调度问题，因此定层为 L1。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "集群中存在异常 Pod: aiops-e2e/rc-pending-nodeselector，状态为 Pending，没有分配到节点。Events 显示 FailedScheduling，原因为 3 nodes 均不匹配 nodeSelector/affinity。Pod 配置了 nodeSelector: {aiops.e2e/nonexistent-node-label: \"true\"}，但集群3个节点均无此标签。节点全部 Ready，排除了节点层面问题。根因是调度约束不匹配，属于典型的调度问题，因此定层为 L1。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}], "possible_scenarios": [{"scenario": "nodeSelector 不匹配", "probability": "高", "reason": "Pod 配置 nodeSelector: {aiops.e2e/nonexistent-node-label: true}，集群3个节点均无该标签，Events 明确显示 3 node(s) didn't match Pod's node affinity/selector"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              10m     <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/83a3b99c3a8c40db/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/83a3b99c3a8c40db/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/83a3b99c3a8c40db/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我将直接执行既有 evidence_plan 中的工具调用。先并行执行独立的几个任务：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  11m                 default-scheduler  0/3 nodes are available:
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:18:44Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [证据链采集] 节点列表已获取，所有节点均正常 Ready。现在执行第 e3 项 —— 查看所有节点的 labels，确认是否存在 `aiops.e2e/nonexistent-node-label` 标签：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAME     STATUS   ROLES           AGE    VERSION   LABELS\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpg
   💭 [证据链采集] 所有证据已采集完毕。下面是证据总结：

---

## 证据采集结论

### 已采集证据

| # | 计划项 | 工具 | 证据摘要 |
|---|--------|------|----------|
| ✅ **e1** | pod-describe (critical) | `kubectl_describe` | Pod `rc-pending-nodeselector` 状态 Pending，未绑定 node。Events 明确显示：**`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`**。配置了 `Node-Selectors: aiops.e2e/nonexistent-node-label=true` |
| ✅ **e2** | pod-yaml (important) | `kubectl_get_yaml` | 确认 `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}`；`phase: Pending`；`conditions[].reason=Unschedulable`；节点无 imagePullSecrets 问题 |
| ✅ **e3** | node-labels (important) | `run_bash_command` | 3 个节点（master/node1/node2）均**不包含** `aiops.e2e/nonexistent-node-label` 标签 — 这是根因的直接证据 |
| ✅ **e4** | node-status (important) | `kubectl_get_by_kind_in_cluster` | 3 个节点全部 **Ready**（status_counts: Ready=3），排除了节点 NotReady/Unschedulable 导致的调度失败 |

### 未采集 / 冲突证据
- **无冲突证据** — Pod 仍存在于 `aiops-e2e` namespace，状态与上游一致。
- **无需额外证据** — 非主异常组：除 Pending 异常外，当前集群无其他异常状态（Running=59，无 Terminating/CrashLoop/ImagePull 等）。

### 根因判定
**Pod `rc-pending-nodeselector` 调度失败**，根因为：
- **nodeSelector 不匹配**：Pod 要求 `aiops.e2e/nonexistent-node-label=true`，但集群 3 个节点的标签中均无此标签
- 对应 runbook 判定规则：**`FailedScheduling + node(s) didn't match node selector/affinity` → 调度约束不匹配（高置信度）**
- 所有节点均 Ready，资源充足，无 taint 问题，排除其他因素
   ✅ [证据链采集] 完成 (21.7s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1-pod-describe","description":"describe Pod rc-pending-nodeselector 获取完整调度状态和Events原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-pending-nodeselector","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e","resource":"pod"},"purpose":"验证当前调度状态、FailedScheduling 事件、nodeSelector/affinity 配置、Conditions 等","evidence_type":"pod_status_and_events","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2-pod-yaml","description":"获取Pod完整YAML，检查nodeSelector和affinity配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod -n aiops-e2e rc-pending-nodeselector -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e","resource":"pod","format":"yaml"},"purpose":"验证nodeSelector/affinity字段具体值","evidence_type":"pod_spec_yaml","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3-node-labels","description":"获取所有节点的labels，验证是否包含Pod所需的标签","level":"important","tool":"run_bash_command","command":"kubectl get nodes --show-labels | head -50","tool_args":{"command":"kubectl get nodes --show-labels | head -50"},"purpose":"验证集群中是否存在包含 aiops.e2e/nonexistent-node-label=true 标签的节点","evidence_type":"node_labels","target_scope":"Node/all","acceptable_tools":["run_bash_command","kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true},{"id":"e4-node-status","description":"检查所有节点的Ready状态","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes","tool_args":{"kind":"nodes","format":"wide"},"purpose":"排除节点NotReady/Unschedulable导致的调度失败","evidence_type":"node_status","target_scope":"Node/all","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  11m                 default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  61s (x2 over 6m1s)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  11m                 default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  61s (x2 over 6m1s)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/83a3b99c3a8c40db/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/83a3b99c3a8c40db/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/83a3b99c3a8c40db/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/83a3b99c3a8c40db/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/83a3b99c3a8c40db/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/83a3b99c3a8c40db/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   238d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          238d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\nnode2    Ready    <none>          238d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/83a3b99c3a8c40db/tools/003-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/83a3b99c3a8c40db/tools/003-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/83a3b99c3a8c40db/tools/003-evidence-kubectl_get_by_kind_in_cluster.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAME     STATUS   ROLES           AGE    VERSION   LABELS\\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\\nnode1    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\nnode2    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/83a3b99c3a8c40db/tools/004-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/83a3b99c3a8c40db/tools/004-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/83a3b99c3a8c40db/tools/004-evidence-run_bash_command.summary.txt"}],"llm_analysis":"所有证据已采集完毕。下面是证据总结：\n\n---\n\n## 证据采集结论\n\n### 已采集证据\n\n| # | 计划项 | 工具 | 证据摘要 |\n|---|--------|------|----------|\n| ✅ **e1** | pod-describe (critical) | `kubectl_describe` | Pod `rc-pending-nodeselector` 状态 Pending，未绑定 node。Events 明确显示：**`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`**。配置了 `Node-Selectors: aiops.e2e/nonexistent-node-label=true` |\n| ✅ **e2** | pod-yaml (important) | `kubectl_get_yaml` | 确认 `nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}`；`phase: Pending`；`conditions[].reason=Unschedulable`；节点无 imagePullSecrets 问题 |\n| ✅ **e3** | node-labels (important) | `run_bash_command` | 3 个节点（master/node1/node2）均**不包含** `aiops.e2e/nonexistent-node-label` 标签 — 这是根因的直接证据 |\n| ✅ **e4** | node-status (important) | `kubectl_get_by_kind_in_cluster` | 3 个节点全部 **Ready**（status_counts: Ready=3），排除了节点 NotReady/Unschedulable 导致的调度失败 |\n\n### 未采集 / 冲突证据\n- **无冲突证据** — Pod 仍存在于 `aiops-e2e` namespace，状态与上游一致。\n- **无需额外证据** — 非主异常组：除 Pending 异常外，当前集群无其他异常状态（Running=59，无 Terminating/CrashLoop/ImagePull 等）。\n\n### 根因判定\n**Pod `rc-pending-nodeselector` 调度失败**，根因为：\n- **nodeSelector 不匹配**：Pod 要求 `aiops.e2e/nonexistent-node-label=true`，但集群 3 个节点的标签中均无此标签\n- 对应 runbook 判定规则：**`FailedScheduling + node(s) didn't match node selector/affinity` → 调度约束不匹配（高置信度）**\n- 所有节点均 Ready，资源充足，无 taint 问题，排除其他因素","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 9 个，匹配计划 4 个，未规划证据 5 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":9,"matched_tool_count":4,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1-pod-describe","description":"describe Pod rc-pending-nodeselector 获取完整调度状态和Events原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-pending-nodeselector","purpose":"验证当前调度状态、FailedScheduling 事件、nodeSelector/affinity 配置、Conditions 等","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-pod-yaml","description":"获取Pod完整YAML，检查nodeSelector和affinity配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod -n aiops-e2e rc-pending-nodeselector -o yaml","purpose":"验证nodeSelector/affinity字段具体值","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3-node-labels","description":"获取所有节点的labels，验证是否包含Pod所需的标签","level":"important","tool":"run_bash_command","command":"kubectl get nodes --show-labels | head -50","purpose":"验证集群中是否存在包含 aiops.e2e/nonexistent-node-label=true 标签的节点","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4-node-status","description":"检查所有节点的Ready状态","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes","purpose":"排除节点NotReady/Unschedulable导致的调度失败","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1-pod-describe | critical | ✅ | kubectl_describe | describe Pod rc-pending-nodeselector 获取完整调度状态... | `kubectl describe pod -n aiops-e2e rc-pending-nodeselector` |
   | e2-pod-yaml | important | ✅ | kubectl_get_yaml | 获取Pod完整YAML，检查nodeSelector和affinity配置 | `kubectl get pod -n aiops-e2e rc-pending-nodeselector -o yaml` |
   | e3-node-labels | important | ✅ | run_bash_command | 获取所有节点的labels，验证是否包含Pod所需的标签 | `kubectl get nodes --show-labels | head -50` |
   | e4-node-status | important | ✅ | kubectl_get_by_kind_in_cl... | 检查所有节点的Ready状态 | `kubectl get nodes` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (22.5s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector（namespace: aiops-e2e）处于 Pending 状态已持续约 11 分钟，根因是 nodeSelector 不匹配。Pod 配置要求节点包含标签 aiops.e2e/nonexistent-node-label=true（e2 证据），但集群全部 3 个节点（master/node1/node2）均无此标签（e3 证据）。调度器 Events 确认 "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"（e1 证据）。所有节点均 Ready（e4 证据），排除了节点不可用问题。集群中其他 59 个 Pod 均正常运行（e5 证据），故障被精确隔离于该 Pod 的调度约束配置。
   confidence=98%
   causal_chain={"root_cause": "Pod rc-pending-nodeselector 配置了 nodeSelector: {aiops.e2e/nonexistent-node-label: true}，但集群 3 个节点均无此标签，导致调度器无法找到匹配节点", "propagation": "Pod 创建后调度器遍历所有 3 个节点 → 逐一检查 nodeSelector 条件 → 所有节点均不满足 → 调度失败 → 调度器重试(61s 间隔) → 持续失败 → Pod 保持 Pending 状态，Events 记录 FailedScheduling", "direct_cause": "nodeSelector 键值对 aiops.e2e/nonexistent-node-label=true 与所有节点的标签集合完全不匹配", "manifestation": "Pod aiops-e2e/rc-pending-nodeselector 持续 Pending 超过 11 分钟，Events 显示 FailedScheduling，条件 PodScheduled=False reason=Unschedulable"}
   rca_analysis={"phenomenon": "Pod aiops-e2e/rc-pending-nodeselector 处于 Pending 状态，持续约 11 分钟，未分配到任何节点。Events 显示 FailedScheduling，调度器报告 3 个节点均不匹配 nodeSelector。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod rc-pending-nodeselector 状态 Pending, node=<none>, Events: FailedScheduling '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml", "content": "Pod 配置 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}, conditions: PodScheduled=False, reason=Unschedulable", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_by_kind_in_cluster / run_bash_command", "content": "集群 3 个节点(master/node1/node2)均 Ready，均不包含标签 aiops.e2e/nonexistent-node-label", "reliability": "高"}, {"id": "e4", "source": "kubectl_get_by_kind_in_cluster (nodes)", "content": "3 个节点全部 Ready (status_counts={Ready: 3})，排除节点不可用导致调度失败", "reliability": "高"}, {"id": "e5", "source": "current_abnormal_summary", "content": "集群共 65 个 Pod，59 Running、1 Pending，无其他异常状态", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedScheduling 11m default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "interpretation": "调度器明确报告所有 3 个节点均因 node affinity/selector 条件不满足而无法调度此 Pod，这是当前故障的直接现象"}, {"evidence_id": "e2", "raw_data": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}, conditions[].reason=Unschedulable", "interpretation": "Pod 的 nodeSelector 要求节点包含标签 aiops.e2e/nonexistent-node-label=true，但该标签名称本身暗示其不存在于任何节点上"}, {"evidence_id": "e3", "raw_data": "master labels: beta.kubernetes.io/arch=amd64,...,kubernetes.io/hostname=master,... (无 aiops.e2e/nonexistent-node-label)", "interpretation": "3 个节点(master/node1/node2)的标签列表中均不包含 aiops.e2e/nonexistent-node-label 标签，导致 Pod 无法调度到任何节点"}, {"evidence_id": "e4", "raw_data": "status_counts={'Ready': 3}, master=Ready, node1=Ready, node2=Ready", "interpretation": "所有节点健康可用，排除了节点 NotReady、磁盘压力、内存压力等节点级别问题"}, {"evidence_id": "e5", "raw_data": "abnormal=1, Running=59, Pending=1, 无其他异常状态", "interpretation": "集群整体健康，仅此一个 Pod 异常，问题被隔离在 nodeSelector 配置层面"}], "causal_chain": {"root_cause": "Pod rc-pending-nodeselector 配置了 nodeSelector: {aiops.e2e/nonexistent-node-label: true}，但集群 3 个节点均无此标签，导致调度器无法找到匹配节点", "propagation": "Pod 创建后调度器遍历所有 3 个节点 → 逐一检查 nodeSelector 条件 → 所有节点均不满足 → 调度失败 → 调度器重试(61s 间隔) → 持续失败 → Pod 保持 Pending 状态，Events 记录 FailedScheduling", "direct_cause": "nodeSelector 键值对 aiops.e2e/nonexistent-node-label=true 与所有节点的标签集合完全不匹配", "manifestation": "Pod aiops-e2e/rc-pending-nodeselector 持续 Pending 超过 11 分钟，Events 显示 FailedScheduling，条件 PodScheduled=False reason=Unschedulable"}, "root_cause": "Pod rc-pending-nodeselector（namespace: aiops-e2e）处于 Pending 状态已持续约 11 分钟，根因是 nodeSelector 不匹配。Pod 配置要求节点包含标签 aiops.e2e/nonexistent-node-label=true（e2 证据），但集群全部 3 个节点（master/node1/node2）均无此标签（e3 证据）。调度器 Events 确认 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"（e1 证据）。所有节点均 Ready（e4 证据），排除了节点不可用问题。集群中其他 59 个 Pod 均正常运行（e5 证据），故障被精确隔离于该 Pod 的调度约束配置。", "root_cause_summary": "Pod rc-pending-nodeselector（namespace: aiops-e2e）处于 Pending 状态已持续约 11 分钟，根因是 nodeSelector 不匹配。Pod 配置要求节点包含标签 aiops.e2e/nonexistent-node-label=true（e2 证据），但集群全部 3 个节点（master/node1/node2）均无此标签（e3 证据）。调度器 Events 确认 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"（e1 证据）。所有节点均 Ready（e4 证据），排除了节点不可用问题。集群中其他 59 个 Pod 均正常运行（e5 证据），故障被精确隔离于该 Pod 的调度约束配置。", "confidence": 0.98, "confidence_reason": "多个直接证据交叉验证：kubectl_describe（调度事件原文）、kubectl_get_yaml（nodeSelector 配置确认）、节点标签查询（3 节点全无此标签）、节点状态（全部 Ready）。因果链完整且无矛盾，置信度高达 0.98", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "资源不足（CPU/内存不足）", "probability": "low", "reason": "Events 未报告 Insufficient cpu/memory，而是明确报告 nodeSelector 不匹配；且 3 节点均 Ready"}, {"cause": "节点 taint 未容忍", "probability": "low", "reason": "Events 未报告 taint 相关错误；Pod 已有 tolerations 容忍 not-ready NoExecute；调度器错误信息明确指向 node affinity/selector"}, {"cause": "PVC 未绑定", "probability": "low", "reason": "Pod 无 PVC 依赖，Events 无相关错误"}, {"cause": "节点不可用", "probability": "low", "reason": "3 节点全部 Ready，排除"}], "limitations": "仅捕获了 1 个异常 Pod，集群其他 Pod 均正常运行。节点标签信息通过 kubectl_get_by_kind_in_cluster 的概要摘要获取，仅展示了部分标签示例，但 3 个节点的标签列表中均未出现 aiops.e2e/nonexistent-node-label，结合调度事件确认已足够证明根因。未检查 Pod 中是否定义了 nodeAffinity（除 nodeSelector 外），但 events 已明确报 node affinity/selector 不匹配，不影响结论。", "llm_raw_analysis": "证据清点：共 5 组证据（e1-e5），全部为直接证据。e1(describe)和 e2(yaml)确认 Pod 状态和 nodeSelector 配置，e3(节点标签)验证根因，e4(节点状态)排除干扰项，e5(集群概览)确认问题孤立。因果链清晰：nodeSelector 配置 → 无节点匹配 → FailedScheduling → Pending。置信度高，无矛盾证据。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector（namespace: aiops-e2e）处于 Pending 状态已持续约 11 分钟，根因是 nodeSelector 不匹配。Pod 配置要求节点包含标签 aiops.e2e/nonexistent-node-label=true（e2 ...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod rc-pending-nodeselector 配置了 nodeSelector: {aiops.e2e/nonexistent-node-label: true}，但集群 3 个节点均无此标签，导致调度器无法找到匹配节点
     传导机制: Pod 创建后调度器遍历所有 3 个节点 → 逐一检查 nodeSelector 条件 → 所有节点均不满足 → 调度失败 → 调度器重试(61s 间隔) → 持续失败 → Pod 保持 Pending 状态，Events 记录 FailedScheduling
     最终表现: Pod aiops-e2e/rc-pending-nodeselector 持续 Pending 超过 11 分钟，Events 显示 FailedScheduling，条件 PodScheduled=False reason=Unschedulable


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (24.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5510 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 37.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为一名资深 K8s 诊断报告专家，我将为您生成一份详尽、完整的诊断报告。

首先，直接回答您的核心问题：

---

## 集群状态速览

您的集群整体运行正常，但存在一个特定问题。

- **集群整体状态**：**基本健康**。集群 3 个节点全部 `Ready`，59 个 Pod 正常运行。
- **已发现的问题**：**1 个 Pod 处于 `Pending` 状态**，无法被调度。
- **根本原因**：该 Pod 配置了一个**不存在的 `nodeSelector` 标签**，导致调度器找不到可以运行它的节点。
- **影响范围**：**仅影响该特定 Pod (`aiops-e2e/rc-pending-nodeselector`)**，不影响其他工作负载。

---

以下是详细的诊断报告。

---
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending |
| **兼容归因层** | L1 - 调度问题 |
| **问题分类** | PendingUnschedulable |
| **置信度** | 高 (98%) |
| **证据完整度** | 4/4 (100%) |
---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-pending-nodeselector` |
| Namespace | `aiops-e2e` |
| Node | `master`, `node1`, `node2` |
| 错误信息 | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 & 事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | `status: Pending`; `Events: Warning FailedScheduling ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` | Pod 因节点不满足调度约束而无法调度。 |
| 2 | Pod 配置 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` | `Node-Selectors: aiops.e2e/nonexistent-node-label=true` | Pod 配置了 `nodeSelector`，要求节点包含标签 `aiops.e2e/nonexistent-node-label=true`。 |
| 3 | 节点标签 | `kubectl get nodes --show-labels` (通过 `run_bash_command` 执行) | 节点 `master`: `beta.kubernetes.io/arch=amd64,...,node-role.kubernetes.io/control-plane=,...`<br>节点 `node1`: `beta.kubernetes.io/arch=amd64,...,metax-tech.com/gpu.installed=false`<br>节点 `node2`: `beta.kubernetes.io/arch=amd64,...,metax-tech.com/gpu.installed=false` | 三个节点的标签列表中均**不包含** `aiops.e2e/nonexistent-node-label`。 |
| 4 | 节点状态 | `kubectl get nodes` | `master` **Ready** (control-plane)<br>`node1` **Ready**<br>`node2` **Ready** | 所有节点均处于 `Ready` 状态，排除了节点不可用导致调度失败的可能性。 |
### 证据关联分析
- **证据 #1 + #2 + #3 印证**：Pod 要求节点有 `aiops.e2e/nonexistent-node-label=true` 标签，但所有 3 个节点都没有，调度器因此拒绝调度。这个因果关系在 `FailedScheduling` 事件中得到了直接确认。
- **证据链**：Pod 配置 (nodeSelector) → 调度器检查所有节点标签 → 无匹配节点 → 调度失败 → Pod 卡在 Pending 状态 → 事件记录。
### 缺失证据
无。所有关键证据均已采集，证据链路完整。

---
## 🎯 根因分析
### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                         │
│ Pod 'rc-pending-nodeselector' 配置了 nodeSelector:                                   │
│ {aiops.e2e/nonexistent-node-label: true}，但集群中所有 3 个节点均无此标签。          │
└──────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                         │
│ Scheduler 遍历节点 → 检查 nodeSelector → 不匹配 → 标记为不可用 → 继续下一个节点       │
└──────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                         │
│ 调度器无法找到任何满足 Pod 调度约束的节点。                                        │
└──────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                     │
│ Pod 状态为 Pending，并持续产生 'FailedScheduling' 事件。                          │
└──────────────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #1 (`FailedScheduling` 事件)、证据 #2 (`Node-Selectors` 配置) 和证据 #3 (节点标签列表)，问题的根本原因是 **Pod `rc-pending-nodeselector` 的 `nodeSelector` 配置了一个集群中不存在的标签 (`aiops.e2e/nonexistent-node-label`)**。这使得调度器无法在 3 个 Ready 节点中找到运行该 Pod 的位置。
**置信度**：高 (98%)
- ✅ `FailedScheduling` 事件已明确指向 node affinity/selector 不匹配。
- ✅ Pod YAML 配置完全符合事件描述。
- ✅ 节点标签列表已确认不存在所需标签。
- ✅ 所有节点状态均为 `Ready`，排除了节点故障。

---
## 🛠️ 修复建议
### 立即执行 (按优先级排序)
**1. [推荐] 移除或修改 `nodeSelector`**
您可以根据实际需求选择以下一种操作：
- **移除 `nodeSelector` 约束** (如果业务不需要节点选择):
  ```bash
  kubectl patch pod rc-pending-nodeselector -n aiops-e2e -p '{"spec": {"nodeSelector": null}}' --type=merge
  ```
  *注意：如果是通过 Deployment、StatefulSet 等工作负载创建的 Pod，请修改工作负载的 YAML 而不是直接 patch Pod。*

- **修改为正确的标签** (如果需要将 Pod 调度到特定节点):
  首先，找到或创建一个合适的节点标签。
  ```bash
  # 例如，将 Pod 调度到 node1
  kubectl label node node1 aiops.e2e/nonexistent-node-label=true --overwrite
  ```
  执行此命令后，调度器会自动将 Pod 调度到 `node1`。

### 后续优化
1. **规范标签命名**：在团队内建立明确的节点标签命名和使用规范，避免使用无意义的标签值（如 `nonexistent-node-label`）。
2. **代码审查**：在部署 YAML 文件前，通过 CI/CD 流程或代码审查检查 `nodeSelector` 和 `nodeAffinity` 等调度配置是否正确。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 调度状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | `STATUS: Running` (或 `Pending` 解决后变为 Running) |
| 2. 检查节点标签 (如果执行了标签修复) | `kubectl get node node1 --show-labels` | 输出中包含 `aiops.e2e/nonexistent-node-label=true` |
| 3. 确认 Pod 所在节点 (如果已调度) | `kubectl get pod rc-pending-nodeselector -n aiops-e2o -o wide` | `NODE` 列显示具体的节点名称 |

---
## ⚠️ 注意事项
- 以上修复操作在您提供的信息范围内有效。如果 Pod 是通过 Deployment/StatefulSet 等更高层级的控制器管理的，请修改对应控制器的 YAML 配置，否则手动 patch Pod 可能会被控制器恢复。
- 虽然集群节点均未配置该标签，但 Pod 标签中包含 `rootcause-e2e=true`，这很可能是一个用于测试的场景，请确认该 Pod 在生产环境中是否仍为必要配置。

---

## 📊 性能统计

├─ 总耗时: 1.6m
├─ 问题定位: 29.1s (30%) ✅
├─ 证据链采集: 21.7s (22%) ✅
├─ 根因分析: 22.5s (23%) ✅
├─ 汇总总结: 24.0s (25%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 10 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 10 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
