## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod workload (aiops-case-v06) stuck in ContainerCreating state on node2 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `FailedMount 46s (x33 over 51m) ... MountVolume.SetUp failed for volume "input" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 确证卷挂载直接失败的核心原因，指出主机路径非目录且错误持续超过51分钟 |
| 2 | K8s Event | kubelet | `FailedMount 6m19s (x20 over 49m) ... timed out waiting for the condition` | 佐证挂载阻塞与超时，支撑根因的持续性 |
| 3 | Metric | prometheus | `kube_pod_container_status_waiting_reason {container="app", reason="ContainerCreating"} = 1` | 确认容器处于“等待挂载”的停滞状态，与事件状态一致 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total {container="app"} = 0` | 证明容器自调度后从未启动，排除了因应用崩溃导致未启动的可能 |
| 5 | K8s State | kubernetes | `pod.status = "Pending"`, `restart_count = 0` | 确认工作负载停留在 `Pending` 阶段，且从未进入 `Running` |

**证据逻辑：** 证据1（Event）直接给出了失败的具体机制——目标路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 检查失败。这与证据2（Event）记录的多次超时和挂起状态一致。证据3和证据4（Metric）从遥测层面证实了容器卡在 `ContainerCreating` 阶段且无重启，这与 Kubernetes 调度器停留在 `Pending` 状态的记录（证据5）完全吻合。

## 🎯 根因分析 · g1

```text
HostPath target path is not a valid directory on node2 → MountVolume.SetUp failed (kubelet type check) → Pod stuck in ContainerCreating/Pending phase → Container 'app' cannot start
```

### 根因结论
已确认根因为 **HostPath 卷配置错误导致挂载失败**。

1. **已确认的根因**：工作负载 `aiops-case-v06/workload` 中的容器 `app` 定义了一个名为 `input` 的 HostPath 卷。在调度目标节点 `node2` 上，该卷指定的目标路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 不符合预期（非目录），导致 kubelet 在执行 `MountVolume.SetUp` 时直接报错。
2. **证据印证**：
   - **核心错误**：证据1（`fact-5040f8513ab6`）明确记录了 `hostPath type check failed`，这是引发后续所有阻塞状态的直接原因。
   - **状态印证**：证据2（`fact-e923c9299267`）记录了该卷的挂载在 49-51 分钟内持续超时。
   - **现象印证**：证据3（`fact-0012edfcb305`）显示容器状态为 `ContainerCreating`，证据4（`fact-ab5dca76a73e`）显示重启次数为 0，这与卷挂载失败导致 Pod 无法进入运行状态的预期完全一致。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 27.8s
├─ 并发证据采集: 44.8s
│  └─ g1 aiops-case-v06/workload: 44.8s (Evidence 36.0s, RCA 8.8s)
└─ 汇总总结: 11.2s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-config-error
