======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 44e7746f2bd94678]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我先扫描全局 Pod 状态，看看当前集群中所有 Pod 的运行情况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 发现了异常 Pod！让我查看一下这个 Pending 状态的 Pod 的详细信息。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  29s   default-scheduler  0/3 nodes are available: 3 Insuffi
   💭 [问题定位] 现在让我获取对应这个异常类型的 runbook 来参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在我来看看节点资源情况，确认 Insufficient cpu 的具体状况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-cpu   0/1     Pending   0          36s   <none>   <
   💭 [问题定位] 好了，我已经掌握了足够的信息。下面是我的诊断结论：

---

## 诊断结论

### 全局 Pod 扫描
集群共 **65 个 Pod**，分布在 `aiops-e2e`、`kube-system`、`monitoring` 等命名空间。

| 状态 | 数量 |
|------|------|
| ✅ Running | **59** |
| ⏳ Pending | **1** |

### 当前异常 Pod 列表

| 命名空间 | Pod 名称 | 状态 | 异常类型 |
|----------|----------|------|----------|
| `aiops-e2e` | `rc-pending-insufficient-cpu` | Pending | **PendingUnschedulable** |

---

### 异常分析

**Pod: `rc-pending-insufficient-cpu`（aiops-e2e 命名空间）**

| 字段 | 内容 |
|------|------|
| **pod_status_keyword** | `Pending` |
| **pod_abnormal_type** | `PendingUnschedulable` |
| **status_category** | `scheduling` |
| **兼容层 (layer)** | **L1** |
| **核心事件** | `FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu.` |
| **3 个节点状态** | 全部 Ready（master/node1/node2） |

**根因定位：** ✅ 集群中 3 个节点全部处于 Ready 状态，但**所有节点的 CPU 资源均已耗尽**，没有足够剩余 CPU 来满足该 Pod 的 requests。调度器找不到可调度节点，也找不到可抢占的受害者 Pod。

---

### 输出总结

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **layer_name** | PendingUnschedulable - CPU 资源不足 |
| **layers** | L1 |
| **confidence** | 高（明确 FailedScheduling + Insufficient cpu） |
| **pod_status_keyword** | Pending |
| **pod_abnormal_type** | PendingUnschedulable |
| **status_category** | scheduling |
| **abnormal_pods** | [`aiops-e2e/rc-pending-insufficient-cpu`] |
| **abnormal_groups** | PendingUnschedulable |
| **key_entities** | Pod: `rc-pending-insufficient-cpu`, Nodes: `master`, `node1`, `node2` |
| **possible_scenarios** | 集群所有节点的 CPU 资源已被现有 Pod 占满，新 Pod 无法调度；需扩容节点或释放已有 Pod 的 CPU 资源 |
   ✅ [问题定位] 完成 (25.1s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '集群所有节点的CPU资源已被现有Pod占满，新Pod无法调度', 'probability': '高', 'reason': 'FailedScheduling事件明确指示3 Insufficient cpu，且3个节点均为Ready状态，无其他调度约束问题'}]
   entities=[{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}]
   reasoning=集群中存在1个异常Pod rc-pending-insufficient-cpu（aiops-e2e命名空间），状态为Pending。kubectl describe显示FailedScheduling事件：0/3 nodes are available: 3 Insufficient cpu，所有3个节点（master/node1/node2）均为Ready状态但CPU资源已耗尽。Pod异常类型为PendingUnschedulable，status_category为scheduling，根因属于调度层问题，归一化兼容层为L1。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable - CPU 资源不足", "confidence": 1.0, "reasoning": "集群中存在1个异常Pod rc-pending-insufficient-cpu（aiops-e2e命名空间），状态为Pending。kubectl describe显示FailedScheduling事件：0/3 nodes are available: 3 Insufficient cpu，所有3个节点（master/node1/node2）均为Ready状态但CPU资源已耗尽。Pod异常类型为PendingUnschedulable，status_category为scheduling，根因属于调度层问题，归一化兼容层为L1。", "abnormal_pods": [{"name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}], "possible_scenarios": [{"scenario": "集群所有节点的CPU资源已被现有Pod占满，新Pod无法调度", "probability": "高", "reason": "FailedScheduling事件明确指示3 Insufficient cpu，且3个节点均为Ready状态，无其他调度约束问题"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-insufficient-cpu                         0/1     Pending     0              27s     <none>           <none>   <none>           <none>            app=rc-pending-insufficient-cpu,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 100%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 好的，现在直接按照既有 evidence_plan 执行采证。先从 critical 级的工具开始，并行调用可独立的工具。

## 第一步：并行调用关键证据工具
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME\nmaster   Ready    control-plane
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
68s         Warning   FailedScheduling   Pod/rc-pending-insufficient-cpu   0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption v
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  68s   default-scheduler  0/3 nodes are available: 3 Insuffi
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:59:10Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizer
   💭 [证据链采集] 很好！节点状态和 Pod 描述已确认。现在并行执行 Prometheus 查询，验证 CPU 资源分配和实际使用情况。
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 execute_prometheus_instant_query 执行成功但结果为空；这表示查询未命中数据，不能视为已采集到指标值。
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 execute_prometheus_instant_query 执行成功但结果为空；这表示查询未命中数据，不能视为已采集到指标值。
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"instance":"10.2.0.49:9100"},"value":[1779346824.125,"4.562172695164814"]},{"metric":{"instance":"10.2.0.50:9100"},"value":[17793
   💭 [证据链采集] Prometheus 的 `kube_node_status_allocatable_cpu_cores` 和 `kube_pod_resource_request` 指标未命中数据。让我试试其他可用的指标来获取节点 CPU 容量和已分配资源。
   💭 [证据链采集] 调用工具: get_metric_names
   💭 [证据链采集] 工具结果: get_metric_names (success)
      📄 get_metric_names 返回 status=success，包含大量 Prometheus 指标名称列表（截断显示），覆盖 node、alertmanager、apiserver、container、controller_runtime 等多个维度。
key_facts: ["status: success", "返回了大量 Prometheus 指标名称，涵盖 node_memory,
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "Capacity:\n  cpu:                12\n  ephemeral-storage:  203770680Ki\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32860476Ki\n  pods:        
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "Capacity:\n  cpu:                12\n  ephemeral-storage:  616601232Ki\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32860484Ki\n  pods:        
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "Capacity:\n  cpu:                12\n  ephemeral-storage:  203770680Ki\n  hugepages-1Gi:      0\n  hugepages-2Mi:      0\n  memory:             32860480Ki\n  pods:        
   💭 [证据链采集] 现在来检查这个 Pod 要求的 CPU 资源量：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "    Requests:\n      cpu:        100k\n      memory:     64Mi\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] 发现关键线索！让我确认一下这个 `100k` 是否写错了：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"requests\": {\n    \"cpu\": \"100k\",\n    \"memory\": \"64Mi\"\n  }\n}\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"name\": \"master\",\n  \"allocatable_cpu\": \"12\"\n}\n{\n  \"name\": \"node1\",\n  \"allocatable_cpu\": \"12\"\n}\n{\n  \"name\": \"node2\",\n  \"allocatable_cpu\"
   💭 [证据链采集] 现在所有关键证据都已采集完毕，让我总结结论。

---

## ✅ 证据采集结论

### 已采集的关键证据

| 证据项 | 级别 | 结果 |
|--------|------|------|
| **ev1 - Pod Describe** | critical ✅ | `Warning FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` |
| **ev2 - FailedScheduling Events** | critical ✅ | 唯一事件：3 个节点全部 `Insufficient cpu`，无其他调度障碍（无 taint/affinity/volume 问题） |
| **ev3 - 节点 CPU 容量** | important ✅ | master=12, node1=12, node2=12，共 36 核可分配 CPU |
| **ev4 - 节点 CPU 使用率** | important ✅ | node1(10.2.0.49)=~4.6%, node2(10.2.0.50)=~14.4%, master(10.2.0.48)=~21.7% — **CPU 使用率并不高** |
| **ev5 - Pod YAML 配置** | important ✅ | 无 nodeSelector/affinity/taints 约束，QoS=Burstable，仅含基础 tolerations |
| **ev6 - 节点已分配资源** | important ✅ | master=4610m(38%), node1=850m(7%), node2=1775m(14%) — 各节点远未到 100% |
| **ev7 - 节点状态** | optional ✅ | 3 节点均为 **Ready**，无异常 |

### 核心发现：Pod 资源请求值写错导致调度失败

通过 `kubectl get pod -o json` 发现 Pod 的 CPU requests 写的是 **`100k`**（即 100,000 个毫核），换算为 **100 个 CPU 核**，而每个节点只有 **12 核**可分配！

- `100k millicores = 100 个 CPU 核` > 任何节点的 `12 核` 容量
- 所以调度器显示 **3 Insufficient cpu**（3 个节点都不够）

### 根因结论
**配置错误**：Pod `rc-pending-insufficient-cpu` 的 resources.requests.cpu 被设置为 `100k`（即 100 核），远超集群中任何节点的 CPU 容量（每节点 12 核）。这不是真正的资源耗尽问题，而是**人为配置错误**导致的调度失败。正常值应为 `100m`（0.1 核）而非 `100k`。
   ✅ [证据链采集] 完成 (49.1s)
   📤 → 下游数据: evidence_items=9/11
   evidence_analysis={"evidence_plan":[{"id":"ev1-critical-describe-pod","description":"Describe 异常 Pod rc-pending-insufficient-cpu 获取 FailedScheduling 原文确认 CPU 资源不足","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e","resource_type":"pod"},"purpose":"验证 FailedScheduling 事件中 '3 Insufficient cpu' 原文，确认资源不足是唯一调度失败原因","evidence_type":"pod_events","target_scope":"Pod/aiops-e2e/rc-pending-insufficient-cpu","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev2-critical-events-unschedulable","description":"按命名空间范围获取调度相关事件，验证是否还有其他 FailedScheduling 或调度约束冲突","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector reason=FailedScheduling","tool_args":{"namespace":"aiops-e2e","field_selector":"reason=FailedScheduling"},"purpose":"采集所有 FailedScheduling 事件确认是否存在除 CPU 外的其他调度障碍","evidence_type":"cluster_events","target_scope":"Namespace/aiops-e2e","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev3-important-node-resources","description":"通过 Prometheus 查询各节点 CPU allocatable 和已使用量，验证节点 CPU 资源是否已满","level":"important","tool":"execute_prometheus_instant_query","command":"sum(kube_node_status_allocatable_cpu_cores) by (node)","tool_args":{"query":"sum(kube_node_status_allocatable_cpu_cores) by (node)","time":""},"purpose":"验证集群各节点总可分配 CPU 核数，确认资源维度","evidence_type":"prometheus_metric","target_scope":"Node/all","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev4-important-node-cpu-usage","description":"通过 Prometheus 查询各节点 CPU 使用率，验证 CPU 是否已耗尽","level":"important","tool":"execute_prometheus_instant_query","command":"sum(node_cpu_seconds_total{mode!=\"idle\"}) by (instance) / sum(node_cpu_seconds_total) by (instance) * 100","tool_args":{"query":"sum(rate(node_cpu_seconds_total{mode!=\"idle\"}[5m])) by (instance) / sum(rate(node_cpu_seconds_total[5m])) by (instance) * 100","time":""},"purpose":"验证各节点 CPU 使用率是否接近 100%，确认 CPU 耗尽导致 Pod 无法调度","evidence_type":"prometheus_metric","target_scope":"Node/all","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev5-important-pod-spec-config","description":"获取 Pod YAML 确认 request/limit 配置及调度约束（nodeSelector/affinity/tolerations）","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e","resource_type":"pod"},"purpose":"验证 Pod 的资源请求量（cpu request/limit）以及是否存在 nodeSelector/affinity/taints 等调度约束","evidence_type":"pod_spec","target_scope":"Pod/aiops-e2e/rc-pending-insufficient-cpu","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"ev6-important-pod-requested-resources","description":"通过 Prometheus 查询各节点已分配 Pod 资源总量，验证节点是否已过载分配","level":"important","tool":"execute_prometheus_instant_query","command":"sum(kube_pod_resource_request{resource=\"cpu\"}) by (node)","tool_args":{"query":"sum(kube_pod_resource_request{resource=\"cpu\"}) by (node)","time":""},"purpose":"查看各节点上 Pod 已经请求的 CPU 总量，验证 allocatable 是否已被占满","evidence_type":"prometheus_metric","target_scope":"Node/all","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev7-optional-node-conditions","description":"确认三个节点的 Ready/Unschedulable 条件状态","level":"optional","tool":"run_bash_command","command":"kubectl get nodes -o wide","tool_args":{"command":"kubectl get nodes -o wide"},"purpose":"验证 master/node1/node2 节点状态是否均为 Ready，排除节点不可用导致调度失败","evidence_type":"node_status","target_scope":"Node/all","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME\\nmaster   Ready    control-plane   238d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32\\nnode1    Ready    <none>          238d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32\\nnode2    Ready    <none>          238d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/001-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/001-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/001-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n68s         Warning   FailedScheduling   Pod/rc-pending-insufficient-cpu   0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  68s   default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nName:             rc-pending-insufficient-cpu\nLabels:           app=rc-pending-insufficient-cpu\nPod 关键区块:\nQoS Class: Burstable\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-26zhx:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  68s   default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:59:10Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-insufficient-cpu, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nvolumes:\n- {\"name\": \"kube-api-access-26zhx\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/004-evidence-kubectl_get_yaml.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"execute_prometheus_instant_query 执行成功但结果为空；这表示查询未命中数据，不能视为已采集到指标值。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/005-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/005-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/005-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"execute_prometheus_instant_query 执行成功但结果为空；这表示查询未命中数据，不能视为已采集到指标值。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/006-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/006-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/006-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"instance\":\"10.2.0.49:9100\"},\"value\":[1779346824.125,\"4.562172695164814\"]},{\"metric\":{\"instance\":\"10.2.0.50:9100\"},\"value\":[1779346824.125,\"14.437428144303658\"]},{\"metric\":{\"instance\":\"10.2.0.48:9100\"},\"value\":[1779346824.125,\"21.71378780905588\"]}]}}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/007-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/007-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/007-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"get_metric_names","data":"get_metric_names 返回 status=success，包含大量 Prometheus 指标名称列表（截断显示），覆盖 node、alertmanager、apiserver、container、controller_runtime 等多个维度。\nkey_facts: [\"status: success\", \"返回了大量 Prometheus 指标名称，涵盖 node_memory, ALERTS, alertmanager, apiserver, cadvisor, container, controller_runtime 等类别\", \"raw_preview 中的指标列表被截断（末尾为 controller_runtime_reconcile_panics_total）\"]\nmissing: [\"指标列表未完整显示，raw_preview 被截断（raw_chars=52697 但预览只显示了部分）\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/008-evidence-get_metric_names.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/008-evidence-get_metric_names.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/008-evidence-get_metric_names.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"Capacity:\\n  cpu:                12\\n  ephemeral-storage:  203770680Ki\\n  hugepages-1Gi:      0\\n  hugepages-2Mi:      0\\n  memory:             32860476Ki\\n  pods:               110\\nAllocatable:\\n  cpu:                12\\n  ephemeral-storage:  187795058378\\n  hugepages-1Gi:      0\\n  hugepages-2Mi:      0\\n  memory:             32758076Ki\\n  pods:               110\\n--\\n  Namespace                   Name                                            CPU Requests  CPU Limits  Memory Requests  Memory Limits  Age\\n  ---------                   ----                                            ------------  ----------  ---------------  -------------  ---\\n  admin                       gpu-metax-mo-metax-operator-5d98db7655-mrv9w    0 (0%)        0 (0%)      0 (0%)           0 (0%)         2d4h\\n  admin                       metax-gpu-label-jr8jw                           0 (0%)        0 (0%)      0 (0%)           0 (0%)         2d4h\\n  aiops                       aiops-copilot-79989db88d-8lrt9                  250m (2%)     1 (8%)      512Mi (1%)       2Gi (6%)       3h35m\\n  default                     cloud-agent-7n4gj                               0 (0%)        0 (0%)      0 (0%)           0 (0%)         2d21h\\n--\\n  Resource           Requests     Limits\\n  --------           --------     ------\\n  cpu                850m (7%)    3200m (26%)\\n  memory             1046Mi (3%)  3578Mi (11%)\\n  ephemeral-storage  0 (0%)       0 (0%)\\n  hugepages-1Gi      0 (0%)       0 (0%)\\n  hugepages-2Mi      0 (0%)       0 (0%)\\nEvents:              <none>\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/009-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/009-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/009-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"Capacity:\\n  cpu:                12\\n  ephemeral-storage:  616601232Ki\\n  hugepages-1Gi:      0\\n  hugepages-2Mi:      0\\n  memory:             32860484Ki\\n  pods:               110\\nAllocatable:\\n  cpu:                12\\n  ephemeral-storage:  568259694471\\n  hugepages-1Gi:      0\\n  hugepages-2Mi:      0\\n  memory:             32758084Ki\\n  pods:               110\\n--\\n  Namespace                   Name                                                 CPU Requests  CPU Limits  Memory Requests  Memory Limits  Age\\n  ---------                   ----                                                 ------------  ----------  ---------------  -------------  ---\\n  admin                       gpu-operator-6dfcc5f6b6-7jqcq                        200m (1%)     500m (4%)   100Mi (0%)       350Mi (1%)     2d21h\\n  admin                       metax-gpu-label-bwmrx                                0 (0%)        0 (0%)      0 (0%)           0 (0%)         2d4h\\n  default                     cloud-agent-sqzp7                                    0 (0%)        0 (0%)      0 (0%)           0 (0%)         2d21h\\n  default                     nfs-client-provisioner-6fcd4994c9-rjzv5              0 (0%)        0 (0%)      0 (0%)           0 (0%)         23d\\n--\\n  Resource           Requests      Limits\\n  --------           --------      ------\\n  cpu                4610m (38%)   8600m (71%)\\n  memory             6890Mi (21%)  12548Mi (39%)\\n  ephemeral-storage  0 (0%)        0 (0%)\\n  hugepages-1Gi      0 (0%)        0 (0%)\\n  hugepages-2Mi      0 (0%)        0 (0%)\\nEvents:              <none>\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/010-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/010-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/010-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"Capacity:\\n  cpu:                12\\n  ephemeral-storage:  203770680Ki\\n  hugepages-1Gi:      0\\n  hugepages-2Mi:      0\\n  memory:             32860480Ki\\n  pods:               110\\nAllocatable:\\n  cpu:                12\\n  ephemeral-storage:  187795058378\\n  hugepages-1Gi:      0\\n  hugepages-2Mi:      0\\n  memory:             32758080Ki\\n  pods:               110\\n--\\n  Namespace                   Name                                            CPU Requests  CPU Limits  Memory Requests  Memory Limits  Age\\n  ---------                   ----                                            ------------  ----------  ---------------  -------------  ---\\n  admin                       metax-gpu-label-np92c                           0 (0%)        0 (0%)      0 (0%)           0 (0%)         2d4h\\n  default                     cloud-agent-k6m8n                               0 (0%)        0 (0%)      0 (0%)           0 (0%)         2d21h\\n  kube-system                 calico-node-d2dhp                               250m (2%)     0 (0%)      0 (0%)           0 (0%)         212d\\n  kube-system                 kube-multus-ds-x7h9s                            100m (0%)     100m (0%)   50Mi (0%)        50Mi (0%)      212d\\n--\\n  Resource           Requests          Limits\\n  --------           --------          ------\\n  cpu                1775m (14%)       4150m (34%)\\n  memory             3573205504 (10%)  5882Mi (18%)\\n  ephemeral-storage  0 (0%)            0 (0%)\\n  hugepages-1Gi      0 (0%)            0 (0%)\\n  hugepages-2Mi      0 (0%)            0 (0%)\\nEvents:              <none>\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/011-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/011-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/011-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"    Requests:\\n      cpu:        100k\\n      memory:     64Mi\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/012-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/012-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/012-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"requests\\\": {\\n    \\\"cpu\\\": \\\"100k\\\",\\n    \\\"memory\\\": \\\"64Mi\\\"\\n  }\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/013-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/013-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/013-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"name\\\": \\\"master\\\",\\n  \\\"allocatable_cpu\\\": \\\"12\\\"\\n}\\n{\\n  \\\"name\\\": \\\"node1\\\",\\n  \\\"allocatable_cpu\\\": \\\"12\\\"\\n}\\n{\\n  \\\"name\\\": \\\"node2\\\",\\n  \\\"allocatable_cpu\\\": \\\"12\\\"\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/014-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/014-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/44e7746f2bd94678/tools/014-evidence-run_bash_command.summary.txt"}],"llm_analysis":"现在所有关键证据都已采集完毕，让我总结结论。\n\n---\n\n## ✅ 证据采集结论\n\n### 已采集的关键证据\n\n| 证据项 | 级别 | 结果 |\n|--------|------|------|\n| **ev1 - Pod Describe** | critical ✅ | `Warning FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` |\n| **ev2 - FailedScheduling Events** | critical ✅ | 唯一事件：3 个节点全部 `Insufficient cpu`，无其他调度障碍（无 taint/affinity/volume 问题） |\n| **ev3 - 节点 CPU 容量** | important ✅ | master=12, node1=12, node2=12，共 36 核可分配 CPU |\n| **ev4 - 节点 CPU 使用率** | important ✅ | node1(10.2.0.49)=~4.6%, node2(10.2.0.50)=~14.4%, master(10.2.0.48)=~21.7% — **CPU 使用率并不高** |\n| **ev5 - Pod YAML 配置** | important ✅ | 无 nodeSelector/affinity/taints 约束，QoS=Burstable，仅含基础 tolerations |\n| **ev6 - 节点已分配资源** | important ✅ | master=4610m(38%), node1=850m(7%), node2=1775m(14%) — 各节点远未到 100% |\n| **ev7 - 节点状态** | optional ✅ | 3 节点均为 **Ready**，无异常 |\n\n### 核心发现：Pod 资源请求值写错导致调度失败\n\n通过 `kubectl get pod -o json` 发现 Pod 的 CPU requests 写的是 **`100k`**（即 100,000 个毫核），换算为 **100 个 CPU 核**，而每个节点只有 **12 核**可分配！\n\n- `100k millicores = 100 个 CPU 核` > 任何节点的 `12 核` 容量\n- 所以调度器显示 **3 Insufficient cpu**（3 个节点都不够）\n\n### 根因结论\n**配置错误**：Pod `rc-pending-insufficient-cpu` 的 resources.requests.cpu 被设置为 `100k`（即 100 核），远超集群中任何节点的 CPU 容量（每节点 12 核）。这不是真正的资源耗尽问题，而是**人为配置错误**导致的调度失败。正常值应为 `100m`（0.1 核）而非 `100k`。","collection_summary":"计划 6 项，实际采集 4 项，未采集 2 项，完整度 67%；其中真实环境证据 8/10 项，完整度 80%；实际执行工具 16 个，匹配计划 5 个，未规划证据 11 个","plan_total":6,"plan_collected":4,"plan_completeness":0.6666666666666666,"environment_evidence_total":10,"environment_evidence_collected":8,"environment_evidence_completeness":0.8,"executed_tool_count":16,"matched_tool_count":5,"unplanned_tool_count":11,"evidence_inventory":[{"id":"ev1-critical-describe-pod","description":"Describe 异常 Pod rc-pending-insufficient-cpu 获取 FailedScheduling 原文确认 CPU 资源不足","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","purpose":"验证 FailedScheduling 事件中 '3 Insufficient cpu' 原文，确认资源不足是唯一调度失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev2-critical-events-unschedulable","description":"按命名空间范围获取调度相关事件，验证是否还有其他 FailedScheduling 或调度约束冲突","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector reason=FailedScheduling","purpose":"采集所有 FailedScheduling 事件确认是否存在除 CPU 外的其他调度障碍","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev3-important-node-resources","description":"通过 Prometheus 查询各节点 CPU allocatable 和已使用量，验证节点 CPU 资源是否已满","level":"important","tool":"execute_prometheus_instant_query","command":"sum(kube_node_status_allocatable_cpu_cores) by (node)","purpose":"验证集群各节点总可分配 CPU 核数，确认资源维度","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev4-important-node-cpu-usage","description":"通过 Prometheus 查询各节点 CPU 使用率，验证 CPU 是否已耗尽","level":"important","tool":"execute_prometheus_instant_query","command":"sum(node_cpu_seconds_total{mode!=\"idle\"}) by (instance) / sum(node_cpu_seconds_total) by (instance) * 100","purpose":"验证各节点 CPU 使用率是否接近 100%，确认 CPU 耗尽导致 Pod 无法调度","collected":false,"source":"planned","outcome":"unknown"},{"id":"ev5-important-pod-spec-config","description":"获取 Pod YAML 确认 request/limit 配置及调度约束（nodeSelector/affinity/tolerations）","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","purpose":"验证 Pod 的资源请求量（cpu request/limit）以及是否存在 nodeSelector/affinity/taints 等调度约束","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev6-important-pod-requested-resources","description":"通过 Prometheus 查询各节点已分配 Pod 资源总量，验证节点是否已过载分配","level":"important","tool":"execute_prometheus_instant_query","command":"sum(kube_pod_resource_request{resource=\"cpu\"}) by (node)","purpose":"查看各节点上 Pod 已经请求的 CPU 总量，验证 allocatable 是否已被占满","collected":false,"source":"planned","outcome":"unknown"},{"id":"ev7-optional-node-conditions","description":"确认三个节点的 Ready/Unschedulable 条件状态","level":"optional","tool":"run_bash_command","command":"kubectl get nodes -o wide","purpose":"验证 master/node1/node2 节点状态是否均为 Ready，排除节点不可用导致调度失败","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["ev4-important-node-cpu-usage(通过 Prometheus 查询各节点 CPU 使用率，验证 CPU 是否已耗尽): 已规划但工具执行失败或无匹配结果","ev6-important-pod-requested-resources(通过 Prometheus 查询各节点已分配 Pod 资源总量，验证节点是否已过载分配): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/6 项, 完整度: 80%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | ev1-critical-... | critical | ✅ | kubectl_describe | Describe 异常 Pod rc-pending-insufficient-cpu 获... | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` |
   | ev2-critical-... | critical | ✅ | kubectl_events | 按命名空间范围获取调度相关事件，验证是否还有其他 FailedScheduling 或调度... | `kubectl get events -n aiops-e2e --field-selector reason=FailedScheduling` |
   | ev3-important... | important | ✅ | execute_prometheus_instan... | 通过 Prometheus 查询各节点 CPU allocatable 和已使用量，验证节... | `sum(kube_node_status_allocatable_cpu_cores) by (node)` |
   | ev4-important... | important | ❌ | execute_prometheus_instan... | 通过 Prometheus 查询各节点 CPU 使用率，验证 CPU 是否已耗尽 | `sum(node_cpu_seconds_total{mode!="idle"}) by (instance) / sum(node_cpu_second...` |
   | ev5-important... | important | ✅ | kubectl_get_yaml | 获取 Pod YAML 确认 request/limit 配置及调度约束（nodeSele... | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml` |
   | ev6-important... | important | ❌ | execute_prometheus_instan... | 通过 Prometheus 查询各节点已分配 Pod 资源总量，验证节点是否已过载分配 | `sum(kube_pod_resource_request{resource="cpu"}) by (node)` |
   | ev7-optional-... | optional | ✅ | run_bash_command | 确认三个节点的 Ready/Unschedulable 条件状态 | `kubectl get nodes -o wide` |

   ⚠️ 未采集原因:
   - ev4-important-node-cpu-usage(通过 Prometheus 查询各节点 CPU 使用率，验证 CPU 是否已耗尽): 已规划但工具执行失败或无匹配结果
   - ev6-important-pod-requested-resources(通过 Prometheus 查询各节点已分配 Pod 资源总量，验证节点是否已过载分配): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (27.0s)
   📤 → 下游数据: root_cause=Pod rc-pending-insufficient-cpu（aiops-e2e 命名空间）处于 Pending 状态的根本原因是资源配置错误。Pod YAML 中 resources.requests.cpu 被设置为 100k（100,000 millicores = 100 核），而集群中 3 个节点（master/node1/node2）每节点 CPU Allocatable 仅有 12 核。调度器 Events 明确报告 "0/3 nodes are available: 3 Insufficient cpu"。各节点实际 CPU 使用率极低（master=21.7%, node1=4.6%, node2=14.4%），已分配 CPU Requests 也很低（master=38%, node1=7%, node2=14%），排除真正的资源耗尽。Pod 无 nodeSelector/affinity 等调度约束，唯一障碍是 CPU request 值写错。
   confidence=92%
   causal_chain={"root_cause": "Pod rc-pending-insufficient-cpu 的 resources.requests.cpu 被配置为 100k（100,000 millicores = 100 个 CPU 核），远超集群任何节点的 CPU 容量（每节点 12 核可分配），属于人为配置错误", "propagation": "调度器评估 Pod 的资源请求（100 核 CPU）→ 遍历所有 3 个 Ready 节点 → 每个节点可分配 CPU 仅 12 核，均无法满足 100 核请求 → 调度器判定 3 Insufficient cpu → 无节点可抢占（preemption: 0/3 No preemption victims found）", "direct_cause": "Pod 的 CPU request 值（100k）大于所有节点的 CPU allocatable 容量（12 核），导致调度器无法找到可用节点", "manifestation": "Pod rc-pending-insufficient-cpu 在 aiops-e2e 命名空间中持续处于 Pending 状态，Events 显示 FailedScheduling：0/3 nodes are available: 3 Insufficient cpu"}
   rca_analysis={"phenomenon": "集群 aiops-e2e 命名空间中 Pod rc-pending-insufficient-cpu 处于 Pending 状态，kubectl describe 显示 FailedScheduling 事件：0/3 nodes are available: 3 Insufficient cpu。集群 3 个节点（master/node1/node2）均为 Ready 状态。", "evidence_inventory": [{"id": "ev1", "source": "run_bash_command (kubectl describe node)", "content": "3 个节点（master/node1/node2）均为 Ready 状态，每节点 CPU Capacity=12，Allocatable=12", "reliability": "高"}, {"id": "ev2", "source": "kubectl_events", "content": "唯一调度事件：FailedScheduling：0/3 nodes are available: 3 Insufficient cpu，无其他调度约束冲突", "reliability": "高"}, {"id": "ev3", "source": "kubectl_get_yaml", "content": "Pod 无 nodeSelector/affinity 约束，QoS Burstable，仅有基础 tolerations", "reliability": "高"}, {"id": "ev4", "source": "run_bash_command (kubectl describe node 各节点)", "content": "master CPU Requests=4610m(38%), node1 CPU Requests=850m(7%), node2 CPU Requests=1775m(14%) — 均远未达到 100%", "reliability": "高"}, {"id": "ev5", "source": "execute_prometheus_instant_query (node_cpu_seconds_total)", "content": "node1 CPU使用率≈4.6%, node2≈14.4%, master≈21.7% — 使用率很低", "reliability": "高"}, {"id": "ev6", "source": "kubectl_describe", "content": "FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu，Pod QoS=Burstable, Node-Selectors=<none>", "reliability": "高"}, {"id": "ev7", "source": "LLM 证据分析结论", "content": "通过 kubectl get pod -o json 发现 Pod 的 CPU requests 设置为 100k（即 100,000 millicores=100 核），远超每节点 12 核容量", "reliability": "中"}], "evidence_analysis": [{"evidence_id": "ev1", "raw_data": "master/node1/node2 均 Ready，每节点 cpu=12, Allocatable=12", "interpretation": "集群所有节点健康且容量一致，每节点可分配 12 核 CPU"}, {"evidence_id": "ev2", "raw_data": "Warning FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu", "interpretation": "调度器判定所有 3 个节点的 CPU 均不足以运行该 Pod，但排除其他调度约束问题（taint/affinity/volume）"}, {"evidence_id": "ev3", "raw_data": "QoS Class: Burstable, Node-Selectors: <none>, Tolerations: 仅基础 tolerations", "interpretation": "Pod 没有特殊的节点选择约束，调度失败原因纯粹是 CPU 资源不足"}, {"evidence_id": "ev4", "raw_data": "master CPU Requests=4610m/12000m(38%), node1=850m/12000m(7%), node2=1775m/12000m(14%)", "interpretation": "各节点已分配 CPU 请求远未达到饱和（最高 38%），说明不是集群整体资源耗尽，而是单个 Pod 请求量异常大"}, {"evidence_id": "ev5", "raw_data": "node1=4.56%, node2=14.44%, master=21.71%", "interpretation": "实际 CPU 使用率很低，进一步证明不是真正的资源耗尽问题"}, {"evidence_id": "ev6", "raw_data": "Warning FailedScheduling 68s default-scheduler 0/3 nodes are available: 3 Insufficient cpu", "interpretation": "调度器确认所有 3 个节点均 CPU 不足，但这不是由于其他 Pod 占满 CPU，而是 Pod 自身请求过大"}, {"evidence_id": "ev7", "raw_data": "Pod 的 CPU requests 被设置为 100k（100,000 millicores=100 核）", "interpretation": "关键根因：Pod 配置错误，CPU requests 写成了 100k（100 核），而每个节点只有 12 核可分配。正常值应为 100m（0.1 核）"}], "causal_chain": {"root_cause": "Pod rc-pending-insufficient-cpu 的 resources.requests.cpu 被配置为 100k（100,000 millicores = 100 个 CPU 核），远超集群任何节点的 CPU 容量（每节点 12 核可分配），属于人为配置错误", "propagation": "调度器评估 Pod 的资源请求（100 核 CPU）→ 遍历所有 3 个 Ready 节点 → 每个节点可分配 CPU 仅 12 核，均无法满足 100 核请求 → 调度器判定 3 Insufficient cpu → 无节点可抢占（preemption: 0/3 No preemption victims found）", "direct_cause": "Pod 的 CPU request 值（100k）大于所有节点的 CPU allocatable 容量（12 核），导致调度器无法找到可用节点", "manifestation": "Pod rc-pending-insufficient-cpu 在 aiops-e2e 命名空间中持续处于 Pending 状态，Events 显示 FailedScheduling：0/3 nodes are available: 3 Insufficient cpu"}, "root_cause": "Pod rc-pending-insufficient-cpu（aiops-e2e 命名空间）处于 Pending 状态的根本原因是资源配置错误。Pod YAML 中 resources.requests.cpu 被设置为 100k（100,000 millicores = 100 核），而集群中 3 个节点（master/node1/node2）每节点 CPU Allocatable 仅有 12 核。调度器 Events 明确报告 \"0/3 nodes are available: 3 Insufficient cpu\"。各节点实际 CPU 使用率极低（master=21.7%, node1=4.6%, node2=14.4%），已分配 CPU Requests 也很低（master=38%, node1=7%, node2=14%），排除真正的资源耗尽。Pod 无 nodeSelector/affinity 等调度约束，唯一障碍是 CPU request 值写错。", "root_cause_summary": "Pod rc-pending-insufficient-cpu（aiops-e2e 命名空间）处于 Pending 状态的根本原因是资源配置错误。Pod YAML 中 resources.requests.cpu 被设置为 100k（100,000 millicores = 100 核），而集群中 3 个节点（master/node1/node2）每节点 CPU Allocatable 仅有 12 核。调度器 Events 明确报告 \"0/3 nodes are available: 3 Insufficient cpu\"。各节点实际 CPU 使用率极低（master=21.7%, node1=4.6%, node2=14.4%），已分配 CPU Requests 也很低（master=38%, node1=7%, node2=14%），排除真正的资源耗尽。Pod 无 nodeSelector/affinity 等调度约束，唯一障碍是 CPU request 值写错。", "confidence": 0.92, "confidence_reason": "有直接证据链：FailedScheduling 事件明确指示 CPU 不足（ev1/ev2/ev6），节点容量数据证实每节点仅 12 核（ev1），节点实际使用率和已分配请求均很低排除真正资源耗尽（ev4/ev5），Pod 无其他约束排除 taint/affinity 问题（ev3）。LLM 分析指出 CPU requests=100k 为 100 核（ev7），虽未提供原始 json 原始输出全文作为直接引用，但所有旁证高度一致指向配置错误。置信度 0.92。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "集群节点 CPU 被其他 Pod 占满导致资源耗尽", "probability": "low", "reason": "各节点 CPU 实际使用率仅 4.6%-21.7%，已分配 CPU Requests 仅 7%-38%，远未饱和。排除此场景。"}, {"cause": "节点 taint/affinity/nodeSelector 不匹配导致无法调度", "probability": "low", "reason": "Pod YAML 显示 Node-Selectors=<none>，仅基础 tolerations，无特殊调度约束。排除此场景。"}, {"cause": "PVC 未绑定或卷依赖未满足", "probability": "low", "reason": "Pod 仅挂载 kube-api-access 默认卷，无 PVC 依赖；FailedScheduling 事件未提及 volume 问题。排除此场景。"}], "limitations": "关键证据 ev7（Pod CPU requests=100k 的原始 JSON）未提供完整原始工具输出原文，该结论来自 LLM 分析而非原始 kubectl get pod -o json 全文。建议人工复核 Pod YAML 中 resources.requests.cpu 字段的原始值以 100% 确认。", "llm_raw_analysis": "## 证据清点\n共采集 7 条关键证据（ev1-ev7），2 条缺失（ev4/ev6 原计划 Prometheus 查询但已被其他证据替代）。\n\n### 关键证据分析\n1. **节点状态（ev1）**: 3 节点均 Ready，每节点 CPU=12，Allocatable=12 — 集群健康\n2. **调度事件（ev2/ev6）**: FailedScheduling 唯一原因 \"3 Insufficient cpu\" — 无其他约束冲突\n3. **Pod 配置（ev3）**: 无 nodeSelector/affinity，仅有基础 tolerations — 排除调度约束问题\n4. **节点已分配资源（ev4）**: master=38%, node1=7%, node2=14% — 远未饱和\n5. **CPU 使用率（ev5）**: master=21.7%, node1=4.6%, node2=14.4% — 很低\n6. **LLM Pod JSON 分析（ev7）**: CPU requests=100k=100核 — 远超节点12核容量\n\n### 因果链\n根因（配置错误：C\n... 截断，原始 785 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-insufficient-cpu（aiops-e2e 命名空间）处于 Pending 状态的根本原因是资源配置错误。Pod YAML 中 resources.requests.cpu 被设置为 100k（100,000 millicores = 100 核），而集群中 ...
   置信度: 92%
   🔗 因果链:
     根本原因: Pod rc-pending-insufficient-cpu 的 resources.requests.cpu 被配置为 100k（100,000 millicores = 100 个 CPU 核），远超集群任何节点的 CPU 容量（每节点 12 核可分配），属于人为配置错误
     传导机制: 调度器评估 Pod 的资源请求（100 核 CPU）→ 遍历所有 3 个 Ready 节点 → 每个节点可分配 CPU 仅 12 核，均无法满足 100 核请求 → 调度器判定 3 Insufficient cpu → 无节点可抢占（preemption: 0/3 No preemption victims found）
     最终表现: Pod rc-pending-insufficient-cpu 在 aiops-e2e 命名空间中持续处于 Pending 状态，Events 显示 FailedScheduling：0/3 nodes are available: 3 Insufficient cpu


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (33.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6778 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 14.7s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，请查收基于您提供的三阶段分析结果生成的集群诊断报告。

---
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending |
| **兼容归因层** | L1 - 调度层 |
| **问题分类** | PendingUnschedulable（资源不足导致无法调度） |
| **置信度** | 高 (92%) |
| **证据完整度** | 4/6 (67%) |
---
## 🧭 当前集群状态总结

您的集群整体运行健康，共有 65 个 Pod，其中 **59 个（91%）运行正常**。当前发现 **1 个问题 Pod**，具体如下：

| 状态 | 命名空间 | Pod 名称 | 问题 |
|------|----------|----------|------|
| ✅ 正常 | 所有 | 59个 Running Pods | 运行无误 |
| ❌ 异常 | `aiops-e2e` | `rc-pending-insufficient-cpu` | 调度失败，持续处于 Pending 状态 |

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-pending-insufficient-cpu` |
| Namespace | `aiops-e2e` |
| 异常状态 | Pending |
| 关键错误事件 | `FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu` |

**集群节点状态**：集群共有 3 个节点（`master`、`node1`、`node2`），均为 `Ready` 状态，不存在节点不可用或 taint 引起的调度问题。
```
NAME     STATUS   ROLES           AGE    VERSION
master   Ready    control-plane   238d   v1.26.8
node1    Ready    <none>          238d   v1.26.8
node2    Ready    <none>          238d   v1.26.8
```
---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` | `status: Pending`<br>`Warning FailedScheduling 68s default-scheduler 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..` | Pod 因 CPU 资源不足无法被调度到任何节点 |
| 2 | 调度事件 | `kubectl events -n aiops-e2e` | `68s Warning FailedScheduling Pod/rc-pending-insufficient-cpu 0/3 nodes are available: 3 Insufficient cpu.` | 事件进一步确认调度器因 CPU 不足而失败 |
| 3 | Pod 资源配置 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o json` | `"requests": {"cpu": "100k", "memory": "64Mi"}` | Pod 请求 **100 核 CPU（100,000 millicores）** |
| 4 | 节点 CPU 容量 | `kubectl describe node master/node1/node2` | `Capacity.cpu: 12`<br>`Allocatable cpu: 12` | 集群 3 个节点，每个节点最大可分配 CPU 容量为 **12 核** |
| 5 | Pod 调度约束 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml` | `Node-Selectors: <none>` <br> `Tolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s` | Pod 没有 `nodeSelector` 或 `affinity` 等调度约束，排除了约束不匹配的原因 |
| 6 | 节点状态 | `kubectl get nodes`（通过 `run_bash_command` 确认） | `master Ready, node1 Ready, node2 Ready` | 所有节点状态正常，排除节点不可用导致的调度失败 |

### 证据关联分析
- **证据 #1 + #2 + #3 + #4 印证**：
  - Pod 请求 100 核 CPU（证据 #3）
  - 集群中最强大的节点也仅有 12 核可分配容量（证据 #4）
  - 调度器发现没有任何节点可以满足请求，因此报告 “3 Insufficient cpu”（证据 #1, #2）
  - **结论**：根本原因是 Pod 的 CPU request 值被误设为 100k，远超集群容量。
- **证据 #5 + #6 辅助排除**：排除了调度约束（nodeSelector/taint）和节点状态导致的调度失败，锁定了资源不足是唯一原因。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| Prometheus 节点 CPU 使用率查询 | important | 已规划但工具执行失败，无法展现其他 Pod 的资源使用情况，但对根因确认影响有限 |
| Prometheus 节点 CPU 请求量查询 | important | 同上，对根因确认影响有限 |
---
## 🎯 根因分析
### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                     │
│ 人为配置错误：Pod `rc-pending-insufficient-cpu` 的 resources.requests.cpu   │
│ 被设置为 100k（100,000 millicores = 100 个 CPU 核）                         │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                     │
│ 调度器评估 Pod 的资源请求（100 核 CPU）→ 遍历所有 3 个 Ready 节点            │
│ → 每个节点可分配 CPU 仅 12 核，均无法满足 100 核请求                         │
│ → 调度器判定 "3 Insufficient cpu" → 无节点可抢占                            │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                     │
│ Pod 的 CPU request 值（100k）大于所有节点的 CPU allocatable 容量（12 核）    │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                 │
│ Pod `rc-pending-insufficient-cpu` 在 `aiops-e2e` 命名空间中持续处于 Pending  │
│ 状态，Events 显示 FailedScheduling                                        │
└──────────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #1 (FailedScheduling 事件)、证据 #3 (`requests: {cpu: “100k“}`) 和证据 #4 (节点 allocatable cpu: 12)，问题的根本原因是 **Pod 的 CPU request 配置错误，被设置为 100 核，远超集群中任何节点的 CPU 容量（12 核）**，导致调度器无法找到合适的节点。这是一个典型的资源配置失误。

**置信度**：高 (92%)
- ✅ 调度器事件明确报告 “3 Insufficient cpu”
- ✅ Pod YAML 直接显示 CPU request 值为 `100k`
- ✅ 节点容量数据完全匹配，根因链完整
- ⚠️ 未完整获取 `kubectl get pod -o json` 全文，但关键字段已获取并验证

**已排除可能原因**：
- 节点不可用 → 证据 #6 显示所有节点 Ready，**已排除**
- finalizer 未清理 → 工具输出显示 `finalizers: <none>`，**已排除**
- 调度约束不匹配 (taint/nodeSelector) → 证据 #5 显示 Pod 无此类约束，**已排除**
- 集群真正资源不足 → 证据 #4 表明节点有足够空闲资源，只是无法满足 100 核的异常请求，**已排除**
---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [强制] 修正 CPU Request 值为正确数值**
这是解决该问题的唯一途径。将 CPU request 从 `100k` 改为一个合理值，例如 `100m`（0.1 核）。
```bash
# 方法一：直接编辑 YAML（推荐，确保可见所有字段）
kubectl edit pod rc-pending-insufficient-cpu -n aiops-e2e

# 方法二：如果 Pod 由 Deployment 管理，则编辑 Deployment
kubectl edit deployment <deployment-name> -n aiops-e2e
```
在编辑器中找到 `resources.requests.cpu` 字段，将 `100k` 修改为 `100m` 或其他你希望的数值。保存后 Pod 会自动重建。

**2. [强制] 删除旧 Pod 以重新调度**
修正配置后，需要删除旧的、处于 Pending 状态的 Pod，让调度器重新调度新 Pod。
```bash
kubectl delete pod rc-pending-insufficient-cpu -n aiops-e2e
```
*依据*：删除旧 Pod 后，Kubernetes 会根据更新后的配置创建新 Pod，调度器此时才能正确评估并分配资源。
### 后续优化
1. **资源请求规范化**：确保所有 Pod 的 `resources.requests` 和 `limits` 是基于应用实际需求设置的，避免出现过小或过大的异常值。例如，编写 Deployment/StatefulSet 时使用 YAML 模板审查机制。
2. **准入控制**：建议在集群中部署 **Kubernete 准入控制器（如 OPA/Gatekeeper 或 Kyverno）**，设置规则禁止 `requests.cpu` 超过节点容量（如 12 核）的 Pod 创建，从源头上拦截此类配置错误。
---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 被删除 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e` | 如已删除，显示 `No resources found`；若由 Deployment 重建，新 Pod 状态应为 `Running` |
| 2. 检查新 Pod 状态 | `kubectl get pod -n aiops-e2e` | 存在一个新 Pod，状态为 `Running`，`READY` 为 `1/1` |
| 3. 验证新 Pod 资源 | `kubectl get pod <new-pod-name> -n aiops-e2e -o yaml | grep -A 3 requests` | 输出中包含 `cpu: 100m` 或你设定的正确值 |
| 4. 确认集群整体健康 | `kubectl get pods --all-namespaces | grep -v Running | grep -v Completed` | 应不显示任何 Pending 或非正常状态的 Pod |
---
## ⚠️ 注意事项
- **谨慎操作**：如果您是手动创建了该 Pod，编辑并删除后 Pod 将不会自动重建。请检查是否有 `Deployment` 或 `StatefulSet` 管理该 Pod。
- **错误值来源**：`100k` 很可能是单位写错导致的，例如将 `100m` 写成了 `100k`，或者错误地使用了 `requests.cpu: 100`（即 100 核）。请务必在修复前确认应用的 CPU 真实需求。
- **Prometheus 数据可用**：集群中 Prometheus 运行正常，但相关查询未返回预期数据。如果需要更深入的资源分析，建议检查 Prometheus 的配置和数据采集链路。

---

## 📊 性能统计

├─ 总耗时: 2.2m
├─ 问题定位: 25.1s (19%) ✅
├─ 证据链采集: 49.1s (36%) ✅
├─ 根因分析: 27.0s (20%) ✅
├─ 汇总总结: 33.5s (25%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 19 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 19 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
