## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | 节点 node2 的 CNI 插件路径 (/opt/cni/bin) 中缺失 Pod 多租户网络 secondary-net 所依赖的 'aiops-unavailable' 插件，导致 kubelet 无法创建 Pod Sandbox。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedCreatePodSandBox`: `rpc error: code = Unknown desc = failed to setup network for sandbox ... plugin type="multus" name="multus-cni-network" failed (add): ... failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` | 直接报错，明确指出在 `/opt/cni/bin` 中找不到 `aiops-unavailable` 插件导致 Multus 添加容器网络失败。 |
| 2 | K8s State | kubernetes | Pod `aiops-case-v14/workload` 状态 `Pending`，异常状态 `ContainerCreating` | 确证了 Pod 因网络沙箱创建失败而阻塞在调度后的等待阶段，未进入运行状态。 |
| 3 | K8s Config | kubernetes | Pod 配置 `cni.projectcalico.org/networks: secondary-net`，依赖多租户网络 | 解释了 Pod 试图调用多租户网络插件（Multus）来附加 `secondary-net` 网络，触发了对缺失插件的查找。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值 `1` (Reason: `ContainerCreating`) | 监控确认容器处于等待网络就绪的阻塞状态，与事件中的网络错误原因一致。 |

证据 1 的 CNI 错误日志与证据 4 的监控等待状态互相印证，确认 Pod 无法启动的物理原因是网络插件缺失；证据 2 的状态与证据 3 的注解进一步限定了故障发生在 Pod 初始化阶段的网络沙箱创建环节。

## 🎯 根因分析 · g1

### 因果链

```text
节点 node2 CNI 路径 (/opt/cni/bin) 缺失插件 "aiops-unavailable" → Multus CNI 初始化容器网络失败 → 节点 kubelet 无法创建 Pod Sandbox (rpc error) → Pod 持续处于 ContainerCreating/Pending 阻塞状态
```

### 根因结论

已确认的根因为：节点 node2 的 CNI 插件目录 (`/opt/cni/bin`) 中缺失了 Pod 多租户网络 (`secondary-net`) 所依赖的特定网络插件 `aiops-unavailable`。

这一缺失导致 kubelet 在尝试为 Pod 创建沙箱时，Multus 插件调用失败，从而引发“FailedCreatePodSandBox”错误。该原因得到了 CNI 错误事件（证据 1）与 Pod 等待状态指标（证据 4）的直接支持。由于容器网络初始化失败，容器未启动，故日志与 Trace 维度不可用，但不影响对该根因的判定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 23.3s
├─ 并发证据采集: 29.3s
│  └─ g1 aiops-case-v14/workload: 29.3s (Evidence 22.6s, RCA 6.5s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-volume-mount-failed, pod-imagepull-failed
