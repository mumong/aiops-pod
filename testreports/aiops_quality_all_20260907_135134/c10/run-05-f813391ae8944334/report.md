## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bwqhh` | CrashLoopBackOff | liveness probe configuration causing periodic unresponsiveness detection |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes (unselected) | 状态: `CrashLoopBackOff`；现象: `liveness probe configuration causing periodic unresponsiveness detection` | 定义当前 Pod 的核心异常状态及官方诊断视角。 |
| 2 | K8s State | kubernetes (unselected) | 容器 `app` 最后一次终止原因: `Error` | 支撑容器异常退出的事实证据。 |
| 3 | Metric | prometheus | `kube_pod_container_status_restarts_total` (容器 app): 7 次 | 证实容器经历多次反复重启。 |
| 4 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason` (容器 app): `Error` | 确认最近一次重启是由于 Error 导致。 |
| 5 | Logging | elasticsearch | 模式: `request completed`, status: 200, path: `/work` (8 次重复) | 显示业务请求在终止前均正常处理完毕。 |
| 6 | Tracing | deepflow | HTTP Flow: GET `/work`, 响应码: 200 (9 次重复) | 证实网络层面的请求在到达服务前均正常且被接受。 |
| 7 | Tracing | tempo | Span: `GET /work`, 属性: `liveness_fail`, 耗时: 3μs | 直接捕获到应用返回成功响应却被判定为 Liveness 失败的异常。 |

**证据关联与冲突说明：**
*   业务层证据 (5, 6) 与 Tracing 证据 (7) 形成冲突：应用确实处理并成功返回了请求 (200 OK)，但系统判定其 `liveness_fail`。
*   由于 Kubernetes 事件和详细日志维度工具执行失败或缺失，缺乏直接解释“为何正常响应被视为失败”的底层机制日志，因此依赖 Tracing 中的 `liveness_fail` 标记作为核心诊断依据。

## 🎯 根因分析 · g1

### 因果链

```text
Liveness Probe 配置不当 → 应用实际响应成功但被判定为 Probe 失败(liveness_fail) → 容器因连续失败被 Kubelet 终止(Error) → 触发 CrashLoopBackOff 并反复重启
```

### 根因结论

**已确认的根因：Liveness Probe 配置不当。**

证据表明，Pod 处于 `CrashLoopBackOff` 状态且重启次数高达 7 次。日志与流量记录证实，业务请求 (GET `/work`) 均正常返回了 HTTP 200 状态码，服务本身并未发生崩溃或响应超时。然而，Tracing 记录 (fact-43cc9952dd61) 明确标记了 `liveness_fail` 事件，证明是存活探针的检查逻辑与应用的实际响应机制存在冲突（例如探针超时设置过短、探针路径与应用健康逻辑不一致等），导致应用被错误地判定为不健康并频繁终止。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 30.3s
├─ 并发证据采集: 42.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bwqhh: 42.0s (Evidence 35.5s, RCA 6.3s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bwqhh**: pod-crashloop-runtime
