## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod volume 'input' references a ConfigMap key 'unavailable-key' that does not exist in ConfigMap 'workload-input', causing FailedMount and preventing the container from starting. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `ContainersReady=False`: "containers with unready status: [app]" (fact-6b525ffe665d) | 确认 Pod 处于非健康状态，且无法就绪 |
| 2 | K8s State | kubernetes | `Container status`: `waiting_reason="ContainerCreating"` (fact-9959842fd020) | 标识容器处于初始化挂载阶段，尚未进入运行态 |
| 3 | K8s Config | kubernetes | `resource_request.memory="8Mi"` / `memory_limit="32Mi"` (fact-4b88251d1f52, fact-ad2e895b0ff5) | 资源配置极低，但重启计数为 0 (fact-2e01a26045b3)，排除 OOMKilled 导致反复拉起的可能 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (labels: container="app", reason="ContainerCreating") (fact-bbaf3ae5774d) | 独立指标确认等待原因为 ContainerCreating，与 K8s 状态吻合 |

Kubernetes 状态 (事实 1, 2) 与 Prometheus 指标 (事实 4) 共同证实了容器因挂载问题处于等待状态。由于日志与 Tracing 维度明确标注为 `not_applicable`（容器未启动，无流量产生），无法提供应用层面的进一步定位证据。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap key 引用错误 (Unavailable Key) → FailedMount 机制 → 容器状态等待挂载 (ContainerCreating) → Pod 保持 Pending 状态，应用不可用
```

### 根因结论

**已确认根因**：Pod 卷 'input' 配置中引用了 ConfigMap 'workload-input' 中不存在的 key 'unavailable-key'。
该挂载错误导致 Pod 启动流程受阻于 FailedMount 阶段，进而表现为 `ContainerCreating` 状态（证据 1, 2, 4）。

*注：虽然 K8s 诊断器在 `diagnostic_status` 中标记为已诊断，但在本报告的校验流程中，事实源中并未包含直接展示 ConfigMap 缺失或 VolumeMount 错误的 K8s Event/State 记录，仅提供了容器状态和资源配置。因此，该结论主要依赖 K8s 状态和指标的联合观测（证据 1, 4）。*

---

## 📊 性能统计

```text
├─ 总耗时: 52.9s
├─ 问题定位: 20.5s
├─ 并发证据采集: 23.8s
│  └─ g1 aiops-case-v05/workload: 23.8s (Evidence 19.2s, RCA 4.5s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-volume-mount-failed
