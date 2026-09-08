## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod 配置引用了不存在的 Multus 网络附加定义 `unavailable-network`，导致 CNI 插件无法创建网络沙箱。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes/fact-3cedf19c508ac` | `FailedCreatePodSandBox`: `failed to setup network for sandbox ... plugin type="multus" ... error loading k8s delegates k8s args: TryLoadPodDelegates: error in getting k8s network for pod: GetNetworkDelegates: failed getting the delegate: getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 确认 CNI 插件因缺失 NAD 配置无法完成 Pod 沙箱网络初始化 |
| 2 | K8s Event | `kubernetes/fact-05414041e14d` | `NoNetworkFound` (持续 60m): `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` | 确认集群范围内该 NetworkAttachmentDefinition 资源长期缺失 |
| 3 | Metric | `prometheus/fact-72d0a6dc0ab5` | `kube_pod_container_status_waiting_reason` (reason: `ContainerCreating`, value: `1`) | 观测到 Pod 停留在创建等待状态，与 CNI 初始化失败的事实一致 |

**证据总结：**
Kubernetes Event 与 Metric 相互印证：Pod 因 Multus 插件找不到指定的 `NetworkAttachmentDefinition` (`unavailable-network`) 而失败，导致容器无法创建，状态卡在 `ContainerCreating`。

## 🎯 根因分析 · g1

### 因果链

```text
配置引用了不存在的 Multus NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 插件解析网络配置失败 → 无法创建 Pod 网络沙箱 (Sandbox) → Pod 卡在 ContainerCreating 状态
```

### 根因结论

已确认根因为 **Pod 配置引用了不存在的 Multus 网络附加定义** `unavailable-network`。

该缺失资源导致 Multus CNI 插件在尝试初始化 Pod 网络沙箱时无法获取网络委托配置 (`GetNetworkDelegates failed`)，引发 `FailedCreatePodSandBox` 错误。Metric 数据证实该故障持续导致 Pod 停留在 `ContainerCreating` 状态，无法进入运行阶段。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 61.8s
├─ 并发证据采集: 38.7s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 38.7s (Evidence 31.4s, RCA 6.9s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- 未调用 Runbook
