## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-05/workload-5dbb5dcd6c-bntfh` | ContainerCreating | Pod aiops-case-05/workload-5dbb5dcd6c-bntfh 卡在 ContainerCreating 状态，phase 为 Pending |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: { "container": "app", "reason": "ContainerCreating" } | 确认 Pod 处于启动停滞状态 |
| 2 | K8s Event | kubelet | `FailedCreatePodSandBox`: 创建 sandbox "4f3cf65d30bb..." 失败，报错 "failed to setup network for sandbox" | 记录 Pod 调度与网络初始化的具体失败机制 |
| 3 | K8s Event | multus | `NoNetworkFound`: cannot find a network-attachment-definition (unavailable-network) in namespace (aiops-case-05) | 锁定根本原因：Pod 请求的 Multus 网络定义缺失 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{container="app", reason="ContainerCreating"}`: 当前值为 1，单样本无趋势 | 从监控维度印证 Pod 持续处于 Waiting 状态 |

**证据关联说明：**
K8s 事件（事实 2、3）与监控指标（事实 4）高度一致：Pod 卡在 `ContainerCreating` 状态（事实 1），根本原因是 Multus 插件在执行网络附加时找不到 `unavailable-network` 配置（事实 3），导致 Sandbox 创建失败（事实 2）。由于容器未启动，Logging 和 Tracing 维度不适用，K8s 事件是本次定位最核心的诊断依据。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 注解引用不存在的 NetworkAttachmentDefinition 'unavailable-network' → Multus CNI 插件无法加载网络配置 → kubelet 执行 FailedCreatePodSandBox 失败 → Pod 卡在 ContainerCreating / Pending 状态
```

### 根因结论
已确认根因为：**Pod 的 `k8s.v1.cni.cncf.io/networks` 注解请求了一个在 `aiops-case-05` 命名空间中不存在的 NetworkAttachmentDefinition（名称为 `unavailable-network`）**。
该缺失导致 Multus CNI 插件无法获取网络配置，进而触发 kubelet 创建 Pod Sandbox 失败（见证据 2、3），使 Pod 永远停留在 `ContainerCreating` 状态（见证据 1、4）。
虽然诊断链完整，但关于该配置缺失的上下文（即：为什么缺失？是否为配置错误？）在输入中未被标记为已决事实（unknowns 状态），故本报告仅针对当前现象的成因进行确认。

---

## 📊 性能统计

```text
├─ 总耗时: 7.0m
├─ 问题定位: 18.1s
├─ 并发证据采集: 394.3s
│  └─ g1 aiops-case-05/workload-5dbb5dcd6c-bntfh: 394.3s (Evidence 384.9s, RCA 9.1s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-05/workload-5dbb5dcd6c-bntfh**: pod-imagepull-failed
