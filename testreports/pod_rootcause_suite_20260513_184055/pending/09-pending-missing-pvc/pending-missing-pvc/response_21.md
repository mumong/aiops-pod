======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 458721fd44bc4fac]

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
name: rc-pending-missing-pvc
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  45m                  default-scheduler  0/3 nodes are available:
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                     READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-missing-pvc   0/1     Pending   0          45m   <none>   <none>   <n
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。
   💭 [问题定位] {
  "layer": "L1",
  "derived_layer": null,
  "layers": [
    "L1"
  ],
  "layer_name": "PendingUnschedulable",
  "confidence": 0.95,
  "reasoning": "检测到异常 Pod 'rc-pending-missing-pvc' 处于 Pending 状态，调度失败原因为 'persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found'。这表明 PVC 未创建或未绑定，导致调度器无法分配节点。该问题属于调度层面（L1）。",
  "abnormal_pods": [
    "rc-pending-missing-pvc"
  ],
  "abnormal_groups": {
    "PendingUnschedulable": 1
  },
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "PendingUnschedulable",
  "status_category": "Scheduling",
  "key_entities": [
    "Pod: rc-pending-missing-pvc",
    "PVC: rc-pending-definitely-missing-pvc",
    "Namespace: aiops-e2e"
  ],
  "possible_scenarios": [
    "PVC 未创建：未定义 PVC 'rc-pending-definitely-missing-pvc'，导致调度器无法找到合适的 PV。",
    "PVC 未绑定：PVC 定义存在，但 StorageClass 未正确配置或没有可用的 PV。",
    "调度约束：Pod 的 nodeSelector、affinity 或 toleration 设置导致无法找到合适的节点。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (48.1s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': "PVC 未创建：未定义 PVC 'rc-pending-definitely-missing-pvc'，导致调度器无法找到合适的 PV。", 'probability': 'high', 'reason': 'Pod 调度失败事件显示 PVC 不存在。'}, {'scenario': 'PVC 未绑定：PVC 定义存在，但 StorageClass 未正确配置或没有可用的 PV。', 'probability': 'medium', 'reason': '调度失败事件未提到 PVC 已定义，但存在命名模式暗示 PVC 可能存在。'}, {'scenario': '调度约束：Pod 的 nodeSelector、affinity 或 toleration 设置导致无法找到合适的节点。', 'probability': 'low', 'reason': '调度失败事件未涉及节点选择器或亲和性问题。'}]
   entities=[{"type": "Pod", "name": "rc-pending-missing-pvc", "namespace": "aiops-e2e"}, {"type": "PVC", "name": "rc-pending-definitely-missing-pvc", "namespace": "aiops-e2e"}]
   reasoning=检测到异常 Pod 'rc-pending-missing-pvc' 处于 Pending 状态，调度失败原因为 'persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found'。这表明 PVC 未创建或未绑定，导致调度器无法分配节点。该问题属于调度层面（L1）。
   layer_analysis={"layer": "L1", "derived_layer": "", "layers": [], "layer_name": "", "confidence": 0.5, "reasoning": "检测到异常 Pod 'rc-pending-missing-pvc' 处于 Pending 状态，调度失败原因为 'persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found'。这表明 PVC 未创建或未绑定，导致调度器无法分配节点。该问题属于调度层面（L1）。", "abnormal_pods": [{"name": "rc-pending-missing-pvc", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-missing-pvc", "namespace": "aiops-e2e"}, {"type": "PVC", "name": "rc-pending-definitely-missing-pvc", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "PVC 未创建：未定义 PVC 'rc-pending-definitely-missing-pvc'，导致调度器无法找到合适的 PV。", "probability": "high", "reason": "Pod 调度失败事件显示 PVC 不存在。"}, {"scenario": "PVC 未绑定：PVC 定义存在，但 StorageClass 未正确配置或没有可用的 PV。", "probability": "medium", "reason": "调度失败事件未提到 PVC 已定义，但存在命名模式暗示 PVC 可能存在。"}, {"scenario": "调度约束：Pod 的 nodeSelector、affinity 或 toleration 设置导致无法找到合适的节点。", "probability": "low", "reason": "调度失败事件未涉及节点选择器或亲和性问题。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-missing-pvc"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-missing-pvc"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-missing-pvc                              0/1     Pending     0             45m    <none>           <none>   <none>           <none>            app=rc-pending-missing-pvc,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/458721fd44bc4fac/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/458721fd44bc4fac/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/458721fd44bc4fac/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 50%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=209 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide pvc rc-pending-definitely-missing-pvc -n aiops-e2e
Error from server (NotFound): persistentvo
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。
   💭 [证据链采集] 已采集证据：
- PVC `rc-pending-definitely-missing-pvc` 不存在，确认调度失败原因是 PVC 未创建。

冲突证据：
- 在命名空间 `aiops-e2e` 中未找到任何 PVC 资源，进一步确认 PVC 未创建。

未采集证据：
- 无。

结论：
当前 Pod `rc-pending-missing-pvc` 处于 Pending 状态，调度失败的根本原因是 PVC `rc-pending-definitely-missing-pvc` 未创建。建议创建该 PVC 以解决调度问题。
   ✅ [证据链采集] 完成 (56.2s)
   📤 → 下游数据: evidence_items=5/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 PVC 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e","tool_args":{"resource_type":"pvc","resource_name":"rc-pending-definitely-missing-pvc","namespace":"aiops-e2e"},"purpose":"确认 PVC 是否存在","evidence_type":"negative","target_scope":"aiops-e2e","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e2","description":"验证 PVC 是否已绑定","level":"important","tool":"kubectl_get_by_name","command":"kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e","tool_args":{"resource_type":"pvc","resource_name":"rc-pending-definitely-missing-pvc","namespace":"aiops-e2e"},"purpose":"确认 PVC 是否已绑定","evidence_type":"negative","target_scope":"aiops-e2e","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=209 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide pvc rc-pending-definitely-missing-pvc -n aiops-e2e\nError from server (NotFound): persistentvolumeclaims \"rc-pending-definitely-missing-pvc\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/458721fd44bc4fac/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/458721fd44bc4fac/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/458721fd44bc4fac/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/458721fd44bc4fac/tools/002-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/458721fd44bc4fac/tools/002-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/458721fd44bc4fac/tools/002-evidence-kubectl_get_by_kind_in_namespace.summary.txt"}],"llm_analysis":"已采集证据：\n- PVC `rc-pending-definitely-missing-pvc` 不存在，确认调度失败原因是 PVC 未创建。\n\n冲突证据：\n- 在命名空间 `aiops-e2e` 中未找到任何 PVC 资源，进一步确认 PVC 未创建。\n\n未采集证据：\n- 无。\n\n结论：\n当前 Pod `rc-pending-missing-pvc` 处于 Pending 状态，调度失败的根本原因是 PVC `rc-pending-definitely-missing-pvc` 未创建。建议创建该 PVC 以解决调度问题。","collection_summary":"计划 2 项，实际采集 1 项，未采集 1 项，完整度 50%；其中真实环境证据 5/6 项，完整度 83%；实际执行工具 4 个，匹配计划 1 个，未规划证据 3 个","plan_total":2,"plan_collected":1,"plan_completeness":0.5,"environment_evidence_total":6,"environment_evidence_collected":5,"environment_evidence_completeness":0.8333333333333334,"executed_tool_count":4,"matched_tool_count":1,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"验证 PVC 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e","purpose":"确认 PVC 是否存在","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"e2","description":"验证 PVC 是否已绑定","level":"important","tool":"kubectl_get_by_name","command":"kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e","purpose":"确认 PVC 是否已绑定","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e2(验证 PVC 是否已绑定): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/2 项, 完整度: 83%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 验证 PVC 是否存在 | `kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e` |
   | e2 | important | ❌ | kubectl_get_by_name | 验证 PVC 是否已绑定 | `kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e` |

   ⚠️ 未采集原因:
   - e2(验证 PVC 是否已绑定): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (10.5s)
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
   ✅ [汇总总结] 完成 (1m 52.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3686 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 47.1s
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
| **兼容归因层** | L1 - 调度层面 |
| **问题分类** | PVC 未找到，导致 Pod 无法调度 |
| **置信度** | 高 |
| **证据完整度** | 1/2 (50%) |

---

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-pending-missing-pvc |
| Namespace | aiops-e2e |
| 错误信息 | `persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found` |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: Pending, REASON: FailedScheduling` | Pod 无法调度 |
| 2 | 调度失败事件 | `kubectl describe pod` | `persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found` | 明确指出 PVC 未找到 |
| 3 | PVC 状态 | `kubectl get pvc` | `Error from server (NotFound)` | PVC 不存在 |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 处于 `Pending` 状态，事件信息明确指出 PVC 未找到，导致调度失败。
- **证据 #3 印证**：尝试获取 PVC 时返回 `NotFound`，说明 PVC 确实未创建或未绑定。

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| PVC 是否定义（StorageClass、PV 状态） | important | 无法确认 PVC 是否存在但未绑定 |

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ PVC 'rc-pending-definitely-missing-pvc' 未创建或未绑定，导致调度失败 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod 依赖的 PVC 不存在 → 调度器无法分配节点 → Pod 保持 Pending 状态 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 调度失败事件显示 PVC 不存在 → 0/3 节点可用                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 'rc-pending-missing-pvc' 处于 Pending 状态，无法调度         │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2（`persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found`）和证据 #3（`kubectl get pvc` 返回 `NotFound`），问题的根本原因是**PVC 'rc-pending-definitely-missing-pvc' 未创建或未绑定**，导致调度器无法找到合适的节点来运行 Pod。
**置信度**：高 (90%)
- ✅ `kubectl describe pod` 明确指出 PVC 不存在
- ✅ `kubectl get pvc` 也验证了 PVC 不存在
- ⚠️ 缺少 PVC 是否定义（StorageClass、PV 状态）的证据，无法确认是否存在但未绑定的情况

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 创建 PVC 'rc-pending-definitely-missing-pvc'**
```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: rc-pending-definitely-missing-pvc
  namespace: aiops-e2e
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
EOF
```
*依据*：调度失败事件明确指出 PVC 未找到，创建 PVC 是修复的前提。

**2. [可选] 验证 PVC 是否绑定成功**
```bash
kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e
```
*目的*：确认 PVC 是否已绑定到 PV，避免再次调度失败。

**3. [可选] 查看 Pod 事件日志**
```bash
kubectl describe pod rc-pending-missing-pvc -n aiops-e2e
```
*目的*：确认调度器是否能正确识别新创建的 PVC。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 PVC 是否存在 | `kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e` | PVC 存在 |
| 2. 确认 PVC 是否绑定 | `kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e` | STATUS: Bound |
| 3. 确认 Pod 是否调度成功 | `kubectl get pod rc-pending-missing-pvc -n aiops-e2e` | STATUS: Running |

---

## ⚠️ 注意事项
- 如果 PVC 已定义但未绑定，需检查 StorageClass 或手动绑定 PV。
- 如果问题持续，建议检查 PVC 的 StorageClass 是否匹配集群中可用的 PV。
- 请确保 PVC 的命名与 Pod 中引用的名称完全一致，避免拼写错误。

---

---

## 📊 性能统计

├─ 总耗时: 3.8m
├─ 问题定位: 48.1s (21%) ✅
├─ 证据链采集: 56.2s (25%) ✅
├─ 根因分析: 10.5s (5%) ✅
├─ 汇总总结: 112.3s (49%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 7 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 7 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
