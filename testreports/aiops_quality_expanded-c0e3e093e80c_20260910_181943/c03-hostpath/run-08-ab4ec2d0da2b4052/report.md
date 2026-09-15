## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod aiops-case-v06/workload 调度的节点 node2 上，HostPath 卷挂载路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 不存在或类型不符，导致容器持久化卷挂载失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedMount`: `hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 明确指出 HostPath 卷挂载失败，原因是指定路径不存在或类型不符，直接支撑根因 |
| 2 | K8s State | Kubernetes | `container.waiting_reason`: `ContainerCreating` | 证实容器处于等待状态，由挂载失败阻断 |
| 3 | K8s State | Kubernetes | `pod.phase`: `Pending` | 证实 Pod 始终停留在 Pending 阶段，无法进入 Running |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 在 reason=`ContainerCreating` 时值为 `1` | 独立指标确认容器持续处于 ContainerCreating 等待态 |
| 5 | K8s Event | Kubernetes | `FailedMount`: `timed out waiting for the condition` | 补充说明 kubelet 挂载卷的超时行为，与路径类型错误互为因果 |

**证据印证说明：**
K8s Events (1, 5) 提供了失败的直接原因（类型检查不通过）和现象（超时等待），K8s States (2, 3) 与 Metrics (4) 分别从 K8s 内部状态和外部监控指标确认了故障的持续性。日志与追踪维度因容器未启动而未产生有效数据，不引入额外干扰。

## 🎯 根因分析 · g1

### 因果链

```text
Node2 上目标路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 不存在或类型不符 → HostPath 卷挂载类型检查失败 → 容器 Persistent Volume 挂载阻塞，kubelet 挂载超时 → Pod 状态为 Pending，容器处于 ContainerCreating 状态
```

### 根因结论

**已确认根因：HostPath 卷挂载配置目标路径不存在或类型错误。**

根据 K8s Event (Fact-60d22ff56e0d) 的 `hostPath type check failed` 错误信息，Pod `aiops-case-v06/workload` 试图在节点 node2 上挂载的 HostPath 卷 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 在节点上不符合要求（路径不存在或非目录类型）。该错误直接导致了 `FailedMount` 事件，阻止了容器启动（表现为 `ContainerCreating` 和 `Pending`）。日志与追踪维度的缺失是由于 Pod 未能成功启动，属于预期结果，不影响上述文件级挂载失败的诊断结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 29.0s
├─ 并发证据采集: 32.9s
│  └─ g1 aiops-case-v06/workload: 32.9s (Evidence 25.7s, RCA 7.1s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-sandbox-create-failed
