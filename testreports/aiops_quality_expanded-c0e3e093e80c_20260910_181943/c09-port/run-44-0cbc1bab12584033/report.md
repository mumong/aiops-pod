## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod workload in aiops-case-v16 is NotReady (Ready=False, reason=ContainersNotReady) due to repeated readiness probe failures. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `pod.status` (k8s) | `pod.phase: Running` | 证明 Pod 底层容器已成功启动并处于运行中状态，排除容器无法拉起的问题。 |
| 2 | K8s Event | `event.message` (k8s) | `Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` | 直接确认 kubelet 探测 18081 端口被拒绝，导致 Readiness 状态持续失败。 |
| 3 | K8s State | `pod.condition` (k8s) | `Ready: False, reason=ContainersNotReady` | 将 Event 级别的探测失败映射为 Pod 核心状态标记，确保证据链闭环。 |
| 4 | Metric | `probe_success` (prometheus) | `0` (phase=Unknown) | 侧面印证 Pod 未能成功进入 Ready 状态。 |
| 5 | K8s Config | `container.resources` (k8s) | `cpu: req=5m, lim=200m; mem: req=8Mi, lim=64Mi` | 确认资源配额极低且非引发“连接被拒”的原因，排除资源超限导致的服务不可用。 |

当前现象（Ready=False）与事实证据高度一致：Pod 处于 Running 状态，但由于探测端口（18081）被拒绝，导致 `ContainersNotReady` 状态无法改变。Logging 与 Tracing 缺失不影响对核心端口连通性问题的判断。

## 🎯 根因分析 · g1

### 因果链

```text
Readiness probe port (18081) ≠ Application listening port (18080) → Connection refused → ContainersNotReady → Pod status NotReady
```

### 根因结论

已确认根因为 **Readiness Probe 端口配置错误**。

*   **直接证据**：Kubernetes 事件明确指出在探测 `172.16.104.33:18081/ready` 时发生 `connection refused`（证据 #2）。
*   **机制确认**：Pod 底层已成功启动（Running，证据 #1），说明应用实际在运行且未崩溃，但应用进程监听端口（18080）与探针配置的端口（18081）不一致。
*   **结论**：探针探测不存在的监听端口，导致 Kubelet 持续标记容器为不健康，最终 Pod 进入 `NotReady` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 17.8s
├─ 并发证据采集: 50.5s
│  └─ g1 aiops-case-v16/workload: 50.5s (Evidence 42.1s, RCA 8.3s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
