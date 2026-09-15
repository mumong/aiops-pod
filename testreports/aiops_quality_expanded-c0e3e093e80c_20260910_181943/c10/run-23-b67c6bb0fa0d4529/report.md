## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-48j8r` | CrashLoopBackOff | Pod workload-79d9f8fd88-48j8r 处于 CrashLoopBackOff，容器因 Liveness Probe 失败被终止（Exit 137）。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod 处于 `CrashLoopBackOff`，容器 `app` 最后退出码 `137`，重启 7 次 | 确认容器被系统强制终止，且处于反复重启的死锁循环中 |
| 2 | K8s Event | Kubernetes | Liveness probe 失败返回 `HTTP statuscode: 500`，随后触发 Killing 事件 | 确定容器是被 Liveness 探针诊断失败后杀死的，而非应用自行退出 |
| 3 | K8s Config | Kubernetes | 内存限制 (`limit`) 为 `96Mi`，当前工作集最高 `~15.5MB`，CPU 限制 `200m` | 排除资源（CPU/内存）耗尽导致的 OOMKilled 或调度资源不足 |
| 4 | Metric | Prometheus | 内存使用量（如 `fact-9499544995f6`）在 `4747264` 到 `15425536` 字节间波动 | 内存消耗稳定，证实故障非内存泄漏引起 |
| 5 | Logging | Elasticsearch | 日志仅包含正常的 `http_request` 200 状态，未出现任何 Panic 或 Error 堆栈 | 日志采集窗口内未记录崩溃现场，无法直接定位内部错误栈 |

**证据说明：**
Kubernetes 事件（#2）与退出码（#1）直接证实容器是由 Kubelet 因健康检查失败而强杀；资源配置与监控指标（#3, #4）排除了内存和计算资源不足的可能性；日志（#5）的空白印证了应用崩溃的突然性，进一步指向应用内部未捕获的运行时错误（如 Panic），排除了外部流量压力导致的过载。

## 🎯 根因分析 · g1

### 因果链

```text
应用进程发生未捕获的内部致命错误（如 Panic） → 进程挂起或异常处理，/health Liveness 接口无法响应（或返回 500） → Kubelet 判定 Liveness 失败，发送 SIGKILL 终止容器（Exit 137） → 容器重启后再次进入相同错误状态，呈现 CrashLoopBackOff
```

### 根因结论

**根因：容器内应用进程发生未捕获的内部运行时错误（Runtime Fatal Error）。**

现有证据（#1, #2, #3, #4）构成闭环：Kubelet 报告 Liveness Probe 失败导致容器退出码为 137（被杀），而监控数据（#4）明确排除了资源耗尽（OOM/CPULimit）作为致死原因。这指向应用自身进程因代码层面的致命缺陷（如 Python 的 Panic/Segfault 等）导致服务假死，从而引发探针超时。

**证据不足部分：** 无法确认具体的异常堆栈，因为日志（#5）在崩溃时刻前仅记录了正常的业务请求，缺乏崩溃现场日志以定位具体的错误行或触发代码路径。

---

## 📊 性能统计

```text
├─ 总耗时: 2.7m
├─ 问题定位: 31.2s
├─ 并发证据采集: 123.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-48j8r: 123.0s (Evidence 111.5s, RCA 11.3s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-48j8r**: pod-crashloop-runtime
