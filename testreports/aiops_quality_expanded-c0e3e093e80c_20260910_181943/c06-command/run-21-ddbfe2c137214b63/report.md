## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | workload pod is in CrashLoopBackOff state with repeated restarts (restarts=9). |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | kubernetes | container last_terminated_reason: Error; waiting_reason: CrashLoopBackOff; waiting_message: back-off 5m0s restarting failed container=app; restart_count: 9 | 确认 `app` 容器陷入持续的崩溃重启循环，当前状态为 `CrashLoopBackOff`，已重启 9 次。 |
| 2 | K8s Event | kubernetes | Warning BackOff 30s (x118 over 25m) Back-off restarting failed container app | 记录容器启动失败后 kubelet 触发的指数退避重试机制，佐证崩溃现象的持续存在。 |
| 3 | K8s Config | kubernetes | container resource_request.cpu: 5m; memory: 8Mi; resource_limit.cpu: 50m; memory: 32Mi | 容器资源请求极低，排除了 OOM 或 CPU 限频导致异常退出的可能性。 |
| 4 | K8s State | kubernetes | container last_exit_code: 127 | 明确指示容器进程启动失败的原因为“命令未找到”（Command Not Found）。 |
| 5 | Logging | elasticsearch | log.message: sh: exec: line 0: /opt/app/unavailable-command: not found | 直接捕获到容器初始化脚本执行失败的确切错误日志，指明命令 `/opt/app/unavailable-command` 在路径中不存在。 |

**证据关联说明**：
K8s 状态确认了 CrashLoopBackOff 现象，而日志（#5）与退出码（#4）形成了直接印证：退出码 127 精确对应 Shell 报错中的 "not found" 提示，排除了网络、依赖或资源不足等其他潜在原因。

## 🎯 根因分析 · g1

### 因果链

```text
镜像中缺失文件 '/opt/app/unavailable-command' → 容器命令执行失败(sh: exec: line 0: ... not found) → 容器以 exit code 127 终止 → 触发 CrashLoopBackOff 重启循环
```

### 根因结论

已确认根因为：**应用容器镜像中不包含启动命令指定的二进制文件或脚本 `/opt/app/unavailable-command`**。

该根因得到了以下决定性事实的直接支持：
- 日志直接报错“not found”：`/opt/app/unavailable-command: not found`（证据 #5）。
- 容器终止退出码为 127，符合系统级命令找不到的标准返回码（证据 #4）。
- 低资源限制（证据 #3）佐证了异常并非由资源超限（如 OOMKilled）引起。

---

## 📊 性能统计

```text
├─ 总耗时: 1.3m
├─ 问题定位: 30.9s
├─ 并发证据采集: 36.9s
│  └─ g1 aiops-case-v08/workload: 36.9s (Evidence 28.3s, RCA 8.5s)
└─ 汇总总结: 9.0s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
