## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-5mlnc 处于 NotReady 状态，且持续对外返回 HTTP 503 错误。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `pod.phase=Running` (fact-116395440682) | 确认 Pod 容器进程处于存活状态，排除 OOM/Killed 导致重启。 |
| 2 | K8s State | kubernetes | `Ready=False`, `ContainersNotReady` (fact-207f71d4f081) | 明确 Pod 不Ready，根因在于容器自身就绪状态，而非基础设施调度。 |
| 3 | K8s Event | kubernetes | `Readiness probe failed: Get "http://172.16.104.16:8080/ready": dial tcp 172.16.104.16:8080: connect: connection refused` (fact-1fa0750a9ecb) | 早期探测阶段网络层无法建立 TCP 连接，反映服务端口未监听或依赖层宕机。 |
| 4 | K8s Event | kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-77f617a5a26f) | 后期探测阶段 TCP 连通性恢复，但应用层明确拒绝服务。 |
| 5 | K8s Config | kubernetes | `container.resource_limit.memory=96Mi` (fact-13e6ed874b53) | 内存限制较小，但在日志未出现 OOM 且 CPU/Memory 监控无飙高的情况下，作为非核心因素记录。 |
| 6 | Metric | prometheus | `kube_pod_container_resource_limits(cpu)=0.2` (fact-06fc502e5e0a) | 验证 Pod 存在 CPU 限制，无超卖或资源耗尽证据。 |
| 7 | Metric | prometheus | `kube_pod_container_status_restarts_total=0` (fact-cdfa37d351aa) | 进一步印证容器自启动后未发生异常退出或重启。 |
| 8 | Logging | elasticsearch | `event=error, message="dependency unavailable", http_status=503, path="/work"` (fact-04cb6b127cfb, 8 occurrences) | 直接指出业务逻辑中调用的下游依赖不可用，并主动返回了 503。 |
| 9 | Tracing | deepflow+tempo | `flow GET /work response_code=503, src_ip=172.16.104.62 -> dst_ip=172.16.104.16` (fact-45c3bcf6a861, 9 occurrences) | 跨网络层证实外部客户端请求进入 Pod 后被应用层拒绝，且耗时稳定(15-28ms)，符合本地业务拒绝特征而非网络中断。 |

**证据间交叉印证说明：**
1.  **事件演进 (Event 3 & 4)**：探针从 `connection refused` 演进为 `503`，结合日志中的 `dependency unavailable`，说明应用自身是“活”的（能接受连接并处理请求），但因其依赖的“外部服务”不可用而主动抛出 503，导致探针持续失败。
2.  **日志与追踪 (Logging 8 & Tracing 9)**：日志记录的 `/work` 端点报错与 Trace 中观测到的 `/work` 端点返回 503 一致，证明故障点位于应用处理业务逻辑阶段。
3.  **状态排除 (State 1 & 2, Metric 7)**：Pod 处于 Running 且重启次数为 0，排除了因资源耗尽（OOM）、CrashLoopBackOff 或容器崩溃导致应用未启动的情况。

## 🎯 根因分析 · g1

### 因果链

```text
下游依赖服务不可用 → 应用业务逻辑触发 dependency unavailable → 持续对外返回 HTTP 503 → Readiness Probe 检查失败 → Pod 状态变为 NotReady
```

### 根因结论

已确认的根因是**应用服务依赖的外部下游服务不可用**。
*   **证据支撑**：日志明确记录了“dependency unavailable”错误（fact-04cb6b127cfb），并伴随 HTTP 503 响应（fact-04cb6b127cfb）；Trace 数据显示该 503 错误在多个请求中稳定复现（fact-45c3bcf6a861）；K8s 探针（fact-77f617a5a26f）因持续接收 503 而判定 Pod NotReady。
*   **现象解释**：Pod 本身运行正常（未重启，内存/CPU 配置合理），但由于应用代码中调用的外部资源断开，应用层无法处理请求，主动返回 503，进而触发 Kubernetes 健康检查机制将 Pod 标记为 NotReady。

**未确认项**：具体是哪个下游服务（如数据库、缓存、第三方 API）不可用；以及早期 `connection refused` 阶段（fact-1fa0750a9ecb）是依赖服务完全宕机还是网络策略导致的暂时性不可达，已演变为 503 的逻辑转折细节未完全明确。

---

## 📊 性能统计

```text
├─ 总耗时: 7.9m
├─ 问题定位: 22.9s
├─ 并发证据采集: 433.1s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 433.1s (Evidence 421.7s, RCA 11.2s)
└─ 汇总总结: 17.8s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
