## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod NotReady |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod Phase: Running; Ready: False (ContainersNotReady); Reason: app container not ready | 确认应用容器已启动但健康检查未通过，处于 NotReady 状态 |
| 2 | K8s Event | kubernetes | Warning Unhealthy: Readiness probe failed: HTTP probe failed with statuscode: 503 (x2390 over 119m) | 提供 Readiness 探针长期失败的直接证据，且为 HTTP 503 错误 |
| 3 | Metric | prometheus | kube_pod_container_status_restarts_total: 0 (container: app) | 排除应用进程崩溃重启导致的不健康状态，确认非 OOMKilled 或 CrashLoopBackOff |
| 4 | Logging | elasticsearch | 模式: `http_request [error] dependency unavailable, http_status: 503, path: /work` (连续 14 条记录，时间窗 02:32:03 - 02:32:51) | 证实应用自身返回 503 状态码，且明确归因为依赖服务不可用，与探针失败原因一致 |
| 5 | Tracing | deepflow | 聚合 13 条等价的 GET /work HTTP Flow，响应码均为 503，从源 172.16.104.62 发往 Pod IP 172.16.104.16 | 通过 L7 层面观测验证了外部或侧边请求在应用层被拦截并返回 503，与探针行为吻合 |
| 6 | K8s Config | kubernetes | CPU 限制 200m, 内存限制 96Mi, 请求内存 24Mi | 资源配额配置正常，日志中 `allocated_mib` 均为 0 也表明未发生资源耗尽 |

**证据综合：**
K8s 事件与探针记录（#1, #2）明确显示了 `HTTP 503` 这一现象；日志（#4）揭示了这一现象的内部成因是“依赖不可用”并返回了 503；Tracing 数据（#5）从网络流转视角独立验证了 GET /work 路径持续返回 503；监控重启次数为 0（#3）排除了进程级故障。多源数据高度自洽，形成闭环。

## 🎯 根因分析 · g1

```text
应用程序底层依赖服务不可用 → 业务逻辑拒绝服务并返回 HTTP 503 → Pod Readiness 探针（HTTP GET /work）连续失败 → Pod 状态变更为 NotReady（Ready=False）
```

**根因结论：**
已确认根因为**应用业务逻辑层面的故障**（应用依赖不可用）。
1. **现象机制**：应用代码捕获到依赖层（如数据库或上游 API）不可用的情况，并主动向调用方（包括集群的 Readiness 探针）返回 `HTTP 503` 状态码（证据 #2, #4, #5）。
2. **最终表现**：由于探针长期收到非 2xx 状态码，Kubernetes 判定应用容器健康检查失败，进而将 Pod 的 `Ready` 状态置为 `False`，阻止流量进入该 Pod（证据 #1, #2）。
3. **边界**：故障并非由资源耗尽、OOM 或网络配置（CNI/Calico）引起（证据 #3, #6, #2 中的 PodIP 信息正常）。目前缺乏决定性的底层拓扑或依赖方指标来进一步确认具体是哪个依赖（如特定数据库或缓存）不可用（属于未知项）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.8m
├─ 问题定位: 17.8s
├─ 并发证据采集: 135.6s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 135.6s (Evidence 125.7s, RCA 9.7s)
└─ 汇总总结: 12.4s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
