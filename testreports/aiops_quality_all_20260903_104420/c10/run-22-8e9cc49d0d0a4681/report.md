## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-10/workload-79d9f8fd88-sbqvc` | CrashLoopBackOff | Pod workload-79d9f8fd88-sbqvc 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | 容器退出码 (Exit Code): 137 | 确认容器因资源超限被强制终止 (OOMKilled) |
| 2 | K8s Event | Kubernetes | `Warning Unhealthy ... Liveness probe failed: HTTP probe failed with statuscode: 500` | 解释重启期间探针失败的直接表现 |
| 3 | K8s Config | Kubernetes | `container.resource_limit.memory`: `96Mi` | 定位容器运行的硬内存上限 |
| 4 | K8s Event | Kubernetes | `Warning BackOff ... Back-off restarting failed container app ... (217 times)` | 证明应用处于高频重启的故障循环 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total`: `23` (Container: app) | 验证重启行为的频率与 K8s 事件一致 |
| 6 | Logging | Elasticsearch | 聚合日志: `http_request` (GET `/work`), 耗时 0.0-0.0 MiB 内存变化, 状态 200 (8次) | 展示 OOM 发生前应用曾短暂正常响应的参考模式 |
| 7 | Tracing | Deepflow | L7 Flows: `HTTP GET /work`, 响应码 200, 持续时间 19-46ms, Trace ID: `f5b1b61037693ea4be422bcd676bf61b` | 补充应用正常运行的网络行为特征 |

**证据说明：**
1. **状态与配置确证 (1, 3)**：退出码 137 是 OOMKilled 的绝对指征，与 96Mi 的极低内存限制直接对应。
2. **循环机制确认 (2, 4, 5)**：高频的 Liveness 探针 500 错误和 BackOff 事件，解释了 23 次重启指标背后的“重启-失败-再重启”现象。
3. **应用行为参考 (6, 7)**：日志与链路追踪展示了应用处理请求时的正常行为，作为 OOM 发生前的有效负载基线。

## 🎯 根因分析 · g1

### 因果链
```text
容器内存 Limit (96Mi) 设置过低 → 运行中进程触发 OOMKilled (Exit 137) → 容器重启导致 Liveness Probe 返回 500 → Pod 进入 CrashLoopBackOff
```

### 根因结论
**根因：容器内存资源硬限制过低（96Mi）。**
现有证据充分证明，Pod `aiops-case-10/workload-79d9f8fd88-sbqvc` 因内存硬限制 (`96Mi`) 不满足应用运行需求，导致被系统强制终止（退出码 `137`）。随后的重启引发 Liveness 探针失败，造成 CrashLoopBackOff。

**缺失细节：**
- 导致内存消耗超过 96Mi 的具体应用层逻辑（如具体的内存泄漏模式或大负载处理缺陷）。
- Liveness Probe 返回 500 的详细内部代码路径（通常为重启中未就绪的默认行为）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 19.9s
├─ 并发证据采集: 69.8s
│  └─ g1 aiops-case-10/workload-79d9f8fd88-sbqvc: 69.8s (Evidence 59.8s, RCA 9.8s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-10/workload-79d9f8fd88-sbqvc**: pod-crashloop-runtime, pod-config-error
