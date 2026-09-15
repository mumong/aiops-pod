## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod workload-5f4fb9ff45-5mlnc (aiops-case-09) 处于 NotReady 状态，且长期无法恢复。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Readiness probe failed: Get "http://172.16.104.16:8080/ready": dial tcp 172.16.104.16:8080: connect: connection refused` (fact-0b873ad92aa7) | 早期确认应用无法监听在 8080 端口 |
| 2 | K8s Event | Kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-747aa2d88ad3) | 近期确认为业务层返回 503 而非连接拒绝 |
| 3 | K8s State | Kubernetes | `ContainersReady: False` (ContainersNotReady), `Ready: False`, Pod Phase: Running (fact-07c9d905ae3a, fact-feff17fd56f8) | 确认 Pod 虽运行但未就绪，无重启 (Restart Count: 0) |
| 4 | Logging | Elasticsearch | `dependency unavailable` on `/work` with HTTP 503 (8 occurrences, fact-38265714bc9a) | 应用日志表明依赖不可用导致返回 503 |
| 5 | Tracing | Deepflow/Tempo | `GET /work` 返回 HTTP 503, src_ip: 172.16.104.62 -> dst_ip: 172.16.104.16, duration: 13ms-99ms (fact-4b74c185e7f4) | 追踪流量证实对应用 503 响应的网络事实 |

**证据印证说明：**
- 日志 (fact-38265714bc9a) 中的 HTTP 503 状态码与 Deepflow 流量记录 (fact-4b74c185e7f4) 完全吻合，证明了应用进程仍在运行（Phase Running），但业务端（如 /work 或 /ready）持续返回 503 错误。
- 早期 K8s 事件 (fact-0b873ad92aa7) 显示 "connection refused"，近期转为 "statuscode: 503" (fact-747aa2d88ad3)，结合应用日志中的 "dependency unavailable"，说明应用进程已启动并监听，但其依赖的外部服务不可用导致健康检查端点持续失败，进而触发 Pod 的 NotReady 状态。

## 🎯 根因分析 · g1

### 因果链

```text
外部依赖服务不可用 (dependency unavailable) → 应用健康检查端点 (/ready) 返回 HTTP 503 → K8s Readiness Probe 连续失败 → Pod 状态被标记为 NotReady
```

### 根因结论

**已确认的根因**是应用进程依赖的外部服务不可用，导致其健康检查端点持续返回 HTTP 503 错误。

- **证据支持**：应用日志明确记录 `dependency unavailable` 并伴随 HTTP 503 (事实编号 4)；Kubernetes 事件从连接拒绝转变为 503 状态码 (事实编号 2)，且网络流量记录证实了 503 响应的存在 (事实编号 5)；Pod 状态显示运行中但未就绪 (事实编号 3)。
- **未知项**：无法从当前证据中确定具体是哪个外部依赖服务不可用 (日志仅笼统提示)。

---

## 📊 性能统计

```text
├─ 总耗时: 2.0m
├─ 问题定位: 28.0s
├─ 并发证据采集: 79.1s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 79.1s (Evidence 69.2s, RCA 9.7s)
└─ 汇总总结: 12.3s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
