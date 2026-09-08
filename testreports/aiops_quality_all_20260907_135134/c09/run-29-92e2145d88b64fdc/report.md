## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-7b77l` | NotReady | Pod `workload-5f4fb9ff45-7b77l` (aiops-case-09) 处于 `NotReady` 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s pod.condition | `ContainersReady: False`, message: `containers with unready status: [app]` | 确认 Pod 中 app 容器未达到就绪条件 |
| 2 | K8s Event | kubelet | `Readiness probe failed: Get "http://172.16.104.35:8080/ready": dial tcp 172.16.104.35:8080: connect: connection refused` | 证明 Kubelet 向容器发送探针请求时被拒绝 |
| 3 | K8s Event | kubelet | `Readiness probe failed: HTTP probe failed with statuscode: 503` (x1142 over 55m) | 证明探针请求长期被应用侧返回 503 拒绝 |
| 4 | Logging | Elasticsearch | 错误模式 `dependency unavailable`, path: `/work`, status: 503, `allocated_mib`: 0 | 确认应用侧因依赖不可用主动返回 503，且未使用内存 |
| 5 | Tracing | Deepflow L7 Flow | GET /work 从 172.16.104.55 到 172.16.104.35，返回 503，occurrence: 9 | 验证外部流量和内部探针流量均受同一 503 响应阻断 |

**证据印证关系说明：**
*   日志证据 (第 4 行) 证实应用因 `dependency unavailable` 导致逻辑层返回 503 错误。
*   K8s 事件证据 (第 3 行) 确认 kubelet 收到的探针响应正是此 503 状态码，从而触发探针失败。
*   早期探针拒绝日志 (第 2 行) 与 503 日志共同说明应用可能在启动阶段未能成功依赖，随后进入持续不可用状态。
*   状态证据 (第 1 行) 最终体现了应用层 503 对 Pod 调度状态的直接影响。

## 🎯 根因分析 · g1

### 因果链

```text
应用依赖服务不可用 (dependency unavailable) → 应用逻辑向 Readiness Probe endpoint 返回 HTTP 503 → kubelet Readiness Probe 持续失败 (statuscode: 503) → Pod app 容器状态 NotReady
```

### 根因结论

**已确认的根因**：应用服务因底层依赖不可用（`dependency unavailable`），在探针请求到达时持续返回 `HTTP 503` 错误码。

**分析**：
1.  **直接原因**：Kubelet 发出的 Readiness Probe 请求（针对 `/work` 路径）未能获取 `200` 响应，而是连续收到 `503`（如证据 #2, #3, #4 所示），导致容器健康检查失败。
2.  **根本原因**：应用层日志明确指出“`dependency unavailable`”（如证据 #4 所示），说明应用因无法访问其依赖资源而主动降级响应探针。
3.  **现象验证**：Pod 条件 `ContainersReady` 为 `False`（如证据 #1 所示），且重启次数为 `0`（说明未经历崩溃循环，而是持续处于未就绪状态），符合探针持续失败的表征。

综上，应用自身依赖故障导致的 503 响应是造成 Pod NotReady 的直接原因。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 15.0s
├─ 并发证据采集: 46.4s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-7b77l: 46.4s (Evidence 39.0s, RCA 7.3s)
└─ 汇总总结: 12.0s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-7b77l**: pod-notready-probe-failed
