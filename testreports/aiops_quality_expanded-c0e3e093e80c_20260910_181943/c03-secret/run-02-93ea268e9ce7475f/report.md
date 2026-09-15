## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Pod aiops-case-v04/workload 配置了名为 'input' 的 Secret 卷，依赖 Secret 'unavailable-input'。由于该 Secret 在集群中不存在且定义为非可选（Optional: false），kubelet 在执行 VolumeMount 时因找不到 Secret 而持续失败，导致 Pod 处于 Pending 状态，容器维持在 ContainerCreating 阶段。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-8a521e76202d) | `FailedMount` : secret "unavailable-input" not found | 直接指出 Secret 缺失导致挂载失败 |
| 2 | K8s Event | kubernetes (fact-9025dad87094) | `Timed out waiting for the condition` for volume [input] | 确认挂载超时，属于同一故障的持续表现 |
| 3 | K8s State | kubernetes (fact-44d92dbc1399) | Pod status: `Pending` | 确认为 Pod 阻塞状态 |
| 4 | K8s State | kubernetes (fact-adac634bc83c) | Container reason: `ContainerCreating` | 表明 Pod 卡在初始化阶段 |
| 5 | Metric | prometheus (fact-78dd54df25a9) | `kube_pod_container_status_waiting_reason` = 1, labels: reason=`ContainerCreating` | 独立指标验证 Pod 处于等待阶段 |

**证据关联：**
K8s 事件 `FailedMount` 与 Pod 状态 `Pending` 直接对应；Metric 显示等待原因确认为 `ContainerCreating`，与 Pod 状态一致。未采集到日志和 Tracing 数据符合容器未启动的预期。

## 🎯 根因分析 · g1

### 因果链

```text
Secret 'unavailable-input' 缺失 (Optional: false) → VolumeMount 失败 (kubelet) → Pod 处于 Pending 阶段，容器维持在 ContainerCreating → 用户可见 Pod 无法启动
```

### 根因结论

已确认根因为 Pod 依赖的 Secret `unavailable-input` 不存在，导致卷挂载失败。
- **支撑证据 1**：K8s Event `FailedMount` 明确指出找不到 Secret "unavailable-input" (#1)。
- **支撑证据 2**：Pod 状态 `Pending` 和 Container 状态 `ContainerCreating` (#3, #4) 证实挂载阻塞。
- **支撑证据 3**：Metric `kube_pod_container_status_waiting_reason` 为 1 且原因为 `ContainerCreating` (#5)，独立验证了上述状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 15.4s
├─ 并发证据采集: 46.4s
│  └─ g1 aiops-case-v04/workload: 46.4s (Evidence 40.5s, RCA 5.8s)
└─ 汇总总结: 7.8s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-sandbox-create-failed
