======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: d3855093519b4fc3]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我先扫描全局 Pod 状态，看看当前集群中有什么异常。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 发现了一个异常 Pod，我来进一步查看它的详情。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE     IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          8m47s   <none>   <none
   💭 [问题定位] Pod 处于 Pending 状态且没有绑定到 Node，标签有 `pod_abnormal_type=PendingUnschedulable`，很可能是调度问题。让我进一步 describe 确认调度事件。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  8m49s  default-scheduler  0/3 nodes are available: 3 node(s) di
   💭 [问题定位] 非常清晰，让我获取对应的 runbook 辅助定位。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 我已经拿到了所有必要信息，现在来做完整的分析定位。

---

## 集群异常诊断报告

### 全局扫描结果

| 状态 | 数量 |
|------|------|
| Running (正常) | 59 |
| **Pending (异常)** | **1** |
| 总计 | 65 |

### 当前异常 Pod

| 命名空间 | Pod 名称 | 状态 | 异常时长 |
|----------|---------|------|---------|
| `aiops-e2e` | `rc-pending-nodeselector` | Pending | 约 9 分钟 |

### 异常详情

**Pod:** `rc-pending-nodeselector`  
**状态:** Pending，未绑定到任何 Node  
**调度事件 (FailedScheduling):**
```
0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.
preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.
```

**根因:** Pod 设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，但集群中 **3 个节点均没有该标签**，导致调度器无法找到匹配的节点。

### 分类定层

| 字段 | 值 |
|------|-----|
| **异常类型** | `PendingUnschedulable` |
| **状态关键字** | `Pending` |
| **兼容层级** | `L1` |
| **层名称** | `调度约束不匹配` |
| **置信度** | `高` |

### 异常组

| 异常组 | 包含 Pod |
|--------|---------|
| PendingUnschedulable | `rc-pending-nodeselector` |

### 可能场景

1. **nodeSelector 标签不存在** — Pod 要求 `aiops.e2e/nonexistent-node-label=true`，但集群中没有节点拥有此标签，导致调度器完全无法放置。
2. **E2E 测试场景** — 从 Pod 标签 `rootcause-e2e=true` 可看出，这是一个端到端测试用例，目的就是验证 nodeSelector 不匹配时的异常处理。

### 下一步建议

- 如果这是测试用例，则当前行为符合预期（Pod 正确停留在 Pending 并报告 FailedScheduling）。
- 如果是业务 Pod，需要：
  - 给目标节点打上对应标签：`kubectl label node <node-name> aiops.e2e/nonexistent-node-label=true`
  - 或修改 Pod 的 nodeSelector 匹配现有节点标签。
   ✅ [问题定位] 完成 (24.4s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector 标签不存在导致调度失败', 'probability': '高', 'reason': "Pod 设置了 nodeSelector 'aiops.e2e/nonexistent-node-label=true'，集群 3 个节点均无此标签，FailedScheduling 事件明确提示 'didn't match Pod's node affinity/selector'"}, {'scenario': 'E2E 测试场景', 'probability': '中', 'reason': "Pod 标签包含 'rootcause-e2e=true'，可能是有意构造的测试用例验证 nodeSelector 不匹配场景"}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}]
   reasoning=集群中存在一个当前仍处于 Pending 状态的异常 Pod: aiops-e2e/rc-pending-nodeselector。Pod 状态为 Pending，Events 显示 FailedScheduling，原因明确为 '3 node(s) didn't match Pod's node affinity/selector'，即 nodeSelector 标签不匹配。按照五层模型，调度约束不匹配属于 L1 层级（scheduling / node_kubelet），异常类型归一化为 PendingUnschedulable。节点本身均 Ready（3 nodes available），非节点故障，根因完全在调度约束层面。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "调度约束不匹配", "confidence": 0.95, "reasoning": "集群中存在一个当前仍处于 Pending 状态的异常 Pod: aiops-e2e/rc-pending-nodeselector。Pod 状态为 Pending，Events 显示 FailedScheduling，原因明确为 '3 node(s) didn't match Pod's node affinity/selector'，即 nodeSelector 标签不匹配。按照五层模型，调度约束不匹配属于 L1 层级（scheduling / node_kubelet），异常类型归一化为 PendingUnschedulable。节点本身均 Ready（3 nodes available），非节点故障，根因完全在调度约束层面。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "nodeSelector 标签不存在导致调度失败", "probability": "高", "reason": "Pod 设置了 nodeSelector 'aiops.e2e/nonexistent-node-label=true'，集群 3 个节点均无此标签，FailedScheduling 事件明确提示 'didn't match Pod's node affinity/selector'"}, {"scenario": "E2E 测试场景", "probability": "中", "reason": "Pod 标签包含 'rootcause-e2e=true'，可能是有意构造的测试用例验证 nodeSelector 不匹配场景"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              8m45s   <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/d3855093519b4fc3/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/d3855093519b4fc3/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/d3855093519b4fc3/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我直接执行既有 evidence_plan 中的工具。先执行 critical 级别的工具。
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  9m15s  default-scheduler  0/3 nodes are available: 3 node(s) di
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE     IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          9m16s   <none>   <none
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-nodeselector
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:18:44Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers: <
   💭 [证据链采集] 现在执行 important 级别的工具：查看节点标签。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAME     STATUS   ROLES           AGE    VERSION   LABELS\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpg
   💭 [证据链采集] 所有工具调用完成。以下是证据采集结论：

---

## 证据采集结论

### ✅ 已采集证据

| 证据维度 | 工具 | 结果 |
|---------|------|------|
| **Pod 当前状态** | `kubectl_get_by_name` | Pod `rc-pending-nodeselector` 在 `aiops-e2e` 命名空间，STATUS=Pending，已持续 9m16s，未绑定节点 |
| **FailedScheduling 事件** | `kubectl_describe` | 2 条 FailedScheduling 事件：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` |
| **Pod 配置 - nodeSelector** | `kubectl_get_yaml` | `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}` — 要求标签 `aiops.e2e/nonexistent-node-label=true` |
| **Pod 配置 - 容器** | `kubectl_get_yaml` | 镜像 `busybox:1.36`，`imagePullPolicy: Never`，命令 `sleep 3600`，QoS BestEffort |
| **Pod 条件** | `kubectl_get_yaml` | `PodScheduled=False`, Reason=`Unschedulable` |
| **集群节点标签** | `run_bash_command` | 3 个节点（master/node1/node2）均 Ready，**没有任何节点的标签包含 `aiops.e2e/nonexistent-node-label`** |

### 🎯 根因结论

Pod `rc-pending-nodeselector` 设置了 nodeSelector `aiops.e2e/nonexistent-node-label=true`，但集群中 3 个节点的标签均不包含该键值对，导致调度器无法放置，属于**调度约束不匹配（nodeSelector 标签不存在）**。该 Pod 标签含 `rootcause-e2e=true`，高度疑似为 E2E 测试场景构造的故障。
   ✅ [证据链采集] 完成 (16.4s)
   📤 → 下游数据: evidence_items=6/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod 当前状态：确认 rc-pending-nodeselector 在 aiops-e2e namespace 中仍处于 Pending 状态","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"验证 FailedScheduling 事件：确认 nodeSelector/affinity 不匹配的具体细节","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3","description":"验证 nodeSelector 配置：查看 Pod YAML spec 中的 nodeSelector 字段","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"","evidence_type":"","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e4","description":"验证集群节点标签：确认节点是否包含 Pod 所需的 nodeSelector 标签","level":"important","tool":"run_bash_command","command":"kubectl get nodes --show-labels","tool_args":{"command":"kubectl get nodes --show-labels"},"purpose":"","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  9m15s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  3m47s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  9m15s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  3m47s  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d3855093519b4fc3/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d3855093519b4fc3/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d3855093519b4fc3/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                      READY   STATUS    RESTARTS   AGE     IP       NODE     NOMINATED NODE   READINESS GATES   LABELS\nrc-pending-nodeselector   0/1     Pending   0          9m16s   <none>   <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d3855093519b4fc3/tools/002-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d3855093519b4fc3/tools/002-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d3855093519b4fc3/tools/002-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d3855093519b4fc3/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d3855093519b4fc3/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d3855093519b4fc3/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAME     STATUS   ROLES           AGE    VERSION   LABELS\\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\\nnode1    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\nnode2    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/d3855093519b4fc3/tools/004-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/d3855093519b4fc3/tools/004-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/d3855093519b4fc3/tools/004-evidence-run_bash_command.summary.txt"}],"llm_analysis":"所有工具调用完成。以下是证据采集结论：\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据\n\n| 证据维度 | 工具 | 结果 |\n|---------|------|------|\n| **Pod 当前状态** | `kubectl_get_by_name` | Pod `rc-pending-nodeselector` 在 `aiops-e2e` 命名空间，STATUS=Pending，已持续 9m16s，未绑定节点 |\n| **FailedScheduling 事件** | `kubectl_describe` | 2 条 FailedScheduling 事件：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` |\n| **Pod 配置 - nodeSelector** | `kubectl_get_yaml` | `nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}` — 要求标签 `aiops.e2e/nonexistent-node-label=true` |\n| **Pod 配置 - 容器** | `kubectl_get_yaml` | 镜像 `busybox:1.36`，`imagePullPolicy: Never`，命令 `sleep 3600`，QoS BestEffort |\n| **Pod 条件** | `kubectl_get_yaml` | `PodScheduled=False`, Reason=`Unschedulable` |\n| **集群节点标签** | `run_bash_command` | 3 个节点（master/node1/node2）均 Ready，**没有任何节点的标签包含 `aiops.e2e/nonexistent-node-label`** |\n\n### 🎯 根因结论\n\nPod `rc-pending-nodeselector` 设置了 nodeSelector `aiops.e2e/nonexistent-node-label=true`，但集群中 3 个节点的标签均不包含该键值对，导致调度器无法放置，属于**调度约束不匹配（nodeSelector 标签不存在）**。该 Pod 标签含 `rootcause-e2e=true`，高度疑似为 E2E 测试场景构造的故障。","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 6/7 项，完整度 86%；实际执行工具 7 个，匹配计划 3 个，未规划证据 4 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":7,"environment_evidence_collected":6,"environment_evidence_completeness":0.8571428571428571,"executed_tool_count":7,"matched_tool_count":3,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证 Pod 当前状态：确认 rc-pending-nodeselector 在 aiops-e2e namespace 中仍处于 Pending 状态","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e","purpose":"","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"验证 FailedScheduling 事件：确认 nodeSelector/affinity 不匹配的具体细节","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"e3","description":"验证 nodeSelector 配置：查看 Pod YAML spec 中的 nodeSelector 字段","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"验证集群节点标签：确认节点是否包含 Pod 所需的 nodeSelector 标签","level":"important","tool":"run_bash_command","command":"kubectl get nodes --show-labels","purpose":"","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["e4(验证集群节点标签：确认节点是否包含 Pod 所需的 nodeSelector 标签): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 86%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_get_by_name | 验证 Pod 当前状态：确认 rc-pending-nodeselector 在 aiop... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_describe | 验证 FailedScheduling 事件：确认 nodeSelector/affini... | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |
   | e3 | critical | ✅ | kubectl_get_yaml | 验证 nodeSelector 配置：查看 Pod YAML spec 中的 nodeSe... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e4 | important | ❌ | run_bash_command | 验证集群节点标签：确认节点是否包含 Pod 所需的 nodeSelector 标签 | `kubectl get nodes --show-labels` |

   ⚠️ 未采集原因:
   - e4(验证集群节点标签：确认节点是否包含 Pod 所需的 nodeSelector 标签): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (18.0s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector（aiops-e2e 命名空间）处于 Pending 状态，根本原因是 Pod 的 nodeSelector 配置为 {"aiops.e2e/nonexistent-node-label": "true"}，而集群 3 个节点（master、node1、node2）均 Ready 但没有任何节点包含此标签。kubectl_describe 显示 2 条 FailedScheduling 事件，明确报告 "3 node(s) didn't match Pod's node affinity/selector"。节点标签检查确认所有节点的标签集合中均不包含 aiops.e2e/nonexistent-node-label。Pod 标签含 rootcause-e2e=true，高度疑似 E2E 测试场景构造的故障。
   confidence=95%
   causal_chain={"root_cause": "Pod 设置了 nodeSelector aiops.e2e/nonexistent-node-label=true，但集群中 3 个节点的标签均不包含该键值对", "propagation": "kube-scheduler 在调度周期中评估节点约束 → 所有 3 个节点均被过滤（filter）掉 → 无可用节点 → Pod 保持 Pending 状态", "direct_cause": "集群节点缺少 Pod 所需的 nodeSelector 标签 aiops.e2e/nonexistent-node-label=true", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e namespace 持续 Pending，Events 显示 FailedScheduling，调度器报告 0/3 nodes available"}
   rca_analysis={"phenomenon": "集群中 Pod aiops-e2e/rc-pending-nodeselector 处于 Pending 状态已持续约 9 分钟，未绑定任何节点，调度器报告 0/3 节点可用。其余 59 个 Pod 均正常运行，集群整体健康。", "evidence_inventory": [{"id": "e1", "source": "kubectl_get_by_name", "content": "Pod rc-pending-nodeselector 在 aiops-e2e namespace，STATUS=Pending，已持续 9m16s，未分配 Node/IP", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe", "content": "2 条 FailedScheduling 事件：0/3 nodes available: 3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_yaml", "content": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}；PodScheduled=False, reason=Unschedulable", "reliability": "高"}, {"id": "e4", "source": "run_bash_command", "content": "3 个节点（master/node1/node2）均 Ready，没有任何节点标签包含 aiops.e2e/nonexistent-node-label", "reliability": "高"}, {"id": "e5", "source": "kubectl_get_by_kind_in_cluster", "content": "集群共 65 个 Pod，59 Running，1 Pending（即此 Pod），无其他异常状态", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "rc-pending-nodeselector 0/1 Pending 0 9m16s <none> <none>", "interpretation": "Pod 当前状态为 Pending，未调度到任何节点，确认异常持续存在"}, {"evidence_id": "e2", "raw_data": "Warning FailedScheduling: 0/3 nodes available: 3 node(s) didn't match Pod's node affinity/selector", "interpretation": "调度器明确拒绝调度，原因是所有 3 个节点都不满足 Pod 的节点亲和性/nodeSelector 约束"}, {"evidence_id": "e3", "raw_data": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}; conditions: PodScheduled=False reason=Unschedulable", "interpretation": "Pod YAML 中指定了 nodeSelector 键值对 aiops.e2e/nonexistent-node-label=true，这是调度约束的直接定义"}, {"evidence_id": "e4", "raw_data": "3 nodes (master, node1, node2) all Ready. None have label 'aiops.e2e/nonexistent-node-label' in any value", "interpretation": "集群中 3 个节点均不包含 Pod 所需的 nodeSelector 标签，这是 FailedScheduling 的直接原因"}, {"evidence_id": "e5", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}", "interpretation": "集群无其他异常 Pod，该问题是集群中唯一异常，故障范围明确、无并发问题"}], "causal_chain": {"root_cause": "Pod 设置了 nodeSelector aiops.e2e/nonexistent-node-label=true，但集群中 3 个节点的标签均不包含该键值对", "propagation": "kube-scheduler 在调度周期中评估节点约束 → 所有 3 个节点均被过滤（filter）掉 → 无可用节点 → Pod 保持 Pending 状态", "direct_cause": "集群节点缺少 Pod 所需的 nodeSelector 标签 aiops.e2e/nonexistent-node-label=true", "manifestation": "Pod rc-pending-nodeselector 在 aiops-e2e namespace 持续 Pending，Events 显示 FailedScheduling，调度器报告 0/3 nodes available"}, "root_cause": "Pod rc-pending-nodeselector（aiops-e2e 命名空间）处于 Pending 状态，根本原因是 Pod 的 nodeSelector 配置为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}，而集群 3 个节点（master、node1、node2）均 Ready 但没有任何节点包含此标签。kubectl_describe 显示 2 条 FailedScheduling 事件，明确报告 \"3 node(s) didn't match Pod's node affinity/selector\"。节点标签检查确认所有节点的标签集合中均不包含 aiops.e2e/nonexistent-node-label。Pod 标签含 rootcause-e2e=true，高度疑似 E2E 测试场景构造的故障。", "root_cause_summary": "Pod rc-pending-nodeselector（aiops-e2e 命名空间）处于 Pending 状态，根本原因是 Pod 的 nodeSelector 配置为 {\"aiops.e2e/nonexistent-node-label\": \"true\"}，而集群 3 个节点（master、node1、node2）均 Ready 但没有任何节点包含此标签。kubectl_describe 显示 2 条 FailedScheduling 事件，明确报告 \"3 node(s) didn't match Pod's node affinity/selector\"。节点标签检查确认所有节点的标签集合中均不包含 aiops.e2e/nonexistent-node-label。Pod 标签含 rootcause-e2e=true，高度疑似 E2E 测试场景构造的故障。", "confidence": 0.95, "confidence_reason": "有直接证据链（kubectl_get_yaml 确认 nodeSelector → run_bash_command 确认节点无该标签 → kubectl_describe 确认 FailedScheduling 事件），因果链清晰完整，置信度高", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "资源不足（CPU/内存不足）", "probability": "low", "reason": "FailedScheduling 事件未提及 Insufficient cpu/memory，明确指向 node affinity/selector 不匹配；且 59 个其他 Pod 均运行正常"}, {"cause": "节点 NotReady/Unschedulable", "probability": "low", "reason": "节点标签检查确认 3 个节点均 Ready，无 SchedulingDisabled 或 NotReady 状态"}, {"cause": "PVC 未绑定", "probability": "low", "reason": "Pod 无卷声明，Volumes 仅包含 kube-api-access-w74s5（ServiceAccount token 投影卷），无 PVC 依赖"}], "limitations": "缺失的 e4（节点标签验证）已由 run_bash_command 补充采集并确认。未对 Pod 的 rootcause-e2e=true 标签是否代表自动化测试场景做进一步确认，但不影响技术根因判断。", "llm_raw_analysis": ""}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector（aiops-e2e 命名空间）处于 Pending 状态，根本原因是 Pod 的 nodeSelector 配置为 {"aiops.e2e/nonexistent-node-label": "true"}，而集群 3 个节点（master、no...
   置信度: 95%
   🔗 因果链:
     根本原因: Pod 设置了 nodeSelector aiops.e2e/nonexistent-node-label=true，但集群中 3 个节点的标签均不包含该键值对
     传导机制: kube-scheduler 在调度周期中评估节点约束 → 所有 3 个节点均被过滤（filter）掉 → 无可用节点 → Pod 保持 Pending 状态
     最终表现: Pod rc-pending-nodeselector 在 aiops-e2e namespace 持续 Pending，Events 显示 FailedScheduling，调度器报告 0/3 nodes available


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (24.4s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5530 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 23.2s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将根据您提供的三个阶段分析结果，为您生成一份详尽的诊断报告。

---
## 📊 诊断概览

根据当前集群状态，发现 **1 个明确的异常 Pod**，集群整体健康度为 **59/60 正常**。

| 项目 | 内容 |
|------|------|
| **集群核心状态** | 59 个 Pod 正常运行，1 个 Pod 处于 Pending 状态 |
| **Pod异常状态** | `Pending` |
| **兼容归因层** | L1 - Scheduling / Node Kubelet |
| **问题分类** | `PendingUnschedulable` (调度失败) |
| **置信度** | **高 (95%)** |
| **证据完整度** | 3/4 (75%) |

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-pending-nodeselector` |
| Namespace | `aiops-e2e` |
| Node | `<none>` (未调度到任何节点) |
| 异常状态 | `Pending`，持续约 9 分钟 |
| 核心错误信息 | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` |

**集群整体状态**:
*   `kubectl get pods --all-namespaces` 显示共 65 个 Pod，其中 **59 个 Running**，**1 个 Pending**。
*   3 个节点（master, node1, node2）状态均为 `Ready`，功能正常。

**结论**: 集群整体运行正常，仅有一个 Pod 因调度约束无法被调度到任何节点上。

---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl_get_by_name` | `STATUS: Pending` | Pod 未被调度，未分配到 Node |
| 2 | 调度事件 | `kubectl describe pod rc-pending-nodeselector` | `Warning FailedScheduling 9m15s default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 调度器尝试失败，所有节点均不满足 Pod 的调度约束 |
| 3 | Pod 配置 | `kubectl get pod rc-pending-nodeselector -o yaml` | `Node-Selectors: aiops.e2e/nonexistent-node-label=true` | Pod 明确要求运行在带有 `aiops.e2e/nonexistent-node-label=true` 标签的节点上 |
| 4 | 节点标签状态 | `run_bash_command: kubectl get nodes --show-labels` | `master labels: ...`<br>`node1 labels: ...`<br>`node2 labels: ...` | **集群所有节点 (3个) 的标签中，均不包含 `aiops.e2e/nonexistent-node-label` 这个键** |

### 证据关联分析
-   **证据 #2 + #3 + #4 印证**：Pod 的 `nodeSelector` 强制要求节点带有 `aiops.e2e/nonexistent-node-label=true` 标签，但集群中 3 个节点均无此标签。调度器无法找到符合条件的节点，因此产生 `FailedScheduling` 事件，Pod 卡在 `Pending` 状态。
-   **证据链**：Pod spec 定义 `nodeSelector` → 调度器执行过滤逻辑 (Filter) → 所有节点均被排除 → 无可用节点 → Pod 状态保持 `Pending`。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | - | 所有关键证据均已成功采集，根因明确。 |

---
## 🎯 根因分析

### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                         │
│ Pod 的 spec 中配置了 nodeSelector: `aiops.e2e/nonexistent-node-label: "true"`，  │
│ 要求调度到带有此特定标签的节点上。                                               │
└──────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                         │
│ kube-scheduler 尝试将此 Pod 调度到集群所有 3 个节点 (master, node1, node2)       │
│ 调度器进行 Node Filtering (节点过滤)，检查每个节点的标签是否匹配 nodeSelector。   │
└──────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                         │
│ 集群中 3 个节点均不包含 Pod 所要求的 key-value 标签 `aiops.e2e/nonexistent-node-label: true`。 │
│ 调度器判定没有任何节点满足调度条件。                                             │
└──────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                     │
│ Pod `rc-pending-nodeselector` 处于 `Pending` 状态，无法正常运行。               │
│ `kubectl describe` 中反复出现 `FailedScheduling` 告警事件。                       │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (`FailedScheduling` 事件)、证据 #3 (`nodeSelector` 配置) 和证据 #4 (节点标签真实情况)，问题的根本原因是 **Pod 的 `nodeSelector` 指定的标签 (`aiops.e2e/nonexistent-node-label=true`) 在集群任何节点上都不存在**，导致调度器无法为其分配节点。

**置信度**：高 (95%)
- ✅ 调度事件明确报告节点与 Pod 的 `affinity/selector` 不匹配。
- ✅ Pod YAML 的 `nodeSelector` 字段与事件描述完全吻合。
- ✅ 节点标签的原始输出直接证明了标签确实不存在。
- ⚠️ 该 Pod 包含 `rootcause-e2e=true` 标签，高度怀疑是 E2E 测试场景有意构造的故障，但此猜测不影响技术根因的确定性。

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）
**1. [必须] 删除 Pod 或修正 Pod 的 nodeSelector**
此 Pod 似乎为测试用例，最直接的修复方式是将其删除。如果是对外服务的业务 Pod，则需要修改其 `nodeSelector`。

```bash
# 方案 A：直接删除这个测试 Pod
kubectl delete pod rc-pending-nodeselector -n aiops-e2e

# 方案 B：如果 Pod 是由 Deployment/StatefulSet 管理，修正其 spec
# 假设它由 Deployment 管理
# kubectl edit deployment <deployment-name> -n aiops-e2e
# 然后在 spec.template.spec 中删除或修改 nodeSelector 字段
```
*依据*：证据 #3 明确了 Pod 定义的 `nodeSelector` 导致调度失败。

### 后续优化
1.  **忽略此 Pod**：如果该 Pod 确实是用于 E2E 测试的故障注入用例，其处于 Pending 状态是预期行为，无需处理。可以通过 Pod 标签 `rootcause-e2e=true` 进行识别和过滤。
2.  **回顾 nodeSelector 使用规范**：确保业务 Pod 使用的 `nodeSelector` 或 `nodeAffinity` 标签确实存在于集群节点上，避免将 Pod 的强制调度约束指向一个不存在的目标。
3.  **标签管理**：集群管理员应维护一份标准化的节点标签清单，并与应用团队共享。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 已删除 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | `Error from server (NotFound): pods "rc-pending-nodeselector" not found` |
| 2. 重新检查集群异常 Pod | `kubectl get pods --all-namespaces \| grep -v Running` | 输出为空，或没有 `Pending` 状态的 Pod |

---
## ⚠️ 注意事项
- 本报告中提到的所有诊断结论**仅适用于 `aiops-e2e` 命名空间下的 `rc-pending-nodeselector` Pod**。集群中其余 59 个 Running Pod 和 3 个 Ready 节点均处于正常工作状态。
- 考虑到 Pod 的 `rootcause-e2e=true` 标签，**强烈建议先与相关团队确认此 Pod 是否为测试用例**，再进行删除或修改操作，以免影响自动化测试流程。

---

## 📊 性能统计

├─ 总耗时: 1.4m
├─ 问题定位: 24.4s (29%) ✅
├─ 证据链采集: 16.4s (20%) ✅
├─ 根因分析: 18.0s (22%) ✅
├─ 汇总总结: 24.4s (29%) ✅
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
