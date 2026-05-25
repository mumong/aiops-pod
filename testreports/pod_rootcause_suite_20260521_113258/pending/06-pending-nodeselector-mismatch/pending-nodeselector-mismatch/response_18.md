======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: fd14d6a3c83540b9]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，我先扫描全局 Pod 状态，看看有哪些异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 发现了一个异常 Pod，我来进一步查看详情。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-nodeselector
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  12m                  default-scheduler  0/3 nodes are available
   💭 [问题定位] 现在我已经掌握了足够的信息。让我获取对应的 runbook 参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在我已经掌握了全部信息，来做定位分析。

---

## 定位分析结果

### 🎯 异常 Pod 扫描结果

| 命名空间 | Pod 名称 | 状态 | 就绪 |
|---------|---------|------|------|
| `aiops-e2e` | `rc-pending-nodeselector` | **Pending** | 0/1 |

集群共 65 个 Pod，其中 59 个 Running，1 个异常 Pending。

---

### 📋 异常详情

**Pod:** `rc-pending-nodeselector`（命名空间 `aiops-e2e`）

**状态关键字:** Pending

**核心事件:**
```
FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector
```

**根因分析:**
该 Pod 设置了 `Node-Selectors: aiops.e2e/nonexistent-node-label=true`，但集群中没有任何节点拥有这个标签，导致所有 3 个节点都不匹配该选择器，调度器无法放置。

---

### 📊 分层输出

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **layer_name** | PendingUnschedulable |
| **pod_abnormal_type** | PendingUnschedulable |
| **pod_status_keyword** | Pending |
| **status_category** | scheduling |
| **confidence** | 高 |

**异常组 (abnormal_groups):**
- `PendingUnschedulable` → `rc-pending-nodeselector`

**关键实体 (key_entities):**
- Pod: `rc-pending-nodeselector` (aiops-e2e)
- 节点: 全部 3 个节点均不匹配

**可能场景 (possible_scenarios):**
1. **nodeSelector 不匹配** (最可能): Pod 指定 `aiops.e2e/nonexistent-node-label=true`，但集群中没有任何节点打了该标签，导致调度器无法找到可用节点。
2. 如果该标签是预期要存在的，说明节点标签缺失或配置有误。

**后续审查方向:**
- 确认节点上是否存在 `aiops.e2e/nonexistent-node-label=true` 标签
- 确认该 Pod 是否被正确配置了预期调度的目标节点标签
   ✅ [问题定位] 完成 (21.5s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'nodeSelector 不匹配', 'probability': '高', 'reason': 'Pod指定 aiops.e2e/nonexistent-node-label=true，但集群3个节点均无此标签，调度器无法放置Pod'}, {'scenario': '节点标签配置缺失', 'probability': '中', 'reason': '如果该标签预期应存在，则说明节点标签配置有误或遗漏'}]
   entities=[{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Node", "name": "all 3 nodes", "namespace": ""}]
   reasoning=集群中存在1个异常Pod rc-pending-nodeselector (aiops-e2e)，状态为Pending，事件显示FailedScheduling: 0/3 nodes are available - 3 node(s) didn't match Pod's node affinity/selector。Pod设置了nodeSelector (aiops.e2e/nonexistent-node-label=true)，但集群中没有任何节点匹配该标签。属于调度约束不匹配问题，归因于L1 scheduling层。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable", "confidence": 0.95, "reasoning": "集群中存在1个异常Pod rc-pending-nodeselector (aiops-e2e)，状态为Pending，事件显示FailedScheduling: 0/3 nodes are available - 3 node(s) didn't match Pod's node affinity/selector。Pod设置了nodeSelector (aiops.e2e/nonexistent-node-label=true)，但集群中没有任何节点匹配该标签。属于调度约束不匹配问题，归因于L1 scheduling层。", "abnormal_pods": [{"name": "rc-pending-nodeselector", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-nodeselector", "namespace": "aiops-e2e"}, {"type": "Node", "name": "all 3 nodes", "namespace": ""}], "possible_scenarios": [{"scenario": "nodeSelector 不匹配", "probability": "高", "reason": "Pod指定 aiops.e2e/nonexistent-node-label=true，但集群3个节点均无此标签，调度器无法放置Pod"}, {"scenario": "节点标签配置缺失", "probability": "中", "reason": "如果该标签预期应存在，则说明节点标签配置有误或遗漏"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-nodeselector"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-nodeselector                             0/1     Pending     0              12m     <none>           <none>   <none>           <none>            app=rc-pending-nodeselector,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/fd14d6a3c83540b9/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/fd14d6a3c83540b9/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/fd14d6a3c83540b9/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，按既有 evidence_plan 执行。先同时启动 e1（describe pod）和 e2（get pod yaml）获取核心证据。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
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
  Warning  FailedScheduling  12m                    default-scheduler  0/3 nodes are availab
   💭 [证据链采集] Pod 的 nodeSelector 已明确为 `aiops.e2e/nonexistent-node-label=true`。现在执行 e3：检查集群各节点的标签，确认无节点匹配。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAME     STATUS   ROLES           AGE    VERSION   LABELS\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpg
   💭 [证据链采集] 所有 3 个节点的标签都已获取，逐一核对。现在我来总结采集到的证据。

---

## ✅ 证据采集完成

### 已采集证据（3 条 critical 级，全部命中）

| 计划项 | 工具 | 关键证据内容 | 证据类型 |
|--------|------|-------------|---------|
| **e1-pod-describe** | `kubectl_describe` | `FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` — 调度器明确拒绝所有 3 个节点 | ✅ 正向证据 |
| **e2-pod-yaml** | `kubectl_get_yaml` | Pod spec `nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}` — Pod 要求节点必须包含此标签 | ✅ 正向证据 |
| **e3-node-list** | `run_bash_command` | 3 个节点标签列表：**master**、**node1**、**node2** — 均**不包含** `aiops.e2e/nonexistent-node-label` 标签 | ✅ 正向证据 |

### 诊断结论

**根因：nodeSelector 标签完全不匹配**

- Pod `rc-pending-nodeselector` 设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`
- 集群 3 个节点（master/node1/node2）均**没有任何一个节点拥有该标签**
- 调度器无法放置 Pod，产生 `FailedScheduling` 事件，Pod 一直卡在 **Pending** 状态

**其他维度验证结果：**
- ❌ 资源不足 — 不存在（调度器未报 Insufficient resource）
- ❌ taint/toleration — 不存在（无 untolerated taint 提示）
- ❌ PVC/卷依赖 — 不存在（Pod 无 PVC 引用）
- ✅ **nodeSelector/affinity 不匹配** — 唯一且明确的根因

### 未采集 / 冲突证据
- 无冲突证据，全部工具结果与上游定位一致。
   ✅ [证据链采集] 完成 (17.8s)
   📤 → 下游数据: evidence_items=5/5
   evidence_analysis={"evidence_plan":[{"id":"e1-pod-describe","description":"验证Pod rc-pending-nodeselector 当前状态、Events中的FailedScheduling原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-pending-nodeselector","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"读取FailedScheduling事件的精确原文，确认调度失败根因","evidence_type":"pod_status_and_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2-pod-yaml","description":"获取Pod完整YAML，检查nodeSelector/affinity配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod -n aiops-e2e rc-pending-nodeselector -o yaml","tool_args":{"kind":"pod","name":"rc-pending-nodeselector","namespace":"aiops-e2e"},"purpose":"检查nodeSelector和affinity的具体标签要求","evidence_type":"pod_spec_config","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3-node-list","description":"获取集群所有节点及其标签，验证是否存在匹配的节点","level":"critical","tool":"run_bash_command","command":"kubectl get nodes --show-labels","tool_args":{},"purpose":"验证集群各节点的标签情况，确认无节点匹配Pod的nodeSelector","evidence_type":"node_label_check","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:18:44Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-nodeselector, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\nnodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nvolumes:\n- {\"name\": \"kube-api-access-w74s5\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fd14d6a3c83540b9/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fd14d6a3c83540b9/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fd14d6a3c83540b9/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-nodeselector\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  12m                    default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  2m27s (x2 over 7m27s)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: aiops.e2e/nonexistent-node-label=true\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-w74s5:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  12m                    default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n  Warning  FailedScheduling  2m27s (x2 over 7m27s)  default-scheduler  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fd14d6a3c83540b9/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fd14d6a3c83540b9/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fd14d6a3c83540b9/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAME     STATUS   ROLES           AGE    VERSION   LABELS\\nmaster   Ready    control-plane   238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=master,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false,node-role.kubernetes.io/control-plane=,node.kubernetes.io/exclude-from-external-load-balancers=\\nnode1    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node1,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\nnode2    Ready    <none>          238d   v1.26.8   beta.kubernetes.io/arch=amd64,beta.kubernetes.io/os=linux,fpga-version=,kubernetes.io/arch=amd64,kubernetes.io/hostname=node2,kubernetes.io/os=linux,metax-tech.com/gpu.installed=false\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fd14d6a3c83540b9/tools/003-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fd14d6a3c83540b9/tools/003-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fd14d6a3c83540b9/tools/003-evidence-run_bash_command.summary.txt"}],"llm_analysis":"所有 3 个节点的标签都已获取，逐一核对。现在我来总结采集到的证据。\n\n---\n\n## ✅ 证据采集完成\n\n### 已采集证据（3 条 critical 级，全部命中）\n\n| 计划项 | 工具 | 关键证据内容 | 证据类型 |\n|--------|------|-------------|---------|\n| **e1-pod-describe** | `kubectl_describe` | `FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` — 调度器明确拒绝所有 3 个节点 | ✅ 正向证据 |\n| **e2-pod-yaml** | `kubectl_get_yaml` | Pod spec `nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}` — Pod 要求节点必须包含此标签 | ✅ 正向证据 |\n| **e3-node-list** | `run_bash_command` | 3 个节点标签列表：**master**、**node1**、**node2** — 均**不包含** `aiops.e2e/nonexistent-node-label` 标签 | ✅ 正向证据 |\n\n### 诊断结论\n\n**根因：nodeSelector 标签完全不匹配**\n\n- Pod `rc-pending-nodeselector` 设置了 `nodeSelector: aiops.e2e/nonexistent-node-label=true`\n- 集群 3 个节点（master/node1/node2）均**没有任何一个节点拥有该标签**\n- 调度器无法放置 Pod，产生 `FailedScheduling` 事件，Pod 一直卡在 **Pending** 状态\n\n**其他维度验证结果：**\n- ❌ 资源不足 — 不存在（调度器未报 Insufficient resource）\n- ❌ taint/toleration — 不存在（无 untolerated taint 提示）\n- ❌ PVC/卷依赖 — 不存在（Pod 无 PVC 引用）\n- ✅ **nodeSelector/affinity 不匹配** — 唯一且明确的根因\n\n### 未采集 / 冲突证据\n- 无冲突证据，全部工具结果与上游定位一致。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 5/5 项，完整度 100%；实际执行工具 5 个，匹配计划 3 个，未规划证据 2 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":5,"environment_evidence_collected":5,"environment_evidence_completeness":1.0,"executed_tool_count":5,"matched_tool_count":3,"unplanned_tool_count":2,"evidence_inventory":[{"id":"e1-pod-describe","description":"验证Pod rc-pending-nodeselector 当前状态、Events中的FailedScheduling原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod -n aiops-e2e rc-pending-nodeselector","purpose":"读取FailedScheduling事件的精确原文，确认调度失败根因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2-pod-yaml","description":"获取Pod完整YAML，检查nodeSelector/affinity配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod -n aiops-e2e rc-pending-nodeselector -o yaml","purpose":"检查nodeSelector和affinity的具体标签要求","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3-node-list","description":"获取集群所有节点及其标签，验证是否存在匹配的节点","level":"critical","tool":"run_bash_command","command":"kubectl get nodes --show-labels","purpose":"验证集群各节点的标签情况，确认无节点匹配Pod的nodeSelector","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1-pod-describe | critical | ✅ | kubectl_describe | 验证Pod rc-pending-nodeselector 当前状态、Events中的Fa... | `kubectl describe pod -n aiops-e2e rc-pending-nodeselector` |
   | e2-pod-yaml | critical | ✅ | kubectl_get_yaml | 获取Pod完整YAML，检查nodeSelector/affinity配置 | `kubectl get pod -n aiops-e2e rc-pending-nodeselector -o yaml` |
   | e3-node-list | critical | ✅ | run_bash_command | 获取集群所有节点及其标签，验证是否存在匹配的节点 | `kubectl get nodes --show-labels` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (20.1s)
   📤 → 下游数据: root_cause=Pod rc-pending-nodeselector (aiops-e2e) 处于Pending状态，根因为nodeSelector调度约束不匹配。Pod YAML确认设置了 nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}，而集群3个节点（master/node1/node2）的标签均不包含该标签。调度器Event明确报告"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector"，无资源不足或taint等其他问题。集群其余59个Pod均正常运行。
   confidence=98%
   causal_chain={"root_cause": "Pod rc-pending-nodeselector 设置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，但集群3个节点均无此标签，导致调度器无法找到任何可调度节点", "propagation": "Pod spec中定义了nodeSelector约束 → kube-scheduler在调度时检查所有节点的标签 → 3个节点均不满足标签条件 → 调度器标记Pod为Unschedulable → 持续重试调度仍失败 → Pod一直处于Pending状态", "direct_cause": "nodeSelector标签不匹配：Pod要求aiops.e2e/nonexistent-node-label=true，集群3个节点均无此标签", "manifestation": "Pod rc-pending-nodeselector 在aiops-e2e命名空间下持续12分钟处于Pending状态，Events持续报告FailedScheduling"}
   rca_analysis={"phenomenon": "集群中存在1个异常Pod rc-pending-nodeselector (namespace: aiops-e2e)，状态为Pending，持续约12分钟。调度器事件显示 FailedScheduling: 0/3 nodes are available - 3 node(s) didn't match Pod's node affinity/selector。", "evidence_inventory": [{"id": "e1-pod-describe", "source": "kubectl_describe", "content": "Pod rc-pending-nodeselector 处于Pending状态，Events显示FailedScheduling: 0/3 nodes不匹配node affinity/selector", "reliability": "高"}, {"id": "e2-pod-yaml", "source": "kubectl_get_yaml", "content": "Pod spec中nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}", "reliability": "高"}, {"id": "e3-node-list", "source": "run_bash_command (kubectl get nodes)", "content": "集群3个节点(master/node1/node2)的标签列表均不包含aiops.e2e/nonexistent-node-label", "reliability": "高"}, {"id": "layer_1", "source": "kubectl_get_by_kind_in_cluster", "content": "集群共65个Pod，仅此1个异常Pending，其余59个Running", "reliability": "高"}, {"id": "layer_2", "source": "kubectl_describe (上游)", "content": "与e1一致，确认FailedScheduling事件", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1-pod-describe", "raw_data": "Warning FailedScheduling 12m default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.", "interpretation": "调度器明确拒绝所有3个节点，原因是节点与Pod的nodeSelector/affinity不匹配，非资源不足或taint问题"}, {"evidence_id": "e2-pod-yaml", "raw_data": "nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}", "interpretation": "Pod明确要求节点必须包含标签 aiops.e2e/nonexistent-node-label=true 才能被调度"}, {"evidence_id": "e3-node-list", "raw_data": "master labels: beta.kubernetes.io/arch=amd64,...,node-role.kubernetes.io/control-plane=; node1 labels: beta.kubernetes.io/arch=amd64,...,kubernetes.io/hostname=node1; node2 labels: ...kubernetes.io/hostname=node2", "interpretation": "集群3个节点（master/node1/node2）的完整标签列表中，均不存在 aiops.e2e/nonexistent-node-label 标签，没有任何节点可以满足Pod的nodeSelector条件"}, {"evidence_id": "layer_1", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}", "interpretation": "集群整体健康，仅此一个Pod异常，不影响其他工作负载"}, {"evidence_id": "layer_2", "raw_data": "与e1一致", "interpretation": "交叉验证确认Pod状态和事件信息一致"}], "causal_chain": {"root_cause": "Pod rc-pending-nodeselector 设置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，但集群3个节点均无此标签，导致调度器无法找到任何可调度节点", "propagation": "Pod spec中定义了nodeSelector约束 → kube-scheduler在调度时检查所有节点的标签 → 3个节点均不满足标签条件 → 调度器标记Pod为Unschedulable → 持续重试调度仍失败 → Pod一直处于Pending状态", "direct_cause": "nodeSelector标签不匹配：Pod要求aiops.e2e/nonexistent-node-label=true，集群3个节点均无此标签", "manifestation": "Pod rc-pending-nodeselector 在aiops-e2e命名空间下持续12分钟处于Pending状态，Events持续报告FailedScheduling"}, "root_cause": "Pod rc-pending-nodeselector (aiops-e2e) 处于Pending状态，根因为nodeSelector调度约束不匹配。Pod YAML确认设置了 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}，而集群3个节点（master/node1/node2）的标签均不包含该标签。调度器Event明确报告\"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"，无资源不足或taint等其他问题。集群其余59个Pod均正常运行。", "root_cause_summary": "Pod rc-pending-nodeselector (aiops-e2e) 处于Pending状态，根因为nodeSelector调度约束不匹配。Pod YAML确认设置了 nodeSelector: {\"aiops.e2e/nonexistent-node-label\": \"true\"}，而集群3个节点（master/node1/node2）的标签均不包含该标签。调度器Event明确报告\"0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector\"，无资源不足或taint等其他问题。集群其余59个Pod均正常运行。", "confidence": 0.98, "confidence_reason": "三条critical级证据（Pod描述、Pod YAML、节点标签列表）完全吻合，形成完整因果链。调度器事件原文明确指向nodeSelector不匹配，无任何矛盾或冲突证据。直接观察到Pod spec中的nodeSelector配置、节点标签列表的缺失，以及调度器的拒绝事件三者一致。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "资源不足（CPU/内存不足）", "probability": "low", "reason": "调度器事件仅报告'node affinity/selector'不匹配，未出现Insufficient cpu/memory等关键字"}, {"cause": "节点taint未被toleration容忍", "probability": "low", "reason": "调度器事件未提及taint相关拒绝原因，Pod已有2个toleration（含not-ready:NoExecute）"}, {"cause": "PVC未绑定或卷依赖未满足", "probability": "low", "reason": "Pod YAML中volumes仅包含kube-api-access-w74s5（ServiceAccount投射卷），无PVC引用"}], "limitations": "未检查节点标签是否本应存在但被误删（即配置漂移），但这不影响根因判定——当前状态就是无匹配节点。未检查是否有节点本应打上该标签但尚未打上。如果期望该标签存在，需进一步检查节点标签管理流程。", "llm_raw_analysis": "证据清点：共5条证据（3条critical级+2条important级）。e1-pod-describe和e2-pod-yaml确认Pod状态为Pending，nodeSelector=aiops.e2e/nonexistent-node-label=true；e3-node-list确认3个节点均无此标签；layer_1确认集群仅此一个异常Pod；layer_2交叉验证。因果链：Pod nodeSelector要求→节点无匹配标签→调度器拒绝→Pending。置信度0.98因证据直接且无矛盾。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-nodeselector (aiops-e2e) 处于Pending状态，根因为nodeSelector调度约束不匹配。Pod YAML确认设置了 nodeSelector: {"aiops.e2e/nonexistent-node-label": "true"}，而集...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod rc-pending-nodeselector 设置了 nodeSelector: aiops.e2e/nonexistent-node-label=true，但集群3个节点均无此标签，导致调度器无法找到任何可调度节点
     传导机制: Pod spec中定义了nodeSelector约束 → kube-scheduler在调度时检查所有节点的标签 → 3个节点均不满足标签条件 → 调度器标记Pod为Unschedulable → 持续重试调度仍失败 → Pod一直处于Pending状态
     最终表现: Pod rc-pending-nodeselector 在aiops-e2e命名空间下持续12分钟处于Pending状态，Events持续报告FailedScheduling


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (21.3s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 4962 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 20.6s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将为您生成一份详尽、完整的诊断报告。

---
## 📊 诊断概览

**针对您的问题“我的集群有什么问题”，以下是核心结论：**

当前集群（共65个Pod）整体运行平稳，**59个Pod正常运行**，但存在 **1个异常Pod**。

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending |
| **兼容归因层** | L1 - Scheduling (调度层) |
| **问题分类** | PendingUnschedulable (调度约束不匹配) |
| **置信度** | 高 (98%) |
| **证据完整度** | 3/3 (100%) |

**总结**：集群中 `aiops-e2e` 命名空间下的 Pod `rc-pending-nodeselector` 因设置了集群中不存在的节点标签（`nodeSelector`），导致无法被调度到任何节点上，持续处于 **Pending** 状态。其他59个Pod均正常运行，集群无资源短缺或节点故障问题。

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 问题 Pod | `rc-pending-nodeselector` |
| Namespace | `aiops-e2e` |
| Node | `<none>` (未分配到节点) |
| 错误信息 | `FailedScheduling: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` |

**Pod 当前状态**：
- **Status**: `Pending`
- **Restarts**: 0
- **Age**: 12m

---

## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | `Warning FailedScheduling 12m default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.` | 调度器明确报告无法调度，原因是**节点亲和性/选择器不匹配** |
| 2 | Pod 配置 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o yaml` | `Node-Selectors: aiops.e2e/nonexistent-node-label=true` | Pod 配置了 `nodeSelector`，要求节点必须包含标签 `aiops.e2e/nonexistent-node-label=true` |
| 3 | 节点标签 | `kubectl get nodes --show-labels` | 3个节点 (`master`, `node1`, `node2`) 的标签列表中**均不包含** `aiops.e2e/nonexistent-node-label` | 集群中没有任何节点满足 Pod 的 `nodeSelector` 约束 |

### 证据关联分析
- **证据 #2 + 证据 #3 印证**：Pod 要求节点拥有 `aiops.e2e/nonexistent-node-label=true` 标签，但集群中所有3个节点均无此标签。
- **证据链**：Pod 定义 `nodeSelector` → `kube-scheduler` 检查所有节点标签 → 无匹配节点 → 触发 `FailedScheduling` 事件（证据 #1） → Pod 持续停留在 `Pending` 状态。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | - | - |

---

## 🎯 根因分析

### 因果链
```
┌──────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                             │
│ Pod 的 nodeSelector 配置了集群中不存在的节点标签                      │
│ (aiops.e2e/nonexistent-node-label=true)                              │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                             │
│ kube-scheduler 根据 nodeSelector 遍历集群所有3个节点，均不匹配       │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                             │
│ 调度器没有任何可调度的节点，标记 Pod 为 Unschedulable                │
│ (Event: FailedScheduling)                                            │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                         │
│ Pod (rc-pending-nodeselector) 持续处于 Pending 状态                   │
└──────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (Pod YAML 中的 `Node-Selectors`) 和证据 #3 (所有节点的标签列表)，问题的根本原因是 **Pod `rc-pending-nodeselector` 的 `nodeSelector` (`aiops.e2e/nonexistent-node-label=true`) 在集群中找不到任何匹配节点**，导致调度失败并持续阻塞。
**置信度**：高 (98%)
- ✅ `kubectl describe` 的事件明确指向 `didn't match Pod's node affinity/selector`
- ✅ `kubectl get pod -o yaml` 和 `kubectl get nodes --show-labels` 直接印证了匹配失败
- ✅ 已排除资源不足、节点污点等其他常见Pending原因（调度器事件未提及）

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）
**1. [推荐] 移除或更正 Pod 的 nodeSelector**

有两种方式，根据业务需求选择其一：

- **方式A：删除 `nodeSelector`，允许 Pod 调度到任何节点**
  ```bash
  # 如果是 Deployment/StatefulSet 等控制器
  kubectl edit deployment rc-pending-nodeselector -n aiops-e2e
  # 在 spec.template.spec 下找到 nodeSelector 并删除
  ```
  *依据*：如果 Pod 不需要特定节点标签，移除约束即可正常调度。

- **方式B：给某个节点打上正确的标签，以匹配 Pod 的需求**
  ```bash
  # 例如，给 node1 打上标签
  kubectl label node node1 aiops.e2e/nonexistent-node-label=true
  ```
  *依据*：如果 Pod 必须调度到具有特定属性的节点上，则需要为节点打上对应标签。

**2. [验证] 查看 Pod 调度结果**
```bash
kubectl get pod rc-pending-nodeselector -n aiops-e2e -w
```
*预期*：Pod 状态从 `Pending` 变为 `ContainerCreating`，最终变为 `Running`。

### 后续优化
1. **标签管理**：审查节点标签的分配与维护流程，确保 `nodeSelector` 引用的标签始终存在。
2. **配置检查**：在 CI/CD 流程中加入对 Pod YAML 中 `nodeSelector`/`affinity` 的校验，防止部署不存在的标签。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e` | STATUS: `Running` |
| 2. 确认节点分配 | `kubectl get pod rc-pending-nodeselector -n aiops-e2e -o wide` | NODE 列显示具体节点名 |
| 3. 确认无新调度失败事件 | `kubectl describe pod rc-pending-nodeselector -n aiops-e2e` | Events 中无新的 `FailedScheduling` |

---

## ⚠️ 注意事项
- 如果集群中其他应用正常，此问题为**孤立问题**，无需担心集群整体健康。
- 如果该 Pod 是由 Deployment 管理，修改 `nodeSelector` 后控制器会自动删除旧Pod并创建新Pod。

---

## 📊 性能统计

├─ 总耗时: 1.3m
├─ 问题定位: 21.5s (27%) ✅
├─ 证据链采集: 17.8s (22%) ✅
├─ 根因分析: 20.1s (25%) ✅
├─ 汇总总结: 21.3s (26%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 6 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 6 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
