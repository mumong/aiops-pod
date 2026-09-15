## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod workload-5dbb5dcd6c-bntfh stuck in ContainerCreating phase |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason` = "ContainerCreating" | 确认 Pod 当前卡在前端状态，容器未启动 |
| 2 | K8s Event | kubernetes | `FailedCreatePodSandBox` (fact-42d73004d0d0): `rpc error: code = Unknown desc = failed to setup network for sandbox ... plugin type="multus" ... error loading k8s delegates ... getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` | 直接指出 kubelet 调用 Multus 创建网络时，因找不到定义的网络资源而失败 |
| 3 | K8s Event | kubernetes | `NoNetworkFound` (fact-010b07d1deaf): `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 持续出现的警告事件，确认 Multus 插件在多个重试周期内均无法定位目标网络 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1, reason="ContainerCreating" (fact-c4c16bab67f8) | 量化验证了 Pod 处于等待状态且未被调度至运行 |

证据表明，Pod 处于 `ContainerCreating` 状态是 kubelet 无法成功配置网络沙箱的直接结果。Kubernetes 事件记录显示，在 Pod 创建及多次重试过程中，Multus CNI 插件均因在 `aiops-case-05` 命名空间中找不到名为 `unavailable-network` 的 `NetworkAttachmentDefinition` 而报错（`NoNetworkFound` 与 `FailedCreatePodSandBox` 事件）。这一配置缺失导致网络插件链中断，进而阻碍了容器的启动。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 引用不存在的 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 插件在命名空间 aiops-case-05 中找不到该定义 → Pod 网络沙箱创建失败 (FailedCreatePodSandBox) → 容器保持 ContainerCreating 状态
```

### 根因结论

已确认的根因为：Pod 配置了引用 `unavailable-network` 的网络注解，但该网络资源在 `aiops-case-05` 命名空间中不存在。

证据编号 2 和 3 明确指出 Multus 插件在尝试加载 k8s 委托网络时，因找不到名为 `unavailable-network` 的 `network-attachment-definitions.k8s.cncf.io` 资源而报错，进而导致 `FailedCreatePodSandBox`，使 Pod 无法进入运行状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 31.6s
├─ 并发证据采集: 47.9s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 47.9s (Evidence 38.6s, RCA 9.1s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-imagepull-failed, pod-volume-mount-failed
