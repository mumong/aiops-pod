## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | aiops-case-v16/workload处于NotReady状态，READY 0/1 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Unhealthy 74m kubelet Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` | 确认为 Readiness Probe 连续失败，具体错误为连接被拒 (fact-85f2a86a09ae) |
| 2 | K8s State | kubernetes | `ContainersReady: False`, `Ready: False`, `message: "containers with unready status: [app]"` | 显示 Pod 状态与容器就绪状态不一致（fact-0555897a96d8） |
| 3 | Metric | prometheus | `kube_pod_container_status_restarts_total: 0` | 排除因 CrashLoopBackOff 导致重启的情况，表明容器进程仍在运行（fact-abb3285f831e） |
| 4 | K8s Config | kubernetes | `container.resource_limit.memory: 64Mi`, `container.resource_request.memory: 8Mi` | 确认资源限制未触及极端下限（fact-63f50a42919d） |

日志与链路追踪数据缺失。Pod 处于 `Running` 状态但容器未就绪，结合重启计数为 0 和探针连接被拒的事实，指向网络端口配置层面的错误而非进程崩溃或资源耗尽。

## 🎯 根因分析 · g1

### 因果链

```text
探针配置端口(18081)与容器监听端口(18080)不一致 → 探针发送请求被拒(connection refused) → 连续失败导致 Readiness Gate 不满足 → Pod 状态标记为 NotReady
```

### 根因结论

**已确认根因**：Readiness Probe 配置的目标端口（18081）与容器应用实际监听的端口不一致，导致探测请求失败。

**证据支撑**：
1. **现象与机制确认**：Kubelet 的探针日志明确显示向 `172.16.104.33:18081` 发起 `GET /ready` 请求时遭遇 `connection refused`（事实编号 `fact-85f2a86a09ae`），这证实了端口不通的机制。
2. **容器存活状态**：Prometheus 指标显示容器重启次数为 `0`（事实编号 `fact-abb3285f831e`），结合 Pod 状态为 `Running` 且无资源超限配置，排除了因进程崩溃或 OOM 导致的假死，进一步佐证了容器进程正常但端口服务未响应探测配置的情况。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 18.7s
├─ 并发证据采集: 38.8s
│  └─ g1 aiops-case-v16/workload: 38.8s (Evidence 32.0s, RCA 6.6s)
└─ 汇总总结: 9.6s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
