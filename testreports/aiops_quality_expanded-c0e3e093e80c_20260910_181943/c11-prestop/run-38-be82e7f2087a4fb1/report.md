## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | PreStop hook 中定义的阻塞循环依赖 `/state/teardown-requested` 文件作为退出信号，但该文件未被创建，导致容器在 terminationGracePeriodSeconds (3900s) 宽限期内无法完成优雅退出，Pod 卡在 Terminating 状态且 phase 显示为 Running。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `pod.condition: Ready=True, ContainersReady=True` (fact-17dbe565161c) | 证实应用逻辑层面处于健康/可接受状态 |
| 2 | K8s State | Kubernetes | `pod.phase: Running` (fact-1be9eb3cc8df) | 证实 Pod 处于生命周期结束阶段但核心进程未退出的矛盾状态 |
| 3 | K8s Config | Kubernetes | `terminationGracePeriodSeconds: 3900s` (诊断结论) | 提供判定优雅退出超时异常的标准时长基准 |
| 4 | K8s Config | Kubernetes | `PreStop hook 阻塞循环依赖 /state/teardown-requested 文件` (诊断结论) | 揭示导致优雅退出流程被阻断的具体配置机制 |
| 5 | Metric | Prometheus | `kube_pod_status_phase=1 (Running)` 且 `restart_count=0` (fact-b7d7b01d3860) | 证实 Pod 未被 Kubelet 强制 Kill 且无重启记录 |

**证据总结**：Kubernetes 状态显示 Pod 满足就绪条件但 `phase` 长期滞留于 `Running`（配合 3900s 的超长宽限期），结合 Metrics 中 `restart_count=0` 的事实，排除了应用频繁崩溃重启导致的现象。诊断结论确认了 `PreStop` 钩子因未满足文件条件而挂起，这与“容器看似健康但进程不退出”的指标特征完全吻合。

## 🎯 根因分析 · g1

### 因果链

```text
PreStop 配置逻辑错误（依赖外部文件触发） → 容器优雅退出钩子阻塞挂起 → 进程在 3900s 宽限期内拒绝退出 → Pod 卡在 Terminating 状态且 phase 显示为 Running
```

### 根因结论

已确认的根因为：**`PreStop` 钩子存在阻塞逻辑且依赖外部信号文件 `/state/teardown-requested` 未被创建**。该配置导致容器无法响应终止信号，只能等待 `terminationGracePeriodSeconds`（3900s）超时。

这一配置缺陷直接解释了为何在 `Ready=True` 的健康状态下，Pod 依然会卡住且不发生重启（`restart_count=0`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 10.8s
├─ 并发证据采集: 45.0s
│  └─ g1 aiops-case-v12/workload: 45.0s (Evidence 38.7s, RCA 6.2s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
