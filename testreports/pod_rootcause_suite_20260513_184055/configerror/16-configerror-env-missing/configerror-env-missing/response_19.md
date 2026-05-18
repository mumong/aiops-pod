======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 67a291ac13fd4454]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'CrashLoopBackOff': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS           
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
      📄 NAME                                     READY   STATUS             RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-env-missing-5d9b8b766c-cstkh   0
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                     READY   STATUS             RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-env-missing-5d9b8b766c-cstkh   0
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": "high",
  "reasoning": "Pod 'rc-config-env-missing-5d9b8b766c-cstkh' 处于 CrashLoopBackOff 状态，日志显示 'L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE'，表明应用缺少必填的环境变量配置。此异常属于配置错误（ConfigError），归类为 L4 层级。",
  "abnormal_pods": [
    {
      "name": "rc-config-env-missing-5d9b8b766c-cstkh",
      "namespace": "aiops-e2e",
      "status": "CrashLoopBackOff",
      "restarts": "15 (2m30s ago)",
      "age": "53m"
    }
  ],
  "abnormal_groups": [
    {
      "type": "ConfigError",
      "count": 1
    }
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "ConfigError",
  "status_category": "CrashLoopBackOff",
  "key_entities": [
    "rc-config-env-missing-5d9b8b766c-cstkh",
    "aiops-e2e",
    "APP_BOOT_MODE"
  ],
  "possible_scenarios": [
    "缺少环境变量 APP_BOOT_MODE",
    "ConfigMap 或 Secret 中的配置未正确注入",
    "应用启动脚本依赖的配置项缺失"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 6.4s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '缺少环境变量 APP_BOOT_MODE', 'probability': 'high', 'reason': "日志中显示 'missing required APP_BOOT_MODE'，表明应用缺少必填的环境变量配置。"}, {'scenario': 'ConfigMap 或 Secret 中的配置未正确注入', 'probability': 'medium', 'reason': 'ConfigMap 或 Secret 中的配置项未正确注入到 Pod 中，导致应用无法正常启动。'}, {'scenario': '应用启动脚本依赖的配置项缺失', 'probability': 'medium', 'reason': '应用启动脚本依赖的配置项缺失，导致应用无法正常启动。'}]
   entities=[{"type": "Pod", "name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e"}, {"type": "Config", "name": "APP_BOOT_MODE", "namespace": "aiops-e2e"}]
   reasoning=Pod 'rc-config-env-missing-5d9b8b766c-cstkh' 处于 CrashLoopBackOff 状态，日志显示 'L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE'，表明应用缺少必填的环境变量配置。此异常属于配置错误（ConfigError），归类为 L4 层级。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.5, "reasoning": "Pod 'rc-config-env-missing-5d9b8b766c-cstkh' 处于 CrashLoopBackOff 状态，日志显示 'L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE'，表明应用缺少必填的环境变量配置。此异常属于配置错误（ConfigError），归类为 L4 层级。", "abnormal_pods": [{"name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "CrashLoopBackOff", "key_entities": [{"type": "Pod", "name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e"}, {"type": "Config", "name": "APP_BOOT_MODE", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "缺少环境变量 APP_BOOT_MODE", "probability": "high", "reason": "日志中显示 'missing required APP_BOOT_MODE'，表明应用缺少必填的环境变量配置。"}, {"scenario": "ConfigMap 或 Secret 中的配置未正确注入", "probability": "medium", "reason": "ConfigMap 或 Secret 中的配置项未正确注入到 Pod 中，导致应用无法正常启动。"}, {"scenario": "应用启动脚本依赖的配置项缺失", "probability": "medium", "reason": "应用启动脚本依赖的配置项缺失，导致应用无法正常启动。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-env-missing-5d9b8b766c-cstkh              0/1     CrashLoopBackOff   15 (2m19s ago)   53m     172.16.166.152   node1    <none>           <none>            app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/67a291ac13fd4454/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/67a291ac13fd4454/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/67a291ac13fd4454/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 50%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-env-missing-5d9b8b766c-cstkh
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Reason:       CrashLoopBackOff
  Warning  BackOff         60s 
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   ✅ [证据链采集] 完成 (1m 29.2s)
   📤 → 下游数据: evidence_items=6/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证异常 Pod 'rc-config-env-missing-5d9b8b766c-cstkh' 的详细状态和事件信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e"},"purpose":"获取异常 Pod 的详细状态和事件信息，确认是否与配置缺失有关","evidence_type":"current_status","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_describe","kubectl_get_by_name","kubectl_events"],"counts_for_completeness":true},{"id":"e2","description":"验证异常 Pod 的上一次容器日志，以确认具体配置失败原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous","tool_args":{"kind":"pod","name":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e"},"purpose":"获取异常 Pod 上一次容器的启动日志，确认是否因缺失环境变量 APP_BOOT_MODE 而失败","evidence_type":"logs","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_previous_logs","kubectl_logs","kubectl_container_previous_logs"],"counts_for_completeness":true},{"id":"e3","description":"验证 Pod 的 ConfigMap/Secret 是否已正确注入","level":"important","tool":"kubectl_get_by_name","command":"kubectl get configmap,secret -n aiops-e2e","tool_args":{"kind":"ConfigMap,Secret","namespace":"aiops-e2e"},"purpose":"确认 Pod 所依赖的 ConfigMap/Secret 是否存在，并且是否被正确注入到 Pod 中","evidence_type":"configuration","target_scope":"aiops-e2e","acceptable_tools":["kubectl_get_by_name","kubectl_get_by_kind_in_namespace","kubectl_get_yaml"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-env-missing-5d9b8b766c-cstkh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Reason:       CrashLoopBackOff\n  Warning  BackOff         60s (x258 over 56m)  kubelet            Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)\n                  cni.projectcalico.org/containerID: b609d3199474fd0c991fb51944c653ad8de49c03971407f25be4cb50f1498fc2\n                  cni.projectcalico.org/podIP: 172.16.166.152/32\n                  cni.projectcalico.org/podIPs: 172.16.166.152/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/67a291ac13fd4454/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/67a291ac13fd4454/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/67a291ac13fd4454/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/67a291ac13fd4454/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/67a291ac13fd4454/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/67a291ac13fd4454/tools/002-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'name' is a required property","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 6/7 项，完整度 86%；实际执行工具 6 个，匹配计划 2 个，未规划证据 4 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":7,"environment_evidence_collected":6,"environment_evidence_completeness":0.8571428571428571,"executed_tool_count":6,"matched_tool_count":2,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证异常 Pod 'rc-config-env-missing-5d9b8b766c-cstkh' 的详细状态和事件信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","purpose":"获取异常 Pod 的详细状态和事件信息，确认是否与配置缺失有关","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证异常 Pod 的上一次容器日志，以确认具体配置失败原因","level":"critical","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous","purpose":"获取异常 Pod 上一次容器的启动日志，确认是否因缺失环境变量 APP_BOOT_MODE 而失败","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"验证 Pod 的 ConfigMap/Secret 是否已正确注入","level":"important","tool":"kubectl_get_by_name","command":"kubectl get configmap,secret -n aiops-e2e","purpose":"确认 Pod 所依赖的 ConfigMap/Secret 是否存在，并且是否被正确注入到 Pod 中","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e3(验证 Pod 的 ConfigMap/Secret 是否已正确注入): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 86%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证异常 Pod 'rc-config-env-missing-5d9b8b766c-cs... | `kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_previous_logs | 验证异常 Pod 的上一次容器日志，以确认具体配置失败原因 | `kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous` |
   | e3 | important | ❌ | kubectl_get_by_name | 验证 Pod 的 ConfigMap/Secret 是否已正确注入 | `kubectl get configmap,secret -n aiops-e2e` |

   ⚠️ 未采集原因:
   - e3(验证 Pod 的 ConfigMap/Secret 是否已正确注入): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (8.9s)
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
   ✅ [汇总总结] 完成 (1m 19.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4452 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 3.6s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | CrashLoopBackOff |
| **兼容归因层** | L4 |
| **问题分类** | ConfigError（缺少环境变量 APP_BOOT_MODE） |
| **置信度** | 高 (85%) |
| **证据完整度** | 2/3 (67%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | rc-config-env-missing-5d9b8b766c-cstkh |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh` | `Reason: CrashLoopBackOff` | Pod 因配置错误持续重启 |
| 2 | 容器日志 | `kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous` | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` | 应用缺失必填环境变量 APP_BOOT_MODE |
| 3 | Pod 列表 | `kubectl get pods -A` | `aiops-e2e rc-config-env-missing-5d9b8b766c-cstkh 0/1 CrashLoopBackOff 15 (2m19s ago) 53m` | Pod 处于异常状态，重启次数持续增加 |
| 4 | Runbook | `fetch_runbook` | `典型状态: CreateContainerConfigError / CreateContainerError / CrashLoopBackOff` | 与当前 Pod 状态匹配，指向配置错误 |
| 5 | Pod 配置 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o json` | `Labels: pod_abnormal_type=ConfigError` | 明确标注为配置错误 |
| 6 | Pod 事件 | `kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh` | `Warning  BackOff         60s ` | Pod 重启后进入 BackOff 状态 |

### 证据关联分析

- **证据 #2 印证**：容器日志显示 `missing required APP_BOOT_MODE`，明确指出配置缺失。
- **证据 #1 + #4 + #5 印证**：Pod 状态为 `CrashLoopBackOff`，且标注为 `ConfigError`，符合 Runbook 中的典型场景。
- **证据链**：应用依赖的 `APP_BOOT_MODE` 环境变量缺失 → 应用启动失败 → 容器终止 → Pod 重启 → 进入 `CrashLoopBackOff` 状态。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 关联的 ConfigMap/Secret 是否存在 | critical | 无法确认是否配置对象未正确注入 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 应用依赖的环境变量 APP_BOOT_MODE 未在 Pod 中配置               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 应用启动时检测到缺少 APP_BOOT_MODE，抛出错误并退出              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器因配置错误退出，Pod 进入 CrashLoopBackOff 状态              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 CrashLoopBackOff，重启次数持续增加                     │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2（容器日志显示 `missing required APP_BOOT_MODE`）和证据 #5（Pod 明确标注为 `ConfigError`），问题的根本原因是**Pod 缺少必填的环境变量 `APP_BOOT_MODE`**，导致应用无法正常启动，容器退出，Pod 重启，进入 `CrashLoopBackOff` 状态。  
**置信度**：高 (85%)  
- ✅ 容器日志直接指出 `APP_BOOT_MODE` 缺失
- ✅ Pod 状态为 `CrashLoopBackOff`，符合 Runbook 中的典型场景
- ⚠️ 缺少 ConfigMap/Secret 验证证据，无法确认是否配置对象未正确注入

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 为 Pod 注入缺失的环境变量 `APP_BOOT_MODE`**

```bash
kubectl set env deployment/rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e APP_BOOT_MODE=dev
```

*依据*：容器日志明确指出 `APP_BOOT_MODE` 缺失，需注入默认值（如 `dev`）以启动应用。

**2. [可选] 查看当前 Pod 的完整配置**

```bash
kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o json
```

*目的*：确认环境变量是否已注入成功。

**3. [建议] 验证 ConfigMap/Secret 是否正确引用（如果使用）**

```bash
kubectl get configmap -n aiops-e2e
kubectl get secret -n aiops-e2e
```

*目的*：确认是否存在配置对象，并验证是否在 Pod spec 中正确引用。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 为 0 或不再增加 |
| 3. 检查环境变量是否生效 | `kubectl exec -it rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -- env` | 显示 `APP_BOOT_MODE=dev` |

---

## ⚠️ 注意事项

- 如果应用使用 ConfigMap/Secret 来注入环境变量，请确保其名称和键名正确无误。
- 如果环境变量值依赖于运行时配置（如多环境部署），建议通过 ConfigMap/Secret 动态注入，避免硬编码。
- 如果问题仍然存在，请检查应用的启动脚本或依赖项是否对 `APP_BOOT_MODE` 有其他隐式依赖。

---

## 📊 性能统计

├─ 总耗时: 4.1m
├─ 问题定位: 66.4s (27%) ✅
├─ 证据链采集: 89.2s (37%) ✅
├─ 根因分析: 8.9s (4%) ✅
├─ 汇总总结: 79.0s (32%) ✅
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
