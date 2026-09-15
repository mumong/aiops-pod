## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v09/workload` | CrashLoopBackOff | Pod `aiops-case-v09/workload` 容器 `app` 处于 `CrashLoopBackOff` 状态，重启 17 次。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: Error (fact-29766f372b49) | 确认进程非正常退出 |
| 2 | K8s Event | kubernetes | `Back-off restarting failed container app` (fact-ae9eba85572b) | 确认重启机制触发 |
| 3 | Logging | elasticsearch | `FileNotFoundError: [Errno 2] No such file or directory: '/input/app.conf'` (fact-3fb4dc88620e) | 提供进程崩溃的直接堆栈与缺失路径证据 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 16 (fact-8d1e08e9d21b) | 从指标侧确认高频率重启现状 |

**证据关系说明：**
Kubernetes 侧的 `CrashLoopBackOff` 事件（#2）与 Metric 侧的高重启计数（#4）共同确立了“频繁重启”的现象。Logging 侧提供的 `FileNotFoundError` 精确指出了崩溃原因（#3），与 `last_terminated_reason: Error` 的 K8s 状态（#1）完全吻合，形成了从“进程代码报错”到“容器重启”的完整证据闭环。

## 🎯 根因分析 · g1

### 因果链

```text
挂载卷 input 未提供文件 'app.conf' → 启动命令执行 Path('/input/app.conf').read_text() 抛出 FileNotFoundError → 进程以 Exit Code 1 终止 → 触发 Always 重启策略导致 CrashLoopBackOff
```

### 根因结论

**已确认的根因：**
应用程序启动逻辑中存在文件读取依赖，具体为执行 `Path('/input/app.conf').read_text()`（证据 #3）。由于部署配置中对应的 `input` 卷未正确挂载配置文件，导致文件不存在。进程因无法读取必需配置抛出 `FileNotFoundError` 并立即退出，从而引发持续重启循环（证据 #1, #2, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 15.1s
├─ 并发证据采集: 38.2s
│  └─ g1 aiops-case-v09/workload: 38.2s (Evidence 29.1s, RCA 9.0s)
└─ 汇总总结: 7.5s
```

📋 Runbook 参考

- **g1 aiops-case-v09/workload**: pod-crashloop-runtime
