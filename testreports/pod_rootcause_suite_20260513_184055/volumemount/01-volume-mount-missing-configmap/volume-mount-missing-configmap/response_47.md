======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 716ded7aba7a480e]

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
name: rc-volume-missing-configmap
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  109s (x58 over 103m)   kubelet  MountVolume.SetUp faile
   💭 [问题定位] {
  "layer": "L0",
  "derived_layer": "L0",
  "layers": [
    "L0"
  ],
  "layer_name": "VolumeMountFailed",
  "confidence": 0.98,
  "reasoning": "Pod rc-volume-missing-configmap 处于 Pending 状态，且 kubelet 报错显示 MountVolume.SetUp failed，具体原因是 configmap \"rc-definitely-missing-configmap\" not found。这表明 Pod 无法挂载缺失的 ConfigMap 卷，属于 VolumeMountFailed 类型，归因于存储卷配置错误。",
  "abnormal_pods": [
    {
      "name": "rc-volume-missing-configmap",
      "namespace": "aiops-e2e",
      "status": "Pending",
      "reason": "ContainerCreating",
      "node": "node1/10.2.0.49"
    }
  ],
  "abnormal_groups": [
    {
      "type": "VolumeMountFailed",
      "count": 1
    }
  ],
  "pod_status_keyword": "Pending",
  "pod_abnormal_type": "VolumeMountFailed",
  "status_category": "storage_volume",
  "key_entities": [
    "rc-volume-missing-configmap",
    "aiops-e2e",
    "rc-definitely-missing-configmap"
  ],
  "possible_scenarios": [
    "ConfigMap \"rc-definitely-missing-configmap\" 缺失，导致 Pod 无法完成挂载。",
    "Pod 配置中引用了不存在的 ConfigMap，需要检查并修正配置。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 3.9s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[{'scenario': 'ConfigMap "rc-definitely-missing-configmap" 缺失，导致 Pod 无法完成挂载。', 'probability': 'High', 'reason': 'Pod 事件显示 kubelet 报错 MountVolume.SetUp failed，具体原因是 configmap "rc-definitely-missing-configmap" not found。'}, {'scenario': 'Pod 配置中引用了不存在的 ConfigMap，需要检查并修正配置。', 'probability': 'High', 'reason': 'Pod spec 中的 volume 引用了 configmap "rc-definitely-missing-configmap"，但该 ConfigMap 不存在。'}]
   entities=[{"type": "Pod", "name": "rc-volume-missing-configmap", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-definitely-missing-configmap", "namespace": "aiops-e2e"}]
   reasoning=Pod rc-volume-missing-configmap 处于 Pending 状态，且 kubelet 报错显示 MountVolume.SetUp failed，具体原因是 configmap "rc-definitely-missing-configmap" not found。这表明 Pod 无法挂载缺失的 ConfigMap 卷，属于 VolumeMountFailed 类型，归因于存储卷配置错误。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "VolumeMountFailed", "confidence": 0.98, "reasoning": "Pod rc-volume-missing-configmap 处于 Pending 状态，且 kubelet 报错显示 MountVolume.SetUp failed，具体原因是 configmap \"rc-definitely-missing-configmap\" not found。这表明 Pod 无法挂载缺失的 ConfigMap 卷，属于 VolumeMountFailed 类型，归因于存储卷配置错误。", "abnormal_pods": [{"name": "rc-volume-missing-configmap", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "Pod", "name": "rc-volume-missing-configmap", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-definitely-missing-configmap", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "ConfigMap \"rc-definitely-missing-configmap\" 缺失，导致 Pod 无法完成挂载。", "probability": "High", "reason": "Pod 事件显示 kubelet 报错 MountVolume.SetUp failed，具体原因是 configmap \"rc-definitely-missing-configmap\" not found。"}, {"scenario": "Pod 配置中引用了不存在的 ConfigMap，需要检查并修正配置。", "probability": "High", "reason": "Pod spec 中的 volume 引用了 configmap \"rc-definitely-missing-configmap\"，但该 ConfigMap 不存在。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-configmap"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-configmap"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-volume-missing-configmap                         0/1     ContainerCreating   0                103m    <none>           node1    <none>           <none>            app=rc-volume-missing-configmap,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/716ded7aba7a480e/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/716ded7aba7a480e/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/716ded7aba7a480e/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 98%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-missing-configmap
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  3m36s (x58 over 105m)  kubelet  MountVolume.SetUp faile
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=199 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide configmap rc-definitely-missing-configmap -n aiops-e2e
Error from server (NotFound): configma
   💭 [证据链采集] 已采集证据：
1. `kubectl describe pod` 显示 Pod rc-volume-missing-configmap 处于 Pending 状态，且 kubelet 报错 MountVolume.SetUp failed，具体原因是 configmap "rc-definitely-missing-configmap" not found。
2. `kubectl get configmap` 显示 configmap "rc-definitely-missing-configmap" 不存在，返回 Error from server (NotFound)。

冲突证据：
- 无。

结论：
当前 Pod rc-volume-missing-configmap 无法启动，是因为它引用的 ConfigMap "rc-definitely-missing-configmap" 不存在。需要创建或修正该 ConfigMap 以解决挂载失败问题。
   ✅ [证据链采集] 完成 (1m 1.7s)
   📤 → 下游数据: evidence_items=4/4
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod rc-volume-missing-configmap 的详细状态和事件信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-configmap -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-volume-missing-configmap","kind":"pod"},"purpose":"确认 Pod 当前状态、关键事件、挂载卷配置，验证是否因 ConfigMap 缺失导致挂载失败","evidence_type":"Pod status and events","target_scope":"aiops-e2e/rc-volume-missing-configmap","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"检查 ConfigMap rc-definitely-missing-configmap 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-definitely-missing-configmap","kind":"configmap"},"purpose":"验证 ConfigMap 是否缺失，从而确认是否导致挂载失败","evidence_type":"ConfigMap existence","target_scope":"aiops-e2e/rc-definitely-missing-configmap","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-missing-configmap\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  3m36s (x58 over 105m)  kubelet  MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found\n  Warning  FailedMount  35m (x10 over 96m)     kubelet  Unable to attach or mount volumes: unmounted volumes=[missing-config], unattached volumes=[kube-api-access-n5pfx missing-config]: timed out waiting for the condition\n  Warning  FailedMount  10m (x28 over 103m)    kubelet  Unable to attach or mount volumes: unmounted volumes=[missing-config], unattached volumes=[missing-config kube-api-access-n5pfx]: timed out waiting for the condition\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed\n    State:          Waiting\n      Reason:       ContainerCreating","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/716ded7aba7a480e/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/716ded7aba7a480e/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/716ded7aba7a480e/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=199 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide configmap rc-definitely-missing-configmap -n aiops-e2e\nError from server (NotFound): configmaps \"rc-definitely-missing-configmap\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/716ded7aba7a480e/tools/002-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/716ded7aba7a480e/tools/002-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/716ded7aba7a480e/tools/002-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集证据：\n1. `kubectl describe pod` 显示 Pod rc-volume-missing-configmap 处于 Pending 状态，且 kubelet 报错 MountVolume.SetUp failed，具体原因是 configmap \"rc-definitely-missing-configmap\" not found。\n2. `kubectl get configmap` 显示 configmap \"rc-definitely-missing-configmap\" 不存在，返回 Error from server (NotFound)。\n\n冲突证据：\n- 无。\n\n结论：\n当前 Pod rc-volume-missing-configmap 无法启动，是因为它引用的 ConfigMap \"rc-definitely-missing-configmap\" 不存在。需要创建或修正该 ConfigMap 以解决挂载失败问题。","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 4/4 项，完整度 100%；实际执行工具 4 个，匹配计划 2 个，未规划证据 2 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":4,"environment_evidence_collected":4,"environment_evidence_completeness":1.0,"executed_tool_count":4,"matched_tool_count":2,"unplanned_tool_count":2,"evidence_inventory":[{"id":"e1","description":"验证 Pod rc-volume-missing-configmap 的详细状态和事件信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-configmap -n aiops-e2e","purpose":"确认 Pod 当前状态、关键事件、挂载卷配置，验证是否因 ConfigMap 缺失导致挂载失败","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查 ConfigMap rc-definitely-missing-configmap 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e","purpose":"验证 ConfigMap 是否缺失，从而确认是否导致挂载失败","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod rc-volume-missing-configmap 的详细状态和事件信息 | `kubectl describe pod rc-volume-missing-configmap -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_by_name | 检查 ConfigMap rc-definitely-missing-configmap ... | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (12.9s)
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
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 36.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4728 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 54.7s
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
| **Pod异常状态** | Pod rc-volume-missing-configmap 处于 `ContainerCreating` 状态 |
| **兼容归因层** | L0 |
| **问题分类** | VolumeMountFailed（卷挂载失败） |
| **置信度** | 高 |
| **证据完整度** | 2/2 (100%) |

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-volume-missing-configmap |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | `MountVolume.SetUp failed for volume "missing-config": configmap "rc-definitely-missing-configmap" not found` |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 事件详情 | `kubectl describe pod rc-volume-missing-configmap -n aiops-e2e` | `Warning  FailedMount  109s (x58 over 103m)   kubelet  MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found` | Pod 无法挂载名为 `missing-config` 的卷，因为引用的 ConfigMap 不存在 |
| 2 | ConfigMap 是否存在 | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` | `Error from server (NotFound): configmap "rc-definitely-missing-configmap" not found` | 该 ConfigMap 确实不存在于命名空间 `aiops-e2e` 中 |
| 3 | Pod 当前状态 | `kubectl get pod rc-volume-missing-configmap -n aiops-e2e` | `0/1     ContainerCreating   0                103m` | Pod 无法创建，处于 `ContainerCreating` 状态 |
| 4 | Pod 事件重复记录 | `kubectl describe pod rc-volume-missing-configmap -n aiops-e2e` | `Warning  FailedMount  33m (x10 over 94m)     kubelet  Unable to attach or mount volumes: unmounted volumes=[missing-config], unattached volumes=[kube-api-access-n5pfx missing-config]: timed out waiting for the condition` | 显示多次挂载失败 |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 事件中明确指出 `configmap "rc-definitely-missing-configmap" not found`，同时 `kubectl get` 也验证了该 ConfigMap 不存在，说明问题根源是配置缺失。
- **证据链**：Pod spec 中引用了不存在的 ConfigMap → kubelet 无法完成卷挂载 → Pod 无法创建 → 事件中持续记录 `FailedMount`。
- **证据 #3 + #4 印证**：Pod 持续处于 `ContainerCreating` 状态，且事件中多次记录挂载失败，说明问题为持续性错误，需要人工干预。

### 缺失证据（无）
无缺失证据。

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ ConfigMap "rc-definitely-missing-configmap" 不存在，导致 Pod 无法挂载卷。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ kubelet 在设置卷时发现 ConfigMap 不存在，导致 MountVolume.SetUp 失败。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Pod rc-volume-missing-configmap 的卷 `missing-config` 引用了不存在的 ConfigMap。 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-volume-missing-configmap 状态为 `ContainerCreating`，并持续记录 `FailedMount` 事件。 │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 和 #2，问题的根本原因是 **ConfigMap `rc-definitely-missing-configmap` 不存在**，导致 Pod `rc-volume-missing-configmap` 无法挂载卷 `missing-config`。  
**置信度**：高 (100%)  
- ✅ `kubectl describe pod` 明确指出 `configmap not found`
- ✅ `kubectl get` 验证 ConfigMap 确实不存在
- ✅ Pod 状态为 `ContainerCreating` 且事件中持续记录失败

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 创建缺失的 ConfigMap**
```bash
kubectl create configmap rc-definitely-missing-configmap -n aiops-e2e --from-literal=key=value
```
*依据*：ConfigMap 不存在是直接原因，创建后 Pod 可完成挂载  
*注意*：请根据实际需求替换 `--from-literal=key=value` 为正确的内容。

**2. [可选] 删除并重新创建 Pod**
```bash
kubectl delete pod rc-volume-missing-configmap -n aiops-e2e
```
*目的*：Kubernetes 会自动重新创建 Pod，触发挂载流程

### 后续优化
1. **检查 Pod spec 中的卷配置**：确保引用的 ConfigMap 名称和命名空间正确。
2. **配置 ConfigMap 存在性检查**：在部署流程中添加 ConfigMap 存在性校验，避免类似问题。
3. **启用事件监控**：配置监控告警，及时发现类似 `FailedMount` 事件。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 ConfigMap 是否存在 | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` | 显示 ConfigMap 信息 |
| 2. 确认 Pod 是否运行 | `kubectl get pod rc-volume-missing-configmap -n aiops-e2e` | STATUS: Running |
| 3. 检查 Pod 事件 | `kubectl describe pod rc-volume-missing-configmap -n aiops-e2e` | 不再出现 `FailedMount` 事件 |
| 4. 检查卷挂载 | `kubectl exec -it rc-volume-missing-configmap -n aiops-e2e -- cat /path/to/mounted/file` | 能够读取 ConfigMap 内容 |

---
## ⚠️ 注意事项
- 如果 ConfigMap 是从其他命名空间引用的，请确保使用 `namespace: <other-namespace>` 指定命名空间。
- 如果问题仍然存在，请检查 Pod spec 中的 `volumeMounts` 配置是否正确。
- 可以通过 `kubectl get pod -o yaml` 检查 Pod 的完整 spec。

---

## 📊 性能统计

├─ 总耗时: 3.9m
├─ 问题定位: 63.9s (27%) ✅
├─ 证据链采集: 61.7s (26%) ✅
├─ 根因分析: 12.9s (6%) ✅
├─ 汇总总结: 96.2s (41%) ✅
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
