======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 72096fbffb9245ee]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，让我先全局扫描一下集群中所有 Pod 的状态，看看有哪些异常。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 我发现了一个异常的 Pod，让我进一步查看它的详细信息。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                             READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-memory   0/1     Pending   0          44m   <non
   💭 [问题定位] 这个 Pod 处于 Pending 状态，并且没有分配到节点。让我查看一下详细的事件信息，看看调度器为什么无法调度它。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-memory
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  44m                default-scheduler  0/3 nodes are avai
   💭 [问题定位] 现在让我获取这个 Pod 的完整 YAML，看看它的资源请求情况，同时看看这个 runbook。
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-insufficient-memory
namespace: aiops-e2e
creationTimestamp: 2026-05-21T08:00:52Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finali
   💭 [问题定位] 现在让我快速查看一下节点资源状态，确认集群的资源情况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 所有节点都 Ready，让我看看节点的内存分配情况。
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 表格摘要: rows=3 abnormal=0 status_counts={}
NAME      AllocatableMemory    CapacityMemory
# 样例行
master   32758084Ki           32860484Ki
node1    32758076Ki           32860476Ki

   💭 [问题定位] 让我也检查一下 Pod 的资源请求。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=249 lines=15
Executing jq query for pods...
{
  "name": "rc-pending-insufficient-memory",
  "containers": [
    {
      "name": "app",
      "resources": {
        
   💭 [问题定位] 找到根本原因了！现在来分析结果。

---

## 诊断结论

### 全局 Pod 状态概览
- **正常 Pod**：59 个 Running
- **异常 Pod**：1 个 Pending

### 异常详情

| 字段 | 内容 |
|------|------|
| **Pod** | `rc-pending-insufficient-memory` |
| **命名空间** | `aiops-e2e` |
| **状态** | Pending（未调度到任何节点） |
| **节点** | 无（`<none>`） |
| **异常类型** | `PendingUnschedulable`（调度失败） |

### 根因

**内存资源请求过大导致无法调度**

该 Pod 的容器请求了 **`100000Gi`（约 100TB）内存**，而集群中 3 个节点每个节点的可分配内存仅有约 **31Gi（约 32GB）**。

调度器事件明确提示：
> `0/3 nodes are available: 3 Insufficient memory.`

### 分层映射

| 维度 | 值 |
|------|-----|
| **layer** | L1 |
| **derived_layer** | PendingUnschedulable |
| **layers** | L1 |
| **layer_name** | 调度失败 - 资源不足 |
| **confidence** | 高 |
| **pod_status_keyword** | Pending |
| **pod_abnormal_type** | PendingUnschedulable |
| **status_category** | scheduling |
| **abnormal_pods** | rc-pending-insufficient-memory (aiops-e2e) |
| **abnormal_groups** | PendingUnschedulable |

### 可能的场景
1. **配置错误**（最可能）：`resources.requests.memory` 设置为 `100000Gi`，远超实际需要，应仅为 `100Mi` 或 `100Gi` 级别
2. **测试/演示场景**：该 Pod 的 label 包含 `pod_abnormal_type=PendingUnschedulable` 和 `rootcause-e2e=true`，很可能是用于演示调度失败的测试用例

### 建议修复方向
- 降低 Pod 的 memory request 到一个合理的值（例如 `100Mi`）
- 或删除该测试 Pod（如果是测试用途）：`kubectl delete pod rc-pending-insufficient-memory -n aiops-e2e`
   ✅ [问题定位] 完成 (30.0s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '配置错误 - memory request 过大', 'probability': '高', 'reason': 'Pod 的 resources.requests.memory 设置为 100000Gi（约100TB），远超集群实际可用内存（每个节点约31Gi），导致所有节点均无法满足调度要求。'}, {'scenario': '测试/演示 Pod', 'probability': '中', 'reason': 'Pod 标签包含 pod_abnormal_type=PendingUnschedulable 和 rootcause-e2e=true，且 annotation 指定了诊断 runbook，很可能是有意创建的测试用例。'}]
   entities=[{"type": "Pod", "name": "rc-pending-insufficient-memory", "namespace": "aiops-e2e"}]
   reasoning=集群中存在 1 个异常 Pod `rc-pending-insufficient-memory`（命名空间 aiops-e2e），状态为 Pending，调度失败。根本原因是该 Pod 的 container `app` 设置了 resources.requests.memory = 100000Gi（约 100TB），而集群 3 个节点（master/node1/node2）每个节点可分配内存仅约 31Gi。调度器事件明确显示 `0/3 nodes are available: 3 Insufficient memory`。所有节点状态均为 Ready，不存在节点级故障。根据五层模型，Pending/PendingUnschedulable 归因于调度层（L1），derived_layer 为 PendingUnschedulable，status_category 为 scheduling。这是一个典型的资源配置错误或测试用例导致的调度失败。
   layer_analysis={"layer": "L1", "derived_layer": "PENDINGUNSCHEDULABLE", "layers": ["L1"], "layer_name": "调度失败 - 资源不足", "confidence": 0.95, "reasoning": "集群中存在 1 个异常 Pod `rc-pending-insufficient-memory`（命名空间 aiops-e2e），状态为 Pending，调度失败。根本原因是该 Pod 的 container `app` 设置了 resources.requests.memory = 100000Gi（约 100TB），而集群 3 个节点（master/node1/node2）每个节点可分配内存仅约 31Gi。调度器事件明确显示 `0/3 nodes are available: 3 Insufficient memory`。所有节点状态均为 Ready，不存在节点级故障。根据五层模型，Pending/PendingUnschedulable 归因于调度层（L1），derived_layer 为 PendingUnschedulable，status_category 为 scheduling。这是一个典型的资源配置错误或测试用例导致的调度失败。", "abnormal_pods": [{"name": "rc-pending-insufficient-memory", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-insufficient-memory", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "配置错误 - memory request 过大", "probability": "高", "reason": "Pod 的 resources.requests.memory 设置为 100000Gi（约100TB），远超集群实际可用内存（每个节点约31Gi），导致所有节点均无法满足调度要求。"}, {"scenario": "测试/演示 Pod", "probability": "中", "reason": "Pod 标签包含 pod_abnormal_type=PendingUnschedulable 和 rootcause-e2e=true，且 annotation 指定了诊断 runbook，很可能是有意创建的测试用例。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-memory"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-memory"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-insufficient-memory                      0/1     Pending     0              44m     <none>           <none>   <none>           <none>            app=rc-pending-insufficient-memory,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/72096fbffb9245ee/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/72096fbffb9245ee/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/72096fbffb9245ee/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我将直接执行既有 evidence_plan 中的关键工具调用，采集真实环境证据。
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-insufficient-memory
namespace: aiops-e2e
creationTimestamp: 2026-05-21T08:00:52Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finali
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                             READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-memory   0/1     Pending   0          45m   <non
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-memory
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  45m                default-scheduler  0/3 nodes are avai
   💭 [证据链采集] 现在执行计划项 e4——验证节点可分配内存。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "master   32758084Ki\nnode1    32758076Ki\nnode2    32758080Ki\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] 同时，我再确认一下 memory request 的具体数值（虽然 YAML 已看到，但从容器资源角度再验证）：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "100000Gi", "stderr": "", "returncode": 0}
   💭 [证据链采集] ## 证据采集结论

### ✅ 已采集证据（共 5 项）

| # | 维度 | 证据内容 | 状态 |
|---|------|---------|------|
| **e1** | Pod 当前状态 | `rc-pending-insufficient-memory` 在 namespace `aiops-e2e`，STATUS=Pending，READY=0/1，已持续 45min | ✅ 异常持续确认 |
| **e2** | FailedScheduling 事件 | 最新事件仍为 `0/3 nodes are available: 3 Insufficient memory`，预选失败：无 victim 可抢占 | ✅ 根因明确 |
| **e3** | Pod 资源配置 | `resources.requests.memory = 100000Gi`（约 100TB），`imagePullPolicy=Never`，镜像 `busybox:1.36` | ✅ 配置证明确认 |
| **e4** | 节点可分配内存 | master=32758084Ki(~31.2Gi), node1=32758076Ki(~31.2Gi), node2=32758080Ki(~31.2Gi) | ✅ 确认节点远不足以满足请求 |
| **e5** | Pod QoS/调度条件 | QoS Class=Burstable, Node-Selectors=`<none>`, Tolerations 仅含默认 not-ready/ unreachable，无亲和性约束 | ✅ 无其他调度约束干扰 |

### ⚠️ 未采集/冲突证据
- 无冲突证据。所有工具调用均成功返回预期结果，Pod 仍存在于指定 namespace，事件持续推送。

### 🧠 根因判断
**Pod 因 resources.requests.memory 配置为 100000Gi（100TB）**，而集群 3 个节点每个仅约 31Gi 可分配内存，导致调度器 `0/3 nodes are available: 3 Insufficient memory`。Pod 具有测试标签 `pod_abnormal_type=PendingUnschedulable` 和 `rootcause-e2e=true`，且 annotation 指定 runbook，确认这是一个**测试/演示用例**引发的调度失败异常。
   ✅ [证据链采集] 完成 (20.1s)
   📤 → 下游数据: evidence_items=11/11
   evidence_analysis={"evidence_plan":[{"id":"e1-pod-status","description":"确认异常 Pod rc-pending-insufficient-memory 当前状态（Pending）是否持续存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-pending-insufficient-memory -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-insufficient-memory","namespace":"aiops-e2e","resource_type":"pod"},"purpose":"验证 Pod 当前状态仍为 Pending，确认异常持续","evidence_type":"current_status","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2-pod-events","description":"获取 Pod 最新调度事件，验证 FailedScheduling + Insufficient memory 是否持续","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-memory -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-insufficient-memory","namespace":"aiops-e2e","resource_type":"pod"},"purpose":"查看最新 FailedScheduling 事件，确认资源不足根因","evidence_type":"events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3-pod-yaml","description":"获取 Pod YAML 确认 memory request 配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-memory -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-insufficient-memory","namespace":"aiops-e2e","resource_type":"pod","output":"yaml"},"purpose":"验证 resources.requests.memory = 100000Gi 配置","evidence_type":"config","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e4-node-memory","description":"验证集群各节点可分配内存","level":"important","tool":"run_bash_command","command":"kubectl get nodes -o custom-columns=NAME:.metadata.name,AllocatableMemory:.status.allocatable.memory --no-headers","tool_args":{"command":"kubectl get nodes -o custom-columns=NAME:.metadata.name,AllocatableMemory:.status.allocatable.memory --no-headers"},"purpose":"确认节点可分配内存远小于 Pod 请求的 100000Gi","evidence_type":"node_resource","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-insufficient-memory\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T08:00:52Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-insufficient-memory, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nvolumes:\n- {\"name\": \"kube-api-access-c69j6\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/72096fbffb9245ee/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/72096fbffb9245ee/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/72096fbffb9245ee/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                             READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS\nrc-pending-insufficient-memory   0/1     Pending   0          45m   <none>   <none>   <none>           <none>            app=rc-pending-insufficient-memory,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/72096fbffb9245ee/tools/002-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/72096fbffb9245ee/tools/002-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/72096fbffb9245ee/tools/002-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-insufficient-memory\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  45m                default-scheduler  0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  19m (x5 over 39m)  default-scheduler  0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nName:             rc-pending-insufficient-memory\nLabels:           app=rc-pending-insufficient-memory\nPod 关键区块:\nQoS Class: Burstable\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-c69j6:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  45m                default-scheduler  0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  19m (x5 over 39m)  default-scheduler  0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/72096fbffb9245ee/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/72096fbffb9245ee/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/72096fbffb9245ee/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"master   32758084Ki\\nnode1    32758076Ki\\nnode2    32758080Ki\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/72096fbffb9245ee/tools/004-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/72096fbffb9245ee/tools/004-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/72096fbffb9245ee/tools/004-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"100000Gi\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/72096fbffb9245ee/tools/005-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/72096fbffb9245ee/tools/005-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/72096fbffb9245ee/tools/005-evidence-run_bash_command.summary.txt"}],"llm_analysis":"## 证据采集结论\n\n### ✅ 已采集证据（共 5 项）\n\n| # | 维度 | 证据内容 | 状态 |\n|---|------|---------|------|\n| **e1** | Pod 当前状态 | `rc-pending-insufficient-memory` 在 namespace `aiops-e2e`，STATUS=Pending，READY=0/1，已持续 45min | ✅ 异常持续确认 |\n| **e2** | FailedScheduling 事件 | 最新事件仍为 `0/3 nodes are available: 3 Insufficient memory`，预选失败：无 victim 可抢占 | ✅ 根因明确 |\n| **e3** | Pod 资源配置 | `resources.requests.memory = 100000Gi`（约 100TB），`imagePullPolicy=Never`，镜像 `busybox:1.36` | ✅ 配置证明确认 |\n| **e4** | 节点可分配内存 | master=32758084Ki(~31.2Gi), node1=32758076Ki(~31.2Gi), node2=32758080Ki(~31.2Gi) | ✅ 确认节点远不足以满足请求 |\n| **e5** | Pod QoS/调度条件 | QoS Class=Burstable, Node-Selectors=`<none>`, Tolerations 仅含默认 not-ready/ unreachable，无亲和性约束 | ✅ 无其他调度约束干扰 |\n\n### ⚠️ 未采集/冲突证据\n- 无冲突证据。所有工具调用均成功返回预期结果，Pod 仍存在于指定 namespace，事件持续推送。\n\n### 🧠 根因判断\n**Pod 因 resources.requests.memory 配置为 100000Gi（100TB）**，而集群 3 个节点每个仅约 31Gi 可分配内存，导致调度器 `0/3 nodes are available: 3 Insufficient memory`。Pod 具有测试标签 `pod_abnormal_type=PendingUnschedulable` 和 `rootcause-e2e=true`，且 annotation 指定 runbook，确认这是一个**测试/演示用例**引发的调度失败异常。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 11/11 项，完整度 100%；实际执行工具 12 个，匹配计划 4 个，未规划证据 8 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":11,"environment_evidence_collected":11,"environment_evidence_completeness":1.0,"executed_tool_count":12,"matched_tool_count":4,"unplanned_tool_count":8,"evidence_inventory":[{"id":"e1-pod-status","description":"确认异常 Pod rc-pending-insufficient-memory 当前状态（Pending）是否持续存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-pending-insufficient-memory -n aiops-e2e","purpose":"验证 Pod 当前状态仍为 Pending，确认异常持续","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-pod-events","description":"获取 Pod 最新调度事件，验证 FailedScheduling + Insufficient memory 是否持续","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-memory -n aiops-e2e","purpose":"查看最新 FailedScheduling 事件，确认资源不足根因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3-pod-yaml","description":"获取 Pod YAML 确认 memory request 配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-memory -n aiops-e2e -o yaml","purpose":"验证 resources.requests.memory = 100000Gi 配置","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"e4-node-memory","description":"验证集群各节点可分配内存","level":"important","tool":"run_bash_command","command":"kubectl get nodes -o custom-columns=NAME:.metadata.name,AllocatableMemory:.status.allocatable.memory --no-headers","purpose":"确认节点可分配内存远小于 Pod 请求的 100000Gi","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_7","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1-pod-status | critical | ✅ | kubectl_get_by_name | 确认异常 Pod rc-pending-insufficient-memory 当前状态（... | `kubectl get pod rc-pending-insufficient-memory -n aiops-e2e` |
   | e2-pod-events | critical | ✅ | kubectl_describe | 获取 Pod 最新调度事件，验证 FailedScheduling + Insuffici... | `kubectl describe pod rc-pending-insufficient-memory -n aiops-e2e` |
   | e3-pod-yaml | critical | ✅ | kubectl_get_yaml | 获取 Pod YAML 确认 memory request 配置 | `kubectl get pod rc-pending-insufficient-memory -n aiops-e2e -o yaml` |
   | e4-node-memory | important | ✅ | run_bash_command | 验证集群各节点可分配内存 | `kubectl get nodes -o custom-columns=NAME:.metadata.name,AllocatableMemory:.st...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (18.5s)
   📤 → 下游数据: root_cause=Pod rc-pending-insufficient-memory（namespace: aiops-e2e）的 container 'app' 配置了 resources.requests.memory=100000Gi（约100TB，证据 e3），而集群 3 个节点 master/node1/node2 的可分配内存分别仅为 32758084Ki/32758076Ki/32758080Ki（约 31.2Gi 每个，证据 e4）。调度器事件明确显示 0/3 nodes are available: 3 Insufficient memory（证据 e2），且无其他调度约束干扰（无 nodeSelector/affinity，证据 e5）。Pod 标签含 pod_abnormal_type=PendingUnschedulable 和 rootcause-e2e=true，annotation 指定诊断 runbook，确认为测试用例或配置错误导致的调度失败。
   confidence=98%
   causal_chain={"root_cause": "Pod 的 resources.requests.memory 被配置为 100000Gi（约 100TB），远大于集群所有节点可分配内存之和", "propagation": "调度器在过滤阶段检查所有 3 个节点的可分配内存（均约 31.2Gi），不满足 100000Gi 的 request，将所有节点标记为 Insufficient memory → 预选阶段也未能找到可抢占的 victim Pod → Pod 持续停留在 Pending 状态", "direct_cause": "每个节点的可分配内存（~31.2Gi）均无法满足 Pod 请求的 100000Gi 内存", "manifestation": "Pod rc-pending-insufficient-memory 在 aiops-e2e 命名空间中处于 Pending 状态，READY=0/1，events 持续报 FailedScheduling: 0/3 nodes are available: 3 Insufficient memory"}
   rca_analysis={"phenomenon": "命名空间 aiops-e2e 中存在 1 个异常 Pod rc-pending-insufficient-memory，状态为 Pending，READY=0/1，已持续 45 分钟。调度器事件显示 FailedScheduling: 0/3 nodes are available: 3 Insufficient memory。", "evidence_inventory": [{"id": "e1-pod-status", "source": "kubectl_get_yaml", "content": "Pod rc-pending-insufficient-memory，phase=Pending，nodeName=None，已持续 45min", "reliability": "高"}, {"id": "e2-pod-events", "source": "kubectl_describe", "content": "Warning FailedScheduling: 0/3 nodes are available: 3 Insufficient memory，无预选 victim", "reliability": "高"}, {"id": "e3-pod-yaml", "source": "kubernetes_jq_query", "content": "container app 的 resources.requests.memory = 100000Gi（约 100TB）", "reliability": "高"}, {"id": "e4-node-memory", "source": "kubernetes_tabular_query", "content": "master AllocatableMemory=32758084Ki(~31.2Gi), node1=32758076Ki(~31.2Gi), node2=32758080Ki(~31.2Gi)", "reliability": "高"}, {"id": "e5-pod-scheduling-context", "source": "kubectl_describe", "content": "QoS Class=Burstable, Node-Selectors=<none>, 仅默认 tolerations，无亲和性约束", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1-pod-status", "raw_data": "phase: Pending, nodeName: None, creationTimestamp: 2026-05-21T08:00:52Z, deletionTimestamp: <absent>", "interpretation": "Pod 当前仍处于 Pending 状态且未分配到任何节点，未被删除或清理，异常持续存在"}, {"evidence_id": "e2-pod-events", "raw_data": "Warning FailedScheduling 45m default-scheduler 0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.", "interpretation": "调度器明确报告所有 3 个节点均因内存不足无法调度该 Pod，且无任何可抢占的 victim Pod"}, {"evidence_id": "e3-pod-yaml", "raw_data": "{\"name\":\"app\",\"resources\":{\"requests\":{\"cpu\":\"50m\",\"memory\":\"100000Gi\"}}}", "interpretation": "Pod 的 container 'app' 请求 100000Gi 内存（约 100TB），这是导致调度器判定内存不足的直接原因"}, {"evidence_id": "e4-node-memory", "raw_data": "master=32758084Ki(~31.2Gi), node1=32758076Ki(~31.2Gi), node2=32758080Ki(~31.2Gi)", "interpretation": "集群 3 个节点每个可分配内存仅约 31.2Gi，总和不足 100Gi，远不满足 100000Gi 的请求量"}, {"evidence_id": "e5-pod-scheduling-context", "raw_data": "QoS Class: Burstable, Node-Selectors: <none>, Tolerations: node.kubernetes.io/not-ready:NoExecute, node.kubernetes.io/unreachable:NoExecute", "interpretation": "无 nodeSelector/亲和性/taint 等额外调度约束干扰，调度失败完全由资源不足导致"}], "causal_chain": {"root_cause": "Pod 的 resources.requests.memory 被配置为 100000Gi（约 100TB），远大于集群所有节点可分配内存之和", "propagation": "调度器在过滤阶段检查所有 3 个节点的可分配内存（均约 31.2Gi），不满足 100000Gi 的 request，将所有节点标记为 Insufficient memory → 预选阶段也未能找到可抢占的 victim Pod → Pod 持续停留在 Pending 状态", "direct_cause": "每个节点的可分配内存（~31.2Gi）均无法满足 Pod 请求的 100000Gi 内存", "manifestation": "Pod rc-pending-insufficient-memory 在 aiops-e2e 命名空间中处于 Pending 状态，READY=0/1，events 持续报 FailedScheduling: 0/3 nodes are available: 3 Insufficient memory"}, "root_cause": "Pod rc-pending-insufficient-memory（namespace: aiops-e2e）的 container 'app' 配置了 resources.requests.memory=100000Gi（约100TB，证据 e3），而集群 3 个节点 master/node1/node2 的可分配内存分别仅为 32758084Ki/32758076Ki/32758080Ki（约 31.2Gi 每个，证据 e4）。调度器事件明确显示 0/3 nodes are available: 3 Insufficient memory（证据 e2），且无其他调度约束干扰（无 nodeSelector/affinity，证据 e5）。Pod 标签含 pod_abnormal_type=PendingUnschedulable 和 rootcause-e2e=true，annotation 指定诊断 runbook，确认为测试用例或配置错误导致的调度失败。", "root_cause_summary": "Pod rc-pending-insufficient-memory（namespace: aiops-e2e）的 container 'app' 配置了 resources.requests.memory=100000Gi（约100TB，证据 e3），而集群 3 个节点 master/node1/node2 的可分配内存分别仅为 32758084Ki/32758076Ki/32758080Ki（约 31.2Gi 每个，证据 e4）。调度器事件明确显示 0/3 nodes are available: 3 Insufficient memory（证据 e2），且无其他调度约束干扰（无 nodeSelector/affinity，证据 e5）。Pod 标签含 pod_abnormal_type=PendingUnschedulable 和 rootcause-e2e=true，annotation 指定诊断 runbook，确认为测试用例或配置错误导致的调度失败。", "confidence": 0.98, "confidence_reason": "所有关键证据均直接采集并交叉验证：Pod 状态持续 Pending（e1）、调度事件明确指向 Insufficient memory（e2）、Pod 资源配置确认为 100000Gi（e3）、节点可分配内存数据精确到 KiB（e4）、无其他调度约束干扰（e5），因果链完整无断层，置信度极高", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "节点 taint/nodeSelector/affinity 不匹配", "probability": "low", "reason": "kubectl_describe 显示 Node-Selectors=<none>，仅默认 tolerations（not-ready/unreachable），无亲和性约束，已排除"}, {"cause": "PVC 未绑定或卷依赖未满足", "probability": "low", "reason": "Pod 仅挂载 kube-api-access-c69j6（默认 ServiceAccount token 卷），无 PVC 依赖，已排除"}, {"cause": "节点 NotReady 或不可用", "probability": "low", "reason": "kubectl_get_by_kind_in_cluster 显示 3 个节点均为 Ready 状态，无异常"}, {"cause": "集群实际资源耗尽（非配置问题）", "probability": "low", "reason": "100000Gi 远超集群总内存（~93.6Gi），即便所有节点空闲也无法满足，属配置级别的异常"}], "limitations": "无。所有关键证据均已采集且无冲突，数据完整性较高。唯一注意点是该 Pod 的 imagePullPolicy=Never 且镜像为 busybox:1.36，若镜像不存在也不会触发调度问题，因为 Pod 尚未到达调度分配节点阶段，镜像拉取不是当前阻塞原因。", "llm_raw_analysis": "L1 根因分析完成。集群仅有 1 个异常组 g1（abnormal_pods 中的 rc-pending-insufficient-memory），无其他异常 Pod。经证据交叉验证，根因为 Pod 资源配置的 memory request（100000Gi）远超集群各节点可分配内存（~31.2Gi/节点），导致调度器在所有 3 个节点上均判定 Insufficient memory，Pod 持续 Pending。非主异常组不存在（仅此一组），已最小验证覆盖。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-insufficient-memory（namespace: aiops-e2e）的 container 'app' 配置了 resources.requests.memory=100000Gi（约100TB，证据 e3），而集群 3 个节点 master/node1/...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod 的 resources.requests.memory 被配置为 100000Gi（约 100TB），远大于集群所有节点可分配内存之和
     传导机制: 调度器在过滤阶段检查所有 3 个节点的可分配内存（均约 31.2Gi），不满足 100000Gi 的 request，将所有节点标记为 Insufficient memory → 预选阶段也未能找到可抢占的 victim Pod → Pod 持续停留在 Pending 状态
     最终表现: Pod rc-pending-insufficient-memory 在 aiops-e2e 命名空间中处于 Pending 状态，READY=0/1，events 持续报 FailedScheduling: 0/3 nodes are available: 3 Insufficient memory


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (23.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5967 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 32.5s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，这是根据您提供的三个阶段分析结果生成的详尽诊断报告。

---
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **核心问题** | 集群中存在 1 个 Pending 状态的 Pod (`rc-pending-insufficient-memory`)，因请求的内存量（100,000Gi）远超集群可用资源，无法被调度到任何节点上。 |
| **整体集群健康度** | 集群中有 65 个 Pod，其中 **59 个正常运行**，1 个异常。集群 3 个节点全部 `Ready`，健康度 99%。 |
| **Pod异常状态** | Pending (PendingUnschedulable) |
| **兼容归因层** | L1 - 调度层 |
| **问题分类** | scheduling (调度失败) |
| **置信度** | 高 (98%) |
| **证据完整度** | 4/4 (100%) |

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 异常Pod | rc-pending-insufficient-memory |
| Namespace | aiops-e2e |
| 受影响节点 | 无（Pod 未被调度到任何节点） |
| 调度器事件摘要 | `0/3 nodes are available: 3 Insufficient memory.` |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 当前状态 | `kubectl_get_by_name` | `STATUS: Pending`，`NODE: <none>`，`AGE: 44m` | Pod 持续处于 `Pending` 状态，从未被调度。 |
| 2 | Pod 调度事件 | `kubectl_describe` | `Warning FailedScheduling  Warning FailedScheduling 19m (x5 over 39m) default-scheduler 0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..` | 调度器找不到任何可用节点，3个节点全部因内存不足被排除。 |
| 3 | Pod 资源配置(YAML) | `kubectl_get_yaml` + `kubernetes_jq_query` | `resources.requests.memory: 100000Gi` (YAML 明确显示) | Pod 的容器 `app` 请求了约 **100TB** 内存。 |
| 4 | 节点可用资源 | `kubernetes_tabular_query` + `run_bash_command` | **master**: `32758084Ki` (~31.2Gi)<br/>**node1**: `32758076Ki` (~31.2Gi)<br/>**node2**: `32758080Ki` (~31.2Gi) | 集群三个节点每个节点最多可分配 `~31.2Gi` 内存。 |
| 5 | Pod 其他调度约束 | `kubectl_describe` | `Node-Selectors: <none>` | Pod 无节点选择器或亲和性等额外调度约束。 |

### 证据关联分析
- **证据 #3 + 证据 #4 直接对比**：Pod 请求内存 (`100000Gi`) 是单个节点可用内存 (`~31Gi`) 的 **3200 多倍**，且高于所有节点内存总和（`~93Gi`），节点根本不可能满足。
- **证据 #2 + 证据 #5 排除其他原因**：调度器事件仅报告 `Insufficient memory`，无 Taint/Toleration、nodeSelector 或 PVC 相关错误，明确了问题核心是资源不足。
- **证据链总结**：Pod 资源配置错误 (Request 100000Gi) → 调度器在所有 3 个节点上执行可行性检查 → 所有节点均因不满足内存需求而被过滤器排除 → Pod 持续 Pending。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | - | 所有关键证据均已采集，无需缺失项。 |

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                    │
│ Pod `rc-pending-insufficient-memory` 的资源配置错误。                         │
│ 其 container `app` 的 `resources.requests.memory` 被设置为 100000Gi (约100TB)。│
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                    │
│ 调度器（kube-scheduler）在预选阶段过滤节点。                                  │
│ 对于每个节点，检查其可分配内存（~31Gi）是否 >= Pod 请求内存（100000Gi）。       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                    │
│ 集群 3 个节点的可分配内存（每个约31Gi）均不能满足 Pod 100000Gi 的内存请求。     │
│ 调度器事件明确指出：`0/3 nodes are available: 3 Insufficient memory.`        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                │
│ Pod `rc-pending-insufficient-memory` 在 `aiops-e2e` 命名空间中处于            │
│ **Pending** 状态，READY=0/1，并持续产生 `FailedScheduling` 事件。            │
└─────────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #3 (`resources.requests.memory: 100000Gi`) 和证据 #4 (节点可分配内存 `~31Gi`)，问题的根本原因是 **Pod 的资源配置存在人为错误**。

Pod 请求的 100,000Gi 内存是一个不切实际的值，导致集群中没有任何节点可以满足其调度需求。此外，Pod 的标签 `pod_abnormal_type=PendingUnschedulable` 和 `rootcause-e2e=true` 强烈暗示这是一个**测试用例**，而非正常的业务应用。

**置信度**：高 (98%)
- ✅ 证据 #2 的调度事件直接指向 `Insufficient memory`。
- ✅ 证据 #3 和 #4 的数据对比提供了无可辩驳的定量证据。
- ✅ 已排除其他可能原因（如 Taint, NodeSelector, PVC）。
- ⚠️ Pod 的 `imagePullPolicy=Never` 和命令 `sh -c sleep 3600` 表明这是一个测试用的静态 Pod，进一步佐证了配置错误的判断。

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）

**1. [确认问题] 查看异常 Pod 的详细配置**
```bash
# 确认 Pod 的资源配置
kubectl get pod rc-pending-insufficient-memory -n aiops-e2e -o yaml | grep -A 10 "resources:"
```
*依据*：验证 `resources.requests.memory` 是否为 100000Gi。

**2. [方案A] 如果这是测试用例且已无用途，删除它：**
```bash
kubectl delete pod rc-pending-insufficient-memory -n aiops-e2e
```
*依据*：如果 Pod 不再需要，删除是最直接的修复方式。

**3. [方案B] 如果需要保留 Pod 但修正配置，需重建 Pod（配置文件无法原地修改）：**
   *   首先，获取 Pod 的完整 YAML 并保存到本地。
   *   然后，修改保存的文件，将 `resources.requests.memory` 设置为一个合理的值，例如 `500Mi` 或 `1Gi`。
   *   最后，删除旧的 Pod 并用修改后的 YAML 重新创建。
```bash
# 步骤1: 导出 YAML
kubectl get pod rc-pending-insufficient-memory -n aiops-e2e -o yaml --export > corrected-pod.yaml

# 步骤2: 编辑 corrected-pod.yaml，将 memory: "100000Gi" 改为 memory: "500Mi"

# 步骤3: 删除旧 Pod
kubectl delete pod rc-pending-insufficient-memory -n aiops-e2e

# 步骤4: 使用修正后的 YAML 创建新 Pod
kubectl apply -f corrected-pod.yaml
```
*依据*：只有通过重建 Pod 才能更改其不可变字段（如 `resources.requests`）。

### 后续优化
- **规范检查**：建议在 CI/CD 或变更流程中加入资源配额校验，防止提交不合理的资源请求。
- **资源配额**：考虑在 Namespace 级别设置 ResourceQuota，限制最大资源请求量，避免单个 Pod 异常配置影响整个集群调度。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 已被删除 | `kubectl get pod rc-pending-insufficient-memory -n aiops-e2e` | 返回 `NotFound` 或 Error |
| 2. 确认没有其他 Pending Pod | `kubectl get pods --all-namespaces --field-selector=status.phase=Pending` | 无输出 (或仅有预期的其他 Pod) |
| 3. (方案B) 确认新 Pod 运行 | `kubectl get pod -n aiops-e2e -l app=rc-pending-insufficient-memory` | `STATUS: Running` 的 Pod |

---
## ⚠️ 注意事项
- 本次问题涉及的 Pod (`rc-pending-insufficient-memory`) 拥有 `rootcause-e2e=true` 和 `pod_abnormal_type=PendingUnschedulable` 标签，极可能是用于 E2E 测试的测试用例，属于**预期内的异常**，而非生产事故。
- 集群内其他 **59 个 Pod** 均正常运行，**3 个节点状态全部 Ready**，集群核心功能无异常。无需对集群进行大规模调整。

---

## 📊 性能统计

├─ 总耗时: 1.5m
├─ 问题定位: 30.0s (32%) ✅
├─ 证据链采集: 20.1s (22%) ✅
├─ 根因分析: 18.5s (20%) ✅
├─ 汇总总结: 23.9s (26%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 13 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 13 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
