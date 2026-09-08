## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod workload-5f4fb9ff45-cfzz6 NotReady |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `Pod:aiops-case-09/workload-5f4fb9ff45-cfzz6` | `Ready=False`, `ContainersNotReady: [app]` (fact-cf63bcf394b2, fact-d01862441e76) | 确认 Pod 处于异常状态 |
| 2 | K8s Event | `Pod:aiops-case-09/workload-5f4fb9ff45-cfzz6` | `Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-20d0de8a850e) | 触发 Pod NotReady 的直接原因 |
| 3 | K8s Config | `Pod:aiops-case-09/workload-5f4fb9ff45-cfzz6` | `app` container: CPU Req 20m / Lim 200m; Mem Req 24Mi / Lim 96Mi (fact-108dafd4a5ad, fact-078c5d539c11, fact-5c887341b4ea, fact-278a6dcae762) | 资源限制明确，非调度或资源不足导致 |
| 4 | K8s Event | `Pod:aiops-case-09/workload-5f4fb9ff45-cfzz6` | Pod Scheduled/Initialized 状态正常，CNI 分配正常，Restart 0 次 (fact-216ba17c4de4, fact-79fb8c2815a9, fact-3843863c20f6) | 排除基础设施/网络/容器启动失败，确认是运行中应用逻辑问题 |
| 5 | Logging | `elasticsearch` | `http_request error: "dependency unavailable", status=503, path=/work` (fact-7fe1a43abcc0, etc., 8 occurrences) | 确认应用自身在请求处理中遭遇下游依赖不可用 |
| 6 | Tracing | `tempo` | `GET /work` 返回 503 (fact-166d5812d353, trace_id: `1d6f8dd45b2ef15147da083fe3943a40`) | 追踪确认了探测请求的具体失败响应 |
| 7 | Tracing | `deepflow` | `HTTP 503` Flow, 源 `172.16.104.19` 目标 `172.16.104.26`, 耗时 16.4-23.7ms (fact-4feb86f5de14, etc., 9 occurrences) | L7 流量验证了 503 响应的持续存在 |

**证据综合说明**：
Pod `workload-5f4fb9ff45-cfzz6` 处于 `Running` 状态但 `Ready` 为 `False`。Kubernetes Readiness Probe 指向 `/work` 端点，持续返回 503，导致 Probe 失败（事实 #1, #2）。应用日志确认了 `/work` 端点因“dependency unavailable”返回 503（事实 #5），追踪记录（事实 #6, #7）独立验证了这一应用层错误现象。资源限制配置（事实 #4）和 0 次重启（事实 #4）排除了资源耗尽或容器重启异常的可能。证据高度一致，均指向应用自身的下游依赖故障。

## 🎯 根因分析 · g1

### 因果链

```text
下游依赖不可用 → /work 端点返回 HTTP 503 → Readiness Probe 持续失败 → Pod 进入 NotReady 状态
```

### 根因结论

已确认根因：**应用内部调用的下游依赖不可用**。
具体机制为：Pod `aiops-case-09/workload-5f4fb9ff45-cfzz6` 中的应用容器在提供 Readiness Probe 端点 `/work` 时，由于依赖的下游组件无法访问（日志明确报错 "dependency unavailable"），导致 `/work` 端点持续返回 `HTTP 503` 状态码。Kubernetes 的探针检测到这一非 2xx/3xx 响应，判定应用不健康，从而将 Pod 状态标记为 `NotReady`。

引用证据：
- 探针失败机制由 K8s Event `HTTP probe failed with statuscode: 503` 证实（事实 #2）。
- 应用层根因由 Elasticsearch 日志 `dependency unavailable` 证实（事实 #5）。
- 现象通过 Tracing 的 `GET /work` 返回 503 独立交叉验证（事实 #6, #7）。

**未知信息**：日志未能提供导致不可用的具体下游依赖（如数据库、缓存或微服务）的身份标识。

---

## 📊 性能统计

```text
├─ 总耗时: 2.5m
├─ 问题定位: 30.1s
├─ 并发证据采集: 100.4s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 100.4s (Evidence 91.1s, RCA 9.1s)
└─ 汇总总结: 16.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
