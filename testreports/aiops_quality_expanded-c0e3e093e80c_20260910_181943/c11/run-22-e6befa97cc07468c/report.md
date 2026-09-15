## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 处于 Terminating 状态无法退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-11/workload` 的 `app` 容器 `last_terminated_reason=Error` | 证实 Pod 容器存在异常退出历史 |
| 2 | K8s State | kubernetes | 容器 `app` 的 `last_exit_code=137` | 证实容器收到 SIGKILL 强制终止信号，排除了进程内部逻辑退出 |
| 3 | K8s State | kubernetes | Pod 状态 `phase=Running`，`ContainersReady` 和 `Ready` 均为 `False`，原因为 `ContainersNotReady` | 描述 Pod 当前的不健康及不可用状态 |
| 4 | K8s Config | kubernetes | 容器资源配置：Request CPU 20m, Limit CPU 200m, Request Memory 24Mi, Limit Memory 96Mi | 提供资源使用基线，但无证据表明触发 OOMKiller 或 CPU Throttling |
| 5 | Metric | prometheus | Pod 删除时间戳 `kube_pod_deletion_timestamp` 记录为 1789098427 (2026-09-11T04:30:10Z) | 确认删除请求已发起，结合当前 Terminating 状态，表明删除流程停滞 |

证据分析：
- **K8s State** 数据明确显示了进程被强制杀死（Exit Code 137）且未发生重启（重启计数为 0）。
- **Metric** 数据确认删除请求的时间点，结合 Pod 持续处于 Terminating 状态，证实 Kubernetes 的 Pod 生命周期管理流程在资源清理阶段发生阻塞。
- 输入中的 **formal_rca** 指出根本原因为 `finalizer 'aiops.lab/hold'` 导致删除流程被 API Server 阻止，上述现象（SIGKILL 后的 Terminating 僵局）与该机制下的预期表现完全一致。

## 🎯 根因分析 · g1

### 因果链
```text
Pod 元数据中存在 finalizer 'aiops.lab/hold' → API Server 拦截资源删除 → Kubelet 收到终止信号但资源未释放 → Pod 进入 Terminating 状态僵局
```

### 根因结论
**根因已确认**：异常由 Kubernetes 的 Finalizer 机制导致。
- **已确认事实**：Pod `aiops-case-11/workload` 处于 `Terminating` 状态，容器 `app` 因 `SIGKILL`（Exit Code 137）被强制终止。
- **机制分析**：根据提供的正式 RCA，Pod 被 finalizer `aiops.lab/hold` 挂起。当执行删除操作时，Kubernetes API Server 因 finalizer 的存在阻止了 Pod 资源的最终释放。Kubelet 成功执行了 Killing 动作，但由于 API 层面的状态未解除，Pod 对象在 Etcd 中无法被清理，导致其长期停留在 Terminating 状态。证据编号 1、2、3 支撑了容器层级的终止现象，结合 RCA 提供的 finalizer 约束，完整解释了资源生命周期停滞的原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 24.9s
├─ 并发证据采集: 39.0s
│  └─ g1 aiops-case-11/workload: 39.0s (Evidence 30.9s, RCA 8.0s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
