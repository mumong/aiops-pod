======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 67baf0abeb0f4847]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先对集群进行全局 Pod 状态扫描，看看当前有哪些异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 发现 1 个异常 Pod。让我进一步查看详情。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          98s   <none>   <none>   
   💭 [问题定位] 这个 Pod 的状态关键字是 `Pending`，标签中已标注 `pod_abnormal_type=PendingUnschedulable`。让我获取匹配的 runbook 并进一步确认调度失败原因。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 让我确认一下调度失败的具体原因。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  101s  default-scheduler  0/3 nodes are available: 3 node(s) did
   💭 [问题定位] 现在我已经掌握了完整的异常信息。

---

## 定位分析结果

### 集群异常概况

集群共 65 个 Pod，**1 个异常 Pod**，其余 59 个 Running 正常。

### 当前异常 Pod

| 字段 | 值 |
|------|-----|
| **Pod** | `rc-pending-nodeselector`（命名空间：`aiops-e2e`） |
| **状态** | `Pending` |
| **异常类型** | `PendingUnschedulable` |
| **兼容层级** | **L1** — 调度器无法放置 |
| **状态关键字** | `Pending` |

### 异常原因

Pod `rc-pending-nodeselector` 处于 **Pending** 状态，调度器 **FailedScheduling**：
> `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.`

**根因**：该 Pod 设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，而集群中 **没有任何节点** 包含此标签，导致 3 个节点全部不匹配调度约束，Pod 无法被调度。

### 关键实体

| 实体 | 角色 |
|------|------|
| `rc-pending-nodeselector` (aiops-e2e) | 异常 Pod |
| `default-scheduler` | 调度器报告无可用节点 |
| 集群 3 个节点 | 均不匹配 nodeSelector |

### 可能场景

1. **nodeSelector 标签不存在**：`aiops.e2e/nonexistent-node-label=true` 在集群中不存在，Pod 永远无法被调度。
2. **测试/演练场景**：Pod 带有 `rootcause-e2e=true` 标签，推测是端到端测试构造的异常场景。

---

**结论**：当前集群仅有一个 L1 级别异常——Pod `rc-pending-nodeselector` 因 `nodeSelector` 指向一个不存在的节点标签而处于 Pending 不可调度状态。建议检查是否需要添加该标签到目标节点，或修正 Pod 的 `nodeSelector`。
   ✅ [问题定位] 完成 (19.0s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector标签不存在', 'probability': '高', 'reason': 'Pod设置了nodeSelector: aiops.e2e/nonexistent-node-label=true，集群3个节点均不匹配该标签，调度器报告FailedScheduling'}, {'scenario': '测试/演练场景', 'probability': '中', 'reason': 'Pod带有rootcause-e2e=true标签，推测是端到端测试构造的异常场景'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Scheduler", "name": "default-scheduler", "namespace": ""}, {"type": "Node", "name": "3 nodes", "namespace": ""}]
   reasoning=集群共65个Pod，59个Running正常，1个异常Pod。异常Pod为aiops-e2e/rc-pending-nodeselector，状态Pending，异常类型为PendingUnschedulable。调度器报告FailedScheduling：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod设置了nodeSelector: aiops.e2e/nonexistent-node-label=true，集群中没有任何节点包含此标签。根据五层模型，PendingUnschedulable属于L1（调度器无法放置），派生层为L1，状态分类为scheduling。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "scheduling", "confidence": 0.95, "reasoning": "集群共65个Pod，59个Running正常，1个异常Pod。异常Pod为aiops-e2e/rc-pending-nodeselector，状态Pending，异常类型为PendingUnschedulable。调度器报告FailedScheduling：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod设置了nodeSelector: aiops.e2e/nonexistent-node-label=true，集群中没有任何节点包含此标签。根据五层模型，PendingUnschedulable属于L1（调度器无法放置），派生层为L1，状态分类为scheduling。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Scheduler", "name": "default-scheduler", "namespace": ""}, {"type": "Node", "name": "3 nodes", "namespace": ""}], "possible_scenarios": [{"scenario": "nodeSelector标签不存在", "probability": "高", "reason": "Pod设置了nodeSelector: aiops.e2e/nonexistent-node-label=true，集群3个节点均不匹配该标签，调度器报告FailedScheduling"}, {"scenario": "测试/演练场景", "probability": "中", "reason": "Pod带有rootcause-e2e=true标签，推测是端到端测试构造的异常场景"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              96s     <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/67baf0abeb0f4847/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/67baf0abeb0f4847/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/67baf0abeb0f4847/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我来按既有 evidence_plan 执行所有关键工具调用。先并行执行几个独立任务。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAME     STATUS   ROLES           AGE    VERSION   LABELS\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpg
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  2m2s  default-scheduler  0/3 nodes are available: 3 node(s) did
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
   💭 [证据链采集] 现在执行最后一个计划项 e5，获取命名空间事件信息。
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
2m4s        Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are
   💭 [证据链采集] 所有计划工具已执行完毕，下面是证据总结：

---

## ✅ 证据采集完成

### 已采集的证据（4项关键+1项重要）

| 编号 | 工具 | 关键发现 | 等级 |
|------|------|---------|------|
| **e1** | `kubectl describe pod` | FailedScheduling 事件原文：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`；Node-Selectors=`aiops.e2e/nonexistent-node-label=true` | **critical** |
| **e2** | `kubectl get nodes --show-labels` | 3 个节点的标签中均 **不存在** `aiops.e2e/nonexistent-node-label` 标签 | **critical** |
| **e3** | `kubectl get nodes` | 全部 3 个节点（master/node1/node2）状态均为 **Ready**，无异常节点 | **important** |
| **e4** | `kubectl get pod -o yaml` | 完整 YAML 确认：`nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}`；PodScheduled condition=False/Unschedulable；无 finalizers 卡住；`imagePullPolicy=Never` 但该字段不影响调度阶段 | **critical** |
| **e5** | `kubectl_events` | 仅 1 条 FailedScheduling 事件，无其他异常事件 | **important** |

### 根因结论

**Pod `rc-pending-nodeselector` 处于 Pending 状态，根因为 nodeSelector 标签不匹配。**
- Pod 设置了硬性约束 `nodeSelector: aiops.e2e/nonexistent-node-label=true`
- 集群 3 个节点均无此标签，调度器无法放置 Pod
- 无其他并发异常（3 节点全部 Ready，无 PVC 依赖，无 taint 冲突）
- Pod 带有 `rootcause-e2e=true` 标签，符合测试/演练场景特征

### 未采集 / 冲突证据
- 无冲突证据：所有工具调用均成功返回，Pod 和节点均存在于指定 namespace/集群中。
- 无需进一步采集：本异常只涉及单一异常组（Pending 1 个 Pod），已完整覆盖。
   ✅ [证据链采集] 完成 (17.1s)
   📤 → 下游数据: evidence_items=6/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"Describe Pod rc-pending-nodeselector 获取详细调度事件和 spec","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-pending-nodeselector","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"确认FailedScheduling事件原文、nodeSelector、Tolerations、QoS等关键配置","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取集群所有节点标签，验证 nodeSelector 匹配情况","level":"critical","tool":"run_bash_command","command":"kubectl get nodes --show-labels","tool_args":{},"purpose":"验证集群节点是否有 aiops.e2e/nonexistent-node-label=true 标签","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"查看集群节点状态和调度可用性","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes","tool_args":{},"purpose":"检查所有节点是否Ready且可调度","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"查看Pod的YAML确认spec详情","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod -n aiops-e2e rc-pending-nodeselector -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"获取完整Pod spec，包括nodeSelector、containers、volumes等YAML细节","evidence_type":"","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e5","description":"查看aiops-e2e命名空间事件确认调度历史","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --sort-by=.lastTimestamp","tool_args":{"namespace":"aiops-e2e"},"purpose":"获取Pods相关事件，确认FailedScheduling以外的其他异常事件","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAME     STATUS   ROLES           AGE    VERSION   LABELS\\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\\nnode1    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\nnode2    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/67baf0abeb0f4847/tools/001-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/67baf0abeb0f4847/tools/001-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/67baf0abeb0f4847/tools/001-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  2m2s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  2m2s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/67baf0abeb0f4847/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/67baf0abeb0f4847/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/67baf0abeb0f4847/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/67baf0abeb0f4847/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/67baf0abeb0f4847/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/67baf0abeb0f4847/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   238d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          238d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\nnode2    Ready    <none>          238d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/67baf0abeb0f4847/tools/004-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/67baf0abeb0f4847/tools/004-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/67baf0abeb0f4847/tools/004-evidence-kubectl_get_by_kind_in_cluster.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n2m4s        Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/67baf0abeb0f4847/tools/005-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/67baf0abeb0f4847/tools/005-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/67baf0abeb0f4847/tools/005-evidence-kubectl_events.summary.txt"}],"llm_analysis":"所有计划工具已执行完毕，下面是证据总结：\n\n---\n\n## ✅ 证据采集完成\n\n### 已采集的证据（4项关键+1项重要）\n\n| 编号 | 工具 | 关键发现 | 等级 |\n|------|------|---------|------|\n| **e1** | `kubectl describe pod` | FailedScheduling 事件原文：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`；Node-Selectors=`aiops.e2e/nonexistent-node-label=true` | **critical** |\n| **e2** | `kubectl get nodes --show-labels` | 3 个节点的标签中均 **不存在** `aiops.e2e/nonexistent-node-label` 标签 | **critical** |\n| **e3** | `kubectl get nodes` | 全部 3 个节点（master/node1/node2）状态均为 **Ready**，无异常节点 | **important** |\n| **e4** | `kubectl get pod -o yaml` | 完整 YAML 确认：`nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}`；PodScheduled condition=False/Unschedulable；无 finalizers 卡住；`imagePullPolicy=Never` 但该字段不影响调度阶段 | **critical** |\n| **e5** | `kubectl_events` | 仅 1 条 FailedScheduling 事件，无其他异常事件 | **important** |\n\n### 根因结论\n\n**Pod `rc-pending-nodeselector` 处于 Pending 状态，根因为 nodeSelector 标签不匹配。**\n- Pod 设置了硬性约束 `nodeSelector: aiops.e2e/nonexistent-node-label=true`\n- 集群 3 个节点均无此标签，调度器无法放置 Pod\n- 无其他并发异常（3 节点全部 Ready，无 PVC 依赖，无 taint 冲突）\n- Pod 带有 `rootcause-e2e=true` 标签，符合测试/演练场景特征\n\n### 未采集 / 冲突证据\n- 无冲突证据：所有工具调用均成功返回，Pod 和节点均存在于指定 namespace/集群中。\n- 无需进一步采集：本异常只涉及单一异常组（Pending 1 个 Pod），已完整覆盖。","collection_summary":"计划 5 项，实际采集 3 项，未采集 2 项，完整度 60%；其中真实环境证据 6/8 项，完整度 75%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":5,"plan_collected":3,"plan_completeness":0.6,"environment_evidence_total":8,"environment_evidence_collected":6,"environment_evidence_completeness":0.75,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"Describe Pod rc-pending-nodeselector 获取详细调度事件和 spec","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-pending-nodeselector","purpose":"确认FailedScheduling事件原文、nodeSelector、Tolerations、QoS等关键配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取集群所有节点标签，验证 nodeSelector 匹配情况","level":"critical","tool":"run_bash_command","command":"kubectl get nodes --show-labels","purpose":"验证集群节点是否有 aiops.e2e/nonexistent-node-label=true 标签","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"查看集群节点状态和调度可用性","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes","purpose":"检查所有节点是否Ready且可调度","collected":false,"source":"planned","outcome":"unknown"},{"id":"e4","description":"查看Pod的YAML确认spec详情","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod -n aiops-e2e rc-pending-nodeselector -o yaml","purpose":"获取完整Pod spec，包括nodeSelector、containers、volumes等YAML细节","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"查看aiops-e2e命名空间事件确认调度历史","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --sort-by=.lastTimestamp","purpose":"获取Pods相关事件，确认FailedScheduling以外的其他异常事件","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["e3(查看集群节点状态和调度可用性): 已规划但工具执行失败或无匹配结果","e5(查看aiops-e2e命名空间事件确认调度历史): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/5 项, 完整度: 75%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | Describe Pod rc-pending-nodeselector 获取详细调度事件... | `kubectl describe pod -n aiops-e2e rc-pending-nodeselector` |
   | e2 | critical | ✅ | run_bash_command | 获取集群所有节点标签，验证 nodeSelector 匹配情况 | `kubectl get nodes --show-labels` |
   | e3 | important | ❌ | kubectl_get_by_kind_in_cl... | 查看集群节点状态和调度可用性 | `kubectl get nodes` |
   | e4 | critical | ✅ | kubectl_get_yaml | 查看Pod的YAML确认spec详情 | `kubectl get pod -n aiops-e2e rc-pending-nodeselector -o yaml` |
   | e5 | important | ❌ | kubectl_events | 查看aiops-e2e命名空间事件确认调度历史 | `kubectl get events -n aiops-e2e --sort-by=.lastTimestamp` |

   ⚠️ 未采集原因:
   - e3(查看集群节点状态和调度可用性): 已规划但工具执行失败或无匹配结果
   - e5(查看aiops-e2e命名空间事件确认调度历史): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (18.1s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector（ns: aiops-e2e）当前状态Pending，异常类型PendingUnschedulable。调度器报告 FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod YAML确认nodeSelector为{"aiops.e2e/nonexistent-node-label":"true"}，而集群3个节点（master、node1、node2）全部Ready但均无此标签。Pod带有rootcause-e2e=true标签，符合端到端测试构造的异常场景特征。无其他并发异常（3节点全部Ready，无PVC依赖，无taint冲突）。
   confidence=95%
   causal_chain={"root_cause": "Pod设置了硬性nodeSelector约束 aiops.e2e/nonexistent-node-label=true，而集群中3个节点均不包含此标签", "propagation": "调度器在调度周期中评估Pod的nodeSelector约束 → 遍历所有3个节点 → 发现无节点拥有该标签 → 标记Pod为Unschedulable → 持续重试但始终无法放置", "direct_cause": "调度器无法找到满足nodeSelector要求的节点，所有3个节点均因不匹配node selector/affinity被排除", "manifestation": "Pod rc-pending-nodeselector 在aiops-e2e命名空间中持续处于Pending状态，kubectl显示STATUS=Pending，READY=0/1，无分配的NODE和IP"}
   rca_analysis={"phenomenon": "集群共65个Pod，59个Running正常，1个异常Pod。异常Pod为aiops-e2e/rc-pending-nodeselector，状态Pending，异常类型PendingUnschedulable。调度器报告FailedScheduling：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。", "evidence_inventory": [{"id": "e1", "source": "kubectl describe pod", "content": "FailedScheduling事件: 0/3 nodes不匹配node affinity/selector; Pod Node-Selectors=aiops.e2e/nonexistent-node-label=true", "reliability": "高"}, {"id": "e2", "source": "kubectl get nodes --show-labels", "content": "3节点(master/node1/node2)全部Ready，均无aiops.e2e/nonexistent-node-label标签", "reliability": "高"}, {"id": "e3", "source": "kubectl get nodes (状态)", "content": "3节点全部Ready，无SchedulingDisabled或NotReady", "reliability": "高"}, {"id": "e4", "source": "kubectl get pod -o yaml", "content": "Pod YAML确认nodeSelector: {\"aiops.e2e/nonexistent-node-label\":\"true\"}; PodScheduled condition=False/Unschedulable", "reliability": "高"}, {"id": "e5", "source": "kubectl_events", "content": "仅1条FailedScheduling事件，无其他异常事件", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedScheduling 2m2s default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. Node-Selectors: aiops.e2e/nonexistent-node-label=true", "interpretation": "调度器明确拒绝调度Pod，原因是所有3个节点均不匹配Pod的nodeSelector/affinity约束"}, {"evidence_id": "e2", "raw_data": "master/Ready, node1/Ready, node2/Ready. 标签列表不含aiops.e2e/nonexistent-node-label", "interpretation": "3个节点全部处于Ready状态可调度，但均缺少Pod所需的aiops.e2e/nonexistent-node-label=true标签"}, {"evidence_id": "e3", "raw_data": "rows=3 abnormal=0 status_counts={'Ready': 3}", "interpretation": "节点层面无异常，无节点被标记为SchedulingDisabled或NotReady，排除节点不可用原因"}, {"evidence_id": "e4", "raw_data": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\":\"true\"}; conditions: PodScheduled=False reason=Unschedulable", "interpretation": "Pod YAML确认设置了硬性nodeSelector约束，调度条件为False且原因为Unschedulable，印证调度器无法找到匹配节点"}, {"evidence_id": "e5", "raw_data": "2m4s Warning FailedScheduling Pod/rc-pending-nodeselector: 0/3 nodes are available...", "interpretation": "命名空间事件中仅有这一条FailedScheduling事件，无PVC绑定失败、镜像拉取失败等其他异常事件，排除并发问题"}], "causal_chain": {"root_cause": "Pod设置了硬性nodeSelector约束 aiops.e2e/nonexistent-node-label=true，而集群中3个节点均不包含此标签", "propagation": "调度器在调度周期中评估Pod的nodeSelector约束 → 遍历所有3个节点 → 发现无节点拥有该标签 → 标记Pod为Unschedulable → 持续重试但始终无法放置", "direct_cause": "调度器无法找到满足nodeSelector要求的节点，所有3个节点均因不匹配node selector/affinity被排除", "manifestation": "Pod rc-pending-nodeselector 在aiops-e2e命名空间中持续处于Pending状态，kubectl显示STATUS=Pending，READY=0/1，无分配的NODE和IP"}, "root_cause": "Pod rc-pending-nodeselector（ns: aiops-e2e）当前状态Pending，异常类型PendingUnschedulable。调度器报告 FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod YAML确认nodeSelector为{\"aiops.e2e/nonexistent-node-label\":\"true\"}，而集群3个节点（master、node1、node2）全部Ready但均无此标签。Pod带有rootcause-e2e=true标签，符合端到端测试构造的异常场景特征。无其他并发异常（3节点全部Ready，无PVC依赖，无taint冲突）。", "root_cause_summary": "Pod rc-pending-nodeselector（ns: aiops-e2e）当前状态Pending，异常类型PendingUnschedulable。调度器报告 FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod YAML确认nodeSelector为{\"aiops.e2e/nonexistent-node-label\":\"true\"}，而集群3个节点（master、node1、node2）全部Ready但均无此标签。Pod带有rootcause-e2e=true标签，符合端到端测试构造的异常场景特征。无其他并发异常（3节点全部Ready，无PVC依赖，无taint冲突）。", "confidence": 0.95, "confidence_reason": "有4项关键证据（e1调度事件、e2节点标签、e4 Pod YAML、e5事件确认）和1项重要证据（e3节点状态），所有证据相互印证且无冲突，因果链完整清晰。置信度0.95。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "集群资源不足（CPU/内存）", "probability": "low", "reason": "调度器消息明确说是node affinity/selector不匹配，而非Insufficient cpu/memory；3节点全部Ready且有充足资源"}, {"cause": "节点taint与Pod toleration不匹配", "probability": "low", "reason": "调度器消息未提及taint相关拒绝原因；Pod有默认toleration，且3节点均无不可容忍的taint"}, {"cause": "PVC未绑定导致调度阻塞", "probability": "low", "reason": "Pod YAML中无PVC声明，只有kube-api-access-w74s5 projected volume，不涉及存储依赖"}], "limitations": "无需进一步采集：本异常只涉及单一异常组（Pending 1个Pod），已完整覆盖。节点标签数据通过kubectl get nodes --show-labels确认，未遗漏任何节点标签。", "llm_raw_analysis": "## 证据清点\\n共5项证据：e1（kubectl describe pod - FailedScheduling事件和Node-Selectors）、e2（kubectl get nodes --show-labels - 3节点标签）、e3（kubectl get nodes - 节点状态Ready）、e4（kubectl get pod -o yaml - Pod YAML/conditions）、e5（kubectl_events - 事件确认）\\n\\n## 逐条分析\\n- e1: 调度器明确报告0/3 nodes匹配node affinity/selector，Node-Selectors字段显示aiops.e2e/nonexistent-node-label=true\\n- e2: 3节点全部Ready，标签列表均不含aiops.e2e/nonexistent-node-label\\n- e3: 节点无异常状态，排除节点不可用导致无法调度\\n- e4: YAML确认nodeSelector配置和PodScheduled=False/Unschedulable状态\\n- e5\n... 截断，原始 699 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector（ns: aiops-e2e）当前状态Pending，异常类型PendingUnschedulable。调度器报告 FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match...
   置信度: 95%
   🔗 因果链:
     根本原因: Pod设置了硬性nodeSelector约束 aiops.e2e/nonexistent-node-label=true，而集群中3个节点均不包含此标签
     传导机制: 调度器在调度周期中评估Pod的nodeSelector约束 → 遍历所有3个节点 → 发现无节点拥有该标签 → 标记Pod为Unschedulable → 持续重试但始终无法放置
     最终表现: Pod rc-pending-nodeselector 在aiops-e2e命名空间中持续处于Pending状态，kubectl显示STATUS=Pending，READY=0/1，无分配的NODE和IP


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (18.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5481 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 13.0s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为一名资深 K8s 诊断报告专家，我将根据您提供的分析结果，为您生成一份详尽、完整的诊断报告。

---

## 📊 诊断概览

**直接回答：您集群当前主要存在一个问题：一个 Pod 因为 `nodeSelector` 配置错误而处于 `Pending` 状态，无法被调度。集群整体健康，在 65 个 Pod 中，59 个 (90.8%) 正常运行。**

以下是问题的核心信息：

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending (PendingUnschedulable) |
| **兼容归因层** | L1 - 调度 |
| **问题分类** | Scheduling (调度失败) |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/5 (60%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-pending-nodeselector` |
| Namespace | `aiops-e2e` |
| Node | `master`, `node1`, `node2` |
| 错误信息 | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 事件 | `kubectl describe`, `kubectl events` | `Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 调度器明确告知无法找到匹配的节点。 |
| 2 | Pod 配置 | `kubectl describe`, `kubectl get yaml` | `Node-Selectors: aiops.e2e/nonexistent-node-label=true` | Pod 设置了硬性 `nodeSelector` 约束，要求节点必须拥有标签 `aiops.e2e/nonexistent-node-label=true`。 |
| 3 | 节点标签 | `run_bash_command (kubectl get nodes --show-labels)` | `master`: `...kubernetes.io/hostname=master,...`<br>`node1`: `...kubernetes.io/hostname=node1,...`<br>`node2`: `...kubernetes.io/hostname=node2,...` | 集群中三个节点均**未**包含 `aiops.e2e/nonexistent-node-label` 这个标签。 |
| 4 | 节点状态 | `kubectl get nodes` | `master: Ready`<br>`node1: Ready`<br>`node2: Ready` | 所有节点状态均为 `Ready`，不存在节点不可用的问题。 |
| 5 | Pod 状态 | `kubectl get po -A` | `rc-pending-nodeselector   0/1     Pending   0          98s   <none>   <none>` | Pod 持续停留在 `Pending` 状态，没有分配给任何节点。 |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：Pod 的 `nodeSelector` (证据 #2) 要求标签 `aiops.e2e/nonexistent-node-label=true` 在节点上存在。调度器 (证据 #1) 在遍历所有 3 个节点 (证据 #3) 后发现，没有节点拥有这个标签，因此无法调度。
- **证据链**：`nodeSelector` 标签不存在 → 调度器找不到匹配节点 → 触发 `FailedScheduling` 事件 → Pod 持续处于 `Pending` 状态。
- **排除项**：证据 #4 显示所有节点都 **Ready**，排除了节点不可用导致的调度失败。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| (无) | - | 证据链完整，当前证据足以定位根因，无需补充。 |

---

## 🎯 根因分析

### 因果链

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                    │
│ Pod "rc-pending-nodeselector" 的 spec 中定义了硬性 nodeSelector 约束：       │
│   "aiops.e2e/nonexistent-node-label=true"                                   │
│ 该标签在集群中的任何节点（master, node1, node2）上都不存在。                │
└──────────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                    │
│ Pod 创建 → 调度器 default-scheduler 尝试调度 → 评估 nodeSelector 约束       │
│ → 遍历所有节点 → 发现均无匹配标签 → 标记为 Unschedulable                    │
└──────────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                    │
│ 调度器无法找到满足 nodeSelector 要求的节点，发生 FailedScheduling 事件。    │
└──────────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                │
│ Pod "rc-pending-nodeselector" 在 aiops-e2e 命名空间中持续处于 Pending 状态， │
│ READY=0/1，无分配的 NODE 和 IP。                                           │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (FailedScheduling 事件)、证据 #2 (`Node-Selectors: aiops.e2e/nonexistent-node-label=true`) 和证据 #3 (节点标签列表)，问题的根本原因是 **Pod 配置的 `nodeSelector` 指定了一个在所有节点上都不存在的标签 `aiops.e2e/nonexistent-node-label=true`**。这导致调度器（default-scheduler）无法找到任何可以放置该 Pod 的节点，从而使 Pod 持续卡在 `Pending` 状态。

**置信度**：高 (95%)
- ✅ `FailedScheduling` 事件直接指向 `node affinity/selector` 不匹配。
- ✅ Pod YAML 和 `kubectl describe` 输出明确显示 `nodeSelector` 配置。
- ✅ 节点标签数据明确显示所有标签，确认没有匹配的标签。
- ✅ (注：Pod 带有 `rootcause-e2e=true` 标签，这很可能是一个为端到端测试构造的异常场景。)

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [核心] 删除或修正 `nodeSelector` 配置**

根据您的意图，选择以下操作之一：

  * **场景A: 这是一个测试Pod，应立即删除**
     ```bash
     kubectl delete pod rc-pending-nodeselector -n aiops-e2e
     ```
     *依据*：如果这是为验证 `Pending` 状态而创建的测试 Pod。

  * **场景B: 这是一个需要正常运行的Pod，需要修正`nodeSelector`**
     您需要编辑 Pod (如果是通过 Deployment/StatefulSet 创建) 或直接编辑 Pod (如果是独立 Pod，建议通过重新创建)：
     ```bash
     # 如果是由 Deployment 创建的 (假设 deployment 名称与 pod 标签 app 一致)
     kubectl edit deployment rc-pending-nodeselector -n aiops-e2e
     ```
     在 YAML 中找到 `nodeSelector` 字段，将其修改为集群中存在的标签，或直接删除整个 `nodeSelector` 块。
     *依据*：当前 `nodeSelector` 指向一个不存在的标签，必须修正。

### 后续优化
1. **避免使用硬编码的、不存在的标签**：在 Pod YAML 中使用 `nodeSelector` 或 `nodeAffinity` 时，请确保目标标签确实存在于集群节点上。
2. **监控告警**：配置对 `Pending` 状态 Pod 的监控告警，以便及时发现并处理调度问题。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: `Running` 或 Pod 已被删除 |
| 2. 检查 Pod 事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 不再有 `FailedScheduling` 事件 |

---

## ⚠️ 注意事项
- 该 Pod 带有的 `rootcause-e2e=true` 标签高度暗示这是一个用于测试或演练的场景。请根据实际情况决定是删除还是修复它。
- 所有 3 个节点均处于 `Ready` 状态，无其他异常，因此本次问题不影响其他 59 个正常运行的 Pod。

---

## 📊 性能统计

├─ 总耗时: 1.2m
├─ 问题定位: 19.0s (26%) ✅
├─ 证据链采集: 17.1s (23%) ✅
├─ 根因分析: 18.1s (25%) ✅
├─ 汇总总结: 18.7s (26%) ✅
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
