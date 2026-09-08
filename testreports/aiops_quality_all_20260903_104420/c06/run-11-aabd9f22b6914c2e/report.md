## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-w9s9c` | CrashLoopBackOff | {'message': 'k8s.v1.cni.cncf.io/networks-status:'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | pod 状态 Running; app 容器 exit_code: 2; restart_count: 10 | 证实容器正经历频繁异常重启 (CrashLoopBackOff) 且以非零状态码退出 |
| 2 | K8s Event | kubernetes | Warning BackOff: Back-off restarting failed container app (x112 over 28m) | 确证 Kubernetes 已识别并执行了重启退避逻辑 |
| 3 | K8s State | kubernetes | container.last_terminated_reason: Error | 提供容器退出的直接系统级原因 |
| 4 | Metric | prometheus | kube_pod_container_status_restarts_total: 10 (app); kube_pod_container_status_last_terminated_reason: 1 (Error) | 通过时序监控独立印证了容器重启次数及退出原因 |
| 5 | Logging | elasticsearch | pattern: "runtime process exiting", http_status: 500, path: "/work" (occurrence_count: 4) | 捕获到应用层的运行时异常日志，指向特定业务端点 |
| 6 | Tracing | deepflow+tempo | l7_flow: GET /work, response_code: 200, duration 18440.0~42413.0us (9 occurrences) | 记录了对应端点的成功响应流量，存在与故障相关的流量特征 |

证据 1-4 在 Kubernetes 和 Metrics 维度高度一致，确认了容器进程异常退出及频繁重启的系统状态。
Logging 维度的 `http_status: 500` 与 `runtime process exiting` 指向具体的应用层运行时错误，而 Tracing 维度的 `GET /work` 成功请求与日志中的 `/work` 失败路径吻合，说明该代码路径在处理特定请求时存在不稳定性。

## 🎯 根因分析 · g1

### 因果链

```text
应用处理 /work 请求时发生未捕获的运行时异常 → 容器进程执行退出逻辑并返回 exit code 2 → Kubernetes 探针检测到进程死亡 → Pod 进入 CrashLoopBackOff 重启循环
```

### 根因结论

**已确认的根因：**
应用层在处理 `/work` 请求时发生了导致进程退出的未捕获运行时错误（`runtime process exiting`，HTTP 500）。
这一内部逻辑故障导致容器进程以 `exit code 2` 退出，Kubernetes 检测到进程死亡后触发重启机制，进而引发 Pod 处于 `CrashLoopBackOff` 状态，表现为持续的异常重启现象（证据 #4, #5）。

**证据不足：**
确切的代码级根因（如具体的 Python Traceback、内存溢出、或外部依赖超时）无法确认。
日志仅显示通用退出信号，且缺乏 DeepFlow/Tempo 缺失的完整 L7 业务参数细节，无法判断该错误是由特定请求参数、代码逻辑缺陷还是资源争用引起。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 37.6s
├─ 并发证据采集: 68.6s
│  └─ g1 aiops-case-06/workload-7679bcf76-w9s9c: 68.6s (Evidence 58.2s, RCA 10.2s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-w9s9c**: pod-crashloop-runtime, pod-config-error
