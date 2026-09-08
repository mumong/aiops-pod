## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx 处于 ContainerCreating 状态，无法完成 sandbox 创建，Pod 状态为 Pending。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | multus | `Warning  NoNetworkFound ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 明确指出 Multus CNI 无法在 `aiops-case-05` 命名空间中找到指定的 `unavailable-network` 网络定义，引发频繁警告。 |
| 2 | K8s Event | kubelet | `FailedCreatePodSandBox ... plugin type="multus" ... failed to setup network ... failed getting the delegate: getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network)` | 提供最终失败机制：kubelet 尝试调用 Multus 插件配置网络时因找不到定义而阻断 sandbox 创建。 |
| 3 | K8s State | kubernetes | `container.waiting_reason: "ContainerCreating"` (container: "app") | 反映 Pod 当前处于等待容器启动的状态，证实启动过程卡在沙箱创建阶段。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating", value="1"}` | 从监控侧确认容器因 `ContainerCreating` 状态被挂起，采样计数为 1，与事件状态一致。 |

**证据印证**：
K8s 事件提供了因果链条的完整细节：事件 #1 (NoNetworkFound) 确认了资源缺失的事实，事件 #2 (FailedCreatePodSandBox) 展示了该缺失如何直接导致 kubelet 失败。状态和指标（#3, #4）确认了这一故障的持续性和对外表现。

## 🎯 根因分析 · g1

### 因果链

```text
网络定义 'unavailable-network' 缺失 → Multus CNI 插件查找失败 (NoNetworkFound) → 容器运行时 sandbox 创建阻断 (FailedCreatePodSandBox) → Pod 滞留于 ContainerCreating 状态
```

### 根因结论

已确认根因为 **Multus CNI 插件因找不到预期的 NetworkAttachmentDefinition 而失败**。

Pod 规范中引用了名为 `unavailable-network` 的网络，但 Multus 插件在初始化容器网络时，在 `aiops-case-05` 命名空间中未能找到该 `network-attachment-definitions.k8s.cni.cncf.io` 资源。这一缺失导致 `kubelet` 无法配置容器网络沙箱，进而使 Pod 永久处于 `ContainerCreating` 状态，应用无法启动 [证据 1, 2, 3]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.9s
├─ 并发证据采集: 46.5s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 46.5s (Evidence 37.5s, RCA 8.9s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed
