## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod workload-5dbb5dcd6c-nhd7v stuck in ContainerCreating/Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.waiting_reason: {"container": "app", "reason": "ContainerCreating"} | 确认容器状态停滞在初始化阶段，未进入运行态 |
| 2 | K8s Event | multus | "cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cncf.io \"unavailable-network\" not found" | 直接指出 Pod 引用了不存在的网络定义资源，导致 CNI 插件执行失败 |
| 3 | K8s Event | kubelet | "Failed to create pod sandbox ... failed to setup network for sandbox ... plugin type=\"multus\" ... Multus ... failed getting the delegate: getKubernetesDelegate: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05) ... not found" | 验证 Kubelet 因网络插件（Multus）返回失败而无法创建 Pod 沙箱 |

证据分析：
1. K8s 事件日志在 multus 和 kubelet 之间呈现完整的因果链条：multus 报告找不到定义，kubelet 因该原因失败；两维度事实高度一致，共同指向网络配置缺失。
2. 当前维度下 Metric、Logging 和 Tracing 均不适用或缺失：Metric 仅有 1 个样本且 trend_evaluable=false；Logging 和 Tracing 因容器未启动而无数据，无法提供额外诊断信息。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 引用的 NetworkAttachmentDefinition 'unavailable-network' 不存在于 'aiops-case-05' 命名空间 → Multus CNI 插件获取委托失败 → 网络配置无法完成，Pod 沙箱创建失败 → 容器长期卡在 ContainerCreating 状态
```

### 根因结论

**已确认的根因**：Pod `workload-5dbb5dcd6c-nhd7v` 的 YAML 配置引用了一个在命名空间 `aiops-case-05` 中不存在的网络定义（`network-attachment-definition` 名为 `unavailable-network`）。

**证据支撑**：
- 事件 `fact-037d4faa77e7` (Kubelet) 和 `fact-032e6c8bde9e` (Multus) 明确记录了相同的错误信息，证实 Multus 插件因找不到该定义而返回失败。
- 状态 `fact-1b833b17f66f` 证实 Pod 因此陷入了 ContainerCreating 的死循环。
- 缺少决定性的 YAML 快照事实以验证具体注解字段，但事件日志已足够确认为引用了不存在的资源。

---

## 📊 性能统计

```text
├─ 总耗时: 6.6m
├─ 问题定位: 32.2s
├─ 并发证据采集: 354.4s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 354.4s (Evidence 344.5s, RCA 9.5s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- 未调用 Runbook
