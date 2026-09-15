## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod workload-5f4fb9ff45-5mlnc in namespace aiops-case-09 remains NotReady due to persistent Readiness probe failures (HTTP 503 and connection refused on port 8080), while the app container process continues to run and process requests. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Readiness probe failed: Get "http://172.16.104.16:8080/ready": dial tcp 172.16.104.16:8080: connect: connection refused` (fact-05fb13c591a9) | 直接证明探针在尝试连接 8080 端口时被拒绝，是服务不可用的直接表现。 |
| 2 | K8s Event | kubelet | `Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-e58bac71fac8) | 补充说明在连接成功或重试期间，应用返回了 HTTP 503 错误，定位故障发生在应用层。 |
| 3 | K8s State | Pod Condition | `Ready=False, ContainersNotReady` (fact-b54d3375f530) | 确认 Pod 状态因探针失败而转变为 NotReady，导致流量不再进入该 Pod。 |
| 4 | K8s State | Pod Phase | `Running` (fact-3d76bb53bfb8) | 排除容器崩溃重启或挂起问题（restart_count=0），确认进程仍在运行。 |
| 5 | Logging | ES 日志聚合 | `dependency unavailable` (http_status: 503, path: /work) 聚合 8 次 (fact-logging) | 提供内部逻辑证据：应用自身报告“依赖不可用”并返回 503，解释了对外的探针失败原因。 |
| 6 | Tracing | Tempo/Deepflow Flow | `GET /work` -> `HTTP 503`, trace_id: `118cdbf67902f1230e2f38d3ff619e5b` (fact-224c2dfe1934) | 通过 Trace ID 关联了具体的流量记录，确认 `/work` 端点确实因上游依赖问题返回了 503。 |

**证据关联与矛盾说明：**
*   **内外一致性**：K8s 探针看到的 `503` (证据 2) 与日志报告的 `dependency unavailable 503` (证据 5) 以及 Trace 记录 (证据 6) 完全一致，相互印证了故障机制是应用层依赖失败，而非网络或端口配置错误。
*   **故障现象**：TCP 连接被拒 (证据 1) 与 `connection refused` 通常意味着端口未监听或连接被防火墙拒绝。在 `Running` 且端口 8080 已暴露的情况下，结合探针返回 503 (证据 2)，表明探针可能在重试时遇到了连接重置或端口临时不可用，但应用核心逻辑已通过 503 暴露了根本原因（依赖缺失）。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部关键依赖不可用 (日志/Trace) → 就绪探针端点 /ready 返回 HTTP 503 (探针失败) → Kubelet 标记 Pod 状态为 NotReady (Ready=False) → 流量被剔除，业务服务中断
```

### 根因结论

*   **已确认根因**：应用依赖服务故障。
*   **证据支撑**：
    *   应用日志 (`fact-logging`) 明确记录 `dependency unavailable`。
    *   Trace 数据 (`fact-224c2dfe1934`) 显示 `/work` 端点返回 `503`。
    *   K8s 探针事件 (`fact-e58bac71fac8`) 证实了应用层返回了 `503`。
*   **局限说明**：日志和探针虽指出了“依赖不可用”，但未明确指出具体是哪个下游服务或组件（如数据库、中间件）名称缺失，因此具体依赖对象仍为“未确认”。

---

## 📊 性能统计

```text
├─ 总耗时: 4.5m
├─ 问题定位: 17.5s
├─ 并发证据采集: 237.2s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 237.2s (Evidence 223.0s, RCA 14.0s)
└─ 汇总总结: 13.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
