## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Volume 'input' 引用了不存在的 ConfigMap Key 'unavailable-key'，导致 kubelet 挂载失败，Pod 无法进入 Running 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `fact-bcef8f70f245` | `Warning FailedMount MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` | 确认根因：ConfigMap 键缺失导致挂载失败 |
| 2 | K8s Event | `fact-88559538050f` | `Warning FailedMount... timed out waiting for the condition` | 现象佐证：挂载阻塞导致长时间等待 |
| 3 | K8s State | `fact-40d844243347` | Pod 状态 `Pending` | 确认当前异常状态 |
| 4 | Metric | `fact-24187bbecfef` | `kube_pod_container_status_waiting_reason` = 1 (reason: ContainerCreating) | 确认容器处于等待挂载阶段 |

**证据链关联：**
Event `fact-bcef8f70f245` 提供了明确的挂载错误原因（`configmap references non-existent config key: unavailable-key`）。Metrics `fact-24187bbecfef` 显示容器处于 `ContainerCreating` 状态，与 Event 中描述的挂载阻塞现象一致。Pod 状态 `Pending` 进一步确认了由于挂载失败，Pod 无法进入 Running 阶段。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 缺失 key 'unavailable-key' → kubelet 执行 MountVolume.SetUp 失败 → Pod 状态卡住 (ContainerCreating/Pending) → 容器 app 无法启动
```

### 根因结论

**已确认的根因：** Pod 中引用的 Volume 'input' 配置的 ConfigMap 缺少指定的 Key `unavailable-key`，导致 Kubernetes 挂载卷失败。

**证据支持：**
1. Kubernetes 事件直接指出 `configmap references non-existent config key: unavailable-key`（证据 #1）。
2. Pod 状态和容器等待原因为挂载失败提供了状态佐证（证据 #3, #4）。
3. 该问题由配置错误（ConfigMap 与 Volume 定义不一致）引起，非集群资源或调度问题。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 24.1s
├─ 并发证据采集: 30.2s
│  └─ g1 aiops-case-v05/workload: 30.2s (Evidence 25.1s, RCA 4.9s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed
