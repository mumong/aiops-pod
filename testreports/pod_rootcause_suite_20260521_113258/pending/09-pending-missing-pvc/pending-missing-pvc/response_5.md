======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 94285eaabc0641a1]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先来全局扫描一下所有 Pod 的状态，看看当前集群中有哪些异常。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 很好，我看到有异常情况了。让我进一步查看这个 Pending Pod 的详细信息。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-missing-pvc
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  3m14s  default-scheduler  0/3 nodes are available: persistentvol
   💭 [问题定位] 现在情况很清楚了。让我获取对应的 runbook 来做参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 但当前异常实际上是 PVC 找不到导致的，让我也获取卷挂载失败的 runbook。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] 现在让我再快速确认一下 PVC 的状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。
   💭 [问题定位] 好的，所有信息都已收集完毕。下面是我的分析报告。

---

## 诊断分析报告

### 全局 Pod 状态概览

我扫描了集群中所有命名空间的 Pod（共 65 个），发现 **1 个异常 Pod**，其余 59 个 Pod 均为 Running 状态。

---

### 当前异常 Pod

| Pod | 命名空间 | 状态 | 异常类型 |
|-----|---------|------|---------|
| `rc-pending-missing-pvc` | `aiops-e2e` | **Pending** | **VolumeMountFailed** (PVC 未找到) |

---

### 详细分析

**Pod**: `rc-pending-missing-pvc` (命名空间: `aiops-e2e`)

**状态**: Pending，未调度到任何节点（nodeName = `<none>`）

**关键事件**:
```
Warning  FailedScheduling  default-scheduler
0/3 nodes are available: persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found.
```

**Pod Volume 配置**:
- 引用了名为 `rc-pending-definitely-missing-pvc` 的 PersistentVolumeClaim
- 类型为 `PersistentVolumeClaim` 卷

**PVC 状态**: 该命名空间下**不存在**名为 `rc-pending-definitely-missing-pvc` 的 PVC。

### 根因判定

Pod 引用的 PVC `rc-pending-definitely-missing-pvc` **不存在**（未创建或已被删除），导致调度器无法绑定卷，Pod 卡在 Pending 状态。

| 维度 | 值 |
|------|-----|
| **layer** | L0 |
| **layer_name** | VolumeMountFailed |
| **pod_abnormal_type** | `VolumeMountFailed` |
| **pod_status_keyword** | `Pending` |
| **status_category** | `storage_volume` |
| **置信度** | 高（Events 原文明确显示 PVC not found） |

### 异常分组

- `abnormal_groups`:
  - `Pending` (1 个 Pod: `rc-pending-missing-pvc`)
  - `VolumeMountFailed` (1 个 Pod: `rc-pending-missing-pvc`)

### 建议修复方向

1. **创建 PVC**：在 `aiops-e2e` 命名空间中创建一个名为 `rc-pending-definitely-missing-pvc` 的 PersistentVolumeClaim，并确保对应的 PV 或 StorageClass 可用。
2. **修正 Pod 配置**：如果 PVC 名称写错了，修改 Pod spec 中的 `claimName` 指向正确的 PVC。
3. 或者如果这个 Pod 只是测试用例不需要存储，移除 volume 中对缺失 PVC 的引用。
   ✅ [问题定位] 完成 (20.5s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[{'scenario': 'Pod引用的PVC rc-pending-definitely-missing-pvc不存在', 'probability': '高', 'reason': "Events原文明确显示persistentvolumeclaim 'rc-pending-definitely-missing-pvc' not found，且kubectl get pvc未找到该PVC"}, {'scenario': 'PVC名称拼写错误或未创建', 'probability': '高', 'reason': 'Pod spec中claimName为rc-pending-definitely-missing-pvc，但集群中不存在同名PVC'}]
   entities=[{"type": "Pod", "name": "rc-pending-missing-pvc", "namespace": "aiops-e2e"}, {"type": "PersistentVolumeClaim", "name": "rc-pending-definitely-missing-pvc", "namespace": "aiops-e2e"}]
   reasoning=集群中存在1个异常Pod rc-pending-missing-pvc（aiops-e2e命名空间），状态为Pending，Events明确显示persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found。Pod引用的PVC不存在，导致调度器无法绑定卷，Pod卡在Pending。根据五层模型，PVC缺失属于存储卷挂载问题，归入L0（Evicted/VolumeMountFailed/磁盘/驱逐层）。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "VolumeMountFailed", "confidence": 0.95, "reasoning": "集群中存在1个异常Pod rc-pending-missing-pvc（aiops-e2e命名空间），状态为Pending，Events明确显示persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found。Pod引用的PVC不存在，导致调度器无法绑定卷，Pod卡在Pending。根据五层模型，PVC缺失属于存储卷挂载问题，归入L0（Evicted/VolumeMountFailed/磁盘/驱逐层）。", "abnormal_pods": [{"name": "rc-pending-missing-pvc", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "Pod", "name": "rc-pending-missing-pvc", "namespace": "aiops-e2e"}, {"type": "PersistentVolumeClaim", "name": "rc-pending-definitely-missing-pvc", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "Pod引用的PVC rc-pending-definitely-missing-pvc不存在", "probability": "高", "reason": "Events原文明确显示persistentvolumeclaim 'rc-pending-definitely-missing-pvc' not found，且kubectl get pvc未找到该PVC"}, {"scenario": "PVC名称拼写错误或未创建", "probability": "高", "reason": "Pod spec中claimName为rc-pending-definitely-missing-pvc，但集群中不存在同名PVC"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-missing-pvc"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-missing-pvc"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-missing-pvc                              0/1     Pending     0              3m12s   <none>           <none>   <none>           <none>            app=rc-pending-missing-pvc,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/94285eaabc0641a1/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/94285eaabc0641a1/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/94285eaabc0641a1/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我将直接执行既有 evidence_plan 中的工具。先同步调用 e1（describe pod）和 e2（get pvc），它们是独立的。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-missing-pvc
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  3m40s  default-scheduler  0/3 nodes are available: persistentvol
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=209 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide pvc rc-pending-definitely-missing-pvc -n aiops-e2e
Error from server (NotFound): persistentvo
   💭 [证据链采集] e1 和 e2 已执行成功。现在执行 e3（获取 Pod YAML 确认 volume 引用）和 e4（列出命名空间下所有 PVC）。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 输出摘要: raw_chars=2917 lines=87
apiVersion: v1
kind: Pod
metadata:
  annotations:
    aiops.e2e/runbook: pod-pending-unschedulable.md
    kubectl.kubernetes.io/last-applied-configuratio
   💭 [证据链采集] 所有计划项已执行完毕。以下是证据采集结论：

---

## ✅ 证据采集结论

### 已采集证据（共 4 项）

| 计划项 | 工具 | 结果 |
|--------|------|------|
| **e1 (critical)** | `kubectl describe pod` | ✅ **Pod 状态 Pending**，Events 原文：`persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found`，3 个节点均不可用。Volumes 中 ClaimName 明确指向缺失的 PVC。 |
| **e2 (critical)** | `kubectl get pvc` | ✅ **PVC 不存在**（`Error from server (NotFound)`），预期负向证据已确认。 |
| **e3 (important)** | `kubectl_get_yaml` | ✅ **Pod spec 确认**：`volumes[0].persistentVolumeClaim.claimName: rc-pending-definitely-missing-pvc`，MountPath: `/data`。 |
| **e4 (important)** | `kubectl get pvc -n aiops-e2e` | ✅ **命名空间下无任何 PVC**，排除其他 PVC 异常干扰。 |

### 未采集证据
- 无。所有计划项均已执行完毕。

### 冲突证据
- 无。

---

### 🔍 根因总结

**Pod `rc-pending-missing-pvc`（aiops-e2e 命名空间）卡在 Pending 的根因：**
Pod 的 spec 中定义了一个 PersistentVolumeClaim 类型卷 `missing-pvc`，引用的 `claimName: rc-pending-definitely-missing-pvc` **在集群中根本不存在**。调度器 Events 明确报告 `persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found`，导致 3 个节点均无法调度该 Pod。**直接修复方案是创建同名 PVC 或修正 Pod 引用的 claimName。**
   ✅ [证据链采集] 完成 (17.5s)
   📤 → 下游数据: evidence_items=5/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod rc-pending-missing-pvc 当前状态与 Events（FailedScheduling + PVC not found）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-missing-pvc -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-missing-pvc","namespace":"aiops-e2e"},"purpose":"确认 Pod 当前状态和 Events 原文中的 persistentvolumeclaim not found 错误","evidence_type":"current_state_and_events","target_scope":"pod_state","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"验证 PVC rc-pending-definitely-missing-pvc 在集群中是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e","tool_args":{"kind":"pvc","name":"rc-pending-definitely-missing-pvc","namespace":"aiops-e2e","resource":"PersistentVolumeClaim"},"purpose":"验证PVC是否存在，预期NotFound即为根因证据","evidence_type":"resource_existence","target_scope":"pvc","acceptable_tools":["kubectl_get_by_name","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"获取 Pod YAML 验证 volumes 中引用的 claimName","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-missing-pvc -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-missing-pvc","namespace":"aiops-e2e","resource":"Pod"},"purpose":"确认Pod spec中volumes[].persistentVolumeClaim.claimName是否指向缺失的PVC","evidence_type":"pod_spec_volumes","target_scope":"pod_spec","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e4","description":"验证集群中所有PVC列表，确认无其他同命名空间异常PVC","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get pvc -n aiops-e2e","tool_args":{"kind":"PersistentVolumeClaim","namespace":"aiops-e2e"},"purpose":"确认aiops-e2e命名空间中所有PVC状态，排除其他PVC异常","evidence_type":"namespace_pvc_list","target_scope":"namespace_pvcs","acceptable_tools":["kubectl_get_by_kind_in_namespace","run_bash_command"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-missing-pvc\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  3m40s  default-scheduler  0/3 nodes are available: persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  missing-pvc:\n    Type:       PersistentVolumeClaim (a reference to a PersistentVolumeClaim in the same namespace)\n    ClaimName:  rc-pending-definitely-missing-pvc\n  kube-api-access-8zzdt:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  3m40s  default-scheduler  0/3 nodes are available: persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/94285eaabc0641a1/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/94285eaabc0641a1/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/94285eaabc0641a1/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=209 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide pvc rc-pending-definitely-missing-pvc -n aiops-e2e\nError from server (NotFound): persistentvolumeclaims \"rc-pending-definitely-missing-pvc\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/94285eaabc0641a1/tools/002-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/94285eaabc0641a1/tools/002-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/94285eaabc0641a1/tools/002-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"工具成功执行，但没有找到资源；这是空/负向观察，不能当作异常已被验证。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/94285eaabc0641a1/tools/003-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/94285eaabc0641a1/tools/003-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/94285eaabc0641a1/tools/003-evidence-kubectl_get_by_kind_in_namespace.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 输出摘要: raw_chars=2917 lines=87\napiVersion: v1\nkind: Pod\nmetadata:\n  annotations:\n    aiops.e2e/runbook: pod-pending-unschedulable.md\n    kubectl.kubernetes.io/last-applied-configuration: |\n      {\"apiVersion\":\"v1\",\"kind\":\"Pod\",\"metadata\":{\"annotations\":{\"aiops.e2e/runbook\":\"pod-pending-unschedulable.md\"},\"labels\":{\"app\":\"rc-pending-missing-pvc\",\"pod_abnormal_type\":\"PendingUnschedulable\",\"rootcause-e2e\":\"true\"},\"name\":\"rc-pending-missing-pvc\",\"namespace\":\"aiops-e2e\"},\"spec\":{\"containers\":[{\"command\":[\"sh\",\"-c\",\"sleep 3600\"],\"image\":\"busybox:1.36\",\"imagePullPolicy\":\"Never\",\"name\":\"app\",\"volumeMounts\":[{\"mountPath\":\"/data\",\"name\":\"missing-pvc\"}]}],\"volumes\":[{\"name\":\"missing-pvc\",\"persistentVolumeClaim\":{\"claimName\":\"rc-pending-definitely-missing-pvc\"}}]}}\n  creationTimestamp: \"2026-05-21T08:47:03Z\"\n  labels:\n    app: rc-pending-missing-pvc\n    pod_abnormal_type: PendingUnschedulable\n    rootcause-e2e: \"true\"\n  name: rc-pending-missing-pvc\n  namespace: aiops-e2e\n  resourceVersion: \"52593594\"\n  uid: 6024a009-c4f2-4238-b684-6e25a1a6096f\nspec:\n  containers:\n  - command:\n    - sh\n    - -c\n    - sleep 3600\n    image: busybox:1.36\n    imagePullPolicy: Never\n    name: app\n    resources: {}\n    terminationMessagePath: /dev/termination-log\n    terminationMessagePolicy: File\n    volumeMounts:\n    - mountPath: /data\n      name: missing-pvc\n    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount\n      name: kube-api-access-8zzdt\n      readOnly: true\n  dnsPolicy: ClusterFirst\n  enableServiceLinks: true\n  preemptionPolicy: PreemptLowerPriority\n  priority: 0\n  restartPolicy: Always\n  schedulerName: default-scheduler","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/94285eaabc0641a1/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/94285eaabc0641a1/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/94285eaabc0641a1/tools/004-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"所有计划项已执行完毕。以下是证据采集结论：\n\n---\n\n## ✅ 证据采集结论\n\n### 已采集证据（共 4 项）\n\n| 计划项 | 工具 | 结果 |\n|--------|------|------|\n| **e1 (critical)** | `kubectl describe pod` | ✅ **Pod 状态 Pending**，Events 原文：`persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found`，3 个节点均不可用。Volumes 中 ClaimName 明确指向缺失的 PVC。 |\n| **e2 (critical)** | `kubectl get pvc` | ✅ **PVC 不存在**（`Error from server (NotFound)`），预期负向证据已确认。 |\n| **e3 (important)** | `kubectl_get_yaml` | ✅ **Pod spec 确认**：`volumes[0].persistentVolumeClaim.claimName: rc-pending-definitely-missing-pvc`，MountPath: `/data`。 |\n| **e4 (important)** | `kubectl get pvc -n aiops-e2e` | ✅ **命名空间下无任何 PVC**，排除其他 PVC 异常干扰。 |\n\n### 未采集证据\n- 无。所有计划项均已执行完毕。\n\n### 冲突证据\n- 无。\n\n---\n\n### 🔍 根因总结\n\n**Pod `rc-pending-missing-pvc`（aiops-e2e 命名空间）卡在 Pending 的根因：**\nPod 的 spec 中定义了一个 PersistentVolumeClaim 类型卷 `missing-pvc`，引用的 `claimName: rc-pending-definitely-missing-pvc` **在集群中根本不存在**。调度器 Events 明确报告 `persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found`，导致 3 个节点均无法调度该 Pod。**直接修复方案是创建同名 PVC 或修正 Pod 引用的 claimName。**","collection_summary":"计划 4 项，实际采集 2 项，未采集 2 项，完整度 50%；其中真实环境证据 5/7 项，完整度 71%；实际执行工具 4 个，匹配计划 2 个，未规划证据 2 个","plan_total":4,"plan_collected":2,"plan_completeness":0.5,"environment_evidence_total":7,"environment_evidence_collected":5,"environment_evidence_completeness":0.7142857142857143,"executed_tool_count":4,"matched_tool_count":2,"unplanned_tool_count":2,"evidence_inventory":[{"id":"e1","description":"验证 Pod rc-pending-missing-pvc 当前状态与 Events（FailedScheduling + PVC not found）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-missing-pvc -n aiops-e2e","purpose":"确认 Pod 当前状态和 Events 原文中的 persistentvolumeclaim not found 错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证 PVC rc-pending-definitely-missing-pvc 在集群中是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e","purpose":"验证PVC是否存在，预期NotFound即为根因证据","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"e3","description":"获取 Pod YAML 验证 volumes 中引用的 claimName","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-missing-pvc -n aiops-e2e -o yaml","purpose":"确认Pod spec中volumes[].persistentVolumeClaim.claimName是否指向缺失的PVC","collected":false,"source":"planned","outcome":"unknown"},{"id":"e4","description":"验证集群中所有PVC列表，确认无其他同命名空间异常PVC","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get pvc -n aiops-e2e","purpose":"确认aiops-e2e命名空间中所有PVC状态，排除其他PVC异常","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e3(获取 Pod YAML 验证 volumes 中引用的 claimName): 已规划但工具执行失败或无匹配结果","e4(验证集群中所有PVC列表，确认无其他同命名空间异常PVC): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/4 项, 完整度: 71%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod rc-pending-missing-pvc 当前状态与 Events（Fa... | `kubectl describe pod rc-pending-missing-pvc -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_by_name | 验证 PVC rc-pending-definitely-missing-pvc 在集群中... | `kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e` |
   | e3 | important | ❌ | kubectl_get_yaml | 获取 Pod YAML 验证 volumes 中引用的 claimName | `kubectl get pod rc-pending-missing-pvc -n aiops-e2e -o yaml` |
   | e4 | important | ❌ | kubectl_get_by_kind_in_na... | 验证集群中所有PVC列表，确认无其他同命名空间异常PVC | `kubectl get pvc -n aiops-e2e` |

   ⚠️ 未采集原因:
   - e3(获取 Pod YAML 验证 volumes 中引用的 claimName): 已规划但工具执行失败或无匹配结果
   - e4(验证集群中所有PVC列表，确认无其他同命名空间异常PVC): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (18.9s)
   📤 → 下游数据: root_cause=Pod rc-pending-missing-pvc（aiops-e2e 命名空间）卡在 Pending 状态的唯一根因是其 spec 中定义了名为 missing-pvc 的 PersistentVolumeClaim 类型卷，claimName 为 rc-pending-definitely-missing-pvc，但该 PVC 在集群中根本不存在（kubectl get pvc 返回 NotFound），且 aiops-e2e 命名空间下无任何 PVC 资源。调度器 Events 确认：persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found，导致 0/3 节点均不可调度。修复方式：创建同名 PVC 或修改 Pod 的 claimName 为存在的 PVC。
   confidence=98%
   causal_chain={"root_cause": "Pod spec 中定义的 PersistentVolumeClaim 'rc-pending-definitely-missing-pvc' 在 aiops-e2e 命名空间中不存在，导致调度器无法绑定卷", "propagation": "Pod 定义了 Volume 类型为 PersistentVolumeClaim，引用 claimName 'rc-pending-definitely-missing-pvc' → 调度器检查该 PVC 是否存在 → 查询返回 NotFound → 调度器判定 PVC 不满足前置条件 → 所有 3 个节点均不可用 → Pod 持续卡在 Pending", "direct_cause": "调度器 FailedScheduling：PVC 'rc-pending-definitely-missing-pvc' not found", "manifestation": "Pod rc-pending-missing-pvc 状态为 Pending，无 IP 分配，无节点调度，持续 3 分钟以上无法启动"}
   rca_analysis={"phenomenon": "Pod rc-pending-missing-pvc（aiops-e2e 命名空间）状态为 Pending，调度器 Events 显示 persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found，0/3 节点可用，Pod 无法调度。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod rc-pending-missing-pvc 状态 Pending，Events: FailedScheduling - persistentvolumeclaim 'rc-pending-definitely-missing-pvc' not found", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_by_name", "content": "kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e 返回 NotFound 错误", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_yaml", "content": "Pod YAML 中 volumes[0].persistentVolumeClaim.claimName 为 rc-pending-definitely-missing-pvc", "reliability": "高"}, {"id": "e4", "source": "kubectl_get_by_kind_in_namespace", "content": "aiops-e2e 命名空间下无任何 PVC 资源", "reliability": "高"}, {"id": "e5", "source": "kubectl_get_by_kind_in_cluster", "content": "集群 65 个 Pod 中仅 1 个异常，59 个 Running，1 个 Pending", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedScheduling 3m40s default-scheduler 0/3 nodes are available: persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found.", "interpretation": "调度器明确拒绝调度 Pod，原因是被引用的 PVC 在集群中不存在。3 个节点均因此不可用。"}, {"evidence_id": "e2", "raw_data": "Error from server (NotFound): persistentvolumeclaims \"rc-pending-definitely-missing-pvc\" not found", "interpretation": "通过 kubectl get pvc 单独查询该 PVC 确认其确实不存在于集群中，排除临时性故障或缓存问题。"}, {"evidence_id": "e3", "raw_data": "volumes:\n  - name: missing-pvc\n    persistentVolumeClaim:\n      claimName: rc-pending-definitely-missing-pvc", "interpretation": "Pod spec 中明确引用了 claimName 为 rc-pending-definitely-missing-pvc 的 PVC，确认引用路径无误，问题在于 PVC 对象缺失而非引用错误。"}, {"evidence_id": "e4", "raw_data": "工具成功执行，但没有找到资源", "interpretation": "aiops-e2e 命名空间下没有任何 PVC 资源，排除其他 PVC 异常干扰，同时说明该 PVC 从未在该命名空间下创建过。"}, {"evidence_id": "e5", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}", "interpretation": "集群整体健康，59/65 Pod 正常运行，仅此一个 Pod 异常，问题范围精确锁定，非集群级故障。"}], "causal_chain": {"root_cause": "Pod spec 中定义的 PersistentVolumeClaim 'rc-pending-definitely-missing-pvc' 在 aiops-e2e 命名空间中不存在，导致调度器无法绑定卷", "propagation": "Pod 定义了 Volume 类型为 PersistentVolumeClaim，引用 claimName 'rc-pending-definitely-missing-pvc' → 调度器检查该 PVC 是否存在 → 查询返回 NotFound → 调度器判定 PVC 不满足前置条件 → 所有 3 个节点均不可用 → Pod 持续卡在 Pending", "direct_cause": "调度器 FailedScheduling：PVC 'rc-pending-definitely-missing-pvc' not found", "manifestation": "Pod rc-pending-missing-pvc 状态为 Pending，无 IP 分配，无节点调度，持续 3 分钟以上无法启动"}, "root_cause": "Pod rc-pending-missing-pvc（aiops-e2e 命名空间）卡在 Pending 状态的唯一根因是其 spec 中定义了名为 missing-pvc 的 PersistentVolumeClaim 类型卷，claimName 为 rc-pending-definitely-missing-pvc，但该 PVC 在集群中根本不存在（kubectl get pvc 返回 NotFound），且 aiops-e2e 命名空间下无任何 PVC 资源。调度器 Events 确认：persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found，导致 0/3 节点均不可调度。修复方式：创建同名 PVC 或修改 Pod 的 claimName 为存在的 PVC。", "root_cause_summary": "Pod rc-pending-missing-pvc（aiops-e2e 命名空间）卡在 Pending 状态的唯一根因是其 spec 中定义了名为 missing-pvc 的 PersistentVolumeClaim 类型卷，claimName 为 rc-pending-definitely-missing-pvc，但该 PVC 在集群中根本不存在（kubectl get pvc 返回 NotFound），且 aiops-e2e 命名空间下无任何 PVC 资源。调度器 Events 确认：persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found，导致 0/3 节点均不可调度。修复方式：创建同名 PVC 或修改 Pod 的 claimName 为存在的 PVC。", "confidence": 0.98, "confidence_reason": "有 4 项直接证据交叉验证：kubectl describe pod 显示 FailedScheduling 事件明确报告 PVC not found；kubectl get pvc 返回 NotFound 确认 PVC 缺失；Pod YAML 确认 claimName 引用路径正确；命名空间下无任何 PVC 排除干扰。证据链完整无矛盾，置信度 0.98。", "primary_runbooks": ["pod-pending-unschedulable.md", "pod-volume-mount-failed.md"], "alternative_causes": [{"cause": "资源不足（CPU/内存不足）导致无法调度", "probability": "low", "reason": "Events 中没有 'Insufficient cpu' 或 'Insufficient memory' 等资源不足提示，明确指向 PVC not found"}, {"cause": "节点 taint/nodeSelector/affinity 不匹配", "probability": "low", "reason": "Pod spec 中 Node-Selectors 为 <none>，Tolerations 仅包含默认的 not-ready 容忍，Events 未提及 taint 或不匹配约束"}, {"cause": "PVC 存在但绑定中或状态异常", "probability": "low", "reason": "直接查询 PVC 返回 NotFound，而非 Pending/Bound 等状态"}], "limitations": "未获取 PVC 的完整创建记录或审计日志来判断该 PVC 是未曾创建、被删除还是拼写错误。但当前证据已足够定位根因为 PVC 缺失。缺失证据（e3 Pod YAML、e4 全量PVC列表）实际已由后续工具补充采集，分析完整。", "llm_raw_analysis": "## 证据清点\\n共采集 5 项有效证据：e1(kubectl_describe)、e2(kubectl_get_by_name)、e3(kubectl_get_yaml)、e4(kubectl_get_by_kind_in_namespace)、e5(cluster overview)。\\n\\n## 逐条分析\\n- e1：Pod describe 显示状态 Pending，Events 明确 FailedScheduling，原因：PVC not found。这是最直接的错误信号。\\n- e2：单独查询该 PVC 返回 NotFound，确认 PVC 确实不存在。\\n- e3：Pod YAML 确认 volumes[0].persistentVolumeClaim.claimName = rc-pending-definitely-missing-pvc，引用路径正确。\\n- e4：命名空间下无任何 PVC，说明该 PVC 从未创建或已被删除。\\n- e5：集群整体 59/65 Running，仅此 1 个 Pending，非集群级问题。\\n\\n## 关联分析\\ne1+e2+e3+e\n... 截断，原始 747 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-missing-pvc（aiops-e2e 命名空间）卡在 Pending 状态的唯一根因是其 spec 中定义了名为 missing-pvc 的 PersistentVolumeClaim 类型卷，claimName 为 rc-pending-definitely-m...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod spec 中定义的 PersistentVolumeClaim 'rc-pending-definitely-missing-pvc' 在 aiops-e2e 命名空间中不存在，导致调度器无法绑定卷
     传导机制: Pod 定义了 Volume 类型为 PersistentVolumeClaim，引用 claimName 'rc-pending-definitely-missing-pvc' → 调度器检查该 PVC 是否存在 → 查询返回 NotFound → 调度器判定 PVC 不满足前置条件 → 所有 3 个节点均不可用 → Pod 持续卡在 Pending
     最终表现: Pod rc-pending-missing-pvc 状态为 Pending，无 IP 分配，无节点调度，持续 3 分钟以上无法启动


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (21.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6202 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 18.7s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将基于您提供的信息，生成一份详尽、完整的诊断报告。

---
## 📊 诊断概览

**您的集群当前状态总结**：
您的集群整体运行健康，`aiops-e2e` 命名空间下存在 **1个异常Pod** (`rc-pending-missing-pvc`)，状态为 `Pending`。其余 **59个Pod** 均正常运行。

**核心问题**：
Pod `rc-pending-missing-pvc` 引用的 PVC `rc-pending-definitely-missing-pvc` **不存在**，导致调度器无法为其分配节点，Pod 卡在 `Pending` 状态。

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending |
| **兼容归因层** | L0 - Evicted/VolumeMountFailed/磁盘/驱逐层 |
| **问题分类** | VolumeMountFailed / PendingUnschedulable (PVC缺失) |
| **置信度** | 高 (98%) |
| **证据完整度** | 2/4 (50%) |

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-pending-missing-pvc` |
| Namespace | `aiops-e2e` |
| 节点 | `<none>` (未分配) |
| 状态 | `Pending` (持续超过 3 分钟) |
| 错误信息 | `persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found` |

---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pods` | `NAMESPACE: aiops-e2e, NAME: rc-pending-missing-pvc, STATUS: Pending` | Pod 卡在 `Pending` 状态，无法调度到任何节点 |
| 2 | Pod 事件 | `kubectl describe pod rc-pending-missing-pvc` | `Warning  FailedScheduling  3m40s  default-scheduler  0/3 nodes are available: persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found.` | 调度器明确报告 PVC 不存在，导致所有 3 个节点均不可用 |
| 3 | Pod 规格 | `kubectl get pod rc-pending-missing-pvc -o yaml` | `volumes: [{"name":"missing-pvc","persistentVolumeClaim":{"claimName":"rc-pending-definitely-missing-pvc"}}]` | Pod 定义了名为 `missing-pvc` 的卷，引用 `claimName` 为 `rc-pending-definitely-missing-pvc` |
| 4 | PVC 存在性 | `kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e` | `Error from server (NotFound): persistentvolumeclaims "rc-pending-definitely-missing-pvc" not found` | 集群中不存在名为 `rc-pending-definitely-missing-pvc` 的 PVC |
| 5 | 命名空间资源 | `kubectl get pvc -n aiops-e2e` | 工具成功执行，但没有找到资源（空列表） | `aiops-e2e` 命名空间下没有任何 PVC 资源 |

### 证据关联分析
- **证据 #2 + #4 + 证据 #5 强关联**：调度器事件明确指出 PVC 不存在，且后续工具确认该 PVC 在集群和命名空间中都是缺失的，三者完美印证。
- **证据链**：Pod 定义了一个 PVC 卷 (claimName: `rc-pending-definitely-missing-pvc`) → 调度器尝试绑定该 PVC → PVC 不存在 → 调度失败 → Pod 卡在 Pending。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| Pod YAML (原始完整) | important | 已通过 `kubectl_get_yaml` 补充获取到关键信息。 |
| 全量PVC列表 | important | 已通过 `kubectl_get_by_kind_in_namespace` 确认命名空间内无 PVC。当前证据已足够定位根因，缺失不影响结论。 |

---
## 🎯 根因分析

### 因果链
```
┌───────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                  │
│ Pod spec 中定义的 PersistentVolumeClaim 'rc-pending-definitely-missing-pvc'│
│ 在 aiops-e2e 命名空间中不存在（可能从未创建、被删除或拼写错误）。          │
└───────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌───────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                  │
│ Pod 定义 Volume 类型为 PersistentVolumeClaim，引用 claimName              │
│ → 调度器检查该 PVC 是否存在 → 查询返回 NotFound                          │
└───────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌───────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                  │
│ 调度器 FailedScheduling：0/3 nodes are available:                         │
│   persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found.    │
└───────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌───────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                              │
│ Pod rc-pending-missing-pvc 状态持续为 Pending，                                │
│ 无法分配到任何节点，无法分配 IP，无法启动。                                │
└───────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #2 (FailedScheduling 事件)、证据 #3 (Pod YAML 中定义的 claimName) 和证据 #4 (PVC 查询结果为 NotFound)，
问题的**根本原因是 Pod `rc-pending-missing-pvc` 引用的 PersistentVolumeClaim `rc-pending-definitely-missing-pvc` 在集群中不存在**，导致调度器无法满足 Pod 的卷依赖，Pod 持续卡在 `Pending` 状态。

**置信度**：高 (98%)
- ✅ `kubectl describe` 事件原文直接指出 PVC not found
- ✅ `kubectl get pvc` 命令返回 NotFound，直接证实事件
- ✅ Pod YAML 确认了 claimName 与事件中缺失的 PVC 名称完全一致
- ⚠️ 无法确认该 PVC 是未曾创建、被手动删除还是 YAML 中拼写错误，但这不影响根因定位。

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）

**方案1：[推荐] 创建缺失的 PVC**
这是最直接的方式，使 Pod 的卷引用得以匹配。
```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: rc-pending-definitely-missing-pvc
  namespace: aiops-e2e
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
EOF
```
*注意*：`storage` 大小和 `accessModes` 需要根据集群中的 StorageClass 和实际需求调整。如果集群没有默认 StorageClass，还需要指定 `storageClassName`。

**方案2：[备选] 修改 Pod 引用指向一个已存在的 PVC**
如果 Pod 不应该绑定这个名称的 PVC，需要修改其 YAML 中的 `claimName`。
```bash
# 1. 首先查看 aiops-e2e 命名空间下是否有其它可用的 PVC
kubectl get pvc -n aiops-e2e

# 2. 如果找到其他可用 PVC，例如 my-existing-pvc, 则修改 Pod
kubectl edit pod rc-pending-missing-pvc -n aiops-e2e
# 在 spec.volumes 下，将 claimName 从 rc-pending-definitely-missing-pvc 改为 my-existing-pvc
# 或者，如果不需要挂载卷，直接删除 volumes 和 volumeMounts 部分。
```
*依据*：当前 YAML 中 `claimName` 指向一个不存在的资源，需要修正这个引用。

### 后续优化
1. **GitOps/Namspaced 资源规划**：确保 Pod 和其依赖的 PVC 在同一个 YAML 文件或部署清单中被一同创建，避免依赖缺失。
2. **资源命名规范**：统一命名规范，减少因拼写错误导致的问题。
3. **预检检查**：在 CI/CD 流程中加入资源检查步骤，例如使用 `kubectl --dry-run=client` 检查资源是否存在依赖错误。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. [方案1] 创建 PVC 后检查 Pod | `kubectl get pod rc-pending-missing-pvc -n aiops-e2e` | STATUS 从 `Pending` 变为 `ContainerCreating` 或 `Running` |
| 2. [方案2] 修改 Pod 后检查 Pod | `kubectl get pod rc-pending-missing-pvc -n aiops-e2e` | STATUS 变为 `Running` (如果引用的 PVC 可用) |
| 3. 检查 Pod 事件 | `kubectl describe pod rc-pending-missing-pvc -n aiops-e2e` | 不再出现 `persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found` 事件 |

---
## ⚠️ 注意事项
- 使用**方案1**时，如果集群中没有默认的 `StorageClass`，PVC 将卡在 `Pending` 状态。你需要 `kubectl get storageclass` 查看并提供 `storageClassName` 字段。
- 使用**方案2**时，`kubectl edit` 修改后 Pod 会被自动重建以应用新配置。
- 此问题为**配置错误**，与集群节点健康度无关。

---

## 📊 性能统计

├─ 总耗时: 1.3m
├─ 问题定位: 20.5s (26%) ✅
├─ 证据链采集: 17.5s (22%) ✅
├─ 根因分析: 18.9s (24%) ✅
├─ 汇总总结: 21.8s (28%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 9 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable, pod-volume-mount-failed
- **参考 Runbook**: pod-pending-unschedulable, pod-volume-mount-failed
- **工具调用**: 9 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
