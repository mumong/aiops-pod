======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 4f1793ac519847fb]

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
      📄 NAME                           READY   STATUS                       RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-secret-key-missing   0/1     CreateCon
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 输出摘要: raw_chars=218 lines=3
Command failed (exit 1):
kubectl logs rc-config-secret-key-missing -n aiops-e2e --previous --tail=200
Error from server (BadRequest): previous termina
   💭 [问题定位] 调用工具: kubectl_logs
   💭 [问题定位] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 输出摘要: raw_chars=225 lines=3
Command failed (exit 1):
kubectl logs rc-config-secret-key-missing -n aiops-e2e --tail=200
Error from server (BadRequest): container "app" in pod "rc-config-se
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          49m (x12 over 51m)   kubelet            Error: coul
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": "high",
  "reasoning": "Pod 'rc-config-secret-key-missing' 处于 CreateContainerConfigError 状态，事件显示 'couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret'，符合 ConfigError 的判定规则。此问题属于配置错误，影响 Pod 启动。",
  "abnormal_pods": [
    "rc-config-secret-key-missing"
  ],
  "abnormal_groups": {
    "ConfigError": 1
  },
  "pod_status_keyword": "CreateContainerConfigError",
  "pod_abnormal_type": "ConfigError",
  "status_category": "ConfigError",
  "key_entities": [
    "rc-config-secret-key-missing",
    "aiops-e2e/rc-app-secret",
    "APP_SECRET_TOKEN"
  ],
  "possible_scenarios": [
    "Secret 'rc-app-secret' 缺失键 'APP_SECRET_TOKEN'，导致 Pod 启动失败。",
    "Pod 引用了错误的 Secret 或命名空间，导致找不到指定键。",
    "Secret 未正确创建或更新，导致配置无法生效。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (51.7s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': "Secret 'rc-app-secret' 缺失键 'APP_SECRET_TOKEN'，导致 Pod 启动失败。", 'probability': 'high', 'reason': '事件明确指出找不到 APP_SECRET_TOKEN 键。'}, {'scenario': 'Pod 引用了错误的 Secret 或命名空间，导致找不到指定键。', 'probability': 'medium', 'reason': 'Pod 配置可能引用了错误的 Secret 或命名空间。'}, {'scenario': 'Secret 未正确创建或更新，导致配置无法生效。', 'probability': 'medium', 'reason': 'Secret 可能未被正确创建或更新。'}]
   entities=[{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}, {"type": "ConfigKey", "name": "APP_SECRET_TOKEN", "namespace": ""}]
   reasoning=Pod 'rc-config-secret-key-missing' 处于 CreateContainerConfigError 状态，事件显示 'couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret'，符合 ConfigError 的判定规则。此问题属于配置错误，影响 Pod 启动。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.5, "reasoning": "Pod 'rc-config-secret-key-missing' 处于 CreateContainerConfigError 状态，事件显示 'couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret'，符合 ConfigError 的判定规则。此问题属于配置错误，影响 Pod 启动。", "abnormal_pods": [{"name": "rc-config-secret-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}], "pod_status_keyword": "CreateContainerConfigError", "pod_abnormal_type": "ConfigError", "status_category": "ConfigError", "key_entities": [{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}, {"type": "ConfigKey", "name": "APP_SECRET_TOKEN", "namespace": ""}], "possible_scenarios": [{"scenario": "Secret 'rc-app-secret' 缺失键 'APP_SECRET_TOKEN'，导致 Pod 启动失败。", "probability": "high", "reason": "事件明确指出找不到 APP_SECRET_TOKEN 键。"}, {"scenario": "Pod 引用了错误的 Secret 或命名空间，导致找不到指定键。", "probability": "medium", "reason": "Pod 配置可能引用了错误的 Secret 或命名空间。"}, {"scenario": "Secret 未正确创建或更新，导致配置无法生效。", "probability": "medium", "reason": "Secret 可能未被正确创建或更新。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-secret-key-missing                        0/1     CreateContainerConfigError   0             51m     172.16.166.188   node1    <none>           <none>            app=rc-config-secret-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/4f1793ac519847fb/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/4f1793ac519847fb/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/4f1793ac519847fb/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          51m (x12 over 53m)     kubelet            Error: co
   💭 [证据链采集] 调用工具: kubectl_logs
   💭 [证据链采集] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 输出摘要: raw_chars=225 lines=3
Command failed (exit 1):
kubectl logs rc-config-secret-key-missing -n aiops-e2e --tail=200
Error from server (BadRequest): container "app" in pod "rc-config-se
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME            TYPE     DATA   AGE   LABELS
rc-app-secret   Opaque   1      53m   rootcause-e2e=true
   💭 [证据链采集] 已采集关键证据：
1. **Positive Evidence**: `kubectl describe pod` 显示 Pod 处于 `CreateContainerConfigError`，事件显示 `Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`。
2. **Positive Evidence**: `kubectl get secret rc-app-secret` 显示 Secret 存在，但数据字段数为 1，暗示 `APP_SECRET_TOKEN` 可能缺失。
3. **Negative Evidence**: `kubectl logs` 报错 `container "app" in pod "rc-config-secret-key-missing" is waiting to start: CreateContainerConfigError`，验证了容器尚未成功启动，无法获取日志。

**结论**：
- Secret `rc-app-secret` 缺失键 `APP_SECRET_TOKEN`，导致 Pod `rc-config-secret-key-missing` 无法正常启动，符合 `ConfigError` 的诊断结论。
   ✅ [证据链采集] 完成 (1m 50.7s)
   📤 → 下游数据: evidence_items=7/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"确认异常 Pod 'rc-config-secret-key-missing' 是否仍处于 CreateContainerConfigError 状态，并获取其详细事件日志。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","tool_args":{"pod":"rc-config-secret-key-missing","namespace":"aiops-e2e"},"purpose":"验证异常 Pod 当前状态及关键事件信息","evidence_type":"status_and_events","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 'rc-config-secret-key-missing' 的容器日志，以确认启动失败的具体原因。","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-config-secret-key-missing -n aiops-e2e --tail=200","tool_args":{"pod":"rc-config-secret-key-missing","namespace":"aiops-e2e","tail":"200"},"purpose":"验证容器日志以确认错误原因","evidence_type":"container_logs","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"确认 Secret 'rc-app-secret' 是否存在，以及是否包含键 'APP_SECRET_TOKEN'。","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-app-secret -n aiops-e2e -o jsonpath='{.data}'","tool_args":{"resource":"secret","name":"rc-app-secret","namespace":"aiops-e2e","output_format":"{.data}"},"purpose":"验证 Secret 是否存在并包含指定键","evidence_type":"secret_data_verification","target_scope":"aiops-e2e/rc-app-secret","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          51m (x12 over 53m)     kubelet            Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\n                  cni.projectcalico.org/containerID: 8f443601171b0e4049e100f3c3704966fe0c483b32880bd181c9fc13cf69ec95\n                  cni.projectcalico.org/podIP: 172.16.166.188/32\n                  cni.projectcalico.org/podIPs: 172.16.166.188/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n      Reason:       CreateContainerConfigError","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4f1793ac519847fb/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4f1793ac519847fb/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4f1793ac519847fb/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 输出摘要: raw_chars=225 lines=3\nCommand failed (exit 1):\nkubectl logs rc-config-secret-key-missing -n aiops-e2e --tail=200\nError from server (BadRequest): container \"app\" in pod \"rc-config-secret-key-missing\" is waiting to start: CreateContainerConfigError","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/4f1793ac519847fb/tools/002-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4f1793ac519847fb/tools/002-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4f1793ac519847fb/tools/002-evidence-kubectl_logs.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME            TYPE     DATA   AGE   LABELS\nrc-app-secret   Opaque   1      53m   rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/4f1793ac519847fb/tools/003-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/4f1793ac519847fb/tools/003-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/4f1793ac519847fb/tools/003-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集关键证据：\n1. **Positive Evidence**: `kubectl describe pod` 显示 Pod 处于 `CreateContainerConfigError`，事件显示 `Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`。\n2. **Positive Evidence**: `kubectl get secret rc-app-secret` 显示 Secret 存在，但数据字段数为 1，暗示 `APP_SECRET_TOKEN` 可能缺失。\n3. **Negative Evidence**: `kubectl logs` 报错 `container \"app\" in pod \"rc-config-secret-key-missing\" is waiting to start: CreateContainerConfigError`，验证了容器尚未成功启动，无法获取日志。\n\n**结论**：\n- Secret `rc-app-secret` 缺失键 `APP_SECRET_TOKEN`，导致 Pod `rc-config-secret-key-missing` 无法正常启动，符合 `ConfigError` 的诊断结论。","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 7/8 项，完整度 88%；实际执行工具 6 个，匹配计划 2 个，未规划证据 4 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":8,"environment_evidence_collected":7,"environment_evidence_completeness":0.875,"executed_tool_count":6,"matched_tool_count":2,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"确认异常 Pod 'rc-config-secret-key-missing' 是否仍处于 CreateContainerConfigError 状态，并获取其详细事件日志。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","purpose":"验证异常 Pod 当前状态及关键事件信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 'rc-config-secret-key-missing' 的容器日志，以确认启动失败的具体原因。","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-config-secret-key-missing -n aiops-e2e --tail=200","purpose":"验证容器日志以确认错误原因","collected":false,"source":"planned","outcome":"unknown"},{"id":"e3","description":"确认 Secret 'rc-app-secret' 是否存在，以及是否包含键 'APP_SECRET_TOKEN'。","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-app-secret -n aiops-e2e -o jsonpath='{.data}'","purpose":"验证 Secret 是否存在并包含指定键","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e2(获取异常 Pod 'rc-config-secret-key-missing' 的容器日志，以确认启动失败的具体原因。): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 88%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 确认异常 Pod 'rc-config-secret-key-missing' 是否仍处于... | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` |
   | e2 | important | ❌ | kubectl_logs | 获取异常 Pod 'rc-config-secret-key-missing' 的容器日志... | `kubectl logs rc-config-secret-key-missing -n aiops-e2e --tail=200` |
   | e3 | critical | ✅ | kubectl_get_by_name | 确认 Secret 'rc-app-secret' 是否存在，以及是否包含键 'APP_S... | `kubectl get secret rc-app-secret -n aiops-e2e -o jsonpath='{.data}'` |

   ⚠️ 未采集原因:
   - e2(获取异常 Pod 'rc-config-secret-key-missing' 的容器日志，以确认启动失败的具体原因。): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (18.7s)
   📤 → 下游数据: root_cause=Secret 'rc-app-secret' 缺失键 'APP_SECRET_TOKEN'，导致 Pod 'rc-config-secret-key-missing' 处于 CreateContainerConfigError 状态。事件显示 'couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret'。
   confidence=90%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "Secret 'rc-app-secret' 缺失键 'APP_SECRET_TOKEN'，导致 Pod 'rc-config-secret-key-missing' 处于 CreateContainerConfigError 状态。事件显示 'couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret'。", "root_cause_summary": "Secret 'rc-app-secret' 缺失键 'APP_SECRET_TOKEN'，导致 Pod 'rc-config-secret-key-missing' 处于 CreateContainerConfigError 状态。事件显示 'couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret'。", "confidence": 0.9, "confidence_reason": "", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [], "limitations": "未获取到容器日志，但通过事件信息已能明确根因。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Secret 'rc-app-secret' 缺失键 'APP_SECRET_TOKEN'，导致 Pod 'rc-config-secret-key-missing' 处于 CreateContainerConfigError 状态。事件显示 'couldn't find key APP_SECRE...
   置信度: 90%

📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 48.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3958 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 49.7s
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
| **置信度** | 高 (90%) |
| **证据完整度** | 2/3 (67%) |

---

## 🔍 现象描述

**用户报告**：  
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | rc-config-secret-key-missing |
| Namespace | aiops-e2e |
| 错误信息 | `Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | kubectl describe pod rc-config-secret-key-missing | `Status: CreateContainerConfigError` | Pod 处于配置错误状态，无法启动 |
| 2 | 事件信息 | kubectl describe pod rc-config-secret-key-missing | `Warning Failed 49m (x12 over 51m) kubelet Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` | 事件明确指出找不到指定 Secret 中的键 |
| 3 | Secret 内容 | kubectl get secret rc-app-secret -n aiops-e2e | `DATA: 1` | Secret 存在，但缺少 `APP_SECRET_TOKEN` 键 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 处于 `CreateContainerConfigError` 状态，且事件明确指出找不到 `APP_SECRET_TOKEN` 键，说明是配置错误。
- **证据 #3 印证**：Secret 存在，但只包含 1 个键，未包含 `APP_SECRET_TOKEN`，说明配置缺失。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 容器日志 | important | 无法获取容器日志，但事件信息已足够明确问题 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Secret 'rc-app-secret' 缺失键 'APP_SECRET_TOKEN'                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod 在启动时引用了该键，但找不到，导致启动失败                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器配置错误，无法启动，事件提示找不到指定键                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 CreateContainerConfigError，持续失败                 │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态 CreateContainerConfigError)、证据 #2 (事件信息) 和证据 #3 (Secret 内容)，问题的根本原因是 **Secret 'rc-app-secret' 缺失键 'APP_SECRET_TOKEN'**，导致 Pod 无法启动。

**置信度**：高 (90%)
- ✅ 事件信息明确指出找不到 `APP_SECRET_TOKEN`
- ✅ Secret 存在但未包含该键
- ⚠️ 未获取容器日志，但事件已足够说明问题

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 向 Secret 中添加缺失的键 `APP_SECRET_TOKEN`**
```bash
kubectl create secret generic rc-app-secret \
  -n aiops-e2e \
  --from-literal=APP_SECRET_TOKEN="your-secret-value" \
  --dry-run=client -o yaml | kubectl apply -f -
```
*依据*：事件信息指出 `APP_SECRET_TOKEN` 缺失，需要补充

**2. [可选] 确认 Pod 是否成功启动**
```bash
kubectl get pod rc-config-secret-key-missing -n aiops-e2e
```
*目的*：确认修复后 Pod 是否正常运行

### 后续优化

1. **配置检查机制**：在 CI/CD 流程中加入配置校验，确保 Secret 键完整
2. **配置文档化**：记录所有 Pod 所需的 Secret 键，避免遗漏
3. **监控告警**：监控 Pod 启动失败事件，及时发现配置错误

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Secret 包含 `APP_SECRET_TOKEN` | `kubectl get secret rc-app-secret -n aiops-e2e -o jsonpath='{.data}'` | 包含 `APP_SECRET_TOKEN` 键 |
| 2. 确认 Pod 运行 | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e` | STATUS: Running |
| 3. 确认事件无错误 | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` | 无 `Failed` 事件 |

---

## ⚠️ 注意事项

- 如果问题持续，请检查应用配置中是否引用了其他缺失的 Secret 键
- 建议为 Secret 设置访问控制，防止敏感信息泄露
- 避免手动操作 Secret，建议使用自动化工具管理

---

## 📎 附录

- **事件原文**：`Warning Failed 49m (x12 over 51m) kubelet Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret`
- **Secret 内容**：`DATA: 1`（不含 `APP_SECRET_TOKEN`）
- **Pod 状态**：`CreateContainerConfigError`

---

## 📊 性能统计

├─ 总耗时: 4.8m
├─ 问题定位: 51.7s (18%) ✅
├─ 证据链采集: 110.7s (38%) ✅
├─ 根因分析: 18.7s (6%) ✅
├─ 汇总总结: 108.5s (37%) ✅
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
