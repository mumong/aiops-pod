======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: f7db64db0d404f8a]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先全局扫描所有 Pod 的状态，看看集群中是否有异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59}
NAMESPACE         NAME                                                READY   STATUS              RESTARTS       A
   💭 [问题定位] 很好，我发现了一个异常 Pod。让我进一步查看它的详细信息。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                              READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-volume-configmap-missing-key   0/1     ContainerCreating   
   💭 [问题定位] Pod 状态是 `ContainerCreating`，并且 label 已经标记了 `pod_abnormal_type=VolumeMountFailed`。让我先获取这个 runbook 来参考定位方向。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] 按照 runbook 指导，我先 describe 这个 Pod 看 Events 原文。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  7s (x13 over 10m)    kubelet            MountVolume
   💭 [问题定位] 现在我已经获取到了足够的信息来完成定位分析。

---

## 定位分析结果

### 异常 Pod 清单

| Pod | 命名空间 | 状态 | 异常类型 |
|-----|---------|------|---------|
| `rc-volume-configmap-missing-key` | `aiops-e2e` | `ContainerCreating` / `Pending` | **VolumeMountFailed** |

### 异常分组（abnormal_groups）

- **VolumeMountFailed** — 1 个 Pod：`rc-volume-configmap-missing-key`

### 异常类型与分层

| 字段 | 值 |
|------|-----|
| **pod_status_keyword** | `ContainerCreating` |
| **pod_abnormal_type** | `VolumeMountFailed` |
| **status_category** | `storage_volume` |
| **layer** | **L0** — 卷挂载失败，属于基础设施存储层异常 |
| **layer_name** | `VolumeMountFailed` |

### 关键证据（来自 `kubectl describe pod` Events）

> `MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key`

Pod 的 `config-volume` 卷引用了 ConfigMap `rc-volume-key-config`，但该 ConfigMap 中**不存在名为 `missing-key` 的键**。

### 根因方向

- **Pod spec** 中 `volumes[].configMap.name = rc-volume-key-config`，`volumes[].configMap.items[]` 中引用了 `missing-key` 这个 key
- 该 ConfigMap 虽然存在，但**不包含 `missing-key` 这个键**，导致 kubelet 无法挂载卷
- 这属于**配置错误**，但按 Pod 异常状态归类走 VolumeMountFailed（L0）

### 后续审查方向（交由 evidence 节点）

1. 确认 ConfigMap `rc-volume-key-config` 的实际内容，查看缺少哪些 key
2. 确认 Pod 中 `volumes[].configMap.items[]` 具体引用了哪些 key
3. 对比后修复 ConfigMap 添加缺失的 key，或修正 Pod spec 中的 key 引用

---

**总结：集群中有 1 个异常 Pod `rc-volume-configmap-missing-key`，卡在 `ContainerCreating` 状态，原因是 ConfigMap 卷引用了不存在的 key `missing-key`，属于 VolumeMountFailed 类型，归为 L0 层。其余 59 个 Pod 均正常运行。**
   ✅ [问题定位] 完成 (17.2s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[{'scenario': 'ConfigMap volume引用了不存在的key', 'probability': '高', 'reason': "Events 原文明确提示 'configmap references non-existent config key: missing-key'，Pod spec中volumes[].configMap.items[]引用了missing-key，但ConfigMap rc-volume-key-config中不包含该key"}]
   entities=[{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}, {"type": "Volume", "name": "config-volume", "namespace": "aiops-e2e"}]
   reasoning=集群中存在1个异常Pod: rc-volume-configmap-missing-key (namespace: aiops-e2e)，当前状态为 ContainerCreating/Pending，异常类型为 VolumeMountFailed。kubectl describe 事件明确显示: 'MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key'。该Pod的config-volume卷引用ConfigMap 'rc-volume-key-config'中的key 'missing-key'，但该ConfigMap中不存在此key。根据五层模型，VolumeMountFailed属于L0层（基础设施存储层异常），status_category为storage_volume。其余59个Pod均正常运行。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "VolumeMountFailed", "confidence": 0.98, "reasoning": "集群中存在1个异常Pod: rc-volume-configmap-missing-key (namespace: aiops-e2e)，当前状态为 ContainerCreating/Pending，异常类型为 VolumeMountFailed。kubectl describe 事件明确显示: 'MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key'。该Pod的config-volume卷引用ConfigMap 'rc-volume-key-config'中的key 'missing-key'，但该ConfigMap中不存在此key。根据五层模型，VolumeMountFailed属于L0层（基础设施存储层异常），status_category为storage_volume。其余59个Pod均正常运行。", "abnormal_pods": [{"name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}, {"type": "Volume", "name": "config-volume", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "ConfigMap volume引用了不存在的key", "probability": "高", "reason": "Events 原文明确提示 'configmap references non-existent config key: missing-key'，Pod spec中volumes[].configMap.items[]引用了missing-key，但ConfigMap rc-volume-key-config中不包含该key"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-volume-configmap-missing-key                     0/1     ContainerCreating   0              10m     <none>           node1    <none>           <none>            app=rc-volume-configmap-missing-key,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/f7db64db0d404f8a/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/f7db64db0d404f8a/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/f7db64db0d404f8a/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 98%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，直接执行既有 evidence_plan 中的关键工具调用。我先从 Pod describe 和 YAML 获取开始，这些是最高优先级的 critical 证据。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  28s (x13 over 10m)    kubelet            MountVolum
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
   💭 [证据链采集] 让我再获取 ConfigMap 的完整 data 内容，以及 Pod 的 events 时间线。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "apiVersion: v1\ndata:\n  existing-key: present\nkind: ConfigMap\nmetadata:\n  annotations:\n    kubectl.kubernetes.io/last-applied-configuration: |\n      {\"apiVersion\":
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
creationTimestamp: 2026-05-21T04:29:04Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
final
   💭 [证据链采集] 让我检查 Pod spec 中 volumes 的 configMap.items 字段，看是否引用了 specific keys。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\"defaultMode\":420,\"items\":[{\"key\":\"missing-key\",\"path\":\"missing-key\"}],\"name\":\"rc-volume-key-config\"}", "stderr": "", "returncode": 0}
   💭 [证据链采集] 好了，所有关键证据已到位，下面给出采证结论。

---

## 采证结论

### ✅ 已采集证据（共 4 条 critical/important 证据）

| 编号 | 证据项 | 证据来源 | 结论 |
|------|--------|----------|------|
| **L0-ev1** | Pod 当前状态和 FailedMount 事件原文 | `kubectl describe pod` | ✅ **关键证据确认** — 事件原文仍活跃：`MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key`（28秒前第13次重复） |
| **L0-ev2** | Pod spec volumes 引用检查 | `kubectl get pod -o yaml` + `jsonpath` | ✅ **关键证据确认** — `volumes[].configMap.items[0].key = "missing-key"`，明确要求从 ConfigMap 读取名为 `missing-key` 的键 |
| **L0-ev3** | ConfigMap 内容确认 | `kubectl get configmap -o yaml` | ✅ **根因证据确认** — ConfigMap `rc-volume-key-config` 中只有 `existing-key: present`，**不包含 `missing-key`** |
| **L0-ev4** | Pod 事件完整时间线 | `kubectl describe`（events 部分） | ✅ **持续性确认** — FailedMount 事件在 10 分钟内重复 13 次，错误始终一致，无缓解趋势 |

### ❌ 未采集 / 冲突证据
- **无冲突证据**：Pod、ConfigMap 均存在于指定 namespace `aiops-e2e` 中，状态与上游 layer_handoff 一致。

### 🎯 根因定位
> **Pod `rc-volume-configmap-missing-key`（namespace: aiops-e2e）卡在 Pending/ContainerCreating，根因为：**
>
> Pod spec 中 `volumes[].configMap.items[]` 要求 ConfigMap `rc-volume-key-config` 提供一个名为 `missing-key` 的键，但该 ConfigMap 实际只有 `existing-key` 一个键，`missing-key` **不存在**。由于 `optional: false`（默认），kubelet 无法完成卷挂载，Pod 持续 Pending。
   ✅ [证据链采集] 完成 (18.1s)
   📤 → 下游数据: evidence_items=6/7
   evidence_analysis={"evidence_plan":[{"id":"L0-ev1","description":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e 确认当前 Events 原文中 FailedMount 错误是否仍存在","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e","resource_type":"pod"},"purpose":"确认Pod当前状态和FailedMount事件原文，验证configmap missing-key错误是否仍然活跃","evidence_type":"events_and_status","target_scope":"Pod/aiops-e2e/rc-volume-configmap-missing-key","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"L0-ev2","description":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml 确认 volumes[].configMap.items[] 引用了 missing-key","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e","resource_type":"pod"},"purpose":"检查Pod spec中volumes[].configMap.items[]是否引用missing-key","evidence_type":"config_and_spec","target_scope":"Pod/aiops-e2e/rc-volume-configmap-missing-key","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"L0-ev3","description":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml 确认ConfigMap中不存在'key: missing-key'","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml","tool_args":{"kind":"configmap","name":"rc-volume-key-config","namespace":"aiops-e2e","resource_type":"configmap"},"purpose":"确认ConfigMap rc-volume-key-config中是否包含missing-key，验证缺失根因","evidence_type":"dependency_check","target_scope":"ConfigMap/aiops-e2e/rc-volume-key-config","acceptable_tools":["kubectl_get_yaml","kubectl_get_by_name","run_bash_command"],"counts_for_completeness":true},{"id":"L0-ev4","description":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-configmap-missing-key 确认事件时间线","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-configmap-missing-key --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-volume-configmap-missing-key"},"purpose":"获取Pod事件完整时间线，确认FailedMount错误的持续性和最新状态","evidence_type":"events_and_status","target_scope":"Pod/aiops-e2e/rc-volume-configmap-missing-key","acceptable_tools":["kubectl_events","run_bash_command"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  28s (x13 over 10m)    kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n  Warning  FailedMount  6m28s                 kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-fbhds config-volume]: timed out waiting for the condition\n  Warning  FailedMount  115s (x3 over 8m42s)  kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  config-volume:\n    Type:      ConfigMap (a volume populated by a ConfigMap)\n    Name:      rc-volume-key-config\n    Optional:  false\n  kube-api-access-fbhds:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedMount  6m28s                 kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-fbhds config-volume]: timed out waiting for the condition\n  Warning  FailedMount  115s (x3 over 8m42s)  kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition\n  Warning  FailedMount  28s (x13 over 10m)    kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f7db64db0d404f8a/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f7db64db0d404f8a/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f7db64db0d404f8a/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: ConfigMap\nname: rc-volume-key-config\nnamespace: aiops-e2e","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f7db64db0d404f8a/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f7db64db0d404f8a/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f7db64db0d404f8a/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T04:29:04Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-configmap-missing-key, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"config-volume\", \"configMap\": \"rc-volume-key-config\"}\n- {\"name\": \"kube-api-access-fbhds\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f7db64db0d404f8a/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f7db64db0d404f8a/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f7db64db0d404f8a/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"apiVersion: v1\\ndata:\\n  existing-key: present\\nkind: ConfigMap\\nmetadata:\\n  annotations:\\n    kubectl.kubernetes.io/last-applied-configuration: |\\n      {\\\"apiVersion\\\":\\\"v1\\\",\\\"data\\\":{\\\"existing-key\\\":\\\"present\\\"},\\\"kind\\\":\\\"ConfigMap\\\",\\\"metadata\\\":{\\\"annotations\\\":{},\\\"labels\\\":{\\\"rootcause-e2e\\\":\\\"true\\\"},\\\"name\\\":\\\"rc-volume-key-config\\\",\\\"namespace\\\":\\\"aiops-e2e\\\"}}\\n  creationTimestamp: \\\"2026-05-21T04:29:04Z\\\"\\n  labels:\\n    rootcause-e2e: \\\"true\\\"\\n  name: rc-volume-key-config\\n  namespace: aiops-e2e\\n  resourceVersion: \\\"52517160\\\"\\n  uid: 5468219a-cec8-424b-b490-66fd39c82b58\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f7db64db0d404f8a/tools/004-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f7db64db0d404f8a/tools/004-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f7db64db0d404f8a/tools/004-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T04:29:04Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-configmap-missing-key, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"config-volume\", \"configMap\": \"rc-volume-key-config\"}\n- {\"name\": \"kube-api-access-fbhds\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f7db64db0d404f8a/tools/005-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f7db64db0d404f8a/tools/005-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f7db64db0d404f8a/tools/005-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\\"defaultMode\\\":420,\\\"items\\\":[{\\\"key\\\":\\\"missing-key\\\",\\\"path\\\":\\\"missing-key\\\"}],\\\"name\\\":\\\"rc-volume-key-config\\\"}\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f7db64db0d404f8a/tools/006-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f7db64db0d404f8a/tools/006-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f7db64db0d404f8a/tools/006-evidence-run_bash_command.summary.txt"}],"llm_analysis":"好了，所有关键证据已到位，下面给出采证结论。\n\n---\n\n## 采证结论\n\n### ✅ 已采集证据（共 4 条 critical/important 证据）\n\n| 编号 | 证据项 | 证据来源 | 结论 |\n|------|--------|----------|------|\n| **L0-ev1** | Pod 当前状态和 FailedMount 事件原文 | `kubectl describe pod` | ✅ **关键证据确认** — 事件原文仍活跃：`MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key`（28秒前第13次重复） |\n| **L0-ev2** | Pod spec volumes 引用检查 | `kubectl get pod -o yaml` + `jsonpath` | ✅ **关键证据确认** — `volumes[].configMap.items[0].key = \"missing-key\"`，明确要求从 ConfigMap 读取名为 `missing-key` 的键 |\n| **L0-ev3** | ConfigMap 内容确认 | `kubectl get configmap -o yaml` | ✅ **根因证据确认** — ConfigMap `rc-volume-key-config` 中只有 `existing-key: present`，**不包含 `missing-key`** |\n| **L0-ev4** | Pod 事件完整时间线 | `kubectl describe`（events 部分） | ✅ **持续性确认** — FailedMount 事件在 10 分钟内重复 13 次，错误始终一致，无缓解趋势 |\n\n### ❌ 未采集 / 冲突证据\n- **无冲突证据**：Pod、ConfigMap 均存在于指定 namespace `aiops-e2e` 中，状态与上游 layer_handoff 一致。\n\n### 🎯 根因定位\n> **Pod `rc-volume-configmap-missing-key`（namespace: aiops-e2e）卡在 Pending/ContainerCreating，根因为：**\n>\n> Pod spec 中 `volumes[].configMap.items[]` 要求 ConfigMap `rc-volume-key-config` 提供一个名为 `missing-key` 的键，但该 ConfigMap 实际只有 `existing-key` 一个键，`missing-key` **不存在**。由于 `optional: false`（默认），kubelet 无法完成卷挂载，Pod 持续 Pending。","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 6/7 项，完整度 86%；实际执行工具 9 个，匹配计划 3 个，未规划证据 6 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":7,"environment_evidence_collected":6,"environment_evidence_completeness":0.8571428571428571,"executed_tool_count":9,"matched_tool_count":3,"unplanned_tool_count":6,"evidence_inventory":[{"id":"L0-ev1","description":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e 确认当前 Events 原文中 FailedMount 错误是否仍存在","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","purpose":"确认Pod当前状态和FailedMount事件原文，验证configmap missing-key错误是否仍然活跃","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"L0-ev2","description":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml 确认 volumes[].configMap.items[] 引用了 missing-key","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","purpose":"检查Pod spec中volumes[].configMap.items[]是否引用missing-key","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"L0-ev3","description":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml 确认ConfigMap中不存在'key: missing-key'","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml","purpose":"确认ConfigMap rc-volume-key-config中是否包含missing-key，验证缺失根因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"L0-ev4","description":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-configmap-missing-key 确认事件时间线","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-configmap-missing-key --sort-by='.lastTimestamp'","purpose":"获取Pod事件完整时间线，确认FailedMount错误的持续性和最新状态","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["L0-ev4(kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-configmap-missing-key 确认事件时间线): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 86%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | L0-ev1 | critical | ✅ | kubectl_describe | kubectl describe pod rc-volume-configmap-miss... | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` |
   | L0-ev2 | critical | ✅ | kubectl_get_yaml | kubectl get pod rc-volume-configmap-missing-k... | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml` |
   | L0-ev3 | critical | ✅ | kubectl_get_yaml | kubectl get configmap rc-volume-key-config -n... | `kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml` |
   | L0-ev4 | important | ❌ | kubectl_events | kubectl get events -n aiops-e2e --field-selec... | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volum...` |

   ⚠️ 未采集原因:
   - L0-ev4(kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-configmap-missing-key 确认事件时间线): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (17.3s)
   📤 → 下游数据: root_cause=Pod rc-volume-configmap-missing-key (namespace: aiops-e2e) 的 config-volume 卷通过 items 字段引用 ConfigMap rc-volume-key-config 中的 key 'missing-key'（证据 L0-ev2），但该 ConfigMap 实际数据仅包含 'existing-key: present'，不包含 'missing-key'（证据 L0-ev3）。kubelet 在 10 分钟内重复 13 次报错 'MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key'（证据 L0-ev1），导致 Pod 持续 Pending，容器状态为 Waiting(ContainerCreating)（证据 L0-ev4）。集群其余 59 个 Pod 均正常运行，问题范围局限于此单一 Pod。
   confidence=98%
   causal_chain={"root_cause": "Pod spec 中 config-volume 卷通过 items[] 引用 ConfigMap rc-volume-key-config 的 key 'missing-key'，但该 ConfigMap 中不存在此 key（仅有 existing-key）。由于卷配置为非可选（optional: false，默认值），kubelet 无法完成挂载。", "propagation": "Pod spec 声明卷引用缺失的 ConfigMap key → kubelet 在执行 MountVolume.SetUp 时发现 items[].key 在 ConfigMap data 中不存在 → 挂载失败 → kubelet 持续重试（10分钟内13次）→ Pod 无法进入 Running 状态", "direct_cause": "ConfigMap rc-volume-key-config 缺少 Pod 卷 items 引用的 key 'missing-key'", "manifestation": "Pod rc-volume-configmap-missing-key 处于 Pending/ContainerCreating 状态，kubectl describe 持续报 FailedMount 事件，容器无法启动"}
   rca_analysis={"phenomenon": "集群 aiops-e2e namespace 中存在 1 个异常 Pod: rc-volume-configmap-missing-key，当前状态为 Pending/ContainerCreating，异常类型为 VolumeMountFailed。其余 59 个 Pod 均正常运行。", "evidence_inventory": [{"id": "L0-ev1", "source": "kubectl_describe", "content": "Pod rc-volume-configmap-missing-key 当前 Events 仍存在 FailedMount 错误：MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key（28秒前第13次重复）", "reliability": "高"}, {"id": "L0-ev2", "source": "kubectl_get_yaml (Pod spec volumes jsonpath)", "content": "Pod volumes[].configMap.items[] 明确指定 key=\"missing-key\"，从 ConfigMap rc-volume-key-config 读取", "reliability": "高"}, {"id": "L0-ev3", "source": "kubectl_get_yaml (ConfigMap)", "content": "ConfigMap rc-volume-key-config 中仅有 existing-key: present，不存在 missing-key 键", "reliability": "高"}, {"id": "L0-ev4", "source": "kubectl_describe", "content": "Pod 状态为 Pending，容器状态 Waiting(ContainerCreating)，10分钟内 FailedMount 重复13次无缓解", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "集群共65个Pod，59个Running，1个异常(rc-volume-configmap-missing-key 为 ContainerCreating)", "reliability": "高"}, {"id": "layer_3", "source": "kubectl_describe", "content": "Events 原文：configmap references non-existent config key: missing-key", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "L0-ev1", "raw_data": "Warning FailedMount 28s (x13 over 10m) kubelet MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key", "interpretation": "kubelet 明确报告卷 config-volume 挂载失败，根本原因是 ConfigMap 引用了不存在的 key: missing-key。该事件持续活跃，最近一次在 28 秒前，10 分钟内重复 13 次。"}, {"evidence_id": "L0-ev2", "raw_data": "volumes[].configMap.items[] = {\"key\":\"missing-key\",\"path\":\"missing-key\"}, name=rc-volume-key-config", "interpretation": "Pod spec 中 config-volume 卷通过 items 字段明确要求从 ConfigMap rc-volume-key-config 中读取 key 为 missing-key 的数据。"}, {"evidence_id": "L0-ev3", "raw_data": "ConfigMap rc-volume-key-config data: existing-key: present（无 missing-key）", "interpretation": "ConfigMap 的实际内容只有 existing-key 一个键，没有 missing-key。这是导致 VolumeMountFailed 的根本原因。"}, {"evidence_id": "L0-ev4", "raw_data": "Pod phase: Pending; containerStatuses: Waiting(ContainerCreating), restartCount: 0", "interpretation": "Pod 持续处于 Pending 状态，容器未启动（0 重启），因为卷挂载阶段卡住，容器无法创建。"}, {"evidence_id": "layer_1", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59}", "interpretation": "集群中 59 个 Pod 正常运行，仅该 Pod 异常，问题范围明确，不涉及集群级故障。"}], "causal_chain": {"root_cause": "Pod spec 中 config-volume 卷通过 items[] 引用 ConfigMap rc-volume-key-config 的 key 'missing-key'，但该 ConfigMap 中不存在此 key（仅有 existing-key）。由于卷配置为非可选（optional: false，默认值），kubelet 无法完成挂载。", "propagation": "Pod spec 声明卷引用缺失的 ConfigMap key → kubelet 在执行 MountVolume.SetUp 时发现 items[].key 在 ConfigMap data 中不存在 → 挂载失败 → kubelet 持续重试（10分钟内13次）→ Pod 无法进入 Running 状态", "direct_cause": "ConfigMap rc-volume-key-config 缺少 Pod 卷 items 引用的 key 'missing-key'", "manifestation": "Pod rc-volume-configmap-missing-key 处于 Pending/ContainerCreating 状态，kubectl describe 持续报 FailedMount 事件，容器无法启动"}, "root_cause": "Pod rc-volume-configmap-missing-key (namespace: aiops-e2e) 的 config-volume 卷通过 items 字段引用 ConfigMap rc-volume-key-config 中的 key 'missing-key'（证据 L0-ev2），但该 ConfigMap 实际数据仅包含 'existing-key: present'，不包含 'missing-key'（证据 L0-ev3）。kubelet 在 10 分钟内重复 13 次报错 'MountVolume.SetUp failed for volume \\\"config-volume\\\" : configmap references non-existent config key: missing-key'（证据 L0-ev1），导致 Pod 持续 Pending，容器状态为 Waiting(ContainerCreating)（证据 L0-ev4）。集群其余 59 个 Pod 均正常运行，问题范围局限于此单一 Pod。", "root_cause_summary": "Pod rc-volume-configmap-missing-key (namespace: aiops-e2e) 的 config-volume 卷通过 items 字段引用 ConfigMap rc-volume-key-config 中的 key 'missing-key'（证据 L0-ev2），但该 ConfigMap 实际数据仅包含 'existing-key: present'，不包含 'missing-key'（证据 L0-ev3）。kubelet 在 10 分钟内重复 13 次报错 'MountVolume.SetUp failed for volume \\\"config-volume\\\" : configmap references non-existent config key: missing-key'（证据 L0-ev1），导致 Pod 持续 Pending，容器状态为 Waiting(ContainerCreating)（证据 L0-ev4）。集群其余 59 个 Pod 均正常运行，问题范围局限于此单一 Pod。", "confidence": 0.98, "confidence_reason": "有直接且明确的证据链：(1) Events 原文直接报错 configmap references non-existent config key: missing-key（L0-ev1）；(2) Pod spec jsonpath 确认引用了该 key（L0-ev2）；(3) ConfigMap yaml 确认不包含该 key（L0-ev3）。三条关键证据完全吻合，因果链清晰完整，无任何冲突证据。剩余未采集的完整事件时间线（L0-ev4 缺失项）不影响根因判断，因为关键事件已由 kubectl describe 提供。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [{"cause": "ConfigMap 本身不存在或被删除", "probability": "low", "reason": "ConfigMap rc-volume-key-config 确实存在于 aiops-e2e namespace 中（证据 L0-ev3），且包含数据 existing-key，因此不是 ConfigMap 缺失问题。"}, {"cause": "节点 node1 存储或卷插件故障", "probability": "low", "reason": "Events 明确指示 ConfigMap key 缺失，而非存储层或 CSI 插件错误。59 个其他 Pod 在集群中正常运行，说明节点无系统性存储故障。"}, {"cause": "网络或 kubelet 通信问题", "probability": "low", "reason": "Events 错误消息明确指向 ConfigMap key 缺失，不是网络超时或通信失败类型。"}], "limitations": "未采集完整事件时间线（kubectl get events --field-selector），但 kubectl describe 已提供最近 10 分钟内的事件摘要，不影响根因判断。ConfigMap 的 items 配置中的 path 字段不需要验证，因为根因在于 key 缺失而非 path。", "llm_raw_analysis": "L0 层级根因分析完成。证据清点：共 4 条关键证据(L0-ev1~L0-ev4) + 2 条重要证据(layer_1, layer_3)。所有证据一致性高。因果链：ConfigMap key 缺失(根因) → kubelet VolumeMount.SetUp 失败(直接原因) → Pod Pending/ContainerCreating(现象)。置信度 0.98，因为直接证据链完整。异常组 g1 仅包含此单一 Pod，已最小验证。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-volume-configmap-missing-key (namespace: aiops-e2e) 的 config-volume 卷通过 items 字段引用 ConfigMap rc-volume-key-config 中的 key 'missing-key'（证据 L0-ev...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod spec 中 config-volume 卷通过 items[] 引用 ConfigMap rc-volume-key-config 的 key 'missing-key'，但该 ConfigMap 中不存在此 key（仅有 existing-key）。由于卷配置为非可选（optional: false，默认值），kubelet 无法完成挂载。
     传导机制: Pod spec 声明卷引用缺失的 ConfigMap key → kubelet 在执行 MountVolume.SetUp 时发现 items[].key 在 ConfigMap data 中不存在 → 挂载失败 → kubelet 持续重试（10分钟内13次）→ Pod 无法进入 Running 状态
     最终表现: Pod rc-volume-configmap-missing-key 处于 Pending/ContainerCreating 状态，kubectl describe 持续报 FailedMount 事件，容器无法启动


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (17.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5920 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 10.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为一名资深 K8s 诊断报告专家，我将根据您提供的三个阶段分析结果，为您生成一份详尽、标准的诊断报告。

---

## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ContainerCreating |
| **兼容归因层** | L0 |
| **问题分类** | VolumeMountFailed (存储卷挂载失败) |
| **置信度** | 98% |
| **证据完整度** | 3/4 (75%) |

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**诊断结果**：集群整体健康。在总共 65 个 Pod 中，**59 个处于 `Running` 状态**，仅发现 **1 个异常 Pod**。

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-volume-configmap-missing-key` |
| Namespace | `aiops-e2e` |
| Node | `node1` |
| 错误信息 | `MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key` |

## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 & 事件 | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` | `Warning FailedMount ... MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key` | **根因已确认**：kubelet 明确报告卷挂载失败，原因是指定的 ConfigMap key 不存在。 |
| 2 | Pod YAML 配置 | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml` | `"items":[{"key":"missing-key","path":"missing-key"}],"name":"rc-volume-key-config"` | **确认配置错误**：Pod spec 中 config-volume 卷的 `items` 字段明确引用了 key `missing-key`。 |
| 3 | ConfigMap 内容 | `kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml` | `data:<br> existing-key: present` | **确认数据缺失**：ConfigMap `rc-volume-key-config` 中仅有 `existing-key`，不包含 Pod 所引用的 `missing-key`。 |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：Pod 的 YAML 配置（#2）声明要挂载 ConfigMap 中的 `missing-key`，但 ConfigMap（#3）中并不包含该 Key。kubelet 执行挂载时发现不匹配，因此报错（#1）。这是一个典型的配置不匹配问题。
- **证据链**：Pod 配置定义（Volume items 引用了错误 Key）→ 实际数据不存在（ConfigMap 缺少该 Key）→ 挂载操作失败（kubelet 报错）→ Pod 无法启动（状态为 ContainerCreating/Pending）。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 完整事件时间线（`kubectl get events`） | important | 虽然未采集，但 `kubectl describe` 已包含10分钟内13次重试的事件摘要，**不影响**根因判断。 |

## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod spec 的 config-volume 卷通过 items 字段引用 ConfigMap        │
│ rc-volume-key-config 中的 key 'missing-key'，但该 ConfigMap    │
│ 中根本不存在这个 key，仅有 existing-key。                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ Pod spec 声明卷引用缺失的 ConfigMap key →                        │
│ kubelet 在执行挂载时检查 items[].key 在 ConfigMap 中不存在 →    │
│ 挂载失败 → kubelet 持续重试（10分钟内13次）                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┘
│ 直接原因                                                        │
│ kubelet 无法挂载 config-volume 卷，错误原文为：                  │
│ "configmap references non-existent config key: missing-key"      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod rc-volume-configmap-missing-key 长期处于 Pending /           │
│ ContainerCreating 状态，无法进入 Running。                       │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1（FailedMount 事件）、#2（Pod YAML 中 items 配置）和 #3（ConfigMap 内容），问题的根本原因是 **Pod 的 volume 配置中 `items` 字段引用了一个不存在的 ConfigMap key** (`missing-key`)，导致 kubelet 无法完成 ConfigMap 挂载。

**置信度**：高 (98%)
- ✅ 证据 #1中的 `kubectl describe` 事件原文直接点出错误原因，是最高优先级证据。
- ✅ 证据 #2 和 #3 通过对比 Pod 配置和 ConfigMap 数据，从配置文件层面完美印证了错误。
- ✅ 集群其余 59 个 Pod 均正常运行，问题域明确，排除了节点、网络等全局性问题。

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 修复 ConfigMap，添加缺失的 Key**
修改 ConfigMap `rc-volume-key-config`，添加对应的 `missing-key`。
```bash
# 获取当前 ConfigMap 并导出到文件
kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml > configmap-patch.yaml

# 修改文件，在 data 字段中添加 missing-key 字段。例如，编辑 configmap-patch.yaml 文件：
# data:
#   existing-key: present
#   missing-key: your-desired-value  # <-- 添加这一行，替换为实际配置值

# 应用修改后的 ConfigMap
kubectl apply -f configmap-patch.yaml
```
*依据：* 添加 Pod 所引用的 Key，是解决挂载失败问题的最直接方法。

**2. [备选] 修正 Pod 配置，移除对缺失 Key 的引用**
如果 `missing-key` 不是应用必需的配置，可以直接修改 Deployment / StatefulSet 等上层资源，移除 `items` 中对 `missing-key` 的引用。
```bash
# 找到控制 Pod 的上层控制器（假设是 Deployment），编辑其配置
kubectl edit deployment <deployment-name> -n aiops-e2e
# 在 volumes[].configMap.items 数组中移除与 missing-key 相关的条目
# volumes:
#   - name: config-volume
#     configMap:
#       name: rc-volume-key-config
#       items:
#       - key: existing-key
#         path: existing-key
# 然后保存退出，控制器会自动重建 Pod
```
*依据：* 如果不需要该配置，修改上层资源以防止将来问题重现。

**3. 手动删除异常 Pod，触发重建**
修改完成后，需要手动删除当前异常的 Pod，等待其被控制器（如果有）重建。
```bash
kubectl delete pod rc-volume-configmap-missing-key -n aiops-e2e
```
*依据：* 删除 Pod 是让配置生效的常用方法。

### 后续优化
1. **配置校验**：在 CI/CD 流程中加入对 Volume 引用的校验，确保引用的 ConfigMap Key 真实存在。
2. **资源清单评审**：在部署 Manifest 提交前，增加人工或自动化 Code Review 环节。

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 检查 Pod 状态 | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e` | STATUS 从 `ContainerCreating/Pending` 变为 `Running` |
| 2. 检查 Pod 事件 | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` | 不再有 `Warning FailedMount` 事件，最后一条事件应为 `Started container` 或 `Successfully assigned` |
| 3. 检查 ConfigMap 内容 | `kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml` | data 字段中包含 `missing-key: <your-value>` (如果采用修复建议#1) |
| 4. 检查集群整体 | `kubectl get pods --all-namespaces` | 所有 Pod 状态正常，无异常 Pod。 |

## ⚠️ 注意事项
- 本次问题仅限于单一 Pod `rc-volume-configmap-missing-key`，集群其余部分运行正常（59/60 Pod 处于 `Running` 状态）。
- 问题由配置错误引起，非资源或环境故障，修复后可立即恢复。
- 如果 Pod 由 Deployment、StatefulSet 等控制器管理，修复 ConfigMap 并删除 Pod 后，控制器会自动重建一个新的 Pod。

---

## 📊 性能统计

├─ 总耗时: 1.2m
├─ 问题定位: 17.2s (24%) ✅
├─ 证据链采集: 18.1s (26%) ✅
├─ 根因分析: 17.3s (25%) ✅
├─ 汇总总结: 17.7s (25%) ✅
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
