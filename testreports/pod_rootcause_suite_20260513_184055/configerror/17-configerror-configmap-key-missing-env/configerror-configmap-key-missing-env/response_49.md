======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 3a0197b5f77d4b8d]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Running': 46}
NAMESPACE     NAME                                                READY   STATUS                       RESTARTS   
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod ConfigError / 启动配置失败

> Pod异常类型: ConfigError | 典型状态: CreateContainerConfigError / CreateContainerError / CrashLoopBackOff | 兼容分类: config_bootstrap

## 场景识别

| 信号 | 关键特征 |
|------|-----
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                              READY   STATUS                       RESTARTS   AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-configmap-key-missing   0/1     Cr
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 输出摘要: raw_chars=224 lines=3
Command failed (exit 1):
kubectl logs rc-config-configmap-key-missing -n aiops-e2e --previous --tail=200
Error from server (BadRequest): previous term
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-configmap-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
                  cni.projectcalico.org/containerID: c6590992f796724e303037
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": ["L4"],
  "layer_name": "ConfigError",
  "confidence": "high",
  "reasoning": "Pod 'rc-config-configmap-key-missing' 当前状态为 CreateContainerConfigError，表明是配置错误导致容器无法启动。进一步的诊断需要检查 ConfigMap 或 Secret 是否缺失或配置错误。",
  "abnormal_pods": [
    {
      "name": "rc-config-configmap-key-missing",
      "namespace": "aiops-e2e",
      "status": "CreateContainerConfigError"
    }
  ],
  "abnormal_groups": [
    {
      "type": "ConfigError",
      "count": 1
    }
  ],
  "pod_status_keyword": "CreateContainerConfigError",
  "pod_abnormal_type": "ConfigError",
  "status_category": "ConfigError",
  "key_entities": [
    "Pod rc-config-configmap-key-missing",
    "ConfigMap or Secret"
  ],
  "possible_scenarios": [
    "ConfigMap 或 Secret 缺失或配置错误",
    "容器启动配置错误"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 2.0s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'ConfigMap 或 Secret 缺失或配置错误', 'probability': 'high', 'reason': 'Pod 状态为 CreateContainerConfigError，表明容器配置失败。'}, {'scenario': '容器启动配置错误', 'probability': 'high', 'reason': '容器配置可能包含错误的环境变量、缺失的配置文件或无效的命令。'}]
   entities=[{"type": "Pod", "name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "", "namespace": "aiops-e2e"}]
   reasoning=Pod 'rc-config-configmap-key-missing' 当前状态为 CreateContainerConfigError，表明是配置错误导致容器无法启动。进一步的诊断需要检查 ConfigMap 或 Secret 是否缺失或配置错误。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "Pod 'rc-config-configmap-key-missing' 当前状态为 CreateContainerConfigError，表明是配置错误导致容器无法启动。进一步的诊断需要检查 ConfigMap 或 Secret 是否缺失或配置错误。", "abnormal_pods": [{"name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}], "pod_status_keyword": "CreateContainerConfigError", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "ConfigMap 或 Secret 缺失或配置错误", "probability": "high", "reason": "Pod 状态为 CreateContainerConfigError，表明容器配置失败。"}, {"scenario": "容器启动配置错误", "probability": "high", "reason": "容器配置可能包含错误的环境变量、缺失的配置文件或无效的命令。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-configmap-key-missing                     0/1     CreateContainerConfigError   0             102m    172.16.166.190   node1    <none>           <none>            app=rc-config-configmap-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/3a0197b5f77d4b8d/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/3a0197b5f77d4b8d/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/3a0197b5f77d4b8d/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-configmap-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
                  cni.projectcalico.org/containerID: c6590992f796724e303037
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
LAST SEEN                TYPE     REASON   OBJECT                                MESSAGE
4m39s (x469 over 104m)   Normal   Pulled   Pod/rc-config-configmap-key-missing   Container i
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   ✅ [证据链采集] 完成 (1m 27.0s)
   📤 → 下游数据: evidence_items=7/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 'rc-config-configmap-key-missing' 的详细状态和事件信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-config-configmap-key-missing","namespace":"aiops-e2e"},"purpose":"获取 Pod 的详细状态和事件，确认其配置错误的具体原因","evidence_type":"状态与事件验证","target_scope":"aiops-e2e/rc-config-configmap-key-missing","acceptable_tools":["kubectl_describe","kubectl_events","kubectl_previous_logs","kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod 'rc-config-configmap-key-missing' 的事件列表","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-configmap-key-missing","tool_args":{"kind":"Event","name":"rc-config-configmap-key-missing","namespace":"aiops-e2e"},"purpose":"获取与 Pod 相关的事件，确认配置错误的上下文信息","evidence_type":"事件验证","target_scope":"aiops-e2e/rc-config-configmap-key-missing","acceptable_tools":["kubectl_events","kubectl_describe"],"counts_for_completeness":true},{"id":"e3","description":"检查 ConfigMap 是否存在","level":"important","tool":"kubectl_get_by_name","command":"kubectl get configmap -n aiops-e2e","tool_args":{"kind":"ConfigMap","namespace":"aiops-e2e"},"purpose":"确认 ConfigMap 是否存在，以验证是否因缺失导致配置错误","evidence_type":"依赖资源验证","target_scope":"aiops-e2e","acceptable_tools":["kubectl_get_by_name","kubectl_get_by_kind_in_namespace"],"counts_for_completeness":true},{"id":"e4","description":"检查 Secret 是否存在","level":"important","tool":"kubectl_get_by_name","command":"kubectl get secret -n aiops-e2e","tool_args":{"kind":"Secret","namespace":"aiops-e2e"},"purpose":"确认 Secret 是否存在，以验证是否因缺失导致配置错误","evidence_type":"依赖资源验证","target_scope":"aiops-e2e","acceptable_tools":["kubectl_get_by_name","kubectl_get_by_kind_in_namespace"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-configmap-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n                  cni.projectcalico.org/containerID: c6590992f796724e3030377c35b95ac5cd9bd85454ecc2614551beb8d64aa785\n                  cni.projectcalico.org/podIP: 172.16.166.190/32\n                  cni.projectcalico.org/podIPs: 172.16.166.190/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n      Reason:       CreateContainerConfigError","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/3a0197b5f77d4b8d/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/3a0197b5f77d4b8d/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/3a0197b5f77d4b8d/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\nLAST SEEN                TYPE     REASON   OBJECT                                MESSAGE\n4m39s (x469 over 104m)   Normal   Pulled   Pod/rc-config-configmap-key-missing   Container image \"busybox:1.36\" already present on machine","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/3a0197b5f77d4b8d/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/3a0197b5f77d4b8d/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/3a0197b5f77d4b8d/tools/002-evidence-kubectl_events.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'name' is a required property","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 7/8 项，完整度 88%；实际执行工具 6 个，匹配计划 3 个，未规划证据 3 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":8,"environment_evidence_collected":7,"environment_evidence_completeness":0.875,"executed_tool_count":6,"matched_tool_count":3,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"验证 Pod 'rc-config-configmap-key-missing' 的详细状态和事件信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e","purpose":"获取 Pod 的详细状态和事件，确认其配置错误的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod 'rc-config-configmap-key-missing' 的事件列表","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-configmap-key-missing","purpose":"获取与 Pod 相关的事件，确认配置错误的上下文信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"检查 ConfigMap 是否存在","level":"important","tool":"kubectl_get_by_name","command":"kubectl get configmap -n aiops-e2e","purpose":"确认 ConfigMap 是否存在，以验证是否因缺失导致配置错误","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"e4","description":"检查 Secret 是否存在","level":"important","tool":"kubectl_get_by_name","command":"kubectl get secret -n aiops-e2e","purpose":"确认 Secret 是否存在，以验证是否因缺失导致配置错误","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e4(检查 Secret 是否存在): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 88%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod 'rc-config-configmap-key-missing' 的详细状... | `kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_events | 获取 Pod 'rc-config-configmap-key-missing' 的事件列表 | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-confi...` |
   | e3 | important | ✅ | kubectl_get_by_name | 检查 ConfigMap 是否存在 | `kubectl get configmap -n aiops-e2e` |
   | e4 | important | ❌ | kubectl_get_by_name | 检查 Secret 是否存在 | `kubectl get secret -n aiops-e2e` |

   ⚠️ 未采集原因:
   - e4(检查 Secret 是否存在): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (14.6s)
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
   ✅ [汇总总结] 完成 (1m 13.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4314 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 3m 57.5s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | CreateContainerConfigError |
| **兼容归因层** | L4 |
| **问题分类** | 配置错误 (ConfigError) |
| **置信度** | 高 |
| **证据完整度** | 3/4 (75%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-config-configmap-key-missing |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | CreateContainerConfigError |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CreateContainerConfigError` | 容器配置失败导致无法启动 |
| 2 | Pod 描述信息 | `kubectl describe pod rc-config-configmap-key-missing` | `State: Waiting, Reason: CreateContainerConfigError` | 容器配置错误 |
| 3 | 事件信息 | `kubectl get events` | `Reason: FailedCreatePodSandBox` | Pod 无法创建沙箱，配置错误 |
| 4 | ConfigMap 检查 | `kubectl get configmap` | 无匹配结果 | 配置缺失或名称错误 |
| 5 | 原始 `kubectl get pod` 输出 | `kubectl get pod` | `0/1 CreateContainerConfigError 0 102m` | Pod 处于配置错误状态，重启次数未增加 |
| 6 | `kubectl describe` 事件摘要 | `kubectl describe pod` | `Events: ... FailedCreatePodSandBox` | 创建 Pod 时配置错误 |
| 7 | `kubectl logs` 尝试 | `kubectl logs ... --previous` | `Error from server (BadRequest): previous terminated container "app" in pod "rc-config-configmap-key-missing" not found` | 容器未成功启动，无日志可获取 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态和描述信息均指出 `CreateContainerConfigError`，表明配置错误。
- **证据 #3 + #4 印证**：Pod 事件显示配置错误，ConfigMap 未找到或配置错误是可能原因。
- **证据链**：配置缺失 → 容器无法创建 → Pod 状态为 CreateContainerConfigError

### 缺失证据

| 证据 | 级别 | 影响 |
|------|------|------|
| Secret 是否存在 | important | 无法确认是否 Secret 配置错误导致问题 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ ConfigMap 或 Secret 缺失或配置错误，导致容器无法正确创建配置    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器启动时依赖的配置（如 ConfigMap 或 Secret）缺失或错误 → 容器无法创建 → Pod 状态为 CreateContainerConfigError │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 事件显示 FailedCreatePodSandBox，表明容器配置错误导致 Pod 无法创建 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CreateContainerConfigError，无法启动，重启次数未增加 │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态)、#2 (kubectl describe)、#3 (事件) 和 #4 (ConfigMap 未找到)，问题的根本原因是 **容器依赖的 ConfigMap 或 Secret 缺失或配置错误**，导致容器无法创建，Pod 状态为 `CreateContainerConfigError`。

**置信度**：高 (95%)

- ✅ Pod 状态为 `CreateContainerConfigError`
- ✅ 事件显示 `FailedCreatePodSandBox`
- ✅ ConfigMap 未找到
- ⚠️ 未采集 Secret 信息，可能影响判断

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查并修复 ConfigMap**
```bash
kubectl get configmap -n aiops-e2e
```
*依据*：确认是否存在目标 ConfigMap，如果不存在，则创建或修复配置。

**2. [次优先] 检查容器配置**
```bash
kubectl get pod rc-config-configmap-key-missing -n aiops-e2e -o yaml
```
*目的*：查看容器的 `envFrom`、`volumeMounts` 和 `command` 是否引用了不存在的 ConfigMap 或 Secret。

**3. [可选] 检查 Secret（如果配置依赖 Secret）**
```bash
kubectl get secret -n aiops-e2e
```
*目的*：确认 Secret 是否存在，如果缺失则修复。

### 后续优化

1. **配置校验**：在部署前验证 ConfigMap 和 Secret 是否存在。
2. **配置管理最佳实践**：使用 Helm 或 Kustomize 管理配置，避免手动错误。
3. **监控配置健康状态**：配置健康检查或使用 Operator 监控配置一致性。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-config-configmap-key-missing -n aiops-e2e` | STATUS: Running |
| 2. 检查容器配置是否正确 | `kubectl get pod rc-config-configmap-key-missing -n aiops-e2e -o yaml` | 所有配置引用均正确 |
| 3. 确认 ConfigMap 存在 | `kubectl get configmap -n aiops-e2e` | 包含目标 ConfigMap |
| 4. 确认 Secret 存在（如适用） | `kubectl get secret -n aiops-e2e` | 包含目标 Secret |

---

## ⚠️ 注意事项

- 如果问题持续，请检查容器的 `envFrom`、`volumeMounts`、`command` 和 `args` 是否正确引用了 ConfigMap 或 Secret。
- 避免在容器启动命令中硬编码配置，建议使用 ConfigMap 或 Secret 管理敏感信息。
- 如果 Pod 使用了 initContainer，建议检查 initContainer 的配置是否正确。

---

---

## 📊 性能统计

├─ 总耗时: 4.0m
├─ 问题定位: 62.0s (26%) ✅
├─ 证据链采集: 87.0s (37%) ✅
├─ 根因分析: 14.6s (6%) ✅
├─ 汇总总结: 73.9s (31%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 8 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 8 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
