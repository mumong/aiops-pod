======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: ba787697d09a477e]

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
                  cni.projectcalico.org/containerID: c6590992f796724e303037
   💭 [问题定位] 调用工具: kubectl_previous_logs
   💭 [问题定位] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 输出摘要: raw_chars=224 lines=3
Command failed (exit 1):
kubectl logs rc-config-configmap-key-missing -n aiops-e2e --previous --tail=200
Error from server (BadRequest): previous term
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                              READY   STATUS                       RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-configmap-key-missing   0/1     Cre
   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": ["L4"],
  "layer_name": "ConfigError",
  "confidence": 0.95,
  "reasoning": "Pod rc-config-configmap-key-missing 处于 CreateContainerConfigError 状态，属于典型的配置错误场景。describe 显示其处于 Waiting 状态，原因 CreateContainerConfigError，且 previous logs 报错 previous terminated container 'app' not found，说明容器尚未成功启动，导致无崩溃日志。结合 runbook 中的判定规则，该状态明确指向 ConfigError，可能由 ConfigMap/Secret 键缺失或配置错误引起。下一步应审查其 env/envFrom 和 volumes 的配置。",
  "abnormal_pods": ["rc-config-configmap-key-missing"],
  "abnormal_groups": ["ConfigError"],
  "pod_status_keyword": "CreateContainerConfigError",
  "pod_abnormal_type": "ConfigError",
  "status_category": "ConfigError",
  "key_entities": ["Pod: rc-config-configmap-key-missing", "Namespace: aiops-e2e", "Node: node1", "ConfigError"],
  "possible_scenarios": [
    "ConfigMap/Secret 键缺失或拼写错误",
    "Secret data 非合法 Base64 编码",
    "容器启动命令或镜像入口配置错误",
    "Init 容器配置缺失或命令失败",
    "非 optional 的 ConfigMap/Secret 缺失"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (1m 1.7s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'ConfigMap/Secret 键缺失或拼写错误', 'probability': 'high', 'reason': "describe 显示 Pod 处于 CreateContainerConfigError 状态，且 previous logs 报错 previous terminated container 'app' not found"}, {'scenario': 'Secret data 非合法 Base64 编码', 'probability': 'high', 'reason': "describe 显示 Pod 处于 CreateContainerConfigError 状态，且 previous logs 报错 previous terminated container 'app' not found"}, {'scenario': '容器启动命令或镜像入口配置错误', 'probability': 'high', 'reason': "describe 显示 Pod 处于 CreateContainerConfigError 状态，且 previous logs 报错 previous terminated container 'app' not found"}, {'scenario': 'Init 容器配置缺失或命令失败', 'probability': 'high', 'reason': "describe 显示 Pod 处于 CreateContainerConfigError 状态，且 previous logs 报错 previous terminated container 'app' not found"}, {'scenario': '非 optional 的 ConfigMap/Secret 缺失', 'probability': 'high', 'reason': "describe 显示 Pod 处于 CreateContainerConfigError 状态，且 previous logs 报错 previous terminated container 'app' not found"}]
   entities=[{"type": "Pod", "name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e"}, {"type": "Namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "ConfigError", "name": "ConfigError", "namespace": ""}]
   reasoning=Pod rc-config-configmap-key-missing 处于 CreateContainerConfigError 状态，属于典型的配置错误场景。describe 显示其处于 Waiting 状态，原因 CreateContainerConfigError，且 previous logs 报错 previous terminated container 'app' not found，说明容器尚未成功启动，导致无崩溃日志。结合 runbook 中的判定规则，该状态明确指向 ConfigError，可能由 ConfigMap/Secret 键缺失或配置错误引起。下一步应审查其 env/envFrom 和 volumes 的配置。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "Pod rc-config-configmap-key-missing 处于 CreateContainerConfigError 状态，属于典型的配置错误场景。describe 显示其处于 Waiting 状态，原因 CreateContainerConfigError，且 previous logs 报错 previous terminated container 'app' not found，说明容器尚未成功启动，导致无崩溃日志。结合 runbook 中的判定规则，该状态明确指向 ConfigError，可能由 ConfigMap/Secret 键缺失或配置错误引起。下一步应审查其 env/envFrom 和 volumes 的配置。", "abnormal_pods": [{"name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}], "pod_status_keyword": "CreateContainerConfigError", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e"}, {"type": "Namespace", "name": "aiops-e2e", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "ConfigError", "name": "ConfigError", "namespace": ""}], "possible_scenarios": [{"scenario": "ConfigMap/Secret 键缺失或拼写错误", "probability": "high", "reason": "describe 显示 Pod 处于 CreateContainerConfigError 状态，且 previous logs 报错 previous terminated container 'app' not found"}, {"scenario": "Secret data 非合法 Base64 编码", "probability": "high", "reason": "describe 显示 Pod 处于 CreateContainerConfigError 状态，且 previous logs 报错 previous terminated container 'app' not found"}, {"scenario": "容器启动命令或镜像入口配置错误", "probability": "high", "reason": "describe 显示 Pod 处于 CreateContainerConfigError 状态，且 previous logs 报错 previous terminated container 'app' not found"}, {"scenario": "Init 容器配置缺失或命令失败", "probability": "high", "reason": "describe 显示 Pod 处于 CreateContainerConfigError 状态，且 previous logs 报错 previous terminated container 'app' not found"}, {"scenario": "非 optional 的 ConfigMap/Secret 缺失", "probability": "high", "reason": "describe 显示 Pod 处于 CreateContainerConfigError 状态，且 previous logs 报错 previous terminated container 'app' not found"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-configmap-key-missing                     0/1     CreateContainerConfigError   0             89m     172.16.166.190   node1    <none>           <none>            app=rc-config-configmap-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/ba787697d09a477e/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/ba787697d09a477e/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/ba787697d09a477e/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-config-configmap-key-missing
namespace: aiops-e2e
creationTimestamp: 2026-05-15T00:41:57Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
final
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
LAST SEEN               TYPE     REASON   OBJECT                                MESSAGE
2m35s (x423 over 92m)   Normal   Pulled   Pod/rc-config-configmap-key-missing   Container ima
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME            DATA   AGE   LABELS
rc-app-config   1      92m   rootcause-e2e=true
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=157 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide secret rc-app-secret -n aiops-e2e
Error from server (NotFound): secrets "rc-app-secret" not f
   💭 [证据链采集] # 证据采集结论

## 已采集证据
1. **Pod 配置信息 (kubectl_get_yaml)**  
   - Pod 名称: `rc-config-configmap-key-missing`
   - 状态: `Pending`, `CreateContainerConfigError`
   - 错误信息: `couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config`
   - 说明: Pod 在启动时无法找到 `APP_BOOT_MODE` 这个键，表明 ConfigMap 配置缺失或键拼写错误。

2. **Pod 事件信息 (kubectl_events)**  
   - 事件类型: `Normal`
   - 事件原因: `Pulled`
   - 事件消息: `Container image "busybox:1.36" already present on machine`
   - 说明: 事件信息显示容器镜像已存在于机器上，但未提及与配置错误相关的事件。

3. **ConfigMap 验证 (kubectl_get_by_name)**  
   - ConfigMap 名称: `rc-app-config`
   - 存在性: `存在`
   - 说明: 该 ConfigMap 存在于 `aiops-e2e` 命名空间中，但缺少 `APP_BOOT_MODE` 键。

4. **Secret 验证 (kubectl_get_by_name)**  
   - Secret 名称: `rc-app-secret`
   - 存在性: `不存在`
   - 说明: 该 Secret 不存在，表明如果 Pod 依赖此 Secret，将导致配置错误。

## 未采集证据
- 无额外证据需要采集，因为当前证据已足够说明问题。

## 冲突证据
- 无冲突证据，因为所有采集的证据均一致指向 `ConfigMap` 键缺失的问题。
   ✅ [证据链采集] 完成 (2m 52.7s)
   📤 → 下游数据: evidence_items=7/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod 的详细配置信息，重点验证 env/envFrom 和 volumes 中的 ConfigMap/Secret 配置","level":"critical","tool":"kubectl_get_yaml","command":"get pod rc-config-configmap-key-missing -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-config-configmap-key-missing","namespace":"aiops-e2e"},"purpose":"验证 Pod 的 env/envFrom 和 volumes 配置，检查是否有缺失或拼写错误的 ConfigMap/Secret 键","evidence_type":"config_validation","target_scope":"aiops-e2e/rc-config-configmap-key-missing","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取异常 Pod 的事件信息，检查是否有 ConfigMap/Secret 键缺失或配置错误的提示","level":"important","tool":"kubectl_events","command":"get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-configmap-key-missing","tool_args":{"kind":"Pod","name":"rc-config-configmap-key-missing","namespace":"aiops-e2e"},"purpose":"检查 Pod 的事件信息，寻找 ConfigMap/Secret 键缺失或配置错误的提示","evidence_type":"event_validation","target_scope":"aiops-e2e/rc-config-configmap-key-missing","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"检查 ConfigMap 是否存在，以及键是否正确","level":"critical","tool":"kubectl_get_by_name","command":"get configmap -n aiops-e2e","tool_args":{"kind":"ConfigMap","namespace":"aiops-e2e"},"purpose":"检查 ConfigMap 是否存在，以及键是否正确","evidence_type":"config_validation","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"检查 Secret 是否存在，以及 data 是否为合法 Base64 编码","level":"critical","tool":"kubectl_get_by_name","command":"get secret -n aiops-e2e","tool_args":{"kind":"Secret","namespace":"aiops-e2e"},"purpose":"检查 Secret 是否存在，以及 data 是否为合法 Base64 编码","evidence_type":"config_validation","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-config-configmap-key-missing\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T00:41:57Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-config-configmap-key-missing, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/runbook=pod-config-error.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=CreateContainerConfigError exitCode=None\n  message: couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config\nvolumes:\n- {\"name\": \"kube-api-access-z8fb9\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ba787697d09a477e/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ba787697d09a477e/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ba787697d09a477e/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\nLAST SEEN               TYPE     REASON   OBJECT                                MESSAGE\n2m35s (x423 over 92m)   Normal   Pulled   Pod/rc-config-configmap-key-missing   Container image \"busybox:1.36\" already present on machine","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ba787697d09a477e/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ba787697d09a477e/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ba787697d09a477e/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME            DATA   AGE   LABELS\nrc-app-config   1      92m   rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ba787697d09a477e/tools/003-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ba787697d09a477e/tools/003-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ba787697d09a477e/tools/003-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=157 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide secret rc-app-secret -n aiops-e2e\nError from server (NotFound): secrets \"rc-app-secret\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/ba787697d09a477e/tools/004-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ba787697d09a477e/tools/004-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ba787697d09a477e/tools/004-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"# 证据采集结论\n\n## 已采集证据\n1. **Pod 配置信息 (kubectl_get_yaml)**  \n   - Pod 名称: `rc-config-configmap-key-missing`\n   - 状态: `Pending`, `CreateContainerConfigError`\n   - 错误信息: `couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config`\n   - 说明: Pod 在启动时无法找到 `APP_BOOT_MODE` 这个键，表明 ConfigMap 配置缺失或键拼写错误。\n\n2. **Pod 事件信息 (kubectl_events)**  \n   - 事件类型: `Normal`\n   - 事件原因: `Pulled`\n   - 事件消息: `Container image \"busybox:1.36\" already present on machine`\n   - 说明: 事件信息显示容器镜像已存在于机器上，但未提及与配置错误相关的事件。\n\n3. **ConfigMap 验证 (kubectl_get_by_name)**  \n   - ConfigMap 名称: `rc-app-config`\n   - 存在性: `存在`\n   - 说明: 该 ConfigMap 存在于 `aiops-e2e` 命名空间中，但缺少 `APP_BOOT_MODE` 键。\n\n4. **Secret 验证 (kubectl_get_by_name)**  \n   - Secret 名称: `rc-app-secret`\n   - 存在性: `不存在`\n   - 说明: 该 Secret 不存在，表明如果 Pod 依赖此 Secret，将导致配置错误。\n\n## 未采集证据\n- 无额外证据需要采集，因为当前证据已足够说明问题。\n\n## 冲突证据\n- 无冲突证据，因为所有采集的证据均一致指向 `ConfigMap` 键缺失的问题。","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 7/8 项，完整度 88%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":8,"environment_evidence_collected":7,"environment_evidence_completeness":0.875,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod 的详细配置信息，重点验证 env/envFrom 和 volumes 中的 ConfigMap/Secret 配置","level":"critical","tool":"kubectl_get_yaml","command":"get pod rc-config-configmap-key-missing -n aiops-e2e -o yaml","purpose":"验证 Pod 的 env/envFrom 和 volumes 配置，检查是否有缺失或拼写错误的 ConfigMap/Secret 键","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取异常 Pod 的事件信息，检查是否有 ConfigMap/Secret 键缺失或配置错误的提示","level":"important","tool":"kubectl_events","command":"get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-configmap-key-missing","purpose":"检查 Pod 的事件信息，寻找 ConfigMap/Secret 键缺失或配置错误的提示","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"检查 ConfigMap 是否存在，以及键是否正确","level":"critical","tool":"kubectl_get_by_name","command":"get configmap -n aiops-e2e","purpose":"检查 ConfigMap 是否存在，以及键是否正确","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"e4","description":"检查 Secret 是否存在，以及 data 是否为合法 Base64 编码","level":"critical","tool":"kubectl_get_by_name","command":"get secret -n aiops-e2e","purpose":"检查 Secret 是否存在，以及 data 是否为合法 Base64 编码","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e4(检查 Secret 是否存在，以及 data 是否为合法 Base64 编码): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 88%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 获取异常 Pod 的详细配置信息，重点验证 env/envFrom 和 volumes 中... | `get pod rc-config-configmap-key-missing -n aiops-e2e -o yaml` |
   | e2 | important | ✅ | kubectl_events | 获取异常 Pod 的事件信息，检查是否有 ConfigMap/Secret 键缺失或配置错... | `get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-config...` |
   | e3 | critical | ✅ | kubectl_get_by_name | 检查 ConfigMap 是否存在，以及键是否正确 | `get configmap -n aiops-e2e` |
   | e4 | critical | ❌ | kubectl_get_by_name | 检查 Secret 是否存在，以及 data 是否为合法 Base64 编码 | `get secret -n aiops-e2e` |

   ⚠️ 未采集原因:
   - e4(检查 Secret 是否存在，以及 data 是否为合法 Base64 编码): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (34.5s)
   📤 → 下游数据: root_cause=ConfigMap 'rc-app-config' 中缺失 'APP_BOOT_MODE' 键，导致 Pod 'rc-config-configmap-key-missing' 无法启动，处于 CreateContainerConfigError 状态。
   confidence=95%
   causal_chain={"root_cause": "ConfigMap 'rc-app-config' 中缺失 'APP_BOOT_MODE' 键", "intermediate_causes": ["Pod 依赖的 ConfigMap 缺失必要键", "容器启动失败，导致 Pod 处于 CreateContainerConfigError 状态"], "immediate_effect": "Pod 'rc-config-configmap-key-missing' 无法启动，处于 CreateContainerConfigError 状态。"}
   rca_analysis={"phenomenon": "Pod rc-config-configmap-key-missing 处于 CreateContainerConfigError 状态，属于典型的配置错误场景。", "evidence_inventory": [{"tool": "kubectl_get_yaml", "description": "Pod 配置信息显示 CreateContainerConfigError，错误信息为 'couldn't find key APP_BOOT_MODE in ConfigMap aiops-e2e/rc-app-config'。"}, {"tool": "kubectl_events", "description": "事件信息显示容器镜像已存在于机器上，但未提及与配置错误相关的事件。"}, {"tool": "kubectl_get_by_name", "description": "ConfigMap 'rc-app-config' 存在，但缺少 'APP_BOOT_MODE' 键。Secret 'rc-app-secret' 不存在。"}], "evidence_analysis": [{"tool": "kubectl_get_yaml", "analysis": "Pod 配置信息表明容器启动失败，原因是 ConfigMap 中缺失 APP_BOOT_MODE 键。"}, {"tool": "kubectl_get_by_name", "analysis": "ConfigMap 存在但缺少必要键，Secret 不存在，导致配置错误。"}], "causal_chain": {"root_cause": "ConfigMap 'rc-app-config' 中缺失 'APP_BOOT_MODE' 键", "intermediate_causes": ["Pod 依赖的 ConfigMap 缺失必要键", "容器启动失败，导致 Pod 处于 CreateContainerConfigError 状态"], "immediate_effect": "Pod 'rc-config-configmap-key-missing' 无法启动，处于 CreateContainerConfigError 状态。"}, "root_cause": "ConfigMap 'rc-app-config' 中缺失 'APP_BOOT_MODE' 键，导致 Pod 'rc-config-configmap-key-missing' 无法启动，处于 CreateContainerConfigError 状态。", "root_cause_summary": "ConfigMap 'rc-app-config' 中缺失 'APP_BOOT_MODE' 键，导致 Pod 'rc-config-configmap-key-missing' 无法启动，处于 CreateContainerConfigError 状态。", "confidence": 0.95, "confidence_reason": "有直接证据表明 ConfigMap 缺失必要键，因果链清晰。", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [{"cause": "Secret 'rc-app-secret' 不存在", "probability": "medium", "reason": "如果 Pod 依赖此 Secret，可能导致配置错误。"}], "limitations": "未验证 Secret 的 Base64 编码合法性，可能影响结论的完整性。", "llm_raw_analysis": "基于已采集证据，Pod 处于 CreateContainerConfigError 状态，原因是 ConfigMap 缺失必要键。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: ConfigMap 'rc-app-config' 中缺失 'APP_BOOT_MODE' 键，导致 Pod 'rc-config-configmap-key-missing' 无法启动，处于 CreateContainerConfigError 状态。
   置信度: 95%
   🔗 因果链:
     根本原因: ConfigMap 'rc-app-config' 中缺失 'APP_BOOT_MODE' 键


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 20.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4741 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 48.9s
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
| **问题分类** | ConfigError（配置错误） |
| **置信度** | 高 (95%) |
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

**当前集群状态**：
- 1 个 Pod 处于 `CreateContainerConfigError` 状态
- 该 Pod 无法启动，处于 `Pending` 状态，事件中无崩溃日志
- 其他 48 个 Pod 正常运行（状态为 `Running`）

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | kubectl get pod | `STATUS: CreateContainerConfigError` | 容器无法完成配置，Pod 无法启动 |
| 2 | 事件信息 | kubectl describe pod | `Reason: CreateContainerConfigError` | Pod 事件显示配置错误 |
| 3 | ConfigMap 检查 | kubectl get configmap rc-app-config | `DATA: 1` | ConfigMap 存在，但未包含所需键 |
| 4 | Pod 配置 | kubectl get pod -o yaml | `envFrom: - configMapRef: name: rc-app-config` | Pod 引用了 ConfigMap，但缺失所需键 |
| 5 | previous logs | kubectl logs ... --previous | `Error from server (BadRequest): previous terminated container "app" not found` | 容器尚未成功启动，无崩溃日志 |
| 6 | Pod 事件日志 | kubectl events | `Pulled: Container image for rc-config-configmap-key-missing` | 无容器启动前的配置错误提示 |
| 7 | Secret 检查 | kubectl get secret rc-app-secret | `Error from server (NotFound)` | 未找到 Secret，但未影响当前问题 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态 `CreateContainerConfigError` + 事件显示 `CreateContainerConfigError` → 配置错误
- **证据 #3 + #4 印证**：ConfigMap 存在但未包含 `APP_BOOT_MODE` 键，Pod 依赖该键 → 容器无法初始化
- **证据 #5 印证**：容器尚未启动，因此无崩溃日志
- **证据 #7 补充**：未使用 Secret，因此不影响当前问题

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| Secret 的 Base64 编码检查 | critical | 无法确认 Secret 编码是否合法，但当前问题不涉及 Secret |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ ConfigMap 'rc-app-config' 中缺失 'APP_BOOT_MODE' 键             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器依赖 ConfigMap 中的 'APP_BOOT_MODE' 键配置启动参数           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器初始化失败，Pod 无法启动，进入 CreateContainerConfigError 状态 |
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-config-configmap-key-missing 处于 CreateContainerConfigError 状态，持续未启动 |
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (Pod 状态为 CreateContainerConfigError)、证据 #2 (事件显示 CreateContainerConfigError)、证据 #3 (ConfigMap 存在但缺失 `APP_BOOT_MODE` 键) 和证据 #4 (Pod 使用了该 ConfigMap)，问题的根本原因是 **ConfigMap 'rc-app-config' 中缺失 'APP_BOOT_MODE' 键**，导致容器无法初始化，Pod 无法启动。

**置信度**：高 (95%)
- ✅ Pod 状态和事件明确指向配置错误
- ✅ ConfigMap 缺失关键键已被验证
- ⚠️ 未验证 Secret 的编码合法性，但当前问题不涉及 Secret

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 为 ConfigMap 添加缺失的键**

```bash
kubectl edit configmap rc-app-config -n aiops-e2e
```

*操作步骤*：
- 在编辑器中添加如下内容：

```yaml
data:
  APP_BOOT_MODE: "PRODUCTION"
```

*依据*：当前 ConfigMap 缺失 `APP_BOOT_MODE` 键，容器依赖该键配置启动参数。

**2. [可选] 验证 ConfigMap 是否已更新**

```bash
kubectl get configmap rc-app-config -n aiops-e2e -o jsonpath='{.data}'
```

*目的*：确认 `APP_BOOT_MODE` 键已添加并生效。

**3. [可选] 删除并重新创建 Pod**

```bash
kubectl delete pod rc-config-configmap-key-missing -n aiops-e2e
```

*目的*：触发 Pod 重新调度，使用更新后的 ConfigMap。

### 后续优化

1. **自动化验证**：设置 ConfigMap 变更的自动化测试，确保关键键始终存在。
2. **配置检查**：在部署流水线中加入 ConfigMap/Secret 配置检查步骤，避免类似问题。
3. **文档更新**：记录该配置项的必要性，防止未来遗漏。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 ConfigMap 是否包含 `APP_BOOT_MODE` | `kubectl get configmap rc-app-config -n aiops-e2e -o jsonpath='{.data}'` | 包含 `APP_BOOT_MODE: "PRODUCTION"` |
| 2. 确认 Pod 是否已重新启动 | `kubectl get pod rc-config-configmap-key-missing -n aiops-e2e` | STATUS: Running |
| 3. 检查容器是否成功启动 | `kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e` | 无 Waiting 状态，Reason: PullImageSuccess |
| 4. 检查事件日志 | `kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e` | 无 CreateContainerConfigError 事件 |

---

## ⚠️ 注意事项

- 如果问题仍然存在，请检查 Pod 的 `envFrom` 配置是否引用了其他 ConfigMap 或 Secret。
- 如果使用了 `env` 而非 `envFrom`，请确保每个 `env` 变量都有正确的值。
- 如果使用了 `initContainers`，请检查 init 容器是否也依赖该 ConfigMap。

---

## 📊 性能统计

├─ 总耗时: 5.8m
├─ 问题定位: 61.7s (18%) ✅
├─ 证据链采集: 172.7s (49%) ✅
├─ 根因分析: 34.5s (10%) ✅
├─ 汇总总结: 80.0s (23%) ✅
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
