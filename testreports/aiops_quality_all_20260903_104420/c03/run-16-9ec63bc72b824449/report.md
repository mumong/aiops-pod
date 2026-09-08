## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-zz82w stuck in ContainerCreating/Pending |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `configmap "unavailable-config" not found` (fact-17b9b6e0e8a3, fact-4866e5938b96) | 确认 Pod 挂载卷时找不到指定 ConfigMap 的具体报错，直接指向缺失资源。 |
| 2 | K8s Event | Kubernetes | `timed out waiting for the condition` (fact-0ec92a9e1a8b, fact-13e2ac4bafba) | 描述因前置挂载失败导致的 kubelet 超时状态，反映故障的持续性和阻塞效应。 |
| 3 | K8s State | Kubernetes | `ContainerCreating` (fact-7a942604141a) | 记录容器的当前异常挂起状态，未进入 Running 阶段。 |
| 4 | K8s State | Kubernetes | `phase: Pending` (fact-0d0f639de8e2) | 记录 Pod 的当前运行阶段，符合因依赖缺失而无法调度的特征。 |
| 5 | K8s Config | Kubernetes | `container.resource_request.cpu: "5m"` / `container.resource_limit.cpu: "50m"` (fact-047d78b75da6, fact-408f6b1731a0) | 提供该容器的资源请求与限制上下文，排除当前现象由资源超限引起。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason = 1` (reason: ContainerCreating) (fact-baeb7bcf19e7) | 通过指标确认该 Pod 处于 `ContainerCreating` 等待状态，与 K8s 事件记录一致。 |

**证据总结：**
Kubernetes 事件提供了决定性的失败原因：Pod 中的 `input` 卷试图挂载名为 `unavailable-config` 的 ConfigMap，但因该资源不存在而导致 `MountVolume.SetUp` 失败。这种挂载阻塞导致 Kubelet 持续等待超时，致使 Pod 始终卡在 `Pending` 和 `ContainerCreating` 状态。Metric 数据进一步佐证了该 Pod 处于等待原因对应的状态。

## 🎯 根因分析 · g1

### 因果链

```text
未找到 ConfigMap 'unavailable-config' → Volume 'input' 挂载失败 (MountVolume.SetUp fails) → Kubelet 持续等待超时 → Pod 滞留于 Pending/ContainerCreating
```

### 根因结论

已确认根因：Pod `aiops-case-03/workload-5b5fc86c8c-zz82w` 中的卷定义引用了名为 `unavailable-config` 的 ConfigMap，但该 ConfigMap 在当前命名空间 `aiops-case-03` 中不存在（可能已被删除或从未创建）。
直接后果：Kubelet 无法完成该卷的挂载，导致容器始终处于 `ContainerCreating` 状态。
缺失事实：无法确认该 ConfigMap 是意外被删除、从未创建，还是被遗漏在部署清单之外。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 20.1s
├─ 并发证据采集: 63.0s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 63.0s (Evidence 54.5s, RCA 8.4s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-imagepull-failed, pod-volume-mount-failed, pod-pending-unschedulable, pod-config-error
