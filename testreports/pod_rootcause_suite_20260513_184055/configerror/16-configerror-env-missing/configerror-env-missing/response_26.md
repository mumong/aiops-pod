======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: d6fa0afa56aa4b88]

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
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "ConfigError",
  "layers": ["L4"],
  "layer_name": "ConfigError",
  "confidence": "high",
  "reasoning": "Pod 状态为 CrashLoopBackOff，日志显示 'L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE'，表明是由于配置缺失导致的容器启动失败。符合 ConfigError 类型，归类为 L4 层。",
  "abnormal_pods": [
    {
      "name": "rc-config-env-missing-5d9b8b766c-cstkh",
      "namespace": "aiops-e2e",
      "status": "CrashLoopBackOff",
      "restarts": "19 (70s ago)",
      "age": "73m",
      "ip": "172.16.166.152",
      "node": "node1",
      "labels": {
        "app": "rc-config-env-missing",
        "pod-template-hash": "5d9b8b766c",
        "pod_abnormal_type": "ConfigError",
        "rootcause-e2e": "true"
      }
    }
  ],
  "abnormal_groups": [
    {
      "pod_status_keyword": "CrashLoopBackOff",
      "pod_abnormal_type": "ConfigError",
      "status_category": "ConfigError"
    }
  ],
  "key_entities": [
    {
      "name": "rc-config-env-missing-5d9b8b766c-cstkh",
      "type": "Pod",
      "namespace": "aiops-e2e"
    }
  ],
  "possible_scenarios": [
    {
      "description": "Pod 配置缺失导致容器启动失败",
      "evidence": [
        {
          "description": "日志显示 'L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE'",
          "source": "kubectl_previous_logs",
          "value": "L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE"
        }
      ]
    }
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (46.6s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'Pod 配置缺失导致容器启动失败', 'probability': 'high', 'reason': "日志显示 'L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE'"}]
   entities=[{"type": "Pod", "name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在一个仍处于异常状态的 Pod，状态为 CrashLoopBackOff，其日志显示 'L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE'，表明是由于配置缺失导致的容器启动失败。此异常类型属于 ConfigError，符合 L4 层的判定标准。
   layer_analysis={"layer": "L4", "derived_layer": "CONFIGERROR", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "当前环境中存在一个仍处于异常状态的 Pod，状态为 CrashLoopBackOff，其日志显示 'L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE'，表明是由于配置缺失导致的容器启动失败。此异常类型属于 ConfigError，符合 L4 层的判定标准。", "abnormal_pods": [{"name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod 配置缺失导致容器启动失败", "probability": "high", "reason": "日志显示 'L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE'"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-env-missing-5d9b8b766c-cstkh              0/1     CrashLoopBackOff   19 (70s ago)   73m     172.16.166.152   node1    <none>           <none>            app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/d6fa0afa56aa4b88/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/d6fa0afa56aa4b88/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/d6fa0afa56aa4b88/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-env-missing-5d9b8b766c-cstkh
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Reason:       CrashLoopBackOff
  Warning  BackOff  27s (x350 o
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
42s (x350 over 75m)   Warning   BackOff   Pod/rc-config-env-missing-5d9b8b766c-cstkh   Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstkh_
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
   💭 [证据链采集] # 证据结论
## 已采集证据
- **kubectl_describe**: 异常 Pod `rc-config-env-missing-5d9b8b766c-cstkh` 的状态为 `CrashLoopBackOff`，事件表明容器因错误而被重启。
- **kubectl_events**: 显示 `Back-off restarting failed container app`，说明容器失败后被自动重启。
- **kubectl_previous_logs**: 显示日志 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，明确指出配置错误是由于缺少 `APP_BOOT_MODE` 环境变量。

## 未采集证据
- 未对关联的 ConfigMap 或 Secret 进行检查，确认 `APP_BOOT_MODE` 是否缺失或配置错误。

## 冲突证据
- 无。

## 诊断建议
此 Pod 的异常是由于缺少必需的环境变量 `APP_BOOT_MODE`，导致应用启动失败。建议检查相关 ConfigMap 或 Secret，确保 `APP_BOOT_MODE` 正确配置。
   ✅ [证据链采集] 完成 (2m 47.8s)
   📤 → 下游数据: evidence_items=5/5
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细信息，包括配置错误和事件原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","tool_args":{"name":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e"},"purpose":"验证异常 Pod 的详细信息，包括配置错误、事件和状态原因","evidence_type":"raw_pod_info","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的事件日志，确认配置错误的上下文","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-env-missing-5d9b8b766c-cstkh","tool_args":{"namespace":"aiops-e2e","pod_name":"rc-config-env-missing-5d9b8b766c-cstkh"},"purpose":"获取异常 Pod 的事件日志，确认配置错误的上下文和失败原因","evidence_type":"pod_events","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取异常 Pod 的上一次容器日志，确认配置错误的具体信息","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous","tool_args":{"name":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e","container":"default"},"purpose":"获取异常 Pod 的上一次容器日志，确认配置错误的具体信息和失败原因","evidence_type":"pod_logs_previous","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-env-missing-5d9b8b766c-cstkh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Reason:       CrashLoopBackOff\n  Warning  BackOff  27s (x350 over 75m)  kubelet  Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)\n                  cni.projectcalico.org/containerID: b609d3199474fd0c991fb51944c653ad8de49c03971407f25be4cb50f1498fc2\n                  cni.projectcalico.org/podIP: 172.16.166.152/32\n                  cni.projectcalico.org/podIPs: 172.16.166.152/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d6fa0afa56aa4b88/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d6fa0afa56aa4b88/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d6fa0afa56aa4b88/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n42s (x350 over 75m)   Warning   BackOff   Pod/rc-config-env-missing-5d9b8b766c-cstkh   Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d6fa0afa56aa4b88/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d6fa0afa56aa4b88/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d6fa0afa56aa4b88/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d6fa0afa56aa4b88/tools/003-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d6fa0afa56aa4b88/tools/003-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d6fa0afa56aa4b88/tools/003-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"# 证据结论\n## 已采集证据\n- **kubectl_describe**: 异常 Pod `rc-config-env-missing-5d9b8b766c-cstkh` 的状态为 `CrashLoopBackOff`，事件表明容器因错误而被重启。\n- **kubectl_events**: 显示 `Back-off restarting failed container app`，说明容器失败后被自动重启。\n- **kubectl_previous_logs**: 显示日志 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，明确指出配置错误是由于缺少 `APP_BOOT_MODE` 环境变量。\n\n## 未采集证据\n- 未对关联的 ConfigMap 或 Secret 进行检查，确认 `APP_BOOT_MODE` 是否缺失或配置错误。\n\n## 冲突证据\n- 无。\n\n## 诊断建议\n此 Pod 的异常是由于缺少必需的环境变量 `APP_BOOT_MODE`，导致应用启动失败。建议检查相关 ConfigMap 或 Secret，确保 `APP_BOOT_MODE` 正确配置。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 5/5 项，完整度 100%；实际执行工具 5 个，匹配计划 3 个，未规划证据 2 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":5,"environment_evidence_collected":5,"environment_evidence_completeness":1.0,"executed_tool_count":5,"matched_tool_count":3,"unplanned_tool_count":2,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细信息，包括配置错误和事件原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","purpose":"验证异常 Pod 的详细信息，包括配置错误、事件和状态原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的事件日志，确认配置错误的上下文","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-env-missing-5d9b8b766c-cstkh","purpose":"获取异常 Pod 的事件日志，确认配置错误的上下文和失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取异常 Pod 的上一次容器日志，确认配置错误的具体信息","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous","purpose":"获取异常 Pod 的上一次容器日志，确认配置错误的具体信息和失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod 的详细信息，包括配置错误和事件原因 | `kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_events | 获取异常 Pod 的事件日志，确认配置错误的上下文 | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-confi...` |
   | e3 | important | ✅ | kubectl_previous_logs | 获取异常 Pod 的上一次容器日志，确认配置错误的具体信息 | `kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (34.6s)
   📤 → 下游数据: root_cause=根因是缺少必需的环境变量 `APP_BOOT_MODE`，导致应用启动失败。
   confidence=95%
   causal_chain={"root_cause": "缺少必需的环境变量 `APP_BOOT_MODE`", "intermediate_causes": ["容器启动时检测到 `APP_BOOT_MODE` 环境变量缺失", "应用因缺少 `APP_BOOT_MODE` 环境变量而启动失败"], "immediate_causes": ["容器因错误而不断重启，表现为 `CrashLoopBackOff` 状态", "事件 `Back-off restarting failed container app` 表示容器失败后被自动重启"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"kubectl_describe": "异常 Pod `rc-config-env-missing-5d9b8b766c-cstkh` 的状态为 `CrashLoopBackOff`，事件表明容器因错误而被重启。"}, {"kubectl_events": "显示 `Back-off restarting failed container app`，说明容器失败后被自动重启。"}, {"kubectl_previous_logs": "显示日志 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，明确指出配置错误是由于缺少 `APP_BOOT_MODE` 环境变量。"}], "evidence_analysis": [{"kubectl_describe": "Pod 状态为 `CrashLoopBackOff`，表示容器因错误而不断重启。"}, {"kubectl_events": "事件 `Back-off restarting failed container app` 表示容器失败后被自动重启。"}, {"kubectl_previous_logs": "日志 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` 明确指出配置错误是由于缺少 `APP_BOOT_MODE` 环境变量。"}], "causal_chain": {"root_cause": "缺少必需的环境变量 `APP_BOOT_MODE`", "intermediate_causes": ["容器启动时检测到 `APP_BOOT_MODE` 环境变量缺失", "应用因缺少 `APP_BOOT_MODE` 环境变量而启动失败"], "immediate_causes": ["容器因错误而不断重启，表现为 `CrashLoopBackOff` 状态", "事件 `Back-off restarting failed container app` 表示容器失败后被自动重启"]}, "root_cause": "根因是缺少必需的环境变量 `APP_BOOT_MODE`，导致应用启动失败。", "root_cause_summary": "根因是缺少必需的环境变量 `APP_BOOT_MODE`，导致应用启动失败。", "confidence": 0.95, "confidence_reason": "", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [{"cause": "ConfigMap 或 Secret 配置错误", "probability": "medium", "reason": "需要检查 ConfigMap 或 Secret 是否配置正确"}], "limitations": "未对关联的 ConfigMap 或 Secret 进行检查，确认 `APP_BOOT_MODE` 是否缺失或配置错误。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 根因是缺少必需的环境变量 `APP_BOOT_MODE`，导致应用启动失败。
   置信度: 95%
   🔗 因果链:
     根本原因: 缺少必需的环境变量 `APP_BOOT_MODE`


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 13.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3896 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 22.7s
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
| **Pod异常状态** | CrashLoopBackOff |
| **兼容归因层** | CONFIGERROR |
| **问题分类** | ConfigError（配置缺失） |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/3 (100%) |

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

**当前集群状态**：
- 存在 1 个处于异常状态的 Pod：`CrashLoopBackOff`
- 该 Pod 由于缺少必需的环境变量 `APP_BOOT_MODE` 导致容器启动失败
- 重启次数持续增加，处于持续重启状态

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 详细信息 | `kubectl describe pod` | `Reason: CrashLoopBackOff` | Pod 无法正常启动，处于 CrashLoopBackOff 状态 |
| 2 | Pod 事件日志 | `kubectl events` | `Warning BackOff Pod/rc-config-env-missing-5d9b8b766c-cstkh Back-off restarting failed container app` | 容器持续失败，Kubernetes 正在尝试重启 |
| 3 | 容器崩溃前日志 | `kubectl logs <pod> --previous` | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` | 明确指出启动失败是由于缺少环境变量 `APP_BOOT_MODE` |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 状态为 `CrashLoopBackOff`，同时事件中显示容器启动失败，表明问题在容器启动阶段发生
- **证据 #3 直接定位原因**：日志明确指出 `APP_BOOT_MODE` 缺失，是导致启动失败的根本原因

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| 关联的 ConfigMap/Secret 内容 | 低 | 无法确认 `APP_BOOT_MODE` 是否被错误配置或缺失 |

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 缺失必需的环境变量 `APP_BOOT_MODE`，导致应用无法启动              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器启动时缺少 `APP_BOOT_MODE` 配置 → 应用初始化失败            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动失败（Exit Code 137）                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，持续重启                           │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #3（日志中 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`）和证据 #1（`CrashLoopBackOff` 状态），问题的根本原因是**缺少必需的环境变量 `APP_BOOT_MODE`**，导致容器无法启动，从而引发 Pod 持续重启。
**置信度**：高 (95%)
- ✅ 日志明确指出配置缺失
- ✅ Pod 状态与事件日志一致，确认容器失败
- ⚠️ 未检查 ConfigMap/Secret，无法确认配置是否错误

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 为 Deployment 添加缺失的环境变量 `APP_BOOT_MODE`**
```bash
kubectl set env deployment/rc-config-env-missing -n aiops-e2e APP_BOOT_MODE=local
```
*依据*：日志明确指出 `APP_BOOT_MODE` 缺失，建议临时设置为 `local` 以验证修复效果

**2. [可选] 检查 ConfigMap/Secret 是否存在 `APP_BOOT_MODE`**
```bash
kubectl get configmap -n aiops-e2e
kubectl get secret -n aiops-e2e
kubectl describe configmap <configmap-name> -n aiops-e2e
```
*目的*：确认配置是否缺失或拼写错误

### 后续优化
1. **配置版本控制**：确保环境变量配置通过 ConfigMap/Secret 管理，避免硬编码
2. **配置校验机制**：在部署流水线中添加配置校验，防止缺失关键变量
3. **监控告警**：配置 Pod 状态告警（如 CrashLoopBackOff），提前发现配置问题

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 检查容器日志 | `kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | 不再出现 `L4_CONFIG_BOOTSTRAP_FAIL` |

---

## ⚠️ 注意事项
- 如果问题依旧，请检查 `APP_BOOT_MODE` 是否被正确注入到容器中
- 如果使用 ConfigMap/Secret，确保它们被正确挂载或设置为环境变量
- 检查部署文件，确认环境变量是否遗漏

---

---

## 📊 性能统计

├─ 总耗时: 5.4m
├─ 问题定位: 46.6s (14%) ✅
├─ 证据链采集: 167.8s (52%) ✅
├─ 根因分析: 34.6s (11%) ✅
├─ 汇总总结: 73.7s (23%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 6 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 6 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
