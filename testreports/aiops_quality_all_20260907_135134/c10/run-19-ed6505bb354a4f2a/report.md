## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | Pod aiops-case-10/workload-79d9f8fd88-bwqhh 处于 CrashLoopBackOff 状态，重启20次。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Container `app` Exit Code: 137, Last Reason: `Error` | 确证进程被系统 OOM Killer 强制终止 |
| 2 | K8s State | Kubernetes | Pod Phase: `Running`, Condition `ContainersReady/Ready`: `False` (`ContainersNotReady`) | 确证容器当前处于崩溃重启中 |
| 3 | Metric | Prometheus | `container_memory_working_set_bytes` 峰值: `15540224` bytes (~14.7MB) | 呈现内存占用随运行时间单调增长的趋势 |
| 4 | K8s Config | Kubernetes | Container Memory Limit: `96Mi`, Request: `24Mi` | 提供容器资源边界配置背景 |

日志中显示 HTTP 请求成功完成，但无法观察到应用侧具体的异常报错或内存分配堆栈；Tracing 数据（Tempo/Deepflow）亦主要记录正常的 HTTP 200 响应，未捕捉到 OOM 发生时刻的特异性链路标记。结合 Exit Code 137 与内存持续增长的事实，判定根因为资源限制下的 OOM Kill，但应用内存持续增长的具体模式（如是否存在 Leak）因日志未捕获关键错误而证据不足。

## 🎯 根因分析 · g1

### 因果链

```text
应用内存持续增长 (Peak ~15.6MB) → 触发 OOM Killer (Exit Code 137) → 容器非正常退出 → Kubernetes 重启容器导致 CrashLoopBackOff
```

### 根因结论

已确认根因为：容器 `app` 因内存占用持续增长，最终达到或逼近系统/配置限制时触发了 Linux OOM Killer（Exit Code 137），导致容器崩溃并进入 CrashLoopBackOff 状态。
*   证据支撑：K8s State 报告退出码 137 及 Error 状态【#1】，Prometheus 监控记录显示 `container_memory_working_set_bytes` 随重启呈现单调增长趋势【#3】。
*   已知局限：输入中未包含能够解释内存为何持续增长的具体应用级错误日志或 Tracing 异常，因此“应用是否存在内存泄漏”这一导致持续增长的前置成因证据不足。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 16.9s
├─ 并发证据采集: 102.9s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 102.9s (Evidence 93.4s, RCA 9.4s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
