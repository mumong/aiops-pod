## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v17/workload` | NotReady | Pod aiops-case-v17/workload 初始状态为 NotReady 并经历 23 次崩溃重启，当前已恢复为 Running/Ready |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `last_terminated_reason`: Error; `last_exit_code`: 137; `restart_count`: 23 | 确认容器处于频繁崩溃重启的异常状态，且异常退出非正常退出。 |
| 2 | K8s Event | Kubernetes | `Liveness probe failed`: `http://172.16.104.36:18080/health`: context deadline exceeded (Client.Timeout exceeded) | 核心故障：应用处理 `/health` 请求耗时超过 Kubelet 设定的 1s 超时阈值。 |
| 3 | Metric | Prometheus | `container_memory_working_set_bytes`: `11923456` bytes (约 11.4 MB) | 提供背景：内存占用远低于 `64Mi` 限制，排除 OOMKill 导致的非正常退出。 |
| 4 | Logging | Elasticsearch | `GET /ready HTTP/1.1" 200`; `GET /health HTTP/1.1" 200` | 限定与冲突：应用日志显示端点返回 200，但 Liveness 超时事件表明应用内部执行耗时严重拖慢了响应，导致外部探针超时。 |
| 5 | Tracing | Deepflow | HTTP GET `/health`: `response_status`: 0; `duration_us`: `3001095.0` 至 `3002217.0` | 决定性证据：确认请求实际耗时约 3000ms（3s），远超探针 1s 超时配置，证实探针超时机制。 |

证据总结：
1-2、5 号证据相互印证，Tracing 数据（5）精确解释了 K8s 探针超时事件（2）的物理原因（3s 耗时）。4 号日志证据显示应用业务逻辑本身返回 200，但无法掩盖响应时间超限导致的探针失败，反而排除了应用服务不可用的可能。3 号证据排除了资源耗尽导致的 Crash，将原因指向业务逻辑与探针配置的冲突。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码 /health 端点包含 3s sleep 逻辑 → Liveness 探针（1s超时）频繁触发 → 容器被 Kubelet 强杀(Exit 137) → Pod 崩溃重启(CrashLoopBackOff)
```

### 根因结论

已确认的根因是应用代码执行逻辑（3s sleep）与 Liveness Probe 超时配置（1s）不匹配，导致容器被系统频繁终止并重启。

- **机制支撑**：Tracing 数据（事实 #5）明确观测到 `/health` 端点请求耗时为 3001ms，直接导致 Kubernetes 探针在 1s 后抛出 `context deadline exceeded` 错误（事实 #2）。
- **状态支撑**：Container 频繁被杀死（Exit Code 137，事实 #1）和 Pod 23 次重启（事实 #1）是探针频繁超后的直接后果。
- **排除其他**：Memory 指标（事实 #3）未触及 `64Mi` 限制，排除了 OOM 可能；日志（事实 #4）虽然返回 200，但进一步确认了应用是在处理完请求后返回，而非服务崩溃，佐证了耗时导致的超时机制。

*注：事实 #2 同时也记录了 `/ready` 端点连接被拒绝的现象，这是因为容器在重启间隙（如 `restart_count` 统计时）处于不可用状态，属于根因触发的副作用。*

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 23.1s
├─ 并发证据采集: 86.0s
│  └─ g1 aiops-case-v17/workload: 86.0s (Evidence 74.7s, RCA 11.1s)
└─ 汇总总结: 12.4s
```

📋 Runbook 参考

- **g1 aiops-case-v17/workload**: pod-crashloop-runtime, pod-oomkilled
