## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod定义中引用的 hostPath 卷挂载路径 (/var/lib/aiops-fixture-unavailable-7f394bef/input) 在节点 node2 上存在类型不匹配（非目录），导致 kubelet 挂载卷失败，容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubelet | `FailedMount`: hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory (fact-9632e06769c5) | 证实节点上挂载路径类型错误，这是导致容器无法启动的直接原因 |
| 2 | K8s State | Pod Status | `phase: Pending` 且 `waiting_reason: ContainerCreating` (fact-d7d785a3493d, fact-45aef0a5d73c) | 确认 Pod 处于等待挂载卷的阻塞状态 |
| 3 | K8s Event | Kubelet | `Timed out waiting for the condition` 挂载失败持续 75 分钟 (fact-b4a6df858966) | 证实该故障持续发生且未自动恢复 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值为 1，reason 为 `ContainerCreating` (fact-8c2e79388170) | 从指标层面独立验证了容器处于挂载等待状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 值为 0 (fact-9977be9c82f7) | 排除因资源不足导致 OOMKill 或重启的可能 |

**证据印证说明：**
Kubernetes 事件（证据 1、2）直接记录了挂载失败的原因与 Pod 状态，Prometheus 指标（证据 4、5）在同一时间点独立确认了容器处于 `ContainerCreating` 等待态且无重启，两者相互印证，排除了瞬态网络或资源调度问题。

## 🎯 根因分析 · g1

### 因果链

```text
节点文件系统状态不匹配（hostPath 非目录） → 挂载卷失败 (FailedMount) → 容器等待初始化 → Pod 持续处于 Pending/ContainerCreating 状态
```

### 根因结论

**已确认根因**：Pod `aiops-case-v06/workload` 的 `hostPath` 卷挂载目标路径在节点上存在类型不匹配（期望是目录，实际非目录）。
- **证据编号**：fact-9632e06769c5, fact-8c2e79388170
- **分析**：Kubelet 报错明确指示挂载目标 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 不是目录，导致挂载操作持续失败（证据 1、3），Pod 因此卡在 `ContainerCreating` 阶段（证据 2、4）。无重启记录（证据 5）进一步排除了运行时容器层面的异常。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 24.5s
├─ 并发证据采集: 37.2s
│  └─ g1 aiops-case-v06/workload: 37.2s (Evidence 30.6s, RCA 6.5s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-imagepull-failed, pod-volume-mount-failed
