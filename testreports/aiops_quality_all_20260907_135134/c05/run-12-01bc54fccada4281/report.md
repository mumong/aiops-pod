## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Multus CNI 无法在 namespace aiops-case-05 中找到名为 'unavailable-network' 的 NetworkAttachmentDefinition 资源，导致 Pod sandbox 创建失败并持续处于 ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Failed to create pod sandbox: ... failed to setup network for sandbox ... plugin type="multus" name="multus-cni-network" failed (add)` | 展示故障触发点：Pod 启动时 kubelet 尝试执行网络初始化时被 Multus 插件拒绝 |
| 2 | K8s Event | multus | `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found` | 揭示根本原因：Multus 在指定命名空间下无法找到 Pod 配置引用的 `unavailable-network` 资源 |
| 3 | K8s State | kubernetes | `ContainerCreating` (waiting_reason) | 确认故障持续状态，容器因上述网络创建失败而停滞在沙箱创建阶段 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` = 1 (reason: ContainerCreating) | 监控侧事实，证实 Pod 正在处于等待原因 `ContainerCreating` 状态，与 K8s 事件状态一致 |

**证据综合说明：**
- 指标（#4）证实了 Pod 处于 Waiting 状态，这与 K8s 事件（#1）中的 `FailedCreatePodSandBox` 直接对应。
- 所有网络错误均由 Multus 发出（#2），并一致指向特定资源名 `unavailable-network` 缺失，排除了其他 CNI 插件或网络策略干扰。

## 🎯 根因分析 · g1

### 因果链

```text
NetworkAttachmentDefinition 'unavailable-network' 在 aiops-case-05 缺失 → 容器创建时 Multus 插件查找失败 → kubelet 无法创建 Pod Sandbox → Pod 停滞于 ContainerCreating 状态
```

### 根因结论

已确认根因为**Pod 依赖的 Multus 网络附件定义（`unavailable-network`）在命名空间 `aiops-case-05` 中不存在**（证据 #2），该配置缺失直接导致 Multus CNI 插件在初始化网络时抛出“not found”异常（证据 #1），从而阻止了 Pod 沙箱的创建并维持了当前故障状态（证据 #3、#4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 17.3s
├─ 并发证据采集: 45.6s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 45.6s (Evidence 38.9s, RCA 6.6s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed, pod-imagepull-failed, pod-sandbox-create-failed
