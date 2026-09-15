## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v15/workload` | CrashLoopBackOff | Pod workload in aiops-case-v15 is in CrashLoopBackOff state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | Exit Code: 137 / Reason: OOMKilled (8条聚合事件) | 直接证据：确认进程被内核 OOM Killer 强制终止。 |
| 2 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` = OOMKilled | 外部指标印证：Pod 容器最后一次异常退出原因为内存超限。 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory` = 64Mi | 资源约束：容器被硬限制在 64 MiB 内存内。 |
| 4 | Logging | Elasticsearch | `startup allocation 256Mi` | 应用行为：应用启动阶段显式请求了 256 MiB 内存空间。 |
| 5 | K8s State | Kubernetes | `container.waiting_reason` = CrashLoopBackOff | 状态表现：Pod 因频繁重启进入退避循环，验证了重启机制。 |

证据说明：
*   **逻辑冲突**：Logging 显示的 `256Mi` 申请量是 K8s Config 中 `64Mi` 硬限制的 4 倍，这种资源供需的极端不匹配直接导致了 `exit_code 137`。
*   **多维度印证**：K8s 状态机（Event/OOMKilled/CrashLoopBackOff）与 Prometheus 指标（`last_terminated_reason`）对同一事件提供了独立且一致的事实支撑。
*   **非调度问题**：Pod 处于 `Running` 阶段，排除了集群资源不足导致的调度失败，故障完全发生在容器运行时环境内。

## 🎯 根因分析 · g1

### 因果链

```text
应用启动分配 256Mi (Logging) > 容器限制 64Mi (K8s Config) → 内核 OOM Killer 终止进程 (Exit Code 137) → 触发 CrashLoopBackOff (K8s State)
```

### 根因结论

已确认根因为 **容器内存资源规格配置过低导致应用启动时 OOM（Out Of Memory）崩溃**。

具体而言，Pod `workload` 中的 `app` 容器被设定的硬内存限制（`limit`）仅为 64 MiB（证据 #3），而应用自身的启动指令或逻辑需要分配 256 MiB 的内存空间（证据 #4）。由于请求量超过限制，Linux 内核的 OOM Killer 机制介入并杀死了该容器进程，导致进程以 `Exit Code 137` 退出（证据 #1）。Kubernetes 依据重启策略不断重试启动，从而形成了“启动 -> 超内存 -> 被杀 -> 退避重启”的 CrashLoopBackOff 故障闭环。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 21.2s
├─ 并发证据采集: 62.2s
│  └─ g1 aiops-case-v15/workload: 62.2s (Evidence 53.1s, RCA 8.9s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-v15/workload**: pod-crashloop-runtime
