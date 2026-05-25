======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 330553ea9c4b4110]

📍 [问题定位] 执行中...
   💭 [问题定位] 首先，我来扫描整个集群的 Pod 状态，了解全局情况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59}
NAMESPACE         NAME                                                READY   STATUS              RESTARTS       A
   💭 [问题定位] 发现了一个异常 Pod。让我进一步查看它的详细信息。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                              READY   STATUS              RESTARTS   AGE     IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-volume-configmap-missing-key   0/1     ContainerCreating 
   💭 [问题定位] Pod 处于 `ContainerCreating` 状态且带有标签 `pod_abnormal_type=VolumeMountFailed`，让我进一步确认异常详情。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  39s (x10 over 4m49s)  kubelet            MountVolum
   💭 [问题定位] 问题很明确了。让我查看相关的 ConfigMap 以确认配置问题。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                   DATA   AGE     LABELS
rc-volume-key-config   1      4m51s   rootcause-e2e=true
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: ConfigMap
name: rc-volume-key-config
namespace: aiops-e2e
   💭 [问题定位] 好的，我已经掌握了全部信息。现在让我获取对应的 runbook 参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] 现在我已经掌握了全部信息，可以输出诊断结果了。

---

## 诊断分析结果

### 全局 Pod 概览

| 指标 | 数值 |
|------|------|
| 总 Pod 数 | 65 |
| 正常 Running | 59 |
| 异常 Pod | **1** |

### 异常 Pod 定位

| Pod 名称 | 命名空间 | 状态 | 就绪 |
|----------|---------|------|------|
| `rc-volume-configmap-missing-key` | `aiops-e2e` | **ContainerCreating** | 0/1 |

### 异常分析

通过 `kubectl describe` 发现关键错误事件：

> **`MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key`**

**根本原因**：Pod 的 Volume `config-volume` 引用了 ConfigMap `rc-volume-key-config`，但 ConfigMap 中**不存在名为 `missing-key` 的 key**。

具体细节：
- Pod 的 volume 定义：`config-volume` 类型为 ConfigMap，引用了 `rc-volume-key-config`
- ConfigMap `rc-volume-key-config` 存在，只有 1 个 data 条目
- Volume 配置要求 key 名称 `missing-key`，但 ConfigMap 中并没有这个 key

### 分层定级

| 字段 | 值 |
|------|-----|
| **layer** | L4 |
| **layer_name** | VolumeMountFailed - ConfigMap key 缺失 |
| **pod_abnormal_type** | `VolumeMountFailed` |
| **pod_status_keyword** | `ContainerCreating` |
| **status_category** | storage_volume |
| **confidence** | 高 |

### 异常组分类

| 异常组 | Pod 列表 |
|--------|---------|
| **volume-mount-failed** | `rc-volume-configmap-missing-key` |

### 排查方向

1. **检查 ConfigMap 定义**：确认 `rc-volume-key-config` 中是否确实需要 `missing-key` 这个 key，还是 key 名称拼写错误
2. **修正 volume 配置**：如果 `missing-key` 是需要的，需在 ConfigMap 中添加该 key；如果不需要，修改 Pod spec 中的 volume 引用，使用正确的 key 名称
3. **相关资源**：ConfigMap `rc-volume-key-config` (aiops-e2e 命名空间)
   ✅ [问题定位] 完成 (18.7s)
   📤 → 下游数据: layer=Layer.L4, layers=L4
   scenarios=[{'scenario': 'ConfigMap volume 引用了不存在的 key', 'probability': '高', 'reason': 'Events 明确提示 configmap references non-existent config key: missing-key，且 ConfigMap rc-volume-key-config 只有 1 个 data 条目，不包含 missing-key'}]
   entities=[{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}]
   reasoning=当前环境存在 1 个异常 Pod: rc-volume-configmap-missing-key (ns: aiops-e2e)，状态 ContainerCreating。kubectl describe 显示关键事件: MountVolume.SetUp failed for volume "config-volume": configmap references non-existent config key: missing-key。Pod 的 volume 引用 ConfigMap rc-volume-key-config 中确实没有 missing-key 这个 key。根据分层规则，VolumeMountFailed 且根因为 ConfigMap key 配置缺失，属于应用配置问题，故定层 L4。
   layer_analysis={"layer": "L4", "derived_layer": "L4", "layers": ["L4"], "layer_name": "VolumeMountFailed - ConfigMap key 缺失", "confidence": 0.98, "reasoning": "当前环境存在 1 个异常 Pod: rc-volume-configmap-missing-key (ns: aiops-e2e)，状态 ContainerCreating。kubectl describe 显示关键事件: MountVolume.SetUp failed for volume \"config-volume\": configmap references non-existent config key: missing-key。Pod 的 volume 引用 ConfigMap rc-volume-key-config 中确实没有 missing-key 这个 key。根据分层规则，VolumeMountFailed 且根因为 ConfigMap key 配置缺失，属于应用配置问题，故定层 L4。", "abnormal_pods": [{"name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "ConfigMap volume 引用了不存在的 key", "probability": "高", "reason": "Events 明确提示 configmap references non-existent config key: missing-key，且 ConfigMap rc-volume-key-config 只有 1 个 data 条目，不包含 missing-key"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-volume-configmap-missing-key                     0/1     ContainerCreating   0              4m47s   <none>           node1    <none>           <none>            app=rc-volume-configmap-missing-key,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/330553ea9c4b4110/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/330553ea9c4b4110/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/330553ea9c4b4110/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L4
   置信度: 98%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我已经理解了既有 evidence_plan，现在开始执行真实工具采证。先从最关键的 critical 级别工具开始：

## Step 1: 执行 e1 - describe Pod 验证 FailedMount 事件
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  62s (x10 over 5m12s)  kubelet            MountVolum
   💭 [证据链采集] ## Step 2: 执行 e2 - 获取 ConfigMap YAML 确认 data 字段
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: ConfigMap
name: rc-volume-key-config
namespace: aiops-e2e
   💭 [证据链采集] YAML 输出未显示完整 data 部分，让我用更直接的方式查看 ConfigMap 的 data 内容：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"existing-key\": \"present\"\n}\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] ## Step 3: 执行 e3 - 获取 Pod YAML 确认 volumes 引用
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
   💭 [证据链采集] ## Step 4: 执行 e4 - 查看 Pod 相关 Events 确认无其他并发异常
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
67s (x10 over 5m17s)   Warning   FailedMount   Pod/rc-volume-configmap-missing-key   MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent c
   💭 [证据链采集] 现在让我查一下 Pod spec 中 volumes 的 configMap items 详细信息，确认是否指定了 `missing-key`：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"defaultMode\": 420,\n  \"items\": [\n    {\n      \"key\": \"missing-key\",\n      \"path\": \"missing-key\"\n    }\n  ],\n  \"name\": \"rc-volume-key-config\"\n}\n
   💭 [证据链采集] 所有证据已采集完毕，以下是结论：

---

## 📋 证据采集结论

### ✅ 已采集证据（4 项）

| 证据项 | 级别 | 结果 |
|--------|------|------|
| **e1 - Pod Describe** | 🔴 Critical | **确认当前故障** - Events 仍持续报告 `MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key`（x10 次，最近 62s） |
| **e2 - ConfigMap 数据** | 🔴 Critical | **根因确认** - ConfigMap `rc-volume-key-config` 的 data 字段只有 `existing-key: present`，**不包含 `missing-key`** |
| **e3 - Pod YAML volumes** | 🔴 Critical | **确认引用链** - Pod spec.volumes[].configMap.items 明确指定了 `key: missing-key`，指向不存在的键 |
| **e4 - Pod Events** | 🟡 Important | **无其他并发异常** - 所有事件均为 `FailedMount`，无 FailedScheduling/OOM/ImagePull 等其他异常 |

### 🔍 根因分析
Pod `rc-volume-configmap-missing-key` 卡在 **ContainerCreating/Pending**，根因为：
1. Pod 的 `config-volume` 卷类型为 ConfigMap，引用了 `rc-volume-key-config`
2. 该卷的 `items` 中指定了 `key: missing-key`
3. 但 ConfigMap `rc-volume-key-config` 的 data 中**只包含 `existing-key`，不包含 `missing-key`**
4. ConfigMap 的 `Optional: false`（非可选），导致 kubelet 无法挂载该卷

### ❌ 未发现冲突/负向证据
- 所有工具均成功执行，对象存在且 namespace 匹配
- 无并发异常（Terminating/Pending/ImagePull 等）
   ✅ [证据链采集] 完成 (18.7s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"Describe Pod rc-volume-configmap-missing-key 确认当前 Events 中 FailedMount 原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e"},"purpose":"验证 FailedMount 事件原文是否仍指向 configmap references non-existent config key: missing-key","evidence_type":"event_observation","target_scope":"Pod:aiops-e2e/rc-volume-configmap-missing-key","acceptable_tools":["kubectl_describe","kubectl_events"],"counts_for_completeness":true},{"id":"e2","description":"获取 ConfigMap rc-volume-key-config 的 YAML 确认不包含 missing-key","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml","tool_args":{"kind":"ConfigMap","name":"rc-volume-key-config","namespace":"aiops-e2e"},"purpose":"验证 ConfigMap 的 data 字段确实不包含 missing-key，确认根因为配置缺失","evidence_type":"resource_config","target_scope":"ConfigMap:aiops-e2e/rc-volume-key-config","acceptable_tools":["kubectl_get_yaml","kubectl_get_by_name","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod YAML 确认 volumes 引用指向 ConfigMap rc-volume-key-config","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e"},"purpose":"确认 Pod spec.volumes 中 configMap 引用的是 rc-volume-key-config，且 items 中指定了 missing-key","evidence_type":"resource_config","target_scope":"Pod:aiops-e2e/rc-volume-configmap-missing-key","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e4","description":"获取 Pod Events 确认不存在其他异常状态（如 Terminating 并发）","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-configmap-missing-key --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-volume-configmap-missing-key"},"purpose":"确认只有 FailedMount 事件，无其他并发异常","evidence_type":"event_observation","target_scope":"Pod:aiops-e2e/rc-volume-configmap-missing-key","acceptable_tools":["kubectl_events","kubectl_describe"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  62s (x10 over 5m12s)  kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n  Warning  FailedMount  3m9s                  kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition\n  Warning  FailedMount  55s                   kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-fbhds config-volume]: timed out waiting for the condition\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  config-volume:\n    Type:      ConfigMap (a volume populated by a ConfigMap)\n    Name:      rc-volume-key-config\n    Optional:  false\n  kube-api-access-fbhds:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedMount  3m9s                  kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition\n  Warning  FailedMount  62s (x10 over 5m12s)  kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n  Warning  FailedMount  55s                   kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-fbhds config-volume]: timed out waiting for the condition\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/330553ea9c4b4110/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/330553ea9c4b4110/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/330553ea9c4b4110/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: ConfigMap\nname: rc-volume-key-config\nnamespace: aiops-e2e","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/330553ea9c4b4110/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/330553ea9c4b4110/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/330553ea9c4b4110/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"existing-key\\\": \\\"present\\\"\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/330553ea9c4b4110/tools/003-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/330553ea9c4b4110/tools/003-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/330553ea9c4b4110/tools/003-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T04:29:04Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-configmap-missing-key, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"config-volume\", \"configMap\": \"rc-volume-key-config\"}\n- {\"name\": \"kube-api-access-fbhds\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/330553ea9c4b4110/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/330553ea9c4b4110/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/330553ea9c4b4110/tools/004-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n67s (x10 over 5m17s)   Warning   FailedMount   Pod/rc-volume-configmap-missing-key   MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n3m14s                  Warning   FailedMount   Pod/rc-volume-configmap-missing-key   Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition\n60s                    Warning   FailedMount   Pod/rc-volume-configmap-missing-key   Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-fbhds config-volume]: timed out waiting for the condition","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/330553ea9c4b4110/tools/005-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/330553ea9c4b4110/tools/005-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/330553ea9c4b4110/tools/005-evidence-kubectl_events.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"defaultMode\\\": 420,\\n  \\\"items\\\": [\\n    {\\n      \\\"key\\\": \\\"missing-key\\\",\\n      \\\"path\\\": \\\"missing-key\\\"\\n    }\\n  ],\\n  \\\"name\\\": \\\"rc-volume-key-config\\\"\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/330553ea9c4b4110/tools/006-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/330553ea9c4b4110/tools/006-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/330553ea9c4b4110/tools/006-evidence-run_bash_command.summary.txt"}],"llm_analysis":"所有证据已采集完毕，以下是结论：\n\n---\n\n## 📋 证据采集结论\n\n### ✅ 已采集证据（4 项）\n\n| 证据项 | 级别 | 结果 |\n|--------|------|------|\n| **e1 - Pod Describe** | 🔴 Critical | **确认当前故障** - Events 仍持续报告 `MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key`（x10 次，最近 62s） |\n| **e2 - ConfigMap 数据** | 🔴 Critical | **根因确认** - ConfigMap `rc-volume-key-config` 的 data 字段只有 `existing-key: present`，**不包含 `missing-key`** |\n| **e3 - Pod YAML volumes** | 🔴 Critical | **确认引用链** - Pod spec.volumes[].configMap.items 明确指定了 `key: missing-key`，指向不存在的键 |\n| **e4 - Pod Events** | 🟡 Important | **无其他并发异常** - 所有事件均为 `FailedMount`，无 FailedScheduling/OOM/ImagePull 等其他异常 |\n\n### 🔍 根因分析\nPod `rc-volume-configmap-missing-key` 卡在 **ContainerCreating/Pending**，根因为：\n1. Pod 的 `config-volume` 卷类型为 ConfigMap，引用了 `rc-volume-key-config`\n2. 该卷的 `items` 中指定了 `key: missing-key`\n3. 但 ConfigMap `rc-volume-key-config` 的 data 中**只包含 `existing-key`，不包含 `missing-key`**\n4. ConfigMap 的 `Optional: false`（非可选），导致 kubelet 无法挂载该卷\n\n### ❌ 未发现冲突/负向证据\n- 所有工具均成功执行，对象存在且 namespace 匹配\n- 无并发异常（Terminating/Pending/ImagePull 等）","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 11 个，匹配计划 4 个，未规划证据 7 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":11,"matched_tool_count":4,"unplanned_tool_count":7,"evidence_inventory":[{"id":"e1","description":"Describe Pod rc-volume-configmap-missing-key 确认当前 Events 中 FailedMount 原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","purpose":"验证 FailedMount 事件原文是否仍指向 configmap references non-existent config key: missing-key","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 ConfigMap rc-volume-key-config 的 YAML 确认不包含 missing-key","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml","purpose":"验证 ConfigMap 的 data 字段确实不包含 missing-key，确认根因为配置缺失","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod YAML 确认 volumes 引用指向 ConfigMap rc-volume-key-config","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","purpose":"确认 Pod spec.volumes 中 configMap 引用的是 rc-volume-key-config，且 items 中指定了 missing-key","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取 Pod Events 确认不存在其他异常状态（如 Terminating 并发）","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-configmap-missing-key --sort-by='.lastTimestamp'","purpose":"确认只有 FailedMount 事件，无其他并发异常","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | Describe Pod rc-volume-configmap-missing-key ... | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_yaml | 获取 ConfigMap rc-volume-key-config 的 YAML 确认不包... | `kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_get_yaml | 获取 Pod YAML 确认 volumes 引用指向 ConfigMap rc-volu... | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml` |
   | e4 | important | ✅ | kubectl_events | 获取 Pod Events 确认不存在其他异常状态（如 Terminating 并发） | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volum...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (16.5s)
   📤 → 下游数据: root_cause=Pod rc-volume-configmap-missing-key (ns: aiops-e2e) 处于 ContainerCreating/Pending 状态，根因为应用配置错误：Pod 的 volume config-volume 引用 ConfigMap rc-volume-key-config 并指定 items[0].key=missing-key（optional=false），但该 ConfigMap 的 data 中仅有 existing-key: present，不包含 missing-key。kubelet Events 明确报错 "MountVolume.SetUp failed for volume 'config-volume': configmap references non-existent config key: missing-key"（x10 次重复，最近 62s）。集群其他 59 个 Pod 均正常运行，无其他并发异常。
   confidence=100%
   causal_chain={"root_cause": "ConfigMap rc-volume-key-config 的 data 中缺少 key 'missing-key'，但 Pod volume 定义中通过 items[0].key=missing-key 引用了该不存在的 key 且 optional=false。", "propagation": "Pod spec 定义 volume config-volume 引用 ConfigMap rc-volume-key-config 并指定 items key=missing-key → kubelet 尝试挂载时读取 ConfigMap 数据 → 发现 missing-key 不存在 → 因 optional=false 无法跳过 → 挂载失败。", "direct_cause": "kubelet MountVolume.SetUp failed: configmap references non-existent config key: missing-key", "manifestation": "Pod rc-volume-configmap-missing-key 卡在 ContainerCreating/Pending 状态已达 5 分钟，READY 0/1，kubelet 持续重试并报 FailedMount 事件。"}
   rca_analysis={"phenomenon": "Pod rc-volume-configmap-missing-key (ns: aiops-e2e) 状态为 ContainerCreating / Pending，0/1 Ready，已持续约 5 分钟。kubelet 持续报错 FailedMount：MountVolume.SetUp failed — configmap references non-existent config key: missing-key。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod describe 显示 Events: Warning FailedMount 'configmap references non-existent config key: missing-key' (x10 over 5m12s, 最近 62s)", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml + run_bash_command", "content": "ConfigMap rc-volume-key-config data 仅有 existing-key: present，不包含 missing-key", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_yaml + run_bash_command", "content": "Pod volumes.config-volume 指定 items[0].key=missing-key, name=rc-volume-key-config, optional=false", "reliability": "高"}, {"id": "e4", "source": "kubectl_events", "content": "全部事件均为 FailedMount，无 FailedScheduling/OOM/ImagePull 等其他异常", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "集群 65 个 Pod 中仅此 1 个异常，59 个 Running，其余正常", "reliability": "高"}, {"id": "layer_2", "source": "kubectl_get_by_name", "content": "Pod 当前状态 ContainerCreating，无其他并发状态", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedMount 62s (x10 over 5m12s) kubelet MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key", "interpretation": "kubelet 明确报告挂载失败原因：ConfigMap 中被引用的 key 'missing-key' 不存在。这是直接的故障现象。"}, {"evidence_id": "e2", "raw_data": "ConfigMap rc-volume-key-config data: {\"existing-key\": \"present\"} — 仅有一个 key 'existing-key'", "interpretation": "ConfigMap 中确实没有 'missing-key' 这个 key，数据面确认了缺失事实。"}, {"evidence_id": "e3", "raw_data": "Pod volumes: [{\"name\":\"config-volume\",\"configMap\":{\"name\":\"rc-volume-key-config\",\"items\":[{\"key\":\"missing-key\",\"path\":\"missing-key\"}],\"defaultMode\":420,\"optional\":false}}]", "interpretation": "Pod 的 volume 定义明确要求从 ConfigMap rc-volume-key-config 中取出 key=missing-key，且 optional=false（不可选），因此 key 不存在直接导致挂载失败。"}, {"evidence_id": "e4", "raw_data": "全部 Event 均为 FailedMount（x10 重复 + 2 次 timeout）", "interpretation": "无其他并发异常如 FailedScheduling、ImagePullBackOff、OOMKill 等，问题仅限于 ConfigMap 卷挂载。"}, {"evidence_id": "layer_1", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59}", "interpretation": "集群中仅此 1 个 Pod 异常，其他 Pod 运行正常，说明问题局限于该 Pod 及其配置，非集群层面故障。"}], "causal_chain": {"root_cause": "ConfigMap rc-volume-key-config 的 data 中缺少 key 'missing-key'，但 Pod volume 定义中通过 items[0].key=missing-key 引用了该不存在的 key 且 optional=false。", "propagation": "Pod spec 定义 volume config-volume 引用 ConfigMap rc-volume-key-config 并指定 items key=missing-key → kubelet 尝试挂载时读取 ConfigMap 数据 → 发现 missing-key 不存在 → 因 optional=false 无法跳过 → 挂载失败。", "direct_cause": "kubelet MountVolume.SetUp failed: configmap references non-existent config key: missing-key", "manifestation": "Pod rc-volume-configmap-missing-key 卡在 ContainerCreating/Pending 状态已达 5 分钟，READY 0/1，kubelet 持续重试并报 FailedMount 事件。"}, "root_cause": "Pod rc-volume-configmap-missing-key (ns: aiops-e2e) 处于 ContainerCreating/Pending 状态，根因为应用配置错误：Pod 的 volume config-volume 引用 ConfigMap rc-volume-key-config 并指定 items[0].key=missing-key（optional=false），但该 ConfigMap 的 data 中仅有 existing-key: present，不包含 missing-key。kubelet Events 明确报错 \"MountVolume.SetUp failed for volume 'config-volume': configmap references non-existent config key: missing-key\"（x10 次重复，最近 62s）。集群其他 59 个 Pod 均正常运行，无其他并发异常。", "root_cause_summary": "Pod rc-volume-configmap-missing-key (ns: aiops-e2e) 处于 ContainerCreating/Pending 状态，根因为应用配置错误：Pod 的 volume config-volume 引用 ConfigMap rc-volume-key-config 并指定 items[0].key=missing-key（optional=false），但该 ConfigMap 的 data 中仅有 existing-key: present，不包含 missing-key。kubelet Events 明确报错 \"MountVolume.SetUp failed for volume 'config-volume': configmap references non-existent config key: missing-key\"（x10 次重复，最近 62s）。集群其他 59 个 Pod 均正常运行，无其他并发异常。", "confidence": 1.0, "confidence_reason": "证据完整且因果关系直接：kubelet Events 原文明确指出了错误原因（e1），ConfigMap 数据面确认 key 缺失（e2），Pod YAML 确认了引用链和 optional=false（e3），三点闭环，无歧义。所有证据均为高可靠性工具采集结果。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [{"cause": "ConfigMap 不存在或被删除", "probability": "low", "reason": "ConfigMap rc-volume-key-config 存在且仅有 1 个 data 条目，未被删除；kubectl_get_yaml 和 run_bash_command 均成功获取"}, {"cause": "Node 节点故障导致无法挂载", "probability": "low", "reason": "FailedMount 事件明确指向 ConfigMap key 缺失而非节点存储问题；节点 node1 上其他 Pod 正常运行"}, {"cause": "CSI/存储插件问题", "probability": "low", "reason": "ConfigMap 卷挂载不依赖外部 CSI 插件，错误信息直接指向 ConfigMap key 缺失而非存储驱动问题"}], "limitations": "未检查 Pod template 上游（如 Deployment/StatefulSet）的 spec 是否也存在同样配置错误，当前仅验证了 Pod 自身；未检查是否还有其他 Pod 引用相同 ConfigMap 但未触发异常（因未引用 missing-key）。", "llm_raw_analysis": "【证据清点】共 6 项关键证据：e1 Pod describe 明确事件原文 'configmap references non-existent config key: missing-key'；e2 ConfigMap 数据仅含 existing-key；e3 Pod YAML volume 定义明确 items[0].key=missing-key 且 optional=false；e4 事件无其他异常；layer_1 集群仅此 1 个异常 Pod；layer_2 状态确认。【逐条分析】e1 是直接故障现象，来源可靠；e2 确认缺失；e3 确认引用链和不可选属性；e4 排除并发问题。【关联分析】e1 和 e3 构成\"Pod 要求 key → kubelet 找不到\"的因果；e2 是缺失的证据面；e3 中 optional=false 解释了为什么 kubelet 不跳过而是持续报错。【因果链】根因：ConfigMap 缺少 key → 传导：Pod volume items 指定了不存在的 key 且不可选 → 直接原因：kubelet 无法完成 MountVolume.SetU\n... 截断，原始 553 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-volume-configmap-missing-key (ns: aiops-e2e) 处于 ContainerCreating/Pending 状态，根因为应用配置错误：Pod 的 volume config-volume 引用 ConfigMap rc-volume-key-co...
   置信度: 100%
   🔗 因果链:
     根本原因: ConfigMap rc-volume-key-config 的 data 中缺少 key 'missing-key'，但 Pod volume 定义中通过 items[0].key=missing-key 引用了该不存在的 key 且 optional=false。
     传导机制: Pod spec 定义 volume config-volume 引用 ConfigMap rc-volume-key-config 并指定 items key=missing-key → kubelet 尝试挂载时读取 ConfigMap 数据 → 发现 missing-key 不存在 → 因 optional=false 无法跳过 → 挂载失败。
     最终表现: Pod rc-volume-configmap-missing-key 卡在 ContainerCreating/Pending 状态已达 5 分钟，READY 0/1，kubelet 持续重试并报 FailedMount 事件。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (16.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5661 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 10.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将为您分析集群问题。

---
## 📊 核心问题总结

首先，直接回答您的问题：**您的集群当前 (诊断时) 状态基本正常，但存在一个明确的问题。**

集群共有 **65 个 Pod**，其中 **59 个正常运行**，**1 个异常**。具体总结如下：

| 项目 | 详情 |
| :--- | :--- |
| **集群总量** | 共计 65 个 Pod，59 个 Running |
| **核心问题** | 1 个 Pod (`rc-volume-configmap-missing-key`) 处于 **ContainerCreating** 状态，无法启动 |
| **错误原因** | Pod 引用的 ConfigMap 中缺少一个指定的配置键 (key) |
| **影响范围** | 仅影响该单个 Pod，不影响集群中其他 59 个 Pod 的正常服务 |

---
## 📊 诊断概览

| 项目 | 内容 |
| :--- | :--- |
| **Pod异常状态** | ContainerCreating (VolumeMountFailed) |
| **兼容归因层** | L4 - 应用配置问题 |
| **问题分类** | VolumeMountFailed (ConfigMap Key 缺失) |
| **置信度** | 高 (100%) |
| **证据完整度** | 4/4 (100%) |

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
| :--- | :--- |
| 异常 Pod | `rc-volume-configmap-missing-key` |
| Namespace | `aiops-e2e` |
| 所在 Node | `node1` |
| 异常状态 | ContainerCreating (初始化中) |
| 错误信息 | `MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key` |

---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Pod 事件 | `kubectl describe pod` / `kubectl events` | `Warning FailedMount: MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key` (该事件已重复出现超过 10 次) | Pod 挂载 `config-volume` 卷失败，因为引用了 ConfigMap 中一个不存在的 key: `missing-key` |
| 2 | ConfigMap 内容 | `kubectl get configmap rc-volume-key-config -o json` | `{"existing-key": "present"}` | ConfigMap `rc-volume-key-config` 中确实**没有**名为 `missing-key` 的键。它只有 `existing-key`。 |
| 3 | Pod 声明 (YAML) | `kubectl get pod rc-volume-configmap-missing-key -o yaml` | `{"items": [{"key": "missing-key", "path": "missing-key"}], "name": "rc-volume-key-config"}` | Pod 的 `config-volume` 卷明确声明从 ConfigMap `rc-volume-key-config` 中**按名称 `missing-key` 挂载**一个键值对。 |
| 4 | 集群其他状态 | `kubectl get pods --all-namespaces` | 集群共有 65 个 Pod，其中 59 个状态为 `Running`。 | 集群中除了这一个 Pod，其他 59 个 Pod 均正常运行，没有其他并发异常。 |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：这是一个因果链。Pod 声明（#3）要求从 ConfigMap `rc-volume-key-config` 中提取键为 `missing-key` 的内容，但该 ConfigMap 的实际数据（#2）中只包含 `existing-key`，不包含 `missing-key`。因此，kubelet 在挂载卷时失败并报错（#1）。
- **证据 #4**：排除了集群范围故障，确认问题只局限于这一个 Pod 及其配置。

---
## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ ConfigMap 'rc-volume-key-config' (ns: aiops-e2e) 数据中        │
│ 缺少 key 'missing-key'，但 Pod 的 volume 定义中指定了该 key。    │
│ (来源: 证据 #2, #3)                                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ kubelet 尝试挂载 volume 'config-volume' → 读取 ConfigMap 数据   │
│ → 找不到 'missing-key' → 因为 volume 的 optional 属性为 false   │
│ (默认值)，无法跳过该错误 → 挂载动作失败。                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ kubelet 报告: MountVolume.SetUp failed for volume "config-volume"│
│ : configmap references non-existent config key: missing-key     │
│ (来源: 证据 #1)                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 'rc-volume-configmap-missing-key' 卡在 ContainerCreating    │
│ 状态，无法启动为 Running。                                      │
│ (来源: kubectl get pod)                                         │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (kubelet 错误事件)，证据 #2 (ConfigMap 内容) 和证据 #3 (Pod 声明)，问题的根本原因是**应用配置错误**。Pod 的 volume 声明中指定了一个不存在的 ConfigMap key (`missing-key`)，导致卷挂载失败，Pod 无法启动。

**置信度**：高 (100%)
- ✅ 错误事件原文明确指出了不存在的 key 名称。
- ✅ ConfigMap 数据与 Pod 声明完全匹配并验证了该 key 确实不存在。
- ⚠️ 无需其他证据，根本原因已十分明确。

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）
**1. [推荐] 修正 Pod 配置：将 `missing-key` 改为 `existing-key`**

- **描述**: 编辑 Pod (或其上层 Deployment/StatefulSet) 的 YAML，将 volume 中引用的 key 名称修正为 ConfigMap 中实际存在的 `existing-key`。

```bash
# 假设 Pod 由某个 Deployment 管理，修改 Deployment
kubectl edit deployment <your-deployment-name> -n aiops-e2e
```
*在编辑器中找到如下字段并修改 `key` 的值：*
```yaml
volumes:
- name: config-volume
  configMap:
    name: rc-volume-key-config
    items:
    - key: missing-key   # 将此值改为 existing-key
      path: missing-key
```

或

**1. [替代方案] 如果 `missing-key` 是正确的 key 名，则更新 ConfigMap：**
- **描述**: 在 ConfigMap `rc-volume-key-config` 中添加名为 `missing-key` 的配置项。

```bash
# 更新 ConfigMap，添加 missing-key 配置项
kubectl patch configmap rc-volume-key-config -n aiops-e2e -p '{"data":{"missing-key":"<your-required-value>"}}'
```
*注意：请将 `<your-required-value>` 替换为实际需要的配置值。*

### 后续优化
1. **代码审查**：在 CI/CD 流程中加入对 Deployment 和 ConfigMap 配置一致性的校验，防止此类不匹配问题再次发生。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
| :--- | :--- | :--- |
| 1. 确认 Pod 被删除重建 | `kubectl get pods -n aiops-e2e` | 旧的 Pod 消失，新的 Pod 被创建 |
| 2. 确认新 Pod 运行 | `kubectl get pods -n aiops-e2e \| grep rc-volume-configmap-missing-key` | STATUS: Running (或很快变为 Running) |
| 3. 检查新 Pod 事件 (如仍有问题) | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` | Events 中不应再出现 `FailedMount  configmap references non-existent config key` 的错误 |

---
## ⚠️ 注意事项
- 如果 Pod 是由 Deployment/StatefulSet 等控制器创建的，**直接删除 Pod 是无效的**，控制器会立即创建一个配置相同的 Pod，问题依旧。必须修改上层的 Deployment/StatefulSet 配置。

---

## 📊 性能统计

├─ 总耗时: 1.2m
├─ 问题定位: 18.7s (27%) ✅
├─ 证据链采集: 18.7s (27%) ✅
├─ 根因分析: 16.5s (24%) ✅
├─ 汇总总结: 16.3s (23%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 12 次
```

📋 诊断追踪

- **核心 Runbook**: pod-volume-mount-failed
- **参考 Runbook**: pod-volume-mount-failed
- **工具调用**: 12 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
