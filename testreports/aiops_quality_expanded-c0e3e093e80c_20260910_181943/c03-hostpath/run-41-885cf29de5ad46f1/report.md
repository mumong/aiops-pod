## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | HostPath 挂载路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 不存在或不是目录 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount  8m5s (x40 over 73m)   kubelet  MountVolume.SetUp failed for volume \"input\" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 核心因果证据：kubelet 明确指出宿主机路径检查失败，确认为目录不存在 |
| 2 | K8s Event | kubernetes | `FailedMount  2m53s (x31 over 71m)  kubelet  Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition` | 辅助现象：因挂载失败导致 Pod 挂载卷操作超时，阻碍了容器启动 |
| 3 | K8s State | kubernetes | `container.waiting_reason`: `ContainerCreating` | 状态确认：容器处于等待挂载卷的状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"} = 1` | 辅助确认：Prometheus 指标验证了容器处于 `ContainerCreating` 的等待原因 |

**证据互证说明：**
Kubernetes Event 提供了决定性的失败原因（hostPath type check failed），Metric 从指标侧印证了容器正卡在 `ContainerCreating` 状态。日志与追踪因容器未启动且无 IP 而不可用，不影响对挂载层面故障的判定。

## 🎯 根因分析 · g1

### 因果链
```text
宿主机关联的 HostPath 路径不存在或非目录 → MountVolume.SetUp 检查失败并超时 → Pod 处于 Pending/ContainerCreating 状态 → 用户可见容器无法启动
```

### 根因结论
根因确认为 **HostPath 挂载路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 不存在或不是目录**。

这一结论直接由事件证据 #1 支撑：kubelet 返回了明确的 `hostPath type check failed` 错误，并指出了具体缺失或无效的宿主机路径。该机制导致了挂载卷挂载失败（证据 #2），从而使 Pod 无法从 `ContainerCreating` 阶段过渡到 `Running` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 18.8s
├─ 并发证据采集: 33.9s
│  └─ g1 aiops-case-v06/workload: 33.9s (Evidence 27.1s, RCA 6.7s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-imagepull-failed
