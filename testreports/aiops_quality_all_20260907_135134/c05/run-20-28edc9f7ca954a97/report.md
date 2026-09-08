## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx in aiops-case-05 is stuck in Pending/ContainerCreating state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | multus | `Warning NoNetworkFound ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` | 明确指出 Multus CNI 在 aiops-case-05 命名空间中找不到所需的网络依赖 `unavailable-network`，这是导致 Pod 停滞的源头信息 |
| 2 | K8s Event | kubelet | `Warning FailedCreatePodSandBox ... failed to setup network for sandbox ... plugin type="multus" ... failed (add): Multus: ... GetNetworkDelegates: failed getting the delegate ... not found` | 证实 kubelet 因网络插件失败导致容器沙箱创建被拒，直接阻断了容器启动流程 |
| 3 | K8s State | kubernetes | `ContainerCreating` (container: app) | 确认当前 Pod 处于等待网络就绪的停滞状态，未进入运行期 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason {container="app", reason="ContainerCreating"} = 1` (sample_count=1) | 提供量化观测，确认单副本容器因 `ContainerCreating` 原因处于等待状态 |

**证据关联：**
K8s Event (Multus) 提供了直接故障原因（找不到 NAD），K8s Event (Kubelet) 证实了该原因引发的直接后果（沙箱创建失败），K8s State 和 Metric 共同描述了这种机制导致的具体停滞现状。

## 🎯 根因分析 · g1

### 因果链

```text
NetworkAttachmentDefinition 'unavailable-network' 缺失 → Multus CNI 无法解析网络配置导致沙箱初始化失败 → 容器无法创建网络环境 → Pod 卡在 ContainerCreating/Pending 状态
```

### 根因结论

已确认的根因：集群中 `aiops-case-05` 命名空间下缺少 Multus CNI 所需的 `NetworkAttachmentDefinition` 资源 `unavailable-network`（证据 1、2）。由于该关键依赖缺失，Multus 插件无法完成网络绑定，导致 kubelet 拒绝创建 Pod 沙箱（证据 2），最终使 Pod 陷入 `ContainerCreating` 状态无法启动（证据 3、4）。缺失的决定性事实为：该 NetworkAttachmentDefinition 是意外被删除还是从未被正确创建。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 53.8s
├─ 并发证据采集: 42.1s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 42.1s (Evidence 33.0s, RCA 9.0s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-sandbox-create-failed, pod-volume-mount-failed, pod-imagepull-failed
