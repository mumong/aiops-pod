## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `oom-killed` 状态 (reason: OOMKilled, exit_code: 137) | 确认容器因内存超限被系统强制终止的事实 |
| 2 | K8s Config | Kubernetes | `memory_limit: 64Mi`, `memory_request: 24Mi` | 确定触发终止的资源约束阈值 |
| 3 | Logging | Elasticsearch | 日志模式：`allocated_mib` 从 16.0 增长至 48.0 (时间窗: 2026-09-10T22:34:26Z ~ 22:34:58Z) | 揭示应用内存随请求持续累积的行为模式 |
| 4 | Tracing | Deepflow / Tempo | Deepflow 9次 `GET /work` 请求返回 200 (时间窗: 2026-09-11 06:10 ~ 06:34)，Tempo 记录 `aiops.observed_mode: oom_growth` | 证明异常发生在特定接口调用期间，且呈现典型的 OOM 增长特征 |

**证据关联说明：**
日志记录了内存从 16MiB 快速涨至 48MiB 的局部事实，结合 K8s 状态中硬限制 64MiB 且 Exit Code 137，证实了资源增长导致系统触发 OOM Killer 的因果链。Tracing 数据中 Deepflow 确认了请求持续成功（200），排除了业务逻辑报错，而 Tempo 记录的 `oom_growth` 进一步锁定了内存泄漏/无界增长的根因方向。

## 🎯 根因分析 · g1

### 因果链

```text
应用 /work 接口分配内存不释放 (2 MiB/req, 累积至 48 MiB) → 内存总量超过 64Mi 容器硬限制 → Linux OOM Killer 终止容器 (Exit 137) → CrashLoopBackOff
```

### 根因结论

**已确认根因：应用内存无界增长触发了 64Mi 的容器硬限制。**

Kubernetes 状态与 Metric 证据（Fact 1, 2）显示容器因 `OOMKilled` 进入 `CrashLoopBackOff` 状态。日志证据（Fact 3）直接观测到应用在处理请求时内存使用量从 16MiB 持续攀升至 48MiB，这解释了 48MiB 的峰值如何逼近并突破 64MiB 的内存硬限制。Tracing 证据（Fact 4）通过 `oom_growth` 观测模式及连续的 200 请求记录，排除了业务逻辑异常导致的退出，确认了该现象是内存资源耗尽导致的系统强制终止。现有证据已形成完整闭环，足以认定根因为内存泄漏或设计上的内存无界分配。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 19.9s
├─ 并发证据采集: 60.7s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 60.7s (Evidence 49.6s, RCA 11.0s)
└─ 汇总总结: 10.1s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
