## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx (aiops-case-05) stuck in ContainerCreating phase due to FailedCreatePodSandBox |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning FailedCreatePodSandBox` kubelet: `failed to setup network for sandbox... plugin type="multus" name="multus-cni-network" failed (add)... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (fact_id: `fact-3089ff791257`) | 直接证明 Pod 调度失败机制，Multus 插件因无法获取网络配置而拒绝创建容器 |
| 2 | K8s Event | Kubernetes | `Warning NoNetworkFound` multus: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` (fact_id: `fact-0679dd705195`) | 提供根本原因证据，确认 `aiops-case-05` 命名空间下缺失名为 `unavailable-network` 的 CRD 资源 |
| 3 | K8s State | Kubernetes | `ContainerCreating` (fact_id: `fact-89854a08737e`) | 确认 Pod 当前异常状态，符合因网络初始化失败导致的阻塞表现 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1, labels: `reason="ContainerCreating"`, `container="app"` (fact_id: `fact-c3800a4a31e3`) | 监控侧数据独立印证 Pod 处于等待状态 |

**证据关系：**
Kubernetes 事件明确指出了失败链路：因缺少 `unavailable-network` 这一具体的 NetworkAttachmentDefinition 资源（事实 2），导致 Multus CNI 插件无法完成网络配置（事实 1），最终致使 Pod 停留在 `ContainerCreating` 状态（事实 3）。Metric 数据（事实 4）作为客观的持续观测，独立证实了该阻塞状态的存在。Logging 和 Tracing 因容器未启动而不可用，但不影响基于 K8s 状态机事件的诊断。

## 🎯 根因分析 · g1

### 因果链

```text
命名空间 aiops-case-05 中缺失 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 插件无法获取网络配置 → 容器沙箱创建失败 (FailedCreatePodSandBox) → Pod 卡在 ContainerCreating 状态
```

### 根因结论

已确认根因为 **命名空间 `aiops-case-05` 中缺失名为 `unavailable-network` 的 `NetworkAttachmentDefinition` 资源**。

该缺失导致 Multus CNI 插件在执行网络插件时无法找到预期的网络配置定义，从而引发 `FailedCreatePodSandBox` 错误，使 Pod 无法进入运行状态。该结论由 K8s 事件中的 `NoNetworkFound` 警告及具体的 `not found` 错误原文直接支撑（证据 1、2）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 22.3s
├─ 并发证据采集: 50.6s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 50.6s (Evidence 42.2s, RCA 8.0s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-imagepull-failed, pod-sandbox-create-failed
