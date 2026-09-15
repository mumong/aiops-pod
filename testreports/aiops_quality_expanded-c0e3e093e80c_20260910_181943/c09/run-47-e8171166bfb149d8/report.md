## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | {'message': 'cni.projectcalico.org/podIPs: 172.16.104.16/32'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status`: `Running` (fact-c639ceff0c55) | 基础容器运行正常，排除了底层容器引擎故障。 |
| 2 | K8s Event | kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-790af188394f) | 直接现象：应用层健康检查持续失败。 |
| 3 | K8s Event | kubernetes | `cni.projectcalico.org/podIP: 172.16.104.16/32` (fact-64d6cac56911) | 确认网络层已分配，排除基础网络配置缺失。 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 0 (fact-69a50491855d) | 确认应用未因 Crash 重启，状态是稳定的 503 而非启动失败。 |
| 5 | Logging | elasticsearch | 模式 `dependency unavailable` 在 `/work` 端点返回 503 (fact-1bb97369cc96) | 应用日志直接指出下游依赖不可用导致 503 响应。 |
| 6 | Tracing | deepflow | L7 Flow `GET /work` 响应状态 503，来源 IP `172.16.104.62` (fact-2fb268bdd37b) | 外部视角确认了流量到达 Pod 后被应用拒绝。 |

证据表明应用逻辑健康（无重启、无崩溃），但在处理 `/work` 请求时持续返回 503，且应用层日志明确归因为 `dependency unavailable`。

## 🎯 根因分析 · g1

### 因果链

```text
未确认的下游依赖故障 → 应用层抛出 "dependency unavailable" → 健康检查端点 GET /work 返回 HTTP 503 → Pod 状态变为 NotReady
```

### 根因结论

**证据不足**。现有证据已确证故障表象是应用依赖不可用导致的健康检查失败，但决定性的根因事实缺失。具体而言：
1. **依赖对象不明**：应用日志仅笼统报错 `dependency unavailable`，未指明具体是哪个服务或组件（fact-1bb97369cc96）。
2. **调用链断裂**：由于日志与追踪系统关联失败（ES 查询未命中有效 trace_id），无法通过 Tracing 追踪 503 响应的完整内部调用链路，无法定位是哪一步下游依赖导致了中断。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 21.6s
├─ 并发证据采集: 96.0s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 96.0s (Evidence 86.5s, RCA 9.4s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
