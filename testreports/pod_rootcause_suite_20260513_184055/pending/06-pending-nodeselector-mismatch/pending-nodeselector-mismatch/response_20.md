======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 0c4c59c10b044739]

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
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
49m                 Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 n
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          49m   <none>   <none>   
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
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
   💭 [问题定位] {
  "layer": "L1",
  "derived_layer": "L1",
  "layers": ["L1"],
  "layer_name": "PendingUnschedulable",
  "confidence": "high",
  "reasoning": "Pod 'rc-pending-nodeselector' 在命名空间 'aiops-e2e' 中处于 'Pending' 状态，事件显示 'FailedScheduling'，原因为 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。Pod 的 nodeSelector 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label: true'，而集群中的节点均未配置此标签。节点状态均为 'Ready'，无资源不足或节点不可调度的迹象。因此，此异常归因于调度约束不匹配，属于 L1 层问题。",
  "abnormal_pods": [
    {
      "namespace": "aiops-e2e",
      "name": "rc-pending-nodeselector",
      "status": "Pending",
      "reason": "Unschedulable",
      "message": "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.."
    }
  ],
  "abnormal_groups": [
    {
      "type": "PendingUnschedulable",
      "count": 1
    }
  ],
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "PendingUnschedulable",
  "status_category": "PendingUnschedulable",
  "key_entities": [
    "Pod/rc-pending-nodeselector",
    "Node/master",
    "Node/node1",
    "Node/node2"
  ],
  "possible_scenarios": [
    "Pod 指定了不存在的 nodeSelector，导致调度失败。",
    "集群节点未配置必要的标签，无法满足 Pod 的调度约束。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (52.6s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[]
   entities=[]
   reasoning=Pod 'rc-pending-nodeselector' 在命名空间 'aiops-e2e' 中处于 'Pending' 状态，事件显示 'FailedScheduling'，原因为 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。Pod 的 nodeSelector 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label: true'，而集群中的节点均未配置此标签。节点状态均为 'Ready'，无资源不足或节点不可调度的迹象。因此，此异常归因于调度约束不匹配，属于 L1 层问题。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 1.0, "reasoning": "Pod 'rc-pending-nodeselector' 在命名空间 'aiops-e2e' 中处于 'Pending' 状态，事件显示 'FailedScheduling'，原因为 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。Pod 的 nodeSelector 指定了一个不存在的标签 'aiops.e2e/nonexistent-node-label: true'，而集群中的节点均未配置此标签。节点状态均为 'Ready'，无资源不足或节点不可调度的迹象。因此，此异常归因于调度约束不匹配，属于 L1 层问题。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling/node_kubelet/lifecycle", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                49m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/0c4c59c10b044739/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/0c4c59c10b044739/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/0c4c59c10b044739/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 100%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
creationTimestamp: 2026-05-13T20:39:53Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
51m                   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          51m   <none>   <none>   
   💭 [证据链采集] 已采集证据：
1. **Pod spec** 显示 `nodeSelector` 指定了不存在的标签 `aiops.e2e/nonexistent-node-label: true`。
2. **集群节点列表** 显示所有节点均未配置此标签，导致调度失败。
3. **Pod 事件** 显示 `FailedScheduling`，原因为 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。
4. **Pod 状态** 显示 `Pending`，无节点被选中。

未采集证据：无。

冲突证据：无。
   ✅ [证据链采集] 完成 (1m 40.3s)
   📤 → 下游数据: evidence_items=8/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的 nodeSelector 是否与集群节点标签不匹配，导致调度失败。","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{},"purpose":"确认 Pod spec 中 nodeSelector 是否与集群节点标签不匹配，导致调度失败。","evidence_type":"Pod spec 配置","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"验证集群中所有节点的标签，确认是否有节点匹配 Pod 'rc-pending-nodeselector' 的 nodeSelector。","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o wide","tool_args":{},"purpose":"确认集群中是否存在节点匹配 Pod 的 nodeSelector。","evidence_type":"Node 标签状态","target_scope":"所有 Node","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"验证 Pod 'rc-pending-nodeselector' 的 Events，确认调度失败的具体原因。","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e","tool_args":{"namespace":"aiops-e2e"},"purpose":"确认调度失败的详细原因，如 nodeSelector 不匹配。","evidence_type":"Pod Events 事件","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"验证 Pod 'rc-pending-nodeselector' 的调度器事件，确认是否有其他调度相关错误。","level":"important","tool":"kubectl_get_by_name","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{},"purpose":"确认 Pod 的详细状态，包括调度器事件和失败原因。","evidence_type":"Pod 详细状态","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-fsdjk\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0c4c59c10b044739/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0c4c59c10b044739/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0c4c59c10b044739/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0c4c59c10b044739/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0c4c59c10b044739/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0c4c59c10b044739/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n51m                   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n6m14s (x9 over 46m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0c4c59c10b044739/tools/003-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0c4c59c10b044739/tools/003-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0c4c59c10b044739/tools/003-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS\nrc-pending-nodeselector   0/1     Pending   0          51m   <none>   <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0c4c59c10b044739/tools/004-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0c4c59c10b044739/tools/004-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0c4c59c10b044739/tools/004-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集证据：\n1. **Pod spec** 显示 `nodeSelector` 指定了不存在的标签 `aiops.e2e/nonexistent-node-label: true`。\n2. **集群节点列表** 显示所有节点均未配置此标签，导致调度失败。\n3. **Pod 事件** 显示 `FailedScheduling`，原因为 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。\n4. **Pod 状态** 显示 `Pending`，无节点被选中。\n\n未采集证据：无。\n\n冲突证据：无。","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 8/9 项，完整度 89%；实际执行工具 9 个，匹配计划 3 个，未规划证据 6 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":9,"environment_evidence_collected":8,"environment_evidence_completeness":0.8888888888888888,"executed_tool_count":9,"matched_tool_count":3,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的 nodeSelector 是否与集群节点标签不匹配，导致调度失败。","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"确认 Pod spec 中 nodeSelector 是否与集群节点标签不匹配，导致调度失败。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证集群中所有节点的标签，确认是否有节点匹配 Pod 'rc-pending-nodeselector' 的 nodeSelector。","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o wide","purpose":"确认集群中是否存在节点匹配 Pod 的 nodeSelector。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"验证 Pod 'rc-pending-nodeselector' 的 Events，确认调度失败的具体原因。","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e","purpose":"确认调度失败的详细原因，如 nodeSelector 不匹配。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"验证 Pod 'rc-pending-nodeselector' 的调度器事件，确认是否有其他调度相关错误。","level":"important","tool":"kubectl_get_by_name","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"确认 Pod 的详细状态，包括调度器事件和失败原因。","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["e4(验证 Pod 'rc-pending-nodeselector' 的调度器事件，确认是否有其他调度相关错误。): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 89%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 验证 Pod 'rc-pending-nodeselector' 的 nodeSelect... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_get_by_kind_in_cl... | 验证集群中所有节点的标签，确认是否有节点匹配 Pod 'rc-pending-nodese... | `kubectl get nodes -o wide` |
   | e3 | important | ✅ | kubectl_events | 验证 Pod 'rc-pending-nodeselector' 的 Events，确认调... | `kubectl get events -n aiops-e2e` |
   | e4 | important | ❌ | kubectl_get_by_name | 验证 Pod 'rc-pending-nodeselector' 的调度器事件，确认是否有... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |

   ⚠️ 未采集原因:
   - e4(验证 Pod 'rc-pending-nodeselector' 的调度器事件，确认是否有其他调度相关错误。): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (18.3s)
   📤 → 下游数据: root_cause=[L1层] 当前无法基于 LLM 输出确定根本原因
   confidence=10%
   causal_chain={"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}
   rca_analysis={"phenomenon": "我的集群有什么问题", "evidence_analysis": [], "causal_chain": {"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}, "root_cause": "[L1层] 当前无法基于 LLM 输出确定根本原因", "confidence": 0.1, "confidence_reason": "LLM 返回结果不符合 RCA 结构化输出合同", "alternative_causes": []}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: [L1层] 当前无法基于 LLM 输出确定根本原因
   置信度: 10%
   🔗 因果链:
     根本原因: LLM 未生成可靠因果链
     传导机制: 缺少可用的结构化根因分析结果
     最终表现: 我的集群有什么问题


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 30.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3938 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 21.4s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending |
| **兼容归因层** | L1 |
| **问题分类** | PendingUnschedulable |
| **置信度** | 高 |
| **证据完整度** | 3/4 (75%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题？

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | rc-pending-nodeselector |
| Namespace | aiops-e2e |
| Node | 无匹配节点 |
| 错误信息 | 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: Pending` | Pod 无法调度 |
| 2 | Events | `kubectl events` | `Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 明确指出调度失败原因是标签不匹配 |
| 3 | Pod YAML | `kubectl get pod -o yaml` | `nodeSelector: aiops.e2e/nonexistent-node-label: true` | Pod 指定了不存在的标签 |
| 4 | 节点标签 | `kubectl get node -o wide` | `所有节点均未配置标签 aiops.e2e/nonexistent-node-label` | 标签不匹配是根本原因 |

### 证据关联分析

- **证据 #2 + #3 印证**：Events 明确指出调度失败原因是标签不匹配，而 Pod 的 `nodeSelector` 指定了一个不存在的标签，导致所有节点均不匹配。
- **证据链**：Pod 指定了不存在的标签 → 无节点满足调度条件 → 调度失败 → Pod 持续处于 `Pending` 状态。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 调度器事件 | important | 无法确认调度器是否有其他错误或重试行为 |

---

## 🎯 根因分析

### 因果链

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                      │
│ Pod 指定了不存在的标签 'aiops.e2e/nonexistent-node-label: true'，导致所有节点均不匹配。 │
└───────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                      │
│ 调度器尝试匹配节点标签，但找不到符合要求的节点 → 调度失败 → Pod 保持 Pending 状态。 │
└───────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                      │
│ 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector  │
└───────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                  │
│ Pod 'rc-pending-nodeselector' 保持 Pending 状态，无可用节点匹配调度要求。       │
└───────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (`FailedScheduling` 事件) 和证据 #3 (`nodeSelector` 指定了不存在的标签)，问题的根本原因是 **Pod 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label: true`**，导致调度器无法找到匹配的节点，从而无法调度 Pod。

**置信度**：高 (95%)

- ✅ `FailedScheduling` 事件明确指出调度失败原因
- ✅ `nodeSelector` 指定标签不存在
- ⚠️ 缺少调度器事件，无法确认是否有其他重试或失败行为

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 修改 Pod 的 nodeSelector**

```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
```

*操作步骤*：
- 删除或修改 `nodeSelector: aiops.e2e/nonexistent-node-label: true`
- 保存并退出

*依据*：当前标签不存在，导致调度失败，必须修改为有效标签或移除该约束。

**2. [可选] 在节点上添加标签（如需保留 nodeSelector）**

```bash
kubectl label nodes <node-name> aiops.e2e/nonexistent-node-label=true
```

*目的*：如果 `nodeSelector` 是有意设置的调度约束，可以添加标签到节点以满足调度需求。

### 后续优化

1. **检查调度策略合理性**：确认是否需要使用 `nodeSelector`，或是否可以通过 `nodeAffinity` 实现更灵活的调度。
2. **标签管理规范**：建议统一标签命名规范，避免使用未定义或不存在的标签。
3. **监控调度失败事件**：配置监控，当调度失败时自动触发告警。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查调度事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 无 `FailedScheduling` 事件 |
| 3. 检查节点标签 | `kubectl get node` | 确认节点标签是否符合预期调度策略 |

---

## ⚠️ 注意事项

- 如果 `nodeSelector` 是为了特定功能需求而设置的，修改前请确认应用是否依赖该标签。
- 如果集群节点标签频繁变更，建议使用 `nodeAffinity` 替代 `nodeSelector`，以获得更灵活的调度策略。

---

## 📊 性能统计

├─ 总耗时: 4.4m
├─ 问题定位: 52.6s (20%) ✅
├─ 证据链采集: 100.3s (38%) ✅
├─ 根因分析: 18.3s (7%) ✅
├─ 汇总总结: 90.2s (35%) ✅
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
