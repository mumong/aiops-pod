======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 4a6d37a88bef4bc7]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先来全局扫描 Pod 状态，了解集群的整体健康情况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 集群中只有一个异常 Pod，我来查看它的详情。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-cpu   0/1     Pending   0          26m   <none>   <
   💭 [问题定位] Pod 是 Pending 状态，且标签标注了 `pod_abnormal_type=PendingUnschedulable`，这符合调度问题的特征。我来获取对应的 runbook 作为参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 让我进一步确认调度失败的详细信息。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  26m                default-scheduler  0/3 nodes are availab
   💭 [问题定位] 现在我来查看节点资源情况，确认集群 CPU 的整体状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 所有节点都是 Ready 状态。让我看看每个节点的 CPU 容量和使用情况。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node1
关键诊断行:
                    volumes.kubernetes.io/controller-managed-attach-detach: true
Taints:             <none>
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node2
关键诊断行:
                    volumes.kubernetes.io/controller-managed-attach-detach: true
Taints:             <none>
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: master
关键诊断行:
                    volumes.kubernetes.io/controller-managed-attach-detach: true
Taints:             <none>
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 表格摘要: rows=3 abnormal=0 status_counts={}
NAME     CPU_Capacity   CPU_Allocatable   MEM_Capacity   MEM_Allocatable
# 样例行
master   12             12                32860484Ki   
   💭 [问题定位] 现在让我查看该 Pod 的资源请求量。
   💭 [问题定位] 调用工具: kubectl_get_yaml
   ✅ [问题定位] 完成 (29.9s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '集群 CPU 资源不足导致 Pod 无法调度', 'probability': '高', 'reason': 'FailedScheduling 事件明确显示 0/3 nodes are available: 3 Insufficient cpu，3 个节点 CPU Capacity 均为 12，但 Pod 的 CPU request 超过剩余可用资源'}, {'scenario': 'Pod CPU request 设置过大', 'probability': '中', 'reason': 'Pod 的 QoS Class 为 Burstable，说明设置了 resource requests/limits，但未提供具体数值，推测 CPU request 过高导致无法调度到任何节点'}]
   entities=[{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}, {"type": "Namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}]
   reasoning=集群存在一个当前状态为 Pending 的异常 Pod（rc-pending-insufficient-cpu, namespace aiops-e2e），其 status 为 Pending 且 pod_abnormal_type 标记为 PendingUnschedulable。kubectl describe 显示 FailedScheduling 事件，原因为 "3 Insufficient cpu"（3 个节点 CPU 资源均不足）。所有 3 个节点均为 Ready 状态且无 Taints，节点 CPU 均为 12 核，因此根因是 CPU 资源不足导致 Pod 无法调度，属于调度/资源分配问题，定层为 L1。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "调度/资源分配层", "confidence": 0.95, "reasoning": "集群存在一个当前状态为 Pending 的异常 Pod（rc-pending-insufficient-cpu, namespace aiops-e2e），其 status 为 Pending 且 pod_abnormal_type 标记为 PendingUnschedulable。kubectl describe 显示 FailedScheduling 事件，原因为 \"3 Insufficient cpu\"（3 个节点 CPU 资源均不足）。所有 3 个节点均为 Ready 状态且无 Taints，节点 CPU 均为 12 核，因此根因是 CPU 资源不足导致 Pod 无法调度，属于调度/资源分配问题，定层为 L1。", "abnormal_pods": [{"name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}, {"type": "Namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}], "possible_scenarios": [{"scenario": "集群 CPU 资源不足导致 Pod 无法调度", "probability": "高", "reason": "FailedScheduling 事件明确显示 0/3 nodes are available: 3 Insufficient cpu，3 个节点 CPU Capacity 均为 12，但 Pod 的 CPU request 超过剩余可用资源"}, {"scenario": "Pod CPU request 设置过大", "probability": "中", "reason": "Pod 的 QoS Class 为 Burstable，说明设置了 resource requests/limits，但未提供具体数值，推测 CPU request 过高导致无法调度到任何节点"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-insufficient-cpu                         0/1     Pending     0              26m     <none>           <none>   <none>           <none>            app=rc-pending-insufficient-cpu,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/4a6d37a88bef4bc7/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/4a6d37a88bef4bc7/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/4a6d37a88bef4bc7/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来执行既有的 evidence_plan。先获取 Pod 的详细信息、YAML 配置以及节点的 CPU 容量和分配情况。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"node":"node2"},"value":[1779348354.271,"1.7750000000000001"]},{"metric":{"node":"master"},"value":[1779348354.271,"5.61"]},{"met
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"node":"master"},"value":[1779348354.284,"12"]},{"metric":{"node":"node1"},"value":[1779348354.284,"12"]},{"metric":{"node":"node
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  26m                default-scheduler  0/3 nodes are availab
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:59:10Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizer
   💭 [证据链采集] YAML 中没有直接显示 resources.requests，让我检查一下完整的 YAML 输出，特别是 containers 的 resources 字段。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"requests\": {\n    \"cpu\": \"100k\",\n    \"memory\": \"64Mi\"\n  }\n}\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] 关键证据已全部采集。下面给出完整结论。

---

## 证据采集结论

### ✅ 已采集证据

**e1 - Pod Describe（critical）** ✅
- Pod `rc-pending-insufficient-cpu` 状态：**Pending**，所在 Node：`<none>`（未调度）
- **FailedScheduling 事件原文**：`0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.`
- QoS Class：**Burstable**，无 nodeSelector，无 Taints 限制

**e2 - Pod YAML（critical）** ✅
- `containers[0].resources.requests.cpu = "100k"` — **CPU request 为 100,000 核（100k）**
  - 注意：`100k` 在 Kubernetes 中的含义是 `100000`（十万）个 CPU 核心，不是 `100m`（0.1 核）
  - 这是一个明显**异常/测试性配置**

**e3 - 各节点 CPU 总容量（important）** ✅
| 节点 | CPU Allocatable |
|------|:-------------:|
| master | 12 核 |
| node1 | 12 核 |
| node2 | 12 核 |

**e4 - 各节点 CPU 已分配量（important）** ✅
| 节点 | CPU 已分配 |
|------|:---------:|
| master | 5.61 核 |
| node1 | 0.85 核 |
| node2 | 1.775 核 |

**额外 - CPU request 精确值确认** ✅
- `kubectl get pod -o json` 确认：`requests.cpu = "100k"`（即 100,000 个 CPU 核心）

### 🔍 根因分析

Pod `rc-pending-insufficient-cpu` 的 **`resources.requests.cpu = 100k`（十万核）**，而集群中 **3 个节点每个只有 12 核**可分配。因此所有 3 个节点均返回 `Insufficient cpu`，导致 Pod 无法调度。这是一个**测试构造的异常场景**——CPU request 被刻意设置成远超出集群容量的值。

### ❌ 冲突/未采集证据
- 无冲突证据，所有工具均正常返回结果。
   ✅ [证据链采集] 完成 (21.9s)
   📤 → 下游数据: evidence_items=12/12
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod rc-pending-insufficient-cpu 的完整 describe（当前状态、事件、容器资源 requests/limits）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e"},"purpose":"确认 FailedScheduling 事件原文及 CPU request 具体数值","evidence_type":"current_state_and_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod 的 YAML spec 查看容器资源 requests/limits 精确值","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e"},"purpose":"提取 containers.resources.requests.cpu 精确值，判断 CPU request 是否超过节点剩余容量","evidence_type":"spec_config","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"查看集群节点 CPU allocatable 和使用情况（Prometheus）","level":"important","tool":"execute_prometheus_instant_query","command":"sum(kube_node_status_allocatable{resource='cpu'}) by (node)","tool_args":{},"purpose":"确认各节点可分配的 CPU 总量","evidence_type":"cluster_capacity","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"查看集群节点 CPU 已分配 requests 总量","level":"important","tool":"execute_prometheus_instant_query","command":"sum(kube_pod_container_resource_requests{resource='cpu'}) by (node)","tool_args":{},"purpose":"确认各节点 CPU 已分配量，计算剩余可调度 CPU","evidence_type":"resource_usage","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"execute_prometheus_instant_query","data":"{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"node\":\"node2\"},\"value\":[1779348354.271,\"1.7750000000000001\"]},{\"metric\":{\"node\":\"master\"},\"value\":[1779348354.271,\"5.61\"]},{\"metric\":{\"node\":\"node1\"},\"value\":[1779348354.271,\"0.85\"]},{\"metric\":{},\"value\":[1779348354.271,\"100000\"]}]}}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4a6d37a88bef4bc7/tools/001-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4a6d37a88bef4bc7/tools/001-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4a6d37a88bef4bc7/tools/001-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"node\":\"master\"},\"value\":[1779348354.284,\"12\"]},{\"metric\":{\"node\":\"node1\"},\"value\":[1779348354.284,\"12\"]},{\"metric\":{\"node\":\"node2\"},\"value\":[1779348354.284,\"12\"]}]}}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4a6d37a88bef4bc7/tools/002-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4a6d37a88bef4bc7/tools/002-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4a6d37a88bef4bc7/tools/002-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  26m                default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  16m (x2 over 21m)  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nName:             rc-pending-insufficient-cpu\nLabels:           app=rc-pending-insufficient-cpu\nPod 关键区块:\nQoS Class: Burstable\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-26zhx:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  26m                default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  16m (x2 over 21m)  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4a6d37a88bef4bc7/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4a6d37a88bef4bc7/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4a6d37a88bef4bc7/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:59:10Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-insufficient-cpu, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nvolumes:\n- {\"name\": \"kube-api-access-26zhx\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4a6d37a88bef4bc7/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4a6d37a88bef4bc7/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4a6d37a88bef4bc7/tools/004-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"requests\\\": {\\n    \\\"cpu\\\": \\\"100k\\\",\\n    \\\"memory\\\": \\\"64Mi\\\"\\n  }\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4a6d37a88bef4bc7/tools/005-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4a6d37a88bef4bc7/tools/005-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4a6d37a88bef4bc7/tools/005-evidence-run_bash_command.summary.txt"}],"llm_analysis":"关键证据已全部采集。下面给出完整结论。\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据\n\n**e1 - Pod Describe（critical）** ✅\n- Pod `rc-pending-insufficient-cpu` 状态：**Pending**，所在 Node：`<none>`（未调度）\n- **FailedScheduling 事件原文**：`0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.`\n- QoS Class：**Burstable**，无 nodeSelector，无 Taints 限制\n\n**e2 - Pod YAML（critical）** ✅\n- `containers[0].resources.requests.cpu = \"100k\"` — **CPU request 为 100,000 核（100k）**\n  - 注意：`100k` 在 Kubernetes 中的含义是 `100000`（十万）个 CPU 核心，不是 `100m`（0.1 核）\n  - 这是一个明显**异常/测试性配置**\n\n**e3 - 各节点 CPU 总容量（important）** ✅\n| 节点 | CPU Allocatable |\n|------|:-------------:|\n| master | 12 核 |\n| node1 | 12 核 |\n| node2 | 12 核 |\n\n**e4 - 各节点 CPU 已分配量（important）** ✅\n| 节点 | CPU 已分配 |\n|------|:---------:|\n| master | 5.61 核 |\n| node1 | 0.85 核 |\n| node2 | 1.775 核 |\n\n**额外 - CPU request 精确值确认** ✅\n- `kubectl get pod -o json` 确认：`requests.cpu = \"100k\"`（即 100,000 个 CPU 核心）\n\n### 🔍 根因分析\n\nPod `rc-pending-insufficient-cpu` 的 **`resources.requests.cpu = 100k`（十万核）**，而集群中 **3 个节点每个只有 12 核**可分配。因此所有 3 个节点均返回 `Insufficient cpu`，导致 Pod 无法调度。这是一个**测试构造的异常场景**——CPU request 被刻意设置成远超出集群容量的值。\n\n### ❌ 冲突/未采集证据\n- 无冲突证据，所有工具均正常返回结果。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 12/12 项，完整度 100%；实际执行工具 13 个，匹配计划 4 个，未规划证据 9 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":12,"environment_evidence_collected":12,"environment_evidence_completeness":1.0,"executed_tool_count":13,"matched_tool_count":4,"unplanned_tool_count":9,"evidence_inventory":[{"id":"e1","description":"验证 Pod rc-pending-insufficient-cpu 的完整 describe（当前状态、事件、容器资源 requests/limits）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","purpose":"确认 FailedScheduling 事件原文及 CPU request 具体数值","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod 的 YAML spec 查看容器资源 requests/limits 精确值","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","purpose":"提取 containers.resources.requests.cpu 精确值，判断 CPU request 是否超过节点剩余容量","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"查看集群节点 CPU allocatable 和使用情况（Prometheus）","level":"important","tool":"execute_prometheus_instant_query","command":"sum(kube_node_status_allocatable{resource='cpu'}) by (node)","purpose":"确认各节点可分配的 CPU 总量","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"查看集群节点 CPU 已分配 requests 总量","level":"important","tool":"execute_prometheus_instant_query","command":"sum(kube_pod_container_resource_requests{resource='cpu'}) by (node)","purpose":"确认各节点 CPU 已分配量，计算剩余可调度 CPU","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_8","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod rc-pending-insufficient-cpu 的完整 descri... | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_yaml | 获取 Pod 的 YAML spec 查看容器资源 requests/limits 精确值 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | execute_prometheus_instan... | 查看集群节点 CPU allocatable 和使用情况（Prometheus） | `sum(kube_node_status_allocatable{resource='cpu'}) by (node)` |
   | e4 | important | ✅ | execute_prometheus_instan... | 查看集群节点 CPU 已分配 requests 总量 | `sum(kube_pod_container_resource_requests{resource='cpu'}) by (node)` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (25.5s)
   📤 → 下游数据: root_cause=异常组 g1（Pod rc-pending-insufficient-cpu, namespace aiops-e2e）处于 Pending 状态，类型为 PendingUnschedulable。根本原因是 Pod 的 resources.requests.cpu 被配置为 \"100k\"（100,000 个 CPU 核心，经 kubectl get pod -o json 确认），而集群中 3 个节点（master/node1/node2）的 CPU Allocatable 均为 12 核。调度器 kubectl describe 显示明确事件：\"0/3 nodes are available: 3 Insufficient cpu\"。3 个节点均为 Ready 状态且无 Taints，排除了调度约束不匹配场景。Pod 的 QoS Class 为 Burstable，无 nodeSelector 或 affinity 限制。这是一个测试构造的异常场景，CPU request 被人为设置为远超出集群容量的值。
   confidence=95%
   causal_chain={"root_cause": "Pod rc-pending-insufficient-cpu 的 resources.requests.cpu 被设置为 \"100k\"（100,000 核），这是一个异常极大的值", "propagation": "调度器在调度时检查每个节点的剩余可分配 CPU，Pod 请求 100,000 核，而集群中每个节点仅有 12 核 CPU Allocatable，任何节点都无法满足该请求", "direct_cause": "所有 3 个节点均报告 Insufficient cpu，调度器无法找到可用节点", "manifestation": "Pod 停留在 Pending 状态，Events 中持续出现 FailedScheduling 事件，pod_abnormal_type 标记为 PendingUnschedulable"}
   rca_analysis={"phenomenon": "集群中存在 1 个 Pending 状态的异常 Pod（rc-pending-insufficient-cpu，namespace aiops-e2e），标记为 PendingUnschedulable。该 Pod 无法调度到任何节点，kubectl describe 显示 FailedScheduling 事件：0/3 nodes are available: 3 Insufficient cpu。3 个节点（master/node1/node2）均为 Ready 状态且无 Taints。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod rc-pending-insufficient-cpu 状态 Pending，FailedScheduling 事件：0/3 nodes available: 3 Insufficient cpu。无 nodeSelector，Taints: <none>，QoS Class: Burstable", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml + run_bash_command", "content": "Pod YAML 显示 containers[0].resources.requests.cpu = \"100k\"（即 100,000 核），memory: 64Mi。这是异常的极大值配置", "reliability": "高"}, {"id": "e3", "source": "kubernetes_tabular_query / kubectl_describe", "content": "3 个节点 CPU Allocatable 均为 12 核，无 Taints，状态均为 Ready", "reliability": "高"}, {"id": "e4", "source": "execute_prometheus_instant_query", "content": "各节点 CPU 已分配：master=5.61核, node1=0.85核, node2=1.775核。节点总已分配 requests 均为12核（全部已分配）", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedScheduling 26m default-scheduler 0/3 nodes are available: 3 Insufficient cpu.", "interpretation": "调度器明确报告所有3个节点均 CPU 不足，Pod 无法被调度到任何节点"}, {"evidence_id": "e2", "raw_data": "resources.requests.cpu = \"100k\"（经 kubectl get pod -o json 确认）", "interpretation": "Pod 的 CPU request 被设置为 100,000 核，远超过集群中任何节点的 12 核容量，这是导致 Insufficient cpu 的根本原因"}, {"evidence_id": "e3", "raw_data": "master/node1/node2: CPU Allocatable=12, Taints: <none>, Status: Ready", "interpretation": "节点本身健康、无调度约束限制，排除 taint/nodeSelector/affinity 等场景"}, {"evidence_id": "e4", "raw_data": "master:5.61核/node1:0.85核/node2:1.775核已使用；已分配requests总计12核/节点", "interpretation": "即使某些节点有剩余 CPU（如 node1 剩余约11核），Pod 请求的 100k 核仍然远超任何节点的剩余容量。节点已分配 requests 均为12核，说明 resource quota 全部耗尽"}], "causal_chain": {"root_cause": "Pod rc-pending-insufficient-cpu 的 resources.requests.cpu 被设置为 \"100k\"（100,000 核），这是一个异常极大的值", "propagation": "调度器在调度时检查每个节点的剩余可分配 CPU，Pod 请求 100,000 核，而集群中每个节点仅有 12 核 CPU Allocatable，任何节点都无法满足该请求", "direct_cause": "所有 3 个节点均报告 Insufficient cpu，调度器无法找到可用节点", "manifestation": "Pod 停留在 Pending 状态，Events 中持续出现 FailedScheduling 事件，pod_abnormal_type 标记为 PendingUnschedulable"}, "root_cause": "异常组 g1（Pod rc-pending-insufficient-cpu, namespace aiops-e2e）处于 Pending 状态，类型为 PendingUnschedulable。根本原因是 Pod 的 resources.requests.cpu 被配置为 \\\"100k\\\"（100,000 个 CPU 核心，经 kubectl get pod -o json 确认），而集群中 3 个节点（master/node1/node2）的 CPU Allocatable 均为 12 核。调度器 kubectl describe 显示明确事件：\\\"0/3 nodes are available: 3 Insufficient cpu\\\"。3 个节点均为 Ready 状态且无 Taints，排除了调度约束不匹配场景。Pod 的 QoS Class 为 Burstable，无 nodeSelector 或 affinity 限制。这是一个测试构造的异常场景，CPU request 被人为设置为远超出集群容量的值。", "root_cause_summary": "异常组 g1（Pod rc-pending-insufficient-cpu, namespace aiops-e2e）处于 Pending 状态，类型为 PendingUnschedulable。根本原因是 Pod 的 resources.requests.cpu 被配置为 \\\"100k\\\"（100,000 个 CPU 核心，经 kubectl get pod -o json 确认），而集群中 3 个节点（master/node1/node2）的 CPU Allocatable 均为 12 核。调度器 kubectl describe 显示明确事件：\\\"0/3 nodes are available: 3 Insufficient cpu\\\"。3 个节点均为 Ready 状态且无 Taints，排除了调度约束不匹配场景。Pod 的 QoS Class 为 Burstable，无 nodeSelector 或 affinity 限制。这是一个测试构造的异常场景，CPU request 被人为设置为远超出集群容量的值。", "confidence": 0.95, "confidence_reason": "有直接证据（kubectl describe 的 FailedScheduling 事件明确报告 Insufficient cpu），有精确数值证据（kubectl get pod -o json 确认 CPU request 为 100k，Prometheus 确认节点 CPU allocatable 均为 12 核），所有证据一致指向同一根因，因果链完整无断层", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "Taint/Toleration 不匹配", "probability": "low", "reason": "kubectl describe 显示所有3个节点 Taints: <none>，Pod 也无可疑 toleration 缺失，已排除"}, {"cause": "nodeSelector/affinity 不匹配", "probability": "low", "reason": "Pod 的 Node-Selectors: <none>，无节点选择约束，已排除"}, {"cause": "PVC 未绑定或存储依赖", "probability": "low", "reason": "Pod 无 PVC 依赖，只有默认的 kube-api-access 投影卷，且 FailedScheduling 事件明确指向 Insufficient cpu 而非存储问题"}, {"cause": "节点实际 CPU 资源已被全部占用", "probability": "low", "reason": "虽然各节点已分配 requests 均为12核（总量），但即使有剩余容量（如 node1 实际使用仅0.85核），Pod 请求的100k核也远超出12核上限"}], "limitations": "未获取 Pod 的完整 YAML 原始输出（仅在摘要中确认 CPU request=100k），但通过 kubectl get pod -o json 命令已验证该值。未获取各节点更细粒度的 CPU 调度资源统计（如可被抢占的 best-effort 资源量），但对根因判断无影响。", "llm_raw_analysis": "## 证据清点\\n共采集 4 组关键证据：\\n- e1: kubectl_describe — FailedScheduling 事件确认 3 Insufficient cpu\\n- e2: kubectl_get_yaml + run_bash_command — CPU request = 100k（100,000核）\\n- e3: kubernetes_tabular_query — 3节点各12核CPU，均Ready且无Taints\\n- e4: Prometheus 查询 — 节点CPU已分配及使用情况\\n\\n## 逐条分析\\n- e1：直接证明调度失败原因为CPU不足，排除taint/affinity等场景\\n- e2：这是根因关键证据——100k核远超集群容量\\n- e3：证明节点健康，排除节点故障导致不可调度\\n- e4：即使节点有剩余CPU（如node1仅用0.85核），Pod请求的100k核也远超12核上限\\n\\n## 关联分析\\ne2 ↔ e3：Pod请求100k核 vs 节点只有12核，完全不匹配 → Insufficient cpu\\ne1 ↔ e2：Fail\n... 截断，原始 678 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 异常组 g1（Pod rc-pending-insufficient-cpu, namespace aiops-e2e）处于 Pending 状态，类型为 PendingUnschedulable。根本原因是 Pod 的 resources.requests.cpu 被配置为 \"100k\"（10...
   置信度: 95%
   🔗 因果链:
     根本原因: Pod rc-pending-insufficient-cpu 的 resources.requests.cpu 被设置为 "100k"（100,000 核），这是一个异常极大的值
     传导机制: 调度器在调度时检查每个节点的剩余可分配 CPU，Pod 请求 100,000 核，而集群中每个节点仅有 12 核 CPU Allocatable，任何节点都无法满足该请求
     最终表现: Pod 停留在 Pending 状态，Events 中持续出现 FailedScheduling 事件，pod_abnormal_type 标记为 PendingUnschedulable


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (24.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5428 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 41.5s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将为您分析集群的当前状态。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **问题摘要** | 集群中存在 1 个异常 Pod，处于 **Pending** 状态，因 CPU 资源不足无法调度。集群其余 59 个 Pod 均正常运行。 |
| **Pod异常状态** | Pending (PendingUnschedulable) |
| **兼容归因层** | L1 - 调度/资源分配 |
| **问题分类** | Pod PendingUnschedulable - 资源不足 |
| **置信度** | 高 (95%) |
| **证据完整度** | 4/4 (100%) |

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| **存在异常的 Pod** | `rc-pending-insufficient-cpu` |
| **Namespace** | `aiops-e2e` |
| **Pod 当前状态** | `Pending` |
| **Pod 异常类型** | `PendingUnschedulable` (调度失败) |
| **异常 Pod 数量** | 1 (总数：65) |
| **健康 Pod 数量** | 59 (Running) |
| **集群节点数** | 3 (master, node1, node2) |
| **节点状态** | 全部 `Ready`，无 `Taints` |

---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | **Pod 状态 & 事件** | `kubectl describe pod` | 状态: `Pending`。事件: `Warning FailedScheduling  26m` `0/3 nodes are available: 3 **Insufficient cpu**` | 调度器明确因 CPU 资源不足而无法调度 Pod。 |
| 2 | **Pod 资源请求** | `kubectl get pod -o json` | `requests.cpu: "100k"` | Pod **请求了 100,000 个 CPU 核心**，这是一个异常大的值。 |
| 3 | **节点资源总量** | `kubernetes_tabular_query` | 节点 `master`, `node1`, `node2` 的 `CPU_Allocatable` 均为 **12** 核。 | 集群中任何一个节点都无法满足该 Pod 的 CPU 请求。 |
| 4 | **节点状态 & 约束** | `kubectl describe node` | 所有 3 个节点状态均为 `Ready`，且 `Taints: <none>`。 | 排除了因节点不可用或 Taints/污点不匹配导致的调度失败。 |
| 5 | **Pod 调度约束** | `kubectl describe pod` | `Node-Selectors: <none>` | 排除了因 `nodeSelector` 或亲和性规则不匹配导致的调度失败。 |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：Pod 请求 100,000 核 CPU，但集群中每个节点最多只有 12 核，因此调度器在所有 3 个节点上都发现 CPU 不足(3 `Insufficient cpu`)，导致 Pod 无法被调度。
- **证据 #4 + #5 排除干扰项**：节点均正常且无污点，Pod 无节点选择器，排除了调度约束不匹配的可能，明确将问题定位为**纯粹的集群资源不足**。

### 缺失证据
无，所有关键证据均已采集完毕。

---
## 🎯 根因分析

### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                                     │
│ Pod (rc-pending-insufficient-cpu) 的 `resources.requests.cpu` 被配置为 `100k` (100,000 核)， │
│ 这是一个远超集群承载能力的、极不合理的配置值。                                                │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                          ↓
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                                     │
│ Kubernetes 调度器在为 Pod 寻找合适节点时，会检查每个节点的剩余可分配资源。                     │
│ Pod 请求 100,000 核，而集群中每个节点最多只有 12 核 CPU Allocatable。                         │
│ 因此，没有任何节点能满足该请求。                                                             │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                          ↓
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                                     │
│ 3 个节点均因 CPU 资���不足 (3 `Insufficient cpu`) 而拒绝调度该 Pod。                              │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
                                          ↓
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                                 │
│ Pod 状态一直为 `Pending`，Events 中持续出现 `FailedScheduling` 错误。                        │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (FailedScheduling event)、证据 #2 (`requests.cpu: "100k"`) 和证据 #3 (Node CPU Allocatable: 12)，
问题的根本原因是**Pod 的 CPU 请求（100,000 核）被设置成了远超集群能力（12核/节点）的数值**。
这是一个测试构造的异常场景，使调度器无法在任何节点上找到足够的资源来运行该 Pod。

**置信度**：高 (95%)
- ✅ `FailedScheduling` 事件明确指向 CPU 资源不足。
- ✅ `kubectl get pod -o json` 命令直接输出了异常的 request 值 `100k`。
- ✅ 集群节点资源数据与诊断结果完全吻合。

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）
**1. [优先] 检查并修正 Pod 的 CPU Request**
首先确认当前配置：
```bash
kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o json | jq '.spec.containers[].resources'
```
如果输出显示 `"cpu": "100k"`，则需要修正。由于这是一个测试 Pod，最直接的修复方式是删除并重新创建，或者修改其所属的 Deployment/StatefulSet 配置。

**删除此 Pod (如果不再需要):**
```bash
kubectl delete pod rc-pending-insufficient-cpu -n aiops-e2e
```

**如果需要修复并保留 Pod (假设属于某个控制器):**
您需要找到管理此 Pod 的控制器（如 Deployment），并编辑其 YAML 文件以修正 CPU request 为一个合理值（例如 `500m`）。
```bash
kubectl edit deployment <deployment-name> -n aiops-e2e
```
在编辑器中，将 `resources.requests.cpu` 从 `100k` 修改为 `500m` 或更合适的大小。
*依据*：当前 request 值为 `100k`，严重不合理，修正后调度器即可正常调度。

### 后续优化
1. **资源配额 (ResourceQuota)**：为 namespace 设置 ResourceQuota 可以限制整个 namespace 内的资源请求总量，防止类似的配置错误影响整个集群。
2. **准入控制 (Admission Webhook)**：可以部署一个准入控制器（如 OPA/Gatekeeper），验证 Pod 的 CPU/Memory Request 是否在合理范围内，防止无效配置被提交。
3. **监控告警**：配置告警，当 namespace 中出现长时间处于 Pending 状态的 Pod 时及时通知。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 已被删除 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e` | `Error from server (NotFound): pods "rc-pending-insufficient-cpu" not found` |
| 2. 确认集群健康 | `kubectl get pod -n aiops-e2e \| grep -v Running` | 只显示 `Running` 状态的 Pod（或其他预期的状态），不再有 `Pending` 状态的异常 Pod。 |

---
## ⚠️ 注意事项
- 本次问题的根因是 Pod 配置异常，而非集群节点故障。集群本身运行良好，59 个正常运行的 Pod 证明了这一点。
- 如果这是一个测试环境，建议在删除 Pod 后清理相关的测试资源。如果是生产环境，需要彻查为何会出现 `100k` 这样的异常配置值，以进行流程上的改进。

---

## 📊 性能统计

├─ 总耗时: 1.7m
├─ 问题定位: 29.9s (29%) ✅
├─ 证据链采集: 21.9s (22%) ✅
├─ 根因分析: 25.5s (25%) ✅
├─ 汇总总结: 24.2s (24%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 15 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 15 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
