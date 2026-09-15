## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload 持续处于 ContainerCreating 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount`: configmap references non-existent config key: unavailable-key (fact-10c25a5bfdba) | 确认挂载失败的具体原因为配置项引用错误 |
| 2 | K8s State | kubernetes | `pod.status`: Pending; `container.waiting_reason`: ContainerCreating (fact-a124c109d584, fact-42bc047e41e4) | 确认 Pod 因卷挂载阻塞无法进入运行状态 |
| 3 | K8s State | kubernetes | `container.resource_limit.memory`: 32Mi; `container.resource_request.cpu`: 5m (fact-39f38a5dcc87, fact-c8084875f407) | 排除因资源配额不足导致的调度或启动失败 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (reason=ContainerCreating): 1 (fact-5c2fe55a4216) | 独立确认容器处于等待状态 |

证据 1 提供了挂载失败的根本原因（Key 不存在），证据 2 和 4 从状态机和指标层面共同印证了容器因该挂载问题而处于等待状态，排除了资源竞争等其他启动阻碍。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-input' 缺少 key 'unavailable-key' → VolumeMount 挂载失败 → 容器无法启动 → Pod 停滞在 ContainerCreating
```

### 根因结论

已确认根因：Pod 定义的 ConfigMap Volume 'input' 强制引用了 ConfigMap 中不存在的 key `unavailable-key`。

这一配置错误导致 `kubelet` 在挂载卷阶段持续失败（证据 1），进而阻塞容器初始化。Kubernetes 状态（证据 2）与 Prometheus 指标（证据 4）均一致记录了因挂载阻塞导致的 `ContainerCreating` 等待状态。

---

## 📊 性能统计

```text
├─ 总耗时: 59.6s
├─ 问题定位: 13.8s
├─ 并发证据采集: 38.7s
│  └─ g1 aiops-case-v05/workload: 38.7s (Evidence 32.2s, RCA 6.4s)
└─ 汇总总结: 7.1s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed, pod-sandbox-create-failed, pod-volume-mount-failed
