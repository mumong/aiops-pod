## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Pod workload-7679bcf76-jwr8b 处于 CrashLoopBackOff 状态，重启6次，退出码为 2。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | 容器 `app` 重启 6 次，退出码 `exit_code=2`，Pod 状态 `CrashLoopBackOff`，`Back-off restarting failed container` 事件累计 22 次 | 确定异常发生频率与容器当前的终止机制，证实应用处于死循环重启状态。 |
| 2 | Logging | `elasticsearch` | 发生 5 次 HTTP 500 错误日志：`event=http_request, message="runtime process exiting", path="/work", http_status=500`，发生在 `12:30:36Z - 12:36:52Z` | 证实主进程在特定接口触发致命错误后直接终止，是容器退出的直接原因。 |
| 3 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason=1` (CrashLoopBackOff)，`kube_pod_container_status_last_terminated_reason=1` (Error)，`kube_pod_container_status_restarts_total=6` | 外部监控指标从独立观测视角印证了 K8s 状态与日志结论，确认异常持续存在。 |
| 4 | Tracing | `deepflow` | 2 次针对 `/work` 的请求返回 HTTP `500`，客户端 IP 为 `172.16.104.59`，响应耗时 `11ms - 12ms` | 网络层面观测到请求在极短时间内返回 500 错误，与进程瞬间崩溃、无长时间阻塞的特征相符。 |
| 5 | Logging | `elasticsearch` | 3 次成功日志：`message="request completed", http_status=200, path="/work"`，发生在 `12:30:42Z - 12:36:50Z`，`allocated_mib` 始终为 0 | 排除内存超限 OOM（OOMKilled）作为主因的可能；证实应用能够处理部分请求，故障具有间歇性。 |

**证据关联说明**：
日志中的 `runtime process exiting` 错误（证据 #2）与 `deepflow` 中的 500 响应（证据 #4）发生时间窗口重合，确认为同一类应用运行时异常引发的请求失败。由于 `allocated_mib` 指标始终为 0（证据 #5），排除了资源限制导致的系统级拦截，锁定为应用代码或环境配置层面的内部崩溃。K8s 的 CrashLoopBackOff（证据 #1）及监控指标（证据 #3）则是该进程不断崩溃后的直接系统表现。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理 HTTP /work 请求时发生内部错误 → 记录 500 错误与 'runtime process exiting' 日志 → 主进程非正常退出 (Exit Code 2) → Kubelet 检测到容器崩溃并触发 CrashLoopBackOff
```

### 根因结论

**已确认根因**：应用运行时错误导致主进程异常退出。

该异常组 `g1` 的核心问题已得到确证。Pod `workload-7679bcf76-jwr8b` 中的 `app` 容器在处理 HTTP 请求时遭遇未捕获的内部错误，导致主进程异常终止（`Exit Code 2`）。

*   **支撑事实**：
    *   应用日志中频繁出现 `runtime process exiting` 伴随 HTTP 500 状态码，明确了崩溃发生在应用逻辑层（支持事实 `fact-266ef80f4fbc` 等）。
    *   网络层观测到对应请求在极短时间内返回 500（支持事实 `fact-089f2d40d83c`），印证了进程瞬间退出的特征。
    *   K8s 状态 `CrashLoopBackOff` 与重启次数 6 次（支持事实 `fact-0dcf3ba773fd`、`fact-4974efa91b88`）完全符合进程意外退出的生命周期表现。

*   **未决因素**：
    由于未收集到导致 HTTP 500 的具体 Python Traceback 堆栈信息（输入 `unknowns`），故障的精确代码行或具体触发条件（如特定参数缺失、外部依赖不可用）未能被确认，但这不影响当前容器崩溃这一主要异常状态的确立。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 24.4s
├─ 并发证据采集: 60.9s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 60.9s (Evidence 49.4s, RCA 11.4s)
└─ 汇总总结: 14.9s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
