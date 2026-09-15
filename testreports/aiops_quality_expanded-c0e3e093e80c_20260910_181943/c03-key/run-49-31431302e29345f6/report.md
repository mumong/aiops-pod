## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod aiops-case-v05/workload 处于 Pending/ContainerCreating 状态，未能启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `FailedMount 7m46s (x31 over 75m) ... timed out waiting for the condition` | 证实挂载卷长期阻塞 |
| 2 | K8s Event | `kubelet` | `FailedMount 2m41s (x45 over 78m) ... MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` | 指出卷引用 ConfigMap 键不存在 |
| 3 | K8s State | `Pod` | `phase: Pending`, `ContainersReady: False`, `Ready: False`, `ContainerCreating` | 容器处于启动受阻状态 |
| 4 | K8s State | `Container` | `waiting_reason: ContainerCreating`, `restart_count: 0` | 确认容器尚未进入运行态且未重启 |
| 5 | Metric | `Prometheus` | `kube_pod_container_status_waiting_reason` (reason: ContainerCreating) = 1 | 从指标侧印证容器持续等待中 |

**证据分析：**
证据 1 和 2 在 kubelet 层面形成了直接证据链，明确指出了 `FailedMount` 的时间跨度（长达 75 分钟）及根本错误原因（`references non-existent config key`）。证据 3 和 4 展示了 Pod 因挂载失败而停留在 `Pending` 及 `ContainerCreating` 阶段的实际运行态，与证据 1 的时间跨度相吻合。证据 5 从时序数据库侧再次确认了容器正处于等待原因 `ContainerCreating` 中。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 定义 ConfigMap Volume 'input' 引用 key 'unavailable-key' → ConfigMap 'workload-input' 中不存在该 key → kubelet 拒绝挂载卷 (FailedMount) → 容器 app 卡在 ContainerCreating 状态
```

### 根因结论

已确认根因为 **Pod 配置引用了不存在的 ConfigMap 键**。具体地，Pod 挂载卷 `input` 时指定了不存在的 key `unavailable-key`，导致 kubelet 执行挂载准备（SetUp）失败并超时，容器因此无法启动。

**支持证据：**
- `fact-622164870de7`: 显示 `FailedMount` 错误伴随 `timed out waiting for the condition`。
- `fact-87c966d93435`: 明确指出 `configmap references non-existent config key: unavailable-key`。

---

## 📊 性能统计

```text
├─ 总耗时: 54.1s
├─ 问题定位: 16.7s
├─ 并发证据采集: 28.6s
│  └─ g1 aiops-case-v05/workload: 28.6s (Evidence 22.5s, RCA 5.9s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-volume-mount-failed
