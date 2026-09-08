## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-06/workload-7679bcf76-jwr8b` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (fact-116ddf5c6d3b) | container=app, reason=CrashLoopBackOff | 确认 Pod 处于崩溃循环状态 |
| 2 | K8s State | kubernetes (fact-1a8ec26d8b81) | "back-off 5m0s restarting failed container=app pod=workload-7679bcf76-jwr8b..." | 确认重启退避机制已触发 |
| 3 | K8s State | kubernetes (fact-2a386996fc9c) | exit_code=2 | 确定容器异常退出码，非 OOMKilled |
| 4 | K8s Event | kubernetes (fact-e6e73542ec1a) | "Warning BackOff 94s (x338 over 76m)" | 确认故障已持续 76 分钟且频繁重启 |
| 5 | Metric | prometheus (fact-63b91cb3820b) | waiting_reason=CrashLoopBackOff (value=1) | 独立指标验证 K8s 状态机 |
| 6 | Metric | prometheus (fact-1d741eaaa606) | kube_pod_container_status_restarts_total=19 | 量化容器重启次数 |
| 7 | Logging | elasticsearch (fact-362d9d23d747) | 模式："runtime process exiting" (HTTP 500, path=/work), 时间 13:23-13:44 | 确定故障触发点为 `/work` 路径处理时的进程退出 |
| 8 | Logging | elasticsearch (fact-58cf5660be05) | 模式："request completed" (HTTP 200), 时间 13:18-13:44 | 证实正常业务流与故障流并存，排除基础设施连接问题 |
| 9 | Tracing | deepflow (fact-786d9b09fcd7) | HTTP GET /work response_code=500 (2次聚合) | 流量层证实 `/work` 接口返回 500 错误 |

**证据交叉印证说明：**
K8s 层面的 `CrashLoopBackOff` 状态与 `exit_code=2` [1, 3, 4] 表明应用进程主动退出。Logging 中的 `"runtime process exiting"` 与 HTTP 500 [7] 结合 Tracing 中的 `/work` 请求失败 [9]，将退出机制精确锁定在 `/work` 接口的处理逻辑上。Metric 提供了重启计数 [6] 的独立佐证，且正常 HTTP 200 日志的存在 [8] 说明容器网络和 Kubelet 工作正常，进一步缩小了故障范围至应用代码逻辑。

## 🎯 根因分析 · g1

### 因果链

```text
Application code handles /work requests (fact-362d9d23d747, fact-9) → Application process exits with code 2 (fact-3) → Kubelet detects failure and restarts container, exceeding restart threshold (fact-4) → Pod enters CrashLoopBackOff state (fact-1)
```

### 根因结论

**已确认根因：** 应用代码在处理 `/work` 请求时存在逻辑缺陷，导致进程触发异常退出。

具体表现为：当应用接收到 `/work` 路径的请求时，代码执行路径触发了非零退出码（exit code 2），导致容器终止。Kubelet 检测到终止后立即尝试重启，由于退出机制持续存在，Pod 陷入重启循环并最终进入 `CrashLoopBackOff` 状态。

**支持证据：**
*   **触发机制：** Logging [7] 和 Tracing [9] 均指向 `/work` 请求处理期间发生进程退出或 500 错误。
*   **故障现象：** K8s State [1, 3] 确认了非 OOM 的强制退出码和 CrashLoopBackOff 状态。
*   **排除外部因素：** 正常 HTTP 200 日志 [8] 证明应用容器在运行时具备基本服务能力，问题具有特定请求路径的选择性。

**未确认事实：**
根据诊断报告，导致 `/opt/aiops/server.py` 中代码缺陷的具体原因（如未处理的异常、断言失败或错误配置）目前证据不足，无法从基础设施层面进一步溯源，需查阅应用源码定位。

---

## 📊 性能统计

```text
├─ 总耗时: 8.0m
├─ 问题定位: 34.0s
├─ 并发证据采集: 431.3s
│  └─ g1 aiops-case-06/workload-7679bcf76-jwr8b: 431.3s (Evidence 420.1s, RCA 11.0s)
└─ 汇总总结: 15.6s
```

📋 Runbook 参考

- **g1 aiops-case-06/workload-7679bcf76-jwr8b**: pod-crashloop-runtime
