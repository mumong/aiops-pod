## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod workload-5dbb5dcd6c-nhd7v 在 aiops-case-05 namespace 中处于 ContainerCreating/Pending 状态，无法启动应用容器。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | multus | `NoNetworkFound`：`cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` | 确认 Multus 插件因无法找到名为 `unavailable-network` 的资源而持续报错 |
| 2 | K8s Event | kubelet | `FailedCreatePodSandBox`：`Failed to create pod sandbox: ... failed to setup network ... plugin type="multus" ... getKubernetesDelegate: cannot find a network-attachment-definition` | 确认底层沙箱创建失败的直接原因是 Multus CNI 获取网络定义失败 |
| 3 | K8s State | kubelet | `ContainerCreating` 状态 (`reason: ContainerCreating`, fact_id: `fact-dda7be276f69`) | 描述 Pod 当前的异常停滞状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` 值为 `1`，标签 `reason="ContainerCreating"` | 验证 Pod 处于等待状态，且持续时间长（覆盖 73 分钟，event x334） |

**证据说明：**
Kubernetes 事件 (fact-01899a9eafc2, fact-8fda19dcbafa) 与状态 (fact-dda7be276f69) 高度一致，明确指向因特定的 `NetworkAttachmentDefinition` 缺失导致网络配置阶段阻塞。Metric (fact-d7e09b31d448) 进一步印证了该等待状态的持续性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置引用了不存在的 NetworkAttachmentDefinition 'unavailable-network' 
→ Multus CNI 插件在节点上查找网络定义失败 (getKubernetesDelegate) 
→ Kubelet 触发 FailedCreatePodSandBox 与 NoNetworkFound 事件 
→ Pod 卡在 ContainerCreating 状态，容器未启动
```

### 根因结论

已确认的根因是 Pod 配置中引用的 `NetworkAttachmentDefinition` 资源 `unavailable-network` 在 `aiops-case-05` 命名空间中不存在（证据 1、2）。这导致 Multus 插件无法完成网络挂载，进而使 Kubelet 无法创建 Pod 沙箱，表现为 Pod 长期处于 `ContainerCreating` 状态（证据 3、4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 19.5s
├─ 并发证据采集: 66.7s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 66.7s (Evidence 57.0s, RCA 9.6s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed
