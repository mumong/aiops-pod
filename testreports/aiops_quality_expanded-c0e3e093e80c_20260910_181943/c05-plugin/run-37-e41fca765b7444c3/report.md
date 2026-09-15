## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod aiops-case-v14/workload 使用 Multus CNI 配置了名为 secondary-net 的网络，但其引用的网络插件可执行文件 aiops-unavailable 在节点 node2 的 CNI 路径 [/opt/cni/bin] 中缺失，导致 Pod 沙箱（Sandbox）创建失败，容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning FailedCreatePodSandBox ... failed to setup network for sandbox "a2dd4c27504ff4dc1725009cd80c4198a6788079c9569c90df5c4e4e4d96e7f7": plugin type="multus" name="multus-cni-network" failed (add): ... error adding container to network "secondary-net": failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` | 直接捕获了 Pod 沙箱创建失败时的 CNI 错误，明确指出缺失名为 `aiops-unavailable` 的插件。 |
| 2 | K8s State | Kubernetes | `Waiting reason: ContainerCreating` | 指示容器因依赖项（此处为网络插件）不可用而处于等待创建状态。 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"} = 1` | 从监控系统确认当前正处于容器等待创建的状态，与 Kubernetes 事件结论一致。 |
| 4 | K8s State | Kubernetes | `Pod status: Pending, phase: Pending, restart_count: 0` | 确认 Pod 调度完成但未能进入运行阶段，且无重启历史，说明问题持续发生且非瞬态。 |

**证据互证：**
Kubernetes 事件（证据 #1）直接提供了故障的根因上下文，表明网络插件缺失是沙箱创建失败的唯一原因；该事件引发的 `ContainerCreating` 状态与等待指标（证据 #3）形成闭环印证。由于 Pod 始终处于 `Pending` 且重启次数为 0（证据 #4），排除了应用层逻辑错误，进一步锚定故障发生在基础设施/网络插件层面。

## 🎯 根因分析 · g1

### 因果链

```text
节点 node2 CNI 路径 [/opt/cni/bin] 中缺失可执行文件 "aiops-unavailable" → Multus CNI 配置 "secondary-net" 调用插件失败 → Pod aiops-case-v14/workload 沙箱创建失败 (FailedCreatePodSandBox) → 容器状态持续为 ContainerCreating (Pending)
```

### 根因结论

已确认的根因为：Pod `aiops-case-v14/workload` 依赖的 Multus CNI 网络配置 `secondary-net` 调用了插件 `aiops-unavailable`，但目标节点 `node2` 的 CNI 插件目录 `[/opt/cni/bin]` 中未找到该可执行文件，导致沙箱创建过程彻底失败（证据 #1）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.6s
├─ 并发证据采集: 37.8s
│  └─ g1 aiops-case-v14/workload: 37.8s (Evidence 30.5s, RCA 7.1s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-volume-mount-failed, pod-sandbox-create-failed, pod-config-error
