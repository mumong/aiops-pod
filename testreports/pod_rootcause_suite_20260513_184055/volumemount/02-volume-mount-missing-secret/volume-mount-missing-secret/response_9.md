======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 47c3f6db245741b6]

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
rc-volume-missing-secret   0/1     ContainerCreating   0          17m
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
68s (x16 over 17m)   Warning   FailedMount   Pod/rc-volume-missing-secret   MountVolume.SetUp failed for volume "missing-secret" : secret "rc-definitely-missing-secret" not f
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
  "reasoning": "Pod 'rc-volume-missing-secret' 处于 ContainerCreating 状态，Events 显示 'secret \"rc-definitely-missing-secret\" not found'，且尝试获取该 Secret 时返回 'Error from server (NotFound)'。这表明 Pod 的 volume 引用了不存在的 Secret，属于典型的 ConfigError 类型。",
  "abnormal_pods": [
    {
      "name": "rc-volume-missing-secret",
      "namespace": "aiops-e2e",
      "status": "ContainerCreating",
      "pod_abnormal_type": "VolumeMountFailed"
    }
  ],
  "abnormal_groups": {
    "VolumeMountFailed": [
      {
        "name": "rc-volume-missing-secret",
        "namespace": "aiops-e2e",
        "status": "ContainerCreating"
      }
    ]
  },
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
    "Pod 'rc-volume-missing-secret' 的 volume 引用了不存在的 Secret 'rc-definitely-missing-secret'。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (43.5s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': "Pod 'rc-volume-missing-secret' 的 volume 引用了不存在的 Secret 'rc-definitely-missing-secret'。", 'probability': '', 'reason': ''}]
   entities=[{"type": "Pod", "name": "rc-volume-missing-secret", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-definitely-missing-secret", "namespace": "aiops-e2e"}]
   reasoning=Pod 'rc-volume-missing-secret' 处于 ContainerCreating 状态，Events 显示 'secret "rc-definitely-missing-secret" not found'，且尝试获取该 Secret 时返回 'Error from server (NotFound)'。这表明 Pod 的 volume 引用了不存在的 Secret，属于典型的 ConfigError 类型。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.5, "reasoning": "Pod 'rc-volume-missing-secret' 处于 ContainerCreating 状态，Events 显示 'secret \"rc-definitely-missing-secret\" not found'，且尝试获取该 Secret 时返回 'Error from server (NotFound)'。这表明 Pod 的 volume 引用了不存在的 Secret，属于典型的 ConfigError 类型。", "abnormal_pods": [{"name": "rc-volume-missing-secret", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "VolumeMountFailed", "key_entities": [{"type": "Pod", "name": "rc-volume-missing-secret", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-definitely-missing-secret", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod 'rc-volume-missing-secret' 的 volume 引用了不存在的 Secret 'rc-definitely-missing-secret'。", "probability": "", "reason": ""}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-secret"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-secret"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-volume-missing-secret                            0/1     ContainerCreating   0                17m     <none>           node1    <none>           <none>            app=rc-volume-missing-secret,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/47c3f6db245741b6/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/47c3f6db245741b6/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/47c3f6db245741b6/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 50%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=187 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide secret rc-definitely-missing-secret -n aiops-e2e
Error from server (NotFound): secrets "rc-de
   💭 [证据链采集] 已采集证据：
- `kubectl_get_by_name` 确认 Secret `rc-definitely-missing-secret` 不存在，返回 `Error from server (NotFound)`。这表明 Pod `rc-volume-missing-secret` 的 volume 引用了不存在的 Secret。

冲突证据：
- 无。

未采集证据：
- 无（当前证据已满足诊断需求）。
   ✅ [证据链采集] 完成 (44.7s)
   📤 → 下游数据: evidence_items=5/5
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 'rc-volume-missing-secret' 的 volume 引用了不存在的 Secret 'rc-definitely-missing-secret'","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-definitely-missing-secret -n aiops-e2e","tool_args":{"name":"rc-definitely-missing-secret","namespace":"aiops-e2e","kind":"Secret"},"purpose":"确认 Secret 是否存在","evidence_type":"negative","target_scope":"aiops-e2e/rc-definitely-missing-secret","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=187 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide secret rc-definitely-missing-secret -n aiops-e2e\nError from server (NotFound): secrets \"rc-definitely-missing-secret\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/47c3f6db245741b6/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/47c3f6db245741b6/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/47c3f6db245741b6/tools/001-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集证据：\n- `kubectl_get_by_name` 确认 Secret `rc-definitely-missing-secret` 不存在，返回 `Error from server (NotFound)`。这表明 Pod `rc-volume-missing-secret` 的 volume 引用了不存在的 Secret。\n\n冲突证据：\n- 无。\n\n未采集证据：\n- 无（当前证据已满足诊断需求）。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 5/5 项，完整度 100%；实际执行工具 5 个，匹配计划 1 个，未规划证据 4 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":5,"environment_evidence_collected":5,"environment_evidence_completeness":1.0,"executed_tool_count":5,"matched_tool_count":1,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证 Pod 'rc-volume-missing-secret' 的 volume 引用了不存在的 Secret 'rc-definitely-missing-secret'","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-definitely-missing-secret -n aiops-e2e","purpose":"确认 Secret 是否存在","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 验证 Pod 'rc-volume-missing-secret' 的 volume 引用... | `kubectl get secret rc-definitely-missing-secret -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 31.1s)
   📤 → 下游数据: root_cause=Pod 'rc-volume-missing-secret' 处于 ContainerCreating 状态，Events 显示 'MountVolume.SetUp failed for volume "missing-secret" : secret "rc-definitely-missing-secret" not found'，且尝试获取该 Secret 时返回 'Error from server (NotFound)'。这表明 Pod 的 volume 引用了不存在的 Secret，属于典型的 ConfigError 类型。
   confidence=90%
   causal_chain={"root_cause": "Secret 'rc-definitely-missing-secret' 不存在", "intermediate_causes": ["Pod 'rc-volume-missing-secret' 的 volume 引用了不存在的 Secret 'rc-definitely-missing-secret'"], "direct_causes": ["MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found"], "symptoms": ["Pod 'rc-volume-missing-secret' 处于 ContainerCreating 状态"]}
   rca_analysis={"phenomenon": "Pod 'rc-volume-missing-secret' 处于 ContainerCreating 状态，Events 显示 'secret \"rc-definitely-missing-secret\" not found'，且尝试获取该 Secret 时返回 'Error from server (NotFound)'。这表明 Pod 的 volume 引用了不存在的 Secret，属于典型的 ConfigError 类型。", "evidence_inventory": [{"tool": "kubectl_get_by_name", "description": "确认 Secret 'rc-definitely-missing-secret' 不存在", "result": "Error from server (NotFound): secrets \"rc-definitely-missing-secret\" not found"}, {"tool": "kubectl_get_by_kind_in_cluster", "description": "显示 Pod 'rc-volume-missing-secret' 处于 ContainerCreating 状态", "result": "0/1 ContainerCreating"}, {"tool": "kubectl_events", "description": "显示 Pod 'rc-volume-missing-secret' 的 Events 中有 'MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found'", "result": "MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found"}], "evidence_analysis": [{"tool": "kubectl_get_by_name", "description": "Secret 'rc-definitely-missing-secret' 不存在", "result": "Error from server (NotFound): secrets \"rc-definitely-missing-secret\" not found"}, {"tool": "kubectl_get_by_kind_in_cluster", "description": "Pod 'rc-volume-missing-secret' 处于 ContainerCreating 状态", "result": "0/1 ContainerCreating"}, {"tool": "kubectl_events", "description": "Pod 'rc-volume-missing-secret' 的 Events 显示 MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found", "result": "MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found"}], "causal_chain": {"root_cause": "Secret 'rc-definitely-missing-secret' 不存在", "intermediate_causes": ["Pod 'rc-volume-missing-secret' 的 volume 引用了不存在的 Secret 'rc-definitely-missing-secret'"], "direct_causes": ["MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found"], "symptoms": ["Pod 'rc-volume-missing-secret' 处于 ContainerCreating 状态"]}, "root_cause": "Pod 'rc-volume-missing-secret' 处于 ContainerCreating 状态，Events 显示 'MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found'，且尝试获取该 Secret 时返回 'Error from server (NotFound)'。这表明 Pod 的 volume 引用了不存在的 Secret，属于典型的 ConfigError 类型。", "root_cause_summary": "Pod 'rc-volume-missing-secret' 处于 ContainerCreating 状态，Events 显示 'MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found'，且尝试获取该 Secret 时返回 'Error from server (NotFound)'。这表明 Pod 的 volume 引用了不存在的 Secret，属于典型的 ConfigError 类型。", "confidence": 0.9, "confidence_reason": "有直接证据表明 Secret 'rc-definitely-missing-secret' 不存在，且 Pod 'rc-volume-missing-secret' 的 Events 显示 MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [], "limitations": "无", "llm_raw_analysis": "已采集证据：\n- `kubectl_get_by_name` 确认 Secret `rc-definitely-missing-secret` 不存在，返回 `Error from server (NotFound)`。这表明 Pod `rc-volume-missing-secret` 的 volume 引用了不存在的 Secret。\n\n冲突证据：\n- 无。\n\n未采集证据：\n- 无（当前证据已满足诊断需求）。\n\n工具原始输出：\n1. [kubectl_get_by_name]: kubectl_get_by_name 输出摘要: raw_chars=187 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide secret rc-definitely-missing-secret -n aiops-e2e\nError from server (NotFound): secrets \"rc-definitely-missing-secret\" not found"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-volume-missing-secret' 处于 ContainerCreating 状态，Events 显示 'MountVolume.SetUp failed for volume "missing-secret" : secret "rc-definitely-missing...
   置信度: 90%
   🔗 因果链:
     根本原因: Secret 'rc-definitely-missing-secret' 不存在


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 26.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4127 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 25.5s
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
| **Pod异常状态** | ContainerCreating |
| **兼容归因层** | L4 |
| **问题分类** | ConfigError（卷挂载失败） |
| **置信度** | 高 (90%) |
| **证据完整度** | 1/1 (100%) |

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
| 错误信息 | secret "rc-definitely-missing-secret" not found |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod rc-volume-missing-secret -n aiops-e2e` | `STATUS: ContainerCreating` | Pod 无法创建，处于挂起状态 |
| 2 | Pod Events | `kubectl describe pod rc-volume-missing-secret -n aiops-e2e` | `MountVolume.SetUp failed for volume "missing-secret" : secret "rc-definitely-missing-secret" not found` | 卷挂载失败，Secret 不存在 |
| 3 | Secret 存在性验证 | `kubectl get secret rc-definitely-missing-secret -n aiops-e2e` | `Error from server (NotFound): secrets "rc-definitely-missing-secret" not found` | Secret 确实不存在 |
| 4 | Pod 标签信息 | `kubectl get pod rc-volume-missing-secret -n aiops-e2e -o wide` | `app=rc-volume-missing-secret,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true` | 明确标记为 VolumeMountFailed |
| 5 | 事件重复记录 | `kubectl get events -n aiops-e2e` | `Warning FailedMount (x16 over 17m): MountVolume.SetUp failed for volume "missing-secret"` | 事件多次重复，确认问题持续 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 处于 ContainerCreating 状态，Events 显示卷挂载失败，直接指向 Secret 缺失。
- **证据 #3 印证**：直接验证 Secret 是否存在，结果为 `NotFound`，确认问题根源。
- **证据 #4 + #5 印证**：标签和事件记录共同确认问题类型为 VolumeMountFailed，且为配置错误。

### 缺失证据（无）

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Secret 'rc-definitely-missing-secret' 不存在，导致卷挂载失败       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod 指定了不存在的 Secret 作为 volume，Kubernetes 无法挂载该卷     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 卷挂载失败，MountVolume.SetUp 报错：secret "rc-definitely-missing-secret" not found │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 ContainerCreating，持续失败，无法正常启动              │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2（MountVolume.SetUp failed）和证据 #3（Secret 不存在），问题的根本原因是**Pod 所引用的 Secret 'rc-definitely-missing-secret' 不存在**，导致卷挂载失败，Pod 无法创建。  
**置信度**：高 (90%)  
- ✅ `kubectl describe pod` 明确指出 Secret 不存在  
- ✅ `kubectl get secret` 验证了 Secret 不存在  
- ✅ 事件重复记录确认了问题持续存在  

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [必须] 创建缺失的 Secret**

```bash
kubectl create secret generic rc-definitely-missing-secret \
  -n aiops-e2e \
  --from-literal=key1=value1 \
  --from-literal=key2=value2
```

*依据*：Secret 缺失是直接原因，必须创建该 Secret 才能完成卷挂载。

**2. [可选] 确认 Pod 是否成功启动**

```bash
kubectl get pod rc-volume-missing-secret -n aiops-e2e
```

*目的*：确认 Pod 是否已成功创建并处于 Running 状态。

### 后续优化

1. **自动化检查**：编写脚本定期检查 Pod 所依赖的 Secret 是否存在，避免类似问题。
2. **文档记录**：记录 Secret 创建逻辑，确保团队成员了解依赖关系。
3. **配置审计**：使用 Helm 或 Kustomize 管理 Secret 和 Pod 配置，确保同步性。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Secret 存在 | `kubectl get secret rc-definitely-missing-secret -n aiops-e2e` | NAME: rc-definitely-missing-secret |
| 2. 确认 Pod 状态 | `kubectl get pod rc-volume-missing-secret -n aiops-e2e` | STATUS: Running |
| 3. 检查 Pod 事件 | `kubectl describe pod rc-volume-missing-secret -n aiops-e2e` | 无 FailedMount 事件 |

---

## ⚠️ 注意事项

- 如果 Secret 的值敏感，请使用加密方式创建（如使用 `--from-file` 和加密文件）。
- 如果该 Secret 是由其他组件（如 CI/CD）自动创建的，请检查其流程是否正常。
- 避免手动删除 Secret，应通过配置管理工具统一处理。

---

## 📊 性能统计

├─ 总耗时: 4.4m
├─ 问题定位: 43.5s (16%) ✅
├─ 证据链采集: 44.7s (17%) ✅
├─ 根因分析: 91.1s (34%) ✅
├─ 汇总总结: 86.2s (32%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 6 次
```

📋 诊断追踪

- **核心 Runbook**: pod-volume-mount-failed
- **参考 Runbook**: pod-volume-mount-failed
- **工具调用**: 6 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
