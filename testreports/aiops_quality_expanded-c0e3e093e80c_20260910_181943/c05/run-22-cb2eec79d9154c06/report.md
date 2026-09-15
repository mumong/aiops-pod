## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-bntfh 的 annotation 中引用了不存在的 NetworkAttachmentDefinition 'unavailable-network'，导致 Multus CNI 插件无法找到网络配置，容器沙箱创建失败（FailedCreatePodSandBox）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | K8s Event | `failed getting the delegate: getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` ([fact-1156c3029503]) | 确立根本故障点：Multus 在加载网络配置时无法定位到预期的 `NetworkAttachmentDefinition` 资源。 |
| 2 | K8s Event | K8s Event | `Failed to create pod sandbox: ... failed to setup network for sandbox ... plugin type="multus" name="multus-cni-network" failed (add)` ([fact-118aa0eb448a]) | 确立业务后果：因网络插件调用失败，导致容器沙箱创建彻底终止，阻碍 Pod 进入运行状态。 |
| 3 | Metric | Prometheus | `kube_pod_container_status_waiting_reason=1` (reason="ContainerCreating") ([fact-fcce626cd72c]) | 量化确认 Pod 正处于等待网络配置解决的初始化阻塞状态。 |

**证据互证说明：**
事实 1 明确指出 `multus` 插件报错无法找到 `unavailable-network` 定义；事实 2 证实该错误直接导致了 `FailedCreatePodSandBox`；事实 3 确认 Pod 因该原因处于 `ContainerCreating` 的持续等待中。三类证据链闭环，明确指向网络配置缺失导致的沙箱创建失败。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 注解引用了不存在的网络资源 (unavailable-network) → Multus CNI 插件查找并失败 (NoNetworkFound) → 容器沙箱网络配置失败 (FailedCreatePodSandBox) → Pod 阻塞在 ContainerCreating 状态
```

### 根因结论

**已确认根因：**
Pod `aiops-case-05/workload-5dbb5dcd6c-bntfh` 的注解配置中引用了一个名为 `unavailable-network` 的 `NetworkAttachmentDefinition` 资源，但该资源在 `aiops-case-05` 命名空间中实际上不存在。这一配置错误导致 Multus CNI 插件在尝试为 Pod 创建网络环境时失败，直接引发 `FailedCreatePodSandBox` 错误，使 Pod 无法脱离 `ContainerCreating` 状态。详见证据编号 `[fact-1156c3029503]`。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 38.7s
├─ 并发证据采集: 26.6s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 26.6s (Evidence 21.8s, RCA 4.6s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-volume-mount-failed
