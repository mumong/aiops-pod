======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 2abe0f5434924105]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，让我先全局扫描所有 Pod，看看当前集群的整体状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59}
NAMESPACE         NAME                                                READY   STATUS              RESTARTS       A
   💭 [问题定位] 发现当前集群有 1 个异常 Pod。让我进一步查看它的详细信息，同时确认其他资源的状态。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                              READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-volume-configmap-missing-key   0/1     ContainerCreating   
   💭 [问题定位] Pod 标签已经标注了 `pod_abnormal_type=VolumeMountFailed`，让我 describe 确认具体原因。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  119s (x17 over 20m)  kubelet            MountVolume
   💭 [问题定位] 情况非常清楚了。现在获取该 ConfigMap 来进一步确认。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                   DATA   AGE   LABELS
rc-volume-key-config   1      20m   rootcause-e2e=true
   💭 [问题定位] 现在让我看一下相关的 runbook 作为参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] 现在我已经掌握了所有必要信息，可以进行分析了。以下是诊断结果：

---

## Pod 异常诊断报告

### 集群概览

扫描发现集群中 **共 65 个 Pod，59 个 Running 正常，1 个异常 Pod**。

---

### 异常 Pod 详情

| 字段 | 值 |
|------|-----|
| **命名空间** | `aiops-e2e` |
| **Pod 名称** | `rc-volume-configmap-missing-key` |
| **状态** | `ContainerCreating`（实际处于 Pending） |
| **READY** | `0/1` |
| **节点** | `node1` |
| **标签** | `pod_abnormal_type=VolumeMountFailed` |

### 根因定位

**Pod 异常类型**: `VolumeMountFailed`（L0 级）

**根本原因**: Pod 挂载了一个名为 `config-volume` 的 ConfigMap 卷，该卷引用的是 ConfigMap **`rc-volume-key-config`**，Pod spec 中指定了 ConfigMap 的 key **`missing-key`**，但该 ConfigMap 中只有 **1 个 data key**，并不包含名为 `missing-key` 的 key。

**关键 Events 证据**:
```
MountVolume.SetUp failed for volume "config-volume" : 
configmap references non-existent config key: missing-key
```

### 分类判断

| 维度 | 值 |
|------|-----|
| **`layer`** | `L0` — VolumeMountFailed |
| **`layer_name`** | 卷挂载失败 - ConfigMap Key 缺失 |
| **`pod_status_keyword`** | `ContainerCreating` |
| **`pod_abnormal_type`** | `VolumeMountFailed` |
| **`status_category`** | `storage_volume` |
| **`confidence`** | 高 |

### 关键实体

- **Pod**: `aiops-e2e/rc-volume-configmap-missing-key`
- **ConfigMap**: `aiops-e2e/rc-volume-key-config` — 仅含 1 个 key，缺失 `missing-key`
- **Volume**: `config-volume`（ConfigMap 类型）
- **节点**: `node1`

### 后续审查方向

1. 确认 ConfigMap `rc-volume-key-config` 应包含哪些 key — 当前仅 1 个 data 条目，但 Pod 引用了 `missing-key`
2. 修改 Pod 的 volume 配置，引用正确的 key 名称，或者向 ConfigMap 补充缺失的 `missing-key` 条目
   ✅ [问题定位] 完成 (16.4s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[{'scenario': 'ConfigMap volume引用了不存在的key', 'probability': '高', 'reason': 'Events明确提示configmap references non-existent config key: missing-key，且ConfigMap仅含1个data key，Pod spec中config-volume引用了rc-volume-key-config，要求key missing-key'}]
   entities=[{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}]
   reasoning=集群中存在1个异常Pod aiops-e2e/rc-volume-configmap-missing-key，状态为ContainerCreating(实际Pending)。Events明确显示MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key。ConfigMap rc-volume-key-config仅含1个data key，缺少Pod引用的missing-key。Pod异常类型为VolumeMountFailed，属于存储卷挂载失败，归入L0层级。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "卷挂载失败 - ConfigMap Key 缺失", "confidence": 0.95, "reasoning": "集群中存在1个异常Pod aiops-e2e/rc-volume-configmap-missing-key，状态为ContainerCreating(实际Pending)。Events明确显示MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key。ConfigMap rc-volume-key-config仅含1个data key，缺少Pod引用的missing-key。Pod异常类型为VolumeMountFailed，属于存储卷挂载失败，归入L0层级。", "abnormal_pods": [{"name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}], "possible_scenarios": [{"scenario": "ConfigMap volume引用了不存在的key", "probability": "高", "reason": "Events明确提示configmap references non-existent config key: missing-key，且ConfigMap仅含1个data key，Pod spec中config-volume引用了rc-volume-key-config，要求key missing-key"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-volume-configmap-missing-key                     0/1     ContainerCreating   0              20m     <none>           node1    <none>           <none>            app=rc-volume-configmap-missing-key,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/2abe0f5434924105/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/2abe0f5434924105/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/2abe0f5434924105/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，按照既有evidence_plan开始执行。先获取Pod的describe信息、YAML和ConfigMap信息，这几个可以并行执行。
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
  Warning  FailedMount  18s (x18 over 20m)   kubelet            MountVolume
   💭 [证据链采集] ConfigMap的data内容没有在摘要中展示，让我通过完整的YAML来查看data字段。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "apiVersion: v1\ndata:\n  existing-key: present\nkind: ConfigMap\nmetadata:\n  annotations:\n    kubectl.kubernetes.io/last-applied-configuration: |\n      {\"apiVersion\":
   💭 [证据链采集] 现在再执行ev-04（查看Pod日志，预期为空负向证据）。
   💭 [证据链采集] 调用工具: kubectl_logs
   💭 [证据链采集] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 输出摘要: raw_chars=221 lines=3
Command failed (exit 1):
kubectl logs rc-volume-configmap-missing-key -n aiops-e2e --tail=50
Error from server (BadRequest): container "app" in pod "rc-volume-
   💭 [证据链采集] 很好，所有证据已采集完毕。以下是证据结论：

---

## 证据采集报告

### ✅ 已采集证据

| 计划项 | 证据内容 | 结论 |
|--------|---------|------|
| **ev-01** (critical) `kubectl describe pod` | Events 原文：`MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key`，已重复 18 次 | ✅ **根因证据确认** — ConfigMap volume 引用了不存在的 key |
| **ev-02** (critical) `kubectl_get_yaml pod` | Pod `.spec.volumes[0].configMap.name=rc-volume-key-config`，volume 类型为 ConfigMap，非 PVC/NFS/hostPath | ✅ volume 引用确认 — 确实为 ConfigMap 类型卷，非 Optional |
| **ev-03** (critical) `kubectl_get_yaml configmap` | ConfigMap `rc-volume-key-config` 的 data 字段只有 **`existing-key: present`**，**没有 `missing-key`** | ✅ **根因确认** — ConfigMap 中不存在 Pod 所需的 `missing-key` |
| **ev-04** (important) `kubectl logs` | 容器未启动，返回 `waiting to start: ContainerCreating` | ✅ 负向证据 — 容器因卷挂载失败未启动，无日志 |

### ❌ 冲突/负向证据
- 无冲突证据，所有工具结果与上游 handoff 完全一致。

### 📋 根因总结
**Pod `rc-volume-configmap-missing-key` 卡在 Pending/ContainerCreating**，原因是 volume `config-volume` 引用了 ConfigMap `rc-volume-key-config`，但该 ConfigMap 的 data 中仅包含 `existing-key`，缺少 Pod items 中要求的 `missing-key`。kubelet 持续 20 分钟重试挂载失败，产生了 18 次 `FailedMount` 事件。

**修复建议**：在 ConfigMap `rc-volume-key-config` 中添加 `missing-key` 键值对，或修改 Pod volume 配置使其引用正确的 key 名称。
   ✅ [证据链采集] 完成 (16.1s)
   📤 → 下游数据: evidence_items=7/8
   evidence_analysis={"evidence_plan":[{"id":"ev-01","description":"验证异常Pod当前状态 - kubectl describe pod rc-volume-configmap-missing-key","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e","resource":"pod"},"purpose":"确认Pod当前状态、Events中的FailedMount原文和卷挂载失败细节","evidence_type":"pod_status_and_events","target_scope":"Pod/aiops-e2e/rc-volume-configmap-missing-key","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"ev-02","description":"验证Pod YAML中的volume引用 - ConfigMap volume spec","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e","resource":"pod","format":"yaml"},"purpose":"查看.spec.volumes确认volume类型为ConfigMap，以及引用的ConfigMap名称和items中的key","evidence_type":"pod_spec_volumes","target_scope":"Pod/aiops-e2e/rc-volume-configmap-missing-key","acceptable_tools":["kubectl_get_yaml","kubectl_get_by_name","run_bash_command"],"counts_for_completeness":true},{"id":"ev-03","description":"验证ConfigMap内容 - 确认missing-key确实不存在","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml","tool_args":{"kind":"configmap","name":"rc-volume-key-config","namespace":"aiops-e2e","format":"yaml"},"purpose":"检查ConfigMap的data字段，确认是否包含Pod引用的missing-key","evidence_type":"configmap_data","target_scope":"ConfigMap/aiops-e2e/rc-volume-key-config","acceptable_tools":["kubectl_get_by_name","kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"ev-04","description":"验证Pod logs - 检查容器是否有启动日志","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-volume-configmap-missing-key -n aiops-e2e","tool_args":{"resource":"pod","name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e"},"purpose":"容器由于卷挂载失败尚未启动，确认logs是否为空（负向证据）","evidence_type":"container_logs","target_scope":"Pod/aiops-e2e/rc-volume-configmap-missing-key","acceptable_tools":["kubectl_logs","kubectl_container_logs"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: ConfigMap\nname: rc-volume-key-config\nnamespace: aiops-e2e","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2abe0f5434924105/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2abe0f5434924105/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2abe0f5434924105/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T04:29:04Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-configmap-missing-key, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"config-volume\", \"configMap\": \"rc-volume-key-config\"}\n- {\"name\": \"kube-api-access-fbhds\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2abe0f5434924105/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2abe0f5434924105/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2abe0f5434924105/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  18s (x18 over 20m)   kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n  Warning  FailedMount  7m24s (x3 over 16m)  kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-fbhds config-volume]: timed out waiting for the condition\n  Warning  FailedMount  33s (x6 over 18m)    kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  config-volume:\n    Type:      ConfigMap (a volume populated by a ConfigMap)\n    Name:      rc-volume-key-config\n    Optional:  false\n  kube-api-access-fbhds:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedMount  7m24s (x3 over 16m)  kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-fbhds config-volume]: timed out waiting for the condition\n  Warning  FailedMount  33s (x6 over 18m)    kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition\n  Warning  FailedMount  18s (x18 over 20m)   kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2abe0f5434924105/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2abe0f5434924105/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2abe0f5434924105/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"apiVersion: v1\\ndata:\\n  existing-key: present\\nkind: ConfigMap\\nmetadata:\\n  annotations:\\n    kubectl.kubernetes.io/last-applied-configuration: |\\n      {\\\"apiVersion\\\":\\\"v1\\\",\\\"data\\\":{\\\"existing-key\\\":\\\"present\\\"},\\\"kind\\\":\\\"ConfigMap\\\",\\\"metadata\\\":{\\\"annotations\\\":{},\\\"labels\\\":{\\\"rootcause-e2e\\\":\\\"true\\\"},\\\"name\\\":\\\"rc-volume-key-config\\\",\\\"namespace\\\":\\\"aiops-e2e\\\"}}\\n  creationTimestamp: \\\"2026-05-21T04:29:04Z\\\"\\n  labels:\\n    rootcause-e2e: \\\"true\\\"\\n  name: rc-volume-key-config\\n  namespace: aiops-e2e\\n  resourceVersion: \\\"52517160\\\"\\n  uid: 5468219a-cec8-424b-b490-66fd39c82b58\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/2abe0f5434924105/tools/004-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2abe0f5434924105/tools/004-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2abe0f5434924105/tools/004-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 输出摘要: raw_chars=221 lines=3\nCommand failed (exit 1):\nkubectl logs rc-volume-configmap-missing-key -n aiops-e2e --tail=50\nError from server (BadRequest): container \"app\" in pod \"rc-volume-configmap-missing-key\" is waiting to start: ContainerCreating","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/2abe0f5434924105/tools/005-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/2abe0f5434924105/tools/005-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/2abe0f5434924105/tools/005-evidence-kubectl_logs.summary.txt"}],"llm_analysis":"很好，所有证据已采集完毕。以下是证据结论：\n\n---\n\n## 证据采集报告\n\n### ✅ 已采集证据\n\n| 计划项 | 证据内容 | 结论 |\n|--------|---------|------|\n| **ev-01** (critical) `kubectl describe pod` | Events 原文：`MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key`，已重复 18 次 | ✅ **根因证据确认** — ConfigMap volume 引用了不存在的 key |\n| **ev-02** (critical) `kubectl_get_yaml pod` | Pod `.spec.volumes[0].configMap.name=rc-volume-key-config`，volume 类型为 ConfigMap，非 PVC/NFS/hostPath | ✅ volume 引用确认 — 确实为 ConfigMap 类型卷，非 Optional |\n| **ev-03** (critical) `kubectl_get_yaml configmap` | ConfigMap `rc-volume-key-config` 的 data 字段只有 **`existing-key: present`**，**没有 `missing-key`** | ✅ **根因确认** — ConfigMap 中不存在 Pod 所需的 `missing-key` |\n| **ev-04** (important) `kubectl logs` | 容器未启动，返回 `waiting to start: ContainerCreating` | ✅ 负向证据 — 容器因卷挂载失败未启动，无日志 |\n\n### ❌ 冲突/负向证据\n- 无冲突证据，所有工具结果与上游 handoff 完全一致。\n\n### 📋 根因总结\n**Pod `rc-volume-configmap-missing-key` 卡在 Pending/ContainerCreating**，原因是 volume `config-volume` 引用了 ConfigMap `rc-volume-key-config`，但该 ConfigMap 的 data 中仅包含 `existing-key`，缺少 Pod items 中要求的 `missing-key`。kubelet 持续 20 分钟重试挂载失败，产生了 18 次 `FailedMount` 事件。\n\n**修复建议**：在 ConfigMap `rc-volume-key-config` 中添加 `missing-key` 键值对，或修改 Pod volume 配置使其引用正确的 key 名称。","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 7/8 项，完整度 88%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":8,"environment_evidence_collected":7,"environment_evidence_completeness":0.875,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"ev-01","description":"验证异常Pod当前状态 - kubectl describe pod rc-volume-configmap-missing-key","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","purpose":"确认Pod当前状态、Events中的FailedMount原文和卷挂载失败细节","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-02","description":"验证Pod YAML中的volume引用 - ConfigMap volume spec","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","purpose":"查看.spec.volumes确认volume类型为ConfigMap，以及引用的ConfigMap名称和items中的key","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-03","description":"验证ConfigMap内容 - 确认missing-key确实不存在","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml","purpose":"检查ConfigMap的data字段，确认是否包含Pod引用的missing-key","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-04","description":"验证Pod logs - 检查容器是否有启动日志","level":"important","tool":"kubectl_logs","command":"kubectl logs rc-volume-configmap-missing-key -n aiops-e2e","purpose":"容器由于卷挂载失败尚未启动，确认logs是否为空（负向证据）","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["ev-04(验证Pod logs - 检查容器是否有启动日志): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 88%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | ev-01 | critical | ✅ | kubectl_describe | 验证异常Pod当前状态 - kubectl describe pod rc-volume-... | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` |
   | ev-02 | critical | ✅ | kubectl_get_yaml | 验证Pod YAML中的volume引用 - ConfigMap volume spec | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml` |
   | ev-03 | critical | ✅ | kubectl_get_yaml | 验证ConfigMap内容 - 确认missing-key确实不存在 | `kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml` |
   | ev-04 | important | ❌ | kubectl_logs | 验证Pod logs - 检查容器是否有启动日志 | `kubectl logs rc-volume-configmap-missing-key -n aiops-e2e` |

   ⚠️ 未采集原因:
   - ev-04(验证Pod logs - 检查容器是否有启动日志): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (16.5s)
   📤 → 下游数据: root_cause=Pod rc-volume-configmap-missing-key（aiops-e2e）卡在 ContainerCreating/Pending 状态 20 分钟，根因为其 volume config-volume 引用了 ConfigMap rc-volume-key-config 中的 key missing-key，但该 ConfigMap 的 data 仅包含 existing-key（唯一 key），缺少 missing-key。kubelet 已产生 18 次 FailedMount 事件明确报告 "configmap references non-existent config key: missing-key"。集群其余 59 个 Pod 均正常运行，问题仅限该 Pod 的 ConfigMap key 引用配置错误。
   confidence=98%
   causal_chain={"root_cause": "ConfigMap rc-volume-key-config 的 data 中缺少 Pod volume items 所需的 key missing-key，导致 kubelet 挂载 config-volume 时反复失败", "propagation": "Pod spec 中 config-volume（非 Optional）引用 ConfigMap rc-volume-key-config，要求 key missing-key → kubelet 尝试挂载时发现 ConfigMap 中不存在该 key → MountVolume.SetUp 失败 → Pod 持续处于 Pending/ContainerCreating 状态 → 超时后产生 timed out waiting for the condition 事件", "direct_cause": "kubelet 无法完成 ConfigMap volume config-volume 的挂载，因为 ConfigMap 中缺少 Pod 引用的 data key: missing-key", "manifestation": "Pod rc-volume-configmap-missing-key 状态为 ContainerCreating（phase: Pending），Ready 0/1，Events 中持续出现 FailedMount 错误"}
   rca_analysis={"phenomenon": "Namespace aiops-e2e 中的 Pod rc-volume-configmap-missing-key 状态为 ContainerCreating（实际 phase 为 Pending），持续约 20 分钟，Ready 为 0/1，kubelet 反复产生 FailedMount 事件。", "evidence_inventory": [{"id": "ev-01", "source": "kubectl_describe", "content": "Events 原文: MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key，重复 18 次", "reliability": "高"}, {"id": "ev-02", "source": "kubectl_get_yaml (Pod)", "content": "Pod spec volumes[0] 为 ConfigMap 类型，名称 rc-volume-key-config，非 Optional", "reliability": "高"}, {"id": "ev-03", "source": "kubectl_get_yaml / run_bash_command (ConfigMap)", "content": "ConfigMap rc-volume-key-config data 字段仅含 existing-key: present，无 missing-key", "reliability": "高"}, {"id": "ev-04", "source": "kubectl_logs", "content": "容器未启动，返回 container is waiting to start: ContainerCreating", "reliability": "高（负向证据）"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "65 个 Pod 中仅 1 个异常 (ContainerCreating)，59 个 Running", "reliability": "高"}, {"id": "layer_4", "source": "kubectl_get_by_name (ConfigMap)", "content": "ConfigMap rc-volume-key-config DATA=1，仅含 1 个 data key", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "ev-01", "raw_data": "Warning FailedMount 18s (x18 over 20m) kubelet MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key", "interpretation": "kubelet 明确报错：ConfigMap volume 引用了不存在的 key missing-key，已重试 18 次持续 20 分钟，这是最直接的根因线索"}, {"evidence_id": "ev-02", "raw_data": "volumes: [{\"name\":\"config-volume\",\"configMap\":\"rc-volume-key-config\"}]", "interpretation": "Pod 的 config-volume 确实引用 ConfigMap rc-volume-key-config，且非 Optional，意味着该 key 必须存在才能挂载成功"}, {"evidence_id": "ev-03", "raw_data": "data:\n  existing-key: present", "interpretation": "ConfigMap rc-volume-key-config 的 data 中只有 existing-key，完全不存在 missing-key，与 ev-01 错误完全对应，构成根因必备条件"}, {"evidence_id": "ev-04", "raw_data": "container \"app\" in pod ... is waiting to start: ContainerCreating", "interpretation": "容器未启动，无法获取日志，这是 Pod 卡在 ContainerCreating 的后果而非原因——符合预期负向证据"}, {"evidence_id": "layer_1", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59}", "interpretation": "集群其他 Pod 运行正常，异常仅局限于该 Pod，排除了集群级或节点级问题"}], "causal_chain": {"root_cause": "ConfigMap rc-volume-key-config 的 data 中缺少 Pod volume items 所需的 key missing-key，导致 kubelet 挂载 config-volume 时反复失败", "propagation": "Pod spec 中 config-volume（非 Optional）引用 ConfigMap rc-volume-key-config，要求 key missing-key → kubelet 尝试挂载时发现 ConfigMap 中不存在该 key → MountVolume.SetUp 失败 → Pod 持续处于 Pending/ContainerCreating 状态 → 超时后产生 timed out waiting for the condition 事件", "direct_cause": "kubelet 无法完成 ConfigMap volume config-volume 的挂载，因为 ConfigMap 中缺少 Pod 引用的 data key: missing-key", "manifestation": "Pod rc-volume-configmap-missing-key 状态为 ContainerCreating（phase: Pending），Ready 0/1，Events 中持续出现 FailedMount 错误"}, "root_cause": "Pod rc-volume-configmap-missing-key（aiops-e2e）卡在 ContainerCreating/Pending 状态 20 分钟，根因为其 volume config-volume 引用了 ConfigMap rc-volume-key-config 中的 key missing-key，但该 ConfigMap 的 data 仅包含 existing-key（唯一 key），缺少 missing-key。kubelet 已产生 18 次 FailedMount 事件明确报告 \"configmap references non-existent config key: missing-key\"。集群其余 59 个 Pod 均正常运行，问题仅限该 Pod 的 ConfigMap key 引用配置错误。", "root_cause_summary": "Pod rc-volume-configmap-missing-key（aiops-e2e）卡在 ContainerCreating/Pending 状态 20 分钟，根因为其 volume config-volume 引用了 ConfigMap rc-volume-key-config 中的 key missing-key，但该 ConfigMap 的 data 仅包含 existing-key（唯一 key），缺少 missing-key。kubelet 已产生 18 次 FailedMount 事件明确报告 \"configmap references non-existent config key: missing-key\"。集群其余 59 个 Pod 均正常运行，问题仅限该 Pod 的 ConfigMap key 引用配置错误。", "confidence": 0.98, "confidence_reason": "有直接证据链：Events 原文（ev-01）明确报错 → Pod volume spec（ev-02）确认引用 → ConfigMap data（ev-03）确证 key 缺失，三步证据环环相扣无矛盾；负向证据（ev-04）和集群健康度（layer_1）均排除其他干扰因素。置信度 0.98。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [{"cause": "ConfigMap 不存在或被删除", "probability": "low", "reason": "ConfigMap rc-volume-key-config 确实存在（DATA=1），排除此可能"}, {"cause": "节点 node1 异常导致卷挂载失败", "probability": "low", "reason": "集群中其他 59 个 Pod 在 node1 及其他节点正常运行，排除节点级问题"}, {"cause": "镜像拉取失败", "probability": "low", "reason": "Pod 的 imagePullPolicy=Never 且 Events 中无 ImagePullBackOff/ErrImagePull 事件，kubelet 唯一报错为 FailedMount"}], "limitations": "ConfigMap 的完整 YAML data 字段已确认仅含 existing-key，但未检查 Pod spec 中是否有 items 字段精确指定要引用的 key 名称——不过 Events 原文已明确指向 missing-key，因此此限制不影响结论。另外 imagePullPolicy=Never 可能是一个次要配置问题（若镜像不存在则后续会失败），但目前容器尚未启动到镜像拉取阶段，暂无法验证。", "llm_raw_analysis": "## 证据清点\\n共采集 8 条证据（含 1 条负向证据）:\\n1. ev-01: kubectl_describe Events — FailedMount 报错 configmap references non-existent config key: missing-key (x18)\\n2. ev-02: Pod YAML volume spec — config-volume 引用 ConfigMap rc-volume-key-config\\n3. ev-03: ConfigMap YAML data — 仅含 existing-key，无 missing-key\\n4. ev-04: kubectl_logs — 容器未启动 (ContainerCreating)\\n5. layer_1: 集群 Pod 概览 — 65 个 Pod 中 59 Running，仅该 Pod 异常\\n6. layer_2: Pod 详情 — 同 layer_1 一致\\n7. layer_3: kubectl_describe 完整摘要\\n8. layer_4: ConfigMap 基本信息 —\n... 截断，原始 918 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-volume-configmap-missing-key（aiops-e2e）卡在 ContainerCreating/Pending 状态 20 分钟，根因为其 volume config-volume 引用了 ConfigMap rc-volume-key-config 中的 ke...
   置信度: 98%
   🔗 因果链:
     根本原因: ConfigMap rc-volume-key-config 的 data 中缺少 Pod volume items 所需的 key missing-key，导致 kubelet 挂载 config-volume 时反复失败
     传导机制: Pod spec 中 config-volume（非 Optional）引用 ConfigMap rc-volume-key-config，要求 key missing-key → kubelet 尝试挂载时发现 ConfigMap 中不存在该 key → MountVolume.SetUp 失败 → Pod 持续处于 Pending/ContainerCreating 状态 → 超时后产生 timed out waiting for the condition 事件
     最终表现: Pod rc-volume-configmap-missing-key 状态为 ContainerCreating（phase: Pending），Ready 0/1，Events 中持续出现 FailedMount 错误


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (15.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6074 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 4.5s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将为您分析集群状态。

---
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **集群整体状态** | 集群中 65 个 Pod 中，59 个正常运行，**1 个异常**。 |
| **Pod异常状态** | `ContainerCreating` (实际 `Pending`) |
| **兼容归因层** | L0 |
| **问题分类** | `VolumeMountFailed` (存储卷挂载失败 - ConfigMap Key 缺失) |
| **置信度** | 高 (98%) |
| **证据完整度** | 3/4 (75%) |

---

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**核心问题总结**：
您的集群整体健康，59 个 Pod 正常运行。但存在 **1 个 Pod** 由于配置错误导致无法启动。

**关键实体**：
| 类型 | 值 |
|------|-----|
| **异常 Pod** | `rc-volume-configmap-missing-key` |
| **命名空间** | `aiops-e2e` |
| **所在节点** | `node1` |
| **错误信息** | `MountVolume.SetUp failed for volume “config-volume” : configmap references non-existent config key: missing-key` |
| **依赖的 ConfigMap** | `rc-volume-key-config` |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态与事件 | `kubectl describe pod rc-volume-configmap-missing-key` | `Reason: ContainerCreating`<br>`Warning FailedMount 18s (x18 over 20m) kubelet ... configmap references non-existent config key: missing-key` | Pod 无法启动，根因是卷挂载失败，因为 ConfigMap 引用了不存在的 key。 |
| 2 | Pod YAML 配置 | `kubectl get pod rc-volume-configmap-missing-key -o yaml` | `phase: Pending`<br>`finalizers: <none>`<br>`terminationGracePeriodSeconds: 30` | Pod 处于 `Pending` 状态，`finalizers` 为空，排除了 finalizer 未清理的问题。 |
| 3 | ConfigMap 内容 | `kubectl get configmap rc-volume-key-config -o yaml` | ```yaml<br>apiVersion: v1<br>data:<br>  existing-key: present<br>kind: ConfigMap<br>metadata:<br>...``` | ConfigMap **只包含一个名为 `existing-key` 的 key**，**不存在 Pod 所依赖的 `missing-key`**。 |
| 4 | 集群整体状态 | `kubectl get pods -A` | `rows=65 abnormal=1 status_counts={'Running': 59}` | 集群中只有这一个异常 Pod，其余均正常运行。 |

### 证据关联分析
- **证据 #1 + 证据 #3 印证**：Pod 事件明确指出引用了不存在的 key `missing-key`，而 ConfigMap 的实际内容证实了该 key 确实不存在。这两条证据直接锁定了问题根因。
- **证据链**：ConfigMap `rc-volume-key-config` 缺少 `missing-key` → Pod 尝试挂载 `config-volume` 卷失败 → kubelet 产生 `FailedMount` 事件 → Pod 卡在 `ContainerCreating` / `Pending` 状态。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 容器启动日志 (`kubectl logs`) | Low | Pod 根本未进入运行状态，因此无启动日志。此证据缺失不影响当前根因判断。 |

---

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因 (Root Cause)                                                               │
│ ConfigMap `rc-volume-key-config` 的 data 中，缺少 Pod 引用的 key `missing-key`。     │
│ (ConfigMap 仅包含 `existing-key`，不包含 `missing-key`)                             │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                             │
│ Pod spec 中定义了一个非可选 (non-optional) 的 configmap volume，并要求 key `missing-key`， │
│ 当 kubelet 尝试挂载此卷时，发现 ConfigMap 中不存在该 key。                             │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因 (Direct Cause)                                                              │
│ kubelet 挂载 `config-volume` 失败，错误信息：                                   │
│ `MountVolume.SetUp failed for volume "config-volume" : configmap references         │
│  non-existent config key: missing-key`                                              │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                         │
│ Pod `rc-volume-configmap-missing-key` 持续处于 `ContainerCreating` / `Pending` 状态，  │
│ Ready 0/1，无法提供服务。                                                             │
└─────────────────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #1 (FailedMount 事件) 和证据 #3 (ConfigMap 内容)，问题的根本原因是 **Pod 的 ConfigMap 卷挂载配置引用了 ConfigMap `rc-volume-key-config` 中不存在的 key `missing-key`**。

**置信度**：高 (98%)
- ✅ Pod 事件直接指向 `missing-key` 缺失。
- ✅ ConfigMap 内容确认了该 key 不存在。
- ✅ 集群中其他 59 个 Pod 均正常运行，排除了集群层面的问题。

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [推荐] 修复 ConfigMap，添加缺失的 key**
这是最直接的修复方式。向 ConfigMap 中添加名为 `missing-key` 的数据项。
```bash
# 方法一：使用 kubectl patch 直接添加 key
kubectl patch configmap rc-volume-key-config -n aiops-e2e -p '{"data":{"missing-key":"请填写正确的值"}}'

# 方法二：使用 kubectl edit 手动编辑
kubectl edit configmap rc-volume-key-config -n aiops-e2e
# 在 data 字段下添加一行:   missing-key: "配置值"
```
*依据*：在 ConfigMap 中添加 `missing-key` 后，kubelet 就能成功挂载卷，Pod 会恢复正常。
*注意*：Pod 不会自动重启以读取更新后的 ConfigMap。您需要手动重启 Pod。

2. **重启 Pod 以应用修复**
```bash
# 删除 Pod，让 Deployment 或其他控制器自动重建
kubectl delete pod rc-volume-configmap-missing-key -n aiops-e2e
```
*依据*：ConfigMap 更新后，只有新启动的 Pod 才能读取到新的数据。

**2. [替代方案] 修改 Pod YAML，移除对缺失 key 的引用**
如果您不需要 `missing-key`，可以修改 Pod 定义，移除对它的引用。
```bash
# 找到 Pod 的控制器 (如 Deployment)
kubectl get deployments -n aiops-e2e

# 编辑 Deployment，修改 volume 配置
kubectl edit deployment <deployment-name> -n aiops-e2e
# 在 items 字段中删除对 missing-key 的引用
```

### 后续优化
1. **配置审查**：在创建或修改 Pod / ConfigMap 时，确保引用的 key 名称完全匹配。
2. **环境变量**：如果应用需要读取 `missing-key` 的内容，确认它是在 ConfigMap 中定义，而不是在 Pod spec 中硬编码。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 被重新创建 | `kubectl get pod -n aiops-e2e \| grep rc-volume-configmap-missing-key` | Pod 名称可能存在新的后缀，`STATUS` 应为 `Running` |
| 2. 检查 Pod 状态 | `kubectl describe pod -n aiops-e2e -l app=rc-volume-configmap-missing-key` | 事件中不应再出现 `FailedMount` 错误，Pod 状态为 `Running` |
| 3. 检查集群总体状态 | `kubectl get pods -A \| grep -v Running \| grep -v Completed` | 只应返回正常的 `Running` 或 `Completed` 的 Pod。 |

---

## ⚠️ 注意事项
- 本次问题**仅限于单个 Pod**，集群其余部分稳定运行，无需恐慌。
- `Pod` 的 `finalizers` 为空，已排除由 finalizer 导致的问题；Pod 的 `terminationGracePeriodSeconds` 为 30 秒，排除了该参数导致的卡住问题。
- 修复 ConfigMap 后，**必须**手动删除 Pod 使其重新创建，否则 Pod 仍将处于异常状态。

---

## 📊 性能统计

├─ 总耗时: 1.1m
├─ 问题定位: 16.4s (25%) ✅
├─ 证据链采集: 16.1s (25%) ✅
├─ 根因分析: 16.5s (26%) ✅
├─ 汇总总结: 15.6s (24%) ✅
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
