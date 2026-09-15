## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod aiops-case-v16/workload status is NotReady |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | `fact-1983f9193184`, `fact-df61983edca7` | Phase: Running | 确定 Pod 容器进程已在运行。 |
| 2 | K8s State | `fact-2926ea971cb4`, `fact-88b06b7e4d71` | Ready: False; Reason: ContainersNotReady | 明确应用当前不具备接收流量的状态。 |
| 3 | K8s Event | `fact-fd2a3cbca96c` | `Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` | 直接证实 Kubelet 因端口未监听被内核拒绝导致 Probe 失败。 |
| 4 | Logging | `fact-5dd54cd9b22b` | `listening on 18080` | 证实实际业务监听端口（18080）与 Probe 探测端口（18081）存在不匹配。 |

当前现象由直接因果链支撑：K8s 事件与指标确认了应用处于运行状态，但日志揭示的业务实际监听端口（18080）与 K8s Probe 目标端口（18081）不一致，导致连接被拒绝，进而触发未就绪状态。

## 🎯 根因分析 · g1

### 因果链

```text
Readiness Probe 配置错误（目标端口 18081） → Kubelet 对应用容器发起 HTTP GET 请求（未监听该端口） → 内核直接拒绝连接（Connection refused） → Pod Ready 状态变为 False，进入 NotReady 状态
```

### 根因结论

已确认的根因为**探针端口配置不匹配**。具体表现为应用容器实际监听在 `18080` 端口（证据 #4），而 K8s 配置的 Readiness Probe 尝试探测 `18081` 端口，直接导致 Kubelet 接收 `connection refused` 错误（证据 #3）。该错误触发 Pod `Ready` 条件变为 `False`（证据 #2），表现为 Pod 处于 `NotReady` 状态，尽管容器本身处于 `Running`（证据 #1）且未发生重启（`restart_count=0`，指标无重启）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.8m
├─ 问题定位: 21.5s
├─ 并发证据采集: 77.7s
│  └─ g1 aiops-case-v16/workload: 77.7s (Evidence 70.8s, RCA 6.8s)
└─ 汇总总结: 8.7s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
