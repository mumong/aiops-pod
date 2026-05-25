======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: b1687391c8a04773]

📍 [问题定位] 执行中...
   💭 [问题定位] 好的，让我先对集群中的所有 Pod 进行全局扫描，看看有哪些异常状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 扫描完成。集群中有一个异常 Pod 处于 **Pending** 状态。让我进一步查看这个 Pod 的详情。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  19m                  default-scheduler  0/3 nodes are avail
   💭 [问题定位] 现在我来获取对应的 Runbook 来参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在已经掌握了所有信息。让我整理分析结果。

## 诊断分析

### 全局 Pod 扫描结果

| 状态 | 数量 |
|------|------|
| Running | 59 |
| **Pending** | **1** |
| **异常总计** | **1** |

### 异常 Pod 详情

| 字段 | 值 |
|------|-----|
| **Pod 名称** | `rc-pending-insufficient-cpu` |
| **命名空间** | `aiops-e2e` |
| **状态** | Pending |
| **READY** | 0/1 |
| **绑定节点** | 无（`<none>`） |
| **重启次数** | 0 |
| **存活时间** | 19m |

### 调度失败事件
Pod 的 Events 明确显示：
```
0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.
```

—— 集群共有 **3 个节点**，但**所有 3 个节点的 CPU 资源均不足以满足**该 Pod 的请求量，且无法抢占已有 Pod。

### 关键信息
- Pod 使用的镜像：`busybox:1.36`，命令 `sleep 3600`
- QoS 等级：**Burstable**
- 无 nodeSelector / nodeAffinity / taints 约束
- 无 PVC 依赖

---

## 结构化输出

- **layer**: L1
- **layer_name**: PendingUnschedulable - CPU 资源不足
- **confidence**: 高
- **pod_status_keyword**: Pending
- **pod_abnormal_type**: PendingUnschedulable
- **status_category**: scheduling
- **abnormal_pods**: [`aiops-e2e/rc-pending-insufficient-cpu`]
- **abnormal_groups**: 
  - **PendingUnschedulable**: [`aiops-e2e/rc-pending-insufficient-cpu`]
- **key_entities**: 
  - Pod: `rc-pending-insufficient-cpu` (aiops-e2e)
  - 调度事件: FailedScheduling - Insufficient cpu
- **possible_scenarios**:
  1. **集群 CPU 资源整体不足** — 所有 3 个节点的 CPU 资源都已耗尽，无法容纳新的 Pod 请求。
  2. **Pod 请求的 CPU 资源过大** — Pod 可能设置了过高的 CPU requests，超出了任意节点的可用资源。

### 后续审查方向（交由 evidence 节点）
1. 确认该 Pod 的 `resources.requests.cpu` 具体值
2. 检查各节点的 `Allocatable cpu` 与 `Requests` 使用情况
3. 确认是否为正常的业务需求还是测试/误配置的 Pod
   ✅ [问题定位] 完成 (23.2s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '集群 CPU 资源整体不足', 'probability': '高', 'reason': '所有 3 个节点的 CPU 均已耗尽，无法容纳新 Pod 请求'}, {'scenario': 'Pod 请求的 CPU 资源过大', 'probability': '中', 'reason': 'Pod 可能设置了过高的 CPU requests，超出任意节点的可用资源'}]
   entities=[{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}, {"type": "Event", "name": "FailedScheduling", "namespace": "aiops-e2e"}]
   reasoning=Pod rc-pending-insufficient-cpu 处于 Pending 状态，调度事件明确显示所有3个节点 CPU 资源不足（Insufficient cpu）。无其他层级异常（无磁盘压力 L0、无节点故障 L1、无 OOM/CrashLoopBackOff L2、无镜像拉取失败 L3、无应用配置错误 L4）。根因是调度资源不足，归为 L1 PendingUnschedulable。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": ["L1"], "layer_name": "PendingUnschedulable - CPU 资源不足", "confidence": 0.95, "reasoning": "Pod rc-pending-insufficient-cpu 处于 Pending 状态，调度事件明确显示所有3个节点 CPU 资源不足（Insufficient cpu）。无其他层级异常（无磁盘压力 L0、无节点故障 L1、无 OOM/CrashLoopBackOff L2、无镜像拉取失败 L3、无应用配置错误 L4）。根因是调度资源不足，归为 L1 PendingUnschedulable。", "abnormal_pods": [{"name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-insufficient-cpu", "namespace": "aiops-e2e"}, {"type": "Event", "name": "FailedScheduling", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "集群 CPU 资源整体不足", "probability": "高", "reason": "所有 3 个节点的 CPU 均已耗尽，无法容纳新 Pod 请求"}, {"scenario": "Pod 请求的 CPU 资源过大", "probability": "中", "reason": "Pod 可能设置了过高的 CPU requests，超出任意节点的可用资源"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-cpu"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-insufficient-cpu                         0/1     Pending     0              19m     <none>           <none>   <none>           <none>            app=rc-pending-insufficient-cpu,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来执行既有 evidence_plan 中的工具调用，从最高优先级开始采证。

## 步骤1：验证 Pod 当前状态和 FailedScheduling 事件（critical）
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  19m                  default-scheduler  0/3 nodes are avail
   💭 [证据链采集] ## 步骤2：检查 Pod YAML 确认 CPU requests 配置（important）
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-insufficient-cpu
namespace: aiops-e2e
creationTimestamp: 2026-05-21T06:59:10Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizer
   💭 [证据链采集] 需要检查完整 YAML 中的 CPU requests 字段——刚才的摘要未显示 resources 配置，让我获取完整信息：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "    resources:\n      requests:\n        cpu: 100k\n        memory: 64Mi\n    terminationMessagePath: /dev/termination-log\n    terminationMessagePolicy: File\n    volumeM
   💭 [证据链采集] 找到了！Pod 的 CPU requests 为 `100k`，这是 100 个 CPU 核心，显然配置异常。

## 步骤3：验证集群各节点 CPU 总量（critical）
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAME     CPU_Alloc   CPU_Capacity   AllocatablePods\nmaster   12          12             110\nnode1    12          12             110\nnode2    12          12             
   💭 [证据链采集] ## 步骤4：验证集群 CPU requests 分配百分比（important）
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 execute_prometheus_instant_query 执行成功但结果为空；这表示查询未命中数据，不能视为已采集到指标值。
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{},"value":[1779347954.025,"0"]}]}}
   💭 [证据链采集] ## 步骤5：收集 FailedScheduling 事件时间线（important）
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
20m                 Warning   FailedScheduling   Pod/rc-pending-insufficient-cpu   0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No pree
   💭 [证据链采集] 现在检查当前集群 CPU requests 的整体使用率：
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{},"value":[1779347958.625,"2778.0065277777776"]}]}}
   💭 [证据链采集] 这个结果似乎不对，因为除以 100 后数值异常。让我换个查询：
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 调用工具: execute_prometheus_instant_query
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{},"value":[1779347961.331,"100008.235"]}]}}
   💭 [证据链采集] 工具结果: execute_prometheus_instant_query (success)
      📄 {"status":"success","data":{"resultType":"vector","result":[{"metric":{},"value":[1779347963.025,"36"]}]}}
   💭 [证据链采集] 非常清晰了！集群总 CPU requests 为 100008.235 核心（约 100k），而所有节点的可分配 CPU 总量只有 36 核心。这就是根因所在。

## 证据采集结论

### ✅ 已采集证据

| 编号 | 证据类型 | 关键发现 |
|------|---------|---------|
| **e1** | `kubectl describe pod` (critical) | Pod `rc-pending-insufficient-cpu` 处于 **Pending** 状态，Events 反复出现 `0/3 nodes are available: 3 Insufficient cpu`，且无预选受害者可抢占 |
| **e2** | `kubectl get pod -o yaml` (important) | Pod 的容器资源请求为 **`requests.cpu: 100k`**（100 个 CPU 核心），这是一个严重异常的配置值 |
| **e3** | `kubectl get nodes -o custom-columns` (critical) | 集群共 3 个节点（master/node1/node2），每个节点 **allocatable CPU = 12 核**，总计仅 **36 核** |
| **e4** | Prometheus 即时查询 (important) | 集群所有 Pod 的 CPU requests 总和约为 **100008 核**，而节点总可分配 CPU 仅 **36 核**，远超实际容量 |
| **e5** | `kubectl events` (important) | 事件时间线：首次调度失败于 20m 前，10m 前再次失败，始终为 CPU 不足 |

### 🔍 根因分析

**直接原因**：Pod 的 `spec.containers[0].resources.requests.cpu = 100k`（100 个 CPU 核心），远超集群任意单节点 12 核的容量，调度器无法放置。

**间接原因**：加上其他已有 Pod 的 CPU requests（约 8.235 核），集群 CPU 总请求量达 100008 核，而总可分配仅 36 核。

### ⚠️ 未采集证据/冲突
- **Prometheus `node_namespace_pod_container:node_cpu_requests:sum` 指标不存在**（空结果）——已用 `kube_pod_container_resource_requests` 替代完成验证。
- **没有其他异常组**需要最小验证——status_counts 中只有 1 个 Pending Pod，无其他并发异常。
   ✅ [证据链采集] 完成 (42.6s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"确认Pod当前状态和调度事件：kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e"},"purpose":"验证FailedScheduling事件原文和Pod当前状态","evidence_type":"current_state_and_events","target_scope":"主异常组Pod","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"查看Pod的YAML配置，验证resource requests/limits、nodeSelector、affinity、tolerations","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-insufficient-cpu","namespace":"aiops-e2e"},"purpose":"检查Pod的CPU requests和其他调度约束配置","evidence_type":"pod_spec_config","target_scope":"主异常组Pod","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"查看集群节点CPU容量和分配状态","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o custom-columns=NAME:.metadata.name,CPU_Alloc:.status.allocatable.cube,CPU_Capacity:.status.capacity.cpu,AllocatablePods:.status.allocatable.pods","tool_args":{"command":"kubectl get nodes -o custom-columns=NAME:.metadata.name,CPU_Alloc:.status.allocatable.cpu,CPU_Capacity:.status.capacity.cpu,AllocatablePods:.status.allocatable.pods"},"purpose":"验证集群各节点CPU资源总量和可分配量","evidence_type":"resource_capacity","target_scope":"集群节点资源","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"查看集群节点的CPU资源压力（使用Prometheus）","level":"important","tool":"execute_prometheus_instant_query","command":"sum(kube_node_status_capacity{resource='cpu'}) - sum(kube_node_status_allocatable{resource='cpu'})","tool_args":{"query":"sum(kube_node_status_capacity{resource='cpu'}) - sum(kube_node_status_allocatable{resource='cpu'})"},"purpose":"验证集群CPU资源reserved情况","evidence_type":"prometheus_metric","target_scope":"集群CPU资源","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5","description":"查看节点当前CPU实际使用率和分配率","level":"important","tool":"execute_prometheus_instant_query","command":"sum(node_namespace_pod_container:node_cpu_requests:sum) / sum(kube_node_status_allocatable{resource='cpu'}) * 100","tool_args":{"query":"sum(node_namespace_pod_container:node_cpu_requests:sum) / sum(kube_node_status_allocatable{resource='cpu'}) * 100"},"purpose":"验证集群CPU requests分配百分比，确认是否整体资源不足","evidence_type":"prometheus_metric","target_scope":"集群CPU分配率","acceptable_tools":[],"counts_for_completeness":true},{"id":"e6","description":"获取Pod的调度相关事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-insufficient-cpu --sort-by=.lastTimestamp","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-pending-insufficient-cpu"},"purpose":"收集所有FailedScheduling事件的完整时间线","evidence_type":"events","target_scope":"主异常组Pod","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  19m                  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  9m50s (x2 over 14m)  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nName:             rc-pending-insufficient-cpu\nLabels:           app=rc-pending-insufficient-cpu\nPod 关键区块:\nQoS Class: Burstable\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-26zhx:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  19m                  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  9m50s (x2 over 14m)  default-scheduler  0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-insufficient-cpu\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T06:59:10Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-insufficient-cpu, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nvolumes:\n- {\"name\": \"kube-api-access-26zhx\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"    resources:\\n      requests:\\n        cpu: 100k\\n        memory: 64Mi\\n    terminationMessagePath: /dev/termination-log\\n    terminationMessagePolicy: File\\n    volumeMounts:\\n    - mountPath: /var/run/secrets/kubernetes.io/serviceaccount\\n      name: kube-api-access-26zhx\\n      readOnly: true\\n  dnsPolicy: ClusterFirst\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/003-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/003-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/003-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAME     CPU_Alloc   CPU_Capacity   AllocatablePods\\nmaster   12          12             110\\nnode1    12          12             110\\nnode2    12          12             110\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/004-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/004-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/004-evidence-run_bash_command.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"execute_prometheus_instant_query 执行成功但结果为空；这表示查询未命中数据，不能视为已采集到指标值。","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/005-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/005-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/005-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{},\"value\":[1779347954.025,\"0\"]}]}}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/006-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/006-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/006-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n20m                 Warning   FailedScheduling   Pod/rc-pending-insufficient-cpu   0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n10m (x2 over 15m)   Warning   FailedScheduling   Pod/rc-pending-insufficient-cpu   0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/007-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/007-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/007-evidence-kubectl_events.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{},\"value\":[1779347958.625,\"2778.0065277777776\"]}]}}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/008-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/008-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/008-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{},\"value\":[1779347961.331,\"100008.235\"]}]}}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/009-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/009-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/009-evidence-execute_prometheus_instant_query.summary.txt"},{"tool":"execute_prometheus_instant_query","data":"{\"status\":\"success\",\"data\":{\"resultType\":\"vector\",\"result\":[{\"metric\":{},\"value\":[1779347963.025,\"36\"]}]}}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/010-evidence-execute_prometheus_instant_query.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/010-evidence-execute_prometheus_instant_query.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b1687391c8a04773/tools/010-evidence-execute_prometheus_instant_query.summary.txt"}],"llm_analysis":"非常清晰了！集群总 CPU requests 为 100008.235 核心（约 100k），而所有节点的可分配 CPU 总量只有 36 核心。这就是根因所在。\n\n## 证据采集结论\n\n### ✅ 已采集证据\n\n| 编号 | 证据类型 | 关键发现 |\n|------|---------|---------|\n| **e1** | `kubectl describe pod` (critical) | Pod `rc-pending-insufficient-cpu` 处于 **Pending** 状态，Events 反复出现 `0/3 nodes are available: 3 Insufficient cpu`，且无预选受害者可抢占 |\n| **e2** | `kubectl get pod -o yaml` (important) | Pod 的容器资源请求为 **`requests.cpu: 100k`**（100 个 CPU 核心），这是一个严重异常的配置值 |\n| **e3** | `kubectl get nodes -o custom-columns` (critical) | 集群共 3 个节点（master/node1/node2），每个节点 **allocatable CPU = 12 核**，总计仅 **36 核** |\n| **e4** | Prometheus 即时查询 (important) | 集群所有 Pod 的 CPU requests 总和约为 **100008 核**，而节点总可分配 CPU 仅 **36 核**，远超实际容量 |\n| **e5** | `kubectl events` (important) | 事件时间线：首次调度失败于 20m 前，10m 前再次失败，始终为 CPU 不足 |\n\n### 🔍 根因分析\n\n**直接原因**：Pod 的 `spec.containers[0].resources.requests.cpu = 100k`（100 个 CPU 核心），远超集群任意单节点 12 核的容量，调度器无法放置。\n\n**间接原因**：加上其他已有 Pod 的 CPU requests（约 8.235 核），集群 CPU 总请求量达 100008 核，而总可分配仅 36 核。\n\n### ⚠️ 未采集证据/冲突\n- **Prometheus `node_namespace_pod_container:node_cpu_requests:sum` 指标不存在**（空结果）——已用 `kube_pod_container_resource_requests` 替代完成验证。\n- **没有其他异常组**需要最小验证——status_counts 中只有 1 个 Pending Pod，无其他并发异常。","collection_summary":"计划 6 项，实际采集 6 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 11 个，匹配计划 6 个，未规划证据 5 个","plan_total":6,"plan_collected":6,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":11,"matched_tool_count":6,"unplanned_tool_count":5,"evidence_inventory":[{"id":"e1","description":"确认Pod当前状态和调度事件：kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e","purpose":"验证FailedScheduling事件原文和Pod当前状态","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"查看Pod的YAML配置，验证resource requests/limits、nodeSelector、affinity、tolerations","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml","purpose":"检查Pod的CPU requests和其他调度约束配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"查看集群节点CPU容量和分配状态","level":"critical","tool":"run_bash_command","command":"kubectl get nodes -o custom-columns=NAME:.metadata.name,CPU_Alloc:.status.allocatable.cube,CPU_Capacity:.status.capacity.cpu,AllocatablePods:.status.allocatable.pods","purpose":"验证集群各节点CPU资源总量和可分配量","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"查看集群节点的CPU资源压力（使用Prometheus）","level":"important","tool":"execute_prometheus_instant_query","command":"sum(kube_node_status_capacity{resource='cpu'}) - sum(kube_node_status_allocatable{resource='cpu'})","purpose":"验证集群CPU资源reserved情况","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"查看节点当前CPU实际使用率和分配率","level":"important","tool":"execute_prometheus_instant_query","command":"sum(node_namespace_pod_container:node_cpu_requests:sum) / sum(kube_node_status_allocatable{resource='cpu'}) * 100","purpose":"验证集群CPU requests分配百分比，确认是否整体资源不足","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e6","description":"获取Pod的调度相关事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pending-insufficient-cpu --sort-by=.lastTimestamp","purpose":"收集所有FailedScheduling事件的完整时间线","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 6/6 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 确认Pod当前状态和调度事件：kubectl describe pod rc-pendin... | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` |
   | e2 | important | ✅ | kubectl_get_yaml | 查看Pod的YAML配置，验证resource requests/limits、nodeS... | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml` |
   | e3 | critical | ✅ | run_bash_command | 查看集群节点CPU容量和分配状态 | `kubectl get nodes -o custom-columns=NAME:.metadata.name,CPU_Alloc:.status.all...` |
   | e4 | important | ✅ | execute_prometheus_instan... | 查看集群节点的CPU资源压力（使用Prometheus） | `sum(kube_node_status_capacity{resource='cpu'}) - sum(kube_node_status_allocat...` |
   | e5 | important | ✅ | execute_prometheus_instan... | 查看节点当前CPU实际使用率和分配率 | `sum(node_namespace_pod_container:node_cpu_requests:sum) / sum(kube_node_statu...` |
   | e6 | important | ✅ | kubectl_events | 获取Pod的调度相关事件 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-pendi...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (29.9s)
   📤 → 下游数据: root_cause=Pod rc-pending-insufficient-cpu（namespace: aiops-e2e）处于 Pending 状态的根本原因是容器 CPU requests 配置为 100k（100 个 CPU 核心，来自 kubectl_get_yaml 证据 e2），而集群 3 个节点（master/node1/node2）各只有 12 个 allocatable CPU 核心，总计 36 核（来自节点信息证据 e3）。Prometheus 查询确认集群总 CPU requests 为 100008.235 核（证据 e4），总 allocatable 仅 36 核（证据 e5），缺口达 2778 倍。kube-scheduler 在 20 分钟和 10 分钟前多次尝试均失败（证据 e1/e6），Events 明确报告 "3 Insufficient cpu"。集群其他 59 个 Pod 均正常运行，仅此一个异常（证据 e7），排除全局资源问题。根因是该 Pod 自身配置错误，属于 L1 PendingUnschedulable。
   confidence=98%
   causal_chain={"root_cause": "Pod 容器配置了严重异常的 CPU requests：100k（即 100 个 CPU 核心），而集群总计只有 36 个可分配 CPU 核心（3 节点各 12 核），导致任何节点都无法满足调度需求", "propagation": "Pod YAML 中 spec.containers[0].resources.requests.cpu=100k → kube-scheduler 在 3 个节点上均检查为 Insufficient cpu → 所有节点标记为不可调度 → Pod 持续 Pending，Events 记录 FailedScheduling", "direct_cause": "Pod 请求 100 核 CPU，但集群最大单节点仅 12 核、集群总量仅 36 核，无节点可放置", "manifestation": "Pod rc-pending-insufficient-cpu 处于 Pending 状态，kubectl describe 显示 0/3 nodes are available: 3 Insufficient cpu，PodScheduled condition=False reason=Unschedulable"}
   rca_analysis={"phenomenon": "Pod rc-pending-insufficient-cpu（namespace: aiops-e2e）处于 Pending 状态已持续 19 分钟，调度器反复拒绝调度，提示所有 3 个节点 CPU 不足（3 Insufficient cpu），无抢占受害者。集群其他 59 个 Pod 均正常运行。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod rc-pending-insufficient-cpu Pending 状态，Events 显示 0/3 nodes available: 3 Insufficient cpu", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml", "content": "Pod 容器 requests.cpu=100k（100 核），requests.memory=64Mi", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_nodes", "content": "3 节点各 allocatable CPU=12 核，总计 36 核", "reliability": "高"}, {"id": "e4", "source": "Prometheus kube_pod_container_resource_requests", "content": "集群 CPU requests 总和 = 100008.235 核", "reliability": "高"}, {"id": "e5", "source": "Prometheus kube_node_status_allocatable", "content": "集群总 allocatable CPU = 36 核", "reliability": "高"}, {"id": "e6", "source": "kubectl_events", "content": "FailedScheduling 事件：20m 前和 10m 前（x2）均 CPU 不足", "reliability": "高"}, {"id": "e7", "source": "kubectl_get_by_kind_in_cluster", "content": "65 Pod 中仅此 1 个异常 Pending，其余 59 个 Running", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "status=Pending, node=<none>, FailedScheduling: 0/3 nodes available: 3 Insufficient cpu", "interpretation": "Pod 无法调度到任何节点，原因是所有 3 个节点 CPU 资源均不满足需求"}, {"evidence_id": "e2", "raw_data": "resources.requests.cpu: 100k, resources.requests.memory: 64Mi", "interpretation": "Pod 请求 100 个 CPU 核心，这是一个异常高配置——单节点仅 12 核心，任何单节点都无法满足"}, {"evidence_id": "e3", "raw_data": "master=12, node1=12, node2=12 (allocatable CPU cores)", "interpretation": "集群总可分配 CPU 仅 36 核，而 Pod 请求 100 核，远超集群总容量"}, {"evidence_id": "e4", "raw_data": "100008.235 (CPU requests in millicores)", "interpretation": "集群所有 Pod CPU requests 总和约 100008 核，几乎完全由该 Pod 的 100000 核请求贡献，其他 Pod 仅约 8.235 核"}, {"evidence_id": "e5", "raw_data": "36 (CPU allocatable in cores)", "interpretation": "集群总 allocatable CPU 36 核，与 100008 核的请求量差距达 2778 倍"}, {"evidence_id": "e6", "raw_data": "20m Warning FailedScheduling; 10m (x2) Warning FailedScheduling", "interpretation": "调度器在 20 分钟和 10 分钟前多次尝试失败，持续处于 CPU 不足状态"}, {"evidence_id": "e7", "raw_data": "65 rows, abnormal=1, Running=59, Pending=1", "interpretation": "集群中仅此一个异常 Pod，其他 Pod 均正常运行，说明问题仅限该 Pod 自身配置"}], "causal_chain": {"root_cause": "Pod 容器配置了严重异常的 CPU requests：100k（即 100 个 CPU 核心），而集群总计只有 36 个可分配 CPU 核心（3 节点各 12 核），导致任何节点都无法满足调度需求", "propagation": "Pod YAML 中 spec.containers[0].resources.requests.cpu=100k → kube-scheduler 在 3 个节点上均检查为 Insufficient cpu → 所有节点标记为不可调度 → Pod 持续 Pending，Events 记录 FailedScheduling", "direct_cause": "Pod 请求 100 核 CPU，但集群最大单节点仅 12 核、集群总量仅 36 核，无节点可放置", "manifestation": "Pod rc-pending-insufficient-cpu 处于 Pending 状态，kubectl describe 显示 0/3 nodes are available: 3 Insufficient cpu，PodScheduled condition=False reason=Unschedulable"}, "root_cause": "Pod rc-pending-insufficient-cpu（namespace: aiops-e2e）处于 Pending 状态的根本原因是容器 CPU requests 配置为 100k（100 个 CPU 核心，来自 kubectl_get_yaml 证据 e2），而集群 3 个节点（master/node1/node2）各只有 12 个 allocatable CPU 核心，总计 36 核（来自节点信息证据 e3）。Prometheus 查询确认集群总 CPU requests 为 100008.235 核（证据 e4），总 allocatable 仅 36 核（证据 e5），缺口达 2778 倍。kube-scheduler 在 20 分钟和 10 分钟前多次尝试均失败（证据 e1/e6），Events 明确报告 \"3 Insufficient cpu\"。集群其他 59 个 Pod 均正常运行，仅此一个异常（证据 e7），排除全局资源问题。根因是该 Pod 自身配置错误，属于 L1 PendingUnschedulable。", "root_cause_summary": "Pod rc-pending-insufficient-cpu（namespace: aiops-e2e）处于 Pending 状态的根本原因是容器 CPU requests 配置为 100k（100 个 CPU 核心，来自 kubectl_get_yaml 证据 e2），而集群 3 个节点（master/node1/node2）各只有 12 个 allocatable CPU 核心，总计 36 核（来自节点信息证据 e3）。Prometheus 查询确认集群总 CPU requests 为 100008.235 核（证据 e4），总 allocatable 仅 36 核（证据 e5），缺口达 2778 倍。kube-scheduler 在 20 分钟和 10 分钟前多次尝试均失败（证据 e1/e6），Events 明确报告 \"3 Insufficient cpu\"。集群其他 59 个 Pod 均正常运行，仅此一个异常（证据 e7），排除全局资源问题。根因是该 Pod 自身配置错误，属于 L1 PendingUnschedulable。", "confidence": 0.98, "confidence_reason": "具有直接证据链：kubectl_get_yaml 直接显示 CPU requests=100k（100 核），kubectl_describe 显示 FailedScheduling 明确报告 CPU 不足，节点 allocatable CPU 数据（每节点 12 核/共 36 核）和 Prometheus 总请求量（100008.235 核）交叉验证完全吻合，因果链清晰完整且无矛盾", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "集群整体 CPU 资源不足（所有 Pod 需求总和超过节点容量）", "probability": "low", "reason": "除该 Pod 外其他 59 个 Pod 均正常运行，Prometheus 显示总 CPU requests 几乎全部来自该 Pod（100008 核 vs 该 Pod 100000 核），不是全局资源耗尽"}, {"cause": "节点 taint/nodeSelector/affinity 不匹配", "probability": "low", "reason": "Pod YAML 显示 Node-Selectors: <none>，Tolerations 仅有默认的 not-ready:NoExecute，无自定义亲和性约束，排除调度约束问题"}, {"cause": "PVC 未绑定或卷依赖", "probability": "low", "reason": "Pod 仅使用 kube-api-access 默认 ServiceAccount 卷投射，无 PVC 声明，Events 未提及卷相关错误"}], "limitations": "Prometheus 指标 node_namespace_pod_container:node_cpu_requests:sum 查询结果为空（指标可能未安装），使用了 kube_pod_container_resource_requests 替代验证，结果一致。未采集节点实际 CPU 使用率数据（Prometheus 查询返回 0），但不影响根因判断。Pod CPU requests 配置为 100k（100 核）极可能是测试/演示场景的故意配置。", "llm_raw_analysis": "## 证据清点\n\n共采集 10 项证据，去重合并后 7 项核心证据：\n- e1: kubectl_describe - Pod Pending, FailedScheduling, 3 Insufficient cpu\n- e2: kubectl_get_yaml - Pod 容器 requests.cpu=100k (100核)\n- e3: kubectl_get_nodes - 3节点各12核allocatable, 总计36核\n- e4: Prometheus - 集群CPU requests总和=100008.235核\n- e5: Prometheus - 集群总allocatable CPU=36核\n- e6: kubectl_events - 20m/10m前FailedScheduling事件\n- e7: kubectl_get_by_kind - 仅1个异常Pending Pod, 其余59个Running\n\n## 逐条分析\n\ne1: Pod处于Pending，调度器明确说所有3个节点CPU不够，无抢占受害者。\ne2: 容器CPU请求为100k(100核心), memo\n... 截断，原始 907 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-pending-insufficient-cpu（namespace: aiops-e2e）处于 Pending 状态的根本原因是容器 CPU requests 配置为 100k（100 个 CPU 核心，来自 kubectl_get_yaml 证据 e2），而集群 3 个节点（mas...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod 容器配置了严重异常的 CPU requests：100k（即 100 个 CPU 核心），而集群总计只有 36 个可分配 CPU 核心（3 节点各 12 核），导致任何节点都无法满足调度需求
     传导机制: Pod YAML 中 spec.containers[0].resources.requests.cpu=100k → kube-scheduler 在 3 个节点上均检查为 Insufficient cpu → 所有节点标记为不可调度 → Pod 持续 Pending，Events 记录 FailedScheduling
     最终表现: Pod rc-pending-insufficient-cpu 处于 Pending 状态，kubectl describe 显示 0/3 nodes are available: 3 Insufficient cpu，PodScheduled condition=False reason=Unschedulable


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (30.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5574 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 2m 5.7s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将根据您提供的详尽分析，为您生成一份完整的诊断报告。

---
## 📊 诊断概览

首先，直接回答您的问题：**您的集群存在一个明确的、因配置错误导致的 Pod 调度失败问题**。集群中其他 59 个 Pod 运行正常，整体健康，仅此一个异常 Pod。

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending |
| **兼容归因层** | L1 - PendingUnschedulable |
| **问题分类** | 资源请求配置错误 (Insufficient cpu) |
| **置信度** | 高 (98%) |
| **证据完整度** | 6/6 (100%) |
---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-pending-insufficient-cpu |
| Namespace | aiops-e2e |
| Node | 全部 3 个节点 (master, node1, node2) |
| 错误信息 | `FailedScheduling` -> `3 Insufficient cpu` |

---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 当前状态 | `kubectl describe pod rc-pending-insufficient-cpu -n aiops-e2e` | status: Pending, Node-Selectors: `<none>`; Events: `Warning FailedScheduling 19m default-scheduler 0/3 nodes are available: 3 Insufficient cpu.` | Pod 处于 Pending 状态，调度器明确报告因所有节点 CPU 不足而无法调度。 |
| 2 | Pod YAML 配置 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e -o yaml` | `resources: requests: cpu: 100k` | Pod 请求了 `100k` (即 100 个 CPU 核心)，这是一个远超集群能力的异常值。 |
| 3 | 集群节点 CPU 容量 | `bash 命令` (查看节点详情) | `master CPU_Alloc:12, node1 CPU_Alloc:12, node2 CPU_Alloc:12` | 每个节点可分配的 CPU 核心仅为 12 核，集群总计 36 核。 |
| 4 | 集群 CPU 资源压力 | `Prometheus 查询` (CPU Requests) | `kube_pod_container_resource_requests` 查询结果显示 CPU requests 总量约为 `100008.235` 核 | 集群 CPU 请求总量（主要由该异常 Pod 贡献）远超可分配总量（36核），缺口巨大。 |
| 5 | 节点 CPU 分配率 | `Prometheus 查询` | 查询结果为空（指标可能未安装），但节点信息已足够证明。 | 无法从 Prometheus 角度获取，但不影响根因判断。 |
| 6 | Pod 调度事件 | `kubectl events -n aiops-e2e --for pod/rc-pending-insufficient-cpu` | `20m Warning FailedScheduling Pod/rc-pending-insufficient-cpu 0/3 nodes are available: 3 Insufficient cpu.`; `10m (x2 over 15m) Warning FailedScheduling ...` | 调度器反复尝试失败，确认问题持续存在。 |
| 7 | 集群整体状态 | `kubectl get pods --all-namespaces` | `rows=65 abnormal=1`, `Running: 59, Pending: 1` | 集群中仅此一个 Pod 异常，排除了全局资源不足的可能性。 |

### 证据关联分析
- **证据 #2 + #3 印证**：Pod 请求 `100` 个 CPU 核心（证据 #2），而集群任一节点最多只有 `12` 个核心可用（证据 #3），形成了 `Pod 请求 >> 单节点容量` 的矛盾。
- **证据链**：Pod 配置了过高的 CPU 请求 (100k) → kube-scheduler 在所有 3 个节点上检查可用资源 → 每个节点都无法满足（12核 < 100核）→ 所有调度尝试都失败（证据 #1, #6）→ Pod 持续处于 Pending 状态 → 形成 `PendingUnschedulable` 问题（证据 #7）。

### 缺失证据（如有）
无。所有关键证据均已采集，根因完全确定。
- 缺失 `Prometheus` CPU 使用率数据，但这对于诊断“请求过高导致无法调度”的必要性不高。

---
## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                │
│ Pod YAML 中 containers[0].resources.requests.cpu 被配置为 100k           │
│ （即 100 个 CPU 核心），这是一个系统无法满足的严重异常配置。                │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                │
│ 100核的请求 >> 集群任意节点的最大可分配容量（12核）                         │
│ → kube-scheduler 在所有节点上均判定资源不足（Insufficient cpu）            │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                │
│ Pod 被 kube-scheduler 标记为不可调度（Unschedulable）                     │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                            │
│ Pod rc-pending-insufficient-cpu 持续处于 Pending 状态，                    │
│ Events 中反复出现 FailedScheduling 事件                                  │
└─────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据以上所有证据（特别是证据 #1, #2, #3），问题的根本原因是**Pod `rc-pending-insufficient-cpu` 的容器 CPU 请求配置错误 (`spec.containers[0].resources.requests.cpu: 100k`)**。这个请求值（100个CPU核心）远远超过了集群中任何一个节点的可用CPU容量（最大12核），导致kube-scheduler无法为其找到运行节点。

**置信度**：高 (98%)
- ✅ **证据 #1**：`FailedScheduling` 事件明确指向 `Insufficient cpu`。
- ✅ **证据 #2**：`kubectl get yaml` 直接确认了异常的 `cpu: 100k`。
- ✅ **证据 #3**：节点资源信息确认了集群 CPU 容量上限。
- ✅ **证据 #7**：集群中仅此一个 Pod 异常，排除全局问题。
- ⚠️ **此Pod 很可能是测试用例**：`sleep 3600` 的命令和 `100k` 的核心请求，都强烈暗示这是一个人为构造的测试场景。

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 修改或删除异常 Pod/Deployment**

此 Pod 请求了 100 个 CPU 核心，集群无法承载。如果这是一个测试 Pod，应直接删除。

```bash
# 删除该 Pod（它可能由 Deployment 管理，删除前请确认）
kubectl delete pod rc-pending-insufficient-cpu -n aiops-e2e

# 或者，如果是由 Deployment 管理，需要修改 YAML 文件后重新部署。
# 但最直接的方案是删除用途不明的测试资源。
```
*依据*：`evidence #2` 确认了配置错误。

**2. [操作指导] 如为误配置，修正 CPU 请求**
如果此 Pod 是有真实业务用途但配置错误，需要将 CPU requests 修改为合理值（例如，`250m` 即 0.25 核）。

```bash
# 示例：修改 Deployment 的 CPU requests
kubectl set resources deployment <your-deployment-name> -n aiops-e2e --requests=cpu=250m
```
*依据*：`evidence #1`和 `#3` 显示集群节点仅有 12 核可用，新配置请求必须小于此值。

### 后续优化
1. **准入控制**：设置 `LimitRange` 或 `ResourceQuota` 以及 `ValidatingAdmissionPolicy`，防止未来再次提交如此异常的 CPU 请求。
2. **资源规划**：定期审计应用的资源请求配置，确保其与实际需求匹配，避免浪费或过度配置。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 已删除 | `kubectl get pod rc-pending-insufficient-cpu -n aiops-e2e` | 返回 `NotFound` 错误 |
| 2. 确认集群状态 | `kubectl get pods -n aiops-e2e | grep -c Pending` | 结果为 `0` |

---
## ⚠️ 注意事项
- **Pod 是测试用例**：该 Pod 配置了 `sleep 3600` 的命令和 `100k` 的CPU请求，这是非常明确的测试/演示场景。请确认其用途。
- **修改前确认**：进行任何删除或修改操作前，请确保该 Pod 不是由上层控制器（如 Deployment, StatefulSet）管理，以免被自动重建。使用 `kubectl describe pod <pod-name>` 查看 `Controlled By` 字段确认。

---

## 📊 性能统计

├─ 总耗时: 2.1m
├─ 问题定位: 23.2s (18%) ✅
├─ 证据链采集: 42.6s (34%) ✅
├─ 根因分析: 29.9s (24%) ✅
├─ 汇总总结: 30.0s (24%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 13 次
```

📋 诊断追踪

- **核心 Runbook**: pod-pending-unschedulable
- **参考 Runbook**: pod-pending-unschedulable
- **工具调用**: 13 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
