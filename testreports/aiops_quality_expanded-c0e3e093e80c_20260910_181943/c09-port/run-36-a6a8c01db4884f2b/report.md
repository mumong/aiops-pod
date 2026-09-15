## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod aiops-case-v16/workload 持续处于 NotReady 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Unhealthy 103s (x768 over 61m) kubelet Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` | 确证 Readiness Probe 持续失败，且因连接被拒导致失败（非超时） |
| 2 | K8s State | kubernetes | `Pod aiops-case-v16/workload` 状态 `Running`，`ContainersReady` 为 `False`，`Ready` 为 `False`，`RestartCount` 为 `0` | 确认容器进程在运行且未重启，排除了 CrashLoopBackOff 或 OOMKilled |
| 3 | K8s Config | kubernetes | `container.app` 资源请求 `cpu: 5m, memory: 8Mi`；硬限制 `cpu: 200m, memory: 64Mi` | 提供容器运行资源基线，当前配置下未发生资源竞争导致的存活问题 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total` = `0` (container: `app`) | 独立印证容器未发生异常重启，进一步排除因资源耗尽导致的崩溃 |

证据分析：
`fact-f300cff2f3ef` 显示探针在 18081 端口被拒绝，结合 `fact-0143f2209f01` 容器在 Running 状态且未重启，表明应用程序本身在运行，但其监听端口与探针配置不符。`fact-eed91f8be8e5` 确认了零重启状态，排除了应用因运行资源不足而频繁退出的可能性。

## 🎯 根因分析 · g1

### 因果链

```text
Readiness Probe 配置为 http://:18081/ready → 应用程序实际在端口 18080 监听且仅实现 /health 路径 → Kubelet 发起的探针请求被拒绝 (Connection Refused) → Pod 状态变为 NotReady
```

### 根因结论

已确认的根因为 **Readiness Probe 配置错误**。

探针被配置为探测端口 `18081` 上的路径 `/ready`，但应用程序实际监听的是端口 `18080` 并仅支持 `/health` 端点。这一不匹配导致 Kubelet 发起的探测请求直接返回 `connection refused` (`fact-f300cff2f3ef`)。由于未发生容器崩溃或资源耗尽（`RestartCount` 为 `0`，`fact-eed91f8be8e5`），Pod 虽在运行但因健康检查未通过而持续处于 `NotReady` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 16.6s
├─ 并发证据采集: 38.0s
│  └─ g1 aiops-case-v16/workload: 38.0s (Evidence 31.1s, RCA 6.7s)
└─ 汇总总结: 10.0s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
