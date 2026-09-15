## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v02/workload` | Pending | Pod aiops-case-v02/workload 处于 Pending 状态且无法调度 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (`fact-15f639c121bf`) | `Warning FailedScheduling 53m ... 0/3 nodes are available: 3 Insufficient memory.` | 确认调度器长期判定内存不足 |
| 2 | K8s State | kubernetes (`fact-88fccca76e45`) | `container.resource_request.memory: 1Pi` | 揭示调度评估的核心异常请求量（1Pi） |
| 3 | K8s State | kubernetes (`fact-92865f3ebd73`) | `PodScheduled=False (Unschedulable): 0/3 nodes are available: 3 Insufficient memory` | 与事件一致，确认当前 Pod 状态 |
| 4 | K8s Config | kubernetes (`fact-9bfacf9a8b9d`) | `container.resource_limit.memory: 1Pi` | 限制与请求一致，均为无法在物理节点满足的超大值 |
| 5 | Metric | prometheus (`fact-d10adce98b14`) | `kube_pod_status_phase: 1` (labels: `phase: Pending`) | 指标层面确认目标 Pod 持续处于 Pending 状态 |

**证据说明：**
1. **请求量级异常**：证据 2 和 4 显示 Pod 对内存的声明高达 `1Pi`，这是导致调度失败的核心上下文。
2. **机制验证**：证据 1 和 3 指出集群中所有 3 个节点均因 `Insufficient memory` 拒绝调度，证明没有节点能满足此量级的资源请求。
3. **状态闭环**：指标证据 5 独立于日志/追踪，在指标维度再次确认了 Pod 长期处于 `Pending` 阶段，与事件时间轴（53m）相符。

## 🎯 根因分析 · g1

### 因果链
```text
容器 app 声明内存资源: 1Pi → 调度器计算节点可用容量不足 → 触发 FailedScheduling 拒绝调度 → Pod 长期处于 Pending 状态
```

### 根因结论
**已确认根因：容器资源声明超出集群物理极限**

证据表明，容器 `app` 显式声明了 `1Pi` (1 PetaByte) 的内存作为 Request (`fact-88fccca76e45`) 和 Limit (`fact-9bfacf9a8b9d`)。Kubernetes 调度器在尝试调度时，发现集群内所有 3 个可用节点均无法满足该内存要求，从而判定为 `Insufficient memory` 并拒绝调度 (`fact-15f639c121bf`, `fact-92865f3ebd73`)。

由于 `1Pi` 远超标准服务器节点（通常为 GB 级别）的物理内存上限，该资源声明属于不可实现的配置，导致 Pod 无法进入 `Running` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 29.6s
├─ 并发证据采集: 40.5s
│  └─ g1 aiops-case-v02/workload: 40.5s (Evidence 32.6s, RCA 7.9s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-v02/workload**: pod-pending-unschedulable
