## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | HostPath volume 'input' 指向的路径 '/var/lib/aiops-fixture-unavailable-7f394bef/input' 在 node2 上不是目录（不存在或类型不符），导致 kubelet 挂载失败，Pod 卡在 ContainerCreating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `event.message` | `MountVolume.SetUp failed for volume "input" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` (fact-344ed05a4cb2) | 确认挂载失败的根本原因是宿主机路径类型检查未通过 |
| 2 | K8s State | `pod.status` | `Pending` (fact-2fc3d0844d5c) | 确认 Pod 因挂载问题卡在初始化阶段，处于 Pending 状态 |
| 3 | Metric | `kube_pod_container_status_waiting_reason` | `ContainerCreating` (fact-c440a7d7c00b) | 确认容器等待原因符合预期，且未因 OOM 或 Crash 重启 |
| 4 | Metric | `kube_pod_container_status_restarts_total` | `0` (fact-793aa471cfc1) | 确认容器无重启记录，排除运行时崩溃因素 |
| 5 | K8s Config | `container.resource_limit.cpu` | `50m` (fact-29e71900d712) | 确认资源限制存在，排除因资源竞争导致的调度延迟 |
| 6 | K8s Config | `container.resource_request.memory` | `8Mi` (fact-7c0cf47552f8) | 确认资源请求存在，排除因资源不足导致的 Pending |

**证据印证与说明**：
- 证据 1 (K8s Event) 直接指出了 `hostPath` 类型检查失败，且明确路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 不是目录。这是挂载失败的唯一直接原因。
- 证据 2 (K8s State) 和证据 3 (Metric) 相互印证，Pod 处于 `Pending` 且容器等待原因为 `ContainerCreating`，这与挂载卡住的状态一致。
- 证据 4 (Metric) 确认没有重启，结合证据 5 和 6 的资源配置，排除了资源短缺、OOM 或运行时错误，进一步锁定故障点在容器启动前的挂载阶段。

## 🎯 根因分析 · g1

### 因果链

```text
HostPath 卷指向路径 '/var/lib/aiops-fixture-unavailable-7f394bef/input' 非目录(或不存在) → 宿主机节点 kubelet 执行挂载时类型检查失败 → Pod 挂载卷失败，状态设为 Pending/ContainerCreating → 用户不可见应用服务
```

### 根因结论

**已确认的根因**：
Pod `aiops-case-v06/workload` 卡在 `ContainerCreating` 状态，其根因是 Kubernetes 节点 `node2` 上的宿主机路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 不符合预期（非目录或不存）。这导致 `kubelet` 在挂载名为 `input` 的 `HostPath` 卷时，因 `type check failed` 而失败（证据 1: fact-344ed05a4cb2）。由于挂载失败，Pod 无法进入 `Running` 状态（证据 2, 3），且无重启发生（证据 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 51.1s
├─ 问题定位: 16.0s
├─ 并发证据采集: 23.9s
│  └─ g1 aiops-case-v06/workload: 23.9s (Evidence 18.8s, RCA 5.0s)
└─ 汇总总结: 11.2s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed
