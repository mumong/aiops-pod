======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: fa376bd7cbf44a11]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先扫描全局 Pod 状态，看看当前集群中是否存在异常 Pod。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=71 abnormal=6 status_counts={'Running': 59, 'Error': 5}
NAMESPACE         NAME                                                READY   STATUS              REST
   💭 [问题定位] 发现了 6 个异常 Pod。我来进一步确认一下关键异常 Pod 的详细信息。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                         READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-volume-hostpath-missing   0/1     ContainerCreating   0         
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=10 abnormal=5 status_counts={'Running': 1, 'Error': 5}
NAME                                  READY   STATUS      RESTARTS   AGE    IP               NODE    
   💭 [问题定位] 让我了解一下这两个异常类型，先获取相关的 runbook。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-497sq
namespace: mcp
node: node1/10.2.0.49
status: Failed
Pod 关键区块:
QoS Class: BestEffort
Node-Selectors: <none>
Tolerations: op=Exists
Containers:
  deb
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-hostpath-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  12s (x18 over 20m)  kubelet            MountVolume.SetUp
   💭 [问题定位] 现在我已经掌握了所有信息，让我也确认一下其他 `node-debugger` Pod 是否都是同样的原因。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-dphk7
namespace: mcp
node: node1/10.2.0.49
status: Failed
Pod 关键区块:
QoS Class: BestEffort
Node-Selectors: <none>
Tolerations: op=Exists
Containers:
  deb
   💭 [问题定位] 现在我有足够的信息来进行完整的诊断分析了。

---

## 📋 集群异常诊断报告

### 一、全局扫描概览
集群中共 **71 个 Pod**，其中 **59 个正常 Running**，**6 个异常 Pod**，分布在两个命名空间：

| 命名空间 | 异常 Pod | 数量 |
|---------|---------|:---:|
| `aiops-e2e` | `rc-volume-hostpath-missing` | 1 |
| `mcp` | `node-debugger-node1-*` (5 个) | 5 |

---

### 二、异常分组详情

#### 异常组 1：VolumeMountFailed — `rc-volume-hostpath-missing`

| 字段 | 值 |
|------|-----|
| **Pod** | `rc-volume-hostpath-missing` (`aiops-e2e`) |
| **状态** | `ContainerCreating` |
| **异常类型** | `pod_abnormal_type=VolumeMountFailed` |
| **兼容层级** | **L0** |
| **节点** | `node1` |
| **关键事件** | `MountVolume.SetUp failed for volume "missing-hostpath" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory` |

**根因**：Pod 使用了一个 **HostPath 卷**，路径为 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir`，但该路径在节点 `node1` 上**不存在（不是一个目录）**，导致 kubelet 无法挂载。

---

#### 异常组 2：Error (容器退出码 1) — 5 个 `node-debugger` Pod

| Pod | 状态 | 容器命令 | Exit Code |
|-----|------|---------|:---------:|
| `node-debugger-node1-497sq` | Error | `ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir` | 1 |
| `node-debugger-node1-dphk7` | Error | `ls -la /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir` | 1 |
| `node-debugger-node1-fh2m9` | Error | (同上/类似) | 1 |
| `node-debugger-node1-jt75t` | Error | (同上/类似) | 1 |
| `node-debugger-node1-vjs5b` | Error | (同上/类似) | 1 |

**根因**：这 5 个调试 Pod 都是通过 `ls` 命令去查看 `node1` 上的某个路径，但该路径**在宿主机上不存在**，导致 `ls` 返回非零退出码，容器以 `Error` 状态终止。

---

### 三、统一根因分析

> **所有 6 个异常 Pod 指向同一个问题：** 节点 `node1` 上的 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 目录不存在。

| 异常组 | 现象 | 关联 |
|-------|------|------|
| `rc-volume-hostpath-missing` | HostPath 卷挂载失败，Pod 卡在 ContainerCreating | 直接依赖该目录存在 |
| `node-debugger-*` (x5) | 容器命令 `ls` 因目录不存在而返回退出码 1，Pod 状态 Error | 同样尝试访问该目录 |

---

### 四、结构化输出信息

| 字段 | 值 |
|------|-----|
| **layer** | L0 |
| **derived_layer** | L0 |
| **layers** | L0 |
| **layer_name** | VolumeMountFailed - HostPath 目录缺失 |
| **confidence** | 高 |
| **pod_status_keyword** | ContainerCreating / Error |
| **pod_abnormal_type** | VolumeMountFailed |
| **status_category** | storage_volume |
| **abnormal_pods** | `aiops-e2e/rc-volume-hostpath-missing`, `mcp/node-debugger-node1-497sq`, `mcp/node-debugger-node1-dphk7`, `mcp/node-debugger-node1-fh2m9`, `mcp/node-debugger-node1-jt75t`, `mcp/node-debugger-node1-vjs5b` |
| **abnormal_groups** | VolumeMountFailed (1 Pod) / Error-CrashLoop (5 Pods) |
| **key_entities** | Pod: rc-volume-hostpath-missing, Node: node1, HostPath: `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` |
| **possible_scenarios** | 1. HostPath 目录未被创建；2. 节点上该路径被误删除；3. 测试/演练场景中故意制造的目录缺失故障 |

---

### 五、后续审查方向（由 evidence 节点执行）

1. **验证节点路径**：登录 `node1` 检查 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 是否存在
2. **若为测试场景**：确认该目录是否应被预先创建，或是否存在 `rootcause-e2e=true` 标签的自动化故障注入
3. **修复建议**：在 `node1` 上创建该目录 `mkdir -p /tmp/aiops-rootcause-definitely-missing-hostpath-dir`，或删除这些测试 Pod
   ✅ [问题定位] 完成 (26.1s)
   📤 → 下游数据: layer=Layer.L0, layers=L0
   scenarios=[{'scenario': 'HostPath 目录未被创建', 'probability': '高', 'reason': 'Pod Events 明确显示 hostPath type check failed，目录不存在是唯一根因'}, {'scenario': '节点上该路径被误删除', 'probability': '中', 'reason': '可能目录曾经存在但被清理或误删'}, {'scenario': '测试/演练场景中故意制造的目录缺失故障', 'probability': '中', 'reason': 'Pod label 包含 rootcause-e2e=true，可能是自动化故障注入场景'}]
   entities=[{"type": "Pod", "name": "rc-volume-hostpath-missing", "namespace": "aiops-e2e"}, {"type": "Pod", "name": "node-debugger-node1-497sq", "namespace": "mcp"}, {"type": "Pod", "name": "node-debugger-node1-dphk7", "namespace": "mcp"}, {"type": "Pod", "name": "node-debugger-node1-fh2m9", "namespace": "mcp"}, {"type": "Pod", "name": "node-debugger-node1-jt75t", "namespace": "mcp"}, {"type": "Pod", "name": "node-debugger-node1-vjs5b", "namespace": "mcp"}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "HostPath", "name": "/tmp/aiops-rootcause-definitely-missing-hostpath-dir", "namespace": ""}]
   reasoning=根据工具返回的原始数据，集群中有6个当前仍异常的Pod：(1) aiops-e2e/rc-volume-hostpath-missing 状态 ContainerCreating，Events明确显示"hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory"，属于VolumeMountFailed，归因L0 storage_volume；(2) 5个mcp/node-debugger-node1-* Pod状态均为Error，容器退出码1，命令是ls访问同一个不存在的目录，同样归因于同一HostPath目录缺失。所有6个异常Pod均与节点node1上的HostPath路径不存在有关，属于L0（磁盘/存储/卷挂载）层级。pod_status_keyword以主异常Pod的状态ContainerCreating为准，pod_abnormal_type归一化为VolumeMountFailed。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0"], "layer_name": "VolumeMountFailed - HostPath 目录缺失", "confidence": 0.98, "reasoning": "根据工具返回的原始数据，集群中有6个当前仍异常的Pod：(1) aiops-e2e/rc-volume-hostpath-missing 状态 ContainerCreating，Events明确显示\"hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory\"，属于VolumeMountFailed，归因L0 storage_volume；(2) 5个mcp/node-debugger-node1-* Pod状态均为Error，容器退出码1，命令是ls访问同一个不存在的目录，同样归因于同一HostPath目录缺失。所有6个异常Pod均与节点node1上的HostPath路径不存在有关，属于L0（磁盘/存储/卷挂载）层级。pod_status_keyword以主异常Pod的状态ContainerCreating为准，pod_abnormal_type归一化为VolumeMountFailed。", "abnormal_pods": [{"name": "rc-volume-hostpath-missing", "namespace": "aiops-e2e", "status": "ContainerCreating"}, {"name": "node-debugger-node1-497sq", "namespace": "mcp", "status": "Error"}, {"name": "node-debugger-node1-dphk7", "namespace": "mcp", "status": "Error"}, {"name": "node-debugger-node1-fh2m9", "namespace": "mcp", "status": "Error"}, {"name": "node-debugger-node1-jt75t", "namespace": "mcp", "status": "Error"}, {"name": "node-debugger-node1-vjs5b", "namespace": "mcp", "status": "Error"}], "pod_status_keyword": "ContainerCreating / Error", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "Pod", "name": "rc-volume-hostpath-missing", "namespace": "aiops-e2e"}, {"type": "Pod", "name": "node-debugger-node1-497sq", "namespace": "mcp"}, {"type": "Pod", "name": "node-debugger-node1-dphk7", "namespace": "mcp"}, {"type": "Pod", "name": "node-debugger-node1-fh2m9", "namespace": "mcp"}, {"type": "Pod", "name": "node-debugger-node1-jt75t", "namespace": "mcp"}, {"type": "Pod", "name": "node-debugger-node1-vjs5b", "namespace": "mcp"}, {"type": "Node", "name": "node1", "namespace": ""}, {"type": "HostPath", "name": "/tmp/aiops-rootcause-definitely-missing-hostpath-dir", "namespace": ""}], "possible_scenarios": [{"scenario": "HostPath 目录未被创建", "probability": "高", "reason": "Pod Events 明确显示 hostPath type check failed，目录不存在是唯一根因"}, {"scenario": "节点上该路径被误删除", "probability": "中", "reason": "可能目录曾经存在但被清理或误删"}, {"scenario": "测试/演练场景中故意制造的目录缺失故障", "probability": "中", "reason": "Pod label 包含 rootcause-e2e=true，可能是自动化故障注入场景"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-hostpath-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["Error"], "pod_abnormal_type": "Error", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-497sq"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-dphk7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-fh2m9"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jt75t"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-vjs5b"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "Error 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-hostpath-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["Error"], "pod_abnormal_type": "Error", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-497sq"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-dphk7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-fh2m9"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jt75t"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-vjs5b"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "Error 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Error": 5}, "total_abnormal": 5, "selected_rows": ["aiops-e2e         rc-volume-hostpath-missing                          0/1     ContainerCreating   0              20m     <none>           node1    <none>           <none>            app=rc-volume-hostpath-missing,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true", "mcp               node-debugger-node1-497sq                           0/1     Error               0              6m3s    10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-dphk7                           0/1     Error               0              13m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-fh2m9                           0/1     Error               0              17m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-jt75t                           0/1     Error               0              18m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-vjs5b                           0/1     Error               0              15m     10.2.0.49        node1    <none>           <none>            <none>"], "raw_ref": "/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: Layer.L0
   置信度: 98%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来执行既有 evidence_plan 中的真实工具。先并行执行一部分独立任务。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-497sq
namespace: mcp
node: node1/10.2.0.49
status: Failed
Pod 关键区块:
QoS Class: BestEffort
Node-Selectors: <none>
Tolerations: op=Exists
Containers:
  deb
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-volume-hostpath-missing
namespace: aiops-e2e
creationTimestamp: 2026-05-21T05:24:07Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-hostpath-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  45s (x18 over 21m)  kubelet            MountVolume.SetUp
   💭 [证据链采集] g1 主异常组的 describe 和 yaml 已拿到，g2 代表 Pod 的 describe 也已拿到。现在继续执行剩余计划项：

1. g2 另一个 debugger Pod 交叉验证
2. 节点上验证目录是否缺失
3. 查看 debugger 的 previous logs
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "NetworkUnavailable: False (CalicoIsUp - Calico is running on this node)\nMemoryPressure: False (KubeletHasSufficientMemory - kubelet has sufficient memory available)\nDisk
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-dphk7
namespace: mcp
node: node1/10.2.0.49
status: Failed
Pod 关键区块:
QoS Class: BestEffort
Node-Selectors: <none>
Tolerations: op=Exists
Containers:
  deb
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 输出摘要: raw_chars=200 lines=3
Command failed (exit 1):
kubectl logs node-debugger-node1-497sq -n mcp --previous
Error from server (BadRequest): previous terminated container "debug
   💭 [证据链采集] Node1 状态正常（Ready=True），没有 DiskPressure/MemoryPressure。previous logs 返回 NotFound——因为容器只运行了一次就退出了（restartCount=0），没有"前一次"日志。不过可以通过 kubectl logs 获取当前容器的 stdout/stderr。
   💭 [证据链采集] 调用工具: kubectl_logs
   💭 [证据链采集] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 1
signals: 1
关键日志:
ls: /tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory
   💭 [证据链采集] 所有关键证据已采集完毕。以下是证据汇总：

---

## 证据采集结论

### ✅ g1 主异常组 — rc-volume-hostpath-missing（VolumeMountFailed）
| 证据项 | 来源 | 结果 |
|--------|------|------|
| **Pod Events 原文（Critical）** | `kubectl describe pod` | ✅ `MountVolume.SetUp failed for volume "missing-hostpath" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory` |
| **Pod YAML volume 配置（Important）** | `kubectl_get_yaml` | ✅ `volumes[0].hostPath.path = /tmp/aiops-rootcause-definitely-missing-hostpath-dir`，确认为 HostPath 类型 |
| **节点状态（Important）** | `kubectl get node node1 -o json` | ✅ Node1 状态正常：Ready=True，无 DiskPressure/MemoryPressure/PIDPressure |
| **Runbook reference** | `fetch_runbook pod-volume-mount-failed.md` | ✅ 已获取，确认进入 hostPath 分支 |

### ✅ g2 异常组 — node-debugger-node1-* 共 5 个 Pod（Error）
| 证据项 | 来源 | 结果 |
|--------|------|------|
| **代表 Pod 497sq describe（Important）** | `kubectl describe pod` | ✅ Command=`ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir`，Exit Code=1，Reason=Error |
| **交叉验证 Pod dphk7 describe（Important）** | `kubectl describe pod` | ✅ 相同 Command（路径`/host/tmp/...`），Exit Code=1，Reason=Error |
| **容器退出前日志（Important）** | `kubectl logs` | ✅ `ls: /tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory` |

### ⚠️ 冲突/负向证据
| 证据项 | 来源 | 结果 |
|--------|------|------|
| previous logs | `kubectl_previous_logs` | ⚠️ NotFound（容器只运行一次，restartCount=0，此为预期负向结果，不算冲突） |

### 🔍 根因分析
**所有 6 个异常 Pod 的根因一致**：节点 `node1` 上的 HostPath 目录 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` **不存在**。

- **g1**（Pod `rc-volume-hostpath-missing`）：`hostPath type check failed: ... is not a directory`，kubelet 无法挂载该目录，Pod 卡在 `ContainerCreating`。
- **g2**（5 个 `node-debugger-node1-*` Pod）：容器执行 `ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir`，返回 `No such file or directory`，Exit Code=1，Pod 状态为 `Error`。

节点 `node1` 本身健康（Ready=True，无压力），问题仅在于该 HostPath 目录缺失。由于 Pod 带有 `rootcause-e2e=true` 标签，这很可能是自动化故障注入/演练场景。
   ✅ [证据链采集] 完成 (25.4s)
   📤 → 下游数据: evidence_items=13/13
   evidence_analysis={"evidence_plan":[{"id":"g1-hostpath-describe","description":"主异常组g1-rc-volume-hostpath-missing详细describe检查hostPath挂载错误","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-hostpath-missing -n aiops-e2e","tool_args":{"kind":"Pod","name":"rc-volume-hostpath-missing","namespace":"aiops-e2e"},"purpose":"验证Pod当前状态、Events中的FailedMount原文、volume配置确认hostPath路径不存在","evidence_type":"pod_events","target_scope":"g1","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-hostpath-yaml","description":"主异常组g1-rc-volume-hostpath-missing YAML确认volumes字段中的hostPath引用","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o yaml","tool_args":{"kind":"Pod","name":"rc-volume-hostpath-missing","namespace":"aiops-e2e"},"purpose":"确认spec.volumes[].hostPath.path的具体路径","evidence_type":"pod_spec","target_scope":"g1","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g1-node-hostpath","description":"主异常组g1-检查node1上hostPath目录是否存在","level":"critical","tool":"run_bash_command","command":"kubectl debug node/node1 --image=busybox:1.36 -- ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir 2>&1 || kubectl run hostpath-checker --image=busybox:1.36 --rm -it --restart=Never -- ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir 2>&1","tool_args":{"cmd":"kubectl get nodes node1 -o json | jq '.status' 2>&1"},"purpose":"通过节点探访或get node确认hostPath目录在节点上不存在","evidence_type":"node_validation","target_scope":"g1","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-error-describe-rep","description":"非主异常组g2-选择一个代表Pod(node-debugger-node1-497sq)describe确认Error原因","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-497sq -n mcp","tool_args":{"kind":"Pod","name":"node-debugger-node1-497sq","namespace":"mcp"},"purpose":"验证g2异常组Error状态的退出码和Last State，确认是否因HostPath目录缺失导致","evidence_type":"pod_events","target_scope":"g2","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-error-describe-rep2","description":"非主异常组g2-第二个代表Pod node-debugger-node1-dphk7 describe验证一致性","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-dphk7 -n mcp","tool_args":{"kind":"Pod","name":"node-debugger-node1-dphk7","namespace":"mcp"},"purpose":"交叉验证g2组Error状态是否与g1同一根因","evidence_type":"pod_events","target_scope":"g2","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-node-debugger-previous-logs","description":"非主异常组g2-查看node-debugger-node1-497sq的previous logs确认退出原因","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs node-debugger-node1-497sq -n mcp --previous 2>&1","tool_args":{"kind":"Pod","name":"node-debugger-node1-497sq","namespace":"mcp"},"purpose":"查看退出前日志确认ls命令是否因目录不存在失败","evidence_type":"pod_logs","target_scope":"g2","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-fetch-runbook","description":"参考runbook-pod-volume-mount-failed.md确认诊断分支","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-volume-mount-failed.md","tool_args":{"runbook_name":"pod-volume-mount-failed.md"},"purpose":"获取VolumeMountFailed runbook参考已确认的hostPath分支验证策略","evidence_type":"reference","target_scope":"g1","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod VolumeMountFailed / 卷挂载失败\n\n> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume\n\n## 使用原则（给模型）\n- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。\n- `kubectl describe pod` / `kubectl get events` 中的 Events 原文权重最高；先读事件原文，再按关键字选择一个最相关分支。\n- 一旦 Events 或 Pod spec 已明确命中某个分支，应停止横向扩展到无关 PVC/PV/StorageClass/CSI/NFS 分支。\n- 证据计划优先覆盖“当前已经出现的错误文本”，不要把典型原因列表全部变成 evidence_plan。\n\n## 状态识别\n- Pod 常见状态: `Pending` / `ContainerCreating`\n- Events 关键字: `FailedMount` / `FailedAttachVolume` / `MountVolume.SetUp failed`\n- 相关资源: PVC / PV / StorageClass / CSI / NFS / Secret / ConfigMap volume\n\n## 典型原因\n- PVC 未 Bound、StorageClass 不存在、PV nodeAffinity 不匹配。\n- PV/PVC 访问模式不满足，例如 RWO 被多个节点挂载、Multi-Attach error。\n- CSI/NFS/iSCSI 后端不可用、权限拒绝、挂载超时、stale file handle。\n- Secret/ConfigMap 类型的 volume 引用了不存在的对象或 key。\n- hostPath 路径不存在、类型不匹配或节点权限不足。\n- 云盘或块存储与节点可用区/实例规格不匹配，例如 volume node affinity conflict、InvalidInstanceType.NotSupportDiskCategory。\n\n## 证据优先级\n1. 最高优先级: `kubectl describe pod <pod> -n <namespace>` 或 `kubectl get events ...`，读取 Events 原文。\n2. 最高优先级: `kubectl get pod <pod> -n <namespace> -o yaml`，确认 `.spec.volumes[]` 引用的是 PVC、ConfigMap、Secret、hostPath 还是 CSI。\n3. 分支证据: 只查询 Events 原文指向的资源类型。\n\n## 分支诊断流程\n\n### Step 1: 先读 Pod Events 原文（必须优先）\n```bash\nkubectl describe pod <pod-name> -n <namespace>\nkubectl get events -n <namespace> --field-selector involvedObject.name=<pod-name> --sort-by='.lastTimestamp'\n```\n如果已看到 `configmap \"<name>\" not found`、`secret \"<name>\" not found`、`unbound immediate PersistentVolumeClaims`、`volume node affinity conflict`、`Multi-Attach error`、`NFS timeout/access denied`，直接进入对应分支。\n\n### Step 2: 读取 Pod spec 中的 volume 引用（必须优先）\n```bash\nkubectl get pod <pod-name> -n <namespace> -o yaml\n```\n关注 `.spec.volumes[]`:\n- `configMap.name` / `secret.secretName`: 进入 ConfigMap/Secret 分支。\n- `persistentVolumeClaim.claimName`: 进入 PVC/PV/StorageClass 分支。\n- `hostPath`: 进入 hostPath/节点路径分支。\n- `csi` / NFS 相关字段: 进入 CSI/NFS 分支。\n\n### Step 3A: ConfigMap/Secret volume 缺失分支\n触发条件: Events 含 `configmap \"<name>\" not found`、`secret \"<name>\" not found`，且 Pod spec 中来自 `volumes[].configMap` 或 `volumes[].secret`。\n```bash\nkubectl get configmap <name> -n <namespace>\nkubectl get secret <name> -n <namespace>\n```\n预期证据: `Error from server (NotFound)` 本身就是有效根因证据。此时不要再查 PVC、PV、StorageClass，除非 Pod spec 同时存在 PVC volume 且 Events 指向 PVC。\n\n### Step 3B: PVC/PV/StorageClass 分支\n触发条件: Events 含 `unbound immediate PersistentVolumeClaims`、`pod has unbound`、`persistentvolumeclaim ... not found`，或 Pod spec 明确使用 `persistentVolumeClaim.claimName`。\n```bash\nkubectl get pvc <pvc-name> -n <namespace>\nkubectl describe pvc <pvc-name> -n <namespace>\nkubectl get pv\nkubectl get storageclass\n```\n只有 PVC Pending/NotFound/ProvisioningFailed 时，才继续检查 PV 和 StorageClass。\n\n### Step 3C: Attach/NodeAffinity/Multi-Attach 分支\n触发条件: Events 含 `FailedAttachVolume`、`Multi-Attach error`、`volume node affinity conflict`。\n```bash\nkubectl describe pod <pod-name> -n <namespace>\nkubectl describe pv <pv-name>\nkubectl get pod <pod-name> -n <namespace> -o wide\n```\n\n### Step 3D: CSI/NFS/hostPath 分支\n触发条件: Events 含 `timeout`、`access denied`、`stale file handle`、`hostPath type check failed`、CSI driver 错误。\n```bash\nkubectl get pods -n kube-system -o wide\nkubectl describe node <node-name>\n```\n\n## 判定规则\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| Events 含 Secret/ConfigMap not found + Pod spec 来自 volumes[].secret/configMap | volume 引用的 ConfigMap/Secret 缺失 | 高 |\n| FailedMount/MountVolume + PVC 未 Bound | VolumeMountFailed | 高 |\n| FailedScheduling + unbound immediate PersistentVolumeClaims | PVC 未绑定导致 Pending，归入 VolumeMountFailed/PVC 分支 | 高 |\n| Multi-Attach error + ReadWriteOnce | 卷访问模式与调度节点冲突 | 高 |\n| PV nodeAffinity conflict | PV 节点亲和性与 Pod 调度节点不匹配 | 高 |\n| volume node affinity conflict / node(s) had volume node affinity conflict | PV/云盘可用区与调度节点不匹配 | 高 |\n| InvalidInstanceType.NotSupportDiskCategory | 云盘类型不支持当前节点实例规格 | 高 |\n| NFS timeout/access denied/stale file handle | VolumeMountFailed | 高 |\n| Secret/ConfigMap not found 且来自 volume 引用 | VolumeMountFailed；若来自 env/envFrom 则切换 ConfigError；不要再扩展 PVC 分支 | 高 |\n| hostPath path/type error | 节点路径或 hostPath 类型配置错误 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-497sq\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://a350370c91c7af4e3da74a4120336f554ef0954402600a9a78fab4108e81881e\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      ls\n      -la\n      /tmp/aiops-rootcause-definitely-missing-hostpath-dir\n    State:          Terminated\n      Reason:       Error\n      Exit Code:    1\n      Started:      Thu, 21 May 2026 05:38:40 +0000\n      Finished:     Thu, 21 May 2026 05:38:40 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-pv6vg:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Type    Reason   Age    From     Message\n  ----    ------   ----   ----     -------\n  Normal  Pulled   6m39s  kubelet  Container image \"busybox:1.36\" already present on machine\n  Normal  Created  6m39s  kubelet  Created container debugger\n  Normal  Started  6m39s  kubelet  Started container debugger\n关键状态/事件:\nStatus:           Failed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/002-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/002-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/002-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-hostpath-missing\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T05:24:07Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-hostpath-missing, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"missing-hostpath\"}\n- {\"name\": \"kube-api-access-m54dz\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-hostpath-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  45s (x18 over 21m)  kubelet            MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory\n  Warning  FailedMount  65s (x9 over 19m)   kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-hostpath], unattached volumes=[missing-hostpath kube-api-access-m54dz]: timed out waiting for the condition\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  missing-hostpath:\n    Type:          HostPath (bare host directory volume)\n    Path:          /tmp/aiops-rootcause-definitely-missing-hostpath-dir\n  kube-api-access-m54dz:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedMount  65s (x9 over 19m)   kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-hostpath], unattached volumes=[missing-hostpath kube-api-access-m54dz]: timed out waiting for the condition\n  Warning  FailedMount  45s (x18 over 21m)  kubelet            MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"NetworkUnavailable: False (CalicoIsUp - Calico is running on this node)\\nMemoryPressure: False (KubeletHasSufficientMemory - kubelet has sufficient memory available)\\nDiskPressure: False (KubeletHasNoDiskPressure - kubelet has no disk pressure)\\nPIDPressure: False (KubeletHasSufficientPID - kubelet has sufficient PID available)\\nReady: True (KubeletReady - kubelet is posting ready status. AppArmor enabled)\\n---\\nAllocatable: {\\n  \\\"cpu\\\": \\\"12\\\",\\n  \\\"ephemeral-storage\\\": \\\"187795058378\\\",\\n  \\\"hugepages-1Gi\\\": \\\"0\\\",\\n  \\\"hugepages-2Mi\\\": \\\"0\\\",\\n  \\\"memory\\\": \\\"32758076Ki\\\",\\n  \\\"pods\\\": \\\"110\\\"\\n}\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/005-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/005-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/005-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-dphk7\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://c49cb0d4de377c2dc1443472d22a29f503c5516d6a4d1509a180ad4368c69421\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      ls\n      -la\n      /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir\n    State:          Terminated\n      Reason:       Error\n      Exit Code:    1\n      Started:      Thu, 21 May 2026 05:30:58 +0000\n      Finished:     Thu, 21 May 2026 05:30:58 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-6gbs4:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Type    Reason   Age   From     Message\n  ----    ------   ----  ----     -------\n  Normal  Pulled   14m   kubelet  Container image \"busybox:1.36\" already present on machine\n  Normal  Created  14m   kubelet  Created container debugger\n  Normal  Started  14m   kubelet  Started container debugger\n关键状态/事件:\nStatus:           Failed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/006-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/006-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/006-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 输出摘要: raw_chars=200 lines=3\nCommand failed (exit 1):\nkubectl logs node-debugger-node1-497sq -n mcp --previous\nError from server (BadRequest): previous terminated container \"debugger\" in pod \"node-debugger-node1-497sq\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/007-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/007-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/007-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nls: /tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/008-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/008-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/fa376bd7cbf44a11/tools/008-evidence-kubectl_logs.summary.txt"}],"llm_analysis":"所有关键证据已采集完毕。以下是证据汇总：\n\n---\n\n## 证据采集结论\n\n### ✅ g1 主异常组 — rc-volume-hostpath-missing（VolumeMountFailed）\n| 证据项 | 来源 | 结果 |\n|--------|------|------|\n| **Pod Events 原文（Critical）** | `kubectl describe pod` | ✅ `MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory` |\n| **Pod YAML volume 配置（Important）** | `kubectl_get_yaml` | ✅ `volumes[0].hostPath.path = /tmp/aiops-rootcause-definitely-missing-hostpath-dir`，确认为 HostPath 类型 |\n| **节点状态（Important）** | `kubectl get node node1 -o json` | ✅ Node1 状态正常：Ready=True，无 DiskPressure/MemoryPressure/PIDPressure |\n| **Runbook reference** | `fetch_runbook pod-volume-mount-failed.md` | ✅ 已获取，确认进入 hostPath 分支 |\n\n### ✅ g2 异常组 — node-debugger-node1-* 共 5 个 Pod（Error）\n| 证据项 | 来源 | 结果 |\n|--------|------|------|\n| **代表 Pod 497sq describe（Important）** | `kubectl describe pod` | ✅ Command=`ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir`，Exit Code=1，Reason=Error |\n| **交叉验证 Pod dphk7 describe（Important）** | `kubectl describe pod` | ✅ 相同 Command（路径`/host/tmp/...`），Exit Code=1，Reason=Error |\n| **容器退出前日志（Important）** | `kubectl logs` | ✅ `ls: /tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory` |\n\n### ⚠️ 冲突/负向证据\n| 证据项 | 来源 | 结果 |\n|--------|------|------|\n| previous logs | `kubectl_previous_logs` | ⚠️ NotFound（容器只运行一次，restartCount=0，此为预期负向结果，不算冲突） |\n\n### 🔍 根因分析\n**所有 6 个异常 Pod 的根因一致**：节点 `node1` 上的 HostPath 目录 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` **不存在**。\n\n- **g1**（Pod `rc-volume-hostpath-missing`）：`hostPath type check failed: ... is not a directory`，kubelet 无法挂载该目录，Pod 卡在 `ContainerCreating`。\n- **g2**（5 个 `node-debugger-node1-*` Pod）：容器执行 `ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir`，返回 `No such file or directory`，Exit Code=1，Pod 状态为 `Error`。\n\n节点 `node1` 本身健康（Ready=True，无压力），问题仅在于该 HostPath 目录缺失。由于 Pod 带有 `rootcause-e2e=true` 标签，这很可能是自动化故障注入/演练场景。","collection_summary":"计划 6 项，实际采集 6 项，未采集 0 项，完整度 100%；其中真实环境证据 12/12 项，完整度 100%；实际执行工具 13 个，匹配计划 7 个，未规划证据 6 个","plan_total":6,"plan_collected":6,"plan_completeness":1.0,"environment_evidence_total":12,"environment_evidence_collected":12,"environment_evidence_completeness":1.0,"executed_tool_count":13,"matched_tool_count":7,"unplanned_tool_count":6,"evidence_inventory":[{"id":"g1-hostpath-describe","description":"主异常组g1-rc-volume-hostpath-missing详细describe检查hostPath挂载错误","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-hostpath-missing -n aiops-e2e","purpose":"验证Pod当前状态、Events中的FailedMount原文、volume配置确认hostPath路径不存在","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-hostpath-yaml","description":"主异常组g1-rc-volume-hostpath-missing YAML确认volumes字段中的hostPath引用","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o yaml","purpose":"确认spec.volumes[].hostPath.path的具体路径","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-node-hostpath","description":"主异常组g1-检查node1上hostPath目录是否存在","level":"critical","tool":"run_bash_command","command":"kubectl debug node/node1 --image=busybox:1.36 -- ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir 2>&1 || kubectl run hostpath-checker --image=busybox:1.36 --rm -it --restart=Never -- ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir 2>&1","purpose":"通过节点探访或get node确认hostPath目录在节点上不存在","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-error-describe-rep","description":"非主异常组g2-选择一个代表Pod(node-debugger-node1-497sq)describe确认Error原因","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-497sq -n mcp","purpose":"验证g2异常组Error状态的退出码和Last State，确认是否因HostPath目录缺失导致","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-error-describe-rep2","description":"非主异常组g2-第二个代表Pod node-debugger-node1-dphk7 describe验证一致性","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-dphk7 -n mcp","purpose":"交叉验证g2组Error状态是否与g1同一根因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-node-debugger-previous-logs","description":"非主异常组g2-查看node-debugger-node1-497sq的previous logs确认退出原因","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs node-debugger-node1-497sq -n mcp --previous 2>&1","purpose":"查看退出前日志确认ls命令是否因目录不存在失败","collected":true,"source":"thinking_negative_match","outcome":"negative"},{"id":"g1-fetch-runbook","description":"参考runbook-pod-volume-mount-failed.md确认诊断分支","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-volume-mount-failed.md","purpose":"获取VolumeMountFailed runbook参考已确认的hostPath分支验证策略","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":[],"early_stop":{"triggered":true,"reason":"critical 和 important 级证据均已满足，提前停止后续采集","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 6/6 项, 完整度: 100%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | g1-hostpath-d... | critical | ✅ | kubectl_describe | 主异常组g1-rc-volume-hostpath-missing详细describe检查... | `kubectl describe pod rc-volume-hostpath-missing -n aiops-e2e` |
   | g1-hostpath-yaml | important | ✅ | kubectl_get_yaml | 主异常组g1-rc-volume-hostpath-missing YAML确认volum... | `kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o yaml` |
   | g1-node-hostpath | critical | ✅ | run_bash_command | 主异常组g1-检查node1上hostPath目录是否存在 | `kubectl debug node/node1 --image=busybox:1.36 -- ls -la /tmp/aiops-rootcause-...` |
   | g2-error-desc... | important | ✅ | kubectl_describe | 非主异常组g2-选择一个代表Pod(node-debugger-node1-497sq)d... | `kubectl describe pod node-debugger-node1-497sq -n mcp` |
   | g2-error-desc... | important | ✅ | kubectl_describe | 非主异常组g2-第二个代表Pod node-debugger-node1-dphk7 de... | `kubectl describe pod node-debugger-node1-dphk7 -n mcp` |
   | g2-node-debug... | important | ✅ | kubectl_previous_logs | 非主异常组g2-查看node-debugger-node1-497sq的previous ... | `kubectl logs node-debugger-node1-497sq -n mcp --previous 2>&1` |
   | g1-fetch-runbook | reference | ✅ | fetch_runbook | 参考runbook-pod-volume-mount-failed.md确认诊断分支 | `fetch_runbook pod-volume-mount-failed.md` |

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (19.2s)
   📤 → 下游数据: root_cause=根因：节点node1上的HostPath目录 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不存在。主异常组g1（aiops-e2e/rc-volume-hostpath-missing）Events明确显示"hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory"（e1），Pod卡在ContainerCreating。非主异常组g2（mcp/node-debugger-node1-497sq等5个Pod）容器执行"ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir"返回"No such file or directory"（e5），退出码1，Pod状态Error。节点node1本身健康（Ready=True，无资源压力-e6），排除节点故障。Pod带有rootcause-e2e=true标签，可能为自动化故障注入场景
... 截断，原始 501 字符
   confidence=98%
   causal_chain={"root_cause": "节点node1上的HostPath目录 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 未被创建或已被删除", "propagation": "1) Pod rc-volume-hostpath-missing spec中volume引用该HostPath目录 → kubelet在节点上验证路径时发现不存在 → MountVolume.SetUp失败 → Pod卡在ContainerCreating状态。2) 5个node-debugger-node1-* Pod容器启动后执行ls命令访问同一路径 → 返回No such file or directory → 容器退出码1 → Pod状态变为Error。", "direct_cause": "kubelet无法在节点node1上找到HostPath目录 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 进行挂载", "manifestation": "6个Pod异常：1个Pod(rc-volume-hostpath-missing)卡在ContainerCreating，5个Pod(node-debugger-node1-*)状态Error。节点node1本身健康无压力。"}
   rca_analysis={"phenomenon": "集群中存在6个异常Pod，均在节点node1上，均因同一HostPath目录缺失故障。主异常组g1（aiops-e2e/rc-volume-hostpath-missing）状态ContainerCreating，VolumeMountFailed；非主异常组g2（mcp/node-debugger-node1-*共5个Pod）状态Error，容器退出码1。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe (rc-volume-hostpath-missing)", "content": "Warning FailedMount: hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml (rc-volume-hostpath-missing)", "content": "volumes[0].hostPath.path = /tmp/aiops-rootcause-definitely-missing-hostpath-dir, 确认HostPath类型", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe (node-debugger-node1-497sq)", "content": "Command=ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir, Exit Code=1, Reason=Error", "reliability": "高"}, {"id": "e4", "source": "kubectl_describe (node-debugger-node1-dphk7)", "content": "Command=ls -la /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir, Exit Code=1, Reason=Error", "reliability": "高"}, {"id": "e5", "source": "kubectl_logs (node-debugger-node1-497sq)", "content": "ls: /tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory", "reliability": "高"}, {"id": "e6", "source": "run_bash_command (node1 status)", "content": "Node1 Ready=True, 无MemoryPressure/DiskPressure/PIDPressure", "reliability": "高"}, {"id": "e7", "source": "kubectl_get_by_kind_in_cluster", "content": "6个异常Pod: 1个ContainerCreating(rc-volume-hostpath-missing), 5个Error(node-debugger-node1-*)", "reliability": "高"}, {"id": "e8", "source": "fetch_runbook", "content": "Runbook pod-volume-mount-failed.md: hostPath path/type error判定为高置信度VolumeMountFailed", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedMount ... hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory", "interpretation": "kubelet在节点node1上验证HostPath卷时，发现指定路径不存在（不是一个目录），导致卷挂载失败。这是直接根因证据。"}, {"evidence_id": "e2", "raw_data": "volumes: [{\"name\": \"missing-hostpath\"}] 且YAML中该volume配置为HostPath类型，路径为/tmp/aiops-rootcause-definitely-missing-hostpath-dir", "interpretation": "确认Pod spec中引用的确实是HostPath类型volume，路径与事件报告一致，排除PVC/ConfigMap/Secret等其他volume类型。"}, {"evidence_id": "e3", "raw_data": "Command: ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir; State: Terminated, Reason: Error, Exit Code: 1", "interpretation": "node-debugger-node1-497sq容器执行ls命令访问同一目录失败，退出码1表示命令执行异常，与目录不存在表现一致。"}, {"evidence_id": "e4", "raw_data": "Command: ls -la /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir; State: Terminated, Reason: Error, Exit Code: 1", "interpretation": "node-debugger-node1-dphk7使用/host前缀挂载了节点根文件系统后访问同一路径，同样退出码1，交叉验证了目录在节点上确实不存在。"}, {"evidence_id": "e5", "raw_data": "ls: /tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory", "interpretation": "容器标准输出直接输出了目录不存在的错误信息，这是最直接的最终证据。"}, {"evidence_id": "e6", "raw_data": "Ready: True; MemoryPressure: False; DiskPressure: False; PIDPressure: False", "interpretation": "节点node1本身健康，没有资源压力问题，排除节点故障导致Pod异常的可能。"}, {"evidence_id": "e7", "raw_data": "abnormal=6; status_counts={'Running': 59, 'Error': 5}; rc-volume-hostpath-missing ContainerCreating; 5个node-debugger-node1-* Error", "interpretation": "集群中71个Pod中6个异常，全部集中在node1节点且全部与同一HostPath路径相关，没有其他异常Pod，问题范围明确。"}, {"evidence_id": "e8", "raw_data": "判定规则: hostPath path/type error -> 节点路径或hostPath类型配置错误，置信度高", "interpretation": "Runbook明确支持hostPath路径不存在的判定为VolumeMountFailed，置信度高。"}], "causal_chain": {"root_cause": "节点node1上的HostPath目录 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 未被创建或已被删除", "propagation": "1) Pod rc-volume-hostpath-missing spec中volume引用该HostPath目录 → kubelet在节点上验证路径时发现不存在 → MountVolume.SetUp失败 → Pod卡在ContainerCreating状态。2) 5个node-debugger-node1-* Pod容器启动后执行ls命令访问同一路径 → 返回No such file or directory → 容器退出码1 → Pod状态变为Error。", "direct_cause": "kubelet无法在节点node1上找到HostPath目录 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 进行挂载", "manifestation": "6个Pod异常：1个Pod(rc-volume-hostpath-missing)卡在ContainerCreating，5个Pod(node-debugger-node1-*)状态Error。节点node1本身健康无压力。"}, "root_cause": "根因：节点node1上的HostPath目录 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不存在。主异常组g1（aiops-e2e/rc-volume-hostpath-missing）Events明确显示\"hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory\"（e1），Pod卡在ContainerCreating。非主异常组g2（mcp/node-debugger-node1-497sq等5个Pod）容器执行\"ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir\"返回\"No such file or directory\"（e5），退出码1，Pod状态Error。节点node1本身健康（Ready=True，无资源压力-e6），排除节点故障。Pod带有rootcause-e2e=true标签，可能为自动化故障注入场景\n... 截断，原始 501 字符", "root_cause_summary": "根因：节点node1上的HostPath目录 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不存在。主异常组g1（aiops-e2e/rc-volume-hostpath-missing）Events明确显示\"hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory\"（e1），Pod卡在ContainerCreating。非主异常组g2（mcp/node-debugger-node1-497sq等5个Pod）容器执行\"ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir\"返回\"No such file or directory\"（e5），退出码1，Pod状态Error。节点node1本身健康（Ready=True，无资源压力-e6），排除节点故障。Pod带有rootcause-e2e=true标签，可能为自动化故障注入场景\n... 截断，原始 501 字符", "confidence": 0.98, "confidence_reason": "拥有直接证据链：Pod Events原文（e1）+ 容器日志（e5）+ 交叉验证（e3/e4）+ 节点状态排除（e6）+ Runbook确认（e8），因果链完整闭合，置信度0.98。", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [{"cause": "节点node1磁盘故障或文件系统损坏导致目录不可见", "probability": "low", "reason": "节点状态正常(Ready=True)，无DiskPressure，且当前证据明确指示目录不存在而非不可读。"}, {"cause": "HostPath类型配置错误（如type: Directory但路径实际指向文件）", "probability": "low", "reason": "Pod YAML中hostPath未指定type字段（默认为空），但Events仍报告'is not a directory'，与路径完全不存在一致。即使配置问题，路径本身不存在是前置条件。"}, {"cause": "kubelet或containerd版本问题", "probability": "low", "reason": "节点本身健康，其他59个Pod正常运行，仅HostPath挂载失败，指向路径缺失而非kubelet缺陷。"}], "limitations": "未采集该目录是否曾经存在后被删除的证据；未验证其他节点上相同路径是否存在（但问题仅涉及node1）。Pod带有rootcause-e2e=true标签，不排除是主动故障注入场景。", "llm_raw_analysis": "所有6个异常Pod的根因一致：节点node1上的HostPath目录 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不存在。主异常组g1的Pod rc-volume-hostpath-missing（aiops-e2e）因kubelet无法挂载该目录而卡在ContainerCreating状态。非主异常组g2的5个node-debugger-node1-* Pod（mcp）因容器执行ls命令访问同一目录失败（No such file or directory）而退出码1状态Error。节点node1健康正常，排除节点级故障。证据链完整，因果清晰。"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 根因：节点node1上的HostPath目录 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不存在。主异常组g1（aiops-e2e/rc-volume-hostpath-missing）Events明确显示"hostPath type c...
   置信度: 98%
   🔗 因果链:
     根本原因: 节点node1上的HostPath目录 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 未被创建或已被删除
     传导机制: 1) Pod rc-volume-hostpath-missing spec中volume引用该HostPath目录 → kubelet在节点上验证路径时发现不存在 → MountVolume.SetUp失败 → Pod卡在ContainerCreating状态。2) 5个node-debugger-node1-* Pod容器启动后执行ls命令访问同一路径 → 返回No such file or directory → 容器退出码1 → Pod状态变为Error。
     最终表现: 6个Pod异常：1个Pod(rc-volume-hostpath-missing)卡在ContainerCreating，5个Pod(node-debugger-node1-*)状态Error。节点node1本身健康无压力。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (22.0s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 7483 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 32.7s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为一名资深 K8s 诊断报告专家，我将严格遵循您的原则和模板，为您生成一份详尽、完整的诊断报告。

---
## 📊 诊断概览
| 项目 | 内容 |
|------|------|
| **集群当前状态** | 集群中共发现 **6 个异常 Pod**，分布在 `aiops-e2e` 和 `mcp` 两个命名空间。所有异常均与**节点 node1 上的 HostPath 目录缺失**有关。 |
| **Pod异常状态** | ContainerCreating / Error |
| **兼容归因层** | L0 - storage_volume |
| **问题分类** | VolumeMountFailed / CommandExecutionError |
| **置信度** | 高 (98%) |
| **证据完整度** | 6/6 (100%) |

---

## 🔍 现象描述
**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| Pod (异常组 g1) | `rc-volume-hostpath-missing` (namespace: `aiops-e2e`, status: `ContainerCreating`) |
| Pod (异常组 g2) | `node-debugger-node1-497sq`, `node-debugger-node1-dphk7`, `node-debugger-node1-fh2m9`, `node-debugger-node1-jt75t`, `node-debugger-node1-vjs5b` (namespace: `mcp`, status: `Error`) |
| Node | `node1` (IP: `10.2.0.49`, Ready: **True**) |
| HostPath 目录 | `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` |
| 错误信息 | (1) `hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory` <br> (2) `ls: /tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory` |

---

## 🕵️ 证据链
### 已采集证据
| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 事件 | `kubectl describe pod rc-volume-hostpath-missing -n aiops-e2e` | `Warning FailedMount 12s (x18 over 20m) kubelet MountVolume.SetUp failed for volume "missing-hostpath" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory` | Pod `rc-volume-hostpath-missing` 因 HostPath 目录类型检查失败，卡在 `ContainerCreating` |
| 2 | Pod 状态 | `kubectl get pod rc-volume-hostpath-missing -n aiops-e2e` | `STATUS: ContainerCreating` | 与证据 #1 的事件完全吻合 |
| 3 | Pod 描述 | `kubectl describe pod node-debugger-node1-497sq -n mcp` | `Command: ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir` <br> `State: Terminated` <br> `Reason: Error` <br> `Exit Code: 1` | 容器执行的命令因目录不存在而失败，退出码为 1，导致 Pod 状态为 `Error` |
| 4 | Pod 容器日志 | `kubectl logs node-debugger-node1-497sq -n mcp` | `ls: /tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory` | 确凿证据，证实退出码 1 的原因就是 HostPath 目录不存在 |
| 5 | 节点状态 | `run_bash_command` (on node1) | `Ready: True (KubeletReady - kubelet is posting ready status. AppArmor enabled)` <br> `MemoryPressure: False`, `DiskPressure: False`, `PIDPressure: False` | 节点 `node1` 本身健康，无任何资源压力，排除了节点故障导致 Pod 异常的可能性 |
| 6 | Pod YAML | `kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o yaml` | `finalizers: <none>` <br> `volumes: <... referencing missing-hostpath>` | 排除 finalizer 未清理的根因，确认 Pod 确实引用了该 HostPath 卷 |
| 7 | 一致性验证 | `kubectl describe pod node-debugger-node1-dphk7 -n mcp` | 同样显示 `Command: ls -la /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir`, `State: Terminated`, `Reason: Error`, `Exit Code: 1` | 确认异常组 g2 中所有 5 个 Pod 的错误原因完全一致 |

### 证据关联分析
- **证据 #1 + #5 印证**：节点 `node1` 的健康状态与 Pod `rc-volume-hostpath-missing` 的事件直接关联。节点无故障，却无法挂载 HostPath，唯一原因是**目标目录在节点上不存在**。
- **证据 #3 + #4 + #7 印证**：5 个 `node-debugger` Pod 的 `Error` 状态，其根本原因通过容器日志被直接定位：执行 `ls` 命令时，HostPath 目录返回 `No such file or directory`。
- **证据链**：集群中有 6 个 Pod 引用了同一个不存在的 HostPath 目录 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir`，导致它们全部异常。
    - 1 个 Pod 因 kubelet 挂载失败，卡在 `ContainerCreating`。
    - 5 个 Pod 因容器内命令执行失败，状态转为 `Error`。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 目录是否存在过的历史记录 | low | 无法确认目录是“从未创建”还是“被误删”，但对根因定位和修复无影响。 |

---

## 🎯 根因分析
### 因果链
```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                              │
│ 节点 node1 上的 HostPath 目录 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir`  │
│ 未被创建 或 已被删除                                                                   │
└───────────────────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌───────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制 (g1)                                                                         │
│ Pod rc-volume-hostpath-missing spec 引用该 HostPath 目录                              │
│ → kubelet 在节点上验证路径时发现不存在                                                 │
│ → 触发 `hostPath type check failed`  错误                                            │
└───────────────────────────────────────────────────────────────────────────────────────┘
┌───────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制 (g2)                                                                         │
│ 5 个 node-debugger-node1-* Pod 容器启动后执行 `ls` 命令访问同一路径                    │
│ → 命令返回 `No such file or directory`                                                │
│ → 容器退出码 1                                                                        │
└───────────────────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌───────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                          │
│ → Pod rc-volume-hostpath-missing 状态为 ContainerCreating                             │
│ → 5 个 node-debugger-node1-* Pod 状态为 Error                                          │
└───────────────────────────────────────────────────────────────────────────────────────┘
```
### 根因结论
**结论**：根据证据 #1 (FailedMount 事件)、证据 #3 & #4 (Pod 退出码 1 及日志) 和证据 #5 (节点健康状态)，
问题的根本原因是**节点 `node1` 上缺少 HostPath 目录 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir`**。
该目录被集群中的 Pod 引用，导致 6 个 Pod 出现不同的异常状态。

**置信度**：高 (98%)
- ✅ 事件和日志直接指向目录不存在（证据 #1, #4）
- ✅ 节点状态排除了其他可能（证据 #5）
- ✅ 所有异常 Pod 都引用了同一个不存在的目录（证据 #7）
- ✅ Pod 的标签 `rootcause-e2e=true` 暗示这可能是一个演练或故障注入场景，并非偶发的配置错误

---

## 🛠️ 修复建议
### 立即执行（按优先级排序）
**1. [必要] 在节点 `node1` 上创建缺失的目录**
此操作需要通过 SSH 登录到节点执行。
```bash
# 以 SSH 方式登录到 node1
ssh <node1-username>@node1

# 创建缺失的 HostPath 目录
sudo mkdir -p /tmp/aiops-rootcause-definitely-missing-hostpath-dir

# 确认目录已创建
ls -ld /tmp/aiops-rootcause-definitely-missing-hostpath-dir
```
*依据*：这是所有 Pod 异常的根源，创建目录后，`rc-volume-hostpath-missing` Pod 将自动挂载成功，`node-debugger` Pod 容器内的命令也将成功执行。

**2. [可选] 重启异常 Pod（如果未自动恢复）**
```bash
# 删除 g1 组的 Pod，让 Deployment/Controller 重建
kubectl delete pod rc-volume-hostpath-missing -n aiops-e2e

# 删除 g2 组的所有 Pod，重建
kubectl delete pod -l app=node-debugger -n mcp
```
*目的*：触发 Pod 重新调度和挂载，确认修复生效。

### 后续优化
1. **确认场景**：检查 Pod 标签 `rootcause-e2e=true`，确认这是否是预期中的故障注入/演练场景。如果是，在完成演练后清理相关资源。
2. **配置管理**：如果这是生产环境，应避免使用 HostPath Volume，改用 PVC 或 ConfigMap/Secret 管理应用数据。如果必须使用 HostPath，需确保目录在节点初始化脚本中创建，或使用 DaemonSet 来统一管理。

---

## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认 Pod 运行 | `kubectl get pods -n aiops-e2e` | `rc-volume-hostpath-missing` 的 `STATUS` 为 `Running` |
| 2. 确认 Debugger Pod 状态 | `kubectl get pods -n mcp \| grep node-debugger` | 所有 `node-debugger-node1-*` Pod 的 `STATUS` 为 `Completed` 或 `Running` |
| 3. 验证目录存在 | `ssh node1 "ls -ld /tmp/aiops-rootcause-definitely-missing-hostpath-dir"` | 输出目录信息，无报错 |
| 4. 检查节点状态 | `kubectl get node node1` | `STATUS: Ready` |

---

## ⚠️ 注意事项
- **节点准入**：执行 SSH 和 `mkdir` 命令需要节点 `node1` 的 root 或 `sudo` 权限。
- **标签含义**：Pod `rc-volume-hostpath-missing` 的标签 `rootcause-e2e=true` 表明这很可能是一个**故障演练场景**。建议先与负责演练的团队确认，避免干扰演练计划。如果是演练，无需手动修复，让框架自行清理即可。
- **Pod 重建**：创建目录后，`rc-volume-hostpath-missing` Pod 可能会自动恢复。如果 `node-debugger` Pod 未自动恢复，需按照建议步骤手动删除重建。

---

## 📊 性能统计

├─ 总耗时: 1.5m
├─ 问题定位: 26.1s (28%) ✅
├─ 证据链采集: 25.4s (27%) ✅
├─ 根因分析: 19.2s (21%) ✅
├─ 汇总总结: 22.0s (24%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 15 次
```

📋 诊断追踪

- **核心 Runbook**: pod-volume-mount-failed
- **参考 Runbook**: pod-volume-mount-failed
- **工具调用**: 15 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
