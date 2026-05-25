======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 0eb835545b0a472a]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我先全局扫描所有 Pod 的状态，看看当前集群中有哪些异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59}
NAMESPACE         NAME                                                READY   STATUS              RESTARTS       A
   💭 [问题定位] 当前集群扫描结果非常清晰，只有一个异常 Pod。

## 当前异常分析

### 全局 Pod 状态概览
| 状态 | 数量 |
|------|------|
| Running (正常) | 59 |
| **ContainerCreating (异常)** | **1** |

### 异常 Pod 详情

| Pod | 命名空间 | 状态 | 标签线索 |
|-----|---------|------|---------|
| **rc-volume-missing-secret** | aiops-e2e | ContainerCreating | `pod_abnormal_type=VolumeMountFailed` |

该 Pod 处于 **ContainerCreating** 状态，并且标签已经标注了异常类型为 `VolumeMountFailed`，说明这是一个**卷挂载失败**的问题。让我进一步确认一下详情。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-missing-secret
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  43s (x16 over 17m)     kubelet            MountVolume.SetU
   💭 [问题定位] 现在我已经拿到了完整的诊断数据，问题非常明确了。

---

## 诊断结果

### 当前异常 Pod

| Pod | 命名空间 | 状态 | 异常类型 |
|-----|---------|------|---------|
| **rc-volume-missing-secret** | aiops-e2e | ContainerCreating / Pending | **VolumeMountFailed** |

### 异常原因

核心问题在卷挂载失败的 Events 中非常清晰：

```
MountVolume.SetUp failed for volume "missing-secret" : secret "rc-definitely-missing-secret" not found
```

Pod 定义了一个名为 `missing-secret` 的 **Secret 类型卷**，引用了 Secret 名称 `rc-definitely-missing-secret`，但该 Secret **在 aiops-e2e 命名空间中不存在**，导致 kubelet 无法挂载，Pod 卡在 ContainerCreating。

### 关键证据

| 证据 | 内容 |
|------|------|
| Events | `secret "rc-definitely-missing-secret" not found`（出现 16 次）|
| Volume 类型 | `Type: Secret`，`SecretName: rc-definitely-missing-secret`，`Optional: false` |
| Pod 标签 | `pod_abnormal_type=VolumeMountFailed` |

### 结构化输出

- **layer**: L0
- **derived_layer**: L0
- **layers**: ["L0"]
- **layer_name**: 卷挂载失败 - Secret 引用缺失
- **confidence**: 高
- **pod_status_keyword**: ContainerCreating
- **pod_abnormal_type**: VolumeMountFailed
- **status_category**: storage_volume
- **abnormal_pods**: ["aiops-e2e/rc-volume-missing-secret"]
- **abnormal_groups**: ["VolumeMountFailed"]
- **key_entities**: ["Pod:rc-volume-missing-secret", "Secret:rc-definitely-missing-secret"]
- **possible_scenarios**: ["Pod 引用了不存在的 Secret 卷 `rc-definitely-missing-secret`，导致 kubelet 无法挂载"]

### 后续方向

需要下游 **evidence 节点** 进一步确认：
1. 验证 `aiops-e2e` 命名空间中是否存在 Secret `rc-definitely-missing-secret`
2. 确认 Pod 的 `.spec.volumes` 中 secret 名称拼写是否正确
3. 检查是否需要先创建该 Secret 或更正引用名称
   ✅ [问题定位] 完成 (15.3s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[{'scenario': 'Pod 引用了不存在的 Secret 卷 rc-definitely-missing-secret，导致 kubelet 无法挂载，Pod 卡在 ContainerCreating', 'probability': '高', 'reason': "Events 明确显示 MountVolume.SetUp failed for volume 'missing-secret' : secret 'rc-definitely-missing-secret' not found，Pod spec 中 volumes[].secret.secretName 确认引用该 Secret 且 Optional=false"}]
   entities=[{"type": "Pod", "name": "rc-volume-missing-secret", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-definitely-missing-secret", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}]
   reasoning=当前环境存在异常 Pod：aiops-e2e/rc-volume-missing-secret，状态为 ContainerCreating/Pending，异常类型为 VolumeMountFailed。核心根因：Pod 引用了 Secret 卷 "missing-secret"，SecretName 为 "rc-definitely-missing-secret"，但该 Secret 在 aiops-e2e 命名空间中不存在，导致 kubelet 无法挂载（Events 显示 'secret "rc-definitely-missing-secret" not found'，出现 16 次）。根据五层模型，VolumeMountFailed 因存储/卷资源缺失归入 L0 层。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "卷挂载失败 - Secret 引用缺失", "confidence": 0.95, "reasoning": "当前环境存在异常 Pod：aiops-e2e/rc-volume-missing-secret，状态为 ContainerCreating/Pending，异常类型为 VolumeMountFailed。核心根因：Pod 引用了 Secret 卷 \"missing-secret\"，SecretName 为 \"rc-definitely-missing-secret\"，但该 Secret 在 aiops-e2e 命名空间中不存在，导致 kubelet 无法挂载（Events 显示 'secret \"rc-definitely-missing-secret\" not found'，出现 16 次）。根据五层模型，VolumeMountFailed 因存储/卷资源缺失归入 L0 层。", "abnormal_pods": [{"name": "rc-volume-missing-secret", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "Pod", "name": "rc-volume-missing-secret", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-definitely-missing-secret", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}], "possible_scenarios": [{"scenario": "Pod 引用了不存在的 Secret 卷 rc-definitely-missing-secret，导致 kubelet 无法挂载，Pod 卡在 ContainerCreating", "probability": "高", "reason": "Events 明确显示 MountVolume.SetUp failed for volume 'missing-secret' : secret 'rc-definitely-missing-secret' not found，Pod spec 中 volumes[].secret.secretName 确认引用该 Secret 且 Optional=false"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-secret"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-secret"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-volume-missing-secret                            0/1     ContainerCreating   0              17m     <none>           node1    <none>           <none>            app=rc-volume-missing-secret,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/0eb835545b0a472a/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/0eb835545b0a472a/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/0eb835545b0a472a/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，根据既有 evidence_plan，我来直接执行工具调用采证。先启动可并行执行的关键工具：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": false, "stdout": "", "stderr": "Error from server (NotFound): secrets \"rc-definitely-missing-secret\" not found\n", "returncode": 1}
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-volume-missing-secret
namespace: aiops-e2e
creationTimestamp: 2026-05-21T04:01:35Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: 
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-missing-secret
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  64s (x16 over 17m)    kubelet            MountVolume.SetUp
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS
node1   Ready    <none>   238d   v1.26.8   10.2.0.49     <
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
65s (x16 over 17m)     Warning   FailedMount   Pod/rc-volume-missing-secret   MountVolume.SetUp failed for volume "missing-secret" : secret "rc-definitely-missing-secret" not
   💭 [证据链采集] 所有 5 个证据项已采集完毕，以下是证据结论：

---

## 证据采集结论

### ✅ 已采集证据（5/5）

| 项 | 级别 | 工具 | 结果 |
|---|---|---|---|
| **e1** | 🔴 critical | `kubectl describe pod` | **确认错误原文仍存在** — `MountVolume.SetUp failed for volume "missing-secret" : secret "rc-definitely-missing-secret" not found`，已出现 16 次，最近一次 64s 前 |
| **e2** | 🔴 critical | `kubectl get pod -o yaml` | **确认 spec 配置** — volumes[0].name=`missing-secret`，type=Secret，`SecretName=rc-definitely-missing-secret`，`Optional=false`（非可选卷） |
| **e3** | 🔴 critical | `kubectl get secret` | **Secret 确实不存在** — `Error from server (NotFound): secrets "rc-definitely-missing-secret" not found` 🎯 根因确认 |
| **e4** | 🟠 important | `kubectl events` | **FailedMount 事件持续发生** — 过去 17 分钟内累计出现 23 次（16+2+5），问题持续且未缓解 |
| **e5** | 🟠 important | `kubectl get node node1` | **节点状态正常** — node1 `Ready`，排除节点异常导致的挂载问题 |

### 📋 根因总结

**Pod `rc-volume-missing-secret`（aiops-e2e）卡在 Pending/ContainerCreating** 的原因：
- 直接原因：Pod 引用了 Secret 卷 `missing-secret`，其 `SecretName=rc-definitely-missing-secret`，但该 Secret 在 aiops-e2e 命名空间中**不存在**（NotFound）。
- 重要配置：`Optional=false`，意味着该 Secret 是**必需卷**，kubelet 无法创建挂载，Pod 只能卡在 ContainerCreating。
- 节点 node1 状态 Ready，排除节点导致的问题。

**修复建议**：在 aiops-e2e 命名空间中创建一个名为 `rc-definitely-missing-secret` 的 Secret，或将 Pod volumes 中的 `Optional` 设为 `true`，或移除该卷引用。
   ✅ [证据链采集] 完成 (15.6s)
   📤 → 下游数据: evidence_items=6/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"Describe Pod rc-volume-missing-secret 确认当前状态和 Events 中的 FailedMount 错误原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-secret -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-volume-missing-secret","namespace":"aiops-e2e"},"purpose":"验证 MountVolume.SetUp failed for volume 'missing-secret': secret 'rc-definitely-missing-secret' not found 错误原文是否仍然存在","evidence_type":"pod_events","target_scope":"Pod","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod YAML 确认 spec.volumes 中 secret.secretName 引用","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-missing-secret -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-volume-missing-secret","namespace":"aiops-e2e"},"purpose":"验证 volumes[].secret.secretName 是否确实引用 rc-definitely-missing-secret 且 optional=false","evidence_type":"pod_spec","target_scope":"Pod","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"确认 Secret rc-definitely-missing-secret 在 aiops-e2e 命名空间中不存在","level":"critical","tool":"run_bash_command","command":"kubectl get secret rc-definitely-missing-secret -n aiops-e2e","tool_args":{"command":"kubectl get secret rc-definitely-missing-secret -n aiops-e2e"},"purpose":"验证 Secret 是否真的不存在（NotFound），确认根因","evidence_type":"resource_existence","target_scope":"Secret","acceptable_tools":["run_bash_command","kubectl_get_by_name"],"counts_for_completeness":true},{"id":"e4","description":"查看 aiops-e2e 命名空间中的 events 确认 Pod 相关的 FailedMount 事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-missing-secret --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e"},"purpose":"确认 FailedMount 事件计数和时间戳，验证问题持续存在","evidence_type":"pod_events","target_scope":"Namespace","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"e5","description":"获取 Node node1 状态确认节点是否正常","level":"important","tool":"kubectl_get_by_name","command":"kubectl get node node1 -o wide","tool_args":{"kind":"Node","name":"node1"},"purpose":"验证节点状态是否 Ready，排除节点异常导致的挂载问题","evidence_type":"node_status","target_scope":"Node","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"run_bash_command","data":"{\"success\": false, \"stdout\": \"\", \"stderr\": \"Error from server (NotFound): secrets \\\"rc-definitely-missing-secret\\\" not found\\n\", \"returncode\": 1}","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/0eb835545b0a472a/tools/001-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0eb835545b0a472a/tools/001-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0eb835545b0a472a/tools/001-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-missing-secret\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T04:01:35Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-missing-secret, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"missing-secret\", \"secret\": null}\n- {\"name\": \"kube-api-access-7n89z\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0eb835545b0a472a/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0eb835545b0a472a/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0eb835545b0a472a/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-missing-secret\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  64s (x16 over 17m)    kubelet            MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found\n  Warning  FailedMount  4m5s (x2 over 8m33s)  kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-secret], unattached volumes=[kube-api-access-7n89z missing-secret]: timed out waiting for the condition\n  Warning  FailedMount  108s (x5 over 15m)    kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-secret], unattached volumes=[missing-secret kube-api-access-7n89z]: timed out waiting for the condition\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  missing-secret:\n    Type:        Secret (a volume populated by a Secret)\n    SecretName:  rc-definitely-missing-secret\n    Optional:    false\n  kube-api-access-7n89z:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedMount  4m5s (x2 over 8m33s)  kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-secret], unattached volumes=[kube-api-access-7n89z missing-secret]: timed out waiting for the condition\n  Warning  FailedMount  108s (x5 over 15m)    kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-secret], unattached volumes=[missing-secret kube-api-access-7n89z]: timed out waiting for the condition\n  Warning  FailedMount  64s (x16 over 17m)    kubelet            MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0eb835545b0a472a/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0eb835545b0a472a/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0eb835545b0a472a/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME    STATUS   ROLES    AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\nnode1   Ready    <none>   238d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0eb835545b0a472a/tools/004-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0eb835545b0a472a/tools/004-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0eb835545b0a472a/tools/004-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n65s (x16 over 17m)     Warning   FailedMount   Pod/rc-volume-missing-secret   MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found\n4m6s (x2 over 8m34s)   Warning   FailedMount   Pod/rc-volume-missing-secret   Unable to attach or mount volumes: unmounted volumes=[missing-secret], unattached volumes=[kube-api-access-7n89z missing-secret]: timed out waiting for the condition\n109s (x5 over 15m)     Warning   FailedMount   Pod/rc-volume-missing-secret   Unable to attach or mount volumes: unmounted volumes=[missing-secret], unattached volumes=[missing-secret kube-api-access-7n89z]: timed out waiting for the condition","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0eb835545b0a472a/tools/005-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0eb835545b0a472a/tools/005-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0eb835545b0a472a/tools/005-evidence-kubectl_events.summary.txt"}],"llm_analysis":"所有 5 个证据项已采集完毕，以下是证据结论：\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据（5/5）\n\n| 项 | 级别 | 工具 | 结果 |\n|---|---|---|---|\n| **e1** | 🔴 critical | `kubectl describe pod` | **确认错误原文仍存在** — `MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found`，已出现 16 次，最近一次 64s 前 |\n| **e2** | 🔴 critical | `kubectl get pod -o yaml` | **确认 spec 配置** — volumes[0].name=`missing-secret`，type=Secret，`SecretName=rc-definitely-missing-secret`，`Optional=false`（非可选卷） |\n| **e3** | 🔴 critical | `kubectl get secret` | **Secret 确实不存在** — `Error from server (NotFound): secrets \"rc-definitely-missing-secret\" not found` 🎯 根因确认 |\n| **e4** | 🟠 important | `kubectl events` | **FailedMount 事件持续发生** — 过去 17 分钟内累计出现 23 次（16+2+5），问题持续且未缓解 |\n| **e5** | 🟠 important | `kubectl get node node1` | **节点状态正常** — node1 `Ready`，排除节点异常导致的挂载问题 |\n\n### 📋 根因总结\n\n**Pod `rc-volume-missing-secret`（aiops-e2e）卡在 Pending/ContainerCreating** 的原因：\n- 直接原因：Pod 引用了 Secret 卷 `missing-secret`，其 `SecretName=rc-definitely-missing-secret`，但该 Secret 在 aiops-e2e 命名空间中**不存在**（NotFound）。\n- 重要配置：`Optional=false`，意味着该 Secret 是**必需卷**，kubelet 无法创建挂载，Pod 只能卡在 ContainerCreating。\n- 节点 node1 状态 Ready，排除节点导致的问题。\n\n**修复建议**：在 aiops-e2e 命名空间中创建一个名为 `rc-definitely-missing-secret` 的 Secret，或将 Pod volumes 中的 `Optional` 设为 `true`，或移除该卷引用。","collection_summary":"计划 5 项，实际采集 4 项，未采集 1 项，完整度 80%；其中真实环境证据 6/7 项，完整度 86%；实际执行工具 6 个，匹配计划 4 个，未规划证据 2 个","plan_total":5,"plan_collected":4,"plan_completeness":0.8,"environment_evidence_total":7,"environment_evidence_collected":6,"environment_evidence_completeness":0.8571428571428571,"executed_tool_count":6,"matched_tool_count":4,"unplanned_tool_count":2,"evidence_inventory":[{"id":"e1","description":"Describe Pod rc-volume-missing-secret 确认当前状态和 Events 中的 FailedMount 错误原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-secret -n aiops-e2e","purpose":"验证 MountVolume.SetUp failed for volume 'missing-secret': secret 'rc-definitely-missing-secret' not found 错误原文是否仍然存在","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod YAML 确认 spec.volumes 中 secret.secretName 引用","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-missing-secret -n aiops-e2e -o yaml","purpose":"验证 volumes[].secret.secretName 是否确实引用 rc-definitely-missing-secret 且 optional=false","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"确认 Secret rc-definitely-missing-secret 在 aiops-e2e 命名空间中不存在","level":"critical","tool":"run_bash_command","command":"kubectl get secret rc-definitely-missing-secret -n aiops-e2e","purpose":"验证 Secret 是否真的不存在（NotFound），确认根因","collected":false,"source":"planned","outcome":"unknown"},{"id":"e4","description":"查看 aiops-e2e 命名空间中的 events 确认 Pod 相关的 FailedMount 事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-missing-secret --sort-by='.lastTimestamp'","purpose":"确认 FailedMount 事件计数和时间戳，验证问题持续存在","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"获取 Node node1 状态确认节点是否正常","level":"important","tool":"kubectl_get_by_name","command":"kubectl get node node1 -o wide","purpose":"验证节点状态是否 Ready，排除节点异常导致的挂载问题","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["e3(确认 Secret rc-definitely-missing-secret 在 aiops-e2e 命名空间中不存在): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/5 项, 完整度: 86%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | Describe Pod rc-volume-missing-secret 确认当前状态和... | `kubectl describe pod rc-volume-missing-secret -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_yaml | 获取 Pod YAML 确认 spec.volumes 中 secret.secretNa... | `kubectl get pod rc-volume-missing-secret -n aiops-e2e -o yaml` |
   | e3 | critical | ❌ | run_bash_command | 确认 Secret rc-definitely-missing-secret 在 aiop... | `kubectl get secret rc-definitely-missing-secret -n aiops-e2e` |
   | e4 | important | ✅ | kubectl_events | 查看 aiops-e2e 命名空间中的 events 确认 Pod 相关的 FailedM... | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volum...` |
   | e5 | important | ✅ | kubectl_get_by_name | 获取 Node node1 状态确认节点是否正常 | `kubectl get node node1 -o wide` |

   ⚠️ 未采集原因:
   - e3(确认 Secret rc-definitely-missing-secret 在 aiops-e2e 命名空间中不存在): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (15.5s)
   📤 → 下游数据: root_cause=根因：Pod aiops-e2e/rc-volume-missing-secret 因引用的 Secret 卷缺失而无法启动。Pod spec 中 volumes[0].secret.secretName=rc-definitely-missing-secret、Optional=false，但该 Secret 在 aiops-e2e 命名空间中不存在（kubectl get secret 返回 NotFound 错误）。kubelet 持续重试 17 分钟，累计触发 23 次 FailedMount 事件（MountVolume.SetUp failed: secret 'rc-definitely-missing-secret' not found），Pod 状态卡在 Pending/ContainerCreating（0/1）。节点 node1 状态 Ready，排除节点侧问题。
   confidence=95%
   causal_chain={"root_cause": "Pod rc-volume-missing-secret 引用了 Secret 卷 missing-secret（SecretName=rc-definitely-missing-secret），但该 Secret 在 aiops-e2e 命名空间中不存在，且 Optional=false 导致该卷为必需卷，kubelet 无法跳过挂载。", "propagation": "Secret 不存在 → kubelet MountVolume.SetUp 失败 → kubelet 持续重试却始终找不到 Secret → FailedMount 事件累计 23 次 → 卷挂载无法完成 → Pod 卡在 Pending/ContainerCreating", "direct_cause": "Secret rc-definitely-missing-secret 在 aiops-e2e 命名空间中不存在（NotFound），Pod volumes 中 Optional=false，kubelet 无法创建 Secret 卷挂载。", "manifestation": "用户可见 Pod aiops-e2e/rc-volume-missing-secret 处于 Pending/ContainerCreating 状态 17 分钟，READY 0/1，Events 持续报 FailedMount 错误。"}
   rca_analysis={"phenomenon": "Pod aiops-e2e/rc-volume-missing-secret 状态为 Pending/ContainerCreating（0/1），异常类型 VolumeMountFailed，当前持续 17 分钟，调度在 node1 节点上。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod rc-volume-missing-secret 状态 Pending，Events 显示 FailedMount: MountVolume.SetUp failed for volume 'missing-secret' : secret 'rc-definitely-missing-secret' not found（x16 over 17m）", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml", "content": "Pod spec 中 volumes[0] name=missing-secret, type=Secret, SecretName=rc-definitely-missing-secret, Optional=false", "reliability": "高"}, {"id": "e3", "source": "run_bash_command (kubectl get secret)", "content": "Secret rc-definitely-missing-secret 在 aiops-e2e 命名空间中不存在（NotFound 错误）", "reliability": "高"}, {"id": "e4", "source": "kubectl_events", "content": "aiops-e2e 命名空间中 Pod/rc-volume-missing-secret 的 FailedMount 事件累计 23 次（16+2+5），持续 17 分钟", "reliability": "高"}, {"id": "e5", "source": "kubectl_get_by_name (node)", "content": "node1 状态 Ready，v1.26.8，正常运行 238 天，无异常标记", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedMount 64s (x16 over 17m) kubelet MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found", "interpretation": "kubelet 明确报告无法挂载卷 missing-secret，因为引用的 Secret rc-definitely-missing-secret 不存在。该错误在过去 17 分钟内重复出现 16 次，是持续性问题而非偶发。"}, {"evidence_id": "e2", "raw_data": "volumes: [{\"name\": \"missing-secret\", \"secret\": null}] -> SecretName: rc-definitely-missing-secret, Optional: false", "interpretation": "Pod 的 volumes 配置中卷 missing-secret 的类型为 Secret，引用的 SecretName 为 rc-definitely-missing-secret，且 Optional=false 表示该卷为必需卷（非可选），kubelet 无法跳过此卷挂载。"}, {"evidence_id": "e3", "raw_data": "Error from server (NotFound): secrets \"rc-definitely-missing-secret\" not found", "interpretation": "直接验证确认 Secret rc-definitely-missing-secret 在 aiops-e2e 命名空间中确实不存在。这是 MountVolume.SetUp 失败的根本原因。"}, {"evidence_id": "e4", "raw_data": "65s (x16 over 17m) Warning FailedMount; 4m6s (x2 over 8m34s); 109s (x5 over 15m)", "interpretation": "FailedMount 事件在 17 分钟内累计触发 23 次（16+2+5），表明 kubelet 持续重试且持续失败，问题未自动恢复。"}, {"evidence_id": "e5", "raw_data": "node1 Ready, v1.26.8, 238d", "interpretation": "节点 node1 状态正常（Ready），运行 238 天，排除节点故障导致的卷挂载失败。问题定位在 Pod 配置层面。"}], "causal_chain": {"root_cause": "Pod rc-volume-missing-secret 引用了 Secret 卷 missing-secret（SecretName=rc-definitely-missing-secret），但该 Secret 在 aiops-e2e 命名空间中不存在，且 Optional=false 导致该卷为必需卷，kubelet 无法跳过挂载。", "propagation": "Secret 不存在 → kubelet MountVolume.SetUp 失败 → kubelet 持续重试却始终找不到 Secret → FailedMount 事件累计 23 次 → 卷挂载无法完成 → Pod 卡在 Pending/ContainerCreating", "direct_cause": "Secret rc-definitely-missing-secret 在 aiops-e2e 命名空间中不存在（NotFound），Pod volumes 中 Optional=false，kubelet 无法创建 Secret 卷挂载。", "manifestation": "用户可见 Pod aiops-e2e/rc-volume-missing-secret 处于 Pending/ContainerCreating 状态 17 分钟，READY 0/1，Events 持续报 FailedMount 错误。"}, "root_cause": "根因：Pod aiops-e2e/rc-volume-missing-secret 因引用的 Secret 卷缺失而无法启动。Pod spec 中 volumes[0].secret.secretName=rc-definitely-missing-secret、Optional=false，但该 Secret 在 aiops-e2e 命名空间中不存在（kubectl get secret 返回 NotFound 错误）。kubelet 持续重试 17 分钟，累计触发 23 次 FailedMount 事件（MountVolume.SetUp failed: secret 'rc-definitely-missing-secret' not found），Pod 状态卡在 Pending/ContainerCreating（0/1）。节点 node1 状态 Ready，排除节点侧问题。", "root_cause_summary": "根因：Pod aiops-e2e/rc-volume-missing-secret 因引用的 Secret 卷缺失而无法启动。Pod spec 中 volumes[0].secret.secretName=rc-definitely-missing-secret、Optional=false，但该 Secret 在 aiops-e2e 命名空间中不存在（kubectl get secret 返回 NotFound 错误）。kubelet 持续重试 17 分钟，累计触发 23 次 FailedMount 事件（MountVolume.SetUp failed: secret 'rc-definitely-missing-secret' not found），Pod 状态卡在 Pending/ContainerCreating（0/1）。节点 node1 状态 Ready，排除节点侧问题。", "confidence": 0.95, "confidence_reason": "直接证据链完整且闭合：Pod Events 直接报错文本 + Pod YAML 确认配置 + kubectl get secret 确认 Secret 不存在 + 节点正常排除干扰项。因果链无断层。缺失证据 e3 已在采集阶段通过 run_bash_command 补充，证据完整。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [{"cause": "节点 node1 故障导致卷挂载失败", "probability": "low", "reason": "已排除：node1 状态 Ready，运行 238 天正常"}, {"cause": "PVC/PV 配置问题", "probability": "low", "reason": "Pod 引用的是 Secret 卷而非 PVC，不涉及 PVC/PV"}, {"cause": "CSI 驱动或存储插件问题", "probability": "low", "reason": "Secret 卷由 kubelet 内置管理，不依赖外部 CSI 驱动；事件明确指向 Secret 不存在而非驱动错误"}], "limitations": "未采集 Pod 的完整 YAML（原始截断），但已采集的关键字段（volumes、SecretName、Optional）足以支撑根因判断。未采集命名空间下所有 Secret 列表，但直接查询目标 Secret 的 NotFound 结果已足够确认根因。", "llm_raw_analysis": "按照 L0 根因分析流程执行。证据清点：共 5 条证据（e1-e5），全部已采集。逐条分析：e1 和 e4 确认 FailedMount 事件持续报 Secret not found；e2 确认 Pod spec 配置了 SecretName=rc-definitely-missing-secret 且 Optional=false；e3 直接验证 Secret 不存在；e5 排除节点故障。关联分析：所有证据指向同一根因——Secret 不存在。因果链：Secret 不存在（根因）→ kubelet MountVolume.SetUp 失败（直接原因）→ 卷无法挂载 → Pod 卡在 Pending/ContainerCreating（现象）。置信度 0.95，证据充分。无其他异常组需要验证。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 根因：Pod aiops-e2e/rc-volume-missing-secret 因引用的 Secret 卷缺失而无法启动。Pod spec 中 volumes[0].secret.secretName=rc-definitely-missing-secret、Optional=false，但该 ...
   置信度: 95%
   🔗 因果链:
     根本原因: Pod rc-volume-missing-secret 引用了 Secret 卷 missing-secret（SecretName=rc-definitely-missing-secret），但该 Secret 在 aiops-e2e 命名空间中不存在，且 Optional=false 导致该卷为必需卷，kubelet 无法跳过挂载。
     传导机制: Secret 不存在 → kubelet MountVolume.SetUp 失败 → kubelet 持续重试却始终找不到 Secret → FailedMount 事件累计 23 次 → 卷挂载无法完成 → Pod 卡在 Pending/ContainerCreating
     最终表现: 用户可见 Pod aiops-e2e/rc-volume-missing-secret 处于 Pending/ContainerCreating 状态 17 分钟，READY 0/1，Events 持续报 FailedMount 错误。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (17.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5838 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 3.6s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将基于您提供的三个阶段分析结果，为您生成一份详尽、完整的诊断报告。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **集群健康状况** | 集群整体运行正常，在 65 个运行态资源中，有 59 个 `Running` 正常。**发现 1 个异常 Pod**，是当前唯一需要关注的问题。 |
| **Pod异常状态** | `ContainerCreating` |
| **兼容归因层** | L0 |
| **问题分类** | `VolumeMountFailed` (卷挂载失败) |
| **置信度** | 高 (95%) |
| **证据完整度** | 4/5 (80%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-volume-missing-secret` |
| Namespace | `aiops-e2e` |
| Node | `node1` |
| 错误信息 | `MountVolume.SetUp failed for volume "missing-secret" : secret "rc-definitely-missing-secret" not found` |

---

## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 事件 | `kubectl describe pod` / `kubectl events` | `Warning FailedMount 64s (x16 over 17m) kubelet MountVolume.SetUp failed for volume "missing-secret" : secret "rc-definitely-missing-secret" not found` | kubelet 尝试挂载名为 `missing-secret` 的卷时失败，原因是指定的 Secret `rc-definitely-missing-secret` 不存在。 |
| 2 | Pod YAML | `kubectl get pod -o yaml` | `volumes[0].secret.secretName=rc-definitely-missing-secret`，`finalizers: <none>`, `terminationGracePeriodSeconds: 30` | Pod 配置明确引用了 Secret `rc-definitely-missing-secret`。排除 finalizer 问题，且 Pod 并非处于 `Terminating` 状态。 |
| 3 | 直接查询 Secret | `kubectl get secret rc-definitely-missing-secret -n aiops-e2e` | `Error from server (NotFound): secrets "rc-definitely-missing-secret" not found` | **直接确认**：名为 `rc-definitely-missing-secret` 的 Secret 在 `aiops-e2e` 命名空间中不存在。 |
| 4 | 节点状态 | `kubectl get node node1` | `STATUS: Ready`，节点运行 238 天，状态健康。 | 排除节点不可用或 kubelet 问题导致的挂载失败。 |
| 5 | 集群异常概览 | `kubectl get all -A` (已汇总) | 集群总计 65 行资源，59 个 Running，唯一异常为当前分析的 Pod。 | 问题范围明确，仅限于目标 Pod，不影响其他工作负载。 |

### 证据关联分析
- **证据 #1 → #3 印证**：Pod 事件日志明确报告 “Secret not found”，证据 #3 通过直接查询 Secret 对象证实该 Secret **确实不存在**，形成完整的证据闭环。
- **证据 #4 排除干扰**：节点状态 `Ready` 表明问题根源在于应用配置，而非底层节点或 kubelet 故障。
- **证据 #5 范围确认**：整个集群只有一个异常，无需在其他 Namespace 或资源中寻找关联问题。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| (无) | - | - |
**备注**：虽然 `e3` 标记为“未采集”，但这是由于工具执行时 Secret 不存在返回了 NotFound 错误，该错误结果本身已构成关键证据，证明 Secret 缺失。因此不构成证据缺失。

---

## 🎯 根因分析

### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                                  │
│ Pod 在 spec 中引用了不存在的 Secret 对象 `rc-definitely-missing-secret` (Optional=false)    │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                                  │
│ kubelet 尝试创建卷挂载 → 根据 spec 查询 Secret `rc-definitely-missing-secret` → 查询失败    │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                                  │
│ kubelet 报错: `MountVolume.SetUp failed for volume "missing-secret" : secret              │
│  "rc-definitely-missing-secret" not found`                                               │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                              │
│ Pod `rc-volume-missing-secret` 处于 `Pending` / `ContainerCreating` 状态，持续 17 分钟。   │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (FailedMount 事件)、证据 #2 (Pod YAML 配置) 和证据 #3 (Secret 查询结果为 NotFound)，
问题的根本原因是 **Pod `rc-volume-missing-secret` 配置引用了 Secret `rc-definitely-missing-secret`，但该 Secret 在 `aiops-e2e` 命名空间中不存在**。由于该 Secret 卷不是可选的 (`Optional=false`)，kubelet 无法跳过挂载，导致 Pod 启动流程卡住。

**置信度**：高 (95%)
- ✅ **证据 #1**: Pod 事件 **明确** 指明 Secret 不存在。
- ✅ **证据 #3**: 直接命令查询 **明确** 返回 NotFound。
- ✅ **证据 #4**: 节点状态 `Ready`，排除了节点故障的干扰。
- ⚠️ **技术限制**: 无法还原该 Secret 是否被误删除或从未创建，但这不影响根因判断。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）
**1. [优先] 创建缺失的 Secret**
```bash
# 方法一：如果知道原始 Secret 内容（建议），创建一个新的 Secret
kubectl create secret generic rc-definitely-missing-secret \
  --from-literal=key1=value1 \
  -n aiops-e2e
```
```bash
# 方法二：如果不知道内容，可以创建一个空的 Secret 来恢复 Pod
kubectl create secret generic rc-definitely-missing-secret \
  --from-literal=dummy-key=dummy-value \
  -n aiops-e2e
```
*依据*：创建 Secret 后，kubelet 会自动重试挂载，Pod 将自动转为 `Running` 状态。

**2. [备选] 如果不再需要该 Secret，修改 Pod 配置**
```bash
# 编辑 Deployment 或 Pod，移除对缺失 Secret 卷的引用，或将 `optional` 设置为 `true`
kubectl edit <deployment/pod> -n aiops-e2e
```
*修改内容示例*：
```yaml
volumes:
- name: missing-secret    # 删除或修改此段
  secret:
    secretName: rc-definitely-missing-secret
    optional: true        # 或添加此字段，使该卷变为非必需
```
*适用场景*：如果应用程序实际上并不依赖该 Secret，可以将其设置为可选，避免启动阻塞。

### 后续优化
1. **配置审计**：在 CI/CD 流程中增加对 Secret 引用的校验，确保在创建资源前 Secret 已存在。
2. **监控告警**：对 `FailedMount` 事件设置告警，以便在 Pod 挂载失败时第一时间感知。
3. **文档**：完善应用部署文档，确保 Secret 的创建步骤被明确记录。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 创建 Secret 后检查 Pod 状态 | `kubectl get pod rc-volume-missing-secret -n aiops-e2e -w` | STATUS 从 `ContainerCreating` 变为 `Running` |
| 2. 最终确认 | `kubectl get pod rc-volume-missing-secret -n aiops-e2e` | READY: `1/1` |
| 3. 检查集群异常总数 | `kubectl get pods -A --field-selector=status.phase!=Running` | 无异常项 |

---

## ⚠️ 注意事项
- **删除风险**：如果错误地删除了生产环境的 Secret，所有引用该 Secret 的 Pod 都将进入 `ContainerCreating` 状态，需谨慎操作。
- **数据安全**：创建 Secret 时，请使用 Base64 格式传输敏感数据。避免在命令行明文输入密码。

---

## 📊 性能统计

├─ 总耗时: 1.1m
├─ 问题定位: 15.3s (24%) ✅
├─ 证据链采集: 15.6s (24%) ✅
├─ 根因分析: 15.5s (24%) ✅
├─ 汇总总结: 17.2s (27%) ✅
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
