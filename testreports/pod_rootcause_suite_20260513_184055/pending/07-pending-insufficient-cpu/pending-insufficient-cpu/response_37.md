======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 6f4072fb68514024]

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
      📄 NAME                          READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-cpu   0/1     Pending   0          88m   <none>   <
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
13m (x15 over 83m)   Warning   FailedScheduling   Pod/rc-pending-insufficient-cpu   0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No pre
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-cpu   0/1     Pending   0          88m   <none>   <
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-cpu   0/1     Pending   0          88m   <none>   <
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (44.5s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '集群CPU资源不足', 'probability': '高', 'reason': 'Events显示3个节点Insufficient cpu，且没有找到可抢占的资源，表明集群CPU资源不足导致Pod无法调度。'}, {'scenario': 'Pod资源配置不合理', 'probability': '中', 'reason': 'Pod可能请求了超过集群可用的CPU资源，需检查Pod的资源配置。'}, {'scenario': '调度器配置问题', 'probability': '低', 'reason': '调度器配置可能限制了Pod的调度，但节点状态正常，因此可能性较低。'}]
   entities=[{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在1个Pod处于Pending状态，其异常类型为PendingUnschedulable，属于L1层级。事件信息显示调度失败原因为3个节点Insufficient cpu，且没有找到可抢占的资源，表明集群存在资源不足问题，影响Pod调度。节点状态均正常（Ready），因此L1层代表调度层面的问题，而非节点层面故障。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "Node/Resource Pressure", "confidence": 0.95, "reasoning": "当前环境中存在1个Pod处于Pending状态，其异常类型为PendingUnschedulable，属于L1层级。事件信息显示调度失败原因为3个节点Insufficient cpu，且没有找到可抢占的资源，表明集群存在资源不足问题，影响Pod调度。节点状态均正常（Ready），因此L1层代表调度层面的问题，而非节点层面故障。", "abnormal_pods": [{"name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "集群CPU资源不足", "probability": "高", "reason": "Events显示3个节点Insufficient cpu，且没有找到可抢占的资源，表明集群CPU资源不足导致Pod无法调度。"}, {"scenario": "Pod资源配置不合理", "probability": "中", "reason": "Pod可能请求了超过集群可用的CPU资源，需检查Pod的资源配置。"}, {"scenario": "调度器配置问题", "probability": "低", "reason": "调度器配置可能限制了Pod的调度，但节点状态正常，因此可能性较低。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-pending-insufficient-cpu                         0/1     Pending     0             88m    <none>           <none>   <none>           <none>            app=rc-pending-insufficient-cpu,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/6f4072fb68514024/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/6f4072fb68514024/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/6f4072fb68514024/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (1m 4.4s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 rc-pending-insufficient-cpu Pod 的调度失败原因","level":"critical","tool":"kubectl_events","command":"kubectl get events --field-selector=reason=FailedScheduling -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","field_selector":"reason=FailedScheduling"},"purpose":"确认 FailedScheduling 事件的具体原因，例如资源不足、taint 不匹配等","evidence_type":"event","target_scope":"Pod/aiops-e2e/rc-pending-insufficient-cpu","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"e2","description":"检查 rc-pending-insufficient-cpu Pod 的资源配置","level":"important","tool":"kubectl_get_by_name","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","tool_args":{"name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e","output":"yaml"},"purpose":"确认 Pod 请求的资源是否超过集群可用资源，例如 CPU、内存等","evidence_type":"resource_definition","target_scope":"Pod/aiops-e2e/rc-pending-insufficient-cpu","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e3","description":"检查节点的资源使用情况","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o wide","tool_args":{},"purpose":"确认节点的资源使用情况，例如 CPU、内存等是否充足","evidence_type":"node_status","target_scope":"Cluster","acceptable_tools":["kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 6 个，匹配计划 3 个，未规划证据 3 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":3,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"验证 rc-pending-insufficient-cpu Pod 的调度失败原因","level":"critical","tool":"kubectl_events","command":"kubectl get events --field-selector=reason=FailedScheduling -n aiops-e2e","purpose":"确认 FailedScheduling 事件的具体原因，例如资源不足、taint 不匹配等","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"e2","description":"检查 rc-pending-insufficient-cpu Pod 的资源配置","level":"important","tool":"kubectl_get_by_name","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","purpose":"确认 Pod 请求的资源是否超过集群可用资源，例如 CPU、内存等","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"e3","description":"检查节点的资源使用情况","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o wide","purpose":"确认节点的资源使用情况，例如 CPU、内存等是否充足","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_events | 验证 rc-pending-insufficient-cpu Pod 的调度失败原因 | `kubectl get events --field-selector=reason=FailedScheduling -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_by_name | 检查 rc-pending-insufficient-cpu Pod 的资源配置 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_get_by_kind_in_cl... | 检查节点的资源使用情况 | `kubectl get nodes -o wide` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (40.4s)
   📤 → 下游数据: root_cause=集群CPU资源不足导致rc-pending-insufficient-cpu Pod无法调度。Events 显示 3 个节点 Insufficient cpu，且没有可抢占的资源，表明集群 CPU 资源不足。
   confidence=95%
   causal_chain={"root_cause": "集群CPU资源不足", "intermediate_causes": ["rc-pending-insufficient-cpu Pod请求的CPU资源超过集群可用资源"], "immediate_causes": ["Pod调度失败事件显示3个节点Insufficient cpu"], "phenomena": ["rc-pending-insufficient-cpu Pod处于Pending状态"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"tool": "kubectl_events", "description": "Pod调度失败的事件日志，显示3个节点Insufficient cpu，且没有可抢占的资源。"}, {"tool": "kubectl_get_by_name", "description": "rc-pending-insufficient-cpu Pod的状态为Pending，未显示具体原因。"}, {"tool": "kubectl_get_by_kind_in_cluster", "description": "集群中存在1个Pending状态的Pod，其余Pod状态正常。"}, {"tool": "kubectl_get_by_kind_in_cluster", "description": "节点状态正常（Ready），未发现节点层面的异常。"}], "evidence_analysis": [{"tool": "kubectl_events", "analysis": "Events 显示 rc-pending-insufficient-cpu 调度失败原因是 3 个节点 Insufficient cpu，且没有可抢占的资源。这表明集群 CPU 资源不足。"}, {"tool": "kubectl_get_by_name", "analysis": "rc-pending-insufficient-cpu Pod 当前状态为 Pending，未提供额外的调度失败信息。"}, {"tool": "kubectl_get_by_kind_in_cluster", "analysis": "集群中 1 个 Pod 处于 Pending 状态，其余 46 个 Pod 正常。节点状态为 Ready，未发现节点异常。"}], "causal_chain": {"root_cause": "集群CPU资源不足", "intermediate_causes": ["rc-pending-insufficient-cpu Pod请求的CPU资源超过集群可用资源"], "immediate_causes": ["Pod调度失败事件显示3个节点Insufficient cpu"], "phenomena": ["rc-pending-insufficient-cpu Pod处于Pending状态"]}, "root_cause": "集群CPU资源不足导致rc-pending-insufficient-cpu Pod无法调度。Events 显示 3 个节点 Insufficient cpu，且没有可抢占的资源，表明集群 CPU 资源不足。", "root_cause_summary": "集群CPU资源不足导致rc-pending-insufficient-cpu Pod无法调度。Events 显示 3 个节点 Insufficient cpu，且没有可抢占的资源，表明集群 CPU 资源不足。", "confidence": 0.95, "confidence_reason": "Events 显示 rc-pending-insufficient-cpu 调度失败原因是 3 个节点 Insufficient cpu，且没有可抢占的资源。这表明集群 CPU 资源不足，因果链清晰。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"scenario": "Pod资源配置不合理", "probability": "中", "reason": "Pod可能请求了超过集群可用的CPU资源，需检查Pod的资源配置。"}, {"scenario": "调度器配置问题", "probability": "低", "reason": "调度器配置可能限制了Pod的调度，但节点状态正常，因此可能性较低。"}], "limitations": "未提供rc-pending-insufficient-cpu Pod的具体资源配置信息，无法确认其请求的CPU资源量。", "llm_raw_analysis": "根据提供的证据，rc-pending-insufficient-cpu Pod 处于 Pending 状态，且调度失败原因是 3 个节点 Insufficient cpu，且没有可抢占的资源。这表明集群 CPU 资源不足，导致该 Pod 无法调度。节点状态正常（Ready），排除了节点层面的问题。因此，集群 CPU 资源不足是导致该 Pod 无法调度的根因。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群CPU资源不足导致rc-pending-insufficient-cpu Pod无法调度。Events 显示 3 个节点 Insufficient cpu，且没有可抢占的资源，表明集群 CPU 资源不足。
   置信度: 95%
   🔗 因果链:
     根本原因: 集群CPU资源不足


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 52.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3790 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 22.0s
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
| **兼容归因层** | L1 - 调度层面问题 |
| **问题分类** | 调度失败（Insufficient cpu） |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/3 (100%) |

---

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题？

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-pending-insufficient-cpu |
| Namespace | aiops-e2e |
| Node | 无（尚未调度） |
| 错误信息 | 0/3 nodes are available: 3 Insufficient cpu |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 调度失败事件 | `kubectl events` | `Warning FailedScheduling Pod/rc-pending-insufficient-cpu 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` | Pod 无法调度，原因是集群 CPU 资源不足 |
| 2 | Pod 详细信息 | `kubectl get pod -n aiops-e2e rc-pending-insufficient-cpu` | `STATUS: Pending, RESTARTS: 0, AGE: 88m` | Pod 仍处于 Pending 状态，未被调度 |
| 3 | 节点资源状态 | `kubectl get node` | `3 nodes, status: Ready` | 节点状态正常，无节点不可用 |

### 证据关联分析
- **证据 #1 印证**：`Warning FailedScheduling` 明确指出 3 个节点均因 `Insufficient cpu` 无法调度该 Pod，表明集群整体 CPU 资源不足。
- **证据 #2 印证**：Pod 仍处于 Pending 状态，未被调度，且无重启，表明调度失败是当前状态的根本原因。
- **证据 #3 印证**：节点状态正常（Ready），排除了节点故障或不可用的可能，进一步确认问题出在资源不足。

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 集群 CPU 资源不足，无法满足 Pod 的 CPU 请求                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 调度器尝试在 3 个节点上调度 Pod，但所有节点均显示 Insufficient cpu |
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod 无法被调度，事件显示 3/3 节点均因 CPU 不足无法调度           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Pending，未被调度，持续显示调度失败事件             │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1（`Warning FailedScheduling` 事件显示 3 个节点均因 `Insufficient cpu` 无法调度 Pod）和证据 #3（节点状态正常），问题的根本原因是**集群 CPU 资源不足**，无法满足 `rc-pending-insufficient-cpu` Pod 的 CPU 请求，导致其无法被调度。
**置信度**：高 (95%)
- ✅ 事件明确指出资源不足
- ✅ 节点状态正常，排除节点层面故障
- ⚠️ 缺少 Pod 的具体资源配置（如 CPU 请求和限制），无法进一步判断其请求量是否合理

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 增加节点 CPU 资源**
```bash
kubectl scale node <node_name> --cpu=新增的CPU数量
```
*依据*：当前 3 个节点均因 CPU 不足无法调度 Pod，建议增加节点资源或添加新节点。

**2. [可选] 调整 Pod 的 CPU 请求**
```bash
kubectl set resources pod/rc-pending-insufficient-cpu -n aiops-e2e --requests=cpu=0.5
```
*依据*：如果该 Pod 请求的 CPU 资源过高，可适当降低其请求值以适应当前资源。

**3. [可选] 查看 Pod 的资源配置**
```bash
kubectl get pod/rc-pending-insufficient-cpu -n aiops-e2e -o yaml
```
*目的*：确认 Pod 的 CPU 请求和限制，以便进一步优化资源配置。

### 后续优化
1. **集群资源规划**：评估当前集群的 CPU 资源是否满足业务需求，考虑扩容或优化资源分配。
2. **资源监控**：部署 Prometheus 或使用 `kubectl top node` 监控节点资源使用情况。
3. **弹性扩缩容**：配置 HPA 或 Cluster Autoscaler 实现自动扩缩容，以应对资源不足问题。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 是否调度成功 | `kubectl get pod/rc-pending-insufficient-cpu -n aiops-e2e` | STATUS: Running |
| 2. 检查节点资源使用 | `kubectl describe node <node_name>` | CPU Allocatable 和 Usage 增加 |
| 3. 查看调度事件 | `kubectl describe pod/rc-pending-insufficient-cpu -n aiops-e2e` | 无 `FailedScheduling` 事件 |

---

## ⚠️ 注意事项
- 如果问题持续，建议进一步检查 Pod 的资源配置（如 CPU 请求和限制）是否合理。
- 考虑使用 Cluster Autoscaler 自动扩展节点以应对资源不足。
- 优先确保关键业务 Pod 能获得足够的资源。

---

---

## 📊 性能统计

├─ 总耗时: 4.4m
├─ 问题定位: 44.5s (17%) ✅
├─ 证据链采集: 64.4s (25%) ✅
├─ 根因分析: 40.4s (15%) ✅
├─ 汇总总结: 112.7s (43%) ✅
├─ LLM 调用: 5 次
└─ 工具调用: 10 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 10 次
- **LLM 调用**: 5 次


======================================================================
✅ 诊断完成!
======================================================================
