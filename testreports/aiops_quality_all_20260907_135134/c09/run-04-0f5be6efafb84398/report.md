## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-7b77l 处于 NotReady 状态，Readiness Probe 持续返回 HTTP 503 错误。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-09/workload-5f4fb9ff45-7b77l` (IP: 172.16.104.35) 处于 `Running` 但 `Ready` 为 `False`，原因 `ContainersNotReady` | 确立故障表象与实体状态 |
| 2 | K8s Event | kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (累计 103 次) | 确认 Kubelet 判定探针失败的直接响应码 |
| 3 | K8s Event | kubernetes | `Readiness probe failed: Get "http://172.16.104.35:8080/ready": dial tcp 172.16.104.35:8080: connect: connection refused` | 提供探针配置（/ready, 8080端口）及连接被拒的历史细节 |
| 4 | K8s Config | kubernetes | 资源限制 `memory`：96Mi，资源请求 `cpu`：20m，`memory`：24Mi | 排除因资源硬限制不足导致的启动失败 |
| 5 | Logging | elasticsearch | 日志模式 `dependency unavailable` (HTTP 503, `/work`) 发生 8 次，`allocated_mib` 始终为 0 | 证实应用代码层面捕获了依赖失败并返回 503 |
| 6 | Tracing | deepflow | HTTP Flow 从 `172.16.104.55` 到 `172.16.104.35` 的 `/work` 请求持续返回 503，发生 9 次 | 从网络层确证业务接口 `/work` 不可用 |
| 7 | Tracing | tempo | Span `GET /work` 返回 `503`，`aiops.observed_mode` 为 `readiness_fail` | 关联应用内部逻辑与 Readiness 失败的具体场景 |

**证据关联说明**：
1.  **逻辑闭环**：证据 #5 (日志) 和 #6 (Trace) 证实应用代码因“下游依赖不可用”主动返回 503，这直接导致了证据 #2 (Kubelet 事件) 中的探针失败。
2.  **探针配置确认**：虽然 Kubelet 事件 #3 提及 `dial connection refused` (8080端口)，但日志 #5 和 Trace #6 聚焦于 `/work` 路径返回的 503。这表明探针可能配置了多个端点（如 `/ready` 和 `/work`），或者 `/ready` 依赖于 `/work` 的状态，导致当前处于“依赖不可用”而非“服务未启动”的状态。

## 🎯 根因分析 · g1

### 因果链

```text
下游依赖服务不可用 → 应用代码捕获异常并返回 HTTP 503 ('dependency unavailable') → Kubelet Readiness Probe 接收非 2xx 响应 → Pod 标记为 NotReady
```

### 根因结论

已确认的根因为 **应用代码因下游依赖不可用而返回 HTTP 503**，导致 Kubernetes Readiness Probe 持续失败。

1.  **机制已确认**：日志事实 `dependency unavailable` (fact-426f3f77bbc8) 与 Trace 事实 `GET /work` 返回 503 (fact-21c1f8197574, fact-5e6190a4e624) 互相印证，表明应用正在运行但无法处理请求，原因是其依赖的后端资源缺失。
2.  **现象已确认**：Kubelet 事件记录证实探针因收到 503 响应而判定容器未就绪 (fact-74cfe723f3ad)，导致 Pod 处于 `NotReady` 状态 (fact-8b10fb12b55e)。
3.  **未知部分**：具体是哪一类下游依赖（数据库、缓存或其他微服务）不可用导致 `dependency unavailable` 在输入事实中无法确定。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 19.6s
├─ 并发证据采集: 88.0s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 88.0s (Evidence 76.7s, RCA 11.1s)
└─ 汇总总结: 14.3s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
