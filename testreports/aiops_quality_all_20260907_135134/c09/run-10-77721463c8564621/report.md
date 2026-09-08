## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod NotReady (0/1 Ready) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (fact-4bc793d4dc58) | `Ready` status: `False`, Reason: `ContainersNotReady` | 确认 Pod 处于 NotReady 状态 |
| 2 | K8s Event | kubelet (fact-736ccd20854a) | `Readiness probe failed: HTTP probe failed with statuscode: 503` | 确认健康检查最终报错，频次 311 次 |
| 3 | K8s Event | kubelet (fact-bc9524347579) | `dial tcp 172.16.104.35:8080/ready: connect: connection refused` | 指出探针连接被拒的具体时刻和端口 |
| 4 | Metric | prometheus (fact-cb9fa78d4ee5) | `kube_pod_container_status_restarts_total`: 0 | 排除因容器 OOM 或崩溃重启导致服务未拉起的可能性 |
| 5 | Tracing | deepflow (fact-858f043c6099) | HTTP GET `dst_ip=172.16.104.35:8080/work` -> 503 (9次) | 证明业务流量同样遭遇 503，确认为服务端逻辑故障 |
| 6 | Logging | elasticsearch (fact-09bb87865322) | `dependency unavailable` (pattern, 8次) | 业务日志直接声明“依赖不可用”，解释 503 产生原因 |

证据链表明：Pod 运行正常且未重启（Metric #4），但业务应用因“依赖不可用”（Logging #6）主动返回 503，导致 Kubelet 探针在 172.16.104.35:8080 端口持续被拒（Event #3）或收到 503（Event #2），最终触发 Tracing #5 中的全流量 503 异常。

## 🎯 根因分析 · g1

### 因果链

```text
Application dependency unavailable → HTTP 503 on /ready → Readiness probe failure (x311) → Pod NotReady
```

### 根因结论

**已确认根因**：应用服务依赖不可用导致就绪探针（Readiness Probe）持续失败。
具体表现为应用业务日志明确记录 `dependency unavailable` (Logging #6)，且业务流量 (Tracing #5) 与健康检查流量 (Event #2) 均收到 HTTP 503 响应，导致 Kubernetes 判定容器未就绪 (K8s State #1)。

**未确认/缺失事实**：
1. **具体缺失依赖对象**：日志仅报告“依赖不可用”，未指明具体是数据库、缓存还是第三方 API（Unknown in Fact #5）。
2. **依赖故障根因**：未查明导致该依赖不可用的具体网络或上游服务故障（Unknown in Fact #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 21.0s
├─ 并发证据采集: 71.6s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 71.6s (Evidence 63.5s, RCA 8.0s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
