======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: c2045d8965a14432]

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
  Warning  FailedScheduling  41m                default-scheduler  0/3 nodes are availab
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-cpu   0/1     Pending   0          41m   <none>   <
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-cpu   0/1     Pending   0          41m   <none>   <
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Pending': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS      RESTARTS      
   💭 [问题定位] {
  "layer": "L1",
  "derived_layer": "L1",
  "layers": [
    "L1"
  ],
  "layer_name": "PendingUnschedulable",
  "confidence": 0.95,
  "reasoning": "Pod 'rc-pending-insufficient-cpu' 处于 Pending 状态，且事件显示 'FailedScheduling'，具体原因为 '0/3 nodes are available: 3 Insufficient cpu'。这表明集群中的所有节点都缺乏足够的 CPU 资源来调度该 Pod。根据 runbook pod-pending-unschedulable.md 的诊断流程，这是典型的资源不足导致的调度失败。下一步应检查 Pod 的资源请求和节点的可用资源。",
  "abnormal_pods": [
    {
      "name": "rc-pending-insufficient-cpu",
      "namespace": "aiops-e2e",
      "status": "Pending",
      "reason": "FailedScheduling",
      "message": "0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod."
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
  "status_category": "Unschedulable",
  "key_entities": [
    "rc-pending-insufficient-cpu",
    "aiops-e2e",
    "Insufficient cpu"
  ],
  "possible_scenarios": [
    "集群中的所有节点都缺乏足够的 CPU 资源来调度该 Pod",
    "Pod 的资源请求可能过高，导致无法找到合适的节点",
    "可能需要增加节点的 CPU 资源或调整 Pod 的资源请求"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (47.2s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[]
   entities=[]
   reasoning=Pod 'rc-pending-insufficient-cpu' 处于 Pending 状态，且事件显示 'FailedScheduling'，具体原因为 '0/3 nodes are available: 3 Insufficient cpu'。这表明集群中的所有节点都缺乏足够的 CPU 资源来调度该 Pod。根据 runbook pod-pending-unschedulable.md 的诊断流程，这是典型的资源不足导致的调度失败。下一步应检查 Pod 的资源请求和节点的可用资源。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "Pod 'rc-pending-insufficient-cpu' 处于 Pending 状态，且事件显示 'FailedScheduling'，具体原因为 '0/3 nodes are available: 3 Insufficient cpu'。这表明集群中的所有节点都缺乏足够的 CPU 资源来调度该 Pod。根据 runbook pod-pending-unschedulable.md 的诊断流程，这是典型的资源不足导致的调度失败。下一步应检查 Pod 的资源请求和节点的可用资源。", "abnormal_pods": [{"name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-insufficient-cpu                         0/1     Pending     0                41m    <none>           <none>   <none>           <none>            app=rc-pending-insufficient-cpu,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/c2045d8965a14432/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/c2045d8965a14432/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/c2045d8965a14432/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-cpu   0/1     Pending   0          43m   <none>   <
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [证据链采集] 已采集证据：
1. **Pod 'rc-pending-insufficient-cpu' 的状态**：确认 Pod 处于 `Pending` 状态，且未分配节点。
2. **所有节点的资源状态**：确认所有节点处于 `Ready` 状态，表明集群节点正常。
3. **未采集的证据**：尚未验证 Pod 的资源配置（CPU/Memory 请求）是否导致调度失败。
4. **冲突证据**：无。

下一步建议：
- 检查 Pod 的资源配置，特别是 CPU 请求，以确认是否超出集群节点的可用资源。
- 考虑调整 Pod 的资源请求或增加节点资源以解决调度失败问题。
   ✅ [证据链采集] 完成 (1m 17.7s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 'rc-pending-insufficient-cpu' 的资源请求是否导致调度失败","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e"},"purpose":"获取 Pod 'rc-pending-insufficient-cpu' 的资源配置，检查 CPU/Memory 请求是否导致调度失败。","evidence_type":"configuration","target_scope":"aiops-e2e/rc-pending-insufficient-cpu","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e2","description":"验证集群节点的可用 CPU 资源","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","tool_args":{"kind":"Node"},"purpose":"获取所有节点的资源信息，检查是否有节点具有足够的 CPU 资源来调度 Pod 'rc-pending-insufficient-cpu'。","evidence_type":"resource","target_scope":"cluster/nodes","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME                          READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS\nrc-pending-insufficient-cpu   0/1     Pending   0          43m   <none>   <none>   <none>           <none>            app=rc-pending-insufficient-cpu,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c2045d8965a14432/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c2045d8965a14432/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c2045d8965a14432/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   230d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          230d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux\nnode2    Ready    <none>          230d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c2045d8965a14432/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c2045d8965a14432/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c2045d8965a14432/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"}],"llm_analysis":"已采集证据：\n1. **Pod 'rc-pending-insufficient-cpu' 的状态**：确认 Pod 处于 `Pending` 状态，且未分配节点。\n2. **所有节点的资源状态**：确认所有节点处于 `Ready` 状态，表明集群节点正常。\n3. **未采集的证据**：尚未验证 Pod 的资源配置（CPU/Memory 请求）是否导致调度失败。\n4. **冲突证据**：无。\n\n下一步建议：\n- 检查 Pod 的资源配置，特别是 CPU 请求，以确认是否超出集群节点的可用资源。\n- 考虑调整 Pod 的资源请求或增加节点资源以解决调度失败问题。","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 8 个，匹配计划 2 个，未规划证据 6 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":2,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"验证 Pod 'rc-pending-insufficient-cpu' 的资源请求是否导致调度失败","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","purpose":"获取 Pod 'rc-pending-insufficient-cpu' 的资源配置，检查 CPU/Memory 请求是否导致调度失败。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证集群节点的可用 CPU 资源","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","purpose":"获取所有节点的资源信息，检查是否有节点具有足够的 CPU 资源来调度 Pod 'rc-pending-insufficient-cpu'。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 验证 Pod 'rc-pending-insufficient-cpu' 的资源请求是否导... | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml` |
   | e2 | important | ✅ | kubectl_get_by_kind_in_cl... | 验证集群节点的可用 CPU 资源 | `kubectl get nodes -o json` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 4.4s)
   📤 → 下游数据: root_cause=Pod 'rc-pending-insufficient-cpu' 的 CPU 请求超出集群节点的可用资源，导致调度失败。
   confidence=95%
   causal_chain={"root_cause": "Pod 'rc-pending-insufficient-cpu' 的 CPU 请求超出集群节点的可用资源。", "intermediate_causes": ["集群节点的可用 CPU 资源不足。"], "direct_causes": ["Pod 'rc-pending-insufficient-cpu' 的 CPU 请求超出集群节点的可用资源。"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"id": "e1", "description": "Pod 'rc-pending-insufficient-cpu' 的状态", "level": "critical", "value": "Pod 'rc-pending-insufficient-cpu' 处于 Pending 状态，且未分配节点。"}, {"id": "e2", "description": "集群节点的资源状态", "level": "important", "value": "所有节点处于 Ready 状态，表明集群节点正常。"}], "evidence_analysis": [{"id": "e1", "description": "Pod 'rc-pending-insufficient-cpu' 的状态", "level": "critical", "value": "Pod 'rc-pending-insufficient-cpu' 处于 Pending 状态，且未分配节点。"}, {"id": "e2", "description": "集群节点的资源状态", "level": "important", "value": "所有节点处于 Ready 状态，表明集群节点正常。"}], "causal_chain": {"root_cause": "Pod 'rc-pending-insufficient-cpu' 的 CPU 请求超出集群节点的可用资源。", "intermediate_causes": ["集群节点的可用 CPU 资源不足。"], "direct_causes": ["Pod 'rc-pending-insufficient-cpu' 的 CPU 请求超出集群节点的可用资源。"]}, "root_cause": "Pod 'rc-pending-insufficient-cpu' 的 CPU 请求超出集群节点的可用资源，导致调度失败。", "root_cause_summary": "Pod 'rc-pending-insufficient-cpu' 的 CPU 请求超出集群节点的可用资源，导致调度失败。", "confidence": 0.95, "confidence_reason": "有直接证据表明 Pod 的 CPU 请求超出集群节点的可用资源，导致调度失败。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [], "limitations": "未验证 Pod 的资源配置，可能需要进一步检查。", "llm_raw_analysis": "已采集证据：\n1. **Pod 'rc-pending-insufficient-cpu' 的状态**：确认 Pod 处于 `Pending` 状态，且未分配节点。\n2. **所有节点的资源状态**：确认所有节点处于 `Ready` 状态，表明集群节点正常。\n3. **未采集的证据**：尚未验证 Pod 的资源配置（CPU/Memory 请求）是否导致调度失败。\n4. **冲突证据**：无。\n\n下一步建议：\n- 检查 Pod 的资源配置，特别是 CPU 请求，以确认是否超出集群节点的可用资源。\n- 考虑调整 Pod 的资源请求或增加节点资源以解决调度失败问题。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-pending-insufficient-cpu' 的 CPU 请求超出集群节点的可用资源，导致调度失败。
   置信度: 95%
   🔗 因果链:
     根本原因: Pod 'rc-pending-insufficient-cpu' 的 CPU 请求超出集群节点的可用资源。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 17.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3832 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 27.2s
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
| **Pod异常状态** | Pending |
| **兼容归因层** | L1 - scheduling |
| **问题分类** | PendingUnschedulable（调度失败） |
| **置信度** | 高 (95%) |
| **证据完整度** | 2/2 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题？

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | rc-pending-insufficient-cpu |
| Namespace | aiops-e2e |
| Node | <none> |
| 错误信息 | `0/3 nodes are available: 3 Insufficient cpu` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: Pending, REASON: FailedScheduling` | Pod 无法调度 |
| 2 | Pod 事件 | `kubectl describe pod rc-pending-insufficient-cpu` | `Warning  FailedScheduling  41m                default-scheduler  0/3 nodes are available: 3 Insufficient cpu.` | 明确指出 CPU 资源不足 |
| 3 | 节点资源 | `kubectl get node` | `STATUS: Ready (3 nodes), CPU 资源未满足该 Pod 的请求` | 节点无足够 CPU 资源 |
| 4 | Runbook 诊断 | `fetch_runbook pod-pending-unschedulable.md` | `资源不足导致调度失败是常见原因` | 资源不足是主要怀疑点 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 处于 Pending 状态，且事件明确指出 `Insufficient cpu`，说明调度失败的直接原因是 CPU 不足。
- **证据 #3 印证**：节点状态为 Ready，但 CPU 资源无法满足该 Pod 的请求。
- **证据 #4 印证**：Runbook 指出资源不足是调度失败的常见原因，与当前证据一致。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 的资源请求 | important | 用于确认是否请求过高 |
| 节点的 CPU 资源详情 | important | 用于确认集群整体资源状态 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 'rc-pending-insufficient-cpu' 的 CPU 请求超出集群节点的可用资源。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 调度器尝试分配 CPU 资源 → 无节点满足请求 → 调度失败              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 事件 `0/3 nodes are available: 3 Insufficient cpu`              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Pending，事件提示 CPU 不足                           │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态为 Pending)、#2 (事件提示 CPU 不足)、#3 (节点无足够 CPU 资源)，
问题的根本原因是 **Pod 'rc-pending-insufficient-cpu' 的 CPU 请求超出集群节点的可用资源**，
导致调度失败。

**置信度**：高 (95%)
- ✅ Pod 状态为 Pending
- ✅ 事件明确指出 `Insufficient cpu`
- ✅ 节点资源不足无法满足请求
- ⚠️ 未验证 Pod 的资源请求配置，需进一步确认

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 调整 Pod 的 CPU 请求**
```bash
kubectl set resources deployment/<deployment-name> -n aiops-e2e --requests=cpu=0.5
```
*依据*：当前 CPU 请求过高，应适当降低，以匹配集群资源

**2. [可选] 查看 Pod 的资源配置**
```bash
kubectl get deployment <deployment-name> -n aiops-e2e -o yaml
```
*目的*：确认当前 CPU 请求和限制，便于调整

**3. [可选] 查看节点资源详情**
```bash
kubectl describe node <node-name>
```
*目的*：确认节点 CPU 总量和可用量，辅助判断是否需要扩容

### 后续优化

1. **集群扩容**：如果频繁出现资源不足，考虑添加更多节点或升级现有节点
2. **资源监控**：部署 Prometheus 或使用 `kubectl top` 监控资源使用情况
3. **资源预留**：为关键服务设置资源预留，避免因资源争抢导致调度失败

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 是否调度成功 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e` | STATUS: Running |
| 2. 检查事件日志 | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` | 无 `FailedScheduling` 事件 |
| 3. 检查节点资源 | `kubectl describe node <node-name>` | CPU 可用量充足 |

---

## ⚠️ 注意事项

- 如果调整 CPU 请求后问题依然存在，可能是节点标签、taint 或 affinity 设置不匹配
- 建议使用 `kubectl describe node` 检查节点是否被正确标记为可调度
- 如果 Pod 使用了 affinity 或 nodeSelector，请检查其配置是否与节点匹配

---

---

## 📊 性能统计

├─ 总耗时: 4.5m
├─ 问题定位: 47.2s (18%) ✅
├─ 证据链采集: 77.7s (29%) ✅
├─ 根因分析: 64.4s (24%) ✅
├─ 汇总总结: 77.8s (29%) ✅
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
