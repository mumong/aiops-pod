======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 6d33d4670e7549c4]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先从全局 Pod 状态扫描开始，看看集群中所有 Pod 的当前状况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 很好，扫描结果很清晰。让我检查一下这个异常的 Pod 的详情。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  4m11s  default-scheduler  0/3 nodes are available: 3 node(s) di
   💭 [问题定位] 再看一下这个 Pod 的标签信息确认异常类型。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE     IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          4m14s   <none>   <none
   💭 [问题定位] 现在我有了完整的诊断信息。这个异常 Pod 的异常类型明确指向 `PendingUnschedulable`，让我获取对应的 runbook 作为参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在我已经掌握了完整的诊断信息，下面给出分析结果。

---

## 诊断分析

### 当前异常 Pod 总览

| 状态 | 数量 |
|------|------|
| Running（正常） | 59 |
| **Pending（异常）** | **1** |
| **总计** | **60** |

---

### 异常 Pod 详情

| 字段 | 内容 |
|------|------|
| **Pod** | `rc-pending-nodeselector` |
| **命名空间** | `aiops-e2e` |
| **状态** | `Pending` |
| **节点** | 未绑定（`<none>`） |
| **Age** | 约 4 分钟 |

### 调度失败事件原文
> `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.`

### 根因分析

Pod 设置了 `nodeSelector`：
```
Node-Selectors: aiops.e2e/nonexistent-node-label=true
```

集群共有 **3 个节点**，**没有任何节点**拥有 `aiops.e2e/nonexistent-node-label=true` 这个标签，因此调度器无法找到匹配的节点，Pod 一直卡在 Pending。

---

### LayerOutput 结构化

- **layer / derived_layer**: PendingUnschedulable
- **layers**: ["PendingUnschedulable"]
- **layer_name**: 调度约束不匹配导致 Pod Pending
- **confidence**: 高
- **reasoning**: Pod `rc-pending-nodeselector` 处于 Pending 状态，FailedScheduling 事件明确指示"3 node(s) didn't match Pod's node affinity/selector"，Pod 的 nodeSelector 要求节点拥有 `aiops.e2e/nonexistent-node-label=true` 标签，但集群中 3 个节点均无此标签。
- **abnormal_pods**: `['aiops-e2e/rc-pending-nodeselector']`
- **abnormal_groups**: `{'PendingUnschedulable': ['aiops-e2e/rc-pending-nodeselector']}`
- **pod_status_keyword**: `Pending`
- **pod_abnormal_type**: `PendingUnschedulable`
- **status_category**: `scheduling`
- **key_entities**:
  | 实体 | 类型 | 说明 |
  |------|------|------|
  | `rc-pending-nodeselector` | Pod | Pending 异常 Pod |
  | `aiops.e2e/nonexistent-node-label=true` | nodeSelector | 不存在的节点标签选择器 |
  | 3 个节点 | Node | 均无匹配标签，全部不可调度 |
- **possible_scenarios**:
  1. **nodeSelector 标签不存在**（最可能）：Pod 要求节点带有 `aiops.e2e/nonexistent-node-label=true` 标签，但集群中没有一个节点有此标签。
  2. **标签拼写错误**：应用配置中节点标签拼写有误，与实际节点标签不一致。

### 建议修复方向（需人工执行）
- 检查期望节点上应有哪个标签，确认节点是否已打标：`kubectl get nodes --show-labels`
- 如果此标签本应存在，为对应节点打标：`kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`
- 如果标签名拼写错误，修正 Deployment/Workload 中的 nodeSelector 配置
   ✅ [问题定位] 完成 (25.5s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector 标签不存在', 'probability': '高', 'reason': 'Pod 要求节点带有 aiops.e2e/nonexistent-node-label=true 标签，但集群中 3 个节点均无此标签，调度器无法匹配任何节点。'}, {'scenario': '标签拼写错误', 'probability': '中', 'reason': '应用配置中节点标签拼写可能有误，与实际节点标签不一致。'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "nodeSelector", "name": "aiops.e2e/nonexistent-node-label=true", "namespace": ""}, {"type": "Node", "name": "3 个节点（均无匹配标签）", "namespace": ""}]
   reasoning=Pod `rc-pending-nodeselector`（命名空间 aiops-e2e）处于 Pending 状态，未绑定节点（node=<none>）。FailedScheduling 事件明确指示 "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"，Pod 的 nodeSelector 要求节点拥有 `aiops.e2e/nonexistent-node-label=true` 标签，但集群中 3 个节点均无此标签。根据五层模型，PendingUnschedulable（调度约束不匹配）归入 L1（scheduling 层）。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "调度约束不匹配导致 Pod Pending", "confidence": 1.0, "reasoning": "Pod `rc-pending-nodeselector`（命名空间 aiops-e2e）处于 Pending 状态，未绑定节点（node=<none>）。FailedScheduling 事件明确指示 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"，Pod 的 nodeSelector 要求节点拥有 `aiops.e2e/nonexistent-node-label=true` 标签，但集群中 3 个节点均无此标签。根据五层模型，PendingUnschedulable（调度约束不匹配）归入 L1（scheduling 层）。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "nodeSelector", "name": "aiops.e2e/nonexistent-node-label=true", "namespace": ""}, {"type": "Node", "name": "3 个节点（均无匹配标签）", "namespace": ""}], "possible_scenarios": [{"scenario": "nodeSelector 标签不存在", "probability": "高", "reason": "Pod 要求节点带有 aiops.e2e/nonexistent-node-label=true 标签，但集群中 3 个节点均无此标签，调度器无法匹配任何节点。"}, {"scenario": "标签拼写错误", "probability": "中", "reason": "应用配置中节点标签拼写可能有误，与实际节点标签不一致。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              4m10s   <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/6d33d4670e7549c4/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/6d33d4670e7549c4/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/6d33d4670e7549c4/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 100%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我直接执行既有 evidence_plan 中的工具调用。先执行相互独立的几个 critical 级任务。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "master\t{\"beta.kubernetes.io/arch\":\"amd64\",\"beta.kubernetes.io/os\":\"linux\",\"fpga-version\":\"\",\"kubernetes.io/arch\":\"amd64\",\"kubernetes.io/hostname\":\"mast
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
4m46s       Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are
   💭 [证据链采集] 三个 critical 级证据已全部返回。接下来执行 important 级的计划项 e4。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAME                      READY   STATUS    RESTARTS   AGE     IP       NODE     NOMINATED NODE   READINESS GATES\nrc-pending-nodeselector   0/1     Pending   0          4
   💭 [证据链采集] 所有计划项已执行完毕，以下是采集证据总结：

---

## 证据采集结论

### ✅ 已采集证据（全部验证通过）

**e1 - Pod YAML 配置验证 ✅**
- Pod `rc-pending-nodeselector` 的 `nodeSelector` 明确配置为：**`{"aiops.e2e/nonexistent-node-label": "true"}`**
- Pod phase = Pending，nodeName = None，未绑定任何节点
- 调度条件 `PodScheduled=False`，reason=Unschedulable

**e2 - FailedScheduling 事件原文 ✅**
- `Warning FailedScheduling`：**"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling."**
- 明确指向节点标签不匹配，非资源不足或 taint 问题

**e3 - 3 个节点标签验证 ✅**
- **master**：标签含 `kubernetes.io/hostname=master`、`node-role.kubernetes.io/control-plane` 等，**无 `aiops.e2e/nonexistent-node-label`**
- **node1**：标签含 `kubernetes.io/hostname=node1` 等，**无 `aiops.e2e/nonexistent-node-label`**
- **node2**：标签含 `kubernetes.io/hostname=node2` 等，**无 `aiops.e2e/nonexistent-node-label`**
- ✅ **确认 3 个节点均不存在 `aiops.e2e/nonexistent-node-label` 标签**

**e4 - aiops-e2e 命名空间异常 Pod 覆盖验证 ✅**
- 除 `rc-pending-nodeselector` 外，该命名空间无其他非 Running/非 Succeeded 状态的 Pod
- 无并发异常组需要覆盖

### 🔍 根因分析
Pod `rc-pending-nodeselector` 的 `nodeSelector` 要求节点带有标签 **`aiops.e2e/nonexistent-node-label=true`**，但集群中 3 个节点（master、node1、node2）均无此标签，调度器无法匹配任何可用节点，导致 Pod 持续 Pending。

### 📋 建议修复方向
1. 为其中一个节点添加目标标签：`kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`
2. 或修正 Pod 的 `nodeSelector` 为集群中实际存在的标签
   ✅ [证据链采集] 完成 (22.5s)
   📤 → 下游数据: evidence_items=6/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod rc-pending-nodeselector 的当前状态和详细 spec（重点 nodeSelector 字段）","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e","resource":"pod","output":"yaml"},"purpose":"确认 nodeSelector 配置和当前状态","evidence_type":"pod_spec","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod 最新 Events，确认 FailedScheduling 具体原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-nodeselector --sort-by=.lastTimestamp","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-pending-nodeselector","sort_by":".lastTimestamp"},"purpose":"确认 FailedScheduling 事件原文","evidence_type":"events","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_events","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"查看集群所有节点的标签，验证哪个节点包含 nodeSelector 要求的标签","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{\"\\t\"}{.metadata.labels}{\"\\n\"}{end}'","tool_args":{"command":"kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{\"\\t\"}{.metadata.labels}{\"\\n\"}{end}'"},"purpose":"验证 3 个节点均无 aiops.e2e/nonexistent-node-label=true 标签","evidence_type":"node_labels","target_scope":"Node/集群全部节点","acceptable_tools":["run_bash_command","kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true},{"id":"e4","description":"验证异常组 g1 的 Pod 是否仍存在，确认无其他并发异常组","level":"important","tool":"run_bash_command","command":"kubectl get pods -n aiops-e2e --field-selector=status.phase!=Running,status.phase!=Succeeded -o wide","tool_args":{"command":"kubectl get pods -n aiops-e2e --field-selector=status.phase!=Running,status.phase!=Succeeded -o wide"},"purpose":"确认 aiops-e2e 命名空间中无其他非 Running 状态的 Pod","evidence_type":"pod_list","target_scope":"Namespace/aiops-e2e","acceptable_tools":["run_bash_command","kubectl_get_by_kind_in_namespace"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"master\\t{\\\"beta.kubernetes.io/arch\\\":\\\"amd64\\\",\\\"beta.kubernetes.io/os\\\":\\\"linux\\\",\\\"fpga-version\\\":\\\"\\\",\\\"kubernetes.io/arch\\\":\\\"amd64\\\",\\\"kubernetes.io/hostname\\\":\\\"master\\\",\\\"kubernetes.io/os\\\":\\\"linux\\\",\\\"metax-tech.com/gpu.installed\\\":\\\"false\\\",\\\"node-role.kubernetes.io/control-plane\\\":\\\"\\\",\\\"node.kubernetes.io/exclude-from-external-load-balancers\\\":\\\"\\\"}\\nnode1\\t{\\\"beta.kubernetes.io/arch\\\":\\\"amd64\\\",\\\"beta.kubernetes.io/os\\\":\\\"linux\\\",\\\"fpga-version\\\":\\\"\\\",\\\"kubernetes.io/arch\\\":\\\"amd64\\\",\\\"kubernetes.io/hostname\\\":\\\"node1\\\",\\\"kubernetes.io/os\\\":\\\"linux\\\",\\\"metax-tech.com/gpu.installed\\\":\\\"false\\\"}\\nnode2\\t{\\\"beta.kubernetes.io/arch\\\":\\\"amd64\\\",\\\"beta.kubernetes.io/os\\\":\\\"linux\\\",\\\"fpga-version\\\":\\\"\\\",\\\"kubernetes.io/arch\\\":\\\"amd64\\\",\\\"kubernetes.io/hostname\\\":\\\"node2\\\",\\\"kubernetes.io/os\\\":\\\"linux\\\",\\\"metax-tech.com/gpu.installed\\\":\\\"false\\\"}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6d33d4670e7549c4/tools/001-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6d33d4670e7549c4/tools/001-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6d33d4670e7549c4/tools/001-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6d33d4670e7549c4/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6d33d4670e7549c4/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6d33d4670e7549c4/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n4m46s       Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6d33d4670e7549c4/tools/003-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6d33d4670e7549c4/tools/003-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6d33d4670e7549c4/tools/003-evidence-kubectl_events.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAME                      READY   STATUS    RESTARTS   AGE     IP       NODE     NOMINATED NODE   READINESS GATES\\nrc-pending-nodeselector   0/1     Pending   0          4m48s   <none>   <none>   <none>           <none>\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6d33d4670e7549c4/tools/004-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6d33d4670e7549c4/tools/004-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6d33d4670e7549c4/tools/004-evidence-run_bash_command.summary.txt"}],"llm_analysis":"所有计划项已执行完毕，以下是采集证据总结：\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据（全部验证通过）\n\n**e1 - Pod YAML 配置验证 ✅**\n- Pod `rc-pending-nodeselector` 的 `nodeSelector` 明确配置为：**`{\"aiops.e2e/nonexistent-node-label\": \"true\"}`**\n- Pod phase = Pending，nodeName = None，未绑定任何节点\n- 调度条件 `PodScheduled=False`，reason=Unschedulable\n\n**e2 - FailedScheduling 事件原文 ✅**\n- `Warning FailedScheduling`：**\"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.\"**\n- 明确指向节点标签不匹配，非资源不足或 taint 问题\n\n**e3 - 3 个节点标签验证 ✅**\n- **master**：标签含 `kubernetes.io/hostname=master`、`node-role.kubernetes.io/control-plane` 等，**无 `aiops.e2e/nonexistent-node-label`**\n- **node1**：标签含 `kubernetes.io/hostname=node1` 等，**无 `aiops.e2e/nonexistent-node-label`**\n- **node2**：标签含 `kubernetes.io/hostname=node2` 等，**无 `aiops.e2e/nonexistent-node-label`**\n- ✅ **确认 3 个节点均不存在 `aiops.e2e/nonexistent-node-label` 标签**\n\n**e4 - aiops-e2e 命名空间异常 Pod 覆盖验证 ✅**\n- 除 `rc-pending-nodeselector` 外，该命名空间无其他非 Running/非 Succeeded 状态的 Pod\n- 无并发异常组需要覆盖\n\n### 🔍 根因分析\nPod `rc-pending-nodeselector` 的 `nodeSelector` 要求节点带有标签 **`aiops.e2e/nonexistent-node-label=true`**，但集群中 3 个节点（master、node1、node2）均无此标签，调度器无法匹配任何可用节点，导致 Pod 持续 Pending。\n\n### 📋 建议修复方向\n1. 为其中一个节点添加目标标签：`kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`\n2. 或修正 Pod 的 `nodeSelector` 为集群中实际存在的标签","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 6/7 项，完整度 86%；实际执行工具 7 个，匹配计划 3 个，未规划证据 4 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":7,"environment_evidence_collected":6,"environment_evidence_completeness":0.8571428571428571,"executed_tool_count":7,"matched_tool_count":3,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证 Pod rc-pending-nodeselector 的当前状态和详细 spec（重点 nodeSelector 字段）","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"确认 nodeSelector 配置和当前状态","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod 最新 Events，确认 FailedScheduling 具体原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-nodeselector --sort-by=.lastTimestamp","purpose":"确认 FailedScheduling 事件原文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"查看集群所有节点的标签，验证哪个节点包含 nodeSelector 要求的标签","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{\"\\t\"}{.metadata.labels}{\"\\n\"}{end}'","purpose":"验证 3 个节点均无 aiops.e2e/nonexistent-node-label=true 标签","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"验证异常组 g1 的 Pod 是否仍存在，确认无其他并发异常组","level":"important","tool":"run_bash_command","command":"kubectl get pods -n aiops-e2e --field-selector=status.phase!=Running,status.phase!=Succeeded -o wide","purpose":"确认 aiops-e2e 命名空间中无其他非 Running 状态的 Pod","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e4(验证异常组 g1 的 Pod 是否仍存在，确认无其他并发异常组): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 86%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 验证 Pod rc-pending-nodeselector 的当前状态和详细 spec（... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_events | 获取 Pod 最新 Events，确认 FailedScheduling 具体原因 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pendi...` |
   | e3 | critical | ✅ | run_bash_command | 查看集群所有节点的标签，验证哪个节点包含 nodeSelector 要求的标签 | `kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metad...` |
   | e4 | important | ❌ | run_bash_command | 验证异常组 g1 的 Pod 是否仍存在，确认无其他并发异常组 | `kubectl get pods -n aiops-e2e --field-selector=status.phase!=Running,status.p...` |

   ⚠️ 未采集原因:
   - e4(验证异常组 g1 的 Pod 是否仍存在，确认无其他并发异常组): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (25.6s)
   📤 → 下游数据: root_cause=Pod `rc-pending-nodeselector`（aiops-e2e 命名空间）处于 Pending 状态的根因是 **nodeSelector 标签不匹配**。Pod YAML 显示 nodeSelector 为 `{"aiops.e2e/nonexistent-node-label": "true"}`，调度器 Events 确认 "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"。节点标签查询结果（e3）验证 master、node1、node2 三个节点的标签列表中均不包含 `aiops.e2e/nonexistent-node-label`。PodScheduled 条件为 False（reason=Unschedulable）。集群其余 59 个 Pod 均正常运行，无其他异常。建议：为任一节点添加该标签（`kubectl label node <node> aiops.e2e/nonexistent-node-label=true`）或修正 Pod 的 no
... 截断，原始 523 字符
   confidence=100%
   causal_chain={"root_cause": "Pod 的 nodeSelector 配置了 aiops.e2e/nonexistent-node-label=true，但集群 3 个节点均无此标签。", "propagation": "调度器 default-scheduler 检查所有 3 个节点的标签，均不满足 nodeSelector 约束 → 标记 PodScheduled=False（Unschedulable）→ Pod 持续 Pending 状态。", "direct_cause": "集群中没有任何节点拥有 aiops.e2e/nonexistent-node-label 标签，调度器无法找到匹配节点。", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中保持 Pending 状态，Events 显示 FailedScheduling，node=&lt;none&gt;，IP=&lt;none&gt;。"}
   rca_analysis={"phenomenon": "Pod `rc-pending-nodeselector`（命名空间 aiops-e2e）处于 Pending 状态，0/1 容器就绪，未绑定节点（node=&lt;none&gt;），创建约 4 分 48 秒。调度条件 PodScheduled=False，reason=Unschedulable。集群中共 65 个 Pod，59 个 Running，仅此 1 个异常。", "evidence_inventory": [{"id": "e1", "source": "kubectl_get_yaml", "content": "Pod rc-pending-nodeselector 的 nodeSelector 为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}，phase=Pending，nodeName=None，PodScheduled=False reason=Unschedulable", "reliability": "高"}, {"id": "e2", "source": "kubectl_events", "content": "Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}, {"id": "e3", "source": "run_bash_command（节点标签查询）", "content": "3 个节点（master, node1, node2）的标签列表均不包含 aiops.e2e/nonexistent-node-label", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster（上游验证）", "content": "集群共 65 个 Pod，Pending 仅此 1 个，命名空间 aiops-e2e 无其他异常 Pod", "reliability": "高"}, {"id": "layer_2", "source": "kubectl_describe（上游验证）", "content": "Node-Selectors: aiops.e2e/nonexistent-node-label=true；QoS Class: BestEffort", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}, phase: Pending, nodeName: None, conditions: PodScheduled=False reason=Unschedulable", "interpretation": "Pod 明确要求调度到带有 aiops.e2e/nonexistent-node-label=true 标签的节点，但当前未绑定任何节点，调度器判定为不可调度。"}, {"evidence_id": "e2", "raw_data": "Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "interpretation": "调度器明确报告 3 个节点均不匹配 Pod 的节点亲和性/选择器，确认不是资源不足或 taint 问题。"}, {"evidence_id": "e3", "raw_data": "master 标签: hostname=master,control-plane; node1 标签: hostname=node1; node2 标签: hostname=node2 — 均无 aiops.e2e/nonexistent-node-label", "interpretation": "集群全部 3 个节点均未配置 aiops.e2e/nonexistent-node-label 标签，导致 Pod 的 nodeSelector 无法匹配任何节点。"}, {"evidence_id": "layer_1", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}", "interpretation": "集群整体健康，仅此 1 个异常 Pod，无并发异常组需要覆盖。"}, {"evidence_id": "layer_2", "raw_data": "Node-Selectors: aiops.e2e/nonexistent-node-label=true; QoS Class: BestEffort", "interpretation": "与 e1 的 nodeSelector 内容一致，交叉验证确认。QoS BestEffort 说明 Pod 无资源请求限制，排除资源不足场景。"}], "causal_chain": {"root_cause": "Pod 的 nodeSelector 配置了 aiops.e2e/nonexistent-node-label=true，但集群 3 个节点均无此标签。", "propagation": "调度器 default-scheduler 检查所有 3 个节点的标签，均不满足 nodeSelector 约束 → 标记 PodScheduled=False（Unschedulable）→ Pod 持续 Pending 状态。", "direct_cause": "集群中没有任何节点拥有 aiops.e2e/nonexistent-node-label 标签，调度器无法找到匹配节点。", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中保持 Pending 状态，Events 显示 FailedScheduling，node=&lt;none&gt;，IP=&lt;none&gt;。"}, "root_cause": "Pod `rc-pending-nodeselector`（aiops-e2e 命名空间）处于 Pending 状态的根因是 **nodeSelector 标签不匹配**。Pod YAML 显示 nodeSelector 为 `{\"aiops.e2e/nonexistent-node-label\": \"true\"}`，调度器 Events 确认 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"。节点标签查询结果（e3）验证 master、node1、node2 三个节点的标签列表中均不包含 `aiops.e2e/nonexistent-node-label`。PodScheduled 条件为 False（reason=Unschedulable）。集群其余 59 个 Pod 均正常运行，无其他异常。建议：为任一节点添加该标签（`kubectl label node <node> aiops.e2e/nonexistent-node-label=true`）或修正 Pod 的 no\n... 截断，原始 523 字符", "root_cause_summary": "Pod `rc-pending-nodeselector`（aiops-e2e 命名空间）处于 Pending 状态的根因是 **nodeSelector 标签不匹配**。Pod YAML 显示 nodeSelector 为 `{\"aiops.e2e/nonexistent-node-label\": \"true\"}`，调度器 Events 确认 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"。节点标签查询结果（e3）验证 master、node1、node2 三个节点的标签列表中均不包含 `aiops.e2e/nonexistent-node-label`。PodScheduled 条件为 False（reason=Unschedulable）。集群其余 59 个 Pod 均正常运行，无其他异常。建议：为任一节点添加该标签（`kubectl label node <node> aiops.e2e/nonexistent-node-label=true`）或修正 Pod 的 no\n... 截断，原始 523 字符", "confidence": 1.0, "confidence_reason": "直接证据完整且因果链清晰：kubectl_get_yaml 直接展示 nodeSelector 配置（e1），kubectl_events 明确报告调度失败原因是节点标签不匹配（e2），节点标签查询（e3）逐一验证 3 个节点均无目标标签，三条证据交叉印证无矛盾。QoS BestEffort 排除了资源不足场景。无任何缺失关键证据。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "资源不足（CPU/内存不足）导致无法调度", "probability": "low", "reason": "FailedScheduling 消息明确为标签不匹配，非 Insufficient cpu/memory；QoS Class=BestEffort 说明 Pod 无资源请求限制，不存在资源不足。"}, {"cause": "节点 taint 未被 toleration 容忍", "probability": "low", "reason": "FailedScheduling 消息为标签不匹配，非 taint/toleration 相关错误；且 Pod 已有 2 个 tolerations（含 node.kubernetes.io/not-ready）"}, {"cause": "PVC 未绑定导致调度阻塞", "probability": "low", "reason": "Pod 无 PVC 卷声明，仅有 kube-api-access 默认卷，不涉及存储前置条件问题。"}], "limitations": "证据充分，无重大缺失。缺失证据项 e4（验证并发异常组）已由上游 layer_1 数据间接覆盖——集群仅此 1 个 Pending Pod，无并发异常组。节点标签名称 aiops.e2e/nonexistent-node-label 本身暗示这是一个测试场景用的标签名。", "llm_raw_analysis": "## 证据清点\n已采集 5 条有效证据：e1（Pod YAML nodeSelector）、e2（FailedScheduling 事件）、e3（3 个节点标签列表）、layer_1（集群整体 Pod 状态统计）、layer_2（kubectl_describe 交叉验证）。\n\n## 逐条分析\n- **e1**：Pod 明确要求 nodeSelector = {\"aiops.e2e/nonexistent-node-label\": \"true\"}，当前 phase=Pending，nodeName=None，PodScheduled=False reason=Unschedulable——这是最直接的配置证据。\n- **e2**：调度器事件原文确认所有 3 个节点均不匹配 Pod 的节点亲和性/选择器，排除资源不足和 taint 可能性。\n- **e3**：逐一列出 3 个节点的所有标签，均不含 aiops.e2e/nonexistent-node-label，直接验证了不匹配的原因。\n- **layer_1**：集群 65 Pods 中仅此 1 个 Pending，说明问题隔离，无并\n... 截断，原始 825 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod `rc-pending-nodeselector`（aiops-e2e 命名空间）处于 Pending 状态的根因是 **nodeSelector 标签不匹配**。Pod YAML 显示 nodeSelector 为 `{"aiops.e2e/nonexistent-node-label":...
   置信度: 100%
   🔗 因果链:
     根本原因: Pod 的 nodeSelector 配置了 aiops.e2e/nonexistent-node-label=true，但集群 3 个节点均无此标签。
     传导机制: 调度器 default-scheduler 检查所有 3 个节点的标签，均不满足 nodeSelector 约束 → 标记 PodScheduled=False（Unschedulable）→ Pod 持续 Pending 状态。
     最终表现: Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中保持 Pending 状态，Events 显示 FailedScheduling，node=&lt;none&gt;，IP=&lt;none&gt;。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (23.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5105 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 37.5s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，这是为您生成的 K8s 诊断报告。

---

## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending |
| **兼容归因层** | L1 - 调度层 (Scheduling) |
| **问题分类** | PendingUnschedulable (调度约束不匹配) |
| **置信度** | 高 (100%) |
| **证据完整度** | 3/4 (75%) |

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| **问题实体** | 命名空间 `aiops-e2e` 下的 Pod `rc-pending-nodeselector` |
| **核心标签** | `aiops.e2e/nonexistent-node-label=true` |
| **集群节点** | 3个 (master, node1, node2) |

**集群整体状态**：
集群共有 65 个 Pod，其中 59 个正常运行，只有 **1 个 Pod 出现异常**。该 Pod 因调度失败而持续处于 **Pending** 状态。

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态与配置 | `kubectl get yaml` | `phase: Pending`, `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}` | Pod 配置了节点选择器，要求节点带有特定标签。 |
| 2 | Pod 事件 | `kubectl events` | `Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` | 调度器明确告知3个节点均不满足Pod的nodeSelector条件，且抢占也无法帮助调度。 |
| 3 | 节点标签 | `run_bash_command` (`kubectl get nodes --show-labels`) | `master: *** (无 aiops.e2e/nonexistent-node-label)`, `node1: *** (无 aiops.e2e/nonexistent-node-label)`, `node2: *** (无 aiops.e2e/nonexistent-node-label)` | 集群中所有3个节点的标签列表均不包含Pod要求的 `aiops.e2e/nonexistent-node-label` 标签。 |

### 证据关联分析

- **证据 #1 + #2 + #3 印证**：Pod `rc-pending-nodeselector` 的 YAML 配置明确要求节点标签 `aiops.e2e/nonexistent-node-label=true`（证据 #1），但集群中3个节点均无此标签（证据 #3），导致调度器无法找到匹配节点，触发 `FailedScheduling` 事件（证据 #2），Pod 因此无限期停留在 Pending 状态。

- **证据链**：**Pod 配置** (nodeSelector) → **调度器检查** (3个节点均不匹配) → **调度失败** (FailedScheduling事件) → **Pod 状态** (Pending)

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| ✅ 无关键证据缺失 | —— | 核心证据链完整，足以确诊。上游 `layer_1` 数据间接确认集群无其他并发异常组，因此缺失项 e4 影响极小。 |

## 🎯 根因分析

### 因果链

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                     │
│ Pod `rc-pending-nodeselector` 的 spec 配置了 nodeSelector                    │
│ `aiops.e2e/nonexistent-node-label=true`，但集群3个节点均无此标签。           │
└──────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                     │
│ 调度器 `default-scheduler` 遍历所有3个节点，根据 nodeSelector 做标签匹配，   │
│ 全部失败 → 标记 PodScheduled=False（Unschedulable）。                         │
└──────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                     │
│ 集群中没有任何节点匹配 Pod 要求的标签，调度器无法找到可用节点。               │
└──────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                 │
│ Pod `rc-pending-nodeselector` 在命名空间 `aiops-e2e` 中持续处于 Pending 状态，│
│ 事件中包含 `FailedScheduling` 警告，Node 和 IP 均显示为 <none>。              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 **#1** (Pod YAML nodeSelector 配置) 和证据 **#3** (节点标签列表不包含该标签)，以及证据 **#2** (调度器事件 `FailedScheduling`)，此问题的根本原因是：

**Pod `rc-pending-nodeselector` 的 `nodeSelector` 配置了一个集群中不存在的标签 `aiops.e2e/nonexistent-node-label=true`，导致调度器找不到任何可用节点。**

**置信度**：高 (100%)
- ✅ 三个核心证据（Pod YAML、事件、节点标签）相互印证，形成完整证据链。
- ✅ 标签名称 `aiops.e2e/nonexistent-node-label` 本身暗示这是一个测试场景或配置错误的标签。
- ✅ 集群中其他 59 个Pod均正常运行，排除了集群层面的通用性问题。

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先方案] 为任一节点添加缺失的标签**（如果该标签是预期需要的）
```bash
# 为 node1 节点添加标签
kubectl label node node1 aiops.e2e/nonexistent-node-label=true --context=<your-context>
```
*依据*：为节点添加此标签后，Pod 将匹配该节点并被调度上去运行。

**2. [常用方案] 修正 Pod 的 `nodeSelector` 为现有标签**（如果节点标签不可修改）
```bash
# 第一步：删除旧 Pod (如果有 Deployment/StatefulSet 管理则需修改其 YAML)
kubectl delete pod rc-pending-nodeselector -n aiops-e2e

# 第二步：重新创建 Pod（或在Deployment/Job YAML中修改 spec.nodeSelector）
# 例如，将 nodeSelector 改为集群中现有的标签，如 `kubernetes.io/hostname: node1`
```
*依据*：移除或修正 Pod 对不存在的标签的依赖，使其能与现有节点匹配。

### 后续优化

1. **勘误与审计**：核实应用配置中 `nodeSelector` 的标签名 `aiops.e2e/nonexistent-node-label` 是否正确，避免在生产环境出现类似的拼写错误或配置不当。
2. **准入控制**：考虑使用 **PodNodeSelector** 或 **OPA/Gatekeeper** 等准入控制器，对 `nodeSelector` 中的标签进行校验，确保其指向集群中真实存在的标签。

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 添加标签后检查 Pod | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -w` | STATUS 从 `Pending` 变为 `Running` |
| 2. 确认 Pod 所在节点 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o wide` | `NODE` 列显示为节点名称（如 `node1`），不再是 `<none>` |

## ⚠️ 注意事项

- `FailedScheduling` 事件是一个关键诊断信号，表明问题是调度层面的，而不是节点或网络层面的。如果添加标签后问题依旧，请检查 Pod 是否还有其他约束，如 `affinity`、`taints/tolerations` 或资源请求超过节点容量。
- 集群当前有且仅有此一个异常 Pod，其余应用运行正常，无需担心集群整体健康度。

---

## 📊 性能统计

├─ 总耗时: 1.6m
├─ 问题定位: 25.5s (26%) ✅
├─ 证据链采集: 22.5s (23%) ✅
├─ 根因分析: 25.6s (26%) ✅
├─ 汇总总结: 23.9s (25%) ✅
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
