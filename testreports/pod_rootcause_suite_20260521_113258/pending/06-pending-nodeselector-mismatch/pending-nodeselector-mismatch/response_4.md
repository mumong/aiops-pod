======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: ff5acc8389244927]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我先全局扫描集群中的所有 Pod，看看当前有哪些异常状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 集群中大部分 Pod 正常运行，但有 **1 个异常 Pod**。让我进一步查看详情。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE    IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          101s   <none>   <none> 
   💭 [问题定位] Pod 处于 Pending 状态且未绑定到节点，看标签指向 `PendingUnschedulable`。让我查看调度事件和 Pod 详情。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  103s  default-scheduler  0/3 nodes are available: 3 node(s) did
   💭 [问题定位] 好的，现在我已经掌握了所有信息。让我获取对应的 runbook 参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在信息齐全了，我来给出完整的定位分析结果。

---

## 集群 Pod 异常定位分析

### 全局扫描结果
集群共有 **65 个 Pod**，分布在多个命名空间，其中：
- **59 个 Running**（正常）
- **1 个 Pending**（异常）

### Pod 异常详情

| 命名空间 | Pod 名称 | 状态 | 就绪 | 重启 | 节点 |
|---------|---------|------|------|------|------|
| `aiops-e2e` | `rc-pending-nodeselector` | **Pending** | 0/1 | 0 | `<none>` |

---

### 异常组归类

**`abnormal_groups`**：
- **PendingUnschedulable**：`rc-pending-nodeselector`（1 个 Pod，Pending，未绑定节点）

---

### 根因分析

从 `kubectl describe` 看到的调度失败信息非常明确：

> **`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.`**

Pod 的 `Node-Selectors` 为：
```
aiops.e2e/nonexistent-node-label=true
```

这意味着 Pod 要求节点必须带有标签 `aiops.e2e/nonexistent-node-label=true`，但集群中 **3 个节点均没有这个标签**，导致没有节点可以调度。

---

### 定位输出

| 字段 | 值 |
|------|-----|
| **`layer`** | **L1** — 调度层异常（PendingUnschedulable） |
| **`layer_name`** | **PendingUnschedulable - nodeSelector 不匹配** |
| **`pod_status_keyword`** | **Pending** |
| **`pod_abnormal_type`** | **PendingUnschedulable** |
| **`status_category`** | **scheduling** |
| **`confidence`** | **高** |
| **`abnormal_pods`** | `aiops-e2e/rc-pending-nodeselector` |
| **`abnormal_groups`** | `PendingUnschedulable`（1 个 Pod） |
| **`key_entities`** | Pod: `rc-pending-nodeselector`（ns: aiops-e2e）|
| **`possible_scenarios`** | nodeSelector 标签 `aiops.e2e/nonexistent-node-label=true` 在集群 3 个节点上均不存在，导致调度器无法放置 Pod |

### 后续审查方向
- 确认是否需要在目标节点上添加标签 `aiops.e2e/nonexistent-node-label=true`
- 或者修改 Pod 的 `nodeSelector` 以匹配现有节点标签
- 可以通过 `kubectl get nodes --show-labels` 查看当前节点标签情况
   ✅ [问题定位] 完成 (19.2s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector 标签不匹配', 'probability': '高', 'reason': "FailedScheduling事件明确提示3 node(s) didn't match Pod's node affinity/selector，Pod指定了标签aiops.e2e/nonexistent-node-label=true但集群节点均无此标签"}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}]
   reasoning=集群中存在1个异常Pod rc-pending-nodeselector（命名空间aiops-e2e），状态为Pending，未绑定任何节点（NODE=<none>）。kubectl describe显示FailedScheduling事件：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod的Node-Selectors为aiops.e2e/nonexistent-node-label=true，但集群3个节点均无此标签。根据五层模型映射规则，PendingUnschedulable归因为L1（调度层异常，scheduling类别），pod_status_keyword为Pending，pod_abnormal_type为PendingUnschedulable。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable - nodeSelector 不匹配", "confidence": 0.95, "reasoning": "集群中存在1个异常Pod rc-pending-nodeselector（命名空间aiops-e2e），状态为Pending，未绑定任何节点（NODE=<none>）。kubectl describe显示FailedScheduling事件：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod的Node-Selectors为aiops.e2e/nonexistent-node-label=true，但集群3个节点均无此标签。根据五层模型映射规则，PendingUnschedulable归因为L1（调度层异常，scheduling类别），pod_status_keyword为Pending，pod_abnormal_type为PendingUnschedulable。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "nodeSelector 标签不匹配", "probability": "高", "reason": "FailedScheduling事件明确提示3 node(s) didn't match Pod's node affinity/selector，Pod指定了标签aiops.e2e/nonexistent-node-label=true但集群节点均无此标签"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              100s    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/ff5acc8389244927/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/ff5acc8389244927/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/ff5acc8389244927/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我已理解任务。根据上游 `layer_handoff` 的定位，Pod `rc-pending-nodeselector` 处于 Pending 状态，异常类型为 `PendingUnschedulable`，已匹配 runbook `pod-pending-unschedulable.md`。既有 evidence_plan 已生成，现在直接执行真实工具采证。

首先执行关键的第 e1（describe）、e2（YAML）、e3（节点标签）和 e4（事件），这几个没有依赖关系可以并行。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nmaster   Ready    co
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:18:44Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
2m9s        Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  2m9s  default-scheduler  0/3 nodes are available: 3 node(s) did
   💭 [证据链采集] 所有关键工具结果已返回，现在执行参考级 runbook 验证（e5）。
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [证据链采集] 全部关键工具执行完毕。以下是本轮证据采集结论。

---

## 证据采集结论

### ✅ 已采集证据

| 计划项 | 维度 | 证据摘要 |
|--------|------|---------|
| **e1 - kubectl_describe pod** | ✅ critical | Pod `rc-pending-nodeselector`（aiops-e2e），STATUS=Pending，NODE=`<none>`，Node-Selectors=`aiops.e2e/nonexistent-node-label=true`。Events: `Warning FailedScheduling - 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` |
| **e2 - kubectl_get_yaml pod** | ✅ critical | `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}`，`phase: Pending`，`conditions.PodScheduled.status=False reason=Unschedulable`，`imagePullPolicy=Never`，无 resource requests/limits（QoS BestEffort） |
| **e3 - kubectl get nodes --show-labels** | ✅ critical | 集群有 **3 个 Ready 节点**（master/node1/node2），**没有任何节点**包含标签 `aiops.e2e/nonexistent-node-label`（节点标签列表均不匹配该 key） |
| **e4 - kubectl_events pod** | ✅ important | 唯一事件：`FailedScheduling` - `3 node(s) didn't match Pod's node affinity/selector`，无其他调度事件 |
| **e5 - fetch_runbook** | ✅ reference | 已读取 runbook，对比判定规则确认：`FailedScheduling + node(s) didn't match node selector/affinity` → **调度约束不匹配**，置信度 **高** |

### ❌ 未采集/不适用
- 无 PVC 相关证据：Pod 未使用 PVC，无需检查
- 无资源不足证据：FailedScheduling 原文不含 `Insufficient` 关键字
- 无 taint/toleration 证据：3 节点均 Ready，Pod tolerations 正常
- 无 Terminating 或其他并发异常组：status_counts 仅有 1 个 Pending

### ⚠️ 冲突/负向证据
无冲突证据。所有工具均正常返回，Pod 和节点均存在且状态可验证。

---

### 🎯 根因结论

**Pod `rc-pending-nodeselector` 调度失败的根本原因是：Pod 设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，但集群 3 个节点（master/node1/node2）均不包含此标签，导致调度器找不到可匹配的节点。** 该标签名中的 `nonexistent` 字面也暗示这是故意构造的异常场景。
   ✅ [证据链采集] 完成 (21.7s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1-pod-describe","description":"验证 Pod rc-pending-nodeselector 当前状态、Events 和 spec（nodeSelector/affinity 约束）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e","resource_type":"pod","resource_name":"rc-pending-nodeselector"},"purpose":"确认 FailedScheduling 事件原文和 nodeSelector/affinity 约束条件","evidence_type":"pod_describe","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2-pod-yaml","description":"获取 Pod YAML 确认 nodeSelector 和调度约束细节","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e","resource_type":"pod","resource_name":"rc-pending-nodeselector"},"purpose":"检查 nodeSelector/affinity 字段和调度策略","evidence_type":"pod_yaml","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3-node-list","description":"获取集群节点列表及其标签，验证是否存在匹配 nodeSelector 的节点","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o wide --show-labels","tool_args":{"command":"kubectl get nodes -o wide --show-labels"},"purpose":"检查节点是否拥有 Pod 所需的 aiops.e2e/nonexistent-node-label=true 标签","evidence_type":"node_labels","target_scope":"cluster_nodes","acceptable_tools":["run_bash_command"],"counts_for_completeness":true},{"id":"e4-events","description":"检查 namesapce aiops-e2e 下与调度相关的事件","level":"important","tool":"kubectl_events","command":"kubectl events -n aiops-e2e --for pod/rc-pending-nodeselector","tool_args":{"namespace":"aiops-e2e","resource_type":"pod","resource_name":"rc-pending-nodeselector"},"purpose":"确认 FailedScheduling 事件详情及后续是否有新的调度事件","evidence_type":"pod_events","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"e5-runbook-ref","description":"获取 PendingUnschedulable runbook 作为参考验证依据","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","tool_args":{"runbook_name":"pod-pending-unschedulable.md"},"purpose":"对比 runbook 场景确认异常是否与 nodeSelector/affinity 不匹配一致","evidence_type":"runbook_reference","target_scope":"reference","acceptable_tools":["fetch_runbook"],"counts_for_completeness":false}],"tool_results":[],"tool_data":[{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\\nmaster   Ready    control-plane   238d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\\nnode1    Ready    <none>          238d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\nnode2    Ready    <none>          238d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ff5acc8389244927/tools/001-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ff5acc8389244927/tools/001-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ff5acc8389244927/tools/001-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ff5acc8389244927/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ff5acc8389244927/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ff5acc8389244927/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n2m9s        Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ff5acc8389244927/tools/003-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ff5acc8389244927/tools/003-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ff5acc8389244927/tools/003-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  2m9s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  2m9s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ff5acc8389244927/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ff5acc8389244927/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ff5acc8389244927/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"fetch_runbook","data":"<runbook>\n# Pod PendingUnschedulable / 调度失败\n\n> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | Pending，且 Events 含 `FailedScheduling` |\n| 资源不足 | `Insufficient cpu/memory/ephemeral-storage`、`Too many pods` |\n| 调度约束 | nodeSelector/affinity 不匹配、节点 taint 未被 toleration 容忍 |\n| 存储前置条件 | `pod has unbound immediate PersistentVolumeClaims` 应切换到 pod-volume-mount-failed |\n| 节点状态 | Node NotReady/Unknown、SchedulingDisabled、Unschedulable 会导致无可用调度节点 |\n\n## 根因分流\n- 资源不足: FailedScheduling 原文含 Insufficient cpu/memory/ephemeral-storage、Too many pods。\n- hostPort 冲突: 原文含 `didn't have free ports for the requested pod ports`，说明目标节点端口已被占用。\n- Taint/Toleration 不匹配: 原文含 `had untolerated taint`，必须检查 Pod tolerations 和 Node taints。\n- nodeSelector / nodeAffinity / podAffinity 不匹配: 原文含 `didn't match Pod's node affinity/selector` 或 affinity/anti-affinity。\n- PVC 未绑定: 原文含 `unbound immediate PersistentVolumeClaims`，根因在存储绑定而不是调度资源。\n- 节点不可调度: Node Ready=False/Unknown、SchedulingDisabled、`node.kubernetes.io/not-ready` 或 `node.kubernetes.io/unreachable`。\n- 镜像、挂载、容器启动错误不会表现为 FailedScheduling；如果 Pod 已绑定 nodeName，应切换到对应 runbook。\n\n## 诊断流程\n\n### Step 1: 确认 Pod 调度失败事件\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n关注 Events 中的 `FailedScheduling` 原文。\n\n### Step 2: 检查 Pod 调度约束\n```bash\nkubectl get pod <pod-name> -n <namespace> -o yaml\n```\n关注: spec.nodeName 是否为空、nodeSelector、affinity、tolerations、topologySpreadConstraints、schedulerName、priorityClassName、resource requests、hostNetwork/hostPort。\n\n### Step 3: 检查节点状态和可调度性\n```bash\nkubectl get nodes -o wide\n```\n关注: STATUS 列是否有 NotReady/Unknown，AGE 判断是否新节点\n\n### Step 4: 检查候选节点详情\n```bash\nkubectl describe node <node-name>\n```\n重点关注:\n- `Conditions` 部分: Ready=False/Unknown 的 reason 和 message\n- `Taints` 部分: 是否有 NoSchedule/NoExecute taint\n- `Allocatable` vs `Capacity`: 资源是否耗尽\n- `Non-terminated Pods`: 节点上运行的 Pod 数量\n\n### Step 5: 检查 PVC 状态（如果 FailedScheduling 指向 PVC）\n```bash\nkubectl get pvc -n <namespace>\nkubectl describe pvc <pvc> -n <namespace>\n```\n关注: Pending、StorageClass、volumeBindingMode、ProvisioningFailed。\n\n### Step 6: 检查 Ready 条件详情\n```bash\nkubectl get node <node-name> -o jsonpath='{.status.conditions[?(@.type==\"Ready\")]}' | python3 -m json.tool\n```\n关注: status, reason, message, lastHeartbeatTime\n\n### Step 7: 检查节点事件\n```bash\nkubectl get events -A --field-selector involvedObject.kind=Node,involvedObject.name=<node-name> --sort-by='.lastTimestamp'\n```\n关注: NodeNotReady、NodeNotSchedulable、PLEG unhealthy 等事件\n\n### Step 8: 检查受影响的 Pending Pod\n```bash\nkubectl get pods -A --field-selector status.phase=Pending | head -20\n```\n\n## 判定规则\n\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| FailedScheduling + Insufficient cpu/memory | 资源不足导致 Pod Pending | 高 |\n| FailedScheduling + Too many pods | 节点 Pod 数量上限导致 Pending | 高 |\n| FailedScheduling + didn't have free ports for the requested pod ports | hostPort 端口冲突导致 Pending | 高 |\n| FailedScheduling + had untolerated taint | taint/toleration 不匹配 | 高 |\n| FailedScheduling + node(s) didn't match node selector/affinity | 调度约束不匹配 | 高 |\n| FailedScheduling + pod has unbound immediate PersistentVolumeClaims | PVC 未绑定，应切换 VolumeMountFailed/PVC 分支 | 高 |\n| 所有候选 Node NotReady/Unschedulable | 无可用调度节点 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ff5acc8389244927/tools/005-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ff5acc8389244927/tools/005-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ff5acc8389244927/tools/005-evidence-fetch_runbook.summary.txt"}],"llm_analysis":"全部关键工具执行完毕。以下是本轮证据采集结论。\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据\n\n| 计划项 | 维度 | 证据摘要 |\n|--------|------|---------|\n| **e1 - kubectl_describe pod** | ✅ critical | Pod `rc-pending-nodeselector`（aiops-e2e），STATUS=Pending，NODE=`<none>`，Node-Selectors=`aiops.e2e/nonexistent-node-label=true`。Events: `Warning FailedScheduling - 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` |\n| **e2 - kubectl_get_yaml pod** | ✅ critical | `nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}`，`phase: Pending`，`conditions.PodScheduled.status=False reason=Unschedulable`，`imagePullPolicy=Never`，无 resource requests/limits（QoS BestEffort） |\n| **e3 - kubectl get nodes --show-labels** | ✅ critical | 集群有 **3 个 Ready 节点**（master/node1/node2），**没有任何节点**包含标签 `aiops.e2e/nonexistent-node-label`（节点标签列表均不匹配该 key） |\n| **e4 - kubectl_events pod** | ✅ important | 唯一事件：`FailedScheduling` - `3 node(s) didn't match Pod's node affinity/selector`，无其他调度事件 |\n| **e5 - fetch_runbook** | ✅ reference | 已读取 runbook，对比判定规则确认：`FailedScheduling + node(s) didn't match node selector/affinity` → **调度约束不匹配**，置信度 **高** |\n\n### ❌ 未采集/不适用\n- 无 PVC 相关证据：Pod 未使用 PVC，无需检查\n- 无资源不足证据：FailedScheduling 原文不含 `Insufficient` 关键字\n- 无 taint/toleration 证据：3 节点均 Ready，Pod tolerations 正常\n- 无 Terminating 或其他并发异常组：status_counts 仅有 1 个 Pending\n\n### ⚠️ 冲突/负向证据\n无冲突证据。所有工具均正常返回，Pod 和节点均存在且状态可验证。\n\n---\n\n### 🎯 根因结论\n\n**Pod `rc-pending-nodeselector` 调度失败的根本原因是：Pod 设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，但集群 3 个节点（master/node1/node2）均不包含此标签，导致调度器找不到可匹配的节点。** 该标签名中的 `nonexistent` 字面也暗示这是故意构造的异常场景。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 7 个，匹配计划 5 个，未规划证据 2 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":7,"matched_tool_count":5,"unplanned_tool_count":2,"evidence_inventory":[{"id":"e1-pod-describe","description":"验证 Pod rc-pending-nodeselector 当前状态、Events 和 spec（nodeSelector/affinity 约束）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"确认 FailedScheduling 事件原文和 nodeSelector/affinity 约束条件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-pod-yaml","description":"获取 Pod YAML 确认 nodeSelector 和调度约束细节","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"检查 nodeSelector/affinity 字段和调度策略","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3-node-list","description":"获取集群节点列表及其标签，验证是否存在匹配 nodeSelector 的节点","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o wide --show-labels","purpose":"检查节点是否拥有 Pod 所需的 aiops.e2e/nonexistent-node-label=true 标签","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4-events","description":"检查 namesapce aiops-e2e 下与调度相关的事件","level":"important","tool":"kubectl_events","command":"kubectl events -n aiops-e2e --for pod/rc-pending-nodeselector","purpose":"确认 FailedScheduling 事件详情及后续是否有新的调度事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5-runbook-ref","description":"获取 PendingUnschedulable runbook 作为参考验证依据","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","purpose":"对比 runbook 场景确认异常是否与 nodeSelector/affinity 不匹配一致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1-pod-describe | critical | ✅ | kubectl_describe | 验证 Pod rc-pending-nodeselector 当前状态、Events 和 ... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e2-pod-yaml | critical | ✅ | kubectl_get_yaml | 获取 Pod YAML 确认 nodeSelector 和调度约束细节 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e3-node-list | critical | ✅ | run_bash_command | 获取集群节点列表及其标签，验证是否存在匹配 nodeSelector 的节点 | `kubectl get nodes -o wide --show-labels` |
   | e4-events | important | ✅ | kubectl_events | 检查 namesapce aiops-e2e 下与调度相关的事件 | `kubectl events -n aiops-e2e --for pod/rc-pending-nodeselector` |
   | e5-runbook-ref | reference | ✅ | fetch_runbook | 获取 PendingUnschedulable runbook 作为参考验证依据 | `fetch_runbook pod-pending-unschedulable.md` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (21.0s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector（命名空间 aiops-e2e）状态为 Pending，根本原因是其 spec.nodeSelector 要求节点包含标签 `aiops.e2e/nonexistent-node-label=true`（来自 kubectl_get_yaml 确认），但集群 3 个节点（master/node1/node2）均不包含该标签（来自 kubectl_get_nodes --show-labels 确认）。调度器事件（kubectl_describe/kubectl_events）明确报告 "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"，preemption 也无法帮助。Pod 不存在资源不足、taint/toleration、PVC 等其他调度障碍。标签名中的 "nonexistent" 表明这可能是测试场景的构造异常。
   confidence=98%
   causal_chain={"root_cause": "Pod 设置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，但集群 3 个节点均不具备该标签", "propagation": "调度器遍历所有 3 个节点，逐一检查节点标签是否匹配 nodeSelector → 所有节点均不包含标签 aiops.e2e/nonexistent-node-label → 调度器无候选节点可调度 → 产生 FailedScheduling 事件 → Pod 持续停留在 Pending 状态", "direct_cause": "节点标签与 Pod 的 nodeSelector 完全无交集，3/3 节点被过滤排除", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中保持 Pending 状态，NODE 列为 <none>，kubectl describe 显示 FailedScheduling 事件"}
   rca_analysis={"phenomenon": "命名空间 aiops-e2e 下 Pod rc-pending-nodeselector 状态为 Pending，未绑定任何节点（NODE=&lt;none&gt;），调度器持续报告 FailedScheduling 事件。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod rc-pending-nodeselector 状态 Pending，NODE=<none>，Node-Selectors=aiops.e2e/nonexistent-node-label=true，FailedScheduling: 0/3 nodes available, 3 didn't match affinity/selector", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml", "content": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}, phase: Pending, conditions.PodScheduled: status=False reason=Unschedulable, imagePullPolicy=Never", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_nodes", "content": "3 个 Ready 节点（master/node1/node2），均无标签 aiops.e2e/nonexistent-node-label", "reliability": "高"}, {"id": "e4", "source": "kubectl_events", "content": "Warning FailedScheduling: 0/3 nodes available, 3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}, {"id": "e5", "source": "fetch_runbook", "content": "runbook 判定规则: FailedScheduling + didn't match node selector/affinity → 调度约束不匹配，置信度高", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Node-Selectors: aiops.e2e/nonexistent-node-label=true, FailedScheduling: 3 node(s) didn't match Pod's node affinity/selector", "interpretation": "Pod 显式要求节点必须包含标签 aiops.e2e/nonexistent-node-label=true，调度器在全部 3 个节点上均未匹配到该标签，导致调度失败。"}, {"evidence_id": "e2", "raw_data": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}, phase: Pending, condition: PodScheduled=False reason=Unschedulable", "interpretation": "YAML 确认 nodeSelector 为唯一调度约束，PodScheduled condition 明确标记为 Unschedulable，表明调度器无法找到符合条件的节点。"}, {"evidence_id": "e3", "raw_data": "master LABELS: beta.kubernetes.io/arch=amd64,...; node1 LABELS: beta.kubernetes.io/arch=amd64,...; node2 LABELS: beta.kubernetes.io/arch=amd64,... (均不含 aiops.e2e/nonexistent-node-label)", "interpretation": "集群 3 个节点（master, node1, node2）的标签列表中均不包含 aiops.e2e/nonexistent-node-label 这个 key，证实没有任何节点可满足 Pod 的 nodeSelector 要求。"}, {"evidence_id": "e4", "raw_data": "Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "interpretation": "调度器事件确认全部 3 个节点均因 node affinity/selector 不匹配而被排除，且 preemption 无法帮助，因为没有候选节点可抢占。"}, {"evidence_id": "e5", "raw_data": "runbook 判定规则: FailedScheduling + node(s) didn't match node selector/affinity → 调度约束不匹配，置信度高", "interpretation": "runbook 诊断规则明确指出该症状组合对应 nodeSelector/affinity 不匹配，与本案例完全吻合。"}], "causal_chain": {"root_cause": "Pod 设置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，但集群 3 个节点均不具备该标签", "propagation": "调度器遍历所有 3 个节点，逐一检查节点标签是否匹配 nodeSelector → 所有节点均不包含标签 aiops.e2e/nonexistent-node-label → 调度器无候选节点可调度 → 产生 FailedScheduling 事件 → Pod 持续停留在 Pending 状态", "direct_cause": "节点标签与 Pod 的 nodeSelector 完全无交集，3/3 节点被过滤排除", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中保持 Pending 状态，NODE 列为 <none>，kubectl describe 显示 FailedScheduling 事件"}, "root_cause": "Pod rc-pending-nodeselector（命名空间 aiops-e2e）状态为 Pending，根本原因是其 spec.nodeSelector 要求节点包含标签 `aiops.e2e/nonexistent-node-label=true`（来自 kubectl_get_yaml 确认），但集群 3 个节点（master/node1/node2）均不包含该标签（来自 kubectl_get_nodes --show-labels 确认）。调度器事件（kubectl_describe/kubectl_events）明确报告 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"，preemption 也无法帮助。Pod 不存在资源不足、taint/toleration、PVC 等其他调度障碍。标签名中的 \"nonexistent\" 表明这可能是测试场景的构造异常。", "root_cause_summary": "Pod rc-pending-nodeselector（命名空间 aiops-e2e）状态为 Pending，根本原因是其 spec.nodeSelector 要求节点包含标签 `aiops.e2e/nonexistent-node-label=true`（来自 kubectl_get_yaml 确认），但集群 3 个节点（master/node1/node2）均不包含该标签（来自 kubectl_get_nodes --show-labels 确认）。调度器事件（kubectl_describe/kubectl_events）明确报告 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"，preemption 也无法帮助。Pod 不存在资源不足、taint/toleration、PVC 等其他调度障碍。标签名中的 \"nonexistent\" 表明这可能是测试场景的构造异常。", "confidence": 0.98, "confidence_reason": "直接证据充分且一致：kubectl_describe 显示 nodeSelector 和 FailedScheduling 事件，kubectl_get_yaml 确认 nodeSelector 精确值，kubectl_get_nodes 确认 3 个节点均无匹配标签，kubectl_events 与 describe 结果完全一致。runbook 判定规则也明确指向该根因。无任何冲突或负向证据。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "资源不足（CPU/内存不足）", "probability": "low", "reason": "FailedScheduling 原文不含 Insufficient cpu/memory 关键字，Pod QoS 为 BestEffort（无 resource requests），已排除"}, {"cause": "节点 taint 未被 toleration 容忍", "probability": "low", "reason": "3 节点均 Ready，无异常 taint 信息；Pod 有 tolerations（node.kubernetes.io/not-ready:NoExecute），已排除"}, {"cause": "PVC 未绑定", "probability": "low", "reason": "Pod 未声明任何 PVC，FailedScheduling 原文不含 unbound PersistentVolumeClaims，已排除"}, {"cause": "节点不可调度（NotReady/Unschedulable）", "probability": "low", "reason": "3 节点 STATUS 均为 Ready，无 SchedulingDisabled 标记，已排除"}], "limitations": "本次分析仅涉及 1 个异常 Pod（rc-pending-nodeselector），集群中其他 59 个 Running Pod 均正常。标签名 \"nonexistent-node-label\" 暗示此 Pod 可能是测试场景的构造异常，但不影响根因判断的准确性。", "llm_raw_analysis": "## 证据清点\n\n共采集 5 项证据，全部成功返回，无冲突或负向证据。\n\n- **e1 (critical)**: kubectl_describe → Pod 状态、nodeSelector、FailedScheduling 事件\n- **e2 (critical)**: kubectl_get_yaml → nodeSelector 精确值、PodScheduled=False/Unschedulable\n- **e3 (critical)**: kubectl_get_nodes --show-labels → 3 个 Ready 节点标签列表\n- **e4 (important)**: kubectl_events → 确认 FailedScheduling 事件\n- **e5 (reference)**: fetch_runbook → runbook 判定规则匹配\n\n## 逐条分析\n\n**e1**: Pod rc-pending-nodeselector 状态 Pending，Node-Selectors=aiops.e2e/nonexistent-node-label=t\n... 截断，原始 1342 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector（命名空间 aiops-e2e）状态为 Pending，根本原因是其 spec.nodeSelector 要求节点包含标签 `aiops.e2e/nonexistent-node-label=true`（来自 kubectl_get_yaml 确...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod 设置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，但集群 3 个节点均不具备该标签
     传导机制: 调度器遍历所有 3 个节点，逐一检查节点标签是否匹配 nodeSelector → 所有节点均不包含标签 aiops.e2e/nonexistent-node-label → 调度器无候选节点可调度 → 产生 FailedScheduling 事件 → Pod 持续停留在 Pending 状态
     最终表现: Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中保持 Pending 状态，NODE 列为 <none>，kubectl describe 显示 FailedScheduling 事件


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (19.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5903 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 21.8s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，这是根据您提供的三个阶段的诊断分析结果生成的详尽诊断报告。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **整体集群状态** | 集群基本健康，在 65 个 Pod 中，59 个运行正常 (Running)，1 个异常 (Pending) |
| **Pod异常状态** | Pending |
| **兼容归因层** | L1 - 调度层异常 |
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
| Node | `<none>` (未绑定) |
| 错误信息 | `FailedScheduling` - 3 node(s) didn't match Pod's node affinity/selector |

**问题总结**：
集群整体运行平稳（65个Pod中59个Running），但存在1个处于 **Pending** 状态的Pod。该Pod无法被调度到任何节点上，调度器明确报告 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。

---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态及事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | `status: Pending`<br>`Node-Selectors: aiops.e2e/nonexistent-node-label=true`<br>`Warning FailedScheduling  2m9s default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | Pod 因 `nodeSelector` 不匹配导致调度失败 |
| 2 | Pod YAML 配置 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` | `spec.nodeSelector: {aiops.e2e/nonexistent-node-label: "true"}` | 确认 Pod 的调度约束是 `nodeSelector` 标签 `aiops.e2e/nonexistent-node-label=true` |
| 3 | 集群节点标签 | `kubectl get nodes --show-labels` | 集群节点 (master, node1, node2) 的标签列表中**均不包含** `aiops.e2e/nonexistent-node-label` | 集群中没有任何节点满足 Pod 的 `nodeSelector` 要求 |
| 4 | 命名空间事件 | `kubectl get events -n aiops-e2e` | `2m9s Warning FailedScheduling Pod/rc-pending-nodeselector 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` | 调度器已穷尽所有节点，但无一匹配，且抢占调度(Preemption)也无法解决 |

### 证据关联分析
- **证据 #1 和 #3 印证**：Pod 的 `Node-Selectors` 要求节点包含 `aiops.e2e/nonexistent-node-label=true`，但集群中所有节点的标签列表均不包含此标签。
- **证据链**：Pod 设置 `nodeSelector` → 调度器遍历所有节点检查标签 → 3 个节点均不满足条件 → 产生 `FailedScheduling` 事件 → Pod 无法被调度，持续处于 `Pending` 状态。

### 缺失证据（如有）
**无。** 所有必需的关键证据均已成功采集，证据链完整。

---
## 🎯 根因分析

### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                                         │
│ Pod (rc-pending-nodeselector) 的 spec 中设置了 nodeSelector: aiops.e2e/nonexistent-node-label=true │
│ 但集群中3个节点均不具备该标签。                                                                　   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                                         │
│ 调度器 (default-scheduler) 在调度时检查节点标签是否匹配 → 遍历所有3个节点，发现均不匹配            │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                                         │
│ 调度器无法找到任何候选节点，产生 FailedScheduling 事件，且 Preemption (抢占) 也无法帮助调度。    │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                                     │
│ Pod rc-pending-nodeselector 状态为 Pending，NODE 列为 <none>，无法正常运行。                      │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #1 (FailedScheduling 事件)、证据 #2 (Pod YAML 确认 nodeSelector) 和证据 #3 (节点标签不匹配)，问题的根本原因是 Pod `rc-pending-nodeselector` 的 `nodeSelector` 指定了一个集群中不存在的节点标签 `aiops.e2e/nonexistent-node-label=true`（标签名中的 `nonexistent` 暗示这可能是一个测试场景），导致调度器无法在任何节点上调度该 Pod。

**置信度**：高 (98%)
- ✅ Pod YAML 明确指定了 `nodeSelector`
- ✅ 调度器事件明确报告节点标签不匹配 (`node affinity/selector`)
- ✅ 节点标签列表证实了该标签不存在
- ✅ 标签名 `nonexistent` 与问题高度吻合

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [推荐] 移除 Pod 的 `nodeSelector` 或修改为正确的标签**
根据您的意图，执行以下操作之一：
- **如果不需要节点选择**：直接编辑 Deployment/StatefulSet/Job 或删除并重建 Pod，移除 `nodeSelector` 配置。
  ```bash
  # 如果是通过 Deployment 管理，先获取完整 YAML，编辑后应用
  kubectl get deployment <deployment-name> -n aiops-e2e -o yaml > deploy.yaml
  # 编辑 deploy.yaml，删除 spec.template.spec.nodeSelector 部分
  # 然后应用更新
  kubectl apply -f deploy.yaml
  ```
- **如果 Pod 是独立创建的**：直接删除 Pod，调度器会自动尝试调度，但需确保源头配置已修改。
- **如果需要选择特定节点**：为期望运行的节点打上正确的标签。
  ```bash
  # 为节点1打上 Pod 需要的标签
  kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true
  ```

**2. [查看] 检查创建此 Pod 的上层控制器**
```bash
# 通过 Pod 的 ownerReferences 查看其父对象
kubectl get pod rc-pending-nodeselector -n aiops-e2e -o jsonpath='{.metadata.ownerReferences}'
```
*目的*：确认 Pod 是由 Deployment、StatefulSet、Job 还是 DaemonSet 创建的，以便从根本上修改配置。

### 后续优化 (如为测试场景可忽略)
1. **配置审查**：检查 CI/CD 或部署脚本中是否硬编码了不存在的 nodeSelector 或标签值。
2. **创建约束检查**：可以考虑使用准入控制器 (Admission Controller) 或策略引擎 (如 OPA/Gatekeeper) 来校验 Pod 的 nodeSelector 是否指向了集群中存在的标签。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 已被调度 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o wide` | NODE 列显示为具体的节点名称，而非 `<none>` |
| 2. 确认 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: `Running` 或 `ContainerCreating` |
| 3. 确认无新的调度失败事件 | `kubectl get events -n aiops-e2e --field-selector reason=FailedScheduling` | 不再显示新的 FailedScheduling 事件 |

---
## ⚠️ 注意事项
- 本次分析仅涉及 1 个异常 Pod，集群中其余 59 个 Pod 均正常运行。
- 标签名 `nonexistent-node-label` 强烈暗示此异常是由测试场景构造的，修复建议需根据实际业务需求选择是移除约束还是打上标签。

---

## 📊 性能统计

├─ 总耗时: 1.4m
├─ 问题定位: 19.2s (23%) ✅
├─ 证据链采集: 21.7s (27%) ✅
├─ 根因分析: 21.0s (26%) ✅
├─ 汇总总结: 19.8s (24%) ✅
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
