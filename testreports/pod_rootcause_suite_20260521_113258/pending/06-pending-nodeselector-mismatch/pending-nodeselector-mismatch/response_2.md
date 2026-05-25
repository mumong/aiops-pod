======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: eb7519c2a941429a]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，让我先全局扫描所有 Pod，看看当前集群中有什么异常。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 现在发现了一个异常 Pod。让我查看更多细节。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          29s   <none>   <none>   
   💭 [问题定位] Pod 处于 Pending 状态且未绑定节点，这符合 PendingUnschedulable 的特征。让我描述一下这个 Pod 并获取相关 runbook。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  31s   default-scheduler  0/3 nodes are available: 3 node(s) did
   💭 [问题定位] 现在我已经获取了所有必要的信息。来看看节点的状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 现在我已经掌握了所有信息，可以进行完整的定位分析。

---

## 定位分析结果

### 当前集群异常概览

| 项目 | 内容 |
|------|------|
| 总 Pod 数 | 65 |
| 正常 Running | 59 |
| 正常 Completed | 0 |
| **异常 Pod 数** | **1** |
| 异常状态 | Pending |
| 3 个 Node | 全部 Ready |

---

### 🧩 异常 Pod 清单

| Pod | 命名空间 | 状态 | 异常类型 |
|-----|---------|------|---------|
| `rc-pending-nodeselector` | `aiops-e2e` | Pending | **PendingUnschedulable** |

---

### 📋 异常分析

#### Pod: `rc-pending-nodeselector` (PendingUnschedulable)

**状态关键字：** `Pending`
**异常类型：** `PendingUnschedulable`
**兼容分层：** L1

**关键证据：**
- `kubectl describe` 显示调度事件：
  - `FailedScheduling` — `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.`
- Pod 设置了 **NodeSelector**: `aiops.e2e/nonexistent-node-label=true`
- 集群 **3 个节点全部 Ready**，但没有任何节点带有该标签
- 这不是资源不足、Taint/Toleration 或 PVC 问题

**根因：** Pod 通过 `nodeSelector` 要求节点具有 `aiops.e2e/nonexistent-node-label=true` 标签，但集群中 3 个节点（master、node1、node2）均没有这个标签，导致调度器无法找到匹配节点。这是一个 **调度约束不匹配** 的问题。

---

### 📊 结构化输出

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **layer_name** | PendingUnschedulable |
| **confidence** | 高 (High) |
| **pod_status_keyword** | Pending |
| **pod_abnormal_type** | PendingUnschedulable |
| **status_category** | scheduling |
| **abnormal_groups** | `PendingUnschedulable` |
| **key_entities** | Pod `rc-pending-nodeselector`, NodeSelector `aiops.e2e/nonexistent-node-label=true` |
| **possible_scenarios** | 1. nodeSelector 引用了集群中不存在的节点标签 2. 测试场景（Pod 标签含 `rootcause-e2e=true`） |

---

### 🔍 后续审查方向建议（交由 evidence 节点处理）

1. **确认 nodeSelector 意图** — 该 Pod 的 `nodeSelector` 是指定了错误的标签值，还是期望有特殊节点加入集群？
2. **检查是否有节点应具有该标签** — 如需要，可给某节点打上 `aiops.e2e/nonexistent-node-label=true` 标签使其可调度
3. **如果是测试用例** — Pod 标签带有 `rootcause-e2e=true`，可能这是一个 E2E 测试场景，属于预期行为
   ✅ [问题定位] 完成 (19.8s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector 引用了集群中不存在的节点标签', 'probability': 'high', 'reason': 'Pod 设置 nodeSelector aiops.e2e/nonexistent-node-label=true，3 个节点均无此标签，FailedScheduling 事件明确提示 node affinity/selector 不匹配'}, {'scenario': '测试场景（预期行为）', 'probability': 'low', 'reason': 'Pod 标签含 rootcause-e2e=true，可能是 E2E 测试用例'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "NodeSelector", "name": "aiops.e2e/nonexistent-node-label=true", "namespace": ""}]
   reasoning=集群中存在 1 个异常 Pod (rc-pending-nodeselector) 处于 Pending 状态，异常类型为 PendingUnschedulable。kubectl describe 显示 FailedScheduling 事件：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod 设置了 nodeSelector (aiops.e2e/nonexistent-node-label=true)，而集群中 3 个节点全部 Ready 但均无此标签，导致调度失败。根因是调度约束不匹配，归为 L1 层（scheduling/node_kubelet）。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "集群中存在 1 个异常 Pod (rc-pending-nodeselector) 处于 Pending 状态，异常类型为 PendingUnschedulable。kubectl describe 显示 FailedScheduling 事件：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod 设置了 nodeSelector (aiops.e2e/nonexistent-node-label=true)，而集群中 3 个节点全部 Ready 但均无此标签，导致调度失败。根因是调度约束不匹配，归为 L1 层（scheduling/node_kubelet）。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "NodeSelector", "name": "aiops.e2e/nonexistent-node-label=true", "namespace": ""}], "possible_scenarios": [{"scenario": "nodeSelector 引用了集群中不存在的节点标签", "probability": "high", "reason": "Pod 设置 nodeSelector aiops.e2e/nonexistent-node-label=true，3 个节点均无此标签，FailedScheduling 事件明确提示 node affinity/selector 不匹配"}, {"scenario": "测试场景（预期行为）", "probability": "low", "reason": "Pod 标签含 rootcause-e2e=true，可能是 E2E 测试用例"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              27s     <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/eb7519c2a941429a/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/eb7519c2a941429a/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/eb7519c2a941429a/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我将直接执行既有 evidence_plan 中的关键工具来采集证据。

## 第一步：执行 critical 级工具 - describe Pod 和 检查节点标签
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  54s   default-scheduler  0/3 nodes are available: 3 node(s) did
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "", "stderr": "", "returncode": 0}
   💭 [证据链采集] 节点标签检查返回空结果——即没有任何节点具有 `aiops.e2e` 前缀的标签。接下来执行 important 级工具。

## 第二步：执行 important 级工具 - 获取 Pod YAML 和完整事件
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:18:44Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
57s         Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are
   💭 [证据链采集] 最后，按 reference 级别获取 runbook 确认诊断路径。
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [证据链采集] ## 证据采集完成 - 结论报告

### ✅ 已采集证据

| 证据项 | 级别 | 结果 |
|--------|------|------|
| **kubectl describe pod** | Critical ✅ | Pod **rc-pending-nodeselector** 处于 **Pending** 状态，Events 显示 `FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。Node-Selectors 明确为 `aiops.e2e/nonexistent-node-label=true` |
| **节点标签搜索** | Critical ✅ | 集群 3 个节点中 **没有任何节点** 包含 `aiops.e2e` 前缀的标签——节点标签查询返回空结果 |
| **Pod YAML** | Important ✅ | `spec.nodeName` 为空（未绑定节点），`nodeSelector` 字段为 `{"aiops.e2e/nonexistent-node-label": "true"}`，`conditions.PodScheduled.status=False`，reason=`Unschedulable`，无 PVC 卷依赖，无 finalizer 卡住 |
| **Pod 事件** | Important ✅ | 仅有一条 `FailedScheduling` 事件，无其他并发异常（无 ImagePull、无 VolumeMount、无 OOM） |
| **Runbook 参考** | Reference ✅ | 匹配 runbook 中 `nodeSelector 不匹配` 的高置信度判定分支 |

### ❌ 冲突/负向证据
- **节点标签不存在**：`aiops.e2e/nonexistent-node-label=true` 标签在 3 个节点中均不存在（负向结果，但就是根因所在）
- **无 PVC/Volume 依赖**：Pod 仅使用默认的 kube-api-access projected volume，无 PVC 存储依赖——排除存储未绑定场景
- **无 Taint/Toleration 问题**：FailedScheduling 原文不含 `untolerated taint`——排除 taint 场景
- **无资源不足**：FailedScheduling 原文不含 `Insufficient cpu/memory`——排除资源不足场景

### 📋 根因结论
**Pod `rc-pending-nodeselector`（namespace: aiops-e2e）处于 Pending 状态的根因是：Pod 设置了 nodeSelector `aiops.e2e/nonexistent-node-label=true`，而集群 3 个节点均无此标签，导致调度器无法放置。** 符合 Runbook 中 `FailedScheduling + node(s) didn't match node selector` 的判定规则，置信度：**高**。Pod 携带 `rootcause-e2e=true` 标签，疑似 E2E 测试用例，预期行为。
   ✅ [证据链采集] 完成 (19.5s)
   📤 → 下游数据: evidence_items=9/9
   evidence_analysis={"evidence_plan":[{"id":"e1-c1","description":"验证 Pod rc-pending-nodeselector 的当前状态和 FailedScheduling 事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"确认 Pod 仍处于 Pending 状态并采集 FailedScheduling 事件原文，验证 nodeSelector 不匹配的根因","evidence_type":"current_state_and_events","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":[],"counts_for_completeness":true},{"id":"e1-c2","description":"验证 Cluster 中 Node 的标签信息，确认 aiops.e2e/nonexistent-node-label=true 标签确实不存在","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, labels: .metadata.labels | to_entries[] | select(.key | contains(\"aiops.e2e\"))}'","tool_args":{},"purpose":"验证集群中没有任何节点具有 aiops.e2e/nonexistent-node-label=true 标签，确认调度约束不匹配","evidence_type":"node_label_verification","target_scope":"Cluster/Node","acceptable_tools":[],"counts_for_completeness":true},{"id":"e1-c3","description":"验证 Pod 的完整 YAML spec，确认 nodeSelector 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"验证 Pod spec 中的 nodeSelector 字段具体配置，与调度事件交叉验证","evidence_type":"pod_spec_verification","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e1-c4","description":"获取 Pod 调度相关事件，确认是否有更多调度失败细节","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-nodeselector","tool_args":{"resource_type":"pod","resource_name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"采集 Pod 的完整事件列表，确认只有 FailedScheduling 事件且没有其他并发异常","evidence_type":"pod_events","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":[],"counts_for_completeness":true},{"id":"e1-r1","description":"引用已匹配的 pod-pending-unschedulable.md runbook 上下文","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","tool_args":{},"purpose":"runbook 参考，确认 node selector 不匹配分支的诊断路径","evidence_type":"reference","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  54s   default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  54s   default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/eb7519c2a941429a/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/eb7519c2a941429a/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/eb7519c2a941429a/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/eb7519c2a941429a/tools/002-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/eb7519c2a941429a/tools/002-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/eb7519c2a941429a/tools/002-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/eb7519c2a941429a/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/eb7519c2a941429a/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/eb7519c2a941429a/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n57s         Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/eb7519c2a941429a/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/eb7519c2a941429a/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/eb7519c2a941429a/tools/004-evidence-kubectl_events.summary.txt"},{"tool":"fetch_runbook","data":"<runbook>\n# Pod PendingUnschedulable / 调度失败\n\n> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | Pending，且 Events 含 `FailedScheduling` |\n| 资源不足 | `Insufficient cpu/memory/ephemeral-storage`、`Too many pods` |\n| 调度约束 | nodeSelector/affinity 不匹配、节点 taint 未被 toleration 容忍 |\n| 存储前置条件 | `pod has unbound immediate PersistentVolumeClaims` 应切换到 pod-volume-mount-failed |\n| 节点状态 | Node NotReady/Unknown、SchedulingDisabled、Unschedulable 会导致无可用调度节点 |\n\n## 根因分流\n- 资源不足: FailedScheduling 原文含 Insufficient cpu/memory/ephemeral-storage、Too many pods。\n- hostPort 冲突: 原文含 `didn't have free ports for the requested pod ports`，说明目标节点端口已被占用。\n- Taint/Toleration 不匹配: 原文含 `had untolerated taint`，必须检查 Pod tolerations 和 Node taints。\n- nodeSelector / nodeAffinity / podAffinity 不匹配: 原文含 `didn't match Pod's node affinity/selector` 或 affinity/anti-affinity。\n- PVC 未绑定: 原文含 `unbound immediate PersistentVolumeClaims`，根因在存储绑定而不是调度资源。\n- 节点不可调度: Node Ready=False/Unknown、SchedulingDisabled、`node.kubernetes.io/not-ready` 或 `node.kubernetes.io/unreachable`。\n- 镜像、挂载、容器启动错误不会表现为 FailedScheduling；如果 Pod 已绑定 nodeName，应切换到对应 runbook。\n\n## 诊断流程\n\n### Step 1: 确认 Pod 调度失败事件\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n关注 Events 中的 `FailedScheduling` 原文。\n\n### Step 2: 检查 Pod 调度约束\n```bash\nkubectl get pod <pod-name> -n <namespace> -o yaml\n```\n关注: spec.nodeName 是否为空、nodeSelector、affinity、tolerations、topologySpreadConstraints、schedulerName、priorityClassName、resource requests、hostNetwork/hostPort。\n\n### Step 3: 检查节点状态和可调度性\n```bash\nkubectl get nodes -o wide\n```\n关注: STATUS 列是否有 NotReady/Unknown，AGE 判断是否新节点\n\n### Step 4: 检查候选节点详情\n```bash\nkubectl describe node <node-name>\n```\n重点关注:\n- `Conditions` 部分: Ready=False/Unknown 的 reason 和 message\n- `Taints` 部分: 是否有 NoSchedule/NoExecute taint\n- `Allocatable` vs `Capacity`: 资源是否耗尽\n- `Non-terminated Pods`: 节点上运行的 Pod 数量\n\n### Step 5: 检查 PVC 状态（如果 FailedScheduling 指向 PVC）\n```bash\nkubectl get pvc -n <namespace>\nkubectl describe pvc <pvc> -n <namespace>\n```\n关注: Pending、StorageClass、volumeBindingMode、ProvisioningFailed。\n\n### Step 6: 检查 Ready 条件详情\n```bash\nkubectl get node <node-name> -o jsonpath='{.status.conditions[?(@.type==\"Ready\")]}' | python3 -m json.tool\n```\n关注: status, reason, message, lastHeartbeatTime\n\n### Step 7: 检查节点事件\n```bash\nkubectl get events -A --field-selector involvedObject.kind=Node,involvedObject.name=<node-name> --sort-by='.lastTimestamp'\n```\n关注: NodeNotReady、NodeNotSchedulable、PLEG unhealthy 等事件\n\n### Step 8: 检查受影响的 Pending Pod\n```bash\nkubectl get pods -A --field-selector status.phase=Pending | head -20\n```\n\n## 判定规则\n\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| FailedScheduling + Insufficient cpu/memory | 资源不足导致 Pod Pending | 高 |\n| FailedScheduling + Too many pods | 节点 Pod 数量上限导致 Pending | 高 |\n| FailedScheduling + didn't have free ports for the requested pod ports | hostPort 端口冲突导致 Pending | 高 |\n| FailedScheduling + had untolerated taint | taint/toleration 不匹配 | 高 |\n| FailedScheduling + node(s) didn't match node selector/affinity | 调度约束不匹配 | 高 |\n| FailedScheduling + pod has unbound immediate PersistentVolumeClaims | PVC 未绑定，应切换 VolumeMountFailed/PVC 分支 | 高 |\n| 所有候选 Node NotReady/Unschedulable | 无可用调度节点 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/eb7519c2a941429a/tools/005-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/eb7519c2a941429a/tools/005-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/eb7519c2a941429a/tools/005-evidence-fetch_runbook.summary.txt"}],"llm_analysis":"## 证据采集完成 - 结论报告\n\n### ✅ 已采集证据\n\n| 证据项 | 级别 | 结果 |\n|--------|------|------|\n| **kubectl describe pod** | Critical ✅ | Pod **rc-pending-nodeselector** 处于 **Pending** 状态，Events 显示 `FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。Node-Selectors 明确为 `aiops.e2e/nonexistent-node-label=true` |\n| **节点标签搜索** | Critical ✅ | 集群 3 个节点中 **没有任何节点** 包含 `aiops.e2e` 前缀的标签——节点标签查询返回空结果 |\n| **Pod YAML** | Important ✅ | `spec.nodeName` 为空（未绑定节点），`nodeSelector` 字段为 `{\"aiops.e2e/nonexistent-node-label\": \"true\"}`，`conditions.PodScheduled.status=False`，reason=`Unschedulable`，无 PVC 卷依赖，无 finalizer 卡住 |\n| **Pod 事件** | Important ✅ | 仅有一条 `FailedScheduling` 事件，无其他并发异常（无 ImagePull、无 VolumeMount、无 OOM） |\n| **Runbook 参考** | Reference ✅ | 匹配 runbook 中 `nodeSelector 不匹配` 的高置信度判定分支 |\n\n### ❌ 冲突/负向证据\n- **节点标签不存在**：`aiops.e2e/nonexistent-node-label=true` 标签在 3 个节点中均不存在（负向结果，但就是根因所在）\n- **无 PVC/Volume 依赖**：Pod 仅使用默认的 kube-api-access projected volume，无 PVC 存储依赖——排除存储未绑定场景\n- **无 Taint/Toleration 问题**：FailedScheduling 原文不含 `untolerated taint`——排除 taint 场景\n- **无资源不足**：FailedScheduling 原文不含 `Insufficient cpu/memory`——排除资源不足场景\n\n### 📋 根因结论\n**Pod `rc-pending-nodeselector`（namespace: aiops-e2e）处于 Pending 状态的根因是：Pod 设置了 nodeSelector `aiops.e2e/nonexistent-node-label=true`，而集群 3 个节点均无此标签，导致调度器无法放置。** 符合 Runbook 中 `FailedScheduling + node(s) didn't match node selector` 的判定规则，置信度：**高**。Pod 携带 `rootcause-e2e=true` 标签，疑似 E2E 测试用例，预期行为。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 8 个，匹配计划 5 个，未规划证据 3 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":5,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1-c1","description":"验证 Pod rc-pending-nodeselector 的当前状态和 FailedScheduling 事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"确认 Pod 仍处于 Pending 状态并采集 FailedScheduling 事件原文，验证 nodeSelector 不匹配的根因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e1-c2","description":"验证 Cluster 中 Node 的标签信息，确认 aiops.e2e/nonexistent-node-label=true 标签确实不存在","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, labels: .metadata.labels | to_entries[] | select(.key | contains(\"aiops.e2e\"))}'","purpose":"验证集群中没有任何节点具有 aiops.e2e/nonexistent-node-label=true 标签，确认调度约束不匹配","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e1-c3","description":"验证 Pod 的完整 YAML spec，确认 nodeSelector 配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"验证 Pod spec 中的 nodeSelector 字段具体配置，与调度事件交叉验证","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e1-c4","description":"获取 Pod 调度相关事件，确认是否有更多调度失败细节","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-nodeselector","purpose":"采集 Pod 的完整事件列表，确认只有 FailedScheduling 事件且没有其他并发异常","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e1-r1","description":"引用已匹配的 pod-pending-unschedulable.md runbook 上下文","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","purpose":"runbook 参考，确认 node selector 不匹配分支的诊断路径","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1-c1 | critical | ✅ | kubectl_describe | 验证 Pod rc-pending-nodeselector 的当前状态和 FailedS... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e1-c2 | critical | ✅ | run_bash_command | 验证 Cluster 中 Node 的标签信息，确认 aiops.e2e/nonexist... | `kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, labels: .me...` |
   | e1-c3 | important | ✅ | kubectl_get_yaml | 验证 Pod 的完整 YAML spec，确认 nodeSelector 配置 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e1-c4 | important | ✅ | kubectl_events | 获取 Pod 调度相关事件，确认是否有更多调度失败细节 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pendi...` |
   | e1-r1 | reference | ✅ | fetch_runbook | 引用已匹配的 pod-pending-unschedulable.md runbook 上下文 | `fetch_runbook pod-pending-unschedulable.md` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (15.0s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector (namespace: aiops-e2e) 处于 Pending 状态，异常类型 PendingUnschedulable。kubectl describe 显示 FailedScheduling 事件："0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"。Pod YAML 确认 nodeSelector 为 {"aiops.e2e/nonexistent-node-label": "true"}，而集群 3 个节点（全部 Ready）均无此标签（节点标签查询返回空）。根因是调度约束不匹配。无资源不足、无 taint/toleration 问题、无 PVC 依赖问题。Pod 标签含 rootcause-e2e=true，疑似 E2E 测试场景。
   confidence=97%
   causal_chain={"root_cause": "Pod 设置了 nodeSelector aiops.e2e/nonexistent-node-label=true，而集群 3 个节点均无此标签", "propagation": "调度器 default-scheduler 在处理 Pod 调度时，检查所有 3 个节点的标签，发现没有任何节点匹配 nodeSelector 要求的 aiops.e2e/nonexistent-node-label=true 标签，所有节点均被过滤；preemption 也无法帮助解决标签不匹配问题", "direct_cause": "调度器找不到满足 nodeSelector 条件的节点，Pod 的 spec.nodeName 保持为空，无法被调度到任何节点", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e namespace 中处于 Pending 状态 ≥57s，kubectl describe 显示 FailedScheduling 事件"}
   rca_analysis={"phenomenon": "集群中存在 1 个异常 Pod (rc-pending-nodeselector, namespace: aiops-e2e) 处于 Pending 状态，异常类型 PendingUnschedulable。Pod 无法被调度到任何节点，Events 显示 FailedScheduling 事件。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod rc-pending-nodeselector 处于 Pending 状态，FailedScheduling 事件：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Node-Selectors: aiops.e2e/nonexistent-node-label=true", "reliability": "高"}, {"id": "e2", "source": "run_bash_command (节点标签搜索)", "content": "集群 3 个节点中均不存在 aiops.e2e/nonexistent-node-label=true 标签（返回空结果）", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_yaml", "content": "Pod spec.nodeName 为空，nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}，conditions.PodScheduled.status=False, reason=Unschedulable，无 PVC 依赖", "reliability": "高"}, {"id": "e4", "source": "kubectl_events", "content": "仅 1 条 FailedScheduling 事件，无其他异常事件", "reliability": "高"}, {"id": "e5", "source": "kubectl_get_by_kind_in_cluster (Nodes)", "content": "3 个节点全部 Ready，无异常节点", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedScheduling 54s default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. Node-Selectors: aiops.e2e/nonexistent-node-label=true", "interpretation": "FailedScheduling 事件明确表明调度失败原因是节点亲和性/选择器不匹配，Pod 设置了 nodeSelector aiops.e2e/nonexistent-node-label=true"}, {"evidence_id": "e2", "raw_data": "节点标签查询返回空 stdout，returncode=0", "interpretation": "确认集群 3 个节点均无 aiops.e2e/nonexistent-node-label=true 标签，这是调度的直接障碍"}, {"evidence_id": "e3", "raw_data": "nodeName: None, nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}, phase: Pending, conditions.PodScheduled: status=False reason=Unschedulable", "interpretation": "Pod 未被绑定到任何节点，nodeSelector 配置与证据 e1 一致，排除 PVC/Volume 依赖问题"}, {"evidence_id": "e4", "raw_data": "57s Warning FailedScheduling Pod/rc-pending-nodeselector 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.", "interpretation": "只有一条 FailedScheduling 事件，无其他并发异常（无 ImagePull、无 VolumeMount 等），说明问题纯在调度阶段"}, {"evidence_id": "e5", "raw_data": "3 个节点全部 Ready，无异常状态节点", "interpretation": "排除节点不可用导致无法调度的可能性，根因不在节点健康状态"}], "causal_chain": {"root_cause": "Pod 设置了 nodeSelector aiops.e2e/nonexistent-node-label=true，而集群 3 个节点均无此标签", "propagation": "调度器 default-scheduler 在处理 Pod 调度时，检查所有 3 个节点的标签，发现没有任何节点匹配 nodeSelector 要求的 aiops.e2e/nonexistent-node-label=true 标签，所有节点均被过滤；preemption 也无法帮助解决标签不匹配问题", "direct_cause": "调度器找不到满足 nodeSelector 条件的节点，Pod 的 spec.nodeName 保持为空，无法被调度到任何节点", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e namespace 中处于 Pending 状态 ≥57s，kubectl describe 显示 FailedScheduling 事件"}, "root_cause": "Pod rc-pending-nodeselector (namespace: aiops-e2e) 处于 Pending 状态，异常类型 PendingUnschedulable。kubectl describe 显示 FailedScheduling 事件：\"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"。Pod YAML 确认 nodeSelector 为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}，而集群 3 个节点（全部 Ready）均无此标签（节点标签查询返回空）。根因是调度约束不匹配。无资源不足、无 taint/toleration 问题、无 PVC 依赖问题。Pod 标签含 rootcause-e2e=true，疑似 E2E 测试场景。", "root_cause_summary": "Pod rc-pending-nodeselector (namespace: aiops-e2e) 处于 Pending 状态，异常类型 PendingUnschedulable。kubectl describe 显示 FailedScheduling 事件：\"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"。Pod YAML 确认 nodeSelector 为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}，而集群 3 个节点（全部 Ready）均无此标签（节点标签查询返回空）。根因是调度约束不匹配。无资源不足、无 taint/toleration 问题、无 PVC 依赖问题。Pod 标签含 rootcause-e2e=true，疑似 E2E 测试场景。", "confidence": 0.97, "confidence_reason": "有完整的直接证据链：kubectl_describe 显示 FailedScheduling 事件 + 节点标签搜索确认标签不存在 + Pod YAML 确认 nodeSelector 配置 + 3 个节点全部 Ready 排除节点故障。FailedScheduling 原文精确匹配 runbook 中 'didn't match node selector' 高置信度判定分支。所有冲突场景（资源不足、taint、PVC）已被负向证据排除。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "集群资源不足（CPU/内存）", "probability": "low", "reason": "FailedScheduling 原文不含 Insufficient cpu/memory 关键词，已排除"}, {"cause": "节点 Taint/Toleration 不匹配", "probability": "low", "reason": "FailedScheduling 原文不含 untolerated taint 关键词，已排除"}, {"cause": "PVC 未绑定", "probability": "low", "reason": "Pod YAML 显示无 PVC 卷依赖，仅使用默认 kube-api-access projected volume，已排除"}, {"cause": "节点不可用（NotReady）", "probability": "low", "reason": "3 个节点全部 Ready，无异常节点状态，已排除"}], "limitations": "仅涉及 1 个异常 Pod，集群整体健康（59/65 个 Pod 运行正常）。Pod 标签含 rootcause-e2e=true，可能是 E2E 测试用例，预期行为而非真实故障。未检查集群中是否存在其他 namespace 的 Pending Pod（但异常 Pod 扫描已覆盖全集群）。", "llm_raw_analysis": "证据清点：共 5 条直接证据（kubectl_describe、节点标签搜索、kubectl_get_yaml、kubectl_events、Nodes 列表）。逐条分析：e1 显示 FailedScheduling 事件明确指向 node affinity/selector 不匹配；e2 直接确认目标标签在所有 3 个节点上不存在；e3 确认 nodeSelector 配置与 e1 一致且无 PVC/Volume 依赖；e4 确认只有一条 FailedScheduling 事件无并发异常；e5 确认 3 个节点全部 Ready 排除节点故障。关联分析：所有证据高度一致，无矛盾。因果链清晰：nodeSelector 引用不存在的标签 → 调度器过滤所有节点 → Pod 无法被调度 → Pending 状态 + FailedScheduling 事件。置信度 0.97。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector (namespace: aiops-e2e) 处于 Pending 状态，异常类型 PendingUnschedulable。kubectl describe 显示 FailedScheduling 事件："0/3 nodes are avai...
   置信度: 97%
   🔗 因果链:
     根本原因: Pod 设置了 nodeSelector aiops.e2e/nonexistent-node-label=true，而集群 3 个节点均无此标签
     传导机制: 调度器 default-scheduler 在处理 Pod 调度时，检查所有 3 个节点的标签，发现没有任何节点匹配 nodeSelector 要求的 aiops.e2e/nonexistent-node-label=true 标签，所有节点均被过滤；preemption 也无法帮助解决标签不匹配问题
     最终表现: Pod rc-pending-nodeselector 在 aiops-e2e namespace 中处于 Pending 状态 ≥57s，kubectl describe 显示 FailedScheduling 事件


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (18.4s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5421 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 12.7s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将根据您提供的详细诊断数据，生成一份专业、完整的报告。

---

## 📊 诊断概览

您的集群当前的整体状况是健康的。在全部 65 个 Pod 中，`Running` 状态的 Pod 有 59 个，仅有 **1 个 Pod** 处于 `Pending` 异常状态。

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending (PendingUnschedulable) |
| **兼容归因层** | L1 - scheduling / node_kubelet |
| **问题分类** | 调度失败 - nodeSelector 约束不匹配 |
| **置信度** | 高 (97%) |
| **证据完整度** | 4/4 (100%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-pending-nodeselector` (namespace: `aiops-e2e`) |
| Namespace | `aiops-e2e` |
| Node | 无目标节点（未调度成功） |
| 错误信息 | `FailedScheduling`: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. |

**集群整体状态**：
| 指标 | 数据 |
|------|------|
| 总 Pod 数 | 65 |
| 正常 Pod 数 (Running) | 59 |
| 异常 Pod 数 | 1 (Pending) |
| 节点总数 | 3 |
| 健康节点数 (Ready) | 3 |

---

## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 & 事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | `Status: Pending`<br>`Warning FailedScheduling 54s: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` | Pod 处于 Pending 状态，调度失败，原因是节点亲和性/选择器不匹配。 |
| 2 | Pod YAML 配置 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` | `Node-Selectors: aiops.e2e/nonexistent-node-label=true` | Pod 明确设置了 `nodeSelector`，要求节点必须包含 `aiops.e2e/nonexistent-node-label=true` 标签。 |
| 3 | 节点标签信息 | `run_bash_command` (获取节点标签) | 命令行执行成功，`stdout` 为空，说明无节点具有该标签。 | 集群中 3 个节点均**不存在** `aiops.e2e/nonexistent-node-label=true` 标签。 |
| 4 | 事件确认 | `kubectl events -n aiops-e2e` | `57s Warning FailedScheduling Pod/rc-pending-nodeselector 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 调度事件反复确认了与证据 #1 相同的失败原因。 |

### 证据关联分析
- **证据 #1 + #2 + #3 + #4 印证**：Pod 的 `nodeSelector` (`aiops.e2e/nonexistent-node-label=true`) 与集群中所有节点（共 3 个）的实际标签不匹配，导致调度器无法找到符合条件的节点，Pod 持续处于 `Pending` 状态。

### 缺失证据
无。证据链完整，已准确定位根因。

---

## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                            │
│ Pod rc-pending-nodeselector 的 spec 中定义了 nodeSelector:           │
│ {"aiops.e2e/nonexistent-node-label": "true"}                       │
│ 但集群中没有任何节点拥有这个标签。                                    │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                            │
│ 调度器 (default-scheduler) 过滤节点 → 所有 3 个节点因标签不匹配被过滤 │
│ → Preemption (抢占) 也无法解决标签不匹配的问题                       │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                            │
│ Pod spec.nodeName 为空，没有可调度的目标节点，Pod 无法被分配。        │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                        │
│ Pod rc-pending-nodeselector 在 aiops-e2e namespace 中持续处于        │
│ Pending 状态超过 57 秒，kubectl 反复报告 FailedScheduling 事件。     │
└─────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (FailedScheduling 事件)、#2 (Pod YAML - nodeSelector)，以及证据 #3 (节点标签查询结果为空)，问题的根本原因是**Pod 的调度约束（nodeSelector）在集群中无法被满足**。

**置信度**：高 (97%)
- ✅ `FailedScheduling` 事件明确指向 `node affinity/selector`。
- ✅ Pod YAML 和节点标签数据直接证实了不匹配。
- ✅ 检查了其他可能性（资源不足、taint/toleration、PVC），均已排除。
- ⚠️ 注意到 Pod 标签包含 `rootcause-e2e=true`，这很可能是一个 E2E (End-to-End) 测试用例，模拟了配置错误的场景，而非业务故障。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）
**1. [确认是否是预期行为] 检查 Pod 标签**
如果这是主动创建的测试 Pod，则无需处理。
```bash
# 查看 Pod 的标签
kubectl get pod rc-pending-nodeselector -n aiops-e2e --show-labels
```
*目的*：确认是否存在 `rootcause-e2e=true` 标签。

**2. [如果非测试场景] 移除或更正 Pod 的标签选择器**
这是解决问题的核心。您需要根据实际意图选择以下一种方案：
- **方案 A (修正节点标签)**：如果某个节点应该承载此 Pod，为其打上正确的标签。
  ```bash
  # 假设要将标签打在名为 <node-name> 的节点上
  kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true
  ```
- **方案 B (修改 Pod Selecor)**：如果 Pod 的节点选择器配置错误（例如，您希望它部署在除了 Master 之外的任何节点），请编辑 Pod/Deployment 的 spec 移除或更正 `nodeSelector` 字段。
  ```bash
  # 直接从 Deployment 中移除 nodeSelector
  kubectl edit deployment <deployment-name> -n aiops-e2e
  # 在 YAML 编辑器中找到 spec.template.spec.nodeSelector 并删除整个块。
  ```
- **方案 C (删除 Pod)**：如果此 Pod 是测试产物且已完成使命，直接删除。
  ```bash
  kubectl delete pod rc-pending-nodeselector -n aiops-e2e
  ```
### 后续优化
1. **审核配置**：在 CI/CD 或应用部署流程中，增加对 `nodeSelector`、`affinity`、`taints` 等调度配置的校验，避免调度约束与集群实际标签不匹配。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: `Running` (或 Pod 已被删除) |
| 2. 检查 Pod 事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 不再有 `Warning FailedScheduling` 事件 |
| 3. 检查节点标签(若使用方案A) | `kubectl get node <node-name> --show-labels` | 看到新添加的 `aiops.e2e/nonexistent-node-label=true` 标签 |

---

## ⚠️ 注意事项
- **此问题大概率是 E2E 测试**：Pod 的标签 (`rootcause-e2e=true`) 强烈暗示这是一个预置的测试场景。如果不是业务问题，建议直接忽略或清除该 Pod。
- **集群健康度**：除本 Pod 外，集群中 59 个 Pod 运行正常，3 个节点全部 Ready，无其他系统性风险。

---

## 📊 性能统计

├─ 总耗时: 1.2m
├─ 问题定位: 19.8s (27%) ✅
├─ 证据链采集: 19.5s (27%) ✅
├─ 根因分析: 15.0s (21%) ✅
├─ 汇总总结: 18.4s (25%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 10 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 10 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
