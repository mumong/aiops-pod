## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-zz82w 处于 Pending/ContainerCreating 状态，Volume 'input' 挂载失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `fact-1b1a87b7fb1f`: `FailedMount`: MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found | 直接指示 Volume 'input' 挂载失败的核心错误 |
| 2 | K8s Event | kubernetes | `fact-dadcda2588d4`: `FailedMount`: Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition | 佐证挂载持续超时 |
| 3 | K8s State | kubernetes | `fact-0646b2c5d359`: pod.phase `Pending`; `fact-04113a6a0aec`: container.waiting_reason `ContainerCreating` | 确认 Pod 卡在启动前状态，未进入运行态 |
| 4 | K8s Event | kubernetes | `fact-4df118e49862`: Ready `False` (ContainersNotReady: [app]) | 确认应用容器未就绪 |
| 5 | Metric | prometheus | `fact-3247f4732751`: `kube_pod_container_status_waiting_reason` 值为 `1` (reason: `ContainerCreating`) | 从监控视角确认容器等待原因与 K8s 状态一致 |
| 6 | Metric | prometheus | `fact-a92a86e45467`: `kube_pod_container_status_restarts_total` 值为 `0` | 确认 Pod 从未成功运行过，无重启行为 |
| 7 | K8s Config | kubernetes | `fact-04113a6a0aec`/`fact-6c2a746c4705`: 资源 Request/Limit CPU 50m/5m, Memory 8Mi/32Mi | 排除资源不足导致的调度或启动失败 |

**证据互证说明：**
- 事件与状态数据（#1-4）一致指向挂载失败是 Pod 停留在 `Pending` 状态的原因。
- 指标数据（#5-6）从外部监控视角确认了等待原因为 `ContainerCreating`，且因从未启动故重启计数为 0，排除了应用启动后崩溃的可能性。
- 资源配置（#7）显示请求极低，排除了资源争用。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 缺失 → VolumeMount 依赖校验失败 → MountVolume.SetUp failed → Pod 卡在 Pending/ContainerCreating 状态
```

### 根因结论

已确认根因为 **Pod 定义中引用的 ConfigMap `unavailable-config` 在命名空间 `aiops-case-03` 中不存在**。

根据 K8s 事件事实 `fact-1b1a87b7fb1f`，kubelet 在执行 Volume 挂载时明确报错 `configmap "unavailable-config" not found`。由于该 Volume 未被标记为 `optional`，挂载校验失败导致 Pod 无法完成初始化，从而进入 `Pending` 状态（事实 `fact-0646b2c5d359`）。指标 `fact-3247f4732751` 确认了容器一直停留在 `ContainerCreating` 阶段。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 23.7s
├─ 并发证据采集: 71.4s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 71.4s (Evidence 63.7s, RCA 7.6s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-imagepull-failed, pod-sandbox-create-failed
