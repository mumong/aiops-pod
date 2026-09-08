## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-kbwsx 处于 ContainerCreating/Pending 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning NoNetworkFound ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` (fact-005de8a839b2, fact-01aea98b7616, fact-032ccc489df9...) | 证实 Pod 引用了不存在的 NetworkAttachmentDefinition |
| 2 | K8s Event | kubernetes | `Warning FailedCreatePodSandBox ... failed setup network for sandbox ... plugin type="multus" ... failed getting the delegate: getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network)` (fact-1c5c16aac603, fact-2a70c75cd68c, fact-337daac596f2...) | 证实 Multus 插件因网络配置缺失导致沙箱创建失败 |
| 3 | K8s State | kubernetes | `reason: ContainerCreating` for container `app` (fact-57b4ab9444a1) | 描述 Pod 处于等待网络就绪的阻塞状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating", container="app"} = 1` (fact-2c6675021a7d) | 数值证据佐证 Pod 因等待原因处于挂起状态 |

上述证据形成闭环：`fact-1` 和 `fact-2` 明确指出 Multus 因缺少 `unavailable-network` 配置导致网络初始化失败；`fact-3` 和 `fact-4` 记录了下层网络故障直接导致的容器状态阻塞结果。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 声明了网络配置 'unavailable-network' → 集群缺少该 NetworkAttachmentDefinition 资源 → Multus 插件初始化失败无法创建 Pod Sandbox → Pod 卡在 ContainerCreating 状态
```

### 根因结论

已确认的根因为 **Pod 声明了不存在的 NetworkAttachmentDefinition `unavailable-network`**。
*   **直接证据**：Kubernetes Event 中反复出现 `NoNetworkFound` (事实 1) 及 `FailedCreatePodSandBox` (事实 2)，明确报出 `cannot find a network-attachment-definition ... "unavailable-network" not found`。
*   **现象印证**：容器因无法建立网络沙箱而被 kubelet 阻塞在 `ContainerCreating` 状态 (事实 3)，Metric (事实 4) 从外部观测证实了该状态的持续性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 16.5s
├─ 并发证据采集: 55.2s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 55.2s (Evidence 48.2s, RCA 6.8s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed, pod-imagepull-failed, pod-sandbox-create-failed
