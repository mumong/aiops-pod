## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | workload-7679bcf76-jwr8b 持续 CrashLoopBackOff (重启24次) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `kubelet` 记录 `BackOff restarting failed container app`，Pod 状态 `CrashLoopBackOff`，重启计数 24 次 (fact-5c9b75807199, fact-b69635fc1e98) | 确定应用容器处于持续崩溃与重启状态 |
| 2 | K8s State | kubernetes | 容器 `app` 最后终止原因为 `Error`，退出码为 `2` (fact-48d1302fc973, fact-2b257f95e786) | 排除 OOMKilled (退出码 137)，指向应用内部逻辑或信号引发的主动退出 |
| 3 | K8s Event | kubernetes | Pod 条件 `ContainersReady` 与 `Ready` 均处于 `False` 状态 (fact-68f1f55a89d7) | 确认应用处于不可用且未就绪状态 |
| 4 | Logging | elasticsearch | 日志模式显示 `runtime process exiting`，`http_status: 500`，发生在处理 `/work` 接口时，且 `allocated_mib` 始终为 0 (fact-1e0bcbeae073) | 提供业务层面直接证据：服务在处理请求时发生 500 错误并主动终止 |
| 5 | Tracing | deepflow | HTTP Flow `GET /work` 对应 `response_code: 500`，且关联到日志中的 Trace ID `6a209b351afca0883d60aa21df483445` (fact-0c9863f20c91) | 链路层面确认请求处理过程中产生了 500 错误响应 |
| 6 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason` 标签为 `Error`，`kube_pod_container_status_waiting_reason` 为 `CrashLoopBackOff`，重启总数 24 (fact-4a6b1a463271, fact-4dbc39b656b5, fact-292f65374130) | 监控系统确认了容器异常终止和重启的具体原因 |

**证据印证说明：**
- 日志 (fact-4) 与链路 (fact-5) 共同指向 `/work` 接口在处理期间发生 500 错误，这解释了容器为何以非零退出码终止。
- 退出码 2 (fact-2) 配合 `runtime process exiting` (fact-4) 证实了是 Python 进程主动退出，而非被系统 OOM 杀死的 137 号信号。
- Kubernetes 状态 (fact-1, fact-3) 与 Prometheus 指标 (fact-6) 均一致反映了 CrashLoopBackOff 的持续发生和重启频率。

## 🎯 根因分析 · g1

### 因果链
```text
应用代码在处理 /work 接口时出现逻辑或依赖异常 → 服务抛出 HTTP 500 状态码并主动终止进程 (exitCode=2) → Kubernetes 检测容器非正常退出并执行重启 → 进入 CrashLoopBackOff 状态，Pod 持续重启 (24次)
```

### 根因结论

**已确认的根因：**
Python 应用程序在处理 `/work` 接口时发生内部异常，导致进程返回 HTTP 500 状态码并主动退出（Exit Code 2）。
- **业务层面**：日志 (fact-4) 明确记录了 `http_status: 500` 且伴随着 `runtime process exiting`。
- **系统层面**：Kubernetes 报告容器以 `Error` 原因终止，退出码为 `2` (fact-2)，且处于 `CrashLoopBackOff` 状态 (fact-1, fact-6)。

**缺失的决定性事实 (证据不足部分)：**
- 无法确认 `/work` 接口返回 500 的**具体业务原因**（如具体的异常堆栈、未找到的资源、配置错误等），因为未采集 previous logs 或 debug 级别的详细日志。
- 无法确认是否存在**上游依赖服务故障**，因为未采集依赖服务的 metrics。

---

## 📊 性能统计

```text
├─ 总耗时: 1.5m
├─ 问题定位: 17.5s
├─ 并发证据采集: 58.5s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 58.5s (Evidence 49.2s, RCA 9.1s)
└─ 汇总总结: 14.8s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
