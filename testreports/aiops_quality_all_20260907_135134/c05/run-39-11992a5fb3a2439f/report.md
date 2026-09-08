## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-kbwsx` | ContainerCreating | Pod workload-5dbb5dcd6c-kbwsx 处于 Pending/ContainerCreating 状态，Pod IP 为空，无法建立网络连接 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning NoNetworkFound ... multus cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io "unavailable-network" not found` (持续 60 分钟) | 明确指向 Multus 插件因缺少网络定义对象而无法完成网络配置 |
| 2 | K8s State | kubernetes | `waiting_reason: "ContainerCreating"` | 证实 Pod 卡在启动阶段，未进入运行状态 |

**证据说明：**
Kubernetes 状态显示容器处于 `ContainerCreating` 等待状态。K8s Event 维度提供了决定性证据，多频次（46 次）出现的 `NoNetworkFound` 警告一致指向 `unavailable-network` 对象缺失，这与 Pod 卡在创建阶段的现象完全吻合。Metric 仅提供一个瞬时样本，缺乏趋势信息。Logging 和 Tracing 因 Pod 未启动而不可用，无法补充应用层信息。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 注解指定网络 'unavailable-network' → Multus CNI 在 aiops-case-05 命名空间找不到该定义对象 → 沙箱网络初始化失败 (FailedCreatePodSandBox) → Pod 保持 ContainerCreating 状态
```

### 根因结论

已确认的根因是 Pod 注解引用了不存在的 NetworkAttachmentDefinition 资源 `unavailable-network`（见证据 1）。这导致 Multus CNI 插件在尝试配置 Pod 网络时失败，直接引发 Pod 处于 `ContainerCreating` 状态（见证据 2）且无 IP 地址。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 24.1s
├─ 并发证据采集: 48.5s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx: 48.5s (Evidence 39.7s, RCA 8.6s)
└─ 汇总总结: 6.5s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-kbwsx**: pod-volume-mount-failed
