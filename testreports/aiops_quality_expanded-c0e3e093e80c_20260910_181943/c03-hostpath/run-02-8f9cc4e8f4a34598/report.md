## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod aiops-case-v06/workload 处于 ContainerCreating (Pending) 状态，未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` | `FailedMount` 59s (x8 over 2m3s) `hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 直接定位挂载失败的根因：宿主机路径缺失或类型不符 |
| 2 | K8s State | `kubernetes` | `ContainerCreating` (Pending)，`restart_count: 0` | 确认 Pod 停留在启动初期，尚未进入运行或重启循环 |
| 3 | K8s Config | `kubernetes` | HostPath Volume 配置为 `/var/lib/aiops-fixture-unavailable-7f394bef/input` | 提供触发 `FailedMount` 的具体资源对象配置依据 |
| 4 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason`: 1 (reason: `ContainerCreating`) | 数值状态与 K8s 事件中的挂载失败原因相互印证 |

**证据关联说明：**
1. `fact-3ec453acccc3` 明确指出了宿主机文件系统层面的缺失或校验失败，结合 `fact-91445577b91e` 中的挂载卷配置，确证是 HostPath 挂载失败导致了后续的容器创建阻塞。
2. 由于容器未能启动，`logging` 和 `tracing` 维度均无数据（`not_applicable`），符合逻辑预期，进一步排除了应用层内部错误的干扰。

## 🎯 根因分析 · g1

### 因果链

```text
Node2 缺少预期的 HostPath 挂载点 (`/var/lib/aiops-fixture-unavailable-7f394bef/input`) → kubelet 挂载 Volume 失败 (FailedMount) → 容器停留在 ContainerCreating 状态 → Pod 状态变为 Pending
```

### 根因结论

已确认根因：**Pod 配置的 HostPath Volume 挂载点不存在**。

Pod `aiops-case-v06/workload` 处于 `Pending` 状态，其根本原因是 kubelet 在调度节点 `node2` 上无法正确挂载名为 `input` 的 Volume。K8s Event (`fact-3ec453acccc3`) 明确记录 `hostPath type check failed`，表明指定的宿主机路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 要么不存在，要么不是目录类型。该挂载失败导致容器初始化受阻，进而停留在 `ContainerCreating` 状态（由 Event 重复触发和 Metric `fact-60a54d842d5a` 共同证实）。

---

## 📊 性能统计

```text
├─ 总耗时: 57.1s
├─ 问题定位: 21.6s
├─ 并发证据采集: 26.6s
│  └─ g1 aiops-case-v06/workload: 26.5s (Evidence 18.9s, RCA 7.6s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-imagepull-failed
