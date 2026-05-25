======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: a6c56a2f15584b72]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我先来扫描整个集群的所有 Pod，看看有没有异常状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59}
NAMESPACE         NAME                                                READY   STATUS              RESTARTS       A
   💭 [问题定位] 发现了一个异常 Pod。让我进一步查看它的详情。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-volume-missing-configmap   0/1     ContainerCreating   0       
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-missing-configmap
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  13s (x6 over 29s)  kubelet            MountVolume.SetUp
   💭 [问题定位] 现在让我获取与此异常类型匹配的 runbook。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] Runbook 已经明确指出了问题。我来再确认一下 ConfigMap 是否存在。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=1 abnormal=0 status_counts={}
NAME               DATA   AGE    LABELS
# 样例行
kube-root-ca.crt   1      117d   <none>
   💭 [问题定位] 很好，我已经掌握了所有必要的信息。现在进行最终分析输出。

## 诊断分析

### 全局 Pod 状态扫描结果

| 状态 | 数量 |
|------|------|
| Running | 59 |
| **异常 (ContainerCreating)** | **1** |

集群中 59 个 Pod 正常运行，仅发现 **1 个异常 Pod**。

---

### 异常 Pod 详情

| 字段 | 值 |
|------|-----|
| **Pod** | `rc-volume-missing-configmap` |
| **命名空间** | `aiops-e2e` |
| **状态** | `ContainerCreating`（卡在容器创建阶段） |
| **Node** | `node1` |
| **镜像** | `busybox:1.36` |

### 关键事件证据
```
Warning  FailedMount  13s (x6)  kubelet  
MountVolume.SetUp failed for volume "missing-config" : 
configmap "rc-definitely-missing-configmap" not found
```

### 根本原因
Pod 引用了名为 `missing-config` 的 **ConfigMap volume**，该 volume 对应的 ConfigMap `rc-definitely-missing-configmap` **在集群中不存在**。当前 `aiops-e2e` 命名空间中只有 kube-root-ca.crt 这一个 ConfigMap，没有找到目标 ConfigMap。

---

### LayerOutput 结构化结果

- **layer**: L0
- **derived_layer**: L0
- **layers**: ["L0"]
- **layer_name**: 卷挂载失败 — ConfigMap Volume 缺失
- **confidence**: 高
- **reasoning**: Pod `rc-volume-missing-configmap` 处于 ContainerCreating 状态，Events 明确显示 `MountVolume.SetUp failed`，原因是 ConfigMap `rc-definitely-missing-configmap` 不存在。根据分层映射规则，VolumeMountFailed 归入 L0。
- **pod_status_keyword**: ContainerCreating
- **pod_abnormal_type**: VolumeMountFailed
- **status_category**: storage_volume
- **abnormal_pods**: [`rc-volume-missing-configmap (aiops-e2e)`]
- **abnormal_groups**: {"VolumeMountFailed": ["rc-volume-missing-configmap"]}
- **key_entities**: {
    "Pod": "rc-volume-missing-configmap@aiops-e2e",
    "Node": "node1",
    "Missing ConfigMap": "rc-definitely-missing-configmap"
  }
- **possible_scenarios**: [
    "ConfigMap `rc-definitely-missing-configmap` 尚未被创建",
    "ConfigMap 名称拼写错误或来自其他命名空间",
    "ConfigMap 已被删除或未随应用部署一起提交"
  ]

### 后续审查方向（交由下游 evidence 节点执行）
1. 确认 `rc-definitely-missing-configmap` 是否应该存在于 `aiops-e2e` 命名空间
2. 检查应用部署清单中的 ConfigMap 名称是否正确
3. 如需修复：创建缺失的 ConfigMap 或更正 Pod volume 引用名称
   ✅ [问题定位] 完成 (19.9s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[{'scenario': 'ConfigMap `rc-definitely-missing-configmap` 尚未被创建', 'probability': '高', 'reason': '当前 aiops-e2e 命名空间下不存在该 ConfigMap，且无其他同名资源'}, {'scenario': 'ConfigMap 名称拼写错误或引用了其他命名空间的对象', 'probability': '中', 'reason': 'Pod 中 volume 引用的名称与未创建的 ConfigMap 同名，可能存在拼写错误'}, {'scenario': 'ConfigMap 已被管理员删除或未随应用部署提交', 'probability': '低', 'reason': '需要进一步确认应用部署历史'}]
   entities=[{"type": "Pod", "name": "rc-volume-missing-configmap", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "ConfigMap", "name": "rc-definitely-missing-configmap", "namespace": "aiops-e2e"}]
   reasoning=Pod `rc-volume-missing-configmap` (namespace `aiops-e2e`) 当前仍处于 ContainerCreating 状态，Events 明确显示 `MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found`。Pod spec 中 volumes 引用了名为 `missing-config` 的 ConfigMap volume，其 name 为 `rc-definitely-missing-configmap`，经查询 `aiops-e2e` 命名空间下只存在 `kube-root-ca.crt` 一个 ConfigMap，目标 ConfigMap 确实不存在。根据分层规则，VolumeMountFailed 由 ConfigMap/Secret 缺失引起归入 L0（storage_volume）。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "卷挂载失败 — ConfigMap Volume 缺失", "confidence": 0.98, "reasoning": "Pod `rc-volume-missing-configmap` (namespace `aiops-e2e`) 当前仍处于 ContainerCreating 状态，Events 明确显示 `MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found`。Pod spec 中 volumes 引用了名为 `missing-config` 的 ConfigMap volume，其 name 为 `rc-definitely-missing-configmap`，经查询 `aiops-e2e` 命名空间下只存在 `kube-root-ca.crt` 一个 ConfigMap，目标 ConfigMap 确实不存在。根据分层规则，VolumeMountFailed 由 ConfigMap/Secret 缺失引起归入 L0（storage_volume）。", "abnormal_pods": [{"name": "rc-volume-missing-configmap", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "Pod", "name": "rc-volume-missing-configmap", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "ConfigMap", "name": "rc-definitely-missing-configmap", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "ConfigMap `rc-definitely-missing-configmap` 尚未被创建", "probability": "高", "reason": "当前 aiops-e2e 命名空间下不存在该 ConfigMap，且无其他同名资源"}, {"scenario": "ConfigMap 名称拼写错误或引用了其他命名空间的对象", "probability": "中", "reason": "Pod 中 volume 引用的名称与未创建的 ConfigMap 同名，可能存在拼写错误"}, {"scenario": "ConfigMap 已被管理员删除或未随应用部署提交", "probability": "低", "reason": "需要进一步确认应用部署历史"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-configmap"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-missing-configmap"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-volume-missing-configmap                         0/1     ContainerCreating   0              27s     <none>           node1    <none>           <none>            app=rc-volume-missing-configmap,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/a6c56a2f15584b72/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/a6c56a2f15584b72/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/a6c56a2f15584b72/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 98%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来执行既有 evidence_plan 中的关键工具，验证 Pod `rc-volume-missing-configmap` 的 ConfigMap volume 缺失根因。

先获取 Pod describe 确认当前事件状态：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_get_yaml
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
  Warning  FailedMount  27s (x7 over 59s)  kubelet            MountVolume.SetUp
   💭 [证据链采集] 现在获取 Pod 的完整事件序列：
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
29s (x7 over 61s)   Warning   FailedMount   Pod/rc-volume-missing-configmap   MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configma
   💭 [证据链采集] ## 证据采集结论

### ✅ 已采集证据（全部基于真实工具结果）

| 项目 | 证据 | 说明 |
|------|------|------|
| **e1 - Pod Events 验证** | `kubectl describe pod` 显示 `Warning FailedMount` 27s (x7 over 59s)，原文：`MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found` | ✅ 关键错误原文已确认，与上游一致 |
| **e2 - ConfigMap 缺失验证** | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` 返回 **`Error from server (NotFound)`** | ✅ ConfigMap 确实不存在，根因确认 |
| **e3 - Pod spec volume 引用验证** | Pod YAML 中 `volumes[0].configMap.name = "rc-definitely-missing-configmap"`，且 `optional: false`（非可选） | ✅ 非可选 ConfigMap volume 引用缺失对象，Pod 无法启动 |
| **e4 - 完整事件序列** | 仅有 1 类事件：`FailedMount` x7 次，均指向同一 ConfigMap not found | ✅ 无其他异常事件干扰 |

### ❌ 未采集证据 / 冲突证据
- **无冲突证据**：所有真实工具结果与上游定位完全一致。

### 根因结论
Pod `rc-volume-missing-configmap`（`aiops-e2e` 命名空间）卡在 **ContainerCreating/Pending** 状态，根本原因是其 volume `missing-config` 引用了 **ConfigMap `rc-definitely-missing-configmap`**，但该 ConfigMap 在当前命名空间中**不存在**（`NotFound`）。由于 `optional: false`，kubelet 无法挂载该卷，Pod 无法进入 Running 状态。
   ✅ [证据链采集] 完成 (20.5s)
   📤 → 下游数据: evidence_items=7/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"Describe Pod rc-volume-missing-configmap 确认当前 MountVolume FailedMount 事件原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-configmap -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-volume-missing-configmap","namespace":"aiops-e2e"},"purpose":"验证 FailedMount 事件原文是否仍为 configmap not found","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"验证 ConfigMap rc-definitely-missing-configmap 在 aiops-e2e 中是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e","tool_args":{"kind":"configmap","name":"rc-definitely-missing-configmap","namespace":"aiops-e2e"},"purpose":"确认 ConfigMap 缺失根因","evidence_type":"resource_exists","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod YAML 确认 volumes 引用配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-volume-missing-configmap","namespace":"aiops-e2e"},"purpose":"确认 spec.volumes 中 ConfigMap 引用名称","evidence_type":"pod_spec","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e4","description":"检查异常 Pod 最近相关事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-missing-configmap --sort-by='.lastTimestamp'","tool_args":{"resource_type":"pod","resource_name":"rc-volume-missing-configmap","namespace":"aiops-e2e"},"purpose":"获取 Pod 相关完整事件序列","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-missing-configmap\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T03:33:04Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-missing-configmap, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"missing-config\", \"configMap\": \"rc-definitely-missing-configmap\"}\n- {\"name\": \"kube-api-access-h7lqz\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a6c56a2f15584b72/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a6c56a2f15584b72/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a6c56a2f15584b72/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=199 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide configmap rc-definitely-missing-configmap -n aiops-e2e\nError from server (NotFound): configmaps \"rc-definitely-missing-configmap\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/a6c56a2f15584b72/tools/002-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a6c56a2f15584b72/tools/002-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a6c56a2f15584b72/tools/002-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-missing-configmap\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  27s (x7 over 59s)  kubelet            MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  missing-config:\n    Type:      ConfigMap (a volume populated by a ConfigMap)\n    Name:      rc-definitely-missing-configmap\n    Optional:  false\n  kube-api-access-h7lqz:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedMount  27s (x7 over 59s)  kubelet            MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a6c56a2f15584b72/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a6c56a2f15584b72/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a6c56a2f15584b72/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n29s (x7 over 61s)   Warning   FailedMount   Pod/rc-volume-missing-configmap   MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a6c56a2f15584b72/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a6c56a2f15584b72/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a6c56a2f15584b72/tools/004-evidence-kubectl_events.summary.txt"}],"llm_analysis":"## 证据采集结论\n\n### ✅ 已采集证据（全部基于真实工具结果）\n\n| 项目 | 证据 | 说明 |\n|------|------|------|\n| **e1 - Pod Events 验证** | `kubectl describe pod` 显示 `Warning FailedMount` 27s (x7 over 59s)，原文：`MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found` | ✅ 关键错误原文已确认，与上游一致 |\n| **e2 - ConfigMap 缺失验证** | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` 返回 **`Error from server (NotFound)`** | ✅ ConfigMap 确实不存在，根因确认 |\n| **e3 - Pod spec volume 引用验证** | Pod YAML 中 `volumes[0].configMap.name = \"rc-definitely-missing-configmap\"`，且 `optional: false`（非可选） | ✅ 非可选 ConfigMap volume 引用缺失对象，Pod 无法启动 |\n| **e4 - 完整事件序列** | 仅有 1 类事件：`FailedMount` x7 次，均指向同一 ConfigMap not found | ✅ 无其他异常事件干扰 |\n\n### ❌ 未采集证据 / 冲突证据\n- **无冲突证据**：所有真实工具结果与上游定位完全一致。\n\n### 根因结论\nPod `rc-volume-missing-configmap`（`aiops-e2e` 命名空间）卡在 **ContainerCreating/Pending** 状态，根本原因是其 volume `missing-config` 引用了 **ConfigMap `rc-definitely-missing-configmap`**，但该 ConfigMap 在当前命名空间中**不存在**（`NotFound`）。由于 `optional: false`，kubelet 无法挂载该卷，Pod 无法进入 Running 状态。","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 7/8 项，完整度 88%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":8,"environment_evidence_collected":7,"environment_evidence_completeness":0.875,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"Describe Pod rc-volume-missing-configmap 确认当前 MountVolume FailedMount 事件原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-missing-configmap -n aiops-e2e","purpose":"验证 FailedMount 事件原文是否仍为 configmap not found","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证 ConfigMap rc-definitely-missing-configmap 在 aiops-e2e 中是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e","purpose":"确认 ConfigMap 缺失根因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取 Pod YAML 确认 volumes 引用配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml","purpose":"确认 spec.volumes 中 ConfigMap 引用名称","collected":false,"source":"planned","outcome":"unknown"},{"id":"e4","description":"检查异常 Pod 最近相关事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-missing-configmap --sort-by='.lastTimestamp'","purpose":"获取 Pod 相关完整事件序列","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e3(获取 Pod YAML 确认 volumes 引用配置): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 88%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | Describe Pod rc-volume-missing-configmap 确认当前... | `kubectl describe pod rc-volume-missing-configmap -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_by_name | 验证 ConfigMap rc-definitely-missing-configmap ... | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` |
   | e3 | important | ❌ | kubectl_get_yaml | 获取 Pod YAML 确认 volumes 引用配置 | `kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml` |
   | e4 | important | ✅ | kubectl_events | 检查异常 Pod 最近相关事件 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volum...` |

   ⚠️ 未采集原因:
   - e3(获取 Pod YAML 确认 volumes 引用配置): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (17.4s)
   📤 → 下游数据: root_cause=Pod `rc-volume-missing-configmap` (namespace `aiops-e2e`) 卡在 ContainerCreating/Pending 状态，根本原因是其 volume `missing-config`（非可选卷，optional=false）引用了 ConfigMap `rc-definitely-missing-configmap`，但该 ConfigMap 在当前命名空间中不存在。证据：kubectl describe 显示 `Warning FailedMount 27s (x7 over 59s)` — `MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found`；直接查询 `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` 返回 `NotFound`；该命名空间下仅有系统自动注入的 `kube-
... 截断，原始 556 字符
   confidence=98%
   causal_chain={"root_cause": "ConfigMap `rc-definitely-missing-configmap` 在命名空间 `aiops-e2e` 中不存在（从未创建或已被删除）", "propagation": "Pod spec volumes 中声明了非可选（optional=false）ConfigMap volume `missing-config` 引用该 ConfigMap → kubelet 在调度 Pod 到 node1 后尝试挂载该卷 → 在命名空间中查找 ConfigMap 失败 → 重复重试（7 次 over ~1 分钟）→ 持续报 FailedMount", "direct_cause": "kubelet 无法挂载 volume `missing-config`，因为其引用的 ConfigMap `rc-definitely-missing-configmap` 返回 NotFound", "manifestation": "Pod `rc-volume-missing-configmap` 卡在 ContainerCreating/Pending 状态，0/1 Ready，无 IP 分配，容器处于 Waiting(ContainerCreating) 状态"}
   rca_analysis={"phenomenon": "Pod `rc-volume-missing-configmap` (namespace `aiops-e2e`) 当前处于 ContainerCreating/Pending 状态，无法进入 Running。集群共 65 个 Pod，仅此 1 个异常。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Warning FailedMount 27s (x7 over 59s) kubelet: MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml", "content": "Pod YAML volumes[0]: name=missing-config, configMap.name=rc-definitely-missing-configmap, optional=false", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_by_name", "content": "kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e → Error from server (NotFound)", "reliability": "高"}, {"id": "e4", "source": "kubectl_get_by_kind_in_namespace", "content": "aiops-e2e 命名空间下仅存在 kube-root-ca.crt 一个 ConfigMap，无 rc-definitely-missing-configmap", "reliability": "高"}, {"id": "e5", "source": "kubectl_get_by_kind_in_cluster", "content": "集群 65 Pod，59 Running，1 ContainerCreating（rc-volume-missing-configmap）", "reliability": "高"}, {"id": "e6", "source": "kubectl_events", "content": "29s (x7 over 61s) Warning FailedMount Pod/rc-volume-missing-configmap: configmap not found", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedMount 27s (x7 over 59s) kubelet MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found", "interpretation": "kubelet 明确报告 volume missing-config 挂载失败，原因是被引用的 ConfigMap rc-definitely-missing-configmap 不存在。该事件已重复 7 次，持续约 1 分钟，说明非瞬时抖动。"}, {"evidence_id": "e2", "raw_data": "volumes: [{\"name\": \"missing-config\", \"configMap\": \"rc-definitely-missing-configmap\"}] 且 optional: false", "interpretation": "Pod spec 中 volume missing-config 引用 ConfigMap rc-definitely-missing-configmap，且 `optional: false`（非可选卷）。kubelet 在缺少该 ConfigMap 时必须阻塞 Pod 启动，不会跳过挂载。"}, {"evidence_id": "e3", "raw_data": "kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e → Error from server (NotFound)", "interpretation": "直接查询确认该 ConfigMap 在目标命名空间中确实不存在。排除了临时 API 缓存或网络抖动导致查询失败的可能。"}, {"evidence_id": "e4", "raw_data": "kubectl get configmap -n aiops-e2e 仅返回 kube-root-ca.crt (1 data, 117d old)", "interpretation": "整个命名空间只有系统自动注入的 kube-root-ca.crt 一个 ConfigMap，无任何用户创建的 ConfigMap。说明 rc-definitely-missing-configmap 从未被创建或已被删除。"}, {"evidence_id": "e5", "raw_data": "rows=65, abnormal=1, status_counts={'Running': 59}", "interpretation": "集群整体健康，59/65 Pod 正常运行，仅此 1 个异常 Pod。该问题为局部故障，不影响集群其他工作负载。"}, {"evidence_id": "e6", "raw_data": "29s (x7 over 61s) Warning FailedMount Pod/rc-volume-missing-configmap", "interpretation": "事件历史与 describe 输出一致，确认 7 次 FailedMount 事件均指向同一 ConfigMap 缺失，无其他类型异常事件。"}], "causal_chain": {"root_cause": "ConfigMap `rc-definitely-missing-configmap` 在命名空间 `aiops-e2e` 中不存在（从未创建或已被删除）", "propagation": "Pod spec volumes 中声明了非可选（optional=false）ConfigMap volume `missing-config` 引用该 ConfigMap → kubelet 在调度 Pod 到 node1 后尝试挂载该卷 → 在命名空间中查找 ConfigMap 失败 → 重复重试（7 次 over ~1 分钟）→ 持续报 FailedMount", "direct_cause": "kubelet 无法挂载 volume `missing-config`，因为其引用的 ConfigMap `rc-definitely-missing-configmap` 返回 NotFound", "manifestation": "Pod `rc-volume-missing-configmap` 卡在 ContainerCreating/Pending 状态，0/1 Ready，无 IP 分配，容器处于 Waiting(ContainerCreating) 状态"}, "root_cause": "Pod `rc-volume-missing-configmap` (namespace `aiops-e2e`) 卡在 ContainerCreating/Pending 状态，根本原因是其 volume `missing-config`（非可选卷，optional=false）引用了 ConfigMap `rc-definitely-missing-configmap`，但该 ConfigMap 在当前命名空间中不存在。证据：kubectl describe 显示 `Warning FailedMount 27s (x7 over 59s)` — `MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found`；直接查询 `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` 返回 `NotFound`；该命名空间下仅有系统自动注入的 `kube-\n... 截断，原始 556 字符", "root_cause_summary": "Pod `rc-volume-missing-configmap` (namespace `aiops-e2e`) 卡在 ContainerCreating/Pending 状态，根本原因是其 volume `missing-config`（非可选卷，optional=false）引用了 ConfigMap `rc-definitely-missing-configmap`，但该 ConfigMap 在当前命名空间中不存在。证据：kubectl describe 显示 `Warning FailedMount 27s (x7 over 59s)` — `MountVolume.SetUp failed for volume \"missing-config\" : configmap \"rc-definitely-missing-configmap\" not found`；直接查询 `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` 返回 `NotFound`；该命名空间下仅有系统自动注入的 `kube-\n... 截断，原始 556 字符", "confidence": 0.98, "confidence_reason": "有直接证据支撑因果链每一环：kubelet Events 明确报错原文（e1）、Pod YAML 确认 volume 引用且非可选（e2）、kubectl get 直接返回 NotFound 确认 ConfigMap 不存在（e3）、命名空间全局 ConfigMap 列表确认无该资源（e4）。所有证据一致且无冲突，置信度 0.98。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [{"cause": "ConfigMap 存在于其他命名空间但因跨命名空间引用限制无法访问", "probability": "low", "reason": "Pod 和 ConfigMap 在同一命名空间 aiops-e2e 中配置，且 kubectl get configmap -n aiops-e2e 确认无此资源；不存在跨命名空间引用场景"}, {"cause": "ConfigMap 名称拼写错误（Pod volume 中拼写与实际创建不一致）", "probability": "low", "reason": "无其他同名 ConfigMap 存在，也无法区分是未创建还是拼写错误；无论哪种情况，修复方式都是创建或修正引用"}, {"cause": "kubelet 节点故障导致无法读取已存在的 ConfigMap", "probability": "low", "reason": "kubectl get 直接返回 NotFound，并非 kubelet 无法读取；且同一节点上其他 Pod 正常运行"}], "limitations": "未采集 ConfigMap 创建历史记录（如 kubectl rollout history 或 Helm release 记录），无法确认该 ConfigMap 是未被创建、已被删除还是部署时遗漏。但该信息不影响当前根因判定——修复措施均为创建该 ConfigMap 或修正 Pod 引用。", "llm_raw_analysis": "L0 根因分析完成。异常组 g1 包含 1 个 Pod `rc-volume-missing-configmap`，状态 ContainerCreating，类型 VolumeMountFailed。因果链完整：ConfigMap 不存在 → kubelet 无法挂载非可选卷 → Pod 阻塞在 ContainerCreating。只有 1 个 issue_group，无其他异常组需要验证。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod `rc-volume-missing-configmap` (namespace `aiops-e2e`) 卡在 ContainerCreating/Pending 状态，根本原因是其 volume `missing-config`（非可选卷，optional=false）引用了 Confi...
   置信度: 98%
   🔗 因果链:
     根本原因: ConfigMap `rc-definitely-missing-configmap` 在命名空间 `aiops-e2e` 中不存在（从未创建或已被删除）
     传导机制: Pod spec volumes 中声明了非可选（optional=false）ConfigMap volume `missing-config` 引用该 ConfigMap → kubelet 在调度 Pod 到 node1 后尝试挂载该卷 → 在命名空间中查找 ConfigMap 失败 → 重复重试（7 次 over ~1 分钟）→ 持续报 FailedMount
     最终表现: Pod `rc-volume-missing-configmap` 卡在 ContainerCreating/Pending 状态，0/1 Ready，无 IP 分配，容器处于 Waiting(ContainerCreating) 状态


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (20.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6309 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 18.4s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将根据您提供的信息，生成一份详尽、完整的诊断报告。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **集群总体状态** | **基本正常**。集群中 65 个 Pod 中，59 个处于 `Running` 状态。 |
| **唯一问题** | Pod `rc-volume-missing-configmap` (命名空间 `aiops-e2e`) 处于 `ContainerCreating` 状态，因卷挂载失败无法运行。 |
| **Pod异常状态** | `ContainerCreating` |
| **兼容归因层** | `L0` - storage_volume |
| **问题分类** | `VolumeMountFailed` - ConfigMap 缺失 |
| **置信度** | 高 (98%) |
| **证据完整度** | 3/4 (75%) |

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

**状态总结**：您的集群中绝大多数 Pod（59/65）运行正常。目前仅发现 **1 个问题 Pod**，它因为挂载一个不存在的 ConfigMap 而无法启动。

---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod rc-volume-missing-configmap -n aiops-e2e` | `NAME READY STATUS RESTARTS AGE IP NODE`<br>`rc-volume-missing-configmap 0/1 ContainerCreating 0 29s <none> node1` | Pod 正在等待容器创建。 |
| 2 | 卷挂载事件 | `kubectl describe pod rc-volume-missing-configmap -n aiops-e2e` | `Warning FailedMount 27s (x7 over 59s) kubelet MountVolume.SetUp failed for volume "missing-config" : configmap "rc-definitely-missing-configmap" not found` | **核心证据**：kubelet 明确报告卷 `missing-config` 挂载失败，原因是引用的 ConfigMap 不存在。 |
| 3 | ConfigMap 存在性 | `kubectl get configmap rc-definitely-missing-configmap -n aiops-e2e` | `Error from server (NotFound): configmaps "rc-definitely-missing-configmap" not found` | **核心证据**：直接查询该 ConfigMap，返回 `NotFound` 错误。 |
| 4 | Namespace ConfigMap 列表 | `kubectl get configmap -n aiops-e2e` | `NAME DATA AGE`<br>`kube-root-ca.crt 1 117d` | 目标命名空间下仅有一个系统自动创建的 ConfigMap (`kube-root-ca.crt`)，所需ConfigMap确实不存在。 |
| 5 | Pod YAML 关键字段 | `kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o yaml` | `deletionTimestamp: <absent>`<br>`deletionGracePeriodSeconds: None`<br>`finalizers: <none>` | 排除了 Pod 处于 Terminating 状态或被 Finalizer 阻塞的可能性。 |

### 证据关联分析
- **证据 #1 + #2 + #3 + #4 印证**：Pod 状态 (ContainerCreating) + 错误事件 (FailedMount) + ConfigMap 不存在 (NotFound) → 根本原因链清晰：Pod 启动时需要挂载一个卷，该卷引用的 ConfigMap 在集群中缺失，导致 Pod 无法创建。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| Pod YAML 中 `volumes` 完整配置 | low | 虽未直接采集到 Pod YAML，但 `kubectl describe` 和事件信息已经明确了缺失的 ConfigMap 名称 (`rc-definitely-missing-configmap`)，不影响根因判定。 |

---
## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ ConfigMap `rc-definitely-missing-configmap` 在命名空间          │
│ `aiops-e2e` 中不存在（从未创建、已被删除或名称拼写错误）。       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┘
│ 传导机制                                                        │
│ Pod spec 中定义了名为 `missing-config` 的卷（`volume`），        │
│ 它引用了一个不存在的 ConfigMap `rc-definitely-missing-configmap`。│
│ kubelet 在 `node1` 上尝试创建并挂载该卷时，                      │
│ 在命名空间 `aiops-e2e` 中查询该 ConfigMap 失败。                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 直接原因                                                        │
│ kubelet 无法挂载卷 `missing-config`，返回错误：                  │
│ `configmap "rc-definitely-missing-configmap" not found`.         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┘
│ 用户可见现象                                                    │
│ Pod `rc-volume-missing-configmap` 卡在 `ContainerCreating` 状态，│
│ 0/1 就绪，无 IP 地址分配。                                      │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (FailedMount 事件) 和证据 #3 (ConfigMap 查询返回 NotFound)，问题的根本原因是 **Pod `rc-volume-missing-configmap` 的卷定义引用了命名空间 `aiops-e2e` 中一个不存在的 ConfigMap `rc-definitely-missing-configmap`**。
**置信度**：高 (98%)
- ✅ kubelet 错误事件直接指向缺失的 ConfigMap。
- ✅ 直接查询证实该 ConfigMap 确实不存在。
- ❌ 缺少配置部署历史，无法确认该 ConfigMap 是原本就没创建、被删除还是拼写错误。

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）
**1. [优先] 创建缺失的 ConfigMap**
根据 Pod 预期要挂载的配置内容，创建 ConfigMap `rc-definitely-missing-configmap`。
```bash
# 示例：创建一个空的 ConfigMap 以快速恢复 Pod
kubectl create configmap rc-definitely-missing-configmap -n aiops-e2e
```
*依据*：证据 #2 和 #3 明确指示 ConfigMap 缺失。创建后，kubelet 会自动重试挂载，Pod 状态将自动从 `ContainerCreating` 恢复。
*注意*：如果 Pod 依赖 ConfigMap 中的特定数据（如配置文件），请确保使用 `--from-file` 或 `--from-literal` 参数提供实际内容。例如：
```bash
# 从文件创建（推荐）
kubectl create configmap rc-definitely-missing-configmap -n aiops-e2e --from-file=myconfig.conf
```

**2. [如果名称拼写错误] 修正 Pod 配置**
如果发现是 Pod YAML 中 ConfigMap 名称拼写错误，例如，正确的 ConfigMap 是 `rc-definitely-existing-configmap`，则需要更新 Pod 所属的控制器（如 Deployment）来修正。假设 Pod 由 Deployment 管理：
```bash
# 首先检查 Pod 的控制器
kubectl get pod rc-volume-missing-configmap -n aiops-e2e -o jsonpath='{.metadata.ownerReferences[0].name}'

# 如果输出是 'rc-volume-missing-configmap'（无控制器），需要手动删除并重新创建
kubectl delete pod rc-volume-missing-configmap -n aiops-e2e
# 然后重新编辑并创建 Pod YAML，修正 ConfigMap 名称

# 如果输出是一个 Deployment 名称（例如 'my-deployment'），编辑 Deployment 修正引用
kubectl edit deployment <deployment-name> -n aiops-e2e
# 在 volumes 部分修正 configMap 的 name 字段
```

### 后续优化
1. **配置管理审核**：评估应用部署和配置管理流程，确保所有应用依赖的资源（如 ConfigMap、Secret）在部署前已创建。
2. **CI/CD 管道检查**：在持续集成/持续部署管道中增加环境及配置一致性检查。
3. **名称规范**：统一 Pod、卷和 ConfigMap 的命名规范，降低因名称拼写错误导致的问题概率。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 创建 ConfigMap | `kubectl create configmap rc-definitely-missing-configmap -n aiops-e2e` | `configmap/rc-definitely-missing-configmap created` |
| 2. 检查 Pod 状态 | `kubectl get pod rc-volume-missing-configmap -n aiops-e2e` | 短暂延迟后，STATUS 变为 `Running`，READY 变为 `1/1` |
| 3. 检查 Pod 事件 | `kubectl describe pod rc-volume-missing-configmap -n aiops-e2e` | `FailedMount` 事件消失，出现 `Successfully mounted` 或 `Pulled` 等正常事件 |

---
## ⚠️ 注意事项
- 如果创建 ConfigMap 后 Pod 仍不恢复，请使用 `kubectl describe pod rc-volume-missing-configmap -n aiops-e2e` 检查最新事件。
- 创建 ConfigMap 时，请确保其内容与 Pod 期望挂载的数据一致（如文件内容和 Key 名称），否则容器应用可能会因读取不到正确配置而崩溃。

---

## 📊 性能统计

├─ 总耗时: 1.3m
├─ 问题定位: 19.9s (25%) ✅
├─ 证据链采集: 20.5s (26%) ✅
├─ 根因分析: 17.4s (22%) ✅
├─ 汇总总结: 20.7s (26%) ✅
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
