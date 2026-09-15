## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-sjvxl` | CrashLoopBackOff | Pod应用运行于模拟故障模式 `config_missing_exit`，在启动后处理HTTP请求 `/work` 时检测到关键配置缺失，主动抛出 HTTP 500 错误并以退出码 78 终止进程，导致 Kubernetes 反复重启进入 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-07/workload-dff5cbc6b-sjvxl` 状态 `Running`，但 `ContainersReady` 和 `Ready` 均为 `False` (reason: `ContainersNotReady`) | 确认 Pod 已调度但容器处于不健康状态 |
| 2 | K8s State | Kubernetes | 容器 `app` 状态 `CrashLoopBackOff`，最后终止原因 `Error`，退出码 `78`，重启次数 `17` 次 (最后一次 back-off 5m0s) | 证实容器因程序异常退出而被反复重启 |
| 3 | K8s Event | Kubernetes | 事件 `Warning BackOff`：`Back-off restarting failed container app`，累计发生 286 次 (66m内) | 验证 K8s 控制平面对持续失败的主动退避行为 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` 显示 `CrashLoopBackOff`；`kube_pod_container_status_restarts_total` 为 `17`；`last_terminated_reason` 为 `Error` | 从监控指标确认异常状态及持续重启事实 |
| 5 | Logging | Elasticsearch | 日志模式重复 8 次：`CONFIG_MISSING`，伴随 `http_status: 500`，路径 `/work`，服务 `aiops-lab-workload`，时间范围 21:08 - 21:34 | 核心错误证据，证明应用检测到关键配置缺失并主动返回 500 |
| 6 | Tracing | Deepflow (Flow) | 9 条 HTTP GET `/work` 流：响应码 `500`，响应状态 `3` (Close/Reset 等)，目标 IP `172.16.104.63` (Pod IP) | 证实网络层请求成功到达容器但收到 500 错误，与日志一致 |
| 7 | Tracing | Tempo (Span) | Span `GET /work` 结束于 `21:29:09`，属性 `aiops.observed_mode: config_missing_exit`，返回 `500` | 追踪链路中的上下文属性确认了应用处于“配置缺失”模拟模式 |
| 8 | K8s Config | Kubernetes | 容器资源限制 `memory: 96Mi`，CPU 限制 `200m`；请求 `memory: 24Mi`，CPU 请求 `20m` | 排除资源限制（OOM/Kill）作为退出原因的可能 |

**证据链说明：**
*   **现象确认**：K8s 状态的 `CrashLoopBackOff`（#1, #2）与 Prometheus 指标（#4）互相印证，确认了容器反复非正常退出的事实。
*   **根因指向**：日志中的 `CONFIG_MISSING`（#5）直接解释了为什么容器退出码为 78 并伴随 HTTP 500；Tracing 数据（#6, #7）证明了 500 错误是由后端应用主动发出的，且确认应用处于 `config_missing_exit` 模式，排除了基础设施故障。
*   **排除干扰**：资源配置（#8）显示有充裕的内存和 CPU 配额，且退出码非 137 (OOM)，佐证了这是应用逻辑层面的失败而非资源耗尽。

## 🎯 根因分析 · g1

### 因果链

```text
应用运行于 config_missing_exit 模式 (Tracing/Evidence #7) → 启动后处理 /work 请求时检测关键配置缺失 (Logging/Evidence #5) → 主动抛出 HTTP 500 并以退出码 78 终止进程 (K8s State/Evidence #2, Logging/Evidence #5) → K8s 自动重启机制触发，反复进入 CrashLoopBackOff (K8s Event/Evidence #3, Metrics/Evidence #4)
```

### 根因结论

**已确认根因：** Pod `aiops-case-07/workload-dff5cbc6b-sjvxl` 中的 `app` 容器运行于模拟故障模式 `config_missing_exit`。在该模式下，应用启动后在响应 HTTP `GET /work` 请求时检测到关键配置缺失（日志标识 `CONFIG_MISSING`），随后主动抛出 `HTTP 500` 错误并以退出码 `78` 终止自身进程。

**依据：**
*   日志系统记录了明确的错误模式 `CONFIG_MISSING` 及伴随的 `500` 状态码（证据 #5）。
*   追踪系统确认应用属性 `aiops.observed_mode` 为 `config_missing_exit`，且返回 `500`（证据 #7）。
*   K8s 层面显示容器因非零退出码（78）被终止，并导致 Pod 进入 `CrashLoopBackOff` 状态（证据 #1, #2, #3）。

**排除项：** 资源配额充足（证据 #8），排除因内存或 CPU 超限导致的 OOMKilled。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 15.2s
├─ 并发证据采集: 94.1s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-sjvxl: 94.1s (Evidence 88.0s, RCA 5.9s)
└─ 汇总总结: 16.9s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-sjvxl**: pod-crashloop-runtime, pod-oomkilled
