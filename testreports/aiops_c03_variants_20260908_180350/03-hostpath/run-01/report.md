## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod 的 HostPath 卷 'input' 挂载失败，因目标路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 在调度节点 node2 上不存在或非目录，导致 kubelet 阻塞在 MountVolume.SetUp 阶段，进而使容器一直处于 ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` (fact-94f43139d93c) | 确诊 HostPath 挂载因目标路径非目录而失败，解释了容器阻塞的直接原因 |
| 2 | K8s State | kubernetes | Pod phase: `Pending`, Container `app` status: `ContainerCreating` (fact-772d0101325e, fact-b4150b476f98) | 确认 Pod 因挂载问题长期停滞在创建阶段，未进入就绪状态 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值 `1`，label `reason: "ContainerCreating"` (fact-7ced5154835c) | 通过监控数据独立验证了应用容器持续处于等待挂载状态的现象 |

**证据关联说明**：Kubernetes 的 `FailedMount` 事件直接指向文件系统层面的配置错误（fact-1）；Pod 的 `Pending` 状态与 `ContainerCreating` 等待原因（fact-2）是挂载失败的同步表现；Metric 数据（fact-3）确认了该状态在监控窗口内持续存在且未发生重置。

## 🎯 根因分析 · g1

### 因果链

```text
HostPath 挂载点 /var/lib/.../input 在 node2 上不存在或非目录 → kubelet MountVolume.SetUp 失败 → 容器阻塞在 ContainerCreating 阶段 → Pod 持续处于 Pending 状态
```

### 根因结论

已确认的根因为 **HostPath 卷挂载配置错误**，具体为 Volume 'input' 在调度节点 `node2` 上的目标路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 不是有效的目录，导致 kubelet 阻塞挂载过程（引用证据 #1、#2、#3）。现有事实已构成完整因果链，无需日志或追踪数据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 28.3s
├─ 并发证据采集: 42.6s
│  └─ g1 aiops-case-v06/workload: 42.6s (Evidence 36.2s, RCA 6.3s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-imagepull-failed, pod-pending-unschedulable, pod-volume-mount-failed
