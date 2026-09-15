## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod aiops-case-v06/workload 的 Volume 'input' 配置为 HostPath 类型，指向节点 node2 上的路径 '/var/lib/aiops-fixture-unavailable-7f394bef/input'。该路径在宿主机上不存在（非目录），导致 Kubelet 在 MountVolume.SetUp 阶段检查失败，无法挂载存储卷，进而导致容器无法启动（ContainerCreating）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedMount`: "hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory" (`fact-a939967e2d5c`) | 直接指出挂载失败的具体机制：宿主机路径校验失败 |
| 2 | K8s State | Kubernetes | Pod 状态 `phase: Pending`, `status: ContainerCreating` (`fact-01b630c04bc6`, `fact-582ca9e2574e`) | 确认可见现象：Pod 停留在启动前阶段，未进入运行状态 |
| 3 | K8s Event | Kubernetes | 重复事件：`FailedMount` (13s x20, 4m50s x28) (`fact-2a859fff5605`) | 证实该挂载失败是持续性故障，且持续至少 45 分钟 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` (`fact-bfebaf941252`) | 从监控侧印证容器一直等待挂载，与 K8s 状态一致 |

**证据综合分析**：
Kubernetes 事件的 `FailedMount` 消息提供了最关键的定论性证据，明确指出故障原因是宿主机上的 HostPath 路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 不是一个目录。Metric 数据的 `ContainerCreating` 状态与 K8s 的 `Pending` 状态形成了完美的闭环印证，排除了资源不足等并发问题。日志与追踪数据因容器无法启动而不适用，不影响存储挂载层面的诊断结论。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置 HostPath Volume 'input' 指向 node2 的 '/var/lib/aiops-fixture-unavailable-7f394bef/input' 
→ 宿主机 node2 上该路径不存在或不是目录 
→ Kubelet MountVolume.SetUp 阶段校验失败 (hostPath type check failed) 
→ Pod 无法挂载存储卷，状态持续 Pending/ContainerCreating
```

### 根因结论

**已确认的根因**：
Pod `aiops-case-v06/workload` 的 Volume 配置使用了 `HostPath` 类型，指向节点 `node2` 上的特定路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input`，但该路径在宿主机上不存在或不符合目录要求（证据 #1）。

这一配置错误直接导致了 `MountVolume.SetUp` 失败，使得容器无法挂载必要的存储卷，进而导致 Pod 陷入 `ContainerCreating` 状态且无法进一步启动（证据 #2, #3, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 21.2s
├─ 并发证据采集: 36.2s
│  └─ g1 aiops-case-v06/workload: 36.2s (Evidence 28.5s, RCA 7.6s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed
