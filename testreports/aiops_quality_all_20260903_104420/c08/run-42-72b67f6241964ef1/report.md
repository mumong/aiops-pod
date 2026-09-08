## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-fl85h` | CrashLoopBackOff | Pod aiops-case-08/workload-5c9c7b6489-fl85h 持续处于 CrashLoopBackOff 状态，容器频繁退出重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Container `app` terminated with reason: OOMKilled (fact-0696b024a286) | 确定进程被系统强制杀死的直接原因 |
| 2 | K8s State | Kubernetes | Container `app` restart count: 24 (fact-22ed8af9b39e) | 验证故障发生的频率与持续性 |
| 3 | K8s Event | Kubernetes | Exit Code: 137 (fact-d3fea9202bfa, fact-5d254d92f3b9) | 确认 OOM Killer 终止行为（信号 9） |
| 4 | K8s Config | Kubernetes | Container `app` memory limit: 64Mi (fact-0946d2eedc4b) | 提供导致被杀的上限阈值 |
| 5 | Metric | Prometheus | Container memory working set 多次突破 47-51MB，最新达到 53MB，接近 64Mi (fact-3b984558c406, fact-639b26b629e6 等) | 显示内存持续向硬限制增长并逼近红线 |
| 6 | Logging | Elasticsearch | HTTP 请求日志显示 `allocated_mib` 从 10 增加至 48 (fact-50d29dea5a18) | 在应用层证实内存随请求累积增长的模式 |

**证据关联分析：**
Kubernetes 状态确认了 `OOMKilled` 和 Exit Code 137 (编号 1, 3)，结合配置中的 64Mi 限制 (编号 4) 解释了 CrashLoopBackOff 的成因。Metric 数据证实内存工作集在不断攀升 (编号 5)，这与日志中观察到的内存分配累积增长模式 (编号 6) 相互印证，共同指向内存消耗超出限制这一根因。

## 🎯 根因分析 · g1

### 因果链

```text
应用逻辑持续分配内存（allocated_mib 递增） → 容器内存工作集突破 64MiB 硬限制 → Linux OOM Killer 强制终止进程（Exit Code 137） → Pod 持续 CrashLoopBackOff
```

### 根因结论

根因已确认：容器内存使用呈累积增长趋势，最终超过了 `64Mi` 的 `memory limit`，触发 Linux OOM Killer 强制终止进程。

- **证据支撑**：Kubernetes 记录了 `OOMKilled` 状态 (fact-0696b024a286) 和 137 退出码 (fact-5d254d92f3b9)；Metric 显示内存持续逼近上限 (fact-3b984558c406)；日志证实了内存分配随请求增长 (fact-50d29dea5a18)。
- **遗留未知**：现有事实无法区分这是应用代码的内存泄漏（Memory Leak）还是业务逻辑导致的正常临时性内存峰值积累（需结合代码审查或更细粒度内存剖析确认）。

---

## 📊 性能统计

```text
├─ 总耗时: 2.9m
├─ 问题定位: 20.3s
├─ 并发证据采集: 141.0s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-fl85h: 141.0s (Evidence 131.0s, RCA 9.9s)
└─ 汇总总结: 11.3s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-fl85h**: pod-crashloop-runtime, pod-oomkilled
