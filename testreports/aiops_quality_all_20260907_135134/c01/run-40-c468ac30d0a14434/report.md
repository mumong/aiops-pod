## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod aiops-case-01/workload-68c557d875-bsq52 处于 Pending 状态，无法分配到节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `FailedScheduling ... 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 明确调度失败的直接原因（节点亲和性/选择器不匹配） |
| 2 | K8s State | kubernetes | `pod.status` = `Pending` | 确认 Pod 处于无法运行且未调度的状态 |
| 3 | K8s Config | kubernetes | `container.resource_request.cpu` = `5m`, `memory` = `8Mi` | 证明 Pod 资源请求极低，并非因资源耗尽导致调度失败 |
| 4 | K8s Config | kubernetes | `container.resource_limit.cpu` = `50m`, `memory` = `32Mi` | 证明资源硬限制设置合理，未出现因超卖或限制过大导致的冲突 |
| 5 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"}` = `1` | 通过 Prometheus 监控确认 Pod 持续处于 Pending 阶段 |

**证据总结：**
Kubernetes 调度事件与 Pod 状态直接印证了 Pod 因节点亲和性/选择器（node affinity/selector）不匹配而被拒绝调度。Metric 数据佐证了这一状态。资源配置（Request/Limit）极低且正常，排除了资源不足的可能性。鉴于 Pod 未启动，Logging 和 Tracing 维度的缺失属于预期结果。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义中包含 NodeSelector 'aiops.lab/unavailable=true' → 集群中 3 个节点均不满足该标签条件 → 调度器触发 FailedScheduling 事件并拒绝分配节点 → Pod 保持 Pending 状态
```

### 根因结论

**根因确认：**
Pod 配置的 `NodeSelector`（节点选择器）`aiops.lab/unavailable=true` 与集群中所有节点的实际标签不匹配。
- 调度器在尝试调度该 Pod 时，发现集群内所有 3 个节点均无法满足该特定的标签选择条件，因此直接拒绝分配（Refused Scheduling）。
- **证据支撑：** 事件 `FailedScheduling` 明确指出节点未匹配 Pod 的 node affinity/selector；Pod 状态为 Pending 且资源请求量极低（CPU 5m, Memory 8Mi），排除了资源不足导致的调度失败。

---

## 📊 性能统计

```text
├─ 总耗时: 53.3s
├─ 问题定位: 17.8s
├─ 并发证据采集: 27.3s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 27.3s (Evidence 20.0s, RCA 7.2s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-bsq52**: pod-pending-unschedulable
