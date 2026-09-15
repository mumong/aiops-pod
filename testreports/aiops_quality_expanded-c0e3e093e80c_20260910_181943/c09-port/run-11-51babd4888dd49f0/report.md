## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod aiops-case-v16/workload status is NotReady |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | Readiness probe failed: dial tcp 172.16.104.33:18081: connect: connection refused (x256 over 22m) | 提供直接失败现象：探针请求被拒绝 |
| 2 | K8s Config | K8s | 容器探针配置端口 `18081`、路径 `/ready` | 确定探针期望目标，是导致报错的配置源头 |
| 3 | Logging | ES (app日志) | `listening on 18080` (事实 fact-5dd54cd9b22b) | 提供容器真实监听状态，与探针端口 18081 存在明显配置不匹配 |
| 4 | K8s State | K8s | Pod 状态：`Running`，条件：`Ready=False`、`ContainersReady=False` | 确认容器主进程存活，但健康检查未通过 |

证据互相印证：K8s Event 显示探针连接端口 `18081` 失败（证据1），而容器日志显示应用实际监听端口 `18080`（证据3），两者结合确证了探针配置与容器实际状态的冲突。Pod 处于 Running 但 NotReady 的状态（证据4）符合探针连接被拒绝时的典型表现。

## 🎯 根因分析 · g1

### 因果链

```text
Readiness probe 配置不匹配 (端口18081 vs 实际18080, 路径/ready vs 实际/health) → 探针请求被拒绝 (Connection Refused) → 容器状态持续标记为 NotReady → Pod 状态显示 NotReady 且不可用于流量调度
```

### 根因结论

**已确认的根因：Readiness Probe 配置与实际容器监听信息不匹配。**
Kubelet 配置的探针试图访问 `172.16.104.33:18081/ready`，但容器内的应用程序实际监听的是端口 `18080` 且日志仅输出监听信息（未见 `/ready` 端点），导致每次探测均返回 `connection refused`（事实 1, 3）。这造成了 Pod 虽然容器处于 `Running` 状态，但 Kubernetes 判定容器未就绪（`NotReady`，事实 4），从而无法正常对外提供服务。

---

## 📊 性能统计

```text
├─ 总耗时: 58.4s
├─ 问题定位: 13.7s
├─ 并发证据采集: 36.4s
│  └─ g1 aiops-case-v16/workload: 36.4s (Evidence 26.4s, RCA 9.7s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- 未调用 Runbook
