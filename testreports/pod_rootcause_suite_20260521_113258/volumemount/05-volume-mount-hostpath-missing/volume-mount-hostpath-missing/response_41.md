======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: 7f2c8144237a4c4b]

📍 [问题定位] 执行中...
   💭 [问题定位] 让我先扫描全局 Pod 状态，了解集群的整体健康状况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=74 abnormal=9 status_counts={'Running': 59, 'Error': 8}
NAMESPACE         NAME                                                READY   STATUS              REST
   💭 [问题定位] 发现有 9 个异常 Pod。让我进一步查看一些关键信息。
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 TodoWrite 输出摘要: raw_chars=369 lines=8
Investigation plan updated with 4 tasks.
# CURRENT INVESTIGATION TASKS
**Task Status**: 0 completed, 1 in progress, 3 pending
[ ] [2] 对 aiops-e2e/rc-volume-hostpa
   💭 [问题定位] 现在让我获取更多信息来区分这些异常类型。先查看 `rc-volume-hostpath-missing` 和其中一个 `node-debugger` Pod 的状态。
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
  Warning  FailedMount  58s (x23 over 31m)    kubelet            MountVolume.Set
   💭 [问题定位] 现在我已经掌握了关键信息。让我检查一下 `node-debugger` 的详细状态。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=13 abnormal=8 status_counts={'Running': 1, 'Error': 8}
NAME                                  READY   STATUS      RESTARTS   AGE     IP               NODE   
   💭 [问题定位] 好的，现在信息已经非常清楚了。让我获取对应的 runbook 参考。
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
   💭 [问题定位] 现在信息已经全部收集完毕，让我更新任务状态并输出最终定位结果。
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 TodoWrite 输出摘要: raw_chars=369 lines=8
Investigation plan updated with 4 tasks.
# CURRENT INVESTIGATION TASKS
**Task Status**: 3 completed, 1 in progress, 0 pending
[~] [4] 输出最终分层定位结果
[✓] [1] 分析异常 Pod 
   💭 [问题定位] 以下是完整的集群异常定位分析结果。

---

## 集群异常定位分析结果

### 一、整体概况

集群共有 **74 个 Pod**，其中 **59 个 Running（正常）**，**9 个异常 Pod**，分布在 2 个命名空间：

| 命名空间 | 异常 Pod 数 | 异常状态 |
|---------|:----------:|---------|
| `aiops-e2e` | 1 | ContainerCreating |
| `mcp` | 8 | Error（均已完成/失败） |

---

### 二、异常组分类

#### 🔴 异常组 A：VolumeMountFailed — `aiops-e2e/rc-volume-hostpath-missing`

| 字段 | 值 |
|------|-----|
| **Pod** | `rc-volume-hostpath-missing`（命名空间: aiops-e2e） |
| **STATUS** | `ContainerCreating`（实际 Pending） |
| **Node** | node1 |
| **异常类型** | `VolumeMountFailed` |
| **兼容层级** | **L0** |
| **状态关键字** | `ContainerCreating` |
| **标签** | `pod_abnormal_type=VolumeMountFailed` |

**关键证据：**
- Events 原文：`MountVolume.SetUp failed for volume "missing-hostpath" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory`
- Volume 类型：`HostPath`，路径指向 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir`
- 根因：宿主机上该路径**不存在或不是目录**，导致 hostPath 类型检查失败

---

#### 🔴 异常组 B：Error（容器一运行即退出）— `mcp/node-debugger-node1-*`

| 字段 | 值 |
|------|-----|
| **Pod 列表** | 8 个 `node-debugger-node1-*` Pod（命名空间: mcp） |
| **STATUS** | `Error`（Terminated，Exit Code 1） |
| **Node** | node1 |
| **异常类型** | `CrashLoopBackOffRuntime`（单次运行即退出，非循环重启） |
| **兼容层级** | **L2** |
| **状态关键字** | `Error` |

**关键证据（以 node-debugger-node1-497sq 为例）：**
- `kubectl describe` 显示容器已 Terminated，Reason=Error，Exit Code=1
- Command 为：`ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir`
- 该路径在宿主机上**不存在**，`ls` 命令返回非零退出码 1
- 镜像 `busybox:1.36` 正常 Pulled
- 容器启动后立即完成退出（Started 和 Finished 在同一秒）

**根因：** 这些 `node-debugger` Pod 是**一次性调试任务**，命令执行的目标路径在宿主机上不存在，导致容器启动后立即失败退出。由于 `restartPolicy` 默认为 `Always`（但 Job 类或单次 Pod 已不再重启，所以保持 Error 状态），这些 Pod 不会自动恢复。

---

### 三、分层汇总

| 兼容层 | 异常组 | 影响范围 |
|:------:|--------|:--------:|
| **L0** | VolumeMountFailed — `rc-volume-hostpath-missing` | 1 Pod 卡在 ContainerCreating |
| **L2** | CrashLoopBackOffRuntime — `node-debugger-node1-*` | 8 个 Pod 均为 Error |

- **主层 (layer): L0** — VolumeMountFailed（影响最大，Pod 被阻塞无法运行）
- **次层 (derived_layer): L2** — 8 个 Error Pod（属于一次性调试任务失败）
- **全部兼容层 (layers):** L0, L2

---

### 四、可能场景

| 场景 | 说明 |
|------|------|
| **L0 - hostPath 路径不存在** | `rc-volume-hostpath-missing` 引用了宿主机路径 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir`，该目录不存在，导致 hostPath 挂载失败 |
| **L2 - 调试 Pod 路径依赖缺失** | 8 个 `node-debugger` Pod 也是因为尝试 `ls` 同一个不存在的路径而失败，与 L0 根因关联 |

---

### 五、关键实体

| 实体 | 类型 | 角色 |
|------|------|------|
| `rc-volume-hostpath-missing` | Pod (aiops-e2e) | L0 异常对象 |
| `node-debugger-node1-*` (x8) | Pod (mcp) | L2 异常对象 |
| `node1` | Node | 所有异常 Pod 所在节点 |
| `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` | 宿主机路径 | L0 和 L2 的共同根因路径 |

---

### 六、总结

集群当前有 **9 个异常 Pod**，核心问题集中在 **node1 宿主机上 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 目录不存在**：
1. **L0 严重问题**：`rc-volume-hostpath-missing` Pod 因 hostPath 卷目录缺失而卡在 ContainerCreating，无法正常启动。
2. **L2 衍生问题**：8 个 `node-debugger` 调试 Pod 因同样的路径缺失导致 `ls` 命令失败，容器退出码 1。

**建议方向**：在 node1 上创建 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 目录，或修改 Pod 配置指向实际存在的路径。
   💭 [问题定位] 调用工具: TodoWrite
   💭 [问题定位] 工具结果: TodoWrite (success)
      📄 TodoWrite 输出摘要: raw_chars=369 lines=8
Investigation plan updated with 4 tasks.
# CURRENT INVESTIGATION TASKS
**Task Status**: 4 completed, 0 in progress, 0 pending
[✓] [1] 分析异常 Pod 的状态分类与异常类型
[✓] [2] 
   💭 [问题定位] 所有任务已完成。以上就是当前集群的全部异常定位分析结果。
   ✅ [问题定位] 完成 (34.0s)
   📤 → 下游数据: layer=Layer.L0, layers=L0+L4
   scenarios=[{'scenario': 'hostPath 路径不存在导致 VolumeMountFailed', 'probability': '高', 'reason': 'Events 明确指示 /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory，hostPath 类型检查失败'}, {'scenario': 'Pod 命令错误导致容器异常退出', 'probability': '高', 'reason': 'node-debugger 容器执行 ls -la 不存在的目录，Exit Code 1，属于应用层配置错误'}]
   entities=[{"type": "Pod", "name": "rc-volume-hostpath-missing", "namespace": "aiops-e2e"}, {"type": "Pod", "name": "node-debugger-node1-497sq", "namespace": "mcp"}, {"type": "Node", "name": "node1", "namespace": ""}]
   reasoning=集群存在 2 类异常 Pod：(1) aiops-e2e/rc-volume-hostpath-missing 处于 ContainerCreating 状态，Events 明确指示 MountVolume.SetUp failed for volume "missing-hostpath": hostPath type check failed，属于 VolumeMountFailed，归因 L0/storage_volume；(2) mcp/node-debugger-node1-* 共 8 个 Pod 处于 Error 状态，Exit Code 1，命令为 ls -la 一个不存在的目录，属于应用命令错误，归因 L4/app_config。当前异常以 aiops-e2e/rc-volume-hostpath-missing 的 VolumeMountFailed 为最底层根因(L0)，同时 node-debugger 的 Error(L4) 作为次要问题。二者均为当前仍活跃的异常对象。
   layer_analysis={"layer": "L0", "derived_layer": "L0", "layers": ["L0", "L4"], "layer_name": "storage_volume", "confidence": 0.95, "reasoning": "集群存在 2 类异常 Pod：(1) aiops-e2e/rc-volume-hostpath-missing 处于 ContainerCreating 状态，Events 明确指示 MountVolume.SetUp failed for volume \"missing-hostpath\": hostPath type check failed，属于 VolumeMountFailed，归因 L0/storage_volume；(2) mcp/node-debugger-node1-* 共 8 个 Pod 处于 Error 状态，Exit Code 1，命令为 ls -la 一个不存在的目录，属于应用命令错误，归因 L4/app_config。当前异常以 aiops-e2e/rc-volume-hostpath-missing 的 VolumeMountFailed 为最底层根因(L0)，同时 node-debugger 的 Error(L4) 作为次要问题。二者均为当前仍活跃的异常对象。", "abnormal_pods": [{"name": "rc-volume-hostpath-missing", "namespace": "aiops-e2e", "status": "ContainerCreating"}, {"name": "node-debugger-node1-497sq", "namespace": "mcp", "status": "Error"}, {"name": "node-debugger-node1-6hc9t", "namespace": "mcp", "status": "Error"}, {"name": "node-debugger-node1-6xw6h", "namespace": "mcp", "status": "Error"}, {"name": "node-debugger-node1-dphk7", "namespace": "mcp", "status": "Error"}, {"name": "node-debugger-node1-fh2m9", "namespace": "mcp", "status": "Error"}, {"name": "node-debugger-node1-jt75t", "namespace": "mcp", "status": "Error"}, {"name": "node-debugger-node1-s5fql", "namespace": "mcp", "status": "Error"}, {"name": "node-debugger-node1-vjs5b", "namespace": "mcp", "status": "Error"}], "pod_status_keyword": "ContainerCreating", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "Pod", "name": "rc-volume-hostpath-missing", "namespace": "aiops-e2e"}, {"type": "Pod", "name": "node-debugger-node1-497sq", "namespace": "mcp"}, {"type": "Node", "name": "node1", "namespace": ""}], "possible_scenarios": [{"scenario": "hostPath 路径不存在导致 VolumeMountFailed", "probability": "高", "reason": "Events 明确指示 /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory，hostPath 类型检查失败"}, {"scenario": "Pod 命令错误导致容器异常退出", "probability": "高", "reason": "node-debugger 容器执行 ls -la 不存在的目录，Exit Code 1，属于应用层配置错误"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-hostpath-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["Error"], "pod_abnormal_type": "Error", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-497sq"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6hc9t"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6xw6h"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-dphk7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-fh2m9"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jt75t"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-s5fql"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-vjs5b"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "Error 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-hostpath-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["Error"], "pod_abnormal_type": "Error", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-497sq"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6hc9t"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6xw6h"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-dphk7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-fh2m9"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jt75t"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-s5fql"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-vjs5b"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "Error 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Error": 8}, "total_abnormal": 8, "selected_rows": ["aiops-e2e         rc-volume-hostpath-missing                          0/1     ContainerCreating   0              31m     <none>           node1    <none>           <none>            app=rc-volume-hostpath-missing,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true", "mcp               node-debugger-node1-497sq                           0/1     Error               0              16m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-6hc9t                           0/1     Error               0              4m9s    10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-6xw6h                           0/1     Error               0              43s     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-dphk7                           0/1     Error               0              24m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-fh2m9                           0/1     Error               0              28m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-jt75t                           0/1     Error               0              29m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-s5fql                           0/1     Error               0              59s     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-vjs5b                           0/1     Error               0              26m     10.2.0.49        node1    <none>           <none>            <none>"], "raw_ref": "/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L0 + L4（主层级: Layer.L0）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来按既有 evidence_plan 执行真实工具采证。先启动多个独立的调用来并行采集关键证据。

## 开始执行证据采集

**异常组 g1（主异常 - ContainerCreating/VolumeMountFailed）** 和 **异常组 g2（Error - 8个 Pod）** 同步开始采集。
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_previous_logs
   💭 [证据链采集] 调用工具: kubectl_get_by_kind_in_namespace
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
   💭 [证据链采集] 工具结果: kubectl_previous_logs (success)
      📄 kubectl_previous_logs 输出摘要: raw_chars=211 lines=3
Command failed (exit 1):
kubectl logs node-debugger-node1-497sq -n mcp --previous --tail=200
Error from server (BadRequest): previous terminated conta
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
  Warning  FailedMount  99s (x23 over 32m)    kubelet            MountVolume.Set
   💭 [证据链采集] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=13 abnormal=8 status_counts={'Running': 1, 'Error': 8}
NAME                                  READY   STATUS      RESTARTS   AGE     IP               NODE   
   💭 [证据链采集] 好，前5项关键证据已到位。现在继续执行最后两个计划项：验证节点上 hostPath 目录是否存在，以及读取已确认的 runbook 参考。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                        READY   STATUS   RESTARTS   AGE     IP          NODE    NOMINATED NODE   READINESS GATES   LABELS
node-debugger-node1-6hc9t   0/1     Error    0          4m57s   10.2.0.49 
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "error: unknown command \"node-shell\" for \"kubectl\"\nCreating debugging pod node-debugger-node1-lrbqz with container debugger on node node1.\nls: /tmp/aiops-rootcause-de
   💭 [证据链采集] 所有关键证据已采集完成。现在看一下 node1 上剩余的 Error Pod 状态一致性：
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 调用工具: kubectl_get_by_name
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                        READY   STATUS   RESTARTS   AGE   IP          NODE    NOMINATED NODE   READINESS GATES   LABELS
node-debugger-node1-6xw6h   0/1     Error    0          94s   10.2.0.49   no
   💭 [证据链采集] 工具结果: kubectl_get_by_name (success)
      📄 NAME                        READY   STATUS   RESTARTS   AGE   IP          NODE    NOMINATED NODE   READINESS GATES   LABELS
node-debugger-node1-dphk7   0/1     Error    0          25m   10.2.0.49   no
   💭 [证据链采集] 所有 Error Pod 状态一致。现在整理证据结论。

---

## 证据采集结论

### ✅ 已采集证据

#### 异常组 g1：aiops-e2e/rc-volume-hostpath-missing（ContainerCreating → VolumeMountFailed）
| 维度 | 证据 | 来源 |
|------|------|------|
| **核心错误** | `MountVolume.SetUp failed for volume "missing-hostpath" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory` | `kubectl_describe pod` Events（x23 over 32m） |
| **Volume 类型** | `volumes[].missing-hostpath` 类型为 `HostPath`，路径 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` | `kubectl_get_yaml pod` |
| **节点路径不存在** | 通过 `kubectl debug node/node1` 在 node1 上执行 `ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir` 返回 `No such file or directory` | `run_bash_command` 真实节点验证 |
| **Pod 当前状态** | phase=`Pending`，container=Waiting(ContainerCreating)，容器命令为 `sh -c sleep 3600`（正常），非命令问题 | `kubectl_get_yaml` |
| **无其他依赖问题** | 不涉及 PVC/PV/StorageClass/Secret/ConfigMap | `kubectl_describe` + `kubectl_get_yaml` 确认 |

**根因：** node1 节点上 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 目录不存在，导致 hostPath 类型检查失败，Pod 卡在 ContainerCreating。

---

#### 异常组 g2：mcp/node-debugger-node1-*（Error × 8）
| 维度 | 证据 | 来源 |
|------|------|------|
| **代表 Pod 状态** | `node-debugger-node1-497sq`：State=Terminated, Reason=Error, Exit Code=1 | `kubectl_describe pod` |
| **执行命令** | `ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir` | `kubectl_describe pod` |
| **无 previous logs** | 容器未重启过（Restart Count=0），`--previous` 日志不存在 | `kubectl_previous_logs` 返回 NotFound |
| **所有 Error Pod 状态一致** | 8 个 Pod 全部在 node1 上，STATUS=Error，0/1 READY，Restarts=0 | `kubectl_get_by_kind_in_namespace mcp` + 单 Pod 确认 |

**根因：** `node-debugger-node1-*` Pod 执行 `ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir`，该目录不存在，`ls` 返回 Exit Code 1，容器直接退出。属于应用命令错误（预期的调试命令目标路径不存在）。

---

### ⚠️ 负向/冲突证据
- **`kubectl_previous_logs`** 对 `node-debugger-node1-497sq` 返回 NotFound：确认该 Pod 从未重启过，Exit Code 1 后直接终止，无 crash 前日志。
- **`kubectl node-shell`** 不可用：回退到 `kubectl debug` 方式验证成功。

---

### 📌 总体判断

**L0 根因（最底层）：** node1 节点上 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 目录不存在

**故障链：**
1. `rc-volume-hostpath-missing`（aiops-e2e）因 hostPath 目录不存在 → **VolumeMountFailed**（L0）
2. 8 个 `node-debugger-node1-*`（mcp）因执行 `ls` 不存在的目录 → **命令错误退出**（L4，次要问题）

**两个异常组共享同一个根因：** 目标路径 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 在 node1 上不存在。
   ✅ [证据链采集] 完成 (27.7s)
   📤 → 下游数据: evidence_items=9/11
   evidence_analysis={"evidence_plan":[{"id":"g1-pod-describe","description":"验证 aiops-e2e/rc-volume-hostpath-missing 当前状态和 Events（VolumeMountFailed 主异常）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-hostpath-missing -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-volume-hostpath-missing","namespace":"aiops-e2e"},"purpose":"确认 Pod 的 ContainerCreating 状态、Events 中的 FailedMount 错误原文","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-pod-yaml","description":"检查 Pod spec volumes 类型，确认 hostPath 路径配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-volume-hostpath-missing","namespace":"aiops-e2e"},"purpose":"确认 volumes[].hostPath 路径配置是否指向不存在的目录","evidence_type":"pod_spec","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g1-node-check","description":"验证 node1 上 hostPath 目录是否存在","level":"important","tool":"run_bash_command","command":"kubectl node-shell node1 -- ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir 2>&1 || kubectl debug node/node1 -it --image=busybox:1.36 -- ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir 2>&1","tool_args":{"command":"kubectl node-shell node1 -- ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir 2>&1 || kubectl debug node/node1 -it --image=busybox:1.36 -- ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir 2>&1"},"purpose":"验证节点上 hostPath 目录确实不存在","evidence_type":"node_path_check","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-pod-describe-rep","description":"验证 mcp/node-debugger-node1-497sq 的 Error 状态和 Exit Code（Error 异常组代表 Pod）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-497sq -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-497sq","namespace":"mcp"},"purpose":"确认该代表 Pod 的 State、Exit Code、Last State 等关键信息","evidence_type":"pod_events","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-pod-previous-logs","description":"获取 mcp/node-debugger-node1-497sq 崩溃前日志","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs pod/node-debugger-node1-497sq -n mcp --previous --tail=200","tool_args":{"name":"node-debugger-node1-497sq","namespace":"mcp"},"purpose":"查看容器退出前的输出，确认命令错误的具体表现","evidence_type":"pod_logs","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-other-pods-status","description":"快速验证 mcp namespace 中其余 7 个 Error Pod 的状态一致性","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get pod -n mcp --field-selector=status.phase!=Running --no-headers","tool_args":{"namespace":"mcp"},"purpose":"确认所有 Error Pod 的状态字段一致性","evidence_type":"pod_status","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-runbook-ref","description":"参考 pod-volume-mount-failed runbook 上下文","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-volume-mount-failed.md","tool_args":{"runbook_name":"pod-volume-mount-failed.md"},"purpose":"确认 runbook 中 hostPath 路径分支的诊断步骤","evidence_type":"reference","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-497sq\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://a350370c91c7af4e3da74a4120336f554ef0954402600a9a78fab4108e81881e\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      ls\n      -la\n      /tmp/aiops-rootcause-definitely-missing-hostpath-dir\n    State:          Terminated\n      Reason:       Error\n      Exit Code:    1\n      Started:      Thu, 21 May 2026 05:38:40 +0000\n      Finished:     Thu, 21 May 2026 05:38:40 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-pv6vg:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Type    Reason   Age   From     Message\n  ----    ------   ----  ----     -------\n  Normal  Pulled   17m   kubelet  Container image \"busybox:1.36\" already present on machine\n  Normal  Created  17m   kubelet  Created container debugger\n  Normal  Started  17m   kubelet  Started container debugger\n关键状态/事件:\nStatus:           Failed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/001-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/001-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/001-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_previous_logs","data":"kubectl_previous_logs 输出摘要: raw_chars=211 lines=3\nCommand failed (exit 1):\nkubectl logs node-debugger-node1-497sq -n mcp --previous --tail=200\nError from server (BadRequest): previous terminated container \"debugger\" in pod \"node-debugger-node1-497sq\" not found","duration_s":0,"semantic_success":false,"raw_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/002-evidence-kubectl_previous_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/002-evidence-kubectl_previous_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/002-evidence-kubectl_previous_logs.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-hostpath-missing\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T05:24:07Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-hostpath-missing, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"missing-hostpath\"}\n- {\"name\": \"kube-api-access-m54dz\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/003-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/003-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/003-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-hostpath-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  99s (x23 over 32m)    kubelet            MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory\n  Warning  FailedMount  9m52s (x10 over 30m)  kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-hostpath], unattached volumes=[missing-hostpath kube-api-access-m54dz]: timed out waiting for the condition\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  missing-hostpath:\n    Type:          HostPath (bare host directory volume)\n    Path:          /tmp/aiops-rootcause-definitely-missing-hostpath-dir\n  kube-api-access-m54dz:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedMount  9m52s (x10 over 30m)  kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-hostpath], unattached volumes=[missing-hostpath kube-api-access-m54dz]: timed out waiting for the condition\n  Warning  FailedMount  99s (x23 over 32m)    kubelet            MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_get_by_kind_in_namespace","data":"kubectl_get_by_kind_in_namespace 表格摘要: rows=13 abnormal=8 status_counts={'Running': 1, 'Error': 8}\nNAME                                  READY   STATUS      RESTARTS   AGE     IP               NODE    NOMINATED NODE   READINESS GATES   LABELS\n# 异常行\nnode-debugger-node1-497sq             0/1     Error       0          17m     10.2.0.49        node1   <none>           <none>            <none>\nnode-debugger-node1-6hc9t             0/1     Error       0          4m54s   10.2.0.49        node1   <none>           <none>            <none>\nnode-debugger-node1-6xw6h             0/1     Error       0          88s     10.2.0.49        node1   <none>           <none>            <none>\nnode-debugger-node1-dphk7             0/1     Error       0          25m     10.2.0.49        node1   <none>           <none>            <none>\nnode-debugger-node1-fh2m9             0/1     Error       0          29m     10.2.0.49        node1   <none>           <none>            <none>\nnode-debugger-node1-jt75t             0/1     Error       0          30m     10.2.0.49        node1   <none>           <none>            <none>\nnode-debugger-node1-s5fql             0/1     Error       0          104s    10.2.0.49        node1   <none>           <none>            <none>\nnode-debugger-node1-vjs5b             0/1     Error       0          27m     10.2.0.49        node1   <none>           <none>            <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/005-evidence-kubectl_get_by_kind_in_namespace.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/005-evidence-kubectl_get_by_kind_in_namespace.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/005-evidence-kubectl_get_by_kind_in_namespace.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                        READY   STATUS   RESTARTS   AGE     IP          NODE    NOMINATED NODE   READINESS GATES   LABELS\nnode-debugger-node1-6hc9t   0/1     Error    0          4m57s   10.2.0.49   node1   <none>           <none>            <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/006-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/006-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/006-evidence-kubectl_get_by_name.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"error: unknown command \\\"node-shell\\\" for \\\"kubectl\\\"\\nCreating debugging pod node-debugger-node1-lrbqz with container debugger on node node1.\\nls: /tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/007-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/007-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/007-evidence-run_bash_command.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                        READY   STATUS   RESTARTS   AGE   IP          NODE    NOMINATED NODE   READINESS GATES   LABELS\nnode-debugger-node1-6xw6h   0/1     Error    0          94s   10.2.0.49   node1   <none>           <none>            <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/008-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/008-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/008-evidence-kubectl_get_by_name.summary.txt"},{"tool":"kubectl_get_by_name","data":"NAME                        READY   STATUS   RESTARTS   AGE   IP          NODE    NOMINATED NODE   READINESS GATES   LABELS\nnode-debugger-node1-dphk7   0/1     Error    0          25m   10.2.0.49   node1   <none>           <none>            <none>","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/009-evidence-kubectl_get_by_name.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/009-evidence-kubectl_get_by_name.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/7f2c8144237a4c4b/tools/009-evidence-kubectl_get_by_name.summary.txt"}],"llm_analysis":"所有 Error Pod 状态一致。现在整理证据结论。\n\n---\n\n## 证据采集结论\n\n### ✅ 已采集证据\n\n#### 异常组 g1：aiops-e2e/rc-volume-hostpath-missing（ContainerCreating → VolumeMountFailed）\n| 维度 | 证据 | 来源 |\n|------|------|------|\n| **核心错误** | `MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory` | `kubectl_describe pod` Events（x23 over 32m） |\n| **Volume 类型** | `volumes[].missing-hostpath` 类型为 `HostPath`，路径 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` | `kubectl_get_yaml pod` |\n| **节点路径不存在** | 通过 `kubectl debug node/node1` 在 node1 上执行 `ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir` 返回 `No such file or directory` | `run_bash_command` 真实节点验证 |\n| **Pod 当前状态** | phase=`Pending`，container=Waiting(ContainerCreating)，容器命令为 `sh -c sleep 3600`（正常），非命令问题 | `kubectl_get_yaml` |\n| **无其他依赖问题** | 不涉及 PVC/PV/StorageClass/Secret/ConfigMap | `kubectl_describe` + `kubectl_get_yaml` 确认 |\n\n**根因：** node1 节点上 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 目录不存在，导致 hostPath 类型检查失败，Pod 卡在 ContainerCreating。\n\n---\n\n#### 异常组 g2：mcp/node-debugger-node1-*（Error × 8）\n| 维度 | 证据 | 来源 |\n|------|------|------|\n| **代表 Pod 状态** | `node-debugger-node1-497sq`：State=Terminated, Reason=Error, Exit Code=1 | `kubectl_describe pod` |\n| **执行命令** | `ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir` | `kubectl_describe pod` |\n| **无 previous logs** | 容器未重启过（Restart Count=0），`--previous` 日志不存在 | `kubectl_previous_logs` 返回 NotFound |\n| **所有 Error Pod 状态一致** | 8 个 Pod 全部在 node1 上，STATUS=Error，0/1 READY，Restarts=0 | `kubectl_get_by_kind_in_namespace mcp` + 单 Pod 确认 |\n\n**根因：** `node-debugger-node1-*` Pod 执行 `ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir`，该目录不存在，`ls` 返回 Exit Code 1，容器直接退出。属于应用命令错误（预期的调试命令目标路径不存在）。\n\n---\n\n### ⚠️ 负向/冲突证据\n- **`kubectl_previous_logs`** 对 `node-debugger-node1-497sq` 返回 NotFound：确认该 Pod 从未重启过，Exit Code 1 后直接终止，无 crash 前日志。\n- **`kubectl node-shell`** 不可用：回退到 `kubectl debug` 方式验证成功。\n\n---\n\n### 📌 总体判断\n\n**L0 根因（最底层）：** node1 节点上 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 目录不存在\n\n**故障链：**\n1. `rc-volume-hostpath-missing`（aiops-e2e）因 hostPath 目录不存在 → **VolumeMountFailed**（L0）\n2. 8 个 `node-debugger-node1-*`（mcp）因执行 `ls` 不存在的目录 → **命令错误退出**（L4，次要问题）\n\n**两个异常组共享同一个根因：** 目标路径 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 在 node1 上不存在。","collection_summary":"计划 6 项，实际采集 5 项，未采集 1 项，完整度 83%；其中真实环境证据 9/10 项，完整度 90%；实际执行工具 13 个，匹配计划 5 个，未规划证据 8 个","plan_total":6,"plan_collected":5,"plan_completeness":0.8333333333333334,"environment_evidence_total":10,"environment_evidence_collected":9,"environment_evidence_completeness":0.9,"executed_tool_count":13,"matched_tool_count":5,"unplanned_tool_count":8,"evidence_inventory":[{"id":"g1-pod-describe","description":"验证 aiops-e2e/rc-volume-hostpath-missing 当前状态和 Events（VolumeMountFailed 主异常）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-hostpath-missing -n aiops-e2e","purpose":"确认 Pod 的 ContainerCreating 状态、Events 中的 FailedMount 错误原文","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-pod-yaml","description":"检查 Pod spec volumes 类型，确认 hostPath 路径配置","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o yaml","purpose":"确认 volumes[].hostPath 路径配置是否指向不存在的目录","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-node-check","description":"验证 node1 上 hostPath 目录是否存在","level":"important","tool":"run_bash_command","command":"kubectl node-shell node1 -- ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir 2>&1 || kubectl debug node/node1 -it --image=busybox:1.36 -- ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir 2>&1","purpose":"验证节点上 hostPath 目录确实不存在","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-pod-describe-rep","description":"验证 mcp/node-debugger-node1-497sq 的 Error 状态和 Exit Code（Error 异常组代表 Pod）","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-497sq -n mcp","purpose":"确认该代表 Pod 的 State、Exit Code、Last State 等关键信息","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-pod-previous-logs","description":"获取 mcp/node-debugger-node1-497sq 崩溃前日志","level":"important","tool":"kubectl_previous_logs","command":"kubectl logs pod/node-debugger-node1-497sq -n mcp --previous --tail=200","purpose":"查看容器退出前的输出，确认命令错误的具体表现","collected":false,"source":"planned","outcome":"unknown"},{"id":"g2-other-pods-status","description":"快速验证 mcp namespace 中其余 7 个 Error Pod 的状态一致性","level":"important","tool":"kubectl_get_by_kind_in_namespace","command":"kubectl get pod -n mcp --field-selector=status.phase!=Running --no-headers","purpose":"确认所有 Error Pod 的状态字段一致性","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-runbook-ref","description":"参考 pod-volume-mount-failed runbook 上下文","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-volume-mount-failed.md","purpose":"确认 runbook 中 hostPath 路径分支的诊断步骤","collected":false,"source":"planned","outcome":"unknown"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["g2-pod-previous-logs(获取 mcp/node-debugger-node1-497sq 崩溃前日志): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 5/6 项, 完整度: 90%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | g1-pod-describe | critical | ✅ | kubectl_describe | 验证 aiops-e2e/rc-volume-hostpath-missing 当前状态和... | `kubectl describe pod rc-volume-hostpath-missing -n aiops-e2e` |
   | g1-pod-yaml | critical | ✅ | kubectl_get_yaml | 检查 Pod spec volumes 类型，确认 hostPath 路径配置 | `kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o yaml` |
   | g1-node-check | important | ✅ | run_bash_command | 验证 node1 上 hostPath 目录是否存在 | `kubectl node-shell node1 -- ls -la /tmp/aiops-rootcause-definitely-missing-ho...` |
   | g2-pod-descri... | critical | ✅ | kubectl_describe | 验证 mcp/node-debugger-node1-497sq 的 Error 状态和 ... | `kubectl describe pod node-debugger-node1-497sq -n mcp` |
   | g2-pod-previo... | important | ❌ | kubectl_previous_logs | 获取 mcp/node-debugger-node1-497sq 崩溃前日志 | `kubectl logs pod/node-debugger-node1-497sq -n mcp --previous --tail=200` |
   | g2-other-pods... | important | ✅ | kubectl_get_by_kind_in_na... | 快速验证 mcp namespace 中其余 7 个 Error Pod 的状态一致性 | `kubectl get pod -n mcp --field-selector=status.phase!=Running --no-headers` |
   | g1-runbook-ref | reference | ❌ | fetch_runbook | 参考 pod-volume-mount-failed runbook 上下文 | `fetch_runbook pod-volume-mount-failed.md` |

   ⚠️ 未采集原因:
   - g2-pod-previous-logs(获取 mcp/node-debugger-node1-497sq 崩溃前日志): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (24.4s)
   📤 → 下游数据: root_cause=集群存在 2 类异常 Pod，根因均指向 node1 节点上 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 目录缺失。g1: aiops-e2e/rc-volume-hostpath-missing (ContainerCreating/VolumeMountFailed) — kubelet Events 明确报错 "hostPath type check failed: ... is not a directory"（x23 over 32m），节点真实验证确认 `ls: No such file or directory`。g2: mcp/node-debugger-node1-* 共 8 个 Pod（Error, Exit Code 1）— 容器执行 `ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir` 因目录不存在返回 Exit Code 1 立即终止。两个异常组独立但共享同一缺失路径的根因。
   confidence=98%
   causal_chain={"root_cause": "node1 节点上 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 目录不存在，导致两个独立的异常组均因此受影响", "propagation": "g1: hostPath 目录缺失 → kubelet 挂载时 hostPath type check 失败 → Pod 卡在 ContainerCreating 无法启动；g2: debug Pod 执行 ls -la 该不存在的目录 → ls 返回 Exit Code 1 → 容器立即终止 → Pod 进入 Error 状态。两条传播路径独立但共享同一个缺失目录的根因。", "direct_cause": "g1: kubelet 无法挂载 hostPath volume missing-hostpath，因为路径不是有效目录；g2: 容器命令 ls -la 目标路径不存在导致非零退出码。", "manifestation": "g1: aiops-e2e/rc-volume-hostpath-missing 处于 Pending/ContainerCreating，Events 反复报 FailedMount；g2: mcp/node-debugger-node1-* 共 8 个 Pod 全部处于 Error 状态，Exit Code 1。"}
   rca_analysis={"phenomenon": "集群存在 2 类异常 Pod：aiops-e2e/rc-volume-hostpath-missing 处于 ContainerCreating（Pending）状态，VolumeMountFailed 类型；mcp/node-debugger-node1-* 共 8 个 Pod 处于 Error 状态，Exit Code 1。", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe (rc-volume-hostpath-missing)", "content": "Events: Warning FailedMount x23 over 32m - hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml (rc-volume-hostpath-missing)", "content": "volumes[].missing-hostpath 类型 HostPath，路径 /tmp/aiops-rootcause-definitely-missing-hostpath-dir；phase=Pending；container命令正常 sh -c sleep 3600", "reliability": "高"}, {"id": "e3", "source": "run_bash_command (node1 节点验证)", "content": "在 node1 上执行 ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir 返回 No such file or directory", "reliability": "高"}, {"id": "e4", "source": "kubectl_describe (node-debugger-node1-497sq)", "content": "State=Terminated, Reason=Error, Exit Code=1; Command: ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir; Restart Count=0", "reliability": "高"}, {"id": "e5", "source": "kubectl_get_by_kind_in_namespace (mcp)", "content": "8 个 node-debugger-node1-* Pod 全部 STATUS=Error, READY=0/1, Restarts=0, 全部在 node1", "reliability": "高"}, {"id": "e6", "source": "kubectl_previous_logs (node-debugger-node1-497sq)", "content": "previous terminated container not found - 容器从未重启过", "reliability": "高"}, {"id": "e7", "source": "kubectl_get_by_kind_in_cluster", "content": "全集群 74 Pod，59 Running，8 Error（mcp/node-debugger），1 ContainerCreating（aiops-e2e）", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "Warning FailedMount 99s (x23 over 32m) kubelet MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory", "interpretation": "kubelet 明确报告 hostPath 挂载失败，原因是路径不是目录（is not a directory），这是 Pod 卡在 ContainerCreating 的直接原因"}, {"evidence_id": "e2", "raw_data": "volumes=[{\"name\":\"missing-hostpath\",\"type\":\"HostPath\",\"path\":\"/tmp/aiops-rootcause-definitely-missing-hostpath-dir\"}], phase=Pending, container=Waiting(ContainerCreating)", "interpretation": "Volume 类型为 HostPath，路径指向 /tmp/aiops-rootcause-definitely-missing-hostpath-dir；Pod 当前处于 Pending 阶段，容器等待挂载完成"}, {"evidence_id": "e3", "raw_data": "ls: /tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory", "interpretation": "在 node1 上真实执行检查确认该目录不存在，验证了 hostPath 路径缺失是真实物理问题"}, {"evidence_id": "e4", "raw_data": "Command: ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir; State: Terminated, Reason: Error, Exit Code: 1, Started/Finished 同秒", "interpretation": "node-debugger 容器执行 ls 命令立即退出（同秒内启动并完成），Exit Code 1 表明 ls 因目标路径不存在而报错退出"}, {"evidence_id": "e5", "raw_data": "8 pods all STATUS=Error, Restarts=0, all on node1, ages range from 88s to 30m", "interpretation": "8 个 Error Pod 状态完全一致，均未重启，全部运行在 node1，均为一次性调试 Pod 执行相同命令后失败"}, {"evidence_id": "e6", "raw_data": "Error from server (BadRequest): previous terminated container \"debugger\" in pod \"node-debugger-node1-497sq\" not found", "interpretation": "容器从未重启过，Exit Code 1 后直接终止，无崩溃前日志可获取"}, {"evidence_id": "e7", "raw_data": "rows=74 abnormal=9, Running=59, Error=8, ContainerCreating=1", "interpretation": "全集群 74 个 Pod 中仅此 9 个异常，其余 59 个 Running 正常，异常范围明确"}], "causal_chain": {"root_cause": "node1 节点上 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 目录不存在，导致两个独立的异常组均因此受影响", "propagation": "g1: hostPath 目录缺失 → kubelet 挂载时 hostPath type check 失败 → Pod 卡在 ContainerCreating 无法启动；g2: debug Pod 执行 ls -la 该不存在的目录 → ls 返回 Exit Code 1 → 容器立即终止 → Pod 进入 Error 状态。两条传播路径独立但共享同一个缺失目录的根因。", "direct_cause": "g1: kubelet 无法挂载 hostPath volume missing-hostpath，因为路径不是有效目录；g2: 容器命令 ls -la 目标路径不存在导致非零退出码。", "manifestation": "g1: aiops-e2e/rc-volume-hostpath-missing 处于 Pending/ContainerCreating，Events 反复报 FailedMount；g2: mcp/node-debugger-node1-* 共 8 个 Pod 全部处于 Error 状态，Exit Code 1。"}, "root_cause": "集群存在 2 类异常 Pod，根因均指向 node1 节点上 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 目录缺失。g1: aiops-e2e/rc-volume-hostpath-missing (ContainerCreating/VolumeMountFailed) — kubelet Events 明确报错 \"hostPath type check failed: ... is not a directory\"（x23 over 32m），节点真实验证确认 `ls: No such file or directory`。g2: mcp/node-debugger-node1-* 共 8 个 Pod（Error, Exit Code 1）— 容器执行 `ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir` 因目录不存在返回 Exit Code 1 立即终止。两个异常组独立但共享同一缺失路径的根因。", "root_cause_summary": "集群存在 2 类异常 Pod，根因均指向 node1 节点上 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 目录缺失。g1: aiops-e2e/rc-volume-hostpath-missing (ContainerCreating/VolumeMountFailed) — kubelet Events 明确报错 \"hostPath type check failed: ... is not a directory\"（x23 over 32m），节点真实验证确认 `ls: No such file or directory`。g2: mcp/node-debugger-node1-* 共 8 个 Pod（Error, Exit Code 1）— 容器执行 `ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir` 因目录不存在返回 Exit Code 1 立即终止。两个异常组独立但共享同一缺失路径的根因。", "confidence": 0.98, "confidence_reason": "g1 有完整证据链：kubectl_describe Events 直接报错 → kubectl_get_yaml 确认 volume 类型和路径 → 节点上 run_bash_command 真实验证路径不存在，因果链闭环且无矛盾。g2 有 kubectl_describe 确认 Exit Code 1 和命令内容，所有 8 个 Pod 状态一致（kubectl_get_by_kind_in_namespace 验证），且 Previous logs 不存在确认未重启。置信度 0.98。", "primary_runbooks": ["pod-volume-mount-failed.md", "pod-crashloop-runtime.md"], "alternative_causes": [{"cause": "g1: PVC/PV 类存储问题", "probability": "low", "reason": "Volume 类型为 HostPath 而非 PVC，Events 不涉及任何 PVC/PV 相关错误，已排除"}, {"cause": "g1: Secret/ConfigMap 缺失", "probability": "low", "reason": "kubectl_describe 无相关 Events，容器环境变量为空，Pod spec 仅有一个额外的 projected volume（kube-api-access）"}, {"cause": "g2: 容器镜像问题", "probability": "low", "reason": "kubectl_describe 显示镜像 busybox:1.36 已存在（Pulled event），且 Exit Code 1 非镜像拉取失败"}, {"cause": "g2: 资源不足/OOMKilled", "probability": "low", "reason": "Exit Code 1 非 OOM(137) 或信号终止(128+n)，QoS BestEffort 但无资源不足证据"}], "limitations": "(1) g2 的 8 个 Error Pod 中仅对 node-debugger-node1-497sq 做了完整 describe 验证，其余 7 个仅通过 kubectl_get_by_kind_in_namespace 确认状态一致（STATUS=Error, Restarts=0, 同节点 node1），假设它们命令和配置相同；但命名模式一致且同属于一个调试工具链，该假设合理。(2) 未采集 g2 容器标准输出日志（kubectl logs），因为容器 Exit Code 1 后日志可能为空或仅有 ls 报错，不影响根因判定。", "llm_raw_analysis": "## 证据清点\\n共采集 7 类证据：kubectl_describe（g1 Pod Events）、kubectl_get_yaml（g1 Pod spec）、run_bash_command（节点路径验证）、kubectl_describe（g2 代表 Pod）、kubectl_get_by_kind_in_namespace（g2 批量验证）、kubectl_previous_logs（负向证据）、kubectl_get_by_kind_in_cluster（全集群概况）。\\n\\n## 逐条分析\\n- e1: g1 Pod Events 直接给出错误原因——hostPath type check failed，路径不是目录\\n- e2: g1 Pod spec 确认 volume 类型为 HostPath、路径配置，排除 PVC 类问题\\n- e3: 节点上真实验证路径不存在，确认是物理路径缺失而非配置错误\\n- e4: g2 代表 Pod 的 Exit Code=1 结合命令内容，确认是 ls 找不到目标目录\\n- e5: 8 个 Error Pod 状态一致，说明不是单 Po\n... 截断，原始 908 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 集群存在 2 类异常 Pod，根因均指向 node1 节点上 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 目录缺失。g1: aiops-e2e/rc-volume-hostpath-missing (ContainerCreating...
   置信度: 98%
   🔗 因果链:
     根本原因: node1 节点上 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 目录不存在，导致两个独立的异常组均因此受影响
     传导机制: g1: hostPath 目录缺失 → kubelet 挂载时 hostPath type check 失败 → Pod 卡在 ContainerCreating 无法启动；g2: debug Pod 执行 ls -la 该不存在的目录 → ls 返回 Exit Code 1 → 容器立即终止 → Pod 进入 Error 状态。两条传播路径独立但共享同一个缺失目录的根因。
     最终表现: g1: aiops-e2e/rc-volume-hostpath-missing 处于 Pending/ContainerCreating，Events 反复报 FailedMount；g2: mcp/node-debugger-node1-* 共 8 个 Pod 全部处于 Error 状态，Exit Code 1。


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (21.7s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6697 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 47.8s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，集群状态报告如下。

## 📊 诊断概览

当前集群主要存在两个异常问题，共9个异常Pod。

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | `ContainerCreating` (1个) / `Error` (8个) |
| **兼容归因层** | `L0` / `L4` (根因共享，独立传播) |
| **问题1分类** | `VolumeMountFailed` (hostPath 路径不存在) |
| **问题2分类** | `CrashLoopBackOffRuntime` / 应用命令错误 (目标路径不存在) |
| **置信度** | 高 (98%) |
| **证据完整度** | 5/6 (83%) |

---

## 🔍 问题总结

**你的集群存在一个底层根因导致的两个独立异常**：

1.  **根本问题**：节点 `node1` 上的关键目录 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` **不存在**。
2.  **异常组1 (L0根因)**：`aiops-e2e/rc-volume-hostpath-missing` Pod 因 hostPath 挂载失败，卡在 `ContainerCreating` 状态。
3.  **异常组2 (L4次要问题)**：`mcp/node-debugger-node1-*` 共 8 个 Pod 因执行 `ls` 命令找不到该不存在的目录，全部以 Exit Code 1 进入 `Error` 状态。

---

## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 & 事件 | `kubectl describe pod rc-volume-hostpath-missing -n aiops-e2e` | `Warning FailedMount 99s (x23 over 32m) kubelet MountVolume.SetUp failed for volume "missing-hostpath" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory` | **确认根因1**：kubelet 因 hostPath 路径不是有效目录而无法挂载卷。 |
| 2 | Pod YAML | `kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o yaml` | `command: sh -c sleep 3600`;  `phase: Pending`; `Ready: status=False` | Pod 因卷挂载失败无法启动，命令本身 (`sleep 3600`) 无问题。 |
| 3 | 节点验证 | `run_bash_command` (kubectl node debug) | `ls: /tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory` | **直接确认**：节点 `node1` 上该目录确实不存在。 |
| 4 | Pod 状态 & 事件 | `kubectl describe pod node-debugger-node1-497sq -n mcp` | `Command: ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir`; `State: Terminated, Reason: Error, Exit Code: 1` | **确认根因2**：容器因执行 `ls` 命令时路径不存在而异常退出。 |
| 5 | 集群状态概览 | `kubectl get pods -A` | `NAMESPACE: mcp` 下有 8 个 Pod 状态为 `Error`，全部位于 `node1` 节点。 | 确认 `g2` 组内 8 个 Pod 状态高度一致，均为 `Error`。 |
| 6 | 历史日志 | `kubectl logs node-debugger-node1-497sq -n mcp --previous` | `Command failed... previous terminated container not found` | Pod 未重启过 (`Restarts: 0`)，日志已无更多信息。 |

### 证据关联分析

-   **证据 #1 + #3 印证**：Pod 事件与节点真实验证结果完全一致，确认 `g1` 的根因为宿主机路径不存在。
-   **证据 #3 + #4 印证**：节点路径不存在与 Pod 命令执行失败的 `Exit Code 1` 直接关联，确认 `g2` 的根因同样为该路径缺失。
-   **证据链**：`/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 目录缺失（根因）→ `g1`: hostPath 卷挂载失败（直接原因1） & `g2`: `ls` 命令找不到文件而失败（直接原因2）→ 用户观察到 Pod 异常（表现）。

### 缺失证据（如有）

| 证据 | 级别 | 影响 |
|------|------|------|
| 已规划但采集失败 | | |
| N/A | N/A | 当前证据链已足够闭环，缺失项不影响根因判定。 |

---

## 🎯 根因分析

### 因果链

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                        传播机制1（VolumeMountFailed）     传播机制2（命令错误） │
│ node1 节点上目录                                │                                    │                   │
│ /tmp/aiops-rootcause-definitely-missing-        │                                    │                   │
│ hostpath-dir **不存在**                          │                                    │                   │
└─────────────────────────────────────────────────┘                                    │                   │
                      │                                                               │                   │
                      ├───────────────────────────────────────────────────────────────┤                   │
                      │                                                               │                   │
                      ▼                                                               ▼                   │
┌──────────────────────────────────────────────┐                 ┌───────────────────────────────────────────┐
│ 直接原因1 (L0)                                │                 │ 直接原因2 (L4)                             │
│ kubelet 尝试挂载 hostPath 卷时，               │                 │ Pod 执行 `ls -la` 命令时，                  │
│ 因路径不是有效目录，hostPath type check 失败。  │                 │ 因目标路径不存在，返回 Exit Code 1。          │
│ 挂载事件反复触发并失败。                       │                 │ 命令即刻终止，容器进入 Error 状态。           │
└──────────────────────────────────────────────┘                 └───────────────────────────────────────────┘
                      │                                                               │
                      ▼                                                               ▼
┌──────────────────────────────────────────────┐                 ┌───────────────────────────────────────────┐
│ 用户可见现象1                                  │                 │ 用户可见现象2                               │
│ Pod `rc-volume-hostpath-missing`               │                 │ `mcp` 命名空间下 8 个 `node-debugger` Pod     │
│ 卡在 **ContainerCreating** 状态。              │                 │ 全部处于 **Error** 状态。                     │
└──────────────────────────────────────────────┘                 └───────────────────────────────────────────┘
```

### 根因结论

**结论**：集群问题的根本原因是**节点 `node1` 上 ` /tmp/aiops-rootcause-definitely-missing-hostpath-dir` 目录缺失**。

-   **证据 #1** 和 **#3** 明确证明 `g1` (VolumeMountFailed) 的直接原因是 hostPath 挂载失败。
-   **证据 #3** 和 **#4** 明确证明 `g2` (Exit Code 1) 的直接原因是 `ls` 命令找不到目录。
-   两个独立异常组共享同一个缺失目录的根因。

**置信度**：高 (98%)
-   ✅ 确凿无误：Pod 事件 (FailedMount)、节点命令 (`ls: No such file...`)、Pod Exit Code (1) 三者完全吻合。
-   ⚠️ 未采集 `g2` 组所有 Pod 的日志，但鉴于 8 个 Pod 状态、节点、命名模式一致，推断其根因相同是合理的。

---

## 🛠️ 修复建议

### 立即执行（按优先级排序）

**1. [优先] 在节点上创建缺失的目录**

*(警告：此操作会触发 Pod 自动恢复)*

```bash
# 使用 kubectl node-shell 进入节点（如果可用），或通过 SSH 登录到 node1 节点
# 然后在 node1 节点上执行：
mkdir -p /tmp/aiops-rootcause-definitely-missing-hostpath-dir
```
*依据*：`Evidence #3` 确认目录 `No such file or directory`，创建后 kubelet 会自动完成 hostPath 挂载，`g1` Pod 应能启动。`g2` 中的 `node-debugger` Pod 是调试用途，通常无需持久保持，但创建目录后新启动的 debug Pod 也将正常运行。

### 后续优化

1.  **资源清理**：删除不再需要的 `Error` 状态 Pod：
    ```bash
    kubectl delete pods -n mcp -l <selector-if-any>  # 或逐个删除
    ```
2.  **配置审查**：检查创建此 hostPath 卷的工作负载配置，确保路径在生产环境也存在，或改用其他更可靠的数据持久化方式 (如 `hostPath` 类型设为 `DirectoryOrCreate`)。
3.  **监控告警**：考虑对关键节点的关键目录存在性进行监控。

---

## 📋 验证步骤

| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 确认目录已创建 | `kubectl node-shell node1 -- ls -ld /tmp/aiops-rootcause-definitely-missing-hostpath-dir` | 显示 `drwxr-xr-x` 开头 |
| 2. 检查 Pod 启动 | `kubectl get pod rc-volume-hostpath-missing -n aiops-e2e` | STATUS 从 `ContainerCreating` 变为 `Running` |
| 3. 确认 Error Pod 状态 | `kubectl get pods -n mcp` | 所有 `node-debugger` Pod 状态应为 `Running` (如果是新启动的) 或已被删除。 |

---

## ⚠️ 注意事项

-   **`kubectl node-shell`** 命令可能需要在集群中预装插件，请根据你的环境调整。如果无法使用，请通过 SSH 或其他方式登录到 `node1` 主机执行 `mkdir` 命令。
-   `node-debugger` 这类 Pod 通常是临时调试工具，其 `Error` 状态通常不影响集群核心服务，但反映了节点环境的缺失。
-   解决根本问题（创建目录）后，`g1` 和 `g2` 的问题将同时被修复。

---

## 📊 性能统计

├─ 总耗时: 1.8m
├─ 问题定位: 34.0s (32%) ✅
├─ 证据链采集: 27.7s (26%) ✅
├─ 根因分析: 24.4s (23%) ✅
├─ 汇总总结: 21.7s (20%) ✅
├─ LLM 调用: 4 次
└─ 工具调用: 18 次
```

📋 诊断追踪

- **核心 Runbook**: pod-volume-mount-failed, pod-crashloop-runtime
- **参考 Runbook**: pod-volume-mount-failed, pod-crashloop-runtime
- **工具调用**: 18 次
- **LLM 调用**: 4 次


======================================================================
✅ 诊断完成!
======================================================================
