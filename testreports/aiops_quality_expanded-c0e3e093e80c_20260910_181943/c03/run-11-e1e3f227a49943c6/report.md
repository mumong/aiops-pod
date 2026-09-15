## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-03/workload-5b5fc86c8c-xn974` | ContainerCreating | Pod spec 引用了不存在的 ConfigMap 'unavailable-config' 且未标记为 Optional，导致 kubelet 挂载卷失败并持续阻塞容器创建。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.status` | status: `Pending` | 确认 Pod 处于未就绪状态 |
| 2 | K8s Event | `FailedMount` | `MountVolume.SetUp failed for volume "input" : configmap "unavailable-config" not found` | 明确指向挂载卷失败的具体缺失对象 |
| 3 | K8s Event | `FailedMount` | `timed out waiting for the condition` (x10) | 证实故障具有持续性，而非短暂抖动 |
| 4 | Metric | `kube_pod_container_status_waiting_reason` | `1` (reason: `ContainerCreating`) | 佐证容器因配置或挂载问题持续处于等待创建阶段 |
| 5 | Metric | `kube_pod_container_status_restarts_total` | `0` | 排除容器启动后崩溃重启导致的问题，进一步锁定在启动前阶段 |

上述 K8s 事件明确记录了因找不到 ConfigMap 导致的挂载失败，且该错误已持续发生 23 次（跨度 31 分钟）；Metric 数据显示 Pod 持续处于 `ContainerCreating` 等待状态且重启次数为 0，排除了运行期故障，与挂载阶段的阻塞状态高度吻合。

## 🎯 根因分析 · g1

### 因果链

```text
Spec 引用不存在的 ConfigMap 'unavailable-config' → kubelet 挂载卷失败（FailedMount） → 容器持续处于 ContainerCreating 阻塞状态 → 用户可见 Pod 状态 Pending 且无法访问
```

### 根因结论

已确认的根因为 Pod 规范中引用了不存在且未标记为 Optional 的 ConfigMap `unavailable-config`（证据 #2, #3）。该缺失依赖导致 kubelet 在启动容器前执行 `MountVolume` 时连续失败，直接引起 Pod 卡在 `ContainerCreating` 阶段无法转入 Running 状态（证据 #1, #4, #5）。

---

## 📊 性能统计

```text
├─ 总耗时: 9.6m
├─ 问题定位: 24.4s
├─ 并发证据采集: 542.1s
│  └─ g1 aiops-case-03/workload-5b5fc86c8c-xn974: 542.1s (Evidence 537.7s, RCA 4.3s)
└─ 汇总总结: 6.7s
```

📋 Runbook 参考

- **g1 aiops-case-03/workload-5b5fc86c8c-xn974**: pod-volume-mount-failed
