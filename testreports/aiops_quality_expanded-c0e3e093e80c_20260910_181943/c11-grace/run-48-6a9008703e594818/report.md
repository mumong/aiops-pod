## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod aiops-case-v13/workload 处于 Terminating 状态，等待 SIGTERM 处理程序完成 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Normal Killing 43s kubelet Stopping container app` | 确认删除操作已触发，容器收到停止信号。 |
| 2 | Logging | app日志 | `application started` (08:05:38.404Z) 到 `SIGTERM received; waiting` (08:05:39.698Z) | 明确应用进程在收到 SIGTERM 后进入等待状态。 |
| 3 | K8s Event | kubelet | `Warning Unhealthy 24s kubelet Readiness probe failed: command ... timed out` | 就绪探针因进程无响应（被挂起）而超时，印证应用逻辑未正常退出。 |
| 4 | K8s State | pod status | `status: Terminating (lasts <invalid>)`, `phase: Running` | 确认 Pod 处于 Terminating 阶段，且容器进程在逻辑上仍处于运行状态。 |

证据 1 与 2 互证：kubelet 发出 Killing 指令后，应用立即捕获 SIGTERM 并打印日志进入 `waiting` 状态。证据 3 提供了进一步佐证：应用因“等待”而无法响应就绪检查探针。证据 4 展示了最终结果：进程未退出导致 Pod 无法完成 Termination 状态转换。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置了 terminationGracePeriodSeconds: 3900 秒 → 
应用捕获 SIGTERM 后进入 while 循环，等待文件 /state/teardown-requested 出现 → 
进程挂起未退出 → 
Pod 保持 Terminating 状态，等待超时或外部强制干预
```

### 根因结论

已确认根因为**应用处理 SIGTERM 的逻辑缺陷**：应用收到终止信号后，进入死循环等待特定的文件（`/state/teardown-requested`）被创建。

该机制直接导致进程在收到终止信号后并未退出，而是阻塞在文件检查逻辑中。这解释了为何在收到 `Killing` 事件（证据 #1）并进入等待状态（证据 #2）后，Pod 的 `Terminating` 状态（证据 #4）迟迟不转变为 `Running` 或其他终态。证据 #3 中的探针超时也符合应用处于阻塞状态的推断。

**缺失事实**：
- `/state/teardown-requested` 文件所在挂载卷的具体挂载来源及该文件当前是否存在，无法仅凭当前数据确认。
- 删除请求的时间戳与 Pod 创建时间戳（08:05:31）之间的逻辑矛盾未解释，可能存在日志采集偏差。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 19.8s
├─ 并发证据采集: 110.0s
│  └─ g1 aiops-case-v13/workload: 110.0s (Evidence 98.3s, RCA 11.4s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
