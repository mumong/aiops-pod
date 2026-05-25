======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 45049702ee694a4d]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来先做全局 Pod 状态扫描，看看集群中所有 Pod 的当前状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59}
NAMESPACE         NAME                                                READY   STATUS              RESTARTS       A
   💭 [问题定位] 发现了一个异常 Pod。让我进一步查看这个 Pod 的详情和 events。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  74s (x13 over 11m)     kubelet            MountVolu
   💭 [问题定位] 让我看看这个 Pod 引用的 ConfigMap 来确认问题。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                   DATA   AGE   LABELS
rc-volume-key-config   1      11m   rootcause-e2e=true
   💭 [问题定位] 调用工具: kubectl_get_yaml
   💭 [问题定位] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: ConfigMap
name: rc-volume-key-config
namespace: aiops-e2e
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-key-config
namespace: aiops-e2e
   💭 [问题定位] 已经查清问题了，获取匹配的 runbook。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] 现在我已经掌握了全部信息，来做完整的定位分析。

---

## 📋 集群异常诊断报告

### 全局扫描概览

| 指标 | 数据 |
|------|------|
| 总 Pod 数 | **65** |
| 正常运行 Pod | **59** (Running) |
| 异常 Pod | **1** |
| 异常率 | **1.5%** |

---

### 当前异常 Pod

| Pod | 命名空间 | 状态 | 重启次数 |
|-----|---------|------|---------|
| `rc-volume-configmap-missing-key` | `aiops-e2e` | **ContainerCreating** (Pending) | 0 |

---

### 异常详情

**Pod:** `rc-volume-configmap-missing-key`  
**命名空间:** `aiops-e2e`  
**状态:** `Pending` → 容器等待中，原因 `ContainerCreating`  
**异常类型:** `VolumeMountFailed`（卷挂载失败）

**核心根因证据：**
```
MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key
```

**根因分析：**
该 Pod 引用了名为 `rc-volume-key-config` 的 **ConfigMap**，该 ConfigMap 确实存在（含 1 个 data key），但 Pod 的 volume 配置中尝试引用的 key **`missing-key`** 在该 ConfigMap 中**不存在**，导致卷挂载失败，Pod 卡在 `ContainerCreating`。

---

### 分层定位结果

| 字段 | 值 |
|------|-----|
| **`pod_status_keyword`** | `ContainerCreating` |
| **`pod_abnormal_type`** | `VolumeMountFailed` |
| **`status_category`** | `storage_volume` |
| **`layer`** | `L0` |
| **`derived_layer`** | `L4`（ConfigMap key 配置缺失） |
| **`layers`** | `["L0", "L4"]` |
| **`layer_name`** | 卷挂载失败 - ConfigMap key 引用缺失 |
| **`confidence`** | `高` |
| **`reasoning`** | Events 明确报错 `configmap references non-existent config key: missing-key`，这是 VolumeMountFailed 的经典场景。ConfigMap 本身存在但 key 不存在，本质是配置错误，所以向下兼容 L4 ConfigError。 |

---

### 异常组

| 异常组 | Pod 列表 |
|--------|---------|
| `VolumeMountFailed` | `rc-volume-configmap-missing-key` |

---

### 关键实体

| 实体 | 类型 | 说明 |
|------|------|------|
| `rc-volume-configmap-missing-key` | Pod | 异常 Pod，卡在 ContainerCreating |
| `rc-volume-key-config` | ConfigMap | 引用的 ConfigMap 存在，但缺少 key `missing-key` |
| `config-volume` | Volume | Pod 中挂载的 volume 名称 |
| `node1` | Node | Pod 所在节点 |

---

### 可能场景

1. **ConfigMap key 拼写错误** — Pod 的 volume 配置中引用了 `missing-key`，但 ConfigMap `rc-volume-key-config` 中没有这个 key，需要检查 ConfigMap 中的实际 key 名称并修正 Pod 的 volume 配置。
2. **ConfigMap 不完整** — ConfigMap 本应包含 `missing-key` 但未正确创建或更新。

---

**总结：** 集群整体健康（59/65 Pod 正常运行），只有一个测试用途的 Pod 因 ConfigMap key 引用缺失而卡在 ContainerCreating，属于 **VolumeMountFailed / L0** 异常，本质是配置错误（兼容 L4）。需要修复 ConfigMap 中的 key 名称或修正 Pod 的 volume 引用。
   ✅ [问题定位] 完成 (21.9s)
   📤 → 下游数据: layer=Layer.L0, layers=L0+L4
   scenarios=[{'scenario': 'ConfigMap key 拼写错误', 'probability': '高', 'reason': 'Pod volume配置引用 missing-key，但 ConfigMap rc-volume-key-config 中不存在该 key'}, {'scenario': 'ConfigMap 不完整', 'probability': '中', 'reason': 'ConfigMap 本应包含 missing-key 但未正确创建或更新'}]
   entities=[{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}, {"type": "Volume", "name": "config-volume", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}]
   reasoning=集群1个异常Pod: rc-volume-configmap-missing-key (aiops-e2e)，状态ContainerCreating/Pending。Events明确报错: MountVolume.SetUp failed for volume "config-volume": configmap references non-existent config key: missing-key。Pod异常类型VolumeMountFailed，根因是卷挂载失败(volume/storage层L0)，但本质是ConfigMap key配置缺失(配置错误L4)，故derived_layer=L4，layers=[L0, L4]。59/65 Pod正常运行，整体健康度较高。
   layer_analysis={"layer": "L0", "derived_layer": "L4", "layers": ["L0", "L4"], "layer_name": "卷挂载失败 - ConfigMap key 引用缺失", "confidence": 1.0, "reasoning": "集群1个异常Pod: rc-volume-configmap-missing-key (aiops-e2e)，状态ContainerCreating/Pending。Events明确报错: MountVolume.SetUp failed for volume \"config-volume\": configmap references non-existent config key: missing-key。Pod异常类型VolumeMountFailed，根因是卷挂载失败(volume/storage层L0)，但本质是ConfigMap key配置缺失(配置错误L4)，故derived_layer=L4，layers=[L0, L4]。59/65 Pod正常运行，整体健康度较高。", "abnormal_pods": [{"name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}, {"type": "Volume", "name": "config-volume", "namespace": "aiops-e2e"}, {"type": "Node", "name": "node1", "namespace": ""}], "possible_scenarios": [{"scenario": "ConfigMap key 拼写错误", "probability": "高", "reason": "Pod volume配置引用 missing-key，但 ConfigMap rc-volume-key-config 中不存在该 key"}, {"scenario": "ConfigMap 不完整", "probability": "中", "reason": "ConfigMap 本应包含 missing-key 但未正确创建或更新"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-volume-configmap-missing-key                     0/1     ContainerCreating   0              11m     <none>           node1    <none>           <none>            app=rc-volume-configmap-missing-key,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/45049702ee694a4d/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/45049702ee694a4d/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/45049702ee694a4d/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L0 + L4（主层级: Layer.L0）
   置信度: 100%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来按照 evidence_plan 执行工具调用，采集真实环境证据。

**Step 1**: 先获取 Runbook 参考（上游已确认 matched_runbooks），然后执行三个 critical 级工具调用。

由于上游已经 fetch_runbook，我不需要重复获取。直接开始采证。

先并行执行三个独立的调用：
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: ConfigMap
name: rc-volume-key-config
namespace: aiops-e2e
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
creationTimestamp: 2026-05-21T04:29:04Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
final
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  100s (x13 over 11m)   kubelet            MountVolum
   💭 [证据链采集] ConfigMap 的 YAML 输出被截断了，我需要查看完整的 ConfigMap data 内容来确认到底有哪些 key。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "apiVersion: v1\ndata:\n  existing-key: present\nkind: ConfigMap\nmetadata:\n  annotations:\n    kubectl.kubernetes.io/last-applied-configuration: |\n      {\"apiVersion\":
   💭 [证据链采集] 现在确认 Pod spec volumes 中的具体 key 引用。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"defaultMode\": 420,\n  \"items\": [\n    {\n      \"key\": \"missing-key\",\n      \"path\": \"missing-key\"\n    }\n  ],\n  \"name\": \"rc-volume-key-config\"\n}\n
   💭 [证据链采集] 所有证据已采集完毕，以下是结论：

---

## 证据采集结论

### ✅ 已采集证据（3 条 critical）

| # | 证据项 | 结果 |
|---|--------|------|
| **e1 - Pod Describe** | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` | ✅ **关键事件确认**: `Warning FailedMount 100s (x13 over 11m) MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key` |
| **e2 - ConfigMap YAML** | `kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml` | ✅ **ConfigMap 内容确认**: 只包含 `existing-key: present`，**并不存在 `missing-key`** |
| **e3 - Pod Volumes 引用** | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o json \| jq '.spec.volumes[]'` | ✅ **Volume 引用确认**: `config-volume` 的 items 中明确要求引用 `key: "missing-key"`，但 ConfigMap 中没有该 key |

### 🎯 根因结论

**Pod `rc-volume-configmap-missing-key`** 卡在 `ContainerCreating` / `Pending` 的根因是 **ConfigMap volume key 配置缺失**：

- Pod 的 volume `config-volume`（类型: ConfigMap）的 `.spec.volumes[].configMap.items[]` 声明了 `key: "missing-key"`（映射到 path: `missing-key`）
- 对应 ConfigMap `rc-volume-key-config` 的 data 字段只包含 `existing-key: present`，**缺少 `missing-key`**
- Kubelet 在挂载 volume 时报错：`configmap references non-existent config key: missing-key`

### ❌ 无冲突 / 负向证据
- 所有工具调用成功返回，对象均存在，namespace 匹配
- ConfigMap 和 Pod 均正常存在于 aiops-e2e 命名空间

### 📋 修复建议
在 ConfigMap `rc-volume-key-config` 中增加 `missing-key` 条目，或修改 Pod volume 引用中的 key 名为 `existing-key`。
   ✅ [证据链采集] 完成 (14.7s)
   📤 → 下游数据: evidence_items=8/8
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"Describe Pod rc-volume-configmap-missing-key 确认当前 Events 原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e"},"purpose":"确认当前 FailedMount 事件原文是否仍然报 missing-key","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"e2","description":"Get ConfigMap rc-volume-key-config 确认实际包含哪些 key","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml","tool_args":{"kind":"ConfigMap","name":"rc-volume-key-config","namespace":"aiops-e2e"},"purpose":"验证 ConfigMap 中是否缺少 missing-key","evidence_type":"configmap_data","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"Get Pod YAML 确认 volumes[].configMap 引用的 key 名称","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e"},"purpose":"确认 Pod spec.volumes 中 configMap 引用的 key 名","evidence_type":"pod_spec","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: ConfigMap\nname: rc-volume-key-config\nnamespace: aiops-e2e","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/45049702ee694a4d/tools/001-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/45049702ee694a4d/tools/001-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/45049702ee694a4d/tools/001-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T04:29:04Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-configmap-missing-key, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"config-volume\", \"configMap\": \"rc-volume-key-config\"}\n- {\"name\": \"kube-api-access-fbhds\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/45049702ee694a4d/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/45049702ee694a4d/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/45049702ee694a4d/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  100s (x13 over 11m)   kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n  Warning  FailedMount  3m7s (x3 over 9m54s)  kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition\n  Warning  FailedMount  52s (x2 over 7m40s)   kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-fbhds config-volume]: timed out waiting for the condition\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  config-volume:\n    Type:      ConfigMap (a volume populated by a ConfigMap)\n    Name:      rc-volume-key-config\n    Optional:  false\n  kube-api-access-fbhds:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedMount  3m7s (x3 over 9m54s)  kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition\n  Warning  FailedMount  100s (x13 over 11m)   kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n  Warning  FailedMount  52s (x2 over 7m40s)   kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-fbhds config-volume]: timed out waiting for the condition\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/45049702ee694a4d/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/45049702ee694a4d/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/45049702ee694a4d/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"apiVersion: v1\\ndata:\\n  existing-key: present\\nkind: ConfigMap\\nmetadata:\\n  annotations:\\n    kubectl.kubernetes.io/last-applied-configuration: |\\n      {\\\"apiVersion\\\":\\\"v1\\\",\\\"data\\\":{\\\"existing-key\\\":\\\"present\\\"},\\\"kind\\\":\\\"ConfigMap\\\",\\\"metadata\\\":{\\\"annotations\\\":{},\\\"labels\\\":{\\\"rootcause-e2e\\\":\\\"true\\\"},\\\"name\\\":\\\"rc-volume-key-config\\\",\\\"namespace\\\":\\\"aiops-e2e\\\"}}\\n  creationTimestamp: \\\"2026-05-21T04:29:04Z\\\"\\n  labels:\\n    rootcause-e2e: \\\"true\\\"\\n  name: rc-volume-key-config\\n  namespace: aiops-e2e\\n  resourceVersion: \\\"52517160\\\"\\n  uid: 5468219a-cec8-424b-b490-66fd39c82b58\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/45049702ee694a4d/tools/004-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/45049702ee694a4d/tools/004-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/45049702ee694a4d/tools/004-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"defaultMode\\\": 420,\\n  \\\"items\\\": [\\n    {\\n      \\\"key\\\": \\\"missing-key\\\",\\n      \\\"path\\\": \\\"missing-key\\\"\\n    }\\n  ],\\n  \\\"name\\\": \\\"rc-volume-key-config\\\"\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/45049702ee694a4d/tools/005-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/45049702ee694a4d/tools/005-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/45049702ee694a4d/tools/005-evidence-run_bash_command.summary.txt"}],"llm_analysis":"所有证据已采集完毕，以下是结论：\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据（3 条 critical）\n\n| # | 证据项 | 结果 |\n|---|--------|------|\n| **e1 - Pod Describe** | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` | ✅ **关键事件确认**: `Warning FailedMount 100s (x13 over 11m) MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key` |\n| **e2 - ConfigMap YAML** | `kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml` | ✅ **ConfigMap 内容确认**: 只包含 `existing-key: present`，**并不存在 `missing-key`** |\n| **e3 - Pod Volumes 引用** | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o json \\| jq '.spec.volumes[]'` | ✅ **Volume 引用确认**: `config-volume` 的 items 中明确要求引用 `key: \"missing-key\"`，但 ConfigMap 中没有该 key |\n\n### 🎯 根因结论\n\n**Pod `rc-volume-configmap-missing-key`** 卡在 `ContainerCreating` / `Pending` 的根因是 **ConfigMap volume key 配置缺失**：\n\n- Pod 的 volume `config-volume`（类型: ConfigMap）的 `.spec.volumes[].configMap.items[]` 声明了 `key: \"missing-key\"`（映射到 path: `missing-key`）\n- 对应 ConfigMap `rc-volume-key-config` 的 data 字段只包含 `existing-key: present`，**缺少 `missing-key`**\n- Kubelet 在挂载 volume 时报错：`configmap references non-existent config key: missing-key`\n\n### ❌ 无冲突 / 负向证据\n- 所有工具调用成功返回，对象均存在，namespace 匹配\n- ConfigMap 和 Pod 均正常存在于 aiops-e2e 命名空间\n\n### 📋 修复建议\n在 ConfigMap `rc-volume-key-config` 中增加 `missing-key` 条目，或修改 Pod volume 引用中的 key 名为 `existing-key`。","collection_summary":"计划 3 项，实际采集 3 项，未采集 0 项，完整度 100%；其中真实环境证据 8/8 项，完整度 100%；实际执行工具 10 个，匹配计划 3 个，未规划证据 7 个","plan_total":3,"plan_collected":3,"plan_completeness":1.0,"environment_evidence_total":8,"environment_evidence_collected":8,"environment_evidence_completeness":1.0,"executed_tool_count":10,"matched_tool_count":3,"unplanned_tool_count":7,"evidence_inventory":[{"id":"e1","description":"Describe Pod rc-volume-configmap-missing-key 确认当前 Events 原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","purpose":"确认当前 FailedMount 事件原文是否仍然报 missing-key","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"Get ConfigMap rc-volume-key-config 确认实际包含哪些 key","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml","purpose":"验证 ConfigMap 中是否缺少 missing-key","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"Get Pod YAML 确认 volumes[].configMap 引用的 key 名称","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","purpose":"确认 Pod spec.volumes 中 configMap 引用的 key 名","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_yaml","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 3/3 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | Describe Pod rc-volume-configmap-missing-key ... | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_yaml | Get ConfigMap rc-volume-key-config 确认实际包含哪些 key | `kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml` |
   | e3 | critical | ✅ | kubectl_get_yaml | Get Pod YAML 确认 volumes[].configMap 引用的 key 名称 | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (17.9s)
   📤 → 下游数据: root_cause=Pod `rc-volume-configmap-missing-key` (namespace: aiops-e2e) 卡在 ContainerCreating/Pending 的根因是 ConfigMap 卷配置缺失。Pod 的 volume `config-volume` 通过 items[0] 声明引用 key: `missing-key`（映射到 path: `missing-key`），但 ConfigMap `rc-volume-key-config` 的 data 字段仅包含 `existing-key: present`，不存在 `missing-key`。Kubelet 事件明确报告(13次): `MountVolume.SetUp failed for volume "config-volume": configmap references non-existent config key: missing-key`。Volume 的 Optional 字段为 false，导致 Kubelet 无法忽略此错误跳过挂载，容器无法启动。集群整体健康，59/65 Pod
... 截断，原始 518 字符
   confidence=98%
   causal_chain={"root_cause": "ConfigMap rc-volume-key-config 缺少 Pod volume 引用的 key 'missing-key'", "propagation": "Pod 的 volume 配置（config-volume，类型 ConfigMap）的 items[0] 声明 key: missing-key → Kubelet 尝试从 ConfigMap 读取该 key 挂载到容器 → ConfigMap 中不存在此 key → Kubelet 报错 MountVolume.SetUp failed → Pod 无法完成 volume 挂载 → 容器无法启动 → Pod 持续处于 ContainerCreating/Pending 状态", "direct_cause": "Volume 'config-volume' 挂载失败，因为 ConfigMap rc-volume-key-config 中不存在 key 'missing-key'", "manifestation": "Pod rc-volume-configmap-missing-key 在 aiops-e2e 命名空间下状态 ContainerCreating/Pending，Events 持续报错 MountVolume.SetUp failed for volume config-volume: configmap references non-existent config key: missing-key"}
   rca_analysis={"phenomenon": "集群 aiops-e2e 命名空间下 Pod `rc-volume-configmap-missing-key` 状态为 ContainerCreating/Pending，无法进入 Running。59/65 Pod 正常运行，仅此 1 个异常 Pod。Events 明确报错卷挂载失败。", "evidence_inventory": [{"id": "e1", "source": "kubectl describe pod", "content": "Pod rc-volume-configmap-missing-key 当前状态 Pending，容器 Waiting(ContainerCreating)。Events: Warning FailedMount x13 — MountVolume.SetUp failed: configmap references non-existent config key: missing-key", "reliability": "高"}, {"id": "e2", "source": "kubectl get configmap -o yaml", "content": "ConfigMap rc-volume-key-config data 字段只包含 existing-key: present，不存在 missing-key", "reliability": "高"}, {"id": "e3", "source": "kubectl get pod -o json | jq .spec.volumes", "content": "Pod volume config-volume 的 items[0] 声明 key: missing-key，映射到 path: missing-key", "reliability": "高"}, {"id": "layer_1", "source": "kubectl get pods -A", "content": "集群 65 Pod 中 59 Running，仅 1 异常 (rc-volume-configmap-missing-key ContainerCreating)", "reliability": "高"}, {"id": "layer_4", "source": "kubectl get configmap", "content": "ConfigMap rc-volume-key-config 仅 1 条 data 条目 (DATA=1)，age=11m", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedMount 100s (x13 over 11m) kubelet MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key", "interpretation": "Kubelet 明确报告挂载 config-volume 失败，原因是 ConfigMap 引用了不存在的 key 'missing-key'。这个事件重复出现 13 次，说明 kubelet 持续重试均失败。"}, {"evidence_id": "e2", "raw_data": "data:\n  existing-key: present\nkind: ConfigMap\nname: rc-volume-key-config", "interpretation": "ConfigMap rc-volume-key-config 实际只包含一个键值对 existing-key: present，完全没有 missing-key 这个 key。"}, {"evidence_id": "e3", "raw_data": "{\"items\": [{\"key\": \"missing-key\", \"path\": \"missing-key\"}], \"name\": \"rc-volume-key-config\"}", "interpretation": "Pod 的 volume 配置中明确要求从 ConfigMap rc-volume-key-config 中读取 key 为 missing-key 的值并挂载到文件路径 missing-key。该 key 在 ConfigMap 中不存在。volume 的 optional 字段为 false（非可选），因此 kubelet 无法忽略此错误继续启动容器。"}, {"evidence_id": "layer_1", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59}", "interpretation": "集群整体健康度较高，59/65 Pod 正常运行，仅此 1 个异常 Pod，属于局部问题。"}, {"evidence_id": "layer_4", "raw_data": "rc-volume-key-config   1      11m", "interpretation": "ConfigMap 只有 1 个 data 条目，进一步确认 missing-key 不存在。"}], "causal_chain": {"root_cause": "ConfigMap rc-volume-key-config 缺少 Pod volume 引用的 key 'missing-key'", "propagation": "Pod 的 volume 配置（config-volume，类型 ConfigMap）的 items[0] 声明 key: missing-key → Kubelet 尝试从 ConfigMap 读取该 key 挂载到容器 → ConfigMap 中不存在此 key → Kubelet 报错 MountVolume.SetUp failed → Pod 无法完成 volume 挂载 → 容器无法启动 → Pod 持续处于 ContainerCreating/Pending 状态", "direct_cause": "Volume 'config-volume' 挂载失败，因为 ConfigMap rc-volume-key-config 中不存在 key 'missing-key'", "manifestation": "Pod rc-volume-configmap-missing-key 在 aiops-e2e 命名空间下状态 ContainerCreating/Pending，Events 持续报错 MountVolume.SetUp failed for volume config-volume: configmap references non-existent config key: missing-key"}, "root_cause": "Pod `rc-volume-configmap-missing-key` (namespace: aiops-e2e) 卡在 ContainerCreating/Pending 的根因是 ConfigMap 卷配置缺失。Pod 的 volume `config-volume` 通过 items[0] 声明引用 key: `missing-key`（映射到 path: `missing-key`），但 ConfigMap `rc-volume-key-config` 的 data 字段仅包含 `existing-key: present`，不存在 `missing-key`。Kubelet 事件明确报告(13次): `MountVolume.SetUp failed for volume \"config-volume\": configmap references non-existent config key: missing-key`。Volume 的 Optional 字段为 false，导致 Kubelet 无法忽略此错误跳过挂载，容器无法启动。集群整体健康，59/65 Pod\n... 截断，原始 518 字符", "root_cause_summary": "Pod `rc-volume-configmap-missing-key` (namespace: aiops-e2e) 卡在 ContainerCreating/Pending 的根因是 ConfigMap 卷配置缺失。Pod 的 volume `config-volume` 通过 items[0] 声明引用 key: `missing-key`（映射到 path: `missing-key`），但 ConfigMap `rc-volume-key-config` 的 data 字段仅包含 `existing-key: present`，不存在 `missing-key`。Kubelet 事件明确报告(13次): `MountVolume.SetUp failed for volume \"config-volume\": configmap references non-existent config key: missing-key`。Volume 的 Optional 字段为 false，导致 Kubelet 无法忽略此错误跳过挂载，容器无法启动。集群整体健康，59/65 Pod\n... 截断，原始 518 字符", "confidence": 0.98, "confidence_reason": "直接证据链完整：(1) Events 原文明确报告错误类型和缺失的 key 名称 (e1)，(2) ConfigMap YAML 确认 data 中确实没有该 key 且仅有一个 existing-key (e2)，(3) Pod YAML 确认 volume 的 items 确实引用了 missing-key 且 optional=false (e3)。三个证据相互印证，因果链清晰无歧义。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [{"cause": "ConfigMap 不存在或被删除", "probability": "low", "reason": "ConfigMap rc-volume-key-config 已确认存在（get configmap 返回正常，DATA=1, age=11m），排除"}, {"cause": "节点 node1 故障导致挂载超时", "probability": "low", "reason": "挂载超时事件（timed out waiting for the condition）是缺失 key 错误的衍生现象，不是独立根因。根本原因已在 Events 中明确"}, {"cause": "镜像拉取失败", "probability": "low", "reason": "Pod 使用 busybox:1.36 且 imagePullPolicy=Never，Events 中没有 ImagePullBackOff/ErrImagePull 相关事件"}, {"cause": "网络/CSI 插件问题", "probability": "low", "reason": "挂载类型为 ConfigMap（非 PVC/CSI），由 kubelet 内建处理，不依赖外部存储插件"}], "limitations": "证据已充分覆盖根因。Pod YAML 的 volumes[].configMap.items 原始输出中未直接展示 optional 字段的完整 JSON，但根据 kubelet 行为（非可选缺失 key 会报错阻止启动，可选则忽略），结合事件持续报错推断 optional=false。ConfigMap 的具体 data 内容通过 run_bash_command 获取确认，准确性高。", "llm_raw_analysis": "## 证据清点\n共采集 3 条 critical 证据 + 5 条重要层验证证据。\n\n## 逐条分析\n- e1 (Pod Describe): Events 直接报错 MountVolume.SetUp failed...configmap references non-existent config key: missing-key。这是最直接的故障现象证据。\n- e2 (ConfigMap YAML): 确认 ConfigMap rc-volume-key-config 的 data 仅有 existing-key: present，无 missing-key。\n- e3 (Pod Volumes JSON): Pod 的 config-volume 的 items[0] 声明 key: missing-key。volume 非 optional。\n- layer_1: 集群整体健康，仅 1 个异常 Pod。\n- layer_4: ConfigMap 只有 1 条 data 条目，确认数据量少，无 missing-key。\n\n## 关联分析\ne1 和 e2、e3 构成完美闭环：e3\n... 截断，原始 698 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod `rc-volume-configmap-missing-key` (namespace: aiops-e2e) 卡在 ContainerCreating/Pending 的根因是 ConfigMap 卷配置缺失。Pod 的 volume `config-volume` 通过 items[0...
   置信度: 98%
   🔗 因果链:
     根本原因: ConfigMap rc-volume-key-config 缺少 Pod volume 引用的 key 'missing-key'
     传导机制: Pod 的 volume 配置（config-volume，类型 ConfigMap）的 items[0] 声明 key: missing-key → Kubelet 尝试从 ConfigMap 读取该 key 挂载到容器 → ConfigMap 中不存在此 key → Kubelet 报错 MountVolume.SetUp failed → Pod 无法完成 volume 挂载 → 容器无法启动 → Pod 持续处于 ContainerCreating/Pending 状态
     最终表现: Pod rc-volume-configmap-missing-key 在 aiops-e2e 命名空间下状态 ContainerCreating/Pending，Events 持续报错 MountVolume.SetUp failed for volume config-volume: configmap references non-existent config key: missing-key


📍 [汇总总结] 执行中...
   ✅ [汇总总结] 完成 (13.5s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5212 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 8.0s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，这是为您生成的 K8s 集群诊断报告。

---
## 📊 诊断概览

您的集群总体健康，在 65 个 Pod 中有 **59 个正常运行**，但存在 **1 个异常 Pod**。

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ContainerCreating |
| **兼容归因层** | L4 - 配置错误 |
| **问题分类** | VolumeMountFailed (ConfigMap key 配置缺失) |
| **置信度** | 高 (98%) |
| **证据完整度** | 3/3 (100%) |

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod | rc-volume-configmap-missing-key |
| Namespace | aiops-e2e |
| Node | node1 |
| 错误信息 | `MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key` |

---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 事件 | kubectl_describe | `Warning FailedMount 100s (x13 over 11m) kubelet MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key` | Kubelet 明确报告 ConfigMap 中缺少 key: `missing-key`，导致卷挂载失败 |
| 2 | ConfigMap 内容 | run_bash_command (kubectl get configmap) | `data: existing-key: present` | ConfigMap `rc-volume-key-config` 中只包含 key `existing-key`，不存在 `missing-key` |
| 3 | Pod Volume 配置 | run_bash_command (kubectl get pod -o json) | `"items": [{"key": "missing-key","path": "missing-key"}], "name": "rc-volume-key-config"` | Pod 明确声明要挂载 ConfigMap 中名为 `missing-key` 的键 |

### 证据关联分析
- **证据 #1 → 直接原因**：Kubelet 事件 (`x13`，重复13次) 直接定位到问题根源：名为 `config-volume` 的卷尝试从 ConfigMap `rc-volume-key-config` 中读取 key `missing-key`，但该 key 不存在。
- **证据 #2 + #3 印证**：Pod 的 YAML 配置（证据 #3）要求挂载 `missing-key`，但 ConfigMap 中仅包含 `existing-key`（证据 #2）。此处存在配置不匹配，且由于 ConfigMap 卷的 `optional` 字段为 `false`（未设置或设置为 `false`），Kubelet 无法忽略此错误并继续启动容器。

### 缺失证据
无。所有关键证据已采集，根因清晰。

---
## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                            │
│ Pod 的 volume 配置（config-volume，类型 ConfigMap）引用了键 missing-key，但            │
│ 目标 ConfigMap (rc-volume-key-config) 中只定义了键 existing-key，缺少该键或键名拼写错误 │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                            │
│ Pod 声明挂载 ConfigMap → Kubelet 读取 ConfigMap 数据 → 在 ConfigMap 中找不到
│ 请求的 key (missing-key) → 因为 optional=false，Kubelet 无法跳过该挂载错误                │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                            │
│ Volume 'config-volume' 挂载失败: Kubelet 报告 MountVolume.SetUp failed，提示
│ "configmap references non-existent config key: missing-key"                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                      ↓
┌─────────────────────────────────────────────────────────────────────────────────────┘
│ 用户可见现象                                                                        │
│ Pod (rc-volume-configmap-missing-key) 持续处于 ContainerCreating/Pending 状态，无法启动 │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据所有证据，问题的根本原因是 **Pod 的 Volume 配置引用了 ConfigMap `rc-volume-key-config` 中一个不存在的键 `missing-key`**。这导致 Kubelet 无法挂载该卷，Pod 卡在 `ContainerCreating` 状态。

**置信度**：高 (98%)
- ✅ Kubelet 事件（x13次）明确报告了确切的错误信息。
- ✅ ConfigMap 的实际内容已验证缺少该键。
- ✅ Pod 的 Volume 配置已验证引用了不存在的键。

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）

**方案1 (推荐): 更新 ConfigMap，添加缺失的 key**
此方案修复 ConfigMap，使其包含 Pod 所需的 `missing-key`。
```bash
kubectl patch configmap rc-volume-key-config -n aiops-e2e --type merge -p '{"data":{"missing-key":"<填入实际配置值>"}}'
```
*依据*：证据 #2 显示 ConfigMap 缺少 key `missing-key`，添加即可解决问题。

**方案2: 删除 Pod，等待自动重建 (如果由 Deployment 管理)**
```bash
kubectl delete pod rc-volume-configmap-missing-key -n aiops-e2e
```
*注意*：此方案仅移除当前 Pod。如果 ConfigMap 未修复，新 Pod 会再次出现相同问题。

**方案3: 修改 Pod/Deployment 配置，移除对 `missing-key` 的引用**
如果 `missing-key` 是冗余或错误的配置，应修改 Pod 定义，移除 `items` 中对 `missing-key` 的引用。

### 后续优化
1. **验证 ConfigMap 完整性**：在部署前，使用脚本或 CI/CD Pipeline 检查 ConfigMap 的 key 是否与 Volume 配置中引用的 key 完全匹配。
2. **考虑设置 `optional: true`**：如果某些 ConfigMap key 对容器启动非必须，可以在 Volume 的 `configMap.items` 中设置 `optional: true`，使 Kubelet 在 key 缺失时也能启动容器，避免 Pod 卡死。

---
## 📋 验证步骤
| 步骤 | 命令 (选择方案1或3执行) | 预期结果 |
|------|------|------|
| 1. 修复 ConfigMap 或 Pod 配置 | 执行上述 `kubectl patch` 或修改 Deployment | 配置变更成功 |
| 2. 触发重建 Pod (如果是 Deployment) | `kubectl delete pod rc-volume-configmap-missing-key -n aiops-e2e` | Pod 被删除，Deployment 自动创建新 Pod |
| 3. 确认新 Pod 状态 | `kubectl get pod -n aiops-e2e` | `Pod` 名称可变为 `rc-volume-configmap-missing-key-xxxxx`，状态为 `Running` |
| 4. 检查 Pod 事件 | `kubectl describe pod <新的Pod名> -n aiops-e2e` | 无 `FailedMount` 错误事件 |

---
## ⚠️ 注意事项
- **键名拼写**：`missing-key` 可能是一个拼写错误，请检查原始配置，确保引用的是 ConfigMap 中正确的键名。
- **ConfigMap 更新**：如果此 Pod 由 Deployment/StatefulSet 管理，ConfigMap 更新后默认需要重启 Pod 才会生效。使用方案的 `kubectl delete pod` 即可触发重启。

---

## 📊 性能统计

├─ 总耗时: 1.1m
├─ 问题定位: 21.9s (32%) ✅
├─ 证据链采集: 14.7s (22%) ✅
├─ 根因分析: 17.9s (26%) ✅
├─ 汇总总结: 13.5s (20%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 11 次
```

📋 诊断追踪

- **核心 Runbook**: pod-volume-mount-failed
- **参考 Runbook**: pod-volume-mount-failed
- **工具调用**: 11 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
