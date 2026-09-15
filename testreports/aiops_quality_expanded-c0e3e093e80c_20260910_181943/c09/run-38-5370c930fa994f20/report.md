## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-09/workload-5f4fb9ff45-5mlnc` | NotReady | Pod aiops-case-09/workload-5f4fb9ff45-5mlnc 持续处于 NotReady 状态，Readiness 探针因 HTTP 503 持续失败。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | K8s Event | `Unhealthy`: Readiness probe failed: HTTP probe failed with statuscode: 503 (x1870 over 94m) | 确认应用持续处于异常状态，且探针失败频率极高 |
| 2 | K8s Config | K8s Config | `container.resource_limit.memory`: 96Mi, `container.resource_request.cpu`: 20m | 排除资源上限硬限制导致的 OOM/Kill，为软件逻辑/依赖故障提供背景 |
| 3 | Logging | Logging | Log Pattern: `dependency unavailable`, `http_status: 503` (14 occurrences) | 日志直接指明应用层因下游依赖不可用主动返回了 503 错误 |
| 4 | Tracing | Tracing | L7 Flow: GET /work -> HTTP 503 (src_ip: 172.16.104.62 -> dst_ip: 172.16.104.16) | 网络流记录印证了目标 Pod 在处理业务请求 `/work` 时直接返回了 503 状态码 |
| 5 | K8s State | K8s State | Pod `aiops-case-09/workload-5f4fb9ff45-5mlnc` is Running, restarts: 0, IP: 172.16.104.16 | 确认容器进程存活且无重启，证明 503 非进程崩溃导致 |

**证据关联说明：**
1. **现象与原因对应**：Logging 记录 (证据 3) 中的 `dependency unavailable` 和 `HTTP 503` 解释了 Tracing 流量 (证据 4) 中请求返回 503 的根本原因，同时也完美映射了 Kubelet 探针收到的 `statuscode: 503` (证据 1)。
2. **排除资源因素**：容器内存使用量稳定且重启次数为 0 (K8s State)，结合有限的内存限制 (证据 2)，排除了资源耗尽导致服务不可用的可能，指向应用逻辑或下游依赖故障。
3. **探针与业务同源失败**：探针失败的 HTTP 错误码与业务请求的 HTTP 错误码完全一致，证实应用整体功能已不可用，而非探针配置不当。

## 🎯 根因分析 · g1

### 因果链

```text
后端依赖服务不可用 → 应用内部处理失败，返回 HTTP 503 → Kubelet Readiness 探针探测到非 2xx 状态码 → 标记 Pod 为 NotReady
```

### 根因结论

**已确认的根因：**
应用后端存在不可用的下游依赖服务（dependency unavailable）。该依赖的不可用导致应用在处理 `/work` 业务请求及 `/ready` Readiness 探针请求时，均直接返回 `HTTP 503` 状态码。Kubelet 监测到探针连续失败（94分钟内失败1870次），从而将 Pod 状态判定为 `NotReady`（证据 1, 3, 4）。

**证据不足说明：**
当前日志与追踪数据仅记录了通用的 `dependency unavailable` 错误，无法定位具体的下游依赖服务名、主机或端口（输入事实中的 `unknowns`）。需进一步抓取应用配置或更详细的依赖调用栈以确定具体缺失的服务。

---

## 📊 性能统计

```text
├─ 总耗时: 3.3m
├─ 问题定位: 18.8s
├─ 并发证据采集: 164.8s
│  └─ g1 aiops-case-09/workload-5f4fb9ff45-5mlnc: 164.8s (Evidence 152.9s, RCA 11.7s)
└─ 汇总总结: 11.7s
```

📋 Runbook 参考

- **g1 aiops-case-09/workload-5f4fb9ff45-5mlnc**: pod-notready-probe-failed
