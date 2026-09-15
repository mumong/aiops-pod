## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod aiops-case-v06/workload stuck in Pending/ContainerCreating |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Status | `status: Pending` | 确认 Pod 未进入运行状态 |
| 2 | K8s Event | `FailedMount` | `hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 明确阻断点：HostPath 路径不存在 |
| 3 | K8s Event | `FailedMount` | `timed out waiting for the condition` | 证明挂载等待超时，导致 Pod 持续阻塞 |
| 4 | Metric | Waiting Reason | `kube_pod_container_status_waiting_reason` 值为 `1`，标签 `reason=ContainerCreating` | 指标侧面印证容器处于挂载卷阶段 |
| 5 | K8s Config | Resource Limits | CPU `50m`, Memory `32Mi` | 排除资源限制导致调度失败的可能 |

**证据逻辑说明：**
Pod 处于 `Pending` 阶段且等待原因为 `ContainerCreating`，Kubernetes 事件日志中的 `FailedMount` 提供了直接原因（HostPath 目录缺失）。“timed out waiting for the condition” 说明 kubelet 持续重试并耗尽超时，最终导致 Pod 无法调度至运行状态。Metrics 中的等待指标与日志中的挂载失败在机制上相互印证。

## 🎯 根因分析 · g1

### 因果链
```text
HostPath 目录 '/var/lib/aiops-fixture-unavailable-7f394bef/input' 缺失 → Kubelet 挂载失败 (FailedMount) → Pod 卡在 ContainerCreating/Pending → 容器无法启动
```

### 根因结论
Pod 被阻塞在 `Pending` 状态的根本原因是其声明的 `HostPath` 卷 `input` 所引用的宿主机目录 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 在目标节点（node2）上不存在或类型不符，导致 `FailedMount`。Kubelet 因无法完成挂载而持续重试直至超时（见证据 #3），直接阻断了 Pod 的生命周期推进。
*注：关于该目录是否应由 Init Container 或外部进程预先创建的逻辑归属，当前事实未能覆盖。*

---

## 📊 性能统计

```text
├─ 总耗时: 9.5m
├─ 问题定位: 31.8s
├─ 并发证据采集: 528.1s
│  └─ g1 aiops-case-v06/workload: 528.1s (Evidence 520.4s, RCA 7.6s)
└─ 汇总总结: 7.7s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-imagepull-failed, pod-volume-mount-failed, pod-sandbox-create-failed
