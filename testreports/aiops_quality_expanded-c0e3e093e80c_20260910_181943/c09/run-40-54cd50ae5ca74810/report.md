## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod workload-5f4fb9ff45-5mlnc 处于 NotReady 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Unhealthy Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-bda73f7f2ba3) | 直接证实探针失败原因，是 Pod 状态异常的直接诱因 |
| 2 | K8s State | Kubernetes | Pod 状态为 `Running`，重启次数 `0` (fact-766c65635581, fact-cf837e2afbe0) | 排除容器崩溃重启（CrashLoopBackOff）导致的不稳定 |
| 3 | Logging | Elasticsearch | 错误模式 `dependency unavailable`，伴随 `http_status: 503` 和 `path: /work`，连续记录 10 次 (fact-4224bd9db1c4 等) | 从应用侧日志确认 /work 端点因“下游不可用”主动拒绝请求 |
| 4 | Tracing | Deepflow | 聚合流量 9 次 `GET /work`，目标 IP `172.16.104.16`（与 Pod 日志一致），响应码 `503`，耗时 `15636-21890 μs` (fact-3fa761b6a275 等) | 从网络流量侧确认应用实际对外返回了 503，与日志和探针结果形成闭环 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 值为 `0` (fact-0550fab4f07a) | 从指标侧二次验证 Pod 运行平稳，无突发重启，故障是逻辑层面的 |
| 6 | K8s Config | Kubernetes | 容器资源 Request `20m` CPU / `24Mi` Mem，Limit `200m` CPU / `96Mi` Mem (fact-15024985469c, fact-7752f33a9e83, fact-b90782e43945, fact-d46ef37e96b9) | 资源配额设置正常，无 OOMKill 迹象 |

**证据印证说明：**
Kubernetes 探针（事实 1）的失败直接源于应用返回的 HTTP 503；Elasticsearch 日志（事实 3）揭示了 503 的内部原因为“dependency unavailable”；Deepflow 流量（事实 4）从网络层再次验证了该 Pod 确实在对外输出 503 错误。三个维度的 503 现象高度一致，共同排除了网络中断或 Pod 崩溃的可能。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖的下游服务不可用 → /work 端点返回 HTTP 503 → Readiness Probe 连续失败 → Pod 状态标记为 NotReady
```

### 根因结论

已确认根因为**应用服务（aiops-lab-workload）的 `/work` 端点持续返回 `HTTP 503` 错误，导致 Kubernetes Readiness 探针判定容器不健康**。

依据证据如下：
1. **现象确证**：K8s Event（事实 1）明确指出探针失败的具体原因为 HTTP 503，并直接导致 Pod 被标记为 `NotReady`。
2. **逻辑溯源**：Elasticsearch 日志（事实 3）与 Deepflow 流量记录（事实 4）均捕获到同一路径 `/work` 的 503 错误，且日志内容精确指出原因是 `dependency unavailable`（依赖不可用）。
3. **排除干扰**：Metric 与 K8s State 事实（事实 2、5）一致证明容器未发生重启（Restart Count = 0）且运行在 `Running` 状态，排除由资源耗尽或代码崩溃（如 OOM）引发的非预期故障。

**缺失的决定性事实**：
日志中记录的 `dependency unavailable` 虽指出了故障性质，但**尚未捕获到导致下游依赖具体不可用（如连接超时、解析失败、认证拒绝等）的底层网络或组件错误日志**。目前证据只能定位到“依赖不可用”这一层级，无法进一步下钻至具体的网络或中间件故障点。

---

## 📊 性能统计

```text
├─ 总耗时: 4.1m
├─ 问题定位: 20.3s
├─ 并发证据采集: 213.7s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 213.7s (Evidence 203.0s, RCA 10.5s)
└─ 汇总总结: 14.4s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
