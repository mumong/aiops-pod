======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 9cd06c1d785f41cc]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我先做一个全局 Pod 扫描，看看集群中所有 Pod 的状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59}
NAMESPACE         NAME                                                READY   STATUS              RESTARTS       A
   💭 [问题定位] 很好，扫描结果已经出来了。我看到有一个异常 Pod，让我进一步查看它的详细信息。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-missing-configmap
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  48s (x8 over 112s)  kubelet            MountVolume.SetU
   💭 [问题定位] 这个 Pod 已经带上了 `pod_abnormal_type=VolumeMountFailed` 标签，完全匹配。让我获取对应的 runbook 进行参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] 现在我已经获得了所有必要的信息。让我整理一下分析结果。

## 全局 Pod 异常分析

### 总体概况
集群共有 **65** 个 Pod，分布在各个命名空间，其中 **59** 个正常 Running，**1** 个异常 Pod。

### 异常 Pod 清单

| 命名空间 | Pod 名称 | 状态 | 异常类型 |
|---------|---------|------|---------|
| `aiops-e2e` | `rc-volume-missing-configmap` | ContainerCreating（Pending） | **VolumeMountFailed** |

---

### 详细分析：`rc-volume-missing-configmap`（L0 级异常）

**状态详情：**
- **当前状态**：`ContainerCreating`（Pending，未进入 Running）
- **异常类型**：`VolumeMountFailed`（L0 — 存储/卷挂载层异常）
- **所在节点**：`node1`

**关键证据（Events）：**
```
Warning  FailedMount  48s (x8 over 112s)  kubelet  
MountVolume.SetUp failed for volume "missing-config" : 
configmap "rc-definitely-missing-configmap" not found
```

**根本原因：**
该 Pod 的 `spec.volumes` 中定义了一个 **ConfigMap 类型的卷** `missing-config`，引用了名为 `rc-definitely-missing-configmap` 的 ConfigMap。但该 ConfigMap 在当前 `aiops-e2e` 命名空间中 **不存在**，导致 kubelet 在挂载卷时失败，Pod 卡在 `ContainerCreating`。

---

### 分层结果

| 字段 | 值 |
|------|-----|
| **layer** | L0 |
| **derived_layer** | L0 |
| **layers** | [L0] |
| **layer_name** | VolumeMountFailed |
| **confidence** | 高 |
| **pod_status_keyword** | ContainerCreating |
| **pod_abnormal_type** | VolumeMountFailed |
| **status_category** | 存储/卷挂载异常 |

### 后续审查方向
1. **确认 ConfigMap 是否存在**：在 `aiops-e2e` 命名空间检查 `rc-definitely-missing-configmap` 是否被误删或从未创建。
2. **检查应用部署清单**：确认是否 ConfigMap 名称拼写错误（例如命名不一致）。
3. **若为故意设计的测试用例**：需创建缺失的 ConfigMap，Pod 即可自动恢复。

**注意**：该 Pod 带有 `rootcause-e2e=true` 和 `pod_abnormal_type=VolumeMountFailed` 标签，看起来是一个 **端到端测试用例**，用于模拟 ConfigMap 卷挂载失败的场景。
   ✅ [问题定位] 完成 (15.8s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[{'scenario': 'ConfigMap卷引用了不存在的ConfigMap对象', 'probability': '高', 'reason': 'Events明确显示 configmap rc-definitely-missing-configmap not found，Pod卡在ContainerCreating'}]
   entities=[{"type": "Pod", "name": "rc-volume-missing-configmap", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-definitely-missing-configmap", "namespace": "aiops-e2e"}]
   reasoning=集群中有一个异常Pod `rc-volume-missing-configmap`（namespace: aiops-e2e），当前状态为ContainerCreating（Pending），异常类型为VolumeMountFailed。关键证据：kubelet FailedMount事件显示`configmap "rc-definitely-missing-configmap" not found`，Pod spec中volume引用了不存在的ConfigMap。该Pod暂未恢复，属于当前活跃的L0级异常（存储/卷挂载层）。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "VolumeMountFailed", "confidence": 0.95, "reasoning": "集群中有一个异常Pod `rc-volume-missing-configmap`（namespace: aiops-e2e），当前状态为ContainerCreating（Pending），异常类型为VolumeMountFailed。关键证据：kubelet FailedMount事件显示`configmap \"rc-definitely-missing-configmap\" not found`，Pod spec中volume引用了不存在的ConfigMap。该Pod暂未恢复，属于当前活跃的L0级异常（存储/卷挂载层）。", "abnormal_pods": [{"name": "rc-volume-missing-configmap", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "Pod", "name": "rc-volume-missing-configmap", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-definitely-missing-configmap", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "ConfigMap卷引用了不存在的ConfigMap对象", "probability": "高", "reason": "Events明确显示 configmap rc-definitely-missing-configmap not found，Pod卡在ContainerCreating"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-configmap"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-configmap"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-volume-missing-configmap                         0/1     ContainerCreating   0              110s    <none>           node1    <none>           <none>            app=rc-volume-missing-configmap,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/9cd06c1d785f41cc/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/9cd06c1d785f41cc/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/9cd06c1d785f41cc/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，根据既有 evidence_plan，我先执行所有 critical 级别的工具调用。由于它们是独立的，可以同时执行。

**Step 1: 获取 Runbook 参考 + 验证 Pod 状态和 Events + 获取 Pod YAML + 确认 ConfigMap 是否存在**
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": false, "stdout": "", "stderr": "Error from server (NotFound): configmaps \"rc-definitely-missing-configmap\" not found\n", "returncode": 1}
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-volume-missing-configmap
namespace: aiops-e2e
creationTimestamp: 2026-05-21T03:33:04Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizer
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-missing-configmap
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  3s (x9 over 2m11s)  kubelet            MountVolume.SetU
   💭 [证据链采集] 所有关键工具已执行完毕，以下是证据采集结论：

---

## ✅ 证据采集结论

### 已采集证据

| # | 工具 | 关键发现 |
|---|------|---------|
| **e1** | `kubectl describe pod` | ✅ Pod `rc-volume-missing-configmap` 当前 status=**Pending**，容器状态 Waiting(Reason=**ContainerCreating**)。Events 中明确显示：`Warning FailedMount` — `MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found`（已出现 9 次） |
| **e2** | `kubectl_get_yaml` | ✅ Pod spec `.spec.volumes[]` 确认：volume **missing-config** 的类型是 **ConfigMap**（`configMap.name: rc-definitely-missing-configmap`），**非 PVC/Secret/hostPath/CSI** |
| **e3** | `run_bash_command` (kubectl get configmap) | ✅ **确认 ConfigMap 不存在** — 返回 `Error from server (NotFound): configmaps "rc-definitely-missing-configmap" not found`，这是根因的直接证据 |
| **e4** | `fetch_runbook` | ✅ 已获取 `pod-volume-mount-failed.md` 作为参考，runbook 的 **Step 3A ConfigMap/Secret volume 缺失分支** 与当前故障完全匹配 |

### 未采集证据
无。所有 critical 级别计划项均已覆盖。

### 冲突证据
无。所有工具结果与上游描述高度一致，不存在冲突。

### 根因判定
**Pod `rc-volume-missing-configmap` 卡在 ContainerCreating 的根本原因**：
Pod spec 中定义了一个 `configMap` 类型的 volume `missing-config`，引用了 ConfigMap `rc-definitely-missing-configmap`，但该 ConfigMap 在命名空间 `aiops-e2e` 中**不存在**。kubelet 反复尝试挂载均失败，导致 Pod 无法进入 Running 状态。
   ✅ [证据链采集] 完成 (11.5s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"Describe Pod rc-volume-missing-configmap in aiops-e2e to get current events and status details","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-configmap -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-volume-missing-configmap","namespace":"aiops-e2e"},"purpose":"验证Pod当前状态、Events中的FailedMount原文、volume引用关系","evidence_type":"Pod Status + Events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"Get Pod YAML to confirm volumes[].configMap.name references","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-volume-missing-configmap","namespace":"aiops-e2e"},"purpose":"确认Pod spec中volumes引用的ConfigMap名称","evidence_type":"Pod Spec Volume Reference","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"Verify ConfigMap rc-definitely-missing-configmap exists in aiops-e2e","level":"critical","tool":"run_bash_command","command":"kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e","tool_args":{},"purpose":"确认Events指向的ConfigMap是否真的不存在","evidence_type":"ConfigMap Existence Check","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"Fetch the reference runbook for VolumeMountFailed context","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-volume-mount-failed.md","tool_args":{},"purpose":"获取runbook作为诊断参考","evidence_type":"Runbook Reference","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod VolumeMountFailed / 卷挂载失败\n\n> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume\n\n## 使用原则（给模型）\n- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。\n- `kubectl describe pod` / `kubectl get events` 中的 Events 原文权重最高；先读事件原文，再按关键字选择一个最相关分支。\n- 一旦 Events 或 Pod spec 已明确命中某个分支，应停止横向扩展到无关 PVC/PV/StorageClass/CSI/NFS 分支。\n- 证据计划优先覆盖“当前已经出现的错误文本”，不要把典型原因列表全部变成 evidence_plan。\n\n## 状态识别\n- Pod 常见状态: `Pending` / `ContainerCreating`\n- Events 关键字: `FailedMount` / `FailedAttachVolume` / `MountVolume.SetUp failed`\n- 相关资源: PVC / PV / StorageClass / CSI / NFS / Secret / ConfigMap volume\n\n## 典型原因\n- PVC 未 Bound、StorageClass 不存在、PV nodeAffinity 不匹配。\n- PV/PVC 访问模式不满足，例如 RWO 被多个节点挂载、Multi-Attach error。\n- CSI/NFS/iSCSI 后端不可用、权限拒绝、挂载超时、stale file handle。\n- Secret/ConfigMap 类型的 volume 引用了不存在的对象或 key。\n- hostPath 路径不存在、类型不匹配或节点权限不足。\n- 云盘或块存储与节点可用区/实例规格不匹配，例如 volume node affinity conflict、InvalidInstanceType.NotSupportDiskCategory。\n\n## 证据优先级\n1. 最高优先级: `kubectl describe pod <pod> -n <namespace>` 或 `kubectl get events ...`，读取 Events 原文。\n2. 最高优先级: `kubectl get pod <pod> -n <namespace> -o yaml`，确认 `.spec.volumes[]` 引用的是 PVC、ConfigMap、Secret、hostPath 还是 CSI。\n3. 分支证据: 只查询 Events 原文指向的资源类型。\n\n## 分支诊断流程\n\n### Step 1: 先读 Pod Events 原文（必须优先）\n```bash\nkubectl describe pod <pod-name> -n <namespace>\nkubectl get events -n <namespace> --field-selector involvedObject.name=<pod-name> --sort-by='.lastTimestamp'\n```\n如果已看到 `configmap \"<name>\" not found`、`secret \"<name>\" not found`、`unbound immediate PersistentVolumeClaims`、`volume node affinity conflict`、`Multi-Attach error`、`NFS timeout/access denied`，直接进入对应分支。\n\n### Step 2: 读取 Pod spec 中的 volume 引用（必须优先）\n```bash\nkubectl get pod <pod-name> -n <namespace> -o yaml\n```\n关注 `.spec.volumes[]`:\n- `configMap.name` / `secret.secretName`: 进入 ConfigMap/Secret 分支。\n- `persistentVolumeClaim.claimName`: 进入 PVC/PV/StorageClass 分支。\n- `hostPath`: 进入 hostPath/节点路径分支。\n- `csi` / NFS 相关字段: 进入 CSI/NFS 分支。\n\n### Step 3A: ConfigMap/Secret volume 缺失分支\n触发条件: Events 含 `configmap \"<name>\" not found`、`secret \"<name>\" not found`，且 Pod spec 中来自 `volumes[].configMap` 或 `volumes[].secret`。\n```bash\nkubectl get configmap <name> -n <namespace>\nkubectl get secret <name> -n <namespace>\n```\n预期证据: `Error from server (NotFound)` 本身就是有效根因证据。此时不要再查 PVC、PV、StorageClass，除非 Pod spec 同时存在 PVC volume 且 Events 指向 PVC。\n\n### Step 3B: PVC/PV/StorageClass 分支\n触发条件: Events 含 `unbound immediate PersistentVolumeClaims`、`pod has unbound`、`persistentvolumeclaim ... not found`，或 Pod spec 明确使用 `persistentVolumeClaim.claimName`。\n```bash\nkubectl get pvc <pvc-name> -n <namespace>\nkubectl describe pvc <pvc-name> -n <namespace>\nkubectl get pv\nkubectl get storageclass\n```\n只有 PVC Pending/NotFound/ProvisioningFailed 时，才继续检查 PV 和 StorageClass。\n\n### Step 3C: Attach/NodeAffinity/Multi-Attach 分支\n触发条件: Events 含 `FailedAttachVolume`、`Multi-Attach error`、`volume node affinity conflict`。\n```bash\nkubectl describe pod <pod-name> -n <namespace>\nkubectl describe pv <pv-name>\nkubectl get pod <pod-name> -n <namespace> -o wide\n```\n\n### Step 3D: CSI/NFS/hostPath 分支\n触发条件: Events 含 `timeout`、`access denied`、`stale file handle`、`hostPath type check failed`、CSI driver 错误。\n```bash\nkubectl get pods -n kube-system -o wide\nkubectl describe node <node-name>\n```\n\n## 判定规则\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| Events 含 Secret/ConfigMap not found + Pod spec 来自 volumes[].secret/configMap | volume 引用的 ConfigMap/Secret 缺失 | 高 |\n| FailedMount/MountVolume + PVC 未 Bound | VolumeMountFailed | 高 |\n| FailedScheduling + unbound immediate PersistentVolumeClaims | PVC 未绑定导致 Pending，归入 VolumeMountFailed/PVC 分支 | 高 |\n| Multi-Attach error + ReadWriteOnce | 卷访问模式与调度节点冲突 | 高 |\n| PV nodeAffinity conflict | PV 节点亲和性与 Pod 调度节点不匹配 | 高 |\n| volume node affinity conflict / node(s) had volume node affinity conflict | PV/云盘可用区与调度节点不匹配 | 高 |\n| InvalidInstanceType.NotSupportDiskCategory | 云盘类型不支持当前节点实例规格 | 高 |\n| NFS timeout/access denied/stale file handle | VolumeMountFailed | 高 |\n| Secret/ConfigMap not found 且来自 volume 引用 | VolumeMountFailed；若来自 env/envFrom 则切换 ConfigError；不要再扩展 PVC 分支 | 高 |\n| hostPath path/type error | 节点路径或 hostPath 类型配置错误 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9cd06c1d785f41cc/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9cd06c1d785f41cc/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9cd06c1d785f41cc/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": false, \"stdout\": \"\", \"stderr\": \"Error from server (NotFound): configmaps \\\"rc-definitely-missing-configmap\\\" not found\\n\", \"returncode\": 1}","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/9cd06c1d785f41cc/tools/002-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9cd06c1d785f41cc/tools/002-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9cd06c1d785f41cc/tools/002-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-missing-configmap\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T03:33:04Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-missing-configmap, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"missing-config\", \"configMap\": \"rc-definitely-missing-configmap\"}\n- {\"name\": \"kube-api-access-h7lqz\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9cd06c1d785f41cc/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9cd06c1d785f41cc/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9cd06c1d785f41cc/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-missing-configmap\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  3s (x9 over 2m11s)  kubelet            MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found\n  Warning  FailedMount  8s                  kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-config], unattached volumes=[missing-config kube-api-access-h7lqz]: timed out waiting for the condition\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  missing-config:\n    Type:      ConfigMap (a volume populated by a ConfigMap)\n    Name:      rc-definitely-missing-configmap\n    Optional:  false\n  kube-api-access-h7lqz:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedMount  8s                  kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-config], unattached volumes=[missing-config kube-api-access-h7lqz]: timed out waiting for the condition\n  Warning  FailedMount  3s (x9 over 2m11s)  kubelet            MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/9cd06c1d785f41cc/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/9cd06c1d785f41cc/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/9cd06c1d785f41cc/tools/004-evidence-kubectl_describe.summary.txt"}],"llm_analysis":"所有关键工具已执行完毕，以下是证据采集结论：\n\n---\n\n## ✅ 证据采集结论\n\n### 已采集证据\n\n| # | 工具 | 关键发现 |\n|---|------|---------|\n| **e1** | `kubectl describe pod` | ✅ Pod `rc-volume-missing-configmap` 当前 status=**Pending**，容器状态 Waiting(Reason=**ContainerCreating**)。Events 中明确显示：`Warning FailedMount` — `MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found`（已出现 9 次） |\n| **e2** | `kubectl_get_yaml` | ✅ Pod spec `.spec.volumes[]` 确认：volume **missing-config** 的类型是 **ConfigMap**（`configMap.name: rc-definitely-missing-configmap`），**非 PVC/Secret/hostPath/CSI** |\n| **e3** | `run_bash_command` (kubectl get configmap) | ✅ **确认 ConfigMap 不存在** — 返回 `Error from server (NotFound): configmaps \"rc-definitely-missing-configmap\" not found`，这是根因的直接证据 |\n| **e4** | `fetch_runbook` | ✅ 已获取 `pod-volume-mount-failed.md` 作为参考，runbook 的 **Step 3A ConfigMap/Secret volume 缺失分支** 与当前故障完全匹配 |\n\n### 未采集证据\n无。所有 critical 级别计划项均已覆盖。\n\n### 冲突证据\n无。所有工具结果与上游描述高度一致，不存在冲突。\n\n### 根因判定\n**Pod `rc-volume-missing-configmap` 卡在 ContainerCreating 的根本原因**：\nPod spec 中定义了一个 `configMap` 类型的 volume `missing-config`，引用了 ConfigMap `rc-definitely-missing-configmap`，但该 ConfigMap 在命名空间 `aiops-e2e` 中**不存在**。kubelet 反复尝试挂载均失败，导致 Pod 无法进入 Running 状态。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 5/5 项，完整度 100%；实际执行工具 4 个，匹配计划 4 个，未规划证据 0 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":5,"environment_evidence_collected":5,"environment_evidence_completeness":1.0,"executed_tool_count":4,"matched_tool_count":4,"unplanned_tool_count":0,"evidence_inventory":[{"id":"e1","description":"Describe Pod rc-volume-missing-configmap in aiops-e2e to get current events and status details","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-configmap -n aiops-e2e","purpose":"验证Pod当前状态、Events中的FailedMount原文、volume引用关系","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"Get Pod YAML to confirm volumes[].configMap.name references","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml","purpose":"确认Pod spec中volumes引用的ConfigMap名称","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"Verify ConfigMap rc-definitely-missing-configmap exists in aiops-e2e","level":"critical","tool":"run_bash_command","command":"kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e","purpose":"确认Events指向的ConfigMap是否真的不存在","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"e4","description":"Fetch the reference runbook for VolumeMountFailed context","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-volume-mount-failed.md","purpose":"获取runbook作为诊断参考","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | Describe Pod rc-volume-missing-configmap in a... | `kubectl describe pod rc-volume-missing-configmap -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_yaml | Get Pod YAML to confirm volumes[].configMap.n... | `kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml` |
   | e3 | critical | ✅ | run_bash_command | Verify ConfigMap rc-definitely-missing-config... | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` |
   | e4 | reference | ✅ | fetch_runbook | Fetch the reference runbook for VolumeMountFa... | `fetch_runbook pod-volume-mount-failed.md` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (17.2s)
   📤 → 下游数据: root_cause=Pod `rc-volume-missing-configmap`（namespace: aiops-e2e）卡在 ContainerCreating 的根本原因是：其 spec.volumes[].configMap 引用的 ConfigMap `rc-definitely-missing-configmap` 在命名空间中不存在。kubelet 已重试 9 次挂载均失败（最近一次 3s 前），事件原文为 `MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found`。直接执行 `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` 返回 Error from server (NotFound)，确认 ConfigMap 对象缺失。集群中其余 59 个 Pod 均正常运行，此异常为孤立问题。
   confidence=100%
   causal_chain={"root_cause": "ConfigMap `rc-definitely-missing-configmap` 在 namespace `aiops-e2e` 中不存在", "propagation": "Pod spec 中 volume `missing-config` 的类型为 configMap，name 指向 `rc-definitely-missing-configmap`，且 Optional=false（非可选）→ kubelet 在 Pod 调度到 node1 后尝试挂载该 ConfigMap volume → ConfigMap 对象不存在 → kubelet 返回 MountVolume.SetUp failed → Pod 无法完成容器创建，卡在 ContainerCreating", "direct_cause": "Pod volume `missing-config` 引用了不存在的 ConfigMap 对象 `rc-definitely-missing-configmap`", "manifestation": "Pod `rc-volume-missing-configmap` 状态为 Pending/ContainerCreating，kubectl describe 持续输出 FailedMount 事件"}
   rca_analysis={"phenomenon": "Pod `rc-volume-missing-configmap`（namespace: aiops-e2e）当前状态为 Pending / ContainerCreating，异常类型 VolumeMountFailed。kubelet 事件持续报告 FailedMount 错误。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod 当前 status=Pending，Events 显示 FailedMount: configmap \"rc-definitely-missing-configmap\" not found（x9 次）", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml", "content": "Pod spec volumes[] 中 volume missing-config 类型为 ConfigMap，引用名 rc-definitely-missing-configmap，非 PVC/Secret/hostPath", "reliability": "高"}, {"id": "e3", "source": "run_bash_command (kubectl get configmap)", "content": "Error from server (NotFound): configmaps \"rc-definitely-missing-configmap\" not found", "reliability": "高"}, {"id": "e4", "source": "fetch_runbook", "content": "Runbook pod-volume-mount-failed.md Step 3A: ConfigMap/Secret volume 缺失分支与当前故障完全匹配", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "集群 65 个 Pod 中仅此 1 个异常，其余 59 个 Running，无其他异常", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedMount 3s (x9 over 2m11s) kubelet MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found", "interpretation": "kubelet 明确报告挂载 volume missing-config 失败，原因是引用的 ConfigMap rc-definitely-missing-configmap 不存在。此事件已持续重试 9 次，说明问题持续存在未恢复。"}, {"evidence_id": "e2", "raw_data": "volumes: [{\"name\": \"missing-config\", \"configMap\": \"rc-definitely-missing-configmap\"}]", "interpretation": "Pod spec 确认 volume missing-config 的类型是 configMap，名称为 rc-definitely-missing-configmap，且 Optional 为 false（非可选）。这直接关联到 e1 的错误。"}, {"evidence_id": "e3", "raw_data": "Error from server (NotFound): configmaps \"rc-definitely-missing-configmap\" not found", "interpretation": "直接执行 kubectl get configmap 确认该 ConfigMap 对象在 aiops-e2e 命名空间中确实不存在。这是根因的最终确认证据。"}, {"evidence_id": "e4", "raw_data": "Runbook Step 3A: ConfigMap/Secret volume 缺失分支 - Events 含 configmap not found 且 Pod spec 来自 volumes[].configMap", "interpretation": "Runbook 明确将这一场景归类为 VolumeMountFailed，判定规则为高置信度，且建议不要再横向扩展到 PVC/PV 分支。当前分析路径符合 runbook 指导。"}, {"evidence_id": "layer_1", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59}", "interpretation": "集群中 59 个 Pod 正常运行，仅此 1 个异常 Pod，说明这是一个孤立的配置问题而非集群基础设施故障。"}], "causal_chain": {"root_cause": "ConfigMap `rc-definitely-missing-configmap` 在 namespace `aiops-e2e` 中不存在", "propagation": "Pod spec 中 volume `missing-config` 的类型为 configMap，name 指向 `rc-definitely-missing-configmap`，且 Optional=false（非可选）→ kubelet 在 Pod 调度到 node1 后尝试挂载该 ConfigMap volume → ConfigMap 对象不存在 → kubelet 返回 MountVolume.SetUp failed → Pod 无法完成容器创建，卡在 ContainerCreating", "direct_cause": "Pod volume `missing-config` 引用了不存在的 ConfigMap 对象 `rc-definitely-missing-configmap`", "manifestation": "Pod `rc-volume-missing-configmap` 状态为 Pending/ContainerCreating，kubectl describe 持续输出 FailedMount 事件"}, "root_cause": "Pod `rc-volume-missing-configmap`（namespace: aiops-e2e）卡在 ContainerCreating 的根本原因是：其 spec.volumes[].configMap 引用的 ConfigMap `rc-definitely-missing-configmap` 在命名空间中不存在。kubelet 已重试 9 次挂载均失败（最近一次 3s 前），事件原文为 `MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found`。直接执行 `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` 返回 Error from server (NotFound)，确认 ConfigMap 对象缺失。集群中其余 59 个 Pod 均正常运行，此异常为孤立问题。", "root_cause_summary": "Pod `rc-volume-missing-configmap`（namespace: aiops-e2e）卡在 ContainerCreating 的根本原因是：其 spec.volumes[].configMap 引用的 ConfigMap `rc-definitely-missing-configmap` 在命名空间中不存在。kubelet 已重试 9 次挂载均失败（最近一次 3s 前），事件原文为 `MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found`。直接执行 `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` 返回 Error from server (NotFound)，确认 ConfigMap 对象缺失。集群中其余 59 个 Pod 均正常运行，此异常为孤立问题。", "confidence": 1.0, "confidence_reason": "具备三条直接证据形成完整因果链：(1) Pod Events 明确显示 ConfigMap not found 错误，(2) Pod YAML 确认 volume 引用该 ConfigMap，(3) kubectl get configmap 直接返回 NotFound 错误。证据之间无冲突，runbook 判定规则将此场景标记为高置信度根因。置信度 1.0。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [{"cause": "PVC/PV 绑定问题", "probability": "low", "reason": "Pod spec 中 volumes[] 类型为 configMap，非 persistentVolumeClaim，且 Events 未指向 PVC 相关错误，已排除"}, {"cause": "CSI/NFS 驱动或后端问题", "probability": "low", "reason": "Pod volume 类型为 ConfigMap（kubelet 本地卷），不涉及 CSI/NFS，已排除"}, {"cause": "节点磁盘或权限问题", "probability": "low", "reason": "Events 明确指出是 ConfigMap not found，而非权限或磁盘错误，已排除"}, {"cause": "Secret volume 缺失", "probability": "low", "reason": "Pod spec 中 volume 类型明确为 configMap 而非 secret，已排除"}], "limitations": "无。所有关键证据均已采集，因果链完整清晰。", "llm_raw_analysis": "## 证据清点\\n共采集 6 条证据：e1 (kubectl_describe)、e2 (kubectl_get_yaml)、e3 (kubectl get configmap 直接验证)、e4 (fetch_runbook)、layer_1 (集群整体状态)、layer_2 (上游验证)。\\n\\n## 逐条分析\\n- e1: Pod Events 明确指向 ConfigMap 缺失，是直接的故障表象证据\\n- e2: Pod spec 确认 volume 类型和名称，将表象与根本原因关联\\n- e3: 直接验证 ConfigMap 不存在，是根因的确认证据\\n- e4: Runbook 指导确认此场景归属和诊断路径正确\\n- layer_1: 集群其余 Pod 正常，排除集群基础设施故障\\n\\n## 关联分析\\ne1→e2→e3 形成完整因果链：e1 报告 ConfigMap 不存在 → e2 确认 Pod 确实引用该 ConfigMap → e3 直接确认 ConfigMap 确实不存在。三条证据相互印证，无冲突。\\n\\n## 因果链\\n根因: ConfigMap 对象缺失 → 直\n... 截断，原始 644 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod `rc-volume-missing-configmap`（namespace: aiops-e2e）卡在 ContainerCreating 的根本原因是：其 spec.volumes[].configMap 引用的 ConfigMap `rc-definitely-missing-con...
   置信度: 100%
   🔗 因果链:
     根本原因: ConfigMap `rc-definitely-missing-configmap` 在 namespace `aiops-e2e` 中不存在
     传导机制: Pod spec 中 volume `missing-config` 的类型为 configMap，name 指向 `rc-definitely-missing-configmap`，且 Optional=false（非可选）→ kubelet 在 Pod 调度到 node1 后尝试挂载该 ConfigMap volume → ConfigMap 对象不存在 → kubelet 返回 MountVolume.SetUp failed → Pod 无法完成容器创建，卡在 ContainerCreating
     最终表现: Pod `rc-volume-missing-configmap` 状态为 Pending/ContainerCreating，kubectl describe 持续输出 FailedMount 事件


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (17.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5586 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 1.9s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为一名资深 K8s 诊断报告专家，我将根据您提供的三阶段分析结果，为您生成一份详尽、完整的诊断报告。

---
## 📊 集群状态总览

根据全面诊断，您的集群整体运行平稳，**65个Pod中有59个正常运行**。但**存在1个活跃的异常Pod**，该问题不影响集群核心功能，但需要及时修复。具体问题摘要如下：

-   **核心问题**：Pod `rc-volume-missing-configmap` 由于无法挂载一个不存在的 ConfigMap 卷，卡在 `ContainerCreating` 状态。
-   **影响范围**：该问题为**孤立异常**，仅影响此单一 Pod，不会波及集群中其他运行正常的服务。
-   **严重程度**：低（L0级），不构成集群级故障，但可能影响依赖此 Pod 的业务。

---
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ContainerCreating / Pending |
| **兼容归因层** | L0 - 存储/卷挂载层 |
| **问题分类** | VolumeMountFailed (ConfigMap 卷挂载失败) |
| **置信度** | 高 (100%) |
| **证据完整度** | 3/3 (100%) |
---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-volume-missing-configmap` |
| Namespace | `aiops-e2e` |
| Node | `node1` |
| 错误信息 | `MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found` |
---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 & 事件 | `kubectl describe pod rc-volume-missing-configmap -n aiops-e2e` | `status: Pending`；`Warning FailedMount 3s (x9 over 2m11s) kubelet MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found`；`Reason: ContainerCreating` | Pod 卡在 Pending/ContainerCreating 状态，kubelet 持续报告 ConfigMap 未找到 |
| 2 | Pod YAML 配置 | `kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml` | `volumes[].configMap.name: rc-definitely-missing-configmap`；`finalizers: <none>`；`terminationGracePeriodSeconds: 30` | Pod spec 明确引用了名为 `rc-definitely-missing-configmap` 的 ConfigMap 作为卷。排除 finalizer 未清理的可能性。 |
| 3 | ConfigMap 存在性 | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` | 返回 `Error from server (NotFound): configmaps "rc-definitely-missing-configmap" not found` | **核心证据**：ConfigMap 对象在命名空间中确实不存在。 |
| 4 | 集群上下文 | `kubectl get pod -A` | 共 65 个 Pod，其中 59 个 Running，仅此 1 个异常 | 集群中其他 Pod 均正常运行，确认问题为孤立事件。 |
### 证据关联分析
-   **证据 #1 + #3 印证**：`kubectl describe` 输出的 `FailedMount` 事件错误文本 (`configmap "rc-definitely-missing-configmap" not found`) 与 `kubectl get configmap` 返回的 `NotFound` 错误**完全一致**，强有力地证实了根因。
-   **证据链**：Pod YAML 配置 (证据 #2) 要求挂载一个名为 `rc-definitely-missing-configmap` 的 ConfigMap → 该 ConfigMap 在集群中不存在 (证据 #3) → kubelet 无法完成挂载 (证据 #1) → Pod 无法启动 (证据 #1)。
### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | - | 所有关键证据均已采集，因果链完整 |
---
## 🎯 根因分析
### 因果链
```
┌──────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                             │
│ ConfigMap 对象 `rc-definitely-missing-configmap` 在 `aiops-e2e`      │
│ 命名空间中不存在。                                                    │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                             │
│ Pod spec 中 volume `missing-config` 的 type 为 configMap，            │
│ name 指向了 `rc-definitely-missing-configmap`。                       │
│ kubelet 在 pod 调度到 node1 后，尝试挂载该 volume → 发现 ConfigMap     │
│ 对象不存在 → 持续重试并报错 `MountVolume.SetUp failed`。               │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                             │
│ Pod 的 volume “missing-config” 引用了不存在的 ConfigMap 对象，         │
│ 导致挂载失败。                                                        │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                         │
│ Pod `rc-volume-missing-configmap` 状态为 Pending/ContainerCreating，  │
│ 持续输出 `FailedMount` 事件。                                         │
└──────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #1 (FailedMount 事件)、#2 (Pod YAML 配置) 和 #3 (ConfigMap 不存在)，问题的根本原因是**Pod `rc-volume-missing-configmap` 的 spec 中，volume `missing-config` 引用的 ConfigMap 对象 `rc-definitely-missing-configmap` 在 `aiops-e2e` 命名空间中不存在**。这导致 kubelet 无法完成挂载，Pod 卡在 `ContainerCreating` 状态无法运行。

**置信度**：高 (100%)
- ✅ Events 和 ConfigMap 查询结果直接指向同一个不存在的对象名，证据确凿。
- ✅ 已排除 `finalizer` 等其他可能性 (证据 #2)。
- ✅ 集群中其余 59 个 Pod 正常运行，确认问题为孤立异常。
---
## 🛠️ 修复建议
### 立即执行（按优先级排序）

**1. [优先] 创建缺失的 ConfigMap**
Pod 引用了 ConfigMap，但该 ConfigMap 本身可能包含一些空数据。最简单的修复方式是创建一个空内容的 ConfigMap 使 Pod 能启动成功。

```bash
kubectl create configmap rc-definitely-missing-configmap -n aiops-e2e --from-literal=key=value
```
*依据*：根因是 ConfigMap 缺失。创建后 Pod 应能自动感知并启动。
*注意*：如果应用期望 ConfigMap 中有特定 key，请将 `--from-literal=key=value` 替换为真实配置。

**2. [备选] 删除/修正不正确的 Pod**
如果此 Pod 是测试或误创建的，可以直接删除它，或修正其 YAML 文件中的 volume 引用。

```bash
# 删除Pod
kubectl delete pod rc-volume-missing-configmap -n aiops-e2e
```
*依据*：移除问题源头，避免警报噪音。
---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 ConfigMap 存在 | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` | 返回 ConfigMap 的详细信息 |
| 2. 确认 Pod 运行 | `kubectl get pod rc-volume-missing-configmap -n aiops-e2e` | STATUS 从 `ContainerCreating` 变为 `Running`，READY 从 `0/1` 变为 `1/1` |
| 3. 检查 Pod 事件 | `kubectl describe pod rc-volume-missing-configmap -n aiops-e2e` | 不再出现 `FailedMount` 的 Warning 事件 |
---
## ⚠️ 注意事项
- 如果创建 ConfigMap 后 Pod 仍未恢复，请检查新创建的 ConfigMap 内部 key 是否符合 Pod 内应用的预期。
- 如果 Pod 不需要该 ConfigMap，建议直接删除该 Pod 及其相关资源，以保持集群资源整洁。

---

## 📊 性能统计

├─ 总耗时: 1.0m
├─ 问题定位: 15.8s (26%) ✅
├─ 证据链采集: 11.5s (19%) ✅
├─ 根因分析: 17.2s (28%) ✅
├─ 汇总总结: 17.3s (28%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 7 次
```

📋 诊断追踪

- **核心 Runbook**: pod-volume-mount-failed
- **参考 Runbook**: pod-volume-mount-failed
- **工具调用**: 7 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
