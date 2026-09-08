## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-7b77l 处于 NotReady 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-09/workload-5f4fb9ff45-7b77l` 状态为 Running，但 Ready 状态为 `False`，原因 `ContainersNotReady` | 确认异常实体及其容器状态 |
| 2 | K8s Event | Kubernetes | `Warning Unhealthy`：Readiness probe failed: HTTP probe failed with statuscode: 503，持续 100 分钟 | 解释 Pod 状态标记为 NotReady 的直接原因 |
| 3 | Logging | Elasticsearch | 应用报错：`dependency unavailable`，伴随 `http_status: 503`，路径 `/work`，连续记录于 `20:35:21` - `20:35:48` | 揭示 Readiness Probe 返回 503 的深层应用原因（依赖不可用） |
| 4 | Tracing | Deepflow | L7 Flow 聚合显示：针对路径 `/work` 的 HTTP GET 请求持续返回 503 状态码，跨多 Trace ID 重复出现 | 独立于日志的 L7 层面确证，排除单条日志偶发性故障 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 值为 `0` | 排除因 CrashLoopBackOff 或资源超限导致的重启 |

**证据关系：**
日志 (3) 与应用层 HTTP Flow (4) 共同证实，应用服务 `/work` 端点因底层“依赖不可用”持续返回 503。这一应用层行为正是导致 Kubernetes Readiness Probe (2) 探测失败的直接机制，进而使 Pod (1) 维持 NotReady 状态。Metric (5) 排除了应用崩溃重启的可能。

## 🎯 根因分析 · g1

### 因果链

```text
未确认的具体上游依赖故障或配置缺失 → 应用 /work 端点因依赖不可用返回 HTTP 503 → Kubernetes Readiness Probe 持续探测失败 → Pod aiops-case-09/workload-5f4fb9ff45-7b77l 被标记为 NotReady
```

### 根因结论

**已确认根因**：应用服务 `aiops-case-09/workload-5f4fb9ff45-7b77l` 内部的 `/work` 端点因后端依赖不可用，持续向 Readiness Probe 返回 HTTP 503 错误。这直接导致 Pod 的健康检查失败并失去 Ready 状态 [证据 2, 3, 4]。

**待确认信息**：当前证据无法指出导致“dependency unavailable”的具体上游服务、网络问题或配置缺失详情。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 22.2s
├─ 并发证据采集: 108.1s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 108.1s (Evidence 100.1s, RCA 7.9s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
