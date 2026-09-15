## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod aiops-case-03/workload-5b5fc86c8c-xn974 卡在 Pending 状态，容器 app 处于 ContainerCreating 等待阶段 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedMount`: MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found | 直接确认 ConfigMap 缺失导致挂载失败 |
| 2 | K8s Event | Kubernetes | `FailedMount`: Unable to attach or mount volumes: unmounted volumes=[input], unattached volumes=[input]: timed out waiting for the condition | 确认挂载阻塞状态持续存在（持续 86 分钟） |
| 3 | K8s State | Kubernetes | Pod `aiops-case-03/workload-5b5fc86c8c-xn974` 状态为 `Pending`，容器 `app` 处于 `ContainerCreating` | 现象级确认容器未进入运行态 |
| 4 | K8s State | Kubernetes | Pod `Ready` status: `False` (ContainersNotReady)；`restart_count`: 0 | 排除容器崩溃重启因素，确认为启动前阻塞 |
| 5 | K8s Config | Kubernetes | 容器 `app` 资源请求：`CPU: 5m`, `Memory: 8Mi`；限制：`CPU: 50m`, `Memory: 32Mi` | 确认非资源（CPU/内存）不足导致的调度或启动问题 |
| 6 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值为 `1` (label: `reason="ContainerCreating"`)；`kube_pod_status_phase` 值为 `1` (label: `phase="Pending"`) | 指标确认当前处于等待/挂起状态 |

**证据关联说明：**
- **K8s Event (E1, E2)** 提供了明确的失败原因（`unavailable-config` 不存在），直接解释了 **K8s State (E3)** 中 Pod 为什么处于 `Pending` 且容器卡在 `ContainerCreating`。
- **K8s State (E4)** 中的重启次数为 0 且 `ContainersNotReady`，与事件中的挂载失败一致，排除了启动后崩溃的可能性。
- **Metric (E6)** 从监控侧印证了 Pod 持续处于 `Pending` 和 `ContainerCreating` 状态，且样本量为 1，未呈现波动。
- 无日志和链路数据，因容器未启动。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义引用不存在的 ConfigMap 'unavailable-config' → 挂载卷 'input' 失败 (FailedMount) → 容器启动被阻塞 (ContainerCreating) → Pod 持续处于 Pending 状态
```

### 根因结论

已确认的根因为 **Pod 配置引用了不存在的 ConfigMap ('unavailable-config')**。

该根因由以下证据充分支撑：
1. **Kubernetes Events (E1, E2)** 明确记录 `configmap "unavailable-config" not found` 并伴随 `timed out waiting for the condition`，指出挂载卷失败。
2. **Kubernetes State (E3, E4)** 证实 Pod 停留在 `Pending` 阶段，容器处于 `ContainerCreating` 且重启次数为 0，符合挂载失败后的等待状态。
3. **Metrics (E6)** 从时序数据侧面确认了该状态已持续存在。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 28.1s
├─ 并发证据采集: 36.8s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 36.8s (Evidence 28.7s, RCA 8.0s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-volume-mount-failed
