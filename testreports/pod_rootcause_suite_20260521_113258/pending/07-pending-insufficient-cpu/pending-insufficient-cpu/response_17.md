======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 64106d4d79fa4e9f]

📍 [问题定位] 执行中...
   💭 [问题定位] 让我先全局扫描所有 Pod 的状态，了解集群的整体健康状况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 发现有一个异常 Pod。让我更详细地查看这个 Pending Pod 的情况。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-cpu   0/1     Pending   0          17m   <none>   <
   💭 [问题定位] 这个 Pod 处于 Pending 状态且没有绑定节点。让我查看它的详细信息，确认调度失败的原因。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  17m                  default-scheduler  0/3 nodes are avail
   💭 [问题定位] Pod 的 label 已经标记了 `pod_abnormal_type=PendingUnschedulable`，这个异常类型与 runbook 匹配。让我获取对应的 runbook 作为参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 好的，我已经拿到了所有需要的信息。现在让我执行诊断总结。

## 诊断分析

我通过全局 Pod 扫描发现集群中 **65 个 Pod** 中有 **1 个异常 Pod**，其余 59 个均处于 Running 正常状态。

---

### 当前异常概览

| 维度 | 内容 |
|------|------|
| **异常 Pod** | `rc-pending-insufficient-cpu`（aiops-e2e 命名空间） |
| **Pod 状态** | Pending（未绑定节点） |
| **异常类型** | `PendingUnschedulable`（调度失败） |
| **兼容层级** | **L1**（调度层问题） |
| **状态关键字** | `Pending` + `FailedScheduling` |

---

### 详细分析

**Pod**: `rc-pending-insufficient-cpu`（aiops-e2e）
- **STATUS**: Pending（17分钟），未绑定任何节点（NODE = \<none\>）
- **Events** 中的关键调度失败信息：
  ```
  FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu.
  preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.
  ```
- **根因非常明确**：集群中 **3 个节点全部 CPU 资源不足**（Insufficient cpu），没有节点能调度这个 Pod。抢占调度（preemption）也无法找到可驱逐的受害者 Pod。

---

### 分层映射

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **layer_name** | PendingUnschedulable — 调度失败 |
| **derived_layer** | L1 |
| **layers** | L1 |
| **status_category** | scheduling |
| **pod_status_keyword** | Pending |
| **pod_abnormal_type** | PendingUnschedulable |
| **confidence** | 高 |
| **key_entities** | Pod: `rc-pending-insufficient-cpu` (aiops-e2e) |
| **possible_scenarios** | 集群节点 CPU 资源全部耗尽，无法调度新的 Pod |

---

### 结论

集群整体健康度良好（59/65 Pod 正常运行），当前唯一的异常是 **一个用于 E2E 测试的 Pod 因集群 CPU 资源不足而无法调度**。这是一个 **L1 调度层问题**，根因是集群所有 3 个节点的 CPU 可分配资源已耗尽，无法满足该 Pod 的 CPU request。建议后续审查节点 CPU 使用率，确认是否需要扩容节点或调整现有 Pod 的资源限制。
   ✅ [问题定位] 完成 (23.6s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '集群节点 CPU 资源耗尽', 'probability': '高', 'reason': 'FailedScheduling 事件明确显示 0/3 nodes are available: 3 Insufficient cpu，所有节点均无法满足 Pod 的 CPU request'}]
   entities=[{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}]
   reasoning=集群中有唯一异常 Pod `rc-pending-insufficient-cpu`（aiops-e2e），状态为 Pending，Events 显示 FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu. 根因为集群所有3个节点 CPU 资源耗尽，导致调度器无法为该 Pod 分配节点。59/65 Pod 正常运行，整体健康度良好。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable — 调度失败", "confidence": 0.98, "reasoning": "集群中有唯一异常 Pod `rc-pending-insufficient-cpu`（aiops-e2e），状态为 Pending，Events 显示 FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu. 根因为集群所有3个节点 CPU 资源耗尽，导致调度器无法为该 Pod 分配节点。59/65 Pod 正常运行，整体健康度良好。", "abnormal_pods": [{"name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "集群节点 CPU 资源耗尽", "probability": "高", "reason": "FailedScheduling 事件明确显示 0/3 nodes are available: 3 Insufficient cpu，所有节点均无法满足 Pod 的 CPU request"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-insufficient-cpu                         0/1     Pending     0              17m     <none>           <none>   <none>           <none>            app=rc-pending-insufficient-cpu,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/64106d4d79fa4e9f/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/64106d4d79fa4e9f/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/64106d4d79fa4e9f/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 98%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 我将按既有 evidence_plan 执行工具调用，采集真实环境证据。先并行执行前三个独立调用。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"name\": \"master\",\n  \"cpu_capacity\": \"12\",\n  \"cpu_allocatable\": \"12\",\n  \"pods_capacity\": \"110\"\n}\n{\n  \"name\": \"node1\",\n  \"cpu_capacity\": \"
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:59:10Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizer
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  18m                 default-scheduler  0/3 nodes are availa
   💭 [证据链采集] 节点 CPU 容量都是 12 核（可分配也是 12），说明集群总 CPU 为 36 核。现在来检查 Pod 的 CPU request 以及各节点的实际 CPU 使用率。
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"node":"master"},"value":[1779347840.525,"2.2385303354406054"]},{"metric":{"node":"node1"},"value":[1779347840.525,"0.99493190670
   💭 [证据链采集] 再来确认一下 Pod spec 中 CPU request 的设置，看它请求了多少 CPU。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"requests\": {\n    \"cpu\": \"100k\",\n    \"memory\": \"64Mi\"\n  }\n}\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] 有意思！Pod 的 CPU request 是 `100k`（即 100000 核），这是一个明显非法的数值——远超过集群所有节点 12 核的容量。现在也检查一下各节点实际的 CPU 使用率与容量对比。
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"node":"master"},"value":[1779347846.631,"18.654419462005045"]},{"metric":{"node":"node1"},"value":[1779347846.631,"8.29109922256
   💭 [证据链采集] ## 证据采集结论

### 已采集证据

| 证据项 | 结果 |
|--------|------|
| **e1 - kubectl describe Pod** ✅ | FailedScheduling 事件确认：`0/3 nodes are available: 3 Insufficient cpu.`，所有 3 个节点均因 CPU 不足无法调度 |
| **e2 - Pod YAML spec** ✅ | Pod 的 CPU request 被设置为 **`100k`（100000 核）**，但每个节点仅有 12 核容量 |
| **e3 - 节点 CPU 容量** ✅ | 3 个节点（master/node1/node2），每节点 **12 核**，总计 36 核 |
| **e4 - Prometheus 节点 CPU 使用率** ✅ | master: **18.7%**、node1: **8.3%**、node2: **15.0%**，各节点 CPU 实际负载远未饱和 |

### 根因分析
Pod `rc-pending-insufficient-cpu` 的 CPU request 配置为 **`100k`（100000 核）**，这是一个明显异常的值（可能是配置笔误，将 `100m` 误写为 `100k`）。集群中每个节点仅有 12 核容量，因此调度器无法在任何节点上满足这个 CPU 请求。

### 冲突证据
- **"集群节点 CPU 资源耗尽"假说不成立**：Prometheus 数据显示各节点实际 CPU 使用率仅 **8%~19%**，资源非常充裕。真正的根因是 Pod 自身的 CPU request 配置错误（`100k`），而不是集群资源不足。

### 建议修复
将 Pod/Deployment 中 CPU request 从 `100k` 修正为合理的值（如 `100m`）。
   ✅ [证据链采集] 完成 (39.0s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"描述 Pod rc-pending-insufficient-cpu 的完整状态、事件和调度详情","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-pending-insufficient-cpu","tool_args":{"kind":"Pod","name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e"},"purpose":"验证 FailedScheduling 事件原文和 Pod 配置","evidence_type":"pod_status_and_events","target_scope":"abnormal_pods","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod 的完整 YAML 以检查资源 requests/limits、nodeSelector、affinity、tolerations 等调度配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod -n aiops-e2e rc-pending-insufficient-cpu -o yaml","tool_args":{"kind":"Pod","name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e"},"purpose":"检查 Pod spec 中 CPU request 和调度约束","evidence_type":"pod_spec_config","target_scope":"abnormal_pods","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"查询集群节点 CPU 容量和可分配量，验证 CPU 是否真正耗尽","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o json | jq -r '.items[] | {name: .metadata.name, cpu_capacity: .status.capacity.cpu, cpu_allocatable: .status.allocatable.cpu, pods_capacity: .status.capacity.pods}'","tool_args":{},"purpose":"验证所有节点的 CPU 容量和可分配量","evidence_type":"node_capacity","target_scope":"cluster_infra","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"查询集群中所有节点的 CPU 实际使用率（Prometheus）","level":"important","tool":"execute_prometheus_instant_query","command":"sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate) by (node)","tool_args":{"query":"sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate) by (node)"},"purpose":"验证各节点的实际 CPU 使用率是否接近或达到容量上限","evidence_type":"node_cpu_usage","target_scope":"cluster_infra","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"name\\\": \\\"master\\\",\\n  \\\"cpu_capacity\\\": \\\"12\\\",\\n  \\\"cpu_allocatable\\\": \\\"12\\\",\\n  \\\"pods_capacity\\\": \\\"110\\\"\\n}\\n{\\n  \\\"name\\\": \\\"node1\\\",\\n  \\\"cpu_capacity\\\": \\\"12\\\",\\n  \\\"cpu_allocatable\\\": \\\"12\\\",\\n  \\\"pods_capacity\\\": \\\"110\\\"\\n}\\n{\\n  \\\"name\\\": \\\"node2\\\",\\n  \\\"cpu_capacity\\\": \\\"12\\\",\\n  \\\"cpu_allocatable\\\": \\\"12\\\",\\n  \\\"pods_capacity\\\": \\\"110\\\"\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/64106d4d79fa4e9f/tools/001-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/64106d4d79fa4e9f/tools/001-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/64106d4d79fa4e9f/tools/001-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:59:10Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-insufficient-cpu, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nvolumes:\n- {\"name\": \"kube-api-access-26zhx\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/64106d4d79fa4e9f/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/64106d4d79fa4e9f/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/64106d4d79fa4e9f/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  18m                 default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  8m4s (x2 over 13m)  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nName:             rc-pending-insufficient-cpu\nLabels:           app=rc-pending-insufficient-cpu\nPod 关键区块:\nQoS Class: Burstable\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-26zhx:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  18m                 default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  8m4s (x2 over 13m)  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/64106d4d79fa4e9f/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/64106d4d79fa4e9f/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/64106d4d79fa4e9f/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"node\":\"master\"},\"value\":[1779347840.525,\"2.2385303354406054\"]},{\"metric\":{\"node\":\"node1\"},\"value\":[1779347840.525,\"0.9949319067075298\"]},{\"metric\":{\"node\":\"node2\"},\"value\":[1779347840.525,\"1.80121884284428\"]}]}}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/64106d4d79fa4e9f/tools/004-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/64106d4d79fa4e9f/tools/004-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/64106d4d79fa4e9f/tools/004-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"requests\\\": {\\n    \\\"cpu\\\": \\\"100k\\\",\\n    \\\"memory\\\": \\\"64Mi\\\"\\n  }\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/64106d4d79fa4e9f/tools/005-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/64106d4d79fa4e9f/tools/005-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/64106d4d79fa4e9f/tools/005-evidence-run_bash_command.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"node\":\"master\"},\"value\":[1779347846.631,\"18.654419462005045\"]},{\"metric\":{\"node\":\"node1\"},\"value\":[1779347846.631,\"8.29109922256275\"]},{\"metric\":{\"node\":\"node2\"},\"value\":[1779347846.631,\"15.010157023702334\"]}]}}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/64106d4d79fa4e9f/tools/006-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/64106d4d79fa4e9f/tools/006-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/64106d4d79fa4e9f/tools/006-evidence-execute_prometheus_instant_query.summary.txt"}],"llm_analysis":"## 证据采集结论\n\n### 已采集证据\n\n| 证据项 | 结果 |\n|--------|------|\n| **e1 - kubectl describe Pod** ✅ | FailedScheduling 事件确认：`0/3 nodes are available: 3 Insufficient cpu.`，所有 3 个节点均因 CPU 不足无法调度 |\n| **e2 - Pod YAML spec** ✅ | Pod 的 CPU request 被设置为 **`100k`（100000 核）**，但每个节点仅有 12 核容量 |\n| **e3 - 节点 CPU 容量** ✅ | 3 个节点（master/node1/node2），每节点 **12 核**，总计 36 核 |\n| **e4 - Prometheus 节点 CPU 使用率** ✅ | master: **18.7%**、node1: **8.3%**、node2: **15.0%**，各节点 CPU 实际负载远未饱和 |\n\n### 根因分析\nPod `rc-pending-insufficient-cpu` 的 CPU request 配置为 **`100k`（100000 核）**，这是一个明显异常的值（可能是配置笔误，将 `100m` 误写为 `100k`）。集群中每个节点仅有 12 核容量，因此调度器无法在任何节点上满足这个 CPU 请求。\n\n### 冲突证据\n- **\"集群节点 CPU 资源耗尽\"假说不成立**：Prometheus 数据显示各节点实际 CPU 使用率仅 **8%~19%**，资源非常充裕。真正的根因是 Pod 自身的 CPU request 配置错误（`100k`），而不是集群资源不足。\n\n### 建议修复\n将 Pod/Deployment 中 CPU request 从 `100k` 修正为合理的值（如 `100m`）。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 9 个，匹配计划 4 个，未规划证据 5 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":9,"matched_tool_count":4,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"描述 Pod rc-pending-insufficient-cpu 的完整状态、事件和调度详情","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-pending-insufficient-cpu","purpose":"验证 FailedScheduling 事件原文和 Pod 配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod 的完整 YAML 以检查资源 requests/limits、nodeSelector、affinity、tolerations 等调度配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod -n aiops-e2e rc-pending-insufficient-cpu -o yaml","purpose":"检查 Pod spec 中 CPU request 和调度约束","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"查询集群节点 CPU 容量和可分配量，验证 CPU 是否真正耗尽","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o json | jq -r '.items[] | {name: .metadata.name, cpu_capacity: .status.capacity.cpu, cpu_allocatable: .status.allocatable.cpu, pods_capacity: .status.capacity.pods}'","purpose":"验证所有节点的 CPU 容量和可分配量","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"查询集群中所有节点的 CPU 实际使用率（Prometheus）","level":"important","tool":"execute_prometheus_instant_query","command":"sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate) by (node)","purpose":"验证各节点的实际 CPU 使用率是否接近或达到容量上限","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 描述 Pod rc-pending-insufficient-cpu 的完整状态、事件和调度详情 | `kubectl describe pod -n aiops-e2e rc-pending-insufficient-cpu` |
   | e2 | critical | ✅ | kubectl_get_yaml | 获取 Pod 的完整 YAML 以检查资源 requests/limits、nodeSel... | `kubectl get pod -n aiops-e2e rc-pending-insufficient-cpu -o yaml` |
   | e3 | critical | ✅ | run_bash_command | 查询集群节点 CPU 容量和可分配量，验证 CPU 是否真正耗尽 | `kubectl get nodes -o json | jq -r '.items[] | {name: .metadata.name, cpu_capa...` |
   | e4 | important | ✅ | execute_prometheus_instan... | 查询集群中所有节点的 CPU 实际使用率（Prometheus） | `sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate)...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (26.6s)
   📤 → 下游数据: root_cause=Pod `rc-pending-insufficient-cpu`（namespace: aiops-e2e）处于 Pending 状态的根本原因是其 CPU request 被设置为 `100k`（100000 核），这是一个异常配置值（很可能是将 `100m` 误写为 `100k`）。集群 3 个节点（master/node1/node2）每节点 CPU allocatable 均为 12 核，总计仅 36 核，远无法满足 100000 核的请求。调度器 Events 明确报告 `0/3 nodes are available: 3 Insufficient cpu`。Prometheus 数据显示各节点实际 CPU 使用率仅为 master=18.7%、node1=8.3%、node2=15.0%，集群资源远未饱和，排除了集群资源真实不足的可能性。集群其他 59/65 个 Pod 均正常运行，问题局限于此 Pod 的配置错误。
   confidence=98%
   causal_chain={"root_cause": "Pod `rc-pending-insufficient-cpu` 的 CPU request 被配置为 `100k`（100000 核），这是一个异常值（可能是 `100m` 误写为 `100k`），远超集群所有 3 个节点累计 36 核的总容量。", "propagation": "Pod 创建后 kube-scheduler 尝试为 Pod 分配节点 → 每个节点检查 CPU 可用资源 → 100000 核的 request 远超任意节点 12 核的 allocatable 容量 → 所有节点均标记为 Insufficient cpu → 调度器无法找到可用节点，持续重试并再次失败。", "direct_cause": "Pod spec 中 `resources.requests.cpu = 100k` 配置错误，导致调度器在所有 3 个节点上均判断为 CPU 不足。", "manifestation": "Pod `rc-pending-insufficient-cpu` 在 aiops-e2e 命名空间中持续处于 Pending 状态，Events 持续输出 `FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu.` 事件。"}
   rca_analysis={"phenomenon": "集群 aiops-e2e 命名空间下 Pod `rc-pending-insufficient-cpu` 处于 Pending 状态（已持续约 18 分钟），无法被调度到任何节点上运行。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod 状态 Pending，Events 显示 FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml", "content": "Pod YAML 显示 cpu request = 100k（100000 核），这是异常值", "reliability": "高"}, {"id": "e3", "source": "node_capacity_query", "content": "3 个节点每节点 CPU allocatable = 12 核，总计 36 核", "reliability": "高"}, {"id": "e4", "source": "Prometheus 节点 CPU 使用率", "content": "master=18.7%, node1=8.3%, node2=15.0%，实际负载远未饱和", "reliability": "高"}, {"id": "e5", "source": "run_bash_command_cpu_request", "content": "Pod 的 CPU request 明确设置为 100k", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "65 Pod 中仅此 1 个异常，其余 59 个 Running，集群整体健康", "reliability": "高"}, {"id": "layer_3", "source": "kubectl_describe", "content": "FailedScheduling 事件确认所有 3 节点均 Insufficient cpu", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedScheduling 0/3 nodes are available: 3 Insufficient cpu.", "interpretation": "调度器明确报告所有 3 个节点 CPU 不足以运行此 Pod。"}, {"evidence_id": "e2", "raw_data": "kubectl_get_yaml 显示 Pod 的 CPU request 为 100k", "interpretation": "Pod 的 CPU request 被设置为 100000 核（100k），这是典型的配置错误值（很可能是 100m 误写为 100k）。"}, {"evidence_id": "e3", "raw_data": "master: 12 核, node1: 12 核, node2: 12 核, 每节点 CPU allocatable=12", "interpretation": "集群所有节点总 CPU 容量仅 36 核，远小于 Pod 请求的 100000 核。"}, {"evidence_id": "e4", "raw_data": "master CPU 使用率=18.7%, node1=8.3%, node2=15.0%", "interpretation": "各节点实际 CPU 负载非常充裕，集群不存在真正的资源瓶颈。"}, {"evidence_id": "e5", "raw_data": "cpu request: 100k", "interpretation": "确认 Pod 的 CPU request 值为异常数值 100k（100000 核），这是调度失败的直接原因。"}, {"evidence_id": "layer_1", "raw_data": "65 Pod, 59 Running, 1 Pending", "interpretation": "集群中仅有这个 Pod 异常，其他工作负载运行正常，说明问题被局限在此 Pod 的配置上。"}, {"evidence_id": "layer_3", "raw_data": "FailedScheduling 17m / 7m24s (x2 over 12m)", "interpretation": "调度失败事件持续发生超过 12 分钟，是持续性故障而非瞬时问题。"}], "causal_chain": {"root_cause": "Pod `rc-pending-insufficient-cpu` 的 CPU request 被配置为 `100k`（100000 核），这是一个异常值（可能是 `100m` 误写为 `100k`），远超集群所有 3 个节点累计 36 核的总容量。", "propagation": "Pod 创建后 kube-scheduler 尝试为 Pod 分配节点 → 每个节点检查 CPU 可用资源 → 100000 核的 request 远超任意节点 12 核的 allocatable 容量 → 所有节点均标记为 Insufficient cpu → 调度器无法找到可用节点，持续重试并再次失败。", "direct_cause": "Pod spec 中 `resources.requests.cpu = 100k` 配置错误，导致调度器在所有 3 个节点上均判断为 CPU 不足。", "manifestation": "Pod `rc-pending-insufficient-cpu` 在 aiops-e2e 命名空间中持续处于 Pending 状态，Events 持续输出 `FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu.` 事件。"}, "root_cause": "Pod `rc-pending-insufficient-cpu`（namespace: aiops-e2e）处于 Pending 状态的根本原因是其 CPU request 被设置为 `100k`（100000 核），这是一个异常配置值（很可能是将 `100m` 误写为 `100k`）。集群 3 个节点（master/node1/node2）每节点 CPU allocatable 均为 12 核，总计仅 36 核，远无法满足 100000 核的请求。调度器 Events 明确报告 `0/3 nodes are available: 3 Insufficient cpu`。Prometheus 数据显示各节点实际 CPU 使用率仅为 master=18.7%、node1=8.3%、node2=15.0%，集群资源远未饱和，排除了集群资源真实不足的可能性。集群其他 59/65 个 Pod 均正常运行，问题局限于此 Pod 的配置错误。", "root_cause_summary": "Pod `rc-pending-insufficient-cpu`（namespace: aiops-e2e）处于 Pending 状态的根本原因是其 CPU request 被设置为 `100k`（100000 核），这是一个异常配置值（很可能是将 `100m` 误写为 `100k`）。集群 3 个节点（master/node1/node2）每节点 CPU allocatable 均为 12 核，总计仅 36 核，远无法满足 100000 核的请求。调度器 Events 明确报告 `0/3 nodes are available: 3 Insufficient cpu`。Prometheus 数据显示各节点实际 CPU 使用率仅为 master=18.7%、node1=8.3%、node2=15.0%，集群资源远未饱和，排除了集群资源真实不足的可能性。集群其他 59/65 个 Pod 均正常运行，问题局限于此 Pod 的配置错误。", "confidence": 0.98, "confidence_reason": "有直接证据链闭环：Pod YAML 明确显示 CPU request=100k → 节点容量数据确认每节点仅 12 核 → Prometheus 确认实际负载远未饱和 → Events 确认所有节点均 Insufficient cpu 无法调度。因果链每一步都有原始数据支持，无任何推测环节。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "集群节点 CPU 资源真实耗尽", "probability": "very_low", "reason": "Prometheus 数据直接证伪：master 18.7%、node1 8.3%、node2 15.0%，CPU 资源非常充裕，不存在资源耗尽情况。"}, {"cause": "nodeSelector/taint/affinity 调度约束不匹配", "probability": "very_low", "reason": "Pod YAML 显示 Node-Selectors: <none>，Tolerations 仅有默认的 not-ready:NoExecute，调度器事件明确报告 Insufficient cpu 而非 node affinity/taint 不匹配。"}, {"cause": "PVC 未绑定导致调度阻塞", "probability": "very_low", "reason": "Pod 无 PVC 声明（仅有一个默认 kube-api-access 卷），且调度器事件未提及 PersistentVolumeClaims。"}], "limitations": "未采集 Pod 所属上层控制器（Deployment/StatefulSet）信息，无法确认该配置错误是直接创建 Pod 还是通过控制器下发。但此限制不影响根因结论的正确性。", "llm_raw_analysis": "## 证据清点\n共采集 6 组直接证据 + 3 组上游验证证据：\n- e1: kubectl_describe → FailedScheduling 事件\n- e2: kubectl_get_yaml → Pod CPU request 配置\n- e3: 节点 CPU 容量查询 → 每节点 12 核\n- e4: Prometheus CPU 使用率 → 各节点 8%-19%\n- e5: 确认 CPU request=100k\n- layer_1/layer_3: 上游层已验证的集群 Pod 列表和 Events\n\n## 逐条分析\n证据高度一致，没有冲突信息。关键突破点在于 e2+e5 发现 CPU request=100k（100000 核），e3 确认每节点仅 12 核，e4 确认节点实际负载极低——这共同排除了\"集群资源真实耗尽\"的假说，定位到 Pod 侧配置错误。\n\n## 关联分析\ne1（调度器报错 Insufficient cpu）与 e2+e5（CPU request=100k）形成直接因果：调度器看到 100k 请求，对比节点 12 核容量，自然报告 CPU 不足。e4（实\n... 截断，原始 643 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod `rc-pending-insufficient-cpu`（namespace: aiops-e2e）处于 Pending 状态的根本原因是其 CPU request 被设置为 `100k`（100000 核），这是一个异常配置值（很可能是将 `100m` 误写为 `100k`）。集群 3 ...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod `rc-pending-insufficient-cpu` 的 CPU request 被配置为 `100k`（100000 核），这是一个异常值（可能是 `100m` 误写为 `100k`），远超集群所有 3 个节点累计 36 核的总容量。
     传导机制: Pod 创建后 kube-scheduler 尝试为 Pod 分配节点 → 每个节点检查 CPU 可用资源 → 100000 核的 request 远超任意节点 12 核的 allocatable 容量 → 所有节点均标记为 Insufficient cpu → 调度器无法找到可用节点，持续重试并再次失败。
     最终表现: Pod `rc-pending-insufficient-cpu` 在 aiops-e2e 命名空间中持续处于 Pending 状态，Events 持续输出 `FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu.` 事件。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (24.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5201 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 54.1s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，收到您的请求。作为资深 K8s 诊断报告专家，我立刻为您分析集群状况。

首先，直接回答您的问题：**您的集群整体健康，但存在一个因配置错误导致无法调度的异常 Pod。**

---

## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending |
| **兼容归因层** | L1 - 基础检查 |
| **问题分类** | PendingUnschedulable (调度失败) |
| **置信度** | 高 (98%) |
| **证据完整度** | 4/4 (100%) |

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**集群整体状态**：
- 集群共有 65 个 Pod，其中 **59 个 Running，1 个 Pending**，整体健康度良好。
- 唯一的问题 Pod 因配置错误导致无法被调度。

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-pending-insufficient-cpu` |
| Namespace | `aiops-e2e` |
| Node | 无 (未调度到任何节点) |
| 错误信息 | `FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu.` |

## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 事件 | `kubectl describe pod rc-pending-insufficient-cpu` | `Warning FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu.` | Pod 因为 CPU 资源不足无法调度 |
| 2 | Pod YAML | `kubectl get pod rc-pending-insufficient-cpu -o yaml` | `resources.requests.cpu: 100k` | Pod 请求了 `100k`（100000 核）CPU，这是一个明显异常的配置值 |
| 3 | 节点容量 | `kubectl describe node` (通过 `run_bash_command` 采集) | 节点 master, node1, node2 的 `cpu_allocatable` 均为 `12` | 集群每个节点最多可分配 12 核 CPU，总计 36 核 |
| 4 | 节点使用率 | Prometheus 查询 `node:node_cpu_utilization:ratio` | master=18.7%, node1=8.3%, node2=15.0% | 集群 CPU 远未饱和，实际使用率极低 |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：Pod 请求 `100k` CPU，但集群总容量仅 36 核，调度器在任何节点上都找不到足够的 CPU，因此报错。
- **证据 #4 排除了集群资源真实不足**：所有节点 CPU 使用率均低于 20%，说明集群有充足的空闲资源，失败原因完全在于 Pod 自身的请求值异常。
- **可能的初步假设已在证据中被排除**：根据工具事实 `Node-Selectors: <none>` 和 `finalizers: <none>`，排除了 nodeSelector 不匹配和 finalizer 未清理作为根因的可能性。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 所属控制器 (如 Deployment) 配置 | 低 | 无法确认该配置错误是直接创建 Pod 还是在 Deployment 中配置的，但不影响根因结论。 |

## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                                    │
│ Pod `rc-pending-insufficient-cpu` 的 `resources.requests.cpu` 被错误配置为 `100k`（100000 核）│
│ 这很可能是 `100m`（0.1 核）的笔误（`m` 误写为 `k`）。                                       │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                                    │
│ Pod 创建 → kube-scheduler 为 Pod 寻找节点 → 检查每个节点的 allocatable CPU                   │
│ → 节点 CPU 总量（36核） << Pod 请求量（100000核） → 所有节点判定为 Insufficient cpu        │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                                    │
│ 调度器在所有 3 个节点都无法满足 Pod 的 CPU request，导致调度失败。                           │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                                │
│ Pod `rc-pending-insufficient-cpu` 持续处于 Pending 状态，事件日志不断显示 FailedScheduling。 │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (CPU request: 100k) 和证据 #3 (节点总容量: 36核)，问题的根本原因是 **Pod 的 `resources.requests.cpu` 被配置成了异常值 `100k`（100000核）**，该值远超集群所有节点的总 CPU 容量，导致 Pod 永远无法被调度。

**置信度**：高 (98%)
- ✅ 权威工具 `kubectl_get_yaml` 明确显示 `requests.cpu: 100k`。
- ✅ `kubectl_describe` 事件明确报告 `3 Insufficient cpu`，直接印证。
- ✅ Prometheus 数据（节点使用率 < 20%）排除了集群真实资源不足的可能性，根因锁定为配置错误。

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 删除异常 Pod 或修正其配置**

由于 Pod 可能由控制器（如 Deployment）管理，直接删除后控制器会以错误配置重建 Pod，因此建议优先修改控制器配置。如果该 Pod 是直接创建的，可以删除后重建。

*方法 A（如果 Pod 由 Deployment 管理，例如 `deployment-name`）：*
```bash
# 需要您先确认 Deployment 名称。假设为 deployment-name
kubectl edit deployment <deployment-name> -n aiops-e2e
```
*在 YAML 编辑器中，将 `resources.requests.cpu` 从 `100k` 修改为 `100m`，保存退出。*

*方法 B（如果 Pod 是直接创建的，快速修复）：*
```bash
# 删除导致问题的 Pod
kubectl delete pod rc-pending-insufficient-cpu -n aiops-e2e
```
*然后创建使用正确配置 `100m` 的新 Pod。*

*依据：* 当前配置 `100k` 是集群无法承载的异常值，修正为 `100m` 是唯一且直接的修复方案。

### 后续优化
1. **添加准入控制**：配置 **ValidatingAdmissionPolicy** 或 **Kyverno/Opa Gatekeeper** 等策略，拦截明显异常的资源配置请求（如 CPU request > 节点容量）。
2. **代码审查**：在 CI/CD 流程中加入对 YAML/Helm Chart 中资源配置的校验，防止类似的笔误进入生产环境。
3. **审计与教育**：提醒相关开发/运维人员注意，`m` 代表毫核（milli-core），`k` 在 Kubernetes 资源表示中无效，是一个常见的错误。

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 检查 Pod 状态 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e` | Pod 应被删除或 STATUS 变为 Running |
| 2. 验证资源 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml | grep -A 3 requests` | `cpu: 100m` (而非 100k) |
| 3. 监控 Pod 日志 | `kubectl logs rc-pending-insufficient-cpu -n aiops-e2e --tail=50` | 应用正常启动日志 |

## ⚠️ 注意事项
- 删除或更新 Pod 前，请确认其功能和影响范围。
- 配置中的 `100k` 值非常特殊，请务必检查历史提交，找出是谁以及为什么要设置这个值，防止其他人复现同样错误。

---

## 📊 性能统计

├─ 总耗时: 1.9m
├─ 问题定位: 23.6s (21%) ✅
├─ 证据链采集: 39.0s (34%) ✅
├─ 根因分析: 26.6s (23%) ✅
├─ 汇总总结: 24.8s (22%) ✅
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
