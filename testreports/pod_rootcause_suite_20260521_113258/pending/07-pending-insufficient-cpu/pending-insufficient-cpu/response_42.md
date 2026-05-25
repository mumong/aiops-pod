======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: ad91b10e1ea24a61]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先全面扫描集群中的所有 Pod，看看当前有哪些异常状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 发现了一个异常 Pod。让我查看它的详细信息以及集群中的其他资源情况。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  51m                default-scheduler  0/3 nodes are availab
   💭 [问题定位] 清晰了！让我再看看集群节点的资源情况，确认整体状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 所有节点都 Ready，现在获取与该异常类型匹配的 runbook。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在我已掌握全部信息，可以做出完整的定位分析了。

---

## 📋 异常定位分析报告

### 整体健康概览

| 指标 | 数值 |
|------|------|
| 总 Pod 数 | **65** |
| 正常运行 Pod | **59 (Running)** |
| 异常 Pod | **1 (Pending)** |
| 集群节点 | **3 台，全部 Ready** |

### 发现的问题

集群中存在 **1 个异常 Pod**，位于 `aiops-e2e` 命名空间：

| Pod 名称 | 状态 | 所属命名空间 |
|----------|------|-------------|
| `rc-pending-insufficient-cpu` | **Pending** | aiops-e2e |

### 详细分析

| 字段 | 值 |
|------|-----|
| **Status** | `Pending` |
| **Node** | 未绑定（`<none>`） |
| **QoS Class** | Burstable |
| **Events** | `FailedScheduling` — `0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` |

**根因**：该 Pod 请求的 CPU 资源超过了所有 3 个节点的可分配余量，调度器无法找到可放置的节点，且没有更低优先级的 Pod 可以被抢占（preemption victims not found）。

### 输出结构化结果

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **derived_layer** | L1 |
| **layers** | ["L1"] |
| **layer_name** | 调度资源不足 |
| **confidence** | 高 |
| **pod_status_keyword** | Pending |
| **pod_abnormal_type** | PendingUnschedulable |
| **status_category** | scheduling |
| **abnormal_pods** | [`aiops-e2e/rc-pending-insufficient-cpu`] |
| **abnormal_groups** | PendingUnschedulable |
| **key_entities** | Pod: `rc-pending-insufficient-cpu`, 节点: master/node1/node2（全部 Ready 但 CPU 余量不足） |
| **possible_scenarios** | (1) Pod requests 的 CPU 值过高，超出集群所有节点剩余可分配量；(2) 集群整体 CPU 分配率已接近饱和；(3) 该 Pod 可能未被设置合理的 priorityClass，导致无法抢占低优先级的 Pod |

### 🔍 后续审查方向（交 evidence 节点）

1. 检查该 Pod 的 `resources.requests.cpu` 具体值
2. 检查各节点的 `Allocatable cpu` 与 `Requests` 使用量，确认剩余量
3. 检查是否有其他高优 Pod 占用了大量 CPU 资源
4. 考虑是否需要为测试/调试类 Pod 降低 CPU request 或配置 priorityClass
   ✅ [问题定位] 完成 (23.5s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': 'Pod requests 的 CPU 值过高，超出集群所有节点剩余可分配量', 'probability': '高', 'reason': 'FailedScheduling 明确提示 3 Insufficient cpu，且 3 个节点均 Ready'}, {'scenario': '集群整体 CPU 分配率已接近饱和', 'probability': '中', 'reason': '3个节点全部CPU不足，说明集群CPU资源整体紧张'}, {'scenario': '该 Pod 未设置合理的 priorityClass，无法抢占低优先级 Pod', 'probability': '中', 'reason': 'preemption 提示 No preemption victims found'}]
   entities=[{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}]
   reasoning=集群中存在1个Pending状态的异常Pod rc-pending-insufficient-cpu (aiops-e2e命名空间)，Events显示FailedScheduling，根因为3个节点CPU均不足（3 Insufficient cpu），且无抢占受害者。3个节点全部Ready，排除节点本身异常。根据五层模型，PendingUnschedulable归因于调度/scheduling，属于L1层。pod_status_keyword为Pending，pod_abnormal_type为PendingUnschedulable，status_category为scheduling。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "调度资源不足", "confidence": 0.95, "reasoning": "集群中存在1个Pending状态的异常Pod rc-pending-insufficient-cpu (aiops-e2e命名空间)，Events显示FailedScheduling，根因为3个节点CPU均不足（3 Insufficient cpu），且无抢占受害者。3个节点全部Ready，排除节点本身异常。根据五层模型，PendingUnschedulable归因于调度/scheduling，属于L1层。pod_status_keyword为Pending，pod_abnormal_type为PendingUnschedulable，status_category为scheduling。", "abnormal_pods": [{"name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}, {"type": "Node", "name": "master", "namespace": ""}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Node", "name": "node2", "namespace": ""}], "possible_scenarios": [{"scenario": "Pod requests 的 CPU 值过高，超出集群所有节点剩余可分配量", "probability": "高", "reason": "FailedScheduling 明确提示 3 Insufficient cpu，且 3 个节点均 Ready"}, {"scenario": "集群整体 CPU 分配率已接近饱和", "probability": "中", "reason": "3个节点全部CPU不足，说明集群CPU资源整体紧张"}, {"scenario": "该 Pod 未设置合理的 priorityClass，无法抢占低优先级 Pod", "probability": "中", "reason": "preemption 提示 No preemption victims found"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-insufficient-cpu                         0/1     Pending     0              51m     <none>           <none>   <none>           <none>            app=rc-pending-insufficient-cpu,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，直接执行既有 evidence_plan，开始采证。先并行执行关键的几个工具。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
52m                 Warning   FailedScheduling   Pod/rc-pending-insufficient-cpu   0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No pree
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  52m                default-scheduler  0/3 nodes are availab
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:59:10Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizer
   💭 [证据链采集] 关键的 Pod 描述和 YAML 已经获取到。describe 和 YAML 中没有显示 resource requests 的具体数值，让我用更精确的方式获取容器资源请求，同时检查节点资源情况。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "null\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"requests\": {\n    \"cpu\": \"100k\",\n    \"memory\": \"64Mi\"\n  }\n}\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"name\": \"master\",\n  \"allocatable\": {\n    \"cpu\": \"12\",\n    \"ephemeral-storage\": \"568259694471\",\n    \"hugepages-1Gi\": \"0\",\n    \"hugepages-2Mi\":
   💭 [证据链采集] 发现一个关键线索！Pod 的 resource requests 中 `cpu: "100k"` — 这不是标准的 CPU 单位（"100k" 不等于 100个核心 或 100m），让我验证一下这个值的实际含义，并检查集群已分配的 CPU 总量。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"cpu\": \"100k\",\n  \"memory\": \"64Mi\"\n}\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"node":"node2"},"value":[1779349894.926,"1.7750000000000001"]},{"metric":{"node":"master"},"value":[1779349894.926,"5.61"]},{"met
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"__name__":"kube_node_status_allocatable","container":"kube-state-metrics","endpoint":"http","instance":"172.16.219.98:8080","job
   💭 [证据链采集] Prometheus 数据非常关键！有一个高值 `100000` 核心出现在 CPU request 总和中。让我进一步确认这个"100k"的实际含义——在 Kubernetes 中，`100k` 会被解析为 `100000` 个 CPU 单位（100000 个核心），这远远超出了单个节点的 12 核容量。
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"name\": \"rc-pending-insufficient-cpu\",\n  \"requests\": {\n    \"cpu\": \"100k\",\n    \"memory\": \"64Mi\"\n  },\n  \"imagePullPolicy\": \"Never\"\n}\n", "stderr
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{"__name__":"kube_pod_container_resource_requests","container":"app","endpoint":"http","instance":"172.16.219.98:8080","job":"kube
   💭 [证据链采集] 现在一切清晰了。让我再查一下节点实际的已分配 CPU 情况，完整确认。
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{},"value":[1779349904.832,"5.61"]}]}}
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{},"value":[1779349905.151,"1.7750000000000001"]}]}}
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{},"value":[1779349905.327,"0.85"]}]}}
   💭 [证据链采集] 好，所有关键证据已采集完毕。总结一下：

---

## 证据采集结论

### ✅ 已采集证据

**1. Pod 当前状态与 FailedScheduling 事件（critical - kubectl_describe）**
- Pod `rc-pending-insufficient-cpu`（aiops-e2e 命名空间）状态：**Pending**，未绑定节点
- **FailedScheduling 事件原文**：`0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.`
- 事件时效性：最早 52m 前，最近 22m 前（共 7 次），为 **持续活跃故障**

**2. Pod YAML 配置（critical - kubectl_get_yaml）**
- `resources.requests.cpu = "100k"` — **这是 100000 个 CPU 核心请求**，不是一个正常的 core 值
- `priorityClassName: null`（未设置优先级类）
- 无 nodeSelector/affinity 约束
- `imagePullPolicy: Never` — 镜像拉取策略为 Never

**3. Prometheus 验证 CPU 请求量（important）**
- Pod `rc-pending-insufficient-cpu` 请求的 CPU = **100,000 核**（Prometheus kube_pod_container_resource_requests 直接记录为 100000 unit=core）
- 3 个节点 allocatable CPU 各为 **12 核**，总计 **36 核**
- 当前已分配（不含此Pod）：master=5.61, node1=0.85, node2=1.775，合计约 **8.24 核**，远低于 36 核可分配容量

**4. 节点资源（important - kubectl + Prometheus）**
- 3 个节点全部 **Ready**（排除了节点异常）
- 集群可分配 CPU = 12+12+12 = **36 核**
- 集群已分配（不含异常 Pod）≈ **8.24 核**，剩余充裕（约 27 核可用）

### 🔍 根因定位
**根本原因**：Pod 的 `resources.requests.cpu` 配置为 `"100k"`，被 Kubernetes 解析为 **100,000 个 CPU 核心**，远超集群所有节点合计的 36 核可分配容量，导致调度器在 3 个节点上都报 `Insufficient cpu`。这是一个**配置错误**（type 写成了 `k` 而非 `m`，实际意图应为 `100m` 即 0.1 核），而非集群资源真正不足。

**辅助原因**：`priorityClassName: null` 且 `imagePullPolicy: Never`（意味着镜像必须已被拉取，否则无法启动）。

### ❌ 冲突/负向证据
- 无冲突证据，所有工具调用结果与上游信号一致并得到验证。
   ✅ [证据链采集] 完成 (43.1s)
   📤 → 下游数据: evidence_items=7/8
   evidence_analysis={"evidence_plan":[{"id":"ev1-critical-pod-describe","description":"Describe the pending pod rc-pending-insufficient-cpu to verify current status, events, and scheduling failures","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e"},"purpose":"验证 Pod 当前状态、FailedScheduling 事件原文、Pod spec 中的 resource requests、priorityClass、nodeSelector/affinity/tolerations 等调度相关配置","evidence_type":"real_time_state_and_events","target_scope":"abnormal_pods[0]","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev2-critical-pod-yaml","description":"Get the full YAML of the pending pod to examine resource requests, priorityClass, and scheduling constraints","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e"},"purpose":"检查 Pod spec.containers[].resources.requests.cpu 具体数值、priorityClassName、nodeSelector、affinity、tolerations 等调度配置","evidence_type":"spec_and_config","target_scope":"abnormal_pods[0]","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"ev3-important-node-resources","description":"Check allocatable and allocatable CPU on all 3 nodes to confirm insufficient cpu across the cluster","level":"important","tool":"run_bash_command","command":"kubectl get nodes -o json | jq -r '.items[] | {name: .metadata.name, allocatable: .status.allocatable, capacity: .status.capacity}'","tool_args":{},"purpose":"获取所有节点的 allocatable CPU 和 total CPU，验证集群 CPU 分配率是否已饱和，确认 3 Insufficient cpu 的根因","evidence_type":"cluster_capacity","target_scope":"active_entities[1,2,3]","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev4-important-events","description":"Check recent events in the aiops-e2e namespace for scheduling-related warnings","level":"important","tool":"kubectl_events","command":"kubectl events -n aiops-e2e --for pod/rc-pending-insufficient-cpu","tool_args":{"namespace":"aiops-e2e","for_kind":"Pod","for_name":"rc-pending-insufficient-cpu"},"purpose":"确认 FailedScheduling 事件的时效性和具体原文，验证 3 Insufficient cpu 和 No preemption victims found 的真实性","evidence_type":"events","target_scope":"abnormal_pods[0]","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev5-reference-runbook","description":"Fetch the runbook for Pod PendingUnschedulable to use as reference","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","tool_args":{"runbook":"pod-pending-unschedulable.md"},"purpose":"获取 PendingUnschedulable runbook 作为诊断参考","evidence_type":"reference","target_scope":"runbook","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n52m                 Warning   FailedScheduling   Pod/rc-pending-insufficient-cpu   0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n22m (x6 over 47m)   Warning   FailedScheduling   Pod/rc-pending-insufficient-cpu   0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/001-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/001-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/001-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  52m                default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  22m (x6 over 47m)  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nName:             rc-pending-insufficient-cpu\nLabels:           app=rc-pending-insufficient-cpu\nPod 关键区块:\nQoS Class: Burstable\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-26zhx:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  52m                default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  22m (x6 over 47m)  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:59:10Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-insufficient-cpu, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nvolumes:\n- {\"name\": \"kube-api-access-26zhx\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"null\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/004-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/004-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/004-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"requests\\\": {\\n    \\\"cpu\\\": \\\"100k\\\",\\n    \\\"memory\\\": \\\"64Mi\\\"\\n  }\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/005-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/005-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/005-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"name\\\": \\\"master\\\",\\n  \\\"allocatable\\\": {\\n    \\\"cpu\\\": \\\"12\\\",\\n    \\\"ephemeral-storage\\\": \\\"568259694471\\\",\\n    \\\"hugepages-1Gi\\\": \\\"0\\\",\\n    \\\"hugepages-2Mi\\\": \\\"0\\\",\\n    \\\"memory\\\": \\\"32758084Ki\\\",\\n    \\\"pods\\\": \\\"110\\\"\\n  },\\n  \\\"capacity\\\": {\\n    \\\"cpu\\\": \\\"12\\\",\\n    \\\"ephemeral-storage\\\": \\\"616601232Ki\\\",\\n    \\\"hugepages-1Gi\\\": \\\"0\\\",\\n    \\\"hugepages-2Mi\\\": \\\"0\\\",\\n    \\\"memory\\\": \\\"32860484Ki\\\",\\n    \\\"pods\\\": \\\"110\\\"\\n  }\\n}\\n{\\n  \\\"name\\\": \\\"node1\\\",\\n  \\\"allocatable\\\": {\\n    \\\"cpu\\\": \\\"12\\\",\\n    \\\"ephemeral-storage\\\": \\\"187795058378\\\",\\n    \\\"hugepages-1Gi\\\": \\\"0\\\",\\n    \\\"hugepages-2Mi\\\": \\\"0\\\",\\n    \\\"memory\\\": \\\"32758076Ki\\\",\\n    \\\"pods\\\": \\\"110\\\"\\n  },\\n  \\\"capacity\\\": {\\n    \\\"cpu\\\": \\\"12\\\",\\n    \\\"ephemeral-storage\\\": \\\"203770680Ki\\\",\\n    \\\"hugepages-1Gi\\\": \\\"0\\\",\\n    \\\"hugepages-2Mi\\\": \\\"0\\\",\\n    \\\"memory\\\": \\\"32860476Ki\\\",\\n    \\\"pods\\\": \\\"110\\\"\\n  }\\n}\\n{\\n  \\\"name\\\": \\\"node2\\\",\\n  \\\"allocatable\\\": {\\n    \\\"cpu\\\": \\\"12\\\",\\n    \\\"ephemeral-storage\\\": \\\"187795058378\\\",\\n    \\\"hugepages-1Gi\\\": \\\"0\\\",\\n    \\\"hugepages-2Mi\\\": \\\"0\\\",\\n    \\\"memory\\\": \\\"32758080Ki\\\",\\n    \\\"pods\\\": \\\"110\\\"\\n  },\\n  \\\"capacity\\\": {\\n    \\\"cpu\\\": \\\"12\\\",\\n    \\\"ephemeral-storage\\\": \\\"203770680Ki\\\",\\n    \\\"hugepages-1Gi\\\": \\\"0\\\",\\n    \\\"hugepages-2Mi\\\": \\\"0\\\",\\n    \\\"memory\\\": \\\"32860480Ki\\\",\\n    \\\"pods\\\": \\\"110\\\"\\n  }\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/006-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/006-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/006-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"cpu\\\": \\\"100k\\\",\\n  \\\"memory\\\": \\\"64Mi\\\"\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/007-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/007-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/007-evidence-run_bash_command.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"node\":\"node2\"},\"value\":[1779349894.926,\"1.7750000000000001\"]},{\"metric\":{\"node\":\"master\"},\"value\":[1779349894.926,\"5.61\"]},{\"metric\":{\"node\":\"node1\"},\"value\":[1779349894.926,\"0.85\"]},{\"metric\":{},\"value\":[1779349894.926,\"100000\"]}]}}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/008-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/008-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/008-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"__name__\":\"kube_node_status_allocatable\",\"container\":\"kube-state-metrics\",\"endpoint\":\"http\",\"instance\":\"172.16.219.98:8080\",\"job\":\"kube-state-metrics\",\"namespace\":\"xnet\",\"node\":\"master\",\"pod\":\"observability-kube-state-metrics-798986b8b7-jz47w\",\"resource\":\"cpu\",\"service\":\"observability-kube-state-metrics\",\"unit\":\"core\"},\"value\":[1779349895.325,\"12\"]},{\"metric\":{\"__name__\":\"kube_node_status_allocatable\",\"container\":\"kube-state-metrics\",\"endpoint\":\"http\",\"instance\":\"172.16.219.98:8080\",\"job\":\"kube-state-metrics\",\"namespace\":\"xnet\",\"node\":\"node1\",\"pod\":\"observability-kube-state-metrics-798986b8b7-jz47w\",\"resource\":\"cpu\",\"service\":\"observability-kube-state-metrics\",\"unit\":\"core\"},\"value\":[1779349895.325,\"12\"]},{\"metric\":{\"__name__\":\"kube_node_status_allocatable\",\"container\":\"kube-state-metrics\",\"endpoint\":\"http\",\"instance\":\"172.16.219.98:8080\",\"job\":\"kube-state-metrics\",\"namespace\":\"xnet\",\"node\":\"node2\",\"pod\":\"observability-kube-state-metrics-798986b8b7-jz47w\",\"resource\":\"cpu\",\"service\":\"observability-kube-state-metrics\",\"unit\":\"core\"},\"value\":[1779349895.325,\"12\"]}]}}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/009-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/009-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/009-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"name\\\": \\\"rc-pending-insufficient-cpu\\\",\\n  \\\"requests\\\": {\\n    \\\"cpu\\\": \\\"100k\\\",\\n    \\\"memory\\\": \\\"64Mi\\\"\\n  },\\n  \\\"imagePullPolicy\\\": \\\"Never\\\"\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/010-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/010-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/010-evidence-run_bash_command.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{\"__name__\":\"kube_pod_container_resource_requests\",\"container\":\"app\",\"endpoint\":\"http\",\"instance\":\"172.16.219.98:8080\",\"job\":\"kube-state-metrics\",\"namespace\":\"aiops-e2e\",\"pod\":\"rc-pending-insufficient-cpu\",\"resource\":\"cpu\",\"service\":\"observability-kube-state-metrics\",\"uid\":\"c8dcdd8b-1273-40ea-b6a8-78a72ec315de\",\"unit\":\"core\"},\"value\":[1779349899.728,\"100000\"]}]}}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/011-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/011-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/011-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{},\"value\":[1779349904.832,\"5.61\"]}]}}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/012-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/012-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/012-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{},\"value\":[1779349905.151,\"1.7750000000000001\"]}]}}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/013-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/013-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/013-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{},\"value\":[1779349905.327,\"0.85\"]}]}}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/014-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/014-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ad91b10e1ea24a61/tools/014-evidence-execute_prometheus_instant_query.summary.txt"}],"llm_analysis":"好，所有关键证据已采集完毕。总结一下：\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据\n\n**1. Pod 当前状态与 FailedScheduling 事件（critical - kubectl_describe）**\n- Pod `rc-pending-insufficient-cpu`（aiops-e2e 命名空间）状态：**Pending**，未绑定节点\n- **FailedScheduling 事件原文**：`0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.`\n- 事件时效性：最早 52m 前，最近 22m 前（共 7 次），为 **持续活跃故障**\n\n**2. Pod YAML 配置（critical - kubectl_get_yaml）**\n- `resources.requests.cpu = \"100k\"` — **这是 100000 个 CPU 核心请求**，不是一个正常的 core 值\n- `priorityClassName: null`（未设置优先级类）\n- 无 nodeSelector/affinity 约束\n- `imagePullPolicy: Never` — 镜像拉取策略为 Never\n\n**3. Prometheus 验证 CPU 请求量（important）**\n- Pod `rc-pending-insufficient-cpu` 请求的 CPU = **100,000 核**（Prometheus kube_pod_container_resource_requests 直接记录为 100000 unit=core）\n- 3 个节点 allocatable CPU 各为 **12 核**，总计 **36 核**\n- 当前已分配（不含此Pod）：master=5.61, node1=0.85, node2=1.775，合计约 **8.24 核**，远低于 36 核可分配容量\n\n**4. 节点资源（important - kubectl + Prometheus）**\n- 3 个节点全部 **Ready**（排除了节点异常）\n- 集群可分配 CPU = 12+12+12 = **36 核**\n- 集群已分配（不含异常 Pod）≈ **8.24 核**，剩余充裕（约 27 核可用）\n\n### 🔍 根因定位\n**根本原因**：Pod 的 `resources.requests.cpu` 配置为 `\"100k\"`，被 Kubernetes 解析为 **100,000 个 CPU 核心**，远超集群所有节点合计的 36 核可分配容量，导致调度器在 3 个节点上都报 `Insufficient cpu`。这是一个**配置错误**（type 写成了 `k` 而非 `m`，实际意图应为 `100m` 即 0.1 核），而非集群资源真正不足。\n\n**辅助原因**：`priorityClassName: null` 且 `imagePullPolicy: Never`（意味着镜像必须已被拉取，否则无法启动）。\n\n### ❌ 冲突/负向证据\n- 无冲突证据，所有工具调用结果与上游信号一致并得到验证。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 17 个，匹配计划 4 个，未规划证据 13 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":17,"matched_tool_count":4,"unplanned_tool_count":13,"evidence_inventory":[{"id":"ev1-critical-pod-describe","description":"Describe the pending pod rc-pending-insufficient-cpu to verify current status, events, and scheduling failures","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","purpose":"验证 Pod 当前状态、FailedScheduling 事件原文、Pod spec 中的 resource requests、priorityClass、nodeSelector/affinity/tolerations 等调度相关配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev2-critical-pod-yaml","description":"Get the full YAML of the pending pod to examine resource requests, priorityClass, and scheduling constraints","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","purpose":"检查 Pod spec.containers[].resources.requests.cpu 具体数值、priorityClassName、nodeSelector、affinity、tolerations 等调度配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev3-important-node-resources","description":"Check allocatable and allocatable CPU on all 3 nodes to confirm insufficient cpu across the cluster","level":"important","tool":"run_bash_command","command":"kubectl get nodes -o json | jq -r '.items[] | {name: .metadata.name, allocatable: .status.allocatable, capacity: .status.capacity}'","purpose":"获取所有节点的 allocatable CPU 和 total CPU，验证集群 CPU 分配率是否已饱和，确认 3 Insufficient cpu 的根因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev4-important-events","description":"Check recent events in the aiops-e2e namespace for scheduling-related warnings","level":"important","tool":"kubectl_events","command":"kubectl events -n aiops-e2e --for pod/rc-pending-insufficient-cpu","purpose":"确认 FailedScheduling 事件的时效性和具体原文，验证 3 Insufficient cpu 和 No preemption victims found 的真实性","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev5-reference-runbook","description":"Fetch the runbook for Pod PendingUnschedulable to use as reference","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-pending-unschedulable.md","purpose":"获取 PendingUnschedulable runbook 作为诊断参考","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | ev1-critical-... | critical | ✅ | kubectl_describe | Describe the pending pod rc-pending-insuffici... | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` |
   | ev2-critical-... | critical | ✅ | kubectl_get_yaml | Get the full YAML of the pending pod to exami... | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml` |
   | ev3-important... | important | ✅ | run_bash_command | Check allocatable and allocatable CPU on all ... | `kubectl get nodes -o json | jq -r '.items[] | {name: .metadata.name, allocata...` |
   | ev4-important... | important | ✅ | kubectl_events | Check recent events in the aiops-e2e namespac... | `kubectl events -n aiops-e2e --for pod/rc-pending-insufficient-cpu` |
   | ev5-reference... | reference | ❌ | fetch_runbook | Fetch the runbook for Pod PendingUnschedulabl... | `fetch_runbook pod-pending-unschedulable.md` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (27.2s)
   📤 → 下游数据: root_cause=根因为 Pod rc-pending-insufficient-cpu (aiops-e2e) 的 requests.cpu 配置为 "100k"（对应 Prometheus 记录的 100,000 core），而集群 3 个节点 master/node1/node2 的 allocatable cpu 各为 12 核（合计仅 36 核）。调度器明确报错 '0/3 nodes are available: 3 Insufficient cpu'。集群实际已分配 CPU 仅约 8.24 核（master=5.61, node1=0.85, node2=1.775），剩余约 27.76 核充裕，说明非真正资源不足而是配置错误。该 Pod 未设置 priorityClass，无法抢占，且 imagePullPolicy=Never 是辅助约束。
   confidence=95%
   causal_chain={"root_cause": "Pod rc-pending-insufficient-cpu 的资源请求配置错误：resources.requests.cpu 设置为 '100k'（100,000 核），远超集群所有 3 个节点合计 36 核的可分配 CPU 容量", "propagation": "调度器在 master/node1/node2 三个节点上评估该 Pod 的 CPU 请求时，发现每个节点均无法满足 100,000 核的需求，标记为 3 Insufficient cpu；由于 priorityClass 未设置，调度器尝试抢占但无可用受害者（No preemption victims found），最终 Pod 持续处于 Pending 状态", "direct_cause": "所有 3 个节点的可分配 CPU（各 12 核，合计 36 核）均无法满足 Pod 请求的 100,000 核 CPU", "manifestation": "Pod rc-pending-insufficient-cpu 在 aiops-e2e 命名空间中持续 Pending 超过 52 分钟，kubectl 显示 STATUS=Pending, NODE=<none>，Events 持续报 FailedScheduling"}
   rca_analysis={"phenomenon": "集群 aiops-e2e 命名空间中的 Pod rc-pending-insufficient-cpu 持续处于 Pending 状态已达 52 分钟，无法调度到任何节点。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod rc-pending-insufficient-cpu 状态 Pending，FailedScheduling 事件：0/3 nodes are available: 3 Insufficient cpu，preemption: 0/3 nodes are available: 3 No preemption victims found", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml", "content": "Pod YAML: resources.requests.cpu = \"100k\", priorityClass 未设置, imagePullPolicy=Never, 无 nodeSelector/affinity 约束", "reliability": "高"}, {"id": "e3", "source": "run_bash_command (kubectl get nodes -o json)", "content": "3 个节点 master/node1/node2 全部 Ready，allocatable cpu 各为 12 核，合计 36 核", "reliability": "高"}, {"id": "e4", "source": "execute_prometheus_instant_query", "content": "异常 Pod 请求 CPU=100000 core；集群已分配(不含异常): master=5.61, node1=0.85, node2=1.775, 合计约 8.24 核", "reliability": "高"}, {"id": "e5", "source": "kubectl_events", "content": "aiops-e2e 命名空间事件：52m 和 22m (x6 over 47m) 两次 FailedScheduling 事件，内容一致", "reliability": "高"}, {"id": "e6", "source": "kubectl_get_by_kind_in_cluster (nodes)", "content": "3 个节点全部 Ready，abnormal=0，排除节点异常", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu. preemption: No preemption victims found", "interpretation": "调度器在所有 3 个节点都检测到 CPU 不足，且没有可抢占的低优先级 Pod"}, {"evidence_id": "e2", "raw_data": "resources.requests.cpu = \"100k\"、priorityClass: null、imagePullPolicy: Never", "interpretation": "Pod 请求的 CPU 为 100k（即 100,000 核），这是一个异常大的值；未设置优先级类意味着无法抢占其他 Pod；imagePullPolicy=Never 要求镜像必须本地存在"}, {"evidence_id": "e3", "raw_data": "master: cpu=12, node1: cpu=12, node2: cpu=12 (allocatable)", "interpretation": "3 个节点每个可分配 12 核，总计 36 核，远小于 Pod 请求的 100,000 核"}, {"evidence_id": "e4", "raw_data": "Pod 请求 cpu=100000 core；集群已分配约 8.24 核 / 36 核可分配", "interpretation": "集群实际剩余 CPU 约 27.76 核，非常充裕。Pod 请求的 100,000 核是异常值，并非集群资源真正不足"}, {"evidence_id": "e5", "raw_data": "两次 FailedScheduling 事件，时间跨度 52m 到 22m 前，持续发生", "interpretation": "该故障并非瞬时事件，而是持续存在的调度阻塞，Pod 自创建后一直无法调度"}, {"evidence_id": "e6", "raw_data": "3 节点 Ready, abnormal=0", "interpretation": "排除节点 NotReady 或网络问题导致的调度失败"}], "causal_chain": {"root_cause": "Pod rc-pending-insufficient-cpu 的资源请求配置错误：resources.requests.cpu 设置为 '100k'（100,000 核），远超集群所有 3 个节点合计 36 核的可分配 CPU 容量", "propagation": "调度器在 master/node1/node2 三个节点上评估该 Pod 的 CPU 请求时，发现每个节点均无法满足 100,000 核的需求，标记为 3 Insufficient cpu；由于 priorityClass 未设置，调度器尝试抢占但无可用受害者（No preemption victims found），最终 Pod 持续处于 Pending 状态", "direct_cause": "所有 3 个节点的可分配 CPU（各 12 核，合计 36 核）均无法满足 Pod 请求的 100,000 核 CPU", "manifestation": "Pod rc-pending-insufficient-cpu 在 aiops-e2e 命名空间中持续 Pending 超过 52 分钟，kubectl 显示 STATUS=Pending, NODE=<none>，Events 持续报 FailedScheduling"}, "root_cause": "根因为 Pod rc-pending-insufficient-cpu (aiops-e2e) 的 requests.cpu 配置为 \"100k\"（对应 Prometheus 记录的 100,000 core），而集群 3 个节点 master/node1/node2 的 allocatable cpu 各为 12 核（合计仅 36 核）。调度器明确报错 '0/3 nodes are available: 3 Insufficient cpu'。集群实际已分配 CPU 仅约 8.24 核（master=5.61, node1=0.85, node2=1.775），剩余约 27.76 核充裕，说明非真正资源不足而是配置错误。该 Pod 未设置 priorityClass，无法抢占，且 imagePullPolicy=Never 是辅助约束。", "root_cause_summary": "根因为 Pod rc-pending-insufficient-cpu (aiops-e2e) 的 requests.cpu 配置为 \"100k\"（对应 Prometheus 记录的 100,000 core），而集群 3 个节点 master/node1/node2 的 allocatable cpu 各为 12 核（合计仅 36 核）。调度器明确报错 '0/3 nodes are available: 3 Insufficient cpu'。集群实际已分配 CPU 仅约 8.24 核（master=5.61, node1=0.85, node2=1.775），剩余约 27.76 核充裕，说明非真正资源不足而是配置错误。该 Pod 未设置 priorityClass，无法抢占，且 imagePullPolicy=Never 是辅助约束。", "confidence": 0.95, "confidence_reason": "有直接调度事件证据（FailedScheduling + 3 Insufficient cpu）、Pod YAML 明确显示 requests.cpu=100k、Prometheus 确认 100,000 core 请求和节点 12 核可分配容量、节点全部 Ready 排除节点异常，因果链完整无歧义", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "集群整体 CPU 资源真正不足", "probability": "low", "reason": "Prometheus 数据显示集群已分配仅 8.24 核/36 核可分配，剩余约 27.76 核充裕，排除真实资源不足"}, {"cause": "Taint/NodeSelector/Affinity 不匹配", "probability": "low", "reason": "Pod YAML 显示无 nodeSelector/affinity 约束，Tolerations 仅有默认的 not-ready:NoExecute，排除调度约束问题"}, {"cause": "PVC 未绑定或卷依赖未满足", "probability": "low", "reason": "Pod 仅使用默认的 kube-api-access 投影卷（ServiceAccount token），无 PVC 依赖，且 FailedScheduling 消息未提及 PVC"}, {"cause": "节点异常（NotReady/Unschedulable）", "probability": "low", "reason": "kubectl_get_by_kind_in_cluster 确认 3 节点全部 Ready，abnormal=0"}], "limitations": "未获取到 Pod 的完整 YAML 原始输出（有截断），但关键字段 requests.cpu=100k 已从多个工具（kubectl_get_yaml + run_bash_command + Prometheus）交叉验证。imagePullPolicy=Never 可能意味着本地镜像不存在时会额外导致拉取失败，但当前 Pod 未到达调度阶段，此问题尚未触发。", "llm_raw_analysis": "## 证据清点\n已采集 6 项关键证据：kubectl_describe（Pod 状态与事件）、kubectl_get_yaml（Pod 配置）、node resource JSON（3 节点各 12 核可分配）、Prometheus 查询（Pod 请求 100000 core + 节点已分配量）、kubectl_events（调度事件确认）、节点状态确认（3 Ready）。\n\n## 逐条分析\n- e1：Pod Pending，FailedScheduling 明确说明 3 个节点全部 CPU 不足，无抢占受害者\n- e2：Pod YAML 显示 requests.cpu = \"100k\"，这是 100,000 核，远超正常值；priorityClass 未设置\n- e3：3 节点 allocatable cpu 各 12 核，合计 36 核，全部 Ready\n- e4：Prometheus 确认 Pod 请求 100000 core，集群已分配仅 8.24 核，剩余 27.76 核充裕\n- e5：事件持续 52 分钟，非瞬时故障\n- e6：排除节点异常\n\n## 因果链\n配置错误（re\n... 截断，原始 573 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 根因为 Pod rc-pending-insufficient-cpu (aiops-e2e) 的 requests.cpu 配置为 "100k"（对应 Prometheus 记录的 100,000 core），而集群 3 个节点 master/node1/node2 的 allocatable c...
   置信度: 95%
   🔗 因果链:
     根本原因: Pod rc-pending-insufficient-cpu 的资源请求配置错误：resources.requests.cpu 设置为 '100k'（100,000 核），远超集群所有 3 个节点合计 36 核的可分配 CPU 容量
     传导机制: 调度器在 master/node1/node2 三个节点上评估该 Pod 的 CPU 请求时，发现每个节点均无法满足 100,000 核的需求，标记为 3 Insufficient cpu；由于 priorityClass 未设置，调度器尝试抢占但无可用受害者（No preemption victims found），最终 Pod 持续处于 Pending 状态
     最终表现: Pod rc-pending-insufficient-cpu 在 aiops-e2e 命名空间中持续 Pending 超过 52 分钟，kubectl 显示 STATUS=Pending, NODE=<none>，Events 持续报 FailedScheduling


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (30.9s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6176 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 4.6s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将根据您提供的所有信息，生成一份详尽、完整的诊断报告。

---
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **集群问题总结** | 集群中存在 1 个 Pending 状态的 Pod `rc-pending-insufficient-cpu`，根本无法被调度。原因是其配置了**一个不可能被满足的 CPU 请求（100,000 核）**，远超过集群所有节点的总可分配 CPU 容量（36 核）。 |
| **Pod异常状态** | Pending |
| **兼容归因层** | L1 - 调度/Scheduling |
| **问题分类** | PendingUnschedulable（因资源请求配置错误导致无法调度） |
| **置信度** | 高 (95%) |
| **证据完整度** | 4/4 (100%) |
---
## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | `rc-pending-insufficient-cpu` |
| Namespace | `aiops-e2e` |
| Node | `master`, `node1`, `node2` |
| 主要问题 | Pod 持续 Pending 状态，无法被调度到任何节点 |
---
## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令/工具 | 原始数据 | 分析结论 |
|---|----------|---------------|----------|----------|
| 1 | Pod 事件 | `kubectl_events`, `kubectl_describe` | `Warning FailedScheduling 0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.` | 调度器在所有3个节点上都因 CPU 不足而调度失败，且无低优先级 Pod 可被抢占。 |
| 2 | Pod 资源配置 | `kubectl_get_yaml`, `run_bash_command` | `resources.requests.cpu: "100k"`<br>`resources.requests.memory: "64Mi"` | **核心证据**。Pod 请求 `100k` 个 CPU (即 100,000 核)，这是一个极度异常且不可能被满足的值。 |
| 3 | 节点资源容量 | `run_bash_command`, `execute_prometheus_instant_query` | 节点 `master` 可分配 CPU: 12 核<br>节点 `node1` 可分配 CPU: 12 核<br>节点 `node2` 可分配 CPU: 12 核<br>**集群总计可分配 CPU: 36 核** | 集群总容量仅 36 核，远无法满足 Pod 请求的 100,000 核。 |
| 4 | 集群 CPU 实际使用 | `execute_prometheus_instant_query` | `master` 已分配: 5.61 核<br>`node1` 已分配: 0.85 核<br>`node2` 已分配: 1.775 核<br>**集群已分配 CPU: 约 8.24 核** | 集群实际上有约 27.76 核的剩余 CPU，说明并非真正资源枯竭，而是 Pod 请求值配置错误。 |
| 5 | Pod 调度约束 | `kubectl_describe` | `Node-Selectors: <none>` | Pod 没有任何节点选择器约束，因此调度失败完全归因于 CPU 资源请求。 |

### 证据关联分析
- **核心证据链 (证据 #1 + #2 + #3)**：调度器报错 `3 Insufficient cpu`，同时工具证实 Pod 请求 `100k` CPU，而集群所有节点可分配 CPU 总和仅为 `36` 核，两者形成了直接、明确的因果关系。
- **排除真正资源不足 (证据 #4)**：集群实际已分配 CPU 仅为 `8.24` 核，远未达到总容量的上限，这有力证明了问题是**配置错误**而非**资源枯竭**。
- **排除调度约束 (证据 #5)**：Pod 未设置 nodeSelector 或亲和性规则，排除了因调度约束不匹配导致的调度失败。

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| 无 | 无 | 证据链完整，所有关键证据均已采集。 |
---
## 🎯 根因分析
### 因果链
```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因 (Root Cause)                                                                             │
│ Pod 'rc-pending-insufficient-cpu' 的资源请求 (resources.requests.cpu) 被错误地设置为 "100k"，即  │
│ 100,000 个 CPU 核心。这是一个配置错误，可能是笔误 (如 "100m" 写成 "100k") 或 CI/CD 脚本问题。    │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制 (Propagation)                                                                           │
│ Kubernetes 调度器评估该 Pod 时，发现其请求的 100,000 核 CPU，远超集群 3 个节点总共 36 核的可用量 │
│ (每个节点 12 核)。由于 Pod 未设置 priorityClassName，调度器尝试抢占但找不到可被抢占的低优先级 Pod │
│ (No preemption victims found)。                                                                   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因 (Direct Cause)                                                                           │
│ 集群中所有 3 个节点 (master, node1, node2) 的可分配 CPU 均无法满足该 Pod 的 100,000 核需求，      │
│ 导致调度失败。                                                                                    │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象 (User-Visible Issue)                                                                │
│ Pod 'rc-pending-insufficient-cpu' 在 aiops-e2e 命名空间中持续处于 Pending 状态，Events 持续报告    │
│ FailedScheduling 错误。                                                                           │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据**证据 #1** (FailedScheduling 事件) 和**证据 #2** (请求 100k CPU) 以及**证据 #3** (节点总 CPU 36核)，问题的根本原因是 **Pod 的资源请求配置错误**。`100k` CPU 是一个不合理值，导致调度器无法在任何节点上为其分配资源。

**置信度**：高 (95%)
- ✅ FailedScheduling 事件与 CPU 请求值完全吻合
- ✅ Pod YAML 和 `run_bash_command` 多次交叉验证了 `100k` 的请求值
- ✅ 节点可分配 CPU 数据（Prometheus + 命令）提供了充分对比
- ⚠️ 由于环境限制，未获得完整 Pod YAML 原始输出，但关键字段已通过多种工具反复验证。`imagePullPolicy: Never` 是次要配置，不影响当前 Pending 问题。
---
## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [优先] 修复 Pod 的 CPU 请求**
此问题是配置错误，需要修改 Pod 或创建它的控制器（如 Deployment、Job等）的 YAML 文件。

- **如果 Pod 由 Deployment 管理**（假设名为 `rc-pending-insufficient-cpu`）：
  ```bash
  # 1. 更新资源请求 (示例改为 100m 即 0.1 核)
  kubectl set resources deployment/rc-pending-insufficient-cpu -n aiops-e2e --requests=cpu=100m
  ```
  *依据*：`100m` 是标准的 CPU 请求单位，代表 0.1 个 CPU 核心。请根据应用实际需求调整此值。

- **如果 Pod 是独立创建**：
  ```bash
  # 由于独立 Pod 无法直接修改，需要删除并重新创建正确配置
  kubectl delete pod rc-pending-insufficient-cpu -n aiops-e2e
  # 然后使用正确的 YAML 重新创建
  ```
  *依据*：修改正在运行的 Pod 的资源配置是受限操作，通常需要重建。

**2. [确认] 查明配置错误来源**
- 检查创建该 Pod 的 CI/CD 配置文件、Helm Values 或 YAML 模板，确认 `cpu` 字段被写为 `"100k"` 的原因（如，是否本应为 `"100m"` 或 `"1"`）。
- 修复源头以防止问题再次发生。

### 后续优化
1. **准入控制**：启用运维策略（如 OPA/Gatekeeper）或准入 Webhook，对 Pod 的资源配置进行校验，禁止设置超过节点容量或明显不合理的资源请求（如 > 1000 核）。
2. **资源配额**：为命名空间 `aiops-e2e` 设置 ResourceQuota，限制其总资源使用上限，防止单个错误 Pod 耗尽命名空间的资源配额。
---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 被调度 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o wide` | `STATUS` 为 `Running` 或 `ContainerCreating`，且 `NODE` 列显示分配到的节点名称 |
| 2. 检查 Pod 事件 | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` | 不再出现 `FailedScheduling` 事件 |
---
## ⚠️ 注意事项
- **“100k”不是标准值**：在 Kubernetes 资源模型中，`k` 并不是 CPU 单位的合法后缀。CPU 的正确单位是 `m` (millicores)，如 `100m` 代表 0.1 核。将 `100k` 视为 100,000 核是 Prometheus 等监控系统的展示方式，Kubernetes API 同样会将其解析为一个极大的数值。
- **`imagePullPolicy: Never`**：该 Pod 配置了 `imagePullPolicy: Never`，意味着如果本地没有该镜像，Pod 会在完成调度后因拉取不到镜像而失败。请在修复资源请求后，也注意确认镜像是否存在。

---

## 📊 性能统计

├─ 总耗时: 2.1m
├─ 问题定位: 23.5s (19%) ✅
├─ 证据链采集: 43.1s (35%) ✅
├─ 根因分析: 27.2s (22%) ✅
├─ 汇总总结: 30.9s (25%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 18 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 18 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
