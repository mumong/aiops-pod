## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-cfzz6 状态为 NotReady，且持续返回 503 错误 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Condition | `ContainersReady: False (reason: ContainersNotReady)`, `Ready: False` (fact-027495da2b4b, fact-2f679417a212) | 证实 Pod 容器未就绪，状态为 NotReady |
| 2 | K8s Event | Readiness Probe Failure 1 | `Readiness probe failed: Get "http://172.16.104.26:8080/ready": dial tcp 172.16.104.26:8080: connect: connection refused` (fact-5730eca6aea1) | 探测请求被拒绝，连接未建立 |
| 3 | K8s Event | Readiness Probe Failure 2 | `Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-cc905f5a6835) | 探测请求收到 503 服务端错误 |
| 4 | K8s Event | Pod Network | `cni.projectcalico.org/podIP: 172.16.104.26/32` (fact-649ca952a13e) | 提供 Pod 网络终端点地址供排查参考 |
| 5 | Logging | 聚合错误日志 | `error: dependency unavailable`, `http_status: 503`, `path: /work`，在 `2026-09-03T17:53:48.536Z` 至 `17:54:22.680Z` 窗口内发生 8 次 (fact-24b1a9562a58 等) | 确认应用内部 `/work` 请求因依赖不可用而失败 |
| 6 | Tracing | L7 Flow | `GET /work` 返回 `503`，源 `172.16.104.19` 到 目标 `172.16.104.26`，在 `2026-09-04 01:53:44` 至 `01:54:08` 连续 9 次 (fact-5a0e422f0500 等) | 外部或侧边调用方持续收到 503，证实端点不可用性 |

**证据关联说明：**
日志 (证据 #5) 与 Tracing (证据 #6) 高度一致，均指向 `GET /work` 路径返回 `503` 且原因为 `dependency unavailable`。Kubelet 探针日志 (证据 #2, #3) 中同时出现 `connection refused` 和 `503`，表明应用端点响应不稳定：既有时不响应连接，有时响应 503。探针状态 (证据 #1) 是上述应用层故障的直接结果。

## 🎯 根因分析 · g1

### 因果链

```text
应用服务 /work 路径因下游依赖不可用 (fact-5a0e422f0500) → 应用返回 HTTP 503 错误 (fact-24b1a9562a58) → kubelet 读取探针连续失败 (fact-cc905f5a6835, fact-5730eca6aea1) → Pod 状态变为 NotReady (fact-2f679417a212)
```

### 根因结论

**已确认根因：应用服务 `/work` 路径因底层依赖不可用（`dependency unavailable`）持续返回 HTTP 503 错误，导致 Kubernetes 读取探针（Readiness Probe）探测失败。**

1. **应用层故障确认**：日志 (fact-24b1a9562a58) 明确记录了 8 次 `dependency unavailable` 且 `http_status: 503`；Tracing (fact-5a0e422f0500) 独立观测到 `GET /work` 持续返回 503。
2. **Kubelet 判定依据**：Kubelet 在探测 `/ready` 时收到了 503 状态码（fact-cc905f5a6835）及连接拒绝（fact-5730eca6aea1），导致 Pod 条件 `ContainersReady` 和 `Ready` 均为 `False`（fact-2f679417a212）。
3. **局限性说明**：虽然确定了是“依赖不可用”导致的问题，但关于“底层依赖服务（如数据库或微服务）为何不可用”以及“`/ready` 端点代码与 `/work` 路径的具体关联逻辑”属于 **未确认** 环节，需要进一步排查依赖服务状态及应用代码实现。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.3s
├─ 并发证据采集: 44.0s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 44.0s (Evidence 35.3s, RCA 8.5s)
└─ 汇总总结: 16.6s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
