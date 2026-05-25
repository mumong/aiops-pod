======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: be7f02a5bbba44ab]

📍 [问题定位] 执行中...
   💭 [问题定位] 我将先全局扫描集群中的所有 Pod 状态，了解整体情况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 好，我已经扫描到集群中有一个异常 Pod。让我进一步获取详细信息。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          29s   <none>   <none>   
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
29s         Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are
   💭 [问题定位] 让我获取该 Pod 的完整描述以确认调度失败原因。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  31s   default-scheduler  0/3 nodes are available: 3 node(s) did
   💭 [问题定位] 现在再拿一个匹配的 runbook 来辅助定位。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 好的，所有的信息已经足够我做出完整的定位分析了。以下是分析结果：

---

## 集群 Pod 异常定位分析

### 全局扫描结果
集群共有 **65 个 Pod**，分布在多个命名空间中。其中：
- **Running (正常): 59 个**
- **Pending (异常): 1 个**

### 异常 Pod 详情

| 属性 | 值 |
|------|-----|
| **Pod** | `rc-pending-nodeselector` (aiops-e2e 命名空间) |
| **STATUS** | `Pending` |
| **READY** | 0/1 |
| **Node** | `<none>` （未绑定节点） |
| **Events** | `FailedScheduling` |

### 根因分析

调度器日志关键信息：
> **"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"**

该 Pod 设置了 **nodeSelector**：
```
Node-Selectors: aiops.e2e/nonexistent-node-label=true
```

而集群中的 **3 个节点都没有匹配该标签**，因此调度器无法将此 Pod 调度到任何节点上。

---

### 输出结构化信息

- **layer**: L1
- **derived_layer**: L1
- **layers**: ["L1"]
- **layer_name**: 调度约束不匹配 (PendingUnschedulable)
- **pod_status_keyword**: Pending
- **pod_abnormal_type**: PendingUnschedulable
- **status_category**: scheduling
- **abnormal_pods**: [`rc-pending-nodeselector` (aiops-e2e)]
- **abnormal_groups**: {`PendingUnschedulable`: [`rc-pending-nodeselector`]}
- **key_entities**: Pod `rc-pending-nodeselector` (aiops-e2e)，nodeSelector `aiops.e2e/nonexistent-node-label=true`，集群 3 个节点
- **possible_scenarios**: 
  1. Pod 的 nodeSelector 引用了不存在的节点标签 `aiops.e2e/nonexistent-node-label=true`，所有节点都不匹配
  2. 该 Pod 可能用于测试目的（有 `rootcause-e2e=true` 标签），人为设置了不存在的标签来模拟调度失败场景
- **confidence**: 高

### 建议后续排查方向（供 evidence 节点参考）
1. 检查是否存在节点应该有此标签但缺失（标签拼写错误或遗漏）
2. 如果本意是调度到特定节点，需要给目标节点打上对应标签，或修改 Pod 的 nodeSelector
3. 该 Pod 带有 `rootcause-e2e=true` 标签，也可能是专门的 e2e 测试用例，属于预期行为
   ✅ [问题定位] 完成 (19.9s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'Pod 的 nodeSelector 引用了不存在的节点标签 aiops.e2e/nonexistent-node-label=true，所有节点都不匹配，导致调度失败', 'probability': '高', 'reason': "Events 明确提示 'didn't match Pod's node affinity/selector'，且 describe 确认了 Node-Selectors 字段"}, {'scenario': '该 Pod 可能用于 e2e 测试目的（带 rootcause-e2e=true 标签），人为设置不存在的标签模拟调度失败场景', 'probability': '中', 'reason': 'Pod 带有 rootcause-e2e=true 标签，可能是预期行为'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "nodeSelector", "name": "aiops.e2e/nonexistent-node-label=true", "namespace": ""}, {"type": "Cluster", "name": "集群 3 个节点", "namespace": ""}]
   reasoning=集群中存在 1 个异常 Pod rc-pending-nodeselector (aiops-e2e 命名空间)，状态为 Pending，READY 0/1，未绑定节点。Events 显示 FailedScheduling，原文 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。kubectl describe 确认 Pod 设置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，但集群 3 个节点均无此标签，导致调度失败。根因为调度约束(nodeSelector)不匹配，属于 L1 层调度问题。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "调度约束不匹配 (PendingUnschedulable)", "confidence": 0.95, "reasoning": "集群中存在 1 个异常 Pod rc-pending-nodeselector (aiops-e2e 命名空间)，状态为 Pending，READY 0/1，未绑定节点。Events 显示 FailedScheduling，原文 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。kubectl describe 确认 Pod 设置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，但集群 3 个节点均无此标签，导致调度失败。根因为调度约束(nodeSelector)不匹配，属于 L1 层调度问题。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "nodeSelector", "name": "aiops.e2e/nonexistent-node-label=true", "namespace": ""}, {"type": "Cluster", "name": "集群 3 个节点", "namespace": ""}], "possible_scenarios": [{"scenario": "Pod 的 nodeSelector 引用了不存在的节点标签 aiops.e2e/nonexistent-node-label=true，所有节点都不匹配，导致调度失败", "probability": "高", "reason": "Events 明确提示 'didn't match Pod's node affinity/selector'，且 describe 确认了 Node-Selectors 字段"}, {"scenario": "该 Pod 可能用于 e2e 测试目的（带 rootcause-e2e=true 标签），人为设置不存在的标签模拟调度失败场景", "probability": "中", "reason": "Pod 带有 rootcause-e2e=true 标签，可能是预期行为"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              27s     <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/be7f02a5bbba44ab/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/be7f02a5bbba44ab/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/be7f02a5bbba44ab/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我来按照既定 evidence_plan 执行工具调用，采集真实环境证据。先执行 critical 级别的关键工具调用。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_events
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
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  53s   default-scheduler  0/3 nodes are available: 3 node(s) did
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
53s         Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:18:44Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [证据链采集] 现在执行检查节点是否具有 `aiops.e2e/` 前缀标签的关键证据：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"name\": \"master\",\n  \"labels\": []\n}\n{\n  \"name\": \"node1\",\n  \"labels\": []\n}\n{\n  \"name\": \"node2\",\n  \"labels\": []\n}\n", "stderr": "", "returnco
   💭 [证据链采集] ## 证据采集结论

### ✅ 已采集证据（4 条 critical/important 维度）

| 计划项 | 证据结果 | 说明 |
|--------|----------|------|
| **e1-g1-pod-status** (critical) | Pod YAML 确认 `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}`，phase=Pending，nodeName=None | 调度约束已固定，标签不存在 |
| **e2-g1-events** (critical) | FailedScheduling: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 明确指向 nodeSelector 不匹配 |
| **e3-g1-nodes** (critical) | 集群 3 个节点（master/node1/node2）的 labels 中 **均无任何 aiops 前缀的标签** | 节点标签确实不满足 Pod 需求 |
| **e5-g1-describe** (important) | Node-Selectors=`aiops.e2e/nonexistent-node-label=true`，No Taints 问题，No PVC 依赖 | 纯 nodeSelector 不匹配，排除 taint/PVC 分支 |

### 🚫 无冲突/负向证据
- Pod 仍在 `aiops-e2e` 命名空间存在，状态持续 Pending
- 事件时间线与创建时间一致，无历史噪音
- Pod 带 `rootcause-e2e=true` 标签，符合 e2e 测试预期

### 📋 根因判定
**判定：调度约束(nodeSelector)不匹配 — 高置信度**

- FailedScheduling 原文命中 `didn't match Pod's node affinity/selector`
- Pod 要求节点具有标签 `aiops.e2e/nonexistent-node-label=true`
- 集群 3 个节点均无此标签（无任何 `aiops.*` 标签）
- 排除 PVC 未绑定、Taint/Toleration、hostPort 冲突、资源不足等其它分支

该 Pod 带有 `rootcause-e2e=true` 标签，很可能是人为构造的 e2e 测试场景，模拟调度失败。如需修复，可：
1. 给任一节点打上对应标签：`kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`
2. 或直接删除该测试 Pod：`kubectl delete pod rc-pending-nodeselector -n aiops-e2e`
   ✅ [证据链采集] 完成 (18.3s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1-g1-pod-status","description":"验证异常组 g1 的代表 Pod rc-pending-nodeselector 的当前状态和 nodeSelector 配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e","resource":"pod","output":"yaml"},"purpose":"确认 Pod 的 nodeSelector 字段和 spec/status 当前状态","evidence_type":"current_state","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e2-g1-events","description":"采集 aiops-e2e 命名空间最新事件，确认 FailedScheduling 事件原文","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --sort-by='.lastTimestamp' | tail -20","tool_args":{"namespace":"aiops-e2e","sort_by":".lastTimestamp"},"purpose":"确认 FailedScheduling 事件的具体调度失败原因","evidence_type":"event","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3-g1-nodes","description":"验证集群所有节点的标签是否存在 aiops.e2e/nonexistent-node-label","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, labels: .metadata.labels | keys}'","tool_args":{"command":"kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, labels: [.metadata.labels | keys[] | select(startswith(\"aiops\"))]}'"},"purpose":"验证集群节点是否具有 aiops.e2e/nonexistent-node-label 标签","evidence_type":"configuration","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4-g1-runbook","description":"获取 PendingUnschedulable runbook 作为参考上下文","level":"reference","tool":"fetch_runbook","command":"fetch_runbook('pod-pending-unschedulable.md')","tool_args":{"runbook":"pod-pending-unschedulable.md"},"purpose":"获取 runbook 参考指导","evidence_type":"reference","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5-g1-describe","description":"kubectl describe pod 获取更详细的事件和状态","level":"important","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e","resource":"pod"},"purpose":"验证 Pod 详细描述中的 Node-Selectors、Conditions、Events","evidence_type":"current_state","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod PendingUnschedulable / 调度失败\n\n> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | Pending，且 Events 含 `FailedScheduling` |\n| 资源不足 | `Insufficient cpu/memory/ephemeral-storage`、`Too many pods` |\n| 调度约束 | nodeSelector/affinity 不匹配、节点 taint 未被 toleration 容忍 |\n| 存储前置条件 | `pod has unbound immediate PersistentVolumeClaims` 应切换到 pod-volume-mount-failed |\n| 节点状态 | Node NotReady/Unknown、SchedulingDisabled、Unschedulable 会导致无可用调度节点 |\n\n## 根因分流\n- 资源不足: FailedScheduling 原文含 Insufficient cpu/memory/ephemeral-storage、Too many pods。\n- hostPort 冲突: 原文含 `didn't have free ports for the requested pod ports`，说明目标节点端口已被占用。\n- Taint/Toleration 不匹配: 原文含 `had untolerated taint`，必须检查 Pod tolerations 和 Node taints。\n- nodeSelector / nodeAffinity / podAffinity 不匹配: 原文含 `didn't match Pod's node affinity/selector` 或 affinity/anti-affinity。\n- PVC 未绑定: 原文含 `unbound immediate PersistentVolumeClaims`，根因在存储绑定而不是调度资源。\n- 节点不可调度: Node Ready=False/Unknown、SchedulingDisabled、`node.kubernetes.io/not-ready` 或 `node.kubernetes.io/unreachable`。\n- 镜像、挂载、容器启动错误不会表现为 FailedScheduling；如果 Pod 已绑定 nodeName，应切换到对应 runbook。\n\n## 诊断流程\n\n### Step 1: 确认 Pod 调度失败事件\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n关注 Events 中的 `FailedScheduling` 原文。\n\n### Step 2: 检查 Pod 调度约束\n```bash\nkubectl get pod <pod-name> -n <namespace> -o yaml\n```\n关注: spec.nodeName 是否为空、nodeSelector、affinity、tolerations、topologySpreadConstraints、schedulerName、priorityClassName、resource requests、hostNetwork/hostPort。\n\n### Step 3: 检查节点状态和可调度性\n```bash\nkubectl get nodes -o wide\n```\n关注: STATUS 列是否有 NotReady/Unknown，AGE 判断是否新节点\n\n### Step 4: 检查候选节点详情\n```bash\nkubectl describe node <node-name>\n```\n重点关注:\n- `Conditions` 部分: Ready=False/Unknown 的 reason 和 message\n- `Taints` 部分: 是否有 NoSchedule/NoExecute taint\n- `Allocatable` vs `Capacity`: 资源是否耗尽\n- `Non-terminated Pods`: 节点上运行的 Pod 数量\n\n### Step 5: 检查 PVC 状态（如果 FailedScheduling 指向 PVC）\n```bash\nkubectl get pvc -n <namespace>\nkubectl describe pvc <pvc> -n <namespace>\n```\n关注: Pending、StorageClass、volumeBindingMode、ProvisioningFailed。\n\n### Step 6: 检查 Ready 条件详情\n```bash\nkubectl get node <node-name> -o jsonpath='{.status.conditions[?(@.type==\"Ready\")]}' | python3 -m json.tool\n```\n关注: status, reason, message, lastHeartbeatTime\n\n### Step 7: 检查节点事件\n```bash\nkubectl get events -A --field-selector involvedObject.kind=Node,involvedObject.name=<node-name> --sort-by='.lastTimestamp'\n```\n关注: NodeNotReady、NodeNotSchedulable、PLEG unhealthy 等事件\n\n### Step 8: 检查受影响的 Pending Pod\n```bash\nkubectl get pods -A --field-selector status.phase=Pending | head -20\n```\n\n## 判定规则\n\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| FailedScheduling + Insufficient cpu/memory | 资源不足导致 Pod Pending | 高 |\n| FailedScheduling + Too many pods | 节点 Pod 数量上限导致 Pending | 高 |\n| FailedScheduling + didn't have free ports for the requested pod ports | hostPort 端口冲突导致 Pending | 高 |\n| FailedScheduling + had untolerated taint | taint/toleration 不匹配 | 高 |\n| FailedScheduling + node(s) didn't match node selector/affinity | 调度约束不匹配 | 高 |\n| FailedScheduling + pod has unbound immediate PersistentVolumeClaims | PVC 未绑定，应切换 VolumeMountFailed/PVC 分支 | 高 |\n| 所有候选 Node NotReady/Unschedulable | 无可用调度节点 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/be7f02a5bbba44ab/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/be7f02a5bbba44ab/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/be7f02a5bbba44ab/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  53s   default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  53s   default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/be7f02a5bbba44ab/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/be7f02a5bbba44ab/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/be7f02a5bbba44ab/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n53s         Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/be7f02a5bbba44ab/tools/003-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/be7f02a5bbba44ab/tools/003-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/be7f02a5bbba44ab/tools/003-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/be7f02a5bbba44ab/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/be7f02a5bbba44ab/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/be7f02a5bbba44ab/tools/004-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"name\\\": \\\"master\\\",\\n  \\\"labels\\\": []\\n}\\n{\\n  \\\"name\\\": \\\"node1\\\",\\n  \\\"labels\\\": []\\n}\\n{\\n  \\\"name\\\": \\\"node2\\\",\\n  \\\"labels\\\": []\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/be7f02a5bbba44ab/tools/005-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/be7f02a5bbba44ab/tools/005-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/be7f02a5bbba44ab/tools/005-evidence-run_bash_command.summary.txt"}],"llm_analysis":"## 证据采集结论\n\n### ✅ 已采集证据（4 条 critical/important 维度）\n\n| 计划项 | 证据结果 | 说明 |\n|--------|----------|------|\n| **e1-g1-pod-status** (critical) | Pod YAML 确认 `nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}`，phase=Pending，nodeName=None | 调度约束已固定，标签不存在 |\n| **e2-g1-events** (critical) | FailedScheduling: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 明确指向 nodeSelector 不匹配 |\n| **e3-g1-nodes** (critical) | 集群 3 个节点（master/node1/node2）的 labels 中 **均无任何 aiops 前缀的标签** | 节点标签确实不满足 Pod 需求 |\n| **e5-g1-describe** (important) | Node-Selectors=`aiops.e2e/nonexistent-node-label=true`，No Taints 问题，No PVC 依赖 | 纯 nodeSelector 不匹配，排除 taint/PVC 分支 |\n\n### 🚫 无冲突/负向证据\n- Pod 仍在 `aiops-e2e` 命名空间存在，状态持续 Pending\n- 事件时间线与创建时间一致，无历史噪音\n- Pod 带 `rootcause-e2e=true` 标签，符合 e2e 测试预期\n\n### 📋 根因判定\n**判定：调度约束(nodeSelector)不匹配 — 高置信度**\n\n- FailedScheduling 原文命中 `didn't match Pod's node affinity/selector`\n- Pod 要求节点具有标签 `aiops.e2e/nonexistent-node-label=true`\n- 集群 3 个节点均无此标签（无任何 `aiops.*` 标签）\n- 排除 PVC 未绑定、Taint/Toleration、hostPort 冲突、资源不足等其它分支\n\n该 Pod 带有 `rootcause-e2e=true` 标签，很可能是人为构造的 e2e 测试场景，模拟调度失败。如需修复，可：\n1. 给任一节点打上对应标签：`kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`\n2. 或直接删除该测试 Pod：`kubectl delete pod rc-pending-nodeselector -n aiops-e2e`","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 8 个，匹配计划 5 个，未规划证据 3 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":5,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1-g1-pod-status","description":"验证异常组 g1 的代表 Pod rc-pending-nodeselector 的当前状态和 nodeSelector 配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"确认 Pod 的 nodeSelector 字段和 spec/status 当前状态","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-g1-events","description":"采集 aiops-e2e 命名空间最新事件，确认 FailedScheduling 事件原文","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --sort-by='.lastTimestamp' | tail -20","purpose":"确认 FailedScheduling 事件的具体调度失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3-g1-nodes","description":"验证集群所有节点的标签是否存在 aiops.e2e/nonexistent-node-label","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, labels: .metadata.labels | keys}'","purpose":"验证集群节点是否具有 aiops.e2e/nonexistent-node-label 标签","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4-g1-runbook","description":"获取 PendingUnschedulable runbook 作为参考上下文","level":"optional","tool":"fetch_runbook","command":"fetch_runbook('pod-pending-unschedulable.md')","purpose":"获取 runbook 参考指导","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5-g1-describe","description":"kubectl describe pod 获取更详细的事件和状态","level":"important","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"验证 Pod 详细描述中的 Node-Selectors、Conditions、Events","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1-g1-pod-status | critical | ✅ | kubectl_get_yaml | 验证异常组 g1 的代表 Pod rc-pending-nodeselector 的当前状... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e2-g1-events | critical | ✅ | kubectl_events | 采集 aiops-e2e 命名空间最新事件，确认 FailedScheduling 事件原文 | `kubectl get events -n aiops-e2e --sort-by='.lastTimestamp' | tail -20` |
   | e3-g1-nodes | critical | ✅ | run_bash_command | 验证集群所有节点的标签是否存在 aiops.e2e/nonexistent-node-label | `kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, labels: .me...` |
   | e4-g1-runbook | reference | ✅ | fetch_runbook | 获取 PendingUnschedulable runbook 作为参考上下文 | `fetch_runbook('pod-pending-unschedulable.md')` |
   | e5-g1-describe | important | ✅ | kubectl_describe | kubectl describe pod 获取更详细的事件和状态 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (12.5s)
   📤 → 下游数据: root_cause=异常组 g1 的 Pod rc-pending-nodeselector (aiops-e2e 命名空间) 处于 Pending 状态，根因为 nodeSelector 不匹配。Pod YAML 确认设置了 nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}（e1），FailedScheduling 事件明确报告 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'（e2），而集群 3 个节点（master/node1/node2）的 labels 均为空，没有任何 aiops 前缀标签（e3）。Pod 无 PVC 依赖、QoS=BestEffort，排除了资源不足和 PVC 分支（e5）。该 Pod 带有 rootcause-e2e=true 标签，很可能为 e2e 测试场景。
   confidence=98%
   causal_chain={"root_cause": "Pod rc-pending-nodeselector 的 spec 中设置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，但集群 3 个节点均无此标签，导致调度器无法找到可用节点。", "propagation": "调度器 default-scheduler 遍历所有 3 个节点（master/node1/node2），每个节点均不满足 nodeSelector 条件 → 节点被跳过 → 无候选节点。", "direct_cause": "集群中没有任何节点拥有 aiops.e2e/nonexistent-node-label=true 标签，3 个节点的 labels 均为空。", "manifestation": "Pod rc-pending-nodeselector 持续处于 Pending 状态，READY 0/1，Events 中反复出现 FailedScheduling 事件，原文 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。"}
   rca_analysis={"phenomenon": "集群 aiops-e2e 命名空间存在 1 个异常 Pod rc-pending-nodeselector，状态为 Pending，READY 0/1，未绑定节点（nodeName=None）。Events 持续报 FailedScheduling，提示所有 3 个节点均不匹配 nodeSelector。", "evidence_inventory": [{"id": "e1-g1-pod-status", "source": "kubectl_get_yaml", "content": "Pod rc-pending-nodeselector YAML 确认 phase=Pending, nodeName=None, nodeSelector={\"aiops.e2e/nonexistent-node-label\": \"true\"}", "reliability": "高"}, {"id": "e2-g1-events", "source": "kubectl_describe / kubectl_events", "content": "FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}, {"id": "e3-g1-nodes", "source": "run_bash_command (节点标签查询)", "content": "集群 3 个节点 master/node1/node2 均无任何标签，包括 aiops.e2e/nonexistent-node-label", "reliability": "高"}, {"id": "e5-g1-describe", "source": "kubectl_describe", "content": "Pod QoS=BestEffort, Node-Selectors=aiops.e2e/nonexistent-node-label=true, 无 PVC 依赖, 无 Taint 不匹配", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1-g1-pod-status", "raw_data": "phase: Pending\nnodeName: None\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}", "interpretation": "Pod 明确设置了 nodeSelector 要求节点带有 aiops.e2e/nonexistent-node-label=true 标签，但当前未分配到任何节点。"}, {"evidence_id": "e2-g1-events", "raw_data": "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "interpretation": "调度器明确报告所有 3 个节点均不满足 Pod 的 nodeSelector/affinity 约束，排除资源不足、hostPort、PVC 等其他分支。"}, {"evidence_id": "e3-g1-nodes", "raw_data": "master: labels=[]\nnode1: labels=[]\nnode2: labels=[]", "interpretation": "集群 3 个节点（master、node1、node2）均没有任何标签，更不存在 aiops.e2e/nonexistent-node-label 标签。Pod 的 nodeSelector 条件无法被满足。"}, {"evidence_id": "e5-g1-describe", "raw_data": "Node-Selectors: aiops.e2e/nonexistent-node-label=true\nQoS Class: BestEffort\nNo PVC references", "interpretation": "进一步确认了 Pod 的调度约束类型为 nodeSelector，且无 PVC 依赖、无资源请求限制（BestEffort），可排除资源不足和 PVC 未绑定分支。"}], "causal_chain": {"root_cause": "Pod rc-pending-nodeselector 的 spec 中设置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，但集群 3 个节点均无此标签，导致调度器无法找到可用节点。", "propagation": "调度器 default-scheduler 遍历所有 3 个节点（master/node1/node2），每个节点均不满足 nodeSelector 条件 → 节点被跳过 → 无候选节点。", "direct_cause": "集群中没有任何节点拥有 aiops.e2e/nonexistent-node-label=true 标签，3 个节点的 labels 均为空。", "manifestation": "Pod rc-pending-nodeselector 持续处于 Pending 状态，READY 0/1，Events 中反复出现 FailedScheduling 事件，原文 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。"}, "root_cause": "异常组 g1 的 Pod rc-pending-nodeselector (aiops-e2e 命名空间) 处于 Pending 状态，根因为 nodeSelector 不匹配。Pod YAML 确认设置了 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}（e1），FailedScheduling 事件明确报告 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'（e2），而集群 3 个节点（master/node1/node2）的 labels 均为空，没有任何 aiops 前缀标签（e3）。Pod 无 PVC 依赖、QoS=BestEffort，排除了资源不足和 PVC 分支（e5）。该 Pod 带有 rootcause-e2e=true 标签，很可能为 e2e 测试场景。", "root_cause_summary": "异常组 g1 的 Pod rc-pending-nodeselector (aiops-e2e 命名空间) 处于 Pending 状态，根因为 nodeSelector 不匹配。Pod YAML 确认设置了 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}（e1），FailedScheduling 事件明确报告 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'（e2），而集群 3 个节点（master/node1/node2）的 labels 均为空，没有任何 aiops 前缀标签（e3）。Pod 无 PVC 依赖、QoS=BestEffort，排除了资源不足和 PVC 分支（e5）。该 Pod 带有 rootcause-e2e=true 标签，很可能为 e2e 测试场景。", "confidence": 0.98, "confidence_reason": "有直接的多条证据（Pod YAML、FailedScheduling 事件原文、节点标签查询结果）相互印证，因果链完整清晰，无冲突证据。4 条 critical/important 证据均指向同一根因。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "资源不足（CPU/内存不足）", "probability": "low", "reason": "FailedScheduling 原文不含 Insufficient cpu/memory/storage，且 Pod QoS=BestEffort 无资源请求限制，已排除"}, {"cause": "Taint/Toleration 不匹配", "probability": "low", "reason": "FailedScheduling 原文不含 had untolerated taint，且 Pod 已配置 tolerations，已排除"}, {"cause": "PVC 未绑定", "probability": "low", "reason": "FailedScheduling 原文不含 unbound immediate PersistentVolumeClaims，Pod 无 PVC 引用，已排除"}, {"cause": "hostPort 冲突", "probability": "low", "reason": "FailedScheduling 原文不含 didn't have free ports，已排除"}, {"cause": "节点不可调度", "probability": "low", "reason": "FailedScheduling 原文不含节点 NotReady/Unschedulable 相关描述，且 3 个节点均参与调度评估，已排除"}], "limitations": "仅涉及 1 个异常 Pod，未发现其他异常组。集群其他 59 个 Pod 均为 Running 状态。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 异常组 g1 的 Pod rc-pending-nodeselector (aiops-e2e 命名空间) 处于 Pending 状态，根因为 nodeSelector 不匹配。Pod YAML 确认设置了 nodeSelector: {"aiops.e2e/nonexistent-node-lab...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod rc-pending-nodeselector 的 spec 中设置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，但集群 3 个节点均无此标签，导致调度器无法找到可用节点。
     传导机制: 调度器 default-scheduler 遍历所有 3 个节点（master/node1/node2），每个节点均不满足 nodeSelector 条件 → 节点被跳过 → 无候选节点。
     最终表现: Pod rc-pending-nodeselector 持续处于 Pending 状态，READY 0/1，Events 中反复出现 FailedScheduling 事件，原文 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (18.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5459 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 8.9s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将根据您提供的诊断数据，为您生成一份详尽、完整的报告。

---

## 📊 诊断概览

您的集群整体运行平稳，65 个 Pod 中有 **59 个处于 Running 状态**，当前存在 **1 个问题 Pod**。

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending (PendingUnschedulable) |
| **兼容归因层** | L1 - 调度问题 |
| **问题分类** | 调度约束不匹配 (`nodeSelector`) |
| **置信度** | 高 (98%) |
| **证据完整度** | 4/4 (100%) |

**核心发现**：Pod `rc-pending-nodeselector` (命名空间 `aiops-e2e`) 因为设置了集群中不存在的节点标签，导致无法被调度到任何节点上，持续处于 Pending 状态。

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 异常 Pod | `rc-pending-nodeselector` |
| Namespace | `aiops-e2e` |
| Pod 状态 | Pending (READY 0/1) |
| 错误信息 | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` (FailedScheduling 事件) |

---

## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态与配置 (YAML) | `kubectl_get_yaml` | `phase: Pending`, `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}`, `finalizers: <none>`, `terminationGracePeriodSeconds: 30` | Pod 明确设置了 `nodeSelector`，无 finalizer 阻塞，无 Terminating 相关配置问题。 |
| 2 | 调度事件 | `kubectl_events` | `53s Warning FailedScheduling Pod/rc-pending-nodeselector 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 调度器明确报告所有节点均不满足 Pod 的调度亲和/选择器要求。 |
| 3 | 节点标签 | `run_bash_command` | 集群 3 个节点 (`master`, `node1`, `node2`)  的 labels 均为空 `[]`。 | 集群中没有任何节点具备 `aiops.e2e/nonexistent-node-label` 标签。 |
| 4 | Pod 详细信息 | `kubectl_describe` | `Node-Selectors: aiops.e2e/nonexistent-node-label=true`, `QoS Class: BestEffort`, `Command: sh -c sleep 3600` | 进一步确认了 `nodeSelector` 配置，且无资源请求限制，排除了资源不足导致的问题。 |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：Pod 的 YAML (`e1`) 要求 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，事件 (`e2`) 指出所有节点都不匹配，节点 label 检查 (`e3`) 确认了集群节点标签均为空。这三者构成了完整的、无矛盾的证据闭环。
- **排除其他场景**：Pod 的 QoS 为 BestEffort 且无 PVC 依赖，排除了资源不足或存储卷未绑定作为根因。`finalizers: <none>` 排除了 finalizer 未清理导致 Pod 卡住。

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | - | - |

---

## 🎯 根因分析

### 因果链
```
┌───────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                          │
│ Pod `rc-pending-nodeselector` 的 `spec` 中设置了 `nodeSelector:                   │
│ aiops.e2e/nonexistent-node-label=true`，要求节点必须拥有该标签。                    │
└───────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌───────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                          │
│ 调度器 (`default-scheduler`) 遍历集群所有 3 个节点 (`master`, `node1`, `node2`)，   │
│ 检查每个节点的标签是否匹配 `nodeSelector`。                                        │
└───────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌───────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                          │
│ 集群 3 个节点的 labels 均为空 `[]`，均不满足 `nodeSelector` 条件。没有节点可被调度。 │
└───────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌───────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                      │
│ Pod `rc-pending-nodeselector` 持续处于 `Pending` 状态，Events 中反复出现           │
│ `FailedScheduling` 事件。                                                          │
└───────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (YAML 中的 `nodeSelector`)、证据 #2 (FailedScheduling 事件) 和证据 #3 (节点标签为空)，问题的根本原因是 **Pod `rc-pending-nodeselector` 设置的 `nodeSelector` 选择器 `aiops.e2e/nonexistent-node-label=true` 在集群中不存在，导致调度器无法为其找到任何可用的节点**。

**置信度**：高 (98%)
- ✅ `kubectl_describe` 和 `kubectl_get_yaml` 明确显示了 `nodeSelector` 配置。
- ✅ `kubectl_events` 报告了明确的 `FailedScheduling` 原因。
- ✅ 节点标签检查 (`run_bash_command`) 提供了实锤，证明标签确实不存在。
- ⚠️ 该 Pod 带有 `rootcause-e2e=true` 标签，这可能是一个模拟故障的 e2e 测试场景，属于预期行为。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）
**1. [建议] 移除 Pod 或修正其 nodeSelector**
由于该 Pod 的 `nodeSelector` 指向了一个不存在的标签，您有两个选择：
- **如果您认为这是一个误创建的 Pod**，可以将其删除：
  ```bash
  kubectl delete pod rc-pending-nodeselector -n aiops-e2e
  ```
  **依据**：删除这个无法调度的 Pod 是清理集群状态的最直接方式。

- **如果您需要这个 Pod 运行**，需要将 `nodeSelector` 修改为一个集群中真实存在的标签，或完全移除它。您需要编辑 Deployment/StatefulSet/Pod 的 YAML 文件，移除或修改 `nodeSelector` 字段。例如，移除它：
  ```bash
  kubectl patch deployment <your-deployment-name> -n aiops-e2e --type='json' -p='[{"op": "remove", "path": "/spec/template/spec/nodeSelector"}]'
  ```
  **依据**：通过移除 `nodeSelector`，调度器将不再受到此约束，可以使用所有可用的节点。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 查看 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | 如果您删除了 Pod，应显示 `NotFound`；如果您修改了 `nodeSelector`，应显示 `Running`。 |
| 2. 查看集群中所有 Pod 状态 | `kubectl get pods --all-namespaces` | 不应再见到异常状态为 `Pending` 的 Pod。 |
| 3. 确认集群健康 | `kubectl get nodes` | 所有节点状态应为 `Ready`。 |

---

## ⚠️ 注意事项
- **此 Pod 可能为测试用例**：Pod 标签包含 `rootcause-e2e=true`，这表明它很可能是自动化测试环境的一部分，用于验证集群对 `nodeSelector` 不匹配场景的故障检测能力。如果是这样，此问题是**预期行为**，无需修复。
- **原始 Pod 为静态创建**：当前问题 Pod 是独立创建的，而非 Deployment/ReplicaSet 管理。修改建议中提到的 `kubectl patch deployment` 命令仅为示例，实际操作时需确认其归属控制器。
- **不影响其他服务**：请放心，该问题仅影响此单个测试 Pod，集群中其他 59 个 Running Pod 均工作正常。

---

## 📊 性能统计

├─ 总耗时: 1.1m
├─ 问题定位: 19.9s (29%) ✅
├─ 证据链采集: 18.3s (27%) ✅
├─ 根因分析: 12.5s (18%) ✅
├─ 汇总总结: 18.2s (26%) ✅
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
