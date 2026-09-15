## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod workload-dff5cbc6b-sjvxl 处于 CrashLoopBackOff，容器 app 退出码 78 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: "Error" | 确认应用容器存在主动异常退出的事实。 |
| 2 | K8s State | Kubernetes | `container.last_exit_code`: 78 | 提供具体的退出码，指向应用内部逻辑。 |
| 3 | K8s State | Kubernetes | `pod.condition` | `Ready` 与 `ContainersReady` 为 `False` (20:41:53Z) | 验证容器崩溃导致的 Pod 不可用状态。 |
| 4 | K8s Event | Kubernetes | `event.message`: "Back-off restarting failed container app... BackOff" (x42 over 12m) | 记录容器启动即崩溃并触发 Kubelet 指数退避重启的机制。 |
| 5 | Logging | Elasticsearch | Pattern: `CONFIG_MISSING` (8 次) / HTTP 500 | 揭示容器在短暂运行期间触发了业务配置缺失错误。 |
| 6 | Tracing | Deepflow + Tempo | Span `GET /work` HTTP 500 (20:30:49.376Z), `trace_id`: a358165... | 关联日志 Pattern 中的 trace_id，确认请求级故障路径。 |
| 7 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 1 (CrashLoopBackOff) / `restarts_total` 7 | 宏观确认集群层面的重启计数与等待状态。 |

日志中捕获到 8 次 `CONFIG_MISSING` 错误，对应 Trace 数据中的 `trace_id: a358165e4c5df7b2882c057473693f30` 的 HTTP 500 请求。应用进程在处理请求后触发业务异常，随后立即退出（Exit 78），导致 Kubernetes 进入 CrashLoopBackOff 状态（重启 7 次）。Metrics 与 Events 确认了这一崩溃周期的持续存在。

## 🎯 根因分析 · g1

### 因果链

```text
运行时检测到配置缺失 (CONFIG_MISSING) → 应用进程主动执行 sys.exit(78) 终止 → kubelet 捕获非零退出码并触发重启 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因是：应用进程在启动后处理请求时检测到**配置缺失（CONFIG_MISSING）**（证据 #5、#6），主动调用退出命令终止（Exit Code 78，证据 #2）。由于缺乏该配置，进程无法恢复运行，被 Kubelet 捕获并持续重启（事件 #4，重启计数 #7），导致 Pod 进入 `CrashLoopBackOff` 状态。

目前仍缺失 `ConfigMap workload-code` 中具体缺失的配置键值以及应用期望的具体配置结构。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 20.8s
├─ 并发证据采集: 60.9s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 60.9s (Evidence 52.0s, RCA 8.8s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
