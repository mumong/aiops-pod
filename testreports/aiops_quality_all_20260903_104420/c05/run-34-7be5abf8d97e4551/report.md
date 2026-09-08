## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod `workload-5dbb5dcd6c-nhd7v` 的 `NetworkAttachmentDefinition` 资源 `unavailable-network` 在 `aiops-case-05` 命名空间中缺失，导致 Multus CNI 无法创建网络沙箱，Pod 持续卡在 ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | `container.waiting_reason` (container: `app`, reason: `ContainerCreating`) | 确认 Pod 处于挂起等待状态，且未能进入调度或启动阶段。 |
| 2 | K8s Event | `kubernetes` | `multus` 事件 `NoNetworkFound` (fact-0ae911c33873, fact-128d2a0736c2 等)：`cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` | 直接指出 Multus CNI 因找不到目标网络定义资源（NAD）而拒绝配置网络。 |
| 3 | K8s Event | `kubernetes` | `kubelet` 事件 `FailedCreatePodSandBox` (fact-741a7a8fe0ff)：`error loading k8s delegates... failed getting the delegate: getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network)...` | 证实网络初始化失败是导致 Pod Sandbox 无法创建的直接原因，与上述 NAD 缺失一致。 |
| 4 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason` (fact-0e43d678b753)：`reason=ContainerCreating` | 外部指标佐证容器处于 Waiting 状态，且未表现出资源不足等调度问题特征。 |

**证据互证**：
K8s 事件证据 (#2, #3) 与 K8s 状态 (#1) 形成完整闭环：Multus 明确报告缺少特定命名空间下的网络定义资源，导致容器沙箱创建失败，Pod 因此卡在 `ContainerCreating` 状态。Metric (#4) 从外部视角验证了这一长期挂起的异常状态。

## 🎯 根因分析 · g1

### 因果链

```text
namespace aiops-case-05 中缺失 NetworkAttachmentDefinition "unavailable-network" → Multus CNI 无法加载 Delegate 配置 → Pod 容器沙箱(Sandbox)创建失败(rpc error) → Pod 持续处于 ContainerCreating 状态等待网络就绪
```

### 根因结论

**已确认的根因**：Pod `workload-5dbb5dcd6c-nhd7v` 依赖的 `NetworkAttachmentDefinition` 资源 `unavailable-network` 在 `aiops-case-05` 命名空间中不存在。
- **影响机制**：Multus CNI 在尝试为 Pod 配置网络时，试图引用该 NAD 资源，但查询失败（`not found`）。这导致网络初始化流程阻断，进而使得 kubelet 无法创建 Pod 的 Sandbox。
- **证据支持**：
  - 持续触发的 `NoNetworkFound` 警告事件（如事实 #2），明确指出 `network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found`。
  - `FailedCreatePodSandBox` 错误事件（事实 #3），确认了网络插件失败是导致沙箱创建异常的根因。
  - 容器状态显示原因为 `ContainerCreating`（事实 #1），排除了应用启动失败的可能性，定位为基础设施配置缺失。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 33.8s
├─ 并发证据采集: 48.1s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 48.1s (Evidence 41.8s, RCA 6.2s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-imagepull-failed, pod-volume-mount-failed
