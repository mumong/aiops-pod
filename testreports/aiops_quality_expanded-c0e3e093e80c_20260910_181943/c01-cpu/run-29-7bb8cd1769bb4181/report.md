## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v01/workload` | Pending | 集群节点CPU资源耗尽导致调度失败 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.status`: Pending (`fact-33258446b1f1`) | 确认应用容器 Pod 最终状态为未就绪。 |
| 2 | K8s Event | kubernetes | `0/3 nodes are available: 3 Insufficient cpu` (`fact-5ee44b381ed6`, `fact-a746ec038bd0`) | 直接表明集群 3 个节点均无法提供调度所需的 CPU 资源，为失败原因的核心证据。 |
| 3 | K8s Config | kubernetes | `container.resource_request.cpu`: `100k` (`fact-004beb60256e`) | 提供调度失败的上下文：调度器需匹配该 CPU 预留量。 |
| 4 | Metric | prometheus | `kube_pod_status_phase{phase="Pending"}=1` (`fact-a4cbd0ab2a90`) | 独立指标数据交叉验证了 Pod 处于 Pending 阶段的事实。 |

**证据关联说明：**
K8s Event (Fact 2) 给出了明确的“3 Insufficient cpu”失败原因，与 K8s Config (Fact 3) 的资源需求及 State (Fact 1) 的 Pending 状态形成完整证据链，直接解释了为何调度失败。Metric (Fact 4) 仅作为状态确认的佐证。由于 Pod 处于 Pending 状态，Logging (not_applicable) 和 Tracing (not_applicable) 工具未采集到数据，符合预期且不影响本次根因分析。

## 🎯 根因分析 · g1

### 因果链

```text
集群节点CPU资源耗尽 → 调度器无法为 Pod 匹配满足资源要求的节点 → 调度失败(Pending) → 应用容器无法启动
```

### 根因结论

已确认根因为：**集群节点 CPU 资源耗尽导致调度失败**。

证据链表明，调度器在尝试调度 `aiops-case-v01/workload` 时，发现全部 3 个可用节点均缺乏满足 `100k` 请求量所需的 CPU 资源（事实编号 `fact-5ee44b381ed6`、`fact-a746ec038bd0`）。尽管资源请求量极小（`100k`），但集群整体已处于无法调度的资源饱和状态，导致 Pod 持续处于 Pending 状态且无法抢占任何节点资源（事实编号 `fact-b35abda6437c`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 11.4s
├─ 并发证据采集: 66.2s
│  └─ g1 aiops-case-v01/workload: 66.2s (Evidence 60.1s, RCA 6.0s)
└─ 汇总总结: 8.6s
```

📋 Runbook 参考

- 未调用 Runbook
