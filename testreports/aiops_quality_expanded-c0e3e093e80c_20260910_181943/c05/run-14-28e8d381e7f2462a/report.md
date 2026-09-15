## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod workload-5dbb5dcd6c-bntfh 持续处于 Pending/ContainerCreating 状态，无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: container="app", reason="ContainerCreating" [fact-e4c01553e66f] | 确证 Pod 容器当前卡在等待创建状态 |
| 2 | K8s Event | kubernetes (multus) | `NoNetworkFound`: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05) [fact-0b86e188ca66] | 暴露 Pod 尝试加载未定义的 CNI 网络资源 |
| 3 | K8s Event | kubernetes (kubelet) | `FailedCreatePodSandBox`: failed to setup network... Multus: cannot find a network-attachment-definition (unavailable-network) [fact-50c33b676294] | 确认因 Multus 插件查找失败导致 Kubelet 无法创建沙箱 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: reason="ContainerCreating", value=1 [fact-f21253dcf04a] | 独立验证 Pod 当前等待状态 |

**证据综述：**
1. Prometheus 监控事实（#4）与 Kubernetes 事件事实（#2, #3）共同印证了 Pod 持续处于 `ContainerCreating` 状态（#1）。
2. Kubernetes 事件（#2, #3）明确指出了阻碍 Pod 启动的直接原因为 Multus 插件在 `aiops-case-05` 命名空间中找不到 `unavailable-network` 定义，且该错误在 29 分钟内高频复现。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 注解引用不存在的 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 插件执行失败 → Kubelet 无法创建 Pod 沙箱 → Pod 卡在 ContainerCreating 状态
```

### 根因结论

已确认的根因是 **Pod 注解引用了不存在的 NetworkAttachmentDefinition 资源** `unavailable-network`。

1.  Pod `workload-5dbb5dcd6c-bntfh` 通过 `k8s.v1.cni.cncf.io/networks` 注解配置了网络依赖。
2.  在尝试启动容器时，Multus CNI 插件在 `aiops-case-05` 命名空间中查找该定义失败 [fact-0b86e188ca66]。
3.  这一失败直接导致 Kubelet 无法完成 Pod 网络沙箱的创建工作 [fact-50c33b676294]，进而使 Pod 一直处于 `ContainerCreating` 状态 [fact-e4c01553e66f] [fact-f21253dcf04a]。

现有证据已构成完整闭环。缺失事实仅涉及业务意图（即是否应补建该网络定义或移除注解），不影响当前故障现象的诊断。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 18.1s
├─ 并发证据采集: 67.1s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 67.1s (Evidence 57.3s, RCA 9.6s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-sandbox-create-failed
