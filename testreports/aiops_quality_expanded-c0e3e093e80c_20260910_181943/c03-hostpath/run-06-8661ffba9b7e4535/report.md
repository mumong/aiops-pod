## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod aiops-case-v06/workload stuck in ContainerCreating state due to volume mount failure. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `FailedMount` | `hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 直接指出宿主机路径验证失败的错误信息 |
| 2 | K8s State | `pod.status` | `Pending` | 证实 Pod 处于未启动的挂起状态 |
| 3 | K8s State | `pod.condition` | `ContainersNotReady`, `type: Ready, status: False` | 证实容器未就绪的根本状态 |
| 4 | K8s State | `container.waiting_reason` | `ContainerCreating` | 证实 Pod 卡在创建容器前的等待状态 |
| 5 | Metric | `kube_pod_container_status_waiting_reason` | `1` (reason: `ContainerCreating`) | 独立确认容器处于创建等待的指标数值 |
| 6 | K8s State | `pod.phase` | `Pending` | 独立确认 Pod 的阶段状态 |

**证据说明**：
1. 事件 `fact-5427b7fa23ab` 明确记录了 kubelet 挂载卷时的失败原因（宿主机路径检查失败），这是导致 `ContainerCreating` 的直接原因。
2. 指标 `fact-8c53deaecb52` 与 K8s 事件中的错误类型一致，共同印证了 Pod 卡在创建阶段的事实，排除了其他错误类型的可能性。
3. 日志和追踪维度标注为 `not_applicable`，因为容器未启动，物理上无法产生相关业务数据，但这不影响基于 K8s 状态和事件的根因诊断。

## 🎯 根因分析 · g1

### 因果链

```text
宿主机节点2上的 /var/lib/aiops-fixture-unavailable-7f394bef/input 路径不存在或不是目录 → kubelet HostPath 卷挂载前置检查失败 (hostPath type check failed) → Pod 的 volume "input" 挂载失败 → 容器 'app' 持续处于 ContainerCreating 等待状态
```

### 根因结论

**已确认的根因**：Pod `aiops-case-v06/workload` 挂载的 `hostPath` 卷 `input` 目标目录在宿主机节点上缺失或无效。

Kubelet 在执行 `MountVolume.SetUp` 阶段检查 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 时，因该路径不满足“是目录”的要求而直接失败（见证据 #1 `fact-5427b7fa23ab`）。这导致 Pod 无法完成卷挂载步骤，从而持续处于 `ContainerCreating` 状态（见证据 #4 `fact-61b63c4985c2`）和 `Pending` 阶段（见证据 #2 `fact-0c3f09b68fc6`）。指标数据 `fact-8c53deaecb52` 独立印证了该等待状态的持续存在。

---

## 📊 性能统计

```text
├─ 总耗时: 57.5s
├─ 问题定位: 17.1s
├─ 并发证据采集: 30.2s
│  └─ g1 aiops-case-v06/workload: 30.2s (Evidence 24.0s, RCA 6.2s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed
