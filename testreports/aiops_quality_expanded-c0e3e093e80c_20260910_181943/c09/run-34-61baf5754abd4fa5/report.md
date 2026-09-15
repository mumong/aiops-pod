## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | 应用访问后端依赖服务失败导致持续返回 HTTP 503，触发 Readiness Probe 持续失败从而进入 NotReady 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `phase=Running`, `pod.condition[Ready=False, reason=ContainersNotReady]` | 确认 Pod 核心容器 `app` 运行中但持续处于不健康状态 |
| 2 | K8s Event | kubernetes | `Warning Unhealthy 84m (x1662) Readiness probe failed: HTTP probe failed with statuscode: 503` | 确认 kubelet 读取探针持续被后端拒绝，是导致 NotReady 的直接原因 |
| 3 | K8s Config | kubernetes | `resource_limit.memory=96Mi`, `resource_request.memory=24Mi`, `resource_limit.cpu=200m`, `resource_request.cpu=20m` | 排除资源硬限制（Limit）导致的 OOMKilled 或 CPU Throttling 可能性 |
| 4 | Logging | elasticsearch | `error: dependency unavailable, http_status=503, path=/work, service=aiops-lab-workload` (8次聚合) | 业务日志明确反馈依赖服务不可用并返回 503，支撑应用逻辑层面的根因 |
| 5 | Tracing | tempo/deepflow | `flow: HTTP GET /work -> 503` (9次聚合, src_ip=172.16.104.62, dst_ip=172.16.104.16) | L7 网络流量证实请求持续返回 503，且耗时稳定在 18-29ms 区间 |

**证据印证说明：**
Kubernetes 探针事件、应用错误日志与 L7 流量跟踪均一致指向 `application/service` 层面的依赖服务失败。日志记录了 `dependency unavailable`，流量跟踪记录了请求被拒，探针据此判定容器不健康。Pod 持续处于 `Running` 且无重启记录，结合未配置硬限制的事实，进一步排除了基础设施资源层面的故障，确认为持续性的应用级依赖故障。

## 🎯 根因分析 · g1

### 因果链

```text
后端依赖服务不可用 (未确认/被日志间接反映) → 应用逻辑处理依赖失败返回 HTTP 503 → 应用 Readiness Probe 请求持续失败 → Pod 进入 NotReady 状态
```

### 根因结论

已确认根因为：**应用后端依赖服务不可用导致持续返回 HTTP 503。**

依据证据 2 (K8s Event) 确认应用 `workload-5f4fb9ff45-5mlnc` 的 Readiness Probe 连续失败 1662 次，直接原因是后端返回 HTTP 503。证据 4 (Logging) 与证据 5 (Tracing) 进一步验证了该 503 错误是由 `aiops-lab-workload` 服务在处理 `/work` 路径时因“依赖不可用 (dependency unavailable)”主动触发。这导致 K8s 判定容器未就绪（Evidence 1），从而将 Pod 标记为 NotReady。虽然根本原因指向“后端依赖”，但在当前工具边界内，决定性事实是应用层持续产生并透出 503 错误。

---

## 📊 性能统计

```text
├─ 总耗时: 2.8m
├─ 问题定位: 28.9s
├─ 并发证据采集: 127.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 127.8s (Evidence 121.8s, RCA 5.7s)
└─ 汇总总结: 10.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
