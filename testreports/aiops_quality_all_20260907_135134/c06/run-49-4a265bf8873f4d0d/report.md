## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Pod workload-7679bcf76-jwr8b 处于 CrashLoopBackOff 状态，重启 28 次。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 状态 `CrashLoopBackOff`，最后退出码 `exit_code: 2` | 直接表征应用进程非正常崩溃并触发重启 |
| 2 | K8s Event | Kubernetes | `BackOff restarting failed container app` (x544 over 121m) | 证实容器已进入高频重启循环，累计重启 28 次 |
| 3 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason{reason="Error"}` 值为 1 | 量化证实容器最后一次终止原因为 Error，与 K8s 状态对应 |
| 4 | Logging | Elasticsearch | `http_request` 错误日志 (2 次)，包含 `http_status: 500`, `message: "runtime process exiting"` | 捕捉到进程崩溃前的关键动作：处理请求后返回 500 并退出 |
| 5 | Tracing | Deepflow | HTTP Flow `GET /work` 返回 `response_code: 500` (5 次)，耗时 4450-5921μs | 独立观测到应用服务层返回 500，证实业务逻辑执行失败 |

**证据关联说明：**
K8s 的 `CrashLoopBackOff` 和 `exit_code: 2` (条目 1, 2) 证实了应用崩溃的事实；日志条目 (条目 4) 中的 `"runtime process exiting"` 与 Deepflow 追踪到的 `500` 响应 (条目 5) 结合，构成了因果闭环：应用在处理 `/work` 请求时发生内部错误并主动退出，而非被系统 OOM 等外部因素杀死。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理 /work 请求时发生内部业务错误 (http_status=500) → 应用记录 "runtime process exiting" 并异常退出 (exitCode 2) → Kubernetes 容器运行时检测到非零退出码并触发重启 → 频繁重启导致 CrashLoopBackOff
```

### 根因结论

已确认根因：**应用进程处理 `/work` 请求时发生内部错误，记录日志并异常退出，导致容器启动失败。**

该结论由以下事实相互印证：
1.  **应用层证据**：Deepflow 追踪到 `GET /work` 返回 500 (条目 5)，且 Elasticsearch 日志在相同时间窗口内记录了 `http_status: 500` 及 `runtime process exiting` (条目 4)。
2.  **系统层证据**：Kubernetes 显示容器最后退出码为 2 (条目 1)，Metric 显示终止原因为 Error (条目 3)，证实进程非正常终止而非健康存活。
3.  **现象层证据**：Pod 处于 `CrashLoopBackOff` 状态 (条目 1, 2)，且重启次数已达 28 次 (条目 2)。

目前**证据不足**的部分：导致 `/work` 请求返回 500 的具体业务逻辑错误或依赖缺陷原因（如代码 Bug、配置错误或下游服务不可用），现有数据未包含详细的堆栈信息（Stack Trace）或更细分的依赖调用链路。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 16.0s
├─ 并发证据采集: 66.5s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 66.5s (Evidence 57.3s, RCA 9.0s)
└─ 汇总总结: 11.2s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
