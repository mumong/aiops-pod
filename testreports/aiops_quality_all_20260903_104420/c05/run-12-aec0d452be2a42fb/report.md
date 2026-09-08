## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod workload-5dbb5dcd6c-nhd7v 卡在 ContainerCreating 状态，无法进入 Running。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `waiting_reason: ContainerCreating` (container: `app`) | 确认 Pod 停滞在启动阶段，处于等待资源就绪状态。 |
| 2 | K8s Event | Multus | `NoNetworkFound`: `cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05)` (频次: 46次，持续 24m) | 核心证据，直接指出 Pod 依赖的特定网络定义在指定 Namespace 中缺失。 |
| 3 | K8s Event | Kubelet | `FailedCreatePodSandBox`: `failed to setup network for sandbox ... plugin type="multus" ... GetNetworkDelegates: failed getting the delegate` (频次: 108次) | 确认沙箱创建失败的机制是 Multus CNI 插件未能获取到网络委托配置。 |

证据说明：Kubernetes 状态显示容器处于等待中（事实 1），而日志与事件明确指出等待原因是 Multus 插件找不到 `unavailable-network` 网络定义（事实 2）。这直接导致了 kubelet 反复尝试创建 Pod 沙箱失败（事实 3），形成了完整的因果闭环。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 注解引用不存在的 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 无法绑定网络资源 → Pod 沙箱创建失败 (FailedCreatePodSandBox) → Pod 状态停滞在 ContainerCreating
```

### 根因结论
已确认根因为 **Pod 配置了不存在的网络引用**。
具体而言，Pod `aiops-case-05/workload-5dbb5dcd6c-nhd7v` 的注解（或配置）要求 Multus 寻找名为 `unavailable-network` 的 `NetworkAttachmentDefinition` 资源，但该资源在 `aiops-case-05` 命名空间中不存在。这导致网络插件无法完成网络初始化，进而阻塞了 Pod 的启动（引用证据 2、3）。

根据输入事实，存在以下未确认的边界情况：
- 该网络定义是否存在于其他 Namespace？
- 该注解名称是否为拼写错误，应指向其他有效的网络定义？
- 是否应移除此注解以回退到默认网络？

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 15.2s
├─ 并发证据采集: 57.0s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 57.0s (Evidence 47.8s, RCA 9.0s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-volume-mount-failed
