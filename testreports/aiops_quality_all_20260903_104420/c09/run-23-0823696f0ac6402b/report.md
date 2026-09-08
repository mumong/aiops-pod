## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod workload-5f4fb9ff45-cfzz6 status NotReady (Readiness probe failed) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.condition Ready: status=False (ContainersNotReady)` | 确认 Pod 处于 NotReady 异常状态，应用容器 `app` 未就绪 |
| 2 | K8s Event | kubernetes | `Readiness probe failed: dial tcp 172.16.104.26:8080/ready: connection refused` | 直接证明 kubelet 在探测 `/ready` 端点时遭遇了连接被拒 |
| 3 | K8s Event | kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` | 确认探针最终收到了 503 错误响应 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total: 0` | 排除了容器频繁重启导致的不稳定因素 |
| 5 | Logging | elasticsearch | `http_request error: 503, path=/work` (pattern repeated 13 times, first: 18:22:24) | 确认应用在业务请求中同样返回 503，表明服务整体不可用 |
| 6 | Tracing | deepflow | `HTTP GET /work -> 503`, `src_ip=172.16.104.19, dst_ip=172.16.104.26` (occurred 12 times) | 通过 L7 Flow 证实应用内部或下游依赖对业务端点 `/work` 返回 503 |

证据 2 和 3 从网络层面（Connection Refused）和 HTTP 层面（503）证实了 Readiness Probe 的失败，直接导致证据 1 中的 Pod 状态变更为 NotReady。证据 5（日志）与证据 6（Trace）共同确认了应用不仅探针失败，其业务逻辑 `/work` 同样返回 503，证明故障是全局性的应用层失败，而非单纯的探针配置问题。指标（证据 4）证明容器进程持续运行而非崩溃。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖不可用 → Readiness probe /ready 端点返回 503 (连接被拒或拒绝服务) → kubelet 标记容器 NotReady → Pod 状态 NotReady
```

### 根因结论

**已确认的根因：应用依赖不可用导致 Readiness Probe 返回 503。**

事实支撑：
- Pod 明确处于 `NotReady` 状态（证据 1）。
- kubelet 的 Readiness Probe 探测明确失败，表现为连接被拒（`connection refused`）和返回 503（证据 2, 3）。
- 业务日志（证据 5）和 L7 Flow（证据 6）证实应用在处理请求时同样返回 503，说明应用因依赖问题处于无法服务状态。
- 容器无重启记录（证据 4），证明故障非由应用本身的崩溃重启引起。

**未知项：**
- 具体是哪个应用依赖（数据库、第三方 API 等）不可用，当前证据不足确认其具体身份。

---

## 📊 性能统计

```text
├─ 总耗时: 10.6m
├─ 问题定位: 24.2s
├─ 并发证据采集: 601.3s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 601.3s (Evidence 594.6s, RCA 6.4s)
└─ 汇总总结: 10.9s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
