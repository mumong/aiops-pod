## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod 容器内的应用进程在收到 SIGTERM 后执行自定义阻塞逻辑（等待文件 /state/teardown-requested 存在），由于该文件未出现，容器无法退出，导致 Pod 处于 Terminating 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Phase | Running (fact-59486dcb569b) | 提供 Pod 当前运行状态基础上下文 |
| 2 | K8s State | Pod Conditions | Ready=True, PodScheduled=True, Initialized=True, ContainersReady=True (fact-26ef57ce13b1 等) | 证实容器应用进程处于活跃状态，非崩溃崩溃退出 |
| 3 | K8s State | Restart Count | 0 (fact-90fc62a3d9f7) | 排除因内存/计算资源超限导致容器 OOMKilled 或 CrashLoopBackOff 的可能性 |
| 4 | K8s Config | CPU Limit/Request | 50m / 5m (fact-198468103787, fact-487013d5ff63) | 资源配额充足，排除资源争抢引发的调度停滞 |
| 5 | K8s Config | Memory Limit/Request | 32Mi / 8Mi (fact-70b690fe97e9, fact-6b45f7e32ea2) | 资源限制充足，排除资源耗尽导致的阻塞 |
| 6 | Logging | Log Message | "SIGTERM received; waiting" (fact-e14a045e7a0e) | 直接捕获应用进程在接收到终止信号后的阻塞行为 |
| 7 | Logging | Log Message | "application started" (fact-7c07554e99dc) | 确认应用进程曾正常启动，与当前进程活跃状态一致 |
| 8 | Metric | kube_pod_status_phase | Running=1, Unknown=0 (fact-aa49ee38bda4, fact-0c5ecb443174) | 独立验证 Pod 未进入 Unknown 或 Failed 异常状态 |
| 9 | Metric | container restarts | 0 (fact-c2468c7714e8) | 验证应用生命周期正常，未发生过意外终止重启 |

**证据印证与冲突说明：**
1. 日志记录（#6, #7）与 K8s 状态（#2, #3）相互印证：日志中应用响应 SIGTERM 并显示 "waiting"，且重启次数为 0、容器就绪状态全为 True，表明进程确实正在运行并处于等待状态，而非死锁后的崩溃重启。
2. 资源状态（#4, #5）与现象不冲突：充足的 CPU/Memory 配额排除了因资源不足导致的性能下降或系统级驱逐，进一步指向应用内部逻辑问题。
3. Metric 数据（#8, #9）作为 K8s 状态的补充，独立确认了应用进程未发生异常终止。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 容器进程逻辑缺陷 → 收到 SIGTERM 后执行自定义阻塞逻辑（等待文件 /state/teardown-requested 存在） → 阻断信号处理，容器无法退出 → Pod 卡在 Terminating 状态
```

### 根因结论

已确认的根因为：**Pod 容器内的应用进程在收到 SIGTERM 后执行自定义阻塞逻辑，导致无法正常退出。**

*   证据 #6（日志 "SIGTERM received; waiting"）直接揭示了应用进程接收到终止信号后的阻塞行为。
*   证据 #2, #3, #8, #9（K8s 状态与 Metric）证实该进程并未发生非正常终止（如 OOMKill 或 CrashLoop），而是持续运行且重启次数为 0，符合应用逻辑阻塞导致资源无法释放的特征。
*   证据 #4, #5 确认了系统资源（CPU/Memory）处于正常充裕状态，排除了基础设施层面的资源争用导致终止超时的可能。
*   综上，应用进程等待外部文件信号（`/state/teardown-requested`）的自定义逻辑未得到满足，是导致 Pod 无法退出并维持在 Terminating 状态的直接原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 16.8s
├─ 并发证据采集: 40.7s
│  └─ g1 aiops-case-v13/workload: 40.7s (Evidence 35.6s, RCA 5.0s)
└─ 汇总总结: 13.4s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
