## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod volume 'input' 引用了 ConfigMap 'workload-input' 中不存在的 key 'unavailable-key'，导致 kubelet 挂载失败，Pod 持续处于 Pending/ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning FailedMount MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` (fact_id: `fact-84d298e45b45`) | 直接定位挂载失败原因：引用的 ConfigMap 缺失 Key |
| 2 | K8s Event | kubelet | `Warning FailedMount 24s kubelet Unable to attach or mount volumes: unmounted volumes=[input]` (fact_id: `fact-3562fdf714c3`) | 证实 kubelet 挂载卷操作持续超时 |
| 3 | K8s State | container | `reason: ContainerCreating` (fact_id: `fact-cc57d1592a69`) | 描述 Pod 卡在初始化阶段的等待状态 |
| 4 | K8s Config | Pod Spec | Volume 'input' 引用 ConfigMap 'workload-input' 的 key 'unavailable-key' (源自 diagnosis 描述) | 提供触发异常的配置依据，确认可疑的挂载路径 |
| 5 | K8s State | Pod Phase | `status: Pending`, `containers with unready status: [app]` (fact_id: `fact-af56bdd18a33`, `fact-4bb13299b720`) | 验证 Pod 因挂载失败而处于不可用状态 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"} = 1` (fact_id: `fact-e9711e41fbee`) | 从监控侧独立印证容器处于等待挂载/启动阶段 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total{container="app"} = 0` (fact_id: `fact-e3e938de2873`) | 排除应用代码崩溃导致的 CrashLoopBackOff，锁定基础设施层 |

上述证据链显示，Kubernetes 事件日志明确指出了挂载失败的具体原因是配置引用了不存在的 key，Pod 状态与 K8s Events 相互印证了 `MountVolume.SetUp` 失败这一直接故障点。Metric 数据从监控维度提供了容器处于 `ContainerCreating` 且未重启的独立侧面验证。Logging/Tracing 因容器未启动而不适用，符合预期。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-input' 中缺少 key 'unavailable-key' → Pod volume 'input' 配置引用该无效 key → kubelet 执行 MountVolume.SetUp 失败 → 容器无法挂载 volume，状态卡在 ContainerCreating
```

### 根因结论

**已确认根因**：Pod `aiops-case-v05/workload` 中 volume `input` 引用了 ConfigMap `workload-input` 中不存在（或不匹配）的 key `unavailable-key`。

证据表明，由于该配置引用错误，kubelet 在尝试挂载 volume 时直接失败并报错 `configmap references non-existent config key`。这导致 Pod 的 `ContainerCreating` 阶段无限期挂起，表现为容器无法启动且 `phase` 为 `Pending`。该故障属于典型的配置错误，与资源不足或节点故障无关。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 27.8s
├─ 并发证据采集: 39.2s
│  └─ g1 aiops-case-v05/workload: 39.2s (Evidence 32.9s, RCA 6.2s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-volume-mount-failed
