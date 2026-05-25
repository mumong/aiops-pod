======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 656fc5842e1f444b]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先全局扫描所有 Pod 的状态，看看有哪些异常。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 发现了一个异常 Pod，让我进一步查看详细信息。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          17m   <none>   <none>   
   💭 [问题定位] 这个 Pod 状态是 Pending 且没有调度到节点上，符合 `PendingUnschedulable` 类型。让我获取调度相关的事件和描述信息。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
17m                   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  17m                  default-scheduler  0/3 nodes are available
   💭 [问题定位] 信息已经很清晰了，让我获取对应的 runbook 来参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在我已经掌握了所有关键信息，可以完成定位分析了。

---

## 诊断结果

### 当前异常 Pod 总览

| Pod | 命名空间 | 状态 | 异常类型 |
|-----|---------|------|---------|
| `rc-pending-nodeselector` | `aiops-e2e` | Pending | PendingUnschedulable |

### 异常分析

**Pod 状态**：`Pending`，未绑定任何 Node（NODE 列为 `<none>`）

**核心事件**：`FailedScheduling`
> `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.`

**根因定位**：
- Pod 设置了 **nodeSelector**：`aiops.e2e/nonexistent-node-label=true`
- 集群中 **3 个节点均不匹配该标签选择器**，导致无法调度
- 没有资源不足、taint 或端口冲突问题，纯属 nodeSelector 约束不匹配

### 输出结构化结果

```json
{
  "layer": "L1",
  "derived_layer": "L1",
  "layers": ["L1"],
  "layer_name": "PendingUnschedulable",
  "confidence": "high",
  "reasoning": "Pod rc-pending-nodeselector 处于 Pending 状态，调度器 FailedScheduling 明确指出 3 个节点均不匹配 Pod 的 nodeSelector（aiops.e2e/nonexistent-node-label=true），属于调度约束不匹配，归入 L1 层",
  "abnormal_pods": [
    {
      "namespace": "aiops-e2e",
      "name": "rc-pending-nodeselector",
      "status": "Pending",
      "node": "<none>"
    }
  ],
  "abnormal_groups": ["PendingUnschedulable"],
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "PendingUnschedulable",
  "status_category": "L1",
  "key_entities": [
    {
      "kind": "Pod",
      "namespace": "aiops-e2e",
      "name": "rc-pending-nodeselector"
    }
  ],
  "possible_scenarios": [
    "Pod 设置了 nodeSelector (aiops.e2e/nonexistent-node-label=true)，但集群中没有任何节点带有该标签，导致调度器无法放置 Pod"
  ]
}
```

### 后续审查方向
- 检查 Pod 的 nodeSelector/affinity 配置是否合理
- 确认是否需要在目标节点上添加对应标签，或修改 Pod 的调度约束
- 该 Pod 是 `BestEffort` QoS（无资源 requests），资源不是问题
   ✅ [问题定位] 完成 (23.0s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'Pod nodeSelector 不匹配', 'probability': '高', 'reason': "FailedScheduling 明确提示 3 个节点均不匹配 Pod's node affinity/selector，nodeSelector 设置为 aiops.e2e/nonexistent-node-label=true，集群中不存在该标签"}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}]
   reasoning=Pod rc-pending-nodeselector (aiops-e2e) 处于 Pending 状态，调度器 FailedScheduling 明确指出 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. Pod 设置了 nodeSelector (aiops.e2e/nonexistent-node-label=true)，集群中 3 个节点均不匹配该标签选择器，属于调度约束不匹配，归入 L1 层 (scheduling)。集群中其他 59 个 Pod 均 Running，无其他异常。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "Pod rc-pending-nodeselector (aiops-e2e) 处于 Pending 状态，调度器 FailedScheduling 明确指出 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. Pod 设置了 nodeSelector (aiops.e2e/nonexistent-node-label=true)，集群中 3 个节点均不匹配该标签选择器，属于调度约束不匹配，归入 L1 层 (scheduling)。集群中其他 59 个 Pod 均 Running，无其他异常。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod nodeSelector 不匹配", "probability": "高", "reason": "FailedScheduling 明确提示 3 个节点均不匹配 Pod's node affinity/selector，nodeSelector 设置为 aiops.e2e/nonexistent-node-label=true，集群中不存在该标签"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              16m     <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/656fc5842e1f444b/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/656fc5842e1f444b/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/656fc5842e1f444b/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来执行既有 evidence_plan 中的工具调用，采集真实环境证据。

先执行多个可以并行调用的工具：
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAME     STATUS   ROLES           AGE    VERSION   LABELS\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpg
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:18:44Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          17m   <none>   <none>   
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  17m                 default-scheduler  0/3 nodes are available:
   💭 [证据链采集] 所有工具调用成功返回。下面是证据采集结论：

---

## 证据采集结论

### ✅ 已采集证据（4项，覆盖 complete 验证）

| # | 证据项 | 等级 | 结果 |
|---|--------|------|------|
| **e1** | `kubectl_get_yaml` — Pod YAML 配置 | **critical** ✅ | ✅ **nodeSelector: `{"aiops.e2e/nonexistent-node-label": "true"}`**；PodScheduled condition=False, reason=Unschedulable；镜像 busybox:1.36 (imagePullPolicy=Never)；无 PVC 依赖 |
| **e2** | `kubectl_describe` — 完整 Events 和 Status | **critical** ✅ | ✅ FailedScheduling 事件 3 次触发：**"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"**；Node-Selectors 明确显示 `aiops.e2e/nonexistent-node-label=true`；QoS Class: BestEffort |
| **e3** | `kubectl get nodes --show-labels` — 节点标签 | **important** ✅ | ✅ 3 个节点（master/node1/node2）**均不存在标签 `aiops.e2e/nonexistent-node-label`**，证实无节点匹配 nodeSelector |
| **e4** | `kubectl_get_by_name` — Pod 当前状态确认 | **important** ✅ | ✅ Pod 仍存在于 aiops-e2e，STATUS=Pending，0/1，17m，无 Node 绑定 |

### 📋 根因分析
**Pod `rc-pending-nodeselector`（aiops-e2e 命名空间）处于 Pending 状态**，调度器明确报告：
> **0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector**

Pod 配置了 `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}`，而集群中 3 个节点（master、node1、node2）均**不包含此标签**。属于**调度约束不匹配**（L1 层 scheduling 问题），无需检查资源不足、PVC 或 taint 分支。

### ❌ 未采集/冲突证据
- 无冲突证据。所有工具均成功返回，Pod 及节点信息与上游描述完全一致。

### 💡 修复建议（仅供参考，不执行）
1. **删除或更正 nodeSelector**：将 Pod spec 中的 `aiops.e2e/nonexistent-node-label=true` 移除，或改为集群中真实存在的标签（如 `kubernetes.io/hostname=node1`）
2. **为节点添加标签**：`kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`（仅当需要按该标签调度时）
   ✅ [证据链采集] 完成 (21.6s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"Pod rc-pending-nodeselector YAML 验证 nodeSelector 配置和 spec 详情","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e","output":"yaml"},"purpose":"验证 Pod 的 nodeSelector/affinity 配置、containers 配置、image 等规格","evidence_type":"PodSpec","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e2","description":"Pod describe 详细事件和状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"获取 Pod 的完整 Events、Status、Conditions、调度失败原文","evidence_type":"PodEvents","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"查询节点标签，验证 nodeSelector 不匹配的根因","level":"important","tool":"run_bash_command","command":"kubectl get nodes --show-labels","tool_args":{"command":"kubectl get nodes --show-labels"},"purpose":"查看所有节点的标签，确认是否存在 aiops.e2e/nonexistent-node-label 标签，验证调度约束不匹配","evidence_type":"NodeLabels","target_scope":"Cluster/Node","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"验证异常 Pod 仍然存在（避免历史对象）","level":"important","tool":"kubectl_get_by_name","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"确认异常 Pod 当前仍存在于集群中，排除历史对象","evidence_type":"PodExistence","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAME     STATUS   ROLES           AGE    VERSION   LABELS\\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\\nnode1    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\nnode2    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/656fc5842e1f444b/tools/001-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/656fc5842e1f444b/tools/001-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/656fc5842e1f444b/tools/001-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/656fc5842e1f444b/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/656fc5842e1f444b/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/656fc5842e1f444b/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS\nrc-pending-nodeselector   0/1     Pending   0          17m   <none>   <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/656fc5842e1f444b/tools/003-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/656fc5842e1f444b/tools/003-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/656fc5842e1f444b/tools/003-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  17m                 default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  7m3s (x2 over 12m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  17m                 default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  7m3s (x2 over 12m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/656fc5842e1f444b/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/656fc5842e1f444b/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/656fc5842e1f444b/tools/004-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"所有工具调用成功返回。下面是证据采集结论：\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据（4项，覆盖 complete 验证）\n\n| # | 证据项 | 等级 | 结果 |\n|---|--------|------|------|\n| **e1** | `kubectl_get_yaml` — Pod YAML 配置 | **critical** ✅ | ✅ **nodeSelector: `{\"aiops.e2e/nonexistent-node-label\": \"true\"}`**；PodScheduled condition=False, reason=Unschedulable；镜像 busybox:1.36 (imagePullPolicy=Never)；无 PVC 依赖 |\n| **e2** | `kubectl_describe` — 完整 Events 和 Status | **critical** ✅ | ✅ FailedScheduling 事件 3 次触发：**\"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"**；Node-Selectors 明确显示 `aiops.e2e/nonexistent-node-label=true`；QoS Class: BestEffort |\n| **e3** | `kubectl get nodes --show-labels` — 节点标签 | **important** ✅ | ✅ 3 个节点（master/node1/node2）**均不存在标签 `aiops.e2e/nonexistent-node-label`**，证实无节点匹配 nodeSelector |\n| **e4** | `kubectl_get_by_name` — Pod 当前状态确认 | **important** ✅ | ✅ Pod 仍存在于 aiops-e2e，STATUS=Pending，0/1，17m，无 Node 绑定 |\n\n### 📋 根因分析\n**Pod `rc-pending-nodeselector`（aiops-e2e 命名空间）处于 Pending 状态**，调度器明确报告：\n> **0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector**\n\nPod 配置了 `nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}`，而集群中 3 个节点（master、node1、node2）均**不包含此标签**。属于**调度约束不匹配**（L1 层 scheduling 问题），无需检查资源不足、PVC 或 taint 分支。\n\n### ❌ 未采集/冲突证据\n- 无冲突证据。所有工具均成功返回，Pod 及节点信息与上游描述完全一致。\n\n### 💡 修复建议（仅供参考，不执行）\n1. **删除或更正 nodeSelector**：将 Pod spec 中的 `aiops.e2e/nonexistent-node-label=true` 移除，或改为集群中真实存在的标签（如 `kubernetes.io/hostname=node1`）\n2. **为节点添加标签**：`kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`（仅当需要按该标签调度时）","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 8 个，匹配计划 4 个，未规划证据 4 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":4,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"Pod rc-pending-nodeselector YAML 验证 nodeSelector 配置和 spec 详情","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"验证 Pod 的 nodeSelector/affinity 配置、containers 配置、image 等规格","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"Pod describe 详细事件和状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"获取 Pod 的完整 Events、Status、Conditions、调度失败原文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"查询节点标签，验证 nodeSelector 不匹配的根因","level":"important","tool":"run_bash_command","command":"kubectl get nodes --show-labels","purpose":"查看所有节点的标签，确认是否存在 aiops.e2e/nonexistent-node-label 标签，验证调度约束不匹配","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"验证异常 Pod 仍然存在（避免历史对象）","level":"important","tool":"kubectl_get_by_name","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e","purpose":"确认异常 Pod 当前仍存在于集群中，排除历史对象","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | Pod rc-pending-nodeselector YAML 验证 nodeSelec... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_describe | Pod describe 详细事件和状态 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e3 | important | ✅ | run_bash_command | 查询节点标签，验证 nodeSelector 不匹配的根因 | `kubectl get nodes --show-labels` |
   | e4 | important | ✅ | kubectl_get_by_name | 验证异常 Pod 仍然存在（避免历史对象） | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (31.7s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector（aiops-e2e 命名空间）处于 Pending 状态，根因是 nodeSelector 不匹配。kubectl_get_yaml 确认 nodeSelector 设置为 {"aiops.e2e/nonexistent-node-label": "true"}（e1）；kubectl_describe 显示调度器 3 次 FailedScheduling 事件，明确报告 "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"（e2）；节点标签查询（e3）确认 master、node1、node2 均不存在该标签。集群其他 59 个 Pod 均 Running，无其他异常。问题为 L1 层调度约束不匹配，无需检查资源不足、PVC 或 taint 分支。修复方式：移除 nodeSelector 或为节点添加匹配标签。
   confidence=98%
   causal_chain={"root_cause": "Pod rc-pending-nodeselector 的 spec 中配置了 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}，但集群中 3 个节点（master、node1、node2）均没有该标签，导致调度器无法找到匹配的节点。", "propagation": "调度器在每次调度周期中检查所有 3 个节点的标签与 Pod 的 nodeSelector 的匹配性，全部不匹配 → 调度失败 → 调度器重试（共触发 3 次 FailedScheduling 事件）→ 抢占机制尝试但无效（抢占不改变节点标签）→ Pod 持续处于 Pending 状态。", "direct_cause": "所有节点均不满足 Pod 的 nodeSelector 标签约束（aiops.e2e/nonexistent-node-label=true），调度器无法将 Pod 绑定到任何节点。", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续 Pending 超过 17 分钟，0/1 容器未启动，无 Node 分配，无 IP 地址，集群 events 中持续产生 FailedScheduling 告警。"}
   rca_analysis={"phenomenon": "Pod rc-pending-nodeselector (namespace: aiops-e2e) 处于 Pending 状态，已持续 17 分钟，0/1 容器就绪，未绑定到任何 Node。集群中其他 59 个 Pod 均正常运行，无其他异常。", "evidence_inventory": [{"id": "e1", "source": "kubectl_get_yaml", "content": "Pod YAML 显示 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}；phase=Pending；PodScheduled condition=False, reason=Unschedulable；无 PVC 依赖", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe", "content": "FailedScheduling 事件 3 次触发，消息: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector；Node-Selectors 明确显示 aiops.e2e/nonexistent-node-label=true", "reliability": "高"}, {"id": "e3", "source": "kubectl get nodes --show-labels", "content": "3 个节点（master/node1/node2）标签列表均不包含 aiops.e2e/nonexistent-node-label 标签", "reliability": "高"}, {"id": "e4", "source": "kubectl_get_by_name", "content": "Pod 当前仍存在，STATUS=Pending，0/1，AGE=17m，无 Node 绑定，无 IP 分配", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "集群 65 个 Pod 中 59 Running, 1 Pending（rc-pending-nodeselector）", "reliability": "高"}, {"id": "layer_3", "source": "kubectl_events", "content": "Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\nphase: Pending\nconditions: PodScheduled status=False reason=Unschedulable", "interpretation": "Pod 明确配置了 nodeSelector，要求节点包含 aiops.e2e/nonexistent-node-label=true 标签。PodScheduled condition 为 False 且 reason=Unschedulable，说明调度器无法找到满足该约束的节点。"}, {"evidence_id": "e2", "raw_data": "Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.\nNode-Selectors: aiops.e2e/nonexistent-node-label=true", "interpretation": "调度器 3 次重试均失败，全部 3 个节点均不满足 nodeSelector/affinity 条件。Node-Selectors 字段确认了 nodeSelector 的具体值为 aiops.e2e/nonexistent-node-label=true。"}, {"evidence_id": "e3", "raw_data": "master labels: ... (无 aiops.e2e/nonexistent-node-label)\nnode1 labels: ... (无 aiops.e2e/nonexistent-node-label)\nnode2 labels: ... (无 aiops.e2e/nonexistent-node-label)", "interpretation": "集群 3 个节点（master、node1、node2）的标签集合中均不存在 aiops.e2e/nonexistent-node-label 标签，证实没有任何节点可以匹配 Pod 的 nodeSelector 约束。"}, {"evidence_id": "e4", "raw_data": "rc-pending-nodeselector 0/1 Pending 0 17m <none> <none>", "interpretation": "Pod 当前仍然存在且状态为 Pending，未分配到 Node，未获得 IP，排除历史对象噪音的可能性。"}, {"evidence_id": "layer_1", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}", "interpretation": "集群中 65 个 Pod 仅有此 1 个异常，其余 59 个 Running，说明集群整体健康，问题局限于该 Pod 的调度约束配置。"}, {"evidence_id": "layer_3", "raw_data": "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.", "interpretation": "调度器明确表示抢占也无法帮助，因为根本原因是 nodeSelector/affinity 不匹配而非资源不足，抢占不影响节点标签匹配。"}], "causal_chain": {"root_cause": "Pod rc-pending-nodeselector 的 spec 中配置了 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}，但集群中 3 个节点（master、node1、node2）均没有该标签，导致调度器无法找到匹配的节点。", "propagation": "调度器在每次调度周期中检查所有 3 个节点的标签与 Pod 的 nodeSelector 的匹配性，全部不匹配 → 调度失败 → 调度器重试（共触发 3 次 FailedScheduling 事件）→ 抢占机制尝试但无效（抢占不改变节点标签）→ Pod 持续处于 Pending 状态。", "direct_cause": "所有节点均不满足 Pod 的 nodeSelector 标签约束（aiops.e2e/nonexistent-node-label=true），调度器无法将 Pod 绑定到任何节点。", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续 Pending 超过 17 分钟，0/1 容器未启动，无 Node 分配，无 IP 地址，集群 events 中持续产生 FailedScheduling 告警。"}, "root_cause": "Pod rc-pending-nodeselector（aiops-e2e 命名空间）处于 Pending 状态，根因是 nodeSelector 不匹配。kubectl_get_yaml 确认 nodeSelector 设置为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}（e1）；kubectl_describe 显示调度器 3 次 FailedScheduling 事件，明确报告 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"（e2）；节点标签查询（e3）确认 master、node1、node2 均不存在该标签。集群其他 59 个 Pod 均 Running，无其他异常。问题为 L1 层调度约束不匹配，无需检查资源不足、PVC 或 taint 分支。修复方式：移除 nodeSelector 或为节点添加匹配标签。", "root_cause_summary": "Pod rc-pending-nodeselector（aiops-e2e 命名空间）处于 Pending 状态，根因是 nodeSelector 不匹配。kubectl_get_yaml 确认 nodeSelector 设置为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}（e1）；kubectl_describe 显示调度器 3 次 FailedScheduling 事件，明确报告 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"（e2）；节点标签查询（e3）确认 master、node1、node2 均不存在该标签。集群其他 59 个 Pod 均 Running，无其他异常。问题为 L1 层调度约束不匹配，无需检查资源不足、PVC 或 taint 分支。修复方式：移除 nodeSelector 或为节点添加匹配标签。", "confidence": 0.98, "confidence_reason": "置信度 0.98：证据链完整且闭环——(e1) YAML 确认 nodeSelector 配置，(e2) 调度器事件明确报告不匹配原因，(e3) 节点标签列表直接证实无匹配标签，(e4) 确认 Pod 当前仍异常，(layer_1/layer_3) 全集群扫描排除其他异常。3 个独立证据源（YAML、Events、节点标签）交叉验证结论一致，因果链清晰无断点。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "集群节点资源不足（CPU/内存）", "probability": "low", "reason": "FailedScheduling 消息明确标注 'didn't match Pod's node affinity/selector' 而非资源不足；抢占机制也确认 'Preemption is not helpful'，排除资源竞争场景。59 个 Pod 正常运行表明集群有足够资源。"}, {"cause": "PVC/PV 未绑定导致调度阻塞", "probability": "low", "reason": "kubectl_get_yaml 显示 Pod 无 PVC 卷声明，仅有 kube-api-access 自动注入卷，不存在 PersistentVolumeClaims 依赖。PodScheduled condition 的 reason=Unschedulable 消息也未提及 PVC。"}, {"cause": "节点 taint 未被 toleration 容忍", "probability": "low", "reason": "调度器消息明确指向 node affinity/selector 不匹配，未提及 taint 相关原因。Pod 已配置了 2 个 tolerations（包括 node.kubernetes.io/not-ready），但节点均 Ready 无异常 taint 问题。"}, {"cause": "镜像拉取问题", "probability": "low", "reason": "镜像问题不会导致调度器 FailedScheduling，Pod 甚至未到达节点调度阶段。imagePullPolicy=Never 但仅在调度到节点后才生效。"}], "limitations": "未采集节点的完整 taint 列表（但 FailedScheduling 消息未提及 taint 相关原因，且节点均为 Ready 状态，taint 导致调度的可能性极低）。未分析 Pod 的 Owner/Controller（如是否存在 ReplicaSet），但该信息不影响 nodeSelector 不匹配的根因判断。", "llm_raw_analysis": "## 证据清点\n共 8 项证据（4 项新采集 + 4 项上游已验证）：\n- e1: kubectl_get_yaml — Pod YAML 配置（critical）\n- e2: kubectl_describe — 完整 Events 和 Status（critical）\n- e3: kubectl get nodes --show-labels — 节点标签（important）\n- e4: kubectl_get_by_name — Pod 当前状态确认（important）\n- layer_1: kubectl_get_by_kind_in_cluster — 全集群扫描（important）\n- layer_2: kubectl_get_by_name — 上游已确认（重要）\n- layer_3: kubectl_events — 集群事件（重要）\n- layer_4: kubectl_describe — 上游已确认（重要）\n\n## 逐条分析\ne1: Pod YAML 明确显示 nodeSelector={\"aiops.e2e/nonexistent-node-label\":\n... 截断，原始 929 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector（aiops-e2e 命名空间）处于 Pending 状态，根因是 nodeSelector 不匹配。kubectl_get_yaml 确认 nodeSelector 设置为 {"aiops.e2e/nonexistent-node-label"...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod rc-pending-nodeselector 的 spec 中配置了 nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}，但集群中 3 个节点（master、node1、node2）均没有该标签，导致调度器无法找到匹配的节点。
     传导机制: 调度器在每次调度周期中检查所有 3 个节点的标签与 Pod 的 nodeSelector 的匹配性，全部不匹配 → 调度失败 → 调度器重试（共触发 3 次 FailedScheduling 事件）→ 抢占机制尝试但无效（抢占不改变节点标签）→ Pod 持续处于 Pending 状态。
     最终表现: Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续 Pending 超过 17 分钟，0/1 容器未启动，无 Node 分配，无 IP 地址，集群 events 中持续产生 FailedScheduling 告警。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (24.4s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6163 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 40.7s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将基于您提供的所有数据，为您生成一份详尽、完整的诊断报告。

---

## 📊 诊断概览

您好，您的集群当前整体运行平稳，但存在 **1 个 Pod 处于 Pending 状态**，无法被调度。

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending (PendingUnschedulable) |
| **兼容归因层** | L1 (Scheduling) |
| **问题分类** | Pod 调度失败 |
| **置信度** | 高 (98%) |
| **证据完整度** | 4/4 (100%) |

**集群状态速览**:
*   **运行中 Pod**: 59 个 (全部正常)
*   **异常 Pod**: 1 个

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-pending-nodeselector` |
| Namespace | `aiops-e2e` |
| Node | `<none>` (未分配到节点) |
| 错误信息 | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` |

**现象摘要**：Pod `rc-pending-nodeselector` 在命名空间 `aiops-e2e` 中已经处于 Pending 状态超过 17 分钟。调度器事件明确报告所有 3 个节点均不匹配其节点选择器 (nodeSelector)。

---

## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod YAML 配置 | `kubectl_get_yaml` | `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}`, `finalizers: <none>`, `deletionTimestamp: <absent>` | Pod 明确配置了 `nodeSelector`，要求节点拥有 `aiops.e2e/nonexistent-node-label=true` 标签。没有 finalizers 阻塞，Pod 也未被删除。 |
| 2 | Pod 事件与状态 | `kubectl_describe` | `Warning FailedScheduling 17m default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.`, `Node-Selectors: aiops.e2e/nonexistent-node-label=true` | 调度器 3 次调度均失败(master, node1, node2)。原因直接指向 Pod 的 `nodeSelector`。 |
| 3 | 节点标签 | `run_bash_command` | `master` (标签: `<...>, kubernetes.io/hostname=master, ...`)<br>`node1` (标签: `<...>, kubernetes.io/hostname=node1, ...`)<br>`node2` (标签: `<...>, kubernetes.io/hostname=node2, ...`) | 集群 3 个节点均 **不包含** `aiops.e2e/nonexistent-node-label` 标签。 |
| 4 | Pod 存在性验证 | `kubectl_get_by_name` | `rc-pending-nodeselector   0/1     Pending   0          17m   <none>   <none>` | 目标 Pod 依然存在且状态未变，并非历史记录。 |
| 5 | 异常概览 | `kubectl_get_by_kind_in_cluster` | `rows=65 abnormal=1`, `status_counts={'Running': 59, 'Pending': 1}` | 集群 65 个 Pod 中，仅目标 Pod 异常，其余 59 个均运行正常。 |

### 证据关联分析
*   **证据 #1 + #2 + #3 印证**：Pod YAML (`#1`) 中配置的 `nodeSelector`，在调度事件 (`#2`) 中被明确指出不匹配，而节点标签查询 (`#3`) 确认了所有 3 个节点确实都没有这个标签。这三条证据形成了一条完整的证据链。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 节点完整 taint 列表 | low | **无影响**。FailedScheduling 消息未提及 taint，且节点均为 Ready。 |

---

## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                                        │
│ Pod rc-pending-nodeselector 的 spec 中配置了 nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}， │
│ 但集群中 master、node1、node2 这 3 个节点均不存在该标签。                                          │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                ↓
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                                        │
│ 调度器每次调度周期检查 Pod 的 nodeSelector 与所有节点标签的匹配性 → 3 个节点均不匹配 → 调度失败      │
│ → 调度器重试（共触发 3 次 FailedScheduling 事件） → 抢占机制尝试但无效（抢占不改变节点标签）         │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                ↓
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                                        │
│ 调度器无法将 Pod 绑定到任何节点，因为所有节点都不满足调度约束。                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                ↓
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                                    │
│ Pod rc-pending-nodeselector 持续 Pending 超过 17 分钟，0/1 容器未启动，无 Node 分配，无 IP 地址。   │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (Pod YAML)、#2 (Pod 事件) 和 #3 (节点标签) 的相互印证，问题的根本原因是**Pod 的 `nodeSelector` 配置了一个集群中不存在的标签**，导致调度器无法找到匹配节点。

**置信度**：高 (98%)
*   ✅ `kubectl_describe` 事件明确指向 “didn't match Pod's node affinity/selector”。
*   ✅ `kubectl_get_yaml` 确认了 `nodeSelector` 的具体内容。
*   ✅ `run_bash_command` 显示所有节点的标签均不包含该标签。
*   ⚠️ 无主要限制，根因明确，证据链完整。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）
**1. [推荐] 修改 Pod 配置，移除或更正 `nodeSelector`**
*   如果您不需要该调度约束，直接移除 `nodeSelector`。
*   如果您需要将 Pod 调度到特定节点，请确保节点上有对应的标签。

    **移除 nodeSelector (假设由 Deployment 管理)**:
    ```bash
    # 1. 获取当前 Deployment 的 YAML
    kubectl get deployment <your-deployment-name> -n aiops-e2e -o yaml > deploy.yaml
    
    # 2. 手动编辑 deploy.yaml，删除或修改 spec.template.spec.nodeSelector 字段
    
    # 3. 应用修改
    kubectl apply -f deploy.yaml
    ```

    **或者，直接编辑 Deployment (如果被 ReplicaSet 控制)**:
    ```bash
    # 如果 Pod 由 Deployment 管理，直接修改 Deployment 
    kubectl edit deployment <your-deployment-name> -n aiops-e2e
    # 在编辑器中找到 nodeSelector 字段，将其删除或修改。
    ```

**2. [备选] 为节点添加匹配的标签**
*   如果您确实希望 Pod 运行在一个特定的节点上，可以为该节点打上所需的标签。

    **为节点 `node1` 添加标签**:
    ```bash
    kubectl label node node1 aiops.e2e/nonexistent-node-label=true
    ```

### 后续优化
1.  **规范 Pod 配置**：在创建 Pod 或 Deployment 时，仔细检查 `nodeSelector` 或 `affinity` 配置，确保目标标签存在。
2.  **CI/CD 流程验证**：在 CI/CD 流程中加入简单的检查，例如通过 `kubectl get nodes --show-labels` 验证新 Pod 的调度约束是否与现有节点标签匹配。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 查看 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS 变为 `Running` 或 `ContainerCreating`。 |
| 2. 检查 Pod 分配节点 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o wide` | `NODE` 列显示一个具体的节点名。 |
| 3. 检查调度事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | Events 中不再出现 `FailedScheduling`。 |

---

## ⚠️ 注意事项
*   **集群范围影响**：此问题仅限于单个 Pod，不影响集群中其他 59 个运行正常的服务。集群整体是健康的。
*   **被排除的候选原因**：根据工具事实，Pod 的 `finalizers` 为空，因此排除了“finalizer 未清理”的可能性。所有节点均为 `Ready` 状态，排除了“节点不可达”的可能性。`FailedScheduling` 事件未提及 CPU/内存不足，排除了“资源不足”的可能性。

---

## 📊 性能统计

├─ 总耗时: 1.7m
├─ 问题定位: 23.0s (23%) ✅
├─ 证据链采集: 21.6s (21%) ✅
├─ 根因分析: 31.7s (31%) ✅
├─ 汇总总结: 24.4s (24%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 9 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 9 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
