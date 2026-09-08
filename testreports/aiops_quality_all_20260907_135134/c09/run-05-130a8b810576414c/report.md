## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | {'type': 'Initialized', 'status': 'True'} |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `kubernetes` | `ContainersNotReady`, `containers with unready status: [app]` | 确认 Pod 处于非就绪状态，直接对应 `NotReady` 现象 |
| 2 | K8s Event | `kubernetes` | `Readiness probe failed: Get "http://172.16.104.35:8080/ready": dial tcp 172.16.104.35:8080: connect: connection refused` | 证实就绪探针探测端口被拒绝，导致探针持续失败 |
| 3 | Logging | `elasticsearch` | `pattern: dependency unavailable` (HTTP 503, path: `/work`) | 揭示应用核心业务路径 `/work` 因下游依赖不可用而返回 503 错误 |
| 4 | Tracing | `tempo` | `GET /work` -> `http.response.status_code: 503` | 独立验证应用处理请求时确实产生了 503 状态码 |
| 5 | K8s Config | `kubernetes` | `resource_limit.memory: 96Mi` | 提供内存硬限制上下文，排除内存软限制导致 OOM 的直接证据（配合重启次数为 0） |

**证据印证说明：**
1. 日志与追踪（#3, #4）从两个维度证实了应用在处理业务请求 `/work` 时存在“下游依赖不可用”导致的 503 错误。
2. K8s 事件（#2）证实了就绪探针（探测路径 `/ready`）因连接被拒而失败，解释了 Pod 为何进入 `NotReady` 状态。
3. 重启次数为 0（无 K8s State 异常）且未观测到明显的内存超限指标，说明容器仍在运行但业务逻辑受限于外部依赖或配置错误。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖的下游组件不可用 → 服务处理 /work 请求返回 503 错误 → Readiness Probe 探测失败 (Connection refused/503) → Pod 状态转为 NotReady
```

### 根因结论

**已确认的根因：应用可用性受限于下游依赖异常，导致就绪探针无法通过。**

日志（证据 #3）和追踪（证据 #4）一致证实应用内部在处理请求时因“依赖不可用”返回 HTTP 503。这一异常导致 K8s 就绪探针（证据 #2）在探测 `/ready` 接口时失败，从而触发 `ContainersNotReady` 状态（证据 #1）。

**证据不足说明：**
当前日志中记录的错误信息为通用的 `dependency unavailable`，**无法确定具体是哪个下游实体（如数据库、缓存或第三方 API）不可用**。由于 `topology` 采集失败且缺乏具体的下游报错细节，根因链在“依赖实体”这一环缺失，需补充排查具体未响应的下游服务。

---

## 📊 性能统计

```text
├─ 总耗时: 2.9m
├─ 问题定位: 23.1s
├─ 并发证据采集: 142.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 142.8s (Evidence 133.0s, RCA 9.7s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
