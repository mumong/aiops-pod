## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | 容器配置遗漏环境变量 `APP_REQUIRED_CONFIG` 导致应用启动时主动退出 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | `Back-off 5m0s restarting failed container=app pod=workload_aiops-case-v10(d3e0dc86-6f8b-4f29-a50c-826bf2a1f1e6)` | 确认异常发生频率与重试周期 |
| 2 | K8s Config | Kubernetes | `container.resource_limit.cpu=50m, memory=32Mi; request: cpu=5m, memory=8Mi` | 证明无资源限制导致的 OOMKilled |
| 3 | Logging | Elasticsearch | `"APP_REQUIRED_CONFIG environment variable is missing"` | 直接定位应用崩溃的具体技术原因 |
| 4 | K8s State | Kubernetes | `container.last_exit_code: 78` | 应用层面的主动错误退出码 |

1. 日志事实（#3）直接揭示了应用启动失败的具体原因（缺失环境变量），这与 K8s 报告的 `CrashLoopBackOff` 状态（#1）及退出码 78（#4）形成因果闭环。
2. Kubernetes 的 CPU 和内存限制配置极低但稳定（#2），排除了因资源争抢导致 Pod 被驱逐的可能，进一步支撑了配置错误导致的启动失败。

## 🎯 根因分析 · g1

### 因果链

```text
容器配置遗漏环境变量 `APP_REQUIRED_CONFIG` → 应用启动时主动退出 → 容器重启失败 → 进入 CrashLoopBackOff 状态
```

### 根因结论

**已确认根因**：Pod `workload_aiops-case-v10` 中 `app` 容器因缺少必需的环境变量 `APP_REQUIRED_CONFIG` 导致启动时主动退出。
该结论由以下事实确证：
- 日志明确报错 `APP_REQUIRED_CONFIG environment variable is missing`（证据 #3）。
- 容器退出码为 78（证据 #4），表明应用逻辑而非运行时异常导致了退出。
- K8s 资源限制处于极低水位但非导致 CrashLoopBackOff 的原因（证据 #2）。

---

## 📊 性能统计

```text
├─ 总耗时: 52.4s
├─ 问题定位: 22.5s
├─ 并发证据采集: 22.4s
│  └─ g1 aiops-case-v10/workload: 22.4s (Evidence 18.4s, RCA 3.9s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
