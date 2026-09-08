## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-cfzz6 状态为 NotReady，就绪探针持续失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (持续 87m) | 确认就绪探针因 HTTP 503 持续失败，这是 Pod 变为 NotReady 的直接原因 |
| 2 | K8s State | kubernetes | Pod Ready 条件：`False` (ContainersNotReady)，Restart Count: `0` | 确认 Pod 虽在运行但处于不健康状态，且未发生容器重启 |
| 3 | Logging | elasticsearch | `dependency unavailable` (http_status: 503, path: /work)，发生 8 次，时间 19:20:14-19:20:40 | 日志记录应用内部业务逻辑因依赖不可用返回 503，解释了探针失败的具体成因 |
| 4 | Tracing | Deepflow | 17 个等价 L7 Flow 显示 `dst_ip: 172.16.104.26` (本 Pod IP) 的 HTTP GET /work 请求均返回 `response_code: 503` | 独立网络流证据证实请求进入 Pod 后均被应用自身以 503 拒绝 |
| 5 | Tracing | Tempo | Trace `d882babe...` 和 `1d6f8dd4...` 确认请求在 `aiops-lab-workload` 服务内处理并返回 503 | 验证了应用服务自身就是导致 HTTP 503 的源头 |
| 6 | Metric | Prometheus | `container_memory_usage_bytes` 峰值 `16.9MB`，远低于内存限制 `96Mi` | 排除因内存耗尽导致的应用无响应或 OOM 重启 |

**证据关联性说明：**
证据 1 和 2 确立了故障现象（K8s 层面 NotReady）；证据 3、4、5 在应用层和流层高度一致地证明了应用自身返回 503 响应，排除了网络层或服务网格拦截导致 503 的可能；证据 6 排除了资源耗尽导致的故障。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部后端依赖不可用 → 应用服务 /work 端点抛出 503 (dependency unavailable) → Kubernetes 就绪探针检测到 HTTP 503 → Pod 被标记为 NotReady (Ready=False)
```

### 根因结论

**已确认的根因：** 
Pod `workload-5f4fb9ff45-cfzz6` 内的应用服务在发起对**内部/外部下游依赖**的调用时，因该依赖不可用，导致应用自身向客户端（即 K8s 就绪探针）返回了 HTTP 503 状态码。这种持续的 HTTP 503 响应触发了 K8s 就绪探针的失败判定，从而将 Pod 状态标记为 NotReady。

**证据支撑：**
*   **日志层面**：明确记录 `dependency unavailable` 且伴随 `http_status: 503` (证据 #3)。
*   **流与追踪层面**：Deepflow 和 Tempo 数据证实，发往该 Pod 的 /work 请求确实由应用自身处理并返回了 503 (证据 #4, #5)。
*   **排除其他资源因素**：内存监控显示资源使用正常，排除了资源不足导致的应用崩溃或无响应 (证据 #6)。

**缺失的未确认事实：**
根据输入事实，日志仅记录了 `dependency unavailable` 的通用消息，**并未指明**具体是哪一个下游依赖服务（如特定的数据库、API 网关或其他微服务）不可用，也未提供该下游依赖的 IP 或域名信息。因此，虽然应用返回 503 的原因已确认为“下游依赖不可用”，但“究竟是哪个下游服务”以及“该下游服务为何不可用”这一更深层的根因证据不足。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 33.7s
├─ 并发证据采集: 105.2s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 105.2s (Evidence 95.0s, RCA 10.1s)
└─ 汇总总结: 13.6s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
