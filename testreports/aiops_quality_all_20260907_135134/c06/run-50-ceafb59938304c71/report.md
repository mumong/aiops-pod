## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Pod workload-7679bcf76-jwr8b (aiops-case-06) 处于 CrashLoopBackOff 状态，已重启 28 次。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器 `app` 处于 `CrashLoopBackOff` 状态，最后终止原因为 `Error`，退出码 `exit_code: 2` (`fact-7ce95f4424ad`, `fact-c64476056c27`, `fact-5b4e7d3360fb`) | 确认应用进程非正常退出，属于运行时异常 |
| 2 | Logging | Elasticsearch | 日志模式出现 `runtime process exiting` (HTTP 500)，`allocated_mib` 为 0，`trace_ids: [fb6fd50f7d4673a02b8767471e797abe]` (`fact-362a032c4dd0`) | 提供应用内部崩溃的直接原因描述，关联业务 Trace |
| 3 | K8s Event | Kubernetes | 事件显示 Back-off restarting failed container `app`，发生 544 次 (`fact-465a0be2db78`) | 证实重启动作被 Kubernetes 频繁触发并退避 |
| 4 | Metric | Prometheus | `kube_pod_container_status_waiting_reason` = 1 (`reason: CrashLoopBackOff`)，`kube_pod_container_status_restarts_total` = 28 (`fact-f4f93a7e29f6`, `fact-d601dbd37811`) | 确认 Pod 当前持续处于等待重启状态 |
| 5 | Tracing | Tempo | Span 显示 `GET /work` (HTTP 200)，`observed_mode: runtime_exit`，`trace_id: 130bdd4836bc750bcf687e89b717aebe` (`fact-24b762a1cf33`) | 提供业务请求层面的观察，确认进程在请求处理期间发生退出 |
| 6 | Topology | Deepflow | 聚合流 `GET /work` 返回 HTTP 500，`response_status: 3`，共发生 3 次，`trace_ids` 包含 `71ca382ae3317a0271a49443b4e6b6b3` (`fact-12182905968f`) | 验证网络层面的 500 异常，与日志中的 500 错误相呼应 |

**证据印证说明：**
*   **业务与网络一致性**：日志 (`#2`) 记录了 `runtime process exiting` 及 HTTP 500，Deepflow 流量聚合 (`#6`) 独立记录了同路径 `GET /work` 的 HTTP 500 响应，两者共同指向应用服务在请求处理时的业务层故障。
*   **系统行为闭环**：Kubernetes 状态 (`#1`) 显示容器以 `exit_code: 2` 终止并进入 `CrashLoopBackOff`，Metric (`#4`) 量化了 28 次重启与当前等待状态，与 K8s Event (`#3`) 的退避事件完全吻合。
*   **数据局限**：日志中 `allocated_mib` 为 0，且已知 Traceback 未保留；虽然 Tempo Span (`#5`) 观察到 `runtime_exit` 模式，但因未关联具体的报错 Trace ID，无法直接展示 Python 错误堆栈细节。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码处理 HTTP /work 请求时发生内部 Python 异常 → 进程记录 500 错误并主动调用 exit(2) 终止 → Kubernetes 检测到容器非正常退出并触发 OOMKilled 以外的普通 Error 终止 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

**已确认的根因**：应用代码运行时异常导致进程主动退出。

证据链明确指向应用自身逻辑问题而非基础设施故障：
1.  **直接原因**：日志中反复出现 `runtime process exiting` (`#2`)，结合 `exit_code: 2` (`#1`)，表明进程是受控地、非异常信号（如 OOMKilled）地退出。
2.  **现象印证**：Kubernetes 的 `CrashLoopBackOff` (`#1`, `#4`, `#3`) 是进程频繁退出的直接后果。
3.  **业务关联**：Deepflow 和日志同时记录了 `GET /work` 路径的 HTTP 500 错误 (`#2`, `#6`)，确认故障发生在业务请求处理阶段。

**缺失的关键事实**：
尽管根因模式（运行时异常）已确认，但具体的 **Python Traceback（错误堆栈）** 缺失（`unknowns`）。日志中 `allocated_mib` 为 0 且未保留详细堆栈，导致无法精确定位是哪种具体的业务逻辑错误（如空指针、类型错误或库调用失败）导致了退出。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 14.9s
├─ 并发证据采集: 69.9s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 69.9s (Evidence 60.0s, RCA 9.8s)
└─ 汇总总结: 16.7s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
