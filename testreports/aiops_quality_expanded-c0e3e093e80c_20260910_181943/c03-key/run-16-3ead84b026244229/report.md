## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload 卡在 ContainerCreating (Pending) 阶段 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount: MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` (fact-08bdb5e55938) | 直接指出挂载失败的具体原因：ConfigMap 键缺失。 |
| 2 | K8s Event | kubernetes | `timed out waiting for the condition: unmounted volumes=[input]` (fact-4c29f4078589) | 证实挂载超时，阻塞了容器启动流程。 |
| 3 | K8s State | kubernetes | `pod.phase: Pending`, `container.waiting_reason: ContainerCreating` (fact-6061be0897f6, fact-3d3947569583) | 确认 Pod 当前处于因等待挂载而挂起的阶段。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` (fact-d9dcc15374d3) | 验证容器正停留在 ContainerCreating 状态，支持挂载阻塞推断。 |

上述证据链表明，Pod 的调度（PodScheduled=True）已成功，但因无法完成 `input` 卷的初始化，容器卡在 `ContainerCreating` 阶段。Metric 的当前快照与 K8s 事件中的挂载超时现象一致，共同指向底层存储挂载逻辑的失败。

## 🎯 根因分析 · g1

### 因果链

```text
Volume 配置错误 (引用 ConfigMap 'workload-input' 中不存在的 key 'unavailable-key') → kubelet MountVolume.SetUp 失败且超时 → 容器无法挂载配置卷并初始化 → Pod 状态持续为 Pending (ContainerCreating)
```

### 根因结论

已确认根因为 **卷挂载配置错误**。Pod `aiops-case-v05/workload` 的卷 `input` 引用了 ConfigMap 中不存在的键 `unavailable-key`，导致 kubelet 无法完成卷挂载（`FailedMount`），进而使容器一直停留在 `ContainerCreating` 状态且无法启动（fact-08bdb5e55938, fact-d9dcc15374d3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 21.7s
├─ 并发证据采集: 43.1s
│  └─ g1 aiops-case-v05/workload: 43.1s (Evidence 35.5s, RCA 7.4s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-volume-mount-failed
