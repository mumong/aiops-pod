======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: ee90357370194204]

📍 [问题定位] 执行中...
   💭 [问题定位] 让我先全局扫描所有 Pod，掌握集群的整体状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59, 'Pending': 1}
NAMESPACE         NAME                                                READY   STATUS      RESTARTS  
   💭 [问题定位] 我看到有一个异常 Pod，让我进一步了解它的情况。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                             READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE   READINESS GATES   LABELS
rc-pending-insufficient-memory   0/1     Pending   0          29m   <non
   💭 [问题定位] Pod 处于 Pending 状态，标签指向 `PendingUnschedulable`，让我看看详细信息和调度事件。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-memory
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  29m                  default-scheduler  0/3 nodes are av
   💭 [问题定位] 现在匹配 runbook 进行定位参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod PendingUnschedulable / 调度失败

> Pod异常类型: PendingUnschedulable | 典型状态: Pending | 兼容分类: scheduling

## 场景识别

| 信号 | 关键特征 |
|------|----------|
| Pod 状态 | Pending，且 Events 含 `FailedSchedul
   💭 [问题定位] 现在我已经有足够信息来做定位分析了。让我整理一下结果。

## 集群 Pod 状态扫描结果

| 状态 | 数量 |
|------|------|
| ✅ **Running** (正常) | 59 |
| ⏳ **Pending** (异常) | 1 |
| **总计** | **60** |

---

## 异常 Pod 定位分析

### 1️⃣ 异常 Pod 识别

| Pod | 命名空间 | 状态 | 原因 |
|-----|---------|------|------|
| `rc-pending-insufficient-memory` | `aiops-e2e` | **Pending** | **FailedScheduling** |

### 2️⃣ 异常详情

**Pod:** `rc-pending-insufficient-memory`
**状态:** Pending（未调度到任何节点）
**调度事件:** `0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod.`
**镜像:** `busybox:1.36`（命令 `sleep 3600`）
**QoS:** Burstable

### 3️⃣ 异常类型判定

- **pod_status_keyword:** `Pending`
- **pod_abnormal_type:** `PendingUnschedulable`
- **兼容层级 (Layer):** **L1**
- **根因:** 集群中 **3 个节点的可用内存均不足**，无法满足此 Pod 的资源请求，且调度器找不到可以抢占的受害者 Pod。

---

## 输出

| 字段 | 值 |
|------|-----|
| **layer** | L1 |
| **layer_name** | 调度资源不足 |
| **pod_abnormal_type** | PendingUnschedulable |
| **status_category** | scheduling |
| **confidence** | 高 |
| **abnormal_pods** | 1 (rc-pending-insufficient-memory) |
| **abnormal_groups** | PendingUnschedulable |
| **key_entities** | Pod: rc-pending-insufficient-memory (aiops-e2e), Nodes: 3个节点均内存不足 |
| **possible_scenarios** | 集群节点内存资源整体紧张，该 Pod 请求的内存大小超出所有节点的可用剩余内存；或节点内存碎片化导致无法分配 |
   ✅ [问题定位] 完成 (21.1s)
   📤 → 下游数据: layer=Layer.L1, layers=L1
   scenarios=[{'scenario': '集群节点内存资源整体紧张，Pod 请求的内存超出所有节点可用剩余内存', 'probability': '高', 'reason': "FailedScheduling 事件明确提示 '0/3 nodes are available: 3 Insufficient memory'，所有节点均不满足内存资源请求"}]
   entities=[{"type": "Pod", "name": "rc-pending-insufficient-memory", "namespace": "aiops-e2e"}, {"type": "Node", "name": "3个节点（均内存不足）", "namespace": ""}]
   reasoning=集群中存在 1 个异常 Pod（rc-pending-insufficient-memory），状态为 Pending，调度事件显示所有 3 个节点均因内存不足无法调度该 Pod。pod_status_keyword 为 Pending，pod_abnormal_type 为 PendingUnschedulable，status_category 为 scheduling。属于调度资源不足，无节点可调度，归入 L1 层级。
   layer_analysis={"layer": "L1", "derived_layer": "L1", "layers": [], "layer_name": "调度资源不足", "confidence": 0.95, "reasoning": "集群中存在 1 个异常 Pod（rc-pending-insufficient-memory），状态为 Pending，调度事件显示所有 3 个节点均因内存不足无法调度该 Pod。pod_status_keyword 为 Pending，pod_abnormal_type 为 PendingUnschedulable，status_category 为 scheduling。属于调度资源不足，无节点可调度，归入 L1 层级。", "abnormal_pods": [{"name": "rc-pending-insufficient-memory", "namespace": "aiops-e2e", "status": "Pending"}], "pod_status_keyword": "Pending", "pod_abnormal_type": "PendingUnschedulable", "status_category": "scheduling", "key_entities": [{"type": "Pod", "name": "rc-pending-insufficient-memory", "namespace": "aiops-e2e"}, {"type": "Node", "name": "3个节点（均内存不足）", "namespace": ""}], "possible_scenarios": [{"scenario": "集群节点内存资源整体紧张，Pod 请求的内存超出所有节点可用剩余内存", "probability": "高", "reason": "FailedScheduling 事件明确提示 '0/3 nodes are available: 3 Insufficient memory'，所有节点均不满足内存资源请求"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-memory"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["Pending"], "pod_abnormal_type": "PendingUnschedulable", "compatible_layers": ["L1"], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-pending-insufficient-memory"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "资源不足导致无法调度", "probability": "中", "reason": "需验证 FailedScheduling 事件"}, {"scenario": "taint/nodeSelector/affinity 不匹配", "probability": "中", "reason": "需验证 Pod spec 和 Node 条件"}, {"scenario": "PVC 未绑定或卷依赖未满足", "probability": "中", "reason": "需验证 PVC/PV 状态"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Pending": 1}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-pending-insufficient-memory                      0/1     Pending     0              29m     <none>           <none>   <none>           <none>            app=rc-pending-insufficient-memory,pod_abnormal_type=PendingUnschedulable,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/ee90357370194204/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/ee90357370194204/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/ee90357370194204/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L1
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 开始执行既有 evidence_plan 中的工具调用。

首先，我要执行 ev-001（关键证据：Pod describe）和 ev-003（重要证据：节点内存信息），这两个无冲突可并行执行。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-pending-insufficient-memory
namespace: aiops-e2e
node: <none>
status: Pending
关键诊断行:
  Warning  FailedScheduling  30m                  default-scheduler  0/3 nodes are av
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "master\t32758084Ki\t32860484Ki\nnode1\t32758076Ki\t32860476Ki\nnode2\t32758080Ki\t32860480Ki\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] 好的，关键证据已获取。接下来执行 ev-002（Pod YAML 查看内存请求量）和 ev-004（集群 FailedScheduling 事件）。
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NAMESPACE   LAST SEEN   TYPE      REASON             OBJECT                               SUBOBJECT   SOURCE                                        MESSAGE                
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-pending-insufficient-memory
namespace: aiops-e2e
creationTimestamp: 2026-05-21T08:00:52Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finali
   💭 [证据链采集] 现在让我再查一下 Pod 的 resources 配置——YAML 摘要中没有显示 resources.requests，我用 jq 精确提取。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"requests\": {\n    \"cpu\": \"50m\",\n    \"memory\": \"100000Gi\"\n  }\n}\n", "stderr": "", "returncode": 0}
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"name\": \"master\",\n  \"allocatable_memory\": \"32758084Ki\",\n  \"allocatable_cpu\": \"12\"\n}\n{\n  \"name\": \"node1\",\n  \"allocatable_memory\": \"32758076Ki\
   💭 [证据链采集] 所有计划项已执行完毕，以下是证据结论：

---

## 证据采集结论

### ✅ 已采集证据

| 证据项 | 来源 | 结论 |
|--------|------|------|
| **ev-001** Pod 状态与调度事件 | `kubectl describe pod` | Pod 仍处于 **Pending** 状态，`FailedScheduling` 事件明确：**0/3 nodes are available: 3 Insufficient memory**，无抢占受害者 |
| **ev-002** Pod 资源请求配置 | `kubectl get pod -o yaml` + json | containers[0].resources.requests.memory = **100000Gi**（约 100TB），containers[0].resources.requests.cpu = **50m** |
| **ev-003** 节点内存容量 | `kubectl get nodes` jsonpath | 3 个节点（master/node1/node2）allocatable 内存均为 **~32,758 MiB（约 32Gi）** |
| **ev-004** 集群 FailedScheduling 事件 | `kubectl get events` | 除本 Pod 外，还有一个历史 Pod `rc-pending-insufficient-cpu` 因 **Insufficient cpu** 无法调度（已进入删除流程） |

### 🔍 根因分析

**Pod `rc-pending-insufficient-memory` 无法调度的直接原因：**
- Pod 请求内存 **100,000 Gi（~100 TB）**
- 集群 3 个节点每个仅 **~32 Gi allocatable 内存**
- Pod 请求量是单个节点容量的 **~3,125 倍**，任何节点都无法满足
- 无 preemption 受害者（其他 Pod 即使被抢占也无法释放 100TB 内存）
- Pod 无 nodeSelector/affinity/taint 约束，排除了调度约束问题
- 无 PVC 依赖，排除了卷挂载问题

**结论：配置错误**——Pod 的 `resources.requests.memory` 被设置为 `100000Gi`，这远超出集群中所有节点的实际可用内存（约 32Gi/节点），导致调度器无法放置。
   ✅ [证据链采集] 完成 (25.9s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"ev-001","description":"验证 Pod rc-pending-insufficient-memory 的当前状态和 FailedScheduling 事件（主异常组完整验证）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-memory -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-pending-insufficient-memory","namespace":"aiops-e2e"},"purpose":"确认 Pod 当前仍处于 Pending 状态，FailedScheduling 事件中明确提示内存不足的详细信息","evidence_type":"event","target_scope":"Pod/aiops-e2e/rc-pending-insufficient-memory","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-002","description":"验证 Pod 的资源请求配置（内存请求量）","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-memory -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-pending-insufficient-memory","namespace":"aiops-e2e"},"purpose":"检查 Pod spec 中 containers.resources.requests.memory 的具体数值，确认内存请求量是否超出节点可用内存","evidence_type":"config","target_scope":"Pod/aiops-e2e/rc-pending-insufficient-memory","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"ev-003","description":"获取集群所有节点的内存容量和可分配量","level":"important","tool":"run_bash_command","command":"kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{\"\\t\"}{.status.allocatable.memory}{\"\\t\"}{.status.capacity.memory}{\"\\n\"}{end}'","tool_args":{},"purpose":"查看所有节点的内存 allocatable 和 capacity，确认节点剩余内存是否足以容纳 Pod 请求","evidence_type":"capacity","target_scope":"Node/集群所有节点","acceptable_tools":[],"counts_for_completeness":true},{"id":"ev-004","description":"检查 Pod 所在集群的事件中是否还有其他调度相关异常","level":"important","tool":"kubectl_events","command":"kubectl get events --all-namespaces --field-selector reason=FailedScheduling -o wide | head -20","tool_args":{},"purpose":"收集集群中所有 FailedScheduling 事件，确认是否只有该 Pod 受影响","evidence_type":"event","target_scope":"Cluster","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-pending-insufficient-memory\nnamespace: aiops-e2e\nnode: <none>\nstatus: Pending\n关键诊断行:\n  Warning  FailedScheduling  30m                  default-scheduler  0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  4m48s (x5 over 24m)  default-scheduler  0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nName:             rc-pending-insufficient-memory\nLabels:           app=rc-pending-insufficient-memory\nPod 关键区块:\nQoS Class: Burstable\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Image:      busybox:1.36\n    Command:\n      sh\n      -c\n      sleep 3600\n    Environment:  <none>\n    Mounts:\nVolumes:\n  kube-api-access-c69j6:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedScheduling  30m                  default-scheduler  0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n  Warning  FailedScheduling  4m48s (x5 over 24m)  default-scheduler  0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\n关键状态/事件:","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ee90357370194204/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ee90357370194204/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ee90357370194204/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"master\\t32758084Ki\\t32860484Ki\\nnode1\\t32758076Ki\\t32860476Ki\\nnode2\\t32758080Ki\\t32860480Ki\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ee90357370194204/tools/002-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ee90357370194204/tools/002-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ee90357370194204/tools/002-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NAMESPACE   LAST SEEN   TYPE      REASON             OBJECT                               SUBOBJECT   SOURCE                                        MESSAGE                                                                                                                                 FIRST SEEN   COUNT   NAME\\naiops-e2e   31m         Warning   FailedScheduling   pod/rc-pending-insufficient-cpu                  default-scheduler, default-scheduler-master   0/3 nodes are available: 3 Insufficient cpu. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..      86m          12      rc-pending-insufficient-cpu.18b182b7ae7cc468\\naiops-e2e   30m         Warning   FailedScheduling   pod/rc-pending-insufficient-cpu                  default-scheduler, default-scheduler-master   skip schedule deleting pod: aiops-e2e/rc-pending-insufficient-cpu                                                                       30m          1       rc-pending-insufficient-cpu.18b185ccaa1f1e42\\naiops-e2e   30m         Warning   FailedScheduling   pod/rc-pending-insufficient-memory               default-scheduler, default-scheduler-master   0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..   30m          1       rc-pending-insufficient-memory.18b185cf1f65f365\\naiops-e2e   4m51s       Warning   FailedScheduling   pod/rc-pending-insufficient-memory               default-scheduler, default-scheduler-master   0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..   24m          5       rc-pending-insufficient-memory.18b18619d4590ba2\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ee90357370194204/tools/003-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ee90357370194204/tools/003-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ee90357370194204/tools/003-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-pending-insufficient-memory\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T08:00:52Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: None\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-pending-insufficient-memory, pod_abnormal_type=PendingUnschedulable\ndiagnostic_annotations: aiops.e2e/runbook=pod-pending-unschedulable.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- PodScheduled: status=False reason=Unschedulable message=0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available: 3 No preemption victims found for incoming pod..\nvolumes:\n- {\"name\": \"kube-api-access-c69j6\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ee90357370194204/tools/004-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ee90357370194204/tools/004-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ee90357370194204/tools/004-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"requests\\\": {\\n    \\\"cpu\\\": \\\"50m\\\",\\n    \\\"memory\\\": \\\"100000Gi\\\"\\n  }\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ee90357370194204/tools/005-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ee90357370194204/tools/005-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ee90357370194204/tools/005-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"name\\\": \\\"master\\\",\\n  \\\"allocatable_memory\\\": \\\"32758084Ki\\\",\\n  \\\"allocatable_cpu\\\": \\\"12\\\"\\n}\\n{\\n  \\\"name\\\": \\\"node1\\\",\\n  \\\"allocatable_memory\\\": \\\"32758076Ki\\\",\\n  \\\"allocatable_cpu\\\": \\\"12\\\"\\n}\\n{\\n  \\\"name\\\": \\\"node2\\\",\\n  \\\"allocatable_memory\\\": \\\"32758080Ki\\\",\\n  \\\"allocatable_cpu\\\": \\\"12\\\"\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/ee90357370194204/tools/006-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/ee90357370194204/tools/006-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/ee90357370194204/tools/006-evidence-run_bash_command.summary.txt"}],"llm_analysis":"所有计划项已执行完毕，以下是证据结论：\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据\n\n| 证据项 | 来源 | 结论 |\n|--------|------|------|\n| **ev-001** Pod 状态与调度事件 | `kubectl describe pod` | Pod 仍处于 **Pending** 状态，`FailedScheduling` 事件明确：**0/3 nodes are available: 3 Insufficient memory**，无抢占受害者 |\n| **ev-002** Pod 资源请求配置 | `kubectl get pod -o yaml` + json | containers[0].resources.requests.memory = **100000Gi**（约 100TB），containers[0].resources.requests.cpu = **50m** |\n| **ev-003** 节点内存容量 | `kubectl get nodes` jsonpath | 3 个节点（master/node1/node2）allocatable 内存均为 **~32,758 MiB（约 32Gi）** |\n| **ev-004** 集群 FailedScheduling 事件 | `kubectl get events` | 除本 Pod 外，还有一个历史 Pod `rc-pending-insufficient-cpu` 因 **Insufficient cpu** 无法调度（已进入删除流程） |\n\n### 🔍 根因分析\n\n**Pod `rc-pending-insufficient-memory` 无法调度的直接原因：**\n- Pod 请求内存 **100,000 Gi（~100 TB）**\n- 集群 3 个节点每个仅 **~32 Gi allocatable 内存**\n- Pod 请求量是单个节点容量的 **~3,125 倍**，任何节点都无法满足\n- 无 preemption 受害者（其他 Pod 即使被抢占也无法释放 100TB 内存）\n- Pod 无 nodeSelector/affinity/taint 约束，排除了调度约束问题\n- 无 PVC 依赖，排除了卷挂载问题\n\n**结论：配置错误**——Pod 的 `resources.requests.memory` 被设置为 `100000Gi`，这远超出集群中所有节点的实际可用内存（约 32Gi/节点），导致调度器无法放置。","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 7/7 项，完整度 100%；实际执行工具 9 个，匹配计划 4 个，未规划证据 5 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":7,"environment_evidence_collected":7,"environment_evidence_completeness":1.0,"executed_tool_count":9,"matched_tool_count":4,"unplanned_tool_count":5,"evidence_inventory":[{"id":"ev-001","description":"验证 Pod rc-pending-insufficient-memory 的当前状态和 FailedScheduling 事件（主异常组完整验证）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-pending-insufficient-memory -n aiops-e2e","purpose":"确认 Pod 当前仍处于 Pending 状态，FailedScheduling 事件中明确提示内存不足的详细信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-002","description":"验证 Pod 的资源请求配置（内存请求量）","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-pending-insufficient-memory -n aiops-e2e -o yaml","purpose":"检查 Pod spec 中 containers.resources.requests.memory 的具体数值，确认内存请求量是否超出节点可用内存","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-003","description":"获取集群所有节点的内存容量和可分配量","level":"important","tool":"run_bash_command","command":"kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{\"\\t\"}{.status.allocatable.memory}{\"\\t\"}{.status.capacity.memory}{\"\\n\"}{end}'","purpose":"查看所有节点的内存 allocatable 和 capacity，确认节点剩余内存是否足以容纳 Pod 请求","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"ev-004","description":"检查 Pod 所在集群的事件中是否还有其他调度相关异常","level":"important","tool":"kubectl_events","command":"kubectl get events --all-namespaces --field-selector reason=FailedScheduling -o wide | head -20","purpose":"收集集群中所有 FailedScheduling 事件，确认是否只有该 Pod 受影响","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | ev-001 | critical | ✅ | kubectl_describe | 验证 Pod rc-pending-insufficient-memory 的当前状态和 ... | `kubectl describe pod rc-pending-insufficient-memory -n aiops-e2e` |
   | ev-002 | critical | ✅ | kubectl_get_yaml | 验证 Pod 的资源请求配置（内存请求量） | `kubectl get pod rc-pending-insufficient-memory -n aiops-e2e -o yaml` |
   | ev-003 | important | ✅ | run_bash_command | 获取集群所有节点的内存容量和可分配量 | `kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.statu...` |
   | ev-004 | important | ✅ | kubectl_events | 检查 Pod 所在集群的事件中是否还有其他调度相关异常 | `kubectl get events --all-namespaces --field-selector reason=FailedScheduling ...` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (26.2s)
   📤 → 下游数据: root_cause=命名空间 aiops-e2e 下的 Pod rc-pending-insufficient-memory 处于 Pending 状态，根因是资源请求配置错误。该 Pod 的 memory request 被设置为 100000Gi（约 100TB），而集群中 3 个节点（master、node1、node2）的 allocatable 内存均仅为约 32,758 MiB（约 32Gi/节点）。Pod 请求量是单个节点容量的约 3,125 倍，任何节点都无法满足。调度器 FailedScheduling 事件明确报告 "0/3 nodes are available: 3 Insufficient memory"。Pod 无 nodeSelector/taint/affinity/PVC 等约束条件，排除了其他调度障碍。
   confidence=98%
   causal_chain={"root_cause": "Pod rc-pending-insufficient-memory 的 resources.requests.memory 被错误配置为 100000Gi（约 100TB），远超集群任何节点的可用内存容量（~32Gi/节点）", "propagation": "kube-scheduler 评估该 Pod 的资源请求，发现 3 个节点的 allocatable 内存（均约 32Gi）均远小于 Pod 请求的 100,000Gi → 调度器标记所有节点为 'Insufficient memory' → 尝试 preemption（抢占）但无任何 Pod 能释放 100TB 内存 → 调度失败 → Pod 停留在 Pending 状态", "direct_cause": "Pod 请求 100,000Gi 内存，而集群 3 节点的 allocatable 内存均仅为约 32Gi，差距达 3,125 倍，导致调度器无法找到可用节点", "manifestation": "Pod rc-pending-insufficient-memory 在 aiops-e2e 命名空间下持续 Pending 约 30 分钟，Events 含 FailedScheduling 警告 '0/3 nodes are available: 3 Insufficient memory'，无 nodeName 分配"}
   rca_analysis={"phenomenon": "命名空间 aiops-e2e 中的 Pod rc-pending-insufficient-memory 处于 Pending 状态，持续约 30 分钟未调度到任何节点。调度器事件报告 \"0/3 nodes are available: 3 Insufficient memory\"，所有 3 个节点（master、node1、node2）均因内存不足拒绝该 Pod。", "evidence_inventory": [{"id": "ev-001", "source": "kubectl_describe", "content": "Pod 状态 Pending，FailedScheduling 事件：0/3 nodes available, 3 Insufficient memory", "reliability": "高"}, {"id": "ev-002", "source": "kubectl_get_yaml + 资源请求查询", "content": "Pod containers[0].resources.requests.memory = 100000Gi（约 100TB）", "reliability": "高"}, {"id": "ev-003", "source": "kubectl_get_nodes allocatable", "content": "3 节点 allocatable 内存均为 ~32,758 MiB（约 32Gi）", "reliability": "高"}, {"id": "ev-004", "source": "kubectl_get_events", "content": "集群另有历史 Pod rc-pending-insufficient-cpu 因 Insufficient cpu 无法调度（已进入删除流程）", "reliability": "高"}, {"id": "layer_1-3", "source": "上游已验证工具结果", "content": "kubectl_get_by_kind_in_cluster: 65 Pods 中 59 Running、1 Pending；kubectl_get_by_name 和 kubectl_describe 均确认该 Pod 为唯一异常", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "ev-001", "raw_data": "Warning FailedScheduling 30m default-scheduler 0/3 nodes are available: 3 Insufficient memory.", "interpretation": "Pod 当前仍处于 Pending 状态，调度器明确拒绝原因：所有 3 个节点均内存不足。无 preemption 受害者可被抢占。这是当前故障的直接现象。"}, {"evidence_id": "ev-002", "raw_data": "resources.requests.memory = 100000Gi（100 TB）", "interpretation": "Pod 配置的内存请求量为 100,000 Gi，这是一个极端异常的数值。该配置是导致调度失败的根因——没有任何节点能提供如此巨大的内存。"}, {"evidence_id": "ev-003", "raw_data": "master: 32758084Ki (~32Gi), node1: 32758076Ki (~32Gi), node2: 32758080Ki (~32Gi)", "interpretation": "集群 3 个节点的 allocatable 内存均为约 32Gi。Pod 请求量（100,000Gi）是单个节点容量的约 3,125 倍，完全无法满足。"}, {"evidence_id": "ev-004", "raw_data": "pod/rc-pending-insufficient-cpu: 0/3 nodes are available: 3 Insufficient cpu", "interpretation": "集群中还有一个历史异常 Pod rc-pending-insufficient-cpu，因 CPU 不足无法调度，且已进入删除流程（skip schedule deleting pod）。该 Pod 由同一个 e2e 测试场景产生，但与当前 Pod 问题相互独立。"}, {"evidence_id": "layer_1-3", "raw_data": "65 Pods, Running=59, Pending=1", "interpretation": "全集群仅此一个异常 Pod，其他 59 个 Pod 均正常运行，说明集群整体健康，问题局限于该 Pod 的资源配置。"}], "causal_chain": {"root_cause": "Pod rc-pending-insufficient-memory 的 resources.requests.memory 被错误配置为 100000Gi（约 100TB），远超集群任何节点的可用内存容量（~32Gi/节点）", "propagation": "kube-scheduler 评估该 Pod 的资源请求，发现 3 个节点的 allocatable 内存（均约 32Gi）均远小于 Pod 请求的 100,000Gi → 调度器标记所有节点为 'Insufficient memory' → 尝试 preemption（抢占）但无任何 Pod 能释放 100TB 内存 → 调度失败 → Pod 停留在 Pending 状态", "direct_cause": "Pod 请求 100,000Gi 内存，而集群 3 节点的 allocatable 内存均仅为约 32Gi，差距达 3,125 倍，导致调度器无法找到可用节点", "manifestation": "Pod rc-pending-insufficient-memory 在 aiops-e2e 命名空间下持续 Pending 约 30 分钟，Events 含 FailedScheduling 警告 '0/3 nodes are available: 3 Insufficient memory'，无 nodeName 分配"}, "root_cause": "命名空间 aiops-e2e 下的 Pod rc-pending-insufficient-memory 处于 Pending 状态，根因是资源请求配置错误。该 Pod 的 memory request 被设置为 100000Gi（约 100TB），而集群中 3 个节点（master、node1、node2）的 allocatable 内存均仅为约 32,758 MiB（约 32Gi/节点）。Pod 请求量是单个节点容量的约 3,125 倍，任何节点都无法满足。调度器 FailedScheduling 事件明确报告 \"0/3 nodes are available: 3 Insufficient memory\"。Pod 无 nodeSelector/taint/affinity/PVC 等约束条件，排除了其他调度障碍。", "root_cause_summary": "命名空间 aiops-e2e 下的 Pod rc-pending-insufficient-memory 处于 Pending 状态，根因是资源请求配置错误。该 Pod 的 memory request 被设置为 100000Gi（约 100TB），而集群中 3 个节点（master、node1、node2）的 allocatable 内存均仅为约 32,758 MiB（约 32Gi/节点）。Pod 请求量是单个节点容量的约 3,125 倍，任何节点都无法满足。调度器 FailedScheduling 事件明确报告 \"0/3 nodes are available: 3 Insufficient memory\"。Pod 无 nodeSelector/taint/affinity/PVC 等约束条件，排除了其他调度障碍。", "confidence": 0.98, "confidence_reason": "直接证据充分：kubectl describe 确认 FailedScheduling 事件及内存不足原因（ev-001），kubectl get yaml + 资源查询直接获取到 Pod 请求内存为 100000Gi（ev-002），节点 allocatable 内存数据确认为约 32Gi/节点（ev-003）。三者形成完整因果链：配置错误 → 资源请求远超节点容量 → 所有节点无法满足 → FailedScheduling → Pending。排除了 nodeSelector/affinity/taint/PVC 等干扰因素。置信度 0.98。", "primary_runbooks": ["pod-pending-unschedulable.md"], "alternative_causes": [{"cause": "集群节点整体内存耗尽（非 Pod 配置问题）", "probability": "low", "reason": "节点 allocatable 内存为 32Gi，正常 Pod 请求不会导致所有节点不可用。且集群中其他 59 个 Pod 均为 Running 状态，说明节点仍有调度能力。"}, {"cause": "taint/nodeSelector/affinity 不匹配导致无可用节点", "probability": "low", "reason": "Pod YAML 显示 Node-Selectors: <none>，Tolerations 仅为默认的 node.kubernetes.io/not-ready 容忍，无其他约束，且 FailedScheduling 事件明确报告的是 'Insufficient memory' 而非节点选择约束不匹配。"}, {"cause": "PVC 未绑定导致 Pod 无法调度", "probability": "low", "reason": "Pod 只引用了 kube-api-access-c69j6（ServiceAccount token 卷），无 PVC 依赖，且事件未提及 PVC 相关错误。"}, {"cause": "历史 Pod rc-pending-insufficient-cpu 相关", "probability": "low", "reason": "该 Pod 因 CPU 不足无法调度且已进入删除流程，与当前内存不足问题相互独立，不会导致本 Pod 无法调度。"}], "limitations": "未采集每个节点上当前已分配内存的详细使用率（allocated vs allocatable），但基于 Pod 请求量 100,000Gi 与节点容量 32Gi 的极端差距，即使节点完全空闲也无法满足，不影响根因结论。未采集 Pod 的 QoS 类别细节（QoS Class: Burstable 已知），但这不影响根因判断。", "llm_raw_analysis": "分析过程：1) 证据清点：共 7 条证据，包括 Pod 描述、YAML 配置、节点资源、集群事件、上游验证结果。2) 逐条分析：ev-001 确认 Pending 状态和 FailedScheduling；ev-002 确认 Pod 请求 100000Gi 内存（约 100TB）；ev-003 确认节点仅 ~32Gi；ev-004 发现另一个历史异常 Pod 但与其独立。3) 关联分析：Pod 请求量（100000Gi）对比节点容量（32Gi）的极端差距是唯一解释。4) 因果链构建：配置错误（100000Gi request）→ 所有节点不可用（3 Insufficient memory）→ 调度失败 → Pending。5) 置信度评估：0.98，直接证据充分且干扰因素已排除。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 命名空间 aiops-e2e 下的 Pod rc-pending-insufficient-memory 处于 Pending 状态，根因是资源请求配置错误。该 Pod 的 memory request 被设置为 100000Gi（约 100TB），而集群中 3 个节点（master、node1、n...
   置信度: 98%
   🔗 因果链:
     根本原因: Pod rc-pending-insufficient-memory 的 resources.requests.memory 被错误配置为 100000Gi（约 100TB），远超集群任何节点的可用内存容量（~32Gi/节点）
     传导机制: kube-scheduler 评估该 Pod 的资源请求，发现 3 个节点的 allocatable 内存（均约 32Gi）均远小于 Pod 请求的 100,000Gi → 调度器标记所有节点为 'Insufficient memory' → 尝试 preemption（抢占）但无任何 Pod 能释放 100TB 内存 → 调度失败 → Pod 停留在 Pending 状态
     最终表现: Pod rc-pending-insufficient-memory 在 aiops-e2e 命名空间下持续 Pending 约 30 分钟，Events 含 FailedScheduling 警告 '0/3 nodes are available: 3 Insufficient memory'，无 nodeName 分配


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (25.4s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5743 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 38.7s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将为您生成一份详尽、完整的诊断报告。

---
## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | Pending / PendingUnschedulable |
| **兼容归因层** | L1 - 节点资源不足 |
| **问题分类** | 资源请求配置错误（内存资源请求远超集群容量） |
| **置信度** | 高 (98%) |
| **证据完整度** | 4/4 (100%) |

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| **问题Pod** | `rc-pending-insufficient-memory` (命名空间: `aiops-e2e`) |
| **Pod状态** | `Pending` |
| **Pod异常类型** | `PendingUnschedulable` |
| **集群节点数** | 3 (master, node1, node2) |
| **错误信息** | `FailedScheduling`: `0/3 nodes are available: 3 Insufficient memory.` |

**当前集群状态总结**：
- 集群中共有 **65** 个 Pod，其中 **59** 个运行正常，**1** 个异常。
- **唯一异常 Pod** 是 `rc-pending-insufficient-memory`，它因所有3个节点都报告“内存不足”而无法被调度，已处于 `Pending` 状态约 **30 分钟**。

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 当前状态 | `kubectl describe pod` | `Status: Pending` <br> `Warning FailedScheduling` <br> `0/3 nodes are available: 3 Insufficient memory.` | Pod 因所有节点内存不足无法调度。 |
| 2 | Pod 资源请求 | `kubectl get pod -o yaml` (通过 `jq`) | `"memory": "100000Gi"` | Pod 的 `resources.requests.memory` 被配置为 **100,000Gi** (约100TB)。 |
| 3 | 节点资源容量 | `bash` 命令 `kubectl get nodes -o json` (通过 `jq`) | master: `32758084Ki` (~32Gi) <br> node1: `32758076Ki` (~32Gi) <br> node2: `32758080Ki` (~32Gi) | 集群中 3 个节点的 `allocatable` 内存容量均为约 **32Gi**。 |
| 4 | 集群调度事件 | `kubectl get events` | 多个 `Warning FailedScheduling` 事件，原因均为 `Insufficient memory`。 | 调度器持续尝试并失败，所有节点都无法满足 Pod 的请求。 |

### 证据关联分析

-   **证据 #2 + 证据 #3 印证**：Pod 请求 `100,000Gi` (约 100TB) 内存，而集群中每个节点的可用内存仅有约 `32Gi`。Pod 的内存请求量是单个节点容量的约 **3,125倍**。这个巨大的差距是核心事实。
-   **证据链**：Pod 配置了极端的内存请求 (100,000Gi) → kube-scheduler 评估所有节点时发现，即使节点完全空闲，其可用内存 (约32Gi) 也远小于Pod请求值 → 所有节点均被标记为 `Insufficient memory` → Pod 调度失败，停留在 `Pending` 状态。

### 缺失证据

无。所有计划证据均已成功采集，完整度为100%，根因明确。

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                │
│ Pod `rc-pending-insufficient-memory` 的 `resources.requests.memory`      │
│ 被错误配置为 100,000Gi（约100TB），这是一个严重的配置错误。               │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                │
│ kube-scheduler 评估 Pod 资源请求 → 发现 3 个节点的 allocatable 内存       │
│ (均约 32Gi) 远小于 Pod 请求的 100,000Gi → 所有节点被标记为                │
│ `Insufficient memory` → 尝试抢占 (preemption) 但无 Pod 能释放 100TB      │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                │
│ 调度器在所有节点上均找不到足够的空闲内存来满足 Pod 的请求。              │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                            │
│ Pod 处于 `Pending` 状态，事件中包含 `FailedScheduling` 警告              │
│ "0/3 nodes are available: 3 Insufficient memory."                       │
└─────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2 (Pod 请求 100,000Gi 内存) 和证据 #3 (每个节点可用内存约 32Gi)，问题的根本原因是 Pod `rc-pending-insufficient-memory` 的 **`resources.requests.memory` 被错误配置为一个天文数字 (100,000Gi)**，远超整个集群的可用资源，导致调度器无法将其调度到任何节点上。

**置信度**：高 (98%)
- ✅ `FailedScheduling` 事件直接指向 `Insufficient memory`。
- ✅ 通过 `kubectl get yaml` 和 `jq` 命令，精确提取了 Pod 的 `memory request` 为 `100000Gi`。
- ✅ 通过 `run_bash_command` 命令，精确获取了所有节点的 `allocatable memory` 容量（均为约 32Gi）。
- ✅ 证据链清晰、完整，无其他干扰因素（Pod 无 `nodeSelector`, `taint`, `affinity` 或 `PVC` 依赖）。

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [核心] 修正 Pod 的内存资源请求**
需要将 `resources.requests.memory` 从 `100000Gi` 修改为合理的值。您需要根据应用的实际需求修改其部署配置。

如果此 Pod 由 Deployment 管理，请使用以下命令：
```bash
# 首先找到管理此 Pod 的 Deployment
# kubectl get pod rc-pending-insufficient-memory -n aiops-e2e -o yaml | grep 'ownerReferences' -A 5

# 假设 Deployment 名称是 rc-pending-insufficient-memory（或类似）
# 将其 request memory 修改为 4Gi（示例值，请根据实际应用调整）
kubectl set resources deployment/rc-pending-insufficient-memory -n aiops-e2e --requests=memory=4Gi
```
*依据*：当前请求 100,000Gi 是配置错误，必须将其修改为合理的值（例如 4Gi）以使其能被调度。

**2. [可选] 先删除 Pod，待资源配置修正后自动重建**
如果修正资源请求后 Pod 未自动重建，可以手动删除它，由控制器重建。
```bash
kubectl delete pod rc-pending-insufficient-memory -n aiops-e2e
```
*注意*：此命令会删除 Pod，如果它是 Deployment 的一部分，控制器会用新的资源配置重新创建它。

### 后续优化

1.  **审查资源清单**：检查创建此 Pod 的 YAML 文件或 Helm Chart，确认 `resources.requests.memory` 设置正确，避免类似错误再次发生。
2.  **实施资源配额 (ResourceQuota)**：在命名空间 `aiops-e2e` 上设置 ResourceQuota，限制单个 Pod 或者所有 Pod 的总资源请求上限，防止“一颗老鼠屎坏了一锅粥”的情况发生。
    ```bash
    # 示例：为命名空间设置配额
    cat <<EOF | kubectl apply -f -
    apiVersion: v1
    kind: ResourceQuota
    metadata:
      name: memory-quota
      namespace: aiops-e2e
    spec:
      hard:
        requests.memory: "200Gi"
        limits.memory: "300Gi"
    EOF
    ```
3.  **强化变更管理**：在 CI/CD 环境中，可以通过策略即代码（如 OPA/Gatekeeper）来校验 Pod 的 `resources.requests` 是否在合理范围内，从源头杜绝此类配置错误。

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 查看 Pod 状态 | `kubectl get pod rc-pending-insufficient-memory -n aiops-e2e` | STATUS 列变为 `Running` 或至少不再是 `Pending` |
| 2. 检查调度事件 | `kubectl describe pod rc-pending-insufficient-memory -n aiops-e2e` | Events 中不再显示 `FailedScheduling` 且 STATUS 为 `Running` |

## ⚠️ 注意事项
-   本次问题完全是由于**人为配置错误**导致，并非集群资源本身不足。集群的 59 个 Running Pod 证明了集群资源在正常使用下是充足的。
-   `100000Gi` 的值明显是一个笔误（例如可能是 `100Gi` 或 `100Mi` 被写成了 `100000Gi`），请务必确认修改后的正确值。

---

## 📊 性能统计

├─ 总耗时: 1.6m
├─ 问题定位: 21.1s (21%) ✅
├─ 证据链采集: 25.9s (26%) ✅
├─ 根因分析: 26.2s (27%) ✅
├─ 汇总总结: 25.4s (26%) ✅
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
