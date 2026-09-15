## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-n5vp8` | CrashLoopBackOff | Application error: Python process in container 'app' crashes with exit code 2 after logging an HTTP 500 error on the '/work' endpoint, leading to CrashLoopBackOff. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `BackOff restarting failed container app in pod workload-7679bcf76-n5vp8... (x180 over 41m)` | 确认 Pod 长期处于启动-失败-重启的循环状态 |
| 2 | K8s State | kubernetes | `container.last_exit_code: 2` | 确认容器进程异常终止的退出码 |
| 3 | Logging | elasticsearch | `request completed`, `http_status: 500`, `path: /work`, `service: aiops-lab-workload` (首次 `2026-09-10T18:43:40.303Z`) | 定位到崩溃发生在应用处理 `/work` 端点请求时，伴随 HTTP 500 错误 |
| 4 | K8s State | kubernetes | `container.waiting_reason: CrashLoopBackOff` | 描述 Pod 当前的运行阻碍状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason=Error` (值 `1`) | 从指标层面确认上一次容器终止原因为 Error，无数值趋势仅展示当前存在 |
| 6 | Tracing | tempo | Trace `6b940021b18df312738422d71af62239`，`GET /work`，`http.response.status_code: 500`，`attributes.aiops.observed_mode: runtime_exit` | 从分布式追踪视角印证 HTTP 请求失败并伴随应用层退出行为 |
| 7 | K8s State | kubernetes | `pod.condition: ContainersReady=False`, `status: Running` | 确认 Pod 节点虽运行但核心业务容器已不就绪 |

**证据链说明：**
日志中 `/work` 端点的 HTTP 500 错误（#3）与 Tracing 中观测到的 `runtime_exit` 行为（#6）直接对应，解释了退出码 2（#2）的来源。Kubernetes 状态（#1, #4, #7）与 Prometheus 指标（#5）互相印证，表明这并非一次性故障，而是持续了 41 分钟的高频重启循环。

## 🎯 根因分析 · g1

### 因果链

```text
应用逻辑异常（处理 /work 时） → 抛出错误/异常 → 进程退出码 2 终止 → CrashLoopBackOff 重启循环
```

### 根因结论

**已确认根因：应用程序内部错误（Exit Code 2）**

现有证据充分指向容器 `app` 内部的 Python 进程存在导致崩溃的应用层故障：
1.  **故障机制明确**：日志（#3）和 Tracing（#6）一致显示，在请求 `/work` 端点时发生了 HTTP 500 错误，且伴随进程退出行为。
2.  **直接后果确认**：Kubernetes 状态（#2, #4, #7）显示容器以 `exit_code: 2` 异常终止，进而触发 Kubernetes 的重启策略，导致 `CrashLoopBackOff`（#1, #5）。

该现象并非由资源限制（如 CPU/Memory 超限）引起，因为日志与监控中未出现 OOM 或 CPU Throttling 特征，而是明确的代码执行路径错误。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 26.9s
├─ 并发证据采集: 60.3s
│  └─ g1 aiops-case-06/workload-7679bcf76-n5vp8: 60.3s (Evidence 54.2s, RCA 6.0s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-n5vp8**: pod-crashloop-runtime
