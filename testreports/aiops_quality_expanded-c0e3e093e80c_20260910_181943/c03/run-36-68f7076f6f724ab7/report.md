## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | workload-5b5fc86c8c-xn974 处于 ContainerCreating 状态，Pod 阶段为 Pending |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount` Warning (x50): MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found | 直接证明卷挂载因 ConfigMap 缺失失败 |
| 2 | K8s State | kubernetes | Pod 状态为 `Pending`，Pod 阶段为 `Pending` | 确认 Pod 处于调度后无法启动的阶段 |
| 3 | K8s State | kubernetes | Pod 状态为 `ContainerCreating` (x36): unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition | 说明容器因卷未挂载被永久阻塞 |
| 4 | K8s Config | kubernetes | 容器 `app` 的内存 request `8Mi` / limit `32Mi` | 排除资源分配不足导致的调度或启动问题 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 持续处于等待状态，无进展 |
| 6 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"} = 1` | 确认 Pod 未脱离 Pending 状态 |
| 7 | Metric | prometheus | `kube_pod_container_status_restarts_total = 0` | 确认容器从未尝试运行，不存在运行态资源耗尽问题 |

证据 1 揭示了底层触发机制：指定的 ConfigMap 不存在且配置为非可选；证据 2、3 和 5 从多维度证实了 Pod 卡在启动挂载阶段的现象；证据 4 排除了资源竞争；证据 7 确认了该 Pod 始终未进入运行态，支持故障处于初始化阶段的判断。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 在 'aiops-case-03' 命名空间中缺失 → 强制挂载非可选卷失败 → 触发 FailedMount 并持续重试 → Pod 处于 Pending/ContainerCreating 状态
```

### 根因结论

**已确认的根因**：Pod 定义中挂载了名为 `unavailable-config` 的 ConfigMap 卷，但该 ConfigMap 在目标命名空间中不存在，且配置为强制挂载。

这导致 kubelet 无法完成卷挂载，Pod 始终被阻塞在 `ContainerCreating` 状态，无法拉起容器。关键证据表明 `FailedMount` 事件由 `configmap "unavailable-config" not found` 引起（见证据 #1），且监控数据证实 Pod 持续处于 Pending 和 ContainerCreating 状态（见证据 #2, #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.4s
├─ 并发证据采集: 44.6s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 44.6s (Evidence 35.4s, RCA 9.1s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-volume-mount-failed, pod-config-error
