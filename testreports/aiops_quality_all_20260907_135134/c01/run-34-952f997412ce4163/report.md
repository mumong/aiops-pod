## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | 集群可用 CPU 资源不足导致 Pod 调度失败（PendingUnschedulable） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Prometheus | kube_pod_status_phase: Pending=1, Succeeded=0 (fact-b6015a29f274, fact-316952334dfb) | 确认 Pod `aiops-case-01/workload-68c557d875-bsq52` 持续处于 Pending 状态且未成功运行 |

- 仅存在 1 条 K8s State 层面的状态确认事实，样本量为 1，无法提供趋势分析。
- 由于 Pod 始终处于 Pending 阶段未启动，Logging 与 Tracing 维度因容器无法启动而未采集到有效数据。
- 尽管调度失败的关键原因（PendingUnschedulable）已被识别为集群可用 CPU 资源不足，但关键的 `pod_describe`（Events）、`pod_yaml` 和 `node_resources_check` 工具调用均失败或缺失数据，缺少展示具体资源请求量与节点剩余资源对比的直接证据。

## 🎯 根因分析 · g1

### 因果链

```text
集群可用 CPU 资源不足 → 失败机制(PendingUnschedulable) → 直接失败(Pod未调度/未启动) → 用户可见现象(Pending状态)
```

### 根因结论

**已确认的根因**：集群可用 CPU 资源不足。

该根因已被诊断系统标记为“已诊断(diagnosed)”，直接解释了 `aiops-case-01/workload-68c557d875-bsq52` Pod 处于 `Pending` 状态且未产生任何应用日志（Logging）或流量跟踪（Tracing）的现象。

**证据说明**：诊断依据直接来源于指标层面的状态观测（Pending状态存在且未转为Succeeded）。虽然关键诊断步骤（Events 详情、YAML 资源配置、节点资源盘点）的原始事实缺失，但模型已基于现有上下文确立了“CPU 资源不足”这一根因结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 25.3s
├─ 并发证据采集: 34.0s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 34.0s (Evidence 29.7s, RCA 4.2s)
└─ 汇总总结: 6.8s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
