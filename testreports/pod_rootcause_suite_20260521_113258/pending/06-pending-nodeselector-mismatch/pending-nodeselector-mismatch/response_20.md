======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: a019dbbca07e40ff]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先来扫描整个集群的所有 Pod，看看当前有哪些异常状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 发现了一个异常 Pod。让我进一步查看它的详情。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          13m   <none>   <none>   
   💭 [问题定位] 这个 Pod 带有 `pod_abnormal_type=PendingUnschedulable` 标签，符合 PendingUnschedulable 类型。让我查看它的描述信息。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  13m                    default-scheduler  0/3 nodes are availab
   💭 [问题定位] 让我获取对应的 runbook 参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在信息很清晰了，我来做完整的分析定位。

## Pod 全局扫描结果

| 状态 | 数量 |
|------|------|
| **Running（正常）** | 59 |
| **Pending（异常）** | 1 |
| **其他异常** | 0 |

整个集群只有一个异常 Pod，集群整体非常健康。

---

## 异常 Pod 分析

| 字段 | 值 |
|------|------|
| **Pod** | `rc-pending-nodeselector` |
| **命名空间** | `aiops-e2e` |
| **当前状态** | `Pending` |
| **调度事件** | `FailedScheduling` |
| **QoS 等级** | `BestEffort` |
| **节点选择器** | `aiops.e2e/nonexistent-node-label=true` |

### Events 关键信息
```
0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.
```
候选节点全部不匹配 Pod 的 `nodeSelector`。

### 根本原因
Pod 设置了 **`nodeSelector: aiops.e2e/nonexistent-node-label=true`**，该标签在集群中任何节点上都不存在，导致 3 个节点全部无法匹配，Pod 无法调度。

---

## 定位输出

- **layer**: L1
- **derived_layer**: L1
- **layers**: L1
- **layer_name**: PendingUnschedulable — 调度约束不匹配
- **pod_status_keyword**: Pending
- **pod_abnormal_type**: PendingUnschedulable
- **status_category**: scheduling
- **abnormal_pods**: rc-pending-nodeselector (aiops-e2e)
- **abnormal_groups**: Pending — FailedScheduling
- **key_entities**: Pod:rc-pending-nodeselector(namespace=aiops-e2e)
- **possible_scenarios**: nodeSelector 标签 `aiops.e2e/nonexistent-node-label=true` 在集群所有节点上均不存在，导致 Pod 无法被调度到任何节点
- **confidence**: 高

---

**总结**：集群整体运行正常（59 个 Pod 全部 Running），只有一个测试用 Pod `rc-pending-nodeselector` 卡在 Pending 状态，原因是其 `nodeSelector` 引用了集群中不存在的标签。这是一个典型的 **L1 调度约束不匹配** 问题。如需修复，可移除或修正该 `nodeSelector` 即可。
   ✅ [问题定位] 完成 (20.4s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector 标签 aiops.e2e/nonexistent-node-label=true 在集群所有节点上均不存在，导致 Pod 无法被调度到任何节点', 'probability': '高', 'reason': "FailedScheduling 事件明确指示 3 node(s) didn't match Pod's node affinity/selector，且 describe 确认 nodeSelector 使用了不存在的标签"}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}]
   reasoning=集群中有一个异常 Pod rc-pending-nodeselector 处于 Pending 状态，Events 显示 FailedScheduling，原因为 nodeSelector 标签 aiops.e2e/nonexistent-node-label=true 在所有 3 个节点上均不存在，导致调度约束不匹配。属于典型的 L1 调度层问题。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable — 调度约束不匹配", "confidence": 0.98, "reasoning": "集群中有一个异常 Pod rc-pending-nodeselector 处于 Pending 状态，Events 显示 FailedScheduling，原因为 nodeSelector 标签 aiops.e2e/nonexistent-node-label=true 在所有 3 个节点上均不存在，导致调度约束不匹配。属于典型的 L1 调度层问题。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "nodeSelector 标签 aiops.e2e/nonexistent-node-label=true 在集群所有节点上均不存在，导致 Pod 无法被调度到任何节点", "probability": "高", "reason": "FailedScheduling 事件明确指示 3 node(s) didn't match Pod's node affinity/selector，且 describe 确认 nodeSelector 使用了不存在的标签"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              13m     <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/a019dbbca07e40ff/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/a019dbbca07e40ff/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/a019dbbca07e40ff/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 98%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我直接执行既有 evidence_plan 中的工具调用。先开始关键的几个工具。
   💭 [证据链采集] 调用工具: kubectl_describe
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
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  14m                    default-scheduler  0/3 nodes are availab
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
14m                     Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0
   💭 [证据链采集] 现在执行节点标签检查，确认所有节点都缺少这个标签。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAME     LABELS\nmaster   map[beta.kubernetes.io/arch:amd64 beta.kubernetes.io/os:linux fpga-version: kubernetes.io/arch:amd64 kubernetes.io/hostname:master kubernetes.io/
   💭 [证据链采集] 所有关键证据已采集完毕，以下是证据总结。

---

## 证据采集结论

### ✅ 已采集证据（全部验证通过）

| 序号 | 证据维度 | 来源 | 结果 |
|:---:|:---------|:-----|:-----|
| **e1** | FailedScheduling 事件原文 | `kubectl describe pod` | ✅ `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` |
| **e2** | Pod YAML 确认 nodeSelector | `kubectl get pod -o yaml` | ✅ 明确配置 `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}`，且 `phase: Pending`，`nodeName: None` |
| **e3** | Pod 事件确认 | `kubectl_events` | ✅ 两次 FailedScheduling 事件（14m 和 3m51s），内容一致 |
| **e4** | 节点标签检查 | `kubectl get nodes -o custom-columns` | ✅ 集群 3 个节点（master/node1/node2）均不包含标签 `aiops.e2e/nonexistent-node-label=true`，**确认为标签缺失** |
| **e5** | Runbook 参考 | `fetch_runbook` | ✅ 匹配规则：`FailedScheduling + node(s) didn't match node selector/affinity → 调度约束不匹配（高置信度）` |

### ❌ 未采集 / 冲突证据
- 无冲突或负向证据：所有工具均正常返回，Pod 仍存在于 aiops-e2e 命名空间。

### 根因结论
Pod `rc-pending-nodeselector`（命名空间 `aiops-e2e`）的 `nodeSelector` 指定了标签 **`aiops.e2e/nonexistent-node-label=true`**，而集群中 **3 个节点均无此标签**，导致调度器无法找到可匹配节点，Pod 卡在 Pending 状态。此属于典型的 **调度约束不匹配** 问题，与上游 L1 定位一致。

### 建议修复方案（仅参考，不执行）
1. **给目标节点打标签**：`kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`
2. **或修改 Pod 的 nodeSelector**：移除或不存在的标签，改用已有标签
3. **或删除无需的 Pod**：`kubectl delete pod rc-pending-nodeselector -n aiops-e2e`
   ✅ [证据链采集] 完成 (21.7s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1-pod-describe","description":"验证 Pod rc-pending-nodeselector 的当前状态、spec.nodeSelector 和 FailedScheduling 事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e","type":"pod"},"purpose":"确认 FailedScheduling 事件原文，验证 nodeSelector 不匹配是根因","evidence_type":"pod_status_and_events","target_scope":"main_abnormal_group_g1","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2-pod-yaml","description":"获取 Pod YAML 验证 spec.nodeSelector 具体配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e","type":"pod"},"purpose":"确认 nodeSelector 中使用了不存在的标签 aiops.e2e/nonexistent-node-label=true","evidence_type":"pod_spec_config","target_scope":"main_abnormal_group_g1","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3-pod-events","description":"获取命名空间事件确认 FailedScheduling 详细原因","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-nodeselector","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-pending-nodeselector"},"purpose":"验证 FailedScheduling 事件原文，确认调度器明确拒绝原因","evidence_type":"pod_events","target_scope":"main_abnormal_group_g1","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4-nodes-check","description":"检查集群所有节点标签，确认 aiops.e2e/nonexistent-node-label 标签不存在","level":"important","tool":"run_bash_command","command":"kubectl get nodes -o custom-columns=NAME:.metadata.name,LABELS:.metadata.labels | head -80","tool_args":{"command":"kubectl get nodes -o custom-columns=NAME:.metadata.name,LABELS:.metadata.labels"},"purpose":"验证集群节点是否缺少 nodeSelector 要求的标签，确认是调度约束不匹配","evidence_type":"node_label_verification","target_scope":"main_abnormal_group_g1","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5-runbook-ref","description":"获取 Pod PendingUnschedulable 排障参考","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","tool_args":{"runbook_name":"pod-pending-unschedulable.md"},"purpose":"确认 runbook 中 nodeSelector/affinity 不匹配的典型验证步骤","evidence_type":"runbook_reference","target_scope":"main_abnormal_group_g1","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a019dbbca07e40ff/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a019dbbca07e40ff/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a019dbbca07e40ff/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  14m                    default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  3m50s (x2 over 8m50s)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  14m                    default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  3m50s (x2 over 8m50s)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a019dbbca07e40ff/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a019dbbca07e40ff/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a019dbbca07e40ff/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n14m                     Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n3m51s (x2 over 8m51s)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a019dbbca07e40ff/tools/003-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a019dbbca07e40ff/tools/003-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a019dbbca07e40ff/tools/003-evidence-kubectl_events.summary.txt"},{"tool":"fetch_runbook","data":"<runbook>\n# Pod PendingUnschedulable / 调度失败\n\n> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | Pending，且 Events 含 `FailedScheduling` |\n| 资源不足 | `Insufficient cpu/memory/ephemeral-storage`、`Too many pods` |\n| 调度约束 | nodeSelector/affinity 不匹配、节点 taint 未被 toleration 容忍 |\n| 存储前置条件 | `pod has unbound immediate PersistentVolumeClaims` 应切换到 pod-volume-mount-failed |\n| 节点状态 | Node NotReady/Unknown、SchedulingDisabled、Unschedulable 会导致无可用调度节点 |\n\n## 根因分流\n- 资源不足: FailedScheduling 原文含 Insufficient cpu/memory/ephemeral-storage、Too many pods。\n- hostPort 冲突: 原文含 `didn't have free ports for the requested pod ports`，说明目标节点端口已被占用。\n- Taint/Toleration 不匹配: 原文含 `had untolerated taint`，必须检查 Pod tolerations 和 Node taints。\n- nodeSelector / nodeAffinity / podAffinity 不匹配: 原文含 `didn't match Pod's node affinity/selector` 或 affinity/anti-affinity。\n- PVC 未绑定: 原文含 `unbound immediate PersistentVolumeClaims`，根因在存储绑定而不是调度资源。\n- 节点不可调度: Node Ready=False/Unknown、SchedulingDisabled、`node.kubernetes.io/not-ready` 或 `node.kubernetes.io/unreachable`。\n- 镜像、挂载、容器启动错误不会表现为 FailedScheduling；如果 Pod 已绑定 nodeName，应切换到对应 runbook。\n\n## 诊断流程\n\n### Step 1: 确认 Pod 调度失败事件\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n关注 Events 中的 `FailedScheduling` 原文。\n\n### Step 2: 检查 Pod 调度约束\n```bash\nkubectl get pod <pod-name> -n <namespace> -o yaml\n```\n关注: spec.nodeName 是否为空、nodeSelector、affinity、tolerations、topologySpreadConstraints、schedulerName、priorityClassName、resource requests、hostNetwork/hostPort。\n\n### Step 3: 检查节点状态和可调度性\n```bash\nkubectl get nodes -o wide\n```\n关注: STATUS 列是否有 NotReady/Unknown，AGE 判断是否新节点\n\n### Step 4: 检查候选节点详情\n```bash\nkubectl describe node <node-name>\n```\n重点关注:\n- `Conditions` 部分: Ready=False/Unknown 的 reason 和 message\n- `Taints` 部分: 是否有 NoSchedule/NoExecute taint\n- `Allocatable` vs `Capacity`: 资源是否耗尽\n- `Non-terminated Pods`: 节点上运行的 Pod 数量\n\n### Step 5: 检查 PVC 状态（如果 FailedScheduling 指向 PVC）\n```bash\nkubectl get pvc -n <namespace>\nkubectl describe pvc <pvc> -n <namespace>\n```\n关注: Pending、StorageClass、volumeBindingMode、ProvisioningFailed。\n\n### Step 6: 检查 Ready 条件详情\n```bash\nkubectl get node <node-name> -o jsonpath='{.status.conditions[?(@.type==\"Ready\")]}' | python3 -m json.tool\n```\n关注: status, reason, message, lastHeartbeatTime\n\n### Step 7: 检查节点事件\n```bash\nkubectl get events -A --field-selector involvedObject.kind=Node,involvedObject.name=<node-name> --sort-by='.lastTimestamp'\n```\n关注: NodeNotReady、NodeNotSchedulable、PLEG unhealthy 等事件\n\n### Step 8: 检查受影响的 Pending Pod\n```bash\nkubectl get pods -A --field-selector status.phase=Pending | head -20\n```\n\n## 判定规则\n\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| FailedScheduling + Insufficient cpu/memory | 资源不足导致 Pod Pending | 高 |\n| FailedScheduling + Too many pods | 节点 Pod 数量上限导致 Pending | 高 |\n| FailedScheduling + didn't have free ports for the requested pod ports | hostPort 端口冲突导致 Pending | 高 |\n| FailedScheduling + had untolerated taint | taint/toleration 不匹配 | 高 |\n| FailedScheduling + node(s) didn't match node selector/affinity | 调度约束不匹配 | 高 |\n| FailedScheduling + pod has unbound immediate PersistentVolumeClaims | PVC 未绑定，应切换 VolumeMountFailed/PVC 分支 | 高 |\n| 所有候选 Node NotReady/Unschedulable | 无可用调度节点 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a019dbbca07e40ff/tools/004-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a019dbbca07e40ff/tools/004-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a019dbbca07e40ff/tools/004-evidence-fetch_runbook.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAME     LABELS\\nmaster   map[beta.kubernetes.io/arch:amd64 beta.kubernetes.io/os:linux fpga-version: kubernetes.io/arch:amd64 kubernetes.io/hostname:master kubernetes.io/os:linux metax-tech.com/gpu.installed:false node-role.kubernetes.io/control-plane: node.kubernetes.io/exclude-from-external-load-balancers:]\\nnode1    map[beta.kubernetes.io/arch:amd64 beta.kubernetes.io/os:linux fpga-version: kubernetes.io/arch:amd64 kubernetes.io/hostname:node1 kubernetes.io/os:linux metax-tech.com/gpu.installed:false]\\nnode2    map[beta.kubernetes.io/arch:amd64 beta.kubernetes.io/os:linux fpga-version: kubernetes.io/arch:amd64 kubernetes.io/hostname:node2 kubernetes.io/os:linux metax-tech.com/gpu.installed:false]\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/a019dbbca07e40ff/tools/005-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/a019dbbca07e40ff/tools/005-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/a019dbbca07e40ff/tools/005-evidence-run_bash_command.summary.txt"}],"llm_analysis":"所有关键证据已采集完毕，以下是证据总结。\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据（全部验证通过）\n\n| 序号 | 证据维度 | 来源 | 结果 |\n|:---:|:---------|:-----|:-----|\n| **e1** | FailedScheduling 事件原文 | `kubectl describe pod` | ✅ `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.` |\n| **e2** | Pod YAML 确认 nodeSelector | `kubectl get pod -o yaml` | ✅ 明确配置 `nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}`，且 `phase: Pending`，`nodeName: None` |\n| **e3** | Pod 事件确认 | `kubectl_events` | ✅ 两次 FailedScheduling 事件（14m 和 3m51s），内容一致 |\n| **e4** | 节点标签检查 | `kubectl get nodes -o custom-columns` | ✅ 集群 3 个节点（master/node1/node2）均不包含标签 `aiops.e2e/nonexistent-node-label=true`，**确认为标签缺失** |\n| **e5** | Runbook 参考 | `fetch_runbook` | ✅ 匹配规则：`FailedScheduling + node(s) didn't match node selector/affinity → 调度约束不匹配（高置信度）` |\n\n### ❌ 未采集 / 冲突证据\n- 无冲突或负向证据：所有工具均正常返回，Pod 仍存在于 aiops-e2e 命名空间。\n\n### 根因结论\nPod `rc-pending-nodeselector`（命名空间 `aiops-e2e`）的 `nodeSelector` 指定了标签 **`aiops.e2e/nonexistent-node-label=true`**，而集群中 **3 个节点均无此标签**，导致调度器无法找到可匹配节点，Pod 卡在 Pending 状态。此属于典型的 **调度约束不匹配** 问题，与上游 L1 定位一致。\n\n### 建议修复方案（仅参考，不执行）\n1. **给目标节点打标签**：`kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`\n2. **或修改 Pod 的 nodeSelector**：移除或不存在的标签，改用已有标签\n3. **或删除无需的 Pod**：`kubectl delete pod rc-pending-nodeselector -n aiops-e2e`","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 7 个，匹配计划 5 个，未规划证据 2 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":7,"matched_tool_count":5,"unplanned_tool_count":2,"evidence_inventory":[{"id":"e1-pod-describe","description":"验证 Pod rc-pending-nodeselector 的当前状态、spec.nodeSelector 和 FailedScheduling 事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"确认 FailedScheduling 事件原文，验证 nodeSelector 不匹配是根因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-pod-yaml","description":"获取 Pod YAML 验证 spec.nodeSelector 具体配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"确认 nodeSelector 中使用了不存在的标签 aiops.e2e/nonexistent-node-label=true","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3-pod-events","description":"获取命名空间事件确认 FailedScheduling 详细原因","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-nodeselector","purpose":"验证 FailedScheduling 事件原文，确认调度器明确拒绝原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4-nodes-check","description":"检查集群所有节点标签，确认 aiops.e2e/nonexistent-node-label 标签不存在","level":"important","tool":"run_bash_command","command":"kubectl get nodes -o custom-columns=NAME:.metadata.name,LABELS:.metadata.labels | head -80","purpose":"验证集群节点是否缺少 nodeSelector 要求的标签，确认是调度约束不匹配","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5-runbook-ref","description":"获取 Pod PendingUnschedulable 排障参考","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","purpose":"确认 runbook 中 nodeSelector/affinity 不匹配的典型验证步骤","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1-pod-describe | critical | ✅ | kubectl_describe | 验证 Pod rc-pending-nodeselector 的当前状态、spec.nod... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e2-pod-yaml | critical | ✅ | kubectl_get_yaml | 获取 Pod YAML 验证 spec.nodeSelector 具体配置 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e3-pod-events | important | ✅ | kubectl_events | 获取命名空间事件确认 FailedScheduling 详细原因 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pendi...` |
   | e4-nodes-check | important | ✅ | run_bash_command | 检查集群所有节点标签，确认 aiops.e2e/nonexistent-node-labe... | `kubectl get nodes -o custom-columns=NAME:.metadata.name,LABELS:.metadata.labe...` |
   | e5-runbook-ref | reference | ✅ | fetch_runbook | 获取 Pod PendingUnschedulable 排障参考 | `fetch_runbook pod-pending-unschedulable.md` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (25.9s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector（命名空间 aiops-e2e）当前状态为 Pending，已持续 14 分钟以上。根本原因是 Pod 的 spec.nodeSelector 配置为 {"aiops.e2e/nonexistent-node-label": "true"}，但集群全部 3 个节点（master、node1、node2）均不包含该标签（证据 e4 节点标签检查结果确认）。调度器报告 "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"（证据 e1/e3），Pod 无法被调度到任何节点。Runbook 判定规则将此类症状标记为高置信度"调度约束不匹配"场景（证据 e5）。集群中其他 59 个 Pod 均正常运行，仅此一个 Pod 异常，属于典型的 nodeSelector 配置错误。
   confidence=98%
   causal_chain={"root_cause": "Pod rc-pending-nodeselector 的 nodeSelector 指定了标签 aiops.e2e/nonexistent-node-label=true，该标签在集群全部 3 个节点（master、node1、node2）上均不存在。", "propagation": "Pod 创建时，调度器（default-scheduler）评估所有节点，发现没有任何节点包含该 nodeSelector 标签，因此无法将 Pod 绑定到任何节点。调度器多次重试（14m 内至少 3 次），每次均因相同原因失败。", "direct_cause": "Pod 的调度约束（nodeSelector）与集群节点标签集合完全不匹配，导致调度器找不到可用节点。", "manifestation": "Pod 保持 Pending 状态超过 14 分钟，kubectl describe 和 kubectl events 持续输出 FailedScheduling 事件，提示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。"}
   rca_analysis={"phenomenon": "集群 aiops-e2e 命名空间中 Pod rc-pending-nodeselector 处于 Pending 状态，调度器持续报 FailedScheduling 事件，提示 0/3 节点可用。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod rc-pending-nodeselector 状态 Pending，nodeSelector 为 aiops.e2e/nonexistent-node-label=true，FailedScheduling 事件: 3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml", "content": "Pod YAML 确认 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}，phase: Pending，nodeName: None", "reliability": "高"}, {"id": "e3", "source": "kubectl_events", "content": "两次 FailedScheduling 事件（14m 前和 3m51s 前），内容一致：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}, {"id": "e4", "source": "kubectl_get_nodes_labels", "content": "集群 3 个节点（master/node1/node2）均不包含标签 aiops.e2e/nonexistent-node-label=true", "reliability": "高"}, {"id": "e5", "source": "fetch_runbook", "content": "Runbook 匹配规则：FailedScheduling + node(s) didn't match node selector/affinity → 调度约束不匹配（高置信度）", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "nodeSelector: aiops.e2e/nonexistent-node-label=true; FailedScheduling: 3 node(s) didn't match Pod's node affinity/selector", "interpretation": "Pod 明确使用了 nodeSelector 约束指定一个标签，而调度器报告所有 3 个节点都不满足该约束，说明该标签在集群中不存在。"}, {"evidence_id": "e2", "raw_data": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}; phase: Pending; nodeName: None", "interpretation": "Pod YAML 确认 nodeSelector 具体配置为 aiops.e2e/nonexistent-node-label=true，Pod 尚未绑定任何节点（nodeName 为空），与 Pending 状态一致。"}, {"evidence_id": "e3", "raw_data": "14m Warning FailedScheduling; 3m51s (x2) Warning FailedScheduling; 内容完全一致", "interpretation": "调度器重试了至少 3 次（14m + 2次在 8m51s 窗口内），每次都因相同原因失败，排除瞬态问题，确认为持续配置性故障。"}, {"evidence_id": "e4", "raw_data": "master: [beta.kubernetes.io/arch, beta.kubernetes.io/os, kubernetes.io/hostname, ...]; node1: [...]; node2: [...] — 均无 aiops.e2e/nonexistent-node-label", "interpretation": "集群 3 个节点的标签清单中均不包含 aiops.e2e/nonexistent-node-label 标签，直接证实了 nodeSelector 引用了不存在的标签。"}, {"evidence_id": "e5", "raw_data": "判定规则：FailedScheduling + node(s) didn't match node selector/affinity → 调度约束不匹配（高置信度）", "interpretation": "Runbook 明确将当前证据组合归类为高置信度的调度约束不匹配场景，与现场症状完全一致。"}], "causal_chain": {"root_cause": "Pod rc-pending-nodeselector 的 nodeSelector 指定了标签 aiops.e2e/nonexistent-node-label=true，该标签在集群全部 3 个节点（master、node1、node2）上均不存在。", "propagation": "Pod 创建时，调度器（default-scheduler）评估所有节点，发现没有任何节点包含该 nodeSelector 标签，因此无法将 Pod 绑定到任何节点。调度器多次重试（14m 内至少 3 次），每次均因相同原因失败。", "direct_cause": "Pod 的调度约束（nodeSelector）与集群节点标签集合完全不匹配，导致调度器找不到可用节点。", "manifestation": "Pod 保持 Pending 状态超过 14 分钟，kubectl describe 和 kubectl events 持续输出 FailedScheduling 事件，提示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。"}, "root_cause": "Pod rc-pending-nodeselector（命名空间 aiops-e2e）当前状态为 Pending，已持续 14 分钟以上。根本原因是 Pod 的 spec.nodeSelector 配置为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}，但集群全部 3 个节点（master、node1、node2）均不包含该标签（证据 e4 节点标签检查结果确认）。调度器报告 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"（证据 e1/e3），Pod 无法被调度到任何节点。Runbook 判定规则将此类症状标记为高置信度\"调度约束不匹配\"场景（证据 e5）。集群中其他 59 个 Pod 均正常运行，仅此一个 Pod 异常，属于典型的 nodeSelector 配置错误。", "root_cause_summary": "Pod rc-pending-nodeselector（命名空间 aiops-e2e）当前状态为 Pending，已持续 14 分钟以上。根本原因是 Pod 的 spec.nodeSelector 配置为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}，但集群全部 3 个节点（master、node1、node2）均不包含该标签（证据 e4 节点标签检查结果确认）。调度器报告 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"（证据 e1/e3），Pod 无法被调度到任何节点。Runbook 判定规则将此类症状标记为高置信度\"调度约束不匹配\"场景（证据 e5）。集群中其他 59 个 Pod 均正常运行，仅此一个 Pod 异常，属于典型的 nodeSelector 配置错误。", "confidence": 0.98, "confidence_reason": "所有关键证据（Pod 状态、nodeSelector 配置、FailedScheduling 事件原文、节点标签清单、Runbook 判定规则）均一致指向同一个根因，因果链完整无断裂。证据全部为直接工具输出，无推测成分。置信度 0.98，留 0.02 裕度应对极小概率的标签一致性延迟问题（已排除，因事件已持续 14 分钟）。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "集群资源不足（CPU/内存不足）", "probability": "很低", "reason": "FailedScheduling 事件原文为 'didn't match Pod's node affinity/selector' 而非 'Insufficient cpu/memory'，且集群 59 个 Running Pod 表明资源充足，排除。"}, {"cause": "节点 taint/toleration 不匹配", "probability": "很低", "reason": "FailedScheduling 事件没有包含 'had untolerated taint' 关键词，且 Pod 已配置 tolerations（node.kubernetes.io/not-ready:NoExecute），排除。"}, {"cause": "PVC 未绑定", "probability": "很低", "reason": "FailedScheduling 事件没有包含 'unbound immediate PersistentVolumeClaims'，Pod 仅使用 kube-api-access 投影卷，无需 PVC，排除。"}, {"cause": "节点不可调度（NotReady/Unschedulable）", "probability": "很低", "reason": "事件没有报告节点状态异常，集群其他 59 个 Running Pod 分布在 3 个节点上，证明所有节点可正常调度，排除。"}], "limitations": "未采集每个节点的完整 taint 清单（已通过 FailedScheduling 原文关键词排除 taint 场景），未采集 PVC/PV 状态（Pod 无需 PVC，已通过事件原文排除）。所有关键证据充分，无实质性局限。", "llm_raw_analysis": "## 证据清点\\n共采集 5 个关键证据：\\n- e1 (kubectl_describe): Pod Pending, nodeSelector=aiops.e2e/nonexistent-node-label=true, FailedScheduling\\n- e2 (kubectl_get_yaml): 确认 nodeSelector 配置, phase=Pending, nodeName=None\\n- e3 (kubectl_events): 两次 FailedScheduling, 内容一致\\n- e4 (kubectl_get_nodes_labels): 3 节点均无该标签\\n- e5 (fetch_runbook): 匹配高置信度调度约束不匹配规则\\n\\n## 逐条分析\\ne1: 调度器明确说所有3个节点不匹配node affinity/selector，结合nodeSelector字段指向特定标签\\ne2: YAML确认该标签键值对，且Pod未绑定任何节点\\ne3: 多次重试均失败，排除瞬态\\ne4: 直接证明标签不存在\\ne5: 规则验证\\n\\n## 关联分析\\n\n... 截断，原始 653 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector（命名空间 aiops-e2e）当前状态为 Pending，已持续 14 分钟以上。根本原因是 Pod 的 spec.nodeSelector 配置为 {"aiops.e2e/nonexistent-node-label": "true"}，但集...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod rc-pending-nodeselector 的 nodeSelector 指定了标签 aiops.e2e/nonexistent-node-label=true，该标签在集群全部 3 个节点（master、node1、node2）上均不存在。
     传导机制: Pod 创建时，调度器（default-scheduler）评估所有节点，发现没有任何节点包含该 nodeSelector 标签，因此无法将 Pod 绑定到任何节点。调度器多次重试（14m 内至少 3 次），每次均因相同原因失败。
     最终表现: Pod 保持 Pending 状态超过 14 分钟，kubectl describe 和 kubectl events 持续输出 FailedScheduling 事件，提示 '0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector'。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (24.2s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5188 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 32.2s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将为您分析集群状况。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **集群状态** | 集群整体运行正常，`65` 个 Pod 中 `59` 个处于 `Running` 状态。存在 **1 个异常 Pod**。 |
| **异常 Pod 详情** | Pod `rc-pending-nodeselector` 处于 **`Pending`** 状态，无法被调度。 |
| **兼容归因层** | L1 - 调度层 |
| **问题分类** | `PendingUnschedulable` (调度约束不匹配) |
| **置信度** | 高 (98%) |
| **证据完整度** | 4/4 (100%) |

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 异常 Pod | `rc-pending-nodeselector` |
| Namespace | `aiops-e2e` |
| 影响范围 | 1 个 Pod 异常，集群其余 59 个 Pod 均正常运行 |
| 核心现象 | Pod 处于 `Pending` 状态，调度器持续报告失败 |

**汇总**：您的集群整体健康，只有一个测试用途的 Pod 因配置错误无法启动。

---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod` | `Status: Pending`；`Warning FailedScheduling 14m default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | Pod 处于 Pending 状态，根本原因是调度约束不匹配。 |
| 2 | Pod 配置 | `kubectl get pod -o yaml` | `phase: Pending`；`Node-Selectors: aiops.e2e/nonexistent-node-label=true` | Pod 的 `nodeSelector` 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label=true`。 |
| 3 | 集群事件 | `kubectl events` | `14m Warning FailedScheduling Pod/rc-pending-nodeselector 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 调度器在 14 分钟内至少尝试了 3 次，每次都因节点不匹配 `nodeSelector` 而失败。 |
| 4 | 节点标签 | `run_bash_command` | `NAME LABELS master map[kubernetes.io/hostname:master...] node1 map[...] node2 map[...]` (未包含 `aiops.e2e/nonexistent-node-label`) | 集群中 3 个节点的标签列表均不包含 `aiops.e2e/nonexistent-node-label` 标签。 |
| 5 | 排障参考 | `fetch_runbook` | `<runbook> # Pod PendingUnschedulable / 调度失败 ... 调度约束: nodeSelector/affinity 不匹配 ...` | 当前现象与 runbook 中描述的 “调度约束不匹配” 场景完全吻合。 |

### 证据关联分析
- **证据 #1 + #2 + #3 + #4 印证**：Pod YAML 配置了 `nodeSelector: {aiops.e2e/nonexistent-node-label: true}` **(#2)** → 调度器评估所有 3 个节点时发现该标签不存在 **(#4)** → 持续 14 分钟报告 `FailedScheduling` 错误，提示节点不匹配 `nodeSelector` **(#1, #3)** → Pod 无法调入任何节点，持续 Pending **(#1)**。

### 缺失证据
**无**。所有关键证据均已采集完毕，问题根因明确。

---
## 🎯 根因分析

### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                    │
│ Pod rc-pending-nodeselector 的 nodeSelector 指定了一个集群中不存在的标签。    │
│ 标签: aiops.e2e/nonexistent-node-label=true                                 │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                     │
│ Pod 创建 → 调度器列举所有节点 → 检查节点标签是否匹配 nodeSelector → 无一匹配 │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                     │
│ 调度器无法找到满足 Pod 调度约束 (nodeSelector) 的节点，持续失败。              │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                 │
│ Pod 状态为 Pending，event 持续产生 FailedScheduling 事件。                    │
└──────────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：集群整体健康，仅一个测试 Pod 存在配置问题。根据证据 #2 (YAML `nodeSelector`) 和证据 #4 (节点标签检查)，Pod `rc-pending-nodeselector` 持续 `Pending` 的根本原因是**其 `spec.nodeSelector` 配置了 `aiops.e2e/nonexistent-node-label=true`，该标签在集群全部 3 个节点上均不存在，导致调度器无法找到匹配节点**。

**置信度**：高 (98%)
- ✅ `FailedScheduling` 事件明确指向 `node affinity/selector` 不匹配
- ✅ Pod YAML 和节点标签信息直接证实了不匹配的存在
- ✅ 集群其他 59 个 Pod 正常运行，排除了集群资源不足或节点故障的可能

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [必须] 删除或修改 Pod 配置，移除不存在的 `nodeSelector` 约束**
- **方案 A（推荐）**：删除这个测试 Pod，如果需要重新创建，使用正确的配置。
  ```bash
  kubectl delete pod rc-pending-nodeselector -n aiops-e2e
  ```
- **方案 B**：如果这是由 Deployment 等控制器管理，可以更新控制器模板。
  ```bash
  # 假设由 Deployment 管理 (当前问题中 Pod 直接创建，此命令仅供参考)
  # kubectl edit deployment <deployment-name> -n aiops-e2e
  ```
  **依据**：移除不存在的 `nodeSelector` 约束后，调度器即可将 Pod 调度到任意可用节点。

**2. [可选] 创建 Pod 时使用正确的节点标签**
如果确实需要将 Pod 调度到特定节点，请先确认正确的节点标签，再创建 Pod。
```bash
# 查看集群所有节点及其标签
kubectl get nodes --show-labels
```
**目的**：从源头避免配置错误。

### 后续优化
1. **代码与配置审查**：在 CI/CD 流程或配置模板中增加对 `nodeSelector`、`affinity` 等调度规则的静态检查，确保引用的标签在目标集群中真实存在。
2. **监控与告警**：对 `Pending` 状态的 Pod 配置告警，以便在问题发生时第一时间介入。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 被删除 | `kubectl get pod -n aiops-e2e \| grep rc-pending-nodeselector` | 无输出 (Pod 已不存在) |
| 2. 重新创建正确 Pod (如果必要) | `kubectl run rc-pending-nodeselector --image=nginx -n aiops-e2e` | `pod/rc-pending-nodeselector created` |
| 3. 检查新 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | `STATUS: Running` |

---
## ⚠️ 注意事项
- **该 Pod 无实际影响**：此异常 Pod `rc-pending-nodeselector` 是一个由 `rootcause-e2e=true` 标签标记的端到端测试 Pod，不服务于任何生产应用，它当前的状态不会影响集群中其他 59 个正常运行的负载。
- **集群本身无问题**：所有 3 个节点均健康且资源充足，问题完全出在 Pod 的配置错误上。

---

## 📊 性能统计

├─ 总耗时: 1.5m
├─ 问题定位: 20.4s (22%) ✅
├─ 证据链采集: 21.7s (24%) ✅
├─ 根因分析: 25.9s (28%) ✅
├─ 汇总总结: 24.2s (26%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 9 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 9 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
