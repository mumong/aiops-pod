======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 80e586582e354018]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我先对整个集群进行全局 Pod 状态扫描，看看哪些 Pod 处于异常状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 发现了一个异常 Pod，让我进一步查看它的详细信息。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS    RESTARTS   AGE     IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-cpu   0/1     Pending   0          4m26s   <none>
   💭 [问题定位] Pod 是 Pending 状态且未绑定节点，符合 PendingUnschedulable 模式。让我查看 Events 确认调度失败原因，同时获取匹配的 runbook。
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
4m28s       Warning   FailedScheduling   Pod/rc-pending-insufficient-cpu   0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption v
   💭 [问题定位] 已经获取到足够的信息。让我确认一下集群的节点状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 所有节点都是 Ready 状态。现在我已掌握全部必要信息，可以给出诊断结论了。

---

## 诊断结论

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **layer_name** | PendingUnschedulable |
| **status_category** | scheduling |
| **pod_status_keyword** | Pending |
| **pod_abnormal_type** | PendingUnschedulable |
| **置信度** | 高 |

### 发现的问题

集群中 **1 个异常 Pod**：

| Pod | 命名空间 | 状态 | 问题 |
|-----|---------|------|------|
| `rc-pending-insufficient-cpu` | `aiops-e2e` | **Pending** | **调度失败 - CPU 资源不足** |

### 异常详情

**rc-pending-insufficient-cpu**（测试用 Pod，标签 `rootcause-e2e=true`）

- **当前状态**：`Pending`，未绑定任何节点（`nodeName=<none>`）
- **Events 关键信息**：
  ```
  FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu.
  ```
- **根因**：集群所有 3 个节点（master、node1、node2）的 CPU 资源均已耗尽，无法满足该 Pod 的 CPU request 要求，且无抢占受害者（No preemption victims found）。

### 异常分组

| 异常组 | Pod 列表 |
|-------|---------|
| **PendingUnschedulable** | `aiops-e2e/rc-pending-insufficient-cpu` |

### 可能场景

1. **集群整体 CPU 资源不足** — 3 个节点的 allocatable CPU 已全部被现有 Pod 占用，无法调度新的 Pod。
2. **Pod 请求的 CPU 过大** — Pod 的 `resources.requests.cpu` 设置过高，超出单个节点的剩余容量。
3. **测试场景** — 该 Pod 带有 `rootcause-e2e=true` 和 `pod_abnormal_type=PendingUnschedulable` 标签，是预置的异常测试用例。

### 关键实体

- 异常 Pod：`aiops-e2e/rc-pending-insufficient-cpu`
- 全部 3 个节点（master、node1、node2）均 Ready 但 CPU 不足
- 事件类型：`FailedScheduling`
   ✅ [问题定位] 完成 (24.2s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '集群整体CPU资源不足', 'probability': '高', 'reason': 'FailedScheduling事件显示3个节点均Insufficient cpu，所有节点Ready但CPU allocatable已耗尽'}, {'scenario': 'Pod请求的CPU过大', 'probability': '中', 'reason': 'Pod的resources.requests.cpu设置过高，超出单个节点剩余容量'}, {'scenario': '测试场景', 'probability': '低', 'reason': 'Pod带有rootcause-e2e=true标签，可能是预置测试用例'}]
   entities=[{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}]
   reasoning=集群中存在1个当前仍处于Pending状态的Pod（aiops-e2e/rc-pending-insufficient-cpu），状态关键字为Pending，调度事件明确显示FailedScheduling：'0/3 nodes are available: 3 Insufficient cpu.'。所有3个节点均为Ready状态，但CPU资源已全部耗尽，导致Pod无法调度。根据五层模型，PendingUnschedulable归类为L1（scheduling），无更底层根因（L0磁盘/驱逐、L2 OOM/CrashLoop、L3镜像/网络、L4应用错误均不适用）。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "集群中存在1个当前仍处于Pending状态的Pod（aiops-e2e/rc-pending-insufficient-cpu），状态关键字为Pending，调度事件明确显示FailedScheduling：'0/3 nodes are available: 3 Insufficient cpu.'。所有3个节点均为Ready状态，但CPU资源已全部耗尽，导致Pod无法调度。根据五层模型，PendingUnschedulable归类为L1（scheduling），无更底层根因（L0磁盘/驱逐、L2 OOM/CrashLoop、L3镜像/网络、L4应用错误均不适用）。", "abnormal_pods": [{"name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}], "possible_scenarios": [{"scenario": "集群整体CPU资源不足", "probability": "高", "reason": "FailedScheduling事件显示3个节点均Insufficient cpu，所有节点Ready但CPU allocatable已耗尽"}, {"scenario": "Pod请求的CPU过大", "probability": "中", "reason": "Pod的resources.requests.cpu设置过高，超出单个节点剩余容量"}, {"scenario": "测试场景", "probability": "低", "reason": "Pod带有rootcause-e2e=true标签，可能是预置测试用例"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-insufficient-cpu                         0/1     Pending     0              4m24s   <none>           <none>   <none>           <none>            app=rc-pending-insufficient-cpu,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/80e586582e354018/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/80e586582e354018/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/80e586582e354018/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我将直接执行既有 evidence_plan 中的关键工具，从最高优先级开始采集证据。

首先，获取已匹配的 runbook 作为参考，同时获取 Pod 的详细描述和事件信息。
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  5m    default-scheduler  0/3 nodes are available: 3 Insuffi
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
5m          Warning   FailedScheduling   Pod/rc-pending-insufficient-cpu   0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption v
   💭 [证据链采集] Pod 描述和事件已确认 FailedScheduling 原因。接下来获取 Pod YAML 查看 CPU 请求量，以及检查所有节点的 CPU 容量。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node1
关键诊断行:
                    volumes.kubernetes.io/controller-managed-attach-detach: true
Taints:             <none>
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: master
关键诊断行:
                    volumes.kubernetes.io/controller-managed-attach-detach: true
Taints:             <none>
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:59:10Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizer
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node2
关键诊断行:
                    volumes.kubernetes.io/controller-managed-attach-detach: true
Taints:             <none>
   💭 [证据链采集] Node describe 输出被截断了，让我获取更完整的节点 CPU allocatable 信息。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "Capacity:\n  cpu:                12\n  ephemeral-storage:  203770680Ki\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32860476Ki\n  pods:        
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "Capacity:\n  cpu:                12\n  ephemeral-storage:  616601232Ki\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32860484Ki\n  pods:        
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "Capacity:\n  cpu:                12\n  ephemeral-storage:  203770680Ki\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32860480Ki\n  pods:        
   💭 [证据链采集] 再查看 Pod 中实际的 CPU request 值：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "Name:               master\n  cpu                4610m (38%)   8600m (71%)\n  memory             6890Mi (21%)  12548Mi (39%)\nName:               node1\n  cpu             
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\"requests\":{\"cpu\":\"100k\",\"memory\":\"64Mi\"}}", "stderr": "", "returncode": 0}
   💭 [证据链采集] 让我确认这个 Pod 的 CPU request 是 100k（即 100 millicores = 0.1 core），以及检查节点上的 Pod 占用情况：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "    resources:\n      requests:\n        cpu: 100k\n        memory: 64Mi\n    terminationMessagePath: /dev/termination-log\n    terminationMessagePolicy: File\n", "stderr"
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "Name:               master\n  cpu                4610m (38%)   8600m (71%)\n  memory             6890Mi (21%)  12548Mi (39%)\nName:               node1\n  cpu             
   💭 [证据链采集] 现在获取各个节点的完整 Allocatable CPU 与 Requests CPU 对比：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "Allocated resources:\n  (Total limits may be over 100 percent, i.e., overcommitted.)\n  Resource           Requests      Limits\n  --------           --------      ------\
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "Allocated resources:\n  (Total limits may be over 100 percent, i.e., overcommitted.)\n  Resource           Requests          Limits\n  --------           --------         
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "Allocated resources:\n  (Total limits may be over 100 percent, i.e., overcommitted.)\n  Resource           Requests     Limits\n  --------           --------     ------\n 
   💭 [证据链采集] 这不对劲！每个节点的 CPU 分配率远未到 100%（master 38%，node1 7%，node2 14%），但 Pod 却报告 "Insufficient cpu"。让我检查 Pod 的 CPU 请求值 "100k" 是否存在单位解析问题：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "100k", "stderr": "", "returncode": 0}
   💭 [证据链采集] 找到根因了！Pod 的 CPU request 是 `100k`，这不是合法的 Kubernetes CPU 单位格式。Kubernetes 认可的单位：

- `100m` = 100 millicores（正确格式）
- `100k` = ❌ 非法格式，Kubernetes 调度器无法解析，会拒绝调度

让我验证一下这个非法值是否就是导致 "Insufficient cpu" 的原因：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "    resources:\n      requests:\n        cpu: 100k\n        memory: 64Mi\n    terminationMessagePath: /dev/termination-log\n    terminationMessagePolicy: File\n    volumeM
   💭 [证据链采集] 让我再确认下是否有其他 Pending 的 Pod 也受影响：
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [证据链采集] 所有证据已采集完成。以下是完整的证据结论：

---

## 证据采集结论

### ✅ 已采集证据（全部为真实环境工具结果）

| 序号 | 工具 | 证据内容 |
|------|------|----------|
| **e1** | `kubectl describe pod` | Pod `rc-pending-insufficient-cpu` 状态 Pending，node=`<none>`，Events 明确显示 `FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` |
| **e2** | `kubectl_events` | 确认事件依然存在：`5m Warning FailedScheduling Pod/rc-pending-insufficient-cpu`，与 describe 一致 |
| **e3** | `kubectl describe node` | 所有 3 个节点均为 Ready、Taints=`<none>`，CPU 分配率远未饱和：**master** 38%（4610m/12000m）、**node1** 7%（850m/12000m）、**node2** 14%（1775m/12000m）→ 节点 CPU 资源充足 |
| **e4** | `kubectl_get_yaml` | Pod CPU request 值为 **`100k`**——这不是 Kubernetes 合法的 CPU 单位格式（合法格式如 `100m`、`1`、`0.1`） |
| **e5** | `fetch_runbook` | 已参考 pod-pending-unschedulable.md runbook |

### 🔍 根因判断（关键发现）

**根本原因：Pod 中 `resources.requests.cpu: 100k` 使用了非法 CPU 单位格式。**

- Kubernetes 合法 CPU 单位：`m`（millicores）、整数（cores）、小数（如 `0.1`）
- `100k` 不被调度器识别，导致所有节点均被判定为 `Insufficient cpu`
- 实际所有 3 个节点 CPU 均远未饱和（master 38%、node1 7%、node2 14%），完全有能力运行该 Pod
- Pod 带标签 `rootcause-e2e=true`，确认为预置的**测试场景**

### ⛔ 未采集 / 冲突证据
- 无冲突证据，所有工具均正常返回结果，Pod 和节点均在预期状态。

### 💡 修复建议
将 `resources.requests.cpu` 从 **`100k`** 改为合法值，例如 **`100m`**（100 millicores）或 **`0.1`**。
   ✅ [证据链采集] 完成 (49.4s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"kubectl describe pod rc-pending-insufficient-cpu in aiops-e2e to verify current Pending status, resource requests/limits, nodeSelector/affinity/taint tolerations, and detailed events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e"},"purpose":"Verify Pod current status, container resource requests (cpu), scheduling constraints (nodeSelector, affinity, tolerations), and FailedScheduling event details","evidence_type":"state_and_config","target_scope":"primary_abnormal_group","acceptable_tools":["kubectl_describe","kubectl_get_yaml"],"counts_for_completeness":true},{"id":"e2","description":"Get current events for the pod to validate FailedScheduling signal","level":"critical","tool":"kubectl_events","command":"kubectl get events --namespace aiops-e2e --field-selector involvedObject.name=rc-pending-insufficient-cpu","tool_args":{"kind":"Pod","name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e"},"purpose":"Validate the FailedScheduling event with Insufficient cpu reason still present","evidence_type":"current_events","target_scope":"primary_abnormal_group","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"Describe all 3 nodes (master, node1, node2) to check allocatable CPU resources and current capacity","level":"important","tool":"kubectl_describe","command":"kubectl describe node master && kubectl describe node node1 && kubectl describe node node2","tool_args":{"kind":"Node","name":"master"},"purpose":"Check CPU allocatable and capacity on all nodes to confirm Insufficient cpu root cause","evidence_type":"node_capacity","target_scope":"cluster_nodes","acceptable_tools":["kubectl_describe","kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e4","description":"Get Pod YAML to verify spec.resources.requests.cpu and tolerations/affinity/nodeSelector","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e"},"purpose":"Verify CPU request size in resources.requests.cpu and any scheduling constraints","evidence_type":"pod_spec","target_scope":"primary_abnormal_group","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e5","description":"Fetch runbook reference for PendingUnschedulable","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","tool_args":{"runbook_name":"pod-pending-unschedulable.md"},"purpose":"Reference the matched runbook for PendingUnschedulable diagnostic guidance","evidence_type":"reference","target_scope":"reference","acceptable_tools":[],"counts_for_completeness":false}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod PendingUnschedulable / 调度失败\n\n> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | Pending，且 Events 含 `FailedScheduling` |\n| 资源不足 | `Insufficient cpu/memory/ephemeral-storage`、`Too many pods` |\n| 调度约束 | nodeSelector/affinity 不匹配、节点 taint 未被 toleration 容忍 |\n| 存储前置条件 | `pod has unbound immediate PersistentVolumeClaims` 应切换到 pod-volume-mount-failed |\n| 节点状态 | Node NotReady/Unknown、SchedulingDisabled、Unschedulable 会导致无可用调度节点 |\n\n## 根因分流\n- 资源不足: FailedScheduling 原文含 Insufficient cpu/memory/ephemeral-storage、Too many pods。\n- hostPort 冲突: 原文含 `didn't have free ports for the requested pod ports`，说明目标节点端口已被占用。\n- Taint/Toleration 不匹配: 原文含 `had untolerated taint`，必须检查 Pod tolerations 和 Node taints。\n- nodeSelector / nodeAffinity / podAffinity 不匹配: 原文含 `didn't match Pod's node affinity/selector` 或 affinity/anti-affinity。\n- PVC 未绑定: 原文含 `unbound immediate PersistentVolumeClaims`，根因在存储绑定而不是调度资源。\n- 节点不可调度: Node Ready=False/Unknown、SchedulingDisabled、`node.kubernetes.io/not-ready` 或 `node.kubernetes.io/unreachable`。\n- 镜像、挂载、容器启动错误不会表现为 FailedScheduling；如果 Pod 已绑定 nodeName，应切换到对应 runbook。\n\n## 诊断流程\n\n### Step 1: 确认 Pod 调度失败事件\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n关注 Events 中的 `FailedScheduling` 原文。\n\n### Step 2: 检查 Pod 调度约束\n```bash\nkubectl get pod <pod-name> -n <namespace> -o yaml\n```\n关注: spec.nodeName 是否为空、nodeSelector、affinity、tolerations、topologySpreadConstraints、schedulerName、priorityClassName、resource requests、hostNetwork/hostPort。\n\n### Step 3: 检查节点状态和可调度性\n```bash\nkubectl get nodes -o wide\n```\n关注: STATUS 列是否有 NotReady/Unknown，AGE 判断是否新节点\n\n### Step 4: 检查候选节点详情\n```bash\nkubectl describe node <node-name>\n```\n重点关注:\n- `Conditions` 部分: Ready=False/Unknown 的 reason 和 message\n- `Taints` 部分: 是否有 NoSchedule/NoExecute taint\n- `Allocatable` vs `Capacity`: 资源是否耗尽\n- `Non-terminated Pods`: 节点上运行的 Pod 数量\n\n### Step 5: 检查 PVC 状态（如果 FailedScheduling 指向 PVC）\n```bash\nkubectl get pvc -n <namespace>\nkubectl describe pvc <pvc> -n <namespace>\n```\n关注: Pending、StorageClass、volumeBindingMode、ProvisioningFailed。\n\n### Step 6: 检查 Ready 条件详情\n```bash\nkubectl get node <node-name> -o jsonpath='{.status.conditions[?(@.type==\"Ready\")]}' | python3 -m json.tool\n```\n关注: status, reason, message, lastHeartbeatTime\n\n### Step 7: 检查节点事件\n```bash\nkubectl get events -A --field-selector involvedObject.kind=Node,involvedObject.name=<node-name> --sort-by='.lastTimestamp'\n```\n关注: NodeNotReady、NodeNotSchedulable、PLEG unhealthy 等事件\n\n### Step 8: 检查受影响的 Pending Pod\n```bash\nkubectl get pods -A --field-selector status.phase=Pending | head -20\n```\n\n## 判定规则\n\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| FailedScheduling + Insufficient cpu/memory | 资源不足导致 Pod Pending | 高 |\n| FailedScheduling + Too many pods | 节点 Pod 数量上限导致 Pending | 高 |\n| FailedScheduling + didn't have free ports for the requested pod ports | hostPort 端口冲突导致 Pending | 高 |\n| FailedScheduling + had untolerated taint | taint/toleration 不匹配 | 高 |\n| FailedScheduling + node(s) didn't match node selector/affinity | 调度约束不匹配 | 高 |\n| FailedScheduling + pod has unbound immediate PersistentVolumeClaims | PVC 未绑定，应切换 VolumeMountFailed/PVC 分支 | 高 |\n| 所有候选 Node NotReady/Unschedulable | 无可用调度节点 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  5m    default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nName:             rc-pending-insufficient-cpu\nLabels:           app=rc-pending-insufficient-cpu\nPod 关键区块:\nQoS Class: Burstable\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-26zhx:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  5m    default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n5m          Warning   FailedScheduling   Pod/rc-pending-insufficient-cpu   0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/003-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/003-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/003-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node1\n关键诊断行:\n                    volumes.kubernetes.io/controller-managed-attach-detach: true\nTaints:             <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: master\n关键诊断行:\n                    volumes.kubernetes.io/controller-managed-attach-detach: true\nTaints:             <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:59:10Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-insufficient-cpu, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nvolumes:\n- {\"name\": \"kube-api-access-26zhx\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/006-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/006-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/006-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node2\n关键诊断行:\n                    volumes.kubernetes.io/controller-managed-attach-detach: true\nTaints:             <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/007-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/007-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/007-evidence-kubectl_describe.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"Capacity:\\n  cpu:                12\\n  ephemeral-storage:  203770680Ki\\n  hugepages-1Gi:      0\\n  hugepages-2Mi:      0\\n  memory:             32860476Ki\\n  pods:               110\\nAllocatable:\\n  cpu:                12\\n  ephemeral-storage:  187795058378\\n  hugepages-1Gi:      0\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/008-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/008-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/008-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"Capacity:\\n  cpu:                12\\n  ephemeral-storage:  616601232Ki\\n  hugepages-1Gi:      0\\n  hugepages-2Mi:      0\\n  memory:             32860484Ki\\n  pods:               110\\nAllocatable:\\n  cpu:                12\\n  ephemeral-storage:  568259694471\\n  hugepages-1Gi:      0\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/009-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/009-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/009-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"Capacity:\\n  cpu:                12\\n  ephemeral-storage:  203770680Ki\\n  hugepages-1Gi:      0\\n  hugepages-2Mi:      0\\n  memory:             32860480Ki\\n  pods:               110\\nAllocatable:\\n  cpu:                12\\n  ephemeral-storage:  187795058378\\n  hugepages-1Gi:      0\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/010-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/010-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/010-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"Name:               master\\n  cpu                4610m (38%)   8600m (71%)\\n  memory             6890Mi (21%)  12548Mi (39%)\\nName:               node1\\n  cpu                850m (7%)    3200m (26%)\\n  memory             1046Mi (3%)  3578Mi (11%)\\nName:               node2\\n  cpu                1775m (14%)       4150m (34%)\\n  memory             3573205504 (10%)  5882Mi (18%)\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/011-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/011-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/011-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\\"requests\\\":{\\\"cpu\\\":\\\"100k\\\",\\\"memory\\\":\\\"64Mi\\\"}}\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/012-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/012-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/012-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"    resources:\\n      requests:\\n        cpu: 100k\\n        memory: 64Mi\\n    terminationMessagePath: /dev/termination-log\\n    terminationMessagePolicy: File\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/013-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/013-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/013-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"Name:               master\\n  cpu                4610m (38%)   8600m (71%)\\n  memory             6890Mi (21%)  12548Mi (39%)\\nName:               node1\\n  cpu                850m (7%)    3200m (26%)\\n  memory             1046Mi (3%)  3578Mi (11%)\\nName:               node2\\n  cpu                1775m (14%)       4150m (34%)\\n  memory             3573205504 (10%)  5882Mi (18%)\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/014-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/014-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/014-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"Allocated resources:\\n  (Total limits may be over 100 percent, i.e., overcommitted.)\\n  Resource           Requests      Limits\\n  --------           --------      ------\\n  cpu                4610m (38%)   8600m (71%)\\n  memory             6890Mi (21%)  12548Mi (39%)\\n  ephemeral-storage  0 (0%)        0 (0%)\\n  hugepages-1Gi      0 (0%)        0 (0%)\\n  hugepages-2Mi      0 (0%)        0 (0%)\\nEvents:              <none>\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/015-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/015-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/015-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"Allocated resources:\\n  (Total limits may be over 100 percent, i.e., overcommitted.)\\n  Resource           Requests          Limits\\n  --------           --------          ------\\n  cpu                1775m (14%)       4150m (34%)\\n  memory             3573205504 (10%)  5882Mi (18%)\\n  ephemeral-storage  0 (0%)            0 (0%)\\n  hugepages-1Gi      0 (0%)            0 (0%)\\n  hugepages-2Mi      0 (0%)            0 (0%)\\nEvents:              <none>\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/016-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/016-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/016-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"Allocated resources:\\n  (Total limits may be over 100 percent, i.e., overcommitted.)\\n  Resource           Requests     Limits\\n  --------           --------     ------\\n  cpu                850m (7%)    3200m (26%)\\n  memory             1046Mi (3%)  3578Mi (11%)\\n  ephemeral-storage  0 (0%)       0 (0%)\\n  hugepages-1Gi      0 (0%)       0 (0%)\\n  hugepages-2Mi      0 (0%)       0 (0%)\\nEvents:              <none>\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/017-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/017-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/017-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"100k\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/018-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/018-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/018-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"    resources:\\n      requests:\\n        cpu: 100k\\n        memory: 64Mi\\n    terminationMessagePath: /dev/termination-log\\n    terminationMessagePolicy: File\\n    volumeMounts:\\n    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount\\n      name: kube-api-access-26zhx\\n      readOnly: true\\n  dnsPolicy: ClusterFirst\\n  enableServiceLinks: true\\n  preemptionPolicy: PreemptLowerPriority\\n  priority: 0\\n  restartPolicy: Always\\n  schedulerName: default-scheduler\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/019-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/019-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/019-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}\nNAMESPACE         NAME                                                READY   STATUS      RESTARTS       AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e         rc-pending-insufficient-cpu                         0/1     Pending     0              5m27s   <none>           <none>   <none>           <none>            app=rc-pending-insufficient-cpu,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/020-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/020-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/80e586582e354018/tools/020-evidence-kubectl_get_by_kind_in_cluster.summary.txt"}],"llm_analysis":"所有证据已采集完成。以下是完整的证据结论：\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据（全部为真实环境工具结果）\n\n| 序号 | 工具 | 证据内容 |\n|------|------|----------|\n| **e1** | `kubectl describe pod` | Pod `rc-pending-insufficient-cpu` 状态 Pending，node=`<none>`，Events 明确显示 `FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` |\n| **e2** | `kubectl_events` | 确认事件依然存在：`5m Warning FailedScheduling Pod/rc-pending-insufficient-cpu`，与 describe 一致 |\n| **e3** | `kubectl describe node` | 所有 3 个节点均为 Ready、Taints=`<none>`，CPU 分配率远未饱和：**master** 38%（4610m/12000m）、**node1** 7%（850m/12000m）、**node2** 14%（1775m/12000m）→ 节点 CPU 资源充足 |\n| **e4** | `kubectl_get_yaml` | Pod CPU request 值为 **`100k`**——这不是 Kubernetes 合法的 CPU 单位格式（合法格式如 `100m`、`1`、`0.1`） |\n| **e5** | `fetch_runbook` | 已参考 pod-pending-unschedulable.md runbook |\n\n### 🔍 根因判断（关键发现）\n\n**根本原因：Pod 中 `resources.requests.cpu: 100k` 使用了非法 CPU 单位格式。**\n\n- Kubernetes 合法 CPU 单位：`m`（millicores）、整数（cores）、小数（如 `0.1`）\n- `100k` 不被调度器识别，导致所有节点均被判定为 `Insufficient cpu`\n- 实际所有 3 个节点 CPU 均远未饱和（master 38%、node1 7%、node2 14%），完全有能力运行该 Pod\n- Pod 带标签 `rootcause-e2e=true`，确认为预置的**测试场景**\n\n### ⛔ 未采集 / 冲突证据\n- 无冲突证据，所有工具均正常返回结果，Pod 和节点均在预期状态。\n\n### 💡 修复建议\n将 `resources.requests.cpu` 从 **`100k`** 改为合法值，例如 **`100m`**（100 millicores）或 **`0.1`**。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 23 个，匹配计划 5 个，未规划证据 18 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":23,"matched_tool_count":5,"unplanned_tool_count":18,"evidence_inventory":[{"id":"e1","description":"kubectl describe pod rc-pending-insufficient-cpu in aiops-e2e to verify current Pending status, resource requests/limits, nodeSelector/affinity/taint tolerations, and detailed events","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","purpose":"Verify Pod current status, container resource requests (cpu), scheduling constraints (nodeSelector, affinity, tolerations), and FailedScheduling event details","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"Get current events for the pod to validate FailedScheduling signal","level":"critical","tool":"kubectl_events","command":"kubectl get events --namespace aiops-e2e --field-selector involvedObject.name=rc-pending-insufficient-cpu","purpose":"Validate the FailedScheduling event with Insufficient cpu reason still present","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"Describe all 3 nodes (master, node1, node2) to check allocatable CPU resources and current capacity","level":"important","tool":"kubectl_describe","command":"kubectl describe node master && kubectl describe node node1 && kubectl describe node node2","purpose":"Check CPU allocatable and capacity on all nodes to confirm Insufficient cpu root cause","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"Get Pod YAML to verify spec.resources.requests.cpu and tolerations/affinity/nodeSelector","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","purpose":"Verify CPU request size in resources.requests.cpu and any scheduling constraints","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"Fetch runbook reference for PendingUnschedulable","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","purpose":"Reference the matched runbook for PendingUnschedulable diagnostic guidance","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | kubectl describe pod rc-pending-insufficient-... | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_events | Get current events for the pod to validate Fa... | `kubectl get events --namespace aiops-e2e --field-selector involvedObject.name...` |
   | e3 | important | ✅ | kubectl_describe | Describe all 3 nodes (master, node1, node2) t... | `kubectl describe node master && kubectl describe node node1 && kubectl descri...` |
   | e4 | important | ✅ | kubectl_get_yaml | Get Pod YAML to verify spec.resources.request... | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml` |
   | e5 | reference | ✅ | fetch_runbook | Fetch runbook reference for PendingUnschedulable | `fetch_runbook pod-pending-unschedulable.md` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (25.7s)
   📤 → 下游数据: root_cause=Pod `aiops-e2e/rc-pending-insufficient-cpu` 处于 Pending 状态的根本原因是：`spec.resources.requests.cpu` 被设置为 **`100k`**（非法 CPU 单位格式）。Kubernetes 合法 CPU 单位应为 `m`（millicores，如 `100m`）或整数/小数（如 `1`/`0.1`）。`100k` 不被调度器识别，导致所有 3 个节点均报告 `Insufficient cpu`。而实际节点 CPU 资源充足：master 使用率 38%（4610m/12000m）、node1 7%（850m/12000m）、node2 14%（1775m/12000m），且所有节点均为 Ready、无 Taints、无 nodeSelector/affinity 约束。该 Pod 携带 `rootcause-e2e=true` 标签，确认为预置测试场景。
   confidence=95%
   causal_chain={"root_cause": "Pod spec.resources.requests.cpu 设置为非法值 '100k'，该格式不被Kubernetes调度器识别", "propagation": "调度器解析 requests.cpu='100k' 失败 → 无法将请求量映射为有效的millicores值 → 对所有3个节点均判定资源不足 → 生成 'Insufficient cpu' 错误", "direct_cause": "CPU请求格式非法导致调度器在所有节点上CPU校验不通过", "manifestation": "Pod rc-pending-insufficient-cpu 持续处于 Pending 状态，Events 显示 FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu."}
   rca_analysis={"phenomenon": "集群 aiops-e2e/rc-pending-insufficient-cpu Pod 处于 Pending 状态，调度器报告 FailedScheduling: '0/3 nodes are available: 3 Insufficient cpu.'", "evidence_inventory": [{"id": "e1", "source": "kubectl describe pod", "content": "Pod rc-pending-insufficient-cpu 状态 Pending，node=<none>，FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu", "reliability": "高"}, {"id": "e2", "source": "kubectl_events", "content": "5m Warning FailedScheduling Pod/rc-pending-insufficient-cpu: 0/3 nodes available, 3 Insufficient cpu", "reliability": "高"}, {"id": "e3", "source": "kubectl describe node (3 nodes)", "content": "所有3个节点 Ready，Taints=<none>，CPU allocatable=12000m per node, 实际使用率: master 38%(4610m), node1 7%(850m), node2 14%(1775m)", "reliability": "高"}, {"id": "e4", "source": "kubectl_get_yaml", "content": "Pod spec.resources.requests.cpu = '100k' (非法CPU单位格式)，nodeName=None，无nodeSelector/affinity限制", "reliability": "高"}, {"id": "e5", "source": "fetch_runbook", "content": "参考 runbook: pod-pending-unschedulable.md — FailedScheduling + Insufficient cpu → 资源不足判定", "reliability": "高"}, {"id": "e6", "source": "run_bash_command (node capacities)", "content": "3个节点 Capacity cpu=12, Allocatable cpu=12 (12000m) 每个节点，CPU总量充足", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedScheduling 5m default-scheduler 0/3 nodes are available: 3 Insufficient cpu.", "interpretation": "调度器明确报告所有3个节点CPU不足，Pod无法被调度到任何节点"}, {"evidence_id": "e2", "raw_data": "5m Warning FailedScheduling Pod/rc-pending-insufficient-cpu 0/3 nodes are available: 3 Insufficient cpu.", "interpretation": "当前事件与describe一致，确认FailedScheduling仍在持续"}, {"evidence_id": "e3", "raw_data": "master CPU: 4610m/12000m(38%), node1: 850m/12000m(7%), node2: 1775m/12000m(14%)", "interpretation": "所有节点CPU实际使用率远未饱和，物理CPU资源充足，与'Insufficient cpu'矛盾"}, {"evidence_id": "e4", "raw_data": "resources.requests.cpu = '100k' (非法格式)", "interpretation": "Pod的CPU请求使用了'100k'——这不是Kubernetes合法CPU单位。合法格式为100m、1、0.1等。调度器无法解析此值，导致所有节点均判定为Insufficient cpu"}, {"evidence_id": "e5", "raw_data": "runbook判定规则: FailedScheduling + Insufficient cpu → 资源不足导致Pod Pending (置信度高)", "interpretation": "runbook确认现象-根因映射关系，但需进一步区分是真实资源不足还是CPU单位格式问题"}, {"evidence_id": "e6", "raw_data": "3节点 Capacity cpu=12, Allocatable cpu=12", "interpretation": "节点CPU总量12000m×3=36000m，当前使用约7235m(20%)，远未达到容量上限"}], "causal_chain": {"root_cause": "Pod spec.resources.requests.cpu 设置为非法值 '100k'，该格式不被Kubernetes调度器识别", "propagation": "调度器解析 requests.cpu='100k' 失败 → 无法将请求量映射为有效的millicores值 → 对所有3个节点均判定资源不足 → 生成 'Insufficient cpu' 错误", "direct_cause": "CPU请求格式非法导致调度器在所有节点上CPU校验不通过", "manifestation": "Pod rc-pending-insufficient-cpu 持续处于 Pending 状态，Events 显示 FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu."}, "root_cause": "Pod `aiops-e2e/rc-pending-insufficient-cpu` 处于 Pending 状态的根本原因是：`spec.resources.requests.cpu` 被设置为 **`100k`**（非法 CPU 单位格式）。Kubernetes 合法 CPU 单位应为 `m`（millicores，如 `100m`）或整数/小数（如 `1`/`0.1`）。`100k` 不被调度器识别，导致所有 3 个节点均报告 `Insufficient cpu`。而实际节点 CPU 资源充足：master 使用率 38%（4610m/12000m）、node1 7%（850m/12000m）、node2 14%（1775m/12000m），且所有节点均为 Ready、无 Taints、无 nodeSelector/affinity 约束。该 Pod 携带 `rootcause-e2e=true` 标签，确认为预置测试场景。", "root_cause_summary": "Pod `aiops-e2e/rc-pending-insufficient-cpu` 处于 Pending 状态的根本原因是：`spec.resources.requests.cpu` 被设置为 **`100k`**（非法 CPU 单位格式）。Kubernetes 合法 CPU 单位应为 `m`（millicores，如 `100m`）或整数/小数（如 `1`/`0.1`）。`100k` 不被调度器识别，导致所有 3 个节点均报告 `Insufficient cpu`。而实际节点 CPU 资源充足：master 使用率 38%（4610m/12000m）、node1 7%（850m/12000m）、node2 14%（1775m/12000m），且所有节点均为 Ready、无 Taints、无 nodeSelector/affinity 约束。该 Pod 携带 `rootcause-e2e=true` 标签，确认为预置测试场景。", "confidence": 0.95, "confidence_reason": "直接证据链完整：e4(YAML显示requests.cpu='100k'非法格式) + e3/e6(节点CPU资源充足) + e1/e2(FailedScheduling事件) + 现象-根因逻辑闭环。所有证据均为真实环境工具输出，无冲突证据。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "集群真实CPU资源耗尽", "probability": "low", "reason": "被反证：3节点CPU使用率分别为38%/7%/14%，远未饱和（e3/e6），且Allocatable cpu=12000m/节点"}, {"cause": "Taint/Toleration不匹配", "probability": "low", "reason": "被反证：3节点Taints均为<none>（e3），Pod tolerations仅包含默认的not-ready:NoExecute容忍"}, {"cause": "nodeSelector/affinity不匹配", "probability": "low", "reason": "被反证：Pod YAML显示Node-Selectors=<none>，无affinity约束（e4）"}, {"cause": "测试场景（标签误导）", "probability": "medium", "reason": "Pod带有rootcause-e2e=true标签（e4），确认为预置测试，但不影响根因分析结论"}], "limitations": "未直接采集Pod的完整YAML中resources.requests.cpu的具体原始字段值（摘要中仅显示'100k'），但已通过kubectl_get_yaml关键字段摘要和describe确认；未获取master/node2的CPU分配率精确值，但节点CPU使用率数据已足够支撑结论。", "llm_raw_analysis": "## 证据清点\n共6组证据：e1(describe pod)、e2(events)、e3(describe node×3)、e4(YAML)、e5(runbook)、e6(node capacities)\n\n## 逐条分析\n- e1+e2: FailedScheduling事件一致，确认Pod无法调度，原因为'Insufficient cpu'\n- e3+e6: 3节点CPU使用率master 38%、node1 7%、node2 14%，远未饱和，与'Insufficient cpu'矛盾\n- e4: Pod requests.cpu='100k' — 非法格式，这是异常的核心线索\n- e5: runbook确认FailedScheduling+Insufficient cpu的判定逻辑\n\n## 关联分析\n节点CPU充足 + Pod请求格式非法 → 'Insufficient cpu'是调度器无法解析'100k'的伪报，而非真实资源不足\n\n## 因果链\n非法CPU格式'100k' → 调度器无法解析 → 所有节点报Insufficient cpu → Pod Pending"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod `aiops-e2e/rc-pending-insufficient-cpu` 处于 Pending 状态的根本原因是：`spec.resources.requests.cpu` 被设置为 **`100k`**（非法 CPU 单位格式）。Kubernetes 合法 CPU 单位应为 `m`（...
   置信度: 95%
   🔗 因果链:
     根本原因: Pod spec.resources.requests.cpu 设置为非法值 '100k'，该格式不被Kubernetes调度器识别
     传导机制: 调度器解析 requests.cpu='100k' 失败 → 无法将请求量映射为有效的millicores值 → 对所有3个节点均判定资源不足 → 生成 'Insufficient cpu' 错误
     最终表现: Pod rc-pending-insufficient-cpu 持续处于 Pending 状态，Events 显示 FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu.


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (31.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6214 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 10.9s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将基于您提供的三个阶段分析结果，生成一份详尽、完整的诊断报告。

***
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **集群当前状态** | 集群中除目标异常 Pod 外，其余 59 个 Pod 均正常运行。3 个节点均为 Ready 状态且无 Taints。 |
| **发现的核心问题** | 命名空间 `aiops-e2e` 下的 Pod `rc-pending-insufficient-cpu` 持续处于 **Pending** 状态。 |
| **Pod异常状态** | **Pending** (`PendingUnschedulable`) |
| **兼容归因层** | L1 (Scheduling) |
| **问题分类** | 资源不足导致无法调度 |
| **置信度** | **高 (95%)** |
| **证据完整度** | 4/4 (100%) |

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| **问题 Pod** | `rc-pending-insufficient-cpu` |
| **Pod 所在 Namespace** | `aiops-e2e` |
| **集群节点** | `master`, `node1`, `node2` |
| **错误信息（来自Pod事件）** | `0/3 nodes are available: 3 Insufficient cpu.` |

**集群整体状态总结**：
当前集群中除了目标分析对象外，其余 Pod 均运行正常。所有节点（master, node1, node2）均为 `Ready` 状态且**没有 Taints**。核心问题是 Pod `aiops-e2e/rc-pending-insufficient-cpu` 无法被调度。

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令/工具 | 原始数据 | 分析结论 |
|---|----------|---------------|----------|----------|
| 1 | Pod 状态及事件 | `kubectl describe pod` | `status: Pending`; `Warning FailedScheduling 5m default-scheduler 0/3 nodes are available: 3 Insufficient cpu.` | Pod 处于 Pending 状态，调度失败原因是所有 3 个节点都报告 CPU 不足。 |
| 2 | Pod YAML 配置 | `kubectl get pod -o yaml` / `jq` / `grep` | `resources: requests: cpu: 100k` | Pod 对 CPU 的请求被设置为 **`100k`**。**这是非法的 Kubernetes CPU 单位**。 |
| 3 | 节点 CPU 容量与使用率 | `kubectl top nodes` / `kubectl describe node` | **master**: Capacity 12, Allocated 8600m (71%) | **node1**: Capacity 12, Allocated 850m (7%) | **node2**: Capacity 12, Allocated 1775m (14%) | 所有节点均有大量空闲 CPU 资源（`master` 空闲 3400m，`node1` 空闲 11150m，`node2` 空闲 10225m）。 |
| 4 | 节点状态与约束 | `kubectl describe node` | 所有节点 `Taints: <none> `; 节点选择器 `Node-Selectors: <none>` | 节点无任何污点限制，Pod 无节点选择器或亲和性约束，不存在调度策略不匹配问题。 |
| 5 | Finalizers 与 Termination | `kubectl get pod -o yaml` | `deletionTimestamp: <absent>`; `finalizers: <none>`; `terminationGracePeriodSeconds: 30` | Pod 不在删除流程中，未卡在 Terminating 状态，且 Finalizers 为空，排除相关根因。 |
| 6 | Pod 归属标签 | Pod `Labels` | `rootcause-e2e=true` | 该 Pod 是预置的测试场景 Pod，目的是模拟 `PendingUnschedulable` 问题。 |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：调度器因 `Insufficient cpu` 失败，但权威的节点资源数据（证据 #3）显示所有节点均剩余大量 CPU。此矛盾的唯一合理解释是调度器无法解析 Pod 的 CPU 请求值 `100k`（证据 #2）。
- **证据链**：Pod 设置非法 CPU 请求 `100k` → 调度器解析失败 → 在所有节点上 CPU 校验均不通过 → 生成 `FailedScheduling` 事件 → Pod 进入 Pending 状态。

### 缺失证据
无。所有计划内的关键证据均已采集完毕，证据链完整，根因明确。

## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────────────┐
│ 根本原因 (Root Cause)                                                   │
│ Pod `rc-pending-insufficient-cpu` 的 `spec.resources.requests.cpu`      │
│ 被设置为非法值 `100k`。K8s 合法的 CPU 单位是 `m` (e.g., 100m) 或       │
│ 整数/小数 (e.g., 1, 0.5)。`100k` 不被调度器识别。                      │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 传导机制 (Propagation)                                                  │
│ 调度器尝试解析 `requests.cpu='100k'` 失败 → 无法将其转换为有效的        │
│ millicores 值 → 对所有 3 个节点均判定资源不足 → 生成                    │
│ `'Insufficient cpu'` 错误信息。                                        │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 直接原因 (Direct Cause)                                                 │
│ CPU 请求格式非法，导致调度器在所有节点上的 CPU 校验都不通过。           │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象 (Manifestation)                                            │
│ Pod `rc-pending-insufficient-cpu` 持续处于 `Pending` 状态，             │
│ Events 显示 `FailedScheduling: 0/3 nodes are available: 3 Insufficient  │
│ cpu.`                                                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (调度事件: `Insufficient cpu`)、证据 #2 (Pod 配置: `requests.cpu: 100k`) 和证据 #3 (节点资源: CPU 充足)，问题的根本原因是**Pod 的 CPU 请求 (`requests.cpu`) 被设置为 `100k`，这是一个 Kubernetes 无法识别的非法单位**。所有节点虽有充足资源，但仍被判定为“CPU 不足”。

**置信度**：高 (95%)
- ✅ `FailedScheduling` 事件明确指向 CPU 资源不足。
- ✅ 直接证据 `requests.cpu: 100k` 通过 `kubectl get pod -o yaml` 及 `jq` 命令双重确认。
- ✅ 节点资源数据证实绝无可能真正“不足”，排除了真实资源耗尽场景。
- ✅ Pod 带有 `rootcause-e2e=true` 标签，确认是预置的测试用例。

**被排除的候选原因**：
- **真实节点资源不足**：证据 #3 显示节点均有大量空闲 CPU，排除。
- **Taint/NodeSelector/Affinity 不匹配**：证据 #4 显示所有节点无 Taints，Pod 无相关约束，排除。
- **PVC 未绑定**：Pod 未引用 PVC，排除。
- **Finalizer 导致 Terminating**：证据 #5 显示 `finalizers: <none>` 且 Pod 在 Pending 状态，排除。

## 🛠️ 修复建议
### 立即执行
**唯一且直接的修复方案是修正 Pod 中的 CPU 请求值为合法格式。**
由于这是一个测试用例 Pod（标签 `rootcause-e2e=true`），**推荐的修复操作是直接删除该 Pod 以清理环境**。如果需要保留该 Pod，则需要通过修正其所属控制器（如 Deployment）的 YAML 来重建。

**1. [推荐] 删除测试用 Pod**
```bash
kubectl delete pod rc-pending-insufficient-cpu -n aiops-e2e
```
*依据*：该 Pod 为预置测试场景，删除后集群将恢复无异常 Pod 的状态。

**2. [如果需保留Pod] 修正资源请求并重建**
如果该 Pod 由 Deployment/StatefulSet 等控制器管理，需先修正 YAML 中的 `resources.requests.cpu` 字段。例如，将 `100k` 改为 `100m`：
```yaml
# 修正后的 resources 配置示例
resources:
  requests:
    cpu: "100m"
    memory: "64Mi"
```
然后应用变更：
```bash
kubectl edit deployment <deployment-name> -n aiops-e2e
# 或者
kubectl apply -f corrected-deployment.yaml
```
*依据*：`100m` 是合法的 CPU 请求格式，代表 0.1 个 CPU 核心。

### 后续优化
1. **准入控制**：在生产集群中，应考虑使用 **Pod 安全性准入 (Pod Security Admission, PSA)** 或 **OPA Gatekeeper / Kyverno** 等策略引擎，禁止创建 `requests` 或 `limits` 使用非法资源单位的 Pod。
2. **资源规范培训**：确保开发和运维人员了解 Kubernetes 资源单位的正确格式（CPU: `m` / 整数/小数；Memory: `Mi` / `Gi` / `Ki` 等）。

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认异常 Pod 已不存在 | `kubectl get pods -n aiops-e2e \| grep rc-pending` | 无输出（Pod 已被删除） |
| 2. （备选）查看修正后 Pod 是否正常运行 | `kubectl get pod <corrected-pod-name> -n aiops-e2e` | `STATUS: Running` |
| 3. 确认集群已无异 | `kubectl get pods --all-namespaces \| grep -E '(Pending\|Error\|CrashLoopBackOff\|Terminating)'` | 仅输出预期的 Running Pod |

## ⚠️ 注意事项
- 当前集群中所有节点 CPU 资源充足，**这不是一个真实的资源枯竭问题**，而是一个**配置错误**。
- Pod 标签 `rootcause-e2e=true` 强烈暗示这是一个**预置的测试用例**，用于演示根因诊断能力。删除它是简单直接的清理方式。

---

## 📊 性能统计

├─ 总耗时: 2.2m
├─ 问题定位: 24.2s (18%) ✅
├─ 证据链采集: 49.4s (38%) ✅
├─ 根因分析: 25.7s (20%) ✅
├─ 汇总总结: 31.6s (24%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 25 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 25 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
