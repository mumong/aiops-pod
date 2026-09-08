## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-2xgjz 处于 ContainerCreating/Pending 状态，容器未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `status: Pending`, `phase: Pending` | 确认 Pod 停留在初始化/等待阶段 |
| 2 | K8s Event | Kubernetes | `FailedMount`: MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found | 确认因 ConfigMap 缺失导致挂载失败 |
| 3 | K8s Event | Kubernetes | `FailedMount`: Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input] | 确认挂载卷持续未就绪状态 |
| 4 | K8s Config | Kubernetes | `container.resource_request.memory`: 8Mi, `container.resource_limit.memory`: 32Mi | 确认内存资源请求与限制范围 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 确认容器处于等待创建的实时状态 |
| 6 | K8s State | Kubernetes | `container.waiting_reason{container="app"} = "ContainerCreating"` | 确认容器等待挂载卷条件满足 |

**证据关联说明：**
Kubernetes 的 Event 记录 (证据 2, 3) 提供了故障的直接原因（找不到 `unavailable-config` ConfigMap），解释了 K8s State 中 Pod 为什么处于 `Pending` 且容器等待原因为 `ContainerCreating`（证据 1, 6）。Prometheus 指标（证据 5）进一步从监控维度印证了容器当前仍然卡在等待创建的状态，确认了故障的持续性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 配置引用不存在的 ConfigMap 'unavailable-config' → kubelet 挂载卷 'input' 失败 → 容器无法启动 → Pod 处于 Pending/ContainerCreating 状态
```

### 根因结论

**已确认的根因**：Pod 定义中引用的 ConfigMap `unavailable-config` 在集群中不存在，导致 `kubelet` 在执行 `MountVolume.SetUp` 时失败，进而使 Pod 无法进入 Running 状态。

该结论由以下事实支撑：
- 证据 2 中的 K8s Event 明确报告 `configmap "unavailable-config" not found` 导致挂载失败。
- 证据 1 和 6 确认了 Pod 因容器未就绪而卡在 `Pending` 和 `ContainerCreating` 状态。
- 证据 5 的指标确认了当前等待原因确认为 `ContainerCreating`。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 25.7s
├─ 并发证据采集: 30.9s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 30.9s (Evidence 22.2s, RCA 8.5s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-volume-mount-failed
