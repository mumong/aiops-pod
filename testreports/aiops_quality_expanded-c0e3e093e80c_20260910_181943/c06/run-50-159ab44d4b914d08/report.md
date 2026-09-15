## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod workload-7679bcf76-n5vp8处于CrashLoopBackOff状态，容器重启频繁（27次），kubectl日志与Prometheus指标均显示终止原因为Error且exitCode=2。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff 40s (x520 over 115m) kubelet Back-off restarting failed container app in pod workload-7679bcf76-n5vp8_aiops-case-06(08e11260-3505-495c-8224-2b91f27f029c)` | 确认 Pod 处于 CrashLoopBackOff 状态，Kubelet 因频繁重启进入指数退避 |
| 2 | K8s State | Kubernetes | `restart_count: 27`, `container.last_terminated_reason: Error`, `exit_code: 2` | 直接表明容器反复以非 0 状态码异常终止 |
| 3 | Metric | Prometheus | `reason="Error"` 且 `reason="CrashLoopBackOff"` 指标值为 1 | 验证容器终止原因及 Pod 等待状态的实时一致性 |
| 4 | Logging | Elasticsearch | 错误日志模式 `runtime process exiting` 伴随 HTTP 500 (4次, 04:01-04:27)；成功日志模式 `request completed` 伴随 HTTP 200 (4次, 04:01-04:17) | 日志记录到应用主动退出的信号，且无 OOMKilled 等系统级终止原因，指向应用层故障 |
| 5 | Tracing | Tempo | Trace `086f3a098b97574a79236521c99cd28f` 显示 `GET /work` 返回 200 且 `aiops.observed_mode: runtime_exit` | 确认正常请求执行完毕后进程立即退出，佐证异常退出并非由请求超时或错误本身引起 |

**证据关联说明：**
Kubernetes 的 Event 和 Container State 确认了容器因 `Error` 终止且 `exitCode=2` 而反复重启；Logging 和 Tracing 事实相互印证，显示应用是在收到 HTTP 请求（200 OK）后主动调用退出逻辑，而非资源耗尽被杀死。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理HTTP请求时异常退出（Exit Code 2） → Kubelet检测到非0终止并重启 → Kubelet触发BackOff退避机制 → Pod进入CrashLoopBackOff状态
```

### 根因结论

**已确认根因：** 容器应用进程在处理请求时发生非零退出（Exit Code 2），导致 Kubelet 判定为错误并持续重启，进而触发 BackOff 机制使 Pod 进入 CrashLoopBackOff 状态。
**依据：** Kubernetes 事实 `exit_code=2`、`reason=Error` 与事件 `Back-off restarting` 直接对应（证据 1-3）；日志和追踪记录到应用进程在成功完成请求后终止，排除了 OOM 或系统层资源限制导致的异常（证据 4-5）。

**未知领域（证据不足）：**
1. 导致 `exitCode 2` 的具体应用内部逻辑（如数据库连接丢失、配置缺失或断言失败）未被日志明确记录（如 Python 的 `sys.exit(2)` 或 `assert` 失败）。
2. 该崩溃是否由特定触发条件（如并发请求、特定参数或负载峰值）引起，目前的日志样本仅显示现象在测试窗口期内的持续发生。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 18.6s
├─ 并发证据采集: 112.7s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 112.7s (Evidence 98.1s, RCA 14.5s)
└─ 汇总总结: 12.1s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
