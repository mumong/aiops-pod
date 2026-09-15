## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | HostPath卷挂载失败：Pod定义的HostPath卷 'input' 指向节点 node2 上的路径 '/var/lib/aiops-fixture-unavailable-7f394bef/input'，但该路径不存在或不是目录，导致Kubelet挂载卷失败，Pod卡在ContainerCreating状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `FailedMount hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` (fact-154095a4ae03) | 直接说明 HostPath 卷挂载因路径非目录而失败 |
| 2 | K8s State | kubelet | `ContainerCreating` (fact-15a5b23b41b2) | 确认 Pod 卡在创建阶段，无法进入运行态 |
| 3 | K8s State | kubelet | `ContainersReady=False`, `Ready=False` (fact-11aa9612c3e8, fact-dfbb07489187) | 确认 Pod 条件未就绪，容器未准备 |
| 4 | K8s State | kubelet | `pod.phase=Pending` (fact-f68ff961d2c5) | 确认集群层面 Pod 处于挂起等待状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (reason=ContainerCreating) (fact-c5c8f033334e) | 独立观测到容器持续处于等待创建状态 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total=0` (fact-db3cfb112511) | 确认容器从未成功启动过，无重启记录 |

**证据印证说明：**
1. K8s Event (fact-154095a4ae03) 提供了故障的物理原因（HostPath 类型检查失败），直接解释了 K8s State 中 Pod 状态为何无法推进。
2. Metric (fact-c5c8f033334e) 与 K8s State (fact-15a5b23b41b2) 相互印证，共同确认 Pod 卡在 `ContainerCreating` 且未发生任何启动动作。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义中 HostPath 卷指向 '/var/lib/aiops-fixture-unavailable-7f394bef/input' → Kubelet 检查路径失败 (非目录) → FailedMount → Pod 卡在 ContainerCreating 状态 (Pending/NotReady)
```

### 根因结论

已确认根因为 **HostPath 卷挂载失败**。

Pod `aiops-case-v06/workload` 中定义的 HostPath 卷 `input` 指向节点 `node2` 上的路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input`，但该路径在节点上不存在或并非目录（证据：`FailedMount` 事件 fact-154095a4ae03）。这一文件系统级别的异常导致 Kubelet 无法完成卷挂载，进而使 Pod 始终无法创建容器，表现为 `ContainerCreating` 状态且未重启（证据：fact-15a5b23b41b2, fact-db3cfb112511）。

---

## 📊 性能统计

```text
├─ 总耗时: 56.6s
├─ 问题定位: 15.9s
├─ 并发证据采集: 30.1s
│  └─ g1 aiops-case-v06/workload: 30.1s (Evidence 23.1s, RCA 6.9s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-imagepull-failed, pod-volume-mount-failed
