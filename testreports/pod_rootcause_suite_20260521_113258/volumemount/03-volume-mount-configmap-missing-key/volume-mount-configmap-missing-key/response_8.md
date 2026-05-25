======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 43f0dbc1446447a6]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先来扫描整个集群的 Pod 状态，看看当前有哪些异常。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59}
NAMESPACE         NAME                                                READY   STATUS              RESTARTS       A
   💭 [问题定位] 看到有一个异常 Pod。让我进一步查看它的详细情况。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  100s (x9 over 3m48s)  kubelet            MountVolum
   💭 [问题定位] 现在让我获取参考的 runbook。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] 现在我已经获取了足够的信息，可以进行完整的定位分析了。

---

## 定位分析结果

### 全局 Pod 扫描
集群共 **65 个 Pod**，其中 **59 个 Running**，**1 个异常 Pod**：

| Pod | 命名空间 | 状态 | 就绪 |
|-----|---------|------|------|
| `rc-volume-configmap-missing-key` | `aiops-e2e` | `ContainerCreating` | `0/1` |

### 异常详情

**Pod:** `rc-volume-configmap-missing-key` (命名空间: `aiops-e2e`)

**当前状态关键字:** `ContainerCreating`  
**Pod 异常类型:** `VolumeMountFailed`  
**状态分类:** `storage_volume`

**关键事件证据:**
```
MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key
```

**根因分析:**
该 Pod 的 `config-volume` 卷引用了 ConfigMap `rc-volume-key-config`，但 ConfigMap 中不存在名为 `missing-key` 的键。Pod spec 中 `volume[].configMap` 的 `optional: false`，因此 kubelet 无法挂载该卷，Pod 卡在 `ContainerCreating`。

### 分层定级

| 字段 | 值 |
|------|-----|
| **layer** | L0 |
| **派生层 (derived_layer)** | L0 |
| **兼容层 (layers)** | L0 |
| **层名称 (layer_name)** | 存储/卷挂载失败 |
| **置信度 (confidence)** | 高 |
| **状态关键字 (pod_status_keyword)** | ContainerCreating |
| **异常类型 (pod_abnormal_type)** | VolumeMountFailed |

### 异常 Pod 列表
| Pod | 命名空间 | 当前状态 | 异常类型 |
|-----|---------|---------|---------|
| `rc-volume-configmap-missing-key` | `aiops-e2e` | ContainerCreating | VolumeMountFailed |

### 异常类型分组
| 异常类型 | Pod 列表 |
|---------|---------|
| VolumeMountFailed | `rc-volume-configmap-missing-key` |

### 关键实体
- **Pod:** `rc-volume-configmap-missing-key` @ `aiops-e2e`
- **Volume:** `config-volume` (ConfigMap 类型)
- **ConfigMap:** `rc-volume-key-config` (已存在，但缺少键 `missing-key`)
- **Node:** `node1`

### 可能场景
1. **ConfigMap key 拼写错误** — Pod 引用的 volume 指定了 key `missing-key`，但 ConfigMap `rc-volume-key-config` 中不存在该键，可能是名称拼写错误或遗漏了配置项。
2. **缺少配置项** — ConfigMap 未包含预期的 `missing-key` 条目，需要补充该配置。
   ✅ [问题定位] 完成 (14.4s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[{'scenario': 'ConfigMap key 拼写错误', 'probability': '高', 'reason': "Pod volume 引用了 key 'missing-key'，但 ConfigMap rc-volume-key-config 中不存在该键，可能是名称拼写错误"}, {'scenario': '缺少配置项', 'probability': '中', 'reason': 'ConfigMap 未包含预期的 missing-key 条目，需要补充该配置'}]
   entities=[{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}]
   reasoning=集群中存在1个异常Pod rc-volume-configmap-missing-key（aiops-e2e命名空间），当前状态为ContainerCreating，异常类型为VolumeMountFailed。关键事件证据显示MountVolume.SetUp failed: configmap references non-existent config key: missing-key，即ConfigMap volume引用了不存在的键，导致卷挂载失败。根据五层模型，VolumeMountFailed归入L0（磁盘/存储/驱逐类），且Pod卡在ContainerCreating未恢复，因此定层L0。当前无其他异常Pod或节点问题。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "存储/卷挂载失败", "confidence": 0.95, "reasoning": "集群中存在1个异常Pod rc-volume-configmap-missing-key（aiops-e2e命名空间），当前状态为ContainerCreating，异常类型为VolumeMountFailed。关键事件证据显示MountVolume.SetUp failed: configmap references non-existent config key: missing-key，即ConfigMap volume引用了不存在的键，导致卷挂载失败。根据五层模型，VolumeMountFailed归入L0（磁盘/存储/驱逐类），且Pod卡在ContainerCreating未恢复，因此定层L0。当前无其他异常Pod或节点问题。", "abnormal_pods": [{"name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}], "possible_scenarios": [{"scenario": "ConfigMap key 拼写错误", "probability": "高", "reason": "Pod volume 引用了 key 'missing-key'，但 ConfigMap rc-volume-key-config 中不存在该键，可能是名称拼写错误"}, {"scenario": "缺少配置项", "probability": "中", "reason": "ConfigMap 未包含预期的 missing-key 条目，需要补充该配置"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-volume-configmap-missing-key                     0/1     ContainerCreating   0              3m47s   <none>           node1    <none>           <none>            app=rc-volume-configmap-missing-key,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/43f0dbc1446447a6/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/43f0dbc1446447a6/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/43f0dbc1446447a6/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来执行既有 evidence_plan 中的关键工具调用。先从最高优先级的工具开始。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  119s (x9 over 4m7s)  kubelet            MountVolume
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
creationTimestamp: 2026-05-21T04:29:04Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
final
   💭 [证据链采集] 非常好，Pod 仍然存在，Events 和 volumes 信息已确认。现在检查 ConfigMap 是否真的缺少 missing-key。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-key-config
namespace: aiops-e2e
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
2m1s (x9 over 4m9s)   Warning   FailedMount   Pod/rc-volume-configmap-missing-key   MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent co
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: ConfigMap
name: rc-volume-key-config
namespace: aiops-e2e
   💭 [证据链采集] 让我查看 ConfigMap 的数据内容，确认具体哪些 key 存在：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"existing-key\": \"present\"\n}\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] ## 证据采集结论

### 已采集证据（全部 critical/important 级）

| 证据项 | 结果 |
|--------|------|
| **e1: `kubectl describe pod`** | Pod `rc-volume-configmap-missing-key` 仍存在，状态 **Pending**，容器状态 **Waiting(ContainerCreating)**。Events 明确提示：`MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key` |
| **e2: `kubectl get pod -o yaml`** | `.spec.volumes[]` 中 `config-volume` 类型为 **ConfigMap**，引用名为 `rc-volume-key-config`，`Optional: false`（非可选） |
| **e3: `kubectl describe configmap`** | ConfigMap `rc-volume-key-config` 存在于 `aiops-e2e` 命名空间 |
| **e4: `kubectl get configmap -o yaml`** | ConfigMap `data` 内容为：`{"existing-key": "present"}` — **不存在 `missing-key` 键** |
| **e5: `kubectl events`** | 共 9 次重复 `FailedMount` 事件，最后一次 2 分钟前，原文一致指向 `non-existent config key: missing-key` |

### 根因结论
**Pod `rc-volume-configmap-missing-key` 卡在 ContainerCreating**，因为其 volume `config-volume` 引用 ConfigMap `rc-volume-key-config` 中的键 `missing-key`，但该 ConfigMap **只包含 `existing-key` 一个键**，`missing-key` 不存在。由于 volume 的 `Optional: false`（非可选），kubelet 无法完成挂载，Pod 持续阻塞。

### 未采集证据 / 冲突证据
- **无冲突证据** — 所有工具均返回预期结果，未出现 NotFound 或 namespace 不匹配。
- 当前集群只有这一个异常组（`g1`），不存在其他异常组需要最小验证。
   ✅ [证据链采集] 完成 (14.8s)
   📤 → 下游数据: evidence_items=5/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"Re-verify Pod current status and Events for rc-volume-configmap-missing-key in aiops-e2e","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e","resource":"pod"},"purpose":"Confirm Pod still exists, verify ContainerCreating status and FailedMount events with non-existent config key error","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"Get Pod YAML to verify volume spec references ConfigMap and the specific key","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e","resource":"pod"},"purpose":"Check .spec.volumes[] to confirm configMap volume name and key being referenced","evidence_type":"","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"Verify the ConfigMap rc-volume-key-config exists and check its keys","level":"critical","tool":"kubectl_describe","command":"kubectl describe configmap rc-volume-key-config -n aiops-e2e","tool_args":{"kind":"configmap","name":"rc-volume-key-config","namespace":"aiops-e2e","resource":"configmap"},"purpose":"Confirm ConfigMap exists and verify whether 'missing-key' is present in its data keys","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"Get ConfigMap YAML for full key list verification","level":"important","tool":"kubectl_get_yaml","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml","tool_args":{"kind":"configmap","name":"rc-volume-key-config","namespace":"aiops-e2e","resource":"configmap"},"purpose":"Examine ConfigMap data section to confirm missing-key is indeed absent","evidence_type":"","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e5","description":"Get events sorted by timestamp for the pod to collect all FailedMount occurrences","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-configmap-missing-key --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-volume-configmap-missing-key","sort_by":".lastTimestamp"},"purpose":"Collect all FailedMount events confirming the non-existent config key error pattern","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  119s (x9 over 4m7s)  kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n  Warning  FailedMount  2m4s                 kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  config-volume:\n    Type:      ConfigMap (a volume populated by a ConfigMap)\n    Name:      rc-volume-key-config\n    Optional:  false\n  kube-api-access-fbhds:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedMount  2m4s                 kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition\n  Warning  FailedMount  119s (x9 over 4m7s)  kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/43f0dbc1446447a6/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/43f0dbc1446447a6/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/43f0dbc1446447a6/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T04:29:04Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-configmap-missing-key, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"config-volume\", \"configMap\": \"rc-volume-key-config\"}\n- {\"name\": \"kube-api-access-fbhds\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/43f0dbc1446447a6/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/43f0dbc1446447a6/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/43f0dbc1446447a6/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-key-config\nnamespace: aiops-e2e","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/43f0dbc1446447a6/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/43f0dbc1446447a6/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/43f0dbc1446447a6/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n2m1s (x9 over 4m9s)   Warning   FailedMount   Pod/rc-volume-configmap-missing-key   MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n2m6s                  Warning   FailedMount   Pod/rc-volume-configmap-missing-key   Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/43f0dbc1446447a6/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/43f0dbc1446447a6/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/43f0dbc1446447a6/tools/004-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: ConfigMap\nname: rc-volume-key-config\nnamespace: aiops-e2e","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/43f0dbc1446447a6/tools/005-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/43f0dbc1446447a6/tools/005-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/43f0dbc1446447a6/tools/005-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"existing-key\\\": \\\"present\\\"\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/43f0dbc1446447a6/tools/006-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/43f0dbc1446447a6/tools/006-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/43f0dbc1446447a6/tools/006-evidence-run_bash_command.summary.txt"}],"llm_analysis":"## 证据采集结论\n\n### 已采集证据（全部 critical/important 级）\n\n| 证据项 | 结果 |\n|--------|------|\n| **e1: `kubectl describe pod`** | Pod `rc-volume-configmap-missing-key` 仍存在，状态 **Pending**，容器状态 **Waiting(ContainerCreating)**。Events 明确提示：`MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key` |\n| **e2: `kubectl get pod -o yaml`** | `.spec.volumes[]` 中 `config-volume` 类型为 **ConfigMap**，引用名为 `rc-volume-key-config`，`Optional: false`（非可选） |\n| **e3: `kubectl describe configmap`** | ConfigMap `rc-volume-key-config` 存在于 `aiops-e2e` 命名空间 |\n| **e4: `kubectl get configmap -o yaml`** | ConfigMap `data` 内容为：`{\"existing-key\": \"present\"}` — **不存在 `missing-key` 键** |\n| **e5: `kubectl events`** | 共 9 次重复 `FailedMount` 事件，最后一次 2 分钟前，原文一致指向 `non-existent config key: missing-key` |\n\n### 根因结论\n**Pod `rc-volume-configmap-missing-key` 卡在 ContainerCreating**，因为其 volume `config-volume` 引用 ConfigMap `rc-volume-key-config` 中的键 `missing-key`，但该 ConfigMap **只包含 `existing-key` 一个键**，`missing-key` 不存在。由于 volume 的 `Optional: false`（非可选），kubelet 无法完成挂载，Pod 持续阻塞。\n\n### 未采集证据 / 冲突证据\n- **无冲突证据** — 所有工具均返回预期结果，未出现 NotFound 或 namespace 不匹配。\n- 当前集群只有这一个异常组（`g1`），不存在其他异常组需要最小验证。","collection_summary":"计划 5 项，实际采集 3 项，未采集 2 项，完整度 60%；其中真实环境证据 5/7 项，完整度 71%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":5,"plan_collected":3,"plan_completeness":0.6,"environment_evidence_total":7,"environment_evidence_collected":5,"environment_evidence_completeness":0.7142857142857143,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"Re-verify Pod current status and Events for rc-volume-configmap-missing-key in aiops-e2e","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","purpose":"Confirm Pod still exists, verify ContainerCreating status and FailedMount events with non-existent config key error","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"Get Pod YAML to verify volume spec references ConfigMap and the specific key","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","purpose":"Check .spec.volumes[] to confirm configMap volume name and key being referenced","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"Verify the ConfigMap rc-volume-key-config exists and check its keys","level":"critical","tool":"kubectl_describe","command":"kubectl describe configmap rc-volume-key-config -n aiops-e2e","purpose":"Confirm ConfigMap exists and verify whether 'missing-key' is present in its data keys","collected":false,"source":"planned","outcome":"unknown"},{"id":"e4","description":"Get ConfigMap YAML for full key list verification","level":"important","tool":"kubectl_get_yaml","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml","purpose":"Examine ConfigMap data section to confirm missing-key is indeed absent","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"Get events sorted by timestamp for the pod to collect all FailedMount occurrences","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-configmap-missing-key --sort-by='.lastTimestamp'","purpose":"Collect all FailedMount events confirming the non-existent config key error pattern","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["e3(Verify the ConfigMap rc-volume-key-config exists and check its keys): 已规划但工具执行失败或无匹配结果","e5(Get events sorted by timestamp for the pod to collect all FailedMount occurrences): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/5 项, 完整度: 71%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | Re-verify Pod current status and Events for r... | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_yaml | Get Pod YAML to verify volume spec references... | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml` |
   | e3 | critical | ❌ | kubectl_describe | Verify the ConfigMap rc-volume-key-config exi... | `kubectl describe configmap rc-volume-key-config -n aiops-e2e` |
   | e4 | important | ✅ | kubectl_get_yaml | Get ConfigMap YAML for full key list verifica... | `kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml` |
   | e5 | important | ❌ | kubectl_events | Get events sorted by timestamp for the pod to... | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volum...` |

   ⚠️ 未采集原因:
   - e3(Verify the ConfigMap rc-volume-key-config exists and check its keys): 已规划但工具执行失败或无匹配结果
   - e5(Get events sorted by timestamp for the pod to collect all FailedMount occurrences): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (15.4s)
   📤 → 下游数据: root_cause=根因：Pod `rc-volume-configmap-missing-key`（aiops-e2e 命名空间）的 volume `config-volume` 引用 ConfigMap `rc-volume-key-config` 中的键 `missing-key`，但该 ConfigMap 实际只包含键 `existing-key`（data: {"existing-key": "present"}），不存在 `missing-key`。由于 `Optional: false`（非可选），kubelet 无法跳过该 volume 挂载，持续报错 `MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key`（e5 显示 9 次重复事件，最近一次 2 分钟前），Pod 持续卡在 Pending/ContainerCreating 状态。集群中仅此 1 个异常 Pod（共 65 个 Pod，59 个 Running），无其他
... 截断，原始 508 字符
   confidence=100%
   causal_chain={"root_cause": "ConfigMap `rc-volume-key-config` 中缺少键 `missing-key`，但 Pod volume 引用了该键，且 volume 设置为非可选（Optional: false）", "propagation": "Pod 创建时 kubelet 尝试挂载 config-volume → 去 ConfigMap rc-volume-key-config 查找 missing-key 键 → 发现该键不存在 → 挂载失败 → 持续重试（9 次 FailedMount）→ Pod 卡在 ContainerCreating/Pending 状态", "direct_cause": "Pod spec 中 volume `config-volume` 引用了 ConfigMap `rc-volume-key-config` 中不存在的键 `missing-key`", "manifestation": "Pod rc-volume-configmap-missing-key 状态为 Pending/ContainerCreating，Events 持续报 FailedMount: configmap references non-existent config key: missing-key"}
   rca_analysis={"phenomenon": "Pod `rc-volume-configmap-missing-key`（命名空间 aiops-e2e）状态为 Pending/ContainerCreating，异常类型 VolumeMountFailed。Events 报错 `MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key`，且 `kubectl events` 显示 9 次重复 FailedMount 事件，最近一次 2 分钟前。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe_pod", "content": "Pod rc-volume-configmap-missing-key 状态 Pending，容器 Waiting(ContainerCreating)，Events: MountVolume.SetUp failed: configmap references non-existent config key: missing-key", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml_pod", "content": "Pod volumes 定义 config-volume 类型 ConfigMap，引用 rc-volume-key-config，Optional: false", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe_configmap", "content": "ConfigMap rc-volume-key-config 存在于 aiops-e2e 命名空间", "reliability": "高"}, {"id": "e4", "source": "kubectl_get_yaml_configmap", "content": "ConfigMap rc-volume-key-config 的 data 字段仅包含 existing-key，无 missing-key", "reliability": "高"}, {"id": "e5", "source": "kubectl_events", "content": "9 次 FailedMount 事件，均指向 non-existent config key: missing-key", "reliability": "高"}, {"id": "e6", "source": "run_bash_command_configmap_data", "content": "ConfigMap data 内容: {\"existing-key\": \"present\"}，确认 missing-key 不存在", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "集群 65 个 Pod，仅此 1 个异常，59 个 Running", "reliability": "高"}, {"id": "layer_2", "source": "kubectl_describe_initial", "content": "初始 describe 与 e1 一致，确认事件持续存在", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key", "interpretation": "Kubelet 明确报告挂载失败的原因是 ConfigMap volume 引用了不存在的键 missing-key，这是导致 Pod 无法进入 Running 的直接原因"}, {"evidence_id": "e2", "raw_data": "volumes: [{\"name\": \"config-volume\", \"configMap\": \"rc-volume-key-config\"}] 且 Optional: false", "interpretation": "Pod spec 中 config-volume 引用 ConfigMap rc-volume-key-config，且 Optional=false 表示该 volume 必须成功挂载，不可跳过"}, {"evidence_id": "e4", "raw_data": "ConfigMap rc-volume-key-config 的 data 字段仅包含 existing-key", "interpretation": "ConfigMap 中不存在 missing-key 键，Pod 引用了 ConfigMap 中不存在的键名"}, {"evidence_id": "e5", "raw_data": "2m1s (x9 over 4m9s) Warning FailedMount ... non-existent config key: missing-key", "interpretation": "Kubelet 持续重试挂载但始终失败，9 次事件验证问题未自愈"}, {"evidence_id": "e6", "raw_data": "{\"existing-key\": \"present\"}", "interpretation": "通过直接读取 ConfigMap data 确认只包含 existing-key 一个键，缺失 missing-key"}], "causal_chain": {"root_cause": "ConfigMap `rc-volume-key-config` 中缺少键 `missing-key`，但 Pod volume 引用了该键，且 volume 设置为非可选（Optional: false）", "propagation": "Pod 创建时 kubelet 尝试挂载 config-volume → 去 ConfigMap rc-volume-key-config 查找 missing-key 键 → 发现该键不存在 → 挂载失败 → 持续重试（9 次 FailedMount）→ Pod 卡在 ContainerCreating/Pending 状态", "direct_cause": "Pod spec 中 volume `config-volume` 引用了 ConfigMap `rc-volume-key-config` 中不存在的键 `missing-key`", "manifestation": "Pod rc-volume-configmap-missing-key 状态为 Pending/ContainerCreating，Events 持续报 FailedMount: configmap references non-existent config key: missing-key"}, "root_cause": "根因：Pod `rc-volume-configmap-missing-key`（aiops-e2e 命名空间）的 volume `config-volume` 引用 ConfigMap `rc-volume-key-config` 中的键 `missing-key`，但该 ConfigMap 实际只包含键 `existing-key`（data: {\"existing-key\": \"present\"}），不存在 `missing-key`。由于 `Optional: false`（非可选），kubelet 无法跳过该 volume 挂载，持续报错 `MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key`（e5 显示 9 次重复事件，最近一次 2 分钟前），Pod 持续卡在 Pending/ContainerCreating 状态。集群中仅此 1 个异常 Pod（共 65 个 Pod，59 个 Running），无其他\n... 截断，原始 508 字符", "root_cause_summary": "根因：Pod `rc-volume-configmap-missing-key`（aiops-e2e 命名空间）的 volume `config-volume` 引用 ConfigMap `rc-volume-key-config` 中的键 `missing-key`，但该 ConfigMap 实际只包含键 `existing-key`（data: {\"existing-key\": \"present\"}），不存在 `missing-key`。由于 `Optional: false`（非可选），kubelet 无法跳过该 volume 挂载，持续报错 `MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key`（e5 显示 9 次重复事件，最近一次 2 分钟前），Pod 持续卡在 Pending/ContainerCreating 状态。集群中仅此 1 个异常 Pod（共 65 个 Pod，59 个 Running），无其他\n... 截断，原始 508 字符", "confidence": 1.0, "confidence_reason": "有直接事件证据（e1、e5）明确报错信息，Pod YAML（e2）和 ConfigMap YAML（e4）以及直接读取的 ConfigMap data（e6）交叉验证完全一致，因果链清晰完整，无可疑冲突点", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [{"cause": "ConfigMap 不存在或命名空间错误", "probability": "low", "reason": "e3 和 e4 已验证 ConfigMap rc-volume-key-config 存在于 aiops-e2e 命名空间，排除该可能"}, {"cause": "Node 磁盘故障或 kubelet 异常", "probability": "low", "reason": "集群其余 59 个 Pod 均 Running 正常，node1 上其他 Pod 无异常，排除节点级问题"}, {"cause": "PVC/PV 相关挂载问题", "probability": "low", "reason": "Events 明确指向 ConfigMap key 缺失而非存储卷问题，runbook 提示应优先按事件原文诊断"}], "limitations": "无缺失关键证据。e3（描述 ConfigMap）和 e5（按时间排序事件）已通过 e4、e1 和工具原始输出间接覆盖，不影响根因结论。当前集群仅此一个异常组，无需对非主异常组做最小验证。", "llm_raw_analysis": "L0 根因分析完成。异常组 g1 仅包含 Pod rc-volume-configmap-missing-key，无其他并发异常 Pod。根因已通过 6 项证据（e1-e6）交叉验证，因果链闭合。修复方案：在 ConfigMap rc-volume-key-config 中添加 missing-key 键，或将 Pod volume 引用的键名改为 existing-key，或将 Optional 设为 true。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 根因：Pod `rc-volume-configmap-missing-key`（aiops-e2e 命名空间）的 volume `config-volume` 引用 ConfigMap `rc-volume-key-config` 中的键 `missing-key`，但该 ConfigMap 实际...
   置信度: 100%
   🔗 因果链:
     根本原因: ConfigMap `rc-volume-key-config` 中缺少键 `missing-key`，但 Pod volume 引用了该键，且 volume 设置为非可选（Optional: false）
     传导机制: Pod 创建时 kubelet 尝试挂载 config-volume → 去 ConfigMap rc-volume-key-config 查找 missing-key 键 → 发现该键不存在 → 挂载失败 → 持续重试（9 次 FailedMount）→ Pod 卡在 ContainerCreating/Pending 状态
     最终表现: Pod rc-volume-configmap-missing-key 状态为 Pending/ContainerCreating，Events 持续报 FailedMount: configmap references non-existent config key: missing-key


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (15.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5863 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 59.9s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ContainerCreating |
| **兼容归因层** | L0 - 磁盘/存储/驱逐类 |
| **问题分类** | VolumeMountFailed（ConfigMap 卷挂载失败） |
| **置信度** | 高 (100%) |
| **证据完整度** | 3/5 (60%) |

---

# 集群现状总结
当前集群共有 **65 个 Pod**，其中 **59 个正在正常运行**，存在 **1 个异常 Pod**，无其他异常。

## 🚨 发现的唯一问题
| 命名空间 | Pod 名称 | 状态 | 异常类型 | 出现时间 |
|----------|----------|------|----------|----------|
| `aiops-e2e` | `rc-volume-configmap-missing-key` | **ContainerCreating / Pending** | VolumeMountFailed | 约 4 分钟前 |

该 Pod 卡在创建阶段无法启动，**不影响集群中其他 59 个正在运行的 Pod**，集群整体健康。

---

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-volume-configmap-missing-key` |
| Namespace | `aiops-e2e` |
| Node | `node1` |
| 错误信息 | `MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key` |
| 问题规模 | 集群 65 个 Pod 中仅 1 个异常，59 个运行正常 |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 当前状态 | `kubectl_describe` | `status: Pending`；`Reason: ContainerCreating`；`Ready: False` | Pod 卡在创建/挂载阶段，无法进入运行状态 |
| 2 | 失败事件（重复） | `kubectl_describe` / `kubectl_events` | `Warning FailedMount 119s (x9 over 4m7s) MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key` | 9 次持续报错，明确指向 ConfigMap 键缺失 |
| 3 | 超时等待事件 | `kubectl_describe` / `kubectl_events` | `Warning FailedMount 2m4s Unable to attach or mount volumes: timed out waiting for the condition` | volume 挂载持续超时 |
| 4 | Pod YAML 配置 | `kubectl_get_yaml` | `command: sh -c sleep 3600`；`finalizers: <none>`；`terminationGracePeriodSeconds: 30` | Pod 为测试用容器，finalizer 正常，不存在清理阻塞 |
| 5 | ConfigMap 实际内容 | `kubectl_get_yaml` + `run_bash_command` | ConfigMap `rc-volume-key-config` 数据：`{"existing-key": "present"}` | 该 ConfigMap 只包含键 `existing-key`，**不存在键 `missing-key`** |

### 证据关联分析
- **证据 #2 + #5 印证关键根因**：Pod volume 引用 `missing-key` → ConfigMap (`rc-volume-key-config`) 数据集仅为 `{"existing-key": "present"}`，不包含 `missing-key` → 挂载失败
- **证据 #3 揭示影响**：挂载失败导致 kubelet 持续重试 → 超时 → Pod 无法完成初始化，卡在 `ContainerCreating` 状态
- **证据 #4 排除其他可能**：`finalizers: <none>` 排除 finalizer 阻塞；`terminationGracePeriodSeconds: 30` 正常，非 Terminating 场景

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| ConfigMap 创建详情和完整 key 列表 | low | 已通过工具命令间接获取（`existing-key`），不影响根因结论 |
| 按时间排序的全部事件 | low | 9 次 FailedMount 事件已从 kubectl describe 和 kubectl events 获取，不影响根因结论 |

---

## 🎯 根因分析
### 因果链
```
┌────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                   │
│ ConfigMap `rc-volume-key-config` 中包含键 `existing-key`，                  │
│ 但**不包含 Pod volume 引用的键 `missing-key`**                              │
└────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                   │
│ Pod 创建 → kubelet 尝试挂载 config-volume 到 ConfigMap  `rc-volume-key-config` │
│       → 查找键 `missing-key` → 该键在 ConfigMap 数据中不存在                │
│       → Volume 为非可选 (Optional: false) → 无法跳过                        │
└────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                   │
│ kubelet 返回错误：`MountVolume.SetUp failed for volume "config-volume" :    │
│ configmap references non-existent config key: missing-key`                  │
└────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                               │
│ Pod 状态为 `ContainerCreating` / `Pending`，持续重试挂载，无法正常运行       │
└────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2（9 次 FailedMount 事件，明确提示 `configmap references non-existent config key: missing-key`）和证据 #5（ConfigMap `rc-volume-key-config` 实际数据仅包含 `existing-key`），
问题的根本原因是 **Pod Volume 配置中引用了 ConfigMap 中不存在的键 `missing-key`**，且该 volume 为非可选（`Optional: false`），导致 kubelet 无法跳过该挂载，Pod 持续卡在 `ContainerCreating` 状态。

**置信度**：高 (100%)
- ✅ 事件错误信息与 ConfigMap 实际内容完全吻合
- ✅ `finalizers: <none>` 排除 finalizer 清理阻塞
- ✅ 集群仅此 1 个异常，非广泛故障

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**方案 1：修复 Pod 配置（最快修复，推荐）**
> 将 Pod/Deployment 中的 volume 引用改为 ConfigMap 中实际存在的键。

**方案 2：修复 ConfigMap（如果 `missing-key` 是必要的配置项）**
```bash
# 向 ConfigMap 添加缺失的键 missing-key
kubectl patch configmap rc-volume-key-config -n aiops-e2e --patch '{"data":{"missing-key":"<对应值>"}}'
```
*依据*：当前 ConfigMap 缺少键 `missing-key`，补充后 kubelet 可正常挂载

**方案 3：重建 Pod（若需立即恢复，可选择删除重建，但问题将重现）**
```bash
kubectl delete pod rc-volume-configmap-missing-key -n aiops-e2e
```
⚠️ 此操作仅临时清除卡住的 Pod，若底层配置未修复，新 Pod 仍会失败。

### 后续优化
1. 在 CI/CD 流程中增加 ConfigMap 键名校验，确保 volume 引用的键与实际配置一致
2. 考虑使用 `optional: true` 挂载非关键配置，避免因缺失配置阻塞整个 Pod 启动

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 已删除 | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e` | 返回 Not Found |
| 2. 确认新 Pod 正常运行 | `kubectl get pod -n aiops-e2e -l app=rc-volume-configmap-missing-key` | STATUS: Running，READY: 1/1 |
| 3. 检查无 FailedMount 事件 | `kubectl get events -n aiops-e2e --field-selector reason=FailedMount` | 无返回结果（或仅历史事件） |
| 4. 确认集群整体健康 | `kubectl get pods --all-namespaces \| grep -E "(CrashLoopBackOff\|Pending\|ContainerCreating\|ImagePullBackOff\|Error)"` | 除预期外的 Pod 外无异常 |

---

## ⚠️ 注意事项
- **本次故障为单 Pod 本地问题，不影响集群整体**：59 个 Pod 正常运行，请勿采取重启节点等大范围操作
- 如果应用是生产服务且 `missing-key` 本应存在，说明上游配置分发或 ConfigMap 更新未到位，需同步排查配置管道

---

## 📊 性能统计

├─ 总耗时: 59.9s
├─ 问题定位: 14.4s (24%) ✅
├─ 证据链采集: 14.8s (25%) ✅
├─ 根因分析: 15.4s (26%) ✅
├─ 汇总总结: 15.3s (26%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 9 次
```

📋 诊断追踪

- **核心 Runbook**: pod-volume-mount-failed
- **参考 Runbook**: pod-volume-mount-failed
- **工具调用**: 9 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
