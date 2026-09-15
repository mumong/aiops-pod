## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v04/workload` | ContainerCreating | Volume mount failure due to missing Secret 'unavailable-input' |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `FailedMount` - `secret "unavailable-input" not found` (fact-1c604d9c3cc7) | 指出容器挂载卷时因 Secret 不存在而失败 |
| 2 | K8s Event | Kubernetes | `timed out waiting for the condition` (fact-671e7ab2535d) | 描述 kubelet 因依赖资源缺失导致的超时现象 |
| 3 | K8s State | Kubernetes | `containers with unready status: [app]` (fact-2d1d7577f19e) | 直接状态：应用容器不可用 |
| 4 | K8s State | Kubernetes | `phase: Pending` (fact-6a5a1e206578) | Pod 处于挂起状态，无法调度至运行期 |
| 5 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 值为 1，标签 `reason: ContainerCreating` (fact-076f3856d195) | 确认应用容器处于等待状态，验证了异常现象 |
| 6 | K8s Config | Kubernetes | CPU Limit: 50m, Memory Limit: 32Mi (fact-6a5a1e206578) | 排除资源限制导致容器启动缓慢的可能性 |

**证据说明：**
1. Kubernetes Event (fact-1c604d9c3cc7) 明确指出 `secret "unavailable-input" not found`，这是导致 `FailedMount` 的直接原因。
2. 状态 `Pending` (fact-6a5a1e206578) 与等待原因 `ContainerCreating` (fact-076f3856d195) 互相印证，表明容器因前置依赖（Secret）缺失而无法进入 `Running` 阶段。
3. 资源配置（Fact-6a5a1e206578, Fact-8fe49f8c0258）正常，排除资源不足导致的调度失败或 OOM。

## 🎯 根因分析 · g1

### 因果链

```text
缺失 Secret 'unavailable-input' → 挂载卷失败 (FailedMount) → 容器状态为 ContainerCreating → Pod 处于 Pending 状态
```

### 根因结论

**已确认的根因：**
Pod 中挂载卷 `input` 所需的 Secret `unavailable-input` 不存在于集群中，导致 kubelet 挂载失败 (K8s Event, fact-1c604d9c3cc7)。这直接导致应用容器 `app` 无法启动，始终停留在 `ContainerCreating` 状态 (Metric, fact-076f3856d195)，进而使 Pod 整体处于 `Pending` 状态 (K8s State, fact-6a5a1e206578)。

证据充分，无需进一步排查。

---

## 📊 性能统计

```text
├─ 总耗时: 58.0s
├─ 问题定位: 19.5s
├─ 并发证据采集: 28.3s
│  └─ g1 aiops-case-v04/workload: 28.3s (Evidence 24.4s, RCA 3.7s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-v04/workload**: pod-volume-mount-failed, pod-pending-unschedulable
