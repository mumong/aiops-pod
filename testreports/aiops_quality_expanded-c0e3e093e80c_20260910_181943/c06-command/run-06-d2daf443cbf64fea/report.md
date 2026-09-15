## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | CrashLoopBackOff |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | Logging | elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` (fact-1f26c7f41d44) | 直接证明容器启动时执行文件缺失，是 Exit Code 127 的成因 |
| 2 | K8s State | kubernetes | `exit_code: 127` (fact-328cb87bd132) | 证实进程未找到可执行文件导致异常退出 |
| 3 | K8s State | kubernetes | `restart_count: 6` (fact-4428faa995b7) | 证实系统持续触发重启循环，形成 CrashLoopBackOff 状态 |
| 4 | K8s State | kubernetes | `reason: CrashLoopBackOff` (fact-79523cc95405) | 确认当前 Pod 最终呈现的异常状态 |
| 5 | Metric | prometheus | `kube_pod_container_status_restarts_total = 6` (fact-58551920e4a6) | 独立验证重启次数与 K8s State 一致 |

证据 1 的日志明确指出了错误文件路径 `/opt/app/unavailable-command`，直接解释了证据 2 中 Exit Code 127 的含义。证据 2 的退出码导致了证据 3 中的重启，最终形成了证据 4 的 CrashLoopBackOff 状态，Metric 数据（证据 5）在重启计数上提供了交叉印证。

## 🎯 根因分析 · g1

### 因果链

```text
容器镜像中缺少 /opt/app/unavailable-command 可执行文件 → 执行 sh -c exec /opt/app/unavailable-command 失败，返回 Exit Code 127 → 容器异常退出并触发自动重启机制 → Pod 进入 CrashLoopBackOff 状态
```

### 根因结论

**已确认的根因**：容器启动命令指定的可执行文件 `/opt/app/unavailable-command` 在容器镜像中不存在，导致启动进程立即失败（Exit Code 127）并触发重启循环。

该结论由以下事实强支撑：
- 日志明确提示文件未找到 (`fact-1f26c7f41d44`)；
- 容器异常退出的退出码 127 是典型的“命令未找到”状态码 (`fact-328cb87bd132`)；
- 系统的重启行为最终表现为 CrashLoopBackOff (`fact-79523cc95405`, `fact-58551920e4a6`)。

**未知项**：无法从现有数据区分是镜像构建过程的错误（如 COPY 命令遗漏），还是容器部署配置中指定的启动命令有误。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 19.3s
├─ 并发证据采集: 43.4s
│  └─ g1 aiops-case-v08/workload: 43.4s (Evidence 33.0s, RCA 10.2s)
└─ 汇总总结: 9.7s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
