## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Readiness Probe 配置的端口（18081）和路径（/ready）与容器应用实际监听的端口（18080）及健康接口路径（/health）不匹配，导致 Kubelet 持续收到 connection refused 错误，Pod 无法变为 Ready 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-096117c2a75e` / `fact-9db140a17984` | pod.phase: `Running`, pod.status: `Running` | 确认 Pod 进程已在容器内启动并运行，应用层无崩溃。 |
| 2 | K8s Event | `fact-85330b1ff118` | `Warning Unhealthy` (x960) `Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` | 确认 Kubelet 针对 `18081/ready` 端口的探测持续失败，产生 TCP 连接拒绝。 |
| 3 | K8s Config | 诊断元数据 | Readiness Probe 配置端口 18081/路径 /ready 与实际监听 18080/路径 /health 不匹配 | 提供异常组诊断结论，确立探测配置与实际服务端口错位的直接因果证据。 |
| 4 | Metric | `fact-0115d0dd4cfc` | `kube_pod_container_status_restarts_total` = `0` | 辅助确认容器内应用进程未被 OOM 或意外终止，重启计数为零。 |

**证据说明：**
*   K8s Event (`#2`) 记录了 Kubelet 对错误端口的持续探测拒绝，且频率极高（77分钟内960次），这是导致 Pod 无法 Ready 的直接现象。
*   K8s State (`#1`) 与 Metric (`#4`) 相互印证，证明应用本身正在正常运行（Running, restarts=0），排除应用崩溃。
*   诊断结论 (`#3`) 解释了 Event (`#2`) 的原因：端口与路径配置的错位。

## 🎯 根因分析 · g1

### 因果链

```text
Readiness Probe 配置错误（端口 18081 vs 18080，路径 /ready vs /health） → Kubelet 向错误端口发送 HTTP GET 请求 → TCP 连接被拒绝（connection refused） → Pod 状态 NotReady (READY=0/1)
```

### 根因结论

**已确认的根因：Readiness Probe 探针配置与容器实际运行服务不匹配。**

诊断结论明确指出，Probe 配置的端口（18081）和路径（/ready）与容器应用实际监听的端口（18080）及健康接口路径（/health）不一致。这一配置错误导致 Kubelet 在探测时收到 `connection refused` 错误（见证据 `#2`），从而使 Pod 无法进入 Ready 状态，尽管应用实际已经在运行（见证据 `#1`, `#4`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 24.7s
├─ 并发证据采集: 37.0s
│  └─ g1 aiops-case-v16/workload: 37.0s (Evidence 29.1s, RCA 7.7s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
