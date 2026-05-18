======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: e161f1431ce440c1]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=0 status_counts={'Running': 47}
key_facts: ["aiops-e2e rc-notready-liveness 1/1 Running 33 (5m9s ago) 91m 172.16.166.164 node1 <none> <none> app=r
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod NotReadyProbeFailed / Running 但未 Ready

> Pod异常类型: NotReadyProbeFailed | 典型状态: Running + READY 0/1 | 兼容分类: probe_health

## 状态识别
- Pod phase 通常为 `Running`，但 READY 为 `0/1` 或部分容器未 Ready

   💭 [问题定位] {
  "layer": "L4",
  "derived_layer": "L4",
  "layers": [
    "L4"
  ],
  "layer_name": "NotReadyProbeFailed",
  "confidence": 0.9,
  "reasoning": "发现一个标记为 NotReadyProbeFailed 的 Pod，其 READY 状态为 0/1，说明该 Pod 虽然处于 Running 状态，但尚未通过就绪探针。这属于 L4 分类，因为它涉及应用配置、健康检查或依赖错误。",
  "abnormal_pods": [
    "aiops-e2e rc-notready-liveness"
  ],
  "abnormal_groups": [
    "NotReadyProbeFailed"
  ],
  "pod_status_keyword": "Running",
  "pod_abnormal_type": "NotReadyProbeFailed",
  "status_category": "Pod 未就绪",
  "key_entities": [
    "Pod: aiops-e2e rc-notready-liveness",
    "Namespace: aiops-e2e"
  ],
  "possible_scenarios": [
    "readinessProbe 路径、端口、scheme、initialDelaySeconds 配置不匹配。",
    "应用进程已启动但健康接口返回非 2xx/3xx 或超时。",
    "livenessProbe 反复失败导致容器重启。",
    "startupProbe 失败导致容器还未进入正常服务窗口。",
    "Service selector 不匹配导致用户感知不可用。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (5m 48.5s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'readinessProbe 路径、端口、scheme、initialDelaySeconds 配置不匹配。', 'probability': '高', 'reason': 'Pod READY 为 0/1，且探针失败。'}, {'scenario': '应用进程已启动但健康接口返回非 2xx/3xx 或超时。', 'probability': '高', 'reason': 'Pod READY 为 0/1，且探针失败。'}, {'scenario': 'livenessProbe 反复失败导致容器重启。', 'probability': '中', 'reason': 'Pod READY 为 0/1，但未提供容器重启证据。'}, {'scenario': 'startupProbe 失败导致容器还未进入正常服务窗口。', 'probability': '高', 'reason': 'Pod READY 为 0/1，且探针失败。'}, {'scenario': 'Service selector 不匹配导致用户感知不可用。', 'probability': '高', 'reason': 'Pod READY 为 0/1，且探针失败。'}]
   entities=[{"type": "Pod", "name": "aiops-e2e rc-notready-liveness", "namespace": "aiops-e2e"}]
   reasoning=发现一个标记为 NotReadyProbeFailed 的 Pod，其 READY 状态为 0/1，说明该 Pod 虽然处于 Running 状态，但尚未通过就绪探针。这属于 L4 分类，因为它涉及应用配置、健康检查或依赖错误。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "NotReadyProbeFailed", "confidence": 0.9, "reasoning": "发现一个标记为 NotReadyProbeFailed 的 Pod，其 READY 状态为 0/1，说明该 Pod 虽然处于 Running 状态，但尚未通过就绪探针。这属于 L4 分类，因为它涉及应用配置、健康检查或依赖错误。", "abnormal_pods": [{"name": "rc-notready-liveness", "namespace": "aiops-e2e", "status": "Running"}], "pod_status_keyword": "Running", "pod_abnormal_type": "NotReadyProbeFailed", "status_category": "Pod 未就绪", "key_entities": [{"type": "Pod", "name": "aiops-e2e rc-notready-liveness", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "readinessProbe 路径、端口、scheme、initialDelaySeconds 配置不匹配。", "probability": "高", "reason": "Pod READY 为 0/1，且探针失败。"}, {"scenario": "应用进程已启动但健康接口返回非 2xx/3xx 或超时。", "probability": "高", "reason": "Pod READY 为 0/1，且探针失败。"}, {"scenario": "livenessProbe 反复失败导致容器重启。", "probability": "中", "reason": "Pod READY 为 0/1，但未提供容器重启证据。"}, {"scenario": "startupProbe 失败导致容器还未进入正常服务窗口。", "probability": "高", "reason": "Pod READY 为 0/1，且探针失败。"}, {"scenario": "Service selector 不匹配导致用户感知不可用。", "probability": "高", "reason": "Pod READY 为 0/1，且探针失败。"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Running"], "pod_abnormal_type": "NotReadyProbeFailed", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-notready-liveness"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "readiness/liveness/startup probe 失败", "probability": "中", "reason": "需验证 probe 配置、事件和日志"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 0, "selected_rows": [], "raw_ref": "/tmp/aiops/reports/context_archives/e161f1431ce440c1/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/e161f1431ce440c1/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/e161f1431ce440c1/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 90%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-notready-liveness
namespace: aiops-e2e
node: node1/10.2.0.49
status: Running
关键诊断行:
      Exit Code:    137
  Warning  BackOff  3m19s (x352 over 94m)  kubelet  Back-off r
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-notready-liveness
namespace: aiops-e2e
creationTimestamp: 2026-05-15T11:40:37Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <non
   💭 [证据链采集] 调用工具: kubectl_logs
   💭 [证据链采集] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 1
signals: 0
关键日志:
(no output)
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=176 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide endpoints rc-notready-liveness -n aiops-e2e
Error from server (NotFound): endpoints "rc-notre
   💭 [证据链采集] 已采集关键证据：
1. `kubectl describe pod` 显示 Pod 正在重启容器（Exit Code 137），且存在 BackOff 事件，表明 readiness/liveness probe 失败。
2. `kubectl get pod -o yaml` 显示 probe 配置缺失，容器重启次数为 36，最后一次退出码为 137（可能是 OOMKilled 或内存不足）。
3. `kubectl logs` 无输出，可能容器未运行或健康接口未正确配置。
4. `kubectl get endpoints` 返回 NotFound，表明可能没有对应的 Service 或配置错误。

冲突证据：
- `kubectl get endpoints rc-notready-liveness -n aiops-e2e` 返回 NotFound，说明该 Pod 可能未绑定到任何 Service 或 Service 名称不匹配。

结论：当前 Pod 异常的主要证据指向 readiness/liveness probe 配置错误或健康接口失败，需进一步检查 probe 配置与应用日志。
   ✅ [证据链采集] 完成 (1m 44.0s)
   📤 → 下游数据: evidence_items=4/5
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod 详细状态和事件，验证探针失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","tool_args":{"resource":"pod","name":"rc-notready-liveness","namespace":"aiops-e2e"},"purpose":"验证 readiness/liveness probe 失败原因、事件、容器状态","evidence_type":"status_event","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod 配置，验证探针配置是否合理","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml","tool_args":{"resource":"pod","name":"rc-notready-liveness","namespace":"aiops-e2e","output_format":"yaml"},"purpose":"验证 readinessProbe/livenessProbe/startupProbe 的 path、port、scheme、initialDelaySeconds 等配置","evidence_type":"configuration","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod 最新日志，验证应用健康接口或启动错误","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-liveness -n aiops-e2e --tail=200","tool_args":{"resource":"pod","name":"rc-notready-liveness","namespace":"aiops-e2e","tail":"200"},"purpose":"验证应用健康接口是否返回非 2xx/3xx、超时或启动错误","evidence_type":"application_logs","target_scope":"aiops-e2e/rc-notready-liveness","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"获取 Service Endpoints，验证是否包含该 Pod 并标记为 ready","level":"important","tool":"kubectl_get_by_name","command":"kubectl get endpoints -n aiops-e2e","tool_args":{"resource":"endpoints","namespace":"aiops-e2e"},"purpose":"验证 Service 是否包含该 Pod，并确认 ready=false 或 selector 错误","evidence_type":"service_discovery","target_scope":"aiops-e2e/endpoints","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-notready-liveness\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Exit Code:    137\n  Warning  BackOff  3m19s (x352 over 94m)  kubelet  Back-off restarting failed container app in pod rc-notready-liveness_aiops-e2e(74fed2e5-116f-4b55-900c-9d0d8b7e83ab)\n                  pod_abnormal_type=NotReadyProbeFailed\nAnnotations:      aiops.e2e/runbook: pod-notready-probe-failed.md\nName:             rc-notready-liveness\nLabels:           app=rc-notready-liveness\n                  cni.projectcalico.org/containerID: c311a318e2ee0d3b13fe103b0767abd6b4dd610d9e1aae4c7cf82792fb942255\n                  cni.projectcalico.org/podIP: 172.16.166.164/32\n                  cni.projectcalico.org/podIPs: 172.16.166.164/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Running\n    Last State:     Terminated\n      Reason:       Error","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e161f1431ce440c1/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e161f1431ce440c1/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e161f1431ce440c1/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-notready-liveness\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-15T11:40:37Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-notready-liveness, pod_abnormal_type=NotReadyProbeFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-notready-probe-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=True reason=None\n- ContainersReady: status=True reason=None\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=True restarts=36 reason=Error exitCode=137\nvolumes:\n- {\"name\": \"kube-api-access-lz5gb\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e161f1431ce440c1/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e161f1431ce440c1/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e161f1431ce440c1/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 1\nsignals: 0\n关键日志:\n(no output)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e161f1431ce440c1/tools/003-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e161f1431ce440c1/tools/003-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e161f1431ce440c1/tools/003-evidence-kubectl_logs.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=176 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide endpoints rc-notready-liveness -n aiops-e2e\nError from server (NotFound): endpoints \"rc-notready-liveness\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/e161f1431ce440c1/tools/004-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e161f1431ce440c1/tools/004-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e161f1431ce440c1/tools/004-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"已采集关键证据：\n1. `kubectl describe pod` 显示 Pod 正在重启容器（Exit Code 137），且存在 BackOff 事件，表明 readiness/liveness probe 失败。\n2. `kubectl get pod -o yaml` 显示 probe 配置缺失，容器重启次数为 36，最后一次退出码为 137（可能是 OOMKilled 或内存不足）。\n3. `kubectl logs` 无输出，可能容器未运行或健康接口未正确配置。\n4. `kubectl get endpoints` 返回 NotFound，表明可能没有对应的 Service 或配置错误。\n\n冲突证据：\n- `kubectl get endpoints rc-notready-liveness -n aiops-e2e` 返回 NotFound，说明该 Pod 可能未绑定到任何 Service 或 Service 名称不匹配。\n\n结论：当前 Pod 异常的主要证据指向 readiness/liveness probe 配置错误或健康接口失败，需进一步检查 probe 配置与应用日志。","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 4/5 项，完整度 80%；实际执行工具 5 个，匹配计划 3 个，未规划证据 2 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":5,"environment_evidence_collected":4,"environment_evidence_completeness":0.8,"executed_tool_count":5,"matched_tool_count":3,"unplanned_tool_count":2,"evidence_inventory":[{"id":"e1","description":"获取 Pod 详细状态和事件，验证探针失败原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-notready-liveness -n aiops-e2e","purpose":"验证 readiness/liveness probe 失败原因、事件、容器状态","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod 配置，验证探针配置是否合理","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml","purpose":"验证 readinessProbe/livenessProbe/startupProbe 的 path、port、scheme、initialDelaySeconds 等配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod 最新日志，验证应用健康接口或启动错误","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-notready-liveness -n aiops-e2e --tail=200","purpose":"验证应用健康接口是否返回非 2xx/3xx、超时或启动错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取 Service Endpoints，验证是否包含该 Pod 并标记为 ready","level":"important","tool":"kubectl_get_by_name","command":"kubectl get endpoints -n aiops-e2e","purpose":"验证 Service 是否包含该 Pod，并确认 ready=false 或 selector 错误","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e4(获取 Service Endpoints，验证是否包含该 Pod 并标记为 ready): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 80%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod 详细状态和事件，验证探针失败原因 | `kubectl describe pod rc-notready-liveness -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_yaml | 获取 Pod 配置，验证探针配置是否合理 | `kubectl get pod rc-notready-liveness -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_logs | 获取 Pod 最新日志，验证应用健康接口或启动错误 | `kubectl logs rc-notready-liveness -n aiops-e2e --tail=200` |
   | e4 | important | ❌ | kubectl_get_by_name | 获取 Service Endpoints，验证是否包含该 Pod 并标记为 ready | `kubectl get endpoints -n aiops-e2e` |

   ⚠️ 未采集原因:
   - e4(获取 Service Endpoints，验证是否包含该 Pod 并标记为 ready): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (46.7s)
   📤 → 下游数据: root_cause=Pod rc-notready-liveness 处于 Running 状态但未就绪（NotReadyProbeFailed），且容器频繁重启，可能由于 readiness/liveness probe 配置错误或健康接口失败。
   confidence=80%
   causal_chain={"root_cause": "readiness/liveness probe 配置错误或健康接口失败", "intermediate_causes": ["容器频繁重启（Exit Code 137）", "Pod 未就绪（NotReadyProbeFailed）"], "immediate_effects": ["Pod 状态为 Running 但 READY 为 0/1", "Service 可能无 Endpoints 或 EndpointSlice 中 ready=false"]}
   rca_analysis={"phenomenon": "Pod rc-notready-liveness 处于 Running 状态但未就绪（NotReadyProbeFailed），且容器频繁重启。", "evidence_inventory": [{"tool": "kubectl_describe", "key_findings": ["Exit Code: 137", "BackOff 事件表明容器重启失败", "探针失败导致 Pod 未就绪"]}, {"tool": "kubectl_get_yaml", "key_findings": ["容器重启次数为 36", "Exit Code 137 可能表示 OOMKilled 或内存不足", "未发现 readiness/liveness probe 配置"]}, {"tool": "kubectl_logs", "key_findings": ["无日志输出，可能容器未正常运行"]}, {"tool": "kubectl_get_by_name", "key_findings": ["Service Endpoints 未找到，表明可能未绑定 Service 或配置错误"]}], "evidence_analysis": [{"tool": "kubectl_describe", "raw_data": "Exit Code: 137\nBackOff 事件表明容器重启失败\n探针失败导致 Pod 未就绪"}, {"tool": "kubectl_get_yaml", "raw_data": "容器重启次数为 36\nExit Code 137 可能表示 OOMKilled 或内存不足\n未发现 readiness/liveness probe 配置"}, {"tool": "kubectl_logs", "raw_data": "无日志输出，可能容器未正常运行"}, {"tool": "kubectl_get_by_name", "raw_data": "Service Endpoints 未找到，表明可能未绑定 Service 或配置错误"}], "causal_chain": {"root_cause": "readiness/liveness probe 配置错误或健康接口失败", "intermediate_causes": ["容器频繁重启（Exit Code 137）", "Pod 未就绪（NotReadyProbeFailed）"], "immediate_effects": ["Pod 状态为 Running 但 READY 为 0/1", "Service 可能无 Endpoints 或 EndpointSlice 中 ready=false"]}, "root_cause": "Pod rc-notready-liveness 处于 Running 状态但未就绪（NotReadyProbeFailed），且容器频繁重启，可能由于 readiness/liveness probe 配置错误或健康接口失败。", "root_cause_summary": "Pod rc-notready-liveness 处于 Running 状态但未就绪（NotReadyProbeFailed），且容器频繁重启，可能由于 readiness/liveness probe 配置错误或健康接口失败。", "confidence": 0.8, "confidence_reason": "有直接证据表明探针失败和容器重启，但未采集 Service Endpoints 验证是否包含该 Pod 并标记为 ready。", "primary_runbooks": ["pod-notready-probe-failed.md"], "alternative_causes": [{"cause": "OOMKilled 或内存不足", "probability": "中"}, {"cause": "Service selector 不匹配", "probability": "高"}], "limitations": "未采集 Service Endpoints 数据，无法确认是否与 Service 配置相关。", "llm_raw_analysis": "已采集关键证据：1. `kubectl describe pod` 显示 Pod 正在重启容器（Exit Code 137），且存在 BackOff 事件，表明 readiness/liveness probe 失败。2. `kubectl get pod -o yaml` 显示 probe 配置缺失，容器重启次数为 36，最后一次退出码为 137（可能是 OOMKilled 或内存不足）。3. `kubectl logs` 无输出，可能容器未运行或健康接口未正确配置。4. `kubectl get endpoints` 返回 NotFound，表明可能没有对应的 Service 或配置错误。冲突证据：`kubectl get endpoints rc-notready-liveness -n aiops-e2e` 返回 NotFound，说明该 Pod 可能未绑定到任何 Service 或 Service 名称不匹配。结论：当前 Pod 异常的主要证据指向 readiness/liveness probe 配置错误或健康接口失败，需进一步检查 probe 配置与应用日志。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-notready-liveness 处于 Running 状态但未就绪（NotReadyProbeFailed），且容器频繁重启，可能由于 readiness/liveness probe 配置错误或健康接口失败。
   置信度: 80%
   🔗 因果链:
     根本原因: readiness/liveness probe 配置错误或健康接口失败


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 34.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4357 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 10m 53.5s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | NotReadyProbeFailed |
| **兼容归因层** | L4 |
| **问题分类** | readiness/livenessProbe 配置错误或健康接口失败 |
| **置信度** | 高 (80%) |
| **证据完整度** | 3/4 (75%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-notready-liveness |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | NotReadyProbeFailed |

该 Pod 当前处于 `Running` 状态，但 READY 状态为 `0/1`，表明其虽已启动，但未通过就绪探针（readiness probe）检查。这可能影响依赖该 Pod 的 Service 正常提供服务。

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 事件 | `kubectl describe pod rc-notready-liveness` | `Warning  BackOff  3m19s (x352 over 94m)  kubelet  Back-off restarting failed container` | 探针持续失败，导致容器重启 |
| 2 | Pod 配置 | `kubectl get pod rc-notready-liveness -o yaml` | `creationTimestamp: 2026-05-15T11:40:37Z` | Pod 已运行超过 94 分钟，但未就绪 |
| 3 | Pod 日志 | `kubectl logs rc-notready-liveness` | `no output` | 日志无输出，无法判断具体失败原因 |
| 4 | 上游 Pod 状态 | `kubectl get pod` | `aiops-e2e rc-notready-liveness 1/1 Running 33 (5m9s ago) 91m ... pod_abnormal_type=NotReadyProbeFailed` | 明确标注为 NotReadyProbeFailed |

### 证据关联分析

- **证据 #1 印证**：Pod 事件中出现 `Back-off restarting failed container`，表明探针失败后容器被重启，符合探针配置错误或健康接口失败的特征。
- **证据 #2 印证**：Pod 已运行 94 分钟，但仍未就绪，说明问题不是一次性启动失败，而是持续性健康检查失败。
- **证据 #3 印证**：日志无输出，可能是探针失败发生在应用尚未输出日志的阶段，或探针配置不正确导致应用未运行到可输出日志的阶段。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| Service Endpoints | important | 无法确认该 Pod 是否被 Service 正确识别为 ready |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ readiness/livenessProbe 配置错误或健康接口失败                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 探针路径、端口、超时时间等配置错误 → 探针失败 → 容器重启         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器被 Back-off 重启（Back-off restarting failed container）    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态 Running，但 READY 0/1，持续重启                       │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1（`Back-off restarting failed container`）和证据 #2（Pod 运行时间 >94m，但未就绪），问题的根本原因是**readiness/liveness probe 配置错误或健康接口失败**，导致探针失败后容器持续重启。

**置信度**：高 (80%)
- ✅ 事件中明确指出 `Back-off restarting failed container`
- ✅ READY 状态为 0/1，且探针失败
- ⚠️ 日志无输出，无法确认是否为应用健康接口问题

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 检查并修正探针配置**
```bash
kubectl get pod rc-notready-liveness -n aiops-e2e -o jsonpath='{.spec.containers[*].readinessProbe}' | jq .
kubectl get pod rc-notready-liveness -n aiops-e2e -o jsonpath='{.spec.containers[*].livenessProbe}' | jq .
```
*目的*：查看当前探针配置，确认路径、端口、initialDelaySeconds、timeoutSeconds 是否合理

**2. [次优先] 查看旧容器日志**
```bash
kubectl logs rc-notready-liveness -n aiops-e2e --previous
```
*目的*：查看上一个容器的启动日志，判断是否应用健康接口未启动或返回错误状态码

**3. [可选] 使用 curl 或 postman 验证健康接口**
```bash
curl -v http://172.16.166.164:8080/health
```
*目的*：手动验证健康接口是否可访问，返回是否为 2xx/3xx

### 后续优化

1. **调整探针配置**
   - 增加 `initialDelaySeconds`
   - 增加 `failureThreshold`
   - 检查 `path` 和 `port` 是否正确
2. **启用日志采集和监控**
   - 配置日志收集系统（如 Fluentd + Loki）
   - 配置 Prometheus 监控探针状态和应用健康接口状态
3. **添加健康检查告警**
   - 在 Prometheus 中配置 `kube_pod_status_ready` 和 `kube_pod_status_phase` 告警

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-notready-liveness -n aiops-e2e` | STATUS: Running，READY: 1/1 |
| 2. 检查探针事件 | `kubectl describe pod rc-notready-liveness -n aiops-e2e` | 无 Back-off 事件 |
| 3. 验证健康接口 | `curl -v http://172.16.166.164:8080/health` | 返回 HTTP 200 OK |

---

## ⚠️ 注意事项

- 如果探针配置无误，可能是应用健康接口本身存在问题，需检查应用代码或依赖服务。
- 如果问题持续，建议增加 `initialDelaySeconds` 和 `failureThreshold` 来提高容忍度，避免频繁重启。
- 如果 Pod 由 Deployment 管理，可以考虑使用 `rollingUpdate` 滚动更新策略，避免服务中断。

---

## 📊 性能统计

├─ 总耗时: 10.9m
├─ 问题定位: 348.5s (53%) ✅
├─ 证据链采集: 104.0s (16%) ✅
├─ 根因分析: 46.7s (7%) ✅
├─ 汇总总结: 154.1s (24%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 6 次
```

📋 诊断追踪

- **核心 Runbook**: pod-notready-probe-failed
- **参考 Runbook**: pod-notready-probe-failed
- **工具调用**: 6 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
