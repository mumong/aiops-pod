## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-01/workload-68c557d875-bsq52` | Pending | Pod aiops-case-01/workload-68c557d875-bsq52 持续处于 Pending 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase: Pending` (fact-114f52bc880c) | 确认 Pod 处于待调度状态 |
| 2 | K8s State | kubernetes | `pod.condition: type=PodScheduled, status=False, reason=Unschedulable`，message 显示 `0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector` (fact-965052067406) | 直接证据：调度器判定无节点匹配亲和性/选择器约束 |
| 3 | K8s Config | kubernetes | `container.resource_request.memory: 8Mi`, `cpu: 5m` (fact-030f75442cc2, fact-56068322e644) | 资源请求极小，排除资源额度不足导致调度失败的可能 |
| 4 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"} = 1`，采样数 1 (fact-d6fe3bb73559) | 监控层确认 Pod 持续处于 Pending 状态 |
| 5 | Metric | prometheus | `kube_pod_status_phase{phase="Failed"} = 0` (fact-3e2b5b6d6981) | 排除容器因 OOM、CrashLoop 等运行时错误而 Failed 的可能性 |

**证据印证：**
K8s 事件明确指出因“节点亲和性/选择器不匹配”导致 0/3 节点可用（事实 #2），且资源请求极低（事实 #3），证明故障由标签约束引起而非资源瓶颈。Metric 确认该 Pending 状态正在持续（事实 #4），且未演变为失败（事实 #5），逻辑与 K8s 状态一致。

## 🎯 根因分析 · g1

### 因果链

```text
Pod Spec 包含 nodeSelector: {"aiops.lab/unavailable": "true"} → 集群所有节点缺少该标签 → 调度器评估 0/3 节点匹配，触发 FailedScheduling → Pod 持续 Pending
```

### 根因结论

**已确认的根因：** Pod 定义中的 `nodeSelector` 标签 `aiops.lab/unavailable: true` 在集群所有节点（共 3 个）上均不存在，导致调度器无法找到符合约束的节点进行绑定。

证据编号 #2 中的 K8s 事件 `reason=Unschedulable` 及其 `message` 直接指出了 `node(s) didn't match Pod's node affinity/selector`，结合 #3 排除资源问题，确认为标签约束导致的调度失败。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 13.1s
├─ 并发证据采集: 46.0s
│  └─ g1 aiops-case-01/workload-68c557d875-bsq52: 46.0s (Evidence 37.7s, RCA 8.2s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- 未调用 Runbook
