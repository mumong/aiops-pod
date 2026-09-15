## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod aiops-case-v10/workload 的容器定义中缺少环境变量 APP_REQUIRED_CONFIG，导致启动脚本因变量为None主动退出并返回 exit code 78。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container: app, reason: CrashLoopBackOff (fact-3178058bc7d4) | 确认应用容器处于持续重启状态 |
| 2 | K8s State | kubernetes | last_terminated_reason: Error, exit_code: 78 (fact-ed55150d7e5c, fact-c28cf52b2b63) | 确认容器因应用层错误异常退出，非系统资源限制 |
| 3 | K8s Event | kubernetes | Warning BackOff restarting failed container app in pod workload_aiops-case-v10 (d3e0dc86...) (fact-b9389d696773) | 确认 Kubernetes 观察到启动失败并实施指数退避 |
| 4 | Logging | elasticsearch | APP_REQUIRED_CONFIG environment variable is missing (fact-260faff3219a) | 确认应用因缺少关键配置变量导致启动失败 |

**证据关联性说明：**
*   日志事实 (#4) 明确指出了应用层缺失 `APP_REQUIRED_CONFIG` 变量，这解释了容器为何以错误方式退出。
*   K8s State 事实 (#2) 确认退出码为 78，结合日志内容可验证该退出是由应用逻辑（缺少配置）触发的，而非 OOMKill 或健康检查失败等其他原因。
*   K8s State/Event 事实 (#1, #3) 确认了 Pod 层面持续重启（CrashLoopBackOff）的现象，是上述启动失败在集群层面的直接后果。

## 🎯 根因分析 · g1

### 因果链

```text
容器定义中缺少环境变量 APP_REQUIRED_CONFIG → 应用启动脚本因变量为None主动退出 (exit code 78) → 容器状态转为 Error → K8s 触发 CrashLoopBackOff 并持续重启
```

### 根因结论

**已确认根因**：Pod `aiops-case-v10/workload` 的容器定义中缺失必需的环境变量 `APP_REQUIRED_CONFIG`。

**分析依据**：
*   **日志直接证据**：Elasticsearch 日志中明确记录 `APP_REQUIRED_CONFIG environment variable is missing` (见证据 #4)。
*   **退出行为印证**：容器以 exit code 78 (通常用于表示应用程序内部错误或配置缺失) 异常退出 (见证据 #2)，这与缺失关键配置变量的行为一致。
*   **状态持续**：Kubernetes 显示容器处于 `CrashLoopBackOff` 状态 (见证据 #1, #3)，表明每次启动都因同样的原因失败。

现有证据已足以构成闭环诊断，无需更多观察数据。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 20.8s
├─ 并发证据采集: 35.7s
│  └─ g1 aiops-case-v10/workload: 35.7s (Evidence 30.8s, RCA 4.8s)
└─ 汇总总结: 9.3s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
