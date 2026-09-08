## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod workload-5dbb5dcd6c-nhd7v 卡在 ContainerCreating 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning NoNetworkFound ... multus cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` (fact-0d93ea823c40) | 持续报错，直接证明 Multus 找不到所需的网络配置，导致网络初始化失败。 |
| 2 | K8s Event | Kubernetes | `Warning FailedCreatePodSandBox ... kubelet ... failed to setup network for sandbox ... plugin type="multus" ... error loading k8s delegates ... cannot find a network-attachment-definition (unavailable-network)` (fact-d42bbf241a5f) | 提供底层因果关系：因为找不到网络定义（呼应证据 1），导致 Kubelet 无法创建 Pod 沙箱。 |
| 3 | K8s State | Kubernetes | `ContainerCreating` (fact-8c29fb4a2c53) | 确认 Pod 停滞在启动阶段，尚未进入运行状态。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"}` = 1 (fact-d10439a0c600) | 独立量化验证了 Pod 处于 `ContainerCreating` 等待状态。 |

**证据印证说明：**
Kubernetes 状态显示 Pod 卡在 `ContainerCreating`，Metric 证实了该状态的量化存在。Kubernetes 事件（证据 1、2）提供了明确的因果链：由于缺少网络定义 `unavailable-network`，导致 Multus CNI 插件失败，进而阻止了沙箱创建。日志与追踪数据因容器未启动而缺失，属于物理限制，不影响本次基于控制面事实的诊断。

## 🎯 根因分析 · g1

### 因果链

```text
Multus NetworkAttachmentDefinition 'unavailable-network' 缺失 → Multus CNI 插件网络配置失败 → Kubelet 无法创建 Pod Sandbox → Pod 状态停滞在 ContainerCreating
```

### 根因结论

已确认的根因是 Pod `workload-5dbb5dcd6c-nhd7v` 引用的 Multus 网络定义 `unavailable-network` 在命名空间 `aiops-case-05` 中不存在（证据 1、2）。这一配置缺失导致网络插件初始化失败，直接阻止了 Pod Sandbox 的创建，从而导致容器状态持续停留在 `ContainerCreating`（证据 3、4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 25.0s
├─ 并发证据采集: 49.8s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 49.8s (Evidence 42.2s, RCA 7.4s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed
