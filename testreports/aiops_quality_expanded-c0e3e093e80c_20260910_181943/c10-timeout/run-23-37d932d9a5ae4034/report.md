## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | Pod的Liveness Probe因应用线程阻塞导致超时（context deadline exceeded），触发kubelet发送SIGKILL（Exit Code 137）强制终止容器；尽管容器内存使用量（~3.7MB-11.9MB）远低于设定的内存Limit（64Mi），但探针超时引发的强制杀死是造成CrashLoopBackOff的直接机制。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Liveness probe failed: Get "http://172.16.104.36:18080/health": context deadline exceeded` (fact-1bf495bf4697) | 确认 Liveness Probe 因超时而失败，是触发容器重启的直接信号。 |
| 2 | K8s Event | Kubernetes | `Container app failed liveness probe, will be restarted` (fact-60edb0ebb90d) | 确认 kubelet 基于 Probe 结果执行了容器重启指令。 |
| 3 | K8s State | Kubernetes | Container exit_code: 137 (fact-85bfbc1d7d26) | 证实容器是被强杀（SIGKILL），而非正常退出或 OOM，指向 Probe 失败后的强制清理。 |
| 4 | K8s State | Kubernetes | CrashLoopBackOff; restart_count: 21 (fact-0be5bfc01412, fact-641db29d83cc) | 确认应用处于持续重启循环中，与上述 Kill 和 Probe 失败现象一致。 |
| 5 | Metric | Prometheus | memory_working_set_bytes: ~3.3MB-3.8MB, memory_limit: 64Mi (fact-06b3c11d9c59, fact-36763920f500) | 证实内存使用正常且远低于 Limit，排除了 OOMKilled 导致重启的可能性。 |
| 6 | Logging | Elasticsearch | `GET /ready HTTP/1.1 200` (fact-012295110816 等) | 提供对照证据：Readiness Probe 成功返回 200，说明服务主线程并非完全不可用，阻塞具有针对性。 |
| 7 | Tracing | Deepflow | L7 Flow GET /health: response_code 200, duration_us: 3000ms-3002ms (fact-33fd71452ae6 聚合) | 捕获到 /health 请求恰好耗尽其默认超时阈值（约 3 秒），验证了“请求耗时过长导致 kubelet 判定超时”的机制。 |

**证据互证说明：**
1. **机制闭环**：Tracing 数据（#7）显示 /health 请求耗时达到约 3 秒，这与 Kubernetes 事件（#1）中 "context deadline exceeded" 超时错误完全对应，解释了 Liveness Probe 为何失败。
2. **排除干扰**：尽管日志（#6）表明服务正在处理正常的 /ready 请求，但超时的 /health 请求直接导致容器被强杀（Exit 137, #3），进而引发 CrashLoopBackOff（#4）。同时，低内存指标（#5）排除了资源耗尽引发的异常。
3. **最终归因**：容器因响应探针超时被强制终止并重启，而根本原因锁定为应用逻辑中 /health 端点处理耗时过长导致超时。

## 🎯 根因分析 · g1

### 因果链

```text
应用线程阻塞（导致/health请求耗时>3秒） → Liveness Probe判定超时(context deadline exceeded) → kubelet强制Kill容器(Exit 137) → Pod进入CrashLoopBackOff状态
```

### 根因结论

**已确认根因**：
容器应用的健康检查端点 `/health` 处理耗时过长（Tracing 记录持续约 3000 毫秒，见证据 #7），超过了 kubelet Liveness Probe 的超时阈值，导致 Probe 连续失败（证据 #1, #2）。kubelet 因此发送 SIGKILL 信号强制终止容器（证据 #3），引发 CrashLoopBackOff 状态（证据 #4）。

**排除情况**：
通过 Metric 和 K8s 状态事实（证据 #5, #3），确认内存使用远低于 Limit（64Mi），且容器退出码为 137 而非 139 或 0，明确排除了 OOM（内存溢出）或正常退出的可能。

**未知领域**：
应用代码或依赖中导致 `/health` 接口响应变慢的具体逻辑（如死锁、慢查询或上游依赖阻塞）未在事实中出现，属于“未确认”状态。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 18.3s
├─ 并发证据采集: 97.5s
│  └─ g1 aiops-case-v17/workload: 97.5s (Evidence 86.2s, RCA 11.1s)
└─ 汇总总结: 14.9s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
