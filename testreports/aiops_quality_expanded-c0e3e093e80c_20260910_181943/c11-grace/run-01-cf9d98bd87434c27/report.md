## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | {'type': 'PodScheduled', 'status': 'True'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `fact-ee4e13b137ba`: Pod `aiops-case-v13/workload` phase=Running | 确认 Pod 处于运行状态 |
| 2 | K8s State | kubernetes | `fact-5dfdbc290978~d99616ec3150`: Pod conditions (PodScheduled/Ready/Initialized/ContainersReady) 均为 True (06:32:17Z-25Z) | 确认 Pod 容器启动成功 |
| 3 | Metric | prometheus | `fact-c9e672bb7f62`: `kube_pod_deletion_timestamp` = 1789371445 (06:37:25Z) | 确认触发删除的时间 |
| 4 | K8s Config | kubernetes | `fact-091266d970e9/8fba19670810`: 内存限制 32Mi，CPU 限制 50m | 资源配置上下文 |
| 5 | Logging | elasticsearch | `fact-d255043122a7`: "application started" (06:32:24.004Z) | 确认应用曾启动 |
| 6 | Logging | elasticsearch | `fact-d8126539b72b`: "SIGTERM received; waiting" (06:32:25.606Z) | 确认应用收到 SIGTERM 但未退出 |

**证据关联说明：**
- K8s 的 deletionTimestamp (证据 #3) 为 06:37:25Z，而日志 (证据 #5, #6) 记录时间为 06:32:24Z 和 06:32:25Z。删除时间晚于日志记录时间，且 `terminationGracePeriodSeconds` 为 3900s，日志时间点在删除请求前，表明该日志不能直接解释当前的 Terminating 状态。
- 应用启动后未重启 (K8s & Metric 均为 0)，排除了 CrashLoop 导致的状态异常。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 被请求删除 (deletionTimestamp=07:37:25Z) → 应用收到 SIGTERM 并打印 "waiting" (日志时间 06:32:25Z) → 缺少应用真正退出的证据 / 无法判断当前是否超时 → Pod 保持 Terminating 且 phase=Running
```

### 根因结论

**证据不足。**

现有证据表明 Pod 处于 Terminating 状态且 phase=Running。日志记录的 `SIGTERM received; waiting` 发生在 `deletionTimestamp` 之前，未能证实当前的阻塞机制。
缺乏以下关键事实以得出确切结论：
1. 当前系统实际时间（用于判定 07:37:25Z + 3900s 是否已超时）。
2. 具体的 Volume detach 失败日志或 Finalizer 执行状态。
3. 节点 (Node2) 的当前 Ready 状态，以排除节点故障导致的 Pod 终止延迟。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 26.8s
├─ 并发证据采集: 70.3s
│  └─ g1 aiops-case-v13/workload: 70.3s (Evidence 56.5s, RCA 13.7s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
