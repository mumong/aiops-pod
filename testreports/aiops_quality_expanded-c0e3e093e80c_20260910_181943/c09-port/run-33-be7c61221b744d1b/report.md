## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod workload in aiops-case-v16 is in NotReady state. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` (fact-022ebcf2dbe6) | 直接证明 Pod 健康检查因连接被拒而持续失败。 |
| 2 | K8s State | Kubernetes | `Ready` 状态为 `False`，原因 `ContainersNotReady` (fact-d197e870a2d6) | 确认容器未达到就绪条件。 |
| 3 | K8s Config | Kubernetes | 资源限制配置：`memory=64Mi`, `cpu=200m` (fact-578713106dcc, fact-7edba62ef60b) | 排除资源耗尽导致的崩溃。 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` 为 0 (fact-5f1cf866e8b4) | 排除因 OOM 或 Panic 导致容器重启。 |

证据 1 显示探针在 18081 端口连接被拒，证据 2 确认该状态导致容器未就绪。结合输入事实中的根因声明，应用实际运行在 18080 端口，二者不匹配是导致探针失败的直接原因。证据 3 和 4 排除了资源限制和容器异常重启的可能性，进一步支持探针配置错误这一结论。

## 🎯 根因分析 · g1

### 因果链

```text
探针目标端口/路径(18081/ready)与应用程序实际监听端口(/health, 18080)不匹配 → 探针连接被拒 → Kubelet 持续报告 Unhealthy 事件 → Pod 状态保持 NotReady
```

### 根因结论

已确认根因为**就绪探针配置不匹配**。

Kubelet 持续向 `172.16.104.33:18081/ready` 发起探测请求（证据 1），导致连接被拒，进而触发 `Readiness probe failed` 事件并阻止 Pod 状态转为 Ready（证据 2）。应用实际运行于 `18080` 端口且健康检查路径为 `/health`，与探针配置存在错位。证据 3 和 4 排除了资源不足或容器异常重启等其他常见原因，确证为探针参数配置错误。

---

## 📊 性能统计

```text
├─ 总耗时: 50.4s
├─ 问题定位: 17.5s
├─ 并发证据采集: 24.0s
│  └─ g1 aiops-case-v16/workload: 24.0s (Evidence 16.5s, RCA 7.4s)
└─ 汇总总结: 8.9s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
