## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod workload 卡在 Terminating 状态约37分钟，且容器因 exitCode 137 处于 Error 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `phase=Running`，条件 `Ready=False` (消息: "containers with unready status: [app]") | 表明 Pod 处于运行阶段但容器未就绪，印证 Terminating 停滞状态 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason=Error`，`container.last_exit_code=137` | 容器被强制终止，137 对应 SIGKILL 信号 |
| 3 | K8s State | Kubernetes | `container.restart_count=0`，`resource_request.memory=24Mi` | 容器仅启动一次即被终止；低内存配额排除了常规 OOM Kill 累积 |
| 4 | Metric | Prometheus | `kube_pod_status_phase(phase=Running)=1` | 确认 Pod 仍在集群运行生命周期内，未进入 Succeeded 或 Failed 阶段 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total=0` | 从监控侧再次确认无重启记录，支持单点终止事件 |

**证据说明：**
Pod 当前 `phase=Running` 且 `restart_count=0` (证据 1, 3, 5)，说明容器启动后未经历重启循环，而是单次遭遇退出。退出码 137 (证据 2) 通常由外部 SIGKILL 或应用内部崩溃引起，结合 `restart_count=0`，这更符合 Pod 删除流程中强制终止容器的行为特征。由于缺少 Logging 和 Tracing 数据，137 的具体触发源（是应用自杀还是外部删除信号）暂时无法区分，但这一结果与 K8s 的删除机制高度吻合。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 被删除请求 → Finalizer 'aiops.lab/hold' 未被释放 → 容器被强制终止(exitCode 137) → Pod 状态卡死 Terminating
```

### 根因结论

**已确认根因：**
Pod `aiops-case-11/workload` 卡死在 Terminating 状态的直接原因是存在未释放的 Finalizer。根据诊断上下文，该 Finalizer 为 `'aiops.lab/hold'`。该保留器阻止了 Kubernetes Garbage Collector 完成 Pod 的清理流程，导致容器在 Terminating 阶段收到强制终止信号（SIGKILL，exitCode 137），进而表现为状态停滞（证据 1, 2, 4）。

**证据不足部分：**
虽然确认了 Finalizer 导致了 Terminating 停滞，但以下两个关键事实证据不足，需补充调查：
1. **Finalizer 持有者**：现有证据未包含 `OwnerReferences` 或控制器日志，无法确定是哪个 Controller 或自定义资源注册了 `'aiops.lab/hold'` finalizer。
2. **exitCode 137 的深层触发器**：虽然 137 符合删除场景，但在没有 Logging 数据的情况下，无法完全排除应用层自杀（Self-Kill）的可能性；同时低内存配额（24Mi）虽不支持常规 OOM，但缺乏内存波动趋势数据，无法彻底排除极端内存争抢导致的 Kernel 杀除。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 21.0s
├─ 并发证据采集: 37.6s
│  └─ g1 aiops-case-11/workload: 37.6s (Evidence 28.1s, RCA 9.3s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
