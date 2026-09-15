## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod workload-7679bcf76-n5vp8 处于 CrashLoopBackOff 状态，容器重启14次，最后重启于2分7秒前。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning BackOff ... Back-off restarting failed container app` (fact-68df8c8eacf1) | 证实容器反复终止触发了 BackOff 机制 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason: Error`, `exit_code: 2` (fact-34cd0d7f452e, fact-644961f15719) | 直接指出应用进程以非零退出码终止 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (label: `reason: CrashLoopBackOff`), `restart_count=14` (fact-c23a4212988c, fact-3fa82927f40d) | 量化验证了当前的 CrashLoopBackOff 状态及累计重启次数 |
| 4 | Logging | elasticsearch | `http_request` ERROR: `runtime process exiting`, `http_status: 500` (fact-252eebff744f 等) | 记录了进程崩溃前最后的日志模式，确认了异常发生上下文 |
| 5 | Tracing | deepflow+tempo | Flow: `GET /work` `response_code: 500` (fact-26d949a3c83b); Span: `GET /work` `aiops.observed_mode: runtime_exit` (fact-fb39fa09688a) | 将 HTTP 500 响应与 `runtime_exit` 信号绑定，锚定了触发应用崩溃的具体操作路径 |

**证据说明**：Kubernetes 指标（#3）与状态（#2）一致确认了 `CrashLoopBackOff` 及 `Error` 终止原因；Logging（#4）与 Tracing（#5）相互印证了导致进程退出的具体请求路径（`GET /work`）及响应结果（500），共同支撑应用层崩溃这一结论。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码在 GET /work 处理期间抛出未捕获异常 → 进程以 exit code 2 终止 → 容器重启策略触发，BackOff 延迟增加 → Pod 状态变为 CrashLoopBackOff
```

### 根因结论

**已确认的根因**：应用代码在 `GET /work` 请求处理期间发生异常，导致 Python 进程以 `exit code 2` 强制终止。

该根因得到了以下证据的充分支撑：
- **异常触发路径**：Tracing 中的 `aiops.observed_mode: runtime_exit` (事实 #5) 结合 HTTP 500 响应，明确指向了应用层崩溃。
- **终止特征**：Kubernetes 状态的 `last_terminated_reason: Error` 与 `exit_code: 2` (事实 #2) 确认了非正常的进程退出行为。
- **持续影响**：Metric 中的 `restart_count=14` 及 `CrashLoopBackOff` 状态 (事实 #3) 验证了崩溃是持续发生的。

**未知项**：Python 异常的具体类型和代码行号（堆栈未打印），缺乏决定性的堆栈跟踪数据以定位源码行号。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 16.3s
├─ 并发证据采集: 83.6s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 83.6s (Evidence 74.8s, RCA 8.7s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
