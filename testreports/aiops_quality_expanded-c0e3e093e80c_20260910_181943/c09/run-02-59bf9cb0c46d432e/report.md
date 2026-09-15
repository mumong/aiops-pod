## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | 应用启动后业务逻辑检测到底层依赖不可用（'dependency unavailable'），导致健康检查端点持续返回 HTTP 503 错误，触发 Kubelet Readiness Probe 失败并移除 Pod 服务发现。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Readiness probe failed: Get "http://172.16.104.16:8080/ready": dial tcp 172.16.104.16:8080: connect: connection refused` (fact-22dd091e301a) | 提供底层 TCP 连接失败的原始异常细节。 |
| 2 | K8s Event | kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-eee780e4abdf) | 确认健康检查端点返回了业务拒绝服务状态。 |
| 3 | Logging | elasticsearch | `http_request` 模式：`message=dependency unavailable`, `http_status=503`, 出现 8 次 (fact-4205ae43c527 等) | 证实 503 状态码由业务逻辑检测到“依赖不可用”主动返回，而非基础设施崩溃。 |
| 4 | Tracing | deepflow | `HTTP GET /work` 流程：`dst_ip=172.16.104.16` (Pod IP), `response_code=503`, 发生 9 次 (fact-4b74c185e7f4 等) | 从 L7 流量层面佐证大量请求到达该 Pod 后均被拒回，形成 503 现象的持续证据。 |

证据表明 Pod 运行环境（172.16.104.16）中业务逻辑检测到依赖缺失，主动返回 503 响应。这既触发了 HTTP 探测器的失败，也解释了底层 TCP 连接层面的拒绝行为；日志与流量均聚焦于同一服务内部的状态拒绝。

## 🎯 根因分析 · g1

### 因果链

```text
应用运行环境内部依赖资源不可用 → 应用代码执行健康检查逻辑并返回 HTTP 503 → Kubelet 探针接收 503 状态码判定为 NotReady → Pod 状态保持 Running 但处于 NotReady，无法接收流量
```

### 根因结论

**已确认的根因**：应用代码在检测到其内部依赖资源不可用时，主动返回了 `HTTP 503` 状态码（详见日志证据 #3、流量证据 #4）。这一行为直接导致 Kubelet 发起的 Readiness 探针判定失败（详见事件证据 #1、#2），使得 Pod 在 `Running` 状态下被标记为 `NotReady`，从而被移除服务发现列表。现有日志中 `dependency unavailable` 的明确提示与探针失败的直接关联，足以支撑该因果链。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 21.7s
├─ 并发证据采集: 108.1s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 108.1s (Evidence 99.5s, RCA 8.5s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
