## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod workload-5f4fb9ff45-7b77l 持续处于 NotReady 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `Ready=False` (Reason: `ContainersNotReady`), `ContainersReady=False`, Phase=`Running`, Restarts=`0` (fact-15582505d8d7/fact-41aecbc3125e/fact-3bf0c6af0379) | 确认应用容器已运行且未重启，但就绪探针持续失败，属于服务级故障而非启动失败。 |
| 2 | K8s Event | Kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-300ff7068d02) | 直接证实就绪探针因后端业务逻辑拒绝而失败，排除了网络不通导致的连接超时。 |
| 3 | Logging | Elasticsearch | `dependency unavailable` (HTTP 503, path: `/work`, 连续发生 8 次, 时间范围 `2026-09-07T19:54:26Z` 至 `19:54:56Z`) (fact-62a00fe00147) | 证实应用自身返回 503 状态码的原因是内部依赖不可用，而非应用进程挂死。 |
| 4 | Tracing | Deepflow/Tempo | HTTP GET `/work` 返回 `503` (src_ip: `172.16.104.55` -> dst_ip: `172.16.104.35`, 出现 9 次, span_id: `c76e0b2351a8325b`) (fact-782b8ac931b0/fact-06c6810c9421) | 从流量侧证实该 Pod IP 对外提供健康检查接口时稳定返回 503，与日志和探针结论一致。 |

**证据逻辑**：
状态指标证实了“进程在运行但拒绝服务”的矛盾（Fact 1）。日志明确了返回 503 的内部原因是下游依赖不可用（Fact 3）。追踪和探针数据分别从流量侧和基础设施侧确认了 `/work` 接口持续返回 503 的状态（Fact 2, Fact 4），形成了从依赖故障到探针拒绝的完整证据链。

## 🎯 根因分析 · g1

```text
下游依赖服务不可用 → 应用 /work 端点处理失败返回 HTTP 503 → Readiness Probe 检查失败 → Pod 状态持续 NotReady
```

**根因结论**：
已确认根因为**应用 `/work` 端点调用下游依赖失败**。事实表明应用逻辑正确捕获了依赖异常并返回了 HTTP 503 错误（Fact 3, Fact 4），Kubernetes 的 Readiness Probe 按预期检测到该错误状态（Fact 2），导致 Pod 持续处于 `NotReady` 状态（Fact 1），尽管容器实际处于运行中且未重启。

---

## 📊 性能统计

```text
├─ 总耗时: 3.1m
├─ 问题定位: 20.6s
├─ 并发证据采集: 153.4s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 153.4s (Evidence 146.5s, RCA 6.7s)
└─ 汇总总结: 10.5s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
