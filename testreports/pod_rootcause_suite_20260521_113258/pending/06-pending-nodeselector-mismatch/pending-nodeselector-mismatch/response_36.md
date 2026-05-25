======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 1bda535a54744cc3]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来先做全局 Pod 状态扫描，看看当前集群的所有 Pod 状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 找到了一个异常 Pod。让我进一步查看详细信息。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          27m   <none>   <none>   
   💭 [问题定位] Pod 处于 Pending 状态且未绑定节点。根据标签 `pod_abnormal_type=PendingUnschedulable`，这很可能是一个调度问题。让我查看详情确认。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  27m                default-scheduler  0/3 nodes are available: 
   💭 [问题定位] 已经找到根因。让我获取对应的 runbook 作为参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在我已经掌握了所有必要信息。以下是分析结果：

---

## 集群 Pod 异常定位分析

### 全局扫描结果
集群共有 **65 个 Pod**，分布在多个命名空间中：
- **Running（正常）**：59 个
- **Pending（异常）**：1 个

### 异常 Pod 详情

| Pod | 命名空间 | 状态 | 异常类型 | 节点 |
|-----|---------|------|---------|------|
| `rc-pending-nodeselector` | aiops-e2e | Pending | PendingUnschedulable | 未绑定 |

### 根因分析

**Pod：`rc-pending-nodeselector`**（aiops-e2e 命名空间）

- **当前状态**：`Pending`，未绑定节点（nodeName 为空）
- **调度事件**：`FailedScheduling` — `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.`
- **根因**：Pod 设置了 `nodeSelector`：`aiops.e2e/nonexistent-node-label=true`，集群中 3 个节点**均没有该标签**，导致没有节点可被调度。
- **镜像**：`busybox:1.36`（正常可拉取）

### 输出结构

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **layer_name** | PendingUnschedulable — nodeSelector 不匹配 |
| **pod_status_keyword** | Pending |
| **pod_abnormal_type** | PendingUnschedulable |
| **status_category** | scheduling |
| **confidence** | 高 |
| **异常 Pod 数量** | 1 |
| **异常组** | PendingUnschedulable × 1 |

**可能场景**：这是一个 E2E 测试场景 Pod，其 `nodeSelector` 使用了不存在的标签 `aiops.e2e/nonexistent-node-label=true`，导致调度器无法找到匹配节点。所有 3 个节点均因不满足 nodeSelector 条件而被排除了。

**建议修复方向**：删除该 `nodeSelector` 约束，或为某个目标节点添加该标签。
   ✅ [问题定位] 完成 (21.7s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector 标签不匹配导致调度失败', 'probability': '高', 'reason': 'Pod 设置了 nodeSelector aiops.e2e/nonexistent-node-label=true，集群中 3 个节点均无此标签，FailedScheduling 事件明确指示此原因'}]
   entities=[{"type": "pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}]
   reasoning=集群中存在当前仍异常的 Pod rc-pending-nodeselector (aiops-e2e)，状态为 Pending，异常类型为 PendingUnschedulable。FailedScheduling 事件明确显示 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector，根因为 nodeSelector (aiops.e2e/nonexistent-node-label=true) 在集群 3 个节点上均无匹配标签。属于调度约束不匹配，归入 L1 (scheduling)。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable — nodeSelector 不匹配", "confidence": 0.95, "reasoning": "集群中存在当前仍异常的 Pod rc-pending-nodeselector (aiops-e2e)，状态为 Pending，异常类型为 PendingUnschedulable。FailedScheduling 事件明确显示 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector，根因为 nodeSelector (aiops.e2e/nonexistent-node-label=true) 在集群 3 个节点上均无匹配标签。属于调度约束不匹配，归入 L1 (scheduling)。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "nodeSelector 标签不匹配导致调度失败", "probability": "高", "reason": "Pod 设置了 nodeSelector aiops.e2e/nonexistent-node-label=true，集群中 3 个节点均无此标签，FailedScheduling 事件明确指示此原因"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              27m     <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/1bda535a54744cc3/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/1bda535a54744cc3/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/1bda535a54744cc3/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我将按照既有 evidence_plan 直接执行工具调用。先并行执行 ev-01、ev-02、ev-03 和 ev-05（runbook 已在上游获取过，但仍按计划补充确认）。
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          27m   <none>   <none>   
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  27m                default-scheduler  0/3 nodes are available: 
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:18:44Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [证据链采集] Pod 确认存在且 Pending，事件明确指向 nodeSelector 不匹配。现在执行 ev-04：检查节点标签，验证是否匹配 `aiops.e2e/nonexistent-node-label=true`。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nmaster   Ready    co
   💭 [证据链采集] 所有工具调用完成。以下是证据采集结论：

---

## ✅ 证据采集结论

### 已采集证据

| # | 计划项 | 证据结果 |
|---|--------|----------|
| **ev-01** | Pod 实时状态确认 | ✅ **Pod rc-pending-nodeselector** 仍存在于 `aiops-e2e` 命名空间，状态 **Pending**，无 Node 绑定，已运行 27m |
| **ev-02** | FailedScheduling 事件确认 | ✅ **Warning FailedScheduling** 明确指示：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`，且 `Preemption is not helpful for scheduling` |
| **ev-03** | nodeSelector YAML 确认 | ✅ YAML 中 `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}` 已确认。标签键名完全匹配 `aiops.e2e/nonexistent-node-label`，值为 `true` |
| **ev-04** | 节点标签验证 | ✅ 集群有 **3 个节点**（master/node1/node2），全部 **Ready**，**均不包含** `aiops.e2e/nonexistent-node-label` 标签，证实该标签在集群中完全不存在 |
| **ev-05** | Runbook 匹配 | ✅ Runbook `pod-pending-unschedulable.md` 判定规则确认：`FailedScheduling + node(s) didn't match node selector/affinity → 调度约束不匹配（高置信度）` 完全命中 |

### 根因结论
**Pod `rc-pending-nodeselector` Pending 的根因为 nodeSelector 标签不匹配。** Pod 的 nodeSelector 要求 `aiops.e2e/nonexistent-node-label=true`，但集群 3 个节点（master/node1/node2）上均不存在此标签，调度器无法放置 Pod。QoS Class 为 BestEffort（无资源请求），因此非资源不足问题。

### 修复建议（仅建议，不执行）
1. **给目标节点打标签**：`kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`
2. **或修改 Pod nodeSelector**：将 `spec.nodeSelector` 改为集群中已存在的标签键值对
3. **或删除该 Pod**（如果是测试残留）：`kubectl delete pod rc-pending-nodeselector -n aiops-e2e`
   ✅ [证据链采集] 完成 (24.6s)
   📤 → 下游数据: evidence_items=7/8
   evidence_analysis={"evidence_plan":[{"id":"ev-01","description":"验证 Pod rc-pending-nodeselector 当前是否仍存在于 aiops-e2e namespace 及最新 status","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o wide","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"确认 Pod 仍存在且处于 Pending 状态，验证 current_abnormal_summary 的实时准确性","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-02","description":"通过 kubectl describe 获取 Pod 最新详细事件（FailedScheduling 确认调度约束不匹配细节）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"确认 FailedScheduling 事件细节，验证 nodeSelector 标签不匹配的根因","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-03","description":"查看 Pod 完整 YAML spec 中的 nodeSelector 配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e","format":"yaml"},"purpose":"确认 nodeSelector 具体键值对，验证 aiops.e2e/nonexistent-node-label=true 是否确实存在","evidence_type":"","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"ev-04","description":"查看集群节点列表及标签，验证哪个节点有匹配 nodeSelector 的标签","level":"important","tool":"run_bash_command","command":"kubectl get nodes -o wide --show-labels","tool_args":{"command":"kubectl get nodes -o wide --show-labels"},"purpose":"验证所有节点是否存在 nodeSelector 要求的标签","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-05","description":"根据已匹配 runbook 引用，确认场景分类（调度约束不匹配）","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","tool_args":{"runbook_name":"pod-pending-unschedulable.md"},"purpose":"引用已匹配 runbook 确认调度约束不匹配的判定分支","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod PendingUnschedulable / 调度失败\n\n> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | Pending，且 Events 含 `FailedScheduling` |\n| 资源不足 | `Insufficient cpu/memory/ephemeral-storage`、`Too many pods` |\n| 调度约束 | nodeSelector/affinity 不匹配、节点 taint 未被 toleration 容忍 |\n| 存储前置条件 | `pod has unbound immediate PersistentVolumeClaims` 应切换到 pod-volume-mount-failed |\n| 节点状态 | Node NotReady/Unknown、SchedulingDisabled、Unschedulable 会导致无可用调度节点 |\n\n## 根因分流\n- 资源不足: FailedScheduling 原文含 Insufficient cpu/memory/ephemeral-storage、Too many pods。\n- hostPort 冲突: 原文含 `didn't have free ports for the requested pod ports`，说明目标节点端口已被占用。\n- Taint/Toleration 不匹配: 原文含 `had untolerated taint`，必须检查 Pod tolerations 和 Node taints。\n- nodeSelector / nodeAffinity / podAffinity 不匹配: 原文含 `didn't match Pod's node affinity/selector` 或 affinity/anti-affinity。\n- PVC 未绑定: 原文含 `unbound immediate PersistentVolumeClaims`，根因在存储绑定而不是调度资源。\n- 节点不可调度: Node Ready=False/Unknown、SchedulingDisabled、`node.kubernetes.io/not-ready` 或 `node.kubernetes.io/unreachable`。\n- 镜像、挂载、容器启动错误不会表现为 FailedScheduling；如果 Pod 已绑定 nodeName，应切换到对应 runbook。\n\n## 诊断流程\n\n### Step 1: 确认 Pod 调度失败事件\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n关注 Events 中的 `FailedScheduling` 原文。\n\n### Step 2: 检查 Pod 调度约束\n```bash\nkubectl get pod <pod-name> -n <namespace> -o yaml\n```\n关注: spec.nodeName 是否为空、nodeSelector、affinity、tolerations、topologySpreadConstraints、schedulerName、priorityClassName、resource requests、hostNetwork/hostPort。\n\n### Step 3: 检查节点状态和可调度性\n```bash\nkubectl get nodes -o wide\n```\n关注: STATUS 列是否有 NotReady/Unknown，AGE 判断是否新节点\n\n### Step 4: 检查候选节点详情\n```bash\nkubectl describe node <node-name>\n```\n重点关注:\n- `Conditions` 部分: Ready=False/Unknown 的 reason 和 message\n- `Taints` 部分: 是否有 NoSchedule/NoExecute taint\n- `Allocatable` vs `Capacity`: 资源是否耗尽\n- `Non-terminated Pods`: 节点上运行的 Pod 数量\n\n### Step 5: 检查 PVC 状态（如果 FailedScheduling 指向 PVC）\n```bash\nkubectl get pvc -n <namespace>\nkubectl describe pvc <pvc> -n <namespace>\n```\n关注: Pending、StorageClass、volumeBindingMode、ProvisioningFailed。\n\n### Step 6: 检查 Ready 条件详情\n```bash\nkubectl get node <node-name> -o jsonpath='{.status.conditions[?(@.type==\"Ready\")]}' | python3 -m json.tool\n```\n关注: status, reason, message, lastHeartbeatTime\n\n### Step 7: 检查节点事件\n```bash\nkubectl get events -A --field-selector involvedObject.kind=Node,involvedObject.name=<node-name> --sort-by='.lastTimestamp'\n```\n关注: NodeNotReady、NodeNotSchedulable、PLEG unhealthy 等事件\n\n### Step 8: 检查受影响的 Pending Pod\n```bash\nkubectl get pods -A --field-selector status.phase=Pending | head -20\n```\n\n## 判定规则\n\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| FailedScheduling + Insufficient cpu/memory | 资源不足导致 Pod Pending | 高 |\n| FailedScheduling + Too many pods | 节点 Pod 数量上限导致 Pending | 高 |\n| FailedScheduling + didn't have free ports for the requested pod ports | hostPort 端口冲突导致 Pending | 高 |\n| FailedScheduling + had untolerated taint | taint/toleration 不匹配 | 高 |\n| FailedScheduling + node(s) didn't match node selector/affinity | 调度约束不匹配 | 高 |\n| FailedScheduling + pod has unbound immediate PersistentVolumeClaims | PVC 未绑定，应切换 VolumeMountFailed/PVC 分支 | 高 |\n| 所有候选 Node NotReady/Unschedulable | 无可用调度节点 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1bda535a54744cc3/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1bda535a54744cc3/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1bda535a54744cc3/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS\nrc-pending-nodeselector   0/1     Pending   0          27m   <none>   <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1bda535a54744cc3/tools/002-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1bda535a54744cc3/tools/002-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1bda535a54744cc3/tools/002-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  27m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  17m (x2 over 22m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  27m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  17m (x2 over 22m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1bda535a54744cc3/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1bda535a54744cc3/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1bda535a54744cc3/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1bda535a54744cc3/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1bda535a54744cc3/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1bda535a54744cc3/tools/004-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\\nmaster   Ready    control-plane   238d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\\nnode1    Ready    <none>          238d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\nnode2    Ready    <none>          238d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1bda535a54744cc3/tools/005-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1bda535a54744cc3/tools/005-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1bda535a54744cc3/tools/005-evidence-run_bash_command.summary.txt"}],"llm_analysis":"所有工具调用完成。以下是证据采集结论：\n\n---\n\n## ✅ 证据采集结论\n\n### 已采集证据\n\n| # | 计划项 | 证据结果 |\n|---|--------|----------|\n| **ev-01** | Pod 实时状态确认 | ✅ **Pod rc-pending-nodeselector** 仍存在于 `aiops-e2e` 命名空间，状态 **Pending**，无 Node 绑定，已运行 27m |\n| **ev-02** | FailedScheduling 事件确认 | ✅ **Warning FailedScheduling** 明确指示：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`，且 `Preemption is not helpful for scheduling` |\n| **ev-03** | nodeSelector YAML 确认 | ✅ YAML 中 `nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}` 已确认。标签键名完全匹配 `aiops.e2e/nonexistent-node-label`，值为 `true` |\n| **ev-04** | 节点标签验证 | ✅ 集群有 **3 个节点**（master/node1/node2），全部 **Ready**，**均不包含** `aiops.e2e/nonexistent-node-label` 标签，证实该标签在集群中完全不存在 |\n| **ev-05** | Runbook 匹配 | ✅ Runbook `pod-pending-unschedulable.md` 判定规则确认：`FailedScheduling + node(s) didn't match node selector/affinity → 调度约束不匹配（高置信度）` 完全命中 |\n\n### 根因结论\n**Pod `rc-pending-nodeselector` Pending 的根因为 nodeSelector 标签不匹配。** Pod 的 nodeSelector 要求 `aiops.e2e/nonexistent-node-label=true`，但集群 3 个节点（master/node1/node2）上均不存在此标签，调度器无法放置 Pod。QoS Class 为 BestEffort（无资源请求），因此非资源不足问题。\n\n### 修复建议（仅建议，不执行）\n1. **给目标节点打标签**：`kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`\n2. **或修改 Pod nodeSelector**：将 `spec.nodeSelector` 改为集群中已存在的标签键值对\n3. **或删除该 Pod**（如果是测试残留）：`kubectl delete pod rc-pending-nodeselector -n aiops-e2e`","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 6/7 项，完整度 86%；实际执行工具 7 个，匹配计划 4 个，未规划证据 3 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":7,"environment_evidence_collected":6,"environment_evidence_completeness":0.8571428571428571,"executed_tool_count":7,"matched_tool_count":4,"unplanned_tool_count":3,"evidence_inventory":[{"id":"ev-01","description":"验证 Pod rc-pending-nodeselector 当前是否仍存在于 aiops-e2e namespace 及最新 status","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o wide","purpose":"确认 Pod 仍存在且处于 Pending 状态，验证 current_abnormal_summary 的实时准确性","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-02","description":"通过 kubectl describe 获取 Pod 最新详细事件（FailedScheduling 确认调度约束不匹配细节）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"确认 FailedScheduling 事件细节，验证 nodeSelector 标签不匹配的根因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-03","description":"查看 Pod 完整 YAML spec 中的 nodeSelector 配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"确认 nodeSelector 具体键值对，验证 aiops.e2e/nonexistent-node-label=true 是否确实存在","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-04","description":"查看集群节点列表及标签，验证哪个节点有匹配 nodeSelector 的标签","level":"important","tool":"run_bash_command","command":"kubectl get nodes -o wide --show-labels","purpose":"验证所有节点是否存在 nodeSelector 要求的标签","collected":false,"source":"planned","outcome":"unknown"},{"id":"ev-05","description":"根据已匹配 runbook 引用，确认场景分类（调度约束不匹配）","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","purpose":"引用已匹配 runbook 确认调度约束不匹配的判定分支","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["ev-04(查看集群节点列表及标签，验证哪个节点有匹配 nodeSelector 的标签): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 86%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | ev-01 | critical | ✅ | kubectl_get_by_name | 验证 Pod rc-pending-nodeselector 当前是否仍存在于 aiops... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o wide` |
   | ev-02 | critical | ✅ | kubectl_describe | 通过 kubectl describe 获取 Pod 最新详细事件（FailedSched... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | ev-03 | critical | ✅ | kubectl_get_yaml | 查看 Pod 完整 YAML spec 中的 nodeSelector 配置 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | ev-04 | important | ❌ | run_bash_command | 查看集群节点列表及标签，验证哪个节点有匹配 nodeSelector 的标签 | `kubectl get nodes -o wide --show-labels` |
   | ev-05 | reference | ✅ | fetch_runbook | 根据已匹配 runbook 引用，确认场景分类（调度约束不匹配） | `fetch_runbook pod-pending-unschedulable.md` |

   ⚠️ 未采集原因:
   - ev-04(查看集群节点列表及标签，验证哪个节点有匹配 nodeSelector 的标签): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (22.2s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector (aiops-e2e 命名空间) 处于 Pending 状态 27 分钟，根因为 nodeSelector 标签不匹配。YAML spec 中 nodeSelector 配置为 {"aiops.e2e/nonexistent-node-label": "true"}，但集群 3 个节点 (master/node1/node2) 均无此标签，FailedScheduling 事件明确报告 "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"。Pod QoS Class 为 BestEffort（无资源请求），排除了资源不足场景。Runbook pod-pending-unschedulable.md 判定规则完全命中，置信度高。
   confidence=95%
   causal_chain={"root_cause": "Pod rc-pending-nodeselector 的 spec.nodeSelector 配置了集群中不存在的标签 aiops.e2e/nonexistent-node-label=true，导致调度器无法找到任何可调度节点", "propagation": "Pod 创建后 scheduler 遍历集群 3 个节点(master/node1/node2)检查 nodeSelector 约束 → 所有节点均不匹配 → scheduler 标记 Unschedulable → 重试调度仍失败 → Pod 持续 Pending", "direct_cause": "nodeSelector (aiops.e2e/nonexistent-node-label=true) 在集群 3 个节点上均无匹配标签", "manifestation": "Pod rc-pending-nodeselector 状态 Pending，FailedScheduling 事件显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'"}
   rca_analysis={"phenomenon": "命名空间 aiops-e2e 中 Pod rc-pending-nodeselector 状态为 Pending，异常类型 PendingUnschedulable，已于 27 分钟前创建但始终未调度到任何节点。", "evidence_inventory": [{"id": "ev-01", "source": "kubectl_get_by_name", "content": "Pod rc-pending-nodeselector 当前状态 Pending，0/1 READY，27m，无 IP 无 Node", "reliability": "高"}, {"id": "ev-02", "source": "kubectl_describe", "content": "FailedScheduling 事件: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}, {"id": "ev-03", "source": "kubectl_get_yaml", "content": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}", "reliability": "高"}, {"id": "ev-04", "source": "run_bash_command (kubectl get nodes -o wide)", "content": "集群3节点(master/node1/node2)均Ready，均不包含 aiops.e2e/nonexistent-node-label 标签", "reliability": "高"}, {"id": "ev-05", "source": "fetch_runbook", "content": "Runbook pod-pending-unschedulable.md: FailedScheduling + didn't match node selector/affinity = 调度约束不匹配(高置信度)", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "ev-01", "raw_data": "rc-pending-nodeselector 0/1 Pending 0 27m <none> <none>", "interpretation": "Pod 当前仍处于 Pending 状态，27 分钟未调度，无节点绑定，确认为活跃异常"}, {"evidence_id": "ev-02", "raw_data": "Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.", "interpretation": "调度器明确报告所有 3 个节点均不匹配 Pod 的 node affinity/selector，且抢占无法帮助，排除资源不足场景"}, {"evidence_id": "ev-03", "raw_data": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}", "interpretation": "Pod YAML 中 nodeSelector 要求节点具有键 aiops.e2e/nonexistent-node-label 值为 true 的标签"}, {"evidence_id": "ev-04", "raw_data": "master Ready, node1 Ready, node2 Ready；LABELS 字段均不包含 aiops.e2e/nonexistent-node-label", "interpretation": "集群中 3 个节点均不存在 Pod 所需的标签，直接证实了 FailedScheduling 事件的原因"}, {"evidence_id": "ev-05", "raw_data": "判定规则: FailedScheduling + node(s) didn't match node selector/affinity → 调度约束不匹配（高置信度）", "interpretation": "Runbook 判定规则完全匹配当前场景，确认根因分类为调度约束(nodeSelector)不匹配"}], "causal_chain": {"root_cause": "Pod rc-pending-nodeselector 的 spec.nodeSelector 配置了集群中不存在的标签 aiops.e2e/nonexistent-node-label=true，导致调度器无法找到任何可调度节点", "propagation": "Pod 创建后 scheduler 遍历集群 3 个节点(master/node1/node2)检查 nodeSelector 约束 → 所有节点均不匹配 → scheduler 标记 Unschedulable → 重试调度仍失败 → Pod 持续 Pending", "direct_cause": "nodeSelector (aiops.e2e/nonexistent-node-label=true) 在集群 3 个节点上均无匹配标签", "manifestation": "Pod rc-pending-nodeselector 状态 Pending，FailedScheduling 事件显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'"}, "root_cause": "Pod rc-pending-nodeselector (aiops-e2e 命名空间) 处于 Pending 状态 27 分钟，根因为 nodeSelector 标签不匹配。YAML spec 中 nodeSelector 配置为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}，但集群 3 个节点 (master/node1/node2) 均无此标签，FailedScheduling 事件明确报告 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"。Pod QoS Class 为 BestEffort（无资源请求），排除了资源不足场景。Runbook pod-pending-unschedulable.md 判定规则完全命中，置信度高。", "root_cause_summary": "Pod rc-pending-nodeselector (aiops-e2e 命名空间) 处于 Pending 状态 27 分钟，根因为 nodeSelector 标签不匹配。YAML spec 中 nodeSelector 配置为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}，但集群 3 个节点 (master/node1/node2) 均无此标签，FailedScheduling 事件明确报告 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"。Pod QoS Class 为 BestEffort（无资源请求），排除了资源不足场景。Runbook pod-pending-unschedulable.md 判定规则完全命中，置信度高。", "confidence": 0.95, "confidence_reason": "直接证据完整且无矛盾：ev-02 FailedScheduling 事件原文明确指向 node affinity/selector 不匹配；ev-03 YAML 确认了 nodeSelector 具体值；ev-04 节点标签采集直接证实 3 个节点均无该标签。因果链从根因到现象全部被工具输出验证，Runbook 规则完全匹配。置信度 0.95。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "资源不足（CPU/内存不足）", "probability": "low", "reason": "Pod QoS Class 为 BestEffort，无资源 requests；FailedScheduling 原文不包含 Insufficient cpu/memory，明确指向 node affinity/selector"}, {"cause": "节点 taint/toleration 不匹配", "probability": "low", "reason": "FailedScheduling 原文不包含 'had untolerated taint'；Pod 有默认 toleration (node.kubernetes.io/not-ready:NoExecute)，且调度器消息明确指向 node affinity/selector"}, {"cause": "PVC 未绑定", "probability": "low", "reason": "Pod 仅有一个 projected volume (kube-api-access)，无 PVC；FailedScheduling 不包含 'unbound immediate PersistentVolumeClaims'"}, {"cause": "节点不可调度", "probability": "low", "reason": "ev-04 显示所有 3 个节点均为 Ready 状态，无 SchedulingDisabled"}], "limitations": "未采集节点完整 labels 列表（ev-04 仅确认标签不存在，未展示节点全部标签信息用于对比），但不影响根因结论。未采集节点资源 allocatable/capacity 详情，但 QoS BestEffort 且 FailedScheduling 消息不指向资源不足，因此不影响判断。", "llm_raw_analysis": "分析流程：1) 证据清点：共7条证据(5条已采集+2条上游layer已验证)，ev-01确认Pod仍Pending，ev-02确认FailedScheduling事件，ev-03确认nodeSelector值，ev-04确认3节点均无匹配标签，ev-05确认runbook判定规则命中。2) 逐条分析：所有证据一致指向nodeSelector标签不匹配。3) 关联分析：ev-02(事件) + ev-03(YAML) + ev-04(节点标签)形成完整三角验证。4) 因果链：用户配置了不存在的nodeSelector标签→调度器无法匹配任何节点→Pod持续Pending。5) 置信度评估：直接证据链完整无缺口，0.95。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector (aiops-e2e 命名空间) 处于 Pending 状态 27 分钟，根因为 nodeSelector 标签不匹配。YAML spec 中 nodeSelector 配置为 {"aiops.e2e/nonexistent-node-labe...
   置信度: 95%
   🔗 因果链:
     根本原因: Pod rc-pending-nodeselector 的 spec.nodeSelector 配置了集群中不存在的标签 aiops.e2e/nonexistent-node-label=true，导致调度器无法找到任何可调度节点
     传导机制: Pod 创建后 scheduler 遍历集群 3 个节点(master/node1/node2)检查 nodeSelector 约束 → 所有节点均不匹配 → scheduler 标记 Unschedulable → 重试调度仍失败 → Pod 持续 Pending
     最终表现: Pod rc-pending-nodeselector 状态 Pending，FailedScheduling 事件显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (29.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6190 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 38.2s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，我是资深 K8s 诊断报告专家。根据您的问题和提供的分析数据，我将直接回答您的问题，并遵循诊断模板生成一份详尽、完整的报告。

---

## 📊 问题直接回答：集群当前状态总结

经诊断，您的集群整体运行正常，仅存在一个明确的异常问题。

### 当前集群状态总览

| 指标 | 数值 |
|---|---|
| 集群总 Pod 数 | 65 |
| 正常运行 Pod 数 | 59 (Status: Running) |
| **异常 Pod 数** | **1 (Status: Pending)** |

### 发现的根本问题

集群中存在一个名为 `rc-pending-nodeselector` 的 Pod，位于 `aiops-e2e` 命名空间，已处于 **Pending (待调度)** 状态 **27分钟**。

**根本原因**：该 Pod 的配置文件 (`spec`) 中设置了节点选择器 (`nodeSelector`) `aiops.e2e/nonexistent-node-label=true`，但集群中的 3 个节点均不包含此标签，导致调度器无法找到任何可用的节点来运行该 Pod。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending / PendingUnschedulable |
| **兼容归因层** | L1 - Scheduling |
| **问题分类** | 调度约束不匹配 (NodeSelector 标签不匹配) |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/4 (75%) |

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-pending-nodeselector` |
| Namespace | `aiops-e2e` |
| Node | `<none>` (未被调度) |
| 错误信息 | `Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` |

---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | `STATUS: Pending` | Pod 处于待调度状态，未能分配到节点。 |
| 2 | 调度事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | `Warning  FailedScheduling  27m  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | **直接证据**：调度器明确报告无节点满足 Pod 的节点亲和性/选择器约束。 |
| 3 | Pod 配置 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` | `spec.nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}` | **根因定位**：Pod 配置了一个集群中不存在的标签选择器。 |
| 4 | 节点状态 | `run_bash_command` (基础信息) | `NAME     STATUS   ROLES`<br>`master   Ready    control-plane`<br>`node1    Ready    <none>`<br>`node2    Ready    <none>` | 集群节点状态为 `Ready`，排除了节点不可用的问题。 |
| 5 | Pod 命令 | `kubectl describe pod` / `kubectl get yaml` | `Command: sleep 3600` | Pod 命令为简单的 `sleep`，排除了应用自身因代码问题（如启动失败、panic）导致的 Pending。 |

### 证据关联分析
- **证据 #2 + #3 + #4 印证**：调度事件显示“节点不匹配 Pod 的节点选择器” (证据 #2)，Pod 的 YAML 配置了 `aiops.e2e/nonexistent-node-label=true` 标签选择器 (证据 #3)，而集群中 3 个节点的 `Ready` 标签列表中均不包含此标签 (证据 #4)。三者构成了完整的因果链。
- **证据 #5 排除干扰**：Pod 的启动命令仅为 `sleep 3600`，这意味着不存在因需要申请特定资源或执行复杂初始化过程而导致的 Pending。问题被精准锁定在调度约束上。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 集群3个节点的完整标签列表 (`kubectl describe node`) | important | 能够详细展示节点标签，直接证明标签缺失，但当前证据链已足够闭环，不影响核心结论。 |

---
## 🎯 根因分析

### 因果链
```
┌───────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                              │
│ Pod 的 spec.nodeSelector 配置为集群中不存在的标签：                     │
│   aiops.e2e/nonexistent-node-label=true                              │
└───────────────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                              │
│ Kube-Scheduler 遍历集群所有 3 个节点，检查 nodeSelector 约束是否满足 →   │
│ 所有节点均不满足 → 无候选节点                                         │
└───────────────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                              │
│ 调度器因无符合条件节点，将 Pod 标记为 "Unschedulable"                  │
└───────────────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                          │
│ Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续处于            │
│ "Pending" 状态，并产生 "FailedScheduling" 事件。                       │
└───────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据**证据 #2** (FailedScheduling 事件)、**证据 #3** (Pod YAML 中的 nodeSelector) 和**证据 #4** (所有节点均不包含该标签)，问题的根本原因是 **Pod `rc-pending-nodeselector` 的 `nodeSelector` 配置了集群中不存在的标签 `aiops.e2e/nonexistent-node-label=true`**，导致调度器无法找到任何匹配节点。
**置信度**：高 (95%)
- ✅ `FailedScheduling` 事件明确指向调度约束不匹配。
- ✅ Pod YAML 中的 `nodeSelector` 配置直接确认了约束条件。
- ✅ `run_bash_command` 输出显示所有3个节点状态 `Ready`，排除了节点不可用的问题。
- ✅ Pod 启动命令为 `sleep`，排除了应用启动依赖问题。

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）
这些命令可直接在您的终端中复制执行。

**1. [推荐] 删除该 Pod(如果不需要)**
如果此 Pod 是测试用例或已废弃，直接删除即可。
```bash
kubectl delete pod rc-pending-nodeselector -n aiops-e2e
```
*依据*：这是最快捷的解决方法，清除未使用的异常对象。

**2. [修正] 为 Pod 的 nodeSelector 匹配的节点打上标签，或修改 Pod 的 nodeSelector**
此方案有 A、B 两个分支，请根据实际情况选择其一。
*依据*：证据 #3 显示 Pod 依赖标签 `aiops.e2e/nonexistent-node-label=true`。

- **分支 A：给其中一个节点打上相应标签，使 Pod 可以被调度。**
  ```bash
  # 将标签打在 node1 上
  kubectl label node node1 aiops.e2e/nonexistent-node-label=true
  ```
  或者如果你希望 Pod 调度到指定节点，也可以不使用nodeSelector方式，而是使用 `nodeName` 或 `nodeAffinity`。

- **分支 B：修改 Deployment（或其他上层控制器）的 YAML，移除或修正 nodeSelector。**
  首先，你需要找到是哪个控制器（如 Deployment, StatefulSet, DaemonSet）创建了这个 Pod。
  ```bash
  # 找到拥有此 Pod 的控制器
  kubectl get pod rc-pending-nodeselector -n aiops-e2e -o jsonpath='{.metadata.ownerReferences[0].name}'
  ```
  假设输出是 `rc-pending-nodeselector`，则执行：
  ```bash
  # 编辑 Deployment，移除 nodeSelector
  kubectl edit deployment rc-pending-nodeselector -n aiops-e2e
  ```
  在打开的编辑器中，找到 `spec.template.spec.nodeSelector` 字段并将其删除，然后保存退出。控制器会自动重建 Pod。

### 后续优化
1. **命名规范**：避免在关键标签中使用 `nonexistent` 等文字，确保标签键值对的准确性。
2. **代码审查**：在应用部署的 CI/CD 或审查流程中，检查 `nodeSelector`、`affinity` 等调度约束的正确性，确保标签在集群中确实存在。
3. **监控告警**：配置针对 `Pending` 状态 Pod 的告警，以便在出现类似问题时快速响应。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 被移除 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | `Error from server (NotFound): pods "rc-pending-nodeselector" not found` |
| 2. (分支 A) 确认标签已添加 | `kubectl get node node1 --show-labels` | 输出的标签列表中包含 `aiops.e2e/nonexistent-node-label=true` |
| 3. (分支 A) 确认 Pod 运行 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | `STATUS: Running` 或 `STATUS: Completed` |

---
## ⚠️ 注意事项
- 本次诊断结论非常明确，证据链完整。问题是由 Pod 配置错误导致的单一事件，并非集群基础设施故障（如节点不可用、kubelet 故障）。
- 如果您的集群中还有其他 Pod 配置了类似 `nonexistent` 的标签，请一并检查。

---

## 📊 性能统计

├─ 总耗时: 1.6m
├─ 问题定位: 21.7s (22%) ✅
├─ 证据链采集: 24.6s (25%) ✅
├─ 根因分析: 22.2s (23%) ✅
├─ 汇总总结: 29.6s (30%) ✅
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
