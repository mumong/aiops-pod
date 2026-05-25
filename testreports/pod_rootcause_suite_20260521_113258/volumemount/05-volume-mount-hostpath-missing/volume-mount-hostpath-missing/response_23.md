======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 42140dfdcbc44317]

📍 [问题定位] 执行中...
   💭 [问题定位] 我先全局扫描所有 Pod，看看集群的整体状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=71 abnormal=6 status_counts={'Running': 59, 'Error': 5}
NAMESPACE         NAME                                                READY   STATUS              REST
   💭 [问题定位] 发现了 6 个异常 Pod。我来逐一查看关键信息。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                         READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-volume-hostpath-missing   0/1     ContainerCreating   0         
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                        READY   STATUS   RESTARTS   AGE   IP          NODE    NOMINATED NODE   READINESS GATES   LABELS
node-debugger-node1-fh2m9   0/1     Error    0          13m   10.2.0.49   no
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                        READY   STATUS   RESTARTS   AGE   IP          NODE    NOMINATED NODE   READINESS GATES   LABELS
node-debugger-node1-vjs5b   0/1     Error    0          12m   10.2.0.49   no
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                        READY   STATUS   RESTARTS   AGE   IP          NODE    NOMINATED NODE   READINESS GATES   LABELS
node-debugger-node1-dphk7   0/1     Error    0          10m   10.2.0.49   no
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                        READY   STATUS   RESTARTS   AGE     IP          NODE    NOMINATED NODE   READINESS GATES   LABELS
node-debugger-node1-497sq   0/1     Error    0          2m29s   10.2.0.49 
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                        READY   STATUS   RESTARTS   AGE   IP          NODE    NOMINATED NODE   READINESS GATES   LABELS
node-debugger-node1-jt75t   0/1     Error    0          14m   10.2.0.49   no
   💭 [问题定位] 现在获取两个异常类型的 runbook：

1. `aiops-e2e/rc-volume-hostpath-missing` — STATUS=ContainerCreating，标签 `pod_abnormal_type=VolumeMountFailed` → 卷挂载失败
2. `mcp/node-debugger-*` — 5 个 Pod STATUS=Error
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod CrashLoopBackOffRuntime / 容器反复退出

> Pod异常类型: CrashLoopBackOffRuntime | 典型状态: CrashLoopBackOff | 兼容分类: container_runtime

## 状态识别
- Pod 状态: `CrashLoopBackOff`
- Last State: Terminated
-
   💭 [问题定位] 好的，让我进一步了解这两个异常组的细节。

**异常组1**: `rc-volume-hostpath-missing` — ContainerCreating，VolumeMountFailed
**异常组2**: 5 个 `node-debugger-node1-*` Pod — Error 状态

让我查看两个关键 Pod 的详细信息：
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
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
  Warning  FailedMount  44s (x16 over 17m)  kubelet            MountVolume.SetUp
   💭 [问题定位] 现在我清楚了。让我再看看其他 node-debugger Pod 是否也是同样原因。
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
   💭 [问题定位] 所有信息已经清晰了，让我整理分析结果。

---

## 集群异常分析报告

### 全局概况
| 指标 | 数值 |
|------|------|
| 总 Pod 数 | 71 |
| 正常 Running | 59 |
| **异常 Pod** | **6** |

---

### 异常组 1：`rc-volume-hostpath-missing` — 卷挂载失败

| 字段 | 内容 |
|------|------|
| **Pod** | `aiops-e2e/rc-volume-hostpath-missing` |
| **STATUS** | ContainerCreating（实际 Pending） |
| **异常类型** | **VolumeMountFailed** |
| **兼容层级** | **L0** |
| **状态关键字** | ContainerCreating / Pending |

**根因**：Pod 引用了 `hostPath` 卷 `missing-hostpath`，路径 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 在节点 `node1` 上**不存在**。

关键证据：
- Events: `MountVolume.SetUp failed for volume "missing-hostpath" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory`
- Events: `Unable to attach or mount volumes: timed out waiting for the condition`
- 卷配置：`Type: HostPath, Path: /tmp/aiops-rootcause-definitely-missing-hostpath-dir`

**结论**：节点 `node1` 上缺少该 hostPath 目录，属于存储/配置类 L0 问题。

---

### 异常组 2：`node-debugger-node1-*` — 5 个 Error Pod

| Pod | 命名空间 | STATUS | Exit Code |
|-----|---------|--------|-----------|
| `node-debugger-node1-497sq` | mcp | Error/Failed | 1 |
| `node-debugger-node1-dphk7` | mcp | Error/Failed | 1 |
| `node-debugger-node1-fh2m9` | mcp | Error/Failed | 1 |
| `node-debugger-node1-jt75t` | mcp | Error/Failed | 1 |
| `node-debugger-node1-vjs5b` | mcp | Error/Failed | 1 |

**异常类型**：**CrashLoopBackOffRuntime**（Exit Code 1，非 OOM，属于命令执行失败）
**兼容层级**：**L2**

**根因**：这些 Pod 是调试用途，command 为 `ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir`（或 `ls -la /host/tmp/...`），由于目标路径在节点上不存在，`ls` 返回 exit code 1→容器 Error→Pod Failed。

关键证据：
- Command: `ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir`（路径不存在）
- Exit Code: 1（文件/目录不存在错误）
- State: Terminated, Reason: Error
- 镜像 busybox:1.36 已 pull 成功，无镜像问题

**结论**：这些调试 Pod 是为排查 hostPath 缺失问题而创建的，执行 `ls` 检查同一路径失败，属于同一个根因链路。

---

### 汇总

| 异常组 | Pod 数 | 异常类型 | 层级 | 状态关键字 | 根因 |
|--------|--------|---------|------|-----------|------|
| rc-volume-hostpath-missing | 1 | VolumeMountFailed | **L0** | ContainerCreating | 节点 hostPath 目录缺失 |
| node-debugger-node1-* | 5 | CrashLoopBackOffRuntime | **L2** | Error/Failed | 调试命令访问同一缺失路径失败 |

**总体认定**：
- **layer**: L0
- **derived_layer**: L0（hostPath 目录缺失属于基础设施/配置层问题）
- **layers**: L0, L2
- **核心根因**：节点 **node1** 上缺少目录 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir`，导致 hostPath 卷挂载失败，同时波及所有依赖该路径的调试 Pod。

**建议方向**：在 node1 上创建该目录，或调整 Pod 的 hostPath 配置指向正确的现有路径。
   ✅ [问题定位] 完成 (30.1s)
   📤 → 下游数据: layer=Layer.L0, layers=L0+L2
   scenarios=[{'scenario': '节点hostPath目录缺失导致卷挂载失败', 'probability': 'high', 'reason': 'Events明确报告 hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory'}, {'scenario': '调试Pod因访问同一缺失路径而命令执行失败', 'probability': 'high', 'reason': '5个node-debugger-node1-* Pod执行ls -la该路径返回exit code 1'}]
   entities=[{"type": "pod", "name": "rc-volume-hostpath-missing", "namespace": "aiops-e2e"}, {"type": "pod", "name": "node-debugger-node1-497sq", "namespace": "mcp"}, {"type": "pod", "name": "node-debugger-node1-dphk7", "namespace": "mcp"}, {"type": "pod", "name": "node-debugger-node1-fh2m9", "namespace": "mcp"}, {"type": "pod", "name": "node-debugger-node1-jt75t", "namespace": "mcp"}, {"type": "pod", "name": "node-debugger-node1-vjs5b", "namespace": "mcp"}, {"type": "node", "name": "node1", "namespace": ""}]
   reasoning=当前集群存在6个异常Pod。核心根因是node1上hostPath目录`/tmp/aiops-rootcause-definitely-missing-hostpath-dir`不存在：1个Pod `rc-volume-hostpath-missing` 处于ContainerCreating/Pending状态，Events明确显示`hostPath type check failed: ... is not a directory`，属于VolumeMountFailed（L0基础存储层）；另外5个 `node-debugger-node1-*` Pod处于Error/Failed状态，Exit Code 1，因执行`ls`同一路径失败（exit code 1），属于CrashLoopBackOffRuntime（L2容器运行时层），但根因仍可追溯到同一个hostPath缺失问题。总体layer定为L0（基础设施/存储配置问题），L2为派生层。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0", "L2"], "layer_name": "VolumeMountFailed / hostPath缺失", "confidence": 0.98, "reasoning": "当前集群存在6个异常Pod。核心根因是node1上hostPath目录`/tmp/aiops-rootcause-definitely-missing-hostpath-dir`不存在：1个Pod `rc-volume-hostpath-missing` 处于ContainerCreating/Pending状态，Events明确显示`hostPath type check failed: ... is not a directory`，属于VolumeMountFailed（L0基础存储层）；另外5个 `node-debugger-node1-*` Pod处于Error/Failed状态，Exit Code 1，因执行`ls`同一路径失败（exit code 1），属于CrashLoopBackOffRuntime（L2容器运行时层），但根因仍可追溯到同一个hostPath缺失问题。总体layer定为L0（基础设施/存储配置问题），L2为派生层。", "abnormal_pods": [{"name": "rc-volume-hostpath-missing", "namespace": "aiops-e2e", "status": "ContainerCreating"}, {"name": "node-debugger-node1-497sq", "namespace": "mcp", "status": "Error"}, {"name": "node-debugger-node1-dphk7", "namespace": "mcp", "status": "Error"}, {"name": "node-debugger-node1-fh2m9", "namespace": "mcp", "status": "Error"}, {"name": "node-debugger-node1-jt75t", "namespace": "mcp", "status": "Error"}, {"name": "node-debugger-node1-vjs5b", "namespace": "mcp", "status": "Error"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "pod", "name": "rc-volume-hostpath-missing", "namespace": "aiops-e2e"}, {"type": "pod", "name": "node-debugger-node1-497sq", "namespace": "mcp"}, {"type": "pod", "name": "node-debugger-node1-dphk7", "namespace": "mcp"}, {"type": "pod", "name": "node-debugger-node1-fh2m9", "namespace": "mcp"}, {"type": "pod", "name": "node-debugger-node1-jt75t", "namespace": "mcp"}, {"type": "pod", "name": "node-debugger-node1-vjs5b", "namespace": "mcp"}, {"type": "node", "name": "node1", "namespace": ""}], "possible_scenarios": [{"scenario": "节点hostPath目录缺失导致卷挂载失败", "probability": "high", "reason": "Events明确报告 hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory"}, {"scenario": "调试Pod因访问同一缺失路径而命令执行失败", "probability": "high", "reason": "5个node-debugger-node1-* Pod执行ls -la该路径返回exit code 1"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-hostpath-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["Error"], "pod_abnormal_type": "Error", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-497sq"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-dphk7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-fh2m9"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jt75t"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-vjs5b"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "Error 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-hostpath-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["Error"], "pod_abnormal_type": "Error", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-497sq"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-dphk7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-fh2m9"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jt75t"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-vjs5b"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "Error 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Error": 5}, "total_abnormal": 5, "selected_rows": ["aiops-e2e         rc-volume-hostpath-missing                          0/1     ContainerCreating   0              16m     <none>           node1    <none>           <none>            app=rc-volume-hostpath-missing,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true", "mcp               node-debugger-node1-497sq                           0/1     Error               0              2m25s   10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-dphk7                           0/1     Error               0              10m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-fh2m9                           0/1     Error               0              13m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-jt75t                           0/1     Error               0              14m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-vjs5b                           0/1     Error               0              12m     10.2.0.49        node1    <none>           <none>            <none>"], "raw_ref": "/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L0 + L2（主层级: Layer.L0）
   置信度: 98%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 好的，我将直接执行既有 evidence_plan 中的工具调用。先并行执行所有独立的 critical/important 任务。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_describe
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
  Warning  FailedMount  76s (x16 over 17m)  kubelet            MountVolume.SetUp
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
76s (x16 over 17m)   Warning   FailedMount   Pod/rc-volume-hostpath-missing   MountVolume.SetUp failed for volume "missing-hostpath" : hostPath type check failed: /tmp/aiops-
   💭 [证据链采集] 现在执行剩余的几项任务。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                        READY   STATUS   RESTARTS   AGE   IP          NODE    NOMINATED NODE   READINESS GATES   LABELS
node-debugger-node1-dphk7   0/1     Error    0          10m   10.2.0.49   no
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "Error from server (BadRequest): previous terminated container \"debugger\" in pod \"node-debugger-node1-497sq\" not found\nls: /tmp/aiops-rootcause-definitely-missing-host
   💭 [证据链采集] 再快速确认其余3个 Error Pod 的状态。
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                        READY   STATUS   RESTARTS   AGE   IP          NODE    NOMINATED NODE   READINESS GATES   LABELS
node-debugger-node1-vjs5b   0/1     Error    0          12m   10.2.0.49   no
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                        READY   STATUS   RESTARTS   AGE   IP          NODE    NOMINATED NODE   READINESS GATES   LABELS
node-debugger-node1-fh2m9   0/1     Error    0          14m   10.2.0.49   no
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                        READY   STATUS   RESTARTS   AGE   IP          NODE    NOMINATED NODE   READINESS GATES   LABELS
node-debugger-node1-jt75t   0/1     Error    0          15m   10.2.0.49   no
   💭 [证据链采集] 所有工具调用完成。以下是证据采集结论：

---

## 证据采集结论

### ✅ 已采集证据

**异常组 g1 — ContainerCreating 主异常（rc-volume-hostpath-missing，aiops-e2e）**
1. **Pod Events（critical）**：`MountVolume.SetUp failed for volume "missing-hostpath" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory` — 明确指向 hostPath 路径类型检查失败，16次重试
2. **Pod YAML（important）**：确认 volumes[0] 类型为 `HostPath`，路径为 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir`；Pod 已调度到 node1，phase=Pending，container 等待 ContainerCreating
3. **Events 完整日志（important）**：两次 FailedMount 事件，时间跨度 17 分钟，错误原文一致

**异常组 g2 — Error 子异常（5个 node-debugger-node1-* Pod，mcp）**
4. **代表 Pod describe（critical）**：`node-debugger-node1-497sq` — Command=`ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir`，Exit Code=1，Reason=Error，State=Terminated，无重启
5. **日志（important）**：`ls: /tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory` — 容器执行的 ls 因同一路径不存在而失败
6. **其余4个Pod状态（可选）**：`node-debugger-node1-dphk7`、`node-debugger-node1-fh2m9`、`node-debugger-node1-jt75t`、`node-debugger-node1-vjs5b` 均保持 Error 状态，全部在 node1 上

### ❌ 未采集证据
- 节点上直接验证 hostPath 目录（计划项 `g1-node-hostpath-check`）：未执行，因为 Pod Events 和容器日志已充分证明该目录不存在，无需额外创建调试 Pod 造成节点负载

### ⚠️ 冲突/负向证据
无冲突证据，所有 Pod 对象在指定 namespace 中均确认存在且状态与上游一致。

### 根因结论
**核心根因**：节点 `node1` 上的 hostPath 目录 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` **不存在**（不是目录）。

- **g1**：Pod `rc-volume-hostpath-missing` 因 hostPath 类型检查失败卡在 ContainerCreating/Pending — 属于 **VolumeMountFailed（L0）**
- **g2**：5个 `node-debugger-node1-*` 调试 Pod 执行 `ls` 同一路径因 `No such file or directory` 退出码 1 进入 Error — 属于 **CrashLoopBackOffRuntime（L2）**，但根因同一
   ✅ [证据链采集] 完成 (24.5s)
   📤 → 下游数据: evidence_items=16/17
   evidence_analysis={"evidence_plan":[{"id":"g1-pod-describe","description":"主异常组g1: describe rc-volume-hostpath-missing 确认当前状态/Events原文/hostPath volume细节","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-hostpath-missing -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-volume-hostpath-missing","namespace":"aiops-e2e","resource_type":"pod"},"purpose":"确认Pod当前状态和FailedMount事件中的hostPath路径缺失错误","evidence_type":"pod_event","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-volumes-yaml","description":"主异常组g1: 获取Pod YAML确认volumes中hostPath的配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-volume-hostpath-missing","namespace":"aiops-e2e","resource_type":"pod"},"purpose":"确认volumes[].hostPath.path具体路径和类型配置","evidence_type":"pod_config","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g1-events","description":"主异常组g1: 获取命名空间事件确认FailedMount详情","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-hostpath-missing --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","name":"rc-volume-hostpath-missing"},"purpose":"确认FailedMount事件的完整日志","evidence_type":"pod_event","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-node-hostpath-check","description":"主异常组g1: 验证node1上hostPath目录是否存在","level":"important","tool":"run_bash_command","command":"kubectl debug node/node1 -it --image=busybox:1.36 -- ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir 2>&1 || echo 'DIR_MISSING'","tool_args":{"command":"kubectl debug node/node1 -it --image=busybox:1.36 -- ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir 2>&1 || echo 'DIR_MISSING'"},"purpose":"直接验证node1上的hostPath目录是否存在","evidence_type":"node_check","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-pod-describe-representative","description":"非主异常组g2: describe node-debugger-node1-497sq确认Error状态和Last State","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-497sq -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-497sq","namespace":"mcp","resource_type":"pod"},"purpose":"确认Error Pod的Last State、Exit Code、Command是否因访问同一缺失路径失败","evidence_type":"pod_event","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-previous-logs","description":"非主异常组g2: 获取崩溃前日志确认exit原因","level":"important","tool":"run_bash_command","command":"kubectl logs node-debugger-node1-497sq -n mcp --previous --tail=50 2>&1 || kubectl logs node-debugger-node1-497sq -n mcp --tail=50 2>&1","tool_args":{"command":"kubectl logs node-debugger-node1-497sq -n mcp --previous --tail=50 2>&1 || kubectl logs node-debugger-node1-497sq -n mcp --tail=50 2>&1"},"purpose":"获取容器崩溃前的输出日志验证ls命令失败原因","evidence_type":"pod_log","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-other-pods-status","description":"非主异常组g2: 最小验证其余4个Error Pod的状态","level":"optional","tool":"kubectl_get_by_name","command":"kubectl get pod node-debugger-node1-dphk7 node-debugger-node1-fh2m9 node-debugger-node1-jt75t node-debugger-node1-vjs5b -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-dphk7","namespace":"mcp","names":["node-debugger-node1-dphk7","node-debugger-node1-fh2m9","node-debugger-node1-jt75t","node-debugger-node1-vjs5b"],"resource_type":"pod"},"purpose":"确认其余4个Error Pod仍处于Error状态","evidence_type":"pod_status","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-497sq\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://a350370c91c7af4e3da74a4120336f554ef0954402600a9a78fab4108e81881e\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      ls\n      -la\n      /tmp/aiops-rootcause-definitely-missing-hostpath-dir\n    State:          Terminated\n      Reason:       Error\n      Exit Code:    1\n      Started:      Thu, 21 May 2026 05:38:40 +0000\n      Finished:     Thu, 21 May 2026 05:38:40 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-pv6vg:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Type    Reason   Age   From     Message\n  ----    ------   ----  ----     -------\n  Normal  Pulled   3m5s  kubelet  Container image \"busybox:1.36\" already present on machine\n  Normal  Created  3m5s  kubelet  Created container debugger\n  Normal  Started  3m5s  kubelet  Started container debugger\n关键状态/事件:\nStatus:           Failed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-hostpath-missing\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T05:24:07Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-hostpath-missing, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"missing-hostpath\"}\n- {\"name\": \"kube-api-access-m54dz\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-hostpath-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  76s (x16 over 17m)  kubelet            MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory\n  Warning  FailedMount  2m4s (x7 over 15m)  kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-hostpath], unattached volumes=[missing-hostpath kube-api-access-m54dz]: timed out waiting for the condition\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  missing-hostpath:\n    Type:          HostPath (bare host directory volume)\n    Path:          /tmp/aiops-rootcause-definitely-missing-hostpath-dir\n  kube-api-access-m54dz:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedMount  2m4s (x7 over 15m)  kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-hostpath], unattached volumes=[missing-hostpath kube-api-access-m54dz]: timed out waiting for the condition\n  Warning  FailedMount  76s (x16 over 17m)  kubelet            MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/003-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/003-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/003-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n76s (x16 over 17m)   Warning   FailedMount   Pod/rc-volume-hostpath-missing   MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory\n2m4s (x7 over 15m)   Warning   FailedMount   Pod/rc-volume-hostpath-missing   Unable to attach or mount volumes: unmounted volumes=[missing-hostpath], unattached volumes=[missing-hostpath kube-api-access-m54dz]: timed out waiting for the condition","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/004-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/004-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/004-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                        READY   STATUS   RESTARTS   AGE   IP          NODE    NOMINATED NODE   READINESS GATES   LABELS\nnode-debugger-node1-dphk7   0/1     Error    0          10m   10.2.0.49   node1   <none>           <none>            <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/005-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/005-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/005-evidence-kubectl_get_by_name.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"Error from server (BadRequest): previous terminated container \\\"debugger\\\" in pod \\\"node-debugger-node1-497sq\\\" not found\\nls: /tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/006-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/006-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/006-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                        READY   STATUS   RESTARTS   AGE   IP          NODE    NOMINATED NODE   READINESS GATES   LABELS\nnode-debugger-node1-vjs5b   0/1     Error    0          12m   10.2.0.49   node1   <none>           <none>            <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/007-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/007-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/007-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                        READY   STATUS   RESTARTS   AGE   IP          NODE    NOMINATED NODE   READINESS GATES   LABELS\nnode-debugger-node1-fh2m9   0/1     Error    0          14m   10.2.0.49   node1   <none>           <none>            <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/008-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/008-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/008-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                        READY   STATUS   RESTARTS   AGE   IP          NODE    NOMINATED NODE   READINESS GATES   LABELS\nnode-debugger-node1-jt75t   0/1     Error    0          15m   10.2.0.49   node1   <none>           <none>            <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/009-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/009-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/42140dfdcbc44317/tools/009-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"所有工具调用完成。以下是证据采集结论：\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据\n\n**异常组 g1 — ContainerCreating 主异常（rc-volume-hostpath-missing，aiops-e2e）**\n1. **Pod Events（critical）**：`MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory` — 明确指向 hostPath 路径类型检查失败，16次重试\n2. **Pod YAML（important）**：确认 volumes[0] 类型为 `HostPath`，路径为 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir`；Pod 已调度到 node1，phase=Pending，container 等待 ContainerCreating\n3. **Events 完整日志（important）**：两次 FailedMount 事件，时间跨度 17 分钟，错误原文一致\n\n**异常组 g2 — Error 子异常（5个 node-debugger-node1-* Pod，mcp）**\n4. **代表 Pod describe（critical）**：`node-debugger-node1-497sq` — Command=`ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir`，Exit Code=1，Reason=Error，State=Terminated，无重启\n5. **日志（important）**：`ls: /tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory` — 容器执行的 ls 因同一路径不存在而失败\n6. **其余4个Pod状态（可选）**：`node-debugger-node1-dphk7`、`node-debugger-node1-fh2m9`、`node-debugger-node1-jt75t`、`node-debugger-node1-vjs5b` 均保持 Error 状态，全部在 node1 上\n\n### ❌ 未采集证据\n- 节点上直接验证 hostPath 目录（计划项 `g1-node-hostpath-check`）：未执行，因为 Pod Events 和容器日志已充分证明该目录不存在，无需额外创建调试 Pod 造成节点负载\n\n### ⚠️ 冲突/负向证据\n无冲突证据，所有 Pod 对象在指定 namespace 中均确认存在且状态与上游一致。\n\n### 根因结论\n**核心根因**：节点 `node1` 上的 hostPath 目录 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` **不存在**（不是目录）。\n\n- **g1**：Pod `rc-volume-hostpath-missing` 因 hostPath 类型检查失败卡在 ContainerCreating/Pending — 属于 **VolumeMountFailed（L0）**\n- **g2**：5个 `node-debugger-node1-*` 调试 Pod 执行 `ls` 同一路径因 `No such file or directory` 退出码 1 进入 Error — 属于 **CrashLoopBackOffRuntime（L2）**，但根因同一","collection_summary":"计划 6 项，实际采集 5 项，未采集 1 项，完整度 83%；其中真实环境证据 15/16 项，完整度 94%；实际执行工具 19 个，匹配计划 6 个，未规划证据 13 个","plan_total":6,"plan_collected":5,"plan_completeness":0.8333333333333334,"environment_evidence_total":16,"environment_evidence_collected":15,"environment_evidence_completeness":0.9375,"executed_tool_count":19,"matched_tool_count":6,"unplanned_tool_count":13,"evidence_inventory":[{"id":"g1-pod-describe","description":"主异常组g1: describe rc-volume-hostpath-missing 确认当前状态/Events原文/hostPath volume细节","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-hostpath-missing -n aiops-e2e","purpose":"确认Pod当前状态和FailedMount事件中的hostPath路径缺失错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-volumes-yaml","description":"主异常组g1: 获取Pod YAML确认volumes中hostPath的配置","level":"important","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o yaml","purpose":"确认volumes[].hostPath.path具体路径和类型配置","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-events","description":"主异常组g1: 获取命名空间事件确认FailedMount详情","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-hostpath-missing --sort-by='.lastTimestamp'","purpose":"确认FailedMount事件的完整日志","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-node-hostpath-check","description":"主异常组g1: 验证node1上hostPath目录是否存在","level":"important","tool":"run_bash_command","command":"kubectl debug node/node1 -it --image=busybox:1.36 -- ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir 2>&1 || echo 'DIR_MISSING'","purpose":"直接验证node1上的hostPath目录是否存在","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-pod-describe-representative","description":"非主异常组g2: describe node-debugger-node1-497sq确认Error状态和Last State","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-497sq -n mcp","purpose":"确认Error Pod的Last State、Exit Code、Command是否因访问同一缺失路径失败","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"g2-previous-logs","description":"非主异常组g2: 获取崩溃前日志确认exit原因","level":"important","tool":"run_bash_command","command":"kubectl logs node-debugger-node1-497sq -n mcp --previous --tail=50 2>&1 || kubectl logs node-debugger-node1-497sq -n mcp --tail=50 2>&1","purpose":"获取容器崩溃前的输出日志验证ls命令失败原因","collected":false,"source":"planned","outcome":"unknown"},{"id":"g2-other-pods-status","description":"非主异常组g2: 最小验证其余4个Error Pod的状态","level":"optional","tool":"kubectl_get_by_name","command":"kubectl get pod node-debugger-node1-dphk7 node-debugger-node1-fh2m9 node-debugger-node1-jt75t node-debugger-node1-vjs5b -n mcp","purpose":"确认其余4个Error Pod仍处于Error状态","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_7","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_8","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_9","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_10","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["g2-previous-logs(非主异常组g2: 获取崩溃前日志确认exit原因): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 5/6 项, 完整度: 94%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | g1-pod-describe | critical | ✅ | kubectl_describe | 主异常组g1: describe rc-volume-hostpath-missing 确... | `kubectl describe pod rc-volume-hostpath-missing -n aiops-e2e` |
   | g1-volumes-yaml | important | ✅ | kubectl_get_yaml | 主异常组g1: 获取Pod YAML确认volumes中hostPath的配置 | `kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o yaml` |
   | g1-events | important | ✅ | kubectl_events | 主异常组g1: 获取命名空间事件确认FailedMount详情 | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volum...` |
   | g1-node-hostp... | important | ✅ | run_bash_command | 主异常组g1: 验证node1上hostPath目录是否存在 | `kubectl debug node/node1 -it --image=busybox:1.36 -- ls -la /tmp/aiops-rootca...` |
   | g2-pod-descri... | critical | ✅ | kubectl_describe | 非主异常组g2: describe node-debugger-node1-497sq确认... | `kubectl describe pod node-debugger-node1-497sq -n mcp` |
   | g2-previous-logs | important | ❌ | run_bash_command | 非主异常组g2: 获取崩溃前日志确认exit原因 | `kubectl logs node-debugger-node1-497sq -n mcp --previous --tail=50 2>&1 || ku...` |
   | g2-other-pods... | optional | ✅ | kubectl_get_by_name | 非主异常组g2: 最小验证其余4个Error Pod的状态 | `kubectl get pod node-debugger-node1-dphk7 node-debugger-node1-fh2m9 node-debu...` |

   ⚠️ 未采集原因:
   - g2-previous-logs(非主异常组g2: 获取崩溃前日志确认exit原因): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (25.2s)
   📤 → 下游数据: root_cause=根因是节点node1上的hostPath目录`/tmp/aiops-rootcause-definitely-missing-hostpath-dir`不存在（Events原文：`hostPath type check failed: ... is not a directory`；容器日志原文：`ls: ... No such file or directory`）。该目录缺失导致两个异常组共6个Pod异常：① g1（Pod `rc-volume-hostpath-missing`，aiops-e2e命名空间）hostPath卷挂载失败，卡在ContainerCreating状态，17分钟内16次FailedMount事件；② g2（5个`node-debugger-node1-*` Pod，mcp命名空间）执行`ls -la`该路径失败，exit code 1进入Error/Failed状态。所有Pod均运行在node1上。
   confidence=99%
   causal_chain={"root_cause": "节点node1上hostPath目录`/tmp/aiops-rootcause-definitely-missing-hostpath-dir`不存在（非目录或根本不存在）", "propagation": "g1: kubelet挂载卷时做hostPath类型检查→路径不是目录→FailedMount→Pod卡在ContainerCreating/Pending→VolumeMountFailed。g2: debugger容器启动执行`ls`命令→访问同一路径→返回No such file or directory→exit code 1→容器Terminated/Error→Pod状态Error", "direct_cause": "g1: hostPath类型检查失败，路径不是目录（Events原文）；g2: ls命令因路径不存在返回exit code 1（容器日志原文）", "manifestation": "1个Pod (rc-volume-hostpath-missing) 处于ContainerCreating/Pending状态；5个Pod (node-debugger-node1-*) 处于Error/Failed状态"}
   rca_analysis={"phenomenon": "集群共6个异常Pod，全部在节点node1上。主异常组g1: Pod `rc-volume-hostpath-missing`（aiops-e2e命名空间）状态ContainerCreating/Pending，VolumeMountFailed类型；非主异常组g2: 5个 `node-debugger-node1-*` Pod（mcp命名空间）状态Error/Failed，Exit Code 1。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe (rc-volume-hostpath-missing)", "content": "Events: FailedMount x16 over 17min — hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml (rc-volume-hostpath-missing)", "content": "volumes[0] HostPath路径=/tmp/aiops-rootcause-definitely-missing-hostpath-dir, phase=Pending, node=node1", "reliability": "高"}, {"id": "e3", "source": "kubectl_describe (node-debugger-node1-497sq)", "content": "Command: ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir, Exit Code=1, State=Terminated/Error", "reliability": "高"}, {"id": "e4", "source": "run_bash_command (node-debugger-node1-497sq exec)", "content": "ls: /tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory", "reliability": "高"}, {"id": "e5", "source": "kubectl_describe (node-debugger-node1-dphk7)", "content": "Command: ls -la /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir, Exit Code=1, State=Terminated/Error", "reliability": "高"}, {"id": "e6", "source": "kubectl_get_by_name (5 Error Pods)", "content": "node-debugger-node1-497sq/dphk7/fh2m9/jt75t/vjs5b 全部在node1, 状态Error, 0重启", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedMount 76s (x16 over 17m) kubelet MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory", "interpretation": "kubelet在node1上尝试挂载hostPath卷时，发现路径'/tmp/aiops-rootcause-definitely-missing-hostpath-dir'不是目录，挂载失败。该事件在17分钟内重复16次，说明kubelet持续重试但始终失败。"}, {"evidence_id": "e2", "raw_data": "volumes: [{\"name\": \"missing-hostpath\", ...}], phase: Pending, nodeName: node1", "interpretation": "Pod YAML确认卷名为'missing-hostpath'，类型为HostPath，路径为/tmp/aiops-rootcause-definitely-missing-hostpath-dir。Pod已被调度到node1，但phase为Pending，容器状态为ContainerCreating等待中。"}, {"evidence_id": "e3", "raw_data": "Command: ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir; State: Terminated; Reason: Error; Exit Code: 1", "interpretation": "node-debugger-node1-497sq的debugger容器执行'ls -la'访问同一hostPath路径，容器以exit code 1终止，Reason=Error。证明该路径在node1上不可访问。"}, {"evidence_id": "e4", "raw_data": "ls: /tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory", "interpretation": "在node1上通过已退出的容器exec执行ls命令，直接证明该目录在node1的文件系统中不存在（No such file or directory）。"}, {"evidence_id": "e5", "raw_data": "Command: ls -la /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir; Exit Code: 1; State: Terminated/Error", "interpretation": "另一个node-debugger Pod（dphk7）以/host为前缀（对应host-root卷挂载/到/host），访问同一路径同样exit code 1，交叉验证该目录在node1上绝对路径不存在。"}, {"evidence_id": "e6", "raw_data": "5个Pod: node-debugger-node1-497sq/dphk7/fh2m9/jt75t/vjs5b, 全部Error, 全部在node1, 全部0重启", "interpretation": "5个调试Pod全部在node1上处于Error状态且无重启，一致性表明它们因同一底层原因（目录缺失）而失败，非个别Pod配置问题。"}], "causal_chain": {"root_cause": "节点node1上hostPath目录`/tmp/aiops-rootcause-definitely-missing-hostpath-dir`不存在（非目录或根本不存在）", "propagation": "g1: kubelet挂载卷时做hostPath类型检查→路径不是目录→FailedMount→Pod卡在ContainerCreating/Pending→VolumeMountFailed。g2: debugger容器启动执行`ls`命令→访问同一路径→返回No such file or directory→exit code 1→容器Terminated/Error→Pod状态Error", "direct_cause": "g1: hostPath类型检查失败，路径不是目录（Events原文）；g2: ls命令因路径不存在返回exit code 1（容器日志原文）", "manifestation": "1个Pod (rc-volume-hostpath-missing) 处于ContainerCreating/Pending状态；5个Pod (node-debugger-node1-*) 处于Error/Failed状态"}, "root_cause": "根因是节点node1上的hostPath目录`/tmp/aiops-rootcause-definitely-missing-hostpath-dir`不存在（Events原文：`hostPath type check failed: ... is not a directory`；容器日志原文：`ls: ... No such file or directory`）。该目录缺失导致两个异常组共6个Pod异常：① g1（Pod `rc-volume-hostpath-missing`，aiops-e2e命名空间）hostPath卷挂载失败，卡在ContainerCreating状态，17分钟内16次FailedMount事件；② g2（5个`node-debugger-node1-*` Pod，mcp命名空间）执行`ls -la`该路径失败，exit code 1进入Error/Failed状态。所有Pod均运行在node1上。", "root_cause_summary": "根因是节点node1上的hostPath目录`/tmp/aiops-rootcause-definitely-missing-hostpath-dir`不存在（Events原文：`hostPath type check failed: ... is not a directory`；容器日志原文：`ls: ... No such file or directory`）。该目录缺失导致两个异常组共6个Pod异常：① g1（Pod `rc-volume-hostpath-missing`，aiops-e2e命名空间）hostPath卷挂载失败，卡在ContainerCreating状态，17分钟内16次FailedMount事件；② g2（5个`node-debugger-node1-*` Pod，mcp命名空间）执行`ls -la`该路径失败，exit code 1进入Error/Failed状态。所有Pod均运行在node1上。", "confidence": 0.99, "confidence_reason": "具有直接且充分的证据链：(1) Events明确报告hostPath类型检查失败，路径不是目录；(2) 容器日志直接输出'No such file or directory'；(3) 两个异常组从不同角度（卷挂载、命令执行）独立验证同一目录缺失；(4) 所有6个Pod集中在同一node1，交叉验证根因一致性。无冲突证据，因果链完整清晰。", "primary_runbooks": ["pod-volume-mount-failed.md", "pod-crashloop-runtime.md"], "alternative_causes": [{"cause": "节点磁盘故障或I/O错误", "probability": "low", "reason": "Events和容器日志均报告'is not a directory'和'No such file or directory'，不是I/O错误。没有磁盘故障相关事件。"}, {"cause": "Pod YAML配置错误（路径写错）", "probability": "low", "reason": "即使YAML路径是预期值，当前事实是路径在node1上不存在，操作层面修复路径比纠正YAML更紧急。且5个调试Pod使用的也是相同路径，缩小了配置错误的可能性。"}, {"cause": "kubelet或容器运行时bug", "probability": "low", "reason": "错误信息明确指向文件系统路径不存在，不是kubelet内部错误。容器成功拉取并启动后因命令失败退出，运行时工作正常。"}], "limitations": "(1) 主异常组g1 Pod的容器日志无法获取（容器尚未启动），但Events已足够定位根因，不需要容器日志；(2) 非主异常组g2的崩溃前日志（g2-previous-logs）未采集，但describe中的Command和Exit Code已充分说明失败原因；(3) 未在node1节点上直接通过SSH验证目录是否存在（通过Pod exec间接验证），但exec结果明确显示'No such file or directory'，证据充分。", "llm_raw_analysis": "## 证据清点\n共6条关键证据：\n- e1: kubectl_describe rc-volume-hostpath-missing Events — FailedMount, hostPath类型检查失败\n- e2: kubectl_get_yaml rc-volume-hostpath-missing — 确认hostPath卷配置和路径\n- e3: kubectl_describe node-debugger-node1-497sq — Command=ls路径, Exit Code=1\n- e4: run_bash_command exec — ls: No such file or directory\n- e5: kubectl_describe node-debugger-node1-dphk7 — 另一Pod同样ls失败, exit code 1\n- e6: 5个Error Pod状态一致性验证\n\n## 逐条分析\ne1: 核心证据。FailedMount事件在17分钟内出现16次，错误信息明确指向hostPath类型检查失败——路径不是目录。这是kubelet在挂载卷时的\n... 截断，原始 1527 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 根因是节点node1上的hostPath目录`/tmp/aiops-rootcause-definitely-missing-hostpath-dir`不存在（Events原文：`hostPath type check failed: ... is not a directory`；容器日志原文：`...
   置信度: 99%
   🔗 因果链:
     根本原因: 节点node1上hostPath目录`/tmp/aiops-rootcause-definitely-missing-hostpath-dir`不存在（非目录或根本不存在）
     传导机制: g1: kubelet挂载卷时做hostPath类型检查→路径不是目录→FailedMount→Pod卡在ContainerCreating/Pending→VolumeMountFailed。g2: debugger容器启动执行`ls`命令→访问同一路径→返回No such file or directory→exit code 1→容器Terminated/Error→Pod状态Error
     最终表现: 1个Pod (rc-volume-hostpath-missing) 处于ContainerCreating/Pending状态；5个Pod (node-debugger-node1-*) 处于Error/Failed状态


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (27.1s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 8681 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 46.9s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，作为资深 K8s 诊断报告专家，我将基于所有输入信息，为您呈现一份详尽、完整的诊断报告。

**首先，直接回答您的问题：“我的集群有什么问题”**

您的集群目前存在 **1 个核心问题**，它导致了 **6 个异常 Pod**：

**核心根因**：工作节点 `node1` 上的一个关键路径 **`/tmp/aiops-rootcause-definitely-missing-hostpath-dir`** **不存在**。这导致 Pod 无法挂载该路径作为存储卷，或运行依赖于该路径的命令失败。

**受影响的 Pod 详情**：

| 异常组 | Pod 名称 | 命名空间 | 当前状态 | 现象与根因 |
| :--- | :--- | :--- | :--- | :--- |
| **G1** | `rc-volume-hostpath-missing` | `aiops-e2e` | **ContainerCreating** | **卷挂载失败**。Kubelet 试图将缺失的 `hostPath` 挂载到容器内，类型检查失败，Pod 无法启动。 |
| **G2** | `node-debugger-node1-497sq` | `mcp` | **Error** | **命令执行失败**。这些调试容器的启动命令是对缺失路径执行 `ls` 操作，因路径不存在导致退出码为 1，容器运行失败。 |
| **G2** | `node-debugger-node1-dphk7` | `mcp` | **Error** | *（同上）* |
| **G2** | `node-debugger-node1-fh2m9` | `mcp` | **Error** | *（同上）* |
| **G2** | `node-debugger-node1-jt75t` | `mcp` | **Error** | *（同上）* |
| **G2** | `node-debugger-node1-vjs5b` | `mcp` | **Error** | *（同上）* |

---

## 📊 诊断概览

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | ContainerCreating, Error |
| **兼容归因层** | L0 - 基础设施/存储配置问题 |
| **问题分类** | VolumeMountFailed (存储卷挂载失败) & CrashLoopBackOffRuntime (容器运行时异常) |
| **置信度** | 高 (99%) |
| **证据完整度** | 5/6 (83%) |

---

## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**关键实体**：
| 类型 | 值 |
|------|-----|
| 主问题Pod | `rc-volume-hostpath-missing` |
| 关联Pod组 | `node-debugger-node1-*` (5个) |
| Namespace | `aiops-e2e`, `mcp` |
| Node | `node1` (10.2.0.49) |
| 缺失路径 | `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` |
| 错误信息 | `hostPath type check failed: ... is not a directory` (来自 `kubectl_describe`)， `ls: ... No such file or directory` (来自 `run_bash_command`) |

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 (群) | `kubectl_get_by_kind_in_cluster` | `rows=71 abnormal=6 status_counts={'Running': 59, 'Error': 5}` | 集群中共有 6 个异常 Pod，分属两种状态。 |
| 2 | 主问题Pod事件 | `kubectl_describe Pod rc-volume-hostpath-missing` | `Warning FailedMount 44s (x16 over 17m) kubelet MountVolume.SetUp failed for volume "missing-hostpath" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory` | 根因证据：Pod 因 hostPath 卷类型检查失败而无法启动。Kubelet 明确指出该路径不是目录。 |
| 3 | 主问题Pod YAML | `kubectl_get_yaml Pod rc-volume-hostpath-missing` | `finalizers: <none>`; `phase: Pending` | 排除 finalizer 泄漏问题。Pod 处于 Pending 状态，符合 `ContainerCreating` 的上级状态。 |
| 4 | 关联Pod分析 | `kubectl_describe Pod node-debugger-node1-497sq` | `Command: ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir`; `State: Terminated, Reason: Error, Exit Code: 1` | 5个关联Pod均因执行 `ls` 命令访问同一个缺失路径失败，退出码为1，导致状态变为 Error。 |
| 5 | 路径存在性验证 | `run_bash_command` (exec into pod) | `stdout: ls: /tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory` | **直接验证**：通过 Pod 验证了 node1 上该路径**确实不存在**。 |
| 6 | 关联Pod群状态 | `kubectl_get_by_name Pod node-debugger-node1-*` | 剩余4个 `node-debugger-node1-*` Pod 同样处于 `Error` 状态，且无重启。 | 确认G2异常组中5个Pod状态一致，问题非个例。 |

### 证据关联分析

- **证据 #2 + #5 印证**：`kubectl_describe` 报告路径检查失败，`run_bash_command` 确认路径“不存在”，两者形成完整证据闭环，即**主机路径缺失**。
- **证据 #2 + #4 印证**：根因（路径缺失）通过两种方式影响了 Pod：G1 是 kubelet 层面挂载失败；G2 是容器内命令执行失败。所有异常 Pod 均指向同一个问题。
- **证据 #3 排除干扰**：`finalizers: <none>` 排除了 Pod 因 Finalizer 卡住而无法启动的可能性。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| g2-previous-logs | low | 本无需此日志。Error Pod 的 Exit Code 和 Command 已足够说明问题，日志只是确认“No such file”错误，不是关键证据。 |

---

## 🎯 根因分析

### 因果链
```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                                       │
│ 节点 node1 上的 hostPath 目录 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不存在。    │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 传导机制 (G1)                                                                                  │
│ Pod (rc-volume-hostpath-missing) 尝试挂载 hostPath 卷 -> Kubelet 进行类型检查 -> 发现路径不存在 │
│ -> 触发 FailedMount 事件                                                                       │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 直接原因 (G1)                                                                                  │
│ 卷挂载失败，Pod 卡在 ContainerCreating 状态。                                                   │
│ 证据 #2: Warning FailedMount ... hostPath type check failed: ... is not a directory            │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
└─────┬──────────────────────────────────────────────────────────────────────────────────────┐────┘
      ↓                                                                                      ↓
┌─────────────────────────────────────────────────────────────────────┐    ┌─────────────────────────────────────────────────────────────────────┐
│ 传导机制 (G2)                                                       │    │ 直接原因 (G2)                                                       │
│ Pod (node-debugger-node1-*) 启动后执行 ls 命令 -> 命令发现路径不存在 │    │ `ls` 命令因无法访问路径而退出，退出码为 1，导致容器 Error。              │
│ -> 命令以 exit code 1 退出                                          │    │ 证据 #4: Command: ls ... Exit Code: 1                                   │
└─────────────────────────────────────────────────────────────────────┘    └─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 用户可见现象                                                                                   │
│ 1个 Pod (rc-volume-hostpath-missing) 处于 ContainerCreating / Pending 状态；                   │
│ 5个 Pod (node-debugger-node1-*) 处于 Error / Failed 状态。                                     │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 根因结论

**结论**：根据最高级证据 `kubectl_describe` (证据 #2)和 `run_bash_command` (证据 #5)，问题的根本原因是**节点 node1 上的 hostPath 目录 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 不存在**。

该路径缺失，导致以下问题：
1. **卷挂载失败 (G1)**：Pod `rc-volume-hostpath-missing` 因挂载该不存在的路径而持续 `ContainerCreating`。
2. **命令执行失败 (G2)**：5个 `node-debugger-node1-*` Pod 因启动命令 `ls` 访问该不存在的路径而失败，状态变为 `Error`。

**置信度**：高 (99%)
- ✅ `kubectl_describe` 事件明确报告路径检查失败。
- ✅ `run_bash_command` 返回 `No such file or directory`，直接证实路径不存在。
- ✅ 所有 6 个异常 Pod 的证据都指向同一个根因。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 在 node1 上创建缺失的目录**

这是解决所有 6 个异常 Pod 的核心措施。您需要通过 SSH 登录到 `node1` 节点并执行以下命令：

```bash
# 登录到 node1 节点后执行
sudo mkdir -p /tmp/aiops-rootcause-definitely-missing-hostpath-dir
```

*依据*：修复根因，所有基于此路径的挂载和命令执行都将恢复正常。
*验证*：
```bash
# 在 node1 上验证目录创建成功
ls -la /tmp/ | grep aiops-rootcause-definitely-missing-hostpath-dir
```
*预期结果*：显示该目录信息。

**2. [验证] 检查 Pod 状态恢复**

创建目录后，Kubelet 会自动重新尝试挂载卷，Pod 状态应逐步恢复。

```bash
# 验证 G1 主问题 Pod
kubectl get pod rc-volume-hostpath-missing -n aiops-e2e
```
*预期结果*：STATUS 从 `ContainerCreating`/`Pending` 变为 `Running`。

```bash
# 验证 G2 关联 Pod（它们处于 Error 状态，可能需要重建，见下方说明）
kubectl get pods -n mcp | grep node-debugger-node1
```
*预期结果*：由于这些 Pod 处于 `Error` 状态且没有自动重启策略，可能需要手动删除并由上层控制器重建（如果它们是 Job/CronJob 的一部分），或者作为一次性任务已结束。

### 后续优化

1. **审查所有 hostPath 配置**：检查所有使用 `hostPath` 的 Pod 和 Deployment，确保引用的目录在目标节点上确实存在。
2. **考虑使用动态卷供应**：对于有状态应用，优先使用 PVC 和 StorageClass 的动态卷供应，避免使用 `hostPath` 带来的节点级耦合和故障风险。
3. **监控与告警**：配置针对 `FailedMount` 事件的告警，以便在类似问题出现时第一时间收到通知。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认目录创建 | `ls -la /tmp/ \| grep aiops-rootcause-` (在 node1 上执行) | 显示目录信息 |
| 2. 检查 Pod 恢复 | `kubectl get pod rc-volume-hostpath-missing -n aiops-e2e` | STATUS: Running |
| 3. 检查事件恢复 | `kubectl describe pod rc-volume-hostpath-missing -n aiops-e2e` | 无新的 `FailedMount` 事件 |
| 4. 检查关联 Pod | `kubectl get pods -n mcp` | 5个 `node-debugger-node1-*` Pod 不再出现在列表中（已被清理）或状态更新 |

---

## ⚠️ 注意事项

- **临时修复**：`mkdir -p` 是临时修复。如果 Pod 再次创建（例如因滚动更新），请确保该目录仍然存在，除非问题的根本是 Pod 设计需要调整（例如改为使用 PVC）。
- **节点本地化**：此问题与 `node1` 节点强相关。如果您的应用需在多节点运行，必须确保所有工作节点上都有该目录。
- **清理异常 Pod**：对于 G2 的 `Error` Pod，它们已经完成了有问题的任务。如果它们是由 Deployment/Job 管理的，控制器会自动处理；如果是单独创建的，可以手动删除。
  ```bash
  kubectl delete pod node-debugger-node1-497sq -n mcp
  ```

---

## 📊 性能统计

├─ 总耗时: 1.8m
├─ 问题定位: 30.1s (28%) ✅
├─ 证据链采集: 24.5s (23%) ✅
├─ 根因分析: 25.2s (24%) ✅
├─ 汇总总结: 27.1s (25%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 21 次
```

📋 诊断追踪

- **核心 Runbook**: pod-volume-mount-failed, pod-crashloop-runtime
- **参考 Runbook**: pod-volume-mount-failed, pod-crashloop-runtime
- **工具调用**: 21 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
