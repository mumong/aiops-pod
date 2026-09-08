## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx stuck in ContainerCreating/Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Container 'app' waiting_reason: `ContainerCreating` [fact-30053d5ca3f6] | 描述 Pod 卡滞的最终状态 |
| 2 | K8s Event | multus | Repeated warnings: `NoNetworkFound`: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` [fact-001b172c1350, fact-0793c00e34d9, 共46条] | 核心错误事件：Multus 尝试查找 Pod 引用的 `unavailable-network` 时失败 |
| 3 | K8s Event | kubelet | `FailedCreatePodSandBox`: `rpc error... Multus... failed getting the delegate: ... cannot find a network-attachment-definition (unavailable-network)` [fact-1add590034a8, fact-28702b73e8c4, 共8次] | 辅助错误事件：底层容器运行时因网络插件报错而放弃创建沙箱 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = `1` (reason: `ContainerCreating`, labels: `container: app`, samples: 1) [fact-7e81a475f598] | 验证容器确实处于等待状态，仅单点样本确认 |

证据说明：
Kubernetes State 与 Metric 确认了容器因网络配置缺失而卡滞在 `ContainerCreating` 状态。多组 `K8s Event` 直接指出了根本原因：Multus 插件试图处理 Pod 的 CNI 网络需求时，发现 Pod 在 `aiops-case-05` 命名空间下引用的 `NetworkAttachmentDefinition` 资源 `unavailable-network` 根本不存在（`not found`），导致 kubelet 无法创建 Pod Sandbox。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 的 annotation 引用了不存在的 NetworkAttachmentDefinition 'unavailable-network'
  →
Multus CNI 插件无法在命名空间 aiops-case-05 中找到该网络定义资源
  →
Pod Sandbox 创建失败 (FailedCreatePodSandBox) 并持续返回 NoNetworkFound 警告
  →
容器 app 卡滞于 ContainerCreating 状态
```

### 根因结论

已确认的根因是：Pod `aiops-case-05/workload-5dbb5dcd6c-kbwsx` 的配置中引用了一个名为 `unavailable-network` 的网络附件定义（`NetworkAttachmentDefinition`），但该资源在目标命名空间 `aiops-case-05` 中并不存在。这一配置错误导致 Multus CNI 插件无法分配网络，引发 `FailedCreatePodSandBox` 错误，使 Pod 无法进入运行状态（证据：[fact-001b172c1350], [fact-1add590034a8]）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 16.0s
├─ 并发证据采集: 48.9s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 48.9s (Evidence 41.6s, RCA 7.2s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed, pod-imagepull-failed
