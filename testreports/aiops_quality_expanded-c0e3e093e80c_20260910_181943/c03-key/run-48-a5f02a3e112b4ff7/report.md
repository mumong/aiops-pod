## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload 卡在 ContainerCreating 状态 (Phase=Pending) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubelet` | `container.waiting_reason` = `ContainerCreating`；`pod.phase` = `Pending`；`pod.condition.Ready` = `False` | 确认 Pod 卡在启动初期，尚未进入运行或故障阶段。 |
| 2 | K8s Event | `kubelet` | `FailedMount` (x31 over 74m)：`timed out waiting for the condition` | 表明挂载操作在长时间（74分钟）内处于阻塞/重试状态，是容器无法启动的直接原因。 |
| 3 | K8s Event | `kubelet` | `FailedMount` (x45 over 77m)：`MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` | 明确指出了阻塞机制：Volume `input` 引用了一个不存在的 ConfigMap 键。 |
| 4 | K8s Config | `Kubernetes` | `volume` 配置项引用了 `configmap` 的 `key: unavailable-key` | 提供了导致 Event 中报错的具体配置源。 |
| 5 | Metric | `Prometheus` | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"}` = 1 | 独立监控数据印证了容器处于等待启动状态的事实。 |

**证据综合说明：**
证据 #2 和 #3 来自同一维度（K8s Event），但互为表里：#2 描述了“超时/阻塞”的宏观状态，#3 揭示了导致该状态的具体配置错误（引用了不存在的 Key）。#1 和 #5 分别从 Pod 状态和监控指标维度确认了该阻塞状态是持续性的，而非瞬时波动。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec中Volume 'input' 引用了不存在的ConfigMap键 'unavailable-key' → Kubelet执行MountVolume.SetUp失败，持续重试 → Volume挂载阻塞，容器进入Waiting状态 → Pod保持ContainerCreating (Pending) 异常
```

### 根因结论

已确认根因为：Pod 配置错误。
Pod Spec 中的 Volume `input` 引用了 ConfigMap 中不存在的键 `unavailable-key`，导致 Kubelet 无法挂载该卷，进而使容器一直处于 `ContainerCreating` 状态（证据 #3, #4）。

**证据编号：** [3], [4], [5]

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 22.1s
├─ 并发证据采集: 32.5s
│  └─ g1 aiops-case-v05/workload: 32.5s (Evidence 25.4s, RCA 7.0s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-volume-mount-failed, pod-imagepull-failed, pod-config-error, pod-sandbox-create-failed
