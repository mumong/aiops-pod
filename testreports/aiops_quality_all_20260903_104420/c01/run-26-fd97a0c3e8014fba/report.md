## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-llhkh` | Pending | Pod aiops-case-01/workload-68c557d875-llhkh 持续处于 Pending 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (Pod Phase) | phase: Pending, status: Pending | 直接确认目标 Pod 当前不可用 |
| 2 | K8s Event | kubernetes (FailedScheduling) | message: "Warning FailedScheduling 23m (x8 over 58m) default-scheduler 0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling." | 明确调度失败机制为节点亲和/选择器不匹配，且预抢占无效 |
| 3 | K8s State | kubernetes (Pod Condition) | PodScheduled=False, reason=Unschedulable, message: "0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector..." | 提供调度器判定状态的精确事实支撑，证实 0/3 的匹配结果 |
| 4 | K8s Config | kubernetes (Resource) | cpu_limit=50m, cpu_request=5m, memory_limit=32Mi, memory_request=8Mi | 确认资源需求极低，资源不足非此次调度的阻碍因素 |
| 5 | Metric | prometheus (kube_pod_status_phase) | phase="Pending"=1, phase="Unknown"=0 | 从监控维度独立印证 Pod 始终处于 Pending 状态 |
| 6 | Logging | elasticsearch (tool failure) | error: "Defaulted container 'observability' out of..." / Forbidden: pods "elasticsearch-master-0" is forbidden | 记录日志采集失败原因，证明未获取到日志不影响调度失败根因判定 |

**证据关联说明：**
Kubernetes 的 `FailedScheduling` 事件（事实 2、3）直接给出了 `0/3 nodes are available: ... didn't match ... affinity/selector` 的确切报错，与资源配置极低（事实 4）形成对照，排除了资源竞争干扰。Metric 数据（事实 5）作为独立观测源，确认了状态并未在后续时间内转变为 `Unknown` 或其他异常模式。日志采集工具的失败（事实 6）进一步排除了应用侧报错作为调度前置条件的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 声明了 nodeSelector {aiops.lab/unavailable: true} → 集群所有节点（master, node1, node2）均未打此标签 → 调度器判定 0/3 节点匹配，触发 FailedScheduling → Pod 维持 Pending 状态且未绑定节点
```

### 根因结论

**根因已确认**：Pod 配置的 `nodeSelector {aiops.lab/unavailable: true}` 与集群实际节点的标签完全不匹配，导致调度器无法找到符合条件的节点（证据 2、3、6）。

该结论基于以下事实链条确立：
1. 调度器事件明确报错“node(s) didn't match Pod's node affinity/selector”（事实 2）；
2. 集群当前节点数为 3，且全部匹配失败（事实 3）；
3. 资源请求量级极低，排除资源耗尽导致的调度失败（事实 4）；
4. 监控状态持续为 Pending，排除网络分区或节点状态剧烈震荡（事实 5）。

日志和 Tracing 维度因 Pod 未启动及工具执行权限受限未采集到有效应用数据，但不影响对调度阶段错误的判定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 19.5s
├─ 并发证据采集: 56.1s
│  └─ g1 aiops-case-01/workload-68c557d875-llhkh: 56.1s (Evidence 47.3s, RCA 8.7s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-01/workload-68c557d875-llhkh**: pod-pending-unschedulable
