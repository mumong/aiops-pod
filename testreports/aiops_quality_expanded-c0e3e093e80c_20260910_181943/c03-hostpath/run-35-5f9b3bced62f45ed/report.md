## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod 调度至 node2 后，kubelet 执行 HostPath 卷 'input' 挂载时，发现指定路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 在节点上不存在或类型非目录，导致 MountVolume.SetUp 持续失败，容器永久阻塞在 ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod 状态 Pending, 容器 waiting_reason: ContainerCreating | 确认当前状态 |
| 2 | K8s Event | kubernetes | `MountVolume.SetUp failed for volume "input" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 核心证据：宿主机路径检查失败 |
| 3 | K8s Config | kubernetes | HostPath 卷名 input，指向路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` | 定位异常实体 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason: ContainerCreating) | 独立观测确认 |

**证据印证说明**
*   **K8s 状态、事件与指标相互印证**：事件 `fact-eae48cecb219` 明确指出 HostPath 卷挂载失败，原因系宿主机路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 不存在或非目录。该事件解释了为何 K8s State 显示 `ContainerCreating`（证据 1）以及 Prometheus 指标显示 `waiting_reason` 为 `ContainerCreating`（证据 4）。
*   **日志/追踪不适用**：Pod 处于 `ContainerCreating` 阶段且未运行，因此未采集到日志与追踪数据属正常物理限制，不影响当前挂载异常的定责。

## 🎯 根因分析 · g1

### 因果链

```text
宿主机路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 不存在或类型非目录 → kubelet 挂载 HostPath 卷 'input' 失败 (MountVolume.SetUp failed) → Pod 容器永久阻塞在 ContainerCreating 状态 → 业务 Pod 不可用
```

### 根因结论

**已确认根因**：Pod 调度至 node2 后，执行 HostPath 卷 `input` 挂载时，节点上 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 路径不存在或不是目录，导致挂载持续失败。

*   **证据支持**：由事件 `fact-eae48cecb219` 直接提供 `hostPath type check failed` 报错，结合 K8s State 与 Prometheus 指标 `ContainerCreating` 确认了阻塞状态及原因（证据 1-4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 14.5s
├─ 并发证据采集: 39.4s
│  └─ g1 aiops-case-v06/workload: 39.4s (Evidence 32.9s, RCA 6.4s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed, pod-imagepull-failed
