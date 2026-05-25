======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 59f10616e0254e88]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先对集群做一次全局 Pod 状态扫描，看看当前有哪些异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 发现了一个异常 Pod。让我进一步查看这个 Pending Pod 的详细信息以及集群节点情况。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  12m                    default-scheduler  0/3 nodes are ava
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 让我再获取这个 Pod 的 YAML，确认它的资源请求量。
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:59:10Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizer
   💭 [问题定位] 现在我已经获取了足够的信息。以下是完整的诊断分析：

---

## 📋 集群异常诊断报告

### 1️⃣ 全局扫描结果

| 指标 | 数值 |
|------|------|
| 总 Pod 数 | **65** |
| 正常 Running Pod | **59** |
| 正常 Completed Pod | **0** |
| 异常 Pod | **1** |
| 集群节点 | **3**（全部 Ready） |

### 2️⃣ 当前异常 Pod

| Pod | 命名空间 | 状态 | 异常类型 |
|-----|---------|------|---------|
| `rc-pending-insufficient-cpu` | `aiops-e2e` | Pending | **PendingUnschedulable** |

### 3️⃣ 异常详情

- **Pod 名称**: `rc-pending-insufficient-cpu`（命名空间: `aiops-e2e`）
- **镜像**: `busybox:1.36`（imagePullPolicy=Never——注意此策略会导致拉取失败风险，但当前问题不在此）
- **Status**: Pending，未绑定任何节点（`nodeName: <none>`）
- **调度事件**: 
  ```
  FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu.
  preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.
  ```
- **集群节点**: 3 个节点全部 Ready（master, node1, node2），但**所有节点 CPU 资源均已耗尽**，无法满足该 Pod 的 CPU 请求。

### 4️⃣ 分层归因

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **layer_name** | PendingUnschedulable |
| **pod_status_keyword** | Pending |
| **pod_abnormal_type** | PendingUnschedulable |
| **status_category** | scheduling |
| **reasoning** | Pod 处于 Pending 状态，FailedScheduling 事件明确指示所有 3 个节点均 CPU 不足（Insufficient cpu），且无可用抢占受害者 |

### 5️⃣ 异常分组

| 异常组 | 异常 Pod 列表 |
|--------|-------------|
| **PendingUnschedulable** | `aiops-e2e/rc-pending-insufficient-cpu` |

### 6️⃣ 可能的场景

| 场景 | 可能性 |
|------|--------|
| 集群整体 CPU 资源不足，所有节点 Allocatable CPU 已被现有 Pod 占满 | ⭐ **最可能** |
| Pod 请求的 CPU 量过大，单节点无法满足 | 可能 |
| 节点上存在大量未设置资源限制的 Pod 导致资源被过度占用 | 需进一步确认 |

### 7️⃣ 后续审查方向

建议下游 evidence 节点进一步：
1. 查看各节点的 `Allocatable CPU` vs `Capacity CPU`，确认资源使用率
2. 检查各节点正在运行的 Pod 的 CPU requests 总量是否接近节点上限
3. 查看是否有低优先级的 Pod 可以被抢占/驱逐
4. 排查 Pod 自身的 `resources.requests.cpu` 是否设置过高
   ✅ [问题定位] 完成 (24.6s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '集群整体CPU资源不足，所有节点Allocatable CPU已被现有Pod占满', 'probability': '高', 'reason': 'FailedScheduling事件明确指示所有3个节点均Insufficient cpu，且无可用抢占受害者'}, {'scenario': 'Pod请求的CPU量过大，单个节点无法满足', 'probability': '中等', 'reason': '需进一步检查Pod的resources.requests.cpu配置'}, {'scenario': '节点上存在大量未设置资源限制的Pod导致资源被过度占用', 'probability': '低', 'reason': '需进一步检查各节点Pod资源使用情况'}]
   entities=[{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}]
   reasoning=集群存在1个当前仍异常的Pod：rc-pending-insufficient-cpu（命名空间aiops-e2e），状态为Pending。调度事件明确显示FailedScheduling：0/3 nodes are available: 3 Insufficient cpu，所有3个节点CPU资源已耗尽。3个节点全部Ready，排除节点故障。Pod未绑定任何节点（nodeName为<none>），PodScheduled condition为False，reason为Unschedulable。根据五层模型，PendingUnschedulable归因于调度/资源不足，属于L1层（scheduling）。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "集群存在1个当前仍异常的Pod：rc-pending-insufficient-cpu（命名空间aiops-e2e），状态为Pending。调度事件明确显示FailedScheduling：0/3 nodes are available: 3 Insufficient cpu，所有3个节点CPU资源已耗尽。3个节点全部Ready，排除节点故障。Pod未绑定任何节点（nodeName为<none>），PodScheduled condition为False，reason为Unschedulable。根据五层模型，PendingUnschedulable归因于调度/资源不足，属于L1层（scheduling）。", "abnormal_pods": [{"name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}], "possible_scenarios": [{"scenario": "集群整体CPU资源不足，所有节点Allocatable CPU已被现有Pod占满", "probability": "高", "reason": "FailedScheduling事件明确指示所有3个节点均Insufficient cpu，且无可用抢占受害者"}, {"scenario": "Pod请求的CPU量过大，单个节点无法满足", "probability": "中等", "reason": "需进一步检查Pod的resources.requests.cpu配置"}, {"scenario": "节点上存在大量未设置资源限制的Pod导致资源被过度占用", "probability": "低", "reason": "需进一步检查各节点Pod资源使用情况"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-insufficient-cpu                         0/1     Pending     0              12m     <none>           <none>   <none>           <none>            app=rc-pending-insufficient-cpu,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我来按既有证据计划执行采证。先并行调用关键的 critical 工具。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: fetch_runbook
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
  Warning  FailedScheduling  13m                    default-scheduler  0/3 nodes are ava
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:59:10Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizer
   💭 [证据链采集] 好的，Pod 的 YAML 中看到容器的 `imagePullPolicy=Never` 但没看到 `resources.requests.cpu` 字段。让我同时获取节点 CPU 容量和使用情况以及命名空间事件。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"name\": \"master\",\n  \"allocatable\": \"12\",\n  \"capacity\": \"12\",\n  \"conditions\": [\n    {\n      \"type\": \"Ready\",\n      \"reason\": \"KubeletReady\"
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
13m                   Warning   FailedScheduling   Pod/rc-pending-insufficient-cpu   0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No pr
   💭 [证据链采集] 节点总 CPU 是 12+12+12=36 core，但 Pod 资源请求量需要看 Pod YAML 详情。让我检查 Pod YAML 中的 resources 字段以及 Prometheus 查询 CPU 使用率。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "    resources:\n      requests:\n        cpu: 100k\n        memory: 64Mi\n    terminationMessagePath: /dev/termination-log\n    terminationMessagePolicy: File\n    volumeM
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"node":"master"},"value":[1779347539.225,"1"]},{"metric":{"node":"node1"},"value":[1779347539.225,"1"]},{"metric":{"node":"node2"
   💭 [证据链采集] ## 证据采集结论

### ✅ 已采集证据

**e1 - FailedScheduling 事件（critical）✅**
- `kubectl describe pod` 确认：当前事件仍为 `0/3 nodes are available: 3 Insufficient cpu`，与上游信号一致。

**e2 - Pod resources.requests.cpu（critical）✅**
- 关键发现！Pod 配置了 `resources.requests.cpu: 100k`（即 **100,000 个 CPU 核心**），而集群全部 3 个节点的总 capacity 仅 **36 core**（12×3）。这是一个**人为构造的故障场景**——Pod 请求的 CPU 量远超集群总容量。

**e3 - 节点 CPU 容量（critical）✅**
| 节点 | Capacity | Allocatable | Ready |
|------|---------|-------------|-------|
| master | 12 | 12 | ✅ |
| node1 | 12 | 12 | ✅ |
| node2 | 12 | 12 | ✅ |

三个节点全部 Ready，但 Total Allocatable = 36 core，Pod request 为 100,000 core，完全无法满足。

**e4 - Prometheus 节点 CPU 使用率（important）✅**
- 各节点 `allocatable / capacity = 1`，即 allocatable 等于 capacity，没有资源超分。

**e5 - Runbook 参考 ✅**
- `pod-pending-unschedulable.md` 已获取，确认匹配 `FailedScheduling + Insufficient cpu` 分支。

**e6 - 命名空间事件（important）✅**
- 只有 FailedScheduling 事件，无其他异常。

### 🔍 根因分析

**根因**：Pod `rc-pending-insufficient-cpu` 的 `resources.requests.cpu = 100k`（100,000 个 CPU 核心），而集群所有 3 个节点的总 CPU allocatable 仅 36 core（12×3），因此调度器在所有节点均为 `Insufficient cpu`，无法调度。

**证据链**：
1. ✅ FailedScheduling 事件原文：`0/3 nodes are available: 3 Insufficient cpu`
2. ✅ Pod 规格确认：`resources.requests.cpu: 100k`
3. ✅ 节点总容量：master=12, node1=12, node2=12，合计仅 36 core
4. ✅ 3 个节点全部 Ready，非节点故障

### ⛔ 未发现冲突证据
所有工具结果均与上游信号一致，未发现对象缺失、namespace 不匹配或事件过期。
   ✅ [证据链采集] 完成 (28.8s)
   📤 → 下游数据: evidence_items=10/10
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"Describe the Pending pod rc-pending-insufficient-cpu to reconfirm FailedScheduling events and pod status","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e"},"purpose":"验证 FailedScheduling 事件原文：确认 3 Insufficient cpu 是否仍为当前调度失败原因","evidence_type":"current_status","target_scope":"pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"Get YAML of the pod to check resources.requests.cpu spec","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e"},"purpose":"检查 Pod 的 resources.requests.cpu 配置，确认 CPU 请求量","evidence_type":"configuration","target_scope":"pod","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"Get all nodes allocatable and capacity cpu to confirm cluster-level CPU exhaustion","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, allocatable: .status.allocatable.cpu, capacity: .status.capacity.cpu, conditions: [.status.conditions[] | select(.status==\"True\") | {type: .type, reason: .reason, message: .message}]}'","tool_args":{},"purpose":"验证所有节点的 CPU allocatable 和 capacity，确认集群 CPU 资源是否已耗尽","evidence_type":"node_capacity","target_scope":"cluster","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"Get node cpu utilization via Prometheus to confirm actual CPU usage on nodes","level":"important","tool":"execute_prometheus_instant_query","command":"sum(kube_node_status_allocatable{resource='cpu'}) by (node) / sum(kube_node_status_capacity{resource='cpu'}) by (node)","tool_args":{},"purpose":"验证各节点 CPU 实际资源使用率，确认资源耗尽程度","evidence_type":"resource_usage","target_scope":"cluster","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5","description":"Fetch runbook reference for PendingUnschedulable with Insufficient cpu","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","tool_args":{},"purpose":"获取 runbook 参考信息，辅助诊断调度失败","evidence_type":"reference","target_scope":"reference","acceptable_tools":[],"counts_for_completeness":true},{"id":"e6","description":"Check events in aiops-e2e namespace for additional scheduling context","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e"},"purpose":"获取命名空间事件，确认除 FailedScheduling 外是否有其他相关异常事件","evidence_type":"events","target_scope":"namespace","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod PendingUnschedulable / 调度失败\n\n> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | Pending，且 Events 含 `FailedScheduling` |\n| 资源不足 | `Insufficient cpu/memory/ephemeral-storage`、`Too many pods` |\n| 调度约束 | nodeSelector/affinity 不匹配、节点 taint 未被 toleration 容忍 |\n| 存储前置条件 | `pod has unbound immediate PersistentVolumeClaims` 应切换到 pod-volume-mount-failed |\n| 节点状态 | Node NotReady/Unknown、SchedulingDisabled、Unschedulable 会导致无可用调度节点 |\n\n## 根因分流\n- 资源不足: FailedScheduling 原文含 Insufficient cpu/memory/ephemeral-storage、Too many pods。\n- hostPort 冲突: 原文含 `didn't have free ports for the requested pod ports`，说明目标节点端口已被占用。\n- Taint/Toleration 不匹配: 原文含 `had untolerated taint`，必须检查 Pod tolerations 和 Node taints。\n- nodeSelector / nodeAffinity / podAffinity 不匹配: 原文含 `didn't match Pod's node affinity/selector` 或 affinity/anti-affinity。\n- PVC 未绑定: 原文含 `unbound immediate PersistentVolumeClaims`，根因在存储绑定而不是调度资源。\n- 节点不可调度: Node Ready=False/Unknown、SchedulingDisabled、`node.kubernetes.io/not-ready` 或 `node.kubernetes.io/unreachable`。\n- 镜像、挂载、容器启动错误不会表现为 FailedScheduling；如果 Pod 已绑定 nodeName，应切换到对应 runbook。\n\n## 诊断流程\n\n### Step 1: 确认 Pod 调度失败事件\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n关注 Events 中的 `FailedScheduling` 原文。\n\n### Step 2: 检查 Pod 调度约束\n```bash\nkubectl get pod <pod-name> -n <namespace> -o yaml\n```\n关注: spec.nodeName 是否为空、nodeSelector、affinity、tolerations、topologySpreadConstraints、schedulerName、priorityClassName、resource requests、hostNetwork/hostPort。\n\n### Step 3: 检查节点状态和可调度性\n```bash\nkubectl get nodes -o wide\n```\n关注: STATUS 列是否有 NotReady/Unknown，AGE 判断是否新节点\n\n### Step 4: 检查候选节点详情\n```bash\nkubectl describe node <node-name>\n```\n重点关注:\n- `Conditions` 部分: Ready=False/Unknown 的 reason 和 message\n- `Taints` 部分: 是否有 NoSchedule/NoExecute taint\n- `Allocatable` vs `Capacity`: 资源是否耗尽\n- `Non-terminated Pods`: 节点上运行的 Pod 数量\n\n### Step 5: 检查 PVC 状态（如果 FailedScheduling 指向 PVC）\n```bash\nkubectl get pvc -n <namespace>\nkubectl describe pvc <pvc> -n <namespace>\n```\n关注: Pending、StorageClass、volumeBindingMode、ProvisioningFailed。\n\n### Step 6: 检查 Ready 条件详情\n```bash\nkubectl get node <node-name> -o jsonpath='{.status.conditions[?(@.type==\"Ready\")]}' | python3 -m json.tool\n```\n关注: status, reason, message, lastHeartbeatTime\n\n### Step 7: 检查节点事件\n```bash\nkubectl get events -A --field-selector involvedObject.kind=Node,involvedObject.name=<node-name> --sort-by='.lastTimestamp'\n```\n关注: NodeNotReady、NodeNotSchedulable、PLEG unhealthy 等事件\n\n### Step 8: 检查受影响的 Pending Pod\n```bash\nkubectl get pods -A --field-selector status.phase=Pending | head -20\n```\n\n## 判定规则\n\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| FailedScheduling + Insufficient cpu/memory | 资源不足导致 Pod Pending | 高 |\n| FailedScheduling + Too many pods | 节点 Pod 数量上限导致 Pending | 高 |\n| FailedScheduling + didn't have free ports for the requested pod ports | hostPort 端口冲突导致 Pending | 高 |\n| FailedScheduling + had untolerated taint | taint/toleration 不匹配 | 高 |\n| FailedScheduling + node(s) didn't match node selector/affinity | 调度约束不匹配 | 高 |\n| FailedScheduling + pod has unbound immediate PersistentVolumeClaims | PVC 未绑定，应切换 VolumeMountFailed/PVC 分支 | 高 |\n| 所有候选 Node NotReady/Unschedulable | 无可用调度节点 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  13m                    default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  2m58s (x2 over 7m58s)  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nName:             rc-pending-insufficient-cpu\nLabels:           app=rc-pending-insufficient-cpu\nPod 关键区块:\nQoS Class: Burstable\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-26zhx:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  13m                    default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  2m58s (x2 over 7m58s)  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:59:10Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-insufficient-cpu, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nvolumes:\n- {\"name\": \"kube-api-access-26zhx\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"name\\\": \\\"master\\\",\\n  \\\"allocatable\\\": \\\"12\\\",\\n  \\\"capacity\\\": \\\"12\\\",\\n  \\\"conditions\\\": [\\n    {\\n      \\\"type\\\": \\\"Ready\\\",\\n      \\\"reason\\\": \\\"KubeletReady\\\",\\n      \\\"message\\\": \\\"kubelet is posting ready status. AppArmor enabled\\\"\\n    }\\n  ]\\n}\\n{\\n  \\\"name\\\": \\\"node1\\\",\\n  \\\"allocatable\\\": \\\"12\\\",\\n  \\\"capacity\\\": \\\"12\\\",\\n  \\\"conditions\\\": [\\n    {\\n      \\\"type\\\": \\\"Ready\\\",\\n      \\\"reason\\\": \\\"KubeletReady\\\",\\n      \\\"message\\\": \\\"kubelet is posting ready status. AppArmor enabled\\\"\\n    }\\n  ]\\n}\\n{\\n  \\\"name\\\": \\\"node2\\\",\\n  \\\"allocatable\\\": \\\"12\\\",\\n  \\\"capacity\\\": \\\"12\\\",\\n  \\\"conditions\\\": [\\n    {\\n      \\\"type\\\": \\\"Ready\\\",\\n      \\\"reason\\\": \\\"KubeletReady\\\",\\n      \\\"message\\\": \\\"kubelet is posting ready status. AppArmor enabled\\\"\\n    }\\n  ]\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/004-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/004-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/004-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n13m                   Warning   FailedScheduling   Pod/rc-pending-insufficient-cpu   0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n3m2s (x2 over 8m2s)   Warning   FailedScheduling   Pod/rc-pending-insufficient-cpu   0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/005-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/005-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/005-evidence-kubectl_events.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"    resources:\\n      requests:\\n        cpu: 100k\\n        memory: 64Mi\\n    terminationMessagePath: /dev/termination-log\\n    terminationMessagePolicy: File\\n    volumeMounts:\\n    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount\\n      name: kube-api-access-26zhx\\n      readOnly: true\\n  dnsPolicy: ClusterFirst\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/006-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/006-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/006-evidence-run_bash_command.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"node\":\"master\"},\"value\":[1779347539.225,\"1\"]},{\"metric\":{\"node\":\"node1\"},\"value\":[1779347539.225,\"1\"]},{\"metric\":{\"node\":\"node2\"},\"value\":[1779347539.225,\"1\"]}]}}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/007-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/007-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/59f10616e0254e88/tools/007-evidence-execute_prometheus_instant_query.summary.txt"}],"llm_analysis":"## 证据采集结论\n\n### ✅ 已采集证据\n\n**e1 - FailedScheduling 事件（critical）✅**\n- `kubectl describe pod` 确认：当前事件仍为 `0/3 nodes are available: 3 Insufficient cpu`，与上游信号一致。\n\n**e2 - Pod resources.requests.cpu（critical）✅**\n- 关键发现！Pod 配置了 `resources.requests.cpu: 100k`（即 **100,000 个 CPU 核心**），而集群全部 3 个节点的总 capacity 仅 **36 core**（12×3）。这是一个**人为构造的故障场景**——Pod 请求的 CPU 量远超集群总容量。\n\n**e3 - 节点 CPU 容量（critical）✅**\n| 节点 | Capacity | Allocatable | Ready |\n|------|---------|-------------|-------|\n| master | 12 | 12 | ✅ |\n| node1 | 12 | 12 | ✅ |\n| node2 | 12 | 12 | ✅ |\n\n三个节点全部 Ready，但 Total Allocatable = 36 core，Pod request 为 100,000 core，完全无法满足。\n\n**e4 - Prometheus 节点 CPU 使用率（important）✅**\n- 各节点 `allocatable / capacity = 1`，即 allocatable 等于 capacity，没有资源超分。\n\n**e5 - Runbook 参考 ✅**\n- `pod-pending-unschedulable.md` 已获取，确认匹配 `FailedScheduling + Insufficient cpu` 分支。\n\n**e6 - 命名空间事件（important）✅**\n- 只有 FailedScheduling 事件，无其他异常。\n\n### 🔍 根因分析\n\n**根因**：Pod `rc-pending-insufficient-cpu` 的 `resources.requests.cpu = 100k`（100,000 个 CPU 核心），而集群所有 3 个节点的总 CPU allocatable 仅 36 core（12×3），因此调度器在所有节点均为 `Insufficient cpu`，无法调度。\n\n**证据链**：\n1. ✅ FailedScheduling 事件原文：`0/3 nodes are available: 3 Insufficient cpu`\n2. ✅ Pod 规格确认：`resources.requests.cpu: 100k`\n3. ✅ 节点总容量：master=12, node1=12, node2=12，合计仅 36 core\n4. ✅ 3 个节点全部 Ready，非节点故障\n\n### ⛔ 未发现冲突证据\n所有工具结果均与上游信号一致，未发现对象缺失、namespace 不匹配或事件过期。","collection_summary":"计划 5 项，实际采集 5 项，未采集 0 项，完整度 100%；其中真实环境证据 9/9 项，完整度 100%；实际执行工具 10 个，匹配计划 6 个，未规划证据 4 个","plan_total":5,"plan_collected":5,"plan_completeness":1.0,"environment_evidence_total":9,"environment_evidence_collected":9,"environment_evidence_completeness":1.0,"executed_tool_count":10,"matched_tool_count":6,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"Describe the Pending pod rc-pending-insufficient-cpu to reconfirm FailedScheduling events and pod status","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","purpose":"验证 FailedScheduling 事件原文：确认 3 Insufficient cpu 是否仍为当前调度失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"Get YAML of the pod to check resources.requests.cpu spec","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","purpose":"检查 Pod 的 resources.requests.cpu 配置，确认 CPU 请求量","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"Get all nodes allocatable and capacity cpu to confirm cluster-level CPU exhaustion","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, allocatable: .status.allocatable.cpu, capacity: .status.capacity.cpu, conditions: [.status.conditions[] | select(.status==\"True\") | {type: .type, reason: .reason, message: .message}]}'","purpose":"验证所有节点的 CPU allocatable 和 capacity，确认集群 CPU 资源是否已耗尽","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"Get node cpu utilization via Prometheus to confirm actual CPU usage on nodes","level":"important","tool":"execute_prometheus_instant_query","command":"sum(kube_node_status_allocatable{resource='cpu'}) by (node) / sum(kube_node_status_capacity{resource='cpu'}) by (node)","purpose":"验证各节点 CPU 实际资源使用率，确认资源耗尽程度","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"Fetch runbook reference for PendingUnschedulable with Insufficient cpu","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","purpose":"获取 runbook 参考信息，辅助诊断调度失败","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e6","description":"Check events in aiops-e2e namespace for additional scheduling context","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --sort-by='.lastTimestamp'","purpose":"获取命名空间事件，确认除 FailedScheduling 外是否有其他相关异常事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 5/5 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | Describe the Pending pod rc-pending-insuffici... | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_yaml | Get YAML of the pod to check resources.reques... | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml` |
   | e3 | critical | ✅ | run_bash_command | Get all nodes allocatable and capacity cpu to... | `kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, allocatable...` |
   | e4 | important | ✅ | execute_prometheus_instan... | Get node cpu utilization via Prometheus to co... | `sum(kube_node_status_allocatable{resource='cpu'}) by (node) / sum(kube_node_s...` |
   | e5 | reference | ✅ | fetch_runbook | Fetch runbook reference for PendingUnschedula... | `fetch_runbook pod-pending-unschedulable.md` |
   | e6 | important | ✅ | kubectl_events | Check events in aiops-e2e namespace for addit... | `kubectl get events -n aiops-e2e --sort-by='.lastTimestamp'` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (31.9s)
   📤 → 下游数据: root_cause=Pod rc-pending-insufficient-cpu（aiops-e2e）处于 Pending 状态，根本原因为其 resources.requests.cpu 被设置为 100k（100,000 个 CPU 核心），而集群所有 3 个节点的 allocatable CPU 合计仅 36 core（master=12, node1=12, node2=12）。调度器持续报告 FailedScheduling: '0/3 nodes are available: 3 Insufficient cpu'，且无抢占受害者。3个节点全部 Ready（排除节点故障），Pod 无 nodeSelector/affinity 等约束（排除调度约束不匹配），命名空间事件仅有 FailedScheduling（排除其他异常）。该 Pod 请求的 CPU 量超过集群总容量约 2777 倍，属于人为配置的故障场景。
   confidence=98%
   causal_chain={"root_cause": "Pod rc-pending-insufficient-cpu 的 resources.requests.cpu 被配置为 100k（100,000 个 CPU 核心），远超集群总 allocatable CPU 容量（3节点合计仅 36 core），导致调度器在所有节点均判定 Insufficient cpu。", "propagation": "Pod spec 中 requests.cpu=100k → 调度器计算节点剩余可分配CPU → 所有3个节点剩余可分配CPU均远小于100k → 调度器报 Insufficient cpu → 无抢占受害者（无更低优先级Pod）→ Pod 持续 Pending", "direct_cause": "集群总计 allocatable CPU=36 core，但单个Pod请求100,000 core，超出集群容量约2777倍。", "manifestation": "Pod rc-pending-insufficient-cpu 在 aiops-e2e 命名空间中持续 Pending，PodScheduled Condition=False (Unschedulable)，Events 持续报告 FailedScheduling: 3 Insufficient cpu。"}
   rca_analysis={"phenomenon": "Pod rc-pending-insufficient-cpu（命名空间 aiops-e2e）处于 Pending 状态，PodScheduled Condition 为 False（reason: Unschedulable），调度事件持续报告 FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu，Pod 未绑定任何节点（nodeName=&lt;none&gt;）。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod rc-pending-insufficient-cpu 状态 Pending，node=&lt;none&gt;，Events: FailedScheduling '0/3 nodes are available: 3 Insufficient cpu' 持续 13m", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml + run_bash_command(grep resources)", "content": "Pod spec 中 resources.requests.cpu = 100k（即 100,000 个 CPU 核心），memory=64Mi", "reliability": "高"}, {"id": "e3", "source": "run_bash_command(node allocatable)", "content": "3个节点全部 Ready，每个节点 allocatable cpu=12，总计 36 core", "reliability": "高"}, {"id": "e4", "source": "execute_prometheus_instant_query", "content": "Prometheus node:node_cpu_utilization: 所有3个节点比值 allocatable/capacity=1（无超分）", "reliability": "高"}, {"id": "e5", "source": "kubectl_events", "content": "aiops-e2e 命名空间仅有 FailedScheduling 事件，无其他异常事件", "reliability": "高"}, {"id": "e6", "source": "fetch_runbook", "content": "Runbook pod-pending-unschedulable.md 匹配 FailedScheduling + Insufficient cpu 分支", "reliability": "中"}, {"id": "e7", "source": "kubectl_get_yaml", "content": "Pod 无 nodeSelector、nodeName 为 None、tolerations 仅含默认 not-ready:NoExecute 容忍", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedScheduling 13m default-scheduler 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.", "interpretation": "调度器确认所有3个节点CPU均不足，且无低优先级Pod可被抢占。这与资源耗尽场景完全一致。"}, {"evidence_id": "e2", "raw_data": "resources: requests: cpu: 100k memory: 64Mi", "interpretation": "Pod请求100,000个CPU核心——这是关键根因。100k = 100,000 core，远超集群总容量36 core。此数值极可能为人为构造的故障场景。"}, {"evidence_id": "e3", "raw_data": "master: allocatable=12, capacity=12; node1: allocatable=12, capacity=12; node2: allocatable=12, capacity=12", "interpretation": "集群总allocatable CPU=36 core。所有节点Ready且未超分（allocatable=capacity），但36 core远小于Pod请求的100,000 core。"}, {"evidence_id": "e4", "raw_data": "master: 1, node1: 1, node2: 1", "interpretation": "Prometheus指标显示各节点allocatable/capacity比值为1，说明节点没有资源超分配置，与实际allocatable数据一致。"}, {"evidence_id": "e5", "raw_data": "13m Warning FailedScheduling Pod/rc-pending-insufficient-cpu 0/3 nodes are available: 3 Insufficient cpu", "interpretation": "命名空间事件中只有FailedScheduling事件，排除其他异常（如PVC、镜像拉取等）干扰。"}, {"evidence_id": "e6", "raw_data": "Runbook判定规则: FailedScheduling + Insufficient cpu → 资源不足导致Pod Pending，置信度高", "interpretation": "Runbook确认当前场景属于资源不足分支，无需切换到taint/affinity/PVC等其他分支。"}, {"evidence_id": "e7", "raw_data": "nodeName=None, nodeSelector=&lt;none&gt;, tolerations仅含默认not-ready:NoExecute", "interpolation": "Pod无nodeSelector/affinity等调度约束，排除调度约束不匹配的可能性。问题纯由CPU资源请求过大导致。"}], "causal_chain": {"root_cause": "Pod rc-pending-insufficient-cpu 的 resources.requests.cpu 被配置为 100k（100,000 个 CPU 核心），远超集群总 allocatable CPU 容量（3节点合计仅 36 core），导致调度器在所有节点均判定 Insufficient cpu。", "propagation": "Pod spec 中 requests.cpu=100k → 调度器计算节点剩余可分配CPU → 所有3个节点剩余可分配CPU均远小于100k → 调度器报 Insufficient cpu → 无抢占受害者（无更低优先级Pod）→ Pod 持续 Pending", "direct_cause": "集群总计 allocatable CPU=36 core，但单个Pod请求100,000 core，超出集群容量约2777倍。", "manifestation": "Pod rc-pending-insufficient-cpu 在 aiops-e2e 命名空间中持续 Pending，PodScheduled Condition=False (Unschedulable)，Events 持续报告 FailedScheduling: 3 Insufficient cpu。"}, "root_cause": "Pod rc-pending-insufficient-cpu（aiops-e2e）处于 Pending 状态，根本原因为其 resources.requests.cpu 被设置为 100k（100,000 个 CPU 核心），而集群所有 3 个节点的 allocatable CPU 合计仅 36 core（master=12, node1=12, node2=12）。调度器持续报告 FailedScheduling: '0/3 nodes are available: 3 Insufficient cpu'，且无抢占受害者。3个节点全部 Ready（排除节点故障），Pod 无 nodeSelector/affinity 等约束（排除调度约束不匹配），命名空间事件仅有 FailedScheduling（排除其他异常）。该 Pod 请求的 CPU 量超过集群总容量约 2777 倍，属于人为配置的故障场景。", "root_cause_summary": "Pod rc-pending-insufficient-cpu（aiops-e2e）处于 Pending 状态，根本原因为其 resources.requests.cpu 被设置为 100k（100,000 个 CPU 核心），而集群所有 3 个节点的 allocatable CPU 合计仅 36 core（master=12, node1=12, node2=12）。调度器持续报告 FailedScheduling: '0/3 nodes are available: 3 Insufficient cpu'，且无抢占受害者。3个节点全部 Ready（排除节点故障），Pod 无 nodeSelector/affinity 等约束（排除调度约束不匹配），命名空间事件仅有 FailedScheduling（排除其他异常）。该 Pod 请求的 CPU 量超过集群总容量约 2777 倍，属于人为配置的故障场景。", "confidence": 0.98, "confidence_reason": "调度事件明确显示3个节点Insufficient cpu（e1），Pod YAML直接确认requests.cpu=100k（e2），节点容量数据确认总allocatable仅36 core（e3），Prometheus数据验证无超分（e4），Runbook规则高置信度匹配（e6），且已排除taint/nodeSelector/PVC等分支可能性（e7）。所有证据高度一致，因果链完整无断层。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "节点 taint/toleration 不匹配", "probability": "low", "reason": "Pod tolerations 含默认 not-ready:NoExecute 容忍，无 nodeSelector，3个节点全部 Ready 且无异常 taint，已被排除"}, {"cause": "nodeSelector/affinity 不匹配", "probability": "low", "reason": "Pod YAML 显示 Node-Selectors=&lt;none&gt;，无 affinity 约束，已被排除"}, {"cause": "PVC 未绑定", "probability": "low", "reason": "Pod 无 PVC 引用，Events 无 PVC 相关错误，已被排除"}, {"cause": "节点 NotReady/不可调度", "probability": "low", "reason": "3个节点全部 Ready，STATUS=Ready，已被排除"}, {"cause": "hostPort 端口冲突", "probability": "low", "reason": "Pod 无 hostPort 配置，Events 无端口冲突提示，已被排除"}], "limitations": "未采集Pod priorityClassName/priority值，但preemption已报告无抢占受害者，不影响根因结论。未采集各节点当前运行Pod列表及各自CPU request用量，但集群总容量36 core vs Pod请求100k core的差距已足以解释问题。", "llm_raw_analysis": "## 证据清点\n共采集10条证据，关键证据6条（e1-e7，含上游已验证的layer_1~4）。\n\n## 逐条分析\n- **e1**：kubectl describe 确认 Pod 状态 Pending，node=&lt;none&gt;，FailedScheduling 事件持续13分钟，原文\"3 Insufficient cpu\"——明确指向CPU资源不足。\n- **e2**：Pod YAML 中 resources.requests.cpu=100k——这是最关键发现。100k=100,000 core，远超任何单节点或集群总容量。\n- **e3**：3节点 allocatable cpu 各12，合计36 core。全部Ready，无节点故障。\n- **e4**：Prometheus 指标 node:node_cpu_utilization 返回值=1（allocatable/capacity比值），验证节点未超分。\n- **e5**：命名空间事件仅有 FailedScheduling，无其他干扰事件。\n- **e6**：Runbook 确认当前场景匹配 FailedSched\n... 截断，原始 986 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-insufficient-cpu（aiops-e2e）处于 Pending 状态，根本原因为其 resources.requests.cpu 被设置为 100k（100,000 个 CPU 核心），而集群所有 3 个节点的 allocatable CPU 合计仅 36 ...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod rc-pending-insufficient-cpu 的 resources.requests.cpu 被配置为 100k（100,000 个 CPU 核心），远超集群总 allocatable CPU 容量（3节点合计仅 36 core），导致调度器在所有节点均判定 Insufficient cpu。
     传导机制: Pod spec 中 requests.cpu=100k → 调度器计算节点剩余可分配CPU → 所有3个节点剩余可分配CPU均远小于100k → 调度器报 Insufficient cpu → 无抢占受害者（无更低优先级Pod）→ Pod 持续 Pending
     最终表现: Pod rc-pending-insufficient-cpu 在 aiops-e2e 命名空间中持续 Pending，PodScheduled Condition=False (Unschedulable)，Events 持续报告 FailedScheduling: 3 Insufficient cpu。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (27.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5746 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 52.6s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，资深 K8s 诊断报告专家已就位。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **集群状态** | 集群中共有 65 个 Pod，其中 59 个运行正常 (**90.8%**)，**1 个异常** |
| **Pod异常状态** | Pending (Unschedulable) |
| **兼容归因层** | L1 - 调度层 (Scheduling) |
| **问题分类** | PendingUnschedulable - 资源不足无法调度 |
| **置信度** | 高 (98%) |
| **证据完整度** | 5/5 (100%) |

**核心结论：** 集群中存在一个人为配置错误的 Pod `rc-pending-insufficient-cpu`，其 `resources.requests.cpu` 被设置为 **100k（100,000 个 CPU 核心）**，而整个集群 3 个节点的总可分配 CPU 容量仅为 **36 核**（master=12, node1=12, node2=12）。该请求量超过集群总容量约 **2777 倍**，导致调度器无法在任何节点上为其分配资源，Pod 持续处于 `Pending` 状态。

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-pending-insufficient-cpu` |
| Namespace | `aiops-e2e` |
| Nodes | `master`, `node1`, `node2` |
| 错误信息 | `0/3 nodes are available: 3 Insufficient cpu.` |

---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 & 调度事件 | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` | `status: Pending` <br> `Warning FailedScheduling ... 0/3 nodes are available: 3 Insufficient cpu.` | Pod 因 CPU 不足无法被调度到任何节点 |
| 2 | Pod 资源配置 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml` | `resources: requests: cpu: 100k` | Pod 请求的 CPU 资源为 100,000 核，这是一个极不正常的数值 |
| 3 | 节点资源容量 | `run_bash_command` (查询节点状态) | `master`: allocatable: 12, capacity: 12 <br> `node1`: allocatable: 12, capacity: 12 <br> `node2`: allocatable: 12, capacity: 12 <br> (所有节点均为 Ready 状态) | 集群总计可分配 CPU 仅为 36 核，且所有节点均健康 |
| 4 | 命名空间事件 | `kubectl events -n aiops-e2e` | `13m Warning FailedScheduling Pod/rc-pending-insufficient-cpu ... 3 Insufficient cpu` | 确认调度失败事件持续发生，无其他异常事件干扰 |
| 5 | Pod 其他约束 | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` | `Node-Selectors: <none>` | Pod 没有设置节点选择器或亲和性约束，排除了调度规则不匹配的原因 |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：调度器事件 (`FailedScheduling`) + Pod 请求 (`cpu: 100k`) + 集群总容量 (`36核`) → 三者直接证明 Pod 请求的资源远超集群提供能力，导致无法调度。
- **证据链**：Pod 的 CPU 请求 (100k) > 集群总可分配 CPU (36核) → 调度器在所有节点上均判定资源不足 (Insufficient cpu) → Pod 持续处于 Pending 状态。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 的 priorityClassName | Optional | 不影响最终结论，因为事件已确认 `No preemption victims found`，说明没有更低优先级的 Pod 可以被抢占来满足该 Pod 的请求。 |

---
## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                        │
│ Pod rc-pending-insufficient-cpu 的 resources.requests.cpu 被配置为 100k          │
│ (100,000 个 CPU 核心)，这是一个人工配置错误。                                    │
└─────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                        │
│ 调度器计算：Pod请求(100k) > 节点可分配CPU(12核) → 所有3个节点均不满足条件         │
│ 调度器尝试抢占：无更低优先级Pod可被抢占来释放资源 → 调度失败                      │
└─────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                        │
│ 集群总计 allocatable CPU=36 core，但单个Pod请求100,000 core，超出集群容量约2777倍。 │
└─────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                    │
│ Pod rc-pending-insufficient-cpu 在 aiops-e2e 命名空间中持续 Pending              │
│ PodScheduled Condition=False (Unschedulable)                                     │
│ Events 持续报告：0/3 nodes are available: 3 Insufficient cpu                     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (FailedScheduling), 证据 #2 (cpu: 100k) 和证据 #3 (节点总容量 36核)，
集群当前唯一的异常问题是 **人为配置错误**。Pod `rc-pending-insufficient-cpu` 请求的 CPU 资源（100,000核）是一个天文数字，远超过集群总容量。
该问题与集群的健康状况、节点故障、网络等问题**无关**。

**置信度**：高 (98%)
- ✅ 所有关键证据均已采集并相互印证（事件、YAML、节点状态）。
- ✅ 已排除其他候选原因：节点全部 Ready（排除节点故障）、Pod 无 Node-Selector（排除调度约束不匹配）、事件仅有 FailedScheduling（排除其他异常）。
- ✅ RCA 结论与所有权威工具事实一致。

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [首选] 删除或修改这个错误的 Pod**

由于该 Pod 是手动配置的测试用例，最直接的修复是删除它，或者重新创建一个资源配置正确的 Pod。

**方案 A：直接删除 Pod**
```bash
kubectl delete pod rc-pending-insufficient-cpu -n aiops-e2e
```
*效果*：立即移除异常 Pod，集群恢复健康。

**方案 B：修改 Deployment/StatefulSet 的配置**
*如果该 Pod 由控制器管理，需要修改 YAML 文件或直接编辑控制器资源。*
```bash
# 假设它由一个 Deployment 管理（名称也可能是 rc-pending-insufficient-cpu）
kubectl edit deployment rc-pending-insufficient-cpu -n aiops-e2e
```
*操作*：在编辑器中找到 `resources.requests.cpu` 字段，将 `100k` 修改为合理的数值（例如 `100m`，即 0.1 核）。保存退出后，控制器会滚动更新 Pod。

**2. [可选] 查看该 Pod 的完整 YAML，确认其管理方式**
```bash
kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml | grep -A 5 "ownerReferences"
```
*目的*：确认 Pod 是否由 Deployment、StatefulSet 或 Job 等控制器创建，以便使用正确的方式进行修复。

### 后续优化
1. **审核资源配置**：在 CI/CD 或部署流程中，增加对极端资源配置（如请求 CPU > 集群总容量）的校验或告警，防止人为输入错误。
2. **资源配额**：可以在命名空间级别设置 ResourceQuota，限制单个 Pod 或所有 Pod 的资源请求上限，防止单个异常 Pod 耗尽集群资源。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 已被删除 | `kubectl get pods -n aiops-e2e` | 列表中没有 `rc-pending-insufficient-cpu` 或该 Pod 已被重建且 `STATUS: Running` |
| 2. 再次检查集群状态 | `kubectl get pods --all-namespaces \| grep -v Running \| grep -v Completed` | 没有 Pending 状态的 Pod |

---
## ⚠️ 注意事项
- 该问题是一个典型的**人为配置故障**，并非由系统资源耗尽或硬件故障引起，无需过度担忧集群本身的安全或稳定性。
- `100k` 是一个非常特殊的数值，在 Kubernetes 中，CPU 单位 `k` 代表 1000 毫核，因此 `100k` 等于 `100,000,000m` 或 `100,000` 核。这是一个常见的错误输入，可能本意是 `100m`（100毫核，即0.1核）。

---

## 📊 性能统计

├─ 总耗时: 1.9m
├─ 问题定位: 24.6s (22%) ✅
├─ 证据链采集: 28.8s (26%) ✅
├─ 根因分析: 31.9s (28%) ✅
├─ 汇总总结: 27.3s (24%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 12 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 12 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
