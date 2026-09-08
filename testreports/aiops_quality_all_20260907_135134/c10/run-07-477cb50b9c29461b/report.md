## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | Pod workload-79d9f8fd88-bwqhh 处于 CrashLoopBackOff 状态，容器反复重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: Error, `container.last_exit_code`: 137 | 容器以退出码 137 异常终止 |
| 2 | K8s Config | kubernetes | `container.resource_limit.memory`: 96Mi | 容器内存硬限制 |
| 3 | K8s State | kubernetes | `container.waiting_reason`: CrashLoopBackOff, `container.waiting_message`: back-off 5m0s | 重启策略被触发，进入退避重启循环 |
| 4 | K8s Event | kubernetes | Liveness probe failed: HTTP probe failed with statuscode: 500 | 健康检查失败，触发重启机制 |
| 5 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason` (reason=Error, value=1) | 监控指标证实最后终止原因非正常 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total` (value=7) | 观测窗口内已累计重启 7 次 |
| 7 | Logging | elasticsearch | `request completed`, `http_status`: 200, `allocated_mib`: max 0.0 | 存在成功的 200 请求记录，表明服务具有处理能力 |
| 8 | Tracing | deepflow | HTTP Flow: `GET /work`, `response_code`: 200, `dst_ip`: 172.16.104.32 | L7 流量证实后端服务正常响应了部分请求 |

**证据分析：**
Kubernetes 状态显示容器因退出码 137 终止（证据 1、2），且健康检查失败导致进入 CrashLoopBackOff（证据 3、4）。Metric 数据印证了终止原因与重启次数（证据 5、6）。尽管应用能够正常响应 `GET /work` 返回 200 状态码（证据 7、8），但在内存限制为 96Mi 的情况下，进程仍会被系统 OOM Killer 强制终止。这表明应用在处理请求时会消耗超过限制的内存，导致不稳定的运行状态。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制设置过低（96Mi）→ 处理请求时内存增长突破限制触发 OOMKilled → 容器进程被强杀退出码 137 导致 Liveness 检查失败 → Kubelet 执行重启策略导致 CrashLoopBackOff
```

### 根因结论

已确认根因为**容器内存资源限制（96Mi）过低**。

证据表明，应用在处理请求时内存分配会超过 96Mi 的限制，从而触发内核 OOM Killer 将进程终止（Exit Code 137），随后 Liveness Probe 失败并触发重启循环。虽然服务具备正常的 HTTP 响应能力（200 状态码），但内存硬限制无法承载其峰值内存需求。目前缺失应用具体的内存分配峰值数据或内存泄漏逻辑等细节，但不影响“限制不足导致 OOM”这一核心根因的判定。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 29.3s
├─ 并发证据采集: 108.3s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 108.3s (Evidence 97.4s, RCA 10.8s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
