======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 55a50041d14d490a]

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
name: rc-config-secret-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  Failed          9m29s (x12 over 11m)  kubelet            Error: cou
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "ConfigError",
  "confidence": 0.95,
  "reasoning": "Pod rc-config-secret-key-missing 处于 CreateContainerConfigError 状态，Events 明确指出 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret。符合 ConfigError 类型，因为是配置缺失导致容器无法启动。需要进一步确认 Secret aiops-e2e/rc-app-secret 是否存在，以及是否包含 APP_SECRET_TOKEN 键。",
  "abnormal_pods": [
    {
      "name": "rc-config-secret-key-missing",
      "namespace": "aiops-e2e",
      "status": "CreateContainerConfigError",
      "reason": "ConfigError",
      "node": "node1"
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
    "Pod: rc-config-secret-key-missing",
    "Secret: aiops-e2e/rc-app-secret",
    "Key: APP_SECRET_TOKEN"
  ],
  "possible_scenarios": [
    "Secret aiops-e2e/rc-app-secret 不存在",
    "Secret aiops-e2e/rc-app-secret 存在但不包含 APP_SECRET_TOKEN 键",
    "Pod 配置错误地引用了 APP_SECRET_TOKEN，但 Secret 中没有该键"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 8.2s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'Secret aiops-e2e/rc-app-secret 不存在', 'probability': 'High', 'reason': 'Events 明确提示找不到 Secret'}, {'scenario': 'Secret aiops-e2e/rc-app-secret 存在但不包含 APP_SECRET_TOKEN 键', 'probability': 'High', 'reason': 'Events 明确提示找不到 key'}, {'scenario': 'Pod 配置错误地引用了 APP_SECRET_TOKEN，但 Secret 中没有该键', 'probability': 'High', 'reason': 'Events 明确提示找不到 key'}]
   entities=[{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}, {"type": "Key", "name": "APP_SECRET_TOKEN", "namespace": ""}]
   reasoning=Pod rc-config-secret-key-missing 处于 CreateContainerConfigError 状态，Events 明确指出 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret。符合 ConfigError 类型，因为是配置缺失导致容器无法启动。需要进一步确认 Secret aiops-e2e/rc-app-secret 是否存在，以及是否包含 APP_SECRET_TOKEN 键。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "Pod rc-config-secret-key-missing 处于 CreateContainerConfigError 状态，Events 明确指出 Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret。符合 ConfigError 类型，因为是配置缺失导致容器无法启动。需要进一步确认 Secret aiops-e2e/rc-app-secret 是否存在，以及是否包含 APP_SECRET_TOKEN 键。", "abnormal_pods": [{"name": "rc-config-secret-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}], "pod_status_keyword": "CreateContainerConfigError", "pod_abnormal_type": "ConfigError", "status_category": "ConfigError", "key_entities": [{"type": "Pod", "name": "rc-config-secret-key-missing", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-app-secret", "namespace": "aiops-e2e"}, {"type": "Key", "name": "APP_SECRET_TOKEN", "namespace": ""}], "possible_scenarios": [{"scenario": "Secret aiops-e2e/rc-app-secret 不存在", "probability": "High", "reason": "Events 明确提示找不到 Secret"}, {"scenario": "Secret aiops-e2e/rc-app-secret 存在但不包含 APP_SECRET_TOKEN 键", "probability": "High", "reason": "Events 明确提示找不到 key"}, {"scenario": "Pod 配置错误地引用了 APP_SECRET_TOKEN，但 Secret 中没有该键", "probability": "High", "reason": "Events 明确提示找不到 key"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-secret-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-secret-key-missing                        0/1     CreateContainerConfigError   0             11m     172.16.166.188   node1    <none>           <none>            app=rc-config-secret-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/55a50041d14d490a/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/55a50041d14d490a/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/55a50041d14d490a/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME            TYPE     DATA   AGE   LABELS
rc-app-secret   Opaque   1      13m   rootcause-e2e=true
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
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-config-secret-key-missing
namespace: aiops-e2e
creationTimestamp: 2026-05-15T02:31:48Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalize
   💭 [证据链采集] 已采集证据：
1. Secret `rc-app-secret` 存在，但未包含 `APP_SECRET_TOKEN` 键。
2. Pod `rc-config-secret-key-missing` 正确引用了 `APP_SECRET_TOKEN` 键，但因 Secret 缺失该键导致 `CreateContainerConfigError`。

冲突证据：
- Secret `rc-app-secret` 不存在 `APP_SECRET_TOKEN` 键，与 Pod 配置冲突，导致容器无法启动。

未采集证据：
- 无其他未采集证据。

结论：当前异常由 Secret `rc-app-secret` 缺失 `APP_SECRET_TOKEN` 键导致，建议修复 Secret 配置以包含该键。
   ✅ [证据链采集] 完成 (1m 16.3s)
   📤 → 下游数据: evidence_items=5/5
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Secret aiops-e2e/rc-app-secret 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-app-secret -n aiops-e2e","tool_args":{"kind":"Secret","name":"rc-app-secret","namespace":"aiops-e2e"},"purpose":"确认 Secret 是否存在","evidence_type":"existence","target_scope":"aiops-e2e","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e2","description":"验证 Secret aiops-e2e/rc-app-secret 是否包含 APP_SECRET_TOKEN 键","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get secret rc-app-secret -n aiops-e2e -o yaml","tool_args":{"kind":"Secret","name":"rc-app-secret","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"确认 Secret 中是否存在 APP_SECRET_TOKEN 键","evidence_type":"configuration","target_scope":"aiops-e2e","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e3","description":"验证 Pod rc-config-secret-key-missing 的完整配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-config-secret-key-missing","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"确认 Pod 是否正确引用了 APP_SECRET_TOKEN 键","evidence_type":"configuration","target_scope":"aiops-e2e","acceptable_tools":["kubectl_get_yaml"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"NAME            TYPE     DATA   AGE   LABELS\nrc-app-secret   Opaque   1      13m   rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/55a50041d14d490a/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/55a50041d14d490a/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/55a50041d14d490a/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Secret\nname: rc-app-secret\nnamespace: aiops-e2e\ntype: Opaque\ndata_keys: EXISTING_SECRET_KEY\nhas_dockerconfigjson: False\ndocker_secret_type_valid: False","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/55a50041d14d490a/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/55a50041d14d490a/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/55a50041d14d490a/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T02:31:48Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-config-secret-key-missing, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/runbook=pod-config-error.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=CreateContainerConfigError exitCode=None\n  message: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\nvolumes:\n- {\"name\": \"kube-api-access-74hmf\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/55a50041d14d490a/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/55a50041d14d490a/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/55a50041d14d490a/tools/003-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"已采集证据：\n1. Secret `rc-app-secret` 存在，但未包含 `APP_SECRET_TOKEN` 键。\n2. Pod `rc-config-secret-key-missing` 正确引用了 `APP_SECRET_TOKEN` 键，但因 Secret 缺失该键导致 `CreateContainerConfigError`。\n\n冲突证据：\n- Secret `rc-app-secret` 不存在 `APP_SECRET_TOKEN` 键，与 Pod 配置冲突，导致容器无法启动。\n\n未采集证据：\n- 无其他未采集证据。\n\n结论：当前异常由 Secret `rc-app-secret` 缺失 `APP_SECRET_TOKEN` 键导致，建议修复 Secret 配置以包含该键。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 5/5 项，完整度 100%；实际执行工具 5 个，匹配计划 3 个，未规划证据 2 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":5,"environment_evidence_collected":5,"environment_evidence_completeness":1.0,"executed_tool_count":5,"matched_tool_count":3,"unplanned_tool_count":2,"evidence_inventory":[{"id":"e1","description":"验证 Secret aiops-e2e/rc-app-secret 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-app-secret -n aiops-e2e","purpose":"确认 Secret 是否存在","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证 Secret aiops-e2e/rc-app-secret 是否包含 APP_SECRET_TOKEN 键","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get secret rc-app-secret -n aiops-e2e -o yaml","purpose":"确认 Secret 中是否存在 APP_SECRET_TOKEN 键","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"验证 Pod rc-config-secret-key-missing 的完整配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml","purpose":"确认 Pod 是否正确引用了 APP_SECRET_TOKEN 键","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 验证 Secret aiops-e2e/rc-app-secret 是否存在 | `kubectl get secret rc-app-secret -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_yaml | 验证 Secret aiops-e2e/rc-app-secret 是否包含 APP_SE... | `kubectl get secret rc-app-secret -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_get_yaml | 验证 Pod rc-config-secret-key-missing 的完整配置 | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e -o yaml` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (2m 17.0s)
   📤 → 下游数据: root_cause=Secret aiops-e2e/rc-app-secret 缺失 APP_SECRET_TOKEN 键，导致 Pod rc-config-secret-key-missing 无法启动，状态为 CreateContainerConfigError。
   confidence=95%
   causal_chain={"root_cause": "Secret aiops-e2e/rc-app-secret 缺失 APP_SECRET_TOKEN 键", "intermediate_causes": ["Pod rc-config-secret-key-missing 引用了 APP_SECRET_TOKEN 键", "Secret aiops-e2e/rc-app-secret 中未包含 APP_SECRET_TOKEN 键"], "direct_causes": ["Pod rc-config-secret-key-missing 无法找到 APP_SECRET_TOKEN 键", "导致容器启动失败，状态为 CreateContainerConfigError"], "effects": ["Pod rc-config-secret-key-missing 无法启动", "容器状态为 CreateContainerConfigError"]}
   rca_analysis={"phenomenon": "Pod rc-config-secret-key-missing 处于 CreateContainerConfigError 状态，由于无法找到 Secret aiops-e2e/rc-app-secret 中的 APP_SECRET_TOKEN 键导致容器启动失败。", "evidence_inventory": [{"id": "e1", "description": "验证 Secret aiops-e2e/rc-app-secret 是否存在", "value": "NAME            TYPE     DATA   AGE   LABELS\nrc-app-secret   Opaque   1      13m   rootcause-e2e=true"}, {"id": "e2", "description": "验证 Secret aiops-e2e/rc-app-secret 是否包含 APP_SECRET_TOKEN 键", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Secret\nname: rc-app-secret\nnamespace: aiops-e2e\ntype: Opaque\ndata_keys: EXISTING_SECRET_KEY\nhas_dockerconfigjson: False\ndocker_secret_type_valid: False"}, {"id": "e3", "description": "验证 Pod rc-config-secret-key-missing 的完整配置", "value": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T02:31:48Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-config-secret-key-missing, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/runbook=pod-config-error.md\ntolerations_c"}, {"id": "layer_1", "description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS                       RESTARTS      AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     rc-config-secret-key-missing                        0/1     CreateContainerConfigError   0             11m     172.16.166.188   node1    <none>           <none>            app=rc-config-secret-key-miss"}, {"id": "layer_2", "description": "上游已验证工具结果: kubectl_describe", "value": "kubectl_describe 摘要:\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          9m29s (x12 over 11m)  kubelet            Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\n                  cni.projectcalico.org/containerID: 8f443601171b0e4049e100f3c3704966fe0c483b32880bd181c9fc13cf69ec95\n                  cni.projectcalico.org/podIP: 172.16.166.188/32\n                  cni.projectcalico.org/podIPs: 172"}], "evidence_analysis": [{"id": "e1", "description": "验证 Secret aiops-e2e/rc-app-secret 是否存在", "analysis": "Secret aiops-e2e/rc-app-secret 存在，但未包含 APP_SECRET_TOKEN 键。", "raw_data": "NAME            TYPE     DATA   AGE   LABELS\nrc-app-secret   Opaque   1      13m   rootcause-e2e=true"}, {"id": "e2", "description": "验证 Secret aiops-e2e/rc-app-secret 是否包含 APP_SECRET_TOKEN 键", "analysis": "Secret aiops-e2e/rc-app-secret 中未包含 APP_SECRET_TOKEN 键。", "raw_data": "kubectl_get_yaml 关键字段摘要:\nkind: Secret\nname: rc-app-secret\nnamespace: aiops-e2e\ntype: Opaque\ndata_keys: EXISTING_SECRET_KEY\nhas_dockerconfigjson: False\ndocker_secret_type_valid: False"}, {"id": "e3", "description": "验证 Pod rc-config-secret-key-missing 的完整配置", "analysis": "Pod rc-config-secret-key-missing 正确引用了 APP_SECRET_TOKEN 键，但由于 Secret 缺失该键导致 CreateContainerConfigError。", "raw_data": "kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T02:31:48Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-config-secret-key-missing, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/runbook=pod-config-error.md\ntolerations_c"}, {"id": "layer_1", "description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "analysis": "Pod rc-config-secret-key-missing 处于 CreateContainerConfigError 状态，表明容器启动失败。", "raw_data": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS                       RESTARTS      AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     rc-config-secret-key-missing                        0/1     CreateContainerConfigError   0             11m     172.16.166.188   node1    <none>           <none>            app=rc-config-secret-key-miss"}, {"id": "layer_2", "description": "上游已验证工具结果: kubectl_describe", "analysis": "Pod rc-config-secret-key-missing 的事件表明由于无法找到 APP_SECRET_TOKEN 键导致启动失败。", "raw_data": "kubectl_describe 摘要:\nname: rc-config-secret-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  Failed          9m29s (x12 over 11m)  kubelet            Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret\n                  cni.projectcalico.org/containerID: 8f443601171b0e4049e100f3c3704966fe0c483b32880bd181c9fc13cf69ec95\n                  cni.projectcalico.org/podIP: 172.16.166.188/32\n                  cni.projectcalico.org/podIPs: 172"}], "causal_chain": {"root_cause": "Secret aiops-e2e/rc-app-secret 缺失 APP_SECRET_TOKEN 键", "intermediate_causes": ["Pod rc-config-secret-key-missing 引用了 APP_SECRET_TOKEN 键", "Secret aiops-e2e/rc-app-secret 中未包含 APP_SECRET_TOKEN 键"], "direct_causes": ["Pod rc-config-secret-key-missing 无法找到 APP_SECRET_TOKEN 键", "导致容器启动失败，状态为 CreateContainerConfigError"], "effects": ["Pod rc-config-secret-key-missing 无法启动", "容器状态为 CreateContainerConfigError"]}, "root_cause": "Secret aiops-e2e/rc-app-secret 缺失 APP_SECRET_TOKEN 键，导致 Pod rc-config-secret-key-missing 无法启动，状态为 CreateContainerConfigError。", "root_cause_summary": "Secret aiops-e2e/rc-app-secret 缺失 APP_SECRET_TOKEN 键，导致 Pod rc-config-secret-key-missing 无法启动，状态为 CreateContainerConfigError。", "confidence": 0.95, "confidence_reason": "有直接证据表明 Secret aiops-e2e/rc-app-secret 缺失 APP_SECRET_TOKEN 键，因果链清晰。", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [], "limitations": "未验证 Secret aiops-e2e/rc-app-secret 是否在其他命名空间中存在，以及是否存在其他可能的配置错误。", "llm_raw_analysis": "已采集证据：\n1. Secret `rc-app-secret` 存在，但未包含 `APP_SECRET_TOKEN` 键。\n2. Pod `rc-config-secret-key-missing` 正确引用了 `APP_SECRET_TOKEN` 键，但因 Secret 缺失该键导致 `CreateContainerConfigError`。\n\n冲突证据：\n- Secret `rc-app-secret` 不存在 `APP_SECRET_TOKEN` 键，与 Pod 配置冲突，导致容器无法启动。\n\n未采集证据：\n- 无其他未采集证据。\n\n结论：当前异常由 Secret `rc-app-secret` 缺失 `APP_SECRET_TOKEN` 键导致，建议修复 Secret 配置以包含该键。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Secret aiops-e2e/rc-app-secret 缺失 APP_SECRET_TOKEN 键，导致 Pod rc-config-secret-key-missing 无法启动，状态为 CreateContainerConfigError。
   置信度: 95%
   🔗 因果链:
     根本原因: Secret aiops-e2e/rc-app-secret 缺失 APP_SECRET_TOKEN 键


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 4.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3921 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 45.8s
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
| 错误信息 | Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `Status: CreateContainerConfigError` | Pod 无法启动，配置错误 |
| 2 | Pod 事件 | `kubectl describe pod rc-config-secret-key-missing` | `Warning Failed 9m29s (x12 over 11m) kubelet Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret` | 明确指出缺失 APP_SECRET_TOKEN 键 |
| 3 | Secret 内容 | `kubectl get secret rc-app-secret -n aiops-e2e -o yaml` | `data_keys: EXISTING_SECRET_KEY` | Secret 缺失 APP_SECRET_TOKEN 键 |

### 证据关联分析
- **证据 #1 + #2 印证**：Pod 状态为 `CreateContainerConfigError`，且事件明确提示 `APP_SECRET_TOKEN` 键缺失，说明 Pod 配置错误。
- **证据 #3 印证**：Secret `rc-app-secret` 中确实没有 `APP_SECRET_TOKEN` 键，确认了配置缺失的根本原因。

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
│ Secret aiops-e2e/rc-app-secret 缺失 APP_SECRET_TOKEN 键         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod rc-config-secret-key-missing 引用了该键但未找到              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ Error: couldn't find key APP_SECRET_TOKEN in Secret aiops-e2e/rc-app-secret |
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-config-secret-key-missing 状态为 CreateContainerConfigError，持续失败 |
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (Pod 状态为 `CreateContainerConfigError`)、证据 #2 (Pod 事件提示 `APP_SECRET_TOKEN` 键缺失) 和证据 #3 (Secret 中确实没有该键)，问题的根本原因是 **Secret `aiops-e2e/rc-app-secret` 缺失 `APP_SECRET_TOKEN` 键**，导致 Pod 无法启动。
**置信度**：高 (95%)
- ✅ 事件日志明确指出找不到 key
- ✅ Secret 确实没有该 key
- ✅ 无其他干扰因素

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 为 Secret 添加缺失的 `APP_SECRET_TOKEN` 键**
```bash
kubectl create secret generic rc-app-secret \
  -n aiops-e2e \
  --from-literal=APP_SECRET_TOKEN="your_secret_token_value" \
  --dry-run=client -o yaml | kubectl apply -f -
```
*依据*：Pod 配置依赖该 key，必须存在才能启动容器

**2. [验证] 确认 Secret 已更新**
```bash
kubectl get secret rc-app-secret -n aiops-e2e -o yaml
```
*目的*：确认 `APP_SECRET_TOKEN` 键已添加

**3. [重启] 删除异常 Pod 以触发重建**
```bash
kubectl delete pod rc-config-secret-key-missing -n aiops-e2e
```
*目的*：触发控制器重新创建 Pod

### 后续优化
1. **配置校验**：在 CI/CD 流程中加入 Pod 配置校验，避免遗漏关键 Secret 键
2. **文档记录**：记录 Secret 的结构和必需键，便于后续维护
3. **监控告警**：监控 Pod 创建失败事件，及时发现配置问题

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-config-secret-key-missing -n aiops-e2e` | STATUS: Running |
| 2. 检查 Secret 内容 | `kubectl get secret rc-app-secret -n aiops-e2e -o yaml` | 包含 `APP_SECRET_TOKEN` 键 |
| 3. 查看 Pod 事件 | `kubectl describe pod rc-config-secret-key-missing -n aiops-e2e` | 无 `Failed` 事件 |

---

## ⚠️ 注意事项
- 如果 Secret 已存在但键名拼写错误（如 `APP_SECRET_TOKEN` 写成 `APP_SECRET_TOKEN_`），同样会导致此问题
- 如果 Secret 存在于其他命名空间，需使用 `--namespace` 参数指定
- 为保证安全，不要在命令中明文传递敏感值，建议使用文件或加密方式

---

## 📊 性能统计

├─ 总耗时: 5.8m
├─ 问题定位: 68.2s (20%) ✅
├─ 证据链采集: 76.3s (22%) ✅
├─ 根因分析: 137.0s (40%) ✅
├─ 汇总总结: 64.3s (19%) ✅
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
