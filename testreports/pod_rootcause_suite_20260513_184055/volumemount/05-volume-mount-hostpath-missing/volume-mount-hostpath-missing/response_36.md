======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: faba6f1da4674e06]

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
      📄 NAME                         READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-volume-hostpath-missing   0/1     ContainerCreating   0         
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
4m21s (x50 over 89m)   Warning   FailedMount   Pod/rc-volume-hostpath-missing   MountVolume.SetUp failed for volume "missing-hostpath" : hostPath type check failed: /tmp/aiop
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-volume-hostpath-missing
namespace: aiops-e2e
creationTimestamp: 2026-05-13T18:26:26Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers
   💭 [问题定位] {
  "layer": "L0",
  "derived_layer": "L0",
  "layers": ["L0"],
  "layer_name": "VolumeMountFailed",
  "confidence": "high",
  "reasoning": "Pod rc-volume-hostpath-missing 处于 ContainerCreating 状态，Events 明确显示 hostPath 类型检查失败，即 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不是一个目录。这表明 hostPath 路径配置错误，属于 VolumeMountFailed 类型，归入 L0 层。",
  "abnormal_pods": ["rc-volume-hostpath-missing"],
  "abnormal_groups": ["VolumeMountFailed"],
  "pod_status_keyword": "ContainerCreating",
  "pod_abnormal_type": "VolumeMountFailed",
  "status_category": "storage_volume",
  "key_entities": ["Pod/rc-volume-hostpath-missing", "Volume/missing-hostpath", "Node/node1"],
  "possible_scenarios": [
    "hostPath 路径 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不存在或不是目录",
    "hostPath 路径权限不足，导致 kubelet 无法访问"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (45.2s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[{'scenario': 'hostPath 路径 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不存在或不是目录', 'probability': 'high', 'reason': 'Events 明确指出 hostPath 类型检查失败，即路径不是目录。'}, {'scenario': 'hostPath 路径权限不足，导致 kubelet 无法访问', 'probability': 'medium', 'reason': '如果路径存在，可能是权限不足导致 kubelet 无法访问。'}]
   entities=[{"type": "Pod", "name": "rc-volume-hostpath-missing", "namespace": "aiops-e2e"}, {"type": "Volume", "name": "missing-hostpath", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}]
   reasoning=Pod rc-volume-hostpath-missing 处于 ContainerCreating 状态，Events 明确显示 hostPath 类型检查失败，即 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不是一个目录。这表明 hostPath 路径配置错误，属于 VolumeMountFailed 类型，归入 L0 层。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "VolumeMountFailed", "confidence": 0.95, "reasoning": "Pod rc-volume-hostpath-missing 处于 ContainerCreating 状态，Events 明确显示 hostPath 类型检查失败，即 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不是一个目录。这表明 hostPath 路径配置错误，属于 VolumeMountFailed 类型，归入 L0 层。", "abnormal_pods": [{"name": "rc-volume-hostpath-missing", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "Pod", "name": "rc-volume-hostpath-missing", "namespace": "aiops-e2e"}, {"type": "Volume", "name": "missing-hostpath", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}], "possible_scenarios": [{"scenario": "hostPath 路径 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不存在或不是目录", "probability": "high", "reason": "Events 明确指出 hostPath 类型检查失败，即路径不是目录。"}, {"scenario": "hostPath 路径权限不足，导致 kubelet 无法访问", "probability": "medium", "reason": "如果路径存在，可能是权限不足导致 kubelet 无法访问。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-hostpath-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-hostpath-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-volume-hostpath-missing                          0/1     ContainerCreating   0                89m    <none>           node1    <none>           <none>            app=rc-volume-hostpath-missing,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/faba6f1da4674e06/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/faba6f1da4674e06/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/faba6f1da4674e06/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-hostpath-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  5m37s (x50 over 91m)  kubelet  MountVolume.SetUp failed 
   💭 [证据链采集] 已采集关键证据：
1. `kubectl describe pod` 明确显示 `MountVolume.SetUp failed for volume "missing-hostpath"`，并且 `hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory`。这表明 hostPath 配置的路径不是目录，导致挂载失败。
2. 事件中还包含 `timed out waiting for the condition`，进一步确认了挂载超时，与 hostPath 路径问题相关。

冲突证据：无。

未采集证据：无（当前证据已满足诊断需求）。
   ✅ [证据链采集] 完成 (47.8s)
   📤 → 下游数据: evidence_items=5/5
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod rc-volume-hostpath-missing 的详细状态和事件，确认 VolumeMountFailed 的具体原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-hostpath-missing -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","name":"rc-volume-hostpath-missing"},"purpose":"获取 Pod 的详细描述信息，特别是 Events 中的 FailedMount 信息，确认 hostPath 路径是否不存在或权限不足","evidence_type":"status_event","target_scope":"aiops-e2e/rc-volume-hostpath-missing","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-hostpath-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  5m37s (x50 over 91m)  kubelet  MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory\n  Warning  FailedMount  38s (x31 over 89m)    kubelet  Unable to attach or mount volumes: unmounted volumes=[missing-hostpath], unattached volumes=[missing-hostpath kube-api-access-42crm]: timed out waiting for the condition\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed\n    State:          Waiting\n      Reason:       ContainerCreating","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/faba6f1da4674e06/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/faba6f1da4674e06/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/faba6f1da4674e06/tools/001-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"已采集关键证据：\n1. `kubectl describe pod` 明确显示 `MountVolume.SetUp failed for volume \"missing-hostpath\"`，并且 `hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory`。这表明 hostPath 配置的路径不是目录，导致挂载失败。\n2. 事件中还包含 `timed out waiting for the condition`，进一步确认了挂载超时，与 hostPath 路径问题相关。\n\n冲突证据：无。\n\n未采集证据：无（当前证据已满足诊断需求）。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 5/5 项，完整度 100%；实际执行工具 5 个，匹配计划 1 个，未规划证据 4 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":5,"environment_evidence_collected":5,"environment_evidence_completeness":1.0,"executed_tool_count":5,"matched_tool_count":1,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证 Pod rc-volume-hostpath-missing 的详细状态和事件，确认 VolumeMountFailed 的具体原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-hostpath-missing -n aiops-e2e","purpose":"获取 Pod 的详细描述信息，特别是 Events 中的 FailedMount 信息，确认 hostPath 路径是否不存在或权限不足","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod rc-volume-hostpath-missing 的详细状态和事件，确认... | `kubectl describe pod rc-volume-hostpath-missing -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (22.6s)
   📤 → 下游数据: root_cause=Pod rc-volume-hostpath-missing 处于 ContainerCreating 状态，Events 明确显示 hostPath 类型检查失败，即 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不是一个目录。这表明 hostPath 路径配置错误，属于 VolumeMountFailed 类型，归入 L0 层。
   confidence=95%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "Pod rc-volume-hostpath-missing 处于 ContainerCreating 状态，Events 明确显示 hostPath 类型检查失败，即 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不是一个目录。这表明 hostPath 路径配置错误，属于 VolumeMountFailed 类型，归入 L0 层。", "root_cause_summary": "Pod rc-volume-hostpath-missing 处于 ContainerCreating 状态，Events 明确显示 hostPath 类型检查失败，即 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不是一个目录。这表明 hostPath 路径配置错误，属于 VolumeMountFailed 类型，归入 L0 层。", "confidence": 0.95, "confidence_reason": "有直接证据，因果链清晰。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [], "limitations": "无", "llm_raw_analysis": "已采集关键证据：\n1. `kubectl describe pod` 明确显示 `MountVolume.SetUp failed for volume \"missing-hostpath\"`，并且 `hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory`。这表明 hostPath 配置的路径不是目录，导致挂载失败。\n2. 事件中还包含 `timed out waiting for the condition`，进一步确认了挂载超时，与 hostPath 路径问题相关。\n\n冲突证据：无。\n\n未采集证据：无（当前证据已满足诊断需求）"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-volume-hostpath-missing 处于 ContainerCreating 状态，Events 明确显示 hostPath 类型检查失败，即 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不是一个目录。这表明 h...
   置信度: 95%

📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 13.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4625 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 8.8s
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
| **兼容归因层** | L0 |
| **问题分类** | VolumeMountFailed |
| **置信度** | 高 (95%) |
| **证据完整度** | 1/1 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-volume-hostpath-missing |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | kubectl describe pod rc-volume-hostpath-missing | `STATUS: ContainerCreating`, `Events: Warning FailedMount: hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory` | Pod 无法完成 VolumeMount，处于 ContainerCreating 状态 |
| 2 | Pod Events | kubectl get events | `4m21s (x50 over 89m) Warning FailedMount: MountVolume.SetUp failed for volume "missing-hostpath": hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory` | 明确指出 hostPath 路径配置错误，不是目录 |
| 3 | Pod YAML | kubectl get pod rc-volume-hostpath-missing -o yaml | `volumeMounts: /tmp/aiops-rootcause-definitely-missing-hostpath-dir` | Pod 挂载路径为 hostPath，路径不存在或不是目录 |
| 4 | Node 信息 | kubectl describe node node1 | N/A | 无需进一步采集，问题与 Node 无关 |
| 5 | Runbook 匹配 | fetch_runbook | 匹配 `pod-volume-mount-failed.md` | 问题归类为 VolumeMountFailed，典型状态为 ContainerCreating |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 无法挂载 hostPath 卷，Events 明确指出路径不是目录。
- **证据链**：用户配置了 hostPath 类型卷，路径 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 不存在或不是目录 → kubelet 挂载失败 → Pod 无法创建 → 状态为 ContainerCreating。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | 无 | 无 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ hostPath 路径 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不存在或不是目录 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ kubelet 尝试挂载 hostPath 卷 → 路径不存在或不是目录 → 挂载失败 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ MountVolume.SetUp failed for volume "missing-hostpath"        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-volume-hostpath-missing 状态为 ContainerCreating，无法创建容器 │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态为 ContainerCreating) 和证据 #2 (Events 明确指出 hostPath 路径不是目录)，问题的根本原因是 **hostPath 路径配置错误**，路径 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 不存在或不是目录，导致 kubelet 无法挂载卷，进而 Pod 无法创建。  
**置信度**：高 (95%)  
- ✅ Events 明确指出 hostPath 类型检查失败  
- ✅ Pod YAML 显示配置了该路径  
- ✅ Runbook 匹配为 VolumeMountFailed 类型

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 创建缺失的目录或修正 hostPath 路径**

```bash
# 在 node1 上执行
mkdir -p /tmp/aiops-rootcause-definitely-missing-hostpath-dir
```

*依据*：Events 明确指出路径不存在或不是目录，创建后 kubelet 可挂载成功

**2. [可选] 修正 Pod YAML 中的 hostPath 配置（如果路径错误）**

```bash
# 编辑对应的 Pod 或 Deployment YAML，将 hostPath 路径修改为有效目录
kubectl edit pod rc-volume-hostpath-missing -n aiops-e2e
```

*依据*：如果路径本身是错误配置，应修正为实际存在的目录

**3. [可选] 删除并重新创建 Pod**

```bash
kubectl delete pod rc-volume-hostpath-missing -n aiops-e2e
```

*依据*：删除后 kubelet 会重新尝试挂载，如果路径已修复则可成功

### 后续优化

1. **路径配置验证**：在部署前验证 hostPath 路径是否真实存在且权限正确
2. **使用 PVC 替代 hostPath（如需持久化）**：hostPath 依赖节点路径，建议使用 PVC + PersistentVolume 提高可移植性
3. **配置 kubelet 日志监控**：监控 kubelet 日志中的 `MountVolume.SetUp failed` 事件，及时发现类似问题

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-volume-hostpath-missing -n aiops-e2e` | STATUS: Running |
| 2. 检查 hostPath 路径 | `ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir` | 目录存在 |
| 3. 检查 kubelet 日志 | `journalctl -u kubelet` | 无 `MountVolume.SetUp failed` 错误 |
| 4. 检查 Pod Events | `kubectl describe pod rc-volume-hostpath-missing -n aiops-e2e` | 无 Warning 级别事件 |

---

## ⚠️ 注意事项

- hostPath 是节点本地路径，不适合跨节点部署，建议考虑使用 PVC/PV 或持久化存储方案
- 如果路径权限不足（如 kubelet 无法访问），需要调整目录权限或使用 `fsGroup` 等安全策略
- 修复后建议删除并重新创建 Pod 以触发 kubelet 重新挂载

---

---

## 📊 性能统计

├─ 总耗时: 4.1m
├─ 问题定位: 45.2s (18%) ✅
├─ 证据链采集: 47.8s (19%) ✅
├─ 根因分析: 22.6s (9%) ✅
├─ 汇总总结: 133.1s (53%) ✅
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
