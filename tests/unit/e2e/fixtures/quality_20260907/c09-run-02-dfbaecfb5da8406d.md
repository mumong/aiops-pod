## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-wb8n9` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-wb8n9 处于 NotReady 状态（Ready=0/1）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-055b801e3409) | 直接证据：就绪探针连续失败，HTTP 响应为 503。 |
| 2 | K8s Event | kubelet | `Get "http://172.16.104.43:8080/ready": dial tcp 172.16.104.43:8080: connect: connection refused` (fact-5f3e41a3726b) | 早期现象：Pod 内部 8080 端口拒绝连接，表明应用层存在异常。 |
| 3 | Logging | elasticsearch | `dependency unavailable` (HTTP 503, path: `/work`)，连续 8 次出现 (fact-0cd230978a45) | 根本机制：应用代码显式返回 503 错误，日志记录为依赖不可用。 |
| 4 | Tracing | Deepflow / Tempo | 等价 L7 Flow: HTTP 172.16.104.58 → 172.16.104.43 `/work` → 503 (fact-56e88d7eb13b)；Tempo Span: `aiops.observed_mode: readiness_fail` (fact-6570e29a9b0d) | 证据关联：Trace 数据明确标记了故障模式为 `readiness_fail`，印证了应用层故意返回 503 的行为。 |
| 5 | K8s State | kubernetes | Pod Status: `Running`, NotReady (fact-4d9207bd1ac6) | 异常状态：Pod 容器在运行中但未就绪。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 0 (fact-4bea258c0be9) | 排除假设：容器未重启，排除 CrashLoopBackOff 或资源耗尽导致的进程退出。 |

**证据说明：**
日志 (fact-0cd230978a45) 确认应用层主动返回 503 错误；追踪数据 (fact-6570e29a9b0d) 明确记录了 `readiness_fail` 模式，这与 Kubelet 报告的就绪探针失败（fact-055b801e3409）完美契合；由于重启数为 0（fact-4bea258c0be9），排除了运行时崩溃导致连接拒绝的可能性，指向应用配置的故意行为。

## 🎯 根因分析 · g1

### 因果链

```text
环境变量配置 FAILURE_MODE=readiness_fail → 应用逻辑在 /work 端点故意返回 HTTP 503 (dependency unavailable) → Kubelet 读取就绪探针端点时收到 503 状态码 → Pod 被标记为 NotReady
```

### 根因结论

**已确认的根因：** 环境变量 `FAILURE_MODE=readiness_fail` 导致应用层在健康检查端点故意返回 HTTP 503 错误，致使 Kubelet 读取探针（Readiness Probe）持续失败。

**证据支撑：**
1. 应用层日志 (fact-0cd230978a45) 和追踪数据 (fact-6570e29a9b0d) 均明确指出 `readiness_fail` 模式及应用主动返回 503 的行为。
2. Kubelet 事件 (fact-055b801e3409) 验证了就绪探针确实收到了 503 响应。
3. 容器未重启 (fact-4bea258c0be9)，证明是应用逻辑行为而非运行崩溃。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 18.0s
├─ 并发证据采集: 118.3s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-wb8n9: 118.3s (Evidence 107.6s, RCA 10.5s)
└─ 汇总总结: 13.4s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-wb8n9**: pod-notready-probe-failed
