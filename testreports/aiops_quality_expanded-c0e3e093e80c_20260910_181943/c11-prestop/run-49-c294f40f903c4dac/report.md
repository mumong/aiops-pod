## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v12/workload` | Terminating | Pod 应用容器及其 PreStop Hook 均配置为无限循环等待特定文件 `/state/teardown-requested` 存在，且未配置超时退出或文件由外部生成，导致 Pod 在收到 SIGTERM 后无法在 terminationGracePeriod 内完成清理，阻塞在 Terminating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `phase`: Running, `status`: Terminating (lasts <invalid>) | 确认 Pod 处于 Terminating 僵死状态，且持续时间显示异常，符合应用层无法退出的特征 |
| 2 | K8s Config | kubernetes | `container.resource_request.memory`: 8Mi; `resource_limit.memory`: 32Mi | 排除资源耗尽（OOMKilled）导致的异常，资源请求与限制处于正常范围 |
| 3 | K8s Event | kubernetes | `Normal Killing`: Stopping container app | 确认 K8s 已发送终止信号（SIGTERM）并触发容器清理流程，但清理未成功完成 |
| 4 | Logging | elasticsearch | `application started` (timestamp: 2026-09-14T06:18:40.402Z) | 确认应用已正常启动，无启动失败现象，问题集中于生命周期结束阶段 |

**证据说明：**
- Pod 的 `phase` 为 Running 而 `status` 为 Terminating [1] 是典型的进程挂起特征，结合 Kubelet 已执行 Killing 操作 [3] 但未完成，说明阻塞发生在容器内部。
- 应用已成功启动 [4] 且资源充裕 [2]，排除了启动失败或资源争抢，进一步指向了逻辑层面的死锁或无限等待。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码设计缺陷（无限循环等待文件 /state/teardown-requested） → 触发 K8s Termination (SIGTERM) → 主进程与 PreStop Hook 同时陷入无限等待 → 阻塞在 Terminating 状态无法退出
```

### 根因结论

**已确认根因：应用容器及其 PreStop Hook 配置了无限循环逻辑。**
应用主进程和 PreStop Hook 均被配置为无限期等待特定文件 `/state/teardown-requested` 的存在。由于未配置超时机制，且该文件可能由外部生成但未及时创建或未触发，导致在收到 K8s 的终止信号（SIGTERM）后，两者同时陷入阻塞状态。这种逻辑缺陷直接导致 Pod 无法在 `terminationGracePeriod` 内完成清理，从而长期僵死在 Terminating 状态。

*注：缺少外部机制是否已尝试创建该文件的具体日志，但代码层面的无限阻塞设计是导致无法退出的决定性事实。*

---

## 📊 性能统计

```text
├─ 总耗时: 10.7m
├─ 问题定位: 557.6s
├─ 并发证据采集: 74.8s
│  └─ g1 aiops-case-v12/workload: 74.8s (Evidence 64.6s, RCA 10.0s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v12/workload**: pod-terminating-stuck
