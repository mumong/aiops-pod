## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload stuck in ContainerCreating (Pending) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` (Fact: `fact-93e183d92787`) | 直接揭示根因：ConfigMap 中缺少键 `unavailable-key` 导致挂载失败。 |
| 2 | K8s Event | Kubernetes | `Warning FailedMount ... Unable to attach or mount volumes: unmounted volumes=[input]... timed out waiting for the condition` (Fact: `fact-7e5000b7e01b`) | 描述挂载失败导致的等待超时现象，解释了 Pod 无法进度的原因。 |
| 3 | K8s State | Kubernetes | `ContainerCreating` (Fact: `fact-5a36d897cf2f`) | 说明 Pod 卡在容器创建阶段，符合挂载阻塞导致无法启动容器的状态。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值为 1 (Fact: `fact-ebb53daa0fcc`) | 确认容器处于等待状态，且未发生重启 (重启计数为 0)。 |

Kubernetes Events 明确指出了挂载失败的具体原因是 ConfigMap 引用了不存在的键（Fact #1），这与 Pod 卡在 `ContainerCreating` 的状态（Fact #3）和 Prometheus 指标中的等待状态（Fact #4）互为印证。

## 🎯 根因分析 · g1

```text
ConfigMap 'workload-input' 缺少键 'unavailable-key' → 卷挂载失败 (FailedMount) → Pod 卡在 ContainerCreating/Pending 状态
```

**已确认的根因：**
集群异常的根本原因是 Pod `aiops-case-v05/workload` 的 Volume 配置引用了 ConfigMap `workload-input` 中不存在的键 `unavailable-key`。这一配置错误直接导致了 Kubernetes 挂载卷失败（Evidence #1），进而使 Pod 无法挂载卷，一直卡在 `ContainerCreating` 阶段（Evidence #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.9s
├─ 并发证据采集: 43.2s
│  └─ g1 aiops-case-v05/workload: 43.2s (Evidence 35.3s, RCA 7.8s)
└─ 汇总总结: 7.2s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed, pod-volume-mount-failed, pod-pending-unschedulable, pod-config-error
