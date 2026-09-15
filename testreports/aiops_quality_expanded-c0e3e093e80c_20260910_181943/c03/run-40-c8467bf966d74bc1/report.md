## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod workload-5b5fc86c8c-xn974 处于 Pending/ContainerCreating 状态，无法启动容器 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-03/workload-5b5fc86c8c-xn974` phase: `Pending` | 确认故障处于集群调度/启动阶段 |
| 2 | K8s Event | Kubernetes | `FailedMount`：`MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 直接锁定根本原因为配置缺失导致挂载失败 |
| 3 | K8s State | Kubernetes | `FailedMount`：`timed out waiting for the condition`（持续 103m） | 说明挂载阻塞已持续较长时间，非瞬时抖动 |
| 4 | K8s Config | Kubernetes | 资源配置：CPU Request `5m` / Limit `50m`；Memory Request `8Mi` / Limit `32Mi` | 排除资源规格不足导致调度的可能性 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1，reason=`ContainerCreating` | 指标状态与 Kubernetes 事件记录的挂载失败原因相互印证 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total` = 0 | 排除容器因启动失败引发频繁重启的可能 |

**证据说明：**
Kubernetes 事件（#2）提供了决定性的错误信息，即挂载卷 `input` 失败，原因是引用了不存在的 ConfigMap。这一事实由 Metrics 指标（#5）中记录的 `ContainerCreating` 等待状态直接印证，且由于重启数为 0（#6），故障点固定在容器启动前的挂载准备阶段，未涉及运行时的应用逻辑。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 引用缺失 ConfigMap 'unavailable-config' → kubelet 执行 MountVolume.SetUp 失败 → Pod 卡在 ContainerCreating 状态 → 容器未进入 Running
```

### 根因结论

已确认根因：Pod 的 Spec 配置中引用了 ConfigMap `unavailable-config`，但该资源在集群中不存在，导致 `kubelet` 在执行卷挂载准备时失败。这解释了为何 Pod 长期处于 `Pending/ContainerCreating` 状态且无重启记录。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 24.2s
├─ 并发证据采集: 39.6s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 39.6s (Evidence 33.0s, RCA 6.5s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-volume-mount-failed, pod-imagepull-failed
