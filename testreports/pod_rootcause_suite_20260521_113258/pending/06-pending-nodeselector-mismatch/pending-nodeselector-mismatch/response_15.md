======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 5e6c09c9b7e74133]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我先全局扫描集群中的所有 Pod 状态，来识别当前存在的异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 我发现了一个异常的 Pod。让我进一步了解它的详情。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          10m   <none>   <none>   
   💭 [问题定位] 这个 Pod 的 label 标记了 `pod_abnormal_type=PendingUnschedulable`，让我获取详细信息和 Events。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  10m    default-scheduler  0/3 nodes are available: 3 node(s) di
   💭 [问题定位] 这个 Pod 非常明确地指向了 **PendingUnschedulable** 异常类型，让我获取对应的 runbook 作为参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在我已经有了足够的信息来做定位分析。以下是完整诊断结果。

---

## 集群 Pod 异常定位分析

### 全局扫描结果

集群共有 **65 个 Pod**，其中 **59 个 Running**（正常），**1 个 Pending**（异常）。

### 异常 Pod 清单

| 命名空间 | Pod 名称 | 状态 | 原因 |
|---------|---------|------|------|
| `aiops-e2e` | `rc-pending-nodeselector` | **Pending** | 调度失败 |

### 异常详情

**Pod:** `rc-pending-nodeselector`（命名空间: `aiops-e2e`）

| 字段 | 内容 |
|------|------|
| **STATUS** | Pending（卡在调度阶段，未绑定节点） |
| **Age** | 10分钟 |
| **QoS Class** | BestEffort |
| **Node-Selectors** | `aiops.e2e/nonexistent-node-label=true` |
| **调度事件** | `FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` |

### 根因分析

**明确的根因：nodeSelector 不匹配**

Pod 设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，但集群中所有 **3 个节点** 均不包含此标签，导致调度器无法找到可调度的节点。

### 定位输出

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **layer_name** | PendingUnschedulable |
| **pod_status_keyword** | Pending |
| **pod_abnormal_type** | PendingUnschedulable |
| **status_category** | scheduling |
| **confidence** | 高 |
| **possible_scenarios** | nodeSelector 标签不匹配导致所有候选节点被排除 |
| **key_entities** | Pod: `aiops-e2e/rc-pending-nodeselector`, Node: 集群内所有3个节点 |

### 后续审查方向（供 evidence 节点参考）

1. 确认 `nodeSelector` 中标签 `aiops.e2e/nonexistent-node-label=true` 是否为真实意图
2. 检查集群节点标签列表，确认是否存在预期标签
3. 如该标签应存在但缺失，需在目标节点上添加对应标签
   ✅ [问题定位] 完成 (21.8s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector标签不匹配导致所有候选节点被排除', 'probability': '高', 'reason': "Pod设置了nodeSelector: aiops.e2e/nonexistent-node-label=true，但3个节点均不包含此标签；Events明确显示FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Node", "name": "集群内所有3个节点", "namespace": ""}]
   reasoning=集群中存在1个异常Pod：aiops-e2e/rc-pending-nodeselector，状态为Pending，调度失败。根因为nodeSelector标签不匹配（aiops.e2e/nonexistent-node-label=true），所有3个节点均被排除。该异常属于调度约束不匹配，归为L1层（scheduling）。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "集群中存在1个异常Pod：aiops-e2e/rc-pending-nodeselector，状态为Pending，调度失败。根因为nodeSelector标签不匹配（aiops.e2e/nonexistent-node-label=true），所有3个节点均被排除。该异常属于调度约束不匹配，归为L1层（scheduling）。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Node", "name": "集群内所有3个节点", "namespace": ""}], "possible_scenarios": [{"scenario": "nodeSelector标签不匹配导致所有候选节点被排除", "probability": "高", "reason": "Pod设置了nodeSelector: aiops.e2e/nonexistent-node-label=true，但3个节点均不包含此标签；Events明确显示FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              10m     <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/5e6c09c9b7e74133/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/5e6c09c9b7e74133/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/5e6c09c9b7e74133/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我按照既有 evidence_plan 直接执行真实工具采证。先从 Pod YAML、Node 标签和 Events 三个关键维度入手。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_events
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
10m                   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3
   💭 [证据链采集] ## 证据采集完成 — 结论

### ✅ 已采集证据

| 证据项 | 来源 | 结果 |
|--------|------|------|
| **Pod YAML (e1)** | `kubectl_get_yaml` | 确认 `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}` ✅ |
| **Node 标签列表 (e2)** | `kubectl get nodes -o jsonpath` | 3 个节点（master/node1/node2）均**不包含** `aiops.e2e/nonexistent-node-label` 标签 ✅ |
| **Events 详情 (e4)** | `kubectl_events` | 2 次 FailedScheduling：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` ✅ |

### 📋 证据综合分析

**根因已锁定：**
- Pod `rc-pending-nodeselector` 设置了 `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}`
- 集群所有 3 个节点（master/node1/node2）均**没有**这个标签
- 调度器判定 `0/3 nodes are available`，所有节点均被排除
- 这是纯粹的**调度约束不匹配**问题，非资源不足、PVC 或节点异常

**负向证据（排除其他场景）：**
- 无资源不足信号（未出现 `Insufficient cpu/memory`）
- 所有节点均为 Ready 状态（无 `NotReady/Unschedulable`）
- 无 PVC 依赖（仅 kube-api-access 默认卷）

### 🛠 建议修复方向

删除或修正 Pod 的 `nodeSelector` 配置，移除 `aiops.e2e/nonexistent-node-label=true`，或为节点添加对应标签。
   ✅ [证据链采集] 完成 (18.6s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod rc-pending-nodeselector 的完整 YAML spec（nodeSelector/affinity 配置）","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e","resource":"pod","output":"yaml"},"purpose":"确认 Pod 的 nodeSelector/affinity 具体配置，验证上游所述 nodeSelector: aiops.e2e/nonexistent-node-label=true","evidence_type":"spec_config","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e2","description":"验证所有3个节点的标签，确认为何无法匹配 Pod 的 nodeSelector","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{\"\\t\"}{.metadata.labels}{\"\\n\"}{end}'","tool_args":{"command":"kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{\"\\t\"}{.metadata.labels}{\"\\n\"}{end}'"},"purpose":"获取所有节点的标签列表，确认是否包含 Pod 所需的标签 aiops.e2e/nonexistent-node-label","evidence_type":"node_labels","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"验证 Pod 的当前 Events（FailedScheduling 原文）","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-nodeselector --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-pending-nodeselector","sort_by":".lastTimestamp"},"purpose":"确认 FailedScheduling 事件的详细信息，验证是否与 nodeSelector 不匹配相关","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"master\\t{\\\"beta.kubernetes.io/arch\\\":\\\"amd64\\\",\\\"beta.kubernetes.io/os\\\":\\\"linux\\\",\\\"fpga-version\\\":\\\"\\\",\\\"kubernetes.io/arch\\\":\\\"amd64\\\",\\\"kubernetes.io/hostname\\\":\\\"master\\\",\\\"kubernetes.io/os\\\":\\\"linux\\\",\\\"metax-tech.com/gpu.installed\\\":\\\"false\\\",\\\"node-role.kubernetes.io/control-plane\\\":\\\"\\\",\\\"node.kubernetes.io/exclude-from-external-load-balancers\\\":\\\"\\\"}\\nnode1\\t{\\\"beta.kubernetes.io/arch\\\":\\\"amd64\\\",\\\"beta.kubernetes.io/os\\\":\\\"linux\\\",\\\"fpga-version\\\":\\\"\\\",\\\"kubernetes.io/arch\\\":\\\"amd64\\\",\\\"kubernetes.io/hostname\\\":\\\"node1\\\",\\\"kubernetes.io/os\\\":\\\"linux\\\",\\\"metax-tech.com/gpu.installed\\\":\\\"false\\\"}\\nnode2\\t{\\\"beta.kubernetes.io/arch\\\":\\\"amd64\\\",\\\"beta.kubernetes.io/os\\\":\\\"linux\\\",\\\"fpga-version\\\":\\\"\\\",\\\"kubernetes.io/arch\\\":\\\"amd64\\\",\\\"kubernetes.io/hostname\\\":\\\"node2\\\",\\\"kubernetes.io/os\\\":\\\"linux\\\",\\\"metax-tech.com/gpu.installed\\\":\\\"false\\\"}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/5e6c09c9b7e74133/tools/001-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/5e6c09c9b7e74133/tools/001-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/5e6c09c9b7e74133/tools/001-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/5e6c09c9b7e74133/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/5e6c09c9b7e74133/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/5e6c09c9b7e74133/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n10m                   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n12s (x2 over 5m12s)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/5e6c09c9b7e74133/tools/003-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/5e6c09c9b7e74133/tools/003-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/5e6c09c9b7e74133/tools/003-evidence-kubectl_events.summary.txt"}],"llm_analysis":"## 证据采集完成 — 结论\n\n### ✅ 已采集证据\n\n| 证据项 | 来源 | 结果 |\n|--------|------|------|\n| **Pod YAML (e1)** | `kubectl_get_yaml` | 确认 `nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}` ✅ |\n| **Node 标签列表 (e2)** | `kubectl get nodes -o jsonpath` | 3 个节点（master/node1/node2）均**不包含** `aiops.e2e/nonexistent-node-label` 标签 ✅ |\n| **Events 详情 (e4)** | `kubectl_events` | 2 次 FailedScheduling：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` ✅ |\n\n### 📋 证据综合分析\n\n**根因已锁定：**\n- Pod `rc-pending-nodeselector` 设置了 `nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}`\n- 集群所有 3 个节点（master/node1/node2）均**没有**这个标签\n- 调度器判定 `0/3 nodes are available`，所有节点均被排除\n- 这是纯粹的**调度约束不匹配**问题，非资源不足、PVC 或节点异常\n\n**负向证据（排除其他场景）：**\n- 无资源不足信号（未出现 `Insufficient cpu/memory`）\n- 所有节点均为 Ready 状态（无 `NotReady/Unschedulable`）\n- 无 PVC 依赖（仅 kube-api-access 默认卷）\n\n### 🛠 建议修复方向\n\n删除或修正 Pod 的 `nodeSelector` 配置，移除 `aiops.e2e/nonexistent-node-label=true`，或为节点添加对应标签。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 6 个，匹配计划 3 个，未规划证据 3 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":3,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"验证 Pod rc-pending-nodeselector 的完整 YAML spec（nodeSelector/affinity 配置）","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"确认 Pod 的 nodeSelector/affinity 具体配置，验证上游所述 nodeSelector: aiops.e2e/nonexistent-node-label=true","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证所有3个节点的标签，确认为何无法匹配 Pod 的 nodeSelector","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{\"\\t\"}{.metadata.labels}{\"\\n\"}{end}'","purpose":"获取所有节点的标签列表，确认是否包含 Pod 所需的标签 aiops.e2e/nonexistent-node-label","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"验证 Pod 的当前 Events（FailedScheduling 原文）","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-nodeselector --sort-by='.lastTimestamp'","purpose":"确认 FailedScheduling 事件的详细信息，验证是否与 nodeSelector 不匹配相关","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 验证 Pod rc-pending-nodeselector 的完整 YAML spec（... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | run_bash_command | 验证所有3个节点的标签，确认为何无法匹配 Pod 的 nodeSelector | `kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metad...` |
   | e4 | critical | ✅ | kubectl_events | 验证 Pod 的当前 Events（FailedScheduling 原文） | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pendi...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (19.4s)
   📤 → 下游数据: root_cause=Pod aiops-e2e/rc-pending-nodeselector 因 nodeSelector 约束无法调度：其配置要求调度到带有 aiops.e2e/nonexistent-node-label=true 标签的节点，但集群 3 个节点（master、node1、node2）均不包含此标签。kubectl_events 确认 2 次 FailedScheduling，均为 "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"。集群其余 59 个 Pod 均正常运行，排除其他故障。此问题属于测试场景构造的调度约束不匹配，非资源不足、节点异常或 PVC 问题。
   confidence=98%
   causal_chain={"root_cause": "Pod rc-pending-nodeselector 的 nodeSelector 指定了不存在的标签 aiops.e2e/nonexistent-node-label=true，集群 3 个节点均不包含此标签。", "propagation": "Pod spec 中设置 nodeSelector → kube-scheduler 尝试将 Pod 绑定到匹配节点 → 遍历 3 个节点均不匹配 → 调度器报告 FailedScheduling → Pod 停留在 Pending 状态", "direct_cause": "调度器无法找到任何满足 nodeSelector 约束的节点（0/3 nodes available）", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续 Pending，Events 显示 FailedScheduling，IP 和 NODE 均为 none"}
   rca_analysis={"phenomenon": "集群 aiops-e2e 命名空间中 Pod rc-pending-nodeselector 处于 Pending 状态，调度失败，已持续约 10 分钟。", "evidence_inventory": [{"id": "e1", "source": "kubectl_get_yaml", "content": "Pod rc-pending-nodeselector 的 nodeSelector 设置为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_nodes_labels", "content": "集群 3 个节点（master、node1、node2）均不包含 aiops.e2e/nonexistent-node-label 标签", "reliability": "高"}, {"id": "e4", "source": "kubectl_events", "content": "2 次 FailedScheduling 事件：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "集群 65 个 Pod 中仅此 1 个异常 Pending Pod，其余 59 个 Running", "reliability": "高"}, {"id": "layer_2", "source": "kubectl_get_by_name", "content": "Pod rc-pending-nodeselector 状态 Pending，IP/NODE 均为 none", "reliability": "高"}, {"id": "layer_3", "source": "kubectl_describe", "content": "FailedScheduling: 3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}", "interpretation": "Pod 要求调度到包含 aiops.e2e/nonexistent-node-label=true 标签的节点上，这是一个不存在的标签键值对。"}, {"evidence_id": "e2", "raw_data": "master: {beta.kubernetes.io/arch, beta.kubernetes.io/os, kubernetes.io/hostname, ...} node1: {...} node2: {...} 均无 aiops.e2e/nonexistent-node-label", "interpretation": "集群全部 3 个节点的标签列表中均不包含 aiops.e2e/nonexistent-node-label 标签，没有任何节点满足 Pod 的调度约束。"}, {"evidence_id": "e4", "raw_data": "10m Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.", "interpretation": "调度器明确报告所有 3 个节点均因 nodeSelector/affinity 不匹配而被排除，且抢占也无帮助。"}, {"evidence_id": "layer_1", "raw_data": "status_counts={'Running': 59, 'Pending': 1}, abnormal=1", "interpretation": "集群整体健康，仅此一个 Pod 异常，排除大规模集群故障。"}, {"evidence_id": "layer_3", "raw_data": "node: <none>, Warning FailedScheduling x2", "interpretation": "Pod 未被分配到任何节点，调度器已重试但持续失败。"}], "causal_chain": {"root_cause": "Pod rc-pending-nodeselector 的 nodeSelector 指定了不存在的标签 aiops.e2e/nonexistent-node-label=true，集群 3 个节点均不包含此标签。", "propagation": "Pod spec 中设置 nodeSelector → kube-scheduler 尝试将 Pod 绑定到匹配节点 → 遍历 3 个节点均不匹配 → 调度器报告 FailedScheduling → Pod 停留在 Pending 状态", "direct_cause": "调度器无法找到任何满足 nodeSelector 约束的节点（0/3 nodes available）", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续 Pending，Events 显示 FailedScheduling，IP 和 NODE 均为 none"}, "root_cause": "Pod aiops-e2e/rc-pending-nodeselector 因 nodeSelector 约束无法调度：其配置要求调度到带有 aiops.e2e/nonexistent-node-label=true 标签的节点，但集群 3 个节点（master、node1、node2）均不包含此标签。kubectl_events 确认 2 次 FailedScheduling，均为 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"。集群其余 59 个 Pod 均正常运行，排除其他故障。此问题属于测试场景构造的调度约束不匹配，非资源不足、节点异常或 PVC 问题。", "root_cause_summary": "Pod aiops-e2e/rc-pending-nodeselector 因 nodeSelector 约束无法调度：其配置要求调度到带有 aiops.e2e/nonexistent-node-label=true 标签的节点，但集群 3 个节点（master、node1、node2）均不包含此标签。kubectl_events 确认 2 次 FailedScheduling，均为 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"。集群其余 59 个 Pod 均正常运行，排除其他故障。此问题属于测试场景构造的调度约束不匹配，非资源不足、节点异常或 PVC 问题。", "confidence": 0.98, "confidence_reason": "三条关键证据（Pod YAML 明确 nodeSelector 值、Node 标签列表确认该标签不存在、Events 明确报告 FailedScheduling 原因为节点不匹配）互相印证，因果链完整直接，无矛盾信号。0.98 置信度。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "资源不足（CPU/内存不足）", "probability": "low", "reason": "Events 中未出现 Insufficient cpu/memory 提示，且集群其他 59 个 Pod 均正常运行"}, {"cause": "节点异常（NotReady/Unschedulable）", "probability": "low", "reason": "3 个节点均正常，Events 明确指向 nodeSelector 不匹配而非节点状态异常"}, {"cause": "PVC 未绑定或卷依赖未满足", "probability": "low", "reason": "Pod 仅挂载默认 kube-api-access 卷，无 PVC 依赖，Events 也未提及卷问题"}], "limitations": "当前分析仅覆盖 1 个异常组（g1），集群中无其他异常 Pod。所有证据均来自上游已验证的工具数据，未发现证据缺失或冲突。", "llm_raw_analysis": "L1 层根因分析完成。证据清点：共 6 条证据（e1 Pod YAML、e2 Node 标签、e4 Events、layer_1~3 上游验证）。逐条分析确认 Pod nodeSelector 指定了集群中不存在的标签（aiops.e2e/nonexistent-node-label=true），3 个节点均不含此标签。Events 明确报告 FailedScheduling。因果链清晰：nodeSelector 约束 → 无匹配节点 → 调度失败 → Pending。已排除资源不足、节点异常、PVC 依赖等候选场景。置信度 0.98。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod aiops-e2e/rc-pending-nodeselector 因 nodeSelector 约束无法调度：其配置要求调度到带有 aiops.e2e/nonexistent-node-label=true 标签的节点，但集群 3 个节点（master、node1、node2）均不包含此标...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod rc-pending-nodeselector 的 nodeSelector 指定了不存在的标签 aiops.e2e/nonexistent-node-label=true，集群 3 个节点均不包含此标签。
     传导机制: Pod spec 中设置 nodeSelector → kube-scheduler 尝试将 Pod 绑定到匹配节点 → 遍历 3 个节点均不匹配 → 调度器报告 FailedScheduling → Pod 停留在 Pending 状态
     最终表现: Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续 Pending，Events 显示 FailedScheduling，IP 和 NODE 均为 none


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (22.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5392 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 22.2s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将根据您提供的分析结果，生成一份详尽、完整的诊断报告。

---

## 📊 诊断概览

首先，直接回答您的问题：**您的集群目前整体运行状况良好，但存在一个明确的、可解释的异常问题。**

| 项目 | 内容 |
|------|------|
| **集群整体状态** | 65 个 Pod 中，59 个正常运行（Running），1 个异常（Pending）。**集群资源充足，节点均正常**。 |
| **Pod异常状态** | Pending (PendingUnschedulable) |
| **兼容归因层** | L1 - Scheduling |
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
| **异常 Pod** | `rc-pending-nodeselector` (位于 `aiops-e2e` 命名空间) |
| **Pod 状态** | `Pending` |
| **Pod 标签** | `app=rc-pending-nodeselector, rootcause-e2e=true` |
| **受影响节点** | 无（Pod 未调度到任何节点） |

---

## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | **Pod YAML 配置** | `kubectl_get_yaml` | `nodeSelector: aiops.e2e/nonexistent-node-label: "true"` | Pod 明确要求调度到带有标签 `aiops.e2e/nonexistent-node-label=true` 的节点。 |
| 2 | **集群节点标签** | `run_bash_command` | 节点 `master`, `node1`, `node2` 的标签均**不包含** `aiops.e2e/nonexistent-node-label`。 | 集群中**没有任何节点**满足 Pod 的 `nodeSelector` 约束。 |
| 3 | **Pod 调度事件** | `kubectl_events` | `Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | kube-scheduler 确认无法在任何节点上调度此 Pod，进一步验证了节点标签不匹配。 |
| 4 | **集群 Pod 状态总览** | `kubectl_get_by_kind_in_cluster` | `rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}` | 集群中其他 59 个 Pod 均正常运行，排除大规模故障。 |
| 5 | **特定 Pod 状态** | `kubectl_get_by_name` | `STATUS: Pending`, `NODE: <none>` | Pod 确实处于未调度状态。 |
| 6 | **详细 Pod 信息** | `kubectl_describe` | `node: <none>`, 集成诊断事件信息。 | 确认 Pod 无调度目标节点。 |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 的 `nodeSelector` 要求一个不存在的标签 (`aiops.e2e/nonexistent-node-label=true`)，而所有 3 个节点的标签都不包含此键值对，直接导致调度失败。
- **证据 #1 + #2 + #3 形成闭环**：Pod 配置 -> 节点无匹配标签 -> 调度器报告 `FailedScheduling`。因果链清晰。
- **证据 #4 排除全局故障**：集群中 59 个 Pod 运行正常，证明问题**仅与特定 Pod 的调度配置有关**。

### 缺失证据（如有）
无。所有关键证据均已成功采集，证据链完整。

---

## 🎯 根因分析

### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                            │
│ Pod `rc-pending-nodeselector` 的 `nodeSelector` 配置了集群中不存在的标签               │
│ (`aiops.e2e/nonexistent-node-label=true`)。                                          │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                            │
│ kube-scheduler 读取 Pod spec -> 发现 `nodeSelector` 约束 -> 遍历所有 3 个节点，       │
│ 未找到匹配标签 -> 无法执行绑定操作。                                                  │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                            │
│ kube-scheduler 无法找到满足 `nodeSelector` 约束的可用节点，触发 `FailedScheduling` 事件。 │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                        │
│ Pod `rc-pending-nodeselector` 状态持续为 `Pending`，`NODE` 和 `IP` 均为 `<none>`。    │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (Pod YAML 中的 `nodeSelector`)、证据 #2 (节点标签列表) 和证据 #3 (`FailedScheduling` 事件)，问题的根本原因是 **Pod `rc-pending-nodeselector` 的调度配置错误**。它要求的节点标签 `aiops.e2e/nonexistent-node-label=true` 在集群的三个节点中均不存在，导致所有节点被排除，无法调度。

**置信度**：高 (98%)
- ✅ 证据 #1 和 #2 直接锁定不匹配的配置和事实。
- ✅ 事件 #3 明确报告 `3 node(s) didn't match Pod's node affinity/selector`。
- ✅ 证据 #4 排除了资源不足或其他集群级问题。

---

## 🛠️ 修复建议

此问题是由测试场景构造引起的，修复取决于用户意图。

### 方案一：移除 `nodeSelector`（如果 Pod 不需要特定节点）
此操作会立即让 Pod 调度到集群中任一可用节点。
```bash
kubectl patch pod rc-pending-nodeselector -n aiops-e2e -p '{"spec":{"nodeSelector": null}}' --type=merge
```

### 方案二：更正 `nodeSelector` 标签（如果 Pod 应调度到特定节点）
假设您希望 Pod 调度到名为 `master` 的节点上，可以修改 `nodeSelector` 为该节点的实际标签。
```bash
# 1. 查看 master 节点标签
kubectl get node master --show-labels

# 2. 创建一个指向 master 节点的 nodeSelector (以 kubernetes.io/hostname=master 为例)
kubectl patch pod rc-pending-nodeselector -n aiops-e2e -p '{"spec":{"nodeSelector":{"kubernetes.io/hostname":"master"}}}' --type=merge
```

### 方案三：添加节点标签（如果标签名是正确的，只是忘记打标签）
如果 `aiops.e2e/nonexistent-node-label` 这个标签是正确的，但节点上尚未添加，可以执行：
```bash
# 假设你想让 Pod 调度到 node1
kubectl label node node1 aiops.e2e/nonexistent-node-label=true
```

### 后续优化
- **审核 Pod 的调度配置**：在部署新工作负载时，确保 `nodeSelector`、`affinity` 等调度约束与集群中实际存在的节点标签一致。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o wide` | STATUS: `Running`，NODE 列显示有值 |
| 2. 确认 Pod 无异常事件 | `kubectl get events --namespace aiops-e2e --field-selector involvedObject.name=rc-pending-nodeselector` | 无 `FailedScheduling` 警告 |

---

## ⚠️ 注意事项
- 此问题**不影响其他 59 个正常工作负载**，集群核心功能正常。
- 根据您选择的修复方案，可能需要调整 `<node-name>`。
- 该 Pod 仅为测试用例 `rootcause-e2e=true`，其目的可能就是人为制造一个故障。请根据需要决定是否修复。

---

## 📊 性能统计

├─ 总耗时: 1.4m
├─ 问题定位: 21.8s (27%) ✅
├─ 证据链采集: 18.6s (23%) ✅
├─ 根因分析: 19.4s (24%) ✅
├─ 汇总总结: 22.3s (27%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 7 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 7 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
