## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod挂载卷配置错误：YAML中定义的ConfigMap卷引用了不存在的键（unavailable-key），导致Kubelet在MountVolume阶段永久失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` (fact-eb79922825f4) | 核心证据：明确指出挂载失败的直接原因是 ConfigMap 键不存在 |
| 2 | K8s State | Kubernetes | `pod.phase: Pending` (fact-299882669b9c), `pod.status: Pending` (fact-b0e1786ef9e6), `container.waiting_reason: ContainerCreating` (fact-ae2ae26967c4) | 现象证据：Pod 卡在等待挂载卷阶段，容器未启动 |
| 3 | K8s Event | Kubernetes | `Unable to attach or mount volumes: unmounted volumes=[input]` (fact-91ee5f1d5a11) | 关联证据：佐证 input 卷挂载失败，导致卷未被挂载 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason: 1` (labels: reason=`ContainerCreating`, fact-cc150e30f632) | 现象印证：监控侧确认容器处于 ContainerCreating 等待状态 |

**证据关联说明：**
*   证据 1 揭示了失败的具体机制：YAML 定义引用的 ConfigMap 键 `unavailable-key` 在目标 ConfigMap 中不存在，触发 Kubelet 挂载失败。
*   证据 2 和 4 从 K8s 状态和监控指标两个维度，印证了因挂载失败导致的 `Pending` 和 `ContainerCreating` 持续状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 中 ConfigMap 卷引用了不存在的键 'unavailable-key' → Kubelet 验证挂载键失败导致 MountVolume.SetUp 失败 → 容器状态卡在 Waiting (reason: ContainerCreating) → Pod 表现为 Pending 且无法启动
```

### 根因结论

已确认根因为 **Pod 挂载卷配置错误**。
具体而言，Pod 的 YAML 配置中定义的 ConfigMap 卷 `input` 引用了不存在的配置键 `unavailable-key`（见证据 1）。这导致 Kubelet 在 `MountVolume` 阶段永久失败，进而使容器无法创建并卡在 `ContainerCreating` 状态（见证据 2、4）。

---

## 📊 性能统计

```text
├─ 总耗时: 57.6s
├─ 问题定位: 18.9s
├─ 并发证据采集: 30.3s
│  └─ g1 aiops-case-v05/workload: 30.3s (Evidence 24.5s, RCA 5.7s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed, pod-volume-mount-failed, pod-pending-unschedulable
