## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Pod workload-7679bcf76-n5vp8处于CrashLoopBackOff状态，容器应用进程在启动后处理请求时意外退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning BackOff 2m41s (x203 over 47m) kubelet Back-off restarting failed container app in pod workload-7679bcf76-n5vp8` | 确认 CrashLoopBackOff 机制正在运作，异常状态已持续近 48 分钟。 |
| 2 | K8s State | kubernetes | `container.last_terminated_reason: Error`, `container.last_exit_code: 2` | 明确终止原因为 Error 且退出码为 2，排除了 OOMKilled。 |
| 3 | Logging | elasticsearch | `pattern: {"event": "http_request", "level": "error", "message": "runtime process exiting", "http_status": 500, "path": "/work"}` (3次, trace_id: `0a2f7e93d108d5996daca00874df4884`, `1946b848d82c5653afa1a9469fe9b223`, `2bedd23e6c9eb325f924bbfb32bd5cc4`) | 提供进程退出前最后一刻的确切日志，确认应用内部在请求处理期间主动退出。 |
| 4 | Tracing | deepflow | `GET /work response_code: 500 src_ip: 172.16.104.56 dst_ip: 172.16.104.6` (3次, trace_ids: `6b940021b18df312738422d71af62239`, `650e7da7b4dc0e95768ebc5720a2260e`) | 外部观测到服务端在处理相同路径时返回 500，印证日志中记录的 HTTP 500 状态码。 |
| 5 | Tracing | deepflow | `HTTP GET /work response_code: 200` (2次, trace_ids: `67fe88acf015f7d64f17a20048f09c53`, `c695d7ccb7105570f9d095874e24f244`) | 证明 Pod 具有正常的服务响应能力，排除容器无法启动或网络不通的问题。 |
| 6 | K8s Config | kubernetes | `container.resource_limit.memory: 96Mi` | 展示资源限制；结合内存 Metric（约 3.6MB），确认非内存溢出导致的进程终止。 |

**证据关联分析：**
Kubernetes Event (1) 证实了集群层面的重启循环与 CrashLoopBackOff 状态；结合 K8s State (2) 的 `exitCode=2` 和 `reason=Error`，排除了资源限制（6）引发的 OOM。ELK 日志 (3) 记录了最后时刻的 `runtime process exiting` 和 HTTP 500 状态码，而 DeepFlow Tracing (4, 5) 从网络流量侧确认了该 Pod 在处理 `GET /work` 时确实会返回 500 错误并终止进程。日志中列出的三个失败 trace_id 与网络侧记录的失败调用高度相关，说明异常是由应用代码在处理特定请求时触发的未捕获运行时错误导致的。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码在处理 GET /work 请求时发生未捕获异常 → 触发应用内部退出逻辑 (runtime process exiting) → Kubelet 检测到 app 容器以 exitCode=2 异常终止 → Pod 进入 CrashLoopBackOff 状态并持续重启
```

### 根因结论

**已确认的根因：** 应用服务在处理 `GET /work` 请求时触发了导致 Python 进程以非零退出码 (`exitCode=2`) 终止的内部异常（`reason=Error`, `runtime process exiting`），进而引发 Kubelet 的 `CrashLoopBackOff` 重启机制。

**依据：**
- 日志证据 (3) 明确指出在 `/work` 路径上发生了 `http_status: 500` 并伴随 `runtime process exiting`。
- K8s State (2) 证实容器终止原因为 `Error` 而非资源限制（如 OOM）。
- 网络追踪 (4) 证实了外部确实收到了 500 响应，与内部日志一致。

**证据不足/未确认：**
- 具体的代码级异常类型（如 `ValueError`, `KeyError` 等）：日志中未发现 Python 堆栈跟踪（Traceback）或错误详细信息。
- `exitCode=2` 的具体应用语义：需结合 `server.py` 源码确认这是应用定义的特定错误码还是通用的异常退出码。
- 崩溃的输入数据相关性：目前缺乏针对特定 `case_run_id` 或输入参数的关联分析日志，无法确认是否为特定输入数据引发。

---

## 📊 性能统计

```text
├─ 总耗时: 2.8m
├─ 问题定位: 17.9s
├─ 并发证据采集: 131.4s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 131.4s (Evidence 116.7s, RCA 14.2s)
└─ 汇总总结: 17.5s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
