======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: a98d1df29b9b41d7]

📍 [问题定位] 执行中...
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Error': 1, 'Running': 46}
NAMESPACE     NAME                                                READY   STATUS      RESTARTS        
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
      📄 NAME                                     READY   STATUS             RESTARTS       AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-env-missing-5d9b8b766c-cstkh   0/1
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
  "confidence": 0.95,
  "reasoning": "Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，符合配置错误导致的启动失败。",
  "abnormal_pods": [
    {
      "name": "rc-config-env-missing-5d9b8b766c-cstkh",
      "namespace": "aiops-e2e",
      "status": "CrashLoopBackOff",
      "restarts": "21 (13s ago)",
      "ip": "172.16.166.152",
      "node": "node1"
    }
  ],
  "abnormal_groups": [
    {
      "type": "ConfigError",
      "count": 1
    }
  ],
  "pod_status_keyword": "CrashLoopBackOff",
  "pod_abnormal_type": "ConfigError",
  "status_category": "CrashLoopBackOffRuntime",
  "key_entities": [
    {
      "kind": "Pod",
      "name": "rc-config-env-missing-5d9b8b766c-cstkh",
      "namespace": "aiops-e2e"
    }
  ],
  "possible_scenarios": [
    "缺少环境变量 APP_BOOT_MODE，导致应用配置校验失败，容器启动失败。"
  ]
}
   ✅ [问题定位] 完成 (36.0s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[]
   entities=[]
   reasoning=Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，符合配置错误导致的启动失败。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "ConfigError", "confidence": 0.95, "reasoning": "Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，符合配置错误导致的启动失败。", "abnormal_pods": [{"name": "rc-config-env-missing-5d9b8b766c-cstkh", "namespace": "aiops-e2e", "status": "Error"}], "pod_status_keyword": "CrashLoopBackOff", "pod_abnormal_type": "ConfigError", "status_category": "CrashLoopBackOffRuntime", "key_entities": [], "possible_scenarios": [], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Error"], "pod_abnormal_type": "Error", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "Error 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Error"], "pod_abnormal_type": "Error", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-config-env-missing-5d9b8b766c-cstkh"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "Error 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Error": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e     rc-config-env-missing-5d9b8b766c-cstkh              0/1     Error       21 (5m20s ago)   82m     172.16.166.152   node1    <none>           <none>            app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 95%

📍 [证据链采集] 执行中...
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
  Warning  BackOff  3m25s (x374
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
3m34s (x374 over 83m)   Warning   BackOff   Pod/rc-config-env-missing-5d9b8b766c-cstkh   Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstk
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                               DESIRED   CURRENT   READY   AGE   CONTAINERS   IMAGES         SELECTOR                                                 LABELS
rc-config-env-missing-5d9b8b766c   1   
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                    READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES         SELECTOR                    LABELS
rc-config-env-missing   0/1     1            0           83m   app        
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=1 abnormal=0 status_counts={}
NAME               DATA   AGE    LABELS
# 样例行
kube-root-ca.crt   1      111d   <none>
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                                     READY   STATUS             RESTARTS        AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-config-env-missing-5d9b8b766c-cstkh   0/
   💭 [证据链采集] # 证据结论

## 已采集证据
1. **kubectl_describe**:
   - Pod 状态为 `CrashLoopBackOff`，重启次数为21次。
   - 最后一次容器终止的退出码为42，且状态为 `Error`。
   - 事件中显示 `Back-off restarting failed container app`。

2. **kubectl_previous_logs**:
   - 日志显示 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，表明配置缺失导致启动失败。

3. **kubectl_get_yaml**:
   - Pod 的 `phase` 为 `Running`，但 `Ready` 状态为 `False`，且 `ContainersReady` 为 `False`。
   - 容器状态为 `CrashLoopBackOff`，退出码为42。
   - 无 `imagePullSecrets`，容器镜像为 `busybox:1.36`。

4. **kubectl_events**:
   - 事件中持续记录 `Back-off restarting failed container app`，表明容器因配置错误而反复失败。

5. **kubectl_get_by_name (ReplicaSet)**:
   - ReplicaSet `rc-config-env-missing-5d9b8b766c` 的 `READY` 状态为 0，表明没有可用的副本。

6. **kubectl_get_by_name (Deployment)**:
   - Deployment `rc-config-env-missing` 的 `READY` 状态为 0，表明没有可用的副本。

7. **kubectl_get_by_kind_in_namespace (ConfigMap)**:
   - 检查 `aiops-e2e` 命名空间下的 ConfigMap，未发现与该 Pod 相关的配置。

8. **kubectl_get_by_kind_in_namespace (Secret)**:
   - 检查 `aiops-e2e` 命名空间下的 Secret，未发现与该 Pod 相关的配置。

9. **kubectl_get_by_name (Pod)**:
   - Pod `rc-config-env-missing-5d9b8b766c-cstkh` 的状态为 `CrashLoopBackOff`，重启次数为21次。

## 未采集证据
- 无进一步的证据需要采集，因为当前证据已经充分说明了问题。

## 冲突证据
- 无冲突证据。

## 结论
- Pod `rc-config-env-missing-5d9b8b766c-cstkh` 处于 `CrashLoopBackOff` 状态，且日志显示 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，表明配置缺失导致启动失败。
- 该 Pod 的 `phase` 为 `Running`，但 `Ready` 状态为 `False`，且 `ContainersReady` 为 `False`。
- 无 `imagePullSecrets`，容器镜像为 `busybox:1.36`。
- ReplicaSet 和 Deployment 的 `READY` 状态为 0，表明没有可用的副本。
- 未发现与该 Pod 相关的 ConfigMap 或 Secret。
   ✅ [证据链采集] 完成 (1m 35.1s)
   📤 → 下游数据: evidence_items=4/4
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取 Pod rc-config-env-missing-5d9b8b766c-cstkh 的详细信息以分析 CrashLoopBackOff 的原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","tool_args":{"pod":"rc-config-env-missing-5d9b8b766c-cstkh","namespace":"aiops-e2e"},"purpose":"获取 Pod 的详细状态、事件和事件历史，以验证配置错误的上下文","evidence_type":"Pod 详细信息","target_scope":"aiops-e2e/rc-config-env-missing-5d9b8b766c-cstkh","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-config-env-missing-5d9b8b766c-cstkh\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Running\n关键诊断行:\n      Reason:       CrashLoopBackOff\n  Warning  BackOff  3m25s (x374 over 83m)  kubelet  Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)\n                  cni.projectcalico.org/containerID: b609d3199474fd0c991fb51944c653ad8de49c03971407f25be4cb50f1498fc2\n                  cni.projectcalico.org/podIP: 172.16.166.152/32\n                  cni.projectcalico.org/podIPs: 172.16.166.152/32\n                  k8s.v1.cni.cncf.io/network-status:\n                  k8s.v1.cni.cncf.io/networks-status:\n关键状态/事件:\n    State:          Waiting\n    Last State:     Terminated\n      Reason:       Error\n      Exit Code:    42","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nL4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/002-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-config-env-missing-5d9b8b766c-cstkh\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-14T22:19:01Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Running\nlabels: app=rc-config-env-missing, pod_abnormal_type=ConfigError\ndiagnostic_annotations: aiops.e2e/runbook=pod-config-error.md\nownerReferences: ReplicaSet/rc-config-env-missing-5d9b8b766c\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=21 reason=CrashLoopBackOff exitCode=42\n  message: back-off 5m0s restarting failed container=app pod=rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)\nvolumes:\n- {\"name\": \"kube-api-access-z9rrw\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n3m34s (x374 over 83m)   Warning   BackOff   Pod/rc-config-env-missing-5d9b8b766c-cstkh   Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def)","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/004-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                               DESIRED   CURRENT   READY   AGE   CONTAINERS   IMAGES         SELECTOR                                                 LABELS\nrc-config-env-missing-5d9b8b766c   1         1         0       83m   app          busybox:1.36   app=rc-config-env-missing,pod-template-hash=5d9b8b766c   app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/005-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/005-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/005-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                    READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES         SELECTOR                    LABELS\nrc-config-env-missing   0/1     1            0           83m   app          busybox:1.36   app=rc-config-env-missing   pod_abnormal_type=ConfigError,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/006-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/006-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/006-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"kubectl_get_by_kind_in_namespace 表格摘要: rows=1 abnormal=0 status_counts={}\nNAME               DATA   AGE    LABELS\n# 样例行\nkube-root-ca.crt   1      111d   <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/007-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/007-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/007-evidence-kubectl_get_by_kind_in_namespace.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/008-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/008-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/008-evidence-kubectl_get_by_kind_in_namespace.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                                     READY   STATUS             RESTARTS        AGE   IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\nrc-config-env-missing-5d9b8b766c-cstkh   0/1     CrashLoopBackOff   21 (102s ago)   83m   172.16.166.152   node1   <none>           <none>            app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/009-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/009-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a98d1df29b9b41d7/tools/009-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"# 证据结论\n\n## 已采集证据\n1. **kubectl_describe**:\n   - Pod 状态为 `CrashLoopBackOff`，重启次数为21次。\n   - 最后一次容器终止的退出码为42，且状态为 `Error`。\n   - 事件中显示 `Back-off restarting failed container app`。\n\n2. **kubectl_previous_logs**:\n   - 日志显示 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，表明配置缺失导致启动失败。\n\n3. **kubectl_get_yaml**:\n   - Pod 的 `phase` 为 `Running`，但 `Ready` 状态为 `False`，且 `ContainersReady` 为 `False`。\n   - 容器状态为 `CrashLoopBackOff`，退出码为42。\n   - 无 `imagePullSecrets`，容器镜像为 `busybox:1.36`。\n\n4. **kubectl_events**:\n   - 事件中持续记录 `Back-off restarting failed container app`，表明容器因配置错误而反复失败。\n\n5. **kubectl_get_by_name (ReplicaSet)**:\n   - ReplicaSet `rc-config-env-missing-5d9b8b766c` 的 `READY` 状态为 0，表明没有可用的副本。\n\n6. **kubectl_get_by_name (Deployment)**:\n   - Deployment `rc-config-env-missing` 的 `READY` 状态为 0，表明没有可用的副本。\n\n7. **kubectl_get_by_kind_in_namespace (ConfigMap)**:\n   - 检查 `aiops-e2e` 命名空间下的 ConfigMap，未发现与该 Pod 相关的配置。\n\n8. **kubectl_get_by_kind_in_namespace (Secret)**:\n   - 检查 `aiops-e2e` 命名空间下的 Secret，未发现与该 Pod 相关的配置。\n\n9. **kubectl_get_by_name (Pod)**:\n   - Pod `rc-config-env-missing-5d9b8b766c-cstkh` 的状态为 `CrashLoopBackOff`，重启次数为21次。\n\n## 未采集证据\n- 无进一步的证据需要采集，因为当前证据已经充分说明了问题。\n\n## 冲突证据\n- 无冲突证据。\n\n## 结论\n- Pod `rc-config-env-missing-5d9b8b766c-cstkh` 处于 `CrashLoopBackOff` 状态，且日志显示 `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`，表明配置缺失导致启动失败。\n- 该 Pod 的 `phase` 为 `Running`，但 `Ready` 状态为 `False`，且 `ContainersReady` 为 `False`。\n- 无 `imagePullSecrets`，容器镜像为 `busybox:1.36`。\n- ReplicaSet 和 Deployment 的 `READY` 状态为 0，表明没有可用的副本。\n- 未发现与该 Pod 相关的 ConfigMap 或 Secret。","collection_summary":"计划 1 项，实际采集 1 项，未采集 0 项，完整度 100%；其中真实环境证据 4/4 项，完整度 100%；实际执行工具 11 个，匹配计划 1 个，未规划证据 10 个","plan_total":1,"plan_collected":1,"plan_completeness":1.0,"environment_evidence_total":4,"environment_evidence_collected":4,"environment_evidence_completeness":1.0,"executed_tool_count":11,"matched_tool_count":1,"unplanned_tool_count":10,"evidence_inventory":[{"id":"e1","description":"获取 Pod rc-config-env-missing-5d9b8b766c-cstkh 的详细信息以分析 CrashLoopBackOff 的原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e","purpose":"获取 Pod 的详细状态、事件和事件历史，以验证配置错误的上下文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_previous_logs","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 1/1 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 获取 Pod rc-config-env-missing-5d9b8b766c-cstkh... | `kubectl describe pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` |

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
   ✅ [根因分析] 完成 (2m 20.1s)
   📤 → 下游数据: root_cause=Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，符合配置错误导致的启动失败。
   confidence=95%
   causal_chain={"root_cause": "配置缺失导致启动失败", "intermediate_causes": ["Pod rc-config-env-missing-5d9b8b766c-cstkh 状态为 CrashLoopBackOff，重启次数为21次。最后一次容器终止的退出码为42，且状态为 Error。事件中显示 Back-off restarting failed container app。", "kubectl_get_by_kind_in_cluster 表格摘要显示异常 Pod 为 rc-config-env-missing-5d9b8b766c-cstkh，状态为 Error，重启次数为21次。", "kubectl_get_by_name 显示 Pod rc-config-env-missing-5d9b8b766c-cstkh 状态为 CrashLoopBackOff，重启次数为21次。", "kubectl_previous_logs 日志摘要显示关键日志 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明配置缺失导致启动失败。"], "direct_causes": ["配置缺失导致启动失败"], "phenomena": ["Pod rc-config-env-missing-5d9b8b766c-cstkh 状态为 CrashLoopBackOff", "日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE"]}
   rca_analysis={"phenomenon": "", "evidence_inventory": [{"e1": "kubectl_describe 摘要: name: rc-config-env-missing-5d9b8b766c-cstkh, namespace: aiops-e2e, node: node1/10.2.0.49, status: Running, 关键诊断行: Reason: CrashLoopBackOff, Warning BackOff 3m25s (x374 over 83m) kubelet Back-off restarting failed container app in pod rc-config-env-missing-5d9b8b766c-cstkh_aiops-e2e(5ed47e61-9e99-459d-88de-ee30d25b1def), cni.projectcalico.org/containerID: b609d3199474fd0c991fb51944c653ad8de49c03971407f25be4cb50f1498fc2, cni.projectcalico.org/podIP: 172.16.166.152/32, cni.pro\n... 截断，原始 694 字符"}, {"layer_1": "kubectl_get_by_kind_in_cluster 表格摘要: rows=49 abnormal=1 status_counts={'Error': 1, 'Running': 46} NAMESPACE NAME READY STATUS RESTARTS AGE IP NODE NOMINATED NODE READINESS GATES LABELS # 异常行 aiops-e2e rc-config-env-missing-5d9b8b766c-cstkh 0/1 Error 21 (5m20s ago) 82m 172.16.166.152 node1 <none> <none> app=rc-config-env-missing,pod-template-hash=5"}, {"layer_2": "kubectl_get_by_name NAME rc-config-env-missing-5d9b8b766c-cstkh READY 0/1 STATUS CrashLoopBackOff RESTARTS 21 (13s ago) AGE 82m IP 172.16.166.152 NODE node1 NOMINATED NODE <none> READINESS GATES <none> LABELS app=rc-config-env-missing,pod-template-hash=5d9b8b766c,pod_abnormal_type=ConfigError,rootcause-e2e=true"}, {"layer_3": "kubectl_previous_logs 日志摘要: lines: 1 signals: 1 关键日志: L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE"}], "evidence_analysis": [{"e1": "Pod rc-config-env-missing-5d9b8b766c-cstkh 状态为 CrashLoopBackOff，重启次数为21次。最后一次容器终止的退出码为42，且状态为 Error。事件中显示 Back-off restarting failed container app。"}, {"layer_1": "kubectl_get_by_kind_in_cluster 表格摘要显示异常 Pod 为 rc-config-env-missing-5d9b8b766c-cstkh，状态为 Error，重启次数为21次。"}, {"layer_2": "kubectl_get_by_name 显示 Pod rc-config-env-missing-5d9b8b766c-cstkh 状态为 CrashLoopBackOff，重启次数为21次。"}, {"layer_3": "kubectl_previous_logs 日志摘要显示关键日志 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明配置缺失导致启动失败。"}], "causal_chain": {"root_cause": "配置缺失导致启动失败", "intermediate_causes": ["Pod rc-config-env-missing-5d9b8b766c-cstkh 状态为 CrashLoopBackOff，重启次数为21次。最后一次容器终止的退出码为42，且状态为 Error。事件中显示 Back-off restarting failed container app。", "kubectl_get_by_kind_in_cluster 表格摘要显示异常 Pod 为 rc-config-env-missing-5d9b8b766c-cstkh，状态为 Error，重启次数为21次。", "kubectl_get_by_name 显示 Pod rc-config-env-missing-5d9b8b766c-cstkh 状态为 CrashLoopBackOff，重启次数为21次。", "kubectl_previous_logs 日志摘要显示关键日志 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，表明配置缺失导致启动失败。"], "direct_causes": ["配置缺失导致启动失败"], "phenomena": ["Pod rc-config-env-missing-5d9b8b766c-cstkh 状态为 CrashLoopBackOff", "日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE"]}, "root_cause": "Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，符合配置错误导致的启动失败。", "root_cause_summary": "Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，符合配置错误导致的启动失败。", "confidence": 0.95, "confidence_reason": "有直接证据，因果链清晰", "primary_runbooks": ["pod-config-error.md"], "alternative_causes": [], "limitations": "", "llm_raw_analysis": "已采集证据分析: Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，符合配置错误导致的启动失败。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-config-env-missing-5d9b8b766c-cstkh 处于 CrashLoopBackOff 状态，且日志显示 L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE，符合配置错误导致的启动失败。
   置信度: 95%
   🔗 因果链:
     根本原因: 配置缺失导致启动失败


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (1m 20.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 3750 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 5m 52.0s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | CrashLoopBackOff |
| **兼容归因层** | L4 |
| **问题分类** | 配置错误（ConfigError） |
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
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: Error, RESTARTS: 21 (5m20s ago)` | Pod 处于 Error 状态，持续重启 |
| 2 | Pod 事件 | `kubectl describe pod` | `Reason: CrashLoopBackOff` | Pod 因容器崩溃进入 CrashLoopBackOff 状态 |
| 3 | 崩溃前日志 | `kubectl logs --previous` | `L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE` | 容器因缺少环境变量 APP_BOOT_MODE 启动失败 |
| 4 | 事件记录 | `kubectl get events` | `Warning BackOff (x374 over 83m) Back-off restarting failed container app` | 频繁重启事件确认容器持续失败 |

### 证据关联分析

- **证据 #1 + #2 印证**：Pod 状态为 Error，且事件中显示 CrashLoopBackOff，确认容器持续失败。
- **证据 #3 印证**：崩溃前日志明确指出缺少 `APP_BOOT_MODE`，说明是环境变量配置错误。
- **证据链**：容器缺少关键环境变量 → 启动失败 → 容器被终止 → Pod 进入 CrashLoopBackOff 状态 → 持续重启。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ 容器缺少关键环境变量 APP_BOOT_MODE，导致启动失败                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 容器初始化阶段因缺少配置参数无法继续执行                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ 容器启动失败，被 Kubernetes 终止并进入 CrashLoopBackOff 状态    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-config-env-missing-5d9b8b766c-cstkh 持续重启，状态为 Error │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #3 (崩溃前日志：`L4_CONFIG_BOOTSTRAP_FAIL: missing required APP_BOOT_MODE`) 和证据 #2 (`Reason: CrashLoopBackOff`)，问题的根本原因是**容器缺少关键环境变量 `APP_BOOT_MODE`**，导致启动失败，进入 CrashLoopBackOff 状态。

**置信度**：高 (95%)
- ✅ 崩溃日志明确指出配置缺失
- ✅ Pod 事件确认频繁重启
- ✅ 无缺失证据，证据链完整

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 为容器添加缺失的环境变量 `APP_BOOT_MODE`**

```bash
kubectl set env deployment/<deployment-name> -n aiops-e2e APP_BOOT_MODE=<value>
```

*依据*：崩溃日志明确指出缺少 `APP_BOOT_MODE`，需补充该配置

**2. [可选] 查看崩溃前日志**

```bash
kubectl logs rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e --previous
```

*目的*：确认是否还有其他配置问题，或应用是否需要更多环境变量

### 后续优化

1. **配置检查自动化**：使用 ConfigMap 或 Helm Chart 管理环境变量，避免遗漏
2. **健康检查优化**：为容器配置 liveness 和 readiness 探针，及时发现启动失败
3. **日志监控**：配置日志告警，当出现 `L4_CONFIG_BOOTSTRAP_FAIL` 类似错误时触发通知

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e` | STATUS: Running |
| 2. 检查重启次数 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 不再增加 |
| 3. 查看环境变量 | `kubectl get pod rc-config-env-missing-5d9b8b766c-cstkh -n aiops-e2e -o jsonpath='{.spec.containers[0].env}'` | 包含 `APP_BOOT_MODE` |

---

## ⚠️ 注意事项

- 如果问题仍然存在，请检查是否还有其他缺失的环境变量
- 建议为关键 Pod 配置 HPA（弹性扩缩容）或设置自动恢复策略
- 使用 `kubectl describe pod` 或 `kubectl get events` 进一步排查其他潜在问题

---

## 📊 性能统计

├─ 总耗时: 5.9m
├─ 问题定位: 36.0s (10%) ✅
├─ 证据链采集: 95.1s (27%) ✅
├─ 根因分析: 140.1s (40%) ✅
├─ 汇总总结: 80.8s (23%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 13 次
```

📋 诊断追踪

- **核心 Runbook**: pod-config-error
- **参考 Runbook**: pod-config-error
- **工具调用**: 13 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
