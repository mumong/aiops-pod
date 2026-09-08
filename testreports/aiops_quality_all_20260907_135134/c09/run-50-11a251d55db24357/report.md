## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod workload-5f4fb9ff45-7b77l 处于 NotReady 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `Ready` 状态 False (`ContainersNotReady`)，`ContainersReady` 状态 False，Pod Phase Running | 确认当前 Pod 处于应用存活但不可接收流量的状态 |
| 2 | K8s Event | Kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (2391 次/118m) | 明确触发 Pod 变为 NotReady 的直接机制 |
| 3 | Metric | Prometheus | `container_cpu_usage_seconds_total` 累计值 15.265876s，重启次数 0 次 | 排除容器崩溃重启问题，表明进程已持续运行但应用逻辑异常 |
| 4 | Logging | Elasticsearch | 错误日志：`dependency unavailable` (`http_status: 503`, `path: /work`) 聚合 15 次 | 揭示 503 响应的直接原因：应用无法访问其依赖的后端资源 |
| 5 | Tracing | Deepflow | L7 Flow：HTTP GET `/work` 响应码 503，源 IP `172.16.104.55` 至目的 IP `172.16.104.35`，持续 11-17ms | 验证了探测请求路径及返回 503 的网络事实 |

**证据印证**：
Kubernetes Event 中的探针失败记录与 Logging 中 `/work` 路径返回 503 的错误日志在路径和时间线上完全吻合。Metric 显示重启次数为 0，表明应用处于持续运行的僵死或错误处理状态，而非进程挂掉，进一步确认问题出在业务逻辑对后端依赖的响应上。Tracing 数据从网络层面证实了外部探测流量在到达该 Pod 时被应用层拒绝。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖的后端服务不可用 → 应用 /work 端点持续返回 HTTP 503 → Kubernetes Readiness 探针探测失败 → Pod 状态变为 NotReady
```

### 根因结论

**已确认的根因：应用依赖的后端服务不可用，导致应用自身健康检查（Readiness Probe）返回 503。**

证据链支撑如下：
1. **直接失败机制（证据 #2）**：Kubernetes Event 记录了近 118 分钟内连续 2391 次 Readiness 探测失败，状态码均为 503。
2. **应用层原因（证据 #4）**：应用日志中多次出现 `dependency unavailable` 伴随 HTTP 503 响应，直接解释了 `/work` 端点返回失败的原因。
3. **网络与探针一致性（证据 #5）**：Trace 数据显示探测流量成功到达 Pod IP (`172.16.104.35`)，并由应用返回 503，排除了网络不通或探针配置错误导致连接被拒的可能。
4. **运行状态排他性（证据 #1, #3）**：Pod 处于 Running 状态且无重启（重启计数 0），说明应用进程本身是存活的，但业务逻辑因依赖问题无法正常服务，进而导致健康检查失效。

**未知信息**：具体是哪一种或哪几个“后端服务”不可用，现有日志仅笼统报为 `dependency unavailable`，缺乏具体的服务名或 IP 标识。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 21.3s
├─ 并发证据采集: 84.0s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 84.0s (Evidence 76.2s, RCA 7.6s)
└─ 汇总总结: 11.8s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
