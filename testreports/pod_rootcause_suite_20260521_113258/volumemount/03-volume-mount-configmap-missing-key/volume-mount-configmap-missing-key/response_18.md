======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: a38b38e1f9e04fdf]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我先对集群进行全面扫描，看看所有 Pod 的状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59}
NAMESPACE         NAME                                                READY   STATUS              RESTARTS       A
   💭 [问题定位] 发现了一个异常 Pod。让我进一步看看它的详情。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  63s (x12 over 9m17s)  kubelet            MountVolum
   💭 [问题定位] 现在让我获取关联的 ConfigMap 信息，以及查看这个 Pod 的标签。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                   DATA   AGE     LABELS
rc-volume-key-config   1      9m18s   rootcause-e2e=true
   💭 [问题定位] 现在我已经掌握了所有必要信息。让我完成诊断分析。

## 诊断分析

### 全局扫描结果
集群共 65 个 Pod，其中 **59 个 Running 正常**，**1 个异常 Pod**。

### 当前异常 Pod

| 字段 | 值 |
|------|-----|
| **Pod 名称** | `rc-volume-configmap-missing-key` |
| **命名空间** | `aiops-e2e` |
| **状态** | `ContainerCreating`（实际处于 Pending） |
| **节点** | `node1` |
| **重启次数** | 0 |
| **标签** | `pod_abnormal_type=VolumeMountFailed` |

### 异常类型与关键证据

**异常类型**：`VolumeMountFailed`（卷挂载失败）

**核心证据** — Pod Events 原文：
```
MountVolume.SetUp failed for volume "config-volume" : 
configmap references non-existent config key: missing-key
```

Pod 的 `.spec.volumes[]` 中引用了名为 `rc-volume-key-config` 的 ConfigMap volume，该 ConfigMap **确实存在**（包含 1 个 data 条目），但 Pod 引用的 key **`missing-key`** 在该 ConfigMap 中**不存在**。

### 分层映射

| 字段 | 值 |
|------|-----|
| **layer** | L0 |
| **derived_layer** | L0 |
| **layers** | [L0] |
| **layer_name** | Volume Mount Failed |
| **status_category** | storage_volume |
| **pod_status_keyword** | ContainerCreating |
| **pod_abnormal_type** | VolumeMountFailed |
| **confidence** | 高 |

### 可能场景

1. **ConfigMap key 拼写错误** — Pod 的 volume 配置中引用了 `missing-key`，但 ConfigMap `rc-volume-key-config` 中不存在该 key。
2. **ConfigMap 内容变更滞后** — 业务更新了 ConfigMap 但未同步更新 volume 中引用的 key 名。
3. **配置模板错误** — 部署模板中 key 名称与实际 ConfigMap data 不匹配。

### 关键实体

- **异常 Pod**: `aiops-e2e/rc-volume-configmap-missing-key`
- **ConfigMap**: `aiops-e2e/rc-volume-key-config`（存在但缺少 key `missing-key`）
- **Volume 名称**: `config-volume`
- **节点**: `node1`
   ✅ [问题定位] 完成 (13.1s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[{'scenario': 'ConfigMap key 拼写错误', 'probability': '高', 'reason': 'Pod volume配置引用了missing-key，但ConfigMap rc-volume-key-config中不存在该key'}, {'scenario': 'ConfigMap 内容变更滞后', 'probability': '低', 'reason': 'ConfigMap存在但缺少引用的key，可能是更新不同步'}, {'scenario': '部署模板配置错误', 'probability': '中', 'reason': '部署模板中key名称与实际ConfigMap data不匹配'}]
   entities=[{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}]
   reasoning=集群存在1个异常Pod rc-volume-configmap-missing-key（aiops-e2e命名空间），状态为ContainerCreating/Pending，标签pod_abnormal_type=VolumeMountFailed。Events显示MountVolume.SetUp failed: configmap references non-existent config key: missing-key。ConfigMap rc-volume-key-config存在但缺少Pod引用的key 'missing-key'。符合L0存储卷异常（storage_volume），根因为volume引用不存在的ConfigMap key。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "Volume Mount Failed", "confidence": 0.95, "reasoning": "集群存在1个异常Pod rc-volume-configmap-missing-key（aiops-e2e命名空间），状态为ContainerCreating/Pending，标签pod_abnormal_type=VolumeMountFailed。Events显示MountVolume.SetUp failed: configmap references non-existent config key: missing-key。ConfigMap rc-volume-key-config存在但缺少Pod引用的key 'missing-key'。符合L0存储卷异常（storage_volume），根因为volume引用不存在的ConfigMap key。", "abnormal_pods": [{"name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "ConfigMap key 拼写错误", "probability": "高", "reason": "Pod volume配置引用了missing-key，但ConfigMap rc-volume-key-config中不存在该key"}, {"scenario": "ConfigMap 内容变更滞后", "probability": "低", "reason": "ConfigMap存在但缺少引用的key，可能是更新不同步"}, {"scenario": "部署模板配置错误", "probability": "中", "reason": "部署模板中key名称与实际ConfigMap data不匹配"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-volume-configmap-missing-key                     0/1     ContainerCreating   0              9m15s   <none>           node1    <none>           <none>            app=rc-volume-configmap-missing-key,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/a38b38e1f9e04fdf/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/a38b38e1f9e04fdf/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/a38b38e1f9e04fdf/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我直接执行既有 evidence_plan 中的工具。先并行调用所有独立工具：

e1: kubectl describe pod
e2: kubectl_get_yaml configmap
e3: kubectl_get_yaml pod
e4: kubectl_events

四个工具没有依赖关系，可以同时执行。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  81s (x12 over 9m35s)  kubelet            MountVolum
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
81s (x12 over 9m35s)   Warning   FailedMount   Pod/rc-volume-configmap-missing-key   MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent c
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
creationTimestamp: 2026-05-21T04:29:04Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
final
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: ConfigMap
name: rc-volume-key-config
namespace: aiops-e2e
   💭 [证据链采集] 很好，关键证据已采集。e2（ConfigMap YAML）需要查看完整输出，让我读取完整的 ConfigMap YAML 来确认 data 字段中是否确实缺少 `missing-key` 这个 key。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "apiVersion: v1\ndata:\n  existing-key: present\nkind: ConfigMap\nmetadata:\n  annotations:\n    kubectl.kubernetes.io/last-applied-configuration: |\n      {\"apiVersion\":
   💭 [证据链采集] 现在让我查看 Pod 的完整 YAML，确认 volumes 中 items 的配置：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "      {\"apiVersion\":\"v1\",\"kind\":\"Pod\",\"metadata\":{\"annotations\":{\"aiops.e2e/runbook\":\"pod-volume-mount-failed.md\"},\"labels\":{\"app\":\"rc-volume-configma
   💭 [证据链采集] 所有证据已采集完毕。现在给出结论。

---

## 📋 证据采集结论

### ✅ 已采集证据（4项）

1. **e1 - Pod Describe（已确认）**：Pod `rc-volume-configmap-missing-key` 状态为 **Pending**，容器处于 `ContainerCreating`。Events 明确指出：
   - `MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key`
   - 该 Warning 已出现 **12 次**，持续 9m35s，是根因证据。

2. **e2 - ConfigMap YAML（已确认）**：ConfigMap `rc-volume-key-config` 的 `data` 字段只包含一个 key：
   ```yaml
   data:
     existing-key: present   # ← 只有这个 key
   ```
   **缺少 Pod 引用的 `missing-key`**。

3. **e3 - Pod YAML（已确认）**：Pod `spec.volumes[].configMap` 配置如下：
   ```yaml
   volumes:
   - configMap:
       items:
       - key: "missing-key"      # ← 引用了不存在的 key
         path: "missing-key"
       name: "rc-volume-key-config"
     name: config-volume
   ```
   明确指定了 `items[0].key=missing-key`，且 `ConfigMap` 中 **不存在此 key**。

4. **e4 - Pod Events 完整时间线（已确认）**：
   - `81s (x12 over 9m35s)` — `configmap references non-existent config key: missing-key`
   - `5m18s` / `45s (x3 over 7m32s)` — `Unable to attach or mount volumes: timed out waiting for the condition`
   - 无其他异常状态并发。

### ❌ 冲突/负向证据
- 无冲突证据。所有对象（Pod、ConfigMap）均正常存在于 `aiops-e2e` 命名空间。

### 🔍 根因判断
**ConfigMap volume key 引用错误** — Pod volume `config-volume` 通过 `items` 指定引用 key `missing-key`，但 ConfigMap `rc-volume-key-config` 的 data 中仅有 `existing-key`，不存在 `missing-key`。ConfigMap 本身存在且完整，故障点在 **部署模板或配置中的 key 名称拼写错误**（将 `existing-key` 误写为 `missing-key`）。

### 💡 修复建议
方案一：修改 Pod volume items 中的 key 为正确的 `existing-key`。
方案二：在 ConfigMap `rc-volume-key-config` 中增加 key `missing-key`。
   ✅ [证据链采集] 完成 (16.5s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"检查异常Pod rc-volume-configmap-missing-key的当前状态和Events确认ConfigMap key缺失错误","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e"},"purpose":"确认Pod当前状态和FailedMount事件原文，验证ConfigMap key missing-key不存在","evidence_type":"real_env","target_scope":"aiops-e2e/rc-volume-configmap-missing-key","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"检查ConfigMap rc-volume-key-config的内容，确认缺少Pod引用的key 'missing-key'","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml","tool_args":{"kind":"configmap","name":"rc-volume-key-config","namespace":"aiops-e2e"},"purpose":"验证ConfigMap的data字段是否包含Pod volume引用的key: missing-key","evidence_type":"real_env","target_scope":"aiops-e2e/rc-volume-key-config","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"检查Pod的volume配置spec，确认volumes引用ConfigMap和items配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e"},"purpose":"查看Pod spec.volumes中ConfigMap volume的items配置，确认引用的key名称","evidence_type":"real_env","target_scope":"aiops-e2e/rc-volume-configmap-missing-key","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e4","description":"查看命名空间事件过滤到该Pod，确认FailedMount事件时间线","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-configmap-missing-key --sort-by='.lastTimestamp'","tool_args":{"resource_type":"pod","resource_name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e"},"purpose":"获取Pod相关事件的完整时间线，确认FailedMount持续状态","evidence_type":"real_env","target_scope":"aiops-e2e","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  81s (x12 over 9m35s)  kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n  Warning  FailedMount  5m18s                 kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-fbhds config-volume]: timed out waiting for the condition\n  Warning  FailedMount  45s (x3 over 7m32s)   kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  config-volume:\n    Type:      ConfigMap (a volume populated by a ConfigMap)\n    Name:      rc-volume-key-config\n    Optional:  false\n  kube-api-access-fbhds:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedMount  5m18s                 kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-fbhds config-volume]: timed out waiting for the condition\n  Warning  FailedMount  81s (x12 over 9m35s)  kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n  Warning  FailedMount  45s (x3 over 7m32s)   kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a38b38e1f9e04fdf/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a38b38e1f9e04fdf/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a38b38e1f9e04fdf/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n81s (x12 over 9m35s)   Warning   FailedMount   Pod/rc-volume-configmap-missing-key   MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n5m18s                  Warning   FailedMount   Pod/rc-volume-configmap-missing-key   Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-fbhds config-volume]: timed out waiting for the condition\n45s (x3 over 7m32s)    Warning   FailedMount   Pod/rc-volume-configmap-missing-key   Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a38b38e1f9e04fdf/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a38b38e1f9e04fdf/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a38b38e1f9e04fdf/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T04:29:04Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-configmap-missing-key, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"config-volume\", \"configMap\": \"rc-volume-key-config\"}\n- {\"name\": \"kube-api-access-fbhds\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a38b38e1f9e04fdf/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a38b38e1f9e04fdf/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a38b38e1f9e04fdf/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: ConfigMap\nname: rc-volume-key-config\nnamespace: aiops-e2e","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a38b38e1f9e04fdf/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a38b38e1f9e04fdf/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a38b38e1f9e04fdf/tools/004-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"apiVersion: v1\\ndata:\\n  existing-key: present\\nkind: ConfigMap\\nmetadata:\\n  annotations:\\n    kubectl.kubernetes.io/last-applied-configuration: |\\n      {\\\"apiVersion\\\":\\\"v1\\\",\\\"data\\\":{\\\"existing-key\\\":\\\"present\\\"},\\\"kind\\\":\\\"ConfigMap\\\",\\\"metadata\\\":{\\\"annotations\\\":{},\\\"labels\\\":{\\\"rootcause-e2e\\\":\\\"true\\\"},\\\"name\\\":\\\"rc-volume-key-config\\\",\\\"namespace\\\":\\\"aiops-e2e\\\"}}\\n  creationTimestamp: \\\"2026-05-21T04:29:04Z\\\"\\n  labels:\\n    rootcause-e2e: \\\"true\\\"\\n  name: rc-volume-key-config\\n  namespace: aiops-e2e\\n  resourceVersion: \\\"52517160\\\"\\n  uid: 5468219a-cec8-424b-b490-66fd39c82b58\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a38b38e1f9e04fdf/tools/005-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a38b38e1f9e04fdf/tools/005-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a38b38e1f9e04fdf/tools/005-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"      {\\\"apiVersion\\\":\\\"v1\\\",\\\"kind\\\":\\\"Pod\\\",\\\"metadata\\\":{\\\"annotations\\\":{\\\"aiops.e2e/runbook\\\":\\\"pod-volume-mount-failed.md\\\"},\\\"labels\\\":{\\\"app\\\":\\\"rc-volume-configmap-missing-key\\\",\\\"pod_abnormal_type\\\":\\\"VolumeMountFailed\\\",\\\"rootcause-e2e\\\":\\\"true\\\"},\\\"name\\\":\\\"rc-volume-configmap-missing-key\\\",\\\"namespace\\\":\\\"aiops-e2e\\\"},\\\"spec\\\":{\\\"containers\\\":[{\\\"command\\\":[\\\"sh\\\",\\\"-c\\\",\\\"sleep 3600\\\"],\\\"image\\\":\\\"busybox:1.36\\\",\\\"imagePullPolicy\\\":\\\"Never\\\",\\\"name\\\":\\\"app\\\",\\\"volumeMounts\\\":[{\\\"mountPath\\\":\\\"/etc/config\\\",\\\"name\\\":\\\"config-volume\\\",\\\"readOnly\\\":true}]}],\\\"volumes\\\":[{\\\"configMap\\\":{\\\"items\\\":[{\\\"key\\\":\\\"missing-key\\\",\\\"path\\\":\\\"missing-key\\\"}],\\\"name\\\":\\\"rc-volume-key-config\\\"},\\\"name\\\":\\\"config-volume\\\"}]}}\\n  creationTimestamp: \\\"2026-05-21T04:29:04Z\\\"\\n  labels:\\n    app: rc-volume-configmap-missing-key\\n    pod_abnormal_type: VolumeMountFailed\\n    rootcause-e2e: \\\"true\\\"\\n  name: rc-volume-configmap-missing-key\\n  namespace: aiops-e2e\\n  resourceVersion: \\\"52517164\\\"\\n  uid: d39235fa-766b-4a08-8ba7-1cb64eb6456a\\nspec:\\n--\\n      name: config-volume\\n      readOnly: true\\n    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount\\n      name: kube-api-access-fbhds\\n      readOnly: true\\n  dnsPolicy: ClusterFirst\\n  enableServiceLinks: true\\n  nodeName: node1\\n  preemptionPolicy: PreemptLowerPriority\\n  priority: 0\\n  restartPolicy: Always\\n--\\n    name: config-volume\\n  - name: kube-api-access-fbhds\\n    projected:\\n      defaultMode: 420\\n      sources:\\n      - serviceAccountToken:\\n          expirationSeconds: 3607\\n          path: token\\n      - configMap:\\n          items:\\n          - key: ca.crt\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a38b38e1f9e04fdf/tools/006-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a38b38e1f9e04fdf/tools/006-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a38b38e1f9e04fdf/tools/006-evidence-run_bash_command.summary.txt"}],"llm_analysis":"所有证据已采集完毕。现在给出结论。\n\n---\n\n## 📋 证据采集结论\n\n### ✅ 已采集证据（4项）\n\n1. **e1 - Pod Describe（已确认）**：Pod `rc-volume-configmap-missing-key` 状态为 **Pending**，容器处于 `ContainerCreating`。Events 明确指出：\n   - `MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key`\n   - 该 Warning 已出现 **12 次**，持续 9m35s，是根因证据。\n\n2. **e2 - ConfigMap YAML（已确认）**：ConfigMap `rc-volume-key-config` 的 `data` 字段只包含一个 key：\n   ```yaml\n   data:\n     existing-key: present   # ← 只有这个 key\n   ```\n   **缺少 Pod 引用的 `missing-key`**。\n\n3. **e3 - Pod YAML（已确认）**：Pod `spec.volumes[].configMap` 配置如下：\n   ```yaml\n   volumes:\n   - configMap:\n       items:\n       - key: \"missing-key\"      # ← 引用了不存在的 key\n         path: \"missing-key\"\n       name: \"rc-volume-key-config\"\n     name: config-volume\n   ```\n   明确指定了 `items[0].key=missing-key`，且 `ConfigMap` 中 **不存在此 key**。\n\n4. **e4 - Pod Events 完整时间线（已确认）**：\n   - `81s (x12 over 9m35s)` — `configmap references non-existent config key: missing-key`\n   - `5m18s` / `45s (x3 over 7m32s)` — `Unable to attach or mount volumes: timed out waiting for the condition`\n   - 无其他异常状态并发。\n\n### ❌ 冲突/负向证据\n- 无冲突证据。所有对象（Pod、ConfigMap）均正常存在于 `aiops-e2e` 命名空间。\n\n### 🔍 根因判断\n**ConfigMap volume key 引用错误** — Pod volume `config-volume` 通过 `items` 指定引用 key `missing-key`，但 ConfigMap `rc-volume-key-config` 的 data 中仅有 `existing-key`，不存在 `missing-key`。ConfigMap 本身存在且完整，故障点在 **部署模板或配置中的 key 名称拼写错误**（将 `existing-key` 误写为 `missing-key`）。\n\n### 💡 修复建议\n方案一：修改 Pod volume items 中的 key 为正确的 `existing-key`。\n方案二：在 ConfigMap `rc-volume-key-config` 中增加 key `missing-key`。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 9 个，匹配计划 4 个，未规划证据 5 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":9,"matched_tool_count":4,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"检查异常Pod rc-volume-configmap-missing-key的当前状态和Events确认ConfigMap key缺失错误","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","purpose":"确认Pod当前状态和FailedMount事件原文，验证ConfigMap key missing-key不存在","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查ConfigMap rc-volume-key-config的内容，确认缺少Pod引用的key 'missing-key'","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml","purpose":"验证ConfigMap的data字段是否包含Pod volume引用的key: missing-key","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"检查Pod的volume配置spec，确认volumes引用ConfigMap和items配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","purpose":"查看Pod spec.volumes中ConfigMap volume的items配置，确认引用的key名称","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"查看命名空间事件过滤到该Pod，确认FailedMount事件时间线","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-configmap-missing-key --sort-by='.lastTimestamp'","purpose":"获取Pod相关事件的完整时间线，确认FailedMount持续状态","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 检查异常Pod rc-volume-configmap-missing-key的当前状态和... | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_yaml | 检查ConfigMap rc-volume-key-config的内容，确认缺少Pod引用... | `kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_get_yaml | 检查Pod的volume配置spec，确认volumes引用ConfigMap和items配置 | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml` |
   | e4 | important | ✅ | kubectl_events | 查看命名空间事件过滤到该Pod，确认FailedMount事件时间线 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volum...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (18.0s)
   📤 → 下游数据: root_cause=Pod rc-volume-configmap-missing-key（aiops-e2e 命名空间）状态为 Pending/ContainerCreating，标签 pod_abnormal_type=VolumeMountFailed。根因诊断如下：Pod spec.volumes[].configMap 配置了 items[0].key=missing-key 引用 ConfigMap rc-volume-key-config，但该 ConfigMap 的 data 仅包含 existing-key: present，不存在 missing-key。kubelet Events 明确报错 "configmap references non-existent config key: missing-key"（x12 次，持续 9m35s），导致卷挂载失败并超时。集群其余 59 个 Pod 均正常 Running，异常范围仅此 1 个 Pod。根因为部署模板/配置中 volume items key 名称拼写错误（将 existing-key 误写为 missing-key）。
   confidence=98%
   causal_chain={"root_cause": "Pod 部署模板中 volume items 配置的 key 名称 'missing-key' 与 ConfigMap rc-volume-key-config 中的实际 key 'existing-key' 不匹配（拼写/配置错误）", "propagation": "Pod 调度到 node1 后，kubelet 尝试挂载 volume config-volume → 检查 ConfigMap rc-volume-key-config 的 data → 未找到 items 指定的 key 'missing-key' → 挂载失败 → 持续重试 12 次", "direct_cause": "Pod volume config-volume 的 items 配置引用 key 'missing-key'，但 ConfigMap rc-volume-key-config 的 data 中仅有 'existing-key'，不存在 'missing-key'", "manifestation": "Pod rc-volume-configmap-missing-key 处于 Pending/ContainerCreating 状态，0/1 Ready，Events 持续报 FailedMount: configmap references non-existent config key: missing-key"}
   rca_analysis={"phenomenon": "集群 aiops-e2e 命名空间中 Pod rc-volume-configmap-missing-key 状态为 Pending/ContainerCreating，标签 pod_abnormal_type=VolumeMountFailed，无法进入 Running 状态。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod rc-volume-configmap-missing-key 状态 Pending，Events 显示 MountVolume.SetUp failed: configmap references non-existent config key: missing-key（x12 over 9m35s）", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml (ConfigMap)", "content": "ConfigMap rc-volume-key-config 的 data 中仅有 existing-key: present，不存在 missing-key", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_yaml (Pod)", "content": "Pod volume config-volume 的 items[0].key=missing-key，引用了一个 ConfigMap 中不存在的 key", "reliability": "高"}, {"id": "e4", "source": "kubectl_events", "content": "事件时间线：81s (x12) FailedMount configmap key 缺失；5m18s/45s FailedMount 卷挂载超时", "reliability": "高"}, {"id": "e5", "source": "kubectl_get_by_kind_in_cluster", "content": "集群共 65 个 Pod，仅此 1 个异常（ContainerCreating），其余 59 个 Running", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedMount 81s (x12 over 9m35s) kubelet MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key", "interpretation": "kubelet 明确报告 volume config-volume 挂载失败，原因是 ConfigMap 引用了不存在的 config key 'missing-key'。此事件已重复 12 次，持续约 9.5 分钟，是持续故障而非瞬态错误。"}, {"evidence_id": "e2", "raw_data": "data:\n  existing-key: present\nkind: ConfigMap\nname: rc-volume-key-config", "interpretation": "ConfigMap rc-volume-key-config 仅包含一个 key 'existing-key'，值 'present'。Pod 引用的 'missing-key' 在该 ConfigMap 中不存在，确认了 key 缺失的事实。"}, {"evidence_id": "e3", "raw_data": "volumes:\n- configMap:\n    items:\n    - key: \"missing-key\"\n      path: \"missing-key\"\n    name: \"rc-volume-key-config\"\n  name: config-volume", "interpretation": "Pod 的 volume spec 明确通过 items 配置指定了 key='missing-key' 映射到 path='missing-key'。这是 Pod 声明的需求端证据，与 ConfigMap 实际内容不匹配构成根因。"}, {"evidence_id": "e4", "raw_data": "81s (x12) FailedMount configmap references non-existent config key; 5m18s FailedMount timed out waiting for the condition", "interpretation": "事件时间线显示：先有 key 缺失错误（根因），随后出现卷挂载超时（次级效应）。无其他异常事件并发，排除多问题干扰。"}, {"evidence_id": "e5", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59}", "interpretation": "集群整体健康，仅此一个异常 Pod。异常被隔离在单一 Pod 上，不影响其他工作负载。根因范围局限在该 Pod 的 volume 配置与 ConfigMap 不匹配上。"}], "causal_chain": {"root_cause": "Pod 部署模板中 volume items 配置的 key 名称 'missing-key' 与 ConfigMap rc-volume-key-config 中的实际 key 'existing-key' 不匹配（拼写/配置错误）", "propagation": "Pod 调度到 node1 后，kubelet 尝试挂载 volume config-volume → 检查 ConfigMap rc-volume-key-config 的 data → 未找到 items 指定的 key 'missing-key' → 挂载失败 → 持续重试 12 次", "direct_cause": "Pod volume config-volume 的 items 配置引用 key 'missing-key'，但 ConfigMap rc-volume-key-config 的 data 中仅有 'existing-key'，不存在 'missing-key'", "manifestation": "Pod rc-volume-configmap-missing-key 处于 Pending/ContainerCreating 状态，0/1 Ready，Events 持续报 FailedMount: configmap references non-existent config key: missing-key"}, "root_cause": "Pod rc-volume-configmap-missing-key（aiops-e2e 命名空间）状态为 Pending/ContainerCreating，标签 pod_abnormal_type=VolumeMountFailed。根因诊断如下：Pod spec.volumes[].configMap 配置了 items[0].key=missing-key 引用 ConfigMap rc-volume-key-config，但该 ConfigMap 的 data 仅包含 existing-key: present，不存在 missing-key。kubelet Events 明确报错 \"configmap references non-existent config key: missing-key\"（x12 次，持续 9m35s），导致卷挂载失败并超时。集群其余 59 个 Pod 均正常 Running，异常范围仅此 1 个 Pod。根因为部署模板/配置中 volume items key 名称拼写错误（将 existing-key 误写为 missing-key）。", "root_cause_summary": "Pod rc-volume-configmap-missing-key（aiops-e2e 命名空间）状态为 Pending/ContainerCreating，标签 pod_abnormal_type=VolumeMountFailed。根因诊断如下：Pod spec.volumes[].configMap 配置了 items[0].key=missing-key 引用 ConfigMap rc-volume-key-config，但该 ConfigMap 的 data 仅包含 existing-key: present，不存在 missing-key。kubelet Events 明确报错 \"configmap references non-existent config key: missing-key\"（x12 次，持续 9m35s），导致卷挂载失败并超时。集群其余 59 个 Pod 均正常 Running，异常范围仅此 1 个 Pod。根因为部署模板/配置中 volume items key 名称拼写错误（将 existing-key 误写为 missing-key）。", "confidence": 0.98, "confidence_reason": "有直接证据链：Pod describe 事件原文明确报错 -> ConfigMap YAML 确认 key 不存在 -> Pod YAML 确认 items 引用错误 key。三条证据相互印证，因果链完整闭合，置信度极高。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [{"cause": "ConfigMap 内容变更滞后（原本有 missing-key 后被删除）", "probability": "low", "reason": "ConfigMap 的 last-applied-configuration 显示创建时只有 existing-key，从未包含 missing-key；无证据表明 key 被删除"}, {"cause": "ConfigMap 名称拼写错误", "probability": "low", "reason": "ConfigMap 名称 rc-volume-key-config 与 Pod volume 引用的名称一致，名称匹配无误"}, {"cause": "镜像拉取问题导致 ContainerCreating", "probability": "low", "reason": "Pod 使用 imagePullPolicy=Never 且镜像 busybox:1.36 存在；Events 无 ImagePullBackOff 或 ErrImagePull 错误"}], "limitations": "未采集 ConfigMap 的完整 YAML data 字段（仅摘要显示 existing-key: present），但多个独立工具（kubectl_get_by_name 显示 DATA=1、run_bash_command 显示 data.existing-key=present）交叉验证确认只有 1 个 key，证据充分。", "llm_raw_analysis": "## 证据清点\\n共采集 7 项证据（e1-e4 核心证据 + 3 项上游已验证结果）\\n\\n## 逐条分析\\n- e1 (kubectl_describe): Pod 状态 Pending 且 Events 明确报告 'configmap references non-existent config key: missing-key'，这是最直接的故障现象证据\\n- e2 (ConfigMap YAML): ConfigMap data 仅有 existing-key，确认 missing-key 不存在\\n- e3 (Pod YAML): Pod volume items[0].key=missing-key，确认错误来源\\n- e4 (kubectl_events): 事件重复 12 次持续 9m35s，排除瞬态故障\\n- e5 (kubectl_get_by_kind): 集群仅此 1 个异常 Pod，问题范围明确\\n\\n## 因果链\\n根因（配置错误：items key 名称不匹配）→ 直接原因（kubelet 挂载时找不到 missing-key）→ 现象（Pod Cont\n... 截断，原始 618 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-volume-configmap-missing-key（aiops-e2e 命名空间）状态为 Pending/ContainerCreating，标签 pod_abnormal_type=VolumeMountFailed。根因诊断如下：Pod spec.volumes[].conf...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod 部署模板中 volume items 配置的 key 名称 'missing-key' 与 ConfigMap rc-volume-key-config 中的实际 key 'existing-key' 不匹配（拼写/配置错误）
     传导机制: Pod 调度到 node1 后，kubelet 尝试挂载 volume config-volume → 检查 ConfigMap rc-volume-key-config 的 data → 未找到 items 指定的 key 'missing-key' → 挂载失败 → 持续重试 12 次
     最终表现: Pod rc-volume-configmap-missing-key 处于 Pending/ContainerCreating 状态，0/1 Ready，Events 持续报 FailedMount: configmap references non-existent config key: missing-key


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (16.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5666 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 4.0s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将根据您提供的三阶段分析结果，为您生成一份详尽、完整的问题诊断报告。

---

## 📊 诊断概览

您好，根据对集群的全面检测，集群中 **59 个 Pod 运行正常**，但发现 **1 个异常 Pod**。以下是问题核心总结：

| 项目 | 内容 |
|------|------|
| **集群总览** | 共 65 个 Pod，其中 59 个 Running，1 个异常 |
| **Pod异常状态** | Pending / ContainerCreating |
| **兼容归因层** | L0 - 存储卷异常 (storage_volume) |
| **问题分类** | **VolumeMountFailed** - ConfigMap 卷挂载失败 |
| **置信度** | **高 (98%)** |
| **证据完整度** | 4/4 (100%) |

**一句话结论**：Pod `rc-volume-configmap-missing-key` 因为引用的 ConfigMap key (`missing-key`) 不存在而无法启动，这是一个明确的**配置错误**问题。

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 异常 Pod | `rc-volume-configmap-missing-key` |
| Namespace | `aiops-e2e` |
| 所在 Node | `node1` (IP: `10.2.0.49`) |
| 错误信息 | `MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 & 事件 | `kubectl describe pod` | 状态: `Pending`；**核心事件**: `Warning FailedMount`(x12), 错误原文: `configmap references non-existent config key: missing-key` | kubelet 明确报告 **ConfigMap Key 缺失** 导致挂载失败 |
| 2 | ConfigMap 内容 | `kubectl get configmap -o yaml` & `run_bash_command` | ConfigMap `rc-volume-key-config` 的 data 仅包含 `existing-key: present` | 确认 ConfigMap **没有** Pod 引用的 `missing-key` |
| 3 | Pod 配置 | `kubectl get pod -o yaml` | Pod volumes 配置中 `items[0].key=missing-key` | Pod 配置明确引用了 **不存在的 key** `missing-key` |
| 4 | 集群概况 | `kubectl get pods -A` | 共 65 个 Pod，其中 59 个 Running，仅此 1 个异常 | 问题**范围唯一**，非整体集群故障 |

### 证据关联分析
- **证据 #1 + #2 + #3 形成完整闭环**：
  - Pod 配置（证据 #3）引用了 `missing-key`。
  - ConfigMap 数据（证据 #2）只包含 `existing-key`。
  - kubelet 尝试挂载时发现不匹配，直接报错（证据 #1）。

### 缺失证据
本次诊断证据链完整（100%），**无缺失证据**。

---

## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                            │
│ Pod 部署模板/配置文件中的 volume items key 名称存在拼写错误：                           │
│ 配置为 'missing-key'，但 ConfigMap 中实际 key 为 'existing-key'                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                          ↓
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                            │
│ Pod 调度到 node1 → kubelet 开始挂载 volume "config-volume"                           │
│ → 解析 ConfigMap rc-volume-key-config 的 data                                       │
│ → 无法找到 items 指定的 key 'missing-key'                                          │
│ → 挂载失败，持续重试（x12 次）                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                          ↓
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                            │
│ kubelet 报告错误: MountVolume.SetUp failed: configmap references non-existent       │
│ config key: missing-key                                                             │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                          ↓
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                        │
│ Pod rc-volume-configmap-missing-key 处于 Pending/ContainerCreating 状态              │
│ 0/1 Ready，Events 持续报 FailedMount 错误                                           │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (kubelet 明确报错)、证据 #2 (ConfigMap 内容验证) 和证据 #3 (Pod 配置验证)，问题的根本原因是 **Pod 部署配置中 volume items 的 key 名称拼写错误**。

**错误配置**：`items[0].key=missing-key`
**正确值**：`existing-key`

**置信度**：高 (98%)
- ✅ 错误消息精确到 key 名称
- ✅ 多个独立工具交叉验证，证据链完整
- ✅ 问题范围唯一，排除了其他集群级故障

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [唯一必要] 更正 ConfigMap volume 挂载配置**

Pod `rc-volume-configmap-missing-key` 通常由 Deployment/StatefulSet 管理。请找到对应的控制器并更新其 volume 配置。

```bash
# 1. 首先找到管理此 Pod 的控制器（假设为 Deployment）
kubectl get deployment -n aiops-e2e | grep rc-volume-configmap-missing-key

# 2. 使用 kubectl edit 修改控制器配置，将 volumes.items[0].key 从 missing-key 改为 existing-key
# 找到类似以下配置并修改:
# volumes:
#   - name: config-volume
#     configMap:
#       name: rc-volume-key-config
#       items:
#         - key: missing-key    # ← 将此行改为 existing-key
#           path: <your_path>
kubectl edit deployment <deployment_name> -n aiops-e2e
```
*依据*：Pod 配置引用错误 key `missing-key`，需要修正为 ConfigMap 中的正确 key `existing-key`。

**2. [验证] 确认 Pod 恢复运行**
```bash
# 查看 Pod 是否重新创建并进入 Running 状态
kubectl get pod -n aiops-e2e -l app=rc-volume-configmap-missing-key -w
```
*预期结果*：旧 Pod 被终止，新 Pod 成功创建，状态变为 `Running`。

### 后续优化
1. **CI/CD 校验**：在部署流水线中增加对 ConfigMap key 的校验，确保引用的 key 真实存在于目标 ConfigMap 中。
2. **配置审计**：使用 `kubectl diff` 或类似工具，在部署前对比实际集群状态与配置文件的差异。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod -n aiops-e2e rc-volume-configmap-missing-key` | STATUS: Running |
| 2. 检查 Pod 事件 | `kubectl describe pod -n aiops-e2e rc-volume-configmap-missing-key` | 无 FailedMount 警告 |
| 3. 确认集群整体 | `kubectl get pods -A | grep -v Running | grep -v Completed` | 所有 Pod 均为 Running 状态 |

---

## ⚠️ 注意事项
- **本次问题影响范围极小**：仅 1 个测试 Pod 受到影响，集群业务正常运行。
- **根因明确，操作简单**：修复只需修改配置文件中的一个 key 名称，无需重启集群或 Node。
- **如果此 Pod 由 Helm Chart 或 GitOps 管理**：应直接修改代码仓库中的模板文件，而非手动 `kubectl edit`，以避免下次部署时覆盖修复。

---

## 📊 性能统计

├─ 总耗时: 1.1m
├─ 问题定位: 13.1s (20%) ✅
├─ 证据链采集: 16.5s (26%) ✅
├─ 根因分析: 18.0s (28%) ✅
├─ 汇总总结: 16.3s (25%) ✅
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
