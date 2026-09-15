## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod workload-5dbb5dcd6c-bntfh 在 aiops-case-05 命名空间中卡在 ContainerCreating 状态，Pod Phase 为 Pending，且无法创建容器沙箱。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | multus | `Warning NoNetworkFound ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` | 直接表明 Multus 插件找不到所需的网络定义资源，是导致失败的直接原因。 |
| 2 | K8s Event | kubelet | `Warning FailedCreatePodSandBox ... Failed to create pod sandbox: rpc error: code = Unknown desc = failed to setup network for sandbox ... Multus: ... error in getting k8s network for pod: GetNetworkDelegates: failed getting the delegate ... "unavailable-network" not found` | 验证了容器沙箱创建因网络插件配置缺失而失败，证实了 `ContainerCreating` 卡住的具体机制。 |
| 3 | K8s State | Kubelet | `container: "app", reason: "ContainerCreating"` | 确认应用容器 `app` 处于等待启动状态，与事件描述一致。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` (reason: `ContainerCreating`, value: `1`) | 从指标层面确认了 Pod 处于等待容器创建的状态，支持了现象描述。 |

证据链闭合：Kubernetes 事件明确指出 `multus` 插件在尝试解析 `unavailable-network` 网络定义时返回 `not found` 错误，直接导致 `kubelet` 无法创建容器沙箱，进而使 Pod 维持在 `ContainerCreating` 状态。指标与状态事实佐证了这一现象的持续性。

## 🎯 根因分析 · g1

### 因果链

```text
配置了引用不存在资源 'unavailable-network' 的网络注解 → Multus CNI 插件无法找到网络定义并抛出错误 → 容器沙箱创建失败 → Pod 卡在 ContainerCreating 状态
```

### 根因结论

已确认的根因是 Pod 配置了引用名为 `unavailable-network` 的 Multus 网络注解，但该名称的 `NetworkAttachmentDefinition` 资源在 `aiops-case-05` 命名空间中不存在。这一配置缺失导致 Multus CNI 插件在初始化网络时无法获取所需的代理配置（证据 1、2），从而阻止了容器沙箱的成功创建，最终表现为 Pod 永远无法通过 `ContainerCreating` 阶段进入运行状态。

---

## 📊 性能统计

```text
├─ 总耗时: 6.2m
├─ 问题定位: 17.6s
├─ 并发证据采集: 348.4s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 348.4s (Evidence 341.1s, RCA 7.2s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-imagepull-failed
