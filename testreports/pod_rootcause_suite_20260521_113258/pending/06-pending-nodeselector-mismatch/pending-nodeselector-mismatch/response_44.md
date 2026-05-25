======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: f43fe07cf19847e6]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来先全局扫描所有 Pod，看看集群当前的运行状态。
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 TodoWrite 输出摘要: raw_chars=264 lines=7
Investigation plan updated with 3 tasks.
# CURRENT INVESTIGATION TASKS
**Task Status**: 0 completed, 1 in progress, 2 pending
[ ] [2] 识别异常 Pod 并分组
[ ] [3] 定位异常类型及
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 TodoWrite 输出摘要: raw_chars=264 lines=7
Investigation plan updated with 3 tasks.
# CURRENT INVESTIGATION TASKS
**Task Status**: 1 completed, 1 in progress, 1 pending
[ ] [3] 定位异常类型及兼容层级
[~] [2] 识别异常 Pod
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          34m   <none>   <none>   
   💭 [问题定位] 这个 Pod 带有 `pod_abnormal_type=PendingUnschedulable` 标签，恰好匹配 runbook。让我进一步确认它的调度状态。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  34m                default-scheduler  0/3 nodes are available: 
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在我已经定位清楚了，让我完成分析。
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 TodoWrite 输出摘要: raw_chars=264 lines=7
Investigation plan updated with 3 tasks.
# CURRENT INVESTIGATION TASKS
**Task Status**: 3 completed, 0 in progress, 0 pending
[✓] [1] 全局扫描所有 Pod 状态
[✓] [2] 识别异常 P
   💭 [问题定位] ## 集群异常状态分析

### 全局概览
集群共有 **65 个 Pod**，其中 **59 个 Running（正常）**，**1 个 Pending（异常）**。整体健康状况良好，仅发现一个异常 Pod。

---

### 异常 Pod 清单

| 命名空间 | Pod 名称 | 状态 | 已运行时间 |
|---------|---------|------|----------|
| aiops-e2e | `rc-pending-nodeselector` | **Pending** | 34 分钟 |

---

### 异常分组

| 异常组 | 状态关键字 | 数量 |
|-------|-----------|:----:|
| **PendingUnschedulable** | Pending | 1 |

---

### 定位分析

**Pod：`rc-pending-nodeselector`** (aiops-e2e 命名空间)

- **状态**：Pending，未绑定节点（nodeName: `<none>`）
- **异常类型**：`PendingUnschedulable`（调度失败）
- **兼容层级**：**L1**

**核心证据**：
- FailedScheduling 事件原文：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`
- Pod 设置了 `nodeSelector`：`aiops.e2e/nonexistent-node-label=true`
- 集群 3 个节点中没有任何一个节点具备此标签，导致调度器无法放置

**根因**：**nodeSelector 与节点标签不匹配** — Pod 要求节点拥有 `aiops.e2e/nonexistent-node-label=true` 标签，但集群中 3 个节点均无该标签。

---

### LayerOutput 结构化摘要

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **layer_name** | PendingUnschedulable |
| **pod_status_keyword** | Pending |
| **pod_abnormal_type** | PendingUnschedulable |
| **status_category** | scheduling |
| **confidence** | 高 |
| **abnormal_pods** | `aiops-e2e/rc-pending-nodeselector` |
| **abnormal_groups** | PendingUnschedulable × 1 |
| **key_entities** | Pod: rc-pending-nodeselector, NodeSelector: aiops.e2e/nonexistent-node-label=true |
| **possible_scenarios** | nodeSelector 引用了集群中不存在的节点标签，导致 Pod 无法被调度 |

**建议方向**：
1. 确认是否需要该 nodeSelector，如不需要则删除它
2. 如果需要，则为目标节点添加对应标签：`kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`
3. 或修改 Pod 的 nodeSelector/affinity 匹配现有节点标签
   ✅ [问题定位] 完成 (30.7s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector 引用了集群中不存在的节点标签导致 Pod 无法调度', 'probability': '高', 'reason': 'FailedScheduling 事件明确提示 node affinity/selector 不匹配，Pod 的 Node-Selectors 字段显示 aiops.e2e/nonexistent-node-label=true，集群 3 个节点均无该标签'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "NodeSelector", "name": "aiops.e2e/nonexistent-node-label=true", "namespace": ""}]
   reasoning=集群65个Pod中59个Running正常，仅1个异常Pod `rc-pending-nodeselector`（aiops-e2e命名空间）处于Pending状态。FailedScheduling事件原文显示：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod设置了nodeSelector: aiops.e2e/nonexistent-node-label=true，但集群3个节点均无此标签，导致调度器无法放置。根因为调度约束（nodeSelector）不匹配，符合L1层级（scheduling/调度失败）。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "集群65个Pod中59个Running正常，仅1个异常Pod `rc-pending-nodeselector`（aiops-e2e命名空间）处于Pending状态。FailedScheduling事件原文显示：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod设置了nodeSelector: aiops.e2e/nonexistent-node-label=true，但集群3个节点均无此标签，导致调度器无法放置。根因为调度约束（nodeSelector）不匹配，符合L1层级（scheduling/调度失败）。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "NodeSelector", "name": "aiops.e2e/nonexistent-node-label=true", "namespace": ""}], "possible_scenarios": [{"scenario": "nodeSelector 引用了集群中不存在的节点标签导致 Pod 无法调度", "probability": "高", "reason": "FailedScheduling 事件明确提示 node affinity/selector 不匹配，Pod 的 Node-Selectors 字段显示 aiops.e2e/nonexistent-node-label=true，集群 3 个节点均无该标签"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              33m     <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/f43fe07cf19847e6/tools/002-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/f43fe07cf19847e6/tools/002-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/f43fe07cf19847e6/tools/002-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我现在开始执行既有 evidence_plan 中的采证工具。先并行执行关键证据项。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAME     STATUS   ROLES           AGE    VERSION   LABELS\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpg
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
34m                 Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 n
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:18:44Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [证据链采集] 所有工具已执行完毕，以下是证据采集结论：

---

## ✅ 已采集证据

**e1 - Pod 完整 YAML ✅**
- Pod `rc-pending-nodeselector` 确认存在，`phase: Pending`
- **nodeSelector: `{"aiops.e2e/nonexistent-node-label": "true"}`** — 确认为关键根因
- condition `PodScheduled=False, reason=Unschedulable`，message 与上游一致

**e2 - 节点标签列表 ✅**
- 集群共 **3 个节点**：`master`、`node1`、`node2`，全部 `Ready`
- 检查所有节点标签，**均不包含 `aiops.e2e/nonexistent-node-label`** 标签
- 节点标签包括：`kubernetes.io/arch`、`kubernetes.io/hostname`、`kubernetes.io/os`、`node-role.kubernetes.io/control-plane` 等标准标签，无自定义的 `aiops.e2e/nonexistent-node-label`

**e3 - Pod Events ✅**
- `FailedScheduling` 事件共出现 3 次（最近 24m、34m 等），原文：
  > `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.`
  > `preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.`

---

## 🔍 冲突/负向证据
- 无冲突证据。Pod 仍在原 namespace，Events 与 YAML 均与上游定位完全一致。

---

## 📋 诊断结论

**根因确认：** Pod `rc-pending-nodeselector` 配置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，但集群 3 个节点均无此标签，导致调度器无法放置任何节点。

**影响范围：** 仅此 1 个 Pod 异常（集群其他 59 个 Pod 运行正常），属于配置错误而非集群故障。

**建议修复：** 去除 Pod spec 中不存在的 `nodeSelector` 约束，或为节点打上对应标签 `kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`。
   ✅ [证据链采集] 完成 (17.0s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证异常Pod rc-pending-nodeselector当前状态和关键配置（nodeSelector）","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"获取Pod完整YAML，确认nodeSelector字段、当前status、conditions等配置","evidence_type":"config","target_scope":"g1","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e2","description":"获取集群所有节点的标签，验证不存在 aiops.e2e/nonexistent-node-label 标签","level":"critical","tool":"run_bash_command","command":"kubectl get nodes --show-labels","tool_args":{"command":"kubectl get nodes --show-labels"},"purpose":"验证集群3个节点是否包含Pod所需标签，确认根因为标签不匹配","evidence_type":"config","target_scope":"g1","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取Pod的Events确认FailedScheduling事件原文","level":"critical","tool":"kubectl_events","command":"kubectl events --for pod/rc-pending-nodeselector -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","kind":"pod","name":"rc-pending-nodeselector"},"purpose":"验证FailedScheduling事件原文与上游定位一致","evidence_type":"event","target_scope":"g1","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAME     STATUS   ROLES           AGE    VERSION   LABELS\\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\\nnode1    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\nnode2    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f43fe07cf19847e6/tools/001-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f43fe07cf19847e6/tools/001-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f43fe07cf19847e6/tools/001-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n34m                 Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n24m (x2 over 29m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f43fe07cf19847e6/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f43fe07cf19847e6/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f43fe07cf19847e6/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f43fe07cf19847e6/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f43fe07cf19847e6/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f43fe07cf19847e6/tools/003-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"所有工具已执行完毕，以下是证据采集结论：\n\n---\n\n## ✅ 已采集证据\n\n**e1 - Pod 完整 YAML ✅**\n- Pod `rc-pending-nodeselector` 确认存在，`phase: Pending`\n- **nodeSelector: `{\"aiops.e2e/nonexistent-node-label\": \"true\"}`** — 确认为关键根因\n- condition `PodScheduled=False, reason=Unschedulable`，message 与上游一致\n\n**e2 - 节点标签列表 ✅**\n- 集群共 **3 个节点**：`master`、`node1`、`node2`，全部 `Ready`\n- 检查所有节点标签，**均不包含 `aiops.e2e/nonexistent-node-label`** 标签\n- 节点标签包括：`kubernetes.io/arch`、`kubernetes.io/hostname`、`kubernetes.io/os`、`node-role.kubernetes.io/control-plane` 等标准标签，无自定义的 `aiops.e2e/nonexistent-node-label`\n\n**e3 - Pod Events ✅**\n- `FailedScheduling` 事件共出现 3 次（最近 24m、34m 等），原文：\n  > `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.`\n  > `preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.`\n\n---\n\n## 🔍 冲突/负向证据\n- 无冲突证据。Pod 仍在原 namespace，Events 与 YAML 均与上游定位完全一致。\n\n---\n\n## 📋 诊断结论\n\n**根因确认：** Pod `rc-pending-nodeselector` 配置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，但集群 3 个节点均无此标签，导致调度器无法放置任何节点。\n\n**影响范围：** 仅此 1 个 Pod 异常（集群其他 59 个 Pod 运行正常），属于配置错误而非集群故障。\n\n**建议修复：** 去除 Pod spec 中不存在的 `nodeSelector` 约束，或为节点打上对应标签 `kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 6 个，匹配计划 3 个，未规划证据 3 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":3,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"验证异常Pod rc-pending-nodeselector当前状态和关键配置（nodeSelector）","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"获取Pod完整YAML，确认nodeSelector字段、当前status、conditions等配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取集群所有节点的标签，验证不存在 aiops.e2e/nonexistent-node-label 标签","level":"critical","tool":"run_bash_command","command":"kubectl get nodes --show-labels","purpose":"验证集群3个节点是否包含Pod所需标签，确认根因为标签不匹配","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取Pod的Events确认FailedScheduling事件原文","level":"critical","tool":"kubectl_events","command":"kubectl events --for pod/rc-pending-nodeselector -n aiops-e2e","purpose":"验证FailedScheduling事件原文与上游定位一致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 验证异常Pod rc-pending-nodeselector当前状态和关键配置（node... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | run_bash_command | 获取集群所有节点的标签，验证不存在 aiops.e2e/nonexistent-node-... | `kubectl get nodes --show-labels` |
   | e3 | critical | ✅ | kubectl_events | 获取Pod的Events确认FailedScheduling事件原文 | `kubectl events --for pod/rc-pending-nodeselector -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (25.3s)
   📤 → 下游数据: root_cause=Pod `rc-pending-nodeselector`（aiops-e2e命名空间）处于Pending状态的根因为：Pod设置了`nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}`（证据e1），但集群3个节点（master、node1、node2）的标签列表中均不包含`aiops.e2e/nonexistent-node-label`键（证据e2）。调度器持续报告 `FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`（证据e3），Pod自创建34分钟以来一直无法调度。集群其他59个Pod运行正常，非集群故障，属于Pod配置错误。
   confidence=100%
   causal_chain={"root_cause": "Pod spec 中配置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，但集群3个节点均无此标签", "propagation": "调度器在调度rc-pending-nodeselector时，依次检查master、node1、node2三个节点，发现所有节点均不满足nodeSelector约束条件 → 标记Pod为Unschedulable → 持续重试3次均失败 → Pod长期处于Pending状态", "direct_cause": "nodeSelector引用的标签 aiops.e2e/nonexistent-node-label 在集群任何节点上都不存在，调度器无法将Pod放置到任何节点", "manifestation": "Pod rc-pending-nodeselector 状态为 Pending，0/1容器未运行，无IP地址，无绑定节点，Events中持续报告 FailedScheduling"}
   rca_analysis={"phenomenon": "集群共65个Pod中59个Running正常，仅1个异常Pod `rc-pending-nodeselector`（aiops-e2e命名空间）处于Pending状态，0/1容器就绪，无IP无Node分配。", "evidence_inventory": [{"id": "e1", "source": "kubectl_get_yaml", "content": "Pod rc-pending-nodeselector phase=Pending, nodeSelector={\"aiops.e2e/nonexistent-node-label\":\"true\"}, condition PodScheduled=False reason=Unschedulable", "reliability": "高"}, {"id": "e2", "source": "run_bash_command (kubectl get nodes -o wide)", "content": "集群3个节点 master/node1/node2 全部Ready，均无 aiops.e2e/nonexistent-node-label 标签", "reliability": "高"}, {"id": "e3", "source": "kubectl_events", "content": "FailedScheduling事件: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "集群65个Pod，Running=59, Pending=1，仅rc-pending-nodeselector异常", "reliability": "高"}, {"id": "layer_2", "source": "kubectl_get_by_name", "content": "rc-pending-nodeselector 0/1 Pending 0 34m <none> <none>", "reliability": "高"}, {"id": "layer_3", "source": "kubectl_describe", "content": "FailedScheduling事件: 3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "phase: Pending\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\nconditions: PodScheduled=False reason=Unschedulable", "interpretation": "Pod明确设置了nodeSelector引用标签 aiops.e2e/nonexistent-node-label=true，且调度条件为False，调度器判定为Unschedulable，说明调度失败直接原因是nodeSelector约束无法满足。"}, {"evidence_id": "e2", "raw_data": "master labels: beta.kubernetes.io/arch=amd64,...,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1 labels: beta.kubernetes.io/arch=amd64,...,metax-tech.com/gpu.installed=false\nnode2 labels: beta.kubernetes.io/arch=amd64,...,metax-tech.com/gpu.installed=false", "interpretation": "集群3个节点（master、node1、node2）均为Ready状态，但所有节点标签中均不包含 aiops.e2e/nonexistent-node-label 键，证实nodeSelector引用的标签在集群中完全不存在。"}, {"evidence_id": "e3", "raw_data": "Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.", "interpretation": "调度器明确报告3个节点均不满足Pod的node affinity/selector约束，且抢占也无帮助，与e1中nodeSelector配置和e2中节点标签缺失完全吻合。"}, {"evidence_id": "layer_1", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}", "interpretation": "集群中除该Pod外其余59个Pod均正常运行，说明集群整体健康，不存在节点级或基础设施级故障，异常范围仅限于此单一Pod。"}, {"evidence_id": "layer_2", "raw_data": "rc-pending-nodeselector 0/1 Pending 0 34m <none> <none>", "interpretation": "Pod自创建34分钟以来一直处于Pending状态，未分配到Node，未获得IP，配置正确性确认。"}, {"evidence_id": "layer_3", "raw_data": "Warning FailedScheduling 34m and 23m (x2 over 28m): 3 node(s) didn't match Pod's node affinity/selector.", "interpretation": "FailedScheduling事件在Pod生命周期内持续出现（34m、28m、23m前），说明调度器持续重试但始终失败，不是瞬时问题。"}], "causal_chain": {"root_cause": "Pod spec 中配置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，但集群3个节点均无此标签", "propagation": "调度器在调度rc-pending-nodeselector时，依次检查master、node1、node2三个节点，发现所有节点均不满足nodeSelector约束条件 → 标记Pod为Unschedulable → 持续重试3次均失败 → Pod长期处于Pending状态", "direct_cause": "nodeSelector引用的标签 aiops.e2e/nonexistent-node-label 在集群任何节点上都不存在，调度器无法将Pod放置到任何节点", "manifestation": "Pod rc-pending-nodeselector 状态为 Pending，0/1容器未运行，无IP地址，无绑定节点，Events中持续报告 FailedScheduling"}, "root_cause": "Pod `rc-pending-nodeselector`（aiops-e2e命名空间）处于Pending状态的根因为：Pod设置了`nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}`（证据e1），但集群3个节点（master、node1、node2）的标签列表中均不包含`aiops.e2e/nonexistent-node-label`键（证据e2）。调度器持续报告 `FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`（证据e3），Pod自创建34分钟以来一直无法调度。集群其他59个Pod运行正常，非集群故障，属于Pod配置错误。", "root_cause_summary": "Pod `rc-pending-nodeselector`（aiops-e2e命名空间）处于Pending状态的根因为：Pod设置了`nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}`（证据e1），但集群3个节点（master、node1、node2）的标签列表中均不包含`aiops.e2e/nonexistent-node-label`键（证据e2）。调度器持续报告 `FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`（证据e3），Pod自创建34分钟以来一直无法调度。集群其他59个Pod运行正常，非集群故障，属于Pod配置错误。", "confidence": 1.0, "confidence_reason": "直接证据完备且完全一致：Pod YAML明确显示nodeSelector配置（e1）、节点标签列表确认该标签不存在（e2）、FailedScheduling事件原文与nodeSelector不匹配完全对应（e3），三条独立证据形成闭环因果链，无任何矛盾或缺失环节。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "资源不足（CPU/内存不足）", "probability": "low", "reason": "FailedScheduling事件明确指向node affinity/selector不匹配，而非Insufficient cpu/memory；集群其他59个Pod运行正常，节点资源充足"}, {"cause": "节点Taint/Toleration不匹配", "probability": "low", "reason": "Pod有2个tolerations且事件未提及taint相关；事件明确指向node affinity/selector"}, {"cause": "PVC未绑定", "probability": "low", "reason": "Pod无PVC卷声明，仅有一个kube-api-access自动挂载卷，不存在存储前置条件问题"}, {"cause": "节点NotReady或SchedulingDisabled", "probability": "low", "reason": "所有3个节点均为Ready状态，有正常运行的59个Pod为证"}], "limitations": "未采集Pod的完整容器镜像拉取策略（imagePullPolicy=Never但仅此不会导致Pending）；未验证该Pod是否由上层控制器（Deployment/ReplicaSet）创建；未检查集群是否有节点自动扩缩容机制可能解决问题。但这些对当前根因结论无影响。", "llm_raw_analysis": "L1层级根因分析：集群65个Pod中59个Running正常（evidence layer_1），仅1个异常Pod rc-pending-nodeselector（aiops-e2e命名空间）处于Pending状态。证据清点显示3条核心证据（e1 Pod YAML、e2 节点标签、e3 Events）完全吻合。Pod的nodeSelector配置了不存在的标签aiops.e2e/nonexistent-node-label=true，3个节点均无此标签，调度器无法放置。异常组g1仅包含该Pod，已最小验证完成。无其他异常组或并发异常。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod `rc-pending-nodeselector`（aiops-e2e命名空间）处于Pending状态的根因为：Pod设置了`nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}`（证据e1），但集群3个节点（master、no...
   置信度: 100%
   🔗 因果链:
     根本原因: Pod spec 中配置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，但集群3个节点均无此标签
     传导机制: 调度器在调度rc-pending-nodeselector时，依次检查master、node1、node2三个节点，发现所有节点均不满足nodeSelector约束条件 → 标记Pod为Unschedulable → 持续重试3次均失败 → Pod长期处于Pending状态
     最终表现: Pod rc-pending-nodeselector 状态为 Pending，0/1容器未运行，无IP地址，无绑定节点，Events中持续报告 FailedScheduling


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (22.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4767 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 35.0s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，资深 K8s 诊断专家已就位。现在为您分析集群状况。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **集群整体状态** | **基本健康**。65个Pod中，59个(90.8%)正常运行，仅1个异常 |
| **Pod异常状态** | Pending |
| **关键异常组** | `rc-pending-nodeselector` (aiops-e2e) - **PendingUnschedulable** |
| **兼容归因层** | L1 - scheduling（调度失败） |
| **问题分类** | **调度约束(nodeSelector)不匹配** |
| **置信度** | **高 (100%)** |
| **证据完整度** | 3/3 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| **集群总Pod数** | 65 |
| **正常Pod数** | 59 (Running) |
| **异常Pod** | `rc-pending-nodeselector` |
| **异常Namespace** | `aiops-e2e` |
| **异常状态** | Pending |
| **错误信息** | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` |

**问题总结**：您的集群总体运行平稳，59个Pod正常运行。唯一的问题是一个名为 `rc-pending-nodeselector` 的测试用Pod，因配置了集群中不存在的节点标签，导致无法被调度，持续处于 Pending 状态超过30分钟。

---

## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | **Pod配置** | `kubectl_get_yaml` | `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}` | Pod 明确要求调度到包含 `aiops.e2e/nonexistent-node-label=true` 标签的节点上 |
| 2 | **节点标签** | `run_bash_command` (获取所有节点标签) | `master` 节点标签：`…`<br>`node1` 节点标签：`…`<br>`node2` 节点标签：`…`<br>**三个节点的标签列表中均不包含 `aiops.e2e/nonexistent-node-label`** | 集群中没有任何节点满足 Pod 的 nodeSelector 要求 |
| 3 | **事件日志** | `kubectl_events` | `34m Warning FailedScheduling Pod/rc-pending-nodeselector 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` <br> `24m (x2 over 29m) Warning …` | 调度器持续报告调度失败，明确原因是节点不满足 `node affinity/selector` |

### 证据关联分析
- **证据 #1 + #2 + #3 相互印证**：Pod 设置了 `nodeSelector` (证据#1)，但集群所有节点都没有匹配的标签 (证据#2)，导致调度器每次尝试都失败并生成 `FailedScheduling` 事件 (证据#3)。这是一个完整的因果闭环，无需其他假设。
- **证据链**：Pod 配置中存在错误的 `nodeSelector` → 调度器检查所有节点均不匹配 → 调度失败（Pending）→ Pod 一直挂起。

### 缺失证据（无）
所有关键证据均已采集，证据链完整，无可疑缺失项。

---

## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod spec 中配置了 nodeSelector: {"aiops.e2e/nonexistent-node-  │
│ label": "true"}，但集群3个节点均无此标签（真实工具事实 e1, e2） │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 调度器(kube-scheduler)依次检查3个节点(master,node1,node2)，    │
│ 发现所有节点均不满足nodeSelector条件                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┘
│ 直接原因                                                        │
│ 调度器报告 FailedScheduling: 0/3 nodes are available，         │
│ Pod 无法被调度到任何节点（真实工具事实 e3）                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-pending-nodeselector 状态为 Pending，0/1容器未运行，     │
│ 无IP地址，无绑定节点。                                         │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (nodeSelector 配置)、证据 #2 (节点标签列表) 和 证据 #3 (FailedScheduling 事件)，问题的根本原因是 **Pod `rc-pending-nodeselector` 的 `nodeSelector` 引用了集群中不存在的标签 `aiops.e2e/nonexistent-node-label=true`**。

**置信度**：**高 (100%)**
- ✅ 证据 #1 直接显示了错误的配置。
- ✅ 证据 #2 直接证明了集群节点上没有该标签。
- ✅ 证据 #3 是调度器官方输出的错误信息，与上述证据完全吻合。

**补充说明**：该Pod带有标签 `rootcause-e2e=true`，这很可能是一个专门用于演示调度失败的测试Pod，并非生产故障。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [推荐] 删除这个测试用Pod（如果不再需要）**
```bash
kubectl delete pod rc-pending-nodeselector -n aiops-e2e
```
*依据*：该Pod很可能是测试用例，删除后集群将恢复100%健康。

**2. [可选项] 修复 Pod 配置使其调度成功**
*方案A：移除 nodeSelector（允许调度到任何节点）*
```bash
kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml > /tmp/pod.yaml
# 编辑 /tmp/pod.yaml，删除 specs 下的 nodeSelector 字段
# 然后删除并重新创建 Pod
kubectl delete pod rc-pending-nodeselector -n aiops-e2e
kubectl apply -f /tmp/pod.yaml
```

*方案B：给某个节点打上正确的标签*
```bash
kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true
# 将 <node-name> 替换为 master, node1 或 node2
```

### 后续优化
1. **验证配置**：在上线Deployment/StatefulSet等控制器时，检查`nodeSelector`和`affinity`配置是否与集群节点标签匹配。
2. **监控告警**：可配置对 `Pending` 状态超过一定时间的 Pod 进行告警。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认Pod被删除 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | `Error from server (NotFound): pods "rc-pending-nodeselector" not found` |
| 2. 确认集群无异常Pod | `kubectl get pods -A \| grep -v Running \| grep -v Completed` | 无输出（除 Running 和 Completed 外无其他状态） |

---

## ⚠️ 注意事项
- 此问题 **不影响集群中其他59个业务Pod的正常运行**。
- 直接删除该Pod是目前最简单直接的解决方案。如果需要使用该Pod，请参考修复建议中的可选方案。

---

## 📊 性能统计

├─ 总耗时: 1.6m
├─ 问题定位: 30.7s (32%) ✅
├─ 证据链采集: 17.0s (18%) ✅
├─ 根因分析: 25.3s (27%) ✅
├─ 汇总总结: 22.0s (23%) ✅
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
