======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: a312ae31bbf54d6b]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来先扫描整个集群的全局 Pod 状态，看看有哪些异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 很好！我扫描到了全集群的 Pod。目前有一个异常 Pod。让我进一步看看它的详情。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  7m51s  default-scheduler  0/3 nodes are available: 3 node(s) di
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE     IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          7m52s   <none>   <none
   💭 [问题定位] 这个 Pod 的标签已经标识了 `pod_abnormal_type=PendingUnschedulable`，正好匹配 runbook。让我获取一下对应的 runbook 作为参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在已经有了完整的定位信息。让我汇总一下分析结果。

## 诊断分析结果

### 全局 Pod 扫描
| 总 Pod 数 | 正常 Running | 异常 |
|-----------|-------------|------|
| 65 | 59 | 1 |

---

### 异常 Pod 详情

| 字段 | 值 |
|------|-----|
| **Pod** | `rc-pending-nodeselector` |
| **命名空间** | `aiops-e2e` |
| **状态** | `Pending` |
| **READY** | `0/1` |
| **节点** | `<none>`（未绑定节点） |
| **异常类型** | `PendingUnschedulable` |
| **兼容分层** | **L1** |

### 根因分析

该 Pod 的 `FailedScheduling` 事件原文：
> **`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.`**

关键证据：
- `Node-Selectors`: **`aiops.e2e/nonexistent-node-label=true`** — Pod 设置了节点选择器，要求节点带有该标签，但集群中 **3 个节点均不匹配**此标签。
- 没有其他资源不足、taint 不匹配或 PVC 未绑定问题。
- 预选（Preemption）不可用，因为调度约束不匹配不会被抢占解决。

### 结论

| 输出字段 | 值 |
|---------|-----|
| **layer** | L1 |
| **layer_name** | PendingUnschedulable |
| **pod_status_keyword** | Pending |
| **pod_abnormal_type** | PendingUnschedulable |
| **status_category** | scheduling |
| **异常 Pod 列表** | `aiops-e2e/rc-pending-nodeselector` |
| **异常类型组** | PendingUnschedulable |
| **可能场景** | Pod 的 `nodeSelector` 指定了 `aiops.e2e/nonexistent-node-label=true`，但集群中没有任何节点拥有该标签，导致调度器无法放置 Pod |

### 后续审查方向（交给 evidence 节点）
- 确认集群节点是否应该包含该标签（可能是手动误配或自动化创建遗漏）
- 检查是否有预期的节点本应带有该标签但未打上
- 如果该标签不再需要，建议修复或移除 nodeSelector
   ✅ [问题定位] 完成 (24.0s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'Pod的nodeSelector指定了不存在的节点标签导致调度失败', 'probability': '高', 'reason': "FailedScheduling事件明确提示0/3 nodes didn't match Pod's node affinity/selector，且Node-Selectors为aiops.e2e/nonexistent-node-label=true，集群中无节点匹配此标签"}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}]
   reasoning=当前存在一个异常Pod rc-pending-nodeselector（命名空间aiops-e2e），状态为Pending，READY 0/1，未绑定节点。FailedScheduling事件明确显示原因：3个节点均不匹配Pod的node affinity/selector。Pod设置了Node-Selectors为aiops.e2e/nonexistent-node-label=true，但集群中无任何节点拥有该标签，导致调度器无法放置Pod。无其他资源不足或taint不匹配问题。根据五层模型，PendingUnschedulable属于L1（调度/scheduling），根因为调度约束不匹配。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.98, "reasoning": "当前存在一个异常Pod rc-pending-nodeselector（命名空间aiops-e2e），状态为Pending，READY 0/1，未绑定节点。FailedScheduling事件明确显示原因：3个节点均不匹配Pod的node affinity/selector。Pod设置了Node-Selectors为aiops.e2e/nonexistent-node-label=true，但集群中无任何节点拥有该标签，导致调度器无法放置Pod。无其他资源不足或taint不匹配问题。根据五层模型，PendingUnschedulable属于L1（调度/scheduling），根因为调度约束不匹配。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod的nodeSelector指定了不存在的节点标签导致调度失败", "probability": "高", "reason": "FailedScheduling事件明确提示0/3 nodes didn't match Pod's node affinity/selector，且Node-Selectors为aiops.e2e/nonexistent-node-label=true，集群中无节点匹配此标签"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              7m49s   <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/a312ae31bbf54d6b/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/a312ae31bbf54d6b/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/a312ae31bbf54d6b/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 98%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我直接执行既有 evidence_plan 中的关键工具，开始采集真实环境证据。

首先并行执行 e1（Pod YAML）、e2（节点标签）、e3（Pod describe）和 e4（runbook 参考）：
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAME     STATUS   ROLES           AGE    VERSION   LABELS\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpg
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  8m21s  default-scheduler  0/3 nodes are available: 3 node(s) di
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:18:44Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [证据链采集] 所有关键证据已采集完毕，以下是证据总结：

---

## 📋 证据采集结论

### 已采集证据（全部成功）

| 证据项 | 来源 | 关键发现 |
|--------|------|----------|
| **e1 - Pod YAML** | `kubectl_get_yaml` | ✅ Pod `rc-pending-nodeselector` 的 `spec.nodeSelector` 明确设为 `{"aiops.e2e/nonexistent-node-label": "true"}`，无 nodeName，phase=Pending，PodScheduled=False，reason=Unschedulable |
| **e2 - 节点标签** | `run_bash_command` | ✅ 集群共3个节点（master/node1/node2），**没有任何节点**拥有 `aiops.e2e/nonexistent-node-label` 标签，已确认标签确实不存在 |
| **e3 - Pod describe** | `kubectl_describe` | ✅ 最新 FailedScheduling 事件原文：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` — 与上游定位完全一致 |
| **e4 - Runbook 参考** | `fetch_runbook` | ✅ 匹配 runbook 中 `nodeSelector/affinity 不匹配` 分支，判定规则：FailedScheduling + `didn't match node selector` → **调度约束不匹配**，置信度：高 |

### 冲突证据 / 负向证据
- **无冲突**：Pod 仍存在于 aiops-e2e 命名空间且状态稳定为 Pending；3 个节点均 Ready（无 NotReady/Unschedulable/taint 干扰）
- 排除了资源不足（无 Insufficient 原文）、taint 不匹配（无 untolerated taint 原文）、PVC 未绑定（无 PersistentVolumeClaims 引用）等其他分支

### 根因判断
Pod `rc-pending-nodeselector` 设置了 `nodeSelector: {aiops.e2e/nonexistent-node-label: "true"}`，集群3个节点均没有该标签，调度器无法放置 Pod。属于 **nodeSelector 指定不存在的节点标签**导致的调度失败，与上游定位完全一致。
   ✅ [证据链采集] 完成 (18.1s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"核心验证: 检查 Pod rc-pending-nodeselector 的 YAML 配置，包括 nodeSelector、affinity 定义","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"验证 pod spec 中的 nodeSelector/affinity 定义，确认调度约束不匹配的根因","evidence_type":"YAML","target_scope":"Pod spec","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e2","description":"验证: 检查集群节点标签，确认无节点匹配 aiops.e2e/nonexistent-node-label=true","level":"critical","tool":"run_bash_command","command":"kubectl get nodes --show-labels","tool_args":{"command":"kubectl get nodes --show-labels"},"purpose":"验证所有节点的标签集合，确认无节点拥有 aiops.e2e/nonexistent-node-label=true 标签","evidence_type":"node_labels","target_scope":"cluster","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"验证: 通过 describe 获取最新的 FailedScheduling 事件详情","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"获取最新的 FailedScheduling 事件原文，确认调度失败原因","evidence_type":"events","target_scope":"Pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"Runbook参考: 获取已匹配 runbook 的详细内容","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","tool_args":{"runbook_name":"pod-pending-unschedulable.md"},"purpose":"参考 runbook 确认当前场景与 nodeSelector/affinity 不匹配分支一致","evidence_type":"reference","target_scope":"reference","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod PendingUnschedulable / 调度失败\n\n> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | Pending，且 Events 含 `FailedScheduling` |\n| 资源不足 | `Insufficient cpu/memory/ephemeral-storage`、`Too many pods` |\n| 调度约束 | nodeSelector/affinity 不匹配、节点 taint 未被 toleration 容忍 |\n| 存储前置条件 | `pod has unbound immediate PersistentVolumeClaims` 应切换到 pod-volume-mount-failed |\n| 节点状态 | Node NotReady/Unknown、SchedulingDisabled、Unschedulable 会导致无可用调度节点 |\n\n## 根因分流\n- 资源不足: FailedScheduling 原文含 Insufficient cpu/memory/ephemeral-storage、Too many pods。\n- hostPort 冲突: 原文含 `didn't have free ports for the requested pod ports`，说明目标节点端口已被占用。\n- Taint/Toleration 不匹配: 原文含 `had untolerated taint`，必须检查 Pod tolerations 和 Node taints。\n- nodeSelector / nodeAffinity / podAffinity 不匹配: 原文含 `didn't match Pod's node affinity/selector` 或 affinity/anti-affinity。\n- PVC 未绑定: 原文含 `unbound immediate PersistentVolumeClaims`，根因在存储绑定而不是调度资源。\n- 节点不可调度: Node Ready=False/Unknown、SchedulingDisabled、`node.kubernetes.io/not-ready` 或 `node.kubernetes.io/unreachable`。\n- 镜像、挂载、容器启动错误不会表现为 FailedScheduling；如果 Pod 已绑定 nodeName，应切换到对应 runbook。\n\n## 诊断流程\n\n### Step 1: 确认 Pod 调度失败事件\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n关注 Events 中的 `FailedScheduling` 原文。\n\n### Step 2: 检查 Pod 调度约束\n```bash\nkubectl get pod <pod-name> -n <namespace> -o yaml\n```\n关注: spec.nodeName 是否为空、nodeSelector、affinity、tolerations、topologySpreadConstraints、schedulerName、priorityClassName、resource requests、hostNetwork/hostPort。\n\n### Step 3: 检查节点状态和可调度性\n```bash\nkubectl get nodes -o wide\n```\n关注: STATUS 列是否有 NotReady/Unknown，AGE 判断是否新节点\n\n### Step 4: 检查候选节点详情\n```bash\nkubectl describe node <node-name>\n```\n重点关注:\n- `Conditions` 部分: Ready=False/Unknown 的 reason 和 message\n- `Taints` 部分: 是否有 NoSchedule/NoExecute taint\n- `Allocatable` vs `Capacity`: 资源是否耗尽\n- `Non-terminated Pods`: 节点上运行的 Pod 数量\n\n### Step 5: 检查 PVC 状态（如果 FailedScheduling 指向 PVC）\n```bash\nkubectl get pvc -n <namespace>\nkubectl describe pvc <pvc> -n <namespace>\n```\n关注: Pending、StorageClass、volumeBindingMode、ProvisioningFailed。\n\n### Step 6: 检查 Ready 条件详情\n```bash\nkubectl get node <node-name> -o jsonpath='{.status.conditions[?(@.type==\"Ready\")]}' | python3 -m json.tool\n```\n关注: status, reason, message, lastHeartbeatTime\n\n### Step 7: 检查节点事件\n```bash\nkubectl get events -A --field-selector involvedObject.kind=Node,involvedObject.name=<node-name> --sort-by='.lastTimestamp'\n```\n关注: NodeNotReady、NodeNotSchedulable、PLEG unhealthy 等事件\n\n### Step 8: 检查受影响的 Pending Pod\n```bash\nkubectl get pods -A --field-selector status.phase=Pending | head -20\n```\n\n## 判定规则\n\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| FailedScheduling + Insufficient cpu/memory | 资源不足导致 Pod Pending | 高 |\n| FailedScheduling + Too many pods | 节点 Pod 数量上限导致 Pending | 高 |\n| FailedScheduling + didn't have free ports for the requested pod ports | hostPort 端口冲突导致 Pending | 高 |\n| FailedScheduling + had untolerated taint | taint/toleration 不匹配 | 高 |\n| FailedScheduling + node(s) didn't match node selector/affinity | 调度约束不匹配 | 高 |\n| FailedScheduling + pod has unbound immediate PersistentVolumeClaims | PVC 未绑定，应切换 VolumeMountFailed/PVC 分支 | 高 |\n| 所有候选 Node NotReady/Unschedulable | 无可用调度节点 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a312ae31bbf54d6b/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a312ae31bbf54d6b/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a312ae31bbf54d6b/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAME     STATUS   ROLES           AGE    VERSION   LABELS\\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\\nnode1    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\nnode2    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a312ae31bbf54d6b/tools/002-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a312ae31bbf54d6b/tools/002-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a312ae31bbf54d6b/tools/002-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  8m21s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  2m53s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  8m21s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  2m53s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a312ae31bbf54d6b/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a312ae31bbf54d6b/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a312ae31bbf54d6b/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a312ae31bbf54d6b/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a312ae31bbf54d6b/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a312ae31bbf54d6b/tools/004-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"所有关键证据已采集完毕，以下是证据总结：\n\n---\n\n## 📋 证据采集结论\n\n### 已采集证据（全部成功）\n\n| 证据项 | 来源 | 关键发现 |\n|--------|------|----------|\n| **e1 - Pod YAML** | `kubectl_get_yaml` | ✅ Pod `rc-pending-nodeselector` 的 `spec.nodeSelector` 明确设为 `{\"aiops.e2e/nonexistent-node-label\": \"true\"}`，无 nodeName，phase=Pending，PodScheduled=False，reason=Unschedulable |\n| **e2 - 节点标签** | `run_bash_command` | ✅ 集群共3个节点（master/node1/node2），**没有任何节点**拥有 `aiops.e2e/nonexistent-node-label` 标签，已确认标签确实不存在 |\n| **e3 - Pod describe** | `kubectl_describe` | ✅ 最新 FailedScheduling 事件原文：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` — 与上游定位完全一致 |\n| **e4 - Runbook 参考** | `fetch_runbook` | ✅ 匹配 runbook 中 `nodeSelector/affinity 不匹配` 分支，判定规则：FailedScheduling + `didn't match node selector` → **调度约束不匹配**，置信度：高 |\n\n### 冲突证据 / 负向证据\n- **无冲突**：Pod 仍存在于 aiops-e2e 命名空间且状态稳定为 Pending；3 个节点均 Ready（无 NotReady/Unschedulable/taint 干扰）\n- 排除了资源不足（无 Insufficient 原文）、taint 不匹配（无 untolerated taint 原文）、PVC 未绑定（无 PersistentVolumeClaims 引用）等其他分支\n\n### 根因判断\nPod `rc-pending-nodeselector` 设置了 `nodeSelector: {aiops.e2e/nonexistent-node-label: \"true\"}`，集群3个节点均没有该标签，调度器无法放置 Pod。属于 **nodeSelector 指定不存在的节点标签**导致的调度失败，与上游定位完全一致。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 6 个，匹配计划 4 个，未规划证据 2 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":4,"unplanned_tool_count":2,"evidence_inventory":[{"id":"e1","description":"核心验证: 检查 Pod rc-pending-nodeselector 的 YAML 配置，包括 nodeSelector、affinity 定义","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"验证 pod spec 中的 nodeSelector/affinity 定义，确认调度约束不匹配的根因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证: 检查集群节点标签，确认无节点匹配 aiops.e2e/nonexistent-node-label=true","level":"critical","tool":"run_bash_command","command":"kubectl get nodes --show-labels","purpose":"验证所有节点的标签集合，确认无节点拥有 aiops.e2e/nonexistent-node-label=true 标签","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"验证: 通过 describe 获取最新的 FailedScheduling 事件详情","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"获取最新的 FailedScheduling 事件原文，确认调度失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"Runbook参考: 获取已匹配 runbook 的详细内容","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","purpose":"参考 runbook 确认当前场景与 nodeSelector/affinity 不匹配分支一致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 核心验证: 检查 Pod rc-pending-nodeselector 的 YAML 配... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | run_bash_command | 验证: 检查集群节点标签，确认无节点匹配 aiops.e2e/nonexistent-no... | `kubectl get nodes --show-labels` |
   | e3 | critical | ✅ | kubectl_describe | 验证: 通过 describe 获取最新的 FailedScheduling 事件详情 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e4 | reference | ✅ | fetch_runbook | Runbook参考: 获取已匹配 runbook 的详细内容 | `fetch_runbook pod-pending-unschedulable.md` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (24.5s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector（命名空间 aiops-e2e）处于 Pending 状态的根本原因是 nodeSelector 指定了集群中不存在的标签 aiops.e2e/nonexistent-node-label=true。kubectl_get_yaml 确认 nodeSelector 配置；节点标签检查（e2）确认 3 个节点（master、node1、node2）均无此标签；kubectl_describe 中 FailedScheduling 事件原文为"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"，排除了资源不足（无 Insufficient 原文）、taint 不匹配（无 untolerated taint 原文）、PVC 未绑定（无 PVC 引用）等其他分支。集群其余 59 个 Running Pod 均正常，问题仅局限于该 Pod 的调度配置错误。
   confidence=98%
   causal_chain={"root_cause": "Pod rc-pending-nodeselector 的 spec.nodeSelector 指定了集群中不存在的标签 aiops.e2e/nonexistent-node-label=true，导致调度器无法找到满足条件的节点", "propagation": "Pod 创建后，调度器（default-scheduler）遍历全部 3 个节点（master/node1/node2），检查节点标签与 Pod 的 nodeSelector 匹配情况 → 均不匹配 → 调度器报告 FailedScheduling → Pod 持续处于 Pending 状态，无法进展到绑定阶段", "direct_cause": "nodeSelector 约束 aiops.e2e/nonexistent-node-label=true 无法被任何节点满足，所有 3 个节点都不具备该标签", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中状态为 Pending（0/1），无绑定的节点，READY 0/1，Events 持续报 FailedScheduling"}
   rca_analysis={"phenomenon": "命名空间 aiops-e2e 中的 Pod rc-pending-nodeselector 处于 Pending 状态（READY 0/1），未绑定节点（nodeName=None），持续约 8 分钟。集群共 65 个 Pod，仅此 1 个异常。", "evidence_inventory": [{"id": "e1", "source": "kubectl_get_yaml", "content": "Pod rc-pending-nodeselector 的 nodeSelector 设为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}，phase=Pending，nodeName=None，PodScheduled=False，reason=Unschedulable", "reliability": "高"}, {"id": "e2", "source": "run_bash_command（节点标签查询）", "content": "集群 3 个节点（master/node1/node2）均无 aiops.e2e/nonexistent-node-label 标签，所有节点 Ready", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe", "content": "FailedScheduling 事件原文：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling", "reliability": "高"}, {"id": "e4", "source": "fetch_runbook（pod-pending-unschedulable.md）", "content": "Runbook 判定规则：FailedScheduling + node selector 不匹配 → 调度约束不匹配，置信度高", "reliability": "高"}, {"id": "layer_1", "source": "上游已验证：kubectl_get_by_kind_in_cluster", "content": "集群 Pod 总数 65，Running=59，Pending=1，仅 rc-pending-nodeselector 异常", "reliability": "高"}, {"id": "layer_2", "source": "上游已验证：kubectl_describe", "content": "两次 FailedScheduling 事件（7m51s 和 2m22s），原因一致：affinity/selector 不匹配", "reliability": "高"}, {"id": "layer_3", "source": "上游已验证：kubectl_get_by_name", "content": "Pod 当前状态：0/1 Pending，AGE 7m52s，无 IP 无 Node", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}, nodeName: None, PodScheduled: False, reason: Unschedulable", "interpretation": "Pod 明确设置了 nodeSelector，要求节点包含标签 aiops.e2e/nonexistent-node-label=true，且未被调度到任何节点（nodeName=None），调度条件为 False"}, {"evidence_id": "e2", "raw_data": "master: LABELS='...aiops.e2e/...' 无匹配; node1/node2 同样无 aiops.e2e/nonexistent-node-label", "interpretation": "集群所有 3 个节点的标签列表中均不包含 aiops.e2e/nonexistent-node-label 标签，Pod 的调度约束无法被任何节点满足"}, {"evidence_id": "e3", "raw_data": "Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "interpretation": "调度器明确报告所有 3 个节点都无法匹配 Pod 的 node affinity/selector，且 preemption 无法帮助调度，排除了资源抢占的可能性"}, {"evidence_id": "e4", "raw_data": "判定规则：FailedScheduling + node(s) didn't match node selector/affinity → 调度约束不匹配，置信度高", "interpretation": "当前证据完全匹配 runbook 中 nodeSelector/affinity 不匹配的场景分支，排除了资源不足、taint、PVC 等其他分支"}, {"evidence_id": "layer_1", "raw_data": "rows=65, abnormal=1, status_counts={'Running': 59, 'Pending': 1}", "interpretation": "集群中仅此一个异常 Pod，其余 59 个 Pod 正常运行，说明问题局限于该 Pod 的调度配置，非集群整体故障"}, {"evidence_id": "layer_2", "raw_data": "FailedScheduling 事件时间戳：7m51s 和 2m22s，持续重试调度失败", "interpretation": "调度器在约 5 分钟内持续重试调度均失败，且失败原因完全一致，非瞬时性问题"}], "causal_chain": {"root_cause": "Pod rc-pending-nodeselector 的 spec.nodeSelector 指定了集群中不存在的标签 aiops.e2e/nonexistent-node-label=true，导致调度器无法找到满足条件的节点", "propagation": "Pod 创建后，调度器（default-scheduler）遍历全部 3 个节点（master/node1/node2），检查节点标签与 Pod 的 nodeSelector 匹配情况 → 均不匹配 → 调度器报告 FailedScheduling → Pod 持续处于 Pending 状态，无法进展到绑定阶段", "direct_cause": "nodeSelector 约束 aiops.e2e/nonexistent-node-label=true 无法被任何节点满足，所有 3 个节点都不具备该标签", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中状态为 Pending（0/1），无绑定的节点，READY 0/1，Events 持续报 FailedScheduling"}, "root_cause": "Pod rc-pending-nodeselector（命名空间 aiops-e2e）处于 Pending 状态的根本原因是 nodeSelector 指定了集群中不存在的标签 aiops.e2e/nonexistent-node-label=true。kubectl_get_yaml 确认 nodeSelector 配置；节点标签检查（e2）确认 3 个节点（master、node1、node2）均无此标签；kubectl_describe 中 FailedScheduling 事件原文为\"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"，排除了资源不足（无 Insufficient 原文）、taint 不匹配（无 untolerated taint 原文）、PVC 未绑定（无 PVC 引用）等其他分支。集群其余 59 个 Running Pod 均正常，问题仅局限于该 Pod 的调度配置错误。", "root_cause_summary": "Pod rc-pending-nodeselector（命名空间 aiops-e2e）处于 Pending 状态的根本原因是 nodeSelector 指定了集群中不存在的标签 aiops.e2e/nonexistent-node-label=true。kubectl_get_yaml 确认 nodeSelector 配置；节点标签检查（e2）确认 3 个节点（master、node1、node2）均无此标签；kubectl_describe 中 FailedScheduling 事件原文为\"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"，排除了资源不足（无 Insufficient 原文）、taint 不匹配（无 untolerated taint 原文）、PVC 未绑定（无 PVC 引用）等其他分支。集群其余 59 个 Running Pod 均正常，问题仅局限于该 Pod 的调度配置错误。", "confidence": 0.98, "confidence_reason": "直接证据完整且因果链清晰：(1) Pod YAML 明确显示 nodeSelector 配置；(2) 节点标签查询确认 3 个节点均无匹配标签；(3) FailedScheduling 事件原文与 nodeSelector 不匹配完全一致；(4) 已排除资源不足、taint、PVC 等其他分支。所有证据高度一致，置信度 0.98。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "节点资源不足（cpu/memory）", "probability": "low", "reason": "FailedScheduling 事件原文为'didn't match Pod's node affinity/selector'，无'Insufficient cpu/memory'或'Insufficient ephemeral-storage'原文，且所有 3 个节点状态均为 Ready"}, {"cause": "节点 taint 未被 toleration 容忍", "probability": "low", "reason": "FailedScheduling 事件中无'had untolerated taint'原文，Pod 已配置了 NotReady/NoExecute toleration"}, {"cause": "PVC 未绑定或卷依赖未满足", "probability": "low", "reason": "Pod YAML 显示只有 kube-api-access-w74s5 自动挂载卷，无 PVC 引用，FailedScheduling 事件无'unbound immediate PersistentVolumeClaims'原文"}, {"cause": "节点不可调度（NotReady/Unschedulable）", "probability": "low", "reason": "节点标签查询显示 master/node1/node2 状态均为 Ready，无 SchedulingDisabled"}], "limitations": "无需额外证据，当前证据链已完整闭环。未采集节点资源 allocatable/capacity 数据，但由于 FailedScheduling 事件已明确指向 affinity/selector 不匹配而非资源不足，不影响根因判断。", "llm_raw_analysis": "L1 根因分析完成。Pod rc-pending-nodeselector（aiops-e2e）异常组唯一，状态 Pending/PendingUnschedulable。所有证据（Pod YAML 的 nodeSelector、节点标签列表、FailedScheduling 事件、runbook 匹配规则）一致指向 nodeSelector 指定不存在的标签这一根因。非主异常组：无其他异常组。已最小验证仅此 1 个异常 Pod。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector（命名空间 aiops-e2e）处于 Pending 状态的根本原因是 nodeSelector 指定了集群中不存在的标签 aiops.e2e/nonexistent-node-label=true。kubectl_get_yaml 确认 nod...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod rc-pending-nodeselector 的 spec.nodeSelector 指定了集群中不存在的标签 aiops.e2e/nonexistent-node-label=true，导致调度器无法找到满足条件的节点
     传导机制: Pod 创建后，调度器（default-scheduler）遍历全部 3 个节点（master/node1/node2），检查节点标签与 Pod 的 nodeSelector 匹配情况 → 均不匹配 → 调度器报告 FailedScheduling → Pod 持续处于 Pending 状态，无法进展到绑定阶段
     最终表现: Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中状态为 Pending（0/1），无绑定的节点，READY 0/1，Events 持续报 FailedScheduling


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (23.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5251 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 29.8s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，这是根据您的需求生成的详尽诊断报告。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **当前集群状态** | 集群整体运行正常，59/65 个 Pod 处于 Running 状态。发现 1 个异常 Pod 待处理。 |
| **异常 Pod** | `rc-pending-nodeselector` (命名空间: `aiops-e2e`) |
| **Pod异常状态** | **Pending** （具体类型：PendingUnschedulable） |
| **兼容归因层** | L1 - 调度层 |
| **问题分类** | 调度约束不匹配 (nodeSelector/Affinity) |
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
| 状态 | **Pending** (READY 0/1) |
| 错误信息 | `FailedScheduling`: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` |
| Pod 节点选择器 | `aiops.e2e/nonexistent-node-label=true` |

---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod YAML配置 | `kubectl_get_yaml` | `nodeSelector: {aiops.e2e/nonexistent-node-label: "true"}` | Pod 配置了一个特定的节点标签选择器。 |
| 2 | 节点标签状态 | `run_bash_command` (获取节点标签) | 3个节点 (`master`, `node1`, `node2`) 的标签列表**均不包含** `aiops.e2e/nonexistent-node-label=true`。 | 集群中**没有任何节点**拥有 Pod 所需的标签。 |
| 3 | Pod 事件与状态 | `kubectl_describe` | **事件**: `Warning FailedScheduling 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.`<br>**状态**: `Status: Pending`<br>**节点**: `Node: <none>` | 调度器明确报告 Pod 无法匹配任何节点的 affinity/selector，导致 Pod 无法被调度到任何节点上。 |

### 证据关联分析
- **证据 #1 + 证据 #2 + 证据 #3 印证**：
  - Pod 指定了一个特定的节点标签 `aiops.e2e/nonexistent-node-label=true`。
  - 集群中所有 3 个节点均无此标签。
  - 调度器因此判断无节点可用，并产生 `FailedScheduling` 事件。

### 缺失证据
无。证据链完整，足以定位根因。

---
## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                │
│ Pod (rc-pending-nodeselector) 的 spec.nodeSelector 配置了集群中          │
│ 不存在的标签：aiops.e2e/nonexistent-node-label=true                     │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                │
│ 调度器(default-scheduler) 遍历全部3个节点 (master, node1, node2)        │
│ 检查节点标签与 Pod 的 nodeSelector 匹配情况 → 均不匹配                 │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                │
│ 调度器报告 FailedScheduling，提示所有节点都不满足 Pod 的                │
│ node affinity/selector。                                               │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                            │
│ Pod (rc-pending-nodeselector) 持续处于 Pending 状态，无法被调度到       │
│ 任何节点，无法提供服务。                                                │
└─────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (Pod YAML 配置) 和证据 #2 (节点标签列表)，问题的根本原因是 **Pod `rc-pending-nodeselector` 的 `nodeSelector` 配置了一个集群中不存在的标签 `aiops.e2e/nonexistent-node-label=true`**。这导致调度器无法找到满足条件的节点，Pod 无法运行。

**置信度**：高 (98%)
- ✅ `kubectl_describe` 提供的事件 `FailedScheduling` 直接印证了调度冲突。
- ✅ `kubectl_get_yaml` 明确显示了 `nodeSelector` 的具体值。
- ✅ 节点标签检查（`run_bash_command`）确认集群中不存在该标签。
- ✅ 已排除资源不足、节点 taint、PVC 未绑定等其它可能的原因。

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）
**1. [优先] 修改 Pod/Deployment 配置，删除或更正不存在的节点标签选择器。**
根据您的部署方式，选择合适的操作：

- **如果 Pod 由 Deployment 创建：**
  ```bash
  # 删除或修改 nodeSelector。以下命令移除了 nodeSelector 配置。
  kubectl patch deployment <deployment-name> -n aiops-e2e --type json \
    -p='[{"op": "remove", "path": "/spec/template/spec/nodeSelector"}]'
  ```
  *请将 `<deployment-name>` 替换为创建该 Pod 的 Deployment 名称（可通过 `kubectl get deployment -n aiops-e2e` 查看）。*
  *此命令会触发 Deployment 滚动更新，创建新的可用 Pod，旧的 Pending Pod 会被删除。*

- **如果 Pod 是直接创建的（Standalone Pod）：**
  ```bash
  # 1. 删除当前异常的、无法调度的 Pod
  kubectl delete pod rc-pending-nodeselector -n aiops-e2e
  
  # 2. 重新创建 Pod 时，确保 YAML 中不包含不存在的 nodeSelector
  ```

**2. [可选] 如果您确实希望 Pod 在特定节点上运行，请为节点打上正确的标签。**
  ```bash
  # 例如，如果希望 Pod 运行在 node1 上
  kubectl label node node1 aiops.e2e/nonexistent-node-label=true
  ```
  *此操作完成后，Pod 无需重启即可自动调度到 `node1` 上。*

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 被删除或状态改变 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | Pod 不存在，或 STATUS 变为 `Running`/`Terminating` |
| 2. 确认新 Pod 正常运行 | `kubectl get pod -n aiops-e2e -l app=rc-pending-nodeselector` | 新的 Pod  STATUS 为 `Running`，READY 为 `1/1` |
| 3. 检查集群整体状态 | `kubectl get pods -A --field-selector=status.phase!=Running` | 输出应不包含 `aiops-e2e` 命名空间下的异常 Pod (除合法 `Succeeded` 或 `Completed` Pod 外) |

---
## ⚠️ 注意事项
- **问题隔离**：此问题**仅影响** `aiops-e2e` 命名空间下的 `rc-pending-nodeselector` Pod，集群中其余 59 个 Pod 运行正常，对所有其他应用和命名空间没有影响。
- **避免误操作**：在修改 Deployment YAML 时，请确保只修改 `nodeSelector` 部分，不要误删其他重要配置。使用 `kubectl edit deployment <deployment-name> -n aiops-e2e` 命令手动编辑 YAML 文件也是一个安全的选择。
- **未来预防**：在创建 Pod/Deployment 时，仔细检查 `nodeSelector` 或 `affinity` 配置，确保引用的标签确实存在于集群节点上。

---

## 📊 性能统计

├─ 总耗时: 1.5m
├─ 问题定位: 24.0s (27%) ✅
├─ 证据链采集: 18.1s (20%) ✅
├─ 根因分析: 24.5s (27%) ✅
├─ 汇总总结: 23.2s (26%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 8 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 8 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
