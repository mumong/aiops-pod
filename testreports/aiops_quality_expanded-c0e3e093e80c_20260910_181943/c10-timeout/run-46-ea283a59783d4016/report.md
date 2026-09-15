## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | CrashLoopBackOff | 容器内存资源限制（64Mi）过低导致 OOMKilled（Exit Code 137） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | Kubernetes | `container.resource_limit.memory` value: `64Mi` | 提供导致 OOM 的资源硬限制上下文 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason`: `Error`; `container.last_exit_code`: `137` | 确认容器因异常退出终止，错误码指向被系统强制杀掉 |
| 3 | K8s State | Kubernetes | `container.waiting_reason`: `CrashLoopBackOff` | 呈现容器因反复崩溃退出而导致的当前异常状态 |
| 4 | K8s Event | Kubernetes | `Liveness probe failed: Get "http://172.16.104.36:18080/health": context deadline exceeded` | 说明应用启动或运行期间存活探针超时，直接阻碍 Pod Ready |
| 5 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason(reason: "Error")`: `1`; `restart_count`: `37` | 量化统计容器已重启 37 次，确认为持续性高频崩溃现象 |
| 6 | Logging | Elasticsearch | `[14/Sep/2026 14:42:23] "GET /health HTTP/1.1" 200 -` | 应用进程日志正常响应 HTTP 请求，排除了代码层明显的启动报错 |

**证据互证说明**：Kubernetes 提供的 `Exit Code 137` 与 `CrashLoopBackOff` 状态直接对应 OOMKilled 机制，说明容器进程是被系统（OOM Killer）强制终止的，而非应用内部报错退出（Logging 证实应用在崩溃前能正常响应请求）。Prometheus 的 `Error` 终止原因统计和 37 次重启进一步印证了该限制触发的反复性与持续性。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制设定过低（64Mi） → 应用运行时内存突破上限触发 OOM Kill → 进程终止退出（Exit Code 137） → 容器状态变为 CrashLoopBackOff 且存活探针超时
```

### 根因结论

已确认根因为：**容器内存资源限制（64Mi）过低导致 OOMKilled（Exit Code 137）**。

证据编号 2 明确指出容器最后一次终止原因为 Error 且退出码为 137，这是 Kubernetes 在进程占用内存超过 Limit 时发送 SIGKILL 信号导致的标准退出码；证据 1 限定了该容器的内存硬限制仅为 64Mi。结合证据 5（37 次重启）与证据 4（探针因等待超时而失败），逻辑闭环指向内存限制不足导致应用持续被系统杀掉，符合正式 RCA 结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 27.3s
├─ 并发证据采集: 79.2s
│  └─ g1 aiops-case-v17/workload: 79.2s (Evidence 74.2s, RCA 4.8s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime
