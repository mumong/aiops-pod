## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v10/workload` | CrashLoopBackOff | Pod aiops-case-v10/workload 的 app 容器处于 CrashLoopBackOff 状态，重启计数 10 次。 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s Event | Kubernetes | Back-off restarting failed container app (3m49s ago, x118 over 28m) | 确认容器频繁崩溃且集群正在进行重启恢复尝试 |
| 2 | K8s State | Kubernetes | exit_code: 78, last_terminated_reason: Error | 记录异常退出的具体原因与退出码，作为诊断线索 |
| 3 | Logging | Elasticsearch | APP_REQUIRED_CONFIG environment variable is missing | 提供直接证据，证明程序因缺失配置变量而主动报错退出 |
| 4 | Metric | Prometheus | restart_count: 10, last_terminated_reason: Error | 独立验证容器重启状态与终止原因的一致性 |

**证据关联说明：**
日志记录的 "APP_REQUIRED_CONFIG environment variable is missing" 解释了 K8s 记录的具体 `exit_code: 78`。该退出直接导致 Pod 进入 CrashLoopBackOff 状态（重启 10 次），且日志与退出码在因果链上形成了完整的闭环。

## 🎯 根因分析 · g1

### 因果链

```text
容器配置中未定义环境变量 APP_REQUIRED_CONFIG → 启动命令检查到该变量缺失 → 应用程序主动打印错误并调用 sys.exit(78) 退出 → 触发 K8s 重启策略导致 CrashLoopBackOff
```

### 根因结论

已确认的根因为：容器启动命令因缺失必需的环境变量 `APP_REQUIRED_CONFIG` 而执行了主动退出（`sys.exit(78)`）。证据表明该异常并非由资源耗尽或系统故障引起，而是应用层面的配置缺失导致程序直接终止（引用证据 #2, #3）。

未确认项：为何 `APP_REQUIRED_CONFIG` 变量在 Deployment 或 PodSpec 中遗漏（配置管理层面），或是否存在关联的 ConfigMap/Secret 试图注入但未生效。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 23.6s
├─ 并发证据采集: 40.4s
│  └─ g1 aiops-case-v10/workload: 40.4s (Evidence 31.2s, RCA 9.1s)
└─ 汇总总结: 6.7s
```

📋 Runbook 参考

- **g1 aiops-case-v10/workload**: pod-crashloop-runtime
