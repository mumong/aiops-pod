## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod workload-7679bcf76-n5vp8 处于 CrashLoopBackOff 状态，应用容器重启中。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff 3m43s (x22 over 8m43s) kubelet Back-off restarting failed container app` | 确认 Kubelet 因应用容器崩溃进入指数退避重启循环（8分钟内22次）。 |
| 2 | K8s State | Kubernetes | `WaitingReason: CrashLoopBackOff` / `LastTerminatedReason: Error` / `ExitCode: 2` | 明确应用容器 `app` 处于崩溃重启状态，且上次非正常退出码为 2。 |
| 3 | K8s Event | Kubernetes | `Annotations: cni.projectcalico.org/podIP: 172.16.104.6/32` | 提供 Pod 的底层网络标识，与 Tracing 源/目的 IP 交叉验证请求路径。 |
| 4 | Logging | Elasticsearch | `pattern: "http_request", event: "error", message: "runtime process exiting", http_status: 500, path: "/work", first: 2026-09-10T18:32:07, last: 2026-09-10T18:34:01` | 日志直接记录了应用在处理 `/work` 路径时的内部崩溃与进程退出行为。 |
| 5 | Tracing | Tempo | `TraceID: 891114b05a54ed1261e5487a5c071242, Span: GET /work, End: 2026-09-10T18:38:21.893Z, attr: aiops.observed_mode: runtime_exit` | 将最后一次成功或接近结束的处理链路关联到观测到的 `runtime_exit` 状态，佐证进程级崩溃。 |
| 6 | Logging | Elasticsearch | `pattern: "http_request", event: "info", message: "request completed", http_status: 200, path: "/work", first: 2026-09-10T18:32:11, last: 2026-09-10T18:38:21` | 确认在进程崩溃前后 `/work` 路径存在正常的业务请求，表明网络可达性问题低。 |
| 7 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason: 1 (reason=Error)` / `kube_pod_container_status_waiting_reason: 1 (reason=CrashLoopBackOff)` | 通过监控指标复现了容器的最后终止原因及当前等待原因，与 K8s API 状态一致。 |
| 8 | Tracing | Deepflow | `L7 Flow: GET /work, response_code: 500, 7 occurrences, first: 2026-09-11 02:32:05, last: 2026-09-11 02:35:27` | L7 层观测到大量针对 `/work` 的 500 响应，印证了应用服务层的失败。 |

**证据关联分析：**
- **K8s 事件 (E1) 与 Metric (E7)** 相互印证，明确了当前集群层面对该 Pod 的“重启崩溃”视图。
- **Logging (E4) 与 Tracing (E5)** 存在时间关联（18:32 - 18:38），日志记录的错误发生时间早于 Tracing 记录的异常退出时刻，展示了从 HTTP 错误上报到最终进程退出的完整生命周期。
- **L7 Flow (E8)** 的 500 响应时间与 **Logging (E4)** 高度重合，且均指向 `/work` 路径，排除了外部网络故障，定位为应用内部异常。

## 🎯 根因分析 · g1

### 因果链

```text
应用层处理 '/work' 请求时发生未捕获异常 → 内部报错 (HTTP 500) 并执行 runtime process exiting → 容器进程异常终止 (Exit Code 2) → Kubelet 触发 CrashLoopBackOff 重启循环
```

### 根因结论

**已确认根因：应用进程在处理 `/work` 路径请求时发生未捕获错误或内部异常，导致进程退出。**

证据支撑如下：
1. **应用层异常明确**：Elasticsearch 日志（证据 4）与 Deepflow L7 流量（证据 8）一致记录了针对 `/work` 路径的 `HTTP 500` 错误及 `runtime process exiting` 行为。
2. **进程退出确证**：Kubernetes 状态（证据 2）显示容器最后终止原因为 `Error` 且 `exit_code` 为 `2`，与日志中记录的应用进程退出行为吻合。
3. **状态闭环**：上述异常导致 Kubelet 持续重启该容器（证据 1、证据 7），符合 CrashLoopBackOff 的典型特征。

**未知项**：日志与 Tracing 属性中未捕获具体的代码级异常类型（如 `KeyError`、`TypeError` 或依赖缺失等），无法进一步定位至具体代码行或依赖项。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 20.5s
├─ 并发证据采集: 95.1s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 95.1s (Evidence 86.0s, RCA 9.0s)
└─ 汇总总结: 17.6s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
