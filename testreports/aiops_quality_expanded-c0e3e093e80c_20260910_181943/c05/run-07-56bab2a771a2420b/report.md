## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod缺少多网卡插件(Multus CNI)依赖的NetworkAttachmentDefinition资源' unavailable-network' |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `NoNetworkFound`: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found (fact-0573f5e62105) | 直接证明 Pod 引用了不存在的 NetworkAttachmentDefinition |
| 2 | K8s Event | Kubernetes | `FailedCreatePodSandBox`: rpc error: code = Unknown desc = failed to setup network for sandbox: plugin type="multus" ... failed (add) ... cannot find a network-attachment-definition (unavailable-network) (fact-2e1065429b99) | 确认网络插件初始化失败是导致 Sandbox 创建失败的直接原因 |
| 3 | K8s State | Kubernetes | `container.waiting_reason`: ContainerCreating (fact-3d2495de26ac) | 确认容器当前处于等待网络配置就绪的阻塞状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason`=1, reason="ContainerCreating" (fact-fa7dd8557975) | 确认等待状态是当前唯一状态，且未发生回落 |

Kubernetes 状态（证据 3）与 Metric（证据 4）相互印证，表明 Pod 长期停滞在创建阶段。Kubernetes 事件（证据 1、2）详细指出了停滞的具体机制：Multus 插件在尝试加载 Delegate 时找不到名为 `unavailable-network` 的 CRD 资源，这与 `diagnosis` 中描述的现象完全一致。Logging 和 Tracing 维度因容器未启动无法获取数据，符合预期。

## 🎯 根因分析 · g1

### 因果链

```text
未创建 CRD 资源 unavailable-network → Multus CNI 插件无法获取网络 Delegate → Pod Sandbox 创建失败 → 容器处于 ContainerCreating 等待状态
```

### 根因结论

**已确认根因**：
Pod `aiops-case-05/workload-5dbb5dcd6c-bntfh` 配置了依赖 Multus CNI 的网络插件，并引用了名为 `unavailable-network` 的 `NetworkAttachmentDefinition` 资源。Kubernetes 集群中 `aiops-case-05` 命名空间下不存在该资源，导致 Multus 插件在初始化网络时抛出 `NoNetworkFound` 错误，进而致使 Pod Sandbox 创建失败（证据 1、2），Pod 持续处于 `ContainerCreating` 状态（证据 3、4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 18.8s
├─ 并发证据采集: 59.5s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 59.5s (Evidence 54.2s, RCA 5.1s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed, pod-sandbox-create-failed, pod-imagepull-failed
