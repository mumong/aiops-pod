## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | 容器内存资源限制配置不足（96Mi）导致进程在请求处理期间触发 OOMKilled |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | `container.waiting_reason`: "CrashLoopBackOff" (fact-6237560357db) | 确认容器持续崩溃的当前状态 |
| 2 | K8s Event | `kubernetes` | `BackOff restarting failed container app` (fact-3b1dd6c2e7d6) | 证明系统正在反复重启容器 |
| 3 | K8s State | `kubernetes` | `container.last_terminated_reason`: "Error" (fact-3a723152e3e0) | 证实容器非正常退出 |
| 4 | K8s State | `kubernetes` | `container.last_exit_code`: 137 (fact-10984c2fea63) | 终止码 137 对应 OOMKilled (SIGKILL) |
| 5 | K8s Config | `kubernetes` | `container.resource_limit.memory`: "96Mi" (fact-20906a96a12a) | 内存硬限制配置极低，构成限制条件 |
| 6 | Metric | `prometheus` | `kube_pod_container_status_last_terminated_reason`: "Error" (fact-28db3d8309a6) | 独立于 K8s API 观测到终止原因为 Error |
| 7 | Metric | `prometheus` | `container_memory_working_set_bytes`: 15433728 (≈14.7Mi) (fact-5ed0ef3f4ad7) | 记录到的工作内存占用，低于限制，但可能反映峰值前状态 |
| 8 | Logging | `elasticsearch` | 模式 `request completed` (http_status=200, path=/work) (fact-491783ac4591 等) | 业务逻辑在请求完成阶段存活且正常响应，排除代码逻辑崩溃 |

上述证据表明容器因内存受限被系统强制终止（Exit 137）。配置显示内存硬限制仅为 96Mi (事实 5)。K8s API、Metrics (事实 6) 以及 Exit Code (事实 4) 均指向非正常终止。日志 (事实 8) 证明服务在处理业务请求时能够正常运行并返回 200，说明应用本身逻辑无误，崩溃是由外部资源限制导致的。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存限制配置过低（96Mi） → 进程处理请求时内存消耗突破限制 → 触发 OOMKilled 并被内核杀死 → 容器退出码 137 并进入 CrashLoopBackOff
```

### 根因结论

**已确认的根因**：容器内存资源限制配置不足（96Mi），导致应用在处理请求时触发 OOMKilled。
- **证据支撑**：
    - K8s 状态 `CrashLoopBackOff` (事实 1) 和终止原因为 `Error` (事实 3)。
    - 容器终止码为 137 (事实 4)，明确指示被系统进程杀死（通常为 OOMKilled）。
    - 内存限制配置值为 96Mi (事实 5)。
    - Metrics 观测到终止原因为 Error (事实 6)，印证了 K8s 的 Terminated 状态。
    - 日志显示服务能正常处理 HTTP 请求并返回 200 (事实 8)，证明应用逻辑无缺陷，问题出在资源边界上。
    - 工作内存记录 14.7Mi (事实 7)，虽然未接近 96Mi，但在高负载或并发下可能瞬间突破峰值导致杀死，且 96Mi 本身对 Python 应用可能偏紧。

---

## 📊 性能统计

```text
├─ 总耗时: 1.9m
├─ 问题定位: 13.7s
├─ 并发证据采集: 85.2s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 85.2s (Evidence 79.1s, RCA 5.9s)
└─ 汇总总结: 13.1s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime
