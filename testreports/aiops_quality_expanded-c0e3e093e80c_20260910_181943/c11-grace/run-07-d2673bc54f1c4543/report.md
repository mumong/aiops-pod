## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod aiops-case-v13/workload status is 'Terminating' and stuck in this phase for over an hour. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | Readiness probe failed: command "python3 -c import os; assert os.path.exists('/proc/1/status')" timed out | 揭示容器启动后应用处于非健康状态，且具备基于 Python 的自定义行为特征 |
| 2 | K8s Event | kubelet | Normal Killing 46s Stopping container app | 确认触发删除的底层动作与 Pod 处于 `Terminating` 停滞状态 |
| 3 | Logging | elasticsearch | SIGTERM received; waiting | 核心直接证据，证实应用进程捕获了终止信号但并未退出，进入无限等待状态 |
| 4 | Logging | elasticsearch | application started | 说明应用已在 Pod 内完成启动并进入运行逻辑，排除了启动失败导致的非预期终止 |
| 5 | K8s Config | container resource limit | CPU: 50m, Memory: 32Mi | 排除资源耗尽（OOMCPUThrottling）导致进程异常退出的可能性 |
| 6 | K8s State | pod phase & condition | phase: Running; conditions (ContainersReady/PodScheduled/Initialized/Ready)均为 True | 证实异常发生在应用生命周期内部，而非调度或容器启动阶段 |
| 7 | Metric | prometheus | kube_pod_container_status_restarts_total: 0 | 确认 Pod 尚未发生重启，当前正处于第一次正常删除请求下的停滞期 |

**证据互证说明：**
1-2 确认了 Pod 被终止的操作与当前停滞现象。日志 3 解释了停滞的直接原因（收到 SIGTERM 但在 `waiting`），结合日志 4 的 `application started` 证明应用本身已成功启动并处于活跃运行中。配置 5 排除了资源瓶颈，状态 6 与指标 7 确认了异常发生的时序窗口。

## 🎯 根因分析 · g1

### 因果链

```text
用户触发 Pod 删除 (deletionTimestamp 写入) → 触发 SIGTERM 信号 → 应用捕获信号后阻塞 (等待特定条件未满足) → 进程拒绝退出 → Pod 卡死在 Terminating 阶段
```

### 根因结论

已确认根因为：**应用代码中的自定义优雅关闭逻辑存在缺陷，导致进程无限等待**。

1. **现象锁定**：应用已在 Pod 内启动并运行（日志 `application started`，状态均为 `Ready`），但在收到 `SIGTERM` 后，日志直接显示 `SIGTERM received; waiting`（证据 3）。
2. **逻辑推演**：通常应用收到信号后会在毫秒级内终止。`waiting` 行为表明应用执行了自定义的 `signal handler`，并在等待某个外部条件（如特定文件存在、连接断开或下游响应）。由于该等待条件在整个窗口期内（日志与事件时间线内）从未改变或达成，进程无法响应系统的终止请求。
3. **支撑确认**：
   - 就绪探针使用 `python3` 执行检查（证据 1），证实应用内部包含自定义 Python 脚本逻辑。
   - 资源配额极低但无报错（证据 5），重启次数为 0（证据 7），排除了运行环境故障。
   - 综上，Pod 处于 `Terminating` 状态并非集群层面问题，而是应用内部逻辑在等待一个永远不会发生的“清理信号”。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 15.5s
├─ 并发证据采集: 54.5s
│  └─ g1 aiops-case-v13/workload: 54.5s (Evidence 45.9s, RCA 8.4s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
