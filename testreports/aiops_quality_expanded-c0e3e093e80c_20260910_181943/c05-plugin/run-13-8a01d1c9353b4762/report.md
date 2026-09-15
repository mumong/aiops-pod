## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | 节点 node2 缺失 CNI 插件二进制文件 'aiops-unavailable'，导致 Multus CNI 在创建 Pod 网络沙箱时因找不到插件而失败，致使 Pod 停滞在 ContainerCreating 阶段。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedCreatePodSandBox ... failed to setup network for sandbox ... plugin type="multus" name="multus-cni-network" failed (add) ... failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` (fact-05cb157b42b5) | 确认 CNI 插件缺失导致网络沙箱创建失败 |
| 2 | K8s State | kubernetes | `reason: "ContainerCreating"` (fact-077806941deb) | 确认 Pod 停滞在网络初始化阶段 |
| 3 | K8s State | kubernetes | `phase: "Pending"` (fact-448f1963b796) | 确认 Pod 整体状态未进入 Running |
| 4 | K8s Config | kubernetes | `Annotations: k8s.v1.cni.cncf.io/networks: secondary-net` (fact-8f82b4b9baf5) | 确认应用请求了二级网络配置，触发了 Multus |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = `1` (labels: `reason: "ContainerCreating"`) (fact-84b48585e35b) | 从监控侧证实 Pod 处于 ContainerCreating 等待状态 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total` = `0` (fact-b82a403c1238) | 确认应用容器尚未启动，排除了应用崩溃重启可能 |
| 7 | Metric | prometheus | `kube_pod_status_phase` = `1` (labels: `phase: "Pending"`) (fact-79ae877d35d9) | 监控数据证实 Pod 处于 Pending 阶段 |

**证据说明：**
Kubernetes 事件（#1）提供了最直接的诊断依据，明确指出了网络插件 `aiops-unavailable` 缺失。状态信息（#2, #3）和监控数据（#5, #7）从不同维度交叉验证了 Pod 停滞在“Pending/ContainerCreating”状态。监控侧未检测到重启（#6），符合容器因网络配置失败而未能启动的特征。日志和追踪数据因容器未启动而不可用。

## 🎯 根因分析 · g1

```text
节点 node2 缺失 CNI 插件二进制文件 'aiops-unavailable' → Multus CNI 无法创建 Pod 网络沙箱 → 容器网络配置失败 → Pod 停滞在 ContainerCreating/Pending 阶段
```

**根因结论：**
已确认根因为**节点 node2 缺失 CNI 插件二进制文件**。
该缺失导致 Multus CNI 在尝试配置 Pod 网络时无法找到 `aiops-unavailable` 插件（证据 #1），从而无法创建网络沙箱。Pod 因此无法通过初始化阶段，被 Kubernetes 调度器保持在 `Pending` 状态（证据 #3），容器状态显示为 `ContainerCreating` 等待（证据 #2, #5）。应用日志与追踪数据不可用（输入未提供）属于该根因导致的衍生现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.8s
├─ 并发证据采集: 40.6s
│  └─ g1 aiops-case-v14/workload: 40.6s (Evidence 34.6s, RCA 5.9s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-volume-mount-failed
