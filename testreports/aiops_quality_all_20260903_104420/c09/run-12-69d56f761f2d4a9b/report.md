## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod workload-5f4fb9ff45-cfzz6 状态 NotReady |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes (fact-accfcf06ccc2) | `Warning Unhealthy ... Readiness probe failed: dial tcp 172.16.104.26:8080/ready: connection refused` (22m前) | 证明探针早期连接尝试失败，应用尚未就绪 |
| 2 | K8s Event | kubernetes (fact-f155717cbbf6) | `Warning Unhealthy ... Readiness probe failed: HTTP probe failed with statuscode: 503` (近22m持续，x415次) | 证明应用已响应但返回 503，是探针持续失败的直接原因 |
| 3 | K8s State | kubernetes (fact-72084c6bf549) | `Ready: False` (`reason: ContainersNotReady`) | 确定 Pod 最终状态为 NotReady |
| 4 | Logging | elasticsearch (fact-0073e7d1993b) | `dependency unavailable`, `http_status: 503`, `path: /work` (8次记录) | 定位到应用 `/work` 业务逻辑因依赖缺失主动返回 503 |
| 5 | Tracing | deepflow (fact-5a0e422f0500) | HTTP 503, `GET /work`, `src_ip: 172.16.104.19` → `dst_ip: 172.16.104.26` | 证实来自外部的流量在 `/work` 端点遭遇 503 响应 |

**证据分析说明：**
1. K8s Event (`#1`, `#2`) 展示了应用从不响应（connection refused）到响应但报错（503）的演变，证明应用进程存活但业务逻辑异常。
2. Logging (`#4`) 与 Tracing (`#5`) 相互印证，明确指出业务端点 `/work` 返回 503 是由于“依赖不可用”这一内部原因所致。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖组件(如DB/Redis)不可用(未确认) → 应用业务逻辑返回 HTTP 503 → Kubelet Readiness 探针检测到 503 持续失败 → Pod 状态变更为 NotReady
```

### 根因结论

已确认根因为 **应用容器内部业务异常**。
证据表明，应用进程（IP `172.16.104.26`）的 `/work` 端点因“依赖不可用”主动返回 `HTTP 503`。Kubelet 的 Readiness Probe 检测到该非成功状态码后，判定探针失败，导致 Pod 状态 `ContainersReady` 为 `False`。
*支持证据*：K8s Event 中的 503 报错记录 (`#2`)，以及 Elasticsearch 日志中明确记录 `dependency unavailable` 导致 `http_status: 503` 的现象 (`#4`)。

**证据不足说明**：
日志与追踪仅指明是“依赖不可用”，但未捕获该依赖组件（如数据库、Redis等）的状态，亦未提供底层网络分区或配置错误的证据，因此**具体是哪个依赖失效以及该依赖失效的根本原因（未确认）**无法通过当前数据判定。

---

## 📊 性能统计

```text
├─ 总耗时: 2.2m
├─ 问题定位: 34.2s
├─ 并发证据采集: 83.3s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 83.3s (Evidence 74.6s, RCA 8.4s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
