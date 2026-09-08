## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod workload-5f4fb9ff45-cfzz6 处于 NotReady 状态，Ready 为 0/1 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Unhealthy 2m13s (x1558 over 77m) kubelet Readiness probe failed: HTTP probe failed with statuscode: 503` [fact-3f02f12d263b] | 直接确认 Readiness Probe 探测持续失败 |
| 2 | K8s State | kubernetes | `pod.condition: Ready=False (reason: ContainersNotReady), phase=Running, restart_count=0` [fact-08bdfda7cb56, fact-c2964beba1a1, fact-9aef12bb731b] | 确认 Pod 处于 Running 状态但未就绪 |
| 3 | Tracing | deepflow | `l7_flow: HTTP GET /work -> 503 (occurrence_count: 9)` [fact-960ad718dc] | 确认应用接口 /work 对外返回 503 状态码 |
| 4 | Logging | elasticsearch | `pattern: {event: http_request, level: error, message: "dependency unavailable", http_status: 503, path: /work}` [fact-32810e386a87] | 确认应用层报错原因为“依赖不可用”并返回 503 |
| 5 | K8s Config | kubernetes | `container.resource_limit.cpu=200m, memory=96Mi; request: 20m, 24Mi` [fact-21b08004e029, fact-ed930664d8af] | 提供容器资源上下文，无异常告警 |

**证据关系说明**：
- K8s 的 Readiness Probe 失败（证据 1）直接由应用接口返回 HTTP 503 引起，这与 Tracing 流（证据 3）和日志报错（证据 4）的 `503 status` 高度吻合。
- 日志中的明确报错信息 "dependency unavailable"（证据 4）解释了 503 的具体业务含义。

## 🎯 根因分析 · g1

### 因果链

```text
应用调用外部依赖失败（未确认具体哪个外部依赖） → 端点 /work 持续返回 HTTP 503 "dependency unavailable" → Kubelet Readiness Probe 探测连续失败 (x1558) → Pod Ready 状态变更为 False (ContainersNotReady)
```

### 根因结论

已确认的根因为应用服务在处理 HTTP GET `/work` 请求时因外部依赖不可用返回了 HTTP 503 错误（证据 4、3），导致 Kubernetes Readiness Probe 探测持续失败，从而使 Pod 状态变为 NotReady（证据 1、2）。

**局限性说明**：输入事实未明确指出导致 503 的具体外部依赖服务名称或地址，该部分标记为未确认。

---

## 📊 性能统计

```text
├─ 总耗时: 10.6m
├─ 问题定位: 21.1s
├─ 并发证据采集: 602.1s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 602.1s (Evidence 590.2s, RCA 11.8s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
