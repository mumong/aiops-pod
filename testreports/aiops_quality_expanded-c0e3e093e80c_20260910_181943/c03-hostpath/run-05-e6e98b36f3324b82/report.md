## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod aiops-case-v06/workload 持续处于 ContainerCreating 状态，无法启动容器 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedMount`: hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory (fact_id: fact-1fdc2d0a6d3e) | 指出挂载失败的根本原因在于宿主机路径类型不匹配，是决定性事实 |
| 2 | K8s Event | Kubernetes | `FailedMount`: timed out waiting for the condition (fact_id: fact-57e666b2a6bf) | 确认了挂载操作的持续失败与超时，支持直接故障表现 |
| 3 | K8s State | Kubernetes | 容器 `app` 状态为 `ContainerCreating`，Pod Phase 为 `Pending`，无重启 (fact_id: fact-45c8795fe7ca) | 确认了故障处于容器创建阶段，Pod 始终未就绪 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 中 `ContainerCreating` 值为 1 (fact_id: fact-6e90d7d470d7) | 独立验证了容器卡在创建等待状态 |

**证据说明**：
Kubernetes 事件 (Fact 1, 2) 提供了确切的错误信息 `hostPath type check failed`，直接指向挂载卷 `input` 的路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 在宿主机上不符合目录要求。Metric 数据 (Fact 4) 与 K8s 状态 (Fact 3) 互相印证了应用容器卡在 `ContainerCreating` 状态的事实，排除了其他容器状态异常的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
节点 node2 上的路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 不是目录 → 
kubelet 执行 MountVolume.SetUp 检测到类型不匹配 → 
卷 'input' 挂载失败并超时 → 
容器无法启动，Pod 停留在 ContainerCreating 状态
```

### 根因结论

**已确认的根因**：
Pod `aiops-case-v06/workload` 配置了一个指向节点 `node2` 的 `HostPath` 卷 `input`，目标路径为 `/var/lib/aiops-fixture-unavailable-7f394bef/input`。该路径在节点上的实际类型不是目录（是文件、不存在的文件或类型不匹配的实体），导致 kubelet 的 `hostPath type check failed`，进而引起挂载超时。

**证据引用**：
- **K8s Event (Fact 1)**: `hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` 明确说明了路径类型错误。
- **K8s State (Fact 3)** & **Metric (Fact 4)**: 证明了挂载失败导致的直接后果——Pod 无法进入运行状态。

该结论证据充分，无需进一步探索。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 17.5s
├─ 并发证据采集: 42.7s
│  └─ g1 aiops-case-v06/workload: 42.7s (Evidence 31.8s, RCA 10.8s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-volume-mount-failed
