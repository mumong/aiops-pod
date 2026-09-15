## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod workload 在 aiops-case-v05 中处于 ContainerCreating 状态，未能进入 Running |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `FailedMount: MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` (fact-19e347d2b645) | 直接指出 Volume 挂载因 ConfigMap 键不存在而失败 |
| 2 | K8s State | kubelet | Pod `status: Pending` (fact-bb379fb9ff40) | 证实 Pod 处于不可用状态 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason = 1` (reason: ContainerCreating, fact-a51f57a898c5) | 证实容器处于等待挂载阶段 |
| 4 | Config | K8s Spec | Container `app` memory request: `8Mi`, limit: `32Mi` (fact-668f3a9229a4, fact-0ce4993ab691) | 资源规格配置正常，排除资源争抢导致的 OOM 或调度失败 |

- **事实印证**：事件中的 `FailedMount` 错误与 Metric 显示的 `ContainerCreating` 等待状态完全吻合。
- **证据关联**：由于挂载失败，容器未能启动，因此无 Logging/Tracing 数据。根因由 K8s Event 明确提供。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-input' 中缺失 key 'unavailable-key' → kubelet 挂载卷 'input' 时校验失败 → MountVolume.SetUp 报错导致 Volume 挂载超时/失败 → Pod 停留在 Pending/ContainerCreating 状态
```

### 根因结论

- **已确认的根因**：Pod `aiops-case-v05/workload` 中的 Volume `input` 挂载失败，其根本原因是 ConfigMap 中引用的配置键 `unavailable-key` 不存在（证据 #1）。
- **现象解释**：由于核心存储卷无法挂载，Pod 无法进入 Running 状态，导致用户观测到的 Pod 持续处于 `ContainerCreating` 或 `Pending` 状态（证据 #2, #3）。
- **结论**：故障由配置错误引起，非资源不足或网络问题。

---

## 📊 性能统计

```text
├─ 总耗时: 9.3m
├─ 问题定位: 14.7s
├─ 并发证据采集: 538.3s
│  └─ g1 aiops-case-v05/workload: 538.3s (Evidence 531.4s, RCA 6.8s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed, pod-pending-unschedulable, pod-volume-mount-failed
