======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 006c41e1b5734684]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先对整个集群进行全局 Pod 状态扫描，看看当前有哪些异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 很好，全局扫描完成。当前集群有 65 个 Pod，其中 59 个 Running，1 个 Pending 异常 Pod。

让我进一步查看这个异常 Pod 的详细信息。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          12m   <none>   <none>   
   💭 [问题定位] Pod 处于 Pending 状态，且标签标注了 `pod_abnormal_type=PendingUnschedulable`，我来进一步确认调度原因。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  12m                    default-scheduler  0/3 nodes are availab
   💭 [问题定位] 现在让我获取对应异常类型的 runbook 作为参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在我已经掌握了所有必要信息。让我做一个全面的诊断分析。

---

## 诊断分析结果

### 集群整体健康概览

| 指标 | 数值 |
|------|------|
| 总 Pod 数 | 65 |
| 正常运行 Pod（Running） | 59 |
| **异常 Pod** | **1** |
| 正常 Completed Pod | 0 |
| 节点数（隐含） | 3 个 |

### 异常 Pod 详情

| 字段 | 值 |
|------|-----|
| **Pod 名称** | `rc-pending-nodeselector` |
| **命名空间** | `aiops-e2e` |
| **状态** | **Pending** |
| **异常类型** | **PendingUnschedulable** |
| **兼容层级** | **L1** |
| **状态关键字** | Pending |
| **已运行时间** | 12 分钟 |

### 根因分析

**核心原因：nodeSelector 不匹配 → 调度约束失败**

从 `kubectl describe` 获取的关键证据：

- **调度事件**：`FailedScheduling` — `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`
- **nodeSelector 设置**：`aiops.e2e/nonexistent-node-label=true`
- **QoS 等级**：BestEffort（无资源 request 限制）
- **3 个节点均不匹配**该 nodeSelector 标签

Pod 设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，但集群中没有任何节点拥有此标签，导致调度器无法将 Pod 放置到任何节点上。

### 结构化输出

| 维度 | 值 |
|------|-----|
| **layer** | L1 |
| **derived_layer** | L1 |
| **layer_name** | PendingUnschedulable |
| **confidence** | 高 |
| **pod_status_keyword** | Pending |
| **pod_abnormal_type** | PendingUnschedulable |
| **status_category** | scheduling |
| **异常 Pod 列表** | `aiops-e2e/rc-pending-nodeselector` |
| **异常分组** | `{Pending: [rc-pending-nodeselector]}` |

### 后续建议方向

1. **检查节点标签**：确认是否需要在目标节点上添加 `aiops.e2e/nonexistent-node-label=true` 标签
2. **修正 nodeSelector**：如果标签不存在，移除或替换为正确的节点标签
3. **或者直接删除该 Pod**（如果这是测试用例创建的，从标签 `rootcause-e2e=true` 来看有可能是 E2E 测试 Pod）
   ✅ [问题定位] 完成 (24.1s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector/affinity不匹配', 'probability': 'high', 'reason': "FailedScheduling事件明确提示0/3 nodes didn't match Pod's node affinity/selector，nodeSelector设置为aiops.e2e/nonexistent-node-label=true，集群中无节点拥有此标签"}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}]
   reasoning=集群中存在1个异常Pod rc-pending-nodeselector (namespace: aiops-e2e)，状态为Pending，异常类型为PendingUnschedulable。Events显示FailedScheduling: 0/3 nodes are available - 3 node(s) didn't match Pod's node affinity/selector。nodeSelector设置为aiops.e2e/nonexistent-node-label=true，集群中没有任何节点拥有此标签，导致调度约束不匹配。属于调度失败类问题，归为L1层。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "集群中存在1个异常Pod rc-pending-nodeselector (namespace: aiops-e2e)，状态为Pending，异常类型为PendingUnschedulable。Events显示FailedScheduling: 0/3 nodes are available - 3 node(s) didn't match Pod's node affinity/selector。nodeSelector设置为aiops.e2e/nonexistent-node-label=true，集群中没有任何节点拥有此标签，导致调度约束不匹配。属于调度失败类问题，归为L1层。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "nodeSelector/affinity不匹配", "probability": "high", "reason": "FailedScheduling事件明确提示0/3 nodes didn't match Pod's node affinity/selector，nodeSelector设置为aiops.e2e/nonexistent-node-label=true，集群中无节点拥有此标签"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              12m     <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/006c41e1b5734684/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/006c41e1b5734684/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/006c41e1b5734684/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我现在执行既有证据计划中的工具调用。先执行 critical 级别的工具。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_events
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
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
13m                     Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  13m                    default-scheduler  0/3 nodes are availab
   💭 [证据链采集] 接下来执行 ev-003，检查集群各节点的 label，验证 nodeSelector 是否匹配任何节点。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "master\t{\"beta.kubernetes.io/arch\":\"amd64\",\"beta.kubernetes.io/os\":\"linux\",\"fpga-version\":\"\",\"kubernetes.io/arch\":\"amd64\",\"kubernetes.io/hostname\":\"mast
   💭 [证据链采集] 所有关键证据已采集完毕，以下是完整证据结论：

---

## ✅ 证据采集结论

### 已采集证据（Critical × 4）

| 证据项 | 来源 | 关键发现 |
|--------|------|----------|
| **ev-001: Pod YAML 配置** | `kubectl_get_yaml` | `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}`，Pod 的调度约束明确要求节点必须具有 `aiops.e2e/nonexistent-node-label=true` 标签；Pod 处于 `Pending` phase，`PodScheduled=False`，`reason=Unschedulable` |
| **ev-002: Pod Events** | `kubectl_events` | 连续 3 次 `FailedScheduling`：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`，确认无节点满足调度约束 |
| **ev-003: 节点 Labels** | `run_bash_command` | 集群 3 个节点（master/node1/node2）的 label 中**均不包含** `aiops.e2e/nonexistent-node-label` 标签，与 nodeSelector 完全无法匹配 |
| **ev-004: Pod Describe** | `kubectl_describe` | 确认 Pod 当前状态为 Pending，未绑定任何节点（`node: <none>`），`Node-Selectors: aiops.e2e/nonexistent-node-label=true`，无 PVC 依赖，镜像策略为 `Never`（不会因镜像拉取失败导致 Pending） |

### 根因定位

**nodeSelector 约束不匹配** — Pod `rc-pending-nodeselector` 设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，但集群中 3 个节点的 label 均不包含此键值对，导致调度器无法将 Pod 放置到任何节点上。

### 异常覆盖检查
- **当前异常组（PendingUnschedulable）**：✅ 完整验证 — Pod 状态、调度事件、节点 label 均已采集
- 集群中无其他并发异常组需覆盖

### 未采集 / 冲突证据
- 无冲突证据；所有工具均正常返回，Pod 与 namespace 均真实存在
   ✅ [证据链采集] 完成 (21.9s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"ev-001","description":"获取 Pod rc-pending-nodeselector 的详细 YAML 配置，检查 nodeSelector/affinity/tolerations 等调度约束","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"验证调度约束(nodeSelector/affinity)配置是否导致调度失败","evidence_type":"pod_spec","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"ev-002","description":"查看 Pod 最新的 Events，确认 FailedScheduling 原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-nodeselector --sort-by=.lastTimestamp","tool_args":{"resource_type":"pod","resource_name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"获取 FailedScheduling 事件的详细调度失败原因","evidence_type":"pod_events","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-003","description":"查看集群所有 Node 的 labels，确认是否有节点匹配 nodeSelector","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{\"\\t\"}{.metadata.labels}{\"\\n\"}{end}'","tool_args":{},"purpose":"验证集群各节点的 label 情况，判断 nodeSelector aiops.e2e/nonexistent-node-label=true 是否匹配","evidence_type":"node_labels","target_scope":"cluster_nodes","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-004","description":"检查当前 Pod 的状态和条件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"获取 Pod 当前完整状态信息作为基准","evidence_type":"pod_describe","target_scope":"Pod/aiops-e2e/rc-pending-nodeselector","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/006c41e1b5734684/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/006c41e1b5734684/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/006c41e1b5734684/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n13m                     Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n2m56s (x2 over 7m56s)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/006c41e1b5734684/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/006c41e1b5734684/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/006c41e1b5734684/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  13m                    default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  2m56s (x2 over 7m56s)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  13m                    default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  2m56s (x2 over 7m56s)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/006c41e1b5734684/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/006c41e1b5734684/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/006c41e1b5734684/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"master\\t{\\\"beta.kubernetes.io/arch\\\":\\\"amd64\\\",\\\"beta.kubernetes.io/os\\\":\\\"linux\\\",\\\"fpga-version\\\":\\\"\\\",\\\"kubernetes.io/arch\\\":\\\"amd64\\\",\\\"kubernetes.io/hostname\\\":\\\"master\\\",\\\"kubernetes.io/os\\\":\\\"linux\\\",\\\"metax-tech.com/gpu.installed\\\":\\\"false\\\",\\\"node-role.kubernetes.io/control-plane\\\":\\\"\\\",\\\"node.kubernetes.io/exclude-from-external-load-balancers\\\":\\\"\\\"}\\nnode1\\t{\\\"beta.kubernetes.io/arch\\\":\\\"amd64\\\",\\\"beta.kubernetes.io/os\\\":\\\"linux\\\",\\\"fpga-version\\\":\\\"\\\",\\\"kubernetes.io/arch\\\":\\\"amd64\\\",\\\"kubernetes.io/hostname\\\":\\\"node1\\\",\\\"kubernetes.io/os\\\":\\\"linux\\\",\\\"metax-tech.com/gpu.installed\\\":\\\"false\\\"}\\nnode2\\t{\\\"beta.kubernetes.io/arch\\\":\\\"amd64\\\",\\\"beta.kubernetes.io/os\\\":\\\"linux\\\",\\\"fpga-version\\\":\\\"\\\",\\\"kubernetes.io/arch\\\":\\\"amd64\\\",\\\"kubernetes.io/hostname\\\":\\\"node2\\\",\\\"kubernetes.io/os\\\":\\\"linux\\\",\\\"metax-tech.com/gpu.installed\\\":\\\"false\\\"}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/006c41e1b5734684/tools/004-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/006c41e1b5734684/tools/004-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/006c41e1b5734684/tools/004-evidence-run_bash_command.summary.txt"}],"llm_analysis":"所有关键证据已采集完毕，以下是完整证据结论：\n\n---\n\n## ✅ 证据采集结论\n\n### 已采集证据（Critical × 4）\n\n| 证据项 | 来源 | 关键发现 |\n|--------|------|----------|\n| **ev-001: Pod YAML 配置** | `kubectl_get_yaml` | `nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}`，Pod 的调度约束明确要求节点必须具有 `aiops.e2e/nonexistent-node-label=true` 标签；Pod 处于 `Pending` phase，`PodScheduled=False`，`reason=Unschedulable` |\n| **ev-002: Pod Events** | `kubectl_events` | 连续 3 次 `FailedScheduling`：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`，确认无节点满足调度约束 |\n| **ev-003: 节点 Labels** | `run_bash_command` | 集群 3 个节点（master/node1/node2）的 label 中**均不包含** `aiops.e2e/nonexistent-node-label` 标签，与 nodeSelector 完全无法匹配 |\n| **ev-004: Pod Describe** | `kubectl_describe` | 确认 Pod 当前状态为 Pending，未绑定任何节点（`node: <none>`），`Node-Selectors: aiops.e2e/nonexistent-node-label=true`，无 PVC 依赖，镜像策略为 `Never`（不会因镜像拉取失败导致 Pending） |\n\n### 根因定位\n\n**nodeSelector 约束不匹配** — Pod `rc-pending-nodeselector` 设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，但集群中 3 个节点的 label 均不包含此键值对，导致调度器无法将 Pod 放置到任何节点上。\n\n### 异常覆盖检查\n- **当前异常组（PendingUnschedulable）**：✅ 完整验证 — Pod 状态、调度事件、节点 label 均已采集\n- 集群中无其他并发异常组需覆盖\n\n### 未采集 / 冲突证据\n- 无冲突证据；所有工具均正常返回，Pod 与 namespace 均真实存在","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 7 个，匹配计划 4 个，未规划证据 3 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":7,"matched_tool_count":4,"unplanned_tool_count":3,"evidence_inventory":[{"id":"ev-001","description":"获取 Pod rc-pending-nodeselector 的详细 YAML 配置，检查 nodeSelector/affinity/tolerations 等调度约束","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"验证调度约束(nodeSelector/affinity)配置是否导致调度失败","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-002","description":"查看 Pod 最新的 Events，确认 FailedScheduling 原因","level":"critical","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-nodeselector --sort-by=.lastTimestamp","purpose":"获取 FailedScheduling 事件的详细调度失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-003","description":"查看集群所有 Node 的 labels，确认是否有节点匹配 nodeSelector","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{\"\\t\"}{.metadata.labels}{\"\\n\"}{end}'","purpose":"验证集群各节点的 label 情况，判断 nodeSelector aiops.e2e/nonexistent-node-label=true 是否匹配","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-004","description":"检查当前 Pod 的状态和条件","level":"important","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e","purpose":"获取 Pod 当前完整状态信息作为基准","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | ev-001 | critical | ✅ | kubectl_get_yaml | 获取 Pod rc-pending-nodeselector 的详细 YAML 配置，检查... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | ev-002 | critical | ✅ | kubectl_events | 查看 Pod 最新的 Events，确认 FailedScheduling 原因 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pendi...` |
   | ev-003 | critical | ✅ | run_bash_command | 查看集群所有 Node 的 labels，确认是否有节点匹配 nodeSelector | `kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metad...` |
   | ev-004 | important | ✅ | kubectl_describe | 检查当前 Pod 的状态和条件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (21.6s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector (namespace: aiops-e2e) 当前处于 Pending 状态，异常类型为 PendingUnschedulable。根本原因是 nodeSelector 不匹配：Pod YAML 中设置了 nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}（ev-001），而集群3个节点（master/node1/node2）的所有标签中均不包含 aiops.e2e/nonexistent-node-label 键（ev-003），调度器连续3次 FailedScheduling 事件均报告"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"（ev-002/ev-004）。Pod 无 PVC/PV 依赖，镜像策略为 Never，无其他调度阻塞因素。集群中无其他异常Pod（65个Pod中仅此1个Pending，其余59个Running）。
   confidence=98%
   causal_chain={"root_cause": "Pod rc-pending-nodeselector 的 nodeSelector 指定了 aiops.e2e/nonexistent-node-label=true，但集群中3个节点均无此标签，导致调度约束无法满足", "propagation": "nodeSelector 约束 → 调度器在所有3个节点上检查标签匹配 → 全部失败 → 持续重试均失败（FailedScheduling） → Pod 停留在 Pending 状态", "direct_cause": "所有3个节点均不匹配 Pod 的 nodeSelector/affinity 约束", "manifestation": "Pod rc-pending-nodeselector 处于 Pending 状态，Events 中持续出现 FailedScheduling 警告，提示 0/3 nodes didn't match Pod's node affinity/selector"}
   rca_analysis={"phenomenon": "集群 aiops-e2e 命名空间中 Pod rc-pending-nodeselector 处于 Pending 状态，异常类型为 PendingUnschedulable，调度器报告 0/3 节点可用。", "evidence_inventory": [{"id": "ev-001", "source": "kubectl_get_yaml", "content": "Pod YAML 显示 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}，phase=Pending，PodScheduled=False，reason=Unschedulable", "reliability": "高"}, {"id": "ev-002", "source": "kubectl_events", "content": "连续 FailedScheduling 事件：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "reliability": "高"}, {"id": "ev-003", "source": "run_bash_command（节点标签采集）", "content": "集群3节点(master/node1/node2)标签均不包含 aiops.e2e/nonexistent-node-label 键", "reliability": "高"}, {"id": "ev-004", "source": "kubectl_describe", "content": "Pod 状态 Pending，node=<none>，Node-Selectors: aiops.e2e/nonexistent-node-label=true，无PVC依赖，镜像策略为Never", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "全集群Pod扫描：65行中仅此1个Pending Pod，其余59个Running", "reliability": "高"}, {"id": "layer_2", "source": "kubectl_get_by_name", "content": "确认Pod rc-pending-nodeselector 0/1 Pending，IP/NODE均为none", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "ev-001", "raw_data": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}, phase: Pending, PodScheduled: False, reason: Unschedulable", "interpretation": "Pod明确要求节点具有 aiops.e2e/nonexistent-node-label=true 标签才能被调度，当前没有被调度到任何节点上"}, {"evidence_id": "ev-002", "raw_data": "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector", "interpretation": "调度器确认所有3个节点都不满足Pod的nodeSelector/affinity约束，无法调度"}, {"evidence_id": "ev-003", "raw_data": "master标签列表：无aiops.e2e/nonexistent-node-label；node1标签列表：无；node2标签列表：无", "interpretation": "集群中3个节点的label集合中完全不包含aiops.e2e/nonexistent-node-label这个标签键，nodeSelector无法匹配任何节点"}, {"evidence_id": "ev-004", "raw_data": "Node-Selectors: aiops.e2e/nonexistent-node-label=true, node: <none>, 镜像策略: Never, 无PVC依赖", "interpretation": "Pod无PVC/PV依赖问题，镜像策略Never也不涉及拉取失败；唯一阻塞调度的原因是nodeSelector不匹配"}, {"evidence_id": "layer_1", "raw_data": "rows=65 abnormal=1 status_counts={'Running':59, 'Pending':1}", "interpretation": "集群中仅此1个异常Pod，无其他并发异常组"}, {"evidence_id": "layer_2", "raw_data": "rc-pending-nodeselector 0/1 Pending 0 12m <none> <none>", "interpretation": "确认Pod当前实际状态与异常组描述一致，未绑定节点"}], "causal_chain": {"root_cause": "Pod rc-pending-nodeselector 的 nodeSelector 指定了 aiops.e2e/nonexistent-node-label=true，但集群中3个节点均无此标签，导致调度约束无法满足", "propagation": "nodeSelector 约束 → 调度器在所有3个节点上检查标签匹配 → 全部失败 → 持续重试均失败（FailedScheduling） → Pod 停留在 Pending 状态", "direct_cause": "所有3个节点均不匹配 Pod 的 nodeSelector/affinity 约束", "manifestation": "Pod rc-pending-nodeselector 处于 Pending 状态，Events 中持续出现 FailedScheduling 警告，提示 0/3 nodes didn't match Pod's node affinity/selector"}, "root_cause": "Pod rc-pending-nodeselector (namespace: aiops-e2e) 当前处于 Pending 状态，异常类型为 PendingUnschedulable。根本原因是 nodeSelector 不匹配：Pod YAML 中设置了 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}（ev-001），而集群3个节点（master/node1/node2）的所有标签中均不包含 aiops.e2e/nonexistent-node-label 键（ev-003），调度器连续3次 FailedScheduling 事件均报告\"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"（ev-002/ev-004）。Pod 无 PVC/PV 依赖，镜像策略为 Never，无其他调度阻塞因素。集群中无其他异常Pod（65个Pod中仅此1个Pending，其余59个Running）。", "root_cause_summary": "Pod rc-pending-nodeselector (namespace: aiops-e2e) 当前处于 Pending 状态，异常类型为 PendingUnschedulable。根本原因是 nodeSelector 不匹配：Pod YAML 中设置了 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}（ev-001），而集群3个节点（master/node1/node2）的所有标签中均不包含 aiops.e2e/nonexistent-node-label 键（ev-003），调度器连续3次 FailedScheduling 事件均报告\"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"（ev-002/ev-004）。Pod 无 PVC/PV 依赖，镜像策略为 Never，无其他调度阻塞因素。集群中无其他异常Pod（65个Pod中仅此1个Pending，其余59个Running）。", "confidence": 0.98, "confidence_reason": "有4个直接证据（Pod YAML nodeSelector字段、调度器FailedScheduling事件、节点标签列表、Pod describe）从不同角度交叉验证了同一个根因，因果链完整无矛盾，置信度极高。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "集群资源不足（CPU/内存不足）", "probability": "low", "reason": "已排除 - FailedScheduling 事件明确报告的是 nodeSelector/affinity 不匹配，而非 Insufficient cpu/memory；且集群中59个Pod均正常Running，资源充裕"}, {"cause": "节点 taint 未被 toleration 容忍", "probability": "low", "reason": "已排除 - Pod 有2个toleration（not-ready:NoExecute for 300s），且 FailedScheduling 事件未提及 taint 问题"}, {"cause": "PVC 未绑定导致阻塞", "probability": "low", "reason": "已排除 - Pod describe 显示无PVC依赖，仅有一个kube-api-access投影卷"}], "limitations": "节点标签数据来源于 run_bash_command 采集的3个节点的完整标签列表，证据充分。未采集 Node 的 taints 信息，但 FailedScheduling 事件未提示 taint 相关问题，且 Pod 已有部分 tolerations，taint 非阻塞因素是合理的推断。", "llm_raw_analysis": "集群中存在1个异常Pod rc-pending-nodeselector（namespace: aiops-e2e），状态为Pending，异常类型PendingUnschedulable。通过Pod YAML确认nodeSelector设为{\"aiops.e2e/nonexistent-node-label\": \"true\"}，而集群3个节点的标签中均不包含此键，导致调度器无法调度，持续产生FailedScheduling事件。无其他异常组需要覆盖。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector (namespace: aiops-e2e) 当前处于 Pending 状态，异常类型为 PendingUnschedulable。根本原因是 nodeSelector 不匹配：Pod YAML 中设置了 nodeSelector: {"aio...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod rc-pending-nodeselector 的 nodeSelector 指定了 aiops.e2e/nonexistent-node-label=true，但集群中3个节点均无此标签，导致调度约束无法满足
     传导机制: nodeSelector 约束 → 调度器在所有3个节点上检查标签匹配 → 全部失败 → 持续重试均失败（FailedScheduling） → Pod 停留在 Pending 状态
     最终表现: Pod rc-pending-nodeselector 处于 Pending 状态，Events 中持续出现 FailedScheduling 警告，提示 0/3 nodes didn't match Pod's node affinity/selector


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (23.4s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5591 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 31.0s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将根据您提供的全面信息，为您生成一份详尽、完整的诊断报告。

首先，直接回答您的核心问题：**您的集群当前存在一个问题，一个名为 `rc-pending-nodeselector` 的 Pod 无法被调度到任何节点上，处于 Pending 状态。** 集群中其他 59 个 Pod 均正常运行，整体稳定性良好。

以下是详细的诊断报告：

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | PendingUnschedulable |
| **兼容归因层** | L1 - 调度失败 |
| **问题分类** | nodeSelector 不匹配 |
| **置信度** | 高 (98%) |
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
| Node | 无（未调度成功） |
| 错误信息 | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` |

**集群整体状态**：
当前集群共 `65` 个 Pod，其中 `59` 个处于 `Running` 状态，`1` 个处于异常状态。除本报告分析的问题外，无其他异常。

---

## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 配置 | `kubectl get pod rc-pending-nodeselector -o yaml` | `nodeSelector: {aiops.e2e/nonexistent-node-label: "true"}` | Pod 明确要求调度到包含标签 `aiops.e2e/nonexistent-node-label=true` 的节点上。 |
| 2 | Pod 事件 | `kubectl events --for pod/rc-pending-nodeselector` | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 调度器无法将 Pod 调度到任何节点，因为所有节点都不符合标签匹配条件。 |
| 3 | 节点标签 | `run_bash_command` 获取节点标签 | 集群中 `master`, `node1`, `node2` 的标签列表均**不包含** `aiops.e2e/nonexistent-node-label` 键。 | 集群中没有任何节点拥有 Pod 所要求的标签。 |
| 4 | Pod 详情 | `kubectl describe pod rc-pending-nodeselector` | `Node-Selectors: aiops.e2e/nonexistent-node-label=true` | 确认 Pod 的 `Node-Selectors` 字段为空，确认 Pod 未调度到任何节点。 |

### 证据关联分析
- **证据 #1 + #3 印证**：Pod 的 `nodeSelector` 要求标签 `aiops.e2e/nonexistent-node-label=true`，但集群中 3 个节点均无此标签，导致调度约束无法满足。
- **证据链**：Pod 配置了严格的 `nodeSelector` → 调度器遍历所有节点（3个）进行标签匹配 → 全部失败 → 触发 `FailedScheduling` 事件 → Pod 停留在 `Pending` 状态。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| Node 的 `taints` 信息 | 低 | `FailedScheduling` 事件明确指示为 `node affinity/selector` 问题，未提及 `taint`。Pod 已有部分 `tolerations`，`taint` 非阻塞因素，不影响根因判断。 |

---

## 🎯 根因分析

### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                                  │
│ Pod "rc-pending-nodeselector" 的 spec 中配置了 nodeSelector:                              │
│ {"aiops.e2e/nonexistent-node-label": "true"}，要求调度到带有该特定标签的节点上。            │
│ 但集群中的3个节点（master, node1, node2）均不包含此标签。                                  │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                        ↓
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                                  │
│ nodeSelector 约束 → 调度器在所有3个节点上检查标签匹配 → 全部失败 →                          │
│ 持续重试均失败（FailedScheduling 事件）                                                    │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                        ↓
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                                  │
│ 所有3个节点均不匹配 Pod 的 nodeSelector 约束条件，导致 Pod 无法被调度。                     │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                        ↓
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                              │
│ Pod "rc-pending-nodeselector" 持续处于 Pending 状态，且 Events 中                               │
│ 反复出现 "FailedScheduling" 告警。                                                             │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #1 (Pod YAML 含 `nodeSelector: {aiops.e2e/nonexistent-node-label: "true"}`)、证据 #2 (`FailedScheduling` 事件) 和证据 #3 (集群节点均无该标签)，问题的根本原因是 **Pod 配置的 `nodeSelector` 标签 (`aiops.e2e/nonexistent-node-label=true`) 在集群中不存在**，导致 Pod 无法被调度。

**置信度**：高 (98%)
- ✅ 证据 #1 和 #2 明确指出了调度失败原因。
- ✅ 证据 #3 直接证实了节点上标签缺失。
- ✅ 集群其他 Pod 正常运行，排除了集群整体资源不足或故障的可能性。

---

## 🛠️ 修复建议

根据您的业务需求，选择以下任一方案执行：

### 立即执行（按优先级排序）

**1. [推荐方案] 添加缺失的节点标签到目标节点**
此方案无需修改 Pod 配置，适用于希望 Pod 运行在特定节点（组）的场景。
```bash
# 假设希望 Pod 调度到 node1 节点，执行：
kubectl label node <node1> aiops.e2e/nonexistent-node-label=true
```
*目的*：使节点满足 Pod 的调度约束，Pod 将被自动调度到该节点。

**2. [备选方案] 删除或修改 Pod 的 nodeSelector**
此方案适用于 Pod 不应有特定标签约束的场景。
1.  导出 Pod 的 YAML、修改 `nodeSelector` 配置，然后重新创建：
    ```bash
    # 删除 nodeSelector，让 Pod 可以调度到任何可用节点
    kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml | \
      grep -v 'nodeSelector:' > /tmp/patched-pod.yaml
    # 或者，如果 pod 由 Deployment 等控制器管理，直接修改 Deployment
    # kubectl edit deployment/<deployment-name> -n aiops-e2e
    ```
    *注意*：如果 Pod 由控制器（如 Deployment）管理，直接修改 Pod 将被控制器还原。正确的做法是修改其父控制器。

### 后续优化
1.  **审计 Pod 配置**：检查所有 `Pending` 状态的 Pod，并审计其 `nodeSelector` 或 `affinity` 配置的合理性。
2.  **标签管理规范**：为关键节点定义统一的标签标准，并在部署时严格保证标签的一致性。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS 变为 `Running` |
| 2. 检查 Pod 所在节点 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o wide` | NODE 列显示具体节点名（如 node1） |
| 3. 确认无异常事件 | `kubectl events --for pod/rc-pending-nodeselector -n aiops-e2e` | 不再出现 `FailedScheduling` 事件 |

---

## ⚠️ 注意事项
- 如果选择修改 `nodeSelector`，请确认 Pod 是否需要运行在特定节点上以满足某些前置条件（如特定的 GPU、存储等）。

---

## 📊 性能统计

├─ 总耗时: 1.5m
├─ 问题定位: 24.1s (26%) ✅
├─ 证据链采集: 21.9s (24%) ✅
├─ 根因分析: 21.6s (24%) ✅
├─ 汇总总结: 23.4s (26%) ✅
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
