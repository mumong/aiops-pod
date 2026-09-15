## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod aiops-case-v04/workload 处于 ContainerCreating 阶段无法启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : secret "unavailable-input" not found` (fact-6a9c8e8cb20f) | 核心证据：Kubelet 明确报告因 Secret 缺失导致挂载失败 |
| 2 | K8s Event | kubernetes | `Warning FailedMount ... timed out waiting for the condition` (fact-c27552ced946) | 佐证挂载阻塞：kubelet 持续超时等待挂载条件 |
| 3 | K8s State | kubernetes | `status: "Pending"` (fact-395c7d2ad3e8) | 描述 Pod 最终处于不可调度/启动状态的停滞结果 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (ContainerCreating=1) (fact-6299dbdad183) | 确认容器正处于等待启动的中间状态，尚未 CrashLoop |
| 5 | K8s Config | kubernetes | `container.resource_request.memory: 8Mi, container.resource_limit.memory: 32Mi` (fact-a0b15ca09f29, fact-1448cdb53a0f) | 上下文排除资源耗尽导致启动失败的可能性 |

证据 1 和 2 直接证实了挂载失败的具体原因（Secret 缺失），证据 3 和 4 展示了这一原因导致的 Pod 状态（Pending）与容器行为（Waiting）。上下文资源配置（证据 5）排除了内存不足作为干扰因素。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'unavailable-input' 不存在 → Kubelet 挂载卷失败 → 容器处于 Waiting/ContainerCreating 状态 → Pod 异常未恢复
```

### 根因结论

**已确认的根因**：
Pod `aiops-case-v04/workload` 引用了 Secret `unavailable-input` 作为 Volume 挂载源，但集群中不存在该 Secret。这一缺失直接导致 Kubelet 在执行 `MountVolume.SetUp` 时失败，使 Pod 陷入 `ContainerCreating` 等待状态且无法进入 `Running`（证据 1, 2）。

**未确认项**：
该 Secret 是处于“从未被创建”还是“被意外删除”的状态（基于异常定义中的 unknowns）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 63.4s
├─ 并发证据采集: 47.0s
│  └─ g1 aiops-case-v04/workload: 47.0s (Evidence 39.2s, RCA 7.7s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-imagepull-failed, pod-volume-mount-failed
