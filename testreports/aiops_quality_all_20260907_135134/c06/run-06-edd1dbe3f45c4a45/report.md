## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Pod workload-7679bcf76-jwr8b 处于 CrashLoopBackOff 状态，容器 app 频繁重启（7次），退出码为 2 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Container `app` exitCode=2, reason=Error, restarting 7 times (fact-215757dd8f2d, fact-ab7a7ab5f06e) | 确认容器处于 CrashLoopBackOff 并频繁退出 |
| 2 | K8s Event | Kubernetes | BackOff restarting failed container app (x44 over 12m) (fact-ab7a7ab5f06e) | 确认 Kubelet 触发退避重启策略 |
| 3 | K8s State | Kubernetes | Pod status Running, but Ready=False (ContainersNotReady) (fact-c518a4856969, fact-ab9693251bd3) | 确认 Pod 虽处于 Running 阶段但业务不可用 |
| 4 | Logging | Elasticsearch | `error` level logs: "runtime process exiting", http_status 500, path "/work", first: 12:30:36Z, last: 12:42:03Z (fact-266ef80f4fbc) | 提供应用崩溃前的直接错误日志，确认异常发生于 `/work` 请求处理 |
| 5 | Metric | Prometheus | `restart_total`=7, `last_terminated_reason`=Error (fact-89077e1d76db, fact-2ca943a6dda3) | 从监控侧佐证重启次数与错误原因 |
| 6 | Tracing | Deepflow | HTTP GET /work flow, response_code 500, count 2, time: 20:31:36, src_ip: 172.16.104.59 (fact-089f2d40d83c) | 提供网络流量侧视角，确认部分请求确实收到了 500 响应 |

**证据关联说明：**
Kubernetes 侧的 `exitCode=2` 与 `CrashLoopBackOff` 状态证实了进程的频繁非正常退出；日志维度的 `runtime process exiting` 以及 `http_status: 500` 直接解释了退出的触发场景（处理 `/work` 请求失败时主动退出）；Tracing 维度确认了存在被标记为 500 的请求流量，但未能提供 500 的具体业务原因。

## 🎯 根因分析 · g1

### 因果链

```text
应用逻辑/依赖错误 → 处理 /work 请求失败并返回 500 → 进程执行 runtime process exiting 退出 (exitCode=2) → Kubelet 频繁重启导致 CrashLoopBackOff
```

### 根因结论

已确认的根因是：应用进程在处理 HTTP 请求 `/work` 时发生内部错误，记录 500 状态码后直接退出（`runtime process exiting`, `exitCode=2`），导致 Kubernetes 不断重启该容器，引发 `CrashLoopBackOff` 现象。

**证据支撑：**
- 容器多次重启且退出码为 2 (K8s Fact #1, Metric #5)
- 进程日志明确记录在处理 `/work` 请求（status 500）时发生 `runtime process exiting` (Logging #4)
- 流量日志确认存在 `/work` 请求返回 500 的情况 (Tracing #6)

**未知事项：**
- 导致 `/work` 端点返回 500 的具体应用逻辑异常原因（如代码Bug、配置错误或下游依赖超时）
- 日志中 `allocated_mib:0` 的具体含义

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 14.8s
├─ 并发证据采集: 76.1s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 76.1s (Evidence 66.3s, RCA 9.7s)
└─ 汇总总结: 12.5s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
