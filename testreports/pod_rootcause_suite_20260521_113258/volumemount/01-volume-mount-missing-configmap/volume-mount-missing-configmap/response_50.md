======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 66545d2f630342a3]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先做全局 Pod 状态扫描，看看集群中有哪些异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59}
NAMESPACE         NAME                                                READY   STATUS              RESTARTS       A
   💭 [问题定位] 发现了一个异常 Pod。让我进一步查看它的详细信息。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-volume-missing-configmap   0/1     ContainerCreating   0       
   💭 [问题定位] Pod 上直接有标签 `pod_abnormal_type=VolumeMountFailed`，让我查一下 runbook 和这个 Pod 的详细描述。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-missing-configmap
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  44s (x21 over 27m)    kubelet            MountVolume.Se
   💭 [问题定位] 现在我已经有了足够的信息。让我再确认一下 ConfigMap 是否真的不存在。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=1 abnormal=0 status_counts={}
NAME               DATA   AGE    LABELS
# 样例行
kube-root-ca.crt   1      117d   <none>
   💭 [问题定位] 完美，证据链已经完整。现在给出诊断结论。

---

## 诊断结论

### 全局 Pod 扫描结果

| 总计 Pod | Running | 异常 Pod |
|---------|---------|---------|
| 65 | 59 | **1** |

### 异常 Pod 详情

| Pod | 命名空间 | 状态 | 异常类型 |
|-----|---------|------|---------|
| `rc-volume-missing-configmap` | aiops-e2e | **ContainerCreating**（Pending） | **VolumeMountFailed** |

### 根因分析

Pod `rc-volume-missing-configmap` 卡在 **ContainerCreating** 状态，根本原因是：

**Volume 引用了不存在的 ConfigMap。**
- Pod 的 `.spec.volumes` 中定义了一个名为 `missing-config` 的 ConfigMap 类型卷，引用了 `rc-definitely-missing-configmap`
- Events 明确报错：**`configmap "rc-definitely-missing-configmap" not found`**
- 检查命名空间 `aiops-e2e` 下确实**不存在**名为 `rc-definitely-missing-configmap` 的 ConfigMap（仅有系统自带的 `kube-root-ca.crt`）

### 输出结构化信息

- **layer**: L0（VolumeMountFailed 归入 L0 层，属于存储/卷配置类问题）
- **derived_layer**: L0
- **layers**: ["L0"]
- **layer_name**: pod-volume-mount-failed
- **confidence**: 高
- **pod_status_keyword**: ContainerCreating
- **pod_abnormal_type**: VolumeMountFailed
- **status_category**: storage_volume
- **abnormal_pods**: [{"name": "rc-volume-missing-configmap", "namespace": "aiops-e2e", "status": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed"}]
- **abnormal_groups**: {"VolumeMountFailed": [{"name": "rc-volume-missing-configmap", "namespace": "aiops-e2e"}]}
- **key_entities**: ["ConfigMap/rc-definitely-missing-configmap/aiops-e2e", "Pod/rc-volume-missing-configmap/aiops-e2e"]
- **possible_scenarios**:
  1. ConfigMap `rc-definitely-missing-configmap` 从未被创建（最常见）
  2. ConfigMap 被手动或自动删除，但 Pod 仍在使用
  3. ConfigMap 名称拼写错误（Pod 中引用的名称与实际名称不一致）
   ✅ [问题定位] 完成 (18.7s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[{'scenario': 'ConfigMap rc-definitely-missing-configmap 从未被创建', 'probability': '高', 'reason': '命名空间 aiops-e2e 下仅有 kube-root-ca.crt，不存在该 ConfigMap，Pod volume 引用指向一个不存在的对象'}, {'scenario': 'ConfigMap 被手动或自动删除，但 Pod 仍在使用', 'probability': '中', 'reason': '若 ConfigMap 之前存在但被删除，Pod 重建时挂载失败'}, {'scenario': 'ConfigMap 名称拼写错误', 'probability': '低', 'reason': 'Pod spec 中 volumes[].configMap.name 为 rc-definitely-missing-configmap，与实际应引用的名称不一致'}]
   entities=[{"type": "Pod", "name": "rc-volume-missing-configmap", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-definitely-missing-configmap", "namespace": "aiops-e2e"}]
   reasoning=Pod rc-volume-missing-configmap (aiops-e2e) 处于 ContainerCreating/Pending 状态，当前仍异常。kubectl describe 明确显示 MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found。检查 aiops-e2e 命名空间下确实不存在该 ConfigMap（仅有 kube-root-ca.crt）。根据跑书判定规则：ConfigMap not found + Pod spec volumes[].configMap -> VolumeMountFailed。VolumeMountFailed 归入 L0（storage_volume 类），属于存储/卷配置故障。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "pod-volume-mount-failed", "confidence": 0.98, "reasoning": "Pod rc-volume-missing-configmap (aiops-e2e) 处于 ContainerCreating/Pending 状态，当前仍异常。kubectl describe 明确显示 MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found。检查 aiops-e2e 命名空间下确实不存在该 ConfigMap（仅有 kube-root-ca.crt）。根据跑书判定规则：ConfigMap not found + Pod spec volumes[].configMap -> VolumeMountFailed。VolumeMountFailed 归入 L0（storage_volume 类），属于存储/卷配置故障。", "abnormal_pods": [{"name": "rc-volume-missing-configmap", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "Pod", "name": "rc-volume-missing-configmap", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-definitely-missing-configmap", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "ConfigMap rc-definitely-missing-configmap 从未被创建", "probability": "高", "reason": "命名空间 aiops-e2e 下仅有 kube-root-ca.crt，不存在该 ConfigMap，Pod volume 引用指向一个不存在的对象"}, {"scenario": "ConfigMap 被手动或自动删除，但 Pod 仍在使用", "probability": "中", "reason": "若 ConfigMap 之前存在但被删除，Pod 重建时挂载失败"}, {"scenario": "ConfigMap 名称拼写错误", "probability": "低", "reason": "Pod spec 中 volumes[].configMap.name 为 rc-definitely-missing-configmap，与实际应引用的名称不一致"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-configmap"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-configmap"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-volume-missing-configmap                         0/1     ContainerCreating   0              27m     <none>           node1    <none>           <none>            app=rc-volume-missing-configmap,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/66545d2f630342a3/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/66545d2f630342a3/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/66545d2f630342a3/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 98%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来执行既有 evidence_plan 中的关键工具调用，采集真实环境证据。

首先，先确认 Pod 的当前状态和 Events，同时查找 ConfigMap。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_find_resource
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_find_resource (success)
      📄 kubectl_find_resource 输出摘要: raw_chars=116 lines=2
Command failed (exit 1):
kubectl get -A --show-labels -o wide configmap | grep -i 'rc-definitely-missing-configmap'
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
  Warning  FailedMount  66s (x21 over 27m)    kubelet            MountVolume.Se
   💭 [证据链采集] 现在执行 ev-04，全量查看 aiops-e2e 命名空间下的 ConfigMap：
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=1 abnormal=0 status_counts={}
NAME               DATA   AGE    LABELS
# 样例行
kube-root-ca.crt   1      117d   <none>
   💭 [证据链采集] ## 证据采集结论

### ✅ 已采集证据（4/4，全部完成）

| 序号 | 证据 | 结果 |
|------|------|------|
| **ev-01** | `kubectl describe pod` — 查看 Pod Events | ✅ **核心证据** — Events 持续显示：`MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found`，已重复 21 次，最新触发在 66s 前。Pod 当前状态为 **Pending**，容器状态为 **ContainerCreating** |
| **ev-02** | `kubectl_find_resource` — 查找 ConfigMap `rc-definitely-missing-configmap` | ✅ **核心证据** — 全集群搜索返回 **NotFound**（exit code 1），该 ConfigMap 在任何命名空间下都不存在 |
| **ev-03** | `kubectl_get_yaml` — Pod YAML 完整验证 | ✅ **核心证据** — `.spec.volumes[0].configMap.name` 明确指向 `rc-definitely-missing-configmap`，且 `Optional: false`（非可选，缺少则无法启动） |
| **ev-04** | `kubectl get configmap -n aiops-e2e` | ✅ **核心证据** — 命名空间下仅有 `kube-root-ca.crt`（系统自动注入），不存在 `rc-definitely-missing-configmap` |

### 🔍 根因结论

**Pod `rc-volume-missing-configmap`（aiops-e2e）卡在 Pending/ContainerCreating**，直接原因是：
- Pod 的 volume `missing-config` 引用了 ConfigMap `rc-definitely-missing-configmap`（非 optional），
- 但该 ConfigMap **从未被创建或已被删除**，命名空间下仅有一个系统自动注入的 `kube-root-ca.crt`，
- kubelet 持续报错 `MountVolume.SetUp failed`，导致 Pod 无法完成挂载启动。

### 🔧 修复建议（仅建议，不执行）
创建缺失的 ConfigMap 即可恢复：
```bash
kubectl create configmap rc-definitely-missing-configmap --from-literal=key=value -n aiops-e2e
```
或调整 Pod spec 中的 volume 引用名称。Pod 创建后会自动重试挂载。
   ✅ [证据链采集] 完成 (15.7s)
   📤 → 下游数据: evidence_items=7/8
   evidence_analysis={"evidence_plan":[{"id":"ev-01","description":"验证 Pod rc-volume-missing-configmap 当前状态和 Events - 确认 FailedMount ConfigMap not found 事件持续存在","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-configmap -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-volume-missing-configmap","namespace":"aiops-e2e"},"purpose":"获取 Pod Events 原文，验证 MountVolume.SetUp failed for configmap not found 事件是否持续存在","evidence_type":"current_state_and_events","target_scope":"Pod/aiops-e2e/rc-volume-missing-configmap","acceptable_tools":["kubectl_describe","kubectl_get_yaml","kubectl_events"],"counts_for_completeness":true},{"id":"ev-02","description":"验证 ConfigMap rc-definitely-missing-configmap 确实不存在于 aiops-e2e 命名空间","level":"critical","tool":"kubectl_find_resource","command":"kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e","tool_args":{"kind":"ConfigMap","name":"rc-definitely-missing-configmap","namespace":"aiops-e2e"},"purpose":"确认 ConfigMap 缺失是当前根因","evidence_type":"resource_existence","target_scope":"ConfigMap/aiops-e2e/rc-definitely-missing-configmap","acceptable_tools":["kubectl_get_by_name","kubectl_find_resource","run_bash_command"],"counts_for_completeness":true},{"id":"ev-03","description":"查看 Pod YAML 确认 volume 引用 configMap.name 字段","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-volume-missing-configmap","namespace":"aiops-e2e"},"purpose":"验证 .spec.volumes[].configMap.name 指向 rc-definitely-missing-configmap","evidence_type":"configuration_details","target_scope":"Pod/aiops-e2e/rc-volume-missing-configmap","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"ev-04","description":"获取 aiops-e2e 命名空间下所有 ConfigMap 列表，确认无 rc-definitely-missing-configmap","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get configmap -n aiops-e2e","tool_args":{"kind":"ConfigMap","namespace":"aiops-e2e"},"purpose":"全量确认命名空间下唯一 ConfigMap 是 kube-root-ca.crt，缺失目标 ConfigMap","evidence_type":"namespace_inventory","target_scope":"ConfigMap/aiops-e2e","acceptable_tools":["kubectl_get_by_kind_in_namespace","run_bash_command"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_find_resource","data":"kubectl_find_resource 输出摘要: raw_chars=116 lines=2\nCommand failed (exit 1):\nkubectl get -A --show-labels -o wide configmap | grep -i 'rc-definitely-missing-configmap'","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/66545d2f630342a3/tools/001-evidence-kubectl_find_resource.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/66545d2f630342a3/tools/001-evidence-kubectl_find_resource.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/66545d2f630342a3/tools/001-evidence-kubectl_find_resource.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-missing-configmap\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T03:33:04Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-missing-configmap, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"missing-config\", \"configMap\": \"rc-definitely-missing-configmap\"}\n- {\"name\": \"kube-api-access-h7lqz\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/66545d2f630342a3/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/66545d2f630342a3/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/66545d2f630342a3/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-missing-configmap\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  66s (x21 over 27m)    kubelet            MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found\n  Warning  FailedMount  5m16s (x10 over 25m)  kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-config], unattached volumes=[missing-config kube-api-access-h7lqz]: timed out waiting for the condition\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  missing-config:\n    Type:      ConfigMap (a volume populated by a ConfigMap)\n    Name:      rc-definitely-missing-configmap\n    Optional:  false\n  kube-api-access-h7lqz:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedMount  5m16s (x10 over 25m)  kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-config], unattached volumes=[missing-config kube-api-access-h7lqz]: timed out waiting for the condition\n  Warning  FailedMount  66s (x21 over 27m)    kubelet            MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/66545d2f630342a3/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/66545d2f630342a3/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/66545d2f630342a3/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"kubectl_get_by_kind_in_namespace 表格摘要: rows=1 abnormal=0 status_counts={}\nNAME               DATA   AGE    LABELS\n# 样例行\nkube-root-ca.crt   1      117d   <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/66545d2f630342a3/tools/004-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/66545d2f630342a3/tools/004-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/66545d2f630342a3/tools/004-evidence-kubectl_get_by_kind_in_namespace.summary.txt"}],"llm_analysis":"## 证据采集结论\n\n### ✅ 已采集证据（4/4，全部完成）\n\n| 序号 | 证据 | 结果 |\n|------|------|------|\n| **ev-01** | `kubectl describe pod` — 查看 Pod Events | ✅ **核心证据** — Events 持续显示：`MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found`，已重复 21 次，最新触发在 66s 前。Pod 当前状态为 **Pending**，容器状态为 **ContainerCreating** |\n| **ev-02** | `kubectl_find_resource` — 查找 ConfigMap `rc-definitely-missing-configmap` | ✅ **核心证据** — 全集群搜索返回 **NotFound**（exit code 1），该 ConfigMap 在任何命名空间下都不存在 |\n| **ev-03** | `kubectl_get_yaml` — Pod YAML 完整验证 | ✅ **核心证据** — `.spec.volumes[0].configMap.name` 明确指向 `rc-definitely-missing-configmap`，且 `Optional: false`（非可选，缺少则无法启动） |\n| **ev-04** | `kubectl get configmap -n aiops-e2e` | ✅ **核心证据** — 命名空间下仅有 `kube-root-ca.crt`（系统自动注入），不存在 `rc-definitely-missing-configmap` |\n\n### 🔍 根因结论\n\n**Pod `rc-volume-missing-configmap`（aiops-e2e）卡在 Pending/ContainerCreating**，直接原因是：\n- Pod 的 volume `missing-config` 引用了 ConfigMap `rc-definitely-missing-configmap`（非 optional），\n- 但该 ConfigMap **从未被创建或已被删除**，命名空间下仅有一个系统自动注入的 `kube-root-ca.crt`，\n- kubelet 持续报错 `MountVolume.SetUp failed`，导致 Pod 无法完成挂载启动。\n\n### 🔧 修复建议（仅建议，不执行）\n创建缺失的 ConfigMap 即可恢复：\n```bash\nkubectl create configmap rc-definitely-missing-configmap --from-literal=key=value -n aiops-e2e\n```\n或调整 Pod spec 中的 volume 引用名称。Pod 创建后会自动重试挂载。","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 7/8 项，完整度 88%；实际执行工具 7 个，匹配计划 3 个，未规划证据 4 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":8,"environment_evidence_collected":7,"environment_evidence_completeness":0.875,"executed_tool_count":7,"matched_tool_count":3,"unplanned_tool_count":4,"evidence_inventory":[{"id":"ev-01","description":"验证 Pod rc-volume-missing-configmap 当前状态和 Events - 确认 FailedMount ConfigMap not found 事件持续存在","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-configmap -n aiops-e2e","purpose":"获取 Pod Events 原文，验证 MountVolume.SetUp failed for configmap not found 事件是否持续存在","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-02","description":"验证 ConfigMap rc-definitely-missing-configmap 确实不存在于 aiops-e2e 命名空间","level":"critical","tool":"kubectl_find_resource","command":"kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e","purpose":"确认 ConfigMap 缺失是当前根因","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"ev-03","description":"查看 Pod YAML 确认 volume 引用 configMap.name 字段","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml","purpose":"验证 .spec.volumes[].configMap.name 指向 rc-definitely-missing-configmap","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-04","description":"获取 aiops-e2e 命名空间下所有 ConfigMap 列表，确认无 rc-definitely-missing-configmap","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get configmap -n aiops-e2e","purpose":"全量确认命名空间下唯一 ConfigMap 是 kube-root-ca.crt，缺失目标 ConfigMap","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["ev-04(获取 aiops-e2e 命名空间下所有 ConfigMap 列表，确认无 rc-definitely-missing-configmap): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 88%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | ev-01 | critical | ✅ | kubectl_describe | 验证 Pod rc-volume-missing-configmap 当前状态和 Even... | `kubectl describe pod rc-volume-missing-configmap -n aiops-e2e` |
   | ev-02 | critical | ✅ | kubectl_find_resource | 验证 ConfigMap rc-definitely-missing-configmap ... | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` |
   | ev-03 | important | ✅ | kubectl_get_yaml | 查看 Pod YAML 确认 volume 引用 configMap.name 字段 | `kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml` |
   | ev-04 | important | ❌ | kubectl_get_by_kind_in_na... | 获取 aiops-e2e 命名空间下所有 ConfigMap 列表，确认无 rc-defi... | `kubectl get configmap -n aiops-e2e` |

   ⚠️ 未采集原因:
   - ev-04(获取 aiops-e2e 命名空间下所有 ConfigMap 列表，确认无 rc-definitely-missing-configmap): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (17.1s)
   📤 → 下游数据: root_cause=Pod rc-volume-missing-configmap (aiops-e2e) 卡在 Pending/ContainerCreating 已 27 分钟，根因是 volume "missing-config" 引用的 ConfigMap "rc-definitely-missing-configmap" 不存在。kubectl describe 显示 FailedMount 事件重复 21 次（最新 66s 前）：MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found。kubectl_find_resource 全集群搜索返回 exit code 1（未找到），aiops-e2e 命名空间下仅有系统注入的 kube-root-ca.crt。Pod YAML 确认该 volume 的 Optional=false，即非可选卷，必须存在才能启动容器。集群其他 59 个 Pod 均正常运行，属局部配置问题。
   confidence=97%
   causal_chain={"root_cause": "ConfigMap rc-definitely-missing-configmap 在 aiops-e2e 命名空间及全集群中不存在（从未被创建或已被删除）", "propagation": "ConfigMap 不存在 → kubelet 尝试挂载 volume missing-config 时获取 ConfigMap 数据失败 → MountVolume.SetUp failed → 卷挂载不满足 → Pod 无法进入 Running 状态 → 容器停留在 ContainerCreating → 30s 超时后变为 Unable to attach or mount volumes → Pod 持续 Pending", "direct_cause": "Pod spec volumes[0].configMap.name=rc-definitely-missing-configmap 指向一个不存在的 ConfigMap，且 Optional=false", "manifestation": "Pod rc-volume-missing-configmap 在 aiops-e2e 命名空间中 0/1 ready，状态 Pending/ContainerCreating，kubelet 持续报 FailedMount configmap not found"}
   rca_analysis={"phenomenon": "Pod rc-volume-missing-configmap (namespace: aiops-e2e) 处于 Pending/ContainerCreating 状态，已持续 27 分钟。kubelet Events 持续报 MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found，已出现 21 次重复。集群整体 65 个 Pod 中 59 个 Running，仅此 1 个异常。", "evidence_inventory": [{"id": "ev-01", "source": "kubectl_describe", "content": "Pod rc-volume-missing-configmap Events 显示 FailedMount: configmap \"rc-definitely-missing-configmap\" not found，重复 21 次，最新 66s 前", "reliability": "高"}, {"id": "ev-02", "source": "kubectl_find_resource", "content": "全集群搜索 configmap rc-definitely-missing-configmap 返回 exit code 1，不存在", "reliability": "高"}, {"id": "ev-03", "source": "kubectl_get_yaml", "content": "Pod spec volumes[0].configMap.name = rc-definitely-missing-configmap, Optional=false", "reliability": "高"}, {"id": "ev-04", "source": "kubectl_get_by_kind_in_namespace", "content": "aiops-e2e 命名空间下仅有 kube-root-ca.crt 1 个 ConfigMap，无 rc-definitely-missing-configmap", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "集群 65 Pods，59 Running，仅此 1 个异常，labels 含 pod_abnormal_type=VolumeMountFailed", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "ev-01", "raw_data": "Warning FailedMount 66s (x21 over 27m) kubelet MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found", "interpretation": "kubelet 明确报告卷挂载失败，原因是引用的 ConfigMap 不存在。该事件持续 27 分钟未消退，证明问题持续存在而非瞬时波动。"}, {"evidence_id": "ev-02", "raw_data": "kubectl get -A --show-labels -o wide configmap | grep -i 'rc-definitely-missing-configmap' → exit 1", "interpretation": "全集群范围搜索该 ConfigMap 均未找到，证明该资源在任何命名空间下都未被创建。"}, {"evidence_id": "ev-03", "raw_data": "volumes: [{\"name\": \"missing-config\", \"configMap\": \"rc-definitely-missing-configmap\"}]且 Optional: false", "interpretation": "Pod 声明了一个非可选的 ConfigMap 卷挂载，Kubernetes 要求该 ConfigMap 必须存在才能启动容器，缺失则 Pod 卡在 ContainerCreating。"}, {"evidence_id": "ev-04", "raw_data": "kubectl_get_by_kind_in_namespace: rows=1, NAME=kube-root-ca.crt, AGE=117d", "interpretation": "aiops-e2e 命名空间下只有系统自动注入的 kube-root-ca.crt ConfigMap，不存在目标 ConfigMap，排除命名空间写错但实际存在的可能性。"}, {"evidence_id": "layer_1", "raw_data": "status_counts={'Running': 59}, total_abnormal=1", "interpretation": "集群整体健康，仅此 1 个 Pod 异常，属于局部配置问题而非基础设施故障。"}], "causal_chain": {"root_cause": "ConfigMap rc-definitely-missing-configmap 在 aiops-e2e 命名空间及全集群中不存在（从未被创建或已被删除）", "propagation": "ConfigMap 不存在 → kubelet 尝试挂载 volume missing-config 时获取 ConfigMap 数据失败 → MountVolume.SetUp failed → 卷挂载不满足 → Pod 无法进入 Running 状态 → 容器停留在 ContainerCreating → 30s 超时后变为 Unable to attach or mount volumes → Pod 持续 Pending", "direct_cause": "Pod spec volumes[0].configMap.name=rc-definitely-missing-configmap 指向一个不存在的 ConfigMap，且 Optional=false", "manifestation": "Pod rc-volume-missing-configmap 在 aiops-e2e 命名空间中 0/1 ready，状态 Pending/ContainerCreating，kubelet 持续报 FailedMount configmap not found"}, "root_cause": "Pod rc-volume-missing-configmap (aiops-e2e) 卡在 Pending/ContainerCreating 已 27 分钟，根因是 volume \"missing-config\" 引用的 ConfigMap \"rc-definitely-missing-configmap\" 不存在。kubectl describe 显示 FailedMount 事件重复 21 次（最新 66s 前）：MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found。kubectl_find_resource 全集群搜索返回 exit code 1（未找到），aiops-e2e 命名空间下仅有系统注入的 kube-root-ca.crt。Pod YAML 确认该 volume 的 Optional=false，即非可选卷，必须存在才能启动容器。集群其他 59 个 Pod 均正常运行，属局部配置问题。", "root_cause_summary": "Pod rc-volume-missing-configmap (aiops-e2e) 卡在 Pending/ContainerCreating 已 27 分钟，根因是 volume \"missing-config\" 引用的 ConfigMap \"rc-definitely-missing-configmap\" 不存在。kubectl describe 显示 FailedMount 事件重复 21 次（最新 66s 前）：MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found。kubectl_find_resource 全集群搜索返回 exit code 1（未找到），aiops-e2e 命名空间下仅有系统注入的 kube-root-ca.crt。Pod YAML 确认该 volume 的 Optional=false，即非可选卷，必须存在才能启动容器。集群其他 59 个 Pod 均正常运行，属局部配置问题。", "confidence": 0.97, "confidence_reason": "四条核心证据（kubectl_describe Event、kubectl_find_resource 全集群搜索、kubectl_get_yaml 确认 Optional=false、kubectl_get_by_kind_in_namespace 确认命名空间下无该 ConfigMap）全部指向同一个结论，证据链完整且无矛盾，因果链清晰。扣 0.03 因为无法 100% 确定是\"从未创建\"还是\"被删除\"，但这对当前故障诊断结论无影响。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [{"cause": "ConfigMap 名称拼写错误——Pod spec 中写错了名称但实际有另一个名称不同的 ConfigMap 存在", "probability": "low", "reason": "kubectl_find_resource 全集群搜索 rc-definitely-missing-configmap 返回 exit 1，确实不存在；且命名空间下仅有 kube-root-ca.crt，排除拼写错误导致名称不匹配的场景"}, {"cause": "ConfigMap 存在于其他命名空间但 Pod 未指定正确命名空间引用", "probability": "low", "reason": "Pod 引用 ConfigMap 时如果未指定 namespace 则默认使用 Pod 所在 namespace（aiops-e2e）；kubectl_find_resource 全集群搜索未找到，且 ConfigMap 跨命名空间引用不被 kubelet 支持，排除此场景"}, {"cause": "RBAC 权限不足导致 kubelet 无法读取 ConfigMap", "probability": "low", "reason": "Events 报的是 'not found' 而非 'forbidden'，且 kubectl（使用用户凭据）也找不到该 ConfigMap，证明资源确实不存在而非权限问题"}], "limitations": "无法区分 ConfigMap 是\"从未被创建\"还是\"曾经存在后被删除\"——但这两种场景的修复方式相同（重新创建 ConfigMap）。kubectl_get_yaml 原始输出被截断（1105 字符），但关键字段已完整提取。未检查 ConfigMap 可能存在于其他命名空间后被删除的 audit log，但对结论无影响。", "llm_raw_analysis": "基于 L0 层级（storage_volume/VolumeMountFailed）进行分析。集群 65 Pods 仅 1 个异常，异常组 g1 只包含 Pod rc-volume-missing-configmap（aiops-e2e），状态 ContainerCreating。上游已按 runbook pod-volume-mount-failed.md 完成 4 条核心证据采集。kubectl_describe 明确报 MountVolume.SetUp failed: configmap not found，kubectl_find_resource 全集群搜索确认不存在，kubectl_get_yaml 确认 Optional=false，kubectl_get_by_kind_in_namespace 确认命名空间下仅 kube-root-ca.crt。根因清晰：Pod 引用的 ConfigMap 缺失导致卷挂载失败。非主异常组无其他异常 Pod 需验证。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-volume-missing-configmap (aiops-e2e) 卡在 Pending/ContainerCreating 已 27 分钟，根因是 volume "missing-config" 引用的 ConfigMap "rc-definitely-missing-conf...
   置信度: 97%
   🔗 因果链:
     根本原因: ConfigMap rc-definitely-missing-configmap 在 aiops-e2e 命名空间及全集群中不存在（从未被创建或已被删除）
     传导机制: ConfigMap 不存在 → kubelet 尝试挂载 volume missing-config 时获取 ConfigMap 数据失败 → MountVolume.SetUp failed → 卷挂载不满足 → Pod 无法进入 Running 状态 → 容器停留在 ContainerCreating → 30s 超时后变为 Unable to attach or mount volumes → Pod 持续 Pending
     最终表现: Pod rc-volume-missing-configmap 在 aiops-e2e 命名空间中 0/1 ready，状态 Pending/ContainerCreating，kubelet 持续报 FailedMount configmap not found


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (16.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5905 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 8.3s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将根据您提供的完整诊断信息，生成一份详尽、完整的诊断报告。

---
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **集群当前状态** | 集群中共有 65 个 Pod，其中 **59 个运行正常**，1 个异常。 |
| **发现的问题** | 位于 `aiops-e2e` 命名空间的 Pod `rc-volume-missing-configmap` 处于 **ContainerCreating** 状态，无法正常运行。 |
| **Pod异常状态** | ContainerCreating |
| **兼容归因层** | L0 - storage_volume |
| **问题分类** | VolumeMountFailed |
| **置信度** | 高 (97%) |
| **证据完整度** | 3/4 (75%) |

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 异常 Pod | rc-volume-missing-configmap |
| Namespace | aiops-e2e |
| 节点 | node1 (10.2.0.49) |
| 错误信息 | `MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found` |
| 缺失的资源 | ConfigMap `rc-definitely-missing-configmap` |

---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 事件 | kubectl describe pod | `Warning FailedMount 44s (x21 over 27m) kubelet MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found` | **核心证据**：kubelet 明确报告卷挂载失败原因是 ConfigMap 不存在。 |
| 2 | 资源验证 | kubectl_find_resource / kubectl_get_by_kind_in_namespace | `kubectl_find_resource` 全集群搜索`rc-definitely-missing-configmap`返回 exit code 1；`aiops-e2e` 命名空间下仅有自动注入的 `kube-root-ca.crt` ConfigMap。 | 确凿证实 ConfigMap `rc-definitely-missing-configmap` 在整个集群中都不存在。 |
| 3 | Pod 配置 | kubectl_get_yaml | Pod 的 Volume 配置中明确引用 `configMap.name: rc-definitely-missing-configmap`，且 `Optional` 字段值为 `false` 或未设置（默认为 false）。 | 确认 Pod 依赖一个必须存在的 ConfigMap，且该 ConfigMap 不存在，导致挂载失败。 |
| 4 | 集群整体状态 | kubectl_get_by_kind_in_cluster | 集群中共 65 个 Pod，其中 `Running: 59`，`abnormal: 1`。 | 确认问题为**局部配置问题**，非集群规模性故障。 |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：Pod 配置要求挂载一个名为 `rc-definitely-missing-configmap` 的 ConfigMap（ev-03），但该 ConfigMap 在集群中并不存在（ev-02），导致 kubelet 无法完成挂载并报错（ev-01）。
- **证据链**：Pod 启动 → kubelet 尝试挂载卷 `missing-config` → 从 API Server 获取 ConfigMap 数据 → 资源不存在 → 挂载失败 → Pod 卡在 `ContainerCreating` 状态。

### 缺失证据（如有）
| 证据 | 级别 | 影响 | 原因 |
|------|------|------|------|
| 获取 `aiops-e2e` 命名空间下完整的 ConfigMap 列表 | important | 低。虽然未采集，但 `kubectl_find_resource` 的 `grep` 全集群搜索失败已足够证明其不存在。 | 执行 `kubectl_get_by_kind_in_namespace ConfigMap` 时，未找到与 `rc-definitely-missing-configmap` 匹配的结果。 |

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                    │
│ 必要的 ConfigMap 资源 rc-definitely-missing-configmap 在 aiops-e2e 命名空间 │
│ 及整个集群中不存在（从未被创建或已被删除）                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                    │
│ Pod 启动 → kubelet 读取 Pod Spec → 发现需要挂载一个 ConfigMap 卷 →         │
│ 向 API Server 请求该 ConfigMap 数据 → 资源不存在 → 返回错误                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                    │
│ kubelet 无法挂载卷 "missing-config"，因为其引用的 ConfigMap                 │
│ "rc-definitely-missing-configmap" 不存在。                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                │
│ Pod rc-volume-missing-configmap 状态为 ContainerCreating，持续 27 分钟。    │
│ kubectl describe 持续显示 FailedMount 错误。                              │
└─────────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #1（FailedMount 事件）、证据 #2（ConfigMap 不存在）和证据 #3（Pod Spec 引用），
问题的根本原因是 **Pod `rc-volume-missing-configmap` 的卷定义中引用的 ConfigMap `rc-definitely-missing-configmap` 在命名空间 `aiops-e2e` 甚至整个集群中都不存在**，导致卷挂载失败，Pod 无法进入 Running 状态。

**置信度**：高 (97%)
- ✅ `kubectl describe` 明确报告 `ConfigMap not found` 错误。
- ✅ 全集群搜索证实该 ConfigMap 确实不存在。
- ✅ 集群内其他 59 个 Pod 运行正常，排除集群级别故障。

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [唯一方案] 创建缺失的 ConfigMap**
该 ConfigMap 必须包含您的应用期望读取的配置数据。如果只是为了让 Pod 启动以进行调试，可以先创建一个空的 ConfigMap。

**创建空 ConfigMap（用于快速恢复 Pod 运行）：**
```bash
kubectl create configmap rc-definitely-missing-configmap -n aiops-e2e --from-literal=key=placeholder-value
```

**创建包含实际配置的 ConfigMap（推荐）：**
请将 `config-file.yaml` 替换为您的实际配置文件。
```bash
kubectl create configmap rc-definitely-missing-configmap -n aiops-e2e --from-file=config-file.yaml
```

*依据*：证据 #2 确认 ConfigMap 缺失，创建后 Pod kubelet 可以成功挂载该卷。

**2. 验证 Pod 是否恢复正常**
创建 ConfigMap 后，Pod 应该会自动从 `ContainerCreating` 状态转换为 `Running`。
```bash
kubectl get pod rc-volume-missing-configmap -n aiops-e2e -w
```

### 后续优化
1. **审查应用部署流程**：检查您的部署 YAML 或 Helm Chart，确保在部署 Pod 之前，所需的 ConfigMap 已被创建。可以考虑使用 `helm --pre-install` hook 或自动化流水线来确保资源创建的顺序。
2. **配置审计**：审查 `rc-volume-missing-configmap` 的 YAML 定义，确认引用的 ConfigMap 名称是否拼写正确。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 执行修复命令 | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` | ConfigMap 已存在 |
| 2. 确认 Pod 运行 | `kubectl get pod rc-volume-missing-configmap -n aiops-e2e` | STATUS: Running |
| 3. 检查无新事件 | `kubectl describe pod rc-volume-missing-configmap -n aiops-e2e \| grep -A5 FailedMount` | 无 FailedMount 事件输出 |

---
## ⚠️ 注意事项
- **重要**：此问题完全是**配置缺失**导致，与集群健康、节点故障、网络问题等无关。集群本身运行良好。
- 创建空的 ConfigMap 可能不会破坏 Pod 启动，但如果应用尝试读取其中的配置数据，可能会引发应用级别的错误。请根据实际情况创建正确的 ConfigMap。
- 如果 Pod 在 `ContainerCreating` 状态等待时间过长（已超过 27 分钟），创建 ConfigMap 后，可能需要短暂等待才能转为 `Running`。如果长时间无变化，可尝试删除 Pod 让其重建：
  ```bash
  kubectl delete pod rc-volume-missing-configmap -n aiops-e2e
  ```

---

## 📊 性能统计

├─ 总耗时: 1.1m
├─ 问题定位: 18.7s (27%) ✅
├─ 证据链采集: 15.7s (23%) ✅
├─ 根因分析: 17.1s (25%) ✅
├─ 汇总总结: 16.8s (25%) ✅
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
