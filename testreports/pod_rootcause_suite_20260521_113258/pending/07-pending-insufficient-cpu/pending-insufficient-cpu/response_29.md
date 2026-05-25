======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 6782911dc88846e5]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来先做一个全局的 Pod 状态扫描，看看集群中是否有异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 发现了一个异常 Pod。让我进一步获取它的详细信息，同时也看看节点情况。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-cpu   0/1     Pending   0          31m   <none>   <
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  31m                default-scheduler  0/3 nodes are availab
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 现在让我获取对应的 runbook 来参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在我已经获取了完整的诊断信息。以下是分析结果。

---

## 集群异常定位分析

### 全局概览
- **节点**: 3 个节点（master、node1、node2），全部 **Ready**，状态正常 ✅
- **正常 Pod**: 59 个 Running，正常运行
- **异常 Pod**: **1 个** Pending

---

### 异常 Pod 详情

| 字段 | 值 |
|------|-----|
| **Pod 名称** | `rc-pending-insufficient-cpu` |
| **命名空间** | `aiops-e2e` |
| **状态** | `Pending` |
| **所属节点** | 未绑定（`<none>`） |
| **重启次数** | 0 |

### 调度失败原因
Events 中明确显示：
> **FailedScheduling**: `0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.`

意味着 **3 个节点 CPU 资源均不足**，且无法抢占已有 Pod 的资源。

---

### 归因定层

| 维度 | 值 |
|------|-----|
| **pod_status_keyword** | `Pending` |
| **pod_abnormal_type** | `PendingUnschedulable` |
| **status_category** | `scheduling` |
| **layer** | `L1` |
| **layer_name** | `调度资源不足` |
| **置信度** | `高` |

**abnormal_groups**: 1 个异常组 — `PendingUnschedulable`

**abnormal_pods**（1 个）:
- `aiops-e2e/rc-pending-insufficient-cpu` — Pending，因集群 CPU 资源不足无法调度

**key_entities**: 
- Pod: `aiops-e2e/rc-pending-insufficient-cpu`
- Nodes: `master`, `node1`, `node2`（全部 Ready 但 CPU 资源已耗尽）
- Scheduler: `default-scheduler`

**possible_scenarios**:
1. **集群 CPU 资源不足** — 最可能。3 个节点的 CPU 均已分配满，无法容纳新的 Pod request。Pod 的 QoS Class 为 `Burstable`，优先级不足以触发抢占。
2. **Pod 的 resource request 设置过大** — 如果 Pod 请求的 CPU 数量超过了任意单节点剩余容量，也会导致无法调度。

---

### 后续审查方向（交给 evidence 节点）
- 检查各节点的 CPU Allocatable 与已分配量，确认剩余容量
- 检查 Pod 的 `resources.requests.cpu` 具体数值
- 判断是否需要扩容节点、调整 Pod request 或降低其他 Workload 的资源占用
   ✅ [问题定位] 完成 (22.8s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '集群CPU资源不足', 'probability': '高', 'reason': '3个节点CPU均已分配满，无法容纳新Pod的resource request，且Pod的QoS Class为Burstable，优先级不足以触发抢占'}, {'scenario': 'Pod的resource request设置过大', 'probability': '中', 'reason': '如果Pod请求的CPU数量超过任意单节点剩余容量，也会导致无法调度'}]
   entities=[{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}, {"type": "Scheduler", "name": "default-scheduler", "namespace": ""}]
   reasoning=集群中存在1个异常Pod (rc-pending-insufficient-cpu in aiops-e2e)，状态为Pending，事件显示FailedScheduling，原因为3个节点CPU资源均不足。3个节点全部Ready正常，59个Pod Running正常。归因为PendingUnschedulable调度资源不足，属于L1层调度问题。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "调度资源不足", "confidence": 0.95, "reasoning": "集群中存在1个异常Pod (rc-pending-insufficient-cpu in aiops-e2e)，状态为Pending，事件显示FailedScheduling，原因为3个节点CPU资源均不足。3个节点全部Ready正常，59个Pod Running正常。归因为PendingUnschedulable调度资源不足，属于L1层调度问题。", "abnormal_pods": [{"name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}, {"type": "Scheduler", "name": "default-scheduler", "namespace": ""}], "possible_scenarios": [{"scenario": "集群CPU资源不足", "probability": "高", "reason": "3个节点CPU均已分配满，无法容纳新Pod的resource request，且Pod的QoS Class为Burstable，优先级不足以触发抢占"}, {"scenario": "Pod的resource request设置过大", "probability": "中", "reason": "如果Pod请求的CPU数量超过任意单节点剩余容量，也会导致无法调度"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-insufficient-cpu                         0/1     Pending     0              31m     <none>           <none>   <none>           <none>            app=rc-pending-insufficient-cpu,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我将按照既有 evidence_plan 执行真实环境工具采证。先执行前两个关键工具，它们是独立的可以并行执行。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  31m                default-scheduler  0/3 nodes are availab
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:59:10Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizer
   💭 [证据链采集] Pod describe 和 get yaml 已获取。现在并行获取节点资源信息和命名空间事件。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "    allocatable:\n      cpu: \"12\"\n      ephemeral-storage: \"568259694471\"\n      hugepages-1Gi: \"0\"\n      hugepages-2Mi: \"0\"\n      memory: 32758084Ki\n      pod
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
31m                 Warning   FailedScheduling   Pod/rc-pending-insufficient-cpu   0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No pree
   💭 [证据链采集] 很好，已经获取了节点的 capacity/allocatable。现在需要确认各节点的 CPU 实际分配情况，验证"3 Insufficient cpu"是否确实成立。让我查一下 Pod 的 resource requests（从 yaml 未看到 requests 设置）和各节点实际已分配 CPU 情况。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"node":"master"},"value":[1779348656.880,"12"]},{"metric":{"node":"node1"},"value":[1779348656.880,"12"]},{"metric":{"node":"node
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "      kubernetes.io/hostname: master\n      kubernetes.io/os: linux\n      metax-tech.com/gpu.installed: \"false\"\n      node-role.kubernetes.io/control-plane: \"\"\n    
   💭 [证据链采集] 现在让我查一下 Pod 的 resource requests 具体值（从 yaml 摘要未显示 resources 字段），以及各节点的 CPU 分配情况。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"node":"node2"},"value":[1779348659.850,"1.7750000000000001"]},{"metric":{"node":"master"},"value":[1779348659.850,"5.61"]},{"met
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "    resources:\n      requests:\n        cpu: 100k\n        memory: 64Mi\n    terminationMessagePath: /dev/termination-log\n    terminationMessagePolicy: File\n    volumeM
   💭 [证据链采集] 等等，我注意到 Pod 的 requests 是 `cpu: 100k`——这应该是测试用的大数值！让我确认一下。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"node":"node2"},"value":[1779348663.226,"1.7750000000000001"]},{"metric":{"node":"master"},"value":[1779348663.226,"5.61"]},{"met
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "      {\"apiVersion\":\"v1\",\"kind\":\"Pod\",\"metadata\":{\"annotations\":{\"aiops.e2e/runbook\":\"pod-pending-unschedulable.md\"},\"labels\":{\"app\":\"rc-pending-insuf
   💭 [证据链采集] 现在真相大白了！让我再确认一下完整信息。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "=== 各节点 allocatable CPU ===\nmaster: allocatable.cpu=12, capacity.cpu=12\nnode1: allocatable.cpu=12, capacity.cpu=12\nnode2: allocatable.cpu=12, capacity.cpu=12\n\n=== 各节点
   💭 [证据链采集] 让我确认一下 "100k" 的含义——这在 K8s 中表示 100000 个 CPU core，远超每个节点 12 个 CPU 的容量。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "100k CPU 含义: 100 * 1000 = 100000 CPU cores\n每个节点只有 12 个 allocatable CPU core\n所以 3 个节点都无法满足 100000 CPU 的请求\n\n=== Pod resource requests 分析 ===\n{\n  \"name\": \"rc-pending
   💭 [证据链采集] 所有关键证据已采集完毕。以下是结论：

---

## 证据采集结论

### 已采集证据（4 项）

1. **Pod Events（critical ✅）** — `kubectl describe pod` 确认：Pod `rc-pending-insufficient-cpu` 当前 STATUS=Pending，调度器持续报 `FailedScheduling`，原文：`0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.`（初始 31m 前，最近 96s 前）

2. **Pod YAML 资源请求（critical ✅）** — Pod 的 resource requests 为 `cpu: 100k`（即 **100,000 个 CPU core**），`memory: 64Mi`。`100k` 在 Kubernetes 中表示 `100 * 1000 = 100000 millicores`，即 100000 个 CPU 核心。

3. **各节点 CPU 容量（critical ✅）** — 3 个节点（master/node1/node2）的 `allocatable.cpu` 均为 12，`capacity.cpu` 均为 12。每个节点最多只能分配 12 个 CPU core，远不及 Pod 请求的 100,000 个。

4. **命名空间事件（important ✅）** — 仅有 FailedScheduling 事件，无其他异常事件。

### 冲突/负向证据
- 无冲突证据，所有工具结果与上游信号完全一致。

### 根因判定
**Pod `rc-pending-insufficient-cpu` 因 `resources.requests.cpu: 100k`（10 万个 CPU）设置远超集群任意节点容量（12 CPU），导致 3 个节点全部 `Insufficient cpu`，始终无法调度。** 这是一个典型的 Pod resource request 配置错误场景。
   ✅ [证据链采集] 完成 (38.7s)
   📤 → 下游数据: evidence_items=7/8
   evidence_analysis={"evidence_plan":[{"id":"e1-pod-describe","description":"Describe the pending pod rc-pending-insufficient-cpu to confirm FailedScheduling events and resource constraints","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-pending-insufficient-cpu","tool_args":{"kind":"pod","name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e","resource_type":"pod","resource_name":"rc-pending-insufficient-cpu"},"purpose":"Confirm current FailedScheduling events with Insufficient cpu reason from real environment","evidence_type":"pod_status_and_events","target_scope":"pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2-pod-yaml","description":"Get pod YAML to check resource requests, nodeSelector, affinity, tolerations","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod -n aiops-e2e rc-pending-insufficient-cpu -o yaml","tool_args":{"kind":"pod","name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e","resource_type":"pod","resource_name":"rc-pending-insufficient-cpu"},"purpose":"Check resource requests, nodeSelector, affinity rules, tolerations that could affect scheduling","evidence_type":"pod_spec","target_scope":"pod","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3-node-resources","description":"Get node resource allocation to verify CPU capacity/allocatable and current usage","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get nodes -o yaml","tool_args":{"resource_type":"nodes"},"purpose":"Verify each node's CPU capacity, allocatable, and conditions to confirm the Insufficient cpu claim","evidence_type":"node_resources","target_scope":"cluster","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e4-events-namespace","description":"Get events in aiops-e2e namespace for additional context","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e","tool_args":{"namespace":"aiops-e2e"},"purpose":"Look for any additional scheduling events or warnings in the namespace","evidence_type":"namespace_events","target_scope":"namespace","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  31m                default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  96s (x6 over 26m)  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nName:             rc-pending-insufficient-cpu\nLabels:           app=rc-pending-insufficient-cpu\nPod 关键区块:\nQoS Class: Burstable\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-26zhx:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  31m                default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  96s (x6 over 26m)  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:59:10Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-insufficient-cpu, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nvolumes:\n- {\"name\": \"kube-api-access-26zhx\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"    allocatable:\\n      cpu: \\\"12\\\"\\n      ephemeral-storage: \\\"568259694471\\\"\\n      hugepages-1Gi: \\\"0\\\"\\n      hugepages-2Mi: \\\"0\\\"\\n      memory: 32758084Ki\\n      pods: \\\"110\\\"\\n    capacity:\\n      cpu: \\\"12\\\"\\n      ephemeral-storage: 616601232Ki\\n      hugepages-1Gi: \\\"0\\\"\\n      hugepages-2Mi: \\\"0\\\"\\n      memory: 32860484Ki\\n      pods: \\\"110\\\"\\n    conditions:\\n    - lastHeartbeatTime: \\\"2026-05-06T01:29:41Z\\\"\\n      lastTransitionTime: \\\"2026-05-06T01:29:41Z\\\"\\n      message: Calico is running on this node\\n      reason: CalicoIsUp\\n      status: \\\"False\\\"\\n      type: NetworkUnavailable\\n    - lastHeartbeatTime: \\\"2026-05-21T07:29:47Z\\\"\\n      lastTransitionTime: \\\"2026-03-26T06:29:35Z\\\"\\n      message: kubelet has sufficient memory available\\n      reason: KubeletHasSufficientMemory\\n      status: \\\"False\\\"\\n      type: MemoryPressure\\n    - lastHeartbeatTime: \\\"2026-05-21T07:29:47Z\\\"\\n      lastTransitionTime: \\\"2026-04-27T06:40:37Z\\\"\\n      message: kubelet has no disk pressure\\n      reason: KubeletHasNoDiskPressure\\n      status: \\\"False\\\"\\n      type: DiskPressure\\n    - lastHeartbeatTime: \\\"2026-05-21T07:29:47Z\\\"\\n      lastTransitionTime: \\\"2026-03-26T06:29:35Z\\\"\\n--\\n    allocatable:\\n      cpu: \\\"12\\\"\\n      ephemeral-storage: \\\"187795058378\\\"\\n      hugepages-1Gi: \\\"0\\\"\\n      hugepages-2Mi: \\\"0\\\"\\n      memory: 32758076Ki\\n      pods: \\\"110\\\"\\n    capacity:\\n      cpu: \\\"12\\\"\\n      ephemeral-storage: 203770680Ki\\n      hugepages-1Gi: \\\"0\\\"\\n      hugepages-2Mi: \\\"0\\\"\\n      memory: 32860476Ki\\n      pods: \\\"110\\\"\\n    conditions:\\n    - lastHeartbeatTime: \\\"2026-05-06T01:29:35Z\\\"\\n      lastTransitionTime: \\\"2026-05-06T01:29:35Z\\\"\\n      message: Calico is running on this node\\n      reason: CalicoIsUp\\n      status: \\\"False\\\"\\n      type: NetworkUnavailable\\n    - lastHeartbeatTime: \\\"2026-05-21T07:25:52Z\\\"\\n      lastTransitionTime: \\\"2026-05-12T05:53:42Z\\\"\\n      message: kubelet has sufficient memory available\\n      reason: KubeletHasSufficientMemory\\n      status: \\\"False\\\"\\n      type: MemoryPressure\\n    - lastHeartbeatTime: \\\"2026-05-21T07:25:52Z\\\"\\n      lastTransitionTime: \\\"2026-05-12T05:53:42Z\\\"\\n      message: kubelet has no disk pressure\\n      reason: KubeletHasNoDiskPressure\\n      status: \\\"False\\\"\\n      type: DiskPressure\\n    - lastHeartbeatTime: \\\"2026-05-21T07:25:52Z\\\"\\n      lastTransitionTime: \\\"2026-05-12T05:53:42Z\\\"\\n--\\n    allocatable:\\n      cpu: \\\"12\\\"\\n      ephemeral-storage: \\\"187795058378\\\"\\n      hugepages-1Gi: \\\"0\\\"\\n      hugepages-2Mi: \\\"0\\\"\\n      memory: 32758080Ki\\n      pods: \\\"110\\\"\\n    capacity:\\n      cpu: \\\"12\\\"\\n      ephemeral-storage: 203770680Ki\\n      hugepages-1Gi: \\\"0\\\"\\n      hugepages-2Mi: \\\"0\\\"\\n      memory: 32860480Ki\\n      pods: \\\"110\\\"\\n    conditions:\\n    - lastHeartbeatTime: \\\"2026-05-06T01:29:38Z\\\"\\n      lastTransitionTime: \\\"2026-05-06T01:29:38Z\\\"\\n      message: Calico is running on this node\\n      reason: CalicoIsUp\\n      status: \\\"False\\\"\\n      type: NetworkUnavailable\\n    - lastHeartbeatTime: \\\"2026-05-21T07:30:19Z\\\"\\n      lastTransitionTime: \\\"2026-04-27T08:31:58Z\\\"\\n      message: kubelet has sufficient memory available\\n      reason: KubeletHasSufficientMemory\\n      status: \\\"False\\\"\\n      type: MemoryPressure\\n    - lastHeartbeatTime: \\\"2026-05-21T07:30:19Z\\\"\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/003-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/003-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/003-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n31m                 Warning   FailedScheduling   Pod/rc-pending-insufficient-cpu   0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n99s (x6 over 26m)   Warning   FailedScheduling   Pod/rc-pending-insufficient-cpu   0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/004-evidence-kubectl_events.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"node\":\"master\"},\"value\":[1779348656.880,\"12\"]},{\"metric\":{\"node\":\"node1\"},\"value\":[1779348656.880,\"12\"]},{\"metric\":{\"node\":\"node2\"},\"value\":[1779348656.880,\"12\"]}]}}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/005-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/005-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/005-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"      kubernetes.io/hostname: master\\n      kubernetes.io/os: linux\\n      metax-tech.com/gpu.installed: \\\"false\\\"\\n      node-role.kubernetes.io/control-plane: \\\"\\\"\\n      node.kubernetes.io/exclude-from-external-load-balancers: \\\"\\\"\\n    name: master\\n    resourceVersion: \\\"52570843\\\"\\n    uid: 0d3a4b73-0869-45de-a554-4646a6dc964f\\n  spec: {}\\n  status:\\n    addresses:\\n--\\n      kubernetes.io/hostname: node1\\n      kubernetes.io/os: linux\\n      metax-tech.com/gpu.installed: \\\"false\\\"\\n    name: node1\\n    resourceVersion: \\\"52569692\\\"\\n    uid: d1c0ae37-0829-4d35-abbb-f6649e35eb40\\n  spec: {}\\n  status:\\n    addresses:\\n--\\n      kubernetes.io/hostname: node2\\n      kubernetes.io/os: linux\\n      metax-tech.com/gpu.installed: \\\"false\\\"\\n    name: node2\\n    resourceVersion: \\\"52571002\\\"\\n    uid: 3ba54e76-a605-43f6-85aa-5587fa987ec5\\n  spec: {}\\n  status:\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/006-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/006-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/006-evidence-run_bash_command.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"node\":\"node2\"},\"value\":[1779348659.850,\"1.7750000000000001\"]},{\"metric\":{\"node\":\"master\"},\"value\":[1779348659.850,\"5.61\"]},{\"metric\":{\"node\":\"node1\"},\"value\":[1779348659.850,\"0.85\"]}]}}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/007-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/007-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/007-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"    resources:\\n      requests:\\n        cpu: 100k\\n        memory: 64Mi\\n    terminationMessagePath: /dev/termination-log\\n    terminationMessagePolicy: File\\n    volumeMounts:\\n    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount\\n      name: kube-api-access-26zhx\\n      readOnly: true\\n  dnsPolicy: ClusterFirst\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/008-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/008-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/008-evidence-run_bash_command.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"node\":\"node2\"},\"value\":[1779348663.226,\"1.7750000000000001\"]},{\"metric\":{\"node\":\"master\"},\"value\":[1779348663.226,\"5.61\"]},{\"metric\":{\"node\":\"node1\"},\"value\":[1779348663.226,\"0.85\"]},{\"metric\":{},\"value\":[1779348663.226,\"100000\"]}]}}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/009-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/009-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/009-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"      {\\\"apiVersion\\\":\\\"v1\\\",\\\"kind\\\":\\\"Pod\\\",\\\"metadata\\\":{\\\"annotations\\\":{\\\"aiops.e2e/runbook\\\":\\\"pod-pending-unschedulable.md\\\"},\\\"labels\\\":{\\\"app\\\":\\\"rc-pending-insufficient-cpu\\\",\\\"pod_abnormal_type\\\":\\\"PendingUnschedulable\\\",\\\"rootcause-e2e\\\":\\\"true\\\"},\\\"name\\\":\\\"rc-pending-insufficient-cpu\\\",\\\"namespace\\\":\\\"aiops-e2e\\\"},\\\"spec\\\":{\\\"containers\\\":[{\\\"command\\\":[\\\"sh\\\",\\\"-c\\\",\\\"sleep 3600\\\"],\\\"image\\\":\\\"busybox:1.36\\\",\\\"imagePullPolicy\\\":\\\"Never\\\",\\\"name\\\":\\\"app\\\",\\\"resources\\\":{\\\"requests\\\":{\\\"cpu\\\":\\\"100000\\\",\\\"memory\\\":\\\"64Mi\\\"}}}]}}\\n    app: rc-pending-insufficient-cpu\\n  name: rc-pending-insufficient-cpu\\n        cpu: 100k\\n        memory: 64Mi\\n    message: '0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/010-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/010-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/010-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"=== 各节点 allocatable CPU ===\\nmaster: allocatable.cpu=12, capacity.cpu=12\\nnode1: allocatable.cpu=12, capacity.cpu=12\\nnode2: allocatable.cpu=12, capacity.cpu=12\\n\\n=== 各节点已分配 CPU (requests) ===\\n{\\n  \\\"node\\\": \\\"master\\\",\\n  \\\"total_cpu_request\\\": 1613\\n}\\n{\\n  \\\"node\\\": \\\"node1\\\",\\n  \\\"total_cpu_request\\\": 850\\n}\\n{\\n  \\\"node\\\": \\\"node2\\\",\\n  \\\"total_cpu_request\\\": 776\\n}\\n\\n=== Pod requests 原文 ===\\n{\\n  \\\"requests\\\": {\\n    \\\"cpu\\\": \\\"100k\\\",\\n    \\\"memory\\\": \\\"64Mi\\\"\\n  }\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/011-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/011-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/011-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"100k CPU 含义: 100 * 1000 = 100000 CPU cores\\n每个节点只有 12 个 allocatable CPU core\\n所以 3 个节点都无法满足 100000 CPU 的请求\\n\\n=== Pod resource requests 分析 ===\\n{\\n  \\\"name\\\": \\\"rc-pending-insufficient-cpu\\\",\\n  \\\"cpu_request\\\": \\\"100k\\\",\\n  \\\"memory_request\\\": \\\"64Mi\\\"\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/012-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/012-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6782911dc88846e5/tools/012-evidence-run_bash_command.summary.txt"}],"llm_analysis":"所有关键证据已采集完毕。以下是结论：\n\n---\n\n## 证据采集结论\n\n### 已采集证据（4 项）\n\n1. **Pod Events（critical ✅）** — `kubectl describe pod` 确认：Pod `rc-pending-insufficient-cpu` 当前 STATUS=Pending，调度器持续报 `FailedScheduling`，原文：`0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.`（初始 31m 前，最近 96s 前）\n\n2. **Pod YAML 资源请求（critical ✅）** — Pod 的 resource requests 为 `cpu: 100k`（即 **100,000 个 CPU core**），`memory: 64Mi`。`100k` 在 Kubernetes 中表示 `100 * 1000 = 100000 millicores`，即 100000 个 CPU 核心。\n\n3. **各节点 CPU 容量（critical ✅）** — 3 个节点（master/node1/node2）的 `allocatable.cpu` 均为 12，`capacity.cpu` 均为 12。每个节点最多只能分配 12 个 CPU core，远不及 Pod 请求的 100,000 个。\n\n4. **命名空间事件（important ✅）** — 仅有 FailedScheduling 事件，无其他异常事件。\n\n### 冲突/负向证据\n- 无冲突证据，所有工具结果与上游信号完全一致。\n\n### 根因判定\n**Pod `rc-pending-insufficient-cpu` 因 `resources.requests.cpu: 100k`（10 万个 CPU）设置远超集群任意节点容量（12 CPU），导致 3 个节点全部 `Insufficient cpu`，始终无法调度。** 这是一个典型的 Pod resource request 配置错误场景。","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 7/8 项，完整度 88%；实际执行工具 16 个，匹配计划 3 个，未规划证据 13 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":8,"environment_evidence_collected":7,"environment_evidence_completeness":0.875,"executed_tool_count":16,"matched_tool_count":3,"unplanned_tool_count":13,"evidence_inventory":[{"id":"e1-pod-describe","description":"Describe the pending pod rc-pending-insufficient-cpu to confirm FailedScheduling events and resource constraints","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-pending-insufficient-cpu","purpose":"Confirm current FailedScheduling events with Insufficient cpu reason from real environment","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-pod-yaml","description":"Get pod YAML to check resource requests, nodeSelector, affinity, tolerations","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod -n aiops-e2e rc-pending-insufficient-cpu -o yaml","purpose":"Check resource requests, nodeSelector, affinity rules, tolerations that could affect scheduling","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3-node-resources","description":"Get node resource allocation to verify CPU capacity/allocatable and current usage","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get nodes -o yaml","purpose":"Verify each node's CPU capacity, allocatable, and conditions to confirm the Insufficient cpu claim","collected":false,"source":"planned","outcome":"unknown"},{"id":"e4-events-namespace","description":"Get events in aiops-e2e namespace for additional context","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e","purpose":"Look for any additional scheduling events or warnings in the namespace","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e3-node-resources(Get node resource allocation to verify CPU capacity/allocatable and current usage): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 88%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1-pod-describe | critical | ✅ | kubectl_describe | Describe the pending pod rc-pending-insuffici... | `kubectl describe pod -n aiops-e2e rc-pending-insufficient-cpu` |
   | e2-pod-yaml | critical | ✅ | kubectl_get_yaml | Get pod YAML to check resource requests, node... | `kubectl get pod -n aiops-e2e rc-pending-insufficient-cpu -o yaml` |
   | e3-node-resou... | critical | ❌ | kubectl_get_yaml | Get node resource allocation to verify CPU ca... | `kubectl get nodes -o yaml` |
   | e4-events-nam... | important | ✅ | kubectl_events | Get events in aiops-e2e namespace for additio... | `kubectl get events -n aiops-e2e` |

   ⚠️ 未采集原因:
   - e3-node-resources(Get node resource allocation to verify CPU capacity/allocatable and current usage): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (31.3s)
   📤 → 下游数据: root_cause=Pod rc-pending-insufficient-cpu (namespace: aiops-e2e) 因 resources.requests.cpu 配置错误（设为 100k，即 100000 millicores）导致无法调度。集群 3 个节点（master/node1/node2）的 allocatable.cpu 均为 12，capacity.cpu 均为 12，均远小于 Pod 请求的 100000 个 CPU core。kubectl describe 显示调度器持续 31 分钟报 FailedScheduling: "0/3 nodes are available: 3 Insufficient cpu"，且无抢占受害者。Pod 的 QoS Class 为 Burstable，不存在 nodeSelector/affinity/taint 约束问题。集群其他 59 个 Pod 均正常运行，3 个节点均 Ready 正常，排除集群健康问题。这是一个典型的 Pod resource request 配置错误场景。
   confidence=98%
   causal_chain={"root_cause": "Pod rc-pending-insufficient-cpu 的 resources.requests.cpu 被设置为 100k（100000 millicores），远超集群中任意节点的 CPU 容量（每个节点仅 12 cores），导致调度器无法在任何节点上分配 CPU 资源", "propagation": "Pod YAML 中 resources.requests.cpu: 100k → kube-scheduler 尝试将 Pod 调度到 3 个节点（master/node1/node2）中的任意一个 → 每个节点 allocatable.cpu 均为 12，不满足 100k 请求 → 调度器标记该 Pod 为 Unschedulable → 持续产生 FailedScheduling Event → Pod 停留在 Pending 状态", "direct_cause": "Pod 的 CPU request（100k）超过所有节点的可分配 CPU 容量（12），调度器无法找到满足资源需求的节点", "manifestation": "Pod rc-pending-insufficient-cpu 在 aiops-e2e 命名空间中持续 Pending 31 分钟，kubectl 显示 STATUS=Pending、NODE=<none>，kubectl describe 显示 FailedScheduling 事件报 '3 Insufficient cpu'，且无抢占受害者"}
   rca_analysis={"phenomenon": "集群 aiops-e2e 命名空间中 Pod rc-pending-insufficient-cpu 当前状态为 Pending，调度器持续报 FailedScheduling 事件，3 个节点全部 Ready 正常但 CPU 均不足", "evidence_inventory": [{"id": "e1-pod-describe", "source": "kubectl_describe", "content": "Pod rc-pending-insufficient-cpu 状态 Pending，Events 显示 FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu，无抢占受害者", "reliability": "高"}, {"id": "e2-pod-yaml", "source": "kubectl_get_yaml", "content": "Pod specs: resources.requests.cpu = 100k (100000 millicores), memory = 64Mi; nodeName=None; phase=Pending; 无 nodeSelector/affinity", "reliability": "高"}, {"id": "e3-node-capacity", "source": "run_bash_command / kubectl_get_node", "content": "3 个节点 (master, node1, node2) 的 allocatable.cpu 均为 12，capacity.cpu 均为 12", "reliability": "高"}, {"id": "e4-node-usage", "source": "execute_prometheus_instant_query", "content": "节点 CPU 实际使用量: master=5.61, node1=0.85, node2=1.775 (cores); Pod request 100k 远超任意节点容量", "reliability": "高"}, {"id": "e5-events-namespace", "source": "kubectl_events", "content": "aiops-e2e 命名空间仅有 FailedScheduling 事件指向该 Pod，无其他异常事件", "reliability": "高"}, {"id": "e6-layer-summary", "source": "layer_verified", "content": "集群 59 Pod Running，1 Pod Pending，3 Node Ready 正常", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1-pod-describe", "raw_data": "Warning FailedScheduling 31m default-scheduler 0/3 nodes are available: 3 Insufficient cpu... Warning FailedScheduling 96s (x6 over 26m) ... 3 Insufficient cpu", "interpretation": "调度器持续 31 分钟无法调度该 Pod，明确报 CPU 不足且无抢占受害者，排除了临时性抖动"}, {"evidence_id": "e2-pod-yaml", "raw_data": "resources: requests: cpu: 100k, memory: 64Mi", "interpretation": "Pod 请求 100k CPU（即 100000 millicores = 100 个 CPU core），这是极不合理的配置数值"}, {"evidence_id": "e3-node-capacity", "raw_data": "allocatable.cpu: 12 (所有3节点); capacity.cpu: 12", "interpretation": "集群中每个节点最多只有 12 个 CPU core 可分配，远不能满足 100k 的请求"}, {"evidence_id": "e4-node-usage", "raw_data": "master=5.61, node1=0.85, node2=1.775 (cores); Pod request=100000 (cores)", "interpretation": "即使 Pod 请求合理，按实际使用量看节点尚有剩余 CPU，但调度器检查的是 resource request 而非实际使用量；Pod 请求 100k cores 远超任何节点容量"}, {"evidence_id": "e5-events-namespace", "raw_data": "31m Warning FailedScheduling Pod/rc-pending-insufficient-cpu... 99s (x6 over 26m) Warning FailedScheduling", "interpretation": "无其他异常事件，所有问题仅集中在该 Pod 的调度失败上"}, {"evidence_id": "e6-layer-summary", "raw_data": "63 Pods total: 59 Running, 1 Pending; 3 Nodes Ready", "interpretation": "集群其余部分健康，所有其他 Pod 正常运行，节点无异常"}], "causal_chain": {"root_cause": "Pod rc-pending-insufficient-cpu 的 resources.requests.cpu 被设置为 100k（100000 millicores），远超集群中任意节点的 CPU 容量（每个节点仅 12 cores），导致调度器无法在任何节点上分配 CPU 资源", "propagation": "Pod YAML 中 resources.requests.cpu: 100k → kube-scheduler 尝试将 Pod 调度到 3 个节点（master/node1/node2）中的任意一个 → 每个节点 allocatable.cpu 均为 12，不满足 100k 请求 → 调度器标记该 Pod 为 Unschedulable → 持续产生 FailedScheduling Event → Pod 停留在 Pending 状态", "direct_cause": "Pod 的 CPU request（100k）超过所有节点的可分配 CPU 容量（12），调度器无法找到满足资源需求的节点", "manifestation": "Pod rc-pending-insufficient-cpu 在 aiops-e2e 命名空间中持续 Pending 31 分钟，kubectl 显示 STATUS=Pending、NODE=<none>，kubectl describe 显示 FailedScheduling 事件报 '3 Insufficient cpu'，且无抢占受害者"}, "root_cause": "Pod rc-pending-insufficient-cpu (namespace: aiops-e2e) 因 resources.requests.cpu 配置错误（设为 100k，即 100000 millicores）导致无法调度。集群 3 个节点（master/node1/node2）的 allocatable.cpu 均为 12，capacity.cpu 均为 12，均远小于 Pod 请求的 100000 个 CPU core。kubectl describe 显示调度器持续 31 分钟报 FailedScheduling: \"0/3 nodes are available: 3 Insufficient cpu\"，且无抢占受害者。Pod 的 QoS Class 为 Burstable，不存在 nodeSelector/affinity/taint 约束问题。集群其他 59 个 Pod 均正常运行，3 个节点均 Ready 正常，排除集群健康问题。这是一个典型的 Pod resource request 配置错误场景。", "root_cause_summary": "Pod rc-pending-insufficient-cpu (namespace: aiops-e2e) 因 resources.requests.cpu 配置错误（设为 100k，即 100000 millicores）导致无法调度。集群 3 个节点（master/node1/node2）的 allocatable.cpu 均为 12，capacity.cpu 均为 12，均远小于 Pod 请求的 100000 个 CPU core。kubectl describe 显示调度器持续 31 分钟报 FailedScheduling: \"0/3 nodes are available: 3 Insufficient cpu\"，且无抢占受害者。Pod 的 QoS Class 为 Burstable，不存在 nodeSelector/affinity/taint 约束问题。集群其他 59 个 Pod 均正常运行，3 个节点均 Ready 正常，排除集群健康问题。这是一个典型的 Pod resource request 配置错误场景。", "confidence": 0.98, "confidence_reason": "有直接证据：kubectl_describe 确认 FailedScheduling 事件 + kubectl_get_yaml 确认 resources.requests.cpu: 100k + 节点 allocatable.cpu 均为 12 的容量数据 + Prometheus 查询验证节点实际 CPU 用量 + 无其他约束（nodeSelector/affinity/taint）干扰。因果链完整清晰，置信度极高。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "节点 CPU 资源真实耗尽（实际使用量打满）", "probability": "low", "reason": "Prometheus 查询显示 master=5.61, node1=0.85, node2=1.775 cores，均远未达到 12 cores 容量，实际资源充足"}, {"cause": "nodeSelector/affinity 约束导致无可用节点", "probability": "low", "reason": "Pod YAML 显示 Node-Selectors: <none>，无 affinity 配置，不存在约束限制"}, {"cause": "节点 taint 未容忍", "probability": "low", "reason": "Pod 已有默认 tolerations（not-ready:NoExecute），且 FailedScheduling 未报 taint 相关错误"}, {"cause": "PVC 未绑定或卷问题", "probability": "low", "reason": "Pod 仅使用 kube-api-access 默认投影卷，无 PVC/PV 依赖，FailedScheduling 也未报卷相关错误"}], "limitations": "节点 allocatable.cpu 数据来自 kubectl get node 输出确认，Prometheus 验证了实际使用量。缺失证据项（e3-node-resources）已被 run_bash_command 和 Prometheus 查询补全。未采集单个 Pod 的详细 resource request 原始 YAML 全文（但关键字段 resources.requests.cpu: 100k 已通过 run_bash_command 第 8 条证据确认）。100k 是一个极不合理的 CPU 请求值，极可能是配置错误（如将 100m 误写为 100k），但根本原因分析本身不受影响。", "llm_raw_analysis": "## 证据清点\n共采集 10 项工具输出，其中关键证据 6 项：\n1. kubectl_describe → FailedScheduling 事件（CPU 不足）\n2. kubectl_get_yaml → Pod 资源请求 cpu: 100k\n3. run_bash_command → 节点 allocatable.cpu = 12\n4. Prometheus 查询 → 节点实际 CPU 用量（master=5.61, node1=0.85, node2=1.775）\n5. kubectl_events → 仅有 FailedScheduling 事件\n6. 上游 layer 验证 → 59 Pod Running, 3 Node Ready\n\n## 逐条分析\n- e1: 调度器明确报 CPU 不足，持续 31 分钟，排除临时抖动\n- e2: Pod 请求 100k CPU = 100000 个 CPU core，极不合理\n- e3: 每个节点最多 12 CPU core，远小于 100k\n- e4: 节点实际 CPU 用量很低（共 ~8.235 cores），并非真实资源耗尽\n-\n... 截断，原始 725 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-insufficient-cpu (namespace: aiops-e2e) 因 resources.requests.cpu 配置错误（设为 100k，即 100000 millicores）导致无法调度。集群 3 个节点（master/node1/node2）的 ...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod rc-pending-insufficient-cpu 的 resources.requests.cpu 被设置为 100k（100000 millicores），远超集群中任意节点的 CPU 容量（每个节点仅 12 cores），导致调度器无法在任何节点上分配 CPU 资源
     传导机制: Pod YAML 中 resources.requests.cpu: 100k → kube-scheduler 尝试将 Pod 调度到 3 个节点（master/node1/node2）中的任意一个 → 每个节点 allocatable.cpu 均为 12，不满足 100k 请求 → 调度器标记该 Pod 为 Unschedulable → 持续产生 FailedScheduling Event → Pod 停留在 Pending 状态
     最终表现: Pod rc-pending-insufficient-cpu 在 aiops-e2e 命名空间中持续 Pending 31 分钟，kubectl 显示 STATUS=Pending、NODE=<none>，kubectl describe 显示 FailedScheduling 事件报 '3 Insufficient cpu'，且无抢占受害者


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (24.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5444 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 56.8s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我现在为您分析集群状况。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **您的集群状态** | **整体健康，但有1个异常Pod**。集群59个Pod正常运行，3个节点全部Ready。 |
| **发现的问题** | 在 `aiops-e2e` 命名空间中，Pod `rc-pending-insufficient-cpu` 处于 **Pending** 状态，无法被调度。 |
| **Pod 异常状态** | `Pending` (PendingUnschedulable) |
| **兼容归因层** | L1 - 调度问题 |
| **问题分类** | `PendingUnschedulable` (资源不足) |
| **置信度** | **高 (98%)** |
| **证据完整度** | 3/4 (75%) |

---
## 🔍 现象描述

**您报告的问题**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| **异常 Pod** | `rc-pending-insufficient-cpu` |
| **命名空间** | `aiops-e2e` |
| **节点** | 全部3个节点（`master`, `node1`, `node2`）均无法调度此Pod |
| **核心错误** | `0/3 nodes are available: 3 Insufficient cpu.` |

---
## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe` | `Warning FailedScheduling 31m default-scheduler 0/3 nodes are available: 3 Insufficient cpu.` | Pod 因 CPU 资源不足无法调度 |
| 2 | Pod YAML 配置 | `kubectl get pod -o yaml` (通过 `run_bash_command`) | `resources.requests.cpu: 100k` | Pod 请求的 CPU 数量异常巨大（100,000 millicores） |
| 3 | 节点 CPU 容量 | `kubectl get node -o yaml` (通过 `run_bash_command`) | `allocatable.cpu: "12"` | 所有3个节点的可分配 CPU 均为 **12 cores** |
| 4 | 集群节点状态 | `kubectl get nodes` | `Status: Ready`; 3 nodes all Ready | 集群节点本身健康，无异常 |

### 证据关联分析
- **证据 #2 + #3 印证**：Pod 请求 **100,000 个 CPU core** (`100k`)，但集群中最大的节点也仅有 **12 个 allocatable CPU core**。这是一个显著的资源请求配置错误。
- **证据 #1 佐证**：调度器持续31分钟报错 `3 Insufficient cpu`，证实了资源不足的事实。

### 缺失证据（如有）
无。虽然计划采集节点资源失败，但通过 `run_bash_command` 和 Prometheus 查询已成功补全。

---
## 🎯 根因分析

### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                         │
│ Pod `rc-pending-insufficient-cpu` 的 `resources.requests.cpu` 配置为 `100k`      │
│ (即100,000 millicores)，这是一个不合理的数值。                                    │
│ 极可能是配置错误（例如：将 100m 误写为 100k）。                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                         │
│ Kube-Scheduler 尝试将 Pod 调度到集群中任意节点(master/node1/node2)                │
│ → 发现每个节点的 `allocatable.cpu` 只有 12，完全不满足 `100k` 的请求             │
│ → 调度器判定无可用节点，标记该 Pod 为 Unschedulable                              │
└──────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                         │
│ 调度器无法找到 CPU 容量大于 100k 的节点，持续产生 `FailedScheduling` 事件         │
│ (事件文本: "3 Insufficient cpu")                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                     │
│ Pod `rc-pending-insufficient-cpu` 状态为 `Pending`，持续约 31 分钟。              │
│ 集群其他 59 个 Pod 和 3 个节点均正常运行。                                       │
└──────────────────────────────────────────────────────────────────────────────────┘
```
### 根因结论

**结论**：根据证据 #1 (调度事件: `3 Insufficient cpu`)、证据 #2 (`resources.requests.cpu: 100k`) 和证据 #3 (节点 `allocatable.cpu: 12`)，
问题的根本原因是 **Pod `rc-pending-insufficient-cpu` 的 CPU 请求 (`100k`) 是一个极不合理的超大数值，远超集群中任何单个节点的 CPU 容量**，导致调度器无法调度。

**置信度**：高 (98%)
- ✅ `kubectl describe` 事件明确指向 CPU 资源不足。
- ✅ `kubectl get pod -o yaml` 直接确认了 `requests.cpu: 100k` 的异常配置。
- ✅ 节点资源数据确认集群最大 CPU 容量仅为 12 core，与 Pod 需求严重不匹配。

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [必须] 更正 Pod 的 CPU 请求值 (推荐)**
当前 `100k` 是错误配置，应立即修改为合理的数值。如果是测试用 Pod，建议直接删掉重建。

```bash
# 1. 删除这个配置错误的 Pod
kubectl delete pod rc-pending-insufficient-cpu -n aiops-e2e

# 2. 重建一个 CPU 请求合理的 Pod（示例使用 100m，即0.1核）
kubectl run rc-pending-insufficient-cpu --image=busybox:1.36 --restart=Never -n aiops-e2e --requests='cpu=100m,memory=64Mi' -- sh -c "sleep 3600"
```
*依据*：当前 `requests.cpu: 100k` 为配置错误。删除后重建一个配置合理的 Pod 是最高效的修复方式。

**2. [可选] 如果是 Deployment/StatefulSet，则直接编辑 YAML**
```bash
# 找到对应的控制器并编辑
kubectl edit deployment <deployment-name> -n aiops-e2e
# 将 spec.template.spec.containers[0].resources.requests.cpu 从 100k 改为 100m
```
*依据*：从根源上修正资源定义，避免 Pod 重建后再次出错。

### 后续优化
1. **准入控制**：建议在集群中配置 **ResourceQuota** 或 **LimitRange**，限制单个 Pod 的 CPU 请求上限，防止此类配置问题。
2. **配置审计**：建议检查 CI/CD 或应用部署流水线中的资源配置模板，确保 `requests.cpu` 的数值单位书写正确（`100m` vs `100k`）。

---
## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 检查 Pod 状态 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e` | `STATUS: Running` |
| 2. 检查调度事件 | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e \| grep -A5 Events` | 不再出现 `FailedScheduling` 事件 |
| 3. 确认 Pod 所在节点 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o wide` | `NODE` 列显示具体节点名称（非 `<none>`） |

---
## ⚠️ 注意事项
- **`100k` 的含义**：`requests.cpu: 100k` 意味着 Pod 请求 `100 * 1000 = 100,000` 个 CPU 核心。这通常是一个书写错误（例如误以为 `k` 是 millicores 的简写）。请检查您应用的配置文件，将 `100k` 修正为 `100m`（即0.1核）或其他合适的值。
- **此问题仅限于单个 Pod**：您集群的其余 59 个 Pod 和 3 个节点均运行正常，无需担心。

---

## 📊 性能统计

├─ 总耗时: 1.9m
├─ 问题定位: 22.8s (20%) ✅
├─ 证据链采集: 38.7s (33%) ✅
├─ 根因分析: 31.3s (27%) ✅
├─ 汇总总结: 24.0s (21%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 17 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 17 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
