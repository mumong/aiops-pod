## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Pod workload-7679bcf76-jwr8b处于CrashLoopBackOff，持续异常退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 退出码 2 (fact-6689a8ec72cd)、Reason: Error (fact-a8a30a44b878) | 直接定位到应用层主动退出，非 OOM 等系统级崩溃 |
| 2 | Logging | Elasticsearch | `runtime process exiting`, http_status: 500, path: /work, count: 4 (fact-7376f1603c05 等) | 提供核心因果链，证明应用在处理特定请求时主动退出 |
| 3 | K8s Event | Kubernetes | BackOff 事件，x157 over 37m (fact-2995ebe78f59) | 证实容器因异常退出引发了 Kubernetes 的指数退避重启 |
| 4 | K8s State | Kubernetes | restart_count: 12 (fact-27cc53871193) | 确认 Pod 处于持续异常重启的 CrashLoopBackOff 状态 |
| 5 | Tracing | Tempo | Span `GET /work` 状态码 500, aiops.observed_mode: runtime_exit, trace_id: 18e0338801b5ff20f216241e4c442d1e (fact-63304b71418d) | 关联日志与请求，精确定位到导致退出的具体请求上下文 |
| 6 | Metric | Prometheus | kube_pod_container_status_restarts_total: 12 (fact-a0b6aaf09788) | 独立验证了 K8s 侧的重启次数记录 |

上述证据形成了闭环：K8s 监控到异常退出（#1, #4），日志确认是 `/work` 接口返回 500 后触发的主动退出（#2），而分布式追踪（#5）将日志中的错误与具体的 HTTP 请求链路绑定，证实了根因发生在应用内部处理该接口时。

## 🎯 根因分析 · g1

### 因果链

```text
应用执行 GET /work 发生内部错误 → 服务返回 HTTP 500 并打印 "runtime process exiting" → 应用进程主动退出，exitCode=2 → kubelet 触发重启，最终陷入 CrashLoopBackOff
```

### 根因结论

已确认根因为：应用在处理 `GET /work` 请求时遭遇内部异常，导致主动返回 `HTTP 500` 并强制终止进程（`exitCode=2`），进而引发 Kubernetes 反复重启。

该结论由以下事实强支撑：
- 应用主动退出的直接证据：日志记录到 `runtime process exiting`，同时伴随 `exit_code: 2`（证据 #1, #2）。
- 触发条件的链路证据：追踪服务 `fact-63304b71418d` 确认导致退出的 Span 是 `GET /work`（返回 500 状态码）。
- 现象证据：K8s 侧记录的高频重启 `x157` 事件与 `CrashLoopBackOff` 状态（证据 #3, #4）。

**缺失事实**：目前证据链无法揭示 `/work` 接口内部发生异常的具体代码逻辑或底层依赖组件故障详情。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 21.1s
├─ 并发证据采集: 75.2s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 75.2s (Evidence 65.1s, RCA 10.0s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
