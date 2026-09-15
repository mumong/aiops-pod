## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod aiops-case-v04/workload 处于 Pending/ContainerCreating 状态，容器未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod `aiops-case-v04/workload` | `phase`: Pending, `status`: ContainersNotReady, `container.waiting_reason`: ContainerCreating [fact-1497bc96a553], [fact-b1524420775d], [fact-06b9085d7c4c] | 确认 Pod 未进入运行状态，且容器处于等待挂载资源的阻塞阶段 |
| 2 | K8s State | Pod `aiops-case-v04/workload` | `restart_count`: 0, `volume.phase`: [未显式报错，但存在挂载事件] [fact-76631c95c108] | 排除应用逻辑错误导致的 CrashLoopBackOff，确认为启动前置阶段的系统级阻塞 |
| 3 | K8s Event | Kubelet `FailedMount` | `message`: "MountVolume.SetUp failed for volume \"input\" : secret \"unavailable-input\" not found" [fact-c26785b6284f] | **直接归因**：明确指出 Volume 'input' 引用的 Secret 'unavailable-input' 不存在，是导致 Pod 停滞的直接原因 |
| 4 | K8s Event | Kubelet `FailedMount` (延续) | `message`: "Unable to attach or mount volumes: unmounted volumes=[input]... timed out waiting for the condition" [fact-9ff12d8ce3ff] | 佐证了因 Secret 缺失，Mount 操作持续超时，状态卡在 ContainerCreating |
| 5 | Metric | Prometheus `kube_pod_container_status_waiting_reason` | `labels`: `{container: "app", reason: "ContainerCreating"}`, `value`: 1, `trend_evaluable`: false [fact-c5d541c2bf9b] | 外部指标观测结果与 K8s API 状态一致，确认集群控制器层面认为该容器仍在等待挂载 |
| 6 | Metric | Prometheus `kube_pod_container_status_restarts_total` | `value`: 0, `trend_evaluable`: false [fact-97a2455f4853] | 确认容器从未成功启动过，排除了因健康检查失败或 OOM 等运行时故障导致的重启 |
| 7 | K8s Config | Container Resources | `cpu.request`: 5m / `cpu.limit`: 50m, `memory.request`: 8Mi / `memory.limit`: 32Mi [fact-06b9085d7c4c], [fact-389aeca73202], [fact-628e44f33b78], [fact-9ed131c62e28] | 资源配额极小，排除了因资源不足（CPU/Memory Request）导致节点无法调度的可能性 |

**证据关联说明**：
Metric [fact-c5d541c2bf9b] 的 `reason: ContainerCreating` 与 K8s 状态 [fact-06b9085d7c4c] 互相印证，排除了网络或 API 延迟导致的假死。关键事件 [fact-c26785b6284f] 直接指出了缺失资源名称，解释了为什么资源 [fact-06b9085d7c4c] 足够却仍然调度失败（问题在 Volume 引用，而非计算资源）。

## 🎯 根因分析 · g1

### 因果链

```text
定义中 Volume 'input' 绑定不存在的 Secret 'unavailable-input' → kubelet 尝试挂载卷失败 (MountVolume.SetUp failed) → Pod 持续处于 Pending/ContainerCreating 状态，等待条件超时 → 应用无法启动，集群控制器报告 FailedMount 事件
```

### 根因结论

已确认的根因为：**Pod `aiops-case-v04/workload` 的 YAML 定义中，Volume `input` 引用了 Secret `unavailable-input`，但该 Secret 在 namespace `aiops-case-v04` 中不存在。**

依据证据 [fact-c26785b6284f] 与 [fact-9ff12d8ce3ff]，Kubelet 在启动容器前必须挂载所有 Volume，由于 Secret 缺失，挂载操作立即失败并进入重试/超时状态（`timed out waiting for the condition`），导致 Pod 无法推进至 `Running` 状态。Metric [fact-c5d541c2bf9b] 确认该状态已在集群层面持续存在，且未发生任何重启（restart_count=0），符合启动前阻塞特征。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 16.1s
├─ 并发证据采集: 40.8s
│  └─ g1 aiops-case-v04/workload: 40.8s (Evidence 32.5s, RCA 8.0s)
└─ 汇总总结: 15.2s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-volume-mount-failed
