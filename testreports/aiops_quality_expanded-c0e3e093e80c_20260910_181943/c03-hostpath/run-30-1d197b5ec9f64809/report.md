## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod `workload` 在 `aiops-case-v06` 中配置了引用宿主机路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 的 hostPath 卷，但该路径在目标节点 `node2` 上不存在或不是目录，导致 kubelet 挂载卷失败（FailedMount），进而阻塞容器创建，使 Pod 状态维持在 `Pending` 和 `ContainerCreating`。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `MountVolume.SetUp failed for volume "input" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 明确指向目标节点宿主机路径缺失或非目录，直接阻断卷挂载。 |
| 2 | K8s State | kubelet | Pod Status: `Pending` | 展示容器因前置步骤未就绪而被阻塞的宏观状态。 |
| 3 | K8s Config | Pod Definition | 配置 hostPath 卷，目标路径为 `/var/lib/aiops-fixture-unavailable-7f394bef/input` | 提供故障发生的具体卷配置对象及目标路径。 |
| 4 | K8s Event | kubelet | `Unable to attach or mount volumes: unmounted volumes=[input]... timed out waiting for the condition` | 说明故障持续时间较长（50m），验证了挂载阻塞导致容器无法启动的长期性。 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 量化证实容器处于创建等待阶段，未发生重启或运行。 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total = 0` | 排除容器启动后反复崩溃（CrashLoopBackOff）的可能性。 |

**证据链说明：**
K8s 事件（#1, #4）与配置（#3）构成了逻辑闭环，证明 Pod 因 `hostPath` 在节点 `node2` 上不存在而阻塞；指标数据（#5, #6）在时间线上印证了该 Pod 长时间处于 `ContainerCreating` 阶段且无任何重启发生，排除了运行时资源不足或应用崩溃导致的等待。

## 🎯 根因分析 · g1

### 因果链

```text
目标节点 node2 上宿主机路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 不存在或非目录 → kubelet 挂载 hostPath 卷失败 (FailedMount) → Pod 状态被强制维持在 Pending 且容器进入 ContainerCreating 等待状态 → 业务服务完全不可用
```

### 根因结论

已确认根因为 **Pod `workload` 配置的 `hostPath` 卷在目标节点 `node2` 上缺乏有效挂载点**（证据 #1, #3）。

具体而言，Pod 定义中引用了路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input`，但 Kubelet 在调度至 `node2` 执行卷挂载时，因该路径在宿主机上类型校验失败（不存在或不是目录），触发了 `FailedMount` 事件。由于挂载前置条件未满足，容器进程无法启动，进而导致 Pod 状态长期停滞在 `Pending` / `ContainerCreating`。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 20.9s
├─ 并发证据采集: 31.4s
│  └─ g1 aiops-case-v06/workload: 31.4s (Evidence 24.4s, RCA 7.0s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-imagepull-failed
