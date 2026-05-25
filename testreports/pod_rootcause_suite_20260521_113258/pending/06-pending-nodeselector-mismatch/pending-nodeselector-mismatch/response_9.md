======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 22d4e6d4f4164852]

📍 [问题定位] 执行中...
   💭 [问题定位] 让我先对集群进行全局 Pod 状态扫描，了解当前有哪些异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 很好，发现了一个异常 Pod。让我进一步查看这个 Pending Pod 的详细信息以及相关节点情况。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  5m49s  default-scheduler  0/3 nodes are available: 3 node(s) di
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE     IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          5m50s   <none>   <none
   💭 [问题定位] 现在我已经获取了足够的定位信息。让我获取对应的 runbook 作为参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在我已经有了足够的信息来输出定位分析结果。

---

## 集群异常定位分析

### 全局 Pod 扫描结果

| 指标 | 数值 |
|------|------|
| 总 Pod 数 | **65** |
| Running 正常 | **59** |
| Pending 异常 | **1** |
| 其他异常 | **0** |

### 当前异常 Pod

| Pod | 命名空间 | 状态 | 异常类型 |
|-----|---------|------|---------|
| `rc-pending-nodeselector` | `aiops-e2e` | **Pending** | **PendingUnschedulable** |

### 异常详情

该 Pod 卡在 **Pending** 状态，调度器事件明确报错：

> **`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.`**

Pod 设置了 **nodeSelector**：`aiops.e2e/nonexistent-node-label=true`——这是一个不存在的节点标签，导致集群中 **3 个节点全部不匹配**，调度器无法放置。

### 分层定位

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **layer_name** | PendingUnschedulable |
| **derived_layer** | L1 |
| **layers** | [L1] |
| **status_category** | scheduling |
| **pod_status_keyword** | Pending |
| **pod_abnormal_type** | PendingUnschedulable |
| **confidence** | 高 |

### 可能场景

1. **nodeSelector 标签不匹配**（最可能）：Pod 要求 `aiops.e2e/nonexistent-node-label=true`，但集群中没有节点带有此标签，导致所有 3 个节点均不满足条件。
2. **节点标签配置缺失**：预期节点应有该标签，但实际未打上。

### 关键实体

- **异常 Pod**：`aiops-e2e/rc-pending-nodeselector`
- **集群节点**：3 个节点均健康且可调度，但因标签不匹配无法放置
- **调度器事件**：`FailedScheduling` - 节点亲和性/选择器不匹配
- **QoS Class**：BestEffort（无资源限制）

**建议后续审查方向**：
- 确认 `aiops.e2e/nonexistent-node-label=true` 标签是否应该存在于节点上
- 若该标签是预期的，则为节点打上对应标签
- 若该标签是测试用例的一部分，确认本次是否属于预期行为（Pod 带有 `rootcause-e2e=true` 标签，疑似 E2E 测试用例）
   ✅ [问题定位] 完成 (21.3s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector 标签不匹配', 'probability': '高', 'reason': 'Pod 要求 aiops.e2e/nonexistent-node-label=true，集群中3个节点均无此标签，导致调度器无法放置'}, {'scenario': '节点标签配置缺失', 'probability': '中', 'reason': '预期节点应有该标签，但实际未打上'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Cluster", "name": "default", "namespace": ""}]
   reasoning=集群中存在1个当前仍处于Pending状态的Pod rc-pending-nodeselector (aiops-e2e命名空间)，调度器事件明确报错：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod设置了不存在的节点标签aiops.e2e/nonexistent-node-label=true，导致所有3个节点均不满足调度约束。Pod状态关键字为Pending，异常类型归为PendingUnschedulable，属于调度层面的问题，定位为L1层。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "集群中存在1个当前仍处于Pending状态的Pod rc-pending-nodeselector (aiops-e2e命名空间)，调度器事件明确报错：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod设置了不存在的节点标签aiops.e2e/nonexistent-node-label=true，导致所有3个节点均不满足调度约束。Pod状态关键字为Pending，异常类型归为PendingUnschedulable，属于调度层面的问题，定位为L1层。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Cluster", "name": "default", "namespace": ""}], "possible_scenarios": [{"scenario": "nodeSelector 标签不匹配", "probability": "高", "reason": "Pod 要求 aiops.e2e/nonexistent-node-label=true，集群中3个节点均无此标签，导致调度器无法放置"}, {"scenario": "节点标签配置缺失", "probability": "中", "reason": "预期节点应有该标签，但实际未打上"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              5m47s   <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/22d4e6d4f4164852/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/22d4e6d4f4164852/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/22d4e6d4f4164852/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我来按既有 evidence_plan 执行工具调用。先执行关键证据采集。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
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
  Warning  FailedScheduling  6m14s  default-scheduler  0/3 nodes are available: 3 node(s) di
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
6m15s       Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [证据链采集] 所有计划中的工具都已成功执行。以下是证据采集结论：

---

## ✅ 已采集证据

| # | 计划项 | 证据类型 | 采集结果 |
|---|--------|---------|---------|
| **e1** | `kubectl describe pod` | ✅ **Critical** | Pod `rc-pending-nodeselector` STATUS=Pending，未绑定节点。FailedScheduling 事件原文：**`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`**。明确指向 **nodeSelector/affinity 不匹配**。 |
| **e2** | `kubectl get pod -o yaml` | ✅ **Critical** | Pod spec 中 `nodeSelector` 明确为 **`{"aiops.e2e/nonexistent-node-label": "true"}`**。PodScheduled=False，reason=Unschedulable。无 PVC 依赖、无 finalizer 阻塞。 |
| **e3** | `kubectl get nodes --show-labels` | ✅ **Important** | 集群共 **3 个节点**（master/node1/node2），状态均为 Ready。**所有节点均不包含 `aiops.e2e/nonexistent-node-label` 标签**——3 个节点上的标签列表中均查无此标签。 |
| **e4** | `kubectl events` | ✅ **Important** | FailedScheduling 事件分别在 **6m15s 和 46s 前** 重复出现，调度器持续失败，未发生变化。 |

## ❌ 未采集 / 冲突证据
- **无冲突证据**：Pod 仍存在于 `aiops-e2e` 命名空间，节点标签信息明确，所有工具均正常返回结果。

## 📋 诊断结论

**根因明确**：Pod `rc-pending-nodeselector` 设置了 `nodeSelector: {aiops.e2e/nonexistent-node-label: "true"}`，但集群中 3 个节点均无此标签，导致调度器无法放置。

**影响范围**：仅此 1 个 Pod，不影响其他 59 个 Running Pod 和集群节点。

**修复建议**：
1. **给目标节点打标签**：`kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`
2. **或修改 Pod 的 nodeSelector**，使其匹配现有节点标签（如 `kubernetes.io/hostname=node1`）
3. 标签生效后 Pod 会自动调度运行，无需重建。
   ✅ [证据链采集] 完成 (16.3s)
   📤 → 下游数据: evidence_items=6/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod rc-pending-nodeselector 当前状态和 FailedScheduling 事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"确认当前 Pending 状态和 FailedScheduling 事件中 nodeSelector/affinity 不匹配的具体错误原文","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"检查 Pod YAML 中的 nodeSelector/affinity 配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"查看 Pod spec 中的 nodeSelector 和 affinity 精确配置","evidence_type":"","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"获取集群所有节点的标签信息","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes --show-labels","tool_args":{"kind":"nodes"},"purpose":"确认集群中所有节点是否匹配 Pod 要求的 nodeSelector 标签 aiops.e2e/nonexistent-node-label=true","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"获取 Pod 相关事件确认调度失败详情","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-nodeselector","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-pending-nodeselector"},"purpose":"确认 FailedScheduling 事件原文和持续时长","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/22d4e6d4f4164852/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/22d4e6d4f4164852/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/22d4e6d4f4164852/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  6m14s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  46s    default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  6m14s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  46s    default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/22d4e6d4f4164852/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/22d4e6d4f4164852/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/22d4e6d4f4164852/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n6m15s       Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n46s         Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/22d4e6d4f4164852/tools/003-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/22d4e6d4f4164852/tools/003-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/22d4e6d4f4164852/tools/003-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   238d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          238d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\nnode2    Ready    <none>          238d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/22d4e6d4f4164852/tools/004-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/22d4e6d4f4164852/tools/004-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/22d4e6d4f4164852/tools/004-evidence-kubectl_get_by_kind_in_cluster.summary.txt"}],"llm_analysis":"所有计划中的工具都已成功执行。以下是证据采集结论：\n\n---\n\n## ✅ 已采集证据\n\n| # | 计划项 | 证据类型 | 采集结果 |\n|---|--------|---------|---------|\n| **e1** | `kubectl describe pod` | ✅ **Critical** | Pod `rc-pending-nodeselector` STATUS=Pending，未绑定节点。FailedScheduling 事件原文：**`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`**。明确指向 **nodeSelector/affinity 不匹配**。 |\n| **e2** | `kubectl get pod -o yaml` | ✅ **Critical** | Pod spec 中 `nodeSelector` 明确为 **`{\"aiops.e2e/nonexistent-node-label\": \"true\"}`**。PodScheduled=False，reason=Unschedulable。无 PVC 依赖、无 finalizer 阻塞。 |\n| **e3** | `kubectl get nodes --show-labels` | ✅ **Important** | 集群共 **3 个节点**（master/node1/node2），状态均为 Ready。**所有节点均不包含 `aiops.e2e/nonexistent-node-label` 标签**——3 个节点上的标签列表中均查无此标签。 |\n| **e4** | `kubectl events` | ✅ **Important** | FailedScheduling 事件分别在 **6m15s 和 46s 前** 重复出现，调度器持续失败，未发生变化。 |\n\n## ❌ 未采集 / 冲突证据\n- **无冲突证据**：Pod 仍存在于 `aiops-e2e` 命名空间，节点标签信息明确，所有工具均正常返回结果。\n\n## 📋 诊断结论\n\n**根因明确**：Pod `rc-pending-nodeselector` 设置了 `nodeSelector: {aiops.e2e/nonexistent-node-label: \"true\"}`，但集群中 3 个节点均无此标签，导致调度器无法放置。\n\n**影响范围**：仅此 1 个 Pod，不影响其他 59 个 Running Pod 和集群节点。\n\n**修复建议**：\n1. **给目标节点打标签**：`kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`\n2. **或修改 Pod 的 nodeSelector**，使其匹配现有节点标签（如 `kubernetes.io/hostname=node1`）\n3. 标签生效后 Pod 会自动调度运行，无需重建。","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 6/7 项，完整度 86%；实际执行工具 7 个，匹配计划 3 个，未规划证据 4 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":7,"environment_evidence_collected":6,"environment_evidence_completeness":0.8571428571428571,"executed_tool_count":7,"matched_tool_count":3,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证 Pod rc-pending-nodeselector 当前状态和 FailedScheduling 事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"确认当前 Pending 状态和 FailedScheduling 事件中 nodeSelector/affinity 不匹配的具体错误原文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查 Pod YAML 中的 nodeSelector/affinity 配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"查看 Pod spec 中的 nodeSelector 和 affinity 精确配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"获取集群所有节点的标签信息","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes --show-labels","purpose":"确认集群中所有节点是否匹配 Pod 要求的 nodeSelector 标签 aiops.e2e/nonexistent-node-label=true","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取 Pod 相关事件确认调度失败详情","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-nodeselector","purpose":"确认 FailedScheduling 事件原文和持续时长","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e4(获取 Pod 相关事件确认调度失败详情): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 86%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod rc-pending-nodeselector 当前状态和 FailedSc... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_yaml | 检查 Pod YAML 中的 nodeSelector/affinity 配置 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_get_by_kind_in_cl... | 获取集群所有节点的标签信息 | `kubectl get nodes --show-labels` |
   | e4 | important | ❌ | kubectl_events | 获取 Pod 相关事件确认调度失败详情 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pendi...` |

   ⚠️ 未采集原因:
   - e4(获取 Pod 相关事件确认调度失败详情): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (18.1s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector（aiops-e2e命名空间）处于Pending状态，根因为其nodeSelector指定了标签aiops.e2e/nonexistent-node-label=true（来自kubectl_get_yaml），而集群全部3个节点（master/node1/node2）的标签列表中均不包含该标签（来自节点标签采集结果），导致调度器报错"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"（来自kubectl_describe和kubectl_events的FailedScheduling事件）。无需资源不足、PVC绑定或taint排查。
   confidence=98%
   causal_chain={"root_cause": "Pod rc-pending-nodeselector 的 nodeSelector 中指定了集群中不存在的标签 aiops.e2e/nonexistent-node-label=true", "propagation": "Pod 被提交到 API Server → scheduler 逐节点检查 nodeSelector 匹配 → 3个节点均无该标签 → 所有节点被过滤 → 调度失败 → Pod 停留在 Pending 状态", "direct_cause": "调度器因 nodeSelector 不匹配无法将 Pod 调度到任何节点", "manifestation": "Pod rc-pending-nodeselector 处于 Pending 状态，未分配节点和 IP，FailedScheduling 事件持续报错"}
   rca_analysis={"phenomenon": "集群中存在1个Pending状态的Pod rc-pending-nodeselector（命名空间aiops-e2e），状态关键字为Pending，异常类型为PendingUnschedulable。调度器事件明确报错：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod rc-pending-nodeselector 状态 Pending，未绑定节点，FailedScheduling 事件：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml", "content": "Pod 的 nodeSelector 为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}，PodScheduled=False, reason=Unschedulable", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_by_kind_in_cluster", "content": "集群3个节点（master/node1/node2）状态均为 Ready，均不包含标签 aiops.e2e/nonexistent-node-label", "reliability": "高"}, {"id": "e4", "source": "kubectl_events", "content": "FailedScheduling 事件在6m15s和46s前重复出现，调度器持续失败", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "kubectl_describe: status=Pending, node=<none>, FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.", "interpretation": "Pod 处于 Pending 状态且未分配到任何节点，调度器明确报告所有3个节点均不满足 Pod 的节点亲和性/选择器约束。"}, {"evidence_id": "e2", "raw_data": "kubectl_get_yaml: nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}, conditions: PodScheduled=False reason=Unschedulable", "interpretation": "Pod 的 nodeSelector 要求节点必须包含 aiops.e2e/nonexistent-node-label=true 标签，但 PodScheduled 条件为 False，原因 Unschedulable 确认调度失败。"}, {"evidence_id": "e3", "raw_data": "kubectl_get_by_kind_in_cluster: master labels=[...]不含aiops.e2e/nonexistent-node-label, node1 labels=[...]不含, node2 labels=[...]不含", "interpretation": "集群全部3个节点（master、node1、node2）的标签列表中均不包含 aiops.e2e/nonexistent-node-label 标签，因此没有节点能满足 Pod 的 nodeSelector 约束。"}, {"evidence_id": "e4", "raw_data": "kubectl_events: 6m15s Warning FailedScheduling, 46s Warning FailedScheduling", "interpretation": "调度器在过去6分钟内持续重试调度但始终失败，事件内容一致，说明问题持续存在且未被修复。"}], "causal_chain": {"root_cause": "Pod rc-pending-nodeselector 的 nodeSelector 中指定了集群中不存在的标签 aiops.e2e/nonexistent-node-label=true", "propagation": "Pod 被提交到 API Server → scheduler 逐节点检查 nodeSelector 匹配 → 3个节点均无该标签 → 所有节点被过滤 → 调度失败 → Pod 停留在 Pending 状态", "direct_cause": "调度器因 nodeSelector 不匹配无法将 Pod 调度到任何节点", "manifestation": "Pod rc-pending-nodeselector 处于 Pending 状态，未分配节点和 IP，FailedScheduling 事件持续报错"}, "root_cause": "Pod rc-pending-nodeselector（aiops-e2e命名空间）处于Pending状态，根因为其nodeSelector指定了标签aiops.e2e/nonexistent-node-label=true（来自kubectl_get_yaml），而集群全部3个节点（master/node1/node2）的标签列表中均不包含该标签（来自节点标签采集结果），导致调度器报错\"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"（来自kubectl_describe和kubectl_events的FailedScheduling事件）。无需资源不足、PVC绑定或taint排查。", "root_cause_summary": "Pod rc-pending-nodeselector（aiops-e2e命名空间）处于Pending状态，根因为其nodeSelector指定了标签aiops.e2e/nonexistent-node-label=true（来自kubectl_get_yaml），而集群全部3个节点（master/node1/node2）的标签列表中均不包含该标签（来自节点标签采集结果），导致调度器报错\"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"（来自kubectl_describe和kubectl_events的FailedScheduling事件）。无需资源不足、PVC绑定或taint排查。", "confidence": 0.98, "confidence_reason": "直接证据完整：Pod YAML 明确显示 nodeSelector 配置（e2）、节点标签列表明确显示该标签不存在（e3）、调度器事件直接印证 node affinity/selector 不匹配（e1/e4）。三条证据相互印证，因果链清晰无歧义。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "资源不足（CPU/内存不足）", "probability": "low", "reason": "调度器事件明确报告是 node affinity/selector 不匹配，而非资源不足；且3个节点均为 Ready 状态，资源充足"}, {"cause": "节点 taint 未容忍", "probability": "low", "reason": "Pod 已配置 tolerations（node.kubernetes.io/not-ready:NoExecute），且调度器事件未提及 taint 相关原因"}, {"cause": "PVC 未绑定", "probability": "low", "reason": "Pod YAML 显示无 PVC 卷声明，仅有一个 kube-api-access 投影卷"}], "limitations": "证据充分，无关键缺失。仅1个异常Pod，影响范围明确。", "llm_raw_analysis": "根据上游采集的证据进行L1层根因分析。异常组g1仅包含1个Pod（rc-pending-nodeselector），证据完整覆盖了Pod状态、YAML配置、节点标签和事件四个维度。无其他异常组需要处理。因果链清晰：Pod设置了不存在的nodeSelector标签 → 所有节点均不匹配 → 调度器无法放置 → Pod持续Pending。置信度0.98。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector（aiops-e2e命名空间）处于Pending状态，根因为其nodeSelector指定了标签aiops.e2e/nonexistent-node-label=true（来自kubectl_get_yaml），而集群全部3个节点（master/...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod rc-pending-nodeselector 的 nodeSelector 中指定了集群中不存在的标签 aiops.e2e/nonexistent-node-label=true
     传导机制: Pod 被提交到 API Server → scheduler 逐节点检查 nodeSelector 匹配 → 3个节点均无该标签 → 所有节点被过滤 → 调度失败 → Pod 停留在 Pending 状态
     最终表现: Pod rc-pending-nodeselector 处于 Pending 状态，未分配节点和 IP，FailedScheduling 事件持续报错


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (27.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5606 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 22.8s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为一名资深 K8s 诊断报告专家，我将根据您提供的分析结果生成一份详尽的诊断报告。

---
## 📊 集群状态总结

首先，直接回答您的问题：**您的集群目前没有严重的全局性问题，但存在一个明确的调度异常 Pod。**

| 项目 | 内容 |
|------|------|
| **集群整体状态** | 集群共65个Pod，其中 **59个运行正常 (Running)**，1个异常 (Pending)。3个节点均处于 `Ready` 状态。 |
| **发现的核心问题** | **1个Pod `rc-pending-nodeselector` (命名空间: aiops-e2e) 处于 `Pending` 状态**，无法被调度。 |
| **问题影响范围** | 仅限于该单个Pod，不会影响集群其他工作负载。 |

---

## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending (PendingUnschedulable) |
| **兼容归因层** | L1 - 调度层 |
| **问题分类** | 调度约束不匹配 (nodeSelector/Affinity) |
| **置信度** | 高 (98%) |
| **证据完整度** | 3/4 (75%) |

---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-pending-nodeselector |
| Namespace | aiops-e2e |
| Pod状态 | Pending |
| 节点 | 未分配 (Node: `<none>`) |
| 错误信息 | `Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` |
---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl_describe` | `Status: Pending`，`Node: <none>`，`Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | Pod 未被调度成功，原因明确是节点标签不匹配。 |
| 2 | Pod 配置 | `kubectl_get_yaml` | `Node-Selectors: aiops.e2e/nonexistent-node-label=true`，`command: sh -c sleep 3600`，`finalizers: <none>` | Pod 的 `nodeSelector` 指定了一个过高的标签键值对。Pod 无finalizer阻塞。 |
| 3 | 节点标签 | `kubectl_get_by_kind_in_cluster` (节点) | 集群3个节点 (master, node1, node2) 标签列表均不包含 `aiops.e2e/nonexistent-node-label=true`。 | 所有节点均不满足Pod的调度约束。 |
| 4 | 调度事件 | `kubectl_events` | `6m15s Warning FailedScheduling Pod/rc-pending-nodeselector 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 调度器的事件日志与 `kubectl_describe` 结果吻合，确认是nodeSelector不匹配导致。 |
| 5 | 集群Pod概览 | `kubectl_get_by_kind_in_cluster` | 集群共65个Pod，59个Running，1个Pending。 | 确认问题范围仅限于此Pod，不影响整体集群健康。 |

### 证据关联分析
- **证据 #1 + #2 + #3 + #4 印证**：`kubectl_describe` 和 `kubectl_events` 中的 `FailedScheduling` 错误，与 Pod YAML 中的 `nodeSelector` 配置 (aiops.e2e/nonexistent-node-label=true) 以及节点标签列表完全一致，形成了完整的证据链。
- **证据链**：Pod 要求 `aiops.e2e/nonexistent-node-label=true` 标签 → 集群3个节点均无此标签 → 调度器找不到匹配节点 → Pod 持续处于 Pending 状态并报错。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | - | 证据链完整，无需额外信息即可确定根因。 |

---
## 🎯 根因分析
### 因果链
```
┌─────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                            │
│ Pod `rc-pending-nodeselector` 的 spec 中 `nodeSelector`              │
│ 指定了一个**集群中不存在的标签** `aiops.e2e/nonexistent-node-label=true`  │
│ (证据#2: kubectl_get_yaml)                                          │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                            │
│ Pod 提交 → scheduler 检查 nodeSelector → 遍历所有3个节点            │
│ → 均无匹配标签 → 所有节点被过滤 → 调度失败                          │
│ (证据#3: 节点标签列表)                                              │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                            │
│ 调度器因 nodeSelector 不匹配，无法将 Pod 部署到任何节点              │
│ (证据#1, #4: FailedScheduling 事件)                                 │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                        │
│ Pod `rc-pending-nodeselector` 处于 **Pending** 状态，              │
│ 未分配节点和 IP，FailedScheduling 事件持续出现。                    │
│ (证据#5: 集群Pod概览)                                              │
└─────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #2 (Pod YAML 中 `nodeSelector: aiops.e2e/nonexistent-node-label=true`) 和证据 #3 (所有节点均无此标签)，问题的根本原因是 **Pod 指定的 `nodeSelector` 无法在集群中找到匹配的节点**，导致调度失败。
**置信度**：高 (98%)
- ✅ `FailedScheduling` 事件明确指向 nodeSelector/affinity 不匹配
- ✅ Pod YAML 和节点标签信息均直接匹配此结论
- ✅ 可以明确排除资源不足（无相关事件）和 PVC 问题（Pod 无 PVC 配置）
- ✅ 工具输出明确显示 `finalizers: <none>`，排除 finalizer 未清理原因

---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [推荐] 修改 Pod spec，移除或更正 `nodeSelector`**
您可以通过编辑对应的控制器（如Deployment、StatefulSet）来更新 Pod 配置。这里假设Pod由名为 `rc-pending-nodeselector` 的控制器管理：
```bash
# 编辑Deployment，去掉 nodeSelector
kubectl edit deployment rc-pending-nodeselector -n aiops-e2e
```
*在编辑器中*：找到 `spec.template.spec.nodeSelector` 部分，将其删除或修改为集群中存在的标签（例如 `kubernetes.io/hostname: node1`）。保存退出后，控制器会自动重建Pod。

**2. [备选] 给其中一个节点打上所需标签**
如果 Pod 必须绑定此标签，选择其中一个节点手动打上标签。
```bash
# 给 node1 打上标签
kubectl label node node1 aiops.e2e/nonexistent-node-label=true
```
*验证*：打标后，Pod 可能会自动被调度到node1上。验证命令：`kubectl get pod rc-pending-nodeselector -n aiops-e2e`

### 后续优化
1. **规范标签管理**：建立命名规范，避免在POD中使用不存在的标签。
2. **前置检查**：在创建或更新资源时，使用 `kubectl` 的 `--dry-run=server` 或 lint 工具（如 `kubeval`）预检查配置错误。
---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认Pod状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: Running (或绑定到节点) |
| 2. 检查节点 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o wide` | NODE 列显示节点名称，如 `node1` |
| 3. 检查调度事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | Events 中不再出现 `FailedScheduling` |
---
## ⚠️ 注意事项
- 如果选择了“修改Pod spec”的方案并删除 `nodeSelector`，Pod 将被调度到集群中任何可用的节点，可能不符合最初的部署意图。
- 如果选择了“给节点打标”的方案，请确保该标签与您的集群配置和应用程序需求一致，避免影响其他资源调度。

---

## 📊 性能统计

├─ 总耗时: 1.4m
├─ 问题定位: 21.3s (26%) ✅
├─ 证据链采集: 16.3s (20%) ✅
├─ 根因分析: 18.1s (22%) ✅
├─ 汇总总结: 27.1s (33%) ✅
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
