======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 186d7d8682484766]

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
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-configmap-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          10m (x12 over 12m)    kubelet            Error: 
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME            DATA   AGE   LABELS
rc-app-config   1      12m   rootcause-e2e=true
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: ConfigMap
name: rc-app-config
namespace: aiops-e2e
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-config-configmap-key-missing
namespace: aiops-e2e
creationTimestamp: 2026-05-15T00:41:57Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
final
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": ["L4"],
  "layer_name": "ConfigError",
  "confidence": 0.95,
  "reasoning": "Pod rc-config-configmap-key-missing 处于 CreateContainerConfigError 状态，Events 显示 Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config。describe 和 YAML 检查确认 ConfigMap rc-app-config 中缺少该键。这属于 ConfigError，归为 L4 层。",
  "abnormal_pods": ["rc-config-configmap-key-missing"],
  "abnormal_groups": ["ConfigError"],
  "pod_status_keyword": "CreateContainerConfigError",
  "pod_abnormal_type": "ConfigError",
  "status_category": "ConfigError",
  "key_entities": {
    "Pod": "rc-config-configmap-key-missing",
    "ConfigMap": "aiops-e2e/rc-app-config",
    "MissingKey": "APP_BOOT_MODE"
  },
  "possible_scenarios": [
    "ConfigMap rc-app-config 缺失键 APP_BOOT_MODE，导致 Pod 启动失败",
    "Pod 引用了 ConfigMap 中不存在的键，配置错误",
    "Pod 的环境变量配置依赖于 ConfigMap 中缺失的键"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (53.8s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'ConfigMap rc-app-config 缺失键 APP_BOOT_MODE，导致 Pod 启动失败', 'probability': 'high', 'reason': 'Pod 启动失败，Events 明确指出缺少 APP_BOOT_MODE 键'}, {'scenario': 'Pod 引用了 ConfigMap 中不存在的键，配置错误', 'probability': 'high', 'reason': 'ConfigMap 中确实不存在该键'}, {'scenario': 'Pod 的环境变量配置依赖于 ConfigMap 中缺失的键', 'probability': 'high', 'reason': 'Pod 的启动失败直接归因于该键的缺失'}]
   entities=[{"type": "Pod", "name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-app-config", "namespace": "aiops-e2e"}, {"type": "MissingKey", "name": "APP_BOOT_MODE", "namespace": ""}]
   reasoning=Pod rc-config-configmap-key-missing 处于 CreateContainerConfigError 状态，Events 显示 Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config。describe 和 YAML 检查确认 ConfigMap rc-app-config 中缺少该键。这属于 ConfigError，归为 L4 层。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "Pod rc-config-configmap-key-missing 处于 CreateContainerConfigError 状态，Events 显示 Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config。describe 和 YAML 检查确认 ConfigMap rc-app-config 中缺少该键。这属于 ConfigError，归为 L4 层。", "abnormal_pods": [{"name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}], "pod_status_keyword": "CreateContainerConfigError", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-app-config", "namespace": "aiops-e2e"}, {"type": "MissingKey", "name": "APP_BOOT_MODE", "namespace": ""}], "possible_scenarios": [{"scenario": "ConfigMap rc-app-config 缺失键 APP_BOOT_MODE，导致 Pod 启动失败", "probability": "high", "reason": "Pod 启动失败，Events 明确指出缺少 APP_BOOT_MODE 键"}, {"scenario": "Pod 引用了 ConfigMap 中不存在的键，配置错误", "probability": "high", "reason": "ConfigMap 中确实不存在该键"}, {"scenario": "Pod 的环境变量配置依赖于 ConfigMap 中缺失的键", "probability": "high", "reason": "Pod 的启动失败直接归因于该键的缺失"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-configmap-key-missing                     0/1     CreateContainerConfigError   0             12m     172.16.166.190   node1    <none>           <none>            app=rc-config-configmap-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/186d7d8682484766/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/186d7d8682484766/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/186d7d8682484766/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME            DATA   AGE   LABELS
rc-app-config   1      15m   rootcause-e2e=true
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-configmap-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          13m (x12 over 15m)   kubelet            Error: c
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                              READY   STATUS                       RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-configmap-key-missing   0/1     Cre
   💭 [证据链采集] 已采集证据：
- ConfigMap rc-app-config 确认缺失键 APP_BOOT_MODE。
- Pod rc-config-configmap-key-missing 状态为 CreateContainerConfigError，Events 明确显示 Error: couldn't find key APP_BOOT_MODE in ConfigMap。
- Pod rc-config-configmap-key-missing 的配置验证了其引用的 ConfigMap 键值缺失。

结论：当前问题由 ConfigMap rc-app-config 缺失键 APP_BOOT_MODE 引起，导致 Pod rc-config-configmap-key-missing 无法正常启动。建议检查业务配置需求并补充该键。
   ✅ [证据链采集] 完成 (2m 13.9s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 ConfigMap rc-app-config 是否存在且包含键 APP_BOOT_MODE","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-app-config -n aiops-e2e -o yaml","tool_args":{"kind":"ConfigMap","name":"rc-app-config","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"确认 ConfigMap 是否包含缺失键 APP_BOOT_MODE","evidence_type":"configuration","target_scope":"aiops-e2e/ConfigMap/rc-app-config","acceptable_tools":["kubectl_get_by_name","kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod rc-config-configmap-key-missing 的完整描述信息","level":"important","tool":"kubectl_describe","command":"kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-config-configmap-key-missing","namespace":"aiops-e2e"},"purpose":"获取 Pod 的详细状态和事件信息，确认 CreateContainerConfigError 的具体原因","evidence_type":"events","target_scope":"aiops-e2e/Pod/rc-config-configmap-key-missing","acceptable_tools":["kubectl_describe","kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod rc-config-configmap-key-missing 的完整 YAML 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-configmap-key-missing -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-config-configmap-key-missing","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"获取 Pod 的完整配置，确认其引用的 ConfigMap 键值是否正确","evidence_type":"configuration","target_scope":"aiops-e2e/Pod/rc-config-configmap-key-missing","acceptable_tools":["kubectl_get_yaml","kubectl_get_by_name"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME            DATA   AGE   LABELS\nrc-app-config   1      15m   rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/186d7d8682484766/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/186d7d8682484766/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/186d7d8682484766/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-configmap-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          13m (x12 over 15m)   kubelet            Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config\n                  cni.projectcalico.org/containerID: c6590992f796724e3030377c35b95ac5cd9bd85454ecc2614551beb8d64aa785\n                  cni.projectcalico.org/podIP: 172.16.166.190/32\n                  cni.projectcalico.org/podIPs: 172.16.166.190/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n      Reason:       CreateContainerConfigError","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/186d7d8682484766/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/186d7d8682484766/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/186d7d8682484766/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                              READY   STATUS                       RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-config-configmap-key-missing   0/1     CreateContainerConfigError   0          15m   172.16.166.190   node1   <none>           <none>            app=rc-config-configmap-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/186d7d8682484766/tools/003-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/186d7d8682484766/tools/003-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/186d7d8682484766/tools/003-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集证据：\n- ConfigMap rc-app-config 确认缺失键 APP_BOOT_MODE。\n- Pod rc-config-configmap-key-missing 状态为 CreateContainerConfigError，Events 明确显示 Error: couldn't find key APP_BOOT_MODE in ConfigMap。\n- Pod rc-config-configmap-key-missing 的配置验证了其引用的 ConfigMap 键值缺失。\n\n结论：当前问题由 ConfigMap rc-app-config 缺失键 APP_BOOT_MODE 引起，导致 Pod rc-config-configmap-key-missing 无法正常启动。建议检查业务配置需求并补充该键。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"验证 ConfigMap rc-app-config 是否存在且包含键 APP_BOOT_MODE","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-app-config -n aiops-e2e -o yaml","purpose":"确认 ConfigMap 是否包含缺失键 APP_BOOT_MODE","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod rc-config-configmap-key-missing 的完整描述信息","level":"important","tool":"kubectl_describe","command":"kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e","purpose":"获取 Pod 的详细状态和事件信息，确认 CreateContainerConfigError 的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod rc-config-configmap-key-missing 的完整 YAML 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-configmap-key-missing -n aiops-e2e -o yaml","purpose":"获取 Pod 的完整配置，确认其引用的 ConfigMap 键值是否正确","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 验证 ConfigMap rc-app-config 是否存在且包含键 APP_BOOT_... | `kubectl get configmap rc-app-config -n aiops-e2e -o yaml` |
   | e2 | important | ✅ | kubectl_describe | 获取 Pod rc-config-configmap-key-missing 的完整描述信息 | `kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e` |
   | e3 | important | ✅ | kubectl_get_yaml | 获取 Pod rc-config-configmap-key-missing 的完整 YA... | `kubectl get pod rc-config-configmap-key-missing -n aiops-e2e -o yaml` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (9.7s)
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
   ✅ [汇总总结] 完成 (1m 2.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3640 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 19.4s
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
| **问题分类** | ConfigError |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/3 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-config-configmap-key-missing |
| Namespace | aiops-e2e |
| ConfigMap | rc-app-config |
| 错误信息 | Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CreateContainerConfigError` | Pod 无法创建容器，配置错误 |
| 2 | Pod 描述 | `kubectl describe pod rc-config-configmap-key-missing` | `Warning: Failed: Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config` | 错误明确指出缺失键 `APP_BOOT_MODE` |
| 3 | ConfigMap 内容 | `kubectl get configmap rc-app-config` | `DATA: 1` | 证实在 ConfigMap 中确实没有键 `APP_BOOT_MODE` |

### 证据关联分析

- **证据 #2 + #3 印证**：Pod 启动失败是因为引用了 ConfigMap 中不存在的键 `APP_BOOT_MODE`。
- **证据链**：Pod 引用了缺失的键 → 容器配置失败 → Pod 状态为 `CreateContainerConfigError`。

### 缺失证据（无）

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ ConfigMap `rc-app-config` 中缺少键 `APP_BOOT_MODE`              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod 引用了 ConfigMap 中不存在的键 APP_BOOT_MODE                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-config-configmap-key-missing 状态为 CreateContainerConfigError，无法启动 │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2（Pod 事件 `couldn't find key APP_BOOT_MODE`）和证据 #3（ConfigMap `rc-app-config` 中确实没有该键），问题的根本原因是**ConfigMap 缺失键 `APP_BOOT_MODE`**，导致 Pod 启动失败。
**置信度**：高 (95%)
- ✅ Pod 事件明确指出键缺失
- ✅ ConfigMap 实际确实没有该键
- ✅ 没有缺失证据

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 向 ConfigMap 添加缺失的键 `APP_BOOT_MODE`**

```bash
kubectl edit configmap rc-app-config -n aiops-e2e
```

*操作步骤*：
- 在打开的 YAML 编辑器中，添加如下字段：
```yaml
data:
  APP_BOOT_MODE: "normal"
```
- 保存并退出，Kubernetes 会自动更新配置。

**2. [可选] 查看 Pod 是否恢复**

```bash
kubectl get pod rc-config-configmap-key-missing -n aiops-e2e
```

*目的*：确认 Pod 状态变为 `Running`。

### 后续优化

1. **配置验证**：在部署前增加配置校验机制，确保引用的键在 ConfigMap 中存在。
2. **自动化检测**：集成 CI/CD 流程中检查 ConfigMap 与 Pod 配置的一致性。
3. **文档记录**：记录所有关键配置项及其用途，避免遗漏。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 ConfigMap 包含键 `APP_BOOT_MODE` | `kubectl get configmap rc-app-config -n aiops-e2e -o jsonpath='{.data}'` | 输出包含 `APP_BOOT_MODE` |
| 2. 确认 Pod 状态 | `kubectl get pod rc-config-configmap-key-missing -n aiops-e2e` | 状态为 `Running` |
| 3. 检查 Pod 事件 | `kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e` | 无 `Error` 事件 |

---

## ⚠️ 注意事项

- 如果 Pod 仍未恢复，请检查是否引用了其他缺失的键。
- 确保 ConfigMap 更新后，Pod 会被重新调度或重新拉起。如果未自动恢复，可手动删除 Pod，触发重建。
- 在生产环境中，建议使用 Helm 或 Kustomize 管理 ConfigMap，避免手动操作错误。

---

## 📊 性能统计

├─ 总耗时: 4.3m
├─ 问题定位: 53.8s (21%) ✅
├─ 证据链采集: 133.9s (52%) ✅
├─ 根因分析: 9.7s (4%) ✅
├─ 汇总总结: 62.0s (24%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 9 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 9 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
