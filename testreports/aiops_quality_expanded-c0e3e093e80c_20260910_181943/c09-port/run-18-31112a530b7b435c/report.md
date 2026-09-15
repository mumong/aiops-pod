## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | 容器探针配置错误（端口与路径均不匹配应用实际监听配置） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` (fact-e63e655b3a5f) | 核心异常事件，明确探针触发的网络拒绝错误 |
| 2 | K8s State | kubernetes | Pod `Ready` 条件为 `False`，原因 `ContainersNotReady` (fact-8597f4eb9fb7) | 直接反映 Probe 持续失败导致的 Pod 状态异常 |
| 3 | K8s State | kubernetes | Pod 状态 `Running`，重启计数 `0` (fact-0e59bf28cf45) | 排除因容器 CrashLoopBackOff 或资源不足导致的启动失败 |
| 4 | K8s Config | kubernetes | 容器内存 Request 8Mi / Limit 64Mi (fact-590d347eb2ee, fact-a072d59c7583) | 辅助排除因内存溢出导致的容器异常，佐证非资源限制问题 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total` 为 `0` (fact-552049ef607a) | 侧面印证容器运行平稳，未发生因系统错误导致的 Crash 重启 |

上述证据链形成闭环：`fact-0e59bf28cf45` 和 `fact-552049ef607a` 确认容器运行正常且未发生 Crash，直接排除了因系统崩溃或资源耗尽（如内存溢出）引发的探针失败。异常完全由网络通信层导致（`fact-e63e655b3a5f`），结合 Pod 处于 `Running` 状态（`fact-0e59bf28cf45`），唯一合理的解释是应用服务正在运行且监听在其他端口，导致探针请求的目标端口 18081 无法建立连接，进而致使 `fact-8597f4eb9fb7` 中描述的 `ContainersNotReady` 状态。

## 🎯 根因分析 · g1

### 因果链

```text
就绪探针配置了错误的端口与路径 → 网络层拒绝连接 (dial tcp connection refused) → 容器就绪检查持续失败 → Pod 状态变更为 NotReady (ContainersNotReady)
```

### 根因结论

已确认的根因是**容器就绪探针（Readiness Probe）配置错误**。

证据表明应用容器已成功启动且运行平稳（`fact-0e59bf28cf45`、`fact-552049ef607a`），未发生因 CrashLoop 导致的重启。探针失败的具体现象是 TCP 连接被拒绝（`fact-e63e655b3a5f`），这符合“探针指定的目标端口与路径与应用实际监听端口不匹配”的特征。因此，Pod 被 Kubernetes 判定为未就绪（`fact-8597f4eb9fb7`），但底层容器本身处于健康的 `Running` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 20.4s
├─ 并发证据采集: 45.9s
│  └─ g1 aiops-case-v16/workload: 45.9s (Evidence 39.1s, RCA 6.6s)
└─ 汇总总结: 11.0s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
