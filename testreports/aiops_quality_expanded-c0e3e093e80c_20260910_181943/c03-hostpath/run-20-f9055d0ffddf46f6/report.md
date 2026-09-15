## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod aiops-case-v06/workload 持续处于 ContainerCreating/Pending 状态，容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | `ContainersReady: False (ContainersNotReady)` (fact-0512b6cf28c0) | 确证 Pod 容器未就绪，处于异常状态。 |
| 2 | K8s State | pod.phase | `Pending` (fact-3733424a27da) | 确证 Pod 未成功调度到运行阶段，停留在初始化阶段。 |
| 3 | K8s Event | kubelet | `Warning FailedMount: ... timed out waiting for the condition` (fact-8e64db8c5bb3) | 核心失败现象，指示卷挂载操作超时且失败。 |
| 4 | K8s Event | kubelet | `Warning FailedMount: hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` (fact-d811732f91d4) | 根本故障点，明确指出了挂载卷因类型不匹配而校验失败。 |
| 5 | K8s Config | container.resource_request | Memory: `8Mi`, CPU: `5m` (fact-3ad8beb2fd8a) | 排除资源配额不足（OOMKill）导致容器无法启动的可能。 |
| 6 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` (fact-8d72a2a8d589) | 独立监控数据印证了 Kubernetes API 中观察到的等待状态。 |

**证据印证说明：**
1. Kubernetes 事件 (Item 3, 4) 直接给出了失败的具体原因（hostPath 类型校验失败），并解释了为何容器处于 `ContainerCreating` (Item 1, 2) 的等待状态。
2. 监控指标 (Item 6) 与 K8s 事件及状态一致，证明了该挂载失败是一个持续存在且未被自愈系统解决的状态。
3. 资源配置 (Item 5) 证实了该问题并非由容器资源限制引起，进一步将故障范围缩小至存储卷本身。

## 🎯 根因分析 · g1

### 因果链

```text
HostPath 路径 /var/lib/aiops-fixture-unavailable-7f3bef/input 在节点 node2 上不存在或类型不匹配 → kubelet 执行 MountVolume.SetUp 时触发 type check failed 错误 → Volume 'input' 挂载失败，Pod 无法完成初始化 → Pod 持续处于 ContainerCreating/Pending 状态
```

### 根因结论

**已确认的根因**：Pod YAML 中定义的 HostPath 卷 `input` 引用的路径 `/var/lib/aiops-fixture-unavailable-7f3bef/input` 在调度节点上不存在，或者存在但类型不匹配（非目录），导致 `kubelet` 的挂载操作因 `hostPath type check failed` 而终止。

该故障通过以下证据得到确证：
*   **直接故障源**：Kubelet 事件报告了具体的 `FailedMount` 错误及详细的路径校验失败信息 (`fact-8e64db8c5bb3`, `fact-d811732f91d4`)。
*   **状态一致性**：Prometheus 指标 (`fact-8d72a2a8d589`) 与 K8s API 状态 (`fact-3733424a27da`) 均确认容器处于等待挂载的 `ContainerCreating` 状态，且无重启记录 (`fact-6bdaa621da7a`, `fact-4cfbc74cd217`)，排除了其他如 OOM 或崩溃重启的可能性。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.9s
├─ 并发证据采集: 37.8s
│  └─ g1 aiops-case-v06/workload: 37.8s (Evidence 28.9s, RCA 8.8s)
└─ 汇总总结: 12.4s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed
