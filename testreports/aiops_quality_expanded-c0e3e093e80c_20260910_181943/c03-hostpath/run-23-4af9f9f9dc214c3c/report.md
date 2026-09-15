## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod aiops-case-v06/workload 配置了 HostPath 挂载卷 'input' 指向节点 node2 上的路径 /var/lib/aiops-fixture-unavailable-7f394bef/input，该路径在节点上不存在或类型不匹配，导致挂载持续失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `FailedMount`: `hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 证实挂载卷 'input' 因源路径类型不匹配导致挂载失败 |
| 2 | K8s Event | `kubelet` | `FailedMount`: `timed out waiting for the condition` | 证实挂载操作超时，验证挂载失败为持续性故障 |
| 3 | K8s State | `kubernetes` | `pod.phase: Pending`, `container.waiting_reason: ContainerCreating` | 定义异常实体状态：容器处于等待启动阶段，未进入运行 |
| 4 | K8s State | `kubernetes` | `pod.condition.ContainersReady: False`, `reason: ContainersNotReady` | 证实 Pod 未就绪，由容器挂载失败直接触发 |
| 5 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason: 1` (reason=ContainerCreating) | 独立观测确认容器状态确认为 ContainerCreating，与 K8s 事件一致 |

**证据分析**：
- 证据 1 和 2 直接指出了导致故障的机制：挂载卷 'input' 指向的 HostPath 路径存在类型冲突（非目录），导致 `FailedMount` 错误并持续超时。
- 证据 3、4 和 5 从 Pod 生命周期和等待原因维度，印证了该挂载失败直接阻塞了容器的启动和就绪。
- 日志与 Tracing 缺失，原因确认为容器未启动（`ContainerCreating`），无应用层数据可获取，不影响根因判定。

## 🎯 根因分析 · g1

### 因果链

```text
HostPath 路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 类型不匹配 → kubelet 挂载检查失败 (FailedMount) → 容器持续处于 ContainerCreating 状态 → Pod 状态 Pending 且未就绪
```

### 根因结论

已确认根因为 **Pod 的 HostPath 挂载配置错误**。
具体而言，Pod `aiops-case-v06/workload` 中名为 `input` 的卷挂载指向节点 `node2` 上的路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input`，但该路径在节点上不存在或类型不匹配（`hostPath type check failed`），导致 `kubelet` 挂载操作超时并拒绝启动容器。该结论由 K8s 事件日志（证据 1, 2）、Pod 状态（证据 3, 4）及 Prometheus 指标（证据 5）共同支撑。

---

## 📊 性能统计

```text
├─ 总耗时: 9.8m
├─ 问题定位: 20.5s
├─ 并发证据采集: 557.4s
│  └─ g1 aiops-case-v06/workload: 557.4s (Evidence 551.1s, RCA 6.2s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed
