## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx 处于 ContainerCreating/Pending 状态，kubelet 反复尝试创建沙箱失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `ContainerCreating` (fact-ee4b730fee8b) | 确认 Pod 容器处于等待创建状态，未进入 Running 阶段 |
| 2 | K8s Event | kubelet | `FailedCreatePodSandBox`: failed to setup network for sandbox: plugin type="multus" ... failed (add) (fact-014122c0bcd6) | 提供底层网络插件调用失败的具体堆栈，指出是网络配置阶段阻断 |
| 3 | K8s Event | multus | `NoNetworkFound`: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found (fact-0e3d59857077) | 明确指出导致网络插件失败的直接原因是缺乏名为 `unavailable-network` 的 NAD 资源，并持续复现 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` (fact-239a6dc2c0c6) | 确认 Pod 等待状态，作为现象的指标侧佐证 |

**证据关联说明：**
事实 #2 确认失败发生在“网络插件”阶段，事实 #3 解释了该阶段失败的具体原因为“找不到指定名称的 NAD”。两者在因果链上形成闭环，确证网络配置是阻断 Pod 启动的唯一瓶颈。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 注解引用不存在的 NetworkAttachmentDefinition (unavailable-network) → Multus CNI 插件查找 NAD 失败 (NoNetworkFound) → kubelet 无法创建 Pod 沙箱 (FailedCreatePodSandBox) → Pod 状态卡在 ContainerCreating
```

### 根因结论

**已确认的根因：**
Pod `workload-5dbb5dcd6c-kbwsx` 的注解中引用了 NetworkAttachmentDefinition (NAD) 资源 `unavailable-network`，但该资源在 `aiops-case-05` 命名空间中不存在（事实 #3）。由于 Multus CNI 插件无法获取该网络定义，导致网络初始化失败，进而阻止 kubelet 创建 Pod 沙箱（事实 #2），最终使 Pod 无法启动。

**支持证据：**
*   K8s Event (fact-0e3d59857077)：Multus 直接报错无法找到 `unavailable-network`。
*   K8s Event (fact-014122c0bcd6)：kubelet 记录的网络插件初始化失败错误，且指向 Multus。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 17.3s
├─ 并发证据采集: 47.5s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 47.5s (Evidence 40.4s, RCA 6.9s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed
