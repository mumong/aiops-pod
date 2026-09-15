## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | HostPath volume 'input' specified in Pod spec points to path '/var/lib/aiops-fixture-unavailable-7f394bef/input' on node 'node2', which does not exist or is not a directory, causing MountVolume.SetUp failure and blocking container startup. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubelet` | `Warning FailedMount 2m23s (x45 over 77m) kubelet MountVolume.SetUp failed for volume "input" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` (fact-47d77f921488) | 明确阻断容器启动的故障机制，指出 HostPath 挂载的具体原因。 |
| 2 | K8s State | `pod.phase` | `Pending` (fact-5e924b2b5020) | 确认 Pod 未进入运行阶段。 |
| 3 | K8s State | `container.waiting_reason` | `ContainerCreating` (fact-07b2d9f9b76a) | 确认容器卡在初始化阶段。 |
| 4 | Metric | `prometheus` | `kube_pod_container_status_waiting_reason=1`，标签 `reason="ContainerCreating"` (fact-6888203f1637) | 独立量化指标证实了容器的等待原因与 K8s 事件一致。 |

**证据说明：**
- 维度 1 中的事件直接给出了挂载失败的机制（目录不存在），维度 3 提供了这一状态的具体表现，两者互为因果链的核心环节。
- 维度 4 的指标数据（fact-6888203f1637）独立验证了维度 3 的状态，且标签 `ContainerCreating` 与事件的 `FailedMount` 机制吻合，排除了其他导致 `ContainerCreating`（如镜像拉取失败）的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
HostPath volume path 不存在于目标节点 → Kubelet 挂载卷失败 → Container 卡在 ContainerCreating 状态 → Pod 处于 Pending 且不可用
```

### 根因结论

已确认根因为：**Pod 规格中定义的 HostPath 挂载点 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 在调度节点 `node2` 上不存在或不是一个目录，导致 kubelet 挂载卷失败，从而阻塞了容器启动。**

该结论得到以下事实支持：
- **直接故障证据**：Kubelet 明确报告 `MountVolume.SetUp failed... hostPath type check failed` (fact-47d77f921488)。
- **状态一致性**：Pod 处于 `Pending` 阶段 (fact-5e924b2b5020)，容器处于 `ContainerCreating` 等待状态 (fact-07b2d9f9b76a)，且 Prometheus 指标 `kube_pod_container_status_waiting_reason` 的值确认为 `ContainerCreating` (fact-6888203f1637)。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.4s
├─ 并发证据采集: 40.7s
│  └─ g1 aiops-case-v06/workload: 40.7s (Evidence 31.5s, RCA 9.0s)
└─ 汇总总结: 9.8s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-imagepull-failed, pod-sandbox-create-failed
