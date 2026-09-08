## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-zz82w` | ContainerCreating | Pod workload-5b5fc86c8c-zz82w 持续处于 ContainerCreating/Pending 状态，容器未启动 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning FailedMount 5m24s (x45 over 80m) kubelet MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` (fact-77d48e3e5e93) | 直接证据：明确显示因 ConfigMap 缺失导致挂载连续失败 |
| 2 | K8s Event | kubernetes | `Warning FailedMount 10m (x31 over 78m) kubelet Unable to attach or mount volumes: unmounted volumes=[input]... timed out waiting for the condition` (fact-e85eb2c383aa) | 佐证证据：确认挂载操作处于等待/超时状态，阻塞启动 |
| 3 | K8s State | kubernetes | `container.waiting_reason`: `ContainerCreating` (fact-405dcdc18eb1) | 症状证据：容器处于等待状态，未进入 Running |
| 4 | K8s State | kubernetes | `pod.phase`: `Pending` (fact-d08591494a86) | 症状证据：Pod 停留在 Pending 阶段 |
| 5 | Metric | prometheus | `kube_pod_container_status_waiting_reason=1` (labels: `container="app", reason="ContainerCreating"`) (fact-6990e488fdd4) | 交叉验证：Prometheus 指标确认容器正以 ContainerCreating 原因处于等待 |

证据 1 和 2 在 80 分钟内重复 76 次，一致指向 ConfigMap 缺失导致的挂载失败。证据 3 和 4 展示了故障导致的 Pod 最终状态（Pending / ContainerCreating），与 Metrics 维度（证据 5）相互印证，确认启动过程已被挂载阻塞。

## 🎯 根因分析 · g1

```text
ConfigMap 'unavailable-config' 不存在于 aiops-case-03 命名空间 →  kubelet 尝试挂载非可选 volume 'input' 失败 → Pod 触发 FailedMount 并持续超时 → Pod 保持在 Pending/ContainerCreating 状态
```

**根因结论：**
根因已确认：Pod 定义的 volume `input` 依赖 ConfigMap `unavailable-config`，该配置在 `aiops-case-03` 命名空间中不存在，且配置为非可选挂载，导致 kubelet 挂载持续失败。
- 此故障直接阻断了容器启动流程，表现为 `ContainerCreating` 状态和重复的 `FailedMount` 事件（证据 1、2、5）。
- 目前无应用日志或 Trace 数据（logging/tracing 采集不可用），因此无法评估业务侧影响，但集群状态故障的根因已明确。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 35.9s
├─ 并发证据采集: 58.6s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-zz82w: 58.6s (Evidence 50.1s, RCA 8.3s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-zz82w**: pod-volume-mount-failed
