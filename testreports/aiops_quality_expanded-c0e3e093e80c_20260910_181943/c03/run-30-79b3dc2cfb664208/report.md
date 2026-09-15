## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-xn974 处于 ContainerCreating/Pending 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount`: MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found (fact-f8bac518bef1) | 直接指出挂载失败的根因为缺少 ConfigMap |
| 2 | K8s Event | kubernetes | `FailedMount`: Unable to attach or mount volumes: unmounted volumes=[input] (fact-ae1d1c5155a3) | 证实 kubelet 持续无法挂载名为 `input` 的卷 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值为 1, reason=ContainerCreating (fact-8608f8001de5) | 观测到容器处于等待启动的具体状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total` 值为 0 (fact-62e24ac596bd) | 确认 Pod 从未成功运行过，排除运行时崩溃可能 |

证据说明：
1. 事件日志（事实 1, 2）提供了故障的直接文字原因，明确指出 ConfigMap 缺失导致挂载失败。
2. 监控指标（事实 3, 4）与事件日志完全印证，展示了容器因挂载阻塞而处于 `ContainerCreating` 状态，且重启次数为 0。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 不存在 → Volume 'input' 挂载失败 (MountVolume.SetUp failed) → 容器状态阻塞在 Waiting (ContainerCreating) → Pod 处于 Pending 状态
```

### 根因结论

已确认的根因是 Pod 定义的 Volume `input` 引用了不存在的 ConfigMap `unavailable-config`，导致挂载卷失败。根据 K8s 事件事实（fact-f8bac518bef1, fact-ae1d1c5155a3），由于该 Volume 配置为 Optional=false（隐含在挂载失败且未被忽略的逻辑中），Kubelet 无法启动容器，直接导致 Pod 阻塞在 Pending/ContainerCreating 状态（由 metric fact-8608f8001de5 和 fact-434b5f9edb69 佐证）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 82.2s
├─ 并发证据采集: 38.2s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 38.2s (Evidence 29.2s, RCA 9.0s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-volume-mount-failed, pod-imagepull-failed
