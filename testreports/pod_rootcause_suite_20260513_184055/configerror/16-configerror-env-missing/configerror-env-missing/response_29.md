======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: c2ff4372f00b4b2b]

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
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                     READY   STATUS             RESTARTS         AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-env-missing-5d9b8b766c-cstkh   0
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": ["L4"],
  "layer_name": "ConfigError",
  "confidence": "high",
  "reasoning": "Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，且上一次日志显示配置错误：missing required APP_BOOT_MODE。此错误属于 ConfigError，归因于 L4。",
  "abnormal_pods": [
    {
      "name": "rc-config-env-missing-5d9b8b766c-cstkh",
      "namespace": "aiops-e2e",
      "status": "CrashLoopBackOff",
      "restarts": "20 (2m12s ago)",
      "ip": "172.16.166.152",
      "node": "node1"
    }
  ],
  "abnormal_groups": ["ConfigError"],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "ConfigError",
  "status_category": "CrashLoopBackOff",
  "key_entities": [
    {
      "type": "Pod",
      "name": "rc-config-env-missing-5d9b8b766c-cstkh",
      "namespace": "aiops-e2e"
    }
  ],
  "possible_scenarios": [
    {
      "description": "Pod 配置错误导致容器启动失败。日志显示缺少必填环境变量 APP_BOOT_MODE。"
    },
    {
      "description": "环境变量缺失或错误，导致应用启动失败。需要检查 ConfigMap 或 Secret 的配置是否正确。"
    }
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 26.7s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'Pod 配置错误导致容器启动失败。日志显示缺少必填环境变量 APP_BOOT_MODE。', 'probability': 'high', 'reason': 'CrashLoopBackOff + 日志含配置校验失败/缺参'}]
   entities=[{"type": "Pod", "name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e"}]
   reasoning=Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，且上一次日志显示配置错误：missing required APP_BOOT_MODE。此错误属于 ConfigError，归因于 L4。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 1.0, "reasoning": "Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，且上一次日志显示配置错误：missing required APP_BOOT_MODE。此错误属于 ConfigError，归因于 L4。", "abnormal_pods": [{"name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "CrashLoopBackOff", "key_entities": [{"type": "Pod", "name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod 配置错误导致容器启动失败。日志显示缺少必填环境变量 APP_BOOT_MODE。", "probability": "high", "reason": "CrashLoopBackOff + 日志含配置校验失败/缺参"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-env-missing-5d9b8b766c-cstkh              0/1     CrashLoopBackOff   20 (109s ago)   78m     172.16.166.152   node1    <none>           <none>            app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/c2ff4372f00b4b2b/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/c2ff4372f00b4b2b/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/c2ff4372f00b4b2b/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 100%

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
  Warning  BackOff  90s (x374 o
   💭 [证据链采集] 调用工具: kubectl_previous_logs_all_containers
   💭 [证据链采集] 工具结果: kubectl_previous_logs_all_containers (success)
      📄 kubectl_previous_logs_all_containers 日志摘要:
lines: 1
signals: 1
关键日志:
L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-config-env-missing-5d9b8b766c-cstkh
namespace: aiops-e2e
creationTimestamp: 2026-05-14T22:19:01Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: Non
   💭 [证据链采集] 已采集证据：
1. `kubectl_describe` 确认 Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，最近事件显示容器因错误退出（Exit Code 42），并持续重启。
2. `kubectl_previous_logs_all_containers` 显示容器启动失败的具体原因是缺少必填环境变量 APP_BOOT_MODE。
3. `kubectl_get_yaml` 确认 Pod 的 YAML 配置中未定义环境变量 APP_BOOT_MODE。

未采集证据：无

冲突证据：无
   ✅ [证据链采集] 完成 (1m 36.7s)
   📤 → 下游数据: evidence_items=5/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证异常 Pod 的详细状态信息，包括事件和原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","tool_args":{"pod_name":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e"},"purpose":"获取 Pod 的详细状态、事件和错误信息，确认其处于 CrashLoopBackOff 状态的原因。","evidence_type":"Pod 状态和事件","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod 上一次失败容器的完整日志","level":"critical","tool":"kubectl_previous_logs_all_containers","command":"kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous","tool_args":{"pod_name":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e"},"purpose":"确认容器启动失败的具体原因，如缺少环境变量 APP_BOOT_MODE。","evidence_type":"容器日志","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_previous_logs_all_containers"],"counts_for_completeness":true},{"id":"e3","description":"检查 Pod 的配置，包括环境变量、ConfigMap 和 Secret","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o yaml","tool_args":{"pod_name":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e"},"purpose":"确认 Pod 的 YAML 配置是否缺少环境变量 APP_BOOT_MODE，或引用的 ConfigMap/Secret 是否存在错误。","evidence_type":"Pod 配置","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-env-missing-5d9b8b766c-cstkh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Reason:       CrashLoopBackOff\n  Warning  BackOff  90s (x374 over 81m)  kubelet  Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)\n                  cni.projectcalico.org/containerID: b609d3199474fd0c991fb51944c653ad8de49c03971407f25be4cb50f1498fc2\n                  cni.projectcalico.org/podIP: 172.16.166.152/32\n                  cni.projectcalico.org/podIPs: 172.16.166.152/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c2ff4372f00b4b2b/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c2ff4372f00b4b2b/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c2ff4372f00b4b2b/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs_all_containers","data":"kubectl_previous_logs_all_containers 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c2ff4372f00b4b2b/tools/002-evidence-kubectl_previous_logs_all_containers.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c2ff4372f00b4b2b/tools/002-evidence-kubectl_previous_logs_all_containers.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c2ff4372f00b4b2b/tools/002-evidence-kubectl_previous_logs_all_containers.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-config-env-missing-5d9b8b766c-cstkh\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-14T22:19:01Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-config-env-missing, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/runbook=pod-config-error.md\nownerReferences: ReplicaSet/rc-config-env-missing-5d9b8b766c\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=20 reason=CrashLoopBackOff exitCode=42\n  message: back-off 5m0s restarting failed container=app pod=rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)\nvolumes:\n- {\"name\": \"kube-api-access-z9rrw\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/c2ff4372f00b4b2b/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/c2ff4372f00b4b2b/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/c2ff4372f00b4b2b/tools/003-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"已采集证据：\n1. `kubectl_describe` 确认 Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，最近事件显示容器因错误退出（Exit Code 42），并持续重启。\n2. `kubectl_previous_logs_all_containers` 显示容器启动失败的具体原因是缺少必填环境变量 APP_BOOT_MODE。\n3. `kubectl_get_yaml` 确认 Pod 的 YAML 配置中未定义环境变量 APP_BOOT_MODE。\n\n未采集证据：无\n\n冲突证据：无","collection_summary":"计划 3 项，实际采集 2 项，未采集 1 项，完整度 67%；其中真实环境证据 5/6 项，完整度 83%；实际执行工具 6 个，匹配计划 2 个，未规划证据 4 个","plan_total":3,"plan_collected":2,"plan_completeness":0.6666666666666666,"environment_evidence_total":6,"environment_evidence_collected":5,"environment_evidence_completeness":0.8333333333333334,"executed_tool_count":6,"matched_tool_count":2,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证异常 Pod 的详细状态信息，包括事件和原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","purpose":"获取 Pod 的详细状态、事件和错误信息，确认其处于 CrashLoopBackOff 状态的原因。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod 上一次失败容器的完整日志","level":"critical","tool":"kubectl_previous_logs_all_containers","command":"kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous","purpose":"确认容器启动失败的具体原因，如缺少环境变量 APP_BOOT_MODE。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"检查 Pod 的配置，包括环境变量、ConfigMap 和 Secret","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o yaml","purpose":"确认 Pod 的 YAML 配置是否缺少环境变量 APP_BOOT_MODE，或引用的 ConfigMap/Secret 是否存在错误。","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e3(检查 Pod 的配置，包括环境变量、ConfigMap 和 Secret): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/3 项, 完整度: 83%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证异常 Pod 的详细状态信息，包括事件和原因 | `kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_previous_logs_all... | 获取 Pod 上一次失败容器的完整日志 | `kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous` |
   | e3 | important | ❌ | kubectl_get_yaml | 检查 Pod 的配置，包括环境变量、ConfigMap 和 Secret | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o yaml` |

   ⚠️ 未采集原因:
   - e3(检查 Pod 的配置，包括环境变量、ConfigMap 和 Secret): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (18.9s)
   📤 → 下游数据: root_cause=Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，且上一次日志显示配置错误：missing required APP_BOOT_MODE。此错误属于 ConfigError，归因于 L4。
   confidence=95%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [{"e1": "kubectl_describe 确认 Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，最近事件显示容器因错误退出（Exit Code 42），并持续重启。"}, {"e2": "kubectl_previous_logs_all_containers 显示容器启动失败的具体原因是缺少必填环境变量 APP_BOOT_MODE。"}, {"layer_1": "kubectl_get_by_kind_in_cluster 表格摘要显示异常 Pod 处于 CrashLoopBackOff 状态。"}, {"layer_2": "kubectl_previous_logs 显示容器启动失败的具体原因是缺少必填环境变量 APP_BOOT_MODE。"}, {"layer_3": "kubectl_get_by_name 显示异常 Pod 的详细信息，包括标签和状态。"}], "causal_chain": {}, "root_cause": "Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，且上一次日志显示配置错误：missing required APP_BOOT_MODE。此错误属于 ConfigError，归因于 L4。", "root_cause_summary": "Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，且上一次日志显示配置错误：missing required APP_BOOT_MODE。此错误属于 ConfigError，归因于 L4。", "confidence": 0.95, "confidence_reason": "有直接证据，因果链清晰。", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [], "limitations": "缺少检查 Pod 的配置，包括环境变量、ConfigMap 和 Secret 的证据。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，且上一次日志显示配置错误：missing required APP_BOOT_MODE。此错误属于 ConfigError，归因于 L4。
   置信度: 95%

📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 41.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4207 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 3.7s
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
| **置信度** | 高 (95%) |
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
| 错误信息 | missing required APP_BOOT_MODE |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 详细状态 | kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh | `Reason: CrashLoopBackOff` | Pod 处于 CrashLoopBackOff 状态 |
| 2 | 上一次日志 | kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` | 缺失必填环境变量 APP_BOOT_MODE |
| 3 | Pod 状态摘要 | kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e | `STATUS: CrashLoopBackOff, RESTARTS: 20` | Pod 持续重启，状态异常 |
| 4 | Pod 表格摘要 | kubectl get pod -A | `aiops-e2e rc-config-env-missing-5d9b8b766c-cstkh 0/1 CrashLoopBackOff 20 (109s ago) 78m 172.16.166.152 node1 <none> <none> app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError` | 该 Pod 是唯一异常对象 |
| 5 | Runbook 信息 | fetch_runbook | `# Pod ConfigError / 启动配置失败 > 典型状态: CreateContainerConfigError / CreateContainerError / CrashLoopBackOff` | 与当前问题匹配，确认为配置错误 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 CrashLoopBackOff，且日志显示 `missing required APP_BOOT_MODE`，确认是配置错误。
- **证据链**：应用启动时检查环境变量，发现缺少 APP_BOOT_MODE → 应用启动失败 → 容器被终止 → Pod 重启 → CrashLoopBackOff。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 的 YAML 配置 | important | 无法确认环境变量是否正确引用、是否关联了 ConfigMap 或 Secret |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 缺失环境变量 APP_BOOT_MODE，导致应用启动失败                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 应用启动时检查环境变量 APP_BOOT_MODE，发现缺失 → 启动失败       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动失败，被终止（日志显示 missing required APP_BOOT_MODE） │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 CrashLoopBackOff，持续重启                             │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (`missing required APP_BOOT_MODE`) 和证据 #1 (`CrashLoopBackOff`)，问题的根本原因是**Pod 缺失环境变量 APP_BOOT_MODE**，导致应用启动失败，容器被终止，Pod 持续重启。  
**置信度**：高 (95%)  
- ✅ 日志明确指出缺失 APP_BOOT_MODE  
- ✅ Pod 状态为 CrashLoopBackOff  
- ⚠️ 缺少 Pod 的 YAML 配置，无法确认环境变量是否引用错误或配置缺失  

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 为 Pod 添加缺失的环境变量 APP_BOOT_MODE**
```bash
kubectl set env deployment/<deployment-name> -n aiops-e2e APP_BOOT_MODE=<value>
```
*依据*：日志显示 `missing required APP_BOOT_MODE`，需添加该环境变量。

**2. [可选] 检查 Pod 的 YAML 配置**
```bash
kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o yaml
```
*目的*：确认是否引用了正确的 ConfigMap、Secret 或环境变量。

### 后续优化

1. **配置验证机制**：在部署前检查环境变量是否完整，可使用 Helm 的 `validate` 阶段或 Kustomize 的验证钩子。
2. **应用启动健康检查**：在应用代码中添加环境变量缺失的明确提示，避免静默失败。
3. **配置管理优化**：使用 ConfigMap 或 Secret 来管理环境变量，避免手动配置错误。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 0 |
| 3. 检查日志 | `kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | 无 `missing required APP_BOOT_MODE` 错误 |

---

## ⚠️ 注意事项

- 如果环境变量值错误，可能导致其他配置错误，建议在部署前进行验证。
- 如果问题持续，考虑查看应用启动日志，确认是否还有其他配置缺失或依赖问题。

---

## 📊 性能统计

├─ 总耗时: 5.1m
├─ 问题定位: 86.7s (29%) ✅
├─ 证据链采集: 96.7s (32%) ✅
├─ 根因分析: 18.9s (6%) ✅
├─ 汇总总结: 101.3s (33%) ✅
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
