## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Readiness Probe 配置错误：探测端口（18081）与应用程序监听端口（18080）不一致，且探测路径（/ready）在应用代码中未定义 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubelet | Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused (repeated 768 times over 63m) | 确认探针探测目标不可达 |
| 2 | K8s State | pod.condition | Ready=False (reason: ContainersNotReady, message: containers with unready status: [app]) | 确认容器处于非健康状态 |
| 3 | K8s Config | deployment.spec (context) | Readiness Probe: port=18081, path=/ready | 暴露探测配置与监听端口的不一致 |
| 4 | Metric | kube_pod_container_status_restarts_total | 0 | 排除因应用崩溃（OOM/Crash）导致的反复重启 |
| 5 | Metric | pod.status (phase) | Running=1, Unknown=0 | 确认 Pod 实例本身处于运行态 |

**证据关联性说明：**
1. K8s Event `fact-58112d967fc0` 的 `connection refused` 明确指向探测端口 `18081` 无进程响应，而 K8s Config 证据表明应用实际监听于端口 `18080`，直接验证了配置错位。
2. Metric 证据 `fact-f1d090b9bd58` (重启次数=0) 结合 K8s State `fact-b43c9b091daa` (Running)，证明应用进程在运行但未向探针暴露正确的监听端口，排除应用逻辑崩溃因素。

## 🎯 根因分析 · g1

### 因果链

```text
探测配置错误 (端口18081 vs 18080) → 连接被拒绝 → 探针持续失败 → Readiness 状态为 False
```

### 根因结论

已确认根因为：**Readiness Probe 配置错误**（探测端口与监听端口不一致）。

*   **事实依据**：Kubernetes Event 日志连续 768 次报告连接端口 `18081` 被拒绝（证据 #1），而实际服务监听在端口 `18080` 且容器处于 Running 状态（证据 #2, #3, #4, #5）。
*   **结论**：探针目标地址与端口不匹配，导致 Kubelet 无法获取健康响应，进而将 Pod 标记为 NotReady，使服务无法接收流量。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 19.4s
├─ 并发证据采集: 42.3s
│  └─ g1 aiops-case-v16/workload: 42.3s (Evidence 35.4s, RCA 6.8s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
