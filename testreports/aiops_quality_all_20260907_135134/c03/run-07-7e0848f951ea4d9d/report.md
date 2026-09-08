## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-2xgjz 卡在 ContainerCreating / Pending 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (fact-50dcb5ed3322) | 提供挂载失败的核心事实，明确缺失的 ConfigMap 名称。 |
| 2 | K8s Event | kubernetes | `Warning FailedMount ... timed out waiting for the condition` (fact-ae96b59ef4ac) | 确认挂载尝试持续失败并达到超时阈值。 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` (fact-055d5b096600) | 证实容器处于 Waiting 状态，与 K8s 事件中的挂载卡死现象一致。 |
| 4 | K8s State | kubernetes | `pod.status = Pending` (fact-dd077feb7cf9) | 确认 Pod 处于 Pending 状态。 |
| 5 | K8s State | kubernetes | `container.resource_limit.memory = 32Mi` (fact-0a2664da741e) | 确认 Pod 的资源限制配置，非导致挂载失败的因素。 |

**证据说明**：
Prometheus 监控指标 (`kube_pod_container_status_waiting_reason`) 证实了容器卡在 `ContainerCreating` 状态，这与 Kubernetes 事件日志中显示的 `FailedMount` 及其底层原因（ConfigMap 缺失）完全印证。所有 Kubernetes 状态与指标均一致指向同一根因。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 在命名空间 'aiops-case-03' 中缺失 → kubelet 挂载 Volume 'input' 失败并持续重试 → 容器 'app' 无法完成挂载并进入 Running 状态 → Pod 状态维持在 Pending/ContainerCreating
```

### 根因结论

已确认根因为**配置错误**：Pod 定义中引用的 ConfigMap `unavailable-config` 在 `aiops-case-03` 命名空间中不存在，导致 `kubelet` 挂载卷失败。这一结论由 K8s 事件日志 (`FailedMount`) 提供直接证据，并由 Prometheus 指标（容器持续处于 `ContainerCreating` 状态）予以佐证。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 24.2s
├─ 并发证据采集: 40.4s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 40.4s (Evidence 30.1s, RCA 10.2s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-imagepull-failed
