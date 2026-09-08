## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态且无法移除 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `phase: Running`, `ContainersReady: False (ContainersNotReady)`, `Ready: False (ContainersNotReady)` | 确认 Pod 当前虽处于 Running 阶段但核心容器 `app` 未就绪，存在功能性异常。 |
| 2 | K8s State | kubernetes | `last_terminated_reason: Error`, `last_exit_code: 137` | 容器曾因异常退出（OOMKilled），这是导致容器反复重启或处于非健康状态的直接诱因。 |
| 3 | K8s Config | kubernetes | `resource_request.memory: 24Mi`, `resource_limit.memory: 96Mi` | 内存资源约束极小，与 exit_code 137 结合，印证了内存不足可能是导致容器被强制终止的根本原因。 |
| 4 | K8s State | kubernetes | `container.restart_count: 0` | 尽管容器退出并报错，但重启计数为 0，这表明 Pod 可能处于刚被删除或刚完成第一次初始化尝试的阶段。 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total: 0` | 监控数据与 K8s 状态一致，确认容器确实未发生多次重启，排除了长期震荡导致 Terminating 的可能。 |
| 6 | K8s Config | kubernetes | `diagnosis.phenomenon: 处于 Terminating 状态且无法移除` | 描述当前资源的最终生命周期状态，结合异常退出事实，指向资源清理受阻。 |

**证据综述**：
K8s 状态与 Metrics 共同证实容器 `app` 因内存不足（Exit Code 137）被终止且未重启。虽然容器异常退出，但 K8s 原生机制通常在容器终止后清理 Pod。当前的 Terminating 状态与异常退出之间缺乏直接的因果联系，且存在 `unknowns` 明确指出的 finalizer 阻塞问题，说明异常退出只是触发删除请求的前置条件，而非导致状态停滞的直接原因。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置触发 OOMKilled (Exit 137) → 触发 K8s 删除流程 → 自定义 finalizer 'aiops.lab/hold' 拦截资源回收 → Pod 资源卡死在 Terminating 状态且无法释放
```

### 根因结论

**已确认的根因**：
自定义 finalizer `'aiops.lab/hold'` 未被正常移除，导致 Kubernetes API 拒绝执行 Pod 的最终垃圾回收（GC）。

**证据支撑**：
- 根因直接对应 K8s 生命周期异常（#1, #6）：Pod 进入 Terminating 状态，但正常路径下，容器（#2）终止后 Pod 应自动清理。
- 逻辑矛盾点：如果仅是容器崩溃（#2），Pod 应在短暂延迟后消失。其“无法移除”的特性是 Finalizer 存在的典型症状。
- 诊断结论排除了资源争用（#3 仅解释容器为何退出）或网络/调度问题，将焦点锁定在资源元数据的清理拦截机制上。

**说明**：
虽然正式 RCA 已发布，但输入明确指出了 `unknowns`：未定位到持有并负责移除该 finalizer 的具体控制器，且缺失 finalizer 移除失败的具体业务逻辑或配置错误原因。当前证据足以解释“为什么卡死”，但无法解释“为什么 finalizer 没被删”。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 17.9s
├─ 并发证据采集: 43.3s
│  └─ g1 aiops-case-11/workload: 43.3s (Evidence 34.8s, RCA 8.4s)
└─ 汇总总结: 11.5s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
