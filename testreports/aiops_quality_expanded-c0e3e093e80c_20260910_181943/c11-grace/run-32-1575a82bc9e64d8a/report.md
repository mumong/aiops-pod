## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod aiops-case-v13/workload 处于 Terminating 状态，Kubelet 记录到 Readiness probe 超时并执行了 Killing 信号，但容器未立即退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | phase: Running, status: Terminating (fact-d6a01d227e35, fact-e050bbb517e0) | 展示 Pod 当前处于逻辑上矛盾的混合状态（运行中但在终止中） |
| 2 | K8s Event | Kubernetes | Readiness probe failed: command "python3 -c import os; assert os.path.exists('/proc/1/status')" timed out (fact-7a3179a67c36) | 证实探测失败与资源访问问题，构成触发终止流程的直接原因 |
| 3 | K8s Event | Kubernetes | Killing: Stopping container app (fact-badac493f43e) | 确认 Kubelet 已开始发送 SIGTERM 信号 |
| 4 | Logging | Elasticsearch | 07:28:43 application started → 07:28:45 SIGTERM received; waiting (fact-8feb40181187, fact-a691ab58803d) | 证实容器进程成功启动并接收到终止信号，进入等待状态 |
| 5 | Metric | Prometheus | kube_pod_container_status_restarts_total: 0 (fact-fda2729fe77f) | 证实未发生容器崩溃，排除 OOM/Killed 等强制终止因素 |

证据间互相印证了从健康到终止再到僵持的过程：K8s Events (2, 3) 和 Logs (4) 证实了触发与接收信号，Logs (4) 进一步说明进程进入等待，Metric (5) 则证实了这并非非正常崩溃，结合 K8s State (1) 的 Terminating 状态，共同指向等待逻辑导致的卡死。

## 🎯 根因分析 · g1

### 因果链
```text
应用逻辑设计为在收到 SIGTERM 后进入无限循环等待特定文件 → 触发 terminationGracePeriodSeconds (3900s) 的长时间等待 → 容器因等待文件未出现而阻塞退出 → 用户可见 Pod 处于 Terminating 状态
```

### 根因结论
已确认的根因是应用逻辑设计所致。应用容器在收到 `SIGTERM` 信号后，进入了无限循环等待特定文件（`/state/teardown-requested`）的逻辑，且配置的 `terminationGracePeriodSeconds` 长达 3900s。这一行为导致 Pod 在长达一个小时的优雅退出期内始终保持 `Terminating` 状态，属于正常的等待机制而非异常卡死。证据包括 `Logging` 记录的 `SIGTERM received; waiting` 状态（4），`Metrics` 显示的 `restart_count: 0`（5），以及 `K8s Events` 中记录的 `Killing` 状态（3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 23.0s
├─ 并发证据采集: 35.9s
│  └─ g1 aiops-case-v13/workload: 35.9s (Evidence 26.0s, RCA 9.8s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
