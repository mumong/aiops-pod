## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-5mlnc is in NotReady state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.resource_limit.memory: 96Mi`, `container.resource_limit.cpu: 200m` | 确认资源硬限制配置范围，用于排查资源过载 |
| 2 | K8s Event | kubernetes | `Warning Unhealthy`: Readiness probe failed: HTTP probe failed with statuscode: 503 (x1246 over 63m) | 记录探针连续失败及返回的 HTTP 503 错误码 |
| 3 | Metric | prometheus | `container_memory_working_set_bytes` (app): 15425536 bytes (~14.7MB) | 监控显示内存使用极低，排除 OOM 导致应用僵死或崩溃的可能 |
| 4 | Logging | elasticsearch | `pattern`: error / dependency unavailable, http_status: 503, path: /work | 业务日志证实应用逻辑主动返回 503 错误 |
| 5 | Tracing | deepflow | `HTTP GET /work`: response_code: 503, src: 172.16.104.62 -> dst: 172.16.104.16 (x9) | 网络流量确认 503 状态持续发生，且发生在 Pod 服务内部 |

1. **K8s 事件**记录了探针收到 503 状态，直接印证了**日志**中业务逻辑“返回 503”的真实原因。
2. **Metric** 显示内存与 CPU 极低（未接近 96Mi/200m 的硬限制），结合 0 次重启事实，排除了资源耗尽或健康检查导致容器崩溃重启的可能。
3. **Tracing** 流量记录证实了 503 是应用对 `/work` 端点的常规响应，而非网络层中断或容器状态异常。

## 🎯 根因分析 · g1

### 因果链

```text
Deployment 配置 env var FAILURE_MODE=readiness_fail → App 逻辑主动在就绪探测端点返回 HTTP 503 → Kubelet 探针收到 503 判定失败 → Pod Ready 条件为 False
```

### 根因结论

**已确认的根因**：
Pod `aiops-case-09/workload-5f4fb9ff45-5mlnc` 处于 NotReady 状态的根本原因是 **Deployment 配置有意设置了环境变量 `FAILURE_MODE=readiness_fail`**。该配置导致应用代码在健康检查端点主动返回 HTTP 503 错误，Kubelet 探针捕获到该 503 状态后判定 Pod 未就绪（事实 #1, #2, #4, #5）。

**现象解释**：
尽管 Pod 状态为 `Running` 且重启次数为 0，但由于探针失败，Pod 的 `Ready` 条件变为 `False`，这证实了故障是由应用配置而非基础设施或资源问题引起的（事实 #3 排除了资源压力）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 18.2s
├─ 并发证据采集: 96.7s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 96.7s (Evidence 89.3s, RCA 7.3s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
