======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: d175c60e89bb4a61]

📍 [问题定位] 执行中...
   💭 [问题定位] 让我先扫描集群中所有的 Pod，获取全局状态概览。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 发现了一个异常 Pod，让我进一步查看它的详细信息。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          35m   <none>   <none>   
   💭 [问题定位] Pod 处于 Pending 状态，有标签 `pod_abnormal_type=PendingUnschedulable`，这暗示调度问题。让我查看详情。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  35m                default-scheduler  0/3 nodes are available: 
   💭 [问题定位] 很好，已经定位到问题。让我也看看节点信息以便更全面地了解集群状况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 现在我已经掌握了完整信息，让我获取相关的 runbook。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 所有信息已收集完毕。下面给出完整的诊断分析结果。

---

## 📋 集群健康诊断报告

### 整体健康概览

| 指标 | 结果 |
|------|------|
| **集群节点** | 3 个节点（master, node1, node2），全部 **Ready** ✅ |
| **总 Pod 数** | 65 个 |
| **正常 Pod** | 59 个 Running ✅ |
| **异常 Pod** | **1 个** Pending ⚠️ |

### 当前异常 Pod

| 命名空间 | Pod 名称 | 状态 | 已运行时间 |
|----------|----------|------|-----------|
| `aiops-e2e` | `rc-pending-nodeselector` | **Pending** | 35 分钟 |

---

### 🔍 详细分析

#### 异常 Pod：`rc-pending-nodeselector`

**异常类型：** `PendingUnschedulable` — 调度失败，Pod 无法分配到任何节点

**根因定位：nodeSelector 不匹配**

从 `kubectl describe` 我们看到关键证据：

- **Events 中的 FailedScheduling：**
  ```
  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.
  ```
  所有 3 个节点都不匹配 Pod 的节点选择约束。

- **Pod 的 nodeSelector：**
  ```
  Node-Selectors: aiops.e2e/nonexistent-node-label=true
  ```
  Pod 要求节点具有标签 `aiops.e2e/nonexistent-node-label=true`。

- **节点实际标签：** 检查 3 个节点（master/node1/node2），**没有任何一个节点**带有 `aiops.e2e/nonexistent-node-label` 这个标签，因此调度器无法将 Pod 放置到任何节点上。

---

### 分类定层

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **layer_name** | PendingUnschedulable |
| **pod_abnormal_type** | `PendingUnschedulable` |
| **pod_status_keyword** | `Pending` |
| **status_category** | `scheduling` |
| **置信度** | 高 |

---

### 异常组与受影响 Pod

| 异常组 | Pod 列表 |
|--------|----------|
| **PendingUnschedulable** | `aiops-e2e/rc-pending-nodeselector` |

---

### 可能的场景

1. **nodeSelector 标签不存在**（最可能）— Pod 要求节点标签 `aiops.e2e/nonexistent-node-label=true`，但集群中没有任何节点有这个标签，这可能是测试场景或配置错误。
2. **集群配置预期** — Pod 的 labels 包含 `rootcause-e2e=true` 和 `pod_abnormal_type=PendingUnschedulable`，说明这很可能是一个**端到端测试 Pod**，用于验证调度失败的异常检测能力。

---

### 建议方向

- 检查是否需要给某个节点打上 `aiops.e2e/nonexistent-node-label=true` 标签
- 如果这是测试用例 Pod，则属于预期行为，无需修复
- 如果是生产配置错误，则需要修正 Pod 的 `nodeSelector` 或添加对应节点标签

---

**总结：集群整体健康，3 个节点均正常运行，59 个 Pod 正常工作。仅有 1 个 Pod 因 nodeSelector 不匹配而无法调度（PendingUnschedulable-L1），属于调度约束问题。**
   ✅ [问题定位] 完成 (30.7s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector 标签不存在', 'probability': '高', 'reason': 'Pod 要求节点标签 aiops.e2e/nonexistent-node-label=true，3个节点均无此标签，导致调度器无法放置 Pod'}, {'scenario': '端到端测试 Pod', 'probability': '中', 'reason': 'Pod labels 包含 rootcause-e2e=true 和 pod_abnormal_type=PendingUnschedulable，表明是测试场景'}]
   entities=[{"type": "pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "node", "name": "master", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}]
   reasoning=集群中存在1个当前仍异常的Pod: aiops-e2e/rc-pending-nodeselector，状态为Pending。kubectl describe 显示 FailedScheduling 事件，原因为 '3 node(s) didn't match Pod's node affinity/selector'。Pod 的 nodeSelector 设置为 aiops.e2e/nonexistent-node-label=true，但集群中3个节点均不包含该标签。3个节点均Ready，无节点异常。因此根因为调度约束不匹配，属于 L1 scheduling 层。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "集群中存在1个当前仍异常的Pod: aiops-e2e/rc-pending-nodeselector，状态为Pending。kubectl describe 显示 FailedScheduling 事件，原因为 '3 node(s) didn't match Pod's node affinity/selector'。Pod 的 nodeSelector 设置为 aiops.e2e/nonexistent-node-label=true，但集群中3个节点均不包含该标签。3个节点均Ready，无节点异常。因此根因为调度约束不匹配，属于 L1 scheduling 层。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "node", "name": "master", "namespace": ""}, {"type": "node", "name": "node1", "namespace": ""}, {"type": "node", "name": "node2", "namespace": ""}], "possible_scenarios": [{"scenario": "nodeSelector 标签不存在", "probability": "高", "reason": "Pod 要求节点标签 aiops.e2e/nonexistent-node-label=true，3个节点均无此标签，导致调度器无法放置 Pod"}, {"scenario": "端到端测试 Pod", "probability": "中", "reason": "Pod labels 包含 rootcause-e2e=true 和 pod_abnormal_type=PendingUnschedulable，表明是测试场景"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              35m     <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来执行既有的 evidence_plan，先直接调用关键工具采集证据。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  36m                default-scheduler  0/3 nodes are available: 
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:18:44Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [证据链采集] 现在，我再专门确认一下各节点的标签中是否包含 `aiops.e2e/nonexistent-node-label` 这个键：
   💭 [证据链采集] 调用工具: kubernetes_tabular_query
   💭 [证据链采集] 工具结果: kubernetes_tabular_query (success)
      📄 kubernetes_tabular_query 输出摘要: raw_chars=228 lines=3
Command failed (exit 1):
kubectl get nodes --all-namespaces -o custom-columns='NAME:.metadata.name,LABEL_EXISTS:.metadata.labels."aiops\.e2e/nonexi
   💭 [证据链采集] 用 jq 更精确地检查：
   💭 [证据链采集] 调用工具: kubernetes_jq_query
   💭 [证据链采集] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=340 lines=5
Script failed (exit 3):
Executing jq query for nodes...
jq: error: syntax error, unexpected INVALID_CHARACTER (Unix shell quoting issues?) at <top-level
   💭 [证据链采集] 调用工具: kubernetes_jq_query
   💭 [证据链采集] 工具结果: kubernetes_jq_query (success)
      📄 kubernetes_jq_query 输出摘要: raw_chars=340 lines=5
Script failed (exit 3):
Executing jq query for nodes...
jq: error: syntax error, unexpected INVALID_CHARACTER (Unix shell quoting issues?) at <top-level
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "master: <absent>\nnode1: <absent>\nnode2: <absent>\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] ## ✅ 证据采集完成

### 已采集证据

**e1 - Pod 描述信息（critical）✅**
- Pod `rc-pending-nodeselector` 仍处于 **Pending** 状态，未绑定到任何节点
- **FailedScheduling** 事件原文：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`
- Pod 的 `Node-Selectors` 明确设置为：**`aiops.e2e/nonexistent-node-label=true`**

**e2 - Pod YAML 配置（critical）✅**
- `nodeSelector` 字段：`{"aiops.e2e/nonexistent-node-label": "true"}`
- `PodScheduled` condition：`status=False, reason=Unschedulable`
- 容器镜像 `busybox:1.36`，`imagePullPolicy=Never`（注意：Never 策略可能也有影响，但当前 root cause 是调度失败）
- 无 PVC/volume 依赖问题，仅有 kube-api-access 投影卷

**e3 - 节点标签检查（important）✅**
- 集群 3 个节点 **master、node1、node2** 全部为 **Ready** 状态，无节点异常
- 3 个节点均 **不包含** `aiops.e2e/nonexistent-node-label` 标签（全部返回 `<absent>`）

### 未采集证据
- 无其他异常组需要验证（status_counts 中仅 1 个 Pending 异常，无其他并发异常状态）

### 冲突证据
- 无冲突证据，所有工具结果均与上游定位一致

### 根因结论
Pod `rc-pending-nodeselector` 设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，但集群中 3 个节点均无此标签，导致调度器无法放置该 Pod，符合 **pod-pending-unschedulable.md** runbook 中"调度约束不匹配"分支。Pod labels 包含 `rootcause-e2e=true` 和 `pod_abnormal_type=PendingUnschedulable`，确认是端到端测试场景。
   ✅ [证据链采集] 完成 (22.9s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod rc-pending-nodeselector 当前状态和 FailedScheduling 事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"确认 Pod 仍处于 Pending 状态，采集 FailedScheduling 事件原文确认调度失败原因","evidence_type":"current_state_and_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"验证 Pod 的 nodeSelector 配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"采集 Pod YAML 中的 nodeSelector/affinity 字段，确认调度约束配置","evidence_type":"config","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"检查集群节点标签分布","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o wide --show-labels","tool_args":{},"purpose":"确认所有节点是否存在 Pod 所需的标签 aiops.e2e/nonexistent-node-label=true","evidence_type":"node_labels","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  36m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  25m (x2 over 30m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  36m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  25m (x2 over 30m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   238d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          238d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\nnode2    Ready    <none>          238d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubernetes_tabular_query","data":"kubernetes_tabular_query 输出摘要: raw_chars=228 lines=3\nCommand failed (exit 1):\nkubectl get nodes --all-namespaces -o custom-columns='NAME:.metadata.name,LABEL_EXISTS:.metadata.labels.\"aiops\\.e2e/nonexistent-node-label\"' | (head -n 1; tail -n +2 | grep -E '.')\nNAME     LABEL_EXISTS","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/004-evidence-kubernetes_tabular_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/004-evidence-kubernetes_tabular_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/004-evidence-kubernetes_tabular_query.summary.txt"},{"tool":"kubernetes_jq_query","data":"kubernetes_jq_query 输出摘要: raw_chars=340 lines=5\nScript failed (exit 3):\nExecuting jq query for nodes...\njq: error: syntax error, unexpected INVALID_CHARACTER (Unix shell quoting issues?) at <top-level>, line 1:\n.items[] | \"\\(.metadata.name): \\(.metadata.labels[\\\"aiops.e2e/nonexistent-node-label\\\"] // \\\"<absent>\\\" )\"                                                  \njq: 1 compile error","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/005-evidence-kubernetes_jq_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/005-evidence-kubernetes_jq_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/005-evidence-kubernetes_jq_query.summary.txt"},{"tool":"kubernetes_jq_query","data":"kubernetes_jq_query 输出摘要: raw_chars=340 lines=5\nScript failed (exit 3):\nExecuting jq query for nodes...\njq: error: syntax error, unexpected INVALID_CHARACTER (Unix shell quoting issues?) at <top-level>, line 1:\n.items[] | \"\\(.metadata.name): \\(.metadata.labels[\\\"aiops.e2e/nonexistent-node-label\\\"] // \\\"<absent>\\\" )\"                                                  \njq: 1 compile error","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/006-evidence-kubernetes_jq_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/006-evidence-kubernetes_jq_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/006-evidence-kubernetes_jq_query.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"master: <absent>\\nnode1: <absent>\\nnode2: <absent>\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/007-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/007-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d175c60e89bb4a61/tools/007-evidence-run_bash_command.summary.txt"}],"llm_analysis":"## ✅ 证据采集完成\n\n### 已采集证据\n\n**e1 - Pod 描述信息（critical）✅**\n- Pod `rc-pending-nodeselector` 仍处于 **Pending** 状态，未绑定到任何节点\n- **FailedScheduling** 事件原文：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`\n- Pod 的 `Node-Selectors` 明确设置为：**`aiops.e2e/nonexistent-node-label=true`**\n\n**e2 - Pod YAML 配置（critical）✅**\n- `nodeSelector` 字段：`{\"aiops.e2e/nonexistent-node-label\": \"true\"}`\n- `PodScheduled` condition：`status=False, reason=Unschedulable`\n- 容器镜像 `busybox:1.36`，`imagePullPolicy=Never`（注意：Never 策略可能也有影响，但当前 root cause 是调度失败）\n- 无 PVC/volume 依赖问题，仅有 kube-api-access 投影卷\n\n**e3 - 节点标签检查（important）✅**\n- 集群 3 个节点 **master、node1、node2** 全部为 **Ready** 状态，无节点异常\n- 3 个节点均 **不包含** `aiops.e2e/nonexistent-node-label` 标签（全部返回 `<absent>`）\n\n### 未采集证据\n- 无其他异常组需要验证（status_counts 中仅 1 个 Pending 异常，无其他并发异常状态）\n\n### 冲突证据\n- 无冲突证据，所有工具结果均与上游定位一致\n\n### 根因结论\nPod `rc-pending-nodeselector` 设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，但集群中 3 个节点均无此标签，导致调度器无法放置该 Pod，符合 **pod-pending-unschedulable.md** runbook 中\"调度约束不匹配\"分支。Pod labels 包含 `rootcause-e2e=true` 和 `pod_abnormal_type=PendingUnschedulable`，确认是端到端测试场景。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 10 个，匹配计划 3 个，未规划证据 7 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":10,"matched_tool_count":3,"unplanned_tool_count":7,"evidence_inventory":[{"id":"e1","description":"验证 Pod rc-pending-nodeselector 当前状态和 FailedScheduling 事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"确认 Pod 仍处于 Pending 状态，采集 FailedScheduling 事件原文确认调度失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证 Pod 的 nodeSelector 配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"采集 Pod YAML 中的 nodeSelector/affinity 字段，确认调度约束配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"检查集群节点标签分布","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o wide --show-labels","purpose":"确认所有节点是否存在 Pod 所需的标签 aiops.e2e/nonexistent-node-label=true","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod rc-pending-nodeselector 当前状态和 FailedSc... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_yaml | 验证 Pod 的 nodeSelector 配置 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | kubectl_get_by_kind_in_cl... | 检查集群节点标签分布 | `kubectl get nodes -o wide --show-labels` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (22.4s)
   📤 → 下游数据: root_cause=Pod aiops-e2e/rc-pending-nodeselector 设置了 nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}（证据e2），但集群3个节点 master/node1/node2 均不包含该标签（证据e3，通过bash命令确认均为 <absent>，证据e4）。调度器报告 "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"（证据e1），Pod 持续 Pending 35分钟。集群其余59个Pod均正常运行（证据e5），无节点异常。Pod labels 含 rootcause-e2e=true 和 pod_abnormal_type=PendingUnschedulable，确认为端到端测试场景。
   confidence=98%
   causal_chain={"root_cause": "Pod 的 nodeSelector 指定了集群中不存在的标签 aiops.e2e/nonexistent-node-label=true，导致调度约束无法满足", "propagation": "调度器（default-scheduler）遍历所有3个Ready节点（master/node1/node2），逐一检查节点标签是否包含 aiops.e2e/nonexistent-node-label=true → 3个节点均不匹配 → 调度器判定 Unschedulable → 持续重试失败", "direct_cause": "Pod 的 nodeSelector 字段设置了一个集群中不存在的标签键值对", "manifestation": "Pod 持续处于 Pending 状态35分钟，Events 中重复出现 FailedScheduling 警告，Pod 无绑定的节点（nodeName=None）"}
   rca_analysis={"phenomenon": "集群中存在1个Pending状态的异常Pod：aiops-e2e/rc-pending-nodeselector，持续35分钟未调度到任何节点，无法运行。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod rc-pending-nodeselector 状态 Pending，FailedScheduling 事件显示 0/3 nodes available: 3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml", "content": "Pod nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}，PodScheduled condition=False reason=Unschedulable", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_by_kind_in_cluster(nodes)", "content": "3个节点(master/node1/node2)全部Ready，均不包含 aiops.e2e/nonexistent-node-label 标签", "reliability": "高"}, {"id": "e4", "source": "run_bash_command", "content": "jq查询节点标签确认：master:<absent>, node1:<absent>, node2:<absent>", "reliability": "高"}, {"id": "e5", "source": "kubectl_get_by_kind_in_cluster(pods)", "content": "集群65个Pod中59个Running，仅此1个Pending异常", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedScheduling 36m default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.", "interpretation": "调度器明确报告所有3个节点均因 node affinity/selector 不匹配而无法调度该Pod，排除了资源不足、taint等其它原因"}, {"evidence_id": "e2", "raw_data": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}", "interpretation": "Pod 的 nodeSelector 要求节点必须带有标签 aiops.e2e/nonexistent-node-label=true，但该标签的键名暗示不存在（nonexistent）"}, {"evidence_id": "e3", "raw_data": "master/node1/node2 标签列表中均不包含 aiops.e2e/nonexistent-node-label", "interpretation": "集群3个节点的标签列表均不包含该标签，与Pod的调度约束完全无法匹配"}, {"evidence_id": "e4", "raw_data": "master: <absent>, node1: <absent>, node2: <absent>", "interpretation": "通过bash命令直接查询节点标签确认3个节点均无此标签，消除了kubectl custom-columns语法报错的疑虑"}, {"evidence_id": "e5", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}", "interpretation": "集群整体健康，无其他异常Pod，该Pending Pod是唯一异常对象"}], "causal_chain": {"root_cause": "Pod 的 nodeSelector 指定了集群中不存在的标签 aiops.e2e/nonexistent-node-label=true，导致调度约束无法满足", "propagation": "调度器（default-scheduler）遍历所有3个Ready节点（master/node1/node2），逐一检查节点标签是否包含 aiops.e2e/nonexistent-node-label=true → 3个节点均不匹配 → 调度器判定 Unschedulable → 持续重试失败", "direct_cause": "Pod 的 nodeSelector 字段设置了一个集群中不存在的标签键值对", "manifestation": "Pod 持续处于 Pending 状态35分钟，Events 中重复出现 FailedScheduling 警告，Pod 无绑定的节点（nodeName=None）"}, "root_cause": "Pod aiops-e2e/rc-pending-nodeselector 设置了 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}（证据e2），但集群3个节点 master/node1/node2 均不包含该标签（证据e3，通过bash命令确认均为 <absent>，证据e4）。调度器报告 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"（证据e1），Pod 持续 Pending 35分钟。集群其余59个Pod均正常运行（证据e5），无节点异常。Pod labels 含 rootcause-e2e=true 和 pod_abnormal_type=PendingUnschedulable，确认为端到端测试场景。", "root_cause_summary": "Pod aiops-e2e/rc-pending-nodeselector 设置了 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}（证据e2），但集群3个节点 master/node1/node2 均不包含该标签（证据e3，通过bash命令确认均为 <absent>，证据e4）。调度器报告 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"（证据e1），Pod 持续 Pending 35分钟。集群其余59个Pod均正常运行（证据e5），无节点异常。Pod labels 含 rootcause-e2e=true 和 pod_abnormal_type=PendingUnschedulable，确认为端到端测试场景。", "confidence": 0.98, "confidence_reason": "因果链完整且无歧义：Pod YAML明确显示nodeSelector设置（e2），kubectl_describe事件直接说明是node affinity/selector不匹配（e1），节点标签查询从两个维度（kubectl节点列表示例和bash命令jq查询）均确认标签不存在（e3/e4），集群无其他并发异常（e5）。所有证据一致，置信度高。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "节点资源不足（CPU/内存）", "probability": "low", "reason": "调度器事件明确报告为 'didn't match Pod's node affinity/selector'，而非 'Insufficient cpu/memory'；且3个节点均Ready"}, {"cause": "节点 taint 未容忍", "probability": "low", "reason": "调度器事件未提及 taint/toleration 相关拒绝原因，且Pod已配置 node.kubernetes.io/not-ready:NoExecute toleration"}, {"cause": "PVC/PV 依赖未满足", "probability": "low", "reason": "Pod 仅使用 kube-api-access 投影卷，无 PVC 绑定依赖，调度器事件也未提及卷相关问题"}, {"cause": "镜像拉取问题", "probability": "low", "reason": "Pod 尚未被调度到任何节点，镜像拉取发生在调度完成后，当前阶段不相关"}], "limitations": "Pod labels 包含 rootcause-e2e=true 和 pod_abnormal_type=PendingUnschedulable，且 diagnostic_annotations 指向 pod-pending-unschedulable.md runbook，确认这是一个构造的端到端测试场景，非生产环境意外故障。imagePullPolicy=Never 可能导致调度成功后容器启动失败，但当前阶段问题在调度层，不影响根因判断。", "llm_raw_analysis": "L1根因分析完成。异常组g1（PendingUnschedulable类型）仅包含1个Pod：rc-pending-nodeselector。证据链清晰：nodeSelector指定不存在标签→3个节点均不匹配→调度器无法放置→Pod Pending。无其他异常组需要分析。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod aiops-e2e/rc-pending-nodeselector 设置了 nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}（证据e2），但集群3个节点 master/node1/node2 均不包含该标签（证据e3，通过b...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod 的 nodeSelector 指定了集群中不存在的标签 aiops.e2e/nonexistent-node-label=true，导致调度约束无法满足
     传导机制: 调度器（default-scheduler）遍历所有3个Ready节点（master/node1/node2），逐一检查节点标签是否包含 aiops.e2e/nonexistent-node-label=true → 3个节点均不匹配 → 调度器判定 Unschedulable → 持续重试失败
     最终表现: Pod 持续处于 Pending 状态35分钟，Events 中重复出现 FailedScheduling 警告，Pod 无绑定的节点（nodeName=None）


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (23.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5423 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 39.6s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，诊断报告如下。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **集群整体状态** | **基本健康**。集群共65个Pod，其中59个正常运行，1个异常。3个节点均正常。 |
| **发现的问题** | **1个Pod处于Pending状态，无法调度**。 |
| **Pod异常状态** | Pending (PendingUnschedulable) |
| **兼容归因层** | L1 - 调度层 |
| **问题分类** | 调度约束不匹配 (FailedScheduling - NodeSelector) |
| **置信度** | 高 (98%) |
| **证据完整度** | 3/3 (100%) |

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| 异常 Pod | `rc-pending-nodeselector` |
| Namespace | `aiops-e2e` |
| 节点 (master) | Ready |
| 节点 (node1) | Ready |
| 节点 (node2) | Ready |
| 错误信息 | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` |

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| e1 | Pod 状态与事件 | `kubectl describe pod` | `status: Pending`<br>`Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | Pod 因调度器无法找到匹配的节点而持续Pending。 |
| e2 | Pod 配置 | `kubectl get pod -o yaml` | `Node-Selectors: aiops.e2e/nonexistent-node-label=true` | Pod 设置了调度约束 `nodeSelector`，要求节点必须包含 `aiops.e2e/nonexistent-node-label=true` 标签。 |
| e3 | 节点标签 | `bash command` | `master: <absent>`<br>`node1: <absent>`<br>`node2: <absent>` | 通过bash命令确认，集群中所有3个节点均**不包含** `aiops.e2e/nonexistent-node-label` 这个标签。 |
| e4 | 节点状态 | `kubectl get nodes` | `master Ready`, `node1 Ready`, `node2 Ready` | 集群所有节点状态均为 `Ready`，无节点异常，排除了节点不可用作为根因。 |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：Pod 必须调度到含有 `aiops.e2e/nonexistent-node-label=true` 标签的节点上（e2），但所有3个节点均无此标签（e3），导致调度器无法排程，产生 `FailedScheduling` 事件（e1）。
- **证据 #4 排除干扰**：所有节点状态均为 `Ready`（e4），排除了因节点宕机或网络问题导致的调度失败。

### 缺失证据
无缺失。所有关键证据均已采集，完整度100%。

## 🎯 根因分析

### 因果链
```
┌───────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                   │
│ Pod (rc-pending-nodeselector) 的 nodeSelector 指定了一个集群中不存在的标签。 │
│ nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}                │
└───────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌───────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                   │
│ 调度器遍历所有3个 Ready 节点 (master, node1, node2)                       │
│ → 逐一检查节点标签是否包含 aiops.e2e/nonexistent-node-label=true          │
│ → 3个节点均不匹配                                                          │
│ → 判定为 Unschedulable                                                     │
└───────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌───────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                   │
│ 调度器无法找到满足 Pod 调度约束的节点，持续重试失败。                      │
└───────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌───────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                               │
│ Pod 持续处于 Pending 状态，Events 中反复出现 FailedScheduling 警告。      │
└───────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (`FailedScheduling` 事件)、#2 (`nodeSelector` 配置) 和 #3 (节点标签缺失)，问题的根本原因是**Pod `rc-pending-nodeselector` 的 `nodeSelector` 字段错误地指定了一个集群中不存在的标签 (`aiops.e2e/nonexistent-node-label=true`)，导致调度器无法将其放置到任何节点上**。

**置信度**：高 (98%)
- ✅ `FailedScheduling` 事件明确指向节点亲和性/选择器不匹配。
- ✅ `kubectl get yaml` 直接确认了 `nodeSelector` 配置。
- ✅ bash命令直接验证了所有节点均不包含所需标签。
- ✅ Pod标签包含 `rootcause-e2e=true` 和 `pod_abnormal_type=PendingUnschedulable`，确认此为模拟故障的端到端测试场景，非生产环境意外问题。

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [核心] 修改或移除 Pod 的 nodeSelector**
此问题是人为构造的测试场景，生产环境防止此问题的方法是在 Pod 定义中修正 `nodeSelector`。

**方案A（推荐）：移除 `nodeSelector` 约束（如果不需要）**
```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
# 在打开的编辑器中，找到 spec.nodeSelector 字段，将其删除或设置为空 {}
# 保存后退出。Pod 将重新调度。
```

**方案B：修正 nodeSelector 为集群中存在的标签**
首先，确认节点上存在哪些标签：
```bash
# 查看节点标签
kubectl get nodes --show-labels
```
获取到现有标签后，再修改 Pod 的 `nodeSelector`：
```bash
kubectl edit pod rc-pending-nodeselector -n aiops-e2e
# 将 spec.nodeSelector 修改为存在的标签键值对，例如:
# nodeSelector:
#   kubernetes.io/hostname: node1
# 保存后退出。
```
*依据*：根因是 `nodeSelector` 设置的标签不存在。
*注意*：修改静态 Pod (非 Deployment 等控制器管理) 的 `nodeSelector` 后，Pod 不会自动重建，可能需要删除并重新创建。对于测试场景，推荐用法是检查并修改上层 Deployment/Job 的配置。

**2. [验证] 查看修改后的 Pod 状态**
```bash
kubectl get pod rc-pending-nodeselector -n aiops-e2e -w
# 观察 STATUS 是否从 Pending 变为 Running
```

### 后续优化
1. **代码与配置审查**：在 CI/CD 流程或 Helm Chart 中增加对 `nodeSelector` 和 `affinity` 规则有效性的校验，确保其引用的标签在目标集群中确实存在。
2. **监控告警**：针对 `Pending` 状态超过一定时间（如 5 分钟）的 Pod 配置告警，以便尽早发现调度问题。

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认问题 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 可以看到 `FailedScheduling` 事件 |
| 2. 修改配置 | 执行上述修复命令 | 命令执行成功 |
| 3. 观察状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -w` | `STATUS` 从 `Pending` 变为 `Running` 或 `ContainerCreating` |
| 4. 检查事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | 应出现 `Scheduled` 和 `Pulled` 等正常事件 |

## ⚠️ 注意事项
- 该 Pod (`rc-pending-nodeselector`) 为端到端测试 Pod，其对 `nodeSelector` 的错误配置是人为构造的。集群整体健康，3个节点均正常，其余59个Pod正常运行。
- 修复后，Pod 可能因 `imagePullPolicy=Never` 而无法拉取镜像，这是另一个分离的问题，不在本次诊断范围内。

---

## 📊 性能统计

├─ 总耗时: 1.7m
├─ 问题定位: 30.7s (31%) ✅
├─ 证据链采集: 22.9s (23%) ✅
├─ 根因分析: 22.4s (23%) ✅
├─ 汇总总结: 23.5s (24%) ✅
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
