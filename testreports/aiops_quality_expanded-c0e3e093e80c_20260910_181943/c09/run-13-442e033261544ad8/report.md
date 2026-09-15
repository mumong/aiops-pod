## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | 应用依赖资源（如数据库连接或外部服务）不可用，导致服务启动后无法正常初始化，Readiness Probe因HTTP 503持续失败，Pod处于NotReady状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Condition | `Ready=False` (reason: `ContainersNotReady`), `ContainersReady=False` | 确认 Pod 当前处于不可用状态，容器未被调度为就绪。 |
| 2 | K8s Event | Readiness Probe | `HTTP probe failed with statuscode: 503` (over 34m, x623) | 证明服务在启动后长时间无法通过就绪检查。 |
| 3 | Logging | L7 Error Log | `dependency unavailable`, http_status=503, path=/work (occurrence_count: 8, first: 01:07:26, last: 01:08:00) | 提供应用层具体错误信息，指向依赖资源不可用且持续复现。 |
| 4 | Tracing | Deepflow L7 Flow | dst_ip=172.16.104.16, protocol=HTTP, response_code=503 (occurrence_count: 9, first: 09:03:21, last: 09:05:40) | 证实该 Pod 对外部请求/探针返回 503 的状态，且流量数据在日志时间窗口后仍持续存在。 |
| 5 | Metric | Restart Count | `kube_pod_container_status_restarts_total=0` | 确认容器未经历重启，排除了因频繁 OOM/Kill 导致的崩溃重启循环。 |
| 6 | K8s Config | Resource Limits | CPU: `200m`, Memory: `96Mi` | 提供容器资源上下文，确认资源限额并非导致服务启动失败的主因（且未发生 OOM）。 |

**证据互证说明：**
*   **现象与根因关联**：K8s 事件 `503` (证据#2) 与日志中的 `dependency unavailable` (证据#3) 直接对应，确认了就绪探针失败的具体业务原因为后端依赖缺失。
*   **多维度状态一致**：Deepflow 流量数据 (证据#4) 与 K8s Probe 日志 (证据#2) 在时间窗口上高度重叠，且均指向目标 IP `172.16.104.16` 返回 503，证实该 Pod 确实在运行中但应用层未就绪。
*   **排除其他干扰**：Pod 处于 `Running` 状态且重启计数为 0 (证据#1, #5)，排除了容器启动失败或崩溃重启的可能性，说明问题出在应用初始化阶段或运行时依赖上。

## 🎯 根因分析 · g1

```text
依赖资源（数据库/外部服务）不可用 → 应用启动初始化失败 → Readiness Probe 持续返回 HTTP 503 → Pod Ready 状态为 False
```

**已确认的根因：**
应用的启动依赖于特定的外部资源（如数据库或第三方服务），但由于这些依赖资源在 Pod 启动时不可用，导致应用无法正常完成初始化。应用进程虽然处于运行状态（Running），但由于未就绪，Readiness Probe 持续返回 HTTP 503 错误。Kubernetes 检测到探针失败后，将 Pod 标记为 `NotReady`，导致流量无法被正确路由。

**证据引用：**
*   日志明确指出了 `dependency unavailable` 和 `statuscode: 503` (证据#3, #2)。
*   K8s 事件确认探针长时间失败且未发生容器重启 (证据#2, #5)。
*   流量监控证实了请求到达该 Pod 后被拒绝（503），证明应用本身存活但服务不可用 (证据#4)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 27.3s
├─ 并发证据采集: 70.7s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 70.7s (Evidence 63.4s, RCA 7.1s)
└─ 汇总总结: 12.4s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
