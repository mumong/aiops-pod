======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 22bd2cc5e3de436d]

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
rc-volume-missing-pvc   0/1     Pending   0          44m   <none>   <none>   <non
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
44m                 Warning   FailedScheduling   Pod/rc-volume-missing-pvc   0/3 nodes are available: persistentvolumeclaim "rc-definitely-missing-pvc" not found. preemption:
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=211 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide persistentvolumeclaim rc-definitely-missing-pvc -n aiops-e2e
Error from server (NotFound): pe
   💭 [问题定位] {
  "layer": "L0",
  "derived_layer": "L0",
  "layers": [
    "L0"
  ],
  "layer_name": "VolumeMountFailed",
  "confidence": 0.95,
  "reasoning": "Pod rc-volume-missing-pvc 处于 Pending 状态，Events 显示 'persistentvolumeclaim "rc-definitely-missing-pvc" not found'。kubectl get pvc rc-definitely-missing-pvc -n aiops-e2e 返回 'Error from server (NotFound)'，确认 PVC 缺失。此问题属于 VolumeMountFailed 类型，归因于 PVC 未找到，符合 L0 层级。",
  "abnormal_pods": [
    "rc-volume-missing-pvc"
  ],
  "abnormal_groups": {
    "VolumeMountFailed": 1
  },
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "VolumeMountFailed",
  "status_category": "VolumeMountFailed",
  "key_entities": [
    "rc-volume-missing-pvc",
    "aiops-e2e",
    "persistentvolumeclaim"
  ],
  "possible_scenarios": [
    "PVC 'rc-definitely-missing-pvc' 未定义或未绑定，导致 Pod 无法调度。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (44.0s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[{'scenario': "PVC 'rc-definitely-missing-pvc' 未定义或未绑定，导致 Pod 无法调度。", 'probability': '高', 'reason': 'Events 显示 \'persistentvolumeclaim "rc-definitely-missing-pvc" not found\'，且 kubectl get pvc 返回 \'Error from server (NotFound)\'。'}]
   entities=[{"type": "Pod", "name": "rc-volume-missing-pvc", "namespace": "aiops-e2e"}, {"type": "PersistentVolumeClaim", "name": "rc-definitely-missing-pvc", "namespace": "aiops-e2e"}]
   reasoning=Pod rc-volume-missing-pvc 处于 Pending 状态，Events 显示 'persistentvolumeclaim "rc-definitely-missing-pvc" not found'。kubectl get pvc rc-definitely-missing-pvc -n aiops-e2e 返回 'Error from server (NotFound)'，确认 PVC 缺失。此问题属于 VolumeMountFailed 类型，归因于 PVC 未找到，符合 L0 层级。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "VolumeMountFailed", "confidence": 0.95, "reasoning": "Pod rc-volume-missing-pvc 处于 Pending 状态，Events 显示 'persistentvolumeclaim \"rc-definitely-missing-pvc\" not found'。kubectl get pvc rc-definitely-missing-pvc -n aiops-e2e 返回 'Error from server (NotFound)'，确认 PVC 缺失。此问题属于 VolumeMountFailed 类型，归因于 PVC 未找到，符合 L0 层级。", "abnormal_pods": [{"name": "rc-volume-missing-pvc", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "Pod", "name": "rc-volume-missing-pvc", "namespace": "aiops-e2e"}, {"type": "PersistentVolumeClaim", "name": "rc-definitely-missing-pvc", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "PVC 'rc-definitely-missing-pvc' 未定义或未绑定，导致 Pod 无法调度。", "probability": "高", "reason": "Events 显示 'persistentvolumeclaim \"rc-definitely-missing-pvc\" not found'，且 kubectl get pvc 返回 'Error from server (NotFound)'。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-pvc"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-pvc"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-volume-missing-pvc                               0/1     Pending     0                44m     <none>           <none>   <none>           <none>            app=rc-volume-missing-pvc,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/22bd2cc5e3de436d/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/22bd2cc5e3de436d/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/22bd2cc5e3de436d/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=211 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide persistentvolumeclaim rc-definitely-missing-pvc -n aiops-e2e
Error from server (NotFound): pe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-missing-pvc
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  46m                 default-scheduler  0/3 nodes are available: p
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (1m 26.1s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 PVC 'rc-definitely-missing-pvc' 是否存在于命名空间 'aiops-e2e' 中","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get persistentvolumeclaim rc-definitely-missing-pvc -n aiops-e2e","tool_args":{"name":"rc-definitely-missing-pvc","kind":"persistentvolumeclaim","namespace":"aiops-e2e"},"purpose":"确认 PVC 是否缺失","evidence_type":"negative","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod 'rc-volume-missing-pvc' 的详细描述信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-pvc -n aiops-e2e","tool_args":{"name":"rc-volume-missing-pvc","kind":"pod","namespace":"aiops-e2e"},"purpose":"获取 Pod 的事件信息和挂载配置","evidence_type":"positive","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取命名空间 'aiops-e2e' 中与 Pod 'rc-volume-missing-pvc' 相关的事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-missing-pvc","tool_args":{"field_selector":"involvedObject.name=rc-volume-missing-pvc","namespace":"aiops-e2e"},"purpose":"检查与 Pod 相关的事件信息","evidence_type":"positive","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=211 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide persistentvolumeclaim rc-definitely-missing-pvc -n aiops-e2e\nError from server (NotFound): persistentvolumeclaims \"rc-definitely-missing-pvc\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/22bd2cc5e3de436d/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/22bd2cc5e3de436d/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/22bd2cc5e3de436d/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-missing-pvc\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  46m                 default-scheduler  0/3 nodes are available: persistentvolumeclaim \"rc-definitely-missing-pvc\" not found. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  102s (x9 over 41m)  default-scheduler  0/3 nodes are available: persistentvolumeclaim \"rc-definitely-missing-pvc\" not found. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/22bd2cc5e3de436d/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/22bd2cc5e3de436d/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/22bd2cc5e3de436d/tools/002-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 6 个，匹配计划 3 个，未规划证据 3 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":3,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"验证 PVC 'rc-definitely-missing-pvc' 是否存在于命名空间 'aiops-e2e' 中","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get persistentvolumeclaim rc-definitely-missing-pvc -n aiops-e2e","purpose":"确认 PVC 是否缺失","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"e2","description":"获取 Pod 'rc-volume-missing-pvc' 的详细描述信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-pvc -n aiops-e2e","purpose":"获取 Pod 的事件信息和挂载配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取命名空间 'aiops-e2e' 中与 Pod 'rc-volume-missing-pvc' 相关的事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-missing-pvc","purpose":"检查与 Pod 相关的事件信息","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 验证 PVC 'rc-definitely-missing-pvc' 是否存在于命名空间 ... | `kubectl get persistentvolumeclaim rc-definitely-missing-pvc -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_describe | 获取 Pod 'rc-volume-missing-pvc' 的详细描述信息 | `kubectl describe pod rc-volume-missing-pvc -n aiops-e2e` |
   | e3 | important | ✅ | kubectl_events | 获取命名空间 'aiops-e2e' 中与 Pod 'rc-volume-missing-... | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volum...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (28.8s)
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
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 26.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4257 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 5.4s
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
| **Pod异常状态** | Pending (VolumeMountFailed) |
| **兼容归因层** | L0 - 资源缺失 |
| **问题分类** | PVC 未找到（VolumeMountFailed） |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/3 (100%) |

---

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-volume-missing-pvc |
| Namespace | aiops-e2e |
| PVC | rc-definitely-missing-pvc |
| 错误信息 | persistentvolumeclaim "rc-definitely-missing-pvc" not found |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | kubectl get pod | `STATUS: Pending` | Pod 无法调度 |
| 2 | Pod 事件 | kubectl events | `persistentvolumeclaim "rc-definitely-missing-pvc" not found` | PVC 未找到 |
| 3 | PVC 存在性验证 | kubectl get pvc | `Error from server (NotFound)` | PVC 不存在 |
| 4 | Pod 详细信息 | kubectl describe pod | `Warning FailedScheduling 0/3 nodes are available: persistentvolumeclaim "rc-definitely-missing-pvc" not found` | 调度失败原因明确 |
| 5 | Runbook 指南 | fetch_runbook | `Pod异常类型: VolumeMountFailed | 典型状态: Pending` | 问题分类匹配 VolumeMountFailed |
| 6 | kubectl get by name | kubectl get pod | `rc-volume-missing-pvc 0/1 Pending` | Pod 状态确认 |
| 7 | kubectl get PVC by name | kubectl get pvc | `persistentvolumeclaim "rc-definitely-missing-pvc" not found` | PVC 不存在 |

### 证据关联分析
- **证据 #2 + #3 印证**：Pod 事件指出 PVC 未找到，kubectl get pvc 确认该 PVC 不存在。
- **证据链**：PVC 未定义 → Pod 无法挂载卷 → 调度失败 → Pod 停留在 Pending 状态。

### 缺失证据（无）
> 所有关键证据已采集，未发现缺失。

---

## 🎯 根因分析
### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                   │
│ PVC 'rc-definitely-missing-pvc' 未定义或未创建，导致 Pod 无法挂载存储卷      │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                   │
│ Pod 依赖的 PVC 不存在 → 无法满足卷挂载依赖 → 调度失败                         │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                   │
│ 调度失败，事件提示 `persistentvolumeclaim "rc-definitely-missing-pvc" not found` │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                               │
│ Pod 'rc-volume-missing-pvc' 处于 Pending 状态，无法调度                        │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (kubectl events 显示 PVC 未找到) 和证据 #3 (kubectl get pvc 返回 Not Found)，问题的根本原因是**PVC 'rc-definitely-missing-pvc' 未定义或未创建**，导致 Pod 无法挂载存储卷并持续处于 Pending 状态。
**置信度**：高 (95%)
- ✅ Pod 事件明确提示 PVC 未找到
- ✅ kubectl get pvc 确认 PVC 不存在
- ✅ Runbook 明确指出 VolumeMountFailed 与 PVC 缺失相关

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 创建缺失的 PVC**
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
*依据*：PVC 未定义导致调度失败，需先创建 PVC 才能调度 Pod。

**2. [可选] 确认 PVC 是否绑定成功**
```bash
kubectl get pvc rc-definitely-missing-pvc -n aiops-e2e
```
*目的*：确认 PVC 是否已绑定到 PV。

**3. [可选] 强制重启 Pod**
```bash
kubectl delete pod rc-volume-missing-pvc -n aiops-e2e
```
*目的*：在 PVC 创建后，删除 Pod 可触发调度器重新尝试挂载 PVC。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 PVC 是否存在 | `kubectl get pvc rc-definitely-missing-pvc -n aiops-e2e` | NAME: rc-definitely-missing-pvc，STATUS: Bound |
| 2. 确认 Pod 是否调度成功 | `kubectl get pod rc-volume-missing-pvc -n aiops-e2e` | STATUS: Running |
| 3. 检查事件是否更新 | `kubectl events -n aiops-e2e` | 无 FailedScheduling 事件 |

---

## ⚠️ 注意事项
- 如果 PVC 依赖的 StorageClass 不存在，也需要一并创建。
- 如果 PVC 需要特定的 StorageClass 或 PV，需确保这些资源也已正确配置。
- 如果 PVC 是由 StatefulSet 或 Deployment 自动创建的，检查其模板是否配置正确。
- 如果 PVC 仍然无法绑定，检查 StorageClass、PV 和集群存储插件（如 CSI）的配置。

---

---

## 📊 性能统计

├─ 总耗时: 4.1m
├─ 问题定位: 44.0s (18%) ✅
├─ 证据链采集: 86.1s (35%) ✅
├─ 根因分析: 28.8s (12%) ✅
├─ 汇总总结: 86.3s (35%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 8 次
```

📋 诊断追踪

- **核心 Runbook**: pod-volume-mount-failed
- **参考 Runbook**: pod-volume-mount-failed
- **工具调用**: 8 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
