======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 8824685d2314469f]

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
      📄 kubectl_previous_logs 输出摘要: raw_chars=207 lines=3
Command failed (exit 1):
kubectl logs rc-config-secret-key-missing -n aiops-e2e --previous
Error from server (BadRequest): previous terminated contain
   💭 [问题定位] 调用工具: kubectl_logs
   💭 [问题定位] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 输出摘要: raw_chars=214 lines=3
Command failed (exit 1):
kubectl logs rc-config-secret-key-missing -n aiops-e2e
Error from server (BadRequest): container "app" in pod "rc-config-secret-key-mi
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-config-secret-key-missing
namespace: aiops-e2e
creationTimestamp: 2026-05-15T02:31:48Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalize
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME            TYPE     DATA   AGE   LABELS
rc-app-secret   Opaque   1      47m   rootcause-e2e=true
   💭 [问题定位] 调用工具: kubectl_get_yaml
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (37.7s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'ConfigError - Secret 中缺失 APP_SECRET_TOKEN 键', 'probability': '高', 'reason': "kubectl describe 显示容器配置错误：couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret"}]
   entities=[{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}]
   reasoning=当前环境中的活跃异常对象是 aiops-e2e/rc-config-secret-key-missing，状态为 CreateContainerConfigError，异常类型为 ConfigError。根据 runbook 的判定规则，CreateContainerConfigError + Secret/ConfigMap/env key 缺失属于 ConfigError，归因于 L4 层级。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "application error", "confidence": 0.95, "reasoning": "当前环境中的活跃异常对象是 aiops-e2e/rc-config-secret-key-missing，状态为 CreateContainerConfigError，异常类型为 ConfigError。根据 runbook 的判定规则，CreateContainerConfigError + Secret/ConfigMap/env key 缺失属于 ConfigError，归因于 L4 层级。", "abnormal_pods": [{"name": "rc-config-secret-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}], "pod_status_keyword": "CreateContainerConfigError", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "ConfigError - Secret 中缺失 APP_SECRET_TOKEN 键", "probability": "高", "reason": "kubectl describe 显示容器配置错误：couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-secret-key-missing                        0/1     CreateContainerConfigError   0             47m     172.16.166.188   node1    <none>           <none>            app=rc-config-secret-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/8824685d2314469f/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/8824685d2314469f/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/8824685d2314469f/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          47m (x12 over 49m)    kubelet            Error: cou
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME            TYPE     DATA   AGE   LABELS
rc-app-secret   Opaque   1      49m   rootcause-e2e=true
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
47m (x12 over 49m)      Warning   Failed           Pod/rc-config-secret-key-missing   Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Secret
name: rc-app-secret
namespace: aiops-e2e
type: Opaque
data_keys: EXISTING_SECRET_KEY
has_dockerconfigjson: False
docker_secret_type_valid: False
   💭 [证据链采集] {
  "collected_evidence": [
    {
      "tool": "kubectl_describe",
      "result": "Pod rc-config-secret-key-missing 的状态为 CreateContainerConfigError，关键事件显示 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret。"
    },
    {
      "tool": "kubectl_get_by_name",
      "result": "Secret rc-app-secret 存在，但 DATA 字段显示为 1，表明 APP_SECRET_TOKEN 键缺失。"
    },
    {
      "tool": "kubectl_events",
      "result": "Pod rc-config-secret-key-missing 的事件中显示 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret，表明配置错误。"
    },
    {
      "tool": "kubectl_get_yaml",
      "result": "Secret rc-app-secret 的 data_keys 显示为 EXISTING_SECRET_KEY，而非 APP_SECRET_TOKEN，确认了键缺失。"
    }
  ],
  "un_collected_evidence": [],
  "conflicting_evidence": []
}
   ✅ [证据链采集] 完成 (2m 4.8s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"describe-pod","description":"获取异常 Pod 的详细描述信息，验证配置错误和事件信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","tool_args":{"pod":"rc-config-secret-key-missing","namespace":"aiops-e2e"},"purpose":"确认 Pod 的配置错误和事件信息","evidence_type":"environment","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"get-secret","description":"获取 Secret 的内容，验证 APP_SECRET_TOKEN 是否缺失","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-app-secret -n aiops-e2e","tool_args":{"kind":"Secret","name":"rc-app-secret","namespace":"aiops-e2e"},"purpose":"确认 Secret 中是否存在 APP_SECRET_TOKEN 键","evidence_type":"environment","target_scope":"aiops-e2e/rc-app-secret","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"get-pod-events","description":"获取异常 Pod 的事件信息，验证是否存在配置错误相关的事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-secret-key-missing","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-config-secret-key-missing"},"purpose":"确认 Pod 的事件中是否有配置错误的提示","evidence_type":"environment","target_scope":"aiops-e2e/rc-config-secret-key-missing","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          47m (x12 over 49m)    kubelet            Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\n                  cni.projectcalico.org/containerID: 8f443601171b0e4049e100f3c3704966fe0c483b32880bd181c9fc13cf69ec95\n                  cni.projectcalico.org/podIP: 172.16.166.188/32\n                  cni.projectcalico.org/podIPs: 172.16.166.188/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n      Reason:       CreateContainerConfigError","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8824685d2314469f/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8824685d2314469f/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8824685d2314469f/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME            TYPE     DATA   AGE   LABELS\nrc-app-secret   Opaque   1      49m   rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8824685d2314469f/tools/002-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8824685d2314469f/tools/002-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8824685d2314469f/tools/002-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n47m (x12 over 49m)      Warning   Failed           Pod/rc-config-secret-key-missing   Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8824685d2314469f/tools/003-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8824685d2314469f/tools/003-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8824685d2314469f/tools/003-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Secret\nname: rc-app-secret\nnamespace: aiops-e2e\ntype: Opaque\ndata_keys: EXISTING_SECRET_KEY\nhas_dockerconfigjson: False\ndocker_secret_type_valid: False","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/8824685d2314469f/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/8824685d2314469f/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/8824685d2314469f/tools/004-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"{\n  \"collected_evidence\": [\n    {\n      \"tool\": \"kubectl_describe\",\n      \"result\": \"Pod rc-config-secret-key-missing 的状态为 CreateContainerConfigError，关键事件显示 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret。\"\n    },\n    {\n      \"tool\": \"kubectl_get_by_name\",\n      \"result\": \"Secret rc-app-secret 存在，但 DATA 字段显示为 1，表明 APP_SECRET_TOKEN 键缺失。\"\n    },\n    {\n      \"tool\": \"kubectl_events\",\n      \"result\": \"Pod rc-config-secret-key-missing 的事件中显示 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret，表明配置错误。\"\n    },\n    {\n      \"tool\": \"kubectl_get_yaml\",\n      \"result\": \"Secret rc-app-secret 的 data_keys 显示为 EXISTING_SECRET_KEY，而非 APP_SECRET_TOKEN，确认了键缺失。\"\n    }\n  ],\n  \"un_collected_evidence\": [],\n  \"conflicting_evidence\": []\n}","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 9 个，匹配计划 3 个，未规划证据 6 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":9,"matched_tool_count":3,"unplanned_tool_count":6,"evidence_inventory":[{"id":"describe-pod","description":"获取异常 Pod 的详细描述信息，验证配置错误和事件信息","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-secret-key-missing -n aiops-e2e","purpose":"确认 Pod 的配置错误和事件信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"get-secret","description":"获取 Secret 的内容，验证 APP_SECRET_TOKEN 是否缺失","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-app-secret -n aiops-e2e","purpose":"确认 Secret 中是否存在 APP_SECRET_TOKEN 键","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"get-pod-events","description":"获取异常 Pod 的事件信息，验证是否存在配置错误相关的事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-secret-key-missing","purpose":"确认 Pod 的事件中是否有配置错误的提示","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | describe-pod | critical | ✅ | kubectl_describe | 获取异常 Pod 的详细描述信息，验证配置错误和事件信息 | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` |
   | get-secret | critical | ✅ | kubectl_get_by_name | 获取 Secret 的内容，验证 APP_SECRET_TOKEN 是否缺失 | `kubectl get secret rc-app-secret -n aiops-e2e` |
   | get-pod-events | important | ✅ | kubectl_events | 获取异常 Pod 的事件信息，验证是否存在配置错误相关的事件 | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-confi...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 0.6s)
   📤 → 下游数据: root_cause=Pod aiops-e2e/rc-config-secret-key-missing 无法启动，状态为 CreateContainerConfigError，原因是 Secret aiops-e2e/rc-app-secret 中缺失键 APP_SECRET_TOKEN。
   confidence=95%
   causal_chain={"root_cause": "Secret aiops-e2e/rc-app-secret 中缺失键 APP_SECRET_TOKEN，导致 Pod aiops-e2e/rc-config-secret-key-missing 无法启动。", "intermediate_causes": [{"cause": "Pod aiops-e2e/rc-config-secret-key-missing 配置中引用了 Secret aiops-e2e/rc-app-secret 的键 APP_SECRET_TOKEN。", "evidence": "kubectl_get_yaml 摘要显示 Pod 配置中引用了 Secret aiops-e2e/rc-app-secret。"}, {"cause": "Secret aiops-e2e/rc-app-secret 中不存在键 APP_SECRET_TOKEN。", "evidence": "kubectl_get_yaml 摘要显示 Secret aiops-e2e/rc-app-secret 的 data_keys 显示为 EXISTING_SECRET_KEY，而非 APP_SECRET_TOKEN。"}, {"cause": "Pod aiops-e2e/rc-config-secret-key-missing 无法启动，状态为 CreateContainerConfigError。", "evidence": "kubectl_describe 摘要显示 Pod aiops-e2e/rc-config-secret-key-missing 的状态为 CreateContainerConfigError，关键事件显示 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret。"}], "direct_causes": [{"cause": "Pod aiops-e2e/rc-config-secret-key-missing 无法启动，状态为 CreateContainerConfigError。", "evidence": "kubectl_describe 摘要显示 Pod aiops-e2e/rc-config-secret-key-missing 的状态为 CreateContainerConfigError，关键事件显示 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret。"}]}
   rca_analysis={"phenomenon": "Pod aiops-e2e/rc-config-secret-key-missing 无法启动，状态为 CreateContainerConfigError，原因是配置错误。", "evidence_inventory": [{"tool": "kubectl_describe", "result": "Pod rc-config-secret-key-missing 的状态为 CreateContainerConfigError，关键事件显示 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret。"}, {"tool": "kubectl_get_by_name", "result": "Secret rc-app-secret 存在，但 DATA 字段显示为 1，表明 APP_SECRET_TOKEN 键缺失。"}, {"tool": "kubectl_events", "result": "Pod rc-config-secret-key-missing 的事件中显示 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret，表明配置错误。"}, {"tool": "kubectl_get_yaml", "result": "Secret rc-app-secret 的 data_keys 显示为 EXISTING_SECRET_KEY，而非 APP_SECRET_TOKEN，确认了键缺失。"}], "evidence_analysis": [{"tool": "kubectl_describe", "analysis": "Pod rc-config-secret-key-missing 的状态为 CreateContainerConfigError，关键事件显示 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret。"}, {"tool": "kubectl_get_by_name", "analysis": "Secret rc-app-secret 存在，但 DATA 字段显示为 1，表明 APP_SECRET_TOKEN 键缺失。"}, {"tool": "kubectl_events", "analysis": "Pod rc-config-secret-key-missing 的事件中显示 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret，表明配置错误。"}, {"tool": "kubectl_get_yaml", "analysis": "Secret rc-app-secret 的 data_keys 显示为 EXISTING_SECRET_KEY，而非 APP_SECRET_TOKEN，确认了键缺失。"}], "causal_chain": {"root_cause": "Secret aiops-e2e/rc-app-secret 中缺失键 APP_SECRET_TOKEN，导致 Pod aiops-e2e/rc-config-secret-key-missing 无法启动。", "intermediate_causes": [{"cause": "Pod aiops-e2e/rc-config-secret-key-missing 配置中引用了 Secret aiops-e2e/rc-app-secret 的键 APP_SECRET_TOKEN。", "evidence": "kubectl_get_yaml 摘要显示 Pod 配置中引用了 Secret aiops-e2e/rc-app-secret。"}, {"cause": "Secret aiops-e2e/rc-app-secret 中不存在键 APP_SECRET_TOKEN。", "evidence": "kubectl_get_yaml 摘要显示 Secret aiops-e2e/rc-app-secret 的 data_keys 显示为 EXISTING_SECRET_KEY，而非 APP_SECRET_TOKEN。"}, {"cause": "Pod aiops-e2e/rc-config-secret-key-missing 无法启动，状态为 CreateContainerConfigError。", "evidence": "kubectl_describe 摘要显示 Pod aiops-e2e/rc-config-secret-key-missing 的状态为 CreateContainerConfigError，关键事件显示 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret。"}], "direct_causes": [{"cause": "Pod aiops-e2e/rc-config-secret-key-missing 无法启动，状态为 CreateContainerConfigError。", "evidence": "kubectl_describe 摘要显示 Pod aiops-e2e/rc-config-secret-key-missing 的状态为 CreateContainerConfigError，关键事件显示 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret。"}]}, "root_cause": "Pod aiops-e2e/rc-config-secret-key-missing 无法启动，状态为 CreateContainerConfigError，原因是 Secret aiops-e2e/rc-app-secret 中缺失键 APP_SECRET_TOKEN。", "root_cause_summary": "Pod aiops-e2e/rc-config-secret-key-missing 无法启动，状态为 CreateContainerConfigError，原因是 Secret aiops-e2e/rc-app-secret 中缺失键 APP_SECRET_TOKEN。", "confidence": 0.95, "confidence_reason": "直接证据表明 Secret aiops-e2e/rc-app-secret 中缺失键 APP_SECRET_TOKEN，导致 Pod aiops-e2e/rc-config-secret-key-missing 无法启动。", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [], "limitations": "无", "llm_raw_analysis": "基于提供的证据，Pod aiops-e2e/rc-config-secret-key-missing 无法启动，状态为 CreateContainerConfigError。关键事件显示 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret。Secret aiops-e2e/rc-app-secret 中缺失键 APP_SECRET_TOKEN，导致 Pod 无法启动。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod aiops-e2e/rc-config-secret-key-missing 无法启动，状态为 CreateContainerConfigError，原因是 Secret aiops-e2e/rc-app-secret 中缺失键 APP_SECRET_TOKEN。
   置信度: 95%
   🔗 因果链:
     根本原因: Secret aiops-e2e/rc-app-secret 中缺失键 APP_SECRET_TOKEN，导致 Pod aiops-e2e/rc-config-secret-key-missing 无法启动。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 1.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3699 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 44.4s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
## 📊 诊断概览
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
| Pod | rc-config-secret-key-missing |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: CreateContainerConfigError` | Pod 无法启动 |
| 2 | Pod 事件 | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` | `Warning  Failed  kubelet  Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` | 容器启动失败，缺少配置密钥 |
| 3 | Secret 内容 | `kubectl get secret rc-app-secret -n aiops-e2e` | `data_keys: EXISTING_SECRET_KEY` | Secret 中缺失 `APP_SECRET_TOKEN` 键 |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 状态为 `CreateContainerConfigError`，且事件信息明确指出 `APP_SECRET_TOKEN` 键缺失。
- **证据 #2 + #3 印证**：Secret 中确实没有 `APP_SECRET_TOKEN` 键，导致容器无法启动。

### 缺失证据
无

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Secret aiops-e2e/rc-app-secret 中缺失 APP_SECRET_TOKEN 键         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器启动时尝试读取 APP_SECRET_TOKEN 键，但未找到                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动失败，Pod 状态为 CreateContainerConfigError             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-config-secret-key-missing 无法启动，状态为 CreateContainerConfigError |
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1（Pod 状态为 CreateContainerConfigError）、证据 #2（Pod 事件中提示缺少 APP_SECRET_TOKEN）和证据 #3（Secret 中确实没有 APP_SECRET_TOKEN 键），问题的根本原因是 **Secret aiops-e2e/rc-app-secret 中缺失键 APP_SECRET_TOKEN**，导致容器无法启动，Pod 持续处于 `CreateContainerConfigError` 状态。
**置信度**：高 (95%)
- ✅ Pod 状态和事件明确指向配置错误
- ✅ Secret 内容验证确认了键缺失

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 在 Secret 中添加缺失的 APP_SECRET_TOKEN 键**
```bash
kubectl edit secret rc-app-secret -n aiops-e2e
```
*操作步骤*：
1. 进入编辑模式后，添加如下内容：
   ```yaml
   data:
     APP_SECRET_TOKEN: <base64-encoded-value>
   ```
2. 保存并退出。

*依据*：事件信息明确提示缺少此键，添加后容器可正常启动。

**2. [可选] 重新启动 Pod**
```bash
kubectl delete pod rc-config-secret-key-missing -n aiops-e2e
```
*目的*：删除当前异常 Pod，Kubernetes 会自动重建。

### 后续优化
1. **配置验证**：在部署前使用 `kubectl apply --dry-run=client -o yaml` 验证配置是否完整。
2. **自动化检查**：在 CI/CD 流程中加入 Secret 键完整性检查。
3. **文档记录**：确保配置文档中包含所有必要的 Secret 键。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e` | STATUS: Running |
| 2. 检查 Secret 内容 | `kubectl get secret rc-app-secret -n aiops-e2e -o jsonpath='{.data}'` | 包含 `APP_SECRET_TOKEN` 键 |
| 3. 查看 Pod 事件 | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` | 无 Failed 事件 |

---

## ⚠️ 注意事项
- 如果添加的 Secret 键未正确编码为 base64，Pod 仍会启动失败。
- 确保 Secret 中的键名与容器中引用的环境变量名一致。
- 如果问题持续，请检查容器的环境变量配置是否正确引用了 Secret 键。

---

## 📊 性能统计

├─ 总耗时: 4.7m
├─ 问题定位: 37.7s (13%) ✅
├─ 证据链采集: 124.8s (44%) ✅
├─ 根因分析: 60.6s (21%) ✅
├─ 汇总总结: 61.3s (22%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 12 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 12 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
