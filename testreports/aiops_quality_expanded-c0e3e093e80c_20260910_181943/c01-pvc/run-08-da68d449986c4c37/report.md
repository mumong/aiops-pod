## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | Pod 'workload' 请求的 PVC 'unavailable-claim' 不存在，导致调度器无法分配节点，Pod 处于 Pending 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status: Pending` (`fact-45f8bb58b0a6`) | 展示实体最终状态 |
| 2 | K8s Event | kubernetes | `FailedScheduling` 连续两次上报，原因为 `persistentvolumeclaim "unavailable-claim" not found` (`fact-7a075b322654`, `fact-88402d07a6a9`) | 直接定位导致调度失败的资源依赖缺失 |
| 3 | K8s Config | kubernetes | 容器配置：CPU Request `5m`/Limit `50m`；Memory Request `8Mi`/Limit `32Mi` (`fact-0b5ffc435eaa`, `fact-20ba60b00f71`, `fact-7c88f8cf39fe`, `fact-e41cfd593062`) | 排除资源容量不足导致的调度瓶颈 |
| 4 | Metric | prometheus | `kube_pod_status_phase` 中 `Pending` 状态值为 `1` (`fact-b330158d6d1b`) | 独立时序确认 Pod 未进入运行状态 |

**证据说明：**
*   K8s 事件 (`#2`) 明确指出了导致调度失败的直接原因（PVC `unavailable-claim` 不存在），这与 Pod 状态的挂起 (`#1`) 逻辑一致。
*   容器资源请求值 (`#3`) 极低，证明 `Pending` 状态非由于集群 CPU/内存配额耗尽引起，将故障范围锁定在 PVC 依赖上。
*   监控指标 (`#4`) 确认了当前状态的持续性。
*   Logging 和 Tracing 维度均为 `not_applicable`，原因是 Pod 未启动，无业务日志与流量，不影响根因判断。

## 🎯 根因分析 · g1

### 因果链
```text
PVC 'unavailable-claim' 不存在 → 调度器因依赖资源缺失而 FailedScheduling → Pod 保持 Pending 状态 → 应用不可用
```

### 根因结论
**已确认根因：** Pod `workload` 请求的 PVC `unavailable-claim` 不存在。

**分析依据：**
调度器事件 `FailedScheduling` (`#2`) 明确报出 PVC 查找失败，这是阻止 Pod 进入运行状态的直接原因。容器资源请求 (`#3`) 排除了资源容量瓶颈，时序指标 (`#4`) 佐证了 Pod 持续处于非就绪状态。逻辑链条完整且直接，无需补充其他维度的决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 45.3s
├─ 问题定位: 16.1s
├─ 并发证据采集: 20.1s
│  └─ g1 aiops-case-v03/workload: 20.1s (Evidence 16.5s, RCA 3.5s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
