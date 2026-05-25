======================================================================
🔄 K8s AIOps Copilot - 工作流诊断模式
======================================================================

📝 问题: 我的集群有什么问题

----------------------------------------------------------------------
🚀 开始诊断 [run_id: b87447a193d541fe]

📍 [问题定位] 执行中...
   💭 [问题定位] 我来先全局扫描集群中的 Pod 状态，看看有没有异常情况。
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=75 abnormal=10 status_counts={'Running': 59, 'Error': 9}
NAMESPACE         NAME                                                READY   STATUS              RES
   💭 [问题定位] 我看到集群中有一些异常 Pod。让我进一步查看关键信息。
   💭 [问题定位] 调用工具: kubectl_get_by_name
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_namespace
   💭 [问题定位] 调用工具: kubectl_get_by_kind_in_cluster
   💭 [问题定位] 工具结果: kubectl_get_by_name (success)
      📄 NAME                         READY   STATUS              RESTARTS   AGE   IP       NODE    NOMINATED NODE   READINESS GATES   LABELS
rc-volume-hostpath-missing   0/1     ContainerCreating   0         
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_cluster (success)
      📄 kubectl_get_by_kind_in_cluster 表格摘要: rows=3 abnormal=0 status_counts={'Ready': 3}
NAME     STATUS   ROLES           AGE    VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION    
   💭 [问题定位] 工具结果: kubectl_get_by_kind_in_namespace (success)
      📄 kubectl_get_by_kind_in_namespace 表格摘要: rows=14 abnormal=9 status_counts={'Running': 1, 'Error': 9}
NAME                                  READY   STATUS      RESTARTS   AGE     IP               NODE   
   💭 [问题定位] 好的，我来获取异常 Pod 的详细信息，看看具体是什么异常。
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 调用工具: kubectl_describe
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-hostpath-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  2m46s (x23 over 33m)  kubelet            MountVolume.Set
   💭 [问题定位] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-jt75t
namespace: mcp
node: node1/10.2.0.49
status: Failed
Pod 关键区块:
QoS Class: BestEffort
Node-Selectors: <none>
Tolerations: op=Exists
Containers:
  deb
   💭 [问题定位] 现在让我取匹配的 runbook 来帮助定位。
   💭 [问题定位] 调用工具: fetch_runbook
   💭 [问题定位] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [问题定位] 好了，我已经掌握了集群中的所有异常情况。下面给出完整的定位分析结果：

---

## 📋 集群异常状态总览

### 整体健康概览
- **节点**: 3 个节点全部 Ready（master/node1/node2），节点层面健康 ✅
- **正常 Pod**: 59 个 Running，5 个正常 Succeeded/Completed
- **异常 Pod**: **10 个**，分布在 2 个命名空间中

---

### 异常组 A：`aiops-e2e/rc-volume-hostpath-missing` — L0 级

| 属性 | 值 |
|------|-----|
| **Pod** | `rc-volume-hostpath-missing`（命名空间 `aiops-e2e`） |
| **状态** | `ContainerCreating` / Pending |
| **Pod 异常类型** | `VolumeMountFailed` |
| **兼容归因层级** | **L0**（存储/卷挂载） |
| **状态关键字** | `ContainerCreating` → 卡在容器创建阶段 |

**关键证据**（来自 Events 和 describe）：
- `MountVolume.SetUp failed for volume "missing-hostpath" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory`
- Pod 引用了 HostPath 类型卷，路径 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` **在节点 node1 上不存在**
- Volume 类型：`HostPath`（裸主机目录），不是 PVC/ConfigMap/Secret
- 标签已预标记 `pod_abnormal_type=VolumeMountFailed`

**审查方向**：需要在 node1 上创建缺失的目录 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir`，或将 Pod volume 路径修正为已存在的目录。

---

### 异常组 B：`mcp/node-debugger-node1-*` — L2 级

| 属性 | 值 |
|------|-----|
| **Pod 列表** | 9 个 `node-debugger-node1-*` Pod（均位于 `mcp` 命名空间） |
| **状态** | 全部 `Error`（已终止，exit code 1） |
| **Pod 异常类型** | `CrashLoopBackOffRuntime`（一次运行即 Exit，但非 OOM） |
| **兼容归因层级** | **L2**（容器运行时/进程退出） |
| **状态关键字** | `Error` → 容器进程运行后以非零码退出 |

**关键证据**（以 `node-debugger-node1-jt75t` 为代表）：
- 容器镜像：`busybox:1.36`
- 启动命令：`ls -la /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir`
- **退出原因**：`Exit Code: 1` — `ls` 命令因目录不存在而报错退出
- 挂载了 hostPath 卷 `host-root`（路径 `/`）
- 容器已启动成功（Pulled/Created/Started 事件正常），但命令执行失败

**根因**：这些 debugger Pod 执行的 `ls` 命令目标路径 `/host/tmp/aiops-rootcause-definitely-missing-hostpath-dir` **不存在**，导致 `ls` 返回 exit code 1。与异常组 A 实际上是**同一个根因**——该目录在 node1 上缺失。

---

### 汇总分析

| 异常组 | Pod 数量 | 异常类型 | 层级 | 根因 |
|--------|---------|---------|------|------|
| A: VolumeMountFailed | 1 | `VolumeMountFailed` | L0 | HostPath 目录不存在 |
| B: Debugger Error | 9 | `CrashLoopBackOffRuntime` | L2 | `ls` 找不到目标目录（相同根因） |

**根本原因链**: node1 节点上 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 目录缺失，导致：
1. hostPath 卷挂载失败（L0，Pod 卡在 ContainerCreating）
2. debugger Pod 执行 `ls -la` 报错退出（L2，9 个 Error Pod）

### 结构输出

```json
{
  "layer": "L0",
  "derived_layer": "L0_L2",
  "layers": ["L0", "L2"],
  "layer_name": "VolumeMountFailed + DebuggerCrash",
  "confidence": 0.95,
  "reasoning": "HostPath 目录 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 在 node1 上缺失，导致一个 Pod 卷挂载失败卡在 ContainerCreating（L0），9 个 debugger Pod 因 ls 找不到目录而 Error 退出（L2）",
  "abnormal_pods": [
    "aiops-e2e/rc-volume-hostpath-missing",
    "mcp/node-debugger-node1-497sq",
    "mcp/node-debugger-node1-6hc9t",
    "mcp/node-debugger-node1-6xw6h",
    "mcp/node-debugger-node1-dphk7",
    "mcp/node-debugger-node1-fh2m9",
    "mcp/node-debugger-node1-jt75t",
    "mcp/node-debugger-node1-lrbqz",
    "mcp/node-debugger-node1-s5fql",
    "mcp/node-debugger-node1-vjs5b"
  ],
  "abnormal_groups": {
    "VolumeMountFailed": ["aiops-e2e/rc-volume-hostpath-missing"],
    "Error_ExitCode1": ["mcp/node-debugger-node1-497sq", "mcp/node-debugger-node1-6hc9t", "mcp/node-debugger-node1-6xw6h", "mcp/node-debugger-node1-dphk7", "mcp/node-debugger-node1-fh2m9", "mcp/node-debugger-node1-jt75t", "mcp/node-debugger-node1-lrbqz", "mcp/node-debugger-node1-s5fql", "mcp/node-debugger-node1-vjs5b"]
  },
  "pod_status_keyword": "ContainerCreating_Error",
  "pod_abnormal_type": "VolumeMountFailed",
  "status_category": "storage_runtime",
  "key_entities": {
    "nodes": ["node1"],
    "missing_path": "/tmp/aiops-rootcause-definitely-missing-hostpath-dir"
  },
  "possible_scenarios": [
    "node1 上 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 目录被误删除或从未创建",
    "hostPath volume 配置引用了不存在的路径",
    "有意的故障注入场景（标签 rootcause-e2e=true 暗示这是 e2e 测试用例）"
  ]
}
```

**建议修复方向**（仅做参考，不执行）：
1. 在 node1 上创建缺失目录：`mkdir -p /tmp/aiops-rootcause-definitely-missing-hostpath-dir`
2. 或修正 Pod spec 中的 hostPath 路径指向正确目录
3. debugger Pod 会自动重新调度，目录创建后新的 debugger Pod 即可正常运行
   ✅ [问题定位] 完成 (31.9s)
   📤 → 下游数据: layer=Layer.L0, layers=L0+L2
   scenarios=[{'scenario': 'node1上HostPath目录被误删除或从未创建', 'probability': '高', 'reason': 'kubectl describe 显示 MountVolume.SetUp failed: hostPath type check failed, 路径不存在'}, {'scenario': 'hostPath volume配置引用了不存在的路径', 'probability': '中', 'reason': 'Pod spec中volume路径指向缺失目录'}, {'scenario': '有意的故障注入e2e测试场景', 'probability': '中', 'reason': 'Pod标签包含rootcause-e2e=true'}]
   entities=[{"type": "node", "name": "node1", "namespace": ""}, {"type": "pod", "name": "rc-volume-hostpath-missing", "namespace": "aiops-e2e"}, {"type": "hostpath", "name": "/tmp/aiops-rootcause-definitely-missing-hostpath-dir", "namespace": ""}]
   reasoning=当前环境中有10个异常Pod。根因是node1上HostPath目录/tmp/aiops-rootcause-definitely-missing-hostpath-dir缺失：(1) aiops-e2e/rc-volume-hostpath-missing卡在ContainerCreating，Event显示MountVolume.SetUp failed - hostPath type check failed，pod_abnormal_type=VolumeMountFailed，归因L0(storage_volume)；(2) mcp命名空间9个node-debugger-node1-* Pod全部Error(exit code 1)，因ls命令找不到同一缺失目录而退出，pod_abnormal_type=CrashLoopBackOffRuntime，归因L2(container_runtime)。选择根因层级L0，因为缺失目录是原始故障点。
   layer_analysis={"layer": "L0", "derived_layer": "L0_L2", "layers": ["L0", "L2"], "layer_name": "VolumeMountFailed + CrashLoopBackOffRuntime", "confidence": 0.95, "reasoning": "当前环境中有10个异常Pod。根因是node1上HostPath目录/tmp/aiops-rootcause-definitely-missing-hostpath-dir缺失：(1) aiops-e2e/rc-volume-hostpath-missing卡在ContainerCreating，Event显示MountVolume.SetUp failed - hostPath type check failed，pod_abnormal_type=VolumeMountFailed，归因L0(storage_volume)；(2) mcp命名空间9个node-debugger-node1-* Pod全部Error(exit code 1)，因ls命令找不到同一缺失目录而退出，pod_abnormal_type=CrashLoopBackOffRuntime，归因L2(container_runtime)。选择根因层级L0，因为缺失目录是原始故障点。", "abnormal_pods": [{"name": "rc-volume-hostpath-missing", "namespace": "aiops-e2e", "status": "ContainerCreating"}, {"name": "node-debugger-node1-497sq", "namespace": "mcp", "status": "Error"}, {"name": "node-debugger-node1-6hc9t", "namespace": "mcp", "status": "Error"}, {"name": "node-debugger-node1-6xw6h", "namespace": "mcp", "status": "Error"}, {"name": "node-debugger-node1-dphk7", "namespace": "mcp", "status": "Error"}, {"name": "node-debugger-node1-fh2m9", "namespace": "mcp", "status": "Error"}, {"name": "node-debugger-node1-jt75t", "namespace": "mcp", "status": "Error"}, {"name": "node-debugger-node1-lrbqz", "namespace": "mcp", "status": "Error"}, {"name": "node-debugger-node1-s5fql", "namespace": "mcp", "status": "Error"}, {"name": "node-debugger-node1-vjs5b", "namespace": "mcp", "status": "Error"}], "pod_status_keyword": "ContainerCreating_Error", "pod_abnormal_type": "VolumeMountFailed", "status_category": "storage_volume", "key_entities": [{"type": "node", "name": "node1", "namespace": ""}, {"type": "pod", "name": "rc-volume-hostpath-missing", "namespace": "aiops-e2e"}, {"type": "hostpath", "name": "/tmp/aiops-rootcause-definitely-missing-hostpath-dir", "namespace": ""}], "possible_scenarios": [{"scenario": "node1上HostPath目录被误删除或从未创建", "probability": "高", "reason": "kubectl describe 显示 MountVolume.SetUp failed: hostPath type check failed, 路径不存在"}, {"scenario": "hostPath volume配置引用了不存在的路径", "probability": "中", "reason": "Pod spec中volume路径指向缺失目录"}, {"scenario": "有意的故障注入e2e测试场景", "probability": "中", "reason": "Pod标签包含rootcause-e2e=true"}], "abnormal_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-hostpath-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["Error"], "pod_abnormal_type": "Error", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-497sq"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6hc9t"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6xw6h"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-dphk7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-fh2m9"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jt75t"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-lrbqz"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-s5fql"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-vjs5b"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "Error 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "issue_groups": [{"group_id": "g1", "status_keywords": ["ContainerCreating"], "pod_abnormal_type": "ContainerCreating", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "aiops-e2e", "name": "rc-volume-hostpath-missing"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "ContainerCreating 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}, {"group_id": "g2", "status_keywords": ["Error"], "pod_abnormal_type": "Error", "compatible_layers": [], "entities": [{"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-497sq"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6hc9t"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-6xw6h"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-dphk7"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-fh2m9"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-jt75t"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-lrbqz"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-s5fql"}, {"kind": "Pod", "namespace": "mcp", "name": "node-debugger-node1-vjs5b"}], "evidence_plan": [], "possible_scenarios": [{"scenario": "Error 待验证", "probability": "低", "reason": "需基于当前状态和事件做最小验证"}]}], "current_abnormal_summary": {"source": "kubectl_get_by_kind_in_cluster", "status_counts": {"Error": 9}, "total_abnormal": 9, "selected_rows": ["aiops-e2e         rc-volume-hostpath-missing                          0/1     ContainerCreating   0              33m     <none>           node1    <none>           <none>            app=rc-volume-hostpath-missing,pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true", "mcp               node-debugger-node1-497sq                           0/1     Error               0              18m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-6hc9t                           0/1     Error               0              5m56s   10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-6xw6h                           0/1     Error               0              2m30s   10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-dphk7                           0/1     Error               0              26m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-fh2m9                           0/1     Error               0              30m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-jt75t                           0/1     Error               0              31m     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-lrbqz                           0/1     Error               0              59s     10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-s5fql                           0/1     Error               0              2m46s   10.2.0.49        node1    <none>           <none>            <none>", "mcp               node-debugger-node1-vjs5b                           0/1     Error               0              28m     10.2.0.49        node1    <none>           <none>            <none>"], "raw_ref": "/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/001-layer-kubectl_get_by_kind_in_cluster.raw.txt", "summary_ref": "/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/001-layer-kubectl_get_by_kind_in_cluster.summary.txt", "structured_ref": "/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/001-layer-kubectl_get_by_kind_in_cluster.structured.json"}}

   ┌──────────────────────────────────────────┐
   │ 📊 问题定位结果                              │
   └──────────────────────────────────────────┘

   层级: L0 + L2（主层级: Layer.L0）
   置信度: 95%

📍 [证据链采集] 执行中...
   💭 [证据链采集] 我来按照既有 evidence_plan 执行工具调用。先执行独立且不互相依赖的多个工具调用。

**主异常组 g1（rc-volume-hostpath-missing）** 和 **非主异常组 g2（node-debugger-node1-*）** 可以同时开始采证。
   💭 [证据链采集] 调用工具: fetch_runbook
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_get_yaml
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_describe
   💭 [证据链采集] 调用工具: kubectl_events
   💭 [证据链采集] 调用工具: kubectl_logs
   💭 [证据链采集] 工具结果: fetch_runbook (success)
      📄 <runbook>
# Pod VolumeMountFailed / 卷挂载失败

> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume

## 使用原则（给模型）
- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。
- `kubectl
   💭 [证据链采集] 工具结果: kubectl_get_yaml (success)
      📄 kubectl_get_yaml 关键字段摘要:
kind: Pod
name: rc-volume-hostpath-missing
namespace: aiops-e2e
creationTimestamp: 2026-05-21T05:24:07Z
deletionTimestamp: <absent>
deletionGracePeriodSeconds: None
finalizers
   💭 [证据链采集] 工具结果: kubectl_logs (success)
      📄 kubectl_logs 日志摘要:
lines: 1
signals: 1
关键日志:
ls: /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: rc-volume-hostpath-missing
namespace: aiops-e2e
node: node1/10.2.0.49
status: Pending
关键诊断行:
  Warning  FailedMount  3m26s (x23 over 34m)  kubelet            MountVolume.Set
   💭 [证据链采集] 工具结果: kubectl_describe (success)
      📄 kubectl_describe 摘要:
name: node-debugger-node1-jt75t
namespace: mcp
node: node1/10.2.0.49
status: Failed
Pod 关键区块:
QoS Class: BestEffort
Node-Selectors: <none>
Tolerations: op=Exists
Containers:
  deb
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
关键诊断行:
3m27s (x23 over 34m)   Warning   FailedMount   Pod/rc-volume-hostpath-missing   MountVolume.SetUp failed for volume "missing-hostpath" : hostPath type check failed: /tmp/aiop
   💭 [证据链采集] 工具结果: kubectl_events (success)
      📄 kubectl_events 摘要:
LAST SEEN   TYPE     REASON    OBJECT                          MESSAGE
31m         Normal   Pulled    Pod/node-debugger-node1-jt75t   Container image "busybox:1.36" already present 
   💭 [证据链采集] 所有 describe/YAML/Events/logs 工具已成功执行。现在执行最后一个关键工具——直接在 node1 上验证缺失目录是否存在。
   💭 [证据链采集] 调用工具: run_bash_command
   💭 [证据链采集] 工具结果: run_bash_command (success)
      📄 {"success": true, "stdout": "Creating debugging pod node-debugger-node1-6mxrg with container debugger on node node1.\nls: /tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or director
   💭 [证据链采集] ## 证据采集完成——结论报告

### ✅ 已采集证据（主异常组 g1：rc-volume-hostpath-missing）

| 证据项 | 结果 |
|--------|------|
| **g1-describe** (Pod Events) | ✅ **已确认** — `MountVolume.SetUp failed for volume "missing-hostpath" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory`，已发生 23 次 |
| **g1-yaml** (Pod spec volumes) | ✅ **已确认** — `.spec.volumes[0].hostPath.path = /tmp/aiops-rootcause-definitely-missing-hostpath-dir`，类型为 HostPath |
| **g1-events** (Events 完整时序) | ✅ **已确认** — FailedMount 事件 x23 持续 34 分钟，最早事件 34m 前开始 |
| **g1-node-check** (目录存在性) | ✅ **已确认** — `ls: /tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory`，目录在 node1 上真实不存在 |

### ✅ 已采集证据（非主异常组 g2：node-debugger-node1-*）

| 证据项 | 结果 |
|--------|------|
| **g2-minimal** (代表 Pod describe) | ✅ **已确认** — Exit Code=1, Reason=Error, 容器命令 `ls -la /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 执行失败 |
| **g2-event-check** (Events) | ✅ **已确认** — 只有 Pulled/Created/Started 正常事件，无异常事件，说明容器正常启动但执行命令因目录缺失退出 |
| **g2-logs** (日志) | ✅ **已确认** — `ls: /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory` |

### 根因结论

**node1 节点上的 HostPath 目录 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 不存在**，导致：

1. **g1 (VolumeMountFailed / L0)** — `rc-volume-hostpath-missing` 卡在 ContainerCreating，Pod Events 明确报 `hostPath type check failed: ... is not a directory`
2. **g2 (Error / 容器退出码 1)** — 9 个 `node-debugger-node1-*` 调试 Pod 执行 `ls` 命令时因找不到同一目录而退出，Exit Code=1

Pod 标签 `rootcause-e2e=true` 提示这是一个故障注入 e2e 测试场景，与上游定位结论一致。
   ✅ [证据链采集] 完成 (24.7s)
   📤 → 下游数据: evidence_items=12/14
   evidence_analysis={"evidence_plan":[{"id":"g1-describe","description":"主异常组g1：aiops-e2e/rc-volume-hostpath-missing - kubectl describe 验证 MountVolume.SetUp failed 事件原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-hostpath-missing -n aiops-e2e","tool_args":{"kind":"pod","name":"rc-volume-hostpath-missing","namespace":"aiops-e2e","resource_type":"pod"},"purpose":"验证上游已捕获的 FailedMount 事件仍存在，确认 hostPath 路径不存在的根因","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-yaml","description":"主异常组g1：aiops-e2e/rc-volume-hostpath-missing - 获取 Pod YAML 确认 volumes 中 hostPath 引用","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o yaml","tool_args":{"kind":"pod","name":"rc-volume-hostpath-missing","namespace":"aiops-e2e","resource_type":"pod"},"purpose":"验证.spec.volumes[].hostPath.path 指向 /tmp/aiops-rootcause-definitely-missing-hostpath-dir","evidence_type":"","target_scope":"","acceptable_tools":["kubectl_get_yaml","run_bash_command"],"counts_for_completeness":true},{"id":"g1-events","description":"主异常组g1：aiops-e2e/rc-volume-hostpath-missing - 获取命名空间事件确认 FailedMount 详情","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-hostpath-missing --sort-by='.lastTimestamp'","tool_args":{"namespace":"aiops-e2e","field_selector":"involvedObject.name=rc-volume-hostpath-missing","sort_by":".lastTimestamp"},"purpose":"确认 FailedMount 事件的完整时序和次数","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-runbook","description":"主异常组g1：获取已确认的 pod-volume-mount-failed runbook 作为参考","level":"reference","tool":"fetch_runbook","command":"fetch_runbook pod-volume-mount-failed.md","tool_args":{"runbook_name":"pod-volume-mount-failed.md"},"purpose":"runbook参考，不作为真实环境证据","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g1-node-check","description":"主异常组g1：验证 node1 上 hostPath 目录是否存在","level":"critical","tool":"run_bash_command","command":"kubectl debug node/node1 -it --image=busybox:1.36 -- ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir 2>&1 || echo 'DIRECTORY_NOT_FOUND'","tool_args":{},"purpose":"直接验证缺失目录在 node1 上是否真实存在","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-minimal","description":"次异常组g2：验证 mcp/node-debugger-node1-* 最小状态 - 选一个代表 Pod describe 确认 Error/exit code 1 因缺失目录","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-jt75t -n mcp","tool_args":{"kind":"pod","name":"node-debugger-node1-jt75t","namespace":"mcp","resource_type":"pod"},"purpose":"验证代表Pod的Error状态、exit code、command是否指向缺失hostpath目录","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-event-check","description":"次异常组g2：验证 mcp 命名空间事件确认 node-debugger 相关事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n mcp --field-selector involvedObject.name=node-debugger-node1-jt75t --sort-by='.lastTimestamp'","tool_args":{"namespace":"mcp","field_selector":"involvedObject.name=node-debugger-node1-jt75t","sort_by":".lastTimestamp"},"purpose":"确认该Pod的Events与Error根因","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true},{"id":"g2-logs","description":"次异常组g2：验证 node-debugger 代表Pod日志确认错误输出","level":"important","tool":"kubectl_logs","command":"kubectl logs node-debugger-node1-jt75t -n mcp","tool_args":{"name":"node-debugger-node1-jt75t","namespace":"mcp"},"purpose":"确认Pod日志输出为 ls: cannot access... 目录不存在的错误","evidence_type":"","target_scope":"","acceptable_tools":[],"counts_for_completeness":true}],"tool_results":[],"tool_data":[{"tool":"fetch_runbook","data":"<runbook>\n# Pod VolumeMountFailed / 卷挂载失败\n\n> Pod异常类型: VolumeMountFailed | 典型状态: Pending / ContainerCreating | 兼容分类: storage_volume\n\n## 使用原则（给模型）\n- Runbook 是诊断 guide，不是要求把所有分支都查完的 checklist。\n- `kubectl describe pod` / `kubectl get events` 中的 Events 原文权重最高；先读事件原文，再按关键字选择一个最相关分支。\n- 一旦 Events 或 Pod spec 已明确命中某个分支，应停止横向扩展到无关 PVC/PV/StorageClass/CSI/NFS 分支。\n- 证据计划优先覆盖“当前已经出现的错误文本”，不要把典型原因列表全部变成 evidence_plan。\n\n## 状态识别\n- Pod 常见状态: `Pending` / `ContainerCreating`\n- Events 关键字: `FailedMount` / `FailedAttachVolume` / `MountVolume.SetUp failed`\n- 相关资源: PVC / PV / StorageClass / CSI / NFS / Secret / ConfigMap volume\n\n## 典型原因\n- PVC 未 Bound、StorageClass 不存在、PV nodeAffinity 不匹配。\n- PV/PVC 访问模式不满足，例如 RWO 被多个节点挂载、Multi-Attach error。\n- CSI/NFS/iSCSI 后端不可用、权限拒绝、挂载超时、stale file handle。\n- Secret/ConfigMap 类型的 volume 引用了不存在的对象或 key。\n- hostPath 路径不存在、类型不匹配或节点权限不足。\n- 云盘或块存储与节点可用区/实例规格不匹配，例如 volume node affinity conflict、InvalidInstanceType.NotSupportDiskCategory。\n\n## 证据优先级\n1. 最高优先级: `kubectl describe pod <pod> -n <namespace>` 或 `kubectl get events ...`，读取 Events 原文。\n2. 最高优先级: `kubectl get pod <pod> -n <namespace> -o yaml`，确认 `.spec.volumes[]` 引用的是 PVC、ConfigMap、Secret、hostPath 还是 CSI。\n3. 分支证据: 只查询 Events 原文指向的资源类型。\n\n## 分支诊断流程\n\n### Step 1: 先读 Pod Events 原文（必须优先）\n```bash\nkubectl describe pod <pod-name> -n <namespace>\nkubectl get events -n <namespace> --field-selector involvedObject.name=<pod-name> --sort-by='.lastTimestamp'\n```\n如果已看到 `configmap \"<name>\" not found`、`secret \"<name>\" not found`、`unbound immediate PersistentVolumeClaims`、`volume node affinity conflict`、`Multi-Attach error`、`NFS timeout/access denied`，直接进入对应分支。\n\n### Step 2: 读取 Pod spec 中的 volume 引用（必须优先）\n```bash\nkubectl get pod <pod-name> -n <namespace> -o yaml\n```\n关注 `.spec.volumes[]`:\n- `configMap.name` / `secret.secretName`: 进入 ConfigMap/Secret 分支。\n- `persistentVolumeClaim.claimName`: 进入 PVC/PV/StorageClass 分支。\n- `hostPath`: 进入 hostPath/节点路径分支。\n- `csi` / NFS 相关字段: 进入 CSI/NFS 分支。\n\n### Step 3A: ConfigMap/Secret volume 缺失分支\n触发条件: Events 含 `configmap \"<name>\" not found`、`secret \"<name>\" not found`，且 Pod spec 中来自 `volumes[].configMap` 或 `volumes[].secret`。\n```bash\nkubectl get configmap <name> -n <namespace>\nkubectl get secret <name> -n <namespace>\n```\n预期证据: `Error from server (NotFound)` 本身就是有效根因证据。此时不要再查 PVC、PV、StorageClass，除非 Pod spec 同时存在 PVC volume 且 Events 指向 PVC。\n\n### Step 3B: PVC/PV/StorageClass 分支\n触发条件: Events 含 `unbound immediate PersistentVolumeClaims`、`pod has unbound`、`persistentvolumeclaim ... not found`，或 Pod spec 明确使用 `persistentVolumeClaim.claimName`。\n```bash\nkubectl get pvc <pvc-name> -n <namespace>\nkubectl describe pvc <pvc-name> -n <namespace>\nkubectl get pv\nkubectl get storageclass\n```\n只有 PVC Pending/NotFound/ProvisioningFailed 时，才继续检查 PV 和 StorageClass。\n\n### Step 3C: Attach/NodeAffinity/Multi-Attach 分支\n触发条件: Events 含 `FailedAttachVolume`、`Multi-Attach error`、`volume node affinity conflict`。\n```bash\nkubectl describe pod <pod-name> -n <namespace>\nkubectl describe pv <pv-name>\nkubectl get pod <pod-name> -n <namespace> -o wide\n```\n\n### Step 3D: CSI/NFS/hostPath 分支\n触发条件: Events 含 `timeout`、`access denied`、`stale file handle`、`hostPath type check failed`、CSI driver 错误。\n```bash\nkubectl get pods -n kube-system -o wide\nkubectl describe node <node-name>\n```\n\n## 判定规则\n| 条件 | 结论 | 置信度 |\n|------|------|--------|\n| Events 含 Secret/ConfigMap not found + Pod spec 来自 volumes[].secret/configMap | volume 引用的 ConfigMap/Secret 缺失 | 高 |\n| FailedMount/MountVolume + PVC 未 Bound | VolumeMountFailed | 高 |\n| FailedScheduling + unbound immediate PersistentVolumeClaims | PVC 未绑定导致 Pending，归入 VolumeMountFailed/PVC 分支 | 高 |\n| Multi-Attach error + ReadWriteOnce | 卷访问模式与调度节点冲突 | 高 |\n| PV nodeAffinity conflict | PV 节点亲和性与 Pod 调度节点不匹配 | 高 |\n| volume node affinity conflict / node(s) had volume node affinity conflict | PV/云盘可用区与调度节点不匹配 | 高 |\n| InvalidInstanceType.NotSupportDiskCategory | 云盘类型不支持当前节点实例规格 | 高 |\n| NFS timeout/access denied/stale file handle | VolumeMountFailed | 高 |\n| Secret/ConfigMap not found 且来自 volume 引用 | VolumeMountFailed；若来自 env/envFrom 则切换 ConfigError；不要再扩展 PVC 分支 | 高 |\n| hostPath path/type error | 节点路径或 hostPath 类型配置错误 | 高 |\n\n</runbook>\nNote: the above runbook is for DIAGNOSTIC REFERENCE ONLY. Follow the DIAGNOSTIC steps to gather evidence using tools, but DO NOT execute any remediation/fix commands. Report your findings and suggest fixes in your analysis.","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/001-evidence-fetch_runbook.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/001-evidence-fetch_runbook.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/001-evidence-fetch_runbook.summary.txt"},{"tool":"kubectl_get_yaml","data":"kubectl_get_yaml 关键字段摘要:\nkind: Pod\nname: rc-volume-hostpath-missing\nnamespace: aiops-e2e\ncreationTimestamp: 2026-05-21T05:24:07Z\ndeletionTimestamp: <absent>\ndeletionGracePeriodSeconds: None\nfinalizers: <none>\nserviceAccountName: default\nnodeName: node1\nrestartPolicy: Always\nterminationGracePeriodSeconds: 30\nimagePullSecrets: <absent>\nphase: Pending\nlabels: app=rc-volume-hostpath-missing, pod_abnormal_type=VolumeMountFailed\ndiagnostic_annotations: aiops.e2e/runbook=pod-volume-mount-failed.md\ntolerations_count: 2\ncontainers:\n- app: image=busybox:1.36 imagePullPolicy=Never\n  command: sh -c sleep 3600\nconditions:\n- Initialized: status=True reason=None\n- Ready: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- ContainersReady: status=False reason=ContainersNotReady message=containers with unready status: [app]\n- PodScheduled: status=True reason=None\ncontainerStatuses:\n- app: ready=False restarts=0 reason=ContainerCreating exitCode=None\nvolumes:\n- {\"name\": \"missing-hostpath\"}\n- {\"name\": \"kube-api-access-m54dz\"}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/002-evidence-kubectl_get_yaml.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/002-evidence-kubectl_get_yaml.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/002-evidence-kubectl_get_yaml.summary.txt"},{"tool":"kubectl_logs","data":"kubectl_logs 日志摘要:\nlines: 1\nsignals: 1\n关键日志:\nls: /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/003-evidence-kubectl_logs.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/003-evidence-kubectl_logs.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/003-evidence-kubectl_logs.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: rc-volume-hostpath-missing\nnamespace: aiops-e2e\nnode: node1/10.2.0.49\nstatus: Pending\n关键诊断行:\n  Warning  FailedMount  3m26s (x23 over 34m)  kubelet            MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory\n  Warning  FailedMount  11m (x10 over 32m)    kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-hostpath], unattached volumes=[missing-hostpath kube-api-access-m54dz]: timed out waiting for the condition\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: node.kubernetes.io/not-ready:NoExecute op=Exists for 300s\nContainers:\n  app:\n    Container ID:\n    Image:         busybox:1.36\n    Image ID:\n    Command:\n      sh\n      -c\n      sleep 3600\n    State:          Waiting\n      Reason:       ContainerCreating\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  missing-hostpath:\n    Type:          HostPath (bare host directory volume)\n    Path:          /tmp/aiops-rootcause-definitely-missing-hostpath-dir\n  kube-api-access-m54dz:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Warning  FailedMount  11m (x10 over 32m)    kubelet            Unable to attach or mount volumes: unmounted volumes=[missing-hostpath], unattached volumes=[missing-hostpath kube-api-access-m54dz]: timed out waiting for the condition\n  Warning  FailedMount  3m26s (x23 over 34m)  kubelet            MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory\n关键状态/事件:\n                  pod_abnormal_type=VolumeMountFailed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/004-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/004-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/004-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_describe","data":"kubectl_describe 摘要:\nname: node-debugger-node1-jt75t\nnamespace: mcp\nnode: node1/10.2.0.49\nstatus: Failed\nPod 关键区块:\nQoS Class: BestEffort\nNode-Selectors: <none>\nTolerations: op=Exists\nContainers:\n  debugger:\n    Container ID:  containerd://0caa984756abd59ba6cd7dabf4ae46eca41c309df1ec063b8be88703fa8d2052\n    Image:         busybox:1.36\n    Image ID:      sha256:114f4abb67995cfe8e368760f3bc8a1d00e12ac9883c7c304d80987f24452e75\n    Command:\n      ls\n      -la\n      /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir\n    State:          Terminated\n      Reason:       Error\n      Exit Code:    1\n      Started:      Thu, 21 May 2026 05:26:21 +0000\n      Finished:     Thu, 21 May 2026 05:26:21 +0000\n    Ready:          False\n    Restart Count:  0\n    Environment:    <none>\n    Mounts:\nVolumes:\n  host-root:\n    Type:          HostPath (bare host directory volume)\n    Path:          /\n  kube-api-access-4b9jh:\n    Type:                    Projected (a volume that contains injected data from multiple sources)\n    ConfigMapName:           kube-root-ca.crt\nEvents:\n  Type    Reason   Age   From     Message\n  ----    ------   ----  ----     -------\n  Normal  Pulled   31m   kubelet  Container image \"busybox:1.36\" already present on machine\n  Normal  Created  31m   kubelet  Created container debugger\n  Normal  Started  31m   kubelet  Started container debugger\n关键状态/事件:\nStatus:           Failed","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/005-evidence-kubectl_describe.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/005-evidence-kubectl_describe.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/005-evidence-kubectl_describe.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\n关键诊断行:\n3m27s (x23 over 34m)   Warning   FailedMount   Pod/rc-volume-hostpath-missing   MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory\n11m (x10 over 32m)     Warning   FailedMount   Pod/rc-volume-hostpath-missing   Unable to attach or mount volumes: unmounted volumes=[missing-hostpath], unattached volumes=[missing-hostpath kube-api-access-m54dz]: timed out waiting for the condition","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/006-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/006-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/006-evidence-kubectl_events.summary.txt"},{"tool":"kubectl_events","data":"kubectl_events 摘要:\nLAST SEEN   TYPE     REASON    OBJECT                          MESSAGE\n31m         Normal   Pulled    Pod/node-debugger-node1-jt75t   Container image \"busybox:1.36\" already present on machine\n31m         Normal   Created   Pod/node-debugger-node1-jt75t   Created container debugger\n31m         Normal   Started   Pod/node-debugger-node1-jt75t   Started container debugger","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/007-evidence-kubectl_events.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/007-evidence-kubectl_events.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/007-evidence-kubectl_events.summary.txt"},{"tool":"run_bash_command","data":"{\"success\": true, \"stdout\": \"Creating debugging pod node-debugger-node1-6mxrg with container debugger on node node1.\\nls: /tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory\\n\", \"stderr\": \"\", \"returncode\": 0}","duration_s":0,"semantic_success":true,"raw_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/008-evidence-run_bash_command.raw.txt","structured_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/008-evidence-run_bash_command.structured.json","summary_ref":"/tmp/aiops/reports/context_archives/b87447a193d541fe/tools/008-evidence-run_bash_command.summary.txt"}],"llm_analysis":"## 证据采集完成——结论报告\n\n### ✅ 已采集证据（主异常组 g1：rc-volume-hostpath-missing）\n\n| 证据项 | 结果 |\n|--------|------|\n| **g1-describe** (Pod Events) | ✅ **已确认** — `MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory`，已发生 23 次 |\n| **g1-yaml** (Pod spec volumes) | ✅ **已确认** — `.spec.volumes[0].hostPath.path = /tmp/aiops-rootcause-definitely-missing-hostpath-dir`，类型为 HostPath |\n| **g1-events** (Events 完整时序) | ✅ **已确认** — FailedMount 事件 x23 持续 34 分钟，最早事件 34m 前开始 |\n| **g1-node-check** (目录存在性) | ✅ **已确认** — `ls: /tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory`，目录在 node1 上真实不存在 |\n\n### ✅ 已采集证据（非主异常组 g2：node-debugger-node1-*）\n\n| 证据项 | 结果 |\n|--------|------|\n| **g2-minimal** (代表 Pod describe) | ✅ **已确认** — Exit Code=1, Reason=Error, 容器命令 `ls -la /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 执行失败 |\n| **g2-event-check** (Events) | ✅ **已确认** — 只有 Pulled/Created/Started 正常事件，无异常事件，说明容器正常启动但执行命令因目录缺失退出 |\n| **g2-logs** (日志) | ✅ **已确认** — `ls: /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory` |\n\n### 根因结论\n\n**node1 节点上的 HostPath 目录 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 不存在**，导致：\n\n1. **g1 (VolumeMountFailed / L0)** — `rc-volume-hostpath-missing` 卡在 ContainerCreating，Pod Events 明确报 `hostPath type check failed: ... is not a directory`\n2. **g2 (Error / 容器退出码 1)** — 9 个 `node-debugger-node1-*` 调试 Pod 执行 `ls` 命令时因找不到同一目录而退出，Exit Code=1\n\nPod 标签 `rootcause-e2e=true` 提示这是一个故障注入 e2e 测试场景，与上游定位结论一致。","collection_summary":"计划 7 项，实际采集 5 项，未采集 2 项，完整度 71%；其中真实环境证据 11/13 项，完整度 85%；实际执行工具 13 个，匹配计划 6 个，未规划证据 7 个","plan_total":7,"plan_collected":5,"plan_completeness":0.7142857142857143,"environment_evidence_total":13,"environment_evidence_collected":11,"environment_evidence_completeness":0.8461538461538461,"executed_tool_count":13,"matched_tool_count":6,"unplanned_tool_count":7,"evidence_inventory":[{"id":"g1-describe","description":"主异常组g1：aiops-e2e/rc-volume-hostpath-missing - kubectl describe 验证 MountVolume.SetUp failed 事件原文","level":"critical","tool":"kubectl_describe","command":"kubectl describe pod rc-volume-hostpath-missing -n aiops-e2e","purpose":"验证上游已捕获的 FailedMount 事件仍存在，确认 hostPath 路径不存在的根因","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-yaml","description":"主异常组g1：aiops-e2e/rc-volume-hostpath-missing - 获取 Pod YAML 确认 volumes 中 hostPath 引用","level":"critical","tool":"kubectl_get_yaml","command":"kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o yaml","purpose":"验证.spec.volumes[].hostPath.path 指向 /tmp/aiops-rootcause-definitely-missing-hostpath-dir","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-events","description":"主异常组g1：aiops-e2e/rc-volume-hostpath-missing - 获取命名空间事件确认 FailedMount 详情","level":"important","tool":"kubectl_events","command":"kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volume-hostpath-missing --sort-by='.lastTimestamp'","purpose":"确认 FailedMount 事件的完整时序和次数","collected":false,"source":"planned","outcome":"unknown"},{"id":"g1-runbook","description":"主异常组g1：获取已确认的 pod-volume-mount-failed runbook 作为参考","level":"optional","tool":"fetch_runbook","command":"fetch_runbook pod-volume-mount-failed.md","purpose":"runbook参考，不作为真实环境证据","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g1-node-check","description":"主异常组g1：验证 node1 上 hostPath 目录是否存在","level":"critical","tool":"run_bash_command","command":"kubectl debug node/node1 -it --image=busybox:1.36 -- ls -la /tmp/aiops-rootcause-definitely-missing-hostpath-dir 2>&1 || echo 'DIRECTORY_NOT_FOUND'","purpose":"直接验证缺失目录在 node1 上是否真实存在","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-minimal","description":"次异常组g2：验证 mcp/node-debugger-node1-* 最小状态 - 选一个代表 Pod describe 确认 Error/exit code 1 因缺失目录","level":"important","tool":"kubectl_describe","command":"kubectl describe pod node-debugger-node1-jt75t -n mcp","purpose":"验证代表Pod的Error状态、exit code、command是否指向缺失hostpath目录","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"g2-event-check","description":"次异常组g2：验证 mcp 命名空间事件确认 node-debugger 相关事件","level":"important","tool":"kubectl_events","command":"kubectl get events -n mcp --field-selector involvedObject.name=node-debugger-node1-jt75t --sort-by='.lastTimestamp'","purpose":"确认该Pod的Events与Error根因","collected":false,"source":"planned","outcome":"unknown"},{"id":"g2-logs","description":"次异常组g2：验证 node-debugger 代表Pod日志确认错误输出","level":"important","tool":"kubectl_logs","command":"kubectl logs node-debugger-node1-jt75t -n mcp","purpose":"确认Pod日志输出为 ls: cannot access... 目录不存在的错误","collected":true,"source":"thinking_match","outcome":"positive"},{"id":"layer_1","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_2","description":"上游已验证工具结果: kubectl_get_by_name","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_3","description":"上游已验证工具结果: kubectl_get_by_kind_in_cluster","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_4","description":"上游已验证工具结果: kubectl_get_by_kind_in_namespace","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"},{"id":"layer_5","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"negative"},{"id":"layer_6","description":"上游已验证工具结果: kubectl_describe","level":"important","tool":"","command":"","purpose":"","collected":true,"source":"layer_verified","outcome":"positive"}],"missing_reasons":["g1-events(主异常组g1：aiops-e2e/rc-volume-hostpath-missing - 获取命名空间事件确认 FailedMount 详情): 已规划但工具执行失败或无匹配结果","g2-event-check(次异常组g2：验证 mcp 命名空间事件确认 node-debugger 相关事件): 已规划但工具执行失败或无匹配结果"],"early_stop":{"triggered":false,"reason":"","required_levels":["critical","important"]}}

   ┌──────────────────────────────────────────┐
   │ 🔍 证据采集结果                              │
   └──────────────────────────────────────────┘

   证据: 5/7 项, 完整度: 85%

   📋 证据采集计划
   | ID | 级别 | 状态 | 工具 | 采集目标 | 命令 |
   |----|------|------|------|----------|------|
   | g1-describe | critical | ✅ | kubectl_describe | 主异常组g1：aiops-e2e/rc-volume-hostpath-missing -... | `kubectl describe pod rc-volume-hostpath-missing -n aiops-e2e` |
   | g1-yaml | critical | ✅ | kubectl_get_yaml | 主异常组g1：aiops-e2e/rc-volume-hostpath-missing -... | `kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -o yaml` |
   | g1-events | important | ❌ | kubectl_events | 主异常组g1：aiops-e2e/rc-volume-hostpath-missing -... | `kubectl get events -n aiops-e2e --field-selector involvedObject.name=rc-volum...` |
   | g1-runbook | reference | ✅ | fetch_runbook | 主异常组g1：获取已确认的 pod-volume-mount-failed runbook... | `fetch_runbook pod-volume-mount-failed.md` |
   | g1-node-check | critical | ✅ | run_bash_command | 主异常组g1：验证 node1 上 hostPath 目录是否存在 | `kubectl debug node/node1 -it --image=busybox:1.36 -- ls -la /tmp/aiops-rootca...` |
   | g2-minimal | important | ✅ | kubectl_describe | 次异常组g2：验证 mcp/node-debugger-node1-* 最小状态 - 选一... | `kubectl describe pod node-debugger-node1-jt75t -n mcp` |
   | g2-event-check | important | ❌ | kubectl_events | 次异常组g2：验证 mcp 命名空间事件确认 node-debugger 相关事件 | `kubectl get events -n mcp --field-selector involvedObject.name=node-debugger-...` |
   | g2-logs | important | ✅ | kubectl_logs | 次异常组g2：验证 node-debugger 代表Pod日志确认错误输出 | `kubectl logs node-debugger-node1-jt75t -n mcp` |

   ⚠️ 未采集原因:
   - g1-events(主异常组g1：aiops-e2e/rc-volume-hostpath-missing - 获取命名空间事件确认 FailedMount 详情): 已规划但工具执行失败或无匹配结果
   - g2-event-check(次异常组g2：验证 mcp 命名空间事件确认 node-debugger 相关事件): 已规划但工具执行失败或无匹配结果

📍 [根因分析] 执行中...
   ⏳ [证据链采集] 仍在处理，等待工具或模型返回...
   ✅ [根因分析] 完成 (26.0s)
   📤 → 下游数据: root_cause=根因是node1节点上的HostPath目录 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 缺失。(1) 主异常组g1（aiops-e2e/rc-volume-hostpath-missing）：Pod spec中定义了HostPath卷指向该目录，kubectl describe显示事件"MountVolume.SetUp failed for volume 'missing-hostpath' : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory"，持续34分钟内已重试23次失败，Pod状态ContainerCreating不可恢复。(2) 次异常组g2（mcp/node-debugger-node1-*共9个Pod）：每个Pod容器执行"ls -la /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir"因目录不
... 截断，原始 633 字符
   confidence=100%
   causal_chain={"root_cause": "node1节点上HostPath目录 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不存在（被删除或从未创建）", "propagation": "该目录被两个独立工作负载引用：(1) aiops-e2e/rc-volume-hostpath-missing的volume定义引用了该目录作为HostPath卷；(2) mcp命名空间中9个node-debugger-node1-*调试Pod的容器命令直接ls该路径。两个工作负载共用同一节点node1", "direct_cause": "g1: kubelet挂载hostPath卷时因目标目录不存在返回hostPath type check failed，Pod无法进入Running状态；g2: 容器启动后执行ls命令因目录不存在返回exit code 1导致容器终止", "manifestation": "1个Pod持续ContainerCreating（VolumeMountFailed），9个Pod持续Error状态（容器退出码1），均集中在node1节点"}
   rca_analysis={"phenomenon": "集群中10个异常Pod，分布在2个异常组：主异常组g1（aiops-e2e/rc-volume-hostpath-missing 状态 ContainerCreating，pod_abnormal_type=VolumeMountFailed）和次异常组g2（mcp/node-debugger-node1-* 共9个Pod状态 Error，exit code 1），全部位于node1节点", "evidence_inventory": [{"id": "e1", "source": "kubectl_describe - g1 Pod", "content": "rc-volume-hostpath-missing Events: MountVolume.SetUp failed - hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory", "reliability": "高"}, {"id": "e2", "source": "kubectl_get_yaml - g1 Pod", "content": "volumes[0].hostPath.path = /tmp/aiops-rootcause-definitely-missing-hostpath-dir，类型HostPath", "reliability": "高"}, {"id": "e3", "source": "kubectl_events - g1", "content": "FailedMount x23 over 34m，最早34m前开始，持续重试中", "reliability": "高"}, {"id": "e4", "source": "run_bash_command - node1目录检查", "content": "调试Pod在node1上执行ls: No such file or directory，目录真实缺失", "reliability": "高"}, {"id": "e5", "source": "kubectl_describe - g2代表Pod", "content": "node-debugger-node1-jt75t Exit Code=1, Reason=Error, 容器命令: ls -la /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir", "reliability": "高"}, {"id": "e6", "source": "kubectl_logs - g2代表Pod", "content": "日志输出: ls: /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory", "reliability": "高"}, {"id": "e7", "source": "kubectl_events - g2代表Pod", "content": "仅Pulled/Created/Started正常事件，容器正常启动但命令执行失败退出", "reliability": "高"}, {"id": "e8", "source": "kubectl_get_by_kind_in_cluster", "content": "75个Pod中10个异常(9 Error + 1 ContainerCreating)，其余59 Running正常", "reliability": "高"}, {"id": "e9", "source": "kubectl_get_by_kind_in_cluster - Nodes", "content": "3节点均Ready，master/node1/node2正常", "reliability": "高"}], "evidence_analysis": [{"evidence_id": "e1", "raw_data": "MountVolume.SetUp failed for volume \"missing-hostpath\" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory", "interpretation": "Pod rc-volume-hostpath-missing 的hostPath卷挂载失败，kubelet明确报告目标路径不是目录（即不存在），这是该Pod卡在ContainerCreating的直接原因"}, {"evidence_id": "e2", "raw_data": "volumes[0]: name=missing-hostpath, Type=HostPath, Path=/tmp/aiops-rootcause-definitely-missing-hostpath-dir", "interpretation": "Pod spec中定义的volume是HostPath类型，路径指向node1上的/tmp/aiops-rootcause-definitely-missing-hostpath-dir，与事件一致"}, {"evidence_id": "e3", "raw_data": "Warning FailedMount 3m27s (x23 over 34m) - MountVolume.SetUp failed", "interpretation": "该错误持续发生34分钟，已重试23次，表明kubelet持续尝试挂载但一直失败，不是临时问题"}, {"evidence_id": "e4", "raw_data": "ls: /tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory", "interpretation": "通过调试Pod在node1节点上直接验证，确认该目录确实不存在，排除了容器视角和节点视角的差异"}, {"evidence_id": "e5", "raw_data": "Command: ls -la /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir, State: Terminated, Reason: Error, Exit Code: 1", "interpretation": "g2组调试Pod的容器命令为列出该目录内容，因目录缺失返回exit code 1，所有9个Pod同理失败"}, {"evidence_id": "e6", "raw_data": "ls: /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory", "interpretation": "日志确认g2组容器执行ls命令时找不到同一目录，印证了退出原因"}, {"evidence_id": "e7", "raw_data": "Normal Pulled → Normal Created → Normal Started，无Warning/Error事件", "interpretation": "g2组容器成功拉取镜像、创建、启动，说明容器运行时正常，异常仅因业务命令（ls）依赖缺失目录而失败"}, {"evidence_id": "e8", "raw_data": "status_counts: Running=59, Error=9, ContainerCreating=1", "interpretation": "集群75个Pod中仅这10个异常，其余正常运行，问题范围局限于node1节点上依赖同一缺失目录的Pod"}, {"evidence_id": "e9", "raw_data": "3 nodes all Ready", "interpretation": "集群节点健康，无节点级故障，排除节点不可用导致Pod异常的可能性"}], "causal_chain": {"root_cause": "node1节点上HostPath目录 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不存在（被删除或从未创建）", "propagation": "该目录被两个独立工作负载引用：(1) aiops-e2e/rc-volume-hostpath-missing的volume定义引用了该目录作为HostPath卷；(2) mcp命名空间中9个node-debugger-node1-*调试Pod的容器命令直接ls该路径。两个工作负载共用同一节点node1", "direct_cause": "g1: kubelet挂载hostPath卷时因目标目录不存在返回hostPath type check failed，Pod无法进入Running状态；g2: 容器启动后执行ls命令因目录不存在返回exit code 1导致容器终止", "manifestation": "1个Pod持续ContainerCreating（VolumeMountFailed），9个Pod持续Error状态（容器退出码1），均集中在node1节点"}, "root_cause": "根因是node1节点上的HostPath目录 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 缺失。(1) 主异常组g1（aiops-e2e/rc-volume-hostpath-missing）：Pod spec中定义了HostPath卷指向该目录，kubectl describe显示事件\"MountVolume.SetUp failed for volume 'missing-hostpath' : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory\"，持续34分钟内已重试23次失败，Pod状态ContainerCreating不可恢复。(2) 次异常组g2（mcp/node-debugger-node1-*共9个Pod）：每个Pod容器执行\"ls -la /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir\"因目录不\n... 截断，原始 633 字符", "root_cause_summary": "根因是node1节点上的HostPath目录 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 缺失。(1) 主异常组g1（aiops-e2e/rc-volume-hostpath-missing）：Pod spec中定义了HostPath卷指向该目录，kubectl describe显示事件\"MountVolume.SetUp failed for volume 'missing-hostpath' : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory\"，持续34分钟内已重试23次失败，Pod状态ContainerCreating不可恢复。(2) 次异常组g2（mcp/node-debugger-node1-*共9个Pod）：每个Pod容器执行\"ls -la /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir\"因目录不\n... 截断，原始 633 字符", "confidence": 1.0, "confidence_reason": "所有关键证据链完整闭合：(1) Pod Events直接报错原文明确指向目录缺失，(2) Pod YAML确认volume配置路径与错误一致，(3) 通过调试Pod在node1上直接验证目录不存在，(4) g2组Pod日志和描述也指向同一目录缺失，(5) 集群节点健康无其他异常。证据充分且交叉验证一致，置信度达到最高", "primary_runbooks": ["pod-volume-mount-failed.md"], "alternative_causes": [{"cause": "节点node1文件系统故障或权限问题", "probability": "low", "reason": "通过调试Pod成功在node1上执行ls命令，说明节点文件系统和容器运行时正常，容器可正常读写其他路径"}, {"cause": "Pod调度到错误节点", "probability": "low", "reason": "Pod YAML明确指定nodeName=node1，且Pod标签rootcause-e2e=true表明该目录应在node1上存在，非调度错误"}, {"cause": "容器镜像拉取失败", "probability": "low", "reason": "g2组Events显示Pulled/Created/Started均正常，且busybox:1.36已存在于node1；g1组imagePullPolicy=Never但未报ImagePullBackOff"}, {"cause": "Kubernetes版本兼容性问题", "probability": "low", "reason": "集群v1.26.8正常运行59个Pod，3节点均Ready，HostPath是基础volume类型无版本兼容问题"}], "limitations": "缺失证据g1-events（命名空间完整事件时序）虽未单独采集，但kubectl describe已包含全部关键FailedMount事件（x23 over 34m），不影响根因判断。g2-event-check（mcp命名空间事件）也由kubectl describe替代覆盖。未采集该目录原本何时被删除或创建的历史信息，但根因结论不受影响——目录当前确实不存在是已确认事实。", "llm_raw_analysis": "## 证据清点\n共采集9项关键证据，覆盖两个异常组全部10个Pod。\n\n## 逐条分析\n- **e1/e2/e3**：g1组Pod Events明确报错hostPath type check failed，YAML确认volume路径，事件持续34分钟23次重试——证据链完整\n- **e4**：直接通过调试Pod在node1上验证目录不存在——最直接的根因证据\n- **e5/e6/e7**：g2组代表Pod的describe显示exit code 1、日志输出\"No such file or directory\"、Events仅正常事件——说明容器运行时无问题，仅因命令依赖缺失目录失败\n- **e8/e9**：集群整体健康，59个Pod正常运行，3节点Ready——问题范围精确锁定在node1上依赖该目录的Pod\n\n## 关联分析\n两个异常组共享同一根因：node1上/tmp/aiops-rootcause-definitely-missing-hostpath-dir缺失。g1通过HostPath volume挂载失败表现（VolumeMountFailed），g2通过容器命令执行失\n... 截断，原始 736 字符"}

   ┌──────────────────────────────────────────┐
   │ 🎯 根因分析结果                              │
   └──────────────────────────────────────────┘

   根因: 根因是node1节点上的HostPath目录 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 缺失。(1) 主异常组g1（aiops-e2e/rc-volume-hostpath-missing）：Pod spec中定义了HostPath卷指...
   置信度: 100%
   🔗 因果链:
     根本原因: node1节点上HostPath目录 /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不存在（被删除或从未创建）
     传导机制: 该目录被两个独立工作负载引用：(1) aiops-e2e/rc-volume-hostpath-missing的volume定义引用了该目录作为HostPath卷；(2) mcp命名空间中9个node-debugger-node1-*调试Pod的容器命令直接ls该路径。两个工作负载共用同一节点node1
     最终表现: 1个Pod持续ContainerCreating（VolumeMountFailed），9个Pod持续Error状态（容器退出码1），均集中在node1节点


📍 [汇总总结] 执行中...
   ⏳ [汇总总结] 仍在处理，等待工具或模型返回...
   ✅ [汇总总结] 完成 (21.6s)

   ┌──────────────────────────────────────────┐
   │ 📋 汇总总结结果                              │
   └──────────────────────────────────────────┘

   报告长度: 6477 字符

----------------------------------------------------------------------
📊 诊断完成! 总耗时: 1m 44.1s
----------------------------------------------------------------------

======================================================================
🎯 诊断报告
======================================================================

## 📋 节点四：汇总总结
----------------------------------------------------------------------
好的，请查收详细的集群诊断报告。

---
## 📊 诊断概览

**直接回答：您的集群当前存在 10 个异常 Pod，根本原因是 `node1` 节点上关键目录 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 缺失。**

| 项目 | 内容 |
|------|------|
| **Pod异常状态** | `ContainerCreating_Error` / `VolumeMountFailed` |
| **兼容归因层** | L0_L2 - 存储卷挂载 + 容器运行时异常 |
| **问题分类** | `storage_volume` / `VolumeMountFailed` |
| **置信度** | **高 (100%)** |
| **证据完整度** | 5/7 (71%) |
---
## 🔍 现象描述

**用户报告**：
> 我的集群有什么问题

**问题总结**：
集群中存在两个问题组，共涉及 **10 个异常 Pod**，全部运行在 **`node1`** 节点上：
1.  **aiops-e2e 命名空间**: 1 个 Pod (`rc-volume-hostpath-missing`) 处于 `ContainerCreating` 状态，无法启动。
2.  **mcp 命名空间**: 9 个 `node-debugger-node1-*` Pod 处于 `Error` 状态，已终止。

**关键实体**：
| 类型 | 值 |
|------|-----|
| 异常节点 | `node1` (10.2.0.49) |
| 异常 Pod (g1) | `rc-volume-hostpath-missing` (aiops-e2e 命名空间) |
| 异常 Pod (g2) | `node-debugger-node1-497sq` 等 9 个 (mcp 命名空间) |
| 缺失路径 | `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` |

---
## 🕵️ 证据链

### 已采集证据

| # | 证据类型 | 来源命令 | 原始数据 | 分析结论 |
|---|----------|----------|----------|----------|
| 1 | Pod 状态 | `kubectl get pod -A` | `[g1] rc-volume-hostpath-missing` 状态: `ContainerCreating` <br>`[g2] node-debugger-node1-*` 9 个 Pod 状态: `Error` | 集群存在 10 个异常 Pod，分属两种异常模式。 |
| 2 | Pod 事件 (g1) | `kubectl describe pod -n aiops-e2e rc-volume-hostpath-missing` | `Warning FailedMount: MountVolume.SetUp failed for volume "missing-hostpath" : hostPath type check failed: /tmp/aiops-rootcause-definitely-missing-hostpath-dir is not a directory` | g1 Pod 因 HostPath 卷挂载失败而卡在 ContainerCreating。 |
| 3 | Pod YAML (g1) | `kubectl get pod -n aiops-e2e rc-volume-hostpath-missing -o yaml` | `volumes: - name: missing-hostpath hostPath: path: /tmp/aiops-rootcause-definitely-missing-hostpath-dir` | 确认 Pod spec 中明确引用了一个不存在的 HostPath 目录。 |
| 4 | Pod 状态 (g2) | `kubectl describe pod -n mcp node-debugger-node1-jt75t` | `Status: Failed` <br>`State: Terminated, Reason: Error, Exit Code: 1` <br>`Command: ls -la /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir` | g2 调试 Pod 执行 `ls` 命令失败，退出码为 1，直接确认是找不到目标目录.|
| 5 | Pod 日志 (g2) | `kubectl logs -n mcp node-debugger-node1-jt75t` | `ls: /host/tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory` | 日志明确显示该目录不存在。 |
| 6 | 节点验证 | `run_bash_command` (通过调试 Pod) | `ls: /tmp/aiops-rootcause-definitely-missing-hostpath-dir: No such file or directory` | 直接登录 `node1` 验证，确认该目录在节点上确实不存在。 |
| 7 | 集群状态 | `kubectl get nodes` | 所有 3 个节点 (包括 master, node1) 均为 `Ready` 状态。 | 节点健康，排除了节点不可达导致的挂载问题。 |

### 证据关联分析
- **证据 #2 + #3 + #6 + #7 印证**：Pod spec 定义了指向 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 的 HostPath 卷，kubelet 在挂载时发现该目录在 `node1` 上不存在并报错 `hostPath type check failed`。节点本身处于健康状态，排除了节点层面的问题。
- **证据 #4 + #5 + #6 印证**：mcp 命名空间的调试 Pod 就是用来检查该目录的，其 `ls` 命令因目录不存在而直接失败退出 (Exit Code 1)，日志和节点验证结果完全一致。
- **完整证据链**：`node1` 上目录缺失 → g1 Pod 卷挂载失败，卡在 `ContainerCreating` → g2 调试 Pod 执行命令失败，状态变为 `Error`。

### 缺失证据（如有）
| 证据 | 级别 | 影响 |
|------|------|------|
| 命名空间完整事件时序（如 kubectl_events） | low | 未影响根因判定。`kubectl describe` 已提供所有关键的 `FailedMount` 事件。 |
| 该目录被删除的历史信息 | low | 根因是“目录当前不存在”，已确认。不需要知道具体何时被删除。 |

---
## 🎯 根因分析

### 因果链
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 根本原因                                                                    │
│ node1 节点上的 HostPath 目录                                              │
│ /tmp/aiops-rootcause-definitely-missing-hostpath-dir 不存在                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 传导机制                                                                    │
│ 该目录被两个独立的工作负载所引用，它们都调度在 node1 上                    │
└─────────────────────────────────────────────────────────────────────────────┘
                           ↓                                       ↓
┌─────────────────────────────┐         ┌─────────────────────────────────────┐
│ 直接原因 (g1)               │         │ 直接原因 (g2)                       │
│ kubelet 挂载 HostPath 卷    │         │ 容器内 ls 命令找不到目录            │
│ 失败，Pod 无法正常运行。     │         │ 导致容器退出 (Exit Code 1)。        │
└─────────────────────────────┘         └─────────────────────────────────────┘
                           ↓                                       ↓
┌─────────────────────────────┐         ┌─────────────────────────────────────┐
│ 用户可见现象 (g1)           │         │ 用户可见现象 (g2)                   │
│ 1 个 Pod 卡在                │         │ 9 个 Pod 处于 Error 状态。          │
│ ContainerCreating 状态。     │         │                                     │
└─────────────────────────────┘         └─────────────────────────────────────┘
```

### 根因结论
**结论**：根据证据 #2、#3、#4、#5 和 #6，问题的根本原因是 **`node1` 节点上的 HostPath 目录 `/tmp/aiops-rootcause-definitely-missing-hostpath-dir` 不存在**，导致引用了该目录的两个工作负载均出现异常。

**置信度**：高 (100%)
- ✅  `kubectl describe` 直接报错“目录不是”（证据 #2）。
- ✅  Pod spec 明确指向该目录（证据 #3）。
- ✅  调试 Pod 日志输出“无此文件或目录”（证据 #5）。
- ✅  直接在 `node1` 上执行命令确认目录不存在（证据 #6）。
- ✅  Pod 上的标签 `rootcause-e2e=true` 表明这是一个被有意触发的故障测试场景。

---
## 🛠️ 修复建议

### 立即执行（按优先级排序）
**1. [唯一核心修复] 在 node1 上创建缺失目录**
该操作会解决所有 10 个异常 Pod 的问题。
```bash
# 在 node1 节点上执行
mkdir -p /tmp/aiops-rootcause-definitely-missing-hostpath-dir
```
*依据*：根本原因是该目录缺失，创建后 Pod 可自动恢复。

**2. [确认修复] 检查 Pod 状态**
执行以下命令，确认 Pod 是否恢复到 `Running` 状态。
```bash
# 检查 aiops-e2e 的 Pod
kubectl get pod rc-volume-hostpath-missing -n aiops-e2e -w

# 检查 mcp 的 Pod（旧 Pod 会因 historyLimit 被清理，新的 Job 会自动成功）
kubectl get pods -n mcp -w
```
*预期结果*：
- `rc-volume-hostpath-missing` 应最终转为 `Running` 状态。
- `mcp` 命名空间中的 `node-debugger` Pod 会因 `ls` 命令执行成功而正常退出（状态变为 `Completed`）或被新 Pod 替代后运行成功。

### 后续优化
1. **确认 Pod 用途**：检查 `aiops-e2e/rc-volume-hostpath-missing` 的标签 `pod_abnormal_type=VolumeMountFailed,rootcause-e2e=true`，确认是否为用于故障测试的 E2E 用例。如果是，修复完成即满足测试目的。
2. **路径管理**：避免在生产工作负载的 Pod spec 中硬编码不存在的 HostPath 目录。

---
## 📋 验证步骤
| 步骤 | 命令 | 预期结果 |
|------|------|----------|
| 1. 验证目录存在 | `kubectl run -it --rm debug --image=busybox --restart=Never -- ls /tmp/aiops-rootcause-definitely-missing-hostpath-dir` | `ls` 命令成功，没有错误输出。 |
| 2. 确认 g1 Pod 运行 | `kubectl get pod rc-volume-hostpath-missing -n aiops-e2e` | STATUS: `Running` |
| 3. 确认 g2 Pod 状态 | `kubectl get pods -n mcp \| grep node-debugger` | 新的 Pod 状态为 `Completed` 或 `Running`。 |

---
## ⚠️ 注意事项
- 修复极其简单，只需在 `node1` 机器上执行一条 `mkdir` 命令。
- 该问题极有可能是由有意的 E2E 故障注入脚本触发的，检查完毕后可清理相关测试资源。
- 所有工作负载均集中于 `node1` 节点，建议排查调度策略以防止单点故障。

---

## 📊 性能统计

├─ 总耗时: 1.7m
├─ 问题定位: 31.9s (31%) ✅
├─ 证据链采集: 24.7s (24%) ✅
├─ 根因分析: 26.0s (25%) ✅
├─ 汇总总结: 21.6s (21%) ✅
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
