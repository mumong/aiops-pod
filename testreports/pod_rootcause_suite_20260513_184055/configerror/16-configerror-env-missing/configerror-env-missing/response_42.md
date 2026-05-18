======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: cd286472dfe44b7c]

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
      📄 NAME                                     READY   STATUS             RESTARTS       AGE    IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-env-missing-5d9b8b766c-cstkh   0/
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": ["L4"],
  "layer_name": "ConfigError",
  "confidence": "high",
  "reasoning": "Pod 状态为 CrashLoopBackOff，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明配置错误导致容器无法正常启动。",
  "abnormal_pods": [
    {
      "name": "rc-config-env-missing-5d9b8b766c-cstkh",
      "namespace": "aiops-e2e",
      "status": "CrashLoopBackOff",
      "restarts": "28 (53s ago)",
      "age": "119m",
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
      "type": "ConfigError",
      "count": 1,
      "pods": [
        {
          "name": "rc-config-env-missing-5d9b8b766c-cstkh",
          "namespace": "aiops-e2e"
        }
      ]
    }
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "ConfigError",
  "status_category": "CrashLoopBackOff",
  "key_entities": [
    {
      "kind": "Pod",
      "name": "rc-config-env-missing-5d9b8b766c-cstkh",
      "namespace": "aiops-e2e"
    }
  ],
  "possible_scenarios": [
    {
      "description": "Pod 缺失必需的环境变量 APP_BOOT_MODE，导致配置启动失败。",
      "confidence": "high"
    }
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (49.8s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'Pod 缺失必需的环境变量 APP_BOOT_MODE，导致配置启动失败。', 'probability': 'high', 'reason': '日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE'}]
   entities=[{"type": "Pod", "name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e"}]
   reasoning=Pod 状态为 CrashLoopBackOff，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明配置错误导致容器无法正常启动。
   layer_analysis={"layer": "L4", "derived_layer": "", "layers": [], "layer_name": "", "confidence": 0.5, "reasoning": "Pod 状态为 CrashLoopBackOff，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明配置错误导致容器无法正常启动。", "abnormal_pods": [{"name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod 缺失必需的环境变量 APP_BOOT_MODE，导致配置启动失败。", "probability": "high", "reason": "日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-env-missing-5d9b8b766c-cstkh              0/1     CrashLoopBackOff   28 (48s ago)   118m    172.16.166.152   node1    <none>           <none>            app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/cd286472dfe44b7c/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/cd286472dfe44b7c/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/cd286472dfe44b7c/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
  Warning  BackOff  74s (x559 o
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
79s (x559 over 121m)   Warning   BackOff   Pod/rc-config-env-missing-5d9b8b766c-cstkh   Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstkh
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
   💭 [证据链采集] # 证据结论

## 已采集证据
1. **kubectl_describe**: Pod 状态为 `CrashLoopBackOff`，且事件显示 `Back-off restarting failed container`。
2. **kubectl_events**: 显示 `Back-off restarting failed container app`，表明容器重复失败。
3. **kubectl_previous_logs**: 显示关键日志 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，表明配置错误。

## 未采集证据
- 无

## 冲突证据
- 无

## 归因结论
当前 Pod 异常由配置错误引起，具体表现为缺失必需的环境变量 `APP_BOOT_MODE`，导致容器无法正常启动。
   ✅ [证据链采集] 完成 (2m 4.5s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"ep1","description":"获取异常 Pod 的详细描述，验证配置错误和事件信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","tool_args":{"pod":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e"},"purpose":"验证 Pod 的当前状态、事件和配置信息，确认是否存在环境变量缺失等问题","evidence_type":"status_and_events","target_scope":"specific_pod","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"ep2","description":"获取异常 Pod 的事件列表，检查是否存在配置错误相关事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-env-missing-5d9b8b766c-cstkh","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-config-env-missing-5d9b8b766c-cstkh"},"purpose":"验证 Pod 的事件信息，确认是否存在配置错误相关事件","evidence_type":"events","target_scope":"specific_pod","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"ep3","description":"获取异常 Pod 的上次容器日志，确认配置错误的具体原因","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous","tool_args":{"pod":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e","container":null,"previous":true},"purpose":"获取上次容器的退出日志，确认配置错误的具体原因","evidence_type":"logs","target_scope":"specific_pod","acceptable_tools":["kubectl_previous_logs"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-env-missing-5d9b8b766c-cstkh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Reason:       CrashLoopBackOff\n  Warning  BackOff  74s (x559 over 121m)  kubelet  Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)\n                  cni.projectcalico.org/containerID: b609d3199474fd0c991fb51944c653ad8de49c03971407f25be4cb50f1498fc2\n                  cni.projectcalico.org/podIP: 172.16.166.152/32\n                  cni.projectcalico.org/podIPs: 172.16.166.152/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/cd286472dfe44b7c/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/cd286472dfe44b7c/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/cd286472dfe44b7c/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n79s (x559 over 121m)   Warning   BackOff   Pod/rc-config-env-missing-5d9b8b766c-cstkh   Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/cd286472dfe44b7c/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/cd286472dfe44b7c/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/cd286472dfe44b7c/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/cd286472dfe44b7c/tools/003-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/cd286472dfe44b7c/tools/003-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/cd286472dfe44b7c/tools/003-evidence-kubectl_previous_logs.summary.txt"}],"llm_analysis":"# 证据结论\n\n## 已采集证据\n1. **kubectl_describe**: Pod 状态为 `CrashLoopBackOff`，且事件显示 `Back-off restarting failed container`。\n2. **kubectl_events**: 显示 `Back-off restarting failed container app`，表明容器重复失败。\n3. **kubectl_previous_logs**: 显示关键日志 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，表明配置错误。\n\n## 未采集证据\n- 无\n\n## 冲突证据\n- 无\n\n## 归因结论\n当前 Pod 异常由配置错误引起，具体表现为缺失必需的环境变量 `APP_BOOT_MODE`，导致容器无法正常启动。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 6 个，匹配计划 3 个，未规划证据 3 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":3,"unplanned_tool_count":3,"evidence_inventory":[{"id":"ep1","description":"获取异常 Pod 的详细描述，验证配置错误和事件信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","purpose":"验证 Pod 的当前状态、事件和配置信息，确认是否存在环境变量缺失等问题","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ep2","description":"获取异常 Pod 的事件列表，检查是否存在配置错误相关事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-env-missing-5d9b8b766c-cstkh","purpose":"验证 Pod 的事件信息，确认是否存在配置错误相关事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ep3","description":"获取异常 Pod 的上次容器日志，确认配置错误的具体原因","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous","purpose":"获取上次容器的退出日志，确认配置错误的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | ep1 | critical | ✅ | kubectl_describe | 获取异常 Pod 的详细描述，验证配置错误和事件信息 | `kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` |
   | ep2 | important | ✅ | kubectl_events | 获取异常 Pod 的事件列表，检查是否存在配置错误相关事件 | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-confi...` |
   | ep3 | important | ✅ | kubectl_previous_logs | 获取异常 Pod 的上次容器日志，确认配置错误的具体原因 | `kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (39.3s)
   📤 → 下游数据: root_cause=Pod rc-config-env-missing-5d9b8b766c-cstkh 无法启动，因为缺少必需的环境变量 APP_BOOT_MODE，导致配置启动失败。
   confidence=90%
   causal_chain={"root_cause": "缺失必需的环境变量 APP_BOOT_MODE", "direct_cause": "容器因缺少 APP_BOOT_MODE 环境变量而启动失败", "symptoms": "Pod 状态为 CrashLoopBackOff"}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"kubectl_describe": "Pod 状态为 `CrashLoopBackOff`，且事件显示 `Back-off restarting failed container`。"}, {"kubectl_events": "显示 `Back-off restarting failed container app`，表明容器重复失败。"}, {"kubectl_previous_logs": "显示关键日志 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，表明配置错误。"}], "evidence_analysis": [{"kubectl_describe": "Pod 状态为 `CrashLoopBackOff`，且事件显示 `Back-off restarting failed container`。"}, {"kubectl_events": "显示 `Back-off restarting failed container app`，表明容器重复失败。"}, {"kubectl_previous_logs": "显示关键日志 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，表明配置错误。"}], "causal_chain": {"root_cause": "缺失必需的环境变量 APP_BOOT_MODE", "direct_cause": "容器因缺少 APP_BOOT_MODE 环境变量而启动失败", "symptoms": "Pod 状态为 CrashLoopBackOff"}, "root_cause": "Pod rc-config-env-missing-5d9b8b766c-cstkh 无法启动，因为缺少必需的环境变量 APP_BOOT_MODE，导致配置启动失败。", "root_cause_summary": "Pod rc-config-env-missing-5d9b8b766c-cstkh 无法启动，因为缺少必需的环境变量 APP_BOOT_MODE，导致配置启动失败。", "confidence": 0.9, "confidence_reason": "有直接证据表明配置错误导致容器无法启动。", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [], "limitations": "未发现其他潜在原因。", "llm_raw_analysis": "当前 Pod 异常由配置错误引起，具体表现为缺失必需的环境变量 `APP_BOOT_MODE`，导致容器无法正常启动。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-config-env-missing-5d9b8b766c-cstkh 无法启动，因为缺少必需的环境变量 APP_BOOT_MODE，导致配置启动失败。
   置信度: 90%
   🔗 因果链:
     根本原因: 缺失必需的环境变量 APP_BOOT_MODE


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 16.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3905 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 50.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | CrashLoopBackOff |
| **兼容归因层** | L4 |
| **问题分类** | ConfigError |
| **置信度** | 高 (90%) |
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

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CrashLoopBackOff, RESTARTS: 28 (48s ago)` | Pod 由于配置错误持续重启 |
| 2 | Pod 事件 | `kubectl describe pod` | `Reason: CrashLoopBackOff` | 容器启动失败，触发重启机制 |
| 3 | 容器日志 | `kubectl logs <pod> --previous` | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` | 缺失关键环境变量 APP_BOOT_MODE，导致容器无法启动 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 CrashLoopBackOff，且事件中明确提示容器启动失败，确认问题为启动失败类错误。
- **证据 #3 印证**：日志中显示 `missing required APP_BOOT_MODE`，直接定位到配置缺失问题。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 缺失必需的环境变量 APP_BOOT_MODE，导致应用无法正常启动。        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器启动时因缺少 APP_BOOT_MODE 环境变量而失败。                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动失败，触发 Kubernetes 的 CrashLoopBackOff 机制。        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CrashLoopBackOff，重启次数持续增加。                 │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (CrashLoopBackOff 状态)、证据 #2 (Pod 事件) 和证据 #3 (日志信息)，问题的根本原因是**容器启动所需的环境变量 APP_BOOT_MODE 未正确配置**，导致容器无法正常启动，触发 Kubernetes 的 CrashLoopBackOff 机制。

**置信度**：高 (90%)
- ✅ 日志明确提示 `missing required APP_BOOT_MODE`
- ✅ Pod 状态和事件信息一致，确认是配置类错误
- ✅ 无缺失关键证据，证据链完整

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 为 Pod 配置 APP_BOOT_MODE 环境变量**
```bash
kubectl set env deployment/<deployment_name> -n aiops-e2e APP_BOOT_MODE=your_value
```
*依据*：日志中提示缺少 `APP_BOOT_MODE`，设置该变量即可解决启动问题。

**2. [可选] 通过 ConfigMap 或 Secret 管理环境变量**
```bash
kubectl create configmap app-config --from-literal=APP_BOOT_MODE=your_value -n aiops-e2e
```
```bash
# 在 Deployment 中引用 ConfigMap
kubectl set env deployment/<deployment_name> -n aiops-e2e --from=configmap/app-config
```
*目的*：将配置集中管理，避免硬编码，便于维护。

### 后续优化

1. **添加配置校验机制**：在部署流程中加入配置校验，防止缺失关键变量。
2. **监控日志和事件**：使用 Prometheus + Alertmanager 或 Kubernetes Events API 监控 Pod 启动失败事件。
3. **优化部署流程**：通过 CI/CD 流程验证环境变量是否正确注入。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 0 |
| 3. 查看容器日志 | `kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | 无 `L4_CONFIG_BOOTSTRAP_FAIL` 错误 |

---

## ⚠️ 注意事项

- 如果设置了 APP_BOOT_MODE 后 Pod 仍无法启动，建议检查其他环境变量是否完整。
- 为避免类似问题，建议使用 ConfigMap/Secret 管理配置，提高可维护性。
- 可考虑在部署流程中加入配置校验，防止缺失关键变量。

---

## 📌 附注

- **证据来源**：`kubectl describe pod`、`kubectl logs --previous`、`kubectl get pod`
- **诊断依据**：日志中明确提示 `missing required APP_BOOT_MODE`，且 Pod 状态为 `CrashLoopBackOff`
- **参考 Runbook**：[pod-config-error.md](#)（未提供链接，但内容匹配当前场景）

---

## 📊 性能统计

├─ 总耗时: 4.8m
├─ 问题定位: 49.8s (17%) ✅
├─ 证据链采集: 124.5s (43%) ✅
├─ 根因分析: 39.3s (14%) ✅
├─ 汇总总结: 76.7s (26%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 7 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 7 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
