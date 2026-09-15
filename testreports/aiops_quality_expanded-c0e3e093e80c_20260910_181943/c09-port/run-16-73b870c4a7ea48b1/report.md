## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Readiness Probe 配置的端口（18081）与应用实际监听的端口（18080）不匹配 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` | 确认 kubelet 尝试连接 Pod IP 的 18081 端口失败，报错为连接被拒。 |
| 2 | Logging | Elasticsearch | `listening on 18080` | 确认应用进程实际监听在 18080 端口。 |
| 3 | K8s State | Kubernetes | Pod 状态 `Running`，重启计数 `0` | 排除因应用崩溃重启导致的异常，确认进程处于持续运行状态。 |

**证据说明：**
事件（#1）与日志（#2）存在明确的端口冲突事实：探针请求 18081，应用监听 18080，导致连接被拒。状态数据（#3）佐证该现象为配置不一致导致的持续健康检查失败，而非应用运行中断。

## 🎯 根因分析 · g1

### 因果链

```text
探针配置端口(18081)与监听端口(18080)不匹配 → 连接被拒绝(dial: connection refused) → 健康检查持续失败 → Pod 处于 NotReady 状态
```

### 根因结论

已确认根因：Readiness Probe 配置的端口（18081）与应用实际监听的端口（18080）不匹配。证据 #1 显示 kubelet 访问 18081 端口时被拒绝，证据 #2 证实应用仅在 18080 端口提供服务。这种配置偏差直接导致了健康检查的持续失败。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 14.3s
├─ 并发证据采集: 42.4s
│  └─ g1 aiops-case-v16/workload: 42.4s (Evidence 36.2s, RCA 6.1s)
└─ 汇总总结: 6.5s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
