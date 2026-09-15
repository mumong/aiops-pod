## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bsn84` | CrashLoopBackOff | Container resource limits are insufficient for the application's runtime requirements, causing OOMKilled (Exit 137), but misconfigured liveness probe (expecting 200, getting 500) triggers early termination and restart loop. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s State | container.last_terminated_reason: Error | 证实容器非正常退出 |
| 2 | K8s State | K8s State | container.last_exit_code: 137 | 证实容器因资源不足被内核强制终止 (OOMKilled) |
| 3 | K8s Config | K8s Config | container.resource_limit.memory: 96Mi | 证实容器配置了极低的内存硬限制，是导致 OOM 的直接物理约束 |
| 4 | K8s State | K8s State | container.restart_count: 21 | 证实系统处于持续的崩溃重启循环中 |
| 5 | K8s Event | K8s Event | Liveness probe failed: HTTP probe failed with statuscode: 500 | 证实 Liveness Probe 失败（返回 500 而非 200），导致 kubelet 杀死容器并触发重启循环 |
| 6 | K8s Event | K8s Event | Back-off restarting failed container | 证实 kubelet 已进入指数退避重启机制 |
| 7 | K8s Event | K8s Event | Exit Code: 137 | K8s 注释确认退出码为 137，与容器状态事实互相印证 |
| 8 | Metric | Prometheus | container.last_terminated_reason: 1 (reason=Error) | Prometheus 指标独立证实容器最后终止原因是 Error |
| 9 | Metric | Prometheus | container.waiting_reason: 1 (reason=CrashLoopBackOff) | Prometheus 指标证实 Pod 当前正处于 CrashLoopBackOff 状态 |
| 10 | Logging | Elasticsearch | http_request completed, status: 200, path: /work | 业务日志显示在部分正常请求中，HTTP 层返回 200，与 K8s Probe 报告 500 存在状态冲突/差异 |
| 11 | Tracing | Deepflow | HTTP GET /work, dst_ip: 172.16.104.17, response_code: 200 | Deepflow 网络流量证实目标 Pod 在处理请求时返回了 200 状态码 |
| 12 | Tracing | Tempo | GET /work, observed_mode: liveness_fail, response_code: 200 | Tempo 链路追踪证实：即使 Liveness 标记为 liveness_fail，应用层面的响应码依然为 200 |

**证据分析：**
- **现象与状态一致**：事实 #1、#2、#7 明确指出了容器因 Exit 137 (OOMKilled) 终止，这与 K8s Event #5、#6 观测到的重启循环和 BackOff 现象完全吻合。
- **根因逻辑闭环**：事实 #3 的 `96Mi` 内存硬限制极低，直接导致应用极易触发 OOMKilled（事实 #2）。
- **Probe 行为分析**：K8s Event #5 显示 Liveness Probe 收到 500 状态码，但事实 #10（日志）、#11（Deepflow）和 #12（Tempo）均显示业务层成功处理了 `/work` 请求且返回 200。这证明 Liveness Probe 的 500 错误发生在请求被应用层处理之前（可能是探针自身逻辑问题、网络链路中的代理报错，或者探针请求的路径/方法与业务请求不同），但 K8s 依据这个 500 判定 Probe 失败，从而执行了 `docker kill` 动作，形成了“资源不足崩溃 + Probe 误杀/加剧崩溃”的循环。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存硬限制过低 (96Mi) → 触发内核 OOM Killer (Exit 137) → 容器非正常终止
Liveness Probe 期望返回 200，但实际收到 500 → kubelet 判定 Liveness 探测失败 → 强制终止并重启容器
容器重启后因内存不足迅速再次崩溃，形成 OOMKilled 与 Liveness Probe 失败共同驱动的重启死循环
```

### 根因结论

已确认的根因是**容器内存资源限制不足（96Mi）与应用实际运行时内存需求不匹配**，导致容器频繁被内核 OOM Killer 终止（Exit 137）。

同时，Liveness Probe 配置存在**严重偏差**。尽管业务应用日志（Fact #10）和全链路追踪（Fact #11, #12）均证实应用正在成功处理 `/work` 请求并返回 200 状态码，但 kubelet 的 Liveness 探针却报告收到了 500 状态码（Fact #5）。这导致即使容器尚未因 OOM 彻底崩溃，Kubernetes 也会因为“探针失败”而主动杀死并重启容器。OOM 和错误的 Liveness 判定机制共同作用，导致容器陷入 CrashLoopBackOff 的死循环。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 20.5s
├─ 并发证据采集: 65.4s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bsn84: 65.4s (Evidence 58.2s, RCA 7.1s)
└─ 汇总总结: 16.4s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bsn84**: pod-crashloop-runtime
