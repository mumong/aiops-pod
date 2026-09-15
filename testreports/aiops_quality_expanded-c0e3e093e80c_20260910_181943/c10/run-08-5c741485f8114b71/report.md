## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-bsn84` | CrashLoopBackOff | Pod aiops-case-10/workload-79d9f8fd88-bsn84 处于 CrashLoopBackOff 状态（表现为反复重启） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Container `app` `last_exit_code`: 137, `restart_count`: 12 | 确认容器被系统强制终止 |
| 2 | K8s Config | Kubernetes | Container `app` `resource_limit.memory`: 96Mi | 提供判定内存超限的资源基准（硬限制） |
| 3 | K8s Event | Kubernetes | Liveness probe failed: HTTP probe failed with statuscode: 500 | 记录触发重启的直接前置条件 |
| 4 | Metric | Prometheus | `kube_pod_container_status_last_terminated_reason`: `Error` | 交叉印证容器终止原因为异常错误 |
| 5 | Logging | Elasticsearch | Pattern `request completed` 在 `03:00:23` ~ `03:06:09` 期间 `http_status` 均正常为 200 | 证明业务应用进程在重启前存活且响应正常，非进程崩溃导致 |
| 6 | Tracing | Tempo/Deepflow | HTTP Flow `GET /work` 响应码 `200`，Trace 关联到 `liveness_fail` 场景 | 佐证探针失败是独立于业务逻辑的外部检测事件 |

证据互相印证：
退出码 137 结合 96Mi 的内存硬限制，指向 OOM（Out of Memory）事件；Logging 和 Tracing 显示进程在终止前的 HTTP 响应正常，排除了应用逻辑崩溃，确认 500 是探针检测终止时的状态而非应用故障。

## 🎯 根因分析 · g1

### 因果链

```text
容器内存使用量突破 96Mi 硬限制 → OOM Kill (Exit 137) → Liveness Probe 返回 500 → Kubelet 判定探针失败并重启容器
```

### 根因结论

确认根因为容器 `app` 内存使用量超过硬限制（96Mi），触发 OOM Kill。由于 OOM Kill 导致容器进程终止，Kubelet 在执行 Liveness Probe 时探测到服务不可用（返回 500 或连接失败），达到重启阈值后再次拉起容器，最终导致 Pod 处于 CrashLoopBackOff 状态。证据（fact-1, fact-2, fact-3, fact-5, fact-6）共同锁定了内存超限及探针失败的双重机制。

---

## 📊 性能统计

```text
├─ 总耗时: 1.6m
├─ 问题定位: 22.4s
├─ 并发证据采集: 68.0s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-bsn84: 67.9s (Evidence 59.0s, RCA 8.8s)
└─ 汇总总结: 8.5s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-bsn84**: pod-crashloop-runtime
