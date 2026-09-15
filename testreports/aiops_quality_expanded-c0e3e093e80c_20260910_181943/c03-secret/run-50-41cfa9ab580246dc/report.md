## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod workload in aiops-case-v04 is stuck in ContainerCreating/Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found` | 提供挂载失败的直接原因，确认为 Secret 缺失导致 |
| 2 | K8s State | kubernetes | `reason: ContainerCreating` (container: app) | 确认容器未能进入运行或重启状态，处于初始化等待 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 为 1 (`ContainerCreating`) | 从监控面确认容器处于 Waiting 状态的事实 |
| 4 | Metric | prometheus | `kube_pod_status_phase` 为 1 (`Pending`) | 从监控面确认 Pod 处于 Pending 状态，佐证集群状态异常 |

证据 1 明确指出了故障的具体机制是挂载名为 `input` 的卷时找不到 `unavailable-input` Secret。证据 2、3 和 4 相互印证，表明 Pod 一直卡在初始化阶段（Waiting/Pending）且没有触发重启（Restart Count 为 0），这符合由于配置缺失导致的启动阻塞特征。

## 🎯 根因分析 · g1

### 因果链

```text
缺失 Secret 'unavailable-input' → Kubelet 挂载卷 'input' 失败 → 触发 MountVolume.SetUp 错误 → Pod 持续处于 ContainerCreating/Pending 状态
```

### 根因结论

已确认的根因：Pod `aiops-case-v04/workload` 的 Volume 配置引用了不存在于当前命名空间的 Secret `unavailable-input`。Kubelet 在启动容器前尝试挂载该卷，因无法找到对应的 Secret 而直接报错（见证据 1），导致容器初始化阻塞在 `ContainerCreating` 状态（见证据 2-4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.5s
├─ 并发证据采集: 37.3s
│  └─ g1 aiops-case-v04/workload: 37.3s (Evidence 29.0s, RCA 8.1s)
└─ 汇总总结: 6.4s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-volume-mount-failed
