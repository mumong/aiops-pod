======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 10de1fd8b3934af8]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来先扫描全局 Pod 状态，看看当前集群中有哪些异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 发现了一个异常的 Pending Pod。让我进一步查看它的详情。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  14m                    default-scheduler  0/3 nodes are availab
   💭 [问题定位] 情况已经很清楚了。让我获取对应的 runbook 参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在我已经掌握了足够的信息，可以做出完整分析了。

## 诊断分析

### 全局 Pod 扫描结果

| 状态 | 数量 |
|------|------|
| ✅ Running | 59 |
| ❌ **Pending** | **1** |
| 总计 | 60 |

### 异常 Pod 识别

| 异常 Pod | 命名空间 | 状态 | 异常类型 |
|----------|---------|------|---------|
| `rc-pending-nodeselector` | `aiops-e2e` | Pending | PendingUnschedulable |

---

### 异常详情

**Pod**: `rc-pending-nodeselector` (aiops-e2e 命名空间)
- **STATUS**: Pending（未绑定到任何节点）
- **Events**: `FailedScheduling` — `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`
- **根因**: Pod 设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，但集群中 **3 个节点都没有这个标签**，导致调度器无法放置该 Pod。
- **镜像**: `busybox:1.36`（正常，非镜像问题）
- **资源请求**: BestEffort（无资源限制，非资源不足问题）

### 异常分组

| 异常组 | 成员 Pod | 数量 |
|--------|---------|:----:|
| **PendingUnschedulable** (调度约束不匹配) | `rc-pending-nodeselector` | 1 |

---

### 分层输出

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **layer_name** | PendingUnschedulable |
| **pod_status_keyword** | Pending |
| **pod_abnormal_type** | PendingUnschedulable |
| **status_category** | scheduling |
| **置信度** | 高 (0.95) |

### 可能场景

1. **nodeSelector 标签不存在**（✅ 实际根因）：Pod 要求 `aiops.e2e/nonexistent-node-label=true`，但集群中没有任何节点拥有该标签，导致 3/3 节点均不匹配。
2. **标签拼写错误或命名空间误用**：可能本意是使用 `aiops.e2e` 命名空间下的某个节点标签，但该标签尚未添加到节点上。

### 后续审查方向（由 evidence 节点执行）

- 确认节点标签列表：检查哪些标签实际存在于节点上
- 确认 Pod 设计意图：该 nodeSelector 是否为有意配置，还是配置错误
   ✅ [问题定位] 完成 (20.4s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector 标签不存在', 'probability': '高', 'reason': 'Pod 要求 aiops.e2e/nonexistent-node-label=true，但集群中 3 个节点均无此标签，导致 FailedScheduling'}, {'scenario': '标签拼写错误或命名空间误用', 'probability': '中', 'reason': '可能本意是使用其他标签，但拼写错误或标签未正确添加到节点上'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}]
   reasoning=集群中存在当前仍处于 Pending 状态的异常 Pod rc-pending-nodeselector（aiops-e2e 命名空间），Events 显示 FailedScheduling，根因为 nodeSelector 标签不匹配（3/3 节点均未匹配），属于调度约束类异常。根据五层模型，PendingUnschedulable 归因于 L1（scheduling/node_kubelet）。集群其余 59 个 Pod 均正常运行，无其他异常。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "集群中存在当前仍处于 Pending 状态的异常 Pod rc-pending-nodeselector（aiops-e2e 命名空间），Events 显示 FailedScheduling，根因为 nodeSelector 标签不匹配（3/3 节点均未匹配），属于调度约束类异常。根据五层模型，PendingUnschedulable 归因于 L1（scheduling/node_kubelet）。集群其余 59 个 Pod 均正常运行，无其他异常。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "nodeSelector 标签不存在", "probability": "高", "reason": "Pod 要求 aiops.e2e/nonexistent-node-label=true，但集群中 3 个节点均无此标签，导致 FailedScheduling"}, {"scenario": "标签拼写错误或命名空间误用", "probability": "中", "reason": "可能本意是使用其他标签，但拼写错误或标签未正确添加到节点上"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              14m     <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/10de1fd8b3934af8/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/10de1fd8b3934af8/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/10de1fd8b3934af8/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   💭 [证据链采集] 好的，我已经收到既有 evidence_plan。现在开始按计划执行工具调用。先并行执行 e1（describe pod）、e2（get pod yaml）、e3（get nodes --show-labels）这三个 critical 级别的工具。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAME     STATUS   ROLES           AGE    VERSION   LABELS\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpg
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  15m                    default-scheduler  0/3 nodes are availab
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:18:44Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [证据链采集] 现在我已经获取了所有关键工具的真实结果。让我拉取 runbook 参考作为补充。
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [证据链采集] ## 证据采集完成 — 结果分析

### ✅ 已采集证据

| 证据项 | 来源 | 结果 |
|--------|------|------|
| **e1: FailedScheduling 事件确认** | `kubectl_describe` | ✓ 明确显示 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` — **nodeSelector/affinity 不匹配** |
| **e2: Pod YAML 确认 nodeSelector** | `kubectl_get_yaml` | ✓ `spec.nodeSelector` = **`{"aiops.e2e/nonexistent-node-label": "true"}`** — 要求一个名为 `aiops.e2e/nonexistent-node-label` 值为 `true` 的标签 |
| **e3: 节点标签清单** | `kubectl get nodes --show-labels` | ✓ 集群共 3 节点（master, node1, node2），**没有任何节点包含 `aiops.e2e/nonexistent-node-label` 标签** |

### 🔍 根因判定
**Pod `rc-pending-nodeselector` 处于 Pending 状态的原因**：
- Pod 的 `nodeSelector` 要求节点具有标签 **`aiops.e2e/nonexistent-node-label=true`**
- 集群 3 个节点（master/node1/node2）均**不具备该标签**
- 调度器无法匹配任何节点，持续报 `FailedScheduling`

### 📋 其他验证
- **PVC 依赖**：Pod 没有 PVC volume，不涉及存储绑定问题
- **Taint/Toleration**：Pod 有 `node.kubernetes.io/not-ready:NoExecute op=Exists for 300s` toleration，但这不是根因
- **资源不足**：事件原文不是 `Insufficient`，而是 `didn't match Pod's node affinity/selector`，排除资源不足
- **集群其他 Pod**：59 个 Running Pod 均正常，仅此 1 个异常 Pod

### 🛠 修复建议
1. **在节点上添加所需标签**：`kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`（任选一个或多个节点）
2. **或修正 Pod 的 nodeSelector**：将 Pod 的 `nodeSelector` 修改为集群节点已有的标签（如 `kubernetes.io/hostname` 等）
   ✅ [证据链采集] 完成 (28.7s)
   📤 → 下游数据: evidence_items=6/6
   evidence_analysis={"evidence_plan":[{"id":"e1-g1-describe-pod","description":"describe Pod rc-pending-nodeselector 确认当前状态、Events(含FailedScheduling原文)、nodeSelector spec","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"验证 FailedScheduling 事件确认 nodeSelector/affinity 不匹配原因","evidence_type":"pod_events_spec","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2-g1-get-pod-yaml","description":"获取 Pod YAML 确认 nodeSelector 具体字段值","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"检查 nodeSelector 的具体标签键值对，与节点标签对比验证不匹配根因","evidence_type":"pod_spec_config","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3-g1-get-nodes","description":"列出所有节点及其 labels，验证哪些节点有匹配标签","level":"critical","tool":"run_bash_command","command":"kubectl get nodes --show-labels","tool_args":{"command":"kubectl get nodes --show-labels"},"purpose":"验证集群节点是否具有 Pod 所需的 nodeSelector 标签","evidence_type":"node_labels","target_scope":"cluster/nodes","acceptable_tools":["run_bash_command","kubectl_get_by_kind_in_cluster"],"counts_for_completeness":true},{"id":"e4-g1-fetch-runbook","description":"获取 runbook 上下文作为参考","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","tool_args":{"runbook_name":"pod-pending-unschedulable.md"},"purpose":"runbook 参考，指导后续验证分支","evidence_type":"reference","target_scope":"reference","acceptable_tools":["fetch_runbook"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAME     STATUS   ROLES           AGE    VERSION   LABELS\\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\\nnode1    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\nnode2    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/10de1fd8b3934af8/tools/001-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/10de1fd8b3934af8/tools/001-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/10de1fd8b3934af8/tools/001-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  15m                    default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  4m32s (x2 over 9m32s)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  15m                    default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  4m32s (x2 over 9m32s)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/10de1fd8b3934af8/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/10de1fd8b3934af8/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/10de1fd8b3934af8/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/10de1fd8b3934af8/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/10de1fd8b3934af8/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/10de1fd8b3934af8/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"fetch_runbook","data":"<runbook>\n# Pod PendingUnschedulable / 调度失败\n\n> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | Pending，且 Events 含 `FailedScheduling` |\n| 资源不足 | `Insufficient cpu/memory/ephemeral-storage`、`Too many pods` |\n| 调度约束 | nodeSelector/affinity 不匹配、节点 taint 未被 toleration 容忍 |\n| 存储前置条件 | `pod has unbound immediate PersistentVolumeClaims` 应切换到 pod-volume-mount-failed |\n| 节点状态 | Node NotReady/Unknown、SchedulingDisabled、Unschedulable 会导致无可用调度节点 |\n\n## 根因分流\n- 资源不足: FailedScheduling 原文含 Insufficient cpu/memory/ephemeral-storage、Too many pods。\n- hostPort 冲突: 原文含 `didn't have free ports for the requested pod ports`，说明目标节点端口已被占用。\n- Taint/Toleration 不匹配: 原文含 `had untolerated taint`，必须检查 Pod tolerations 和 Node taints。\n- nodeSelector / nodeAffinity / podAffinity 不匹配: 原文含 `didn't match Pod's node affinity/selector` 或 affinity/anti-affinity。\n- PVC 未绑定: 原文含 `unbound immediate PersistentVolumeClaims`，根因在存储绑定而不是调度资源。\n- 节点不可调度: Node Ready=False/Unknown、SchedulingDisabled、`node.kubernetes.io/not-ready` 或 `node.kubernetes.io/unreachable`。\n- 镜像、挂载、容器启动错误不会表现为 FailedScheduling；如果 Pod 已绑定 nodeName，应切换到对应 runbook。\n\n## 诊断流程\n\n### Step 1: 确认 Pod 调度失败事件\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n关注 Events 中的 `FailedScheduling` 原文。\n\n### Step 2: 检查 Pod 调度约束\n```bash\nkubectl get pod <pod-name> -n <namespace> -o yaml\n```\n关注: spec.nodeName 是否为空、nodeSelector、affinity、tolerations、topologySpreadConstraints、schedulerName、priorityClassName、resource requests、hostNetwork/hostPort。\n\n### Step 3: 检查节点状态和可调度性\n```bash\nkubectl get nodes -o wide\n```\n关注: STATUS 列是否有 NotReady/Unknown，AGE 判断是否新节点\n\n### Step 4: 检查候选节点详情\n```bash\nkubectl describe node <node-name>\n```\n重点关注:\n- `Conditions` 部分: Ready=False/Unknown 的 reason 和 message\n- `Taints` 部分: 是否有 NoSchedule/NoExecute taint\n- `Allocatable` vs `Capacity`: 资源是否耗尽\n- `Non-terminated Pods`: 节点上运行的 Pod 数量\n\n### Step 5: 检查 PVC 状态（如果 FailedScheduling 指向 PVC）\n```bash\nkubectl get pvc -n <namespace>\nkubectl describe pvc <pvc> -n <namespace>\n```\n关注: Pending、StorageClass、volumeBindingMode、ProvisioningFailed。\n\n### Step 6: 检查 Ready 条件详情\n```bash\nkubectl get node <node-name> -o jsonpath='{.status.conditions[?(@.type==\"Ready\")]}' | python3 -m json.tool\n```\n关注: status, reason, message, lastHeartbeatTime\n\n### Step 7: 检查节点事件\n```bash\nkubectl get events -A --field-selector involvedObject.kind=Node,involvedObject.name=<node-name> --sort-by='.lastTimestamp'\n```\n关注: NodeNotReady、NodeNotSchedulable、PLEG unhealthy 等事件\n\n### Step 8: 检查受影响的 Pending Pod\n```bash\nkubectl get pods -A --field-selector status.phase=Pending | head -20\n```\n\n## 判定规则\n\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| FailedScheduling + Insufficient cpu/memory | 资源不足导致 Pod Pending | 高 |\n| FailedScheduling + Too many pods | 节点 Pod 数量上限导致 Pending | 高 |\n| FailedScheduling + didn't have free ports for the requested pod ports | hostPort 端口冲突导致 Pending | 高 |\n| FailedScheduling + had untolerated taint | taint/toleration 不匹配 | 高 |\n| FailedScheduling + node(s) didn't match node selector/affinity | 调度约束不匹配 | 高 |\n| FailedScheduling + pod has unbound immediate PersistentVolumeClaims | PVC 未绑定，应切换 VolumeMountFailed/PVC 分支 | 高 |\n| 所有候选 Node NotReady/Unschedulable | 无可用调度节点 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/10de1fd8b3934af8/tools/004-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/10de1fd8b3934af8/tools/004-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/10de1fd8b3934af8/tools/004-evidence-fetch_runbook.summary.txt"}],"llm_analysis":"## 证据采集完成 — 结果分析\n\n### ✅ 已采集证据\n\n| 证据项 | 来源 | 结果 |\n|--------|------|------|\n| **e1: FailedScheduling 事件确认** | `kubectl_describe` | ✓ 明确显示 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` — **nodeSelector/affinity 不匹配** |\n| **e2: Pod YAML 确认 nodeSelector** | `kubectl_get_yaml` | ✓ `spec.nodeSelector` = **`{\"aiops.e2e/nonexistent-node-label\": \"true\"}`** — 要求一个名为 `aiops.e2e/nonexistent-node-label` 值为 `true` 的标签 |\n| **e3: 节点标签清单** | `kubectl get nodes --show-labels` | ✓ 集群共 3 节点（master, node1, node2），**没有任何节点包含 `aiops.e2e/nonexistent-node-label` 标签** |\n\n### 🔍 根因判定\n**Pod `rc-pending-nodeselector` 处于 Pending 状态的原因**：\n- Pod 的 `nodeSelector` 要求节点具有标签 **`aiops.e2e/nonexistent-node-label=true`**\n- 集群 3 个节点（master/node1/node2）均**不具备该标签**\n- 调度器无法匹配任何节点，持续报 `FailedScheduling`\n\n### 📋 其他验证\n- **PVC 依赖**：Pod 没有 PVC volume，不涉及存储绑定问题\n- **Taint/Toleration**：Pod 有 `node.kubernetes.io/not-ready:NoExecute op=Exists for 300s` toleration，但这不是根因\n- **资源不足**：事件原文不是 `Insufficient`，而是 `didn't match Pod's node affinity/selector`，排除资源不足\n- **集群其他 Pod**：59 个 Running Pod 均正常，仅此 1 个异常 Pod\n\n### 🛠 修复建议\n1. **在节点上添加所需标签**：`kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`（任选一个或多个节点）\n2. **或修正 Pod 的 nodeSelector**：将 Pod 的 `nodeSelector` 修改为集群节点已有的标签（如 `kubernetes.io/hostname` 等）","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 5/5 项，完整度 100%；实际执行工具 5 个，匹配计划 4 个，未规划证据 1 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":5,"environment_evidence_collected":5,"environment_evidence_completeness":1.0,"executed_tool_count":5,"matched_tool_count":4,"unplanned_tool_count":1,"evidence_inventory":[{"id":"e1-g1-describe-pod","description":"describe Pod rc-pending-nodeselector 确认当前状态、Events(含FailedScheduling原文)、nodeSelector spec","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"验证 FailedScheduling 事件确认 nodeSelector/affinity 不匹配原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-g1-get-pod-yaml","description":"获取 Pod YAML 确认 nodeSelector 具体字段值","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"检查 nodeSelector 的具体标签键值对，与节点标签对比验证不匹配根因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3-g1-get-nodes","description":"列出所有节点及其 labels，验证哪些节点有匹配标签","level":"critical","tool":"run_bash_command","command":"kubectl get nodes --show-labels","purpose":"验证集群节点是否具有 Pod 所需的 nodeSelector 标签","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4-g1-fetch-runbook","description":"获取 runbook 上下文作为参考","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","purpose":"runbook 参考，指导后续验证分支","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1-g1-describ... | critical | ✅ | kubectl_describe | describe Pod rc-pending-nodeselector 确认当前状态、E... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e2-g1-get-pod... | critical | ✅ | kubectl_get_yaml | 获取 Pod YAML 确认 nodeSelector 具体字段值 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e3-g1-get-nodes | critical | ✅ | run_bash_command | 列出所有节点及其 labels，验证哪些节点有匹配标签 | `kubectl get nodes --show-labels` |
   | e4-g1-fetch-r... | reference | ✅ | fetch_runbook | 获取 runbook 上下文作为参考 | `fetch_runbook pod-pending-unschedulable.md` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (22.2s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector（aiops-e2e 命名空间）处于 Pending 状态已 15 分钟，根本原因是 nodeSelector 不匹配。kubectl_get_yaml 确认其 spec.nodeSelector = {"aiops.e2e/nonexistent-node-label": "true"}。kubectl_get_nodes 显示集群 3 个节点（master、node1、node2）的 LABELS 中均无该标签。kubectl_describe Events 明确记录："0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"。集群其余 59 个 Pod 均正常运行，无其他异常。
   confidence=98%
   causal_chain={"root_cause": "Pod rc-pending-nodeselector 的 spec.nodeSelector 定义了 aiops.e2e/nonexistent-node-label=true 标签要求，但集群 3 个节点（master、node1、node2）均不具备该标签，导致调度器无法匹配任何可用节点", "propagation": "Pod 创建时被 scheduler 调度 → scheduler 检查所有节点的 label 是否匹配 nodeSelector → 3 个节点均不匹配 → 调度器记录 FailedScheduling 事件 → Pod 持续保持在 Pending 状态，无法进入 Running", "direct_cause": "nodeSelector 标签不匹配：Pod 要求 aiops.e2e/nonexistent-node-label=true，但集群所有节点均无此标签", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续 Pending 状态，kubectl 显示 0/1 READY，Events 反复报 FailedScheduling"}
   rca_analysis={"phenomenon": "集群 aiops-e2e 命名空间中的 Pod rc-pending-nodeselector 持续处于 Pending 状态（已 15 分钟），调度器 Events 显示 FailedScheduling。集群其余 59 个 Pod 均正常运行，无其他异常。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod rc-pending-nodeselector 状态 Pending，Events 含 FailedScheduling: 0/3 nodes available - 3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml", "content": "Pod YAML spec.nodeSelector = {\"aiops.e2e/nonexistent-node-label\": \"true\"}，nodeName=None，phase=Pending", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_nodes", "content": "3 个节点（master, node1, node2）均 Ready，LABELS 中均不含 aiops.e2e/nonexistent-node-label 标签", "reliability": "高"}, {"id": "e4", "source": "kubectl_get_by_kind_in_cluster", "content": "集群共 65 个 Pod，Running=59，Pending=1（仅 rc-pending-nodeselector）", "reliability": "高"}, {"id": "e5", "source": "fetch_runbook", "content": "Runbook pod-pending-unschedulable.md: nodeSelector/affinity 不匹配时 FailedScheduling 含 'didn't match Pod's node affinity/selector'", "reliability": "参考"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.", "interpretation": "Pod 调度失败，明确指向 nodeSelector/affinity 不匹配问题，非资源不足或 taint 问题"}, {"evidence_id": "e2", "raw_data": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}", "interpretation": "Pod 要求节点具有键为 aiops.e2e/nonexistent-node-label 值为 true 的标签，这是调度约束的具体条件"}, {"evidence_id": "e3", "raw_data": "master LABELS: ...无 aiops.e2e/nonexistent-node-label...; node1 LABELS: ...无...; node2 LABELS: ...无...", "interpretation": "集群全部 3 个节点均不包含所需标签，因此调度器无法匹配任何节点"}, {"evidence_id": "e4", "raw_data": "status_counts={'Running': 59, 'Pending': 1}", "interpretation": "集群整体健康，仅此一个异常 Pod，排除大规模集群故障"}, {"evidence_id": "e5", "raw_data": "FailedScheduling + node(s) didn't match node selector/affinity → 调度约束不匹配", "interpretation": "Runbook 确认当前现象完全匹配 nodeSelector 不匹配场景"}], "causal_chain": {"root_cause": "Pod rc-pending-nodeselector 的 spec.nodeSelector 定义了 aiops.e2e/nonexistent-node-label=true 标签要求，但集群 3 个节点（master、node1、node2）均不具备该标签，导致调度器无法匹配任何可用节点", "propagation": "Pod 创建时被 scheduler 调度 → scheduler 检查所有节点的 label 是否匹配 nodeSelector → 3 个节点均不匹配 → 调度器记录 FailedScheduling 事件 → Pod 持续保持在 Pending 状态，无法进入 Running", "direct_cause": "nodeSelector 标签不匹配：Pod 要求 aiops.e2e/nonexistent-node-label=true，但集群所有节点均无此标签", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续 Pending 状态，kubectl 显示 0/1 READY，Events 反复报 FailedScheduling"}, "root_cause": "Pod rc-pending-nodeselector（aiops-e2e 命名空间）处于 Pending 状态已 15 分钟，根本原因是 nodeSelector 不匹配。kubectl_get_yaml 确认其 spec.nodeSelector = {\"aiops.e2e/nonexistent-node-label\": \"true\"}。kubectl_get_nodes 显示集群 3 个节点（master、node1、node2）的 LABELS 中均无该标签。kubectl_describe Events 明确记录：\"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"。集群其余 59 个 Pod 均正常运行，无其他异常。", "root_cause_summary": "Pod rc-pending-nodeselector（aiops-e2e 命名空间）处于 Pending 状态已 15 分钟，根本原因是 nodeSelector 不匹配。kubectl_get_yaml 确认其 spec.nodeSelector = {\"aiops.e2e/nonexistent-node-label\": \"true\"}。kubectl_get_nodes 显示集群 3 个节点（master、node1、node2）的 LABELS 中均无该标签。kubectl_describe Events 明确记录：\"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"。集群其余 59 个 Pod 均正常运行，无其他异常。", "confidence": 0.98, "confidence_reason": "三条关键证据完全一致且相互印证：Events 原文明确指示 nodeSelector 不匹配（e1）、Pod YAML 精确显示了 nodeSelector 字段值（e2）、节点标签清单证实所有节点均无该标签（e3）。Runbook 匹配规则完全吻合。无任何矛盾证据。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "资源不足（CPU/内存）", "probability": "low", "reason": "FailedScheduling 原文为 'didn't match Pod's node affinity/selector'，不含 'Insufficient' 关键词，排除资源不足"}, {"cause": "Taint/Toleration 不匹配", "probability": "low", "reason": "FailedScheduling 原文不含 'had untolerated taint'，且 3 节点均 Ready 无 NoSchedule taint"}, {"cause": "PVC 未绑定", "probability": "low", "reason": "Pod YAML 显示 volumes 仅含 kube-api-access-w74s5（Projected 类型），无 PVC volume"}, {"cause": "节点不可调度", "probability": "low", "reason": "3 个节点 STATUS 均为 Ready，无 NotReady 或 SchedulingDisabled"}], "limitations": "未采集各节点的完整 taint 列表和 allocatable 资源，但从 FailedScheduling 原文已可完全排除。由于所有 3 个节点均无匹配标签，无需进一步检查单个节点详情。", "llm_raw_analysis": "## 证据清点\n共 5 条证据，其中 e1-e4 为直接工具证据（高可靠性），e5 为 runbook 参考。\n\n## 逐条分析\n- **e1 (kubectl_describe)**：Pod 状态 Pending，Events 明确提示 nodeSelector/affinity 不匹配，这是调度器给出的直接失败原因。\n- **e2 (kubectl_get_yaml)**：从 YAML 中提取到 nodeSelector 具体值为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}，这是问题的根本条件。\n- **e3 (kubectl_get_nodes)**：3 个节点标签列表中均不包含 aiops.e2e/nonexistent-node-label 键，证实 Pod 条件无法被满足。\n- **e4 (kubectl_get_by_kind_in_cluster)**：确认仅此一个 Pod 异常，其他 59 个 Running 正常，无并发异常组。\n- **e5 (runbook)**：验证当前现象与 nodeSelector 不匹配场景完\n... 截断，原始 690 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector（aiops-e2e 命名空间）处于 Pending 状态已 15 分钟，根本原因是 nodeSelector 不匹配。kubectl_get_yaml 确认其 spec.nodeSelector = {"aiops.e2e/nonexisten...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod rc-pending-nodeselector 的 spec.nodeSelector 定义了 aiops.e2e/nonexistent-node-label=true 标签要求，但集群 3 个节点（master、node1、node2）均不具备该标签，导致调度器无法匹配任何可用节点
     传导机制: Pod 创建时被 scheduler 调度 → scheduler 检查所有节点的 label 是否匹配 nodeSelector → 3 个节点均不匹配 → 调度器记录 FailedScheduling 事件 → Pod 持续保持在 Pending 状态，无法进入 Running
     最终表现: Pod rc-pending-nodeselector 在 aiops-e2e 命名空间中持续 Pending 状态，kubectl 显示 0/1 READY，Events 反复报 FailedScheduling


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (22.8s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5279 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 34.1s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将根据您提供的阶段分析结果，为您生成一份完整的诊断报告。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending |
| **兼容归因层** | L1 - Scheduling/Node-Kubelet |
| **问题分类** | PendingUnschedulable (调度失败) |
| **置信度** | 高 (98%) |
| **证据完整度** | 3/3 (100%) |
| **核心问题** | 集群中存在 1 个处于 `Pending` 状态的 Pod (`rc-pending-nodeselector`)，其余 59 个 Pod 均正常运行。该 Pod 因 `nodeSelector` 标签不匹配而无法被调度。 |

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 集群状态 | 基本健康，60/65 个 Pod 正常运行 |
| 异常Pod | `rc-pending-nodeselector` |
| Namespace | `aiops-e2e` |
| Node | 无（未调度到任何节点） |
| 错误信息 | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` |

---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe` | **Pod Status**: `Pending` <br> **Events**: `Warning FailedScheduling` ... `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` <br> **Node-Selectors**: `aiops.e2e/nonexistent-node-label=true` | Pod 因调度约束不满足无法调度到任何节点。 |
| 2 | Pod 配置 | `kubectl get -o yaml` | **spec.nodeSelector**: `{"aiops.e2e/nonexistent-node-label": "true"}` <br> **phase**: `Pending` <br> **finalizers**: `<none>` <br> **terminationGracePeriodSeconds**: 30s | Pod YAML 明确指定了 `nodeSelector`，要求节点必须包含 `aiops.e2e/nonexistent-node-label=true` 标签。 |
| 3 | 节点信息 | `kubectl get nodes -o wide` | 集群 3 个节点（master, node1, node2）标签列表均**不包含** `aiops.e2e/nonexistent-node-label` 标签。 | 所有节点均不满足 Pod 的标签选择条件，导致调度失败。 |
| 4 | 集群概况 | `kubectl get pods -A` | 总计 65 个 Pod，其中 `Running` 59 个，`Pending` 1 个。 | 集群整体健康，此问题为局部异常。 |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：`kubectl describe` 事件明确指出节点不匹配 `node affinity/selector`，`kubectl get yaml` 揭示了具体的 selector `aiops.e2e/nonexistent-node-label=true`，而 `kubectl get nodes` 证实集群中确实没有节点拥有此标签。三者形成完整证据链。
- **排除项**：工具输出显示 `finalizers: <none>`，**明确排除了** “Finalizer 未清理” 作为根因。

### 缺失证据（如有）
无。所有计划内的关键证据均已采集。

---
## 🎯 根因分析

### 因果链
```
┌───────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                  │
│ Pod (rc-pending-nodeselector) 的 spec.nodeSelector 配置了一个              │
│ 集群中不存在的标签: aiops.e2e/nonexistent-node-label=true                  │
└───────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌───────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                  │
│ 调度器尝试将 Pod 调度到节点 → 检查所有 3 个节点的 Labels                  │
│ → 3 个节点的 Labels 均不包含 aiops.e2e/nonexistent-node-label             │
│ → 调度器无法找到满足条件的节点                                            │
└───────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌───────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                  │
│ 调度器拒绝调度，产生 FailedScheduling 事件                                │
└───────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌───────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                              │
│ Pod 状态持续为 Pending，Events 中反复出现 FailedScheduling 警告           │
└───────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (FailedScheduling 事件)、证据 #2 (`nodeSelector` 配置) 和证据 #3 (节点 Labels)，问题的根本原因是**Pod的规格(spec)中配置了`nodeSelector`标签 (`aiops.e2e/nonexistent-node-label=true`)，但集群所有节点均未匹配此标签**，导致 Pod 无法被调度。

**置信度**：高 (98%)
- ✅ 调度器事件明确指向 “node affinity/selector not match”。
- ✅ Pod YAML 明确显示了该不存在的标签。
- ✅ 所有节点的 Labels 都已列出并确认不包含该标签。
- ⚠️ 已排除 “Finalizer 未清理” 等其他可能性。

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [推荐] 删除并重建此异常 Pod**
   - 如果此 Pod 是测试用例或不再需要，可以直接删除。
   ```bash
   kubectl delete pod rc-pending-nodeselector -n aiops-e2e
   ```
   *依据*：该 Pod 因配置错误而无法运行，且无其他依赖。

**2. [调试方向] 如果必须运行此 Pod，请修复 `nodeSelector`**
   - **方案A：为某个节点添加标签**
     - 选择一个节点（例如`node1`），添加 Pod 所期望的标签。
     ```bash
     kubectl label node node1 aiops.e2e/nonexistent-node-label=true
     ```
   - **方案B：修改 Pod 的 `nodeSelector`**
     - 先删除 Pod，然后编辑其 YAML（或 Deployment YAML），将 `nodeSelector` 修改为集群中已有的标签（例如 `kubernetes.io/hostname: node1`），再重新创建。
     ```bash
     # 1. 删除当前 Pod
     kubectl delete pod rc-pending-nodeselector -n aiops-e2e
     
     # 2. （仅作为示例）如果 Pod 由 Deployment 管理，更新其 YAML
     # kubectl edit deployment/<deployment-name> -n aiops-e2e
     # 将 nodeSelector: 部分修改为已有标签
     ```

   *依据*：修改 Pod 或节点标签是解决 nodeSelector 不匹配问题的标准方法。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 已被删除（或状态变化） | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | `Error from server (NotFound): pods "rc-pending-nodeselector" not found` （如果执行了删除） |
| 2. 确认所有 Pod 正常运行 | `kubectl get pods -n aiops-e2e` | 所有 Pod 的 `STATUS` 列均为 `Running` 或 `Completed` |
| 3. 确认集群整体健康 | `kubectl get pods -A` | 无 `Pending` 状态的 Pod |

---
## ⚠️ 注意事项
- 此问题是**配置错误**导致的，并非集群资源不足或节点故障。集群的健康状态是良好的。
- 如果决定为节点打标签，请确保该操作符合您的集群资源管理规范，避免对其他工作负载产生意外影响。
- 根因报告中提到 `terminationGracePeriodSeconds: 30`，这个字段是 Pod 优雅终止的超时时间，与本问题的分析无关，已排除。

---

## 📊 性能统计

├─ 总耗时: 1.6m
├─ 问题定位: 20.4s (22%) ✅
├─ 证据链采集: 28.7s (31%) ✅
├─ 根因分析: 22.2s (24%) ✅
├─ 汇总总结: 22.8s (24%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 7 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 7 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
