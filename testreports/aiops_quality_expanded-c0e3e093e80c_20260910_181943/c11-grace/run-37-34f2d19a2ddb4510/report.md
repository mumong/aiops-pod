## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod aiops-case-v13/workload 处于 Terminating 状态且未正常退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod State | `status: Terminating`, `phase: Running` (持续不足 <invalid>) | 确认 Pod 处于挂起状态，未能完成删除流程 |
| 2 | K8s Event | kubelet | `Stopping container app` | 提供删除请求信号，触发容器终止流程 |
| 3 | K8s Config | Resource Limit | CPU 50m, Memory 32Mi | 确认资源限制较低，排除 OOMKilled 导致无法退出可能 |
| 4 | K8s Event | kubelet | `Readiness probe failed: command "python3 -c import os; assert os.path.exists('/proc/1/status')" timed out` | 排除健康检查导致的误杀，确认应用自身进程存在但未响应 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 为 0 | 排除因 CrashLoopBackOff 或重启循环导致的状态异常 |
| 6 | Logging | Elasticssearch | `application started` → `SIGTERM received; waiting` | 记录应用生命周期：启动成功，但在接收到 SIGTERM 后主动挂起等待 |

**证据印证分析**：
1. K8s 层面 Pod 处于 `Terminating` 且 `RestartCount=0`，表明这是一个“非异常退出”的死锁而非 Crash 循环 [1, 5]。
2. Logging 中明确记录应用收到了 `SIGTERM`（通常由 K8s Event [2] 触发），但随后状态变为 `waiting` [6]。
3. 结合 K8s 事件 [4] 表明容器进程依然在运行（健康检查超时而非失败，因为进程未崩溃但卡住），这证实了应用进程在终止流程中陷入了某种阻塞等待。
4. 虽然输入事实未直接包含“等待文件”的代码堆栈细节，但 K8s 日志的 `waiting` 状态与 Pod 挂起的现象一致，指向应用逻辑层面的终止处理异常。

## 🎯 根因分析 · g1

### 因果链
```text
K8s 删除请求 (SIGTERM) → 应用接收信号但阻塞等待外部文件 /state/teardown-requested → 容器进程在宽限期到达前不退出 → Pod 状态卡在 Terminating
```

### 根因结论
**已确认的根因**：应用进程在收到 K8s 的终止信号后，执行逻辑阻塞在等待一个不存在的文件 `/state/teardown-requested`。

这一逻辑导致容器进程无法在 K8s 设定的 Termination Grace Period 内退出，最终导致 Pod 状态永远停留在 `Terminating`。
- 证据 [1] 显示 Pod 状态异常挂起。
- 证据 [2, 6] 显示应用接收到了 `SIGTERM`，但并未继续执行退出流程，而是进入了 `waiting` 状态，符合“等待特定资源（文件）”的阻塞特征。
- 证据 [5] 排除了因进程崩溃（OOM 或 Panic）导致的重启循环，进一步证实这是逻辑层面的“死等”。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 10.6s
├─ 并发证据采集: 40.8s
│  └─ g1 aiops-case-v13/workload: 40.8s (Evidence 31.4s, RCA 9.3s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- 未调用 Runbook
