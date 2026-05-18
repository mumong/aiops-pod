======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 837bfb117a434fdd]

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
  Warning  FailedScheduling  31s   default-scheduler  0/3 nodes are available: 3 Insuffi
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-cpu   0/1     Pending   0          34s   <none>   <
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Pending': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS      RESTARTS      
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-cpu   0/1     Pending   0          40s   <none>   <
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (36.2s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '资源不足导致调度失败', 'probability': '高', 'reason': '事件描述显示 0/3 nodes are available: 3 Insufficient cpu'}]
   entities=[{"type": "pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}]
   reasoning=当前仍异常的 Pod 为 aiops-e2e/rc-pending-insufficient-cpu，状态为 Pending，异常类型为 PendingUnschedulable，归一化为 L1。事件描述指出 0/3 nodes are available: 3 Insufficient cpu，说明是资源不足导致的调度失败，属于 L1 层级。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "Node / Scheduling", "confidence": 0.95, "reasoning": "当前仍异常的 Pod 为 aiops-e2e/rc-pending-insufficient-cpu，状态为 Pending，异常类型为 PendingUnschedulable，归一化为 L1。事件描述指出 0/3 nodes are available: 3 Insufficient cpu，说明是资源不足导致的调度失败，属于 L1 层级。", "abnormal_pods": [{"name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "资源不足导致调度失败", "probability": "高", "reason": "事件描述显示 0/3 nodes are available: 3 Insufficient cpu"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-insufficient-cpu                         0/1     Pending     0                27s    <none>           <none>   <none>           <none>            app=rc-pending-insufficient-cpu,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/837bfb117a434fdd/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/837bfb117a434fdd/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/837bfb117a434fdd/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  3m13s  default-scheduler  0/3 nodes are available: 3 Insuff
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (2m 16.4s)
   📤 → 下游数据: evidence_items=8/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 aiops-e2e 命名空间中 rc-pending-insufficient-cpu Pod 的详细描述，验证其调度失败的原因，例如资源不足、nodeSelector/affinity 不匹配、taint 不匹配等。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-pending-insufficient-cpu","kind":"pod"},"purpose":"验证 Pod 调度失败的详细原因，例如资源不足、nodeSelector/affinity 不匹配、taint 不匹配等。","evidence_type":"pod_description","target_scope":"aiops-e2e/rc-pending-insufficient-cpu","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取 aiops-e2e 命名空间中 rc-pending-insufficient-cpu Pod 的事件记录，验证是否有 FailedScheduling 事件，以及事件中的具体原因，例如资源不足、taint 不匹配等。","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-pending-insufficient-cpu","tool_args":{"namespace":"aiops-e2e","name":"rc-pending-insufficient-cpu","kind":"pod"},"purpose":"验证 Pod 是否存在 FailedScheduling 事件，以及事件中的具体原因，例如资源不足、taint 不匹配等。","evidence_type":"pod_events","target_scope":"aiops-e2e/rc-pending-insufficient-cpu","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"e3","description":"验证集群中所有节点的资源使用情况，确认是否存在资源不足的问题，例如 CPU、内存等。","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","tool_args":{"kind":"node"},"purpose":"确认节点资源是否不足，例如 CPU、内存等。","evidence_type":"node_resources","target_scope":"cluster","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  3m13s  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nName:             rc-pending-insufficient-cpu\nLabels:           app=rc-pending-insufficient-cpu\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/837bfb117a434fdd/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/837bfb117a434fdd/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/837bfb117a434fdd/tools/001-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 8/9 项，完整度 89%；实际执行工具 7 个，匹配计划 2 个，未规划证据 5 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":9,"environment_evidence_collected":8,"environment_evidence_completeness":0.8888888888888888,"executed_tool_count":7,"matched_tool_count":2,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"获取 aiops-e2e 命名空间中 rc-pending-insufficient-cpu Pod 的详细描述，验证其调度失败的原因，例如资源不足、nodeSelector/affinity 不匹配、taint 不匹配等。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","purpose":"验证 Pod 调度失败的详细原因，例如资源不足、nodeSelector/affinity 不匹配、taint 不匹配等。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 aiops-e2e 命名空间中 rc-pending-insufficient-cpu Pod 的事件记录，验证是否有 FailedScheduling 事件，以及事件中的具体原因，例如资源不足、taint 不匹配等。","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-pending-insufficient-cpu","purpose":"验证 Pod 是否存在 FailedScheduling 事件，以及事件中的具体原因，例如资源不足、taint 不匹配等。","collected":false,"source":"planned","outcome":"unknown"},{"id":"e3","description":"验证集群中所有节点的资源使用情况，确认是否存在资源不足的问题，例如 CPU、内存等。","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o json","purpose":"确认节点资源是否不足，例如 CPU、内存等。","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e2(获取 aiops-e2e 命名空间中 rc-pending-insufficient-cpu Pod 的事件记录，验证是否有 FailedScheduling 事件，以及事件中的具体原因，例如资源不足、taint 不匹配等。): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 89%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 aiops-e2e 命名空间中 rc-pending-insufficient-cp... | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` |
   | e2 | critical | ❌ | kubectl_events | 获取 aiops-e2e 命名空间中 rc-pending-insufficient-cp... | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-pendi...` |
   | e3 | important | ✅ | kubectl_get_by_kind_in_cl... | 验证集群中所有节点的资源使用情况，确认是否存在资源不足的问题，例如 CPU、内存等。 | `kubectl get nodes -o json` |

   ⚠️ 未采集原因:
   - e2(获取 aiops-e2e 命名空间中 rc-pending-insufficient-cpu Pod 的事件记录，验证是否有 FailedScheduling 事件，以及事件中的具体原因，例如资源不足、taint 不匹配等。): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (25.8s)
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
   ✅ [汇总总结] 完成 (1m 15.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4079 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 34.3s
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
| **兼容归因层** | L1 - 调度失败 |
| **问题分类** | 资源不足导致调度失败 |
| **置信度** | 高 (95%) |
| **证据完整度** | 2/3 (67%) |

---

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-pending-insufficient-cpu |
| Namespace | aiops-e2e |
| Node | <none> |
| 错误信息 | 0/3 nodes are available: 3 Insufficient cpu |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: Pending`, `REASON: PendingUnschedulable`, `Events: Warning FailedScheduling 0/3 nodes are available: 3 Insufficient cpu` | Pod 无法调度，原因是 CPU 资源不足 |
| 2 | Node 资源状态 | `kubectl get node` | `status_counts={'Ready': 3}` | 所有节点状态正常，但资源不足 |
| 3 | Pod 详细信息 | `kubectl describe pod` | `Warning FailedScheduling 0/3 nodes are available: 3 Insufficient cpu` | 明确指出调度失败是由于 CPU 资源不足 |

### 证据关联分析
- **证据 #1 + #3 印证**：Pod 的 `FailedScheduling` 事件与 `0/3 nodes are available: 3 Insufficient cpu` 明确指向 CPU 资源不足
- **证据链**：Pod 请求的 CPU 资源 > 集群可用 CPU → 无法调度 → Pod 保持 Pending 状态

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 的完整事件记录 | critical | 无法验证是否有其他调度失败原因（如 nodeSelector、affinity、taint 不匹配） |

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 请求的 CPU 资源超过集群当前可用资源                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 调度器无法找到满足 CPU 请求的节点 → 无法调度                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 调度失败事件（0/3 nodes are available: 3 Insufficient cpu）     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Pending，无法启动                                    │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (Pod 状态为 Pending, Reason: PendingUnschedulable) 和证据 #3 (Events 明确指出 `0/3 nodes are available: 3 Insufficient cpu`)，问题的根本原因是**Pod 请求的 CPU 资源超出当前集群可用资源**，导致调度失败。
**置信度**：高 (95%)
- ✅ `kubectl describe pod` 明确指出调度失败是由于 CPU 不足
- ⚠️ 缺少完整的事件记录，无法排除其他调度失败原因（如 taint、nodeSelector、affinity 不匹配）

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 增加节点资源或调整 Pod 资源请求**
```bash
# 选项1：添加更多节点（假设集群支持自动扩缩容）
kubectl scale nodepool <nodepool-name> --replicas=4

# 选项2：降低 Pod 的 CPU 请求（临时缓解）
kubectl set resources pod/rc-pending-insufficient-cpu -n aiops-e2e --requests=cpu=500m
```
*依据*：当前调度失败明确指向 CPU 不足，建议增加节点资源或降低请求

**2. [可选] 检查 Pod 的 nodeSelector/affinity/taint**
```bash
kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e | grep -iE 'nodeSelector|affinity|taint'
```
*目的*：确认是否有额外调度约束（如 nodeSelector 不匹配）

### 后续优化
1. **监控资源使用**：配置资源使用监控（如 Prometheus + Grafana），观察 CPU 使用率
2. **优化调度策略**：启用 `preemption` 或 `priorityClass` 以提高关键 Pod 的调度优先级
3. **资源规划**：评估工作负载资源需求，合理分配 CPU/内存限制和请求

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e` | STATUS: Running |
| 2. 检查调度事件 | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` | 无 FailedScheduling 事件 |
| 3. 检查节点资源 | `kubectl describe node <node-name>` | CPU 可用量 >= Pod 请求量 |

---

## ⚠️ 注意事项
- 如果集群使用节点池（NodePool）或自动扩缩容，请确保扩缩容策略配置正确
- 如果问题反复出现，考虑使用 HPA（Horizontal Pod Autoscaler）或 VPA（Vertical Pod Autoscaler）自动调整资源
- 确保所有节点的标签（Labels）与 Pod 的 nodeSelector/affinity 匹配

---

## 📎 附录
- **事件记录缺失**：建议执行 `kubectl get events -n aiops-e2e` 获取完整的事件日志
- **Pod 详细配置**：建议执行 `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml` 查看完整的资源请求和调度约束

---

## 📊 性能统计

├─ 总耗时: 4.6m
├─ 问题定位: 36.2s (13%) ✅
├─ 证据链采集: 136.4s (50%) ✅
├─ 根因分析: 25.8s (9%) ✅
├─ 汇总总结: 75.9s (28%) ✅
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
