## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod `workload` 中 volume `input` 引用了 ConfigMap `workload-input` 中不存在的 key `unavailable-key`（或 ConfigMap 数据为空但 Pod spec 期望存在子路径/keys），导致 kubelet 挂载卷失败，容器卡在 `ContainerCreating` 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-d01dfc14df00) | `MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` | **直接归因**：精准定位失败机制为 ConfigMap 键缺失导致的挂载失败。 |
| 2 | K8s Event | kubernetes (fact-a8a7d3fca81b) | `Warning FailedMount... Unable to attach or mount volumes: unmounted volumes=[input]...` | **现象印证**：显示故障的持续性与广泛性（x35 over 55m），表明系统反复重试挂载均告失败。 |
| 3 | K8s State | kubernetes (fact-c6a317ee5683) | `container.waiting_reason`: `ContainerCreating` | **现象确认**：证实容器因挂载阻塞而停滞，未进入运行状态。 |
| 4 | K8s State | kubernetes (fact-726096e381a4) | `pod.phase`: `Pending` | **状态佐证**：Pod 整体处于挂起状态，未满足调度后的启动条件。 |
| 5 | K8s State | kubernetes (fact-85ca9f6164a5) | `ContainersReady`: `False` (reason: `ContainersNotReady`) | **就绪性证据**：Kubernetes 核心探针明确指示容器不可用。 |
| 6 | Metric | prometheus (fact-3ccebe583a39) | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"}` = `1` | **监控印证**：独立监控源确认容器处于等待挂载的资源状态。 |

**证据关联说明：**
1. 指标 `ContainerCreating` (E6) 与 K8s 事件 `FailedMount` (E1, E2) 以及容器状态 `waiting` (E3) 形成闭环，一致指向挂载阶段受阻。
2. 具体的挂载错误信息 (E1) 给出了唯一的根因路径（`configmap references non-existent config key`），排除了资源不足或调度失败的干扰。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap `workload-input` 缺少 Pod 引用的 `unavailable-key` → Kubelet 挂载卷失败 (FailedMount) → 容器无限期重试挂载 → Pod 卡在 ContainerCreating 状态
```

### 根因结论

已确认根因为 **ConfigMap 配置错误**。
`workload` Pod 的 volume `input` 引用了 ConfigMap `workload-input` 中不存在的 key `unavailable-key`，导致 kubelet 无法完成卷挂载。由于 Pod 依赖该卷启动，容器无法进入 Running 状态，最终表现为无限期停滞在 `ContainerCreating` (证据 #1, #2, #3)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 29.1s
├─ 并发证据采集: 36.5s
│  └─ g1 aiops-case-v05/workload: 36.5s (Evidence 31.2s, RCA 5.2s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-volume-mount-failed
