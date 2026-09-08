## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-kbwsx stuck in ContainerCreating/Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: `ContainerCreating` | 确认 Pod 处于无法启动容器的停滞状态 |
| 2 | K8s Event | Kubernetes | `FailedCreatePodSandBox`: `Failed to create pod sandbox: ... plugin type="multus" ... failed: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 定位直接失败原因为 Multus CNI 插件未能找到网络配置 |
| 3 | K8s Event | Kubernetes | `NoNetworkFound` (累计 46 次): `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` | 证实 Pod 反复尝试加载名为 `unavailable-network` 的网络附件但始终失败 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason`: 1 (reason: `ContainerCreating`) | 指标状态印证了容器持续处于等待网络配置的原因 |

**证据说明：**
Pod 处于 `ContainerCreating` 等待状态（#1、#4），根本原因在于 Multus CNI 插件在创建沙箱时（#2）无法解析网络依赖。这一阻塞原因在长达 88 分钟的采集窗口内持续复发（#3），排除了瞬时网络抖动可能，确认为配置缺失导致的持续性故障。由于容器未能成功启动，日志与追踪数据不可用，Kubernetes 层面的状态与事件已成为判断根因的充分且唯一依据。

## 🎯 根因分析 · g1

### 因果链

```text
缺少 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 插件解析网络失败 → Pod 沙箱创建失败 (FailedCreatePodSandBox) → Pod 处于 ContainerCreating/Pending 状态
```

### 根因结论

**已确认根因：**
Pod `aiops-case-05/workload-5dbb5dcd6c-kbwsx` 启动失败是由于 Multus CNI 插件无法找到其配置中引用的网络附件定义（`network-attachment-definitions.k8s.cncf.io "unavailable-network"`）。该对象在 Pod 所在的 `aiops-case-05` 命名空间中不存在，导致网络插件执行失败并阻止容器启动（证据 #2、#3）。

**未确认事项：**
无法确定该网络定义（`unavailable-network`）是否本应存在于当前命名空间，还是应存在于其他命名空间，亦或是名称配置有误（如拼写错误或资源名不同）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 51.6s
├─ 并发证据采集: 44.1s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 44.1s (Evidence 36.0s, RCA 7.9s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-imagepull-failed, pod-volume-mount-failed
