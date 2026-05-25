======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: e67851313a9d4f84]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我先扫描全局 Pod 状态，看看当前集群中存在哪些异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 全局 Pod 扫描完成，发现以下情况：

- **正常 Pod**：59 个 Running，状态正常
- **异常 Pod**：1 个 Pending

让我进一步查看这个异常 Pod 的详细信息。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  22m                default-scheduler  0/3 nodes are available: 
   💭 [问题定位] 现在情况非常清楚了。我来获取对应的 runbook 作为参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在我已经掌握了所有信息，以下是诊断结果。

---

## 集群异常诊断报告

### 📊 全局概况

| 项目 | 数量 |
|------|------|
| 总 Pod 数 | 65 |
| 正常 Running | 59 |
| 异常 Pod | **1** |

### 🚨 异常 Pod 详情

| Pod | 命名空间 | 状态 | 年龄 |
|-----|---------|------|------|
| **rc-pending-nodeselector** | aiops-e2e | **Pending** | 22m |

### 🔍 根因分析

**Pod: `rc-pending-nodeselector`** (aiops-e2e 命名空间)

- **状态关键字**: Pending
- **异常类型**: **PendingUnschedulable**（调度失败）
- **兼容层级**: **L1**
- **根因**: **nodeSelector 不匹配** — Pod 设置了 `Node-Selectors: aiops.e2e/nonexistent-node-label=true`，但集群中 3 个节点都没有该标签，因此调度器无法找到可用节点。
  ```
  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.
  ```
- **Pod 配置**:
  - 镜像: `busybox:1.36`
  - QoS: BestEffort（无资源限制）
  - 无亲和性/反亲和性约束，仅有 nodeSelector
  - 容忍度: 仅有默认的 `node.kubernetes.io/not-ready:NoExecute` toleration

### 📋 异常分组

| 异常组 | Pod 列表 |
|--------|---------|
| `PendingUnschedulable` | rc-pending-nodeselector |

### 🎯 可能场景

1. **nodeSelector 标签不存在** — Pod 要求节点有 `aiops.e2e/nonexistent-node-label=true` 标签，但集群中没有任何节点打了此标签。
2. **测试/调试 Pod 配置错误** — 从 Pod 名称 `rc-pending-nodeselector` 和标签 `rootcause-e2e=true` 来看，这很可能是一个 E2E 测试用例 Pod，其 nodeSelector 指向了一个不存在的标签，属于预期行为。

### 📈 层次判定

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **layer_name** | PendingUnschedulable - 调度约束不匹配 |
| **derived_layer** | L1 |
| **layers** | L1 |
| **confidence** | 高 |
| **status_category** | scheduling |

### 💡 建议方向

- 如果这是**测试场景**：无需处理，属于预期行为。
- 如果是**生产环境误配置**：需要给目标节点打上 `aiops.e2e/nonexistent-node-label=true` 标签，或修改 Pod 的 nodeSelector 为集群中实际存在的标签。
   ✅ [问题定位] 完成 (20.1s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector标签不存在', 'probability': '高', 'reason': 'Pod要求节点有aiops.e2e/nonexistent-node-label=true标签，但集群中没有任何节点打了此标签'}, {'scenario': '测试/调试Pod配置错误', 'probability': '中', 'reason': '从Pod名称rc-pending-nodeselector和标签rootcause-e2e=true来看，可能是E2E测试用例Pod'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Node", "name": "所有3个节点", "namespace": ""}]
   reasoning=集群中存在1个异常Pod rc-pending-nodeselector（aiops-e2e命名空间），状态为Pending，异常类型为PendingUnschedulable。根因为nodeSelector标签不匹配：Pod设置了Node-Selectors: aiops.e2e/nonexistent-node-label=true，但集群中3个节点均无此标签，调度器无法找到可用节点，Events中明确显示"3 node(s) didn't match Pod's node affinity/selector"。根据五层模型，调度约束不匹配属于L1（scheduling）层级。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable - 调度约束不匹配", "confidence": 0.95, "reasoning": "集群中存在1个异常Pod rc-pending-nodeselector（aiops-e2e命名空间），状态为Pending，异常类型为PendingUnschedulable。根因为nodeSelector标签不匹配：Pod设置了Node-Selectors: aiops.e2e/nonexistent-node-label=true，但集群中3个节点均无此标签，调度器无法找到可用节点，Events中明确显示\"3 node(s) didn't match Pod's node affinity/selector\"。根据五层模型，调度约束不匹配属于L1（scheduling）层级。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Node", "name": "所有3个节点", "namespace": ""}], "possible_scenarios": [{"scenario": "nodeSelector标签不存在", "probability": "高", "reason": "Pod要求节点有aiops.e2e/nonexistent-node-label=true标签，但集群中没有任何节点打了此标签"}, {"scenario": "测试/调试Pod配置错误", "probability": "中", "reason": "从Pod名称rc-pending-nodeselector和标签rootcause-e2e=true来看，可能是E2E测试用例Pod"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              22m     <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/e67851313a9d4f84/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/e67851313a9d4f84/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/e67851313a9d4f84/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来执行既有 evidence_plan 中的真实工具调用，采集关键证据。

先从最关键的 3 个 critical/important 工具开始：
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAME     STATUS   ROLES           AGE    VERSION   LABELS\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpg
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-nodeselector   0/1     Pending   0          22m   <none>   <none>   
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
  Warning  FailedScheduling  22m                default-scheduler  0/3 nodes are available: 
   💭 [证据链采集] 所有核心工具已成功执行，现在再获取 Pod 事件完整信息作为补充证据：
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
22m                 Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 n
   💭 [证据链采集] 所有 evidence_plan 工具执行完毕，以下是证据采集结论：

---

## 证据采集结论

### 已采集证据（4项）

| 计划项 | 工具 | 关键发现 |
|--------|------|---------|
| **e1-g1-verify-pod-exists** ✅ | `kubectl_get_by_name` | Pod `rc-pending-nodeselector` 在 `aiops-e2e` 命名空间中**确认存在**，状态为 **Pending**（0/1），已持续 22m，未绑定节点 |
| **e2-g1-events** ✅ | `kubectl_describe` | **FailedScheduling** 事件：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`，3个节点均不符合调度约束 |
| **e3-g1-pod-yaml** ✅ | `kubectl_get_yaml` | Pod spec 中 **nodeSelector** 定义为：`{"aiops.e2e/nonexistent-node-label": "true"}`，要求节点包含该标签 |
| **e4-g1-node-labels** ✅ | `run_bash_command` | 3个节点（master/node1/node2）的标签中**均不包含** `aiops.e2e/nonexistent-node-label` 标签，没有任何节点能匹配 Pod 的 nodeSelector |

### 未采集 / 冲突证据
无。所有调用均成功返回，未发现 NotFound 或空事件。

### 根因判定
**Pod `rc-pending-nodeselector` 处于 Pending 状态的根因：nodeSelector 标签不匹配。** Pod 配置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，但集群 3 个节点的标签中均不存在该标签，导致调度器无法找到任何可调度的节点。调度器 Events 明确报告 `3 node(s) didn't match Pod's node affinity/selector`，且声明抢占无法帮助（`Preemption is not helpful for scheduling`）。从 Pod 名称和标签 `rootcause-e2e=true` 来看，此 Pod 很可能是为测试/演示 nodeSelector 不匹配场景而创建的 E2E 测试用例。
   ✅ [证据链采集] 完成 (21.3s)
   📤 → 下游数据: evidence_items=6/7
   evidence_analysis={"evidence_plan":[{"id":"e1-g1-verify-pod-exists","description":"验证异常Pod rc-pending-nodeselector是否仍存在于aiops-e2e命名空间，确认当前状态","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o wide","tool_args":{"kind":"Pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"确认Pod存在且仍为Pending状态，作为后续所有证据的基础","evidence_type":"current_state","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2-g1-events","description":"采集Pod当前Events，验证FailedScheduling事件中的调度失败原因原文","level":"critical","tool":"kubectl_events","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e | grep -A10 Events","tool_args":{"namespace":"aiops-e2e","pod_name":"rc-pending-nodeselector"},"purpose":"获取FailedScheduling事件原文，确认调度约束不匹配的具体原因","evidence_type":"events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e3-g1-pod-yaml","description":"获取Pod完整YAML，验证nodeSelector/nodeAffinity配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"验证Pod spec中nodeSelector配置是否包含不存在的标签aiops.e2e/nonexistent-node-label=true","evidence_type":"configuration","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e4-g1-node-labels","description":"获取集群所有节点的标签，验证是否存在Pod要求的nodeSelector标签","level":"important","tool":"run_bash_command","command":"kubectl get nodes --show-labels | head -50","tool_args":{"command":"kubectl get nodes --show-labels | head -50"},"purpose":"检查所有节点的标签，确认是否有节点包含Pod所需的标签aiops.e2e/nonexistent-node-label=true","evidence_type":"configuration","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5-reference-runbook","description":"获取已确认的Pod PendingUnschedulable runbook作为参考","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","tool_args":{"runbook_name":"pod-pending-unschedulable.md"},"purpose":"参考runbook中调度约束不匹配分支的验证要点","evidence_type":"reference","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAME     STATUS   ROLES           AGE    VERSION   LABELS\\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\\nnode1    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\nnode2    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e67851313a9d4f84/tools/001-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e67851313a9d4f84/tools/001-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e67851313a9d4f84/tools/001-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                      READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS\nrc-pending-nodeselector   0/1     Pending   0          22m   <none>   <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e67851313a9d4f84/tools/002-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e67851313a9d4f84/tools/002-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e67851313a9d4f84/tools/002-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e67851313a9d4f84/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e67851313a9d4f84/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e67851313a9d4f84/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  22m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  12m (x2 over 17m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  22m                default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  12m (x2 over 17m)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e67851313a9d4f84/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e67851313a9d4f84/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e67851313a9d4f84/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n22m                 Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n12m (x2 over 17m)   Warning   FailedScheduling   Pod/rc-pending-nodeselector   0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/e67851313a9d4f84/tools/005-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/e67851313a9d4f84/tools/005-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/e67851313a9d4f84/tools/005-evidence-kubectl_events.summary.txt"}],"llm_analysis":"所有 evidence_plan 工具执行完毕，以下是证据采集结论：\n\n---\n\n## 证据采集结论\n\n### 已采集证据（4项）\n\n| 计划项 | 工具 | 关键发现 |\n|--------|------|---------|\n| **e1-g1-verify-pod-exists** ✅ | `kubectl_get_by_name` | Pod `rc-pending-nodeselector` 在 `aiops-e2e` 命名空间中**确认存在**，状态为 **Pending**（0/1），已持续 22m，未绑定节点 |\n| **e2-g1-events** ✅ | `kubectl_describe` | **FailedScheduling** 事件：`0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector`，3个节点均不符合调度约束 |\n| **e3-g1-pod-yaml** ✅ | `kubectl_get_yaml` | Pod spec 中 **nodeSelector** 定义为：`{\"aiops.e2e/nonexistent-node-label\": \"true\"}`，要求节点包含该标签 |\n| **e4-g1-node-labels** ✅ | `run_bash_command` | 3个节点（master/node1/node2）的标签中**均不包含** `aiops.e2e/nonexistent-node-label` 标签，没有任何节点能匹配 Pod 的 nodeSelector |\n\n### 未采集 / 冲突证据\n无。所有调用均成功返回，未发现 NotFound 或空事件。\n\n### 根因判定\n**Pod `rc-pending-nodeselector` 处于 Pending 状态的根因：nodeSelector 标签不匹配。** Pod 配置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`，但集群 3 个节点的标签中均不存在该标签，导致调度器无法找到任何可调度的节点。调度器 Events 明确报告 `3 node(s) didn't match Pod's node affinity/selector`，且声明抢占无法帮助（`Preemption is not helpful for scheduling`）。从 Pod 名称和标签 `rootcause-e2e=true` 来看，此 Pod 很可能是为测试/演示 nodeSelector 不匹配场景而创建的 E2E 测试用例。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 7 个，匹配计划 4 个，未规划证据 3 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":7,"matched_tool_count":4,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1-g1-verify-pod-exists","description":"验证异常Pod rc-pending-nodeselector是否仍存在于aiops-e2e命名空间，确认当前状态","level":"critical","tool":"kubectl_get_by_name","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o wide","purpose":"确认Pod存在且仍为Pending状态，作为后续所有证据的基础","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-g1-events","description":"采集Pod当前Events，验证FailedScheduling事件中的调度失败原因原文","level":"critical","tool":"kubectl_events","command":"kubectl describe pod rc-pending-nodeselector -n aiops-e2e | grep -A10 Events","purpose":"获取FailedScheduling事件原文，确认调度约束不匹配的具体原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3-g1-pod-yaml","description":"获取Pod完整YAML，验证nodeSelector/nodeAffinity配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml","purpose":"验证Pod spec中nodeSelector配置是否包含不存在的标签aiops.e2e/nonexistent-node-label=true","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4-g1-node-labels","description":"获取集群所有节点的标签，验证是否存在Pod要求的nodeSelector标签","level":"important","tool":"run_bash_command","command":"kubectl get nodes --show-labels | head -50","purpose":"检查所有节点的标签，确认是否有节点包含Pod所需的标签aiops.e2e/nonexistent-node-label=true","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5-reference-runbook","description":"获取已确认的Pod PendingUnschedulable runbook作为参考","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","purpose":"参考runbook中调度约束不匹配分支的验证要点","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1-g1-verify-... | critical | ✅ | kubectl_get_by_name | 验证异常Pod rc-pending-nodeselector是否仍存在于aiops-e2... | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o wide` |
   | e2-g1-events | critical | ✅ | kubectl_events | 采集Pod当前Events，验证FailedScheduling事件中的调度失败原因原文 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e | grep -A10 Events` |
   | e3-g1-pod-yaml | important | ✅ | kubectl_get_yaml | 获取Pod完整YAML，验证nodeSelector/nodeAffinity配置 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` |
   | e4-g1-node-la... | important | ✅ | run_bash_command | 获取集群所有节点的标签，验证是否存在Pod要求的nodeSelector标签 | `kubectl get nodes --show-labels | head -50` |
   | e5-reference-... | reference | ❌ | fetch_runbook | 获取已确认的Pod PendingUnschedulable runbook作为参考 | `fetch_runbook pod-pending-unschedulable.md` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (24.5s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector（aiops-e2e）处于 PendingUnschedulable 状态，根因为 nodeSelector 标签不匹配：Pod 配置了 nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}（证据 e3），而集群 3 个节点（master/node1/node2）的标签中均无该标签（证据 e4）。调度器 Events 明确报告 "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"（证据 e2/e5），且抢占无法解决。Pod 已持续 Pending 22 分钟（证据 e1）。从 Pod 名称 rc-pending-nodeselector 和标签 rootcause-e2e=true 来看，这很可能是 E2E 测试用例，非生产业务 Pod。
   confidence=100%
   causal_chain={"root_cause": "Pod rc-pending-nodeselector 配置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，但集群 3 个节点均未打该标签，导致调度器无法找到任何可用节点", "propagation": "Pod YAML 中 nodeSelector 定义 → kube-scheduler 检查所有 3 个节点的标签 → 无节点匹配 → 调度器标记 PodScheduled=False，reason=Unschedulable → 产生 FailedScheduling 事件 → Pod 持续处于 Pending 状态", "direct_cause": "节点标签与 Pod nodeSelector 不匹配：Pod 要求标签 aiops.e2e/nonexistent-node-label=true，但集群 3 个节点（master/node1/node2）的标签中均无此标签", "manifestation": "Pod rc-pending-nodeselector（aiops-e2e）状态 Pending，0/1 容器就绪，未绑定节点（NODE=<none>），Events 显示 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\""}
   rca_analysis={"phenomenon": "集群中 Pod rc-pending-nodeselector（命名空间 aiops-e2e）处于 Pending 状态，异常类型 PendingUnschedulable，0/1 容器就绪，未绑定节点，已持续 22 分钟。", "evidence_inventory": [{"id": "e1", "source": "kubectl_get_by_name", "content": "Pod rc-pending-nodeselector 确认存在，状态 Pending，0/1，AGE 22m，未分配节点（NODE=<none>）", "reliability": "高"}, {"id": "e2", "source": "kubectl_describe", "content": "Events 显示 2 次 FailedScheduling：0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector。Pod 配置 Node-Selectors: aiops.e2e/nonexistent-node-label=true", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_yaml", "content": "Pod YAML 确认 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}，PodScheduled condition 状态=False，reason=Unschedulable", "reliability": "高"}, {"id": "e4", "source": "run_bash_command（节点标签列表）", "content": "3 个节点（master/node1/node2）的标签中均不包含 aiops.e2e/nonexistent-node-label 标签", "reliability": "高"}, {"id": "e5", "source": "kubectl_events", "content": "与 kubectl_describe 一致的 FailedScheduling 事件，确认 3 个节点均不匹配 nodeSelector", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "rc-pending-nodeselector   0/1     Pending   0          22m   <none>   <none>", "interpretation": "Pod 当前存在且处于 Pending 状态，未分配到任何节点，验证了异常现象持续存在"}, {"evidence_id": "e2", "raw_data": "Warning FailedScheduling 22m default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.", "interpretation": "调度器明确报告所有 3 个节点都不匹配 Pod 的 node affinity/selector，且抢占无法帮助——说明问题不是资源不足，而是调度约束无法满足"}, {"evidence_id": "e3", "raw_data": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\nconditions: PodScheduled status=False reason=Unschedulable", "interpretation": "Pod 明确要求节点具有 aiops.e2e/nonexistent-node-label=true 标签；PodScheduled 条件为 False 且 reason=Unschedulable，与调度器事件一致"}, {"evidence_id": "e4", "raw_data": "master: labels=...（不包含 aiops.e2e/nonexistent-node-label）\nnode1: labels=...（不包含）\nnode2: labels=...（不包含）", "interpretation": "集群中 3 个节点的标签列表中均不存在 aiops.e2e/nonexistent-node-label 标签，没有任何节点能匹配 Pod 的 nodeSelector 约束"}, {"evidence_id": "e5", "raw_data": "22m Warning FailedScheduling Pod/rc-pending-nodeselector 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.", "interpretation": "独立的事件采集与 describe 结果完全一致，交叉验证了调度失败原因"}], "causal_chain": {"root_cause": "Pod rc-pending-nodeselector 配置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，但集群 3 个节点均未打该标签，导致调度器无法找到任何可用节点", "propagation": "Pod YAML 中 nodeSelector 定义 → kube-scheduler 检查所有 3 个节点的标签 → 无节点匹配 → 调度器标记 PodScheduled=False，reason=Unschedulable → 产生 FailedScheduling 事件 → Pod 持续处于 Pending 状态", "direct_cause": "节点标签与 Pod nodeSelector 不匹配：Pod 要求标签 aiops.e2e/nonexistent-node-label=true，但集群 3 个节点（master/node1/node2）的标签中均无此标签", "manifestation": "Pod rc-pending-nodeselector（aiops-e2e）状态 Pending，0/1 容器就绪，未绑定节点（NODE=<none>），Events 显示 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\""}, "root_cause": "Pod rc-pending-nodeselector（aiops-e2e）处于 PendingUnschedulable 状态，根因为 nodeSelector 标签不匹配：Pod 配置了 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}（证据 e3），而集群 3 个节点（master/node1/node2）的标签中均无该标签（证据 e4）。调度器 Events 明确报告 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"（证据 e2/e5），且抢占无法解决。Pod 已持续 Pending 22 分钟（证据 e1）。从 Pod 名称 rc-pending-nodeselector 和标签 rootcause-e2e=true 来看，这很可能是 E2E 测试用例，非生产业务 Pod。", "root_cause_summary": "Pod rc-pending-nodeselector（aiops-e2e）处于 PendingUnschedulable 状态，根因为 nodeSelector 标签不匹配：Pod 配置了 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}（证据 e3），而集群 3 个节点（master/node1/node2）的标签中均无该标签（证据 e4）。调度器 Events 明确报告 \"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"（证据 e2/e5），且抢占无法解决。Pod 已持续 Pending 22 分钟（证据 e1）。从 Pod 名称 rc-pending-nodeselector 和标签 rootcause-e2e=true 来看，这很可能是 E2E 测试用例，非生产业务 Pod。", "confidence": 1.0, "confidence_reason": "直接证据链完整：Pod YAML 确认 nodeSelector 配置（e3）→ 节点标签列表确认无匹配标签（e4）→ 调度器 Events 确认失败原因（e2/e5）→ Pod 状态确认 Pending（e1）。因果链完全闭合，无矛盾或模糊点，置信度 1.0。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "资源不足（CPU/内存不足）", "probability": "low", "reason": "调度器 Events 明确说 \"3 node(s) didn't match Pod's node affinity/selector\"，而非资源不足类错误（如 Insufficient cpu/memory）；且提到 Preemption is not helpful，进一步排除资源不足场景"}, {"cause": "节点 taint 未容忍", "probability": "low", "reason": "Pod 已配置 Tolerations 容忍 not-ready/not-ready 的 NoExecute 300s，且调度器未提及 taint 相关拒绝信息"}, {"cause": "PVC 未绑定", "probability": "low", "reason": "Pod 仅使用 kube-api-access-w74s5（Projected 类型卷），无 PVC 依赖，Events 中未出现 PersistentVolumeClaims 相关错误"}], "limitations": "无。证据完整覆盖了调度约束不匹配场景所需的所有维度（Pod spec、节点标签、调度器 Events），分析结论明确。", "llm_raw_analysis": "## 证据清点\n共采集 5 项证据，全部成功返回，无冲突或 NotFound。\n\n## 逐条分析\n- e1（kubectl_get_by_name）：Pod 存在且 Pending，未分配节点，持续 22m — 确认异常现象当前仍存在\n- e2（kubectl_describe）：FailedScheduling 事件原文显示 3 个节点均不匹配 node affinity/selector，且抢占无帮助 — 直接定位到调度约束问题\n- e3（kubectl_get_yaml）：Pod 的 nodeSelector 明确配置为 aiops.e2e/nonexistent-node-label=true，PodScheduled=False，reason=Unschedulable — 确认了 Pod 侧的调度约束\n- e4（节点标签列表）：3 个节点标签均不含 aiops.e2e/nonexistent-node-label — 确认了集群侧无匹配标签\n- e5（kubectl_events）：与 e2 交叉验证，事件内容一致\n\n## 关联分析\ne2+e3+e4+e5 构成完整证据闭环\n... 截断，原始 681 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector（aiops-e2e）处于 PendingUnschedulable 状态，根因为 nodeSelector 标签不匹配：Pod 配置了 nodeSelector: {"aiops.e2e/nonexistent-node-label": "tr...
   置信度: 100%
   🔗 因果链:
     根本原因: Pod rc-pending-nodeselector 配置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，但集群 3 个节点均未打该标签，导致调度器无法找到任何可用节点
     传导机制: Pod YAML 中 nodeSelector 定义 → kube-scheduler 检查所有 3 个节点的标签 → 无节点匹配 → 调度器标记 PodScheduled=False，reason=Unschedulable → 产生 FailedScheduling 事件 → Pod 持续处于 Pending 状态
     最终表现: Pod rc-pending-nodeselector（aiops-e2e）状态 Pending，0/1 容器就绪，未绑定节点（NODE=<none>），Events 显示 "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (20.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4774 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 26.4s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将根据您提供的详尽信息，为您生成一份完整的诊断报告。

---

## 📊 诊断概览

您的集群整体运行正常，**在 65 个 Pod 中，仅有 1 个 Pod 处于异常状态**。该问题根源明确，属于非生产性测试用例的配置错误，不影响核心业务运行。

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending (PendingUnschedulable) |
| **兼容归因层** | L1 - 调度约束不匹配 |
| **问题分类** | NodeSelector 标签不匹配 |
| **置信度** | 高 (100%) |
| **证据完整度** | 4/4 (100%) |

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-pending-nodeselector` |
| Namespace | `aiops-e2e` |
| Node | 未绑定 (NODE=`<none>`) |
| 错误信息 | `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` |

## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod状态确认 | `kubectl_get_by_name` | `NAME: rc-pending-nodeselector, STATUS: Pending, AGE: 22m` | Pod 仍存在，且处于 Pending 状态。 |
| 2 | 调度器事件 | `kubectl_events` | `22m Warning FailedScheduling ... 3 node(s) didn't match Pod's node affinity/selector.` | 调度器明确因节点亲和性/选择器不匹配而无法调度。 |
| 3 | Pod 配置 | `kubectl_get_yaml` | `Node-Selectors: aiops.e2e/nonexistent-node-label=true`, `command: sh -c sleep 3600` | Pod 配置了一个特定标签 `aiops.e2e/nonexistent-node-label=true`，且容器启动后仅为休眠。 |
| 4 | 节点标签 | `run_bash_command` | 集群 3 个节点 (master/node1/node2) 的标签列表中**均没有** `aiops.e2e/nonexistent-node-label` 标签。 | 集群中没有任何节点满足 Pod 的 nodeSelector 要求。 |

### 证据关联分析
- **证据 #2 + #3 + #4 印证**：调度器事件 `FailedScheduling` 与 Pod 的 `Node-Selectors` 配置，以及节点标签的缺失，三者形成完整的因果链。Pod 要求节点拥有 `aiops.e2e/nonexistent-node-label=true` 标签，但集群所有节点均无此标签。
- **证据链**：Pod YAML 定义 `Node-Selectors` → kube-scheduler 检查节点标签 → 无节点匹配 → 上报 `FailedScheduling` 事件 → Pod 持续 Pending。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| (无) | - | 所有关键证据均已采集，分析结论完整。 |

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                    │
│ Pod rc-pending-nodeselector 配置了 nodeSelector:                              │
│   aiops.e2e/nonexistent-node-label=true，但集群 3 个节点均无此标签。          │
└─────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                    │
│ kube-scheduler 无法找到任何满足标签条件的节点，导致 Pod 调度失败。             │
└─────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                    │
│ 调度器产生 FailedScheduling 事件，Pod 无法被分配到任何节点。                  │
└─────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                │
│ Pod rc-pending-nodeselector 状态为 Pending，无法运行。                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (FailedScheduling 事件)、#3 (Pod 的 nodeSelector 配置) 和 #4 (节点标签缺失)，问题的根本原因是**Pod `rc-pending-nodeselector` 的 `nodeSelector` 配置了一个集群中不存在的标签 `aiops.e2e/nonexistent-node-label=true`**，导致调度器无法为其找到合适的节点。

**置信度**：高 (100%)
- ✅ 调度器事件、Pod 配置、节点标签事实三者完全吻合。
- ✅ 从 Pod 名称 `rc-pending-nodeselector` 和标签 `rootcause-e2e=true` 判断，这是一个**测试或演示用例**，非生产业务 Pod，对核心业务无影响。

## 🛠️ 修复建议

### 立即执行（按优先级排序）
**1. [首选方案] 修改或移除 Pod 的 nodeSelector 配置**

由于集群中没有标签 `aiops.e2e/nonexistent-node-label`，您有两个选择：
- **方案A：删除 Pod（如果是测试用例）**
  ```bash
  kubectl delete pod rc-pending-nodeselector -n aiops-e2e
  ```
  *依据*：从Pod特征看，这很可能是一个E2E测试Pod，删除即可解决问题。

- **方案B：为任意一个节点打上要求的标签，或修改Pod配置**
  - 为节点打标签（例如在 `node1` 上）：
    ```bash
    kubectl label node node1 aiops.e2e/nonexistent-node-label=true
    ```
  - **或者**，修改 Pod 的 `nodeSelector` 为一个存在的标签（例如 `kubernetes.io/os=linux`）：
    ```bash
    kubectl edit pod rc-pending-nodeselector -n aiops-e2e
    ```
    在打开的 YAML 文件中，将 `nodeSelector` 下的值修改为 `kubernetes.io/os: linux`。
  *依据*：证据 #4 显示所有节点都有 `kubernetes.io/os=linux` 标签。

### 后续优化
1. **配置合规检查**：在 CI/CD 流程中增加对 Pod `nodeSelector` 或 `nodeAffinity` 的校验，确保引用的标签存在于目标集群中。
2. **资源管理**：对于非生产用途的测试、调试 Pod，建议使用独立的命名空间进行管理，并设置资源配额及 TTL 清理策略，避免其长期占用或干扰生产环境。

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态（方案A） | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | `Error from server (NotFound): pods "rc-pending-nodeselector" not found` |
| 2. 确认 Pod 状态（方案B） | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | `STATUS: Running` |

## ⚠️ 注意事项
- 本报告诊断的 Pod `rc-pending-nodeselector` 是一个独立的异常案例，集群中其余 59 个 Running 状态的 Pod 均正常运行。请放心，此次问题不影响集群整体健康。

---

## 📊 性能统计

├─ 总耗时: 1.4m
├─ 问题定位: 20.1s (23%) ✅
├─ 证据链采集: 21.3s (25%) ✅
├─ 根因分析: 24.5s (28%) ✅
├─ 汇总总结: 20.5s (24%) ✅
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
