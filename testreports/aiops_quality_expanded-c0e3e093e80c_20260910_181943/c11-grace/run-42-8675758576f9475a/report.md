## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod workload (aiops-case-v13) 处于 Terminating 状态且卡住，容器进程未响应终止信号。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Normal Killing 52s Stopping container app` | 确认 Kubelet 发起终止信号的时间点 (17:52:52) |
| 2 | Logging | elasticsearch | `SIGTERM received; waiting` (17:52:54) | 直接证明应用进程接收信号后处于阻塞等待状态，未退出 |
| 3 | K8s Event | kubelet | `Readiness probe failed: command "python3 -c import os; assert os.path.exists('/proc/1/status')" timed out` (多次) | 探针超时证实进程未响应系统调用，导致健康检查失效 |
| 4 | K8s State | kubernetes | `status: Terminating (lasts <invalid>)` | 确认 Pod 处于终止状态的卡点现象 |
| 5 | Metric | prometheus | `restart_count: 0` | 确认此为初始故障，非重启循环 |

**证据印证说明：**
日志明确记录了 `SIGTERM received; waiting` (证据 2)，与 Kubelet 发起 `Stopping container` 事件 (证据 1) 的时间顺序一致，证明进程在信号处理上出现了阻塞。由于进程僵死（证据 2），导致探针读取 `/proc/1/status` 失败 (证据 3)，进而使 Pod 被锁定在 `Terminating` 状态 (证据 4)。指标未重启 (证据 5) 排除了应用已崩溃重启的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
应用未实现有效 SIGTERM 处理逻辑 → 进程阻塞等待 (未退出) → 就绪探针超时 & Kubelet 终止流程卡住 → Pod 处于 Terminating 状态
```

### 根因结论

**已确认根因**：应用容器在收到 SIGTERM 信号后未能正常退出。
**证据支持**：
1. 日志证据显示应用明确接收到了信号 (`SIGTERM received`) 但紧接着进入了等待状态 (`waiting`) [证据 #2]。
2. K8s 探针超时错误 (`timed out`) 确认了容器进程僵死，无法响应系统级读取请求 [证据 #3]。
3. 上述原因直接导致了 Pod 状态被锁定在 `Terminating` [证据 #4]。

**缺失/未确认事实**：
虽然确认了“阻塞等待”这一行为，但无法从当前数据确认应用具体的等待对象（是 I/O 阻塞、死锁还是逻辑错误）[引用 unknowns]。Tracing 数据缺失无法提供代码级调用栈细节。

---

## 📊 性能统计

```text
├─ 总耗时: 2.7m
├─ 问题定位: 13.2s
├─ 并发证据采集: 139.2s
│  └─ g1 aiops-case-v13/workload: 139.2s (Evidence 127.1s, RCA 12.0s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
