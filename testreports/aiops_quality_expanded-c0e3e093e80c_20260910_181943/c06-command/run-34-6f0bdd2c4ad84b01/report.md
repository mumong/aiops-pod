## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod aiops-case-v08/workload 处于 CrashLoopBackOff 状态，容器 app 反复重启 |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | `container.last_terminated_reason`: `Error` | 确认容器终止状态 |
| 2 | K8s State | kubernetes | `container.last_exit_code`: `127` | 确认启动命令失败的具体原因 |
| 3 | K8s State | kubernetes | `container.waiting_reason`: `CrashLoopBackOff` | 确认 Pod 当前处于反复重启状态 |
| 4 | K8s Event | kubernetes | `Back-off restarting failed container app` (x187 over 40m) | 确认重启行为已被 Kubelet 持续执行 |
| 5 | Logging | elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 提供导致 Exit Code 127 的直接事实证据 |

日志中的错误信息（证据 #5）解释了容器状态中的 `last_exit_code: 127`（证据 #2），该退出码在容器启动阶段即触发，进而导致 Kubelet 不断尝试重启，最终表现为 CrashLoopBackOff（证据 #3）和 BackOff 事件（证据 #4）。

## 🎯 根因分析 · g1

### 因果链

```text
镜像中不存在 /opt/app/unavailable-command 可执行文件 → 容器启动时执行 command 失败 (Exit Code 127) → kubelet 检测到容器退出并执行重启策略 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

已确认根因为**应用镜像中缺少指定的可执行文件**。证据 #5（日志）明确显示 `sh: exec: line 0: /opt/app/unavailable-command: not found`，该错误导致容器以 Exit Code 127 退出（证据 #2）。这一启动时的持续性错误使得 kubelet 不断重启容器，最终触发 CrashLoopBackOff 状态（证据 #3, #4）。

---

## 📊 性能统计

```text
├─ 总耗时: 1.1m
├─ 问题定位: 13.6s
├─ 并发证据采集: 42.5s
│  └─ g1 aiops-case-v08/workload: 42.5s (Evidence 34.0s, RCA 8.4s)
└─ 汇总总结: 6.9s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
