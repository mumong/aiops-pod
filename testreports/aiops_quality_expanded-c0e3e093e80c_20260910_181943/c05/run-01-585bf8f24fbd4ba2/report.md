## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod workload-5dbb5dcd6c-bntfh in aiops-case-05 is stuck in `ContainerCreating` (Pending) state due to repeated `FailedCreatePodSandBox`. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `FailedCreatePodSandBox`: `failed to setup network for sandbox ... plugin type="multus" name="multus-cni-network" failed (add) ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 直接证实 kubelet 因 Multus CNI 插件找不到指定网络定义而创建沙箱失败 |
| 2 | K8s Event | multus | `NoNetworkFound`: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 独立于 kubelet，由 Multus 组件直接确认网络定义资源缺失 |
| 3 | K8s State | kubernetes | `pod.phase`: `Pending`; `container.waiting_reason`: `ContainerCreating`; `pod.condition.Reason`: `ContainersNotReady` | 确认 Pod 停留在等待阶段，容器未启动且未就绪 |
| 4 | K8s Config | kubernetes | `k8s.v1.cni.cncf.io/networks: unavailable-network` | 揭示根因上下文：Pod 注解显式请求了一个名为 "unavailable-network" 的网络 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (container: app, reason: ContainerCreating): `1` | 从指标层面确认容器持续处于等待创建状态，无重启记录 |

**证据小结：**
kubelet 与 Multus 组件的日志事件（#1, #2）高度一致，共同指向 CNI 初始化失败。K8s 状态（#3）和指标（#5）确认了该失败导致的持续阻塞现象。配置事实（#4）提供了具体的错误来源，即注解中引用的网络定义不存在。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 引用不存在的 NetworkAttachmentDefinition 'unavailable-network' (K8s Config) 
→ Multus CNI 在命名空间 aiops-case-05 中找不到该 CRD 
→ kubelet 调用 Multus 插件创建 Pod 沙箱失败 
→ Pod 状态卡死在 ContainerCreating (Pending)
```

### 根因结论

**已确认的根因**：Pod `workload-5dbb5dcd6c-bntfh` 在注解 `k8s.v1.cni.cncf.io/networks` 中引用了名为 `unavailable-network` 的 `NetworkAttachmentDefinition`，但在命名空间 `aiops-case-05` 中该资源不存在（证据 #1, #2, #4）。这导致 Multus CNI 插件初始化失败，进而使 kubelet 无法创建 Pod 沙箱，容器因此无法启动（证据 #3, #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 39.6s
├─ 并发证据采集: 58.2s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 58.2s (Evidence 48.5s, RCA 9.6s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-imagepull-failed, pod-sandbox-create-failed, pod-volume-mount-failed
