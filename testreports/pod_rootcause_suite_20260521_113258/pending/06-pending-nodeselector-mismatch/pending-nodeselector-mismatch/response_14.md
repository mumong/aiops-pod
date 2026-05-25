======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 113cd7c49d194bae]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先从全局 Pod 状态扫描开始，看看集群中所有 Pod 的当前状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 发现了一个异常 Pod。让我进一步查看这个 Pending Pod 的详细信息，以及它的异常类型标签。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  9m21s  default-scheduler  0/3 nodes are available: 3 node(s) di
   💭 [问题定位] 很好，我已经获取了足够的信息来进行定位分析。现在让我拉取匹配的 runbook 作为参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 我已经完成全局扫描和异常定位，现在进行分析总结。

---

## 诊断分析结果

### 全局 Pod 概况

| 项目 | 数值 |
|------|------|
| 集群 Pod 总数 | **65** |
| 正常运行 Pod (Running/Ready) | **59** |
| Pending (调度失败) | **1** |
| 其他异常 | **0** |

### 异常 Pod 详情

| 字段 | 值 |
|------|-----|
| **Pod 名称** | `rc-pending-nodeselector` |
| **命名空间** | `aiops-e2e` |
| **STATUS** | `Pending` |
| **Node** | 未绑定 (无 Node) |
| **异常类型标签** | `pod_abnormal_type=PendingUnschedulable` |

### 异常证据与根因定位

**FailedScheduling 关键信息：**
```
0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.
```

**根因：Pod 的 nodeSelector 约束没有匹配到任何节点**

Pod 设置了以下调度约束：
- `Node-Selectors: aiops.e2e/nonexistent-node-label=true` — 这是一个**不存在的节点标签**，集群中 3 个节点均无此标签，导致所有节点都不满足调度条件。

### 输出结构化结果

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **层名称** | PendingUnschedulable |
| **状态关键字** | Pending |
| **异常类型** | PendingUnschedulable |
| **状态分类** | scheduling |
| **置信度** | 高 |
| **异常 Pod 数** | 1 |
| **异常组** | PendingUnschedulable |

### 可能场景

1. **nodeSelector 配置错误** — `aiops.e2e/nonexistent-node-label=true` 标签在集群节点上不存在，导致 Pod 无法调度到任何节点。
2. **节点标签缺失** — 预期该标签应存在于某些节点上，但尚未被标记。

### 后续建议审查方向

- 检查节点标签列表，确认是否需要为特定节点打上该标签
- 验证 Pod yaml 中 `nodeSelector` 的值是否拼写正确
- 如该标签确实不应该存在，移除 nodeSelector 或改用 nodeAffinity 实现更灵活的调度策略
   ✅ [问题定位] 完成 (22.8s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector配置错误', 'probability': '高', 'reason': 'Pod设置了aiops.e2e/nonexistent-node-label=true标签选择器，集群3个节点均无此标签，导致调度约束无法满足'}, {'scenario': '节点标签缺失', 'probability': '中', 'reason': '预期该标签可能应存在于某些节点上，但尚未被标记'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}]
   reasoning=集群中存在1个异常Pod（rc-pending-nodeselector, namespace: aiops-e2e），状态为Pending，事件明确显示FailedScheduling：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod设置了nodeSelector为aiops.e2e/nonexistent-node-label=true，该标签在集群3个节点上均不存在，导致Pod无法调度到任何节点。符合L1层调度约束不匹配的特征，状态关键字为Pending，异常类型为PendingUnschedulable，状态分类为scheduling。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "集群中存在1个异常Pod（rc-pending-nodeselector, namespace: aiops-e2e），状态为Pending，事件明确显示FailedScheduling：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod设置了nodeSelector为aiops.e2e/nonexistent-node-label=true，该标签在集群3个节点上均不存在，导致Pod无法调度到任何节点。符合L1层调度约束不匹配的特征，状态关键字为Pending，异常类型为PendingUnschedulable，状态分类为scheduling。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "nodeSelector配置错误", "probability": "高", "reason": "Pod设置了aiops.e2e/nonexistent-node-label=true标签选择器，集群3个节点均无此标签，导致调度约束无法满足"}, {"scenario": "节点标签缺失", "probability": "中", "reason": "预期该标签可能应存在于某些节点上，但尚未被标记"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              9m19s   <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/113cd7c49d194bae/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/113cd7c49d194bae/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/113cd7c49d194bae/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来执行既有 evidence_plan 中的工具调用。先启动最高优先级的 critical 工具：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  9m50s  default-scheduler  0/3 nodes are available: 3 node(s) di
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:18:44Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [证据链采集] Critical 级工具已完成。现在继续执行 important 级工具：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
9m53s       Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAME     STATUS   ROLES           AGE    VERSION   LABELS\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpg
   💭 [证据链采集] 最后，按计划拉取 runbook 作为 reference 对比验证：
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [证据链采集] ## 证据采集结论

### ✅ 已采集证据

| # | 证据项 | 工具 | 结果 |
|---|--------|------|------|
| **e1** | Pod 状态与调度事件 | `kubectl_describe` | Pod `rc-pending-nodeselector` 处于 **Pending** 状态，QoS Class: BestEffort，绑定节点: **<none>**。Events 中 2 次 `FailedScheduling`：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` |
| **e2** | Pod YAML 调度约束 | `kubectl_get_yaml` | `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}`，`imagePullPolicy=Never`，`phase: Pending`，`condition: PodScheduled=False, reason=Unschedulable` |
| **e3** | 集群节点标签 | `run_bash_command` | 集群 3 个节点（master/node1/node2）全部 **Ready** 状态，但**没有任何节点**包含 `aiops.e2e/nonexistent-node-label` 标签。节点标签中没有匹配的 key |
| **e4** | Namespace 事件 | `kubectl_events` | Pod 唯一事件为 `FailedScheduling`，无其他异常事件。namespace 无其他异常 |
| **e6** | Runbook 匹配验证 | `fetch_runbook` | 当前证据与 Runbook 中 **"nodeSelector/affinity 不匹配"** 分支完全吻合：`FailedScheduling + didn't match Pod's node affinity/selector` |

### 🔍 根因结论

**调度约束不匹配**：Pod `rc-pending-nodeselector` 设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，但集群 3 个节点（master、node1、node2）**均不存在此标签**。调度器无法找到任何满足条件的节点，导致 Pod 持续 Pending。

### ⚠️ 无冲突/负向证据

所有工具返回结果一致，Namespace 匹配，Pod 存在，状态与上游描述一致。
   ✅ [证据链采集] 完成 (22.6s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1-pod-describe","description":"验证 Pod rc-pending-nodeselector 当前状态和 FailedScheduling 事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"获取当前 Pod 状态、Events 中的 FailedScheduling 原因，验证 upstream 已发现的 nodeSelector 不匹配是否仍然存在","evidence_type":"status_and_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2-pod-yaml","description":"获取 Pod 完整 YAML 以验证 nodeSelector 配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"检查 Pod spec 中的 nodeSelector、affinity、tolerations 等调度约束配置","evidence_type":"config","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3-node-list","description":"查看集群节点及其标签，验证节点是否缺少期望标签","level":"important","tool":"run_bash_command","command":"kubectl get nodes --show-labels","tool_args":{},"purpose":"检查集群中所有节点的标签，验证是否任何节点具有 aiops.e2e/nonexistent-node-label=true 标签，以及节点状态是否正常","evidence_type":"node_labels","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4-events","description":"从 namespace 层面获取事件，聚焦节点调度相关异常","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e"},"purpose":"收集 aiops-e2e namespace 中最近的事件，验证除 FailedScheduling 外是否存在其他异常事件","evidence_type":"events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e6-runbook-ref","description":"参考已确认的 runbook 验证调度约束不匹配场景","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","tool_args":{},"purpose":"将当前发现与 runbook 中 FailedScheduling + node selector/affinity 不匹配分支对比验证","evidence_type":"reference","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  9m50s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  4m21s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  9m50s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  4m21s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/113cd7c49d194bae/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/113cd7c49d194bae/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/113cd7c49d194bae/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/113cd7c49d194bae/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/113cd7c49d194bae/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/113cd7c49d194bae/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n9m53s       Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n4m24s       Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/113cd7c49d194bae/tools/003-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/113cd7c49d194bae/tools/003-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/113cd7c49d194bae/tools/003-evidence-kubectl_events.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAME     STATUS   ROLES           AGE    VERSION   LABELS\\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\\nnode1    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\nnode2    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/113cd7c49d194bae/tools/004-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/113cd7c49d194bae/tools/004-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/113cd7c49d194bae/tools/004-evidence-run_bash_command.summary.txt"},{"tool":"fetch_runbook","data":"<runbook>\n# Pod PendingUnschedulable / 调度失败\n\n> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling\n\n## 场景识别\n\n| 信号 | 关键特征 |\n|------|----------|\n| Pod 状态 | Pending，且 Events 含 `FailedScheduling` |\n| 资源不足 | `Insufficient cpu/memory/ephemeral-storage`、`Too many pods` |\n| 调度约束 | nodeSelector/affinity 不匹配、节点 taint 未被 toleration 容忍 |\n| 存储前置条件 | `pod has unbound immediate PersistentVolumeClaims` 应切换到 pod-volume-mount-failed |\n| 节点状态 | Node NotReady/Unknown、SchedulingDisabled、Unschedulable 会导致无可用调度节点 |\n\n## 根因分流\n- 资源不足: FailedScheduling 原文含 Insufficient cpu/memory/ephemeral-storage、Too many pods。\n- hostPort 冲突: 原文含 `didn't have free ports for the requested pod ports`，说明目标节点端口已被占用。\n- Taint/Toleration 不匹配: 原文含 `had untolerated taint`，必须检查 Pod tolerations 和 Node taints。\n- nodeSelector / nodeAffinity / podAffinity 不匹配: 原文含 `didn't match Pod's node affinity/selector` 或 affinity/anti-affinity。\n- PVC 未绑定: 原文含 `unbound immediate PersistentVolumeClaims`，根因在存储绑定而不是调度资源。\n- 节点不可调度: Node Ready=False/Unknown、SchedulingDisabled、`node.kubernetes.io/not-ready` 或 `node.kubernetes.io/unreachable`。\n- 镜像、挂载、容器启动错误不会表现为 FailedScheduling；如果 Pod 已绑定 nodeName，应切换到对应 runbook。\n\n## 诊断流程\n\n### Step 1: 确认 Pod 调度失败事件\n```bash\nkubectl describe pod <pod-name> -n <namespace>\n```\n关注 Events 中的 `FailedScheduling` 原文。\n\n### Step 2: 检查 Pod 调度约束\n```bash\nkubectl get pod <pod-name> -n <namespace> -o yaml\n```\n关注: spec.nodeName 是否为空、nodeSelector、affinity、tolerations、topologySpreadConstraints、schedulerName、priorityClassName、resource requests、hostNetwork/hostPort。\n\n### Step 3: 检查节点状态和可调度性\n```bash\nkubectl get nodes -o wide\n```\n关注: STATUS 列是否有 NotReady/Unknown，AGE 判断是否新节点\n\n### Step 4: 检查候选节点详情\n```bash\nkubectl describe node <node-name>\n```\n重点关注:\n- `Conditions` 部分: Ready=False/Unknown 的 reason 和 message\n- `Taints` 部分: 是否有 NoSchedule/NoExecute taint\n- `Allocatable` vs `Capacity`: 资源是否耗尽\n- `Non-terminated Pods`: 节点上运行的 Pod 数量\n\n### Step 5: 检查 PVC 状态（如果 FailedScheduling 指向 PVC）\n```bash\nkubectl get pvc -n <namespace>\nkubectl describe pvc <pvc> -n <namespace>\n```\n关注: Pending、StorageClass、volumeBindingMode、ProvisioningFailed。\n\n### Step 6: 检查 Ready 条件详情\n```bash\nkubectl get node <node-name> -o jsonpath='{.status.conditions[?(@.type==\"Ready\")]}' | python3 -m json.tool\n```\n关注: status, reason, message, lastHeartbeatTime\n\n### Step 7: 检查节点事件\n```bash\nkubectl get events -A --field-selector involvedObject.kind=Node,involvedObject.name=<node-name> --sort-by='.lastTimestamp'\n```\n关注: NodeNotReady、NodeNotSchedulable、PLEG unhealthy 等事件\n\n### Step 8: 检查受影响的 Pending Pod\n```bash\nkubectl get pods -A --field-selector status.phase=Pending | head -20\n```\n\n## 判定规则\n\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| FailedScheduling + Insufficient cpu/memory | 资源不足导致 Pod Pending | 高 |\n| FailedScheduling + Too many pods | 节点 Pod 数量上限导致 Pending | 高 |\n| FailedScheduling + didn't have free ports for the requested pod ports | hostPort 端口冲突导致 Pending | 高 |\n| FailedScheduling + had untolerated taint | taint/toleration 不匹配 | 高 |\n| FailedScheduling + node(s) didn't match node selector/affinity | 调度约束不匹配 | 高 |\n| FailedScheduling + pod has unbound immediate PersistentVolumeClaims | PVC 未绑定，应切换 VolumeMountFailed/PVC 分支 | 高 |\n| 所有候选 Node NotReady/Unschedulable | 无可用调度节点 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/113cd7c49d194bae/tools/005-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/113cd7c49d194bae/tools/005-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/113cd7c49d194bae/tools/005-evidence-fetch_runbook.summary.txt"}],"llm_analysis":"## 证据采集结论\n\n### ✅ 已采集证据\n\n| # | 证据项 | 工具 | 结果 |\n|---|--------|------|------|\n| **e1** | Pod 状态与调度事件 | `kubectl_describe` | Pod `rc-pending-nodeselector` 处于 **Pending** 状态，QoS Class: BestEffort，绑定节点: **<none>**。Events 中 2 次 `FailedScheduling`：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` |\n| **e2** | Pod YAML 调度约束 | `kubectl_get_yaml` | `nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}`，`imagePullPolicy=Never`，`phase: Pending`，`condition: PodScheduled=False, reason=Unschedulable` |\n| **e3** | 集群节点标签 | `run_bash_command` | 集群 3 个节点（master/node1/node2）全部 **Ready** 状态，但**没有任何节点**包含 `aiops.e2e/nonexistent-node-label` 标签。节点标签中没有匹配的 key |\n| **e4** | Namespace 事件 | `kubectl_events` | Pod 唯一事件为 `FailedScheduling`，无其他异常事件。namespace 无其他异常 |\n| **e6** | Runbook 匹配验证 | `fetch_runbook` | 当前证据与 Runbook 中 **\"nodeSelector/affinity 不匹配\"** 分支完全吻合：`FailedScheduling + didn't match Pod's node affinity/selector` |\n\n### 🔍 根因结论\n\n**调度约束不匹配**：Pod `rc-pending-nodeselector` 设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，但集群 3 个节点（master、node1、node2）**均不存在此标签**。调度器无法找到任何满足条件的节点，导致 Pod 持续 Pending。\n\n### ⚠️ 无冲突/负向证据\n\n所有工具返回结果一致，Namespace 匹配，Pod 存在，状态与上游描述一致。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 6 个，匹配计划 5 个，未规划证据 1 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":6,"matched_tool_count":5,"unplanned_tool_count":1,"evidence_inventory":[{"id":"e1-pod-describe","description":"验证 Pod rc-pending-nodeselector 当前状态和 FailedScheduling 事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"获取当前 Pod 状态、Events 中的 FailedScheduling 原因，验证 upstream 已发现的 nodeSelector 不匹配是否仍然存在","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-pod-yaml","description":"获取 Pod 完整 YAML 以验证 nodeSelector 配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"检查 Pod spec 中的 nodeSelector、affinity、tolerations 等调度约束配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3-node-list","description":"查看集群节点及其标签，验证节点是否缺少期望标签","level":"important","tool":"run_bash_command","command":"kubectl get nodes --show-labels","purpose":"检查集群中所有节点的标签，验证是否任何节点具有 aiops.e2e/nonexistent-node-label=true 标签，以及节点状态是否正常","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4-events","description":"从 namespace 层面获取事件，聚焦节点调度相关异常","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --sort-by='.lastTimestamp'","purpose":"收集 aiops-e2e namespace 中最近的事件，验证除 FailedScheduling 外是否存在其他异常事件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e6-runbook-ref","description":"参考已确认的 runbook 验证调度约束不匹配场景","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","purpose":"将当前发现与 runbook 中 FailedScheduling + node selector/affinity 不匹配分支对比验证","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1-pod-describe | critical | ✅ | kubectl_describe | 验证 Pod rc-pending-nodeselector 当前状态和 FailedSc... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e2-pod-yaml | critical | ✅ | kubectl_get_yaml | 获取 Pod 完整 YAML 以验证 nodeSelector 配置 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e3-node-list | important | ✅ | run_bash_command | 查看集群节点及其标签，验证节点是否缺少期望标签 | `kubectl get nodes --show-labels` |
   | e4-events | important | ✅ | kubectl_events | 从 namespace 层面获取事件，聚焦节点调度相关异常 | `kubectl get events -n aiops-e2e --sort-by='.lastTimestamp'` |
   | e6-runbook-ref | reference | ✅ | fetch_runbook | 参考已确认的 runbook 验证调度约束不匹配场景 | `fetch_runbook pod-pending-unschedulable.md` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (19.1s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector（namespace: aiops-e2e）处于 Pending 状态，根因为 nodeSelector 配置错误。Pod YAML 中 nodeSelector 设置为 {"aiops.e2e/nonexistent-node-label": "true"}（证据 e2），集群 3 个节点（master, node1, node2）的标签列表均不包含 aiops.e2e/nonexistent-node-label 标签（证据 e3）。调度器排除所有节点，Events 中 2 次 FailedScheduling 均报 "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"（证据 e1、e4）。无其他异常 Pod、节点均 Ready，排除了资源不足、taint/toleration 不匹配、PVC 未绑定等其他场景。
   confidence=98%
   causal_chain={"root_cause": "Pod rc-pending-nodeselector 的 nodeSelector 配置为 aiops.e2e/nonexistent-node-label=true，而集群 3 个节点（master、node1、node2）均不存在该标签", "propagation": "调度器在过滤节点时，检查每个节点的标签是否匹配 Pod 的 nodeSelector → 3 个节点均不匹配 → 无可用节点 → Pod 进入 Pending 状态，调度器反复重试仍失败", "direct_cause": "Pod 设置了节点不存在的 nodeSelector 标签 aiops.e2e/nonexistent-node-label=true，导致所有节点被调度器过滤掉", "manifestation": "Pod rc-pending-nodeselector（namespace: aiops-e2e）持续 Pending，Events 显示 FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"}
   rca_analysis={"phenomenon": "集群 aiops-e2e 命名空间下 Pod rc-pending-nodeselector 处于 Pending 状态，无法调度到任何节点。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod rc-pending-nodeselector 状态 Pending，节点 <none>，Events 中 2 次 FailedScheduling：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml", "content": "Pod YAML 中 nodeSelector 配置为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}，phase: Pending，condition PodScheduled=False, reason=Unschedulable", "reliability": "高"}, {"id": "e3", "source": "run_bash_command (kubectl get nodes)", "content": "集群 3 个节点（master, node1, node2）均为 Ready 状态，但均不包含 aiops.e2e/nonexistent-node-label 标签", "reliability": "高"}, {"id": "e4", "source": "kubectl_events", "content": "Namespace aiops-e2e 中 Pod 唯一事件为 FailedScheduling，无其他异常事件", "reliability": "高"}, {"id": "e6", "source": "fetch_runbook", "content": "Runbook 确认 FailedScheduling + didn't match Pod's node affinity/selector 对应 nodeSelector/affinity 不匹配场景", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "kubectl_describe 摘要: status=Pending, node=<none>, Warning FailedScheduling 9m50s 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "interpretation": "Pod 无法调度到任何节点，调度器明确报告节点与 Pod 的 node affinity/selector 不匹配，排除了资源不足、taint 不匹配等其他场景"}, {"evidence_id": "e2", "raw_data": "kubectl_get_yaml: nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}, phase: Pending, condition: PodScheduled=False, reason=Unschedulable", "interpretation": "Pod 明确设置了 nodeSelector，要求节点包含 aiops.e2e/nonexistent-node-label=true 标签；PodScheduled=False 且 reason=Unschedulable 证实调度失败"}, {"evidence_id": "e3", "raw_data": "stdout: master Labels=..., node1 Labels=..., node2 Labels=... 全部不含 aiops.e2e/nonexistent-node-label", "interpretation": "集群 3 个节点（master/node1/node2）均为 Ready 可调度状态，但没有任何节点拥有 Pod 所需的 aiops.e2e/nonexistent-node-label 标签，直接导致调度约束无法满足"}, {"evidence_id": "e4", "raw_data": "kubectl_events 摘要: 仅 2 条 FailedScheduling 事件，无其他 Warning/Error", "interpretation": "Namespace 层面无其他异常事件（如节点 NotReady、PVC 绑定失败等），排除并发故障干扰"}, {"evidence_id": "e6", "raw_data": "Runbook 判定规则: FailedScheduling + node(s) didn't match node selector/affinity -> 调度约束不匹配，置信度高", "interpretation": "当前证据完全匹配 runbook 中 nodeSelector/affinity 不匹配分支，根因判定规则得到验证"}], "causal_chain": {"root_cause": "Pod rc-pending-nodeselector 的 nodeSelector 配置为 aiops.e2e/nonexistent-node-label=true，而集群 3 个节点（master、node1、node2）均不存在该标签", "propagation": "调度器在过滤节点时，检查每个节点的标签是否匹配 Pod 的 nodeSelector → 3 个节点均不匹配 → 无可用节点 → Pod 进入 Pending 状态，调度器反复重试仍失败", "direct_cause": "Pod 设置了节点不存在的 nodeSelector 标签 aiops.e2e/nonexistent-node-label=true，导致所有节点被调度器过滤掉", "manifestation": "Pod rc-pending-nodeselector（namespace: aiops-e2e）持续 Pending，Events 显示 FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"}, "root_cause": "Pod rc-pending-nodeselector（namespace: aiops-e2e）处于 Pending 状态，根因为 nodeSelector 配置错误。Pod YAML 中 nodeSelector 设置为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}（证据 e2），集群 3 个节点（master, node1, node2）的标签列表均不包含 aiops.e2e/nonexistent-node-label 标签（证据 e3）。调度器排除所有节点，Events 中 2 次 FailedScheduling 均报 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"（证据 e1、e4）。无其他异常 Pod、节点均 Ready，排除了资源不足、taint/toleration 不匹配、PVC 未绑定等其他场景。", "root_cause_summary": "Pod rc-pending-nodeselector（namespace: aiops-e2e）处于 Pending 状态，根因为 nodeSelector 配置错误。Pod YAML 中 nodeSelector 设置为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}（证据 e2），集群 3 个节点（master, node1, node2）的标签列表均不包含 aiops.e2e/nonexistent-node-label 标签（证据 e3）。调度器排除所有节点，Events 中 2 次 FailedScheduling 均报 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"（证据 e1、e4）。无其他异常 Pod、节点均 Ready，排除了资源不足、taint/toleration 不匹配、PVC 未绑定等其他场景。", "confidence": 0.98, "confidence_reason": "所有证据完全一致，因果链清晰完整：e2 确定 nodeSelector 配置、e3 确认节点无此标签、e1/e4 确认调度失败事件原文、e6 确认 runbook 匹配。证据完整覆盖根因诊断全链路，无冲突或负向证据。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "集群资源不足（CPU/内存不足）", "probability": "low", "reason": "FailedScheduling 原文未含 Insufficient cpu/memory，明确为 didn't match Pod's node affinity/selector"}, {"cause": "节点 taint/toleration 不匹配", "probability": "low", "reason": "FailedScheduling 原文未含 had untolerated taint，且 Pod 已有 tolerations 配置"}, {"cause": "PVC 未绑定导致调度失败", "probability": "low", "reason": "FailedScheduling 原文未含 unbound immediate PersistentVolumeClaims，且 Pod 无 PVC 卷"}, {"cause": "节点不可调度（NotReady）", "probability": "low", "reason": "证据 e3 显示 3 个节点均为 Ready 状态"}], "limitations": "未检查节点的完整 allocatable 资源（CPU/memory）和运行 Pod 数量，但 FailedScheduling 原文已明确指向 node affinity/selector 不匹配，而非资源不足，因此不影响根因判定。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector（namespace: aiops-e2e）处于 Pending 状态，根因为 nodeSelector 配置错误。Pod YAML 中 nodeSelector 设置为 {"aiops.e2e/nonexistent-node-label": ...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod rc-pending-nodeselector 的 nodeSelector 配置为 aiops.e2e/nonexistent-node-label=true，而集群 3 个节点（master、node1、node2）均不存在该标签
     传导机制: 调度器在过滤节点时，检查每个节点的标签是否匹配 Pod 的 nodeSelector → 3 个节点均不匹配 → 无可用节点 → Pod 进入 Pending 状态，调度器反复重试仍失败
     最终表现: Pod rc-pending-nodeselector（namespace: aiops-e2e）持续 Pending，Events 显示 FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (28.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6053 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 32.6s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将严格按照您的核心原则和报告模板，为您生成一份详尽、完整的诊断报告。

⚠️ **首先，直接回答您的核心问题「我的集群有什么问题」：**

您的集群**整体健康，但存在一个明确的调度问题**。在 65 个 Pod 中，59 个运行正常，**仅有 1 个 Pod (`rc-pending-nodeselector`) 处于 `Pending` 状态**。

---

## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending (PendingUnschedulable) |
| **兼容归因层** | L1 - 调度约束不匹配 |
| **问题分类** | 调度失败 (FailedScheduling) - nodeSelector 不匹配 |
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
| Node | `<none>` (未调度到任何节点) |
| **核心错误信息** | `FailedScheduling`: 0/3 nodes are available: **3 node(s) didn`t match Pod`s node affinity/selector.** |

**集群状态**：
在 65 个 Pod 中，59 个 `Running`，1 个 `Pending`。集群中 `master`, `node1`, `node2` 共 3 个节点，状态均为 `Ready`。

---

## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态与事件 | `kubectl describe pod` | `Node-Selectors: aiops.e2e/nonexistent-node-label=true` <br> `Warning FailedScheduling` ... `3 node(s) didn`t match Pod`s node affinity/selector.` | Pod 配置了 nodeSelector `aiops.e2e/nonexistent-node-label=true`，调度器明确报告无节点匹配该选择器。 |
| 2 | Pod 完整配置 | `kubectl get pod -o yaml` | `nodeSelector: {“aiops.e2e/nonexistent-node-label”: “true”}` <br> `finalizers: <none>` <br> `terminationGracePeriodSeconds: 30` | 确认 Pod YAML 中 nodeSelector 字段的设置。同时，排除“finalizer 未清理”作为根因。 |
| 3 | 节点标签 | `run_bash_command` (运行 `kubectl get nodes -o custom-columns=...`) | 节点 `master`: `labels: ...kubernetes.io/hostname=master...` <br> 节点 `node1`: `labels: ...kubernetes.io/hostname=node1...` <br> 节点 `node2`: `labels: ...kubernetes.io/hostname=node2...` <br> **3 个节点的标签列表中均不包含 `aiops.e2e/nonexistent-node-label`。** | 集群中没有任何节点拥有 Pod 所要求的标签，这是无法调度的直接证据。 |
| 4 | Namespace 事件 | `kubectl events` | `Warning FailedScheduling Pod/rc-pending-nodeselector 0/3 nodes are available: 3 node(s) didn`t match Pod`s node affinity/selector.` | 从事件系统确认调度失败原因，排除了资源不足（`Insufficient cpu/memory`）等其他候选场景。 |

### 证据关联分析
- **证据 #1 + 证据 #3 印证**：Pod 要求节点有 `aiops.e2e/nonexistent-node-label=true` 标签，但集群 3 个节点均无此标签。《br> - **证据链**：Pod 设置不存在的 nodeSelector → 调度器过滤掉所有节点 → 无可用节点 → 调度失败，Pod 持续 `Pending`。
- **排除项**：证据 #2 明确显示 `finalizers: <none>`，排除了“finalizer 阻塞”的可能性。所有节点均为 `Ready` 状态，排除了“节点不可达”的根本原因。

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | N/A | 证据链完整，足以确定根因。 |

---

## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────┐
│ 根本原因                                                        │
│ Pod rc-pending-nodeselector 的 nodeSelector 配置错误             │
│ 内容为: aiops.e2e/nonexistent-node-label=true                   │
│ 该标签在集群3个节点（master, node1, node2）上均不存在。          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 传导机制                                                        │
│ 调度器（default-scheduler）尝试调度Pod：                          │
│ 1. 过滤节点: 检查每个节点是否符合Pod的调度约束（nodeSelector）。 │
│ 2. 结果: 3个节点均不匹配Pod的请求。                              │
│ 3. 调度失败: 节点列表中无可用的候选节点。                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┘
│ 直接原因                                                        │
│ Pod 无法被调度到任何节点。                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                    │
│ Pod 状态为 Pending，且事件中持续报错 FailedScheduling。          │
└─────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (Pod 事件和 `Node-Selectors`), 证据 #2 (Pod YAML `nodeSelector`), 和证据 #3 (节点标签列表)，
问题的根本原因是 Pod `rc-pending-nodeselector` 的 **`nodeSelector` 配置了集群中不存在的标签 `aiops.e2e/nonexistent-node-label=true`**。
这导致调度器在过滤节点时，无法找到任何满足约束的节点，Pod 因此一直处于 `Pending` 状态。

**置信度**：高 (98%)
- ✅ Pod `describe` 和 `Event` 都明确指向 `node affinity/selector` 不匹配。
- ✅ 节点标签的原始输出直接证实了缺失该标签。
- ✅ 完美符合 L1 层“调度约束不匹配”的特征。
- ⚠️ 排除了资源不足、taint/toleration 等低概率可能性。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）
**1. [唯一根因] 移除错误 nodeSelector 或为节点打上标签**

   **方案 A (推荐): 修改 Pod/Deployment，移除或修正 nodeSelector**
   如果业务上无需特殊的节点选择，直接移除该配置。命令如下（假设 Pod 由 Deployment 管理）：
   ```bash
   # 方法一：编辑并移除 nodeSelector (推荐)
   kubectl edit deployment <deployment-name> -n aiops-e2e
   ```
   在打开的编辑器中，找到并删除 `nodeSelector:` 相关的几行。
   ```yaml
   # 删除类似下面的内容
   nodeSelector:
     aiops.e2e/nonexistent-node-label: "true"
   ```
   *依据*：这是解决问题的直接方式，确保 Pod 可以被调度到任何可用节点。

   **方案 B: 如果需要该标签，为特定节点打上标签**
   如果业务逻辑需要节点具有此标签，请选择一个或多个节点并打上标签。
   ```bash
   # 假设要为 node2 打上标签
   kubectl label node node2 aiops.e2e/nonexistent-node-label=true
   ```
   *注意*：打标签后，Pod 理论上很快就能够被调度。如果还需调度到 master，需考虑 master 节点通常有 taint，可能需要添加 tolerations。

**2. [验证] 确认 Pod 已被调度**
   ```bash
   kubectl get pod rc-pending-nodeselector -n aiops-e2e
   ```
   *预期结果*：`STATUS` 从 `Pending` 变为 `Running` 或 `ContainerCreating`，`NODE` 列显示节点名称。

**3. [验证] 查看 Pod 最新事件**
   ```bash
   kubectl describe pod rc-pending-nodeselector -n aiops-e2e
   ```
   *预期结果*：底部的事件列表显示 `Successfully assigned` 新的事件信息。

### 后续优化
1. **CI/CD 检查**：在发布流水线中增加对 `nodeSelector` 和 `nodeAffinity` 的校验，确保引用的标签在目标集群中存在。
2. **文档化**：将集群节点标签清单维护在文档中，供开发者查询。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running |
| 2. 检查调度事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 事件中出现 `Successfully assigned` |
| 3. 确认无异常 Pod | `kubectl get pod -n aiops-e2e` | 列表中没有 `Pending` 状态的 Pod |

---

## ⚠️ 注意事项
- 如果您选择 **方案 A (移除 nodeSelector)**，请确保该 Pod 没有其他硬性约束（如特定节点上的本地存储卷），否则可能会导致其他问题。
- 此问题**不涉及**集群资源不足、kubelet 断开、PV/PVC 未绑定等其他常见问题，完全取决于 Pod 配置与节点标签的匹配度。该 Pod 是由测试框架创造出来模拟故障的，其名称 `nonexistent-node-label` 已经清晰指示了问题所在。

---

## 📊 性能统计

├─ 总耗时: 1.5m
├─ 问题定位: 22.8s (25%) ✅
├─ 证据链采集: 22.6s (24%) ✅
├─ 根因分析: 19.1s (21%) ✅
├─ 汇总总结: 28.0s (30%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 8 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 8 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
