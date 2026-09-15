## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | 应用在处理 /work 请求时发生未捕获的运行时异常（Error exit code 2），导致进程直接退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | 容器 app 退出码 2 (fact-8cd892d5b887, fact-f8d76c94dffd) | 确认应用进程异常退出并导致 CrashLoopBackOff (fact-7084f7863e7e) |
| 2 | Metric | prometheus | 容器 app 状态 `CrashLoopBackOff`=1，重启总数 6 (fact-6efe357630ac, fact-da47a5b1497b) | 量化异常持续时间，证明系统已尝试多次重启 |
| 3 | K8s Config | kubernetes | 内存硬限制 96Mi，CPU 200m (fact-6632ccfa30d2, fact-d7d474b0f3a5) | 作为资源约束上下文，但日志显示分配内存为 0 MiB，排除 OOMKill |
| 4 | Logging | elasticsearch | 4 条重复日志：`http_status=200`, `path=/work` (fact-7ebf5a765ab9 等); 4 条重复日志：`http_status=500`, `runtime process exiting` (fact-7f29f52b1580 等) | 确认故障发生在处理 `/work` 请求时，且每次均触发运行时错误并退出 |
| 5 | Tracing | tempo | Span 记录 `observed_mode="runtime_exit"`, `http.response.status_code=200`, trace_id `891114b05a54ed1261e5487a5c071242` (fact-92b101e3f379) | 链路级确认在 `/work` 请求返回 200 时，进程随即以 runtime_exit 模式终止 |
| 6 | Tracing | deepflow | 7 次成功 Flow (HTTP GET /work 200, trace_ids: `bcf7475ff0cec26e70b014063be5b8db` 等); 2 次 500 Flow (trace_ids: `c9c473a44216a6fd6ea7013e9c7db04e`) | 跨维度观测证实 `/work` 路径下请求频繁，且部分请求伴随直接的状态码异常 |

证据表明应用在处理 `/work` 请求时发生未捕获的运行时异常。K8s 事件和 Metric 确认了由 Exit Code 2 导致的进程异常终止和反复重启；Log 聚合展示了 `http_status=500` 和 `runtime process exiting` 模式与 CrashLoop 的高度一致性；Tracing 中的 `observed_mode: runtime_exit` 进一步锁定了进程级退出机制。日志中分配内存始终为 0 MiB，结合 96Mi 的硬限制，排除了资源超限（OOM）导致的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码 /work 路径处理失败 → 未捕获运行时异常 (Exit code 2) → 容器进程直接退出 → Kubelet 触发 CrashLoopBackOff 及 Pod 重启
```

### 根因结论

已确认根因是应用在处理 `/work` 请求时发生未捕获的运行时异常。应用进程在收到请求后直接以 exit code 2 终止，Kubelet 随之执行重启策略，导致 Pod 处于 CrashLoopBackOff 状态。该结论由容器退出码事实、K8s 事件及 `runtime process exiting` 日志相互印证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 16.0s
├─ 并发证据采集: 61.6s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 61.6s (Evidence 55.3s, RCA 6.2s)
└─ 汇总总结: 12.7s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime, pod-imagepull-failed, pod-config-error
