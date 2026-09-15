## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-5mlnc处于NotReady状态，Readiness Probe持续失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Readiness probe failed: HTTP probe failed with statuscode: 503` (fact-c0f23c59e0da) | 直接导致 Kubernetes 判定 Pod 未就绪的现象证据 |
| 2 | K8s Event | kubelet | `Readiness probe failed: dial tcp 172.16.104.16:8080: connect: connection refused` (fact-69d8bb45b93d) | 早期诊断线索，表明目标端口曾不可达，可能为依赖故障的前兆 |
| 3 | Metric | prometheus | `kube_pod_container_status_restarts_total` = `0` (fact-7cdc9ff218f0) | 排除因 OOMKilled 或应用崩溃重启导致的故障 |
| 4 | Logging | elasticsearch | `dependency unavailable` pattern, `http_status: 503`, `path: /work` (fact-5e7d8b04b85b 等) | 确认应用侧返回 503 的具体原因为内部依赖不可用 |
| 5 | Tracing | deepflow | `GET /work` flow `response_code: 503`, `src_ip: 172.16.104.62 -> dst_ip: 172.16.104.16` (fact-4b74c185e7f4 等) | 独立于日志确认了健康检查接口 `/work` 被持续返回 503 的错误 |

证据之间形成闭环：K8s Event (No.1) 记录了 Readiness Probe 收到 503 状态；Logging (No.4) 与 Tracing (No.5) 共同证实了应用代码在执行 `/work` 接口时，因“内部依赖不可用”主动返回了 503。Metric (No.3) 排除了容器自身进程异常的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
已验证的上游原因：应用内部关键依赖服务/资源不可用 → 失败机制：应用无法完成健康检查逻辑，返回 503 状态码 → 直接失败：Kubelet Readiness Probe 连续收到 503 HTTP 错误 → 用户可见现象：Pod Ready 条件变为 False，状态显示为 NotReady
```

### 根因结论

已确认根因为**应用内部依赖不可用**。

事实支撑：
1.  **现象层**：Kubernetes 记录 Readiness Probe 持续失败，状态码为 503（事实 1）。
2.  **应用层**：日志明确抛出 `dependency unavailable` 错误且伴随 HTTP 503（事实 4）。
3.  **链路层**：流量分析确认了目标健康检查端点 `/work` 确实在返回 503（事实 5）。
4.  **排除项**：容器未发生重启（事实 3），证明是应用逻辑层面的依赖阻断而非资源或进程问题。

未确认项：
具体是哪个内部依赖（如特定数据库、缓存或外部 API）不可用，当前证据不足以直接定位，需通过未提供的 Trace ID 进行跨服务调用链的深层排查。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 20.6s
├─ 并发证据采集: 74.3s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 74.3s (Evidence 64.9s, RCA 9.3s)
└─ 汇总总结: 11.4s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
