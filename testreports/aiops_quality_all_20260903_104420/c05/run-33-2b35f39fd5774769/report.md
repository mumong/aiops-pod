## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-nhd7v` | ContainerCreating | Pod workload-5dbb5dcd6c-nhd7v stuck in ContainerCreating/Pending state |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.waiting_reason: app = ContainerCreating | 确认容器运行处于停滞状态，未启动 |
| 2 | K8s Event | multus (kubernetes) | NoNetworkFound: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05): network-attachment-definitions.k8s.cni.cncf.io "unavailable-network" not found (fact-022d727dba15) | 直接归因：Multus 插件因找不到指定的 CNI 网络定义而阻塞了网络配置 |
| 3 | Metric | prometheus | kube_pod_container_status_waiting_reason: value=1, labels: container=app, reason=ContainerCreating (fact-66299ffa759c) | 独立指标佐证容器正在等待网络就绪 |

**证据说明：**
- K8s Event 中的 `NoNetworkFound` 错误（#2）与 Pod 状态（#1）及 Prometheus 指标（#3）完全一致，指向同一阻塞原因。
- 日志和 Tracing 因容器未启动，无业务数据，进一步排除了应用层导致启动失败的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
Namespace 'aiops-case-05' 缺少 'unavailable-network' 网络定义 → Multus CNI 无法完成沙箱网络初始化 → 容器网络接口创建阻塞 → Pod 状态卡死在 ContainerCreating
```

### 根因结论

已确认的根因是：集群 `aiops-case-05` 命名空间下引用了不存在的网络附件定义（`unavailable-network`）。
- **事实支撑**：Multus 持续报错找不到 `network-attachment-definitions.k8s.cni.cncf.io "unavailable-network"`（#2），直接导致容器网络初始化被阻断（#1）。
- **局限说明**：现有证据确认为资源缺失导致的故障，但关于“为什么 Manifest 引用了该不存在的网络定义”属于设计或配置层面的未知（Unknown），不影响当前的故障诊断结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 15.8s
├─ 并发证据采集: 50.0s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v: 50.0s (Evidence 41.6s, RCA 8.1s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-nhd7v**: pod-imagepull-failed, pod-volume-mount-failed, pod-pending-unschedulable, pod-sandbox-create-failed
