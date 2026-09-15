## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod 定义中引用了不存在 Secret `unavailable-input` 挂载到卷 `input`，导致 VolumeMount 失败，容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | 容器 `app` 处于 `ContainerCreating` 等待状态 (`fact-9fb325defb6e`) | 确认容器卡在启动初始化阶段，未进入运行态 |
| 2 | K8s State | `kubernetes` | Pod 条件 `ContainersReady: False`，原因 `ContainersNotReady: [app]` (`fact-5a82aad76328`) | 明确指示 Pod 处于 Pending 阶段，等待容器资源/配置就绪 |
| 3 | K8s State | `kubernetes` | Pod 整体状态 `phase: Pending`，重启计数为 0 (`fact-8c7718a3f619`, `fact-d0e654f73ca9`) | 验证容器从未成功启动过，处于初始挂起状态 |
| 4 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason` 记录 `ContainerCreating` 状态且值为 1 (`fact-e99cbd3bd1a7`) | 外部监控指标印证 K8s API 中的容器状态 |

当前异常组中 Logging 与 Tracing 维度均为 `not_applicable`（容器未启动且无 Pod IP），无其他维度的直接报错原文。正式诊断依据为 Pod 配置引用了不存在的 Secret `unavailable-input`，导致卷挂载失败，容器无法启动。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 引用不存在 Secret unavailable-input → 卷 input 挂载失败 → 容器 app 卡在 ContainerCreating → Pod 处于 Pending 状态
```

### 根因结论

已确认的根因是 **Pod 定义中引用了不存在的 Secret `unavailable-input`**。

该配置错误导致 Pod 在调度后无法完成卷挂载，进而使得容器 `app` 停滞在 `ContainerCreating` 阶段（见证据 1-4），表现为 Pod 状态为 `Pending` 且 `ContainersReady` 为 `False`。现有的 K8s 状态和 Metric 证据一致支持该容器未启动且卡在初始化阶段的结论。

---

## 📊 性能统计

```text
├─ 总耗时: 59.5s
├─ 问题定位: 22.0s
├─ 并发证据采集: 30.0s
│  └─ g1 aiops-case-v04/workload: 30.0s (Evidence 25.3s, RCA 4.6s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-imagepull-failed, pod-pending-unschedulable, pod-volume-mount-failed
