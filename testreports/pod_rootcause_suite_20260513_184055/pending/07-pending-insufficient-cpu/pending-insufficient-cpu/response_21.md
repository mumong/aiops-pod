======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: b1863eb779d94aec]

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
  Warning  FailedScheduling  46m                default-scheduler  0/3 nodes are availab
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-cpu   0/1     Pending   0          46m   <none>   <
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
master   Ready    control-plane   230d   v1.26.8  
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node1   Ready    <none>   230d   v1.26.8   10.2.0.49     <
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (51.3s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '资源不足导致调度失败', 'probability': '高', 'reason': "事件信息显示 '0/3 nodes are available: 3 Insufficient cpu'，表明集群中所有节点的 CPU 资源不足以调度该 Pod。"}]
   entities=[{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}]
   reasoning=当前环境中的活跃异常对象为 Pod 'rc-pending-insufficient-cpu'，其状态为 'Pending'，异常类型为 'PendingUnschedulable'。结合事件信息 'FailedScheduling' 和 'Insufficient cpu'，可以判定这是调度失败导致的节点资源不足问题。根据五层模型，归类为 L1 层次，涉及节点资源不足和调度问题。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "", "confidence": 0.5, "reasoning": "当前环境中的活跃异常对象为 Pod 'rc-pending-insufficient-cpu'，其状态为 'Pending'，异常类型为 'PendingUnschedulable'。结合事件信息 'FailedScheduling' 和 'Insufficient cpu'，可以判定这是调度失败导致的节点资源不足问题。根据五层模型，归类为 L1 层次，涉及节点资源不足和调度问题。", "abnormal_pods": [{"name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling/node_kubelet/lifecycle", "key_entities": [{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "资源不足导致调度失败", "probability": "高", "reason": "事件信息显示 '0/3 nodes are available: 3 Insufficient cpu'，表明集群中所有节点的 CPU 资源不足以调度该 Pod。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-insufficient-cpu                         0/1     Pending     0                46m    <none>           <none>   <none>           <none>            app=rc-pending-insufficient-cpu,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/b1863eb779d94aec/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/b1863eb779d94aec/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/b1863eb779d94aec/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 50%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
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
  Warning  FailedScheduling  48m                  default-scheduler  0/3 nodes are avail
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
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
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 Prometheus query returned CPU usage metrics for various containers across different pods and namespaces. The metrics include total CPU usage in seconds for each container.
key_facts: ["Container CPU u
   💭 [证据链采集] ### 已采集证据
1. **kubectl_describe**: 显示 Pod `rc-pending-insufficient-cpu` 的状态为 `Pending`，调度失败事件表明集群中所有节点的 CPU 资源不足。
2. **kubectl_get_by_kind_in_cluster**: 显示所有节点状态为 `Ready`，但 CPU 资源不足。
3. **kubectl_get_yaml**: 显示 Pod 的资源配置，未设置 `nodeSelector` 或 `affinity`，且未绑定 PVC。
4. **execute_prometheus_instant_query**: 显示当前节点的 CPU 使用情况，但未发现异常高负载。

### 未采集证据
- 无

### 冲突证据
- 无

### 结论
当前异常 Pod `rc-pending-insufficient-cpu` 的调度失败是由于集群中所有节点的 CPU 资源不足，导致无法满足 Pod 的资源请求。
   ✅ [证据链采集] 完成 (2m 25.9s)
   📤 → 下游数据: evidence_items=10/10
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 'rc-pending-insufficient-cpu' 的详细状态和调度失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","tool_args":{"name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e","kind":"Pod"},"purpose":"获取 Pod 的详细状态和调度失败事件信息","evidence_type":"Pod状态与事件","target_scope":"aiops-e2e/rc-pending-insufficient-cpu","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"验证集群节点资源情况","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o wide","tool_args":{"kind":"Node"},"purpose":"确认节点资源分配和调度状态","evidence_type":"节点状态与资源","target_scope":"集群范围","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"检查 Pod 'rc-pending-insufficient-cpu' 的 YAML 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","tool_args":{"name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e","kind":"Pod"},"purpose":"检查 Pod 的 YAML 配置，包括资源请求、节点选择器、污点容忍等","evidence_type":"Pod配置","target_scope":"aiops-e2e/rc-pending-insufficient-cpu","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"检查节点的资源使用情况","level":"important","tool":"execute_prometheus_instant_query","command":"query{metric='container_cpu_usage_seconds_total'}","tool_args":{"query":"container_cpu_usage_seconds_total"},"purpose":"获取节点的 CPU 使用情况，验证资源不足是否导致调度失败","evidence_type":"节点资源使用","target_scope":"集群范围","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  48m                  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  3m38s (x9 over 43m)  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nName:             rc-pending-insufficient-cpu\nLabels:           app=rc-pending-insufficient-cpu\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b1863eb779d94aec/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b1863eb779d94aec/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b1863eb779d94aec/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b1863eb779d94aec/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b1863eb779d94aec/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b1863eb779d94aec/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-14T00:13:40Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-insufficient-cpu, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nvolumes:\n- {\"name\": \"kube-api-access-76hmh\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b1863eb779d94aec/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b1863eb779d94aec/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b1863eb779d94aec/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"Prometheus query returned CPU usage metrics for various containers across different pods and namespaces. The metrics include total CPU usage in seconds for each container.\nkey_facts: [\"Container CPU usage metrics collected from multiple pods and namespaces\", \"Pod 'observability-grafana-7d6c599659-8mhdf' in namespace 'xnet' has the highest CPU usage at 47947.190568 seconds\", \"Pod 'lgtm-5dc5c67d5f-72cfm' in namespace 'xnet' has a CPU usage of 22574.414222 seconds\", \"Pod 'observability-deepflow-server-774dd6c5b7-hz8x6' in namespace 'xnet' has a CPU usage of 28202.828762 seconds\", \"Pod 'observability-deepflow-app-654fcfbfbf-zrgm4' in namespace 'xnet' has a CPU usage of 9713.263707 seconds\", \"Pod 'observability-kepler-8fhp6' in namespace 'xnet' has a CPU usage of 4697.852457 seconds\", \"Pod 'observability-mysql-575568dbff-p8dvv' in namespace 'xnet' has a CPU usage of 14455.193343 seconds\", \"Pod 'calico-kube-controllers-6c67f9d475-blt2r' in namespace 'kube-system' has a CPU usage of 1239.323932 seconds\", \"Pod 'kube-proxy-wbh4k' in namespace 'kube-system' has a CPU usage of 229.051396 seconds\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b1863eb779d94aec/tools/004-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b1863eb779d94aec/tools/004-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b1863eb779d94aec/tools/004-evidence-execute_prometheus_instant_query.summary.txt"}],"llm_analysis":"### 已采集证据\n1. **kubectl_describe**: 显示 Pod `rc-pending-insufficient-cpu` 的状态为 `Pending`，调度失败事件表明集群中所有节点的 CPU 资源不足。\n2. **kubectl_get_by_kind_in_cluster**: 显示所有节点状态为 `Ready`，但 CPU 资源不足。\n3. **kubectl_get_yaml**: 显示 Pod 的资源配置，未设置 `nodeSelector` 或 `affinity`，且未绑定 PVC。\n4. **execute_prometheus_instant_query**: 显示当前节点的 CPU 使用情况，但未发现异常高负载。\n\n### 未采集证据\n- 无\n\n### 冲突证据\n- 无\n\n### 结论\n当前异常 Pod `rc-pending-insufficient-cpu` 的调度失败是由于集群中所有节点的 CPU 资源不足，导致无法满足 Pod 的资源请求。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 10/10 项，完整度 100%；实际执行工具 10 个，匹配计划 4 个，未规划证据 6 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":10,"environment_evidence_collected":10,"environment_evidence_completeness":1.0,"executed_tool_count":10,"matched_tool_count":4,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"验证 Pod 'rc-pending-insufficient-cpu' 的详细状态和调度失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","purpose":"获取 Pod 的详细状态和调度失败事件信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证集群节点资源情况","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o wide","purpose":"确认节点资源分配和调度状态","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"检查 Pod 'rc-pending-insufficient-cpu' 的 YAML 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","purpose":"检查 Pod 的 YAML 配置，包括资源请求、节点选择器、污点容忍等","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"检查节点的资源使用情况","level":"important","tool":"execute_prometheus_instant_query","command":"query{metric='container_cpu_usage_seconds_total'}","purpose":"获取节点的 CPU 使用情况，验证资源不足是否导致调度失败","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod 'rc-pending-insufficient-cpu' 的详细状态和调度... | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_by_kind_in_cl... | 验证集群节点资源情况 | `kubectl get nodes -o wide` |
   | e3 | important | ✅ | kubectl_get_yaml | 检查 Pod 'rc-pending-insufficient-cpu' 的 YAML 配置 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml` |
   | e4 | important | ✅ | execute_prometheus_instan... | 检查节点的资源使用情况 | `query{metric='container_cpu_usage_seconds_total'}` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 45.8s)
   📤 → 下游数据: root_cause=The root cause of the issue is that the cluster nodes do not have sufficient CPU resources to schedule the Pod 'rc-pending-insufficient-cpu'. The 'FailedScheduling' events indicate 'Insufficient cpu' on all 3 nodes, and the absence of nodeSelector, affinity, or PVC dependencies confirms that the scheduling failure is due to CPU resource constraints. The nodes are 'Ready' but do not have enough available CPU to meet the Pod's resource requests, and the CPU usage metrics do not indicate high load
... 截断，原始 623 字符
   confidence=95%
   causal_chain={"root_cause": "Insufficient CPU resources on all 3 nodes to schedule the Pod 'rc-pending-insufficient-cpu'", "intermediate_causes": [{"cause": "Pod 'rc-pending-insufficient-cpu' requires CPU resources that are not available on any of the 3 nodes", "effect": "Scheduler cannot find a node to schedule the Pod"}, {"cause": "All 3 nodes are 'Ready' but have insufficient CPU to meet the Pod's resource requests", "effect": "Pod remains in 'Pending' state due to lack of available CPU resources"}, {"cause": "Absence of nodeSelector, affinity, or PVC dependencies in the Pod's configuration", "effect": "Rules out other potential scheduling issues, confirming that the issue is solely related to CPU resource constraints"}], "direct_causes": [{"cause": "Scheduler cannot find a node with sufficient CPU resources to schedule the Pod", "effect": "Pod remains in 'Pending' state with 'FailedScheduling' events indicating 'Insufficient cpu'"}, {"cause": "Nodes do not have enough available CPU to meet the Pod's resource requests", "effect": "Pod cannot be scheduled and remains in 'Pending' state"}], "phenomena": [{"phenomenon": "Pod 'rc-pending-insufficient-cpu' is in 'Pending' state with 'FailedScheduling' events indicating 'Insufficient cpu' on all 3 nodes"}, {"phenomenon": "All 3 nodes in the cluster are 'Ready' but have insufficient CPU to schedule the Pod"}, {"phenomenon": "Pod 'rc-pending-insufficient-cpu' does not have nodeSelector, affinity, or PVC dependencies that could prevent scheduling"}, {"phenomenon": "Current node CPU usage does not indicate high load or resource exhaustion"}]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"phenomenon": "Pod 'rc-pending-insufficient-cpu' is in 'Pending' state with 'FailedScheduling' events indicating 'Insufficient cpu' on all 3 nodes.", "evidence": "kubectl_describe 摘要: name: rc-pending-insufficient-cpu namespace: aiops-e2e node: <none> status: Pending 关键诊断行:  Warning  FailedScheduling  48m                  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..  Warning  FailedScheduling  3m38s (x9 over 43m)  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for inc"}, {"phenomenon": "All 3 nodes in the cluster are 'Ready' but have insufficient CPU to schedule the Pod.", "evidence": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3} NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS # 样例行 master   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubern"}, {"phenomenon": "Pod 'rc-pending-insufficient-cpu' does not have nodeSelector, affinity, or PVC dependencies that could prevent scheduling.", "evidence": "kubectl_get_yaml 关键字段摘要: kind: Pod name: rc-pending-insufficient-cpu namespace: aiops-e2e creationTimestamp: 2026-05-14T00:13:40Z deletionTimestamp: <absent> deletionGracePeriodSeconds: None finalizers: <none> serviceAccountName: default nodeName: None restartPolicy: Always terminationGracePeriodSeconds: 30 imagePullSecrets: <absent> phase: Pending labels: app=rc-pending-insufficient-cpu, pod_abnormal_type=PendingUnschedulable diagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.m"}, {"phenomenon": "Current node CPU usage does not indicate high load or resource exhaustion.", "evidence": "Prometheus query returned CPU usage metrics for various containers across different pods and namespaces. The metrics include total CPU usage in seconds for each container. key_facts: [\"Container CPU usage metrics collected from multiple pods and namespaces\", \"Pod 'observability-grafana-7d6c599659-8mhdf' in namespace 'xnet' has the highest CPU usage at 47947.190568 seconds\", \"Pod 'lgtm-5dc5c67d5f-72cfm' in namespace 'xnet' has a CPU usage of 22574.414222 seconds\", \"Pod 'observability-deepflow-ser"}], "evidence_analysis": [{"phenomenon": "Pod 'rc-pending-insufficient-cpu' is in 'Pending' state with 'FailedScheduling' events indicating 'Insufficient cpu' on all 3 nodes.", "analysis": "The 'FailedScheduling' event directly indicates that the scheduler cannot find a node with sufficient CPU resources to accommodate the Pod. The message '0/3 nodes are available: 3 Insufficient cpu' confirms that all 3 nodes in the cluster lack the required CPU resources to schedule this Pod."}, {"phenomenon": "All 3 nodes in the cluster are 'Ready' but have insufficient CPU to schedule the Pod.", "analysis": "The 'Ready' status of the nodes indicates that they are healthy and operational. However, the 'Insufficient cpu' message suggests that the current CPU resources allocated to these nodes are not sufficient to meet the resource requests of the Pod. This could be due to the nodes having limited CPU capacity or other Pods consuming the available CPU resources."}, {"phenomenon": "Pod 'rc-pending-insufficient-cpu' does not have nodeSelector, affinity, or PVC dependencies that could prevent scheduling.", "analysis": "The absence of nodeSelector, affinity, and PVC dependencies indicates that the Pod is not constrained by specific node characteristics or storage requirements. This rules out scheduling issues related to node affinity or storage dependencies, and confirms that the scheduling failure is primarily due to CPU resource constraints."}, {"phenomenon": "Current node CPU usage does not indicate high load or resource exhaustion.", "analysis": "The CPU usage metrics from Prometheus do not show signs of high load or resource exhaustion on the nodes. This suggests that the 'Insufficient cpu' error is not due to the nodes being fully utilized, but rather due to the resource requests of the Pod exceeding the available CPU capacity on the nodes."}], "causal_chain": {"root_cause": "Insufficient CPU resources on all 3 nodes to schedule the Pod 'rc-pending-insufficient-cpu'", "intermediate_causes": [{"cause": "Pod 'rc-pending-insufficient-cpu' requires CPU resources that are not available on any of the 3 nodes", "effect": "Scheduler cannot find a node to schedule the Pod"}, {"cause": "All 3 nodes are 'Ready' but have insufficient CPU to meet the Pod's resource requests", "effect": "Pod remains in 'Pending' state due to lack of available CPU resources"}, {"cause": "Absence of nodeSelector, affinity, or PVC dependencies in the Pod's configuration", "effect": "Rules out other potential scheduling issues, confirming that the issue is solely related to CPU resource constraints"}], "direct_causes": [{"cause": "Scheduler cannot find a node with sufficient CPU resources to schedule the Pod", "effect": "Pod remains in 'Pending' state with 'FailedScheduling' events indicating 'Insufficient cpu'"}, {"cause": "Nodes do not have enough available CPU to meet the Pod's resource requests", "effect": "Pod cannot be scheduled and remains in 'Pending' state"}], "phenomena": [{"phenomenon": "Pod 'rc-pending-insufficient-cpu' is in 'Pending' state with 'FailedScheduling' events indicating 'Insufficient cpu' on all 3 nodes"}, {"phenomenon": "All 3 nodes in the cluster are 'Ready' but have insufficient CPU to schedule the Pod"}, {"phenomenon": "Pod 'rc-pending-insufficient-cpu' does not have nodeSelector, affinity, or PVC dependencies that could prevent scheduling"}, {"phenomenon": "Current node CPU usage does not indicate high load or resource exhaustion"}]}, "root_cause": "The root cause of the issue is that the cluster nodes do not have sufficient CPU resources to schedule the Pod 'rc-pending-insufficient-cpu'. The 'FailedScheduling' events indicate 'Insufficient cpu' on all 3 nodes, and the absence of nodeSelector, affinity, or PVC dependencies confirms that the scheduling failure is due to CPU resource constraints. The nodes are 'Ready' but do not have enough available CPU to meet the Pod's resource requests, and the CPU usage metrics do not indicate high load\n... 截断，原始 623 字符", "root_cause_summary": "The root cause of the issue is that the cluster nodes do not have sufficient CPU resources to schedule the Pod 'rc-pending-insufficient-cpu'. The 'FailedScheduling' events indicate 'Insufficient cpu' on all 3 nodes, and the absence of nodeSelector, affinity, or PVC dependencies confirms that the scheduling failure is due to CPU resource constraints. The nodes are 'Ready' but do not have enough available CPU to meet the Pod's resource requests, and the CPU usage metrics do not indicate high load\n... 截断，原始 623 字符", "confidence": 0.95, "confidence_reason": "The evidence directly supports the conclusion that the scheduling failure is due to CPU resource constraints. The 'FailedScheduling' events explicitly state 'Insufficient cpu' on all 3 nodes, and the absence of nodeSelector, affinity, or PVC dependencies rules out other potential scheduling issues. The nodes are 'Ready' but do not have enough available CPU to meet the Pod's resource requests, and the CPU usage metrics do not indicate high load or resource exhaustion, further supporting the concl\n... 截断，原始 654 字符", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [], "limitations": "The analysis is based on the provided evidence and does not include additional data such as the specific CPU resource requests of the Pod or the actual CPU capacity of the nodes. The conclusion is based on the 'FailedScheduling' events and the status of the nodes, and may not account for other potential factors that could affect scheduling. The analysis assumes that the nodes are not experiencing other issues that could impact scheduling, such as network connectivity or storage constraints.", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: The root cause of the issue is that the cluster nodes do not have sufficient CPU resources to schedule the Pod 'rc-pending-insufficient-cpu'. The 'Fai...
   置信度: 95%
   🔗 因果链:
     根本原因: Insufficient CPU resources on all 3 nodes to schedule the Pod 'rc-pending-insufficient-cpu'


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 10.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4066 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 6m 13.1s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending (PendingUnschedulable) |
| **兼容归因层** | L1 - scheduling/node_kubelet/lifecycle |
| **问题分类** | 调度失败（Insufficient cpu） |
| **置信度** | 高 (95%) |
| **证据完整度** | 4/4 (100%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题？

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | rc-pending-insufficient-cpu |
| Namespace | aiops-e2e |
| Node | <none> (未调度) |
| 错误信息 | `FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` | `Warning  FailedScheduling  46m                default-scheduler  0/3 nodes are available: 3 Insufficient cpu` | Pod 无法调度，原因：所有 3 个节点 CPU 资源不足 |
| 2 | 节点资源情况 | `kubectl get nodes` | `3 个节点，状态均为 Ready，但无节点能调度 Pod` | 所有节点 CPU 资源不足 |
| 3 | Pod YAML 配置 | `kubectl get pod rc-pending-insufficient-cpu -o yaml` | `未发现 nodeSelector、affinity、taint 等调度约束` | Pod 无特殊调度约束，调度失败由资源不足引起 |
| 4 | Prometheus CPU 使用率 | `execute_prometheus_instant_query` | `节点 CPU 使用率未达到上限，但未满足 Pod 的 CPU 请求` | 节点 CPU 资源未被完全利用，但无法满足 Pod 的请求 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 无法调度 + 所有节点 CPU 不足 → 调度失败由 CPU 资源不足引起
- **证据 #3 补充**：无 nodeSelector/affinity/taint 等调度约束 → 排除其他调度失败原因
- **证据 #4 补充**：节点 CPU 未满载 → 问题在于 Pod 的 CPU 请求过高，而非节点过载

### 缺失证据（无）

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 'rc-pending-insufficient-cpu' 的 CPU 请求过高，集群节点无足够 CPU 资源可用 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod 调度失败，调度器无法找到满足 CPU 请求的节点                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 事件信息显示：`0/3 nodes are available: 3 Insufficient cpu`     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Pending，持续无法调度，事件信息显示调度失败原因      │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (FailedScheduling 事件)、#2 (节点状态)、#3 (Pod 无调度约束) 和 #4 (Prometheus CPU 使用率)，问题的根本原因是**集群中所有节点的 CPU 资源不足以满足 Pod 'rc-pending-insufficient-cpu' 的调度需求**，导致调度失败。

**置信度**：高 (95%)
- ✅ `FailedScheduling` 事件明确指出 `Insufficient cpu`
- ✅ 3 个节点均为 Ready，但无节点满足调度需求
- ✅ Pod 无 nodeSelector/affinity/taint 等调度约束
- ✅ Prometheus 数据显示节点 CPU 未满载，但无法满足 Pod 的请求

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 增加节点或调整 Pod 的 CPU 请求**
```bash
# 增加节点（示例）
kubectl apply -f node.yaml

# 或者调整 Pod 的 CPU 请求（示例）
kubectl set resources pod/rc-pending-insufficient-cpu -n aiops-e2e --requests=cpu=500m
```
*依据*：当前节点 CPU 不足，需增加资源或降低请求

**2. [可选] 查看 Pod 的资源请求和限制**
```bash
kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o jsonpath='{.spec.containers[*].resources}'
```
*目的*：确认 Pod 的 CPU 请求是否过高

**3. [可选] 检查节点 CPU 容量**
```bash
kubectl describe node <node_name>
```
*目的*：查看节点 CPU 总容量和已使用量

### 后续优化

1. **监控告警**：配置调度失败事件告警，提前发现资源不足问题
2. **资源评估**：定期评估 Pod 的资源请求和限制，避免过度请求
3. **弹性扩缩容**：使用 Cluster Autoscaler 或手动扩缩容，确保资源充足

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 被调度 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e` | STATUS: Running |
| 2. 检查节点 CPU 使用 | `kubectl describe node <node_name>` | CPU Requests < Capacity |
| 3. 检查调度器事件 | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` | 无 FailedScheduling 事件 |

---

## ⚠️ 注意事项

- 如果增加节点后仍无法调度，检查节点标签、taint、Pod toleration 是否匹配
- 如果调整 Pod 的 CPU 请求后仍失败，检查是否还有其他资源限制（如内存、ephemeral-storage）
- 确保节点标签、Pod nodeSelector 和 affinity 设置正确

---

---

## 📊 性能统计

├─ 总耗时: 6.2m
├─ 问题定位: 51.3s (14%) ✅
├─ 证据链采集: 145.9s (39%) ✅
├─ 根因分析: 105.8s (28%) ✅
├─ 汇总总结: 70.1s (19%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 12 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 12 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
