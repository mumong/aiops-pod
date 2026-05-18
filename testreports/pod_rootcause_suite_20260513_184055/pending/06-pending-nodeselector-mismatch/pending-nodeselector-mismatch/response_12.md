======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 9a2330942dab4787]

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
rc-pending-nodeselector   0/1     Pending   0          28m   <none>   <none>   
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
28m                 Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 n
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
creationTimestamp: 2026-05-13T20:39:53Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] {
  "layer": "L1",
  "derived_layer": "L1",
  "layers": [
    "L1"
  ],
  "layer_name": "PendingUnschedulable",
  "confidence": 0.95,
  "reasoning": "Pod rc-pending-nodeselector 处于 Pending 状态，Events 显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。Pod 的 nodeSelector 指定了 'aiops.e2e/nonexistent-node-label': 'true'，但集群中所有 Node 都没有这个标签。这表明调度失败是由于 nodeSelector 不匹配导致的，符合 L1 分类。",
  "abnormal_pods": [
    {
      "name": "rc-pending-nodeselector",
      "namespace": "aiops-e2e",
      "status": "Pending",
      "abnormal_type": "PendingUnschedulable"
    }
  ],
  "abnormal_groups": {
    "PendingUnschedulable": [
      {
        "name": "rc-pending-nodeselector",
        "namespace": "aiops-e2e"
      }
    ]
  },
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "PendingUnschedulable",
  "status_category": "PendingUnschedulable",
  "key_entities": {
    "Pod": "rc-pending-nodeselector",
    "Namespace": "aiops-e2e",
    "NodeSelector": "aiops.e2e/nonexistent-node-label=true"
  },
  "possible_scenarios": [
    "Pod rc-pending-nodeselector 的 nodeSelector 指定了 'aiops.e2e/nonexistent-node-label': 'true'，但集群中所有 Node 都没有这个标签，导致调度失败。",
    "需要检查 nodeSelector 是否正确，并确保集群中至少有一个 Node 拥有该标签。"
  ]
}
   ✅ [问题定位] 完成 (57.2s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[]
   entities=[]
   reasoning=Pod rc-pending-nodeselector 处于 Pending 状态，Events 显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。Pod 的 nodeSelector 指定了 'aiops.e2e/nonexistent-node-label': 'true'，但集群中所有 Node 都没有这个标签。这表明调度失败是由于 nodeSelector 不匹配导致的，符合 L1 分类。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "Pod rc-pending-nodeselector 处于 Pending 状态，Events 显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。Pod 的 nodeSelector 指定了 'aiops.e2e/nonexistent-node-label': 'true'，但集群中所有 Node 都没有这个标签。这表明调度失败是由于 nodeSelector 不匹配导致的，符合 L1 分类。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                28m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/9a2330942dab4787/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/9a2330942dab4787/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/9a2330942dab4787/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  30m                default-scheduler  0/3 nodes are available: 
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (1m 12.9s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 'rc-pending-nodeselector' 的详细信息以验证调度失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"确认 Pod 的 nodeSelector、affinity、taint 等配置是否导致调度失败","evidence_type":"configuration","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 'rc-pending-nodeselector' 的 Events 以确认调度失败的详细原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-nodeselector","tool_args":{"kind":"Event","namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-pending-nodeselector"},"purpose":"确认调度失败的详细原因，例如资源不足、标签不匹配等","evidence_type":"event","target_scope":"Events/aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"e3","description":"获取所有 Node 的详细信息以验证是否存在标签不匹配导致调度失败","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","tool_args":{"kind":"Node"},"purpose":"确认所有 Node 的标签是否匹配 Pod 的 nodeSelector 或 affinity 配置","evidence_type":"configuration","target_scope":"Nodes","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  30m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  15m (x3 over 25m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9a2330942dab4787/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9a2330942dab4787/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9a2330942dab4787/tools/001-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 6 个，匹配计划 3 个，未规划证据 3 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":3,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 'rc-pending-nodeselector' 的详细信息以验证调度失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"确认 Pod 的 nodeSelector、affinity、taint 等配置是否导致调度失败","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 'rc-pending-nodeselector' 的 Events 以确认调度失败的详细原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-nodeselector","purpose":"确认调度失败的详细原因，例如资源不足、标签不匹配等","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"e3","description":"获取所有 Node 的详细信息以验证是否存在标签不匹配导致调度失败","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","purpose":"确认所有 Node 的标签是否匹配 Pod 的 nodeSelector 或 affinity 配置","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod 'rc-pending-nodeselector' 的详细信息以验证调度... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_events | 获取异常 Pod 'rc-pending-nodeselector' 的 Events 以... | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pendi...` |
   | e3 | important | ✅ | kubectl_get_by_kind_in_cl... | 获取所有 Node 的详细信息以验证是否存在标签不匹配导致调度失败 | `kubectl get nodes -o json` |

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (3m 40.1s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector 的 nodeSelector 指定了 'aiops.e2e/nonexistent-node-label': 'true'，但集群中所有 Node 都没有这个标签，导致调度失败。
   confidence=95%
   causal_chain={"root_cause": "Pod rc-pending-nodeselector 的 nodeSelector 指定了 'aiops.e2e/nonexistent-node-label': 'true'，但集群中所有 Node 都没有这个标签。", "intermediate_causes": ["Pod rc-pending-nodeselector 处于 Pending 状态，Events 显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。", "Pod 的 nodeSelector 指定了 'aiops.e2e/nonexistent-node-label': 'true'，但集群中所有 Node 都没有这个标签。"], "direct_causes": ["Pod rc-pending-nodeselector 处于 Pending 状态，Events 显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。", "Pod 的 nodeSelector 指定了 'aiops.e2e/nonexistent-node-label': 'true'，但集群中所有 Node 都没有这个标签。"], "effects": ["Pod rc-pending-nodeselector 无法被调度到任何节点。", "Pod rc-pending-nodeselector 处于 Pending 状态。"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"id": "e1", "description": "获取异常 Pod 'rc-pending-nodeselector' 的详细信息以验证调度失败原因", "level": "critical", "value": "kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  30m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  15m (x3 over 25m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 node"}, {"id": "e2", "description": "获取异常 Pod 'rc-pending-nodeselector' 的 Events 以确认调度失败的详细原因", "level": "critical", "value": "kubectl_events 摘要:\n关键诊断行:\n28m                 Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n13m (x3 over 23m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for schedulin"}, {"id": "e3", "description": "获取所有 Node 的详细信息以验证是否存在标签不匹配导致调度失败", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Pending': 1, 'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS      RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                28m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type"}, {"id": "layer_1", "description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Pending': 1, 'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS      RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                28m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type"}, {"id": "layer_2", "description": "上游已验证工具结果: kubectl_get_by_name", "level": "important", "value": "NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS\nrc-pending-nodeselector   0/1     Pending   0          28m   <none>   <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"}, {"id": "layer_3", "description": "上游已验证工具结果: kubectl_events", "level": "important", "value": "kubectl_events 摘要:\n关键诊断行:\n28m                 Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n13m (x3 over 23m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for schedulin"}, {"id": "layer_4", "description": "上游已验证工具结果: kubectl_get_yaml", "level": "important", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSe"}, {"id": "layer_5", "description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubern"}], "evidence_analysis": [{"id": "e1", "description": "获取异常 Pod 'rc-pending-nodeselector' 的详细信息以验证调度失败原因", "level": "critical", "value": "kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  30m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  15m (x3 over 25m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 node"}, {"id": "e2", "description": "获取异常 Pod 'rc-pending-nodeselector' 的 Events 以确认调度失败的详细原因", "level": "critical", "value": "kubectl_events 摘要:\n关键诊断行:\n28m                 Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n13m (x3 over 23m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for schedulin"}, {"id": "e3", "description": "获取所有 Node 的详细信息以验证是否存在标签不匹配导致调度失败", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Pending': 1, 'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS      RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                28m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type"}, {"id": "layer_1", "description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Pending': 1, 'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS      RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                28m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type"}, {"id": "layer_2", "description": "上游已验证工具结果: kubectl_get_by_name", "level": "important", "value": "NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS\nrc-pending-nodeselector   0/1     Pending   0          28m   <none>   <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"}, {"id": "layer_3", "description": "上游已验证工具结果: kubectl_events", "level": "important", "value": "kubectl_events 摘要:\n关键诊断行:\n28m                 Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n13m (x3 over 23m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for schedulin"}, {"id": "layer_4", "description": "上游已验证工具结果: kubectl_get_yaml", "level": "important", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSe"}, {"id": "layer_5", "description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubern"}], "causal_chain": {"root_cause": "Pod rc-pending-nodeselector 的 nodeSelector 指定了 'aiops.e2e/nonexistent-node-label': 'true'，但集群中所有 Node 都没有这个标签。", "intermediate_causes": ["Pod rc-pending-nodeselector 处于 Pending 状态，Events 显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。", "Pod 的 nodeSelector 指定了 'aiops.e2e/nonexistent-node-label': 'true'，但集群中所有 Node 都没有这个标签。"], "direct_causes": ["Pod rc-pending-nodeselector 处于 Pending 状态，Events 显示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。", "Pod 的 nodeSelector 指定了 'aiops.e2e/nonexistent-node-label': 'true'，但集群中所有 Node 都没有这个标签。"], "effects": ["Pod rc-pending-nodeselector 无法被调度到任何节点。", "Pod rc-pending-nodeselector 处于 Pending 状态。"]}, "root_cause": "Pod rc-pending-nodeselector 的 nodeSelector 指定了 'aiops.e2e/nonexistent-node-label': 'true'，但集群中所有 Node 都没有这个标签，导致调度失败。", "root_cause_summary": "Pod rc-pending-nodeselector 的 nodeSelector 指定了 'aiops.e2e/nonexistent-node-label': 'true'，但集群中所有 Node 都没有这个标签，导致调度失败。", "confidence": 0.95, "confidence_reason": "有直接证据表明调度失败是由于 nodeSelector 不匹配导致的。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"id": "alternative_cause_1", "description": "资源不足导致无法调度"}], "limitations": "无", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector 的 nodeSelector 指定了 'aiops.e2e/nonexistent-node-label': 'true'，但集群中所有 Node 都没有这个标签，导致调度失败。
   置信度: 95%
   🔗 因果链:
     根本原因: Pod rc-pending-nodeselector 的 nodeSelector 指定了 'aiops.e2e/nonexistent-node-label': 'true'，但集群中所有 Node 都没有这个标签。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 9.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3717 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 6m 59.5s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | PendingUnschedulable |
| **兼容归因层** | L1 - 调度失败 |
| **问题分类** | nodeSelector 不匹配导致调度失败 |
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
| Node | <none> |
| 错误信息 | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | kubectl get pod | `STATUS: Pending, RESTARTS: 0` | Pod 处于调度失败状态 |
| 2 | Pod Events | kubectl events | `Warning FailedScheduling Pod/rc-pending-nodeselector 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 明确说明调度失败是由于 nodeSelector 不匹配 |
| 3 | Node 标签 | kubectl get node | 所有 Node 没有标签 `aiops.e2e/nonexistent-node-label` | nodeSelector 指定的标签不存在，导致无节点匹配 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 `Pending`，Events 明确指出 `nodeSelector 不匹配` → 与 Pod spec 中指定的标签不匹配。
- **证据链**：Pod 的 `nodeSelector` 指定了一个不存在的标签 → 无节点满足调度条件 → Pod 无法调度 → 状态为 `Pending`。

### 缺失证据（无）

| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | 无 | 无 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 的 nodeSelector 指定了 'aiops.e2e/nonexistent-node-label': 'true'，但集群中所有 Node 都没有这个标签。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 无节点满足 nodeSelector 条件 → 调度失败                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 调度器找不到匹配节点 → Pod 处于 Pending 状态                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-pending-nodeselector 处于 Pending 状态，Events 显示调度失败原因。 │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态为 Pending) 和证据 #2 (Events 显示 `nodeSelector 不匹配`)，问题的根本原因是 **Pod 的 `nodeSelector` 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label`**，导致调度器找不到匹配的节点，Pod 无法调度。

**置信度**：高 (95%)
- ✅ Events 明确指出 `nodeSelector 不匹配`
- ✅ Pod spec 确认了 nodeSelector 的设置
- ✅ 所有 Node 没有这个标签

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 删除或修改 nodeSelector 设置**
```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
```
*操作*：在 spec 中删除或修改 `nodeSelector: aiops.e2e/nonexistent-node-label: 'true'`，改为符合节点标签的值或移除该字段。

**2. [可选] 手动打上标签（如果需要该标签）**
```bash
kubectl label nodes <node-name> aiops.e2e/nonexistent-node-label=true
```
*目的*：如果该标签是应用运行的必要条件，可在节点上添加该标签以满足调度需求。

### 后续优化

1. **标签管理规范**：确保 nodeSelector 使用的标签在节点上真实存在，避免因标签错误导致调度失败。
2. **调度策略校验**：在生产环境中，建议使用 `nodeAffinity` 替代 `nodeSelector` 以获得更灵活的调度策略。
3. **自动化监控**：配置调度失败告警，及时发现调度问题。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查调度器事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 无 FailedScheduling 事件 |
| 3. 检查 nodeSelector 是否生效 | 查看 Pod spec | `nodeSelector` 字段已修改或删除 |

---

## ⚠️ 注意事项

- 如果 nodeSelector 是测试或开发环境的临时设置，建议删除或使用真实存在的标签。
- 如果该标签是业务逻辑的一部分，建议评估是否需要添加标签到节点或调整调度策略。
- 如果 Pod 依赖其他调度策略（如 affinity、taint），也需一并检查。

---

## 📊 性能统计

├─ 总耗时: 7.0m
├─ 问题定位: 57.2s (14%) ✅
├─ 证据链采集: 72.9s (17%) ✅
├─ 根因分析: 220.1s (52%) ✅
├─ 汇总总结: 69.3s (17%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 8 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 8 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
