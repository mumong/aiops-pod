## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod workload-5dbb5dcd6c-nhd7v 处于 ContainerCreating (Waiting) 状态，Sandbox 无法创建。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | fact-7b03112de84d: container="app", reason="ContainerCreating" | 确认 Pod 容器卡在创建阶段，未进入运行状态。 |
| 2 | K8s Event | multus | fact-03a6055c8938: "cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io \"unavailable-network\" not found" | 核心证据：Multus 插件明确报出缺少关键网络附件定义资源。 |
| 3 | K8s Event | kubelet | fact-1219282678eb: "failed to setup network for sandbox... plugin type=\"multus\"... failed getting the delegate: getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network)... not found" | 直接证据：证明网络配置失败导致 Pod Sandbox 创建彻底中止。 |
| 4 | Metric | prometheus | fact-87cbf28d5326: kube_pod_container_status_waiting_reason=1, labels={container="app", reason="ContainerCreating"} | 佐证 Pod 处于等待状态，且原因与 K8s State 一致。 |

**证据说明：**
K8s Event 中 Multus 与 Kubelet 发出的 `NoNetworkFound` 和 `FailedCreatePodSandBox` 错误完全互为因果，指向同一个缺失资源。Metric 数据确认了该异常的持续性。由于 Pod 未能启动，Logging 和 Tracing 维度不可用。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义引用的 NetworkAttachmentDefinition `unavailable-network` 缺失 → Multus 插件无法获取网络配置 (getKubernetesDelegate 失败) → 导致 Kubelet 无法创建 Pod Sandbox (FailedCreatePodSandBox) → Pod 状态停留在 ContainerCreating
```

### 根因结论

**已确认的根因：**
Pod `workload-5dbb5dcd6c-nhd7v` 通过注解引用了一个名为 `unavailable-network` 的 NetworkAttachmentDefinition，但该资源在 `aiops-case-05` 命名空间中并不存在（事实 #2、#3）。这导致 Multus CNI 插件在尝试为 Pod 配置网络时抛出 `NoNetworkFound` 错误，进而引发 `FailedCreatePodSandBox`，使得 Pod 永远卡在 `ContainerCreating` 状态。

**证据不足项：**
缺失 `unavailable-network` 资源的确切期望定义内容（事实 #2 中的 unknowns），需人工确认该资源是否被误删、配置错误还是遗漏部署。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 23.7s
├─ 并发证据采集: 48.0s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 48.0s (Evidence 37.9s, RCA 9.9s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed, pod-sandbox-create-failed
