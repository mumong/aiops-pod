======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 1a7a6351290f4a57]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先扫描全局 Pod 状态，看看集群中有哪些异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 发现了一个异常 Pod，让我进一步查看它的详细信息。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          23m   <none>   <none>   
   💭 [问题定位] 这个 Pod 还带有 `pod_abnormal_type=PendingUnschedulable` 标签，符合 Pending 不可调度的情况。让我获取匹配的 runbook 参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在让我 describe 这个 Pod 确认调度失败的具体原因。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  23m                default-scheduler  0/3 nodes are available: 
   💭 [问题定位] 现在我已经掌握了所有必要信息，可以做出完整的定位分析。以下是总结。

---

## 📋 集群异常定位分析

### 全局扫描结果
| 状态 | 数量 |
|------|------|
| ✅ Running | 59 |
| ⚠️ Pending | 1 |
| 总计 | 65 |

### 异常 Pod 识别

| Pod | 命名空间 | 状态 | 年龄 |
|-----|---------|------|------|
| `rc-pending-nodeselector` | `aiops-e2e` | **Pending** | 23m |

---

### 详细分析

**Pod:** `rc-pending-nodeselector`（aiops-e2e 命名空间）

**状态：** Pending，未绑定节点（`node: <none>`）

**调度失败事件：**
```
0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.
```

**根因：** Pod 设置了 nodeSelector：
```
Node-Selectors: aiops.e2e/nonexistent-node-label=true
```
集群中的 **3 个节点均没有** `aiops.e2e/nonexistent-node-label=true` 这个标签，导致调度器无法找到任何候选节点。

**其他特征：**
- QoS Class: BestEffort（无资源限制，不是资源不足问题）
- 镜像 `busybox:1.36` 正常
- 没有关联 PVC，不是卷挂载问题
- 不是 taint/toleration 问题

---

### 输出结构

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **layer_name** | PendingUnschedulable |
| **pod_status_keyword** | Pending |
| **pod_abnormal_type** | PendingUnschedulable |
| **status_category** | scheduling |
| **异常 Pod 数** | 1 |
| **异常组** | PendingUnschedulable × 1 |
| **核心实体** | `aiops-e2e/rc-pending-nodeselector` |
| **场景** | nodeSelector 不匹配导致调度失败 |

**建议方向：** 检查 Pod 的 `nodeSelector` 配置，为节点添加匹配的标签，或修改 Pod 的 nodeSelector/affinity。
   ✅ [问题定位] 完成 (22.7s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector/nodeAffinity不匹配导致调度失败', 'probability': '高', 'reason': "Event原文: 3 node(s) didn't match Pod's node affinity/selector. Pod配置Node-Selectors: aiops.e2e/nonexistent-node-label=true，集群3个节点均无此标签"}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}]
   reasoning=集群中存在1个仍处于Pending状态的Pod（rc-pending-nodeselector），调度事件明确提示0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector，根因为nodeSelector（aiops.e2e/nonexistent-node-label=true）不匹配任何节点标签。属于调度约束问题，归为L1层。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 1.0, "reasoning": "集群中存在1个仍处于Pending状态的Pod（rc-pending-nodeselector），调度事件明确提示0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector，根因为nodeSelector（aiops.e2e/nonexistent-node-label=true）不匹配任何节点标签。属于调度约束问题，归为L1层。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "nodeSelector/nodeAffinity不匹配导致调度失败", "probability": "高", "reason": "Event原文: 3 node(s) didn't match Pod's node affinity/selector. Pod配置Node-Selectors: aiops.e2e/nonexistent-node-label=true，集群3个节点均无此标签"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              23m     <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/1a7a6351290f4a57/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/1a7a6351290f4a57/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/1a7a6351290f4a57/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 100%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我已经收到了上游的 evidence_plan，现在开始按计划执行工具调用来采集证据。

首先，执行 ev-001（critical）：检查 Pod 的 FailedScheduling 事件和调度约束
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  24m                default-scheduler  0/3 nodes are available: 
   💭 [证据链采集] 很好！ev-001 已确认关键信息。接下来执行 ev-002（critical）：获取 Pod YAML 确认 nodeSelector 等调度约束详情。
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
   💭 [证据链采集] 证据已经非常清晰。现在执行 ev-003（important）：检查所有节点标签，确认所需标签是否存在于任何节点上。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAME     STATUS   ROLES           AGE    VERSION   LABELS\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpg
   💭 [证据链采集] 所有三个计划的工具都已执行完毕，现在进行证据总结。

---

## ✅ 证据采集结论

### 已采集证据（3/3 计划项全部完成）

**ev-001 ✅ kubectl describe pod**（critical）
- Pod `rc-pending-nodeselector` 状态 **Pending**，未绑定任何节点
- **FailedScheduling 事件**（共 3 次，最近 13m）原文：
  > `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`
- **Node-Selectors** 字段显示：`aiops.e2e/nonexistent-node-label=true`

**ev-002 ✅ kubectl get pod -o yaml**（critical）
- 确认 `nodeSelector` 字段：`{"aiops.e2e/nonexistent-node-label": "true"}`
- condition `PodScheduled=False`，reason=`Unschedulable`
- Pod 的 QoS Class: **BestEffort**，无资源请求限制，排除资源不足
- 无 PVC 卷依赖，排除存储前置条件问题

**ev-003 ✅ 节点标签检查**（important）
- 集群共 **3 个节点**（master, node1, node2），全部 Ready
- **没有任何节点**包含 `aiops.e2e/nonexistent-node-label` 标签
- 因此 3/3 节点均不匹配 Pod 的 nodeSelector，0 个可用节点

### 根因结论

> **Pod `rc-pending-nodeselector` 调度失败**的根本原因是：Pod 的 `nodeSelector` 要求节点具有标签 `aiops.e2e/nonexistent-node-label=true`，但集群中 3 个节点（master, node1, node2）均无此标签，导致调度器无法放置该 Pod。这属于**调度约束配置错误（L1层）**。

### 冲突/负向证据
无。所有工具均成功返回，结果完全对齐上游判断。

### 未采集证据
无。本轮计划已全部覆盖。
   ✅ [证据链采集] 完成 (21.6s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"ev-001","description":"验证 Pod rc-pending-nodeselector 的调度事件和完整配置（nodeSelector/affinity/volumes）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"检查 FailedScheduling 事件原文和 Pod spec 调度约束","evidence_type":"pod_event","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_describe","kubectl_get_yaml"],"counts_for_completeness":true},{"id":"ev-002","description":"获取 Pod YAML 以检查 nodeSelector/affinity/tolerations 完整配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"确认 nodeSelector 字段内容和其他调度约束","evidence_type":"pod_spec","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml","kubectl_describe","run_bash_command"],"counts_for_completeness":true},{"id":"ev-003","description":"列举集群可用节点及其标签，验证 nodeSelector 匹配情况","level":"important","tool":"run_bash_command","command":"kubectl get nodes --show-labels","tool_args":{},"purpose":"检查所有节点标签，确认 aiops.e2e/nonexistent-node-label=true 是否存在于任何节点","evidence_type":"node_label","target_scope":"Cluster/Nodes","acceptable_tools":["run_bash_command","kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  24m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  13m (x2 over 18m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  24m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  13m (x2 over 18m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1a7a6351290f4a57/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1a7a6351290f4a57/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1a7a6351290f4a57/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1a7a6351290f4a57/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1a7a6351290f4a57/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1a7a6351290f4a57/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAME     STATUS   ROLES           AGE    VERSION   LABELS\\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\\nnode1    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\nnode2    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/1a7a6351290f4a57/tools/003-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/1a7a6351290f4a57/tools/003-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/1a7a6351290f4a57/tools/003-evidence-run_bash_command.summary.txt"}],"llm_analysis":"所有三个计划的工具都已执行完毕，现在进行证据总结。\n\n---\n\n## ✅ 证据采集结论\n\n### 已采集证据（3/3 计划项全部完成）\n\n**ev-001 ✅ kubectl describe pod**（critical）\n- Pod `rc-pending-nodeselector` 状态 **Pending**，未绑定任何节点\n- **FailedScheduling 事件**（共 3 次，最近 13m）原文：\n  > `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`\n- **Node-Selectors** 字段显示：`aiops.e2e/nonexistent-node-label=true`\n\n**ev-002 ✅ kubectl get pod -o yaml**（critical）\n- 确认 `nodeSelector` 字段：`{\"aiops.e2e/nonexistent-node-label\": \"true\"}`\n- condition `PodScheduled=False`，reason=`Unschedulable`\n- Pod 的 QoS Class: **BestEffort**，无资源请求限制，排除资源不足\n- 无 PVC 卷依赖，排除存储前置条件问题\n\n**ev-003 ✅ 节点标签检查**（important）\n- 集群共 **3 个节点**（master, node1, node2），全部 Ready\n- **没有任何节点**包含 `aiops.e2e/nonexistent-node-label` 标签\n- 因此 3/3 节点均不匹配 Pod 的 nodeSelector，0 个可用节点\n\n### 根因结论\n\n> **Pod `rc-pending-nodeselector` 调度失败**的根本原因是：Pod 的 `nodeSelector` 要求节点具有标签 `aiops.e2e/nonexistent-node-label=true`，但集群中 3 个节点（master, node1, node2）均无此标签，导致调度器无法放置该 Pod。这属于**调度约束配置错误（L1层）**。\n\n### 冲突/负向证据\n无。所有工具均成功返回，结果完全对齐上游判断。\n\n### 未采集证据\n无。本轮计划已全部覆盖。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 6 个，匹配计划 3 个，未规划证据 3 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":3,"unplanned_tool_count":3,"evidence_inventory":[{"id":"ev-001","description":"验证 Pod rc-pending-nodeselector 的调度事件和完整配置（nodeSelector/affinity/volumes）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"检查 FailedScheduling 事件原文和 Pod spec 调度约束","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-002","description":"获取 Pod YAML 以检查 nodeSelector/affinity/tolerations 完整配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"确认 nodeSelector 字段内容和其他调度约束","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-003","description":"列举集群可用节点及其标签，验证 nodeSelector 匹配情况","level":"important","tool":"run_bash_command","command":"kubectl get nodes --show-labels","purpose":"检查所有节点标签，确认 aiops.e2e/nonexistent-node-label=true 是否存在于任何节点","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | ev-001 | critical | ✅ | kubectl_describe | 验证 Pod rc-pending-nodeselector 的调度事件和完整配置（nod... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | ev-002 | critical | ✅ | kubectl_get_yaml | 获取 Pod YAML 以检查 nodeSelector/affinity/tolerat... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | ev-003 | important | ✅ | run_bash_command | 列举集群可用节点及其标签，验证 nodeSelector 匹配情况 | `kubectl get nodes --show-labels` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (22.5s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector（aiops-e2e命名空间）已Pending持续23分钟，根本原因是Pod的nodeSelector指定了标签aiops.e2e/nonexistent-node-label=true，但集群3个节点（master、node1、node2）均不包含该标签。调度器事件明确报告"3 node(s) didn't match Pod's node affinity/selector"。Pod YAML确认nodeSelector字段为{"aiops.e2e/nonexistent-node-label":"true"}，且Pod无PVC依赖、无资源请求（QoS BestEffort），排除了资源不足和存储前置条件两个候选场景。集群中其他59个Pod均正常运行，说明集群整体调度能力正常，问题局限于该Pod的调度约束配置错误。
   confidence=98%
   causal_chain={"root_cause": "Pod rc-pending-nodeselector 的 nodeSelector 配置了不存在的标签 aiops.e2e/nonexistent-node-label=true，集群3个节点均无此标签", "propagation": "调度器评估所有3个节点(nodeSelector匹配检查) → 3/3节点均不匹配 → 调度失败 → Pod 保持在 Pending 状态 → 调度器每约5分钟重试一次，持续失败", "direct_cause": "Pod 的 nodeSelector 约束（aiops.e2e/nonexistent-node-label=true）无法被集群中任何节点满足", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续 Pending 23分钟，无 IP 分配，无节点绑定，Events 中反复出现 FailedScheduling 事件"}
   rca_analysis={"phenomenon": "集群中存在1个Pending状态的Pod（rc-pending-nodeselector，命名空间aiops-e2e），已Pending 23分钟，无法调度。59个Running Pod运行正常。", "evidence_inventory": [{"id": "ev-001", "source": "kubectl_describe", "content": "Pod rc-pending-nodeselector 状态 Pending，FailedScheduling 事件：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}, {"id": "ev-002", "source": "kubectl_get_yaml", "content": "Pod YAML 确认 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}，PodScheduled=False，reason=Unschedulable，无PVC依赖，无资源请求", "reliability": "高"}, {"id": "ev-003", "source": "kubectl_get_nodes（run_bash_command）", "content": "集群3节点(master/node1/node2)全部Ready，均无标签 aiops.e2e/nonexistent-node-label", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "集群65个Pod，仅此Pod异常(Pending)，其余59个Running", "reliability": "高"}, {"id": "layer_2", "source": "kubectl_get_by_name", "content": "确认Pod rc-pending-nodeselector 状态Pending，IP/Node均为none", "reliability": "高"}, {"id": "layer_3", "source": "kubectl_describe（上游）", "content": "确认FailedScheduling事件共3次，从23m到13m持续发生", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "ev-001", "raw_data": "Warning FailedScheduling 24m default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "interpretation": "调度器明确报告3个节点均不匹配Pod的节点亲和性/选择器约束，Pod无法被调度到任何节点"}, {"evidence_id": "ev-002", "raw_data": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}; PodScheduled=False reason=Unschedulable; 无PVC卷依赖; QoS BestEffort（无资源限制）", "interpretation": "Pod的nodeSelector要求节点包含aiops.e2e/nonexistent-node-label=true标签；排除资源不足和PVC未绑定这两个候选场景"}, {"evidence_id": "ev-003", "raw_data": "3节点标签列表：master(control-plane), node1, node2 - 均无 aiops.e2e/nonexistent-node-label 标签", "interpretation": "集群全部3个节点均不包含Pod所需的标签，与调度事件完全吻合，确认为nodeSelector不匹配问题"}, {"evidence_id": "layer_1", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}", "interpretation": "集群整体健康，仅此1个Pod异常，非大规模故障"}, {"evidence_id": "layer_2", "raw_data": "rc-pending-nodeselector 0/1 Pending 0 23m <none> <none>", "interpretation": "Pod未获得IP和节点分配，确认调度失败"}, {"evidence_id": "layer_3", "raw_data": "Warning FailedScheduling 23m... 13m (x2 over 18m)", "interpretation": "调度器持续重试但始终失败，问题持续存在"}], "causal_chain": {"root_cause": "Pod rc-pending-nodeselector 的 nodeSelector 配置了不存在的标签 aiops.e2e/nonexistent-node-label=true，集群3个节点均无此标签", "propagation": "调度器评估所有3个节点(nodeSelector匹配检查) → 3/3节点均不匹配 → 调度失败 → Pod 保持在 Pending 状态 → 调度器每约5分钟重试一次，持续失败", "direct_cause": "Pod 的 nodeSelector 约束（aiops.e2e/nonexistent-node-label=true）无法被集群中任何节点满足", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续 Pending 23分钟，无 IP 分配，无节点绑定，Events 中反复出现 FailedScheduling 事件"}, "root_cause": "Pod rc-pending-nodeselector（aiops-e2e命名空间）已Pending持续23分钟，根本原因是Pod的nodeSelector指定了标签aiops.e2e/nonexistent-node-label=true，但集群3个节点（master、node1、node2）均不包含该标签。调度器事件明确报告\"3 node(s) didn't match Pod's node affinity/selector\"。Pod YAML确认nodeSelector字段为{\"aiops.e2e/nonexistent-node-label\":\"true\"}，且Pod无PVC依赖、无资源请求（QoS BestEffort），排除了资源不足和存储前置条件两个候选场景。集群中其他59个Pod均正常运行，说明集群整体调度能力正常，问题局限于该Pod的调度约束配置错误。", "root_cause_summary": "Pod rc-pending-nodeselector（aiops-e2e命名空间）已Pending持续23分钟，根本原因是Pod的nodeSelector指定了标签aiops.e2e/nonexistent-node-label=true，但集群3个节点（master、node1、node2）均不包含该标签。调度器事件明确报告\"3 node(s) didn't match Pod's node affinity/selector\"。Pod YAML确认nodeSelector字段为{\"aiops.e2e/nonexistent-node-label\":\"true\"}，且Pod无PVC依赖、无资源请求（QoS BestEffort），排除了资源不足和存储前置条件两个候选场景。集群中其他59个Pod均正常运行，说明集群整体调度能力正常，问题局限于该Pod的调度约束配置错误。", "confidence": 0.98, "confidence_reason": "三个关键证据（kubectl_describe调度事件、kubectl_get_yaml确认nodeSelector、节点标签列表验证）完全对齐，因果链完整无断点。排除了资源不足和PVC依赖两个候选场景。证据覆盖了Pod配置、调度器行为和节点状态三个维度，交叉验证一致，置信度极高。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "资源不足（CPU/内存不足）", "probability": "low", "reason": "Pod QoS为BestEffort，无资源请求限制，调度事件未提及Insufficient资源，已排除"}, {"cause": "节点taint未容忍", "probability": "low", "reason": "调度事件提到的是'node affinity/selector'而非taint相关消息，且Pod有NoExecute toleration，已排除"}, {"cause": "PVC未绑定", "probability": "low", "reason": "Pod YAML显示无PVC卷，仅有kube-api-access投影卷，已排除"}, {"cause": "节点NotReady/SchedulingDisabled", "probability": "low", "reason": "3节点均为Ready状态，调度事件未提及节点不可用，已排除"}], "limitations": "未采集节点完整标签列表的原始JSON输出（仅从表格摘要提取），但表格已包含全部标签信息，不影响结论。未检查是否新节点可被添加来携带该标签（超出诊断范围）。", "llm_raw_analysis": "根因分析完成。Pod rc-pending-nodeselector 的 nodeSelector 标签在集群中不存在，导致Unschedulable。所有证据高度一致，无冲突或负向证据。异常组g1（PendingUnschedulable）仅含此1个Pod，已完整覆盖。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector（aiops-e2e命名空间）已Pending持续23分钟，根本原因是Pod的nodeSelector指定了标签aiops.e2e/nonexistent-node-label=true，但集群3个节点（master、node1、node2）均不...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod rc-pending-nodeselector 的 nodeSelector 配置了不存在的标签 aiops.e2e/nonexistent-node-label=true，集群3个节点均无此标签
     传导机制: 调度器评估所有3个节点(nodeSelector匹配检查) → 3/3节点均不匹配 → 调度失败 → Pod 保持在 Pending 状态 → 调度器每约5分钟重试一次，持续失败
     最终表现: Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续 Pending 23分钟，无 IP 分配，无节点绑定，Events 中反复出现 FailedScheduling 事件


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (26.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5202 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 33.0s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将为你分析集群的当前状态。

---

## 📊 集群状态概览

您的集群中 **存在 1 个异常 Pod**，其余 59 个 Pod 均正常运行，整体健康度较高，问题范围明确。

| 项目 | 内容 |
|------|------|
| **集群 Pod 总数** | 65 |
| **正常运行 Pod** | 59 (Running) |
| **异常 Pod 数** | **1 (Pending)** |
| **异常状态** | Pending (PendingUnschedulable) |
| **异常 Pod 名称** | `rc-pending-nodeselector` |
| **异常命名空间** | `aiops-e2e` |
| **诊断结论** | Pod 因 `nodeSelector` 配置了不存在的节点标签，导致无法被调度到任何节点。 |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-pending-nodeselector` |
| Namespace | `aiops-e2e` |
| 当前状态 | **Pending** (已持续 23 分钟) |
| 错误信息 | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` |

---

## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod` | `Status: Pending`<br>`Node: <none>`<br>`IP: <none>` | Pod 未被调度到任何节点，未获取网络资源。 |
| 2 | 调度事件 | `kubectl describe pod` | `Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 调度器明确报告：集群 **3 个节点全部不匹配** Pod 的亲和性/选择器约束。 |
| 3 | Pod 配置 | `kubectl get pod -o yaml` | `Node-Selectors: aiops.e2e/nonexistent-node-label=true` | Pod 明确指定了一个节点选择器标签 `aiops.e2e/nonexistent-node-label=true`。 |
| 4 | 节点标签 | `run_bash_command` | `master` 标签列表: `...`<br>`node1` 标签列表: `...`<br>`node2` 标签列表: `...` | 集群中 **所有 3 个节点（master, node1, node2）的标签列表均不包含** `aiops.e2e/nonexistent-node-label`。 |
| 5 | Pod 配置 | `kubectl get pod -o yaml` | `command: sh -c sleep 3600`<br>`terminationGracePeriodSeconds: 30` | Pod 本身是一个简单的睡眠任务，无 PVC、资源请求或复杂的生命周期配置，排除了存储和资源不足的场景。 |
| 6 | 集群状态 | `kubectl get all` | 集群中共 65 个 Pod，其中 59 个 **Running**，1 个 **Pending** | 集群调度能力正常，问题仅局限于该特定 Pod 的配置。 |

### 证据关联分析
- **证据 #1 + #2 + #3 + #4 印证**：
  1.  **配置冲突**：Pod 配置了 `nodeSelector: {aiops.e2e/nonexistent-node-label: true}` (证据 #3)，要求 Pod 必须调度到拥有该标签的节点上。
  2.  **匹配失败**：调度器遍历所有 3 个节点 (证据 #2)，但没有任何节点拥有该标签 (证据 #4)。
  3.  **结果**：Pod 被卡在 `Pending` 状态，无法被调度 (证据 #1)。
- **证据 #5 排除干扰项**：Pod 配置简单（一个 `sleep` 进程），排除了资源不足 (QoS BestEffort)、PVC 未绑定等其他常见的 `Pending` 原因。

### 缺失证据（无）
所有关键证据均已采集，完整度 100%，无需缺失证据。

---

## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod (rc-pending-nodeselector) 的 nodeSelector 配置了              │
│ 一个集群中不存在的标签: `aiops.e2e/nonexistent-node-label=true`   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 调度器尝试将 Pod 调度到任何节点 → 检查 nodeSelector 条件         │
│ → 3/3 节点均不满足 → 调度失败 → 进入重试循环                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 没有任何节点满足 Pod 的调度约束                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Pending，IP 为空，未绑定任何节点，持续 23 分钟        │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (FailedScheduling 事件报告所有节点不匹配)、证据 #3 (Pod 配置了 `nodeSelector`) 和证据 #4 (节点均无此标签)，
问题的根本原因是 **Pod `rc-pending-nodeselector` 的 `nodeSelector` 指定了一个集群中不存在的标签 `aiops.e2e/nonexistent-node-label=true`**，导致调度器无法找到任何可调度的节点。

**置信度**：**高 (98%)**
- ✅ 调度事件 (`FailedScheduling`) 直接指出了节点不匹配。
- ✅ Pod YAML (`nodeSelector`) 和节点标签 (`run_bash_command`) 的配置被完全验证。
- ✅ 排除了资源不足 (Pod 无资源请求) 和 PVC 未绑定 (Pod 无 PVC) 等其他可能性。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [推荐] 修正 Pod 的 nodeSelector**
最直接的修复是修改 Deployment / StatefulSet / Job 等上层控制器，移除或修改错误的 `nodeSelector`。

- **如果此标签是误加，应移除**：
  ```bash
  # 假设该 Pod 由 Deployment 管理 (请确认实际控制器类型)
  kubectl edit deployment <deployment-name> -n aiops-e2e
  # 在编辑器中找到 spec.template.spec.nodeSelector 字段，将其删除或注释掉，然后保存退出。
  ```

- **如果此标签是特定节点才有的，应修正为正确的标签名**：
  首先，找出正确标签。假设你需要调度到 `node1`，先看它的标签：
  ```bash
  kubectl describe node node1 | grep Labels -A 20
  ```
  然后修改 `nodeSelector`，将 `aiops.e2e/nonexistent-node-label` 替换为正确的标签键值对。

- **如果此 Pod 是测试用的，可以直接删除**：
  ```bash
  kubectl delete pod rc-pending-nodeselector -n aiops-e2e
  ```

**依据**：移除不存在的节点选择器约束是解除 Pod 卡在 Pending 状态的唯一方法。

### 后续优化
1. **配置管理**：在 CI/CD 或应用部署流程中，增加对 `nodeSelector` / `nodeAffinity` 的校验，确保其引用的标签在目标集群中实际存在。
2. **监控告警**：配置对 `FailedScheduling` 事件的告警，可以及时发现调度失败的 Pod。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 被删除/更新 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | Pod 状态应消失（已删除）或被新的 Pod 替换并处于 `Running` 状态 |
| 2. 检查新 Pod 事件 | `kubectl describe pod <new-pod-name> -n aiops-e2e` | `Events` 中不再出现 `FailedScheduling` 事件，并显示 `Successfully assigned` 事件 |

---

## ⚠️ 注意事项
- 当前集群功能正常，此问题仅影响一个特定 Pod，不影响其他 59 个正常运行的应用。
- 执行修复前，请明确该 Pod 是否被 Deployment / StatefulSet / Job 等控制器管理。如果是，直接编辑控制器是最佳实践，`kubectl delete pod` 仅在 Pod 是裸 Pod 时有效。
- 请勿在生产环境中随意删除未确认角色的 Pod。

---

## 📊 性能统计

├─ 总耗时: 1.6m
├─ 问题定位: 22.7s (24%) ✅
├─ 证据链采集: 21.6s (23%) ✅
├─ 根因分析: 22.5s (24%) ✅
├─ 汇总总结: 26.2s (28%) ✅
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
