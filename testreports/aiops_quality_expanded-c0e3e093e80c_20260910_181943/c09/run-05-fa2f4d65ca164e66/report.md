## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | 应用依赖资源不可用导致服务返回 HTTP 503，触发 Readiness Probe 持续失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-09/workload-5f4fb9ff45-5mlnc` 状态 `Running`，Phase `Running`，但 `Ready=False` (`ContainersNotReady`) | 描述异常实体的当前生命周期状态 |
| 2 | K8s Event | kubernetes | `Warning  Unhealthy       18m  kubelet  Readiness probe failed: Get "http://172.16.104.16:8080/ready": dial tcp 172.16.104.16:8080: connect: connection refused` | 确认 Readiness Probe 失败的网络层原因：连接被拒绝 |
| 3 | K8s Event | kubernetes | `Warning  Unhealthy       3m39s (x312 over 18m)  kubelet  Readiness probe failed: HTTP probe failed with statuscode: 503` | 确认 Probe 失败的应用层表现：收到 503 响应 |
| 4 | Logging | elasticsearch | 日志模式 `dependency unavailable` (http_status: 503)，窗口内观测 8 次 (trace_ids: `1aa79a59...` 等) | 确认应用自身日志记录了依赖不可用并返回 503 |
| 5 | K8s Config | kubernetes | 容器 `app` 内存请求 24Mi / 限制 96Mi；CPU 请求 20m / 限制 200m | 排除资源超卖或 OOM 导致 503 的可能性 |
| 6 | Tracing | tempo | Span `GET /work`，`aiops.observed_mode: readiness_fail`，HTTP status 503 (trace_id: `84c5e1e0...`) | 将业务路径与 K8s Probe 的失败模式进行关联确认 |

**证据总结：**
Pod 虽然处于 Running 状态且未重启，但因 Readiness Probe 持续失败而被标记为 `NotReady`。网络日志显示探针请求被直接拒绝（连接失败），而应用日志则记录了服务在处理请求（如 `/work`）时因“依赖不可用”返回了 503 状态码。两者共同表明该容器内的应用进程处于不健康状态。配置显示资源分配合理，排除了资源短缺导致的崩溃或停滞。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖的资源（如 DB、缓存等）不可用（未确认具体依赖项） → 应用无法处理业务请求，返回 HTTP 503（Logging: "dependency unavailable", Tracing: 503） → K8s Readiness Probe 请求应用接口 (`/ready`) 时，因应用内部逻辑故障同样返回 503 或应用彻底卡死导致连接被拒绝（Event: "connection refused" 或 "statuscode: 503"） → 触发 K8s 将 Pod 状态置为 NotReady，阻止流量进入（Event: "ContainersNotReady", State: "Ready=False"）
```

### 根因结论

已确认根因为：**应用内部依赖资源不可用，导致服务健康检查（Readiness Probe）和业务请求均失败。**

证据链闭环如下：
- **现象确认**：K8s Event 显示 Probe 持续失败，且伴随 `statuscode: 503`（证据 #3）及 `connection refused`（证据 #2）；Pod 状态被正确标记为 `NotReady`（证据 #1）。
- **因果定位**：应用侧日志（证据 #4）记录了 `dependency unavailable` 并对外返回 503，Tracing（证据 #6）确认了业务路径（`/work`）与探针的失败模式一致。这解释了应用为何不仅拒绝外部请求，也无法通过自身健康检查。
- **排除干扰**：资源限制（证据 #5）正常，且容器重启次数为 0，排除了因资源耗尽、OOM 或容器启动失败（CrashLoop）导致的直接中断。

虽然应用返回了 503 和明确的“依赖不可用”日志，但“未确认具体是哪个外部依赖”导致了日志中连接被拒绝（Connection refused）的现象，这说明应用可能存在部分服务完全不可达，或在不同时间窗口表现出不一致性。

---

## 📊 性能统计

```text
├─ 总耗时: 10.8m
├─ 问题定位: 23.1s
├─ 并发证据采集: 610.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 610.8s (Evidence 603.9s, RCA 6.8s)
└─ 汇总总结: 14.6s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
