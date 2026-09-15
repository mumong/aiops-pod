## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Readiness Probe configuration error: mismatched port (probe targets 18081, application listens on 18080) and path (probe targets /ready, application implements /health) causing 'connection refused' errors. |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Unhealthy ... Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` | 证明探针持续失败，直接触发 Pod 状态异常 |
| 2 | Logging | elasticsearch | `listening on 18080` | 提供应用真实监听端口，与探针配置的 18081 端口形成直接冲突 |
| 3 | K8s State | kubernetes | `ContainersReady=False`, `Ready=False`, message: `containers with unready status: [app]` | 确认 Pod 进入非就绪状态，由上述探针失败导致 |

探针配置为向 `18081/ready` 发起请求，但应用进程实际监听在 `18080` 端口（见证据 2）。由于应用未监听探针指定的端口，导致 `connection refused`，进而使得 `ContainersReady` 和 `Ready` 状态持续为 `False`。

## 🎯 根因分析 · g1

### 因果链

```text
探针配置错误 (端口 18081, 路径 /ready) → 探针发出连接请求 → 连接被拒绝 (connection refused) → Pod 状态 NotReady
```

### 根因结论

已确认根因为 **Readiness Probe 配置错误**：探针的端口与路径与应用实际配置不匹配。探针指向的端口 `18081`（见事实 `fact-36edc9b11203`）与应用日志显示的监听端口 `18080`（见事实 `fact-5dd54cd9b22b`）不一致。这一不匹配导致探针请求连续失败，进而使 Pod 的 `ContainersReady` 状态变为 `False`，表现为 Pod NotReady 异常（见事实 `fact-662b93aac53d`）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 19.5s
├─ 并发证据采集: 36.1s
│  └─ g1 aiops-case-v16/workload: 36.1s (Evidence 26.1s, RCA 9.9s)
└─ 汇总总结: 7.3s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
