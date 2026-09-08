## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-cfzz6 处于 NotReady 状态，Readiness Probe 持续返回 503。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Readiness probe failed: Get "http://172.16.104.26:8080/ready": dial tcp 172.16.104.26:8080: connect: connection refused` | 早期网络连通性故障证据，显示探针请求被拒绝 |
| 2 | K8s Event | Kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (x311) | 持续的状态证据，表明连接建立后应用主动拒绝服务 |
| 3 | Logging | Elasticsearch | `dependency unavailable` (http_status: 503) 在 18:10:31 - 18:11:09 重复 8 次 | 应用内部根因日志，证实 503 响应是由上游依赖不可用触发 |
| 4 | Tracing | Tempo | Span `1958329029c7c0fd`：`GET /work` 响应 503，耗时 3ms | 验证 `/work` 端点确实因应用内部逻辑返回 503 |

Pod 处于 Running 状态且无重启，探针故障完全由应用层返回 503 导致。日志中“dependency unavailable”与 Trace 中 503 响应形成因果闭环，表明 Readiness 探针因应用依赖失败而持续不可用。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部依赖服务不可用 → Readiness Probe 端点持续返回 HTTP 503 → Kubelet 判定探针持续失败 → Pod 状态 NotReady (0/1 Ready)
```

### 根因结论

**已确认根因：** 应用代码中的上游依赖（日志标记为 "dependency unavailable"）不可用，导致服务健康检查端点返回 503 (Service Unavailable) 错误。

**证据支撑：**
1. **现象确认：** Kubernetes 事件记录显示探针失败从“连接拒绝”（可能为冷启动或网络瞬断）转为持续的 `HTTP 503`（事实 1、2）。
2. **内部原因：** 应用日志明确指出报错 `dependency unavailable` 并伴随 503 状态码（事实 3）。
3. **链路佐证：** Tempo 追踪显示对应请求确实返回了 503（事实 4）。

**缺失信息：** 具体的上游依赖服务名称未在日志或追踪中暴露，因此无法精确定位是哪个外部组件故障导致了应用抛出此异常。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 23.6s
├─ 并发证据采集: 80.2s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 80.2s (Evidence 71.9s, RCA 8.2s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
