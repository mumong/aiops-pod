## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod workload-5dbb5dcd6c-nhd7v 在 aiops-case-05 命名空间中处于 ContainerCreating / Pending 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | multus (fact-055ac61c33be) | `Warning NoNetworkFound` `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` | 直接证明 Multus 插件在查找指定网络定义时失败 |
| 2 | K8s Event | kubelet (fact-0d4c479f81bd) | `Warning FailedCreatePodSandBox` `failed setup network for sandbox ... plugin type="multus" ... error loading k8s delegates ... failed getting the delegate: getKubernetesDelegate: cannot find a network-attachment-definition` | 确认底层容器运行时因网络插件报错导致 Pod Sandbox 创建失败 |
| 3 | K8s State | kubernetes (fact-0d950d883735) | `reason: ContainerCreating` (container: app) | 确认 Pod 卡在容器创建阶段的实际状态 |
| 4 | Metric | Prometheus (fact-efc905ed1853) | `kube_pod_container_status_waiting_reason=1` (labels: reason=ContainerCreating) | 指标数据与 K8s 事件现象一致，确认容器处于等待态 |

**证据说明：**
Kubernetes 事件（证据 1, 2）一致指出失败原因为 `NoNetworkFound`，具体为 Multus 插件无法在 `aiops-case-05` 命名空间中找到名为 `unavailable-network` 的 NetworkAttachmentDefinition。这一网络配置错误直接导致 kubelet 无法创建 Pod 沙箱（证据 2），从而使 Pod 停留在 ContainerCreating 状态（证据 3），与 Prometheus 指标（证据 4）反映的状态完全吻合。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 包含指向 'unavailable-network' 的 CNI 注解 → Multus 插件在指定命名空间内未找到对应的 NetworkAttachmentDefinition 定义 → kubelet 报告 NoNetworkFound 错误并终止 PodSandbox 创建 → Pod 卡在 ContainerCreating / Pending 状态
```

### 根因结论

**已确认的根因：**
Pod `workload-5dbb5dcd6c-nhd7v` 通过 Multus CNI 注解引用了一个不存在的网络定义资源（`unavailable-network`）。由于该资源在 `aiops-case-05` 命名空间中不存在，Multus 插件无法完成网络插件链的加载与附加，进而导致 kubelet 无法创建 Pod 沙箱，最终使 Pod 无限期卡在 `ContainerCreating` 状态。

**支撑证据：**
- **K8s Event (fact-055ac61c33be, fact-0d4c479f81bd)**：重复记录的 `NoNetworkFound` 警告和 `FailedCreatePodSandBox` 错误明确指出了缺失的资源名称和失败的具体位置。
- **K8s State (fact-0d950d883735)**：状态 `ContainerCreating` 与网络创建失败的机制相符。
- **Metric (fact-efc905ed1853)**：等待原因 `ContainerCreating` 佐证了上述状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 26.9s
├─ 并发证据采集: 40.6s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 40.6s (Evidence 33.0s, RCA 7.3s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed
