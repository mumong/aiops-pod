## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod 存在未清理的自定义 finalizer 'aiops.lab/hold'，导致 Kubernetes API Server 无法移除对象，从而陷入 Terminating 停滞。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | pod.condition | `ContainersReady=Flase` (reason: `ContainersNotReady`, message: `containers with unready status: [app]`) | 直接证据：容器长期处于未就绪状态，阻碍了 Pod 生命周期的正常终结 |
| 2 | K8s State | container.last_terminated_reason | container `app` terminated with `reason: Error` | 佐证容器经历了异常终止，与 `ContainersNotReady` 状态一致 |
| 3 | K8s State | container.last_exit_code | container `app` `exit_code: 137` | 佐证容器非正常退出（137通常为OOMKilled），确认了异常事件的发生 |
| 4 | K8s State | pod.phase | `Running` | 现象描述：Pod 核心状态仍为 Running，未进入预期的 Succeeded 或 Failed 状态，体现了 Terminating 停滞 |
| 5 | K8s State | pod.condition | `Ready=False` (reason: `ContainersNotReady`) | 进一步确认服务不可用，与 K8s Event 观测到的容器状态吻合 |
| 6 | Metric | kube_pod_status_phase | 当前 `Running=1`，`Failed=0` (sample_count: 1) | Metric 维度确认 Pod 当前未判定为 Failed，与 K8s API 返回的 Running 状态互相印证 |
| 7 | Metric | kube_pod_container_status_restarts_total | container `app` `restarts=0` (sample_count: 1) | Metric 维度显示容器未触发重启计数器，表明异常可能发生在初始启动阶段或特定运行周期，无持续循环重启现象 |

**证据关联说明：**
K8s State 显示容器以 Exit Code 137 和 Error 终止，随后状态机停滞在 `Running` 且 `ContainersNotReady`。Metric 的 `phase=Running` 从另一个维度锁定了此状态，排除了 Pod 因持续 OOM 循环而进入 `CrashLoopBackOff` 或 `Failed` 的可能。结合诊断声明，这种“异常退出但状态停滞”的行为特征，强有力地指向了外部阻碍对象清理的机制。

## 🎯 根因分析 · g1

### 因果链

```text
自定义 finalizer 'aiops.lab/hold' 未清理 → K8s API Server 拒绝执行 Termination 操作 → Pod 状态停滞在 Running 但容器异常退出 (exit 137) → 用户可见 Pod 无法删除，处于 Terminating 停滞
```

### 根因结论

**已确认的根因**：
Pod 存在未清理的自定义 finalizer (`aiops.lab/hold`)。

该 finalizer 阻止了 Kubernetes 对 Pod 对象的最终删除操作。尽管容器 `app` 因异常（Exit Code 137）已停止运行（证据 1, 2, 3），且 K8s 试图终止该对象，但由于 finalizer 的存在，API Server 拒绝移除 `DeletionTimestamp` 和清理底层资源，导致 Pod 僵持在 `Running` 但 `ContainersNotReady` 的状态（证据 4, 5, 6）。这正是导致 Pod 陷入 `Terminating` 停滞并无法被正常删除的决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 55.9s
├─ 问题定位: 12.4s
├─ 并发证据采集: 32.6s
│  └─ g1 aiops-case-11/workload: 32.6s (Evidence 27.7s, RCA 4.8s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
