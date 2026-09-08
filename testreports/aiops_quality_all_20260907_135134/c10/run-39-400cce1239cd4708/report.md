## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | {'message': 'k8s.v1.cni.cncf.io/network-status:'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: Error (`fact-7b6830362098`) | 确认应用容器因错误终止，引发重启循环 |
| 2 | K8s State | Kubernetes | `container.last_exit_code`: 137 (`fact-778557af86bf`) | 终止码 137 (128+9) 指向进程被 SIGKILL 信号强制杀死 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory`: 96Mi (`fact-8dd331c4b49d`) | 存在极低的内存硬限制，为 OOMKilled 提供了可能的系统级触发条件 |
| 4 | K8s Event | Kubernetes | `Exit Code: 137` (`fact-a17ed1fa865d`) | 佐证终止原因与系统级信号有关 |
| 5 | K8s Event | Kubernetes | Liveness probe failed: HTTP 500 (`fact-e31b099b6d24`) | 崩溃前网络层出现异常响应，是资源耗尽或应用无响应的前兆 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: 34 (`fact-acb372cf5dae`) | 证实重启频率极高，触发 BackOff 状态 |
| 7 | Logging | Elasticsearch | `event: http_request`, `/work`, `http_status: 200`, `allocated_mib` 记录内全为 0 (`fact-03d2ec45c354` 等) | 崩溃前窗口日志显示应用曾正常响应请求，但日志聚合数据未包含内存增长指标 |
| 8 | Tracing | Tempo/Deepflow | `http.response.status_code: 200`, `duration_us`: 11ms-19ms (`fact-5c8fe5cc8208`, `fact-3f50225a3034`) | 网络流量追踪记录到健康的 GET /work 请求，证明应用进程在崩溃前仍有处理能力 |

**证据印证与冲突：**
*   **现象一致性**：K8s 状态（137 退出码、Error 终止）与 Metrics（高重启计数）和 Events（Liveness 500）共同指向一个突然终止的应用进程。
*   **证据缺口**：Tracing 和 Logging 显示崩溃前有正常的 HTTP 200 响应，未直接捕获到 OOM 报错或应用内部的 panic；且 Logging 聚合数据中 `allocated_mib` 恒为 0，说明崩溃瞬间的内存指标未被有效记录或采样未覆盖该峰值，无法直接证实是 OOM 还是其他 SIGKILL 源。

## 🎯 根因分析 · g1

### 因果链

```text
应用异常终止 (exit 137 / SIGKILL) → Liveness Probe 失败 (HTTP 500) → BackOff 触发重启 → Pod 状态 CrashLoopBackOff
```

### 根因结论

**证据不足**。

尽管终止码 137 (SIGKILL) 和内存限制 96Mi 强烈暗示 **OOMKilled** 的可能性，但现有证据无法区分 **OOM Killer 系统级干预** 与 **应用内部调用 syscall 自我终止**（如检测到内存泄漏主动退出）。日志与链路追踪中缺乏崩溃瞬间的系统级报错（如 OOMKiller 日志）及内存峰值指标，且 Liveness Probe 的 500 错误可能是崩溃前的假死现象而非直接原因，因此决定性事实缺失。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 14.5s
├─ 并发证据采集: 67.1s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 67.1s (Evidence 55.6s, RCA 11.4s)
└─ 汇总总结: 12.5s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
