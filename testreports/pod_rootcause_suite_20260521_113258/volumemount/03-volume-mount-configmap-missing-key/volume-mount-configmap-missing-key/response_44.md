======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 25b337973d084b92]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来先扫描全局 Pod 状态，看看集群里有哪些异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=65 abnormal=1 status_counts={'Running': 59}
NAMESPACE         NAME                                                READY   STATUS              RESTARTS       A
   💭 [问题定位] 找到了一个异常 Pod，让我抓住它进行描述确认：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-configmap-missing-key
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  67s (x19 over 23m)  kubelet            MountVolume.
   💭 [问题定位] 现在我来获取对应的 runbook 参考。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] 好的，我已收集到所有必要信息。以下是诊断分析结果：

---

## 🔍 集群异常诊断

### 全局 Pod 概览
| 状态 | 数量 |
|------|------|
| Running | 59 |
| 异常 | 1 |

### 当前异常 Pod

| Pod | 命名空间 | STATUS | 异常类型 |
|-----|---------|--------|---------|
| `rc-volume-configmap-missing-key` | aiops-e2e | ContainerCreating/Pending | VolumeMountFailed |

### 详细分析

**异常 Pod：`rc-volume-configmap-missing-key` @ `aiops-e2e`**

- **状态**：ContainerCreating（实际卡在 Pending）
- **核心事件**：`MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent config key: missing-key`
- **根本原因**：Pod 引用了一个名为 `rc-volume-key-config` 的 ConfigMap，其中引用了名为 `missing-key` 的键（key），但这个键在 ConfigMap 中**不存在**。
- Volume 类型：`configMap`（非必须的 PVC 挂载）

### 关键实体

| 实体 | 类型 | 说明 |
|------|------|------|
| rc-volume-configmap-missing-key | Pod | 异常 Pod |
| config-volume | Volume | 引用 ConfigMap `rc-volume-key-config`，配置的 key `missing-key` 不存在 |
| rc-volume-key-config | ConfigMap | 存在的 ConfigMap，但缺少 `missing-key` 这个键 |

### 可能场景

1. **ConfigMap key 拼写错误**：Pod 挂载配置中指定的 key `missing-key` 在 `rc-volume-key-config` 中不存在
2. **ConfigMap 内容不完整**：部署时 ConfigMap 没有包含预期键
3. **配置名称变更**：应用或模板预期了一个 key，但 ConfigMap 中实际 key 名不同

### 分层输出

| 字段 | 值 |
|------|-----|
| **layer** | L0 |
| **layer_name** | VolumeMountFailed |
| **pod_abnormal_type** | VolumeMountFailed |
| **pod_status_keyword** | ContainerCreating |
| **status_category** | volume_mount_failed |
| **confidence** | 高 |

### 后续审查方向（给下游 evidence）

1. 确认 `rc-volume-key-config` ConfigMap 中实际包含的键值对
2. 对比 Pod volume 配置中引用的 key 名与实际 ConfigMap 中的 key 名
3. 修正 ConfigMap 补上缺失的 key，或修正 Pod volume 配置中的 key 名
   ✅ [问题定位] 完成 (15.2s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[{'scenario': 'ConfigMap key 拼写错误', 'probability': '高', 'reason': "Pod volume 配置中引用了 key 'missing-key'，但 ConfigMap rc-volume-key-config 中不存在该键"}, {'scenario': 'ConfigMap 内容不完整', 'probability': '中', 'reason': '部署时 ConfigMap 没有包含预期键 missing-key'}, {'scenario': '配置名称变更', 'probability': '中', 'reason': '应用或模板预期了一个 key，但 ConfigMap 中实际 key 名不同'}]
   entities=[{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "Volume", "name": "config-volume", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}]
   reasoning=当前集群存在1个异常Pod：rc-volume-configmap-missing-key（aiops-e2e命名空间），状态为ContainerCreating/Pending。核心事件为MountVolume.SetUp failed for volume "config-volume": configmap references non-existent config key: missing-key。Pod引用了ConfigMap rc-volume-key-config，但指定的key missing-key在ConfigMap中不存在。根据五层模型，VolumeMountFailed属于L0（存储卷挂载失败，与存储/配置引用相关），同时status_category为volume_mount_failed。其余59个Pod运行正常。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "VolumeMountFailed", "confidence": 0.95, "reasoning": "当前集群存在1个异常Pod：rc-volume-configmap-missing-key（aiops-e2e命名空间），状态为ContainerCreating/Pending。核心事件为MountVolume.SetUp failed for volume \"config-volume\": configmap references non-existent config key: missing-key。Pod引用了ConfigMap rc-volume-key-config，但指定的key missing-key在ConfigMap中不存在。根据五层模型，VolumeMountFailed属于L0（存储卷挂载失败，与存储/配置引用相关），同时status_category为volume_mount_failed。其余59个Pod运行正常。", "abnormal_pods": [{"name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e", "status": "ContainerCreating"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "volume_mount_failed", "key_entities": [{"type": "Pod", "name": "rc-volume-configmap-missing-key", "namespace": "aiops-e2e"}, {"type": "Volume", "name": "config-volume", "namespace": "aiops-e2e"}, {"type": "ConfigMap", "name": "rc-volume-key-config", "namespace": "aiops-e2e"}], "possible_scenarios": [{"scenario": "ConfigMap key 拼写错误", "probability": "高", "reason": "Pod volume 配置中引用了 key 'missing-key'，但 ConfigMap rc-volume-key-config 中不存在该键"}, {"scenario": "ConfigMap 内容不完整", "probability": "中", "reason": "部署时 ConfigMap 没有包含预期键 missing-key"}, {"scenario": "配置名称变更", "probability": "中", "reason": "应用或模板预期了一个 key，但 ConfigMap 中实际 key 名不同"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-configmap-missing-key"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {}, "total_abnormal": 1, "selected_rows": ["aiops-e2e         rc-volume-configmap-missing-key                     0/1     ContainerCreating   0              23m     <none>           node1    <none>           <none>            app=rc-volume-configmap-missing-key,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true"], "raw_ref": "/tmp/aiops/reports/context_archives/25b337973d084b92/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/25b337973d084b92/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/25b337973d084b92/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我已收到既有 evidence_plan，直接执行工具调用采集证据。先执行所有 critical 级别工具以及 reference 的 runbook。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
88s (x19 over 23m)   Warning   FailedMount   Pod/rc-volume-configmap-missing-key   MountVolume.SetUp failed for volume "config-volume" : configmap references non-existent con
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
  Warning  FailedMount  88s (x19 over 23m)  kubelet            MountVolume.
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: ConfigMap
name: rc-volume-key-config
namespace: aiops-e2e
   💭 [证据链采集] 现在让我检查 ConfigMap 的完整内容，确认缺少哪些 key。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "apiVersion: v1\ndata:\n  existing-key: present\nkind: ConfigMap\nmetadata:\n  annotations:\n    kubectl.kubernetes.io/last-applied-configuration: |\n      {\"apiVersion\":
   💭 [证据链采集] 现在确认 Pod spec 的 volumes 中引用了哪些 key：
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "{\n  \"defaultMode\": 420,\n  \"items\": [\n    {\n      \"key\": \"missing-key\",\n      \"path\": \"missing-key\"\n    }\n  ],\n  \"name\": \"rc-volume-key-config\"\n}\n
   💭 [证据链采集] 所有工具调用完成，以下是证据采集结论。

---

## ✅ 已采集证据（4 项 critical + 1 项 important + runbook reference）

### 1️⃣ [Critical] kubectl describe pod — FailedMount 事件原文 ✅
**Pod**: `rc-volume-configmap-missing-key` | **状态**: `Pending` / `ContainerCreating`
```
Warning  FailedMount  88s (x19 over 23m)  kubelet
  MountVolume.SetUp failed for volume "config-volume" :
  configmap references non-existent config key: missing-key
```
**结论**: 事件原文明确指明根因——volume 引用了 ConfigMap 中不存在的 key `missing-key`。

### 2️⃣ [Critical] kubectl_get_yaml (Pod spec) — 确认 volume 类型 ✅
- `volumes[0].name = "config-volume"`
- `volumes[0].configMap.name = "rc-volume-key-config"`
- `volumes[0].configMap.items[0].key = "missing-key"` ← 就是问题根源
- 该 volume 为 **ConfigMap 类型**（非 PVC/NFS/CSI），对应 **Step 3A ConfigMap 缺失分支**

### 3️⃣ [Critical] kubectl_get_yaml (ConfigMap) — 确认 ConfigMap 内容 ✅
**ConfigMap**: `rc-volume-key-config`（namespace: aiops-e2e）
```
data:
  existing-key: present
```
ConfigMap 存在且正常，但 **只包含 key `existing-key`**，**不包含 key `missing-key`**。

### 4️⃣ [Important] kubectl_events — 完整事件上下文 ✅
共 19 次 FailedMount 重复事件，均围绕同一个根因，确认无其他异常事件（如 OOM、ImagePull 等）并发。

### 📘 Runbook Reference
已获取 `pod-volume-mount-failed.md`，确认符合 **Step 3A: ConfigMap/Secret volume 缺失分支**。

---

## 🔍 冲突/负向证据
- **无冲突证据**：所有工具结果与 upstream layer_handoff 完全一致，Pod 仍然存在且状态未变。

---

## 🧠 根因结论

> **Volume 引用 ConfigMap key 不存在**
> - Pod `rc-volume-configmap-missing-key` 通过 ConfigMap volume `config-volume` 引用了 key `missing-key`
> - ConfigMap `rc-volume-key-config` 中实际只有 key `existing-key`，没有 `missing-key`
> - 导致 `MountVolume.SetUp failed`，Pod 卡在 `ContainerCreating`/`Pending`

**建议修复**（仅供参考，不执行）：
1. 更新 Pod volume 配置，将 items 中的 key 从 `missing-key` 改为 `existing-key`
2. 或在 ConfigMap `rc-volume-key-config` 中补全 key `missing-key`
3. 修正后 Pod 将自动重新挂载并进入 Running 状态
   ✅ [证据链采集] 完成 (16.8s)
   📤 → 下游数据: evidence_items=7/7
   evidence_analysis={"evidence_plan":[{"id":"e1","description":"检查Pod当前状态和Events，验证MountVolume.SetUp failed错误","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e"},"purpose":"验证FailedMount事件原文：configmap references non-existent config key: missing-key","evidence_type":"pod_events","target_scope":"rc-volume-configmap-missing-key","acceptable_tools":["kubectl_describe"],"counts_for_completeness":true},{"id":"e2","description":"检查Pod YAML确认volume引用ConfigMap的配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e"},"purpose":"验证.spec.volumes[].configMap.items中引用的key名称","evidence_type":"pod_spec_volumes","target_scope":"rc-volume-configmap-missing-key","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e3","description":"检查ConfigMap实际包含的key列表，确认missing-key是否存在","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml","tool_args":{"kind":"configmap","name":"rc-volume-key-config","namespace":"aiops-e2e"},"purpose":"验证ConfigMap rc-volume-key-config中是否存在key 'missing-key'","evidence_type":"configmap_content","target_scope":"rc-volume-key-config","acceptable_tools":["kubectl_get_by_name","kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"e4","description":"获取Pod相关事件辅助确认","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-configmap-missing-key --sort-by='.lastTimestamp'","tool_args":{"resource_type":"pod","resource_name":"rc-volume-configmap-missing-key","namespace":"aiops-e2e"},"purpose":"补充验证FailedMount事件的完整上下文","evidence_type":"pod_events","target_scope":"rc-volume-configmap-missing-key","acceptable_tools":["kubectl_events"],"counts_for_completeness":true},{"id":"e5","description":"获取已确认的runbook作为参考","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-volume-mount-failed.md","tool_args":{},"purpose":"获取VolumeMountFailed runbook作为参考","evidence_type":"runbook_reference","target_scope":"runbook","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod VolumeMountFailed / 卷挂载失败\n\n> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume\n\n## 使用原则（给模型）\n- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。\n- `kubectl describe pod` / `kubectl get events` 中的 Events 原文权重最高；先读事件原文，再按关键字选择一个最相关分支。\n- 一旦 Events 或 Pod spec 已明确命中某个分支，应停止横向扩展到无关 PVC/PV/StorageClass/CSI/NFS 分支。\n- 证据计划优先覆盖“当前已经出现的错误文本”，不要把典型原因列表全部变成 evidence_plan。\n\n## 状态识别\n- Pod 常见状态: `Pending` / `ContainerCreating`\n- Events 关键字: `FailedMount` / `FailedAttachVolume` / `MountVolume.SetUp failed`\n- 相关资源: PVC / PV / StorageClass / CSI / NFS / Secret / ConfigMap volume\n\n## 典型原因\n- PVC 未 Bound、StorageClass 不存在、PV nodeAffinity 不匹配。\n- PV/PVC 访问模式不满足，例如 RWO 被多个节点挂载、Multi-Attach error。\n- CSI/NFS/iSCSI 后端不可用、权限拒绝、挂载超时、stale file handle。\n- Secret/ConfigMap 类型的 volume 引用了不存在的对象或 key。\n- hostPath 路径不存在、类型不匹配或节点权限不足。\n- 云盘或块存储与节点可用区/实例规格不匹配，例如 volume node affinity conflict、InvalidInstanceType.NotSupportDiskCategory。\n\n## 证据优先级\n1. 最高优先级: `kubectl describe pod <pod> -n <namespace>` 或 `kubectl get events ...`，读取 Events 原文。\n2. 最高优先级: `kubectl get pod <pod> -n <namespace> -o yaml`，确认 `.spec.volumes[]` 引用的是 PVC、ConfigMap、Secret、hostPath 还是 CSI。\n3. 分支证据: 只查询 Events 原文指向的资源类型。\n\n## 分支诊断流程\n\n### Step 1: 先读 Pod Events 原文（必须优先）\n```bash\nkubectl describe pod <pod-name> -n <namespace>\nkubectl get events -n <namespace> --field-selector involvedObject.name=<pod-name> --sort-by='.lastTimestamp'\n```\n如果已看到 `configmap \"<name>\" not found`、`secret \"<name>\" not found`、`unbound immediate PersistentVolumeClaims`、`volume node affinity conflict`、`Multi-Attach error`、`NFS timeout/access denied`，直接进入对应分支。\n\n### Step 2: 读取 Pod spec 中的 volume 引用（必须优先）\n```bash\nkubectl get pod <pod-name> -n <namespace> -o yaml\n```\n关注 `.spec.volumes[]`:\n- `configMap.name` / `secret.secretName`: 进入 ConfigMap/Secret 分支。\n- `persistentVolumeClaim.claimName`: 进入 PVC/PV/StorageClass 分支。\n- `hostPath`: 进入 hostPath/节点路径分支。\n- `csi` / NFS 相关字段: 进入 CSI/NFS 分支。\n\n### Step 3A: ConfigMap/Secret volume 缺失分支\n触发条件: Events 含 `configmap \"<name>\" not found`、`secret \"<name>\" not found`，且 Pod spec 中来自 `volumes[].configMap` 或 `volumes[].secret`。\n```bash\nkubectl get configmap <name> -n <namespace>\nkubectl get secret <name> -n <namespace>\n```\n预期证据: `Error from server (NotFound)` 本身就是有效根因证据。此时不要再查 PVC、PV、StorageClass，除非 Pod spec 同时存在 PVC volume 且 Events 指向 PVC。\n\n### Step 3B: PVC/PV/StorageClass 分支\n触发条件: Events 含 `unbound immediate PersistentVolumeClaims`、`pod has unbound`、`persistentvolumeclaim ... not found`，或 Pod spec 明确使用 `persistentVolumeClaim.claimName`。\n```bash\nkubectl get pvc <pvc-name> -n <namespace>\nkubectl describe pvc <pvc-name> -n <namespace>\nkubectl get pv\nkubectl get storageclass\n```\n只有 PVC Pending/NotFound/ProvisioningFailed 时，才继续检查 PV 和 StorageClass。\n\n### Step 3C: Attach/NodeAffinity/Multi-Attach 分支\n触发条件: Events 含 `FailedAttachVolume`、`Multi-Attach error`、`volume node affinity conflict`。\n```bash\nkubectl describe pod <pod-name> -n <namespace>\nkubectl describe pv <pv-name>\nkubectl get pod <pod-name> -n <namespace> -o wide\n```\n\n### Step 3D: CSI/NFS/hostPath 分支\n触发条件: Events 含 `timeout`、`access denied`、`stale file handle`、`hostPath type check failed`、CSI driver 错误。\n```bash\nkubectl get pods -n kube-system -o wide\nkubectl describe node <node-name>\n```\n\n## 判定规则\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| Events 含 Secret/ConfigMap not found + Pod spec 来自 volumes[].secret/configMap | volume 引用的 ConfigMap/Secret 缺失 | 高 |\n| FailedMount/MountVolume + PVC 未 Bound | VolumeMountFailed | 高 |\n| FailedScheduling + unbound immediate PersistentVolumeClaims | PVC 未绑定导致 Pending，归入 VolumeMountFailed/PVC 分支 | 高 |\n| Multi-Attach error + ReadWriteOnce | 卷访问模式与调度节点冲突 | 高 |\n| PV nodeAffinity conflict | PV 节点亲和性与 Pod 调度节点不匹配 | 高 |\n| volume node affinity conflict / node(s) had volume node affinity conflict | PV/云盘可用区与调度节点不匹配 | 高 |\n| InvalidInstanceType.NotSupportDiskCategory | 云盘类型不支持当前节点实例规格 | 高 |\n| NFS timeout/access denied/stale file handle | VolumeMountFailed | 高 |\n| Secret/ConfigMap not found 且来自 volume 引用 | VolumeMountFailed；若来自 env/envFrom 则切换 ConfigError；不要再扩展 PVC 分支 | 高 |\n| hostPath path/type error | 节点路径或 hostPath 类型配置错误 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/25b337973d084b92/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/25b337973d084b92/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/25b337973d084b92/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n88s (x19 over 23m)   Warning   FailedMount   Pod/rc-volume-configmap-missing-key   MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n10m (x3 over 19m)    Warning   FailedMount   Pod/rc-volume-configmap-missing-key   Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-fbhds config-volume]: timed out waiting for the condition\n87s (x7 over 21m)    Warning   FailedMount   Pod/rc-volume-configmap-missing-key   Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/25b337973d084b92/tools/002-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/25b337973d084b92/tools/002-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/25b337973d084b92/tools/002-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T04:29:04Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-configmap-missing-key, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"config-volume\", \"configMap\": \"rc-volume-key-config\"}\n- {\"name\": \"kube-api-access-fbhds\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/25b337973d084b92/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/25b337973d084b92/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/25b337973d084b92/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-configmap-missing-key\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  88s (x19 over 23m)  kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n  Warning  FailedMount  10m (x3 over 19m)   kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-fbhds config-volume]: timed out waiting for the condition\n  Warning  FailedMount  87s (x7 over 21m)   kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  config-volume:\n    Type:      ConfigMap (a volume populated by a ConfigMap)\n    Name:      rc-volume-key-config\n    Optional:  false\n  kube-api-access-fbhds:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedMount  10m (x3 over 19m)   kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[kube-api-access-fbhds config-volume]: timed out waiting for the condition\n  Warning  FailedMount  88s (x19 over 23m)  kubelet            MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key\n  Warning  FailedMount  87s (x7 over 21m)   kubelet            Unable to attach or mount volumes: unmounted volumes=[config-volume], unattached volumes=[config-volume kube-api-access-fbhds]: timed out waiting for the condition\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/25b337973d084b92/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/25b337973d084b92/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/25b337973d084b92/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: ConfigMap\nname: rc-volume-key-config\nnamespace: aiops-e2e","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/25b337973d084b92/tools/005-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/25b337973d084b92/tools/005-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/25b337973d084b92/tools/005-evidence-kubectl_get_yaml.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"apiVersion: v1\\ndata:\\n  existing-key: present\\nkind: ConfigMap\\nmetadata:\\n  annotations:\\n    kubectl.kubernetes.io/last-applied-configuration: |\\n      {\\\"apiVersion\\\":\\\"v1\\\",\\\"data\\\":{\\\"existing-key\\\":\\\"present\\\"},\\\"kind\\\":\\\"ConfigMap\\\",\\\"metadata\\\":{\\\"annotations\\\":{},\\\"labels\\\":{\\\"rootcause-e2e\\\":\\\"true\\\"},\\\"name\\\":\\\"rc-volume-key-config\\\",\\\"namespace\\\":\\\"aiops-e2e\\\"}}\\n  creationTimestamp: \\\"2026-05-21T04:29:04Z\\\"\\n  labels:\\n    rootcause-e2e: \\\"true\\\"\\n  name: rc-volume-key-config\\n  namespace: aiops-e2e\\n  resourceVersion: \\\"52517160\\\"\\n  uid: 5468219a-cec8-424b-b490-66fd39c82b58\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/25b337973d084b92/tools/006-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/25b337973d084b92/tools/006-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/25b337973d084b92/tools/006-evidence-run_bash_command.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"{\\n  \\\"defaultMode\\\": 420,\\n  \\\"items\\\": [\\n    {\\n      \\\"key\\\": \\\"missing-key\\\",\\n      \\\"path\\\": \\\"missing-key\\\"\\n    }\\n  ],\\n  \\\"name\\\": \\\"rc-volume-key-config\\\"\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/25b337973d084b92/tools/007-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/25b337973d084b92/tools/007-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/25b337973d084b92/tools/007-evidence-run_bash_command.summary.txt"}],"llm_analysis":"所有工具调用完成，以下是证据采集结论。\n\n---\n\n## ✅ 已采集证据（4 项 critical + 1 项 important + runbook reference）\n\n### 1️⃣ [Critical] kubectl describe pod — FailedMount 事件原文 ✅\n**Pod**: `rc-volume-configmap-missing-key` | **状态**: `Pending` / `ContainerCreating`\n```\nWarning  FailedMount  88s (x19 over 23m)  kubelet\n  MountVolume.SetUp failed for volume \"config-volume\" :\n  configmap references non-existent config key: missing-key\n```\n**结论**: 事件原文明确指明根因——volume 引用了 ConfigMap 中不存在的 key `missing-key`。\n\n### 2️⃣ [Critical] kubectl_get_yaml (Pod spec) — 确认 volume 类型 ✅\n- `volumes[0].name = \"config-volume\"`\n- `volumes[0].configMap.name = \"rc-volume-key-config\"`\n- `volumes[0].configMap.items[0].key = \"missing-key\"` ← 就是问题根源\n- 该 volume 为 **ConfigMap 类型**（非 PVC/NFS/CSI），对应 **Step 3A ConfigMap 缺失分支**\n\n### 3️⃣ [Critical] kubectl_get_yaml (ConfigMap) — 确认 ConfigMap 内容 ✅\n**ConfigMap**: `rc-volume-key-config`（namespace: aiops-e2e）\n```\ndata:\n  existing-key: present\n```\nConfigMap 存在且正常，但 **只包含 key `existing-key`**，**不包含 key `missing-key`**。\n\n### 4️⃣ [Important] kubectl_events — 完整事件上下文 ✅\n共 19 次 FailedMount 重复事件，均围绕同一个根因，确认无其他异常事件（如 OOM、ImagePull 等）并发。\n\n### 📘 Runbook Reference\n已获取 `pod-volume-mount-failed.md`，确认符合 **Step 3A: ConfigMap/Secret volume 缺失分支**。\n\n---\n\n## 🔍 冲突/负向证据\n- **无冲突证据**：所有工具结果与 upstream layer_handoff 完全一致，Pod 仍然存在且状态未变。\n\n---\n\n## 🧠 根因结论\n\n> **Volume 引用 ConfigMap key 不存在**\n> - Pod `rc-volume-configmap-missing-key` 通过 ConfigMap volume `config-volume` 引用了 key `missing-key`\n> - ConfigMap `rc-volume-key-config` 中实际只有 key `existing-key`，没有 `missing-key`\n> - 导致 `MountVolume.SetUp failed`，Pod 卡在 `ContainerCreating`/`Pending`\n\n**建议修复**（仅供参考，不执行）：\n1. 更新 Pod volume 配置，将 items 中的 key 从 `missing-key` 改为 `existing-key`\n2. 或在 ConfigMap `rc-volume-key-config` 中补全 key `missing-key`\n3. 修正后 Pod 将自动重新挂载并进入 Running 状态","collection_summary":"计划 4 项，实际采集 4 项，未采集 0 项，完整度 100%；其中真实环境证据 6/6 项，完整度 100%；实际执行工具 8 个，匹配计划 5 个，未规划证据 3 个","plan_total":4,"plan_collected":4,"plan_completeness":1.0,"environment_evidence_total":6,"environment_evidence_collected":6,"environment_evidence_completeness":1.0,"executed_tool_count":8,"matched_tool_count":5,"unplanned_tool_count":3,"evidence_inventory":[{"id":"e1","description":"检查Pod当前状态和Events，验证MountVolume.SetUp failed错误","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e","purpose":"验证FailedMount事件原文：configmap references non-existent config key: missing-key","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e2","description":"检查Pod YAML确认volume引用ConfigMap的配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml","purpose":"验证.spec.volumes[].configMap.items中引用的key名称","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e3","description":"检查ConfigMap实际包含的key列表，确认missing-key是否存在","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml","purpose":"验证ConfigMap rc-volume-key-config中是否存在key 'missing-key'","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e4","description":"获取Pod相关事件辅助确认","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-configmap-missing-key --sort-by='.lastTimestamp'","purpose":"补充验证FailedMount事件的完整上下文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"e5","description":"获取已确认的runbook作为参考","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-volume-mount-failed.md","purpose":"获取VolumeMountFailed runbook作为参考","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 4/4 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | e1 | critical | ✅ | kubectl_describe | 检查Pod当前状态和Events，验证MountVolume.SetUp failed错误 | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` |
   | e2 | critical | ✅ | kubectl_get_yaml | 检查Pod YAML确认volume引用ConfigMap的配置 | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e -o yaml` |
   | e3 | critical | ✅ | kubectl_get_yaml | 检查ConfigMap实际包含的key列表，确认missing-key是否存在 | `kubectl get configmap rc-volume-key-config -n aiops-e2e -o yaml` |
   | e4 | important | ✅ | kubectl_events | 获取Pod相关事件辅助确认 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volum...` |
   | e5 | reference | ✅ | fetch_runbook | 获取已确认的runbook作为参考 | `fetch_runbook pod-volume-mount-failed.md` |

📍 [根因分析] 执行中...
   ✅ [根因分析] 完成 (14.0s)
   📤 → 下游数据: root_cause=Pod rc-volume-configmap-missing-key（aiops-e2e 命名空间）卡在 Pending/ContainerCreating 状态，原因是其 volume 'config-volume' 从 ConfigMap 'rc-volume-key-config' 中引用了 key 'missing-key'（Pod YAML 可见 volumes[0].configMap.items[0].key='missing-key'），但该 ConfigMap 实际仅包含 key 'existing-key'（kubectl_get_yaml 确认 data 字段只有 existing-key）。kubelet 在 23 分钟内报告了 19 次 FailedMount 事件（MountVolume.SetUp failed for volume "config-volume": configmap references non-existent config key: missing-key）。集群其余 59 个 Pod 均正常运行，无其他异常。
   confidence=95%
   causal_chain={"root_cause": "ConfigMap rc-volume-key-config 中缺少 key 'missing-key'，但 Pod volume 配置引用了该 key", "propagation": "Pod 调度到 node1 后，kubelet 尝试挂载 config-volume 时发现引用的 key missing-key 在 ConfigMap 中不存在 → MountVolume.SetUp failed → Pod 卡在 ContainerCreating/Pending 无法继续启动", "direct_cause": "Pod spec.volumes[0].configMap.items[0].key='missing-key' 指向 ConfigMap 中不存在的 key", "manifestation": "Pod rc-volume-configmap-missing-key 状态为 Pending/ContainerCreating，Events 持续报 FailedMount: configmap references non-existent config key: missing-key"}
   rca_analysis={"phenomenon": "Pod rc-volume-configmap-missing-key（namespace: aiops-e2e）处于 Pending/ContainerCreating 状态，kubelet 持续报告 MountVolume.SetUp failed 错误。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe", "content": "Pod 状态 Pending，FailedMount 事件: MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key（88s x19 over 23m）", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml (Pod spec)", "content": "Pod volumes[].configMap.name=rc-volume-key-config，volumes[].configMap.items[0].key=missing-key", "reliability": "高"}, {"id": "e3", "source": "kubectl_get_yaml (ConfigMap)", "content": "ConfigMap rc-volume-key-config 存在，data 中仅含 existing-key，不包含 missing-key", "reliability": "高"}, {"id": "e4", "source": "kubectl_events", "content": "连续 19 次 FailedMount 事件，均指向同一根因，无其他并发异常事件", "reliability": "高"}, {"id": "e5", "source": "kubectl_get_by_kind_in_cluster", "content": "集群共 65 Pod，59 Running，仅此 1 个异常 Pod", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedMount 88s (x19 over 23m) kubelet MountVolume.SetUp failed for volume \"config-volume\" : configmap references non-existent config key: missing-key", "interpretation": "kubelet 明确报告 ConfigMap volume 引用了不存在的 key 'missing-key'，这是直接错误原因。"}, {"evidence_id": "e2", "raw_data": "volumes: [{\"name\":\"config-volume\",\"configMap\":{\"name\":\"rc-volume-key-config\",\"items\":[{\"key\":\"missing-key\",\"path\":\"missing-key\"}]}}]", "interpretation": "Pod 的 volume 配置确实从 ConfigMap rc-volume-key-config 中引用了 items[0].key='missing-key'，与错误信息完全吻合。"}, {"evidence_id": "e3", "raw_data": "data:\n  existing-key: present\nkind: ConfigMap\nname: rc-volume-key-config", "interpretation": "ConfigMap 实际只有 key 'existing-key'，没有 'missing-key'，确认是 key 引用不存在的根因。"}, {"evidence_id": "e4", "raw_data": "88s (x19 over 23m) Warning FailedMount Pod/rc-volume-configmap-missing-key MountVolume.SetUp failed ...", "interpretation": "事件持续复现（19次），时间跨 23 分钟，说明问题稳定存在且未被自动恢复。"}, {"evidence_id": "e5", "raw_data": "rows=65 abnormal=1 status_counts={'Running': 59}", "interpretation": "集群中仅此 1 个异常 Pod，其余 59 个 Pod 正常运行，问题被限定在单个 Pod 的 ConfigMap volume 引用范围。"}], "causal_chain": {"root_cause": "ConfigMap rc-volume-key-config 中缺少 key 'missing-key'，但 Pod volume 配置引用了该 key", "propagation": "Pod 调度到 node1 后，kubelet 尝试挂载 config-volume 时发现引用的 key missing-key 在 ConfigMap 中不存在 → MountVolume.SetUp failed → Pod 卡在 ContainerCreating/Pending 无法继续启动", "direct_cause": "Pod spec.volumes[0].configMap.items[0].key='missing-key' 指向 ConfigMap 中不存在的 key", "manifestation": "Pod rc-volume-configmap-missing-key 状态为 Pending/ContainerCreating，Events 持续报 FailedMount: configmap references non-existent config key: missing-key"}, "root_cause": "Pod rc-volume-configmap-missing-key（aiops-e2e 命名空间）卡在 Pending/ContainerCreating 状态，原因是其 volume 'config-volume' 从 ConfigMap 'rc-volume-key-config' 中引用了 key 'missing-key'（Pod YAML 可见 volumes[0].configMap.items[0].key='missing-key'），但该 ConfigMap 实际仅包含 key 'existing-key'（kubectl_get_yaml 确认 data 字段只有 existing-key）。kubelet 在 23 分钟内报告了 19 次 FailedMount 事件（MountVolume.SetUp failed for volume \"config-volume\": configmap references non-existent config key: missing-key）。集群其余 59 个 Pod 均正常运行，无其他异常。", "root_cause_summary": "Pod rc-volume-configmap-missing-key（aiops-e2e 命名空间）卡在 Pending/ContainerCreating 状态，原因是其 volume 'config-volume' 从 ConfigMap 'rc-volume-key-config' 中引用了 key 'missing-key'（Pod YAML 可见 volumes[0].configMap.items[0].key='missing-key'），但该 ConfigMap 实际仅包含 key 'existing-key'（kubectl_get_yaml 确认 data 字段只有 existing-key）。kubelet 在 23 分钟内报告了 19 次 FailedMount 事件（MountVolume.SetUp failed for volume \"config-volume\": configmap references non-existent config key: missing-key）。集群其余 59 个 Pod 均正常运行，无其他异常。", "confidence": 0.95, "confidence_reason": "错误事件原文、Pod YAML 中的 volume 引用、ConfigMap 实际内容三者完全对应，因果链清晰无歧义。所有关键证据（kubectl_describe、kubectl_get_yaml Pod/ConfigMap、kubectl_events）均为工具采集的原始数据，无推测或间接推断。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [{"cause": "ConfigMap 对象不存在", "probability": "low", "reason": "kubectl_get_yaml 已确认 ConfigMap rc-volume-key-config 存在于 aiops-e2e 命名空间，排除此可能"}, {"cause": "ConfigMap 被删除后重建但内容不完整", "probability": "low", "reason": "当前 ConfigMap 存在，仅有 existing-key，且创建时间与 Pod 一致（2026-05-21T04:29:04Z），非中途删除重建"}, {"cause": "PVC/PV/存储后端问题", "probability": "low", "reason": "Runbook Step 3A 明确：Events 指向 ConfigMap key 缺失，应停止扩展 PVC/PV/CSI/NFS 分支；Pod spec 也确认 volume 类型为 ConfigMap 而非 PVC"}], "limitations": "未检查 ConfigMap 是否曾被修改或是否有多个版本，但当前状态已能完整解释根因，不影响结论。Pod 的 imagePullPolicy=Never 且 image=busybox:1.36，但当前错误在挂载阶段已被阻断，未执行到镜像拉取阶段，不影响根因判断。", "llm_raw_analysis": "L0 根因分析完成。集群仅 1 个异常 Pod（rc-volume-configmap-missing-key），其余 59 个 Pod 运行正常。异常组 g1 的根因为：Pod 通过 ConfigMap volume 引用了一个不存在的 key 'missing-key'，ConfigMap 'rc-volume-key-config' 中实际只有 'existing-key'。根据 pod-volume-mount-failed.md runbook 的 Step 3A 分支，此问题属于 ConfigMap volume 缺失分支，无需扩展 PVC/PV/CSI 分支。修复方式：将 Pod volume items 中的 key 从 missing-key 改为 existing-key，或在 ConfigMap 中补全 missing-key。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: Pod rc-volume-configmap-missing-key（aiops-e2e 命名空间）卡在 Pending/ContainerCreating 状态，原因是其 volume 'config-volume' 从 ConfigMap 'rc-volume-key-config' 中引用了...
   置信度: 95%
   🔗 因果链:
     根本原因: ConfigMap rc-volume-key-config 中缺少 key 'missing-key'，但 Pod volume 配置引用了该 key
     传导机制: Pod 调度到 node1 后，kubelet 尝试挂载 config-volume 时发现引用的 key missing-key 在 ConfigMap 中不存在 → MountVolume.SetUp failed → Pod 卡在 ContainerCreating/Pending 无法继续启动
     最终表现: Pod rc-volume-configmap-missing-key 状态为 Pending/ContainerCreating，Events 持续报 FailedMount: configmap references non-existent config key: missing-key


📍 [汇总总结] 执行中...
   ✅ [汇总总结] 完成 (14.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 5502 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 0.6s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为一名资深 K8s 诊断报告专家，我将为您分析集群状态。

---
## 📊 诊断概览

根据分析，您的集群整体运行正常，**60 个 Pod 中 59 个运行正常（Running）**，存在 **1 个异常 Pod**。

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ContainerCreating / Pending (VolumeMountFailed) |
| **兼容归因层** | L0 - 存储卷挂载失败 |
| **问题分类** | VolumeMountFailed - ConfigMap Key Not Found |
| **置信度** | 高 (95%) |
| **证据完整度** | 4/4 (100%) |

---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 异常 Pod | **rc-volume-configmap-missing-key** |
| Namespace | **aiops-e2e** |
| Node | **node1** |
| 核心错误事件 | **MountVolume.SetUp failed for volume "config-volume": configmap references non-existent config key: missing-key** |

**集群现状摘要**：
- **集群共有 60 个 Pod**：其中 59 个处于 `Running` 状态，1 个处于 `ContainerCreating` 状态。
- **异常 Pod 详情**：Pod `rc-volume-configmap-missing-key` 自创建以来（23分钟）一直卡在 `ContainerCreating` 状态，无法启动。
- **根本原因**：Pod 的 Volume 配置从 ConfigMap `rc-volume-key-config` 中引用了一个不存在的 key `missing-key`。

---
## 🕵️ 证据链

### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态与事件 | `kubectl describe pod` | `Warning FailedMount 88s (x19 over 23m) kubelet ... MountVolume.SetUp failed for volume "config-volume": configmap references non-existent config key: missing-key` | kubelet 反复报告 ConfigMap 中缺少指定的 key。 |
| 2 | Pod YAML 配置 | `kubectl get pod -o yaml` | `volumes[0].configMap.items[0].key='missing-key'` | Pod 明确指定挂载 ConfigMap `rc-volume-key-config` 中的 key `missing-key`。 |
| 3 | ConfigMap 内容 | `kubectl get configmap -o yaml` | `data: existing-key: present` | ConfigMap `rc-volume-key-config` 中**仅有** key `existing-key`，**不包含** `missing-key`。 |
| 4 | 集群事件 | `kubectl events` | `88s (x19 over 23m) Warning FailedMount Pod/rc-volume-configmap-missing-key MountVolume.SetUp failed ...` | 在 23 分钟内持续产生 19 次挂载失败事件。 |

### 证据关联分析
- **证据 #1 + #2 + #3 印证**：Pod YAML 配置要求挂载 `missing-key` (证据 #2)，但 ConfigMap (证据 #3) 中不包含此 key，直接导致 kubelet 挂载失败 (证据 #1 和 #4)。
- **因果链明确**：配置错误 → 卷挂载失败 → Pod 卡在 `ContainerCreating`。

### 缺失证据
| 证据 | 级别 | 影响 |
|------|------|------|
| Pod 崩溃前日志 | 不适用 | Pod 尚未启动，无容器日志。不影响根因判断。 |

---
## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                │
│ ConfigMap 'rc-volume-key-config' 中缺少 key 'missing-key'。             │
│ Pod spec.volumes[0].configMap.items[0].key 引用了 ConfigMap 中不存在的  │
│ key。                                                       (证据 #2, #3)│
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                │
│ Pod 调度到 node1，kubelet 尝试挂载 config-volume。发现引用的 key        │
│ 'missing-key' 在 ConfigMap 中不存在 → 挂载失败。                         │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 直接原因                                                                │
│ kubelet 持续报告 FailedMount 事件：                                    │
│ "configmap references non-existent config key: missing-key" (证据 #1, #4)│
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                            │
│ Pod 'rc-volume-configmap-missing-key' 状态为 ContainerCreating/Pending，│
│ 持续 23 分钟无法启动。                                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2 (Pod YAML 配置) 和证据 #3 (ConfigMap 内容)，问题的根本原因是 **应用 YAML 配置错误**。Pod `rc-volume-configmap-missing-key` 的 Volume 配置指定挂载 ConfigMap `rc-volume-key-config` 中的 key `missing-key`，但该 key 在 ConfigMap 中并不存在（ConfigMap 实际只包含 key `existing-key`），导致 kubelet 挂载失败，Pod 卡在 `ContainerCreating` 状态无法启动。

**置信度**：高 (95%)
- ✅ 事件日志明确指向“ConfigMap references non-existent config key”
- ✅ Pod YAML 与 ConfigMap 内容的直接对比证实了不匹配

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）

**修复此问题有两种可行方案，请根据实际情况选择其一：**

**方案一：修正 ConfigMap（推荐，如果 Pod 配置是正确的）**
如果 Pod 配置中引用的 `missing-key` 是正确且必需的，则将此 key 添加到 ConfigMap 中。
```bash
# 1. 编辑 ConfigMap
kubectl edit configmap rc-volume-key-config -n aiops-e2e

# 2. 在 data 字段下添加 missing-key，保存后退出。例如修改后如下：
# apiVersion: v1
# data:
#   missing-key: <your-desired-value>
#   existing-key: present
# ...

# 3. 无需操作 Pod，ConfigMap 修改后，kubelet 会自动重试挂载。
```

**方案二：修正 Pod 配置（如果 'missing-key' 是拼写错误）**
如果 Pod 配置中引用的 `missing-key` 是拼写错误，应将其修正为 ConfigMap 中存在的 key，例如 `existing-key`。
```bash
# 此方案需要重建 Pod 或 Deployment。如果 Pod 由 Deployment 管理：
kubectl edit deployment <deployment-name> -n aiops-e2e
# 找到 volumes[0].configMap.items[0].key 字段，将其值从 'missing-key' 改为 'existing-key'。
```

### 后续优化
1. **CI/CD 检查**：在 CI/CD 流水线中加入 ConfigMap Key 的校验步骤，确保应用配置引用的 key 与部署的 ConfigMap 一致。
2. **配置管理**：统一管理 ConfigMap 和应用配置，避免手动编辑导致的key不匹配。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 状态 | `kubectl get pod rc-volume-configmap-missing-key -n aiops-e2e` | STATUS 从 `ContainerCreating` 变为 `Running` 或 `CrashLoopBackOff` |
| 2. 检查 Pod 事件 | `kubectl describe pod rc-volume-configmap-missing-key -n aiops-e2e` | 不再出现 `FailedMount` 事件 |

---
## ⚠️ 注意事项
- **无需重启其他 59 个正常 Pod**，集群整体健康。
- 如果修复后 Pod 进入 `CrashLoopBackOff` 状态，是 Pod 内应用本身的问题，与本次 ConfigMap 挂载故障无关，需另行排查应用日志。

---

## 📊 性能统计

├─ 总耗时: 1.0m
├─ 问题定位: 15.2s (25%) ✅
├─ 证据链采集: 16.8s (28%) ✅
├─ 根因分析: 14.0s (23%) ✅
├─ 汇总总结: 14.6s (24%) ✅
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
