## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod workload (aiops-case-v05) stuck in ContainerCreating/Pending due to FailedMount |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `phase: Pending`, `condition: ContainersReady=False (reason: ContainersNotReady)` | 确认 Pod 未启动，容器处于等待状态 |
| 2 | K8s Event | kubernetes | `FailedMount`: `MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` | 直接指出挂载失败原因是 ConfigMap 中缺少 `unavailable-key` 键 |
| 3 | K8s Event | kubernetes | `FailedMount`: `Unable to attach or mount volumes: unmounted volumes=[input]... timed out waiting for the condition` | 证实 kubelet 在多次重试后仍无法挂载 `input` 卷 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = `1` (reason: `ContainerCreating`), `restart_count` = `0` | 指标状态与 K8s Event 现象一致，容器持续处于创建等待期且未发生过重启 |

**证据印证说明：**
K8s Event (fact-5beefbd07cf0, fact-f7eaa1b47e21) 明确记录了挂载失败的具体原因（ConfigMap 键值不匹配），这与 Pod 处于 `ContainerCreating/Pending` 状态（fact-87ad278a8961）及 Prometheus 监控的等待原因（fact-86f97f6ea776）完全吻合。缺失的日志和追踪数据符合“容器未启动”的客观限制。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-input' 缺少 Pod 挂载所需的键 'unavailable-key' → kubelet 在 VolumeSetUp 阶段执行挂载失败 → Pod 卷挂载永久处于超时/失败状态 → 容器无法创建，Pod 卡在 Pending/ContainerCreating 状态
```

### 根因结论

已确认根因为 Pod 声明的 volume `input` 试图挂载 ConfigMap `workload-input` 中不存在的具体键 `unavailable-key`。

Kubelet 在多次尝试挂载该卷后均报 `FailedMount` 错误（见证据 #2, #3），导致容器始终无法进入运行状态，因此 Pod 保持在 `Pending` 阶段且无重启记录。该配置错误是阻断容器启动的直接且唯一证据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.4s
├─ 并发证据采集: 38.9s
│  └─ g1 aiops-case-v05/workload: 38.9s (Evidence 31.1s, RCA 7.7s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed, pod-volume-mount-failed
