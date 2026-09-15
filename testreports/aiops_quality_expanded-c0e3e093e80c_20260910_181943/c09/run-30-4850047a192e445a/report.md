## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod workload-5f4fb9ff45-5mlnc (aiops-case-09) 处于 NotReady 状态，Ready/ContainersReady均为False，由 Readiness Probe 持续返回 503 导致。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Pod Condition | `Ready: False (ContainersNotReady: app)` | 确认 Pod 当前处于非就绪状态，应用容器 `app` 无法提供服务 |
| 2 | K8s Event | K8s Event | `Warning Unhealthy 30s (x1558 over 75m) kubelet Readiness probe failed: HTTP probe failed with statuscode: 503` | 揭示持续 75 分钟的 Ready 探针失败现象，且直接报错为 503 |
| 3 | Tracing | Deepflow HTTP Flow | `GET /work -> 503`, `src_ip: 172.16.104.62 -> dst_ip: 172.16.104.16`, 9 次重复 | 确认为应用内部自身发起的请求持续返回 503，排除网络不通导致的探针失败 |
| 4 | Logging | Elasticsearch Log | `dependency unavailable` (http_status: 503, path: `/work`), 8 次 | 确认 503 由应用层业务逻辑触发（业务依赖缺失），而非资源过载或宕机 |
| 5 | K8s Config | K8s Resource Limits | `cpu_limit: 200m`, `memory_limit: 96Mi` | 资源限制存在，但结合日志中无 OOM/Killed 记录，排除资源争抢导致的 503 |
| 6 | K8s Config | K8s Resource Requests | `cpu_request: 20m`, `memory_request: 24Mi` | 资源分配正常，容器未因调度问题被驱逐 |

**证据分析：**
K8s 事件（#2）与深度流追踪（#3）高度一致，均指向 `/work` 端点持续返回 503。日志证据（#4）提供了关键的因果解释：该 503 是由“业务依赖不可用（dependency unavailable）”引起的应用层拒绝，而非 Kubernetes 基础设施问题。由于应用容器本身处于 Running 状态且无重启（重启计数为 0），可以判定应用进程存活但业务逻辑故障，直接导致了探针的持续失败。

## 🎯 根因分析 · g1

```text
应用服务内部依赖不可用（具体组件未确认） → HTTP GET /work 端点持续返回 503 错误码 → Readiness Probe 连续失败（75分钟内触发1558次） → Kubelet 移除 Pod Ready 条件，状态变更为 NotReady
```

**根因结论：**
已确认根因为**应用服务自身的业务逻辑故障导致健康检查接口持续返回 503 错误**。
*   **证据支撑**：日志记录明确显示 `dependency unavailable`（#4），配合 Deepflow 追踪确认该 503 为内部 HTTP 请求返回（#3），进而导致 Kubelet 探针持续失败（#2）。
*   **未知项**：日志仅记录了“依赖不可用”，但未指明具体的下游依赖地址或组件名称，因此**具体是哪个下游依赖缺失或故障无法从当前事实中确定**。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 23.0s
├─ 并发证据采集: 75.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 75.8s (Evidence 64.3s, RCA 11.3s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
