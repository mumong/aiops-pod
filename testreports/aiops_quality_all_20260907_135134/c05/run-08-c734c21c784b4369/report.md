## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx 处于 Pending 状态，卡在 ContainerCreating 阶段，无法分配网络。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason` = `ContainerCreating` (`fact-0fa59b4ae6c4`) | 确认 Pod 处于等待状态，未进入 Running 阶段 |
| 2 | Metric | prometheus | `kube_pod_container_status_waiting_reason` value=1, labels: `container=app`, `reason=ContainerCreating` (`fact-9c77e3b4fd0a`) | 实时指标确认容器处于 `ContainerCreating` 等待态，佐证状态持久性 |
| 3 | K8s Event | kubelet | `FailedCreatePodSandBox`: `rpc error: ... failed to setup network for sandbox "...": ... cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (`fact-085db9e5e0fb`) | 直接记录底层 CNI 插件因缺失网络定义导致 Sandbox 创建失败的原因 |
| 4 | K8s Event | multus | `NoNetworkFound`: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (多次，e.g. `fact-0fe04ab99dac`, `fact-1c1727b4d5f0`) | 从 Multus 侧持续报出特定网络定义 `unavailable-network` 的查找失败错误 |

**证据关联分析：**
Kubernetes 的容器状态（事实 1）与 Prometheus 指标（事实 2）共同锁定了故障阶段为网络准备（ContainerCreating）。kubelet（事实 3）与 Multus（事实 4）的日志和事件高度一致，均明确指向同一个缺失对象 `network-attachment-definition (unavailable-network)`，证实了 Pod 因缺乏预期的 CNI 配置而无法启动网络沙箱。

## 🎯 根因分析 · g1

### 因果链

```text
命名空间 aiops-case-05 中缺少 'unavailable-network' NetworkAttachmentDefinition → Multus CNI 插件查找网络定义失败 → 无法创建 Pod 网络 Sandbox (FailedCreatePodSandBox) → Pod 状态卡在 ContainerCreating
```

### 根因结论

已确认的根因为：Pod 配置（注解或规范）中请求了一个名为 `unavailable-network` 的 Multus 网络附加定义，但该资源在 `aiops-case-05` 命名空间中不存在。

这一缺失导致 Multus CNI 插件在初始化容器网络时无法找到对应的网络定义，进而引发 `FailedCreatePodSandBox` 错误，使 Pod 始终无法完成网络配置并进入 `ContainerCreating` 状态（见事实 1、3、4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 33.6s
├─ 并发证据采集: 46.4s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 46.4s (Evidence 36.8s, RCA 9.3s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-sandbox-create-failed, pod-imagepull-failed, pod-volume-mount-failed
