## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-2xgjz 持续处于 ContainerCreating/Pending 状态，无法进入 Running。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount 3m5s (x19 over 25m) kubelet MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (fact-9170ff0b847a) | 核心错误日志，明确指出挂载卷 `input` 因找不到 ConfigMap `unavailable-config` 而失败 |
| 2 | K8s Config | kubernetes | `container.resource_request.memory: 8Mi` (fact-15d03ed86b8f) | 排除因内存请求过大导致调度失败的可能 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory: 32Mi` (fact-202e00064aed) | 排除因内存硬限制导致容器无法启动的可能 |
| 4 | K8s State | kubernetes | `container.waiting_reason: ContainerCreating` (fact-2c47ff5736f5) | 确认容器处于等待状态，尚未开始初始化 |
| 5 | K8s State | kubernetes | `pod.status: Pending` (fact-681714820457) | 确认 Pod 停留在 Pending/ContainerCreating 阶段，未进入 Running |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (fact-9a30fedfed52, labels: container=app, reason=ContainerCreating) | 监控数据确认容器持续处于 ContainerCreating 等待态 |

**证据小结：**
Kubernetes 事件 (fact-9170ff0b847a) 直接给出了失败原因：Volume 挂载因缺少 ConfigMap 而报错，且该错误在 25 分钟内反复出现 (x19)。配置 (fact-15d03ed86b8f, fact-202e00064aed) 显示资源限制合理，排除了资源不足。状态和监控 (fact-2c47ff5736f5, fact-9a30fedfed52) 一致证实了 Pod 卡在初始化阶段。Metric 无时序数据无法展示趋势，但单点值与事件频率吻合。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 在 namespace 'aiops-case-03' 中缺失 → 
Pod volume 'input' 引用不存在的 ConfigMap 且非可选 (Optional: false) → 
kubelet 执行 MountVolume.SetUp 失败并触发 FailedMount 事件 (fact-9170ff0b847a) → 
Pod 卡在 ContainerCreating/Pending 状态 (fact-2c47ff5736f5, fact-681714820457)
```

### 根因结论

已确认的根因是 **Pod 依赖的 ConfigMap `unavailable-config` 不存在**。

Pod `workload-5b5fc86c8c-2xgjz` 的 YAML 配置中定义了一个名为 `input` 的卷，该卷引用了 ConfigMap `unavailable-config`。由于该 ConfigMap 未创建或未被引用（且配置非可选），Kubelet 在挂载卷步骤中无法找到对应的配置数据，导致 `MountVolume.SetUp` 永久失败。这一故障直接表现为 `FailedMount` 警告事件（fact-9170ff0b847a），并使得容器无法完成初始化，进而导致 Pod 始终处于 `ContainerCreating` 和 `Pending` 状态（fact-2c47ff5736f5, fact-681714820457），无法分配 IP 或启动任何业务逻辑。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 25.2s
├─ 并发证据采集: 45.4s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 45.4s (Evidence 35.8s, RCA 9.5s)
└─ 汇总总结: 12.7s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-sandbox-create-failed
