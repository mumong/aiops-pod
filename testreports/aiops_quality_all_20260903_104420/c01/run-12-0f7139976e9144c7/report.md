## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 处于 Pending 状态，未被调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | default-scheduler | `FailedScheduling  0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling..` | 确认为节点亲和/标签不匹配导致的调度拒绝 |
| 2 | K8s State | pod.condition | `Unschedulable: 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 确认 Pod 因无法匹配节点而保持 Unschedulable |
| 3 | K8s State | pod.phase | `Pending` | 确认 Pod 当前始终处于未调度状态 |
| 4 | K8s Config | resource requests/limits | CPU: 5m/50m, Memory: 8Mi/32Mi | 资源请求极低，排除因资源耗尽导致的调度失败 |
| 5 | Metric | kube_pod_status_phase | `phase=Pending, value=1`；`phase=Running, value=0` | 验证 Pod 持续处于 Pending 状态且未转为 Running |

**证据关联分析：**
Kubernetes 调度事件（证据 1、2）明确指向 `node affinity/selector` 不匹配。结合资源配置证据（证据 4）显示资源请求极低，排除了集群资源瓶颈，进一步将故障根因锁定在节点标签匹配问题上。Metric 数据（证据 5）与 Pod 状态（证据 3）相互印证，确认故障具有持续性。由于 Pod 处于 Pending 状态，Logging 和 Tracing 工具调用失败或未产生数据。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义包含 nodeSelector: {aiops.lab/unavailable: true} → 集群节点均无 aiops.lab/unavailable=true 标签 → 调度器拒绝调度 (FailedScheduling: 0/3 nodes didn't match) → Pod 保持 Pending 状态
```

### 根因结论

**已确认的根因：**
Pod `aiops-case-01/workload-68c557d875-llhkh` 配置了 `nodeSelector: {aiops.lab/unavailable: true}`，但集群内所有节点（master, node1, node2）均缺少该标签，导致 `default-scheduler` 无法匹配到任何可用节点，从而产生 `FailedScheduling` 事件并拒绝调度。该结论由调度器事件（证据 1、2）与 Pod 状态（证据 3）直接证实。

---

## 📊 性能统计

```text
├─ 总耗时: 10.7m
├─ 问题定位: 558.3s
├─ 并发证据采集: 73.1s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 73.1s (Evidence 64.0s, RCA 8.9s)
└─ 汇总总结: 8.8s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
