## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod aiops-case-v08/workload 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | Logging | Elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 证明容器内进程因找不到命令而直接退出 |
| 2 | K8s State | Kubernetes | `last_exit_code: 127` | 确认进程退出码 127 (Command not found)，与日志匹配 |
| 3 | K8s State | Kubernetes | `last_terminated_reason: Error` | 表明容器处于非成功终止的异常退出状态 |
| 4 | K8s Event | Kubernetes | `Warning BackOff ... back-off 5m0s restarting failed container=app pod=workload_aiops-case-v08(00e5e755-886e-4661-9e8a-00d1e71595f6)` | 显示 Pod 进入 CrashLoopBackOff 且因频繁重启被限流 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="CrashLoopBackOff"} = 1` | 确认当前 Pod 等待原因确认为 CrashLoopBackOff |

日志直接揭示了 `command not found` 错误并对应 127 退出码；K8s 状态显示容器因 Error 退出，Metric 佐证了当前的 CrashLoopBackOff 等待状态。多源数据互相印证了进程启动失败导致重启循环的单一事实。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置命令 /opt/app/unavailable-command (fact 1, 2) → 镜像中不存在该二进制文件导致进程启动失败 (fact 1, 2) → 进程以 Exit Code 127 退出 (fact 2) → Kubernetes 检测到异常退出并触发 CrashLoopBackOff (fact 3, 4, 5)
```

### 根因结论

**已确认的根因**：Pod 配置的错误命令路径 `/opt/app/unavailable-command` 指向不存在的可执行文件，导致容器启动即失败并触发重启循环。

**证据支撑**：
1. **故障机理**：日志 (fact 1) 明确报错 `not found`，且容器退出码 (fact 2) 为 127，直接证实是命令缺失导致的启动失败。
2. **故障现象**：容器终止原因 (fact 3) 为 Error，且 Metric (fact 5) 确认 Pod 处于 CrashLoopBackOff 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 18.8s
├─ 并发证据采集: 35.1s
│  └─ g1 aiops-case-v08/workload: 35.1s (Evidence 25.5s, RCA 9.5s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
