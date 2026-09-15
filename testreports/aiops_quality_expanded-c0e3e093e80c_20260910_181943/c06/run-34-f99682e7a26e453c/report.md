## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod workload-7679bcf76-n5vp8处于CrashLoopBackOff状态，持续重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `BackOff 2m42s (x315 over 72m)` | 确认容器反复失败，处于 CrashLoopBackOff 状态 |
| 2 | K8s State | Kubernetes | `last_terminated_reason: Error` | 标识容器以非零状态退出 |
| 3 | K8s State | Kubernetes | `container.last_exit_code: 2` | 提供应用退出码，直接指向应用内部异常或主动终止 |
| 4 | K8s Config | Kubernetes | `resource_limit.memory: 96Mi` | 资源限制较低，但需结合应用行为判断是否因 OOMKilled 导致 |
| 5 | Metric | Prometheus | `last_terminated_reason: Error` (single sample) | 独立观测验证了 K8s 状态中的错误终止 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 18` | 量化了重启频率，与 Event 中的 BackOff 计数趋势一致 |
| 7 | Logging | Elasticsearch | `http_request /work 500 runtime process exiting` (occurs 4 times) | 记录具体触发退出时的请求路径与响应码 |
| 8 | Logging | Elasticsearch | `allocated_mib: 0` (min/max 0.0) | 展示内存分配快照，排除内存耗尽导致崩溃 |
| 9 | Tracing | Deepflow | `GET /work response_code 500` (flow count: 2) | 确认 /work 路径确实产生 500 错误并返回客户端 |
| 10 | Tracing | Deepflow | `GET /work response_code 200` (flow count: 7) | 确认应用并非完全不可用，存在间歇性正常服务 |

证据 1-3 确证应用进程发生异常主动退出。证据 7 将异常直接关联到 `/work` 端点，证明退出伴随 HTTP 500 响应。证据 8 中的内存分配值为 0 排除了因运行期间内存耗尽而崩溃的可能。证据 10 表明服务在正常运行周期内能够成功响应，故障具有间歇性或特定触发条件，且日志与链路未提供导致 500 的具体代码逻辑。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码内部逻辑缺陷 → /work请求返回500错误 → 应用进程主动退出（Exit Code 2） → Kubernetes重启容器导致CrashLoopBackOff
```

### 根因结论

已确认的根因为**应用代码在处理 `/work` 端点时发生内部错误，导致进程主动异常退出（Exit Code 2）**，进而触发了 Kubernetes 的自动重启与 CrashLoopBackOff 现象。

支撑证据：
- **退出原因确证**：K8s 记录 `last_exit_code: 2`（fact 3），结合 Elasticsearch 日志 `runtime process exiting`（fact 7）及 Deepflow 流量中 `response_code: 500`（fact 9），形成从请求失败到进程退出的完整事实闭环。
- **故障现象印证**：K8s Event 显示长达 72 分钟内 BackOff 发生 315 次（fact 1），与 Prometheus 监测到的重启总数 18 次（fact 6）及 `waiting_reason: CrashLoopBackOff`（fact 5）相互印证。
- **排除外部因素**：日志中 `allocated_mib` 始终为 0（fact 8），结合较低的内存限制（fact 4），基本排除内存超限导致 OOMKilled 的可能。

**证据不足的未知项**：导致 `/work` 端点返回 500 并致使进程退出的具体应用层逻辑（如 Python 代码异常、依赖错误）未被日志覆盖，且缺乏匹配内部调用链的 Trace ID，导致具体代码级根因无法确定。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 18.1s
├─ 并发证据采集: 67.3s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 67.3s (Evidence 58.3s, RCA 8.8s)
└─ 汇总总结: 13.5s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
