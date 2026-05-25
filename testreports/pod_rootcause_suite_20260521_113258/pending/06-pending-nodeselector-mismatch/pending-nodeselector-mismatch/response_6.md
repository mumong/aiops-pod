======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: f84a1482cbc94c0a]

📍 [问题定位] 执行中...
   💭 [问题定位] 让我先全局扫描整个集群的 Pod 状态，看看有没有异常。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 我看到有一个异常 Pod，让我进一步查看它的详细信息。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  3m3s  default-scheduler  0/3 nodes are available: 3 node(s) did
   💭 [问题定位] 现在让我获取对应的 runbook 参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 已经掌握全部信息，以下是分析结果。

---

## 集群 Pod 异常分析

### 全局扫描结果

| 状态 | 数量 |
|------|------|
| Running | 59 |
| Pending | 1 |
| **总计** | **65** |

集群整体健康，**59 个 Pod 正常运行**，仅发现 **1 个异常 Pod**。

---

### 异常 Pod 详情

| 字段 | 值 |
|------|-----|
| **Pod** | `rc-pending-nodeselector` |
| **命名空间** | `aiops-e2e` |
| **状态** | `Pending` |
| **READY** | 0/1 |
| **调度失败原因** | `FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` |
| **Node-Selector** | `aiops.e2e/nonexistent-node-label=true` |

### 诊断结论

**`pod_abnormal_type`**: PendingUnschedulable  
**`status_category`**: scheduling  
**`layer`**: L1（调度约束不匹配）

**根本原因**: Pod 设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，集群中 **3 个节点均不包含此标签**，导致没有任何节点可以调度该 Pod。

---

### 异常分组

| 异常组 | Pod | 原因 |
|--------|-----|------|
| **PendingUnschedulable** | `rc-pending-nodeselector` | nodeSelector 不匹配，无可用节点 |

### 可能场景

1. **nodeSelector 标签拼写错误** — 设置的标签 `aiops.e2e/nonexistent-node-label=true` 在集群中不存在
2. **节点未正确打标** — 期望运行此工作负载的节点缺少预期标签
3. **测试/演练场景** — Pod 带有 `rootcause-e2e=true` 标签，可能为 E2E 测试用例

### 关键实体

- **异常 Pod**: `aiops-e2e/rc-pending-nodeselector`
- **节点**: 集群共有 3 个节点，均无匹配标签
- **调度约束**: `nodeSelector: aiops.e2e/nonexistent-node-label=true`

### 建议修复方向（需下游执行）

- 确认 Pod 应该调度到哪些节点，为目标节点添加标签：`kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`
- 或移除/修改 Pod 的 nodeSelector 约束
   ✅ [问题定位] 完成 (19.1s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector标签拼写错误', 'probability': '高', 'reason': '设置的标签 aiops.e2e/nonexistent-node-label=true 在集群中不存在，3个节点均不匹配'}, {'scenario': '节点未正确打标', 'probability': '中', 'reason': '期望运行此工作负载的节点缺少预期标签'}, {'scenario': '测试/演练场景', 'probability': '中', 'reason': 'Pod带有 rootcause-e2e=true 标签，可能为E2E测试用例'}]
   entities=[{"type": "pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "node", "name": "集群3个节点", "namespace": ""}, {"type": "label", "name": "aiops.e2e/nonexistent-node-label=true", "namespace": ""}]
   reasoning=集群中发现1个Pending Pod (rc-pending-nodeselector)，调度失败原因为nodeSelector/affinity不匹配（3个节点均无对应标签）。根据五层模型，调度约束不匹配属于L1（调度/节点kubelet层）。pod_abnormal_type=PendingUnschedulable，status_category=scheduling。集群其余59个Pod正常运行，节点均Ready。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "调度约束不匹配", "confidence": 1.0, "reasoning": "集群中发现1个Pending Pod (rc-pending-nodeselector)，调度失败原因为nodeSelector/affinity不匹配（3个节点均无对应标签）。根据五层模型，调度约束不匹配属于L1（调度/节点kubelet层）。pod_abnormal_type=PendingUnschedulable，status_category=scheduling。集群其余59个Pod正常运行，节点均Ready。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "node", "name": "集群3个节点", "namespace": ""}, {"type": "label", "name": "aiops.e2e/nonexistent-node-label=true", "namespace": ""}], "possible_scenarios": [{"scenario": "nodeSelector标签拼写错误", "probability": "高", "reason": "设置的标签 aiops.e2e/nonexistent-node-label=true 在集群中不存在，3个节点均不匹配"}, {"scenario": "节点未正确打标", "probability": "中", "reason": "期望运行此工作负载的节点缺少预期标签"}, {"scenario": "测试/演练场景", "probability": "中", "reason": "Pod带有 rootcause-e2e=true 标签，可能为E2E测试用例"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              3m1s    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/f84a1482cbc94c0a/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/f84a1482cbc94c0a/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/f84a1482cbc94c0a/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 100%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我已收到既有 evidence_plan，现在开始执行。先获取 runbook 参考信息，同时启动 Pod 的 describe 检查。
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 调用工具: kubectl_describe
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
  Warning  FailedScheduling  3m28s  default-scheduler  0/3 nodes are available: 3 node(s) di
   💭 [证据链采集] Pod 的 describe 已确认关键信息。接下来执行节点标签检查和 Pod YAML 获取。
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 调用工具: kubectl_get_yaml
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
   💭 [证据链采集] 现在采集 Pod 的事件作为补充证据。
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
3m33s       Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are
   💭 [证据链采集] 全部关键证据已采集完毕，汇总如下：

---

## 证据采集结论

### 已采集证据

| 证据维度 | 工具 | 结果摘要 |
|---------|------|---------|
| **Pod 当前状态** | `kubectl_describe` | Pod `rc-pending-nodeselector` 仍处于 **Pending** 状态，未绑定节点（`node: <none>`） |
| **FailedScheduling 原文** | `kubectl_describe` + `kubectl_events` | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` |
| **nodeSelector 配置** | `kubectl_get_yaml` | `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}` |
| **节点标签验证** | `kubectl_get_by_kind_in_cluster` | 3个节点（master/node1/node2）均 **无** `aiops.e2e/nonexistent-node-label` 标签；所有节点均 Ready |
| **Pod 不含 PVC 依赖** | `kubectl_get_yaml` | volumes 仅有 `kube-api-access-w74s5`（ServiceAccount token），无 PVC 依赖，排除存储分支 |
| **imagePullPolicy=Never** | `kubectl_get_yaml` | busybox:1.36 镜像的 pullPolicy=Never，但 Pod 未调度到节点所以不会触发拉取，不影响当前 Pending |

### 根因判定

根据 runbook `pod-pending-unschedulable.md` 判定规则：
- **FailedScheduling** + **`node(s) didn't match node selector`** → **调度约束不匹配** → 置信度 **高**
- Pod 设置 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，而集群3个节点（master/node1/node2）均无此标签
- 所有节点 Ready，无资源不足、taint 或端口冲突迹象

**根因：Pod 的 nodeSelector 引用了一个不存在的标签 `aiops.e2e/nonexistent-node-label=true`，3个节点均未匹配此标签，导致调度器无法放置 Pod。**

### 建议修复方案
- **方案1（推荐）**：检查预期运行此 Pod 的节点，为其添加标签 `kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`
- **方案2**：如果该 Pod 无需特定节点标签，删除或修正 Pod spec 中的 `nodeSelector` 字段
- **方案3**：如果此 Pod 是 E2E 测试用例（特征：`rootcause-e2e=true` 标签），确认测试场景预期即为验证 nodeSelector 不匹配的排障能力
   ✅ [证据链采集] 完成 (22.8s)
   📤 → 下游数据: evidence_items=6/7
   evidence_analysis={"evidence_plan":[{"id":"e1-describe-pod","description":"kubectl describe Pod rc-pending-nodeselector 确认 FailedScheduling 事件和 nodeSelector 配置","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"确认Pod当前仍Pending，验证FailedScheduling事件的详细原因和nodeSelector配置","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2-check-nodes-labels","description":"查看所有节点标签确认是否存在 aiops.e2e/nonexistent-node-label 标签","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes --show-labels","tool_args":{"kind":"nodes"},"purpose":"验证所有节点是否有 aiops.e2e/nonexistent-node-label=true 标签","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3-check-pod-events","description":"获取集群事件确认调度异常相关事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-nodeselector","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-pending-nodeselector"},"purpose":"采集FailedScheduling事件的完整原文","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4-pod-yaml","description":"获取Pod完整YAML确认nodeSelector和调度配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e","format":"yaml"},"purpose":"验证nodeSelector字段内容和调度约束配置","evidence_type":"","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e5-runbook-ref","description":"引用已确认的Pod调度失败runbook作为参考","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","tool_args":{"runbook_name":"pod-pending-unschedulable.md"},"purpose":"获取runbook参考信息辅助判断调度失败场景","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod PendingUnschedulable / 调度失败\n\n> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | Pending，且 Events 含 `FailedScheduling` |\n| 资源不足 | `Insufficient cpu/memory/ephemeral-storage`、`Too many pods` |\n| 调度约束 | nodeSelector/affinity 不匹配、节点 taint 未被 toleration 容忍 |\n| 存储前置条件 | `pod has unbound immediate PersistentVolumeClaims` 应切换到 pod-volume-mount-failed |\n| 节点状态 | Node NotReady/Unknown、SchedulingDisabled、Unschedulable 会导致无可用调度节点 |\n\n## 根因分流\n- 资源不足: FailedScheduling 原文含 Insufficient cpu/memory/ephemeral-storage、Too many pods。\n- hostPort 冲突: 原文含 `didn't have free ports for the requested pod ports`，说明目标节点端口已被占用。\n- Taint/Toleration 不匹配: 原文含 `had untolerated taint`，必须检查 Pod tolerations 和 Node taints。\n- nodeSelector / nodeAffinity / podAffinity 不匹配: 原文含 `didn't match Pod's node affinity/selector` 或 affinity/anti-affinity。\n- PVC 未绑定: 原文含 `unbound immediate PersistentVolumeClaims`，根因在存储绑定而不是调度资源。\n- 节点不可调度: Node Ready=False/Unknown、SchedulingDisabled、`node.kubernetes.io/not-ready` 或 `node.kubernetes.io/unreachable`。\n- 镜像、挂载、容器启动错误不会表现为 FailedScheduling；如果 Pod 已绑定 nodeName，应切换到对应 runbook。\n\n## 诊断流程\n\n### Step 1: 确认 Pod 调度失败事件\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n关注 Events 中的 `FailedScheduling` 原文。\n\n### Step 2: 检查 Pod 调度约束\n```bash\nkubectl get pod <pod-name> -n <namespace> -o yaml\n```\n关注: spec.nodeName 是否为空、nodeSelector、affinity、tolerations、topologySpreadConstraints、schedulerName、priorityClassName、resource requests、hostNetwork/hostPort。\n\n### Step 3: 检查节点状态和可调度性\n```bash\nkubectl get nodes -o wide\n```\n关注: STATUS 列是否有 NotReady/Unknown，AGE 判断是否新节点\n\n### Step 4: 检查候选节点详情\n```bash\nkubectl describe node <node-name>\n```\n重点关注:\n- `Conditions` 部分: Ready=False/Unknown 的 reason 和 message\n- `Taints` 部分: 是否有 NoSchedule/NoExecute taint\n- `Allocatable` vs `Capacity`: 资源是否耗尽\n- `Non-terminated Pods`: 节点上运行的 Pod 数量\n\n### Step 5: 检查 PVC 状态（如果 FailedScheduling 指向 PVC）\n```bash\nkubectl get pvc -n <namespace>\nkubectl describe pvc <pvc> -n <namespace>\n```\n关注: Pending、StorageClass、volumeBindingMode、ProvisioningFailed。\n\n### Step 6: 检查 Ready 条件详情\n```bash\nkubectl get node <node-name> -o jsonpath='{.status.conditions[?(@.type==\"Ready\")]}' | python3 -m json.tool\n```\n关注: status, reason, message, lastHeartbeatTime\n\n### Step 7: 检查节点事件\n```bash\nkubectl get events -A --field-selector involvedObject.kind=Node,involvedObject.name=<node-name> --sort-by='.lastTimestamp'\n```\n关注: NodeNotReady、NodeNotSchedulable、PLEG unhealthy 等事件\n\n### Step 8: 检查受影响的 Pending Pod\n```bash\nkubectl get pods -A --field-selector status.phase=Pending | head -20\n```\n\n## 判定规则\n\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| FailedScheduling + Insufficient cpu/memory | 资源不足导致 Pod Pending | 高 |\n| FailedScheduling + Too many pods | 节点 Pod 数量上限导致 Pending | 高 |\n| FailedScheduling + didn't have free ports for the requested pod ports | hostPort 端口冲突导致 Pending | 高 |\n| FailedScheduling + had untolerated taint | taint/toleration 不匹配 | 高 |\n| FailedScheduling + node(s) didn't match node selector/affinity | 调度约束不匹配 | 高 |\n| FailedScheduling + pod has unbound immediate PersistentVolumeClaims | PVC 未绑定，应切换 VolumeMountFailed/PVC 分支 | 高 |\n| 所有候选 Node NotReady/Unschedulable | 无可用调度节点 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f84a1482cbc94c0a/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f84a1482cbc94c0a/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f84a1482cbc94c0a/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  3m28s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  3m28s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f84a1482cbc94c0a/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f84a1482cbc94c0a/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f84a1482cbc94c0a/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f84a1482cbc94c0a/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f84a1482cbc94c0a/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f84a1482cbc94c0a/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   238d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          238d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\nnode2    Ready    <none>          238d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f84a1482cbc94c0a/tools/004-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f84a1482cbc94c0a/tools/004-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f84a1482cbc94c0a/tools/004-evidence-kubectl_get_by_kind_in_cluster.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n3m33s       Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f84a1482cbc94c0a/tools/005-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f84a1482cbc94c0a/tools/005-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f84a1482cbc94c0a/tools/005-evidence-kubectl_events.summary.txt"}],"llm_analysis":"全部关键证据已采集完毕，汇总如下：\n\n---\n\n## 证据采集结论\n\n### 已采集证据\n\n| 证据维度 | 工具 | 结果摘要 |\n|---------|------|---------|\n| **Pod 当前状态** | `kubectl_describe` | Pod `rc-pending-nodeselector` 仍处于 **Pending** 状态，未绑定节点（`node: <none>`） |\n| **FailedScheduling 原文** | `kubectl_describe` + `kubectl_events` | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` |\n| **nodeSelector 配置** | `kubectl_get_yaml` | `nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}` |\n| **节点标签验证** | `kubectl_get_by_kind_in_cluster` | 3个节点（master/node1/node2）均 **无** `aiops.e2e/nonexistent-node-label` 标签；所有节点均 Ready |\n| **Pod 不含 PVC 依赖** | `kubectl_get_yaml` | volumes 仅有 `kube-api-access-w74s5`（ServiceAccount token），无 PVC 依赖，排除存储分支 |\n| **imagePullPolicy=Never** | `kubectl_get_yaml` | busybox:1.36 镜像的 pullPolicy=Never，但 Pod 未调度到节点所以不会触发拉取，不影响当前 Pending |\n\n### 根因判定\n\n根据 runbook `pod-pending-unschedulable.md` 判定规则：\n- **FailedScheduling** + **`node(s) didn't match node selector`** → **调度约束不匹配** → 置信度 **高**\n- Pod 设置 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，而集群3个节点（master/node1/node2）均无此标签\n- 所有节点 Ready，无资源不足、taint 或端口冲突迹象\n\n**根因：Pod 的 nodeSelector 引用了一个不存在的标签 `aiops.e2e/nonexistent-node-label=true`，3个节点均未匹配此标签，导致调度器无法放置 Pod。**\n\n### 建议修复方案\n- **方案1（推荐）**：检查预期运行此 Pod 的节点，为其添加标签 `kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`\n- **方案2**：如果该 Pod 无需特定节点标签，删除或修正 Pod spec 中的 `nodeSelector` 字段\n- **方案3**：如果此 Pod 是 E2E 测试用例（特征：`rootcause-e2e=true` 标签），确认测试场景预期即为验证 nodeSelector 不匹配的排障能力","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 5/6 项，完整度 83%；实际执行工具 6 个，匹配计划 4 个，未规划证据 2 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":6,"environment_evidence_collected":5,"environment_evidence_completeness":0.8333333333333334,"executed_tool_count":6,"matched_tool_count":4,"unplanned_tool_count":2,"evidence_inventory":[{"id":"e1-describe-pod","description":"kubectl describe Pod rc-pending-nodeselector 确认 FailedScheduling 事件和 nodeSelector 配置","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"确认Pod当前仍Pending，验证FailedScheduling事件的详细原因和nodeSelector配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-check-nodes-labels","description":"查看所有节点标签确认是否存在 aiops.e2e/nonexistent-node-label 标签","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes --show-labels","purpose":"验证所有节点是否有 aiops.e2e/nonexistent-node-label=true 标签","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3-check-pod-events","description":"获取集群事件确认调度异常相关事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-nodeselector","purpose":"采集FailedScheduling事件的完整原文","collected":false,"source":"planned","outcome":"unknown"},{"id":"e4-pod-yaml","description":"获取Pod完整YAML确认nodeSelector和调度配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"验证nodeSelector字段内容和调度约束配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5-runbook-ref","description":"引用已确认的Pod调度失败runbook作为参考","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","purpose":"获取runbook参考信息辅助判断调度失败场景","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["e3-check-pod-events(获取集群事件确认调度异常相关事件): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 83%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1-describe-pod | critical | ✅ | kubectl_describe | kubectl describe Pod rc-pending-nodeselector ... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e2-check-node... | critical | ✅ | kubectl_get_by_kind_in_cl... | 查看所有节点标签确认是否存在 aiops.e2e/nonexistent-node-lab... | `kubectl get nodes --show-labels` |
   | e3-check-pod-... | important | ❌ | kubectl_events | 获取集群事件确认调度异常相关事件 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pendi...` |
   | e4-pod-yaml | important | ✅ | kubectl_get_yaml | 获取Pod完整YAML确认nodeSelector和调度配置 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e5-runbook-ref | reference | ✅ | fetch_runbook | 引用已确认的Pod调度失败runbook作为参考 | `fetch_runbook pod-pending-unschedulable.md` |

   ⚠️ 未采集原因:
   - e3-check-pod-events(获取集群事件确认调度异常相关事件): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (23.9s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector (namespace: aiops-e2e) 处于 Pending 状态的根本原因是 nodeSelector 引用了集群中不存在的标签。具体证据：kubectl_describe 显示 nodeSelector 为 aiops.e2e/nonexistent-node-label=true；kubectl_get_yaml 确认 nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}；节点标签检查显示 3 个节点（master、node1、node2）均 Ready 但均无该标签；FailedScheduling 事件原文 "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector" 直接验证了调度约束不匹配。集群其余 59 个 Pod 正常运行，无其他异常。
   confidence=98%
   causal_chain={"root_cause": "Pod rc-pending-nodeselector 的 spec.nodeSelector 中设置了标签 aiops.e2e/nonexistent-node-label=true，但集群 3 个节点（master、node1、node2）均未打该标签，导致调度器无法找到任何匹配节点。", "propagation": "调度器 default-scheduler 遍历 3 个节点，逐一检查节点标签是否匹配 Pod 的 nodeSelector 约束 → 3 个节点均不满足条件 → 调度器报告 FailedScheduling 事件 → 调度队列将 Pod 标记为不可调度 → Pod 持续保持 Pending 状态。", "direct_cause": "3 个节点均未匹配 Pod 的 nodeSelector 约束：nodeSelector 配置为 aiops.e2e/nonexistent-node-label=true，但所有节点标签中不存在该键值对。", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续 Pending，node=&lt;none&gt;，Events 中出现 Warning FailedScheduling，调度器消息明确指出 '3 node(s) didn't match Pod's node affinity/selector'。"}
   rca_analysis={"phenomenon": "集群 aiops-e2e 命名空间中 Pod rc-pending-nodeselector 处于 Pending 状态，pod_abnormal_type=PendingUnschedulable，status_category=scheduling。该 Pod 创建时间约 3 分 28 秒，未分配到节点（node: &lt;none&gt;），集群其余 59 个 Pod 均正常 Running，3 个节点均 Ready。", "evidence_inventory": [{"id": "e1-describe-pod", "source": "kubectl_describe", "content": "Pod rc-pending-nodeselector 状态 Pending，node=&lt;none&gt;，FailedScheduling 事件原文：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}, {"id": "e2-check-nodes-labels", "source": "kubectl_get_by_kind_in_cluster", "content": "3 个节点（master/node1/node2）均 Ready，LABELS 中均不含 aiops.e2e/nonexistent-node-label 标签", "reliability": "高"}, {"id": "e4-pod-yaml", "source": "kubectl_get_yaml", "content": "Pod 完整 YAML 确认 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}，无 PVC 依赖，nodeName=None，phase=Pending", "reliability": "高"}, {"id": "e5-runbook-ref", "source": "fetch_runbook", "content": "Runbook 判定规则：FailedScheduling + node(s) didn't match node selector → 调度约束不匹配，置信度高", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "集群 Pod 总数 65，异常 1（Pending），其余 59 个 Running", "reliability": "高"}, {"id": "layer_2", "source": "kubectl_describe", "content": "FailedScheduling 事件确认：0/3 nodes available，3 nodes didn't match node affinity/selector", "reliability": "高"}, {"id": "e3-check-pod-events", "source": "kubectl_events", "content": "集群事件确认：3m33s Warning FailedScheduling Pod/rc-pending-nodeselector - 0/3 nodes available，3 nodes didn't match node affinity/selector", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1-describe-pod", "raw_data": "kubectl_describe 摘要: node: <none>, status: Pending, Node-Selectors: aiops.e2e/nonexistent-node-label=true, Warning FailedScheduling 3m28s default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.", "interpretation": "Pod 明确处于 Pending 状态且未分配到任何节点，FailedScheduling 事件明确指向 node affinity/selector 不匹配，而非资源不足或 taint 问题。"}, {"evidence_id": "e2-check-nodes-labels", "raw_data": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}, master/node1/node2 LABELS 中均无 aiops.e2e/nonexistent-node-label", "interpretation": "三个节点均健康 Ready，但全部缺少 Pod 所需的 aiops.e2e/nonexistent-node-label=true 标签，这是调度器无法匹配任何节点的直接原因。"}, {"evidence_id": "e4-pod-yaml", "raw_data": "kubectl_get_yaml 关键字段: nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}, nodeName: None, phase: Pending, volumes: 仅有 kube-api-access-w74s5 (无PVC)", "interpretation": "Pod YAML 确认 nodeSelector 引用了标签 aiops.e2e/nonexistent-node-label=true，且不含 PVC 依赖，排除存储未绑定场景。nodeName=None 证实从未被调度。"}, {"evidence_id": "e5-runbook-ref", "raw_data": "Runbook 判定规则: FailedScheduling + `node(s) didn't match node selector` → 调度约束不匹配 → 置信度高", "interpretation": "Runbook 判定规则与实际情况完全吻合，验证了根因诊断方向的正确性。"}, {"evidence_id": "layer_1", "raw_data": "kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}", "interpretation": "集群整体健康，仅此一 Pod 异常，异常范围明确，无并发异常事件。"}, {"evidence_id": "layer_2", "raw_data": "kubectl_describe 摘要: Warning FailedScheduling 3m3s default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.", "interpretation": "与 e1 一致，确认调度失败的根本原因是 node affinity/selector 不匹配，排除资源不足、taint、hostPort 冲突等场景。"}, {"evidence_id": "e3-check-pod-events", "raw_data": "kubectl_events 摘要: 3m33s Warning FailedScheduling Pod/rc-pending-nodeselector 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.", "interpretation": "集群事件独立验证了 FailedScheduling 事件的详细内容，与 kubectl_describe 结果一致。"}], "causal_chain": {"root_cause": "Pod rc-pending-nodeselector 的 spec.nodeSelector 中设置了标签 aiops.e2e/nonexistent-node-label=true，但集群 3 个节点（master、node1、node2）均未打该标签，导致调度器无法找到任何匹配节点。", "propagation": "调度器 default-scheduler 遍历 3 个节点，逐一检查节点标签是否匹配 Pod 的 nodeSelector 约束 → 3 个节点均不满足条件 → 调度器报告 FailedScheduling 事件 → 调度队列将 Pod 标记为不可调度 → Pod 持续保持 Pending 状态。", "direct_cause": "3 个节点均未匹配 Pod 的 nodeSelector 约束：nodeSelector 配置为 aiops.e2e/nonexistent-node-label=true，但所有节点标签中不存在该键值对。", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续 Pending，node=&lt;none&gt;，Events 中出现 Warning FailedScheduling，调度器消息明确指出 '3 node(s) didn't match Pod's node affinity/selector'。"}, "root_cause": "Pod rc-pending-nodeselector (namespace: aiops-e2e) 处于 Pending 状态的根本原因是 nodeSelector 引用了集群中不存在的标签。具体证据：kubectl_describe 显示 nodeSelector 为 aiops.e2e/nonexistent-node-label=true；kubectl_get_yaml 确认 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}；节点标签检查显示 3 个节点（master、node1、node2）均 Ready 但均无该标签；FailedScheduling 事件原文 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\" 直接验证了调度约束不匹配。集群其余 59 个 Pod 正常运行，无其他异常。", "root_cause_summary": "Pod rc-pending-nodeselector (namespace: aiops-e2e) 处于 Pending 状态的根本原因是 nodeSelector 引用了集群中不存在的标签。具体证据：kubectl_describe 显示 nodeSelector 为 aiops.e2e/nonexistent-node-label=true；kubectl_get_yaml 确认 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}；节点标签检查显示 3 个节点（master、node1、node2）均 Ready 但均无该标签；FailedScheduling 事件原文 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\" 直接验证了调度约束不匹配。集群其余 59 个 Pod 正常运行，无其他异常。", "confidence": 0.98, "confidence_reason": "直接证据链完整：kubectl_describe（Pod 状态 + FailedScheduling 事件 + nodeSelector 原文）+ kubectl_get_yaml（YAML 确认 nodeSelector）+ 节点标签检查（3 节点均无该标签）+ kubectl_events（独立验证事件）。所有证据相互印证，因果链清晰无歧义，runbook 判定规则完全匹配。", "primary_runbooks": [], "alternative_causes": [{"cause": "资源不足（CPU/内存不足）", "probability": "low", "reason": "FailedScheduling 原文无 Insufficient cpu/memory 关键字，且 3 个节点均 Ready，集群仅运行 59 个 Running Pod，排除资源不足。"}, {"cause": "Taint/Toleration 不匹配", "probability": "low", "reason": "FailedScheduling 原文无 had untolerated taint 关键字，且 Pod 已配置 tolerations（node.kubernetes.io/not-ready:NoExecute），排除 taint 不匹配。"}, {"cause": "PVC 未绑定或卷依赖未满足", "probability": "low", "reason": "FailedScheduling 原文无 unbound immediate PersistentVolumeClaims 关键字，kubectl_get_yaml 确认 Pod volumes 仅含 kube-api-access-w74s5（ServiceAccount token），无 PVC 依赖。"}, {"cause": "hostPort 端口冲突", "probability": "low", "reason": "FailedScheduling 原文无 didn't have free ports 关键字，排除 hostPort 冲突。"}], "limitations": "已采集的证据充分覆盖了根因分析所需的所有关键维度。缺失证据 e3-check-pod-events 已通过 kubectl_events 间接补充采集并确认与 kubectl_describe 一致。未检查 Pod 的 priorityClassName 和 topologySpreadConstraints，但基于 FailedScheduling 原文（明确指向 node affinity/selector），这些字段不影响当前根因判定。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector (namespace: aiops-e2e) 处于 Pending 状态的根本原因是 nodeSelector 引用了集群中不存在的标签。具体证据：kubectl_describe 显示 nodeSelector 为 aiops.e2e/non...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod rc-pending-nodeselector 的 spec.nodeSelector 中设置了标签 aiops.e2e/nonexistent-node-label=true，但集群 3 个节点（master、node1、node2）均未打该标签，导致调度器无法找到任何匹配节点。
     传导机制: 调度器 default-scheduler 遍历 3 个节点，逐一检查节点标签是否匹配 Pod 的 nodeSelector 约束 → 3 个节点均不满足条件 → 调度器报告 FailedScheduling 事件 → 调度队列将 Pod 标记为不可调度 → Pod 持续保持 Pending 状态。
     最终表现: Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续 Pending，node=&lt;none&gt;，Events 中出现 Warning FailedScheduling，调度器消息明确指出 '3 node(s) didn't match Pod's node affinity/selector'。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (24.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5999 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 30.4s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将为您分析集群现状并就发现的问题生成详尽报告。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **集群整体状态** | 集群共 65 个 Pod，59 个正常运行，3 个节点均 Ready。存在 **1 个异常 Pod**。 |
| **主要问题** | Pod `rc-pending-nodeselector` 处于 **Pending** 状态，无法调度。 |
| **Pod异常状态** | Pending (PendingUnschedulable) |
| **兼容归因层** | L1 - 调度/节点kubelet层 |
| **问题分类** | nodeSelector 不匹配导致调度失败 |
| **置信度** | 高 (98%) |
| **证据完整度** | 3/4 (75%) |

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-pending-nodeselector |
| Namespace | aiops-e2e |
| Node | `<none>` (未调度到任何节点) |
| 错误信息 | `FailedScheduling`: 3 node(s) didn't match Pod's node affinity/selector. |

---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态与事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | `Warning FailedScheduling ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 调度器确认 3 个节点均不满足 Pod 的调度约束 |
| 2 | Pod 配置 (YAML) | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` | `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}` | Pod 配置了一个名为 `aiops.e2e/nonexistent-node-label` 且值为 `true` 的节点选择器 |
| 3 | 节点信息 | `kubectl get nodes -o wide` | 3 个节点 (master, node1, node2) 均 `Ready`；标签列表显示 `kubernetes.io/hostname=master/node1/node2` 等，均 **不包含** `aiops.e2e/nonexistent-node-label` 标签 | 集群中没有任何节点拥有 Pod 所需的标签 |
| 4 | 集群事件 | `kubectl events --for pod/rc-pending-nodeselector -n aiops-e2e` | `3m33s Warning FailedScheduling Pod/rc-pending-nodeselector 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..` | 事件记录与 `kubectl describe` 结果一致，进一步排除了抢占调度的可能性 |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：Pod 要求调度到 `aiops.e2e/nonexistent-node-label=true` 的节点，但集群中三个 Ready 节点均无此标签，导致调度器无法找到匹配节点。
- **证据链**：`nodeSelector` 约束 (`aiops.e2e/nonexistent-node-label=true`) → 调度器检查 3 个节点 → 所有节点标签均不匹配 → 产生 `FailedScheduling` 事件 → Pod 持续 Pending。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| N/A | - | 所有关键证据均已通过 `kubectl describe`、`kubectl get nodes` 和集群事件间接或直接采集，证据链完整。 |

---
## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                    │
│ Pod rc-pending-nodeselector 的 spec.nodeSelector 配置了一个集群中           │
│ 不存在的标签: aiops.e2e/nonexistent-node-label=true                        │
└─────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                    │
│ 1. 调度器 default-scheduler 尝试将 Pod 绑定到节点                            │
│ 2. 调度器遍历 3 个节点的标签，与 Pod 的 nodeSelector 进行匹配               │
│ 3. 3 个节点均不包含 aiops.e2e/nonexistent-node-label 标签                    │
│ 4. 调度器标记 Pod 为不可调度，并生成 FailedScheduling 事件                    │
└─────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                    │
│ 3 个节点均不符合 Pod 的 nodeSelector 约束                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                │
│ Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续 Pending，            │
│ 无法被调度到任何节点上运行。                                                │
└─────────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #1 (FailedScheduling 事件)、证据 #2 (Pod YAML 中的 `nodeSelector`)、证据 #3 (节点标签列表) 以及证据 #4 (集群事件)，问题的根本原因是**Pod 配置的 `nodeSelector` 中引用了集群中不存在的标签 `aiops.e2e/nonexistent-node-label=true`**，导致调度器无法找到可以运行该 Pod 的节点。

**置信度**：高 (98%)
- ✅ `FailedScheduling` 事件直接指向 `node affinity/selector` 不匹配。
- ✅ Pod YAML 明确显示了错误的标签名。
- ✅ 节点标签输出确认了没有任何节点拥有此标签。

---
## 🛠️ 修复建议
**注意**：该 Pod 带有 `rootcause-e2e=true` 标签，可能是一个 E2E 测试用例。在操作前请确认是否需要保留此 Pod。

### 立即执行（按优先级排序）
**1. [推荐] 修复 Pod/Deployment 的 nodeSelector**
根据意图，如果希望 Pod 运行在某个特定节点上，应先检查该节点的标签，再修改 `nodeSelector`。

```bash
# 查看期望运行 Pod 的节点标签（例如 node1）
kubectl describe node node1 | grep Labels -A 20
# 假设正确的标签是 disktype=ssd
# 编辑 Pod (如果是直接创建的) 或 Deployment
# 修改 nodeSelector 内容
kubectl edit deploy <your-deployment-name> -n aiops-e2e

# 或者直接更新 deployment
# kubectl set selector deploy <your-deployment-name> -n aiops-e2e 'disktype=ssd' --local -o yaml | kubectl apply -f -
```
*依据*：根本原因是`nodeSelector`键值对错误。修复 Pod 配置是根治方案。

**2. [临时] 直接删除此测试 Pod**
如果确认该 Pod 是测试废弃的，可以将其删除。
```bash
kubectl delete pod rc-pending-nodeselector -n aiops-e2e
```
*目的*：移除集群中的异常对象，快速解决“PENDING”告警。删除后，如果是 Deploy/RS 管理，会重建；如果是裸 Pod，则彻底删除。

**3. [备选] 为节点添加标签**
如果该 Pod 的 `nodeSelector` 是正确的，并且您的意图是让具有特定标签的工作负载运行在某个或多个节点上，则应该为节点打上该标签。
```bash
# 为 node1 和 node2 添加 Pod 所需的标签
kubectl label node node1 aiops.e2e/nonexistent-node-label=true
kubectl label node node2 aiops.e2e/nonexistent-node-label=true
```
*依据*：满足 Pod 的调度约束，使其能够被调度。添加标签后，Pod 将自动被调度。

### 后续优化
1. **命名规范审查**：`aiops.e2e/nonexistent-node-label` 这个标签名带有 `e2e` 和 `nonexistent` 字样，可能是由测试工具或 CI/CD 流程错误创建。建议审查相关应用的部署配置，避免类似问题。
2. **配置校验**：在部署流水线中增加对 `nodeSelector` 等关键调度配置的静态校验，确保其引用的标签在目标集群中存在。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: `Running` 或该 Pod 已不再存在 |
| 2. 检查 Pod 调度到的节点 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o wide` | NODE 列为非 `<none>` 的具体节点名 |
| 3. 检查整体集群 Pod | `kubectl get pods -n aiops-e2e | grep -v Running` | 无异常状态 Pod |

---
## ⚠️ 注意事项
- 本集群除上述一个特定 Pod 外，其余 59 个 Pod 和 3 个节点均运行正常，不存在其他问题。
- 请根据实际业务意图选择修复方案（修复配置、删除 Pod 或给节点打标签）。

---

## 📊 性能统计

├─ 总耗时: 1.5m
├─ 问题定位: 19.1s (21%) ✅
├─ 证据链采集: 22.8s (25%) ✅
├─ 根因分析: 23.9s (26%) ✅
├─ 汇总总结: 24.5s (27%) ✅
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
