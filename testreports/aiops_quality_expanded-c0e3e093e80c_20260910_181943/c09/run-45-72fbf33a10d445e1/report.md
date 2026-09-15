## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | 应用依赖服务不可用导致应用实例在 /work 端点持续返回 HTTP 503，触发 Readiness Probe 失败使 Pod 处于 NotReady 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Pod Condition | `ContainersReady=False`, `Ready=False`, Reason: `ContainersNotReady`, Message: `containers with unready status: [app]` | 确认应用容器 `app` 启动成功但处于未就绪状态，导致 Pod 服务不可用。 |
| 2 | K8s Event | Readiness Probe | `Warning Unhealthy 59s`, `Readiness probe failed: HTTP probe failed with statuscode: 503` | 直接定位就绪探针因接收 503 错误而失败，解释容器未就绪的技术原因。 |
| 3 | K8s Event | CNI Annotations | `cni.projectcalico.org/podIP: 172.16.104.16/32` | 确认 Pod 已获得网络资源，排除因网络初始化失败导致未就绪的可能性。 |
| 4 | Metric | Restart Count | `kube_pod_container_status_restarts_total` 值为 `0` | 排除应用容器因 OOM、CrashLoop 等自身进程崩溃问题导致的不稳定。 |
| 5 | Logging | 聚合日志 | 8 次 `http_request` (level: `error`), Message: `dependency unavailable`, HTTP Status: 503, Path: `/work` | 确认应用业务层在 `/work` 端点因上游依赖服务不可用而主动返回 503 错误。 |
| 6 | Tracing | Deepflow Flow | 9 次 HTTP GET `/work`, Response Code: 503, Response Status: 3 (错误/超时/重试), Duration: 18ms~30ms | 确认应用对外表现为频繁且低延迟的 503 响应，与日志中的“依赖不可用”行为一致。 |

**证据互证说明：**
1. **探针与业务逻辑闭环**：K8s 探针报告的 HTTP 503（#2）与日志记录的 `dependency unavailable` 返回 503（#5）直接对应，证明 Readiness Probe 失败是应用业务逻辑返回 503 的直接后果，而非网络中断或探针配置错误。
2. **自身稳定性排除**：容器重启次数为 0（#4）且 K8s 状态为 Running（#1），证明容器进程本身存活且未因内存限制（96Mi，#上下文）或 CPU（200m，#上下文）崩溃，问题纯粹源于外部依赖故障引发的业务拒绝服务。
3. **流量确认**：Tracing 数据（#6）在短时间窗口内（约 16 分钟）捕获了 9 次相同的 503 失败请求，证实了该依赖不可用问题的持续性和高频发生，导致 Readiness Probe 持续被判定为失败。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖服务不可用 → 业务逻辑返回 HTTP 503 → Readiness Probe 检查失败（HTTP 503） → Pod 状态变为 NotReady
```

### 根因结论

**已确认的根因**：应用实例 `workload-5f4fb9ff45-5mlnc` 的 `/work` 端点因**依赖服务不可用**（Dependency unavailable）而持续向客户端和探针返回 **HTTP 503** 错误，触发 K8s Readiness Probe 机制将其判定为不健康（NotReady）。

*   **证据支持**：
    *   应用代码明确记录了 `dependency unavailable` 错误并在 `/work` 路径返回 503（日志事实 #5、追踪事实 #6）。
    *   K8s Readiness Probe 因接收到该 503 响应而持续报错（事件事实 #2）。
    *   容器运行状态正常且无重启（指标事实 #4、状态事实 #1），排除了容器自身的故障。
    *   该结论由输入 `formal_rca` 明确确认且可发布。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 24.1s
├─ 并发证据采集: 70.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 70.8s (Evidence 64.2s, RCA 6.5s)
└─ 汇总总结: 13.2s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
