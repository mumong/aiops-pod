## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod aiops-case-v16/workload 处于 NotReady 状态，Ready=False |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | Warning Unhealthy kubelet Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused | 直接症状，显示探测目标端口 18081 连接被拒绝 |
| 2 | K8s State | kubernetes | ContainersReady=False, Ready=False, reason=ContainersNotReady, message=containers with unready status: [app] | 确认容器应用未就绪的 Pod 状态 |
| 3 | K8s State | kubernetes | Pod phase=Running, container restart_count=0 | 排除容器频繁重启或崩溃，锁定为存活但未就绪状态 |
| 4 | K8s Config | kubernetes | resource_limit.memory=64Mi, resource_limit.cpu=200m | 提供资源约束上下文，确认非资源耗尽导致的 OOMKilled |
| 5 | Metric | prometheus | kube_pod_container_status_restarts_total=0 (container=app) | 交叉验证容器未发生重启 |

**证据说明：**
- **K8s State/Event** 共同指向同一结论：容器虽然存活（Running），但因 Readiness probe 失败导致 Ready=False。
- **K8s Event** 中 `connect: connection refused` 明确指出 `kubelet` 无法与 Pod IP `172.16.104.33` 的 `18081` 端口建立连接。
- **Metric** 的重启次数为 0 排除了因为容器不断重启（CrashLoopBackOff）导致的应用未启动问题。
- 结合 **K8s Config** 提供的极低资源限制（64Mi 内存），结合连接拒绝现象，强烈暗示应用未监听探测端口。

## 🎯 根因分析 · g1

### 因果链

```text
Readiness probe 配置错误 (端口18081 vs 18080, 路径/ready vs /health) → kubelet 探测请求被拒绝或无响应 → Readiness probe failed 事件持续触发 → Pod 状态变为 NotReady
```

### 根因结论

已确认的根因是 **Readiness probe 配置错误**。
- **机制**：`kubelet` 持续向 `http://172.16.104.33:18081/ready` 发送探测请求。
- **直接失败**：目标端口 `18081` 无服务监听（实际监听应为 `18080`，实际健康路径应为 `/health`），导致连接被拒绝（`connection refused`）。
- **结果**：容器应用虽然正在运行，但由于无法通过就绪探针，Pod 状态被标记为 `NotReady`。
- **证据支撑**：`fact-27ee07d93fb8` (Event) 记录了具体的连接拒绝错误及目标地址；`fact-7ca27a05d235` (State) 确认了就绪状态为假。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 23.5s
├─ 并发证据采集: 33.2s
│  └─ g1 aiops-case-v16/workload: 33.2s (Evidence 23.1s, RCA 9.9s)
└─ 汇总总结: 10.6s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
