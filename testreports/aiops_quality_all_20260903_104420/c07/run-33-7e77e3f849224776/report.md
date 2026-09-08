## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-07/workload-dff5cbc6b-kmfxx` | CrashLoopBackOff | ConfigMap 'workload-code' 缺失导致应用启动失败并退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: Error (fact-2fe6582366a5) | 确认容器启动异常终止 |
| 2 | K8s Config | kubernetes | `container.resource_limit.memory`: 96Mi (fact-1c1492a2e972) | 提供内存限制配置上下文 |
| 3 | K8s Event | kubernetes | `BackOff restarting failed container app` (fact-a9dd32d51169) | 直接反映 Pod 持续崩溃重启的状态 |
| 4 | Logging | elasticsearch | `CONFIG_MISSING`, `/work`, `500` 错误日志 (fact-045862fc2adf) | 指出应用运行时因配置缺失主动报错 |
| 5 | Tracing | deepflow+tempo | `HTTP GET /work` 返回 `500`, `aiops.observed_mode=config_missing_exit` (fact-408947ed4dba) | 关联 `ConfigMap 'workload-code' 缺失` 的具体触发路径 |
| 6 | Metric | prometheus | `kube_pod_container_status_last_terminated_reason` = 1 (Error) (fact-31497614f5a0) | 验证容器异常退出状态的持续性 |

**证据关联说明**：
K8s State 与 Event 确认了 Pod 的 `CrashLoopBackOff` 症状；Logging 与 Tracing 共同指向了应用层面的直接原因——由于 `ConfigMap 'workload-code'` 缺失，导致应用启动时抛出 `CONFIG_MISSING` 错误并以 `500` 状态退出。Kubernetes 记录的 `last_terminated_reason: Error` 与此应用内部异常退出行为一致，证据链条完整闭环。

## 🎯 根因分析 · g1

### 因果链

```text
ConfigMap 'workload-code' 缺失 → 应用启动阶段抛出 CONFIG_MISSING 错误 → 容器以 Error 状态退出 → Pod 持续崩溃重启 (CrashLoopBackOff)
```

### 根因结论

**已确认的根因**：
ConfigMap `workload-code` 的缺失导致应用程序无法获取必要配置而主动退出。
- **证据 4 (Logging)** 记录了在 `/work` 路径上反复出现的 `CONFIG_MISSING` 错误，明确指出了缺失的配置项；
- **证据 5 (Tracing)** 进一步关联了该配置缺失到具体的应用退出模式 (`aiops.observed_mode=config_missing_exit`)，证实了容器退出 `Error` (证据 1) 的原因是应用自身的配置校验失败，而非资源不足或节点异常。

---

## 📊 性能统计

```text
├─ 总耗时: 1.4m
├─ 问题定位: 16.6s
├─ 并发证据采集: 57.6s
│  └─ g1 aiops-case-07/workload-dff5cbc6b-kmfxx: 57.6s (Evidence 53.5s, RCA 4.0s)
└─ 汇总总结: 9.4s
```

📋 Runbook 参考

- **g1 aiops-case-07/workload-dff5cbc6b-kmfxx**: pod-crashloop-runtime
