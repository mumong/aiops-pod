## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod workload (aiops-case-v08) 状态 CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | Logging | elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 提供决定性事实：明确指明容器启动时无法执行指定命令 |
| 2 | K8s State | kubernetes | `container.last_exit_code`: 127 | 佐证命令执行失败（退出码 127 对应 Command Not Found） |
| 3 | K8s Event | kubernetes | `Back-off restarting failed container app` (x234 over 52m) | 确认异常持续时长与系统触发指数退避重试的机制 |
| 4 | Metric | prometheus | `kube_pod_container_status_restarts_total`: 15 | 量化重启频率，确认重启并非偶发 |
| 5 | K8s Config | kubernetes | `container.resource_limit.cpu`: 50m, `resource_limit.memory`: 32Mi | 确认资源限制配置；排除资源耗尽（OOM/CPULimit）导致 Crash 的可能 |

**证据说明**：
Metric 数据（#4）与 K8s Event 数据（#3）共同证实了异常的持续性与系统级的重试行为。Logging 提供的原始错误日志（#1）直接指向具体的失败命令，这与容器退出码 127（#2）严格对应，构成了完整的“启动失败”因果链，排除了配置错误或系统限制等其他潜在因素。

## 🎯 根因分析 · g1

### 因果链

```text
启动命令 /opt/app/unavailable-command 在镜像中不存在 → 容器进程返回 exitCode 127 (Command Not Found) → kubelet 触发 BackOff 指数退避重试 → Pod 状态 CrashLoopBackOff
```

### 根因结论

已确认根因为：启动命令配置错误（`/opt/app/unavailable-command`）。

**依据**：
1. Logging 维度（事实 #1）直接捕获到 `not found` 错误，明确指出了失败的执行路径。
2. K8s State 维度（事实 #2）显示的退出码 127 与上述命令未找到的情况完全一致。
3. 结合 K8s Config 维度（事实 #5）证明资源配置极低但非导致命令找不到的原因，且 Metric 维度（事实 #4）确认了由此导致的持续崩溃循环。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 15.8s
├─ 并发证据采集: 41.4s
│  └─ g1 aiops-case-v08/workload: 41.4s (Evidence 34.5s, RCA 6.8s)
└─ 汇总总结: 8.2s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
