## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | {'container': 'app', 'reason': 'CrashLoopBackOff'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.last_terminated_reason` | reason: `Error` | 证实容器已非正常终止，存在导致崩溃的终止事件。 |
| 2 | K8s State | `container.last_exit_code` | exit_code: `137` | 进程被强制终止（通常对应 SIGKILL，由 OOMKiller 或 Kubelet 发送）。 |
| 3 | K8s State | `container.waiting_reason` | reason: `CrashLoopBackOff` | 确认当前核心现象：容器反复退出并进入重启等待期。 |
| 4 | K8s Event | `event.message` | `Liveness probe failed: HTTP probe failed with statuscode: 500` | 提供导致 Kubelet 发送 SIGKILL 的直接机制：探测失败。 |
| 5 | K8s Event | `event.message` | `Back-off restarting failed container` | 证实系统正在执行重启背退逻辑，支持 CrashLoopBackOff 状态。 |
| 6 | Metric | `container_memory_working_set_bytes` | first: `3.5MB`, last: `15.6MB` (max: `15.6MB`) | 展示实际内存消耗（约 15MB）与限制（96Mi）之间存在较大余量，降低 OOM 概率，但无法完全排除。 |
| 7 | Logging | `log.message` | `http_request completed (http_status: 200)` (8 occurrences, 22:57:05-22:57:29) | 崩溃前日志显示应用层正常返回 200，与 Kubelet 报告的 500 探测失败存在不一致，阻碍直接因果推断。 |

**证据矛盾与局限：**
退出码 137 指向 SIGKILL，而探测失败（Event #4）是 Kubelet 发送 SIGKILL 的标准原因；但应用日志（#7）显示 HTTP 200，与探测失败不吻合，暗示可能存在 Sidecar、网关或资源饥饿导致的瞬时不可用。由于 `kubectl_logs_grep` 失败且未能获取崩溃瞬间（exit moment）的日志，无法确认是应用本身错误还是探测机制的误报/代理行为。

## 🎯 根因分析 · g1

### 因果链

```text
Liveness Probe HTTP 500 (未确认瞬时不可用原因) → Kubelet 发送 SIGKILL (Exit Code 137) → 容器终止并重启 → CrashLoopBackOff (反复重启循环)
```

### 根因结论

证据不足。

目前的证据仅能证实容器因探测失败被杀并陷入重启循环。虽然退出码 137 暗示 OOM 或强制终止，但 Metric 显示的内存使用量（15MB）远低于限制值（96Mi），使得 OOM 假设缺乏支持。同时，应用日志（返回 200）与 Kubelet 报告的探测失败（500）不一致，且缺乏崩溃时刻的直接日志证据来解释为何探测会失败。因此，无法确定导致探测失败的真正底层原因（如应用不稳定、资源瞬时尖峰、或 Sidecar/网络拦截问题）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 13.4s
├─ 并发证据采集: 97.8s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 97.8s (Evidence 87.4s, RCA 10.3s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
