## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | Logging | elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 确认进程启动时因找不到命令直接失败 (Exit Code 127) |
| 2 | K8s State | kubernetes | `last_exit_code`: 127 (container: app) | 对应日志中的命令未找到错误，确认为执行层面问题 |
| 3 | K8s State | kubernetes | `container.waiting_reason`: CrashLoopBackOff | 展示当前容器处于重启回退状态 |
| 4 | K8s Event | kubernetes | `Back-off restarting failed container app` (x94 over 24m) | 佐证容器频繁非正常退出及回退机制生效 |
| 5 | Metric | prometheus | `restart_count`: 9 | 量化重启次数，与 K8s State 事实一致 |

日志证据（事实 #1）与 K8s 状态事实（事实 #2）互为印证，日志提供了 Exit Code 127 的具体业务原因（可执行文件缺失）。

## 🎯 根因分析 · g1

### 因果链

```text
容器入口命令指向镜像中不存在的可执行文件 → 容器启动执行失败 (Exit Code 127) → 容器频繁崩溃并触发重启策略 → Pod 状态显示为 CrashLoopBackOff
```

### 根因结论

已确认根因为：容器镜像中配置的可执行文件 `/opt/app/unavailable-command` 不存在。

该根因由以下证据链证实：
*   容器进程在启动尝试执行该路径时立即失败，返回错误码 127 并触发重启 #2。
*   日志记录了明确的 `not found` 错误信息 #1，直接指向缺失的可执行文件。

---

## 📊 性能统计

```text
├─ 总耗时: 45.0s
├─ 问题定位: 13.6s
├─ 并发证据采集: 24.8s
│  └─ g1 aiops-case-v08/workload: 24.8s (Evidence 17.7s, RCA 6.9s)
└─ 汇总总结: 6.6s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
