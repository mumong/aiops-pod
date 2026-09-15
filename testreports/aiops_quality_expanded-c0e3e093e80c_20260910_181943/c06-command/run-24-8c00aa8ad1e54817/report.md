## 📊 异常概览与现象

| 组 | 异常实体 | 异常状态 | 关键错误信息 |
|---|---|---|---|
| g1 | `aiops-case-v08/workload` | CrashLoopBackOff | Pod配置指定了不存在的可执行文件 /opt/app/unavailable-command，导致容器启动失败 (Exit 127) |

---

## 🕵️ 证据内容 · g1

| # | 类型 | 来源 | 真实原始结果 | 诊断作用 |
|---|---|---|---|---|
| 1 | K8s State | Kubernetes | container.last_exit_code: 127 | 提供终止代码事实，指示文件未找到 |
| 2 | Logging | Elasticsearch | `sh: exec: line 0: /opt/app/unavailable-command: not found` | 直接揭示容器启动时的致命错误原因 |
| 3 | K8s State | Kubernetes | pod.condition: Ready=False, ContainersNotReady | 确认业务容器未就绪，符合预期 |
| 4 | K8s State | Kubernetes | container.waiting_reason: CrashLoopBackOff | 描述当前 Pod 所处的异常循环状态 |

Kubernetes 状态与日志证据高度一致：`Exit 127` 终止码与日志中的 "not found" 报错互为印证，共同指向执行文件缺失；`CrashLoopBackOff` 是这一机制导致的直接运行状态。

## 🎯 根因分析 · g1

### 因果链

```text
镜像配置指定了不存在的可执行文件 /opt/app/unavailable-command → 容器启动时 shell 无法找到该文件 (Exit 127) → 直接失败 → 用户可见现象
```

### 根因结论

已确认的根因：Pod 配置指定了不存在的可执行文件 `/opt/app/unavailable-command`。
该配置直接导致容器启动执行失败（Exit 127），并引发 Kubernetes 的自动重试与 `CrashLoopBackOff` 循环状态。事实支撑如下：
- 原始日志明确报错 `/opt/app/unavailable-command: not found`（见证据 #2）。
- 容器最后终止状态码为 `127`（见证据 #1），这是系统级“命令未找到”的标准错误码。
- 容器当前处于 `CrashLoopBackOff` 等待状态（见证据 #4），符合配置错误导致启动失败的典型模式。

---

## 📊 性能统计

```text
├─ 总耗时: 1.2m
├─ 问题定位: 24.3s
├─ 并发证据采集: 39.9s
│  └─ g1 aiops-case-v08/workload: 39.9s (Evidence 33.2s, RCA 6.5s)
└─ 汇总总结: 6.7s
```

📋 Runbook 参考

- **g1 aiops-case-v08/workload**: pod-crashloop-runtime
