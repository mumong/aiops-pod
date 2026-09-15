## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-08/workload-5c9c7b6489-p8462` | Running | 应用代码在 /work 端点处理请求时存在内存泄漏，导致容器内存单调增长并最终触发 OOMKilled。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s State | `exit_code=137`, `reason=OOMKilled` (fact-75b6537b06cc, fact-66c437674c07) | 容器因耗尽内存被强制终止的确切证据 |
| 2 | K8s State | K8s State | `reason=CrashLoopBackOff`, `waiting_message=back-off 40s restarting failed container=app` (fact-c8e535baa132, fact-c8d428ef95b5) | 反映 OOMKilled 后的系统自愈行为 |
| 3 | Metric | Prometheus | `kube_pod_container_status_restarts_total=3` (fact-f47be59422aa) | 容器重启频次，印证故障的持续性 |
| 4 | Logging | Elasticsearch | 8 次 `http_request` 到 `/work`，`allocated_mib` 从 10 增至 36 (fact-60bbdf5100ff等) | 直接观测到 `/work` 端点处理期间内存单调增长 |
| 5 | Tracing | Tempo/Deepflow | Span/Flow `GET /work` 标记为 `oom_growth`，且伴随 200 响应 (fact-0c1c2d0834b9, 9条等价 Flow) | 确认 `/work` 请求正常执行（成功）但触发内存增长 |

**证据印证：**
1. 日志 (Fact 4) 与追踪 (Fact 5) 共同证明 `/work` 端点在处理正常请求时存在持续的内存分配行为，确认了内存增长的因果触发点。
2. 日志中 `allocated_mib` 的单调增长 (Fact 4) 直接导致了容器内存耗尽，随后 K8s 状态 (Fact 1, 2) 显示容器触发 OOMKilled 并被强制重启。
3. 追踪中该接口返回 200 状态码表明内存泄漏发生在应用逻辑层（如未释放引用），而非上游请求异常导致的临时资源飙升。

## 🎯 根因分析 · g1

### 因果链

```text
应用代码在 /work 端点处理请求时内存泄漏 (Fact 4, 5) → 容器内存单调增长直至耗尽 → 触发容器运行时 OOMKilled (Fact 1) → 进入 CrashLoopBackOff 循环 (Fact 2)
```

### 根因结论

**已确认的根因**：应用代码在 `/work` 端点存在内存泄漏。
**证据支撑**：
1. 追踪数据 (Fact 5) 将 `/work` 请求直接标记为 `oom_growth` 模式。
2. 日志证据 (Fact 4) 显示在处理 `/work` 请求的连续记录中，`allocated_mib` 字段呈现从 10 到 36 的单调增长。
3. 这种内存的不可逆增长最终导致容器耗尽系统分配的内存上限（Memory Limit: 64Mi），触发 OOMKilled (Fact 1)。

---

## 📊 性能统计

```text
├─ 总耗时: 7.0m
├─ 问题定位: 29.3s
├─ 并发证据采集: 382.1s
│  └─ g1 aiops-case-08/workload-5c9c7b6489-p8462: 382.1s (Evidence 375.3s, RCA 6.7s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-08/workload-5c9c7b6489-p8462**: pod-crashloop-runtime
