## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod aiops-case-v06/workload 处于 ContainerCreating 状态，挂载卷 input 持续失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod.condition Ready=False, ContainersNotReady: [app] | 确认 Pod 启动失败，容器未进入运行状态 |
| 2 | K8s Event | kubernetes | FailedMount: MountVolume.SetUp failed for volume "input" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory | 直接指出卷挂载失败原因：目标路径不是有效目录 |
| 3 | K8s State | kubernetes | pod.status Pending; container.waiting_reason ContainerCreating | 确认 Pod 卡在等待卷挂载阶段，无法推进至镜像拉取或容器创建 |
| 4 | Metric | prometheus | kube_pod_container_status_waiting_reason{reason="ContainerCreating"}=1 | 独立观测确认 Pod 处于 ContainerCreating 等待原因，状态持续 |

**证据互证：** 事件日志 `FailedMount` (Fact 2) 提供了明确的失败机制（HostPath 类型检查失败），直接解释了为何 K8s 状态 (Fact 1, 3) 显示为 `ContainersNotReady` 且持续 `ContainerCreating`。Metric (Fact 4) 从监控维度印证了 Pod 等待状态的持续性，与事件日志中的“x13 over 11m”超时记录一致，未观察到其他资源异常或重试成功迹象。

## 🎯 根因分析 · g1

### 因果链

```text
宿主机路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 不存在或类型不匹配 → kubelet 执行 MountVolume.SetUp 检查 HostPath 失败 → 卷 input 挂载超时，容器无法进入 ImagePull 阶段 → Pod 保持 ContainerCreating 状态
```

### 根因结论

已确认根因为 **Pod 挂载卷 `input` 配置的 HostPath 目标路径在宿主机上无效** (对应证据 Fact 2)。

Pod 定义中引用的 HostPath `/var/lib/aiops-fixture-unavailable-7f394bef/input` 在目标节点上不存在或不是预期的目录类型，导致 kubelet 的 `MountVolume.SetUp` 步骤抛出 `hostPath type check failed` 错误。该直接故障阻断了容器的初始化流程，导致 Pod 状态锁定在 `ContainerCreating` / `Pending` (对应证据 Fact 1, 3, 4)，无法进入后续的镜像拉取或运行阶段。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 12.5s
├─ 并发证据采集: 40.2s
│  └─ g1 aiops-case-v06/workload: 40.2s (Evidence 31.7s, RCA 8.4s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-imagepull-failed
