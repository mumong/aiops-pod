## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Readiness Probe 配置端口（18081）与容器实际监听端口（18080）不一致 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused | 确认 Probe 配置端口 18081 的连接被拒绝 |
| 2 | Logging | app container | listening on 18080 | 确认应用实际监听端口为 18080 |
| 3 | K8s State | Pod conditions | ContainersReady=False, Ready=False | 确认 Pod 当前未就绪 |

现有证据链闭环：日志 [2] 证明应用仅暴露 18080 端口，而 K8s Event [1] 显示探针持续向 18081 端口发起连接并失败，两者端口配置不一致直接导致了 [3] 中的未就绪状态。

## 🎯 根因分析 · g1

### 因果链

```text
Probe 配置端口（18081）与容器监听端口（18080）不一致 → 健康检查请求无法到达应用 → 探针持续失败 → Pod Readiness 状态转为 False
```

### 根因结论

已确认根因为**配置端口不一致**（证据 [1]、[2]）。Kubelet 尝试访问未开放的 18081 端口导致连接拒绝，进而使 `app` 容器被标记为 `Unready`，导致 Pod 无法进入就绪状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 15.6s
├─ 并发证据采集: 41.0s
│  └─ g1 aiops-case-v16/workload: 41.0s (Evidence 34.5s, RCA 6.3s)
└─ 汇总总结: 5.7s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
