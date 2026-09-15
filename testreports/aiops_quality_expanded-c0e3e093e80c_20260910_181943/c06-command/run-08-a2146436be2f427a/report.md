## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod aiops-case-v08/workload 处于 CrashLoopBackOff 状态 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container `app` exit_code: 127 | 确认进程因命令未找到立即终止 |
| 2 | K8s Event | Kubernetes | Warning BackOff (x25 over 9m44s): "Back-off restarting failed container app" | 确认反复重启及退避行为 |
| 3 | Logging | Elasticsearch | "sh: exec: line 0: /opt/app/unavailable-command: not found" | 直接证明启动命令执行失败 |
| 4 | K8s Config | Kubernetes | container `app` resource_request.memory: 8Mi; resource_limit.memory: 32Mi | 排除内存资源不足导致的 OOM 终止 |

证据链：日志 `not found` (Fact #3) 解释了退出码 `127` (Fact #1) 的根本原因；Kubernetes 事件 (Fact #2) 确认了该异常导致的状态转换。资源配置 (Fact #4) 显示内存请求极低但并非零，且 `127` 退出码非 OOM Killer 特征，进一步排除资源争抢可能。

## 🎯 根因分析 · g1

### 因果链

```text
容器镜像中缺少二进制文件 /opt/app/unavailable-command → 容器启动命令执行失败，进程退出并返回 exit code 127 (command not found) → Kubernetes 检测到容器持续非正常退出，触发重启退避逻辑 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为 **容器启动命令配置指向了镜像中不存在的二进制文件**。
具体表现为：Pod 容器 `app` 尝试执行 `/opt/app/unavailable-command`，但该文件在镜像中不存在，导致进程以 `exit code 127` 失败退出 [Fact #1]。Kubernetes 日志确认了该错误信息为 "not found" [Fact #3]，随后的反复重启导致了 CrashLoopBackOff 状态 [Fact #2]。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 17.0s
├─ 并发证据采集: 40.0s
│  └─ g1 aiops-case-v08/workload: 40.0s (Evidence 31.1s, RCA 8.7s)
└─ 汇总总结: 7.1s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
