## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | 容器应用启动时绑定端口为18080，而Readiness Probe配置的目标端口为18081，导致探针请求因connection refused被拒绝，容器持续处于unready状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Unhealthy Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` (重复 192 次) | **直接证据**：探针在 15 分钟内持续请求 18081 端口且被拒绝，确立探针与业务端口冲突现象。 |
| 2 | Logging | Elasticsearch | 日志输出 `listening on 18080` | **证据印证**：业务实际监听端口为 18080，与探针请求端口 (18081) 不一致，确认端口配置不匹配。 |
| 3 | K8s State | Kubernetes | `ContainersReady: False`, `Ready: False` (ContainersNotReady) | **异常状态**：确认容器因探针失败处于 NotReady 状态，且 `restart_count=0`，排除 OOM 重启干扰。 |
| 4 | K8s Config | Kubernetes | Memory Limit: 64Mi, CPU Limit: 200m (ResourceRequest: 5m/8Mi) | **环境背景**：资源限制明确且充足，排除因内存/CPU 不足导致应用启动失败或崩溃的可能性。 |

**证据说明**：
K8s Event 明确指出了探针请求的 18081 端口失败（connection refused），而 Elasticsearch 日志直接证实了应用实际在 18080 端口监听（fact 2 验证了端口差异）。两者直接印证了探针配置与实际服务端口不一致是导致 `connection refused` 的核心原因，且 Pod 状态确认为 NotReady。

## 🎯 根因分析 · g1

```text
应用硬编码监听端口 18080 (fact 2) → Readiness Probe 错误配置目标端口为 18081 → 探针请求连接被拒 (fact 1) → 容器状态持续为 NotReady (fact 3)
```

### 根因结论
**根因：Readiness Probe 配置错误（端口不匹配）。**

应用代码（或配置）将服务绑定在了 **18080** 端口，而 Kubernetes Readiness Probe 被错误地配置为探测 **18081** 端口。这导致 kubelet 发送的请求无法连接到服务，触发 `connection refused` 异常，从而使容器被标记为 `NotReady` 并失去流量（证据 1、2、3 互相印证）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 22.5s
├─ 并发证据采集: 38.4s
│  └─ g1 aiops-case-v16/workload: 38.4s (Evidence 30.6s, RCA 7.6s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
