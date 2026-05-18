======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 723dc13cc4224c75]

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
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          32s   <none>   <none>   
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  34s   default-scheduler  0/3 nodes are available: 3 node(s) did
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          37s   <none>   <none>   
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  41s   default-scheduler  0/3 nodes are available: 3 node(s) did
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (56.3s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '节点未匹配 Pod 的 node affinity/selector', 'probability': '高', 'reason': "事件原文明确指出 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在一个处于 Pending 状态的 Pod (rc-pending-nodeselector)，其异常类型为 PendingUnschedulable，这表明调度失败。根据事件信息，调度失败的原因是节点未匹配 Pod 的 node affinity/selector。这属于调度或节点 kubelet 层级的问题，因此归类为 L1 层级。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "", "confidence": 0.5, "reasoning": "当前环境中存在一个处于 Pending 状态的 Pod (rc-pending-nodeselector)，其异常类型为 PendingUnschedulable，这表明调度失败。根据事件信息，调度失败的原因是节点未匹配 Pod 的 node affinity/selector。这属于调度或节点 kubelet 层级的问题，因此归类为 L1 层级。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "节点未匹配 Pod 的 node affinity/selector", "probability": "高", "reason": "事件原文明确指出 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                26s    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/723dc13cc4224c75/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/723dc13cc4224c75/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/723dc13cc4224c75/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  3m11s  default-scheduler  0/3 nodes are available: 3 node(s) di
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
3m14s       Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [证据链采集] 已采集证据：
1. `kubectl_describe` 显示 Pod `rc-pending-nodeselector` 的调度失败原因为节点未匹配 Pod 的 node affinity/selector。
2. `kubectl_events` 显示调度失败事件，原因与上述一致。
3. `kubectl_get_by_kind_in_cluster` 显示所有节点都处于 Ready 状态，但未匹配 Pod 的 node affinity/selector。

结论：
当前 Pod 无法调度是因为集群中没有节点满足其 node affinity/selector 的要求。需要检查 Pod 的 node affinity/selector 配置，并确保集群中有节点满足这些条件。
   ✅ [证据链采集] 完成 (2m 3.6s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"evidence-pod-describe","description":"获取 Pod 'rc-pending-nodeselector' 的详细信息，以确认其调度失败的具体原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-pending-nodeselector","kind":"Pod"},"purpose":"验证 Pod 的 FailedScheduling 事件和调度失败原因","evidence_type":"Pod Describe","target_scope":"Pod","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"evidence-pod-events","description":"获取 Pod 'rc-pending-nodeselector' 的事件信息，以确认调度失败的具体原因。","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-nodeselector","tool_args":{"namespace":"aiops-e2e","name":"rc-pending-nodeselector","kind":"Pod"},"purpose":"验证 Pod 的 FailedScheduling 事件和调度失败原因","evidence_type":"Pod Events","target_scope":"Pod","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"evidence-node-list","description":"列出所有节点，以确认是否有节点匹配 Pod 的 node affinity/selector。","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes","tool_args":{"kind":"Node"},"purpose":"验证节点状态和标签，以确认是否有节点匹配 Pod 的 node affinity/selector","evidence_type":"Node List","target_scope":"Node","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  3m11s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/723dc13cc4224c75/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/723dc13cc4224c75/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/723dc13cc4224c75/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n3m14s       Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/723dc13cc4224c75/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/723dc13cc4224c75/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/723dc13cc4224c75/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/723dc13cc4224c75/tools/003-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/723dc13cc4224c75/tools/003-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/723dc13cc4224c75/tools/003-evidence-kubectl_get_by_kind_in_cluster.summary.txt"}],"llm_analysis":"已采集证据：\n1. `kubectl_describe` 显示 Pod `rc-pending-nodeselector` 的调度失败原因为节点未匹配 Pod 的 node affinity/selector。\n2. `kubectl_events` 显示调度失败事件，原因与上述一致。\n3. `kubectl_get_by_kind_in_cluster` 显示所有节点都处于 Ready 状态，但未匹配 Pod 的 node affinity/selector。\n\n结论：\n当前 Pod 无法调度是因为集群中没有节点满足其 node affinity/selector 的要求。需要检查 Pod 的 node affinity/selector 配置，并确保集群中有节点满足这些条件。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 9 个，匹配计划 3 个，未规划证据 6 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":9,"matched_tool_count":3,"unplanned_tool_count":6,"evidence_inventory":[{"id":"evidence-pod-describe","description":"获取 Pod 'rc-pending-nodeselector' 的详细信息，以确认其调度失败的具体原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"验证 Pod 的 FailedScheduling 事件和调度失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"evidence-pod-events","description":"获取 Pod 'rc-pending-nodeselector' 的事件信息，以确认调度失败的具体原因。","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-nodeselector","purpose":"验证 Pod 的 FailedScheduling 事件和调度失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"evidence-node-list","description":"列出所有节点，以确认是否有节点匹配 Pod 的 node affinity/selector。","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes","purpose":"验证节点状态和标签，以确认是否有节点匹配 Pod 的 node affinity/selector","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | evidence-pod-... | critical | ✅ | kubectl_describe | 获取 Pod 'rc-pending-nodeselector' 的详细信息，以确认其调度... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | evidence-pod-... | important | ✅ | kubectl_events | 获取 Pod 'rc-pending-nodeselector' 的事件信息，以确认调度失... | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pendi...` |
   | evidence-node... | important | ✅ | kubectl_get_by_kind_in_cl... | 列出所有节点，以确认是否有节点匹配 Pod 的 node affinity/selector。 | `kubectl get nodes` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (2m 18.2s)
   📤 → 下游数据: root_cause=Pod 'rc-pending-nodeselector' 无法调度的原因是集群中没有节点满足其 node affinity/selector 的要求。根据 kubectl_describe 和 kubectl_events 的输出，调度失败事件显示 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。此外，kubectl_get_by_kind_in_cluster 的输出显示所有节点都处于 Ready 状态，但未匹配 Pod 的 node affinity/selector。需要检查 Pod 的 node affinity/selector 配置，并确保集群中有节点满足这些条件。
   confidence=95%
   causal_chain={"root_cause": "节点未匹配 Pod 的 node affinity/selector", "intermediate_causes": ["Pod 'rc-pending-nodeselector' 的 node affinity/selector 配置要求特定的节点标签，但集群中没有节点满足这些要求。", "调度器无法找到匹配的节点，导致 Pod 无法调度。"], "immediate_causes": ["Pod 'rc-pending-nodeselector' 的调度失败事件显示 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。", "所有节点都处于 Ready 状态，但未匹配 Pod 的 node affinity/selector。"], "symptoms": ["Pod 'rc-pending-nodeselector' 的状态为 Pending。", "Pod 'rc-pending-nodeselector' 的调度失败事件显示节点未匹配 node affinity/selector。"]}
   rca_analysis={"phenomenon": "Pod 'rc-pending-nodeselector' 无法调度", "evidence_inventory": [{"id": "evidence-pod-describe", "description": "获取 Pod 'rc-pending-nodeselector' 的详细信息，以确认其调度失败的具体原因。", "level": "critical", "value": "kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  3m11s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:"}, {"id": "evidence-pod-events", "description": "获取 Pod 'rc-pending-nodeselector' 的事件信息，以确认调度失败的具体原因。", "level": "important", "value": "kubectl_events 摘要:\n关键诊断行:\n3m14s       Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.."}, {"id": "evidence-node-list", "description": "列出所有节点，以确认是否有节点匹配 Pod 的 node affinity/selector。", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubern"}, {"id": "layer_1", "description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Pending': 1, 'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS      RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                26s    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type"}, {"id": "layer_3", "description": "上游已验证工具结果: kubectl_describe", "level": "important", "value": "kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  34s   default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:"}, {"id": "layer_5", "description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubern"}, {"id": "layer_6", "description": "上游已验证工具结果: kubectl_describe", "level": "important", "value": "kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  41s   default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:"}], "evidence_analysis": [{"id": "evidence-pod-describe", "description": "Pod 'rc-pending-nodeselector' 的详细信息显示调度失败的原因是节点未匹配 Pod 的 node affinity/selector。", "level": "critical", "value": "kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  3m11s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:"}, {"id": "evidence-pod-events", "description": "Pod 'rc-pending-nodeselector' 的事件信息显示调度失败的原因是节点未匹配 Pod 的 node affinity/selector。", "level": "important", "value": "kubectl_events 摘要:\n关键诊断行:\n3m14s       Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.."}, {"id": "evidence-node-list", "description": "所有节点都处于 Ready 状态，但未匹配 Pod 的 node affinity/selector。", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubern"}], "causal_chain": {"root_cause": "节点未匹配 Pod 的 node affinity/selector", "intermediate_causes": ["Pod 'rc-pending-nodeselector' 的 node affinity/selector 配置要求特定的节点标签，但集群中没有节点满足这些要求。", "调度器无法找到匹配的节点，导致 Pod 无法调度。"], "immediate_causes": ["Pod 'rc-pending-nodeselector' 的调度失败事件显示 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。", "所有节点都处于 Ready 状态，但未匹配 Pod 的 node affinity/selector。"], "symptoms": ["Pod 'rc-pending-nodeselector' 的状态为 Pending。", "Pod 'rc-pending-nodeselector' 的调度失败事件显示节点未匹配 node affinity/selector。"]}, "root_cause": "Pod 'rc-pending-nodeselector' 无法调度的原因是集群中没有节点满足其 node affinity/selector 的要求。根据 kubectl_describe 和 kubectl_events 的输出，调度失败事件显示 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。此外，kubectl_get_by_kind_in_cluster 的输出显示所有节点都处于 Ready 状态，但未匹配 Pod 的 node affinity/selector。需要检查 Pod 的 node affinity/selector 配置，并确保集群中有节点满足这些条件。", "root_cause_summary": "Pod 'rc-pending-nodeselector' 无法调度的原因是集群中没有节点满足其 node affinity/selector 的要求。根据 kubectl_describe 和 kubectl_events 的输出，调度失败事件显示 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。此外，kubectl_get_by_kind_in_cluster 的输出显示所有节点都处于 Ready 状态，但未匹配 Pod 的 node affinity/selector。需要检查 Pod 的 node affinity/selector 配置，并确保集群中有节点满足这些条件。", "confidence": 0.95, "confidence_reason": "有直接证据表明调度失败的原因是节点未匹配 Pod 的 node affinity/selector。kubectl_describe 和 kubectl_events 的输出明确指出了这一点，且 kubectl_get_by_kind_in_cluster 的输出显示所有节点都处于 Ready 状态，但未匹配 Pod 的 node affinity/selector。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [], "limitations": "当前证据未显示 Pod 的 node affinity/selector 具体配置，因此无法进一步验证集群中是否有节点满足这些条件。", "llm_raw_analysis": "已采集证据显示 Pod 'rc-pending-nodeselector' 的调度失败原因为节点未匹配 Pod 的 node affinity/selector。kubectl_describe 和 kubectl_events 的输出明确指出了这一点，且 kubectl_get_by_kind_in_cluster 的输出显示所有节点都处于 Ready 状态，但未匹配 Pod 的 node affinity/selector。需要检查 Pod 的 node affinity/selector 配置，并确保集群中有节点满足这些条件。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-pending-nodeselector' 无法调度的原因是集群中没有节点满足其 node affinity/selector 的要求。根据 kubectl_describe 和 kubectl_events 的输出，调度失败事件显示 0/3 nodes are available:...
   置信度: 95%
   🔗 因果链:
     根本原因: 节点未匹配 Pod 的 node affinity/selector


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 26.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4219 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 6m 44.5s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
---
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **Pod异常状态** | PendingUnschedulable |
| **兼容归因层** | L1 - 调度或节点 kubelet 层级 |
| **问题分类** | 调度失败（node affinity/selector 不匹配） |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/3 (100%) |

---

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-pending-nodeselector |
| Namespace | aiops-e2e |
| 错误信息 | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` |

当前集群中有一个 Pod（`rc-pending-nodeselector`）处于 `Pending` 状态，异常类型为 `PendingUnschedulable`，表明调度失败。具体原因是 Pod 的 node affinity/selector 与集群中所有节点的标签不匹配，导致调度器无法将该 Pod 分配到任何节点上运行。

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 事件 | `kubectl describe pod rc-pending-nodeselector` | `Warning  FailedScheduling  34s   default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | Pod 无法调度，因为所有节点都不满足其 node affinity/selector 条件 |
| 2 | Pod 信息 | `kubectl get pod rc-pending-nodeselector` | `STATUS: Pending, RESTARTS: 0` | Pod 处于调度失败状态 |
| 3 | 节点状态 | `kubectl get nodes` | `STATUS: Ready, ROLES: control-plane`（共 3 个节点） | 所有节点状态正常，但未匹配 Pod 的 node affinity/selector |

### 证据关联分析
- **证据 #1 印证**：`FailedScheduling` 事件明确指出调度失败原因是 node affinity/selector 不匹配。
- **证据 #2 + #3 印证**：Pod 无法调度，而所有节点状态正常，说明调度失败不是因为节点状态问题，而是标签不匹配。

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 的 node affinity/selector 配置 | critical | 无法确认具体标签要求，无法验证是否有节点匹配 |

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 的 node affinity/selector 配置与集群中所有节点的标签不匹配    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 调度器尝试将 Pod 分配到满足 node affinity/selector 的节点，但没有可用节点 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 PendingUnschedulable，无法调度，持续处于 Pending 状态  │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1（`FailedScheduling` 事件）和证据 #3（节点状态正常），问题的根本原因是 **Pod 的 node affinity/selector 配置与集群中所有节点的标签不匹配**，导致调度器无法找到合适的节点运行该 Pod。

**置信度**：高 (95%)
- ✅ 事件信息明确指出调度失败原因是 node affinity/selector 不匹配
- ✅ 节点状态正常，排除节点不可用问题
- ⚠️ 缺少 Pod 的 node affinity/selector 配置，无法进一步验证具体标签要求

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 检查并更新 Pod 的 node affinity/selector 配置**
```bash
kubectl get deployment/rc-pending-nodeselector -n aiops-e2e -o yaml
```
*依据*：确认当前的 nodeSelector 或 affinity 配置，与节点标签进行比对。

**2. [优先] 检查节点标签**
```bash
kubectl get nodes --show-labels
```
*依据*：确认节点上是否存在 Pod 所需的标签。

**3. [可选] 修改 Pod 的 nodeSelector/affinity 配置**
```bash
kubectl set node-selector deployment/rc-pending-nodeselector -n aiops-e2e key=value
```
*依据*：将 Pod 的 nodeSelector 设置为与集群中一个或多个节点匹配的标签。

**4. [可选] 添加缺失标签到节点**
```bash
kubectl label nodes <node-name> key=value
```
*依据*：如果节点缺少 Pod 所需标签，可以手动添加。

### 后续优化
1. **标签管理**：统一管理节点标签，确保调度需求与节点标签一致。
2. **调度策略验证**：在部署前验证 Pod 的 nodeSelector/affinity 配置是否匹配目标节点。
3. **监控调度失败事件**：设置监控告警，及时发现调度失败事件。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查调度事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 无 FailedScheduling 事件 |
| 3. 检查节点标签 | `kubectl get nodes --show-labels` | 包含 Pod 所需的标签 |

---

## ⚠️ 注意事项
- 如果当前 Pod 的 nodeSelector/affinity 配置是业务需求，但集群中确实没有满足条件的节点，建议扩展集群或添加新节点。
- 如果是测试/开发环境，可临时将 nodeSelector 设置为 `node-role.kubernetes.io/control-plane` 以调度到 control-plane 节点（不推荐生产环境）。
- 请确保标签更新后，重启 Pod 以触发重新调度。

---

---

## 📊 性能统计

├─ 总耗时: 6.7m
├─ 问题定位: 56.3s (14%) ✅
├─ 证据链采集: 123.6s (31%) ✅
├─ 根因分析: 138.2s (34%) ✅
├─ 汇总总结: 86.5s (21%) ✅
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
