## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v06/workload` | ContainerCreating | Pod workload (aiops-case-v06) 卡在 ContainerCreating 状态，持续 Pending。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount 31s (x7 over 63s) kubelet MountVolume.SetUp failed for volume "input" : hostPath type check failed: /var/lib/aiops-fixture-unavailable-7f394bef/input is not a directory` | 直接证明挂载失败原因：节点上路径缺失或非目录 |
| 2 | K8s State | kubernetes | `pod.phase: Pending` | 说明 Pod 调度后卡在预启动阶段 |
| 3 | K8s State | kubernetes | `container.waiting_reason: ContainerCreating` | 说明容器启动被阻塞在挂载阶段 |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason{reason="ContainerCreating"} = 1` | 佐证容器当前等待状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total{container="app"} = 0` | 说明容器尚未启动过，无重启行为 |

**证据关联说明：**
Kubernetes 事件（#1）提供了根因的直接证据，指出 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 无法挂载。状态（#2, #3）和指标（#4）一致反映该 Pod 因挂载阻塞而处于 Pending/ContainerCreating 状态，且指标（#5）确认容器从未成功启动。

## 🎯 根因分析 · g1

### 因果链

```text
宿主机路径 /var/lib/aiops-fixture-unavailable-7f394bef/input 不存在 #1 → Pod声明 HostPath 卷 'input' 映射到该路径 → kubelet 执行 hostPath type check 失败 (FailedMount) #1 → 容器状态维持在 Waiting/ContainerCreating #3, Pod 处于 Pending #2
```

### 根因结论

Pod `aiops-case-v06/workload` 的 `ContainerCreating` 状态和 `Pending` 阶段是由 HostPath 卷挂载失败直接导致的。

**确认证据：**
*   **失败机制确认**：Kubernetes Event（#1）明确记录 `FailedMount`，原因是宿主机节点上的指定路径 `/var/lib/aiops-fixture-unavailable-7f394bef/input` 不是一个目录（`is not a directory`）。
*   **状态一致性**：Pod 状态（#2, #3）与 Metrics 数据（#4）完全一致，均指向容器启动卡在等待阶段，且无重启记录（#5），证明问题持续存在且未被系统自动重试修复。

**未知项：**
输入中提到“从命名看可能是故意缺失的测试用例”，表明该路径不存在可能是预期行为（即故障本身是测试验证的一部分）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 16.5s
├─ 并发证据采集: 40.1s
│  └─ g1 aiops-case-v06/workload: 40.1s (Evidence 30.8s, RCA 9.2s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v06/workload**: pod-sandbox-create-failed, pod-config-error, pod-imagepull-failed, pod-volume-mount-failed
