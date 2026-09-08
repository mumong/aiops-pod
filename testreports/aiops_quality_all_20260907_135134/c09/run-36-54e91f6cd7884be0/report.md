## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | The application's readiness endpoint (/work) returns HTTP 503 'dependency unavailable' due to an underlying dependency failure, causing the kubelet's readiness probe to fail continuously and the Pod to remain in NotReady state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod.phase=Running, pod.status=Running, pod.condition.Ready=False (ContainersNotReady) | 确定 Pod 核心容器运行正常但健康检查未通过 |
| 2 | K8s Config | kubernetes | container.resource_request.cpu=20m, memory=24Mi; container.resource_limit.cpu=200m, memory=96Mi | 排除资源限制不足导致启动失败的可能 |
| 3 | K8s Event | kubernetes | Readiness probe failed: HTTP probe failed with statuscode: 503 (持续 70 分钟) | 确认 kubelet 探测行为与故障现象的直接证据 |
| 4 | Logging | elasticsearch | pattern: dependency unavailable, http_status: 503, path: /work (8 次, 2026-09-07 20:05:10 ~ 20:05:49) | 提供应用内部报错的具体错误文本与时间窗口 |
| 5 | Tracing | deepflow | l7_flow: GET /work -> 503, src_ip: 172.16.104.55 -> dst_ip: 172.16.104.35 (9 次, 2026-09-08 04:00:41 ~ 04:05:41) | 验证探测流量（或调用流量）均收到 503 响应 |
| 6 | Tracing | tempo | span: GET /work, status_code: 503, trace_id: 19d91041c588289dbde79a42192f2e1e | 确认应用侧对特定路径返回的具体状态码 |

K8s 事件与日志共同证实了 `/work` 路径持续返回 503 状态码；日志的 `dependency unavailable` 与 Trace 的 L7 流量 503 响应相互印证，说明应用自身逻辑（而非 K8s 层）是导致探测失败的直接原因；资源请求与限制数据表明环境资源充足，排除了资源不足的可能。

## 🎯 根因分析 · g1

### 因果链
```text
应用底层依赖异常 → 应用 /work 端点返回 503 → kubelet 探测失败 → Pod 状态 NotReady
```

### 根因结论
已确认根因为**应用依赖故障**。具体表现为应用健康检查端点 `/work` 持续返回 HTTP 503 状态码（错误信息为 `dependency unavailable`），导致 K8s kubelet 持续探测失败，进而使 Pod 处于 `NotReady` 状态 [事实编号 3, 4, 5]。应用运行在 `Running` 状态且未重启，证明是业务逻辑或下游依赖问题，而非启动或资源类故障。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 19.5s
├─ 并发证据采集: 63.3s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 63.3s (Evidence 56.5s, RCA 6.6s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
