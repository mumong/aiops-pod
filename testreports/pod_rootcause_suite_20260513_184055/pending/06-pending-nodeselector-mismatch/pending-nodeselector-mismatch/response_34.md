======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: e0761182d0b3461d]

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
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  8m58s (x15 over 78m)  default-scheduler  0/3 nodes are availabl
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
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Node
name: master
namespace: None
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Node
name: node1
namespace: None
   💭 [问题定位] 调用工具: kubectl_get_yaml
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (34.5s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector 不匹配导致调度失败', 'probability': '高', 'reason': 'Pod 的 nodeSelector 设置了不存在的节点标签，导致无法匹配任何节点。'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}]
   reasoning=当前环境中有一个 Pod 处于 Pending 状态，其 pod_abnormal_type 为 PendingUnschedulable。根据 runbook 分析，Pod 无法调度的原因是 nodeSelector 不匹配。根据五层模型，PendingUnschedulable 属于 L1 层级，与调度或节点状态相关。因此，当前环境的异常层级定为 L1。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "", "confidence": 0.5, "reasoning": "当前环境中有一个 Pod 处于 Pending 状态，其 pod_abnormal_type 为 PendingUnschedulable。根据 runbook 分析，Pod 无法调度的原因是 nodeSelector 不匹配。根据五层模型，PendingUnschedulable 属于 L1 层级，与调度或节点状态相关。因此，当前环境的异常层级定为 L1。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "nodeSelector 不匹配导致调度失败", "probability": "高", "reason": "Pod 的 nodeSelector 设置了不存在的节点标签，导致无法匹配任何节点。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                84m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/e0761182d0b3461d/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/e0761182d0b3461d/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/e0761182d0b3461d/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 50%

📍 [证据链采集] 执行中...
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
   💭 [证据链采集] 已采集证据：
1. **Pod `rc-pending-nodeselector` 的 YAML 配置**：确认 `nodeSelector` 设置了 `aiops.e2e/nonexistent-node-label=true`，这是导致调度失败的关键配置。
2. **集群中所有节点的状态**：确认所有节点（master、node1、node2）的标签中均不存在 `aiops.e2e/nonexistent-node-label=true`，导致 Pod 无法找到匹配的节点。

**结论**：当前 Pod 无法调度的根本原因是其 `nodeSelector` 设置了不存在的标签 `aiops.e2e/nonexistent-node-label=true`，导致没有节点匹配。
   ✅ [证据链采集] 完成 (1m 1.5s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的 nodeSelector 是否匹配集群中任何节点","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"确认 Pod 的 nodeSelector 设置是否匹配任何节点的标签","evidence_type":"configuration","target_scope":"Pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"验证集群中所有节点的标签，确认是否有节点匹配 'rc-pending-nodeselector' 的 nodeSelector","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","tool_args":{"kind":"Node"},"purpose":"确认集群中是否存在节点匹配 Pod 的 nodeSelector 条件","evidence_type":"configuration","target_scope":"Node","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-fsdjk\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e0761182d0b3461d/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e0761182d0b3461d/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e0761182d0b3461d/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e0761182d0b3461d/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e0761182d0b3461d/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e0761182d0b3461d/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"}],"llm_analysis":"已采集证据：\n1. **Pod `rc-pending-nodeselector` 的 YAML 配置**：确认 `nodeSelector` 设置了 `aiops.e2e/nonexistent-node-label=true`，这是导致调度失败的关键配置。\n2. **集群中所有节点的状态**：确认所有节点（master、node1、node2）的标签中均不存在 `aiops.e2e/nonexistent-node-label=true`，导致 Pod 无法找到匹配的节点。\n\n**结论**：当前 Pod 无法调度的根本原因是其 `nodeSelector` 设置了不存在的标签 `aiops.e2e/nonexistent-node-label=true`，导致没有节点匹配。","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 8 个，匹配计划 2 个，未规划证据 6 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":2,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的 nodeSelector 是否匹配集群中任何节点","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"确认 Pod 的 nodeSelector 设置是否匹配任何节点的标签","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证集群中所有节点的标签，确认是否有节点匹配 'rc-pending-nodeselector' 的 nodeSelector","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","purpose":"确认集群中是否存在节点匹配 Pod 的 nodeSelector 条件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 验证 Pod 'rc-pending-nodeselector' 的 nodeSelect... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_get_by_kind_in_cl... | 验证集群中所有节点的标签，确认是否有节点匹配 'rc-pending-nodeselect... | `kubectl get nodes -o json` |

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
   ✅ [根因分析] 完成 (2m 37.8s)
   📤 → 下游数据: root_cause=Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 aiops.e2e/nonexistent-node-label=true，导致无法找到匹配的节点。
   confidence=90%
   causal_chain={"root_cause": "Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 aiops.e2e/nonexistent-node-label=true，导致无法找到匹配的节点。", "intermediate_causes": ["nodeSelector 设置了不存在的标签", "集群中所有节点的标签均不存在 aiops.e2.e/nonexistent-node-label=true", "Pod 'rc-pending-nodeselector' 的 FailedScheduling 事件显示 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"], "immediate_causes": ["Pod 'rc-pending-nodeselector' 无法找到匹配的节点", "Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 aiops.e2e/nonexistent-node-label=true"], "symptoms": ["Pod 'rc-pending-nodeselector' 的状态为 Pending", "Pod 'rc-pending-nodeselector' 的 Events 显示 FailedScheduling"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"id": "e1", "description": "验证 Pod 'rc-pending-nodeselector' 的 nodeSelector 是否匹配集群中任何节点", "level": "critical", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSe"}, {"id": "e2", "description": "验证集群中所有节点的标签，确认是否有节点匹配 'rc-pending-nodeselector' 的 nodeSelector", "level": "critical", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubern"}, {"id": "layer_1", "description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Pending': 1, 'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS      RESTARTS         AGE    IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                84m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type"}, {"id": "layer_2", "description": "上游已验证工具结果: kubectl_describe", "level": "important", "value": "kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  8m58s (x15 over 78m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:"}, {"id": "layer_3", "description": "上游已验证工具结果: kubectl_get_yaml", "level": "important", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSe"}, {"id": "layer_4", "description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubern"}, {"id": "layer_5", "description": "上游已验证工具结果: kubectl_get_yaml", "level": "important", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Node\nname: master\nnamespace: None"}, {"id": "layer_6", "description": "上游已验证工具结果: kubectl_get_yaml", "level": "important", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Node\nname: node1\nnamespace: None"}], "evidence_analysis": [{"id": "e1", "description": "Pod 'rc-pending-nodeselector' 的 YAML 配置显示 nodeSelector 设置了 aiops.e2e/nonexistent-node-label=true", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSe"}, {"id": "e2", "description": "集群中所有节点的标签均不存在 aiops.e2e/nonexistent-node-label=true", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubern"}, {"id": "layer_2", "description": "Pod 'rc-pending-nodeselector' 的 FailedScheduling 事件显示 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "value": "kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  8m58s (x15 over 78m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:"}], "causal_chain": {"root_cause": "Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 aiops.e2e/nonexistent-node-label=true，导致无法找到匹配的节点。", "intermediate_causes": ["nodeSelector 设置了不存在的标签", "集群中所有节点的标签均不存在 aiops.e2.e/nonexistent-node-label=true", "Pod 'rc-pending-nodeselector' 的 FailedScheduling 事件显示 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"], "immediate_causes": ["Pod 'rc-pending-nodeselector' 无法找到匹配的节点", "Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 aiops.e2e/nonexistent-node-label=true"], "symptoms": ["Pod 'rc-pending-nodeselector' 的状态为 Pending", "Pod 'rc-pending-nodeselector' 的 Events 显示 FailedScheduling"]}, "root_cause": "Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 aiops.e2e/nonexistent-node-label=true，导致无法找到匹配的节点。", "root_cause_summary": "Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 aiops.e2e/nonexistent-node-label=true，导致无法找到匹配的节点。", "confidence": 0.9, "confidence_reason": "有直接证据表明 Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 aiops.e2e/nonexistent-node-label=true，且集群中所有节点的标签均不存在该标签，导致无法找到匹配的节点。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [], "limitations": "", "llm_raw_analysis": "已采集证据：\n1. **Pod `rc-pending-nodeselector` 的 YAML 配置**：确认 `nodeSelector` 设置了 `aiops.e2e/nonexistent-node-label=true`，这是导致调度失败的关键配置。\n2. **集群中所有节点的状态**：确认所有节点（master、node1、node2）的标签中均不存在 `aiops.e2e/nonexistent-node-label=true`，导致 Pod 无法找到匹配的节点。\n\n**结论**：当前 Pod 无法调度的根本原因是其 `nodeSelector` 设置了不存在的标签 `aiops.e2e/nonexistent-node-label=true`，导致没有节点匹配。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 aiops.e2e/nonexistent-node-label=true，导致无法找到匹配的节点。
   置信度: 90%
   🔗 因果链:
     根本原因: Pod 'rc-pending-nodeselector' 的 nodeSelector 设置了不存在的标签 aiops.e2e/nonexistent-node-label=true，导致无法找到匹配的节点。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 8.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4767 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 6m 22.5s
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
| **兼容归因层** | L1 |
| **问题分类** | 调度失败（nodeSelector 不匹配） |
| **置信度** | 高 (90%) |
| **证据完整度** | 2/2 (100%) |

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
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: Pending` | Pod 无法调度，处于 Pending 状态 |
| 2 | FailedScheduling 事件 | `kubectl describe pod` | `Warning  FailedScheduling  8m58s (x15 over 78m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 明确指出 nodeSelector 不匹配 |
| 3 | Pod spec 的 nodeSelector | `kubectl get pod -o yaml` | `aiops.e2e/nonexistent-node-label: "true"` | Pod 设置了不存在的 nodeSelector 标签 |
| 4 | 节点标签 | `kubectl get nodes -o yaml` | 节点 master 和 node1 都不包含 `aiops.e2e/nonexistent-node-label: "true"` | 无节点满足 nodeSelector 条件 |
| 5 | Pod 事件 | `kubectl describe pod` | `preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` | 调度器尝试抢占失败 |
| 6 | 集群节点状态 | `kubectl get node` | `STATUS: Ready` | 所有节点状态正常，无资源不足问题 |
| 7 | Runbook | `fetch_runbook` | `Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling` | 指出调度失败的常见原因包括 nodeSelector 不匹配 |
| 8 | Pod YAML 配置 | `kubectl get pod -o yaml` | `nodeSelector: { aiops.e2e/nonexistent-node-label: "true" }` | nodeSelector 设置了不存在的标签 |

### 证据关联分析
- **证据 #2 + #3 印证**：`nodeSelector: aiops.e2e/nonexistent-node-label: "true"` + `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` → 明确表明 nodeSelector 不匹配是调度失败的直接原因。
- **证据链**：
  - Pod 设置了不存在的 nodeSelector → 没有节点匹配 → 调度失败 → Pod 保持 Pending 状态。

---
## 🎯 根因分析
### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                     │
│ Pod 设置了不存在的 nodeSelector 标签 aiops.e2e/nonexistent-node-label: "true" │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                     │
│ 没有任何节点具备该标签 → 调度器无法找到匹配节点 → 调度失败                   │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                     │
│ `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                 │
│ Pod 保持 Pending 状态，事件显示调度失败                                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (FailedScheduling 事件) 和证据 #3 (nodeSelector 设置了不存在的标签)，问题的根本原因是 **Pod 设置了不存在的 nodeSelector 标签 aiops.e2e/nonexistent-node-label: "true"**，导致调度器无法找到匹配的节点，从而无法调度 Pod。
**置信度**：高 (90%)
- ✅ 事件明确指出 `3 node(s) didn't match Pod's node affinity/selector`
- ✅ Pod YAML 明确设置了不存在的 nodeSelector 标签
- ✅ 节点标签检查显示无节点满足该条件

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 修正 nodeSelector 配置**
```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
```
*操作说明*：删除或修改 `nodeSelector: aiops.e2e/nonexistent-node-label: "true"` 为集群中存在的标签（例如 `kubernetes.io/role=node`）。

**2. [可选] 添加缺失的节点标签（如需保留 nodeSelector）**
```bash
kubectl label nodes <node-name> aiops.e2e/nonexistent-node-label=true
```
*操作说明*：如果希望保留 nodeSelector，可为至少一个节点添加该标签。

**3. [建议] 验证调度是否成功**
```bash
kubectl get pod rc-pending-nodeselector -n aiops-e2e
```
*预期输出*：`STATUS: Running` 或 `STATUS: ContainerCreating`

### 后续优化
1. **标签管理**：确保 nodeSelector 使用的标签在集群中存在。
2. **调度策略审查**：检查其他 Pod 的调度策略，确保 nodeSelector、affinity、taint 等设置合理。
3. **自动化检测**：通过 CI/CD 或 Helm 部署时增加 nodeSelector 标签存在性校验。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 是否已调度 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查事件是否消失 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 无 FailedScheduling 事件 |
| 3. 检查节点标签 | `kubectl get nodes --show-labels` | 节点包含修正后的 nodeSelector 所需标签 |

---
## ⚠️ 注意事项
- 如果修改 nodeSelector 后 Pod 仍无法调度，请检查 affinity、taint、资源限制等其他调度条件。
- 避免使用不存在的标签作为调度约束，这会导致调度失败。
- 如果标签是拼写错误，请在所有节点上统一修正。

---

---

## 📊 性能统计

├─ 总耗时: 6.4m
├─ 问题定位: 34.5s (9%) ✅
├─ 证据链采集: 61.5s (16%) ✅
├─ 根因分析: 157.8s (41%) ✅
├─ 汇总总结: 128.5s (34%) ✅
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
