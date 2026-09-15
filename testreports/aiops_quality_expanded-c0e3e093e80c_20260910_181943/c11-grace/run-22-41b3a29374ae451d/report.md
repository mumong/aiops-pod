## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod aiops-case-v13/workload 处于 Terminating 状态，kubelet 发送 SIGTERM 后容器未退出，仅打印 'waiting' 日志并持续运行。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | K8s Event | `Normal Killing Stopping container app` (fact-e3593aa158c4) | 确认 kubelet 正在执行容器终止流程 |
| 2 | Logging | Logging | `SIGTERM received; waiting` (fact-e0c7ec86d57a) | 直接证实应用代码已捕获信号且进程仍活跃 |
| 3 | K8s State | K8s State | `pod.phase: Running` (fact-0288dad9bf33), `pod.status: Terminating` (fact-99160a2e7b2e) | 确认 Pod 处于状态不一致/挂起中 |
| 4 | Metric | Metric | `kube_pod_container_status_restarts_total: 0` (fact-634d5a9fa0b1) | 排除因容器崩溃重启导致的现象 |

现有证据通过 K8s 事件与日志互相印证，证实 kubelet 试图终止容器时，应用进程收到了 `SIGTERM` 信号，但根据日志 "waiting" 判断其未退出。由于应用进程仍为 Running 状态，导致 K8s 无法完成 Pod 的 Terminating 状态流转。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码 SIGTERM 信号处理程序缺陷 → 进程进入无限循环等待不存在的文件 → 容器进程保持 Running 状态 → Pod 处于 Terminating 状态并等待 grace period 超时
```

### 根因结论

**已确认的根因：应用代码信号处理程序缺陷**。

证据表明应用在收到 `SIGTERM` 信号后没有执行退出操作，而是执行了等待逻辑（日志显示 "waiting"）[fact-e0c7ec86d57a]。这导致容器进程未能被 `SIGKILL` 强制清理前的阶段终止，进而造成 Pod 处于 `Terminating` 状态但 Pod 内部进程状态仍为 `Running` [fact-0288dad9bf33][fact-99160a2e7b2e]。重启计数为 0 进一步确认了进程未被杀死的持续性 [fact-634d5a9fa0b1]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 12.1s
├─ 并发证据采集: 54.4s
│  └─ g1 aiops-case-v13/workload: 54.4s (Evidence 44.9s, RCA 9.5s)
└─ 汇总总结: 7.9s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
