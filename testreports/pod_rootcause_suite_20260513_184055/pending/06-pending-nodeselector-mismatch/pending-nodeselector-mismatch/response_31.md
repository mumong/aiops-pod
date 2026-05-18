======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 2c03f66236434866]

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
31m (x9 over 71m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 n
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          76m   <none>   <none>   
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
  "layers": [
    "L1"
  ],
  "layer_name": "PendingUnschedulable",
  "confidence": "high",
  "reasoning": "Pod rc-pending-nodeselector 处于 Pending 状态，Events 显示 FailedScheduling 原因为 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。诊断表明 Pod 的 nodeSelector 设置了不存在的标签 aiops.e2e/nonexistent-node-label，导致无法匹配任何节点。",
  "abnormal_pods": [
    {
      "name": "rc-pending-nodeselector",
      "namespace": "aiops-e2e",
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
  "status_category": "scheduling",
  "key_entities": [
    {
      "type": "Pod",
      "name": "rc-pending-nodeselector",
      "namespace": "aiops-e2e"
    },
    {
      "type": "Node",
      "name": "master"
    },
    {
      "type": "Node",
      "name": "node1"
    },
    {
      "type": "Node",
      "name": "node2"
    }
  ],
  "possible_scenarios": [
    "Pod 的 nodeSelector 设置了不存在的标签 aiops.e2e/nonexistent-node-label，导致无法匹配任何节点。",
    "集群中没有节点具有标签 aiops.e2e/nonexistent-node-label 为 true，导致 Pod 无法调度。",
    "需要检查 Pod 的 nodeSelector 配置，并确保集群中存在具有相应标签的节点。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 6.8s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'Pod 的 nodeSelector 设置了不存在的标签 aiops.e2e/nonexistent-node-label，导致无法匹配任何节点。', 'probability': 'high', 'reason': 'Events 明确指出 0/3 nodes are available，且 nodeSelector 匹配失败。'}, {'scenario': '集群中没有节点具有标签 aiops.e2e/nonexistent-node-label 为 true，导致 Pod 无法调度。', 'probability': 'high', 'reason': '节点标签检查显示所有节点均无该标签。'}, {'scenario': '需要检查 Pod 的 nodeSelector 配置，并确保集群中存在具有相应标签的节点。', 'probability': 'high', 'reason': '当前配置导致调度失败，需修复 nodeSelector 或添加匹配标签。'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}]
   reasoning=当前异常对象为 Pod 'rc-pending-nodeselector'，其状态为 'Pending'，reason 为 'Unschedulable'，message 明确指出 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。结合诊断分析，该 Pod 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致无法匹配任何节点。这属于调度失败（scheduling）范畴，归因于调度约束不匹配。当前仍存在异常 Pod，因此判定为 L1。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "当前异常对象为 Pod 'rc-pending-nodeselector'，其状态为 'Pending'，reason 为 'Unschedulable'，message 明确指出 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。结合诊断分析，该 Pod 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致无法匹配任何节点。这属于调度失败（scheduling）范畴，归因于调度约束不匹配。当前仍存在异常 Pod，因此判定为 L1。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}], "possible_scenarios": [{"scenario": "Pod 的 nodeSelector 设置了不存在的标签 aiops.e2e/nonexistent-node-label，导致无法匹配任何节点。", "probability": "high", "reason": "Events 明确指出 0/3 nodes are available，且 nodeSelector 匹配失败。"}, {"scenario": "集群中没有节点具有标签 aiops.e2e/nonexistent-node-label 为 true，导致 Pod 无法调度。", "probability": "high", "reason": "节点标签检查显示所有节点均无该标签。"}, {"scenario": "需要检查 Pod 的 nodeSelector 配置，并确保集群中存在具有相应标签的节点。", "probability": "high", "reason": "当前配置导致调度失败，需修复 nodeSelector 或添加匹配标签。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-nodeselector                             0/1     Pending     0                76m    <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/2c03f66236434866/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/2c03f66236434866/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/2c03f66236434866/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ✅ [证据链采集] 完成 (1m 13.8s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的调度失败原因，重点关注 nodeSelector 是否配置了不存在的标签","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"确认 Pod 的 nodeSelector 配置是否导致调度失败","evidence_type":"configuration","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e2","description":"验证集群中所有节点的标签，确认是否存在与 Pod 的 nodeSelector 匹配的标签","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","tool_args":{"kind":"Node","namespace":""},"purpose":"确认集群中是否存在具有标签 aiops.e2e/nonexistent-node-label 的节点","evidence_type":"node_configuration","target_scope":"Nodes","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true},{"id":"e3","description":"检查 Pod 'rc-pending-nodeselector' 的 Events，确认调度失败的具体原因","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e","tool_args":{"kind":"Event","namespace":"aiops-e2e"},"purpose":"确认调度失败的 Events 信息，包括 FailedScheduling 的具体原因","evidence_type":"event","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T20:39:53Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-fsdjk\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c03f66236434866/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c03f66236434866/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c03f66236434866/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2c03f66236434866/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2c03f66236434866/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2c03f66236434866/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 7 个，匹配计划 3 个，未规划证据 4 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":7,"matched_tool_count":3,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证 Pod 'rc-pending-nodeselector' 的调度失败原因，重点关注 nodeSelector 是否配置了不存在的标签","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"确认 Pod 的 nodeSelector 配置是否导致调度失败","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证集群中所有节点的标签，确认是否存在与 Pod 的 nodeSelector 匹配的标签","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","purpose":"确认集群中是否存在具有标签 aiops.e2e/nonexistent-node-label 的节点","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"检查 Pod 'rc-pending-nodeselector' 的 Events，确认调度失败的具体原因","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e","purpose":"确认调度失败的 Events 信息，包括 FailedScheduling 的具体原因","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 验证 Pod 'rc-pending-nodeselector' 的调度失败原因，重点关注... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_get_by_kind_in_cl... | 验证集群中所有节点的标签，确认是否存在与 Pod 的 nodeSelector 匹配的标签 | `kubectl get nodes -o json` |
   | e3 | important | ✅ | kubectl_events | 检查 Pod 'rc-pending-nodeselector' 的 Events，确认调... | `kubectl get events -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (20.8s)
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
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 5.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4788 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 46.5s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | PendingUnschedulable |
| **兼容归因层** | L1 |
| **问题分类** | 调度失败（NodeSelector 不匹配） |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/3 (100%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题？

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | rc-pending-nodeselector |
| Namespace | aiops-e2e |
| Node | master, node1, node2 |
| 错误信息 | 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod -n aiops-e2e` | `STATUS: Pending, REASON: Unschedulable` | Pod 无法调度 |
| 2 | Pod Events | `kubectl events -n aiops-e2e` | `Warning FailedScheduling 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 明确指出 nodeSelector 不匹配 |
| 3 | Pod YAML | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` | `nodeSelector: aiops.e2e/nonexistent-node-label: "true"` | Pod 使用了不存在的标签 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 `Pending`，Events 明确指出 `nodeSelector` 不匹配 → 无法调度。
- **证据 #3 印证**：Pod 的 `nodeSelector` 设置了不存在的标签 `aiops.e2e/nonexistent-node-label`，导致与所有节点不匹配。
- **证据链**：Pod 使用了错误的 nodeSelector → 无节点匹配 → 无法调度 → Pod 呈现 `Pending` 状态。

### 缺失证据（无）

---

## 🎯 根因分析

### 因果链

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                                                           │
│ Pod 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'，导致无法匹配任何节点。                  │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                                                           │
│ Kubernetes 调度器尝试将 Pod 分配给具有匹配标签的节点，但无节点满足 nodeSelector 条件。                            │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                                                           │
│ 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。                                     │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                                                       │
│ Pod 'rc-pending-nodeselector' 处于 Pending 状态，无法调度，持续显示 Unschedulable。                               │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态 Pending)、证据 #2 (Events 明确指出 nodeSelector 不匹配) 和证据 #3 (Pod YAML 显示 nodeSelector 设置了不存在的标签)，问题的根本原因是**Pod 的 nodeSelector 设置了不存在的标签 'aiops.e2e/nonexistent-node-label'**，导致调度失败。

**置信度**：高 (95%)
- ✅ Events 明确指出调度失败原因
- ✅ Pod YAML 显示 nodeSelector 设置了不存在的标签
- ✅ 所有节点均无该标签

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 修改 Pod 的 nodeSelector**

```bash
# 删除或修改 nodeSelector
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
```

*操作示例*：  
在编辑器中，删除或修改如下字段：
```yaml
nodeSelector:
  aiops.e2e/nonexistent-node-label: "true"
```

**2. [可选] 添加标签到节点（如果需要保留 nodeSelector）**

```bash
# 给节点添加标签
kubectl label nodes <node-name> aiops.e2e/nonexistent-node-label=true
```

*依据*：如果业务需求确实需要该 nodeSelector，可以添加标签到节点以允许调度。

### 后续优化

1. **标签管理规范**：
   - 确保 nodeSelector 使用的标签在集群中存在。
   - 建议使用命名空间前缀（如 `aiops.e2e/xxx`）避免冲突。

2. **Pod 调度策略优化**：
   - 使用 `nodeAffinity` 替代 `nodeSelector`，支持更灵活的调度策略。
   - 配置默认调度策略，避免因标签缺失导致调度失败。

3. **监控与告警**：
   - 配置事件监控，当出现 `FailedScheduling` 事件时触发告警。
   - 使用 Prometheus + Alertmanager 检测 Pod 调度失败率。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 是否调度成功 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查 Events 是否消失 | `kubectl events -n aiops-e2e` | 无 `FailedScheduling` 事件 |
| 3. 检查节点标签 | `kubectl get node -o jsonpath='{.metadata.labels}'` | 确认标签是否已添加或修改 |

---

## ⚠️ 注意事项

- 修改 `nodeSelector` 会影响 Pod 的调度行为，需确保修改后的标签在集群中存在。
- 如果使用 `nodeAffinity` 替代 `nodeSelector`，建议使用 `requiredDuringSchedulingIgnoredDuringExecution` 以确保调度时匹配。
- 如果问题涉及多个 Pod，建议统一管理标签和调度策略，避免重复问题。

---

## 📊 性能统计

├─ 总耗时: 4.8m
├─ 问题定位: 66.8s (23%) ✅
├─ 证据链采集: 73.8s (26%) ✅
├─ 根因分析: 20.8s (7%) ✅
├─ 汇总总结: 125.0s (44%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 9 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 9 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
