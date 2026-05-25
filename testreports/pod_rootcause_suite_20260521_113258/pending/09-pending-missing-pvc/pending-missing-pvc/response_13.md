======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: bb4dbdf5d8ce4749]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，让我先全局扫描所有 Pod 的状态，了解集群的整体情况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 发现了一个异常 Pod，状态是 **Pending**。让我进一步查看这个 Pod 的详细信息。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-missing-pvc
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  9m47s  default-scheduler  0/3 nodes are available: persistentvol
   💭 [问题定位] 现在情况很明确了。让我获取对应的 runbook 作为参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] 现在我已经掌握了全部信息。让我输出诊断结果。

---

## 诊断结果

### 集群总体概览

| 指标 | 数值 |
|------|------|
| 总 Pod 数 | 65 |
| 正常运行 Pod (Running) | 59 |
| 异常 Pod | **1** |
| 异常率 | **1.5%** |

集群整体健康，仅发现 **1 个异常 Pod**。

---

### 异常 Pod 详情

| 字段 | 值 |
|------|-----|
| **Namespace** | `aiops-e2e` |
| **Pod 名称** | `rc-pending-missing-pvc` |
| **STATUS** | `Pending` |
| **READY** | `0/1` |
| **节点** | `<none>`（未调度） |
| **已运行** | 约 9 分 45 秒 |

---

### 异常识别

**状态关键字**: `Pending`  
**Pod 异常类型**: `VolumeMountFailed`（因 PVC 缺失导致无法调度，属于卷挂载失败类别）  
**状态分类**: `pending_volume`  
**兼容层级**: **L0**

**异常组 (abnormal_groups)**:
- `Pending` → 1 个 Pod：`rc-pending-missing-pvc`

---

### 根因分析

从 `kubectl describe` 中 Events 关键信息：

```
Warning  FailedScheduling  default-scheduler
0/3 nodes are available: persistentvolumeclaim
"rc-pending-definitely-missing-pvc" not found.
```

Pod 的 `spec.volumes` 中引用了一个 PVC：
- **ClaimName**: `rc-pending-definitely-missing-pvc`

该 PVC **不存在于集群中**，导致调度器无法将 Pod 绑定到任何节点（3 个节点均不可用），Pod 一直卡在 Pending。

---

### 关键实体

| 资源类型 | 名称 | 状态 |
|---------|------|------|
| Pod | `rc-pending-missing-pvc` (aiops-e2e) | Pending |
| PVC（引用的） | `rc-pending-definitely-missing-pvc` | **不存在** |
| 节点 | 集群中 3 个节点 | 均正常，但无法调度该 Pod |

---

### 可能场景

1. **PVC 未创建**：引用的 PVC `rc-pending-definitely-missing-pvc` 从未被创建。
2. **PVC 名称拼写错误**：Pod yaml 中 ClaimName 与实际创建的 PVC 名称不匹配。
3. **PVC 已被删除**：PVC 曾经存在但被手动或自动清理掉了。

---

### Layer 输出摘要

| 字段 | 值 |
|------|-----|
| **layer** | L0 |
| **derived_layer** | L0 |
| **layers** | [L0] |
| **layer_name** | VolumeMountFailed - PVC 缺失 |
| **confidence** | 高 |
| **pod_status_keyword** | Pending |
| **pod_abnormal_type** | VolumeMountFailed |
| **status_category** | pending_volume |

> 建议下游 evidence 节点进一步检查：确认 PVC `rc-pending-definitely-missing-pvc` 是否应该存在，如果应该存在则创建该 PVC，如果名称有误则修正 Pod 的 volume 引用。
   ✅ [问题定位] 完成 (20.5s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[{'scenario': 'PVC 未创建', 'probability': '高', 'reason': '引用的PVC rc-pending-definitely-missing-pvc 在集群中不存在，kubectl get 返回 NotFound'}, {'scenario': 'PVC 名称拼写错误', 'probability': '中', 'reason': 'Pod yaml中ClaimName与实际创建的PVC名称可能不匹配'}, {'scenario': 'PVC 已被删除', 'probability': '低', 'reason': 'PVC可能曾经存在但被手动或自动清理'}]
   entities=[{"type": "Pod", "name": "rc-pending-missing-pvc", "namespace": "aiops-e2e"}, {"type": "PVC", "name": "rc-pending-definitely-missing-pvc", "namespace": "aiops-e2e"}]
   reasoning=集群中仅发现1个异常Pod：aiops-e2e/rc-pending-missing-pvc，状态为Pending。kubectl describe Events显示调度失败原因：persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found。Pod spec.volumes引用了不存在的PVC，属于VolumeMountFailed异常类型，归因于存储卷问题，符合L0层级（磁盘/存储/驱逐类）。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "VolumeMountFailed - PVC 缺失", "confidence": 0.95, "reasoning": "集群中仅发现1个异常Pod：aiops-e2e/rc-pending-missing-pvc，状态为Pending。kubectl describe Events显示调度失败原因：persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found。Pod spec.volumes引用了不存在的PVC，属于VolumeMountFailed异常类型，归因于存储卷问题，符合L0层级（磁盘/存储/驱逐类）。", "abnormal_pods": [{"name": "rc-pending-missing-pvc", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "VolumeMountFailed", "status_category": "pending_volume", "key_entities": [{"type": "Pod", "name": "rc-pending-missing-pvc", "namespace": "aiops-e2e"}, {"type": "PVC", "name": "rc-pending-definitely-missing-pvc", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "PVC 未创建", "probability": "高", "reason": "引用的PVC rc-pending-definitely-missing-pvc 在集群中不存在，kubectl get 返回 NotFound"}, {"scenario": "PVC 名称拼写错误", "probability": "中", "reason": "Pod yaml中ClaimName与实际创建的PVC名称可能不匹配"}, {"scenario": "PVC 已被删除", "probability": "低", "reason": "PVC可能曾经存在但被手动或自动清理"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-missing-pvc"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-missing-pvc"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-missing-pvc                              0/1     Pending     0              9m45s   <none>           <none>   <none>           <none>            app=rc-pending-missing-pvc,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/bb4dbdf5d8ce4749/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/bb4dbdf5d8ce4749/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/bb4dbdf5d8ce4749/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来执行既有 evidence_plan 中的工具，先采集最高优先级的证据。由于这些调用互不依赖，可以同时执行。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
10m                 Warning   FailedScheduling   Pod/rc-pending-missing-pvc   0/3 nodes are available: persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found. pr
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-missing-pvc
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  10m                default-scheduler  0/3 nodes are available: p
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 kubectl_get_by_name 输出摘要: raw_chars=209 lines=3
Command failed (exit 1):
kubectl get --show-labels -o wide pvc rc-pending-definitely-missing-pvc -n aiops-e2e
Error from server (NotFound): persistentvo
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 输出摘要: raw_chars=2917 lines=87
apiVersion: v1
kind: Pod
metadata:
  annotations:
    aiops.e2e/runbook: pod-pending-unschedulable.md
    kubectl.kubernetes.io/last-applied-configuratio
   💭 [证据链采集] ## 证据采集完成

### ✅ 已采集证据

| 证据项 | 关键结论 |
|--------|---------|
| **kubectl describe pod** (ev1) | Pod `rc-pending-missing-pvc` 状态 **Pending**，Events 明确显示 `persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found`，调度器无法放置 |
| **kubectl get pod -o yaml** (ev2) | Pod spec.volumes 明确引用 PVC `rc-pending-definitely-missing-pvc`，挂载路径 `/data` |
| **kubectl get pvc** (ev3) | PVC `rc-pending-definitely-missing-pvc` **不存在** — `Error from server (NotFound)` |
| **kubectl events** (ev4) | 完整事件时间线：10m 前、5m4s 前、4s 前共 3 次 FailedScheduling，错误原文一致，无其他异常事件 |

### 🔍 诊断结论

**根因：Pod 引用的 PVC `rc-pending-definitely-missing-pvc` 在 `aiops-e2e` 命名空间中不存在。**

- 异常 Pod **仅 1 个**：`aiops-e2e/rc-pending-missing-pvc`（Pending）
- 集群其余 59 个 Pod 均为 Running，无其他异常
- Pod 镜像 `busybox:1.36`（imagePullPolicy=Never）、命令、资源等配置均正常
- 调度器 3 个节点均可用，唯一阻塞原因就是 PVC 缺失

**建议修复方案：** 创建 PVC `rc-pending-definitely-missing-pvc` 或将 Pod volume 引用指向一个已存在的 PVC 名称。
   ✅ [证据链采集] 完成 (15.9s)
   📤 → 下游数据: evidence_items=4/6
   evidence_analysis={"evidence_plan":[{"id":"ev1-pod-describe","description":"kubectl describe pod 获取 Pod Events 中 FailedScheduling 原文——确认 PVC not found 错误","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-missing-pvc -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-missing-pvc","namespace":"aiops-e2e","resource":"pod"},"purpose":"验证上游已识别的 FailedScheduling 事件：persistentvolumeclaim 'rc-pending-definitely-missing-pvc' not found","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev2-pod-yaml","description":"kubectl get pod -o yaml 检查 Pod spec.volumes 中引用的 PVC 名称","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-missing-pvc -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-missing-pvc","namespace":"aiops-e2e","resource":"pod"},"purpose":"确认 Pod 引用的 PVC claimName","evidence_type":"","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"ev3-pvc-check","description":"检查 PVC rc-pending-definitely-missing-pvc 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e","tool_args":{"kind":"pvc","name":"rc-pending-definitely-missing-pvc","namespace":"aiops-e2e","resource":"pvc"},"purpose":"验证上游提示的 PVC 不存在，确认确根因","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev4-events","description":"获取 Pod 相关 Events 验证完整错误上下文","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-missing-pvc --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-pending-missing-pvc"},"purpose":"获取完整事件时间线，确认 FailedScheduling 原因无变化","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n10m                 Warning   FailedScheduling   Pod/rc-pending-missing-pvc   0/3 nodes are available: persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n4s (x2 over 5m4s)   Warning   FailedScheduling   Pod/rc-pending-missing-pvc   0/3 nodes are available: persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bb4dbdf5d8ce4749/tools/001-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bb4dbdf5d8ce4749/tools/001-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bb4dbdf5d8ce4749/tools/001-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-missing-pvc\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  10m                default-scheduler  0/3 nodes are available: persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  4s (x2 over 5m4s)  default-scheduler  0/3 nodes are available: persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  missing-pvc:\n    Type:       PersistentVolumeClaim (a reference to a PersistentVolumeClaim in the same namespace)\n    ClaimName:  rc-pending-definitely-missing-pvc\n  kube-api-access-8zzdt:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  10m                default-scheduler  0/3 nodes are available: persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  4s (x2 over 5m4s)  default-scheduler  0/3 nodes are available: persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/bb4dbdf5d8ce4749/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bb4dbdf5d8ce4749/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bb4dbdf5d8ce4749/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_name","data":"kubectl_get_by_name 输出摘要: raw_chars=209 lines=3\nCommand failed (exit 1):\nkubectl get --show-labels -o wide pvc rc-pending-definitely-missing-pvc -n aiops-e2e\nError from server (NotFound): persistentvolumeclaims \"rc-pending-definitely-missing-pvc\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/bb4dbdf5d8ce4749/tools/003-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bb4dbdf5d8ce4749/tools/003-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bb4dbdf5d8ce4749/tools/003-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 输出摘要: raw_chars=2917 lines=87\napiVersion: v1\nkind: Pod\nmetadata:\n  annotations:\n    aiops.e2e/runbook: pod-pending-unschedulable.md\n    kubectl.kubernetes.io/last-applied-configuration: |\n      {\"apiVersion\":\"v1\",\"kind\":\"Pod\",\"metadata\":{\"annotations\":{\"aiops.e2e/runbook\":\"pod-pending-unschedulable.md\"},\"labels\":{\"app\":\"rc-pending-missing-pvc\",\"pod_abnormal_type\":\"PendingUnschedulable\",\"rootcause-e2e\":\"true\"},\"name\":\"rc-pending-missing-pvc\",\"namespace\":\"aiops-e2e\"},\"spec\":{\"containers\":[{\"command\":[\"sh\",\"-c\",\"sleep 3600\"],\"image\":\"busybox:1.36\",\"imagePullPolicy\":\"Never\",\"name\":\"app\",\"volumeMounts\":[{\"mountPath\":\"/data\",\"name\":\"missing-pvc\"}]}],\"volumes\":[{\"name\":\"missing-pvc\",\"persistentVolumeClaim\":{\"claimName\":\"rc-pending-definitely-missing-pvc\"}}]}}\n  creationTimestamp: \"2026-05-21T08:47:03Z\"\n  labels:\n    app: rc-pending-missing-pvc\n    pod_abnormal_type: PendingUnschedulable\n    rootcause-e2e: \"true\"\n  name: rc-pending-missing-pvc\n  namespace: aiops-e2e\n  resourceVersion: \"52593594\"\n  uid: 6024a009-c4f2-4238-b684-6e25a1a6096f\nspec:\n  containers:\n  - command:\n    - sh\n    - -c\n    - sleep 3600\n    image: busybox:1.36\n    imagePullPolicy: Never\n    name: app\n    resources: {}\n    terminationMessagePath: /dev/termination-log\n    terminationMessagePolicy: File\n    volumeMounts:\n    - mountPath: /data\n      name: missing-pvc\n    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount\n      name: kube-api-access-8zzdt\n      readOnly: true\n  dnsPolicy: ClusterFirst\n  enableServiceLinks: true\n  preemptionPolicy: PreemptLowerPriority\n  priority: 0\n  restartPolicy: Always\n  schedulerName: default-scheduler","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/bb4dbdf5d8ce4749/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/bb4dbdf5d8ce4749/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/bb4dbdf5d8ce4749/tools/004-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"## 证据采集完成\n\n### ✅ 已采集证据\n\n| 证据项 | 关键结论 |\n|--------|---------|\n| **kubectl describe pod** (ev1) | Pod `rc-pending-missing-pvc` 状态 **Pending**，Events 明确显示 `persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found`，调度器无法放置 |\n| **kubectl get pod -o yaml** (ev2) | Pod spec.volumes 明确引用 PVC `rc-pending-definitely-missing-pvc`，挂载路径 `/data` |\n| **kubectl get pvc** (ev3) | PVC `rc-pending-definitely-missing-pvc` **不存在** — `Error from server (NotFound)` |\n| **kubectl events** (ev4) | 完整事件时间线：10m 前、5m4s 前、4s 前共 3 次 FailedScheduling，错误原文一致，无其他异常事件 |\n\n### 🔍 诊断结论\n\n**根因：Pod 引用的 PVC `rc-pending-definitely-missing-pvc` 在 `aiops-e2e` 命名空间中不存在。**\n\n- 异常 Pod **仅 1 个**：`aiops-e2e/rc-pending-missing-pvc`（Pending）\n- 集群其余 59 个 Pod 均为 Running，无其他异常\n- Pod 镜像 `busybox:1.36`（imagePullPolicy=Never）、命令、资源等配置均正常\n- 调度器 3 个节点均可用，唯一阻塞原因就是 PVC 缺失\n\n**建议修复方案：** 创建 PVC `rc-pending-definitely-missing-pvc` 或将 Pod volume 引用指向一个已存在的 PVC 名称。","collection_summary":"计划 4 项，实际采集 2 项，未采集 2 项，完整度 50%；其中真实环境证据 4/6 项，完整度 67%；实际执行工具 5 个，匹配计划 2 个，未规划证据 3 个","plan_total":4,"plan_collected":2,"plan_completeness":0.5,"environment_evidence_total":6,"environment_evidence_collected":4,"environment_evidence_completeness":0.6666666666666666,"executed_tool_count":5,"matched_tool_count":2,"unplanned_tool_count":3,"evidence_inventory":[{"id":"ev1-pod-describe","description":"kubectl describe pod 获取 Pod Events 中 FailedScheduling 原文——确认 PVC not found 错误","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-missing-pvc -n aiops-e2e","purpose":"验证上游已识别的 FailedScheduling 事件：persistentvolumeclaim 'rc-pending-definitely-missing-pvc' not found","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev2-pod-yaml","description":"kubectl get pod -o yaml 检查 Pod spec.volumes 中引用的 PVC 名称","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-missing-pvc -n aiops-e2e -o yaml","purpose":"确认 Pod 引用的 PVC claimName","collected":false,"source":"planned","outcome":"unknown"},{"id":"ev3-pvc-check","description":"检查 PVC rc-pending-definitely-missing-pvc 是否存在","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e","purpose":"验证上游提示的 PVC 不存在，确认确根因","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"ev4-events","description":"获取 Pod 相关 Events 验证完整错误上下文","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-missing-pvc --sort-by='.lastTimestamp'","purpose":"获取完整事件时间线，确认 FailedScheduling 原因无变化","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["ev2-pod-yaml(kubectl get pod -o yaml 检查 Pod spec.volumes 中引用的 PVC 名称): 已规划但工具执行失败或无匹配结果","ev4-events(获取 Pod 相关 Events 验证完整错误上下文): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 2/4 项, 完整度: 67%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | ev1-pod-describe | critical | ✅ | kubectl_describe | kubectl describe pod 获取 Pod Events 中 FailedSc... | `kubectl describe pod rc-pending-missing-pvc -n aiops-e2e` |
   | ev2-pod-yaml | critical | ❌ | kubectl_get_yaml | kubectl get pod -o yaml 检查 Pod spec.volumes 中... | `kubectl get pod rc-pending-missing-pvc -n aiops-e2e -o yaml` |
   | ev3-pvc-check | critical | ✅ | kubectl_get_by_name | 检查 PVC rc-pending-definitely-missing-pvc 是否存在 | `kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e` |
   | ev4-events | important | ❌ | kubectl_events | 获取 Pod 相关 Events 验证完整错误上下文 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pendi...` |

   ⚠️ 未采集原因:
   - ev2-pod-yaml(kubectl get pod -o yaml 检查 Pod spec.volumes 中引用的 PVC 名称): 已规划但工具执行失败或无匹配结果
   - ev4-events(获取 Pod 相关 Events 验证完整错误上下文): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (20.1s)
   📤 → 下游数据: root_cause=根因：Pod aiops-e2e/rc-pending-missing-pvc spec.volumes 引用的 PersistentVolumeClaim "rc-pending-definitely-missing-pvc" 在命名空间中不存在。kubectl get pvc 返回 NotFound 错误确认该PVC缺失。调度器Events显示 "0/3 nodes are available: persistentvolumeclaim 'rc-pending-definitely-missing-pvc' not found"，3个节点均可用，无资源不足、taint或其他调度约束问题。集群其他59个Pod均为Running状态，无并发异常。Pod镜像为busybox:1.36，QoS Class为BestEffort，无特殊调度约束，唯一阻塞原因即为PVC缺失。
   confidence=97%
   causal_chain={"root_cause": "PVC rc-pending-definitely-missing-pvc 在 aiops-e2e 命名空间中从未创建或被删除", "propagation": "Pod spec.volumes 引用了该不存在的PVC → kube-scheduler 在调度时检查卷依赖 → 发现PVC不存在 → 拒绝调度到任何节点 → Pod 持续处于 Pending 状态", "direct_cause": "Pod 引用的 PersistentVolumeClaim 'rc-pending-definitely-missing-pvc' 不存在（NotFound）", "manifestation": "Pod rc-pending-missing-pvc 处于 Pending 状态，Events 显示 FailedScheduling，调度器报告 PVC not found"}
   rca_analysis={"phenomenon": "集群中仅发现1个异常Pod：aiops-e2e/rc-pending-missing-pvc，状态为Pending。其余59个Pod均为Running。Pod Events显示调度失败原因：persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found。", "evidence_inventory": [{"id": "ev1-pod-describe", "source": "kubectl_describe", "content": "Pod rc-pending-missing-pvc 状态 Pending，Events 显示 FailedScheduling: PVC rc-pending-definitely-missing-pvc not found", "reliability": "高"}, {"id": "ev3-pvc-check", "source": "kubectl_get_by_name", "content": "kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e 返回 NotFound 错误", "reliability": "高"}, {"id": "ev4-events", "source": "kubectl_events", "content": "10m前、5m4s前、4s前共3次 FailedScheduling，错误原文一致", "reliability": "高"}, {"id": "ev2-pod-yaml", "source": "kubectl_get_yaml", "content": "Pod spec.volumes 引用 PVC ClaimName: rc-pending-definitely-missing-pvc", "reliability": "高"}, {"id": "ev5-cluster-summary", "source": "kubectl_get_by_kind_in_cluster", "content": "集群65个Pod中仅1个Pending，其余59个Running", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "ev1-pod-describe", "raw_data": "Warning  FailedScheduling  10m  default-scheduler  0/3 nodes are available: persistentvolumeclaim \"rc-pending-definitely-missing-pvc\" not found.", "interpretation": "调度器明确报告PVC不存在，这是Pod无法调度的直接原因。3个节点均可用，不存在节点资源问题。"}, {"evidence_id": "ev3-pvc-check", "raw_data": "Error from server (NotFound): persistentvolumeclaims \"rc-pending-definitely-missing-pvc\" not found", "interpretation": "PVC rc-pending-definitely-missing-pvc 在 aiops-e2e 命名空间中确实不存在，验证了调度器错误信息。"}, {"evidence_id": "ev4-events", "raw_data": "10m ago, 5m4s ago (x2 over), 4s ago (x2 over 5m4s) — 共3次 FailedScheduling", "interpretation": "事件时间线显示调度器持续重试但始终因同一原因失败，无其他异常事件干扰。"}, {"evidence_id": "ev2-pod-yaml", "raw_data": "Volumes:\n  missing-pvc:\n    Type: PersistentVolumeClaim\n    ClaimName: rc-pending-definitely-missing-pvc", "interpretation": "Pod spec确认引用了该不存在的PVC作为卷，挂载点为默认路径，与调度错误吻合。"}, {"evidence_id": "ev5-cluster-summary", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}", "interpretation": "集群整体健康，仅此1个Pod异常，问题范围明确，不存在其他并发故障。"}], "causal_chain": {"root_cause": "PVC rc-pending-definitely-missing-pvc 在 aiops-e2e 命名空间中从未创建或被删除", "propagation": "Pod spec.volumes 引用了该不存在的PVC → kube-scheduler 在调度时检查卷依赖 → 发现PVC不存在 → 拒绝调度到任何节点 → Pod 持续处于 Pending 状态", "direct_cause": "Pod 引用的 PersistentVolumeClaim 'rc-pending-definitely-missing-pvc' 不存在（NotFound）", "manifestation": "Pod rc-pending-missing-pvc 处于 Pending 状态，Events 显示 FailedScheduling，调度器报告 PVC not found"}, "root_cause": "根因：Pod aiops-e2e/rc-pending-missing-pvc spec.volumes 引用的 PersistentVolumeClaim \"rc-pending-definitely-missing-pvc\" 在命名空间中不存在。kubectl get pvc 返回 NotFound 错误确认该PVC缺失。调度器Events显示 \"0/3 nodes are available: persistentvolumeclaim 'rc-pending-definitely-missing-pvc' not found\"，3个节点均可用，无资源不足、taint或其他调度约束问题。集群其他59个Pod均为Running状态，无并发异常。Pod镜像为busybox:1.36，QoS Class为BestEffort，无特殊调度约束，唯一阻塞原因即为PVC缺失。", "root_cause_summary": "根因：Pod aiops-e2e/rc-pending-missing-pvc spec.volumes 引用的 PersistentVolumeClaim \"rc-pending-definitely-missing-pvc\" 在命名空间中不存在。kubectl get pvc 返回 NotFound 错误确认该PVC缺失。调度器Events显示 \"0/3 nodes are available: persistentvolumeclaim 'rc-pending-definitely-missing-pvc' not found\"，3个节点均可用，无资源不足、taint或其他调度约束问题。集群其他59个Pod均为Running状态，无并发异常。Pod镜像为busybox:1.36，QoS Class为BestEffort，无特殊调度约束，唯一阻塞原因即为PVC缺失。", "confidence": 0.97, "confidence_reason": "直接证据链完整：(1) kubectl describe pod 明确显示 FailedScheduling + PVC not found；(2) kubectl get pvc 返回 NotFound 确认PVC不存在；(3) kubectl get pod -o yaml 确认Pod spec引用了该PVC名称；(4) kubectl events 确认只有同一错误持续重试，无其他异常；(5) 集群整体只有1个异常Pod，问题边界清晰。证据链无缺口，置信度高。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [{"cause": "PVC 名称拼写错误", "probability": "low", "reason": "已经被kubectl get pvc NotFound验证，无论拼写错误还是未创建，结果一致——PVC不存在。且Pod yaml中ClaimName与错误消息完全一致，排除了误报。"}, {"cause": "PVC 已被删除", "probability": "low", "reason": "PVC可能曾经存在后被删除，但当前事实是PVC不存在，不影响根因判断。"}, {"cause": "节点资源不足", "probability": "excluded", "reason": "Events明确写的是PVC not found，而非CPU/Memory不足；且3个节点均可用，preemption victims=0但原因不同。"}, {"cause": "taint/nodeSelector 不匹配", "probability": "excluded", "reason": "Pod Node-Selectors为<none>，Tolerations仅为默认的not-ready容忍，Events未提及taint相关错误。"}], "limitations": "未采集kubectl get events的完整原始输出（仅摘要），但describe pod已覆盖全部关键事件。PVC不存在的原因（从未创建/拼写错误/被删除）无法进一步区分，但所有可能性的修复方案一致：创建该PVC或修改Pod引用。Pod的imagePullPolicy在yaml中未显式设置，但从describe结果看镜像拉取不是阻塞因素。", "llm_raw_analysis": "L0根因分析完成。异常组g1仅包含1个Pod：aiops-e2e/rc-pending-missing-pvc，状态Pending，异常类型VolumeMountFailed。上游layer_handoff已将pod_abnormal_type修正为VolumeMountFailed（区别于初始的PendingUnschedulable），与kubectl describe显示的PVC not found错误一致。非主异常组不存在，无需最小验证。证据链完整：describe pod → FailedScheduling due to PVC not found → kubectl get pvc → NotFound确认 → pod yaml确认卷引用。因果链清晰，无需升级到L1层做进一步排查。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 根因：Pod aiops-e2e/rc-pending-missing-pvc spec.volumes 引用的 PersistentVolumeClaim "rc-pending-definitely-missing-pvc" 在命名空间中不存在。kubectl get pvc 返回 NotFou...
   置信度: 97%
   🔗 因果链:
     根本原因: PVC rc-pending-definitely-missing-pvc 在 aiops-e2e 命名空间中从未创建或被删除
     传导机制: Pod spec.volumes 引用了该不存在的PVC → kube-scheduler 在调度时检查卷依赖 → 发现PVC不存在 → 拒绝调度到任何节点 → Pod 持续处于 Pending 状态
     最终表现: Pod rc-pending-missing-pvc 处于 Pending 状态，Events 显示 FailedScheduling，调度器报告 PVC not found


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (25.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6973 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 21.9s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **集群整体状态** | **基本健康**：共 65 个 Pod，其中 59 个 Running (91%)，1 个 Pending (1.5%) |
| **发现的问题** | 1 个 Pod (`aiops-e2e/rc-pending-missing-pvc`) 处于 **Pending** 状态，原因是引用了一个不存在的 PVC |
| **Pod异常状态** | Pending |
| **兼容归因层** | L1 - 存储卷问题 |
| **问题分类** | VolumeMountFailed / PendingUnschedulable |
| **置信度** | 高 (97%) |
| **证据完整度** | 2/4 (50%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | `rc-pending-missing-pvc` (aiops-e2e) |
| Namespace | aiops-e2e |
| 异常状态 | Pending |
| 缺失 PVC | `rc-pending-definitely-missing-pvc` |
| 集群节点数 | 3 个（全部可用） |
| 集群健康Pod数 | 59/65 (91%) 正常 |

**核心事实**：集群中 65 个 Pod 中有 59 个正常运行，仅有 **1 个 Pod** 处于 Pending 状态，且根因已明确。

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pods -A` | `STATUS: Pending` / `READY: 0/1` | Pod 未调度到任何节点 |
| 2 | Pod 描述 | `kubectl describe pod rc-pending-missing-pvc -n aiops-e2e` | `Warning FailedScheduling: 0/3 nodes are available: persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found.` | 调度器明确报告 PVC 不存在导致无法调度 |
| 3 | Events | `kubectl events` | `10m Warning FailedScheduling Pod/rc-pending-missing-pvc 0/3 nodes are available: persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found.` | 多次重试仍失败，确认 PVC 缺失是持续性问题 |
| 4 | PVC 检查 | `kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e` | `Error from server (NotFound): persistentvolumeclaims "rc-pending-definitely-missing-pvc" not found` | 目标 PVC 确实不存在于命名空间中 |
| 5 | Pod YAML | `kubectl get pod rc-pending-missing-pvc -n aiops-e2e -o yaml` | `volumes: [{name: "missing-pvc", persistentVolumeClaim: {claimName: "rc-pending-definitely-missing-pvc"}}]` | Pod spec 明确引用了不存在的 PVC |
| 6 | 节点状态 | `kubectl describe` 事件原文 | `0/3 nodes are available` -> 3 个节点均可用于调度 | 非节点资源/taint 问题，唯一阻塞是 PVC 缺失 |

### 证据关联分析

- **证据 #2 + #3 + #4 印证**：`kubectl describe` 和 `kubectl events` 均显示 `persistentvolumeclaim "rc-pending-definitely-missing-pvc" not found`，且 `kubectl get pvc` 直接返回 `NotFound` → **PVC 确实不存在**。
- **证据 #5 确认引用链**：Pod YAML 中 `volumes.persistentVolumeClaim.claimName` 指向 `rc-pending-definitely-missing-pvc` → 完美对应调度器报错信息。
- **证据 #6 排除其它原因**：`0/3 nodes are available` 表示所有节点都可用，说明不是资源不足、节点 taint、节点亲和性等问题。Pod 的 `Node-Selectors: <none>` 进一步排除调度约束问题。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 完整 `kubectl get events` 原始输出 | low | 已通过 `kubectl describe` 获取全部关键事件，不影响诊断结论 |
| Pod YAML 完整内容 | low | 已通过工具获取 `volumes` 段关键内容，足够定位根因 |

---

## 🎯 根因分析

### 因果链

```
┌────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                    │
│ PV/PVC "rc-pending-definitely-missing-pvc" 在 aiops-e2e 命名空间中          │
│ 从未创建、名称拼写错误、或被手动/自动删除                                    │
└────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                    │
│ Pod spec.volumes 引用 claimName="rc-pending-definitely-missing-pvc"         │
│ → kube-scheduler 调度时检查卷依赖                                           │
│ → 通过 API Server 查询 PVC → 返回 NotFound                                 │
│ → 调度器判定该 Pod 无法调度到任何节点                                       │
└────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                    │
│ 调度器 Events 明确报告:                                                    │
│ "0/3 nodes are available: persistentvolumeclaim                            │
│  'rc-pending-definitely-missing-pvc' not found"                            │
└────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                │
│ Pod rc-pending-missing-pvc 处于 Pending 状态，持续 FailedScheduling        │
└────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (Events 报告 PVC not found)、证据 #4 (kubectl get pvc 返回 NotFound)、证据 #5 (Pod YAML 引用该 PVC)，问题的根本原因是 **Pod `rc-pending-missing-pvc` 引用的 PersistentVolumeClaim `rc-pending-definitely-missing-pvc` 在 `aiops-e2e` 命名空间中不存在**。

集群中 3 个节点均正常工作，无资源不足、taint、节点亲和性等调度约束问题。集群另外 59 个 Pod 运行正常，此问题为**孤立的配置错误问题**，不影响其他工作负载。

**置信度**：高 (97%)
- ✅ `kubectl describe` 和 `kubectl events` 均直接显示 PVC not found 错误
- ✅ `kubectl get pvc` 明确返回 `NotFound`
- ✅ Pod YAML 确认引用名称完全匹配
- ✅ 3 个节点均可用，排除其他调度问题

---

## 🛠️ 修复建议

### 立即执行（二选一，按优先级排序）

**方案 1：[推荐] 创建缺失的 PVC**

先准备 PVC YAML 文件（注意：您需要根据实际存储后端调整 `storageClassName`）：

```yaml
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
  # 如果不确定 storageClass，可注释下一行使用集群默认
  # storageClassName: standard
```

创建 PVC：
```bash
# 将上述 YAML 保存为 pvc.yaml 后执行
kubectl apply -f pvc.yaml
```

*依据*：创建的 PVC 名称必须与 Pod 引用的 `rc-pending-definitely-missing-pvc` 完全一致

验证 PVC 是否创建成功：
```bash
kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e
```
*预期输出*：PVC 状态为 `Bound` (如果存在匹配 PV) 或 `Pending` (等待 PV 供给)

验证 Pod 是否自动恢复调度：
```bash
kubectl get pod rc-pending-missing-pvc -n aiops-e2e -w
```
*预期结果*：PVC 创建后，Pod 应自动进入调度并在满足条件后启动

---

**方案 2：修改 Pod 引用（如果 PVC 名称拼写错误）**

如果 PVC 已存在但名称不同，需要修改 Pod 的 volume 引用。由于该 Pod 可能由 Deployment/StatefulSet 管理，**不应直接修改 Pod**，建议修改控制器：

```bash
# 先检查 Pod 的属主
kubectl get pod rc-pending-missing-pvc -n aiops-e2e -o jsonpath='{.metadata.ownerReferences[0].kind}/{.metadata.ownerReferences[0].name}'
```

如果属主是 Deployment，修改其 YAML 中的 volume claim name：
```bash
kubectl edit deployment <owner-name> -n aiops-e2e
```
找到 `volumes` 段，修改 `claimName` 为正确的 PVC 名称。

### 后续优化

1. **名称规范**：建议建立 PVC 命名规范，避免 Pod 引用与 PVC 创建名称不一致的情况
2. **验证流程**：在 CI/CD 中增加 PVC 存在性校验步骤，提前发现引用问题
3. **监控告警**：配置 Pending Pod 告警，及时捕获类似问题

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 PVC 存在 | `kubectl get pvc rc-pending-definitely-missing-pvc -n aiops-e2e` | STATUS 不为 NotFound |
| 2. 确认 Pod 恢复 | `kubectl get pod rc-pending-missing-pvc -n aiops-e2e -w` | STATUS 从 Pending 变为 Running |
| 3. 检查 Events 无新错误 | `kubectl describe pod rc-pending-missing-pvc -n aiops-e2e` | 不再出现 FailedScheduling 事件 |
| 4. 集群整体确认 | `kubectl get pods -A \| grep -v Running \| grep -v Completed` | 无异常状态 Pod |

---

## ⚠️ 注意事项

1. **PVC 存储类**：创建 PVC 时，如果集群中没有与 `storageClassName` 匹配的 StorageClass，PVC 将保持 Pending 状态。请根据实际存储环境调整。
2. **Pod 控制器**：如果直接删除并重新创建该 Pod，它依然会因 PVC 缺失而陷入同样的 Pending 状态。**必须解决 PVC 问题**才是根本方案。
3. **集群整体健康**：除本问题外，集群运行正常，59 个 Running Pod 无异常，无需额外排查。

---

## 📊 性能统计

├─ 总耗时: 1.4m
├─ 问题定位: 20.5s (25%) ✅
├─ 证据链采集: 15.9s (19%) ✅
├─ 根因分析: 20.1s (25%) ✅
├─ 汇总总结: 25.3s (31%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 7 次
```

📋 诊断追踪

- **核心 Runbook**: pod-volume-mount-failed
- **参考 Runbook**: pod-volume-mount-failed, pod-pending-unschedulable
- **工具调用**: 7 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
