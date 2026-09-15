## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v03/workload` | Pending | aiops-case-v03/workload 处于 Pending 状态且持续 FailedScheduling |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod `aiops-case-v03/workload` | phase: Pending; condition PodScheduled status: False, reason: Unschedulable (`fact-ae92e9e067dd`, `fact-ce2046afa2fd`) | 直接观测到 Pod 调度失败的最终状态 |
| 2 | K8s Event | default-scheduler | `FailedScheduling`: `0/3 nodes are available: persistentvolumeclaim "unavailable-claim" not found` (`fact-44b2b645e18c`) | 定位调度失败的具体原因为引用了不存在的 PVC |
| 3 | K8s Config | Pod container `app` | resource requests: cpu=5m, memory=8Mi; limits: cpu=50m, memory=32Mi (`fact-bc3966a56fd5`, `fact-d04e09148443`, `fact-1982ab48f7eb`, `fact-5128f0a29858`) | 证明资源请求极低，排除资源耗尽导致调度失败的可能 |
| 4 | Metric | kube_pod_status_phase | phase=Pending: value=1 (sample_count=1); phase=Succeeded: value=0 (sample_count=1) (`fact-faa0856ea18c`, `fact-7d8c7495a35b`) | 确认 Pod 尚未启动，排除已崩溃或已完成的情况 |
| 5 | Tool Error | kubectl describe | `persistentvolumeclaims "unavailable-claim" not found` (command_failed) (`failed_tool_attempts`) | 外部验证了 PVC 确实不存在于当前环境中 |

**证据综合说明：**
1. **状态一致性**：K8s 事件（证据2）与 Pod 状态（证据1）高度一致，均指向 `Pending` 状态下的 `FailedScheduling`。
2. **因果验证**：K8s 事件明确指出缺失 `unavailable-claim`，且通过工具失败记录（证据5）二次确认了该 PVC 确实未被创建。
3. **排除干扰**：资源请求极低（证据3）结合调度器返回的特定错误信息（证据2），排除了节点资源不足的可能性；Metric（证据4）仅作为状态确认，无额外趋势信息。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 声明了不存在的 PVC 'unavailable-claim' → 调度器无法找到/绑定存储卷 → Pod 持续处于 Unschedulable (Pending) 状态 → 业务应用未启动
```

### 根因结论

**已确认根因**：Pod `aiops-case-v03/workload` 的 YAML 配置中引用了名为 `unavailable-claim` 的 PersistentVolumeClaim，但该 PVC 在当前 `aiops-case-v03` 命名空间中不存在，导致 Kubernetes 调度器无法为其绑定存储资源，从而引发持续的 `FailedScheduling` 错误。

**证据支撑**：
- **核心事实**：调度器事件明确指出 `persistentvolumeclaim "unavailable-claim" not found`（证据2），`kubectl` 执行结果确认该 PVC 确实不存在（证据5）。
- **辅助事实**：Pod 状态确认为 `Pending` 且 `Unschedulable`（证据1），且资源请求极低（证据3），进一步排除了资源争抢等复杂因素。

**当前未知**：PVC 缺失的确切原因（如部署遗漏或上游清理导致）需结合部署历史或配置仓库确认。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 42.1s
├─ 并发证据采集: 41.3s
│  └─ g1 aiops-case-v03/workload: 41.3s (Evidence 33.4s, RCA 7.8s)
└─ 汇总总结: 12.0s
```

📋 Runbook 参考

- **g1 aiops-case-v03/workload**: pod-pending-unschedulable
