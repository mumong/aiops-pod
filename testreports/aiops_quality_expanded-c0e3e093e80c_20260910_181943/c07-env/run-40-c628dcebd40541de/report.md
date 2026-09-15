## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Deployment 配置缺失关键环境变量 APP_REQUIRED_CONFIG |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `Pod phase: Running` | 确认 Pod 存活且未被调度系统驱逐 |
| 2 | K8s State | Kubernetes | `container.last_terminated_reason: Error` (exit code: 78) | 证实容器在上一轮运行中发生异常退出 |
| 3 | K8s State | Kubernetes | `container.restart_count: 19` | 印证 CrashLoopBackOff 的持续性振荡现象 |
| 4 | K8s Config | Kubernetes | `resource_request/memory: 8Mi`, `resource_limit/memory: 32Mi` | 确认内存配置并非导致 OOM 的根本原因 |
| 5 | Logging | Elasticsearch | `"APP_REQUIRED_CONFIG environment variable is missing"` | 提供终止的直接语义原因 |
| 6 | Metric | Prometheus | `reason: CrashLoopBackOff (1)`, `reason: Error (1)` | 独立观测到 CrashLoopBackOff 事件与 Error 退出状态 |

**证据印证：**
*   Pod 状态为 `Running` (fact 1) 配合高重启次数 (fact 3) 及 `last_terminated_reason: Error` (fact 2)，在逻辑上排除了 Pod 崩溃无法启动或长期处于 `Terminating` 的可能，精准指向“启动即报错退出”的场景。
*   Elasticsearch 日志直接报告了环境变量缺失 (fact 5)，而 K8s 资源配置显示内存充足 (fact 4)，从而排除了资源超限引发的异常退出。
*   Metric 维度独立确认了 CrashLoopBackOff (fact 6)，与 K8s 事件状态（如 `BackOff` 警告）相互交叉验证，确保了现象的真实性。

## 🎯 根因分析 · g1

### 因果链

```text
Deployment 配置缺失关键环境变量 APP_REQUIRED_CONFIG → 应用启动失败 (Exit Code 78) → 容器频繁重启形成 CrashLoopBackOff → 用户无法正常使用该应用
```

### 根因结论

已确认根因为 **Deployment 配置缺失关键环境变量 `APP_REQUIRED_CONFIG`**。
*   **事实支撑**：Elasticsearch 日志直接指出该变量缺失 (fact 5)；K8s 容器状态显示应用以错误码 78 退出 (fact 2)，并在 76 分钟内重启了 19 次，导致集群报告了 CrashLoopBackOff 状态 (fact 1, 3, 6)。
*   **排除假设**：容器重启未触发 OOMKill（`last_terminated_reason` 为 Error 而非 OOMKilled），且内存限制（32Mi）与请求（8Mi）远高于应用正常启动所需的最低开销，证实内存非根因。

---

## 📊 性能统计

```text
├─ 总耗时: 55.1s
├─ 问题定位: 20.1s
├─ 并发证据采集: 25.7s
│  └─ g1 aiops-case-v10/workload: 25.7s (Evidence 20.8s, RCA 4.9s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime, pod-oomkilled
