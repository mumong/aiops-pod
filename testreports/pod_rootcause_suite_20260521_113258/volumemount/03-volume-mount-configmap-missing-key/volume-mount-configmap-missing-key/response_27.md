======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: a06049aeb9c24dfe]

📍 [问题定位] 执行中...
   💭 [问题定位] 首先，让我全局扫描集群中的所有 Pod，了解整体状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59}
NAMESPACE         NAME                                                READY   STATUS              RESTARTS       A
   💭 [问题定位] 集群中 65 个 Pod 中，59 个 Running 正常，但我发现了一个异常 Pod。让我进一步查看这个 Pod 的详细信息。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                              READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-volume-configmap-missing-key   0/1     ContainerCreating   
   💭 [问题定位] 这个 Pod 处于 `ContainerCreating` 状态，且 label 标记了 `pod_abnormal_type=VolumeMountFailed`。让我获取相应 runbook 并进一步查看详情。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  15s (x15 over 14m)   kubelet            MountVolume
   💭 [问题定位] 现在我已经掌握了所有需要的信息。让我输出分析结果。
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 TodoWrite 输出摘要: raw_chars=287 lines=7
Investigation plan updated with 3 tasks.
# CURRENT INVESTIGATION TASKS
**Task Status**: 3 completed, 0 in progress, 0 pending
[✓] [1] 全局扫描集群 Pod 状态，识别所有异常 Pod
[✓]
   💭 [问题定位] ## 集群状态定位分析

### 全局概览
- **总 Pod 数**: 65
- **正常运行 Pod**: 59 个（Running）
- **异常 Pod**: 1 个

### 发现的异常 Pod

| Pod | 命名空间 | 状态 | 异常类型 |
|-----|---------|------|---------|
| `rc-volume-configmap-missing-key` | aiops-e2e | ContainerCreating（Pending） | **VolumeMountFailed** |

---

### 异常详情：`rc-volume-configmap-missing-key`

**当前状态**：`Pending` → `ContainerCreating`，0/1 Ready

**关键事件**：
```
MountVolume.SetUp failed for volume "config-volume" : 
configmap references non-existent config key: missing-key
```

**根因分析**：
该 Pod 引用了名为 `rc-volume-key-config` 的 ConfigMap 作为 volume（卷名 `config-volume`），但 ConfigMap 中并不存在名为 `missing-key` 的配置键（key）。由于 volume 的 `Optional: false`（非可选），kubelet 无法挂载该卷，导致 Pod 卡在 ContainerCreating 状态。

---

### 输出结构

| 字段 | 值 |
|------|-----|
| **layer** | L0 |
| **layer_name** | 卷挂载失败 - ConfigMap key 不存在 |
| **pod_status_keyword** | ContainerCreating |
| **pod_abnormal_type** | VolumeMountFailed |
| **status_category** | storage_volume |
| **confidence** | 高 |
| **abnormal_pods** | [`aiops-e2e/rc-volume-configmap-missing-key`] |
| **abnormal_groups** | VolumeMountFailed |
| **兼容层 layers** | [L0] |

**推理**：Events 明确显示 `configmap references non-existent config key: missing-key`，Pod 状态为 ContainerCreating，匹配 VolumeMountFailed 异常类型，属于存储/卷挂载问题，归入 L0 层。

**后续审查方向**：检查 ConfigMap `rc-volume-key-config` 中是否包含 `missing-key` 这个键，若确实缺失，则需在 ConfigMap 中添加该键，或修改 Pod volume 配置引用正确的键名。
   ✅ [问题定位] 完成 (15.9s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[{'scenario': 'ConfigMap 中缺少 Pod volume 引用的 key', 'probability': '高', 'reason': 'Event 明确提示 configmap references non-existent config key: missing-key'}]
   entities=[{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}, {"type": "Volume", "name": "config-volume", "namespace": "aiops-e2e"}]
   reasoning=Pod rc-volume-configmap-missing-key 处于 ContainerCreating/Pending 状态，Event 明确显示 MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key。Pod volumes 引用 ConfigMap rc-volume-key-config 且 Optional: false，但 ConfigMap 中缺失 key missing-key。根因为存储/卷挂载失败，符合 VolumeMountFailed 异常类型，归入 L0 层。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "卷挂载失败 - ConfigMap key 不存在", "confidence": 0.98, "reasoning": "Pod rc-volume-configmap-missing-key 处于 ContainerCreating/Pending 状态，Event 明确显示 MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key。Pod volumes 引用 ConfigMap rc-volume-key-config 且 Optional: false，但 ConfigMap 中缺失 key missing-key。根因为存储/卷挂载失败，符合 VolumeMountFailed 异常类型，归入 L0 层。", "abnormal_pods": [{"name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}, {"type": "Volume", "name": "config-volume", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "ConfigMap 中缺少 Pod volume 引用的 key", "probability": "高", "reason": "Event 明确提示 configmap references non-existent config key: missing-key"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-volume-configmap-missing-key                     0/1     ContainerCreating   0              14m     <none>           node1    <none>           <none>            app=rc-volume-configmap-missing-key,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/a06049aeb9c24dfe/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/a06049aeb9c24dfe/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/a06049aeb9c24dfe/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 98%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我来执行既有 evidence_plan 中的关键工具调用。先并行执行前三个不需要依赖的工具：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
creationTimestamp: 2026-05-21T04:29:04Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
final
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  33s (x15 over 14m)  kubelet            MountVolume.
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: ConfigMap
name: rc-volume-key-config
namespace: aiops-e2e
   💭 [证据链采集] 注意到 `kubectl_get_yaml configmap` 的输出中没有显示 `data` 字段，我需要查看完整内容来确认是否包含 key `missing-key`。让我用更详细的方式获取 ConfigMap 内容，同时采集 events。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "apiVersion: v1\ndata:\n  existing-key: present\nkind: ConfigMap\nmetadata:\n  annotations:\n    kubectl.kubernetes.io/last-applied-configuration: |\n      {\"apiVersion\":
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
35s (x15 over 14m)   Warning   FailedMount   Pod/rc-volume-configmap-missing-key   MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent con
   💭 [证据链采集] 所有关键证据已采集完成。以下是证据结论：

---

## ✅ 已采集证据

### 🔴 证据 e1 — `kubectl describe pod`（critical ✅）
- **Pod 状态**: `Pending`（Waiting Reason=ContainerCreating）
- **核心错误事件**: `MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key`
- **Volume 配置**: `config-volume` → ConfigMap `rc-volume-key-config`，**Optional: false**
- 15 次重复出现，持续 14 分钟，根因稳定不抖动

### 🔴 证据 e2 — `kubectl get pod -o yaml`（critical ✅）
- `.spec.volumes[].configMap.name` = `rc-volume-key-config`
- 验证了 volume 类型为 ConfigMap，且没有任何额外 PVC/PV/CSI/NFS 引用

### 🔴 证据 e3 — `kubectl get configmap -o yaml`（critical ✅）
- ConfigMap `rc-volume-key-config` **存在**，但仅包含一个 key: `existing-key`
- **缺失 key**: `missing-key`（Pod volume 引用的 key 在 ConfigMap 中不存在）
- 确认 ConfigMap 本身存在，不是"对象缺失"问题，而是"引用的 key 缺失"问题

### 🟡 证据 e4 — `kubectl_events`（important ✅）
- 事件时间线: 最近 33s 内仍有 FailedMount 事件
- 错误原文: `configmap references non-existent config key: missing-key`
- 与 describe 结果一致，确认故障持续活跃中

---

## 📋 证据结论

**根因**: Pod `rc-volume-configmap-missing-key` volume `config-volume` 引用了 ConfigMap `rc-volume-key-config` 中的 key `missing-key`，但该 ConfigMap 中实际只存在 key `existing-key`，**缺少 `missing-key`**。由于 volume 配置 `Optional: false`，kubelet 严格校验必须存在该 key，导致挂载失败，Pod 卡在 `Pending/ContainerCreating`。

**异常归类**: **VolumeMountFailed — ConfigMap volume key 缺失** ✅，与上游 L0 定位完全一致。

**修复建议**: 在 ConfigMap `rc-volume-key-config` 中添加 key `missing-key`，或将 Pod volume 的 `Optional` 设为 `true`。
   ✅ [证据链采集] 完成 (14.3s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"Describe Pod rc-volume-configmap-missing-key in aiops-e2e to capture current Events and status","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e"},"purpose":"验证Pod当前状态和FailedMount事件是否仍存在","evidence_type":"pod_event","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"Get Pod YAML to check volumes spec and ConfigMap reference","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml"},"purpose":"验证volumes[].configMap引用和optional设置","evidence_type":"pod_spec","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"Get ConfigMap rc-volume-key-config to verify it exists and check keys","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml","tool_args":{"kind":"configmap","name":"rc-volume-key-config","namespace":"aiops-e2e","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml"},"purpose":"验证ConfigMap是否存在以及是否包含Pod引用的key","evidence_type":"configmap_volume","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e4","description":"Get Events in aiops-e2e namespace for the pod to confirm FailedMount details","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-configmap-missing-key --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-volume-configmap-missing-key"},"purpose":"采集FailedMount事件的详细时间线和错误原文","evidence_type":"pod_event","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T04:29:04Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-configmap-missing-key, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"config-volume\", \"configMap\": \"rc-volume-key-config\"}\n- {\"name\": \"kube-api-access-fbhds\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a06049aeb9c24dfe/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a06049aeb9c24dfe/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a06049aeb9c24dfe/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  33s (x15 over 14m)  kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n  Warning  FailedMount  6m4s (x3 over 12m)  kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition\n  Warning  FailedMount  93s (x3 over 10m)   kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-fbhds config-volume]: timed out waiting for the condition\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  config-volume:\n    Type:      ConfigMap (a volume populated by a ConfigMap)\n    Name:      rc-volume-key-config\n    Optional:  false\n  kube-api-access-fbhds:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedMount  6m4s (x3 over 12m)  kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition\n  Warning  FailedMount  93s (x3 over 10m)   kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-fbhds config-volume]: timed out waiting for the condition\n  Warning  FailedMount  33s (x15 over 14m)  kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a06049aeb9c24dfe/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a06049aeb9c24dfe/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a06049aeb9c24dfe/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: ConfigMap\nname: rc-volume-key-config\nnamespace: aiops-e2e","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a06049aeb9c24dfe/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a06049aeb9c24dfe/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a06049aeb9c24dfe/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"apiVersion: v1\\ndata:\\n  existing-key: present\\nkind: ConfigMap\\nmetadata:\\n  annotations:\\n    kubectl.kubernetes.io/last-applied-configuration: |\\n      {\\\"apiVersion\\\":\\\"v1\\\",\\\"data\\\":{\\\"existing-key\\\":\\\"present\\\"},\\\"kind\\\":\\\"ConfigMap\\\",\\\"metadata\\\":{\\\"annotations\\\":{},\\\"labels\\\":{\\\"rootcause-e2e\\\":\\\"true\\\"},\\\"name\\\":\\\"rc-volume-key-config\\\",\\\"namespace\\\":\\\"aiops-e2e\\\"}}\\n  creationTimestamp: \\\"2026-05-21T04:29:04Z\\\"\\n  labels:\\n    rootcause-e2e: \\\"true\\\"\\n  name: rc-volume-key-config\\n  namespace: aiops-e2e\\n  resourceVersion: \\\"52517160\\\"\\n  uid: 5468219a-cec8-424b-b490-66fd39c82b58\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a06049aeb9c24dfe/tools/004-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a06049aeb9c24dfe/tools/004-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a06049aeb9c24dfe/tools/004-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n35s (x15 over 14m)   Warning   FailedMount   Pod/rc-volume-configmap-missing-key   MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n6m6s (x3 over 12m)   Warning   FailedMount   Pod/rc-volume-configmap-missing-key   Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition\n95s (x3 over 10m)    Warning   FailedMount   Pod/rc-volume-configmap-missing-key   Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-fbhds config-volume]: timed out waiting for the condition","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a06049aeb9c24dfe/tools/005-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a06049aeb9c24dfe/tools/005-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a06049aeb9c24dfe/tools/005-evidence-kubectl_events.summary.txt"}],"llm_analysis":"所有关键证据已采集完成。以下是证据结论：\n\n---\n\n## ✅ 已采集证据\n\n### 🔴 证据 e1 — `kubectl describe pod`（critical ✅）\n- **Pod 状态**: `Pending`（Waiting Reason=ContainerCreating）\n- **核心错误事件**: `MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key`\n- **Volume 配置**: `config-volume` → ConfigMap `rc-volume-key-config`，**Optional: false**\n- 15 次重复出现，持续 14 分钟，根因稳定不抖动\n\n### 🔴 证据 e2 — `kubectl get pod -o yaml`（critical ✅）\n- `.spec.volumes[].configMap.name` = `rc-volume-key-config`\n- 验证了 volume 类型为 ConfigMap，且没有任何额外 PVC/PV/CSI/NFS 引用\n\n### 🔴 证据 e3 — `kubectl get configmap -o yaml`（critical ✅）\n- ConfigMap `rc-volume-key-config` **存在**，但仅包含一个 key: `existing-key`\n- **缺失 key**: `missing-key`（Pod volume 引用的 key 在 ConfigMap 中不存在）\n- 确认 ConfigMap 本身存在，不是\"对象缺失\"问题，而是\"引用的 key 缺失\"问题\n\n### 🟡 证据 e4 — `kubectl_events`（important ✅）\n- 事件时间线: 最近 33s 内仍有 FailedMount 事件\n- 错误原文: `configmap references non-existent config key: missing-key`\n- 与 describe 结果一致，确认故障持续活跃中\n\n---\n\n## 📋 证据结论\n\n**根因**: Pod `rc-volume-configmap-missing-key` volume `config-volume` 引用了 ConfigMap `rc-volume-key-config` 中的 key `missing-key`，但该 ConfigMap 中实际只存在 key `existing-key`，**缺少 `missing-key`**。由于 volume 配置 `Optional: false`，kubelet 严格校验必须存在该 key，导致挂载失败，Pod 卡在 `Pending/ContainerCreating`。\n\n**异常归类**: **VolumeMountFailed — ConfigMap volume key 缺失** ✅，与上游 L0 定位完全一致。\n\n**修复建议**: 在 ConfigMap `rc-volume-key-config` 中添加 key `missing-key`，或将 Pod volume 的 `Optional` 设为 `true`。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 8 个，匹配计划 4 个，未规划证据 4 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":4,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"Describe Pod rc-volume-configmap-missing-key in aiops-e2e to capture current Events and status","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","purpose":"验证Pod当前状态和FailedMount事件是否仍存在","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"Get Pod YAML to check volumes spec and ConfigMap reference","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","purpose":"验证volumes[].configMap引用和optional设置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"Get ConfigMap rc-volume-key-config to verify it exists and check keys","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml","purpose":"验证ConfigMap是否存在以及是否包含Pod引用的key","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"Get Events in aiops-e2e namespace for the pod to confirm FailedMount details","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-configmap-missing-key --sort-by='.lastTimestamp'","purpose":"采集FailedMount事件的详细时间线和错误原文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | Describe Pod rc-volume-configmap-missing-key ... | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_yaml | Get Pod YAML to check volumes spec and Config... | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml` |
   | e3 | critical | ✅ | kubectl_get_yaml | Get ConfigMap rc-volume-key-config to verify ... | `kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml` |
   | e4 | important | ✅ | kubectl_events | Get Events in aiops-e2e namespace for the pod... | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volum...` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (14.1s)
   📤 → 下游数据: root_cause=根因为 ConfigMap 缺失 key。Pod aiops-e2e/rc-volume-configmap-missing-key 的 volume config-volume 引用 ConfigMap rc-volume-key-config（Optional: false），但该 ConfigMap 中仅有 existing-key 一个 key，缺少 missing-key。kubelet 严格验证后拒绝挂载，报错 'MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key'（15 次重复，持续 14 分钟），Pod 卡在 Pending/ContainerCreating。集群其他 59 个 Pod 均正常运行。
   confidence=98%
   causal_chain={"root_cause": "ConfigMap rc-volume-key-config 中缺失 Pod volume config-volume 引用的 key missing-key，且 volume 属性 Optional: false（严格模式）", "propagation": "kubelet 在挂载 config-volume 时校验 ConfigMap key → 发现 missing-key 不存在 → 挂载失败返回 FailedMount 事件 → 卷挂载一直无法完成 → 依赖该卷的所有容器无法启动 → Pod 卡在 Pending/ContainerCreating", "direct_cause": "Volume config-volume (ConfigMap 类型) 挂载失败，因 ConfigMap rc-volume-key-config 缺少 key missing-key", "manifestation": "Pod rc-volume-configmap-missing-key 处于 Pending 状态，容器 Waiting Reason=ContainerCreating，kubelet 重复报 Warning FailedMount"}
   rca_analysis={"phenomenon": "Pod aiops-e2e/rc-volume-configmap-missing-key 处于 Pending 状态（容器 Waiting Reason=ContainerCreating），持续 14 分钟未就绪，集群仅此一个异常 Pod。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod 状态 Pending，核心 Event: MountVolume.SetUp failed for volume \"config-volume\": configmap references non-existent config key: missing-key，15 次重复，持续 14 分钟", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml (Pod)", "content": "Pod volume config-volume 引用 ConfigMap rc-volume-key-config，Optional: false", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_yaml (ConfigMap)", "content": "ConfigMap rc-volume-key-config 存在，仅包含 key existing-key，缺失 key missing-key", "reliability": "高"}, {"id": "e4", "source": "kubectl_events", "content": "35s 前仍有 FailedMount 事件，错误原文一致：configmap references non-existent config key: missing-key", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "集群 65 Pod 中 59 个 Running，仅此 1 个异常（ContainerCreating）", "reliability": "高"}, {"id": "layer_2", "source": "kubectl_get_by_name", "content": "Pod 状态 ContainerCreating，无 IP，调度在 node1", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key", "interpretation": "kubelet 明确报告 volume config-volume 挂载失败，原因是 ConfigMap 中引用的 key missing-key 不存在。15 次重复说明故障稳定持续。"}, {"evidence_id": "e2", "raw_data": "volumes: [{\"name\":\"config-volume\",\"configMap\":\"rc-volume-key-config\"}]", "interpretation": "Pod spec 确认 config-volume 类型为 ConfigMap，引用 ConfigMap rc-volume-key-config，且 Optional: false（默认），kubelet 严格校验 key 必须存在。"}, {"evidence_id": "e3", "raw_data": "data: existing-key: present", "interpretation": "ConfigMap rc-volume-key-config 确实存在且包含数据，但仅有 existing-key 一个 key。缺失的 missing-key 正是 Pod 引用的 key，直接匹配 e1 错误信息。"}, {"evidence_id": "e4", "raw_data": "35s (x15 over 14m) Warning FailedMount Pod/rc-volume-configmap-missing-key MountVolume.SetUp failed...", "interpretation": "时间戳最近 35s 内仍有事件，确认故障当前活跃，非历史记录。与 e1 互相印证。"}, {"evidence_id": "layer_1", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59}", "interpretation": "集群整体健康，仅此一个异常 Pod，不影响其他 59 个 Pod，问题范围明确。"}, {"evidence_id": "layer_2", "raw_data": "0/1 ContainerCreating 0 14m <none> node1", "interpretation": "Pod 未获得 IP，调度到 node1 但无法启动，与卷挂载失败一致——容器创建前需完成卷挂载。"}], "causal_chain": {"root_cause": "ConfigMap rc-volume-key-config 中缺失 Pod volume config-volume 引用的 key missing-key，且 volume 属性 Optional: false（严格模式）", "propagation": "kubelet 在挂载 config-volume 时校验 ConfigMap key → 发现 missing-key 不存在 → 挂载失败返回 FailedMount 事件 → 卷挂载一直无法完成 → 依赖该卷的所有容器无法启动 → Pod 卡在 Pending/ContainerCreating", "direct_cause": "Volume config-volume (ConfigMap 类型) 挂载失败，因 ConfigMap rc-volume-key-config 缺少 key missing-key", "manifestation": "Pod rc-volume-configmap-missing-key 处于 Pending 状态，容器 Waiting Reason=ContainerCreating，kubelet 重复报 Warning FailedMount"}, "root_cause": "根因为 ConfigMap 缺失 key。Pod aiops-e2e/rc-volume-configmap-missing-key 的 volume config-volume 引用 ConfigMap rc-volume-key-config（Optional: false），但该 ConfigMap 中仅有 existing-key 一个 key，缺少 missing-key。kubelet 严格验证后拒绝挂载，报错 'MountVolume.SetUp failed for volume \\\"config-volume\\\" : configmap references non-existent config key: missing-key'（15 次重复，持续 14 分钟），Pod 卡在 Pending/ContainerCreating。集群其他 59 个 Pod 均正常运行。", "root_cause_summary": "根因为 ConfigMap 缺失 key。Pod aiops-e2e/rc-volume-configmap-missing-key 的 volume config-volume 引用 ConfigMap rc-volume-key-config（Optional: false），但该 ConfigMap 中仅有 existing-key 一个 key，缺少 missing-key。kubelet 严格验证后拒绝挂载，报错 'MountVolume.SetUp failed for volume \\\"config-volume\\\" : configmap references non-existent config key: missing-key'（15 次重复，持续 14 分钟），Pod 卡在 Pending/ContainerCreating。集群其他 59 个 Pod 均正常运行。", "confidence": 0.98, "confidence_reason": "有直接证据链：Pod spec 明确引用 ConfigMap 和 key（e2）→ Event 明确报错缺失 key（e1/e4）→ ConfigMap 内容确认缺失该 key（e3）。三级证据互相印证，因果链完整闭合，无歧义。置信度 0.98。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [{"cause": "ConfigMap 对象不存在", "probability": "low", "reason": "证据 e3 确认 ConfigMap rc-volume-key-config 存在于 aiops-e2e namespace，不是对象缺失"}, {"cause": "PVC/PV 存储问题", "probability": "low", "reason": "证据 e2 确认 volume 类型为 ConfigMap，非 PVC/PV/CSI/NFS，已排除存储基础设施问题"}, {"cause": "节点资源不足", "probability": "low", "reason": "Event 未报资源不足错误，节点 node1 上其他 Pod 正常运行；QoS Class BestEffort 无资源约束"}], "limitations": "未采集 ConfigMap 完整 YAML 的 data 字段内容以确认 missing-key 是否被删除或从未创建（当前仅采集到 existing-key: present），但错误信息已足够定位。未采集 ConfigMap 的历史事件确认 missing-key 何时被移除，不影响根因判断。", "llm_raw_analysis": "L0 根因分析完成。证据链完整：Pod spec → volume config-volume 引用 ConfigMap rc-volume-key-config（Optional: false）→ Event 报 missing-key 不存在 → ConfigMap 内容确认仅含 existing-key。根因为 ConfigMap key 缺失。集群仅此一个异常 Pod，不影响全局。上游 L0 层 primary_problem 结论完全正确，本分析进一步通过 ConfigMap 内容验证确认了 key 缺失的具体情况。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 根因为 ConfigMap 缺失 key。Pod aiops-e2e/rc-volume-configmap-missing-key 的 volume config-volume 引用 ConfigMap rc-volume-key-config（Optional: false），但该 Config...
   置信度: 98%
   🔗 因果链:
     根本原因: ConfigMap rc-volume-key-config 中缺失 Pod volume config-volume 引用的 key missing-key，且 volume 属性 Optional: false（严格模式）
     传导机制: kubelet 在挂载 config-volume 时校验 ConfigMap key → 发现 missing-key 不存在 → 挂载失败返回 FailedMount 事件 → 卷挂载一直无法完成 → 依赖该卷的所有容器无法启动 → Pod 卡在 Pending/ContainerCreating
     最终表现: Pod rc-volume-configmap-missing-key 处于 Pending 状态，容器 Waiting Reason=ContainerCreating，kubelet 重复报 Warning FailedMount


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (15.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6122 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 59.7s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，以下是基于您提供的完整诊断分析生成的详尽诊断报告。

---
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **集群整体状态** | 集群共 65 个 Pod，其中 59 个正常运行，1 个异常 |
| **Pod异常状态** | ContainerCreating / Pending (VolumeMountFailed) |
| **兼容归因层** | L0 |
| **问题分类** | `VolumeMountFailed` - ConfigMap Key 缺失 |
| **置信度** | 高 (98%) |
| **证据完整度** | 4/4 (100%) |
---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 受影响 Pod | `rc-volume-configmap-missing-key` |
| Namespace | `aiops-e2e` |
| 节点 | `node1` |
| 错误信息 | `MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key` |
---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` | `STATUS: ContainerCreating`，`READY: 0/1` | Pod 无法进入 Running 状态，卡在容器创建阶段 |
| 2 | Pod 详细状态 | `kubectl describe pod` | `status: Pending`, `Reason: ContainerCreating`, `Ready: False` | Pod 持续处于 Pending/ContainerCreating 状态 |
| 3 | Pod 事件 | `kubectl describe pod` / `kubectl events` | `Warning FailedMount 33s (x15 over 14m) kubelet MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key` | kubelet 明确报告 ConfigMap 中缺少 key `missing-key`，导致卷挂载失败 |
| 4 | 卷挂载超时事件 | `kubectl describe pod` | `Warning FailedMount 6m4s (x3 over 12m) kubelet Unable to attach or mount volumes: unmounted volumes=[config-volume], ...: timed out waiting for the condition` | 由于卷挂载失败，挂载操作最终超时 |
| 5 | Pod YAML 配置 | `kubectl get pod -o yaml` | `volumes: config-volume (ConfigMap: rc-volume-key-config)` | Pod 引用了名为 `rc-volume-key-config` 的 ConfigMap 作为卷 |
| 6 | ConfigMap 内容 | `kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml` | `data: existing-key: present` | 该 ConfigMap 只存在 `existing-key` 一个键，**缺少 `missing-key`** |
| 7 | 容器命令 | `kubectl get pod -o yaml` | `command: sh -c sleep 3600` | 容器本身是用于测试的简单命令，非业务应用问题 |
### 证据关联分析
- **证据 #3 + 证据 #6 印证**：Pod 的 Event 明确指出 `configmap references non-existent config key: missing-key`，直接查验 ConfigMap 内容后确认确实缺少该键，问题原因锁定。
- **证据链**：Pod 的 Volume 配置引用 ConfigMap `rc-volume-key-config` 并指定 key `missing-key` → kubelet 试图挂载时在 ConfigMap 中找不到该 key → 挂载失败，上报 Warning 事件 → 容器无法创建 → Pod 卡在 `ContainerCreating` 状态。
### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| ConfigMap 历史事件/变更记录 | low | 无法确定 `missing-key` 是最初未创建还是后续被删除，但不影响根因判断和修复 |
---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                                │
│ ConfigMap `rc-volume-key-config` 中未包含 Pod 的 Volume 配置引用的 key `missing-key`。    │
│ (ConfigMap 中仅存在 `existing-key`)                                                      │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                          ↓
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                                │
│ kubelet 在挂载 `config-volume` (ConfigMap 类型) 时，检查 ConfigMap `rc-volume-key-config`│
│ → 发现 key `missing-key` 不存在 → 挂载失败                                             │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                          ↓
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                                │
│ Volume 挂载失败，kubelet 报告错误：`MountVolume.SetUp failed for volume "config-volume" │
│ : configmap references non-existent config key: missing-key`                            │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                          ↓
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                            │
│ Pod `rc-volume-configmap-missing-key` 状态为 `Pending` / `ContainerCreating`，            │
│ 持续无法变为 Running 状态                                                               │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #3 (kubelet 报错 ConfigMap 缺失 key) 和证据 #6 (ConfigMap 内容确认缺少 key)，问题的根本原因是 **Pod `rc-volume-configmap-missing-key` 引用的 ConfigMap `rc-volume-key-config` 中不包含所配置的 key `missing-key`**。由于 Pod 的 Volume 配置默认为 `Optional: false`，即该 key 必须存在，因此 kubelet 严格校验失败，导致卷挂载卡住，Pod 无法启动。

**置信度**：高 (98%)
- ✅ Event 和 ConfigMap 内容双重确认根本原因
- ✅ 集群内其他 59 个 Pod 均正常，排除集群级故障
- ✅ 容器工作负载是简单的 `sleep 3600`，排除应用自身问题

### 已排除候选原因
- **Finalizer 未清理**：已排除。工具输出显示 `finalizers: <none>`。
- **kubelet/节点不可达**：已排除。节点 `node1` 正常工作，且集群中在该节点上的其他 Pod 正常运行。
---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [首选] 将缺失的 key `missing-key` 添加到 ConfigMap 中**
此操作将直接解决根本问题，Pod 将会自动进入 `Running` 状态。
```bash
kubectl patch configmap rc-volume-key-config -n aiops-e2e -p '{"data":{"missing-key":"<your-desired-value>"}}'
```
*依据*：根本原因是 ConfigMap 缺少 key，补充后 kubelet 将能成功挂载。
**2. [备选] 如果该 key 是误配，修改 Pod 的 Volume 配置**
如果确认 `missing-key` 是误配置，应更新引用此 ConfigMap 的 Deployment 或 StatefulSet。假设这是一个 `ReplicationController`，可执行以下命令：
```bash
kubectl edit rc rc-volume-configmap-missing-key -n aiops-e2e
```
将 Pod 模板中 volume `config-volume` 的 `items` 下列表中的 `missing-key` 删除或替换为 `existing-key`。
*依据*：如果 key 是误配，应从 Pod 配置中移除其引用。
### 后续优化
1. **规范管理**：在创建引用 ConfigMap key 的 Pod 时，确保 ConfigMap 已包含所有必要的 key。
2. **变更审核**：对 ConfigMap 的变更应经过审核，避免删除或修改被 Pod 引用的 key。
---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 更新 ConfigMap | 执行**修复建议 1** 的命令 | 无错误返回 |
| 2. 检查 Pod 状态 | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e` | `STATUS: Running (或 ContainerCreating → Running)` |
| 3. 确认 Pod 就绪 | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e` | `READY: 1/1` |
| 4. 检查不再有 FailedMount 事件 | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` | Events 中不再出现 `FailedMount` |
---
## ⚠️ 注意事项
- 本报告完全基于测试环境设计的问题进行诊断，修复命令中 `missing-key` 的值需替换为实际期望的值。

---

## 📊 性能统计

├─ 总耗时: 59.7s
├─ 问题定位: 15.9s (27%) ✅
├─ 证据链采集: 14.3s (24%) ✅
├─ 根因分析: 14.1s (24%) ✅
├─ 汇总总结: 15.5s (26%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 10 次
```

📋 诊断追踪

- **核心 Runbook**: pod-volume-mount-failed
- **参考 Runbook**: pod-volume-mount-failed
- **工具调用**: 10 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
