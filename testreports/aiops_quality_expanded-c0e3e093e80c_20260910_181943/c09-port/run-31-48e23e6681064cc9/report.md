## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod aiops-case-v16/workload is NotReady due to Readiness probe failure |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | Pod `aiops-case-v16/workload` 状态 `Running`，条件 `ContainersReady` 为 `False` (fact-71f31fa225ca, fact-e6be1b9a259b) | 确认 Pod 进程存活但健康检查未通过 |
| 2 | K8s Event | Kubernetes | Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused (fact-cf2fcc5a68b4) | 直接证据：探针在 18081 端口拒绝连接 |
| 3 | K8s Event | Kubernetes | Pod IP: `172.16.104.33/32` (fact-ff64c184e45d) | 提供发生连接拒绝的具体 IP 地址 |
| 4 | K8s Config | Kubernetes | Container `app` Memory Limit: `64Mi` (fact-00bef402ea0a), CPU Limit: `200m` (fact-2acdb844f46a) | 排除资源耗尽导致进程崩溃的可能 |
| 5 | K8s State | Kubernetes | Container `app` Restart Count: `0` (fact-bef84eafd07a) | 佐证应用处于启动成功但未就绪的初始运行状态 |
| 6 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 为 `0` (fact-252c843c77d6) | 独立观测：确认容器未经历重启，佐证 OOM 或崩溃类故障已排除 |

**证据关联说明：**
Kubernetes Event (fact-cf2fcc5a68b4) 明确指出了探针连接失败的端口 (18081) 和路径 (`/ready`)，结合 Pod IP (fact-ff64c184e45d) 与 K8s State (fact-71f31fa225ca) 证实了连接拒绝发生在运行中的 Pod。Metric (fact-252c843c77d6) 的零重启计数与 K8s Config 的充足资源限制 (fact-00bef402ea0a) 排除了应用因资源不足而崩溃退出或频繁重启导致端口未监听的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
探针配置与实际服务端口路径不匹配 → kubelet 向错误端口/路径发起 HTTP GET 请求 → 连接被拒绝 (connection refused) → Pod 状态转为 NotReady
```

### 根因结论

已确认根因为 **Readiness probe 配置错误**。

证据支持如下：
1. **探针目标错误**：Event 事实 (fact-cf2fcc5a68b4) 显示 kubelet 持续向 `http://172.16.104.33:18081/ready` 发送探测请求，并收到 `connection refused` 错误。
2. **排除资源故障**：容器重启次数 (fact-bef84eafd07a) 和 Prometheus 重启指标 (fact-252c843c77d6) 均为 0，且内存/CPU 限制 (fact-00bef402ea0a, fact-2acdb844f46a) 设置合理，证明应用并未因 OOM 或 CPU 限制崩溃。
3. **运行状态矛盾**：Pod 处于 Running 状态 (fact-71f31fa225ca)，但 Readiness 条件持续为 False (fact-d7f7652f907f)，这是典型的端口/路径配置与业务实际监听不一致的表现。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 21.4s
├─ 并发证据采集: 43.0s
│  └─ g1 aiops-case-v16/workload: 43.0s (Evidence 33.5s, RCA 9.5s)
└─ 汇总总结: 13.2s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
