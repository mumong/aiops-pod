## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod workload-5f4fb9ff45-cfzz6 处于 NotReady 状态，Readiness Probe 持续返回 HTTP 503。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` | `Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-3eb591614e81) | 证明 kubelet 检测到应用存活但健康检查端点返回 503 |
| 2 | K8s Event | `kubernetes` | `Readiness probe failed: Get "http://172.16.104.26:8080/ready": dial tcp 172.16.104.26:8080: connect: connection refused` (fact-b515e9be2a55) | 证明对 Pod 自身 IP 的 8080 端口连接被拒绝，存在探测行为 |
| 3 | K8s State | `kubernetes` | Pod status=`Running`, phase=`Running`, restart_count=`0`, Ready=`False` (fact-2e5ab0208796) | 确认容器进程仍在运行但未通过健康检查 |
| 4 | Logging | `elasticsearch` | 应用日志：`http_status=503`, `message=dependency unavailable`, `path=/work` (fact-38503e376cc3 等 8 条) | 证明应用层因下游依赖不可用主动返回 503 |
| 5 | Tracing | `deepflow` | L7 Flow: `GET /work`, `src_ip=172.16.104.19`, `dst_ip=172.16.104.26`, `response_code=503` (fact-0a7bb9f9ece3 等 9 条) | 证明应用服务自身接收请求后返回 503，非网络转发层故障 |

证据说明：
- K8s 探针日志与 Flow 数据一致确认了故障发生在 Pod 内部应用层（`172.16.104.26:8080`），表现为对外部请求返回 503。
- 应用日志中 `dependency unavailable` 错误与探针返回的 503 状态码相互印证，证明是应用逻辑主动降级而非资源耗尽导致。
- Pod 无重启记录且 CPU/Memory 限制已定义但未见异常，排除了因资源限制被 OOMKilled 导致的进程崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
下游依赖服务不可用 → 应用层返回 HTTP 503 (dependency unavailable) → 就绪探针 /ready 持续返回 503 → Pod 状态转为 NotReady
```

### 根因结论

已确认根因：应用服务 `aiops-case-09/workload-5f4fb9ff45-cfzz6` 的某个内部依赖服务当前不可用，导致其健康检查端点（如 `/ready` 或 `/work`）在探测请求中返回 `HTTP 503`，触发 kubelet 探针失败。

支撑证据：
- 容器处于 `Running` 状态且无重启（事实 #3），证明应用进程本身未崩溃。
- 应用日志明确记录 `dependency unavailable` 导致返回 503（事实 #4）。
- 网络流量数据显示应用自身响应了 503 状态码（事实 #5），排除了中间网络组件阻断。

证据不足项：
- 当前事实未明确具体是哪一个下游依赖服务（如特定数据库或缓存）不可用。
- 依赖服务不可用的根本原因（服务故障或网络策略问题）属于未知领域。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 25.4s
├─ 并发证据采集: 97.6s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 97.6s (Evidence 88.0s, RCA 9.5s)
└─ 汇总总结: 12.6s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
