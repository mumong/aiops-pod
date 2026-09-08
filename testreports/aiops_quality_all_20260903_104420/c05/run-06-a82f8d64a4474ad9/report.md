## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod 配置引用了不存在的 Multus NetworkAttachmentDefinition 'unavailable-network'，导致 kubelet 无法完成 Pod 沙箱网络初始化（SandboxCreateFailed）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | multus | `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` (fact-04bd71017ec1, fact-06f427b248a6) | 直接指出 Pod 引用的网络资源不存在，是网络初始化失败的根因线索 |
| 2 | K8s Event | kubelet | `Failed to create pod sandbox... failed to setup network for sandbox... plugin type="multus" ... cannot find a network-attachment-definition (unavailable-network) ... not found` (fact-0c56cacf4961) | 证实 kubelet 在启动 Pod 沙箱时因 Multus 插件找不到网络配置而中止，属于直接失败机制 |
| 3 | K8s Event | kubelet/multus | 46 条重复事件，其中 `FailedCreatePodSandBox` 与 `NoNetworkFound` 交替出现，时间跨度从 7m41s 至 63s (fact-04bd71017ec1 至 fact-fd0ff4318f02) | 确认该故障持续发生且未被重试恢复，状态为持续阻断 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason="ContainerCreating", fact-3fe75138fb43) | 佐证 Pod 处于创建等待阶段，未能进入运行状态 |

**证据小结：**
Kubernetes 事件 (fact-1, 2, 3) 清晰构建了“引用资源缺失 -> 插件报错 -> 沙箱创建失败”的因果链；Metrics (fact-4) 从状态维度印证了容器卡在 `ContainerCreating`。Logging 与 Tracing 均为不可用（日志维度说明“容器未启动，物理上不会产生应用日志或业务 Trace”），事实链闭合，无需补充其他维度。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 引用了不存在的 Multus NetworkAttachmentDefinition 'unavailable-network' (事实来源: K8s Event fact-1,2) 
→ Multus CNI 插件在执行 Add 时尝试获取 k8s delegates 失败，抛出 getKubernetesDelegate error (事实来源: K8s Event fact-2) 
→ kubelet 无法完成 Pod 沙箱网络初始化，触发 SandboxCreateFailed 并回滚 (事实来源: K8s Event fact-2) 
→ 容器始终处于 ContainerCreating 等待状态 (事实来源: Metric fact-4)
```

### 根因结论

**已确认的根因**：Pod 配置中引用的 Multus `NetworkAttachmentDefinition` 资源 `unavailable-network` 在命名空间 `aiops-case-05` 中不存在（证据编号：1, 2）。

该缺失导致 Multus 插件在 Pod 生命周期初期（Sandbox 创建阶段）立即报错，kubelet 因此无法完成网络插件的初始化步骤，直接导致 Pod 陷入 `ContainerCreating` 状态并持续产生 `FailedCreatePodSandBox` 事件。当前证据链（K8s Event + Metric）完整且一致，足以支持结论发布。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 26.7s
├─ 并发证据采集: 40.1s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 40.1s (Evidence 35.1s, RCA 4.8s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed, pod-imagepull-failed, pod-sandbox-create-failed
