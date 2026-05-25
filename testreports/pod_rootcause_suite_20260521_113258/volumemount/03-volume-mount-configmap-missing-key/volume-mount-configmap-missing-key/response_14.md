======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 60610a1a989a4c48]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，让我先全局扫描所有 Pod 的状态，看看有哪些异常。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59}
NAMESPACE         NAME                                                READY   STATUS              RESTARTS       A
   💭 [问题定位] 发现了一个异常 Pod。让我查看一下这个 Pod 的详细信息。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
55s (x11 over 7m7s)   Warning   FailedMount   Pod/rc-volume-configmap-missing-key   MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent co
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                              READY   STATUS              RESTARTS   AGE    IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-volume-configmap-missing-key   0/1     ContainerCreating  
   💭 [问题定位] Pod 上有 `pod_abnormal_type=VolumeMountFailed` 标签，这个异常明显是卷挂载失败。让我获取对应的 runbook 参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] 现在我已经掌握了所有必要的信息。让我看看这个 Pod 的详细 YAML 确认 volume 引用。
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
creationTimestamp: 2026-05-21T04:29:04Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
final
   💭 [问题定位] 现在让我确认一下这个 ConfigMap 是否存在。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                   DATA   AGE     LABELS
rc-volume-key-config   1      7m11s   rootcause-e2e=true
   💭 [问题定位] ConfigMap 存在，但 Events 明确指出 `configmap references non-existent config key: missing-key`。让我看看 ConfigMap 中有哪些 key。
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: ConfigMap
name: rc-volume-key-config
namespace: aiops-e2e
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
creationTimestamp: 2026-05-21T04:29:04Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
final
   💭 [问题定位] 有了这些证据，我对当前问题已经有清晰的判断。以下是完整的分析：

---

## 📋 全局 Pod 状态扫描结果

集群中总共 **65 个 Pod**，其中 **59 个 Running（正常）**，**1 个异常 Pod**。

---

## 🔴 异常 Pod 定位

| Pod | 命名空间 | 状态 | 关键事件 |
|-----|---------|------|---------|
| `rc-volume-configmap-missing-key` | `aiops-e2e` | **ContainerCreating** (卡住) | `MountVolume.SetUp failed` — ConfigMap 缺少 key |

---

## 📊 诊断分析

### 异常组归类

| 异常组 | 包含 Pod | 状态关键字 | 异常类型 | 兼容层 |
|-------|---------|-----------|---------|-------|
| VolumeMountFailed | `rc-volume-configmap-missing-key` | ContainerCreating | `VolumeMountFailed` | **L0** |

### 根因定位

Pod Events 原文清晰指示：
> **`MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key`**

这说明：
1. Pod 引用了 ConfigMap 卷 `rc-volume-key-config`
2. ConfigMap **存在**（有 1 个 data key）
3. 但 Pod volume 中试图引用的 key **`missing-key`** 在该 ConfigMap 中**不存在**

### 关键实体

| 实体 | 类型 | 说明 |
|-----|------|------|
| `rc-volume-configmap-missing-key` | Pod | 异常 Pod，卡在 ContainerCreating |
| `rc-volume-key-config` | ConfigMap | 存在，但缺少 Pod 引用的 `missing-key` |
| `config-volume` | Volume | Pod volume 定义，引用不存在的 key |

### 可能场景

1. **ConfigMap key 名称拼写错误** — Pod spec 中 volumes[].configMap.items 引用了一个 key，但 ConfigMap 中实际不存在该 key
2. **ConfigMap 数据不完整** — ConfigMap 的 data 字段包含了某些 key，但缺少被引用的 key `missing-key`

---

## ✅ 结论

| 字段 | 值 |
|------|-----|
| **layer** | L0 |
| **derived_layer** | L0 |
| **layers** | ["L0"] |
| **layer_name** | VolumeMountFailed |
| **pod_status_keyword** | ContainerCreating |
| **pod_abnormal_type** | VolumeMountFailed |
| **status_category** | storage_volume |
| **confidence** | 高 |
| **abnormal_pods** | 1 个 (`rc-volume-configmap-missing-key`) |
| **abnormal_groups** | VolumeMountFailed |

该异常属于 **L0（存储/卷/节点资源层）**，具体是 ConfigMap volume 引用了不存在的 key 导致挂载失败，Pod 卡在 ContainerCreating。需要修复 ConfigMap `rc-volume-key-config` 补充缺失的 `missing-key` 字段，或修正 Pod 的 volume 引用。
   ✅ [问题定位] 完成 (19.9s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[{'scenario': 'ConfigMap key 名称拼写错误或缺失', 'probability': '高', 'reason': 'Pod spec volumes[].configMap 引用了 key missing-key，但 ConfigMap rc-volume-key-config 中不存在该 key'}, {'scenario': 'ConfigMap 数据不完整', 'probability': '中', 'reason': 'ConfigMap 存在但仅有 1 个 data key，缺少 Pod 引用的 missing-key'}]
   entities=[{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}, {"type": "Volume", "name": "config-volume", "namespace": "aiops-e2e"}]
   reasoning=Pod rc-volume-configmap-missing-key 卡在 ContainerCreating，Events 明确显示 MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key。ConfigMap rc-volume-key-config 虽然存在（1个data key），但Pod volume引用的key missing-key不存在。属于L0存储/卷挂载失败。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "VolumeMountFailed", "confidence": 0.98, "reasoning": "Pod rc-volume-configmap-missing-key 卡在 ContainerCreating，Events 明确显示 MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key。ConfigMap rc-volume-key-config 虽然存在（1个data key），但Pod volume引用的key missing-key不存在。属于L0存储/卷挂载失败。", "abnormal_pods": [{"name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}, {"type": "Volume", "name": "config-volume", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "ConfigMap key 名称拼写错误或缺失", "probability": "高", "reason": "Pod spec volumes[].configMap 引用了 key missing-key，但 ConfigMap rc-volume-key-config 中不存在该 key"}, {"scenario": "ConfigMap 数据不完整", "probability": "中", "reason": "ConfigMap 存在但仅有 1 个 data key，缺少 Pod 引用的 missing-key"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-volume-configmap-missing-key                     0/1     ContainerCreating   0              7m6s    <none>           node1    <none>           <none>            app=rc-volume-configmap-missing-key,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/60610a1a989a4c48/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/60610a1a989a4c48/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/60610a1a989a4c48/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 98%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我将按照既有 evidence_plan 执行工具调用，采集关键证据。

## Step 1: 执行 ev-01 - 查看 Pod Events 确认 FailedMount 原文
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  78s (x11 over 7m30s)  kubelet            MountVolum
   💭 [证据链采集] **ev-01 已采集** ✅ — Pod Events 明确显示 `MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key`

## Step 2: 执行 ev-02 - 查看 ConfigMap 的 data 字段是否包含 missing-key
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: ConfigMap
name: rc-volume-key-config
namespace: aiops-e2e
   💭 [证据链采集] YAML 输出被截断了，我需要获取完整内容来确认 data 字段。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "apiVersion: v1\ndata:\n  existing-key: present\nkind: ConfigMap\nmetadata:\n  annotations:\n    kubectl.kubernetes.io/last-applied-configuration: |\n      {\"apiVersion\":
   💭 [证据链采集] **ev-02 已采集** ✅ — ConfigMap `rc-volume-key-config` 的 data 字段只有 `existing-key: present`，**不存在 Pod 引用的 key `missing-key`**。

## Step 3: 执行 ev-03 - 确认 Pod spec.volumes 中 configMap items 引用了 missing-key
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
   💭 [证据链采集] YAML 输出被截断了，我需要确认 volumes 中 `configMap.items` 的具体内容。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\"configMap\":{\"defaultMode\":420,\"items\":[{\"key\":\"missing-key\",\"path\":\"missing-key\"}],\"name\":\"rc-volume-key-config\"},\"name\":\"config-volume\"}", "stderr
   💭 [证据链采集] **ev-03 已采集** ✅ — Pod spec.volumes 中 `configVolume.items[0].key` 明确引用了 `missing-key`，而 ConfigMap 中只有 `existing-key`，没有 `missing-key`。

---

## 证据采集结论

### ✅ 已采集证据（3条 critical/important）

| 证据项 | 来源 | 关键内容 |
|-------|------|---------|
| **ev-01** ✅ | `kubectl describe pod` | Pod Events: `MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key`（11次重复） |
| **ev-02** ✅ | `kubectl get configmap -o yaml` | ConfigMap `rc-volume-key-config` data 字段仅包含 `existing-key: present`，**缺少 key `missing-key`** |
| **ev-03** ✅ | `kubectl get pod -o jsonpath` | Pod spec.volumes 中 `configMap.items[0].key=missing-key`，明确要求挂载一个不存在的 key |

### 🔍 根因分析

Pod `rc-volume-configmap-missing-key` 卡在 `ContainerCreating/Pending`，原因是 **ConfigMap volume 引用了不存在的 key**：

- ConfigMap `rc-volume-key-config`（存在于 `aiops-e2e` 命名空间）的 data 字段只包含 `existing-key` 一个 key
- Pod 的 volume `config-volume` 通过 `items[0].key: missing-key` 要求挂载一个叫 `missing-key` 的 key
- 该 key 在 ConfigMap 中不存在，导致 kubelet 无法挂载卷，Pod 持续卡在 `ContainerCreating`

### ⛔ 未发现冲突证据
- Pod 和 ConfigMap 均存在于指定命名空间，无 NotFound 冲突
- 事件内容与上游描述完全一致
   ✅ [证据链采集] 完成 (15.6s)
   📤 → 下游数据: evidence_items=10/10
   evidence_analysis={"evidence_plan":[{"id":"ev-01","description":"检查 Pod 当前状态和 Events（核心证据：确认 MountVolume.SetUp failed for configmap key missing-key）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e"},"purpose":"确认 Pod Events 中 FailedMount 的原文：configmap references non-existent config key: missing-key","evidence_type":"pod_events","target_scope":"Pod/rc-volume-configmap-missing-key","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-02","description":"检查 ConfigMap 内容，确认是否缺失 key 'missing-key'","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml","tool_args":{"kind":"configmap","name":"rc-volume-key-config","namespace":"aiops-e2e"},"purpose":"验证 ConfigMap 的 data 字段是否包含 Pod volume 引用的 key 'missing-key'","evidence_type":"resource_yaml","target_scope":"ConfigMap/rc-volume-key-config","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"ev-03","description":"检查 Pod YAML 中 volumes[].configMap 的 items 引用","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e"},"purpose":"确认 Pod spec.volumes 中 configMap 的 items 引用了 key: missing-key","evidence_type":"pod_spec","target_scope":"Pod/rc-volume-configmap-missing-key","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  78s (x11 over 7m30s)  kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n  Warning  FailedMount  3m13s                 kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-fbhds config-volume]: timed out waiting for the condition\n  Warning  FailedMount  55s (x2 over 5m27s)   kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  config-volume:\n    Type:      ConfigMap (a volume populated by a ConfigMap)\n    Name:      rc-volume-key-config\n    Optional:  false\n  kube-api-access-fbhds:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedMount  3m13s                 kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-fbhds config-volume]: timed out waiting for the condition\n  Warning  FailedMount  78s (x11 over 7m30s)  kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n  Warning  FailedMount  55s (x2 over 5m27s)   kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/60610a1a989a4c48/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/60610a1a989a4c48/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/60610a1a989a4c48/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: ConfigMap\nname: rc-volume-key-config\nnamespace: aiops-e2e","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/60610a1a989a4c48/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/60610a1a989a4c48/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/60610a1a989a4c48/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"apiVersion: v1\\ndata:\\n  existing-key: present\\nkind: ConfigMap\\nmetadata:\\n  annotations:\\n    kubectl.kubernetes.io/last-applied-configuration: |\\n      {\\\"apiVersion\\\":\\\"v1\\\",\\\"data\\\":{\\\"existing-key\\\":\\\"present\\\"},\\\"kind\\\":\\\"ConfigMap\\\",\\\"metadata\\\":{\\\"annotations\\\":{},\\\"labels\\\":{\\\"rootcause-e2e\\\":\\\"true\\\"},\\\"name\\\":\\\"rc-volume-key-config\\\",\\\"namespace\\\":\\\"aiops-e2e\\\"}}\\n  creationTimestamp: \\\"2026-05-21T04:29:04Z\\\"\\n  labels:\\n    rootcause-e2e: \\\"true\\\"\\n  name: rc-volume-key-config\\n  namespace: aiops-e2e\\n  resourceVersion: \\\"52517160\\\"\\n  uid: 5468219a-cec8-424b-b490-66fd39c82b58\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/60610a1a989a4c48/tools/003-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/60610a1a989a4c48/tools/003-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/60610a1a989a4c48/tools/003-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T04:29:04Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-configmap-missing-key, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"config-volume\", \"configMap\": \"rc-volume-key-config\"}\n- {\"name\": \"kube-api-access-fbhds\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/60610a1a989a4c48/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/60610a1a989a4c48/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/60610a1a989a4c48/tools/004-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\\"configMap\\\":{\\\"defaultMode\\\":420,\\\"items\\\":[{\\\"key\\\":\\\"missing-key\\\",\\\"path\\\":\\\"missing-key\\\"}],\\\"name\\\":\\\"rc-volume-key-config\\\"},\\\"name\\\":\\\"config-volume\\\"}\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/60610a1a989a4c48/tools/005-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/60610a1a989a4c48/tools/005-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/60610a1a989a4c48/tools/005-evidence-run_bash_command.summary.txt"}],"llm_analysis":"**ev-03 已采集** ✅ — Pod spec.volumes 中 `configVolume.items[0].key` 明确引用了 `missing-key`，而 ConfigMap 中只有 `existing-key`，没有 `missing-key`。\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据（3条 critical/important）\n\n| 证据项 | 来源 | 关键内容 |\n|-------|------|---------|\n| **ev-01** ✅ | `kubectl describe pod` | Pod Events: `MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key`（11次重复） |\n| **ev-02** ✅ | `kubectl get configmap -o yaml` | ConfigMap `rc-volume-key-config` data 字段仅包含 `existing-key: present`，**缺少 key `missing-key`** |\n| **ev-03** ✅ | `kubectl get pod -o jsonpath` | Pod spec.volumes 中 `configMap.items[0].key=missing-key`，明确要求挂载一个不存在的 key |\n\n### 🔍 根因分析\n\nPod `rc-volume-configmap-missing-key` 卡在 `ContainerCreating/Pending`，原因是 **ConfigMap volume 引用了不存在的 key**：\n\n- ConfigMap `rc-volume-key-config`（存在于 `aiops-e2e` 命名空间）的 data 字段只包含 `existing-key` 一个 key\n- Pod 的 volume `config-volume` 通过 `items[0].key: missing-key` 要求挂载一个叫 `missing-key` 的 key\n- 该 key 在 ConfigMap 中不存在，导致 kubelet 无法挂载卷，Pod 持续卡在 `ContainerCreating`\n\n### ⛔ 未发现冲突证据\n- Pod 和 ConfigMap 均存在于指定命名空间，无 NotFound 冲突\n- 事件内容与上游描述完全一致","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 10/10 项，完整度 100%；实际执行工具 12 个，匹配计划 3 个，未规划证据 9 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":10,"environment_evidence_collected":10,"environment_evidence_completeness":1.0,"executed_tool_count":12,"matched_tool_count":3,"unplanned_tool_count":9,"evidence_inventory":[{"id":"ev-01","description":"检查 Pod 当前状态和 Events（核心证据：确认 MountVolume.SetUp failed for configmap key missing-key）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","purpose":"确认 Pod Events 中 FailedMount 的原文：configmap references non-existent config key: missing-key","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-02","description":"检查 ConfigMap 内容，确认是否缺失 key 'missing-key'","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml","purpose":"验证 ConfigMap 的 data 字段是否包含 Pod volume 引用的 key 'missing-key'","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-03","description":"检查 Pod YAML 中 volumes[].configMap 的 items 引用","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","purpose":"确认 Pod spec.volumes 中 configMap 的 items 引用了 key: missing-key","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | ev-01 | critical | ✅ | kubectl_describe | 检查 Pod 当前状态和 Events（核心证据：确认 MountVolume.SetUp... | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` |
   | ev-02 | critical | ✅ | kubectl_get_yaml | 检查 ConfigMap 内容，确认是否缺失 key 'missing-key' | `kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml` |
   | ev-03 | important | ✅ | kubectl_get_yaml | 检查 Pod YAML 中 volumes[].configMap 的 items 引用 | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (14.3s)
   📤 → 下游数据: root_cause=Pod rc-volume-configmap-missing-key (namespace: aiops-e2e) 卡在 ContainerCreating/Pending 状态，根因是 volume "config-volume" 通过 configMap.items[0].key=missing-key 引用了一个 ConfigMap 中不存在的 key。ConfigMap rc-volume-key-config 的 data 字段仅包含 existing-key: present，缺少 missing-key。kubelet Events 已报 11 次 FailedMount（78s over 7m30s）。集群其余 59 个 Pod 均正常运行，故障隔离在此 Pod 的配置错误上。
   confidence=98%
   causal_chain={"root_cause": "Pod spec.volumes[].configMap.items[0].key 引用了一个在 ConfigMap 中不存在的 key 'missing-key'（ConfigMap rc-volume-key-config 仅包含 existing-key）", "propagation": "kubelet 在挂载 config-volume 时检查 ConfigMap 内容，发现 items[0].key=missing-key 在 ConfigMap data 字段中不存在，由于 Optional=false（默认），kubelet 无法完成挂载 → 持续重试并报 FailedMount", "direct_cause": "ConfigMap rc-volume-key-config 的 data 字段缺少 Pod 要求的 key 'missing-key'", "manifestation": "Pod rc-volume-configmap-missing-key 卡在 ContainerCreating/Pending 状态，无法进入 Running，Events 持续报 MountVolume.SetUp failed"}
   rca_analysis={"phenomenon": "集群 aiops-e2e 命名空间中 Pod rc-volume-configmap-missing-key 卡在 ContainerCreating/Pending 状态，kubelet Events 持续报 FailedMount：MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key", "evidence_inventory": [{"id": "ev-01", "source": "kubectl_describe", "content": "Pod Events: FailedMount x11 over 7m30s — MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key", "reliability": "高"}, {"id": "ev-02", "source": "kubectl_get_yaml / run_bash_command", "content": "ConfigMap rc-volume-key-config 的 data 字段仅包含 existing-key: present，缺失 key missing-key", "reliability": "高"}, {"id": "ev-03", "source": "kubectl_get_yaml / run_bash_command", "content": "Pod spec.volumes[0].configMap.items[0].key=missing-key，明确引用不存在的 key", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "集群 65 行 Pod 中仅此 1 个异常，其余 59 个 Running", "reliability": "高"}, {"id": "layer_5", "source": "kubectl_get_by_name", "content": "ConfigMap rc-volume-key-config 存在，DATA=1，age=7m11s", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "ev-01", "raw_data": "Warning FailedMount 78s (x11 over 7m30s) kubelet MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key", "interpretation": "kubelet 明确报告 ConfigMap volume 挂载失败，原因是 ConfigMap 中不存在 key 'missing-key'，这是最直接的故障证据"}, {"evidence_id": "ev-02", "raw_data": "data:\n  existing-key: present\nkind: ConfigMap\nname: rc-volume-key-config", "interpretation": "ConfigMap rc-volume-key-config 存在，但 data 字段只包含一个 key 'existing-key'，确实没有 Pod 引用的 'missing-key'"}, {"evidence_id": "ev-03", "raw_data": "{\"configMap\":{\"defaultMode\":420,\"items\":[{\"key\":\"missing-key\",\"path\":\"missing-key\"}],\"name\":\"rc-volume-key-config\"},\"name\":\"config-volume\"}", "interpretation": "Pod volume 的 configMap.items[0].key 明确指定了 'missing-key'，且 Optional 默认为 false（非可选），因此 kubelet 必须找到该 key 才能完成挂载"}, {"evidence_id": "layer_1", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59}", "interpretation": "集群中仅有此 1 个异常 Pod，其余 59 个 Pod 均正常运行，说明问题隔离在此 Pod 的 ConfigMap volume 配置上，非集群级故障"}, {"evidence_id": "layer_5", "raw_data": "rc-volume-key-config 1 7m11s rootcause-e2e=true", "interpretation": "ConfigMap 本身存在且已创建，仅包含 1 个 data key，与 Pod 期望的 'missing-key' 不匹配"}], "causal_chain": {"root_cause": "Pod spec.volumes[].configMap.items[0].key 引用了一个在 ConfigMap 中不存在的 key 'missing-key'（ConfigMap rc-volume-key-config 仅包含 existing-key）", "propagation": "kubelet 在挂载 config-volume 时检查 ConfigMap 内容，发现 items[0].key=missing-key 在 ConfigMap data 字段中不存在，由于 Optional=false（默认），kubelet 无法完成挂载 → 持续重试并报 FailedMount", "direct_cause": "ConfigMap rc-volume-key-config 的 data 字段缺少 Pod 要求的 key 'missing-key'", "manifestation": "Pod rc-volume-configmap-missing-key 卡在 ContainerCreating/Pending 状态，无法进入 Running，Events 持续报 MountVolume.SetUp failed"}, "root_cause": "Pod rc-volume-configmap-missing-key (namespace: aiops-e2e) 卡在 ContainerCreating/Pending 状态，根因是 volume \"config-volume\" 通过 configMap.items[0].key=missing-key 引用了一个 ConfigMap 中不存在的 key。ConfigMap rc-volume-key-config 的 data 字段仅包含 existing-key: present，缺少 missing-key。kubelet Events 已报 11 次 FailedMount（78s over 7m30s）。集群其余 59 个 Pod 均正常运行，故障隔离在此 Pod 的配置错误上。", "root_cause_summary": "Pod rc-volume-configmap-missing-key (namespace: aiops-e2e) 卡在 ContainerCreating/Pending 状态，根因是 volume \"config-volume\" 通过 configMap.items[0].key=missing-key 引用了一个 ConfigMap 中不存在的 key。ConfigMap rc-volume-key-config 的 data 字段仅包含 existing-key: present，缺少 missing-key。kubelet Events 已报 11 次 FailedMount（78s over 7m30s）。集群其余 59 个 Pod 均正常运行，故障隔离在此 Pod 的配置错误上。", "confidence": 0.98, "confidence_reason": "有直接证据链：Pod Events 文本明确报错（ev-01）、ConfigMap data 确认缺失该 key（ev-02）、Pod spec 确认引用了不存在的 key（ev-03），三者闭环且完全一致。异常组仅 1 个 Pod，无冲突证据。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [{"cause": "Pod 引用了错误的 ConfigMap 名称", "probability": "low", "reason": "Pod 引用的 ConfigMap 名称 rc-volume-key-config 经确认存在于同一 namespace，且 age 匹配，名称正确"}, {"cause": "ConfigMap 尚未传播到 node", "probability": "low", "reason": "ConfigMap 已存在 7m11s，且错误信息明确说是 key 不存在而非 ConfigMap 不存在"}, {"cause": "网络或 node 问题导致挂载失败", "probability": "low", "reason": "Events 明确报 'configmap references non-existent config key'，非网络/节点层面的错误"}], "limitations": "未获取 ConfigMap 完整 YAML 的 data 字段全文（ev-02 仅看到摘要），但 run_bash_command 已补充确认 data 仅含 existing-key: present；Pod YAML 中 volumes[].configMap 未设置 optional=true，因此默认 optional=false，必须找到该 key 才能挂载", "llm_raw_analysis": "L0 根因分析完成。异常组 g1 仅包含 1 个 Pod rc-volume-configmap-missing-key。所有证据均指向同一个原因：ConfigMap 缺少 Pod 引用的 key。kubectl describe 的 Events 文本（ev-01）是最高权重证据，明确说明错误类型；ConfigMap data 内容（ev-02）和 Pod spec volumes 配置（ev-03）提供了完整因果链的输入和输出验证。无其他异常 Pod 需要分析。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-volume-configmap-missing-key (namespace: aiops-e2e) 卡在 ContainerCreating/Pending 状态，根因是 volume "config-volume" 通过 configMap.items[0].key=missin...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod spec.volumes[].configMap.items[0].key 引用了一个在 ConfigMap 中不存在的 key 'missing-key'（ConfigMap rc-volume-key-config 仅包含 existing-key）
     传导机制: kubelet 在挂载 config-volume 时检查 ConfigMap 内容，发现 items[0].key=missing-key 在 ConfigMap data 字段中不存在，由于 Optional=false（默认），kubelet 无法完成挂载 → 持续重试并报 FailedMount
     最终表现: Pod rc-volume-configmap-missing-key 卡在 ContainerCreating/Pending 状态，无法进入 Running，Events 持续报 MountVolume.SetUp failed


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (18.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6139 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 8.4s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将根据您提供的分析结果，生成一份详尽、完整的诊断报告。

报告将直接回答您“我的集群有什么问题”这一核心问题，并严格遵循诊断模板格式，引用所有可用证据。

---
## 📊 诊断概览

**核心问题总结**：您的集群整体运行正常（59/65 Pod 为 `Running` 状态），但存在 **1 个 Pod** 因**配置错误**卡在 `ContainerCreating` 状态，无法启动。该问题与集群基础设施无关，是一个隔离的、配置层面的故障。

| 项目 | 内容 |
|------|------|
| **集群整体状态** | 大部分 Pod (59/65) 正常运行，1 个异常 Pod |
| **Pod异常状态** | ContainerCreating (VolumeMountFailed) |
| **兼容归因层** | L0 - 存储/卷挂载失败 |
| **问题分类** | `VolumeMountFailed` (ConfigMap Key 缺失) |
| **置信度** | **高 (98%)** |
| **证据完整度** | 3/3 (100%) |

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 集群总体 | 包含 65 个 Pod，其中 59 个正常运行 |
| 异常 Pod | `rc-volume-configmap-missing-key` (Namespace: `aiops-e2e`) |
| Pod 状态 | `ContainerCreating` / `Pending` |
| 关键事件 | `MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key` |
| 涉及 ConfigMap | `rc-volume-key-config` (Namespace: `aiops-e2e`) |
| 涉及 Volume | `config-volume` |

---
## 🕵️ 证据链

### 已采集证据
所有关键证据均已采集，证据链完整。

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | **Pod 状态与事件** | `kubectl_describe` (ev-01) | `status: Pending` <br> `Warning FailedMount 78s (x11 over 7m30s) kubelet MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key` <br> `Warning FailedMount 3m13s kubelet Unable to attach or mount volumes...` | 确认 Pod 因卷挂载失败而卡住。事件明确指出错误根因：引用了不存在的 ConfigMap key `missing-key`。 |
| 2 | **ConfigMap 内容** | `run_bash_command` (ev-02) | `apiVersion: v1`<br>`data:`<br>`  existing-key: present`<br>`kind: ConfigMap`<br>`...` | 确认 ConfigMap `rc-volume-key-config` 只包含一个 key `existing-key`，**缺少** Pod 要求的 `missing-key`。 |
| 3 | **Pod 卷定义** | `run_bash_command` (ev-03) | `{"configMap":{"defaultMode":420,"items":[{"key":"missing-key","path":"missing-key"}],"name":"rc-volume-key-config"},"name":"config-volume"}` | Pod YAML 中 `volumes` 定义了一个名为 `config-volume` 的卷，它引用 ConfigMap `rc-volume-key-config`，并通过 `items` 字段明确要求挂载 `missing-key` 这个 key。 |

### 证据关联分析
- **证据 #1 + 证据 #2 印证**：Pod 事件错误 `configmap references non-existent config key: missing-key` 与 ConfigMap 内容 `data: existing-key: present` 完全吻合，证实了问题的根本原因为**配置不匹配**。
- **证据 #3 定位问题源**：Pod 的 YAML 定义 `spec.volumes[].configMap.items[].key` 明确指向了 `missing-key`，这直接导致了卷挂载失败。

### 缺失证据
无。所有关键证据都已采集完毕，证据链闭环。

---
## 🎯 根因分析

### 因果链
```
┌──────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                 │
│ Pod 配置错误：spec.volumes[].configMap.items[0].key 设置了 "missing-key" │
│ 但 ConfigMap 'rc-volume-key-config' 的 data 字段不包含这个 key        │
└──────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                 │
│ kubelet 在节点 'node1' 上挂载卷时，通过 items 字段定位 ConfigMap key ── │
│ → 发现 'missing-key' 不存在 → 由于参数 optional=false (默认)，挂载失败  │
└──────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                 │
│ 卷 'config-volume' 挂载失败（MountVolume.SetUp failed）                  │
└──────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                             │
│ Pod 状态 : ContainerCreating, Ready: False                              │
│ Events 持续报错 FailedMount，共 11 次                                   │
└──────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (FailedMount 事件)、证据 #2 (ConfigMap 内容) 和证据 #3 (Pod Volume 定义)，问题的根本原因是**Pod `rc-volume-configmap-missing-key` 的卷挂载配置错误**。

Pod YAML 中的 `volumes[].configMap` 通过 `items` 字段指定了一个键 `missing-key`，但同命名空间下的 `ConfigMap rc-volume-key-config` 中**不存在**这个键。这导致 kubelet 无法完成卷的挂载，Pod 持续卡在 `ContainerCreating`/`Pending` 状态。

**置信度**：高 (98%)
- ✅ 集群其他 59 个 Pod 正常运行，排除了集群基础设施问题。
- ✅ `kubectl describe` 事件直接、明确地指出了错误原因。
- ✅ `run_bash_command` 对 ConfigMap 和 Pod 内容的检查，为事件提供了精确的证据。

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 修正 ConfigMap，添加缺失的 Key**
向 ConfigMap `rc-volume-key-config` 中添加 Pod 所需的 `missing-key`。这是最直接且影响最小的修复方式。
```bash
# 添加缺失的 key (value 为示例，请根据实际需求填写)
kubectl patch configmap rc-volume-key-config -n aiops-e2e -p '{"data":{"missing-key":"your-value-here"}}'
```
*依据*：证据 #2 确认 ConfigMap 缺少此 key。添加后，kubelet 将自动挂载，Pod 会进入 `Running` 状态。

**2. [备选] 修正 Pod YAML，移除对缺失 Key 的引用**
如果 Pod 实际上不需要 `missing-key`，或者该 key 是错误配置，应修改 Pod YAML 以移除对它的引用。
```bash
# 1) 导出 Deployment/ReplicaSet/Pod 的 YAML
kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml > pod-fix.yaml

# 2) 编辑该文件 (手动操作)：
#    a) 在 volumes[].configMap 下删除整个 items 字段，使 Volume 引用整个 ConfigMap。
#    或者
#    b) 修改 items[0].key 为 'existing-key' 或其他存在的键。
#    或者
#    c) 在 spec.volumes[].configMap 下添加 optional: true

# 3) 重新应用 YAML (需先删除旧的 Pod)
#    kubectl delete pod rc-volume-configmap-missing-key -n aiops-e2e --force --grace-period=0
#    kubectl apply -f pod-fix.yaml
```
*依据*：证据 #3 显示正是 YAML 中的这个错误配置导致了问题。

### 后续优化
1. **配置规范**：建议在 CI/CD 流程中加入对 ConfigMap 与实际 Pod Volume 引用的校验，防止类似的配置错配问题再次发生。
2. **资源评估**：该 Pod 的 `command: [ "sh", "-c", "sleep 3600" ]` 是一个测试占位符，请确认生产环境中是否已替换为正确的应用命令。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 更新 ConfigMap | `kubectl patch configmap rc-volume-key-config -n aiops-e2e -p '{"data":{"missing-key":"dummy"}}'` | `configmap/rc-volume-key-config patched` |
| 2. 等待 Pod 自动恢复 | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -w` | STATUS 从 `ContainerCreating` 变为 `Running`，READY 变为 `1/1` |
| 3. 最终确认 | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e` | `STATUS: Running`, `RESTARTS: 0` |

---
## ⚠️ 注意事项
- 除了当前 Pod 外，集群中没有发现其他问题。
- 如果集群中有依赖 `ConfigMap rc-volume-key-config` 的其他 Pod，请注意更新 ConfigMap 时不要引入不兼容的数据。

---

## 📊 性能统计

├─ 总耗时: 1.1m
├─ 问题定位: 19.9s (29%) ✅
├─ 证据链采集: 15.6s (23%) ✅
├─ 根因分析: 14.3s (21%) ✅
├─ 汇总总结: 18.7s (27%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 13 次
```

📋 诊断追踪

- **核心 Runbook**: pod-volume-mount-failed
- **参考 Runbook**: pod-volume-mount-failed
- **工具调用**: 13 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
