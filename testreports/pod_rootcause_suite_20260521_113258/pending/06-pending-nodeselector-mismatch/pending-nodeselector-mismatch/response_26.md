======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 0947a682cd884f4a]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来先扫描整个集群的 Pod 状态，看看有哪些异常。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 发现一个异常 Pod。让我进一步查看详情。
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
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          18m   <none>   <none>   
   💭 [问题定位] 让我进一步确认调度失败的原因。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  18m                  default-scheduler  0/3 nodes are available
   💭 [问题定位] 很好，信息已经足够了。现在来做完整的分析。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 所有节点都 Ready，没有异常。现在我已有全部信息，可以输出了。

---

## 诊断结果

### 全局概览
集群共 **65 个 Pod**，分布在 3 个命名空间，其中 **59 个 Running（正常）**，**1 个 Pending（异常）**，3 个节点全部 **Ready** 状态。

---

### 🚨 异常 Pod 识别

| Pod | 命名空间 | 状态 | 持续时间 |
|-----|---------|------|---------|
| `rc-pending-nodeselector` | `aiops-e2e` | **Pending** | 18 分钟 |

### 📋 异常组归类

| 异常组 | 包含 Pod | 数量 |
|-------|---------|:----:|
| **PendingUnschedulable** | rc-pending-nodeselector | 1 |

---

### 🔍 根因分析

**Pod:** `rc-pending-nodeselector`（`aiops-e2e` 命名空间）

**异常类型:** `PendingUnschedulable`（调度失败）

**关键证据（Events — FailedScheduling）:**
```
0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.
```

**根因：nodeSelector 不匹配**
- Pod 设置了 `Node-Selectors: aiops.e2e/nonexistent-node-label=true`
- 集群中 **没有任何节点** 包含该标签（`aiops.e2e/nonexistent-node-label=true`），因此 3 个节点全部不满足调度条件

**其他特征：**
- 3 个节点全部 **Ready**，无异常
- 容器镜像 `busybox:1.36` 可正常拉取
- 未设置资源 requests（QoS Class: BestEffort），不存在资源不足问题
- 无 PVC 依赖，无存储问题
- Pod 名称和标签 `rootcause-e2e=true` 表明这很可能是一个 **E2E 测试用例**

---

### 📊 分层输出

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **layer_name** | PendingUnschedulable |
| **pod_status_keyword** | Pending |
| **pod_abnormal_type** | PendingUnschedulable |
| **status_category** | scheduling |
| **confidence** | 高 |
| **layers（兼容所有异常）** | {"L1": ["PendingUnschedulable"]} |

**`abnormal_pods`:**
```json
[{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending", "pod_abnormal_type": "PendingUnschedulable"}]
```

**`abnormal_groups`:**
```json
{"PendingUnschedulable": ["rc-pending-nodeselector"]}
```

**`possible_scenarios`:**
1. **nodeSelector 标签不匹配**（主要）：Pod 要求节点具备 `aiops.e2e/nonexistent-node-label=true` 标签，但集群中没有任何节点有此标签。
2. **E2E 测试 Pod**：从标签 `rootcause-e2e=true` 来看，此 Pod 是故意创建的测试用例，用于验证调度失败场景，可能无需修复。

**审查方向建议（给下游 evidence）：**
- 确认该 Pod 是否为 E2E 测试 Pod（`rootcause-e2e=true`），如是则无需处理
- 如为真实业务 Pod，需将 `nodeSelector` 改为集群节点上真实存在的标签，或为节点打上对应标签
   ✅ [问题定位] 完成 (25.7s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector 标签不匹配', 'probability': 'high', 'reason': 'Pod 设置了 Node-Selectors: aiops.e2e/nonexistent-node-label=true，但集群中 3 个节点均无此标签，导致 FailedScheduling'}, {'scenario': 'E2E 测试 Pod', 'probability': 'medium', 'reason': 'Pod 标签包含 rootcause-e2e=true，可能为故意创建的测试用例，用于验证调度失败场景'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}]
   reasoning=集群中存在一个异常 Pod `rc-pending-nodeselector`（aiops-e2e 命名空间），状态为 Pending，持续 18 分钟。Events 显示 FailedScheduling 原因是 node selector/affinity 不匹配（0/3 nodes available: 3 node(s) didn't match Pod's node affinity/selector）。3 个节点全部 Ready，无资源或节点问题。根据五层模型，调度约束不匹配（nodeSelector/affinity）归因于 L1（scheduling 类）。Pod 异常类型为 PendingUnschedulable，status_category 为 scheduling。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 1.0, "reasoning": "集群中存在一个异常 Pod `rc-pending-nodeselector`（aiops-e2e 命名空间），状态为 Pending，持续 18 分钟。Events 显示 FailedScheduling 原因是 node selector/affinity 不匹配（0/3 nodes available: 3 node(s) didn't match Pod's node affinity/selector）。3 个节点全部 Ready，无资源或节点问题。根据五层模型，调度约束不匹配（nodeSelector/affinity）归因于 L1（scheduling 类）。Pod 异常类型为 PendingUnschedulable，status_category 为 scheduling。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "nodeSelector 标签不匹配", "probability": "high", "reason": "Pod 设置了 Node-Selectors: aiops.e2e/nonexistent-node-label=true，但集群中 3 个节点均无此标签，导致 FailedScheduling"}, {"scenario": "E2E 测试 Pod", "probability": "medium", "reason": "Pod 标签包含 rootcause-e2e=true，可能为故意创建的测试用例，用于验证调度失败场景"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              18m     <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/0947a682cd884f4a/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/0947a682cd884f4a/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/0947a682cd884f4a/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 100%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 按照既有 evidence_plan，开始执行真实工具采证：

**步骤 e1**：describe Pod 确认当前状态和 FailedScheduling 事件
**步骤 e2**：获取 Pod YAML 检查 nodeSelector/affinity 配置
**步骤 e3**：获取所有节点标签，验证匹配情况
**步骤 e4**：获取命名空间事件补充验证

开始并行执行 e1、e2、e3：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:18:44Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  19m                  default-scheduler  0/3 nodes are available
   💭 [证据链采集] 所有三个 critical 级工具执行完毕。现在执行 e4 - 获取命名空间事件：
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
19m                   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3
   💭 [证据链采集] 所有证据已采集完毕，以下是取证结论。

---

## 证据采集结论

### ✅ 已采集证据（4/4 计划项全部完成）

**e1 ✅ kubectl describe pod** — Pod 当前状态确认：
- **Status**: Pending（持续 19 分钟），node: `<none>`
- **Node-Selectors**: `aiops.e2e/nonexistent-node-label=true`
- **FailedScheduling 事件原文**：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.`
- 所有 3 个节点均排除，preemption 也无法帮助调度

**e2 ✅ kubectl get yaml** — Pod 调度约束确认：
- `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}` — 要求节点有此标签
- `phase: Pending`，`condition: PodScheduled=False`，reason=`Unschedulable`
- 无 PVC/volume 依赖问题，无 taint/toleration 冲突
- QoS Class: BestEffort，无资源 limits/requests

**e3 ✅ 集群节点标签确认** — 3 个节点（master/node1/node2）全部 **Ready**：
- 节点标签包括：`kubernetes.io/arch=amd64`、`kubernetes.io/os=linux`、`kubernetes.io/hostname=xxx`、`metax-tech.com/gpu.installed=false` 等
- **没有任何一个节点包含 `aiops.e2e/nonexistent-node-label` 标签**

**e4 ✅ 命名空间事件补充验证** — 与 describe 一致，仅有 FailedScheduling 事件，无其他异常

### ⚠️ 冲突/负向证据
- 无冲突证据。所有工具执行成功，namespace 准确匹配 `aiops-e2e`。

### 🔍 根因判定
> **Pod `rc-pending-nodeselector`（aiops-e2e 命名空间）处于 Pending 状态的根本原因是：Pod 的 `nodeSelector` 要求节点具有 `aiops.e2e/nonexistent-node-label=true` 标签，但集群中 3 个节点（master/node1/node2）均不包含该标签，导致调度器无法放置 Pod。** 3 个节点均为 Ready，无资源不足、taint 或 PVC 问题。结合 Pod 标签 `rootcause-e2e=true` 和 annotation `aiops.e2e/runbook=pod-pending-unschedulable.md`，此 Pod 极可能是 E2E 测试场景的故意构造用例。
   ✅ [证据链采集] 完成 (21.1s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"Describe Pod rc-pending-nodeselector 确认当前状态和 Events 中的 FailedScheduling 原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"确认 Pod 仍处于 Pending 状态，并获取 FailedScheduling 事件原文确认调度失败原因（nodeSelector/affinity 不匹配）","evidence_type":"current_status","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod YAML 检查 nodeSelector/affinity 配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"检查 Pod spec 中的 nodeSelector、affinity 等调度约束配置，验证是否设置了不匹配的标签选择器","evidence_type":"config_detail","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"列出所有节点及其标签，验证 nodeSelector 是否匹配","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes --show-labels","tool_args":{},"purpose":"获取所有节点的标签，验证 Pod 的 nodeSelector/affinity 是否有可用节点匹配","evidence_type":"config_detail","target_scope":"Node/all","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"获取集群 Events 确认调度相关事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e"},"purpose":"获取命名空间内的调度事件，作为 FailedScheduling 的补充验证","evidence_type":"events","target_scope":"Namespace/aiops-e2e","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0947a682cd884f4a/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0947a682cd884f4a/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0947a682cd884f4a/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   238d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          238d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\nnode2    Ready    <none>          238d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0947a682cd884f4a/tools/002-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0947a682cd884f4a/tools/002-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0947a682cd884f4a/tools/002-evidence-kubectl_get_by_kind_in_cluster.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  19m                  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  8m45s (x2 over 13m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  19m                  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  8m45s (x2 over 13m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0947a682cd884f4a/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0947a682cd884f4a/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0947a682cd884f4a/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n19m                   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n8m47s (x2 over 13m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0947a682cd884f4a/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0947a682cd884f4a/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0947a682cd884f4a/tools/004-evidence-kubectl_events.summary.txt"}],"llm_analysis":"所有证据已采集完毕，以下是取证结论。\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据（4/4 计划项全部完成）\n\n**e1 ✅ kubectl describe pod** — Pod 当前状态确认：\n- **Status**: Pending（持续 19 分钟），node: `<none>`\n- **Node-Selectors**: `aiops.e2e/nonexistent-node-label=true`\n- **FailedScheduling 事件原文**：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.`\n- 所有 3 个节点均排除，preemption 也无法帮助调度\n\n**e2 ✅ kubectl get yaml** — Pod 调度约束确认：\n- `nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}` — 要求节点有此标签\n- `phase: Pending`，`condition: PodScheduled=False`，reason=`Unschedulable`\n- 无 PVC/volume 依赖问题，无 taint/toleration 冲突\n- QoS Class: BestEffort，无资源 limits/requests\n\n**e3 ✅ 集群节点标签确认** — 3 个节点（master/node1/node2）全部 **Ready**：\n- 节点标签包括：`kubernetes.io/arch=amd64`、`kubernetes.io/os=linux`、`kubernetes.io/hostname=xxx`、`metax-tech.com/gpu.installed=false` 等\n- **没有任何一个节点包含 `aiops.e2e/nonexistent-node-label` 标签**\n\n**e4 ✅ 命名空间事件补充验证** — 与 describe 一致，仅有 FailedScheduling 事件，无其他异常\n\n### ⚠️ 冲突/负向证据\n- 无冲突证据。所有工具执行成功，namespace 准确匹配 `aiops-e2e`。\n\n### 🔍 根因判定\n> **Pod `rc-pending-nodeselector`（aiops-e2e 命名空间）处于 Pending 状态的根本原因是：Pod 的 `nodeSelector` 要求节点具有 `aiops.e2e/nonexistent-node-label=true` 标签，但集群中 3 个节点（master/node1/node2）均不包含该标签，导致调度器无法放置 Pod。** 3 个节点均为 Ready，无资源不足、taint 或 PVC 问题。结合 Pod 标签 `rootcause-e2e=true` 和 annotation `aiops.e2e/runbook=pod-pending-unschedulable.md`，此 Pod 极可能是 E2E 测试场景的故意构造用例。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 8 个，匹配计划 4 个，未规划证据 4 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":4,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"Describe Pod rc-pending-nodeselector 确认当前状态和 Events 中的 FailedScheduling 原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"确认 Pod 仍处于 Pending 状态，并获取 FailedScheduling 事件原文确认调度失败原因（nodeSelector/affinity 不匹配）","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod YAML 检查 nodeSelector/affinity 配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"检查 Pod spec 中的 nodeSelector、affinity 等调度约束配置，验证是否设置了不匹配的标签选择器","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"列出所有节点及其标签，验证 nodeSelector 是否匹配","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes --show-labels","purpose":"获取所有节点的标签，验证 Pod 的 nodeSelector/affinity 是否有可用节点匹配","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取集群 Events 确认调度相关事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --sort-by='.lastTimestamp'","purpose":"获取命名空间内的调度事件，作为 FailedScheduling 的补充验证","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | Describe Pod rc-pending-nodeselector 确认当前状态和 ... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_yaml | 获取 Pod YAML 检查 nodeSelector/affinity 配置 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e3 | critical | ✅ | kubectl_get_by_kind_in_cl... | 列出所有节点及其标签，验证 nodeSelector 是否匹配 | `kubectl get nodes --show-labels` |
   | e4 | important | ✅ | kubectl_events | 获取集群 Events 确认调度相关事件 | `kubectl get events -n aiops-e2e --sort-by='.lastTimestamp'` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (24.0s)
   📤 → 下游数据: root_cause=Pod `rc-pending-nodeselector`（aiops-e2e 命名空间）处于 Pending 状态的根本原因是：Pod 的 `nodeSelector` 字段要求节点具有 `aiops.e2e/nonexistent-node-label=true` 标签，但集群中 3 个节点（master、node1、node2）均不包含该标签。调度器 Events 明确报告 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.`，PodScheduled condition 为 False、reason=Unschedulable。3 个节点全部 Ready，无资源不足（QoS BestEffort）、无 taint 冲突（Tolerations 仅含默认 NotReady:NoExecute）、无 PVC 依赖问题。Pod 标签含 `rootcause-e2e=true` 且 annotation 指向 `pod-pending-unschedulable.md`，极可能是
... 截断，原始 509 字符
   confidence=100%
   causal_chain={"root_cause": "Pod 的 nodeSelector 指定了集群中不存在的标签 `aiops.e2e/nonexistent-node-label=true`，3 个节点均无此标签，导致调度器无法找到匹配节点", "propagation": "Pod 创建后调度器遍历所有 3 个 Ready 节点，逐一检查 nodeSelector 标签条件 → 所有节点均不满足 → 调度器标记为 Unschedulable → 重试 3 次后仍失败 → Pod 持续处于 Pending 状态", "direct_cause": "Pod spec 中 nodeSelector 字段要求节点具有 `aiops.e2e/nonexistent-node-label=true`，但集群中没有任何节点拥有该标签", "manifestation": "Pod rc-pending-nodeselector（aiops-e2e）状态为 Pending，describe 显示 FailedScheduling 事件，kubectl get 显示 STATUS=Pending 已持续 19 分钟，IP 和 NODE 均为 <none>"}
   rca_analysis={"phenomenon": "集群 aiops-e2e 命名空间中 Pod `rc-pending-nodeselector` 处于 Pending 状态，持续约 19 分钟，调度器报告 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod rc-pending-nodeselector 状态 Pending，Node-Selectors: aiops.e2e/nonexistent-node-label=true，FailedScheduling 事件显示 3 节点均不匹配 node affinity/selector", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml", "content": "Pod YAML 确认 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}，phase: Pending，PodScheduled=False reason=Unschedulable", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_by_kind_in_cluster (nodes)", "content": "3 个节点全部 Ready，标签列表不含 aiops.e2e/nonexistent-node-label，包括 master/node1/node2", "reliability": "高"}, {"id": "e4", "source": "kubectl_events", "content": "命名空间事件仅有 FailedScheduling，与 describe 一致，无其他异常事件", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedScheduling 19m default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. Pod Node-Selectors: aiops.e2e/nonexistent-node-label=true", "interpretation": "Pod 明确设置了 nodeSelector 要求节点具有 aiops.e2e/nonexistent-node-label=true 标签，调度器确认所有 3 个节点均不满足此条件"}, {"evidence_id": "e2", "raw_data": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}, phase: Pending, conditions: PodScheduled=False reason=Unschedulable", "interpretation": "YAML 配置确认 nodeSelector 为唯一调度约束，无 PVC 依赖或资源请求问题；PodScheduled condition 明确标记为 Unschedulable"}, {"evidence_id": "e3", "raw_data": "master: beta.kubernetes.io/arch=amd64,kubernetes.io/hostname=master,... node1: beta.kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,... node2: beta.kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,...", "interpretation": "3 个节点标签覆盖架构、操作系统、主机名、GPU 等属性，但无一包含 aiops.e2e/nonexistent-node-label 标签"}, {"evidence_id": "e4", "raw_data": "19m Warning FailedScheduling Pod/rc-pending-nodeselector 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.", "interpretation": "集群全局 events 与 Pod 自身 events 一致，无其他干扰事件，确认唯一故障原因为 nodeSelector 不匹配"}], "causal_chain": {"root_cause": "Pod 的 nodeSelector 指定了集群中不存在的标签 `aiops.e2e/nonexistent-node-label=true`，3 个节点均无此标签，导致调度器无法找到匹配节点", "propagation": "Pod 创建后调度器遍历所有 3 个 Ready 节点，逐一检查 nodeSelector 标签条件 → 所有节点均不满足 → 调度器标记为 Unschedulable → 重试 3 次后仍失败 → Pod 持续处于 Pending 状态", "direct_cause": "Pod spec 中 nodeSelector 字段要求节点具有 `aiops.e2e/nonexistent-node-label=true`，但集群中没有任何节点拥有该标签", "manifestation": "Pod rc-pending-nodeselector（aiops-e2e）状态为 Pending，describe 显示 FailedScheduling 事件，kubectl get 显示 STATUS=Pending 已持续 19 分钟，IP 和 NODE 均为 <none>"}, "root_cause": "Pod `rc-pending-nodeselector`（aiops-e2e 命名空间）处于 Pending 状态的根本原因是：Pod 的 `nodeSelector` 字段要求节点具有 `aiops.e2e/nonexistent-node-label=true` 标签，但集群中 3 个节点（master、node1、node2）均不包含该标签。调度器 Events 明确报告 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.`，PodScheduled condition 为 False、reason=Unschedulable。3 个节点全部 Ready，无资源不足（QoS BestEffort）、无 taint 冲突（Tolerations 仅含默认 NotReady:NoExecute）、无 PVC 依赖问题。Pod 标签含 `rootcause-e2e=true` 且 annotation 指向 `pod-pending-unschedulable.md`，极可能是\n... 截断，原始 509 字符", "root_cause_summary": "Pod `rc-pending-nodeselector`（aiops-e2e 命名空间）处于 Pending 状态的根本原因是：Pod 的 `nodeSelector` 字段要求节点具有 `aiops.e2e/nonexistent-node-label=true` 标签，但集群中 3 个节点（master、node1、node2）均不包含该标签。调度器 Events 明确报告 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.`，PodScheduled condition 为 False、reason=Unschedulable。3 个节点全部 Ready，无资源不足（QoS BestEffort）、无 taint 冲突（Tolerations 仅含默认 NotReady:NoExecute）、无 PVC 依赖问题。Pod 标签含 `rootcause-e2e=true` 且 annotation 指向 `pod-pending-unschedulable.md`，极可能是\n... 截断，原始 509 字符", "confidence": 1.0, "confidence_reason": "直接证据充分：Pod 的 nodeSelector 明确指定不存在的标签（e2），3 个节点的标签集合已全部列出且均不包含该标签（e3），调度器 Events 明确报告 3/3 节点因 node affinity/selector 不匹配而不可用（e1/e4），三项证据完全一致，因果链清晰完整，置信度达到最高", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "资源不足（CPU/内存不足）", "probability": "low", "reason": "Pod 的 QoS Class 为 BestEffort，无资源 requests/limits，且 3 节点全部 Ready 无资源压力事件；FailedScheduling 消息明确指向 nodeSelector 不匹配而非资源不足"}, {"cause": "节点 taint 未容忍", "probability": "low", "reason": "Pod 已配置默认的 node.kubernetes.io/not-ready:NoExecute toleration，且 FailedScheduling 消息未提及 taint 相关拒绝原因"}, {"cause": "PVC 未绑定或卷依赖未满足", "probability": "low", "reason": "Pod YAML 显示 volumes 仅含 kube-api-access-w74s5（默认 ServiceAccount token 卷），无 PVC 声明；FailedScheduling 消息未提及卷相关错误"}], "limitations": "证据未覆盖节点完整标签列表的原始 JSON 输出（仅摘要行），但摘要已充分显示关键标签（包括 arch、os、hostname、gpu 等），足以确认 aiops.e2e/nonexistent-node-label 标签不存在。此外，Pod 可能是 E2E 测试用例（rootcause-e2e=true 标签），但此判断不影响根因分析的正确性。", "llm_raw_analysis": "所有证据均指向同一结论。已采集 4 项证据：kubectl_describe 确认 FailedScheduling 事件和 Node-Selectors；kubectl_get_yaml 确认 nodeSelector 精确值为 aiops.e2e/nonexistent-node-label=true；节点列表确认 3 个 Ready 节点均无此标签；集群 events 验证无其他干扰因素。无冲突证据。唯一异常组 g1 仅含 1 个 Pod rc-pending-nodeselector，最小验证通过。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod `rc-pending-nodeselector`（aiops-e2e 命名空间）处于 Pending 状态的根本原因是：Pod 的 `nodeSelector` 字段要求节点具有 `aiops.e2e/nonexistent-node-label=true` 标签，但集群中 3 个节点（m...
   置信度: 100%
   🔗 因果链:
     根本原因: Pod 的 nodeSelector 指定了集群中不存在的标签 `aiops.e2e/nonexistent-node-label=true`，3 个节点均无此标签，导致调度器无法找到匹配节点
     传导机制: Pod 创建后调度器遍历所有 3 个 Ready 节点，逐一检查 nodeSelector 标签条件 → 所有节点均不满足 → 调度器标记为 Unschedulable → 重试 3 次后仍失败 → Pod 持续处于 Pending 状态
     最终表现: Pod rc-pending-nodeselector（aiops-e2e）状态为 Pending，describe 显示 FailedScheduling 事件，kubectl get 显示 STATUS=Pending 已持续 19 分钟，IP 和 NODE 均为 <none>


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (26.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6009 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 37.6s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将根据您提供的全部分析结果，为您生成一份详尽、完整的诊断报告。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending |
| **兼容归因层** | L1 - 调度类 |
| **问题分类** | PendingUnschedulable (调度失败) |
| **置信度** | 高 (100%) |
| **证据完整度** | 4/4 (100%) |
---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-pending-nodeselector |
| Namespace | aiops-e2e |
| Node | 无（未调度） |
| 错误信息 | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` |
---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe pod` | `status: Pending` | Pod 无法被调度到任何节点上运行 |
| 2 | 调度事件 | `kubectl describe pod` / `kubectl events` | `Warning FailedScheduling 19m default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..` | 调度器明确报告失败原因是节点亲和性/选择器不匹配 |
| 3 | Pod 调度约束 | `kubectl describe pod` / `kubectl get yaml` | `Node-Selectors: aiops.e2e/nonexistent-node-label=true` | Pod 的 `nodeSelector` 要求节点必须携带 `aiops.e2e/nonexistent-node-label=true` 标签 |
| 4 | 集群节点状态 | `kubectl get nodes` | `kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}` | 集群中 3 个节点（master、node1、node2）全部处于 Ready 状态 |
| 5 | 集群节点标签 | `kubectl get nodes` | `master: beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/hostname=master...`; `node1: beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/hostname=node1...`; `node2: beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,kubernetes.io/hostname=node2...` | 所有节点的标签中均不包含 `aiops.e2e/nonexistent-node-label` 标签 |
| 6 | Pod 标签 | `kubectl get pod` | `app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true` | Pod 标签 `rootcause-e2e=true` 表明该 Pod 很可能是用于 E2E 测试的。 |
| 7 | Pod 容器配置 | `kubectl get yaml` | `command: sh -c sleep 3600`; `finalizers: <none>`; `QoS: BestEffort` | Pod 启动后会长时间运行 (sleep 3600)；无 finalizer 阻塞问题；无资源请求/限制，不会因资源不足被调度。 |
### 证据关联分析
- **证据 #1 + #2 + #3 + #5 核心印证**：Pod Pending -> 调度器报错 `no nodes matched node affinity/selector` -> Pod `nodeSelector` 要求标签 `aiops.e2e/nonexistent-node-label=true` -> 集群所有节点均无此标签。这是一个完整的证据链，明确指向了 **调度约束不匹配** 是导致 Pod 无法调度的根本原因。
- **证据 #4 排他性分析**：3 个节点全部 Ready，排除了节点不可用、节点 NotReady 等常见的调度失败原因。
- **证据 #7 排他性分析**：Pod 的 QoS 为 `BestEffort` 且无 finalizer 问题，排除资源不足或 finalizer 阻塞作为根因。

---
## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                                │
│ Pod 的 nodeSelector 字段指定了一个不存在的标签：aiops.e2e/nonexistent-node-label=true    │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                                │
│ Pod 创建后，调度器对所有 3 个 Ready 节点检查 nodeSelector 条件 → 全部不满足             │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                                │
│ 调度器无法为 Pod 找到任何匹配的 Node，报告 FailedScheduling 事件                        │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                            │
│ Pod rc-pending-nodeselector 持续处于 Pending 状态，IP 和 NODE 均为 <none>               │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #1 (Pod Pending), 证据 #2 (FailedScheduling), 证据 #3 (Node-Selectors: `aiops.e2e/nonexistent-node-label=true`) 和 证据 #5 (节点缺少该标签)，问题的根本原因是 **Pod 的 nodeSelector 配置错误**。该 Pod 要求运行在带有 `aiops.e2e/nonexistent-node-label=true` 标签的节点上，但集群中的 3 个节点均未设置此标签，导致调度器无法完成调度，Pod 持续 Pending。

**置信度**：高 (100%)
- ✅ `kubectl describe` 中的 Events 信息直接、明确地指出了具体原因。
- ✅ 节点标签信息也与该结论完全吻合。
- ✅ 已排除节点故障（节点全部 Ready）和资源不足（Pod 为 BestEffort，且事件未提及资源不足）作为根因。

---
## 🛠️ 修复建议
**说明**：由于该 Pod 带有 `rootcause-e2e=true` 标签，它很可能是一个 **E2E 测试用例**，用于主动验证调度失败的诊断场景。**如果这是测试用例，则无需修复**。

如果不是测试用例，或您希望让该 Pod 成功运行，请按以下步骤操作：

### 立即执行（按优先级排序）
**1. [验证] 确认 Pod 是否为测试用例**
```bash
# 查看 Pod 标签
kubectl get pod rc-pending-nodeselector -n aiops-e2e --show-labels
```
*目的*：确认 Pod 标签中是否包含 `rootcause-e2e=true`。如果是，则此 Pod 正常处于预期状态。

**2. [修复] 方法一：删除测试 Pod（推荐）**
```bash
kubectl delete pod rc-pending-nodeselector -n aiops-e2e
```
*依据*：如果确认为测试用例，删除它是最快的恢复方式。

**3. [修复] 方法二：为节点添加缺失的标签**
*依据*：如果这不是测试用例，且 Pod 需要运行在特定节点上。
```bash
# 选择一个合适的节点（例如 node1），为其添加 Pod 所需的标签
kubectl label node node1 aiops.e2e/nonexistent-node-label=true
```
然后 Pod 将会被调度到 node1 上。

**4. [修复] 方法三：修改 Pod 的 nodeSelector**
*依据*：如果可以容忍 Pod 运行在任何节点上，可以移除或修改 nodeSelector。
```bash
# 请注意：对于通过 Deployment 等控制器创建的 Pod，应修改控制器配置，而非直接修改 Pod。
# 假设您有对应的部署配置，编辑并移除 nodeSelector，或将其改为匹配现有节点的标签。
# 例如，修改为匹配所有节点的标签：
kubectl edit deployment <deployment-name> -n aiops-e2e
# 找到 spec.template.spec.nodeSelector，将其设置为 kubernetes.io/os: linux
```
---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | Pod 已不存在（删除后）或 STATUS 变为 Running（修复后） |
| 2. 检查全局异常 Pod | `kubectl get pods -A \| grep -v Running` | 不应再看到 Pending 的 Pod |
| 3. 确认节点标签（如果执行了添加标签） | `kubectl get node node1 --show-labels` | 节点标签中包含 `aiops.e2e/nonexistent-node-label=true` |
---
## ⚠️ 注意事项
- **E2E 测试嫌疑**：Pod 的标签 `rootcause-e2e=true` 强烈暗示这是一个预置的测试场景。在采取任何修复行动前，请先验证这一点。
- **无资源问题**：集群中 59 个 Pod 正常运行，仅此 1 个 Pending Pod 由调度约束引起，说明集群整体健康，不存在资源紧张问题。

---

## 📊 性能统计

├─ 总耗时: 1.6m
├─ 问题定位: 25.7s (26%) ✅
├─ 证据链采集: 21.1s (22%) ✅
├─ 根因分析: 24.0s (25%) ✅
├─ 汇总总结: 26.7s (27%) ✅
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
