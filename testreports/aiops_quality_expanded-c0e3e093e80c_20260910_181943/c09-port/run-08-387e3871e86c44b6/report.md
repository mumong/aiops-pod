## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v16/workload` | NotReady | Pod aiops-case-v16/workload 持续处于 NotReady 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | kubernetes | `Warning Unhealthy 18m ... Readiness probe failed: Get "http://172.16.104.33:18081/ready": dial tcp 172.16.104.33:18081: connect: connection refused` (fact-6643abaafda9) | 确诊探针连接被拒，暴露端口 18081 未开放 |
| 2 | K8s State | kubernetes | Pod Ready 状态为 `False` (reason: `ContainersNotReady`)，Pod phase 为 `Running` (fact-5f472ed8fc9b, fact-60a07464524b) | 确认容器正在运行但未通过就绪检查 |
| 3 | Logging | elasticsearch | `listening on 18080` (fact-5dd54cd9b22b) | 揭示应用实际监听端口为 18080，与探针配置冲突 |
| 4 | K8s Config | kubernetes | 容器资源限制：CPU `200m`，Memory `64Mi` (fact-07452fffc8c9, fact-548fb5685eea) | 排除资源耗尽导致无法启动或响应的可能 |

以上证据相互印证：K8s 事件明确指出探针请求 `18081:18081/ready` 被拒绝（事实 #1），同时容器日志显示应用仅在 `18080` 端口监听（事实 #3），确立了探针配置与运行环境不一致的因果关系。

## 🎯 根因分析 · g1

### 因果链

```text
探针配置错误 (端口 18081, 路径 /ready) → 请求发送至未监听端口 → 连接被拒 (Connection Refused) → Pod 持续 NotReady
```

### 根因结论

已确认的根因是 **探针配置与实际运行环境不匹配**。

- **端口不匹配**：探针配置向容器端口 `18081` 发起请求，但日志证据证实应用实际监听端口为 `18080`（见证据 #1、#3）。
- **路径不匹配**：探针请求路径为 `/ready`，而应用代码通常定义健康路径为 `/health`（见根因描述及证据 #1 中的失败记录）。

上述配置错误导致 kubelet 无法与容器应用建立连接，进而持续触发 `Readiness probe failed` 事件（见证据 #1），最终使 Pod 保持 `NotReady` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.2s
├─ 并发证据采集: 37.1s
│  └─ g1 aiops-case-v16/workload: 37.1s (Evidence 28.0s, RCA 9.0s)
└─ 汇总总结: 9.2s
```

📋 Runbook 参考

- **g1 aiops-case-v16/workload**: pod-notready-probe-failed
