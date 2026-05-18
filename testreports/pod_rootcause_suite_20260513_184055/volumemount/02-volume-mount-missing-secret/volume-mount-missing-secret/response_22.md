======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 62567b449de4404e]

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
rc-volume-missing-secret   0/1     ContainerCreating   0          42m
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
12m (x23 over 42m)     Warning   FailedMount   Pod/rc-volume-missing-secret   MountVolume.SetUp failed for volume "missing-secret" : secret "rc-definitely-missing-secret" not
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=187 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide secret rc-definitely-missing-secret -n aiops-e2e
Error from server (NotFound): secrets "rc-de
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
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": 0.95,
  "reasoning": "当前异常 Pod rc-volume-missing-secret 处于 ContainerCreating 状态，Events 显示 MountVolume.SetUp failed 且明确指向 secret \"rc-definitely-missing-secret\" not found。Pod spec 中的 volumes[].secret 字段为 null，进一步确认引用的 Secret 不存在。此问题属于 ConfigError 层，因为是配置缺失（Secret 未创建）导致的卷挂载失败。",
  "abnormal_pods": [
    "aiops-e2e/rc-volume-missing-secret"
  ],
  "abnormal_groups": {
    "VolumeMountFailed": 1
  },
  "pod_status_keyword": "ContainerCreating",
  "pod_abnormal_type": "VolumeMountFailed",
  "status_category": "VolumeMountFailed",
  "key_entities": [
    "Pod/aiops-e2e/rc-volume-missing-secret",
    "Secret/aiops-e2e/rc-definitely-missing-secret"
  ],
  "possible_scenarios": [
    "Secret rc-definitely-missing-secret 未创建，导致 Pod rc-volume-missing-secret 无法挂载卷",
    "Pod rc-volume-missing-secret 的 volumes 配置引用了不存在的 Secret",
    "Pod rc-volume-missing-secret 的 volume 配置错误，需要检查 volumes[].secret 的名称和命名空间"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (55.2s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'Secret rc-definitely-missing-secret 未创建，导致 Pod rc-volume-missing-secret 无法挂载卷', 'probability': 'High', 'reason': 'Events 明确显示 secret not found'}, {'scenario': 'Pod rc-volume-missing-secret 的 volumes 配置引用了不存在的 Secret', 'probability': 'High', 'reason': 'Pod spec 中的 volumes[].secret 字段为 null'}, {'scenario': 'Pod rc-volume-missing-secret 的 volume 配置错误，需要检查 volumes[].secret 的名称和命名空间', 'probability': 'High', 'reason': 'Pod spec 明确引用了错误的 Secret'}]
   entities=[{"type": "Pod", "name": "rc-volume-missing-secret", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-definitely-missing-secret", "namespace": "aiops-e2e"}]
   reasoning=当前异常 Pod rc-volume-missing-secret 处于 ContainerCreating 状态，Events 显示 MountVolume.SetUp failed 且明确指向 secret "rc-definitely-missing-secret" not found。Pod spec 中的 volumes[].secret 字段为 null，进一步确认引用的 Secret 不存在。此问题属于 ConfigError 层，因为是配置缺失（Secret 未创建）导致的卷挂载失败。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "当前异常 Pod rc-volume-missing-secret 处于 ContainerCreating 状态，Events 显示 MountVolume.SetUp failed 且明确指向 secret \"rc-definitely-missing-secret\" not found。Pod spec 中的 volumes[].secret 字段为 null，进一步确认引用的 Secret 不存在。此问题属于 ConfigError 层，因为是配置缺失（Secret 未创建）导致的卷挂载失败。", "abnormal_pods": [{"name": "rc-volume-missing-secret", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "VolumeMountFailed", "key_entities": [{"type": "Pod", "name": "rc-volume-missing-secret", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-definitely-missing-secret", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Secret rc-definitely-missing-secret 未创建，导致 Pod rc-volume-missing-secret 无法挂载卷", "probability": "High", "reason": "Events 明确显示 secret not found"}, {"scenario": "Pod rc-volume-missing-secret 的 volumes 配置引用了不存在的 Secret", "probability": "High", "reason": "Pod spec 中的 volumes[].secret 字段为 null"}, {"scenario": "Pod rc-volume-missing-secret 的 volume 配置错误，需要检查 volumes[].secret 的名称和命名空间", "probability": "High", "reason": "Pod spec 明确引用了错误的 Secret"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-secret"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-secret"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-volume-missing-secret                            0/1     ContainerCreating   0                42m    <none>           node1    <none>           <none>            app=rc-volume-missing-secret,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/62567b449de4404e/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/62567b449de4404e/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/62567b449de4404e/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 95%

📍 [证据链采集] 执行中...
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
  Warning  FailedMount  13m (x23 over 44m)    kubelet            MountVolume.SetUp
   💭 [证据链采集] 已采集证据:
- kubectl_describe 显示 Pod rc-volume-missing-secret 的 status 为 Pending，且存在多个 FailedMount 事件，指出 secret "rc-definitely-missing-secret" not found。
   ✅ [证据链采集] 完成 (42.1s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod rc-volume-missing-secret 的详细状态和 Events 原文，以确认卷挂载失败的具体原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-secret -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","pod_name":"rc-volume-missing-secret"},"purpose":"获取 Pod 的详细状态和 Events，以确认卷挂载失败的具体原因","evidence_type":"environment","target_scope":"aiops-e2e/rc-volume-missing-secret","acceptable_tools":["kubectl_describe","kubectl_get_by_name","kubectl_get_by_kind_in_namespace","kubectl_events","kubectl_get_yaml","kubectl_get_by_kind_in_cluster","kubectl_find_resource"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-missing-secret\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  13m (x23 over 44m)    kubelet            MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found\n  Warning  FailedMount  26m                   kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-secret], unattached volumes=[kube-api-access-8jtht missing-secret]: timed out waiting for the condition\n  Warning  FailedMount  3m53s (x16 over 42m)  kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-secret], unattached volumes=[missing-secret kube-api-access-8jtht]: timed out waiting for the condition\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed\n    State:          Waiting\n      Reason:       ContainerCreating","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/62567b449de4404e/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/62567b449de4404e/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/62567b449de4404e/tools/001-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"已采集证据:\n- kubectl_describe 显示 Pod rc-volume-missing-secret 的 status 为 Pending，且存在多个 FailedMount 事件，指出 secret \"rc-definitely-missing-secret\" not found。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 6 个，匹配计划 1 个，未规划证据 5 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":1,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证 Pod rc-volume-missing-secret 的详细状态和 Events 原文，以确认卷挂载失败的具体原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-secret -n aiops-e2e","purpose":"获取 Pod 的详细状态和 Events，以确认卷挂载失败的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod rc-volume-missing-secret 的详细状态和 Events... | `kubectl describe pod rc-volume-missing-secret -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (28.8s)
   📤 → 下游数据: root_cause=Pod rc-volume-missing-secret 无法启动，因为它引用了一个不存在的 Secret rc-definitely-missing-secret。
   confidence=95%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "Pod rc-volume-missing-secret 无法启动，因为它引用了一个不存在的 Secret rc-definitely-missing-secret。", "root_cause_summary": "Pod rc-volume-missing-secret 无法启动，因为它引用了一个不存在的 Secret rc-definitely-missing-secret。", "confidence": 0.95, "confidence_reason": "Events 明确显示 MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found。此外，尝试获取该 Secret 的命令返回了 NotFound 错误，确认了该 Secret 不存在。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [], "limitations": "未发现其他相关证据。", "llm_raw_analysis": "证据清点：\n1. kubectl_describe 显示 Pod rc-volume-missing-secret 的 status 为 Pending，且存在多个 FailedMount 事件，指出 secret \"rc-definitely-missing-secret\" not found。\n\n逐条分析：\n- kubectl_describe 显示 Pod rc-volume-missing-secret 的 status 为 Pending，且存在多个 FailedMount 事件，指出 secret \"rc-definitely-missing-secret\" not found。这表明 Pod 无法启动，因为它引用了一个不存在的 Secret。\n\n关联分析：\n- Pod rc-volume-missing-secret 的 status 为 Pending，且存在多个 FailedMount 事件，指出 secret \"rc-definitely-missing-secret\" not found。这表明 Pod 无法启动，因为它引用了一个不存在的 Secret。\n\n因果链\n... 截断，原始 888 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-volume-missing-secret 无法启动，因为它引用了一个不存在的 Secret rc-definitely-missing-secret。
   置信度: 95%

📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 55.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4646 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 1.5s
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
| Pod | rc-volume-missing-secret |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | MountVolume.SetUp failed for volume "missing-secret": secret "rc-definitely-missing-secret" not found |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod rc-volume-missing-secret -n aiops-e2e` | `STATUS: ContainerCreating` | Pod 处于创建中，因卷挂载失败无法启动 |
| 2 | Events 原文 | `kubectl describe pod rc-volume-missing-secret -n aiops-e2e` | `Warning FailedMount: MountVolume.SetUp failed for volume "missing-secret": secret "rc-definitely-missing-secret" not found` | 卷挂载失败，原因是 Secret 不存在 |
| 3 | Secret 验证 | `kubectl get secret rc-definitely-missing-secret -n aiops-e2e` | `Error from server (NotFound): secrets "rc-definitely-missing-secret" not found` | Secret 确实未创建 |
| 4 | Pod YAML 配置 | `kubectl get pod rc-volume-missing-secret -n aiops-e2e -o yaml` | `volumes[].secret 字段为 null` | Pod 配置中引用了错误或不存在的 Secret |
| 5 | 事件时间线 | `kubectl get events -n aiops-e2e` | `12m (x23 over 42m) Warning FailedMount` | 事件重复多次，持续失败 |
| 6 | Runbook 匹配 | `fetch_runbook` | `# Pod VolumeMountFailed / 卷挂载失败` | 匹配典型卷挂载失败场景 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 `ContainerCreating`，Events 明确显示 `MountVolume.SetUp failed for volume "missing-secret"`，说明卷挂载失败。
- **证据 #2 + #3 印证**：卷挂载失败的原因是 Secret `rc-definitely-missing-secret` 不存在，且 `kubectl get secret` 也验证了此 Secret 不存在。
- **证据 #4 印证**：Pod 的 YAML 配置中引用了错误的 Secret，导致卷挂载失败。

### 缺失证据（无）

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Secret rc-definitely-missing-secret 未创建                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod rc-volume-missing-secret 尝试挂载一个不存在的 Secret        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ MountVolume.SetUp failed，因为 Secret 不存在                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-volume-missing-secret 无法启动，状态为 ContainerCreating │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (Events 显示 `MountVolume.SetUp failed for volume "missing-secret": secret "rc-definitely-missing-secret" not found`) 和证据 #3 (`kubectl get secret` 显示 Secret 不存在)，问题的根本原因是**Secret `rc-definitely-missing-secret` 未创建**，导致 Pod `rc-volume-missing-secret` 无法挂载卷。

**置信度**：高 (95%)
- ✅ Events 明确指向 Secret 不存在
- ✅ `kubectl get secret` 验证了 Secret 不存在
- ✅ Pod YAML 显示引用了错误的 Secret

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 创建缺失的 Secret**
```bash
kubectl create secret generic rc-definitely-missing-secret -n aiops-e2e --from-literal=data=example
```
*依据*：Events 明确显示 Secret 不存在，需创建该 Secret 以解决卷挂载失败问题。

**2. [可选] 验证 Secret 是否创建成功**
```bash
kubectl get secret rc-definitely-missing-secret -n aiops-e2e
```
*目的*：确认 Secret 已成功创建。

**3. [可选] 重新调度 Pod**
```bash
kubectl delete pod rc-volume-missing-secret -n aiops-e2e
```
*目的*：删除 Pod 后由控制器重新创建，以尝试挂载成功。

### 后续优化

1. **配置自动创建 Secret 的机制**（如使用 Operator、CI/CD 集成）
2. **加强配置校验**：在 CI/CD 阶段校验引用的 Secret 是否存在，避免部署失败
3. **监控卷挂载失败事件**：使用 Prometheus 或 Kubernetes Events 监控卷挂载失败事件，及时发现类似问题

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Secret 是否存在 | `kubectl get secret rc-definitely-missing-secret -n aiops-e2e` | NAME: rc-definitely-missing-secret |
| 2. 确认 Pod 是否启动 | `kubectl get pod rc-volume-missing-secret -n aiops-e2e` | STATUS: Running |
| 3. 检查 Events 是否正常 | `kubectl describe pod rc-volume-missing-secret -n aiops-e2e` | No FailedMount events |
| 4. 检查卷是否挂载成功 | `kubectl exec -it rc-volume-missing-secret -n aiops-e2e -- ls /path/to/mount` | 文件或目录存在 |

---

## ⚠️ 注意事项

- 如果 Secret 需要敏感数据（如密码、证书），请使用 `--from-file` 或 `--from-literal` 安全创建。
- 如果问题仍存在，请检查 Pod 的 YAML 配置中卷的名称是否与 Secret 名称一致。
- 如果 Pod 仍然无法启动，建议检查卷的其他配置（如 volumeMounts 路径）是否正确。

---

## 📊 性能统计

├─ 总耗时: 4.0m
├─ 问题定位: 55.2s (23%) ✅
├─ 证据链采集: 42.1s (17%) ✅
├─ 根因分析: 28.8s (12%) ✅
├─ 汇总总结: 115.5s (48%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 7 次
```

📋 诊断追踪

- **核心 Runbook**: pod-volume-mount-failed
- **参考 Runbook**: pod-volume-mount-failed
- **工具调用**: 7 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
