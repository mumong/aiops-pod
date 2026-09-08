## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx (aiops-case-05) stuck in ContainerCreating/Pending state; kubelet FailedCreatePodSandBox errors due to Multus CNI failure. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | multus | `Warning NoNetworkFound ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (fact-05a0792bb99d) | 明确指出 Multus 在 `aiops-case-05` 命名空间中找不到名为 `unavailable-network` 的网络附件定义。 |
| 2 | K8s Event | kubelet | `Warning FailedCreatePodSandBox ... Failed to create pod sandbox: rpc error ... plugin type="multus" ... failed (add)` (fact-2bc04167ce3f) | 直接证据，kubelet 因 Multus 网络插件配置失败而无法创建 Pod 沙箱。 |
| 3 | K8s State | kubernetes | `container: "app", reason: "ContainerCreating"` (fact-8d883e50ad91) | 确认 Pod 处于创建中状态，等待网络或其他资源就绪。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值为 `1`，标签 `reason="ContainerCreating"` (fact-a9ecf2b39af6) | 从指标层面验证 Pod 卡在 `ContainerCreating` 状态，与事件状态一致。 |

上述事件证据显示，Multus 插件多次报告找不到 `unavailable-network` 网络配置，导致 kubelet 无法创建 Pod 沙箱。指标进一步证实了容器持续处于等待创建状态。两者共同指向网络配置缺失导致的启动阻塞。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 注解引用了不存在的 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 插件在命名空间 'aiops-case-05' 中查找代理失败 → Kubelet 无法创建 Pod 沙箱（FailedCreatePodSandBox） → Pod 停留在 ContainerCreating 状态
```

### 根因结论

已确认根因为：Pod 的注解引用了名为 `unavailable-network` 的 `NetworkAttachmentDefinition` 资源，但该资源在 `aiops-case-05` 命名空间中不存在。

这一缺失导致 Multus CNI 插件在执行网络配置时无法找到对应的代理，进而引发 `FailedCreatePodSandBox` 错误，最终使 Pod 无法进入运行状态。证据编号 1、2、3 均直接支持这一结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 24.7s
├─ 并发证据采集: 45.9s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 45.9s (Evidence 36.2s, RCA 9.6s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed, pod-sandbox-create-failed
