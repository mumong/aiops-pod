## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | 容器 `app` 的 command 脚本强依赖环境变量 `APP_REQUIRED_CONFIG`，但 Pod 定义中该变量未配置（Environment: <none>），导致进程启动时检查缺失主动退出（exit code 78），Kubernetes 按 `restartPolicy=Always` 反复重启直至进入 CrashLoopBackOff。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Config | kubernetes | Environment: <none> | 确认容器定义中缺失关键环境变量 `APP_REQUIRED_CONFIG`，构成故障前置条件 |
| 2 | K8s Event | kubernetes | `Warning BackOff... Back-off restarting failed container app` (fact-10a043e567a1) | 证实容器因启动失败触发重启退避机制 |
| 3 | Logging | elasticsearch | `APP_REQUIRED_CONFIG environment variable is missing` (fact-15fa015b88a8) | 提供进程退出时的直接错误日志，明确缺失变量的位置 |
| 4 | K8s State | kubernetes | `container.exit_code: 78` (fact-1e9cba681e54) | 结合日志确认进程因配置缺失主动退出而非崩溃 |

**证据说明：**
Kubernetes 事件 (fact-10a043e567a1) 与日志 (fact-15fa015b88a8) 形成闭环：配置中缺失变量导致应用启动检查失败（日志记录），退出码 78 (fact-1e9cba681e54) 导致 K8s 判定异常并触发 BackOff 重启（事件记录）。

## 🎯 根因分析 · g1

### 因果链

```text
Pod YAML 未定义环境变量 `APP_REQUIRED_CONFIG` → 容器 `app` 启动执行检查逻辑：检测 `os.getenv('APP_REQUIRED_CONFIG')` 为 None → 进程主动打印错误日志并执行 `sys.exit(78)` 退出 → Kubernetes 重启容器触发指数退避，最终进入 CrashLoopBackOff 状态
```

### 根因结论

根因确认为**容器应用配置错误**：`app` 容器的 command 脚本强依赖环境变量 `APP_REQUIRED_CONFIG`，但 Pod 定义中未配置该变量（Environment: <none>），导致启动时检查失败主动退出（exit code 78），进而触发 K8s 重启机制进入 CrashLoopBackOff。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 22.0s
├─ 并发证据采集: 46.0s
│  └─ g1 aiops-case-v10/workload: 46.0s (Evidence 35.9s, RCA 10.0s)
└─ 汇总总结: 7.4s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
