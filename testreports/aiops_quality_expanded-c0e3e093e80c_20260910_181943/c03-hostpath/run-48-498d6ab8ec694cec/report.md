## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | HostPath卷挂载失败。Pod `workload` 尝试挂载名为 `input` 的 HostPath 卷，目标路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 在调度节点 `node2` 上不存在或不是目录，导致 kubelet 持续挂载失败，Pod 永久处于 ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Status | `phase`: `Pending`, `status`: `ContainerCreating` | 确认 Pod 因挂载问题卡在启动阶段，尚未进入运行态 |
| 2 | K8s Event | FailedMount | `hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 直接定位挂载失败的物理原因：目标路径在节点上不存在或非目录 |
| 3 | K8s Event | FailedMount | `timed out waiting for the condition` | 证实挂载尝试在长时间窗口内持续失败，排除短暂网络抖动 |
| 4 | Metric | Waiting Reason | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"} = 1` | 提供时序证据，与 Kubernetes 状态一致，确认容器处于等待资源挂载的停滞状态 |

**证据印证分析：**
1.  K8s 状态与事件直接解释了 Pod 为何处于 `Pending` 和 `ContainerCreating` 且无重启（Restart Count=0），因为容器甚至未能启动。
2.  Metric 数据中的 `ContainerCreating` 等待原因与 K8s Event 的 `FailedMount` 互为印证，表明 Pod 卡在卷挂载前置条件检查阶段。
3.  日志和链路追踪（Logging/Tracing）因容器未启动而物理缺失，符合预期，进一步佐证故障发生在容器启动之前的挂载阶段。

## 🎯 根因分析 · g1

### 因果链

```text
HostPath 挂载目标路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 在节点 node2 上不存在或不是目录 → 挂载前置类型检查失败 (hostPath type check failed) → 挂载动作超时且持续失败 (FailedMount) → Pod 永久处于 ContainerCreating 状态
```

### 根因结论

已确认根因为 **HostPath 卷挂载失败**。
Pod `workload` 尝试挂载名为 `input` 的 HostPath 卷，但调度节点 `node2` 上的目标路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 校验失败（非目录或不存在），导致 `kubelet` 持续挂载失败。
证据编号 [2, 3, 4] 明确支持该结论。
*注意：路径在节点上不存在的根本原因（如清理脚本残留、节点状态不一致或配置错误）属于未确认事项。*

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.5s
├─ 并发证据采集: 40.3s
│  └─ g1 aiops-case-v06/workload: 40.3s (Evidence 34.8s, RCA 5.4s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed
