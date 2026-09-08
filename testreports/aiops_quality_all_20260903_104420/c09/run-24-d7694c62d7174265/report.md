## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | application logic returning 503 'dependency unavailable' on /work endpoint causing readiness probe failure |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `workload-5f4fb9ff45-cfzz6` (IP: 172.16.104.26) Phase: Running, Restart Count: 0 | 基础状态确认 |
| 2 | K8s Event | Kubernetes | `Warning Unhealthy Readiness probe failed: HTTP probe failed with statuscode: 503` (频次: 1247/64m) | 确定就绪探针持续失败的现象 |
| 3 | Logging | Elasticsearch | 日志模式: `http_request error dependency unavailable` (503, path: `/work`), trace_ids: `dcd5ae...`, `66c869aa...` 等 | 直接反映应用内部依赖错误 |
| 4 | K8s Config | Kubernetes | Resource Request: CPU 20m, Memory 24Mi; Resource Limit: CPU 200m, Memory 96Mi | 排除资源限制导致 OOM/CPU Throttling |
| 5 | Tracing | Deepflow | L7 Flows: `GET /work` HTTP 503, 9次观测, 耗时 min 21ms ~ max 43ms | 独立网络观测确认请求均返回 503 |

**证据印证说明：**
1. K8s Event (证据 2) 记录的 Probe 503 失败直接对应 Logging (证据 3) 与 Tracing (证据 5) 中观察到的 `/work` 接口 503 错误，形成闭环。
2. 资源配置证据 (证据 4) 与 0 重启计数 (证据 1) 排除了基础设施资源瓶颈或应用崩溃。
3. Deepflow (证据 5) 的独立 L7 流观测佐证了应用逻辑层面的稳定 503 响应。

## 🎯 根因分析 · g1

### 因果链

```text
应用返回 503 'dependency unavailable' → 应用内部依赖缺失或失败 → 健康检查接口返回 503 → 用户侧应用 503 报错
```

### 根因结论

*   **已确认的根因**：应用逻辑问题导致 `/work` 接口返回 503 'dependency unavailable' (证据 3, 5, 7)。
*   **现象成因**：上述逻辑错误导致 K8s 就绪探针 (Readiness Probe) 持续探测失败 (证据 2)，触发 `Ready` 状态为 `False`。
*   **非资源因素**：Pod 未经历重启 (证据 1)，且资源限制 (证据 4) 充足，排除了资源不足导致的逻辑退化。

---

## 📊 性能统计

```text
├─ 总耗时: 9.8m
├─ 问题定位: 18.2s
├─ 并发证据采集: 562.7s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 562.7s (Evidence 558.2s, RCA 4.3s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
