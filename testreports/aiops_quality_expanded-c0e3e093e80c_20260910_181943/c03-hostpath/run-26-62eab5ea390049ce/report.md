## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | HostPath volume 'input' points to '/var/lib/aiops-fixture-unavailable-7f394bef/input' which is not a valid directory on node 'node2'. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container.waiting_reason: `ContainerCreating` | 确认 `app` 容器停留在调度后、启动前的阻塞状态 |
| 2 | K8s Event | kubernetes | FailedMount: `hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 直接证明 Volume 挂载因宿主机目录类型不符而失败 |
| 3 | K8s Event | kubernetes | FailedMount: `timed out waiting for the condition` | 佐证挂载操作在多次重试后超时，排除了短暂网络抖动因素 |
| 4 | Metric | prometheus | `kube_pod_status_phase` (phase: `Pending`, value: `1`) | 指标层面确认 Pod 当前处于 Pending 状态 |
| 5 | K8s State | kubernetes | pod.condition: `Ready` (status: `False`, reason: `ContainersNotReady`) | 确认 Pod 未就绪且无容器处于运行状态 |

K8s 状态、Event 与 Metric 共同指向同一结论：Pod 卡在初始化阶段，挂载卷失败是阻断容器启动的直接原因。

## 🎯 根因分析 · g1

### 因果链

```text
HostPath volume 'input' 指向 '/var/lib/aiops-fixture-unavailable-7f394bef/input' → 
该路径在 node2 上不是有效目录 (hostPath type check failed) → 
kubelet 挂载卷失败并超时 (timed out waiting for the condition) → 
Pod 持续处于 Pending 状态且容器等待启动 (ContainerCreating)
```

### 根因结论

已确认根因：Pod `aiops-case-v06/workload` 的 `input` 卷挂载失败。
**证据引用**：Kubernetes Event 明确指出宿主机节点 `node2` 上的目标路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 不是一个有效的目录（类型检查失败），导致 Kubelet 无法完成卷挂载，进而使容器无法启动，Pod 维持在 Pending 状态 [证据 2, 3, 4]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 12.4s
├─ 并发证据采集: 45.5s
│  └─ g1 aiops-case-v06/workload: 45.5s (Evidence 38.3s, RCA 7.1s)
└─ 汇总总结: 7.6s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed, pod-sandbox-create-failed, pod-imagepull-failed
