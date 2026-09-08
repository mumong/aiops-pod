## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-cfzz6` | NotReady | Pod workload-5f4fb9ff45-cfzz6 状态为 NotReady，Readiness Probe 持续返回 HTTP 503。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | ContainersReady: False (reason: ContainersNotReady), Pod Status: Running | 确认应用容器在宿主机已运行，但因容器层未就绪，导致 Pod 处于 NotReady 状态。 |
| 2 | K8s Event | Kubernetes | Readiness probe failed: HTTP probe failed with statuscode: 503 | 直接记录了 Kubernetes Readiness 探针连续探测失败的核心现象。 |
| 3 | Logging | Elasticsearch | 应用日志报错模式：`message="dependency unavailable"`, `http_status=503`, `path="/work"` | 提供了应用层视角的原始错误信息，证明业务代码主动抛出了 503，根源指向依赖不可用。 |
| 4 | Tracing | Deepflow | L7 Flow: `GET /work` (dst_ip: 172.16.104.26) 响应状态 503，发生 9 次，耗时 19ms-32ms | 确认外部流量进入 Pod 内部并收到了 503 响应；短耗时表明应用在接收到请求后快速判定依赖失败并返回，未阻塞在连接阶段。 |

**证据印证说明**：
- K8s 探针（#2）捕获的 503 状态与日志（#3）中的 `http_status: 503` 及链路追踪（#4）中的 `response_code: 503` 完全一致，证明探针探测与业务报错发生在同一异常链路上。
- 追踪链路（#4）显示请求进入了 Pod IP `172.16.104.26` 且耗时极短，结合日志“依赖不可用”，确认是应用层逻辑主动拒绝或探测失败，而非网络不通或后端无响应。
- Pod 处于 Running 状态但未就绪（#1），进一步排除了容器崩溃或拉起失败的情况，确认为应用逻辑异常。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖服务不可用 (未确认具体目标) → 应用 /work 端点处理请求时检测到依赖缺失 → 应用主动返回 HTTP 503 状态码 → Kubernetes Readiness Probe 连续探测失败 → Pod 状态变更为 NotReady (ContainersNotReady)
```

### 根因结论

**已确认的根因**：应用层服务（`aiops-lab-workload`）在 `/work` 端点处检测到**依赖不可用**，主动向 Kubernetes Readiness 探针返回了 HTTP 503 状态码，导致探针连续失败，Pod 最终失去就绪状态。

**缺失的决定性事实**：虽然根因已定位为“应用依赖不可用”，但现有日志仅提示 `dependency unavailable`，未指明具体缺失的下游依赖组件名称或目标地址；追踪数据亦未覆盖指向下游具体服务（如数据库、其他微服务）的失败根因。因此，当前无法进一步确认是下游服务真的宕机，还是应用内部配置/逻辑错误导致的误报。

---

## 📊 性能统计

```text
├─ 总耗时: 2.3m
├─ 问题定位: 15.9s
├─ 并发证据采集: 109.0s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-cfzz6: 109.0s (Evidence 98.6s, RCA 10.2s)
└─ 汇总总结: 10.4s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-cfzz6**: pod-notready-probe-failed
