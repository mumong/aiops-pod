## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Application readiness probe returns HTTP 503 due to 'dependency unavailable' |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status`: Running, `restart_count`: 0 | 确认 Pod 实例存活且未发生崩溃重启 |
| 2 | K8s Event | kubernetes | `event.message`: Readiness probe failed: HTTP probe failed with statuscode: 503 | 直接展示探针在 19m 内的持续失败模式 |
| 3 | K8s Event | kubernetes | `event.message`: Get "http://172.16.104.35:8080/ready": dial tcp 172.16.104.35:8080: connect: connection refused | 提供具体的连接拒绝现场，确认端口/网络不可达 |
| 4 | Logging | elasticsearch | `pattern`: `dependency unavailable`, `http_status`: 503, `path`: `/work` (occurrence: 8) | 从应用内部视角印证 503 状态码源于内部依赖问题 |
| 5 | Tracing | deepflow | `l7_flow`: GET `/work` response_code: 503, src_ip: 172.16.104.55 -> dst_ip: 172.16.104.35 | 提供 L7 流量级别的 503 响应证据，与日志现象一致 |
| 6 | K8s Config | kubernetes | `container.resource_limit.memory`: 96Mi | 提供内存上限上下文，结合无重启事实，排除 OOMKill |

**证据关联与印证：**
1. 事件 `#2` (503) 与日志 `#4` (503) 相互印证了探针返回的最终状态码；
2. 事件 `#3` (Connection refused) 解释了探针为何失败，而日志 `#4` 中的 `dependency unavailable` 提供了该连接被拒绝的具体业务原因（即依赖服务不可用）；
3. 追踪 `#5` 确认了目标 Pod IP 接收到了 GET 请求并返回 503，进一步佐证了故障发生在 Pod 内部。

## 🎯 根因分析 · g1

### 因果链

```text
依赖服务不可用 → 应用无法就绪并返回 HTTP 503 → 探测端连接被拒或返回错误 → 探针持续失败导致 NotReady
```

### 根因结论

已确认的根因是**应用依赖不可用导致探针返回 HTTP 503**。
*   **事实支撑**：`K8s Event` 显示探针因连接拒绝 (`connection refused`) 或状态码 503 失败（见证据 `#2, #3`），同时 `Logging` 聚合结果显示同一时间窗口内存在 8 次 "dependency unavailable" 的错误日志（见证据 `#4`）。
*   **现象关联**：这些内部错误导致应用拒绝处理就绪请求，进而触发 kubelet 持续返回 503，最终使 Pod 维持 NotReady 状态。
*   **补充**：无容器重启记录且内存未超限（见证据 `#1, #6`），排除因资源耗尽或崩溃导致的应用不可用。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 13.4s
├─ 并发证据采集: 65.7s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 65.7s (Evidence 60.2s, RCA 5.3s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
