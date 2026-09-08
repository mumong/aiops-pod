## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | 应用启动后读取配置失败（CONFIG_MISSING），导致进程以退出码 78 主动终止，引发 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff 2m34s (x109 over 27m) kubelet Back-off restarting failed container app in pod workload-dff5cbc6b-fkzvn_aiops-case-07` | 证实应用启动失败已引发 kubelet 指数退避重试 |
| 2 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff` | 确认当前容器处于异常等待状态 |
| 3 | K8s State | Kubernetes | `container.last_terminated_reason: Error`，`container.last_exit_code: 78` | 提供进程非正常终止的直接证据 |
| 4 | Logging | Elasticsearch | Pattern: `error CONFIG_MISSING` (path: `/work`, status: 500)，出现 8 次，首个时间戳 `14:38:47Z` | 揭示进程退出的直接原因是缺失关键配置项 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 9 | 佐证容器多次重启现象（结合 K8s 计数为 10 次） |

**证据关联与印证：**
- 日志证据（#4）明确了错误语义 `CONFIG_MISSING`，直接解释了 K8s 状态中 `last_terminated_reason`（#3）为何是 `Error` 以及退出码 78 的来源。
- 事件（#1）与指标（#5）从运行时和监控系统两个维度，印证了由于上述错误导致的反复重启与 CrashLoopBackOff 行为。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动时读取关键配置失败（CONFIG_MISSING） → 进程主动退出（错误码 78） → kubelet 重启策略触发失败 → 用户可见 CrashLoopBackOff
```

### 根因结论

**已确认的根因：应用内部逻辑报错 `CONFIG_MISSING`**

1. **直接原因**：容器 `app` 在启动或初始化阶段因未能读取到关键配置项（日志记录为 `CONFIG_MISSING`），导致业务进程以退出码 `78` 异常终止（证据 #3, #4）。
2. **机制确认**：Kubernetes 根据重启策略自动重试该容器，但在配置缺失问题未解决的情况下，每次启动均会重复上述失败逻辑，进而触发 `CrashLoopBackOff` 状态（证据 #2, #5）和指数退避事件（证据 #1）。
3. **结论依据**：K8s 状态事实与日志事实之间存在直接的因果映射关系（退出码 78 对应 `CONFIG_MISSING`），事实链条完整且无逻辑冲突。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 28.2s
├─ 并发证据采集: 40.3s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 40.3s (Evidence 34.9s, RCA 5.3s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime
