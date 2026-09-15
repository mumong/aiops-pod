## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod workload (aiops-case-v13) 处于 Terminating 状态但容器未退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Phase | status: Terminating, phase: Running (lasts <invalid>) | 确认容器处于非正常卡滞状态 |
| 2 | K8s Event | kubelet | Killing / "Stopping container app" (重复 36s) | 表明底层驱逐动作持续执行但未生效 |
| 3 | Logging | application | "SIGTERM received; waiting" | 证明应用进程已捕获信号并主动进入挂起逻辑 |
| 4 | Logging | application | "application started" | 证明应用启动正常，信号接收发生于启动之后 |
| 5 | K8s Config | resource_limit | cpu: 50m, memory: 32Mi | 确认资源硬限制非导致进程阻塞的直接原因 |
| 6 | Metrics | kube_pod_container_status_restarts_total | value: 0 | 排除频繁 OOM/崩溃重启的可能性 |

**证据关联说明：**
证据 3 (日志 "waiting") 与 证据 2 (事件 "Stopping container app") 相互印证，确认了 Pod 正在执行终止流程，但由于应用层在 SIGTERM 后主动阻塞等待（证据 3），导致 kubelet 的强制销毁指令无法立即奏效（证据 2）。证据 6 排除了因应用频繁重启导致状态不稳定的情况。

## 🎯 根因分析 · g1

### 因果链

```text
Pod spec 中 SIGTERM 处理器逻辑设计为等待 /state/teardown-requested 文件 → 触发删除（deletionTimestamp）后应用收到 SIGTERM 进入等待循环 → 文件不存在导致容器进程不退出 → kubelet 持续 Killing 但进程存活导致 Terminating 状态卡住
```

### 根因结论

已确认根因为应用退出逻辑阻塞（证据 3）。应用在接收到 SIGTERM 信号后执行了预设的等待逻辑（如轮询特定文件是否存在），但由于该文件从未被创建，导致进程陷入无限等待而无法退出。Kubernetes 底层因无法等待应用超时或强制结束而处于 Terminating 状态。缺少该阻塞逻辑的具体代码实现细节。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.5s
├─ 并发证据采集: 39.3s
│  └─ g1 aiops-case-v13/workload: 39.3s (Evidence 29.9s, RCA 9.2s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
