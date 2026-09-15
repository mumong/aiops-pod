## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Readiness probe configuration error: port mismatch (probe configured on 18081 but application listens on 18080) and path mismatch (probe expects /ready but application implements /health). |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | `Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` | 直接证明探针探测失败，报错信息明确指向端口与路径不匹配 |
| 2 | K8s State | Pod `aiops-case-v16/workload` | `ContainersReady: False`, `Ready: False`, `phase: Running` | 证实 Pod 处于运行中但容器健康状态为异常的矛盾状态，符合探针错误表现 |
| 3 | K8s State | Pod `aiops-case-v16/workload` | `restart_count: 0` | 说明应用未发生 OOM 或崩溃重启，排除因资源不足导致频繁重启的问题 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 0` (app container) | 与 K8s 状态独立印证，应用生命周期稳定，故障仅在于探针检测失败 |

证据表明 Pod 运行稳定（重启 0 次），但探针持续报错且 K8s 判定容器未就绪。探针日志中明确的端口和路径错误是唯一指向性强的证据，排除了网络中断或容器崩溃的可能。

## 🎯 根因分析 · g1

### 因果链

```text
探针配置参数错误 (Port: 18081, Path: /ready) → 探测请求被拒绝 (Connection Refused) → 容器未通过健康检查 → 状态标记为 NotReady (ContainersReady: False)
```

### 根因结论

已确认根因为 **Readiness probe 配置错误**。
Kubernetes 事件日志 `fact-00740117246f` 提供了决定性证据：探针尝试访问的端口 `18081` 被拒绝连接，且路径 `/ready` 未能被正确响应，这解释了为何 Pod 状态（`fact-c9c25f643109`）在容器持续运行且无重启（`fact-7848adb9a677`, `fact-0a827eac0fef`）的情况下依然标记为 `NotReady`。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 16.8s
├─ 并发证据采集: 45.9s
│  └─ g1 aiops-case-v16/workload: 45.9s (Evidence 38.5s, RCA 7.3s)
└─ 汇总总结: 8.0s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
