## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | `container.last_exit_code`: 127 | 确认容器因命令/程序不存在而退出（标准 POSIX 错误码） |
| 2 | K8s Event | Kubernetes | `event.message`: "Warning  BackOff         24s (x234 over 50m)" | 证实重启已陷入指数退避循环（50分钟内重启234次） |
| 3 | Logging | Elasticsearch | `log.message`: "sh: exec: line 0: /opt/app/unavailable-command: not found" | 直接证明镜像中缺少指定可执行文件，导致 Shell 执行失败 |
| 4 | K8s State | Kubernetes | `pod.condition.Ready`: False, `reason`: ContainersNotReady | 描述因容器崩溃导致的最终可用状态 |
| 5 | Metrics | Prometheus | `kube_pod_container_status_restarts_total`: 14 (截至 2026-09-11T13:53:17Z) | 确认当前重启总次数 |
| 6 | K8s Config | Kubernetes | `resource_request`: cpu 5m, memory 8Mi; `resource_limit`: cpu 50m, memory 32Mi | 资源请求与限制极低，排除因资源争抢（OOM/Throttling）导致崩溃的可能 |

**证据关联分析：**
日志 `fact-13cb3242823d` 显示的错误信息 `not found` 与 K8s 状态 `fact-5c2b5ce7c64d` 中的退出码 127 完全匹配，确认了启动失败的技术机制。该失败机制直接触发了 Kubelet 的重启逻辑，进而表现为 `fact-8e9a2b5e6db7` 中的 BackOff 警告。

## 🎯 根因分析 · g1

### 因果链

```text
Pod 配置指定了镜像中不存在的可执行文件路径 `/opt/app/unavailable-command` → 
容器启动时 Shell 执行失败并退出 (Exit Code 127) → 
Kubelet 触发重启并进入 BackOff 机制 → 
用户可见 CrashLoopBackOff 状态与 Ready=False
```

### 根因结论

已确认根因为**容器启动配置错误**：
1. **具体原因**：容器配置的启动命令指向了一个在容器镜像中不存在的可执行文件 `/opt/app/unavailable-command`。
2. **证据支撑**：
   - 日志证据 `fact-13cb3242823d` 明确指出系统提示找不到该文件 (`not found`)。
   - 系统日志证据 `fact-5c2b5ce7c64d` 确认容器以退出码 127 终止，这是典型的“命令未找到”信号。
   - 这些证据共同导致容器反复崩溃，最终因指数退避限制进入 `CrashLoopBackOff` 状态。

---

## 📊 性能统计

```text
├─ 总耗时: 1.0m
├─ 问题定位: 11.1s
├─ 并发证据采集: 40.2s
│  └─ g1 aiops-case-v08/workload: 40.2s (Evidence 33.8s, RCA 6.3s)
└─ 汇总总结: 10.2s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
