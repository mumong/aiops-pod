## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v13/workload` | Terminating | 应用自定义信号处理逻辑阻塞优雅退出，导致 Pod 在 grace period 耗尽前无法终止 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Event | `Warning Unhealthy... Readiness probe failed: command "python3 -c import os; assert os.path.exists('/proc/1/status')" timed out` | 证实应用主进程处于挂起或阻塞状态，无法响应探针请求。 |
| 2 | K8s State | K8s Event | `Normal Killing Stopping container app` | 表明 kubelet 已发送终止信号，进入终止流程。 |
| 3 | Logging | Log | `SIGTERM received; waiting` | 提供核心证据：应用接收到 SIGTERM 后未退出，而是主动进入了等待状态。 |
| 4 | Logging | Log | `application started` | 证实应用此前已成功启动并运行。 |
| 5 | K8s State | K8s Config | Container Resource Limits: `cpu: 50m`, `memory: 32Mi` | 资源限制极低但属于合理配置范围，非导致挂起的主因。 |
| 6 | K8s Event | K8s Event | `cni.projectcalico.org/podIP: 172.16.104.27/32` | 网络配置正常。 |
| 7 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 0` | 验证无历史重启记录，排除 OOM/Killed 导致的反复重启。 |
| 8 | K8s State | K8s State | `pod.status: Terminating (lasts <invalid>)` | 确认 Pod 当前的异常滞留状态。 |

**证据印证说明：**
事实 1 和 事实 3 形成逻辑闭环：日志明确记录应用捕获 SIGTERM 后进入 `waiting` 状态，这直接导致事实 1 中探针检查 `/proc/1/status` 时超时。事实 2 表明底层 kubelet 仍按预期发送终止请求。事实 8 和事实 7 排除了其他故障模式（如重启循环或崩溃），确证这是一个由于应用代码逻辑阻塞引起的挂起问题。

## 🎯 根因分析 · g1

### 因果链

```text
应用捕获 SIGTERM 并执行自定义信号处理逻辑 → 应用进入无限等待循环（非预期行为） → kubelet 的终止请求未被进程退出响应 → Pod 卡在 Terminating 状态且 Readiness Probe 超时
```

### 根因结论

已确认的根因为：**应用自定义信号处理逻辑阻塞优雅退出**。

*   **证据编号**：事实 3 (Logging: `SIGTERM received; waiting`)、事实 1 (K8s Event: `Readiness probe failed... timed out`)。
*   **分析**：应用代码逻辑在接收到 SIGTERM 信号后未执行正常的清理和退出动作，而是陷入了等待状态（通常如等待外部文件或信号），导致容器进程未响应 kubelet 的优雅退出请求。
*   **未决事项**：关于 grace period (3900s) 结束后 kubelet 是否会强制 kill 该进程，当前证据不足以确认，需观察更长时间窗口。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 18.0s
├─ 并发证据采集: 32.1s
│  └─ g1 aiops-case-v13/workload: 32.1s (Evidence 23.7s, RCA 8.4s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-v13/workload**: pod-terminating-stuck
