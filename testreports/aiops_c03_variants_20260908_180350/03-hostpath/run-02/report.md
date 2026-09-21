## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | HostPath volume 'input' 配置指向的路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 在调度节点 node2 上不是预期目录（类型不匹配或不存在），导致挂载持续失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `Pod phase: Pending` ([fact-01a9a54b0820]) | 确认为 Pod 调度或启动阶段卡死 |
| 2 | K8s Event | Kubernetes | `FailedMount: MountVolume.SetUp failed for volume "input" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` ([fact-bfe0e6c797c1]) | **直接根因**：Kubelet 报告目标路径类型不匹配或不存在 |
| 3 | K8s State | Kubernetes | `Container "app" waiting reason: ContainerCreating` ([fact-37cf36508f43]) | 容器持续处于启动等待状态，未因 OOM 或崩溃退出 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` ([fact-fe854d3c259d]) | 独立验证容器未进入 Running 或 Failed 状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 0` ([fact-14e90602d1b5]) | 排除容器内应用进程崩溃或重启导致的问题 |

**证据关联说明**：
Kubernetes Event (`#2`) 明确指出 HostPath 挂载失败，与 K8s State 的 Pod 状态 (`#1`) 和容器等待原因 (`#3`) 完全一致。Metric 数据 (`#4`, `#5`) 证实了该故障是持续的等待状态，且排除了应用层面的崩溃重启。Logging 与 Tracing 维度因 Pod 未成功启动而未采集数据，但现有证据已足够闭环。

## 🎯 根因分析 · g1

### 因果链

```text
Node2 上的路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 类型不匹配或不存在 → Kubelet 执行 MountVolume.SetUp 失败 → Pod "app" 因挂载失败卡在 ContainerCreating → 现象：Pod 处于 Pending，ContainersReady=False
```

### 根因结论

已确认根因为 **HostPath 卷 'input' 配置指向的目标路径在调度节点 node2 上不是预期目录**，导致 Kubelet 挂载卷持续失败，Pod 无法完成启动。

依据事实：
- `fact-bfe0e6c797c1`: Kubelet 抛出 `hostPath type check failed` 事件，直接定位挂载失败原因。
- `fact-37cf36508f43`: 容器等待原因为 `ContainerCreating`，符合挂载卡死特征。
- `fact-fe854d3c259d`: Metrics 证实容器持续处于等待状态。

日志与追踪维度因容器未启动而未产生有效数据，但不影响根因判定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 19.4s
├─ 并发证据采集: 42.8s
│  └─ g1 aiops-case-v06/workload: 42.8s (Evidence 34.5s, RCA 8.2s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-imagepull-failed, pod-volume-mount-failed, pod-config-error
