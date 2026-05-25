======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 563f99c728a444b4]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先做一个全局 Pod 状态扫描，看看当前集群中所有 Pod 的状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59}
NAMESPACE         NAME                                                READY   STATUS              RESTARTS       A
   💭 [问题定位] 发现有一个异常 Pod。让我查看它的详细信息。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-volume-missing-configmap   0/1     ContainerCreating   0       
   💭 [问题定位] 这个 Pod 带有 `pod_abnormal_type=VolumeMountFailed` 标签，让我进一步查看它的详情和事件。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-missing-configmap
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  86s (x18 over 21m)  kubelet            MountVolume.SetU
   💭 [问题定位] 现在让我获取对应的 runbook 来确认诊断方向。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] 好的，现在我已经掌握了所有信息。让我输出诊断结果。

---

## 🔍 集群 Pod 异常诊断

### 全局扫描结果
在集群 **65 个 Pod** 中，**59 个 Running 正常**，发现 **1 个异常 Pod**。

---

### 异常 Pod 清单

| 命名空间 | Pod 名称 | 状态 | 就绪 |
|---------|---------|------|------|
| `aiops-e2e` | `rc-volume-missing-configmap` | **ContainerCreating (Pending)** | 0/1 |

---

### 详细分析

**异常 Pod：`rc-volume-missing-configmap` (aiops-e2e)**

- **状态**：ContainerCreating（卡在 Pending）
- **节点**：node1 (10.2.0.49)
- **关键 Events（核心证据）**：
  ```
  MountVolume.SetUp failed for volume "missing-config" :
  configmap "rc-definitely-missing-configmap" not found
  ```
- **Volume 配置**：Pod 的 `.spec.volumes` 中引用了名为 `missing-config` 的 ConfigMap 卷，对应 ConfigMap 名为 `rc-definitely-missing-configmap`，且 `optional: false`（非可选）。
- **根本原因**：Pod 挂载的 ConfigMap `rc-definitely-missing-configmap` **不存在于 `aiops-e2e` 命名空间中**，导致 kubelet 无法挂载卷，Pod 卡在 ContainerCreating。

---

### 诊断输出

| 字段 | 值 |
|------|-----|
| **layer** | `L0` |
| **derived_layer** | `L0` |
| **layers** | `["L0"]` |
| **layer_name** | `VolumeMountFailed - ConfigMap 缺失` |
| **confidence** | `高` |
| **pod_status_keyword** | `ContainerCreating` |
| **pod_abnormal_type** | `VolumeMountFailed` |
| **status_category** | `storage_volume` |
| **abnormal_pods** | `[{"namespace": "aiops-e2e", "name": "rc-volume-missing-configmap", "status": "ContainerCreating"}]` |
| **abnormal_groups** | `{"VolumeMountFailed": ["aiops-e2e/rc-volume-missing-configmap"]}` |
| **key_entities** | `Pod: rc-volume-missing-configmap`, `ConfigMap: rc-definitely-missing-configmap (不存在)`, `Node: node1` |
| **possible_scenarios** | `ConfigMap "rc-definitely-missing-configmap" 未在 aiops-e2e 命名空间中创建；或者拼写错误；或者已被删除。由于 optional=false，卷挂载必须成功，缺失即阻塞 Pod 启动。` |

---

### 审查方向建议（交给下游 evidence）

1. **确认 ConfigMap 是否存在**：`kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e`
2. **如不存在**：创建该 ConfigMap，或修正 Pod volume 引用为正确的 ConfigMap 名称
3. **如存在但在其他命名空间**：ConfigMap 卷只能引用同命名空间的对象，需在 `aiops-e2e` 中创建
   ✅ [问题定位] 完成 (20.8s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[{'scenario': 'ConfigMap 不存在', 'probability': '高', 'reason': "Events 明确显示 configmap 'rc-definitely-missing-configmap' not found，且 Pod spec 中 volumes[].configMap.name 引用此名称，optional=false"}, {'scenario': 'ConfigMap 拼写错误', 'probability': '中', 'reason': '引用的 ConfigMap 名称可能拼写有误或被误删除'}, {'scenario': 'ConfigMap 在别的命名空间', 'probability': '低', 'reason': 'ConfigMap 卷只能引用同命名空间对象，若在其他命名空间则无法挂载'}]
   entities=[{"type": "Pod", "name": "rc-volume-missing-configmap", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-definitely-missing-configmap", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}]
   reasoning=集群中存在1个异常Pod rc-volume-missing-configmap (aiops-e2e)，状态为ContainerCreating/Pending。kubectl describe 显示关键事件: MountVolume.SetUp failed for volume "missing-config": configmap "rc-definitely-missing-configmap" not found。Pod volumes 引用了一个不存在的ConfigMap且optional=false，导致kubelet无法挂载卷，Pod卡在ContainerCreating。该异常属于卷挂载失败(VolumeMountFailed)，归类为L0层(storage_volume)。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "VolumeMountFailed - ConfigMap 缺失", "confidence": 0.95, "reasoning": "集群中存在1个异常Pod rc-volume-missing-configmap (aiops-e2e)，状态为ContainerCreating/Pending。kubectl describe 显示关键事件: MountVolume.SetUp failed for volume \"missing-config\": configmap \"rc-definitely-missing-configmap\" not found。Pod volumes 引用了一个不存在的ConfigMap且optional=false，导致kubelet无法挂载卷，Pod卡在ContainerCreating。该异常属于卷挂载失败(VolumeMountFailed)，归类为L0层(storage_volume)。", "abnormal_pods": [{"name": "rc-volume-missing-configmap", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "Pod", "name": "rc-volume-missing-configmap", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-definitely-missing-configmap", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}], "possible_scenarios": [{"scenario": "ConfigMap 不存在", "probability": "高", "reason": "Events 明确显示 configmap 'rc-definitely-missing-configmap' not found，且 Pod spec 中 volumes[].configMap.name 引用此名称，optional=false"}, {"scenario": "ConfigMap 拼写错误", "probability": "中", "reason": "引用的 ConfigMap 名称可能拼写有误或被误删除"}, {"scenario": "ConfigMap 在别的命名空间", "probability": "低", "reason": "ConfigMap 卷只能引用同命名空间对象，若在其他命名空间则无法挂载"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-configmap"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-configmap"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-volume-missing-configmap                         0/1     ContainerCreating   0              21m     <none>           node1    <none>           <none>            app=rc-volume-missing-configmap,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/563f99c728a444b4/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/563f99c728a444b4/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/563f99c728a444b4/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来直接执行既有 evidence_plan 中的关键工具。先并行执行几个独立的 critical 级工具调用。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-volume-missing-configmap
namespace: aiops-e2e
creationTimestamp: 2026-05-21T03:33:04Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizer
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=199 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide configmap rc-definitely-missing-configmap -n aiops-e2e
Error from server (NotFound): configma
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-missing-configmap
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  111s (x18 over 22m)  kubelet            MountVolume.Set
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
111s (x18 over 22m)   Warning   FailedMount   Pod/rc-volume-missing-configmap   MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-config
   💭 [证据链采集] 所有四个关键工具都已成功执行，以下是证据采集结论：

---

## ✅ 已采集证据

### 1️⃣ ev-pod-describe (critical) ✅
**Pod 当前状态**：`Pending`，容器 `State: Waiting (Reason: ContainerCreating)`
**核心事件**：
- `Warning FailedMount` — `MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found`（x18 次，持续 22 分钟）
- `Warning FailedMount` — `Unable to attach or mount volumes: timed out waiting for the condition`（x9 次）

### 2️⃣ ev-pod-yaml (critical) ✅
**Volume 定义确认**：
```yaml
volumes:
  - name: missing-config
    configMap:
      name: rc-definitely-missing-configmap
      optional: false
```
- `optional: false` — 明确为非可选挂载，ConfigMap 缺失直接阻塞 Pod 启动
- Pod 所在节点：`node1`，无 Finalizer 卡住，无 deletionTimestamp

### 3️⃣ ev-configmap-notfound (critical) ✅
**命令返回**：`Error from server (NotFound): configmaps "rc-definitely-missing-configmap" not found`
→ ConfigMap **确实不存在**，这是根因证据。

### 4️⃣ ev-pod-events (important) ✅
事件时间线清晰：Pod 创建 22 分钟内，FailedMount 事件持续重复（x18 + x9），kubelet 反复尝试挂载 ConfigMap volume 均失败。

---

## ❌ 未采集 / 冲突证据
- 无冲突证据 — 所有工具结果与上游描述完全一致。

## 📋 最终诊断结论
**根因**：Pod `rc-volume-missing-configmap` 的 volume `missing-config` 引用了 ConfigMap `rc-definitely-missing-configmap`，且 `optional=false`。但该 ConfigMap **在 aiops-e2e 命名空间中不存在**，导致 kubelet 无法挂载卷，Pod 持续卡在 `Pending/ContainerCreating`。这是明确的 **L0 层 ConfigMap volume 缺失故障**。
   ✅ [证据链采集] 完成 (14.1s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"ev-pod-describe","description":"kubectl describe pod rc-volume-missing-configmap -n aiops-e2e 验证 FailedMount 事件和当前状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-configmap -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-volume-missing-configmap","namespace":"aiops-e2e"},"purpose":"验证 FailedMount 事件原文：MountVolume.SetUp failed for volume 'missing-config': configmap 'rc-definitely-missing-configmap' not found","evidence_type":"events","target_scope":"pod","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"ev-pod-yaml","description":"kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml 确认 spec.volumes[].configMap.name 引用","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-volume-missing-configmap","namespace":"aiops-e2e"},"purpose":"验证 volumes[].configMap.name 是否为 'rc-definitely-missing-configmap' 且 optional=false","evidence_type":"configuration","target_scope":"pod","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"ev-configmap-notfound","description":"验证 ConfigMap 'rc-definitely-missing-configmap' 在 ns aiops-e2e 中不存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e","tool_args":{"kind":"ConfigMap","name":"rc-definitely-missing-configmap","namespace":"aiops-e2e"},"purpose":"验证 ConfigMap 确实不存在，返回 NotFound 即为根因证据","evidence_type":"resource_existence","target_scope":"configmap","acceptable_tools":["kubectl_get_by_name"],"counts_for_completeness":true},{"id":"ev-pod-events","description":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-missing-configmap 获取完整事件时间线","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-missing-configmap --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-volume-missing-configmap"},"purpose":"获取 FailedMount 事件完整时间线和重复次数","evidence_type":"events","target_scope":"pod","acceptable_tools":["kubectl_events"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-missing-configmap\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T03:33:04Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-missing-configmap, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"missing-config\", \"configMap\": \"rc-definitely-missing-configmap\"}\n- {\"name\": \"kube-api-access-h7lqz\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/563f99c728a444b4/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/563f99c728a444b4/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/563f99c728a444b4/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=199 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide configmap rc-definitely-missing-configmap -n aiops-e2e\nError from server (NotFound): configmaps \"rc-definitely-missing-configmap\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/563f99c728a444b4/tools/002-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/563f99c728a444b4/tools/002-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/563f99c728a444b4/tools/002-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-missing-configmap\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  111s (x18 over 22m)  kubelet            MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found\n  Warning  FailedMount  2m10s (x9 over 20m)  kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-config], unattached volumes=[missing-config kube-api-access-h7lqz]: timed out waiting for the condition\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  missing-config:\n    Type:      ConfigMap (a volume populated by a ConfigMap)\n    Name:      rc-definitely-missing-configmap\n    Optional:  false\n  kube-api-access-h7lqz:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedMount  2m10s (x9 over 20m)  kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-config], unattached volumes=[missing-config kube-api-access-h7lqz]: timed out waiting for the condition\n  Warning  FailedMount  111s (x18 over 22m)  kubelet            MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/563f99c728a444b4/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/563f99c728a444b4/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/563f99c728a444b4/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n111s (x18 over 22m)   Warning   FailedMount   Pod/rc-volume-missing-configmap   MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found\n2m10s (x9 over 20m)   Warning   FailedMount   Pod/rc-volume-missing-configmap   Unable to attach or mount volumes: unmounted volumes=[missing-config], unattached volumes=[missing-config kube-api-access-h7lqz]: timed out waiting for the condition","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/563f99c728a444b4/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/563f99c728a444b4/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/563f99c728a444b4/tools/004-evidence-kubectl_events.summary.txt"}],"llm_analysis":"所有四个关键工具都已成功执行，以下是证据采集结论：\n\n---\n\n## ✅ 已采集证据\n\n### 1️⃣ ev-pod-describe (critical) ✅\n**Pod 当前状态**：`Pending`，容器 `State: Waiting (Reason: ContainerCreating)`\n**核心事件**：\n- `Warning FailedMount` — `MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found`（x18 次，持续 22 分钟）\n- `Warning FailedMount` — `Unable to attach or mount volumes: timed out waiting for the condition`（x9 次）\n\n### 2️⃣ ev-pod-yaml (critical) ✅\n**Volume 定义确认**：\n```yaml\nvolumes:\n  - name: missing-config\n    configMap:\n      name: rc-definitely-missing-configmap\n      optional: false\n```\n- `optional: false` — 明确为非可选挂载，ConfigMap 缺失直接阻塞 Pod 启动\n- Pod 所在节点：`node1`，无 Finalizer 卡住，无 deletionTimestamp\n\n### 3️⃣ ev-configmap-notfound (critical) ✅\n**命令返回**：`Error from server (NotFound): configmaps \"rc-definitely-missing-configmap\" not found`\n→ ConfigMap **确实不存在**，这是根因证据。\n\n### 4️⃣ ev-pod-events (important) ✅\n事件时间线清晰：Pod 创建 22 分钟内，FailedMount 事件持续重复（x18 + x9），kubelet 反复尝试挂载 ConfigMap volume 均失败。\n\n---\n\n## ❌ 未采集 / 冲突证据\n- 无冲突证据 — 所有工具结果与上游描述完全一致。\n\n## 📋 最终诊断结论\n**根因**：Pod `rc-volume-missing-configmap` 的 volume `missing-config` 引用了 ConfigMap `rc-definitely-missing-configmap`，且 `optional=false`。但该 ConfigMap **在 aiops-e2e 命名空间中不存在**，导致 kubelet 无法挂载卷，Pod 持续卡在 `Pending/ContainerCreating`。这是明确的 **L0 层 ConfigMap volume 缺失故障**。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 7 个，匹配计划 4 个，未规划证据 3 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":7,"matched_tool_count":4,"unplanned_tool_count":3,"evidence_inventory":[{"id":"ev-pod-describe","description":"kubectl describe pod rc-volume-missing-configmap -n aiops-e2e 验证 FailedMount 事件和当前状态","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-configmap -n aiops-e2e","purpose":"验证 FailedMount 事件原文：MountVolume.SetUp failed for volume 'missing-config': configmap 'rc-definitely-missing-configmap' not found","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-pod-yaml","description":"kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml 确认 spec.volumes[].configMap.name 引用","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml","purpose":"验证 volumes[].configMap.name 是否为 'rc-definitely-missing-configmap' 且 optional=false","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-configmap-notfound","description":"验证 ConfigMap 'rc-definitely-missing-configmap' 在 ns aiops-e2e 中不存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e","purpose":"验证 ConfigMap 确实不存在，返回 NotFound 即为根因证据","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"ev-pod-events","description":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-missing-configmap 获取完整事件时间线","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-missing-configmap --sort-by='.lastTimestamp'","purpose":"获取 FailedMount 事件完整时间线和重复次数","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | ev-pod-describe | critical | ✅ | kubectl_describe | kubectl describe pod rc-volume-missing-config... | `kubectl describe pod rc-volume-missing-configmap -n aiops-e2e` |
   | ev-pod-yaml | critical | ✅ | kubectl_get_yaml | kubectl get pod rc-volume-missing-configmap -... | `kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml` |
   | ev-configmap-... | critical | ✅ | kubectl_get_by_name | 验证 ConfigMap 'rc-definitely-missing-configmap... | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` |
   | ev-pod-events | important | ✅ | kubectl_events | kubectl get events -n aiops-e2e --field-selec... | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volum...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (16.8s)
   📤 → 下游数据: root_cause=Pod rc-volume-missing-configmap (aiops-e2e) 因 volume 挂载失败卡在 Pending/ContainerCreating。kubectl describe 确认 kubelet 报错 'MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found'（x18 次，持续 22 分钟）。Pod YAML 确认 volumes[].configMap.name=rc-definitely-missing-configmap 且 optional=false。kubectl get configmap 返回 'NotFound'，确认该 ConfigMap 在 aiops-e2e 命名空间中不存在。全集群 65 Pod 中仅此 1 个异常，其余 59 个 Running 正常，无其他并发故障。
   confidence=98%
   causal_chain={"root_cause": "ConfigMap 'rc-definitely-missing-configmap' 在命名空间 aiops-e2e 中不存在（可能被删除或拼写错误）。", "propagation": "Pod spec volumes[].configMap.name 引用该不存在的 ConfigMap 且 optional=false → kubelet 在节点 node1 上尝试挂载卷时无法找到该 ConfigMap → MountVolume.SetUp failed → Pod 无法完成容器创建。", "direct_cause": "Volume 'missing-config' 的 ConfigMap 引用 'rc-definitely-missing-configmap' 在 aiops-e2e 命名空间中不存在，且 optional=false。", "manifestation": "Pod rc-volume-missing-configmap 卡在 Pending/ContainerCreating 状态，kubelet 持续报 Warning FailedMount 事件，22 分钟内已重试 18 次仍失败。"}
   rca_analysis={"phenomenon": "集群 aiops-e2e 命名空间中 Pod rc-volume-missing-configmap 处于 Pending/ContainerCreating 状态，容器 Waiting(Reason=ContainerCreating)，已持续 22 分钟。kubelet 反复报 FailedMount 事件：MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found。", "evidence_inventory": [{"id": "ev-pod-describe", "source": "kubectl_describe", "content": "Pod 状态 Pending，容器 Waiting(ContainerCreating)。FailedMount 事件显示 configmap not found，x18 次持续 22 分钟。", "reliability": "高"}, {"id": "ev-pod-yaml", "source": "kubectl_get_yaml", "content": "Volume missing-config 引用 configMap.name=rc-definitely-missing-configmap，optional=false。", "reliability": "高"}, {"id": "ev-configmap-notfound", "source": "kubectl_get_by_name", "content": "kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e 返回 NotFound 错误。", "reliability": "高"}, {"id": "ev-pod-events", "source": "kubectl_events", "content": "FailedMount 事件持续 22 分钟，x18 次 configmap not found + x9 次 timed out waiting。", "reliability": "高"}, {"id": "layer-cluster-scan", "source": "kubectl_get_by_kind_in_cluster", "content": "全集群 65 Pod 中仅此 1 个异常，59 个 Running 正常。", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "ev-configmap-notfound", "raw_data": "Error from server (NotFound): configmaps \"rc-definitely-missing-configmap\" not found", "interpretation": "ConfigMap 'rc-definitely-missing-configmap' 在命名空间 aiops-e2e 中确实不存在，这是根因的直接证据。"}, {"evidence_id": "ev-pod-yaml", "raw_data": "volumes: [{\"name\": \"missing-config\", \"configMap\": \"rc-definitely-missing-configmap\"}], optional: false", "interpretation": "Pod spec 明确引用该 ConfigMap 作为卷，且 optional=false，意味着 ConfigMap 必须存在，缺失直接阻塞 Pod 启动。"}, {"evidence_id": "ev-pod-describe", "raw_data": "Warning FailedMount 111s (x18 over 22m) MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found", "interpretation": "kubelet 在节点 node1 上反复尝试挂载该 ConfigMap 卷均失败，Pod 因此无法进入 Running 状态。"}, {"evidence_id": "ev-pod-events", "raw_data": "111s (x18 over 22m) Warning FailedMount + 2m10s (x9 over 20m) Warning FailedMount timed out", "interpretation": "事件时间线显示故障持续了 22 分钟，kubelet 已重试 18 次挂载，最终超时，故障是持续性的而非瞬态。"}, {"evidence_id": "layer-cluster-scan", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59}", "interpretation": "全集群 65 个 Pod 中仅此 1 个异常，其余 59 个 Pod 均在 Running 状态，无其他并发异常，故障范围局限于此单一 Pod。"}], "causal_chain": {"root_cause": "ConfigMap 'rc-definitely-missing-configmap' 在命名空间 aiops-e2e 中不存在（可能被删除或拼写错误）。", "propagation": "Pod spec volumes[].configMap.name 引用该不存在的 ConfigMap 且 optional=false → kubelet 在节点 node1 上尝试挂载卷时无法找到该 ConfigMap → MountVolume.SetUp failed → Pod 无法完成容器创建。", "direct_cause": "Volume 'missing-config' 的 ConfigMap 引用 'rc-definitely-missing-configmap' 在 aiops-e2e 命名空间中不存在，且 optional=false。", "manifestation": "Pod rc-volume-missing-configmap 卡在 Pending/ContainerCreating 状态，kubelet 持续报 Warning FailedMount 事件，22 分钟内已重试 18 次仍失败。"}, "root_cause": "Pod rc-volume-missing-configmap (aiops-e2e) 因 volume 挂载失败卡在 Pending/ContainerCreating。kubectl describe 确认 kubelet 报错 'MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found'（x18 次，持续 22 分钟）。Pod YAML 确认 volumes[].configMap.name=rc-definitely-missing-configmap 且 optional=false。kubectl get configmap 返回 'NotFound'，确认该 ConfigMap 在 aiops-e2e 命名空间中不存在。全集群 65 Pod 中仅此 1 个异常，其余 59 个 Running 正常，无其他并发故障。", "root_cause_summary": "Pod rc-volume-missing-configmap (aiops-e2e) 因 volume 挂载失败卡在 Pending/ContainerCreating。kubectl describe 确认 kubelet 报错 'MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found'（x18 次，持续 22 分钟）。Pod YAML 确认 volumes[].configMap.name=rc-definitely-missing-configmap 且 optional=false。kubectl get configmap 返回 'NotFound'，确认该 ConfigMap 在 aiops-e2e 命名空间中不存在。全集群 65 Pod 中仅此 1 个异常，其余 59 个 Running 正常，无其他并发故障。", "confidence": 0.98, "confidence_reason": "直接证据链完整：① Pod YAML 确认 ConfigMap 引用和 optional=false → ② kubectl get configmap 确认 NotFound → ③ kubectl describe/events 确认 kubelet 持续报 FailedMount 事件。三个独立工具结果完全一致，无冲突证据，因果链清晰无跳转。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [{"cause": "ConfigMap 拼写错误", "probability": "low", "reason": "Pod YAML 中引用的名称 'rc-definitely-missing-configmap' 与 ConfigMap 实际名称不一致的可能性无法完全排除，但无论拼写错误还是被删除，根因本质相同——引用的 ConfigMap 不存在。"}, {"cause": "ConfigMap 在别的命名空间", "probability": "low", "reason": "ConfigMap 卷只能引用同命名空间对象，若在其他命名空间则无法挂载，但这与 'NotFound' 错误一致，且属于同一种根因类型——引用的 ConfigMap 在当前命名空间不可用。"}, {"cause": "kubelet 或节点问题", "probability": "low", "reason": "FailedMount 事件明确指向 ConfigMap not found 而非节点存储或网络问题，且集群中其他 59 个 Pod 在 node1 及其他节点上正常运行。"}], "limitations": "未确认 ConfigMap 是被删除还是从未创建（Event 时间线 22 分钟，Pod 创建时间 2026-05-21T03:33:04Z，可查看 archive 确认），但这不影响根因结论——ConfigMap 当前确实不存在。", "llm_raw_analysis": "## 证据清点\n共 6 条证据：critical 级 3 条（ev-pod-describe, ev-pod-yaml, ev-configmap-notfound），important 级 3 条（ev-pod-events, layer-cluster-scan, layer_2, layer_3）。\n\n## 逐条分析\n- ev-configmap-notfound：ConfigMap 确实不存在，退出码 1，NotFound 错误。\n- ev-pod-yaml：spec.volumes[0].configMap.name=rc-definitely-missing-configmap，optional=false，无 deletionTimestamp，Pod 未被删除。\n- ev-pod-describe：kubelet 在 node1 上反复挂载失败，错误信息与 ev-configmap-notfound 完全对应。\n- ev-pod-events：22 分钟内持续重试 18 次，非瞬态故障。\n- layer-cluster-scan：仅此 1 个异常 Pod，故障范围明确。\n... 截断，原始 955 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-volume-missing-configmap (aiops-e2e) 因 volume 挂载失败卡在 Pending/ContainerCreating。kubectl describe 确认 kubelet 报错 'MountVolume.SetUp failed for vol...
   置信度: 98%
   🔗 因果链:
     根本原因: ConfigMap 'rc-definitely-missing-configmap' 在命名空间 aiops-e2e 中不存在（可能被删除或拼写错误）。
     传导机制: Pod spec volumes[].configMap.name 引用该不存在的 ConfigMap 且 optional=false → kubelet 在节点 node1 上尝试挂载卷时无法找到该 ConfigMap → MountVolume.SetUp failed → Pod 无法完成容器创建。
     最终表现: Pod rc-volume-missing-configmap 卡在 Pending/ContainerCreating 状态，kubelet 持续报 Warning FailedMount 事件，22 分钟内已重试 18 次仍失败。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (20.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 7173 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 12.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，这是根据您提供的诊断数据生成的详尽诊断报告。

---
## 📊 诊断概览

**核心回答：您的集群整体健康，仅存在 1 个问题 Pod。** 在总共 65 个 Pod 中，59 个处于 `Running` 状态，运行正常。唯一的异常 Pod `rc-volume-missing-configmap` 卡在 `ContainerCreating` 状态，原因是其引用的 ConfigMap `rc-definitely-missing-configmap` 不存在。

| 项目 | 内容 |
|------|------|
| **集群状态总结** | 65 个 Pod 中，59 个运行正常 (Ready)，1 个异常 (ContainerCreating)，其余 Pod 状态正常。 |
| **Pod异常状态** | `ContainerCreating` / `Pending` |
| **兼容归因层** | L0 - storage_volume |
| **问题分类** | `VolumeMountFailed` - ConfigMap 卷挂载失败 |
| **置信度** | 高 (98%) |
| **证据完整度** | 4/4 (100%) |

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 问题 Pod | `rc-volume-missing-configmap` |
| Namespace | `aiops-e2e` |
| Node | `node1` |
| 异常状态 | `ContainerCreating` (kubectl describe 显示为 `Pending`) |
| 核心错误信息 | `MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found` |

---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态及事件 | `kubectl describe pod rc-volume-missing-configmap -n aiops-e2e` | `status: Pending`，`Warning FailedMount 111s (x18 over 22m) kubelet MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found` | 明确指示 Pod 因 ConfigMap 不存在导致卷挂载失败，事件已重复 18 次，持续 22 分钟。 |
| 2 | Pod Spec 分析 | `kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml` | `spec.volumes[].configMap.name: rc-definitely-missing-configmap`，`optional:` 未设置 (默认 false) | 确认 Pod 的 volume `missing-config` 引用的 ConfigMap 名称，且该引用是**强制**的 (optional=false)。 |
| 3 | ConfigMap 存在性验证 | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` | `Error from server (NotFound): configmaps "rc-definitely-missing-configmap" not found` | **直接确认**，该 ConfigMap 在 `aiops-e2e` 命名空间下确实**不存在**。 |
| 4 | 完整事件时间线 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-missing-configmap` | `111s (x18 over 22m) Warning FailedMount Pod/rc-volume-missing-configmap MountVolume.SetUp failed...` | 时间线证实问题自 Pod 创建后持续存在，kubelet 已重试 18 次均失败。 |
| 5 | 集群状态 | `kubectl get pods --all-namespaces` | `rows=65 abnormal=1 status_counts={'Running': 59}` | 集群中 59 个 Pod 正常运行，仅此 1 个 Pod 异常，说明问题孤立，非集群性问题。 |

### 证据关联分析
- **证据 #1 + 证据 #3 印证**：kubelet 报告“ConfigMap not found”，而 `kubectl get` 命令也返回 `NotFound`，两者完全一致，**排除误报可能**。
- **证据 #1 + 证据 #2 印证**：kubelet 报错的 ConfigMap 名称 (`rc-definitely-missing-configmap`) 与 Pod YAML 中引用的名称完全一致，**确认引用关系无误**。同时，因 `optional=false`，kubelet 无法跳过此错误，必须等待 ConfigMap 就绪。
- **证据链**：Pod 引用不存在的 ConfigMap → kubelet 无法挂载卷 → Pod 无法进入 Ready 状态 → 持续处于 Pending/ContainerCreating。
- **证据 #5**：仅此 Pod 异常，其余正常，说明非集群级别问题，如网络、kubelet 等。

### 缺失证据（如有）
无。所有关键证据（Pod 状态、事件、YAML、ConfigMap 存在性）均已采集，证据链完整。

---
## 🎯 根因分析

### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因 (Root Cause)                                                                  │
│ ConfigMap 'rc-definitely-missing-configmap' 在 'aiops-e2e' 命名空间中不存在。          │
│ (可能原因：从未创建、被误删除，或名称拼写错误)                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                       ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制 (Propagation)                                                                 │
│ 1. Pod spec 中 volume 'missing-config' 强制引用 (optional=false) 该 ConfigMap。        │
│ 2. kubelet 在调度到 node1 后，尝试创建该 volume 时，在命名空间中查找对应的 ConfigMap。│
│ 3. 因为 ConfigMap 不存在，kubelet 无法完成挂载操作。                                   │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                       ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因 (Direct Cause)                                                                 │
│ kubelet 报告 MountVolume.SetUp failed，错误信息明确指向 ConfigMap 不存在。            │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                       ↓
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象 (Manifestation)                                                            │
│ Pod 'rc-volume-missing-configmap' 卡在 'Pending' / 'ContainerCreating' 状态，          │
│ 持续报 Warning FailedMount 事件，无法提供服务。                                         │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (FailedMount 事件)、证据 #2 (YAML spec)、证据 #3 (ConfigMap NotFound) 和证据 #4 (事件时间线)，问题的根本原因是 **Pod `rc-volume-missing-configmap` 引用的 ConfigMap `rc-definitely-missing-configmap` 在 `aiops-e2e` 命名空间中不存在，且该 ConfigMap 引用被设置为 `optional: false`（默认值）**。这导致 kubelet 无法挂载卷，Pod 被阻塞在创建流程中。

**置信度**：高 (98%)
- ✅ 错误事件信息与工具观测（NotFound）**完全吻合**。
- ✅ Pod YAML 确认了引用关系和强制属性。
- ✅ 证据覆盖了 Pod 状态、事件、Spec 定义和目标资源存在性，链条完整。

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）

**1. [优先] 创建缺失的 ConfigMap**
需要创建一个名为 `rc-definitely-missing-configmap` 的 ConfigMap，内容需与 volume 期望的一致。以下是创建示例（假设需要一些通用数据，请根据实际需求修改 data 部分）。
```bash
# 创建一个空的 ConfigMap 或包含所需数据的 ConfigMap
kubectl create configmap rc-definitely-missing-configmap -n aiops-e2e --from-literal=key1=value1

# 或者，如果知道 Pod 期望的内容，也可以通过文件创建
# kubectl create configmap rc-definitely-missing-configmap -n aiops-e2e --from-file=config.properties
```
*依据*：证据 #1 和 #3 表明，只要 ConfigMap 存在并有效，kubelet 将自动挂载，Pod 会从 `Pending` 转为 `Running`。

**2. [备选] 如果不需要该卷，修改 Pod 配置**
如果该 ConfigMap 中的数据已不再需要，可以在 Pod 的 YAML 中将 `optional` 设置为 `true`，这样 kubelet 将跳过挂载失败，Pod 可以正常启动。

```bash
# 首先，获取当前 Pod 的 YAML 并导出
kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml > /tmp/pod.yaml

# 编辑 /tmp/pod.yaml ，找到 volumes 下的 missing-config 条目，添加或修改 optional: true
# ...
# volumes:
#   - name: missing-config
#     configMap:
#       name: rc-definitely-missing-configmap
#       optional: true
# ...

# 应用修改（注意：对于已经存在的 Pod，需要删除后重新创建）
kubectl delete pod rc-volume-missing-configmap -n aiops-e2e
kubectl apply -f /tmp/pod.yaml
```
**建议**：优先采用方案 1（创建 ConfigMap），因为它更符合业务逻辑。方案 2 仅在确认该 ConfigMap 数据确实无用时采用。

### 后续优化
1. **检查 ConfigMap 丢失原因**：确认该 ConfigMap 是否是被误删除，还是从未创建。如果是 CI/CD 流程的一部分，检查部署流水线是否有遗漏。
2. **规范资源管理**：在引用其他资源（如 ConfigMap, Secret, PVC）时，建议进行前置检查，避免因依赖不存在导致 Pod 启动失败。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 创建 ConfigMap | `kubectl create configmap rc-definitely-missing-configmap -n aiops-e2e --from-literal=key1=value1` | `configmap/rc-definitely-missing-configmap created` |
| 2. 确认 Pod 状态恢复 | `kubectl get pod rc-volume-missing-configmap -n aiops-e2e` | **STATUS** 列显示 `Running`，**READY** 列显示 `1/1` |
| 3. 检查 Pod 事件 | `kubectl describe pod rc-volume-missing-configmap -n aiops-e2e` | 不再有 `Warning FailedMount` 事件，Events 末尾显示正常的 `Started` 或 `Pulled` 等事件。 |
| 4. 确认错误事件消失 | `kubectl get events -n aiops-e2e --field-selector reason=FailedMount` | 返回 `No resources found in aiops-e2e namespace.` |

---
## ⚠️ 注意事项
- 修复后，Pod 会自动由 Kubernetes 控制平面重新调度并挂载，无需额外重启 Pod。
- 如果执行方案 2（修改为 `optional: true`），请确保应用可以容忍该 ConfigMap 的数据缺失，否则可能会在运行时引发新的问题（如应用崩溃、读取空配置等）。

---

## 📊 性能统计

├─ 总耗时: 1.2m
├─ 问题定位: 20.8s (29%) ✅
├─ 证据链采集: 14.1s (20%) ✅
├─ 根因分析: 16.8s (23%) ✅
├─ 汇总总结: 20.5s (28%) ✅
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
