## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-7b77l is in NotReady state due to continuous Readiness probe failures returning HTTP 503. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `fact-6317bf5bc331`: Readiness probe failed: HTTP probe failed with statuscode: 503 (x1974 over 96m) | 确认应用层探针持续返回 503 错误，是 Pod 状态异常的直接触发原因 |
| 2 | K8s State | kubernetes | `fact-251d9b5f082f`: Ready=False (ContainersNotReady); 容器 `app` 未就绪 | 确认 Kubelet 因探针失败将 Pod 标记为 NotReady |
| 3 | Logging | elasticsearch | `fact-39583c605084`: 错误日志 `dependency unavailable`，HTTP 503，路径 `/work`；数值字段 `allocated_mib` 维持为 0 | 确认应用自身报告因缺少依赖导致 `/work` 端点返回 503，排除资源耗尽 |
| 4 | Tracing | Deepflow | `fact-0e32dbbd8e18`: HTTP GET `/work` 返回 503；Dst IP `172.16.104.35`；关联 Trace ID `6f6bdf0cfdfd482b9d037f0ef4321493` | 从网络流角度印证 `/work` 路径持续 503，且流量目标与 Pod IP 一致 |
| 5 | Tracing | Tempo | `fact-114ca8885591`: Trace `6f6bdf0cfdfd482b9d037f0ef4321493` 确认应用服务 `aiops-lab-workload` 响应 503 | 提供日志中相同 Trace ID 的链路详情，证实故障发生在应用内部而非网络层 |
| 6 | Metric | prometheus | `fact-d0b6b9afa624`: `kube_pod_container_status_ready` 在 61 个样本中连续保持 0 | 从监控指标角度佐证 Pod 持续处于不Ready状态 |

证据 3 与证据 5 通过 Trace ID `6f6bdf0cfdfd482b9d037f0ef4321493` 形成闭环，确认了日志中“依赖不可用”的报错与网络层 503 响应的同源性。证据 2 明确展示了该机制导致的最终 K8s 状态。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖不可用（未确认具体组件） → GET /work 端点返回 HTTP 503 → 探针连续失败 → Pod 状态标记为 NotReady
```

### 根因结论

已确认的根因是**应用级依赖缺失或不可用导致 `/work` 健康检查端点持续返回 HTTP 503 状态码**。

1. **直接证据**：K8s Event `fact-6317bf5bc331` 与 Prometheus 指标 `fact-d0b6b9afa624` 证实探针失败与 Pod 处于 NotReady 状态的连续性。
2. **故障定界**：Logging `fact-39583c605084` 与 Tracing `fact-114ca8885591` 明确指出是应用自身因“dependency unavailable”拒绝请求，且数值字段显示内存分配为 0，排除了资源耗尽（OOM）的可能性。
3. **链路印证**：Trace ID 的跨维度一致性排除了网络代理或 CNI 故障的可能性。

**缺失的决定性事实**：日志与拓扑中均未识别出导致 503 错误的具体“dependency”（依赖组件）的身份或状态，无法进一步下钻到依赖组件级别。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 17.2s
├─ 并发证据采集: 110.4s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 110.4s (Evidence 100.3s, RCA 10.0s)
└─ 汇总总结: 13.3s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
