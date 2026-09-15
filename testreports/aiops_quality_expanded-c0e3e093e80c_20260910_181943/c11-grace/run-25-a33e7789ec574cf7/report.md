## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod workload 处于 Terminating 状态，但尚未完成终止 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase: Running` | 证明应用进程在 Terminating 状态下仍保持活跃 |
| 2 | K8s State | kubernetes | `terminationGracePeriodSeconds: 3900` | 定义 Pod 退出的最大宽限期，解释为何长期滞留 |
| 3 | Logging | elasticsearch | `SIGTERM received; waiting` | 确认应用已收到终止信号但正在等待特定条件 |
| 4 | Logging | elasticsearch | `application started` | 确认应用启动无异常，退出问题仅发生于终止阶段 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total: 0` | 排除因应用崩溃重启导致的异常终止现象 |

证据逻辑说明：
1.  **状态与现象印证**：K8s 报告 Pod 为 Running，但逻辑上处于终止流程，结合日志中的 `SIGTERM received`，确认应用已捕获终止信号但未退出（证据 1, 3）。
2.  **排除重启干扰**：Metric 显示重启次数为 0，说明进程未发生异常崩溃，而是处于正常的等待退出状态（证据 5）。
3.  **超时根源定位**：结合 `terminationGracePeriodSeconds: 3900` 及应用等待特定文件的行为，可锁定是等待逻辑导致了长达 3900 秒的终止阻塞（证据 2, 3）。

## 🎯 根因分析 · g1

### 因果链

```text
外部触发终止但未设置卸载信号文件 /state/teardown-requested → 应用层 SIGTERM 处理器阻塞在 while not Path('/state/teardown-requested').exists() 循环 → Kubernetes 等待 terminationGracePeriodSeconds (3900s) 超时 → Pod 处于 Terminating (等待期) 状态
```

### 根因结论

已确认的根因是：**应用优雅退出逻辑强依赖文件 `/state/teardown-requested`，但上游未创建该文件，导致 Pod 在 3900 秒的 terminationGracePeriodSeconds 宽限期内无限等待 SIGTERM 处理结束。**

*   **已确认环节**：应用已收到 `SIGTERM`（证据 3），但进入特定等待逻辑未退出（证据 3, 1），且无重启异常（证据 5）。
*   **未确认环节**：上游触发终止的控制器或 API 调用为何未创建 `/state/teardown-requested` 文件。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 24.3s
├─ 并发证据采集: 40.1s
│  └─ g1 aiops-case-v13/workload: 40.1s (Evidence 31.1s, RCA 8.8s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
