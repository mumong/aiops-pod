======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 4eb0a6ca351b419f]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先来扫描整个集群的所有 Pod，看看当前有哪些异常状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 发现了一个异常 Pod。让我查看详细信息。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          38m   <none>   <none>   
   💭 [问题定位] 这个 Pod 的标签里标注了 `pod_abnormal_type=PendingUnschedulable`，让我描述一下看看详细信息。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  38m                default-scheduler  0/3 nodes are available: 
   💭 [问题定位] 很好，信息非常清晰了。现在让我获取相关的 runbook 来参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在我已经收集到了足够的信息来进行完整的定位分析。

---

## 定位分析结果

### 全局 Pod 状态扫描

| 状态 | 数量 |
|------|------|
| Running（正常） | 59 |
| **Pending（异常）** | **1** |
| **合计** | 65（其中 **异常 1**） |

---

### 异常 Pod 详情

| Pod | 命名空间 | 状态 | 年龄 |
|-----|---------|------|------|
| `rc-pending-nodeselector` | `aiops-e2e` | Pending | 38分钟 |

### 调度失败根因

从 `kubectl describe` 得到的关键信息：

- **Events 中明确报错**：
  ```
  FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.
  ```
- **Node-Selectors** 设置为：`aiops.e2e/nonexistent-node-label=true`
- **3 个节点均不匹配**该 nodeSelector，且抢占调度也无法帮助（3 Preemption is not helpful）

---

### 输出分类

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **layer_name** | 调度约束不匹配（nodeSelector） |
| **pod_status_keyword** | Pending |
| **pod_abnormal_type** | PendingUnschedulable |
| **status_category** | scheduling |
| **异常 Pod 数** | 1 |
| **置信度** | **高** |

---

### 异常组

| 组名 | Pod 列表 | 状态关键字 | 数量 |
|------|---------|-----------|------|
| `PendingUnschedulable` | `rc-pending-nodeselector` | Pending | 1 |

### 关键实体

| 实体类型 | 名称 | 说明 |
|---------|------|------|
| Pod | `rc-pending-nodeselector` | 当前唯一异常 Pod |
| Namespace | `aiops-e2e` | 异常 Pod 所在命名空间 |
| 节点 | 集群中 3 个节点 | 均因 nodeSelector 不匹配不可调度 |

### 可能的场景

1. **nodeSelector 指向不存在的标签** — Pod 设置了 `aiops.e2e/nonexistent-node-label=true` 的 nodeSelector，但集群中没有任何节点具有该标签，导致所有 3 个节点都不满足条件。
2. **测试/e2e 场景** — Pod 标签含有 `rootcause-e2e=true` 和 `pod_abnormal_type=PendingUnschedulable`，表明这是一个用于验证调度失败检测能力的 E2E 测试 Pod。

### 建议方向

- 确认该 Pod 是否是有意创建的 E2E 测试用例（从标签看可能性很大）。
- 若为误配置，可调整 nodeSelector 为集群节点上真实存在的标签，或直接移除 nodeSelector。
   ✅ [问题定位] 完成 (25.3s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector指向不存在的标签', 'probability': '高', 'reason': 'Pod设置了aiops.e2e/nonexistent-node-label=true的nodeSelector，3个节点均无该标签导致调度失败'}, {'scenario': 'E2E测试场景', 'probability': '高', 'reason': 'Pod标签包含rootcause-e2e=true和pod_abnormal_type=PendingUnschedulable，表明是用于验证调度失败检测能力的测试用例'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}]
   reasoning=集群中存在1个异常Pod rc-pending-nodeselector（namespace: aiops-e2e），状态为Pending，事件明确显示FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod设置了nodeSelector: aiops.e2e/nonexistent-node-label=true，但集群3个节点均不匹配该标签。根据五层模型，调度约束不匹配属于L1（scheduling/node_kubelet）范畴。仅1个异常Pod，其余59个Pod均正常Running，问题明确且范围受限。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "调度约束不匹配（nodeSelector）", "confidence": 0.95, "reasoning": "集群中存在1个异常Pod rc-pending-nodeselector（namespace: aiops-e2e），状态为Pending，事件明确显示FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod设置了nodeSelector: aiops.e2e/nonexistent-node-label=true，但集群3个节点均不匹配该标签。根据五层模型，调度约束不匹配属于L1（scheduling/node_kubelet）范畴。仅1个异常Pod，其余59个Pod均正常Running，问题明确且范围受限。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "nodeSelector指向不存在的标签", "probability": "高", "reason": "Pod设置了aiops.e2e/nonexistent-node-label=true的nodeSelector，3个节点均无该标签导致调度失败"}, {"scenario": "E2E测试场景", "probability": "高", "reason": "Pod标签包含rootcause-e2e=true和pod_abnormal_type=PendingUnschedulable，表明是用于验证调度失败检测能力的测试用例"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              38m     <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/4eb0a6ca351b419f/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/4eb0a6ca351b419f/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/4eb0a6ca351b419f/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我将按照既有 evidence_plan 执行真实环境证据采集。先启动关键工具调用。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_events
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
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  39m                default-scheduler  0/3 nodes are available: 
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
39m                 Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 n
   💭 [证据链采集] 所有 critical 和 important 级工具已执行完毕。现在按计划获取 runbook 参考。
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [证据链采集] ## 📋 证据采集结果

### 已采集证据（4项关键证据）

| 证据项 | 来源 | 结果 |
|--------|------|------|
| **① Pod 当前状态** | `kubectl describe pod` (ev-001) | ✅ Pod 仍为 **Pending**，未绑定任何 Node，QoS Class: BestEffort |
| **② FailedScheduling 事件原文** | `kubectl describe pod` + `kubectl_events` (ev-001, ev-004) | ✅ `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` — 持续 39 分钟，无变化 |
| **③ Pod spec nodeSelector 配置** | `kubectl_get_yaml` (ev-002) | ✅ **关键证据**: `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}` — 明确指向一个不存在的标签键值对 |
| **④ 3 个节点标签清单** | `run_bash_command` (ev-003) | ✅ 3 个节点（master/node1/node2）均 **不包含** `aiops.e2e/nonexistent-node-label` 标签，直接证实节点标签不匹配 |

### 冲突/负向证据
- ❌ **无冲突证据**：Pod 实体存在、namespace 匹配、事件非空、节点标签清单完整，所有结果均一致指向同一根因。

### 根因判定（依据 runbook 判定规则）
> **判定结论**：`FailedScheduling + node(s) didn't match node selector/affinity` → **调度约束不匹配（置信度：高）**
>
> **具体原因**：Pod 的 nodeSelector 设置为 `aiops.e2e/nonexistent-node-label=true`，而集群 3 个节点均无此标签，导致调度器无法放置。从 Pod 标签 `rootcause-e2e=true` 和 `pod_abnormal_type=PendingUnschedulable` 判断，这是一个 **E2E 测试用例**，用于验证调度失败检测能力。

### 建议修复方案（仅供参考，不执行）
- **短期修复**：将 Pod 的 nodeSelector 改为集群中实际存在的标签（如 `node-role.kubernetes.io/control-plane=` 或 `kubernetes.io/hostname=node1`），或删除 nodeSelector 使其调度到任意节点
- **长期/测试场景**：既然是 E2E 测试 Pod，可以直接删除该 Pod 以消除告警：`kubectl delete pod rc-pending-nodeselector -n aiops-e2e`
   ✅ [证据链采集] 完成 (24.5s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"ev-001","description":"验证Pod rc-pending-nodeselector 当前状态、nodeSelector、FailedScheduling事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e","resource_type":"pod"},"purpose":"验证Pod是否仍处于Pending状态，确认FailedScheduling事件原文（nodeSelector/affinity不匹配），检查nodeSelector配置","evidence_type":"current_status","target_scope":"abnormal_pods[0]","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"ev-002","description":"获取Pod完整YAML以查看nodeSelector配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e","resource_type":"pod"},"purpose":"确认Pod spec中的nodeSelector具体配置值，验证aiops.e2e/nonexistent-node-label=true标签设置","evidence_type":"pod_spec_config","target_scope":"abnormal_pods[0]","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"ev-003","description":"查看集群所有节点的标签，确认没有匹配nodeSelector的节点","level":"important","tool":"run_bash_command","command":"kubectl get nodes --show-labels","tool_args":{"command":"kubectl get nodes --show-labels"},"purpose":"验证3个节点的标签，确认均不包含aiops.e2e/nonexistent-node-label标签，作为nodeSelector不匹配的直接证据","evidence_type":"node_label_check","target_scope":"cluster_nodes","acceptable_tools":["run_bash_command","kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true},{"id":"ev-004","description":"查看集群事件中关于该Pod的Pending相关事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-nodeselector","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-pending-nodeselector"},"purpose":"确认FailedScheduling事件最新时间戳和完整消息，确认调度失败原因是否稳定一致","evidence_type":"events","target_scope":"abnormal_pods[0]","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"ev-005","description":"获取runbook作为排障参考","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","tool_args":{"runbook_name":"pod-pending-unschedulable.md"},"purpose":"获取调度失败Runbook作为参考上下文","evidence_type":"reference","target_scope":"runbook","acceptable_tools":["fetch_runbook"],"counts_for_completeness":false}],"tool_results":[],"tool_data":[{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAME     STATUS   ROLES           AGE    VERSION   LABELS\\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\\nnode1    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\nnode2    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4eb0a6ca351b419f/tools/001-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4eb0a6ca351b419f/tools/001-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4eb0a6ca351b419f/tools/001-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4eb0a6ca351b419f/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4eb0a6ca351b419f/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4eb0a6ca351b419f/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  39m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  28m (x2 over 33m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  39m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  28m (x2 over 33m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4eb0a6ca351b419f/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4eb0a6ca351b419f/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4eb0a6ca351b419f/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n39m                 Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n28m (x2 over 33m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4eb0a6ca351b419f/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4eb0a6ca351b419f/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4eb0a6ca351b419f/tools/004-evidence-kubectl_events.summary.txt"},{"tool":"fetch_runbook","data":"<runbook>\n# Pod PendingUnschedulable / 调度失败\n\n> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | Pending，且 Events 含 `FailedScheduling` |\n| 资源不足 | `Insufficient cpu/memory/ephemeral-storage`、`Too many pods` |\n| 调度约束 | nodeSelector/affinity 不匹配、节点 taint 未被 toleration 容忍 |\n| 存储前置条件 | `pod has unbound immediate PersistentVolumeClaims` 应切换到 pod-volume-mount-failed |\n| 节点状态 | Node NotReady/Unknown、SchedulingDisabled、Unschedulable 会导致无可用调度节点 |\n\n## 根因分流\n- 资源不足: FailedScheduling 原文含 Insufficient cpu/memory/ephemeral-storage、Too many pods。\n- hostPort 冲突: 原文含 `didn't have free ports for the requested pod ports`，说明目标节点端口已被占用。\n- Taint/Toleration 不匹配: 原文含 `had untolerated taint`，必须检查 Pod tolerations 和 Node taints。\n- nodeSelector / nodeAffinity / podAffinity 不匹配: 原文含 `didn't match Pod's node affinity/selector` 或 affinity/anti-affinity。\n- PVC 未绑定: 原文含 `unbound immediate PersistentVolumeClaims`，根因在存储绑定而不是调度资源。\n- 节点不可调度: Node Ready=False/Unknown、SchedulingDisabled、`node.kubernetes.io/not-ready` 或 `node.kubernetes.io/unreachable`。\n- 镜像、挂载、容器启动错误不会表现为 FailedScheduling；如果 Pod 已绑定 nodeName，应切换到对应 runbook。\n\n## 诊断流程\n\n### Step 1: 确认 Pod 调度失败事件\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n关注 Events 中的 `FailedScheduling` 原文。\n\n### Step 2: 检查 Pod 调度约束\n```bash\nkubectl get pod <pod-name> -n <namespace> -o yaml\n```\n关注: spec.nodeName 是否为空、nodeSelector、affinity、tolerations、topologySpreadConstraints、schedulerName、priorityClassName、resource requests、hostNetwork/hostPort。\n\n### Step 3: 检查节点状态和可调度性\n```bash\nkubectl get nodes -o wide\n```\n关注: STATUS 列是否有 NotReady/Unknown，AGE 判断是否新节点\n\n### Step 4: 检查候选节点详情\n```bash\nkubectl describe node <node-name>\n```\n重点关注:\n- `Conditions` 部分: Ready=False/Unknown 的 reason 和 message\n- `Taints` 部分: 是否有 NoSchedule/NoExecute taint\n- `Allocatable` vs `Capacity`: 资源是否耗尽\n- `Non-terminated Pods`: 节点上运行的 Pod 数量\n\n### Step 5: 检查 PVC 状态（如果 FailedScheduling 指向 PVC）\n```bash\nkubectl get pvc -n <namespace>\nkubectl describe pvc <pvc> -n <namespace>\n```\n关注: Pending、StorageClass、volumeBindingMode、ProvisioningFailed。\n\n### Step 6: 检查 Ready 条件详情\n```bash\nkubectl get node <node-name> -o jsonpath='{.status.conditions[?(@.type==\"Ready\")]}' | python3 -m json.tool\n```\n关注: status, reason, message, lastHeartbeatTime\n\n### Step 7: 检查节点事件\n```bash\nkubectl get events -A --field-selector involvedObject.kind=Node,involvedObject.name=<node-name> --sort-by='.lastTimestamp'\n```\n关注: NodeNotReady、NodeNotSchedulable、PLEG unhealthy 等事件\n\n### Step 8: 检查受影响的 Pending Pod\n```bash\nkubectl get pods -A --field-selector status.phase=Pending | head -20\n```\n\n## 判定规则\n\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| FailedScheduling + Insufficient cpu/memory | 资源不足导致 Pod Pending | 高 |\n| FailedScheduling + Too many pods | 节点 Pod 数量上限导致 Pending | 高 |\n| FailedScheduling + didn't have free ports for the requested pod ports | hostPort 端口冲突导致 Pending | 高 |\n| FailedScheduling + had untolerated taint | taint/toleration 不匹配 | 高 |\n| FailedScheduling + node(s) didn't match node selector/affinity | 调度约束不匹配 | 高 |\n| FailedScheduling + pod has unbound immediate PersistentVolumeClaims | PVC 未绑定，应切换 VolumeMountFailed/PVC 分支 | 高 |\n| 所有候选 Node NotReady/Unschedulable | 无可用调度节点 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4eb0a6ca351b419f/tools/005-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4eb0a6ca351b419f/tools/005-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4eb0a6ca351b419f/tools/005-evidence-fetch_runbook.summary.txt"}],"llm_analysis":"## 📋 证据采集结果\n\n### 已采集证据（4项关键证据）\n\n| 证据项 | 来源 | 结果 |\n|--------|------|------|\n| **① Pod 当前状态** | `kubectl describe pod` (ev-001) | ✅ Pod 仍为 **Pending**，未绑定任何 Node，QoS Class: BestEffort |\n| **② FailedScheduling 事件原文** | `kubectl describe pod` + `kubectl_events` (ev-001, ev-004) | ✅ `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` — 持续 39 分钟，无变化 |\n| **③ Pod spec nodeSelector 配置** | `kubectl_get_yaml` (ev-002) | ✅ **关键证据**: `nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}` — 明确指向一个不存在的标签键值对 |\n| **④ 3 个节点标签清单** | `run_bash_command` (ev-003) | ✅ 3 个节点（master/node1/node2）均 **不包含** `aiops.e2e/nonexistent-node-label` 标签，直接证实节点标签不匹配 |\n\n### 冲突/负向证据\n- ❌ **无冲突证据**：Pod 实体存在、namespace 匹配、事件非空、节点标签清单完整，所有结果均一致指向同一根因。\n\n### 根因判定（依据 runbook 判定规则）\n> **判定结论**：`FailedScheduling + node(s) didn't match node selector/affinity` → **调度约束不匹配（置信度：高）**\n>\n> **具体原因**：Pod 的 nodeSelector 设置为 `aiops.e2e/nonexistent-node-label=true`，而集群 3 个节点均无此标签，导致调度器无法放置。从 Pod 标签 `rootcause-e2e=true` 和 `pod_abnormal_type=PendingUnschedulable` 判断，这是一个 **E2E 测试用例**，用于验证调度失败检测能力。\n\n### 建议修复方案（仅供参考，不执行）\n- **短期修复**：将 Pod 的 nodeSelector 改为集群中实际存在的标签（如 `node-role.kubernetes.io/control-plane=` 或 `kubernetes.io/hostname=node1`），或删除 nodeSelector 使其调度到任意节点\n- **长期/测试场景**：既然是 E2E 测试 Pod，可以直接删除该 Pod 以消除告警：`kubectl delete pod rc-pending-nodeselector -n aiops-e2e`","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 7 个，匹配计划 5 个，未规划证据 2 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":7,"matched_tool_count":5,"unplanned_tool_count":2,"evidence_inventory":[{"id":"ev-001","description":"验证Pod rc-pending-nodeselector 当前状态、nodeSelector、FailedScheduling事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"验证Pod是否仍处于Pending状态，确认FailedScheduling事件原文（nodeSelector/affinity不匹配），检查nodeSelector配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-002","description":"获取Pod完整YAML以查看nodeSelector配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"确认Pod spec中的nodeSelector具体配置值，验证aiops.e2e/nonexistent-node-label=true标签设置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-003","description":"查看集群所有节点的标签，确认没有匹配nodeSelector的节点","level":"important","tool":"run_bash_command","command":"kubectl get nodes --show-labels","purpose":"验证3个节点的标签，确认均不包含aiops.e2e/nonexistent-node-label标签，作为nodeSelector不匹配的直接证据","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-004","description":"查看集群事件中关于该Pod的Pending相关事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-nodeselector","purpose":"确认FailedScheduling事件最新时间戳和完整消息，确认调度失败原因是否稳定一致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-005","description":"获取runbook作为排障参考","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","purpose":"获取调度失败Runbook作为参考上下文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | ev-001 | critical | ✅ | kubectl_describe | 验证Pod rc-pending-nodeselector 当前状态、nodeSelect... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | ev-002 | critical | ✅ | kubectl_get_yaml | 获取Pod完整YAML以查看nodeSelector配置 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | ev-003 | important | ✅ | run_bash_command | 查看集群所有节点的标签，确认没有匹配nodeSelector的节点 | `kubectl get nodes --show-labels` |
   | ev-004 | important | ✅ | kubectl_events | 查看集群事件中关于该Pod的Pending相关事件 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pendi...` |
   | ev-005 | reference | ✅ | fetch_runbook | 获取runbook作为排障参考 | `fetch_runbook pod-pending-unschedulable.md` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (24.3s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector（namespace: aiops-e2e）当前状态为 Pending，持续 39 分钟未调度。直接原因是 Pod 的 nodeSelector 配置为 {"aiops.e2e/nonexistent-node-label": "true"}（ev-002），而集群 3 个节点（master、node1、node2）的标签中均不包含此标签（ev-003），调度器 FailedScheduling 事件明确报告 "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"（ev-001, ev-004）。该 Pod 带有标签 rootcause-e2e=true 和 pod_abnormal_type=PendingUnschedulable，属于 E2E 测试用例。集群其余 59 个 Pod 均正常 Running，故障范围明确且受限。
   confidence=100%
   causal_chain={"root_cause": "Pod 的 nodeSelector 设置为 aiops.e2e/nonexistent-node-label=true，而集群 3 个节点均无此标签，导致调度器无法找到匹配的节点", "propagation": "调度器遍历 3 个节点（master/node1/node2）的标签，均不匹配 nodeSelector 条件 → 判定无可用节点 → 持续重试，每次均失败", "direct_cause": "nodeSelector 引用了集群中不存在的标签键值对 aiops.e2e/nonexistent-node-label=true", "manifestation": "Pod rc-pending-nodeselector 状态为 Pending，持续 39 分钟，Events 显示 FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"}
   rca_analysis={"phenomenon": "集群 aiops-e2e 命名空间下 Pod rc-pending-nodeselector 状态为 Pending，持续 39 分钟未调度到任何节点，Events 显示 FailedScheduling。", "evidence_inventory": [{"id": "ev-001", "source": "kubectl_describe", "content": "Pod rc-pending-nodeselector 状态 Pending，未绑定节点，QoS Class: BestEffort，Node-Selectors: aiops.e2e/nonexistent-node-label=true", "reliability": "高"}, {"id": "ev-002", "source": "kubectl_get_yaml", "content": "Pod YAML 确认 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}，nodeName=None，phase=Pending", "reliability": "高"}, {"id": "ev-003", "source": "kubectl_get_nodes_labels", "content": "3 个节点 master/node1/node2 均不包含 aiops.e2e/nonexistent-node-label 标签", "reliability": "高"}, {"id": "ev-004", "source": "kubectl_events", "content": "FailedScheduling 事件: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}, {"id": "ev-005", "source": "kubectl_get_by_kind_in_cluster", "content": "集群共 65 个 Pod，59 个 Running，仅此 1 个 Pending", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "ev-001", "raw_data": "Node-Selectors: aiops.e2e/nonexistent-node-label=true, status: Pending, node: <none>", "interpretation": "Pod 设置了 nodeSelector 指向 aiops.e2e/nonexistent-node-label=true，但未调度到任何节点，直接说明调度约束是 Pod 未调度的原因"}, {"evidence_id": "ev-002", "raw_data": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}, nodeName: None, phase: Pending", "interpretation": "YAML 确认 nodeSelector 精确配置为 aiops.e2e/nonexistent-node-label=true，且 nodeName 为空（未绑定节点），排除了已绑定节点后出错的场景"}, {"evidence_id": "ev-003", "raw_data": "master LABELS: ...无 aiops.e2e/nonexistent-node-label... node1 LABELS: ...无... node2 LABELS: ...无...", "interpretation": "集群 3 个节点（master、node1、node2）的标签列表中均不包含 aiops.e2e/nonexistent-node-label 键，直接证据表明 nodeSelector 无法匹配任何节点"}, {"evidence_id": "ev-004", "raw_data": "Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.", "interpretation": "调度器明确报告没有节点匹配 Pod 的 node affinity/selector，与 nodeSelector 分析完全吻合；事件持续 39 分钟且重复出现，非瞬时问题"}, {"evidence_id": "ev-005", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}", "interpretation": "集群其余 59 个 Pod 均正常 Running，异常范围仅限此 1 个 Pod，非集群整体故障"}], "causal_chain": {"root_cause": "Pod 的 nodeSelector 设置为 aiops.e2e/nonexistent-node-label=true，而集群 3 个节点均无此标签，导致调度器无法找到匹配的节点", "propagation": "调度器遍历 3 个节点（master/node1/node2）的标签，均不匹配 nodeSelector 条件 → 判定无可用节点 → 持续重试，每次均失败", "direct_cause": "nodeSelector 引用了集群中不存在的标签键值对 aiops.e2e/nonexistent-node-label=true", "manifestation": "Pod rc-pending-nodeselector 状态为 Pending，持续 39 分钟，Events 显示 FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"}, "root_cause": "Pod rc-pending-nodeselector（namespace: aiops-e2e）当前状态为 Pending，持续 39 分钟未调度。直接原因是 Pod 的 nodeSelector 配置为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}（ev-002），而集群 3 个节点（master、node1、node2）的标签中均不包含此标签（ev-003），调度器 FailedScheduling 事件明确报告 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"（ev-001, ev-004）。该 Pod 带有标签 rootcause-e2e=true 和 pod_abnormal_type=PendingUnschedulable，属于 E2E 测试用例。集群其余 59 个 Pod 均正常 Running，故障范围明确且受限。", "root_cause_summary": "Pod rc-pending-nodeselector（namespace: aiops-e2e）当前状态为 Pending，持续 39 分钟未调度。直接原因是 Pod 的 nodeSelector 配置为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}（ev-002），而集群 3 个节点（master、node1、node2）的标签中均不包含此标签（ev-003），调度器 FailedScheduling 事件明确报告 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"（ev-001, ev-004）。该 Pod 带有标签 rootcause-e2e=true 和 pod_abnormal_type=PendingUnschedulable，属于 E2E 测试用例。集群其余 59 个 Pod 均正常 Running，故障范围明确且受限。", "confidence": 1.0, "confidence_reason": "全部 4 项关键证据（Pod 状态、YAML nodeSelector、节点标签清单、FailedScheduling 事件）完全一致指向同一根因，无冲突证据，因果链清晰完整，置信度 1.0", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "资源不足（CPU/内存）导致无法调度", "probability": "low", "reason": "FailedScheduling 事件原文为 'didn't match Pod's node affinity/selector'，而非 'Insufficient cpu/memory'，已排除"}, {"cause": "节点 Taint/Toleration 不匹配", "probability": "low", "reason": "事件原文未提及 'had untolerated taint'，且 Pod 已有 tolerations（not-ready:NoExecute op=Exists 300s），已排除"}, {"cause": "PVC 未绑定导致 Pending", "probability": "low", "reason": "Pod 未引用任何 PVC，事件原文无 'unbound immediate PersistentVolumeClaims'，已排除"}, {"cause": "节点不可调度（NotReady/SchedulingDisabled）", "probability": "low", "reason": "3 个节点 STATUS 均为 Ready，已排除"}], "limitations": "该 Pod 带有 E2E 测试标签（rootcause-e2e=true），属于人工构造的故障测试用例，非生产环境意外故障。根因分析本身证据充分，无局限性。", "llm_raw_analysis": "## 证据清点\n共 8 项已验证事实（4 项关键采集 + 3 项上游验证 + 1 项 runbook），覆盖 Pod 状态、YAML 配置、节点标签、调度事件、集群全局状态。\n\n## 逐条分析\n- **ev-001 (kubectl_describe)**：Pod 当前 Pending，未绑定 node，Node-Selectors=aiops.e2e/nonexistent-node-label=true，直接展示调度约束\n- **ev-002 (kubectl_get_yaml)**：确认 nodeSelector 精确值，nodeName=None 排除已绑定后出错场景\n- **ev-003 (节点标签)**：3 个节点均无 aiops.e2e/nonexistent-node-label 标签，是根因的直接物理证据\n- **ev-004 (kubectl_events)**：FailedScheduling 原文与调度约束分析完全吻合，持续 39 分钟\n- **ev-005 (集群 Pod 统计)**：59/65 Running，仅此 1 个异常，非集群级问题\n\n## 关联分析\n... 截断，原始 945 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector（namespace: aiops-e2e）当前状态为 Pending，持续 39 分钟未调度。直接原因是 Pod 的 nodeSelector 配置为 {"aiops.e2e/nonexistent-node-label": "true"}（e...
   置信度: 100%
   🔗 因果链:
     根本原因: Pod 的 nodeSelector 设置为 aiops.e2e/nonexistent-node-label=true，而集群 3 个节点均无此标签，导致调度器无法找到匹配的节点
     传导机制: 调度器遍历 3 个节点（master/node1/node2）的标签，均不匹配 nodeSelector 条件 → 判定无可用节点 → 持续重试，每次均失败
     最终表现: Pod rc-pending-nodeselector 状态为 Pending，持续 39 分钟，Events 显示 FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (21.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5349 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 36.0s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，请查收您的集群诊断报告。

---
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending |
| **兼容归因层** | L1 - scheduling/node_kubelet |
| **问题分类** | PendingUnschedulable |
| **置信度** | 高 (100%) |
| **证据完整度** | 4/4 (100%) |

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-pending-nodeselector |
| Namespace | aiops-e2e |
| Node | (未分配) |
| 错误信息 | `FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` |

**集群总结**：集群共 65 个 Pod，其中 **59 个运行正常 (Running)**，仅 **1 个异常 Pod (Pending)**。核心问题是该 Pod 调度失败。

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态及事件 | `kubectl describe pod` | `Status: Pending`，`Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | Pod 处于 Pending 状态，原因是调度约束不匹配 |
| 2 | Pod YAML 配置 | `kubectl get pod -o yaml` | `nodeSelector: {aiops.e2e/nonexistent-node-label: "true"}` | Pod 设置了特定的节点标签选择器，要求节点必须具有 `aiops.e2e/nonexistent-node-label: true` 标签 |
| 3 | 节点标签 | `run_bash_command` 获取节点信息 | `master:` 标签列表无 `aiops.e2e/nonexistent-node-label`<br>`node1:` 标签列表无 `aiops.e2e/nonexistent-node-label`<br>`node2:` 标签列表无 `aiops.e2e/nonexistent-node-label` | **集群 3 个节点的标签均不匹配 Pod 要求的 `aiops.e2e/nonexistent-node-label=true`** |
| 4 | 集群事件 | `kubectl events` | `39m Warning FailedScheduling Pod/rc-pending-nodeselector 0/3 nodes are available: ... preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..` | 调度失败事件已重复出现，且抢占调度也无法解决该问题（因为任何节点都不满足约束）。 |
| 5 | 排除项 | `kubectl get pod -o yaml` | `finalizers: <none>` | 明确排除 "finalizer 未清理" 作为根因。 |
| 6 | 归类标签 | Pod Label | `rootcause-e2e=true, pod_abnormal_type=PendingUnschedulable` | 该 Pod 表明上带有人为构造的 E2E 测试标签，属于测试故障场景。 |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：Pod 的 nodeSelector 要求节点拥有 `aiops.e2e/nonexistent-node-label=true` 标签 → 调度器检查所有 3 个节点，发现都不具备该标签 → 产生 `FailedScheduling` 事件，Pod 保持 `Pending`。
- **证据链**：Pod 配置了错误的调度约束 → 所有节点均不满足条件 → 调度失败 → Pod 持续 Pending。

### 缺失证据
无。所有关键证据均已采集，根因明确。

---
## 🎯 根因分析
### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                            │
│ Pod rc-pending-nodeselector 的 spec 中设置了 nodeSelector:                            │
│ {aiops.e2e/nonexistent-node-label: "true"}，但该标签在集群中不存在           │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                          ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                            │
│ 调度器遍历集群 3 个节点（master, node1, node2）的标签，未找到匹配标签                │
│ 抢占式调度也无法生效（因为没有符合条件的节点）                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                          ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                            │
│ 调度器无法将 Pod 调度到任何节点，持续报告 "0/3 nodes are available"               │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                          ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                        │
│ Pod rc-pending-nodeselector 状态为 Pending，持续 39 分钟无法运行                    │
└──────────────────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #1 (FailedScheduling 事件)、证据 #2 (nodeSelector 配置) 和证据 #3 (节点标签列表)，问题根本原因是 **Pod 的 nodeSelector 指定的标签 `aiops.e2e/nonexistent-node-label=true` 与集群中任何一个节点的标签都不匹配**，导致调度器无法找到可运行的节点。

**置信度**：高 (100%)
- ✅ FailedScheduling 事件明确指出 “didn't match Pod's node affinity/selector”。
- ✅ Pod YAML 明确显示错误的 nodeSelector 配置。
- ✅ 节点标签数据明确显示所有节点都不包含该标签。

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [建议] 移除错误 NodeSelector 或更正标签**
   - 方案A：如果 Pod 不需要特定节点，可移除 nodeSelector。
     ```bash
     # 注意：直接编辑 Deployment 或 StatefulSet 的 YAML 并应用，以下为移除 Pod 中 nodeSelector 的示例
     kubectl patch pod rc-pending-nodeselector -n aiops-e2e -p '{"spec":{"nodeSelector":{}}}'
     ```
   - 方案B：如果 Pod 应该运行在特定节点上，可以给目标节点打上正确的标签。例如，如果想让 Pod 调度到 `node1`：
     ```bash
     kubectl label node node1 aiops.e2e/nonexistent-node-label=true
     ```
   - 方案C：如果 Pod 是测试用例，确认其预期行为为 `Pending`，则无需操作。

**2. [可选] 确认是否为测试用例**
  ```bash
  kubectl get pod rc-pending-nodeselector -n aiops-e2e -o jsonpath='{.metadata.labels}'
  ```
  *上述命令会返回标签，如果包含 `rootcause-e2e=true`，则该 Pod 可能为构造的测试故障，无需修复。*

### 后续优化
1. **Pipeline 校验**：在 CI/CD 中增加对 `nodeSelector` 和 `affinity` 的校验，确保其引用的标签在目标集群中真实存在。
2. **告警策略**：设置对 `FailedScheduling` 事件的告警，以便及时发现类似的配置错误。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 | 验证对象 |
|------|------|----------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: `Pending` (如果不修) / `Running` (如果修复) | 第 1 点 |
| 2. 检查事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 不再有新的 `FailedScheduling` 事件 | 第 1 点 |

---
## ⚠️ 注意事项
- 该 Pod 带有 `rootcause-e2e=true` 标签，极大概率是用于验证平台监控和诊断能力的**主动构造的测试故障**，不属于生产环境中的意外故障。如果是这样，只需确认监控系统已准确发现问题即可。

---

## 📊 性能统计

├─ 总耗时: 1.6m
├─ 问题定位: 25.3s (26%) ✅
├─ 证据链采集: 24.5s (26%) ✅
├─ 根因分析: 24.3s (25%) ✅
├─ 汇总总结: 21.8s (23%) ✅
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
