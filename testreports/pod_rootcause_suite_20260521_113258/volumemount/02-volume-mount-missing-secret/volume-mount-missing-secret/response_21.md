======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 961c38b87d7f43de]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我先做一个全局的 Pod 状态扫描，看看当前集群中有哪些异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59}
NAMESPACE         NAME                                                READY   STATUS              RESTARTS       A
   💭 [问题定位] 发现一个异常 Pod。让我进一步查看它的详情。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-missing-secret
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  31s (x13 over 10m)     kubelet            MountVolume.SetU
   💭 [问题定位] 现在我已经掌握了完整信息。让我获取匹配的 runbook 来参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] 现在我已经掌握了所有必要信息，以下是完整的诊断分析结果。

---

## 📋 全局 Pod 扫描结果

| 总量 | 正常 Running | 异常 |
|:---:|:---:|:---:|
| 65 | 59 | **1** |

## ❌ 当前异常 Pod

| Pod | 命名空间 | 状态 | 标签 |
|:---|:---:|:---:|:---|
| **rc-volume-missing-secret** | aiops-e2e | `ContainerCreating` (实际 Pending) | `pod_abnormal_type=VolumeMountFailed` |

---

## 🔍 定位分析

### Pod 关键信息

| 字段 | 内容 |
|:---|:---|
| **状态** | Pending（容器 Waiting Reason=ContainerCreating） |
| **节点** | node1 |
| **镜像** | busybox:1.36 |
| **QoS** | BestEffort |

### 卷配置

Pod 引用了两个 Volume：

1. **missing-secret**（Secret 类型）→ 引用了 `rc-definitely-missing-secret`
2. **kube-api-access-7n89z**（Projected）→ ServiceAccount 默认注入

### Events 核心错误（最高优先级证据）

```
Warning  FailedMount  MountVolume.SetUp failed for volume "missing-secret" : 
         secret "rc-definitely-missing-secret" not found
```

**根因非常明确**：Volume `missing-secret` 引用的 Secret `rc-definitely-missing-secret` 在 `aiops-e2e` 命名空间中**不存在**。

---

## 🏷 异常分类

| 维度 | 值 |
|:---|:---|
| **pod_abnormal_type** | `VolumeMountFailed` |
| **pod_status_keyword** | `ContainerCreating` |
| **status_category** | `volume_mount` |
| **兼容层 (layer)** | **L0** |
| **派生层 (derived_layer)** | L0 |
| **所有兼容层 (layers)** | [L0] |
| **置信度** | 高 |

### 异常组 (abnormal_groups)

| 异常类型 | Pod 列表 |
|:---|:---|
| **VolumeMountFailed** | `aiops-e2e/rc-volume-missing-secret` |

### 异常 Pod 列表 (abnormal_pods)

| Namespace | Name | Status |
|:---|:---|:---|
| aiops-e2e | rc-volume-missing-secret | Pending / ContainerCreating |

---

## 🎯 可能场景

| # | 场景描述 | 可能性 |
|:---:|:---|:---:|
| 1 | **Secret 对象缺失** — `rc-definitely-missing-secret` 这个 Secret 从未创建或被误删除，导致 Pod 无法挂载该卷 | ⭐⭐⭐ 最高 |
| 2 | **命名空间错误** — Secret 被创建在了其他命名空间（如 default 或其他 ns），而 Pod 在 `aiops-e2e` 中查找不到 | ⭐⭐ |
| 3 | **Secret 名称拼写错误** — Pod 的 `volumes[].secret.secretName` 字段 `rc-definitely-missing-secret` 与实际 Secret 名称不一致 | ⭐⭐ |

---

## 📌 后续审查方向（给 evidence 节点）

1. **验证 Secret 是否存在**：`kubectl get secret rc-definitely-missing-secret -n aiops-e2e`（预期返回 NotFound）
2. **确认是未创建还是命名空间放错**：搜索全集群同名 Secret
3. **修复方向**：创建对应的 Secret，或修正 Pod 中引用的 Secret 名称

---

✅ **诊断结论**：集群当前只有一个异常 Pod `rc-volume-missing-secret`，卡在 `ContainerCreating` 状态，根因是引用的 Secret `rc-definitely-missing-secret` 不存在，归类为 **L0 - VolumeMountFailed**。
   ✅ [问题定位] 完成 (17.2s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[{'scenario': 'Secret对象缺失 — rc-definitely-missing-secret这个Secret从未创建或被误删除，导致Pod无法挂载该卷', 'probability': '高', 'reason': 'Events明确报错secret not found，kubectl describe事件原文确认'}, {'scenario': '命名空间错误 — Secret被创建在了其他命名空间，而Pod在aiops-e2e中查找不到', 'probability': '中', 'reason': 'Secret名称正确但命名空间不匹配是常见场景'}, {'scenario': 'Secret名称拼写错误 — Pod volumes[].secret.secretName字段与实际Secret名称不一致', 'probability': '中', 'reason': '配置中secretName=rc-definitely-missing-secret可能拼写错误'}]
   entities=[{"type": "Pod", "name": "rc-volume-missing-secret", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-definitely-missing-secret", "namespace": "aiops-e2e"}, {"type": "Volume", "name": "missing-secret", "namespace": "aiops-e2e"}]
   reasoning=集群中存在1个当前仍异常的Pod: aiops-e2e/rc-volume-missing-secret，状态为Pending/ContainerCreating。kubectl describe 事件明确显示: MountVolume.SetUp failed for volume "missing-secret" : secret "rc-definitely-missing-secret" not found。根因是Pod引用了不存在的Secret，属于卷挂载失败。根据五层模型，VolumeMountFailed归因于L0（磁盘/存储/驱逐层）。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "VolumeMountFailed", "confidence": 0.95, "reasoning": "集群中存在1个当前仍异常的Pod: aiops-e2e/rc-volume-missing-secret，状态为Pending/ContainerCreating。kubectl describe 事件明确显示: MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found。根因是Pod引用了不存在的Secret，属于卷挂载失败。根据五层模型，VolumeMountFailed归因于L0（磁盘/存储/驱逐层）。", "abnormal_pods": [{"name": "rc-volume-missing-secret", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "volume_mount", "key_entities": [{"type": "Pod", "name": "rc-volume-missing-secret", "namespace": "aiops-e2e"}, {"type": "Secret", "name": "rc-definitely-missing-secret", "namespace": "aiops-e2e"}, {"type": "Volume", "name": "missing-secret", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Secret对象缺失 — rc-definitely-missing-secret这个Secret从未创建或被误删除，导致Pod无法挂载该卷", "probability": "高", "reason": "Events明确报错secret not found，kubectl describe事件原文确认"}, {"scenario": "命名空间错误 — Secret被创建在了其他命名空间，而Pod在aiops-e2e中查找不到", "probability": "中", "reason": "Secret名称正确但命名空间不匹配是常见场景"}, {"scenario": "Secret名称拼写错误 — Pod volumes[].secret.secretName字段与实际Secret名称不一致", "probability": "中", "reason": "配置中secretName=rc-definitely-missing-secret可能拼写错误"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-secret"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-secret"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-volume-missing-secret                            0/1     ContainerCreating   0              10m     <none>           node1    <none>           <none>            app=rc-volume-missing-secret,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/961c38b87d7f43de/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/961c38b87d7f43de/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/961c38b87d7f43de/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来执行既有 evidence_plan 中的关键工具。先从最高优先级的开始：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-missing-secret
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  53s (x13 over 11m)  kubelet            MountVolume.SetUp f
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-volume-missing-secret
namespace: aiops-e2e
creationTimestamp: 2026-05-21T04:01:35Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: 
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=187 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide secret rc-definitely-missing-secret -n aiops-e2e
Error from server (NotFound): secrets "rc-de
   💭 [证据链采集] 关键证据已经获取。现在执行 e4 和 e5 计划项：
   💭 [证据链采集] 调用工具: kubectl_find_resource
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
55s (x13 over 11m)   Warning   FailedMount   Pod/rc-volume-missing-secret   MountVolume.SetUp failed for volume "missing-secret" : secret "rc-definitely-missing-secret" not f
   💭 [证据链采集] 工具结果: kubectl_find_resource (success)
      📄 kubectl_find_resource 输出摘要: raw_chars=110 lines=2
Command failed (exit 1):
kubectl get -A --show-labels -o wide secret | grep -i 'rc-definitely-missing-secret'
   💭 [证据链采集] 所有证据已采集完成，下面给出结论。

---

## 证据采集结论

### ✅ 已采集证据

| # | 工具 | 关键发现 |
|---|------|---------|
| **e1** | `kubectl describe pod` | Pod `rc-volume-missing-secret` 状态 **Pending**，Events 明确报错：`MountVolume.SetUp failed for volume "missing-secret" : secret "rc-definitely-missing-secret" not found`（已持续 11 分钟，重复 13 次） |
| **e2** | `kubectl get pod -o yaml` | 卷 `missing-secret` 的 **Type=Secret**，**SecretName=rc-definitely-missing-secret**，且 **Optional=false**（非可选卷，缺失将阻止 Pod 启动） |
| **e3** | `kubectl get secret` | **Error from server (NotFound): secrets "rc-definitely-missing-secret" not found** — Secret 在 `aiops-e2e` 命名空间不存在 |
| **e4** | `kubectl get secret -A \| grep` | 全集群范围搜索 **未找到** 名为 `rc-definitely-missing-secret` 的 Secret — 该 Secret **在任何命名空间中都不存在** |
| **e5** | `kubectl events` | 事件时间线确认：`FailedMount` 在 11 分钟内持续出现，无任何恢复信号 |

### 🔍 根因判定

**根本原因：** Pod `rc-volume-missing-secret` 在 `aiops-e2e` 命名空间中引用了 Secret `rc-definitely-missing-secret`（卷名 `missing-secret`，`optional: false`），但该 Secret **从未被创建**（全集群搜索不到），导致 kubelet 无法挂载卷，Pod 卡在 `ContainerCreating` → `Pending`。

### 📋 排除项
- ❌ 命名空间错误 — Secret 不在 `aiops-e2e`，也未在任何其他命名空间存在（已全集群搜索确认）
- ❌ 名称拼写错误 — 非拼写问题，是 Secret **完全不存在**
- ✅ 最终场景：**Secret 对象缺失** — `rc-definitely-missing-secret` 未被创建或被误删除
   ✅ [证据链采集] 完成 (13.4s)
   📤 → 下游数据: evidence_items=6/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证Pod rc-volume-missing-secret的当前状态和卷挂载事件（最高优先级）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-secret -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-volume-missing-secret","namespace":"aiops-e2e"},"purpose":"读取Pod Events原文，验证FailedMount事件是否仍指向secret not found","evidence_type":"current_state_and_events","target_scope":"Pod/aiops-e2e/rc-volume-missing-secret","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取Pod YAML，查看volumes[].secret.secretName引用","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-missing-secret -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-volume-missing-secret","namespace":"aiops-e2e"},"purpose":"确认spec.volumes中secret卷的引用名称","evidence_type":"configuration","target_scope":"Pod/aiops-e2e/rc-volume-missing-secret","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"查询Secret rc-definitely-missing-secret是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-definitely-missing-secret -n aiops-e2e","tool_args":{"kind":"secret","name":"rc-definitely-missing-secret","namespace":"aiops-e2e"},"purpose":"验证Secret是否存在于aiops-e2e命名空间，NotFound即根因证据","evidence_type":"dependency_verification","target_scope":"Secret/aiops-e2e/rc-definitely-missing-secret","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"查询所有namespace中是否存在同名Secret","level":"important","tool":"kubectl_find_resource","command":"kubectl get secret -A | grep rc-definitely-missing-secret","tool_args":{},"purpose":"检查Secret是否被创建在了其他命名空间","evidence_type":"cross_namespace_check","target_scope":"Secret/all-namespaces/rc-definitely-missing-secret","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5","description":"获取Pod相关事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-missing-secret --sort-by='.lastTimestamp'","tool_args":{"resource_type":"pod","resource_name":"rc-volume-missing-secret","namespace":"aiops-e2e"},"purpose":"补充Pod事件时间线，确认FailedMount持续状态","evidence_type":"events_timeline","target_scope":"Pod/aiops-e2e/rc-volume-missing-secret","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-missing-secret\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  53s (x13 over 11m)  kubelet            MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found\n  Warning  FailedMount  2m16s               kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-secret], unattached volumes=[kube-api-access-7n89z missing-secret]: timed out waiting for the condition\n  Warning  FailedMount  2s (x4 over 9m7s)   kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-secret], unattached volumes=[missing-secret kube-api-access-7n89z]: timed out waiting for the condition\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  missing-secret:\n    Type:        Secret (a volume populated by a Secret)\n    SecretName:  rc-definitely-missing-secret\n    Optional:    false\n  kube-api-access-7n89z:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedMount  2m16s               kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-secret], unattached volumes=[kube-api-access-7n89z missing-secret]: timed out waiting for the condition\n  Warning  FailedMount  53s (x13 over 11m)  kubelet            MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found\n  Warning  FailedMount  2s (x4 over 9m7s)   kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-secret], unattached volumes=[missing-secret kube-api-access-7n89z]: timed out waiting for the condition\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/961c38b87d7f43de/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/961c38b87d7f43de/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/961c38b87d7f43de/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-missing-secret\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T04:01:35Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-missing-secret, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"missing-secret\", \"secret\": null}\n- {\"name\": \"kube-api-access-7n89z\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/961c38b87d7f43de/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/961c38b87d7f43de/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/961c38b87d7f43de/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=187 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide secret rc-definitely-missing-secret -n aiops-e2e\nError from server (NotFound): secrets \"rc-definitely-missing-secret\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/961c38b87d7f43de/tools/003-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/961c38b87d7f43de/tools/003-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/961c38b87d7f43de/tools/003-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n55s (x13 over 11m)   Warning   FailedMount   Pod/rc-volume-missing-secret   MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found\n2m18s                Warning   FailedMount   Pod/rc-volume-missing-secret   Unable to attach or mount volumes: unmounted volumes=[missing-secret], unattached volumes=[kube-api-access-7n89z missing-secret]: timed out waiting for the condition\n4s (x4 over 9m9s)    Warning   FailedMount   Pod/rc-volume-missing-secret   Unable to attach or mount volumes: unmounted volumes=[missing-secret], unattached volumes=[missing-secret kube-api-access-7n89z]: timed out waiting for the condition","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/961c38b87d7f43de/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/961c38b87d7f43de/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/961c38b87d7f43de/tools/004-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_find_resource","data":"kubectl_find_resource 输出摘要: raw_chars=110 lines=2\nCommand failed (exit 1):\nkubectl get -A --show-labels -o wide secret | grep -i 'rc-definitely-missing-secret'","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/961c38b87d7f43de/tools/005-evidence-kubectl_find_resource.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/961c38b87d7f43de/tools/005-evidence-kubectl_find_resource.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/961c38b87d7f43de/tools/005-evidence-kubectl_find_resource.summary.txt"}],"llm_analysis":"所有证据已采集完成，下面给出结论。\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据\n\n| # | 工具 | 关键发现 |\n|---|------|---------|\n| **e1** | `kubectl describe pod` | Pod `rc-volume-missing-secret` 状态 **Pending**，Events 明确报错：`MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found`（已持续 11 分钟，重复 13 次） |\n| **e2** | `kubectl get pod -o yaml` | 卷 `missing-secret` 的 **Type=Secret**，**SecretName=rc-definitely-missing-secret**，且 **Optional=false**（非可选卷，缺失将阻止 Pod 启动） |\n| **e3** | `kubectl get secret` | **Error from server (NotFound): secrets \"rc-definitely-missing-secret\" not found** — Secret 在 `aiops-e2e` 命名空间不存在 |\n| **e4** | `kubectl get secret -A \\| grep` | 全集群范围搜索 **未找到** 名为 `rc-definitely-missing-secret` 的 Secret — 该 Secret **在任何命名空间中都不存在** |\n| **e5** | `kubectl events` | 事件时间线确认：`FailedMount` 在 11 分钟内持续出现，无任何恢复信号 |\n\n### 🔍 根因判定\n\n**根本原因：** Pod `rc-volume-missing-secret` 在 `aiops-e2e` 命名空间中引用了 Secret `rc-definitely-missing-secret`（卷名 `missing-secret`，`optional: false`），但该 Secret **从未被创建**（全集群搜索不到），导致 kubelet 无法挂载卷，Pod 卡在 `ContainerCreating` → `Pending`。\n\n### 📋 排除项\n- ❌ 命名空间错误 — Secret 不在 `aiops-e2e`，也未在任何其他命名空间存在（已全集群搜索确认）\n- ❌ 名称拼写错误 — 非拼写问题，是 Secret **完全不存在**\n- ✅ 最终场景：**Secret 对象缺失** — `rc-definitely-missing-secret` 未被创建或被误删除","collection_summary":"计划 5 项，实际采集 4 项，未采集 1 项，完整度 80%；其中真实环境证据 6/7 项，完整度 86%；实际执行工具 6 个，匹配计划 4 个，未规划证据 2 个","plan_total":5,"plan_collected":4,"plan_completeness":0.8,"environment_evidence_total":7,"environment_evidence_collected":6,"environment_evidence_completeness":0.8571428571428571,"executed_tool_count":6,"matched_tool_count":4,"unplanned_tool_count":2,"evidence_inventory":[{"id":"e1","description":"验证Pod rc-volume-missing-secret的当前状态和卷挂载事件（最高优先级）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-secret -n aiops-e2e","purpose":"读取Pod Events原文，验证FailedMount事件是否仍指向secret not found","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取Pod YAML，查看volumes[].secret.secretName引用","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-missing-secret -n aiops-e2e -o yaml","purpose":"确认spec.volumes中secret卷的引用名称","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"查询Secret rc-definitely-missing-secret是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get secret rc-definitely-missing-secret -n aiops-e2e","purpose":"验证Secret是否存在于aiops-e2e命名空间，NotFound即根因证据","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"e4","description":"查询所有namespace中是否存在同名Secret","level":"important","tool":"kubectl_find_resource","command":"kubectl get secret -A | grep rc-definitely-missing-secret","purpose":"检查Secret是否被创建在了其他命名空间","collected":false,"source":"planned","outcome":"unknown"},{"id":"e5","description":"获取Pod相关事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-missing-secret --sort-by='.lastTimestamp'","purpose":"补充Pod事件时间线，确认FailedMount持续状态","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["e4(查询所有namespace中是否存在同名Secret): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/5 项, 完整度: 86%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证Pod rc-volume-missing-secret的当前状态和卷挂载事件（最高优先级） | `kubectl describe pod rc-volume-missing-secret -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_yaml | 获取Pod YAML，查看volumes[].secret.secretName引用 | `kubectl get pod rc-volume-missing-secret -n aiops-e2e -o yaml` |
   | e3 | critical | ✅ | kubectl_get_by_name | 查询Secret rc-definitely-missing-secret是否存在 | `kubectl get secret rc-definitely-missing-secret -n aiops-e2e` |
   | e4 | important | ❌ | kubectl_find_resource | 查询所有namespace中是否存在同名Secret | `kubectl get secret -A | grep rc-definitely-missing-secret` |
   | e5 | important | ✅ | kubectl_events | 获取Pod相关事件 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volum...` |

   ⚠️ 未采集原因:
   - e4(查询所有namespace中是否存在同名Secret): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (15.0s)
   📤 → 下游数据: root_cause=Pod aiops-e2e/rc-volume-missing-secret 状态为 Pending/ContainerCreating，kubectl describe 显示 MountVolume.SetUp failed for volume "missing-secret" : secret "rc-definitely-missing-secret" not found（重复13次，持续11分钟）。Pod YAML 确认卷 missing-secret 类型为 Secret，secretName=rc-definitely-missing-secret，optional=false。kubectl get secret 在 aiops-e2e 命名空间返回 NotFound，全集群搜索也未找到该 Secret。根因：Secret 对象缺失，从未被创建或已被误删除。
   confidence=98%
   causal_chain={"root_cause": "Secret 'rc-definitely-missing-secret' 在集群任何命名空间中均不存在（从未创建或被误删除）", "propagation": "Pod 声明了卷 missing-secret（Type=Secret, SecretName=rc-definitely-missing-secret, optional=false）→ kubelet 尝试挂载该卷 → 向 API Server 查询 Secret → API Server 返回 NotFound → kubelet 无法完成卷挂载 → Pod 卡在 ContainerCreating/Pending 状态", "direct_cause": "Pod 引用的非可选 Secret 卷 'missing-secret' 找不到对应的 Secret 对象", "manifestation": "Pod rc-volume-missing-secret 在 aiops-e2e 命名空间中持续处于 Pending/ContainerCreating 状态，kubectl describe 显示 FailedMount 事件：secret not found"}
   rca_analysis={"phenomenon": "集群中存在1个异常Pod: aiops-e2e/rc-volume-missing-secret，当前状态为Pending/ContainerCreating，持续约11分钟，无法启动。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod rc-volume-missing-secret 状态 Pending，Events: MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found（重复13次，持续11分钟）", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml", "content": "卷 missing-secret 类型 Secret，SecretName=rc-definitely-missing-secret，optional=false", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_by_name", "content": "kubectl get secret rc-definitely-missing-secret -n aiops-e2e 返回 NotFound", "reliability": "高"}, {"id": "e4", "source": "kubectl_find_resource", "content": "全集群 grep 搜索 rc-definitely-missing-secret 未找到匹配的 Secret", "reliability": "高"}, {"id": "e5", "source": "kubectl_events", "content": "FailedMount 事件在11分钟内持续出现，无恢复信号", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "全集群65个Pod中仅此1个异常，其余59个Running", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedMount 53s (x13 over 11m) kubelet MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found", "interpretation": "Pod 卷挂载失败的直接错误信息，明确指向 Secret 缺失。kubelet 无法找到名为 rc-definitely-missing-secret 的 Secret 对象。"}, {"evidence_id": "e2", "raw_data": "volumes: [{\"name\": \"missing-secret\", \"secret\": null}]；Pod YAML 中 secretName=rc-definitely-missing-secret，optional=false", "interpretation": "Pod 声明了一个非可选的 Secret 卷，且 SecretName 为 rc-definitely-missing-secret。optional=false 意味着该卷缺失会阻塞 Pod 启动。YAML 中 secret 字段为 null 进一步表明 Kubernetes 无法解析到对应的 Secret 对象。"}, {"evidence_id": "e3", "raw_data": "Error from server (NotFound): secrets \"rc-definitely-missing-secret\" not found", "interpretation": "在 Pod 所在命名空间 aiops-e2e 中查询该 Secret，API Server 确认该 Secret 不存在。这是直接证据。"}, {"evidence_id": "e4", "raw_data": "kubectl get -A --show-labels -o wide secret | grep -i 'rc-definitely-missing-secret' 返回 exit 1，无匹配", "interpretation": "全集群范围搜索也未找到该 Secret，排除命名空间放错的可能性。该 Secret 在任何命名空间中都不存在。"}, {"evidence_id": "e5", "raw_data": "55s (x13 over 11m) Warning FailedMount ... secret not found；2m18s Warning FailedMount ... timed out waiting", "interpretation": "事件时间线显示挂载失败持续发生，kubelet 反复重试但始终失败，最终超时。没有其他事件表明问题正在解决。"}, {"evidence_id": "layer_1", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59}", "interpretation": "全集群中仅有此1个异常 Pod，其他 Pod 正常运行，说明问题隔离在此 Pod 及其依赖的 Secret 对象上，非集群全局性问题。"}], "causal_chain": {"root_cause": "Secret 'rc-definitely-missing-secret' 在集群任何命名空间中均不存在（从未创建或被误删除）", "propagation": "Pod 声明了卷 missing-secret（Type=Secret, SecretName=rc-definitely-missing-secret, optional=false）→ kubelet 尝试挂载该卷 → 向 API Server 查询 Secret → API Server 返回 NotFound → kubelet 无法完成卷挂载 → Pod 卡在 ContainerCreating/Pending 状态", "direct_cause": "Pod 引用的非可选 Secret 卷 'missing-secret' 找不到对应的 Secret 对象", "manifestation": "Pod rc-volume-missing-secret 在 aiops-e2e 命名空间中持续处于 Pending/ContainerCreating 状态，kubectl describe 显示 FailedMount 事件：secret not found"}, "root_cause": "Pod aiops-e2e/rc-volume-missing-secret 状态为 Pending/ContainerCreating，kubectl describe 显示 MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found（重复13次，持续11分钟）。Pod YAML 确认卷 missing-secret 类型为 Secret，secretName=rc-definitely-missing-secret，optional=false。kubectl get secret 在 aiops-e2e 命名空间返回 NotFound，全集群搜索也未找到该 Secret。根因：Secret 对象缺失，从未被创建或已被误删除。", "root_cause_summary": "Pod aiops-e2e/rc-volume-missing-secret 状态为 Pending/ContainerCreating，kubectl describe 显示 MountVolume.SetUp failed for volume \"missing-secret\" : secret \"rc-definitely-missing-secret\" not found（重复13次，持续11分钟）。Pod YAML 确认卷 missing-secret 类型为 Secret，secretName=rc-definitely-missing-secret，optional=false。kubectl get secret 在 aiops-e2e 命名空间返回 NotFound，全集群搜索也未找到该 Secret。根因：Secret 对象缺失，从未被创建或已被误删除。", "confidence": 0.98, "confidence_reason": "直接证据链完整且闭环：(1) Events 明文报错 secret not found (e1/e5) → (2) YAML 确认 Secret 引用配置 (e2) → (3) kubectl get 确认 Secret 不存在 (e3) → (4) 全集群搜索确认不在任何命名空间 (e4)。所有证据高度一致、无冲突。因果链清晰无歧义。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [{"cause": "Secret 存在于其他命名空间", "probability": "low", "reason": "已通过 kubectl get -A 全集群搜索排除，未找到任何名为 rc-definitely-missing-secret 的 Secret"}, {"cause": "Secret 名称拼写错误", "probability": "low", "reason": "Pod YAML 中 secretName=rc-definitely-missing-secret 与 Events 中引用的名称一致，且全集群搜索无此名称的 Secret，不是拼写问题而是完全不存在"}, {"cause": "RBAC/权限导致 Secret 不可见", "probability": "low", "reason": "kubectl 使用管理员权限查询仍返回 NotFound，且全集群搜索也返回空，排除权限问题"}], "limitations": "证据 e4（全集群搜索）原始输出仅2行，确认无匹配，但未列出所有已存在的 Secret 供比对。已采集的证据足以锁死根因，无需额外数据。未采集的 e4（全集群搜索）已被 kubectl_find_resource 替代完成。", "llm_raw_analysis": "L0 根因分析完成。异常组 g1（单 Pod: aiops-e2e/rc-volume-missing-secret）的根因明确：Secret 'rc-definitely-missing-secret' 不存在。五层模型归属 L0（磁盘/存储/驱逐层）- VolumeMountFailed 子类。仅此1个异常组，已完全覆盖。非主异常组不存在。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod aiops-e2e/rc-volume-missing-secret 状态为 Pending/ContainerCreating，kubectl describe 显示 MountVolume.SetUp failed for volume "missing-secret" : secret...
   置信度: 98%
   🔗 因果链:
     根本原因: Secret 'rc-definitely-missing-secret' 在集群任何命名空间中均不存在（从未创建或被误删除）
     传导机制: Pod 声明了卷 missing-secret（Type=Secret, SecretName=rc-definitely-missing-secret, optional=false）→ kubelet 尝试挂载该卷 → 向 API Server 查询 Secret → API Server 返回 NotFound → kubelet 无法完成卷挂载 → Pod 卡在 ContainerCreating/Pending 状态
     最终表现: Pod rc-volume-missing-secret 在 aiops-e2e 命名空间中持续处于 Pending/ContainerCreating 状态，kubectl describe 显示 FailedMount 事件：secret not found


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (18.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6148 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 3.6s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，请查收您的集群诊断报告。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **当前异常 Pod 状态** | ContainerCreating / VolumeMountFailed |
| **兼容归因层** | L0 - 磁盘/存储/驱逐层 |
| **问题分类** | VolumeMountFailed - Secret 不存在 |
| **是否影响全局** | **否**。集群中 65 个 Pod 中仅 1 个异常，其余 59 个 Pod 运行正常。 |
| **置信度** | 高 (98%) |
| **证据完整度** | 4/5 (80%) |

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**问题总结**：

您的集群整体运行健康。根据对全集群 65 个 Pod 的扫描，有 1 个 Pod 处于**异常状态**，其余 Pod 均运行正常。

**关键实体**：

| 类型 | 值 |
|------|-----|
| 异常Pod | `aiops-e2e/rc-volume-missing-secret` |
| 异常状态 | Pending / ContainerCreating |
| 关联Secret | `rc-definitely-missing-secret` |
| 关联Volume | `missing-secret` |
| 所在Node | `node1` |
| 错误信息 | `MountVolume.SetUp failed for volume "missing-secret" : secret "rc-definitely-missing-secret" not found` |

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|---|---|---|---|
| 1 | Pod 状态与事件 | `kubectl describe pod` | 状态: Pending<br>事件: `Warning FailedMount 53s (x13 over 11m) kubelet MountVolume.SetUp failed for volume "missing-secret" : secret "rc-definitely-missing-secret" not found` | Pod 卡在挂载卷阶段，错误信息明确指向Secret缺失。 |
| 2 | Pod 配置 | `kubectl get pod -o yaml` | `volumes` 定义引用了 `secretName: rc-definitely-missing-secret`，且 `optional` 字段缺失（默认为 `false`）。 | Pod 配置要求挂载一个名为 `rc-definitely-missing-secret` 的 Secret，且该Secret是必需的。 |
| 3 | Secret 查询 | `kubectl get secret -n aiops-e2e` | `Error from server (NotFound): secrets "rc-definitely-missing-secret" not found` | 在 Pod 所在命名空间 `aiops-e2e` 中确实**不存在**该 Secret。 |
| 4 | Pod 相关事件 | `kubectl events` | `55s (x13 over 11m) Warning FailedMount Pod/rc-volume-missing-secret MountVolume.SetUp failed for volume "missing-secret" : secret "rc-definitely-missing-secret" not found` | 事件系统反复报告相同的挂载失败错误，排除了瞬时错误，确认是持续性问题。 |
| 5 | 全集群搜索 | `kubectl get secret -A` | `grep` 搜索无匹配结果，`Command failed (exit 1)` | 该 Secret 在集群**任何命名空间**中都不存在。 |
| 6 | 集群概况 | `kubectl get pods -A` | `rows=65 abnormal=1 status_counts={'Running': 59}` | 集群中 65 个 Pod 有 1 个异常，其余 59 个运行正常，故障范围有限。 |

### 证据关联分析

- **证据 #1 + 证据 #3 印证**：Pod 事件 `secret not found` 与 Secret 查询 `NotFound` 直接对应，确认了根因，排除了临时性 API 错误。
- **证据 #2 + 证据 #5 印证**：Pod YAML 中的 `secretName` 与全集群都找不到的 Secret 名称一致，说明问题出在 Secret 本身，而非 Pod 配置错误。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 全集群所有现有 Secret 列表 | low | 用于进一步确认该 Secret 是否被拼写错误或误创建在别处。当前全集群搜索已返回无匹配，此证据为锦上添花。 |

## 🎯 根因分析

### 因果链

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                    │
│ Secret 'rc-definitely-missing-secret' 在集群任何命名空间中均不存在。          │
│ (可能原因：从未被创建、被误删除、或因部署流程问题未正确生成)                  │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                    │
│ Pod rc-volume-missing-secret 声明了一个必需卷 "missing-secret"               │
│   ↓                                                                         │
│ 该卷类型为 Secret，指定的 secretName 为 'rc-definitely-missing-secret'      │
│   ↓                                                                         │
│ kubelet 尝试挂载该卷，向 API Server 发起查询                                         │
│   ↓                                                                         │
│ API Server返回'NotFound'                                                     │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                    │
│ kubelet 无法找到并创建所需的 Secret 卷挂载，持续重试并报错                    │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                │
│ Pod 状态卡在 'Pending' / 'ContainerCreating'，无法进入 Running 状态。        │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #1 (FailedMount 事件)、#3 (Secret 查询 NotFound)、#5 (全集群搜索无匹配)，问题的根本原因是 **Pod `aiops-e2e/rc-volume-missing-secret` 所引用的 Secret `rc-definitely-missing-secret` 在集群中完全不存在**，导致卷挂载失败，Pod 无法启动。

**置信度**：高 (98%)
- ✅ **事件系统直接报错**：`MountVolume.SetUp failed for volume “missing-secret” : secret “rc-definitely-missing-secret” not found`
- ✅ **直接验证失效**：`kubectl get secret -n aiops-e2e rc-definitely-missing-secret` 确认在目标命名空间不存在。
- ✅ **全集群搜索**：`kubectl get secret -A | grep rc-definitely-missing-secret` 确认在任何命名空间都不存在。

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 创建缺失的 Secret**

如果您知道该 Secret 的内容（例如，一个 Token 或密码），请使用以下命令创建它：

```bash
# 请将 <your-secret-data> 替换为实际的 Secret 内容
kubectl create secret generic rc-definitely-missing-secret \
  --from-literal=key1=value1 \
  -n aiops-e2e
```
*依据*：根本原因是 Secret 对象缺失，创建后即可解决。

**2. [可选] 如果该 Secret 不应存在，则删除或修改 Pod**

如果该 Secret 是配置错误，不应被使用，您需要：
   a. **删除 Pod（由 Deployment 管理）**: 如果是 Deployment 管理的 Pod，需修改 Deployment 配置移除卷引用。
   b. **删除 Pod**:
       ```bash
       kubectl delete pod rc-volume-missing-secret -n aiops-e2e
       ```
   c. **（重要）检查并修正创建该 Pod 的控制器（如 Deployment）**:
       ```bash
       kubectl edit deployment <deployment-name> -n aiops-e2e
       ```
       在 YAML 编辑器中，找到 `volumes` 部分，并移除引用 `rc-definitely-missing-secret` 的条目。

### 后续优化

1. **CI/CD 流程检查**：部署流水线应确保 Pod 引用的所有 ConfigMap/Secret 对象在部署时都已存在。
2. **资源告警**：配置对 `FailedMount` 事件的监控和告警，以便及时发现问题。
3. **配置校验**：使用 `kubectl apply --dry-run=client` 或类似工具进行预校验。

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认修复 | `kubectl get pod rc-volume-missing-secret -n aiops-e2e` | 状态变为 `Running` |
| 2. 检查事件 | `kubectl describe pod rc-volume-missing-secret -n aiops-e2e` | 不再出现 `FailedMount` 错误 |
| 3. 确认集群状态 | `kubectl get pods -A | grep -v Running` | 不再输出异常 Pod（或输出为 0） |

## ⚠️ 注意事项

- 创建 Secret 时，请确保数据格式正确（如 base64 编码）。
- 如果 Pod 是由 Deployment 等控制器创建的，删除 Pod 后会重新创建，问题会复现，因此必须修改该控制器的配置。
- 此问题**仅限于单个 Pod**，不影响集群中其他 59 个正在运行的服务。

---

## 📊 性能统计

├─ 总耗时: 1.1m
├─ 问题定位: 17.2s (27%) ✅
├─ 证据链采集: 13.4s (21%) ✅
├─ 根因分析: 15.0s (24%) ✅
├─ 汇总总结: 18.0s (28%) ✅
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
