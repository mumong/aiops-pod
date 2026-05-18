======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: f89322460e5e4c8d]

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
  Warning  FailedScheduling  37m                default-scheduler  0/3 nodes are available: p
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                     READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-missing-pvc   0/1     Pending   0          37m   <none>   <none>   <n
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。
   💭 [问题定位] {
  "layer": "L1",
  "derived_layer": "L1",
  "layers": [
    "L1"
  ],
  "layer_name": "PendingUnschedulable",
  "confidence": 0.95,
  "reasoning": "Pod rc-pending-missing-pvc 处于 Pending 状态，调度失败原因为 PVC 'rc-pending-definitely-missing-pvc' 未找到。此问题属于调度失败范畴，归类为 L1 层级。",
  "abnormal_pods": [
    {
      "name": "rc-pending-missing-pvc",
      "namespace": "aiops-e2e",
      "status": "Pending",
      "key_events": [
        "FailedScheduling: persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found"
      ]
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
  "status_category": "调度失败",
  "key_entities": [
    "Pod: rc-pending-missing-pvc",
    "PVC: rc-pending-definitely-missing-pvc",
    "Namespace: aiops-e2e"
  ],
  "possible_scenarios": [
    "PVC 'rc-pending-definitely-missing-pvc' 未创建或命名错误，导致 Pod 无法绑定存储",
    "Pod 的存储请求与集群中可用的存储类不匹配"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (56.4s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': "PVC 'rc-pending-definitely-missing-pvc' 未创建或命名错误，导致 Pod 无法绑定存储", 'probability': '高', 'reason': 'FailedScheduling 事件显示 PVC 未找到'}, {'scenario': 'Pod 的存储请求与集群中可用的存储类不匹配', 'probability': '中', 'reason': 'PVC 可能配置了特定 StorageClass 但未满足条件'}]
   entities=[{"type": "Pod", "name": "rc-pending-missing-pvc", "namespace": "aiops-e2e"}, {"type": "PVC", "name": "rc-pending-definitely-missing-pvc", "namespace": "aiops-e2e"}]
   reasoning=Pod rc-pending-missing-pvc 处于 Pending 状态，调度失败原因为 PVC 'rc-pending-definitely-missing-pvc' 未找到。此问题属于调度失败范畴，归类为 L1 层级。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "Pod rc-pending-missing-pvc 处于 Pending 状态，调度失败原因为 PVC 'rc-pending-definitely-missing-pvc' 未找到。此问题属于调度失败范畴，归类为 L1 层级。", "abnormal_pods": [{"name": "rc-pending-missing-pvc", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "调度失败", "key_entities": [{"type": "Pod", "name": "rc-pending-missing-pvc", "namespace": "aiops-e2e"}, {"type": "PVC", "name": "rc-pending-definitely-missing-pvc", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "PVC 'rc-pending-definitely-missing-pvc' 未创建或命名错误，导致 Pod 无法绑定存储", "probability": "高", "reason": "FailedScheduling 事件显示 PVC 未找到"}, {"scenario": "Pod 的存储请求与集群中可用的存储类不匹配", "probability": "中", "reason": "PVC 可能配置了特定 StorageClass 但未满足条件"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-missing-pvc"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-missing-pvc"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-missing-pvc                              0/1     Pending     0             37m    <none>           <none>   <none>           <none>            app=rc-pending-missing-pvc,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/f89322460e5e4c8d/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/f89322460e5e4c8d/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/f89322460e5e4c8d/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=227 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide persistentvolumeclaim rc-pending-definitely-missing-pvc -n aiops-e2e
Error from server (NotFo
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-missing-pvc
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  40m                default-scheduler  0/3 nodes are available: p
   💭 [证据链采集] 已采集证据：
1. PVC 'rc-pending-definitely-missing-pvc' 不存在（kubectl_get_by_name 返回 NotFound）
2. Pod 'rc-pending-missing-pvc' 处于 Pending 状态，调度失败原因为 PVC 未找到（kubectl_describe 显示 FailedScheduling 事件）

未采集证据：
- 无

冲突证据：
- 无

结论：当前 Pod 调度失败的根本原因是 PVC 'rc-pending-definitely-missing-pvc' 未创建或命名错误，导致 Pod 无法绑定存储。建议检查 PVC 配置并确保其存在。
   ✅ [证据链采集] 完成 (1m 27.3s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 PVC 'rc-pending-definitely-missing-pvc' 是否存在于命名空间 'aiops-e2e' 中","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e","tool_args":{"kind":"PersistentVolumeClaim","name":"rc-pending-definitely-missing-pvc","namespace":"aiops-e2e"},"purpose":"确认 PVC 是否存在，这是调度失败的关键原因","evidence_type":"existence","target_scope":"aiops-e2e","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e2","description":"验证 Pod 'rc-pending-missing-pvc' 的详细状态和事件信息","level":"important","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-missing-pvc -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-pending-missing-pvc","namespace":"aiops-e2e"},"purpose":"获取 Pod 的详细状态和事件信息，确认调度失败的具体原因","evidence_type":"status_and_events","target_scope":"aiops-e2e","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=227 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide persistentvolumeclaim rc-pending-definitely-missing-pvc -n aiops-e2e\nError from server (NotFound): persistentvolumeclaims \"rc-pending-definitely-missing-pvc\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/f89322460e5e4c8d/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f89322460e5e4c8d/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f89322460e5e4c8d/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-missing-pvc\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  40m                default-scheduler  0/3 nodes are available: persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  29m (x2 over 34m)  default-scheduler  0/3 nodes are available: persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f89322460e5e4c8d/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f89322460e5e4c8d/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f89322460e5e4c8d/tools/002-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"已采集证据：\n1. PVC 'rc-pending-definitely-missing-pvc' 不存在（kubectl_get_by_name 返回 NotFound）\n2. Pod 'rc-pending-missing-pvc' 处于 Pending 状态，调度失败原因为 PVC 未找到（kubectl_describe 显示 FailedScheduling 事件）\n\n未采集证据：\n- 无\n\n冲突证据：\n- 无\n\n结论：当前 Pod 调度失败的根本原因是 PVC 'rc-pending-definitely-missing-pvc' 未创建或命名错误，导致 Pod 无法绑定存储。建议检查 PVC 配置并确保其存在。","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 5 个，匹配计划 2 个，未规划证据 3 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":5,"matched_tool_count":2,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"验证 PVC 'rc-pending-definitely-missing-pvc' 是否存在于命名空间 'aiops-e2e' 中","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e","purpose":"确认 PVC 是否存在，这是调度失败的关键原因","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"e2","description":"验证 Pod 'rc-pending-missing-pvc' 的详细状态和事件信息","level":"important","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-missing-pvc -n aiops-e2e","purpose":"获取 Pod 的详细状态和事件信息，确认调度失败的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 验证 PVC 'rc-pending-definitely-missing-pvc' 是否... | `kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_describe | 验证 Pod 'rc-pending-missing-pvc' 的详细状态和事件信息 | `kubectl describe pod rc-pending-missing-pvc -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (16.2s)
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
   ✅ [汇总总结] 完成 (56.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3584 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 36.3s
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
| **问题分类** | 调度失败 |
| **置信度** | 高 (95%) |
| **证据完整度** | 2/2 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | rc-pending-missing-pvc |
| Namespace | aiops-e2e |
| 错误信息 | PVC 'rc-pending-definitely-missing-pvc' 未找到 |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod rc-pending-missing-pvc` | `Warning: FailedScheduling 0/3 nodes are available: persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found.` | Pod 无法调度，原因为 PVC 未找到 |
| 2 | PVC 存在性 | `kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e` | `Error from server (NotFound): persistentvolumeclaims "rc-pending-definitely-missing-pvc" not found` | PVC 未创建或命名错误 |

### 证据关联分析

- **证据 #1 印证**：Pod 事件 `FailedScheduling` 明确指出 PVC `rc-pending-definitely-missing-pvc` 未找到。
- **证据 #2 印证**：尝试获取 PVC 时返回 `NotFound`，确认 PVC 不存在或命名错误。

### 缺失证据（无）

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ PVC 'rc-pending-definitely-missing-pvc' 未创建或命名错误         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod 依赖的 PVC 未绑定，导致调度器无法分配节点                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 调度失败事件 `persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found` 被触发 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-pending-missing-pvc 状态为 Pending，无法调度              │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1（`FailedScheduling` 事件）和证据 #2（`PVC 未找到`），问题的根本原因是 **PVC 'rc-pending-definitely-missing-pvc' 未创建或命名错误**，导致 Pod 无法调度。  
**置信度**：高 (95%)  
- ✅ `FailedScheduling` 事件明确指出 PVC 未找到  
- ✅ `kubectl get pvc` 验证 PVC 不存在  

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 创建缺失的 PVC**

```bash
kubectl create -f - <<EOF
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

*依据*：PVC 未创建，需手动创建以满足 Pod 调度需求。

**2. [可选] 验证 PVC 是否绑定成功**

```bash
kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e
```

*目的*：确认 PVC 已成功创建并绑定到存储类（如存在）。

### 后续优化

1. **自动化检查**：编写脚本或使用 Operator 监控 PVC 是否缺失。
2. **命名规范**：确保 PVC 名称与 Pod 定义一致，避免拼写错误。
3. **文档化**：记录 PVC 的创建流程，确保团队成员了解依赖关系。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 PVC 存在 | `kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e` | STATUS: Bound |
| 2. 确认 Pod 运行 | `kubectl get pod rc-pending-missing-pvc -n aiops-e2e` | STATUS: Running |
| 3. 检查调度事件 | `kubectl describe pod rc-pending-missing-pvc -n aiops-e2e` | 无 `FailedScheduling` 事件 |

---

## ⚠️ 注意事项

- 如果 PVC 创建后 Pod 仍未调度成功，需进一步检查 PVC 的 StorageClass 配置是否匹配。
- 如果 PVC 名称拼写错误，需修改 Pod 定义中的 PVC 名称以匹配。
- 确保 PVC 的 StorageClass 在集群中存在并可用。

---

## 📊 性能统计

├─ 总耗时: 3.6m
├─ 问题定位: 56.4s (26%) ✅
├─ 证据链采集: 87.3s (40%) ✅
├─ 根因分析: 16.2s (7%) ✅
├─ 汇总总结: 56.3s (26%) ✅
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
