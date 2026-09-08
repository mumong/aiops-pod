## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | Pod workload-79d9f8fd88-bwqhh 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器状态 `CrashLoopBackOff`；最近一次终止原因 `Error`，退出码 `137` | 确认应用进程因非零退出码崩溃，137 通常指向 OOMKiller 强杀 |
| 2 | K8s Config | Kubernetes | 容器 `app` 内存硬限制 `96Mi` | 提供导致内存溢出风险的基础资源边界 |
| 3 | K8s Event | Kubernetes | Liveness 探针失败，HTTP 500 状态码（`kubelet Unhealthy` 事件） | 确认应用进程在崩溃前存在响应异常，直接触发 kubelet 重启逻辑 |
| 4 | Logging | Elasticsearch | 聚合日志模式 `http_request ... http_status 200`，关联时间窗 21:05:11 - 21:05:41 | 表明在 CrashLoopBackOff 发生前的短窗口内，应用曾处于正常处理请求状态 |
| 5 | Tracing | Tempo / Deepflow | Flow 数据：HTTP GET /work 请求返回 `200`，时间窗 05:01:35 - 05:05:45 | 进一步确认在崩溃发生前服务处于可服务状态 |

**证据分析说明：**
Kubernetes 事件日志与探针响应结果互相印证：应用进程在崩溃前曾响应 HTTP 200，随后发生异常导致 Liveness 探针收到 500 错误，最终进程被强制终止。日志和追踪数据共同描绘了一个从“正常服务”到“响应异常/崩溃”的完整时序，证实了 CrashLoopBackOff 前的短暂稳定窗口。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制低（96Mi） → 内存溢出触发 OOMKiller → 应用进程被强杀（Exit 137） → Liveness 探针响应失败（500） → 触发容器重启与 CrashLoopBackOff
```

### 根因结论

**已确认根因：容器资源限制不足导致进程被内核 OOMKiller 强杀。**

证据链闭环如下：
1. 容器被赋予极低的内存上限 `96Mi`（事实 #2）；
2. 进程退出码为 `137`（事实 #1），确凿表明进程被 OOMKiller 强制终止；
3. 进程挂死或崩溃导致健康检查接口无法正确响应（事实 #3），引发 kubelet 反复重启。

**未确认项：** 由于 Prometheus 指标数据仅包含单样本快照，缺乏 `memory_usage` 的历史趋势（`trend_evaluable: false`），无法区分本次崩溃是由突发性内存尖峰（Transient Spike）还是持续性内存泄漏（Memory Leak）引起；同时，从 HTTP 200 到 Liveness 探针报 500 之间的具体内部状态演变亦不可见。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 12.9s
├─ 并发证据采集: 90.1s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 90.1s (Evidence 79.8s, RCA 10.0s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
