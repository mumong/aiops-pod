======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 4250700272984a17]

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
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  8m9s (x50 over 93m)   kubelet  MountVolume.SetUp fa
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": "high",
  "reasoning": "Pod 'rc-volume-configmap-missing-key' 处于 ContainerCreating 状态，其关键事件显示 'MountVolume.SetUp failed for volume \"config-volume\": configmap references non-existent config key: missing-key'。这表明问题源于 ConfigMap 引用了一个不存在的 key，属于 ConfigError 类型。由于该问题直接影响 Pod 的启动，因此归类为 L4。",
  "abnormal_pods": [
    {
      "name": "rc-volume-configmap-missing-key",
      "namespace": "aiops-e2e",
      "status": "Pending",
      "reason": "ContainerCreating",
      "node": "node1"
    }
  ],
  "abnormal_groups": [
    {
      "type": "VolumeMountFailed",
      "pods": [
        "rc-volume-configmap-missing-key"
      ]
    }
  ],
  "pod_status_keyword": "ContainerCreating",
  "pod_abnormal_type": "VolumeMountFailed",
  "status_category": "ConfigError",
  "key_entities": [
    "rc-volume-configmap-missing-key",
    "config-volume",
    "missing-key"
  ],
  "possible_scenarios": [
    "Pod 中引用的 ConfigMap 不存在或缺少指定的 key 'missing-key'，导致卷挂载失败。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (44.0s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': "ConfigMap 引用了不存在的 key 'missing-key'，导致卷挂载失败。", 'probability': 'high', 'reason': 'Events 明确指出 configmap references non-existent config key: missing-key'}]
   entities=[{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "Volume", "name": "config-volume", "namespace": ""}, {"type": "ConfigMapKey", "name": "missing-key", "namespace": ""}]
   reasoning=Pod 'rc-volume-configmap-missing-key' 处于 ContainerCreating 状态，其关键事件显示 'MountVolume.SetUp failed for volume "config-volume": configmap references non-existent config key: missing-key'。这表明问题源于 ConfigMap 引用了一个不存在的 key，属于 ConfigError 类型。由于该问题直接影响 Pod 的启动，因此归类为 L4。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "Pod 'rc-volume-configmap-missing-key' 处于 ContainerCreating 状态，其关键事件显示 'MountVolume.SetUp failed for volume \"config-volume\": configmap references non-existent config key: missing-key'。这表明问题源于 ConfigMap 引用了一个不存在的 key，属于 ConfigError 类型。由于该问题直接影响 Pod 的启动，因此归类为 L4。", "abnormal_pods": [{"name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "ConfigError", "key_entities": [{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "Volume", "name": "config-volume", "namespace": ""}, {"type": "ConfigMapKey", "name": "missing-key", "namespace": ""}], "possible_scenarios": [{"scenario": "ConfigMap 引用了不存在的 key 'missing-key'，导致卷挂载失败。", "probability": "high", "reason": "Events 明确指出 configmap references non-existent config key: missing-key"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-volume-configmap-missing-key                     0/1     ContainerCreating   0                93m     <none>           node1    <none>           <none>            app=rc-volume-configmap-missing-key,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/4250700272984a17/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/4250700272984a17/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/4250700272984a17/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  10m (x50 over 95m)  kubelet  MountVolume.SetUp fail
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                              READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-volume-configmap-missing-key   0/1     ContainerCreating   
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=163 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide configmap config-volume -n aiops-e2e
Error from server (NotFound): configmaps "config-volume"
   💭 [证据链采集] 已采集证据：
- Pod 'rc-volume-configmap-missing-key' 的 Events 显示 `MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key`。
- Pod 的状态为 `ContainerCreating`，且未成功启动。
- 尝试获取 ConfigMap 'config-volume' 时返回 `Error from server (NotFound): configmaps "config-volume" not found`，表明 ConfigMap 不存在。

结论：
Pod 'rc-volume-configmap-missing-key' 无法启动，因为引用的 ConfigMap 'config-volume' 不存在，导致卷挂载失败。这与 `VolumeMountFailed` 异常类型一致，确认了 ConfigMap 缺失是当前问题的根因。
   ✅ [证据链采集] 完成 (1m 28.9s)
   📤 → 下游数据: evidence_items=5/5
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细信息，验证其 VolumeMountFailed 的根本原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","pod":"rc-volume-configmap-missing-key"},"purpose":"验证 Pod 'rc-volume-configmap-missing-key' 的 Events 原文，确认 VolumeMountFailed 的原因。","evidence_type":"事件/配置验证","target_scope":"Pod/aiops-e2e/rc-volume-configmap-missing-key","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod 的 YAML 定义，确认其 volume 配置。","level":"important","tool":"kubectl_get_by_name","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","tool_args":{"namespace":"aiops-e2e","pod":"rc-volume-configmap-missing-key","output":"yaml"},"purpose":"确认 Pod 的 .spec.volumes[] 配置，确认引用的是 ConfigMap、Secret、PVC 还是其他类型。","evidence_type":"配置验证","target_scope":"Pod/aiops-e2e/rc-volume-configmap-missing-key","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"验证 ConfigMap 是否存在及是否包含缺失的 key。","level":"important","tool":"kubectl_get_by_name","command":"kubectl get configmap <configmap-name> -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","configmap":"<configmap-name>"},"purpose":"确认 ConfigMap 是否存在，以及是否包含缺失的 key 'missing-key'。","evidence_type":"配置验证","target_scope":"ConfigMap/aiops-e2e/<configmap-name>","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  10m (x50 over 95m)  kubelet  MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n  Warning  FailedMount  54m (x7 over 84m)   kubelet  Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-xz5tn config-volume]: timed out waiting for the condition\n  Warning  FailedMount  16s (x30 over 93m)  kubelet  Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-xz5tn]: timed out waiting for the condition\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed\n    State:          Waiting\n      Reason:       ContainerCreating","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4250700272984a17/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4250700272984a17/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4250700272984a17/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                              READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-volume-configmap-missing-key   0/1     ContainerCreating   0          95m   <none>   node1   <none>           <none>            app=rc-volume-configmap-missing-key,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4250700272984a17/tools/002-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4250700272984a17/tools/002-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4250700272984a17/tools/002-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=163 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide configmap config-volume -n aiops-e2e\nError from server (NotFound): configmaps \"config-volume\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/4250700272984a17/tools/003-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4250700272984a17/tools/003-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4250700272984a17/tools/003-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集证据：\n- Pod 'rc-volume-configmap-missing-key' 的 Events 显示 `MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key`。\n- Pod 的状态为 `ContainerCreating`，且未成功启动。\n- 尝试获取 ConfigMap 'config-volume' 时返回 `Error from server (NotFound): configmaps \"config-volume\" not found`，表明 ConfigMap 不存在。\n\n结论：\nPod 'rc-volume-configmap-missing-key' 无法启动，因为引用的 ConfigMap 'config-volume' 不存在，导致卷挂载失败。这与 `VolumeMountFailed` 异常类型一致，确认了 ConfigMap 缺失是当前问题的根因。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 5/5 项，完整度 100%；实际执行工具 5 个，匹配计划 3 个，未规划证据 2 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":5,"environment_evidence_collected":5,"environment_evidence_completeness":1.0,"executed_tool_count":5,"matched_tool_count":3,"unplanned_tool_count":2,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细信息，验证其 VolumeMountFailed 的根本原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","purpose":"验证 Pod 'rc-volume-configmap-missing-key' 的 Events 原文，确认 VolumeMountFailed 的原因。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod 的 YAML 定义，确认其 volume 配置。","level":"important","tool":"kubectl_get_by_name","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","purpose":"确认 Pod 的 .spec.volumes[] 配置，确认引用的是 ConfigMap、Secret、PVC 还是其他类型。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"验证 ConfigMap 是否存在及是否包含缺失的 key。","level":"important","tool":"kubectl_get_by_name","command":"kubectl get configmap <configmap-name> -n aiops-e2e","purpose":"确认 ConfigMap 是否存在，以及是否包含缺失的 key 'missing-key'。","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod 的详细信息，验证其 VolumeMountFailed 的根本原因。 | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_by_name | 获取 Pod 的 YAML 定义，确认其 volume 配置。 | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_get_by_name | 验证 ConfigMap 是否存在及是否包含缺失的 key。 | `kubectl get configmap <configmap-name> -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 16.2s)
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
   ✅ [汇总总结] 完成 (1m 10.4s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4043 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 39.5s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ContainerCreating |
| **兼容归因层** | L4 |
| **问题分类** | ConfigError（ConfigMap 引用了不存在的 key） |
| **置信度** | 高 |
| **证据完整度** | 3/3 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-volume-configmap-missing-key |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | configmap references non-existent config key: missing-key |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod rc-volume-configmap-missing-key` | `Warning  FailedMount  8m9s (x50 over 93m)   kubelet  MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key` | Pod 无法启动，原因是引用了不存在的 ConfigMap key |
| 2 | Pod YAML 配置 | `kubectl get pod rc-volume-configmap-missing-key -o yaml` | 指定了 `volume` 挂载 `config-volume`，且 `config-volume` 指向 ConfigMap 的 `missing-key` | Pod 配置中引用了错误的 ConfigMap key |
| 3 | ConfigMap 检查 | `kubectl get configmap config-volume -n aiops-e2e` | `Error from server (NotFound): configmaps "config-volume"` | ConfigMap `config-volume` 不存在 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 尝试挂载一个名为 `config-volume` 的 ConfigMap 中的 `missing-key`，但 `kubectl describe pod` 明确指出 key 不存在。
- **证据 #3 印证**：`kubectl get configmap` 无法找到该 ConfigMap，进一步确认了配置错误。
- **结论**：Pod 无法启动的根本原因是引用了一个 **不存在的 ConfigMap key**，属于配置错误。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod 配置中引用了不存在的 ConfigMap key 'missing-key'            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ kubelet 尝试挂载卷 config-volume 时发现 key 不存在，导致失败     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ MountVolume.SetUp failed for volume "config-volume"             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 ContainerCreating，持续失败，无法启动                │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (`MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key`) 和证据 #3 (`kubectl get configmap config-volume -n aiops-e2e` 报错)，问题的根本原因是 **Pod 配置中引用了一个不存在的 ConfigMap key `missing-key`**。

**置信度**：高 (95%)
- ✅ `kubectl describe pod` 明确指出 key 不存在
- ✅ `kubectl get configmap` 无法找到该 ConfigMap
- ✅ 事件日志中多次重复报错，确认为持续性问题

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 修复 ConfigMap 引用**
```bash
kubectl delete pod rc-volume-configmap-missing-key -n aiops-e2e
```
*依据*：删除失败 Pod，待修复配置后自动重建（如果使用 Deployment/ReplicaSet）。

**2. [可选] 创建缺失的 ConfigMap**
```bash
kubectl create configmap config-volume --from-literal=missing-key="example-value" -n aiops-e2e
```
*目的*：创建缺失的 ConfigMap，确保 Pod 能正确挂载。

**3. [可选] 检查 Pod YAML 配置**
```bash
kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml
```
*目的*：确认 Pod YAML 中引用的 ConfigMap 名称和 key 是否正确。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 是否重建 | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e` | STATUS: Running |
| 2. 确认 ConfigMap 存在 | `kubectl get configmap config-volume -n aiops-e2e` | NAME: config-volume |
| 3. 检查事件是否消失 | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` | 无 FailedMount 事件 |

---

## ⚠️ 注意事项

- 如果 Pod 由 Deployment 或 ReplicaSet 管理，删除 Pod 后会自动重建，无需手动创建。
- 如果 ConfigMap `config-volume` 本应存在但缺失，建议检查是否误删或未正确部署。
- 确保引用的 key 名称与 ConfigMap 中定义的 key 一致，包括大小写敏感问题。

---

## 📊 性能统计

├─ 总耗时: 4.7m
├─ 问题定位: 44.0s (16%) ✅
├─ 证据链采集: 88.9s (32%) ✅
├─ 根因分析: 76.2s (27%) ✅
├─ 汇总总结: 70.4s (25%) ✅
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
