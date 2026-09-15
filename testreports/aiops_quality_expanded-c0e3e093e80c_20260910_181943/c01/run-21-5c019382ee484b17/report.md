## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-gtzc8` | Pending | Pod workload-68c557d875-gtzc8 处于 Pending 状态，未调度到任何节点 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `default-scheduler` | `FailedScheduling` (22m): `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 明确表明调度失败的原因为“节点亲和性/选择器不匹配” |
| 2 | K8s Event | `default-scheduler` | `FailedScheduling` (33m): `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 重复确认该 Pod 持续因标签不匹配被拒绝调度 |
| 3 | K8s State | Pod Condition | `PodScheduled=False`: `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` | 反映调度器判断当前集群环境无符合 Pod 要求的节点 |
| 4 | K8s State | Pod Phase | `Pending` | 验证 Pod 持续处于未调度阶段，未进入运行状态 |
| 5 | K8s Config | 资源 Request | CPU: `5m`, Memory: `8Mi` | 证明 Pod 资源请求极低，非资源容量耗尽导致调度失败 |
| 6 | Metric | `kube_pod_status_phase` | `Pending=1` | 监控数据确认 Pod 处于 Pending 状态的客观事实 |
| 7 | Metric | `kube_pod_status_phase` | `Unknown=0` | 排除 Pod 处于 Unknown 状态的可能性，确认定位在调度阶段 |

**证据印证：**
Kubernetes Event 与 Pod 状态字段（#1-#3）均一致指向“节点选择器不匹配”（node affinity/selector mismatch），且资源请求极低（#5），排除容量不足。Metric 数据（#6-#7）进一步印证了 Pod 停留在 Pending 阶段的持续状态。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义了 nodeSelector: {aiops.lab/unavailable: true} → 集群节点 (master, node1, node2) 均无 aiops.lab/unavailable 标签 → default-scheduler 判定 0/3 nodes available → Pod 持续保持 Pending 状态
```

### 根因结论

已确认的根因是 **Pod 的 nodeSelector 要求节点具有 `aiops.lab/unavailable=true` 标签，但集群中所有 3 个可用节点均不具备该标签**，导致调度器无法找到匹配节点，Pod 被永远挂起。

该结论由以下证据支撑：
1. K8s Event 明确报告 "didn't match Pod's node affinity/selector"（#1, #2）；
2. Pod 状态持续显示 `PodScheduled=False`，拒绝原因指向节点匹配失败（#3）；
3. Metric 显示 Pod 始终在 Pending 状态，未出现其他类型的启动失败（#6）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.7s
├─ 并发证据采集: 38.0s
│  └─ g1 aiops-case-01/workload-68c557d875-gtzc8: 38.0s (Evidence 30.1s, RCA 7.8s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-gtzc8**: pod-pending-unschedulable
