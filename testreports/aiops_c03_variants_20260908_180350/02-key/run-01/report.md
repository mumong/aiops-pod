## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v05/workload` | ContainerCreating | Pod `workload` (aiops-case-v05) stuck in `ContainerCreating` / Pending phase |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Warning FailedMount: MountVolume.SetUp failed for volume "input" : configmap references non-existent config key: unavailable-key | 确认挂载卷失败的确切原因（ConfigMap Key 缺失） |
| 2 | K8s State | kubernetes | container.waiting_reason = ContainerCreating | 确认当前容器卡在启动前的挂载阶段 |
| 3 | K8s State | kubernetes | pod.status = Pending, phase = Pending | 确认 Pod 处于等待资源就绪状态，未进入运行阶段 |
| 4 | Metric | prometheus | kube_pod_container_status_waiting_reason = 1 (reason: ContainerCreating) | 通过监控指标交叉验证了 Kubernetes 事件中的等待原因 |
| 5 | Metric | prometheus | kube_pod_container_status_restarts_total = 0 | 证明该容器尚未启动过，排除了因运行期资源不足导致重启的可能性 |

**证据关联说明：**
证据 1 提供了唯一的故障直接原因（ConfigMap 键不存在），证据 2、3 展示了由此引发的 Pod 状态结果（Pending/ContainerCreating）。证据 4 独立地从监控系统角度证实了处于 ContainerCreating 阶段的等待状态。证据 5 排除了应用逻辑或运行期崩溃因素。四个证据在因果链上逻辑闭环。

## 🎯 根因分析 · g1

### 因果链
```text
ConfigMap 定义引用了不存在的 Key (`unavailable-key`) → Kubelet 尝试挂载 Volume 失败 → 触发 FailedMount 事件，容器运行时无法初始化 → Pod 卡在 ContainerCreating/Pending 状态，无法对外提供服务
```

### 根因结论
已确认的根因是 **ConfigMap 引用错误**（证据 1）。
Volume `input` 指向的 ConfigMap 中并不存在指定的键 `unavailable-key`，导致 Kubelet 在执行 `MountVolume.SetUp` 时持续失败（证据 1）。该挂载失败直接阻塞了容器运行时的初始化流程，导致容器原因始终为 `ContainerCreating`（证据 2、4）且 Pod 状态保持为 `Pending`（证据 3）。由于容器从未启动，因此没有重启记录（证据 5）。现有事实确凿，无需额外排查其他维度。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 24.2s
├─ 并发证据采集: 39.8s
│  └─ g1 aiops-case-v05/workload: 39.8s (Evidence 30.6s, RCA 9.1s)
└─ 汇总总结: 7.7s
```

📋 Runbook 参考

- **g1 aiops-case-v05/workload**: pod-imagepull-failed, pod-sandbox-create-failed
