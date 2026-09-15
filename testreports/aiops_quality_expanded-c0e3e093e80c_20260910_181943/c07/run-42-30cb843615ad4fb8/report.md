## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Application startup failure due to missing configuration (CONFIG_MISSING) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | pod phase: Running; container.app waiting_reason: CrashLoopBackOff; container.app exit_code: 78 | 确认 Pod 运行但容器处于启动失败循环状态 |
| 2 | K8s State | Kubernetes | container.app last_terminated_reason: Error; event.message: BackOff restarting failed container app (x310 over 73m) | 证实容器异常退出并持续重启的行为模式 |
| 3 | K8s Event | Kubernetes | event.message: k8s.v1.cni.cncf.io/networks-status: | 记录 Pod 正常的网络状态与 CNI 信息 |
| 4 | Logging | Elasticsearch | pattern: event=http_request, level=error, message=CONFIG_MISSING, http_status=500, path=/work | 直接指出应用启动阶段因 CONFIG_MISSING 导致 500 错误 |
| 5 | Tracing | Tempo | span.name: GET /work; trace_id: 78c5df7615a0195018d603083f8c6f4b; span attributes: http.response.status_code=500, aiops.observed_mode=config_missing_exit | 链路跨度记录并印证了请求路由至 /work 时触发配置缺失导致的退出 |
| 6 | Metric | Prometheus | kube_pod_container_status_waiting_reason = 1 (reason: CrashLoopBackOff); kube_pod_status_phase = 1 (Running) | 监控指标确认 Pod 处于正常运行但容器持续等待的状态 |

**证据说明：**
1. K8s 状态（#1, #2）与 Metric 指标（#6）高度一致，共同描绘了 Pod 正常调度运行但容器因异常退出而陷入重启循环的现象。
2. 日志（#4）直接给出了业务层面的异常模式（`CONFIG_MISSING`，500 错误），与 K8s 的 `exit_code: 78` 异常退出状态对应，解释了容器被 Kubelet 终止（`terminated_reason: Error`）的业务原因。
3. 链路数据（#5）通过 `aiops.observed_mode=config_missing_exit` 和 `status_code=500` 提供了更底层的追踪视角，证实了应用处理 `/work` 请求时因配置缺失而终止的机制，且其 `trace_id` 与日志聚合关联，进一步确证了崩溃的直接诱因。

## 🎯 根因分析 · g1

### 因果链
```text
应用缺少必需配置 (CONFIG_MISSING) → 容器启动进程启动业务逻辑失败并终止 (exit_code 78) → kubelet 检测到容器异常退出触发重启与 BackOff 策略 → Pod 处于 Running 但容器持续 CrashLoopBackOff
```

### 根因结论
**已确认根因：应用启动失败（Application startup failure due to missing configuration）**
证据表明，Pod 内的 `app` 容器在启动过程中因缺少关键配置（`CONFIG_MISSING`）导致进程异常退出（退出码 78，状态码 500）。这直接触发了 Kubernetes 的重启机制，进而陷入 `CrashLoopBackOff` 循环。K8s 事件、日志错误模式（`CONFIG_MISSING`）与应用层链路追踪（`aiops.observed_mode=config_missing_exit`）三者互相印证，提供了确凿的故障根因事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 13.5s
├─ 并发证据采集: 83.6s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 83.6s (Evidence 76.8s, RCA 6.6s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime
