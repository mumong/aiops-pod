## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod workload-5f4fb9ff45-cfzz6 处于 NotReady 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | `kubernetes` | `fact-21e3e9380005` Readiness probe failed: HTTP probe failed with statuscode: 503 (x1662 over 84m) | 确认 kubelet 持续判定就绪探针失败 |
| 2 | K8s State | `kubernetes` | `fact-4d9c4503ca66` Ready: False, ContainersNotReady: [app] | 确认 Pod 无法进入 Ready 状态，直接表现为 NotReady |
| 3 | Logging | `elasticsearch` | `fact-60072e117551` 8次重复: "dependency unavailable", http_status: 503, path: /work | 提供应用侧故障的直接证据：HTTP 503 及 503 原因描述 |
| 4 | Tracing | `tempo` | `fact-166d5812d353` Flow: GET /work -> 503, trace_id: `1d6f8dd45b2ef15147da083fe3943a40` | 通过 Trace ID 关联日志与 Tracing，证明 `1d6f8dd45b2ef15147da083fe3943a40` 请求链路因应用返回 503 失败 |

证据间相互印证：K8s Event (1) 记录了探针失败；日志 (3) 与 Tracing (4) 证实了应用在处理 `/work` 端点时因 `dependency unavailable` 主动返回了 503 状态码，从而构成了探针失败的直接原因。

## 🎯 根因分析 · g1

### 因果链

```text
应用容器内部依赖资源不可用 → 应用进程在 /work 端点返回 HTTP 503 错误 → kubelet Readiness Probe 判定失败，容器处于 ContainersNotReady 状态 → Pod 无法进入 Ready 状态
```

### 根因结论

**已确认根因：应用侧 /work 端点因依赖不可用返回 HTTP 503，导致 K8s 就绪探针连续失败。**
证据显示应用进程（通过日志 `fact-60072e117551` 和 Tracing `fact-166d5812d353` 确认）在 `/work` 请求中返回了 `http_status: 503`，K8s Event `fact-21e3e9380005` 证实 kubelet 捕获了该 503 状态并持续报出 Readiness probe failed，导致 Pod 保持 `ContainersNotReady` (证据 `fact-4d9c4503ca66`)。

**未确认事项：导致 503 的具体下游依赖资源或配置错误是什么。**
输入中明确指出存在未知项 `unknowns`：["具体是哪个下游依赖服务或资源 unavailable 导致 503"]，现有事实仅确认了应用返回 503 这一现象，未定位到该 503 的根源依赖。

---

## 📊 性能统计

```text
├─ 总耗时: 2.1m
├─ 问题定位: 20.7s
├─ 并发证据采集: 95.4s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 95.4s (Evidence 84.3s, RCA 10.9s)
└─ 汇总总结: 11.1s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
