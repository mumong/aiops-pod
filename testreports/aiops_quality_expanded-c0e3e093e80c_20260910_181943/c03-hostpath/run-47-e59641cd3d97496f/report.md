## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod挂载Volume 'input'失败：宿主机节点 node2 上 /var/lib/aiops-fixture-unavailable-7f394bef/input 路径不是一个有效的目录（HostPath type check failed），导致容器无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod `aiops-case-v06/workload` | 状态 `Pending`，Pod 阶段 `Pending`；Ready 状态为 `False` (`ContainersNotReady`) | 确定异常实体状态 |
| 2 | K8s State | Pod `aiops-case-v06/workload` | 容器 `app` 状态 `ContainerCreating`；重启计数 `0` | 明确容器卡在启动阶段，尚未进入运行期 |
| 3 | K8s Event | kubelet | `FailedMount`：HostPath type check failed: `/var/lib/aiops-fixture-unavailable-7f394bef/input` is not a directory | 直接指出 Volume 挂载失败的根因 |
| 4 | K8s Event | kubelet | `Timed out`：`unmounted volumes=[input]`，在 77-79 分钟内反复重试挂载 | 印证挂载失败是持续存在的阻塞状态 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 为 `1` (Label: `reason=ContainerCreating`) | 时序数据侧面印证 K8s 事件与 Pod 状态 |

**证据关联说明：**
Kubernetes 事件（#3, #4）直接提供了失败机制，明确指出宿主机上的指定 HostPath 不是一个有效的目录；Pod 状态（#1, #2）和 Metric 数据（#5）一致表明容器因此原因处于持续等待（Waiting/Creating）状态，且无重启行为，符合挂载失败的特征。

## 🎯 根因分析 · g1

### 因果链

```text
宿主机节点 node2 上 /var/lib/aiops-fixture-unavailable-7f394bef/input 路径不是有效目录 → HostPath Volume 类型校验失败 (FailedMount) → kubelet 阻塞 Pod 挂载 → 容器 `app` 进入 ContainerCreating 等待状态，Pod 整体处于 Pending 状态
```

### 根因结论

已确认的根因是 Pod `aiops-case-v06/workload` 使用的 HostPath Volume `input` 挂载失败。K8s 事件 `fact-928609b81005` 记录了明确的底层错误：节点上指定的路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 不是一个有效的目录（HostPath type check failed）。这一状态导致容器无法完成初始化，Pod 一直停留在 `Pending` 状态，并在 79 分钟的重试窗口内持续阻塞。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 14.4s
├─ 并发证据采集: 41.8s
│  └─ g1 aiops-case-v06/workload: 41.8s (Evidence 35.2s, RCA 6.6s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-sandbox-create-failed
