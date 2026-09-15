## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod 配置引用了名为 'unavailable-network' 的 NetworkAttachmentDefinition，但该资源在 'aiops-case-05' 命名空间中不存在，导致 Multus CNI 插件无法初始化网络，Pod 陷入 Pending/ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | multus | `Warning NoNetworkFound ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (fact-0091ec74fdd5) | 确认为根因；明确指示 Multus 插件无法在目标命名空间找到名为 `unavailable-network` 的依赖资源。 |
| 2 | K8s Event | kubelet | `Warning FailedCreatePodSandBox ... failed to setup network for sandbox ... plugin type="multus" ... getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) ... not found` (fact-b4340515e874) | 确认为直接失败机制；Kubelet 因 Multus 初始化网络失败而拒绝创建 Pod 沙箱。 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 当前值 `ContainerCreating` (fact-427d8a60e06f) | 现象状态佐证；容器卡在等待阶段，验证了容器未正常启动的外部表现。 |

**证据说明**：
Kubernetes 事件 (fact-0091ec74fdd5, fact-b4340515e874) 与 Metric 状态 (fact-427d8a60e06f) 形成闭环：Multus 因找不到 `unavailable-network` 资源而报错导致 Pod 无法启动，Metric 捕捉到了 Pod 持续处于 `ContainerCreating` 状态的阻塞结果。由于容器未启动，Logging 和 Tracing 维度无数据，诊断完全依赖 K8s 控制层的事实。

## 🎯 根因分析 · g1

### 因果链

```text
缺少 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 插件网络初始化失败 → 容器沙箱创建拒绝 → Pod 陷入 ContainerCreating 状态
```

### 根因结论

已确认的根因为 Pod 配置错误引用了不存在的网络定义。Kubelet 在尝试创建容器沙箱时调用 Multus 插件，因 `network-attachment-definitions.k8s.cni.cncf.io "unavailable-network"` 在 `aiops-case-05` 命名空间中未找到而抛出错误 (fact-b4340515e874)，直接导致 Pod 处于 `ContainerCreating` 状态 (fact-427d8a60e06f)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 37.4s
├─ 并发证据采集: 29.0s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 29.0s (Evidence 22.5s, RCA 6.3s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed
