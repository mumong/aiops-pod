## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | aiops-case-v08/workload Pod 处于 CrashLoopBackOff 状态，容器 app 反复退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s API | `container.last_exit_code: 127` | 确认应用进程因“未找到命令”直接崩溃退出 |
| 2 | Logging | ElasticSearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 捕获到进程启动失败的明确错误，支撑 Root Cause |
| 3 | K8s State | K8s API | `container.waiting_reason: CrashLoopBackOff` | 展示容器因反复异常退出进入重启退避状态 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` (current: 11, window: 6-11) | 量化了 CrashLoopBackOff 导致的频繁重启现象 |

**证据说明：**
K8s 层面的 exit code 127（事实 #1）与日志中的 `not found` 报错（事实 #2）完全一致，共同锁定了“可执行文件缺失”为直接崩溃原因。Metric 提供的 11 次重启（事实 #4）解释了为何 K8s 当前处于 CrashLoopBackOff 状态（事实 #3）而非立即 Restarting。

## 🎯 根因分析 · g1

### 因果链
```text
镜像中缺少 /opt/app/unavailable-command 文件 → 容器启动执行 command 'sh -c exec /opt/app/unavailable-command' 失败 → 容器进程以 exit code 127 退出并进入 CrashLoopBackOff → Pod 状态持续为 CrashLoopBackOff
```

### 根因结论
已确认根因为镜像中指定的可执行文件 `/opt/app/unavailable-command` 不存在。该文件的缺失导致应用容器无法启动，进程以 `exit code 127`（命令未找到）退出，进而触发 Kubernetes 的 CrashLoopBackOff 机制 [事实 #1, #2, #3]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 20.8s
├─ 并发证据采集: 44.1s
│  └─ g1 aiops-case-v08/workload: 44.1s (Evidence 33.6s, RCA 10.4s)
└─ 汇总总结: 6.9s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
