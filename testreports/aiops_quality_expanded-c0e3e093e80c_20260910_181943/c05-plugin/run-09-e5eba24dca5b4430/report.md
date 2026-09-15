## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | 目标节点 node2 的 /opt/cni/bin 路径下缺失 Pod 附加网络所需的 CNI 插件 'aiops-unavailable'，导致 Multus CNI 执行失败，无法创建 Pod Sandbox，从而使容器状态保持在 ContainerCreating。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedCreatePodSandBox ... Failed to create pod sandbox: rpc error: code = Unknown desc = failed to setup network for sandbox "a2dd4c27504ff4dc1725009cd80c4198a6788079c9569c90df5c4e4e4d96e7f7": plugin type="multus" name="multus-cni-network" failed (add): [aiops-case-v14/workload:secondary-net]: error adding container to network "secondary-net": failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` (fact-5d3ecbf15700) | 提供直接因果证据，定位到 CNI 插件缺失导致网络初始化失败 |
| 2 | K8s State | kubernetes | `container.waiting_reason: ContainerCreating` (fact-908ae0978e9c) | 描述当前阻碍业务容器运行的状态 |
| 3 | K8s Config | kubernetes | `Annotations: k8s.v1.cni.cncf.io/networks: secondary-net` (fact-33a742eef458) | 说明 Pod 期望通过 Multus 配置附加网络，从而触发了对特定 CNI 插件的查找 |
| 4 | K8s State | kubernetes | `pod.phase: Pending` (fact-4818da35b454) | 确认 Pod 卡在调度或初始化阶段，尚未进入运行状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` (fact-0d74b14176e0) | 从监控层确认容器持续处于等待状态 |
| 6 | Metric | prometheus | `kube_pod_container_status_restarts_total = 0` (fact-8734efdce74a) | 排除业务应用已崩溃重启的可能性，验证故障发生在启动前阶段 |

K8s Event 明确给出了失败机制与具体错误信息（缺失 'aiops-unavailable' 插件），直接支撑了状态保持 `ContainerCreating` 和 `Pending` 的现象。Metric 的等待原因与重启数为零的数据，排除了应用层启动后崩溃的场景，将问题严格限定在 Kubelet 执行 CNI 插件调用的初始化阶段。

## 🎯 根因分析 · g1

### 因果链

```text
节点 node2 的 CNI 插件路径下缺失 'aiops-unavailable' 插件 → Multus CNI 尝试为 secondary-net 附加网络时执行失败 → Kubelet 创建 Pod Sandbox 流程因网络初始化报错中断 → Pod 容器状态卡在 ContainerCreating
```

### 根因结论

已确认根因为：目标节点 node2 的 `/opt/cni/bin` 路径下缺少名为 `aiops-unavailable` 的 CNI 插件。

具体而言，Pod `aiops-case-v14/workload` 配置了附加网络 `secondary-net`，在调度至 node2 后，Kubelet 调用 Multus CNI 进行网络配置，但在指定路径下未能找到该插件文件（见证据表 #1，fact-5d3ecbf15700）。这一缺失导致网络设置失败，进而使 Pod Sandbox 无法创建，容器一直处于 `ContainerCreating` 状态等待中（见证据表 #2，fact-908ae0978e9c）。

目前证据不足以判断该插件应当是“被意外删除/未部署”，还是“Pod YAML 配置中错误引用了不存在的插件名称”。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 12.3s
├─ 并发证据采集: 41.4s
│  └─ g1 aiops-case-v14/workload: 41.4s (Evidence 33.7s, RCA 7.6s)
└─ 汇总总结: 12.5s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-volume-mount-failed
