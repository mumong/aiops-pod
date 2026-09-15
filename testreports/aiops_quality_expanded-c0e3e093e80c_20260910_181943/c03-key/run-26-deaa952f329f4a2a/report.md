## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload 卡在 ContainerCreating 状态，无法启动应用容器 app。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet (fact-31ffcf2d33e6) | `Warning FailedMount... configmap references non-existent config key: unavailable-key` (117s 内发生 23 次) | 确认卷挂载失败的根本原因是 ConfigMap 引用了不存在的 key |
| 2 | K8s Event | kubelet (fact-401c331b0947) | `Warning FailedMount... timed out waiting for the condition` (10m 内发生 10 次) | 证实挂载操作因上游校验失败而持续超时 |
| 3 | K8s State | Pod/Container (fact-0f546153a17b) | `pod.status: Pending` | 显示 Pod 当前处于挂起状态 |
| 4 | K8s State | Container (fact-b381c3474aae) | `container.waiting_reason: ContainerCreating` | 显示容器卡在初始化阶段，未进入运行态 |
| 5 | K8s Config | Container (fact-12556ef2e248) | `container.resource_limit.memory: 32Mi` | 提供运行资源上下文，排除资源不足作为直接原因 |
| 6 | Metric | Prometheus (fact-2617aabba362) | `kube_pod_container_status_waiting_reason` = 1 (label: reason="ContainerCreating") | 监控指标确认容器等待状态，与事件日志一致 |

证据 1 (FailedMount) 和 证据 2 (Timed Out) 互相印证，明确指出挂载卷 `input` 因 ConfigMap key 缺失而失败，直接导致了 证据 3 (Pending) 和 证据 4 (ContainerCreating) 所呈现的 Pod 状态停滞。监控数据 (证据 6) 在宏观层面复现了该异常状态。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-input' 不存在 key 'unavailable-key' → kubelet 卷挂载校验失败 (FailedMount) → MountVolume.SetUp 失败且超时 → Pod 处于 ContainerCreating/Pending 状态，无法启动应用
```

### 根因结论

**已确认根因**：Pod 的 `volume 'input'` 挂载了 ConfigMap `workload-input`，但该 ConfigMap 中不存在 Spec 中引用的 key `unavailable-key` (证据 1)。这导致 kubelet 在初始化卷挂载时校验失败 (证据 2)，进而使 Pod 无法完成初始化，始终停留在 `ContainerCreating` 状态 (证据 3, 4)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.8s
├─ 并发证据采集: 43.9s
│  └─ g1 aiops-case-v05/workload: 43.9s (Evidence 35.3s, RCA 8.2s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-volume-mount-failed, pod-pending-unschedulable
