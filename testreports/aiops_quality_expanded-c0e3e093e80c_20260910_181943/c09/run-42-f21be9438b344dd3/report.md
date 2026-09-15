## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod NotReady (Readiness Probe failed: HTTP 503) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod | `status: Running` (Pod 存活) | 确认业务容器进程在运行 |
| 2 | K8s Event | Pod | `Readiness probe failed: HTTP probe failed with statuscode: 503` (持续 106 分钟) | 确诊 Pod 被标记为 NotReady 的直接诱因 |
| 3 | Logging | ES | 8 次 `dependency unavailable` 错误 (trace_ids 如 `5ccad1bc...`) | 证实应用自身检测到上游依赖不可用并主动返回 503 |
| 4 | Tracing | Tempo | `GET /work` 返回 `http.response.status_code: 503` (耗时 ~3ms) | 从流量层面确认应用层返回了故障响应，非网络或网关层问题 |

**证据说明：**
K8s 探针持续失败（证据 2）的根源在于应用内部（证据 3、4），Pod 处于 `Running` 状态（证据 1）但 `NotReady`。日志与 Trace 数据通过时间、路径（`/work`）及 TraceID 实现了强关联，证实故障由应用内部逻辑触发。

## 🎯 根因分析 · g1

### 因果链
```text
上游依赖不可用 → 应用层探测失败 → Readiness Probe 返回 503 → Pod 被标记为 NotReady
```

### 根因结论
**已确认根因：应用依赖不可用（Dependency unavailable）**
应用服务因依赖组件不可用，在接收就绪探针请求时主动返回 503 错误，导致 K8s 调度器将该 Pod 标记为 `NotReady`。
证据来源：K8s Readiness Probe 事件 `fact-ed22e56bc689` 与应用日志记录 `fact-132e2578e7a7` 相互印证，明确了故障发生在应用层而非基础设施层。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.4s
├─ 并发证据采集: 38.2s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 38.2s (Evidence 30.3s, RCA 7.8s)
└─ 汇总总结: 7.2s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
