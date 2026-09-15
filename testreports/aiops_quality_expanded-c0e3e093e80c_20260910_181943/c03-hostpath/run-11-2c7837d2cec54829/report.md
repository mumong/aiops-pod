## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod aiops-case-v06/workload 卡在 ContainerCreating/Pending 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (Pod Status) | `status: Pending`; `ContainersReady: False` (`containers with unready status: [app]`) | 确认 Pod 处于挂起状态，核心容器 `app` 未能就绪，符合输入中描述的“卡在 ContainerCreating/Pending 状态”的异常现象。 |
| 2 | K8s Event | kubernetes (Warning) | `FailedMount` (x14 over 12m) `MountVolume.SetUp failed for volume "input" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 直接揭示 Pod 卡住的核心阻碍：主机路径类型校验失败。Kubelet 在目标节点上无法将指定路径视为有效目录，直接拒绝挂载卷。 |
| 3 | K8s Event | kubernetes (Warning) | `FailedMount` (x5 over 10m) `timed out waiting for the condition` | 佐证挂载操作持续处于阻塞和超时状态，反映了该故障具有持续性而非瞬时抖动。 |
| 4 | Metric | Prometheus (`kube_pod_container_status_waiting_reason`) | `reason: ContainerCreating`, value `1` (timestamp: `2026-09-11T11:50:39.522000Z`) | 独立于 K8s Event 的状态确认，表明容器正处于等待初始化的阶段，与 Kubelet 挂载卷失败的现象逻辑一致。 |

K8s Event (fact-2) 与 Metric (fact-4) 从控制面机制和监控系统两个维度互相印证：Kubelet 因目标路径类型不符合预期而挂载失败，导致容器状态被永久锁定在 `ContainerCreating`。

## 🎯 根因分析 · g1

### 因果链
```text
HostPath 路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 在目标节点 node2 上类型检查失败 (非目录或不存在) → Kubelet 执行 MountVolume.SetUp 时拒绝挂载 volume "input" → Pod 容器状态维持在 Waiting/ContainerCreating，无法进入 Running → Pod 整体处于 Pending 且业务负载无法调度运行
```

### 根因结论
已确认的根因为：**Pod 规格 (Spec) 中定义的 HostPath 卷路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 在调度目标节点上不符合预期，导致 Kubelet 挂载卷操作失败。**

Kubelet 在节点上对该路径进行类型检查时，判定该路径不是有效的目录（`is not a directory` 或路径不存在），从而触发了 `MountVolume.SetUp failed` 错误。这种持续的挂载错误阻止了容器 `app` 的启动，进而导致整个 Pod 长期滞留在 `ContainerCreating` / `Pending` 状态。此结论完全由 Kubernetes 事件记录 (`FailedMount`, `hostPath type check failed`) 及容器状态支撑，逻辑链条闭合。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.9s
├─ 并发证据采集: 39.9s
│  └─ g1 aiops-case-v06/workload: 39.9s (Evidence 32.3s, RCA 7.6s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed
