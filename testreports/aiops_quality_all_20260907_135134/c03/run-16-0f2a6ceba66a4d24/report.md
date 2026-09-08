## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-2xgjz` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-2xgjz 处于 ContainerCreating/Pending 状态，无法启动。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `FailedMount`：`MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 定位失败根因：缺失的 ConfigMap 导致挂载无法完成 |
| 2 | K8s Event | kubelet | `FailedMount`：`timed out waiting for the condition` (x10 over 25m) | 佐证挂载失败导致 Pod 长时间阻塞的客观事实 |
| 3 | K8s State | pod status | `Pending` (fact-5dc9dbe9ed40) | 确认 Pod 处于阻塞状态，且 `ContainerCreating` 未进入 `Running` |
| 4 | Metric | prometheus | `kube_pod_container_status_waiting_reason`: 1, `reason=ContainerCreating` (fact-5903dc48da2a) | 独立观测指标印证容器卡在创建阶段，未发生重启 |
| 5 | K8s Config | spec | `volumes=[input]` 依赖缺失配置 | 提供触发挂载检查的卷定义上下文 |

**证据说明：**
1. 事件与指标双向印证：事件日志明确指出 `configmap "unavailable-config" not found` 是导致 `FailedMount` 的直接原因；Prometheus 的等待原因指标同步显示为 `ContainerCreating`，排除其他原因（如 OOM、CrashLoopBackOff）导致挂起的可能。
2. 状态一致性：Pod 状态为 `Pending` 且重启次数为 0，说明故障发生在容器启动前的挂载阶段，未触及容器应用逻辑，因此 Logging 和 Tracing 无数据符合物理逻辑。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'unavailable-config' 不存在 → kubelet 尝试挂载卷 'input' 失败 → Pod 阻塞在 MountVolume.SetUp 阶段 → 状态变为 ContainerCreating/Pending
```

### 根因结论

已确认根因为 Pod 的 `volume 'input'` 引用了一个不存在（名称为 `unavailable-config`）的 ConfigMap。Kubelet 在启动容器前必须验证并挂载所有卷，由于配置对象缺失，挂载操作持续失败并超时，导致 Pod 永远无法进入 `Running` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 52.6s
├─ 问题定位: 21.5s
├─ 并发证据采集: 23.2s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-2xgjz: 23.2s (Evidence 17.0s, RCA 6.0s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-2xgjz**: pod-imagepull-failed
