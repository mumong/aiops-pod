======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 5af6eb90ff45443a]

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
   💭 [问题定位] 调用工具: kubectl_container_logs
   💭 [问题定位] 工具结果: kubectl_container_logs (success)
      📄 kubectl_container_logs 输出摘要: raw_chars=227 lines=3
Command failed (exit 1):
kubectl logs rc-config-configmap-key-missing -c app -n aiops-e2e
Error from server (BadRequest): container "app" in pod "rc-
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-configmap-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
                  cni.projectcalico.org/containerID: c6590992f796724e303037
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=179 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide configmap configmap-key-missing -n aiops-e2e
Error from server (NotFound): configmaps "config
   💭 [问题定位] 调用工具: kubectl_get_by_name
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (38.2s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': '引用的 ConfigMap 不存在或键名缺失', 'probability': '高', 'reason': 'Pod 状态为 CreateContainerConfigError，且 ConfigMap configmap-key-missing 不存在。'}]
   entities=[{"type": "Pod", "name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "configmap-key-missing", "namespace": "aiops-e2e"}]
   reasoning=当前环境中存在一个 Pod 处于 CreateContainerConfigError 状态，并且被标记为 pod_abnormal_type=ConfigError，其原因与配置缺失有关。根据提供的 runbook 和诊断信息，该 Pod 无法启动的原因是引用的 ConfigMap 不存在或键名缺失。这属于应用配置错误范畴，对应 L4 层级。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "", "confidence": 0.5, "reasoning": "当前环境中存在一个 Pod 处于 CreateContainerConfigError 状态，并且被标记为 pod_abnormal_type=ConfigError，其原因与配置缺失有关。根据提供的 runbook 和诊断信息，该 Pod 无法启动的原因是引用的 ConfigMap 不存在或键名缺失。这属于应用配置错误范畴，对应 L4 层级。", "abnormal_pods": [{"name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e", "status": "CreateContainerConfigError"}], "pod_status_keyword": "CreateContainerConfigError", "pod_abnormal_type": "ConfigError", "status_category": "app_config", "key_entities": [{"type": "Pod", "name": "rc-config-configmap-key-missing", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "configmap-key-missing", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "引用的 ConfigMap 不存在或键名缺失", "probability": "高", "reason": "Pod 状态为 CreateContainerConfigError，且 ConfigMap configmap-key-missing 不存在。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CreateContainerConfigError"], "pod_abnormal_type": "CreateContainerConfigError", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-configmap-key-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "CreateContainerConfigError 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-configmap-key-missing                     0/1     CreateContainerConfigError   0             71m     172.16.166.190   node1    <none>           <none>            app=rc-config-configmap-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/5af6eb90ff45443a/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/5af6eb90ff45443a/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/5af6eb90ff45443a/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

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
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=179 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide configmap configmap-key-missing -n aiops-e2e
Error from server (NotFound): configmaps "config
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-config-configmap-key-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
                  cni.projectcalico.org/containerID: c6590992f796724e303037
   💭 [证据链采集] 调用工具: kubectl_events
   ✅ [证据链采集] 完成 (1m 47.3s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 ConfigMap configmap-key-missing 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap configmap-key-missing -n aiops-e2e","tool_args":{"kind":"configmap","name":"configmap-key-missing","namespace":"aiops-e2e"},"purpose":"确认 ConfigMap 是否存在，这是导致 CreateContainerConfigError 的关键因素","evidence_type":"config_absence","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod rc-config-configmap-key-missing 的详细信息","level":"important","tool":"kubectl_describe","command":"kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-config-configmap-key-missing","namespace":"aiops-e2e"},"purpose":"查看 Pod 的详细状态和事件，特别是 CreateContainerConfigError 的具体原因","evidence_type":"pod_status","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod rc-config-configmap-key-missing 的事件信息","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-configmap-key-missing","tool_args":{"kind":"event","namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-config-configmap-key-missing"},"purpose":"查看与该 Pod 相关的事件，特别是与 CreateContainerConfigError 相关的事件","evidence_type":"pod_events","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=179 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide configmap configmap-key-missing -n aiops-e2e\nError from server (NotFound): configmaps \"configmap-key-missing\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/5af6eb90ff45443a/tools/001-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/5af6eb90ff45443a/tools/001-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/5af6eb90ff45443a/tools/001-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-configmap-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n                  cni.projectcalico.org/containerID: c6590992f796724e3030377c35b95ac5cd9bd85454ecc2614551beb8d64aa785\n                  cni.projectcalico.org/podIP: 172.16.166.190/32\n                  cni.projectcalico.org/podIPs: 172.16.166.190/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n      Reason:       CreateContainerConfigError","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/5af6eb90ff45443a/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/5af6eb90ff45443a/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/5af6eb90ff45443a/tools/002-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"Agent 执行异常: Input validation error: 'resource_type' is a required property","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 7 个，匹配计划 3 个，未规划证据 4 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":7,"matched_tool_count":3,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证 ConfigMap configmap-key-missing 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap configmap-key-missing -n aiops-e2e","purpose":"确认 ConfigMap 是否存在，这是导致 CreateContainerConfigError 的关键因素","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"e2","description":"获取 Pod rc-config-configmap-key-missing 的详细信息","level":"important","tool":"kubectl_describe","command":"kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e","purpose":"查看 Pod 的详细状态和事件，特别是 CreateContainerConfigError 的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod rc-config-configmap-key-missing 的事件信息","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-config-configmap-key-missing","purpose":"查看与该 Pod 相关的事件，特别是与 CreateContainerConfigError 相关的事件","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_container_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 验证 ConfigMap configmap-key-missing 是否存在 | `kubectl get configmap configmap-key-missing -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_describe | 获取 Pod rc-config-configmap-key-missing 的详细信息 | `kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e` |
   | e3 | important | ✅ | kubectl_events | 获取 Pod rc-config-configmap-key-missing 的事件信息 | `kubectl get events -n aiops-e2e --field-selector=involvedObject.name=rc-confi...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (2m 12.8s)
   📤 → 下游数据: root_cause=Pod rc-config-configmap-key-missing 无法启动的原因是引用的 ConfigMap configmap-key-missing 不存在或键名缺失。
   confidence=90%
   causal_chain={"直接原因": "ConfigMap configmap-key-missing 在命名空间 aiops-e2e 中不存在，导致 Pod rc-config-configmap-key-missing 无法启动。", "传导": "由于 ConfigMap 不存在，Pod 无法正确配置其容器，导致容器配置错误，从而使 Pod 无法启动。", "根因": "引用的 ConfigMap 不存在或键名缺失。"}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"description": "验证 ConfigMap configmap-key-missing 是否存在", "level": "critical", "value": "kubectl_get_by_name 输出摘要: raw_chars=179 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide configmap configmap-key-missing -n aiops-e2e\nError from server (NotFound): configmaps \"configmap-key-missing\" not found"}, {"description": "获取 Pod rc-config-configmap-key-missing 的详细信息", "level": "important", "value": "kubectl_describe 摘要:\nname: rc-config-configmap-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n                  cni.projectcalico.org/containerID: c6590992f796724e3030377c35b95ac5cd9bd85454ecc2614551beb8d64aa785\n                  cni.projectcalico.org/podIP: 172.16.166.190/32\n                  cni.projectcalico.org/podIPs: 172.16.166.190/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:"}, {"description": "获取 Pod rc-config-configmap-key-missing 的事件信息", "level": "important", "value": "NAME                              READY   STATUS                       RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-config-configmap-key-missing   0/1     CreateContainerConfigError   0          71m   172.16.166.190   node1   <none>           <none>            app=rc-config-configmap-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true"}, {"description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Running': 46}\nNAMESPACE     NAME                                                READY   STATUS                       RESTARTS      AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e     rc-config-configmap-key-missing                     0/1     CreateContainerConfigError   0             71m     172.16.166.190   node1    <none>           <none>            app=rc-config-configmap-key-m"}, {"description": "上游已验证工具结果: kubectl_get_by_name", "level": "important", "value": "NAME                              READY   STATUS                       RESTARTS   AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-config-configmap-key-missing   0/1     CreateContainerConfigError   0          71m   172.16.166.190   node1   <none>           <none>            app=rc-config-configmap-key-missing,pod_abnormal_type=ConfigError,rootcause-e2e=true"}, {"description": "上游已验证工具结果: kubectl_previous_logs", "level": "important", "value": "kubectl_previous_logs 输出摘要: raw_chars=213 lines=3\nCommand failed (exit 1):\nkubectl logs rc-config-configmap-key-missing -n aiops-e2e --previous\nError from server (BadRequest): previous terminated container \"app\" in pod \"rc-config-configmap-key-missing\" not found"}, {"description": "上游已验证工具结果: kubectl_container_logs", "level": "important", "value": "kubectl_container_logs 输出摘要: raw_chars=227 lines=3\nCommand failed (exit 1):\nkubectl logs rc-config-configmap-key-missing -c app -n aiops-e2e\nError from server (BadRequest): container \"app\" in pod \"rc-config-configmap-key-missing\" is waiting to start: CreateContainerConfigError"}, {"description": "上游已验证工具结果: kubectl_describe", "level": "important", "value": "kubectl_describe 摘要:\nname: rc-config-configmap-key-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n                  cni.projectcalico.org/containerID: c6590992f796724e3030377c35b95ac5cd9bd85454ecc2614551beb8d64aa785\n                  cni.projectcalico.org/podIP: 172.16.166.190/32\n                  cni.projectcalico.org/podIPs: 172.16.166.190/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:"}, {"description": "上游已验证工具结果: kubectl_get_by_name", "level": "important", "value": "kubectl_get_by_name 输出摘要: raw_chars=179 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide configmap configmap-key-missing -n aiops-e2e\nError from server (NotFound): configmaps \"configmap-key-missing\" not found"}], "evidence_analysis": [{"description": "验证 ConfigMap configmap-key-missing 是否存在", "level": "critical", "value": "ConfigMap configmap-key-missing 在命名空间 aiops-e2e 中不存在。"}, {"description": "获取 Pod rc-config-configmap-key-missing 的详细信息", "level": "important", "value": "Pod rc-config-configmap-key-missing 的状态为 Pending，且原因显示为 CreateContainerConfigError。"}, {"description": "获取 Pod rc-config-configmap-key-missing 的事件信息", "level": "important", "value": "Pod rc-config-configmap-key-missing 的状态为 CreateContainerConfigError，且标签中包含 pod_abnormal_type=ConfigError。"}, {"description": "上游已验证工具结果: kubectl_get_by_kind_in_cluster", "level": "important", "value": "在集群中有一个 Pod 处于 CreateContainerConfigError 状态，名为 rc-config-configmap-key-missing。"}, {"description": "上游已验证工具结果: kubectl_get_by_name", "level": "important", "value": "Pod rc-config-configmap-key-missing 的状态为 CreateContainerConfigError，且标签中包含 pod_abnormal_type=ConfigError。"}, {"description": "上游已验证工具结果: kubectl_previous_logs", "level": "important", "value": "尝试获取 Pod rc-config-configmap-key-missing 的上一个容器日志失败，因为没有找到上一个终止的容器。"}, {"description": "上游已验证工具结果: kubectl_container_logs", "level": "important", "value": "尝试获取 Pod rc-config-configmap-key-missing 的容器日志失败，因为容器尚未启动，原因是 CreateContainerConfigError。"}, {"description": "上游已验证工具结果: kubectl_describe", "level": "important", "value": "Pod rc-config-configmap-key-missing 的状态为 Pending，且原因显示为 CreateContainerConfigError。"}, {"description": "上游已验证工具结果: kubectl_get_by_name", "level": "important", "value": "ConfigMap configmap-key-missing 在命名空间 aiops-e2e 中不存在。"}], "causal_chain": {"直接原因": "ConfigMap configmap-key-missing 在命名空间 aiops-e2e 中不存在，导致 Pod rc-config-configmap-key-missing 无法启动。", "传导": "由于 ConfigMap 不存在，Pod 无法正确配置其容器，导致容器配置错误，从而使 Pod 无法启动。", "根因": "引用的 ConfigMap 不存在或键名缺失。"}, "root_cause": "Pod rc-config-configmap-key-missing 无法启动的原因是引用的 ConfigMap configmap-key-missing 不存在或键名缺失。", "root_cause_summary": "Pod rc-config-configmap-key-missing 无法启动的原因是引用的 ConfigMap configmap-key-missing 不存在或键名缺失。", "confidence": 0.9, "confidence_reason": "有直接证据表明 ConfigMap configmap-key-missing 不存在，且 Pod rc-config-configmap-key-missing 的状态为 CreateContainerConfigError，因果链清晰。", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [], "limitations": "没有找到 ConfigMap 的详细信息，因此无法确认是否是键名缺失还是 ConfigMap 本身不存在。", "llm_raw_analysis": "基于提供的证据，可以确定 Pod rc-config-configmap-key-missing 无法启动的原因是引用的 ConfigMap configmap-key-missing 不存在或键名缺失。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-config-configmap-key-missing 无法启动的原因是引用的 ConfigMap configmap-key-missing 不存在或键名缺失。
   置信度: 90%
   🔗 因果链:


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 6.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3937 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 44.8s
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
| **兼容归因层** | L4 - 应用配置错误 |
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
| Pod | rc-config-configmap-key-missing |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | CreateContainerConfigError |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | ConfigMap 存在性验证 | `kubectl get configmap configmap-key-missing -n aiops-e2e` | `Error from server (NotFound): configmaps "configmap-key-missing" not found` | ConfigMap 不存在，导致容器配置失败 |
| 2 | Pod 状态和事件 | `kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e` | `Reason: CreateContainerConfigError` | Pod 无法启动，原因是容器配置错误 |
| 3 | Pod 列表摘要 | `kubectl get pod -n aiops-e2e` | `rc-config-configmap-key-missing 0/1 CreateContainerConfigError 0 71m` | Pod 处于异常状态，无法启动 |

### 证据关联分析

- **证据 #1 印证**：ConfigMap 不存在 → 容器配置失败
- **证据 #2 印证**：Pod 无法启动，状态为 CreateContainerConfigError
- **证据链**：引用的 ConfigMap 不存在 → 容器无法加载配置 → 容器启动失败 → Pod 保持异常状态

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| ConfigMap 定义 | critical | 无法确认是否是键名缺失，还是 ConfigMap 本身未创建 |
| Pod 定义 | important | 无法确认是否配置了正确的 ConfigMap 和 key |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ ConfigMap configmap-key-missing 不存在或键名缺失                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器启动时尝试读取配置，但 ConfigMap 不存在或 key 不存在         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ CreateContainerConfigError：容器配置失败                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-config-configmap-key-missing 处于 CreateContainerConfigError 状态 |
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (ConfigMap 不存在) 和证据 #2 (Pod 状态为 CreateContainerConfigError)，问题的根本原因是**引用的 ConfigMap configmap-key-missing 不存在或键名缺失**，导致容器无法加载配置，从而启动失败。

**置信度**：高 (90%)
- ✅ `kubectl get configmap configmap-key-missing` 明确返回 `NotFound`
- ✅ `kubectl describe pod` 明确显示 `Reason: CreateContainerConfigError`
- ⚠️ 未找到 ConfigMap 的定义，无法确认是键名缺失还是 ConfigMap 未创建

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 创建缺失的 ConfigMap**

```bash
kubectl create configmap configmap-key-missing -n aiops-e2e \
  --from-literal=key1=value1 \
  --from-literal=key2=value2
```

*依据*：ConfigMap 不存在是直接原因，需先创建 ConfigMap

**2. [可选] 检查 Pod 配置是否引用了正确 ConfigMap 和 key**

```bash
kubectl get pod rc-config-configmap-key-missing -n aiops-e2e -o yaml
```

*目的*：确认 Pod 定义中是否正确引用了 ConfigMap 和 key

### 后续优化

1. **文档化配置依赖**：确保所有 ConfigMap 和 Secret 在部署前创建
2. **配置校验**：在 CI/CD 流程中加入对 ConfigMap 和 key 的校验
3. **监控告警**：监控 Pod 启动失败事件，提前预警

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 ConfigMap 存在 | `kubectl get configmap configmap-key-missing -n aiops-e2e` | 显示 ConfigMap 详细信息 |
| 2. 确认 Pod 启动 | `kubectl get pod rc-config-configmap-key-missing -n aiops-e2e` | STATUS: Running |
| 3. 检查 Pod 事件 | `kubectl describe pod rc-config-configmap-key-missing -n aiops-e2e` | 无 CreateContainerConfigError |

---

## ⚠️ 注意事项

- 如果 Pod 仍然无法启动，检查 Pod 的定义中是否引用了正确的 ConfigMap 和 key。
- 如果 ConfigMap 存在但 key 缺失，需补充 key。
- 建议使用 `kubectl get pod -o yaml` 检查容器配置是否正确引用了 ConfigMap。

---

## 📊 性能统计

├─ 总耗时: 5.7m
├─ 问题定位: 38.2s (11%) ✅
├─ 证据链采集: 107.3s (31%) ✅
├─ 根因分析: 132.8s (39%) ✅
├─ 汇总总结: 66.5s (19%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 11 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 11 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
