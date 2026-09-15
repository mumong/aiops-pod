## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod `workload` 的容器进程被配置为在收到 SIGTERM 后仅打印日志而不调用 `exit()`，导致进程未在 terminationGracePeriodSeconds (3900s) 宽限期内执行退出逻辑，从而卡死在 Terminating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod | `pod.status`: Terminating, `pod.phase`: Running | 确认 Pod 处于终止卡死状态，未进入 Finished |
| 2 | K8s State | Pod | `pod.condition` (Ready, ContainersReady): True | 确认 Pod 在异常前处于健康就绪状态 |
| 3 | K8s Event | kubelet | `Stopping container app` | 确认 Kubernetes 试图停止容器进程 |
| 4 | K8s Event | kubelet | `Readiness probe failed: ... timed out` | 确认健康检查失效，与进程僵死状态一致 |
| 5 | Logging | es | `SIGTERM received; waiting` | 捕获到应用层收到终止信号并挂起等待 |

日志捕获到收到 `SIGTERM` 后进程进入 `waiting` 状态，配合 K8s 层面的终止事件和就绪探针失败，构成“进程收到信号但未正常退出”的完整证据链。

## 🎯 根因分析 · g1

### 因果链

```text
容器进程未实现 SIGTERM 处理逻辑(仅等待) → 进程无法在宽限期内正常退出 → Pod 状态僵死(Terminating) → 就绪探针失败/不可访问
```

### 根因结论

已确认根因：Pod `workload` 的容器进程在处理 `SIGTERM` 信号时存在逻辑缺陷。证据显示应用层收到终止信号后仅输出“等待”日志而不调用退出逻辑，导致 Pod 在宽限期内卡在 Terminating 状态且就绪探针超时（引用证据 5 与证据 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 19.3s
├─ 并发证据采集: 39.9s
│  └─ g1 aiops-case-v13/workload: 39.9s (Evidence 32.5s, RCA 7.2s)
└─ 汇总总结: 5.9s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
