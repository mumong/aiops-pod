## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v14/workload` | ContainerCreating | Pod aiops-case-v14/workload stuck in Pending/ContainerCreating |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-v14/workload` 状态 `Pending`，容器 `app` 等待原因 `ContainerCreating` | 确立异常实体与当前停滞阶段 |
| 2 | K8s Event | kubernetes | `FailedCreatePodSandBox`: `rpc error... failed to setup network for sandbox... plugin type="multus"... error adding container to network "secondary-net": failed to find plugin "aiops-unavailable" in path [/opt/cni/bin /opt/cni/bin]` | 明确失败机制：缺少特定 CNI 插件 |
| 3 | K8s Config | kubernetes | Pod 使用注解 `k8s.v1.cni.cncf.io/networks: secondary-net` 请求 Multus 网络 | 确认异常发生的网络上下文 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (reason=`ContainerCreating`) 值为 1，无趋势样本 | 确认 Pod 持续处于等待网络绑定的等待状态 |

证据 2 直接提供了失败原因（找不到 `aiops-unavailable` 插件），证据 1 与 4 相互印证该 Pod 目前停留在沙箱创建前的等待阶段，未出现重启，确认为首次调度阻塞。

## 🎯 根因分析 · g1

### 因果链

```text
节点 (Node2) 缺失 CNI 插件 'aiops-unavailable' → Multus 无法加载插件完成网络附加 → Kubelet 创建 Pod 沙箱失败 (FailedCreatePodSandBox) → Pod 处于 Pending/ContainerCreating 状态
```

### 根因结论

已确认的根因是节点上缺少名为 `aiops-unavailable` 的 CNI 二进制插件，导致 Multus 网络插件在挂载名为 `secondary-net` 的第二层网络时调用失败。Kubernetes 事件记录 (`fact-35d954b6a2b8`) 中明确报错 `failed to find plugin "aiops-unavailable" in path`，直接阻断了 Pod 的网络初始化进程。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 27.5s
├─ 并发证据采集: 38.5s
│  └─ g1 aiops-case-v14/workload: 38.5s (Evidence 29.5s, RCA 8.8s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-v14/workload**: pod-volume-mount-failed
