======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 0195ac56a9b248a1]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来先做全局 Pod 状态扫描，看看集群中有什么异常。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 发现一个明显的异常 Pod。让我进一步确认它的状态详情。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-memory
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  10m    default-scheduler  0/3 nodes are available: 3 Ins
   💭 [问题定位] 现在我有足够的证据了，让我再拿一下匹配的 runbook 作为参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在已经获取了足够的信息，可以给出完整的定位分析了。

---

## 当前集群 Pod 异常诊断

### 全局扫描结果

| 状态 | 数量 |
|------|------|
| **Running** | 59 |
| **Pending** | 1 |
| **其他正常** | Completed/Succeeded - 5 |
| **总计** | 65 |

### 发现的异常 Pod

| 命名空间 | Pod 名称 | 状态 | 异常类型 |
|---------|---------|------|---------|
| `aiops-e2e` | `rc-pending-insufficient-memory` | **Pending** | **PendingUnschedulable** |

---

### 异常详情分析

**Pod:** `rc-pending-insufficient-memory` (aiops-e2e 命名空间)  
**状态:** Pending，未绑定节点（node = `<none>`）  
**异常类型:** `PendingUnschedulable`  
**兼容层级:** L1

**调度失败原因（来自 Events）：**
```
0/3 nodes are available: 3 Insufficient memory.
preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.
```

集群中 **3 个节点全部内存不足**，无法调度该 Pod，且抢占（preemption）也找不到可以驱逐的 Pod 来释放内存。

**Pod 信息：**
- 镜像：`busybox:1.36`
- QoS 类别：`Burstable`
- 无节点选择器（nodeSelector）、无特殊容忍度
- 请求资源（隐含）：该 Pod 请求的内存超过了 3 个节点上任何单个节点的剩余可分配内存

---

### 关键实体

| 实体类型 | 名称 |
|---------|------|
| 异常 Pod | `aiops-e2e/rc-pending-insufficient-memory` |
| 异常类型 | PendingUnschedulable |
| 受影响节点 | 全部 3 个节点（内存均不足） |
| 关键事件 | FailedScheduling - Insufficient memory |

### 可能场景

1. **集群整体内存资源不足** — 3 个节点都已分配了大部分内存，剩余可分配量不满足此 Pod 的 requests 要求
2. **Pod 请求了较大的内存量** — 该 Pod 可能设置了较高的 `resources.requests.memory`
3. **节点上运行了过多业务 Pod** — 导致没有空闲内存留给新 Pod

---

### 输出结构化摘要

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **layer_name** | PendingUnschedulable - 内存不足 |
| **pod_status_keyword** | Pending |
| **pod_abnormal_type** | PendingUnschedulable |
| **status_category** | scheduling |
| **abnormal_pods 数量** | 1 |
| **abnormal_groups 类型** | PendingUnschedulable |

> **建议下一步**：检查各节点的内存分配情况（`kubectl describe node` 查看 Allocatable 与 Allocated resources），确认是否需要扩容节点、优化现有 Pod 资源请求、或降低该 Pod 的 memory request。
   ✅ [问题定位] 完成 (23.0s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '集群整体内存资源不足', 'probability': '高', 'reason': '3个节点全部报告 Insufficient memory，无节点可调度'}, {'scenario': 'Pod 请求了较大的内存量', 'probability': '中', 'reason': 'Pod 为 Burstable QoS，可能设置了较高的 resources.requests.memory'}, {'scenario': '节点上运行了过多业务 Pod 导致内存耗尽', 'probability': '中', 'reason': '集群中 Running Pod 有 59 个，可能占用了大量内存'}]
   entities=[{"type": "Pod", "name": "rc-pending-insufficient-memory", "namespace": "aiops-e2e"}, {"type": "Cluster", "name": "全部3个节点（内存均不足）", "namespace": ""}]
   reasoning=集群中存在一个当前仍处于 Pending 状态的异常 Pod `rc-pending-insufficient-memory`（aiops-e2e 命名空间），异常类型为 PendingUnschedulable。Events 明确显示 0/3 nodes are available: 3 Insufficient memory，所有节点内存均不足，调度失败且抢占无受害者。根据五层模型，PendingUnschedulable 归因于调度/节点资源不足，属于 L1 层级。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable - 内存不足", "confidence": 0.95, "reasoning": "集群中存在一个当前仍处于 Pending 状态的异常 Pod `rc-pending-insufficient-memory`（aiops-e2e 命名空间），异常类型为 PendingUnschedulable。Events 明确显示 0/3 nodes are available: 3 Insufficient memory，所有节点内存均不足，调度失败且抢占无受害者。根据五层模型，PendingUnschedulable 归因于调度/节点资源不足，属于 L1 层级。", "abnormal_pods": [{"name": "rc-pending-insufficient-memory", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-insufficient-memory", "namespace": "aiops-e2e"}, {"type": "Cluster", "name": "全部3个节点（内存均不足）", "namespace": ""}], "possible_scenarios": [{"scenario": "集群整体内存资源不足", "probability": "高", "reason": "3个节点全部报告 Insufficient memory，无节点可调度"}, {"scenario": "Pod 请求了较大的内存量", "probability": "中", "reason": "Pod 为 Burstable QoS，可能设置了较高的 resources.requests.memory"}, {"scenario": "节点上运行了过多业务 Pod 导致内存耗尽", "probability": "中", "reason": "集群中 Running Pod 有 59 个，可能占用了大量内存"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-memory"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-memory"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-insufficient-memory                      0/1     Pending     0              10m     <none>           <none>   <none>           <none>            app=rc-pending-insufficient-memory,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/0195ac56a9b248a1/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/0195ac56a9b248a1/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/0195ac56a9b248a1/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来按既有 evidence_plan 执行工具调用，先并行执行前三项关键工具：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"name\": \"master\",\n  \"capacity\": \"32860484Ki\",\n  \"allocatable\": \"32758084Ki\",\n  \"conditions\": [\n    {\n      \"type\": \"MemoryPressure\",\n      \"s
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-memory
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  10m                  default-scheduler  0/3 nodes are av
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-insufficient-memory
namespace: aiops-e2e
creationTimestamp: 2026-05-21T08:00:52Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finali
   💭 [证据链采集] 好的，describe 和 YAML 都确认了 Pod 没有设置 resources.requests.memory，这意味着调度器是按 0 请求来算的。现在来查 Prometheus 内存使用率和 Pod 的 resources 细节。

从 YAML 没看到 resources 字段，让我再专门确认一下 Pod spec 的资源请求：
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"requests\": {\n    \"cpu\": \"50m\",\n    \"memory\": \"100000Gi\"\n  }\n}\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 execute_prometheus_instant_query 执行成功但结果为空；这表示查询未命中数据，不能视为已采集到指标值。
   💭 [证据链采集] 找到了根本原因！让我再验证一下节点总内存容量做对比：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "master: 32860484Ki = 31 Gi\nnode1: 32860476Ki = 31 Gi\nnode2: 32860480Ki = 31 Gi\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] ## 证据采集结论

### ✅ 已采集证据

| 证据维度 | 结果 |
|---------|------|
| **Pod 当前状态**（e1 - describe） | **Pending**，`node: <none>`，最新 FailedScheduling 事件在 **26s 前**（仍在持续重试） |
| **FailedScheduling 事件原文**（e1） | **`0/3 nodes are available: 3 Insufficient memory`** + `3 No preemption victims found` |
| **Pod 内存请求量**（e2 - YAML + json） | **`resources.requests.memory = 100000Gi`**（十万 Gi！） |
| **Pod QoS**（e1） | **Burstable**（有 requests 但没 limits） |
| **Pod 其他调度约束**（e1/e2） | 无 nodeSelector、无 affinity、无 taint/toleration 冲突、无 PVC 依赖 |
| **节点容量**（e3 - nodes json） | 3 个节点各自 **capacity ≈ 31Gi**，**allocatable ≈ 31Gi** |
| **节点状态**（e3） | 全部 **Ready=True**，**MemoryPressure=False**，节点本身无异常 |
| **Prometheus 内存指标**（e4） | 查询命中为空（Prometheus 可能未就绪），但节点容量数据已充分说明问题 |

### 🔍 根因定位
**Pod `rc-pending-insufficient-memory` 设置了 `resources.requests.memory = 100000Gi`**（十万 Gi），而集群每个节点仅有约 **31Gi** 可分配内存。调度器评估所有 3 个节点后，没有任何节点能提供 100000Gi 内存，因此 `0/3 nodes are available: 3 Insufficient memory`。Pod 本身 QoS 为 Burstable、无额外调度约束，根因**明确为 Pod 内存请求量严重超出集群容量**，属于配置错误。

### ❌ 未采集证据 / 冲突
- **Prometheus 内存使用率查询**（e4）：返回空结果，Prometheus 指标可能未部署或未就绪，不作为根因判断依据——节点容量对比已足够确定问题。
- **集群节点本身无异常**：所有节点 Ready、无 MemoryPressure，因此问题不在节点层面，而在 Pod 自身的资源请求配置。
   ✅ [证据链采集] 完成 (29.8s)
   📤 → 下游数据: evidence_items=5/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证 Pod rc-pending-insufficient-memory 的当前状态和 FailedScheduling 事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-memory -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-insufficient-memory","namespace":"aiops-e2e"},"purpose":"验证 Pod 当前是否仍处于 Pending 状态，并获取 FailedScheduling 事件原文确认资源不足原因","evidence_type":"pod_status_and_events","target_scope":"aiops-e2e/rc-pending-insufficient-memory","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"获取 Pod YAML 检查 resources.requests 内存配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-memory -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-insufficient-memory","namespace":"aiops-e2e"},"purpose":"检查 Pod 的内存请求量（resources.requests.memory），判断是否请求了较大内存","evidence_type":"pod_spec_resources","target_scope":"aiops-e2e/rc-pending-insufficient-memory","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"查看集群所有 Node 的内存容量和 allocatable 资源","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, capacity: .status.capacity.memory, allocatable: .status.allocatable.memory, conditions: [.status.conditions[] | select(.type==\"MemoryPressure\" or .type==\"Ready\") | {type: .type, status: .status}]}'","tool_args":{},"purpose":"验证集群各节点的内存容量和可分配内存，确认是否有节点内存不足或处于 MemoryPressure 状态","evidence_type":"node_memory_capacity","target_scope":"集群全部节点","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"通过 Prometheus 查询集群节点的内存使用率","level":"critical","tool":"execute_prometheus_instant_query","command":"sum by (node) (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100","tool_args":{"query":"sum by (node) (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100"},"purpose":"获取所有节点的实时内存使用率，验证是否确实存在节点内存不足","evidence_type":"node_memory_usage_promql","target_scope":"集群全部节点","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5","description":"Fetch 已确认的 runbook 作为参考","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","tool_args":{"runbook_name":"pod-pending-unschedulable.md"},"purpose":"获取 PendingUnschedulable 运行手册作为诊断参考","evidence_type":"reference","target_scope":"reference","acceptable_tools":[],"counts_for_completeness":false}],"tool_results":[],"tool_data":[{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"name\\\": \\\"master\\\",\\n  \\\"capacity\\\": \\\"32860484Ki\\\",\\n  \\\"allocatable\\\": \\\"32758084Ki\\\",\\n  \\\"conditions\\\": [\\n    {\\n      \\\"type\\\": \\\"MemoryPressure\\\",\\n      \\\"status\\\": \\\"False\\\"\\n    },\\n    {\\n      \\\"type\\\": \\\"Ready\\\",\\n      \\\"status\\\": \\\"True\\\"\\n    }\\n  ]\\n}\\n{\\n  \\\"name\\\": \\\"node1\\\",\\n  \\\"capacity\\\": \\\"32860476Ki\\\",\\n  \\\"allocatable\\\": \\\"32758076Ki\\\",\\n  \\\"conditions\\\": [\\n    {\\n      \\\"type\\\": \\\"MemoryPressure\\\",\\n      \\\"status\\\": \\\"False\\\"\\n    },\\n    {\\n      \\\"type\\\": \\\"Ready\\\",\\n      \\\"status\\\": \\\"True\\\"\\n    }\\n  ]\\n}\\n{\\n  \\\"name\\\": \\\"node2\\\",\\n  \\\"capacity\\\": \\\"32860480Ki\\\",\\n  \\\"allocatable\\\": \\\"32758080Ki\\\",\\n  \\\"conditions\\\": [\\n    {\\n      \\\"type\\\": \\\"MemoryPressure\\\",\\n      \\\"status\\\": \\\"False\\\"\\n    },\\n    {\\n      \\\"type\\\": \\\"Ready\\\",\\n      \\\"status\\\": \\\"True\\\"\\n    }\\n  ]\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0195ac56a9b248a1/tools/001-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0195ac56a9b248a1/tools/001-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0195ac56a9b248a1/tools/001-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-insufficient-memory\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  10m                  default-scheduler  0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  26s (x2 over 5m26s)  default-scheduler  0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nName:             rc-pending-insufficient-memory\nLabels:           app=rc-pending-insufficient-memory\nPod 关键区块:\nQoS Class: Burstable\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-c69j6:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  10m                  default-scheduler  0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  26s (x2 over 5m26s)  default-scheduler  0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0195ac56a9b248a1/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0195ac56a9b248a1/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0195ac56a9b248a1/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-insufficient-memory\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T08:00:52Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-insufficient-memory, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nvolumes:\n- {\"name\": \"kube-api-access-c69j6\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0195ac56a9b248a1/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0195ac56a9b248a1/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0195ac56a9b248a1/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"requests\\\": {\\n    \\\"cpu\\\": \\\"50m\\\",\\n    \\\"memory\\\": \\\"100000Gi\\\"\\n  }\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0195ac56a9b248a1/tools/004-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0195ac56a9b248a1/tools/004-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0195ac56a9b248a1/tools/004-evidence-run_bash_command.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"execute_prometheus_instant_query 执行成功但结果为空；这表示查询未命中数据，不能视为已采集到指标值。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/0195ac56a9b248a1/tools/005-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0195ac56a9b248a1/tools/005-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0195ac56a9b248a1/tools/005-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"master: 32860484Ki = 31 Gi\\nnode1: 32860476Ki = 31 Gi\\nnode2: 32860480Ki = 31 Gi\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0195ac56a9b248a1/tools/006-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0195ac56a9b248a1/tools/006-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0195ac56a9b248a1/tools/006-evidence-run_bash_command.summary.txt"}],"llm_analysis":"## 证据采集结论\n\n### ✅ 已采集证据\n\n| 证据维度 | 结果 |\n|---------|------|\n| **Pod 当前状态**（e1 - describe） | **Pending**，`node: <none>`，最新 FailedScheduling 事件在 **26s 前**（仍在持续重试） |\n| **FailedScheduling 事件原文**（e1） | **`0/3 nodes are available: 3 Insufficient memory`** + `3 No preemption victims found` |\n| **Pod 内存请求量**（e2 - YAML + json） | **`resources.requests.memory = 100000Gi`**（十万 Gi！） |\n| **Pod QoS**（e1） | **Burstable**（有 requests 但没 limits） |\n| **Pod 其他调度约束**（e1/e2） | 无 nodeSelector、无 affinity、无 taint/toleration 冲突、无 PVC 依赖 |\n| **节点容量**（e3 - nodes json） | 3 个节点各自 **capacity ≈ 31Gi**，**allocatable ≈ 31Gi** |\n| **节点状态**（e3） | 全部 **Ready=True**，**MemoryPressure=False**，节点本身无异常 |\n| **Prometheus 内存指标**（e4） | 查询命中为空（Prometheus 可能未就绪），但节点容量数据已充分说明问题 |\n\n### 🔍 根因定位\n**Pod `rc-pending-insufficient-memory` 设置了 `resources.requests.memory = 100000Gi`**（十万 Gi），而集群每个节点仅有约 **31Gi** 可分配内存。调度器评估所有 3 个节点后，没有任何节点能提供 100000Gi 内存，因此 `0/3 nodes are available: 3 Insufficient memory`。Pod 本身 QoS 为 Burstable、无额外调度约束，根因**明确为 Pod 内存请求量严重超出集群容量**，属于配置错误。\n\n### ❌ 未采集证据 / 冲突\n- **Prometheus 内存使用率查询**（e4）：返回空结果，Prometheus 指标可能未部署或未就绪，不作为根因判断依据——节点容量对比已足够确定问题。\n- **集群节点本身无异常**：所有节点 Ready、无 MemoryPressure，因此问题不在节点层面，而在 Pod 自身的资源请求配置。","collection_summary":"计划 4 项，实际采集 3 项，未采集 1 项，完整度 75%；其中真实环境证据 5/6 项，完整度 83%；实际执行工具 7 个，匹配计划 3 个，未规划证据 4 个","plan_total":4,"plan_collected":3,"plan_completeness":0.75,"environment_evidence_total":6,"environment_evidence_collected":5,"environment_evidence_completeness":0.8333333333333334,"executed_tool_count":7,"matched_tool_count":3,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证 Pod rc-pending-insufficient-memory 的当前状态和 FailedScheduling 事件","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-memory -n aiops-e2e","purpose":"验证 Pod 当前是否仍处于 Pending 状态，并获取 FailedScheduling 事件原文确认资源不足原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"获取 Pod YAML 检查 resources.requests 内存配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-memory -n aiops-e2e -o yaml","purpose":"检查 Pod 的内存请求量（resources.requests.memory），判断是否请求了较大内存","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"查看集群所有 Node 的内存容量和 allocatable 资源","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, capacity: .status.capacity.memory, allocatable: .status.allocatable.memory, conditions: [.status.conditions[] | select(.type==\"MemoryPressure\" or .type==\"Ready\") | {type: .type, status: .status}]}'","purpose":"验证集群各节点的内存容量和可分配内存，确认是否有节点内存不足或处于 MemoryPressure 状态","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"通过 Prometheus 查询集群节点的内存使用率","level":"critical","tool":"execute_prometheus_instant_query","command":"sum by (node) (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100","purpose":"获取所有节点的实时内存使用率，验证是否确实存在节点内存不足","collected":false,"source":"planned","outcome":"unknown"},{"id":"e5","description":"Fetch 已确认的 runbook 作为参考","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","purpose":"获取 PendingUnschedulable 运行手册作为诊断参考","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":["e4(通过 Prometheus 查询集群节点的内存使用率): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/4 项, 完整度: 83%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证 Pod rc-pending-insufficient-memory 的当前状态和 ... | `kubectl describe pod rc-pending-insufficient-memory -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_yaml | 获取 Pod YAML 检查 resources.requests 内存配置 | `kubectl get pod rc-pending-insufficient-memory -n aiops-e2e -o yaml` |
   | e3 | critical | ✅ | run_bash_command | 查看集群所有 Node 的内存容量和 allocatable 资源 | `kubectl get nodes -o json | jq '.items[] | {name: .metadata.name, capacity: ....` |
   | e4 | critical | ❌ | execute_prometheus_instan... | 通过 Prometheus 查询集群节点的内存使用率 | `sum by (node) (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) /...` |
   | e5 | reference | ❌ | fetch_runbook | Fetch 已确认的 runbook 作为参考 | `fetch_runbook pod-pending-unschedulable.md` |

   ⚠️ 未采集原因:
   - e4(通过 Prometheus 查询集群节点的内存使用率): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (24.4s)
   📤 → 下游数据: root_cause=Pod `rc-pending-insufficient-memory`（aiops-e2e 命名空间）当前 Pending，异常类型 PendingUnschedulable。YAML 确认其 `resources.requests.memory = 100000Gi`（证据e2），而集群3个节点（master/node1/node2）各自 allocatable 仅约31Gi（evidence e3：32758084Ki/32758076Ki/32758080Ki）。调度器判定 `0/3 nodes are available: 3 Insufficient memory`，抢占也无受害者（evidence e1：最新事件26s前）。Pod 无 nodeSelector/affinity/PVC 等额外调度约束，QoS Burstable（evidence e1/e2），故障纯由 Pod 自身内存请求配置错误导致。
   confidence=98%
   causal_chain={"root_cause": "Pod rc-pending-insufficient-memory 的 resources.requests.memory 被错误配置为 100000Gi（约十万Gi），而集群3个节点每个仅约31Gi可分配内存，Pod请求量超过集群总容量3个数量级", "propagation": "Pod创建后进入调度队列 → scheduler遍历所有3个节点（master/node1/node2）→ 每个节点评估均发现可用内存（约31Gi）远小于Pod请求（100000Gi）→ 所有节点标记为Insufficient memory → 尝试抢占（preemption），但因没有任何运行中Pod能释放100000Gi内存，找不到受害者 → 调度失败，Pod持续Pending", "direct_cause": "调度器在全部3个节点上均遇到 Insufficient memory，无法满足 Pod 100000Gi 的内存请求", "manifestation": "Pod rc-pending-insufficient-memory 在 aiops-e2e 命名空间持续 Pending，Events 显示 0/3 nodes are available: 3 Insufficient memory，抢占无受害者"}
   rca_analysis={"phenomenon": "集群 aiops-e2e 命名空间中 Pod `rc-pending-insufficient-memory` 当前处于 Pending 状态，异常类型为 PendingUnschedulable。Events 持续显示：0/3 nodes are available: 3 Insufficient memory，且抢占无受害者。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod rc-pending-insufficient-memory 当前状态 Pending，node: <none>，Warning FailedScheduling 0/3 nodes: 3 Insufficient memory，最新事件 26s 前", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml", "content": "Pod YAML 显示 resources.requests.memory = 100000Gi，无 nodeSelector/affinity/PVC，QoS Burstable", "reliability": "高"}, {"id": "e3", "source": "run_bash_command (node resources)", "content": "3个节点容量均为约31Gi，allocatable约31Gi，全部Ready=True，MemoryPressure=False", "reliability": "高"}, {"id": "e4", "source": "execute_prometheus_instant_query", "content": "Prometheus 内存指标查询返回空结果，无法获取节点实际内存使用率", "reliability": "低"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedScheduling 26s (x2 over 5m26s) default-scheduler 0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.", "interpretation": "调度器在最近26秒仍在尝试调度Pod，但3个节点全部报告内存不足，且没有可抢占的受害者Pod——说明没有任何节点能满足该Pod的内存请求量。"}, {"evidence_id": "e2", "raw_data": "resources.requests.memory = 100000Gi", "interpretation": "Pod 请求了100000Gi内存，远超集群中任何一个节点的容量（约31Gi）。这是调度的根本障碍。无其他调度约束（nodeSelector/affinity/taint不匹配等），排除了其他调度场景。"}, {"evidence_id": "e3", "raw_data": "master: capacity=32860484Ki(≈31Gi) allocatable=32758084Ki; node1: capacity=32860476Ki(≈31Gi); node2: capacity=32860480Ki(≈31Gi); 全部Ready=True MemoryPressure=False", "interpretation": "集群3个节点各自仅有约31Gi可分配内存，所有节点健康正常。即使节点上没有任何Pod运行，最空闲的节点也只能提供31Gi，远不及Pod请求的100000Gi。"}, {"evidence_id": "e4", "raw_data": "execute_prometheus_instant_query 返回空结果", "interpretation": "Prometheus 查询未命中数据，无法获取实际内存使用率。但节点容量与Pod请求量的直接对比已足够确定根因，无需依赖此数据。"}], "causal_chain": {"root_cause": "Pod rc-pending-insufficient-memory 的 resources.requests.memory 被错误配置为 100000Gi（约十万Gi），而集群3个节点每个仅约31Gi可分配内存，Pod请求量超过集群总容量3个数量级", "propagation": "Pod创建后进入调度队列 → scheduler遍历所有3个节点（master/node1/node2）→ 每个节点评估均发现可用内存（约31Gi）远小于Pod请求（100000Gi）→ 所有节点标记为Insufficient memory → 尝试抢占（preemption），但因没有任何运行中Pod能释放100000Gi内存，找不到受害者 → 调度失败，Pod持续Pending", "direct_cause": "调度器在全部3个节点上均遇到 Insufficient memory，无法满足 Pod 100000Gi 的内存请求", "manifestation": "Pod rc-pending-insufficient-memory 在 aiops-e2e 命名空间持续 Pending，Events 显示 0/3 nodes are available: 3 Insufficient memory，抢占无受害者"}, "root_cause": "Pod `rc-pending-insufficient-memory`（aiops-e2e 命名空间）当前 Pending，异常类型 PendingUnschedulable。YAML 确认其 `resources.requests.memory = 100000Gi`（证据e2），而集群3个节点（master/node1/node2）各自 allocatable 仅约31Gi（evidence e3：32758084Ki/32758076Ki/32758080Ki）。调度器判定 `0/3 nodes are available: 3 Insufficient memory`，抢占也无受害者（evidence e1：最新事件26s前）。Pod 无 nodeSelector/affinity/PVC 等额外调度约束，QoS Burstable（evidence e1/e2），故障纯由 Pod 自身内存请求配置错误导致。", "root_cause_summary": "Pod `rc-pending-insufficient-memory`（aiops-e2e 命名空间）当前 Pending，异常类型 PendingUnschedulable。YAML 确认其 `resources.requests.memory = 100000Gi`（证据e2），而集群3个节点（master/node1/node2）各自 allocatable 仅约31Gi（evidence e3：32758084Ki/32758076Ki/32758080Ki）。调度器判定 `0/3 nodes are available: 3 Insufficient memory`，抢占也无受害者（evidence e1：最新事件26s前）。Pod 无 nodeSelector/affinity/PVC 等额外调度约束，QoS Burstable（evidence e1/e2），故障纯由 Pod 自身内存请求配置错误导致。", "confidence": 0.98, "confidence_reason": "有直接证据（e2 YAML 确认 requests.memory=100000Gi）、节点容量证据（e3 确认每个节点仅31Gi）、调度事件证据（e1 确认 FailedScheduling Insufficient memory），因果链完整清晰，无冲突证据。Prometheus 数据未采集（e4）但不影响判断，因节点容量对比已足够。置信度0.98。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "节点内存实际被其他Pod占满（节点MemoryPressure）", "probability": "low", "reason": "节点条件显示 MemoryPressure=False（证据e3），且即使节点完全空闲（0使用率），31Gi也远不够100000Gi，所以此场景即使存在也不影响根因"}, {"cause": "nodeSelector/affinity/taint 不匹配导致无可用节点", "probability": "low", "reason": "Pod YAML 明确显示 Node-Selectors: <none>，无affinity配置，仅有默认toleration（证据e1/e2），排除了调度约束类场景"}, {"cause": "PVC 未绑定导致 Pod 挂起", "probability": "low", "reason": "Pod 无 PVC 依赖，仅有默认 kube-api-access-c69j6 投射卷（证据e2），排除了存储前置条件场景"}], "limitations": "Prometheus 内存使用率指标查询为空（证据e4），未能获取节点实际内存使用情况；但节点容量与Pod请求量之间的巨大差距（31Gi vs 100000Gi）已足够独立确认根因，不影响结论。", "llm_raw_analysis": "## 证据清点\n共采集7条证据，其中关键证据3条（e1/e2/e3），辅助证据1条（e4），上游已验证证据2条（layer_1/layer_2）。\n\n## 逐条分析\n- **e1（kubectl_describe）**：Pod仍在Pending，最新FailedScheduling事件26s前，3节点全部Insufficient memory，无抢占受害者。无nodeSelector/affinity/taint问题。\n- **e2（kubectl_get_yaml）**：关键发现——resources.requests.memory=100000Gi。无PVC依赖，无其他调度约束。\n- **e3（节点资源）**：3节点各自capacity≈31Gi，allocatable≈31Gi，全部Ready且无MemoryPressure。\n- **e4（Prometheus）**：查询为空，不可用，但不影响判断。\n\n## 关联分析\ne2（请求100000Gi）与e3（节点31Gi）对比：100000Gi >> 31Gi，即使所有节点内存空着也无法调度。e1确认调度器实际的失败原因正是\"Ins\n... 截断，原始 691 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod `rc-pending-insufficient-memory`（aiops-e2e 命名空间）当前 Pending，异常类型 PendingUnschedulable。YAML 确认其 `resources.requests.memory = 100000Gi`（证据e2），而集群3个节点...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod rc-pending-insufficient-memory 的 resources.requests.memory 被错误配置为 100000Gi（约十万Gi），而集群3个节点每个仅约31Gi可分配内存，Pod请求量超过集群总容量3个数量级
     传导机制: Pod创建后进入调度队列 → scheduler遍历所有3个节点（master/node1/node2）→ 每个节点评估均发现可用内存（约31Gi）远小于Pod请求（100000Gi）→ 所有节点标记为Insufficient memory → 尝试抢占（preemption），但因没有任何运行中Pod能释放100000Gi内存，找不到受害者 → 调度失败，Pod持续Pending
     最终表现: Pod rc-pending-insufficient-memory 在 aiops-e2e 命名空间持续 Pending，Events 显示 0/3 nodes are available: 3 Insufficient memory，抢占无受害者


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (27.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5627 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 44.9s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将根据您提供的诊断上下文，为您呈现一份详尽、完整的诊断报告。

---

## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **集群核心问题** | 集群中 `aiops-e2e` 命名空间下的 Pod `rc-pending-insufficient-memory` 因配置了**极高的内存请求（100000Gi）**，导致无法在任何节点上调度，处于永久 `Pending` 状态。 |
| **Pod异常状态** | Pending |
| **兼容归因层** | L1 - 调度/节点资源不足 |
| **问题分类** | PendingUnschedulable (Insufficient memory) |
| **置信度** | 高 (95%) |
| **证据完整度** | 3/4 (75%) |

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 异常 Pod | `rc-pending-insufficient-memory` |
| 命名空间 | `aiops-e2e` |
| 当前状态 | Pending (未分配到任何节点) |
| 核心错误信息 (Events) | `0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` |

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| e1 | Pod 调度事件 | `kubectl describe pod rc-pending-insufficient-memory -n aiops-e2e` | `Warning FailedScheduling ... 0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` | 调度器明确报告所有节点内存不足，且无法通过抢占现有Pod来释放资源。 |
| e2 | Pod 资源配置 | `kubectl get pod rc-pending-insufficient-memory -n aiops-e2e -o yaml` | `resources.requests.memory: 100000Gi` | Pod 请求的内存资源为惊人的 **100,000 GiB**，这是一个不合理的配置。 |
| e3 | 节点资源容量 | `run_bash_command` (查询节点资源) | `master: 32860484Ki ≈ 31 Gi`<br>`node1: 32860476Ki ≈ 31 Gi`<br>`node2: 32860480Ki ≈ 31 Gi` | 集群中三个节点各自的**可用内存 (Allocatable) 约为 31 GiB**。 |

### 证据关联分析
- **证据 e2 + e3 印证**：Pod 请求的内存（`100000Gi`）是单个节点可用内存（约`31Gi`）的 **3200 倍以上**，甚至远超整个集群（约`93Gi`）的总可用内存。
- **证据 e1 + e2 + e3 印证**：由于 Pod 的请求量在物理上无法被满足，调度器在所有节点上均判定为 `Insufficient memory`，且由于没有单个Pod能释放`100000Gi`的内存，抢占也自然失败，导致 Pod 永久 Pending。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 节点实时内存使用率 (Prometheus) | low | 即使节点内存使用率为 0%，也无法满足 100000Gi 的请求，对该问题的根因判断无影响。 |

## 🎯 根因分析
### 因果链
```
┌──────────────────────────────────────────────────────────────┐
│ 根本原因                                                      │
│ Pod `rc-pending-insufficient-memory` 的 YAML 配置错误，       │
│ 其 `resources.requests.memory` 被设置为 100000Gi。            │
│ (证据e2: resources.requests.memory: 100000Gi)                 │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 传导机制                                                      │
│ Pod创建后，kube-scheduler 尝试为其分配节点。它遍历所有3个节点  │
│ (证据e3: 每节点约31Gi可分配内存)，但发现没有任何节点能满足    │
│ 100000Gi 的请求，因此判定所有节点不满足。                       │
│ (证据e1: 0/3 nodes are available: 3 Insufficient memory)      │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 直接原因                                                      │
│ 所有节点报告 `Insufficient memory`，调度器无法找到可用节点。   │
│ 尝试抢占也失败 (No preemption victims found)。                  │
│ (证据e1)                                                      │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                  │
│ Pod `rc-pending-insufficient-memory` 持续处于 Pending 状态。  │
└──────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 e2 (Pod YAML 显示内存请求为 `100000Gi`) 和证据 e3 (节点最大可用内存约 `31Gi`)，问题的**根本原因是人为配置错误**。Pod 的 `resources.requests.memory` 值被错误地设置为一个极不合理的巨大数值（100000Gi），远超集群所有节点总和的可用内存，导致调度器永远无法为其分配节点。

**置信度**：高 (98%)
- ✅ 证据 e1 的调度失败事件直接指向 `Insufficient memory`
- ✅ 证据 e2 的原始 YAML 直接暴露了异常数值 `100000Gi`
- ✅ 证据 e3 证明了节点容量与 Pod 请求之间不成比例的差距
- ⚠️ 缺失的 Prometheus 数据（证据e4）不影响根本结论的得出。

**被排除的错误归因**：
- ❌ **节点资源不足**：不是根因。节点确实有其容量限制，但问题核心在于 Pod 自身请求了一个不可能的数字，而不是节点上运行了太多Pod。
- ❌ **Finalizer 未清理**：已明确排除，YAML显示 `finalizers: <none>`。
- ❌ **Taint/NodeSelector/Affinity 不匹配**：被排除，Pod 无额外调度约束。

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [必须] 删除或修正错误 Pod**
由于该 Pod 从未被调度成功，它只是一个阻塞无用的“鬼影”对象。最直接的修复方式就是删除它。
```bash
kubectl delete pod rc-pending-insufficient-memory -n aiops-e2e
```
*依据*：此 Pod 配置错误，没有保留价值。
*替代方案*：如果这是一个 Deployment/StatefulSet 创建的，请修正对应的 YAML 或 Helm Values。

**2. [如果无法删除，应急修复] 覆盖修正错误的资源请求 (通常不推荐)**
在极少数必须保留 Pod 的情况下，可以尝试对其资源请求进行原地更新（如果 Pod 不在运行的控制器下）。
```bash
kubectl patch pod rc-pending-insufficient-memory -n aiops-e2e -p '{"spec":{"containers":[{"name":"rc-pending-insufficient-memory","resources":{"requests":{"memory":"1Gi"}}}]}]}}'
```
*注意*：此命令可能不生效，因为 Pod 一旦 `Pending` 且被调度器评估过，其 `requests` 通常不允许修改。最可靠的方法还是删除重建。

### 后续优化
1. **引入资源配额 (ResourceQuota)**：在 `aiops-e2e` 命名空间设置 `ResourceQuota`，限制单个 Pod 或整个命名空间能请求的最大资源量，防止类似的“手误”再次发生。
2. **CI/CD 流水线检查**：在应用部署的 CI/CD 流程中，加入对资源请求值的**合理性校验**，例如，如果 `resources.requests.memory` 大于某个阈值（如 100Gi），则自动预警或阻止部署。
3. **使用准入控制器 (Admission Webhook)**：更高级的方案是部署一个准入控制器（如 OPA/Gatekeeper），根据策略自动拒绝或修正这类明显错误的资源配置。

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 删除异常 Pod | `kubectl delete pod rc-pending-insufficient-memory -n aiops-e2e` | `pod "rc-pending-insufficient-memory" deleted` |
| 2. 确认异常 Pod 消失 | `kubectl get pod -n aiops-e2e \| grep rc-pending-insufficient-memory` | 无输出结果 |
| 3. 检查集群整体 Pod 状态 | `kubectl get pods --all-namespaces \| grep -v Running \| grep -v Completed` | 如果该 Pod 是唯一的异常对象，则其他所有 Pod 均为 Running 或 Completed 状态。 |

## ⚠️ 注意事项
- **问题的根本原因是配置错误，而非基础设施故障。** 集群本身是健康的，65个Pod中有59个正常运行。
- 修复时，请务必确认 `rc-pending-insufficient-memory` 这个 Pod 是否为某个上层工作负载（如 Deployment, Job）创建的子对象。如果是，直接删除 Pod 后，控制器会尝试重建一个新的 Pod，该 Pod 会因同样的配置错误再次 Pending。这种情况下，必须修改上层工作负载的 YAML 配置。
- 集群中的其他 59 个 Running Pod 目前正常工作，此问题对集群稳定性没有影响。

---

## 📊 性能统计

├─ 总耗时: 1.7m
├─ 问题定位: 23.0s (22%) ✅
├─ 证据链采集: 29.8s (28%) ✅
├─ 根因分析: 24.4s (23%) ✅
├─ 汇总总结: 27.6s (26%) ✅
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
