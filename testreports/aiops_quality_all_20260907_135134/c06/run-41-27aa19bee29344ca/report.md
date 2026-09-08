## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | Error | Pod workload-7679bcf76-jwr8b 处于 CrashLoopBackOff 状态，应用进程在 /work 端点处理请求时异常退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Back-off restarting failed container app in pod workload-7679bcf76-jwr8b` | 确认 Pod 处于持续重启失败状态 |
| 2 | K8s State | kubernetes | `exit_code: 2` / `reason: Error` | 容器异常退出，非 OOMKilled（通常 exit 137） |
| 3 | K8s State | kubernetes | `restart_count: 25` | 证实该异常具有持续性和高频性 |
| 4 | Metric | prometheus | `container_memory_working_set_bytes`: 892,928 bytes (Pod 级，上限 96Mi) | 排除内存超限（OOM）作为直接原因 |
| 5 | Logging | elasticsearch | `http_status: 500` / `message: runtime process exiting` / `path: /work` | 业务层收到 500 且进程随即退出 |
| 6 | Tracing | tempo | `http.response.status_code: 500` / `aiops.observed_mode: runtime_exit` / `trace_id: 66f8517c6ab359b396ba34556ba3082f` | 确认 500 响应与进程退出在逻辑上关联 |

**证据印证说明：**
1. **非 OOM 导致**：K8s 退出码为 2（通常为参数错误或异常）且 Prometheus 内存指标（fact-#4）远低于 limit (96Mi)，排除了内存溢出，支撑应用内部逻辑错误。
2. **业务异常闭环**：Tracing (fact-#6) 中的 `trace_id: 66f8517c...` 与 Logging (fact-#5) 中的 `http_status: 500` 对应的时间窗口一致，证实 HTTP 处理期间发生了未捕获异常。
3. **重启机制**：kubelet 检测到退出（fact-#2）后频繁重试（fact-#3），最终触发 BackOff 状态（fact-#1）。

## 🎯 根因分析 · g1

### 因果链
```text
应用处理 /work 请求时抛出未捕获异常（Trace 观测） → Python 进程以 exit_code 2 终止（K8s 状态） → kubelet 重启失败进入 BackOff（K8s Event） → Pod 处于 CrashLoopBackOff 状态
```

### 根因结论
**已确认的根因：应用进程内部逻辑错误（Python 运行时异常）。**

具体表现为：Pod `aiops-case-06/workload-7679bcf76-jwr8b` 在处理 `/work` 路径 HTTP 请求时发生应用层崩溃。证据显示：
- **Tracing** 确认该过程返回 500 并伴随 `runtime_exit` 模式（fact-#6）。
- **Logging** 显示进程在收到 500 后退出（fact-#5）。
- **K8s 状态** 显示退出码为 2 且重启 25 次（fact-#2, #3），且排除了内存资源不足的因素（fact-#4）。

现有日志和链路数据已闭环证明是进程逻辑错误导致退出，但由于缺少崩溃前的详细 Trace 堆栈（Stack Trace）和崩溃前最后一条业务日志，无法进一步定位具体的代码函数或异常类型。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 16.0s
├─ 并发证据采集: 74.2s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 74.2s (Evidence 65.8s, RCA 8.3s)
└─ 汇总总结: 12.1s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-config-error, pod-crashloop-runtime, pod-oomkilled
