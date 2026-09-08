## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-w9s9c 处于 CrashLoopBackOff，应用进程在处理 /work 请求时返回 500 错误并退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning BackOff 62s (x112 over 26m)` | 确认 Pod 已进入指数退避重启循环，持续时间长达 26 分钟 |
| 2 | K8s State | Pod | `container.last_terminated_reason: "Error"`, `exit_code: 2` | 提供容器退出的直接原因代码与状态，指向应用层崩溃而非资源耗尽 |
| 3 | Logging | Elasticsearch | `http_status: 500`, `message: "runtime process exiting"`, `path: "/work"` | 确认应用进程在处理 `/work` 请求时返回 500 后终止，且未捕获内存异常 |
| 4 | Tracing | Deepflow | `HTTP GET /work`, `response_code: 200`, `occurrence_count: 9` | 显示该接口在 19:54 至 20:16 期间存在多次成功请求，说明故障由特定条件触发而非服务完全不可用 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 2 → 9` | 通过多时间窗口（51 个样本）观测到重启频次呈上升趋势 |

上述证据链显示：日志中 500 错误直接伴随进程退出行为；Metric 显示重启次数随时间增加；K8s Event 证实退避循环已持续 26 分钟。Tracing 中存在的成功请求进一步限定故障非全局性宕机，而是特定请求下的应用未捕获异常。

## 🎯 根因分析 · g1

### 因果链

```text
应用业务逻辑在处理 /work 路径时抛出未捕获异常 → 容器应用进程以非零退出码 (Exit Code 2) 强制退出 → Kubernetes 重启策略触发，kubelet 进入指数退避重启循环 → Pod 状态持续表现为 CrashLoopBackOff
```

### 根因结论

已确认的根因为：**应用代码在处理 `/work` 请求时发生未捕获的内部错误（HTTP 500），导致 Python 进程直接退出（runtime process exiting），进而触发 kubelet 的重启循环（CrashLoopBackOff）**。

支撑证据：
- 日志明确记录进程因 HTTP 500 错误后执行退出 (`fact-778e3ba9615a`, `fact-521de38f63f2`)；
- K8s 事件确认退避循环已持续 26 分钟且次数达 112 次 (`fact-d07dc7bd9aec`)；
- 容器退出码为 2 且原因标记为 Error (`fact-c0be162cdfbf`, `fact-1286c61548f7`)；
- 监控数据显示 Pod 重启次数在 20 分钟内从 2 次增至 9 次 (`fact-1e8699ca0101`)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 19.2s
├─ 并发证据采集: 71.8s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 71.8s (Evidence 56.5s, RCA 15.2s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
