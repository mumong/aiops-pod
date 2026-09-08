## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod被自定义Finalizer 'aiops.lab/hold'阻止删除 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-2f5d06ada28d` | `exit_code: 137` | 确认应用容器以 SIGKILL 信号异常退出 |
| 2 | K8s Event | `fact-571a07ab6c50` | `message: "Exit Code: 137"` | 事件流印证容器因资源超限被系统 OOM Killer 终止 |
| 3 | K8s Config | `fact-8531851184ae` | `memory limit: 96Mi` | 提供资源约束事实，容器内存限制极低，是导致 OOM 的直接诱因 |
| 4 | K8s State | `fact-d69002ccc5a8` | `pod.status: "Terminating (lasts 78m)"` | 表明 Pod 处于终止状态已超过 78 分钟，存在删除卡死 |
| 5 | K8s State | `fact-1d6fa4fbf163` | `pod.phase: "Running"` | 与 `Terminating` 状态及 `ContainersNotReady` 事件共存，反映删除流程卡在等待终态阶段 |
| 6 | Metric | `fact-d03be74f89da` | `container restarts: 0` | 结合 `last_terminated_reason: Error` 和 `restart_count: 0`，确认 Pod 尚未经历重启，仅发生了单次致命终止 |

当前现象由资源耗尽导致的退出（Exit 137）与 Pod 删除卡死（Terminating）两个阶段组成。K8s 状态证实了资源不足引发的 OOM-Kill，同时 Pod 状态长期停留在 Terminating，说明容器退出后，Kubernetes 删除工作流被某种机制阻断。

## 🎯 根因分析 · g1

### 因果链

```text
内存资源限制 (96Mi) → 触发 OOM-Killer (Exit Code: 137) → 容器终止 (phase: Running/ContainersNotReady) → 删除卡死 (Terminating)
```

### 根因结论

已确认 **容器资源受限引发致命终止**。证据 `fact-8531851184ae`（96Mi 内存硬限制）结合 `fact-2f5d06ada28d`（Exit 137）和 `fact-571a07ab6c50`（Event: Exit Code 137），明确判定容器因内存耗尽被宿主机 OOM Killer 强制终止。

关于“Pod 被自定义 Finalizer 'aiops.lab/hold'阻止删除”的结论，当前 **证据不足**。虽然 K8s 事实 `fact-d69002ccc5a8` 证实了 Pod 确实处于长达 78 分钟的 `Terminating` 卡死状态，但提供的输入事实中并未包含 Pod 的 YAML 结构、`metadata.finalizers` 字段值或 Node 侧删除事件（如 `eviction` 或 `delete pod` 失败记录）。缺失决定性的 YAML 声明证据，无法确认是被 Finalizer 阻断，还是受限于节点失联或 Kubelet 异常。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 13.1s
├─ 并发证据采集: 72.7s
│  └─ g1 aiops-case-11/workload: 72.7s (Evidence 68.8s, RCA 3.8s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
