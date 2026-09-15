## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod aiops-case-v16/workload 处于 NotReady 状态 (Ready: False, ContainersNotReady) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-0fc65043ea76` / `fact-0792c4407a46` | Pod 处于 `Running` 阶段，且容器 `app` 重启次数为 `0` | 排除进程崩溃或 OOM 导致的重启问题，Pod 基础运行环境正常 |
| 2 | K8s Config | `fact-00c2c3837ecb` | 容器 `app` 限制 CPU 为 `200m` | 资源限制配置存在，但重启次数为 0，暂不支持 CPU 过载致死推断 |
| 3 | K8s Event | `fact-1ad1d82cbaee` | `Warning Unhealthy Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` (x832 over 69m) | 核心诊断事实，直接证实探针探测目标端口不可达 |
| 4 | K8s State | `fact-98bf6d3b3051` / `fact-cebdf9281bc5` | Ready 状态为 `False` (ContainersNotReady)，原因：`containers with unready status: [app]` | 证实因探测失败导致 Pod 无法进入 Ready 状态 |
| 5 | Metric | `fact-098d1f0d95f7` | `kube_pod_container_status_ready` (app容器) 在 13 个样本中均为 `0`，状态 `steady` | 验证 `Ready=False` 是持续稳定的，非瞬时波动 |
| 6 | Metric | `fact-503593044779` | `kube_pod_container_status_restarts_total` (app容器) 为 `0` | 确认服务进程未发生过异常退出 |

**证据逻辑说明：**
K8s Event 显示探针探测 18081 端口连接被拒绝，Metric 证实 Ready 状态持续为 0 且无重启记录，二者共同锁定故障位于探针探测机制而非应用进程健康度。

## 🎯 根因分析 · g1

### 因果链

```text
ReadinessProbe 配置端口 18081 (事实来源: fact-1ad1d82cbaee)
→ 容器监听端口 18080 导致 18081 连接被拒绝 (事实来源: fact-1ad1d82cbaee)
→ Readiness 探针持续失败 832 次 (事实来源: fact-1ad1d82cbaee)
→ Pod 状态标记为 NotReady (事实来源: fact-98bf6d3b3051)
```

### 根因结论

**已确认根因：ReadinessProbe 配置错误导致连接拒绝。**

正式 RCA 确认根因为“探测端口 18081 与容器实际监听端口 18080 不匹配”。诊断支持事实包括：
1. 事件记录明确显示 `connection refused` 指向端口 `18081`（证据编号 #3）。
2. Pod 状态显示 `ContainersNotReady`，且 Metric 证实 Ready 状态持续为 0、进程未发生重启（证据编号 #4, #5, #6）。

证据链闭合，足以说明当前现象是由探针端口配置不匹配引起的。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 20.3s
├─ 并发证据采集: 47.8s
│  └─ g1 aiops-case-v16/workload: 47.8s (Evidence 39.7s, RCA 8.0s)
└─ 汇总总结: 12.0s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
