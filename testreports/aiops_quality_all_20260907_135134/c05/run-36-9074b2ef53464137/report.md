## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod 配置了不存在的 Multus 网络附件定义 `unavailable-network`（annotation `k8s.v1.cni.cncf.io/networks`），导致 Multus 无法解析网络配置，kubelet 持续抛出 `FailedCreatePodSandBox` 错误，Pod 卡在 ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | multus | `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (fact-060cb7f4d318) | 明确指出了缺失的具体资源名及所属命名空间 |
| 2 | K8s Event | kubelet | `FailedCreatePodSandBox` ... `failed to setup network` ... `cannot find a network-attachment-definition "unavailable-network" not found` (fact-18b81cd55da8) | 确认了网络配置错误直接导致沙箱创建失败的底层机制 |
| 3 | K8s State | kubernetes | `container.waiting_reason: ContainerCreating` (fact-cea045a44b9e) | 确认 Pod 处于持续等待状态，未进入运行阶段 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"} = 1` (fact-369bbd9e623c) | 从监控指标确认当前存在处于该特定状态的容器实例 |

**证据说明：**
1、2 号事件证据形成了完整的因果闭环：Multus 报出缺失配置错误，kubelet 随即抛出沙箱创建失败错误；3、4 号状态与指标证据确认了该错误导致的最终容器状态表现，排除了运行时的偶发性波动。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 引用不存在的网络定义 (unavailable-network) → Multus 插件查找失败 (NoNetworkFound) → 网络初始化失败 (FailedCreatePodSandBox) → Pod 卡在 ContainerCreating 状态
```

### 根因结论

**已确认的根因**：Pod `aiops-case-05/workload-5dbb5dcd6c-kbwsx` 的 `k8s.v1.cni.cncf.io/networks` 注解中引用了名为 `unavailable-network` 的 NetworkAttachmentDefinition，但该资源在 `aiops-case-05` 命名空间中不存在。

Multus CNI 插件在尝试初始化网络时无法解析该配置，导致 `kubelet` 在创建 Pod 沙箱时失败 (证据 #2)，进而使 Pod 无法进入运行阶段，一直停留在 `ContainerCreating` 状态 (证据 #3, #4)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 25.8s
├─ 并发证据采集: 44.4s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 44.4s (Evidence 37.2s, RCA 7.0s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed, pod-imagepull-failed, pod-sandbox-create-failed
