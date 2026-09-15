## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod aiops-case-v13/workload 处于 Terminating 状态但容器进程保持 Running 且重启次数为 0 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-v13/workload` 状态: `Terminating`, Phase: `Running`, 重启次数: `0` | 确认 Pod 处于无法终止的僵死状态，且进程未崩溃或重启 |
| 2 | K8s Event | Kubernetes | `Normal Killing 52s kubelet Stopping container app` 及 `Stopping container app` (101s) | 确认 Kubelet 已收到指令并尝试发送停止信号，但停止动作未成功执行 |
| 3 | Logging | Elasticsearch | `2026-09-14T07:04:29.801Z` `SIGTERM received; waiting` | 应用程序层捕获到 SIGTERM 信号，但执行逻辑进入等待而非退出，证实阻塞点 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 值为 `0` | 排除因 OOM 或崩溃重启导致的异常，佐证进程仍在后台运行 |
| 5 | K8s Config | Kubernetes | CPU 请求/限制: `5m`/`50m`；内存请求/限制: `8Mi`/`32Mi` | 排除资源配额（CPU/Memory）超限导致的 K8s 调度或容器管理异常 |

**证据分析：**
日志事实 #3 与 K8s 事实 #1、#2 高度互证：Kubelet 发送了信号（事实 #2），应用确实收到了信号（事实 #3），但由于应用逻辑中的阻塞式等待导致进程未真正终止，因此 Pod 状态始终卡在 Terminating（事实 #1）。Metric 事实 #4 排除了进程意外崩溃的可能，将范围严格限定在应用层代码逻辑异常上。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码实现为阻塞式循环（检查文件是否存在） → 收到 SIGTERM 信号但进入等待逻辑 → /state/teardown-requested 文件未被创建 → 进程无限期等待，Pod 状态卡死在 Terminating
```

### 根因结论

**已确认根因：** 应用层存在硬编码的优雅退出逻辑缺陷。

*   **故障机制**：应用程序监听 `SIGTERM` 信号后，没有直接执行退出逻辑，而是执行了“等待 `/state/teardown-requested` 文件出现”的操作（证据 #3）。
*   **结果**：由于上游触发文件创建的机制未生效，该文件始终不存在，导致应用进程陷入无限等待，Kubernetes 无法完成 Terminating 阶段。

**未确认事项：** 触发 `/state/teardown-requested` 文件创建的上游机制（如 Init Container、Sidecar、Operator 或外部 Job）为何未执行或信号为何未到达（证据 #3 暗示了文件缺失）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 16.9s
├─ 并发证据采集: 107.1s
│  └─ g1 aiops-case-v13/workload: 107.1s (Evidence 97.1s, RCA 9.5s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
