======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 6aafd329d8b24393]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Running': 46}
NAMESPACE     NAME                                                READY   STATUS              RESTARTS         AGE
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
      📄 NAME                       READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-volume-missing-secret   0/1     ContainerCreating   0          22m
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
2m1s (x18 over 22m)   Warning   FailedMount   Pod/rc-volume-missing-secret   MountVolume.SetUp failed for volume "missing-secret" : secret "rc-definitely-missing-secret" not 
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                       READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-volume-missing-secret   0/1     ContainerCreating   0          22m
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=187 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide secret rc-definitely-missing-secret -n aiops-e2e
Error from server (NotFound): secrets "rc-de
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": 0.95,
  "reasoning": "Pod 'rc-volume-missing-secret' 处于 ContainerCreating 状态，且事件中显示 'secret \"rc-definitely-missing-secret\" not found'。进一步确认发现该 Secret 不存在，表明 Pod 的 VolumeMountFailed 是由于引用了缺失的 Secret 对象。这属于配置错误（ConfigError）。",
  "abnormal_pods": [
    {
      "name": "rc-volume-missing-secret",
      "namespace": "aiops-e2e",
      "status": "ContainerCreating",
      "reason": "FailedMount",
      "message": "MountVolume.SetUp failed for volume 'missing-secret': secret 'rc-definitely-missing-secret' not found"
    }
  ],
  "abnormal_groups": [
    {
      "pod_abnormal_type": "VolumeMountFailed",
      "count": 1
    }
  ],
  "pod_status_keyword": "ContainerCreating",
  "pod_abnormal_type": "VolumeMountFailed",
  "status_category": "VolumeMountFailed",
  "key_entities": [
    {
      "kind": "Pod",
      "name": "rc-volume-missing-secret",
      "namespace": "aiops-e2e"
    },
    {
      "kind": "Secret",
      "name": "rc-definitely-missing-secret",
      "namespace": "aiops-e2e"
    }
  ],
  "possible_scenarios": [
    {
      "scenario": "Pod 引用了不存在的 Secret",
      "evidence": "Events 显示 'secret \"rc-definitely-missing-secret\" not found'，且 kubectl get secret 无法找到该 Secret"
    }
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (49.1s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'Pod 引用了不存在的 Secret', 'probability': 'high', 'reason': 'Events 显示 \'secret "rc-definitely-missing-secret" not found\'，且 kubectl get secret 无法找到该 Secret'}]
   entities=[{"type": "Pod", "name": "rc-volume-missing-secret", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-definitely-missing-secret", "namespace": "aiops-e2e"}]
   reasoning=Pod 'rc-volume-missing-secret' 处于 ContainerCreating 状态，且事件中显示 'secret "rc-definitely-missing-secret" not found'。进一步确认发现该 Secret 不存在，表明 Pod 的 VolumeMountFailed 是由于引用了缺失的 Secret 对象。这属于配置错误（ConfigError）
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "Pod 'rc-volume-missing-secret' 处于 ContainerCreating 状态，且事件中显示 'secret \"rc-definitely-missing-secret\" not found'。进一步确认发现该 Secret 不存在，表明 Pod 的 VolumeMountFailed 是由于引用了缺失的 Secret 对象。这属于配置错误（ConfigError）", "abnormal_pods": [{"name": "rc-volume-missing-secret", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "VolumeMountFailed", "key_entities": [{"type": "Pod", "name": "rc-volume-missing-secret", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-definitely-missing-secret", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod 引用了不存在的 Secret", "probability": "high", "reason": "Events 显示 'secret \"rc-definitely-missing-secret\" not found'，且 kubectl get secret 无法找到该 Secret"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-secret"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-secret"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-volume-missing-secret                            0/1     ContainerCreating   0                22m     <none>           node1    <none>           <none>            app=rc-volume-missing-secret,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/6aafd329d8b24393/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/6aafd329d8b24393/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/6aafd329d8b24393/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-missing-secret
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  88s (x19 over 23m)  kubelet            MountVolume.SetUp f
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=187 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide secret rc-definitely-missing-secret -n aiops-e2e
Error from server (NotFound): secrets "rc-de
   💭 [证据链采集] 已采集证据:
1. `kubectl describe pod` 显示 Pod rc-volume-missing-secret 挂载失败，具体原因为 secret "rc-definitely-missing-secret" 未找到。
2. `kubectl get secret` 尝试获取 secret rc-definitely-missing-secret 时返回 "NotFound"，确认该 Secret 不存在。

结论:
Pod rc-volume-missing-secret 处于 ContainerCreating 状态，其 VolumeMountFailed 是由于引用了不存在的 Secret "rc-definitely-missing-secret" 所致。此问题属于配置错误（ConfigError）。
   ✅ [证据链采集] 完成 (59.9s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod rc-volume-missing-secret 的详细状态和事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-secret -n aiops-e2e","tool_args":{},"purpose":"获取 Pod 的详细描述信息和事件日志，验证其挂载失败的具体原因","evidence_type":"state_event","target_scope":"aiops-e2e/rc-volume-missing-secret","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"验证 Secret rc-definitely-missing-secret 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-definitely-missing-secret -n aiops-e2e","tool_args":{},"purpose":"确认 Secret 是否存在，以验证挂载失败是否因引用了缺失的 Secret","evidence_type":"resource_absence","target_scope":"aiops-e2e/rc-definitely-missing-secret","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-missing-secret\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  88s (x19 over 23m)  kubelet            MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found\n  Warning  FailedMount  6m7s                kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-secret], unattached volumes=[kube-api-access-8jtht missing-secret]: timed out waiting for the condition\n  Warning  FailedMount  98s (x9 over 21m)   kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-secret], unattached volumes=[missing-secret kube-api-access-8jtht]: timed out waiting for the condition\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed\n    State:          Waiting\n      Reason:       ContainerCreating","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/6aafd329d8b24393/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6aafd329d8b24393/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6aafd329d8b24393/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=187 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide secret rc-definitely-missing-secret -n aiops-e2e\nError from server (NotFound): secrets \"rc-definitely-missing-secret\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/6aafd329d8b24393/tools/002-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/6aafd329d8b24393/tools/002-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/6aafd329d8b24393/tools/002-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集证据:\n1. `kubectl describe pod` 显示 Pod rc-volume-missing-secret 挂载失败，具体原因为 secret \"rc-definitely-missing-secret\" 未找到。\n2. `kubectl get secret` 尝试获取 secret rc-definitely-missing-secret 时返回 \"NotFound\"，确认该 Secret 不存在。\n\n结论:\nPod rc-volume-missing-secret 处于 ContainerCreating 状态，其 VolumeMountFailed 是由于引用了不存在的 Secret \"rc-definitely-missing-secret\" 所致。此问题属于配置错误（ConfigError）。","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 7 个，匹配计划 2 个，未规划证据 5 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":7,"matched_tool_count":2,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证 Pod rc-volume-missing-secret 的详细状态和事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-secret -n aiops-e2e","purpose":"获取 Pod 的详细描述信息和事件日志，验证其挂载失败的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证 Secret rc-definitely-missing-secret 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-definitely-missing-secret -n aiops-e2e","purpose":"确认 Secret 是否存在，以验证挂载失败是否因引用了缺失的 Secret","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod rc-volume-missing-secret 的详细状态和事件 | `kubectl describe pod rc-volume-missing-secret -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_by_name | 验证 Secret rc-definitely-missing-secret 是否存在 | `kubectl get secret rc-definitely-missing-secret -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (21.1s)
   📤 → 下游数据: root_cause=[L4层] 当前无法基于 LLM 输出确定根本原因
   confidence=10%
   causal_chain={"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}
   rca_analysis={"phenomenon": "我的集群有什么问题", "evidence_analysis": [], "causal_chain": {"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}, "root_cause": "[L4层] 当前无法基于 LLM 输出确定根本原因", "confidence": 0.1, "confidence_reason": "LLM 返回结果不符合 RCA 结构化输出合同", "alternative_causes": []}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: [L4层] 当前无法基于 LLM 输出确定根本原因
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
   ✅ [汇总总结] 完成 (1m 33.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4252 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 43.1s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ContainerCreating |
| **兼容归因层** | L4 |
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
| Pod | rc-volume-missing-secret |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | `MountVolume.SetUp failed for volume "missing-secret": secret "rc-definitely-missing-secret" not found` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod rc-volume-missing-secret` | `status: ContainerCreating`, `Events: FailedMount` | Pod 无法创建，挂载失败 |
| 2 | Secret 存在性 | `kubectl get secret rc-definitely-missing-secret -n aiops-e2e` | `Error from server (NotFound): secrets "rc-definitely-missing-secret" not found` | Secret 不存在，导致卷挂载失败 |
| 3 | Events 信息 | `kubectl get events` | `MountVolume.SetUp failed for volume "missing-secret": secret "rc-definitely-missing-secret" not found` | 明确指出 Secret 缺失 |
| 4 | Pod 事件摘要 | `kubectl describe pod` | `Warning  FailedMount  88s (x19 over 23m)  kubelet            MountVolume.SetUp failed` | Pod 持续尝试挂载失败 |
| 5 | kubectl get pods | `kubectl get pods -n aiops-e2e` | `rc-volume-missing-secret 0/1 ContainerCreating` | Pod 无法正常启动 |
| 6 | kubectl get secret | `kubectl get secret rc-definitely-missing-secret -n aiops-e2e` | `NotFound` | Secret 不存在 |
| 7 | Events 多次失败 | `kubectl get events` | `Warning FailedMount (x18 over 22m)` | 持续尝试挂载失败 |

### 证据关联分析

- **证据 #1 + #3 印证**：Pod 状态为 `ContainerCreating`，Events 明确指出 `secret "rc-definitely-missing-secret" not found`，说明是卷挂载失败。
- **证据 #2 印证**：尝试获取 Secret 时返回 `NotFound`，说明配置中引用了不存在的 Secret。
- **证据链**：Pod 的 `volume` 引用了不存在的 Secret → 挂载失败 → Pod 无法启动 → 持续重启或卡在 `ContainerCreating`。

### 缺失证据（无）

无缺失证据，所有关键证据已采集。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Secret "rc-definitely-missing-secret" 不存在，导致 Pod 挂载失败     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod 的 volume 引用了不存在的 Secret，MountVolume.SetUp 失败     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 挂载失败，Pod 无法进入 Running 状态，状态为 ContainerCreating    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 ContainerCreating，Events 显示 secret not found      │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态为 ContainerCreating) 和证据 #2 (Secret 不存在)，问题的根本原因是 **Pod 引用了不存在的 Secret `rc-definitely-missing-secret`**，导致卷挂载失败，Pod 无法启动。

**置信度**：高 (95%)  
- ✅ Events 明确指出 `secret not found`  
- ✅ `kubectl get secret` 返回 `NotFound`

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 创建缺失的 Secret**
```bash
kubectl create secret generic rc-definitely-missing-secret -n aiops-e2e --from-literal=data=example
```
*依据*：Events 明确指出缺失该 Secret

**2. [可选] 检查 Pod 的 volume 配置**
```bash
kubectl get pod rc-volume-missing-secret -n aiops-e2e -o jsonpath='{.spec.volumes}'
```
*目的*：确认 Pod 是否确实引用了 `missing-secret` 卷

### 后续优化

1. **配置验证**：在部署前添加 Secret 存在性检查
2. **CI/CD 集成**：确保 Secret 在部署前已创建
3. **监控事件**：配置事件告警，当出现 `FailedMount` 时及时通知
4. **文档更新**：记录该 Secret 的用途和创建方法，避免重复问题

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Secret 存在 | `kubectl get secret rc-definitely-missing-secret -n aiops-e2e` | 应返回 Secret 信息 |
| 2. 确认 Pod 状态 | `kubectl get pod rc-volume-missing-secret -n aiops-e2e` | STATUS: Running |
| 3. 检查事件 | `kubectl get events -n aiops-e2e` | 无 `FailedMount` 事件 |

---

## ⚠️ 注意事项

- 如果 Secret 不需要，应修改 Pod 的 volume 配置，移除对它的引用
- 如果 Secret 是测试用，建议创建后删除，并更新 Pod 配置以避免依赖缺失的资源
- 建议在部署流程中加入 Secret 存在性校验，避免类似问题再次发生

---

## 📊 性能统计

├─ 总耗时: 3.7m
├─ 问题定位: 49.1s (22%) ✅
├─ 证据链采集: 59.9s (27%) ✅
├─ 根因分析: 21.1s (9%) ✅
├─ 汇总总结: 93.0s (42%) ✅
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
