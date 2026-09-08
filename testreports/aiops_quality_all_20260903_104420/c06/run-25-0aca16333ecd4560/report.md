## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-w9s9c处于CrashLoopBackOff状态，容器反复以exitCode=2退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.last_terminated_reason: Error; container.waiting_reason: CrashLoopBackOff; container.last_exit_code: 2 | 确认容器因应用层错误退出并陷入重启循环 |
| 2 | K8s Event | kubernetes | Back-off restarting failed container app in pod workload-7679bcf76-w9s9c_aiops-case-06(x2246 over 54m) | 证实故障已持续超过 54 分钟，呈现长期不可用状态 |
| 3 | Logging | elasticsearch | pattern: 'http_request' level=error, message='runtime process exiting', http_status=500, path='/work', service='aiops-lab-workload' (occurrence_count: 5) | 显示应用在处理 /work 请求时返回 500 并主动终止进程，直接触发 Exit Code 2 |
| 4 | Logging | elasticsearch | pattern: 'http_request' level=info, message='request completed', http_status=200, path='/work' (occurrence_count: 3) | 证实故障是间歇性的（非全量失败），属于应用层面的逻辑或资源异常 |
| 5 | Tracing | deepflow | flow: GET /work response_code=500 (occurrence_count: 3, trace_ids: 5ece3a3567c00350affa4aa671974916, a20983a0df407fabfebf02a857a821f0, 00775f8b4349217aaa79618a772f0c9f) | 确认 L7 网络层记录到 500 状态码，且 trace_id 与日志中的错误模式匹配 |
| 6 | Tracing | deepflow | flow: GET /work response_code=200 (occurrence_count: 6, trace_ids: faf9cab3241d28fa6fb3be64fa088632, 97a75c073642b491e78d960ba0ad27a4, b108f94420f321786f588771ea8c124d, dd9d5506e571f94d00a178756bbf164d, 1dd0390e01743daee89421c7f5eee5fc) | 确认流量在正常路径下能成功返回 200，排除网络层拦截或路由配置错误 |

**证据综合分析：**
Kubernetes 层面（#1, #2）显示容器因非零退出码反复重启，处于 CrashLoopBackOff 状态。Logging（#3）与 Tracing（#5）在相同的 `/work` 接口路径上交叉印证了 500 错误和进程退出现象。Tracing 中成功返回 200 的记录（#6）与部分成功的日志（#4）共同证实了该故障为应用内部处理逻辑的间歇性失败，而非基础设施或网络层的硬性阻断。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理 /work 接口发生内部异常（未体现具体类型） → 返回 HTTP 500 并调用进程退出 → Exit Code 2 触发 K8s 重启策略 → CrashLoopBackOff
```

### 根因结论

已确认根因：**应用业务逻辑异常导致请求失败并主动退出。**
应用在处理 HTTP 请求 `GET /work` 时发生未捕获的运行时错误，导致进程主动终止（`exitCode=2`），Kubernetes 随后将其重启并触发 `CrashLoopBackOff`（证据 #1, #3, #6）。

**证据不足说明：**
导致 `/work` 返回 500 的具体异常类型（如内存溢出、空指针或第三方依赖故障）在日志和 Trace 中均未体现，无法进一步定位至具体的代码行或底层原因。

---

## 📊 性能统计

```text
├─ 总耗时: 3.7m
├─ 问题定位: 35.9s
├─ 并发证据采集: 171.8s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 171.8s (Evidence 159.1s, RCA 12.5s)
└─ 汇总总结: 14.5s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime
