## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod workload-5b5fc86c8c-2xgjz 处于 ContainerCreating/Pending 状态，无法启动容器。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedMount` [fact-77067b236293]: `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 直接指明挂载失败原因：缺少依赖的 ConfigMap |
| 2 | K8s State | Kubernetes | Pod Phase: `Pending` [fact-bcc74a5b2a71]；状态 `ContainersNotReady` [fact-020005562caf] | 确认 Pod 处于调度等待/未就绪状态 |
| 3 | K8s State | Kubernetes | Container `app` waiting reason: `ContainerCreating` [fact-706b85ce5756] | 明确异常状态分类 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值为 `1` [fact-d5b0979be718]，label: `reason="ContainerCreating"` | 指标层证实 Pod 持续处于挂载/启动阻塞中 |

**证据关联说明：**
Kubernetes Event `fact-77067b236293` 提供了明确的缺失资源标识（`unavailable-config`），该事实直接支撑了 Pod 无法从 `ContainerCreating` 向前推进的阻塞状态（`fact-706b85ce5756`, `fact-d5b0979be718`）。Pod 始终处于 `Pending` 且未重启过（`restart_count: 0`），说明故障发生在容器启动前的挂载阶段。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 不存在 → Volume 'input' 挂载非可选且依赖缺失 → Kubelet FailedMount 阻塞 → Pod 持续 Pending/ContainerCreating
```

### 根因结论

**已确认根因：** Pod YAML 中 volume `input` 绑定（引用）了一个在 `aiops-case-03` 命名空间中不存在的 ConfigMap `unavailable-config`（且该挂载被配置为非可选）。

该配置错误导致 kubelet 在挂载卷阶段失败，并持续超时阻断 Pod 的启动流程，表现为 Pod 长期滞留于 `Pending` / `ContainerCreating` 状态。证据编号：`fact-77067b236293`, `fact-020005562caf`, `fact-d5b0979be718`。

---

## 📊 性能统计

```text
├─ 总耗时: 57.0s
├─ 问题定位: 20.8s
├─ 并发证据采集: 27.5s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 27.5s (Evidence 20.4s, RCA 7.0s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-volume-mount-failed
