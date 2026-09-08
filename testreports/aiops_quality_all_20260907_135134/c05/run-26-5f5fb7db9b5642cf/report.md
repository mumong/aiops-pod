## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx 卡在 ContainerCreating 状态，Sandbox 创建失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `ContainerCreating` (container: app) | 确认 Pod 处于启动阻塞阶段 |
| 2 | K8s Event | multus | `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 揭示 Multus 插件尝试查找指定网络配置但失败 |
| 3 | K8s Event | kubelet | `FailedCreatePodSandBox ... plugin type="multus" ... getKubernetesDelegate: cannot find a network-attachment-definition "unavailable-network" not found` | 确认 kubelet 因网络沙箱创建失败而终止 Pod 启动 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (reason: ContainerCreating) | 量化确认容器处于等待状态的单一指标观测 |

**证据关联说明：**
Kubernetes State 确认了阻塞现象，K8s Event (multus/kubelet) 提供了因果链上的完整错误信息，Metric 验证了该现象在监控维度的存在。日志与 Tracing 维度因容器未启动而无法采集，与现象逻辑一致。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了不存在的 NetworkAttachmentDefinition 'unavailable-network' → Multus 插件在节点查找网络定义失败 → kubelet 执行 FailedCreatePodSandBox 报错 → Pod 卡在 ContainerCreating 状态
```

### 根因结论

已确认的根因为：Pod 配置中引用了 `aiops-case-05` 命名空间下不存在的 NetworkAttachmentDefinition `unavailable-network`（证据 2, 3）。这一配置错误导致 Multus CNI 插件无法获取网络参数，进而触发 kubelet 沙箱创建失败，表现为 Pod 持续处于 `ContainerCreating` 状态（证据 1, 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.1s
├─ 并发证据采集: 43.0s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 43.0s (Evidence 33.4s, RCA 9.4s)
└─ 汇总总结: 7.2s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-sandbox-create-failed
