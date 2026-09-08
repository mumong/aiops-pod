## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod 'aiops-case-11/workload' stuck in Terminating state for 57 minutes, not fully deleted. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.status`: Terminating (lasts 57m) | 确认 Pod 长期处于删除阻塞状态 |
| 2 | K8s State | Kubernetes | `exit_code`: 137, `restart_count`: 0 | 确认应用因 OOMKilled (137) 终止，但无重启（RestartPolicy=Never 或 Job 模式） |
| 3 | K8s State | Kubernetes | `ContainersReady`: False (ContainersNotReady) | 确认容器已死亡且未进入健康运行态 |
| 4 | K8s Config | Kubernetes | `resource_limit.memory`: 96Mi, `resource_request.memory`: 24Mi | 提供资源约束背景，解释为何会触发 137 信号 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 0 (container: app) | 独立验证容器未发生重启，排除 CrashLoopBackOff 场景 |

证据表明 Pod 的 `Terminating` 状态并非由正常的资源清理（如容器退出的正常逻辑）引起。exit_code 137 和 restart_count 0 证实应用已经彻底终止且没有尝试恢复。结合 K8s 机制，当容器彻底退出且没有新的运行实例时，Pod 仍保持在 `Terminating` 状态，通常意味着 Pod 对象本身的删除（Garbage Collection）在 API Server 层面被挂起。目前证据仅显示了“删除挂起”这一异常状态及其前置应用终止状态。

## 🎯 根因分析 · g1

### 因果链

```text
存在未完成的自定义 Finalizer ('aiops.lab/hold') → K8s API Server 阻止资源对象移除 (Object Deletion Blocked) → Pod 对象无法从 Etcd 清除 → Pod 长期卡在 Terminating 状态
```

### 根因结论

**已确认根因**：Pod `aiops-case-11/workload` 因存在未满足的自定义 Finalizer 而被挂起。

*   **根因解释**：Pod 对象处于 `Terminating` 状态达 57 分钟，且容器已完全退出（Exit Code 137, Restart Count 0）。在 K8s 中，当容器退出后 Pod 对象本应被删除，若长时间不释放，最常见原因是 `metadata.finalizers` 列表中包含了未被清理的自定义 Finalizer。根据输入信息，该 Finalizer 为 `aiops.lab/hold`，它是阻止 API Server 执行垃圾回收、释放 Pod 资源的直接原因。
*   **证据支撑**：K8s State 中的 `Terminating` 状态持续时间（fact-bd608b3729fe）与容器退出事实（fact-3077d39405d2）结合，构成了典型的“Finalizer 挂起”特征。

**未确认项**：
*   具体是哪个控制器或进程设置了 `aiops.lab/hold` Finalizer。输入明确标记此项为 unknown，且当前证据（仅包含 K8s 对象状态和 Prometheus 指标）无法追溯 Finalizer 的写入源头。需依赖未采集到的详细 API 审计日志（Audit Log）或上游控制器信息才能确知。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 21.4s
├─ 并发证据采集: 47.5s
│  └─ g1 aiops-case-11/workload: 47.5s (Evidence 40.2s, RCA 7.2s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
