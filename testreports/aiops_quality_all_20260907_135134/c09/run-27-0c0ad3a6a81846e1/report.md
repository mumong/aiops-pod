## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | {'type': 'Warning', 'reason': 'Unhealthy', 'message': 'Warning  Unhealthy       103s (x1039 over 51m)  kubelet            Readiness probe failed: HTTP probe failed with statuscode: 503'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (x1039 over 51m) | 确认就绪探针长期连续返回 503 错误，是 Pod 不Ready的直接原因 |
| 2 | K8s Event | kubernetes | `Readiness probe failed: Get "http://172.16.104.35:8080/ready": dial tcp 172.16.104.35:8080: connect: connection refused` (51m前) | 证实应用容器监听地址 172.16.104.35:8080 的 /ready 端点存在连接拒绝的早期现象 |
| 3 | Logging | elasticsearch | `error: dependency unavailable`, path=/work, http_status=503, first: 19:46:16, last: 19:46:54 | 确认应用进程正在运行但持续报依赖不可用，验证了探针返回 503 的底层业务逻辑 |
| 4 | Tracing | deepflow/Tempo | flow: GET /work, src_ip: 172.16.104.55 → dst_ip: 172.16.104.35, response_code: 503, count: 9 | 从 L7 网络流层面独立证实了从 104.55 到应用 104.35 的 /work 端点大量返回 503 |
| 5 | K8s State | kubernetes | pod.status: Running, pod.condition(Ready): False, container.restart_count: 0 | 排除容器频繁崩溃重启的可能，确认为应用健康状态检查失败 |

**证据印证：**
1. **探针失败与依赖不可用印证**：K8s Event 中探针在 `/ready` 端点持续报 503（#1），Logging 和 Tracing 中应用针对 `/work` 端点报“依赖不可用”并返回 503（#3, #4）；这表明应用的依赖服务调用异常导致了 503 状态，进而使得就绪探针失败。
2. **早期故障印证**：连接拒绝（#2）发生在较早期，而后续的 503 错误持续了 51 分钟（#1），说明应用虽然启动（Running, #5）并进入了处理请求阶段，但未能成功连接或获取依赖服务。

## 🎯 根因分析 · g1

### 因果链

```text
上游/外部依赖服务不可用 → 应用进程运行但调用失败 (dependency unavailable) → Kubelet Readiness Probe (/ready) 连续接收到 503 → Pod Ready 状态持续为 False
```

### 根因结论

**诊断状态：证据不足 (inconclusive)**

1. **已确认现象**：Pod `aiops-case-09/workload-5f4fb9ff45-7b77l` 处于 `Running` 但 `NotReady` 状态。根本表象是应用进程在处理健康检查或业务请求时，因上游依赖不可用（Logging 报告 "dependency unavailable"，Tracing 确认 503 响应），导致 Kubelet 发出的 `GET /ready` 探针收到 `503` 或连接被拒（Connection refused）。
2. **缺失决定性事实**：
   - **未知上游依赖方**：虽然明确指向“外部依赖服务不可用”，但日志和追踪数据均未包含具体是哪个外部服务（如数据库、缓存或第三方 API）响应失败或超时。
   - **缺乏拓扑关联**：缺少应用与外部服务间的依赖拓扑关系数据（Topolgy 查询规划但未获取到有效结果），无法将 "dependency unavailable" 映射到具体的服务名或 IP。
   - 因此，虽然明确了故障机制（依赖缺失导致 503），但无法定位故障的**具体根因实体**（即哪个上游服务出了问题）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 14.7s
├─ 并发证据采集: 74.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 74.8s (Evidence 63.3s, RCA 11.3s)
└─ 汇总总结: 13.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
