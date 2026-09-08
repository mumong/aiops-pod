## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod `aiops-case-09/workload-5f4fb9ff45-cfzz6` 持续处于 NotReady 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` | `Unhealthy` Warning: Readiness probe failed: HTTP probe failed with statuscode: 503 (持续 2m52s, 累计 2182 次) | 确认应用层健康检查失败，是导致 Pod 状态异常的直接入口。 |
| 2 | K8s State | `kubernetes` | `ContainersReady/Ready` 状态为 `False`，原因 `ContainersNotReady`，消息指向容器 `app` | 确认集群层面观察到容器未就绪，与 Probe 结果一致。 |
| 3 | K8s State | `kubernetes` | Pod 整体 `phase` 为 `Running`，容器 `status` 为 `Running`，`restart_count` 为 0 | 排除容器崩溃 (CrashLoopBackOff) 或启动失败，确认是运行时逻辑拒绝服务。 |
| 4 | K8s Config | `kubernetes` | `app` 容器内存 Request `24Mi`，Limit `96Mi`；CPU Request `20m`，Limit `200m` | 提供资源基线，用于对比 Metrics 是否出现 OOM 或 Resource Pressure。 |
| 5 | Metric | `prometheus` | `container_memory_usage_bytes`: `16568320` bytes (约 15.8MB) | 内存使用量远低于 96Mi 上限，排除内存不足 (OOMKilled) 导致的拒绝服务。 |
| 6 | Logging | `elasticsearch` | 模式 `dependency unavailable` (http_status: 503)，聚合 14 次，`numeric_fields` 显示 `allocated_mib` 在观察窗口内保持 0 不变 | 确认应用日志明确记录了 503 错误及“依赖不可用”上下文，且非因自身资源分配失败引发。 |
| 7 | Tracing | `tempo` | Span `GET /work`，`http.response.status_code: 503`，`aiops.observed_mode: readiness_fail` (trace: `5a23e0c8...`) | 追踪数据证实 `/work` 端点返回 503，且该行为是触发 readiness 失败的根本原因。 |
| 8 | Tracing | `deepflow` | L7 Flow (HTTP GET /work) 返回 503，响应状态 3，发生时间 `03:15:26` 至 `03:38:56`，持续 9 次 | 网络流量层面交叉验证了应用对 `/work` 端点的持续 503 响应。 |

**证据小结**：
1. 应用日志与追踪数据互相印证：`dependency unavailable` 的日志模式与 `GET /work` 端点返回 503 的 Span/Flow 一致。
2. 性能指标排除资源瓶颈：当前 15.8MB 的内存使用和 0 次重启，证明 503 错误并非由 OOM 或 CPU 饥饿引起。
3. 故障定位清晰：所有证据均指向 `/work` 端点逻辑返回 503 导致 Readiness Probe 失败。

## 🎯 根因分析 · g1

### 因果链

```text
下游依赖不可用 → 应用 /work 端点返回 HTTP 503 → Readiness Probe 持续失败 → Pod 状态标记为 NotReady
```

### 根因结论

**已确认根因**：应用服务在 `/work` 端点由于“下游依赖不可用”而返回 `HTTP 503`，导致 Kubernetes Readiness Probe 判定失败。

*   **依据**：
    *   **现象**：Pod `aiops-case-09/workload-5f4fb9ff45-cfzz6` 处于 `NotReady` 状态，连续 2000+ 次 Readiness Probe 返回 `503` (事实 1, 2)。
    *   **机制**：应用日志记录了 `dependency unavailable` 且 `http_status: 503` (事实 6)；追踪数据确认 `GET /work` 端点返回 `503` (事实 7, 8)。
    *   **排除**：容器正常运行、内存充足、无重启，排除资源受限导致的启动失败 (事实 3, 4, 5)。

**未确认部分**：具体的“下游依赖组件名称”及该依赖不可用的具体原因 (如网络不通、服务宕机、配置错误等) 在现有证据中缺失。

---

## 📊 性能统计

```text
├─ 总耗时: 2.9m
├─ 问题定位: 28.8s
├─ 并发证据采集: 131.1s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 131.1s (Evidence 121.2s, RCA 9.6s)
└─ 汇总总结: 15.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
