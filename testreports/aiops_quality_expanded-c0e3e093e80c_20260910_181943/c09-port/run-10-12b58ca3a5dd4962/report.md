## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Readiness Probe 配置错误（端口18081与路径/ready不匹配容器实际监听端口18080及路径/health） |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Warning Unhealthy ... Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` | 证明探针配置与容器实际服务不符，是引发异常的直接原因 |
| 2 | K8s Config | Kubernetes | `container.resource_limit.memory: 64Mi`, `container.resource_request.memory: 8Mi`, `container.resource_limit.cpu: 200m`, `container.resource_request.cpu: 5m` | 资源限制与请求合理，排除资源耗尽导致容器无响应的可能性 |
| 3 | Logging | Elasticsearch | `listening on 18080` | 确认应用实际监听端口为 18080，与探针请求的 18081 冲突 |
| 4 | K8s Event | Kubernetes | `Ready: False, reason: ContainersNotReady, message: containers with unready status: [app]` | 明确展示应用状态未就绪，验证探针失败的后果 |

日志记录显示应用正在 `18080` 端口正常监听且无重启记录（`restart_count: 0`），证明容器进程本身是健康的。然而，Kubernetes 事件明确指出探针在尝试访问 `http://172.16.104.33:18081/ready` 时遭遇 `connection refused`，表明探针配置的目标端口和路径均与实际运行环境不匹配。

## 🎯 根因分析 · g1

### 因果链

```text
探针错误配置（目标端口 18081） → 无法连接实际监听端口（18080） → 状态检查失败 → 容器未就绪且服务被隔离
```

### 根因结论

根因确认为 **Readiness Probe 配置错误**。

证据编号 1 和 3 形成了直接的因果闭环：日志事实证实应用实际监听在端口 `18080`，而探针事件明确显示系统在尝试访问端口 `18081` 时发生连接拒绝。这种端口和路径的严重不匹配导致探针持续失败，进而触发 Kubernetes 将容器标记为 `NotReady`，使其无法接收流量。现有证据已充分说明故障机理，无需补充决定性事实。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 22.2s
├─ 并发证据采集: 36.2s
│  └─ g1 aiops-case-v16/workload: 36.2s (Evidence 29.7s, RCA 6.3s)
└─ 汇总总结: 8.3s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
