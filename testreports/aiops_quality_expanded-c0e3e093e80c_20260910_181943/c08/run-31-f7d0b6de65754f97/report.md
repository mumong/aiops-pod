## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | Pod aiops-case-08/workload-5c9c7b6489-p8462处于CrashLoopBackOff状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 状态为 `OOMKilled`，退出码 137（fact-674a0c0d5b1b, fact-0cf948db0459） | 确诊内核强制终止，直接指向资源耗尽（内存） |
| 2 | K8s Config | Kubernetes | 容器 `app` 配置了 `memory_limit: 64Mi`，`memory_request: 24Mi`（fact-0d39ee558037, fact-3e119cb53345） | 确认存在硬性资源瓶颈，且上限非常低 |
| 3 | K8s Event | Kubernetes | 连续 97 分钟内 `kubelet` 发出 `BackOff` 事件，反复重启失败（fact-15e9dd3e4121, fact-1c084a90277c） | 证实故障处于持续发生的 CrashLoop 状态 |
| 4 | Metric | Prometheus | 容器重启总数 `kube_pod_container_status_restarts_total` 在观测窗口内从 15.0 增至 20.0（fact-16d061e255f9） | 量化崩溃频率，印证 K8s Event 描述的循环现象 |
| 5 | Logging | Elasticsearch | 日志显示应用在 5 分钟内 8 次出现 `memory allocation advanced`，且 `allocated_mib` 在 2.0 至 48.0 之间波动（fact-aggregated-logs） | 证明应用在处理请求时发生内存分配行为 |
| 6 | Tracing | Tempo/Deepflow | Tempo Span 标记 `aiops.observed_mode: oom_growth`，对应 Deepflow Flow 请求路径为 `GET /work`（fact-67a2e56057ca, fact-flow-getwork） | 将 OOM 现象与具体的触发端点 `/work` 关联起来 |

**证据说明：**
Kubernetes 的 `OOMKilled` 状态和退出码 137 提供了最直接的死因证据。Metric 中的重启上升趋势与 K8s Event 相互印证。日志确认了内存分配的活跃性，而 Tracing 数据进一步将这一行为锁定在 `GET /work` 请求上，结合 64Mi 的硬性内存上限，构成了完整的证据链。

## 🎯 根因分析 · g1

### 因果链

```text
配置了 64Mi 的容器内存限制 → 容器在处理 GET /work 请求时内存分配持续增长 → 内存使用超出硬限制触发内核 OOMKiller → 容器崩溃、重启并进入 CrashLoopBackOff
```

### 根因结论

**已确认的根因：应用容器内存资源限制配置过低（64Mi）。**

当前应用在处理业务请求时存在持续的内存分配增长行为。由于容器被硬限制在 64Mi 的内存上限，一旦应用运行时的内存占用触及该界限，Kubernetes 内核便会强制杀死进程。这直接导致了容器反复崩溃并触发 Kubernetes 的自动重启机制，表现为 `CrashLoopBackOff`。

支持证据包括：容器直接死因为 `OOMKilled`（证据 #1）、明确的 64Mi 内存上限配置（证据 #2）、以及通过 Trace 和 Log 确认的 `/work` 端点触发的内存分配行为（证据 #5, #6）。现有证据已充分闭环，无需更多数据即可确认此根因。

---

## 📊 性能统计

```text
├─ 总耗时: 5.2m
├─ 问题定位: 12.8s
├─ 并发证据采集: 286.0s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 286.0s (Evidence 277.3s, RCA 8.5s)
└─ 汇总总结: 12.4s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
