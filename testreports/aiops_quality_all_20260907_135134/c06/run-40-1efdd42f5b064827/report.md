## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | {'message': 'Annotations:      cni.projectcalico.org/containerID: 47db51232873ac00e8b8528cfe9e09ea63ff24eb4542a57d46baeaaa4e019ace'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff 14m (x406 over 103m) kubelet Back-off restarting failed container app in pod workload-7679bcf76-jwr8b...` | 证实异常持续存在且重启间隔拉长 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason: Error`, `last_exit_code: 2`, `restart_count: 24` | 确认应用容器反复异常退出 |
| 3 | Logging | Elasticsearch | `pattern: runtime process exiting`, `http_status: 500`, `path: /work`, `occurrence_count: 4`, `time_range: 13:44 - 14:05` | 确认在 `/work` 请求时发生应用级致命错误 |
| 4 | Tracing | Deepflow | `flow: HTTP GET /work response_code: 500`, `src_ip: 172.16.104.59`, `dst_ip: 172.16.104.52` | 网络层面确认 `/work` 接口返回 500 错误 |
| 5 | Tracing | Tempo | `trace_id: 130bdd4836bc750bcf687e89b717aebe`, `http.response.status_code: 200`, `aiops.observed_mode: runtime_exit` | 关联日志成功，确认请求处理完成后发生退出行为 |
| 6 | Metric | Prometheus | `container_oom_events_total: 0`, `sample_count: 209` | 排除因 OOM 导致退出的可能 |
| 7 | K8s Config | Kubernetes | `resource_request: cpu 20m, memory 24Mi`, `resource_limit: cpu 200m, memory 96Mi` | 资源配额极低，但无 OOM 证据，提示可能与内存管理逻辑有关 |

**证据关系说明：**
- 日志中 `runtime process exiting` (E#3) 与 Deepflow 的 500 HTTP Flow (E#4) 互为因果，表明应用先收到请求报错，随后内部进程崩溃。
- Tempo 链路 (E#5) 为 200 状态且带有 `runtime_exit` 标记，说明 HTTP 响应已发出（或请求已处理完毕），但随后进程立即终止，印证了 E#2 中的 exit_code 2。
- 尽管资源限制非常低 (E#7)，但 OOM 计数器 (E#6) 长时间为 0，证明退出并非由 K8s 的 OOM Kill 机制触发，而是应用内部异常。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理 /work 请求时触发内部逻辑错误 → 进程未捕获致命异常或主动调用 Exit(2) → 容器停止并返回错误码 2 → K8s CrashLoopBackOff
```

### 根因结论

**证据不足**。

现有证据已确认为**应用层异常**而非基础设施故障（如 OOM 或节点问题）：
1.  明确排除了内存溢出：Prometheus OOM 计数器 (E#6) 在较长观察窗口内始终为 0。
2.  锁定了故障场景：日志 (E#3) 和链路 (E#4, E#5) 一致表明，应用在响应 `/work` 接口时发生内部崩溃（`runtime process exiting`）。

但缺乏以下**决定性事实**来定义具体根因：
- 缺少应用崩溃时的**堆栈跟踪 (Stack Trace)** 或具体的**错误消息详情**（日志中仅有 `runtime process exiting`）。
- 缺少与特定**输入数据**或**资源状态**相关的关联分析，无法判断是否由特定请求参数引起。
- 无法确认应用退出 (Exit Code 2) 是否与健康检查机制或其他依赖服务有关。

因此，只能定性为“应用内部致命错误导致进程退出”，无法精确定位到具体的代码逻辑或依赖错误。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 37.3s
├─ 并发证据采集: 83.2s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 83.2s (Evidence 71.1s, RCA 11.9s)
└─ 汇总总结: 14.1s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime, pod-oomkilled
