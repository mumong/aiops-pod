======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: e6d7c9c302f5469b]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先对整个集群的 Pod 状态做一次全局扫描，看看有哪些异常情况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 好的，我看到了集群中有一个异常 Pod。让我进一步确认它的详细信息。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  29m                default-scheduler  0/3 nodes are available: 
   💭 [问题定位] 现在情况已经很清楚了。让我也看一下这个 Pod 的标签来确认它携带的异常类型标记。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          29m   <none>   <none>   
   💭 [问题定位] 好的，分析完毕。以下是定位结果：

---

## 🔍 集群异常诊断

### 全局 Pod 概览
| 状态 | 数量 |
|------|------|
| Running | 59 |
| **Pending** | **1** |
| 总计 | 65 |

### 异常 Pod 详情

| Pod | 命名空间 | 状态 | 已持续 |
|-----|---------|------|-------|
| **rc-pending-nodeselector** | aiops-e2e | **Pending** | 29m |

### 异常分析

**Pod 名称：** `rc-pending-nodeselector`
**状态关键字：** `Pending`
**异常类型：** `PendingUnschedulable`（调度失败）
**兼容层级：** L1

**根因定位：**
该 Pod 设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，这个标签在集群中**不存在于任何节点上**，导致调度器无法找到匹配的节点。

调度器事件明确报错：
> `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`

集群中有 3 个节点，全部因为 nodeSelector 不匹配而无法调度该 Pod。

**关键发现：**
- `Node-Selectors: aiops.e2e/nonexistent-node-label=true` — 节点标签不存在
- `QoS Class: BestEffort` — 没有资源限制要求
- 这不是资源不足问题，而是纯粹的选择器/亲和性配置问题

### 输出结构化结果

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **layer_name** | PendingUnschedulable |
| **status_category** | 调度阻塞 |
| **pod_abnormal_type** | PendingUnschedulable |
| **pod_status_keyword** | Pending |
| **affected_pods** | 1 |
| **affected_namespaces** | aiops-e2e |

**后续审查方向：**
1. 确认 Pod 的 `nodeSelector` / `affinity` 配置是否故意设置
2. 检查是否需要给节点打上对应标签 `aiops.e2e/nonexistent-node-label=true`
3. 或者修改 Pod 的调度约束以匹配已有节点标签
   ✅ [问题定位] 完成 (21.6s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector 标签不存在于任何节点上', 'probability': '高', 'reason': 'Pod 配置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，集群中 3 个节点均不匹配，调度事件明确报告 node affinity/selector 不匹配'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Namespace", "name": "aiops-e2e", "namespace": ""}]
   reasoning=当前环境中存在一个活跃的异常 Pod 'rc-pending-nodeselector'（命名空间 aiops-e2e），状态为 Pending，持续 29 分钟。根因是 Pod 设置了不存在的 nodeSelector 标签 'aiops.e2e/nonexistent-node-label=true'，导致调度器无法匹配任何节点（事件显示 0/3 nodes available）。pod_status_keyword 为 Pending，pod_abnormal_type 归一化为 PendingUnschedulable（调度失败），属于 L1 层级（调度阻塞/scheduling）。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "当前环境中存在一个活跃的异常 Pod 'rc-pending-nodeselector'（命名空间 aiops-e2e），状态为 Pending，持续 29 分钟。根因是 Pod 设置了不存在的 nodeSelector 标签 'aiops.e2e/nonexistent-node-label=true'，导致调度器无法匹配任何节点（事件显示 0/3 nodes available）。pod_status_keyword 为 Pending，pod_abnormal_type 归一化为 PendingUnschedulable（调度失败），属于 L1 层级（调度阻塞/scheduling）。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Namespace", "name": "aiops-e2e", "namespace": ""}], "possible_scenarios": [{"scenario": "nodeSelector 标签不存在于任何节点上", "probability": "高", "reason": "Pod 配置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，集群中 3 个节点均不匹配，调度事件明确报告 node affinity/selector 不匹配"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              29m     <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/e6d7c9c302f5469b/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/e6d7c9c302f5469b/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/e6d7c9c302f5469b/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我将直接按既有 evidence_plan 执行关键工具调用，验证 Pod PendingUnschedulable 的根因。

首先，并行执行三个核心证据工具：
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAME     STATUS   ROLES           AGE    VERSION   LABELS\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpg
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  29m                default-scheduler  0/3 nodes are available: 
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:18:44Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [证据链采集] 让我再获取节点标签的精确匹配证据，确认 `aiops.e2e/nonexistent-node-label` 标签确实不存在于任何节点：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "=== 确认结果: 没有任何节点包含 'aiops.e2e/nonexistent-node-label' 标签 ===\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] 所有证据已采集完毕。以下是证据结论：

---

## 📋 证据采集结论

### ✅ 已采集证据（全部 critical 级）

| 证据项 | 结果 |
|--------|------|
| **ev1 - Pod YAML（nodeSelector）** | Pod `rc-pending-nodeselector` 明确配置了 `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}`，且 `nodeName: None`，`phase: Pending`，`PodScheduled=False`，`reason=Unschedulable` |
| **ev2 - 节点标签检查** | 集群共 **3 个节点**（master/node1/node2），**没有任何节点**包含 `aiops.e2e/nonexistent-node-label` 标签 |
| **ev3 - Pod Describe（FailedScheduling 事件）** | 调度器事件明确报告：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`，且 preemption 不可用 |

### 🔍 根因判定
Pod `rc-pending-nodeselector` 卡在 **Pending** 状态的唯一原因是 **nodeSelector 标签 `aiops.e2e/nonexistent-node-label=true` 在集群 3 个节点上均不存在**，导致调度器完全无法放置该 Pod。

### ⚠️ 冲突/负向证据
无冲突证据。所有工具返回结果与 `primary_problem` 完全一致，Pod 仍存在且异常状态持续约 29 分钟。
   ✅ [证据链采集] 完成 (20.3s)
   📤 → 下游数据: evidence_items=5/6
   evidence_analysis={"evidence_plan":[{"id":"ev1-node-selector","description":"检查 Pod 'rc-pending-nodeselector' 的完整 YAML/spec，确认 nodeSelector 配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"验证 Pod 的 nodeSelector/affinity 配置，确认调度失败根因","evidence_type":"","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"ev2-nodes-check","description":"检查集群所有节点的 labels，确认是否存在 nodeSelector 匹配的标签","level":"critical","tool":"run_bash_command","command":"kubectl get nodes --show-labels","tool_args":{"command":"kubectl get nodes --show-labels"},"purpose":"验证集群节点是否存在 'aiops.e2e/nonexistent-node-label' 标签","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev3-pod-describe","description":"kubectl describe pod 查看当前调度事件详情","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"验证 FailedScheduling 事件原文","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAME     STATUS   ROLES           AGE    VERSION   LABELS\\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\\nnode1    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\nnode2    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e6d7c9c302f5469b/tools/001-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e6d7c9c302f5469b/tools/001-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e6d7c9c302f5469b/tools/001-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  29m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  19m (x2 over 24m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  29m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  19m (x2 over 24m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e6d7c9c302f5469b/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e6d7c9c302f5469b/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e6d7c9c302f5469b/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e6d7c9c302f5469b/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e6d7c9c302f5469b/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e6d7c9c302f5469b/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"=== 确认结果: 没有任何节点包含 'aiops.e2e/nonexistent-node-label' 标签 ===\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e6d7c9c302f5469b/tools/004-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e6d7c9c302f5469b/tools/004-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e6d7c9c302f5469b/tools/004-evidence-run_bash_command.summary.txt"}],"llm_analysis":"所有证据已采集完毕。以下是证据结论：\n\n---\n\n## 📋 证据采集结论\n\n### ✅ 已采集证据（全部 critical 级）\n\n| 证据项 | 结果 |\n|--------|------|\n| **ev1 - Pod YAML（nodeSelector）** | Pod `rc-pending-nodeselector` 明确配置了 `nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}`，且 `nodeName: None`，`phase: Pending`，`PodScheduled=False`，`reason=Unschedulable` |\n| **ev2 - 节点标签检查** | 集群共 **3 个节点**（master/node1/node2），**没有任何节点**包含 `aiops.e2e/nonexistent-node-label` 标签 |\n| **ev3 - Pod Describe（FailedScheduling 事件）** | 调度器事件明确报告：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`，且 preemption 不可用 |\n\n### 🔍 根因判定\nPod `rc-pending-nodeselector` 卡在 **Pending** 状态的唯一原因是 **nodeSelector 标签 `aiops.e2e/nonexistent-node-label=true` 在集群 3 个节点上均不存在**，导致调度器完全无法放置该 Pod。\n\n### ⚠️ 冲突/负向证据\n无冲突证据。所有工具返回结果与 `primary_problem` 完全一致，Pod 仍存在且异常状态持续约 29 分钟。","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 5/6 项，完整度 83%；实际执行工具 7 个，匹配计划 2 个，未规划证据 5 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":6,"environment_evidence_collected":5,"environment_evidence_completeness":0.8333333333333334,"executed_tool_count":7,"matched_tool_count":2,"unplanned_tool_count":5,"evidence_inventory":[{"id":"ev1-node-selector","description":"检查 Pod 'rc-pending-nodeselector' 的完整 YAML/spec，确认 nodeSelector 配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"验证 Pod 的 nodeSelector/affinity 配置，确认调度失败根因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev2-nodes-check","description":"检查集群所有节点的 labels，确认是否存在 nodeSelector 匹配的标签","level":"critical","tool":"run_bash_command","command":"kubectl get nodes --show-labels","purpose":"验证集群节点是否存在 'aiops.e2e/nonexistent-node-label' 标签","collected":false,"source":"planned","outcome":"unknown"},{"id":"ev3-pod-describe","description":"kubectl describe pod 查看当前调度事件详情","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"验证 FailedScheduling 事件原文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["ev2-nodes-check(检查集群所有节点的 labels，确认是否存在 nodeSelector 匹配的标签): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 83%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | ev1-node-sele... | critical | ✅ | kubectl_get_yaml | 检查 Pod 'rc-pending-nodeselector' 的完整 YAML/spe... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | ev2-nodes-check | critical | ❌ | run_bash_command | 检查集群所有节点的 labels，确认是否存在 nodeSelector 匹配的标签 | `kubectl get nodes --show-labels` |
   | ev3-pod-describe | critical | ✅ | kubectl_describe | kubectl describe pod 查看当前调度事件详情 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |

   ⚠️ 未采集原因:
   - ev2-nodes-check(检查集群所有节点的 labels，确认是否存在 nodeSelector 匹配的标签): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (22.3s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector（命名空间 aiops-e2e）处于 Pending 状态已持续 29 分钟，根因为 Pod spec 中配置了 nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}（证据 ev1-yaml），而集群 3 个节点（master/node1/node2）均不包含该标签（证据 ev2-nodes）。调度器事件明确报告 0/3 nodes available: 3 node(s) didn't match Pod's node affinity/selector（证据 ev3-events）。集群其他 59 个 Pod 运行正常，仅此 1 个异常（证据 ev4-cluster-overview），无其他并发异常。
   confidence=98%
   causal_chain={"root_cause": "Pod 'rc-pending-nodeselector' 的 spec 中配置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，而集群中 3 个节点均不包含该标签，导致调度器无法匹配任何节点", "propagation": "Pod 创建后，调度器尝试将所有 3 个节点与 nodeSelector 条件匹配 → 3 个节点均不满足条件 → 调度器将 Pod 标记为 Unschedulable → Pod 持续停留在 Pending 状态 → 事件中记录 FailedScheduling", "direct_cause": "nodeSelector 标签 'aiops.e2e/nonexistent-node-label=true' 在集群所有节点上均不存在", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续 Pending 29 分钟，Node 和 IP 均为空，调度事件反复报告 0/3 nodes available"}
   rca_analysis={"phenomenon": "命名空间 aiops-e2e 中的 Pod 'rc-pending-nodeselector' 状态为 Pending，持续约 29 分钟。Pod 未调度到任何节点（nodeName=None），IP 和 Node 均为空，调度器报告 FailedScheduling 事件，pod_abnormal_type 归一化为 PendingUnschedulable。", "evidence_inventory": [{"id": "ev1-yaml", "source": "kubectl_get_yaml", "content": "Pod rc-pending-nodeselector 的 nodeSelector 明确配置为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}，phase=Pending，PodScheduled=False，reason=Unschedulable", "reliability": "高"}, {"id": "ev2-nodes", "source": "run_bash_command（节点标签扫描）", "content": "集群 3 个节点（master/node1/node2）均不包含 'aiops.e2e/nonexistent-node-label' 标签", "reliability": "高"}, {"id": "ev3-events", "source": "kubectl_describe", "content": "FailedScheduling 事件: 0/3 nodes available - 3 node(s) didn't match Pod's node affinity/selector，preemption 不可用", "reliability": "高"}, {"id": "ev4-cluster-overview", "source": "kubectl_get_by_kind_in_cluster", "content": "集群共 65 个 Pod，59 个 Running，仅此 1 个 Pending，无其他异常", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "ev1-yaml", "raw_data": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}, phase: Pending, PodScheduled=False, reason=Unschedulable", "interpretation": "Pod spec 明确设置了 nodeSelector 条件，要求节点包含 aiops.e2e/nonexistent-node-label=true 标签；Pod 处于 Pending 状态，调度条件未满足。"}, {"evidence_id": "ev2-nodes", "raw_data": "master/node1/node2 节点标签列表均不包含 aiops.e2e/nonexistent-node-label", "interpretation": "集群所有 3 个节点均没有 Pod 所需的 nodeSelector 标签，Pod 无法被调度到任何节点上。"}, {"evidence_id": "ev3-events", "raw_data": "Warning FailedScheduling: 0/3 nodes available - 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes Preemption is not helpful for scheduling.", "interpretation": "调度器确认所有 3 个节点因 node affinity/selector 不匹配而不可调度，且抢占策略也无法解决此问题。"}, {"evidence_id": "ev4-cluster-overview", "raw_data": "rows=65 abnormal=1 status_counts={'Running':59, 'Pending':1}", "interpretation": "集群整体健康，59 个 Pod 正常运行，仅此 1 个异常 Pod，确认问题范围局限于此 Pod，非集群级别故障。"}], "causal_chain": {"root_cause": "Pod 'rc-pending-nodeselector' 的 spec 中配置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，而集群中 3 个节点均不包含该标签，导致调度器无法匹配任何节点", "propagation": "Pod 创建后，调度器尝试将所有 3 个节点与 nodeSelector 条件匹配 → 3 个节点均不满足条件 → 调度器将 Pod 标记为 Unschedulable → Pod 持续停留在 Pending 状态 → 事件中记录 FailedScheduling", "direct_cause": "nodeSelector 标签 'aiops.e2e/nonexistent-node-label=true' 在集群所有节点上均不存在", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续 Pending 29 分钟，Node 和 IP 均为空，调度事件反复报告 0/3 nodes available"}, "root_cause": "Pod rc-pending-nodeselector（命名空间 aiops-e2e）处于 Pending 状态已持续 29 分钟，根因为 Pod spec 中配置了 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}（证据 ev1-yaml），而集群 3 个节点（master/node1/node2）均不包含该标签（证据 ev2-nodes）。调度器事件明确报告 0/3 nodes available: 3 node(s) didn't match Pod's node affinity/selector（证据 ev3-events）。集群其他 59 个 Pod 运行正常，仅此 1 个异常（证据 ev4-cluster-overview），无其他并发异常。", "root_cause_summary": "Pod rc-pending-nodeselector（命名空间 aiops-e2e）处于 Pending 状态已持续 29 分钟，根因为 Pod spec 中配置了 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}（证据 ev1-yaml），而集群 3 个节点（master/node1/node2）均不包含该标签（证据 ev2-nodes）。调度器事件明确报告 0/3 nodes available: 3 node(s) didn't match Pod's node affinity/selector（证据 ev3-events）。集群其他 59 个 Pod 运行正常，仅此 1 个异常（证据 ev4-cluster-overview），无其他并发异常。", "confidence": 0.98, "confidence_reason": "三条关键证据（Pod YAML 直接显示 nodeSelector、节点标签扫描确认标签不存在、FailedScheduling 事件明确报告 3/3 节点不匹配）完全一致，因果链完整闭合，无矛盾证据。置信度 0.98。", "primary_runbooks": [], "alternative_causes": [{"cause": "集群资源不足（CPU/内存不足）", "probability": "low", "reason": "事件明确报告的是 'node affinity/selector' 不匹配而非资源不足，且集群 59 个 Pod 正常运行证明资源充足"}, {"cause": "节点污点（taint）不匹配", "probability": "low", "reason": "事件未提及 taint 相关错误，Pod 有 2 个 toleration（not-ready:NoExecute），非 taint 问题"}, {"cause": "PVC/PV 未绑定", "probability": "low", "reason": "Pod 仅有 kube-api-access 投影卷，无 PVC 依赖；事件也未报 volume 相关错误"}], "limitations": "节点标签检查是通过 run_bash_command 扫描节点标签完成的，确认 3 个节点均无匹配标签。如果集群中新增了节点或现有节点被重新打标签，此问题可自动解决。未采集节点数量变化或动态拓扑信息，但当前证据已足够完整确定根因。", "llm_raw_analysis": "## 证据清点\n共 4 条已采集证据：\n1. ev1-yaml: Pod YAML 显示 nodeSelector 配置\n2. ev2-nodes: 节点标签扫描结果\n3. ev3-events: kubectl describe 的 FailedScheduling 事件\n4. ev4-cluster-overview: 集群 Pod 全局状态\n\n## 逐条分析\n- ev1-yaml: Pod spec 中 nodeSelector 为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}，这是调度约束条件\n- ev2-nodes: 3 个节点均无此标签，无节点满足条件\n- ev3-events: 调度器确认 0/3 节点可用，原因明确为 node affinity/selector 不匹配\n- ev4-cluster-overview: 集群整体健康，仅此 Pod 异常，范围明确\n\n## 关联分析\nev1 定义了条件（需要标签），ev2 证明了条件不满足（无节点有此标签），ev3 验证了结果（调度失败事件），ev4 排除了其他并发问题。四者形成了\n... 截断，原始 641 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector（命名空间 aiops-e2e）处于 Pending 状态已持续 29 分钟，根因为 Pod spec 中配置了 nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}（证据 ev1-...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod 'rc-pending-nodeselector' 的 spec 中配置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，而集群中 3 个节点均不包含该标签，导致调度器无法匹配任何节点
     传导机制: Pod 创建后，调度器尝试将所有 3 个节点与 nodeSelector 条件匹配 → 3 个节点均不满足条件 → 调度器将 Pod 标记为 Unschedulable → Pod 持续停留在 Pending 状态 → 事件中记录 FailedScheduling
     最终表现: Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续 Pending 29 分钟，Node 和 IP 均为空，调度事件反复报告 0/3 nodes available


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (26.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5949 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 31.0s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将严格遵循您的指示，为您生成一份详尽完整的诊断报告。

---
## 📊 诊断概览

根据对您集群的全面扫描，当前集群中 **存在 1 个异常 Pod**，其余 59 个运行中的 Pod 均正常。具体问题总结如下：

**核心问题发现：**
您的集群中，命名空间 `aiops-e2e` 下的 Pod `rc-pending-nodeselector` 处于 **Pending (待调度)** 状态，持续了 **29 分钟**。根本原因是该 Pod 配置了一个在集群中不存在的 `nodeSelector` 标签，导致调度器无法为其分配任何工作节点。

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending |
| **兼容归因层** | L1 - 调度阻塞 (Scheduling) |
| **问题分类** | PendingUnschedulable (调度失败) |
| **置信度** | 高 (98%) |
| **证据完整度** | 2/3 (67%) |

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-pending-nodeselector` |
| Namespace | `aiops-e2e` |
| Node | 无 (未分配) |
| 持续时间 | 29 分钟 |
| 错误信息 | `Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` |

---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod YAML 配置 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` | `Node-Selectors: aiops.e2e/nonexistent-node-label=true` | Pod 明确要求调度到包含 `aiops.e2e/nonexistent-node-label=true` 标签的节点。 |
| 2 | 调度事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | `Warning FailedScheduling 29m default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 调度器尝试了所有 3 个节点，全部因为不匹配 `nodeSelector` 而失败。 |
| 3 | 节点标签 | `run_bash_command` (节点标签扫描) | 节点 `master`, `node1`, `node2` 的标签列表中**均不包含** `aiops.e2e/nonexistent-node-label=true`。 | 集群无可用的节点来满足 Pod 的调度约束。 |
| 4 | 集群概览 | `kubectl get pod -A` | `rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}` | 集群中其他 Pod 均正常运行，此问题是**孤立事件**。 |
| 5 | Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | `NAME ... READY STATUS RESTARTS AGE ... rc-pending-nodeselector 0/1 Pending 0 29m` | Pod 没有处于 Running 状态，也没有被调度到任何 Node 上。 |

### 证据关联分析
- **证据 #1 + #2 + #3 形成闭环**：Pod YAML 配置了 `nodeSelector`（#1） → 调度器尝试在 3 个节点上寻找该标签失败（#2） → 扫描节点标签确认节点上确实没有这个标签（#3）。这形成了一个完整的因果链。
- **证据 #4 排除全局问题**：集群其他 Pod 正常运行，说明问题并非集群级资源或调度器故障，而是特定 Pod 的配置错误。

### 缺失证据（如有）
无。当前证据已足够支撑根因判断，因此不存在缺失的证据。

---
## 🎯 根因分析

### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                             │
│ Pod 'rc-pending-nodeselector' 的 spec 中配置了 nodeSelector:                          │
│   "aiops.e2e/nonexistent-node-label=true"                                            │
│ 该标签在集群任意节点上均不存在。                                                        │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制 (Propagation)                                                                │
│ 1. Pod 创建后，调度器尝试将 Pod 与集群中所有 3 个节点匹配 (master, node1, node2)。        │
│ 2. 由于所有节点都缺少 Pod 要求的标签 "aiops.e2e/nonexistent-node-label=true"，调度失败。 │
│ 3. 调度器将 Pod 标记为 Unschedulable，并反复重试调度直至超时。                             │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                             │
│ 调度器因找不到匹配的节点，报告 FailedScheduling 事件。                                  │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                         │
│ Pod 'rc-pending-nodeselector' 持续处于 Pending 状态，且无法被调度到任何节点上。          │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (YAML 配置)、#2 (调度事件) 和 #3 (节点标签)，问题的根本原因是：
**Pod `rc-pending-nodeselector` 的 YAML 配置中指定了一个在集群中所有节点上都不存在的 `nodeSelector` 标签 (`aiops.e2e/nonexistent-node-label=true`)，导致调度器无法为其找到合适的节点，从而使其持续处于 Pending 状态。**

**置信度**：高 (98%)
- ✅ 证据 #1 和 #3 直接证实了 `nodeSelector` 与节点标签的不匹配。
- ✅ 证据 #2 中的 `FailedScheduling` 事件直接印证了此问题。
- ✅ 证据 #4 排除了其他可能的集群级调度问题。

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 修改或移除 Pod 的 `nodeSelector` 配置** (推荐)

既然这是一个测试 Pod (`rc-pending-nodeselector`)，最简单的修复方式是移除错误的 `nodeSelector`，或将其改为一个在集群节点上真实存在的标签。
```bash
# 查看集群节点上存在的标签（例如：beta.kubernetes.io/arch=amd64 或 kubernetes.io/arch=amd64）
kubectl get nodes --show-labels

# 方法一：修改 Deployment（如果 Pod 是由 Deployment 管理的）
# 使用 "kubectl edit deployment" 修改 nodeSelector 字段
# kubectl edit deployment <deployment-name> -n aiops-e2e

# 方法二：如果 Pod 是独立创建的，直接删除重建（推荐用于此测试场景）
kubectl delete pod rc-pending-nodeselector -n aiops-e2e
```
*依据*：删除 Pod 后，如果它是通过 Deployment 等控制器创建的，控制器会创建一个不包含错误 `nodeSelector` 的新 Pod。

**2. [替代方案] 为某个节点添加 Pod 所需的标签**
如果业务需要 Pod 调度到特定标签的节点，可手动为节点打上标签。
```bash
# 为 node1 添加标签 aiops.e2e/nonexistent-node-label=true
kubectl label node node1 aiops.e2e/nonexistent-node-label=true
```
*效果*：打标后，调度器会自动将 `rc-pending-nodeselector` 调度到该节点。
*依据*：此操作直接满足了 Pod 的调度约束。

### 后续优化
1. **审查 Pod 配置**：在创建或更新 Pod/Deployment 时，确保 `nodeSelector`、`affinity` 等调度约束所引用的标签在集群中存在。
2. **配置 Preflight 检查**：可通过准入控制器 (Admission Controller) 或 CI/CD 流水线，在部署前先校验节点标签是否存在，避免此类配置错误进入生产环境。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态已更新 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | (若删除重建) STATUS 应为 Running； (若打标签) STATUS 应从 Pending 变为 Running。 |
| 2. 检查 Pod 被分配的 Node | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o wide` | NODE 列应显示具体节点名称，如 `node1`。 |
| 3. 确认不再有调度事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | Events 小节不应再有新的 `FailedScheduling` Warning 事件。 |

---
## ⚠️ 注意事项
- 此问题为一次性配置错误，修复后不会复发。
- 如果该 Pod 是某个 Deployment 或 StatefulSet 控制器的一部分，直接删除 Pod 即可自动恢复，无需修改控制器 YAML 文件（除非控制器的模板也包含了同样的 `nodeSelector`）。

---

## 📊 性能统计

├─ 总耗时: 1.5m
├─ 问题定位: 21.6s (24%) ✅
├─ 证据链采集: 20.3s (22%) ✅
├─ 根因分析: 22.3s (25%) ✅
├─ 汇总总结: 26.7s (29%) ✅
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
