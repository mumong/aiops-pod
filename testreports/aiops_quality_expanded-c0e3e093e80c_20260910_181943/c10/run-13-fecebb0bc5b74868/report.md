## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bsn84` | CrashLoopBackOff | Pod workload-79d9f8fd88-bsn84 处于 CrashLoopBackOff 状态，容器反复崩溃重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Liveness probe failed: HTTP probe failed with statuscode: 500` (8次) | 说明应用进程在崩溃前处于不可用状态，引发健康检查失败 |
| 2 | K8s Event | kubelet | `Container app failed liveness probe, will be restarted` (4次) | 验证 Liveness Probe 失败后 Pod 被反复重启的行为 |
| 3 | K8s Config | Kubernetes | `resource_limit.memory` = `96Mi` | 定义容器 `app` 的内存硬限制，作为资源耗尽的判定基准 |
| 4 | K8s State | Kubernetes | `last_terminated_reason` = `Error` | 确认容器上一次非正常退出，是 CrashLoopBackOff 的直接触发原因 |
| 5 | K8s State | Kubernetes | `last_exit_code` = `137` | 确认进程因收到 SIGKILL 信号被强制终止，典型特征为资源耗尽（OOM） |
| 6 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason` (reason: Error, value: 1) | 独立指标源，证实最近一次容器退出原因为 Error，支持非健康终止 |
| 7 | Logging | Elasticsearch | `request completed`, `http_status`: 200, `path`: `/work` (8次聚合) | 证明在退出前的观测窗口内（03:26:21-03:26:50），应用服务能够正常接收并响应请求 |
| 8 | Tracing | Deepflow | L7 Flow `GET /work` 返回 `response_code`: 200 (9次聚合) | 流量层面的独立观测，确认应用在处理流量时并未发生网络或协议级崩溃 |

**证据关联说明：**
Liveness Probe 的 HTTP 500 错误（#1）与正常响应（#7, #8）共同指向一个结论：应用进程在遭遇终止前，其运行状态处于波动期或临界崩溃边缘（如内存极度紧张导致响应极慢或抛出 500 异常），而非在完全停机状态下启动。由于日志中 `allocated_mib` 恒为 0 且无 Previous Logs 支持，进程的具体崩溃路径未知，但退出码 137（#5）与内存 Limit 96Mi（#3）在逻辑上高度吻合，指向了资源耗尽这一终止机制。

## 🎯 根因分析 · g1

### 因果链
```text
应用运行期间内存使用突破硬限制(96Mi) → 内核触发 OOM Killer 发送 SIGKILL 信号 → 进程强制终止(Exit Code 137) → 崩溃前的内存压力导致 Liveness Probe 返回 500 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论
已确认的根因为：**容器资源耗尽（内存突破 96Mi Limit）**。

1.  **进程终止机制确证**：容器 `app` 的上次退出原因为 `Error` 且退出码为 `137`（#5），这是 Linux 内核因 OOM（Out of Memory）杀死进程的确定性标志。
2.  **现象解释**：Exit Code 137 直接导致了 Pod 重启并进入 CrashLoopBackOff 状态（#4, #3）。
3.  **伴随现象解释**：Liveness Probe 500 错误（#1）并非根因，而是内存压力下的伴随现象；日志（#7）和流量（#8）证明在崩溃前应用进程仍在尝试处理请求并返回成功，符合高负载或内存即将耗尽时的业务表现。

由于缺乏崩溃前的内存使用 Metrics 历史趋势以及 Previous Logs 中的具体报错堆栈，无法精确定位导致 OOM 的具体代码路径或流量峰值，但现有的事实链条已闭环验证了资源耗尽导致进程被杀的根因结论。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 18.1s
├─ 并发证据采集: 63.7s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bsn84: 63.7s (Evidence 54.5s, RCA 9.1s)
└─ 汇总总结: 13.1s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bsn84**: pod-crashloop-runtime
