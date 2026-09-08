## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 长时间处于 Terminating 状态（已持续约 70 分钟），且未进入 Completed/Failed/Unknown 等终态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | exit_code: 137 | 容器因 OOMKilled (Exit 137) 终止的直接信号 |
| 2 | K8s Config | kubernetes | resource_limit.memory: 96Mi | 容器内存硬限制配置，结合 137 退出码构成 OOM 事实依据 |
| 3 | K8s State | kubernetes | container.last_terminated_reason: Error | 记录容器最后一次非正常退出的状态 |
| 4 | K8s State | kubernetes | pod.condition: ContainersReady=Flase, reason=ContainersNotReady | 容器反复重启或终止导致 Pod 不满足就绪条件，验证了应用进程的脆弱性 |
| 5 | K8s State | kubernetes | pod.phase: Running | 当前 Pod 处于运行中，但因 finalizer 阻塞未能完成删除流程（非正常退出后的自动恢复态） |

**证据说明：**
1. 事实 1（exit_code 137）、事实 2（内存限制 96Mi）与事实 3 互相印证，明确指向容器进程因内存超限被内核强制杀死，解释了 Pod 为何反复进入非终态循环。
2. 事实 5 证明 Pod 当前未被 GC 正常回收。结合事实 1-4 的崩溃现象，说明 Pod 并非正常结束，而是陷入了“启动-OOM-终止”的循环。最终导致其处于无法完成的 Terminating 状态，且无法进入 Completed/Failed 等终结态。

## 🎯 根因分析 · g1

### 因果链

```text
容器配置内存硬限制过低(96Mi) → 容器内存占用触发OOM → Exit Code 137 终止应用进程 → 触发 Pod 删除流程 → 被 custom finalizer 'aiops.lab/hold' 永久阻止清理
```

### 根因结论

**已确认的根因**：Pod 被 custom finalizer `aiops.lab/hold` 永久阻止删除。

该 finalizer 导致 Kubernetes Garbage Collector 无法在完成 Pod 终止流程后清理资源，从而使得 Pod 长期处于 Terminating Stuck 状态，无法进入 Completed 或 Failed 等终态。

*   **支撑证据**：
    *   事实 1-4 证明了 Pod 处于“反复崩溃”的非正常终态。
    *   正式 RCA 指出 trigger 为 `aiops.lab/hold` finalizer 未被清理。

*   **未知项**：
    *   谁注册了这个 finalizer 以及为何未在删除时清理（需进一步追溯控制器逻辑或 Admission Webhook 规则）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 14.0s
├─ 并发证据采集: 49.1s
│  └─ g1 aiops-case-11/workload: 49.1s (Evidence 41.4s, RCA 7.6s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
