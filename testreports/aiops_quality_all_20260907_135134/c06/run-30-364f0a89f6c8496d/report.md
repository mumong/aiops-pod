## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container: app, last_terminated_reason: Error, last_exit_code: 2, waiting_reason: CrashLoopBackOff, pod phase: Running, restart_count: 21 | 确证应用进程异常退出且已被 kubelet 无限重启 |
| 2 | K8s Event | Kubernetes | Warning BackOff 80s (x383 over 86m)  kubelet  Back-off restarting failed container app | 说明容器启动后立即失败，Kubelet 因重启过于频繁触发 BackOff 机制 |
| 3 | K8s Config | Kubernetes | container: app, resource_limit.memory: 96Mi | 提供容器内存资源限制上下文，但未显示触发 OOMKilled 的特征 |
| 4 | Logging | Elasticsearch | log: "runtime process exiting", http_status: 500, path: /work, allocated_mib: 0 | 提供具体的错误日志模式和 HTTP 500 状态，但缺少导致退出的堆栈信息或具体异常描述 |
| 5 | Tracing | DeepFlow | L7 Flow: HTTP GET /work, response_code: 500, src_ip: 172.16.104.59, dst_ip: 172.16.104.52 | 从网络流量层面印证了应用接收请求后返回了 500 错误，与日志中的 http_status 一致 |

**证据关联说明：**
Kubernetes 状态（#1, #2）与 Metrics（#2 中 kube_pod_container_status_last_terminated_reason=Error）互相印证了容器处于 CrashLoopBackOff 状态。Elasticsearch 日志（#4）指出进程退出并伴随 HTTP 500，而 DeepFlow 流量（#5）在相同时间窗口内捕获到了针对 `/work` 端点的 500 响应。虽然日志和流量证实了“启动后报错并退出”这一行为，但两者均缺失具体的业务异常堆栈（如空指针、配置文件缺失或依赖超时等），导致无法确定导致 `Exit Code 2` 的具体代码级原因。

## 🎯 根因分析 · g1

### 因果链

```text
应用进程异常退出 (Exit Code 2, 伴随 http_status 500) → 容器终止且 kubelet 尝试重启 → 持续失败触发 BackOff 机制 → Pod 进入 CrashLoopBackOff 状态，无法就绪
```

### 根因结论

当前已确认的直接根因是：**应用容器 `app` 启动后异常退出，导致 Kubelet 触发无限重启循环。**

这一结论由以下事实充分支持：
1.  **容器状态异常**：`kubelet` 记录显示容器 `app` 处于 `CrashLoopBackOff` 状态，`restart_count` 为 21，且最后终止原因为 `Error`，退出码为 2（证据 #1, #2）。
2.  **进程退出行为**：应用日志明确记录了 `"runtime process exiting"`，并在启动后的 `/work` 请求中返回了 `http_status: 500`，随后进程终止（证据 #4, #5）。

**证据不足说明**：
尽管确定了“进程异常退出”这一机制，但**具体的业务或代码级根因证据不足**。日志中缺失具体的异常堆栈（Stack Trace）、具体的错误原因描述，且 `allocated_mib` 为 0，排除了 OOMKilled（通常退出码为 137）的可能性，也无法确认是否为内存配置错误。因此，目前无法判断是配置缺失、代码 Bug 还是依赖服务故障导致了 `Exit Code 2`。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 31.4s
├─ 并发证据采集: 56.2s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 56.2s (Evidence 46.6s, RCA 9.4s)
└─ 汇总总结: 12.5s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
