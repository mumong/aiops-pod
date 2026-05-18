======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 4c2a2b1622dc4a19]

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
name: rc-volume-missing-secret
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  19s (x40 over 65m)   kubelet  MountVolume.SetUp failed for
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-volume-missing-secret
namespace: aiops-e2e
creationTimestamp: 2026-05-13T12:34:17Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: 
   💭 [问题定位] {
  "layer": "L3",
  "derived_layer": "L3",
  "layers": [
    "L3"
  ],
  "layer_name": "VolumeMountFailed",
  "confidence": "high",
  "reasoning": "Pod 'rc-volume-missing-secret' 在状态 'Pending' 且事件显示 'MountVolume.SetUp failed for volume 'missing-secret' : secret 'rc-definitely-missing-secret' not found'，符合 VolumeMountFailed 类型。此类型归类为 L3 层次，因为属于卷挂载失败，涉及 StorageClass/PV/NFS/CSI 等存储相关组件的问题。",
  "abnormal_pods": [
    {
      "name": "rc-volume-missing-secret",
      "namespace": "aiops-e2e",
      "status": "Pending",
      "reason": "ContainerCreating",
      "pod_abnormal_type": "VolumeMountFailed"
    }
  ],
  "abnormal_groups": [
    "VolumeMountFailed"
  ],
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "VolumeMountFailed",
  "status_category": "storage_volume",
  "key_entities": [
    "Pod: rc-volume-missing-secret",
    "Volume: missing-secret",
    "Secret: rc-definitely-missing-secret"
  ],
  "possible_scenarios": [
    "Secret 'rc-definitely-missing-secret' 不存在或未正确配置",
    "卷 'missing-secret' 引用了缺失的 Secret",
    "Pod spec 中的卷配置错误，导致挂载失败"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 1.3s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[{'scenario': "Secret 'rc-definitely-missing-secret' 不存在或未正确配置", 'probability': 'high', 'reason': "事件原文显示 'secret 'rc-definitely-missing-secret' not found'"}, {'scenario': "卷 'missing-secret' 引用了缺失的 Secret", 'probability': 'high', 'reason': 'Pod spec 中的卷配置错误，导致挂载失败'}, {'scenario': 'Pod spec 中的卷配置错误，导致挂载失败', 'probability': 'high', 'reason': "Pod spec 显示 'secret': null，说明引用对象缺失"}]
   entities=[{"type": "Pod", "name": "rc-volume-missing-secret", "namespace": "aiops-e2e"}, {"type": "Volume", "name": "missing-secret", "namespace": ""}, {"type": "Secret", "name": "rc-definitely-missing-secret", "namespace": ""}]
   reasoning=当前环境中存在一个异常 Pod 'rc-volume-missing-secret'，状态为 Pending，且其事件中明确提到 'MountVolume.SetUp failed for volume 'missing-secret' : secret 'rc-definitely-missing-secret' not found'。此错误属于 VolumeMountFailed 类型，归因于存储组件（secret 类型卷）缺失，符合 L3 层次。由于当前仍存在异常 Pod，因此判定为 L3 层次。
   layer_analysis={"layer": "L3", "derived_layer": "L3", "layers": ["L3"], "layer_name": "VolumeMountFailed", "confidence": 0.95, "reasoning": "当前环境中存在一个异常 Pod 'rc-volume-missing-secret'，状态为 Pending，且其事件中明确提到 'MountVolume.SetUp failed for volume 'missing-secret' : secret 'rc-definitely-missing-secret' not found'。此错误属于 VolumeMountFailed 类型，归因于存储组件（secret 类型卷）缺失，符合 L3 层次。由于当前仍存在异常 Pod，因此判定为 L3 层次。", "abnormal_pods": [{"name": "rc-volume-missing-secret", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "Pod", "name": "rc-volume-missing-secret", "namespace": "aiops-e2e"}, {"type": "Volume", "name": "missing-secret", "namespace": ""}, {"type": "Secret", "name": "rc-definitely-missing-secret", "namespace": ""}], "possible_scenarios": [{"scenario": "Secret 'rc-definitely-missing-secret' 不存在或未正确配置", "probability": "high", "reason": "事件原文显示 'secret 'rc-definitely-missing-secret' not found'"}, {"scenario": "卷 'missing-secret' 引用了缺失的 Secret", "probability": "high", "reason": "Pod spec 中的卷配置错误，导致挂载失败"}, {"scenario": "Pod spec 中的卷配置错误，导致挂载失败", "probability": "high", "reason": "Pod spec 显示 'secret': null，说明引用对象缺失"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-secret"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-secret"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-volume-missing-secret                            0/1     ContainerCreating   0                65m     <none>           node1    <none>           <none>            app=rc-volume-missing-secret,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/4c2a2b1622dc4a19/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/4c2a2b1622dc4a19/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/4c2a2b1622dc4a19/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L3
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=187 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide secret rc-definitely-missing-secret -n aiops-e2e
Error from server (NotFound): secrets "rc-de
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-volume-missing-secret
namespace: aiops-e2e
creationTimestamp: 2026-05-13T12:34:17Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: 
   💭 [证据链采集] 已采集证据：
- e1: Secret 'rc-definitely-missing-secret' 在命名空间 'aiops-e2e' 中确实缺失（NotFound），这是导致卷 'missing-secret' 挂载失败的直接原因。
- e2: Pod 'rc-volume-missing-secret' 的 spec 中确实引用了名为 'missing-secret' 的卷，但该卷的 `secret` 字段为 `null`，表明它引用了不存在的 Secret。

未采集证据：
- 无

冲突证据：
- 无

结论：当前 Pod 异常状态 'ContainerCreating' 是由卷 'missing-secret' 引用的 Secret 'rc-definitely-missing-secret' 缺失直接导致的。这与 Runbook 'pod-volume-mount-failed.md' 中描述的典型原因一致。建议创建缺失的 Secret 或修正 Pod 的卷配置。
   ✅ [证据链采集] 完成 (1m 0.3s)
   📤 → 下游数据: evidence_items=5/5
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Secret 'rc-definitely-missing-secret' 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-definitely-missing-secret -n aiops-e2e","tool_args":{"name":"rc-definitely-missing-secret","kind":"Secret","namespace":"aiops-e2e"},"purpose":"确认 Secret 是否缺失，这是导致卷挂载失败的主要原因","evidence_type":"negative","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"验证 Pod 'rc-volume-missing-secret' 的卷配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-missing-secret -n aiops-e2e -o yaml","tool_args":{"name":"rc-volume-missing-secret","kind":"Pod","namespace":"aiops-e2e"},"purpose":"确认 Pod spec 中的 volume 引用是否正确","evidence_type":"configuration","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=187 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide secret rc-definitely-missing-secret -n aiops-e2e\nError from server (NotFound): secrets \"rc-definitely-missing-secret\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/4c2a2b1622dc4a19/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4c2a2b1622dc4a19/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4c2a2b1622dc4a19/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-missing-secret\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T12:34:17Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-missing-secret, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"missing-secret\", \"secret\": null}\n- {\"name\": \"kube-api-access-8jtht\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4c2a2b1622dc4a19/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4c2a2b1622dc4a19/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4c2a2b1622dc4a19/tools/002-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"已采集证据：\n- e1: Secret 'rc-definitely-missing-secret' 在命名空间 'aiops-e2e' 中确实缺失（NotFound），这是导致卷 'missing-secret' 挂载失败的直接原因。\n- e2: Pod 'rc-volume-missing-secret' 的 spec 中确实引用了名为 'missing-secret' 的卷，但该卷的 `secret` 字段为 `null`，表明它引用了不存在的 Secret。\n\n未采集证据：\n- 无\n\n冲突证据：\n- 无\n\n结论：当前 Pod 异常状态 'ContainerCreating' 是由卷 'missing-secret' 引用的 Secret 'rc-definitely-missing-secret' 缺失直接导致的。这与 Runbook 'pod-volume-mount-failed.md' 中描述的典型原因一致。建议创建缺失的 Secret 或修正 Pod 的卷配置。","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 5/5 项，完整度 100%；实际执行工具 5 个，匹配计划 2 个，未规划证据 3 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":5,"environment_evidence_collected":5,"environment_evidence_completeness":1.0,"executed_tool_count":5,"matched_tool_count":2,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"验证 Secret 'rc-definitely-missing-secret' 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-definitely-missing-secret -n aiops-e2e","purpose":"确认 Secret 是否缺失，这是导致卷挂载失败的主要原因","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"e2","description":"验证 Pod 'rc-volume-missing-secret' 的卷配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-missing-secret -n aiops-e2e -o yaml","purpose":"确认 Pod spec 中的 volume 引用是否正确","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 验证 Secret 'rc-definitely-missing-secret' 是否存在 | `kubectl get secret rc-definitely-missing-secret -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_yaml | 验证 Pod 'rc-volume-missing-secret' 的卷配置 | `kubectl get pod rc-volume-missing-secret -n aiops-e2e -o yaml` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (21.0s)
   📤 → 下游数据: root_cause=[L3层] 当前无法基于 LLM 输出确定根本原因
   confidence=10%
   causal_chain={"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}
   rca_analysis={"phenomenon": "我的集群有什么问题", "evidence_analysis": [], "causal_chain": {"trigger": "LLM 未生成可靠因果链", "mechanism": "缺少可用的结构化根因分析结果", "manifestation": "我的集群有什么问题"}, "root_cause": "[L3层] 当前无法基于 LLM 输出确定根本原因", "confidence": 0.1, "confidence_reason": "LLM 返回结果不符合 RCA 结构化输出合同", "alternative_causes": []}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: [L3层] 当前无法基于 LLM 输出确定根本原因
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
   ✅ [汇总总结] 完成 (1m 58.4s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4534 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 21.0s
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
| **兼容归因层** | L3 |
| **问题分类** | VolumeMountFailed |
| **置信度** | 高 |
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
| 错误信息 | `MountVolume.SetUp failed for volume "missing-secret" : secret "rc-definitely-missing-secret" not found` |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: ContainerCreating`, `REASON: VolumeMountFailed` | Pod 因卷挂载失败而处于 ContainerCreating 状态 |
| 2 | Pod 事件 | `kubectl describe pod rc-volume-missing-secret` | `MountVolume.SetUp failed for volume "missing-secret" : secret "rc-definitely-missing-secret" not found` | 事件明确指出 Secret 不存在 |
| 3 | Pod YAML 配置 | `kubectl get pod rc-volume-missing-secret -o yaml` | `volumes` 中引用了名为 `missing-secret` 的 Secret 类型卷 | 说明 Pod 配置中依赖了该 Secret |
| 4 | Secret 是否存在 | `kubectl get secret rc-definitely-missing-secret -n aiops-e2e` | `Error from server (NotFound): secrets "rc-definitely-missing-secret" not found` | 该 Secret 不存在 |
| 5 | Runbook 匹配 | `fetch_runbook` | 匹配 `pod-volume-mount-failed.md` | 确认此为 VolumeMountFailed 类型问题 |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 状态为 ContainerCreating，且事件显示 `secret 'rc-definitely-missing-secret' not found`，确认挂载失败。
- **证据 #3 + #4 印证**：Pod 定义中引用了该 Secret，但实际环境中未找到该 Secret，导致卷挂载失败。
- **因果链完整**：Secret 缺失 → 卷挂载失败 → Pod 无法启动 → 状态为 ContainerCreating。

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | 无 | 证据链完整，无需补充 |

---
## 🎯 根因分析
### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                     │
│ Secret 'rc-definitely-missing-secret' 不存在，导致卷 'missing-secret' 无法挂载 │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                     │
│ Pod rc-volume-missing-secret 定义中引用了该 Secret，但实际环境中不存在          │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                     │
│ MountVolume.SetUp failed for volume "missing-secret" : secret not found        │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                 │
│ Pod 状态为 ContainerCreating，且无法启动                                     │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (`MountVolume.SetUp failed for volume "missing-secret" : secret "rc-definitely-missing-secret" not found`) 和证据 #4 (`kubectl get secret rc-definitely-missing-secret -n aiops-e2e` 报错)，问题的根本原因是 **Secret 'rc-definitely-missing-secret' 不存在**，导致 Pod 无法挂载卷，从而处于 ContainerCreating 状态。

**置信度**：高 (95%)
- ✅ 事件日志明确指出 Secret 不存在
- ✅ `kubectl get secret` 验证确认该 Secret 不存在
- ✅ Pod YAML 中引用了该 Secret

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 创建缺失的 Secret**
```bash
kubectl create secret generic rc-definitely-missing-secret -n aiops-e2e
```
*依据*：Pod 配置引用了此 Secret，但当前环境中不存在。创建后 Pod 应能成功挂载卷。

**2. [可选] 创建 Secret 并添加内容（如需要）**
```bash
kubectl create secret generic rc-definitely-missing-secret -n aiops-e2e \
  --from-literal=key1=value1 \
  --from-literal=key2=value2
```
*依据*：如果该 Secret 需要具体内容（如配置文件、证书等），可按需添加。

### 后续优化
1. **验证修复效果**：
   ```bash
   kubectl get pod rc-volume-missing-secret -n aiops-e2e
   ```
   确认状态为 `Running`。

2. **自动化监控**：配置监控告警，当 Pod 处于异常状态时触发告警。

3. **文档更新**：确保团队了解 Secret 的依赖关系，避免类似问题再次发生。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Secret 存在 | `kubectl get secret rc-definitely-missing-secret -n aiops-e2e` | 显示 Secret 详细信息 |
| 2. 确认 Pod 状态 | `kubectl get pod rc-volume-missing-secret -n aiops-e2e` | STATUS: Running |
| 3. 检查事件 | `kubectl describe pod rc-volume-missing-secret -n aiops-e2e` | 无 FailedMount 类型事件 |

---
## ⚠️ 注意事项
- 如果 Secret 需要特定内容（如证书、配置文件），请确保内容正确无误。
- 请确保创建的 Secret 所在的命名空间与 Pod 的命名空间一致。
- 如果问题仍然存在，请检查 Pod 的卷配置是否正确（例如名称是否匹配、是否在容器中正确挂载）。

---

---

## 📊 性能统计

├─ 总耗时: 4.3m
├─ 问题定位: 61.3s (23%) ✅
├─ 证据链采集: 60.3s (23%) ✅
├─ 根因分析: 21.0s (8%) ✅
├─ 汇总总结: 118.4s (45%) ✅
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
