## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod 'workload' 存在自定义 finalizer 'aiops.lab/hold'，阻止了 Kubernetes API Server 在容器终止后完成对象删除流程，导致 Pod 处于 Terminating 挂起状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod.phase: `Running` (fact-5a268862cde1) | 确认容器进程仍存活，未发生正常退出的预期行为。 |
| 2 | K8s Event | kubernetes | condition type: `Ready`, status: `False`, reason: `ContainersNotReady` (fact-5f1dacba451e) | 容器异常导致 Pod 健康检查失败，符合被阻塞的异常特征。 |
| 3 | K8s Config | kubernetes | container.resource_limit.memory: `96Mi` (fact-a14e6775cc09) | 提供容器资源环境基线，用于排查是否因资源受限导致进程异常。 |
| 4 | Metric | prometheus | container.restart_count: `0` (fact-a4c7d2d9c042) | 排除因资源耗尽导致 Pod 频繁重启（CrashLoopBackOff）的可能性。 |
| 5 | Metric | prometheus | kube_pod_status_phase (Running): `1` (fact-8874d7600c98) | 独立指标确认 Pod 处于活跃运行状态，与 K8s API 报告一致。 |
| 6 | Logging | elasticsearch | 4 条日志均返回 http_status: 200 (fact-f6128af0681d 等) | 证明应用进程在终止前正在正常处理业务流量，未发生代码级崩溃。 |

**证据总结**：
应用进程在 Pod 生命周期中表现正常（Metric 显示重启 0 次，Logging 显示 200 响应），排除了因 OOM 或业务逻辑错误导致主动退出的情况。结合 K8s 状态显示容器未就绪但 Pod 仍为 Running，且官方诊断报告指出存在自定义 finalizer 阻断删除，证据链共同指向 Pod 因外部配置原因无法完成终止流程（即 Terminating 挂起状态）。

## 🎯 根因分析 · g1

### 因果链

```text
自定义 finalizer 'aiops.lab/hold' 配置 → 容器进程仍存活 → 阻碍 API Server 清理 Pod 对象 → 用户可见 Terminating 状态挂起
```

### 根因结论

根因已确认：Pod 'workload' 配置了自定义 `finalizer: aiops.lab/hold`，该机制强制等待 Pod 被显式释放才能完成删除。由于容器进程处于活跃状态（`phase: Running`，无重启记录），且无相关业务日志表明其正在配合释放，导致 API Server 无法移除该 Pod 对象。此过程排除了常见的 OOMKilled（无 137 退出码）或 CrashLoop 重启现象，属于配置阻塞导致的资源挂起。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 32.8s
├─ 并发证据采集: 29.2s
│  └─ g1 aiops-case-11/workload: 29.2s (Evidence 21.5s, RCA 7.7s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
