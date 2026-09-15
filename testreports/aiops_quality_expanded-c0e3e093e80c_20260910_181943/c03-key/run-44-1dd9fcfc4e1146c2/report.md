## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod YAML 中 ConfigMap 卷 'input' 引用了不存在的 key 'unavailable-key'，导致 MountVolume.SetUp 失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `fact-c1955bf84674`: MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key | 定位失败机制为 ConfigMap 引用缺失 Key |
| 2 | K8s Event | Kubernetes | `fact-0ee873c5548d`: Timed out waiting for the condition (unmounted volumes=[input]) | 确认挂载超时及卷挂载状态异常 |
| 3 | K8s State | Kubernetes | `fact-3f4076bbbe5f`: Waiting reason is ContainerCreating; `fact-82d015af0889`: Phase is Pending | 确认可见现象为 Pod 持续处于挂载等待/挂起状态 |
| 4 | Metric | Prometheus | `fact-6b05e83b2f9e`: `kube_pod_container_status_waiting_reason` = 1, label `reason=ContainerCreating` | 独立确认容器因挂载未就绪而处于 Waiting 状态 |
| 5 | Metric | Prometheus | `fact-5051b20141f6`: `kube_pod_status_phase` = 1, label `phase=Pending` | 独立确认 Pod 处于 Pending 阶段，与 K8s 状态一致 |

**证据印证说明：**
Kubernetes 事件明确指出了 `MountVolume.SetUp` 失败的根本原因是 `configmap references non-existent config key: unavailable-key`。Kubernetes 状态（Pending/ContainerCreating）与 Prometheus 采集到的指标（`waiting_reason=ContainerCreating` 和 `phase=Pending`）相互印证了该现象的持续性。日志与追踪维度的 `not_applicable` 状态符合容器尚未启动无法产生流量的物理事实。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 配置引用了不存在的 ConfigMap Key ('unavailable-key') → MountVolume.SetUp 失败 → 卷挂载超时 (Timed out) → Pod 处于 ContainerCreating/Pending 状态且不可用
```

### 根因结论
已确认根因为：**Pod YAML 中 ConfigMap 卷 'input' 引用了不存在的 key 'unavailable-key'**。
该错误直接导致 Kubernetes 挂载卷机制失败（`MountVolume.SetUp failed`），引发 Pod 进入 `ContainerCreating` 的等待状态且无法转为 Ready（证据编号：1, 2, 3）。此结论由事件日志直接证实，并被 Prometheus 指标（证据编号：4, 5）观测到的状态一致支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 30.1s
├─ 并发证据采集: 34.7s
│  └─ g1 aiops-case-v05/workload: 34.7s (Evidence 28.0s, RCA 6.6s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed, pod-volume-mount-failed, pod-sandbox-create-failed
