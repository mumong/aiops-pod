======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 18e455a7144546c5]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先进行全局 Pod 状态扫描，看看集群中当前有哪些异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59}
NAMESPACE         NAME                                                READY   STATUS              RESTARTS       A
   💭 [问题定位] 扫描结果很清楚，发现了一个异常 Pod。让我查看它的详情。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  73s (x15 over 15m)   kubelet            MountVolume
   💭 [问题定位] 现在根据异常类型匹配 runbook。该 Pod 的异常类型是 VolumeMountFailed，让我获取对应的 runbook。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] 现在我已经有了足够的定位信息，来完成分析。

## 定位分析结果

### 全局异常 Pod 扫描

| 范围 | 总数 | 正常 | 异常 |
|------|------|------|------|
| 全集群 Pod | 65 | 64（Running=59, Completed?=5） | **1** |

### 异常 Pod 详情

| Pod | 命名空间 | Status | 异常类型 |
|-----|---------|--------|---------|
| `rc-volume-configmap-missing-key` | `aiops-e2e` | ContainerCreating / Pending | **VolumeMountFailed** |

### 根因分析

通过 `kubectl describe` 查看 Events，核心错误信息：

> **`MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key`**

这个 Pod 的定义中，`volumes[0]` 是一个 **ConfigMap 类型卷**，引用了名为 `rc-volume-key-config` 的 ConfigMap，但该 ConfigMap 中**不存在名为 `missing-key` 的键**。

Pod 状态卡在 `ContainerCreating`，卷无法挂载完成，因此一直无法进入 Running。

### 输出结构化结果

```json
{
  "layer": "L0",
  "derived_layer": "L0",
  "layers": ["L0"],
  "layer_name": "VolumeMountFailed — ConfigMap key 缺失",
  "confidence": 0.98,
  "reasoning": "Pod rc-volume-configmap-missing-key 卡在 ContainerCreating/Pending，Events 明确报错 MountVolume.SetUp failed: configmap references non-existent config key: missing-key，符合 L0 VolumeMountFailed 归因",
  "abnormal_pods": ["aiops-e2e/rc-volume-configmap-missing-key"],
  "abnormal_groups": ["VolumeMountFailed"],
  "pod_status_keyword": "ContainerCreating",
  "pod_abnormal_type": "VolumeMountFailed",
  "status_category": "storage_volume",
  "key_entities": {
    "Pod": "rc-volume-configmap-missing-key",
    "Namespace": "aiops-e2e",
    "Volume": "config-volume",
    "ConfigMap": "rc-volume-key-config",
    "MissingKey": "missing-key"
  },
  "possible_scenarios": [
    "ConfigMap 'rc-volume-key-config' 中缺少 'missing-key' 这个 key，Pod 引用了不存在的配置键",
    "ConfigMap 可能已存在但内容不完整，需要补全缺失的 key",
    "如果 Pod 模板中写错了 key 名称，需要修正 Pod spec 中的 key 引用"
  ]
}
```

### 问题总结

你的集群中当前存在 **1 个异常 Pod**，属于 **L0 层 VolumeMountFailed** 类型：

- **Pod**: `rc-volume-configmap-missing-key`（命名空间：`aiops-e2e`）
- **问题**: Pod 引用的 ConfigMap 卷 `config-volume` 中指定的 key `missing-key` 在 ConfigMap `rc-volume-key-config` 中不存在，导致卷挂载失败，Pod 卡在 `ContainerCreating`
- **后续审查方向**: 检查 `ConfigMap rc-volume-key-config` 的内容，确认所需的 `missing-key` 是否正确拼写，或向 ConfigMap 中添加该 key
   ✅ [问题定位] 完成 (14.4s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[{'scenario': "ConfigMap 'rc-volume-key-config' 中缺少 'missing-key' 这个 key，Pod 引用了不存在的配置键", 'probability': '高', 'reason': "Events 明确报错 'configmap references non-existent config key: missing-key'"}, {'scenario': 'Pod spec 中 volume key 名称拼写错误，需要修正 Pod 模板中的 key 引用', 'probability': '中', 'reason': '如果 ConfigMap 中实际存在的是其他 key 名称，则需修正 Pod spec'}, {'scenario': 'ConfigMap 内容不完整，需要补全缺失的 key', 'probability': '中', 'reason': 'ConfigMap 存在但缺少 Pod 引用的 key'}]
   entities=[{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}, {"type": "Volume", "name": "config-volume", "namespace": "aiops-e2e"}]
   reasoning=Pod rc-volume-configmap-missing-key (aiops-e2e) 状态为 ContainerCreating/Pending，kubectl describe Events 明确报错 'MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key'，Pod spec volumes[0] 引用 ConfigMap 'rc-volume-key-config'，但该 ConfigMap 不存在 key 'missing-key'，导致卷挂载失败。符合 L0 VolumeMountFailed 归因（storage_volume）。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "VolumeMountFailed — ConfigMap key 缺失", "confidence": 0.98, "reasoning": "Pod rc-volume-configmap-missing-key (aiops-e2e) 状态为 ContainerCreating/Pending，kubectl describe Events 明确报错 'MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key'，Pod spec volumes[0] 引用 ConfigMap 'rc-volume-key-config'，但该 ConfigMap 不存在 key 'missing-key'，导致卷挂载失败。符合 L0 VolumeMountFailed 归因（storage_volume）。", "abnormal_pods": [{"name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}, {"type": "Volume", "name": "config-volume", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "ConfigMap 'rc-volume-key-config' 中缺少 'missing-key' 这个 key，Pod 引用了不存在的配置键", "probability": "高", "reason": "Events 明确报错 'configmap references non-existent config key: missing-key'"}, {"scenario": "Pod spec 中 volume key 名称拼写错误，需要修正 Pod 模板中的 key 引用", "probability": "中", "reason": "如果 ConfigMap 中实际存在的是其他 key 名称，则需修正 Pod spec"}, {"scenario": "ConfigMap 内容不完整，需要补全缺失的 key", "probability": "中", "reason": "ConfigMap 存在但缺少 Pod 引用的 key"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-volume-configmap-missing-key                     0/1     ContainerCreating   0              15m     <none>           node1    <none>           <none>            app=rc-volume-configmap-missing-key,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/18e455a7144546c5/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/18e455a7144546c5/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/18e455a7144546c5/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 98%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来按照既有 evidence_plan 执行工具调用，采集真实环境证据。首先执行所有 critical 级别的工具（互不依赖，可并行）：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: ConfigMap
name: rc-volume-key-config
namespace: aiops-e2e
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
  Warning  FailedMount  91s (x15 over 15m)   kubelet            MountVolume
   💭 [证据链采集] 现在获取 ConfigMap 的完整 YAML 内容来确认是否包含缺失的 key：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
93s (x15 over 15m)    Warning   FailedMount   Pod/rc-volume-configmap-missing-key   MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent co
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "apiVersion: v1\ndata:\n  existing-key: present\nkind: ConfigMap\nmetadata:\n  annotations:\n    kubectl.kubernetes.io/last-applied-configuration: |\n      {\"apiVersion\":
   💭 [证据链采集] 所有证据已采集完毕。以下是最终结论：

---

## 证据采集结论

### ✅ 已采集的证据（共 4 项）

| 证据 | 来源 | 结论 |
|------|------|------|
| **Pod 状态验证** | `kubectl describe pod` | Pod `rc-volume-configmap-missing-key` 处于 **Pending** 状态，容器 Waiting(ContainerCreating)，QoS BestEffort |
| **Pod Events 原文** | `kubectl describe pod` / `kubectl_events` | **关键证据**：`MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key`（重复出现 15 次） |
| **Pod spec volumes** | `kubectl_get_yaml` | volume `config-volume` 类型为 ConfigMap，引用 ConfigMap `rc-volume-key-config`，**非 optional**（必须存在） |
| **ConfigMap 内容验证** | `kubectl get configmap -o yaml` | ConfigMap `rc-volume-key-config` **存在**，但 data 中**只有** `existing-key: present`，**缺少** Pod 引用的 key `missing-key` |

### 冲突/负向证据
- 无冲突证据；所有目标对象均真实存在于 `aiops-e2e` 命名空间。

### 根因判定
**Pod 卷挂载失败**（VolumeMountFailed）→ ConfigMap `rc-volume-key-config` 中不存在 key `missing-key`，而 Pod spec 中 volume `config-volume` 引用了该 key 且 `optional: false`，导致 kubelet 无法挂载 ConfigMap 卷，Pod 卡在 ContainerCreating/Pending。
   ✅ [证据链采集] 完成 (12.0s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"ev1","description":"验证异常 Pod 当前状态和完整事件原文 - kubectl describe pod rc-volume-configmap-missing-key","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e"},"purpose":"确认 Pod 当前状态和 FailedMount 事件原文","evidence_type":"current_state_and_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev2","description":"验证 Pod spec 中 volume 引用 - kubectl get pod rc-volume-configmap-missing-key -o yaml","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e"},"purpose":"确认 .spec.volumes[].configMap 引用 ConfigMap 和 key","evidence_type":"spec_volume_reference","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"ev3","description":"验证 ConfigMap 'rc-volume-key-config' 是否存在及其 keys","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml","tool_args":{"kind":"configmap","name":"rc-volume-key-config","namespace":"aiops-e2e"},"purpose":"确认 ConfigMap 存在并检查是否包含 Pod 引用的 key 'missing-key'","evidence_type":"configmap_content","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"ev4","description":"获取 Pod 相关事件确认 FailedMount 详细错误","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-configmap-missing-key --sort-by='.lastTimestamp'","tool_args":{"resource_type":"pod","resource_name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e"},"purpose":"获取完整事件确认 FailedMount 根因","evidence_type":"events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: ConfigMap\nname: rc-volume-key-config\nnamespace: aiops-e2e","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/18e455a7144546c5/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/18e455a7144546c5/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/18e455a7144546c5/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T04:29:04Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-configmap-missing-key, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"config-volume\", \"configMap\": \"rc-volume-key-config\"}\n- {\"name\": \"kube-api-access-fbhds\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/18e455a7144546c5/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/18e455a7144546c5/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/18e455a7144546c5/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  91s (x15 over 15m)   kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n  Warning  FailedMount  2m31s (x3 over 11m)  kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-fbhds config-volume]: timed out waiting for the condition\n  Warning  FailedMount  16s (x4 over 13m)    kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  config-volume:\n    Type:      ConfigMap (a volume populated by a ConfigMap)\n    Name:      rc-volume-key-config\n    Optional:  false\n  kube-api-access-fbhds:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedMount  2m31s (x3 over 11m)  kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-fbhds config-volume]: timed out waiting for the condition\n  Warning  FailedMount  91s (x15 over 15m)   kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n  Warning  FailedMount  16s (x4 over 13m)    kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/18e455a7144546c5/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/18e455a7144546c5/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/18e455a7144546c5/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n93s (x15 over 15m)    Warning   FailedMount   Pod/rc-volume-configmap-missing-key   MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n2m33s (x3 over 11m)   Warning   FailedMount   Pod/rc-volume-configmap-missing-key   Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-fbhds config-volume]: timed out waiting for the condition\n18s (x4 over 13m)     Warning   FailedMount   Pod/rc-volume-configmap-missing-key   Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/18e455a7144546c5/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/18e455a7144546c5/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/18e455a7144546c5/tools/004-evidence-kubectl_events.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"apiVersion: v1\\ndata:\\n  existing-key: present\\nkind: ConfigMap\\nmetadata:\\n  annotations:\\n    kubectl.kubernetes.io/last-applied-configuration: |\\n      {\\\"apiVersion\\\":\\\"v1\\\",\\\"data\\\":{\\\"existing-key\\\":\\\"present\\\"},\\\"kind\\\":\\\"ConfigMap\\\",\\\"metadata\\\":{\\\"annotations\\\":{},\\\"labels\\\":{\\\"rootcause-e2e\\\":\\\"true\\\"},\\\"name\\\":\\\"rc-volume-key-config\\\",\\\"namespace\\\":\\\"aiops-e2e\\\"}}\\n  creationTimestamp: \\\"2026-05-21T04:29:04Z\\\"\\n  labels:\\n    rootcause-e2e: \\\"true\\\"\\n  name: rc-volume-key-config\\n  namespace: aiops-e2e\\n  resourceVersion: \\\"52517160\\\"\\n  uid: 5468219a-cec8-424b-b490-66fd39c82b58\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/18e455a7144546c5/tools/005-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/18e455a7144546c5/tools/005-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/18e455a7144546c5/tools/005-evidence-run_bash_command.summary.txt"}],"llm_analysis":"所有证据已采集完毕。以下是最终结论：\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集的证据（共 4 项）\n\n| 证据 | 来源 | 结论 |\n|------|------|------|\n| **Pod 状态验证** | `kubectl describe pod` | Pod `rc-volume-configmap-missing-key` 处于 **Pending** 状态，容器 Waiting(ContainerCreating)，QoS BestEffort |\n| **Pod Events 原文** | `kubectl describe pod` / `kubectl_events` | **关键证据**：`MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key`（重复出现 15 次） |\n| **Pod spec volumes** | `kubectl_get_yaml` | volume `config-volume` 类型为 ConfigMap，引用 ConfigMap `rc-volume-key-config`，**非 optional**（必须存在） |\n| **ConfigMap 内容验证** | `kubectl get configmap -o yaml` | ConfigMap `rc-volume-key-config` **存在**，但 data 中**只有** `existing-key: present`，**缺少** Pod 引用的 key `missing-key` |\n\n### 冲突/负向证据\n- 无冲突证据；所有目标对象均真实存在于 `aiops-e2e` 命名空间。\n\n### 根因判定\n**Pod 卷挂载失败**（VolumeMountFailed）→ ConfigMap `rc-volume-key-config` 中不存在 key `missing-key`，而 Pod spec 中 volume `config-volume` 引用了该 key 且 `optional: false`，导致 kubelet 无法挂载 ConfigMap 卷，Pod 卡在 ContainerCreating/Pending。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 7 个，匹配计划 4 个，未规划证据 3 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":7,"matched_tool_count":4,"unplanned_tool_count":3,"evidence_inventory":[{"id":"ev1","description":"验证异常 Pod 当前状态和完整事件原文 - kubectl describe pod rc-volume-configmap-missing-key","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","purpose":"确认 Pod 当前状态和 FailedMount 事件原文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev2","description":"验证 Pod spec 中 volume 引用 - kubectl get pod rc-volume-configmap-missing-key -o yaml","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","purpose":"确认 .spec.volumes[].configMap 引用 ConfigMap 和 key","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev3","description":"验证 ConfigMap 'rc-volume-key-config' 是否存在及其 keys","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml","purpose":"确认 ConfigMap 存在并检查是否包含 Pod 引用的 key 'missing-key'","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev4","description":"获取 Pod 相关事件确认 FailedMount 详细错误","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-configmap-missing-key --sort-by='.lastTimestamp'","purpose":"获取完整事件确认 FailedMount 根因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | ev1 | critical | ✅ | kubectl_describe | 验证异常 Pod 当前状态和完整事件原文 - kubectl describe pod r... | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` |
   | ev2 | critical | ✅ | kubectl_get_yaml | 验证 Pod spec 中 volume 引用 - kubectl get pod rc-... | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml` |
   | ev3 | critical | ✅ | kubectl_get_yaml | 验证 ConfigMap 'rc-volume-key-config' 是否存在及其 keys | `kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml` |
   | ev4 | important | ✅ | kubectl_events | 获取 Pod 相关事件确认 FailedMount 详细错误 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volum...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (16.4s)
   📤 → 下游数据: root_cause=Pod rc-volume-configmap-missing-key (aiops-e2e) 卡在 ContainerCreating/Pending 状态的根因是：Pod spec 中 volume "config-volume" 引用 ConfigMap "rc-volume-key-config" 的 key "missing-key"（optional=false），但该 ConfigMap 的 data 中仅包含 "existing-key: present"，不存在 "missing-key"。kubelet 在 15 分钟内重复 15 次报错 "MountVolume.SetUp failed for volume 'config-volume': configmap references non-existent config key: missing-key"，导致卷无法挂载，容器无法启动。集群其余 59 个 Running Pod 均正常，无其他异常组。
   confidence=98%
   causal_chain={"root_cause": "ConfigMap 'rc-volume-key-config' 的 data 中缺少 key 'missing-key'，该 key 被 Pod spec volume 'config-volume' 引用且设置为非可选(optional=false)", "propagation": "Pod spec 声明 volume config-volume 引用 ConfigMap rc-volume-key-config 中的 key missing-key → kubelet 在挂载卷时读取 ConfigMap 内容 → 发现 data 中不存在 missing-key → 挂载失败 → kubelet 持续重试产生 FailedMount Events → Pod 无法进入 Running 状态", "direct_cause": "MountVolume.SetUp failed: configmap references non-existent config key: missing-key", "manifestation": "Pod rc-volume-configmap-missing-key 状态为 Pending/ContainerCreating，QoS BestEffort，容器处于 Waiting(ContainerCreating)，持续 15 分钟无变化"}
   rca_analysis={"phenomenon": "Pod rc-volume-configmap-missing-key (aiops-e2e) 状态为 Pending/ContainerCreating，kubelet Events 报错 MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key，卷挂载失败导致容器无法启动。", "evidence_inventory": [{"id": "e1", "source": "kubectl_get_by_kind_in_cluster", "content": "集群 65 个 Pod 中仅 1 个异常：rc-volume-configmap-missing-key 状态 ContainerCreating", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe", "content": "Pod 实际状态 Pending，kubelet Events 明确报错：configmap references non-existent config key: missing-key", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_yaml", "content": "Pod spec volumes[0] 引用 ConfigMap rc-volume-key-config，name=config-volume，optional=false", "reliability": "高"}, {"id": "e4", "source": "kubectl_get_yaml (ConfigMap)", "content": "ConfigMap rc-volume-key-config 存在，data 中仅包含 existing-key: present，无 missing-key", "reliability": "高"}, {"id": "e5", "source": "kubectl_events", "content": "FailedMount 事件 15 次重复：MountVolume.SetUp failed - configmap references non-existent config key: missing-key", "reliability": "高"}, {"id": "e6", "source": "run_bash_command (get configmap)", "content": "ConfigMap rc-volume-key-config 原始 YAML 确认 data 中只有 existing-key，无 missing-key", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59}; rc-volume-configmap-missing-key 0/1 ContainerCreating", "interpretation": "集群整体健康，仅此一个异常 Pod，不存在其他并发异常组需关注。"}, {"evidence_id": "e2", "raw_data": "Warning FailedMount 91s (x15 over 15m) kubelet MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key", "interpretation": "明确指出了卷挂载失败的根因——ConfigMap 中缺失 Pod 引用的 key missing-key。"}, {"evidence_id": "e3", "raw_data": "volumes: [{\"name\": \"config-volume\", \"configMap\": \"rc-volume-key-config\"}] 且 optional: false", "interpretation": "Pod spec 将 config-volume 挂载为 ConfigMap 类型的卷，引用 rc-volume-key-config，且设置为非 optional，意味着该 key 必须存在，否则 kubelet 拒绝启动容器。"}, {"evidence_id": "e4", "raw_data": "ConfigMap rc-volume-key-config data 字段：existing-key: present", "interpretation": "ConfigMap 确实存在于 aiops-e2e 命名空间，但 data 中只有 existing-key，没有 Pod 引用的 missing-key。"}, {"evidence_id": "e5", "raw_data": "93s (x15 over 15m) Warning FailedMount Pod/rc-volume-configmap-missing-key MountVolume.SetUp failed ...", "interpretation": "kubelet 持续重试卷挂载，每次均因同一个原因失败，15 次事件表明问题持续存在而非瞬态。"}, {"evidence_id": "e6", "raw_data": "data:\n  existing-key: present\nkind: ConfigMap\nmetadata:\n  name: rc-volume-key-config\n  namespace: aiops-e2e", "interpretation": "直接查看 ConfigMap 原始 YAML，确认 data 中仅有一个 key existing-key，missing-key 确实不存在。"}], "causal_chain": {"root_cause": "ConfigMap 'rc-volume-key-config' 的 data 中缺少 key 'missing-key'，该 key 被 Pod spec volume 'config-volume' 引用且设置为非可选(optional=false)", "propagation": "Pod spec 声明 volume config-volume 引用 ConfigMap rc-volume-key-config 中的 key missing-key → kubelet 在挂载卷时读取 ConfigMap 内容 → 发现 data 中不存在 missing-key → 挂载失败 → kubelet 持续重试产生 FailedMount Events → Pod 无法进入 Running 状态", "direct_cause": "MountVolume.SetUp failed: configmap references non-existent config key: missing-key", "manifestation": "Pod rc-volume-configmap-missing-key 状态为 Pending/ContainerCreating，QoS BestEffort，容器处于 Waiting(ContainerCreating)，持续 15 分钟无变化"}, "root_cause": "Pod rc-volume-configmap-missing-key (aiops-e2e) 卡在 ContainerCreating/Pending 状态的根因是：Pod spec 中 volume \"config-volume\" 引用 ConfigMap \"rc-volume-key-config\" 的 key \"missing-key\"（optional=false），但该 ConfigMap 的 data 中仅包含 \"existing-key: present\"，不存在 \"missing-key\"。kubelet 在 15 分钟内重复 15 次报错 \"MountVolume.SetUp failed for volume 'config-volume': configmap references non-existent config key: missing-key\"，导致卷无法挂载，容器无法启动。集群其余 59 个 Running Pod 均正常，无其他异常组。", "root_cause_summary": "Pod rc-volume-configmap-missing-key (aiops-e2e) 卡在 ContainerCreating/Pending 状态的根因是：Pod spec 中 volume \"config-volume\" 引用 ConfigMap \"rc-volume-key-config\" 的 key \"missing-key\"（optional=false），但该 ConfigMap 的 data 中仅包含 \"existing-key: present\"，不存在 \"missing-key\"。kubelet 在 15 分钟内重复 15 次报错 \"MountVolume.SetUp failed for volume 'config-volume': configmap references non-existent config key: missing-key\"，导致卷无法挂载，容器无法启动。集群其余 59 个 Running Pod 均正常，无其他异常组。", "confidence": 0.98, "confidence_reason": "有 4 项直接证据：① kubectl describe 给出明确错误信息；② kubectl_events 确认 15 次重复报错；③ kubectl_get_yaml 确认 Pod spec volume 引用且 optional=false；④ run_bash_command 直接读取 ConfigMap 原始 YAML 确认 data 中确实缺少 missing-key。因果链完整且无歧义，置信度 0.98。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [{"cause": "ConfigMap 'rc-volume-key-config' 不存在或被删除", "probability": "low", "reason": "run_bash_command 确认 ConfigMap 存在于 aiops-e2e 命名空间，creationTimestamp 与 Pod 一致，data 字段存在，仅缺少 missing-key"}, {"cause": "ConfigMap key 名称拼写错误（Pod 引用写错）", "probability": "low", "reason": "Pod 名称为 rc-volume-configmap-missing-key，明确指向 missing-key 问题；ConfigMap data 中只有 existing-key，说明 Pod 引用的 key 确实未被定义"}, {"cause": "kubelet 或节点问题导致卷挂载失败", "probability": "low", "reason": "Events 错误信息明确指向 configmap key 缺失而非节点问题，且集群中其他 59 个 Pod 在 node1 上正常运行"}], "limitations": "未获取 ConfigMap 的完整 YAML 中 items 字段（如果使用了 subPath/items 方式引用 key），但原始 YAML 输出已明确 data 中只包含 existing-key，且 Events 错误信息直接报 missing-key 不存在，足以定位根因。未验证是否还有其他 Pod 引用同一 ConfigMap 的 missing-key，但当前仅一个异常 Pod。", "llm_raw_analysis": "## 证据清点\\n共 6 项已采集证据：kubectl_get_by_kind_in_cluster（集群概览）、kubectl_describe（Pod 详细状态+Events）、kubectl_get_yaml（Pod spec volumes）、kubectl_get_yaml（ConfigMap 信息）、kubectl_events（Pod 事件）、run_bash_command（ConfigMap 原始 YAML）。\\n\\n## 逐条分析\\n- e1：集群 65 Pod 仅 1 异常，无其他异常组需关注\\n- e2：确凿证据——kubelet 报错 \\\"configmap references non-existent config key: missing-key\\\"\\n- e3：Pod volume config-volume 引用 ConfigMap rc-volume-key-config 且 optional=false\\n- e4/e6：ConfigMap rc-volume-key-config 存在但 data 仅有 existing-key，无 missi\n... 截断，原始 841 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-volume-configmap-missing-key (aiops-e2e) 卡在 ContainerCreating/Pending 状态的根因是：Pod spec 中 volume "config-volume" 引用 ConfigMap "rc-volume-key-conf...
   置信度: 98%
   🔗 因果链:
     根本原因: ConfigMap 'rc-volume-key-config' 的 data 中缺少 key 'missing-key'，该 key 被 Pod spec volume 'config-volume' 引用且设置为非可选(optional=false)
     传导机制: Pod spec 声明 volume config-volume 引用 ConfigMap rc-volume-key-config 中的 key missing-key → kubelet 在挂载卷时读取 ConfigMap 内容 → 发现 data 中不存在 missing-key → 挂载失败 → kubelet 持续重试产生 FailedMount Events → Pod 无法进入 Running 状态
     最终表现: Pod rc-volume-configmap-missing-key 状态为 Pending/ContainerCreating，QoS BestEffort，容器处于 Waiting(ContainerCreating)，持续 15 分钟无变化


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (16.4s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6048 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 59.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，请查收您的集群诊断报告。

---
## 📊 诊断概览
您的集群整体健康，65个Pod中**59个处于Running状态**，仅发现**1个异常问题**。

| 项目 | 内容 |
|------|------|
| **集群整体状态** | 基本健康，1个异常 |
| **Pod异常状态** | ContainerCreating（VolumeMountFailed） |
| **兼容归因层** | L0 - 基础可用性层 |
| **问题分类** | VolumeMountFailed / storage_volume |
| **置信度** | **高 (98%)** |
| **证据完整度** | 4/4 (100%) |

**核心问题**：Pod `rc-volume-configmap-missing-key` (命名空间 `aiops-e2e`) 引用了 ConfigMap 中**不存在的配置键 (key)**，导致卷挂载失败，Pod 卡在 `ContainerCreating` 状态。

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| **异常 Pod** | `rc-volume-configmap-missing-key` |
| **命名空间** | `aiops-e2e` |
| **所在节点** | `node1` (10.2.0.49) |
| **Pod 状态** | `ContainerCreating` / `Pending` |
| **错误信息** | `MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key` |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 & 事件 | `kubectl describe pod` | `status: Pending` , `Reason: ContainerCreating` , `Warning FailedMount 73s (x15 over 15m) kubelet MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key` | Pod 卡在创建阶段，kubelet 明确报错找不到 ConfigMap 的 key。 |
| 2 | Pod 规格 | `kubectl get pod -o yaml` | `finalizers: <none>` , `terminationGracePeriodSeconds: 30` , `command: sh -c sleep 3600` | Pod 规格正常，排除 finalizer 阻塞问题。 |
| 3 | 被引用的 ConfigMap | `kubectl get configmap rc-volume-key-config -o yaml` | `data:` <br> `existing-key: present` | ConfigMap `rc-volume-key-config` 存在，但 data 中**只有 `existing-key`**，**没有 `missing-key`**。 |
| 4 | 相关事件 | `kubectl get events` | `93s (x15 over 15m) Warning FailedMount Pod/rc-volume-configmap-missing-key MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key` | 事件记录与 Pod describe 完全一致，确认错误持续存在。 |

### 证据关联分析
- **证据 #1 + #3 + #4 印证**：kubelet 尝试挂载卷时，去 ConfigMap `rc-volume-key-config` 里找 key `missing-key`，但该 ConfigMap 的 data 中只包含 `existing-key`，导致挂载失败，持续报错。
- **证据 #2**：Pod 的 finalizers 为空，`terminationGracePeriodSeconds` 为 30s，排除因 finalizer 或优雅关闭超时导致的异常，使问题进一步聚焦到卷挂载失败上。

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | - | 证据链完整，足以定位根因 |

---
## 🎯 根因分析
### 因果链
```
┌──────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                  │
│ ***ConfigMap 'rc-volume-key-config' 的 data 中缺少 key 'missing-key'***  │
│ ConfigMap 文件中只有 "existing-key"，但 Pod 引用了一个不存在的 "missing-key"。 │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                  │
│ Pod spec volumes[0] 引用 ConfigMap 'rc-volume-key-config' 且              │
│ optional=false（默认，即非可选）→ 卷挂载时 kubelet 检查 ConfigMap 内容       │
│ → 发现缺失 'missing-key' → 挂载失败                                      │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┘
│ 直接原因                                                                  │
│ kubelet 15 分钟内重复 15 次报错：MountVolume.SetUp failed for volume      │
│ "config-volume" : configmap references non-existent config key: missing-key│
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┘
│ 用户可见现象                                                              │
│ Pod rc-volume-configmap-missing-key 状态为 Pending/ContainerCreating，      │
│ 持续 15 分钟无变化，容器无法启动                                           │
└──────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #1, #3, #4，问题的根本原因是 **Pod `rc-volume-configmap-missing-key` 的 YAML 配置中，引用了 ConfigMap `rc-volume-key-config` 里一个不存在的 key，即 `missing-key`**。这导致 kubelet 无法完成卷挂载，Pod 一直卡在 `ContainerCreating` 状态。

**置信度**：高 (98%)
- ✅ `kubectl describe` 和 `kubectl get events` 的 FailedMount 事件原文完全一致且明确指出了缺失的 key。
- ✅ `kubectl get configmap` 的输出显示 ConfigMap 的数据域 (data) 中确实不包含 `missing-key`。
- ✅ 证据链完整，无需猜测。

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）

**方案一：[推荐] 修正 Pod 的 YAML 配置**
如果 `missing-key` 是一个拼写错误或引用错误，应修改 Pod/Deployment 的 YAML 文件。
```bash
# 1. 假设是 Deployment
kubectl edit deployment <your-deployment-name> -n aiops-e2e
# 2. 找到 volume 'config-volume' 的 configMap 部分
# 3. 将 items 中的 key 从 'missing-key' 改为 'existing-key'，或者删除不存在的引用
# 4. 保存退出后，Deployment 会自动滚动更新 Pod
```
*依据*：从 ConfigMap 的实际内容 (`existing-key`) 推断，Pod 配置可能存在拼写错误。

**方案二：[备选] 修正 ConfigMap**
如果 Pod 引用的 `missing-key` 是必须的，则把它添加到 ConfigMap 中。
```bash
# 1. 获取当前 ConfigMap 的 YAML
kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml > /tmp/config.yaml

# 2. 编辑 /tmp/config.yaml，在 data 字段下添加 missing-key 及其对应的值
# 例如：
# data:
#   existing-key: present
#   missing-key: "your_required_value_here"

# 3. 应用更新
kubectl apply -f /tmp/config.yaml

# 4. 强制重启 Pod（如果它没有自动更新）
kubectl delete pod rc-volume-configmap-missing-key -n aiops-e2e --force --grace-period=0
```
*依据*：如果 Pod 的引用是正确的，那么修复 ConfigMap 使其内容完整即可解决问题。

### 后续优化
1. **代码审查**：在 CI/CD 流程中增加对 ConfigMap 引用的校验，确保所有引用的 key 都真实存在。
2. **命名规范**：建议在 Pod 和 ConfigMap 的命名上使用更明确的语义，减少混淆。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e` | STATUS 为 `Running`，READY 为 `1/1` |
| 2. 检查事件 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-configmap-missing-key` | 无 `FailedMount` 事件，或有 `Pulled`、`Created`、`Started` 等正常事件 |
| 3. 验证卷挂载 | `kubectl exec rc-volume-configmap-missing-key -n aiops-e2e -- cat /path/to/mounted/missing-key` | 能正常读取到配置文件内容 |

---
## ⚠️ 注意事项
- 选择 **方案一（修改 Pod 配置）** 是最安全的做法，因为它不涉及修改工作负载依赖的数据源。
- 如果选择 **方案二（修改 ConfigMap）**，请确保添加的内容正确无误，并注意 ConfigMap 的热更新特性（通常需要重启 Pod 才能读取到最新的配置）。

---

## 📊 性能统计

├─ 总耗时: 59.3s
├─ 问题定位: 14.4s (24%) ✅
├─ 证据链采集: 12.0s (20%) ✅
├─ 根因分析: 16.4s (28%) ✅
├─ 汇总总结: 16.4s (28%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 8 次
```

📋 诊断追踪

- **核心 Runbook**: pod-volume-mount-failed
- **参考 Runbook**: pod-volume-mount-failed
- **工具调用**: 8 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
