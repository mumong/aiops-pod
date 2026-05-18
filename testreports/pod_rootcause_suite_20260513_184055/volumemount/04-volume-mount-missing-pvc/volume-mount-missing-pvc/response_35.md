======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: aca611d654a547b8]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Pending': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS      RESTARTS      
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                    READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-volume-missing-pvc   0/1     Pending   0          94m   <none>   <none>   <non
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
19m (x15 over 89m)   Warning   FailedScheduling   Pod/rc-volume-missing-pvc   0/3 nodes are available: persistentvolumeclaim "rc-definitely-missing-pvc" not found. preemption
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=211 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide persistentvolumeclaim rc-definitely-missing-pvc -n aiops-e2e
Error from server (NotFound): pe
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=62 abnormal=8 status_counts={'Pending': 8}
NAMESPACE       NAME                                                 STATUS    VOLUME                              
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Pending': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS      RESTARTS      
   💭 [问题定位] {
  "layer": "L0",
  "derived_layer": "L0",
  "layers": [
    "L0"
  ],
  "layer_name": "Pod VolumeMountFailed",
  "confidence": 0.95,
  "reasoning": "Pod 'rc-volume-missing-pvc' 处于 Pending 状态，并且 Events 显示 'persistentvolumeclaim "rc-definitely-missing-pvc" not found'。这表明 PVC 未找到，导致 Pod 无法调度和挂载卷，符合 VolumeMountFailed 的诊断。",
  "abnormal_pods": [
    "aiops-e2e/rc-volume-missing-pvc"
  ],
  "abnormal_groups": {
    "PodVolumeMountFailed": 1
  },
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "VolumeMountFailed",
  "status_category": "VolumeMountFailed",
  "key_entities": [
    "Pod: aiops-e2e/rc-volume-missing-pvc",
    "PVC: aiops-e2e/rc-definitely-missing-pvc"
  ],
  "possible_scenarios": [
    "PVC 'rc-definitely-missing-pvc' 未创建或未绑定到任何 PV。",
    "Pod 'rc-volume-missing-pvc' 引用了不存在的 PVC，导致调度失败。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (49.9s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[{'scenario': "PVC 'rc-definitely-missing-pvc' 未创建或未绑定到任何 PV。", 'probability': 'high', 'reason': 'Events 明确指出 PVC 不存在。'}, {'scenario': "Pod 'rc-volume-missing-pvc' 引用了不存在的 PVC，导致调度失败。", 'probability': 'high', 'reason': 'Pod spec 中引用了不存在的 PVC，导致调度失败。'}]
   entities=[{"type": "Pod", "name": "rc-volume-missing-pvc", "namespace": "aiops-e2e"}, {"type": "PVC", "name": "rc-definitely-missing-pvc", "namespace": "aiops-e2e"}]
   reasoning=Pod 'rc-volume-missing-pvc' 处于 Pending 状态，并且 Events 显示 'persistentvolumeclaim "rc-definitely-missing-pvc" not found'。这表明 PVC 未找到，导致 Pod 无法调度和挂载卷，符合 VolumeMountFailed 的诊断。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "Pod VolumeMountFailed", "confidence": 0.95, "reasoning": "Pod 'rc-volume-missing-pvc' 处于 Pending 状态，并且 Events 显示 'persistentvolumeclaim \"rc-definitely-missing-pvc\" not found'。这表明 PVC 未找到，导致 Pod 无法调度和挂载卷，符合 VolumeMountFailed 的诊断。", "abnormal_pods": [{"name": "rc-volume-missing-pvc", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "Pod", "name": "rc-volume-missing-pvc", "namespace": "aiops-e2e"}, {"type": "PVC", "name": "rc-definitely-missing-pvc", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "PVC 'rc-definitely-missing-pvc' 未创建或未绑定到任何 PV。", "probability": "high", "reason": "Events 明确指出 PVC 不存在。"}, {"scenario": "Pod 'rc-volume-missing-pvc' 引用了不存在的 PVC，导致调度失败。", "probability": "high", "reason": "Pod spec 中引用了不存在的 PVC，导致调度失败。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-pvc"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-pvc"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-volume-missing-pvc                               0/1     Pending     0                94m    <none>           <none>   <none>           <none>            app=rc-volume-missing-pvc,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/aca611d654a547b8/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/aca611d654a547b8/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/aca611d654a547b8/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-missing-pvc
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  20m (x15 over 90m)  default-scheduler  0/3 nodes are available: p
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=211 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide persistentvolumeclaim rc-definitely-missing-pvc -n aiops-e2e
Error from server (NotFound): pe
   💭 [证据链采集] 已采集证据：
- Pod 'rc-volume-missing-pvc' 处于 Pending 状态，Events 显示调度失败，原因是找不到 PVC 'rc-definitely-missing-pvc'。
- PVC 'rc-definitely-missing-pvc' 不存在，验证命令返回 'NotFound'。

结论：
Pod 'rc-volume-missing-pvc' 无法调度是因为引用了不存在的 PVC 'rc-definitely-missing-pvc'。这符合 VolumeMountFailed 的诊断，归因于 PVC 缺失。建议创建该 PVC 或调整 Pod 配置以引用存在的 PVC。
   ✅ [证据链采集] 完成 (1m 9.7s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 'rc-volume-missing-pvc' 的详细状态和 Events 信息，以确认 Pending 的原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-pvc -n aiops-e2e","tool_args":{"pod_name":"rc-volume-missing-pvc","namespace":"aiops-e2e"},"purpose":"验证 Pod 'rc-volume-missing-pvc' 的详细状态和 Events 信息，以确认 Pending 的原因。","evidence_type":"events","target_scope":"Pod/aiops-e2e/rc-volume-missing-pvc","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"验证 PVC 'rc-definitely-missing-pvc' 是否存在。","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get persistentvolumeclaim rc-definitely-missing-pvc -n aiops-e2e","tool_args":{"resource_name":"rc-definitely-missing-pvc","namespace":"aiops-e2e"},"purpose":"验证 PVC 'rc-definitely-missing-pvc' 是否存在。","evidence_type":"existence","target_scope":"PVC/aiops-e2e/rc-definitely-missing-pvc","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-missing-pvc\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  20m (x15 over 90m)  default-scheduler  0/3 nodes are available: persistentvolumeclaim \"rc-definitely-missing-pvc\" not found. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/aca611d654a547b8/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/aca611d654a547b8/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/aca611d654a547b8/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=211 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide persistentvolumeclaim rc-definitely-missing-pvc -n aiops-e2e\nError from server (NotFound): persistentvolumeclaims \"rc-definitely-missing-pvc\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/aca611d654a547b8/tools/002-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/aca611d654a547b8/tools/002-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/aca611d654a547b8/tools/002-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集证据：\n- Pod 'rc-volume-missing-pvc' 处于 Pending 状态，Events 显示调度失败，原因是找不到 PVC 'rc-definitely-missing-pvc'。\n- PVC 'rc-definitely-missing-pvc' 不存在，验证命令返回 'NotFound'。\n\n结论：\nPod 'rc-volume-missing-pvc' 无法调度是因为引用了不存在的 PVC 'rc-definitely-missing-pvc'。这符合 VolumeMountFailed 的诊断，归因于 PVC 缺失。建议创建该 PVC 或调整 Pod 配置以引用存在的 PVC。","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 8 个，匹配计划 2 个，未规划证据 6 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":2,"unplanned_tool_count":6,"evidence_inventory":[{"id":"e1","description":"验证 Pod 'rc-volume-missing-pvc' 的详细状态和 Events 信息，以确认 Pending 的原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-pvc -n aiops-e2e","purpose":"验证 Pod 'rc-volume-missing-pvc' 的详细状态和 Events 信息，以确认 Pending 的原因。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证 PVC 'rc-definitely-missing-pvc' 是否存在。","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get persistentvolumeclaim rc-definitely-missing-pvc -n aiops-e2e","purpose":"验证 PVC 'rc-definitely-missing-pvc' 是否存在。","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod 'rc-volume-missing-pvc' 的详细状态和 Events ... | `kubectl describe pod rc-volume-missing-pvc -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_by_name | 验证 PVC 'rc-definitely-missing-pvc' 是否存在。 | `kubectl get persistentvolumeclaim rc-definitely-missing-pvc -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (32.9s)
   📤 → 下游数据: root_cause=[L0层] 当前无法基于 LLM 输出确定根本原因
   confidence=10%
   causal_chain={"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}
   rca_analysis={"phenomenon": "我的集群有什么问题", "evidence_analysis": [], "causal_chain": {"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}, "root_cause": "[L0层] 当前无法基于 LLM 输出确定根本原因", "confidence": 0.1, "confidence_reason": "LLM 返回结果不符合 RCA 结构化输出合同", "alternative_causes": []}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: [L0层] 当前无法基于 LLM 输出确定根本原因
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
   ✅ [汇总总结] 完成 (1m 14.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3646 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 47.0s
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
| **Pod异常状态** | Pod 'rc-volume-missing-pvc' 处于 Pending 状态 |
| **兼容归因层** | L0 |
| **问题分类** | VolumeMountFailed |
| **置信度** | 高 (95%) |
| **证据完整度** | 2/2 (100%) |

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-volume-missing-pvc |
| Namespace | aiops-e2e |
| 错误信息 | persistentvolumeclaim "rc-definitely-missing-pvc" not found |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod rc-volume-missing-pvc` | `status: Pending` | Pod 无法调度 |
| 2 | Events 信息 | `kubectl events` | `Warning FailedScheduling Pod/rc-volume-missing-pvc 0/3 nodes are available: persistentvolumeclaim "rc-definitely-missing-pvc" not found` | PVC 不存在导致调度失败 |
| 3 | PVC 状态 | `kubectl get persistentvolumeclaim rc-definitely-missing-pvc -n aiops-e2e` | `Error from server (NotFound): persistentvolumeclaims "rc-definitely-missing-pvc" not found` | PVC 不存在 |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 处于 Pending 状态，Events 明确指出 PVC 不存在。
- **证据链**：PVC 不存在 → Pod 无法挂载卷 → 调度失败 → Pod 始终处于 Pending 状态。

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ PVC 'rc-definitely-missing-pvc' 未创建或未绑定到任何 PV。         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod 'rc-volume-missing-pvc' 引用了不存在的 PVC，导致调度失败。     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ `kubectl events` 显示：persistentvolumeclaim "rc-definitely-missing-pvc" not found。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 'rc-volume-missing-pvc' 处于 Pending 状态，无法调度。         │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1（Pod 状态为 Pending）、证据 #2（Events 显示 PVC 未找到）、以及证据 #3（尝试获取 PVC 报错），可以确认问题的根本原因是 **PVC 'rc-definitely-missing-pvc' 未创建或未绑定到任何 PV**，导致 Pod 无法调度和挂载卷，从而一直处于 Pending 状态。
**置信度**：高 (95%)
- ✅ Events 明确指出 PVC 不存在
- ✅ kubectl get PVC 报错验证了 PVC 不存在
- ✅ Pod 状态为 Pending，符合 VolumeMountFailed 的诊断特征

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 创建 PVC 'rc-definitely-missing-pvc'**
```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: rc-definitely-missing-pvc
  namespace: aiops-e2e
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
EOF
```
*依据*：Events 明确指出 PVC 不存在，创建 PVC 是解决调度失败的必要条件。

**2. [可选] 确认 PVC 是否绑定成功**
```bash
kubectl get pvc rc-definitely-missing-pvc -n aiops-e2e
```
*目的*：确认 PVC 是否绑定成功，若未绑定可检查 StorageClass 配置。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 PVC 是否存在 | `kubectl get pvc rc-definitely-missing-pvc -n aiops-e2e` | PVC 状态为 Bound |
| 2. 确认 Pod 是否调度成功 | `kubectl get pod rc-volume-missing-pvc -n aiops-e2e` | STATUS: Running |
| 3. 检查 PVC 是否绑定 | `kubectl describe pvc rc-definitely-missing-pvc -n aiops-e2e` | Status: Bound |

---
## ⚠️ 注意事项
- 如果 PVC 无法绑定，需要检查 StorageClass 是否存在，或 PV 是否满足 PVC 的要求。
- 如果 Pod 仍然无法调度，建议检查 Node 的 Taint、NodeSelector、PodAffinity 等配置。
- 确保 PVC 的命名和 Pod 中的引用完全一致，避免拼写错误。

---

---

## 📊 性能统计

├─ 总耗时: 3.8m
├─ 问题定位: 49.9s (22%) ✅
├─ 证据链采集: 69.7s (31%) ✅
├─ 根因分析: 32.9s (15%) ✅
├─ 汇总总结: 74.5s (33%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 9 次
```

📋 诊断追踪

- **核心 Runbook**: pod-volume-mount-failed
- **参考 Runbook**: pod-volume-mount-failed
- **工具调用**: 9 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
