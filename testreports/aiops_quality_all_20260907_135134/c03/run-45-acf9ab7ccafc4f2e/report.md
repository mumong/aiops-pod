## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod 配置中声明了引用 ConfigMap 'unavailable-config' 的卷 'input'，但该 ConfigMap 在命名空间 'aiops-case-03' 中不存在。由于卷配置未标记为 Optional，Kubelet 在执行 MountVolume.SetUp 阶段时因找不到依赖资源而持续失败，导致 Pod 状态卡在 Pending/ContainerCreating，无法调度容器启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount`: `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 指出卷挂载失败的确切原因为依赖的 ConfigMap 缺失 |
| 2 | K8s State | kubernetes | `phase: Pending`, `status: Pending`, `container.waiting_reason: ContainerCreating` | 证实 Pod 因无法完成初始化而处于等待状态 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值为 `1`，标签 `reason: ContainerCreating` | 通过监控指标从另一个维度确认 Pod 处于容器创建等待阶段 |
| 4 | K8s Event | kubernetes | `FailedMount`: `timed out waiting for the condition` (x31) | 记录挂载失败是一个持续存在的现象 |
| 5 | K8s State | kubernetes | `container.restart_count: 0` | 排除容器因崩溃重启导致的异常，定位在启动前阶段 |

**证据关联说明：**
Kubernetes 状态 (fact-17f721eed1ae, fact-f1645c9d480b) 与 Prometheus 监控指标 (fact-9169d849a02c) 在 `Pending/ContainerCreating` 现象上达成一致。事件日志中的 `configmap "unavailable-config" not found` (fact-fcd395e90b12) 为这一阻塞状态提供了直接的原因解释。

## 🎯 根因分析 · g1

### 因果链

```text
缺失必要配置资源 (ConfigMap 'unavailable-config') → Kubelet 卷挂载阶段 (MountVolume.SetUp) 查找失败 → Pod 初始化阻塞，无法创建容器沙箱 → Pod 状态持续为 Pending / ContainerCreating
```

### 根因结论

**已确认的根因：**
Pod 配置中声明的卷 `input` 引用了 ConfigMap `unavailable-config`，但该 ConfigMap 在 `aiops-case-03` 命名空间中不存在。由于配置中未标记为 `Optional`，Kubelet 在 `MountVolume.SetUp` 阶段因找不到依赖资源而报错 (fact-fcd395e90b12)，导致 Pod 卡在 `Pending` 状态 (fact-17f721eed1ae) 且无法进入运行态。Metric (fact-9169d849a02c) 进一步印证了容器持续处于 `ContainerCreating` 等待原因中。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 23.3s
├─ 并发证据采集: 37.2s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 37.2s (Evidence 30.3s, RCA 6.8s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-sandbox-create-failed, pod-imagepull-failed
