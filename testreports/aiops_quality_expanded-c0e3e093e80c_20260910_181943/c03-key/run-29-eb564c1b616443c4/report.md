## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod workload (aiops-case-v05) stuck in ContainerCreating/Pending due to FailedMount |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Warning FailedMount ... MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key` (fact-25619b866236) | 直接指出 Volume 挂载失败的具体原因：ConfigMap 键不存在 |
| 2 | K8s Event | kubelet | `Warning FailedMount ... Unable to attach or mount volumes: unmounted volumes=[input]...` (fact-258712d583ca) | 确认挂载失败为持续性阻塞动作，导致 Pod 无法继续 |
| 3 | K8s State | K8s | `container.waiting_reason` = `ContainerCreating`, `pod.phase` = `Pending` (fact-1d23f13608b3, fact-6ef8d437468c) | 描述 Pod 当前状态，与 FailedMount 事件一致 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason` (reason=ContainerCreating) = `1` (fact-2f4949f6f904) | 从指标层面印证容器等待启动状态 |

**证据说明：**
Kubelet 事件 `fact-25619b866236` 与 `fact-258712d583ca` 提供了直接的阻塞证据，确认了 `Unavailable-key` 键缺失导致挂载动作不断重试失败。状态数据（fact-1d23f13608b3）与等待原因指标（fact-2f4949f6f904）均一致指向 `ContainerCreating`。由于容器未成功挂载并启动，日志与 Tracing 维度为 `not_applicable`（物理限制），无法提供其他维度的补充观测。

## 🎯 根因分析 · g1

### 因果链
```text
Pod YAML 引用了 ConfigMap 'workload-input' 中不存在的 key 'unavailable-key' (fact-25619b866236)
  → kubelet MountVolume.SetUp 校验失败 (fact-25619b866236)
    → Volume 'input' 挂载失败，Pod 卡在 ContainerCreating 状态 (fact-1d23f13608b3, fact-258712d583ca)
      → 用户可见 Pod 无法启动 (fact-6ef8d437468c)
```

### 根因结论
**已确认的根因**：Pod 的 Volume 配置引用了 ConfigMap `workload-input` 中不存在（或键名有误）的 key `unavailable-key`。这直接导致 kubelet 在尝试挂载该卷时报错 `MountVolume.SetUp failed`，从而阻断了容器的启动过程。上述结论由 K8s Event 中的明确报错信息（fact-25619b866236）以及 Pod 持续处于 Waiting/Pending 状态的指标和状态数据（fact-1d23f13608b3, fact-2f4949f6f904）共同证实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 40.2s
├─ 并发证据采集: 42.9s
│  └─ g1 aiops-case-v05/workload: 42.9s (Evidence 34.5s, RCA 8.3s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed, pod-sandbox-create-failed
