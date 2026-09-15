## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod `workload` 的 VolumeMount 配置引用了缺失的 Secret `unavailable-input`，导致 kubelet 无法挂载卷，容器卡在 `ContainerCreating` 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount  5s (x8 over 15m)    kubelet            Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition` | 明确指向挂载卷失败，确认卷名 `input` 无法挂载 |
| 2 | K8s Event | kubernetes | `Warning FailedMount  96s (x16 over 17m)  kubelet            MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found` | 给出挂载失败的根本原因：引用了不存在的 Secret `unavailable-input` |
| 3 | K8s State | kubernetes | `pod.phase: Pending`, `pod.status: Pending` | 确认 Pod 停留在 Pending 状态，尚未进入运行阶段 |
| 4 | K8s State | kubernetes | `container.waiting_reason: ContainerCreating` (container: `app`) | 确认容器处于挂载卷的等待状态，尚未启动应用逻辑 |
| 5 | K8s Config | kubernetes | `container.resource_request.cpu: 5m`, `container.resource_limit.cpu: 50m` | 资源请求与限制配置，确认不是 CPU 资源不足导致挂起 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 验证了容器持续处于 ContainerCreating 状态的指标事实 |

**证据关联说明**：
Kubernetes Event 中的两次 `FailedMount` 记录提供了最直接的因果关系链，明确指出了 `secret "unavailable-input" not found` 是挂载失败的直接原因。Kubernetes State 和 Metric 数据共同印证了 Pod 当前卡在 `Pending`/`ContainerCreating` 状态的持续性现象。配置与资源指标正常，排除了资源调度问题。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义引用了不存在的 Secret "unavailable-input" → kubelet 执行 MountVolume 失败并触发 FailedMount 事件 → 容器无法挂载卷，状态卡在 ContainerCreating → Pod 整体处于 Pending 状态，用户无法访问服务
```

### 根因结论

已确认根因：Pod `workload` 的 VolumeMount 配置引用了缺失的 Secret `unavailable-input`，导致 kubelet 无法挂载卷。

证据来源：
- K8s Event `fact-25b8fd30dfa4` 和 `fact-db3ce16592a3` 明确记录挂载失败的具体错误信息，指向 Secret 不存在。
- K8s State `fact-34619db7513f` 显示容器处于 `ContainerCreating` 状态，与挂载失败直接相关。
- K8s State `fact-79a6a8bb32d8` 和 `fact-c3946accf1f2` 显示 Pod 处于 `Pending` 状态，进一步确认了故障现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 17.7s
├─ 并发证据采集: 41.1s
│  └─ g1 aiops-case-v04/workload: 41.1s (Evidence 35.2s, RCA 5.9s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-volume-mount-failed
