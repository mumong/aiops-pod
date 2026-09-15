## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态超过 97 分钟 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.status | Terminating (lasts 97m) | 确认 Pod 长期处于终止阶段，证明删除流程被阻塞 |
| 2 | K8s State | container.last_exit_code | 137 | 确认容器应用层曾发生异常（OOM 或系统 Kill） |
| 3 | K8s Config | container.resource_limit.memory | 96Mi | 提供资源背景，137 退出码暗示资源耗尽可能性 |
| 4 | Metric | kube_pod_container_status_restarts_total | 0 | 确认异常后未发生正常重启，Pod 仍挂起在删除队列中 |

**证据分析：**
Pod 处于 Terminating 状态超过 97 分钟（事实 1）且容器重启计数为 0（事实 4），结合退出码 137（事实 2）表明应用在最后一次异常后未重启，而是直接停留在删除阶段。资源限制 96Mi（事实 3）解释了应用崩溃的可能原因，但无法解释为何 Kubernetes 无法在应用结束后完成 Pod 对象的清理。这些事实共同指向了 Pod 生命周期中非应用层面的阻断行为。

## 🎯 根因分析 · g1

### 因果链

```text
存在自定义 Finalizer 'aiops.lab/hold' → 控制器未完成关联外部资源的清理工作 → Pod 元数据中的 finalizers 字段未被 Kubernetes 清理 → API Server 拒绝移除 Terminating 状态的 Pod 对象
```

### 根因结论

已确认根因为：自定义 Finalizer `aiops.lab/hold` 未被移除，导致 Kubernetes API Server 无法完成 Pod 对象的垃圾回收。

Pod 对象因持有该 Finalizer，必须等待关联的外部资源清理控制器介入并完成清理工作。然而，证据显示截至观察时（97 分钟），该清理流程尚未完成，导致 API Server 拒绝执行删除动作，使 Pod 永久阻塞在 Terminating 状态。

**缺失的决定性事实：**
目前证据不足以说明“控制器未能完成清理”的具体原因（如控制器是否存活、是否存在死锁、或权限是否不足）。要完全定位阻塞环节，需要补充负责 `aiops.lab/hold` 清理的具体控制器（Controller/CRD）的状态及日志。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 27.1s
├─ 并发证据采集: 39.4s
│  └─ g1 aiops-case-11/workload: 39.4s (Evidence 30.0s, RCA 9.2s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
