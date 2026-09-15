## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod workload 处于 Pending/ContainerCreating 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedCreatePodSandBox`: "failed to setup network for sandbox... plugin type=\"multus\" name=\"multus-cni-network\"... error adding container to network \"secondary-net\": failed to find plugin \"aiops-unavailable\" in path [/opt/cni/bin /opt/cni/bin]" | 直接失败现象，明确缺失插件名及路径 |
| 2 | K8s State | kubernetes | `ContainerCreating` / `Pending`，`ContainersReady` 状态为 `False` | 描述 Pod 当前停滞的阻塞状态 |
| 3 | K8s Config | kubernetes | Pod 配置 `k8s.v1.cni.cncf.io/networks: secondary-net` | 指示 Pod 请求了名为 `secondary-net` 的附加网络 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值为 `1` (`reason: ContainerCreating`) | 从监控时序数据确认 Pod 处于等待创建容器的状态 |

**证据关联说明：**
Kubernetes 事件 (#1) 揭示了 `multus` 调用 `secondary-net` 附加网络时，在宿主机路径 `/opt/cni/bin` 下未能找到名为 `aiops-unavailable` 的插件二进制文件。这一底层网络配置缺失直接导致 SandBox 创建失败，进而表现为 Pod 状态 (#2) 长期卡在 `ContainerCreating`。监控数据 (#4) 的时序观测与这一即时故障原因相互印证，证实了阻塞发生在容器初始化前的网络准备阶段。

## 🎯 根因分析 · g1

### 因果链

```text
Multus 网络配置引用不存在的 CNI 插件 'aiops-unavailable' → 节点 CNI 运行时插件缺失 → 网络初始化失败 (SandBox 创建报错) → Pod 卡在 ContainerCreating 状态
```

### 根因结论

**已确认的根因**：Pod 使用的 Multus 附加网络配置（`secondary-net`）引用了名为 `aiops-unavailable` 的 CNI 插件，但目标节点（node2）的 `/opt/cni/bin` 目录下缺失该插件的二进制文件。

该缺失直接导致 kubelet 在执行 Pod SandBox 创建时无法完成网络附加步骤，从而抛出 `FailedCreatePodSandBox` 错误。这一机制导致容器无法启动，表现为 Pod 永久处于 `ContainerCreating` 状态，且重启计数为 0（无应用逻辑运行）。证据 #1 中的报错原文与证据 #3 中的网络注解构成了完整的因果闭环。

---

## 📊 性能统计

```text
├─ 总耗时: 10.3m
├─ 问题定位: 17.4s
├─ 并发证据采集: 592.5s
│  └─ g1 aiops-case-v14/workload: 592.5s (Evidence 584.7s, RCA 7.7s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-volume-mount-failed
