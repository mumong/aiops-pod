======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: f79bd49c450c409a]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来先扫描一下集群中所有 Pod 的状态，看看是否存在异常。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 我发现了一个异常 Pod。让我进一步查看它的详细信息。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  7m11s  default-scheduler  0/3 nodes are available: 3 node(s) di
   💭 [问题定位] 好的，情况很清晰了。让我获取相关的 runbook 作为参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在我已经获取了足够的信息。让我做一个完整的分析。

---

## 集群异常诊断分析

### 当前集群 Pod 状态总览

| 状态 | 数量 |
|------|------|
| ✅ Running | 59 个 |
| ❌ Pending | 1 个 |
| **总计** | **60 个 Pod** |

### 发现的异常 Pod

| 命名空间 | Pod 名称 | 状态 | 异常类型 |
|---------|---------|:----:|:--------:|
| `aiops-e2e` | `rc-pending-nodeselector` | Pending | **PendingUnschedulable** |

---

### 异常详情

**Pod:** `rc-pending-nodeselector`（命名空间：`aiops-e2e`）

- **STATUS:** Pending（未调度到任何节点）
- **NODE:** `<none>`（未绑定节点）

**调度失败原因：**  
`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`

Pod 设置了节点选择器：`aiops.e2e/nonexistent-node-label=true`，而集群中 **3 个节点均没有这个标签**，因此没有任何节点满足调度条件。

**其他特征：**
- QoS Class: `BestEffort`（无资源限制请求）
- 镜像: `busybox:1.36`，启动命令 `sleep 3600`
- 该 Pod 是 E2E 测试 Pod（`rootcause-e2e=true` 标签），用于验证节点选择器不匹配的场景

---

### 分层输出

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **layer_name** | PendingUnschedulable |
| **pod_status_keyword** | Pending |
| **pod_abnormal_type** | PendingUnschedulable |
| **status_category** | scheduling |
| **confidence** | 高 |

### 异常组

```
abnormal_groups = {
  "PendingUnschedulable": ["aiops-e2e/rc-pending-nodeselector"]
}
```

### 可能场景

1. **节点选择器不匹配（已确认）** — Pod 使用了 `aiops.e2e/nonexistent-node-label=true`，而集群中的 3 个节点都没有这个标签，导致调度器无法放置。
2. **E2E 测试场景** — 从 Pod 标签 `rootcause-e2e=true` 和命名空间 `aiops-e2e` 来看，这很可能是一个故意构造的测试用例，用于验证 Pod 因节点标签不匹配而 Pending 的故障场景。

### 后续审查方向

- 确认该 Pod 是否为有意的测试用例（如果是，则无需修复）
- 如果是正式业务 Pod，需要在节点上添加匹配的标签，或修改 Pod 的 `nodeSelector`/`affinity` 配置
- 检查是否有其他同类 Pending Pod 需要一并处理
   ✅ [问题定位] 完成 (24.2s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '节点选择器不匹配', 'probability': '高', 'reason': 'Pod设置nodeSelector=aiops.e2e/nonexistent-node-label=true，集群3个节点均无此标签，调度器无法放置'}, {'scenario': 'E2E测试场景', 'probability': '中', 'reason': 'Pod标签rootcause-e2e=true且命名空间aiops-e2e，可能为故意构造的测试用例'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}]
   reasoning=集群中存在1个Pending状态的异常Pod（rc-pending-nodeselector），调度失败原因为节点选择器标签不匹配（3个节点均无aiops.e2e/nonexistent-node-label=true标签），属于调度约束不匹配的PendingUnschedulable场景，对应L1层级。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "集群中存在1个Pending状态的异常Pod（rc-pending-nodeselector），调度失败原因为节点选择器标签不匹配（3个节点均无aiops.e2e/nonexistent-node-label=true标签），属于调度约束不匹配的PendingUnschedulable场景，对应L1层级。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Namespace", "name": "aiops-e2e", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "节点选择器不匹配", "probability": "高", "reason": "Pod设置nodeSelector=aiops.e2e/nonexistent-node-label=true，集群3个节点均无此标签，调度器无法放置"}, {"scenario": "E2E测试场景", "probability": "中", "reason": "Pod标签rootcause-e2e=true且命名空间aiops-e2e，可能为故意构造的测试用例"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              7m10s   <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我已收到上游的 layer_handoff 和既有 evidence_plan。现在直接执行计划中的关键工具，先执行两个 critical 级别的工具：
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
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
  Warning  FailedScheduling  7m42s  default-scheduler  0/3 nodes are available: 3 node(s) di
   💭 [证据链采集] 好的，Pod YAML 和 describe 已确认调度失败原因。接下来执行两个 important 级别的节点标签验证工具：
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAME     STATUS   ROLES           AGE    VERSION   LABELS\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] 让我再完整看一下所有节点的标签，确认没有遗漏：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": false, "stdout": "", "stderr": "jq: error: syntax error, unexpected INVALID_CHARACTER (Unix shell quoting issues?) at <top-level>, line 1:\n.items[] | \"\\(.metadata.name): \\(.metadata.la
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "master: beta.kubernetes.io/arch, beta.kubernetes.io/os, fpga-version, kubernetes.io/arch, kubernetes.io/hostname, kubernetes.io/os, metax-tech.com/gpu.installed, node-role
   💭 [证据链采集] 现在也检查一下是否存在其他异常 Pod，确保没有遗漏异常组：
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [证据链采集] 所有计划中的工具已执行完毕。以下是证据采集结论：

---

## 证据采集结论

### ✅ 已采集证据（4条）

**e1 - Pod YAML 调度约束配置** ✅
- `rc-pending-nodeselector` 设置了 `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}`
- Pod 仅有默认 tolerations（`not-ready:NoExecute op=Exists for 300s`）
- PodScheduled 条件：`status=False, reason=Unschedulable`

**e2 - FailedScheduling 事件原文** ✅
- 两条 Warning 事件，核心原文：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.`
- 确认调度失败原因为 **节点选择器/亲和性不匹配**

**e3/e4 - 节点标签验证** ✅
- 集群共 3 个节点：`master`、`node1`、`node2`，全部 Ready
- 3 个节点的标签集合中 **均不包含 `aiops.e2e/nonexistent-node-label`** 标签
- 标签包括：`kubernetes.io/hostname`、`beta.kubernetes.io/arch`、`beta.kubernetes.io/os`、`fpga-version`、`metax-tech.com/gpu.installed` 等，均与 Pod 需要的 `aiops.e2e/nonexistent-node-label=true` 不匹配

### ✅ 负向/冲突证据
- **无冲突证据**：Pod 确认存在于 `aiops-e2e` 命名空间，3 个节点均 Ready 且标签可验证
- **无其他异常组**：全集群 65 个 Pod 中 59 个 Running，仅此 1 个 Pending，无并发异常

### 📋 根因结论
Pod `rc-pending-nodeselector`（命名空间 `aiops-e2e`）因设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，而集群 3 个节点均无此标签，导致调度器无法放置，持续 Pending。该 Pod 带有 `rootcause-e2e=true` 标签，疑似 E2E 测试场景的构造用例。
   ✅ [证据链采集] 完成 (26.9s)
   📤 → 下游数据: evidence_items=5/6
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"获取Pod rc-pending-nodeselector的完整YAML配置，检查nodeSelector/affinity设置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"验证Pod的nodeSelector/affinity/toleration等调度约束配置","evidence_type":"","target_scope":"pod_rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e2","description":"查看Pod最新事件，确认FailedScheduling详细原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"采集FailedScheduling事件原文，确认调度失败具体原因","evidence_type":"","target_scope":"pod_rc-pending-nodeselector","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"查询集群所有节点信息，确认节点标签和状态","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o wide","tool_args":{},"purpose":"查看集群节点标签，验证是否缺少Pod所需的nodeSelector标签","evidence_type":"","target_scope":"cluster_nodes","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"查看节点标签详情，确认是否有aiops.e2e/nonexistent-node-label标签","level":"important","tool":"run_bash_command","command":"kubectl get nodes --show-labels","tool_args":{},"purpose":"验证所有节点的标签集合，确认是否匹配Pod的nodeSelector","evidence_type":"","target_scope":"cluster_node_labels","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  7m42s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  2m13s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  7m42s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  2m13s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}\nNAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION       CONTAINER-RUNTIME     LABELS\n# 样例行\nmaster   Ready    control-plane   238d   v1.26.8   10.2.0.48     <none>        Ubuntu 22.04.4 LTS   5.15.0-173-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\nnode1    Ready    <none>          238d   v1.26.8   10.2.0.49     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\nnode2    Ready    <none>          238d   v1.26.8   10.2.0.50     <none>        Ubuntu 22.04.4 LTS   5.15.0-176-generic   containerd://1.6.32   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/003-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/003-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/003-evidence-kubectl_get_by_kind_in_cluster.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAME     STATUS   ROLES           AGE    VERSION   LABELS\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/004-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/004-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/004-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": false, \"stdout\": \"\", \"stderr\": \"jq: error: syntax error, unexpected INVALID_CHARACTER (Unix shell quoting issues?) at <top-level>, line 1:\\n.items[] | \\\"\\\\(.metadata.name): \\\\(.metadata.labels | keys | join(\\\\\\\", \\\\\\\"))\\\"                                                                \\njq: 1 compile error\\n\", \"returncode\": 3}","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/005-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/005-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/005-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"master: beta.kubernetes.io/arch, beta.kubernetes.io/os, fpga-version, kubernetes.io/arch, kubernetes.io/hostname, kubernetes.io/os, metax-tech.com/gpu.installed, node-role.kubernetes.io/control-plane, node.kubernetes.io/exclude-from-external-load-balancers\\nnode1: beta.kubernetes.io/arch, beta.kubernetes.io/os, fpga-version, kubernetes.io/arch, kubernetes.io/hostname, kubernetes.io/os, metax-tech.com/gpu.installed\\nnode2: beta.kubernetes.io/arch, beta.kubernetes.io/os, fpga-version, kubernetes.io/arch, kubernetes.io/hostname, kubernetes.io/os, metax-tech.com/gpu.installed\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/006-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/006-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/006-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_get_by_kind_in_cluster","data":"kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}\nNAMESPACE         NAME                                                READY   STATUS      RESTARTS       AGE     IP               NODE     NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\naiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              7m52s   <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/007-evidence-kubectl_get_by_kind_in_cluster.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/007-evidence-kubectl_get_by_kind_in_cluster.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/f79bd49c450c409a/tools/007-evidence-kubectl_get_by_kind_in_cluster.summary.txt"}],"llm_analysis":"所有计划中的工具已执行完毕。以下是证据采集结论：\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据（4条）\n\n**e1 - Pod YAML 调度约束配置** ✅\n- `rc-pending-nodeselector` 设置了 `nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}`\n- Pod 仅有默认 tolerations（`not-ready:NoExecute op=Exists for 300s`）\n- PodScheduled 条件：`status=False, reason=Unschedulable`\n\n**e2 - FailedScheduling 事件原文** ✅\n- 两条 Warning 事件，核心原文：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.`\n- 确认调度失败原因为 **节点选择器/亲和性不匹配**\n\n**e3/e4 - 节点标签验证** ✅\n- 集群共 3 个节点：`master`、`node1`、`node2`，全部 Ready\n- 3 个节点的标签集合中 **均不包含 `aiops.e2e/nonexistent-node-label`** 标签\n- 标签包括：`kubernetes.io/hostname`、`beta.kubernetes.io/arch`、`beta.kubernetes.io/os`、`fpga-version`、`metax-tech.com/gpu.installed` 等，均与 Pod 需要的 `aiops.e2e/nonexistent-node-label=true` 不匹配\n\n### ✅ 负向/冲突证据\n- **无冲突证据**：Pod 确认存在于 `aiops-e2e` 命名空间，3 个节点均 Ready 且标签可验证\n- **无其他异常组**：全集群 65 个 Pod 中 59 个 Running，仅此 1 个 Pending，无并发异常\n\n### 📋 根因结论\nPod `rc-pending-nodeselector`（命名空间 `aiops-e2e`）因设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，而集群 3 个节点均无此标签，导致调度器无法放置，持续 Pending。该 Pod 带有 `rootcause-e2e=true` 标签，疑似 E2E 测试场景的构造用例。","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 5/6 项，完整度 83%；实际执行工具 8 个，匹配计划 3 个，未规划证据 5 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":6,"environment_evidence_collected":5,"environment_evidence_completeness":0.8333333333333334,"executed_tool_count":8,"matched_tool_count":3,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"获取Pod rc-pending-nodeselector的完整YAML配置，检查nodeSelector/affinity设置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"验证Pod的nodeSelector/affinity/toleration等调度约束配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"查看Pod最新事件，确认FailedScheduling详细原因","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"采集FailedScheduling事件原文，确认调度失败具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"查询集群所有节点信息，确认节点标签和状态","level":"important","tool":"kubectl_get_by_kind_in_cluster","command":"kubectl get nodes -o wide","purpose":"查看集群节点标签，验证是否缺少Pod所需的nodeSelector标签","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"查看节点标签详情，确认是否有aiops.e2e/nonexistent-node-label标签","level":"important","tool":"run_bash_command","command":"kubectl get nodes --show-labels","purpose":"验证所有节点的标签集合，确认是否匹配Pod的nodeSelector","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["e4(查看节点标签详情，确认是否有aiops.e2e/nonexistent-node-label标签): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 83%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_yaml | 获取Pod rc-pending-nodeselector的完整YAML配置，检查node... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e2 | critical | ✅ | kubectl_describe | 查看Pod最新事件，确认FailedScheduling详细原因 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e3 | important | ✅ | kubectl_get_by_kind_in_cl... | 查询集群所有节点信息，确认节点标签和状态 | `kubectl get nodes -o wide` |
   | e4 | important | ❌ | run_bash_command | 查看节点标签详情，确认是否有aiops.e2e/nonexistent-node-label标签 | `kubectl get nodes --show-labels` |

   ⚠️ 未采集原因:
   - e4(查看节点标签详情，确认是否有aiops.e2e/nonexistent-node-label标签): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (23.2s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector (namespace: aiops-e2e) 处于 Pending 状态，原因是 Pod 设置了 nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}（证据 e1），调度器两次 FailedScheduling 事件均报告 "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"（证据 e2）。集群 3 个节点（master, node1, node2）全部 Ready，但标签集合中均不包含 aiops.e2e/nonexistent-node-label 键（证据 e3/e4），导致没有任何节点可调度。集群其余 59 个 Pod 均正常运行，无其他异常组（证据 e5）。该 Pod 带有 pod_abnormal_type=PendingUnschedulable 和 rootcause-e2e=true 标签，可能为 E2E 测试构造用例。
   confidence=98%
   causal_chain={"root_cause": "Pod rc-pending-nodeselector 设置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，而集群 3 个健康节点均无此标签，导致调度器无法放置，持续 Pending。该 Pod 带有 rootcause-e2e=true 标签，疑似 E2E 测试构造用例。", "propagation": "Pod spec 定义 → 调度器解析 nodeSelector → 遍历 3 个节点标签 → 均不匹配 → 标记 Unschedulable → 重试 2 次仍失败 → Pod 持续 Pending", "direct_cause": "nodeSelector 约束 `aiops.e2e/nonexistent-node-label=true` 在集群中没有节点满足", "manifestation": "Pod rc-pending-nodeselector 状态为 Pending，0/1 Ready，无绑定节点，Events 中持续出现 FailedScheduling 警告"}
   rca_analysis={"phenomenon": "集群 aiops-e2e 命名空间中 Pod rc-pending-nodeselector 处于 Pending 状态，status=0/1，已持续约 7.5 分钟，IP 和 Node 均为 <none>。", "evidence_inventory": [{"id": "e1", "source": "kubectl_get_yaml", "content": "Pod rc-pending-nodeselector 设置了 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}，PodScheduled 条件 status=False, reason=Unschedulable", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe", "content": "两条 FailedScheduling 事件：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_by_kind_in_cluster", "content": "集群 3 个节点（master, node1, node2）均 Ready，标签列表中均不含 aiops.e2e/nonexistent-node-label", "reliability": "高"}, {"id": "e4", "source": "run_bash_command (kubectl+ jq)", "content": "各节点标签明细确认：master/node1/node2 标签集合中均无 aiops.e2e/nonexistent-node-label 标签", "reliability": "高"}, {"id": "e5", "source": "kubectl_get_by_kind_in_cluster (全集群Pod)", "content": "全集群 65 Pod，59 Running，仅此 1 个 Pending，无其他异常组", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\nconditions: PodScheduled status=False reason=Unschedulable", "interpretation": "Pod 明确要求调度到具有 aiops.e2e/nonexistent-node-label=true 标签的节点，调度器判定为 Unschedulable"}, {"evidence_id": "e2", "raw_data": "Warning FailedScheduling 7m42s/2m13s: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "interpretation": "调度器明确报告所有 3 个节点均不满足 nodeSelector/affinity 约束，两次重试均失败"}, {"evidence_id": "e3", "raw_data": "rows=3 abnormal=0 status_counts={'Ready': 3}\nmaster labels: beta.kubernetes.io/arch,beta.kubernetes.io/os,..., node-role.kubernetes.io/control-plane,...\nnode1 labels: beta.kubernetes.io/arch,...,kubernetes.io/os,...\nnode2 labels: 同上", "interpretation": "集群 3 节点全部 Ready 且健康，但标签集合中均不包含 aiops.e2e/nonexistent-node-label 键"}, {"evidence_id": "e4", "raw_data": "master: beta.kubernetes.io/arch, beta.kubernetes.io/os, fpga-version, kubernetes.io/arch, kubernetes.io/hostname, kubernetes.io/os, metax-tech.com/gpu.installed, node-role.kubernetes.io/control-plane\nnode1: 同范围不含 aiops.e2e/nonexistent-node-label\nnode2: 同范围不含", "interpretation": "基于 jsonpath 提取的节点标签键集合验证确认：3 个节点均无 aiops.e2e/nonexistent-node-label 标签，标签不存在而非值不匹配"}, {"evidence_id": "e5", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}", "interpretation": "集群除该 Pod 外所有工作负载正常运行，无并发异常组，故障范围局限于 rc-pending-nodeselector 一个 Pod"}], "causal_chain": {"root_cause": "Pod rc-pending-nodeselector 设置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，而集群 3 个健康节点均无此标签，导致调度器无法放置，持续 Pending。该 Pod 带有 rootcause-e2e=true 标签，疑似 E2E 测试构造用例。", "propagation": "Pod spec 定义 → 调度器解析 nodeSelector → 遍历 3 个节点标签 → 均不匹配 → 标记 Unschedulable → 重试 2 次仍失败 → Pod 持续 Pending", "direct_cause": "nodeSelector 约束 `aiops.e2e/nonexistent-node-label=true` 在集群中没有节点满足", "manifestation": "Pod rc-pending-nodeselector 状态为 Pending，0/1 Ready，无绑定节点，Events 中持续出现 FailedScheduling 警告"}, "root_cause": "Pod rc-pending-nodeselector (namespace: aiops-e2e) 处于 Pending 状态，原因是 Pod 设置了 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}（证据 e1），调度器两次 FailedScheduling 事件均报告 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"（证据 e2）。集群 3 个节点（master, node1, node2）全部 Ready，但标签集合中均不包含 aiops.e2e/nonexistent-node-label 键（证据 e3/e4），导致没有任何节点可调度。集群其余 59 个 Pod 均正常运行，无其他异常组（证据 e5）。该 Pod 带有 pod_abnormal_type=PendingUnschedulable 和 rootcause-e2e=true 标签，可能为 E2E 测试构造用例。", "root_cause_summary": "Pod rc-pending-nodeselector (namespace: aiops-e2e) 处于 Pending 状态，原因是 Pod 设置了 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}（证据 e1），调度器两次 FailedScheduling 事件均报告 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"（证据 e2）。集群 3 个节点（master, node1, node2）全部 Ready，但标签集合中均不包含 aiops.e2e/nonexistent-node-label 键（证据 e3/e4），导致没有任何节点可调度。集群其余 59 个 Pod 均正常运行，无其他异常组（证据 e5）。该 Pod 带有 pod_abnormal_type=PendingUnschedulable 和 rootcause-e2e=true 标签，可能为 E2E 测试构造用例。", "confidence": 0.98, "confidence_reason": "拥有多条直接证据形成完整因果链：Pod YAML 证实 nodeSelector 约束（e1）、调度器事件原文确认全部节点均不匹配（e2）、节点标签清单证实目标标签在所有 3 个节点上均不存在（e3/e4）、全集群 Pod 状态确认无并发异常（e5）。证据充分、无冲突、因果链清晰。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "节点资源不足（CPU/内存不足导致无法调度）", "probability": "low", "reason": "FailedScheduling 事件明确报告 'didn't match Pod's node affinity/selector'，而非 Insufficient cpu/memory；且 3 节点均为 Ready 状态，集群其他 59 Pod 正常运行"}, {"cause": "节点 taint 未被容忍", "probability": "low", "reason": "调度器错误信息未提及 taint 相关原因，且 Pod 有默认 tolerations（not-ready:NoExecute）"}, {"cause": "PVC 未绑定导致调度阻塞", "probability": "low", "reason": "Pod 仅有一个 kube-api-access 投影卷，无 PVC 依赖；事件未提及 PersistentVolumeClaims"}], "limitations": "已采集的证据完整覆盖了根因所需的全部维度（Pod 调度约束、调度事件、节点标签、全集群状态），无缺失证据。无需额外采集。", "llm_raw_analysis": "## 证据清点\\n共 5 条有效证据：e1 Pod YAML（nodeSelector 配置）、e2 FailedScheduling 事件、e3 节点列表及标签、e4 节点标签键明细、e5 全集群 Pod 状态。缺失证据 e4 已通过工具采集补全。\\n\\n## 逐条分析\\n- e1: Pod 明确设置 nodeSelector 要求 aiops.e2e/nonexistent-node-label=true，直接定义调度约束\\n- e2: 调度器两次报告全部 3 节点均不匹配 affinity/selector，排除资源不足等其它原因\\n- e3/e4: 3 节点标签集合确认均无此标签，且节点全部 Ready 健康\\n- e5: 集群无其他异常，故障范围单一\\n\\n## 关联分析\\ne1 定义约束 → e2 报告约束无法满足 → e3/e4 验证约束确实无法满足 → e5 确认这是集群唯一问题。证据链完整闭环。\\n\\n## 因果链\\n根因：Pod nodeSelector 引用了集群中不存在的标签 → 直接原因：调度器找不到匹配节点 → 现象：Pod 持续 Pending 并产生 F\n... 截断，原始 518 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector (namespace: aiops-e2e) 处于 Pending 状态，原因是 Pod 设置了 nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}（证据 e1），调度器两次 F...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod rc-pending-nodeselector 设置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，而集群 3 个健康节点均无此标签，导致调度器无法放置，持续 Pending。该 Pod 带有 rootcause-e2e=true 标签，疑似 E2E 测试构造用例。
     传导机制: Pod spec 定义 → 调度器解析 nodeSelector → 遍历 3 个节点标签 → 均不匹配 → 标记 Unschedulable → 重试 2 次仍失败 → Pod 持续 Pending
     最终表现: Pod rc-pending-nodeselector 状态为 Pending，0/1 Ready，无绑定节点，Events 中持续出现 FailedScheduling 警告


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (20.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4502 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 34.9s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将基于您提供的诊断数据，为您生成一份详尽、完整的诊断报告。

---
## 📊 诊断概览

**核心回答：** 您的集群整体运行健康，59 个 Pod 正常运行。目前仅发现 **1 个 Pending 状态的异常 Pod**。该问题并非集群故障，而是由于一个 Pod 的调度约束（nodeSelector）配置错误，导致无法被调度到任何节点上。

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending |
| **兼容归因层** | L1 - 基础调度异常 |
| **问题分类** | PendingUnschedulable (调度约束不匹配) |
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
| Node | <none> (未调度) |
| 错误信息 | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` |
---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 配置 | `kubectl get pod rc-pending-nodeselector -o yaml` | `nodeSelector: aiops.e2e/nonexistent-node-label=true` | Pod 要求节点必须包含 `aiops.e2e/nonexistent-node-label=true` 标签 |
| 2 | Pod 事件 | `kubectl describe pod rc-pending-nodeselector` | `Warning FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 调度器明确告知，**3 个节点均不满足** Pod 的调度约束 |
| 3 | 节点状态与标签 | `kubectl get nodes` | 三个节点 (master, node1, node2) **状态均为 Ready** | 集群节点本身是健康的，问题不在节点 |
| 4 | 节点标签列表 | `kubectl get nodes --show-labels` | 节点标签列表：`beta.kubernetes.io/arch, beta.kubernetes.io/os, fpga-version, kubernetes.io/arch...` | **三个节点均不包含** `aiops.e2e/nonexistent-node-label` 标签键 |
### 证据关联分析
- **证据 #1 + #2 + #4 印证**：Pod 要求节点标签 `aiops.e2e/nonexistent-node-label=true` (证据 #1)，调度器查询所有3个健康节点后均不满足此条件 (证据 #4)，因此触发 FailedScheduling 事件 (证据 #2)。
- **证据 #2 + #3 印证**：集群 `3/3` 的节点都是 `Ready` 状态，排除了节点不可用导致调度失败的场景，确认问题出在 Pod 自身的约束上。
- **证据链**：Pod 配置 `nodeSelector` → 调度器检查节点标签 → 无节点匹配 → Pod 持续 `Pending`。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| (无) | - | - |

---
## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                │
│ Pod rc-pending-nodeselector 配置了 nodeSelector:                         │
│ {"aiops.e2e/nonexistent-node-label": "true"}，该标签在集群中不存在。     │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                │
│ Scheduler 加载 Pod -> 解析 nodeSelector -> 遍历集群所有3个节点标签 ->    │
│ 均不匹配 -> 标记为 Unschedulable                                        │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                │
│ 调度器无法将 Pod 分配到任何节点（nodeSelector 不匹配）                  │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                            │
│ Pod rc-pending-nodeselector 状态为 Pending，0/1 容器就绪。              │
└─────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #1 (Pod YAML 中的 `nodeSelector`) 和证据 #4 (节点标签列表)，问题的根本原因是 **Pod 的 nodeSelector 指定了一个不存在的标签 `aiops.e2e/nonexistent-node-label=true`**，导致集群中没有任何一个节点满足调度条件，因此 Pod 持续 Pending。

**置信度**：高 (98%)
- ✅ Pod YAML 明确指示了不存在的标签选择器
- ✅ 调度器事件明确报告了节点不匹配
- ✅ 3个节点状态均为 Ready，排除了节点层面的故障
- ⚠️ 该 Pod 带有 `rootcause-e2e=true` 标签，很可能是一个用于测试的 E2E 用例，而非生产事故。
---
## 🛠️ 修复建议

### 立即执行（按优先级排序）
**1. [清理] 如果是测试用例，删除该 Pod**
```bash
kubectl delete pod rc-pending-nodeselector -n aiops-e2e
```
*依据*：该 Pod 标签 `rootcause-e2e=true`，极有可能是测试用例，删除即可消除告警。
**2. [修复] 如果是生产 Pod，修改 nodeSelector**
*步骤*：
  - a. 导出当前 Pod YAML
  ```bash
  kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml > rc-pending.yaml
  ```
  - b. 编辑文件，修正或删除 `nodeSelector` 字段。
  - c. 删除旧 Pod 并重新创建
  ```bash
  kubectl delete pod rc-pending-nodeselector -n aiops-e2e
  kubectl apply -f rc-pending.yaml
  ```
*依据*：如果该 Pod 是生产应用，需修正其节点选择策略，例如使用正确的标签或删除 `nodeSelector` 使用默认调度。
**3. [替代方案] 如果 nodeSelector 必须保留，给节点打标签**
```bash
# 选择一个目标节点，例如 node1
kubectl label node node1 aiops.e2e/nonexistent-node-label=true
```
*目的*：如果 `nodeSelector` 是强制要求，则必须为至少一个节点打上此标签。

### 后续优化
1. **CI/CD 流水线检查**：在部署流水线中加入对 `nodeSelector` 和 `affinity` 的校验，确保目标标签存在于集群中，避免非预期的调度失败。
2. **监控告警**：对 `Pending` 状态的 Pod 设置告警，以便及时发现类似调度问题。虽然本案例为测试，但在生产中该告警至关重要。

---

## 📊 性能统计

├─ 总耗时: 1.6m
├─ 问题定位: 24.2s (26%) ✅
├─ 证据链采集: 26.9s (28%) ✅
├─ 根因分析: 23.2s (24%) ✅
├─ 汇总总结: 20.5s (22%) ✅
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
