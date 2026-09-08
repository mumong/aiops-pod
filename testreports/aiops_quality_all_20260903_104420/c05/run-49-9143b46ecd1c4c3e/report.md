## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod workload-5dbb5dcd6c-nhd7v 处于 Pending/ContainerCreating 状态，未恢复 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.waiting_reason`: `ContainerCreating` | 确认 Pod 当前处于因配置或资源问题导致的容器创建等待状态。 |
| 2 | K8s Event | Multus | `Warning NoNetworkFound` ... `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` | 明确报错为 Multus CNI 插件在指定命名空间下找不到名为 `unavailable-network` 的网络附加定义资源。 |
| 3 | K8s Event | Kubelet | `Warning FailedCreatePodSandBox` ... `failed to setup network for sandbox ... plugin type="multus" ... error loading k8s delegates` | 确认底层沙箱创建失败的具体机制为 Multus 插件无法解析并加载 Pod 代理网络配置。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"}` = `1` | 确认容器状态为 `ContainerCreating` 持续存在（单样本，未消除）。 |

**证据说明：**
Kubernetes 事件（证据 #2, #3）与状态指标（证据 #1, #4）高度一致，均指向同一个失败链条。事件 #2 提供了具体缺失的资源名称 `unavailable-network`，事件 #3 证实了该缺失直接导致了 `FailedCreatePodSandBox`，从而使得 Pod 停留在 `ContainerCreating` 状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 注解引用不存在的 NetworkAttachmentDefinition 'unavailable-network' 
→ Multus CNI 插件尝试加载该网络定义失败 
→ Kubelet 创建 Pod 沙箱时因网络配置错误被 Multus 拒绝 
→ Pod 卡在 ContainerCreating 状态且触发 FailedCreatePodSandBox 告警
```

### 根因结论

**已确认根因：Pod 引用了不存在的网络附加定义（NetworkAttachmentDefinition）。**

Pod `workload-5dbb5dcd6c-nhd7v` 的 YAML 配置中声明了 Multus 注解，要求使用名为 `unavailable-network` 的网络定义，但在 `aiops-case-05` 命名空间中该资源不存在（证据 #2）。这导致 Multus CNI 插件无法获取网络配置，进而引发 kubelet 反复创建沙箱失败（证据 #3），最终造成 Pod 处于 `ContainerCreating` 等待状态（证据 #1, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 28.8s
├─ 并发证据采集: 46.6s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 46.6s (Evidence 38.7s, RCA 7.8s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed
