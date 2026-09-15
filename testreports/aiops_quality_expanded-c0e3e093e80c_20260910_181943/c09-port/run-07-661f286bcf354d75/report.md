## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod aiops-case-v16/workload status is NotReady |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | K8s Event | `Warning Unhealthy ... Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` (x192 over 17m) | 确认探针在 pod IP `172.16.104.33` 的 `18081` 端口及 `/ready` 路径连接被拒绝 |
| 2 | K8s Config | K8s Config | `container.resource_limit.memory`: `64Mi` (app 容器) | 提供资源配置背景，非当前故障直接证据 |
| 3 | K8s State | K8s Event | Pod `Ready` 状态: `False` (reason: `ContainersNotReady`, message: `containers with unready status: [app]`) | 直接反映应用容器未通过就绪检查 |
| 4 | Metric | Prometheus | `kube_pod_container_status_restarts_total` (app): `0` | 应用运行期间无重启，排除近期容器崩溃导致的连带影响 |
| 5 | Logging | Elasticsearch | `listening on 18080` | 确认应用实际监听端口为 `18080` |

证据间的一致性表明，Pod 虽然处于 `Running` 状态且应用无重启，但探针试图连接应用实际未监听的端口 `18081`，导致了持续的 `connection refused` 和 NotReady 状态。

## 🎯 根因分析 · g1

### 因果链

```text
探针配置目标 (端口 18081, 路径 /ready) → 连接被拒绝 (实际应用监听端口 18080) → 探针持续失败 (connection refused) → Pod 状态 NotReady
```

### 根因结论

已确认根因为 **就绪探针配置错误**。

具体表现为探针的目标端口（18081）与路径（`/ready`）同应用实际运行环境不匹配。证据 #1 显示 kubelet 在 18081 端口发起 `/ready` 请求时被拒绝，而证据 #5 确认应用进程仅监听 18080 端口。这种不匹配直接导致了探针的持续失败，进而将 Pod 标记为 NotReady（证据 #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 15.6s
├─ 并发证据采集: 42.6s
│  └─ g1 aiops-case-v16/workload: 42.6s (Evidence 32.1s, RCA 10.4s)
└─ 汇总总结: 8.4s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
