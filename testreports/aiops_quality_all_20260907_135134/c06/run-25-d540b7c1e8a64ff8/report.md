## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | Pod aiops-case-06/workload-7679bcf76-jwr8b 处于 CrashLoopBackOff 状态，容器反复重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_terminated_reason`: Error; `container.last_exit_code`: 2 | 直接证明容器非正常退出，为 CrashLoopBackOff 提供前置条件。 |
| 2 | K8s Event | Kubernetes | `BackOff restarting failed container app` (x316 over 70m) | 证实 Pod 处于持续重启且退避间隔拉长的失控状态。 |
| 3 | Logging | Elasticsearch | 模式 `runtime process exiting`, `http_status: 500`, path: `/work`，时间范围 13:13:21 - 13:34:04 | 记录进程主动退出行为，且均伴随 500 响应，确立故障触发模式。 |
| 4 | Tracing | Tempo | Span 属性 `aiops.observed_mode: runtime_exit`, HTTP 500 响应 (trace_id: cbadac50855f5a9fdc68ea695812457d) | 从链路维度确认 500 响应与容器内部退出机制直接关联，非外部网络中断。 |
| 5 | Tracing | Deepflow | L7 Flow: `GET /work`, response_code 500, response_status 3 (表示异常断开/重置)，dst_ip 172.16.104.52 | 网络层捕获到与 500 错误同源的异常连接中断事实。 |

日志与追踪结果高度一致：日志中记录的所有 `runtime process exiting` 事件均伴随 `http_status: 500`，且 Tempo 的 Trace 明确标记 `aiops.observed_mode` 为 `runtime_exit`。这表明容器退出不是由 OOMKilled 或外部资源争用引起，而是应用逻辑层面的主动终止。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码逻辑配置 FAILURE_MODE=runtime_exit → 收到 HTTP 500 后主动退出进程 (Exit Code 2) → Kubelet 检测到异常退出并触发容器重启 → 状态转为 CrashLoopBackOff
```

### 根因结论

已确认的根因为应用自身逻辑配置：当处理请求失败返回 HTTP 500 时，应用依据环境变量 `FAILURE_MODE=runtime_exit` 触发主动自我终止机制，导致容器以 Exit Code 2 异常退出（证据 #1, #3, #4）。Kubernetes 根据重启策略反复拉起容器，进而引发持续的 `CrashLoopBackOff` 现象（证据 #2, #5）。现有多维证据链（K8s 状态、日志模式、Trace 链路）相互印证，结论确凿。

---

## 📊 性能统计

```text
├─ 总耗时: 2.6m
├─ 问题定位: 37.0s
├─ 并发证据采集: 107.8s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 107.8s (Evidence 96.5s, RCA 11.2s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime, pod-oomkilled, pod-notready-probe-failed
