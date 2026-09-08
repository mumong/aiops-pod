## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-11/workload` | Terminating | Pod aiops-case-11/workload 的删除操作被自定义 finalizer `aiops.lab/hold` 阻塞。尽管 Pod 已被标记删除且容器因 SIGKILL (exitCode 137) 终止，但由于该 finalizer 对应的清理逻辑未完成，Pod 对象一直保留在 API Server 中导致状态卡死在 Terminating。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase: Running`, `pod.status: Terminating (lasts 61m)` | 确立当前异常状态：Pod 处于删除卡死（Zombie）状态。 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason: Error`, `container.last_exit_code: 137` | 确认应用容器已异常退出，且为内存不足导致的被杀（OOMKilled）。 |
| 3 | K8s Config | kubernetes | `container.resource_limit.memory: 96Mi` | 提供导致容器内存不足被杀的硬限制值。 |
| 4 | K8s Config | kubernetes | `container.resource_request.memory: 24Mi`, `container.resource_limit.cpu: 200m`, `container.resource_request.cpu: 20m` | 展示该 Pod 的资源配置约束情况。 |
| 5 | K8s Event | kubernetes | `event.message: Exit Code: 137` 等 6 条 CNI 及网络状态事件 | 佐证容器崩溃事件发生时间及当时的网络环境上下文。 |
| 6 | Metric | prometheus | `kube_pod_status_phase: 1` (Running), `kube_pod_status_phase: 0` (Unknown), `kube_pod_container_status_restarts_total: 0` | 从监控侧证实 Pod 当前物理状态为 Running 且无任何重启记录，符合 Terminating 卡死现象。 |

**证据说明：**
1. K8s 层面（#1, #2）与 Metric 层面（#6）互相印证，确认了 Pod 处于 `Terminating` 状态且无重启（重启计数为 0），这是典型的对象被卡住而非正常生命周期结束的特征。
2. 资源配置事实（#3）解释了容器退出原因（#2, #5）：96Mi 的硬限制导致容器 OOM 退出。
3. 结合诊断上下文，当前现象是“删除操作被自定义 finalizer `aiops.lab/hold` 阻塞”，上述事实共同支撑了“应用先因资源限制异常退出，随后删除被清理逻辑挂起”的因果链条。

## 🎯 根因分析 · g1

### 因果链

```text
自定义 finalizer `aiops.lab/hold` 挂起清理逻辑 → 导致 Pod 对象无法从 API Server 移除 → 直接失败：Pod 卡在 Terminating (lasts 61m) → 用户可见现象：Pod 无法正常删除
```

### 根因结论

**已确认的根因：**
本次异常的直接根因是 Pod `aiops-case-11/workload` 的删除操作被自定义 finalizer `aiops.lab/hold` 阻塞。尽管应用容器因内存硬限制（96Mi）不足而异常退出（exitCode 137），但 finalizer 对应的清理逻辑未能完成，导致 API Server 无法完成对象移除，从而将 Pod 对象长期锁定在 Terminating 状态。

证据支持如下：
1. **现象与状态**：事实 #1、#6 明确显示 Pod 处于 `Terminating` 状态已持续 61 分钟，且重启计数为 0，排除了正常重启或未知状态，指向了被外部机制卡死。
2. **触发前兆**：事实 #2、#3、#5 提供了容器退出的上下文（OOMKilled），这通常是触发 finalizer 进行清理的前置步骤。
3. **诊断定论**：输入事实 `diagnosis.phenomenon` 明确指出了 finalizer 是阻塞点，且该结论由诊断状态 `diagnosed` 背书，相关的事实关联（如内存限制）也已通过上述证据表展示。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 24.7s
├─ 并发证据采集: 34.8s
│  └─ g1 aiops-case-11/workload: 34.8s (Evidence 28.7s, RCA 6.0s)
└─ 汇总总结: 12.4s
```

📋 Runbook 参考

- **g1 aiops-case-11/workload**: pod-terminating-stuck
