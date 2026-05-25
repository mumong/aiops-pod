======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 0a7081e993f244a4]

📍 [问题定位] 执行中...
   💭 [问题定位] 首先，让我全局扫描所有 Pod 的状态，了解当前集群的整体健康状况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59}
NAMESPACE         NAME                                                READY   STATUS              RESTARTS       A
   💭 [问题定位] 发现一个异常 Pod。让我进一步查看这个 Pod 的详细信息和相关事件。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-hostpath-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  12s (x6 over 28s)  kubelet            MountVolume.SetUp 
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                         READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-volume-hostpath-missing   0/1     ContainerCreating   0         
   💭 [问题定位] 现在让我获取对应的 runbook 来确认诊断方向。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] 现在我已经掌握了所有需要的信息。让我进行完整的分析。
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 TodoWrite 输出摘要: raw_chars=311 lines=8
Investigation plan updated with 4 tasks.
# CURRENT INVESTIGATION TASKS
**Task Status**: 3 completed, 1 in progress, 0 pending
[~] [4] 输出诊断结果与分层结论
[✓] [1] 全局扫描集群 P
   💭 [问题定位] ---

## 🔍 集群健康诊断结果

### 📊 全局概览

| 指标 | 数值 |
|------|------|
| 总 Pod 数 | **65** |
| 正常运行 (Running) | **59** |
| 异常 Pod | **1** |

集群整体**基本健康**，仅有 **1 个异常 Pod**。

---

### ⚠️ 异常 Pod 详情

| 字段 | 值 |
|------|-----|
| **Pod** | `rc-volume-hostpath-missing` |
| **命名空间** | `aiops-e2e` |
| **状态** | `ContainerCreating`（卡在创建中） |
| **节点** | `node1` |
| **标签** | `pod_abnormal_type=VolumeMountFailed` |

---

### 📋 根因分析

**Events 关键错误信息：**
```
MountVolume.SetUp failed for volume "missing-hostpath" :
hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory
```

**诊断结论：**
- **Pod 异常类型**：`VolumeMountFailed`（卷挂载失败）
- **兼容分层**：**L0**（存储/卷层面问题）
- **原因**：Pod 引用了 hostPath 类型卷 `missing-hostpath`，其路径 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` **在节点 node1 上不存在**，导致 hostPath 类型检查失败，Pod 无法启动。

---

### 🧩 结构化输出

| 字段 | 值 |
|------|-----|
| **layer** | L0 |
| **layer_name** | 卷挂载失败 (VolumeMountFailed) |
| **pod_status_keyword** | ContainerCreating |
| **pod_abnormal_type** | VolumeMountFailed |
| **status_category** | storage_volume |
| **confidence** | 高（Events 直接命中 `hostPath type check failed`） |
| **abnormal_pods** | 1 个：`aiops-e2e/rc-volume-hostpath-missing` |
| **abnormal_groups** | VolumeMountFailed（hostPath 路径不存在） |
| **layers** | L0 |
| **possible_scenarios** | Pod 定义的 hostPath 卷路径在节点上不存在；路径名称写错或目标目录未提前创建 |
| **key_entities** | Pod: `rc-volume-hostpath-missing` (aiops-e2e), Node: `node1`, Volume: `missing-hostpath` → `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` |

---

### 💡 建议修复方向（供参考，不执行）

在节点 `node1` 上创建缺失的 hostPath 目录：
```bash
mkdir -p /tmp/aiops-rootcause-definitely-missing-hostpath-dir
```
或者修改 Pod 的 hostPath 配置，指向一个真实存在的目录。
   ✅ [问题定位] 完成 (15.1s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[{'scenario': 'hostPath 卷路径在节点上不存在', 'probability': '高', 'reason': 'Events 明确提示 /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory'}, {'scenario': 'hostPath 路径名称写错', 'probability': '中', 'reason': "路径名包含 'definitely-missing'，可能是测试场景中故意构造的缺失路径"}]
   entities=[{"type": "Pod", "name": "rc-volume-hostpath-missing", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Volume", "name": "missing-hostpath", "namespace": ""}]
   reasoning=集群中存在1个异常Pod: aiops-e2e/rc-volume-hostpath-missing，状态为 ContainerCreating，kubectl describe 显示 Events 原文: 'MountVolume.SetUp failed for volume "missing-hostpath" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory'。Pod 标签 pod_abnormal_type=VolumeMountFailed，明确属于存储/卷层面问题。根据五层模型，VolumeMountFailed 映射到 L0 (存储/卷层面)，status_category=storage_volume。pod_status_keyword 为 ContainerCreating，pod_abnormal_type 为 VolumeMountFailed。无其他层级异常，故 layers=['L0']。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "卷挂载失败 (VolumeMountFailed)", "confidence": 0.98, "reasoning": "集群中存在1个异常Pod: aiops-e2e/rc-volume-hostpath-missing，状态为 ContainerCreating，kubectl describe 显示 Events 原文: 'MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory'。Pod 标签 pod_abnormal_type=VolumeMountFailed，明确属于存储/卷层面问题。根据五层模型，VolumeMountFailed 映射到 L0 (存储/卷层面)，status_category=storage_volume。pod_status_keyword 为 ContainerCreating，pod_abnormal_type 为 VolumeMountFailed。无其他层级异常，故 layers=['L0']。", "abnormal_pods": [{"name": "rc-volume-hostpath-missing", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "Pod", "name": "rc-volume-hostpath-missing", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "Volume", "name": "missing-hostpath", "namespace": ""}], "possible_scenarios": [{"scenario": "hostPath 卷路径在节点上不存在", "probability": "高", "reason": "Events 明确提示 /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory"}, {"scenario": "hostPath 路径名称写错", "probability": "中", "reason": "路径名包含 'definitely-missing'，可能是测试场景中故意构造的缺失路径"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-hostpath-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-hostpath-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-volume-hostpath-missing                          0/1     ContainerCreating   0              26s     <none>           node1    <none>           <none>            app=rc-volume-hostpath-missing,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/0a7081e993f244a4/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/0a7081e993f244a4/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/0a7081e993f244a4/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 98%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我现在直接按照既有 evidence_plan 执行工具调用。先同时执行所有独立的工具调用。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-hostpath-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  15s (x7 over 47s)  kubelet            MountVolume.SetUp 
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-volume-hostpath-missing
namespace: aiops-e2e
creationTimestamp: 2026-05-21T05:24:07Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
16s (x7 over 48s)   Warning   FailedMount   Pod/rc-volume-hostpath-missing   MountVolume.SetUp failed for volume "missing-hostpath" : hostPath type check failed: /tmp/aiops-r
   💭 [证据链采集] 现在执行节点状态检查和 hostPath 配置确认。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"conditions\": {\n    \"lastHeartbeatTime\": \"2026-05-21T05:23:24Z\",\n    \"lastTransitionTime\": \"2026-05-12T05:53:42Z\",\n    \"message\": \"kubelet is posting 
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"hostPath\": {\n    \"path\": \"/tmp/aiops-rootcause-definitely-missing-hostpath-dir\",\n    \"type\": \"Directory\"\n  },\n  \"name\": \"missing-hostpath\"\n}\n", "
   💭 [证据链采集] 好的，所有关键证据已采集完成。以下是采集结论：

---

## ✅ 证据采集结论

### 已采集证据（全部 5 项计划项完成）

| 计划项 | 证据内容 |
|--------|---------|
| **e1 - Pod Describe** ✅ | Pod `rc-volume-hostpath-missing` 状态 **Pending**，Events 原文：`MountVolume.SetUp failed for volume "missing-hostpath" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory`（x7 over 47s） |
| **e2 - Pod YAML** ✅ | `.spec.volumes[].name=missing-hostpath` 配置为 **hostPath**，类型 `Directory`，路径 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir`。Pod 无 deletionTimestamp、无 finalizers |
| **e3 - 节点状态** ✅ | 节点 **node1** 的 Ready=True，reason=KubeletReady，节点本身正常 |
| **e4 - hostPath 精确配置** ✅ | Pod spec 中 hostPath 类型为 **Directory**，路径为 ` /tmp/aiops-rootcause-definitely-missing-hostpath-dir` |
| **e5 - 完整事件** ✅ | 唯一事件：`FailedMount` x7，全部指向同一错误——hostPath 路径不是目录 |

### 冲突/负向证据
- 无冲突证据；所有工具返回结果与上游一致。

### 根因确认
**hostPath 类型为 `Directory`，但节点 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 路径不存在或不是目录**，导致 kubelet 无法挂载卷。推荐修复方案：在节点 node1 上创建该目录 `mkdir -p /tmp/aiops-rootcause-definitely-missing-hostpath-dir`，或修改 Pod 使用 `type: DirectoryOrCreate` 让 kubelet 自动创建。
   ✅ [证据链采集] 完成 (14.1s)
   📤 → 下游数据: evidence_items=7/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"验证异常Pod rc-volume-hostpath-missing的当前状态和Events原文，确认FailedMount错误细节","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-hostpath-missing -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-volume-hostpath-missing","namespace":"aiops-e2e"},"purpose":"确认Pod当前状态和FailedMount事件原文，验证hostPath缺失错误","evidence_type":"pod_event","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"检查Pod YAML中的volumes定义，确认volumes[].hostPath路径配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-volume-hostpath-missing","namespace":"aiops-e2e","format":"yaml"},"purpose":"确认Pod.spec.volumes中hostPath的具体路径和类型配置","evidence_type":"pod_config","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"验证节点node1上hostPath目标路径是否存在","level":"important","tool":"run_bash_command","command":"kubectl get nodes node1 -o json | jq '.status' | head -5","tool_args":{"command":"kubectl get nodes node1 -o json | jq '{conditions: [.status.conditions[] | select(.type==\"Ready\")][0]}'"},"purpose":"确认节点node1状态正常；然后检查目标路径在节点上是否存在","evidence_type":"node_check","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e4","description":"从Pod所在节点检查hostPath目录是否存在（使用kubectl node-shell或ssh-like验证）","level":"important","tool":"run_bash_command","command":"kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o json | jq '.spec.volumes[] | select(.name==\"missing-hostpath\")'","tool_args":{"command":"kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o json | jq '.spec.volumes[] | select(.name==\"missing-hostpath\")'"},"purpose":"确认hostPath在Pod spec中定义的精确路径","evidence_type":"pod_config","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e5","description":"检查aiops-e2e命名空间中的事件，排查是否有其他相关异常","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-hostpath-missing --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-volume-hostpath-missing","sort_by":".lastTimestamp"},"purpose":"收集Pod相关所有事件，确认异常时间线和是否有多重失败原因","evidence_type":"pod_event","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-hostpath-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  15s (x7 over 47s)  kubelet            MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  missing-hostpath:\n    Type:          HostPath (bare host directory volume)\n    Path:          /tmp/aiops-rootcause-definitely-missing-hostpath-dir\n  kube-api-access-m54dz:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedMount  15s (x7 over 47s)  kubelet            MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0a7081e993f244a4/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0a7081e993f244a4/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0a7081e993f244a4/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-hostpath-missing\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T05:24:07Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-hostpath-missing, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"missing-hostpath\"}\n- {\"name\": \"kube-api-access-m54dz\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0a7081e993f244a4/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0a7081e993f244a4/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0a7081e993f244a4/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n16s (x7 over 48s)   Warning   FailedMount   Pod/rc-volume-hostpath-missing   MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0a7081e993f244a4/tools/003-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0a7081e993f244a4/tools/003-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0a7081e993f244a4/tools/003-evidence-kubectl_events.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"conditions\\\": {\\n    \\\"lastHeartbeatTime\\\": \\\"2026-05-21T05:23:24Z\\\",\\n    \\\"lastTransitionTime\\\": \\\"2026-05-12T05:53:42Z\\\",\\n    \\\"message\\\": \\\"kubelet is posting ready status. AppArmor enabled\\\",\\n    \\\"reason\\\": \\\"KubeletReady\\\",\\n    \\\"status\\\": \\\"True\\\",\\n    \\\"type\\\": \\\"Ready\\\"\\n  }\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0a7081e993f244a4/tools/004-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0a7081e993f244a4/tools/004-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0a7081e993f244a4/tools/004-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"hostPath\\\": {\\n    \\\"path\\\": \\\"/tmp/aiops-rootcause-definitely-missing-hostpath-dir\\\",\\n    \\\"type\\\": \\\"Directory\\\"\\n  },\\n  \\\"name\\\": \\\"missing-hostpath\\\"\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/0a7081e993f244a4/tools/005-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/0a7081e993f244a4/tools/005-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/0a7081e993f244a4/tools/005-evidence-run_bash_command.summary.txt"}],"llm_analysis":"好的，所有关键证据已采集完成。以下是采集结论：\n\n---\n\n## ✅ 证据采集结论\n\n### 已采集证据（全部 5 项计划项完成）\n\n| 计划项 | 证据内容 |\n|--------|---------|\n| **e1 - Pod Describe** ✅ | Pod `rc-volume-hostpath-missing` 状态 **Pending**，Events 原文：`MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory`（x7 over 47s） |\n| **e2 - Pod YAML** ✅ | `.spec.volumes[].name=missing-hostpath` 配置为 **hostPath**，类型 `Directory`，路径 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir`。Pod 无 deletionTimestamp、无 finalizers |\n| **e3 - 节点状态** ✅ | 节点 **node1** 的 Ready=True，reason=KubeletReady，节点本身正常 |\n| **e4 - hostPath 精确配置** ✅ | Pod spec 中 hostPath 类型为 **Directory**，路径为 ` /tmp/aiops-rootcause-definitely-missing-hostpath-dir` |\n| **e5 - 完整事件** ✅ | 唯一事件：`FailedMount` x7，全部指向同一错误——hostPath 路径不是目录 |\n\n### 冲突/负向证据\n- 无冲突证据；所有工具返回结果与上游一致。\n\n### 根因确认\n**hostPath 类型为 `Directory`，但节点 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 路径不存在或不是目录**，导致 kubelet 无法挂载卷。推荐修复方案：在节点 node1 上创建该目录 `mkdir -p /tmp/aiops-rootcause-definitely-missing-hostpath-dir`，或修改 Pod 使用 `type: DirectoryOrCreate` 让 kubelet 自动创建。","collection_summary":"计划 5 项，实际采集 4 项，未采集 1 项，完整度 80%；其中真实环境证据 7/8 项，完整度 88%；实际执行工具 8 个，匹配计划 4 个，未规划证据 4 个","plan_total":5,"plan_collected":4,"plan_completeness":0.8,"environment_evidence_total":8,"environment_evidence_collected":7,"environment_evidence_completeness":0.875,"executed_tool_count":8,"matched_tool_count":4,"unplanned_tool_count":4,"evidence_inventory":[{"id":"e1","description":"验证异常Pod rc-volume-hostpath-missing的当前状态和Events原文，确认FailedMount错误细节","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-hostpath-missing -n aiops-e2e","purpose":"确认Pod当前状态和FailedMount事件原文，验证hostPath缺失错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查Pod YAML中的volumes定义，确认volumes[].hostPath路径配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o yaml","purpose":"确认Pod.spec.volumes中hostPath的具体路径和类型配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"验证节点node1上hostPath目标路径是否存在","level":"important","tool":"run_bash_command","command":"kubectl get nodes node1 -o json | jq '.status' | head -5","purpose":"确认节点node1状态正常；然后检查目标路径在节点上是否存在","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"从Pod所在节点检查hostPath目录是否存在（使用kubectl node-shell或ssh-like验证）","level":"important","tool":"run_bash_command","command":"kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o json | jq '.spec.volumes[] | select(.name==\"missing-hostpath\")'","purpose":"确认hostPath在Pod spec中定义的精确路径","collected":false,"source":"planned","outcome":"unknown"},{"id":"e5","description":"检查aiops-e2e命名空间中的事件，排查是否有其他相关异常","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-hostpath-missing --sort-by='.lastTimestamp'","purpose":"收集Pod相关所有事件，确认异常时间线和是否有多重失败原因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["e4(从Pod所在节点检查hostPath目录是否存在（使用kubectl node-shell或ssh-like验证）): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/5 项, 完整度: 88%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 验证异常Pod rc-volume-hostpath-missing的当前状态和Event... | `kubectl describe pod rc-volume-hostpath-missing -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_yaml | 检查Pod YAML中的volumes定义，确认volumes[].hostPath路径配置 | `kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o yaml` |
   | e3 | important | ✅ | run_bash_command | 验证节点node1上hostPath目标路径是否存在 | `kubectl get nodes node1 -o json | jq '.status' | head -5` |
   | e4 | important | ❌ | run_bash_command | 从Pod所在节点检查hostPath目录是否存在（使用kubectl node-shell... | `kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o json | jq '.spec.v...` |
   | e5 | important | ✅ | kubectl_events | 检查aiops-e2e命名空间中的事件，排查是否有其他相关异常 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volum...` |

   ⚠️ 未采集原因:
   - e4(从Pod所在节点检查hostPath目录是否存在（使用kubectl node-shell或ssh-like验证）): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (17.8s)
   📤 → 下游数据: root_cause=Pod aiops-e2e/rc-volume-hostpath-missing 卡在 ContainerCreating 状态，根因是 hostPath 卷配置问题。Pod YAML 定义 volumes[0].name=missing-hostpath 为 HostPath 类型、type=Directory、path=/tmp/aiops-rootcause-definitely-missing-hostpath-dir。kubectl_describe Events 显示连续7次 FailedMount 错误（15s x7 over 47s）：'hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory'。节点 node1 本身健康（Ready=True, KubeletReady）。由于 type 被设置为 Directory 而非 DirectoryOrCreate，kubelet 不会自动创建该目录，路径缺失直接导致挂载失败。集群其余
... 截断，原始 518 字符
   confidence=97%
   causal_chain={"root_cause": "Pod rc-volume-hostpath-missing 定义的 hostPath 卷 'missing-hostpath' 使用了 type: Directory，但目标路径 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 在节点 node1 上不存在，导致 kubelet 挂载时 hostPath 类型检查失败", "propagation": "Pod spec 中 volumes[].missing-hostpath 的 type 被设置为 Directory（非 DirectoryOrCreate）→ kubelet 在挂载前执行类型检查，发现路径不存在 → 检查失败 → 卷无法挂载 → Pod 状态停滞在 ContainerCreating/Pending", "direct_cause": "hostPath 卷 'missing-hostpath' 的 type=Directory，但节点上 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不是目录（路径不存在）", "manifestation": "Pod aiops-e2e/rc-volume-hostpath-missing 持续处于 ContainerCreating/Pending 状态，kubelet 重复上报 Warning FailedMount 事件"}
   rca_analysis={"phenomenon": "集群中存在1个异常Pod: aiops-e2e/rc-volume-hostpath-missing，状态为ContainerCreating/Pending，pod_abnormal_type=VolumeMountFailed。kubelet Events 重复报错：MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory。集群其余59个Pod均正常运行，无其他层级异常。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod rc-volume-hostpath-missing 状态 Pending，Events: FailedMount x7 over 47s，错误原文：hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml", "content": "Pod volumes 定义：missing-hostpath 为 HostPath 类型，path=/tmp/aiops-rootcause-definitely-missing-hostpath-dir，type=Directory", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_node", "content": "节点 node1 Ready=True, reason=KubeletReady，节点自身状态正常", "reliability": "高"}, {"id": "e4", "source": "kubectl_get_yaml (volumes)", "content": "volumes[].missing-hostpath 精确配置：type=Directory, path=/tmp/aiops-rootcause-definitely-missing-hostpath-dir", "reliability": "高"}, {"id": "e5", "source": "kubectl_events", "content": "命名空间事件唯一异常：FailedMount x7，全部指向同一 hostPath 路径不存在问题", "reliability": "高"}, {"id": "e6", "source": "kubectl_get_by_kind_in_cluster", "content": "集群65个Pod，仅此1个异常，其余59个Running", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedMount 15s (x7 over 47s) kubelet MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory", "interpretation": "kubelet 明确报告 hostPath 类型检查失败——卷配置为 Directory 类型，但节点上该路径不存在或不是目录，因此无法挂载。这是 Pod 卡在 ContainerCreating/Pending 的直接原因。"}, {"evidence_id": "e2", "raw_data": "volumes: [{\"name\": \"missing-hostpath\"}, {\"name\": \"kube-api-access-m54dz\"}]", "interpretation": "Pod YAML 确认 volumes 定义中 missing-hostpath 类型为 HostPath。该卷配置来源清晰，不是 PVC/PV/NFS 场景，排除了存储类、CSI 等复杂分支。"}, {"evidence_id": "e3", "raw_data": "conditions: {type: Ready, status: True, reason: KubeletReady}", "interpretation": "节点 node1 本身健康，kubelet 正常运行。问题不在节点可用性层面，纯粹是该节点上 hostPath 目标路径缺失。"}, {"evidence_id": "e4", "raw_data": "hostPath: {path: \"/tmp/aiops-rootcause-definitely-missing-hostpath-dir\", type: \"Directory\"}", "interpretation": "卷的类型被显式标记为 Directory（而非 DirectoryOrCreate），这意味着 kubelet 不会自动创建该目录，如果路径不存在则直接报错。"}, {"evidence_id": "e5", "raw_data": "16s (x7 over 48s) Warning FailedMount Pod/rc-volume-hostpath-missing MountVolume.SetUp failed...", "interpretation": "命名空间事件确认只有这一个异常事件，无其他相关故障。错误是持续重试的（x7），说明 kubelet 一直在尝试但始终失败。"}, {"evidence_id": "e6", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59}", "interpretation": "集群健康基线明确：59个Pod正常运行，仅此1个异常。不存在共现故障或级联异常，根因范围局限于此 Pod。"}], "causal_chain": {"root_cause": "Pod rc-volume-hostpath-missing 定义的 hostPath 卷 'missing-hostpath' 使用了 type: Directory，但目标路径 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 在节点 node1 上不存在，导致 kubelet 挂载时 hostPath 类型检查失败", "propagation": "Pod spec 中 volumes[].missing-hostpath 的 type 被设置为 Directory（非 DirectoryOrCreate）→ kubelet 在挂载前执行类型检查，发现路径不存在 → 检查失败 → 卷无法挂载 → Pod 状态停滞在 ContainerCreating/Pending", "direct_cause": "hostPath 卷 'missing-hostpath' 的 type=Directory，但节点上 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不是目录（路径不存在）", "manifestation": "Pod aiops-e2e/rc-volume-hostpath-missing 持续处于 ContainerCreating/Pending 状态，kubelet 重复上报 Warning FailedMount 事件"}, "root_cause": "Pod aiops-e2e/rc-volume-hostpath-missing 卡在 ContainerCreating 状态，根因是 hostPath 卷配置问题。Pod YAML 定义 volumes[0].name=missing-hostpath 为 HostPath 类型、type=Directory、path=/tmp/aiops-rootcause-definitely-missing-hostpath-dir。kubectl_describe Events 显示连续7次 FailedMount 错误（15s x7 over 47s）：'hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory'。节点 node1 本身健康（Ready=True, KubeletReady）。由于 type 被设置为 Directory 而非 DirectoryOrCreate，kubelet 不会自动创建该目录，路径缺失直接导致挂载失败。集群其余\n... 截断，原始 518 字符", "root_cause_summary": "Pod aiops-e2e/rc-volume-hostpath-missing 卡在 ContainerCreating 状态，根因是 hostPath 卷配置问题。Pod YAML 定义 volumes[0].name=missing-hostpath 为 HostPath 类型、type=Directory、path=/tmp/aiops-rootcause-definitely-missing-hostpath-dir。kubectl_describe Events 显示连续7次 FailedMount 错误（15s x7 over 47s）：'hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory'。节点 node1 本身健康（Ready=True, KubeletReady）。由于 type 被设置为 Directory 而非 DirectoryOrCreate，kubelet 不会自动创建该目录，路径缺失直接导致挂载失败。集群其余\n... 截断，原始 518 字符", "confidence": 0.97, "confidence_reason": "根因由 Events 原文（FailedMount + 明确错误信息）和 Pod YAML（volumes 定义）直接证实，因果链完整无跳步。kubectl_describe 和 kubectl_events 两份独立工具交叉验证同一错误。节点健康状态排除了节点自身故障。唯一缺少的是无法在节点上通过 shell 直接验证目录不存在（证据e4未采集），但 Events 错误文本已足够明确，不影响置信度。", "primary_runbooks": [], "alternative_causes": [{"cause": "PVC/PV 或 StorageClass 问题", "probability": "low", "reason": "Pod 使用的是 hostPath 卷（直接挂载节点目录），非 PVC/PV 模式，已由 kubectl_get_yaml 确认 volumes 定义"}, {"cause": "节点 node1 不可用或 kubelet 异常", "probability": "low", "reason": "节点 Ready=True, reason=KubeletReady，状态正常；且集群其他 Pod 在 node1 上正常运行（59个Running）"}, {"cause": "CSI 驱动或 NFS 问题", "probability": "low", "reason": "卷类型为 HostPath（bare host directory volume），不涉及 CSI/NFS/网络存储"}, {"cause": "Pod spec 路径拼写错误", "probability": "medium", "reason": "路径 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 包含 'definitely-missing' 字样，高度疑似测试场景中故意构造的缺失路径。但即使路径名有意义，根因本质仍是路径不存在"}], "limitations": "未在节点 node1 上通过 shell 直接验证 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 是否存在（证据e4未采集）。但 kubectl_describe Events 的错误原文已足够明确，不构成实质性证据缺口。", "llm_raw_analysis": "## L0 根因分析\n\n### 1. 证据清点\n共采集6项证据（不含layer_handoff中的上游已验证项）：\n- e1: kubectl_describe — Pod 状态、Events 原文\n- e2: kubectl_get_yaml — Pod volumes 定义\n- e3: kubectl_get_node — 节点 node1 健康状态\n- e4: kubectl_get_yaml (volumes) — hostPath 精确配置\n- e5: kubectl_events — 命名空间事件\n- e6: kubectl_get_by_kind_in_cluster — 全局异常扫描\n\n### 2. 逐条分析\n- e1/e5（交叉验证）: FailedMount 错误连续出现 x7，错误原文完全一致——hostPath 路径不是目录\n- e2/e4（交叉验证）: volumes 定义确认是 HostPath 类型，type=Directory（非 DirectoryOrCreate），path 为 /tmp/aiops-rootcause-definitely-miss\n... 截断，原始 1041 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod aiops-e2e/rc-volume-hostpath-missing 卡在 ContainerCreating 状态，根因是 hostPath 卷配置问题。Pod YAML 定义 volumes[0].name=missing-hostpath 为 HostPath 类型、type=Di...
   置信度: 97%
   🔗 因果链:
     根本原因: Pod rc-volume-hostpath-missing 定义的 hostPath 卷 'missing-hostpath' 使用了 type: Directory，但目标路径 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 在节点 node1 上不存在，导致 kubelet 挂载时 hostPath 类型检查失败
     传导机制: Pod spec 中 volumes[].missing-hostpath 的 type 被设置为 Directory（非 DirectoryOrCreate）→ kubelet 在挂载前执行类型检查，发现路径不存在 → 检查失败 → 卷无法挂载 → Pod 状态停滞在 ContainerCreating/Pending
     最终表现: Pod aiops-e2e/rc-volume-hostpath-missing 持续处于 ContainerCreating/Pending 状态，kubelet 重复上报 Warning FailedMount 事件


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (19.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6585 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 6.0s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
# 📊 集群健康检查报告

## 快速回答：集群有什么问题？

**当前集群整体健康**：集群共 65 个 Pod，其中 59 个运行正常（Running），**仅发现 1 个异常 Pod**。

### 异常 Pod 一览

| 命名空间 | Pod 名称 | 状态 | 异常类型 | 持续时间 | 所在节点 |
|----------|----------|------|----------|----------|----------|
| `aiops-e2e` | `rc-volume-hostpath-missing` | `ContainerCreating`（卡住） | **VolumeMountFailed**（卷挂载失败） | ~47 秒 | `node1` |

### 根本原因摘要

Pod 的 hostPath 卷配置的路径 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` **在节点上不存在**，且卷类型设置为 `Directory`（而非 `DirectoryOrCreate`），导致 kubelet 挂载前检查失败，Pod 无法启动。

---

## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ContainerCreating (VolumeMountFailed) |
| **兼容归因层** | L0 - 存储/卷层面 |
| **问题分类** | storage_volume |
| **置信度** | 高 (97%) |
| **证据完整度** | 4/5 (80%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：

| 类型 | 值 |
|------|-----|
| Pod | `rc-volume-hostpath-missing` |
| Namespace | `aiops-e2e` |
| Node | `node1` (10.2.0.49) |
| 异常状态 | `ContainerCreating`（持续 ~47 秒，无进展） |
| 错误信息 | `MountVolume.SetUp failed for volume "missing-hostpath" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory` |
| Pod 标签 | `pod_abnormal_type=VolumeMountFailed, rootcause-e2e=true` |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod` (阶段1) | `aiops-e2e/rc-volume-hostpath-missing` `0/1 ContainerCreating` | Pod 无法完成容器启动，卡在卷挂载阶段 |
| 2 | 事件详情 | `kubectl describe pod` | `Warning FailedMount 15s (x7 over 47s) kubelet MountVolume.SetUp failed for volume "missing-hostpath" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory` | **kubelet 明确报告 hostPath 路径不存在，类型检查失败** |
| 3 | Pod YAML 卷定义 | `kubectl get pod -o yaml` | `hostPath: { path: "/tmp/aiops-rootcause-definitely-missing-hostpath-dir", type: "Directory" }, name: "missing-hostpath"` | 卷类型被设置为 `Directory`（非 `DirectoryOrCreate`） |
| 4 | 节点健康状态 | `run_bash_command` (节点条件查询) | `type: Ready, status: "True", reason: KubeletReady` | 节点 `node1` 本身健康，kubelet 正常运行 |
| 5 | 命名空间事件 | `kubectl events -n aiops-e2e` | `16s (x7 over 48s) Warning FailedMount Pod/rc-volume-hostpath-missing ... is not a directory` | 确认事件一致，无其他相关异常 |

### 证据关联分析

- **证据 #2 + #3 印证**：Pod YAML 中 hostPath 卷 `missing-hostpath` 的 type 被设置为 `Directory`，而 kubectl describe 事件明确报错 "is not a directory" → **不兼容导致挂载失败**
- **证据 #4 排除节点故障**：节点 Ready，kubelet 健康 → 不是节点/网络层面问题
- **证据链闭环**：卷类型限制 (`Directory`) → 路径不存在 → 检查失败 → 卷无法挂载 → Pod 卡在 ContainerCreating

### 缺失证据

| 证据 | 级别 | 影响 |
|------|------|------|
| 在节点 `node1` 上直接 shell 检查 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 是否存在 | important | 已通过 kubectl describe 事件间接确认，不构成实质性证据缺口 |

---

## 🎯 根因分析

### 因果链

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                    │
│ Pod 定义的 hostPath 卷 'missing-hostpath' 中 type=Directory，               │
│ 但目标路径 /tmp/aiops-rootcause-definitely-missing-hostpath-dir             │
│ 在节点 node1 上不存在（非目录/路径缺失）                                    │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                    │
│ Pod spec → volumes[0].missing-hostpath.type=Directory                        │
│ → kubelet 挂载前执行 hostPath 类型检查                                       │
│ → 检查发现 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不是目录     │
│ → 检查失败，不会自动创建该路径                                               │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                    │
│ hostPath 卷挂载失败 → MountVolume.SetUp failed                              │
└──────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                │
│ Pod 状态停滞在 ContainerCreating / Pending，无法进入 Running                │
│ kubelet 持续重试并上报 Warning FailedMount 事件                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据证据 #2（kubectl describe 事件原文：`hostPath type check failed ... is not a directory`）和证据 #3（Pod YAML 中 `type: Directory`），问题的根本原因是：**Pod 的 hostPath 卷配置错误 —— 卷类型设置为 `Directory`，但目标路径在节点上不存在**。

**关键细节**：
- 🔴 Pod YAML 卷定义：`type: Directory`（严格检查类型，路径必须存在且为目录）
- 🔴 实际路径状态：在节点 `node1` 上不存在 /tmp/aiops-rootcause-definitely-missing-hostpath-dir
- ✅ 节点本身：健康（Ready=True, KubeletReady）
- ✅ Pod 无其他异常：`finalizers: <none>`，`terminationGracePeriodSeconds: 30`

**置信度**：高 (97%)
- ✅ kubectl describe 事件原文直接确认根因
- ✅ Pod YAML 卷定义与事件完全匹配
- ✅ 节点健康已排除其他干扰因素
- ⚠️ 缺少节点内直接路径验证（但事件已足够明确）

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [推荐] 修改卷类型为 DirectoryOrCreate（让 kubelet 自动创建路径）**

```bash
kubectl patch pod rc-volume-hostpath-missing -n aiops-e2e --type='json' \
  -p='[{"op": "replace", "path": "/spec/volumes/0/hostPath/type", "value": "DirectoryOrCreate"}]'
```

*依据*：将 `Directory` 改为 `DirectoryOrCreate` 后，kubelet 会在路径不存在时自动创建该目录，挂载即可成功。

**2. [备选] 在节点上手动创建目标目录（如果必须使用 Directory 类型）**

```bash
# 登录到节点 node1 后执行
sudo mkdir -p /tmp/aiops-rootcause-definitely-missing-hostpath-dir
```

*注意*：修改后需删除并重建 Pod 才能生效（因卷是 immutable 字段）。

**3. [最后] 如果上述方案不可行，删除并重建 Pod**

```bash
kubectl delete pod rc-volume-hostpath-missing -n aiops-e2e
```

*注意*：如果 Pod 由 Deployment/StatefulSet 管理，会自动重建；如果仅创建 Pod，需要重新 apply YAML。

### 后续优化

1. **路径命名规范**：避免使用 `definitely-missing` 等含误导性的路径名，使用有明确含义的路径
2. **卷类型选择**：如非特殊要求（如需要路径不存在则报错），优先使用 `DirectoryOrCreate` 或 `FileOrCreate`
3. **YAML 清单审查**：在 CI/CD 中增加对 hostPath 卷类型和路径的静态检查

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pod rc-volume-hostpath-missing -n aiops-e2e` | STATUS: Running |
| 2. 检查事件变化 | `kubectl events -n aiops-e2e --for=pod/rc-volume-hostpath-missing` | 不再出现 FailedMount 事件 |
| 3. 确认容器日志 | `kubectl logs rc-volume-hostpath-missing -n aiops-e2e` | 容器启动成功，输出 sleep 相关日志 |

---

## ⚠️ 注意事项

- **集群其他 59 个 Pod 均正常运行**，此问题仅影响 `aiops-e2e` 命名空间中的测试 Pod `rc-volume-hostpath-missing`
- 该 Pod 标签包含 `rootcause-e2e=true`，可能是为根因分析测试而构造的故意问题场景
- 如果路径必须某些特定文件/目录结构，`DirectoryOrCreate` 仅创建空目录，不能替代人工初始化

---

## 📊 性能统计

├─ 总耗时: 1.1m
├─ 问题定位: 15.1s (23%) ✅
├─ 证据链采集: 14.1s (21%) ✅
├─ 根因分析: 17.8s (27%) ✅
├─ 汇总总结: 19.1s (29%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 10 次
```

📋 诊断追踪

- **核心 Runbook**: pod-volume-mount-failed
- **参考 Runbook**: pod-volume-mount-failed
- **工具调用**: 10 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
