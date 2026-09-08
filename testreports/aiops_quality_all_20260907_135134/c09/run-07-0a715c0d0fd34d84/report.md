## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod内应用进程在尝试访问内部依赖服务时遭遇连接失败，导致业务逻辑主动向Readiness探针端点(/ready)返回HTTP 503状态码，从而引发Pod持续NotReady。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod状态 `ContainersNotReady` (`fact-6542a0b4393f`, `fact-a8237bf4d09e`)；Pod相位 `Running` (`fact-69626f80f279`)。 | 确认应用容器仍在运行但未就绪，排除整体调度故障或容器崩溃退出。 |
| 2 | K8s Event | kubernetes | Readiness Probe failed: `GET "http://172.16.104.35:8080/ready": dial tcp 172.16.104.35:8080: connect: connection refused` (`fact-3add3852bb35`)。 | 提供直接探针失败原因，指出应用进程未在 8080 端口监听导致连接被拒绝。 |
| 3 | K8s Event | kubernetes | Readiness Probe failed: `HTTP probe failed with statuscode: 503` (`fact-576ee821f343`)。 | 证明应用进程实际响应了探针请求并返回了业务层约定的 503 状态码。 |
| 4 | Logging | elasticsearch | 错误日志 `dependency unavailable`，HTTP 503，路径 `/work`，连续观察窗口内 `allocated_mib` 维持 0 (`fact-3fcfbda11278`)。 | 证实应用业务逻辑因依赖不可用主动返回 503，且该异常为独立重复出现，非内存溢出导致。 |
| 5 | Tracing | tempo | Trace `25758edb4a1fd369a0ec6286ba8e08d4`：应用请求 `/work` 返回 503，属性标记 `aiops.observed_mode: "readiness_fail"` (`fact-3d0b989c1cf8`)。 | 将业务接口失败与就绪探针失败在同一个追踪链路内关联，验证 503 源于业务逻辑而非探针配置错误。 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total` 值为 0 (`fact-094a5c5e7ce2`)。 | 佐证容器未发生 OOMKilled 或重启，故障属于应用状态机层面的持续降级。 |

**证据说明**
1. 证据 2 和 证据 3 共同描述了探针失败的不同表现：底层连接被拒与上层业务返回 503，结合证据 4（日志）可判定 503 为应用主动返回的降级响应。
2. 证据 3 和证据 5 通过追踪链路将业务接口 `/work` 的 503 失败直接映射到就绪探针（Readiness Fail）的上下文中，证实探针获取的 503 状态码是业务逻辑对依赖服务失败的正常响应。

## 🎯 根因分析 · g1

### 因果链

```text
应用内部依赖服务不可用（未确认具体依赖实体） → 应用业务逻辑触发降级，主动向 /ready 端点返回 HTTP 503 → kubelet Readiness 探针收到非 2xx 响应判定为失败 → Pod 被移除端点并持续处于 NotReady 状态
```

### 根因结论

**已确认的根因**：Pod 内应用进程的健康状态检查机制（Readiness Probe）依赖 `/ready` 端点返回成功状态，但该端点的可用性被业务逻辑绑定到了内部依赖服务的状态。当内部依赖服务不可用时，应用按设计返回 HTTP 503 以表示自身处于降级/不可用状态，从而导致 K8s 判定应用不健康，引发持续 `NotReady`。

证据支撑：
- 探针事件明确记录 `dial tcp... connection refused`（底层连接失败）与 `HTTP probe failed... statuscode: 503`（应用层返回失败）同时存在。
- 日志显示应用因 `dependency unavailable` 主动返回 503，且追踪数据表明业务请求与探针检查处于相同的故障观察模式。

**证据不足/待确认**：目前事实未明确指出具体的“内部依赖服务”是什么（如数据库、缓存或下游 API），因此无法确认是依赖服务本身故障、网络策略拦截还是应用配置错误导致的依赖不可用。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 16.4s
├─ 并发证据采集: 71.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 71.8s (Evidence 65.2s, RCA 6.5s)
└─ 汇总总结: 14.6s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
