## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod workload-5f4fb9ff45-7b77l (aiops-case-09) is in Running state but marked NotReady due to repeated Readiness Probe failures. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `ContainersReady/Ready: False, reason: ContainersNotReady` (2026-09-07T18:55:18Z) | 确认 Pod 容器已启动但因自身未就绪被判定为不可用。 |
| 2 | K8s Event | kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (1662次/81m) | 提供直接证据，表明探针在极短时间内持续因 HTTP 503 失败。 |
| 3 | Logging | elasticsearch | `http_request 503` 聚合日志，包含 8 条独立 `trace_ids`，记录 "dependency unavailable" 错误 (2026-09-07T20:15:59.419Z - 2026-09-07T20:16:27.533Z) | 确认应用代码内部确实发生了 "dependency unavailable" 业务错误。 |
| 4 | Tracing | deepflow | L7 Flow 聚合，`dst_ip: 172.16.104.35`, `GET /work`, `response_code: 503`，关联 `trace_ids: [1b83c0dc..., ...]` | 证明 Pod 实际网络 IP 在处理 GET /work 请求时返回了 503。 |
| 5 | K8s Config | kubernetes | `memory_limit: 96Mi`, `cpu_limit: 200m` | 资源配额处于常规水平，无显著异常限制迹象。 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total: 0` (针对 container: app) | 确认应用在长周期（81m）内处于稳定运行状态，未发生 CrashLoopBackOff。 |

**证据说明：**
K8s State 和 Event 维度通过 `ContainersNotReady` 状态和频繁的 HTTP 503 探针失败，锁定了 Pod 不可用的直接原因。Logging 维度中具体的 `trace_ids` 与 Tracing 维度的聚合 Flow（关联了相同的 `1b83c0dc...` 等 ID）以及 Pod IP (`172.16.104.35`) 互相印证，排除了网络策略拦截或探针配置错误（探针本身未报错，而是收到了 503），证实 503 是由应用逻辑对 `/work` 端点的实际响应导致的。Metric 维度中重启次数为 0，佐证了这是一个稳定的功能异常而非瞬时系统资源崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
应用业务层依赖不可用（"dependency unavailable"） → Readiness Probe (GET /work) 接收 503 响应 → kubelet 判定探针连续失败 → Pod Ready 状态转为 False (ContainersNotReady)
```

### 根因结论

**已确认根因：**
应用容器 `workload-5f4fb9ff45-7b77l` 内部代码在 `/work` 端点发生“依赖不可用（dependency unavailable）”业务错误，持续返回 HTTP 503。由于 K8s 配置的 Readiness Probe 监控该端点，探针因反复收到 503 响应而判定失败，从而触发 `ContainersNotReady` 状态，导致 Pod 虽在运行但未就绪，流量无法进入。
（证据编号：#2, #3, #4, #5）

**未知/未确认事项：**
应用为何报出 "dependency unavailable"。可能是内部调用的数据库/缓存服务不可达，或是配置缺失。当前缺乏关于该应用内部依赖项状态的具体事实（如依赖组件的日志或网络连通性），无法确定是底层基础设施故障还是应用配置错误。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 21.7s
├─ 并发证据采集: 79.1s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 79.1s (Evidence 68.7s, RCA 10.2s)
└─ 汇总总结: 13.0s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
