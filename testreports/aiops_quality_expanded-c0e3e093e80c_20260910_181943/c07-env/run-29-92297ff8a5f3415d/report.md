## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod aiops-case-v10/workload 处于 CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.waiting_reason`: CrashLoopBackOff; `container.last_terminated_reason`: Error | 确认应用频繁异常终止且处于重启退避状态 |
| 2 | K8s State | kubernetes | `container.last_exit_code`: 78 | 锁定进程退出时的系统返回码 |
| 3 | K8s Event | kubernetes | `BackOff         3m27s (x235 over 53m)  kubelet            Back-off restarting failed container app` | 提供容器启动失败的历史频率与退避时长证据 |
| 4 | Logging | elasticsearch | `APP_REQUIRED_CONFIG environment variable is missing` | 直接指出应用启动失败的具体原因（缺少关键环境变量） |

日志中明确指出的缺失环境变量 `APP_REQUIRED_CONFIG` 结合容器退出码 `78` 与终止原因 `Error`，共同指向应用启动阶段的配置缺失导致进程主动异常退出。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 定义未配置环境变量 APP_REQUIRED_CONFIG → 应用检查环境缺失并 sys.exit(78) → kubelet 检测异常退出并触发重启 → CrashLoopBackOff
```

### 根因结论

已确认的根因为 Pod 中缺失必需的环境变量 `APP_REQUIRED_CONFIG`。应用进程在启动阶段因发现该关键配置缺失（见 Logging 证据 #4）而执行了退出码 78 的退出逻辑，导致容器反复崩溃并触发 K8s 的重启退避机制（见 K8s State 证据 #1-2 与 K8s Event 证据 #3）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 16.7s
├─ 并发证据采集: 45.9s
│  └─ g1 aiops-case-v10/workload: 45.9s (Evidence 36.6s, RCA 9.2s)
└─ 汇总总结: 6.2s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
