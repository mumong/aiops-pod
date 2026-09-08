## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod workload-5dbb5dcd6c-nhd7v is stuck in Pending state with container status ContainerCreating due to missing network attachment definition. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: ContainerCreating (container: app) | 确认 Pod 处于等待网络配置的停滞状态。 |
| 2 | K8s Event | kubernetes/multus | `NoNetworkFound`: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 明确指出 Multus CNI 无法找到 Pod 所需的网络配置资源。 |
| 3 | K8s Event | kubernetes/kubelet | `FailedCreatePodSandBox`: `failed to setup network for sandbox ... plugin type="multus" ... failed (add)` | 确认底层 kubelet 因网络插件失败而无法创建 Pod 沙箱。 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason: ContainerCreating, sample_count: 1) | 实时数据印证容器因网络问题持续处于等待状态。 |

**证据说明：**
Kubernetes 事件日志中高频出现的 `NoNetworkFound`（multus 组件）与 `FailedCreatePodSandBox`（kubelet 组件）形成因果闭环，直接指向网络配置缺失。Metric 监控提供了当前状态的实时快照，证实异常仍在持续。

## 🎯 根因分析 · g1

### 因果链

```text
缺少 NetworkAttachmentDefinition 资源 (namespace: aiops-case-05, name: unavailable-network) → Multus CNI 插件无法加载网络配置 → Kubelet 创建 Pod 沙箱 (sandbox) 失败 → Pod 陷入 ContainerCreating/Pending 状态
```

### 根因结论

根因已确认。Pod `workload-5dbb5dcd6c-nhd7v` 请求的网络附件 `unavailable-network` 对应的 `NetworkAttachmentDefinition` 资源在命名空间 `aiops-case-05` 中不存在。这一配置缺失导致 Multus CNI 报出 `NoNetworkFound` 错误，进而触发 kubelet 的 `FailedCreatePodSandBox` 机制，最终使容器无法进入运行状态（对应证据 #2 和 #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 20.1s
├─ 并发证据采集: 54.6s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 54.6s (Evidence 45.1s, RCA 9.4s)
└─ 汇总总结: 8.1s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed
