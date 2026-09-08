## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod workload-5f4fb9ff45-cfzz6 持续处于 NotReady 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Readiness probe failed: HTTP probe failed with statuscode: 503 (发生 2701 次，覆盖 130 分钟) | 描述 Pod 持续 NotReady 的直接触发机制 |
| 2 | K8s State | kubernetes | Pod phase=Running, condition Ready=False (ContainersNotReady), restart_count=0 | 确认 Pod 运行中但健康检查失败，且非崩溃重启 |
| 3 | K8s Config | kubernetes | container app memory_request=24Mi, memory_limit=96Mi | 排除容器资源超限（OOM）导致失败 |
| 4 | Logging | elasticsearch | 10 次 `dependency unavailable` 错误 (status 503, path: `/work`)，观测时间 20:03:09 ~ 20:03:53 | 证明应用业务逻辑中下游依赖不可用，返回 503 |
| 5 | Tracing | deepflow + tempo | 10 次 GET `/work` 请求返回 503 (耗时 18.6ms~32.5ms)，trace_id `5a23e0c80f2d1e117abdc6c429c94edd` | 确认 L7 请求层面对 `/work` 端点的持续拒绝，并验证了时间窗口一致性 |

**证据印证说明**：
1. K8s Event (证据 1) 中 503 错误与 Logging (证据 4) 及 Tracing (证据 5) 中的 `dependency unavailable` 业务错误完全吻合，共同指向 `/work` 端点因依赖问题无法提供正常响应。
2. K8s State (证据 2) 证明 Pod 进程存活（Running, 0 restarts）但应用层健康检查失败，排除了容器崩溃等基础设施层面的重启原因。
3. 资源配置 (证据 3) 显示容器有充足的资源配额，排除了资源竞争导致的延迟或崩溃。

## 🎯 根因分析 · g1

### 因果链
```text
下游依赖服务不可用 → 应用健康检查端点 /work 持续返回 HTTP 503 状态码 → kubelet Readiness Probe 探测连续失败 → Pod 标记为 NotReady (服务不可用)
```

### 根因结论
**已确认根因**：应用 `workload-5f4fb9ff45-cfzz6` 内部的依赖服务不可用（日志明确记录为 `dependency unavailable`），导致其就绪探针端点 `/work` 持续返回 HTTP 503 错误，触发 K8s 持续判定 Pod 为 NotReady 状态。

**证据不足**：目前无法确认导致 `dependency unavailable` 的具体底层依赖服务名称及其故障原因（该信息属于 `unknowns` 范畴）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.7m
├─ 问题定位: 21.2s
├─ 并发证据采集: 71.3s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 71.3s (Evidence 61.3s, RCA 9.8s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
