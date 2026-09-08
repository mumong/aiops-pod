## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-zz82w 长期处于 ContainerCreating/Pending 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `status=Pending` | 确认 Pod 无法进入运行状态 |
| 2 | K8s Event | Kubernetes | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (持续 51m) | 直接指出挂载失败是由于 ConfigMap 缺失导致的，确立因果关系 |
| 3 | K8s Event | Kubernetes | `Warning FailedMount ... Unable to attach or mount volumes: unmounted volumes=[input]: timed out waiting for the condition` (持续 49m) | 证实挂载卷操作因条件未满足而长时间阻塞，符合 ConfigMap 不存在时的表现 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason=ContainerCreating, value=1, timestamp=2026-09-03T07:02:57Z) | 独立验证容器长期处于创建等待中 |

证据 1、4 共同确认 Pod 处于停滞状态；证据 2、3 提供了导致停滞的具体机制：kubelet 在尝试挂载名为 `input` 的卷时，因为找不到 ConfigMap `unavailable-config` 而直接报错或超时，这构成了从状态到根因的唯一证据链。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 声明了 ConfigMap volume 'unavailable-config' (事实 1) → ConfigMap 'unavailable-config' 在 namespace 'aiops-case-03' 中不存在 → kubelet 挂载卷失败，触发 FailedMount 事件 (证据 2、3) → Pod 因卷挂载失败而永远处于 ContainerCreating/Pending 状态 (证据 1、4)
```

### 根因结论

已确认根因：Pod YAML 中声明的 ConfigMap volume `unavailable-config` 不存在。
Kubernetes 调度器虽然成功调度了 Pod（`PodScheduled=True`），但在 kubelet 阶段，由于该 ConfigMap 缺失，卷挂载操作直接失败（`configmap "unavailable-config" not found`）。因为这是一个非可选挂载点，Kubernetes 不会让容器启动，导致 Pod 永远阻塞在 `ContainerCreating/Pending` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 34.2s
├─ 并发证据采集: 66.0s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 66.0s (Evidence 57.6s, RCA 8.2s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed
