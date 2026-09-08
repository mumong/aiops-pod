## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | 应用依赖不可用导致就绪探针持续返回503 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | Readiness probe failed: HTTP probe failed with statuscode: 503 (fact-7910fc887aae) | 确认就绪探针因应用返回 503 而持续失败 |
| 2 | K8s State | Kubernetes | Ready: False (ContainersNotReady); phase: Running; restart_count: 0 (fact-32db6344bc7d, fact-03fa3f673ecb) | 排除容器崩溃重启导致的 CrashLoop，确认为应用业务逻辑层故障 |
| 3 | K8s Config | Kubernetes | Memory limit: 96Mi; CPU limit: 200m (fact-49367d2c4004, fact-94257443423b) | 资源限制存在但无 OOM 迹象 |
| 4 | Metric | Prometheus | kube_pod_container_status_ready: 0 (fact-8407acf41c1f) | 独立指标确认 Pod 当前处于未就绪状态 |
| 5 | Logging | Elasticsearch | "dependency unavailable", http_status: 503, path: /work (fact-597f158b0d09 等) | 应用日志明确记录底层依赖不可用，并直接导致 HTTP 503 |
| 6 | Tracing | Deepflow/Tempo | HTTP 503 on GET /work (flow: fact-4feb86f5de14; span: fact-166d5812d353, trace_id: 1d6f8dd45b2ef15147da083fe3943a40) | 链路追踪确认流量到达应用且返回 503，且与日志中的 trace_id 一致 |

证据间形成了完整的闭环：Tracing 确认请求到达了目标 Pod 并返回了 503（E#6），应用日志证实了返回 503 的内部原因是“dependency unavailable”（E#5），K8s 的事件与指标则记录了这一 503 导致探针连续失败并最终将 Pod 标记为 Unready（E#1, E#2, E#4）。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖服务不可用 → 应用业务逻辑返回 HTTP 503 → K8s 就绪探针读取到 503 响应失败 → Pod 状态标记为 Unready (Readiness: False)
```

### 根因结论

已确认根因为**应用依赖服务不可用**。
该根因通过以下证据链得到直接验证：
1.  **故障触发机制**：K8s 就绪探针执行对 `/work` 路径的 HTTP 探测并收到 `503` 响应（E#1）。
2.  **直接原因**：应用层面的日志和 Tracing 追踪一致表明，该 `503` 响应是由业务代码抛出的，且日志明确记载了原因为“dependency unavailable”（E#5, E#6）。
3.  **状态确认**：Metrics 和 Pod Condition 指标独立确认了 Pod 的 `Ready` 状态为 `False`，且 `restart_count` 为 0，排除了资源不足或启动失败的干扰（E#2, E#4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 17.3s
├─ 并发证据采集: 70.9s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 70.9s (Evidence 62.6s, RCA 8.2s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
