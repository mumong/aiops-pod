======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 7c401f34315b4e49]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，让我先扫描全局 Pod 状态，看看当前集群中有哪些异常。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 扫描到 1 个异常 Pod。让我进一步看看它的详情。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                             READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-memory   0/1     Pending   0          31m   <non
   💭 [问题定位] 这个 Pod 处于 Pending 状态且没有绑定到节点，同时 label 上标记了 `pod_abnormal_type=PendingUnschedulable`。让我获取该 Pod 的详细事件，确认调度失败原因。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-memory
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  31m               default-scheduler  0/3 nodes are avail
   💭 [问题定位] 确认了调度失败原因是"内存不足"。现在这个场景明确匹配 `pod-pending-unschedulable.md` runbook，让我获取参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 好的，信息已经足够了。现在进行完整的定位分析。

---

## 定位分析结果

### 全局 Pod 扫描结果
集群共 65 个 Pod，其中 **59 个 Running（正常）**，**1 个异常**。

### 异常 Pod 清单

| Pod | 命名空间 | 状态 | 年龄 |
|-----|---------|------|------|
| `rc-pending-insufficient-memory` | `aiops-e2e` | **Pending** | 31m |

### 异常状态分析

**Pod:** `rc-pending-insufficient-memory`（aiops-e2e 命名空间）
- **状态:** Pending，未绑定到任何节点（nodeName 为空）
- **Events:** `FailedScheduling` — `0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.`
- **Pod 类型:** Burstable QoS，requests 内存需求导致集群中 3 个节点均无法满足
- **镜像:** `busybox:1.36`，启动命令 `sleep 3600`

### 异常分类

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **derived_layer** | L1 |
| **layers** | ["L1"] |
| **layer_name** | 调度资源不足 |
| **pod_status_keyword** | Pending |
| **pod_abnormal_type** | PendingUnschedulable |
| **status_category** | scheduling |

### 根因分析

**根本原因：集群所有 3 个 Worker 节点均内存不足（Insufficient memory），无法调度该 Pod。**

具体来说：
1. 该 Pod 申请了内存在各节点 `Allocatable` 剩余之外
2. 调度器尝试抢占（preemption），但 3 个节点均找不到可驱逐的低优先级 Pod
3. 没有任何调度约束（无 nodeSelector、无 taint、无亲和性配置）限制节点选择，纯粹是资源不足

### 关键实体
- **异常 Pod:** `rc-pending-insufficient-memory`（aiops-e2e）
- **受影响节点:** 全部 3 个 Worker 节点（均 Insufficient memory）
- **调度器:** default-scheduler

### 可能的排查方向
1. **检查节点内存分配情况** — 查看各节点的 `Allocatable.memory` 与已分配 Pod 的内存总和
2. **检查 Pod 资源请求** — 确认该 Pod 的 `resources.requests.memory` 是否设置过高
3. **评估是否可以扩缩节点** — 增加节点或迁移负载释放内存
4. **检查是否有其他高内存占用的 Pod** — 是否集群整体内存使用率过高
   ✅ [问题定位] 完成 (23.0s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '集群节点内存资源不足', 'probability': '高', 'reason': 'FailedScheduling 明确提示 3 Insufficient memory，3个节点均无法满足 Pod 内存请求'}, {'scenario': 'Pod 资源请求设置过高', 'probability': '中', 'reason': '需进一步检查 Pod 的 resources.requests.memory 是否超出节点可用容量'}]
   entities=[{"type": "Pod", "name": "rc-pending-insufficient-memory", "namespace": "aiops-e2e"}, {"type": "Node", "name": "所有3个Worker节点", "namespace": ""}]
   reasoning=集群中存在异常 Pod rc-pending-insufficient-memory（aiops-e2e 命名空间），状态为 Pending，事件为 FailedScheduling，原因：0/3 nodes are available: 3 Insufficient memory。属典型调度资源不足问题，对应 L1 调度层。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "调度资源不足", "confidence": 0.95, "reasoning": "集群中存在异常 Pod rc-pending-insufficient-memory（aiops-e2e 命名空间），状态为 Pending，事件为 FailedScheduling，原因：0/3 nodes are available: 3 Insufficient memory。属典型调度资源不足问题，对应 L1 调度层。", "abnormal_pods": [{"name": "rc-pending-insufficient-memory", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-insufficient-memory", "namespace": "aiops-e2e"}, {"type": "Node", "name": "所有3个Worker节点", "namespace": ""}], "possible_scenarios": [{"scenario": "集群节点内存资源不足", "probability": "高", "reason": "FailedScheduling 明确提示 3 Insufficient memory，3个节点均无法满足 Pod 内存请求"}, {"scenario": "Pod 资源请求设置过高", "probability": "中", "reason": "需进一步检查 Pod 的 resources.requests.memory 是否超出节点可用容量"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-memory"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-memory"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-insufficient-memory                      0/1     Pending     0              31m     <none>           <none>   <none>           <none>            app=rc-pending-insufficient-memory,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，开始按照既有 evidence_plan 执行采证。先获取 runbook 参考，同时开始关键证据采集。
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
name: rc-pending-insufficient-memory
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  31m                  default-scheduler  0/3 nodes are av
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-insufficient-memory
namespace: aiops-e2e
creationTimestamp: 2026-05-21T08:00:52Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finali
   💭 [证据链采集] 很好！Pod 的 describe 和 YAML 已采集到关键信息。继续执行节点资源和 Prometheus 查询。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=1 abnormal=1 status_counts={'Pending': 1}
NAME                             READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS G
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"name\": \"master\",\n  \"allocatable\": {\n    \"cpu\": \"12\",\n    \"ephemeral-storage\": \"568259694471\",\n    \"hugepages-1Gi\": \"0\",\n    \"hugepages-2Mi\":
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"instance":"10.2.0.49:9100"},"value":[1779352367.026,"0.9117947043737284"]},{"metric":{"instance":"10.2.0.50:9100"},"value":[1779
   💭 [证据链采集] 现在让我再查一下 Pod 的资源请求（requests）具体值，刚才的 YAML 输出来看这个 Pod 没有显式设置 resources.requests，但仍然被提示 Insufficient memory，让我确认一下细节。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"requests\": {\n    \"cpu\": \"50m\",\n    \"memory\": \"100000Gi\"\n  }\n}\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] 找到根本原因了！让我再查一下节点的实际总内存来做个对比。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"name\": \"master\",\n  \"memory_capacity\": \"32860484Ki\",\n  \"memory_allocatable\": \"32758084Ki\"\n}\n{\n  \"name\": \"node1\",\n  \"memory_capacity\": \"328604
   💭 [证据链采集] 全部证据已采集完毕，以下是结论：

---

## 📋 证据采集结论

### ✅ 已采集的关键证据

| # | 证据 | 来源 | 结论 |
|---|------|------|------|
| **e1** | FailedScheduling 事件原文 | `kubectl describe pod` | ✅ 明确：`0/3 nodes are available: 3 Insufficient memory`，3 个 Worker 节点全部内存不足 |
| **e2** | Pod spec resources.requests | `kubectl_get_yaml` + json 查询 | ✅ **Pod 请求 memory=100000Gi（100TB）**，极度异常，不可能被任何节点满足 |
| **e3** | 3 个节点的可分配内存 | `kubectl get nodes -o json` | ✅ 每个节点可分配约 **32Gi**（约 31.2 GiB），而 Pod 请求 100000Gi |
| **e4** | 节点内存可用比例 (Prometheus) | PromQL 即时查询 | ✅ master=91.2%, node1=83.4%, node2=53.5% — 节点均正常运行、内存充足 |
| **e5** | aiops-e2e 命名空间 Pod 状态 | `kubectl get pod -n aiops-e2e` | ✅ 仅此一个 Pod 异常（Pending），无其他异常 |

### 🔍 根因分析

**根本原因：Pod `rc-pending-insufficient-memory` 的资源请求量异常**

- Pod `spec.containers[0].resources.requests.memory = **100000Gi**（约 100 TB）
- 而集群中每个 Worker 节点的可分配内存仅约 **32Gi**
- 3 个节点全部 Ready 且健康，但无法满足这个离谱的内存请求
- Prometheus 数据显示节点内存可用比例高达 53%~91%，说明集群资源本身是充足的

**这很可能是 E2E 测试构造的异常场景**——人为将 Pod 内存请求设置为远超集群容量的值来触发调度失败。

### ❌ 冲突/负向证据
- 无。所有工具调用均成功返回，无 NotFound/空事件。

### ⚠️ 建议修复方案（仅供参考，不执行）
- 将 Pod 的 `resources.requests.memory` 修改为合理的值（如 128Mi、256Mi）
- 或直接删除重建该 Pod（如为测试用途）
   ✅ [证据链采集] 完成 (27.4s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证异常Pod rc-pending-insufficient-memory的当前状态和事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-memory -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-insufficient-memory","namespace":"aiops-e2e"},"purpose":"验证FailedScheduling事件原文确认Insufficient memory原因","evidence_type":"event","target_scope":"Pod/aiops-e2e/rc-pending-insufficient-memory","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"查看Pod YAML中的资源请求配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-memory -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-insufficient-memory","namespace":"aiops-e2e"},"purpose":"检查Pod的resources.requests.memory和resources.requests.cpu确认资源请求值","evidence_type":"config","target_scope":"Pod/aiops-e2e/rc-pending-insufficient-memory","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"获取集群节点资源容量和已分配资源","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, allocatable: .status.allocatable, conditions: [.status.conditions[] | select(.reason==\"KubeletReady\" or .status!=\"True\")]}'","tool_args":{"command":"kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, allocatable: .status.allocatable, conditions: [.status.conditions[] | select(.reason==\"KubeletReady\" or .status!=\"True\")]}'"},"purpose":"验证3个节点的可分配内存容量和节点健康状态","evidence_type":"resource","target_scope":"Node/all","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"查看节点内存使用率(Prometheus)","level":"important","tool":"execute_prometheus_instant_query","command":"sum(node_memory_MemAvailable_bytes) by (instance) / sum(node_memory_MemTotal_bytes) by (instance)","tool_args":{"query":"sum(node_memory_MemAvailable_bytes) by (instance) / sum(node_memory_MemTotal_bytes) by (instance)"},"purpose":"验证各节点当前内存可用比例，确认资源不足的实际状况","evidence_type":"metric","target_scope":"Node/all","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5","description":"获取Pod所在命名空间所有Pod状态全面确认无其他异常","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get pod -n aiops-e2e","tool_args":{"kind":"pod","namespace":"aiops-e2e"},"purpose":"验证aiops-e2e命名空间下是否有其他异常Pod状态","evidence_type":"status_check","target_scope":"Namespace/aiops-e2e","acceptable_tools":[],"counts_for_completeness":true},{"id":"r1","description":"参考runbook确认资源不足分支的典型排查步骤","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","tool_args":{"runbook":"pod-pending-unschedulable.md"},"purpose":"将已匹配runbook作为排查参考","evidence_type":"reference","target_scope":"reference","acceptable_tools":[],"counts_for_completeness":false}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod PendingUnschedulable / 调度失败\n\n> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | Pending，且 Events 含 `FailedScheduling` |\n| 资源不足 | `Insufficient cpu/memory/ephemeral-storage`、`Too many pods` |\n| 调度约束 | nodeSelector/affinity 不匹配、节点 taint 未被 toleration 容忍 |\n| 存储前置条件 | `pod has unbound immediate PersistentVolumeClaims` 应切换到 pod-volume-mount-failed |\n| 节点状态 | Node NotReady/Unknown、SchedulingDisabled、Unschedulable 会导致无可用调度节点 |\n\n## 根因分流\n- 资源不足: FailedScheduling 原文含 Insufficient cpu/memory/ephemeral-storage、Too many pods。\n- hostPort 冲突: 原文含 `didn't have free ports for the requested pod ports`，说明目标节点端口已被占用。\n- Taint/Toleration 不匹配: 原文含 `had untolerated taint`，必须检查 Pod tolerations 和 Node taints。\n- nodeSelector / nodeAffinity / podAffinity 不匹配: 原文含 `didn't match Pod's node affinity/selector` 或 affinity/anti-affinity。\n- PVC 未绑定: 原文含 `unbound immediate PersistentVolumeClaims`，根因在存储绑定而不是调度资源。\n- 节点不可调度: Node Ready=False/Unknown、SchedulingDisabled、`node.kubernetes.io/not-ready` 或 `node.kubernetes.io/unreachable`。\n- 镜像、挂载、容器启动错误不会表现为 FailedScheduling；如果 Pod 已绑定 nodeName，应切换到对应 runbook。\n\n## 诊断流程\n\n### Step 1: 确认 Pod 调度失败事件\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n关注 Events 中的 `FailedScheduling` 原文。\n\n### Step 2: 检查 Pod 调度约束\n```bash\nkubectl get pod <pod-name> -n <namespace> -o yaml\n```\n关注: spec.nodeName 是否为空、nodeSelector、affinity、tolerations、topologySpreadConstraints、schedulerName、priorityClassName、resource requests、hostNetwork/hostPort。\n\n### Step 3: 检查节点状态和可调度性\n```bash\nkubectl get nodes -o wide\n```\n关注: STATUS 列是否有 NotReady/Unknown，AGE 判断是否新节点\n\n### Step 4: 检查候选节点详情\n```bash\nkubectl describe node <node-name>\n```\n重点关注:\n- `Conditions` 部分: Ready=False/Unknown 的 reason 和 message\n- `Taints` 部分: 是否有 NoSchedule/NoExecute taint\n- `Allocatable` vs `Capacity`: 资源是否耗尽\n- `Non-terminated Pods`: 节点上运行的 Pod 数量\n\n### Step 5: 检查 PVC 状态（如果 FailedScheduling 指向 PVC）\n```bash\nkubectl get pvc -n <namespace>\nkubectl describe pvc <pvc> -n <namespace>\n```\n关注: Pending、StorageClass、volumeBindingMode、ProvisioningFailed。\n\n### Step 6: 检查 Ready 条件详情\n```bash\nkubectl get node <node-name> -o jsonpath='{.status.conditions[?(@.type==\"Ready\")]}' | python3 -m json.tool\n```\n关注: status, reason, message, lastHeartbeatTime\n\n### Step 7: 检查节点事件\n```bash\nkubectl get events -A --field-selector involvedObject.kind=Node,involvedObject.name=<node-name> --sort-by='.lastTimestamp'\n```\n关注: NodeNotReady、NodeNotSchedulable、PLEG unhealthy 等事件\n\n### Step 8: 检查受影响的 Pending Pod\n```bash\nkubectl get pods -A --field-selector status.phase=Pending | head -20\n```\n\n## 判定规则\n\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| FailedScheduling + Insufficient cpu/memory | 资源不足导致 Pod Pending | 高 |\n| FailedScheduling + Too many pods | 节点 Pod 数量上限导致 Pending | 高 |\n| FailedScheduling + didn't have free ports for the requested pod ports | hostPort 端口冲突导致 Pending | 高 |\n| FailedScheduling + had untolerated taint | taint/toleration 不匹配 | 高 |\n| FailedScheduling + node(s) didn't match node selector/affinity | 调度约束不匹配 | 高 |\n| FailedScheduling + pod has unbound immediate PersistentVolumeClaims | PVC 未绑定，应切换 VolumeMountFailed/PVC 分支 | 高 |\n| 所有候选 Node NotReady/Unschedulable | 无可用调度节点 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-insufficient-memory\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  31m                  default-scheduler  0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  6m30s (x5 over 26m)  default-scheduler  0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nName:             rc-pending-insufficient-memory\nLabels:           app=rc-pending-insufficient-memory\nPod 关键区块:\nQoS Class: Burstable\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-c69j6:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  31m                  default-scheduler  0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  6m30s (x5 over 26m)  default-scheduler  0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-insufficient-memory\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T08:00:52Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-insufficient-memory, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nvolumes:\n- {\"name\": \"kube-api-access-c69j6\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"kubectl_get_by_kind_in_namespace 表格摘要: rows=1 abnormal=1 status_counts={'Pending': 1}\nNAME                             READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\nrc-pending-insufficient-memory   0/1     Pending   0          31m   <none>   <none>   <none>           <none>            app=rc-pending-insufficient-memory,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/004-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/004-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/004-evidence-kubectl_get_by_kind_in_namespace.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"name\\\": \\\"master\\\",\\n  \\\"allocatable\\\": {\\n    \\\"cpu\\\": \\\"12\\\",\\n    \\\"ephemeral-storage\\\": \\\"568259694471\\\",\\n    \\\"hugepages-1Gi\\\": \\\"0\\\",\\n    \\\"hugepages-2Mi\\\": \\\"0\\\",\\n    \\\"memory\\\": \\\"32758084Ki\\\",\\n    \\\"pods\\\": \\\"110\\\"\\n  },\\n  \\\"conditions\\\": [\\n    {\\n      \\\"lastHeartbeatTime\\\": \\\"2026-05-06T01:29:41Z\\\",\\n      \\\"lastTransitionTime\\\": \\\"2026-05-06T01:29:41Z\\\",\\n      \\\"message\\\": \\\"Calico is running on this node\\\",\\n      \\\"reason\\\": \\\"CalicoIsUp\\\",\\n      \\\"status\\\": \\\"False\\\",\\n      \\\"type\\\": \\\"NetworkUnavailable\\\"\\n    },\\n    {\\n      \\\"lastHeartbeatTime\\\": \\\"2026-05-21T08:31:02Z\\\",\\n      \\\"lastTransitionTime\\\": \\\"2026-03-26T06:29:35Z\\\",\\n      \\\"message\\\": \\\"kubelet has sufficient memory available\\\",\\n      \\\"reason\\\": \\\"KubeletHasSufficientMemory\\\",\\n      \\\"status\\\": \\\"False\\\",\\n      \\\"type\\\": \\\"MemoryPressure\\\"\\n    },\\n    {\\n      \\\"lastHeartbeatTime\\\": \\\"2026-05-21T08:31:02Z\\\",\\n      \\\"lastTransitionTime\\\": \\\"2026-04-27T06:40:37Z\\\",\\n      \\\"message\\\": \\\"kubelet has no disk pressure\\\",\\n      \\\"reason\\\": \\\"KubeletHasNoDiskPressure\\\",\\n      \\\"status\\\": \\\"False\\\",\\n      \\\"type\\\": \\\"DiskPressure\\\"\\n    },\\n    {\\n      \\\"lastHeartbeatTime\\\": \\\"2026-05-21T08:31:02Z\\\",\\n      \\\"lastTransitionTime\\\": \\\"2026-03-26T06:29:35Z\\\",\\n      \\\"message\\\": \\\"kubelet has sufficient PID available\\\",\\n      \\\"reason\\\": \\\"KubeletHasSufficientPID\\\",\\n      \\\"status\\\": \\\"False\\\",\\n      \\\"type\\\": \\\"PIDPressure\\\"\\n    },\\n    {\\n      \\\"lastHeartbeatTime\\\": \\\"2026-05-21T08:31:02Z\\\",\\n      \\\"lastTransitionTime\\\": \\\"2026-03-26T06:29:51Z\\\",\\n      \\\"message\\\": \\\"kubelet is posting ready status. AppArmor enabled\\\",\\n      \\\"reason\\\": \\\"KubeletReady\\\",\\n      \\\"status\\\": \\\"True\\\",\\n      \\\"type\\\": \\\"Ready\\\"\\n    }\\n  ]\\n}\\n{\\n  \\\"name\\\": \\\"node1\\\",\\n  \\\"allocatable\\\": {\\n    \\\"cpu\\\": \\\"12\\\",\\n    \\\"ephemeral-storage\\\": \\\"187795058378\\\",\\n    \\\"hugepages-1Gi\\\": \\\"0\\\",\\n    \\\"hugepages-2Mi\\\": \\\"0\\\",\\n    \\\"memory\\\": \\\"32758076Ki\\\",\\n    \\\"pods\\\": \\\"110\\\"\\n  },\\n  \\\"conditions\\\": [\\n    {\\n      \\\"lastHeartbeatTime\\\": \\\"2026-05-06T01:29:35Z\\\",\\n      \\\"lastTransitionTime\\\": \\\"2026-05-06T01:29:35Z\\\",\\n      \\\"message\\\": \\\"Calico is running on this node\\\",\\n      \\\"reason\\\": \\\"CalicoIsUp\\\",\\n      \\\"status\\\": \\\"False\\\",\\n      \\\"type\\\": \\\"NetworkUnavailable\\\"\\n    },\\n    {\\n      \\\"lastHeartbeatTime\\\": \\\"2026-05-21T08:32:10Z\\\",\\n      \\\"lastTransitionTime\\\": \\\"2026-05-12T05:53:42Z\\\",\\n      \\\"message\\\": \\\"kubelet has sufficient memory available\\\",\\n      \\\"reason\\\": \\\"KubeletHasSufficientMemory\\\",\\n      \\\"status\\\": \\\"False\\\",\\n      \\\"type\\\": \\\"MemoryPressure\\\"\\n    },\\n    {\\n      \\\"lastHeartbeatTime\\\": \\\"2026-05-21T08:32:10Z\\\",\\n      \\\"lastTransitionTime\\\": \\\"2026-05-12T05:53:42Z\\\",\\n      \\\"message\\\": \\\"kubelet has no disk pressure\\\",\\n      \\\"reason\\\": \\\"KubeletHasNoDiskPressure\\\",\\n      \\\"status\\\": \\\"False\\\",\\n      \\\"type\\\": \\\"DiskPressure\\\"\\n    },\\n    {\\n      \\\"lastHeartbeatTime\\\": \\\"2026-05-21T08:32:10Z\\\",\\n      \\\"lastTransitionTime\\\": \\\"2026-05-12T05:53:42Z\\\",\\n      \\\"message\\\": \\\"kubelet has sufficient PID available\\\",\\n      \\\"reason\\\": \\\"KubeletHasSufficientPID\\\",\\n      \\\"status\\\": \\\"False\\\",\\n      \\\"type\\\": \\\"PIDPressure\\\"\\n    },\\n    {\\n      \\\"lastHeartbeatTime\\\": \\\"2026-05-21T08:32:10Z\\\",\\n      \\\"lastTransitionTime\\\": \\\"2026-05-12T05:53:42Z\\\",\\n      \\\"message\\\": \\\"kubelet is posting ready status. AppArmor enabled\\\",\\n      \\\"reason\\\": \\\"KubeletReady\\\",\\n      \\\"status\\\": \\\"True\\\",\\n      \\\"type\\\": \\\"Ready\\\"\\n    }\\n  ]\\n}\\n{\\n  \\\"name\\\": \\\"node2\\\",\\n  \\\"allocatable\\\": {\\n    \\\"cpu\\\": \\\"12\\\",\\n    \\\"ephemeral-storage\\\": \\\"187795058378\\\",\\n    \\\"hugepages-1Gi\\\": \\\"0\\\",\\n    \\\"hugepages-2Mi\\\": \\\"0\\\",\\n    \\\"memory\\\": \\\"32758080Ki\\\",\\n    \\\"pods\\\": \\\"110\\\"\\n  },\\n  \\\"conditions\\\": [\\n    {\\n      \\\"lastHeartbeatTime\\\": \\\"2026-05-06T01:29:38Z\\\",\\n      \\\"lastTransitionTime\\\": \\\"2026-05-06T01:29:38Z\\\",\\n      \\\"message\\\": \\\"Calico is running on this node\\\",\\n      \\\"reason\\\": \\\"CalicoIsUp\\\",\\n      \\\"status\\\": \\\"False\\\",\\n      \\\"type\\\": \\\"NetworkUnavailable\\\"\\n    },\\n    {\\n      \\\"lastHeartbeatTime\\\": \\\"2026-05-21T08:31:37Z\\\",\\n      \\\"lastTransitionTime\\\": \\\"2026-04-27T08:31:58Z\\\",\\n      \\\"message\\\": \\\"kubelet has sufficient memory available\\\",\\n      \\\"reason\\\": \\\"KubeletHasSufficientMemory\\\",\\n      \\\"status\\\": \\\"False\\\",\\n      \\\"type\\\": \\\"MemoryPressure\\\"\\n    },\\n    {\\n      \\\"lastHeartbeatTime\\\": \\\"2026-05-21T08:31:37Z\\\",\\n      \\\"lastTransitionTime\\\": \\\"2026-04-27T08:31:58Z\\\",\\n      \\\"message\\\": \\\"kubelet has no disk pressure\\\",\\n      \\\"reason\\\": \\\"KubeletHasNoDiskPressure\\\",\\n      \\\"status\\\": \\\"False\\\",\\n      \\\"type\\\": \\\"DiskPressure\\\"\\n    },\\n    {\\n      \\\"lastHeartbeatTime\\\": \\\"2026-05-21T08:31:37Z\\\",\\n      \\\"lastTransitionTime\\\": \\\"2026-04-27T08:31:58Z\\\",\\n      \\\"message\\\": \\\"kubelet has sufficient PID available\\\",\\n      \\\"reason\\\": \\\"KubeletHasSufficientPID\\\",\\n      \\\"status\\\": \\\"False\\\",\\n      \\\"type\\\": \\\"PIDPressure\\\"\\n    },\\n    {\\n      \\\"lastHeartbeatTime\\\": \\\"2026-05-21T08:31:37Z\\\",\\n      \\\"lastTransitionTime\\\": \\\"2026-04-27T08:31:58Z\\\",\\n      \\\"message\\\": \\\"kubelet is posting ready status. AppArmor enabled\\\",\\n      \\\"reason\\\": \\\"KubeletReady\\\",\\n      \\\"status\\\": \\\"True\\\",\\n      \\\"type\\\": \\\"Ready\\\"\\n    }\\n  ]\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/005-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/005-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/005-evidence-run_bash_command.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"instance\":\"10.2.0.49:9100\"},\"value\":[1779352367.026,\"0.9117947043737284\"]},{\"metric\":{\"instance\":\"10.2.0.50:9100\"},\"value\":[1779352367.026,\"0.8343781953276398\"]},{\"metric\":{\"instance\":\"10.2.0.48:9100\"},\"value\":[1779352367.026,\"0.5347154351104506\"]}]}}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/006-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/006-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/006-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"requests\\\": {\\n    \\\"cpu\\\": \\\"50m\\\",\\n    \\\"memory\\\": \\\"100000Gi\\\"\\n  }\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/007-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/007-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/007-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"name\\\": \\\"master\\\",\\n  \\\"memory_capacity\\\": \\\"32860484Ki\\\",\\n  \\\"memory_allocatable\\\": \\\"32758084Ki\\\"\\n}\\n{\\n  \\\"name\\\": \\\"node1\\\",\\n  \\\"memory_capacity\\\": \\\"32860476Ki\\\",\\n  \\\"memory_allocatable\\\": \\\"32758076Ki\\\"\\n}\\n{\\n  \\\"name\\\": \\\"node2\\\",\\n  \\\"memory_capacity\\\": \\\"32860480Ki\\\",\\n  \\\"memory_allocatable\\\": \\\"32758080Ki\\\"\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/008-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/008-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/7c401f34315b4e49/tools/008-evidence-run_bash_command.summary.txt"}],"llm_analysis":"全部证据已采集完毕，以下是结论：\n\n---\n\n## 📋 证据采集结论\n\n### ✅ 已采集的关键证据\n\n| # | 证据 | 来源 | 结论 |\n|---|------|------|------|\n| **e1** | FailedScheduling 事件原文 | `kubectl describe pod` | ✅ 明确：`0/3 nodes are available: 3 Insufficient memory`，3 个 Worker 节点全部内存不足 |\n| **e2** | Pod spec resources.requests | `kubectl_get_yaml` + json 查询 | ✅ **Pod 请求 memory=100000Gi（100TB）**，极度异常，不可能被任何节点满足 |\n| **e3** | 3 个节点的可分配内存 | `kubectl get nodes -o json` | ✅ 每个节点可分配约 **32Gi**（约 31.2 GiB），而 Pod 请求 100000Gi |\n| **e4** | 节点内存可用比例 (Prometheus) | PromQL 即时查询 | ✅ master=91.2%, node1=83.4%, node2=53.5% — 节点均正常运行、内存充足 |\n| **e5** | aiops-e2e 命名空间 Pod 状态 | `kubectl get pod -n aiops-e2e` | ✅ 仅此一个 Pod 异常（Pending），无其他异常 |\n\n### 🔍 根因分析\n\n**根本原因：Pod `rc-pending-insufficient-memory` 的资源请求量异常**\n\n- Pod `spec.containers[0].resources.requests.memory = **100000Gi**（约 100 TB）\n- 而集群中每个 Worker 节点的可分配内存仅约 **32Gi**\n- 3 个节点全部 Ready 且健康，但无法满足这个离谱的内存请求\n- Prometheus 数据显示节点内存可用比例高达 53%~91%，说明集群资源本身是充足的\n\n**这很可能是 E2E 测试构造的异常场景**——人为将 Pod 内存请求设置为远超集群容量的值来触发调度失败。\n\n### ❌ 冲突/负向证据\n- 无。所有工具调用均成功返回，无 NotFound/空事件。\n\n### ⚠️ 建议修复方案（仅供参考，不执行）\n- 将 Pod 的 `resources.requests.memory` 修改为合理的值（如 128Mi、256Mi）\n- 或直接删除重建该 Pod（如为测试用途）","collection_summary":"计划 5 项，实际采集 5 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 10 个，匹配计划 6 个，未规划证据 4 个","plan_total":5,"plan_collected":5,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":10,"matched_tool_count":6,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证异常Pod rc-pending-insufficient-memory的当前状态和事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-memory -n aiops-e2e","purpose":"验证FailedScheduling事件原文确认Insufficient memory原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"查看Pod YAML中的资源请求配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-memory -n aiops-e2e -o yaml","purpose":"检查Pod的resources.requests.memory和resources.requests.cpu确认资源请求值","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取集群节点资源容量和已分配资源","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, allocatable: .status.allocatable, conditions: [.status.conditions[] | select(.reason==\"KubeletReady\" or .status!=\"True\")]}'","purpose":"验证3个节点的可分配内存容量和节点健康状态","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"查看节点内存使用率(Prometheus)","level":"important","tool":"execute_prometheus_instant_query","command":"sum(node_memory_MemAvailable_bytes) by (instance) / sum(node_memory_MemTotal_bytes) by (instance)","purpose":"验证各节点当前内存可用比例，确认资源不足的实际状况","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"获取Pod所在命名空间所有Pod状态全面确认无其他异常","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get pod -n aiops-e2e","purpose":"验证aiops-e2e命名空间下是否有其他异常Pod状态","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"r1","description":"参考runbook确认资源不足分支的典型排查步骤","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","purpose":"将已匹配runbook作为排查参考","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 5/5 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证异常Pod rc-pending-insufficient-memory的当前状态和事件 | `kubectl describe pod rc-pending-insufficient-memory -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_yaml | 查看Pod YAML中的资源请求配置 | `kubectl get pod rc-pending-insufficient-memory -n aiops-e2e -o yaml` |
   | e3 | critical | ✅ | run_bash_command | 获取集群节点资源容量和已分配资源 | `kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, allocatable...` |
   | e4 | important | ✅ | execute_prometheus_instan... | 查看节点内存使用率(Prometheus) | `sum(node_memory_MemAvailable_bytes) by (instance) / sum(node_memory_MemTotal_...` |
   | e5 | important | ✅ | kubectl_get_by_kind_in_na... | 获取Pod所在命名空间所有Pod状态全面确认无其他异常 | `kubectl get pod -n aiops-e2e` |
   | r1 | reference | ✅ | fetch_runbook | 参考runbook确认资源不足分支的典型排查步骤 | `fetch_runbook pod-pending-unschedulable.md` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (20.8s)
   📤 → 下游数据: root_cause=Pod rc-pending-insufficient-memory（aiops-e2e 命名空间）持续 Pending 31分钟，根因为 Pod 配置了异常的 resources.requests.memory=100000Gi（约 100TB），而集群3个 Worker 节点可分配内存均仅约 32Gi（master=32758084Ki, node1=32758076Ki, node2=32758080Ki），差距超 3000 倍。调度器明确报错 "0/3 nodes are available: 3 Insufficient memory"（e1）。Prometheus 数据显示节点内存利用率 53%~91% 均正常（e4），集群整体资源充足。Pod 的 imagePullPolicy=Never 但无其他调度约束问题（无 nodeSelector/affinity）。该 Pod 带有 pod_abnormal_type=PendingUnschedulable 标签和 aiops.e2e/runbook 注解，确认是 E2E 测试构造的异常场景。
   confidence=100%
   causal_chain={"root_cause": "Pod spec 中 resources.requests.memory 被设置为 100000Gi（约 100TB），远超集群中任意 Worker 节点可分配内存（各约 32Gi）", "propagation": "调度器评估 Pod 资源请求时，遍历所有 3 个 Worker 节点，发现节点可分配内存均远小于 Pod 请求的 100000Gi，判定所有节点均不可用，无抢占候选", "direct_cause": "所有 3 个 Worker 节点均无法满足 Pod 的内存请求（请求 100000Gi，节点最大提供约 32Gi），导致 FailedScheduling：3 Insufficient memory", "manifestation": "Pod rc-pending-insufficient-memory 在 aiops-e2e 命名空间中持续 Pending 状态 31 分钟，Events 中重复出现 FailedScheduling 警告"}
   rca_analysis={"phenomenon": "Pod rc-pending-insufficient-memory（命名空间 aiops-e2e）处于 Pending 状态，调度失败事件 FailedScheduling 明确报告：0/3 nodes are available: 3 Insufficient memory。集群中所有3个 Worker 节点均无法满足该 Pod 的内存请求。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod rc-pending-insufficient-memory Pending，FailedScheduling: 0/3 nodes are available: 3 Insufficient memory", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml + JSON 查询", "content": "Pod resources.requests.memory = 100000Gi（约 100 TB）", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_nodes_json", "content": "3个 Worker 节点（master/node1/node2）各 allocatable memory ≈ 32758Mi（约 32Gi）", "reliability": "高"}, {"id": "e4", "source": "Prometheus 即时查询", "content": "节点内存利用率：master=91.2%, node1=83.4%, node2=53.5% — 均有足够可用内存", "reliability": "高"}, {"id": "e5", "source": "kubectl_get_by_kind_in_namespace", "content": "aiops-e2e 命名空间仅此 1 个异常 Pod，无其他 Pending/Running 异常", "reliability": "高"}, {"id": "e6", "source": "kubectl_get_by_kind_in_cluster", "content": "全集群 65 个 Pod，59 Running，1 Pending（仅此 Pod），无其他异常", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedScheduling 31m default-scheduler 0/3 nodes are available: 3 Insufficient memory", "interpretation": "调度器明确报告所有3个节点均因内存不足无法调度此 Pod，非节点状态或调度约束问题"}, {"evidence_id": "e2", "raw_data": "resources.requests.memory = 100000Gi", "interpretation": "Pod 请求 100000Gi（约 100 TB）内存，远超任何单个节点的容量，这是调度失败的直接原因"}, {"evidence_id": "e3", "raw_data": "master: 32758084Ki, node1: 32758076Ki, node2: 32758080Ki", "interpretation": "每个 Worker 节点可分配内存仅约 32Gi，远小于 Pod 请求的 100000Gi（约 100TB），差距超过 3000 倍"}, {"evidence_id": "e4", "raw_data": "10.2.0.48=53.5%, 10.2.0.49=91.2%, 10.2.0.50=83.4%", "interpretation": "所有节点内存利用率均未达 100%，集群整体内存资源充足，不是集群资源耗尽问题"}, {"evidence_id": "e5", "raw_data": "rows=1 abnormal=1 Pending=1", "interpretation": "命名空间内仅此 Pod 异常，无其他竞争资源或级联故障"}, {"evidence_id": "e6", "raw_data": "rows=65 abnormal=1 status_counts={\"Running\":59,\"Pending\":1}", "interpretation": "全集群 65 个 Pod 中 59 个正常运行，仅此 1 个 Pending，排除大规模集群故障"}], "causal_chain": {"root_cause": "Pod spec 中 resources.requests.memory 被设置为 100000Gi（约 100TB），远超集群中任意 Worker 节点可分配内存（各约 32Gi）", "propagation": "调度器评估 Pod 资源请求时，遍历所有 3 个 Worker 节点，发现节点可分配内存均远小于 Pod 请求的 100000Gi，判定所有节点均不可用，无抢占候选", "direct_cause": "所有 3 个 Worker 节点均无法满足 Pod 的内存请求（请求 100000Gi，节点最大提供约 32Gi），导致 FailedScheduling：3 Insufficient memory", "manifestation": "Pod rc-pending-insufficient-memory 在 aiops-e2e 命名空间中持续 Pending 状态 31 分钟，Events 中重复出现 FailedScheduling 警告"}, "root_cause": "Pod rc-pending-insufficient-memory（aiops-e2e 命名空间）持续 Pending 31分钟，根因为 Pod 配置了异常的 resources.requests.memory=100000Gi（约 100TB），而集群3个 Worker 节点可分配内存均仅约 32Gi（master=32758084Ki, node1=32758076Ki, node2=32758080Ki），差距超 3000 倍。调度器明确报错 \"0/3 nodes are available: 3 Insufficient memory\"（e1）。Prometheus 数据显示节点内存利用率 53%~91% 均正常（e4），集群整体资源充足。Pod 的 imagePullPolicy=Never 但无其他调度约束问题（无 nodeSelector/affinity）。该 Pod 带有 pod_abnormal_type=PendingUnschedulable 标签和 aiops.e2e/runbook 注解，确认是 E2E 测试构造的异常场景。", "root_cause_summary": "Pod rc-pending-insufficient-memory（aiops-e2e 命名空间）持续 Pending 31分钟，根因为 Pod 配置了异常的 resources.requests.memory=100000Gi（约 100TB），而集群3个 Worker 节点可分配内存均仅约 32Gi（master=32758084Ki, node1=32758076Ki, node2=32758080Ki），差距超 3000 倍。调度器明确报错 \"0/3 nodes are available: 3 Insufficient memory\"（e1）。Prometheus 数据显示节点内存利用率 53%~91% 均正常（e4），集群整体资源充足。Pod 的 imagePullPolicy=Never 但无其他调度约束问题（无 nodeSelector/affinity）。该 Pod 带有 pod_abnormal_type=PendingUnschedulable 标签和 aiops.e2e/runbook 注解，确认是 E2E 测试构造的异常场景。", "confidence": 1.0, "confidence_reason": "证据链完整且闭合：kubectl_describe 直接显示 FailedScheduling 原文（e1），kubectl_get_yaml + JSON 查询直接获取到 Pod 内存请求值 100000Gi（e2），kubectl_get_nodes_json 确认各节点可分配内存约 32Gi（e3），Prometheus 确认集群内存充足（e4）。根因明确且直接，无任何冲突证据或逻辑缺口。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "集群节点内存资源整体不足", "probability": "已排除", "reason": "Prometheus 数据显示节点内存利用率 53%~91%，均远未达 100%，且其他 59 个 Pod 正常运行，排除集群资源耗尽"}, {"cause": "节点 taint/toleration 不匹配", "probability": "已排除", "reason": "FailedScheduling 原文为 'Insufficient memory' 而非 'had untolerated taint'，且 Pod 有 default tolerations，无 nodeSelector"}, {"cause": "节点状态异常（NotReady/Unschedulable）", "probability": "已排除", "reason": "所有3个节点 Ready=True 且无 SchedulingDisabled，健康运行中"}, {"cause": "PVC 未绑定", "probability": "已排除", "reason": "Pod 无 PVC 卷依赖，FailedScheduling 原文不含 'unbound immediate PersistentVolumeClaims'"}], "limitations": "未获取 Pod 完整 YAML 中 resources.limits 字段（仅确认了 requests.memory=100000Gi）；未排查是否有其他相同 labels 的 Pod 或 workloads（Deployment/StatefulSet）可能触发类似配置；未验证 10.2.0.48/49/50 三个 IP 与 master/node1/node2 的精确对应关系（但容量数据一致，不影响结论）。", "llm_raw_analysis": "异常组 g1：仅包含 Pod rc-pending-insufficient-memory（aiops-e2e），类型 PendingUnschedulable。上游已验证全集群 65 Pod 中仅此 1 个异常，无需处理其他异常组。根因直接明确为 Pod 资源请求 memory=100000Gi 远超节点容量，属构造的 E2E 测试场景。证据充分、因果链闭合，置信度 1.0。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-insufficient-memory（aiops-e2e 命名空间）持续 Pending 31分钟，根因为 Pod 配置了异常的 resources.requests.memory=100000Gi（约 100TB），而集群3个 Worker 节点可分配内存均仅约 3...
   置信度: 100%
   🔗 因果链:
     根本原因: Pod spec 中 resources.requests.memory 被设置为 100000Gi（约 100TB），远超集群中任意 Worker 节点可分配内存（各约 32Gi）
     传导机制: 调度器评估 Pod 资源请求时，遍历所有 3 个 Worker 节点，发现节点可分配内存均远小于 Pod 请求的 100000Gi，判定所有节点均不可用，无抢占候选
     最终表现: Pod rc-pending-insufficient-memory 在 aiops-e2e 命名空间中持续 Pending 状态 31 分钟，Events 中重复出现 FailedScheduling 警告


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (22.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5732 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 33.8s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，以下是基于您提供的详细分析结果生成的集群诊断报告。

---

## 📊 集群状态速览

根据实时数据，您的集群整体运行正常，但存在 **1 个待处理问题**。

| 项目 | 状态 |
| :--- | :--- |
| **总 Pod 数** | 65 |
| **运行正常 Pod** | 59 |
| **异常 Pod 数** | 1 |
| **异常 Pod 详情** | `rc-pending-insufficient-memory` (命名空间: `aiops-e2e`) 处于 `Pending` 状态 |

**核心问题总结**：由于 Pod `rc-pending-insufficient-memory` 请求了 **100,000 Gi (约 100 TB)** 的内存，而集群中 3 个工作节点的最大可用内存仅为 **~32 Gi**，导致调度器无法找到合适节点，Pod 持续卡在 Pending 状态。这是一个典型的资源申请超出集群容量的问题。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod 异常状态** | Pending |
| **兼容归因层** | L1 - 调度层 |
| **问题分类** | PendingUnschedulable - 资源不足 |
| **置信度** | 高 (100%) |
| **证据完整度** | 5/5 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-pending-insufficient-memory` |
| Namespace | `aiops-e2e` |
| Node | 所有 3 个 Worker 节点 |
| 错误信息 | `0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态与事件 | `kubectl describe pod rc-pending-insufficient-memory` | `Status: Pending`. <br> `Warning FailedScheduling 31m default-scheduler 0/3 nodes are available: 3 Insufficient memory.` | Pod 因**所有节点内存不足**无法被调度。 |
| 2 | Pod 资源配置 | `kubectl get pod rc-pending-insufficient-memory -o yaml` | `resources.requests.memory: 100000Gi` | Pod **请求了约 100 TB 的内存**，这是一个极其异常且巨大的数值。 |
| 3 | 集群节点容量 | `kubectl describe node` | `master`: allocatable memory = `32758084Ki` (~32 Gi)<br> `node1`: allocatable memory = `32758076Ki` (~32 Gi)<br> `node2`: allocatable memory = `32758080Ki` (~32 Gi) | 所有 Worker 节点可分配内存均约 32 Gi，远小于 Pod 请求的 100000Gi。 |
| 4 | 节点内存使用率 | Prometheus 查询 (`node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes`) | `10.2.0.49`: 91% <br> `10.2.0.50`: 53% | 节点内存利用率在正常范围，**排除了节点自身内存耗尽导致的问题**。 |
| 5 | 异常 Pod 独特性 | `kubectl get pods -n aiops-e2e` | rows=1, abnormal=1, status_counts={'Pending': 1} | 该命名空间下仅此一个 Pod 异常，确认问题独立。 |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：Pod 请求内存 (100000Gi) >> 任一节点可用内存 (~32Gi) → 调度器判定所有节点不可用 → 产生 `FailedScheduling` 事件。
- **证据 #4 反证**：节点实际内存使用率正常，说明问题不在集群资源不足，而在于 Pod 自身的资源请求配置不合理。

### 缺失证据
无。所有关键证据均已被采集。

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                    │
│ Pod `rc-pending-insufficient-memory` 的 spec 中 `resources.requests.memory`  │
│ 设置为 100000Gi（约 100TB），这是一个异常配置。                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                    │
│ Kubernetes 调度器在调度 Pod 时，会检查节点剩余可分配资源是否满足 Pod 的      │
│ `requests`。遍历所有 3 个 Worker 节点后，发现其最大可分配内存 (约 32Gi)     │
│ 远小于 Pod 请求 (100000Gi)。                                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                    │
│ 所有 3 个 Worker 节点均无法满足 Pod 的内存请求，调度失败。                   │
│ 事件显示：`0/3 nodes are available: 3 Insufficient memory.`                │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                │
│ Pod `rc-pending-insufficient-memory` 在 `aiops-e2e` 命名空间中持续处于      │
│ `Pending` 状态达 31 分钟。                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据 **证据 #1**（FailedScheduling 事件）、**证据 #2**（Pod 请求 `100000Gi` 内存）和 **证据 #3**（节点最大可用内存 ~32Gi），问题的根本原因是 **Pod 配置了异常的、远超集群容量的内存请求 (`100000Gi`)**，导致调度器无法将其调度到任何节点。

**置信度**：高 (100%)
- ✅ 事件信息明确指向 `Insufficient memory`。
- ✅ Pod YAML 直接确认了 `100000Gi` 的请求。
- ✅ 节点容量数据完全匹配，证实集群无法满足该请求。
- ✅ 该 Pod 带有的标签 (`pod_abnormal_type=PendingUnschedulable`) 表明这是一个由 E2E 测试框架构造的异常场景。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 确认该 Pod 是否为测试对象，如果是，直接删除**
*依据*：该 Pod 带有 `rootcause-e2e=true` 标签，且请求异常巨大，极有可能是系统健康检查或 E2E 测试构造的异常 Pod，而非业务应用。

```bash
# 1.1 确认 Pod 标签和注解
kubectl describe pod rc-pending-insufficient-memory -n aiops-e2e

# 1.2 如果确认是测试 Pod，直接删除
kubectl delete pod rc-pending-insufficient-memory -n aiops-e2e
```

**2. [备选] 如果该 Pod 必须运行，修改其资源请求**
*依据*：需要修改其 `resources.requests.memory` 为一个小于集群可用内存的值（如 `4Gi`）。

```bash
# 注意：直接修改 Pod 资源是受限的，Deployment/StatefulSet 等控制器可直接修改。
# 如果 Pod 是由控制器创建的，请修改控制器 YAML，然后重建 Pod。
# 以下命令仅供参考，实际需要根据 Pod 创建方式调整。
# 如果您确认 Pod 是独立创建的，可以尝试重新创建它：
kubectl get pod rc-pending-insufficient-memory -n aiops-e2e -o yaml > pod.yaml
# 编辑 pod.yaml，将 resources.requests.memory 改为 4Gi
# 然后删除旧 Pod 并重新创建
kubectl delete pod rc-pending-insufficient-memory -n aiops-e2e
kubectl apply -f pod.yaml
```

### 后续优化
1.  **资源配额**：在命名空间级别配置 `ResourceQuota`，防止单个命名空间申请过多资源。
2.  **准入控制**：使用 `LimitRange` 为命名空间设置默认请求/限制，并配置最大可申请的资源配置，避免类似的异常配置被提交。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 检查 Pod 状态 | `kubectl get pod rc-pending-insufficient-memory -n aiops-e2e` | 输出显示 `NotFound`（如果已删除）或状态为 `Running`（如果已修复）。 |
| 2. 检查集群异常 Pod 总数 | `kubectl get pods --all-namespaces | grep -v Running` | 输出中不再包含 `rc-pending-insufficient-memory`。 |

---

## ⚠️ 注意事项
- **切勿**在生产环境中创建请求过大的资源。查看该 Pod 的创建者（OwnerReference），确认是哪些系统组件或人员提交了此配置。
- 该 Pod 包含 `aiops.e2e/runbook` 注解，强烈暗示这是一个自动化排障演练场景。

---

## 📊 性能统计

├─ 总耗时: 1.6m
├─ 问题定位: 23.0s (25%) ✅
├─ 证据链采集: 27.4s (29%) ✅
├─ 根因分析: 20.8s (22%) ✅
├─ 汇总总结: 22.5s (24%) ✅
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
