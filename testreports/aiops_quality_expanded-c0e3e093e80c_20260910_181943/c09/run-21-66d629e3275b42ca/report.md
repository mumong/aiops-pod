## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | 应用后端依赖服务不可用导致应用层返回503，触发Readiness Probe持续失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod status: `Running`, Ready: `False` (`ContainersNotReady: containers with unready status: [app]`) | 确认应用容器虽处于运行状态，但未通过就绪检查，流量不可达。 |
| 2 | K8s Event | Kubernetes | `Warning Unhealthy... Readiness probe failed: HTTP probe failed with statuscode: 503` | 直接反映应用层返回 503 错误，触发探针失败。 |
| 3 | K8s Event | Kubernetes | `Warning Unhealthy... Readiness probe failed: Get "http://172.16.104.16:8080/ready": dial tcp 172.16.104.16:8080: connect: connection refused` | 提供历史/详细诊断信息，确认端口 8080 拒绝连接，佐证应用处理异常。 |
| 4 | Logging | Elasticsearch | Pattern: `dependency unavailable`, http_status: 503, path: `/work`, 出现 8 次 (01:27:48 ~ 01:28:12) | 确认业务逻辑层面发生了上游依赖不可用，直接导致 HTTP 503 响应。 |
| 5 | Tracing | Deepflow | L7 Flow: GET /work -> 503, src_ip: 172.16.104.62 -> dst_ip: 172.16.104.16, 重复 9 次 | 验证 503 响应在 L7 层被持续观测，且涉及同网段内请求，证实服务不可用状态。 |
| 6 | Tracing | Tempo | Span: GET /work (Trace: 118cdbf...), status_code: 503 | 确认特定 Trace 内应用处理请求并返回 503 的事实，与日志和流量匹配。 |

证据间相互印证：
日志记录的 `dependency unavailable` (http_status: 503) 完美解释了 K8s 探针收到的 `HTTP probe failed with statuscode: 503` 和 Deepflow 抓取的 L7 层 503 响应。
Pod 状态 `Ready: False` 是上述异常结果在集群层面的直接表现。

## 🎯 根因分析 · g1

### 因果链

```text
应用后端依赖服务不可用 → 业务层处理异常并拒绝请求 → 返回 HTTP 503 响应 → 触发 Readiness Probe 失败并阻断流量
```

### 根因结论

已确认根因为：**应用后端依赖服务不可用**。
证据支持如下：
1. **应用层表现**：应用返回 HTTP 503 错误，由日志模式 `dependency unavailable` (fact #4) 和 Tracing Span (fact #6) 证实。
2. **集群层面反馈**：K8s Readiness Probe 因接收到 503 状态码判定失败 (fact #2, #3)，导致 Pod 进入 `Ready: False` 状态 (fact #1)。
3. **流量层面观测**：Deepflow 记录了大量从客户端到 Pod IP 172.16.104.16 的 GET /work 请求返回 503 (fact #5)。

现有证据完整支撑上述因果链，无需补充其他决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 27.3s
├─ 并发证据采集: 38.3s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 38.3s (Evidence 33.1s, RCA 5.1s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
