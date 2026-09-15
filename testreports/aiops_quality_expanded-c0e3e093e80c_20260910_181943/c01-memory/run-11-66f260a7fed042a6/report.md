## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod workload in aiops-case-v02 is stuck in Pending state with FailedScheduling error. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | status: False, reason: Unschedulable, message: 0/3 nodes are available: 3 Insufficient memory | 确认 Pod 因资源不足被调度器拒绝，处于不可调度状态 |
| 2 | K8s State | pod.status | status: Pending | 确认 Pod 持续处于挂起状态，未进入运行期 |
| 3 | K8s Event | event.message | Warning FailedScheduling 0/3 nodes are available: 3 Insufficient memory | 明确记录 3 个节点均因内存不足拒绝调度，且无抢占对象 |
| 4 | K8s Config | container.resource_request.memory | value: "1Pi" | 根本原因：Pod 请求内存高达 1 PiB（1,125,899,906,842,624 Bytes） |
| 5 | K8s Config | container.resource_limit.memory | value: "1Pi" | 辅助确认：硬限制同样设定为 1 PiB，进一步排除调度误差 |
| 6 | Metric | kube_pod_status_phase | value: 1 (Pending), value: 0 (Failed) | 观测确认集群内 Pending 状态的 Pod 数，验证状态未自动恢复 |

上述证据链条完整：配置文件中设定的 `1Pi` 内存请求远超常规集群节点能力（通常数十至数百 GB），导致 Kubernetes 调度器对所有节点执行资源评估时均判定为 `Insufficient memory`，进而使 Pod 长期保持 `Pending` 且无节点可调度。

## 🎯 根因分析 · g1

### 因果链

```text
配置设定 Pod 内存请求为 1Pi (fact-21db01ff587f) → 请求量级远超集群节点物理内存上限 (context) → 调度器在所有节点评估中判定 Insufficient memory (fact-1, 3) → Pod 被拒绝调度，状态变更为 Pending (fact-2, 6)
```

### 根因结论

**已确认的根因**：Pod 的资源配置错误。

Pod `aiops-case-v02/workload` 在 YAML 配置中将 `memory` 的请求与限制同时设定为 `1Pi`（fact-21db01ff587f, fact-23642ba1f1a5）。该数值（约 1.12 PiB）远远超过了集群中任何单节点的可用内存总量，导致调度器在执行调度策略时，无法找到任何一个满足该资源需求的节点，因此返回 `Insufficient memory` 错误（fact-3），使 Pod 陷入 `Pending` 状态无法启动（fact-2, 6）。该结论由 K8s 事件、状态条件及配置事实直接支撑，证据充分。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 16.4s
├─ 并发证据采集: 86.4s
│  └─ g1 aiops-case-v02/workload: 86.4s (Evidence 77.4s, RCA 8.9s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
