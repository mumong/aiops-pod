## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod 的 /ready 端点强依赖外部服务（IP 172.16.104.62）的 /work 接口；下游服务不可用（返回 503）导致应用自报不健康，触发 Readiness Probe 失败，使 Pod 保持 NotReady 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `Ready=False` (reason: `ContainersNotReady`), `phase=Running`, `restart_count=0` | 确认 Pod 处于运行但不健康状态，且非因崩溃重启导致 |
| 2 | K8s Event | kubernetes | `Readiness probe failed: HTTP probe failed with statuscode: 503` (发生 519 次) | 证明应用自身健康检查直接失败，而非网络不通 |
| 3 | K8s Event | kubernetes | `Readiness probe failed: dial tcp 172.16.104.16:8080: connect: connection refused` | 确认应用进程正在监听且存活，但拒绝连接，指向内部逻辑故障 |
| 4 | Logging | elasticsearch | pattern: `dependency unavailable` (http_status: 503, path: `/work`, service: `aiops-lab-workload`) | 日志揭示应用因依赖不可用而主动返回 503 |
| 5 | Tracing | deepflow | 聚合 9 条 `L7 Flow`，`GET /work`，`src_ip: 172.16.104.62`, `dst_ip: 172.16.104.16`, `response_code: 503` | 链路数据证实 Pod 向其自身或同集群依赖（172.16.104.62）发起的请求均被拒 |

证据表明 Pod 应用本身正在运行并监听请求，但由于其强依赖的外部服务（`172.16.104.62`）的 `/work` 接口持续返回 503，导致应用自报不健康并触发 Readiness Probe 失败。

## 🎯 根因分析 · g1

### 因果链

```text
下游服务 (172.16.104.62) 返回 503 不可用 → 应用 /ready 端点因依赖失败返回 503 → Kubernetes Readiness Probe 校验失败 → Pod 状态持续为 NotReady
```

### 根因结论

**已确认根因**：Pod 的 Readiness 探针（/ready 端点）强依赖于外部服务 `172.16.104.62` 的可用性。由于该下游服务故障或不可用（返回 503），导致 Pod 健康检查连续失败，从而使 Pod 被标记为 `NotReady`。

**未确认信息**：下游服务 `172.16.104.62` 的具体身份及其返回 503 的根本原因。

---

## 📊 性能统计

```text
├─ 总耗时: 2.4m
├─ 问题定位: 15.9s
├─ 并发证据采集: 117.9s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 117.9s (Evidence 106.8s, RCA 10.8s)
└─ 汇总总结: 9.5s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
