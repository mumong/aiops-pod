## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Application application error (python3 /opt/aiops/server.py) causing HTTP 500 and immediate process exit (exit code 2) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.last_terminated_reason=Error; container.waiting_reason=CrashLoopBackOff | 确认应用容器处于异常重启状态 |
| 2 | K8s Event | kubernetes | BackOff: 2m26s (x157 over 37m) restarting failed container app | 证实进程频繁退出并触发指数退避，异常已持续约37分钟 |
| 3 | K8s State | kubernetes | container.last_exit_code=2 | 提供进程退出码，指向应用内部错误而非系统资源拦截 |
| 4 | K8s Config | kubernetes | request.memory=24Mi, limit.memory=96Mi, request.cpu=20m, limit.cpu=200m | 排除 OOMKill，资源请求和限制相对充裕且配置合理 |
| 5 | Metric | prometheus | kube_pod_container_status_waiting_reason(CrashLoopBackOff)=1; kube_pod_container_status_last_terminated_reason(Error)=1 | 独立时序指标交叉验证 K8s 状态，确认等待原因为 CrashLoopBackOff |
| 6 | Metric | prometheus | kube_pod_container_status_restarts_total (first=1.0, last=11.0, max=11.0, min=1.0) | 提供重启计数，反映容器在观察窗口内的剧烈震荡 |
| 7 | Logging | elasticsearch | repeated_log_pattern: event=http_request, level=error, message="runtime process exiting", http_status=500, path="/work", allocated_mib 0.0->0.0 | 捕获导致退出的具体日志模式，指向 HTTP 请求处理期间 Python 进程崩溃 |
| 8 | Tracing | deepflow | l7_flow: GET /work, src_ip=172.16.104.56, dst_ip=172.16.104.6, response_code=500, trace_id=6b940021b18df312738422d71af62239 | 捕获失败的请求流量，500 响应码与日志中的 HTTP 500 直接对应 |

**证据说明：**
* K8s 的 `CrashLoopBackOff` 状态（#1, #2）和 Metric 的 `CrashLoopBackOff` 指标（#5）互相印证了容器处于故障恢复循环中。
* 日志显示的 `"runtime process exiting"` 伴随 HTTP 500（#7）解释了 `exit_code=2`（#3）的根本来源。
* 追踪流量中的 `response_code=500`（#8）关联了日志错误发生时的具体业务请求（path="/work"），证实了 500 错误是应用崩溃的直接前置现象。

## 🎯 根因分析 · g1

### 因果链
```text
Application application error (python3 /opt/aiops/server.py) → HTTP 500 异常并立即退出 → exit code 2 → CrashLoopBackOff
```

### 根因结论
已确认根因为 **应用内部错误（Application Error）**。

具体机制如下：
应用容器在运行 Python 服务（`/opt/aiops/server.py`）时，在处理特定请求（如 `GET /work`）过程中发生未捕获异常或致命错误。该错误导致进程以 **exit code 2** 立即退出，并返回 **HTTP 500** 状态码。Kubernetes 检测到容器异常退出后，按预期策略进行重启，但因问题未修复，导致容器陷入频繁的 **CrashLoopBackOff** 循环。证据链中日志报错、退出码、K8s 状态及 Metric 指标均一致指向这一由应用自身引发的故障，排除了资源配置不足（如 OOM）或调度等基础设施层面的问题。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 23.3s
├─ 并发证据采集: 104.5s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 104.5s (Evidence 98.3s, RCA 6.0s)
└─ 汇总总结: 13.2s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
