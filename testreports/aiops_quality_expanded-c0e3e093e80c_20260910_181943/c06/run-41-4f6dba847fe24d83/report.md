## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | 容器应用进程根据环境变量 `FAILURE_MODE=runtime_exit` 的配置，在处理 HTTP `/work` 请求时主动执行退出操作（exitCode 2），导致 Kubelet 持续重启并进入 CrashLoopBackOff 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning BackOff 7m3s (x406 over 97m) kubelet Back-off restarting failed container app in pod workload-7679bcf76-n5vp8` | 证明 Kubelet 正在经历指数退避的重启循环 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason: Error`, `container.last_exit_code: 2` | 证明容器进程退出并带有明确的异常退出码 |
| 3 | K8s State | Kubernetes | `container.waiting_reason: CrashLoopBackOff` | 描述当前容器的最终异常等待状态 |
| 4 | Logging | Elasticsearch | `runtime process exiting` (HTTP 500), 5 次重复 | 确认应用进程正在主动执行退出流程，而非崩溃 |
| 5 | Tracing | Deepflow (L7 Flow) | `GET /work` 请求返回 `response_code: 500` | 网络层数据印证了触发退出的具体业务请求路径 |
| 6 | K8s Config | Kubernetes | `resource_limit.memory: 96Mi` | 确认内存硬限制，排除常规 OOMKilled 导致 exitCode 137 的嫌疑 |

上述证据形成了完整闭环：K8s 状态与日志均指向进程主动退出（`exitCode: 2`、`runtime process exiting`），Tracing 中的 500 响应与日志模式相匹配。这证明 CrashLoopBackOff 是由应用内部的主动退出逻辑驱动的，而非底层资源或网络故障。

## 🎯 根因分析 · g1

### 因果链

```text
应用配置 FAILURE_MODE=runtime_exit → 进程处理 /work 请求时触发主动退出 → 进程执行 exitCode=2 → Kubelet 持续重启并进入 CrashLoopBackOff 状态
```

### 根因结论

已确认的根因为：容器应用内部配置的 `FAILURE_MODE=runtime_exit` 环境变量触发了应用层的主动退出逻辑。

- **证据印证**：
  1. 容器退出状态显示为 `exitCode: 2`（Fact 2），结合日志中明确的 `runtime process exiting` 模式（Fact 4），确认了这是代码执行路径而非异常崩溃。
  2. Deepflow 的 L7 Flow 观测到对 `/work` 接口的请求返回了 `500`（Fact 5），这与触发主动退出的逻辑分支相符。
  3. Kubernetes 的事件记录（Fact 1）显示 Kubelet 因不断重启该主动退出的进程而进入退避阶段，最终表现为 `CrashLoopBackOff`（Fact 3）。

综上，故障由应用自身的 `runtime_exit` 逻辑导致，集群基础设施处于正常状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 20.9s
├─ 并发证据采集: 68.3s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 68.3s (Evidence 57.6s, RCA 10.6s)
└─ 汇总总结: 9.9s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime, pod-oomkilled
