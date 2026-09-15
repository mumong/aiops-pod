## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod 挂载卷配置中引用的 ConfigMap 'unavailable-config' 不存在，且该卷配置为必需（Optional: false），导致 kubelet 挂载卷失败，Pod 持续处于 Pending/ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedMount: MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (fact-d05489b2a3b8) | 直接记录挂载卷时找不到指定 ConfigMap 的具体原因 |
| 2 | K8s State | kubernetes | Pod status: `Pending` (fact-53cf3c2654c1) | 确认 Pod 处于无法启动的阶段 |
| 3 | K8s Event | kubernetes | `FailedMount: Unable to attach or mount volumes: unmounted volumes=[input]` (fact-b654c829b0bb) | 辅助印证因挂载失败导致的资源未挂载状态 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` for container 'app' is `1` (reason: ContainerCreating) (fact-69916c56243a) | 数值上确认容器正卡在创建等待阶段 |
| 5 | K8s Config | kubernetes | container resource_request/memory: `8Mi` (fact-c21312f3c251) | 上下文信息，非导致状态异常的直接原因 |

**证据说明：**
Kubernetes 事件（#1）明确指出挂载失败的根本原因是 ConfigMap `unavailable-config` 缺失，该事实直接解释了 Pod 为何处于 `Pending`（#2）状态以及 `ContainerCreating`（#4）等待中。缺失的日志与追踪数据是因为容器未能启动，无法产生运行时观测，进一步锁定了故障发生在 K8s 基础设施初始化阶段。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 不存在 → kubelet 挂载卷 'input' 失败(必需卷) → Pod 无法启动(ContainerCreating) → Pod 状态为 Pending
```

### 根因结论
根因已确认：Pod 挂载卷配置中引用的 ConfigMap `unavailable-config` 不存在，且该卷配置为必需（Optional: false），导致 kubelet 挂载卷失败，Pod 持续处于 Pending/ContainerCreating 状态（见证据 #1）。

---

## 📊 性能统计

```text
├─ 总耗时: 54.0s
├─ 问题定位: 17.4s
├─ 并发证据采集: 28.9s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 28.9s (Evidence 23.2s, RCA 5.6s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-imagepull-failed
