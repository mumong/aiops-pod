## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | Pod aiops-case-v13/workload 处于 Terminating 状态，尚未完成资源清理 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod 条件 | `Ready=True` (06:40:04), `ContainersReady=True` (06:40:04) [fact-64ab942a078d, fact-c620d862ed4a] | 证明容器在终止前已正常启动并就绪，排除了启动失败导致的异常终止。 |
| 2 | K8s State | Pod 阶段 | `phase: Running` [fact-7519a762bb07] | 反映观察窗口内 Pod 的实际运行状态与 Terminating 现象的矛盾，暗示底层容器进程未被 Kubelet 强制杀死。 |
| 3 | Logging | 日志消息 | 06:40:03 "application started" -> 06:40:05 "SIGTERM received; waiting" [fact-01503b72de10, fact-e31099381f9c] | 提供核心时序证据：应用接收到 SIGTERM 后进入等待状态，未主动退出。 |
| 4 | Metric | 重启计数 | `kube_pod_container_status_restarts_total = 0` [fact-ec8b1c3ff304] | 佐证容器未发生非正常崩溃（OOM 或信号退出），处于静默挂起状态。 |

**证据分析：**
日志 [fact-e31099381f9c] 中 "SIGTERM received; waiting" 与 K8s 状态 [fact-7519a762bb07] 中 Pod 仍显示 Running 但处于 Terminating 形成关键印证。结合重启计数为 0 [fact-ec8b1c3ff304]，说明容器进程捕获了终止信号但被逻辑挂起，而非被 Kubelet 强制 kill 掉（否则状态会变为 Error/CrashLoop）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 收到终止请求（deletionTimestamp 已设置） → 应用捕获 SIGTERM 信号并执行自定义优雅退出逻辑 → 持续阻塞等待外部文件 /state/teardown-requested 创建（文件缺失） → 容器进程挂起导致 Pod 维持在 Terminating 状态
```

### 根因结论

**已确认的根因：** 应用容器的自定义优雅退出逻辑存在阻塞。

**分析依据：**
日志 [fact-e31099381f9c] 明确记录了 "SIGTERM received; waiting"，且重启计数 [fact-ec8b1c3ff304] 为 0，表明容器没有退出，而是进入了死锁或长等待状态。结合现象，这是应用等待一个不存在的外部依赖（如文件）导致的优雅终止超时。正式 RCA 指出该逻辑等待 `/state/teardown-requested` 文件，该文件的缺失直接导致了当前 Pod 无法完成资源清理。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 16.4s
├─ 并发证据采集: 50.4s
│  └─ g1 aiops-case-v13/workload: 50.4s (Evidence 41.3s, RCA 9.0s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
