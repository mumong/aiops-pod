======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: cbeb796abf5d4f4c]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先查看当前所有 Pod 的状态，了解集群中是否存在异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 发现一个 Pending 状态的异常 Pod。让我进一步查看详情。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  13m                    default-scheduler  0/3 nodes are ava
   💭 [问题定位] 现在让我获取这个 Pod 的详细信息，以及查看节点资源情况。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                          READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-cpu   0/1     Pending   0          13m   <none>   <
   💭 [问题定位] 现在查看节点状态，确认集群节点资源情况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 让我看一下这个 Pod 的 YAML 确认它的资源请求，以及检查节点的 CPU 容量。
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:59:10Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizer
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node1
关键诊断行:
                    volumes.kubernetes.io/controller-managed-attach-detach: true
Taints:             <none>
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: master
关键诊断行:
                    volumes.kubernetes.io/controller-managed-attach-detach: true
Taints:             <none>
   💭 [问题定位] 注意到这个 Pod 使用了 `imagePullPolicy=Never`，而 busybox:1.36 镜像可能没有拉取到。不过核心问题是调度失败。让我看看这个 Pod 的资源请求详情。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubernetes_tabular_query
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node2
关键诊断行:
                    volumes.kubernetes.io/controller-managed-attach-detach: true
Taints:             <none>
   💭 [问题定位] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 表格摘要: rows=3 abnormal=0 status_counts={}
NAME     CPU_Alloc   CPU_Cap   MEM_Alloc    MEM_Cap      PODS_Alloc
# 样例行
master   12          12        32758084Ki   32860484Ki   110
   💭 [问题定位] 每个节点有 12 个 CPU，但所有 3 个节点都显示 `Insufficient cpu`。让我看看这个 Pod 到底请求了多少 CPU。
   💭 [问题定位] 调用工具: kubernetes_jq_query
   💭 [问题定位] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=243 lines=15
Executing jq query for pods...
{
  "name": "rc-pending-insufficient-cpu",
  "containers": [
    {
      "name": "app",
      "resources": {
        "re
   💭 [问题定位] 找到根因了！Pod 的 CPU requests 设置为 `"100k"`（100,000 个 CPU），而集群每个节点只有 12 个 CPU，所以没有任何节点能调度。

现在来看看是否存在其他异常对象。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   ✅ [问题定位] 完成 (30.7s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'Pod CPU requests 配置过大导致无法调度', 'probability': '高', 'reason': 'Pod 的 CPU requests 设置为 100k，而每个节点仅有 12 个 CPU，0/3 节点可用'}]
   entities=[{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}]
   reasoning=集群中存在一个当前仍异常的 Pod rc-pending-insufficient-cpu（aiops-e2e 命名空间），状态为 Pending。Events 显示 FailedScheduling 且原因为 '3 Insufficient cpu'。进一步检查发现该 Pod 的 CPU requests 设置为 "100k"（100,000 个 CPU），而集群 3 个节点每个只有 12 个 CPU，没有任何节点能满足调度需求。所有 3 个节点均为 Ready 状态且无 Taints，根因是 Pod 自身资源请求配置错误导致调度失败。根据五层模型，PendingUnschedulable 且根因为资源不足/调度失败归为 L1。pod_status_keyword=Pending，pod_abnormal_type=PendingUnschedulable，status_category=scheduling。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "调度/资源不足", "confidence": 1.0, "reasoning": "集群中存在一个当前仍异常的 Pod rc-pending-insufficient-cpu（aiops-e2e 命名空间），状态为 Pending。Events 显示 FailedScheduling 且原因为 '3 Insufficient cpu'。进一步检查发现该 Pod 的 CPU requests 设置为 \"100k\"（100,000 个 CPU），而集群 3 个节点每个只有 12 个 CPU，没有任何节点能满足调度需求。所有 3 个节点均为 Ready 状态且无 Taints，根因是 Pod 自身资源请求配置错误导致调度失败。根据五层模型，PendingUnschedulable 且根因为资源不足/调度失败归为 L1。pod_status_keyword=Pending，pod_abnormal_type=PendingUnschedulable，status_category=scheduling。", "abnormal_pods": [{"name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}], "possible_scenarios": [{"scenario": "Pod CPU requests 配置过大导致无法调度", "probability": "高", "reason": "Pod 的 CPU requests 设置为 100k，而每个节点仅有 12 个 CPU，0/3 节点可用"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-insufficient-cpu                         0/1     Pending     0              13m     <none>           <none>   <none>           <none>            app=rc-pending-insufficient-cpu,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/cbeb796abf5d4f4c/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/cbeb796abf5d4f4c/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/cbeb796abf5d4f4c/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 100%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，上游已经完成了定位分析，我的任务是执行既有 evidence_plan 中的工具调用，采集当前环境证据。让我开始执行。

## 执行证据计划

首先，获取 runbook 参考（reference 级别），同时启动 critical 级别的 Pod describe 和 YAML 检查：
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
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
   💭 [证据链采集] 现在执行节点容量验证：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAME     CPU_ALLOCATABLE   MEM_ALLOCATABLE\nmaster   12                32758084Ki\nnode1    12                32758076Ki\nnode2    12                32758080Ki\n", "stderr
   💭 [证据链采集] 好的，所有证据已采集完成。下面是证据总结：

---

## ✅ 已采集证据总结

### Critical 证据（3项）

| # | 证据项 | 结果 |
|---|--------|------|
| 1 | **Pod describe** — `rc-pending-insufficient-cpu` | ✅ **Pod 状态 Pending**，Events 显示：`0/3 nodes are available: 3 Insufficient cpu`。QoS Class: Burstable。无 nodeSelector，Node 和 IP 均为 `<none>`。 |
| 2 | **Pod YAML** — `rc-pending-insufficient-cpu` | ✅ **`nodeName: None`**，`phase: Pending`。PodScheduled condition=`False`，reason=`Unschedulable`，message=`0/3 nodes are available: 3 Insufficient cpu`。Confirm container resources in detailed view needed for CPU request value. |
| 3 | **节点可分配 CPU 容量** | ✅ 三个节点（master/node1/node2）**每个仅可分配 12 个 CPU**，远小于 Pod 的 CPU requests（100k/100,000 个 CPU）。 |

### Reference 证据（1项）
- **Runbook 已获取** — `pod-pending-unschedulable.md`，确认根因分流规则：`FailedScheduling + Insufficient cpu` → **资源不足**，置信度**高**。

---

## 🔍 分析结论

**根因：Pod `rc-pending-insufficient-cpu` 的 CPU requests 被设置为 `100k`（100,000 个 CPU），而集群 3 个节点每个仅有 12 个可分配 CPU，没有任何节点能满足调度需求。**

**完整证据链：**
1. `FailedScheduling` 原文：「0/3 nodes are available: 3 Insufficient cpu」— 明确指向 CPU 资源不足
2. Pod 未绑定任何节点（`nodeName: None`），PodScheduled condition=False
3. 3 个节点 CPU 可分配量分别为 12/12/12，所有节点均远小于 100k
4. 所有节点 Ready 且无 Taints，不存在调度约束或节点健康问题

**建议修复**：将 Pod 的 `resources.requests.cpu` 从 `100k` 改为合理值（如 `100m` 或 `1`），使其小于任意节点的可分配 CPU 容量。
   ✅ [证据链采集] 完成 (24.1s)
   📤 → 下游数据: evidence_items=14/14
   evidence_analysis={"evidence_plan":[{"id":"g1-pod-describe","description":"Describe the pending pod rc-pending-insufficient-cpu in aiops-e2e to verify current status, events and scheduling details","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e"},"purpose":"验证 Pod 当前状态、Pending 原因、FailedScheduling 事件及关键调度错误原文","evidence_type":"pod_status_and_events","target_scope":"main_abnormal_group","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-pod-yaml-verify","description":"Get the full YAML of the pod to verify CPU requests value (100k) and all resource specs","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e"},"purpose":"验证 Pod spec 中 containers[].resources.requests.cpu 是否为 100k 及完整资源配置","evidence_type":"pod_resource_spec","target_scope":"main_abnormal_group","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g1-node-capacity","description":"Check all 3 node capacities to verify no node can satisfy 100k CPU request","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o custom-columns=NAME:.metadata.name,CPU_ALLOCATABLE:.status.allocatable.cpu,MEM_ALLOCATABLE:.status.allocatable.memory","tool_args":{},"purpose":"验证集群 3 个节点的可分配 CPU 资源，确认是否所有节点均小于 100k 导致调度失败","evidence_type":"node_resource_capacity","target_scope":"main_abnormal_group","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-fetch-runbook","description":"Fetch runbook for pod-pending-unschedulable as reference context","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","tool_args":{"runbook_name":"pod-pending-unschedulable.md"},"purpose":"获取已匹配的 runbook 参考上下文","evidence_type":"reference","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod PendingUnschedulable / 调度失败\n\n> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | Pending，且 Events 含 `FailedScheduling` |\n| 资源不足 | `Insufficient cpu/memory/ephemeral-storage`、`Too many pods` |\n| 调度约束 | nodeSelector/affinity 不匹配、节点 taint 未被 toleration 容忍 |\n| 存储前置条件 | `pod has unbound immediate PersistentVolumeClaims` 应切换到 pod-volume-mount-failed |\n| 节点状态 | Node NotReady/Unknown、SchedulingDisabled、Unschedulable 会导致无可用调度节点 |\n\n## 根因分流\n- 资源不足: FailedScheduling 原文含 Insufficient cpu/memory/ephemeral-storage、Too many pods。\n- hostPort 冲突: 原文含 `didn't have free ports for the requested pod ports`，说明目标节点端口已被占用。\n- Taint/Toleration 不匹配: 原文含 `had untolerated taint`，必须检查 Pod tolerations 和 Node taints。\n- nodeSelector / nodeAffinity / podAffinity 不匹配: 原文含 `didn't match Pod's node affinity/selector` 或 affinity/anti-affinity。\n- PVC 未绑定: 原文含 `unbound immediate PersistentVolumeClaims`，根因在存储绑定而不是调度资源。\n- 节点不可调度: Node Ready=False/Unknown、SchedulingDisabled、`node.kubernetes.io/not-ready` 或 `node.kubernetes.io/unreachable`。\n- 镜像、挂载、容器启动错误不会表现为 FailedScheduling；如果 Pod 已绑定 nodeName，应切换到对应 runbook。\n\n## 诊断流程\n\n### Step 1: 确认 Pod 调度失败事件\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n关注 Events 中的 `FailedScheduling` 原文。\n\n### Step 2: 检查 Pod 调度约束\n```bash\nkubectl get pod <pod-name> -n <namespace> -o yaml\n```\n关注: spec.nodeName 是否为空、nodeSelector、affinity、tolerations、topologySpreadConstraints、schedulerName、priorityClassName、resource requests、hostNetwork/hostPort。\n\n### Step 3: 检查节点状态和可调度性\n```bash\nkubectl get nodes -o wide\n```\n关注: STATUS 列是否有 NotReady/Unknown，AGE 判断是否新节点\n\n### Step 4: 检查候选节点详情\n```bash\nkubectl describe node <node-name>\n```\n重点关注:\n- `Conditions` 部分: Ready=False/Unknown 的 reason 和 message\n- `Taints` 部分: 是否有 NoSchedule/NoExecute taint\n- `Allocatable` vs `Capacity`: 资源是否耗尽\n- `Non-terminated Pods`: 节点上运行的 Pod 数量\n\n### Step 5: 检查 PVC 状态（如果 FailedScheduling 指向 PVC）\n```bash\nkubectl get pvc -n <namespace>\nkubectl describe pvc <pvc> -n <namespace>\n```\n关注: Pending、StorageClass、volumeBindingMode、ProvisioningFailed。\n\n### Step 6: 检查 Ready 条件详情\n```bash\nkubectl get node <node-name> -o jsonpath='{.status.conditions[?(@.type==\"Ready\")]}' | python3 -m json.tool\n```\n关注: status, reason, message, lastHeartbeatTime\n\n### Step 7: 检查节点事件\n```bash\nkubectl get events -A --field-selector involvedObject.kind=Node,involvedObject.name=<node-name> --sort-by='.lastTimestamp'\n```\n关注: NodeNotReady、NodeNotSchedulable、PLEG unhealthy 等事件\n\n### Step 8: 检查受影响的 Pending Pod\n```bash\nkubectl get pods -A --field-selector status.phase=Pending | head -20\n```\n\n## 判定规则\n\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| FailedScheduling + Insufficient cpu/memory | 资源不足导致 Pod Pending | 高 |\n| FailedScheduling + Too many pods | 节点 Pod 数量上限导致 Pending | 高 |\n| FailedScheduling + didn't have free ports for the requested pod ports | hostPort 端口冲突导致 Pending | 高 |\n| FailedScheduling + had untolerated taint | taint/toleration 不匹配 | 高 |\n| FailedScheduling + node(s) didn't match node selector/affinity | 调度约束不匹配 | 高 |\n| FailedScheduling + pod has unbound immediate PersistentVolumeClaims | PVC 未绑定，应切换 VolumeMountFailed/PVC 分支 | 高 |\n| 所有候选 Node NotReady/Unschedulable | 无可用调度节点 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/cbeb796abf5d4f4c/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/cbeb796abf5d4f4c/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/cbeb796abf5d4f4c/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  13m                    default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  3m50s (x2 over 8m50s)  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nName:             rc-pending-insufficient-cpu\nLabels:           app=rc-pending-insufficient-cpu\nPod 关键区块:\nQoS Class: Burstable\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-26zhx:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  13m                    default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  3m50s (x2 over 8m50s)  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/cbeb796abf5d4f4c/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/cbeb796abf5d4f4c/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/cbeb796abf5d4f4c/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:59:10Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-insufficient-cpu, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nvolumes:\n- {\"name\": \"kube-api-access-26zhx\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/cbeb796abf5d4f4c/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/cbeb796abf5d4f4c/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/cbeb796abf5d4f4c/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAME     CPU_ALLOCATABLE   MEM_ALLOCATABLE\\nmaster   12                32758084Ki\\nnode1    12                32758076Ki\\nnode2    12                32758080Ki\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/cbeb796abf5d4f4c/tools/004-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/cbeb796abf5d4f4c/tools/004-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/cbeb796abf5d4f4c/tools/004-evidence-run_bash_command.summary.txt"}],"llm_analysis":"好的，所有证据已采集完成。下面是证据总结：\n\n---\n\n## ✅ 已采集证据总结\n\n### Critical 证据（3项）\n\n| # | 证据项 | 结果 |\n|---|--------|------|\n| 1 | **Pod describe** — `rc-pending-insufficient-cpu` | ✅ **Pod 状态 Pending**，Events 显示：`0/3 nodes are available: 3 Insufficient cpu`。QoS Class: Burstable。无 nodeSelector，Node 和 IP 均为 `<none>`。 |\n| 2 | **Pod YAML** — `rc-pending-insufficient-cpu` | ✅ **`nodeName: None`**，`phase: Pending`。PodScheduled condition=`False`，reason=`Unschedulable`，message=`0/3 nodes are available: 3 Insufficient cpu`。Confirm container resources in detailed view needed for CPU request value. |\n| 3 | **节点可分配 CPU 容量** | ✅ 三个节点（master/node1/node2）**每个仅可分配 12 个 CPU**，远小于 Pod 的 CPU requests（100k/100,000 个 CPU）。 |\n\n### Reference 证据（1项）\n- **Runbook 已获取** — `pod-pending-unschedulable.md`，确认根因分流规则：`FailedScheduling + Insufficient cpu` → **资源不足**，置信度**高**。\n\n---\n\n## 🔍 分析结论\n\n**根因：Pod `rc-pending-insufficient-cpu` 的 CPU requests 被设置为 `100k`（100,000 个 CPU），而集群 3 个节点每个仅有 12 个可分配 CPU，没有任何节点能满足调度需求。**\n\n**完整证据链：**\n1. `FailedScheduling` 原文：「0/3 nodes are available: 3 Insufficient cpu」— 明确指向 CPU 资源不足\n2. Pod 未绑定任何节点（`nodeName: None`），PodScheduled condition=False\n3. 3 个节点 CPU 可分配量分别为 12/12/12，所有节点均远小于 100k\n4. 所有节点 Ready 且无 Taints，不存在调度约束或节点健康问题\n\n**建议修复**：将 Pod 的 `resources.requests.cpu` 从 `100k` 改为合理值（如 `100m` 或 `1`），使其小于任意节点的可分配 CPU 容量。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 13/13 项，完整度 100%；实际执行工具 13 个，匹配计划 4 个，未规划证据 9 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":13,"environment_evidence_collected":13,"environment_evidence_completeness":1.0,"executed_tool_count":13,"matched_tool_count":4,"unplanned_tool_count":9,"evidence_inventory":[{"id":"g1-pod-describe","description":"Describe the pending pod rc-pending-insufficient-cpu in aiops-e2e to verify current status, events and scheduling details","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","purpose":"验证 Pod 当前状态、Pending 原因、FailedScheduling 事件及关键调度错误原文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-pod-yaml-verify","description":"Get the full YAML of the pod to verify CPU requests value (100k) and all resource specs","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","purpose":"验证 Pod spec 中 containers[].resources.requests.cpu 是否为 100k 及完整资源配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-node-capacity","description":"Check all 3 node capacities to verify no node can satisfy 100k CPU request","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o custom-columns=NAME:.metadata.name,CPU_ALLOCATABLE:.status.allocatable.cpu,MEM_ALLOCATABLE:.status.allocatable.memory","purpose":"验证集群 3 个节点的可分配 CPU 资源，确认是否所有节点均小于 100k 导致调度失败","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-fetch-runbook","description":"Fetch runbook for pod-pending-unschedulable as reference context","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","purpose":"获取已匹配的 runbook 参考上下文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_8","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_9","description":"上游已验证工具结果: kubernetes_tabular_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_10","description":"上游已验证工具结果: kubernetes_jq_query","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | g1-pod-describe | critical | ✅ | kubectl_describe | Describe the pending pod rc-pending-insuffici... | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` |
   | g1-pod-yaml-v... | critical | ✅ | kubectl_get_yaml | Get the full YAML of the pod to verify CPU re... | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml` |
   | g1-node-capacity | critical | ✅ | run_bash_command | Check all 3 node capacities to verify no node... | `kubectl get nodes -o custom-columns=NAME:.metadata.name,CPU_ALLOCATABLE:.stat...` |
   | g1-fetch-runbook | reference | ✅ | fetch_runbook | Fetch runbook for pod-pending-unschedulable a... | `fetch_runbook pod-pending-unschedulable.md` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (56.5s)
   📤 → 下游数据: root_cause=命名空间 aiops-e2e 中 Pod rc-pending-insufficient-cpu 处于 Pending 状态的根本原因是其 resources.requests.cpu 被错误设置为 '100k'（即 100,000 个 CPU），但集群 3 个节点（master、node1、node2）的 CPU 可分配量均为 12 个（证据 e3, e4）。调度器 Events 明确报告 '0/3 nodes are available: 3 Insufficient cpu'（证据 e1），PodScheduled condition=False（证据 e2）。所有节点均为 Ready 且无 Taints（证据 e5, e6），排除了节点健康或调度约束问题。这是一个 Pod 配置错误导致的资源请求溢出问题。
   confidence=100%
   causal_chain={"root_cause": "Pod rc-pending-insufficient-cpu 的 CPU requests 被配置为 100k（100,000 个 CPU），远超集群任一节点（每个节点仅 12 个 CPU）的容量。", "propagation": "调度器尝试将 Pod 分配到节点时，逐节点检查 CPU 资源是否满足 100k 的请求，所有 3 个节点均远不达标，报告 Insufficient cpu；抢占逻辑也因无符合条件的 victim Pod 而失败。Pod 持续处于 Pending 状态。", "direct_cause": "所有 3 个节点均为 Ready 且无 Taints，但 CPU 可分配量（12）小于 Pod 请求的 CPU 数量（100k），调度器无法找到任何可用的候选节点。", "manifestation": "用户可见 Pod rc-pending-insufficient-cpu 长时间处于 Pending 状态，kubectl 输出显示 <none> 的 Node 和 IP，Events 不断重试 FailedScheduling。"}
   rca_analysis={"phenomenon": "命名空间 aiops-e2e 中的 Pod rc-pending-insufficient-cpu 处于 Pending 状态，Events 持续报告 FailedScheduling 错误，具体原因为 '3 Insufficient cpu'，Pod 未被调度到任何节点。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod rc-pending-insufficient-cpu 当前状态为 Pending，Events 显示 FailedScheduling：'0/3 nodes are available: 3 Insufficient cpu'", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml", "content": "Pod YAML 中 nodeName: None, phase: Pending, PodScheduled condition=False, reason=Unschedulable", "reliability": "高"}, {"id": "e3", "source": "kubernetes_jq_query", "content": "Pod 容器 'app' 的 resources.requests.cpu 设置为 '100k'（100,000 个 CPU），resources.requests.memory 为 '64Mi'", "reliability": "高"}, {"id": "e4", "source": "kubernetes_tabular_query", "content": "所有 3 个节点（master、node1、node2）的 CPU_Alloc 均为 12，即每个节点只有 12 个可分配 CPU 核心", "reliability": "高"}, {"id": "e5", "source": "kubectl_get_by_kind_in_cluster", "content": "3 个节点均处于 Ready 状态，无异常", "reliability": "高"}, {"id": "e6", "source": "kubectl_describe (nodes)", "content": "节点 master、node1、node2 均无 Taints（Taints: <none>）", "reliability": "高"}, {"id": "e7", "source": "fetch_runbook", "content": "Runbook 确认 FailedScheduling + Insufficient cpu 指向资源不足场景，置信度高", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedScheduling 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.", "interpretation": "调度器明确报告所有节点均 CPU 不足，且没有抢占候选 Pod，进一步确认是绝对资源不足以满足请求，而非被其他 Pod 占满可抢占资源。"}, {"evidence_id": "e2", "raw_data": "nodeName: None, phase: Pending, condition: PodScheduled=False, reason: Unschedulable", "interpretation": "Pod 从未被绑定到任何节点，当前调度失败直接导致无法进入 Running 状态。"}, {"evidence_id": "e3", "raw_data": "resources.requests.cpu = \"100k\"", "interpretation": "Pod 的 CPU 请求被设置为 100k（即 100,000 个 CPU 核心），这是一个极不合理的配置值。正常 Pod 请求通常为 0.5、1、2 个 CPU，100k 远超物理机能力。"}, {"evidence_id": "e4", "raw_data": "master: CPU_Alloc=12, node1: CPU_Alloc=12, node2: CPU_Alloc=12", "interpretation": "集群中 3 个节点的 CPU 可分配总量合计为 36 个核心，远低于 Pod 请求的 100,000 个核心，没有任何一个节点可以满足调度条件。"}, {"evidence_id": "e5", "raw_data": "rows=3, abnormal=0, status_counts={\"Ready\": 3}", "interpretation": "集群节点健康状态正常，排除了节点故障导致不可调度的可能性。"}, {"evidence_id": "e6", "raw_data": "Taints: <none> (for all 3 nodes)", "interpretation": "节点无任何 Taint，排斥了因 taint/toleration 不匹配导致调度失败的场景。"}, {"evidence_id": "e7", "raw_data": "Runbook 判定规则：FailedScheduling + Insufficient cpu → 资源不足导致 Pod Pending（置信度高）", "interpretation": "Runbook 也验证了当前现象完全匹配资源不足的调度失败模式，无需进入其他分支排查。"}], "causal_chain": {"root_cause": "Pod rc-pending-insufficient-cpu 的 CPU requests 被配置为 100k（100,000 个 CPU），远超集群任一节点（每个节点仅 12 个 CPU）的容量。", "propagation": "调度器尝试将 Pod 分配到节点时，逐节点检查 CPU 资源是否满足 100k 的请求，所有 3 个节点均远不达标，报告 Insufficient cpu；抢占逻辑也因无符合条件的 victim Pod 而失败。Pod 持续处于 Pending 状态。", "direct_cause": "所有 3 个节点均为 Ready 且无 Taints，但 CPU 可分配量（12）小于 Pod 请求的 CPU 数量（100k），调度器无法找到任何可用的候选节点。", "manifestation": "用户可见 Pod rc-pending-insufficient-cpu 长时间处于 Pending 状态，kubectl 输出显示 <none> 的 Node 和 IP，Events 不断重试 FailedScheduling。"}, "root_cause": "命名空间 aiops-e2e 中 Pod rc-pending-insufficient-cpu 处于 Pending 状态的根本原因是其 resources.requests.cpu 被错误设置为 '100k'（即 100,000 个 CPU），但集群 3 个节点（master、node1、node2）的 CPU 可分配量均为 12 个（证据 e3, e4）。调度器 Events 明确报告 '0/3 nodes are available: 3 Insufficient cpu'（证据 e1），PodScheduled condition=False（证据 e2）。所有节点均为 Ready 且无 Taints（证据 e5, e6），排除了节点健康或调度约束问题。这是一个 Pod 配置错误导致的资源请求溢出问题。", "root_cause_summary": "命名空间 aiops-e2e 中 Pod rc-pending-insufficient-cpu 处于 Pending 状态的根本原因是其 resources.requests.cpu 被错误设置为 '100k'（即 100,000 个 CPU），但集群 3 个节点（master、node1、node2）的 CPU 可分配量均为 12 个（证据 e3, e4）。调度器 Events 明确报告 '0/3 nodes are available: 3 Insufficient cpu'（证据 e1），PodScheduled condition=False（证据 e2）。所有节点均为 Ready 且无 Taints（证据 e5, e6），排除了节点健康或调度约束问题。这是一个 Pod 配置错误导致的资源请求溢出问题。", "confidence": 1.0, "confidence_reason": "证据链完整且高度一致：调度器 Events（e1）与节点容量数据（e4）直接匹配，Pod YAML（e3）确认了异常值，节点状态（e5, e6）排除了其他常见场景。根因明确无歧义，置信度达到最高。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "节点 Taint/Toleration 不匹配导致调度失败", "probability": "low", "reason": "已通过证据 e6 排除：所有 3 个节点 Taints 均为 <none>，Pod 也无 Tolerations 特殊要求。"}, {"cause": "节点 NotReady 或不可用", "probability": "low", "reason": "已通过证据 e5 排除：3 个节点均为 Ready 状态，无异常。"}, {"cause": "PVC 未绑定导致 Pod 无法调度", "probability": "low", "reason": "Pod YAML（e2）中未引用任何 PVC，Events 也未报告 PVC 相关错误。"}, {"cause": "节点资源被其他 Pod 占满但可抢占", "probability": "low", "reason": "调度器已尝试抢占并报告 'No preemption victims found'（e1），说明是绝对资源不足而非被占满。且 100k 远大于节点 12 的总量，即使空节点也无法满足。"}], "limitations": "证据未包含 Pod 的完整 YAML 原始内容，但关键字段（resources.requests.cpu）已通过 jq 查询确认，可靠性高。未采集 Pod QoS 类别的显式确认，但 Burstable 对根因无影响。整体证据充分，无重大缺失。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 命名空间 aiops-e2e 中 Pod rc-pending-insufficient-cpu 处于 Pending 状态的根本原因是其 resources.requests.cpu 被错误设置为 '100k'（即 100,000 个 CPU），但集群 3 个节点（master、node1、nod...
   置信度: 100%
   🔗 因果链:
     根本原因: Pod rc-pending-insufficient-cpu 的 CPU requests 被配置为 100k（100,000 个 CPU），远超集群任一节点（每个节点仅 12 个 CPU）的容量。
     传导机制: 调度器尝试将 Pod 分配到节点时，逐节点检查 CPU 资源是否满足 100k 的请求，所有 3 个节点均远不达标，报告 Insufficient cpu；抢占逻辑也因无符合条件的 victim Pod 而失败。Pod 持续处于 Pending 状态。
     最终表现: 用户可见 Pod rc-pending-insufficient-cpu 长时间处于 Pending 状态，kubectl 输出显示 <none> 的 Node 和 IP，Events 不断重试 FailedScheduling。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (2m 19.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 94 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 4m 10.7s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
报告生成失败: peer closed connection without sending complete message body (incomplete chunked read)

---

## 📊 性能统计

├─ 总耗时: 4.2m
├─ 问题定位: 30.7s (12%) ✅
├─ 证据链采集: 24.1s (10%) ✅
├─ 根因分析: 56.5s (23%) ✅
├─ 汇总总结: 139.3s (56%) ✅
├─ LLM 调用: 3 次
└─ 工具调用: 16 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 16 次
- **LLM 调用**: 3 次


======================================================================
✅ 诊断完成!
======================================================================
