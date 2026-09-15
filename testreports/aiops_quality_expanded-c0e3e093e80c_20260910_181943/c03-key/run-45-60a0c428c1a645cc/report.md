## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | aiops-case-v05/workload Pod stuck in ContainerCreating/Pending state due to FailedMount |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | fact-23d0b83bb795 | FailedMount: configmap references non-existent config key: unavailable-key (40次/73m) | 核心证据：明确指出 ConfigMap 缺键导致挂载失败 |
| 2 | K8s Event | fact-ff46f0865e94 | 无法挂载卷 [input]，超时等待 (31次/71m) | 佐证：证实挂载动作持续阻塞 |
| 3 | Metric | fact-d011b10468ce | kube_pod_container_status_waiting_reason = 1 (reason: ContainerCreating) | 佐证：当前处于等待挂载状态 |
| 4 | K8s Config | fact-abd0c27cbe88 | pod.status = Pending | 佐证：Pod 状态停留在等待阶段 |
| 5 | Metric | fact-b3a3616d5477 | kube_pod_container_status_restarts_total = 0 | 排除重启：容器尚未启动 |

Kubernetes 事件（#1, #2）直接揭示了挂载失败的底层原因，即 `unavailable-key` 不存在。Metric（#3）与 Pod 状态（#4）共同确认了 Pod 正处于因挂载阻塞而导致的 `ContainerCreating` 等待期。重启计数为 0（#5）与 Pod 尚未进入运行阶段的事实相符，排除了应用启动后崩溃的可能性。

## 🎯 根因分析 · g1

### 因果链
```text
ConfigMap `workload-input` 缺键 `unavailable-key` → kubelet 挂载卷失败 → FailedMount 错误累积 → Pod 卡在 ContainerCreating/Pending 状态
```

### 根因结论
已确认的根因为：Pod 挂载卷 `input` 依赖的 ConfigMap `workload-input` 缺少所需的配置键 `unavailable-key`（证据 #1, #2）。该缺失导致 kubelet 无法完成挂载操作，从而将 Pod 阻塞在 ContainerCreating/Pending 状态（证据 #3, #4），容器因此从未启动且无重启（证据 #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 58.4s
├─ 问题定位: 20.9s
├─ 并发证据采集: 30.1s
│  └─ g1 aiops-case-v05/workload: 30.1s (Evidence 21.6s, RCA 8.4s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-volume-mount-failed
