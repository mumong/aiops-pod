======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 569051fa283d4558]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来先做一个全局 Pod 状态扫描，看看集群里有哪些异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 发现了一个异常 Pod。让我进一步查看这个 Pending Pod 的详细状态。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE     IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          4m35s   <none>   <none
   💭 [问题定位] 这个 Pod 处于 Pending 状态且没有绑定节点，符合 `PendingUnschedulable` 的特征。让我查看一下调度事件确认原因。
   💭 [问题定位] 调用工具: kubectl_events
   💭 [问题定位] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
4m36s       Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are
   💭 [问题定位] 现在我获取一下这个 Pod 的详细定义，看看它的 nodeSelector 或 affinity 配置。
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:18:44Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [问题定位] 很好，我已经清楚了全部情况。让我获取对应的 runbook 参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在我已经掌握了所有必要的信息，下面给出完整的异常定位分析。

---

## 异常定位分析

### 全局状态概览

| 指标 | 数值 |
|------|------|
| 总 Pod 数 | 65 |
| 正常 Pod (Running) | 59 |
| **异常 Pod** | **1** |

### 当前异常 Pod

| Pod | 命名空间 | 状态 | 年龄 |
|-----|---------|------|------|
| `rc-pending-nodeselector` | `aiops-e2e` | Pending | 4m35s |

### 异常分组

| 异常类型 (abnormal_group) | 包含 Pod | 数量 |
|--------------------------|---------|:----:|
| `PendingUnschedulable` | rc-pending-nodeselector | 1 |

### 关键证据

- **Pod 状态**: `Pending`，未绑定节点（`nodeName: <none>`）
- **调度事件**: `FailedScheduling` — `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`
- **根因**: Pod 设置了 `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}`，集群中 3 个节点均没有该标签，导致无可用调度节点。
- **Pod 无 PVC/volume 依赖**，不存在存储绑定问题。
- **节点状态正常**（Running 的 59 个 Pod 正常运行表明节点健康）。

### 诊断结论

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **derived_layer** | L1 |
| **layers** | ["L1"] |
| **layer_name** | 调度约束不匹配导致 Pod 无法调度 |
| **pod_status_keyword** | Pending |
| **pod_abnormal_type** | PendingUnschedulable |
| **status_category** | scheduling |
| **confidence** | 高 |
| **key_entities** | Pod: `aiops-e2e/rc-pending-nodeselector` |
| **possible_scenarios** | nodeSelector / nodeAffinity 不匹配：Pod 要求节点包含标签 `aiops.e2e/nonexistent-node-label=true`，集群中 3 个节点均无此标签 |

### 问题描述

集群中 Pod `rc-pending-nodeselector` 因设置了 `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}`，而所有节点均不匹配该标签选择器，导致调度器无法找到可用节点，Pod 一直卡在 Pending 状态。这是一个 e2e 测试用的模拟异常 Pod（标签 `rootcause-e2e=true` 表明其为测试用例），问题明确指向 **调度约束不匹配**。

### 建议审查方向
- 检查 Pod 的 `nodeSelector`/`affinity` 配置是否正确
- 确认目标节点是否具有预期的标签
- 如果该 Pod 是 e2e 测试用例，需确认测试环境是否正确配置了节点标签
   ✅ [问题定位] 完成 (26.3s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector/nodeAffinity 不匹配', 'probability': '高', 'reason': 'Pod nodeSelector 要求标签 aiops.e2e/nonexistent-node-label=true，3 个节点均无此标签，导致 FailedScheduling'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Node", "name": "全部 3 个节点", "namespace": ""}]
   reasoning=当前集群中发现 1 个异常 Pod：rc-pending-nodeselector（aiops-e2e 命名空间），状态为 Pending，未绑定节点。调度事件显示 FailedScheduling：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod 设置了 nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}，而集群 3 个节点均无此标签。节点状态正常（59 个 Running Pod 证明节点健康），根因是调度约束不匹配，符合 L1 调度层异常。属于典型的 PendingUnschedulable 类型，status_category 为 scheduling。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "调度约束不匹配导致 Pod 无法调度", "confidence": 0.98, "reasoning": "当前集群中发现 1 个异常 Pod：rc-pending-nodeselector（aiops-e2e 命名空间），状态为 Pending，未绑定节点。调度事件显示 FailedScheduling：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod 设置了 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}，而集群 3 个节点均无此标签。节点状态正常（59 个 Running Pod 证明节点健康），根因是调度约束不匹配，符合 L1 调度层异常。属于典型的 PendingUnschedulable 类型，status_category 为 scheduling。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Node", "name": "全部 3 个节点", "namespace": ""}], "possible_scenarios": [{"scenario": "nodeSelector/nodeAffinity 不匹配", "probability": "高", "reason": "Pod nodeSelector 要求标签 aiops.e2e/nonexistent-node-label=true，3 个节点均无此标签，导致 FailedScheduling"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              4m32s   <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/569051fa283d4558/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/569051fa283d4558/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/569051fa283d4558/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 98%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 现在开始执行既有 evidence_plan 中的关键工具调用。先并行执行 ev1、ev2、ev3、ev4 中独立的工具。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
5m7s        Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  5m7s  default-scheduler  0/3 nodes are available: 3 node(s) did
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
   💭 [证据链采集] 所有关键证据已采集完毕。以下是证据结论：

---

## ✅ 已采集证据

### ev1 — kubectl describe pod 详细描述（critical ✅）
- **状态**：Pending，未绑定节点（`node: <none>`）
- **调度事件**：`Warning FailedScheduling` → `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`
- **nodeSelector**：`aiops.e2e/nonexistent-node-label=true`
- **镜像**：busybox:1.36，`imagePullPolicy=Never`（空镜像拉取策略不影响调度）
- **QoS**：BestEffort（无资源限制，排除资源不足）

### ev2 — Pod YAML 完整配置（critical ✅）
- `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}` ✅ 确认标签选择器
- `conditions.PodScheduled: status=False, reason=Unschedulable` ✅ 调度失败明确
- 无 PVC/volume 依赖，排除存储前置条件
- 无 deletionTimestamp/finalizers，排除 Terminating 卡住

### ev3 — 集群 3 个节点标签全量检查（critical ✅）
| 节点 | 状态 | 标签 |
|------|------|------|
| master | Ready | `kubernetes.io/hostname=master`, `node-role.kubernetes.io/control-plane=` 等 |
| node1 | Ready | `kubernetes.io/hostname=node1` 等 |
| node2 | Ready | `kubernetes.io/hostname=node2` 等 |

**关键发现**：3 个节点均 **没有** `aiops.e2e/nonexistent-node-label` 标签 ✅

### ev4 — Pod 事件确认（important ✅）
- 唯一事件：`FailedScheduling`（5m7s 前），内容与 ev1/ev2 完全一致

---

## 📋 诊断结论

**根因确认**：Pod `rc-pending-nodeselector` 设置了 `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}`，而集群 3 个节点（master/node1/node2）均无此标签，导致调度器无法匹配任何节点，符合 **nodeSelector/affinity 不匹配** 场景。

**排除项**：
- ❌ 资源不足 — QoS BestEffort，节点 Ready 且有 59 个 Running Pod
- ❌ taint/toleration — 无相关 FailedScheduling 信息
- ❌ PVC 未绑定 — Pod 无卷依赖
- ❌ Node 不可用 — 3 节点均为 Ready
- ❌ 镜像拉取 — 调度层问题，未到拉镜像阶段

**推荐修复方案**：修改 Pod spec 中的 `nodeSelector` 使用集群节点上真实存在的标签，或为节点添加 `aiops.e2e/nonexistent-node-label=true` 标签。
   ✅ [证据链采集] 完成 (20.2s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"ev1","description":"验证异常 Pod rc-pending-nodeselector 当前状态和详细信息，检查 nodeSelector、nodeAffinity、taint tolerations","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"验证 FailedScheduling 事件、nodeSelector/亲和性约束、节点调度条件","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev2","description":"验证 Pod 的 YAML 完整 spec，特别关注 nodeSelector、affinity、tolerations 字段","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"获取完整的 Pod spec 以验证 nodeSelector/affinity 配置","evidence_type":"","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"ev3","description":"获取集群所有节点的标签信息，验证哪些标签可用","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes --show-labels","tool_args":{"kind":"Node"},"purpose":"检查各节点标签，验证 nodeSelector 匹配条件是否满足","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev4","description":"获取 Pod 相关的调度事件，验证 FailedScheduling 细节","level":"important","tool":"kubectl_events","command":"kubectl events --for pod/rc-pending-nodeselector -n aiops-e2e","tool_args":{"namespace":"aiops-e2e","kind":"Pod","name":"rc-pending-nodeselector"},"purpose":"确认 FailedScheduling 事件内容和调度失败原因","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n5m7s        Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/569051fa283d4558/tools/001-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/569051fa283d4558/tools/001-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/569051fa283d4558/tools/001-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  5m7s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  5m7s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/569051fa283d4558/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/569051fa283d4558/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/569051fa283d4558/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   238d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          238d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\nnode2    Ready    <none>          238d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/569051fa283d4558/tools/003-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/569051fa283d4558/tools/003-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/569051fa283d4558/tools/003-evidence-kubectl_get_by_kind_in_cluster.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/569051fa283d4558/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/569051fa283d4558/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/569051fa283d4558/tools/004-evidence-kubectl_get_yaml.summary.txt"}],"llm_analysis":"所有关键证据已采集完毕。以下是证据结论：\n\n---\n\n## ✅ 已采集证据\n\n### ev1 — kubectl describe pod 详细描述（critical ✅）\n- **状态**：Pending，未绑定节点（`node: <none>`）\n- **调度事件**：`Warning FailedScheduling` → `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`\n- **nodeSelector**：`aiops.e2e/nonexistent-node-label=true`\n- **镜像**：busybox:1.36，`imagePullPolicy=Never`（空镜像拉取策略不影响调度）\n- **QoS**：BestEffort（无资源限制，排除资源不足）\n\n### ev2 — Pod YAML 完整配置（critical ✅）\n- `nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}` ✅ 确认标签选择器\n- `conditions.PodScheduled: status=False, reason=Unschedulable` ✅ 调度失败明确\n- 无 PVC/volume 依赖，排除存储前置条件\n- 无 deletionTimestamp/finalizers，排除 Terminating 卡住\n\n### ev3 — 集群 3 个节点标签全量检查（critical ✅）\n| 节点 | 状态 | 标签 |\n|------|------|------|\n| master | Ready | `kubernetes.io/hostname=master`, `node-role.kubernetes.io/control-plane=` 等 |\n| node1 | Ready | `kubernetes.io/hostname=node1` 等 |\n| node2 | Ready | `kubernetes.io/hostname=node2` 等 |\n\n**关键发现**：3 个节点均 **没有** `aiops.e2e/nonexistent-node-label` 标签 ✅\n\n### ev4 — Pod 事件确认（important ✅）\n- 唯一事件：`FailedScheduling`（5m7s 前），内容与 ev1/ev2 完全一致\n\n---\n\n## 📋 诊断结论\n\n**根因确认**：Pod `rc-pending-nodeselector` 设置了 `nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}`，而集群 3 个节点（master/node1/node2）均无此标签，导致调度器无法匹配任何节点，符合 **nodeSelector/affinity 不匹配** 场景。\n\n**排除项**：\n- ❌ 资源不足 — QoS BestEffort，节点 Ready 且有 59 个 Running Pod\n- ❌ taint/toleration — 无相关 FailedScheduling 信息\n- ❌ PVC 未绑定 — Pod 无卷依赖\n- ❌ Node 不可用 — 3 节点均为 Ready\n- ❌ 镜像拉取 — 调度层问题，未到拉镜像阶段\n\n**推荐修复方案**：修改 Pod spec 中的 `nodeSelector` 使用集群节点上真实存在的标签，或为节点添加 `aiops.e2e/nonexistent-node-label=true` 标签。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 8 个，匹配计划 4 个，未规划证据 4 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":4,"unplanned_tool_count":4,"evidence_inventory":[{"id":"ev1","description":"验证异常 Pod rc-pending-nodeselector 当前状态和详细信息，检查 nodeSelector、nodeAffinity、taint tolerations","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"验证 FailedScheduling 事件、nodeSelector/亲和性约束、节点调度条件","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev2","description":"验证 Pod 的 YAML 完整 spec，特别关注 nodeSelector、affinity、tolerations 字段","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"获取完整的 Pod spec 以验证 nodeSelector/affinity 配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev3","description":"获取集群所有节点的标签信息，验证哪些标签可用","level":"critical","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes --show-labels","purpose":"检查各节点标签，验证 nodeSelector 匹配条件是否满足","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev4","description":"获取 Pod 相关的调度事件，验证 FailedScheduling 细节","level":"important","tool":"kubectl_events","command":"kubectl events --for pod/rc-pending-nodeselector -n aiops-e2e","purpose":"确认 FailedScheduling 事件内容和调度失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_events","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | ev1 | critical | ✅ | kubectl_describe | 验证异常 Pod rc-pending-nodeselector 当前状态和详细信息，检查... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | ev2 | critical | ✅ | kubectl_get_yaml | 验证 Pod 的 YAML 完整 spec，特别关注 nodeSelector、affin... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | ev3 | critical | ✅ | kubectl_get_by_kind_in_cl... | 获取集群所有节点的标签信息，验证哪些标签可用 | `kubectl get nodes --show-labels` |
   | ev4 | important | ✅ | kubectl_events | 获取 Pod 相关的调度事件，验证 FailedScheduling 细节 | `kubectl events --for pod/rc-pending-nodeselector -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (24.0s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector（aiops-e2e 命名空间）处于 Pending 状态，根因是 nodeSelector 不匹配。Pod spec 设置了 nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}（ev1/ev2 确认），而集群 3 个节点（master、node1、node2）的标签列表中均不含该标签（ev3 确认）。调度器事件明确报告 "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"（ev4 确认）。已排除资源不足（QoS BestEffort，节点 Ready 且有 59 个 Running Pod）、taint/toleration（事件无相关提示）、PVC 未绑定（Pod 无卷依赖）等其他场景。
   confidence=99%
   causal_chain={"root_cause": "Pod rc-pending-nodeselector 的 spec 中设置了 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}，而集群全部 3 个节点（master、node1、node2）均无此标签", "propagation": "调度器在调度该 Pod 时，遍历所有 3 个节点检查 nodeSelector 条件，发现所有节点均不满足标签要求，返回 Unschedulable 状态，调度队列中该 Pod 被标记为不可调度且不触发抢占", "direct_cause": "nodeSelector 引用了不存在的节点标签 aiops.e2e/nonexistent-node-label=true，导致调度器无法为 Pod 找到匹配节点", "manifestation": "Pod rc-pending-nodeselector 保持在 Pending 状态超过 5 分钟，事件持续报 FailedScheduling，Pod 未绑定任何节点（node=<none>），IP 地址为空"}
   rca_analysis={"phenomenon": "集群中存在 1 个异常 Pod：rc-pending-nodeselector（aiops-e2e 命名空间），状态为 Pending，未绑定节点（node: \\<none\\>）。调度事件持续报 FailedScheduling：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。", "evidence_inventory": [{"id": "ev1", "source": "kubectl_describe", "content": "Pod rc-pending-nodeselector 状态 Pending，node=<none>，Node-Selectors=aiops.e2e/nonexistent-node-label=true，QoS BestEffort，无资源限制", "reliability": "高"}, {"id": "ev2", "source": "kubectl_get_yaml", "content": "Pod YAML 确认 nodeSelector={\"aiops.e2e/nonexistent-node-label\": \"true\"}，conditions.PodScheduled=False reason=Unschedulable，无 PVC 依赖，无 deletionTimestamp", "reliability": "高"}, {"id": "ev3", "source": "kubectl_get_by_kind_in_cluster", "content": "集群 3 个节点（master/node1/node2）均为 Ready 状态，标签列表均不含 aiops.e2e/nonexistent-node-label", "reliability": "高"}, {"id": "ev4", "source": "kubectl_events", "content": "Pod 唯一事件为 FailedScheduling（5m7s）：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}, {"id": "layer_1", "source": "layer_verified_kubectl_get_by_kind_in_cluster", "content": "集群 65 个 Pod，59 Running、1 Pending（即 rc-pending-nodeselector），无其他异常 Pod", "reliability": "高"}, {"id": "layer_3", "source": "layer_verified_kubectl_events", "content": "事件时间 4m36s，与 ev4 内容一致，均为 FailedScheduling 0/3 nodes", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "ev1", "raw_data": "Node-Selectors: aiops.e2e/nonexistent-node-label=true; Qos Class: BestEffort", "interpretation": "Pod 明确设置了 nodeSelector 要求标签 aiops.e2e/nonexistent-node-label=true，且 QoS 为 BestEffort 表明无资源限制，排除资源不足场景"}, {"evidence_id": "ev2", "raw_data": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}; conditions: PodScheduled=False reason=Unschedulable", "interpretation": "YAML 确认 nodeSelector 配置与 describe 一致，PodScheduled=False 且 reason=Unschedulable 是调度失败的明确标识；无 PVC/volume 依赖、无 deletionTimestamp 排除存储和 Terminating 场景"}, {"evidence_id": "ev3", "raw_data": "3 nodes Ready: master labels=[...,kubernetes.io/hostname=master,...], node1 labels=[...,kubernetes.io/hostname=node1,...], node2 labels=[...,kubernetes.io/hostname=node2,...]", "interpretation": "3 个节点全部 Ready 且标签列表中均无 aiops.e2e/nonexistent-node-label 标签，直接证明 nodeSelector 条件无法被任何节点满足"}, {"evidence_id": "ev4", "raw_data": "Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "interpretation": "调度器明确报告 3/3 节点均不匹配 Pod 的 node affinity/selector，与 nodeSelector 不匹配的结论完全吻合"}, {"evidence_id": "layer_1", "raw_data": "59 Running, 1 Pending; 异常行: aiops-e2e rc-pending-nodeselector 0/1 Pending", "interpretation": "集群其余 Pod 均正常运行，说明节点健康、集群整体正常，异常仅局限于该 Pod 的调度约束问题"}, {"evidence_id": "layer_3", "raw_data": "4m36s Warning FailedScheduling Pod/rc-pending-nodeselector 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "interpretation": "上游采集与当前采集的 FailedScheduling 事件时间和内容一致，证据可交叉验证，排除数据不一致"}], "causal_chain": {"root_cause": "Pod rc-pending-nodeselector 的 spec 中设置了 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}，而集群全部 3 个节点（master、node1、node2）均无此标签", "propagation": "调度器在调度该 Pod 时，遍历所有 3 个节点检查 nodeSelector 条件，发现所有节点均不满足标签要求，返回 Unschedulable 状态，调度队列中该 Pod 被标记为不可调度且不触发抢占", "direct_cause": "nodeSelector 引用了不存在的节点标签 aiops.e2e/nonexistent-node-label=true，导致调度器无法为 Pod 找到匹配节点", "manifestation": "Pod rc-pending-nodeselector 保持在 Pending 状态超过 5 分钟，事件持续报 FailedScheduling，Pod 未绑定任何节点（node=<none>），IP 地址为空"}, "root_cause": "Pod rc-pending-nodeselector（aiops-e2e 命名空间）处于 Pending 状态，根因是 nodeSelector 不匹配。Pod spec 设置了 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}（ev1/ev2 确认），而集群 3 个节点（master、node1、node2）的标签列表中均不含该标签（ev3 确认）。调度器事件明确报告 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"（ev4 确认）。已排除资源不足（QoS BestEffort，节点 Ready 且有 59 个 Running Pod）、taint/toleration（事件无相关提示）、PVC 未绑定（Pod 无卷依赖）等其他场景。", "root_cause_summary": "Pod rc-pending-nodeselector（aiops-e2e 命名空间）处于 Pending 状态，根因是 nodeSelector 不匹配。Pod spec 设置了 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}（ev1/ev2 确认），而集群 3 个节点（master、node1、node2）的标签列表中均不含该标签（ev3 确认）。调度器事件明确报告 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"（ev4 确认）。已排除资源不足（QoS BestEffort，节点 Ready 且有 59 个 Running Pod）、taint/toleration（事件无相关提示）、PVC 未绑定（Pod 无卷依赖）等其他场景。", "confidence": 0.99, "confidence_reason": "所有关键证据（ev1~ev4）相互交叉验证，因果链完整闭合：Pod spec 明确展示 nodeSelector 值（ev1/ev2）、节点标签全量确认该标签不存在（ev3）、调度事件直接给出不匹配结论（ev4）。无任何矛盾或缺失环节，置信度极高。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "集群资源不足（CPU/内存不足）", "probability": "low", "reason": "Pod QoS 为 BestEffort，无资源 requests/limits；且调度事件未报告 Insufficient cpu/memory，而是明确报告 node affinity/selector 不匹配"}, {"cause": "节点 taint 未容忍", "probability": "low", "reason": "Pod 已有 tolerations（node.kubernetes.io/not-ready:NoExecute），且 FailedScheduling 事件未提及 taint 相关原因，直接指向 node affinity/selector"}, {"cause": "PVC/PV 未绑定导致调度阻塞", "probability": "low", "reason": "Pod YAML 中 volumes 仅包含 kube-api-access-w74s5（ServiceAccount token 投射卷），无 PVC 依赖"}, {"cause": "节点 NotReady 或不可用", "probability": "low", "reason": "3 节点均为 Ready 状态（ev3），集群有 59 个 Running Pod 证明节点健康且运行正常"}], "limitations": "证据覆盖完整，无缺失。仅有一个异常 Pod，分析边界清晰。", "llm_raw_analysis": "L1 根因分析完成。异常组 g1（PendingUnschedulable）仅含一个 Pod rc-pending-nodeselector。所有证据指向 nodeSelector 不匹配这一根因，无其他异常 Pod 或 issue group 需要分析。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector（aiops-e2e 命名空间）处于 Pending 状态，根因是 nodeSelector 不匹配。Pod spec 设置了 nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}（...
   置信度: 99%
   🔗 因果链:
     根本原因: Pod rc-pending-nodeselector 的 spec 中设置了 nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}，而集群全部 3 个节点（master、node1、node2）均无此标签
     传导机制: 调度器在调度该 Pod 时，遍历所有 3 个节点检查 nodeSelector 条件，发现所有节点均不满足标签要求，返回 Unschedulable 状态，调度队列中该 Pod 被标记为不可调度且不触发抢占
     最终表现: Pod rc-pending-nodeselector 保持在 Pending 状态超过 5 分钟，事件持续报 FailedScheduling，Pod 未绑定任何节点（node=<none>），IP 地址为空


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (23.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5732 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 34.5s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将为您呈现一份详尽、完整的诊断报告。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **集群健康总览** | 集群共有 65 个 Pod，其中 59 个运行正常，1 个异常。当前发现一个问题。 |
| **Pod异常状态** | Pending |
| **兼容归因层** | L1 - 调度层 |
| **问题分类** | PendingUnschedulable (调度失败) |
| **置信度** | 高 (99%) |
| **证据完整度** | 4/4 (100%) |

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-pending-nodeselector` |
| Namespace | `aiops-e2e` |
| Node | 集群全部 3 个节点 (`master`, `node1`, `node2`) |
| 错误信息 | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` |

---
## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl describe` | `status: Pending` <br> `Node-Selectors: aiops.e2e/nonexistent-node-label=true` <br> `Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | Pod 因 nodeSelector 约束无法被调度到任何节点。 |
| 2 | Pod 完整配置 | `kubectl get yaml` | `nodeSelector: aiops.e2e/nonexistent-node-label: "true"` <br> `finalizers: <none>` <br> `terminationGracePeriodSeconds: 30` <br> `deletionGracePeriodSeconds: None` | Pod 配置明确要求节点必须具有 `aiops.e2e/nonexistent-node-label=true` 标签，且不存在因 finalizer 或优雅退出导致的卡住问题。 |
| 3 | 节点标签信息 | `kubectl get nodes` | `master` 标签: `beta.kubernetes.io/arch=amd64, kubernetes.io/hostname=master, node-role.kubernetes.io/control-plane=`, ...<br> `node1` 标签: `beta.kubernetes.io/arch=amd64, kubernetes.io/hostname=node1`, ...<br> `node2` 标签: `beta.kubernetes.io/arch=amd64, kubernetes.io/hostname=node2`, ...<br> 所有节点状态均为 `Ready`。 | 集群3个节点的标签列表均 **不包含** `aiops.e2e/nonexistent-node-label` 标签。 |
| 4 | 调度事件 | `kubectl events` | `5m7s Warning FailedScheduling Pod/rc-pending-nodeselector 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..` | 调度器遍历所有节点后，明确因节点亲和性/选择器不匹配而失败，且由于资源未被占满，抢占机制也无帮助。 |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：Pod 的 `nodeSelector` 要求节点具有 `aiops.e2e/nonexistent-node-label=true` 标签，但集群所有3个节点的标签列表均不包含此标签。这直接导致调度器无法找到可用节点。
- **证据 #4 佐证**：调度事件信息 `3 node(s) didn't match Pod's node affinity/selector` 是上述结论的直接证明。

### 缺失证据（如有）
所有关键证据（Pod 状态、YAML配置、节点标签、调度事件）均已采集，无缺失。

---
## 🎯 根因分析

### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                         │
│ Pod (`rc-pending-nodeselector`) 的 spec 中设置了 nodeSelector:                     │
│ `{"aiops.e2e/nonexistent-node-label": "true"}`。                                 │
│ 但集群所有3个节点均未打上此标签。                                                │
└──────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                         │
│ 调度器 (default-scheduler) 在调度 Pod 时，遍历所有节点并检查节点标签是否匹配      │
│ Pod 的 nodeSelector 要求，所有节点均不满足，调度失败。                           │
└──────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                         │
│ Pod 无法被调度 (Unschedulable)，调度队列中该 Pod 被标记为不可调度且不触发抢占。    │
└──────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                     │
│ Pod 保持 `Pending` 状态超过5分钟，事件中持续输出 `FailedScheduling` 错误，         │
│ Pod 未绑定任何节点（`node=<none>`），IP 地址为空。                               │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (nodeSelector: aiops.e2e/nonexistent-node-label=true)、证据 #2 (YAML 确认) 和证据 #3 (节点标签列表)，问题的根本原因是 **Pod 配置的 `nodeSelector` 引用了集群节点不存在的标签**，导致调度器无法完成调度。

**置信度**：高 (99%)
- ✅ 证据链完整且明确：Pod spec → 节点标签 → 调度事件，指向同一结论。
- ✅ 已基于权威工具事实排除资源不足（集群有59个Running Pod）、taint/toleration（事件无相关提示）、finalizer 未清理等常见原因。

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）
**1. [推荐] 修复 Pending Pod：移除错误的 nodeSelector 或更正为正确的节点标签**
此方案将移除 nodeSelector 约束，使 Pod 能被调度到任意节点。

```bash
# 方案A：移除 nodeSelector，让Pod可以调度到任何满足资源条件的节点
kubectl patch pod rc-pending-nodeselector -n aiops-e2e -p '{"spec": {"nodeSelector": null}}'
```
*依据*：根源是 nodeSelector 标签不匹配，移除该约束即可解决调度问题。如果 Pod 由 Deployment 管理，请直接修改 Deployment 的 spec。

**2. [备选] 如果必须使用该节点标签，请为特定节点打上标签**
```bash
# 方案B：如果必须将Pod调度到特定节点（例如 node1），请先为该节点打上标签
kubectl label node node1 aiops.e2e/nonexistent-node-label=true
```
*结果*：执行后，Pod 将自动被调度到打了标签的节点上。

### 后续优化
1. **规范标签管理**：在 CI/CD 或部署流程中增加 Pod `nodeSelector` 与节点标签的校验环节，防止类似错误再次发生。
2. **预检脚本**：可以在部署前使用以下命令检查节点是否存在所需标签：
   ```bash
   # 检查节点是否有特定标签
   kubectl get nodes -l aiops.e2e/nonexistent-node-label=true
   ```
   如果返回空，说明没有任何节点匹配，应提前中止部署。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS 从 `Pending` 变为 `Running` 或 `ContainerCreating` |
| 2. 检查调度事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | Events 中不再出现 `FailedScheduling` 错误 |
| 3. 确认 Pod 所在节点 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o wide` | `NODE` 列显示具体节点名称（如 `node1`），而非 `<none>` |

---
## ⚠️ 注意事项
- 此问题纯粹是集群配置/应用部署配置错误，不影响集群中其他59个正在运行的应用。
- 如果 Pod 是由 Deployment 管理的，建议修改 Deployment 的 YAML 而非直接修改 Pod，以便更新的配置能持续生效。
- 建议使用 `kubectl get pods -A --field-selector=status.phase!=Running` 定期巡检，及时发现 Pending 状态并阻截在早期。

---

## 📊 性能统计

├─ 总耗时: 1.6m
├─ 问题定位: 26.3s (28%) ✅
├─ 证据链采集: 20.2s (21%) ✅
├─ 根因分析: 24.0s (25%) ✅
├─ 汇总总结: 23.9s (25%) ✅
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
