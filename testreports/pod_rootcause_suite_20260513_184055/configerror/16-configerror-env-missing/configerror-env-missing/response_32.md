======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 2008d59c33324833]

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
  "reasoning": "Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，且 previous logs 显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，符合 ConfigError 的诊断特征。",
  "abnormal_pods": ["rc-config-env-missing-5d9b8b766c-cstkh"],
  "abnormal_groups": ["CrashLoopBackOff"],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "ConfigError",
  "status_category": "ConfigError",
  "key_entities": ["APP_BOOT_MODE", "ConfigMap/Secret"],
  "possible_scenarios": [
    "Pod 的环境变量 APP_BOOT_MODE 缺失，导致应用启动失败。",
    "ConfigMap 或 Secret 中的 key APP_BOOT_MODE 未正确配置或未被正确引用。",
    "Pod 的配置文件缺失或配置错误，导致应用启动时配置校验失败。"
  ]
}
   ⏳ [问题定位] 仍在处理，等待工具或模型返回...
   ✅ [问题定位] 完成 (44.3s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'Pod 的环境变量 APP_BOOT_MODE 缺失，导致应用启动失败。', 'probability': 'high', 'reason': '日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE'}, {'scenario': 'ConfigMap 或 Secret 中的 key APP_BOOT_MODE 未正确配置或未被正确引用。', 'probability': 'high', 'reason': 'Pod 的配置资源可能引用错误或缺失 APP_BOOT_MODE'}, {'scenario': 'Pod 的配置文件缺失或配置错误，导致应用启动时配置校验失败。', 'probability': 'high', 'reason': '日志表明配置校验失败，且未找到 APP_BOOT_MODE'}]
   entities=[{"type": "ConfigMap/Secret", "name": "APP_BOOT_MODE", "namespace": "aiops-e2e"}]
   reasoning=Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，且 previous logs 显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，符合 ConfigError 的诊断特征。
   layer_analysis={"layer": "L4", "derived_layer": "CONFIGERROR", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，且 previous logs 显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，符合 ConfigError 的诊断特征。", "abnormal_pods": [{"name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e", "status": "CrashLoopBackOff"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "ConfigError", "key_entities": [{"type": "ConfigMap/Secret", "name": "APP_BOOT_MODE", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod 的环境变量 APP_BOOT_MODE 缺失，导致应用启动失败。", "probability": "high", "reason": "日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE"}, {"scenario": "ConfigMap 或 Secret 中的 key APP_BOOT_MODE 未正确配置或未被正确引用。", "probability": "high", "reason": "Pod 的配置资源可能引用错误或缺失 APP_BOOT_MODE"}, {"scenario": "Pod 的配置文件缺失或配置错误，导致应用启动时配置校验失败。", "probability": "high", "reason": "日志表明配置校验失败，且未找到 APP_BOOT_MODE"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["CrashLoopBackOff"], "pod_abnormal_type": "ConfigError", "compatible_layers": ["L4"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ConfigMap/Secret/env 配置缺失", "probability": "中", "reason": "需验证 Pod spec、事件和配置对象"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"CrashLoopBackOff": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-env-missing-5d9b8b766c-cstkh              0/1     CrashLoopBackOff   22 (51s ago)   88m     172.16.166.152   node1    <none>           <none>            app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/2008d59c33324833/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/2008d59c33324833/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/2008d59c33324833/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 95%

📍 [证据链采集] 执行中...
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
  Warning  BackOff  4m36s (x396
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 日志摘要:
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
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
4m46s (x396 over 89m)   Warning   BackOff   Pod/rc-config-env-missing-5d9b8b766c-cstkh   Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstk
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=163 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide configmap APP_BOOT_MODE -n aiops-e2e
Error from server (NotFound): configmaps "APP_BOOT_MODE"
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=157 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide secret APP_BOOT_MODE -n aiops-e2e
Error from server (NotFound): secrets "APP_BOOT_MODE" not f
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=1 abnormal=0 status_counts={}
NAME               DATA   AGE    LABELS
# 样例行
kube-root-ca.crt   1      111d   <none>
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。
   💭 [证据链采集] # 证据结论

## 已采集证据
1. **Pod 详细描述** (`kubectl describe pod`):
   - Pod `rc-config-env-missing-5d9b8b766c-cstkh` 处于 `CrashLoopBackOff` 状态，重启次数持续增加。
   - 最后一次失败容器的退出码为 `42`，表明是配置错误或启动失败。
   - Pod 的日志显示 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，表明缺少关键配置。

2. **Pod 前次日志** (`kubectl_previous_logs`):
   - 显示 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，确认了配置缺失。

3. **Pod YAML 配置** (`kubectl_get_yaml`):
   - Pod 的 YAML 配置中未找到 `APP_BOOT_MODE` 环境变量。
   - Pod 的 `imagePullSecrets` 未配置，但不是当前问题的关键。

4. **Pod 事件** (`kubectl_events`):
   - 显示 `Back-off restarting failed container app`，表明容器持续失败。

5. **ConfigMap 检查** (`kubectl_get_by_name` for ConfigMap `APP_BOOT_MODE`):
   - 未找到 `APP_BOOT_MODE` ConfigMap，确认配置缺失。

6. **Secret 检查** (`kubectl_get_by_name` for Secret `APP_BOOT_MODE`):
   - 未找到 `APP_BOOT_MODE` Secret，确认配置缺失。

## 未采集证据
- 暂无。

## 冲突证据
- 无。

## 结论
- Pod `rc-config-env-missing-5d9b8b766c-cstkh` 处于 `CrashLoopBackOff` 状态，原因是缺少 `APP_BOOT_MODE` 环境变量。
- `APP_BOOT_MODE` 既不在 ConfigMap 也不在 Secret 中定义，导致应用启动失败。
- 问题归类为 `ConfigError`，符合 `pod-config-error.md` 的诊断特征。
   ✅ [证据链采集] 完成 (2m 37.4s)
   📤 → 下游数据: evidence_items=3/3
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取异常 Pod rc-config-env-missing-5d9b8b766c-cstkh 的详细状态和事件信息，以验证 CrashLoopBackOff 的具体原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","tool_args":{"name":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e"},"purpose":"获取 Pod 的详细状态、事件和配置，用于诊断 CrashLoopBackOff 的具体原因。","evidence_type":"Pod 详细信息","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-env-missing-5d9b8b766c-cstkh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Reason:       CrashLoopBackOff\n  Warning  BackOff  4m36s (x396 over 89m)  kubelet  Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)\n                  cni.projectcalico.org/containerID: b609d3199474fd0c991fb51944c653ad8de49c03971407f25be4cb50f1498fc2\n                  cni.projectcalico.org/podIP: 172.16.166.152/32\n                  cni.projectcalico.org/podIPs: 172.16.166.152/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/002-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-config-env-missing-5d9b8b766c-cstkh\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-14T22:19:01Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-config-env-missing, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/runbook=pod-config-error.md\nownerReferences: ReplicaSet/rc-config-env-missing-5d9b8b766c\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=22 reason=CrashLoopBackOff exitCode=42\n  message: back-off 5m0s restarting failed container=app pod=rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)\nvolumes:\n- {\"name\": \"kube-api-access-z9rrw\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n4m46s (x396 over 89m)   Warning   BackOff   Pod/rc-config-env-missing-5d9b8b766c-cstkh   Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/004-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=163 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide configmap APP_BOOT_MODE -n aiops-e2e\nError from server (NotFound): configmaps \"APP_BOOT_MODE\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/005-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/005-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/005-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=157 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide secret APP_BOOT_MODE -n aiops-e2e\nError from server (NotFound): secrets \"APP_BOOT_MODE\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/006-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/006-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/006-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"kubectl_get_by_kind_in_namespace 表格摘要: rows=1 abnormal=0 status_counts={}\nNAME               DATA   AGE    LABELS\n# 样例行\nkube-root-ca.crt   1      111d   <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/007-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/007-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/007-evidence-kubectl_get_by_kind_in_namespace.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/008-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/008-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2008d59c33324833/tools/008-evidence-kubectl_get_by_kind_in_namespace.summary.txt"}],"llm_analysis":"# 证据结论\n\n## 已采集证据\n1. **Pod 详细描述** (`kubectl describe pod`):\n   - Pod `rc-config-env-missing-5d9b8b766c-cstkh` 处于 `CrashLoopBackOff` 状态，重启次数持续增加。\n   - 最后一次失败容器的退出码为 `42`，表明是配置错误或启动失败。\n   - Pod 的日志显示 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，表明缺少关键配置。\n\n2. **Pod 前次日志** (`kubectl_previous_logs`):\n   - 显示 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，确认了配置缺失。\n\n3. **Pod YAML 配置** (`kubectl_get_yaml`):\n   - Pod 的 YAML 配置中未找到 `APP_BOOT_MODE` 环境变量。\n   - Pod 的 `imagePullSecrets` 未配置，但不是当前问题的关键。\n\n4. **Pod 事件** (`kubectl_events`):\n   - 显示 `Back-off restarting failed container app`，表明容器持续失败。\n\n5. **ConfigMap 检查** (`kubectl_get_by_name` for ConfigMap `APP_BOOT_MODE`):\n   - 未找到 `APP_BOOT_MODE` ConfigMap，确认配置缺失。\n\n6. **Secret 检查** (`kubectl_get_by_name` for Secret `APP_BOOT_MODE`):\n   - 未找到 `APP_BOOT_MODE` Secret，确认配置缺失。\n\n## 未采集证据\n- 暂无。\n\n## 冲突证据\n- 无。\n\n## 结论\n- Pod `rc-config-env-missing-5d9b8b766c-cstkh` 处于 `CrashLoopBackOff` 状态，原因是缺少 `APP_BOOT_MODE` 环境变量。\n- `APP_BOOT_MODE` 既不在 ConfigMap 也不在 Secret 中定义，导致应用启动失败。\n- 问题归类为 `ConfigError`，符合 `pod-config-error.md` 的诊断特征。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 3/3 项，完整度 100%；实际执行工具 9 个，匹配计划 1 个，未规划证据 8 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":3,"environment_evidence_collected":3,"environment_evidence_completeness":1.0,"executed_tool_count":9,"matched_tool_count":1,"unplanned_tool_count":8,"evidence_inventory":[{"id":"e1","description":"获取异常 Pod rc-config-env-missing-5d9b8b766c-cstkh 的详细状态和事件信息，以验证 CrashLoopBackOff 的具体原因。","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","purpose":"获取 Pod 的详细状态、事件和配置，用于诊断 CrashLoopBackOff 的具体原因。","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取异常 Pod rc-config-env-missing-5d9b8b766c-cst... | `kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (21.2s)
   📤 → 下游数据: root_cause=Pod rc-config-env-missing-5d9b8b766c-cstkh 缺失 APP_BOOT_MODE 环境变量导致启动失败，且未在 ConfigMap 或 Secret 中找到该配置。
   confidence=95%
   causal_chain={}
   rca_analysis={"phenomenon": "", "evidence_inventory": [], "evidence_analysis": [], "causal_chain": {}, "root_cause": "Pod rc-config-env-missing-5d9b8b766c-cstkh 缺失 APP_BOOT_MODE 环境变量导致启动失败，且未在 ConfigMap 或 Secret 中找到该配置。", "root_cause_summary": "Pod rc-config-env-missing-5d9b8b766c-cstkh 缺失 APP_BOOT_MODE 环境变量导致启动失败，且未在 ConfigMap 或 Secret 中找到该配置。", "confidence": 0.95, "confidence_reason": "有直接证据表明 APP_BOOT_MODE 缺失，且 ConfigMap 和 Secret 中未找到该配置。", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [], "limitations": "", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-config-env-missing-5d9b8b766c-cstkh 缺失 APP_BOOT_MODE 环境变量导致启动失败，且未在 ConfigMap 或 Secret 中找到该配置。
   置信度: 95%

📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 0.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4740 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 43.7s
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
| **兼容归因层** | CONFIGERROR |
| **问题分类** | ConfigError（L4_CONFIG_BOOTSTRAP_FAIL） |
| **置信度** | 高 (95%) |
| **证据完整度** | 1/1 (100%) |

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
| 1 | Pod 状态 | kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh | `Reason: CrashLoopBackOff` | Pod 处于重启循环中 |
| 2 | Pod 事件 | kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh | `Warning  BackOff  4m36s (x396) Back-off restarting failed container app` | 容器启动失败，持续重启 |
| 3 | 崩溃前日志 | kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` | 缺失关键环境变量 APP_BOOT_MODE |
| 4 | ConfigMap/Secret 检查 | kubectl get configmap APP_BOOT_MODE -n aiops-e2e | `Error from server (NotFound): configmaps "APP_BOOT_MODE"` | ConfigMap 未找到 |
| 5 | ConfigMap/Secret 检查 | kubectl get secret APP_BOOT_MODE -n aiops-e2e | `Error from server (NotFound): secrets "APP_BOOT_MODE" not found` | Secret 未找到 |

### 证据关联分析
- **证据 #1 + #3 印证**：CrashLoopBackOff + 日志显示 `missing required APP_BOOT_MODE` → 应用启动失败
- **证据 #4 + #5 印证**：ConfigMap 和 Secret 都未找到 `APP_BOOT_MODE` → 配置缺失
- **因果链**：APP_BOOT_MODE 未在 ConfigMap/Secret 中定义 → Pod 启动失败 → CrashLoopBackOff

### 缺失证据（无）
无缺失证据，证据完整度为 100%。

---

## 🎯 根因分析
### 因果链
```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                            │
│ Pod rc-config-env-missing-5d9b8b766c-cstkh 缺失 APP_BOOT_MODE 环境变量，导致启动失败  │
└───────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                            │
│ 应用启动时检查到 APP_BOOT_MODE 缺失，抛出 L4_CONFIG_BOOTSTRAP_FAIL 错误               │
└───────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                            │
│ 容器启动失败，触发 CrashLoopBackOff 机制，Pod 持续重启                                │
└───────────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                      │
│ Pod rc-config-env-missing-5d9b8b766c-cstkh 状态为 CrashLoopBackOff，重启次数持续增加  │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #3 (`L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`) 和证据 #4/5 (`ConfigMap/Secret APP_BOOT_MODE not found`)，问题的根本原因是**Pod rc-config-env-missing-5d9b8b766c-cstkh 缺失环境变量 APP_BOOT_MODE，且未在 ConfigMap 或 Secret 中定义该变量**，导致应用启动失败并进入 CrashLoopBackOff 状态。
**置信度**：高 (95%)
- ✅ 日志明确显示缺失 APP_BOOT_MODE
- ✅ ConfigMap/Secret 都未找到该变量
- ✅ Pod 事件显示持续重启

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 创建 ConfigMap 或 Secret 并添加 APP_BOOT_MODE**
```bash
# 创建 ConfigMap 示例
kubectl create configmap app-boot-mode -n aiops-e2e --from-literal=APP_BOOT_MODE=dev

# 或创建 Secret（如果敏感）
kubectl create secret generic app-boot-mode -n aiops-e2e --from-literal=APP_BOOT_MODE=dev
```
*依据*：证据 #4/5 显示当前没有定义该变量，应用依赖此变量启动

**2. [可选] 更新 Pod 的配置，引用新的 ConfigMap/Secret**
```bash
# 示例：修改 deployment 引用新的 ConfigMap
kubectl set env deployment/<deployment-name> -n aiops-e2e APP_BOOT_MODE=dev
# 或者在 deployment YAML 中添加 env 从 configmap/secret 挂载
```

### 后续优化
1. **配置校验**：在部署流程中增加配置校验步骤，确保所有必需环境变量存在
2. **文档更新**：在部署文档中明确列出所有必需的环境变量
3. **监控告警**：配置 Pod 启动失败告警，及时发现类似问题

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 ConfigMap/Secret 存在 | `kubectl get configmap app-boot-mode -n aiops-e2e` 或 `kubectl get secret app-boot-mode -n aiops-e2e` | 存在 |
| 2. 确认 Pod 运行 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | STATUS: Running |
| 3. 检查重启次数 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |

---

## ⚠️ 注意事项
- 如果问题仍然存在，检查应用是否还依赖其他缺失的环境变量
- 确保 ConfigMap/Secret 的权限配置正确，Pod 有权限读取
- 如果使用 Secret，建议启用自动解密功能（如 Kubernetes Secrets Manager）

---

---

## 📊 性能统计

├─ 总耗时: 5.7m
├─ 问题定位: 44.3s (13%) ✅
├─ 证据链采集: 157.4s (46%) ✅
├─ 根因分析: 21.2s (6%) ✅
├─ 汇总总结: 120.7s (35%) ✅
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
