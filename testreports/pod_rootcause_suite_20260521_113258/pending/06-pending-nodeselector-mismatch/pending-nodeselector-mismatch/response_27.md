======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: a6f7680413274767]

📍 [问题定位] 执行中...
   💭 [问题定位] 让我先扫描全局 Pod 状态，看看当前集群中是否存在异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 发现了一个异常的 Pod，让我进一步查看详情。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  19m                  default-scheduler  0/3 nodes are available
   💭 [问题定位] 好的，让我获取一个匹配的 runbook 来辅助定位。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在我已经掌握了全面的信息，可以给出定位分析了。

---

## 🎯 定位分析结果

### 全局概览
集群共有 **65 个 Pod**，其中 **59 个 Running（正常）**，**1 个异常 Pending Pod**。

### 异常 Pod 详情

| 字段 | 值 |
|------|------|
| **Pod 名称** | `rc-pending-nodeselector` |
| **命名空间** | `aiops-e2e` |
| **状态** | `Pending` |
| **READY** | `0/1` |
| **绑定节点** | `<none>`（未调度） |

### 关键诊断证据
- **FailedScheduling 事件**: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.`
- **原因**: Pod 设置了 `Node-Selectors: aiops.e2e/nonexistent-node-label=true`，而集群中 **3 个节点均没有该标签**，因此没有节点可以调度。

### 异常类型判定

| 维度 | 值 |
|------|------|
| **pod_status_keyword** | `Pending` |
| **pod_abnormal_type** | `PendingUnschedulable` |
| **status_category** | `scheduling` |
| **兼容层级（layer）** | `L1` |
| **derived_layer** | `L1` |
| **layers** | `["L1"]` |
| **layer_name** | `调度约束不匹配（PendingUnschedulable）` |

### possible_scenarios
1. **nodeSelector 不匹配**（高置信度）：`aiops.e2e/nonexistent-node-label=true` 标签在所有节点上均不存在，导致调度器无法放置该 Pod。
2. **测试/验证场景**：该 Pod 带有 `rootcause-e2e=true` 标签，疑似为 E2E 测试故意构造的异常场景。

### abnormal_pods
- `aiops-e2e/rc-pending-nodeselector`（Pending）

### abnormal_groups
- **PendingUnschedulable**: `[aiops-e2e/rc-pending-nodeselector]`

### key_entities
- **Pod**: `aiops-e2e/rc-pending-nodeselector`
- **NodeSelector**: `aiops.e2e/nonexistent-node-label=true`
- **Scheduler 事件**: FailedScheduling — nodeSelector/affinity 不匹配

### 置信度
**高（High）** — FailedScheduling 事件原文直接指出 nodeSelector/affinity 不匹配，证据确凿。
   ✅ [问题定位] 完成 (20.2s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector 不匹配', 'probability': '高', 'reason': 'Pod 设置了 Node-Selectors: aiops.e2e/nonexistent-node-label=true，集群3个节点均无该标签，FailedScheduling 事件直接指出 node affinity/selector 不匹配'}, {'scenario': '测试/验证场景', 'probability': '中', 'reason': 'Pod 带有 rootcause-e2e=true 标签，可能是 E2E 测试构造的异常场景'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "NodeSelector", "name": "aiops.e2e/nonexistent-node-label=true", "namespace": ""}]
   reasoning=集群中有1个异常Pod: aiops-e2e/rc-pending-nodeselector，状态为Pending，READY 0/1，未绑定节点（node=&lt;none&gt;）。FailedScheduling事件明确指出"3 node(s) didn't match Pod's node affinity/selector"，Pod设置了Node-Selectors: aiops.e2e/nonexistent-node-label=true，而集群3个节点均没有该标签，导致调度失败。无其他层级的异常证据（无OOM、无镜像拉取失败、无应用错误、无节点NotReady），根因明确为调度约束不匹配，属于L1层级。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "调度约束不匹配（PendingUnschedulable）", "confidence": 0.95, "reasoning": "集群中有1个异常Pod: aiops-e2e/rc-pending-nodeselector，状态为Pending，READY 0/1，未绑定节点（node=&lt;none&gt;）。FailedScheduling事件明确指出\"3 node(s) didn't match Pod's node affinity/selector\"，Pod设置了Node-Selectors: aiops.e2e/nonexistent-node-label=true，而集群3个节点均没有该标签，导致调度失败。无其他层级的异常证据（无OOM、无镜像拉取失败、无应用错误、无节点NotReady），根因明确为调度约束不匹配，属于L1层级。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "NodeSelector", "name": "aiops.e2e/nonexistent-node-label=true", "namespace": ""}], "possible_scenarios": [{"scenario": "nodeSelector 不匹配", "probability": "高", "reason": "Pod 设置了 Node-Selectors: aiops.e2e/nonexistent-node-label=true，集群3个节点均无该标签，FailedScheduling 事件直接指出 node affinity/selector 不匹配"}, {"scenario": "测试/验证场景", "probability": "中", "reason": "Pod 带有 rootcause-e2e=true 标签，可能是 E2E 测试构造的异常场景"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              19m     <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/a6f7680413274767/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/a6f7680413274767/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/a6f7680413274767/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我来按既有 evidence_plan 执行工具调用。先执行相互独立的工具调用。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: run_bash_command
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
19m                  Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  19m                 default-scheduler  0/3 nodes are available:
   💭 [证据链采集] 所有工具调用已完成，现在对采集到的证据进行汇总分析。

---

## 证据采集结论

### ✅ 已采集证据摘要

**e1 - Pod Describe（critical）✅**
Pod `rc-pending-nodeselector` 状态为 **Pending**，未绑定节点（node=`<none>`）。  
关键配置：
- **Node-Selectors**: `aiops.e2e/nonexistent-node-label=true`
- **Image**: `busybox:1.36`（imagePullPolicy=Never）
- **QoS Class**: BestEffort

**e2 - Pod Events（important）✅**
两次 `FailedScheduling` 事件，原文一致：
> `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.`

**e3 - Pod YAML（critical）✅**
YAML 确认：
- `spec.nodeSelector` = `{"aiops.e2e/nonexistent-node-label": "true"}`
- `status.phase` = `Pending`
- `status.conditions[].reason` = `Unschedulable`
- 无 `deletionTimestamp`，无 `finalizers`，无 PVC 引用

**e4 - Node Labels（important）✅**
集群共 **3 个节点**（master/node1/node2），均为 **Ready** 状态，**没有任何节点**包含 `aiops.e2e/nonexistent-node-label` 标签。

**e5 - Runbook（reference）✅**
Runbook 判定规则匹配：`FailedScheduling + node(s) didn't match node selector/affinity` → **调度约束不匹配（高置信度）**。

### 🎯 根因结论

| 维度 | 结果 |
|------|------|
| **根本原因** | Pod 设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，但集群3个节点均无该标签，调度器无法放置 |
| **调度器原文** | `3 node(s) didn't match Pod's node affinity/selector` |
| **节点状态** | 3节点均为 Ready，资源正常，非节点故障 |
| **Pod 配置** | 无 PVC、无资源请求（BestEffort），无 hostPort，排除了其他调度因素 |
| **置信度** | **高** — FailedScheduling 原文+Pod spec+Node labels 三者完全吻合 |

### ❌ 冲突/负向证据
无。所有工具均正确定位到目标对象，证据链一致。

### ⛔ 未采集证据
无。已有证据已完整覆盖异常根因，不需要额外采集。
   ✅ [证据链采集] 完成 (20.4s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1-g1-describe","description":"describe异常Pod rc-pending-nodeselector，确认当前状态、Events中的FailedScheduling原文、nodeSelector配置","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"确认FailedScheduling事件原文和nodeSelector配置","evidence_type":"Pod状态与事件","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2-g1-events","description":"获取异常Pod的Events，确认调度失败事件详情","level":"important","tool":"kubectl_events","command":"kubectl events --for pod/rc-pending-nodeselector -n aiops-e2e","tool_args":{"resource_type":"pod","resource_name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"采集FailedScheduling事件原文验证调度失败根因","evidence_type":"事件","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3-g1-nodeselector","description":"获取Pod的完整YAML，提取nodeSelector配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"验证nodeSelector字段内容：aiops.e2e/nonexistent-node-label=true","evidence_type":"Pod配置","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e4-g1-nodes","description":"获取集群所有节点及其标签，验证是否存在匹配nodeSelector的节点","level":"important","tool":"run_bash_command","command":"kubectl get nodes --show-labels","tool_args":{},"purpose":"验证集群节点是否包含aiops.e2e/nonexistent-node-label=true标签","evidence_type":"节点标签","target_scope":"集群节点","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5-g1-runbook","description":"获取Pod PendingUnschedulable runbook参考","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","tool_args":{},"purpose":"参考runbook确认调度约束不匹配的典型检查步骤","evidence_type":"reference","target_scope":"reference","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod PendingUnschedulable / 调度失败\n\n> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | Pending，且 Events 含 `FailedScheduling` |\n| 资源不足 | `Insufficient cpu/memory/ephemeral-storage`、`Too many pods` |\n| 调度约束 | nodeSelector/affinity 不匹配、节点 taint 未被 toleration 容忍 |\n| 存储前置条件 | `pod has unbound immediate PersistentVolumeClaims` 应切换到 pod-volume-mount-failed |\n| 节点状态 | Node NotReady/Unknown、SchedulingDisabled、Unschedulable 会导致无可用调度节点 |\n\n## 根因分流\n- 资源不足: FailedScheduling 原文含 Insufficient cpu/memory/ephemeral-storage、Too many pods。\n- hostPort 冲突: 原文含 `didn't have free ports for the requested pod ports`，说明目标节点端口已被占用。\n- Taint/Toleration 不匹配: 原文含 `had untolerated taint`，必须检查 Pod tolerations 和 Node taints。\n- nodeSelector / nodeAffinity / podAffinity 不匹配: 原文含 `didn't match Pod's node affinity/selector` 或 affinity/anti-affinity。\n- PVC 未绑定: 原文含 `unbound immediate PersistentVolumeClaims`，根因在存储绑定而不是调度资源。\n- 节点不可调度: Node Ready=False/Unknown、SchedulingDisabled、`node.kubernetes.io/not-ready` 或 `node.kubernetes.io/unreachable`。\n- 镜像、挂载、容器启动错误不会表现为 FailedScheduling；如果 Pod 已绑定 nodeName，应切换到对应 runbook。\n\n## 诊断流程\n\n### Step 1: 确认 Pod 调度失败事件\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n关注 Events 中的 `FailedScheduling` 原文。\n\n### Step 2: 检查 Pod 调度约束\n```bash\nkubectl get pod <pod-name> -n <namespace> -o yaml\n```\n关注: spec.nodeName 是否为空、nodeSelector、affinity、tolerations、topologySpreadConstraints、schedulerName、priorityClassName、resource requests、hostNetwork/hostPort。\n\n### Step 3: 检查节点状态和可调度性\n```bash\nkubectl get nodes -o wide\n```\n关注: STATUS 列是否有 NotReady/Unknown，AGE 判断是否新节点\n\n### Step 4: 检查候选节点详情\n```bash\nkubectl describe node <node-name>\n```\n重点关注:\n- `Conditions` 部分: Ready=False/Unknown 的 reason 和 message\n- `Taints` 部分: 是否有 NoSchedule/NoExecute taint\n- `Allocatable` vs `Capacity`: 资源是否耗尽\n- `Non-terminated Pods`: 节点上运行的 Pod 数量\n\n### Step 5: 检查 PVC 状态（如果 FailedScheduling 指向 PVC）\n```bash\nkubectl get pvc -n <namespace>\nkubectl describe pvc <pvc> -n <namespace>\n```\n关注: Pending、StorageClass、volumeBindingMode、ProvisioningFailed。\n\n### Step 6: 检查 Ready 条件详情\n```bash\nkubectl get node <node-name> -o jsonpath='{.status.conditions[?(@.type==\"Ready\")]}' | python3 -m json.tool\n```\n关注: status, reason, message, lastHeartbeatTime\n\n### Step 7: 检查节点事件\n```bash\nkubectl get events -A --field-selector involvedObject.kind=Node,involvedObject.name=<node-name> --sort-by='.lastTimestamp'\n```\n关注: NodeNotReady、NodeNotSchedulable、PLEG unhealthy 等事件\n\n### Step 8: 检查受影响的 Pending Pod\n```bash\nkubectl get pods -A --field-selector status.phase=Pending | head -20\n```\n\n## 判定规则\n\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| FailedScheduling + Insufficient cpu/memory | 资源不足导致 Pod Pending | 高 |\n| FailedScheduling + Too many pods | 节点 Pod 数量上限导致 Pending | 高 |\n| FailedScheduling + didn't have free ports for the requested pod ports | hostPort 端口冲突导致 Pending | 高 |\n| FailedScheduling + had untolerated taint | taint/toleration 不匹配 | 高 |\n| FailedScheduling + node(s) didn't match node selector/affinity | 调度约束不匹配 | 高 |\n| FailedScheduling + pod has unbound immediate PersistentVolumeClaims | PVC 未绑定，应切换 VolumeMountFailed/PVC 分支 | 高 |\n| 所有候选 Node NotReady/Unschedulable | 无可用调度节点 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a6f7680413274767/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a6f7680413274767/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a6f7680413274767/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAME     STATUS   ROLES           AGE    VERSION   LABELS\\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\\nnode1    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\nnode2    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a6f7680413274767/tools/002-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a6f7680413274767/tools/002-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a6f7680413274767/tools/002-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a6f7680413274767/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a6f7680413274767/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a6f7680413274767/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n19m                  Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n9m4s (x2 over 14m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a6f7680413274767/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a6f7680413274767/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a6f7680413274767/tools/004-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  19m                 default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  9m4s (x2 over 14m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  19m                 default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  9m4s (x2 over 14m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a6f7680413274767/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a6f7680413274767/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a6f7680413274767/tools/005-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"所有工具调用已完成，现在对采集到的证据进行汇总分析。\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据摘要\n\n**e1 - Pod Describe（critical）✅**\nPod `rc-pending-nodeselector` 状态为 **Pending**，未绑定节点（node=`<none>`）。  \n关键配置：\n- **Node-Selectors**: `aiops.e2e/nonexistent-node-label=true`\n- **Image**: `busybox:1.36`（imagePullPolicy=Never）\n- **QoS Class**: BestEffort\n\n**e2 - Pod Events（important）✅**\n两次 `FailedScheduling` 事件，原文一致：\n> `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.`\n\n**e3 - Pod YAML（critical）✅**\nYAML 确认：\n- `spec.nodeSelector` = `{\"aiops.e2e/nonexistent-node-label\": \"true\"}`\n- `status.phase` = `Pending`\n- `status.conditions[].reason` = `Unschedulable`\n- 无 `deletionTimestamp`，无 `finalizers`，无 PVC 引用\n\n**e4 - Node Labels（important）✅**\n集群共 **3 个节点**（master/node1/node2），均为 **Ready** 状态，**没有任何节点**包含 `aiops.e2e/nonexistent-node-label` 标签。\n\n**e5 - Runbook（reference）✅**\nRunbook 判定规则匹配：`FailedScheduling + node(s) didn't match node selector/affinity` → **调度约束不匹配（高置信度）**。\n\n### 🎯 根因结论\n\n| 维度 | 结果 |\n|------|------|\n| **根本原因** | Pod 设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，但集群3个节点均无该标签，调度器无法放置 |\n| **调度器原文** | `3 node(s) didn't match Pod's node affinity/selector` |\n| **节点状态** | 3节点均为 Ready，资源正常，非节点故障 |\n| **Pod 配置** | 无 PVC、无资源请求（BestEffort），无 hostPort，排除了其他调度因素 |\n| **置信度** | **高** — FailedScheduling 原文+Pod spec+Node labels 三者完全吻合 |\n\n### ❌ 冲突/负向证据\n无。所有工具均正确定位到目标对象，证据链一致。\n\n### ⛔ 未采集证据\n无。已有证据已完整覆盖异常根因，不需要额外采集。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 6 个，匹配计划 5 个，未规划证据 1 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":5,"unplanned_tool_count":1,"evidence_inventory":[{"id":"e1-g1-describe","description":"describe异常Pod rc-pending-nodeselector，确认当前状态、Events中的FailedScheduling原文、nodeSelector配置","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"确认FailedScheduling事件原文和nodeSelector配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-g1-events","description":"获取异常Pod的Events，确认调度失败事件详情","level":"important","tool":"kubectl_events","command":"kubectl events --for pod/rc-pending-nodeselector -n aiops-e2e","purpose":"采集FailedScheduling事件原文验证调度失败根因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3-g1-nodeselector","description":"获取Pod的完整YAML，提取nodeSelector配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"验证nodeSelector字段内容：aiops.e2e/nonexistent-node-label=true","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4-g1-nodes","description":"获取集群所有节点及其标签，验证是否存在匹配nodeSelector的节点","level":"important","tool":"run_bash_command","command":"kubectl get nodes --show-labels","purpose":"验证集群节点是否包含aiops.e2e/nonexistent-node-label=true标签","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5-g1-runbook","description":"获取Pod PendingUnschedulable runbook参考","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","purpose":"参考runbook确认调度约束不匹配的典型检查步骤","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1-g1-describe | critical | ✅ | kubectl_describe | describe异常Pod rc-pending-nodeselector，确认当前状态、... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e2-g1-events | important | ✅ | kubectl_events | 获取异常Pod的Events，确认调度失败事件详情 | `kubectl events --for pod/rc-pending-nodeselector -n aiops-e2e` |
   | e3-g1-nodesel... | critical | ✅ | kubectl_get_yaml | 获取Pod的完整YAML，提取nodeSelector配置 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e4-g1-nodes | important | ✅ | run_bash_command | 获取集群所有节点及其标签，验证是否存在匹配nodeSelector的节点 | `kubectl get nodes --show-labels` |
   | e5-g1-runbook | reference | ✅ | fetch_runbook | 获取Pod PendingUnschedulable runbook参考 | `fetch_runbook pod-pending-unschedulable.md` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (30.0s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector（namespace: aiops-e2e）状态为 Pending（READY 0/1），未绑定节点已持续19分钟。kubectl_describe 确认 Node-Selectors 为 aiops.e2e/nonexistent-node-label=true；kubectl_get_yaml 确认 spec.nodeSelector={"aiops.e2e/nonexistent-node-label":"true"}；集群3个节点（master/node1/node2）均为 Ready 状态但均无该标签；FailedScheduling 事件原文："0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"。无资源不足、无 PVC 依赖、无节点故障等其他因素。根因为调度约束不匹配。
   confidence=98%
   causal_chain={"root_cause": "Pod 的 spec.nodeSelector 配置了标签 aiops.e2e/nonexistent-node-label=true，但集群3个节点均没有该标签，导致调度器找不到可调度节点。", "propagation": "Pod 创建时被调度器选中但无法放置 → 调度器轮询所有3个节点均不匹配 nodeSelector → 产生 FailedScheduling 事件 → Pod 持续停留在 Pending 状态 → 抢占机制也无法解决（因为不是资源问题而是硬约束）。", "direct_cause": "3个节点均不满足 Pod 的 nodeSelector 标签约束（FailedScheduling: 3 node(s) didn't match Pod's node affinity/selector）", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中状态为 Pending，READY 0/1，node=<none>，已持续19分钟无法启动。"}
   rca_analysis={"phenomenon": "集群中存在1个异常Pod: aiops-e2e/rc-pending-nodeselector，状态为Pending（READY 0/1），未绑定任何节点（node=&lt;none&gt;），持续19分钟无法调度。集群其余59个Pod均正常运行。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod rc-pending-nodeselector 状态 Pending，node=<none>，Node-Selectors: aiops.e2e/nonexistent-node-label=true，FailedScheduling 事件原文", "reliability": "高"}, {"id": "e2", "source": "kubectl_events", "content": "两次 FailedScheduling 事件: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_yaml", "content": "Pod YAML: nodeSelector={\"aiops.e2e/nonexistent-node-label\":\"true\"}, phase=Pending, condition reason=Unschedulable, 无PVC引用", "reliability": "高"}, {"id": "e4", "source": "kubectl_get_nodes", "content": "集群3个节点(master/node1/node2)均为Ready状态，均无 aiops.e2e/nonexistent-node-label 标签", "reliability": "高"}, {"id": "e5", "source": "fetch_runbook", "content": "Runbook判定: FailedScheduling + didn't match node selector/affinity → 调度约束不匹配(高置信度)", "reliability": "高"}, {"id": "e6", "source": "kubectl_get_by_kind_in_cluster", "content": "集群65个Pod中仅此1个异常，其余59个Running，无其他异常状态", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "kubectl_describe: node=<none>, status=Pending, Node-Selectors: aiops.e2e/nonexistent-node-label=true, Warning FailedScheduling 19m: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "interpretation": "Pod 明确设置了 nodeSelector=aiops.e2e/nonexistent-node-label=true，调度器报告所有3个节点均不满足该选择器条件，Pod 无法调度。"}, {"evidence_id": "e2", "raw_data": "Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.", "interpretation": "调度器在19分钟和9分钟前各产生一次 FailedScheduling 事件，持续无法调度，且抢占（preemption）也无帮助，说明问题不是资源竞争而是硬约束不满足。"}, {"evidence_id": "e3", "raw_data": "kubectl_get_yaml: nodeSelector={\"aiops.e2e/nonexistent-node-label\":\"true\"}, phase=Pending, conditions.reason=Unschedulable, conditions.message=0/3 nodes are available: ..., 无PVC引用, imagePullPolicy=Never, QoS=BestEffort", "interpretation": "YAML 确认 nodeSelector 键值对、Unschedulable 条件、无 PVC 依赖，排除了 PVC 未绑定、资源请求不足等其他可能的调度失败原因。"}, {"evidence_id": "e4", "raw_data": "master Labels: beta.kubernetes.io/arch=amd64,...,node1 Labels: beta.kubernetes.io/arch=amd64,...,node2 Labels: beta.kubernetes.io/arch=amd64,... （均不含 aiops.e2e/nonexistent-node-label）", "interpretation": "集群3个节点的标签列表中均不包含 aiops.e2e/nonexistent-node-label=true，直接验证了调度器报告'不匹配'的结论——没有节点拥有该标签。"}, {"evidence_id": "e5", "raw_data": "Runbook: FailedScheduling + node(s) didn't match node selector/affinity → 调度约束不匹配（高置信度）", "interpretation": "Runbook 判定规则完全匹配当前证据组合，支撑根因结论为'调度约束不匹配'。"}, {"evidence_id": "e6", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}", "interpretation": "集群整体健康，仅此1个Pod异常，排除了大规模集群故障的可能，问题隔离在这个Pod的调度配置上。"}], "causal_chain": {"root_cause": "Pod 的 spec.nodeSelector 配置了标签 aiops.e2e/nonexistent-node-label=true，但集群3个节点均没有该标签，导致调度器找不到可调度节点。", "propagation": "Pod 创建时被调度器选中但无法放置 → 调度器轮询所有3个节点均不匹配 nodeSelector → 产生 FailedScheduling 事件 → Pod 持续停留在 Pending 状态 → 抢占机制也无法解决（因为不是资源问题而是硬约束）。", "direct_cause": "3个节点均不满足 Pod 的 nodeSelector 标签约束（FailedScheduling: 3 node(s) didn't match Pod's node affinity/selector）", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中状态为 Pending，READY 0/1，node=<none>，已持续19分钟无法启动。"}, "root_cause": "Pod rc-pending-nodeselector（namespace: aiops-e2e）状态为 Pending（READY 0/1），未绑定节点已持续19分钟。kubectl_describe 确认 Node-Selectors 为 aiops.e2e/nonexistent-node-label=true；kubectl_get_yaml 确认 spec.nodeSelector={\"aiops.e2e/nonexistent-node-label\":\"true\"}；集群3个节点（master/node1/node2）均为 Ready 状态但均无该标签；FailedScheduling 事件原文：\"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"。无资源不足、无 PVC 依赖、无节点故障等其他因素。根因为调度约束不匹配。", "root_cause_summary": "Pod rc-pending-nodeselector（namespace: aiops-e2e）状态为 Pending（READY 0/1），未绑定节点已持续19分钟。kubectl_describe 确认 Node-Selectors 为 aiops.e2e/nonexistent-node-label=true；kubectl_get_yaml 确认 spec.nodeSelector={\"aiops.e2e/nonexistent-node-label\":\"true\"}；集群3个节点（master/node1/node2）均为 Ready 状态但均无该标签；FailedScheduling 事件原文：\"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"。无资源不足、无 PVC 依赖、无节点故障等其他因素。根因为调度约束不匹配。", "confidence": 0.98, "confidence_reason": "FailedScheduling 事件原文（3 nodes didn't match node affinity/selector）、Pod YAML 的 nodeSelector 配置（aiops.e2e/nonexistent-node-label=true）、节点标签列表（3节点均无该标签）三者完全吻合，形成闭环证据链。Runbook 判定规则完全匹配。无任何冲突证据。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "资源不足（CPU/内存不足）", "probability": "low", "reason": "FailedScheduling 原文不含 Insufficient cpu/memory，且 Pod QoS 为 BestEffort（无资源请求），调度器未报告资源不足信息"}, {"cause": "taint/toleration 不匹配", "probability": "low", "reason": "FailedScheduling 原文不含 had untolerated taint，节点均为 Ready 状态无特殊 taint；Pod 有 tolerations（node.kubernetes.io/not-ready:NoExecute）"}, {"cause": "PVC 未绑定", "probability": "low", "reason": "YAML 中无 PVC 引用，FailedScheduling 原文不含 unbound immediate PersistentVolumeClaims"}, {"cause": "节点不可调度（NotReady/SchedulingDisabled）", "probability": "low", "reason": "3节点均为 Ready 状态，无 NotReady/Unknown/SchedulingDisabled 标志"}, {"cause": "hostPort 端口冲突", "probability": "low", "reason": "FailedScheduling 原文不含 didn't have free ports，Pod 无 hostPort 配置"}], "limitations": "该 Pod 带有 rootcause-e2e=true 标签，且镜像使用 imagePullPolicy=Never（需本地已有 busybox:1.36），可能为 E2E 测试构造的异常场景，但这不影响调度约束不匹配的根因判定。当前证据已覆盖所有必要维度，无证据缺失。", "llm_raw_analysis": "## 证据清点\n共7条证据（e1-e6 + 集群整体状态），覆盖 Pod 状态、Events、YAML 配置、节点标签、Runbook 参考、集群整体健康状况。\n\n## 逐条分析\n- **e1（kubectl_describe）**：Pod 状态 Pending，未绑定节点，明确设置了 Node-Selectors: aiops.e2e/nonexistent-node-label=true，调度器报告 FailedScheduling\n- **e2（kubectl_events）**：两次 FailedScheduling 事件，原文一致，确认所有3节点均不满足 node affinity/selector\n- **e3（kubectl_get_yaml）**：确认 nodeSelector 配置、无 PVC、无资源请求（BestEffort）、condition reason=Unschedulable\n- **e4（kubectl_get_nodes）**：3节点全部 Ready，标签列表均不含 aiops.e2e/nonexistent-node-label\n- **e5（ru\n... 截断，原始 907 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector（namespace: aiops-e2e）状态为 Pending（READY 0/1），未绑定节点已持续19分钟。kubectl_describe 确认 Node-Selectors 为 aiops.e2e/nonexistent-node-l...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod 的 spec.nodeSelector 配置了标签 aiops.e2e/nonexistent-node-label=true，但集群3个节点均没有该标签，导致调度器找不到可调度节点。
     传导机制: Pod 创建时被调度器选中但无法放置 → 调度器轮询所有3个节点均不匹配 nodeSelector → 产生 FailedScheduling 事件 → Pod 持续停留在 Pending 状态 → 抢占机制也无法解决（因为不是资源问题而是硬约束）。
     最终表现: Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中状态为 Pending，READY 0/1，node=<none>，已持续19分钟无法启动。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (30.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6028 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 41.4s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我现在根据您提供的三个阶段的详细分析结果，为您生成一份完整的诊断报告。

---

## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending (PendingUnschedulable) |
| **兼容归因层** | L1 |
| **问题分类** | 调度约束不匹配（NodeSelector 不匹配） |
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
| Node | `<none>` （未绑定节点） |
| 错误信息 | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` |

**当前集群核心状态总结**：
集群运行正常，65个Pod中64个运行正常（Running），仅1个Pod `aiops-e2e/rc-pending-nodeselector` 处于异常状态（Pending）。该Pod由于配置了不存在的节点标签选择器，无法被调度到任何节点上，已持续 19 分钟。

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod` | `Status: Pending`, `Node: <none>` | Pod 未成功调度到任何节点，处于待调度状态 |
| 2 | 调度事件 | `kubectl describe pod` / `kubectl get events` | `Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 明确指出了调度失败的原因是节点亲和性/选择器不匹配 |
| 3 | Pod 配置 | `kubectl get pod -o yaml` | `nodeSelector: {"aiops.e2e/nonexistent-node-label":"true"}` | Pod 要求节点必须包含标签 `aiops.e2e/nonexistent-node-label=true` |
| 4 | 节点标签 | `run_bash_command` (kubectl get nodes) | 节点 `master`: `kubernetes.io/hostname=master`; 节点 `node1`: `kubernetes.io/hostname=node1`; 节点 `node2`: `kubernetes.io/hostname=node2`（3个节点均`Ready`，但均无 `aiops.e2e/nonexistent-node-label` 标签） | 集群3个节点是健康的，但没有任何一个节点拥有 Pod 所要求的标签 |
| 5 | 节点状态 | `kubectl get nodes` | `NAME     STATUS   ROLES           AGE    VERSION` <br> `master   Ready    control-plane   238d   v1.26.8` <br> `node1    Ready    <none>          238d   v1.26.8` <br> `node2    Ready    <none>          238d   v1.26.8` | 3个节点均处于 Ready 状态，排除了节点不可用导致的问题 |
| 6 | Pod 容器配置 | `kubectl describe pod` | `Command: sleep 3600`, `Image: busybox:1.36` | Pod 是一个简单的测试Pod，不需要复杂的资源或存储 |

### 证据关联分析
- **证据 #2 + #3 + #4 印证**：调度器（default-scheduler）报告 `FailedScheduling` 事件，明确指出所有3个节点均不满足 Pod 的亲和性/选择器。**证据 #3** 进一步揭示 Pod 要求节点拥有标签 `aiops.e2e/nonexistent-node-label=true`，而**证据 #4** 确认集群3个节点的标签列表中均不存在该标签。三者形成完整证据链，直接定位根因。
- **证据链**：Pod 配置硬性标签选择器 → 调度器在所有Ready节点上查找该标签 → 未找到 → 尝试抢占（Preemption）但无法解决 → 产生FailedScheduling事件 → Pod 停留在Pending状态。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | - | 证据完整，无需额外采集 |

当前证据已覆盖所有必要维度（Pod状态、调度事件、Pod配置、节点标签），根因明确，无缺失证据。

---
## 🎯 根因分析
### 因果链
```
┌────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                           │
│ Pod 的 spec.nodeSelector 配置了集群中不存在的标签                     │
│ nodeSelector: { "aiops.e2e/nonexistent-node-label": "true" }      │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                           │
│ Pod 创建 → 调度器检查所有 Ready 节点 → 3个节点均不满足 nodeSelector  │
│ → 调度失败 → 调度器尝试抢占（Preemption）→ 抢占对硬约束无效          │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                           │
│ 调度器确认所有节点均不匹配 Pod 的 node affinity/selector，              │
│ 产生 FailedScheduling 事件。                                       │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                       │
│ Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续处于 Pending  │
│ 状态，READY 0/1，未绑定任何节点，已持续 19 分钟。                     │
└────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #2 (FailedScheduling 事件)、证据 #3 (Pod 的 nodeSelector YAML 配置) 和证据 #4 (节点标签列表)，问题的根本原因是 **Pod `rc-pending-nodeselector` 的节点选择器（nodeSelector）指定了一个在集群所有节点上都不存在的标签 `aiops.e2e/nonexistent-node-label=true`**，导致调度器无法找到可调度的节点。

**置信度**：高 (98%)
- ✅ `FailedScheduling` 事件原文直接指向”节点亲和性/选择器不匹配”。
- ✅ Pod YAML 中 `nodeSelector` 配置与事件描述一致。
- ✅ 节点标签数据显示所有节点均无此标签。
- ✅ 排除了资源不足、节点不可用等其他常见原因。

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [核心方案] 修改或移除 Pod 的 nodeSelector**
由于该 Pod 看起来是 E2E 测试或调试用途（镜像为 `busybox`，且带有 `rootcause-e2e=true` 标签），最直接的修复是移除或修改其 nodeSelector 约束。
```bash
# 方式一：删除该测试Pod（如果不再需要）
kubectl delete pod rc-pending-nodeselector -n aiops-e2e

# 方式二：如果是Deployment/Job等控制器管理的，编辑控制器移除nodeSelector
# 假设是由Deployment管理，执行：
kubectl edit deployment <deployment-name> -n aiops-e2e
# 移除 spec.template.spec.nodeSelector 字段

# 方式三：直接编辑Pod（仅建议用于测试Pod，因为修改会失效，通常需要重建）
# kubectl edit pod rc-pending-nodeselector -n aiops-e2e
# 然后删除 spec.nodeSelector 或将其值改为集群中存在的标签
```
*依据*：根因为标签不匹配，所以直接解决标签约束是最快的方法。

**2. [诊断验证] 确认节点标签，为节点打上所需标签（不推荐用于生产）**
如果这个标签是预期的，并且您希望Pod运行在特定节点上，那么可以为目标节点打上标签。
```bash
# 为 node1 节点打上所需的标签
kubectl label node node1 aiops.e2e/nonexistent-node-label=true

# 验证
kubectl get node node1 --show-labels | grep aiops.e2e

# 观察Pod是否被调度
kubectl get pod rc-pending-nodeselector -n aiops-e2e -w
```
*注意*：此操作仅在您确实需要为节点添加此特定标签时才执行。仅作为诊断验证手段。

### 后续优化
1. **审核部署清单**：在CI/CD流程中增加Pod配置校验，确保 `nodeSelector`、`affinity` 等调度约束引用的标签在目标集群中存在。
2. **监控调度失败事件**：对 `FailedScheduling` 事件配置告警，以便及时发现问题。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 是否被删除或重调度 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | Pod 不再存在，或 STATUS 变为 `Running`（如果正在调度） |
| 2. 检查节点标签（如果执行了标签操作） | `kubectl get node node1 --show-labels \| grep aiops.e2e` | 显示 `aiops.e2e/nonexistent-node-label=true` |
| 3. 确认无其他调度失败事件 | `kubectl get events -n aiops-e2e \| grep FailedScheduling` | 无新输出的 `FailedScheduling` 事件 |

---
## ⚠️ 注意事项
- 该 Pod 带有 `rootcause-e2e=true` 标签，镜像为 `busybox`，很可能是E2E测试或人为构造的调试场景，并非生产工作负载。建议优先确认该Pod的Owner，再决定是删除还是修复。
- 不要直接给所有节点打上 `aiops.e2e/nonexistent-node-label=true` 标签，这可能导致更严重的配置混乱。正确的做法是修改Pod或控制器的定义。
- 真实环境证据显示所有节点均正常工作（Ready），该问题属于典型的**配置错误**，不影响集群整体健康度。

---

## 📊 性能统计

├─ 总耗时: 1.7m
├─ 问题定位: 20.2s (20%) ✅
├─ 证据链采集: 20.4s (20%) ✅
├─ 根因分析: 30.0s (30%) ✅
├─ 汇总总结: 30.8s (30%) ✅
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
