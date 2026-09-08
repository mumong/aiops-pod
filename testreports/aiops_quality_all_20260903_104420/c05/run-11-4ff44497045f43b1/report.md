## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-nhd7v 配置了 Multus CNI 注解 `k8s.v1.cni.cncf.io/networks: unavailable-network`，但在 `aiops-case-05` 命名空间下不存在对应的 NetworkAttachmentDefinition 资源。这导致 Kubelet/Multus 在创建容器沙箱时无法发现网络定义，触发了 `NoNetworkFound` 事件和 `FailedCreatePodSandBox` 失败，使 Pod 状态长期维持在 `Pending`，容器状态卡在 `ContainerCreating`。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: reason=`ContainerCreating` | 确认容器处于启动等待阶段，结合无日志/Tracing，指向基础设施配置或网络沙箱创建失败。 |
| 2 | K8s Event | multus | `NoNetworkFound`: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (连续出现约 11 分钟) | 直接揭示 Multus CNI 插件在寻找特定网络定义时失败。 |
| 3 | K8s Event | kubelet | `FailedCreatePodSandBox`: `Failed to create pod sandbox: ... plugin type="multus" ... failed (add): ... cannot find a network-attachment-definition (unavailable-network)` (23m 内累计 85 次) | 证明网络配置缺失导致容器沙箱创建直接报错，Pod 无法进入运行态。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"}`: 值为 `1` (样本数 1，趋势不可用) | 量化了当前处于等待状态的容器，与 K8s 事件时间窗口一致。 |

**证据印证说明：**
1. **指标与状态呼应**：Metric 显示容器持续处于 `ContainerCreating` 等待态（#4），这与 K8s 状态中 `ContainerCreating` 原因完全吻合（#1），排除了容器崩溃重启（CrashLoopBackOff）的可能性。
2. **事件构成因果闭环**：`multus` 发出的 `NoNetworkFound` 事件（#2）明确指出了缺失资源名称（`unavailable-network`），而 `kubelet` 的 `FailedCreatePodSandBox` 事件（#3）则是同一原因导致的直接执行结果，二者互为因果，完整解释了 Pod 为何卡在创建阶段。
3. **辅助数据限制**：因容器未能成功启动，Logging 和 Tracing 维度确实无业务日志或数据产出，进一步印证故障发生在启动前置阶段（CNI 网络挂载）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 包含指向不存在的 NetworkAttachmentDefinition 'unavailable-network' 的 Multus 注解 → 
Multus CNI 在命名空间内查找网络定义失败，触发 'NoNetworkFound' 事件 → 
Kubelet 无法获取网络配置，执行 'FailedCreatePodSandBox' 失败 → 
Pod 维持在 'Pending' 状态，容器卡在 'ContainerCreating'
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-05/workload-5dbb5dcd6c-nhd7v` 的 Spec 中配置了 Multus CNI 注解，要求使用名为 `unavailable-network` 的网络定义（见证据 #2、#3），但在对应的 `aiops-case-05` 命名空间下，该 `NetworkAttachmentDefinition` 资源实际并不存在。

该配置不一致导致 Multus CNI 插件在容器沙箱创建阶段无法解析网络配置，直接引发 `FailedCreatePodSandBox` 错误，从而使得 Pod 无法从 `Pending` 状态进入 `Running` 状态，容器长期卡在 `ContainerCreating`。证据链完整，无需更多补充。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 14.7s
├─ 并发证据采集: 41.2s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 41.2s (Evidence 32.1s, RCA 8.8s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed
