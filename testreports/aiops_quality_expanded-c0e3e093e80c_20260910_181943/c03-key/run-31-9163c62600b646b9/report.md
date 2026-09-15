## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod workload (aiops-case-v05) stuck in Pending / ContainerCreating state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount: MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` | 核心错误：直接指出挂载失败是因为 ConfigMap `workload-input` 中缺少键 `unavailable-key`。 |
| 2 | K8s Event | kubernetes | `FailedMount: Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition` | 持续性症状：表明该挂载失败是高频复现（x16/x23），导致挂载卷长期处于超时等待状态。 |
| 3 | K8s State | kubernetes | Pod `status=Pending`, Phase=`Pending`, Container `waiting_reason=ContainerCreating`, RestartCount=`0` | 状态确认：Pod 未能调度完成进入 Running 状态，且无重启记录，符合挂载阻塞导致的启动挂起特征。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 指标印证：监控侧确认容器处于等待创建状态的实例数为 1。 |
| 5 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"} = 1` | 指标印证：监控侧确认 Pod 处于 Pending 阶段。 |

**证据分析：**
Kubernetes 事件（#1, #2）提供了决定性的错误信息，明确将挂载失败归因于配置键缺失；Pod 状态（#3）和监控指标（#4, #5）从不同维度一致确认了 Pod 处于非运行的挂起状态，且无重启日志或追踪数据，完全符合配置错误导致的启动阻塞模式。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-input' 缺失键 'unavailable-key' → 卷 'input' 挂载失败（引用了不存在的配置键） → Pod 持续抛出 FailedMount 事件并停留在 Pending 状态 → 容器无法启动
```

### 根因结论

**已确认的根因：**
卷挂载配置错误导致容器启动阻塞。
具体而言，Pod 中的卷 `input` 引用了 ConfigMap `workload-input` 中的键 `unavailable-key`，但该键在 ConfigMap 中实际并不存在。这直接导致了 `FailedMount` 事件（见证据 #1），并引发后续的挂载超时等待（见证据 #2），使得 Pod 始终处于 `Pending` / `ContainerCreating` 状态（见证据 #3, #5）。

**缺失事实：**
当前证据无法解释为什么 `workload-input` ConfigMap 中缺失该键（如：是否为部署步骤遗漏、ConfigMap 配置错误或键名拼写错误），但这属于变更管理范畴，不影响对当前 Pod 挂起原因的判定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 44.3s
├─ 并发证据采集: 38.3s
│  └─ g1 aiops-case-v05/workload: 38.3s (Evidence 29.0s, RCA 9.2s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-volume-mount-failed
