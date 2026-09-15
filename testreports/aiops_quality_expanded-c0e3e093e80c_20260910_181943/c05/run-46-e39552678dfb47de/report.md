## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-bntfh 的 YAML 中通过注解 `k8s.v1.cni.cncf.io/networks` 指定了网络附加定义 `unavailable-network`，但该 CR 在 namespace 中不存在，导致 Multus CNI 插件无法完成 Pod Sandbox 的网络初始化，引发 `FailedCreatePodSandBox` 错误。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 状态 `ContainerCreating` (`fact-2a63e2e85fef`) | 确认 Pod 停留在启动阶段，网络插件正在尝试分配网络 |
| 2 | K8s Event | Kubernetes | 46 次 `Warning NoNetworkFound`，信息均为 `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (`fact-0067255f695e` 等) | 提供决定性证据：Multus 插件因找不到指定网络定义而反复失败，阻止了 Pod 调度 |

证据表明，Pod 在创建过程中因 Multus CNI 插件无法解析网络附加定义而陷入无限重试循环。Kubernetes 事件 `NoNetworkFound` 明确指出了缺失的资源对象及其在 Pod 注解中的命名，构成了导致容器无法脱离 `ContainerCreating` 状态的直接原因。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 注解指定不存在的网络定义 `unavailable-network` → Multus 插件无法初始化网络 → 容器卡死在 `ContainerCreating` 状态 → 用户 Pod 启动失败
```

### 根因结论

已确认根因：Pod `aiops-case-05/workload-5dbb5dcd6c-bntfh` 的 YAML 定义中引用了网络附加定义 `unavailable-network`，但该资源在 `aiops-case-05` 命名空间中不存在。这导致 Multus CNI 插件在尝试为 Pod 分配网络时反复失败，引发 `FailedCreatePodSandBox` 错误，进而使容器始终停留在 `ContainerCreating` 状态。

这一结论由 Kubernetes 层面记录的 46 次 `NoNetworkFound` 警告事件直接证实，且无其他相互冲突的指标或日志。

---

## 📊 性能统计

```text
├─ 总耗时: 6.3m
├─ 问题定位: 27.5s
├─ 并发证据采集: 345.3s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 345.3s (Evidence 338.4s, RCA 6.6s)
└─ 汇总总结: 7.0s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed
