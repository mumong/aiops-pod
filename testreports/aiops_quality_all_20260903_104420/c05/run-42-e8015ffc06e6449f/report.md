## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-nhd7v stuck in ContainerCreating/Pending, unable to start. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | multus | `Warning NoNetworkFound ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (46条记录, 跨度53m-6s) | 确认定性事实：Pod 依赖的 CNI 网络定义缺失，导致网络配置失败 |
| 2 | K8s Event | kubelet | `Warning FailedCreatePodSandBox ... Failed to create pod sandbox: plugin type="multus" ... cannot find a network-attachment-definition (unavailable-network) ... not found` | 确认最终失败机制：Kubelet 因 Multus 报错而中止 Sandbox 创建 |
| 3 | K8s State | kubernetes | `container.waiting_reason: ContainerCreating` | 描述 Pod 当前停滞状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"} = 1` | 辅助验证容器当前确实处于 Waiting 状态 |

**证据关联说明：**
*   事件 `fact-7037c3e0f269` (6s 前) 与 `fact-a75152bec1ea` (4m21s 前) 构成了完整的因果证据链：Multus 持续找不到 `unavailable-network` (Event 1) 直接导致 Kubelet 创建 Sandbox 失败 (Event 2)。
*   State 和 Metric 记录 (Row 3, 4) 一致表明 Pod 因上述网络配置错误一直停留在 `ContainerCreating` 阶段。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 注解引用了不存在的 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 找不到资源并抛出 NoNetworkFound 错误 → Kubelet 无法创建 Pod Sandbox (FailedCreatePodSandBox) → Pod 陷入 ContainerCreating/Pending 状态无法启动
```

### 根因结论

已确认根因为：Pod `workload-5dbb5dcd6c-nhd7v` 配置了 CNI 网络注解，要求使用名为 `unavailable-network` 的网络定义，但该资源在 `aiops-case-05` 命名空间中不存在（`network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found`）。这导致 Multus 插件初始化失败，进而使 kubelet 无法完成沙箱创建，引发持续等待（见证据 `fact-7037c3e0f269`、`fact-a75152bec1ea`、`fact-8b7bdab7a87b`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 19.6s
├─ 并发证据采集: 46.4s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 46.4s (Evidence 38.3s, RCA 7.9s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed, pod-imagepull-failed
