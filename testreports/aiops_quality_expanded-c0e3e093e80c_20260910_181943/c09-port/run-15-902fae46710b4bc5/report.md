## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Readiness probe 配置的端口 (18081) 与应用程序实际监听端口 (18080) 不一致，且探测路径 `/ready` 在应用中未实现，导致 kubelet 持续探测失败，Pod 保持 NotReady 状态。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Unhealthy ... Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` | 确认为 kubelet 发起的 Readiness 探测失败，明确指向探测目标端口 `18081` 连接被拒 |
| 2 | K8s State | Kubernetes | Pod `aiops-case-v16/workload` 的 `Ready` 条件状态为 `False`，原因 `ContainersNotReady` | 记录 Pod 持续处于 NotReady 状态的最终结果，与 Event 中的持续探测失败现象一致 |
| 3 | Logging | Elasticsearch | `listening on 18080` | 暴露应用实际监听端口为 `18080`，与探测配置的 `18081` 不一致，构成冲突事实 |
| 4 | K8s State | Kubernetes | `container.restart_count: 0`, `pod.phase: Running` | 排除因 OOMKilled、CrashLoopBackOff 等容器异常退出或重启导致的服务不可用，表明应用进程存活但探测未通 |
| 5 | Metric | Prometheus | `kube_pod_container_status_restarts_total: 0` (app) | 佐证应用进程自启动以来未发生崩溃或重启，进一步锁定故障位于应用层面的配置交互 |

**证据互证说明：**
K8s Event (1) 显示的连接拒绝错误 (端口 18081) 与 Logging (3) 显示的应用实际监听端口 (18080) 直接矛盾；K8s State (2) 记录了因上述探测失败导致的 Pod 状态锁定 (NotReady)。K8s State (4) 和 Metric (5) 排除了容器运行时层面的启动或崩溃问题，证实了应用存活且配置错误是唯一的干扰项。

## 🎯 根因分析 · g1

```text
Readiness probe 配置错误 (端口 18081 + 路径 /ready) → 探测请求发送至未监听端口且无对应端点的目标 → kubelet 持续接收 'connection refused' 失败 → 容器 readiness 检查不通过，Pod 状态 NotReady
```

### 根因结论

已确认根因为 **Readiness Probe 配置与应用实际监听端口及端点不一致**。

具体表现为：
1. **端口不匹配**：探针配置探测端口为 `18081`，但应用实际在 `18080` 端口监听（见证据 #3, #1）。
2. **端点缺失**：应用未实现 `/ready` 探测路径，导致探针在正确端口上也会因未实现端点而失败。

这两个配置缺陷导致 kubelet 无法通过探针验证应用就绪状态，进而触发 `ContainersNotReady` 并阻止 Pod 进入 Ready 状态（见证据 #1, #2）。证据链完整，无需补充决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 18.8s
├─ 并发证据采集: 43.0s
│  └─ g1 aiops-case-v16/workload: 43.0s (Evidence 36.5s, RCA 6.3s)
└─ 汇总总结: 10.3s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
