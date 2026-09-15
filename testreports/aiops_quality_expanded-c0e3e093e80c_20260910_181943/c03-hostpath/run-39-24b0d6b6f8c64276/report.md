## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod aiops-case-v06/workload 的 spec.volumes 中定义了一个 hostPath 卷 'input'，其配置类型要求为 'Directory'，指向节点 node2 上的路径 '/var/lib/aiops-fixture-unavailable-7favailable-7f394bef/input'。然而该路径在节点上实际不存在（'No such file or directory'），导致 kubelet 在 MountVolume.SetUp 阶段因 'hostPath type check failed' 持续挂载失败，进而阻塞容器创建流程，使 Pod 长期停留在 ContainerCreating/Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod condition | Ready=False (ContainersNotReady)；ContainersReady=False | 确认 Pod 处于未就绪状态，且应用容器未进入运行生命周期 [fact-04159f2d5ba8, fact-c163a256a316] |
| 2 | K8s State | Pod phase | Pending | 确认 Pod 因前置依赖（如挂载）未完成而无法进入 Running 阶段 [fact-58d9b88939e6] |
| 3 | K8s Event | FailedMount | "hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory" | 直接指明卷 'input' 挂载失败的具体原因：目标路径不存在 [fact-ae25825171cc] |
| 4 | K8s Event | FailedMount | "timed out waiting for the condition" (持续重复 20+ 次) | 验证 kubelet 正在持续重试挂载，导致阻塞时间延长 [fact-006e2e49f827] |
| 5 | Metric | kube_pod_container_status_waiting_reason | app 容器 reason=ContainerCreating (当前值=1) | 从指标侧确认应用容器正处于容器创建阶段，未能推进 [fact-c2ac3bf71224] |

证据说明：
1. K8s 事件（#3, #4）提供了明确的失败机制：`hostPath` 挂载在 `MountVolume.SetUp` 阶段因路径不存在而失败。
2. K8s 状态（#1, #2）和指标（#5）共同印证了这一故障的持续性：由于挂载失败，Pod 被阻塞在 `Pending` 阶段，容器无法创建，导致 `ContainerCreating` 状态长期不消退。
3. 资源配置（50m CPU/32Mi Memory）极小，排除了资源争抢导致的调度或启动缓慢，进一步锁定故障点为挂载本身。

## 🎯 根因分析 · g1

### 因果链

```text
节点 node2 上缺少目标目录 '/var/lib/aiops-fixture-unavailable-7f394bef/input' → 
kubelet 执行 MountVolume.SetUp 时 hostPath 类型检查失败 → 
卷 'input' 挂载持续超时失败 → 
Pod aiops-case-v06/workload 阻塞在 ContainerCreating/Pending 状态，应用未启动
```

### 根因结论

已确认根因：**Pod `aiops-case-v06/workload` 定义的 `hostPath` 卷挂载目标路径在节点上不存在**。

证据支撑：
* K8s Event 直接报错 "hostPath type check failed: ... is not a directory"（证据 #3）。
* 该事件反复触发，导致 Pod 状态卡在 `Pending` 且应用容器状态为 `ContainerCreating`（证据 #1, #2, #5）。
* 资源限制极低且重启次数为 0，排除了其他启动故障可能。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 13.7s
├─ 并发证据采集: 79.9s
│  └─ g1 aiops-case-v06/workload: 79.9s (Evidence 71.0s, RCA 8.9s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-imagepull-failed, pod-pending-unschedulable, pod-volume-mount-failed, pod-config-error, pod-sandbox-create-failed
