## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-wmjhr` | CrashLoopBackOff | Pod aiops-case-08/workload-5c9c7b6489-wmjhr 持续处于 CrashLoopBackOff 状态（重启 8 次），容器启动后崩溃。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `container.last_terminated_reason` | `reason: "OOMKilled"` (container: app) | 确认容器是被内核 OOM Killer 强制终止 |
| 2 | K8s Event | `event.message` | `Exit Code: 137` / `Reason: OOMKilled` (累计 8 次) | 佐证每次重启均因内存耗尽被杀，非应用逻辑崩溃 |
| 3 | K8s Config | `container.resource_limit.memory` | `value: "64Mi"` | 提供触发 OOM 的系统资源硬限制阈值 |
| 4 | K8s Config | `container.resource_request.memory` | `value: "24Mi"` | 确认资源请求远低于限制，非调度预留不足 |
| 5 | Metric | `container_memory_working_set_bytes` | 多次采样峰值达 `57536512` (~54.8 MiB)，当前轮次达 `51318784` (~48.9 MiB) (fact-91ab5b16c53d, fact-545e72caa544) | 证实内存使用量随重启循环逐渐攀升并逼近 64Mi 上限 |
| 6 | Logging | `log.message` (pattern: `memory allocation advanced`) | 分配内存从 `12 MiB` 增长至 `48 MiB` (fact-5db2ccba5eec...fact-02a6b74edee4) | 揭示内存增长的直接来源是 `/work` 端点的内存分配行为 |

**证据关联：**
应用日志显示 `/work` 接口在处理请求时内存分配持续增加（12-48 MiB），这与 Prometheus 监控到的容器内存工作集接近 64Mi 限制高度一致；随后 K8s 状态机反复报告 `OOMKilled` 和 `BackOff`，证实内存溢出导致进程被杀并触发重启循环。

## 🎯 根因分析 · g1

### 因果链

```text
应用 /work 端点请求导致内存分配增加 (Logging: 12Mi->48Mi) → 
内存使用量逼近并突破 container.memory limit 64Mi (Metric: 峰值~54.8Mi, Config: 64Mi) → 
Linux cgroup OOM Killer 触发，终止容器 (K8s: OOMKilled, Exit Code 137) → 
Kubelet 执行重启策略，Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

**已确认根因：** 容器 `app` 处理 `/work` 端点时发生内存持续增长（从 12MiB 累积至 48MiB），触发了 Kubernetes 配置的 `memory: 64Mi` 硬限制，导致内核 OOM Killer 发送 SIGKILL 信号终止进程。
- **证据支撑：**
    - 日志直接记录内存分配增加（事实 #6）；
    - 监控显示内存峰值逼近限制（事实 #5）；
    - 配置确认限制值为 64Mi（事实 #3）；
    - 状态反复报告 OOMKilled（事实 #1, #2）。

---

## 📊 性能统计

```text
├─ 总耗时: 3.4m
├─ 问题定位: 19.2s
├─ 并发证据采集: 175.2s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-wmjhr: 175.2s (Evidence 162.8s, RCA 12.2s)
└─ 汇总总结: 11.6s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-wmjhr**: pod-crashloop-runtime
