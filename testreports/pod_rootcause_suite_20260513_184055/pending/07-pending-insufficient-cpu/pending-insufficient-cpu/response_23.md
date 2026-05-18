======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: a6af245ffcbe4ec8]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Pending': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS      RESTARTS      
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  52m                  default-scheduler  0/3 nodes are avail
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
creationTimestamp: 2026-05-14T00:13:40Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizer
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-cpu   0/1     Pending   0          52m   <none>   <
   💭 [问题定位] {
  "layer": "L1",
  "derived_layer": "L1",
  "layers": [
    "L1"
  ],
  "layer_name": "PendingUnschedulable",
  "confidence": 0.95,
  "reasoning": "Pod 'rc-pending-insufficient-cpu' is in Pending state with the reason 'FailedScheduling' and the message '0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..'. This indicates that the cluster does not have enough CPU resources to schedule the Pod. The nodes are in 'Ready' status, so the issue is likely due to insufficient CPU resources on the nodes.",
  "abnormal_pods": [
    {
      "name": "rc-pending-insufficient-cpu",
      "namespace": "aiops-e2e",
      "status": "Pending",
      "reason": "FailedScheduling",
      "message": "0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.."
    }
  ],
  "abnormal_groups": [
    {
      "type": "PendingUnschedulable",
      "count": 1,
      "pods": [
        "rc-pending-insufficient-cpu"
      ]
    }
  ],
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "PendingUnschedulable",
  "status_category": "PendingUnschedulable",
  "key_entities": [
    "rc-pending-insufficient-cpu",
    "aiops-e2e"
  ],
  "possible_scenarios": [
    "Insufficient CPU resources on the nodes to schedule the Pod.",
    "The nodes may have reached their maximum capacity for running Pods.",
    "The Pod may be requesting more CPU resources than are available on any single node."
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 16.2s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[]
   entities=[]
   reasoning=Pod 'rc-pending-insufficient-cpu' is in Pending state with the reason 'FailedScheduling' and the message '0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..'. This indicates that the cluster does not have enough CPU resources to schedule the Pod. The nodes are in 'Ready' status, so the issue is likely due to insufficient CPU resources on the nodes.
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "Pod 'rc-pending-insufficient-cpu' is in Pending state with the reason 'FailedScheduling' and the message '0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..'. This indicates that the cluster does not have enough CPU resources to schedule the Pod. The nodes are in 'Ready' status, so the issue is likely due to insufficient CPU resources on the nodes.", "abnormal_pods": [{"name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-insufficient-cpu                         0/1     Pending     0                52m    <none>           <none>   <none>           <none>            app=rc-pending-insufficient-cpu,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/a6af245ffcbe4ec8/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/a6af245ffcbe4ec8/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/a6af245ffcbe4ec8/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  55m                default-scheduler  0/3 nodes are availab
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 execute_prometheus_instant_query 执行成功但结果为空；这表示查询未命中数据，不能视为已采集到指标值。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
creationTimestamp: 2026-05-14T00:13:40Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizer
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=1 abnormal=1 status_counts={'Pending': 1}
NAME                          READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATE
   💭 [证据链采集] 已采集证据：
1. **kubectl_describe Pod**：确认 Pod `rc-pending-insufficient-cpu` 处于 Pending 状态，调度失败原因为 `0/3 nodes are available: 3 Insufficient cpu`。
2. **kubectl_get_by_kind_in_cluster Node**：所有节点（master、node1、node2）处于 Ready 状态，但未显示足够 CPU 资源分配。
3. **kubectl_get_yaml Pod**：Pod 的 CPU 请求未显式配置，且 `PodScheduled` 条件为 `False`，原因为 `Unschedulable`。
4. **kubectl_get_by_kind_in_namespace Pod**：确认异常 Pod 为 `rc-pending-insufficient-cpu`，状态为 `Pending`。

未采集证据：
1. **Prometheus 查询**：`sum(kube_node_status_capacity_cpu_cores) - sum(kube_node_status_allocatable_cpu_cores)` 返回空，未能获取节点 CPU 资源分配情况。

冲突证据：
1. Prometheus 查询未返回数据，无法验证节点 CPU 资源是否不足。
   ✅ [证据链采集] 完成 (1m 45.6s)
   📤 → 下游数据: evidence_items=8/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 'rc-pending-insufficient-cpu' 的详细状态和事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-pending-insufficient-cpu","kind":"Pod"},"purpose":"获取 Pod 的详细状态、事件和调度失败原因","evidence_type":"status_event","target_scope":"aiops-e2e/rc-pending-insufficient-cpu","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"验证集群节点的资源分配和状态","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes","tool_args":{"kind":"Node"},"purpose":"确认节点是否 Ready 以及是否有足够的 CPU 资源分配","evidence_type":"node_status","target_scope":"cluster/nodes","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true},{"id":"e3","description":"验证节点资源使用情况","level":"important","tool":"execute_prometheus_instant_query","command":"query","tool_args":{"query":"sum(kube_node_status_capacity_cpu_cores) - sum(kube_node_status_allocatable_cpu_cores)"},"purpose":"","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"验证 Pod 的资源配置（如 cpu requests/limits）","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","tool_args":{"namespace":"aiops-e2e","name":"rc-pending-insufficient-cpu","kind":"Pod"},"purpose":"检查 Pod 的 CPU 请求和限制是否合理","evidence_type":"pod_config","target_scope":"aiops-e2e/rc-pending-insufficient-cpu","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  55m                default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  10m (x9 over 50m)  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nName:             rc-pending-insufficient-cpu\nLabels:           app=rc-pending-insufficient-cpu\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a6af245ffcbe4ec8/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a6af245ffcbe4ec8/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a6af245ffcbe4ec8/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a6af245ffcbe4ec8/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a6af245ffcbe4ec8/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a6af245ffcbe4ec8/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"execute_prometheus_instant_query 执行成功但结果为空；这表示查询未命中数据，不能视为已采集到指标值。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/a6af245ffcbe4ec8/tools/003-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a6af245ffcbe4ec8/tools/003-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a6af245ffcbe4ec8/tools/003-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-14T00:13:40Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-insufficient-cpu, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nvolumes:\n- {\"name\": \"kube-api-access-76hmh\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a6af245ffcbe4ec8/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a6af245ffcbe4ec8/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a6af245ffcbe4ec8/tools/004-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"kubectl_get_by_kind_in_namespace 表格摘要: rows=1 abnormal=1 status_counts={'Pending': 1}\nNAME                          READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\nrc-pending-insufficient-cpu   0/1     Pending   0          55m   <none>   <none>   <none>           <none>            app=rc-pending-insufficient-cpu,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a6af245ffcbe4ec8/tools/005-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a6af245ffcbe4ec8/tools/005-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a6af245ffcbe4ec8/tools/005-evidence-kubectl_get_by_kind_in_namespace.summary.txt"}],"llm_analysis":"已采集证据：\n1. **kubectl_describe Pod**：确认 Pod `rc-pending-insufficient-cpu` 处于 Pending 状态，调度失败原因为 `0/3 nodes are available: 3 Insufficient cpu`。\n2. **kubectl_get_by_kind_in_cluster Node**：所有节点（master、node1、node2）处于 Ready 状态，但未显示足够 CPU 资源分配。\n3. **kubectl_get_yaml Pod**：Pod 的 CPU 请求未显式配置，且 `PodScheduled` 条件为 `False`，原因为 `Unschedulable`。\n4. **kubectl_get_by_kind_in_namespace Pod**：确认异常 Pod 为 `rc-pending-insufficient-cpu`，状态为 `Pending`。\n\n未采集证据：\n1. **Prometheus 查询**：`sum(kube_node_status_capacity_cpu_cores) - sum(kube_node_status_allocatable_cpu_cores)` 返回空，未能获取节点 CPU 资源分配情况。\n\n冲突证据：\n1. Prometheus 查询未返回数据，无法验证节点 CPU 资源是否不足。","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 8/9 项，完整度 89%；实际执行工具 9 个，匹配计划 3 个，未规划证据 6 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":9,"environment_evidence_collected":8,"environment_evidence_completeness":0.8888888888888888,"executed_tool_count":9,"matched_tool_count":3,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"验证 Pod 'rc-pending-insufficient-cpu' 的详细状态和事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","purpose":"获取 Pod 的详细状态、事件和调度失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证集群节点的资源分配和状态","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes","purpose":"确认节点是否 Ready 以及是否有足够的 CPU 资源分配","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"验证节点资源使用情况","level":"important","tool":"execute_prometheus_instant_query","command":"query","purpose":"","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"验证 Pod 的资源配置（如 cpu requests/limits）","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","purpose":"检查 Pod 的 CPU 请求和限制是否合理","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e4(验证 Pod 的资源配置（如 cpu requests/limits）): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 89%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod 'rc-pending-insufficient-cpu' 的详细状态和事件 | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_by_kind_in_cl... | 验证集群节点的资源分配和状态 | `kubectl get nodes` |
   | e3 | important | ✅ | execute_prometheus_instan... | 验证节点资源使用情况 | `query` |
   | e4 | important | ❌ | kubectl_get_yaml | 验证 Pod 的资源配置（如 cpu requests/limits） | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml` |

   ⚠️ 未采集原因:
   - e4(验证 Pod 的资源配置（如 cpu requests/limits）): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 18.5s)
   📤 → 下游数据: root_cause=集群节点的 CPU 资源不足，导致 Pod 'rc-pending-insufficient-cpu' 无法调度。
   confidence=90%
   causal_chain={"root_cause": "集群节点的 CPU 资源不足，导致 Pod 'rc-pending-insufficient-cpu' 无法调度。", "intermediate_causes": ["Pod 'rc-pending-insufficient-cpu' 的 CPU 请求未显式配置，导致调度器无法找到合适的节点。", "集群节点的 CPU 资源不足，导致调度器无法找到合适的节点。"], "direct_causes": ["Pod 'rc-pending-insufficient-cpu' 的 CPU 请求未显式配置。", "集群节点的 CPU 资源不足。"], "symptoms": ["Pod 'rc-pending-insufficient-cpu' 处于 Pending 状态。", "调度失败原因为 '0/3 nodes are available: 3 Insufficient cpu'。"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"description": "验证 Pod 'rc-pending-insufficient-cpu' 的详细状态和事件", "value": "kubectl_describe 摘要:\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  55m                default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  10m (x9 over 50m)  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incomin\n... 截断，原始 507 字符", "level": "critical"}, {"description": "验证集群节点的资源分配和状态", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubern\n... 截断，原始 612 字符", "level": "important"}, {"description": "验证节点资源使用情况", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-14T00:13:40Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-insufficient-cpu, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.m\n... 截断，原始 828 字符", "level": "important"}], "evidence_analysis": [{"description": "Pod 'rc-pending-insufficient-cpu' 的详细状态和事件", "value": "kubectl_describe 显示 Pod 'rc-pending-insufficient-cpu' 处于 Pending 状态，调度失败原因为 '0/3 nodes are available: 3 Insufficient cpu'。"}, {"description": "集群节点的资源分配和状态", "value": "kubectl_get_by_kind_in_cluster 显示所有节点处于 Ready 状态，但未显示足够 CPU 资源分配。"}, {"description": "节点资源使用情况", "value": "kubectl_get_yaml 显示 Pod 'rc-pending-insufficient-cpu' 的 CPU 请求未显式配置，且 'PodScheduled' 条件为 'False'，原因为 'Unschedulable'。"}], "causal_chain": {"root_cause": "集群节点的 CPU 资源不足，导致 Pod 'rc-pending-insufficient-cpu' 无法调度。", "intermediate_causes": ["Pod 'rc-pending-insufficient-cpu' 的 CPU 请求未显式配置，导致调度器无法找到合适的节点。", "集群节点的 CPU 资源不足，导致调度器无法找到合适的节点。"], "direct_causes": ["Pod 'rc-pending-insufficient-cpu' 的 CPU 请求未显式配置。", "集群节点的 CPU 资源不足。"], "symptoms": ["Pod 'rc-pending-insufficient-cpu' 处于 Pending 状态。", "调度失败原因为 '0/3 nodes are available: 3 Insufficient cpu'。"]}, "root_cause": "集群节点的 CPU 资源不足，导致 Pod 'rc-pending-insufficient-cpu' 无法调度。", "root_cause_summary": "集群节点的 CPU 资源不足，导致 Pod 'rc-pending-insufficient-cpu' 无法调度。", "confidence": 0.9, "confidence_reason": "有直接证据，因果链清晰。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [], "limitations": "未能获取节点 CPU 资源分配情况，因为 Prometheus 查询未返回数据。", "llm_raw_analysis": "已采集证据：\n1. **kubectl_describe Pod**：确认 Pod `rc-pending-insufficient-cpu` 处于 Pending 状态，调度失败原因为 `0/3 nodes are available: 3 Insufficient cpu`。\n2. **kubectl_get_by_kind_in_cluster Node**：所有节点（master、node1、node2）处于 Ready 状态，但未显示足够 CPU 资源分配。\n3. **kubectl_get_yaml Pod**：Pod 的 CPU 请求未显式配置，且 `PodScheduled` 条件为 `False`，原因为 `Unschedulable`。\n4. **kubectl_get_by_kind_in_namespace Pod**：确认异常 Pod 为 `rc-pending-insufficient-cpu`，状态为 `Pending`。\n\n未采集证据：\n1. **Prometheus 查询**：`sum(kube_node_status_capacity_cpu_cor\n... 截断，原始 621 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群节点的 CPU 资源不足，导致 Pod 'rc-pending-insufficient-cpu' 无法调度。
   置信度: 90%
   🔗 因果链:
     根本原因: 集群节点的 CPU 资源不足，导致 Pod 'rc-pending-insufficient-cpu' 无法调度。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 12.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4180 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 6m 32.6s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pod 'rc-pending-insufficient-cpu' 处于 Pending 状态 |
| **兼容归因层** | L1 |
| **问题分类** | 调度失败（PendingUnschedulable） |
| **置信度** | 高 (90%) |
| **证据完整度** | 3/4 (75%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-pending-insufficient-cpu |
| Namespace | aiops-e2e |
| Node | <none> |
| 错误信息 | `0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态和事件 | `kubectl describe pod rc-pending-insufficient-cpu` | `Warning  FailedScheduling  52m                  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` | Pod 无法调度，因为集群节点 CPU 资源不足 |
| 2 | 节点状态 | `kubectl get node` | `rows=3 abnormal=0 status_counts={'Ready': 3}` | 所有节点处于 Ready 状态，无异常 |
| 3 | Prometheus 查询 | `execute_prometheus_instant_query` | 查询未命中数据，无结果 | 无法获取节点 CPU 使用率数据，限制诊断精度 |

### 证据关联分析

- **证据 #1 印证**：`0/3 nodes are available: 3 Insufficient cpu` 明确表明节点 CPU 资源不足，无法调度 Pod。
- **证据 #2 补充**：节点状态为 Ready，排除节点状态异常的可能。
- **证据链**：Pod 申请的 CPU 资源 > 节点可用 CPU 资源 → 调度失败 → Pod 状态为 Pending。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 的 CPU requests/limits 配置 | important | 无法确认 Pod 请求的 CPU 资源大小，影响资源调整建议的准确性 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 集群节点的 CPU 资源不足，无法满足 Pod 'rc-pending-insufficient-cpu' 的调度需求。│
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod 请求的 CPU 资源 > 节点可用 CPU 资源 → 调度失败              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 调度失败事件 `0/3 nodes are available: 3 Insufficient cpu`      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Pending，事件显示 `FailedScheduling`                │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (FailedScheduling 事件) 和证据 #2 (节点状态为 Ready)，问题的根本原因是**集群节点的 CPU 资源不足**，导致 Pod 'rc-pending-insufficient-cpu' 无法调度。

**置信度**：高 (90%)
- ✅ `FailedScheduling` 事件明确指向资源不足
- ✅ 节点状态为 Ready，排除节点状态异常
- ⚠️ 缺少 Pod CPU requests/limits 配置，无法精确计算所需资源

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 增加集群节点的 CPU 资源**
```bash
# 如果使用 Kubelet 调度器，可考虑增加节点资源或使用 HPA
kubectl scale node <node-name> --cpu=4
```
*依据*：当前节点 CPU 资源不足，需扩展资源以满足调度需求。

**2. [可选] 调整 Pod 的 CPU 请求（requests）**
```bash
kubectl set resources pod/rc-pending-insufficient-cpu -n aiops-e2e --requests=cpu=0.5
```
*依据*：如果 Pod 的 CPU 请求过高，适当调整以匹配可用资源。

**3. [可选] 检查 Pod 的 CPU 限制（limits）**
```bash
kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o jsonpath='{.spec.containers[*].resources.limits.cpu}'
```
*目的*：确认 Pod 的 CPU 限制是否设置过高。

### 后续优化

1. **资源监控**：部署 Prometheus 并配置 CPU 使用率监控，避免类似问题重复发生。
2. **自动扩缩容**：配置 HPA（Horizontal Pod Autoscaler）以根据负载动态调整资源。
3. **资源评估**：使用 `kubectl describe pod` 或 `kubectl get pod -o yaml` 评估 Pod 的资源需求，确保与集群资源匹配。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e` | STATUS: Running |
| 2. 检查 CPU 使用率 | Prometheus 查询 `container_cpu_usage_seconds_total` | CPU 使用率 < 80% |
| 3. 检查调度器事件 | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` | 无 `FailedScheduling` 事件 |

---

## ⚠️ 注意事项

- 如果问题仍然存在，建议进一步检查节点 CPU 使用率和调度策略。
- 如果集群使用污点（Taint）或节点选择器（nodeSelector），请确认 Pod 的 toleration 和 nodeSelector 配置是否匹配。
- 考虑启用调度器预调度（Preemption）功能，以提升资源利用率。

---

## 📊 性能统计

├─ 总耗时: 6.5m
├─ 问题定位: 76.2s (19%) ✅
├─ 证据链采集: 105.6s (27%) ✅
├─ 根因分析: 78.5s (20%) ✅
├─ 汇总总结: 132.3s (34%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 11 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 11 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
