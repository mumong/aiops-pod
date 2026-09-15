## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod 通过 annotation k8s.v1.cni.cncf.io/networks 声明了网络依赖 'unavailable-network'，但 namespace aiops-case-05 中不存在对应的 NetworkAttachmentDefinition 资源，导致 Multus CNI 插件无法找到网络配置，进而使 kubelet 在创建 Pod Sandbox 时失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `ContainerCreating` (container `app`) | 确认目标容器 `app` 处于等待状态，未进入运行阶段 |
| 2 | K8s Event | kubelet | `Failed to create pod sandbox: ... failed to setup network for sandbox ... plugin type="multus" ... failed (add)` | 指出 `kubelet` 在尝试创建 Pod Sandbox 时，因网络插件 `multus` 执行失败而回滚 |
| 3 | K8s Event | multus | `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` | 明确失败原因：Multus 插件在 `aiops-case-05` 命名空间中查找名为 `unavailable-network` 的网络定义资源时返回 404 未找到 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1 (`ContainerCreating`) | 量化证实容器因上述原因长时间处于等待状态 |

**证据关联说明：**
证据 2 与证据 3 共同构成了完整的因果链条：证据 2 展示了 `kubelet` 调用 `multus` 插件失败的宏观结果，而证据 3 精确指出了 `multus` 失败的具体原因是“找不到名为 `unavailable-network` 的 NetworkAttachmentDefinition”。证据 1 的状态与证据 4 的监控指标相互印证，表明该配置缺失是一个持续存在的阻断性故障。

## 🎯 根因分析 · g1

### 因果链

```text
未声明 NetworkAttachmentDefinition 资源 (unavailable-network) → Multus 插件查找失败 (not found) → 网络配置初始化阻塞 → Pod Sandbox 创建回滚 → 容器处于 ContainerCreating 状态
```

### 根因结论

已确认根因为 **配置引用缺失**。
Pod 的 annotation `k8s.v1.cni.cncf.io/networks` 声明依赖名为 `unavailable-network` 的网络，但该依赖对应的 Kubernetes 自定义资源 `NetworkAttachmentDefinition` 在 `aiops-case-05` 命名空间中不存在（见证据 #3）。这导致 CNI 插件 Multus 无法注入网络环境，进而致使 `kubelet` 无法完成 Sandbox 创建，最终 Pod 长期停留在 `ContainerCreating` 状态（见证据 #1, #2）。

未知因素：该 `NetworkAttachmentDefinition` 资源是配置遗漏、拼写错误导致，还是已被意外删除，当前证据不足以区分。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 27.6s
├─ 并发证据采集: 39.6s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 39.6s (Evidence 31.6s, RCA 7.8s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-imagepull-failed, pod-volume-mount-failed, pod-sandbox-create-failed
