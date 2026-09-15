## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod workload-5f4fb9ff45-5mlnc 处于 NotReady 状态，持续报告 Readiness probe failed: HTTP probe failed with statuscode: 503 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Unhealthy 2m24s (x2182 over 107m) kubelet Readiness probe failed: HTTP probe failed with statuscode: 503` | 直接记录 Probe 失败事实及频次 |
| 2 | K8s State | Kubernetes | `containers with unready status: [app]` (Ready=False, ContainersReady=False) | 确认 Pod 状态持续不满足就绪条件 |
| 3 | Logging | Elasticsearch | `dependency unavailable`, HTTP status 503, path `/work`, 聚合 8 条 (02:20:07 ~ 02:20:33) | 揭示应用逻辑层返回 503 的直接原因 |
| 4 | Tracing | DeepFlow/Tempo | Flow 记录 9 次 `GET /work` 返回 `response_code: 503` (10:07 ~ 10:19); Span `e82686c35f799057` 记录 `http.response.status_code: 503` | 确认 503 响应为应用持续行为，非瞬时故障 |

**证据说明：**
- **维度印证**：K8s 探针持续返回 503 状态（#1, #2），其根本原因由日志中的“dependency unavailable”（#3）和 Tracing 中的 HTTP 503 响应（#4）一致锁定。
- **状态排他**：Pod 运行状态 `Running` 且 `restart_count: 0`（事实 `fact-d574eaf73455`, `fact-ad8e709b5f1d`），排除了容器崩溃（CrashLoopBackOff）或重启导致的不稳定，确认故障源在于应用对外部依赖的调用结果。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖服务不可用（未确认具体依赖实体） → 业务接口 /work 返回 503 (dependency unavailable) → K8s Readiness Probe 连续失败 (503) → Pod 状态 NotReady，流量被剔除
```

### 根因结论

**已确认根因**：Pod `aiops-case-09/workload-5f4fb9ff45-5mlnc` 内的 `app` 容器因依赖服务不可用，持续对就绪探针端点 `/work` 返回 HTTP 503 状态，导致 Kubernetes 判定容器未就绪。

**缺失事实**：日志明确提示错误原因为“dependency unavailable”，但输入数据中未包含关于该具体依赖服务（是外部服务还是集群内其他 Pod）的状态或网络连接日志，无法进一步确认上游依赖中断的根因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 21.7s
├─ 并发证据采集: 65.1s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 65.1s (Evidence 56.9s, RCA 8.0s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
