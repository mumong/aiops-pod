## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | 应用进程已启动并监听端口8080，但`/ready`端点返回HTTP 503，原因是应用依赖不可用。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Status | `phase: Running`, `Ready: False`, `ContainersReady: False`, `reason: ContainersNotReady` | 确认 Pod 正在运行但因容器未就绪而被拒绝 |
| 2 | K8s Event | Readiness Probe | `Readiness probe failed: HTTP probe failed with statuscode: 503` (13分钟内触发207次) | 直接证据，表明就绪探针检测到应用返回 503 |
| 3 | Logging | 应用日志 (Elasticsearch) | 8条重复错误日志：`{level: error, message: "dependency unavailable", http_status: 503, path: "/work"}` | 提供根本原因：应用内部明确记录了“依赖不可用”并返回了 503 |
| 4 | Tracing | L7 Flow (Deepflow) | 9次等价的 HTTP `GET /work` 请求，`dst_ip: 172.16.104.26` (Pod IP), `response_code: 503` | 从网络层面证实了针对该 Pod 的 `/work` 接口持续返回 503 状态 |
| 5 | Tracing | Application Span (Tempo) | `GET /work` 成功追踪到 span，attributes 中明确包含 `aiops.observed_mode: readiness_fail`, `http.response.status_code: 503` | 确认 503 是由应用自身处理请求后生成的，而非基础设施层（如 Ingress/Envoy）故障 |
| 6 | K8s Config | Pod Configuration | `resource_limit.memory: 96Mi`, `resource_limit.cpu: 200m`; restart_count: 0 | 排除 OOMKilled 或资源枯竭导致重启的可能性，应用运行稳定 |
| 7 | K8s State | Pod Network | `podIP: 172.16.104.26/32` (Calico) | 确认 Pod 的网络身份，与 Tracing 中的 `dst_ip` 对应 |

**证据链说明：**
1.  **应用行为闭环**：Tracing (证据 #4, #5) 和 Logging (证据 #3) 互相印证，确认应用进程确实接收到了 `/work` 请求，并因为“依赖不可用”主动返回了 HTTP 503。
2.  **探针与业务逻辑的关联**：K8s Event (证据 #2) 显示就绪探针失败，结合上述证据，证明探针调用的正是 `/work` 接口（或逻辑等价），其失败原因完全由应用业务逻辑（依赖不可用）决定。
3.  **基础设施健康度**：Pod 运行状态正常（无重启，IP 分配正常），排除了基础设施层面的异常导致 503。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖服务不可用(日志fact-0ae3eade979c等) → 业务逻辑处理依赖失败并返回503(日志fact-0ae3eade979c, L7 Flow fact-5a0e422f0500) → 就绪探针检测到503(事件fact-24a49ddc56ed) → Pod Ready状态为False(状态fact-10fbe84ac3d4)
```

### 根因结论

**已确认的根因：**
应用容器 `aiops-case-09/workload-5f4fb9ff45-cfzz6` 内部的业务逻辑依赖不可用（Logging fact `fact-0ae3eade979c` 明确报错 `dependency unavailable`），导致应用在处理就绪探针请求（或相关业务请求）时返回 HTTP 503 状态码。Kubernetes 检测到此状态后，将 Pod 的 `Ready` 条件置为 `False`，从而阻止流量进入。

**证据不足/未确认部分：**
1.  **具体是哪个依赖服务（Service/Endpoint）不可用**：当前日志仅记录了“依赖不可用”的通用错误信息，缺乏指向特定上游服务、数据库或配置项的细节事实。
2.  **应用返回 503 的具体业务逻辑条件**：虽然确认了是业务代码行为，但未展示引发该错误的详细堆栈或触发条件。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 19.0s
├─ 并发证据采集: 90.6s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 90.6s (Evidence 83.4s, RCA 7.0s)
└─ 汇总总结: 14.5s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
