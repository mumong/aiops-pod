## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | 容器 'app' 的 Pod 定义中缺失必需的 'APP_REQUIRED_CONFIG' 环境变量，导致应用程序启动时检查失败并主动调用 sys.exit(78) 退出。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | K8s State | container 'app' 配置缺失环境变量 `APP_REQUIRED_CONFIG` | 确定直接导致崩溃的根本配置缺陷 |
| 2 | Logging | Elasticsearch | 日志明确报告 `APP_REQUIRED_CONFIG environment variable is missing` | 证实应用因缺少关键配置而启动失败 |
| 3 | K8s Event | K8s State | `Warning BackOff 81s (x235 over 51m)` 及 `back-off 5m0s restarting failed container=app` | 反映 Pod 处于 CrashLoopBackOff 状态 |
| 4 | K8s State | K8s State | `last_exit_code`: 78 | 证明应用主动退出并返回特定非零状态码 |

**证据说明：**
Kubernetes 指标与事件数据确认了 Pod 处于 `CrashLoopBackOff` 状态并经历大量重启（`reason: Error`）。日志事实与配置事实高度印证：应用因找不到 `APP_REQUIRED_CONFIG` 而主动退出（Exit Code 78），进而触发了 Kubernetes 的重启机制。

## 🎯 根因分析 · g1

### 因果链

```text
缺少 APP_REQUIRED_CONFIG 环境变量配置 → 应用启动检查失败 → 应用调用 sys.exit(78) 主动退出 → 容器反复重启并进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因：**容器 'app' 的 Pod 定义中缺失必需的 `APP_REQUIRED_CONFIG` 环境变量**。
该配置缺失直接导致应用程序在启动阶段检查失败并主动调用 `sys.exit(78)` 退出。此退出被 K8s 视为 Error 状态，进而触发重启，形成 CrashLoopBackOff 现象（证据编号 1, 2, 3, 4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 28.5s
├─ 并发证据采集: 35.2s
│  └─ g1 aiops-case-v10/workload: 35.2s (Evidence 29.8s, RCA 5.3s)
└─ 汇总总结: 6.6s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
