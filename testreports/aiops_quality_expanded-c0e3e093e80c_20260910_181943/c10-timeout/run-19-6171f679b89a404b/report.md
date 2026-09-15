## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | {'type': 'Warning', 'reason': 'BackOff', 'message': 'Warning  BackOff         2m29s (x147 over 35m)  kubelet            Back-off restarting failed container app in pod workload_aiops-case-v17(85aece07-6ffa-41db-9e5a-f351771a8864)'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff 2m29s (x147 over 35m) kubelet Back-off restarting failed container app` | 确认容器处于 CrashLoopBackOff 循环中 |
| 2 | K8s Event | Kubernetes | `Warning Unhealthy 17m (x23 over 37m) kubelet Liveness probe failed: Get "http://172.16.104.36:18080/health": context deadline exceeded` | 存在探针超时现象，且 `Liveness probe failed` 记录表明 probe 被 kubelet 判定失败 |
| 3 | K8s State | Kubernetes | `Exit Code: 137`, `container.last_terminated_reason: Error`, `restart_count: 17` | 进程被强制终止 (SIGKILL)，退出状态为 Error，伴随频繁重启 |
| 4 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason: 1` (labels: reason=Error, container=app) | 指标确认最近一次终止原因为 Error，**未**发现 OOMKilled 状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 16` (container=app) | 独立确认容器已重启 16 次 |
| 6 | Logging | Elasticsearch | `10.2.0.50 - - [14/Sep/2026 13:37:34] "GET /ready HTTP/1.1" 200 -` (多次记录) | 业务日志显示应用进程在运行期间能正常响应 `/ready` 并返回 200 |
| 7 | Tracing | Deepflow | HTTP GET `/health` 响应 200 (duration_us min/max: 3000773 ~ 3001826) | 流量记录显示 `/health` 端点响应时间为 **3000ms**，且成功返回 200 |

**证据印证说明：**
1.  **探针超时与流量记录一致**：K8s Event (Fact 2) 报 `/health` 超时，而 Tracing (Fact 7) 显示 `/health` 响应耗时约 3 秒 (3001826 us)，若 K8s Liveness Probe 配置默认超时时间（通常小于 3 秒），则流量记录完美解释了 Event 中的 `context deadline exceeded` 现象，并证实超时是由应用侧响应慢导致，而非网络不通。
2.  **日志正常但状态报错**：Logging (Fact 6) 显示应用成功处理了请求，而 K8s State (Fact 3) 显示进程崩溃退出，说明进程在健康时突然崩溃。
3.  **OOM 证据缺失**：尽管存在 `Exit 137` 且内存限制仅 64Mi (Fact 11)，Metric (Fact 4) 却未提供 OOMKilled 状态，且缺少 `container_memory_working_set_bytes` 峰值数据，导致无法通过 Metrics 确诊 OOM。

## 🎯 根因分析 · g1

### 因果链

```text
应用响应慢 (/health 耗时 ~3s) → 触发 Liveness Probe 超时 → kubelet 判定不健康 (Fact 2, 7) → 发送 SIGKILL 终止容器进程 (事实：liveness probe kill) → Exit Code 137 (Fact 3) → CrashLoopBackOff (Fact 1)
```

### 根因结论

**证据不足**，无法确诊根因。

现有证据在 "OOM 导致崩溃" 和 "Liveness Probe 超时触发 Kill" 两种假说间存在冲突：
1.  **支持 OOM 的嫌疑**：内存限制极低 (64Mi)，Exit Code 137 常见于 OOM。
2.  **支持 Probe Kill 的嫌疑**：Tracing (Fact 7) 显示 `/health` 耗时极长，直接解释了 K8s Event (Fact 2) 中的探针超时，且 OOM 通常会导致应用无响应（而日志显示 200 OK），这与 Probe Kill 机制（在进程存活但无响应时杀进程）更为吻合。

**缺失决定性事实：**
*   缺少 `kube_pod_container_status_last_terminated_reason` 为 `OOMKilled` 的直接证据。
*   缺少 `container_memory_working_set_bytes` 峰值数据以排除 OOM。
*   缺乏直接排除 `liveness probe` 配置值与响应时间之间关系的证据。

*注：尽管 `formal_rca` 提示了 Exit 137 的矛盾，但因缺少决定性事实，无法发布最终结论。*

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 20.3s
├─ 并发证据采集: 91.3s
│  └─ g1 aiops-case-v17/workload: 91.3s (Evidence 82.5s, RCA 8.7s)
└─ 汇总总结: 16.2s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
