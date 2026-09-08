## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-fkzvn` | CrashLoopBackOff | Pod aiops-case-07/workload-dff5cbc6b-fkzvn 处于 CrashLoopBackOff 状态，容器重启 10 次。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: "CrashLoopBackOff"; `last_terminated_reason`: "Error"; `restart_count`: 10 | 确认应用容器持续崩溃并重启的症状 |
| 2 | K8s Event | Kubernetes | `BackOff`: "Warning  BackOff         3m30s (x109 over 28m)  kubelet            Back-off restarting failed container app" | 显示集群层面的重启抑制与频繁重试现象 |
| 3 | K8s Config | Kubernetes | `resource_request.memory`: "24Mi"; `resource_limit.memory`: "96Mi"; `resource_request.cpu`: "20m"; `resource_limit.cpu`: "200m" | 内存资源受限，且配置了硬上限 |
| 4 | Logging | Elasticsearch | `CONFIG_MISSING` (8次): `http_status`: 500; `path`: "/work"; `service`: "aiops-lab-workload"; `time_range`: 14:38:47 - 15:02:39; `numeric_fields`: `allocated_mib`: 0.0 | 揭示应用启动失败的具体原因：在访问 `/work` 时因配置缺失返回 500 |
| 5 | Tracing | Tempo | `span name`: "GET /work"; `http.request.method`: "GET"; `http.response.status_code`: 500; `attributes.aiops.observed_mode`: "config_missing_exit"; `trace_id`: "261d9e55a970c37b1d05368956e13953" | 精确捕获到触发错误的特定 HTTP 调用及其上下文 |
| 6 | K8s State | Kubernetes | `container.last_exit_code`: 78 | 确认应用进程因该错误导致的退出状态码 |
| 7 | Tracing | Deepflow | HTTP Flow: `GET /work` `172.16.104.27` -> `172.16.104.7`, `response_status`: 3 (error), `duration_us`: 4929 - 17495 | 从网络层佐证了错误的 HTTP 请求流向与耗时 |

证据分析：
Kubernetes 状态显示容器处于 CrashLoopBackOff，退出码为 78。日志中 `CONFIG_MISSING` 错误与 Tempo Trace 中的 `aiops.observed_mode: "config_missing_exit"` 相互印证，证实应用因配置缺失在处理 `/work` 请求时抛出 500 错误并崩溃。Deepflow 流量数据与 Trace 的 `261d9e55a970c37b1d05368956e13953` 链路一致，确认了该错误触发的流量。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动后尝试加载配置 → 配置缺失触发 HTTP 500 错误 (CONFIG_MISSING) → 应用进程以退出码 78 终止 → Kubernetes 触发 CrashLoopBackOff 并重启
```

### 根因结论

**已确认的根因**：
应用启动后立即访问 `/work` 路径获取配置，但因配置缺失（`CONFIG_MISSING`）抛出 500 错误并退出（退出码 78），导致 Kubernetes 触发指数退避的 `CrashLoopBackOff` 状态。

**支撑证据**：
- **现象验证**：容器频繁重启 10 次且处于 `CrashLoopBackOff` 状态 (fact-001696a608d0, fact-eab2a0299cfa)；
- **失败机制**：日志显示重复的 `CONFIG_MISSING` 错误，且对应 HTTP 状态码 500 (fact-0bf8c10f8ebd)；
- **流程闭环**：Trace 数据显示该错误发生在 `GET /work` 请求中，且应用观察模式明确标记为 `config_missing_exit` (fact-10d9788ad8e5)；
- **退出确认**：应用进程最终因该错误以退出码 78 终止 (fact-370e7a3799fe)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 19.6s
├─ 并发证据采集: 50.4s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-fkzvn: 50.4s (Evidence 40.5s, RCA 9.7s)
└─ 汇总总结: 14.9s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-fkzvn**: pod-crashloop-runtime, pod-oomkilled, pod-config-error
