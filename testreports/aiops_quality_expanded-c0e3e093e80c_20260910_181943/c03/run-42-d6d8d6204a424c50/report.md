## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod workload-5b5fc86c8c-xn974 处于 Pending/ContainerCreating 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` (fact-43871e590b97) | `Warning FailedMount ... Unable to attach or mount volumes: unmounted volumes=[input]` | 确认底层挂载机制阻塞在 `input` 卷，导致容器无法创建。 |
| 2 | K8s Event | `kubelet` (fact-b77230262543) | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 明确指出 `input` 卷因依赖的 ConfigMap 不存在而挂载失败。 |
| 3 | K8s State | `container.waiting_reason` (fact-c4d1f037e907) | `reason: ContainerCreating` | 确认应用容器 `app` 正处于等待阶段，状态停滞。 |
| 4 | Metric | `kube_pod_container_status_waiting_reason` (fact-b8e168456538) | `value: 1` (labels: `reason: ContainerCreating`) | 验证集群指标与 K8s 事件中的等待状态一致。 |
| 5 | K8s State | `pod.phase` (fact-566cbf4bd083) | `phase: Pending` | 确认 Pod 处于调度后的挂载/启动阻塞期，尚未进入运行态。 |

**证据说明**：K8s 事件（#1, #2）提供了最直接的因果证据，指明 `input` 卷因找不到 `unavailable-config` 导致挂载失败，从而引发容器处于 `ContainerCreating` 状态（#3）。Metric 数据（#4）从监控维度独立印证了该等待状态的存在。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 在 aiops-case-03 中缺失 → Pod Spec 中 Volume 'input' 引用该 ConfigMap 且未设为 Optional → Kubelet 执行 MountVolume.SetUp 失败 → Pod 停留在 Pending/ContainerCreating 状态
```

### 根因结论

**已确认根因：Pod 依赖的 ConfigMap 缺失导致挂载失败**
Kubelet 事件明确记录 `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (证据 #2)。由于该 Volume 依赖的 ConfigMap 不存在，Kubelet 无法完成挂载操作，导致 Pod 被阻塞在 `ContainerCreating` 阶段，无法启动应用容器。该结论由 K8s 状态（证据 #3, #5）与 Metric 指标（证据 #4）相互印证。

---

## 📊 性能统计

```text
├─ 总耗时: 52.0s
├─ 问题定位: 14.0s
├─ 并发证据采集: 28.7s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 28.7s (Evidence 20.5s, RCA 7.9s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-volume-mount-failed, pod-sandbox-create-failed
