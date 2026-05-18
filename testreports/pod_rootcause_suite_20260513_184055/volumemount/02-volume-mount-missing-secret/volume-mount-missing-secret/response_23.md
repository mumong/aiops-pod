======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 27d6c9e0509d4707]

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
  Warning  FailedMount  14m (x23 over 44m)    kubelet            MountVolume.SetUp
   💭 [问题定位] {
  "layer": "L3",
  "derived_layer": "L3",
  "layers": [
    "L3"
  ],
  "layer_name": "ImagePullFailed / VolumeMountFailed / SandboxCreateFailed",
  "confidence": 0.95,
  "reasoning": "异常 Pod 'rc-volume-missing-secret' 当前状态为 Pending，且事件显示 MountVolume.SetUp failed，明确指向 VolumeMountFailed 异常类型。根据 runbook，该异常通常归类为 L3，涉及存储卷挂载失败、Secret/ConfigMap 缺失等问题。证据显示 'secret \"rc-definitely-missing-secret\" not found'，符合 VolumeMountFailed 的典型原因，因此判定为 L3。",
  "abnormal_pods": [
    {
      "name": "rc-volume-missing-secret",
      "namespace": "aiops-e2e",
      "status": "Pending",
      "reason": "ContainerCreating",
      "key_events": [
        "MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found",
        "Unable to attach or mount volumes: unmounted volumes=[missing-secret], unattached volumes=[kube-api-access-8jtht missing-secret]: timed out waiting for the condition"
      ]
    }
  ],
  "abnormal_groups": [
    {
      "type": "VolumeMountFailed",
      "count": 1,
      "pods": [
        "rc-volume-missing-secret"
      ]
    }
  ],
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "VolumeMountFailed",
  "status_category": "VolumeMountFailed",
  "key_entities": [
    "rc-volume-missing-secret",
    "missing-secret",
    "rc-definitely-missing-secret",
    "secret"
  ],
  "possible_scenarios": [
    "Secret \"rc-definitely-missing-secret\" 缺失导致卷挂载失败",
    "PVC/PV 配置不正确，无法绑定到 Pod",
    "节点 node1 上的卷挂载配置错误",
    "CSI/NFS 服务不可用或权限不足"
  ]
}
   ✅ [问题定位] 完成 (40.6s)
   📤 → 下游数据: layer=Layer.L3, layers=L3
   scenarios=[]
   entities=[]
   reasoning=当前环境中存在异常 Pod 'rc-volume-missing-secret'，其状态为 Pending，且事件显示 MountVolume.SetUp failed，明确指向 VolumeMountFailed 异常类型。根据 runbook，该异常通常归类为 L3，涉及存储卷挂载失败、Secret/ConfigMap 缺失等问题。证据显示 'secret "rc-definitely-missing-secret" not found'，符合 VolumeMountFailed 的典型原因，因此判定为 L3。
   layer_analysis={"layer": "L3", "derived_layer": "", "layers": [], "layer_name": "", "confidence": 0.5, "reasoning": "当前环境中存在异常 Pod 'rc-volume-missing-secret'，其状态为 Pending，且事件显示 MountVolume.SetUp failed，明确指向 VolumeMountFailed 异常类型。根据 runbook，该异常通常归类为 L3，涉及存储卷挂载失败、Secret/ConfigMap 缺失等问题。证据显示 'secret \"rc-definitely-missing-secret\" not found'，符合 VolumeMountFailed 的典型原因，因此判定为 L3。", "abnormal_pods": [{"name": "rc-volume-missing-secret", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "VolumeMountFailed", "status_category": "VolumeMountFailed", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-secret"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-secret"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-volume-missing-secret                            0/1     ContainerCreating   0                44m     <none>           node1    <none>           <none>            app=rc-volume-missing-secret,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/27d6c9e0509d4707/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/27d6c9e0509d4707/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/27d6c9e0509d4707/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L3
   置信度: 50%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
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
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=187 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide secret rc-definitely-missing-secret -n aiops-e2e
Error from server (NotFound): secrets "rc-de
   💭 [证据链采集] 已采集证据：
1. `kubectl_get_yaml` 确认 Pod `rc-volume-missing-secret` 中定义了名为 `missing-secret` 的卷，且其引用的 Secret 为 `null`。
2. `kubectl_get_by_name` 尝试获取 Secret `rc-definitely-missing-secret` 时失败，返回 `Error from server (NotFound): secrets "rc-definitely-missing-secret" not found`，证实 Secret 缺失。

结论：当前异常 Pod `rc-volume-missing-secret` 的卷挂载失败是由于引用的 Secret `rc-definitely-missing-secret` 不存在。该问题符合 `VolumeMountFailed` 异常类型，归类为 L3。建议创建缺失的 Secret 以解决问题。
   ✅ [证据链采集] 完成 (1m 1.4s)
   📤 → 下游数据: evidence_items=4/4
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod rc-volume-missing-secret 的详细信息以确认其 VolumeMountFailed 的具体原因","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-missing-secret -n aiops-e2e -o yaml","tool_args":{"namespace":"aiops-e2e","name":"rc-volume-missing-secret","kind":"Pod"},"purpose":"确认 Pod 中 volume 类型及引用的 Secret 是否缺失","evidence_type":"current_state","target_scope":"aiops-e2e/rc-volume-missing-secret","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e2","description":"获取 Secret rc-definitely-missing-secret 是否存在","level":"important","tool":"kubectl_get_by_name","command":"kubectl get secret rc-definitely-missing-secret -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-definitely-missing-secret","kind":"Secret"},"purpose":"确认 Secret 是否缺失，以验证 FailedMount 事件的根源","evidence_type":"dependency_check","target_scope":"aiops-e2e/rc-definitely-missing-secret","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-missing-secret\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-13T12:34:17Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-missing-secret, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"missing-secret\", \"secret\": null}\n- {\"name\": \"kube-api-access-8jtht\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/27d6c9e0509d4707/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/27d6c9e0509d4707/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/27d6c9e0509d4707/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=187 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide secret rc-definitely-missing-secret -n aiops-e2e\nError from server (NotFound): secrets \"rc-definitely-missing-secret\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/27d6c9e0509d4707/tools/002-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/27d6c9e0509d4707/tools/002-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/27d6c9e0509d4707/tools/002-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集证据：\n1. `kubectl_get_yaml` 确认 Pod `rc-volume-missing-secret` 中定义了名为 `missing-secret` 的卷，且其引用的 Secret 为 `null`。\n2. `kubectl_get_by_name` 尝试获取 Secret `rc-definitely-missing-secret` 时失败，返回 `Error from server (NotFound): secrets \"rc-definitely-missing-secret\" not found`，证实 Secret 缺失。\n\n结论：当前异常 Pod `rc-volume-missing-secret` 的卷挂载失败是由于引用的 Secret `rc-definitely-missing-secret` 不存在。该问题符合 `VolumeMountFailed` 异常类型，归类为 L3。建议创建缺失的 Secret 以解决问题。","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 4/4 项，完整度 100%；实际执行工具 4 个，匹配计划 2 个，未规划证据 2 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":4,"environment_evidence_collected":4,"environment_evidence_completeness":1.0,"executed_tool_count":4,"matched_tool_count":2,"unplanned_tool_count":2,"evidence_inventory":[{"id":"e1","description":"获取 Pod rc-volume-missing-secret 的详细信息以确认其 VolumeMountFailed 的具体原因","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-missing-secret -n aiops-e2e -o yaml","purpose":"确认 Pod 中 volume 类型及引用的 Secret 是否缺失","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Secret rc-definitely-missing-secret 是否存在","level":"important","tool":"kubectl_get_by_name","command":"kubectl get secret rc-definitely-missing-secret -n aiops-e2e","purpose":"确认 Secret 是否缺失，以验证 FailedMount 事件的根源","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 获取 Pod rc-volume-missing-secret 的详细信息以确认其 Vol... | `kubectl get pod rc-volume-missing-secret -n aiops-e2e -o yaml` |
   | e2 | important | ✅ | kubectl_get_by_name | 获取 Secret rc-definitely-missing-secret 是否存在 | `kubectl get secret rc-definitely-missing-secret -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (31.2s)
   📤 → 下游数据: root_cause=Pod 'rc-volume-missing-secret' 处于 ContainerCreating 状态是由于其引用的 Secret 'rc-definitely-missing-secret' 不存在，导致卷 'missing-secret' 无法挂载。
   confidence=90%
   causal_chain={"root_cause": "Secret rc-definitely-missing-secret 不存在", "direct_consequence": "卷 missing-secret 无法挂载", "intermediate_consequence": "Pod rc-volume-missing-secret 无法完成容器创建", "final_consequence": "Pod rc-volume-missing-secret 处于 ContainerCreating 状态"}
   rca_analysis={"phenomenon": "Pod 'rc-volume-missing-secret' 处于 ContainerCreating 状态，且挂载卷失败，导致其无法正常运行。", "evidence_inventory": [{"tool": "kubectl_get_yaml", "description": "Pod rc-volume-missing-secret 定义了名为 missing-secret 的卷，但引用的 Secret 为 null"}, {"tool": "kubectl_get_by_name", "description": "Secret rc-definitely-missing-secret 不存在，导致卷挂载失败"}], "evidence_analysis": [{"tool": "kubectl_get_yaml", "analysis": "Pod rc-volume-missing-secret 中定义了一个名为 missing-secret 的卷，但该卷引用的 Secret 为 null，表明该 Secret 未被正确配置。"}, {"tool": "kubectl_get_by_name", "analysis": "尝试获取 rc-definitely-missing-secret 时返回 'secrets \"rc-definitely-missing-secret\" not found'，证实该 Secret 不存在。"}], "causal_chain": {"root_cause": "Secret rc-definitely-missing-secret 不存在", "direct_consequence": "卷 missing-secret 无法挂载", "intermediate_consequence": "Pod rc-volume-missing-secret 无法完成容器创建", "final_consequence": "Pod rc-volume-missing-secret 处于 ContainerCreating 状态"}, "root_cause": "Pod 'rc-volume-missing-secret' 处于 ContainerCreating 状态是由于其引用的 Secret 'rc-definitely-missing-secret' 不存在，导致卷 'missing-secret' 无法挂载。", "root_cause_summary": "Pod 'rc-volume-missing-secret' 处于 ContainerCreating 状态是由于其引用的 Secret 'rc-definitely-missing-secret' 不存在，导致卷 'missing-secret' 无法挂载。", "confidence": 0.9, "confidence_reason": "有直接证据表明 Secret 不存在，且与 Pod 挂载失败直接相关。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [], "limitations": "无", "llm_raw_analysis": "已采集证据：\n1. `kubectl_get_yaml` 确认 Pod `rc-volume-missing-secret` 中定义了名为 `missing-secret` 的卷，且其引用的 Secret 为 `null`。\n2. `kubectl_get_by_name` 尝试获取 Secret `rc-definitely-missing-secret` 时失败，返回 `Error from server (NotFound): secrets \"rc-definitely-missing-secret\" not found`，证实 Secret 缺失。\n\n结论：当前异常 Pod `rc-volume-missing-secret` 的卷挂载失败是由于引用的 Secret `rc-definitely-missing-secret` 不存在。该问题符合 `VolumeMountFailed` 异常类型，归类为 L3。建议创建缺失的 Secret 以解决问题。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod 'rc-volume-missing-secret' 处于 ContainerCreating 状态是由于其引用的 Secret 'rc-definitely-missing-secret' 不存在，导致卷 'missing-secret' 无法挂载。
   置信度: 90%
   🔗 因果链:
     根本原因: Secret rc-definitely-missing-secret 不存在


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 47.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3924 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 0.4s
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
| **Pod异常状态** | ContainerCreating / VolumeMountFailed |
| **兼容归因层** | L3 - 存储卷挂载失败 |
| **问题分类** | VolumeMountFailed（Secret 不存在） |
| **置信度** | 高 (90%) |
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
| 1 | Pod 状态 | kubectl get pod | `STATUS: ContainerCreating` | Pod 无法创建，因卷挂载失败 |
| 2 | Pod 事件 | kubectl describe pod | `MountVolume.SetUp failed for volume "missing-secret": secret "rc-definitely-missing-secret" not found` | 明确指出 Secret 不存在 |
| 3 | Secret 存在性验证 | kubectl get secret | `Error from server (NotFound): secrets "rc-definitely-missing-secret" not found` | 确认 Secret 缺失 |
| 4 | Pod YAML 信息 | kubectl get pod -o yaml | `Volumes: missing-secret` | Pod 引用了不存在的 Secret |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 状态为 `ContainerCreating`，且事件提示 `MountVolume.SetUp failed`，说明容器无法启动，因卷挂载失败。
- **证据 #2 + #3 印证**：事件中明确指出引用的 Secret 不存在，而 `kubectl get secret` 验证结果一致，确认是 Secret 缺失问题。
- **因果链**：Secret 缺失 → 卷挂载失败 → Pod 无法创建 → 状态为 `ContainerCreating`

### 缺失证据（无）

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Secret 'rc-definitely-missing-secret' 不存在，导致卷 'missing-secret' 无法挂载 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod rc-volume-missing-secret 引用了该 Secret，但未创建           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ MountVolume.SetUp failed for volume "missing-secret"            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 ContainerCreating，事件提示 Secret 不存在            │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (MountVolume.SetUp failed) 和证据 #3 (Secret 不存在)，问题的根本原因是**Pod `rc-volume-missing-secret` 引用了不存在的 Secret `rc-definitely-missing-secret`**，导致卷 `missing-secret` 无法挂载，Pod 无法创建。
**置信度**：高 (90%)
- ✅ `MountVolume.SetUp failed` 事件明确指向卷挂载失败
- ✅ `kubectl get secret` 验证 Secret 不存在
- ✅ Pod YAML 明确引用了该 Secret

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 创建缺失的 Secret**
```bash
kubectl create secret generic rc-definitely-missing-secret -n aiops-e2e --from-literal=key1=value1
```
*依据*：Secret 缺失是当前问题的根本原因，创建后可恢复卷挂载流程

**2. [可选] 强制重启 Pod**
```bash
kubectl delete pod rc-volume-missing-secret -n aiops-e2e
```
*目的*：Secret 创建后，删除 Pod 以触发重新创建流程

### 后续优化
1. **配置 Secret 自动同步**：如果该 Secret 是由其他系统生成（如 CI/CD、Config Management），确保流程中包含 Secret 创建步骤
2. **资源模板校验**：在部署前校验引用的 Secret 是否存在，避免部署失败
3. **监控 Secret 存在性**：通过监控工具（如 Prometheus + kube-state-metrics）监控 Secret 存在性

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Secret 存在 | `kubectl get secret rc-definitely-missing-secret -n aiops-e2e` | 输出 Secret 详情 |
| 2. 确认 Pod 状态 | `kubectl get pod rc-volume-missing-secret -n aiops-e2e` | STATUS: Running |
| 3. 确认卷挂载正常 | `kubectl describe pod rc-volume-missing-secret -n aiops-e2e` | 无 `FailedMount` 事件 |

---
## ⚠️ 注意事项
- 如果 Secret 是由其他服务生成的（如 Helm Chart、Argo CD、GitOps 工具），请检查其部署流程是否成功
- 确保在部署 Pod 之前，所有依赖的 Secret、ConfigMap 等资源都已创建
- 本问题属于 L3 问题，涉及存储卷挂载，建议关注部署流程中的资源依赖检查

---

## 📊 性能统计

├─ 总耗时: 4.0m
├─ 问题定位: 40.6s (17%) ✅
├─ 证据链采集: 61.4s (26%) ✅
├─ 根因分析: 31.2s (13%) ✅
├─ 汇总总结: 107.3s (45%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 5 次
```

📋 诊断追踪

- **核心 Runbook**: pod-volume-mount-failed
- **参考 Runbook**: pod-volume-mount-failed
- **工具调用**: 5 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
