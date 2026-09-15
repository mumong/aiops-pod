## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod workload-5f4fb9ff45-5mlnc (aiops-case-09) 处于 NotReady 状态，Kubelet 持续报告 Readiness Probe 失败（HTTP 503），导致 Pod 未被标记为 Ready（0/1），尽管容器进程处于 Running 状态且未发生重启。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `workload-5f4fb9ff45-5mlnc` 状态为 `Running`，容器 `app` 重启次数 `0` (fact-06af26d39df8, fact-70b2baafdf5a) | 排除应用崩溃、内存超限重启或容器进程退出的可能性 |
| 2 | K8s Config | Kubernetes | Pod IP `172.16.104.16` (fact-22abb5bb0542, fact-827d788b8c85)，内存硬限制 `96Mi` (fact-240fe05fd306) | 确认故障实体及网络标识 |
| 3 | K8s Event | Kubernetes | Kubelet 持续报告 Readiness 失败：`connection refused` (fact-c5272e3ba309) 及 HTTP 503 (fact-771f67d03adf) | 直接导致 Pod 处于 `NotReady` 状态 |
| 4 | Logging | Elasticsearch | 应用日志 `aiops-lab-workload` 频繁输出 `dependency unavailable`，伴随 HTTP 状态码 `503`，路径 `/work` (fact_ids: fact-082a91e4a5c7 等 8条) | 证实应用层健康检查端点 `/work` 收到内部依赖不可用错误 |
| 5 | Tracing | Tempo | Trace `118cdbf67902f1230e2f38d3ff619e5b` 中，服务 `aiops-lab-workload` 处理 `GET /work` 返回 `503` (fact-224c2dfe1934) | 跨链路确认健康检查请求被应用正确处理但明确拒绝 |
| 6 | Tracing | Deepflow | 流量聚合显示源 `172.16.104.62` 到目标 `172.16.104.16` 的 `GET /work` 请求返回 HTTP `503`，连续发生 `9` 次 (fact_ids: fact-45c3bcf6a861 等) | 网络层确认 Readiness 探针（来自同集群内其他 Pod）收到了真实的 `503` 响应 |

**证据印证：**
1. K8s 事件显示探针失败，同时应用日志（Log #4）和 Trace（Trace #4、#5）一致指出应用自身在处理 `/work` 端点时因依赖不可用主动返回了 `503`。
2. 容器状态 `Running` 且无重启（State #1）排除了资源不足导致的进程异常，将根因锁定在应用逻辑层面。

## 🎯 根因分析 · g1

### 因果链

```text
外部依赖组件（数据库/缓存等）不可用 → 应用服务 '/work' 端点返回 HTTP 503 (dependency unavailable) → Kubelet Readiness Probe 接收非 2xx 响应 → Pod 标记为 NotReady (0/1)
```

### 根因结论

已确认根因为 **应用服务 '/work' 端点依赖的外部组件不可用**。

- **证据支撑**：
  - K8s 事件显示探针持续返回 HTTP 503 (fact-771f67d03adf)。
  - 应用日志明确记录 `dependency unavailable` 及 503 状态 (fact-082a91e4a5c7 等)。
  - 流量日志与 Trace 数据一致确认了该 503 响应由应用直接返回 (fact-45c3bcf6a861, fact-224c2dfe1934)。
- **未确认事项**：
  - 具体是哪个外部依赖（如特定数据库实例或缓存集群）不可用，因日志和 Tracing 数据中未包含目标 Host/IP 信息，无法进一步定位上游组件。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 19.4s
├─ 并发证据采集: 74.6s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 74.6s (Evidence 61.3s, RCA 13.2s)
└─ 汇总总结: 13.9s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed, pod-crashloop-runtime, pod-oomkilled
