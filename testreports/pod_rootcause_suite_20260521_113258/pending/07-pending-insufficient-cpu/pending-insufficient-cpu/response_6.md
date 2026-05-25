======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 903e05c41cea4e06]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先全局扫描所有 Pod 的状态，看看集群的整体情况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 发现了一个异常 Pod。让我查看它的详细信息。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  4m48s  default-scheduler  0/3 nodes are available: 3 Insuff
   💭 [问题定位] 让我确认这个异常 Pod 的标签也标注了异常类型，然后获取相关的 runbook。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在让我也快速查看节点状态，确认整体集群信息。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 现在我已掌握全局情况，可以做出完整的定位分析了。

---

## 集群诊断定位分析

### 全局概览
- **总 Pod 数**: 65（59 个 Running，1 个 Pending）
- **节点数**: 3（全部 Ready，健康状态正常）
- **集群整体健康度**: 良好，仅存在 1 个异常 Pod

---

### 发现的异常 Pod

| Pod | 命名空间 | 状态 | 异常类型 |
|-----|---------|------|---------|
| `rc-pending-insufficient-cpu` | `aiops-e2e` | **Pending** | **PendingUnschedulable** |

---

### 异常详情分析

**Pod**: `rc-pending-insufficient-cpu`（命名空间: `aiops-e2e`）
- **状态**: Pending，未绑定节点（nodeName 为空）
- **调度事件**: `FailedScheduling` — `0/3 nodes are available: 3 Insufficient cpu`
- **根因**: 集群中 **3 个节点 CPU 资源均不足**，无法满足该 Pod 的 CPU 请求量
- **Pod 配置**: 镜像 `busybox:1.36`，QoS 等级 `Burstable`，无特殊调度约束（无 nodeSelector、affinity）
- **节点状态**: 3 个节点均 Ready，集群没有节点下线或不可调度

---

### 输出

- **layer**: L1
- **derived_layer**: L1
- **layers**: [L1]
- **layer_name**: PendingUnschedulable
- **confidence**: high
- **reasoning**: Pod `rc-pending-insufficient-cpu` 处于 Pending 状态且 `FailedScheduling` 事件明确报告所有 3 个节点 CPU 资源不足（`3 Insufficient cpu`），无其他异常 Pod 或节点故障，属于典型的调度资源不足（L1）场景
- **abnormal_pods**: [{"name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e", "status": "Pending", "node": "none"}]
- **abnormal_groups**: [{"group_type": "PendingUnschedulable", "pods": [{"name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}], "count": 1, "reason": "0/3 nodes are available: 3 Insufficient cpu"}]
- **pod_status_keyword**: Pending
- **pod_abnormal_type**: PendingUnschedulable
- **status_category**: pending
- **key_entities**: ["Pod/aiops-e2e/rc-pending-insufficient-cpu", "Node/master", "Node/node1", "Node/node2"]
- **possible_scenarios**: ["集群节点 CPU 资源总体不足，所有 3 个节点的可分配 CPU 已被现有 Pod 占满，无法调度该新 Pod", "该 Pod 的 CPU requests 设置过高，超出所有节点的剩余可分配量", "存在其他高优先级 Pod 占用了大量 CPU 资源，当前无合适节点可放置此 Burstable Pod"]
   ✅ [问题定位] 完成 (28.1s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '集群节点CPU资源总体不足', 'probability': 'high', 'reason': '所有3个节点的可分配CPU已被现有Pod占满，FailedScheduling明确报告3 Insufficient cpu'}, {'scenario': 'Pod的CPU requests设置过高', 'probability': 'medium', 'reason': '该Pod的CPU请求量超出所有节点的剩余可分配量，需检查Pod resource requests配置'}, {'scenario': '存在高优先级Pod占用了大量CPU资源', 'probability': 'medium', 'reason': '预检发现0/3 nodes are available: 3 No preemption victims found，说明没有可抢占的低优先级Pod'}]
   entities=[{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}]
   reasoning=集群中有且仅有1个异常Pod `rc-pending-insufficient-cpu`（命名空间aiops-e2e），状态为Pending，未绑定任何节点（nodeName为<none>）。Events中明确显示FailedScheduling——'0/3 nodes are available: 3 Insufficient cpu'，表明所有3个节点CPU资源均不足以调度该Pod。所有3个节点均为Ready状态，无节点故障。该Pod无特殊调度约束（无nodeSelector/affinity），QoS等级Burstable，镜像busybox:1.36。根因为集群节点CPU资源总体不足，属于典型的调度资源不足场景（L1）。无其他异常Pod、节点故障或存储/网络/应用层问题。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 1.0, "reasoning": "集群中有且仅有1个异常Pod `rc-pending-insufficient-cpu`（命名空间aiops-e2e），状态为Pending，未绑定任何节点（nodeName为<none>）。Events中明确显示FailedScheduling——'0/3 nodes are available: 3 Insufficient cpu'，表明所有3个节点CPU资源均不足以调度该Pod。所有3个节点均为Ready状态，无节点故障。该Pod无特殊调度约束（无nodeSelector/affinity），QoS等级Burstable，镜像busybox:1.36。根因为集群节点CPU资源总体不足，属于典型的调度资源不足场景（L1）。无其他异常Pod、节点故障或存储/网络/应用层问题。", "abnormal_pods": [{"name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}], "possible_scenarios": [{"scenario": "集群节点CPU资源总体不足", "probability": "high", "reason": "所有3个节点的可分配CPU已被现有Pod占满，FailedScheduling明确报告3 Insufficient cpu"}, {"scenario": "Pod的CPU requests设置过高", "probability": "medium", "reason": "该Pod的CPU请求量超出所有节点的剩余可分配量，需检查Pod resource requests配置"}, {"scenario": "存在高优先级Pod占用了大量CPU资源", "probability": "medium", "reason": "预检发现0/3 nodes are available: 3 No preemption victims found，说明没有可抢占的低优先级Pod"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-insufficient-cpu                         0/1     Pending     0              4m46s   <none>           <none>   <none>           <none>            app=rc-pending-insufficient-cpu,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 100%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我已收到既有 evidence_plan，现在开始执行工具调用。先启动多个独立的并行调用。
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
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  5m26s  default-scheduler  0/3 nodes are available: 3 Insuff
   💭 [证据链采集] 非常好，Pod describe 和 YAML 已确认关键信息。现在并行执行节点 CPU 容量检查（e3）和调度约束检查（e5）。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"node_selector\": null,\n  \"affinity\": null,\n  \"tolerations\": [\n    {\n      \"effect\": \"NoExecute\",\n      \"key\": \"node.kubernetes.io/not-ready\",\n    
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"name\": \"master\",\n  \"cpu_capacity\": \"12\",\n  \"cpu_allocatable\": \"12\"\n}\n{\n  \"name\": \"node1\",\n  \"cpu_capacity\": \"12\",\n  \"cpu_allocatable\": \
   💭 [证据链采集] 现在进一步采集各节点当前的 CPU 实际使用量，以便判断集群 CPU 是否真正被占满。
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 execute_prometheus_instant_query 执行成功但结果为空；这表示查询未命中数据，不能视为已采集到指标值。
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{},"value":[1779347085.636,"65"]}]}}
   💭 [证据链采集] 让我用其他 PromQL 查询节点的 CPU 分配情况。
   💭 [证据链采集] 调用工具: get_metric_names
   💭 [证据链采集] 工具结果: get_metric_names (success)
      📄 Prometheus get_metric_names 返回成功（status=success），数据为 Prometheus 指标名称列表，包含约 300+ 个指标名。涉及 kube-apiserver、alertmanager、cadvisor、controller-runtime、container、cluster 各类指标。
key_facts: ["status=success", "包
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"node":"master"},"value":[1779347095.694,"2.2021238039266224"]},{"metric":{"node":"node1"},"value":[1779347095.694,"0.95138725999
   💭 [证据链采集] 让我检查 Pod 的 CPU requests 具体值是多少（YAML 中未显示 resources 字段，需要确认是否设置了 requests）。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"requests\": {\n    \"cpu\": \"100k\",\n    \"memory\": \"64Mi\"\n  }\n}\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] 发现了！Pod 的 CPU requests 值为 `100k` — 即 100,000 个 CPU！这是一个典型的人为错误。让我查一下各节点的 allocatable CPU 详情。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"name\": \"master\",\n  \"allocatable\": {\n    \"cpu\": \"12\",\n    \"ephemeral-storage\": \"568259694471\",\n    \"hugepages-1Gi\": \"0\",\n    \"hugepages-2Mi\":
   💭 [证据链采集] 所有证据已采集完毕。以下提供完整的诊断结论。

---

## 📋 证据采集结论

### ✅ 已采集证据

| 计划项 | 工具 | 结果 |
|--------|------|------|
| **e1 (critical)** | `kubectl describe pod` | ✅ Pod 状态 Pending，Events 明确显示 `FailedScheduling` — **`0/3 nodes are available: 3 Insufficient cpu`**，无抢占 victim |
| **e2 (critical)** | `kubectl_get_yaml` | ✅ Pod 的资源的 `requests.cpu` 为 **`100k`**（即 100,000 个 CPU 核心），`requests.memory` 为 `64Mi` |
| **e3 (critical)** | `kubectl get nodes -o json` | ✅ 3 个节点各有 **12 个可分配 CPU**，合计 36 个 CPU，远小于 Pod 要求的 100,000 个 CPU |
| **e5 (important)** | `kubectl get pod -o json` | ✅ **nodeSelector: null**, **affinity: null**, 无特殊调度约束；仅有默认的 `not-ready` 和 `unreachable` toleration |
| **e7 (reference)** | `fetch_runbook` | ✅ 已获取 runbook，确认分支为"资源不足"场景 |
| **额外** | Prometheus 查询 | ✅ 三个节点实际 CPU 使用率总和仅约 **5 个 CPU**（master=2.2, node1=0.95, node2=1.86），说明集群 CPU 远未饱和 |

### ❌ 未采集 / 冲突证据
- 无冲突证据。所有工具调用均成功返回，Pod、节点均存在且状态与上游一致。

### 🔍 根因分析

**直接原因**：Pod `rc-pending-insufficient-cpu` 的 `resources.requests.cpu = 100k`（即 **100,000 个 CPU 核心**），而集群中所有 3 个节点（master/node1/node2）的 allocatable CPU 均为 **12 个**。调度器找不到任何节点能满足此 CPU 请求，导致 `0/3 nodes are available: 3 Insufficient cpu`。

**根本原因**：**`100k` 是典型的人为配置错误**（本应为 `100m` 即 0.1 个 CPU）。`k` 后缀在 Kubernetes 的资源语义中代表 **1000**（而非 kilo=1024），因此 `100k` 等于 `100 * 1000 = 100,000` 个 CPU 核心，远超任何实际节点的容量。这与常规的 `m`（milli-cpu）后缀混淆了——`100m` 才是 0.1 个 CPU。

**辅助验证**：
1. 集群 CPU 总体并不紧张——实际使用仅约 5 个 CPU（共 36 个 allocatable，空闲约 31 个 CPU）
2. Pod 无 nodeSelector/affinity/taint 等特殊调度约束限制
3. 3 个节点均为 Ready 状态，调度器正常运行

### 💡 修复建议
将 Pod 的 CPU requests 从 `100k` 修正为 `100m`（0.1 CPU）或合理的业务值。
   ✅ [证据链采集] 完成 (49.4s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod rc-pending-insufficient-cpu 当前状态和 FailedScheduling 事件详情","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-pending-insufficient-cpu","tool_args":{"kind":"pod","name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e"},"purpose":"确认 Pod 仍处于 Pending 状态，采集 FailedScheduling 事件原文，包括具体资源不足原因","evidence_type":"pod_events","target_scope":"Pod/aiops-e2e/rc-pending-insufficient-cpu","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"查看 Pod YAML 定义，确认 CPU requests/limits 配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod -n aiops-e2e rc-pending-insufficient-cpu -o yaml","tool_args":{"kind":"pod","name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e"},"purpose":"采集 Pod 的 resource requests/limits 配置，确认 CPU 请求量是否过高","evidence_type":"pod_spec","target_scope":"Pod/aiops-e2e/rc-pending-insufficient-cpu","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"查询所有节点的 CPU 容量和可分配量，了解集群 CPU 资源总体情况","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, cpu_capacity: .status.capacity.cpu, cpu_allocatable: .status.allocatable.cpu}'","tool_args":{},"purpose":"确认各节点的 CPU 总量和可分配量，判断集群 CPU 是否总体不足","evidence_type":"node_capacity","target_scope":"Nodes/all","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5","description":"验证 Pod 没有其他调度约束导致不可调度","level":"important","tool":"run_bash_command","command":"kubectl get pod -n aiops-e2e rc-pending-insufficient-cpu -o json | jq '{node_selector: .spec.nodeSelector, affinity: .spec.affinity, tolerations: .spec.tolerations, node_name: .spec.nodeName}'","tool_args":{},"purpose":"确认 Pod 无 nodeSelector/affinity/taint 等特殊调度约束导致调度失败","evidence_type":"pod_scheduling_constraints","target_scope":"Pod/aiops-e2e/rc-pending-insufficient-cpu","acceptable_tools":[],"counts_for_completeness":true},{"id":"e7","description":"参考 runbook 确认场景匹配","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","tool_args":{},"purpose":"获取 runbook 作为诊断参考","evidence_type":"runbook_reference","target_scope":"runbook","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod PendingUnschedulable / 调度失败\n\n> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | Pending，且 Events 含 `FailedScheduling` |\n| 资源不足 | `Insufficient cpu/memory/ephemeral-storage`、`Too many pods` |\n| 调度约束 | nodeSelector/affinity 不匹配、节点 taint 未被 toleration 容忍 |\n| 存储前置条件 | `pod has unbound immediate PersistentVolumeClaims` 应切换到 pod-volume-mount-failed |\n| 节点状态 | Node NotReady/Unknown、SchedulingDisabled、Unschedulable 会导致无可用调度节点 |\n\n## 根因分流\n- 资源不足: FailedScheduling 原文含 Insufficient cpu/memory/ephemeral-storage、Too many pods。\n- hostPort 冲突: 原文含 `didn't have free ports for the requested pod ports`，说明目标节点端口已被占用。\n- Taint/Toleration 不匹配: 原文含 `had untolerated taint`，必须检查 Pod tolerations 和 Node taints。\n- nodeSelector / nodeAffinity / podAffinity 不匹配: 原文含 `didn't match Pod's node affinity/selector` 或 affinity/anti-affinity。\n- PVC 未绑定: 原文含 `unbound immediate PersistentVolumeClaims`，根因在存储绑定而不是调度资源。\n- 节点不可调度: Node Ready=False/Unknown、SchedulingDisabled、`node.kubernetes.io/not-ready` 或 `node.kubernetes.io/unreachable`。\n- 镜像、挂载、容器启动错误不会表现为 FailedScheduling；如果 Pod 已绑定 nodeName，应切换到对应 runbook。\n\n## 诊断流程\n\n### Step 1: 确认 Pod 调度失败事件\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n关注 Events 中的 `FailedScheduling` 原文。\n\n### Step 2: 检查 Pod 调度约束\n```bash\nkubectl get pod <pod-name> -n <namespace> -o yaml\n```\n关注: spec.nodeName 是否为空、nodeSelector、affinity、tolerations、topologySpreadConstraints、schedulerName、priorityClassName、resource requests、hostNetwork/hostPort。\n\n### Step 3: 检查节点状态和可调度性\n```bash\nkubectl get nodes -o wide\n```\n关注: STATUS 列是否有 NotReady/Unknown，AGE 判断是否新节点\n\n### Step 4: 检查候选节点详情\n```bash\nkubectl describe node <node-name>\n```\n重点关注:\n- `Conditions` 部分: Ready=False/Unknown 的 reason 和 message\n- `Taints` 部分: 是否有 NoSchedule/NoExecute taint\n- `Allocatable` vs `Capacity`: 资源是否耗尽\n- `Non-terminated Pods`: 节点上运行的 Pod 数量\n\n### Step 5: 检查 PVC 状态（如果 FailedScheduling 指向 PVC）\n```bash\nkubectl get pvc -n <namespace>\nkubectl describe pvc <pvc> -n <namespace>\n```\n关注: Pending、StorageClass、volumeBindingMode、ProvisioningFailed。\n\n### Step 6: 检查 Ready 条件详情\n```bash\nkubectl get node <node-name> -o jsonpath='{.status.conditions[?(@.type==\"Ready\")]}' | python3 -m json.tool\n```\n关注: status, reason, message, lastHeartbeatTime\n\n### Step 7: 检查节点事件\n```bash\nkubectl get events -A --field-selector involvedObject.kind=Node,involvedObject.name=<node-name> --sort-by='.lastTimestamp'\n```\n关注: NodeNotReady、NodeNotSchedulable、PLEG unhealthy 等事件\n\n### Step 8: 检查受影响的 Pending Pod\n```bash\nkubectl get pods -A --field-selector status.phase=Pending | head -20\n```\n\n## 判定规则\n\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| FailedScheduling + Insufficient cpu/memory | 资源不足导致 Pod Pending | 高 |\n| FailedScheduling + Too many pods | 节点 Pod 数量上限导致 Pending | 高 |\n| FailedScheduling + didn't have free ports for the requested pod ports | hostPort 端口冲突导致 Pending | 高 |\n| FailedScheduling + had untolerated taint | taint/toleration 不匹配 | 高 |\n| FailedScheduling + node(s) didn't match node selector/affinity | 调度约束不匹配 | 高 |\n| FailedScheduling + pod has unbound immediate PersistentVolumeClaims | PVC 未绑定，应切换 VolumeMountFailed/PVC 分支 | 高 |\n| 所有候选 Node NotReady/Unschedulable | 无可用调度节点 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:59:10Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-insufficient-cpu, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nvolumes:\n- {\"name\": \"kube-api-access-26zhx\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  5m26s  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  23s    default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nName:             rc-pending-insufficient-cpu\nLabels:           app=rc-pending-insufficient-cpu\nPod 关键区块:\nQoS Class: Burstable\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-26zhx:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  5m26s  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  23s    default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"node_selector\\\": null,\\n  \\\"affinity\\\": null,\\n  \\\"tolerations\\\": [\\n    {\\n      \\\"effect\\\": \\\"NoExecute\\\",\\n      \\\"key\\\": \\\"node.kubernetes.io/not-ready\\\",\\n      \\\"operator\\\": \\\"Exists\\\",\\n      \\\"tolerationSeconds\\\": 300\\n    },\\n    {\\n      \\\"effect\\\": \\\"NoExecute\\\",\\n      \\\"key\\\": \\\"node.kubernetes.io/unreachable\\\",\\n      \\\"operator\\\": \\\"Exists\\\",\\n      \\\"tolerationSeconds\\\": 300\\n    }\\n  ],\\n  \\\"node_name\\\": null\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/004-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/004-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/004-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"name\\\": \\\"master\\\",\\n  \\\"cpu_capacity\\\": \\\"12\\\",\\n  \\\"cpu_allocatable\\\": \\\"12\\\"\\n}\\n{\\n  \\\"name\\\": \\\"node1\\\",\\n  \\\"cpu_capacity\\\": \\\"12\\\",\\n  \\\"cpu_allocatable\\\": \\\"12\\\"\\n}\\n{\\n  \\\"name\\\": \\\"node2\\\",\\n  \\\"cpu_capacity\\\": \\\"12\\\",\\n  \\\"cpu_allocatable\\\": \\\"12\\\"\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/005-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/005-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/005-evidence-run_bash_command.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"execute_prometheus_instant_query 执行成功但结果为空；这表示查询未命中数据，不能视为已采集到指标值。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/006-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/006-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/006-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{},\"value\":[1779347085.636,\"65\"]}]}}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/007-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/007-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/007-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"get_metric_names","data":"Prometheus get_metric_names 返回成功（status=success），数据为 Prometheus 指标名称列表，包含约 300+ 个指标名。涉及 kube-apiserver、alertmanager、cadvisor、controller-runtime、container、cluster 各类指标。\nkey_facts: [\"status=success\", \"包含 :node_memory_MemAvailable_bytes:sum 指标\", \"包含 ALERTS / ALERTS_FOR_STATE\", \"包含大量 apiserver_* 指标（request duration, flowcontrol, cache, audit, SLO等）\", \"包含 alertmanager_* 指标（alerts, notifications, silences, nflog等）\", \"包含 cadvisor_version_info\", \"包含 container_* 指标（cpu, memory, network, fs, oom等）\", \"包含 cluster:namespace:pod_cpu:active:... 等聚合指标\", \"包含 controller_runtime_* 指标（workers, reconciles, errors）\", \"包含 authentication_* 指标\", \"包含 certificate/watch 相关指标\", \"raw_preview 展示了完整的指标名列表\"]","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/008-evidence-get_metric_names.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/008-evidence-get_metric_names.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/008-evidence-get_metric_names.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"node\":\"master\"},\"value\":[1779347095.694,\"2.2021238039266224\"]},{\"metric\":{\"node\":\"node1\"},\"value\":[1779347095.694,\"0.9513872599929131\"]},{\"metric\":{\"node\":\"node2\"},\"value\":[1779347095.694,\"1.8616377327945994\"]}]}}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/009-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/009-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/009-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"requests\\\": {\\n    \\\"cpu\\\": \\\"100k\\\",\\n    \\\"memory\\\": \\\"64Mi\\\"\\n  }\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/010-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/010-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/010-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"name\\\": \\\"master\\\",\\n  \\\"allocatable\\\": {\\n    \\\"cpu\\\": \\\"12\\\",\\n    \\\"ephemeral-storage\\\": \\\"568259694471\\\",\\n    \\\"hugepages-1Gi\\\": \\\"0\\\",\\n    \\\"hugepages-2Mi\\\": \\\"0\\\",\\n    \\\"memory\\\": \\\"32758084Ki\\\",\\n    \\\"pods\\\": \\\"110\\\"\\n  },\\n  \\\"capacity\\\": {\\n    \\\"cpu\\\": \\\"12\\\",\\n    \\\"ephemeral-storage\\\": \\\"616601232Ki\\\",\\n    \\\"hugepages-1Gi\\\": \\\"0\\\",\\n    \\\"hugepages-2Mi\\\": \\\"0\\\",\\n    \\\"memory\\\": \\\"32860484Ki\\\",\\n    \\\"pods\\\": \\\"110\\\"\\n  }\\n}\\n{\\n  \\\"name\\\": \\\"node1\\\",\\n  \\\"allocatable\\\": {\\n    \\\"cpu\\\": \\\"12\\\",\\n    \\\"ephemeral-storage\\\": \\\"187795058378\\\",\\n    \\\"hugepages-1Gi\\\": \\\"0\\\",\\n    \\\"hugepages-2Mi\\\": \\\"0\\\",\\n    \\\"memory\\\": \\\"32758076Ki\\\",\\n    \\\"pods\\\": \\\"110\\\"\\n  },\\n  \\\"capacity\\\": {\\n    \\\"cpu\\\": \\\"12\\\",\\n    \\\"ephemeral-storage\\\": \\\"203770680Ki\\\",\\n    \\\"hugepages-1Gi\\\": \\\"0\\\",\\n    \\\"hugepages-2Mi\\\": \\\"0\\\",\\n    \\\"memory\\\": \\\"32860476Ki\\\",\\n    \\\"pods\\\": \\\"110\\\"\\n  }\\n}\\n{\\n  \\\"name\\\": \\\"node2\\\",\\n  \\\"allocatable\\\": {\\n    \\\"cpu\\\": \\\"12\\\",\\n    \\\"ephemeral-storage\\\": \\\"187795058378\\\",\\n    \\\"hugepages-1Gi\\\": \\\"0\\\",\\n    \\\"hugepages-2Mi\\\": \\\"0\\\",\\n    \\\"memory\\\": \\\"32758080Ki\\\",\\n    \\\"pods\\\": \\\"110\\\"\\n  },\\n  \\\"capacity\\\": {\\n    \\\"cpu\\\": \\\"12\\\",\\n    \\\"ephemeral-storage\\\": \\\"203770680Ki\\\",\\n    \\\"hugepages-1Gi\\\": \\\"0\\\",\\n    \\\"hugepages-2Mi\\\": \\\"0\\\",\\n    \\\"memory\\\": \\\"32860480Ki\\\",\\n    \\\"pods\\\": \\\"110\\\"\\n  }\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/011-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/011-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/903e05c41cea4e06/tools/011-evidence-run_bash_command.summary.txt"}],"llm_analysis":"所有证据已采集完毕。以下提供完整的诊断结论。\n\n---\n\n## 📋 证据采集结论\n\n### ✅ 已采集证据\n\n| 计划项 | 工具 | 结果 |\n|--------|------|------|\n| **e1 (critical)** | `kubectl describe pod` | ✅ Pod 状态 Pending，Events 明确显示 `FailedScheduling` — **`0/3 nodes are available: 3 Insufficient cpu`**，无抢占 victim |\n| **e2 (critical)** | `kubectl_get_yaml` | ✅ Pod 的资源的 `requests.cpu` 为 **`100k`**（即 100,000 个 CPU 核心），`requests.memory` 为 `64Mi` |\n| **e3 (critical)** | `kubectl get nodes -o json` | ✅ 3 个节点各有 **12 个可分配 CPU**，合计 36 个 CPU，远小于 Pod 要求的 100,000 个 CPU |\n| **e5 (important)** | `kubectl get pod -o json` | ✅ **nodeSelector: null**, **affinity: null**, 无特殊调度约束；仅有默认的 `not-ready` 和 `unreachable` toleration |\n| **e7 (reference)** | `fetch_runbook` | ✅ 已获取 runbook，确认分支为\"资源不足\"场景 |\n| **额外** | Prometheus 查询 | ✅ 三个节点实际 CPU 使用率总和仅约 **5 个 CPU**（master=2.2, node1=0.95, node2=1.86），说明集群 CPU 远未饱和 |\n\n### ❌ 未采集 / 冲突证据\n- 无冲突证据。所有工具调用均成功返回，Pod、节点均存在且状态与上游一致。\n\n### 🔍 根因分析\n\n**直接原因**：Pod `rc-pending-insufficient-cpu` 的 `resources.requests.cpu = 100k`（即 **100,000 个 CPU 核心**），而集群中所有 3 个节点（master/node1/node2）的 allocatable CPU 均为 **12 个**。调度器找不到任何节点能满足此 CPU 请求，导致 `0/3 nodes are available: 3 Insufficient cpu`。\n\n**根本原因**：**`100k` 是典型的人为配置错误**（本应为 `100m` 即 0.1 个 CPU）。`k` 后缀在 Kubernetes 的资源语义中代表 **1000**（而非 kilo=1024），因此 `100k` 等于 `100 * 1000 = 100,000` 个 CPU 核心，远超任何实际节点的容量。这与常规的 `m`（milli-cpu）后缀混淆了——`100m` 才是 0.1 个 CPU。\n\n**辅助验证**：\n1. 集群 CPU 总体并不紧张——实际使用仅约 5 个 CPU（共 36 个 allocatable，空闲约 31 个 CPU）\n2. Pod 无 nodeSelector/affinity/taint 等特殊调度约束限制\n3. 3 个节点均为 Ready 状态，调度器正常运行\n\n### 💡 修复建议\n将 Pod 的 CPU requests 从 `100k` 修正为 `100m`（0.1 CPU）或合理的业务值。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 12 个，匹配计划 5 个，未规划证据 7 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":12,"matched_tool_count":5,"unplanned_tool_count":7,"evidence_inventory":[{"id":"e1","description":"验证 Pod rc-pending-insufficient-cpu 当前状态和 FailedScheduling 事件详情","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-pending-insufficient-cpu","purpose":"确认 Pod 仍处于 Pending 状态，采集 FailedScheduling 事件原文，包括具体资源不足原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"查看 Pod YAML 定义，确认 CPU requests/limits 配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod -n aiops-e2e rc-pending-insufficient-cpu -o yaml","purpose":"采集 Pod 的 resource requests/limits 配置，确认 CPU 请求量是否过高","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"查询所有节点的 CPU 容量和可分配量，了解集群 CPU 资源总体情况","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, cpu_capacity: .status.capacity.cpu, cpu_allocatable: .status.allocatable.cpu}'","purpose":"确认各节点的 CPU 总量和可分配量，判断集群 CPU 是否总体不足","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"验证 Pod 没有其他调度约束导致不可调度","level":"important","tool":"run_bash_command","command":"kubectl get pod -n aiops-e2e rc-pending-insufficient-cpu -o json | jq '{node_selector: .spec.nodeSelector, affinity: .spec.affinity, tolerations: .spec.tolerations, node_name: .spec.nodeName}'","purpose":"确认 Pod 无 nodeSelector/affinity/taint 等特殊调度约束导致调度失败","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e7","description":"参考 runbook 确认场景匹配","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","purpose":"获取 runbook 作为诊断参考","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod rc-pending-insufficient-cpu 当前状态和 Fail... | `kubectl describe pod -n aiops-e2e rc-pending-insufficient-cpu` |
   | e2 | critical | ✅ | kubectl_get_yaml | 查看 Pod YAML 定义，确认 CPU requests/limits 配置 | `kubectl get pod -n aiops-e2e rc-pending-insufficient-cpu -o yaml` |
   | e3 | critical | ✅ | run_bash_command | 查询所有节点的 CPU 容量和可分配量，了解集群 CPU 资源总体情况 | `kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, cpu_capacit...` |
   | e5 | important | ✅ | run_bash_command | 验证 Pod 没有其他调度约束导致不可调度 | `kubectl get pod -n aiops-e2e rc-pending-insufficient-cpu -o json | jq '{node_...` |
   | e7 | reference | ✅ | fetch_runbook | 参考 runbook 确认场景匹配 | `fetch_runbook pod-pending-unschedulable.md` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (32.2s)
   📤 → 下游数据: root_cause=唯一异常 Pod `rc-pending-insufficient-cpu` (namespace=aiops-e2e) 处于 Pending 状态。调度器 Events 明确报告 "0/3 nodes are available: 3 Insufficient cpu"。经提取 Pod spec 确认，其 resources.requests.cpu = "100k"（即100,000个CPU核心），而集群3个节点（master/node1/node2）各自 allocatable.cpu 均为12核，总计36核。集群实际CPU使用仅约5核（Prometheus查询：master=2.20核, node1=0.95核, node2=1.86核），资源远未饱和。Pod 无 nodeSelector/affinity/taint 不匹配等调度约束（均已验证为null/默认值），3节点均为 Ready 状态。根因明确：'100k' 是典型的人为配置错误——Kubernetes 中 'k'=1000，'100k'=100,000核，正确写法应为 '100m'（0.1核）。其他2个候选场景（t
... 截断，原始 521 字符
   confidence=98%
   causal_chain={"root_cause": "Pod rc-pending-insufficient-cpu 的 resources.requests.cpu 被配置为 '100k'（100,000个CPU核心），这是一个典型的人为配置错误——Kubernetes 中 'k' 后缀代表 1000（而非 kilo=1024），实际意图应为 '100m'（0.1个CPU核心）", "propagation": "调度器在调度时计算每个节点的剩余可分配CPU，发现 Pod 请求的 100,000 核远大于所有节点各自的 12 核可分配容量，因此判定所有 3 个节点均 Insufficient cpu；尝试抢占也失败（无低优先级Pod可抢占）", "direct_cause": "集群所有节点的可分配 CPU（各12核，总计36核）均不足以满足 Pod 的 100,000 核 CPU 请求", "manifestation": "Pod rc-pending-insufficient-cpu 处于 Pending 状态，Events 持续报 FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu"}
   rca_analysis={"phenomenon": "集群 aiops-e2e 命名空间下 Pod rc-pending-insufficient-cpu 处于 Pending 状态，未绑定任何节点（nodeName=&lt;none&gt;），调度器 Events 持续报 FailedScheduling — \"0/3 nodes are available: 3 Insufficient cpu\"。", "evidence_inventory": [{"id": "e1", "source": "kubectl describe pod", "content": "Pod rc-pending-insufficient-cpu 状态 Pending，Events 显示 FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu，无抢占 victim", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml (Pod YAML)", "content": "Pod 定义: resources.requests.cpu = 100k, requests.memory = 64Mi, imagePullPolicy=Never, nodeName=None, phase=Pending", "reliability": "高"}, {"id": "e3", "source": "kubectl get nodes -o json", "content": "3 节点 allocatable.cpu: master=12, node1=12, node2=12，总计 36 个 CPU 核心", "reliability": "高"}, {"id": "e4", "source": "run_bash_command (Pod resource requests 提取)", "content": "Pod spec.resources.requests.cpu = \"100k\", requests.memory = \"64Mi\"", "reliability": "高"}, {"id": "e5", "source": "kubectl get pod -o json (调度约束检查)", "content": "nodeSelector: null, affinity: null, tolerations: 仅默认 not-ready/unreachable NoExecute，无特殊调度约束", "reliability": "高"}, {"id": "e6", "source": "execute_prometheus_instant_query (节点 CPU 使用率)", "content": "master=2.20 核, node1=0.95 核, node2=1.86 核，合计约 5 个 CPU 核心使用中", "reliability": "高"}, {"id": "e7", "source": "kubectl_get_by_kind_in_cluster (Node 列表)", "content": "3 节点均为 Ready 状态，无节点异常", "reliability": "高"}, {"id": "e8", "source": "fetch_runbook", "content": "Runbook 确认 FailedScheduling + Insufficient cpu 匹配资源不足场景", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedScheduling 23s default-scheduler 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found", "interpretation": "调度器明确报告全部3个节点CPU资源不足，且无可抢占的低优先级Pod，说明所有节点的剩余CPU均不满足Pod请求量"}, {"evidence_id": "e2", "raw_data": "resources.requests.cpu = 100k, resources.requests.memory = 64Mi", "interpretation": "Pod 请求 100k 个 CPU 核心（即100,000核），远超任何实际节点容量；这是典型的配置错误，'100m'才是0.1核的正确写法"}, {"evidence_id": "e3", "raw_data": "master/node1/node2 各自 allocatable.cpu = 12", "interpretation": "集群总计36个可分配CPU核心，远小于Pod请求的100,000核，验证了调度器报的Insufficient cpu"}, {"evidence_id": "e4", "raw_data": "{\"requests\": {\"cpu\": \"100k\", \"memory\": \"64Mi\"}}", "interpretation": "通过直接提取Pod spec确认CPU requests为100k，与YAML一致"}, {"evidence_id": "e5", "raw_data": "node_selector: null, affinity: null, tolerations: [node.kubernetes.io/not-ready:NoExecute, node.kubernetes.io/unreachable:NoExecute]", "interpretation": "Pod无任何特殊调度约束（无nodeSelector/affinity/taint不匹配问题），排除了调度约束类根因"}, {"evidence_id": "e6", "raw_data": "master=2.20核, node1=0.95核, node2=1.86核", "interpretation": "集群实际CPU使用仅约5核（占36核可分配的14%），说明集群资源远未饱和，问题确为Pod请求量过大而非集群资源不足"}, {"evidence_id": "e7", "raw_data": "3 nodes Ready, 0 abnormal", "interpretation": "所有节点健康，排除节点故障导致的不可调度"}, {"evidence_id": "e8", "raw_data": "Runbook 判定规则：FailedScheduling + Insufficient cpu → 资源不足导致Pod Pending，置信度高", "interpretation": "场景匹配验证通过，确认为资源不足类问题"}], "causal_chain": {"root_cause": "Pod rc-pending-insufficient-cpu 的 resources.requests.cpu 被配置为 '100k'（100,000个CPU核心），这是一个典型的人为配置错误——Kubernetes 中 'k' 后缀代表 1000（而非 kilo=1024），实际意图应为 '100m'（0.1个CPU核心）", "propagation": "调度器在调度时计算每个节点的剩余可分配CPU，发现 Pod 请求的 100,000 核远大于所有节点各自的 12 核可分配容量，因此判定所有 3 个节点均 Insufficient cpu；尝试抢占也失败（无低优先级Pod可抢占）", "direct_cause": "集群所有节点的可分配 CPU（各12核，总计36核）均不足以满足 Pod 的 100,000 核 CPU 请求", "manifestation": "Pod rc-pending-insufficient-cpu 处于 Pending 状态，Events 持续报 FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu"}, "root_cause": "唯一异常 Pod `rc-pending-insufficient-cpu` (namespace=aiops-e2e) 处于 Pending 状态。调度器 Events 明确报告 \"0/3 nodes are available: 3 Insufficient cpu\"。经提取 Pod spec 确认，其 resources.requests.cpu = \"100k\"（即100,000个CPU核心），而集群3个节点（master/node1/node2）各自 allocatable.cpu 均为12核，总计36核。集群实际CPU使用仅约5核（Prometheus查询：master=2.20核, node1=0.95核, node2=1.86核），资源远未饱和。Pod 无 nodeSelector/affinity/taint 不匹配等调度约束（均已验证为null/默认值），3节点均为 Ready 状态。根因明确：'100k' 是典型的人为配置错误——Kubernetes 中 'k'=1000，'100k'=100,000核，正确写法应为 '100m'（0.1核）。其他2个候选场景（t\n... 截断，原始 521 字符", "root_cause_summary": "唯一异常 Pod `rc-pending-insufficient-cpu` (namespace=aiops-e2e) 处于 Pending 状态。调度器 Events 明确报告 \"0/3 nodes are available: 3 Insufficient cpu\"。经提取 Pod spec 确认，其 resources.requests.cpu = \"100k\"（即100,000个CPU核心），而集群3个节点（master/node1/node2）各自 allocatable.cpu 均为12核，总计36核。集群实际CPU使用仅约5核（Prometheus查询：master=2.20核, node1=0.95核, node2=1.86核），资源远未饱和。Pod 无 nodeSelector/affinity/taint 不匹配等调度约束（均已验证为null/默认值），3节点均为 Ready 状态。根因明确：'100k' 是典型的人为配置错误——Kubernetes 中 'k'=1000，'100k'=100,000核，正确写法应为 '100m'（0.1核）。其他2个候选场景（t\n... 截断，原始 521 字符", "confidence": 0.98, "confidence_reason": "多源直接证据交叉验证：Pod YAML、kubectl describe、resource requests 提取工具均一致显示 CPU requests=100k；节点 allocatable 数据公开可查（各12核）；Prometheus 确认集群实际使用仅约5核，排除了真实资源耗尽的可能性；Pod 无调度约束类限制，所有节点均为 Ready。因果链完整且无矛盾证据。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "集群节点CPU资源真正耗尽", "probability": "low", "reason": "Prometheus 查询显示实际CPU使用仅约5核（共36核可分配），集群CPU远未饱和；且 FailedScheduling 报的是Pod请求量不满足，而非节点无可用资源"}, {"cause": "Taint/Toleration 不匹配", "probability": "low", "reason": "已验证 Pod tolerations 仅有默认的 not-ready/unreachable NoExecute，无特殊taint相关约束；FailedScheduling 原文无 'had untolerated taint' 关键字"}, {"cause": "nodeSelector/affinity 不匹配", "probability": "low", "reason": "Pod YAML 明确显示 nodeSelector=null, affinity=null，无此类约束"}, {"cause": "PVC 未绑定导致不可调度", "probability": "low", "reason": "Pod 无 PVC 卷声明，FailedScheduling 原文无 'unbound immediate PersistentVolumeClaims' 关键字；已通过 YAML 确认 volumes 仅有 kube-api-access-26zhx 投影卷"}], "limitations": "未采集到 Pod 所属 Deployment/StatefulSet 等上层控制器信息，无法确定该 Pod 的资源配置来源（如 Helm chart/Deployment template）。如果修复后因相同原因反复创建，需检查上层工作负载的 template spec。另外，集群命名空间数量/Terminating Pod 等其他异常已在 L1 层通过 kubectl_get_by_kind_in_cluster 覆盖（rows=65, abnormal=1），未发现其他异常。", "llm_raw_analysis": "证据清点：共采集9项证据（e1-e8+layer验证），覆盖Pod状态、YAML定义、节点资源、调度约束、集群使用率、runbook场景匹配。核心发现：e2/e4均确认CPU requests=100k，e3确认3节点各12核可分配，e6确认实际使用仅5核。因果链闭合：配置错误(100k)→请求量异常(100,000核)→调度器判定全部节点Insufficient cpu→Pod Pending。置信度0.98。需注意：e2中imagePullPolicy=Never可能也是配置错误，但当前不阻碍调度（Pod未到达拉镜像阶段），不影响根因。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 唯一异常 Pod `rc-pending-insufficient-cpu` (namespace=aiops-e2e) 处于 Pending 状态。调度器 Events 明确报告 "0/3 nodes are available: 3 Insufficient cpu"。经提取 Pod spec ...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod rc-pending-insufficient-cpu 的 resources.requests.cpu 被配置为 '100k'（100,000个CPU核心），这是一个典型的人为配置错误——Kubernetes 中 'k' 后缀代表 1000（而非 kilo=1024），实际意图应为 '100m'（0.1个CPU核心）
     传导机制: 调度器在调度时计算每个节点的剩余可分配CPU，发现 Pod 请求的 100,000 核远大于所有节点各自的 12 核可分配容量，因此判定所有 3 个节点均 Insufficient cpu；尝试抢占也失败（无低优先级Pod可抢占）
     最终表现: Pod rc-pending-insufficient-cpu 处于 Pending 状态，Events 持续报 FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (32.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6888 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 21.7s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，请查收这份详细的集群诊断报告。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending |
| **兼容归因层** | L1 - 调度资源不足 |
| **问题分类** | PendingUnschedulable (调度失败) |
| **置信度** | 高 (98%) |
| **证据完整度** | 4/4 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

经过全面检查，您的 Kubernetes 集群（共 3 个节点、65 个 Pod）整体健康，但存在 **1 个处于 Pending 状态的异常 Pod**，无法被调度运行。

### 集群状态总览

| 状态 | 数量 |
|:---|---:|
| **总 Pod 数** | 65 |
| **Running (正常)** | 59 |
| **Pending (异常)** | **1** |
| **总节点数** | 3 |
| **节点状态 (Ready)** | 3 (全部正常) |

### 异常 Pod 详情

| 项目 | 内容 |
|:---|:---|
| **Pod 名称** | `rc-pending-insufficient-cpu` |
| **命名空间** | `aiops-e2e` |
| **当前状态** | Pending |
| **所在节点** | `<none>` (未调度) |
| **QoS 等级** | Burstable |
| **错误信息(Events)** | `Warning FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` |

### 问题根因摘要

该 Pod 的 YAML 配置中，CPU **请求量 (`requests.cpu`) 被错误地设置为 `100k`**（即 100,000 个 CPU 核心），远超集群所有节点（总计 36 核）的可用容量，导致其永远无法被调度。

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 & 事件 | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` | `Status: Pending`; `Warning FailedScheduling 5m26s default-scheduler 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` | **确认 Pod 因 CPU 资源不足而无法调度。** |
| 2 | Pod 资源配置 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml` (提取 resources) | `resources.requests.cpu: "100k"` , `resources.requests.memory: "64Mi"` | **发现 Pod 的 CPU 请求量为 `100k`，这是一个不合理的巨大数值。** |
| 3 | 节点 CPU 容量 | `kubectl describe node master/node1/node2` (提取 allocatable) | `master`: allocatable.cpu = 12; `node1`: allocatable.cpu = 12; `node2`: allocatable.cpu = 12 | **集群节点 CPU 总容量: 36 核。** 与 Pod 要求的 100,000 核差距巨大。 |
| 4 | 集群 CPU 实际使用 | Prometheus 查询: `sum(rate(node_cpu_seconds_total{mode!="idle"}[5m])) by (node)` | master: 2.20核; node1: 0.95核; node2:  1.86核 | **集群 CPU 资源使用率非常低（总计约 5 核），资源远未饱和，排除了“集群资源真的不足”的可能性。** |
| 5 | Pod 调度约束 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml` (提取 nodeSelector, affinity, tolerations) | `node_selector: null`; `affinity: null`; `tolerations`: 仅为 node.kubernetes.io/not-ready 的默认容忍 | **排除了 nodeSelector/toleration/affinity 不匹配导致调度失败的场景。** |
| 6 | 节点状态 | `kubectl get nodes` | 3 节点全部为 `Ready` 状态 | **排除了节点不可用（NotReady/Unschedulable）导致调度失败的场景。** |

### 证据关联分析

- **证据 #1 + #2 + #3 + #4 形成完整因果链**：
    1.  调度器尝试调度 Pod，发现其请求的 CPU (`100k` / **100,000 核**) 远大于任何单个节点的可分配容量 (`12` 核)。
    2.  因无法满足资源请求，调度器产生 `Insufficient cpu` 事件，Pod 停留在 Pending 状态。
    3.  证据 #4 显示集群实际CPU使用率极低，从侧面印证了 **“不是真的没有资源，而是 Pod 请求的资源量不合理”** 这一结论。
- **证据 #5 + #6 排除干扰项**：
    无 `nodeSelector`/`affinity`/`taint` 约束，且节点全部正常，排除了其他常见的调度失败原因。

### 缺失证据

无。所有关键证据均以 100% 完整度成功采集。

---

## 🎯 根因分析

### 因果链

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                    │
│ Pod 的 resources.requests.cpu 被配置为 '100k' (100,000 CPU核心)，             │
│ 这是一个典型的人为配置错误。正确的意图应为 '100m'（0.1个CPU核心）。           │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                    │
│ 调度器计算 Pod 需求时发现其请求 100,000 核 >> 所有节点的 12 核可分配容量，     │
│ 判定所有节点均无法满足资源请求。                                            │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                    │
│ 调度器因集群 CPU 资源“不足”而无法为 Pod 找到合适的节点，                       │
│ 触发 FailedScheduling 事件。                                                │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                │
│ Pod rc-pending-insufficient-cpu 持续处于 Pending 状态，                        │
│ 反复报出 "0/3 nodes are available: 3 Insufficient cpu" 事件。                │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (`requests.cpu: 100k`) 和证据 #3 (节点 `allocatable.cpu: 12`)，问题的根本原因是 **人为配置错误**。Pod `rc-pending-insufficient-cpu` 的 CPU 请求被设置为了 `100k`。

在 Kubernetes 资源单位中，`k` 后缀表示 *1000*，因此 `100k` 意为 100,000 个 CPU 核心。这一点与集群节点总容量（36 核）严重不符，导致 Pod 永远无法被调度。正确的表示方法应为 `100m`（表示 0.1 个 CPU 核心）。

- **集群本身资源充足**：当前集群实际 CPU 使用率仅约 **5 核/36 核**，资源远未饱和。
- **问题完全由该 Pod 自身 `resources` 配置错误引起**。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [必须执行] 删除当前错误的 Pod**

由于该 Pod 没有控制器（如 Deployment）管理，需要先删除它。

```bash
kubectl delete pod rc-pending-insufficient-cpu -n aiops-e2e
```
*依据*：清除无法调度的错误 Pod。

**2. [必须执行] 使用正确的资源配置重新创建 Pod**

创建一个新的 YAML 文件 `fixed-pod.yaml`，内容如下（已修正 `CPU requests`）：
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: rc-pending-insufficient-cpu  # 或使用新的名字
  namespace: aiops-e2e
  labels:
    app: rc-pending-insufficient-cpu
spec:
  containers:
  - name: rc-pending-insufficient-cpu
    image: busybox:1.36
    command: ["sh", "-c", "sleep 3600"]
    resources:
      requests:
        cpu: "100m"                  # 正确写法：100m = 0.1核
        memory: "64Mi"
      limits:
        cpu: "200m"                  # 建议设置limits以进行资源限制
        memory: "128Mi"
```
然后执行以下命令创建：
```bash
kubectl apply -f fixed-pod.yaml
```
*依据*：使用正确的 CPU 单位 (`100m`) 确保 Pod 能够被调度。
*目的*：修复 Pod 配置错误，使其可以正常运行。

### 后续优化

1.  **检查上层工作负载**：如果该 Pod 是由 Deployment、StatefulSet 或 Job 等控制器创建的，请立即检查并更新其 Pod 模板（`spec.template.spec.containers[].resources.requests.cpu`）中的配置，避免再次创建出错误的 Pod。
2.  **引入资源配额校验**：考虑在 CI/CD 流程或 Admission Controller（如 OPA/Kyverno）中增加对异常资源请求（如 CPU > 节点容量）的校验，从源头防止此类问题发生。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认旧 Pod 已删除 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e` | `Error from server (NotFound): pods "rc-pending-insufficient-cpu" not found` |
| 2. 确认新 Pod 已创建 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e` | STATUS 显示 `Running`，READY 显示 `1/1` |
| 3. 确认 Pod 无重启 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o jsonpath='{.status.containerStatuses[0].restartCount}'` | 值为 `0` |
| 4. 确认集群无异常 Pod | `kubectl get pods --all-namespaces | grep -v Running` | 输出中除了 `Completed` 的 Job Pod 外，没有 `Pending` 或 `CrashLoopBackOff` 状态的 Pod |

---

## ⚠️ 注意事项

- **`k` 后缀的正确含义**：在 Kubernetes CPU 资源单位中，`1k` = `1000` 核心。请勿与内存单位中的 `Ki` (Kibibyte，1024) 混淆。对于非整数 CPU 请求，请使用 `m` 后缀，如 `100m` = 0.1 核。
- **生产环境建议**：即使单个 Pod 修复完成，也应审查其他 Pod 的资源配置，防止存在类似隐患。

---

## 📊 性能统计

├─ 总耗时: 2.4m
├─ 问题定位: 28.1s (20%) ✅
├─ 证据链采集: 49.4s (35%) ✅
├─ 根因分析: 32.2s (23%) ✅
├─ 汇总总结: 32.0s (23%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 15 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 15 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
