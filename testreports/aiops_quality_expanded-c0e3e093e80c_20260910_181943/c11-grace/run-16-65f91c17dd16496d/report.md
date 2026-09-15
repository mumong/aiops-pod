## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | 应用代码在接收 SIGTERM 后进入无限循环等待外部信号文件（/state/teardown-requested），且该文件始终未被创建，导致容器无法在 terminationGracePeriodSeconds 内主动退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | Pod `aiops-case-v13/workload` 状态为 `Terminating (lasts <invalid>)` | 证明 Pod 处于终止阻塞状态，未成功退出 |
| 2 | K8s Event | kubernetes | `Normal Killing Stopping container app` (33s前) | 确认 kubelet 已发送 SIGTERM 信号 |
| 3 | Logging | elasticsearch | `SIGTERM received; waiting` (06:59:45.748Z) | 确认应用代码已收到信号并进入等待阻塞循环 |
| 4 | Logging | elasticsearch | `application started` (06:59:44.304Z) | 确认应用启动后仅维持约 1.4s 即进入终止流程 |
| 5 | K8s Config | kubernetes | Container `app` 请求 `5m CPU / 8Mi Memory`，限制 `50m CPU / 32Mi Memory` | 排除资源过载导致的处理延迟，确认为应用逻辑问题 |
| 6 | K8s Event | kubernetes | 5条网络注解记录（如 `PodIP: 172.16.104.7/32`） | 排除网络插件状态异常引发的退出阻碍 |

**证据分析：**
日志记录（#3, #4）直接展示了 Pod 在启动后仅 1.4 秒便收到终止信号，但随后立即陷入阻塞。该现象与 Kubernetes 状态（#1, #2）完全吻合，证实阻塞发生在应用层而非资源层。尽管 Pod 资源限制极低（#5），但由于日志显示是在“接收信号后”等待，而非因资源争抢无法执行退出逻辑，故资源非根因。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 被调度终止 → 发送 SIGTERM 信号 → 应用代码等待外部文件 /state/teardown-requested 创建 → 文件始终未创建导致阻塞 → 容器超时无法退出 (Terminating)
```

### 根因结论

已确认根因为：**应用代码存在缺陷，在接收 SIGTERM 后进入无限循环，死等外部信号文件 `/state/teardown-requested`。**

该根因得到了日志事实 `fact-d9df62ec6e69` 的直接证实（日志显示“收到 SIGTERM 并等待”）。结合当前状态 `Terminating` 及重启次数为 0（`fact-b09d18d367f5`），确认该阻塞发生在当前的终止生命周期内，而非因资源耗尽导致的应用挂起。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 16.7s
├─ 并发证据采集: 38.1s
│  └─ g1 aiops-case-v13/workload: 38.1s (Evidence 31.7s, RCA 6.3s)
└─ 汇总总结: 9.1s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
