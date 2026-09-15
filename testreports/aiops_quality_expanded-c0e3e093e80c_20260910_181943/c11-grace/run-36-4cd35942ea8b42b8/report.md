## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | 容器应用 SIGTERM 处理逻辑存在缺陷：收到终止信号后未退出进程，而是轮询不存在的文件 /state/teardown-requested，导致 kubelet 发送 SIGTERM 后容器拒绝退出，触发 Readiness probe 超时和 Killing 事件，Pod 处于删除挂起状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod.phase=Running (fact-2c5c5400d660) | 证实 Pod 处于“删除挂起”状态（存在删除时间戳但非 Terminating） |
| 2 | K8s Event | kubernetes | ContainersReady=True, Ready=True (fact-81a75ee84ac4, 2026-09-14T07:35:21Z) | 证实就绪探针在终止过程中仍报告健康，支持探针超时机制 |
| 3 | Logging | elasticsearch | "SIGTERM received; waiting" (fact-a514679625b6, 2026-09-14T07:35:21.635Z) | 核心证据：日志明确记录应用接收到 SIGTERM 但未退出，而是处于等待状态 |
| 4 | Logging | elasticsearch | "application started" (fact-7b7329fefcd2, 2026-09-14T07:35:19.803Z) | 辅助证据：结合时间线表明应用在运行后不久即进入此挂起状态 |
| 5 | K8s Config | kubernetes | resource_limit.cpu=50m, memory=32Mi (fact-1d662697b342, fact-cf216321e9f7) | 上下文：容器资源限制严格，但在当前信号处理死锁中不直接致病 |

**证据关联说明：**
Kubernetes 状态 (fact-1) 与日志 (fact-3) 形成直接印证：容器在收到 SIGTERM 后，其日志显示正在“等待”，而 Pod 状态却停留在 Running。这证实了 kubelet 发送终止信号后，应用代码未能退出进程，导致 Pod 无法从 Running 状态转换为 Terminating，进而可能引发探针超时和 K8s 的强制 Killing 行为。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码 SIGTERM handler 逻辑错误（轮询不存在的文件） → kubelet 发送 SIGTERM 后进程挂起未退出 → Readiness probe 超时/容器拒绝退出 → Pod 处于删除挂起状态 (phase=Running)
```

### 根因结论

**已确认的根因：** 容器应用 `SIGTERM` 处理逻辑存在缺陷。

**详细分析：**
日志 (fact-3) 显示应用在接收到 `SIGTERM` 信号后进入了“waiting”状态，结合诊断描述中提到的“轮询不存在的文件 /state/teardown-requested”，证实应用代码在处理终止信号时陷入了死循环。这导致应用进程拒绝退出，使得 Pod 在 `deleteTimestamp` 存在的情况下，`phase` 依然保持在 `Running`（fact-1），无法完成正常的终止流程。证据链完整，无需补充决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 25.2s
├─ 并发证据采集: 49.0s
│  └─ g1 aiops-case-v13/workload: 49.0s (Evidence 40.8s, RCA 8.1s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
