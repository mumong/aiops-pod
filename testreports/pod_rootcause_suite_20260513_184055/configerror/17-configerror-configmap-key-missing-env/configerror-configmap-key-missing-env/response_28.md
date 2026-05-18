======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: ecbbdfd20bb24d9d]

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
      📄 NAME                              READY   STATUS                       RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-configmap-key-missing   0/1     Cre
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 输出摘要: raw_chars=213 lines=3
Command failed (exit 1):
kubectl logs rc-config-configmap-key-missing -n aiops-e2e --previous
Error from server (BadRequest): previous terminated cont
   💭 [问题定位] 调用工具: kubectl_logs
   💭 [问题定位] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 输出摘要: raw_chars=220 lines=3
Command failed (exit 1):
kubectl logs rc-config-configmap-key-missing -n aiops-e2e
Error from server (BadRequest): container "app" in pod "rc-config-configmap-
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-configmap-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          52m (x12 over 54m)     kubelet            Error:
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME            DATA   AGE   LABELS
rc-app-config   1      54m   rootcause-e2e=true
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (36.7s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'Pod 配置错误导致容器启动失败', 'probability': '高', 'reason': 'Pod 状态为 CreateContainerConfigError，且事件中提示找不到 ConfigMap 中的键 APP_BOOT_MODE。'}, {'scenario': 'ConfigMap 键名拼写错误或缺失', 'probability': '高', 'reason': 'ConfigMap rc-app-config 中缺少必要的键 APP_BOOT_MODE，导致容器无法正常启动。'}]
   entities=[{"type": "Pod", "name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-app-config", "namespace": "aiops-e2e"}]
   reasoning=当前环境中的活跃异常对象是 Pod rc-config-configmap-key-missing，其状态为 CreateContainerConfigError，归一化异常类型为 ConfigError。根据分析文本和 runbook 判定规则，这属于 L4 层级的异常，涉及应用配置错误。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "L4", "confidence": 0.5, "reasoning": "当前环境中的活跃异常对象是 Pod rc-config-configmap-key-missing，其状态为 CreateContainerConfigError，归一化异常类型为 ConfigError。根据分析文本和 runbook 判定规则，这属于 L4 层级的异常，涉及应用配置错误。", "abnormal_pods": [{"name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}], "pod_status_keyword": "CreateContainerConfigError", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-app-config", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod 配置错误导致容器启动失败", "probability": "高", "reason": "Pod 状态为 CreateContainerConfigError，且事件中提示找不到 ConfigMap 中的键 APP_BOOT_MODE。"}, {"scenario": "ConfigMap 键名拼写错误或缺失", "probability": "高", "reason": "ConfigMap rc-app-config 中缺少必要的键 APP_BOOT_MODE，导致容器无法正常启动。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-configmap-key-missing                     0/1     CreateContainerConfigError   0             54m     172.16.166.190   node1    <none>           <none>            app=rc-config-configmap-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/ecbbdfd20bb24d9d/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/ecbbdfd20bb24d9d/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/ecbbdfd20bb24d9d/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 50%

📍 [证据链采集] 执行中...
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
  Warning  Failed          53m (x12 over 55m)   kubelet            Error: c
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME            DATA   AGE   LABELS
rc-app-config   1      55m   rootcause-e2e=true
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: ConfigMap
name: rc-app-config
namespace: aiops-e2e
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\"EXISTING_KEY\":\"present\"}", "stderr": "", "returncode": 0}
   💭 [证据链采集] # 证据结论

### 已采集证据
1. **Pod 详细信息**（通过 `kubectl describe pod`）：
   - Pod 名称：`rc-config-configmap-key-missing`
   - 命名空间：`aiops-e2e`
   - 状态：`Pending`
   - 事件：`Warning Failed: Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config`
   - 原因：`CreateContainerConfigError`

2. **ConfigMap 信息**（通过 `kubectl get configmap`）：
   - ConfigMap 名称：`rc-app-config`
   - 命名空间：`aiops-e2e`
   - 数据字段数量：`1`
   - 年龄：`55m`
   - 标签：`rootcause-e2e=true`

3. **ConfigMap 内容**（通过 `kubectl get configmap -o jsonpath`）：
   - ConfigMap 中包含的键：`EXISTING_KEY`
   - 未找到键 `APP_BOOT_MODE`，确认该键缺失。

### 未采集证据
- 无

### 冲突证据
- 无

### 结论
- Pod `rc-config-configmap-key-missing` 因为 `APP_BOOT_MODE` 键缺失导致 `CreateContainerConfigError`。
- ConfigMap `rc-app-config` 确实缺失了 `APP_BOOT_MODE` 键。
   ✅ [证据链采集] 完成 (1m 12.6s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod rc-config-configmap-key-missing 的详细状态和事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e","tool_args":{"pod":"rc-config-configmap-key-missing","namespace":"aiops-e2e"},"purpose":"获取 Pod rc-config-configmap-key-missing 的详细信息，包括事件和状态，以确认 CreateContainerConfigError 的具体原因。","evidence_type":"state_event","target_scope":"aiops-e2e/rc-config-configmap-key-missing","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"验证 ConfigMap rc-app-config 的内容","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-app-config -n aiops-e2e -o yaml","tool_args":{"kind":"ConfigMap","name":"rc-app-config","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"获取 ConfigMap rc-app-config 的内容，验证其是否包含所需的键 APP_BOOT_MODE。","evidence_type":"resource_config","target_scope":"aiops-e2e/rc-app-config","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-configmap-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          53m (x12 over 55m)   kubelet            Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config\n                  cni.projectcalico.org/containerID: c6590992f796724e3030377c35b95ac5cd9bd85454ecc2614551beb8d64aa785\n                  cni.projectcalico.org/podIP: 172.16.166.190/32\n                  cni.projectcalico.org/podIPs: 172.16.166.190/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n      Reason:       CreateContainerConfigError","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ecbbdfd20bb24d9d/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ecbbdfd20bb24d9d/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ecbbdfd20bb24d9d/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME            DATA   AGE   LABELS\nrc-app-config   1      55m   rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ecbbdfd20bb24d9d/tools/002-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ecbbdfd20bb24d9d/tools/002-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ecbbdfd20bb24d9d/tools/002-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: ConfigMap\nname: rc-app-config\nnamespace: aiops-e2e","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ecbbdfd20bb24d9d/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ecbbdfd20bb24d9d/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ecbbdfd20bb24d9d/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\\"EXISTING_KEY\\\":\\\"present\\\"}\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ecbbdfd20bb24d9d/tools/004-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ecbbdfd20bb24d9d/tools/004-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ecbbdfd20bb24d9d/tools/004-evidence-run_bash_command.summary.txt"}],"llm_analysis":"# 证据结论\n\n### 已采集证据\n1. **Pod 详细信息**（通过 `kubectl describe pod`）：\n   - Pod 名称：`rc-config-configmap-key-missing`\n   - 命名空间：`aiops-e2e`\n   - 状态：`Pending`\n   - 事件：`Warning Failed: Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config`\n   - 原因：`CreateContainerConfigError`\n\n2. **ConfigMap 信息**（通过 `kubectl get configmap`）：\n   - ConfigMap 名称：`rc-app-config`\n   - 命名空间：`aiops-e2e`\n   - 数据字段数量：`1`\n   - 年龄：`55m`\n   - 标签：`rootcause-e2e=true`\n\n3. **ConfigMap 内容**（通过 `kubectl get configmap -o jsonpath`）：\n   - ConfigMap 中包含的键：`EXISTING_KEY`\n   - 未找到键 `APP_BOOT_MODE`，确认该键缺失。\n\n### 未采集证据\n- 无\n\n### 冲突证据\n- 无\n\n### 结论\n- Pod `rc-config-configmap-key-missing` 因为 `APP_BOOT_MODE` 键缺失导致 `CreateContainerConfigError`。\n- ConfigMap `rc-app-config` 确实缺失了 `APP_BOOT_MODE` 键。","collection_summary":"计划 2 项，实际采集 2 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 9 个，匹配计划 2 个，未规划证据 7 个","plan_total":2,"plan_collected":2,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":9,"matched_tool_count":2,"unplanned_tool_count":7,"evidence_inventory":[{"id":"e1","description":"验证 Pod rc-config-configmap-key-missing 的详细状态和事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e","purpose":"获取 Pod rc-config-configmap-key-missing 的详细信息，包括事件和状态，以确认 CreateContainerConfigError 的具体原因。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证 ConfigMap rc-app-config 的内容","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-app-config -n aiops-e2e -o yaml","purpose":"获取 ConfigMap rc-app-config 的内容，验证其是否包含所需的键 APP_BOOT_MODE。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/2 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod rc-config-configmap-key-missing 的详细状态和事件 | `kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_by_name | 验证 ConfigMap rc-app-config 的内容 | `kubectl get configmap rc-app-config -n aiops-e2e -o yaml` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (1m 17.8s)
   📤 → 下游数据: root_cause=Pod rc-config-configmap-key-missing 因为 ConfigMap rc-app-config 缺失 APP_BOOT_MODE 键导致容器启动失败，状态为 CreateContainerConfigError。
   confidence=90%
   causal_chain={"root_cause": "ConfigMap rc-app-config 缺失 APP_BOOT_MODE 键", "intermediate_causes": ["Pod rc-config-configmap-key-missing 依赖 ConfigMap rc-app-config 中的 APP_BOOT_MODE 键", "APP_BOOT_MODE 键缺失导致容器配置错误"], "immediate_causes": ["Pod rc-config-configmap-key-missing 的容器因配置错误无法启动", "Pod 状态变为 CreateContainerConfigError"]}
   rca_analysis={"phenomenon": "Pod rc-config-configmap-key-missing 因配置错误导致容器启动失败，状态为 CreateContainerConfigError。", "evidence_inventory": [{"e1": "验证 Pod rc-config-configmap-key-missing 的详细状态和事件"}, {"e2": "验证 ConfigMap rc-app-config 的内容"}, {"layer_1": "上游已验证工具结果: kubectl_get_by_kind_in_cluster"}, {"layer_2": "上游已验证工具结果: kubectl_get_by_name"}, {"layer_3": "上游已验证工具结果: kubectl_previous_logs"}, {"layer_4": "上游已验证工具结果: kubectl_logs"}, {"layer_5": "上游已验证工具结果: kubectl_describe"}, {"layer_6": "上游已验证工具结果: kubectl_get_by_name"}], "evidence_analysis": [{"e1": "Pod rc-config-configmap-key-missing 的事件显示 Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config"}, {"e2": "ConfigMap rc-app-config 只包含 1 个键，缺失了 APP_BOOT_MODE"}, {"layer_1": "kubectl_get_by_kind_in_cluster 显示 Pod rc-config-configmap-key-missing 的状态为 CreateContainerConfigError"}, {"layer_2": "kubectl_get_by_name 确认 Pod rc-config-configmap-key-missing 的状态为 CreateContainerConfigError"}, {"layer_3": "kubectl_previous_logs 显示 previous terminated container \"app\" in pod \"rc-config-configmap-key-missing\" not found"}, {"layer_4": "kubectl_logs 显示 container \"app\" in pod \"rc-config-configmap-key-missing\" is waiting to start: CreateContainerConfigError"}, {"layer_5": "kubectl_describe 显示 Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config"}, {"layer_6": "kubectl_get_by_name 显示 ConfigMap rc-app-config 包含 1 个键"}], "causal_chain": {"root_cause": "ConfigMap rc-app-config 缺失 APP_BOOT_MODE 键", "intermediate_causes": ["Pod rc-config-configmap-key-missing 依赖 ConfigMap rc-app-config 中的 APP_BOOT_MODE 键", "APP_BOOT_MODE 键缺失导致容器配置错误"], "immediate_causes": ["Pod rc-config-configmap-key-missing 的容器因配置错误无法启动", "Pod 状态变为 CreateContainerConfigError"]}, "root_cause": "Pod rc-config-configmap-key-missing 因为 ConfigMap rc-app-config 缺失 APP_BOOT_MODE 键导致容器启动失败，状态为 CreateContainerConfigError。", "root_cause_summary": "Pod rc-config-configmap-key-missing 因为 ConfigMap rc-app-config 缺失 APP_BOOT_MODE 键导致容器启动失败，状态为 CreateContainerConfigError。", "confidence": 0.9, "confidence_reason": "直接证据显示 ConfigMap rc-app-config 缺失 APP_BOOT_MODE 键，导致容器配置错误，因果链清晰。", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [], "limitations": "ConfigMap rc-app-config 中的键数量未详细列出，仅确认缺失 APP_BOOT_MODE 键。", "llm_raw_analysis": "基于已采集的证据，确认了以下因果关系：\n1. Pod rc-config-configmap-key-missing 的状态为 CreateContainerConfigError，由 kubectl_get_by_kind_in_cluster 和 kubectl_get_by_name 确认。\n2. kubectl_describe 显示 Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config，表明配置错误。\n3. kubectl_get_by_name 显示 ConfigMap rc-app-config 仅包含 1 个键，缺失了 APP_BOOT_MODE。\n因此，根因是 ConfigMap rc-app-config 缺失 APP_BOOT_MODE 键导致容器配置错误，置信度为 0.9。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-config-configmap-key-missing 因为 ConfigMap rc-app-config 缺失 APP_BOOT_MODE 键导致容器启动失败，状态为 CreateContainerConfigError。
   置信度: 90%
   🔗 因果链:
     根本原因: ConfigMap rc-app-config 缺失 APP_BOOT_MODE 键


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 13.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3887 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 20.9s
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
| **证据完整度** | 2/2 (100%) |

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
| 错误信息 | `Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod rc-config-configmap-key-missing` | `Warning  Failed 52m (x12 over 54m) kubelet Error: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config` | 容器因配置缺失启动失败 |
| 2 | ConfigMap 内容 | `kubectl get configmap rc-app-config -n aiops-e2e -o yaml` | `kind: ConfigMap, name: rc-app-config, data: {"EXISTING_KEY":"present"}` | 缺失键 `APP_BOOT_MODE` |

### 证据关联分析

- **证据 #1 印证**：`Warning Failed` 明确指出 `APP_BOOT_MODE` 键缺失，导致容器配置错误
- **证据链**：容器启动时引用了 `APP_BOOT_MODE` 键 → 但 ConfigMap 中不存在该键 → 容器无法创建 → Pod 状态为 `CreateContainerConfigError`

### 缺失证据（无）

| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | 无 | 无 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ ConfigMap aiops-e2e/rc-app-config 缺失键 APP_BOOT_MODE          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器启动时引用 ConfigMap 中的 APP_BOOT_MODE 键，但未找到         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 创建容器失败（Error: couldn't find key APP_BOOT_MODE）          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-config-configmap-key-missing 状态为 CreateContainerConfigError，持续失败 |
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1（`Warning Failed` 提示 `APP_BOOT_MODE` 未找到）和证据 #2（`ConfigMap` 中仅存在 `EXISTING_KEY`），问题的根本原因是 **ConfigMap `rc-app-config` 缺失关键键 `APP_BOOT_MODE`**，导致容器无法正常启动。

**置信度**：高 (90%)
- ✅ `kubectl describe pod` 明确提示 `APP_BOOT_MODE` 未找到
- ✅ `kubectl get configmap` 显示数据字段缺失
- ✅ 匹配 `pod-config-error.md` 运行手册的典型配置错误场景

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 向 ConfigMap 中添加缺失的键 `APP_BOOT_MODE`**

```bash
kubectl patch configmap rc-app-config -n aiops-e2e --type merge -p '{"data":{"APP_BOOT_MODE":"value"}}'
```

*依据*：容器配置中引用了此键，必须添加其定义

**2. [可选] 重启 Pod 以触发新配置生效**

```bash
kubectl delete pod rc-config-configmap-key-missing -n aiops-e2e
```

*依据*：Kubernetes 会自动重新拉起 Pod 并使用更新后的 ConfigMap

### 后续优化

1. **配置校验自动化**：在 CI/CD 流程中增加 ConfigMap 键完整性校验
2. **配置文档化**：明确记录哪些 ConfigMap 键是必需的
3. **监控告警**：配置 Pod 启动失败告警（如 `PodStatus=CreateContainerConfigError`）

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 ConfigMap 内容 | `kubectl get configmap rc-app-config -n aiops-e2e -o yaml` | 包含 `APP_BOOT_MODE` 键 |
| 2. 确认 Pod 运行 | `kubectl get pod rc-config-configmap-key-missing -n aiops-e2e` | STATUS: Running |
| 3. 确认事件日志 | `kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e` | 无 `Failed` 事件 |

---

## ⚠️ 注意事项

- 如果 Pod 重启后仍失败，请检查容器启动脚本是否还依赖其他未定义的键
- 避免硬编码键名，建议通过 Helm 或 Kustomize 管理 ConfigMap
- 建议使用 ConfigMap 的 `immutable` 字段防止误操作

--- 

## 📎 附件参考

- **诊断上下文归档**：`/tmp/aiops/reports/context_archives/ecbbdfd20bb24d9d/layer/full_analysis.md`
- **Runbook**：`pod-config-error.md`

---

## 📊 性能统计

├─ 总耗时: 4.3m
├─ 问题定位: 36.7s (14%) ✅
├─ 证据链采集: 72.6s (28%) ✅
├─ 根因分析: 77.8s (30%) ✅
├─ 汇总总结: 73.8s (28%) ✅
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
