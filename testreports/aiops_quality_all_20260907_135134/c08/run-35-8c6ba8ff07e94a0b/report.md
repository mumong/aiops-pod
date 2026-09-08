## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | RecentRestart | Pod workload-5c9c7b6489-wmjhr 处于 CrashLoopBackOff 状态，容器 app 频繁重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container `app` 终止原因 `OOMKilled`，当前状态 `CrashLoopBackOff`，重启计数 `21` | 证实容器因内存超限被强制终止且处于崩溃循环 |
| 2 | K8s State | Kubernetes | 容器最近退出码 `137` | 137 (128+SIGKILL) 是 Linux OOM Killer 强制杀进程的标志性信号 |
| 3 | K8s Config | Kubernetes | `app` 容器的 Memory Limit 硬限制为 `64Mi`，Request 为 `24Mi` | 提供判定 OOM 的关键容量阈值 |
| 4 | Logging | Elasticsearch | `/work` 端点请求日志中 `allocated_mib` 字段在观察窗口内从 `12` 增加到 `34` (max: 34, min: 12) | 显示应用在处理请求时存在显著的内存递增分配行为 |
| 5 | Tracing | Tempo | Span `66fac7b7a0afef02099280b3ed1689de` 显示 `/work` 请求在 `oom_growth` 模式下运行 | 从 Trace 维度独立印证了应用代码的内存增长特征 |

证据链表明：应用在执行 `/work` 请求时发生内存分配（Logging/Tracing 证据 #4, #5），其峰值需求逼近或超过 Pod 配置的 64 MiB 硬限制（K8s Config #3），进而导致内核 OOM Killer 介入并发送 SIGKILL（Exit Code 137，K8s State #2），最终引发 `OOMKilled` 事件与 `CrashLoopBackOff`（K8s State #1）。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码在 /work 端点执行递增式内存分配（Logging/Tracing 观察到 allocated_mib 增加） → 累积内存使用量超过容器 Limit（64 MiB，K8s State #3） → 触发 Linux OOM Killer 终止进程（OOMKilled, Exit Code 137，K8s State #2） → Kubelet 重启失败进入 CrashLoopBackOff（K8s State #1）
```

### 根因结论

**已确认根因**：容器 `app` 在处理 `/work` 请求时，因代码逻辑执行内存分配操作，导致内存消耗超过了 Pod 配置的 Memory Limit（`64Mi`），触发系统 OOM Killer 强制终止进程，从而产生频繁重启。

该结论由多维度事实交叉印证：
1. **资源限制**：K8s 配置明确记录内存硬限制为 64 MiB（#3）；
2. **崩溃信号**：Exit Code 137 与 `OOMKilled` 状态证实了系统级资源保护机制的触发（#1, #2）；
3. **应用行为**：日志记录（#4）与追踪数据（#5）共同证实了应用在处理请求时存在明确的内存增长行为。

---

## 📊 性能统计

```text
├─ 总耗时: 9.9m
├─ 问题定位: 13.7s
├─ 并发证据采集: 571.6s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 571.6s (Evidence 559.6s, RCA 11.8s)
└─ 汇总总结: 10.8s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-oomkilled, pod-crashloop-runtime
