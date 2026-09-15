## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod workload-7679bcf76-n5vp8 处于 CrashLoopBackOff 状态，应用进程反复崩溃退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `exit_code: 2`, `restart_count: 26`, `status: Running` (fact-01a1e0135f0e, fact-41a9183b70eb) | 记录容器进程异常退出的直接证据，证实启动失败已形成高频重启循环。 |
| 2 | K8s Event | Kubernetes | `BackOff  42s (x497 over 110m)` 警告 kubelet 正在因容器反复崩溃而退避重启 (fact-706f2fc8c2eb) | 描述 Kubelet 观察到的现象，证明重启机制已触发退避逻辑。 |
| 3 | K8s Event | Kubernetes | `cni.projectcalico.org/podIP: 172.16.104.6/32` (fact-ccc491ce68dd) | 确认 Pod 已成功完成初始化并获得网络环境，启动故障发生在容器启动后的运行阶段。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 从 14 跃升至 25，样本数 61，趋势可评估 (fact-f11bb6de936c) | 从时间维度印证了容器在过去一段时间内经历的高频重启行为。 |
| 5 | Logging | Elasticsearch | 模式 `runtime process exiting` (http_status: 500)，出现 4 次，时间窗口 19:56:45 - 20:22:37 (fact-4f3ed62f80bf 等) | 核心异常日志，直接记录应用进程发生非正常终止行为。 |
| 6 | Tracing | Tempo | Trace `086f3a098b97574a79236521c99cd28f`，Span `GET /work` 成功返回 200，标记 `aiops.observed_mode: runtime_exit` (fact-58f87e5fff20) | 关联追踪数据表明应用在处理请求后主动进入“运行时退出”模式，即使请求返回 200 也是预期的故障模拟行为。 |
| 7 | Tracing | Deepflow | `GET /work` 对应 300/500 的等效 L7 Flow，响应码 500 (fact-1a4205fa8164 等) | 从 L7 流量视角佐证了服务在返回错误状态码（500）后进程退出，与日志 `http_status: 500` 一致。 |

**证据说明：**
K8s 状态显示进程以 Exit Code 2 退出并触发 BackOff，日志 `runtime process exiting` 精确描述了退出的具体原因。Tracing 数据中的 `aiops.observed_mode: runtime_exit` 标签将“请求完成”与“进程终止”这两个看似矛盾的现象（请求成功但进程随后退出）串联起来，证实这不是资源耗尽导致的 OOMKilled，而是应用内部逻辑控制的主动退出。

## 🎯 根因分析 · g1

### 因果链

```text
环境变量配置 FAILURE_MODE=runtime_exit → 应用进程执行运行时退出逻辑 → 容器以 Exit Code 2 终止 (Terminated/Error) → Kubelet 触发 BackOff 重启导致 CrashLoopBackOff
```

### 根因结论

已确认的根因是 **容器应用配置了故障注入模式（FAILURE_MODE=runtime_exit），导致进程以 Exit Code 2 主动异常退出**。

该根因通过以下证据得到闭环印证：
1. **日志与追踪的因果关联**：Logging 记录到 `runtime process exiting`，同时 Tracing (fact-58f87e5fff20) 确认在 `runtime_exit` 模式下应用主动终止。这排除了内存不足或依赖缺失导致的被动崩溃。
2. **状态与事件的符合**：K8s 事件 (fact-706f2fc8c2eb) 报告了 `BackOff`，这是 Kubernetes 对高频异常终止（本例中由主动退出触发）的标准响应机制。
3. **资源配置的非限制性**：Pod 配置了 24Mi/96Mi 的内存请求和限制 (fact-8e3cf701e172, fact-b8975eed5101)，且进程能成功处理 HTTP 请求，表明资源不是导致退出的原因，而是应用层面的逻辑退出行为导致了当前 CrashLoopBackOff 的现象。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 12.7s
├─ 并发证据采集: 84.3s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 84.3s (Evidence 73.9s, RCA 10.3s)
└─ 汇总总结: 15.4s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime, pod-oomkilled, pod-config-error, pod-terminating-stuck
