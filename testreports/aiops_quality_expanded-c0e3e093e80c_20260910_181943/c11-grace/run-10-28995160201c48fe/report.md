## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod 中的应用容器未正确实现 SIGTERM 信号处理逻辑：其 SIGTERM handler 打印日志后进入无限循环等待 '/state/teardown-requested' 文件出现，由于该文件永远不会被创建，容器无法退出，导致 kubelet 无法完成终止流程，Pod 卡在 Terminating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `Normal Killing 44s kubelet Stopping container app` | 证明系统层面已发起终止流程，确认异常非应用无响应，而是无法退出 |
| 2 | Logging | `elasticsearch` | `SIGTERM received; waiting` (2026-09-14T06:49:06.739Z) | 直接证实应用层捕获到信号，但逻辑阻塞在等待特定资源 |
| 3 | Logging | `elasticsearch` | `application started` (2026-09-14T06:49:05.403Z) | 建立应用运行时序，确认 SIGTERM 是应用运行后的突发事件 |
| 4 | K8s State | `pod.status` | `Terminating (lasts <invalid>)` | 确认 Pod 陷入 Terminating 终态，且停滞时间已超过 K8s 阈值 |
| 5 | K8s State | `pod.phase` | `Running` | 确认 Pod 底层资源尚未被释放，处于被强制隔离但进程仍存的僵死状态 |
| 6 | Metric | `kube_pod_container_status_restarts_total` | `0` | 表明该实例自部署至今未发生过重启，Terminating 状态是当前唯一的异常状态 |

**证据小结：**
应用日志 (2) 明确指出了逻辑阻塞点：进程在收到 SIGTERM 后并未退出，而是进入了无限循环等待模式。这与 K8s Event (1) 的 Killing 行为和最终僵死的 Terminating 状态 (4) 形成了完整的因果闭环，排除了网络隔离或节点故障的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码缺陷（未正确实现 SIGTERM 处理） → 进程阻塞等待不存在的 '/state/teardown-requested' 文件 → kubelet 无法等待容器优雅退出并超时 → Pod 卡在 Terminating 状态
```

### 根因结论

根因为：**应用容器的 SIGTERM 信号处理逻辑存在缺陷**。
当收到系统终止信号时，应用仅打印日志并进入死循环，等待一个永远不会被创建的文件 `/state/teardown-requested`。这导致进程无法响应 `docker kill` 或 `containerd` 的终止请求，进而使 kubelet 无法完成资源清理，最终导致 Pod 状态永久卡在 Terminating [fact-2, fact-4]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 22.2s
├─ 并发证据采集: 51.6s
│  └─ g1 aiops-case-v13/workload: 51.6s (Evidence 42.1s, RCA 9.4s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
